from __future__ import annotations

import datetime as dt
import re
from typing import Any


DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
]

OCR_CHAR_MAP = str.maketrans(
    {
        "O": "0",
        "o": "0",
        "I": "1",
        "l": "1",
        "|": "1",
        "S": "5",
        "B": "8",
    }
)


def clean_string(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_email(value: Any) -> str:
    return clean_string(value).lower()


def normalize_phone(value: Any) -> str:
    raw = clean_string(value).translate(OCR_CHAR_MAP)
    digits = re.sub(r"\D+", "", raw)
    if len(digits) == 11 and digits.startswith("1"):
        return digits[1:]
    return digits


def parse_date(value: Any) -> str:
    raw = clean_string(value)
    if not raw:
        return ""
    for fmt in DATE_FORMATS:
        try:
            return dt.datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return raw


def to_float(value: Any) -> float | None:
    raw = clean_string(value)
    if not raw:
        return None
    raw = raw.replace(" ", "")
    raw = re.sub(r"(?i)(usd|eur|gbp|cad|aud|inr|jpy)", "", raw)
    raw = raw.replace("$", "").replace("€", "").replace("£", "")
    raw = raw.translate(OCR_CHAR_MAP)

    if "," in raw and "." in raw:
        raw = raw.replace(",", "")
    elif "," in raw and raw.count(",") == 1:
        left, right = raw.split(",")
        if len(right) in (1, 2):
            raw = f"{left}.{right}"
        else:
            raw = left + right
    else:
        raw = raw.replace(",", "")

    raw = re.sub(r"[^0-9.\-]", "", raw)
    try:
        return float(raw)
    except ValueError:
        return None


def detect_currency(value: Any, default: str = "USD") -> str:
    raw = clean_string(value)
    if not raw:
        return default
    upper = raw.upper()
    if "EUR" in upper or "€" in raw:
        return "EUR"
    if "GBP" in upper or "£" in raw:
        return "GBP"
    if "CAD" in upper:
        return "CAD"
    if "AUD" in upper:
        return "AUD"
    if "INR" in upper or "₹" in raw:
        return "INR"
    if "JPY" in upper or "¥" in raw:
        return "JPY"
    return "USD" if ("$" in raw or "USD" in upper) else default
