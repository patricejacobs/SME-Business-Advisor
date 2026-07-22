# WhatsApp Business Plan Intake Agent

A conversational WhatsApp agent that collects what a Guyanese small business
owner needs for a business plan, saves it to a database and a per-client log
file, and queues the client for an administrator to contact about payment.

## How it works

```
Owner's WhatsApp
      |
      v
Meta Cloud API  --webhook-->  FastAPI (app/main.py)
                                   |
                                   v
                         state machine (conversation.py)
                                   |
                    +--------------+--------------+
                    v                             v
            Claude (llm.py)                 SQLite (db.py)
      interprets the reply,              clients / answers /
      writes the next message              messages tables
                                                  |
                                                  v
                                      log file per client (logs.py)
                                                  |
                                                  v
                                    admin CLI (export.py) -> CSV
```

The **question sequence is fixed** in `questions.py` — Claude never decides what
to ask next, so every required field gets filled. Claude handles two things per
turn: interpreting a messy reply (`"bout 400 thousand a month"` → `"GYD
400,000/month, client's estimate"`) and wording the next question naturally.
One API call per inbound message.

Conversation state lives in the database, not memory. A client can answer three
questions, disappear for a week, and pick up exactly where they left off — and
the server can restart without losing anyone.

## The gate

Before a single business question is asked, the agent secures the three things
you specified:

| Field | How it is captured |
|---|---|
| **Telephone number** | Taken from WhatsApp metadata — never asked |
| **Client name** | First question |
| **Business plan title** | Second question |

Only then does it move to the business questions. All three are promoted onto
the `clients` row so an administrator sees who a lead is without opening the
answers table.

## The questions

32 questions in six waves, matching the full `plan-intake-desk` checklist (a superset of the
lighter `client-intake` skill) so the output drops straight into generating a filed plan:

1. **Gate** — name, plan title
2. **The business** — registration, what they sell, years trading, location, staff, staff roles, owner's experience, equipment
3. **Money** — revenue, cost of goods, fixed costs, bank account, records, payment terms, debts, one-time start-up costs, owner's own contribution
4. **Goals** — why now, twelve-month goal, biggest worry
5. **Compliance** — TIN/VAT, GRA returns, NIS/PAYE, licences
6. **Market** — competition, how customers find them, suppliers, what breaks, funding needed, funding source

Edit `questions.py` to change them. Order is load-bearing; the gate must stay first.

## Setup

### 1. Install

```bash
cd whatsapp-agent
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash; use .venv\Scripts\activate in PowerShell
pip install -r requirements.txt
cp .env.example .env
```

### 2. Test it before touching Meta

```bash
python -m app.simulate
```

Runs the whole conversation in your terminal — real state machine, real Claude
calls, real database, real log file. No WhatsApp account needed. Add `--reset`
to start over. **Do this first** and tune the questions until you like the feel.

### 3. Meta WhatsApp Cloud API

You need a Meta Business account with a verified business, and a phone number
dedicated to the bot (it cannot be a number already on the WhatsApp app).

1. developers.facebook.com → create an app → add the **WhatsApp** product
2. **API Setup** gives you `WHATSAPP_PHONE_NUMBER_ID` and a temporary
   `WHATSAPP_ACCESS_TOKEN` (24h — generate a permanent System User token for
   production)
3. **App Settings → Basic** gives you `WHATSAPP_APP_SECRET`
4. Invent any random string for `WHATSAPP_VERIFY_TOKEN`
5. Put all four in `.env`

### 4. Run and connect the webhook

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Meta requires a public HTTPS URL. For local testing:

```bash
ngrok http 8000
```

In Meta → WhatsApp → Configuration → Webhook:
- **Callback URL:** `https://your-domain/webhook`
- **Verify token:** the same string you put in `.env`
- **Subscribe to:** the `messages` field

Message the bot's number from your phone. It should greet you and ask your name.

## Administrator workflow

```bash
python -m app.export list                 # completed intakes awaiting contact
python -m app.export list --all           # everyone, including in-progress
python -m app.export show 7               # one client's full answers
python -m app.export csv leads.csv        # spreadsheet: one row per client
python -m app.export mark 7 contacted
python -m app.export mark 7 paid --note "Paid via MMG 2026-07-20"
python -m app.export relog                # rebuild all log files from the database
```

Follow-up statuses: `new` → `contacted` → `paid` (or `declined`).

**Log files** land in `data/logs/00007-anita-persaud.md` — a formatted markdown
brief grouped by wave, with the client's own words preserved alongside the
cleaned value. Anything the client sends after finishing gets appended under
"Added after the intake".

**CSV** opens directly in Excel (UTF-8 BOM included) with one column per question.

## Files

| File | Purpose |
|---|---|
| `app/main.py` | FastAPI webhook — verification, signatures, dedupe, background dispatch |
| `app/conversation.py` | State machine — where each client is in the script |
| `app/questions.py` | The question script. **Edit this to change what is asked** |
| `app/llm.py` | Claude — answer interpretation and message wording, with fallbacks |
| `app/whatsapp.py` | Meta Cloud API send + webhook signature verification |
| `app/db.py` | SQLite schema and queries |
| `app/logs.py` | Per-client markdown log file |
| `app/export.py` | Administrator CLI |
| `app/simulate.py` | Terminal simulator for testing without WhatsApp |

## What has been verified

Tested end to end with a stubbed Claude call: gate ordering, phone capture,
unclear-reply handling (holds position instead of advancing), full 32-question
completion, all answers persisted, log file written with waves intact,
post-intake appends, webhook signature verification (valid/invalid/missing),
replay deduplication, non-text webhook events ignored, and CSV export contents.
The live webhook surface was exercised through FastAPI's test client.

**Not yet tested against real Meta infrastructure** — that needs your account
credentials. Step 2 above (`python -m app.simulate`) exercises everything except
the Meta transport.

## Operational notes

- **Cost.** One Claude call per inbound message, ~32 messages per completed
  intake. Running on `claude-opus-4-8`. If volume makes that expensive, change
  `MODEL` in `config.py` — but simulate first and check the interpretation
  quality on messy real-world answers before downgrading.
- **The 24-hour window.** Meta only lets you send free-form messages within 24
  hours of the client's last message. If a client goes quiet mid-intake, you
  cannot nudge them without an approved message template.
- **Signatures.** `ALLOW_UNSIGNED_WEBHOOKS=1` exists for local testing only.
  Leave it at `0` in production or anyone who finds your URL can drive the bot.
- **Client data.** `data/agent.db` and `data/logs/` contain client financial
  information. Do not commit them; back them up somewhere access-controlled.
- **Scale.** SQLite handles thousands of clients fine here. If several
  administrators need simultaneous write access later, `db.py` is the only file
  that needs to change to move to PostgreSQL.

## Scope

This agent collects information. It does not give advice, quote prices, or
generate the plan — the system prompt in `llm.py` explicitly holds it back from
all three, so a client cannot be told something an advisor has not approved.
Writing the actual plan is the advisor's job, using the `business-plan` skill in
the parent repo with the log file as input.
