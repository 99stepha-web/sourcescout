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
