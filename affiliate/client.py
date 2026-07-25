"""
Alibaba API Client
"""

from __future__ import annotations

from typing import Any, Dict

import requests
from requests.exceptions import RequestException

from config.affiliate import AlibabaConfig

from affiliate.auth import generate_signature
from affiliate.exceptions import (
    APIError,
    AuthenticationError,
    InvalidResponseError,
    NetworkError,
    RateLimitError,
)


class AlibabaAPIClient:
    """
    Low-level HTTP client for Alibaba CPS APIs.
    """

    def __init__(self, config: AlibabaConfig):
        self.config = config
        self.session = requests.Session()

    def get(
        self,
        url_path: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Send an authenticated GET request.
        """

        request_params = dict(params)

        request_params["appKey"] = self.config.app_key

        signature = generate_signature(
            url_path=url_path,
            params=request_params,
            secret_key=self.config.secret_key,
        )

        request_params["_aop_signature"] = signature

        url = f"{self.config.base_url}/{url_path}"

        try:
            response = self.session.get(
                url,
                params=request_params,
                timeout=self.config.timeout,
            )

            response.raise_for_status()

        except RequestException as exc:
            raise NetworkError(str(exc)) from exc

        try:
            payload = response.json()

        except ValueError as exc:
            raise InvalidResponseError(
                "Alibaba API returned invalid JSON."
            ) from exc

        status = str(payload.get("status", ""))

        if status != "200":

            message = payload.get("msg", "Unknown API error")

            lower = message.lower()

            if "signature" in lower or "appkey" in lower:
                raise AuthenticationError(message)

            if "rate" in lower or "limit" in lower:
                raise RateLimitError(status, message)

            raise APIError(status, message)

        return payload
