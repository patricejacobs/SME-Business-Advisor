"""Administrator CLI - the follow-up workflow lives here.

A client can now have more than one engagement (business plan) over time, so
every command below operates per-engagement, not per-client - "id" in these
commands is always an engagement id.

    python -m app.export list                     # who is waiting to be contacted
    python -m app.export list --all               # every engagement, including in-progress
    python -m app.export show 7                   # one engagement's full answers
    python -m app.export csv leads.csv            # one row per engagement, all answers
    python -m app.export mark 7 contacted         # new | contacted | paid | declined
    python -m app.export mark 7 paid --note "Paid via MMG 2026-07-20"
    python -m app.export pull <render-url> <local-dir>   # sync completed intakes down
    python -m app.export off-hours                       # who to call back, and when
"""

import argparse
import csv
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

from . import db, logs
from .questions import ALL_QUESTIONS

load_dotenv()

VALID_STATUSES = ("new", "contacted", "paid", "declined")

_ENGAGEMENT_QUERY = """
    SELECT engagements.*, clients.name AS client_name, clients.phone AS client_phone
    FROM engagements JOIN clients ON clients.id = engagements.client_id
"""


def cmd_list(args: argparse.Namespace) -> None:
    query = _ENGAGEMENT_QUERY
    if not args.all:
        query += " WHERE engagements.status = 'complete' AND engagements.admin_status = 'new'"
    query += " ORDER BY engagements.completed_at IS NULL, engagements.completed_at DESC, engagements.created_at DESC"

    with db.connect() as conn:
        rows = conn.execute(query).fetchall()

    if not rows:
        print("No engagements waiting. Use --all to see everyone.")
        return

    print(f"{'ID':>4}  {'PHONE':<15} {'NAME':<20} {'STATUS':<12} {'FOLLOW-UP':<10} TITLE")
    print("-" * 100)
    for row in rows:
        print(
            f"{row['id']:>4}  "
            f"+{row['client_phone']:<14} "
            f"{(row['client_name'] or '-')[:19]:<20} "
            f"{row['status']:<12} "
            f"{row['admin_status']:<10} "
            f"{(row['plan_title'] or '-')[:40]}"
        )
    print(f"\n{len(rows)} engagement(s).")


def cmd_show(args: argparse.Namespace) -> None:
    with db.connect() as conn:
        row = conn.execute(
            _ENGAGEMENT_QUERY + " WHERE engagements.id = ?", (args.engagement_id,)
        ).fetchone()
    if row is None:
        sys.exit(f"No engagement with id {args.engagement_id}")

    print(f"\n{row['plan_title'] or '(no title yet)'}")
    print(f"Client:    {row['client_name'] or '(not given)'}")
    print(f"WhatsApp:  +{row['client_phone']}")
    print(f"Status:    {row['status']} / follow-up: {row['admin_status']}")
    print(f"Started:   {row['created_at']}")
    print(f"Completed: {row['completed_at'] or '(in progress)'}")
    if row["log_path"]:
        print(f"Log file:  {row['log_path']}")
    if row["admin_notes"]:
        print(f"Notes:     {row['admin_notes']}")

    answers = {r["question_key"]: r for r in db.get_answers(row["id"])}
    print()
    for question in ALL_QUESTIONS:
        answer = answers.get(question.key)
        value = (answer["parsed_value"] or answer["raw_answer"]) if answer else "(not answered)"
        print(f"  {question.text}\n    {value}\n")


