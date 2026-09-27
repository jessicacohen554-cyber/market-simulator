"""The ST_GAS_PEAKER_PLANTS skip is scoped to the plant's ST_GAS slice (PJM-NEXT-5).

The registry is defined on a plant's gas-steam slice, so a coal or CC unit at a
listed plant (Montour's pre-2023 coal units) keeps its measured outage windows.
"""

from __future__ import annotations

from market_sim.data.outages import ST_GAS_PEAKER_PLANTS
from scripts.data.derive_campd_unit_outages import _is_listed_peaker_steam


def test_listed_plant_gas_steam_unit_is_skipped() -> None:
    """A listed plant's ST_GAS unit carries no overlay (unchanged behaviour)."""
    code = next(iter(ST_GAS_PEAKER_PLANTS))
    assert _is_listed_peaker_steam(code, "ST_GAS")


def test_listed_plant_coal_and_cc_units_are_kept() -> None:
    """A listed plant's coal / CC units keep their windows (the repaired defect)."""
    code = next(iter(ST_GAS_PEAKER_PLANTS))
    for group in ("COAL", "CC_REGULAR", "ST_CHP"):
        assert not _is_listed_peaker_steam(code, group)


def test_unlisted_plant_is_never_skipped() -> None:
    """An unlisted plant's gas-steam unit is never skipped by this helper."""
    code = max(ST_GAS_PEAKER_PLANTS) + 1
    assert not _is_listed_peaker_steam(code, "ST_GAS")
