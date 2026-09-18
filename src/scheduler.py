"""APScheduler wrapper — periodic collection without babysitting tabs.

Usage::

    python -m src.main schedule --hours 8,20   # scrape daily at 08:05 + 20:05

Each hour becomes an independent cron trigger; every trigger runs the SAME
polite pipeline (:func:`src.main.do_scrape` with the configured delays/caps).
Scheduling changes *when* collection happens, never *how aggressively* —
still one low-volume pass per trigger. ``max_instances=1`` skips a run if the
previous one is still going instead of piling up browsers.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

#: Module logger — configured once by :func:`src.log.setup_logging`.
log = logging.getLogger(__name__)


def run_scheduled(hours: list[int]) -> None:
    """Start the blocking daily scheduler (Ctrl+C stops it cleanly).

    Args:
        hours: Hours of day (0–23) to scrape at ``:05`` past the hour.
    """
    # Deferred import: main imports scheduler only for the `schedule` command,
    # so importing it here avoids a main↔scheduler import cycle.
    from .main import do_scrape

    sched = BlockingScheduler()
    for h in hours:
        sched.add_job(do_scrape, CronTrigger(hour=h, minute=5),
                      name=f"naukri-scrape-{h:02d}05", max_instances=1)
        log.info("Scheduled daily scrape at %02d:05", h)
    log.info("Scheduler started (Ctrl+C to stop). Hours: %s", hours)
    try:
        sched.start()  # blocks until interrupted
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")
