"""Run the whole conversation in your terminal - no WhatsApp, no Meta account.

    python -m app.simulate

Uses a fake phone number so it never collides with a real client. Everything
else is real: the same state machine, the same Claude calls, the same database
writes, the same log file. This is the fastest way to test changes to
questions.py or the system prompt.
"""

import sys

from . import conversation, db, logs

FAKE_PHONE = "592000000000"


def main() -> None:
    db.init()

    if "--reset" in sys.argv:
        with db.connect() as conn:
            conn.execute("DELETE FROM clients WHERE phone = ?", (FAKE_PHONE,))
        print(f"Cleared simulated client {FAKE_PHONE}\n")

    print("=" * 68)
    print("  SIMULATED WHATSAPP SESSION - type 'quit' to stop")
    print("=" * 68)

    # An empty first message triggers the greeting, same as a real first contact.
    for reply in conversation.handle(FAKE_PHONE, ""):
        print(f"\n[agent] {reply}\n")

    while True:
        try:
            text = input("[you]   ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text.lower() in {"quit", "exit"}:
            break
        if not text:
            continue

        for reply in conversation.handle(FAKE_PHONE, text):
            print(f"\n[agent] {reply}\n")

    client = db.get_client(FAKE_PHONE)
    if client:
        answered = len(db.get_answers(client["id"]))
        print("-" * 68)
        print(f"State:    {client['state']}")
        print(f"Name:     {client['name']}")
        print(f"Title:    {client['plan_title']}")
        print(f"Answered: {answered} question(s)")
        if answered:
            print(f"Log file: {logs.write_log(client['id'])}")


if __name__ == "__main__":
    main()
