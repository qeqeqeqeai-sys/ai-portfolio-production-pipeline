import os
import time
from typing import Any, Dict, List, Optional

import requests


class SupabaseRestClient:
    """
    Shared Supabase REST client for graph foundation pipelines.

    Supports:
    - select
    - insert
    - upsert
    - update

    Uses Supabase REST API only.
    No Supabase Python SDK.
    """

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not self.url:
            raise RuntimeError("Missing SUPABASE_URL")

        if not self.key:
            raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY")

        self.base_url = self.url.rstrip("/") + "/rest/v1"

        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, str]] = None,
        json_body: Optional[Any] = None,
        prefer: Optional[str] = None,
        timeout: int = 60,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"

        headers = dict(self.headers)

        if prefer:
            headers["Prefer"] = prefer

        last_error = None

        for attempt in range(3):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=timeout,
                )

                if response.status_code in (200, 201, 204):
                    if response.text:
                        return response.json()
                    return []

                last_error = f"{response.status_code}: {response.text}"

            except Exception as exc:
                last_error = str(exc)

            time.sleep(1.5 * (attempt + 1))

        raise RuntimeError(
            f"Supabase REST request failed: {method} {url}: {last_error}"
        )

    def select(
        self,
        table: str,
        *,
        columns: str = "*",
        filters: Optional[Dict[str, str]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, str] = {"select": columns}

        if filters:
            params.update(filters)

        if order:
            params["order"] = order

        if limit is not None:
            params["limit"] = str(limit)

        return self._request(
            "GET",
            table,
            params=params,
        )

    def insert(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        *,
        return_rows: bool = False,
    ) -> List[Dict[str, Any]]:
        if not rows:
            return []

        return self._request(
            "POST",
            table,
            json_body=rows,
            prefer="return=representation" if return_rows else "return=minimal",
        )

    def upsert(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        *,
        on_conflict: str,
        return_rows: bool = False,
    ) -> List[Dict[str, Any]]:
        if not rows:
            return []

        return self._request(
            "POST",
            table,
            params={"on_conflict": on_conflict},
            json_body=rows,
            prefer=(
                "resolution=merge-duplicates,"
                + ("return=representation" if return_rows else "return=minimal")
            ),
        )

    def update(
        self,
        table: str,
        filters: Dict[str, str],
        values: Dict[str, Any],
        *,
        return_rows: bool = False,
    ) -> List[Dict[str, Any]]:
        if not filters:
            raise RuntimeError("Update requires filters to avoid accidental full-table update.")

        return self._request(
            "PATCH",
            table,
            params=filters,
            json_body=values,
            prefer="return=representation" if return_rows else "return=minimal",
        )