def cmd_csv(args: argparse.Namespace) -> None:
    query = _ENGAGEMENT_QUERY
    if not args.all:
        query += " WHERE engagements.status = 'complete'"
    query += " ORDER BY engagements.id"

    with db.connect() as conn:
        rows = conn.execute(query).fetchall()

    fieldnames = [
        "id",
        "phone",
        "name",
        "plan_title",
        "status",
        "admin_status",
        "created_at",
        "completed_at",
        "log_path",
        *[q.key for q in ALL_QUESTIONS],
    ]

    out = Path(args.path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            answers = {r["question_key"]: r for r in db.get_answers(row["id"])}
            out_row = {
                "id": row["id"],
                "phone": f"+{row['client_phone']}",
                "name": row["client_name"],
                "plan_title": row["plan_title"],
                "status": row["status"],
                "admin_status": row["admin_status"],
                "created_at": row["created_at"],
                "completed_at": row["completed_at"],
                "log_path": row["log_path"],
            }
            for question in ALL_QUESTIONS:
                answer = answers.get(question.key)
                out_row[question.key] = (
                    (answer["parsed_value"] or answer["raw_answer"]) if answer else ""
                )
            writer.writerow(out_row)

    print(f"Wrote {len(rows)} engagement(s) to {out}")


def cmd_mark(args: argparse.Namespace) -> None:
    if args.status not in VALID_STATUSES:
        sys.exit(f"Status must be one of: {', '.join(VALID_STATUSES)}")

    engagement = db.get_engagement(args.engagement_id)
    if engagement is None:
        sys.exit(f"No engagement with id {args.engagement_id}")

    fields = {"admin_status": args.status}
    if args.status == "contacted" and not engagement["contacted_at"]:
        fields["contacted_at"] = db.now()
    if args.note:
        existing = engagement["admin_notes"] or ""
        stamped = f"[{db.now()}] {args.note}"
        fields["admin_notes"] = f"{existing}\n{stamped}".strip()

    db.update_engagement(args.engagement_id, **fields)

    with db.connect() as conn:
        name_row = conn.execute(
            "SELECT clients.name FROM clients JOIN engagements ON engagements.client_id = clients.id "
            "WHERE engagements.id = ?",
            (args.engagement_id,),
        ).fetchone()
    print(f"Engagement {args.engagement_id} ({(name_row['name'] if name_row else None) or 'unnamed'}) -> {args.status}")


def cmd_off_hours(args: argparse.Namespace) -> None:
    """List everyone who has texted outside working hours, for callback follow-up."""
    rows = db.list_off_hours_contacts()
    if not rows:
        print("No off-hours contacts logged.")
        return

    print(f"{'WHEN (UTC)':<20} {'PHONE':<15} NAME")
    print("-" * 60)
    for row in rows:
        print(f"{row['contacted_at']:<20} +{row['phone']:<14} {row['name'] or '(not given yet)'}")
    print(f"\n{len(rows)} off-hours contact(s).")


def cmd_pull(args: argparse.Namespace) -> None:
    """Pull all completed intakes from a deployed instance down to a local folder.

    Reads ADMIN_API_KEY from the local .env - must match the value set in the
    deployment's own environment variables. Overwrites idempotently; safe to
    re-run at any time (e.g. daily, before running `plan-intake-desk` locally).
    """
    admin_key = os.getenv("ADMIN_API_KEY", "").strip()
    if not admin_key:
        sys.exit("ADMIN_API_KEY is not set in your local .env - add the same value used on the deployment.")

    url = args.render_url.rstrip("/") + "/admin/logs"
    try:
        response = httpx.get(url, headers={"Authorization": f"Bearer {admin_key}"}, timeout=30)
    except httpx.HTTPError as exc:
        sys.exit(f"Could not reach {url}: {exc}")

    if response.status_code == 401:
        sys.exit("Rejected (401) - ADMIN_API_KEY here doesn't match the deployment's value.")
    if response.status_code != 200:
        sys.exit(f"Unexpected response {response.status_code}: {response.text}")

    engagements = response.json().get("engagements", [])
    out_dir = Path(args.local_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for engagement in engagements:
        path = out_dir / engagement["filename"]
        path.write_text(engagement["markdown"], encoding="utf-8")
        print(f"Pulled #{engagement['id']:>3}  {engagement['client_name'] or '(unnamed)':<25} -> {path}")

    print(f"\n{len(engagements)} completed intake(s) synced to {out_dir}")


def cmd_relog(args: argparse.Namespace) -> None:
    """Regenerate log files from the database."""
    with db.connect() as conn:
        rows = conn.execute("SELECT id FROM engagements ORDER BY id").fetchall()
    for row in rows:
        path = logs.write_log(row["id"])
        print(f"Wrote {path}")


def main() -> None:
    db.init()

    parser = argparse.ArgumentParser(
        prog="python -m app.export",
        description="Administrator tools for the business plan intake agent.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List engagements waiting for follow-up")
    p_list.add_argument("--all", action="store_true", help="Include in-progress engagements")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show one engagement's full answers")
    p_show.add_argument("engagement_id", type=int)
    p_show.set_defaults(func=cmd_show)

    p_csv = sub.add_parser("csv", help="Export engagements and answers to CSV")
    p_csv.add_argument("path", help="Output file, e.g. leads.csv")
    p_csv.add_argument("--all", action="store_true", help="Include in-progress engagements")
    p_csv.set_defaults(func=cmd_csv)

    p_mark = sub.add_parser("mark", help="Set an engagement's follow-up status")
    p_mark.add_argument("engagement_id", type=int)
    p_mark.add_argument("status", help=" | ".join(VALID_STATUSES))
    p_mark.add_argument("--note", default="", help="Append a timestamped note")
    p_mark.set_defaults(func=cmd_mark)

    p_relog = sub.add_parser("relog", help="Regenerate all log files from the database")
    p_relog.set_defaults(func=cmd_relog)

    p_off_hours = sub.add_parser("off-hours", help="List everyone who texted outside working hours")
    p_off_hours.set_defaults(func=cmd_off_hours)

    p_pull = sub.add_parser("pull", help="Sync completed intakes from a deployed instance to a local folder")
    p_pull.add_argument("render_url", help="Base URL of the deployment, e.g. https://your-app.onrender.com")
    p_pull.add_argument("local_dir", help="Local folder to write synced .md files into")
    p_pull.set_defaults(func=cmd_pull)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
