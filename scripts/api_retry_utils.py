import time
import random
from typing import Optional, Dict, Any

import requests


RETRY_STATUS_CODES = {408, 429, 500, 502, 503, 504}


def request_with_retries(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_payload: Optional[Any] = None,
    data: Optional[Any] = None,
    timeout: int = 60,
    max_attempts: int = 3,
    base_sleep_seconds: float = 2.0,
    service_name: str = "API",
) -> requests.Response:
    """
    Production-safe HTTP retry wrapper.

    Retries on:
    - timeout
    - connection errors
    - 408 request timeout
    - 429 rate limit
    - 5xx transient server errors

    Does NOT retry normal 4xx errors except 408/429.
    """

    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json_payload,
                data=data,
                timeout=timeout,
            )

            if response.status_code not in RETRY_STATUS_CODES:
                return response

            last_error = (
                f"{service_name} returned retryable status "
                f"{response.status_code}: {response.text[:500]}"
            )

        except requests.exceptions.RequestException as exc:
            last_error = f"{service_name} request exception: {exc}"

        if attempt < max_attempts:
            sleep_time = base_sleep_seconds * (2 ** (attempt - 1))
            sleep_time += random.uniform(0, 1.5)

            print(
                f"[WARN] {service_name} request failed on attempt "
                f"{attempt}/{max_attempts}. Retrying in {sleep_time:.1f}s..."
            )

            time.sleep(sleep_time)

    raise RuntimeError(
        f"{service_name} request failed after {max_attempts} attempts. "
        f"Last error: {last_error}"
    )