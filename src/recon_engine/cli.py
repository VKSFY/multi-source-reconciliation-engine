from __future__ import annotations

import argparse
import json

from .config import EngineConfig
from .engine import ReconciliationEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-source data reconciliation engine")
    parser.add_argument("--config", required=True, help="Path to JSON config")
    args = parser.parse_args()

    config = EngineConfig.load(args.config)
    result = ReconciliationEngine(config).run()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
