"""Conditional dual-fuel exemption in the NEISO cold-snap gas derate.

Guards the rule-19 [R-ONE-MECH] scope correction added by session neiso-110
(``docs/FINDING-neiso110-winter-oil-driver-2026-09-16.md``): the cold-snap
derate exempts every EIA-860 dual-fuel unit on the premise that
``apply_dual_fuel_pricing`` has switched it to oil, but that switch is
``mc = min(gas, oil)`` and therefore fires only where delivered gas has
actually reached the oil parity. ``neiso_coldsnap_derate_dualfuel_unswitched``
turns the premise into a per-hour condition.

The load-bearing property, and the reason the correction cannot overreach:
**where the premise holds, the arm is byte-identical to the legacy exemption.**
"""

from __future__ import annotations

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import dual_fuel_plant_groups
from market_sim.model.interchange.neiso import inject_neiso_gas_coldsnap_derate

_T = 8760
_YEAR = 2022
_T0, _SLOPE, _CAP = -7.0, 0.018, 0.20


class _Fleet:
    """Minimal FleetArrays stand-in: the derate touches only these four fields."""

    def __init__(self, plant_codes: list[int]) -> None:
        n = len(plant_codes)
        self.plant_group = np.array(["CC_REGULAR"] * n)
        self.plant_code = np.array(plant_codes)
        self.pmax = np.full(n, 100.0)
        self.availability = np.ones((n, _T))


def _codes() -> list[int]:
    """[a registered dual-fuel CC_REGULAR plant, a non-dual sentinel]."""
    dual = [p for p, g in dual_fuel_plant_groups() if g == "CC_REGULAR"]
    assert dual, "no dual-fuel CC_REGULAR plant registered"
    return [int(dual[0]), 999999]


def _run(mask: np.ndarray | None) -> np.ndarray:
    fleet = _Fleet(_codes())
    assert inject_neiso_gas_coldsnap_derate(
        fleet, "NEISO", _YEAR, _T0, _SLOPE, _CAP, dual_switch_active=mask
    )
    return fleet.availability.copy()


def test_field_defaults_off() -> None:
    """Default-off, so every existing run stays byte-identical."""
    assert (
        ScenarioConfig(iso="NEISO").neiso_coldsnap_derate_dualfuel_unswitched is False
    )


def test_legacy_exempts_dual_fuel_and_derates_the_rest() -> None:
    avail = _run(None)
    assert np.all(avail[0] == 1.0), "dual-fuel row must be exempt with mask=None"
    assert avail[1].mean() < 1.0, "non-dual row must be derated"


def test_switch_always_active_is_byte_identical_to_legacy() -> None:
    """The correction cannot remove an exemption the premise actually earns."""
    assert np.array_equal(_run(np.ones(_T, dtype=bool)), _run(None))


def test_switch_never_active_derates_dual_fuel_like_any_gas_unit() -> None:
    """Where the premise fails the unit is, in that hour, a plain gas unit."""
    armed = _run(np.zeros(_T, dtype=bool))
    assert np.array_equal(armed[0], armed[1])


def test_non_dual_rows_are_untouched_by_the_gate() -> None:
    """The correction is scoped to the exemption; it never widens the derate."""
    legacy = _run(None)
    for mask in (np.zeros(_T, dtype=bool), np.ones(_T, dtype=bool)):
        assert np.array_equal(_run(mask)[1], legacy[1])


def test_partial_mask_derates_exactly_the_unswitched_hours() -> None:
    mask = np.zeros(_T, dtype=bool)
    mask[: _T // 2] = True  # switch fires in the first half only
    armed, legacy = _run(mask), _run(None)
    first, second = slice(0, _T // 2), slice(_T // 2, _T)
    assert np.array_equal(armed[0][first], legacy[0][first]), "exempt half must hold"
    derated = _run(np.zeros(_T, dtype=bool))
    assert np.array_equal(armed[0][second], derated[0][second]), "other half derated"


def test_non_neiso_iso_is_a_no_op() -> None:
    fleet = _Fleet(_codes())
    assert not inject_neiso_gas_coldsnap_derate(
        fleet, "PJM", _YEAR, _T0, _SLOPE, _CAP, dual_switch_active=np.zeros(_T, bool)
    )
    assert np.all(fleet.availability == 1.0)
