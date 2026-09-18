"""Layer 5 (analysis/output): Pandas over SQLite → CSV / Excel snapshots.

Ownership rule: **SQLite is the source of truth**; files produced here are
disposable point-in-time snapshots for quick filtering/sharing. Re-running an
export never touches the database.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import select

from .config import SETTINGS
from .db import get_engine
from .models import JobRow

#: Module logger — configured once by :func:`src.log.setup_logging`.
log = logging.getLogger(__name__)

#: Column order for every export (kept stable so diffs stay readable).
COLUMNS = ["job_id", "title", "company", "location", "search_location",
           "experience", "salary", "posted", "url", "apply_url",
           "skills", "first_seen", "last_seen"]


def load_frame(location: str = "", limit: int = 5000) -> pd.DataFrame:
    """Load jobs from SQLite into a :class:`~pandas.DataFrame`.

    Args:
        location: Optional case-insensitive filter matched against BOTH the
            job's own ``location`` and the ``search_location`` it was found
            under (e.g. ``"pune"``). Empty string disables filtering.
        limit: Max rows, freshest first (mirrors :func:`src.db.fetch_all_jobs`).
    """
    engine = get_engine()
    stmt = select(JobRow).order_by(JobRow.last_seen.desc()).limit(limit)
    with engine.connect() as conn:
        df = pd.read_sql(stmt, conn)
    if location:
        # Match either column — a Hyderabad-found job may list "Pune" and v.v.
        mask = df["location"].str.contains(location, case=False, na=False) | \
            df["search_location"].str.contains(location, case=False, na=False)
        df = df[mask]
    return df[COLUMNS]


def export_jobs(fmt: str = "csv", location: str = "",
                out_path: str | None = None) -> Path:
    """Export the current DB snapshot to CSV or Excel.

    Args:
        fmt: ``"csv"`` (default) or ``"excel"`` (``.xlsx`` via openpyxl).
        location: Forwarded to :func:`load_frame` for pre-export filtering.
        out_path: Explicit destination; otherwise a timestamped file under
            ``OUTPUT_DIR`` (``naukri_export_<ts>.csv|.xlsx``).

    Returns:
        Path of the written file.
    """
    df = load_frame(location=location)
    out_dir = SETTINGS.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    if out_path:
        dest = Path(out_path)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "xlsx" if fmt == "excel" else "csv"
        dest = out_dir / f"naukri_export_{ts}.{suffix}"
    if fmt == "excel":
        df.to_excel(dest, index=False)
    else:
        df.to_csv(dest, index=False)
    log.info("Exported %d rows -> %s", len(df), dest)
    return dest
