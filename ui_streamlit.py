from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import streamlit as st

from src.recon_engine.config import EngineConfig, SourceConfig
from src.recon_engine.engine import ReconciliationEngine
from src.recon_engine.ingestion import Ingestor
from src.recon_engine.normalization import FIELD_ALIASES


CANONICAL_FIELDS = sorted(FIELD_ALIASES.keys())
DEFAULT_ID_FIELDS = ["customer_id", "email", "phone"]
DEFAULT_CRITICAL_FIELDS = ["name", "email", "phone", "address", "amount", "status"]


def infer_source_type(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext == ".csv":
        return "csv"
    if ext in (".xlsx", ".xlsm"):
        return "excel"
    if ext in (".json", ".jsonl"):
        return "api"
    if ext in (".pdf", ".txt", ".tsv"):
        return "pdf"
    return "csv"


def save_uploaded_files(files: list[Any], root: Path) -> list[dict[str, str]]:
    out = []
    os.makedirs(root, exist_ok=True)
    for f in files:
        target = root / f.name
        with target.open("wb") as w:
            w.write(f.getbuffer())
        out.append({"name": Path(f.name).stem, "path": str(target), "type": infer_source_type(f.name)})
    return out


def parse_path_input(raw: str) -> list[dict[str, str]]:
    out = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        p = Path(line)
        out.append({"name": p.stem, "path": str(p), "type": infer_source_type(line)})
    return out


def main() -> None:
    st.set_page_config(page_title="Reconciliation Engine", page_icon=":bar_chart:", layout="wide")
    st.title("Multi-Source Data Reconciliation")
    st.caption("Upload or reference your files, map schema fields, and run reconciliation.")

    ingest = Ingestor()
    workspace = Path(".ui_uploads")

    with st.sidebar:
        st.subheader("Run Settings")
        out_dir = st.text_input("Output folder", value="output")
        threshold = st.slider("Fuzzy matching threshold", min_value=0.70, max_value=0.99, value=0.88, step=0.01)
        id_cols = st.multiselect("Entity ID columns", CANONICAL_FIELDS, default=DEFAULT_ID_FIELDS)
        critical_cols = st.multiselect("Critical mismatch columns", CANONICAL_FIELDS, default=DEFAULT_CRITICAL_FIELDS)
        alias_json = st.text_area(
            "Global field aliases (JSON: canonical -> [aliases])",
            value=json.dumps(FIELD_ALIASES, indent=2),
            height=220,
        )

    uploaded = st.file_uploader(
        "Upload sources (CSV, XLSX, JSON/JSONL, PDF/TXT)",
        type=["csv", "xlsx", "xlsm", "json", "jsonl", "pdf", "txt", "tsv"],
        accept_multiple_files=True,
    )
    path_input = st.text_area(
        "Or provide local file paths (one per line)",
        placeholder=r"C:\data\source_shopify.csv",
        height=100,
    )

    sources = []
    if uploaded:
        sources.extend(save_uploaded_files(uploaded, workspace))
    if path_input.strip():
        sources.extend(parse_path_input(path_input))

    if not sources:
        st.info("Add at least one source to continue.")
        return

    st.subheader("Source Mapping")
    configured_sources: list[SourceConfig] = []
    for idx, s in enumerate(sources):
        with st.expander(f"{s['name']} ({s['type']})", expanded=True):
            name = st.text_input("Source name", value=s["name"], key=f"name_{idx}")
            source_type = st.selectbox(
                "Source type",
                ["csv", "excel", "api", "pdf"],
                index=["csv", "excel", "api", "pdf"].index(s["type"]) if s["type"] in ["csv", "excel", "api", "pdf"] else 0,
                key=f"type_{idx}",
            )
            path = st.text_input("Path", value=s["path"], key=f"path_{idx}")
            st.caption("Per-source field mapping (set to ignore, auto, or canonical target).")

            field_map: dict[str, str] = {}
            columns = []
            count = 0
            try:
                columns, count = ingest.peek_columns(SourceConfig(name=name, type=source_type, path=path))
                st.write(f"Detected {len(columns)} fields across {count} rows.")
            except Exception as e:
                st.error(f"Could not read source: {e}")

            options = ["(auto)", "(ignore)"] + CANONICAL_FIELDS
            for col in columns:
                suggested = "(auto)"
                norm_col = col.lower().strip()
                for canonical, aliases in FIELD_ALIASES.items():
                    if norm_col == canonical or norm_col in [a.lower() for a in aliases]:
                        suggested = canonical
                        break
                choice = st.selectbox(
                    f"Map `{col}`",
                    options,
                    index=options.index(suggested),
                    key=f"map_{idx}_{col}",
                )
                if choice not in ("(auto)", "(ignore)"):
                    field_map[col] = choice

            configured_sources.append(SourceConfig(name=name, type=source_type, path=path, field_map=field_map))

    if st.button("Run Reconciliation", type="primary"):
        try:
            aliases = json.loads(alias_json) if alias_json.strip() else {}
            config = EngineConfig(
                sources=configured_sources,
                source_priority=[s.name for s in configured_sources],
                id_columns=id_cols or DEFAULT_ID_FIELDS,
                critical_columns=critical_cols or DEFAULT_CRITICAL_FIELDS,
                output_dir=out_dir,
                similarity_threshold=float(threshold),
                field_aliases=aliases,
            )
            result = ReconciliationEngine(config).run()
            st.success("Reconciliation completed.")
            st.json(result["summary"])
            st.write(f"Artifacts written to `{result['output_dir']}`")
        except Exception as e:
            st.error(f"Run failed: {e}")


if __name__ == "__main__":
    main()
