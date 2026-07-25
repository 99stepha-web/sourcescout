def calculate_trend_score(product):
    return {
        "trend_score": getattr(product, "trend_score", 0)
    }
