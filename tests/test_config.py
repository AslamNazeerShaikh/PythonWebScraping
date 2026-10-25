"""Tests for src.config — env readers and their malformed-input fallbacks."""
from __future__ import annotations

from src import config


def test_get_returns_default_when_unset(monkeypatch):
    monkeypatch.delenv("MISSING_VAR_XYZ", raising=False)
    assert config._get("MISSING_VAR_XYZ", "dflt") == "dflt"


def test_get_strips_whitespace(monkeypatch):
    monkeypatch.setenv("PADDED_VAR", "  hi  ")
    assert config._get("PADDED_VAR", "") == "hi"


def test_get_int_valid_and_invalid(monkeypatch):
    monkeypatch.setenv("INT_OK", "42")
    assert config._get_int("INT_OK", 1) == 42
    monkeypatch.setenv("INT_BAD", "abc")
    assert config._get_int("INT_BAD", 7) == 7  # malformed -> default, no crash


def test_get_float_valid_and_invalid(monkeypatch):
    monkeypatch.setenv("FLOAT_OK", "2.5")
    assert config._get_float("FLOAT_OK", 1.0) == 2.5
    monkeypatch.setenv("FLOAT_BAD", "xyz")
    assert config._get_float("FLOAT_BAD", 9.5) == 9.5


def test_get_bool_variants(monkeypatch):
    for truthy in ("1", "true", "TRUE", "yes", "Y"):
        monkeypatch.setenv("FLAG_X", truthy)
        assert config._get_bool("FLAG_X", False) is True
    for falsy in ("0", "false", "no", "", "maybe"):
        monkeypatch.setenv("FLAG_X", falsy)
        assert config._get_bool("FLAG_X", False) is False
    monkeypatch.delenv("FLAG_X", raising=False)
    assert config._get_bool("FLAG_X", True) is True  # unset -> default


def test_settings_singleton_has_expected_defaults():
    assert "pune" in config.SETTINGS.locations
    assert config.SETTINGS.experience >= 1
    assert config.SETTINGS.output_dir.name == "output"


def test_email_collector_settings_defaults():
    s = config.SETTINGS
    # The 11 target domains from docs/SPEC-linkedin-email-collector.md
    assert s.email_domains == [
        "cognizant.com", "capgemini.com", "ltm.com", "hexaware.com",
        "infosys.com", "tcs.com", "wipro.com", "epam.com", "kforce.com",
        "persistent.com", "xoriant.com",
    ]
    assert s.email_max_scrolls == 40
    assert s.email_default_target == 10
    assert s.email_domain_pause_s == 300
    assert s.email_date_facet == "past-month"
