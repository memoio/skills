---
name: datadid-checkin
description: Manages DataDid token via email login and performs daily check-in via script. Use when user mentions DataDid, check-in, datadid login, or wants to login/configure DataDid and execute check-in through agent conversation.
---

# DataDid Check-in Skill

Manages DataDid authentication (email + verification code login) and check-in flow through conversation.

## Workflow

### Step 1: Login (Email + Verification Code)

**Preferred method**: Use email + verification code login instead of pasting token.

1. **Check if already logged in**

   - Run: `python scripts/token_helper.py check`
   - If "Token exists", proceed to Step 2 (Execute Check-in)
   - If "Token not configured", proceed with login

2. **Send verification code**
   - Ask the user for their DataDid account email
   - Run: `python scripts/login.py send_code <EMAIL>`
   - On success, tell the user: "Verification code sent. Please check your email and provide the code."

3. **Complete login with code**
   - When the user provides the verification code (e.g. "123456")
   - Run: `python scripts/login.py login <EMAIL> <CODE>`
   - On success, token is saved locally. Inform the user "Login successful."

4. **Alternative: Manual token** (if user prefers)
   - If the user provides both access_token and refresh_token: `python scripts/token_helper.py save <ACCESS_TOKEN> <REFRESH_TOKEN>`

API reference: [DataDID Developer Platform](https://memolabs.gitbook.io/datadid-developer-platform/en/api) — `POST /v2/login/email/code` and `POST /v2/login/email`.

### Step 2: Execute Check-in

1. **Pre-check**: Ensure token exists (run Step 1 check)
2. **Choose check-in type**:
   - **DataDID points** (action record): `python scripts/checkin.py`
   - **AliveCheck** (daily alive check): `python scripts/alive_checkin.py` or `python scripts/alive_checkin.py checkin`
3. **AliveCheck status & profile**:
   - Status (subscription + today check-in): `python scripts/alive_checkin.py status`
   - Profile (display name): `python scripts/alive_checkin.py profile`
4. **Parse output**: Reply to the user based on success/failure from the script output

## Trigger Scenarios

- User says "DataDid check-in", "check in for me", "execute check-in", "AliveCheck check-in", "alive check", "check-in status", "AliveCheck profile"
- User asks "DataDid info", "show my DataDid", "DataDid profile", "my check-in status", "DataDid status"
- User says "DataDid login", "log in to DataDid", "I want to login"
- User asks "DataDid token", "how to configure DataDid", "save my token"
- User provides email and wants to login

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/login.py` | Email + verification code login (send_code, login) |
| `scripts/token_helper.py` | Check, save, read token; validates and auto-refreshes when access_token expires |
| `scripts/checkin.py` | DataDID points check-in (POST /v2/data/record/add) |
| `scripts/alive_checkin.py` | AliveCheck: checkin, status, profile |
| `scripts/datadid_info.py` | Aggregated DataDid info: user profile, points check-in today, AliveCheck status |

Paths are relative to the skill directory: `datadid-checkin/`.

## Check-in APIs

- **DataDID**: `POST /v2/data/record/add` — [DataDID API](https://memolabs.gitbook.io/datadid-developer-platform/en/api)
- **AliveCheck**: `POST /v2/alive-check/checkin`

### Step 3: Show DataDid Info

When the user wants to see their DataDid information:

1. Run: `python scripts/datadid_info.py`
2. This aggregates:
   - **DataDID user profile** — `GET /v2/user/info` (name, icon, address, did, email, etc.)
   - **Today's points check-in** — `GET /v2/data/record/:actionID` (whether daily points action is completed today)
   - **AliveCheck status** — `GET /v2/alive-check/status` (subscription, today_checked, consecutive_days, etc.)
3. Reply to the user with a summary of the combined output
