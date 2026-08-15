"""
Category relevance filter.

The Alimama search UI returns loosely-matched results for a given
Chinese keyword — a search for desk accessories can still surface
supplements, phones, or food. This module scores how likely a
discovered product's title actually belongs to the same category as
the search keyword, so off-category products can be rejected before
spending a Claude call on them.

Deterministic and keyword-based (no external calls) — this needs to
run cheaply over every discovered candidate.
"""

import re

import category_taxonomy


def _bigrams(text):
    text = re.sub(r"\s+", "", text or "")
    return {text[i:i + 2] for i in range(len(text) - 1)}


def relevance_score(keyword, title):
    """
    Return (score 0-100, reason string).

    100  keyword and title resolve to the same known category
    0    keyword and title resolve to different known categories
         (hard mismatch — e.g. office keyword, supplement product)
    50   category can't be confidently determined for one or both
         sides; falls back to character-bigram overlap between
         keyword and title so we don't block what we can't classify
    """

    keyword_category = category_taxonomy.category_for(keyword)
    title_categories = category_taxonomy.categories_for(title)

    if keyword_category and title_categories:
        if keyword_category in title_categories:
            return 100.0, f"category match: {keyword_category}"

        best_title_category = max(title_categories, key=title_categories.get)

        return 0.0, (
            f"category mismatch: keyword implies "
            f"'{keyword_category}', product looks like "
            f"'{best_title_category}'"
        )

    # Can't classify one or both sides with the known taxonomy.
    # Don't reject blindly — fall back to lexical overlap so an
    # unmapped-but-genuinely-related keyword/title pair isn't
    # punished just because our category list is incomplete.
    kw_grams = _bigrams(keyword)
    title_grams = _bigrams(title)

    if not kw_grams:
        return 50.0, "keyword too short to classify"

    overlap = len(kw_grams & title_grams) / len(kw_grams)
    score = round(50.0 + overlap * 50.0, 1)

    return score, f"no known category on both sides; lexical overlap {overlap:.0%}"
