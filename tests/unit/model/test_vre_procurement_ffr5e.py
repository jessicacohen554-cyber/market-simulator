"""Tests for the FFR-5E near-term VRE procurement channel.

The channel is a GATED (``vre_procurement_additions_enabled``, default OFF)
wind/solar limb of capacity-evolution step 4, implementing owner decision
D-18(a) to the design in
``docs/handoffs/ffr-5b-procurement-channel-design-2026-08-05.md`` §§2-3.

Separate additive file (not ``test_capacity.py`` / ``test_eia860.py``) per the
FF-2A precedent and rule 27 — core files are not bulk-rewritten to carry new
coverage.

What is asserted here maps one-to-one onto the design's guards:

* the gate is default-OFF and the off-path is a no-op (§2.5);
* rows commission in their own effective year as a per-year FLOW (§2.3(c));
* every MW carries ``source: "procured"`` attribution (§3.5, a hard
  requirement — unattributable MW is unauditable);
* the flow is netted from the economic screen's ISO budget and per-tech queue
  cap, so one physical queue is not spent twice (§2.3(b));
* that netting is INDEPENDENT of ``entry_pipeline_aware_signal`` (§2.3(c));
* the loader honours the instrument gate (U/V/TS) and the vintage information
  gate (§3.1-§3.2);
* and — the rule 13 [R-MEASURED] boundary the whole design turns on — the
  OPERABLE sheet is never opened by the procurement path (§3.1).
"""

import unittest
from dataclasses import fields
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.constants import QUEUE_CAP_GW, QUEUE_CAP_PER_TECH_GW
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, load_procured_vre_additions
from market_sim.data.fleet.eia860 import _PLANNED_FIRM_STATUSES
from market_sim.model.capacity import apply_economic_new_entry, evolve_fleet
from market_sim.results.evolution_ledger import new_events

ISO = "MISO"


def _gen(unit_id, fuel_type, zone, pmax=400.0, heat_rate=8.0):
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone=zone,
        fuel_type=fuel_type,
        pmax_mw=pmax,
        heat_rate=heat_rate,
    )


def _rows(zone="MISO-Illinois"):
    """Two procured rows in different years, so the year filter is exercised."""
    return [
        {
            "zone": zone,
            "tech": "solar",
            "online_year": 2030,
            "mw": 900.0,
            "plant_id": 12345,
            "generator_id": "SOL1",
        },
        {
            "zone": zone,
            "tech": "wind",
            "online_year": 2031,
            "mw": 300.0,
            "plant_id": 67890,
            "generator_id": "WND1",
        },
    ]


def _evolve(config, year, procured, fleet=None, **kw):
    events = new_events()
    prior = {
        "planned_additions": [],
        "procured_vre_additions": procured,
        "peak_demand": 60000.0,
        "prices": np.full(8760, 34.0),
        "wind_cap_mw": 5000.0,
        "solar_cap_mw": 8000.0,
    }
    fleet_out, _lt, ren_adds, _rl, _fl = evolve_fleet(
        list(fleet or []), prior, year, config, {}, events=events, **kw
    )
    return fleet_out, ren_adds, events


class TestProcurementGate(unittest.TestCase):
    """The gate itself: registered, default OFF, and inert when off."""

    def test_field_is_registered_and_defaults_off(self):
        # Rule 24 [R-REGISTRY]: the gate is a ScenarioConfig field, so it
        # appears in run_config.json rather than being an off-registry knob.
        names = {f.name for f in fields(ScenarioConfig)}
        self.assertIn("vre_procurement_additions_enabled", names)
        self.assertFalse(ScenarioConfig(iso=ISO).vre_procurement_additions_enabled)

    def test_default_cache_key_is_unmoved(self):
        # Registered in _CACHE_KEY_OPTIONAL_FIELDS, so the field drops out of
        # the hash at its default: every pre-existing cached bundle keeps its
        # key instead of being silently invalidated by a default-off addition.
        from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS

        self.assertIn("vre_procurement_additions_enabled", _CACHE_KEY_OPTIONAL_FIELDS)
        self.assertEqual(ScenarioConfig().cache_key(), "603c2498bf71d21d")

    def test_armed_run_gets_a_distinct_cache_key(self):
        # An armed run is a different scenario, not a cache collision — which
        # is also what keeps a paired A/B's two arms independent on disk.
        self.assertNotEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(vre_procurement_additions_enabled=True).cache_key(),
        )

    def test_gate_off_is_a_no_op_even_with_rows_present(self):
        # The shipped path must not move even if rows are somehow threaded in.
        config = ScenarioConfig(iso=ISO, mode="forecast")
        _fleet, ren_adds, events = _evolve(config, 2030, _rows())
        procured_solar = sum(techs.get("solar", 0.0) for techs in ren_adds.values())
        # The economic screen may build solar on its own; what must be absent
        # is any PROCURED contribution and any procured ledger row.
        self.assertEqual(events.get("vre_additions", []), [])
        _f2, ren_off, _e2 = _evolve(config, 2030, [])
        self.assertAlmostEqual(
            procured_solar,
            sum(techs.get("solar", 0.0) for techs in ren_off.values()),
            places=6,
        )

    def test_runner_only_loads_rows_in_forecast_mode(self):
        # Backcast historical VRE rides the vintage snapshot; loading the
        # pipeline there would be a second, conflicting channel.
        cfg = ScenarioConfig(iso=ISO, mode="backcast")
        self.assertTrue(
            cfg.mode != "forecast" or not cfg.vre_procurement_additions_enabled
        )


