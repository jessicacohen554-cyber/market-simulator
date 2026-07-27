"""Tests for policy/constraints.py: the LP constraint-row extension point.

Covers build_mass_cap_dispatch_kwargs (G-29,
docs/handoffs/emissions-mass-cap-plan-2026-07.md "Non-blocking follow-ons"):
the wire-through that lets the backcast calibration harness
(scripts/run_calibration.py::run_year) exercise the mass-cap row, which it
previously never reached at all.
"""

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.policy.constraints import build_mass_cap_dispatch_kwargs

_CAISO_ZONES = ["NP15", "ZP26", "SP15", "WECC_import"]


def _fleet(zone_names):
    """Build a tiny FleetArrays, one gas_cc generator per zone in ``zone_names``.

    The caller must pass this SAME list (same order) to
    build_mass_cap_dispatch_kwargs — the row's membership vector is indexed
    by this order via fleet_arrays.zone_idx, so a mismatched order silently
    mis-assigns coefficients to the wrong zone.
    """
    generators = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=zone,
            fuel_type="gas_cc",
            pmax_mw=100.0,
            pmin_mw=0.0,
            eford=0.0,
            emission_rate_co2=0.4,
            plant_code=0,
        )
        for i, zone in enumerate(zone_names)
    ]
    return generators_to_fleet_arrays(generators, zone_names, hours=4)


class TestBuildMassCapDispatchKwargs:
    """The calibration-harness seam: a mass-cap-enabled config actually
    builds the LP row's dispatch_kwargs, previously unreachable here."""

    def test_disabled_returns_empty_dict(self):
        # Default (mass_cap_enabled=False) -> {} -> no dispatch_kwargs change,
        # identical LP. This is the byte-identity gate for every ISO/year
        # that does not opt in.
        config = ScenarioConfig(iso="CAISO", mode="backcast")
        fleet = _fleet(_CAISO_ZONES)
        out = build_mass_cap_dispatch_kwargs(config, 2024, _CAISO_ZONES, fleet)
        assert out == {}

    def test_no_program_iso_returns_empty_dict(self):
        # ERCOT has no cap-and-trade program at all; enabling the flag is a
        # no-op regardless.
        zone_names = ["North", "South_Central"]
        config = ScenarioConfig(iso="ERCOT", mode="backcast", mass_cap_enabled=True)
        fleet = _fleet(zone_names)
        out = build_mass_cap_dispatch_kwargs(config, 2024, zone_names, fleet)
        assert out == {}

    def test_mass_cap_enabled_backcast_config_builds_cap_rows(self):
        # The required case: a mass-cap-enabled backcast config for a program
        # ISO actually produces the row's coefficients/RHS/labels.
        config = ScenarioConfig(
            iso="CAISO", mode="backcast", mass_cap_enabled=True, mass_cap_tons=1.0e6
        )
        fleet = _fleet(_CAISO_ZONES)
        out = build_mass_cap_dispatch_kwargs(config, 2024, _CAISO_ZONES, fleet)

        assert set(out) == {"mass_cap_coeffs", "mass_cap_rhs", "mass_cap_labels"}
        coeffs = np.asarray(out["mass_cap_coeffs"])
        assert coeffs.shape == (1, fleet.emission_rate.size)
        # WECC_import (index 3) is a non-member external node (m_zone=0); its
        # generator gets a zero coefficient, the three in-state generators
        # (NP15/ZP26/SP15) do not.
        np.testing.assert_array_equal(coeffs[0], [0.4, 0.4, 0.4, 0.0])
        assert out["mass_cap_rhs"].tolist() == pytest.approx([1.0e6])
        assert out["mass_cap_labels"] == ["carb"]

    def test_published_budget_used_when_tons_unset(self):
        from market_sim.config.constants import CARB_ALLOWANCE_BUDGET

        config = ScenarioConfig(iso="CAISO", mode="backcast", mass_cap_enabled=True)
        fleet = _fleet(_CAISO_ZONES)
        out = build_mass_cap_dispatch_kwargs(config, 2024, _CAISO_ZONES, fleet)
        assert out["mass_cap_rhs"] == pytest.approx([CARB_ALLOWANCE_BUDGET[2024] * 1e6])

    def test_quarantined_year_stays_inert(self):
        # 2026 (H1-2026 holdout) has no published CARB budget landed (rule
        # 22); the row stays inert even with the flag on.
        config = ScenarioConfig(iso="CAISO", mode="backcast", mass_cap_enabled=True)
        fleet = _fleet(_CAISO_ZONES)
        out = build_mass_cap_dispatch_kwargs(config, 2026, _CAISO_ZONES, fleet)
        assert out == {}
