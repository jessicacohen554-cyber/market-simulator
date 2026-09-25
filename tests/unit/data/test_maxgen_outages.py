"""Tests for the declared-event-window (maxgen) revealed-derate channel (M-2).

Covers the frozen identification guards of
``scripts/data/derive_campd_maxgen_outages.py`` (window clipping/merging, the
in-merit certificate, the ±45-day capability basis with best-hour credit,
disjointness vs the std/short extracts) and the consumer
(:func:`market_sim.data.outages.unit_outage_maxgen_derate_factors` +
``ScenarioConfig.unit_outage_maxgen_events`` gate in
``fleet.generators_to_fleet_arrays``): off-state byte identity, hour-granular
window application, and class-agnostic routing (the CT/CC leg is this
channel's reason to exist). Trivial synthetic cases first (CLAUDE.md testing
pattern).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.data import outages
from market_sim.data.outages import _hour_of_year
from scripts.data.derive_campd_maxgen_outages import (
    _overlaps,
    _zone_in_region,
    assert_disjoint,
    capability_and_derate,
    certificate_hours,
    merge_event_blocks,
)


class CapabilityAndDerateTest(unittest.TestCase):
    """Guard 3: ±45d capability basis, best-event-hour credit, floor at 0."""

    def setUp(self):
        # Trivial synthetic case: a 10-day hourly clock, one unit.
        self.clock = pd.date_range("2025-07-01", periods=240, freq="h")
        self.gross = np.zeros(240)

    def test_absent_unit_derates_full_capability(self):
        # Ran at 100 MW for a day two weeks... (here: day 1), silent in the
        # block (day 5) -> derate = full demonstrated capability.
        self.gross[0:24] = 100.0
        cap, best, derate = capability_and_derate(
            self.gross,
            self.clock,
            pd.Timestamp("2025-07-05"),
            pd.Timestamp("2025-07-06"),
        )
        self.assertEqual(cap, 100.0)
        self.assertEqual(best, 0.0)
        self.assertEqual(derate, 100.0)

    def test_best_hour_credit_zeroes_the_derate(self):
        # A single in-block hour at capability -> not derated (reserve
        # holdback is invisible to the measure by design).
        self.gross[0:24] = 100.0
        self.gross[4 * 24 + 12] = 100.0  # one hour inside the block
        cap, best, derate = capability_and_derate(
            self.gross,
            self.clock,
            pd.Timestamp("2025-07-05"),
            pd.Timestamp("2025-07-06"),
        )
        self.assertEqual(best, 100.0)
        self.assertEqual(derate, 0.0)

    def test_partial_reduction_measures_the_gap(self):
        self.gross[0:24] = 100.0
        self.gross[4 * 24 : 5 * 24] = 60.0  # ran reduced through the block
        cap, best, derate = capability_and_derate(
            self.gross,
            self.clock,
            pd.Timestamp("2025-07-05"),
            pd.Timestamp("2025-07-06"),
        )
        self.assertEqual(derate, 40.0)

    def test_block_hour_outside_never_counts_as_best(self):
        # Output the hour AFTER the block ends must not credit the block
        # (half-open end).
        self.gross[0:24] = 100.0
        self.gross[5 * 24] = 100.0  # first hour after block end
        cap, best, derate = capability_and_derate(
            self.gross,
            self.clock,
            pd.Timestamp("2025-07-05"),
            pd.Timestamp("2025-07-06"),
        )
        self.assertEqual(best, 0.0)
        self.assertEqual(derate, 100.0)

    def test_capability_window_is_centered_and_clipped(self):
        # Capability evidence outside ±45d of the block midpoint is ignored;
        # here the clock is only 10 days so clipping is exercised trivially,
        # and the event_month basis reads the block's calendar month only.
        self.gross[0:24] = 80.0  # July evidence
        cap45, _, _ = capability_and_derate(
            self.gross,
            self.clock,
            pd.Timestamp("2025-07-05"),
            pd.Timestamp("2025-07-06"),
            basis="pm45d",
        )
        capm, _, deratem = capability_and_derate(
            self.gross,
            self.clock,
            pd.Timestamp("2025-07-05"),
            pd.Timestamp("2025-07-06"),
            basis="event_month",
        )
        self.assertEqual(cap45, 80.0)
        self.assertEqual(capm, 80.0)
        self.assertEqual(deratem, 80.0)
        with self.assertRaises(ValueError):
            capability_and_derate(
                self.gross,
                self.clock,
                pd.Timestamp("2025-07-05"),
                pd.Timestamp("2025-07-06"),
                basis="year",
            )


class MergeEventBlocksTest(unittest.TestCase):
    """Guard 1: declared windows merge into blocks; overlap never widens scope."""

    @staticmethod
    def _row(region: str, level: str, start: str, end: str) -> dict:
        return {
            "region": region,
            "level": level,
            "start_model": pd.Timestamp(start),
            "end_model_excl": pd.Timestamp(end),
        }

    def test_overlapping_and_contiguous_same_region_merge(self):
        df = pd.DataFrame(
            [
                self._row(
                    "footprint",
                    "capacity_advisory",
                    "2025-07-28 12:00",
                    "2025-07-29 22:00",
                ),
                self._row(
                    "footprint", "maxgen_alert", "2025-07-28 14:00", "2025-07-28 22:00"
                ),
                self._row(
                    "footprint",
                    "maxgen_warning",
                    "2025-07-29 00:00",
                    "2025-07-30 00:00",
                ),
            ]
        )
        blocks = merge_event_blocks(df)
        self.assertEqual(len(blocks), 1)
        b = blocks[0]
        self.assertEqual(b["start"], pd.Timestamp("2025-07-28 12:00"))
        self.assertEqual(b["end"], pd.Timestamp("2025-07-30 00:00"))
        self.assertEqual(b["n_windows"], 3)

    def test_distinct_regions_and_gaps_stay_separate(self):
        df = pd.DataFrame(
            [
                self._row(
                    "midwest",
                    "maxgen_event_step1",
                    "2025-06-23 00:00",
                    "2025-06-24 00:00",
                ),
                self._row(
                    "midwest", "maxgen_warning", "2025-06-24 00:00", "2025-06-25 00:00"
                ),
                self._row(
                    "footprint",
                    "capacity_advisory",
                    "2025-07-24 00:00",
                    "2025-07-25 00:00",
                ),
            ]
        )
        blocks = merge_event_blocks(df)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["region"], "midwest")
        self.assertEqual(blocks[0]["end"], pd.Timestamp("2025-06-25 00:00"))
        self.assertEqual(blocks[1]["region"], "footprint")

    def test_zone_region_scope(self):
        self.assertTrue(_zone_in_region("MISO-South", "south"))
        self.assertFalse(_zone_in_region("MISO-South", "midwest"))
        self.assertTrue(_zone_in_region("MISO-East", "midwest"))
        self.assertTrue(_zone_in_region("MISO-South", "footprint"))
        with self.assertRaises(ValueError):
            _zone_in_region("MISO-East", "narnia")


class CertificateHoursTest(unittest.TestCase):
    """Guard 2: region-scoped DA in-merit certificate."""

    def setUp(self):
        ts = pd.date_range("2025-07-28", periods=48, freq="h")
        self.hub = pd.DataFrame({"INDIANA.HUB": 40.0, "ARKANSAS.HUB": 40.0}, index=ts)

    def test_counts_distinct_hours_above_threshold_in_region(self):
        self.hub.loc["2025-07-28 15:00":"2025-07-28 17:00", "INDIANA.HUB"] = 300.0
        n = certificate_hours(
            self.hub,
            "midwest",
            pd.Timestamp("2025-07-28 12:00"),
            pd.Timestamp("2025-07-29 22:00"),
        )
        self.assertEqual(n, 3)
        # The South hubs never cleared $150 -> a south-scoped window is slack.
        n_south = certificate_hours(
            self.hub,
            "south",
            pd.Timestamp("2025-07-28 12:00"),
            pd.Timestamp("2025-07-29 22:00"),
        )
        self.assertEqual(n_south, 0)

    def test_hours_outside_the_window_never_count(self):
        self.hub.loc["2025-07-28 05:00", "INDIANA.HUB"] = 500.0  # pre-window
        n = certificate_hours(
            self.hub,
            "footprint",
            pd.Timestamp("2025-07-28 12:00"),
            pd.Timestamp("2025-07-29 22:00"),
        )
        self.assertEqual(n, 0)


class DisjointnessTest(unittest.TestCase):
    """Guard 4: std/short-covered unit-hours are excluded; overlaps assert."""

    COVERED = {
        (889, "1"): [
            (pd.Timestamp("2025-07-28"), pd.Timestamp("2025-07-31"))  # day-grain
        ]
    }

    def test_overlap_detection(self):
        self.assertTrue(
            _overlaps(
                self.COVERED,
                889,
                "1",
                pd.Timestamp("2025-07-28 12:00"),
                pd.Timestamp("2025-07-30 00:00"),
            )
        )
        self.assertFalse(
            _overlaps(
                self.COVERED,
                889,
                "2",  # different unit
                pd.Timestamp("2025-07-28 12:00"),
                pd.Timestamp("2025-07-30 00:00"),
            )
        )
        self.assertFalse(
            _overlaps(
                self.COVERED,
                889,
                "1",
                pd.Timestamp("2025-08-05 00:00"),  # disjoint window
                pd.Timestamp("2025-08-06 00:00"),
            )
        )

    def test_assert_disjoint_raises_on_overlap(self):
        row = {
            "facility_id": 889,
            "unit_id": "1",
            "window_start": "2025-07-28 12:00",
            "window_end": "2025-07-30 00:00",
        }
        with self.assertRaises(AssertionError):
            assert_disjoint([row], self.COVERED)
        # A non-overlapping row passes.
        clean = dict(
            row, window_start="2025-08-05 00:00", window_end="2025-08-06 00:00"
        )
        assert_disjoint([clean], self.COVERED)


class MaxgenDerateFactorsTest(unittest.TestCase):
    """The consumer loader: hour-granular, class-agnostic, no-op when absent."""

    # Baldwin Energy Complex — a real MISO plant in the model fleet, so
    # _iso_plant_capacity("MISO") carries its (code, COAL) bin (the same
    # anchor the short-window tests use).
    PLANT = 889

    COLS = [
        "facility_name",
        "facility_id",
        "unit_id",
        "plant_group",
        "zone",
        "region",
        "levels",
        "window_start",
        "window_end",
        "capability_mw",
        "capability_month_mw",
        "capability_basis",
        "best_window_mw",
        "derate_mw",
        "derate_month_mw",
        "nameplate_mw",
        "capacity_source",
        "plant_capacity_mw",
    ]

    def _row(self, code: int, group: str, derate: float) -> dict:
        return {
            "facility_name": "x",
            "facility_id": code,
            "unit_id": "1",
            "plant_group": group,
            "zone": "MISO-East",
            "region": "footprint",
            "levels": "maxgen_warning",
            "window_start": "2025-07-28 12:00",
            "window_end": "2025-07-30 00:00",
            "capability_mw": derate,
            "capability_month_mw": derate,
            "capability_basis": "pm45d",
            "best_window_mw": 0.0,
            "derate_mw": derate,
            "derate_month_mw": derate,
            "nameplate_mw": derate,
            "capacity_source": "eia_exact",
            "plant_capacity_mw": 0.0,
        }

    def _factors(self, rows: list[dict] | None, year: int = 2025):
        outages.unit_outage_maxgen_derate_factors.cache_clear()
        if rows is None:
            target = Path("/nonexistent/maxgen.csv")
            with patch.object(
                outages, "unit_outage_maxgen_csv_for_iso", return_value=target
            ):
                return outages.unit_outage_maxgen_derate_factors(year, iso="MISO")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "campd-unit-outages-maxgen-MISO.csv"
            pd.DataFrame(rows, columns=self.COLS).to_csv(path, index=False)
            with patch.object(
                outages, "unit_outage_maxgen_csv_for_iso", return_value=path
            ):
                factors = outages.unit_outage_maxgen_derate_factors(year, iso="MISO")
        outages.unit_outage_maxgen_derate_factors.cache_clear()
        return factors

    def test_missing_file_is_a_noop(self):
        self.assertEqual(self._factors(None), {})

    def test_hour_granular_window_derates_only_its_span(self):
        factors = self._factors([self._row(self.PLANT, "COAL", 300.0)])
        key = (self.PLANT, "COAL")
        self.assertIn(key, factors)
        arr = factors[key]
        self.assertEqual(arr.shape, (HOURS_PER_YEAR,))
        lo = _hour_of_year(7, 28, 12)
        hi = _hour_of_year(7, 30, 0)
        cap = outages._iso_plant_capacity("MISO")[key]
        np.testing.assert_allclose(arr[lo:hi], 1.0 - 300.0 / cap)
        # Hour-granular boundaries: the hour before the declared start and
        # the return-to-normal hour itself are untouched (no day inflation).
        self.assertEqual(arr[lo - 1], 1.0)
        self.assertEqual(arr[hi], 1.0)
        self.assertTrue((arr[:lo] == 1.0).all())
        self.assertTrue((arr[hi:] == 1.0).all())

    def test_class_agnostic_ct_rows_route(self):
        # The CT/CC leg is this channel's reason to exist: a CT_PEAKER row
        # must route (the std/short loaders exclude CTs by design).
        cap_map = outages._iso_plant_capacity("MISO")
        ct_key = next(k for k in cap_map if k[1] == "CT_PEAKER")
        factors = self._factors([self._row(ct_key[0], "CT_PEAKER", 50.0)])
        self.assertIn(ct_key, factors)

    def test_unknown_plant_and_nonpositive_derate_are_skipped(self):
        rows = [
            self._row(999999999, "COAL", 300.0),  # not in the model fleet
            self._row(self.PLANT, "COAL", 0.0),  # floored-out derate
        ]
        self.assertEqual(self._factors(rows), {})


class FleetGateByteIdentityTest(unittest.TestCase):
    """The ScenarioConfig gate: default off everywhere, byte-identical off-state."""

    def _fleet_arrays(self, cfg):
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays

        gen = Generator(
            unit_id="889_1",
            name="baldwin synth",
            zone="MISO-East",
            fuel_type="coal",
            pmax_mw=600.0,
            pmin_mw=0.0,
            heat_rate=10.0,
            vom=4.0,
            emission_rate_co2=0.95,
            nox_rate=0.0,
            eford=0.05,
            online_year=1975,
            plant_code=889,
            is_campd_bin=True,
            plant_group="COAL_BIT",
        )
        return generators_to_fleet_arrays(
            [gen],
            ["MISO-East"],
            hours=HOURS_PER_YEAR,
            iso="MISO",
            config=cfg,
            year=2025,
        )

    def test_default_off_and_explicit_off_are_byte_identical(self):
        from market_sim.config.scenarios import ScenarioConfig

        self.assertFalse(ScenarioConfig().unit_outage_maxgen_events)
        base = ScenarioConfig(
            weather_year=2025, iso="MISO", mode="backcast", outage_source="historic"
        )
        off = base.with_overrides(unit_outage_maxgen_events=False)
        fa_default = self._fleet_arrays(base)
        fa_off = self._fleet_arrays(off)
        np.testing.assert_array_equal(fa_default.availability, fa_off.availability)

    def test_flag_on_derates_only_inside_registry_windows(self):
        from market_sim.config.scenarios import ScenarioConfig

        base = ScenarioConfig(
            weather_year=2025, iso="MISO", mode="backcast", outage_source="historic"
        )
        on = base.with_overrides(unit_outage_maxgen_events=True)
        rows = pd.DataFrame(
            [
                {
                    "facility_id": 889,
                    "unit_id": "1",
                    "plant_group": "COAL",
                    "window_start": "2025-07-28 12:00",
                    "window_end": "2025-07-30 00:00",
                    "derate_mw": 300.0,
                }
            ]
        )
        outages.unit_outage_maxgen_derate_factors.cache_clear()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "campd-unit-outages-maxgen-MISO.csv"
            rows.to_csv(path, index=False)
            with patch.object(
                outages, "unit_outage_maxgen_csv_for_iso", return_value=path
            ):
                fa_on = self._fleet_arrays(on)
        outages.unit_outage_maxgen_derate_factors.cache_clear()
        fa_off = self._fleet_arrays(base)
        lo = _hour_of_year(7, 28, 12)
        hi = _hour_of_year(7, 30, 0)
        # Inside the declared window: strictly reduced; outside: untouched.
        self.assertTrue(
            (fa_on.availability[0, lo:hi] < fa_off.availability[0, lo:hi]).all()
        )
        np.testing.assert_array_equal(
            fa_on.availability[0, :lo], fa_off.availability[0, :lo]
        )
        np.testing.assert_array_equal(
            fa_on.availability[0, hi:], fa_off.availability[0, hi:]
        )

    def test_flag_on_with_no_file_is_byte_identical(self):
        from market_sim.config.scenarios import ScenarioConfig

        base = ScenarioConfig(
            weather_year=2025, iso="MISO", mode="backcast", outage_source="historic"
        )
        on = base.with_overrides(unit_outage_maxgen_events=True)
        outages.unit_outage_maxgen_derate_factors.cache_clear()
        with patch.object(
            outages,
            "unit_outage_maxgen_csv_for_iso",
            return_value=Path("/nonexistent/maxgen.csv"),
        ):
            fa_on = self._fleet_arrays(on)
        outages.unit_outage_maxgen_derate_factors.cache_clear()
        fa_off = self._fleet_arrays(base)
        np.testing.assert_array_equal(fa_on.availability, fa_off.availability)


if __name__ == "__main__":
    unittest.main()
