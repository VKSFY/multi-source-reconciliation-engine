from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    subprocess.check_call([sys.executable, str(root / "scripts" / "generate_sample_data.py")])
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "src.recon_engine",
            "--config",
            str(root / "configs" / "reconciliation_config.json"),
        ]
    )


if __name__ == "__main__":
    main()
