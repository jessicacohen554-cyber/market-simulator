"""Which fuels enter the accredited-supply ledger (FFR-1C / audit FR-3, FR-26).

The forecast-readiness audit's FR-26 names this exact missing test: "none
asserts which fuels enter the accredited ledger (FR-3)". Hydro was dispatched
through the energy-budget path but contributed 0 MW to
:func:`accredited_firm_capacity_mw` for every ISO, because that ledger is built
from the persistent ``fleet`` and hydro never enters it — a ledger-structure
exclusion FF-2B measured at CAISO 3,601 MW / NYISO 3,343 MW / NEISO 30 MW of
dispatched-but-unaccredited nameplate
(docs/handoffs/ff-2b-adequacy-basis-2026-07.md §4).

These tests are hermetic: the hydro budget loader is patched with fixtures, so
they assert the LEDGER's composition and the published credits, never the
current on-disk EIA vintage.
"""

import unittest
from unittest import mock

import numpy as np

from market_sim.config.constants import (
    EFORD,
    HYDRO_ACCREDITATION_CREDIT_BY_ISO,
    RENEWABLE_CAPACITY_CREDIT,
)
from market_sim.data.eia923 import EIA923_LATEST_FINAL_VINTAGE
from market_sim.data.fleet import Generator
from market_sim.model.capacity import (
    accredited_firm_capacity_mw,
    modelled_hydro_nameplate_mw,
    resolve_hydro_capacity_credit,
)

# The dispatched-but-unaccredited hydro nameplate FF-2B measured per ISO, the
# gap this lane closes (ff-2b-adequacy-basis-2026-07.md §2.2/§2.3/§4).
FF2B_HYDRO_NAMEPLATE_MW = {"CAISO": 3_601.0, "NYISO": 3_343.0, "NEISO": 30.0}


class _FakeBudget:
    """Minimal :class:`~market_sim.data.hydro.HydroBudget` stand-in."""

    def __init__(self, rows):
        # rows: (plant_id, zone, max_mw, annual_mwh)
        self.plant_ids = np.array([r[0] for r in rows], dtype=int)
        self.zones = [r[1] for r in rows]
        self.max_mw = np.array([r[2] for r in rows], dtype=float)
        self.monthly_energy = np.array(
            [[r[3] / 12.0] * 12 for r in rows], dtype=float
        ).reshape(len(rows), 12)
        self.plant_names = [f"plant_{r[0]}" for r in rows]
        self.min_mw = np.zeros(len(rows), dtype=float)


def _patch_budget(rows):
    """Patch the hydro budget loader with ``rows`` and clear the ledger cache."""
    modelled_hydro_nameplate_mw.cache_clear()
    return mock.patch(
        "market_sim.data.hydro.load_hydro_budget",
        lambda iso, year, **kw: _FakeBudget(rows),
    )


def _thermal(unit_id="g1", fuel="gas_cc", mw=1_000.0, zone="NP15"):
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone=zone,
        fuel_type=fuel,
        pmax_mw=mw,
        vom=2.0,
        eford=EFORD[fuel],
    )


class TestHydroAccreditationCredits(unittest.TestCase):
    """Every credit is the ISO's published factor, never a tuned value."""

    def test_published_credits_are_the_registry_values(self):
        # Published anchors, one per ISO — see the constant's citation block.
        self.assertAlmostEqual(HYDRO_ACCREDITATION_CREDIT_BY_ISO["CAISO"], 0.7041)
        self.assertAlmostEqual(HYDRO_ACCREDITATION_CREDIT_BY_ISO["NYISO"], 0.3844)
        self.assertAlmostEqual(HYDRO_ACCREDITATION_CREDIT_BY_ISO["MISO"], 0.62)
        self.assertAlmostEqual(HYDRO_ACCREDITATION_CREDIT_BY_ISO["PJM"], 0.38)
        # NEISO (capx-S4): Σ summer SCC of ISO-NE's ACTIVE conventional-hydro
        # fleet (Aug-2026 SCC Monthly Report, 1,396.472 MW) over the model's
        # own accreditation basis (1,899.5 MW) — both halves published/derived,
        # never tuned; see the constant's citation block.
        self.assertAlmostEqual(
            HYDRO_ACCREDITATION_CREDIT_BY_ISO["NEISO"], 1_396.472 / 1_899.5
        )
        for iso, credit in HYDRO_ACCREDITATION_CREDIT_BY_ISO.items():
            with self.subTest(iso=iso):
                self.assertEqual(resolve_hydro_capacity_credit(iso), credit)

    def test_unpublished_isos_take_the_generic_class_derate(self):
        # ERCOT has no published hydro accreditation product (energy-only): it
        # takes the generic published derate, never another ISO's value
        # (rule 25). NEISO left this list at capx-S4 (2026-08-30) when its
        # per-resource SCC aggregate landed in the registry.
        generic = RENEWABLE_CAPACITY_CREDIT["hydro"]
        for iso in ("ERCOT",):
            with self.subTest(iso=iso):
                self.assertNotIn(iso, HYDRO_ACCREDITATION_CREDIT_BY_ISO)
                self.assertEqual(resolve_hydro_capacity_credit(iso), generic)
        self.assertEqual(resolve_hydro_capacity_credit(None), generic)

    def test_published_credits_are_fractions(self):
        for iso, credit in HYDRO_ACCREDITATION_CREDIT_BY_ISO.items():
            with self.subTest(iso=iso):
                self.assertGreater(credit, 0.0)
                self.assertLessEqual(credit, 1.0)


