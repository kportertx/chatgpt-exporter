"""HTTP client for ChatGPT backend API with rate limiting and retries."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request


class APIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class FatalAPIError(APIError):
    """Non-retryable error (401, 403)."""


class APIClient:
    def __init__(
        self,
        headers: dict[str, str],
        base_url: str = "https://chatgpt.com",
        rate_limit: float = 3.0,
        max_retries: int = 8,
    ):
        self.headers = headers
        self.base_url = base_url.rstrip("/")
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self._last_request_time: float = 0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.monotonic()

    def get_json(self, path: str, params: dict | None = None) -> dict:
        """GET request with rate limiting and retries. Returns parsed JSON."""
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)

        for attempt in range(self.max_retries + 1):
            self._throttle()

            req = urllib.request.Request(url)
            for key, value in self.headers.items():
                req.add_header(key, value)

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    raise FatalAPIError(
                        f"HTTP {e.code}: {e.reason}. Check your token/workspace.",
                        status_code=e.code,
                    ) from e
                if e.code == 404:
                    raise APIError(
                        f"HTTP 404: Not found ({path})", status_code=404
                    ) from e
                if e.code == 429 or e.code >= 500:
                    if attempt < self.max_retries:
                        retry_after = e.headers.get("Retry-After")
                        delay = (
                            float(retry_after)
                            if retry_after
                            else min(2 ** (attempt + 1), 120)
                        )
                        if e.code == 429:
                            # Permanently slow down to avoid repeated throttling
                            self.rate_limit = min(self.rate_limit * 1.5, 30)
                            print(f"  HTTP 429, retrying in {delay:.0f}s (rate limit now {self.rate_limit:.1f}s)...")
                        else:
                            print(f"  HTTP {e.code}, retrying in {delay:.0f}s...")
                        time.sleep(delay)
                        continue
                raise APIError(f"HTTP {e.code}: {e.reason}", status_code=e.code) from e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                if attempt < self.max_retries:
                    delay = min(2 ** (attempt + 1), 60)
                    print(f"  Network error, retrying in {delay:.0f}s...")
                    time.sleep(delay)
                    continue
                raise APIError(f"Network error: {e}") from e

        raise APIError(f"Max retries exceeded for {path}")

    # --- Convenience methods ---

    def list_conversations(self, offset: int = 0, limit: int = 28) -> dict:
        return self.get_json(
            "/backend-api/conversations", {"offset": offset, "limit": limit}
        )

    def get_conversation(self, conversation_id: str) -> dict:
        return self.get_json(f"/backend-api/conversation/{conversation_id}")

    def list_projects(self) -> list[dict]:
        data = self.get_json("/backend-api/gizmos/snorlax/sidebar")
        return data.get("items", [])

    def list_project_conversations(
        self, gizmo_id: str, cursor: int = 0
    ) -> dict:
        return self.get_json(
            f"/backend-api/gizmos/{gizmo_id}/conversations", {"cursor": cursor}
        )
