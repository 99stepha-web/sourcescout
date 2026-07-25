"""
Affiliate configuration objects.
"""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AlibabaConfig:
    """
    Configuration for the Alibaba Affiliate API.
    """

    app_key: str
    secret_key: str
    base_url: str = "https://usapi.alibaba.com/openapi"
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "AlibabaConfig":
        """
        Load configuration from environment variables.
        """

        app_key = os.getenv("ALIBABA_APP_KEY")
        secret_key = os.getenv("ALIBABA_SECRET_KEY")

        if not app_key:
            raise ValueError("Missing ALIBABA_APP_KEY")

        if not secret_key:
            raise ValueError("Missing ALIBABA_SECRET_KEY")

        return cls(
            app_key=app_key,
            secret_key=secret_key,
        )
