"""
SourceScout Intelligence Configuration

All scoring thresholds, weights and calibration values
are defined here.

Changing this file should never require changing
an analyzer.
"""

# --------------------------------------------------
# Trend Analyzer
# --------------------------------------------------

TREND_CONFIG = {
    "weights": {
        "sales": 0.70,
        "reviews": 0.30,
    },
    "sales_bands": [
        (50, 10),
        (200, 25),
        (800, 45),
        (2000, 70),
        (5000, 90),
        (999999, 100),
    ],
    "review_bands": [
        (20, 10),
        (100, 25),
        (300, 45),
        (700, 70),
        (1500, 90),
        (999999, 100),
    ],
}

# --------------------------------------------------
# Competition Analyzer
# --------------------------------------------------

COMPETITION_CONFIG = {
    "weights": {
        "reviews": 0.40,
        "followers": 0.30,
        "verified": 0.20,
        "rating": 0.10,
    }
}

# --------------------------------------------------
# Supplier Analyzer
# --------------------------------------------------

SUPPLIER_CONFIG = {
    "weights": {
        "rating": 0.40,
        "years": 0.30,
        "verified": 0.20,
        "followers": 0.10,
    }
}

# --------------------------------------------------
# Pricing Analyzer
# --------------------------------------------------

PRICING_CONFIG = {
    "weights": {
        "margin": 0.50,
        "shipping": 0.25,
        "import": 0.15,
        "fees": 0.10,
    }
}

# --------------------------------------------------
# Profitability Analyzer
# --------------------------------------------------

PROFITABILITY_CONFIG = {
    "weights": {
        "roi": 0.50,
        "margin": 0.30,
        "efficiency": 0.20,
    }
}

# --------------------------------------------------
# Product Scorer
# --------------------------------------------------

SCORER_CONFIG = {
    "weights": {
        "trend": 0.30,
        "competition": 0.20,
        "supplier": 0.20,
        "pricing": 0.15,
        "profitability": 0.15,
    },
    "decision_thresholds": {
        "STRONG_BUY": 85,
        "BUY": 70,
        "REVIEW": 55,
        "REJECT": 0,
    },
}

# --------------------------------------------------
# Product Selection (discovery-time hard filter + ranking)
#
# Demand + customer satisfaction + momentum matter more than
# commission alone — a high commission on a product nobody buys is
# worse than a moderate commission on a proven bestseller.
# --------------------------------------------------

SELECTION_CONFIG = {
    "weights": {
        "sales": 0.25,
        "feedback": 0.20,
        "trend": 0.15,
        "commission": 0.15,
        "supplier": 0.10,
        "price": 0.10,
        "content": 0.05,
    },

    # Normalized 0-100 bands for monthly_sales (falls back to `orders`
    # when monthly_sales isn't available). Logarithmic-ish so one
    # exceptional seller doesn't flatten the scale for everyone else.
    "sales_bands": [
        (10, 15),
        (50, 35),
        (200, 55),
        (1000, 75),
        (5000, 90),
        (999999, 100),
    ],

    # Bands for review_count, used only for confidence weighting —
    # a 5.0 rating on 3 reviews must not outscore 4.8 on 2,000.
    "review_count_bands": [
        (5, 10),
        (20, 30),
        (100, 55),
        (500, 75),
        (2000, 90),
        (999999, 100),
    ],

    "hard_filter": {
        "min_commission_rate": 1.0,
        "min_category_relevance": 40,
        # A product can still survive a low/zero sales signal if it
        # shows real trend evidence (badges, rising promoter count).
        "min_sales_without_trend_evidence": 1,
    },

    "claude_analysis_limit": 12,
    "article_generation_limit": 5,

    "approval_thresholds": {
        "min_selection_score_for_claude": 45,
        "min_ai_score_for_promote": 70,
        "min_ai_score_for_review": 50,
    },
}
