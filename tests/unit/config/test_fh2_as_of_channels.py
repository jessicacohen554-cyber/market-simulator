"""FH-2 — as-of addressability of the demand-growth, capacity-price and policy channels.

Contract suite for ``docs/handoffs/fh-2-as-of-driver-plumbing-2026-08.md``
(hindcast-forward plan §4 rows 6/13/14). Four groups, trivial-first:

1. **Demand-growth vintage** (:data:`constants.DEMAND_GROWTH_RATES_VINTAGES` +
   ``ScenarioConfig.demand_growth_vintage``): the default resolves today's
   table byte-identically; an unknown vintage — or a vintage with no row for
   the run's ISO — RAISES rather than silently falling back to the current
   (2025/2026-edition) rates. The registry ships EMPTY at FH-2, so the
   "known vintage" behaviour is exercised against an injected table.
2. **``runner._scale_demand`` backward span**: previously an empty
   ``range(weather_year, year)`` that silently applied factor 1.0. Now
   de-grows as the exact inverse of the forward compounding, and hard-errors
   in the T1-FF full-forward lane.
3. **Capacity-price ``year`` threading**: all three screens (thermal
   retirement, thermal entry, storage entry) must reach the shared pricing
   seam WITH the model year, so ``resolve_demand_curve_vintage`` selects the
   historic delivery-year vintage. Verified on the committed PJM
   2021/22-2025/26 anchors.
4. **Policy as-of rows**: the RGGI 2021 membership row (Virginia enrolled) and
   the CAISO statutory historic RPS knots; plus the guard that every knot at or
   after 2026 is unchanged, so plain forecasts stay byte-identical.
"""

import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

