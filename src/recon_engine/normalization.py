from __future__ import annotations

from typing import Any

from .utils import (
    clean_string,
    detect_currency,
    normalize_email,
    normalize_phone,
    parse_date,
    to_float,
)


FIELD_ALIASES = {
    "customer_id": ["customer_id", "id", "cust_id", "client_id"],
    "name": ["name", "full_name", "customer_name"],
    "email": ["email", "email_address", "mail"],
    "phone": ["phone", "phone_number", "contact"],
    "address": ["address", "addr", "location"],
    "dob": ["dob", "date_of_birth", "birth_date"],
    "amount": ["amount", "balance", "total_amount", "value"],
    "status": ["status", "state", "record_status"],
    "updated_at": ["updated_at", "last_updated", "modified_at"],
    "currency": ["currency", "curr", "ccy"],
    "notes": ["notes", "memo", "description", "details"],
}


def _invert_aliases() -> dict[str, str]:
    out: dict[str, str] = {}
    for canonical, aliases in FIELD_ALIASES.items():
        for a in aliases:
            out[a.lower()] = canonical
    return out


ALIASES = _invert_aliases()


def build_alias_lookup(
    global_aliases: dict[str, list[str]] | None = None,
    source_field_map: dict[str, str] | None = None,
) -> dict[str, str]:
    out = dict(ALIASES)
    if global_aliases:
        for canonical, aliases in global_aliases.items():
            for alias in aliases:
                out[alias.lower().strip()] = canonical.lower().strip()
            out[canonical.lower().strip()] = canonical.lower().strip()
    if source_field_map:
        for source_field, canonical in source_field_map.items():
            out[source_field.lower().strip()] = canonical.lower().strip()
    return out


def normalize_record(
    record: dict[str, Any],
    source_name: str,
    row_num: int,
    global_aliases: dict[str, list[str]] | None = None,
    source_field_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    alias_lookup = build_alias_lookup(global_aliases, source_field_map)
    canon: dict[str, Any] = {
        "source_name": source_name,
        "source_row": row_num,
    }
    for key, value in record.items():
        target = alias_lookup.get(key.lower().strip(), key.lower().strip())
        canon[target] = value

    canon["customer_id"] = clean_string(canon.get("customer_id", ""))
    canon["name"] = clean_string(canon.get("name", "")).title()
    canon["email"] = normalize_email(canon.get("email", ""))
    canon["phone"] = normalize_phone(canon.get("phone", ""))
    canon["address"] = clean_string(canon.get("address", "")).title()
    canon["dob"] = parse_date(canon.get("dob", ""))
    canon["updated_at"] = parse_date(canon.get("updated_at", ""))

    amount_raw = canon.get("amount", "")
    amount = to_float(amount_raw)
    canon["amount"] = "" if amount is None else round(amount, 2)
    canon["currency"] = clean_string(canon.get("currency", "")) or detect_currency(amount_raw)
    canon["status"] = clean_string(canon.get("status", "")).lower()
    canon["notes"] = clean_string(canon.get("notes", ""))
    return canon


def completeness_score(record: dict[str, Any], fields: list[str]) -> int:
    return sum(1 for f in fields if record.get(f) not in ("", None))
