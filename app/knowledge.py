"""The Desk's Guyana reference material, bundled into this service so the

bot can answer a genuine factual question a client asks right when they
confirm they're ready to resume their business plan - see
conversation._handle_resume_plan_confirmation, the only caller of
answer_from_knowledge_base() in llm.py.

These are copies of the files under the main project's `references/`
directory (compliance, finance ecosystem, operating context) - not a
live link. If the source files are revised, re-copy them here and
redeploy; there is no automatic sync between the two repos.
"""

import re
from pathlib import Path

from .config import BASE_DIR

REFERENCES_DIR = BASE_DIR / "references"

TOPICS = ("compliance", "finance", "operating_context")

_FILENAMES = {
    "compliance": "guyana-compliance.md",
    "finance": "guyana-finance-ecosystem.md",
    "operating_context": "guyana-operating-context.md",
}


def _load(topic: str) -> tuple[str, str]:
    path = REFERENCES_DIR / _FILENAMES[topic]
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^last_verified:\s*(\S+)", text, re.MULTILINE)
    last_verified = match.group(1) if match else "an unknown date"
    return text, last_verified


_LOADED = {topic: _load(topic) for topic in TOPICS}


def content_for(topic: str) -> str:
    return _LOADED[topic][0]


def last_verified_for(topic: str) -> str:
    return _LOADED[topic][1]
