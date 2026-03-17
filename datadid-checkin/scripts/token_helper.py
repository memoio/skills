#!/usr/bin/env python3
"""
DataDid token management utility.
Stores access_token and refresh_token. Validates tokens and refreshes when access_token expires.
Usage: python token_helper.py <check|save|get> [access_token] [refresh_token]
"""
import base64
import json
import os
import sys
import time
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "datadid"
TOKEN_FILE = CONFIG_DIR / "tokens.json"
LEGACY_TOKEN_FILE = CONFIG_DIR / "token"

BASE_URL = os.environ.get("DATADID_BASE_URL", "https://data-be.metamemo.one")
REFRESH_URL = f"{BASE_URL.rstrip('/')}/v2/login/refresh"

# Browser-like User-Agent to avoid Cloudflare 403 (Error 1010)
USER_AGENT = os.environ.get(
    "DATADID_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)

# Leeway in seconds before exp to consider token expired (avoid edge cases)
JWT_LEEWAY = 30


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.chmod(0o700)


def _load_tokens():
    """Load tokens from file. Returns (access_token, refresh_token) or (None, None)."""
    if TOKEN_FILE.exists() and TOKEN_FILE.stat().st_size > 0:
        try:
            data = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
            return data.get("access_token"), data.get("refresh_token")
        except (json.JSONDecodeError, KeyError):
            pass
    # Legacy: plain token file (access_token only, no refresh)
    if LEGACY_TOKEN_FILE.exists() and LEGACY_TOKEN_FILE.stat().st_size > 0:
        return LEGACY_TOKEN_FILE.read_text(encoding="utf-8").strip(), None
    return None, None


def _is_jwt_expired(token):
    """
    Parse JWT payload and check if token is expired via exp claim.
    Returns True if expired or unparseable, False if still valid.
    """
    if not token:
        return True
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return True
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
        exp = payload.get("exp")
        if exp is None:
            return False
        return time.time() >= (exp - JWT_LEEWAY)
    except Exception:
        return True


def _is_access_token_valid(access_token):
    """Check if access_token is valid (not expired). Uses JWT exp claim."""
    return not _is_jwt_expired(access_token)


def _refresh_access_token(refresh_token):
    """
    Call POST /v2/login/refresh with refresh_token.
    Returns (success, new_access_token or error_message).
    """
    import urllib.request

    req = urllib.request.Request(
        REFRESH_URL,
        data=b"",
        headers={
            "Authorization": refresh_token,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if body.get("result") != 1:
                return False, body.get("message", "Refresh failed")
            data = body.get("data") or {}
            new_token = data.get("access_token")
            if not new_token:
                return False, "No access_token in refresh response"
            return True, new_token
    except Exception as e:
        return False, str(e)


def _get_valid_access_token():
    """
    Get a valid access_token. If expired, try refresh. Saves new token on refresh.
    Returns (access_token, None) on success, or (None, error_message) on failure.
    """
    access_token, refresh_token = _load_tokens()
    if not access_token:
        return None, "Token not configured"
    if not refresh_token:
        return None, "Refresh token not configured. Please login again."

    if _is_jwt_expired(refresh_token):
        return None, "Refresh token expired. Please login again."

    if _is_access_token_valid(access_token):
        return access_token, None

    success, result = _refresh_access_token(refresh_token)
    if success:
        _save_tokens(result, refresh_token)
        return result, None
    return None, f"Refresh token expired or invalid: {result}"


def _save_tokens(access_token, refresh_token):
    """Save both tokens to file."""
    ensure_config_dir()
    TOKEN_FILE.write_text(
        json.dumps({"access_token": access_token, "refresh_token": refresh_token}, indent=2),
        encoding="utf-8",
    )
    TOKEN_FILE.chmod(0o600)


def save_tokens(access_token, refresh_token):
    """Save both tokens (for use by login.py). No CLI output."""
    _save_tokens(access_token.strip(), refresh_token.strip())


def check():
    """
    Check if tokens exist and are valid.
    Validates access_token; if expired, tries refresh. Fails if refresh_token is expired.
    """
    access_token, refresh_token = _load_tokens()
    if not access_token:
        print("Token not configured")
        sys.exit(1)
    if not refresh_token:
        if _is_access_token_valid(access_token):
            print("Token exists")
            sys.exit(0)
        print("Refresh token not configured. Please login again.")
        sys.exit(1)

    if _is_jwt_expired(refresh_token):
        print("Refresh token expired. Please login again.")
        sys.exit(1)

    if _is_access_token_valid(access_token):
        print("Token exists")
        sys.exit(0)

    success, result = _refresh_access_token(refresh_token)
    if success:
        _save_tokens(result, refresh_token)
        print("Token exists")
        sys.exit(0)

    print("Refresh token expired. Please login again.")
    sys.exit(1)


def save(access_token, refresh_token):
    """Save access_token and refresh_token to local storage."""
    if not access_token or not access_token.strip():
        print("Error: Access token cannot be empty", file=sys.stderr)
        sys.exit(2)
    if not refresh_token or not refresh_token.strip():
        print("Error: Refresh token cannot be empty", file=sys.stderr)
        sys.exit(2)
    _save_tokens(access_token.strip(), refresh_token.strip())
    print("Token saved")


def get():
    """
    Get valid access_token. Refreshes if expired. Used by checkin script.
    Returns token string, or exits with error.
    """
    token, err = _get_valid_access_token()
    if err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(2)
    return token


def main():
    if len(sys.argv) < 2:
        print("Usage: token_helper.py <check|save|get> [access_token] [refresh_token]", file=sys.stderr)
        sys.exit(2)

    cmd = sys.argv[1].lower()

    if cmd == "check":
        check()
    elif cmd == "save":
        if len(sys.argv) < 4:
            print("Usage: token_helper.py save <access_token> <refresh_token>", file=sys.stderr)
            sys.exit(2)
        save(sys.argv[2], sys.argv[3])
    elif cmd == "get":
        token = get()
        print(token)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
