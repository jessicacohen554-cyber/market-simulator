"""Tests for the FF-2A entry-stack gates in ``market_sim.model.capacity``.

Separate file (not ``test_capacity.py``) deliberately: the FF-2A session's
push channel cannot move rule-27 core files whole, so the new coverage lives
in an additive module. All three gates default OFF; the off-path must stay
byte-identical to the pre-FF-2A screen, and each armed gate must do exactly
its one job.
"""

import unittest

import numpy as np

from market_sim.config.constants import (
    DEFAULT_MARKET_DESIGN,
    MARKET_DESIGN,
    QUEUE_CAP_PER_TECH_GW,
)
from market_sim.config.entry_config import ENTRY_COD_LAG_YEARS
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator
from market_sim.model.capacity import (
    apply_economic_new_entry,
    apply_reserve_margin_build,
    evolve_fleet,
    resolve_renewable_capacity_credit,
)


def _gen(unit_id, fuel_type, pmax=100.0, heat_rate=10.0, zone="Z0", **kwargs):
    """Build a Generator with the attributes the capacity logic reads."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone=zone,
        fuel_type=fuel_type,
        pmax_mw=pmax,
        heat_rate=heat_rate,
        **kwargs,
    )


def _entry_by_tech(new_fleet, renewable_additions):
    """Collapse a new-entry result into ``{fuel: total_mw}``."""
    by_tech: dict[str, float] = {}
    for g in new_fleet:
        by_tech[g.fuel_type] = by_tech.get(g.fuel_type, 0.0) + g.pmax_mw
    for by_fuel in renewable_additions.values():
        for fuel, mw in by_fuel.items():
            by_tech[fuel] = by_tech.get(fuel, 0.0) + mw
    return by_tech


class TestEntryStackFF2A(unittest.TestCase):
    """FF-2A entry-stack gates: VRE capacity revenue, growth ladder, COD lag."""

    @staticmethod
    def _config(iso="PJM", **kw):
        # Emerging techs pushed out so only the classic four are screened.
        return ScenarioConfig(
            iso=iso,
            h2_available_year=2099,
            ccs_available_year=2099,
            egs_available_year=2099,
            offshore_wind_available_year=2099,
            **kw,
        )

    def test_vre_capacity_revenue_zero_when_gate_off(self):
        # BLK-7's measured $0 stays $0 with the gate off — the diagnostic
        # ledger records the zero explicitly.
        config = self._config(entry_screen_diagnostics=True)
        ledger: list[dict] = []
        apply_economic_new_entry(
            [], np.full(8760, 30.0), 2030, config, "PJM", screen_ledger=ledger
        )
        solar = next(r for r in ledger if r["tech"] == "solar")
        self.assertEqual(solar["capacity_revenue_per_mw_yr"], 0.0)

    def test_vre_capacity_revenue_paid_in_capacity_market_iso(self):
        # Gate on in PJM: solar earns price x credit through the SAME
        # resolver the adequacy ledger uses (rule 19).
        config = self._config(
            entry_screen_diagnostics=True, entry_vre_capacity_revenue=True
        )
        ledger: list[dict] = []
        apply_economic_new_entry(
            [],
            np.full(8760, 30.0),
            2030,
            config,
            "PJM",
            screen_ledger=ledger,
            wind_pool_mw=5000.0,
            solar_pool_mw=5000.0,
            peak_demand_mw=100_000.0,
        )
        solar = next(r for r in ledger if r["tech"] == "solar")
        self.assertGreater(solar["capacity_revenue_per_mw_yr"], 0.0)
        credit = resolve_renewable_capacity_credit(
            "solar",
            "PJM",
            installed_mw=5000.0,
            peak_demand_mw=100_000.0,
            curves_enabled=config.renewable_elcc_curves,
        )
        # Same per-firm-MW price seam as thermal: payment = price x credit.
        design = MARKET_DESIGN.get("PJM", DEFAULT_MARKET_DESIGN)
        firm_price = design.capacity_price_per_firm_mw_yr(
            config, None, iso="PJM", year=2030
        )
        self.assertAlmostEqual(
            solar["capacity_revenue_per_mw_yr"], firm_price * credit, places=6
        )

    def test_vre_capacity_revenue_noop_in_energy_only_iso(self):
        # ERCOT prices capacity at zero — the armed gate must change nothing.
        config = self._config(
            iso="ERCOT",
            entry_screen_diagnostics=True,
            entry_vre_capacity_revenue=True,
        )
        ledger: list[dict] = []
        apply_economic_new_entry(
            [],
            np.full(8760, 30.0),
            2030,
            config,
            "ERCOT",
            screen_ledger=ledger,
            wind_pool_mw=5000.0,
            solar_pool_mw=5000.0,
            peak_demand_mw=80_000.0,
        )
        solar = next(r for r in ledger if r["tech"] == "solar")
        self.assertEqual(solar["capacity_revenue_per_mw_yr"], 0.0)

    def test_growth_ladder_caps_listed_tech_only(self):
        # A listed tech is capped at its ladder MW; an absent tech keeps the
        # static-cap behaviour (rule 25 neutral fallback).
        config = self._config(iso="ERCOT")
        prices = np.full(8760, 250.0)
        new_fleet, additions = apply_economic_new_entry(
            [],
            prices,
            2030,
            config,
            "ERCOT",
            entry_rate_caps_mw={"wind": 500.0},
        )
        by_tech = _entry_by_tech(new_fleet, additions)
        self.assertAlmostEqual(by_tech["wind"], 500.0)
        # Solar carries no ladder row: still bounded only by static caps.
        self.assertGreater(by_tech.get("solar", 0.0), 500.0)

    def test_backstop_rate_limit_caps_build(self):
        config = ScenarioConfig(iso="ERCOT", reserve_margin_build_enabled=True)
        fleet = [_gen("cc", "gas_cc", pmax=1000.0)]
        _, built_uncapped = apply_reserve_margin_build(
            fleet, 5000.0, 8000.0, 2030, config, "ERCOT"
        )
        self.assertGreater(built_uncapped, 200.0)
        new_fleet, built = apply_reserve_margin_build(
            fleet, 5000.0, 8000.0, 2030, config, "ERCOT", rate_limit_mw=200.0
        )
        self.assertAlmostEqual(built, 200.0)
        unit = next(g for g in new_fleet if g.unit_id == "gas_ct_adequacy_2030")
        self.assertAlmostEqual(unit.pmax_mw, 200.0)

    def test_cod_lag_defers_builds_to_pipeline(self):
        # With the lag gate armed, cleared builds book pending rows instead
        # of materializing; decision and COD years are both recorded.
        config = self._config(iso="ERCOT", entry_commissioning_lag=True)
        pipeline: list[dict] = []
        new_fleet, additions = apply_economic_new_entry(
            [],
            np.full(8760, 250.0),
            2030,
            config,
            "ERCOT",
            entry_pipeline=pipeline,
        )
        self.assertEqual(new_fleet, [])
        self.assertEqual(additions, {})
        self.assertTrue(pipeline)
        for row in pipeline:
            self.assertEqual(row["decision_year"], 2030)
            self.assertEqual(
                row["cod_year"], 2030 + ENTRY_COD_LAG_YEARS.get(row["tech"], 2)
            )

    def test_pending_queue_nets_against_caps(self):
        # A wind pipeline already holding the full per-tech cap blocks a new
        # wind decision (the anti-stuffing netting).
        config = self._config(iso="ERCOT", entry_commissioning_lag=True)
        cap_mw = QUEUE_CAP_PER_TECH_GW["ERCOT"]["wind"] * 1000.0
        pipeline = [
            {
                "tech": "wind",
                "mw": cap_mw,
                "zone": "ERCOT-West",
                "decision_year": 2029,
                "cod_year": 2031,
                "seq": 0,
                "kind": "vre",
            }
        ]
        apply_economic_new_entry(
            [],
            np.full(8760, 250.0),
            2030,
            config,
            "ERCOT",
            entry_pipeline=pipeline,
        )
        new_wind = [
            r for r in pipeline if r["tech"] == "wind" and r["decision_year"] == 2030
        ]
        self.assertEqual(new_wind, [])

    def test_evolve_fleet_commissions_due_pipeline_rows(self):
        # Rows at their COD year materialize (thermal → fleet, VRE → pools)
        # and leave the pipeline; the ledger carries both years.
        from market_sim.data.renewables import get_renewable_zone
        from market_sim.results.evolution_ledger import new_events

        solar_zone = get_renewable_zone("ERCOT", "solar")
        pipeline = [
            {
                "tech": "solar",
                "mw": 100.0,
                "zone": solar_zone,
                "decision_year": 2028,
                "cod_year": 2030,
                "seq": 0,
                "kind": "vre",
            },
            {
                "tech": "gas_ct",
                "mw": 50.0,
                "zone": "ERCOT-Houston",
                "decision_year": 2028,
                "cod_year": 2030,
                "seq": 1,
                "kind": "thermal",
            },
            {
                "tech": "wind",
                "mw": 75.0,
                "zone": "ERCOT-West",
                "decision_year": 2029,
                "cod_year": 2031,
                "seq": 0,
                "kind": "vre",
            },
        ]
        config = ScenarioConfig(iso="ERCOT", entry_commissioning_lag=True)
        events = new_events()
        fleet, _, renewable_additions, _, _ = evolve_fleet(
            [],
            None,
            2030,
            config,
            {},
            events=events,
            entry_pipeline=pipeline,
        )
        self.assertAlmostEqual(renewable_additions[solar_zone]["solar"], 100.0)
        self.assertAlmostEqual(
            sum(g.pmax_mw for g in fleet if g.fuel_type == "gas_ct"), 50.0
        )
        # The undelivered 2031 wind row stays pending.
        self.assertEqual(len(pipeline), 1)
        self.assertEqual(pipeline[0]["tech"], "wind")
        commissioned = [
            e for e in events["entry_pipeline"] if e["event"] == "commissioned"
        ]
        self.assertEqual(sorted(r["tech"] for r in commissioned), ["gas_ct", "solar"])
        for row in commissioned:
            self.assertIn("decision_year", row)
            self.assertIn("cod_year", row)


if __name__ == "__main__":
    unittest.main()
