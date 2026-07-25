"""
Shared data cleaning helpers.
"""


def clean_text(value, default=""):
    if value is None:
        return default
    return str(value).strip()


def clean_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default
