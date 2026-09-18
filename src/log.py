"""Logging setup — one call at startup, standard library only.

We deliberately use :mod:`logging` instead of ``structlog``: the app needs
timestamped, leveled lines (``INFO Starting scraper`` …) and nothing more.
Call :func:`setup_logging` once (CLI entry does this); library modules only
obtain ``logging.getLogger(__name__)`` and never configure handlers.
"""
from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging to stdout.

    Args:
        level: Level name such as ``"INFO"``/``"DEBUG"``. Unknown names fall
            back to ``INFO`` instead of raising.

    Side effects:
        - Installs a ``HH:MM:SS LEVEL logger: message`` format (``force=True``
          so repeated calls / test runs re-apply cleanly).
        - Quiets the ``playwright`` logger to ``WARNING`` — its INFO chatter
          would otherwise drown out scraper progress lines.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    # Playwright is chatty at INFO — keep our signal clean.
    logging.getLogger("playwright").setLevel(logging.WARNING)
