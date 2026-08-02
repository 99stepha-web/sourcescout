from __future__ import annotations
import json,re
from bs4 import BeautifulSoup
from connectors.models import MarketplaceProduct

class AlibabaParserError(Exception):
    pass

class AlibabaParser:
    def parse(self, html:str)->MarketplaceProduct:
        soup=BeautifulSoup(html,"lxml")
        raw=self._parse_json_ld(soup) or self._parse_initial_state(html) or self._parse_html(soup)
        if raw is None:
            raise AlibabaParserError("Unable to parse Alibaba product.")
        d={
            "product_id":"","product_title":"","category":"","brand":"",
            "price":0.0,"original_price":None,"currency":"USD",
            "monthly_sales":0,"review_count":0,"rating":0.0,
            "wishlist_count":0,"view_count":0,
            "seller_id":"","seller_name":"","seller_rating":0.0,
            "seller_years":0,"seller_followers":0,
            "verified_supplier":False,
            "shipping_cost":0.0,"estimated_import_cost":0.0,
            "estimated_margin":0.0,"marketplace_fee":0.0,
            "country":"China"
        }
        d.update(raw)
        return MarketplaceProduct(marketplace="alibaba", raw_data=d)

    def _parse_json_ld(self,soup):
        for tag in soup.find_all("script", type="application/ld+json"):
            try:
                obj=json.loads(tag.string or "")
                if isinstance(obj,dict) and obj.get("@type")=="Product":
                    offers=obj.get("offers",{}) if isinstance(obj.get("offers"),dict) else {}
                    rating=obj.get("aggregateRating",{}) if isinstance(obj.get("aggregateRating"),dict) else {}
                    return {
                        "product_id":obj.get("sku",""),
                        "product_title":obj.get("name",""),
                        "price":float(offers.get("price",0) or 0),
                        "currency":offers.get("priceCurrency","USD"),
                        "rating":float(rating.get("ratingValue",0) or 0),
                        "review_count":int(rating.get("reviewCount",0) or 0),
                    }
            except Exception:
                pass
        return None

    def _parse_initial_state(self,html):
        m=re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', html, re.S)
        if not m:
            return None
        try:
            return {"product_title": json.loads(m.group(1)).get("subject","")}
        except Exception:
            return None

    def _parse_html(self,soup):
        if soup.title and soup.title.string:
            return {"product_title": soup.title.string.strip()}
        return None

