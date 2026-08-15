import re
from urllib.parse import urlsplit, parse_qs


ID_QUERY_KEYS = ("id", "itemId", "item_id", "itemid", "spuId", "goodsId")

NUMERIC_ID_PATTERN = re.compile(r"(\d{6,})")


def extract_stable_product_id(product_url) -> str:
    """
    Derive a stable platform product ID from a product URL so the
    same real-world listing maps to the same ID across scrapes.
    Falls back to "" (caller should generate a random ID) when no
    stable identifier can be found.
    """

    if not product_url:
        return ""

    try:
        query = parse_qs(urlsplit(str(product_url)).query)

        for key in ID_QUERY_KEYS:
            values = query.get(key)
            if values and values[0]:
                return values[0]

    except Exception:
        pass

    match = NUMERIC_ID_PATTERN.search(str(product_url))

    if match:
        return match.group(1)

    return ""


TAOBAO_URL_PATTERN = re.compile(
    r"https?://(?:s\.click\.taobao\.com|m\.tb\.cn)/[A-Za-z0-9._/?=&%:+~#-]+",
    re.IGNORECASE,
)


def clean_affiliate_url(value) -> str:
    """
    Return one clean raw Taobao affiliate URL.

    Handles:
      https://m.tb.cn/h.xxxxx
      [https://m.tb.cn/h.xxxxx](https://m.tb.cn/h.xxxxx)
      arbitrary clipboard text containing the URL
    """

    if not value:
        return ""

    text = str(value).strip()

    match = TAOBAO_URL_PATTERN.search(text)

    if not match:
        return ""

    url = match.group(0).rstrip(
        " \t\r\n)]}>.,;\"'"
    )

    try:
        parsed = urlsplit(url)

        if parsed.scheme.lower() != "https":
            return ""

        if parsed.netloc.lower() not in {
            "m.tb.cn",
            "s.click.taobao.com",
        }:
            return ""

        if not parsed.path:
            return ""

    except Exception:
        return ""

    return url
