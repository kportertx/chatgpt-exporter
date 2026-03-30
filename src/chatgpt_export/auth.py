"""Authentication: token exchange and header construction."""

from __future__ import annotations

import json
import urllib.request


class AuthError(Exception):
    pass


def exchange_session_token(session_token: str, base_url: str) -> str:
    """Exchange a session cookie for an access token."""
    url = f"{base_url}/api/auth/session"
    req = urllib.request.Request(url)
    req.add_header("Cookie", f"__Secure-next-auth.session-token={session_token}")
    req.add_header("User-Agent", "chatgpt-export/0.1")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        raise AuthError(f"Failed to exchange session token: {e}") from e

    access_token = data.get("accessToken")
    if not access_token:
        raise AuthError("No accessToken in session response. Token may be expired.")
    return access_token


def build_headers(access_token: str, workspace_id: str | None = None) -> dict[str, str]:
    """Build request headers for backend API calls."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "chatgpt-export/0.1",
    }
    if workspace_id:
        headers["ChatGPT-Account-Id"] = workspace_id
    return headers
