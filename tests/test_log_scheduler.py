"""Tests for src.log and src.scheduler."""
from __future__ import annotations

import logging

import pytest

from src.log import setup_logging


def test_setup_logging_levels():
    setup_logging("DEBUG")
    assert logging.getLogger().level == logging.DEBUG
    setup_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING
    # Unknown level falls back to INFO instead of raising.
    setup_logging("BOGUS_LEVEL_XYZ")
    assert logging.getLogger().level == logging.INFO
    # Playwright chatter is always quieted.
    assert logging.getLogger("playwright").level == logging.WARNING


class _FakeSched:
    """BlockingScheduler stand-in — records jobs, scriptable start()."""

    instances: list = []

    def __init__(self) -> None:
        self.jobs: list = []
        self.raise_on_start: Exception | None = None
        _FakeSched.instances.append(self)

    def add_job(self, fn, trigger, name="", max_instances=1):  # type: ignore[no-untyped-def]
        self.jobs.append((fn, trigger, name, max_instances))

    def start(self) -> None:
        if self.raise_on_start is not None:
            raise self.raise_on_start


def test_run_scheduled_registers_cron_jobs(monkeypatch):
    import src.scheduler as sched_mod

    _FakeSched.instances.clear()
    monkeypatch.setattr(sched_mod, "BlockingScheduler", _FakeSched)
    sched_mod.run_scheduled([8, 20])
    sched = _FakeSched.instances[-1]
    assert len(sched.jobs) == 2
    names = [j[2] for j in sched.jobs]
    assert names == ["naukri-scrape-0805", "naukri-scrape-2005"]
    assert all(j[3] == 1 for j in sched.jobs)  # max_instances=1
    # do_scrape wired as the job function (deferred import works).
    from src.main import do_scrape
    assert all(j[0] is do_scrape for j in sched.jobs)


def test_run_scheduled_handles_interrupt(monkeypatch):
    import src.scheduler as sched_mod

    _FakeSched.instances.clear()

    def _factory():  # type: ignore[no-untyped-def]
        s = _FakeSched()
        s.raise_on_start = KeyboardInterrupt()
        return s

    monkeypatch.setattr(sched_mod, "BlockingScheduler", _factory)
    sched_mod.run_scheduled([9])  # must not propagate
    assert len(_FakeSched.instances[-1].jobs) == 1


def test_run_scheduled_handles_system_exit(monkeypatch):
    import src.scheduler as sched_mod

    _FakeSched.instances.clear()

    def _factory():  # type: ignore[no-untyped-def]
        s = _FakeSched()
        s.raise_on_start = SystemExit(0)
        return s

    monkeypatch.setattr(sched_mod, "BlockingScheduler", _factory)
    sched_mod.run_scheduled([9])
    assert pytest is not None  # reached here = SystemExit swallowed
