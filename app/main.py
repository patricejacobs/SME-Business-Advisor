"""FastAPI webhook for the Meta WhatsApp Cloud API.

Meta expects a 200 within seconds and retries anything slower, so inbound
messages are acknowledged immediately and processed in a background task.
Deduplication happens before the ack, keyed on Meta's message ID, so a retry
can never run the same message through the state machine twice.
"""

import hmac
import json
import logging
import os
import time
from contextlib import asynccontextmanager, contextmanager

from fastapi import BackgroundTasks, FastAPI, Request, Response

from . import config, conversation, db, stt, whatsapp
from .logs import log_path_for, render_log

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

# BackgroundTasks can run concurrently across separate webhook requests, but a
# single client's conversation never should - two of a client's messages
# arriving close together (someone typing fast, or Meta redelivering) must be
# handled strictly one after another. Otherwise both can read the same
# "engagement complete" state before either has acted on it, each start a new
# engagement, and a later message ends up referencing one that's already been
# superseded - this is what caused a real FOREIGN KEY constraint crash in
# production. The lock lives in the shared SQLite database (db.py) rather
# than process memory - an in-memory lock only protects whichever single
# worker process happens to hold it, and does nothing if Render is running
# more than one.
_LOCK_POLL_SECONDS = 0.2
_LOCK_TIMEOUT_SECONDS = 25


@contextmanager
def _lock_for(phone: str):
    deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
    while not db.try_acquire_phone_lock(phone):
        if time.monotonic() > deadline:
            raise TimeoutError(f"Could not acquire conversation lock for {phone}")
        time.sleep(_LOCK_POLL_SECONDS)
    try:
        yield
    finally:
        db.release_phone_lock(phone)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    """Which exact commit this running instance is serving from - Render sets

    RENDER_GIT_COMMIT automatically on every deploy. Exists so a fresh push
    can be confirmed as actually live (not just "the server is responding",
    which a stale instance mid-rollover would also satisfy) before relying
    on a retest against it.
    """
    return {"commit": os.getenv("RENDER_GIT_COMMIT", "unknown")}


def _admin_authorized(request: Request) -> bool:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return False
    provided = header.removeprefix("Bearer ").strip()
    return hmac.compare_digest(provided, config.ADMIN_API_KEY)


@app.get("/admin/logs")
def admin_logs(request: Request) -> Response:
    """Pull completed intakes (engagements) as JSON, for `python -m app.export

    pull` to sync locally. Deliberately read-only and scoped to completed
    engagements only - this is a data handoff to the advisor, not a general
    API. Always returns everything complete (not just new since last pull);
    the local pull command overwrites idempotently. A client with more than
    one completed plan appears once per plan.
    """
    if not _admin_authorized(request):
        log.warning("Rejected /admin/logs request with missing or bad admin key")
        return Response(status_code=401, content="unauthorized")

    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id FROM engagements WHERE status = 'complete' ORDER BY id"
        ).fetchall()

    engagements = []
    for row in rows:
        client, engagement, markdown = render_log(row["id"])
        engagements.append(
            {
                "id": engagement["id"],
                "filename": log_path_for(client, engagement).name,
                "client_name": client["name"],
                "client_phone": client["phone"],
                "completed_at": engagement["completed_at"],
                "markdown": markdown,
            }
        )

    return Response(content=json.dumps({"engagements": engagements}), media_type="application/json")


@app.get("/admin/engagements")
def admin_engagements(request: Request) -> Response:
    """Every engagement regardless of completion status, one row per business

    plan (joined with the owning client's identity) - for diagnosing where a
    conversation actually got to (which question it's stuck on, when it was
    last seen) when a completed-only view via /admin/logs isn't enough.
    """
    if not _admin_authorized(request):
        log.warning("Rejected /admin/engagements request with missing or bad admin key")
        return Response(status_code=401, content="unauthorized")

    with db.connect() as conn:
        rows = conn.execute(
            "SELECT engagements.id, engagements.plan_title, engagements.state, "
            "engagements.status, engagements.created_at, engagements.updated_at, "
            "engagements.completed_at, clients.id AS client_id, clients.phone, "
            "clients.name, clients.last_seen_at, clients.last_persona "
            "FROM engagements JOIN clients ON clients.id = engagements.client_id "
            "ORDER BY engagements.id DESC"
        ).fetchall()

    engagements = [dict(row) for row in rows]
    return Response(content=json.dumps({"engagements": engagements}), media_type="application/json")


