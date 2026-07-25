from __future__ import annotations

import logging
from typing import Final

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


DEFAULT_HEADERS: Final = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


class FetchError(Exception):
    """Raised when a page cannot be fetched."""


class ProductFetcher:
    def __init__(self, timeout: float = 30.0):
        self.client = httpx.Client(
            timeout=timeout,
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    def fetch(self, url: str) -> str:
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as exc:
            logger.exception("Failed to fetch %s", url)
            raise FetchError(str(exc)) from exc

    def close(self) -> None:
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
