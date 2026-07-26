"""Unit tests for the NYISO SCR/EDRP demand-response supply blocks.

:mod:`market_sim.data.nyiso_demand_response` turns the Gold-Book-registered
SCR + EDRP capability into one price-responsive pseudo-generator per model zone,
gated on ``ScenarioConfig.nyiso_scr_edrp``. These tests exercise the enrollment
aggregation, the gate, the strike-in-vom construction, and the seasonal
availability profile against the shipped enrollment CSV.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_MAP
from market_sim.data.nyiso_demand_response import (
    _enrollment_path,
    build_nyiso_dr_generators,
    load_scr_edrp_enrollment,
    nyiso_dr_seasonal_availability,
)

# The five NYISO model zones the A-K Gold Book rows aggregate onto.
_MODEL_ZONES = {
    "Upstate_West",
    "Capital_Hudson",
    "Lower_Hudson",
    "NYC",
    "Long_Island",
}

_pytestmark_needs_csv = pytest.mark.skipif(
    not _enrollment_path().exists(),
    reason="NYISO SCR/EDRP enrollment CSV absent (build_nyiso_scr_edrp.py)",
)


def test_demand_response_fuel_code_registered():
    """The pseudo-gen fuel type has a stable integer code (16)."""
    assert FUEL_TYPE_MAP["demand_response"] == 16


def test_gate_off_builds_nothing():
    """No DR generators unless ``nyiso_scr_edrp`` is on — default off."""
    cfg = ScenarioConfig()
    assert cfg.nyiso_scr_edrp is False
    assert build_nyiso_dr_generators(cfg, 2023) == []


@_pytestmark_needs_csv
def test_enrollment_aggregates_to_model_zones():
    """A-K rows fold onto the five model zones with non-negative MW."""
    enr = load_scr_edrp_enrollment(2023)
    assert enr, "expected non-empty 2023 enrollment"
    assert set(enr).issubset(_MODEL_ZONES)
    for zone, mw in enr.items():
        assert mw["summer"] >= 0.0 and mw["winter"] >= 0.0


@_pytestmark_needs_csv
def test_enrollment_year_clamps_to_on_disk_range():
    """Years outside the Gold-Book range clamp to the nearest vintage."""
    lo = load_scr_edrp_enrollment(2019)  # -> earliest (2023)
    hi = load_scr_edrp_enrollment(2099)  # -> latest (2025)
    assert lo == load_scr_edrp_enrollment(2023)
    assert hi == load_scr_edrp_enrollment(2025)


@_pytestmark_needs_csv
def test_build_generators_carry_strike_in_vom():
    """One block per enrolled zone; MC = strike carried in vom, MC-fuel = 0."""
    cfg = ScenarioConfig(nyiso_scr_edrp=True, nyiso_scr_edrp_strike=450.0)
    gens = build_nyiso_dr_generators(cfg, 2023)
    assert gens, "expected DR generators with the gate on"
    for g in gens:
        assert g.fuel_type == "demand_response"
        assert g.zone in _MODEL_ZONES
        assert g.vom == 450.0
        assert g.heat_rate == 0.0
        assert g.pmin_mw == 0.0
        assert g.pmax_mw > 0.0
    # Registered NYCA summer SCR+EDRP is ~1.2-1.5 GW (Gold Book).
    total = sum(g.pmax_mw for g in gens)
    assert 1000.0 < total < 1800.0


@_pytestmark_needs_csv
def test_seasonal_availability_summer_full_winter_derated():
    """Availability is 1.0 in the summer capability period, winter/summer else."""
    prof = nyiso_dr_seasonal_availability(2023, 8760)
    assert set(prof).issubset(_MODEL_ZONES)
    enr = load_scr_edrp_enrollment(2023)
    # Hour 4000 (~mid-June) is summer; hour 100 (early Jan) is winter.
    for zone, series in prof.items():
        assert series.shape == (8760,)
        assert np.isclose(series[4000], 1.0)
        winter_frac = enr[zone]["winter"] / enr[zone]["summer"]
        assert np.isclose(series[100], winter_frac)
        assert np.all(series >= 0.0)
