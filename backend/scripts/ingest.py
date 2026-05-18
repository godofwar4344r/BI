from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "backend"))

from app.core.config import Settings  # noqa: E402
from app.main import build_services  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest BI decision cases from JSONL.")
    parser.add_argument(
        "--path",
        type=Path,
        default=ROOT / "data" / "sample_decision_cases.jsonl",
        help="Path to JSONL decision-case dataset.",
    )
    args = parser.parse_args()
    services = build_services(Settings())
    count = services.ingestion.ingest_jsonl(args.path)
    print(f"Ingested {count} decision cases from {args.path}")


if __name__ == "__main__":
    main()
