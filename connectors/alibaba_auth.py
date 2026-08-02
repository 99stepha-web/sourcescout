"""
Alibaba Open Platform Authentication

Implements HMAC-SHA256 request signing according to
Alibaba Open Platform documentation.

Author: SourceScout
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Dict

from dotenv import load_dotenv

load_dotenv()


class AlibabaAuth:
    """
    Handles Alibaba Open API request signing.
    """

    def __init__(self):
        self.app_key = os.getenv("ALIBABA_APP_KEY")
        self.app_secret = os.getenv("ALIBABA_APP_SECRET")

        if not self.app_key:
            raise ValueError("Missing ALIBABA_APP_KEY")

        if not self.app_secret:
            raise ValueError("Missing ALIBABA_APP_SECRET")

    def build_signature(
        self,
        api_path: str,
        params: Dict[str, str],
    ) -> str:
        """
        Generate an Alibaba HMAC-SHA256 signature.

        Signature string:

            api_path +
            key1value1 +
            key2value2 ...

        Parameters are sorted alphabetically.
        """

        pieces = [api_path]

        for key in sorted(params.keys()):
            value = params[key]

            if value is None:
                continue

            pieces.append(f"{key}{value}")

        sign_string = "".join(pieces)

        signature = hmac.new(
            self.app_secret.encode("utf-8"),
            sign_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest().upper()

        return signature

    def signed_parameters(
        self,
        api_path: str,
        params: Dict[str, str],
    ) -> Dict[str, str]:
        """
        Return a signed parameter dictionary.
        """

        payload = dict(params)

        payload["appKey"] = self.app_key

        payload["sign"] = self.build_signature(
            api_path,
            payload,
        )

        return payload
