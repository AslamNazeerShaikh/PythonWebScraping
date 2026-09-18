"""Tests for src.stealth_browser — profiles, uBlock, engines, fallback."""
from __future__ import annotations

from types import SimpleNamespace

import src.stealth_browser as sb
from src.config import SETTINGS
from tests.conftest import FakeContext, FakePage, FakeRoute, fake_playwright


# -- human_pause ------------------------------------------------------------------
def test_human_pause_zero_is_instant():
    sb.human_pause(0, 0)  # must return immediately, no error


# -- install_ublock_into_profile ---------------------------------------------------
def test_install_ublock_missing_xpi(tmp_path):
    assert sb.install_ublock_into_profile(
        tmp_path / "prof", "/nonexistent/ublock.xpi") is False


def test_install_ublock_copy_and_idempotent(tmp_path):
    xpi = tmp_path / "ublock.xpi"
    xpi.write_bytes(b"fake-xpi-bytes")
    profile = tmp_path / "prof"
    assert sb.install_ublock_into_profile(profile, str(xpi)) is True
    dest = profile / "extensions" / "uBlock0@raymondhill.net.xpi"
    assert dest.exists()
    assert sb.install_ublock_into_profile(profile, str(xpi)) is True  # skip copy


def test_install_ublock_exception_returns_false(tmp_path, monkeypatch):
    import shutil
    xpi = tmp_path / "ublock.xpi"
    xpi.write_bytes(b"fake-xpi-bytes")
    monkeypatch.setattr(shutil, "copyfile",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    assert sb.install_ublock_into_profile(tmp_path / "prof", str(xpi)) is False


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


# -- _prep_profile ---------------------------------------------------------------------
def test_prep_profile_removes_empty_and_creates_parent(tmp_path):
    empty = tmp_path / "a" / "prof"
    empty.mkdir(parents=True)  # exists but empty -> removed...
    sb._prep_profile(empty)
    assert not empty.exists()
    sb._prep_profile(empty)  # ...missing parent recreated without error
    assert empty.parent.exists()


def test_prep_profile_rmdir_failure_is_swallowed(tmp_path, monkeypatch):
    from pathlib import Path
    prof = tmp_path / "prof"
    prof.mkdir()  # empty -> rmdir attempted...
    monkeypatch.setattr(Path, "rmdir",
                        lambda self: (_ for _ in ()).throw(OSError("locked")))
    sb._prep_profile(prof)  # ...fails -> except: pass, then parent ensured
    assert prof.parent.exists()


def test_prep_profile_keeps_nonempty(tmp_path):
    prof = tmp_path / "prof"
    prof.mkdir()
    (prof / "prefs.js").write_text("user_pref('x', 1);")
    sb._prep_profile(prof)
    assert (prof / "prefs.js").exists()


# -- engine launches ----------------------------------------------------------------------
def _tune_browser(monkeypatch, tmp_path, **kw):
    monkeypatch.setattr(SETTINGS, "user_data_dir", tmp_path / "prof")
    for k, v in kw.items():
        monkeypatch.setattr(SETTINGS, k, v)


def test_launch_firefox_defaults(monkeypatch, tmp_path):
    _tune_browser(monkeypatch, tmp_path, ublock_xpi_path="")
    p = fake_playwright(firefox_ctxs=[FakeContext()])
    ctx = sb._launch_firefox(p)
    assert isinstance(ctx, FakeContext)
    sent = p.firefox.kwargs[0]
    assert sent["locale"] == SETTINGS.locale
    assert "user_agent" not in sent  # genuine engine UA (no pinning -> no rot)
    assert sent["firefox_user_prefs"]["dom.webdriver.enabled"] is False


def test_launch_firefox_first_run_with_xpi(monkeypatch, tmp_path):
    xpi = tmp_path / "ub.xpi"
    xpi.write_bytes(b"x")
    _tune_browser(monkeypatch, tmp_path, ublock_xpi_path=str(xpi))
    sb._launch_firefox(fake_playwright(firefox_ctxs=[FakeContext()]))


def test_launch_firefox_existing_profile_installs_xpi(monkeypatch, tmp_path):
    xpi = tmp_path / "ub.xpi"
    xpi.write_bytes(b"x")
    prof = tmp_path / "prof"
    prof.mkdir()
    (prof / "prefs.js").write_text("user_pref('x', 1);")
    _tune_browser(monkeypatch, tmp_path, ublock_xpi_path=str(xpi))
    sb._launch_firefox(fake_playwright(firefox_ctxs=[FakeContext()]))
    assert (prof / "extensions" / "uBlock0@raymondhill.net.xpi").exists()


def test_launch_chromium_unpacked_args_recorded(monkeypatch, tmp_path):
    unpacked = tmp_path / "ubo"
    unpacked.mkdir()
    _tune_browser(monkeypatch, tmp_path, ublock_unpacked_dir=str(unpacked),
                  ublock_xpi_path="")
    p = fake_playwright(chromium_ctxs=[FakeContext()])
    sb._launch_chromium(p)
    args = p.chromium.kwargs[0]["args"]
    assert any("--load-extension" in a for a in args)


def test_launch_chromium_xpi_only_message(monkeypatch, tmp_path):
    _tune_browser(monkeypatch, tmp_path, ublock_unpacked_dir="",
                  ublock_xpi_path="/tmp/ub.xpi")
    sb._launch_chromium(fake_playwright(chromium_ctxs=[FakeContext()]))


def test_launch_chromium_plain(monkeypatch, tmp_path):
    _tune_browser(monkeypatch, tmp_path, ublock_unpacked_dir="",
                  ublock_xpi_path="")
    p = fake_playwright(chromium_ctxs=[FakeContext()])
    ctx = sb._launch_chromium(p)
    assert isinstance(ctx, FakeContext)
    assert "user_agent" not in p.chromium.kwargs[0]  # genuine engine UA


# -- launch_context dispatch + fallback ------------------------------------------------------
def test_launch_context_chromium_direct(monkeypatch, tmp_path):
    _tune_browser(monkeypatch, tmp_path, browser="chromium",
                  ublock_unpacked_dir="", ublock_xpi_path="")
    p = fake_playwright(chromium_ctxs=[FakeContext()], firefox_err=RuntimeError("unused"))
    assert isinstance(sb.launch_context(p), FakeContext)


def test_launch_context_firefox_ok(monkeypatch, tmp_path):
    _tune_browser(monkeypatch, tmp_path, browser="firefox", ublock_xpi_path="")
    p = fake_playwright(firefox_ctxs=[FakeContext()])
    assert isinstance(sb.launch_context(p), FakeContext)


def test_launch_context_firefox_failure_falls_back(monkeypatch, tmp_path):
    _tune_browser(monkeypatch, tmp_path, browser="firefox", ublock_xpi_path="",
                  ublock_unpacked_dir="")
    p = fake_playwright(firefox_err=RuntimeError("Could not find profile folder"),
                        chromium_ctxs=[FakeContext()])
    assert isinstance(sb.launch_context(p), FakeContext)


def test_launch_playwright_returns_handle_and_context(monkeypatch, tmp_path):
    _tune_browser(monkeypatch, tmp_path, browser="chromium",
                  ublock_unpacked_dir="", ublock_xpi_path="")
    sentinel = object()
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
