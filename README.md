# Multi-Source Data Reconciliation Engine
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-style entity reconciliation engine for messy, multi-source business data.

Advanced reconciliation pipeline that ingests CSV, Excel, API JSON, and PDF/TXT table data, then:

- normalizes heterogeneous schemas and formats
- clusters fuzzy-matchable entities across sources
- flags duplicates and critical mismatches
- generates reconciliation reports
- exports a clean unified dataset (golden records)

Designed for real data issues:

- alias field names and per-source mapping overrides
- missing values and multi-line fields
- currency and numeric format inconsistencies
- slight OCR-style corruption in digits/text

## Features

- Multi-source ingestion (CSV, Excel, JSON/JSONL, PDF/TXT)
- Schema aliasing with per-source field mapping overrides
- Fuzzy entity matching and clustering
- Duplicate detection across systems
- Critical-field mismatch detection
- Golden record selection
- Audit-ready output artifacts and reconciliation summary

## Tech Stack

- Python 3.10+
- Streamlit (UI)
- `rapidfuzz` (fuzzy matching)
- `requests` (API ingestion)
- `pdfplumber` (PDF extraction when available)
- Built-in CSV/JSON/XML/ZIP handling for portable parsing

## Why This Exists

Operational data rarely lives in one clean source. Finance exports, storefront systems, APIs, and invoice documents often disagree on schema, formatting, and even values. This project reconciles those inputs into one auditable, unified dataset with mismatch and duplicate visibility.

## How It Works

1. Ingest raw records from CSV, Excel, API JSON/JSONL, and PDF/TXT tables.
2. Normalize schema and data formats (aliases, dates, phones, amounts, currency).
3. Match and cluster entities using key-based and fuzzy logic.
4. Generate duplicate reports, mismatch reports, and golden unified records.

## Architecture

```text
┌─────────────┐    ┌───────────────┐    ┌──────────────┐    ┌─────────────┐
│  Ingestion  │ -> │ Normalization │ -> │   Matching   │ -> │  Reporting  │
└─────────────┘    └───────────────┘    └──────────────┘    └─────────────┘
```

## Project Structure

```text
.
├─ configs/
│  └─ reconciliation_config.json
├─ scripts/
│  ├─ generate_sample_data.py
│  └─ run_demo.py
├─ src/recon_engine/
│  ├─ cli.py
│  ├─ config.py
│  ├─ engine.py
│  ├─ ingestion.py
│  ├─ matching.py
│  ├─ normalization.py
│  ├─ pdf_io.py
│  ├─ reporting.py
│  └─ xlsx_io.py
├─ tests/
│  └─ test_engine.py
└─ ui_streamlit.py
```

## Launch UI (Recommended)

To launch the interactive app:

```bash
streamlit run ui_streamlit.py
```

UI workflow:

- Upload files or paste local file paths.
- Review detected fields per source.
- Map source fields to canonical fields (or ignore).
- Tune fuzzy matching threshold and mismatch columns.
- Run reconciliation and inspect summary/output path.

## CLI / Config Run

To run the engine with a config file:

```bash
python -m src.recon_engine --config configs/reconciliation_config.json
```

Example config snippet:

```json
{
  "sources": [
    { "name": "shopify", "type": "csv", "path": "data/source_shopify.csv" },
    { "name": "quickbooks", "type": "excel", "path": "data/source_quickbooks.xlsx" },
    { "name": "api", "type": "api", "path": "data/source_api.json" },
    { "name": "invoices", "type": "pdf", "path": "data/source_invoices.pdf" }
  ],
  "similarity_threshold": 0.88,
  "field_aliases": {
    "order_id": ["order_id", "invoice_id", "txn_id"],
    "amount": ["amount", "total_amount", "invoice_total"]
  }
}
```

## Demo and Validation

To generate sample sources and run reconciliation:

```bash
python scripts/run_demo.py
```

To run validation checks:

```bash
python tests/test_engine.py
```

## Output Artifacts

Generated in configured output folder (default `output/`):

- `normalized_records.csv`
- `duplicate_records.csv`
- `mismatch_report.csv`
- `unified_dataset.csv`
- `reconciliation_report.json`

Example `unified_dataset.csv` rows:

```csv
group_id,customer_id,order_id,name,email,amount,currency,has_mismatch,golden_source
G00001,CUST-1001,INV-9001,Alice Johnson,alice@example.com,1210.0,USD,yes,finance_excel
G00002,CUST-1003,INV-9033,Carla Diaz,carla@example.com,990.0,USD,yes,ops_api
G00003,CUST-1004,INV-9050,David Lee,david.lee@example.com,150.75,USD,no,ops_api
```

## Notes

- API source can be local JSON/JSONL or HTTP endpoint.
- Excel reader is internal and optimized for common single-sheet table layouts.
- PDF parser supports `pdfplumber` text extraction (if installed) with fallback parsing.
- Extend aliases via config `field_aliases`; override per-source mappings with `field_map`.
