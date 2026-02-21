from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class SourceConfig:
    name: str
    type: str
    path: str
    field_map: dict[str, str] = field(default_factory=dict)


@dataclass
class EngineConfig:
    sources: list[SourceConfig]
    source_priority: list[str]
    id_columns: list[str]
    critical_columns: list[str]
    output_dir: str
    similarity_threshold: float
    field_aliases: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str) -> "EngineConfig":
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return cls(
            sources=[SourceConfig(**s) for s in raw["sources"]],
            source_priority=raw["source_priority"],
            id_columns=raw["id_columns"],
            critical_columns=raw["critical_columns"],
            output_dir=raw["output_dir"],
            similarity_threshold=float(raw.get("similarity_threshold", 0.9)),
            field_aliases=raw.get("field_aliases", {}),
        )
