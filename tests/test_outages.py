"""Tests for the historic-outage availability overlay loader."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import CAMPD_BINS_CSV, RAW_DATA_DIR
from market_sim.data.outages import (
    MIN_OUTAGE_SPAN_HOURS,
    QUALIFYING_PLANT_GROUPS,
    _hour_of_year,
    _MONTH_OF_HOUR,
    _plant_cems_envelope,
    _qualifying_plant_codes,
    outage_hour_mask,
    outage_masks_for_year,
    unit_outage_derate_factors,
)

# Repository root (tests/ lives at the repo root).
REPO = Path(__file__).parents[1]
BINS_CSV = str(CAMPD_BINS_CSV)
OUTAGES_CSV = str(RAW_DATA_DIR / "ercot-outages.csv")


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
        self.assertEqual(int(m24.sum()), HOURS_PER_YEAR - _hour_of_year(12, 16, 9))
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
            # 111 (coal): 1-day span (24h) -> below the 48h threshold, excluded.
            "111,Coaly,1,2023-03-01 00:00:00,2023-03-02 00:00:00,90\n"
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
        # 111's only masked hours are the 14-day January window; the 1-day
        # March window (below the 48h threshold) must not appear.
        coal = masks[111]
        self.assertEqual(int(coal.sum()), 14 * 24)
        self.assertFalse(coal[_hour_of_year(3, 2, 0)])

    def test_span_threshold_is_strict(self):
        # 47 h (just under the 48h threshold) is excluded; 48 h (= threshold)
        # is included (the filter drops spans strictly shorter than the
        # threshold).
        with tempfile.TemporaryDirectory() as d:
            bins = Path(d) / "bins.csv"
            bins.write_text("Plant_Group,Plant_Code\nCOAL,10\nCOAL,11\n")
            outages = Path(d) / "outages.csv"
            outages.write_text(
                "oris_code,plant_name,unit,outage_start,outage_stop,"
                "duration_hours\n"
                "10,Edge,1,2023-01-01 00:00:00,2023-01-02 23:00:00,1\n"  # 47h
                "11,Over,1,2023-01-01 00:00:00,2023-01-03 00:00:00,1\n"  # 48h
            )
            masks = outage_masks_for_year(
                2023,
                HOURS_PER_YEAR,
                outages_path=str(outages),
                bins_path=str(bins),
            )
        self.assertNotIn(10, masks)
        self.assertIn(11, masks)
        self.assertEqual(MIN_OUTAGE_SPAN_HOURS, 48)

    def test_missing_extract_returns_empty(self):
        masks = outage_masks_for_year(
            2023,
            HOURS_PER_YEAR,
            outages_path="/no/such/outages.csv",
            bins_path=BINS_CSV,
        )
        self.assertEqual(masks, {})


class RealDataIntegrationTest(unittest.TestCase):
    """Sanity checks against the committed ERCOT extracts."""

    def test_qualifying_codes_cover_known_coal_cc_plants(self):
        codes = _qualifying_plant_codes(BINS_CSV)
        # Coleto Creek (coal), Frontera (CC), Barney M Davis (has a CC bin).
        for code in (6178, 298, 7097, 55098, 4939):
            self.assertIn(code, codes)

    def test_san_miguel_qualifies_and_has_outage(self):
        # San Miguel (6183) is a coal plant (qualifying code) with a >= 2-day
        # window in the legacy ERCOT extract for 2023 and 2024, so it is masked
        # those years. (The sparse legacy extract has no qualifying 2025 entry.)
        self.assertIn(6183, _qualifying_plant_codes(BINS_CSV))
        for year in (2023, 2024):
            masks = outage_masks_for_year(
                year,
                HOURS_PER_YEAR,
                outages_path=OUTAGES_CSV,
                bins_path=BINS_CSV,
            )
            self.assertIn(6183, masks)
            self.assertGreaterEqual(int(masks[6183].sum()), MIN_OUTAGE_SPAN_HOURS)

    def test_coleto_2023_outage_lands_in_winter_spring(self):
        masks = outage_masks_for_year(
            2023,
            HOURS_PER_YEAR,
            outages_path=OUTAGES_CSV,
            bins_path=BINS_CSV,
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
            2023,
            HOURS_PER_YEAR,
            outages_path=OUTAGES_CSV,
            bins_path=BINS_CSV,
        )
        self.assertNotIn(60264, masks)
        self.assertNotIn(60264, _qualifying_plant_codes(BINS_CSV))

    def test_qualifying_groups_are_coal_cc_and_steam(self):
        # Coal, combined cycle (regular + CHP), gas steam (+ CHP) and CT_CHP
        # carry the historic overlay; CT_PEAKER does not (no overlay coverage).
        self.assertEqual(
            QUALIFYING_PLANT_GROUPS,
            frozenset({"COAL", "CC_REGULAR", "CC_CHP", "CT_CHP", "ST_GAS", "ST_CHP"}),
        )
        self.assertNotIn("CT_PEAKER", QUALIFYING_PLANT_GROUPS)


class NEISOUnitOutageSmokeTest(unittest.TestCase):
    """Smoke tests for the NEISO unit-outage overlay (P1 verification).

    NEISO's CAMPD unit-level coverage: CT/MA/ME/RI/VT for 2023+2024+2025;
    NH for 2023+2024 only (NH_2025 unit-level parquet not yet uploaded —
    NH 2025 falls back to the statistical availability model).

    The fossil fleet is primarily gas CC/CHP and oil steam (ST_GAS); the one
    genuine coal facility is Merrimack Station (2364, NH), whose units 1+2
    burn coal and use the averaged real-run rule.  The event-based rule fires
    for all load-following CC/ST units.  CT_CHP windows are recorded in the
    CSV but excluded from the derate overlay (_generic_unit_outage_target
    returns None for combustion turbines), matching the ERCOT convention.
    """

    NEISO_CSV: Path = RAW_DATA_DIR / "campd-unit-outages-NEISO.csv"

    def _df(self) -> pd.DataFrame:
        return pd.read_csv(self.NEISO_CSV)

    def test_neiso_unit_outage_csv_exists(self):
        self.assertTrue(
            self.NEISO_CSV.exists(),
            f"NEISO unit-outage CSV missing: {self.NEISO_CSV}",
        )

    def test_csv_covers_all_three_years(self):
        df = self._df()
        years_present = set(df["outage_start"].str[:4].unique())
        for yr in ("2023", "2024", "2025"):
            self.assertIn(yr, years_present, f"Year {yr} absent from NEISO CSV")

    def test_merrimack_present_every_year(self):
        # The NH_2025 unit-level extract has since landed, so every backcast year
        # is broadly covered AND Merrimack (2364, the lone NEISO coal plant, in
        # NH) appears in all three years. (This formerly asserted a 2025 NH gap;
        # the gap closed when the NH_2025 CAMPD parquet was uploaded.)
        df = self._df()
        facs = {
            yr: set(
                df[df["outage_start"].str.startswith(yr)]["facility_id"].astype(int)
            )
            for yr in ("2023", "2024", "2025")
        }
        self.assertGreater(
            min(len(s) for s in facs.values()),
            20,
            "all three backcast years should be broadly covered",
        )
        self.assertIn(2364, facs["2023"], "Merrimack (NH coal) present in 2023")
        self.assertIn(2364, facs["2024"], "Merrimack (NH coal) present in 2024")
        self.assertIn(2364, facs["2025"], "Merrimack (NH coal) present in 2025")

    def test_event_based_rule_dominates_plant_group_mix(self):
        # CC_REGULAR + CC_CHP + ST_GAS + CT_CHP (all event-based) > COAL rows.
        df = self._df()
        event_based = (
            df["plant_group"].isin({"CC_REGULAR", "CC_CHP", "ST_GAS", "CT_CHP"}).sum()
        )
        coal = (df["plant_group"] == "COAL").sum()
        self.assertGreater(
            event_based, coal * 10, "event-based rows should heavily dominate"
        )

    def test_coal_target_is_merrimack_only_all_years(self):
        # Merrimack (2364, NH) is the single NEISO coal facility.
        df = self._df()
        coal = df[df["plant_group"] == "COAL"]
        self.assertFalse(coal.empty, "Merrimack coal rows must be present")
        self.assertEqual(
            set(coal["facility_id"].unique()),
            {2364},
            "COAL group must be exclusively Merrimack (2364)",
        )
        # Coal rows span the three backcast years plus 2022 — the NEISO
        # calibration-complete marker (2026-07-07) authorized the one-shot
        # holdout intake, which appended the 2022 windows (rule 22).
        coal_years = set(coal["outage_start"].str[:4].unique())
        self.assertEqual(
            coal_years,
            {"2022", "2023", "2024", "2025"},
            "COAL rows expected in every backcast + holdout-validation year",
        )

    def test_kleen_energy_cc_windows_detected(self):
        # Kleen Energy (56798, Southington CT) is a CC_REGULAR plant with
        # multiple sustained outage windows across all three years.
        df = self._df()
        kleen = df[(df["facility_id"] == 56798) & (df["plant_group"] == "CC_REGULAR")]
        self.assertFalse(kleen.empty, "Kleen Energy CC windows must be in CSV")
        for yr in ("2023", "2024", "2025"):
            self.assertTrue(
                kleen["outage_start"].str.startswith(yr).any(),
                f"Kleen Energy missing {yr} windows",
            )

    def test_bridgeport_harbor_cc_windows_detected(self):
        # Bridgeport Harbor (568, CT) is a single-unit CC; outage windows
        # appear in every backcast year.
        df = self._df()
        bh = df[(df["facility_id"] == 568) & (df["plant_group"] == "CC_REGULAR")]
        self.assertFalse(bh.empty, "Bridgeport Harbor CC windows must be in CSV")

    def test_derate_factors_load_for_2023_and_2024(self):
        # unit_outage_derate_factors must return a non-empty dict for
        # 2023 and 2024 with valid (0,1]-bounded availability arrays.
        for year in (2023, 2024):
            factors = unit_outage_derate_factors(year, iso="NEISO")
            self.assertGreater(
                len(factors),
                0,
                f"NEISO derate factors empty for {year}",
            )
            for key, arr in factors.items():
                self.assertEqual(arr.shape, (HOURS_PER_YEAR,))
                self.assertTrue(
                    np.all((arr >= 0.0) & (arr <= 1.0)),
                    f"Derate array out of [0,1] for {key} in {year}",
                )

    def test_derate_factors_load_for_2025(self):
        # 2025 coverage is now complete for every NEISO state including NH, so the
        # derate factors load and are non-empty (Merrimack coal is present —
        # see test_merrimack_coal_in_derate_all_years).
        factors = unit_outage_derate_factors(2025, iso="NEISO")
        self.assertGreater(
            len(factors), 0, "NEISO 2025 derate factors must be non-empty"
        )

    def test_merrimack_coal_in_derate_all_years(self):
        # Merrimack coal (2364) is in the derate for all three years now that the
        # NH_2025 unit-level parquet has landed.
        key = (2364, "COAL")
        self.assertIn(key, unit_outage_derate_factors(2023, iso="NEISO"))
        self.assertIn(key, unit_outage_derate_factors(2024, iso="NEISO"))
        self.assertIn(key, unit_outage_derate_factors(2025, iso="NEISO"))

    def test_kleen_energy_in_derate_all_years(self):
        key = (56798, "CC_REGULAR")
        for year in (2023, 2024, 2025):
            self.assertIn(
                key,
                unit_outage_derate_factors(year, iso="NEISO"),
                f"Kleen Energy missing from derate factors {year}",
            )

    def test_within_window_retiree_capped_by_observed_outages(self):
        # Mystic (1588) is a within-window plant exit injected into the backcast
        # fleet; it ran ~16% of hours on fuel-security dispatch, so its observed
        # CEMS outage windows must derate (1588, CC_REGULAR) to a low
        # availability ceiling — else the LP runs the ~1.4 GW CC as baseload.
        # Present 2023/2024 (operated then), absent 2025 (retired mid-2024).
        key = (1588, "CC_REGULAR")
        for year in (2023, 2024):
            factors = unit_outage_derate_factors(year, iso="NEISO")
            self.assertIn(
                key,
                factors,
                f"Mystic derate missing for {year} — retiree not in capacity "
                "denominator or outage windows not derived",
            )
            self.assertLess(
                float(factors[key].mean()),
                0.5,
                f"Mystic {year} availability ceiling too high — over-dispatch",
            )

    def test_derate_availability_in_bounds(self):
        # Availability arrays must be in [0, 1] — no negative values or > 1.
        # All-zero availability is valid (e.g. Stony Brook 6081 whose 5-unit
        # CAMPD total of 507 MW exceeds the 209 MW fleet entry for the
        # CC_REGULAR bin, so concurrent unit outages clip to full derate).
        for year in (2023, 2024, 2025):
            for key, arr in unit_outage_derate_factors(year, iso="NEISO").items():
                self.assertGreaterEqual(
                    float(arr.min()), 0.0, f"Negative availability for {key} in {year}"
                )
                self.assertLessEqual(
                    float(arr.max()), 1.0, f"Availability > 1 for {key} in {year}"
                )

    def test_coal_in_neiso_for_2025(self):
        # The NH_2025 unit-level parquet has landed, so Merrimack's COAL derate
        # entry is now present in 2025 (it formerly asserted the NH_2025 gap).
        factors_2025 = unit_outage_derate_factors(2025, iso="NEISO")
        coal_keys = [k for k in factors_2025 if k[1] == "COAL"]
        self.assertEqual(
            coal_keys, [(2364, "COAL")], "Merrimack COAL derate expected for NEISO 2025"
        )

    def test_other_iso_unit_outage_csvs_untouched(self):
        # The NEISO P1 work must not alter ERCOT, PJM, or CAISO unit-outage CSVs.
        raw = RAW_DATA_DIR
        for iso in ("CAISO", "PJM"):
            path = raw / f"campd-unit-outages-{iso}.csv"
            self.assertTrue(path.exists(), f"{iso} unit-outage CSV must still exist")
        # ERCOT uses the canonical name.
        ercot_path = raw / "campd-unit-outages.csv"
        self.assertTrue(ercot_path.exists(), "ERCOT unit-outage CSV must still exist")


class NEISOFloorOutageExemptTest(unittest.TestCase):
    """The NEISO temperature-reliability-floor outage exemption (CLAUDE.md #11).

    The CAMPD unit-outage overlay's "sustained CF < 5%" detector, built for
    baseload coal/CC, misreads the lone Merrimack-class COAL unit's economic
    idleness (a sub-10% annual-CF winter peaker) as a forced outage, and its
    ``unit_capacity_mw / plant_capacity_mw`` derate is taken against the 108 MW
    model bin while the CSV unit capacities are the real ~460 MW plant — so a
    single coal-unit "outage" over-derates the bin to ZERO (Merrimack
    availability was 0 of 8760 h in 2024), structurally capping the temperature
    floor's ``frac × available`` at ~0. ``neiso_floor_outage_exempt`` (default
    ON) skips the unit-outage overlay for the floor classes so the floor — whose
    coefficients are regressed from each unit's own measured CF, already netting
    out real downtime — governs their availability, mirroring
    ``ct_mustrun_per_plant``'s WEFOR/planned-outage exemption.
    """

    def _merrimack_avail(self, *, floor: bool, year: int = 2024):
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import (
            generators_to_fleet_arrays,
            load_fleet_from_csv,
        )

        iso_config = get_iso_config("NEISO")
        zones = [z.name for z in iso_config.zones]
        gens = load_fleet_from_csv("NEISO", iso_config, year=year)
        cfg = ScenarioConfig(
            mode="backcast",
            weather_year=year,
            outage_source="historic",
            reliability_floor=floor,
        )
        fa = generators_to_fleet_arrays(
            gens, zones, hours=HOURS_PER_YEAR, iso="NEISO", config=cfg, year=year
        )
        groups = np.asarray(fa.plant_group)
        codes = np.asarray(fa.plant_code)
        rows = np.flatnonzero((codes == 2364) & (groups == "COAL"))
        self.assertGreater(rows.size, 0, "Merrimack COAL tranche must exist")
        return fa.availability[rows].mean(axis=0)

    def test_exemption_restores_merrimack_availability_2024(self):
        # With the reliability floor ON, the NEISO floor-class outage exemption
        # fires and Merrimack is available year-round (the floor governs it). With
        # the floor OFF (the no-fix baseline) the unit-outage overlay zeros it for
        # all of 2024.
        avail_fixed = self._merrimack_avail(floor=True)
        avail_bug = self._merrimack_avail(floor=False)
        self.assertEqual(
            int((avail_bug > 1e-6).sum()),
            0,
            "no-fix baseline: 2024 Merrimack availability is zeroed by the overlay",
        )
        self.assertEqual(
            int((avail_fixed > 1e-6).sum()),
            HOURS_PER_YEAR,
            "exemption: 2024 Merrimack availability restored every hour",
        )


class RetireeCemsEnvelopeTest(unittest.TestCase):
    """The within-window retiree measured-availability cap (CEMS envelope)."""

    def _write_extract(self, d: Path, rows: list[dict]) -> None:
        pd.DataFrame(rows).to_parquet(d / "ZZ_2023.parquet")

    def test_monthly_peak_envelope_clips_to_one_and_zeros_idle_months(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            # Unit ran near nameplate (100 MW) in Jan, half in Feb, idle after.
            rows = []
            for h in range(24):
                rows.append(
                    {
                        "facilityId": "999",
                        "date": "2023-01-15",
                        "hour": h,
                        "grossLoad": 100.0,
                    }
                )
                rows.append(
                    {
                        "facilityId": "999",
                        "date": "2023-02-15",
                        "hour": h,
                        "grossLoad": 50.0,
                    }
                )
            self._write_extract(d, rows)
            import market_sim.data.outages as O

            orig = O.CAMPD_UNIT_LEVEL_DIR
            try:
                O.CAMPD_UNIT_LEVEL_DIR = d
                cap = O._plant_cems_envelope("ZZ", 2023, 999, 100.0, HOURS_PER_YEAR)
            finally:
                O.CAMPD_UNIT_LEVEL_DIR = orig
            self.assertIsNotNone(cap)
            jan = cap[_MONTH_OF_HOUR == 1]
            feb = cap[_MONTH_OF_HOUR == 2]
            mar = cap[_MONTH_OF_HOUR == 3]
            self.assertAlmostEqual(float(jan.max()), 1.0, places=3)  # clipped
            self.assertAlmostEqual(float(feb.max()), 0.5, places=3)
            self.assertEqual(float(mar.max()), 0.0)  # idle -> zero

    def test_absent_plant_with_extract_caps_to_zero(self):
        # A within-window retiree absent from an extract that EXISTS did not run
        # -> capped to zero (not skipped), overriding a collapsed planned date.
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            self._write_extract(
                d,
                [
                    {
                        "facilityId": "111",
                        "date": "2023-01-01",
                        "hour": 0,
                        "grossLoad": 10.0,
                    }
                ],
            )
            import market_sim.data.outages as O

            orig = O.CAMPD_UNIT_LEVEL_DIR
            try:
                O.CAMPD_UNIT_LEVEL_DIR = d
                cap = O._plant_cems_envelope("ZZ", 2023, 999, 100.0, HOURS_PER_YEAR)
            finally:
                O.CAMPD_UNIT_LEVEL_DIR = orig
            self.assertIsNotNone(cap)
            self.assertTrue((cap == 0.0).all())

    def test_missing_extract_returns_none(self):
        # No state extract at all -> data gap, no cap (COD aging stands).
        cap = _plant_cems_envelope("ZZ", 1999, 999, 100.0, HOURS_PER_YEAR)
        self.assertIsNone(cap)


if __name__ == "__main__":
    unittest.main()
