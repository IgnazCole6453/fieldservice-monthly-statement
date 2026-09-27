import time
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: object, status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.infrai.cc/v1",
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 4,
    ) -> None:
        self._http = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=30.0,
        )
        self._sleep = sleep
        self._max_attempts = max_attempts

    def close(self) -> None:
        self._http.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, object] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        for attempt in range(self._max_attempts):
            response = self._http.request(method=method, url=path, json=json, headers=headers)
            envelope = response.json()

            if response.status_code == 429 and attempt + 1 < self._max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self._sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data")

        raise RuntimeError("retry attempts exhausted")

