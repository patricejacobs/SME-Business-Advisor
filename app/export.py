"""Administrator CLI - the follow-up workflow lives here.

    python -m app.export list                     # who is waiting to be contacted
    python -m app.export list --all               # everyone, including in-progress
    python -m app.export show 7                   # one client's full answers
    python -m app.export csv leads.csv            # one row per client, all answers
    python -m app.export mark 7 contacted         # new | contacted | paid | declined
    python -m app.export mark 7 paid --note "Paid via MMG 2026-07-20"
"""

import argparse
import csv
import sys
from pathlib import Path

from . import db, logs
from .questions import ALL_QUESTIONS

VALID_STATUSES = ("new", "contacted", "paid", "declined")


def cmd_list(args: argparse.Namespace) -> None:
    query = "SELECT * FROM clients"
    params: tuple = ()
    if not args.all:
        query += " WHERE status = 'complete' AND admin_status = 'new'"
    query += " ORDER BY completed_at IS NULL, completed_at DESC, created_at DESC"

    with db.connect() as conn:
        rows = conn.execute(query, params).fetchall()

    if not rows:
        print("No clients waiting. Use --all to see everyone.")
        return

    print(f"{'ID':>4}  {'PHONE':<15} {'NAME':<20} {'STATUS':<12} {'FOLLOW-UP':<10} TITLE")
    print("-" * 100)
    for row in rows:
        print(
            f"{row['id']:>4}  "
            f"+{row['phone']:<14} "
            f"{(row['name'] or '-')[:19]:<20} "
            f"{row['status']:<12} "
            f"{row['admin_status']:<10} "
            f"{(row['plan_title'] or '-')[:40]}"
        )
    print(f"\n{len(rows)} client(s).")


def cmd_show(args: argparse.Namespace) -> None:
    with db.connect() as conn:
        client = conn.execute(
            "SELECT * FROM clients WHERE id = ?", (args.client_id,)
        ).fetchone()
    if client is None:
        sys.exit(f"No client with id {args.client_id}")

    print(f"\n{client['plan_title'] or '(no title yet)'}")
    print(f"Client:    {client['name'] or '(not given)'}")
    print(f"WhatsApp:  +{client['phone']}")
    print(f"Status:    {client['status']} / follow-up: {client['admin_status']}")
    print(f"Started:   {client['created_at']}")
    print(f"Completed: {client['completed_at'] or '(in progress)'}")
    if client["log_path"]:
        print(f"Log file:  {client['log_path']}")
    if client["admin_notes"]:
        print(f"Notes:     {client['admin_notes']}")

    answers = {r["question_key"]: r for r in db.get_answers(client["id"])}
    print()
    for question in ALL_QUESTIONS:
        row = answers.get(question.key)
        value = (row["parsed_value"] or row["raw_answer"]) if row else "(not answered)"
        print(f"  {question.text}\n    {value}\n")


def cmd_csv(args: argparse.Namespace) -> None:
    with db.connect() as conn:
        query = "SELECT * FROM clients"
        if not args.all:
            query += " WHERE status = 'complete'"
        query += " ORDER BY id"
        clients = conn.execute(query).fetchall()

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
        for client in clients:
            answers = {r["question_key"]: r for r in db.get_answers(client["id"])}
            row = {
                "id": client["id"],
                "phone": f"+{client['phone']}",
                "name": client["name"],
                "plan_title": client["plan_title"],
                "status": client["status"],
                "admin_status": client["admin_status"],
                "created_at": client["created_at"],
                "completed_at": client["completed_at"],
                "log_path": client["log_path"],
            }
            for question in ALL_QUESTIONS:
                answer = answers.get(question.key)
                row[question.key] = (
                    (answer["parsed_value"] or answer["raw_answer"]) if answer else ""
                )
            writer.writerow(row)

    print(f"Wrote {len(clients)} client(s) to {out}")


def cmd_mark(args: argparse.Namespace) -> None:
    if args.status not in VALID_STATUSES:
        sys.exit(f"Status must be one of: {', '.join(VALID_STATUSES)}")

    with db.connect() as conn:
        client = conn.execute(
            "SELECT * FROM clients WHERE id = ?", (args.client_id,)
        ).fetchone()
    if client is None:
        sys.exit(f"No client with id {args.client_id}")

    fields = {"admin_status": args.status}
    if args.status == "contacted" and not client["contacted_at"]:
        fields["contacted_at"] = db.now()
    if args.note:
        existing = client["admin_notes"] or ""
        stamped = f"[{db.now()}] {args.note}"
        fields["admin_notes"] = f"{existing}\n{stamped}".strip()

    db.update_client(client["phone"], **fields)
    print(f"Client {args.client_id} ({client['name'] or 'unnamed'}) -> {args.status}")


def cmd_relog(args: argparse.Namespace) -> None:
    """Regenerate log files from the database."""
    with db.connect() as conn:
        clients = conn.execute("SELECT id FROM clients ORDER BY id").fetchall()
    for client in clients:
        path = logs.write_log(client["id"])
        print(f"Wrote {path}")


def main() -> None:
    db.init()

    parser = argparse.ArgumentParser(
        prog="python -m app.export",
        description="Administrator tools for the business plan intake agent.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List clients waiting for follow-up")
    p_list.add_argument("--all", action="store_true", help="Include in-progress clients")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show one client's full answers")
    p_show.add_argument("client_id", type=int)
    p_show.set_defaults(func=cmd_show)

    p_csv = sub.add_parser("csv", help="Export clients and answers to CSV")
    p_csv.add_argument("path", help="Output file, e.g. leads.csv")
    p_csv.add_argument("--all", action="store_true", help="Include in-progress clients")
    p_csv.set_defaults(func=cmd_csv)

    p_mark = sub.add_parser("mark", help="Set a client's follow-up status")
    p_mark.add_argument("client_id", type=int)
    p_mark.add_argument("status", help=" | ".join(VALID_STATUSES))
    p_mark.add_argument("--note", default="", help="Append a timestamped note")
    p_mark.set_defaults(func=cmd_mark)

    p_relog = sub.add_parser("relog", help="Regenerate all log files from the database")
    p_relog.set_defaults(func=cmd_relog)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
