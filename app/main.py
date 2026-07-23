"""FastAPI webhook for the Meta WhatsApp Cloud API.

Meta expects a 200 within seconds and retries anything slower, so inbound
messages are acknowledged immediately and processed in a background task.
Deduplication happens before the ack, keyed on Meta's message ID, so a retry
can never run the same message through the state machine twice.
"""

import hmac
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import BackgroundTasks, FastAPI, Request, Response

from . import config, conversation, db, whatsapp
from .logs import log_path_for, render_log

GUYANA_TZ = ZoneInfo(config.TIMEZONE)


def is_within_working_hours() -> bool:
    hour = datetime.now(GUYANA_TZ).hour
    return config.WORKING_HOURS_START <= hour < config.WORKING_HOURS_END

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init()
    log.info("Database ready at %s", config.DB_PATH)
    log.info("Logs will be written to %s", config.LOG_DIR)
    if config.ALLOW_UNSIGNED_WEBHOOKS:
        log.warning("ALLOW_UNSIGNED_WEBHOOKS=1 - webhook signatures are NOT checked")
    yield


app = FastAPI(title="Guyana SME Business Plan Intake Agent", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _admin_authorized(request: Request) -> bool:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return False
    provided = header.removeprefix("Bearer ").strip()
    return hmac.compare_digest(provided, config.ADMIN_API_KEY)


@app.get("/admin/logs")
def admin_logs(request: Request) -> Response:
    """Pull completed intakes as JSON, for `python -m app.export pull` to sync locally.

    Deliberately read-only and scoped to completed clients only - this is a data
    handoff to the advisor, not a general API. Always returns everything complete
    (not just new since last pull); the local pull command overwrites idempotently.
    """
    if not _admin_authorized(request):
        log.warning("Rejected /admin/logs request with missing or bad admin key")
        return Response(status_code=401, content="unauthorized")

    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id FROM clients WHERE status = 'complete' ORDER BY id"
        ).fetchall()

    clients = []
    for row in rows:
        client, markdown = render_log(row["id"])
        clients.append(
            {
                "id": client["id"],
                "filename": log_path_for(client).name,
                "name": client["name"],
                "phone": client["phone"],
                "completed_at": client["completed_at"],
                "markdown": markdown,
            }
        )

    return Response(content=json.dumps({"clients": clients}), media_type="application/json")


@app.get("/webhook")
def verify(request: Request) -> Response:
    """Meta calls this once when you register the webhook URL."""
    params = request.query_params
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == config.WHATSAPP_VERIFY_TOKEN
    ):
        log.info("Webhook verified by Meta")
        return Response(content=params.get("hub.challenge", ""), media_type="text/plain")
    log.warning("Webhook verification failed - check WHATSAPP_VERIFY_TOKEN")
    return Response(status_code=403, content="verification failed")


@app.post("/webhook")
async def receive(request: Request, background: BackgroundTasks) -> Response:
    raw = await request.body()

    if not whatsapp.verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        log.warning("Rejected webhook with bad or missing signature")
        return Response(status_code=403, content="bad signature")

    try:
        payload = await request.json()
    except Exception:
        log.exception("Webhook body was not valid JSON")
        return Response(status_code=200, content="ok")

    for wa_id, phone, text in whatsapp.extract_text_messages(payload):
        if db.already_processed(wa_id):
            log.info("Skipping duplicate delivery of %s", wa_id)
            continue
        # Recorded before the ack so a retry arriving mid-processing is dropped.
        db.log_message(client_id=None, direction="in", body=text, wa_id=wa_id)

        if not is_within_working_hours():
            log.info(
                "Received %s outside working hours (%s:00-%s:00 %s) - logged, not processed",
                wa_id, config.WORKING_HOURS_START, config.WORKING_HOURS_END, config.TIMEZONE,
            )
            continue

        background.add_task(_process, phone, text)

    return Response(status_code=200, content="ok")


def _process(phone: str, text: str) -> None:
    """Run the state machine and deliver the replies. Runs off the request path."""
    try:
        replies = conversation.handle(phone, text)
    except Exception:
        log.exception("Conversation failed for %s", phone)
        whatsapp.send_text(
            phone,
            "Sorry, something went wrong on our end. Please send that again "
            "in a moment and we will pick up where we left off.",
        )
        return

    client = db.get_client(phone)
    client_id = client["id"] if client else None

    for reply in replies:
        whatsapp.send_text(phone, reply)
        db.log_message(client_id=client_id, direction="out", body=reply)
