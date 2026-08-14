"""Tests for the NYISO EAST-tier reserve families and the published-spin gate.

Covers the two config-gated levers added by the nyiso-84 C3c scarcity-formation
lane (the NYCA/East supporting tier, successor to nyiso-83's Zone-J/K work):

* ``nyiso_east_reserve_families`` — the published EAST spin_10 (330 MW) and
  total_30 (1,200 MW) families the model carried nowhere (rule 14 [R-ACCURATE]
  omission; only the EAST 10-minute-total row was represented). Demand-curve
  values are PINNED from the Ancillary Services Manual §6.8 items 2 and 12:
  both $40/MW — NOT the $775 of item 7 (the 10-minute total).
* ``nyiso_spin_reserve_online`` — re-classes the PUBLISHED spinning families
  (nyca_10min_spin, and east_10min_spin when present) onto the online-gated
  class-2 machinery the in-city obligation and path A already use (rule 19
  [R-ONE-MECH]): spinning reserve is synchronized supply by product
  definition, so idle quick-start capacity backs none of it.

Both flags default off and must be byte-inert flag-off.
"""

from types import SimpleNamespace

import numpy as np
import pytest

from market_sim.config.reserve_config import _nyiso_design
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.model.reserves import (
    NYISO_RCPF_EAST_FAMILIES,
    NYISO_SPIN_ONLINE_FAMILIES,
)

T = 48
ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
EAST_ZONES = {"Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"}


