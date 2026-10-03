"""Every registered backcast year has a measured nuclear availability basis.

``fleet.arrays._nuclear_monthly`` reads ``NUCLEAR_MONTHLY_CF_BY_YEAR[iso][year]``
and, when the row is absent, silently falls back to the static forecast pattern
``NUCLEAR_MONTHLY_CF[iso] x (1 - EFORD)`` — a year-invariant CF. That is how PJM,
NWPP, SPP and SOCO 2019-2022 backcasts ran on the forecast fallback for weeks
(model nuclear byte-identical across years; closeout-SOCO-2 FINDING §d,
closeout-nuclear-rows FINDING 2026-10-03). Rule 14 [R-ACCURATE].

The invariant, per ISO, over every year any registered backcast run of that ISO
carries (the ISO determination covers every registered year, rule 30): the year
has a ``NUCLEAR_MONTHLY_CF_BY_YEAR`` row, OR the ISO's keeper arms a measured
daily nuclear overlay (``nuclear_unit_availability`` /
``ercot_nuclear_unit_availability``) in its recorded ``run_config.json``.
Fails closed: a missing keeper record or bundle config is a failure, and the
message names every uncovered ISO-year.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from market_sim.config.constants import NUCLEAR_MONTHLY_CF_BY_YEAR

_ROOT = Path(__file__).resolve().parents[3]
_BACKCAST = _ROOT / "frontend" / "data" / "backcast"
_ISOS = ("CAISO", "ERCOT", "MISO", "NEISO", "NWPP", "NYISO", "PJM", "SOCO", "SPP")
_OVERLAY_FIELDS = ("nuclear_unit_availability", "ercot_nuclear_unit_availability")

#: ISO-years whose rows are derived in an open lane that has not reached main.
#: Each entry must still be uncovered at HEAD (see the test below), so the
#: allowance cannot outlive the merge that fills it. SOCO 2019-2022: lane
#: claude/closeout-soco-2 (PRECOMMIT-closeout-soco-2-2026-10-03.md) — delete these
#: entries when that lane merges main.
_PENDING_ROWS: frozenset[tuple[str, int]] = frozenset(
    ("SOCO", y) for y in (2019, 2020, 2021, 2022)
)


def _registered_years() -> dict[str, set[int]]:
    """Return every year any registered backcast run carries, by ISO."""
    years: dict[str, set[int]] = defaultdict(set)
    for path in sorted((_BACKCAST / "registry").glob("*.json")):
        rec = json.loads(path.read_text())
        if rec.get("iso") in _ISOS:
            years[rec["iso"]].update(int(y) for y in rec.get("years") or ())
    return years


def _keeper_arms_nrc_overlay(iso: str) -> bool:
    """Return whether ``iso``'s keeper recorded an armed daily nuclear overlay."""
    keeper = json.loads((_BACKCAST / "keepers" / f"{iso}.json").read_text())["keeper"]
    reg = json.loads((_BACKCAST / "registry" / f"{keeper}.json").read_text())
    run_config = json.loads((_ROOT / reg["bundle"] / "run_config.json").read_text())
    scenario = run_config["scenario_config"]
    return any(bool(scenario.get(f)) for f in _OVERLAY_FIELDS)


def _uncovered() -> list[tuple[str, int]]:
    """Return every registered ISO-year with neither a table row nor an overlay."""
    years = _registered_years()
    missing = []
    for iso in _ISOS:
        assert years.get(iso), f"{iso}: no registered backcast years found"
        if _keeper_arms_nrc_overlay(iso):
            continue
        table = NUCLEAR_MONTHLY_CF_BY_YEAR.get(iso, {})
        missing += [(iso, y) for y in sorted(years[iso]) if y not in table]
    return missing


def test_every_registered_year_has_a_measured_nuclear_basis() -> None:
    """No registered backcast year reads the forecast fallback CF unnoticed."""
    missing = [m for m in _uncovered() if m not in _PENDING_ROWS]
    assert not missing, (
        "registered backcast ISO-years read the static NUCLEAR_MONTHLY_CF forecast "
        "fallback (no NUCLEAR_MONTHLY_CF_BY_YEAR row and no armed NRC overlay): "
        + ", ".join(f"{iso} {y}" for iso, y in missing)
        + " -- add rows with scripts/data/derive_nuclear_monthly_cf.py (rule 14)"
    )


def test_pending_allowances_are_still_pending() -> None:
    """A pending entry whose row has landed must be deleted, not left standing."""
    landed = sorted(_PENDING_ROWS - set(_uncovered()))
    assert not landed, (
        "these _PENDING_ROWS entries are now covered; delete them: "
        + ", ".join(f"{iso} {y}" for iso, y in landed)
    )


def test_every_row_is_twelve_capped_months() -> None:
    """Each table row is 12 monthly CFs in [0, 1] (the LP availability bound)."""
    for iso, by_year in NUCLEAR_MONTHLY_CF_BY_YEAR.items():
        for year, row in by_year.items():
            assert len(row) == 12, f"{iso} {year}: {len(row)} months"
            assert all(0.0 <= cf <= 1.0 for cf in row), f"{iso} {year}: {row}"