class TestModelledHydroNameplate(unittest.TestCase):
    """The accreditation basis is the model's OWN dispatched hydro fleet."""

    def test_applies_the_build_hydro_fleet_filters(self):
        rows = [
            (1, "NP15", 500.0, 1e6),  # counted
            (2, "SP15_rest", 250.0, 5e5),  # counted
            (3, "NOT_A_ZONE", 900.0, 1e6),  # dropped: outside the model zones
            (4, "NP15", 0.0, 1e6),  # dropped: no MW envelope
            (5, "NP15", 400.0, 0.0),  # dropped: no energy budget
        ]
        with _patch_budget(rows):
            self.assertAlmostEqual(modelled_hydro_nameplate_mw("CAISO", 2026), 750.0)

    def test_missing_budget_credits_zero_never_fabricates(self):
        modelled_hydro_nameplate_mw.cache_clear()

        def _boom(iso, year, **kw):
            raise ValueError("no EIA-923 hydro generation")

        with mock.patch("market_sim.data.hydro.load_hydro_budget", _boom):
            self.assertEqual(modelled_hydro_nameplate_mw("CAISO", 2030), 0.0)

    def test_unknown_iso_credits_zero(self):
        modelled_hydro_nameplate_mw.cache_clear()
        self.assertEqual(modelled_hydro_nameplate_mw("NOT_AN_ISO", 2026), 0.0)


class TestForecastVintageClampIsStable(unittest.TestCase):
    """The forecast hydro basis never falls off the EIA-923 vintage cliff.

    Open-frontier item 6 feared the accredited hydro fleet "silently drops"
    past the last EIA-923 final vintage — vintages after
    :data:`~market_sim.data.eia923.EIA923_LATEST_FINAL_VINTAGE` are monthly
    EARLY releases carrying only the large reporters, so an unclamped forecast
    year would accredit a partial census and the adequacy ledger would shrink
    for a purely bookkeeping reason. :func:`modelled_hydro_nameplate_mw` clamps
    the census year, which is what makes the basis stable; this is the
    regression guard for that clamp (capx D-2, 2026-08-24).

    Hermetic and year-SENSITIVE by construction: the patched loader serves the
    FULL plant census only at or before the final vintage and a partial
    (large-reporters-only) census after it, so the assertions below fail if the
    clamp is ever removed rather than passing trivially.
    """

    # Full final-release census vs the partial early-release census that a
    # post-vintage year would see without the clamp.
    _FULL = [(1, "Upstate_West", 700.0, 1e6), (2, "Capital_Hudson", 300.0, 5e5)]
    _PARTIAL = [(1, "Upstate_West", 700.0, 1e6)]

    def _patch_vintage_sensitive(self):
        modelled_hydro_nameplate_mw.cache_clear()

        def _loader(iso, year, **kw):
            rows = self._FULL if year <= EIA923_LATEST_FINAL_VINTAGE else self._PARTIAL
            return _FakeBudget(rows)

        return mock.patch("market_sim.data.hydro.load_hydro_budget", _loader)

    def test_every_forecast_year_sees_the_full_final_release_census(self):
        # 1,000 MW = the full census. Without the clamp the post-vintage years
        # would each report 700 MW — the "silent drop" this guards.
        with self._patch_vintage_sensitive():
            for year in (2026, 2027, 2030, 2040, 2050):
                with self.subTest(year=year):
                    self.assertAlmostEqual(
                        modelled_hydro_nameplate_mw("NYISO", year), 1_000.0
                    )

    def test_year_none_matches_the_clamped_forecast_basis(self):
        # The callers that thread no solve year must resolve the same basis as
        # the ones that do, or the ledger and the backstop could disagree.
        with self._patch_vintage_sensitive():
            self.assertAlmostEqual(
                modelled_hydro_nameplate_mw("NYISO", None),
                modelled_hydro_nameplate_mw("NYISO", 2026),
            )

    def test_a_pre_vintage_hindcast_year_is_not_clamped_forward(self):
        # The clamp is a ceiling, not a pin: a backcast year at or below the
        # final vintage still resolves its OWN census.
        with self._patch_vintage_sensitive():
            self.assertAlmostEqual(
                modelled_hydro_nameplate_mw("NYISO", EIA923_LATEST_FINAL_VINTAGE),
                1_000.0,
            )


