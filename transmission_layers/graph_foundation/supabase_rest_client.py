import os
import time
import requests
from typing import Any, Dict, List, Optional


class SupabaseRestClient:
    """
    Minimal Supabase REST client.
    Uses REST only. Does not use Supabase Python SDK.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ) -> None:
        self.supabase_url = (supabase_url or os.getenv("SUPABASE_URL") or "").rstrip("/")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        if not self.supabase_url:
            raise ValueError("Missing SUPABASE_URL.")
        if not self.supabase_key:
            raise ValueError("Missing SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY.")

        self.base_rest_url = f"{self.supabase_url}/rest/v1"
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

   def _request(self, method: str, path: str, **kwargs: Any) -> Any:
    url = f"{self.base_rest_url}/{path.lstrip('/')}"

    # allow override headers safely
    request_headers = kwargs.pop("headers", self.headers)

    last_error = None

    for attempt in range(1, self.max_retries + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=request_headers,
                timeout=self.timeout_seconds,
                **kwargs,
            )

            if response.status_code in (200, 201, 204):
                if not response.text:
                    return None
                return response.json()

            last_error = RuntimeError(
                f"Supabase REST error {response.status_code}: {response.text[:2000]}"
            )

        except Exception as exc:
            last_error = exc

        if attempt < self.max_retries:
            time.sleep(min(2 ** attempt, 8))

    raise last_error

    def select(
        self,
        table: str,
        query: str = "select=*",
    ) -> List[Dict[str, Any]]:
        return self._request("GET", f"{table}?{query}") or []

    def upsert(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        on_conflict: str,
    ) -> List[Dict[str, Any]]:
        if not rows:
            return []

        path = f"{table}?on_conflict={on_conflict}"
        headers = dict(self.headers)
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"

        return self._request("POST", path, headers=headers, json=rows) or []

    def insert(
        self,
        table: str,
        rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not rows:
            return []
        return self._request("POST", table, json=rows) or []

    def patch_by_eq(
        self,
        table: str,
        column: str,
        value: str,
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        path = f"{table}?{column}=eq.{value}"
        headers = dict(self.headers)
        headers["Prefer"] = "return=representation"
        return self._request("PATCH", path, headers=headers, json=payload) or []
