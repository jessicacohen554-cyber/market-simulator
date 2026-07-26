"""Tests for the NYISO Zone-J/K in-city locational reserve mechanisms.

Covers the two config-gated levers added by the in-city must-run lane
(``docs/handoffs/nyiso-incity-mustrun-charter-2026-07.md`` §3, armed by the
owner's 2026-07-26 adjudication reopening the closed C3a "reserve" lever as a
COMMITMENT-OBLIGATION driver):

* ``nyiso_li_locational_reserve`` — the published Long Island (Zone K) ladder
  (10-min 120 MW; 30-min 270 MW off-peak / 540 MW on-peak), which the model
  carried nowhere at all (rule 14 [R-ACCURATE] omission).
* ``nyiso_incity_commitment_obligation`` — re-classes the published NYC + LI
  10-minute families onto an ONLINE-GATED in-pocket obligation class
  (steam ∪ fast-start GT), so meeting the requirement forces dispatch rather
  than counting idle capacity.

Plus the MST §2.15 On-Peak calendar the LI 30-minute diurnal step resolves
through. Both flags default off and must be byte-inert flag-off.
"""

from types import SimpleNamespace

import numpy as np
import pytest

from market_sim.config.reserve_config import _nyiso_design
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.model.reserves import (
    NYISO_LI_30MIN_ONPEAK_MW,
    nerc_holidays,
    nyiso_li_30min_requirement_mw,
    nyiso_onpeak_mask,
)

T = 48
ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]


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


class TestOnPeakCalendar:
    """MST §2.15 Definitions-O: 7 a.m.-11 p.m. EPT, Mon-Fri, ex-NERC holidays."""

    def test_nerc_holidays_2024(self):
        got = set(str(d) for d in nerc_holidays(2024))
        assert got == {
            "2024-01-01",  # New Year's Day
            "2024-05-27",  # Memorial Day (last Monday in May)
            "2024-07-04",  # Independence Day
            "2024-09-02",  # Labor Day (first Monday in September)
            "2024-11-28",  # Thanksgiving (fourth Thursday in November)
            "2024-12-25",  # Christmas Day
        }

    def test_sunday_fixed_holiday_observed_monday(self):
        # 2028-01-01 falls on a Saturday; 2023-01-01 falls on a SUNDAY and is
        # observed Monday 2023-01-02 under the NERC/NAESB convention.
        got = set(str(d) for d in nerc_holidays(2023))
        assert "2023-01-02" in got
        assert "2023-01-01" not in got

    def test_onpeak_hour_window_is_hb7_through_hb22(self):
        # 2024-01-02 is a Tuesday and not a holiday.
        mask = nyiso_onpeak_mask(2024, 48)
        day2 = mask[24:48]
        assert not day2[:7].any()  # HB 0-6 off-peak
        assert day2[7:23].all()  # HB 7-22 on-peak (7 a.m.-11 p.m.)
        assert not day2[23]  # HB 23 off-peak

    def test_weekend_is_all_offpeak(self):
        # 2024-01-06 is a Saturday -> hours 120..167 of the year.
        mask = nyiso_onpeak_mask(2024, 8784)
        assert not mask[120:168].any()

    def test_onpeak_hour_count_matches_calendar(self):
        # 2024: 366 days, 262 weekdays, 6 NERC holidays (all on weekdays)
        # -> 256 on-peak days x 16 h.
        assert int(nyiso_onpeak_mask(2024, 8784).sum()) == 256 * 16

    def test_holiday_hours_are_offpeak(self):
        mask = nyiso_onpeak_mask(2024, 8784)
        july4 = (31 + 29 + 31 + 30 + 31 + 30 + 3) * 24  # start of Jul 4
        assert not mask[july4 : july4 + 24].any()


class TestLiRequirementSeries:
    def test_two_published_levels_only(self):
        req = nyiso_li_30min_requirement_mw(2024, 8784, 270.0, 540.0)
        assert set(np.unique(req)) == {270.0, 540.0}

    def test_onpeak_hours_carry_the_onpeak_level(self):
        req = nyiso_li_30min_requirement_mw(2024, 8784, 270.0, 540.0)
        mask = nyiso_onpeak_mask(2024, 8784)
        assert np.all(req[mask] == 540.0)
        assert np.all(req[~mask] == 270.0)


