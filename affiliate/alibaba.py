"""
Alibaba Affiliate Provider
"""

from __future__ import annotations

from typing import List

from config.affiliate import AlibabaConfig

from affiliate.client import AlibabaAPIClient
from affiliate.endpoints import (
    PRODUCT_DETAIL,
    PROMOTION_LINK,
)
from affiliate.provider import (
    AffiliateLink,
    AffiliateProvider,
)


class AlibabaAffiliateProvider(AffiliateProvider):
    """
    Alibaba CPS Affiliate Provider
    """

    name = "alibaba"

    def __init__(self, config: AlibabaConfig):
        self.config = config
        self.client = AlibabaAPIClient(config)

    def generate_product_link(
        self,
        product_id: str,
    ) -> AffiliateLink:

        return self._generate_link(
            link_type="product",
            value=product_id,
        )

    def generate_url_link(
        self,
        url: str,
    ) -> AffiliateLink:

        return self._generate_link(
            link_type="url",
            value=url,
        )

    def _generate_link(
        self,
        link_type: str,
        value: str,
    ) -> AffiliateLink:

        url_path = PROMOTION_LINK.format(
            app_key=self.config.app_key,
        )

        response = self.client.get(
            url_path=url_path,
            params={
                "linkType": link_type,
                "value": value,
            },
        )

        data = response["data"]
        links = data["promotionLink"]

        return AffiliateLink(
            original_url=value,
            affiliate_url=links["pc"],
            provider=self.name,
            desktop_url=links.get("pc"),
            mobile_url=links.get("wap"),
            app_url=links.get("app"),
        )

    def get_product_details(
        self,
        product_ids: List[str],
    ):
        """
        Retrieve product details.

        This method will be finalized after implementing the
        official Product Detail API specification.
        """

        url_path = PRODUCT_DETAIL.format(
            app_key=self.config.app_key,
        )

        return self.client.get(
            url_path=url_path,
            params={
                "productIds": ",".join(product_ids),
            },
        )
