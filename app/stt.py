"""Speech-to-text for WhatsApp voice notes, via OpenAI's Whisper API.

Claude's API has no audio input as of this writing, so voice notes need a
separate transcription step before they can go through the normal text
pipeline. This is optional - if OPENAI_API_KEY isn't set, the caller should
fall back to asking the client to type instead (see main.py).
"""

import logging

import httpx

from . import config

log = logging.getLogger(__name__)

TRANSCRIBE_URL = "https://api.openai.com/v1/audio/transcriptions"


def is_configured() -> bool:
    return bool(config.OPENAI_API_KEY)


def transcribe_audio(audio_bytes: bytes, mime_type: str) -> str | None:
    """Transcribe a voice note as English text. Returns None on failure or silence.

    WhatsApp voice notes arrive as audio/ogg (opus codec), which Whisper
    accepts directly - no transcoding needed.
    """
    if not is_configured():
        return None

    ext = "ogg" if "ogg" in mime_type else "m4a" if "m4a" in mime_type else "mp3"
    files = {"file": (f"voice_note.{ext}", audio_bytes, mime_type)}
    data = {"model": "whisper-1", "language": "en"}
    headers = {"Authorization": f"Bearer {config.OPENAI_API_KEY}"}

    try:
        response = httpx.post(TRANSCRIBE_URL, headers=headers, files=files, data=data, timeout=60)
        if response.status_code >= 400:
            log.error("Whisper transcription failed (%s): %s", response.status_code, response.text)
            return None
        text = response.json().get("text", "").strip()
        return text or None
    except httpx.HTTPError:
        log.exception("Whisper transcription errored")
        return None
