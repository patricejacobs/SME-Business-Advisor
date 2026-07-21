"""Meta WhatsApp Cloud API - outbound send and webhook signature verification."""

import hashlib
import hmac
import logging
from typing import Any, Iterator

import httpx

from . import config

log = logging.getLogger(__name__)

SEND_URL = (
    f"https://graph.facebook.com/{config.GRAPH_API_VERSION}"
    f"/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
)


def verify_signature(raw_body: bytes, header: str | None) -> bool:
    """Verify X-Hub-Signature-256 so only Meta can drive the bot."""
    if config.ALLOW_UNSIGNED_WEBHOOKS:
        log.warning("Signature verification is DISABLED - do not run this in production")
        return True
    if not config.WHATSAPP_APP_SECRET:
        log.error("WHATSAPP_APP_SECRET is not set - rejecting webhook")
        return False
    if not header or not header.startswith("sha256="):
        return False

    provided = header.removeprefix("sha256=")
    expected = hmac.new(
        config.WHATSAPP_APP_SECRET.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, provided)


def send_text(to_phone: str, body: str) -> None:
    """Send a plain text WhatsApp message. Logs and swallows delivery errors."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }
    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        response = httpx.post(SEND_URL, json=payload, headers=headers, timeout=30)
        if response.status_code >= 400:
            log.error(
                "WhatsApp send failed (%s) to %s: %s",
                response.status_code,
                to_phone,
                response.text,
            )
    except httpx.HTTPError:
        log.exception("WhatsApp send errored for %s", to_phone)


def extract_text_messages(payload: dict[str, Any]) -> Iterator[tuple[str, str, str]]:
    """Yield (wa_message_id, from_phone, text) for each inbound text message.

    Meta batches events and also sends delivery/read status callbacks through
    the same webhook. Everything that is not an inbound text is skipped.
    """
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value") or {}
            for message in value.get("messages", []) or []:
                if message.get("type") != "text":
                    continue
                wa_id = message.get("id")
                sender = message.get("from")
                text = ((message.get("text") or {}).get("body") or "").strip()
                if wa_id and sender and text:
                    yield wa_id, sender, text
