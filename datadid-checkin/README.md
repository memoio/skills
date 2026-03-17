# DataDid Check-in Skill

An Agent skill for DataDid authentication and daily check-in. Supports email+verification code login, DataDID points check-in, and AliveCheck.

**GitHub**: [memoio/skills](https://github.com/memoio/skills) | [中文文档](docs/README_zh.md)

---

## Installation

### Prerequisites

- Python 3.6+
- Claude-cli

### Clone & Install

```bash
# Clone the skills repo
git clone https://github.com/memoio/skills.git
cd skills

# Copy datadid-checkin to Claude skills directory
mkdir -p ~/.claude/skills
cp -r datadid-checkin ~/.claude/skills/
```

To install for a specific project instead of globally, copy to `your-project/.claude/skills/`.

---

### Install via Claude

You can start Claude and install through conversation:

```bash
# Start Claude
claude

# Ask Claude to install
Help me install all skills from https://github.com/orgs/memoio/skills
```

---

## Usage

After installation, you can talk directly to the agent:

- "Help me log in to DataDid with alice@example.com"
- "Show my DataDid info"
- "Check my AliveCheck status"
- "Check in for me on DataDid"
- "Complete my AliveCheck check-in"

### Command Line

You can also run scripts from the command line. Commands are run from the skill directory (`~/.claude/skills/datadid-checkin/`). Paths below are relative to it.

### Login

**Email + verification code** (recommended):

```bash
# 1. Send verification code
python scripts/login.py send_code example@example.com

# 2. Login with code (after receiving email)
python scripts/login.py login example@example.com 123456
```

**Manual token** (if you have access_token and refresh_token):

```bash
python scripts/token_helper.py save <ACCESS_TOKEN> <REFRESH_TOKEN>
```

Tokens are stored in `~/.config/datadid/tokens.json`.

### Check-in

**DataDID points check-in**:

```bash
python scripts/checkin.py
```

**AliveCheck check-in**:

```bash
python scripts/alive_checkin.py checkin
# Optional: with coordinates
python scripts/alive_checkin.py checkin 31.2304 121.4737
```

### Status

**Check if logged in**:

```bash
python scripts/token_helper.py check
```

**AliveCheck status** (subscription, today_checked, consecutive_days):

```bash
python scripts/alive_checkin.py status
```

**AliveCheck profile** (display name):

```bash
python scripts/alive_checkin.py profile
```

### DataDid Info

Aggregated user profile, today's points check-in status, and AliveCheck status:

```bash
python scripts/datadid_info.py
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/login.py` | Email + verification code login (`send_code`, `login`) |
| `scripts/token_helper.py` | Token check, save, get; auto-refreshes when expired |
| `scripts/checkin.py` | DataDID points check-in |
| `scripts/alive_checkin.py` | AliveCheck: `checkin`, `status`, `profile` |
| `scripts/datadid_info.py` | Aggregated DataDid info (user profile, today's points check-in, AliveCheck status) |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATADID_BASE_URL` | `https://data-be.metamemo.one` | DataDID API base URL |
| `DATADID_SOURCE` | `Agent` | Source identifier for login |
| `DATADID_USER_AGENT` | Chrome-like UA | Override if Cloudflare blocks (e.g. 403) |
| `DATADID_CHECKIN_URL` | `https://data-be.metamemo.one/v2/data/record/add` | Check-in endpoint |
| `DATADID_RECORD_ACTION_ID` | `70` | Action ID for points check-in |
| `ALIVECHECK_BASE_URL` | `http://localhost:8081` | AliveCheck service URL |
| `ALIVECHECK_LATITUDE` | - | Optional latitude for AliveCheck |
| `ALIVECHECK_LONGITUDE` | - | Optional longitude for AliveCheck |

---

## API Reference

- [DataDID API Docs](https://memolabs.gitbook.io/datadid-developer-platform/en/api)
- [MemoLabs](https://memolabs.org)
- [Sample Code](https://github.com/memoio/call-datadid-demo)
