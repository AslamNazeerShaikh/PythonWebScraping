"""Tests for src.domain_targets — flexible CSV domain/target parsing."""
from __future__ import annotations

import pytest

from src.domain_targets import DomainTarget, parse_domain_targets


def _write(tmp_path, text: str):
    path = tmp_path / "targets.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_one_domain_per_row_with_at_and_target(tmp_path):
    path = _write(tmp_path, "@cognizant.com:5\n@capgemini.com:2\n")
    assert parse_domain_targets(path) == [
        DomainTarget("cognizant.com", 5),
        DomainTarget("capgemini.com", 2),
    ]


def test_two_column_csv_with_header(tmp_path):
    path = _write(tmp_path, "domain,target\n@cognizant.com,5\ncapgemini.com,2\n")
    assert parse_domain_targets(path) == [
        DomainTarget("cognizant.com", 5),
        DomainTarget("capgemini.com", 2),
    ]


def test_bare_domains_use_default_target(tmp_path):
    path = _write(tmp_path, "cognizant.com\n@tcs.com\n")
    assert parse_domain_targets(path, default_target=7) == [
        DomainTarget("cognizant.com", 7),
        DomainTarget("tcs.com", 7),
    ]


def test_quoted_comma_packed_line(tmp_path):
    path = _write(tmp_path, '"@cognizant.com:5,@capgemini.com:2"\n')
    assert parse_domain_targets(path) == [
        DomainTarget("cognizant.com", 5),
        DomainTarget("capgemini.com", 2),
    ]


def test_domain_target_pairs_on_one_row(tmp_path):
    path = _write(tmp_path, "@tcs.com,5,@wipro.com,2\n")
    assert parse_domain_targets(path) == [
        DomainTarget("tcs.com", 5),
        DomainTarget("wipro.com", 2),
    ]


def test_target_before_domain_is_accepted(tmp_path):
    path = _write(tmp_path, "5,@tcs.com\n")
    assert parse_domain_targets(path) == [DomainTarget("tcs.com", 5)]


def test_duplicate_domain_keeps_first_order_and_last_target(tmp_path):
    path = _write(tmp_path, "@tcs.com:2\n@wipro.com:3\n@tcs.com:9\n")
    assert parse_domain_targets(path) == [
        DomainTarget("tcs.com", 9),
        DomainTarget("wipro.com", 3),
    ]


def test_utf8_bom_is_tolerated(tmp_path):
    path = tmp_path / "bom.csv"
    path.write_text("\ufeff@tcs.com:4\n", encoding="utf-8")
    assert parse_domain_targets(path) == [DomainTarget("tcs.com", 4)]


def test_empty_or_header_only_file_raises(tmp_path):
    path = _write(tmp_path, "domain,target\n\n")
    with pytest.raises(ValueError, match="no company domains"):
        parse_domain_targets(path)


def test_zero_target_without_valid_domain_raises(tmp_path):
    path = _write(tmp_path, "@tcs.com:0\n")
    with pytest.raises(ValueError, match="no company domains"):
        parse_domain_targets(path)


def test_non_positive_default_target_raises(tmp_path):
    path = _write(tmp_path, "@tcs.com\n")
    with pytest.raises(ValueError, match="default_target"):
        parse_domain_targets(path, default_target=0)


def test_ignores_numeric_and_header_cells(tmp_path):
    path = _write(tmp_path, "company,target,notes\n5,@tcs.com:3,keep\n")
    assert parse_domain_targets(path) == [DomainTarget("tcs.com", 3)]


def test_blank_cells_and_zero_neighbour_are_ignored(tmp_path):
    path = _write(tmp_path, "@tcs.com,,0\n")
    assert parse_domain_targets(path, default_target=6) == [
        DomainTarget("tcs.com", 6),
    ]
