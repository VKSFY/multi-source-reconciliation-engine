from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from src.recon_engine.pdf_io import write_simple_pdf_table
from src.recon_engine.xlsx_io import write_simple_xlsx

SAMPLES = BASE / "samples"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    os.makedirs(SAMPLES / "csv", exist_ok=True)
    os.makedirs(SAMPLES / "excel", exist_ok=True)
    os.makedirs(SAMPLES / "api", exist_ok=True)
    os.makedirs(SAMPLES / "pdf", exist_ok=True)

    csv_rows = [
        {
            "id": "CUST-1001",
            "full_name": "alice johnson",
            "email_address": "ALICE@example.com",
            "phone_number": "(555) 123-4567",
            "addr": "100 Main St, Denver",
            "birth_date": "01/12/1990",
            "balance": "1200.50",
            "state": "Active",
            "last_updated": "2025-10-01",
        },
        {
            "id": "",
            "full_name": "Bob Smith",
            "email_address": "bob.smith@example.com",
            "phone_number": "555-999-8888",
            "addr": "9 Lake Rd, Austin",
            "birth_date": "1985-04-09",
            "balance": "500",
            "state": "active",
            "last_updated": "2025-10-02",
        },
    ]
    _write_csv(SAMPLES / "csv" / "customers.csv", csv_rows)

    excel_rows = [
        {
            "customer_id": "CUST-1001",
            "customer_name": "Alice Johnson",
            "email": "alice@example.com",
            "contact": "1-555-123-4567",
            "address": "100 Main Street, Denver",
            "date_of_birth": "1990-01-12",
            "total_amount": "1210.00",
            "status": "active",
            "updated_at": "2025-11-01",
        },
        {
            "customer_id": "CUST-1003",
            "customer_name": "Carla Diaz",
            "email": "carla@example.com",
            "contact": "5557776666",
            "address": "500 Pine Ave, Miami",
            "date_of_birth": "1992/05/17",
            "total_amount": "980.30",
            "status": "inactive",
            "updated_at": "2025-10-10",
        },
    ]
    write_simple_xlsx(str(SAMPLES / "excel" / "customers.xlsx"), excel_rows)

    api_rows = [
        {
            "client_id": "CUST-1003",
            "name": "Carla Diaz",
            "mail": "carla@example.com",
            "phone": "5557776666",
            "location": "500 Pine Ave, Miami",
            "dob": "17-05-1992",
            "value": "990.00",
            "record_status": "inactive",
            "modified_at": "2025-12-01",
        },
        {
            "client_id": "CUST-1004",
            "name": "David Lee",
            "mail": "david.lee@example.com",
            "phone": "5551112222",
            "location": "44 Elm St, Seattle",
            "dob": "1988-09-30",
            "value": "150.75",
            "record_status": "active",
            "modified_at": "2025-10-12",
        },
    ]
    with (SAMPLES / "api" / "customers_api.json").open("w", encoding="utf-8") as f:
        json.dump({"data": api_rows}, f, indent=2)

    pdf_rows = [
        {
            "cust_id": "CUST-1004",
            "full_name": "David Lee",
            "email": "david.lee@example.com",
            "phone": "555-111-2222",
            "address": "44 Elm Street, Seattle",
            "dob": "09/30/1988",
            "amount": "150.75",
            "status": "active",
            "updated_at": "2025-10-15",
        },
        {
            "cust_id": "CUST-1005",
            "full_name": "Eva Long",
            "email": "eva.long@example.com",
            "phone": "5553334444",
            "address": "77 River Rd, Boston",
            "dob": "1993-02-01",
            "amount": "2100",
            "status": "active",
            "updated_at": "2025-11-20",
        },
    ]
    write_simple_pdf_table(
        str(SAMPLES / "pdf" / "customers.pdf"),
        headers=list(pdf_rows[0].keys()),
        rows=pdf_rows,
    )

    print("Sample sources generated under ./samples")


if __name__ == "__main__":
    main()