def _fa(extra=()):
    """One quick-start gas_ct per zone, plus optional (zone, fuel) pseudo-gens."""
    zone_of = list(range(len(ZONES)))
    fuel_of = [FUEL_TYPE_MAP["gas_ct"]] * len(ZONES)
    for zone_name, fuel_name in extra:
        zone_of.append(ZONES.index(zone_name))
        fuel_of.append(FUEL_TYPE_MAP[fuel_name])
    n = len(zone_of)
    return FleetArrays(
        pmax=np.full(n, 1000.0),
        pmin=np.full(n, 250.0),
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
        nyiso_li_locational_reserve=False,
        nyiso_incity_commitment_obligation=False,
        nyiso_east_reserve_families=False,
        nyiso_spin_reserve_online=False,
        nyiso_ordc_measured_step_span=False,
        commitment_enabled=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _family(design, name):
    for fam in design.families:
        if fam.name == name:
            return fam
    return None


class TestEastFamiliesPinnedValues:
    """The published cells, exactly as pinned from the sources."""

    def test_constant_carries_pinned_asm_values(self):
        # ASM §6.8 item 2 (Eastern spin) and item 12 (Eastern 30-min): $40/MW.
        # Requirements: LRR posting region=EAST, spin_10 330 / total_30 1200.
        assert NYISO_RCPF_EAST_FAMILIES == (
            ("east_10min_spin", 330.0, 0.0, 40.0),
            ("east_30min_total", 1200.0, 0.0, 40.0),
        )

    def test_spin_online_families_are_the_published_spin_cells(self):
        assert NYISO_SPIN_ONLINE_FAMILIES == {"nyca_10min_spin", "east_10min_spin"}


class TestEastFamiliesLadder:
    """nyiso_east_reserve_families: the rule-14 omission fix, flag-gated."""

    def test_flag_off_is_inert(self):
        design = _nyiso_design(_config(), _fa(), T, ZONES)
        assert _family(design, "east_10min_spin") is None
        assert _family(design, "east_30min_total") is None

    def test_flag_on_adds_both_families(self):
        design = _nyiso_design(
            _config(nyiso_east_reserve_families=True), _fa(), T, ZONES
        )
        spin = _family(design, "east_10min_spin")
        t30 = _family(design, "east_30min_total")
        assert spin is not None and t30 is not None
        assert float(spin.requirement[0]) == 330.0
        assert float(t30.requirement[0]) == 1200.0
        # Demand-curve ceiling $40/MW for BOTH (never item 7's $775).
        assert float(np.max(spin.ordc_penalties)) == pytest.approx(40.0)
        assert float(np.max(t30.ordc_penalties)) == pytest.approx(40.0)
        # Natural classes when the gate is off: spin/10min -> quick (1),
        # 30min -> full fleet (0).
        assert spin.reserve_class == 1
        assert t30.reserve_class == 0
        for fam in (spin, t30):
            got = {z for z, m in zip(ZONES, fam.zone_mask) if m}
            assert got == EAST_ZONES

    def test_existing_east_10min_total_untouched(self):
        base = _nyiso_design(_config(), _fa(), T, ZONES)
        design = _nyiso_design(
            _config(nyiso_east_reserve_families=True), _fa(), T, ZONES
        )
        for d in (base, design):
            tot = _family(d, "east_10min_total")
            assert tot is not None
            assert float(tot.requirement[0]) == 1200.0
            assert float(np.max(tot.ordc_penalties)) == pytest.approx(775.0)
        # The ladder flag ADDS families; it removes / re-keys nothing.
        assert {f.name for f in base.families} <= {f.name for f in design.families}


class TestSpinOnlineGate:
    """nyiso_spin_reserve_online: published spin families on the gated class."""

    def test_flag_off_nyca_spin_is_quick_class(self):
        design = _nyiso_design(_config(), _fa(), T, ZONES)
        assert _family(design, "nyca_10min_spin").reserve_class == 1
        assert design.online_gated is None

    def test_gate_reclasses_published_spin_families(self):
        design = _nyiso_design(
            _config(nyiso_east_reserve_families=True, nyiso_spin_reserve_online=True),
            _fa(),
            T,
            ZONES,
        )
        assert _family(design, "nyca_10min_spin").reserve_class == 2
        assert _family(design, "east_10min_spin").reserve_class == 2
        # Non-spin families keep their natural classes.
        assert _family(design, "east_30min_total").reserve_class == 0
        assert _family(design, "east_10min_total").reserve_class == 1
        assert _family(design, "nyca_30min_total").reserve_class == 0
        # Class 2 is the online-gated quick-start set (path-A machinery).
        assert design.online_gated is not None
        assert list(design.online_gated) == [False, False, True]
        np.testing.assert_array_equal(design.eligible[2], design.eligible[1])
        # rho = fleet (pmax-pmin)/pmin = (1000-250)/250 = 3.0 on this fleet.
        assert design.online_rho == pytest.approx(3.0)

    def test_gate_without_ladder_gates_nyca_spin_only(self):
        design = _nyiso_design(_config(nyiso_spin_reserve_online=True), _fa(), T, ZONES)
        assert _family(design, "nyca_10min_spin").reserve_class == 2
        assert _family(design, "east_10min_spin") is None

    def test_mutually_exclusive_with_path_a(self):
        with pytest.raises(ValueError, match="rule 19"):
            _nyiso_design(
                _config(
                    nyiso_spin_reserve_online=True,
                    nyiso_synchronised_reserve=True,
                ),
                _fa(),
                T,
                ZONES,
            )

    def test_composes_with_incity_obligation(self):
        # Under the obligation the class-2 row is the steam-union in-pocket
        # fleet; the published spin families share it (online steam headroom
        # IS synchronized supply). Steam pseudo-gen makes the union differ
        # from quick, so the sharing is observable.
        fa = _fa(extra=[("NYC", "gas_st")])
        design = _nyiso_design(
            _config(
                nyiso_east_reserve_families=True,
                nyiso_spin_reserve_online=True,
                nyiso_incity_commitment_obligation=True,
            ),
            fa,
            T,
            ZONES,
        )
        assert _family(design, "nyca_10min_spin").reserve_class == 2
        assert _family(design, "east_10min_spin").reserve_class == 2
        assert _family(design, "nyc_10min_total").reserve_class == 2
        # Class-2 eligibility = quick | steam (the steam unit is the last gen).
        assert bool(design.eligible[2][-1])
        assert not bool(design.eligible[1][-1])