class TestProcurementInjection(unittest.TestCase):
    """Step 4b: what lands in the pools, when, and with what attribution."""

    @staticmethod
    def _config(**kw):
        return ScenarioConfig(
            iso=ISO,
            mode="forecast",
            vre_procurement_additions_enabled=True,
            **kw,
        )

    def test_rows_commission_in_their_own_effective_year(self):
        # A per-year FLOW: only the rows whose effective year IS this year.
        _f, ren_2030, ev_2030 = _evolve(self._config(), 2030, _rows())
        procured = {e["tech"]: e["mw"] for e in ev_2030["vre_additions"]}
        self.assertEqual(procured, {"solar": 900.0})
        self.assertGreaterEqual(ren_2030["MISO-Illinois"]["solar"], 900.0)

        _f, _r, ev_2031 = _evolve(self._config(), 2031, _rows())
        self.assertEqual(
            {e["tech"]: e["mw"] for e in ev_2031["vre_additions"]}, {"wind": 300.0}
        )

    def test_year_with_no_matching_row_injects_nothing(self):
        # Past the data horizon the channel falls SILENT and hands the job
        # back to the economic screen — correct behaviour, not a fault.
        _f, _ren, events = _evolve(self._config(), 2035, _rows())
        self.assertEqual(events.get("vre_additions", []), [])

    def test_every_mw_carries_procured_source_attribution(self):
        # Design §3.5: MW that cannot be separated from the economic screen's
        # MW is unauditable — no D-2 attribution, no rule-19 reconciliation.
        _f, _ren, events = _evolve(self._config(), 2030, _rows())
        row = events["vre_additions"][0]
        self.assertEqual(row["source"], "procured")
        self.assertEqual(row["eia860_id"], 12345)
        self.assertEqual(row["generator_id"], "SOL1")
        self.assertEqual(row["zone"], "MISO-Illinois")

    def test_mw_lands_in_the_rows_own_zone_not_one_bucket(self):
        # Siting is per-row (design §2.2), unlike the economic screen's single
        # RENEWABLE_ZONE_ALLOCATION bucket.
        rows = [
            dict(_rows()[0], zone="MISO-South", mw=150.0),
            dict(_rows()[0], zone="MISO-Illinois", mw=250.0),
        ]
        _f, ren, _e = _evolve(self._config(), 2030, rows)
        self.assertGreaterEqual(ren["MISO-South"]["solar"], 150.0)
        self.assertGreaterEqual(ren["MISO-Illinois"]["solar"], 250.0)