@app.get("/admin/test-notify")
def test_notify(request: Request) -> Response:
    """Resends the admin completion notification for the most recently

    completed engagement, clearly marked [TEST] - lets the admin confirm the
    ADMIN_NOTIFY_PHONE_NUMBERS feature actually delivers, using real data,
    without waiting for (or faking) a brand new completion.
    """
    if not _admin_authorized(request):
        log.warning("Rejected /admin/test-notify request with missing or bad admin key")
        return Response(status_code=401, content="unauthorized")

    if not config.ADMIN_NOTIFY_PHONE_NUMBERS:
        return Response(
            status_code=400,
            content=json.dumps({"error": "ADMIN_NOTIFY_PHONE_NUMBERS is not set"}),
            media_type="application/json",
        )

    with db.connect() as conn:
        row = conn.execute(
            "SELECT id FROM engagements WHERE status = 'complete' ORDER BY completed_at DESC LIMIT 1"
        ).fetchone()
    if row is None:
        return Response(
            status_code=404,
            content=json.dumps({"error": "no completed engagements to test with"}),
            media_type="application/json",
        )

    engagement = db.get_engagement(row["id"])
    with db.connect() as conn:
        client_row = conn.execute(
            "SELECT * FROM clients WHERE id = ?", (engagement["client_id"],)
        ).fetchone()

    conversation._notify_admin_of_completion(dict(client_row), dict(engagement), has_skipped=False, test=True)

    return Response(
        content=json.dumps(
            {
                "sent_to": sorted(config.ADMIN_NOTIFY_PHONE_NUMBERS),
                "engagement_id": engagement["id"],
                "plan_title": engagement["plan_title"],
            }
        ),
        media_type="application/json",
    )


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

        background.add_task(_process, phone, text, wa_id)

    for wa_id, phone, media_type, media_id, caption in whatsapp.extract_media_messages(payload):
        if db.already_processed(wa_id):
            log.info("Skipping duplicate delivery of %s", wa_id)
            continue
        db.log_message(client_id=None, direction="in", body=f"[{media_type}]", wa_id=wa_id)

        if media_type == "image":
            background.add_task(_process_image, phone, media_id, caption, wa_id)
        elif media_type == "audio":
            background.add_task(_process_audio, phone, media_id, wa_id)
        else:
            background.add_task(_process_unsupported_media, phone, wa_id)

    return Response(status_code=200, content="ok")


def _process(phone: str, text: str, wa_id: str) -> None:
    """Run the state machine and deliver the replies. Runs off the request path."""
    whatsapp.show_typing(wa_id)
    try:
        with _lock_for(phone):
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


def _process_image(phone: str, media_id: str, caption: str, wa_id: str) -> None:
    """Download a WhatsApp image and run it through the state machine. Runs off the request path."""
    whatsapp.show_typing(wa_id)
    try:
        image_bytes, mime_type = whatsapp.download_media(media_id)
    except Exception:
        log.exception("Failed to download image %s for %s", media_id, phone)
        whatsapp.send_text(
            phone,
            "Sorry, I couldn't download that photo. Could you try sending it again, "
            "or just type your answer instead?",
        )
        return

    try:
        with _lock_for(phone):
            replies = conversation.handle_image(phone, image_bytes, mime_type, caption)
    except Exception:
        log.exception("Image conversation failed for %s", phone)
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


def _process_audio(phone: str, media_id: str, wa_id: str) -> None:
    """Download a WhatsApp voice note, transcribe it, and run it through the
    state machine same as any typed message. Runs off the request path."""
    whatsapp.show_typing(wa_id)

    if not stt.is_configured():
        whatsapp.send_text(
            phone,
            "Thanks for the voice note! I can't listen to voice messages just yet - "
            "could you reply with a text message instead?",
        )
        return

    try:
        audio_bytes, mime_type = whatsapp.download_media(media_id)
    except Exception:
        log.exception("Failed to download audio %s for %s", media_id, phone)
        whatsapp.send_text(
            phone,
            "Sorry, I couldn't download that voice note. Could you try sending "
            "it again, or just type your answer instead?",
        )
        return

    text = stt.transcribe_audio(audio_bytes, mime_type)
    if not text:
        whatsapp.send_text(
            phone,
            "Sorry, I couldn't quite make that out - could you try recording it "
            "again, or just type your answer instead?",
        )
        return

    try:
        with _lock_for(phone):
            replies = conversation.handle(phone, text)
    except Exception:
        log.exception("Conversation failed for %s (from voice note)", phone)
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


def _process_unsupported_media(phone: str, wa_id: str) -> None:
    """Voice notes and other media without a handler yet. Runs off the request path."""
    whatsapp.show_typing(wa_id)
    whatsapp.send_text(
        phone,
        "Thanks for sending that! I can't listen to voice notes just yet - "
        "could you reply with a text message instead?",
    )