class TestLiLocationalLadder:
    def test_default_off_no_li_families(self):
        design = _nyiso_design(_config(), _fa(), T, ZONES)
        assert _family(design, "li_10min_total") is None
        assert _family(design, "li_30min_total") is None

    def test_flag_on_adds_both_published_li_families(self):
        design = _nyiso_design(
            _config(nyiso_li_locational_reserve=True), _fa(), T, ZONES
        )
        ten = _family(design, "li_10min_total")
        thirty = _family(design, "li_30min_total")
        assert ten is not None and thirty is not None
        # Published cells: 120 MW flat; 270/540 diurnal.
        assert np.all(ten.requirement == 120.0)
        assert set(np.unique(thirty.requirement)) == {270.0, NYISO_LI_30MIN_ONPEAK_MW}

    def test_li_families_are_zone_k_only(self):
        design = _nyiso_design(
            _config(nyiso_li_locational_reserve=True), _fa(), T, ZONES
        )
        li_col = ZONES.index("Long_Island")
        for name in ("li_10min_total", "li_30min_total"):
            zmask = _family(design, name).zone_mask
            assert zmask[li_col]
            assert zmask.sum() == 1

    def test_li_30min_ordc_widths_translate_with_requirement(self):
        """The diurnal levels ARE the published curve span, so widths scale."""
        design = _nyiso_design(
            _config(nyiso_li_locational_reserve=True), _fa(), T, ZONES
        )
        fam = _family(design, "li_30min_total")
        widths = np.asarray(fam.ordc_step_widths)
        assert widths.ndim == 2  # (n_steps, T) — per-hour, not static
        total = widths.sum(axis=0)
        np.testing.assert_allclose(total, fam.requirement, rtol=1e-9)

    def test_li_span_scaling_does_not_leak_onto_seny(self):
        """Scoped per-family: SENY keeps its static curve (rule 19)."""
        base = _nyiso_design(_config(), _fa(), T, ZONES)
        with_li = _nyiso_design(
            _config(nyiso_li_locational_reserve=True), _fa(), T, ZONES
        )
        for name in ("seny_30min_total", "nyc_30min_total", "nyc_10min_total"):
            np.testing.assert_array_equal(
                np.asarray(_family(base, name).ordc_step_widths),
                np.asarray(_family(with_li, name).ordc_step_widths),
            )


class TestInCityCommitmentObligation:
    def test_default_off_no_online_gating(self):
        design = _nyiso_design(_config(), _fa(), T, ZONES)
        assert design.online_gated is None
        assert design.eligible.shape[0] == 2

    def test_flag_on_adds_online_gated_obligation_class(self):
        design = _nyiso_design(
            _config(nyiso_incity_commitment_obligation=True), _fa(), T, ZONES
        )
        assert design.eligible.shape[0] == 3
        assert list(design.online_gated) == [False, False, True]

    def test_obligation_class_includes_steam(self):
        fa = _fa(extra=[("NYC", "gas_st")])
        steam_col = len(ZONES)
        base = _nyiso_design(_config(), fa, T, ZONES)
        # Steam is NOT in the idle-allowed quick-start class...
        assert not base.eligible[1][steam_col]
        design = _nyiso_design(
            _config(nyiso_incity_commitment_obligation=True), fa, T, ZONES
        )
        # ...but IS in the online-gated in-pocket obligation class.
        assert design.eligible[2][steam_col]

    def test_nyc_10min_family_moves_to_obligation_class(self):
        design = _nyiso_design(
            _config(nyiso_incity_commitment_obligation=True), _fa(), T, ZONES
        )
        assert _family(design, "nyc_10min_total").reserve_class == 2
        # The 30-minute families stay on the full thermal class.
        assert _family(design, "nyc_30min_total").reserve_class == 0
        assert _family(design, "seny_30min_total").reserve_class == 0

    def test_li_10min_family_moves_to_obligation_class_when_present(self):
        design = _nyiso_design(
            _config(
                nyiso_incity_commitment_obligation=True,
                nyiso_li_locational_reserve=True,
            ),
            _fa(),
            T,
            ZONES,
        )
        assert _family(design, "li_10min_total").reserve_class == 2
        assert _family(design, "li_30min_total").reserve_class == 0

    def test_east_10min_stays_on_quick_start_class(self):
        """Only the in-POCKET (J/K) 10-minute families are obligations."""
        design = _nyiso_design(
            _config(nyiso_incity_commitment_obligation=True), _fa(), T, ZONES
        )
        assert _family(design, "east_10min_total").reserve_class == 1

    def test_online_rho_within_physical_band(self):
        design = _nyiso_design(
            _config(nyiso_incity_commitment_obligation=True), _fa(), T, ZONES
        )
        assert 0.5 <= design.online_rho <= 4.0

    def test_mutually_exclusive_with_synchronised_reserve(self):
        """Same phenomenon, two mechanisms — rule 19 [R-ONE-MECH]."""
        with pytest.raises(ValueError, match="rule 19"):
            _nyiso_design(
                _config(
                    nyiso_incity_commitment_obligation=True,
                    nyiso_synchronised_reserve=True,
                ),
                _fa(),
                T,
                ZONES,
            )


