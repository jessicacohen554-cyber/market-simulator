"""Source-consistency: cost constants vs the cross-source benchmark derivation.

Asserts the constants the capacity-cost-grounding session (2026-07-19)
derivation-locked equal what ``scripts/data/derive_cost_benchmark_envelope.py``
computes from the committed NREL ATB 2024 extract plus
``data/raw/new-build-cost-benchmarks/benchmarks_2026.csv`` (CLAUDE.md rule 23 —
deterministic, tested functions of real data sources, never hand-set numbers).
Reads only committed raw files, so it runs in CI with no clean-build step.

Covers: the literature-envelope ``TECH_COST_MULTIPLIERS`` capex ratios (the
PB-1 lever's low/high bounds), the ATB-derived li-ion ``STORAGE_TECHS`` costs,
``OFFSHORE_WIND_PARAMS``, the AEO2026-premium hydrogen-turbine costs, the
ATB-derived EGS FOM, benchmark-table hygiene, and the requirement that every
operative mid lies inside its own literature envelope.
"""

import unittest

from market_sim.config.constants import (
    GEOTHERMAL_PARAMS,
    HYDROGEN_TURBINE_PARAMS,
    NEW_ENTRY_COSTS,
    OFFSHORE_WIND_PARAMS,
    STORAGE_TECHS,
    TECH_COST_MULTIPLIERS,
)
from scripts.data import derive_cost_benchmark_envelope as env


class TestBenchmarkTableHygiene(unittest.TestCase):
    def test_rows_load_and_carry_provenance(self) -> None:
        rows = env.load_benchmarks()
        self.assertGreater(len(rows), 30)
        for row in rows:
            self.assertTrue(row["url"], row["source_id"])
            self.assertTrue(row["source_ref"], row["source_id"])
            self.assertIn(row["dollar_year"], range(2020, 2031), row["source_id"])
            # Every row carries at least one capex figure.
            self.assertTrue(
                any(
                    row[f] is not None
                    for f in (
                        "capex_per_kw_low",
                        "capex_per_kw_mid",
                        "capex_per_kw_high",
                    )
                ),
                row["source_id"],
            )

    def test_unverified_rows_never_enforce_the_envelope(self) -> None:
        # verified=0 rows (primaries unreachable from this environment) are
        # documentation: envelope_points_2026 must ignore them even when
        # in_envelope=1 (DOE Liftoff EGS), so the enforced range rests only on
        # documents QA'd against their committed markdown conversions.
        rows = env.load_benchmarks()
        unverified = {r["source_id"] for r in rows if not r["verified"]}
        self.assertTrue(unverified)  # the flag is in use
        for tech in ("geothermal_egs", "storage_iron_air"):
            ids = {sid for sid, _ in env.envelope_points_2026(rows, tech)}
            self.assertFalse(ids & unverified, ids)

    def test_h2_premium_literals_match_benchmark_rows(self) -> None:
        # The derive module's AEO2026 ratio literals must equal the cited
        # benchmark rows so the two records cannot drift apart.
        by_id = {r["source_id"]: r for r in env.load_benchmarks()}
        self.assertEqual(
            by_id["aeo2026_h2_ct"]["capex_per_kw_mid"], env._AEO2026_H2_CT_CAPEX
        )
        self.assertEqual(
            by_id["aeo2026_gas_ct"]["capex_per_kw_mid"], env._AEO2026_FRAME_CT_CAPEX
        )
        self.assertEqual(
            by_id["aeo2026_h2_ct"]["fom_per_kw_yr_mid"], env._AEO2026_H2_CT_FOM
        )
        self.assertEqual(
            by_id["aeo2026_gas_ct"]["fom_per_kw_yr_mid"], env._AEO2026_FRAME_CT_FOM
        )