class TestAccreditedLedgerFuelComposition(unittest.TestCase):
    """FR-26: assert exactly which resources the accredited ledger counts."""

    def test_hydro_is_present_in_the_ledger(self):
        rows = [(1, "NP15", 1_000.0, 1e6)]
        with _patch_budget(rows):
            firm = accredited_firm_capacity_mw([], iso="CAISO", year=2026)
        # thermal 0 + wind 0 + solar 0 + storage 0 + CAISO firm imports
        # (ADEQUACY_EXTERNAL_TIE_FIRM_MW) + hydro at its published credit.
        self.assertAlmostEqual(firm - 3_371.0, 1_000.0 * 0.7041, places=6)

    def test_every_class_contributes_on_its_own_basis(self):
        rows = [(1, "NP15", 1_000.0, 1e6)]
        fleet = [_thermal(mw=2_000.0)]
        with _patch_budget(rows):
            firm = accredited_firm_capacity_mw(
                fleet,
                wind_pool_mw=1_000.0,
                solar_pool_mw=1_000.0,
                storage_firm_mw=300.0,
                iso="CAISO",
                year=2026,
            )
        expected = (
            2_000.0 * (1.0 - EFORD["gas_cc"])  # thermal UCAP
            + 1_000.0 * RENEWABLE_CAPACITY_CREDIT["wind"]
            + 1_000.0 * RENEWABLE_CAPACITY_CREDIT["solar"]
            + 300.0  # storage, passed in pre-accredited
            + 3_371.0  # CAISO firm RA imports (FF-2B)
            + 1_000.0 * 0.7041  # hydro (FFR-1C)
        )
        self.assertAlmostEqual(firm, expected, places=6)

    def test_hydro_is_never_double_counted_against_the_fleet(self):
        # The persistent fleet structurally carries no hydro, but if it ever
        # did, the pool credits only the capability the fleet loop did not.
        rows = [(1, "NP15", 1_000.0, 1e6)]
        hydro_unit = Generator(
            unit_id="h1",
            name="h1",
            zone="NP15",
            fuel_type="hydro",
            pmax_mw=400.0,
            vom=0.0,
            eford=0.0,
        )
        with _patch_budget(rows):
            firm = accredited_firm_capacity_mw([hydro_unit], iso="CAISO", year=2026)
        # 400 MW accredited by the existing fleet loop at the generic hydro
        # credit; only the remaining 600 MW earns the published pool credit.
        expected = 3_371.0 + 400.0 * RENEWABLE_CAPACITY_CREDIT["hydro"] + 600.0 * 0.7041
        self.assertAlmostEqual(firm, expected, places=6)

    def test_legacy_generic_basis_is_byte_identical(self):
        # iso=None must reproduce the pre-FFR-1C ledger exactly: no hydro pool
        # is resolvable without an ISO, and no firm-import credit applies.
        fleet = [_thermal(mw=2_000.0)]
        modelled_hydro_nameplate_mw.cache_clear()
        self.assertAlmostEqual(
            accredited_firm_capacity_mw(fleet),
            2_000.0 * (1.0 - EFORD["gas_cc"]),
            places=6,
        )


class TestFF2BGapMagnitudes(unittest.TestCase):
    """The FF-2B measured gaps now land in the ledger at published credits."""

    def test_ff2b_measured_nameplate_enters_at_the_published_credit(self):
        expected_firm = {
            # CAISO: CPUC CY2025 non-dispatchable-hydro NQC technology factor.
            "CAISO": 3_601.0 * 0.7041,
            # NYISO: 2025-26 Final CAF, Limited Control Run of River (RoS).
            "NYISO": 3_343.0 * 0.3844,
            # NEISO (capx-S4): the ISO-NE per-resource SCC aggregate factor.
            "NEISO": 30.0 * (1_396.472 / 1_899.5),
        }
        zone = {"CAISO": "NP15", "NYISO": "Upstate_West", "NEISO": "North"}
        for iso, nameplate in FF2B_HYDRO_NAMEPLATE_MW.items():
            with self.subTest(iso=iso):
                rows = [(1, zone[iso], nameplate, 1e6)]
                with _patch_budget(rows):
                    with_hydro = accredited_firm_capacity_mw(
                        iso=iso, fleet=[], year=2026
                    )
                    modelled_hydro_nameplate_mw.cache_clear()
                with _patch_budget([]):
                    without_hydro = accredited_firm_capacity_mw(
                        iso=iso, fleet=[], year=2026
                    )
                modelled_hydro_nameplate_mw.cache_clear()
                # `without_hydro` IS the pre-FFR-1C ledger for this ISO: an
                # empty hydro fleet reproduces the old firm_clean_mw = 0 state.
                self.assertAlmostEqual(
                    with_hydro - without_hydro, expected_firm[iso], places=6
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
