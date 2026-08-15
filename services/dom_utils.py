import re


def clean_number(text: str) -> float:
    text = text.replace(",", "")
    m = re.search(r"[\d.]+", text)
    return float(m.group()) if m else 0.0


def clean_int(text: str) -> int:
    text = text.replace(",", "")
    m = re.search(r"\d+", text)
    return int(m.group()) if m else 0


def clean_text(text: str) -> str:
    return " ".join(text.split())
