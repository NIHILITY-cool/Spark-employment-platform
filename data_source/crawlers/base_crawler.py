from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import requests


class BaseCrawler:
    """Small base crawler with retries, throttling, and raw response saving."""

    def __init__(
        self,
        headers: dict[str, str],
        delay_seconds: float,
        timeout_seconds: int,
        logger: logging.Logger,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.logger = logger

    def get_json(self, url: str, params: dict[str, Any] | None = None, retries: int = 2) -> dict[str, Any]:
        response = self._get(url, params=params, retries=retries)
        return response.json()

    def get_text(self, url: str, params: dict[str, Any] | None = None, retries: int = 2) -> str:
        response = self._get(url, params=params, retries=retries)
        response.encoding = response.encoding or "utf-8"
        return response.text

    def _get(self, url: str, params: dict[str, Any] | None = None, retries: int = 2) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(1, retries + 2):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout_seconds)
                response.raise_for_status()
                if self.delay_seconds > 0:
                    time.sleep(self.delay_seconds)
                return response
            except Exception as exc:  # requests has several useful exception subclasses.
                last_error = exc
                self.logger.warning("request failed attempt=%s url=%s error=%s", attempt, url, exc)
                time.sleep(min(self.delay_seconds * attempt, 5))
        raise RuntimeError(f"request failed after retries: {url}") from last_error

    @staticmethod
    def save_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def save_text(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
