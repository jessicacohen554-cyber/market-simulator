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
        import market_sim.data.online_reserve_rho as orr

        design = _nyiso_design(
            _config(nyiso_incity_commitment_obligation=True), _fa(), T, ZONES
        )
        lo, hi = orr.RHO_CLIP
        assert lo <= design.online_rho <= hi

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
    """rho has a THREE-tier identification, in rule 14 [R-ACCURATE] order.

    1. the MEASURED CAMPD statistic (``data.online_reserve_rho``) — the
       aggregate 10-minute deliverable headroom per MW on-line over the
       eligible fleet's own operating record;
    2. the eligible fleet's own cap-weighted ``(pmax-pmin)/pmin`` at min load —
       correct on a fleet carrying real ``pmin`` values, but DEAD CODE on the
       binned/tranche fleets NYISO actually runs, where must-run rides
       ``min_gen`` and ``pmin`` is identically zero;
    3. a neutral 1.0, which rule 21 [R-DOF] does not admit in a keeper and
       which the design logs a warning for.

    Tiers 2 and 3 are exercised with the measured loader patched OFF, so these
    stay unit tests of the fallback contract rather than of whichever ISO
    artifacts happen to be on disk. The gate is a real constraint at every tier
    (``R <= rho * sum_g P``: idle capacity backs nothing); only the multiplier
    differs.
    """

    @staticmethod
    def _no_measured(monkeypatch):
        """Patch the measured seam to miss, exposing the pmin/neutral tiers."""
        import market_sim.data.online_reserve_rho as orr

        monkeypatch.setattr(orr, "load_online_rho", lambda iso, family_set: None)

    def test_measured_statistic_wins_when_the_artifact_covers_the_iso(
        self, monkeypatch
    ):
        import market_sim.data.online_reserve_rho as orr

        measured = orr.OnlineReserveRho(
            iso="NYISO",
            family_set="incity_obligation",
            mechanism="nyiso_incity_commitment_obligation",
            rho=0.8,
            rho_minload=1.9,
            rho_fullhour=0.7,
            online_unit_hours=401361,
            campd_coverage_frac=0.955,
            years="2023-2024-2025",
        )
        monkeypatch.setattr(orr, "load_online_rho", lambda iso, family_set: measured)
        design = _nyiso_design(
            _config(nyiso_incity_commitment_obligation=True), _fa(), T, ZONES
        )
        # The fixture's own pmin path would say 3.0; the measurement outranks it.
        assert design.online_rho == pytest.approx(0.8)

    def test_measured_statistic_solves_at_its_own_measurement(self, monkeypatch):
        """A measurement inside the band returns THE MEASUREMENT.

        Owner ruling 2026-08-22 (nyiso-151, card nyiso-145 option A): the
        uncited 0.5 floor is DELETED — ``RHO_CLIP = (0.0, 4.0)`` — so the
        real NYISO values (0.3014 / 0.2011), which the old floor overrode,
        now reach the LP as measured. Pinned so a re-introduced floor cannot
        silently override data again.
        """
        import market_sim.data.online_reserve_rho as orr

        measured = orr.OnlineReserveRho(
            iso="NYISO",
            family_set="incity_obligation",
            mechanism="nyiso_incity_commitment_obligation",
            rho=0.3014,
            rho_minload=1.2462,
            rho_fullhour=0.2864,
            online_unit_hours=401361,
            campd_coverage_frac=0.955,
            years="2023-2024-2025",
        )
        monkeypatch.setattr(orr, "load_online_rho", lambda iso, family_set: measured)
        design = _nyiso_design(
            _config(nyiso_incity_commitment_obligation=True), _fa(), T, ZONES
        )
        assert orr.RHO_CLIP == (0.0, 4.0)
        assert design.online_rho == pytest.approx(0.3014)

    def test_rho_is_computed_from_the_fleet_when_pmin_is_positive(self, monkeypatch):
        self._no_measured(monkeypatch)
        design = _nyiso_design(
            _config(nyiso_incity_commitment_obligation=True), _fa(), T, ZONES
        )
        # fixture: pmin 250, pmax 1000 -> (1000-250)/250 = 3.0
        assert design.online_rho == pytest.approx(3.0)

    def test_rho_falls_back_to_neutral_when_no_unit_has_positive_pmin(
        self, monkeypatch
    ):
        self._no_measured(monkeypatch)
        fa = _fa()
        fa.pmin = np.zeros_like(fa.pmin)  # the real NYISO legacy-bin case
        design = _nyiso_design(
            _config(nyiso_incity_commitment_obligation=True), fa, T, ZONES
        )
        assert design.online_rho == pytest.approx(1.0)
        # The gate is still installed and still online-gated.
        assert list(design.online_gated) == [False, False, True]
