"""
Tests for product_scoring.py and category_relevance.py — the
hard-filter / opportunity-ranking layer that runs before any Claude
call. All product data here is synthetic test fixture data, not real
scraped content.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from product_scoring import (
    calculate_selection_score,
    deduplicate_candidates,
    hard_filter,
)
from category_relevance import relevance_score

KEYWORD = "办公桌配件"


def test_a_high_commission_no_demand_is_rejected():
    product = {
        "title": "日本进口遥控器收纳盒办公桌整理盒多格手机收纳盒办公室笔筒",
        "commission_rate": 2.01,
        "monthly_sales": 0,
        "orders": 0,
        "rating": None,
        "review_count": 0,
        "supplier_score": None,
        "trend_score": None,
        "badges": None,
        "price": 15.0,
    }

    result = calculate_selection_score(product, KEYWORD)

    assert result["selection_status"] in ("HARD_FILTERED", "LOW_PRIORITY")
    assert result["selection_score"] < 45


def test_b_moderate_commission_huge_sales_excellent_rating_is_high_priority():
    product = {
        "title": "办公桌折叠桌腿支架配件五金件",
        "commission_rate": 6.0,
        "monthly_sales": 8000,
        "orders": 8000,
        "rating": 4.8,
        "review_count": 20000,
        "supplier_score": 92,
        "trend_score": 70,
        "badges": "热销,爆款",
        "price": 40.0,
    }

    result = calculate_selection_score(product, KEYWORD)

    assert result["selection_status"] == "RANKED"
    assert result["selection_score"] >= 70


def test_c_high_sales_terrible_rating_is_downgraded():
    strong = {
        "title": "办公桌收纳盒五金配件挂钩",
        "commission_rate": 5.0,
        "monthly_sales": 6000,
        "orders": 6000,
        "rating": 4.8,
        "review_count": 3000,
        "supplier_score": 80,
        "trend_score": None,
        "badges": None,
        "price": 20.0,
    }

    bad_rating = dict(strong, rating=2.1)

    strong_score = calculate_selection_score(strong, KEYWORD)["selection_score"]
    bad_rating_score = calculate_selection_score(bad_rating, KEYWORD)["selection_score"]

    assert bad_rating_score < strong_score


def test_d_new_product_rapidly_rising_sales_is_trending():
    product = {
        "title": "办公桌线槽走线盒新款配件",
        "commission_rate": 4.0,
        "monthly_sales": 500,
        "orders": 500,
        "rating": None,
        "review_count": 0,
        "supplier_score": 60,
        "trend_score": None,
        "badges": "新品,趋势",
        "price": 25.0,
    }

    history = [{"monthly_sales": 100}, {"monthly_sales": 500}]

    result = calculate_selection_score(product, KEYWORD, history=history)

    assert result["breakdown"]["trend"]["score"] >= 70
    assert result["selection_status"] in ("RANKED", "LOW_PRIORITY")


def test_e_wrong_category_is_rejected_regardless_of_strength():
    product = {
        "title": "NAD+ 保健品 抗衰老补剂",
        "commission_rate": 10.0,
        "monthly_sales": 5000,
        "orders": 5000,
        "rating": 4.9,
        "review_count": 10000,
        "supplier_score": 95,
        "trend_score": 90,
        "badges": "爆款",
        "price": 300.0,
    }

    result = calculate_selection_score(product, KEYWORD)

    assert result["selection_status"] == "CATEGORY_MISMATCH"


def test_f_missing_commission_is_low_confidence_not_fabricated():
    product = {
        "title": "办公桌配件五金件支架",
        "commission_rate": None,
        "monthly_sales": 200,
        "orders": 200,
        "rating": None,
        "review_count": None,
        "supplier_score": None,
        "trend_score": None,
        "badges": None,
        "price": 30.0,
    }

    result = calculate_selection_score(product, KEYWORD)

    assert result["breakdown"]["commission"]["score"] is None
    assert result["breakdown"]["commission"]["confidence"] == "LOW"


def test_g_missing_sales_is_low_confidence_not_fabricated():
    product = {
        "title": "办公桌配件收纳盒",
        "commission_rate": 4.0,
        "monthly_sales": None,
        "orders": None,
        "rating": None,
        "review_count": None,
        "supplier_score": None,
        "trend_score": None,
        "badges": None,
        "price": 20.0,
    }

    result = calculate_selection_score(product, KEYWORD)

    assert result["breakdown"]["sales"]["score"] is None
    assert result["breakdown"]["sales"]["confidence"] == "LOW"


def test_h_duplicate_products_keep_only_strongest_candidate():
    weaker = {
        "product_id": "X1",
        "title": "办公桌配件A",
        "commission_rate": 3.0,
        "monthly_sales": 100,
        "price": 10,
    }

    stronger = {
        "product_id": "X1",
        "title": "办公桌配件A",
        "commission_rate": 5.0,
        "monthly_sales": 500,
        "price": 10,
    }

    survivors, dropped = deduplicate_candidates([weaker, stronger], KEYWORD)

    assert len(survivors) == 1
    assert len(dropped) == 1
    assert survivors[0]["commission_rate"] == 5.0


def test_category_relevance_matches_same_category():
    score, _ = relevance_score(KEYWORD, "320款组合办公桌配件大全工位配件屏风隔断卡座")
    assert score == 100.0


def test_category_relevance_rejects_health_supplement():
    score, _ = relevance_score(KEYWORD, "NAD+ 保健品")
    assert score == 0.0


def test_hard_filter_never_fabricates_a_pass_for_restricted_products():
    product = {
        "title": "办公桌配件 处方药品",
        "commission_rate": 20.0,
        "monthly_sales": 9000,
    }

    passed, reasons = hard_filter(product, category_score=100)

    assert passed is False
    assert reasons
