from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    subprocess.check_call([sys.executable, str(root / "scripts" / "run_demo.py")])

    out = root / "output"
    unified = read_csv(out / "unified_dataset.csv")
    dupes = read_csv(out / "duplicate_records.csv")
    mismatches = read_csv(out / "mismatch_report.csv")
    with (out / "reconciliation_report.json").open("r", encoding="utf-8") as f:
        report = json.load(f)

    assert len(unified) == 5, f"Expected 5 unified records, got {len(unified)}"
    assert report["summary"]["duplicate_groups"] >= 3, "Expected at least 3 duplicate groups"
    assert len(dupes) >= 6, f"Expected at least 6 duplicate rows, got {len(dupes)}"
    assert len(mismatches) >= 2, f"Expected at least 2 mismatch groups, got {len(mismatches)}"

    print("All checks passed.")


if __name__ == "__main__":
    main()
