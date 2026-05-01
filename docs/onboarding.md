# Student Onboarding Guide

## For Administrators

### 1. Prerequisites

- GCP project with Compute Engine enabled
- `gcloud` CLI installed and authenticated
- An Anthropic API key
- A Discord bot token for the student (see Discord Bot Setup below)
- The Virtual TA's MCP endpoint URL

### 2. Create a Discord Bot

1. Go to https://discord.com/developers/applications
2. Click **New Application** and name it (e.g., "CSE452 TA — Alice")
3. Go to **Bot** > click **Reset Token** > copy the token
4. Uncheck **Public Bot**
5. Enable **Message Content Intent** under Privileged Gateway Intents
6. Go to **Installation** > set Install Link to **None**
7. Go to **OAuth2 > URL Generator** > check **bot** scope
8. Under bot permissions, check **Send Messages**, **Read Message History**, **Attach Files**
9. Copy the generated URL and send it to the student to invite the bot to their server

### 3. Provision the VM

```bash
cd provisioning/

./provision-student.sh \
  --project my-project-123 \
  --zone us-west1-c \
  --service-account 123456-compute@developer.gserviceaccount.com \
  --vm-name nanoclaw-alice \
  --discord-token "MTQ4OD..." \
  --anthropic-key "sk-ant-..." \
  --virtual-ta-url "http://<virtual-ta-host>:8000"
```

### 4. Pair the Student

1. Tell the student to DM the bot on Discord
2. The bot replies with a pairing code
3. Approve the pairing:

```bash
gcloud compute ssh nanoclaw-alice --project=my-project-123 --zone=us-west1-c
cd ~/nanoclaw && docker compose -f docker-compose.yml run --rm nanoclaw-cli pairing approve discord <CODE>
```

---

## For Students

### 1. Get Started

Your personal AI assistant is a Discord bot. DM it to start chatting.

### 2. Connect Your Tools

On first use, the agent will ask you to connect your accounts:

**EdStem:**
1. Go to https://edstem.org/us/settings/api-tokens
2. Generate a new API token
3. DM the bot: "Connect my Ed account" and paste the token when asked

**Canvas:**
The agent will send you an authorization link. Click it, log in with your UW account, and approve access.

**Google Workspace:**
Same flow — click the authorization link, log in with your Google account, and approve.

### 3. What You Can Ask

- "What's due this week?" (Canvas)
- "Explain the CAP theorem" (Virtual TA with lecture slides)
- "What's new on Ed?" (EdStem)
- "When is the midterm?" (EdStem + Virtual TA)
- "What's my grade in CSE 452?" (Canvas)
- "Help me study for the midterm" (combines Canvas + EdStem + Virtual TA)
- "Create a study doc for Paxos" (Google Docs + Virtual TA)
