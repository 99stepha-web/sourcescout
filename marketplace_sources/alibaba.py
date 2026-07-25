from typing import Any


class AlibabaConnector:
    """
    Alibaba marketplace discovery connector.

    The connector is currently prepared for an official
    Alibaba API or affiliate product feed.

    Once API credentials are available, the search_products()
    method will call the real Alibaba endpoint and normalize
    results for SourceScout.
    """

    platform = "Alibaba"


    def __init__(
        self,
        app_key=None,
        app_secret=None,
    ):

        self.app_key = app_key
        self.app_secret = app_secret


    def search_products(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:

        keyword = keyword.strip()

        if not keyword:
            raise ValueError(
                "A search keyword is required."
            )

        # --------------------------------------------------
        # IMPORTANT
        # --------------------------------------------------
        #
        # Real Alibaba API integration will be added here
        # after the API credentials and available product
        # search endpoint have been confirmed.
        #
        # We deliberately return an empty result instead of
        # generating fake marketplace products.
        # --------------------------------------------------

        return []
