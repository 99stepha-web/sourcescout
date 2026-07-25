def calculate_cross_market_score(product):
    return {
        "cross_market_score": getattr(product, "cross_market_score", 0)
    }
