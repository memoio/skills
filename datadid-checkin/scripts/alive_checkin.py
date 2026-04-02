#!/usr/bin/env python3
"""
AliveCheck script: check-in, status.
Uses DataDID access token. API: data-did/AliveCheck/docs/API.md
"""
import json
import os
import sys
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

# Use same base URL as DataDID API (alive-check is served under same backend)
ALIVE_CHECK_BASE = os.environ.get("ALIVE_CHECK_BASE_URL", "https://datadid-alivecheck.memolabs.net")
BASE_URL = f"{ALIVE_CHECK_BASE.rstrip('/')}/v2/alive-check"
USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)

def _request(method, path, data=None):
    """Make authenticated request. Returns (success, result_dict)."""
    import urllib.request

    url = f"{BASE_URL}{path}"
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {token}", 
        "User-Agent": USER_AGENT
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            return False, json.loads(err_body)
        except json.JSONDecodeError:
            return False, {"result": -1, "error": err_body}
    except Exception as e:
        return False, {"result": -1, "error": str(e)}


def get_status():
    """GET /status - subscription and today check-in status."""
    return _request("GET", "/status")


def do_alive_checkin(latitude=None, longitude=None):
    """POST /checkin. Returns (success, result_dict)."""
    body = {}
    if latitude is not None:
        body["latitude"] = float(latitude)
    if longitude is not None:
        body["longitude"] = float(longitude)
    data = json.dumps(body).encode("utf-8")
    success, result = _request("POST", "/checkin", data)
    return result.get("result") == 0, result


if __name__ == "__main__":
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "checkin").lower()

    if cmd == "status":
        success, result = get_status()
        if success and result.get("result") == 0:
            data = result.get("data", {})
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(result.get("error", result), file=sys.stderr)
            sys.exit(1)

    else:
        lat = os.environ.get("ALIVECHECK_LATITUDE")
        lng = os.environ.get("ALIVECHECK_LONGITUDE")
        if cmd == "checkin" and len(sys.argv) >= 4:
            try:
                lat, lng = float(sys.argv[2]), float(sys.argv[3])
            except (ValueError, IndexError):
                pass
        elif cmd != "checkin" and len(sys.argv) >= 3:
            try:
                lat, lng = float(sys.argv[1]), float(sys.argv[2])
            except (ValueError, IndexError):
                pass

        success, result = do_alive_checkin(lat, lng)
        if success:
            print("AliveCheck check-in successful")
            data = result.get("data", {})
            if data:
                print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            err = result.get("error", result)
            print(f"AliveCheck check-in failed: {err}", file=sys.stderr)
            sys.exit(1)
