"""Per-client log file.

Written when the intake completes, and rewritten if the client sends anything
afterwards. Format matches clients/<name>/profile.md conventions in the parent
repo so an advisor can drop it straight into an engagement folder.
"""

import re
from pathlib import Path

from . import config, db
from .questions import ALL_QUESTIONS


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug[:60] or "unnamed"


def log_path_for(client) -> Path:
    name = _slug(client["name"])
    return config.LOG_DIR / f"{client['id']:05d}-{name}.md"


def render_log(client_id: int) -> tuple[dict, str]:
    """Build the markdown log text for a client. Returns (client_row, markdown) - does not write to disk."""
    with db.connect() as conn:
        client = conn.execute(
            "SELECT * FROM clients WHERE id = ?", (client_id,)
        ).fetchone()
    if client is None:
        raise ValueError(f"no client with id {client_id}")

    answers = {row["question_key"]: row for row in db.get_answers(client_id)}

    lines: list[str] = [
        f"# {client['plan_title'] or 'Business plan intake'}",
        "",
        f"- **Client:** {client['name'] or '(not given)'}",
        f"- **WhatsApp:** +{client['phone']}",
        f"- **Started:** {client['created_at']}",
        f"- **Completed:** {client['completed_at'] or '(in progress)'}",
        f"- **Questions answered:** {len(answers)} of {len(ALL_QUESTIONS)}",
        "",
        "> Collected over WhatsApp by the intake agent. Figures are the owner's",
        "> own estimates unless stated otherwise - verify before relying on them.",
        "",
    ]

    current_wave = None
    for question in ALL_QUESTIONS:
        row = answers.get(question.key)
        if question.wave != current_wave:
            current_wave = question.wave
            lines += ["", f"## {current_wave}", ""]

        lines.append(f"**{question.text}**")
        if row is None:
            lines += ["", "_Not answered._", ""]
            continue

        lines += ["", row["parsed_value"] or row["raw_answer"], ""]
        if row["raw_answer"] != (row["parsed_value"] or row["raw_answer"]):
            lines += [f"_Client's own words: \"{row['raw_answer']}\"_", ""]

    extra = answers.get("additional_notes")
    if extra is not None:
        lines += ["", "## Added after the intake", "", extra["raw_answer"], ""]

    return client, "\n".join(lines)


def write_log(client_id: int) -> Path:
    client, markdown = render_log(client_id)
    path = log_path_for(client)
    path.write_text(markdown, encoding="utf-8")
    return path