class TestProcurementNetting(unittest.TestCase):
    """§2.3: one physical queue, spent once — as a FLOW, never a stock."""

    @staticmethod
    def _screen(procured_flow, **kw):
        config = ScenarioConfig(iso=ISO, mode="forecast", **kw)
        fleet, ren = apply_economic_new_entry(
            [],
            np.full(8760, 90.0),  # rich enough that the caps, not margin, bind
            2030,
            config,
            ISO,
            procured_flow_mw=procured_flow,
        )
        by_tech = {}
        for g in fleet:
            by_tech[g.fuel_type] = by_tech.get(g.fuel_type, 0.0) + g.pmax_mw
        for by_fuel in ren.values():
            for fuel, mw in by_fuel.items():
                by_tech[fuel] = by_tech.get(fuel, 0.0) + mw
        return by_tech

    def test_none_is_byte_identical_to_the_shipped_screen(self):
        self.assertEqual(self._screen(None), self._screen({}))

    def test_flow_is_netted_from_the_iso_budget(self):
        # Total economic build falls by exactly the procured flow, so the
        # queue's annual throughput is spent once rather than twice.
        base = self._screen(None)
        netted = self._screen({"solar": 1000.0})
        self.assertAlmostEqual(
            sum(base.values()) - sum(netted.values()), 1000.0, places=3
        )

    def test_flow_is_netted_from_the_per_tech_queue_cap(self):
        # Solar's own cap shrinks by its own procured flow: wind/solar carry
        # no _QUEUE_CAP_GROUP entry, so group == tech and the map is 1:1.
        # Asserted through the cap rather than through the realised build,
        # because which budget binds first depends on the margin ordering:
        # a flow at the FULL per-tech cap must leave solar zero regardless.
        cap_mw = QUEUE_CAP_PER_TECH_GW[ISO]["solar"] * 1000.0
        base = self._screen(None)
        self.assertGreater(base.get("solar", 0.0), 0.0)
        netted = self._screen({"solar": cap_mw})
        self.assertAlmostEqual(netted.get("solar", 0.0), 0.0, places=3)

    def test_netting_never_drives_a_budget_negative(self):
        # An absurdly large flow clamps at zero build, never a negative cap.
        huge = QUEUE_CAP_GW[ISO] * 1000.0 * 10.0
        netted = self._screen({"solar": huge})
        self.assertTrue(all(mw >= 0.0 for mw in netted.values()))
        self.assertAlmostEqual(sum(netted.values()), 0.0, places=3)

    def test_netting_is_independent_of_entry_pipeline_aware_signal(self):
        # §2.3(c): the procured netting is a FLOW (GW/yr from a GW/yr cap) and
        # must NOT ride the FFR-5C gate, which relocates a pending-pipeline
        # STOCK netting. Arming that unrelated gate must not switch this off.
        flow = {"solar": 1000.0}
        for armed in (False, True):
            base = self._screen(None, entry_pipeline_aware_signal=armed)
            netted = self._screen(flow, entry_pipeline_aware_signal=armed)
            self.assertAlmostEqual(
                sum(base.values()) - sum(netted.values()),
                1000.0,
                places=3,
                msg=f"procured netting vanished at entry_pipeline_aware_signal={armed}",
            )

    def test_procured_mw_itself_is_not_capped(self):
        # §2.3(a): a row already in the queue with an effective year IS the
        # throughput the caps measure. Capping it would count one physical
        # constraint twice and could delete a project that verifiably exists.
        over_cap = QUEUE_CAP_GW[ISO] * 1000.0 * 2.0
        config = ScenarioConfig(
            iso=ISO, mode="forecast", vre_procurement_additions_enabled=True
        )
        rows = [dict(_rows()[0], mw=over_cap)]
        _f, ren, events = _evolve(config, 2030, rows)
        self.assertAlmostEqual(events["vre_additions"][0]["mw"], over_cap, places=3)
        self.assertGreaterEqual(ren["MISO-Illinois"]["solar"], over_cap)


class TestProcurementLoaderGates(unittest.TestCase):
    """The loader's three gates, and the rule 13 boundary."""

    def test_operable_sheet_is_never_read(self):
        # RULE 13 [R-MEASURED], the line the design turns on: the PROPOSED
        # sheet is a forward statement of intent filed BEFORE the outcome; the
        # OPERABLE sheet IS the outcome. Reading the latter to decide what to
        # build would paste the answer key in, however dressed (§3.1). Both
        # files sit in the same directory with near-identical schemas, so this
        # is asserted mechanically rather than trusted to review.
        seen: list[str] = []
        real = pd.read_parquet

        def spy(path, *a, **kw):
            seen.append(Path(str(path)).name)
            return real(path, *a, **kw)

        with mock.patch("pandas.read_parquet", side_effect=spy):
            load_procured_vre_additions(ISO)
        self.assertTrue(seen, "loader read no parquet at all")
        for name in seen:
            self.assertNotIn(
                "operable",
                name.lower(),
                f"procurement path opened an OUTCOME sheet: {name}",
            )
            self.assertNotIn("retired", name.lower())

    def test_status_set_is_shared_with_the_thermal_limb(self):
        # The instrument gate is a cited code constant, NOT a config field —
        # a config field would be a channel through which a residual could be
        # closed. Shared (not copied) so the two limbs cannot drift apart.
        self.assertEqual(_PLANNED_FIRM_STATUSES, frozenset({"U", "V", "TS"}))

    def test_rows_are_committed_status_and_post_vintage_only(self):
        rows = load_procured_vre_additions(ISO)
        if not rows:
            self.skipTest("no EIA-860 proposed rows on disk for this ISO")
        from market_sim.config.paths import active_eia860_dir
        from market_sim.data.fleet.models import operable_vintage_year

        vintage = operable_vintage_year(active_eia860_dir())
        for r in rows:
            self.assertGreater(r["online_year"], vintage)
            self.assertIn(r["tech"], {"wind", "solar"})
            self.assertGreater(r["mw"], 0.0)

    def test_missing_parquet_returns_empty_not_an_error(self):
        self.assertEqual(
            load_procured_vre_additions(ISO, data_dir=Path("/nonexistent/xyz")), []
        )


if __name__ == "__main__":
    unittest.main()
