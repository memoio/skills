#!/usr/bin/env python3
"""
DataDid email + verification code login.
Usage:
  python login.py send_code <email>     - Send verification code to email
  python login.py login <email> <code> - Login with email and code, save token
"""
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from token_helper import save_tokens

# DataDID API base URL (https://memolabs.gitbook.io/datadid-developer-platform/en/api)
BASE_URL = os.environ.get("DATADID_BASE_URL", "https://data-be.metamemo.one")
CODE_URL = f"{BASE_URL.rstrip('/')}/v2/login/email/code"
LOGIN_URL = f"{BASE_URL.rstrip('/')}/v2/login/email"
SOURCE = os.environ.get("DATADID_SOURCE", "Agent")

# Browser-like User-Agent to avoid Cloudflare 403 (Error 1010: browser_signature_banned)
USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)

def _post(url: str, data: dict, headers=None):
    """POST JSON and return (success, response_dict)."""
    import urllib.request

    req_data = json.dumps(data).encode("utf-8")
    req_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, application/hal+json",
        "User-Agent": USER_AGENT,
    }
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, data=req_data, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return True, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return False, json.loads(body)
        except json.JSONDecodeError:
            return False, {"result": 0, "message": body}
    except Exception as e:
        return False, {"result": 0, "message": str(e)}


def send_code(email: str) -> tuple[bool, str]:
    """
    Send verification code to email.
    POST /v2/login/email/code
    Returns (success, message).
    """
    success, resp = _post(CODE_URL, {"email": email})
    if not success:
        return False, resp.get("message", str(resp))
    if resp.get("result") != 1:
        return False, resp.get("message", "Failed to send code")
    return True, "Verification code sent. Check your email."


def login_with_code(email: str, code: str) -> tuple[bool, str]:
    """
    Login with email and verification code.
    POST /v2/login/email
    Returns (success, message). On success, saves access_token locally.
    """
    success, resp = _post(
        LOGIN_URL,
        {"email": email, "code": code, "source": SOURCE},
    )
    if not success:
        return False, resp.get("message", str(resp))
    if resp.get("result") != 1:
        return False, resp.get("message", "Login failed")
    data = resp.get("data") or {}
    access_token = data.get("accessToken")
    refresh_token = data.get("refreshToken")
    if not access_token:
        return False, "No accessToken in response"
    if not refresh_token:
        return False, "No refreshToken in response"
    save_tokens(access_token, refresh_token)
    return True, "Login successful. Token saved."


def main():
    if len(sys.argv) < 2:
        print("Usage: login.py send_code <email> | login.py login <email> <code>", file=sys.stderr)
        sys.exit(2)

    cmd = sys.argv[1].lower()

    if cmd == "send_code":
        if len(sys.argv) < 3:
            print("Usage: login.py send_code <email>", file=sys.stderr)
            sys.exit(2)
        email = sys.argv[2].strip()
        success, msg = send_code(email)
        if success:
            print(msg)
        else:
            print(f"Error: {msg}", file=sys.stderr)
            sys.exit(1)
    elif cmd == "login":
        if len(sys.argv) < 4:
            print("Usage: login.py login <email> <code>", file=sys.stderr)
            sys.exit(2)
        email = sys.argv[2].strip()
        code = sys.argv[3].strip()
        success, msg = login_with_code(email, code)
        if success:
            print(msg)
        else:
            print(f"Error: {msg}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