class TestEnvelopeMultipliers(unittest.TestCase):
    def test_committed_multipliers_match_envelope_derivation(self) -> None:
        derived = env.derive_envelope_multipliers()
        self.assertEqual(set(derived), set(env._ENVELOPE_TECHS))
        for tech, cases in derived.items():
            for case in ("low", "mid", "high"):
                self.assertEqual(
                    TECH_COST_MULTIPLIERS[tech][case]["capex_per_kw"],
                    cases[case]["capex_per_kw"],
                    f"TECH_COST_MULTIPLIERS[{tech!r}][{case!r}] drifted from the "
                    f"literature-envelope derivation — re-run "
                    f"scripts/data/derive_cost_benchmark_envelope.py",
                )

    def test_envelope_contains_atb_cases_and_mid(self) -> None:
        # low ≤ ATB Advanced ratio, high ≥ ATB Conservative ratio, and the
        # envelope brackets mid=1.0 — the lever can never be narrower than
        # FF-1E's ATB-internal basis, and mid always lies inside.
        from scripts.data.derive_entry_costs_from_atb import (
            derive_tech_cost_multipliers,
        )

        atb = derive_tech_cost_multipliers()
        for tech in env._ENVELOPE_TECHS:
            low = TECH_COST_MULTIPLIERS[tech]["low"]["capex_per_kw"]
            high = TECH_COST_MULTIPLIERS[tech]["high"]["capex_per_kw"]
            self.assertLessEqual(low, atb[tech]["low"]["capex_per_kw"], tech)
            self.assertGreaterEqual(high, atb[tech]["high"]["capex_per_kw"], tech)
            self.assertLessEqual(low, 1.0, tech)
            self.assertGreaterEqual(high, 1.0, tech)

    def test_every_mid_within_its_literature_envelope(self) -> None:
        for line in env.validation_table():
            self.assertTrue(
                line["mid_within_envelope"],
                f"{line['tech']} operative mid {line['mid_2026usd_per_kw']} is "
                f"outside [{line['envelope_low']}, {line['envelope_high']}]",
            )

    def test_gas_lever_no_longer_degenerate(self) -> None:
        # The regression the envelope basis fixes: FF-1E's ATB-internal gas CT
        # spread was 1.0/1.0 (inert lever) and gas CC ±1%. The published-cost
        # envelope must keep both levers strictly two-sided.
        for tech in ("gas_ct", "gas_cc"):
            self.assertLess(TECH_COST_MULTIPLIERS[tech]["low"]["capex_per_kw"], 0.99)
            self.assertGreater(
                TECH_COST_MULTIPLIERS[tech]["high"]["capex_per_kw"], 1.01
            )


class TestDerivedTechConstants(unittest.TestCase):
    def test_storage_li_ion_matches_atb_derivation(self) -> None:
        derived = env.derive_storage_li_ion()
        for name, vals in derived.items():
            for param, value in vals.items():
                self.assertEqual(
                    STORAGE_TECHS[name][param],
                    value,
                    f"STORAGE_TECHS[{name!r}][{param!r}] drifted from the ATB "
                    f"derivation",
                )

    def test_storage_capex_per_kwh_is_bundled_convention(self) -> None:
        for name in ("li_ion_4hr", "li_ion_8hr", "li_ion_12hr"):
            tech = STORAGE_TECHS[name]
            self.assertAlmostEqual(
                tech["capex_per_kwh"],
                round(tech["capex_per_kw"] / tech["duration_hr"], 1),
                places=1,
                msg=name,
            )

    def test_offshore_wind_matches_atb_derivation(self) -> None:
        derived = env.derive_offshore_wind()
        for key, vals in derived.items():
            for param, value in vals.items():
                self.assertEqual(OFFSHORE_WIND_PARAMS[key][param], value, (key, param))

    def test_hydrogen_matches_aeo_premium_derivation(self) -> None:
        derived = env.derive_hydrogen_turbines()
        for key, vals in derived.items():
            for param, value in vals.items():
                self.assertEqual(
                    HYDROGEN_TURBINE_PARAMS[key][param], value, (key, param)
                )
        # The premium keeps H2 strictly costlier than its unabated gas host.
        self.assertGreater(
            HYDROGEN_TURBINE_PARAMS["h2_ct"]["capex_kw"],
            NEW_ENTRY_COSTS["gas_ct"]["capex_per_kw"],
        )
        self.assertGreater(
            HYDROGEN_TURBINE_PARAMS["h2_ccgt"]["capex_kw"],
            NEW_ENTRY_COSTS["gas_cc"]["capex_per_kw"],
        )

    def test_egs_fom_matches_atb_derivation(self) -> None:
        self.assertEqual(GEOTHERMAL_PARAMS["egs"]["fom_kw_yr"], env.derive_egs_fom())


if __name__ == "__main__":
    unittest.main()
