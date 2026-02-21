from __future__ import annotations

import os
from collections import defaultdict
from typing import Any

from .config import EngineConfig
from .ingestion import Ingestor
from .matching import cluster_records, detect_field_mismatches
from .normalization import completeness_score, normalize_record
from .reporting import write_csv, write_json


class ReconciliationEngine:
    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.ingestor = Ingestor()
        self.priority_index = {
            name: idx for idx, name in enumerate(config.source_priority)
        }

    def run(self) -> dict[str, Any]:
        normalized: list[dict[str, Any]] = []
        source_counts: dict[str, int] = {}

        for src in self.config.sources:
            rows = self.ingestor.read_source(src)
            source_counts[src.name] = len(rows)
            for i, row in enumerate(rows, start=1):
                normalized.append(
                    normalize_record(
                        row,
                        source_name=src.name,
                        row_num=i,
                        global_aliases=self.config.field_aliases,
                        source_field_map=src.field_map,
                    )
                )

        groups = cluster_records(normalized, threshold=self.config.similarity_threshold)
        duplicates = {k: v for k, v in groups.items() if len(v) > 1}

        mismatch_rows: list[dict[str, Any]] = []
        unified: list[dict[str, Any]] = []
        group_map: dict[str, str] = {}
        for idx, (entity_key, recs) in enumerate(groups.items(), start=1):
            group_id = f"G{idx:05d}"
            group_map[entity_key] = group_id
            mismatch = detect_field_mismatches(recs, self.config.critical_columns)
            if mismatch:
                mismatch_rows.append(
                    {
                        "group_id": group_id,
                        "entity_key": entity_key,
                        "record_count": len(recs),
                        "mismatch_fields": ", ".join(sorted(mismatch.keys())),
                        "details": str(mismatch),
                    }
                )
            unified.append(self._pick_golden_record(group_id, recs, mismatch))

        duplicate_rows = []
        for entity_key, recs in duplicates.items():
            for rec in recs:
                duplicate_rows.append(
                    {
                        "group_id": group_map[entity_key],
                        "entity_key": entity_key,
                        "source_name": rec["source_name"],
                        "source_row": rec["source_row"],
                        "name": rec.get("name", ""),
                        "email": rec.get("email", ""),
                        "phone": rec.get("phone", ""),
                        "status": rec.get("status", ""),
                    }
                )

        summary = {
            "total_records_ingested": len(normalized),
            "source_counts": source_counts,
            "entity_groups": len(groups),
            "duplicate_groups": len(duplicates),
            "duplicate_records": len(duplicate_rows),
            "mismatch_groups": len(mismatch_rows),
            "output_records": len(unified),
        }

        out_dir = self.config.output_dir
        os.makedirs(out_dir, exist_ok=True)
        write_csv(os.path.join(out_dir, "normalized_records.csv"), normalized)
        write_csv(os.path.join(out_dir, "duplicate_records.csv"), duplicate_rows)
        write_csv(os.path.join(out_dir, "mismatch_report.csv"), mismatch_rows)
        write_csv(os.path.join(out_dir, "unified_dataset.csv"), unified)
        write_json(
            os.path.join(out_dir, "reconciliation_report.json"),
            {"summary": summary, "mismatches": mismatch_rows},
        )
        return {"summary": summary, "output_dir": out_dir}

    def _pick_golden_record(
        self,
        group_id: str,
        records: list[dict[str, Any]],
        mismatch: dict[str, list[Any]],
    ) -> dict[str, Any]:
        fields = sorted({k for rec in records for k in rec.keys()})
        best = max(
            records,
            key=lambda r: (
                completeness_score(r, self.config.critical_columns + self.config.id_columns),
                -self.priority_index.get(r["source_name"], 999),
                str(r.get("updated_at", "")),
            ),
        )
        merged = defaultdict(str)
        for field in fields:
            for rec in sorted(
                records,
                key=lambda r: (
                    self.priority_index.get(r["source_name"], 999),
                    -completeness_score(r, [field]),
                ),
            ):
                value = rec.get(field, "")
                if value not in ("", None):
                    merged[field] = value
                    break
        merged["group_id"] = group_id
        merged["golden_source"] = best.get("source_name", "")
        merged["has_mismatch"] = "yes" if mismatch else "no"
        merged["mismatch_fields"] = ", ".join(sorted(mismatch.keys()))
        return dict(merged)
