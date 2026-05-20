"""Tests for the historic-outage availability overlay loader."""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.data.outages import (
    MIN_OUTAGE_SPAN_HOURS,
    QUALIFYING_PLANT_GROUPS,
    _hour_of_year,
    _qualifying_plant_codes,
    outage_hour_mask,
    outage_masks_for_year,
)

# Repository root (tests/ lives at the repo root).
REPO = Path(__file__).parents[1]
BINS_CSV = str(REPO / "inputs" / "custom-bin-assignments.csv")
OUTAGES_CSV = str(REPO / "inputs" / "raw-data" / "ercot-outages.csv")


class HourOfYearTest(unittest.TestCase):
    """The (month, day, hour) -> 8760-clock index, on a non-leap calendar."""

    def test_year_boundaries(self):
        self.assertEqual(_hour_of_year(1, 1, 0), 0)
        self.assertEqual(_hour_of_year(12, 31, 23), HOURS_PER_YEAR - 1)

    def test_march_first_at_day_of_year_59(self):
        # Non-leap: Jan (31) + Feb (28) = 59 days precede Mar 1.
        self.assertEqual(_hour_of_year(3, 1, 0), 59 * 24)

    def test_feb29_snaps_to_march_boundary(self):
        # Feb 29 is dropped from the clock; it maps to Mar 1 00:00.
        self.assertEqual(_hour_of_year(2, 29, 5), 59 * 24)


class OutageHourMaskTest(unittest.TestCase):
    """The (start, stop, year) -> length-8760 bool mask util."""

    def test_simple_window_is_half_open(self):
        # 10:00 -> 13:00 covers hours 10, 11, 12; the stop hour is the
        # return-to-service hour and is not masked.
        mask = outage_hour_mask("2023-01-01 10:00", "2023-01-01 13:00", 2023)
        self.assertEqual(int(mask.sum()), 3)
        self.assertTrue(mask[10] and mask[11] and mask[12])
        self.assertFalse(mask[13])

    def test_window_in_other_year_is_empty(self):
        mask = outage_hour_mask("2023-05-01", "2023-05-20", 2024)
        self.assertEqual(int(mask.sum()), 0)

    def test_degenerate_window_is_empty(self):
        mask = outage_hour_mask("2023-05-01 05:00", "2023-05-01 05:00", 2023)
        self.assertEqual(int(mask.sum()), 0)

    def test_year_straddle_splits_and_unions(self):
        # T H Wharton's real window: 2024-12-16 09:00 -> 2025-01-03 11:00.
        start, stop = "2024-12-16 09:00", "2025-01-03 11:00"
        m24 = outage_hour_mask(start, stop, 2024)
        m25 = outage_hour_mask(start, stop, 2025)
        # 2024 portion runs from the start hour through year end.
        self.assertTrue(m24[-1])
        self.assertEqual(
            int(m24.sum()), HOURS_PER_YEAR - _hour_of_year(12, 16, 9)
        )
        # 2025 portion runs from year start up to the stop hour (exclusive).
        self.assertTrue(m25[0])
        self.assertEqual(int(m25.sum()), _hour_of_year(1, 3, 11))

    def test_leap_window_contiguous_with_feb29_dropped(self):
        # A window across Feb 29 in a leap year stays contiguous on the
        # non-leap clock: the dropped Feb 29 simply does not appear.
        mask = outage_hour_mask("2024-02-17 08:00", "2024-03-03 17:00", 2024)
        lo = _hour_of_year(2, 17, 8)
        hi = _hour_of_year(3, 3, 17)
        self.assertEqual(int(mask.sum()), hi - lo)
        self.assertTrue(mask[lo])
        self.assertTrue(mask[hi - 1])
        self.assertFalse(mask[hi])


