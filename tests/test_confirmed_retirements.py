"""Tests for the confirmed-retirement consumption seam and first-year wiring.

Covers ``data.confirmed_retirements.load_confirmed_exits`` (superseded filter,
earliest-instrument-per-unit) against a tmp CLEAN_DIR fixture, the first-year
``build_base_fleet`` exclusion (closing the "a 2026 exit can never happen in
2026" hole), the flag-off byte-identical guard, the post-2026-07-05 default-on
canary, and the forecast-mode-only gate that keeps a backcast run a hard
no-op regardless of the flag's default (``runner._confirmed_exits_active``).
"""

import datetime as dt
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import pandas as pd

from scripts import curate_confirmed_retirements as curate_cr
from scripts.lib import clean_io
from scripts.lib import confirmed_retirements as cr

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import fleet as fleet_mod
from market_sim.data.confirmed_retirements import (
    ConfirmedExit,
    load_announced_reversal_plants,
    load_confirmed_exits,
)
from market_sim.data.fleet import Generator, build_base_fleet
from market_sim.runner import _confirmed_exits_active

# Two live rows for one unit (earliest wins) + a superseded row for another.
_CSV = """iso,plant_id,generator_id,unit_name,capacity_mw,exit_year,exit_month,confirmation_class,instrument_id,instrument,instrument_date,superseded,superseding_instrument,source_url,source_doc,accessed,notes
ERCOT,111,1,Alpha 1,100.0,2030,,consent_decree,cd-late,Decree A,2024-01-01,false,,https://e/1,doc,2026-07-05,
ERCOT,111,1,Alpha 1,100.0,2027,,rto_deactivation,deact-early,Deact A,2024-06-01,false,,https://e/2,doc,2026-07-05,
ERCOT,222,3,Beta 3,300.0,2026,,statute,stat-beta,Statute B,2023-01-01,true,superseding amendment,https://e/3,doc,2026-07-05,
"""

_SPINE = pd.DataFrame(
    {
        "plant_id": [111, 222],
        "generator_id": ["1", "3"],
        "nameplate_capacity_mw": [100.0, 300.0],
    }
)


