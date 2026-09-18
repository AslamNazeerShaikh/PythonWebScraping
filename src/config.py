"""Central configuration — every tunable lives here, loaded from `.env`.

Resolution order for each setting:
    1. Environment variable / `.env` file (via :func:`dotenv.load_dotenv`).
    2. Hardcoded default below (pre-tuned for a .NET dev, 6+ yrs, Pune + Hyderabad).

The :data:`SETTINGS` singleton is imported across the app; CLI flags in
:mod:`src.main` overwrite its fields per-run. Tests may freely
``monkeypatch`` its attributes (undone automatically after each test).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load `.env` (if present) into `os.environ` before any `_get*` call runs.
load_dotenv()

#: Absolute path of the project root (parent of `src/`).
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Low-level env readers — each tolerates a missing/malformed variable and
# falls back to the caller-supplied default instead of crashing at import.
# ---------------------------------------------------------------------------
def _get(name: str, default: str = "") -> str:
    """Return stripped env var ``name`` or ``default`` when unset."""
    return os.getenv(name, default).strip()


def _get_int(name: str, default: int) -> int:
    """Return env var ``name`` parsed as :class:`int`, else ``default``."""
    try:
        return int(_get(name, str(default)))
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    """Return env var ``name`` parsed as :class:`float`, else ``default``."""
    try:
        return float(_get(name, str(default)))
    except ValueError:
        return default


def _get_bool(name: str, default: bool) -> bool:
    """Return env var ``name`` parsed as flag (1/true/yes/y), else ``default``."""
    return _get(name, str(default)).lower() in ("1", "true", "yes", "y")


# ---------------------------------------------------------------------------
# Settings container
# ---------------------------------------------------------------------------
@dataclass
class Settings:
    """All runtime settings. Grouped by concern; see `.env.example`."""

    # -- Search profile: tuned for .NET 6+ yrs, Pune + Hyderabad ------------
    keywords: str = _get("KEYWORDS", "asp.net core c# .net fullstack")
    locations: list[str] = field(
        default_factory=lambda: [
            s.strip().lower()
            for s in _get("LOCATIONS", "pune,hyderabad").split(",")
            if s.strip()
        ]
    )
    experience: int = _get_int("EXPERIENCE", 6)
    date_filter: int = _get_int("DATE_FILTER", 7)  # posted within last N days
    max_pages_per_search: int = _get_int("MAX_PAGES_PER_SEARCH", 3)
    max_jobs_total: int = _get_int("MAX_JOBS_TOTAL", 60)
    enrich_details: bool = _get_bool("ENRICH_DETAILS", True)

    # -- Browser engine (Chrome-only stack) --------------------------------
    browser: str = _get("BROWSER", "chromium")
    headless: bool = _get_bool("HEADLESS", False)
    slow_mo_ms: int = _get_int("SLOW_MO_MS", 80)  # ms between actions
    user_data_dir: Path = field(
        default_factory=lambda: (BASE_DIR / _get("USER_DATA_DIR", ".pw-profile")).resolve()
    )
    timezone: str = _get("TIMEZONE", "Asia/Kolkata")
    locale: str = _get("LOCALE", "en-IN")
    viewport_w: int = _get_int("VIEWPORT_W", 1366)
    viewport_h: int = _get_int("VIEWPORT_H", 768)

    # -- Ad/tracker blocking -------------------------------------------------
    # uBlock Origin Lite, unpacked dir (vendor/download-ubol.sh fetches it).
    # Loaded headed-only; headless-shell can't load extensions (fallback covers).
    ublock_unpacked_dir: str = _get("UBLOCK_UNPACKED_DIR", "vendor/ubol-chrome")
    adblock_fallback: bool = _get_bool("ADBLOCK_FALLBACK", True)

    # -- Politeness (anti-ban): random pause range between page visits ------
    min_delay_s: float = _get_float("MIN_DELAY_S", 2.0)
    max_delay_s: float = _get_float("MAX_DELAY_S", 5.0)
    nav_timeout_ms: int = _get_int("NAV_TIMEOUT_MS", 45000)

    # -- Outputs --------------------------------------------------------------
    output_dir: Path = field(
        default_factory=lambda: (BASE_DIR / _get("OUTPUT_DIR", "output")).resolve()
    )

    # -- Persistence / logging ------------------------------------------------
    database_url: str = _get("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'jobs.db').resolve()}")
    log_level: str = _get("LOG_LEVEL", "INFO")


#: Process-wide settings singleton — import this, never re-instantiate.
SETTINGS = Settings()