from market_sim.config import constants
from market_sim.config.constants import (
    DEMAND_GROWTH_RATES,
    DEMAND_GROWTH_RATES_VINTAGES,
    MARKET_DESIGN,
    RGGI_MEMBER_STATES_BY_YEAR,
    resolve_demand_curve_vintage,
)
from market_sim.config.scenario_resolvers import (
    resolve_demand_growth_rate,
    resolve_demand_growth_table,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.capacity import (
    apply_economic_new_entry,
    capacity_revenue_per_mw_yr,
    thermal_accreditation_fraction,
)
from market_sim.model.storage import estimate_capacity_value
from market_sim.policy.rps import get_rps_target
from market_sim.runner import _scale_demand

# A synthetic as-of vintage: deliberately UNLIKE today's table (ERCOT mid near
# 8.5 %/yr) so a leak to the current rates is visible as a value, not just a
# key. Two ISOs only — the missing-ISO refusal is part of the contract.
_VINTAGE_2021 = {
    2021: {
        "ERCOT": {
            "low": {"near": 0.010, "long": 0.005},
            "mid": {"near": 0.020, "long": 0.010},
            "high": {"near": 0.030, "long": 0.020},
        },
        "PJM": {
            "low": {"near": 0.000, "long": 0.000},
            "mid": {"near": 0.005, "long": 0.005},
            "high": {"near": 0.010, "long": 0.010},
        },
    }
}


def _with_vintages(table):
    """Patch the vintage registry everywhere the resolver can read it."""
    return mock.patch.object(constants, "DEMAND_GROWTH_RATES_VINTAGES", table)


class TestDemandGrowthVintageMechanism(unittest.TestCase):
    """Plan §4 row 6 — the second BLOCKER's mechanism (values are FH-3's)."""

    def test_registry_populated_by_fh3(self):
        # Was test_registry_ships_empty_at_fh2, per its own instruction: "if
        # this ever fails, the values landed". FH-3 landed them 2026-08-02
        # (docs/handoffs/fh-3-asknown-driver-vintages-2026-08.md). The
        # fail-closed contract below is unchanged and still enforced.
        self.assertEqual(sorted(DEMAND_GROWTH_RATES_VINTAGES), [2021, 2023])
        for as_of, table in DEMAND_GROWTH_RATES_VINTAGES.items():
            for iso, cases in table.items():
                # Inner shape must match DEMAND_GROWTH_RATES exactly, so one
                # resolver serves both (rule 19 [R-ONE-MECH]).
                self.assertIn("mid", cases, f"{as_of}/{iso} must carry a central case")
                for case, eras in cases.items():
                    self.assertIn(case, ("low", "mid", "high"), f"{as_of}/{iso}")
                    self.assertEqual(
                        sorted(eras), ["long", "near"], f"{as_of}/{iso}/{case}"
                    )

    def test_no_vintage_cell_inherits_the_current_table(self):
        # The values must actually be as-of, not copies: every landed near rate
        # differs from the live 2025/26-vintage rate for that ISO. ERCOT is the
        # headline (8.5 %/yr live vs 2.0 % as-of-2021).
        for as_of, table in DEMAND_GROWTH_RATES_VINTAGES.items():
            for iso, cases in table.items():
                live = DEMAND_GROWTH_RATES[iso]["mid"]["near"]
                self.assertNotAlmostEqual(
                    cases["mid"]["near"],
                    live,
                    msg=f"{as_of}/{iso} matches the live table",
                )

    def test_default_none_resolves_current_table(self):
        config = ScenarioConfig(iso="ERCOT")
        self.assertIsNone(config.demand_growth_vintage)
        self.assertIs(resolve_demand_growth_table(config), DEMAND_GROWTH_RATES)

    def test_default_rate_unchanged_by_the_seam(self):
        # The as-of seam must not perturb the current lane: the resolved rate
        # equals the raw table lookup for every era, path and ISO.
        for iso, rates in DEMAND_GROWTH_RATES.items():
            for path in ("low", "mid", "high"):
                config = ScenarioConfig(iso=iso, demand_growth_path=path)
                self.assertAlmostEqual(
                    resolve_demand_growth_rate(config, 2028), rates[path]["near"]
                )
                self.assertAlmostEqual(
                    resolve_demand_growth_rate(config, 2035), rates[path]["long"]
                )

    def test_unknown_vintage_raises_at_config_build(self):
        # Fail-closed at build time (the FH-1 pre-solve-guard precedent), not
        # at the first _scale_demand call hours into a run. 2019 is the probe
        # year: it was 2021 until FH-3 landed that vintage for real.
        with self.assertRaises(ValueError) as ctx:
            ScenarioConfig(iso="ERCOT", demand_growth_vintage=2019)
        self.assertIn("DEMAND_GROWTH_RATES_VINTAGES", str(ctx.exception))

    def test_landed_vintage_builds_and_resolves(self):
        # The converse of the guard above: a vintage FH-3 actually landed must
        # build cleanly and return that edition's rate, not the live table's.
        config = ScenarioConfig(iso="ERCOT", demand_growth_vintage=2021)
        self.assertAlmostEqual(resolve_demand_growth_rate(config, 2023), 0.0200)
        # The point of the assertion is that the VINTAGE table and the LIVE
        # table are distinct, not the live table's level (SCN-LOAD re-derived it
        # from the 2025 LTLF on 2026-09-06; the 2021 vintage is frozen).
        self.assertNotAlmostEqual(
            DEMAND_GROWTH_RATES["ERCOT"]["mid"]["near"],
            resolve_demand_growth_rate(config, 2023),
        )

    def test_missing_case_in_a_landed_vintage_raises(self):
        # FH-3: the missing-ISO refusal, one level down. Most vintage cells
        # carry `mid` alone because the edition published no low/high SERIES
        # (inventing a band would breach rule 5). Before this guard a low/high
        # request on such a cell fell through to the scalar
        # config.demand_growth_rate (1 %/yr) — a silent answer no edition ever
        # published, i.e. exactly the leak this seam exists to close.
        for path in ("low", "high"):
            config = ScenarioConfig(
                iso="PJM", demand_growth_vintage=2021, demand_growth_path=path
            )
            with self.assertRaises(ValueError) as ctx:
                resolve_demand_growth_rate(config, 2023)
            self.assertIn(path, str(ctx.exception))
            self.assertIn("PJM", str(ctx.exception))

    def test_published_band_still_interpolates(self):
        # ...and where the edition DID publish a full low/base/high series
        # (NYISO Gold Book Table I-1a), all three cases resolve normally.
        rates = {
            p: resolve_demand_growth_rate(
                ScenarioConfig(
                    iso="NYISO", demand_growth_vintage=2021, demand_growth_path=p
                ),
                2023,
            )
            for p in ("low", "mid", "high")
        }
        self.assertLess(rates["low"], rates["mid"])
        self.assertLess(rates["mid"], rates["high"])
        # The 2021 Gold Book forecast NY energy DECLINING to 2030 on efficiency
        # and codes — a negative central near rate is real, not a sign error.
        self.assertLess(rates["mid"], 0.0)

    def test_unknown_vintage_raises_at_the_resolver(self):
        # Defence in depth: even a config that got past __post_init__ (e.g. one
        # mutated after build) cannot silently draw today's rates.
        config = ScenarioConfig(iso="ERCOT")
        object.__setattr__(config, "demand_growth_vintage", 1999)
        with self.assertRaises(ValueError):
            resolve_demand_growth_table(config)
        with self.assertRaises(ValueError):
            resolve_demand_growth_rate(config, 2023)

    def test_vintage_never_falls_back_to_the_current_table(self):
        # The whole point: an unknown vintage must NOT return DEMAND_GROWTH_RATES.
        config = ScenarioConfig(iso="ERCOT")
        object.__setattr__(config, "demand_growth_vintage", 2019)
        with self.assertRaises(ValueError):
            resolve_demand_growth_table(config)

    def test_known_vintage_resolves_its_own_rates(self):
        with _with_vintages(_VINTAGE_2021):
            config = ScenarioConfig(iso="ERCOT", demand_growth_vintage=2021)
            self.assertEqual(resolve_demand_growth_table(config), _VINTAGE_2021[2021])
            # Near era (<= DEMAND_GROWTH_TRANSITION_YEAR) and long era both come
            # from the vintage, NOT from today's 8.5 %/2.5 % ERCOT rates.
            self.assertAlmostEqual(resolve_demand_growth_rate(config, 2023), 0.020)
            self.assertAlmostEqual(resolve_demand_growth_rate(config, 2035), 0.010)
            self.assertNotAlmostEqual(
                resolve_demand_growth_rate(config, 2023),
                DEMAND_GROWTH_RATES["ERCOT"]["mid"]["near"],
            )

    def test_known_vintage_honours_path_and_percentile(self):
        # The PB-1 levers keep working on a vintage table — one mechanism, two
        # addresses (rule 19), not a second growth path.
        with _with_vintages(_VINTAGE_2021):
            low = ScenarioConfig(
                iso="ERCOT", demand_growth_vintage=2021, demand_growth_path="low"
            )
            high = ScenarioConfig(
                iso="ERCOT", demand_growth_vintage=2021, demand_growth_path="high"
            )
            p75 = ScenarioConfig(
                iso="ERCOT",
                demand_growth_vintage=2021,
                demand_growth_percentile=0.75,
            )
            self.assertAlmostEqual(resolve_demand_growth_rate(low, 2023), 0.010)
            self.assertAlmostEqual(resolve_demand_growth_rate(high, 2023), 0.030)
            # 0.75 = halfway between mid (0.020) and high (0.030).
            self.assertAlmostEqual(resolve_demand_growth_rate(p75, 2023), 0.025)

    def test_vintage_missing_the_iso_raises(self):
        # Borrowing today's rate for an ISO the vintage does not carry is the
        # same leak as an unknown vintage — refused, not filled in.
        with _with_vintages(_VINTAGE_2021):
            config = ScenarioConfig(iso="CAISO", demand_growth_vintage=2021)
            with self.assertRaises(ValueError) as ctx:
                resolve_demand_growth_rate(config, 2023)
            self.assertIn("CAISO", str(ctx.exception))

    def test_backcast_refuses_a_vintage(self):
        with _with_vintages(_VINTAGE_2021):
            with self.assertRaises(ValueError) as ctx:
                ScenarioConfig(iso="ERCOT", mode="backcast", demand_growth_vintage=2021)
            self.assertIn("backcast", str(ctx.exception))

    def test_cache_key_neutral_at_default_and_distinct_when_set(self):
        # Rule 24 registration: the field is dropped from the hash at its None
        # default (every pre-FH-2 cached run keeps its key) and enters the key
        # when set (a vintage-addressed run is a distinct scenario).
        # The GLOBAL default forecast key. ADVANCED e5ecd4105ada3e58 ->
        # 547053bdfccd4264 on 2026-09-06 by capx D65-B (owner ruling Q47): the
        # COUPLED arming of ccs_retrofit_fixed_cost_co2_scaling (Act A, a declared
        # (b'-1) default flip) with ccs_retrofit_vom_adder 8.0 -> 2.95 $/MWh 2026$
        # (Act B, re-identified off the widened ATB extract). Act B is NOT a
        # _CACHE_KEY_OPTIONAL_FIELDS member, so it has no drop value and re-keys
        # unconditionally. Pre-declared BEFORE the solve in
        # docs/handoffs/PRECOMMIT-capx-d65b-2026-09-06.md §3; cache-epoch ledger
        # entry 2026-09-06c in src/market_sim/results/cache.py. Nothing about THIS
        # field moved — the pin advances because the global default did.
        self.assertEqual(ScenarioConfig().cache_key(), "547053bdfccd4264")
        with _with_vintages(_VINTAGE_2021):
            base = ScenarioConfig(iso="ERCOT")
            vintaged = ScenarioConfig(iso="ERCOT", demand_growth_vintage=2021)
            self.assertNotEqual(base.cache_key(), vintaged.cache_key())

    def test_every_landed_vintage_covers_every_registered_iso(self):
        # FH-3 landed 11 of 12 cells; (2021, CAISO) was the MANUAL DOWNLOAD it
        # refused to guess, and the refusal is what blocked FH-5's CAISO Arm K.
        # The CEDU 2020 intake closes it, so BOTH vintages are now complete
        # across the registry. A new ISO added to MARKET_DESIGN without its
        # vintage rows fails here rather than at a solve.
        for as_of in DEMAND_GROWTH_RATES_VINTAGES:
            for iso in MARKET_DESIGN:
                config = ScenarioConfig(iso=iso, demand_growth_vintage=as_of)
                rate = resolve_demand_growth_rate(config, 2023)
                self.assertIsInstance(rate, float, f"{as_of}/{iso}")

    def test_caiso_2021_is_the_cedu_2020_edition(self):
        # CEC "California Energy Demand Forecast Update, 2020-2030" (CEDU 2020),
        # STATE Form 1.2 Total_Energy_For_Load, adopted 2021-01-26 — the latest
        # CEC edition published at or before the 2021 base year. Values pinned so
        # a later re-derivation has to cite a source-data change (rule 23).
        cell = DEMAND_GROWTH_RATES_VINTAGES[2021]["CAISO"]
        self.assertEqual(
            cell,
            {
                "low": {"near": 0.0009, "long": 0.0009},
                "mid": {"near": 0.0091, "long": 0.0091},
                "high": {"near": 0.0158, "long": 0.0158},
            },
        )
        # The edition's horizon ends 2030 => long is EDGE-HELD to near, the same
        # construction ERCOT and NEISO carry in this vintage.
        for case, eras in cell.items():
            self.assertAlmostEqual(eras["long"], eras["near"], msg=case)
        # CEDU 2020 publishes three STATE workbooks whose Form 2.2 economic and
        # demographic drivers differ, so the band is edition-published, not
        # invented (rule 5) — and it orders low < mid < high.
        rates = {
            p: resolve_demand_growth_rate(
                ScenarioConfig(
                    iso="CAISO", demand_growth_vintage=2021, demand_growth_path=p
                ),
                2023,
            )
            for p in ("low", "mid", "high")
        }
        self.assertLess(rates["low"], rates["mid"])
        self.assertLess(rates["mid"], rates["high"])
        # ...and it is genuinely as-of: well under the live 2.8 %/yr CAISO rate,
        # which encodes a data-center boom no 2021 edition had seen.
        self.assertLess(rates["high"], DEMAND_GROWTH_RATES["CAISO"]["mid"]["near"])

    def test_fh3_cells_are_undisturbed_by_the_caiso_intake(self):
        # The CEDU 2020 row is PURELY ADDITIVE: every cell FH-3 landed still
        # resolves to its own edition's rate. Guards a neighbouring-row slip in
        # the same dict literal.
        for iso, near in (
            ("ERCOT", 0.0200),
            ("PJM", 0.0034),
            ("NYISO", -0.0038),
            ("NEISO", 0.0107),
            ("MISO", 0.0117),
        ):
            config = ScenarioConfig(iso=iso, demand_growth_vintage=2021)
            self.assertAlmostEqual(
                resolve_demand_growth_rate(config, 2023), near, msg=iso
            )

    def test_a_vintage_with_no_row_still_fails_closed_for_every_iso(self):
        # Landing (2021, CAISO) must NOT soften the seam. 2020 and 2022 are
        # genuinely unregistered vintages: they raise for CAISO exactly as for
        # every other ISO, and the message names the registry rather than
        # quietly handing back the current (2025/26-edition) table.
        for as_of in (2020, 2022):
            self.assertNotIn(as_of, DEMAND_GROWTH_RATES_VINTAGES)
            for iso in MARKET_DESIGN:
                with self.assertRaises(ValueError, msg=f"{as_of}/{iso}") as ctx:
                    ScenarioConfig(iso=iso, demand_growth_vintage=as_of)
                self.assertIn("DEMAND_GROWTH_RATES_VINTAGES", str(ctx.exception))


class TestScaleDemandBothDirections(unittest.TestCase):
    """Plan §4 row 6 compounding defect — the silent backward 1.0."""

    @staticmethod
    def _base():
        return np.ones((2, 24))

    def test_forward_span_unchanged(self):
        config = ScenarioConfig(iso="ERCOT", weather_year=2024)
        expected = 1.0
        for y in (2024, 2025, 2026):
            expected *= 1.0 + resolve_demand_growth_rate(config, y)
        got = _scale_demand(self._base(), config, 2027)
        self.assertAlmostEqual(float(got[0, 0]), expected)

    def test_same_year_is_unity(self):
        config = ScenarioConfig(iso="ERCOT", weather_year=2024)
        got = _scale_demand(self._base(), config, 2024)
        self.assertAlmostEqual(float(got[0, 0]), 1.0)

    def test_backward_span_de_grows_instead_of_silently_holding(self):
        config = ScenarioConfig(iso="ERCOT", weather_year=2027)
        got = float(_scale_demand(self._base(), config, 2024)[0, 0])
        self.assertLess(got, 1.0)  # the old behaviour returned exactly 1.0
        expected = 1.0
        for y in (2024, 2025, 2026):
            expected *= 1.0 + resolve_demand_growth_rate(config, y)
        self.assertAlmostEqual(got, 1.0 / expected)

    def test_directions_compose_to_identity(self):
        forward = ScenarioConfig(iso="ERCOT", weather_year=2024)
        backward = ScenarioConfig(iso="ERCOT", weather_year=2027)
        grown = _scale_demand(self._base(), forward, 2027)
        round_trip = _scale_demand(grown, backward, 2024)
        np.testing.assert_allclose(round_trip, self._base())

    def test_full_forward_hindcast_hard_errors_on_a_backward_span(self):
        # Both shipped T1-FF arms pin the weather base at/below every solve
        # year; a backward span there is a posture misconfiguration, and
        # de-growing a later measured weather year into an "as-of" forecast
        # would import post-base information (rule 13).
        config = ScenarioConfig(
            iso="ERCOT",
            hindcast=True,
            start_year=2023,
            end_year=2025,
            crossover_forward_year=2023,
            weather_year=2025,
        )
        self.assertTrue(config.is_full_forward_hindcast)
        with self.assertRaises(ValueError) as ctx:
            _scale_demand(self._base(), config, 2023)
        self.assertIn("full-forward hindcast", str(ctx.exception))
        # ... and the forward span in the same run is untouched.
        np.testing.assert_allclose(
            _scale_demand(self._base(), config, 2025), self._base()
        )


class TestCapacityPriceYearThreading(unittest.TestCase):
    """Plan §4 row 13 — ``year`` must reach all three screens' pricing seam.

    Gate-on configs only: the CR-1 clearing gate stays owner-armed (no default
    is flipped here), so these assert the mechanism, not a shipped posture.
    """

    ON = SimpleNamespace(capacity_market_clearing=True)

    # The committed PJM vintages (MARKET_DESIGN_VINTAGES["PJM"]) — published
    # UCAP net-CONE $/MW-day x 365 / 1000. Recomputed here from the published
    # $/MW-day figures so the assertion is against the SOURCE arithmetic, not
    # against the constant it is checking.
    PJM_ANCHORS = {
        2021: ("2021/2022", 321.57 * 365.0 / 1000.0),
        2022: ("2022/2023", 260.5 * 365.0 / 1000.0),
        2023: ("2023/2024", 274.96 * 365.0 / 1000.0),
        2024: ("2024/2025", 293.19 * 365.0 / 1000.0),
        2025: ("2025/2026", 228.81 * 365.0 / 1000.0),
    }

    def test_pjm_historic_delivery_year_anchors(self):
        for year, (label, anchor) in self.PJM_ANCHORS.items():
            vintage = resolve_demand_curve_vintage("PJM", year)
            self.assertEqual(vintage.delivery_year, label, msg=f"year {year}")
            self.assertAlmostEqual(
                vintage.net_cone_curve_per_kw_yr, anchor, places=6, msg=f"year {year}"
            )

    def test_thermal_retirement_screen_prices_on_the_year_vintage(self):
        frac = thermal_accreditation_fraction("gas_cc", 0.05, "PJM")
        design = MARKET_DESIGN["PJM"]
        seen = set()
        for year in self.PJM_ANCHORS:
            got = capacity_revenue_per_mw_yr("PJM", "gas_cc", 0.05, self.ON, 1.0, year)
            self.assertAlmostEqual(
                got,
                design.capacity_price_per_firm_mw_yr(self.ON, 1.0, iso="PJM", year=year)
                * frac,
            )
            seen.add(round(got, 3))
        # Five distinct delivery years => five distinct prices: the year is
        # genuinely selecting a vintage, not being swallowed.
        self.assertEqual(len(seen), len(self.PJM_ANCHORS))

    def test_thermal_entry_screen_prices_on_the_year_vintage(self):
        # The entry screen reaches the seam through apply_economic_new_entry's
        # own ``year`` argument; the diagnostic ledger exposes what it paid.
        design = MARKET_DESIGN["PJM"]

        def _payment(year):
            config = ScenarioConfig(
                iso="PJM",
                entry_screen_diagnostics=True,
                capacity_market_clearing=True,
                h2_available_year=2099,
                ccs_available_year=2099,
                egs_available_year=2099,
                offshore_wind_available_year=2099,
            )
            ledger: list[dict] = []
            apply_economic_new_entry(
                [],
                np.full(8760, 30.0),
                year,
                config,
                "PJM",
                screen_ledger=ledger,
                reserve_position=1.0,
            )
            row = next(r for r in ledger if r["tech"] == "gas_cc")
            expected = design.capacity_price_per_firm_mw_yr(
                config, 1.0, iso="PJM", year=year
            )
            return row["capacity_revenue_per_mw_yr"], expected

        payments = {}
        for year in (2021, 2025, 2026):
            got, expected = _payment(year)
            self.assertGreater(got, 0.0)
            # The screen pays price x accreditation on the SAME seam (rule 19).
            self.assertAlmostEqual(
                got,
                expected * thermal_accreditation_fraction("gas_cc", 0.05, "PJM"),
                places=3,
            )
            payments[year] = round(got, 3)
        self.assertEqual(len(set(payments.values())), 3)

    def test_storage_entry_screen_prices_on_the_year_vintage(self):
        config = ScenarioConfig(
            iso="PJM", storage_capacity_value=True, capacity_market_clearing=True
        )
        values = {
            year: round(
                estimate_capacity_value(
                    "li_ion_4hr", 0.0, config, "PJM", reserve_position=1.0, year=year
                ),
                3,
            )
            for year in self.PJM_ANCHORS
        }
        self.assertEqual(len(set(values.values())), len(self.PJM_ANCHORS))

    def test_gate_off_is_year_invariant(self):
        # No default flip: with the clearing gate off every year prices the
        # flat registry anchor, exactly as before.
        off = SimpleNamespace(capacity_market_clearing=False)
        base = capacity_revenue_per_mw_yr("PJM", "gas_cc", 0.05)
        for year in (None, 2021, 2025, 2026, 2030):
            self.assertEqual(
                capacity_revenue_per_mw_yr("PJM", "gas_cc", 0.05, off, 1.0, year),
                base,
            )

    def test_ercot_energy_only_is_zero_at_every_year(self):
        for year in (None, 2021, 2026):
            self.assertEqual(
                capacity_revenue_per_mw_yr("ERCOT", "gas_cc", 0.05, self.ON, 1.0, year),
                0.0,
            )


class TestPolicyAsOfRows(unittest.TestCase):
    """Plan §4 row 14 — the smallest-first policy as-of rows."""

    def test_rggi_2021_membership_includes_virginia(self):
        self.assertIn(2021, RGGI_MEMBER_STATES_BY_YEAR)
        self.assertIn("VA", RGGI_MEMBER_STATES_BY_YEAR[2021])
        self.assertIn("VA", RGGI_MEMBER_STATES_BY_YEAR[2023])
        self.assertNotIn("VA", RGGI_MEMBER_STATES_BY_YEAR[2024])
        self.assertNotIn("VA", RGGI_MEMBER_STATES_BY_YEAR[2025])
        # Pennsylvania was never an actual member (entry enjoined).
        for states in RGGI_MEMBER_STATES_BY_YEAR.values():
            self.assertNotIn("PA", states)

    def test_2022_row_enrolls_virginia(self):
        # [R-HOLDOUT] was removed 2026-09-09 and PJM solves 2022 (pjm-h22), so
        # the quarantine that kept 2022 absent is spent: VA was a 2022 member.
        self.assertIn("VA", RGGI_MEMBER_STATES_BY_YEAR[2022])

    def test_per_generator_membership_uses_the_2021_set(self):
        # Before the 2021 row existed this fell back to max(year) = the 2025,
        # post-exit set, un-enrolling a Virginia plant in the year it joined.
        from market_sim.policy.cap_and_trade import per_generator_membership

        fleet = SimpleNamespace(
            zone_idx=np.array([0, 0]), plant_code=np.array([101, 102])
        )
        states = {101: "VA", 102: "OH"}
        for year, va_expected in ((2021, 1.0), (2023, 1.0), (2025, 0.0)):
            got = per_generator_membership(
                "PJM", year, np.array([0.5]), fleet, plant_state=states
            )
            self.assertAlmostEqual(got[0], va_expected, msg=f"VA in {year}")
            self.assertAlmostEqual(got[1], 0.0, msg=f"OH in {year}")

    def test_caiso_historic_rps_knots_are_statutory(self):
        # SB X1-2 (2011) 33 % by 2020 -> the standing CP4 requirement in 2021;
        # SB 100 (2018) 44 % by 2024. Both Pub. Util. Code 399.15(b)(2)(B).
        self.assertAlmostEqual(get_rps_target("CAISO", 2021), 0.33)
        self.assertAlmostEqual(get_rps_target("CAISO", 2024), 0.44)
        # The edge-hold below the first knot now holds the 2021 statute, not
        # the 2026 target it used to hand every historic year.
        self.assertAlmostEqual(get_rps_target("CAISO", 2019), 0.33)

    def test_forecast_era_rps_targets_pinned(self):
        # Pinned forecast-era knots. DELIBERATELY UPDATED by FFR-7B Arm 1
        # (rule 14 [R-ACCURATE]; FFR-6B §8): the renewable row now carries
        # each statute's RENEWABLE tier only — NEISO's 2026 knot is the
        # per-state Class-I blend (0.29, was the CES-blend 0.30) and CAISO
        # plateaus at the statutory 60% RPS (§399.15(b)(2)(C)) instead of
        # ramping to SB 100's zero-carbon 1.00. Clean/zero-emission tiers
        # left the row (they are a separate row family, FFR-6B §6.3).
        expected_2026 = {
            "ERCOT": 0.0,
            "CAISO": 0.50,
            "NYISO": 0.40,
            "NEISO": 0.29,
            "PJM": 0.185,
            "MISO": 0.11,
        }
        for iso, target in expected_2026.items():
            self.assertAlmostEqual(get_rps_target(iso, 2026), target, msg=iso)
        self.assertAlmostEqual(get_rps_target("CAISO", 2030), 0.60)
        self.assertAlmostEqual(get_rps_target("CAISO", 2045), 0.60)

    def test_other_isos_still_edge_hold_and_that_is_disclosed(self):
        # Documented FH-2 disclose row: the five blend-based ISOs carry no
        # historic knot, so a forward-lane historic year still receives the
        # 2026 blend. Pinned so the day one lands, this test is updated
        # deliberately rather than the disclose list silently going stale.
        for iso in ("NYISO", "NEISO", "PJM", "MISO"):
            self.assertAlmostEqual(
                get_rps_target(iso, 2021), get_rps_target(iso, 2026), msg=iso
            )


if __name__ == "__main__":
    unittest.main()
