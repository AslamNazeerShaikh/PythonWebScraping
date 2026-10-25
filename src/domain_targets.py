"""Parse ``collect-emails`` input CSV files into ordered domain targets.

Accepted shapes (all cells are scanned, so headers/extra columns are fine)::

    @cognizant.com:5
    @capgemini.com:2

    domain,target
    @cognizant.com,5
    @capgemini.com,2

    "@cognizant.com:5,@capgemini.com:2"

Domains may omit ``@``; targets are positive integers and fall back to
``EMAIL_DEFAULT_TARGET`` when omitted.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

#: A DNS-ish company domain (at least one dot, no scheme/path).
_DOMAIN_RE = re.compile(
    r"^@?(?P<domain>(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,})$",
    re.IGNORECASE,
)

#: ``@domain:5`` / ``domain=5`` (spaces tolerated).
_EMBEDDED_RE = re.compile(
    r"^@?(?P<domain>(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,})"
    r"\s*[:=]\s*(?P<target>\d+)$",
    re.IGNORECASE,
)

_INT_RE = re.compile(r"^\d+$")


@dataclass(frozen=True)
class DomainTarget:
    """One input row: search ``domain`` until ``target`` unique emails."""

    domain: str
    target: int


def _clean_cell(value: object) -> str:
    """Strip whitespace and the quotes CSV users often paste around values."""
    return str(value or "").strip().strip("'\"").strip()


def _domain(value: str) -> str | None:
    """Return the normalised domain, or ``None`` when the cell isn't one."""
    match = _DOMAIN_RE.fullmatch(_clean_cell(value))
    return match.group("domain").lower() if match else None


def _embedded(value: str) -> tuple[str, int] | None:
    """Parse ``@domain:5`` (or ``domain=5``) in one cell."""
    match = _EMBEDDED_RE.fullmatch(_clean_cell(value))
    if not match:
        return None
    target = int(match.group("target"))
    if target < 1:
        return None
    return match.group("domain").lower(), target


def _flatten_row(row: list[str]) -> list[str]:
    """Split quoted comma-packed cells and drop blanks."""
    cells: list[str] = []
    for raw in row:
        for part in _clean_cell(raw).split(","):
            part = _clean_cell(part)
            if part:
                cells.append(part)
    return cells


def parse_domain_targets(path: str | Path,
                         default_target: int = 10) -> list[DomainTarget]:
    """Read an input CSV and return unique domains in first-seen order.

    Args:
        path: CSV file path (UTF-8, BOM tolerated).
        default_target: Target used when a domain has no ``:N`` suffix.

    Returns:
        Ordered :class:`DomainTarget` rows. Duplicate domains keep their
        first position and last explicit target.

    Raises:
        ValueError: If the file has no recognisable domain, or
            ``default_target`` is not positive.
    """
    if default_target < 1:
        raise ValueError("default_target must be a positive integer")

    ordered: list[str] = []
    targets: dict[str, int] = {}
    with Path(path).expanduser().open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.reader(handle):
            cells = _flatten_row(row)
            for index, cell in enumerate(cells):
                parsed = _embedded(cell)
                if parsed:
                    domain, target = parsed
                else:
                    domain = _domain(cell)
                    if not domain:
                        continue
                    target = _neighbour_target(cells, index) or default_target
                if domain not in targets:
                    ordered.append(domain)
                targets[domain] = target

    if not ordered:
        raise ValueError(
            f"no company domains found in {path!s}; expected e.g. "
            "'@cognizant.com:5' or a domain,target CSV")
    return [DomainTarget(domain, targets[domain]) for domain in ordered]


def _neighbour_target(cells: list[str], index: int) -> int | None:
    """Read a numeric target in the cell before/after a bare domain."""
    for neighbour in (index + 1, index - 1):
        if 0 <= neighbour < len(cells) and _INT_RE.fullmatch(cells[neighbour]):
            value = int(cells[neighbour])
            if value >= 1:
                return value
    return None
