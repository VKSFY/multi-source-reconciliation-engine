from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

try:
    from rapidfuzz import fuzz  # type: ignore
except Exception:  # pragma: no cover
    fuzz = None


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if fuzz is not None:
        return float(fuzz.token_sort_ratio(a, b)) / 100.0
    return SequenceMatcher(a=a.lower(), b=b.lower()).ratio()


def canonical_entity_key(record: dict[str, Any]) -> str:
    for key in ("customer_id", "email", "phone"):
        value = str(record.get(key, "")).strip()
        if value:
            return f"{key}:{value}"
    name = str(record.get("name", "")).strip().lower()
    dob = str(record.get("dob", "")).strip()
    if name and dob:
        return f"name_dob:{name}:{dob}"
    return f"fallback:{hash((name, str(record.get('address', '')).lower()))}"


def cluster_records(records: list[dict[str, Any]], threshold: float) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    leftovers: list[dict[str, Any]] = []

    for rec in records:
        key = canonical_entity_key(rec)
        if key.startswith("fallback:"):
            leftovers.append(rec)
            continue
        groups.setdefault(key, []).append(rec)

    for rec in leftovers:
        placed = False
        for k, members in groups.items():
            probe = members[0]
            score = similarity(rec.get("name", ""), probe.get("name", ""))
            same_dob = rec.get("dob", "") and rec.get("dob", "") == probe.get("dob", "")
            if score >= threshold and (same_dob or score >= threshold + 0.05):
                members.append(rec)
                placed = True
                break
        if not placed:
            groups[canonical_entity_key(rec)] = [rec]
    groups = _merge_similar_groups(groups, threshold)
    return groups


def _representative(record_list: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        record_list,
        key=lambda r: sum(1 for k in ("customer_id", "email", "phone", "name", "dob") if r.get(k)),
    )


def _should_merge_groups(a: list[dict[str, Any]], b: list[dict[str, Any]], threshold: float) -> bool:
    ra = _representative(a)
    rb = _representative(b)
    name_score = similarity(ra.get("name", ""), rb.get("name", ""))
    email_score = similarity(ra.get("email", ""), rb.get("email", ""))
    same_phone = ra.get("phone", "") and ra.get("phone", "") == rb.get("phone", "")
    same_dob = ra.get("dob", "") and ra.get("dob", "") == rb.get("dob", "")
    if same_phone and name_score >= threshold - 0.1:
        return True
    if same_dob and (name_score >= threshold or email_score >= threshold - 0.05):
        return True
    return name_score >= threshold + 0.05 and email_score >= threshold - 0.05


def _merge_similar_groups(
    groups: dict[str, list[dict[str, Any]]], threshold: float
) -> dict[str, list[dict[str, Any]]]:
    keys = list(groups.keys())
    consumed: set[str] = set()
    merged: dict[str, list[dict[str, Any]]] = {}
    for i, key in enumerate(keys):
        if key in consumed:
            continue
        base = list(groups[key])
        for j in range(i + 1, len(keys)):
            other_key = keys[j]
            if other_key in consumed:
                continue
            if _should_merge_groups(base, groups[other_key], threshold):
                base.extend(groups[other_key])
                consumed.add(other_key)
        merged[key] = base
    return merged


def detect_field_mismatches(records: list[dict[str, Any]], critical_fields: list[str]) -> dict[str, list[Any]]:
    mismatches: dict[str, list[Any]] = {}
    for field in critical_fields:
        values = []
        for rec in records:
            value = rec.get(field, "")
            if value not in ("", None) and value not in values:
                values.append(value)
        if len(values) > 1:
            mismatches[field] = values
    return mismatches
