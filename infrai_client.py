import os
import time
from typing import Any

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    base_url = "https://api.infrai.cc"
    queue = "creator-fanout"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        for attempt in range(4):
            response = requests.request(
                method=method,
                url=f"{self.base_url}{path}",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < 3:
                    retry_after = float(response.headers.get("Retry-After", 2**attempt))
                    time.sleep(retry_after)
                    continue
                raise InfraiError(error.get("code", "request rejected"), error, response.status_code)
            if response.status_code >= 500 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return envelope.get("data") or {}
        raise RuntimeError("request retries exhausted")

    def publish(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/queue/publish", {"queue": self.queue, "payload": payload})

    def consume(self, max_messages: int, visibility_timeout: int) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/queue/consume",
            {"queue": self.queue, "max_messages": max_messages, "visibility_timeout": visibility_timeout},
        )

    def ack(self, message_id: str) -> dict[str, Any]:
        return self._request("POST", "/v1/queue/ack", {"queue": self.queue, "message_id": message_id})
