"""
Shared product category taxonomy.

Single source of truth for keyword -> category matching, used by:
  - catalog_enhancer.py (website catalog category badges/filter)
  - category_relevance.py (discovery-time category-relevance filter)

Keep category names stable — the website catalog persists them into
already-published HTML.
"""

CATEGORY_KEYWORDS = {
    "Coffee & Espresso": [
        "coffee", "espresso", "咖啡",
    ],
    "Beauty": [
        "beauty", "skincare", "makeup", "美容", "护肤", "化妆品",
    ],
    "Fashion": [
        "jacket", "shirt", "dress", "bag", "shoes",
        "fashion", "服装", "外套", "鞋", "包",
    ],
    "Electronics": [
        "phone", "laptop", "tablet", "camera",
        "headphone", "电子", "手机", "电脑", "耳机",
    ],
    "Outdoor & Travel": [
        "travel", "camping", "outdoor",
        "portable", "旅行", "户外", "便携",
    ],
    "Home & Kitchen": [
        "kitchen", "cooking", "home",
        "厨房", "家用",
    ],
    "Office & Desk": [
        "office", "desk", "stationery",
        "办公", "桌", "文具", "工位",
    ],
    "Health & Supplements": [
        "supplement", "vitamin", "health",
        "保健品", "保健", "维生素", "营养",
        "nad+", "nad",
    ],
    "Food & Snacks": [
        "snack", "food", "tea", "零食", "食品", "茶叶",
    ],
}


def categories_for(text):
    """
    Return every category with at least one keyword hit in text, as
    {category_name: hit_count}. A title can legitimately match more
    than one category (e.g. a desk organizer mentioning "电脑桌"
    also contains the Electronics keyword "电脑") — callers that need
    a single best guess should use category_for, but relevance
    checks should consider the full set.
    """

    t = (text or "").lower()
    hits = {}

    for name, words in CATEGORY_KEYWORDS.items():
        count = sum(1 for w in words if w in t)
        if count:
            hits[name] = count

    return hits


def category_for(text):
    """
    Return the single best-matching category name for text (most
    keyword hits, ties broken by CATEGORY_KEYWORDS order), or None if
    no category matches.
    """

    hits = categories_for(text)

    if not hits:
        return None

    return max(hits, key=lambda name: (hits[name], -list(CATEGORY_KEYWORDS).index(name)))