class BuildMasksFilterTest(unittest.TestCase):
    """The coal/CC group + span>10-day filter, on synthetic inputs."""

    def _write_inputs(self, tmp: Path) -> tuple[str, str]:
        bins = tmp / "bins.csv"
        bins.write_text(
            "Plant_Group,Plant_Code\n"
            "COAL,111\n"
            "CC_REGULAR,222\n"
            "CT_PEAKER,333\n"
            "ST_GAS,444\n"
            "CC_REGULAR,444\n"  # 444 has both ST_GAS and CC -> qualifies
        )
        outages = tmp / "outages.csv"
        outages.write_text(
            "oris_code,plant_name,unit,outage_start,outage_stop,duration_hours\n"
            # 111 (coal): 14-day span -> qualifies.
            "111,Coaly,1,2023-01-01 00:00:00,2023-01-15 00:00:00,42\n"
            # 111 (coal): 4-day span -> below threshold, excluded.
            "111,Coaly,1,2023-03-01 00:00:00,2023-03-05 00:00:00,90\n"
            # 222 (CC): 19-day span but tiny duration_hours -> qualifies
            # (span, not duration_hours, decides).
            "222,Ccy,1,2023-06-01 00:00:00,2023-06-20 00:00:00,50\n"
            # 333 (peaker): 19-day span but not coal/CC -> excluded.
            "333,Peaky,1,2023-02-01 00:00:00,2023-02-20 00:00:00,300\n"
            # 444 (has a CC bin): 12-day span -> qualifies.
            "444,Dualy,1,2023-08-01 00:00:00,2023-08-13 00:00:00,200\n"
            # 555 not in the bin file at all -> excluded.
            "555,Ghost,1,2023-09-01 00:00:00,2023-09-20 00:00:00,400\n"
        )
        return str(outages), str(bins)

    def test_filter_keeps_only_coal_cc_long_spans(self):
        with tempfile.TemporaryDirectory() as d:
            out_path, bins_path = self._write_inputs(Path(d))
            masks = outage_masks_for_year(
                2023, HOURS_PER_YEAR, outages_path=out_path, bins_path=bins_path
            )
        self.assertEqual(set(masks), {111, 222, 444})
        self.assertNotIn(333, masks)  # peaker excluded
        self.assertNotIn(555, masks)  # absent from bin file excluded

    def test_short_span_not_masked(self):
        with tempfile.TemporaryDirectory() as d:
            out_path, bins_path = self._write_inputs(Path(d))
            masks = outage_masks_for_year(
                2023, HOURS_PER_YEAR, outages_path=out_path, bins_path=bins_path
            )
        # 111's only masked hours are the 14-day January window; the 4-day
        # March window must not appear.
        coal = masks[111]
        self.assertEqual(int(coal.sum()), 14 * 24)
        self.assertFalse(coal[_hour_of_year(3, 2, 0)])

    def test_span_threshold_is_strict(self):
        # Exactly 240 h is excluded; 264 h (11 days) is included.
        with tempfile.TemporaryDirectory() as d:
            bins = Path(d) / "bins.csv"
            bins.write_text("Plant_Group,Plant_Code\nCOAL,10\nCOAL,11\n")
            outages = Path(d) / "outages.csv"
            outages.write_text(
                "oris_code,plant_name,unit,outage_start,outage_stop,"
                "duration_hours\n"
                "10,Edge,1,2023-01-01 00:00:00,2023-01-11 00:00:00,1\n"  # 240h
                "11,Over,1,2023-01-01 00:00:00,2023-01-12 00:00:00,1\n"  # 264h
            )
            masks = outage_masks_for_year(
                2023, HOURS_PER_YEAR,
                outages_path=str(outages), bins_path=str(bins),
            )
        self.assertNotIn(10, masks)
        self.assertIn(11, masks)
        self.assertEqual(MIN_OUTAGE_SPAN_HOURS, 240)

    def test_missing_extract_returns_empty(self):
        masks = outage_masks_for_year(
            2023, HOURS_PER_YEAR,
            outages_path="/no/such/outages.csv", bins_path=BINS_CSV,
        )
        self.assertEqual(masks, {})


class RealDataIntegrationTest(unittest.TestCase):
    """Sanity checks against the committed ERCOT extracts."""

    def test_qualifying_codes_cover_known_coal_cc_plants(self):
        codes = _qualifying_plant_codes(BINS_CSV)
        # Coleto Creek (coal), Frontera (CC), Barney M Davis (has a CC bin).
        for code in (6178, 298, 7097, 55098, 4939):
            self.assertIn(code, codes)

    def test_san_miguel_qualifies_as_plant_but_has_no_long_outage(self):
        # San Miguel (6183) is a coal plant, so it is a qualifying plant
        # code, but it has only short-span outages -> no mask in any year.
        self.assertIn(6183, _qualifying_plant_codes(BINS_CSV))
        for year in (2023, 2024, 2025):
            masks = outage_masks_for_year(
                year, HOURS_PER_YEAR,
                outages_path=OUTAGES_CSV, bins_path=BINS_CSV,
            )
            self.assertNotIn(6183, masks)

    def test_coleto_2023_outage_lands_in_winter_spring(self):
        masks = outage_masks_for_year(
            2023, HOURS_PER_YEAR,
            outages_path=OUTAGES_CSV, bins_path=BINS_CSV,
        )
        self.assertIn(6178, masks)
        coleto = masks[6178]
        # Outaged hours fall in Jan + Feb-Apr, none in the summer peak.
        self.assertTrue(coleto[_hour_of_year(1, 10, 0)])
        jun_to_sep = slice(_hour_of_year(6, 1, 0), _hour_of_year(10, 1, 0))
        self.assertFalse(coleto[jun_to_sep].any())

    def test_peaker_plant_not_in_masks(self):
        # Bacliff (60264) is a peaker present in the outage CSV but not
        # coal/CC, so it never appears in the masks.
        masks = outage_masks_for_year(
            2023, HOURS_PER_YEAR,
            outages_path=OUTAGES_CSV, bins_path=BINS_CSV,
        )
        self.assertNotIn(60264, masks)
        self.assertNotIn(60264, _qualifying_plant_codes(BINS_CSV))

    def test_qualifying_groups_are_coal_and_cc(self):
        self.assertEqual(
            QUALIFYING_PLANT_GROUPS, frozenset({"COAL", "CC_REGULAR", "CC_CHP"})
        )


if __name__ == "__main__":
    unittest.main()
