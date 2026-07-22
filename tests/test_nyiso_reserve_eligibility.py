"""Tests for NYISO reserve-SUPPLY eligibility levers (issue #1344, lever 3).

Covers the two config-gated unions in ``_nyiso_design`` that add non-thermal
resources to the energy+reserve co-optimization's eligible supply:

* ``nyiso_hydro_reserve_eligible`` — conventional hydro into BOTH the full
  (30-min) and quick-start (10-min) classes (lever 3 step 1, East/NYCA).
* ``nyiso_scr_edrp_reserve_eligible`` — SCR/EDRP demand response into the FULL
  (30-min) class ONLY, scoped to the downstate SENY zones (lever 3 step 2).

Both default off (byte-identical) and are grounded market-design inputs (NYISO
Ancillary Services Manual), never residual tunes.
"""

from types import SimpleNamespace

import numpy as np

from market_sim.config.reserve_config import _nyiso_design
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays

T = 48
ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
DOWNSTATE = {"Lower_Hudson", "NYC", "Long_Island"}


def _fa(extra=()):
    """Thermal gas unit per zone, plus optional (zone, fuel) extra pseudo-gens.

    ``extra`` is a list of (zone_name, fuel_type_name) — used to inject hydro or
    demand_response blocks in specific zones.
    """
    zone_of = list(range(len(ZONES)))
    fuel_of = [FUEL_TYPE_MAP["gas_ct"]] * len(ZONES)
    for zone_name, fuel_name in extra:
        zone_of.append(ZONES.index(zone_name))
        fuel_of.append(FUEL_TYPE_MAP[fuel_name])
    n = len(zone_of)
    return FleetArrays(
        pmax=np.full(n, 1000.0),
        pmin=np.zeros(n),
        heat_rate=np.full(n, 8.0),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.array(zone_of, dtype=int),
        fuel_type_idx=np.array(fuel_of, dtype=int),
        availability=np.ones((n, T)),
        unit_ids=[f"g{i}" for i in range(n)],
        efficiency_bin=np.zeros(n, dtype=int),
        plant_code=np.zeros(n, dtype=int),
    )


def _config(**overrides):
    base = dict(
        iso="NYISO",
        weather_year=2024,
        nyiso_rcpf_products=None,
        nyiso_rcpf_locational=None,
        nyiso_synchronised_reserve=False,
        nyiso_rcpf_enabled=False,
        nyiso_dynamic_reserve_requirements=False,
        nyiso_hydro_reserve_eligible=False,
        nyiso_scr_edrp_reserve_eligible=False,
        commitment_enabled=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestHydroReserveEligibility:
    def test_default_off_hydro_not_eligible(self):
        fa = _fa(extra=[("Upstate_West", "hydro")])
        design = _nyiso_design(_config(), fa, T, ZONES)
        hydro_col = len(ZONES)  # appended after the per-zone thermal gens
        assert not design.eligible[0][hydro_col]  # full (30-min)
        assert not design.eligible[1][hydro_col]  # quick (10-min)

    def test_flag_on_hydro_eligible_both_classes(self):
        fa = _fa(extra=[("Upstate_West", "hydro")])
        design = _nyiso_design(_config(nyiso_hydro_reserve_eligible=True), fa, T, ZONES)
        hydro_col = len(ZONES)
        assert design.eligible[0][hydro_col]  # full (30-min)
        assert design.eligible[1][hydro_col]  # quick (10-min)


class TestScrEdrpReserveEligibility:
    def test_default_off_dr_not_eligible(self):
        fa = _fa(extra=[("NYC", "demand_response")])
        design = _nyiso_design(_config(), fa, T, ZONES)
        dr_col = len(ZONES)
        assert not design.eligible[0][dr_col]
        assert not design.eligible[1][dr_col]

    def test_downstate_dr_eligible_30min_only(self):
        fa = _fa(extra=[("NYC", "demand_response")])
        design = _nyiso_design(
            _config(nyiso_scr_edrp_reserve_eligible=True), fa, T, ZONES
        )
        dr_col = len(ZONES)
        assert design.eligible[0][dr_col]  # full (30-min) — SCR is 30-min
        assert not design.eligible[1][dr_col]  # NOT quick (10-min)

    def test_upstate_dr_not_eligible_when_scoped(self):
        # DR in Upstate_West (not a SENY zone) stays ineligible with the flag on:
        # the union is scoped to the downstate reserve tail.
        fa = _fa(extra=[("Upstate_West", "demand_response")])
        design = _nyiso_design(
            _config(nyiso_scr_edrp_reserve_eligible=True), fa, T, ZONES
        )
        dr_col = len(ZONES)
        assert not design.eligible[0][dr_col]
        assert not design.eligible[1][dr_col]

    def test_each_downstate_zone_covered(self):
        extra = [(z, "demand_response") for z in ("Lower_Hudson", "NYC", "Long_Island")]
        fa = _fa(extra=extra)
        design = _nyiso_design(
            _config(nyiso_scr_edrp_reserve_eligible=True), fa, T, ZONES
        )
        for k in range(len(extra)):
            assert design.eligible[0][len(ZONES) + k]

    def test_hydro_and_dr_compose(self):
        # Both levers on together: hydro (upstate, both classes) + downstate DR
        # (30-min only) are independently unioned.
        fa = _fa(extra=[("Upstate_West", "hydro"), ("NYC", "demand_response")])
        design = _nyiso_design(
            _config(
                nyiso_hydro_reserve_eligible=True,
                nyiso_scr_edrp_reserve_eligible=True,
            ),
            fa,
            T,
            ZONES,
        )
        hydro_col, dr_col = len(ZONES), len(ZONES) + 1
        assert design.eligible[0][hydro_col] and design.eligible[1][hydro_col]
        assert design.eligible[0][dr_col] and not design.eligible[1][dr_col]
