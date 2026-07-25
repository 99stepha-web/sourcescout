def score_level(score):
    if score >= 80:
        return "HIGH"
    elif score >= 60:
        return "MEDIUM"
    elif score >= 40:
        return "LOW"
    return "VERY LOW"
