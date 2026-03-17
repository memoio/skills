#!/usr/bin/env python3
"""
DataDid info: aggregates user profile, today's check-in status, and AliveCheck status.
API reference: https://memolabs.gitbook.io/datadid-developer-platform/en/api

- GET /v2/user/info: user profile (name, icon, address, did, email, etc.)
- GET /v2/data/record/:actionID: whether today's points check-in is done
- AliveCheck GET /status: subscription and today check-in status
"""
import json
import os
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from token_helper import get
except ImportError:
    import subprocess
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "token_helper.py"), "get"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Error: Token not configured. Please login first.", file=sys.stderr)
        sys.exit(2)
    token = result.stdout.strip()
else:
    token = get()

# DataDID API
DATADID_BASE = os.environ.get("DATADID_BASE_URL", "https://data-be.metamemo.one")
USER_INFO_URL = f"{DATADID_BASE.rstrip('/')}/v2/user/info"
# Action ID for daily points check-in (same as checkin.py)
RECORD_ACTION_ID = int(os.environ.get("DATADID_RECORD_ACTION_ID", "70"))
RECORD_URL = f"{DATADID_BASE.rstrip('/')}/v2/data/record/{RECORD_ACTION_ID}"

# AliveCheck
ALIVECHECK_BASE = os.environ.get("ALIVECHECK_BASE_URL", "http://localhost:8081")
ALIVECHECK_STATUS_URL = f"{ALIVECHECK_BASE.rstrip('/')}/v2/alive-check/status"

USER_AGENT = os.environ.get(
    "DATADID_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)


def _get(url, headers=None):
    """GET request. Returns (success, result_dict or error_msg)."""
    import urllib.request

    h = {"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            return False, json.loads(err_body)
        except json.JSONDecodeError:
            return False, {"error": err_body}
    except Exception as e:
        return False, {"error": str(e)}


def _is_today(timestamp):
    """Check if Unix timestamp is today (UTC)."""
    if timestamp is None:
        return False
    t = time.gmtime(int(timestamp))
    today = time.gmtime()
    return (t.tm_year, t.tm_yday) == (today.tm_year, today.tm_yday)


def fetch_user_info():
    """GET /v2/user/info. Returns (success, data or error)."""
    ok, resp = _get(USER_INFO_URL)
    if not ok:
        return False, resp
    if resp.get("result") != 1:
        return False, resp.get("data") or resp.get("message", str(resp))
    return True, resp.get("data", {})


def fetch_today_checkin_status():
    """
    GET /v2/data/record/:actionID. Check if today's points check-in is done.
    Returns (success, is_checked_today, record_or_msg).
    """
    ok, resp = _get(RECORD_URL)
    if not ok:
        return False, False, resp
    if resp.get("result") != 1:
        return True, False, None
    data = resp.get("data")
    if not data:
        return True, False, None
    ts = data.get("time")
    is_today = _is_today(ts)
    return True, is_today, data


def fetch_alivecheck_status():
    """AliveCheck GET /status. Returns (success, data or error)."""
    ok, resp = _get(ALIVECHECK_STATUS_URL)
    if not ok:
        return False, resp
    if resp.get("result") != 0:
        return False, resp.get("error", resp)
    return True, resp.get("data", {})


def fetch_all():
    """
    Fetch all DataDid info and return a combined structure.
    """
    out = {"user_info": None, "points_checkin_today": None, "alivecheck": None}

    # 1. User profile (GET /v2/user/info)
    ok, data = fetch_user_info()
    if ok:
        out["user_info"] = data
    else:
        out["user_info_error"] = str(data) if not isinstance(data, dict) else data.get("error", data)

    # 2. Today's points check-in (GET /v2/data/record/:actionID)
    ok, is_today, rec = fetch_today_checkin_status()
    if ok:
        out["points_checkin_today"] = is_today
        if rec:
            out["points_record"] = rec
    else:
        out["points_checkin_error"] = str(rec) if not isinstance(rec, dict) else rec.get("error", rec)

    # 3. AliveCheck status (GET /status)
    ok, data = fetch_alivecheck_status()
    if ok:
        out["alivecheck"] = data
    else:
        out["alivecheck_error"] = str(data) if not isinstance(data, dict) else data.get("error", data)

    return out


if __name__ == "__main__":
    result = fetch_all()
    print(json.dumps(result, ensure_ascii=False, indent=2))