class TestRuleNineteenFloorSubstitution:
    """The obligation REPLACES the NYC/LI ST_GAS floor limbs (charter §2)."""

    @staticmethod
    def _specs():
        from market_sim.config.iso_configs import RELIABILITY_FLOOR_REGISTRY

        return RELIABILITY_FLOOR_REGISTRY.get("NYISO", [])

    def test_default_off_keeps_every_limb(self):
        from market_sim.config.iso_configs import (
            drop_obligation_owned_reliability_specs,
        )

        specs = self._specs()
        assert specs, "NYISO reliability-floor registry should be populated"
        kept = drop_obligation_owned_reliability_specs(specs, _config())
        assert kept is specs  # byte-identical no-op

    def test_obligation_drops_nyc_and_li_steam_limbs(self):
        from market_sim.config.iso_configs import (
            drop_obligation_owned_reliability_specs,
        )

        specs = self._specs()
        kept = drop_obligation_owned_reliability_specs(
            specs, _config(nyiso_incity_commitment_obligation=True)
        )
        dropped = {(s.zone, s.plant_class) for s in specs} - {
            (s.zone, s.plant_class) for s in kept
        }
        assert dropped == {("NYC", "ST_GAS"), ("Long_Island", "ST_GAS")}

    def test_non_pocket_steam_limb_survives(self):
        """Capital_Hudson is outside the load pockets — untouched."""
        from market_sim.config.iso_configs import (
            drop_obligation_owned_reliability_specs,
        )

        kept = drop_obligation_owned_reliability_specs(
            self._specs(), _config(nyiso_incity_commitment_obligation=True)
        )
        assert any(
            s.zone == "Capital_Hudson" and s.plant_class == "ST_GAS" for s in kept
        )

    def test_other_downstate_classes_survive(self):
        """Only ST_GAS is superseded; LI CT_PEAKER limbs stay."""
        from market_sim.config.iso_configs import (
            drop_obligation_owned_reliability_specs,
        )

        kept = drop_obligation_owned_reliability_specs(
            self._specs(), _config(nyiso_incity_commitment_obligation=True)
        )
        assert any(
            s.zone == "Long_Island" and s.plant_class == "CT_PEAKER" for s in kept
        )


class TestObligationRhoFallback:
    """rho is a live fleet computation, with a documented neutral fallback.

    The real NYISO solve logs ``rho=1.00``. That is NOT the computation
    failing — it is the documented fallback for a fleet whose tranches carry
    ``pmin == 0`` (no unit satisfies ``pmin > 0 and pmax > pmin``), which is
    the case for the legacy equal-width bins NYISO uses. The gate is still a
    real constraint at rho = 1 (``R <= sum_g P``: idle capacity backs nothing);
    only the headroom multiplier is neutral rather than fleet-derived.
    Pinned here so a later reader does not mistake 1.00 for a broken average.
    """

    def test_rho_is_computed_from_the_fleet_when_pmin_is_positive(self):
        design = _nyiso_design(
            _config(nyiso_incity_commitment_obligation=True), _fa(), T, ZONES
        )
        # fixture: pmin 250, pmax 1000 -> (1000-250)/250 = 3.0
        assert design.online_rho == pytest.approx(3.0)

    def test_rho_falls_back_to_neutral_when_no_unit_has_positive_pmin(self):
        fa = _fa()
        fa.pmin = np.zeros_like(fa.pmin)  # the real NYISO legacy-bin case
        design = _nyiso_design(
            _config(nyiso_incity_commitment_obligation=True), fa, T, ZONES
        )
        assert design.online_rho == pytest.approx(1.0)
        # The gate is still installed and still online-gated.
        assert list(design.online_gated) == [False, False, True]
