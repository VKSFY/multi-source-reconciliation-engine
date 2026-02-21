from __future__ import annotations

import os
import re
from typing import Any

try:
    import pdfplumber  # type: ignore
except Exception:  # pragma: no cover
    pdfplumber = None


def write_simple_pdf_table(path: str, headers: list[str], rows: list[dict[str, Any]]) -> None:
    lines = ["|".join(headers)]
    for row in rows:
        lines.append("|".join(str(row.get(h, "")) for h in headers))

    text_ops = []
    y = 760
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        text_ops.append(f"BT /F1 10 Tf 50 {y} Td ({safe}) Tj ET")
        y -= 14
    stream_content = "\n".join(text_ops).encode("latin-1", errors="replace")

    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
    )
    objects.append(
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
    )
    objects.append(
        f"5 0 obj << /Length {len(stream_content)} >> stream\n".encode("latin-1")
        + stream_content
        + b"\nendstream endobj\n"
    )

    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj

    xref_start = len(pdf)
    xref = [f"0 {len(objects)+1}\n", "0000000000 65535 f \n"]
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n")
    trailer = (
        f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF"
    ).encode("latin-1")
    pdf += b"xref\n" + "".join(xref).encode("latin-1") + trailer

    with open(path, "wb") as f:
        f.write(pdf)


def _infer_delimiter(line: str) -> str:
    candidates = ["|", "\t", ";", ","]
    scores = {d: line.count(d) for d in candidates}
    best = max(scores, key=lambda d: scores[d])
    return best if scores[best] > 0 else "|"


def _parse_delimited_lines(lines: list[str], delimiter: str | None = None) -> list[dict[str, str]]:
    trimmed = [l.strip() for l in lines if l and l.strip()]
    if not trimmed:
        return []
    delim = delimiter or _infer_delimiter(trimmed[0])
    header_line = next((l for l in trimmed if l.count(delim) >= 2), trimmed[0])
    headers = [h.strip().lower() for h in header_line.split(delim)]
    data_lines = trimmed[trimmed.index(header_line) + 1 :]

    out: list[dict[str, str]] = []
    for line in data_lines:
        if line.count(delim) == 0:
            if out:
                # Preserve continuation rows common in OCR exports.
                last = out[-1]
                first_key = headers[0]
                last[first_key] = (last.get(first_key, "") + " " + line).strip()
            continue
        cols = [c.strip() for c in line.split(delim)]
        if len(cols) < len(headers):
            cols += [""] * (len(headers) - len(cols))
        if len(cols) > len(headers):
            cols = cols[: len(headers) - 1] + [" ".join(cols[len(headers) - 1 :])]
        out.append({headers[i]: cols[i] for i in range(len(headers))})
    return out


def _extract_text_runs_from_pdf_bytes(path: str) -> list[str]:
    with open(path, "rb") as f:
        data = f.read().decode("latin-1", errors="ignore")
    text_runs = re.findall(r"\((.*?)\)\s*Tj", data, flags=re.DOTALL)
    return [
        t.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
        for t in text_runs
    ]


def read_simple_pdf_table(path: str, delimiter: str = "|") -> list[dict[str, str]]:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".tsv", ".csv"):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return _parse_delimited_lines(f.read().splitlines(), delimiter=None)

    lines: list[str] = []
    if pdfplumber is not None:
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text() or ""
                    lines.extend(extracted.splitlines())
        except Exception:
            lines = []
    if not lines:
        lines = _extract_text_runs_from_pdf_bytes(path)
    return _parse_delimited_lines(lines, delimiter=delimiter)
