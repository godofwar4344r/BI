from __future__ import annotations

import logging
import sys


def configure_logging(environment: str) -> None:
    level = logging.DEBUG if environment == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        stream=sys.stdout,
    )
