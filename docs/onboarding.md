# Onboarding Guide

This document covers two flows:

1. **Course staff** — provision a per-student VM running NanoClaw +
   the Student Assistant MCP servers, and pair the bot with the
   student's Discord account.
2. **Students** — accept the bot invite, DM it, connect Ed/Canvas/
   Google, and start asking questions.

---

## For Course Staff

### What you'll provision (per student)

A dedicated GCP VM running:
- NanoClaw (the per-student agent host) listening on the loopback
  gateway, with a Discord channel adapter
- A small Python venv shipping the EdStem and Gradescope MCP servers
- mcporter wired to the shared Virtual TA HTTP MCP endpoint, plus the
  per-student stdio MCP servers above

Each student's VM is independent — token leaks, OOMs, or noisy-
neighbor effects are bounded to one student. The shared Virtual TA
backend is the only multi-tenant component, and per-user
authorization is enforced at the MCP layer (see ChatCSE
`backend/app/mcp_server.py::get_playback`).

### Prerequisites

- GCP project with Compute Engine enabled
- `gcloud` CLI installed and authenticated (`gcloud auth login`)
- An Anthropic API key (per-student or shared with rate limits)
- A Discord bot **per student** — see [Discord Bot Setup](#discord-bot-setup) below
- The deployed Virtual TA URL (e.g.
  `https://chatcse.example.com`) — the MCP endpoint is at `/mcp` on
  port 8001 of that host

### Discord Bot Setup

One application per student. Reusing one bot across students is not
supported — each Discord application's token is what NanoClaw uses
to identify which student is messaging.

1. https://discord.com/developers/applications → **New Application**
   (e.g. "CSE 452 TA — Alice")
2. **Bot** tab → **Reset Token** → copy the token (you will paste it
   into `--discord-token` below; it's never persisted by the
   provisioning script)
3. Uncheck **Public Bot**
4. **Privileged Gateway Intents** → enable **Message Content Intent**
5. **Installation** → set Install Link to **None**
6. **OAuth2 → URL Generator** → check **bot** scope, then under bot
   permissions check **Send Messages**, **Read Message History**,
   **Attach Files**
7. Send the generated URL to the student so they invite the bot to a
   server they own (or to themselves for DMs only — Discord requires
   an invite even for DMs)

### Provisioning a student VM

```bash
cd provisioning/

./provision-student.sh \
  --project my-project-123 \
  --zone us-west1-c \
  --service-account 123456-compute@developer.gserviceaccount.com \
  --vm-name nanoclaw-alice \
  --discord-token "MTQ4OD..." \
  --anthropic-key "sk-ant-..." \
  --virtual-ta-url "https://chatcse.example.com" \
  [--ed-token "<student's ed token>"] \
  [--ed-course-id 12345] \
  [--composio-key "<composio-mcp-key>"]
```

The script installs Docker, Node 22, Python 3.13, clones
[qwibitai/nanoclaw](https://github.com/qwibitai/nanoclaw), runs
NanoClaw's onboard flow non-interactively with the student's
Anthropic key, registers the Discord channel, then clones this repo
to `~/student-assistant` for the custom MCP servers.

Total wall time is 5–10 minutes per VM. The VM is
billable from this point — `gcloud compute instances stop <vm-name>`
when not in use.

### Pairing the student's Discord account

NanoClaw doesn't trust an inbound Discord DM until the sending user
is paired with the bot. This is a one-shot per student:

1. Tell the student to open Discord, find the bot in their server or
   DM list, and **DM the bot** with anything (e.g. "hi")
2. The bot replies with a 6-digit pairing code
3. Approve from the VM:

```bash
gcloud compute ssh nanoclaw-alice --project=my-project-123 --zone=us-west1-c
cd ~/nanoclaw && \
  docker compose -f docker-compose.yml run --rm nanoclaw-cli \
    pairing approve discord <CODE>
```

After this the bot will respond to the student's DMs.

### Verifying the deploy

From the VM:

```bash
# 1. NanoClaw process up
ps aux | grep -E "node.*dist/index" | grep -v grep    # exactly 1 line

# 2. PID lock present (prevents multi-instance races)
cat ~/nanoclaw/data/nanoclaw.pid                       # numeric PID

# 3. Discord adapter listening
docker logs $(docker ps --filter name=nanoclaw -q) | grep "Discord Gateway connected"

# 4. Virtual TA reachable from the VM
curl -fsS "${VIRTUAL_TA_URL}/health"                   # {"status":"healthy",...}
```

Smoke test the full chain by DMing the bot a course question (e.g.
"What is Paxos?"). Within 60–120 s the bot should reply with a
verbatim transcript, attach an audio MP3, and attach the cited slide
PNGs in citation order. If it doesn't:

- Container OOMing → check `docker stats` and `dmesg`. The container
  is capped at 2 GB by default; override via
  `NANOCLAW_CONTAINER_MEMORY=4g` in `~/nanoclaw/.env` and restart.
- "Not logged in / Please run /login" → the OneCLI gateway didn't
  apply. `docker ps --filter name=onecli` should show it healthy.
  Restart NanoClaw if not.
- Bot replies but with no attachments → the Virtual TA backend is
  reachable but its TTS/slide pipeline is failing. Check the backend
  logs (`grep "MCP\] Audio" backend.log`).

### Lifecycle

| Action | Command |
|---|---|
| SSH | `gcloud compute ssh <vm-name> --project=<p> --zone=<z>` |
| Stop (preserves disk, halts billing) | `gcloud compute instances stop <vm-name> ...` |
| Restart | `gcloud compute instances start <vm-name> ...` |
| Tear down | `gcloud compute instances delete <vm-name> ...` |

After a restart, NanoClaw and the OneCLI gateway should auto-start.
If not:

```bash
cd ~/nanoclaw && docker compose -f docker-compose.yml up -d
```

---

## For Students

### Step 1 — Accept the bot invite

Course staff will share an invite URL. Click it, log in to Discord,
and add the bot to a server you own (or make a private server with
just you for the bot to live in). Then DM the bot — anything works
for the first message ("hi", "hello").

The bot will reply with a 6-digit code. Share that code with course
staff. They'll approve the pairing, and from then on the bot will
respond to your messages.

### Step 2 — Connect your accounts

The first time you DM the bot, it'll ask you to connect the tools
you want to use. None of these are required, but each one expands
what the bot can do for you.

**EdStem** (recommended — needed for course logistics + announcements)

1. Go to https://edstem.org/us/settings/api-tokens
2. Click **New Token** → copy the token
3. DM the bot: `/connect-ed <paste-token-here>`

**Canvas / Google Workspace** (optional — for assignments, calendar,
Docs)

The bot will send you an authorization link the first time you ask
something that needs Canvas or Google. Click it, sign in, and
approve. Tokens are scoped to your account.

### Step 3 — Ask things

Plain English. Some patterns that work well:

| You ask… | The bot pulls from… |
|---|---|
| "What is Paxos?" | ChatCSE Virtual TA → orchestrator → DnH pipeline → returns transcript + audio + slide PNGs |
| "When is the midterm?" | Virtual TA admin pipeline → fetches course website + searches Ed |
| "What's new on Ed?" | Your personal EdStem MCP server (uses your token, not staff's) |
| "What's due this week?" | Canvas via Composio |
| "Explain accept-phase to me again" | Multi-turn — the bot remembers the last few turns of context |

### What to expect on a course-content question

Typical timing:
- ~5 s: bot acknowledges
- ~50–90 s: orchestrator runs RAG against lecture slides + transcripts
- ~10–20 s: TTS + slide PNG export
- Final message in the DM: text transcript + 1 MP3 + N slide images

If you hit "rate limited" — by default the cap is 10 questions per
minute per student. That's a defense against runaway agents looping;
in normal use you should never see it.

If something looks wrong, tell course staff your VM name (your bot
should know — ask "what VM am I on?").

---

## Architecture cheat sheet

```
You (Discord DM)
   │
   ▼
Discord Gateway ── (your bot token) ──► your VM
                                            │
                            ┌───────────────┘
                            ▼
                   NanoClaw host (Node)   ◄── PID lock prevents zombies
                            │                   (single instance per VM)
                            ▼
                   per-student container (Docker, 2 GB cap)
                            │
                            ▼
                   Claude SDK + mcporter
                            │
              ┌─────────────┼──────────────────────┐
              ▼             ▼                      ▼
   stdio MCP: EdStem    HTTPS MCP: Virtual TA   stdio MCP: Gradescope
   (your Ed token)      (per-user auth via      (Canvas LTI)
                        Supabase JWT, owned-
                        response gate, signed
                        media URLs)
                            │
                            ▼
                   ChatCSE backend (FastAPI, Postgres)
                   ├── Orchestrator (plan/execute/synthesize)
                   ├── DnH pipeline (RAG over slides + transcripts)
                   ├── Admin pipeline (fetch + Ed search)
                   ├── TTS service (Google Cloud)
                   └── Slide exporter (PyMuPDF)
```

The shared Virtual TA is the only multi-tenant component. Per-user
isolation guarantees:
- `ask_question` writes Question/Response under the authenticated
  user's id (resolved from Supabase JWT)
- `get_playback` rejects response_ids that don't belong to the
  caller (ownership check)
- Per-response audio + slide directories
  (`selected_slides/response_<id>/`) so concurrent students never
  see each other's media
- HMAC-signed media URLs with 10-minute expiry, signed against
  `SECRET_KEY` (boot fails fast if `SECRET_KEY` is the default
  placeholder outside DEV)
- Per-user MCP rate limit (10/min default, configurable; backend can
  be in-memory for single-host or DB-backed for multi-host —
  `MCP_ASK_RATE_BACKEND=database`)
- Stale media swept every hour, deleted after 24 h
