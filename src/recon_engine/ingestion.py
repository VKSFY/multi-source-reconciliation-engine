from __future__ import annotations

import csv
import json
import os
from typing import Any

import requests

from .config import SourceConfig
from .pdf_io import read_simple_pdf_table
from .xlsx_io import read_simple_xlsx


class Ingestor:
    def __init__(self, timeout_s: int = 20) -> None:
        self.timeout_s = timeout_s

    def read_source(self, source: SourceConfig) -> list[dict[str, Any]]:
        kind = source.type.lower()
        if kind == "csv":
            return self._read_csv(source.path)
        if kind == "excel":
            return self._read_excel(source.path)
        if kind == "api":
            return self._read_api(source.path)
        if kind == "pdf":
            return self._read_pdf(source.path)
        raise ValueError(f"Unsupported source type: {source.type}")

    def _read_csv(self, path: str) -> list[dict[str, Any]]:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    def _read_excel(self, path: str) -> list[dict[str, Any]]:
        return read_simple_xlsx(path)

    def _read_pdf(self, path: str) -> list[dict[str, Any]]:
        return read_simple_pdf_table(path)

    def _read_api(self, path_or_url: str) -> list[dict[str, Any]]:
        if os.path.exists(path_or_url):
            with open(path_or_url, "r", encoding="utf-8", errors="ignore") as f:
                if path_or_url.lower().endswith(".jsonl"):
                    return [json.loads(line) for line in f if line.strip()]
                payload = json.load(f)
        else:
            resp = requests.get(path_or_url, timeout=self.timeout_s)
            resp.raise_for_status()
            payload = resp.json()
        if isinstance(payload, list):
            return [dict(item) for item in payload]
        if isinstance(payload, dict) and "data" in payload and isinstance(payload["data"], list):
            return [dict(item) for item in payload["data"]]
        raise ValueError("API payload must be a list or {data:[...]}")

    def peek_columns(self, source: SourceConfig, max_rows: int = 50) -> tuple[list[str], int]:
        rows = self.read_source(source)
        sample = rows[:max_rows]
        columns = sorted({k for row in sample for k in row.keys()})
        return columns, len(rows)