class TestLoadConfirmedExits(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        (self.raw_root / cr.DATATYPE).mkdir(parents=True)
        (self.raw_root / cr.DATATYPE / "ercot.csv").write_text(_CSV)
        self.spine_path = root / "spine.parquet"
        _SPINE.to_parquet(self.spine_path, index=False)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"
        curate_cr.curate(
            raw_root=self.raw_root, isos=["ERCOT"], spine_path=self.spine_path
        )

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_earliest_live_instrument_and_superseded_dropped(self) -> None:
        exits = load_confirmed_exits("ERCOT")
        # Beta 3 is superseded -> dropped; Alpha 1 keeps the earliest live year.
        self.assertEqual(len(exits), 1)
        e = exits[0]
        self.assertEqual((e.plant_id, e.generator_id), (111, "1"))
        self.assertEqual(e.exit_year, 2027)  # earliest of {2030, 2027}
        self.assertEqual(e.mw, 100.0)

    def test_absent_partition_returns_empty(self) -> None:
        self.assertEqual(load_confirmed_exits("MISO"), [])


def _nuke(plant_code, gen_id, retirement_year=None):
    return Generator(
        unit_id=f"{plant_code}_{gen_id}",
        name=f"{plant_code}_{gen_id}",
        zone="ERCOT",
        fuel_type="nuclear",
        pmax_mw=1000.0,
        pmin_mw=900.0,
        plant_code=plant_code,
        retirement_year=retirement_year,
    )


class TestBuildBaseFleetFirstYear(unittest.TestCase):
    """A unit confirmed for the first simulated year is excluded up front."""

    def _run(self, enabled: bool) -> list[str]:
        from market_sim.config.iso_configs import get_iso_config

        iso_config = get_iso_config("ERCOT")
        zone_names = [z.name for z in iso_config.zones]
        fleet = [_nuke(111, "1"), _nuke(222, "2")]
        config = ScenarioConfig(iso="ERCOT", confirmed_exits_enabled=enabled)
        exits = [
            ConfirmedExit(plant_id=111, generator_id="1", exit_year=2026, mw=1000.0)
        ]
        # Non-CAMPD path: aggregate_fleet passes nuclear through unchanged.
        with mock.patch.object(fleet_mod, "load_fleet_from_csv", return_value=fleet):
            out = build_base_fleet(
                None,
                "ERCOT",
                iso_config,
                zone_names,
                config,
                [],
                [],
                2026,
                confirmed_exits=exits,
            )
        return sorted(g.unit_id for g in out if g.fuel_type == "nuclear")

    def test_confirmed_first_year_unit_excluded(self) -> None:
        self.assertEqual(self._run(enabled=True), ["222_2"])

    def test_flag_off_keeps_confirmed_unit(self) -> None:
        # Flag off: the confirmed exit is ignored, both units present.
        self.assertEqual(self._run(enabled=False), ["111_1", "222_2"])


class TestConfirmedExitsDefaultAndBackcastGate(unittest.TestCase):
    """Post-2026-07-05 default flip + the forecast-mode-only gate that makes
    a backcast run byte-identical regardless of the flag's default."""

    def test_default_is_enabled(self) -> None:
        self.assertTrue(ScenarioConfig().confirmed_exits_enabled)

    def test_forecast_mode_active_by_default(self) -> None:
        config = ScenarioConfig(mode="forecast")
        self.assertTrue(_confirmed_exits_active(config))

    def test_backcast_mode_is_noop_even_with_flag_on(self) -> None:
        config = ScenarioConfig(mode="backcast")
        # The flag's value is unaffected by mode -- it's the forecast-only
        # gate in runner._confirmed_exits_active that must suppress it.
        self.assertTrue(config.confirmed_exits_enabled)
        self.assertFalse(_confirmed_exits_active(config))

    def test_flag_off_disables_even_in_forecast(self) -> None:
        config = ScenarioConfig(mode="forecast", confirmed_exits_enabled=False)
        self.assertFalse(_confirmed_exits_active(config))


# A Byron/Dresden-analog reversal row (instrument_date pre-2020, superseding
# instrument dated 2021-09-15) + a Braunig-analog confirmed exit whose OWN
# instrument postdates 2020 -- the two RC-1B D4 regressions.
_GATE_CSV = """iso,plant_id,generator_id,unit_name,capacity_mw,exit_year,exit_month,confirmation_class,instrument_id,instrument,instrument_date,superseded,superseding_instrument,superseding_instrument_date,source_url,source_doc,accessed,notes
PJM,6023,1,Byron 1,1224.9,2021,9,rto_deactivation,pjm-deact-byron-1,Deactivation notice,2020-08-27,true,CEJA reversal,2021-09-15,https://e/1,doc,2026-07-05,
ERCOT,3612,1,Braunig 1,225.0,2025,3,rto_deactivation,ercot-nso-braunig-1,NSO acceptance,2024-03-13,false,,,https://e/2,doc,2026-07-05,
"""


class TestHindcastInformationGate(unittest.TestCase):
    """RC-1B / RC-0B D4: as-of-vintage-cutoff gating for both channels."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        (self.raw_root / cr.DATATYPE).mkdir(parents=True)
        (self.raw_root / cr.DATATYPE / "pjm.csv").write_text(_GATE_CSV)
        (self.raw_root / cr.DATATYPE / "ercot.csv").write_text(_GATE_CSV)
        self.spine_path = root / "spine.parquet"
        pd.DataFrame(
            {
                "plant_id": [6023, 3612],
                "generator_id": ["1", "1"],
                "nameplate_capacity_mw": [1224.9, 225.0],
            }
        ).to_parquet(self.spine_path, index=False)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"
        curate_cr.curate(
            raw_root=self.raw_root, isos=["PJM", "ERCOT"], spine_path=self.spine_path
        )
        self._cutoff_2020 = dt.date(2020, 12, 31)

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_byron_dresden_reversal_not_suppressed_as_of_2020(self) -> None:
        # The CEJA reversal (2021-09-15) postdates the 2020 cutoff -> the
        # plant must NOT appear as a suppressed reversal in an as-of-2020
        # hindcast (its announced date should still fire).
        self.assertEqual(
            load_announced_reversal_plants("PJM", as_of=self._cutoff_2020),
            frozenset(),
        )

    def test_byron_dresden_reversal_suppressed_once_ceja_knowable(self) -> None:
        self.assertEqual(
            load_announced_reversal_plants("PJM", as_of=dt.date(2022, 1, 1)),
            frozenset({6023}),
        )

    def test_reversal_no_cutoff_is_byte_identical_to_pre_rc1b(self) -> None:
        self.assertEqual(load_announced_reversal_plants("PJM"), frozenset({6023}))

    def test_braunig_confirmed_exit_not_knowable_as_of_2020(self) -> None:
        # instrument_date 2024-03-13 postdates the 2020 cutoff.
        self.assertEqual(load_confirmed_exits("ERCOT", as_of=self._cutoff_2020), [])

    def test_braunig_confirmed_exit_present_with_no_cutoff(self) -> None:
        exits = load_confirmed_exits("ERCOT")
        self.assertEqual(len(exits), 1)
        self.assertEqual(exits[0].plant_id, 3612)


if __name__ == "__main__":
    unittest.main()
