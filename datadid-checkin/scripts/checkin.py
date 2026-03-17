#!/usr/bin/env python3
"""
DataDid check-in script.
Reads local token and calls the check-in API.
"""
import os
import sys
from pathlib import Path


# Add token_helper directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from token_helper import get
except ImportError:
    # Fallback when run as standalone script
    import subprocess
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "token_helper.py"), "get"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Error: Token not configured. Please save DataDid token first.", file=sys.stderr)
        sys.exit(2)
    token = result.stdout.strip()
else:
    token = get()

# ========== Check-in API configuration (modify per platform) ==========
# Example: DataDid check-in endpoint POST /api/checkin
CHECKIN_URL = os.environ.get("DATADID_CHECKIN_URL", "https://data-be.metamemo.one/v2/data/record/add")
# Request header: typically Authorization: Bearer <token> or X-Token: <token>
HEADER_NAME = os.environ.get("DATADID_HEADER_NAME", "Authorization")
HEADER_PREFIX = os.environ.get("DATADID_HEADER_PREFIX", "Bearer ")
USER_AGENT = os.environ.get(
    "DATADID_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)


def do_checkin():
    import urllib.request
    import json

    url = CHECKIN_URL
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        HEADER_NAME: f"{HEADER_PREFIX}{token}".strip(),
    }
    data = json.dumps({"actionid": 70}).encode("utf-8")  # Add request body as needed

    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            try:
                obj = json.loads(body)
                return True, obj
            except json.JSONDecodeError:
                return True, {"raw": body}
    except urllib.error.HTTPError as e:
        return False, {"error": str(e), "code": e.code, "body": e.read().decode("utf-8", errors="replace")}
    except Exception as e:
        return False, {"error": str(e)}


if __name__ == "__main__":
    import json

    success, result = do_checkin()
    if success:
        print("Check-in successful")
        if isinstance(result, dict) and result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Check-in failed:", result.get("error", result), file=sys.stderr)
        if "body" in result:
            print(result["body"], file=sys.stderr)
        sys.exit(1)
