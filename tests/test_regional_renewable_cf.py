"""The regional new-build CF table stays tied to its eGRID derivation.

Rule 23 ``[R-FROZEN-DERIVE]``: :data:`REGIONAL_RENEWABLE_CF` is a measured
parameter, so it may move only when a new eGRID vintage lands — never because
a number downstream of it looked better. The reconciliation test is the thing
that makes that enforceable rather than aspirational.

The eGRID workbooks live under ``data/raw/fleet-egrid`` and are hydrated only
by a data profile that asks for them, so the reconciliation skips (rather than
fails) where they are absent. The shape and range assertions below need no data
and always run.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from market_sim.config.constants import (
    NEW_ENTRY_COSTS,
    PPA_COST_RECOVERY_YR,
    REGIONAL_RENEWABLE_CF,
)

REPO = Path(__file__).resolve().parents[1]
DERIVE = REPO / "scripts" / "data" / "derive_regional_renewable_cf.py"


def _load_derive_module():
    spec = importlib.util.spec_from_file_location("derive_regional_cf", DERIVE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_table_shape_and_plausible_range() -> None:
    """Every entry is a real capacity factor for a technology we cost."""
    assert set(REGIONAL_RENEWABLE_CF) <= set(NEW_ENTRY_COSTS)
    for tech, by_iso in REGIONAL_RENEWABLE_CF.items():
        assert by_iso, f"{tech}: empty table"
        for iso, cf in by_iso.items():
            assert iso.isupper(), f"{tech}/{iso}: ISO names are upper-case"
            assert 0.05 < cf < 0.60, f"{tech}/{iso}: implausible capacity factor {cf}"


def test_solar_never_beats_wind_on_the_same_grid() -> None:
    """A physical ordering no US grid violates — a cheap guard on a bad re-derive."""
    for iso, solar_cf in REGIONAL_RENEWABLE_CF["solar"].items():
        wind_cf = REGIONAL_RENEWABLE_CF["wind"].get(iso)
        if wind_cf is not None:
            assert solar_cf < wind_cf, (
                f"{iso}: solar CF {solar_cf} >= wind CF {wind_cf}"
            )


def test_recovery_period_is_shorter_than_book_life() -> None:
    """The PPA basis is a contract term, so it must sit inside the book life."""
    for tech in ("wind", "solar"):
        assert PPA_COST_RECOVERY_YR < NEW_ENTRY_COSTS[tech]["lifetime_yr"]


def test_matches_the_egrid_derivation() -> None:
    """The committed constant reproduces the derive script exactly."""
    mod = _load_derive_module()
    missing = [
        name
        for name in mod.VINTAGE_YEARS.values()
        if not (mod.EGRID_DIR / name).exists()
    ]
    if missing:
        pytest.skip(f"eGRID vintages not hydrated: {', '.join(missing)}")
    assert mod.derive() == REGIONAL_RENEWABLE_CF
