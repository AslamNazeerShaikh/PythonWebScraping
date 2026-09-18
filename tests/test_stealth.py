"""Tests for src.stealth_browser — Chrome-only launcher + uBO Lite wiring."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import src.stealth_browser as sb
from src.config import SETTINGS
from tests.conftest import FakeContext, FakeMouse, FakePage, FakeRoute, fake_playwright


# -- human_pause ------------------------------------------------------------------
def test_human_pause_zero_is_instant():
    sb.human_pause(0, 0)  # must return immediately, no error


# -- _extension_args (uBO Lite wiring, headed-only) ----------------------------------
def _tune(monkeypatch, tmp_path, **kw):
    monkeypatch.setattr(SETTINGS, "user_data_dir", tmp_path / "prof")
    monkeypatch.setattr(SETTINGS, "headless", False)
    for k, v in kw.items():
        monkeypatch.setattr(SETTINGS, k, v)


def test_extension_args_unset_dir(monkeypatch, tmp_path):
    _tune(monkeypatch, tmp_path, ublock_unpacked_dir="")
    assert sb._extension_args() == []


def test_extension_args_skipped_when_headless(monkeypatch, tmp_path):
    ext = tmp_path / "ubol"
    ext.mkdir()
    _tune(monkeypatch, tmp_path, ublock_unpacked_dir=str(ext))
    monkeypatch.setattr(SETTINGS, "headless", True)
    assert sb._extension_args() == []  # headless-shell can't load extensions


def test_extension_args_missing_dir(monkeypatch, tmp_path):
    _tune(monkeypatch, tmp_path,
          ublock_unpacked_dir=str(tmp_path / "does-not-exist"))
    assert sb._extension_args() == []


def test_extension_args_headed_load(monkeypatch, tmp_path):
    ext = tmp_path / "ubol"
    ext.mkdir()
    _tune(monkeypatch, tmp_path, ublock_unpacked_dir=str(ext))
    args = sb._extension_args()
    assert len(args) == 2 and all(str(ext) in a for a in args)
    assert any(a.startswith("--load-extension=") for a in args)


# -- _maybe_block_ads ---------------------------------------------------------------
def _handler(monkeypatch, fallback=True):
    monkeypatch.setattr(SETTINGS, "adblock_fallback", fallback)
    ctx = FakeContext()
    sb._maybe_block_ads(ctx)
    return ctx


def test_blocker_disabled_registers_nothing(monkeypatch):
    assert _handler(monkeypatch, fallback=False).routes == []


def test_blocker_aborts_trackers_pixels_and_continues_rest(monkeypatch):
    ctx = _handler(monkeypatch, fallback=True)
    assert len(ctx.routes) == 1
    _, handle = ctx.routes[0]
    tracker = FakeRoute()
    handle(tracker, SimpleNamespace(url="https://doubleclick.net/x",
                                    resource_type="script"))
    assert tracker.aborted and not tracker.continued
    pixel = FakeRoute()
    handle(pixel, SimpleNamespace(url="https://site.test/pixel.gif",
                                  resource_type="image"))
    assert pixel.aborted
    image_ok = FakeRoute()
    handle(image_ok, SimpleNamespace(url="https://site.test/photo.jpg",
                                     resource_type="image"))
    assert image_ok.continued and not image_ok.aborted
    normal = FakeRoute()
    handle(normal, SimpleNamespace(url="https://www.naukri.com/jobs",
                                   resource_type="document"))
    assert normal.continued


# -- engine launch ----------------------------------------------------------------------
def test_launch_chromium_headed_with_ubol(monkeypatch, tmp_path):
    ext = tmp_path / "ubol"
    ext.mkdir()
    _tune(monkeypatch, tmp_path, ublock_unpacked_dir=str(ext))
    p = fake_playwright(chromium_ctxs=[FakeContext()])
    ctx = sb._launch_chromium(p)
    assert isinstance(ctx, FakeContext)
    sent = p.chromium.kwargs[0]
    assert "user_agent" not in sent  # genuine engine UA (no pinning -> no rot)
    assert sent["locale"] == SETTINGS.locale
    assert any("--load-extension=" in a for a in sent["args"])


def test_launch_chromium_headless_skips_extension(monkeypatch, tmp_path):
    ext = tmp_path / "ubol"
    ext.mkdir()
    _tune(monkeypatch, tmp_path, ublock_unpacked_dir=str(ext))
    monkeypatch.setattr(SETTINGS, "headless", True)
    p = fake_playwright(chromium_ctxs=[FakeContext()])
    sb._launch_chromium(p)
    assert not any("--load-extension=" in a
                   for a in p.chromium.kwargs[0]["args"])


# -- launch_context dispatch ------------------------------------------------------------------
def test_launch_context_chromium(monkeypatch, tmp_path):
    _tune(monkeypatch, tmp_path, browser="chromium", ublock_unpacked_dir="")
    p = fake_playwright(chromium_ctxs=[FakeContext()])
    assert isinstance(sb.launch_context(p), FakeContext)


def test_launch_context_empty_browser_defaults_to_chromium(monkeypatch, tmp_path):
    _tune(monkeypatch, tmp_path, browser="", ublock_unpacked_dir="")
    p = fake_playwright(chromium_ctxs=[FakeContext()])
    assert isinstance(sb.launch_context(p), FakeContext)


def test_launch_context_rejects_firefox(monkeypatch, tmp_path):
    _tune(monkeypatch, tmp_path, browser="firefox")
    with pytest.raises(ValueError, match="Chrome-only"):
        sb.launch_context(fake_playwright())


def test_launch_playwright_returns_handle_and_context(monkeypatch, tmp_path):
    _tune(monkeypatch, tmp_path, browser="chromium", ublock_unpacked_dir="")
    started = {}

    class _FakeStart:
        def start(self):
            started["yes"] = True
            return fake_playwright(chromium_ctxs=[FakeContext()])

    monkeypatch.setattr(sb, "sync_playwright", _FakeStart)
    pw, ctx = sb.launch_playwright()
    assert started and isinstance(ctx, FakeContext)
    assert hasattr(pw, "chromium")
    assert isinstance(FakePage(), FakePage)  # import sanity (page fake intact)
    assert isinstance(FakeMouse(), FakeMouse)
