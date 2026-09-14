"""Tests for the historic-outage availability overlay loader."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.outages import (
    QUALIFYING_PLANT_GROUPS,
    _hour_of_year,
    _MONTH_OF_HOUR,
    _plant_cems_envelope,
    outage_hour_mask,
    unit_outage_derate_factors,
)
from tests.helpers import REPO_ROOT

# Repository root (tests/ lives at the repo root).
REPO = REPO_ROOT


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


class QualifyingPlantGroupsTest(unittest.TestCase):
    """The set of plant groups whose CAMPD outages are derived."""

    def test_qualifying_groups_are_coal_cc_and_steam(self):
        # Coal, combined cycle (regular + CHP), gas steam (+ CHP) and CT_CHP are
        # the groups the unit-outage detector derives; CT_PEAKER is not (CTs
        # dispatch economically and carry no derate).
        self.assertEqual(
            QUALIFYING_PLANT_GROUPS,
            frozenset({"COAL", "CC_REGULAR", "CC_CHP", "CT_CHP", "ST_GAS", "ST_CHP"}),
        )
        self.assertNotIn("CT_PEAKER", QUALIFYING_PLANT_GROUPS)


class SingleUnitPlantFullyZeroedTest(unittest.TestCase):
    """The per-unit derate — now the SOLE CAMPD outage layer — fully zeros a
    genuinely single-unit plant (the unit's capacity equals its plant-bin
    capacity, so the removed share is 1.0), replacing what the removed
    facility-summed overlay used to do for a whole-plant CEMS dropout.
    """

    def _factors(self, unit_csv: Path, cap: dict, year: int):
        from unittest.mock import patch

        from market_sim.data import outages

        outages.unit_outage_derate_factors.cache_clear()
        with (
            patch.object(outages, "unit_outage_csv_for_iso", return_value=unit_csv),
            patch.object(outages, "_iso_plant_capacity", return_value=cap),
        ):
            return outages.unit_outage_derate_factors(year, HOURS_PER_YEAR, iso="MISO")

    def test_single_unit_plant_fully_zeroed_in_window(self):
        with tempfile.TemporaryDirectory() as td:
            unit = Path(td) / "campd-unit-outages-MISO.csv"
            pd.DataFrame(
                [
                    {
                        "facility_name": "Solo Coal",
                        "facility_id": 70001,
                        "unit_id": "1",
                        # unit capacity == the plant-bin capacity -> pct 100%.
                        "unit_capacity_mw": 500.0,
                        "plant_capacity_mw": 500.0,
                        "unit_pct_of_plant": 100.0,
                        "plant_group": "COAL",
                        "capacity_source": "eia_exact",
                        "outage_start": "2023-06-01",
                        "outage_end": "2023-06-20",  # 20 days >= 5-day floor
                        "duration_days": 20.0,
                        "peer_units_online": 0,
                        "total_units_at_plant": 1,
                    }
                ]
            ).to_csv(unit, index=False)
            factors = self._factors(unit, {(70001, "COAL"): 500.0}, 2023)
        key = (70001, "COAL")
        self.assertIn(key, factors)
        arr = factors[key]
        self.assertEqual(arr.shape, (HOURS_PER_YEAR,))
        # Availability is zeroed for every hour inside the outage window...
        self.assertEqual(arr[_hour_of_year(6, 10, 0)], 0.0)
        # ...and full outside it.
        self.assertEqual(arr[0], 1.0)
        self.assertEqual(arr[_hour_of_year(12, 31, 23)], 1.0)


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
        # Merrimack (2364, NH) is the single NEISO coal facility ACROSS THE
        # BACKCAST YEARS. The owner-authorized 2018-2026 backfill (59f8bc30,
        # 2026-07-24) legitimately added Bridgeport Harbor 3 (568, CT coal,
        # retired 2021-06) windows for 2018-2021, so the exclusivity claim is
        # scoped to 2022+ where it remains a fleet fact.
        df = self._df()
        coal = df[
            (df["plant_group"] == "COAL") & (df["outage_start"].str[:4] >= "2022")
        ]
        self.assertFalse(coal.empty, "Merrimack coal rows must be present")
        self.assertEqual(
            set(coal["facility_id"].unique()),
            {2364},
            "COAL group must be exclusively Merrimack (2364) in 2022+",
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


class ErcotNuclearUnitAvailabilityTest(unittest.TestCase):
    """The window-grain nuclear refuel series (60-Day DAM disclosure CSV)."""

    def test_committed_series_shape_and_windows(self):
        from market_sim.data.outages import ercot_nuclear_unit_availability_series

        s = ercot_nuclear_unit_availability_series(2024)
        # All four reactors present: CP 6145 units 1/2, STP 6251 units 1/2.
        self.assertEqual(set(s), {(6145, 1), (6145, 2), (6251, 1), (6251, 2)})
        stp2 = s[(6251, 2)]
        self.assertEqual(stp2.shape, (HOURS_PER_YEAR,))
        # STP-2 refuel 2024-03-23 -> 2024-05-19: OUT on the May-8 scarcity
        # event, back for the May-24..27 record heat.
        may8_he18 = _hour_of_year(5, 8, 17)
        self.assertEqual(stp2[may8_he18], 0.0)
        may27_he18 = _hour_of_year(5, 27, 17)
        self.assertGreater(stp2[may27_he18], 0.9)
        # Bounded in [0, 1] wherever covered; NaN only on uncovered dates
        # (2024 is fully covered -> no NaN at all).
        finite = np.isfinite(stp2)
        self.assertTrue(finite.all())
        self.assertTrue((stp2[finite] >= 0.0).all())
        self.assertTrue((stp2[finite] <= 1.0).all())

    def test_uncovered_dates_are_nan(self):
        from market_sim.data.outages import ercot_nuclear_unit_availability_series

        s = ercot_nuclear_unit_availability_series(2025)
        cp1 = s[(6145, 1)]
        # Nov-Dec 2025 deliveries publish in the 2026 disclosure files (not
        # yet on disk), so those dates are NaN -> the caller keeps the
        # monthly-CF smear there.
        dec15 = _hour_of_year(12, 15, 12)
        self.assertTrue(np.isnan(cp1[dec15]))
        # Spring 2025 is covered: CP-1 refuel 2025-04-21 -> 2025-05-14.
        may1 = _hour_of_year(5, 1, 12)
        self.assertEqual(cp1[may1], 0.0)

    def test_fleet_application_gated_and_min_gen_tracks(self):
        """Flag off -> smear untouched; flag on -> windows land, floor follows."""
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays

        def nuke(unit_no: int, code: int, mw: float) -> Generator:
            return Generator(
                unit_id=f"{code}_{unit_no}",
                name=f"nuke {code}_{unit_no}",
                zone="Houston" if code == 6251 else "North",
                fuel_type="nuclear",
                pmax_mw=mw,
                pmin_mw=0.0,
                heat_rate=10.4,
                vom=2.0,
                emission_rate_co2=0.0,
                nox_rate=0.0,
                eford=0.03,
                online_year=1989,
                plant_code=code,
            )

        gens = [nuke(1, 6251, 1300.0), nuke(2, 6251, 1280.0)]
        zones = ["Houston", "North"]
        base_cfg = dict(weather_year=2024, iso="ERCOT", mode="backcast")
        cfg_off = ScenarioConfig(**base_cfg)
        cfg_on = ScenarioConfig(**base_cfg, ercot_nuclear_unit_availability=True)
        fa_off = generators_to_fleet_arrays(
            gens, zones, hours=HOURS_PER_YEAR, iso="ERCOT", config=cfg_off, year=2024
        )
        fa_on = generators_to_fleet_arrays(
            gens, zones, hours=HOURS_PER_YEAR, iso="ERCOT", config=cfg_on, year=2024
        )
        h = _hour_of_year(5, 8, 17)  # May 8 HE18, STP-2 out in reality
        # Flag off: the 2024 May smear (0.78) for both units.
        self.assertAlmostEqual(fa_off.availability[1, h], 0.78, places=2)
        # Flag on: STP-2 (row 1) zeroed on the event day, STP-1 (row 0) near 1.
        self.assertEqual(fa_on.availability[1, h], 0.0)
        self.assertGreater(fa_on.availability[0, h], 0.9)
        # Nuclear flat must-run floor tracks the overlaid availability.
        self.assertAlmostEqual(
            float(fa_on.min_gen[1, h]),
            float(fa_on.availability[1, h] * 1280.0),
            places=3,
        )
        self.assertAlmostEqual(
            float(fa_on.min_gen[0, h]),
            float(fa_on.availability[0, h] * 1300.0),
            places=3,
        )


class NuclearUnitAvailabilityTest(unittest.TestCase):
    """The ISO-generic per-reactor daily nuclear series (NRC status CSV)."""

    def test_committed_pjm_series_shape_windows_and_wedge_months(self):
        from market_sim.data.outages import nuclear_unit_availability_series

        s = nuclear_unit_availability_series("PJM", 2024)
        # All 31 active PJM reactors present (dormant Crane 8011 absent).
        self.assertEqual(len(s), 31)
        self.assertIn((6103, 1), s)
        self.assertNotIn((8011, 1), s)
        d3 = s[(869, 3)]
        self.assertEqual(d3.shape, (HOURS_PER_YEAR,))
        # Dresden 3 full-unit stop 2024-08-24..27 (NRC 0 % power) in a
        # covered month -> 0.0; two days later it is back near rating.
        self.assertEqual(d3[_hour_of_year(8, 25, 12)], 0.0)
        self.assertGreater(d3[_hour_of_year(8, 31, 12)], 0.9)
        # 2024-11 is a wedge-dropped month (NRC thermal-% cannot express the
        # 923 net anchor) -> NaN, the monthly smear stands there.
        self.assertTrue(np.isnan(d3[_hour_of_year(11, 15, 12)]))
        # Covered values bounded in [0, 1].
        finite = np.isfinite(d3)
        self.assertTrue((d3[finite] >= 0.0).all())
        self.assertTrue((d3[finite] <= 1.0).all())

    def test_unknown_iso_degrades_to_empty(self):
        """No extract -> {}, so the caller keeps its monthly smear.

        Asserted against a synthetic ISO name rather than a real one: the
        derived extracts (``nuclear-availability-<ISO>.csv``) are an
        intake-by-intake growing set — CAISO, NEISO, NYISO and PJM all carry
        one now — so pinning this contract to whichever ISO happens to be
        uncovered today re-breaks the moment that ISO's extract lands (which
        is exactly what happened when NEISO's did). A name no intake will ever
        produce tests the degradation path itself.
        """
        from market_sim.data.outages import nuclear_unit_availability_series

        self.assertEqual(nuclear_unit_availability_series("NO_SUCH_ISO", 2024), {})

    def test_covered_iso_without_rows_for_the_year_degrades_to_empty(self):
        """The second empty-dict leg: extract present, no rows for ``year``."""
        from market_sim.data.outages import nuclear_unit_availability_series

        # NEISO has an extract (Millstone 2 & 3, Seabrook) but its coverage
        # window does not reach 1990 — the year filter empties the frame.
        self.assertTrue(nuclear_unit_availability_series("NEISO", 2024))
        self.assertEqual(nuclear_unit_availability_series("NEISO", 1990), {})

    def test_fleet_application_gated_pjm_scoped_and_min_gen_tracks(self):
        """Flag off -> smear untouched; flag on -> windows land, floor follows,
        wedge-dropped months keep the smear."""
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays

        def nuke(unit_no: int, code: int, mw: float) -> Generator:
            return Generator(
                unit_id=f"{code}_{unit_no}",
                name=f"nuke {code}_{unit_no}",
                zone="PJM_ComEd",
                fuel_type="nuclear",
                pmax_mw=mw,
                pmin_mw=0.0,
                heat_rate=10.4,
                vom=2.0,
                emission_rate_co2=0.0,
                nox_rate=0.0,
                eford=0.03,
                online_year=1971,
                plant_code=code,
            )

        gens = [nuke(2, 869, 902.0), nuke(3, 869, 895.0)]
        zones = ["PJM_ComEd"]
        base_cfg = dict(weather_year=2024, iso="PJM", mode="backcast")
        cfg_off = ScenarioConfig(**base_cfg)
        cfg_on = ScenarioConfig(**base_cfg, nuclear_unit_availability=True)
        fa_off = generators_to_fleet_arrays(
            gens, zones, hours=HOURS_PER_YEAR, iso="PJM", config=cfg_off, year=2024
        )
        fa_on = generators_to_fleet_arrays(
            gens, zones, hours=HOURS_PER_YEAR, iso="PJM", config=cfg_on, year=2024
        )
        h = _hour_of_year(8, 25, 12)  # Dresden 3 full stop, covered month
        # Flag off: the 2024 Aug smear (0.99) for both units.
        self.assertAlmostEqual(fa_off.availability[1, h], 0.99, places=2)
        self.assertAlmostEqual(fa_off.availability[0, h], 0.99, places=2)
        # Flag on: Dresden 3 (row 1) zeroed on the event day, Dresden 2 near 1.
        self.assertEqual(fa_on.availability[1, h], 0.0)
        self.assertGreater(fa_on.availability[0, h], 0.9)
        # Wedge-dropped month (2024-11): both keep the smear (0.93).
        hw = _hour_of_year(11, 15, 12)
        self.assertAlmostEqual(fa_on.availability[1, hw], 0.93, places=2)
        self.assertAlmostEqual(
            fa_on.availability[1, hw], fa_off.availability[1, hw], places=6
        )
        # Nuclear flat must-run floor tracks the overlaid availability.
        self.assertAlmostEqual(
            float(fa_on.min_gen[1, h]),
            float(fa_on.availability[1, h] * 895.0),
            places=3,
        )
        self.assertAlmostEqual(
            float(fa_on.min_gen[0, h]),
            float(fa_on.availability[0, h] * 902.0),
            places=3,
        )

    def test_committed_nyiso_series_covers_every_reactor_and_month(self):
        """NYISO leg (nyiso-98): four reactors, no wedge-dropped month."""
        from market_sim.data.outages import nuclear_unit_availability_series

        for year in (2023, 2024, 2025):
            s = nuclear_unit_availability_series("NYISO", year)
            # FitzPatrick, Ginna, Nine Mile Point 1 + 2. Indian Point 2/3
            # retired 2020/2021 and carry no NRC rows.
            self.assertEqual(sorted(s), [(2589, 1), (2589, 2), (6110, 1), (6122, 1)])
            for key, arr in s.items():
                self.assertEqual(arr.shape, (HOURS_PER_YEAR,), msg=f"{year} {key}")
                # Every NYISO month reconciles inside WEDGE_TOL, so unlike PJM
                # no month is dropped and the series is finite throughout.
                self.assertFalse(np.isnan(arr).any(), msg=f"{year} {key}")
                self.assertTrue(((arr >= 0.0) & (arr <= 1.0)).all())
        # Nine Mile Point 1's measured 2023-03-13..04-19 refuel outage: the
        # fleet-month smear cannot see it (Mar/Apr CF 0.86/0.74 spread over
        # all four units), the overlay zeroes the unit that is actually out.
        nmp1 = nuclear_unit_availability_series("NYISO", 2023)[(2589, 1)]
        self.assertEqual(nmp1[_hour_of_year(3, 20, 12)], 0.0)
        self.assertGreater(nmp1[_hour_of_year(5, 15, 12)], 0.9)
        # 2025 refuel window on the same unit, 2025-03-17..04-04.
        self.assertEqual(
            nuclear_unit_availability_series("NYISO", 2025)[(2589, 1)][
                _hour_of_year(3, 25, 12)
            ],
            0.0,
        )

    def test_nyiso_fleet_application_replaces_the_smear(self):
        """Flag on -> the out unit is zeroed and only it; flag off -> smear."""
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays

        def nuke(unit_no: int, code: int, mw: float) -> Generator:
            return Generator(
                unit_id=f"{code}_{unit_no}",
                name=f"nuke {code}_{unit_no}",
                zone="Upstate_West",
                fuel_type="nuclear",
                pmax_mw=mw,
                pmin_mw=0.0,
                heat_rate=10.4,
                vom=2.0,
                emission_rate_co2=0.0,
                nox_rate=0.0,
                eford=0.03,
                online_year=1969,
                plant_code=code,
            )

        gens = [nuke(1, 2589, 619.7), nuke(1, 6110, 844.0)]
        base = dict(weather_year=2023, iso="NYISO", mode="backcast")
        fa_off, fa_on = (
            generators_to_fleet_arrays(
                gens,
                ["Upstate_West"],
                hours=HOURS_PER_YEAR,
                iso="NYISO",
                config=cfg,
                year=2023,
            )
            for cfg in (
                ScenarioConfig(**base),
                ScenarioConfig(**base, nuclear_unit_availability=True),
            )
        )
        h = _hour_of_year(3, 20, 12)  # NMP-1 out, FitzPatrick at power
        # Off: the March smear (0.86) on both units — the outage is invisible.
        self.assertAlmostEqual(fa_off.availability[0, h], 0.86, places=2)
        self.assertAlmostEqual(fa_off.availability[1, h], 0.86, places=2)
        # On: NMP-1 zeroed, FitzPatrick lifted to its measured near-full state.
        self.assertEqual(fa_on.availability[0, h], 0.0)
        self.assertGreater(fa_on.availability[1, h], 0.9)
        # The flat must-run floor follows the overlay (zero MW while out).
        self.assertEqual(float(fa_on.min_gen[0, h]), 0.0)

    def test_ercot_is_excluded_from_the_generic_flag(self):
        """ERCOT keeps its own flag/file — the generic one must not fire there."""
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays

        gen = Generator(
            unit_id="6145_1",
            name="nuke",
            zone="ERCOT_South",
            fuel_type="nuclear",
            pmax_mw=1250.0,
            pmin_mw=0.0,
            heat_rate=10.4,
            vom=2.0,
            emission_rate_co2=0.0,
            nox_rate=0.0,
            eford=0.03,
            online_year=1988,
            plant_code=6145,
        )
        base = dict(weather_year=2023, iso="ERCOT", mode="backcast")
        arrays = [
            generators_to_fleet_arrays(
                [gen],
                ["ERCOT_South"],
                hours=HOURS_PER_YEAR,
                iso="ERCOT",
                config=cfg,
                year=2023,
            )
            for cfg in (
                ScenarioConfig(**base),
                ScenarioConfig(**base, nuclear_unit_availability=True),
            )
        ]
        np.testing.assert_array_equal(arrays[0].availability, arrays[1].availability)


class NuclearUnitAvailabilityRunnerWiringTest(unittest.TestCase):
    """The flag reaches the solved config and the recorded config (nyiso-98).

    The nyiso-89 §4a defect class in its config-borne form: a calibration flag
    that is recorded in ``run_config.json`` but never applied to the
    ``ScenarioConfig`` the LP solves with makes the arm silently inert — it
    fails as "the mechanism is byte-identical to its control", not as a crash.
    ``nuclear_unit_availability`` travels on the config (not as a
    ``load_fleet_from_csv`` argument), so the seams to pin are the runner's
    ``with_overrides`` and the full runner's kwarg forwarding.
    """

    def test_run_calibration_applies_the_override(self) -> None:
        import ast

        tree = ast.parse(Path("scripts/run_calibration.py").read_text())
        applied = any(
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "with_overrides"
            and any(k.arg == "nuclear_unit_availability" for k in n.keywords)
            for n in ast.walk(tree)
        )
        self.assertTrue(
            applied,
            "run_calibration.py::run_year never applies "
            "with_overrides(nuclear_unit_availability=...), so the flag would "
            "be recorded but not solved",
        )

    def test_run_calibration_full_forwards_and_records(self) -> None:
        src = Path("scripts/run_calibration_full.py").read_text()
        for needle, why in (
            ("--nuclear-unit-availability", "no CLI flag"),
            (
                "nuclear_unit_availability=args.nuclear_unit_availability",
                "argparse value never dispatched",
            ),
            (
                "nuclear_unit_availability=nuclear_unit_availability",
                "never forwarded to run_year",
            ),
            (
                '"nuclear_unit_availability": nuclear_unit_availability',
                "absent from run_config.json",
            ),
            (
                "recorded_cfg.with_overrides(nuclear_unit_availability=True)",
                "recorded_cfg does not mirror the solved config",
            ),
        ):
            self.assertIn(needle, src, why)

    def test_flag_is_registered_in_the_cache_key(self) -> None:
        """An unregistered field silently serves the control's cached results."""
        from market_sim.config.scenarios import ScenarioConfig

        base = ScenarioConfig().cache_key()
        self.assertEqual(
            base, ScenarioConfig(nuclear_unit_availability=False).cache_key()
        )
        self.assertNotEqual(
            base, ScenarioConfig(nuclear_unit_availability=True).cache_key()
        )


class ErcotThermalDamAvailabilityTest(unittest.TestCase):
    """The measured class-day thermal availability series + fleet rescale."""

    def test_committed_series_shape_and_values(self):
        from market_sim.data.outages import ercot_thermal_dam_availability_series

        s = ercot_thermal_dam_availability_series(2023)
        # ST_GAS joined the covered scope 2026-07-18 (the measured-availability
        # backcast re-architecture) and COAL 2026-07-24 (ERCOT-110) — see the
        # derive script's class-scope note. COAL is ONE class because the ERCOT
        # LP has one coal plant_group (the COAL_PRB / COAL_LIGNITE split is
        # reporting-only). The loader is scope-blind: the
        # ercot_thermal_dam_availability_coal gate drops COAL at the APPLY
        # seam, not here.
        self.assertEqual(set(s), {"CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL"})
        cc = s["CC_REGULAR"]
        self.assertEqual(cc.shape, (HOURS_PER_YEAR,))
        # Jun 14 2023 (a June over-formation day): measured CC fraction ~0.828
        # — well above the model's statistical ~0.76 the forensics measured.
        # (Re-pinned 0.834 -> 0.828 at the ercot-191 ruling-#9 train-grain
        # re-derive, signature A1 — a committed-artifact re-pin, not tuning.)
        jun14 = _hour_of_year(6, 14, 19)
        self.assertAlmostEqual(cc[jun14], 0.828, places=2)
        # Oct-2023 disclosure publication hole -> NaN (statistical kept).
        oct15 = _hour_of_year(10, 15, 12)
        self.assertTrue(np.isnan(cc[oct15]))
        finite = np.isfinite(cc)
        self.assertTrue((cc[finite] >= 0.0).all())
        self.assertTrue((cc[finite] <= 1.0).all())

    def test_fleet_application_rescales_class_day_mean(self):
        """Flag on -> covered class-day mean equals the measured fraction;
        zeroed tranches stay zero; uncovered days and forecast mode no-op."""
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays

        def cc(i: int, mw: float) -> Generator:
            return Generator(
                unit_id=f"55555_{i}",
                name=f"cc {i}",
                zone="Houston",
                fuel_type="gas_cc",
                pmax_mw=mw,
                pmin_mw=0.0,
                heat_rate=7.5,
                vom=2.0,
                emission_rate_co2=0.4,
                nox_rate=0.0,
                eford=0.05,
                online_year=2005,
                plant_code=55555,
                is_campd_bin=True,
                plant_group="CC_REGULAR",
            )

        gens = [cc(1, 400.0), cc(2, 300.0), cc(3, 300.0)]
        zones = ["Houston"]
        base = dict(weather_year=2023, iso="ERCOT", mode="backcast")
        cfg_off = ScenarioConfig(**base)
        cfg_on = ScenarioConfig(**base, ercot_thermal_dam_availability=True)
        fa_off = generators_to_fleet_arrays(
            gens, zones, hours=HOURS_PER_YEAR, iso="ERCOT", config=cfg_off, year=2023
        )
        fa_on = generators_to_fleet_arrays(
            gens, zones, hours=HOURS_PER_YEAR, iso="ERCOT", config=cfg_on, year=2023
        )
        from market_sim.data.outages import ercot_thermal_dam_availability_series

        target = ercot_thermal_dam_availability_series(2023)["CC_REGULAR"]
        pmax = np.array([400.0, 300.0, 300.0])
        d0 = _hour_of_year(6, 14, 0)  # Jun 14, a covered day
        day = slice(d0, d0 + 24)
        got = float((fa_on.availability[:, day].mean(axis=1) * pmax).sum() / pmax.sum())
        self.assertAlmostEqual(got, float(target[d0]), places=3)
        # Flag off: the statistical availability differs from the measured.
        off = float(
            (fa_off.availability[:, day].mean(axis=1) * pmax).sum() / pmax.sum()
        )
        self.assertNotAlmostEqual(off, float(target[d0]), places=3)
        # Uncovered day (Oct-2023 hole): byte-identical to the flag-off run.
        o0 = _hour_of_year(10, 15, 0)
        np.testing.assert_array_equal(
            fa_on.availability[:, o0 : o0 + 24], fa_off.availability[:, o0 : o0 + 24]
        )
        # Forecast mode: the overlay cannot even be CONSTRUCTED there. It used
        # to be a silent no-op; since FFR-1D (audit FR-11) ScenarioConfig
        # refuses the measured DAM-award record in mode="forecast" (rule 13),
        # which is strictly stronger than asserting the no-op.
        with self.assertRaises(ValueError) as ctx:
            ScenarioConfig(
                weather_year=2023,
                iso="ERCOT",
                mode="forecast",
                ercot_thermal_dam_availability=True,
            )
        self.assertIn("backcast-only measured overlays", str(ctx.exception))

    def test_committed_hourly_series_reconciles_with_day_grain(self):
        """ERCOT-96 class-hour series: shape, day-mean reconciliation, the
        summer afternoon dip, and the Oct-2023 publication hole."""
        from market_sim.data.outages import (
            ercot_thermal_dam_availability_hourly_series,
            ercot_thermal_dam_availability_series,
        )

        s = ercot_thermal_dam_availability_hourly_series(2023)
        # Same class scope as the day grain (ERCOT-110 added COAL).
        self.assertEqual(set(s), {"CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL"})
        cc = s["CC_REGULAR"]
        self.assertEqual(cc.shape, (HOURS_PER_YEAR,))
        finite = np.isfinite(cc)
        self.assertTrue((cc[finite] >= 0.0).all())
        self.assertTrue((cc[finite] <= 1.0).all())
        # Day-mean of the hourly grain reconciles with the day file (both come
        # from the same site-hour intermediate; rounding tolerance only).
        day = ercot_thermal_dam_availability_series(2023)["CC_REGULAR"]
        d0 = _hour_of_year(6, 14, 0)
        self.assertAlmostEqual(
            float(np.nanmean(cc[d0 : d0 + 24])), float(day[d0]), places=2
        )
        # The measured afternoon ambient dip on a 2023 tail day (Aug 25):
        # hod 14 (HE 15) sits below the overnight hod 4 (HE 5) capability.
        a0 = _hour_of_year(8, 25, 0)
        self.assertLess(cc[a0 + 14], cc[a0 + 4])
        # Oct-2023 disclosure publication hole -> NaN (statistical kept).
        self.assertTrue(np.isnan(cc[_hour_of_year(10, 15, 12)]))

    def test_fleet_application_hourly_grain(self):
        """ERCOT-96 grain switch: the class-hour cap-weighted availability
        lands on the measured hourly fraction; the hourly flag alone (base
        off) is a no-op; uncovered days keep the pre-overlay stack."""
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays

        def cc(i: int, mw: float) -> Generator:
            return Generator(
                unit_id=f"55555_{i}",
                name=f"cc {i}",
                zone="Houston",
                fuel_type="gas_cc",
                pmax_mw=mw,
                pmin_mw=0.0,
                heat_rate=7.5,
                vom=2.0,
                emission_rate_co2=0.4,
                nox_rate=0.0,
                eford=0.05,
                online_year=2005,
                plant_code=55555,
                is_campd_bin=True,
                plant_group="CC_REGULAR",
            )

        gens = [cc(1, 400.0), cc(2, 300.0), cc(3, 300.0)]
        zones = ["Houston"]
        pmax = np.array([400.0, 300.0, 300.0])
        base = dict(weather_year=2023, iso="ERCOT", mode="backcast")
        cfg_day = ScenarioConfig(**base, ercot_thermal_dam_availability=True)
        cfg_hr = ScenarioConfig(
            **base,
            ercot_thermal_dam_availability=True,
            ercot_thermal_dam_availability_hourly=True,
        )
        fa_day = generators_to_fleet_arrays(
            gens, zones, hours=HOURS_PER_YEAR, iso="ERCOT", config=cfg_day, year=2023
        )
        fa_hr = generators_to_fleet_arrays(
            gens, zones, hours=HOURS_PER_YEAR, iso="ERCOT", config=cfg_hr, year=2023
        )
        from market_sim.data.outages import (
            ercot_thermal_dam_availability_hourly_series,
        )

        t_h = ercot_thermal_dam_availability_hourly_series(2023)["CC_REGULAR"]
        # Aug 25 hod 14 (HE 15) — a covered tail-day afternoon hour: the
        # cap-weighted class availability equals the measured HOURLY fraction,
        # not the day-flat one.
        h = _hour_of_year(8, 25, 14)
        got = float((fa_hr.availability[:, h] * pmax).sum() / pmax.sum())
        self.assertAlmostEqual(got, float(t_h[h]), places=3)
        day_flat = float((fa_day.availability[:, h] * pmax).sum() / pmax.sum())
        self.assertNotAlmostEqual(got, day_flat, places=3)
        # The measured intra-day SHAPE survives: afternoon below overnight.
        h4 = _hour_of_year(8, 25, 4)
        got4 = float((fa_hr.availability[:, h4] * pmax).sum() / pmax.sum())
        self.assertLess(got, got4)
        # Uncovered day (Oct-2023 hole): byte-identical to the day-grain run
        # (both fall through to the pre-overlay statistical stack there).
        o0 = _hour_of_year(10, 15, 0)
        np.testing.assert_array_equal(
            fa_hr.availability[:, o0 : o0 + 24],
            fa_day.availability[:, o0 : o0 + 24],
        )
        # Hourly flag WITHOUT the base flag: the mechanism is unarmed — the
        # whole overlay (either grain) must not apply.
        cfg_orphan = ScenarioConfig(**base, ercot_thermal_dam_availability_hourly=True)
        cfg_off = ScenarioConfig(**base)
        fa_orphan = generators_to_fleet_arrays(
            gens, zones, hours=HOURS_PER_YEAR, iso="ERCOT", config=cfg_orphan, year=2023
        )
        fa_off = generators_to_fleet_arrays(
            gens, zones, hours=HOURS_PER_YEAR, iso="ERCOT", config=cfg_off, year=2023
        )
        np.testing.assert_array_equal(fa_orphan.availability, fa_off.availability)

    def test_coal_scope_gate(self):
        """ERCOT-110 coal class-SCOPE gate: with the gate OFF the coal classes
        are untouched even though the derived artifacts now carry them (so the
        re-derive cannot move a keeper); with it ON the coal class-HOUR
        cap-weighted availability lands on the measured DAM fraction."""
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays
        from market_sim.data.outages import (
            ercot_thermal_dam_availability_hourly_series,
        )

        def coal(i: int, mw: float) -> Generator:
            # Martin Lake (6146) — a crosswalked DAM coal site
            # (MLSES_UNIT1/2/3). plant_group is the bare "COAL" the ERCOT bin
            # file assigns the whole coal fleet; the supply-rank split is
            # applied only at reporting time, so the overlay must key on COAL.
            return Generator(
                unit_id=f"6146_{i}",
                name=f"coal {i}",
                zone="Northeast",
                fuel_type="coal",
                pmax_mw=mw,
                pmin_mw=0.0,
                heat_rate=10.3,
                vom=4.0,
                emission_rate_co2=1.0,
                nox_rate=0.0,
                eford=0.07,
                online_year=1978,
                plant_code=6146,
                is_campd_bin=True,
                plant_group="COAL",
            )

        gens = [coal(1, 800.0), coal(2, 800.0), coal(3, 780.0)]
        zones = ["Northeast"]
        pmax = np.array([800.0, 800.0, 780.0])
        base = dict(
            weather_year=2023,
            iso="ERCOT",
            mode="backcast",
            ercot_thermal_dam_availability=True,
            ercot_thermal_dam_availability_hourly=True,
        )
        cfg_off = ScenarioConfig(**base)
        cfg_on = ScenarioConfig(**base, ercot_thermal_dam_availability_coal=True)
        cfg_bare = ScenarioConfig(weather_year=2023, iso="ERCOT", mode="backcast")
        kw = dict(hours=HOURS_PER_YEAR, iso="ERCOT", config=None, year=2023)
        fa_off = generators_to_fleet_arrays(gens, zones, **{**kw, "config": cfg_off})
        fa_on = generators_to_fleet_arrays(gens, zones, **{**kw, "config": cfg_on})
        fa_bare = generators_to_fleet_arrays(gens, zones, **{**kw, "config": cfg_bare})

        # Gate OFF: coal is byte-identical to the run with the whole measured
        # overlay unarmed — the gas-armed keeper is unmoved by the re-derive.
        np.testing.assert_array_equal(fa_off.availability, fa_bare.availability)

        # Gate ON: the cap-weighted class-HOUR mean equals the measured
        # fraction on a covered summer-tail hour, and it BINDS (moves off the
        # statistical stack).
        t_h = ercot_thermal_dam_availability_hourly_series(2023)["COAL"]
        h = _hour_of_year(8, 25, 14)
        got = float((fa_on.availability[:, h] * pmax).sum() / pmax.sum())
        self.assertAlmostEqual(got, float(t_h[h]), places=3)
        self.assertNotAlmostEqual(
            got, float((fa_off.availability[:, h] * pmax).sum() / pmax.sum()), places=3
        )
        # Uncovered day (Oct-2023 publication hole): the pre-overlay stack is
        # kept even with the gate armed.
        o0 = _hour_of_year(10, 15, 0)
        np.testing.assert_array_equal(
            fa_on.availability[:, o0 : o0 + 24],
            fa_off.availability[:, o0 : o0 + 24],
        )
        # Forecast mode: the statistical stack is the forward analogue (the G4
        # mode-aware seam), and since FFR-1D (audit FR-11) the measured DAM
        # record cannot be armed there at all — ScenarioConfig refuses it
        # (rule 13), which is strictly stronger than the old no-op assertion.
        with self.assertRaises(ValueError) as ctx:
            ScenarioConfig(
                weather_year=2023,
                iso="ERCOT",
                mode="forecast",
                ercot_thermal_dam_availability=True,
                ercot_thermal_dam_availability_hourly=True,
                ercot_thermal_dam_availability_coal=True,
            )
        self.assertIn("backcast-only measured overlays", str(ctx.exception))

    def test_plant_grain_preserves_class_total_and_pins_plants(self):
        """ERCOT-97 plant grain: a crosswalked plant is pinned to its own
        measured fraction and the unmapped remainder is water-filled so the
        class-HOUR cap-weighted total is UNCHANGED (a within-class
        redistribution, not a level change; zero fitted parameters)."""
        import logging

        from market_sim.data.fleet import (
            _dam_waterfill,
            _ercot_dam_plant_hourly_apply,
        )

        # Water-fill invariant: the cap-weighted mean lands on the target.
        a = np.array([[0.9, 0.5], [0.8, 0.2]])
        cap = np.array([100.0, 50.0])
        tgt = np.array([0.7, 0.9])
        new = _dam_waterfill(a, cap, tgt, np.array([True, True]))
        cw = (new * cap[:, None]).sum(axis=0) / cap.sum()
        np.testing.assert_allclose(cw, tgt, atol=1e-9)
        self.assertLessEqual(float(new.max()), 1.0)

        # Redistribution: class of 1200 MW, measured class fraction 0.75 (class
        # live = 900 MW). Two mapped plants (101 @ 0.50 over 400 MW = 200;
        # 202 @ 1.00 over 300 MW = 300; mapped live = 500), one unmapped plant
        # (303, 500 MW). Residual target = (900 − 500)/500 = 0.80.
        class _G:
            def __init__(self, pc, grp, pm):
                self.plant_code = pc
                self.plant_group = grp
                self.pmax_mw = pm

        gens = [
            _G(101, "CC_REGULAR", 200.0),
            _G(101, "CC_REGULAR", 200.0),
            _G(202, "CC_REGULAR", 300.0),
            _G(303, "CC_REGULAR", 500.0),
        ]
        pmax = np.array([200.0, 200.0, 300.0, 500.0])
        avail = np.ones((4, 2))
        meas_h = {"CC_REGULAR": np.array([0.75, 0.75])}
        plant_series = {101: np.array([0.50, 0.50]), 202: np.array([1.0, 1.0])}
        done = _ercot_dam_plant_hourly_apply(
            avail, gens, pmax, 2, 2023, meas_h, plant_series, logging.getLogger("t")
        )
        self.assertEqual(done, {"CC_REGULAR"})
        # Mapped plants pinned to their measured fractions.
        cw101 = (avail[0:2] * pmax[0:2, None]).sum(axis=0) / 400.0
        np.testing.assert_allclose(cw101, [0.5, 0.5], atol=1e-9)
        np.testing.assert_allclose(avail[2], [1.0, 1.0], atol=1e-9)
        # Unmapped residual water-filled to 0.80.
        np.testing.assert_allclose(avail[3], [0.8, 0.8], atol=1e-9)
        # Class total UNCHANGED (measured): 0.75 × 1200 = 900 MW.
        class_live = (avail * pmax[:, None]).sum(axis=0)
        np.testing.assert_allclose(class_live, [900.0, 900.0], atol=1e-6)

    def test_plant_series_missing_files_is_a_noop(self):
        """The plant loader degrades to {} when its inputs are absent, so the
        caller keeps the class-HOUR grain (missing-file no-op convention)."""
        import market_sim.data.outages as _o

        real_xw = _o.ERCOT_DAM_PLANT_CROSSWALK_CSV
        try:
            # ercot-191: the cache lives on the shared _ercot_dam_plant_frames
            # builder (frac + covered-rating series, ruling #10).
            _o._ercot_dam_plant_frames.cache_clear()
            _o.ERCOT_DAM_PLANT_CROSSWALK_CSV = real_xw.parent / "does-not-exist.csv"
            self.assertEqual(_o.ercot_thermal_dam_availability_plant_series(2023), {})
        finally:
            _o.ERCOT_DAM_PLANT_CROSSWALK_CSV = real_xw
            _o._ercot_dam_plant_frames.cache_clear()

    def test_zeroed_tranches_stay_zero_and_cap_holds(self):
        """The rescale is multiplicative (zeros preserved) and caps at 1.0."""
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays

        def ct(i: int) -> Generator:
            return Generator(
                unit_id=f"66666_{i}",
                name=f"ct {i}",
                zone="North",
                fuel_type="gas_ct",
                pmax_mw=100.0,
                pmin_mw=0.0,
                heat_rate=10.5,
                vom=4.0,
                emission_rate_co2=0.55,
                nox_rate=0.0,
                eford=0.06,
                online_year=2001,
                plant_code=66666,
                is_campd_bin=True,
                plant_group="CT_PEAKER",
            )

        gens = [ct(1), ct(2)]
        cfg = ScenarioConfig(
            weather_year=2023,
            iso="ERCOT",
            mode="backcast",
            ercot_thermal_dam_availability=True,
        )
        fa = generators_to_fleet_arrays(
            gens, ["North"], hours=HOURS_PER_YEAR, iso="ERCOT", config=cfg, year=2023
        )
        self.assertTrue((fa.availability <= 1.0 + 1e-9).all())
        self.assertTrue((fa.availability >= 0.0).all())


class ShortUnitOutageDerateTest(unittest.TestCase):
    """The < 5-day baseload-coal short-window companion overlay.

    Windows come from ``campd-unit-outages-short-<ISO>.csv`` (derive script
    ``--short-windows`` mode); the loader must (a) no-op when the file is
    absent, (b) drop rows at/above the standard overlay's 5-day floor
    (disjointness) and non-COAL rows (defense in depth), and (c) derate the
    plant's COAL bin by the unit's capacity share over the window only.
    """

    # Baldwin Energy Complex — a real MISO coal plant present in the model
    # fleet, so _iso_plant_capacity("MISO") carries its (code, COAL) bin.
    PLANT = 889
    UNIT_MW = 625.1

    def _write_short_csv(self, tmpdir: str, rows: list[dict]) -> Path:
        path = Path(tmpdir) / "campd-unit-outages-short-MISO.csv"
        cols = [
            "facility_name",
            "facility_id",
            "unit_id",
            "unit_capacity_mw",
            "plant_capacity_mw",
            "unit_pct_of_plant",
            "plant_group",
            "capacity_source",
            "outage_start",
            "outage_end",
            "duration_days",
            "peer_units_online",
            "total_units_at_plant",
        ]
        pd.DataFrame(rows, columns=cols).to_csv(path, index=False)
        return path

    def _factors(self, csv_path: Path | None, year: int):
        from unittest.mock import patch

        from market_sim.data import outages

        outages.unit_outage_short_derate_factors.cache_clear()
        target = csv_path if csv_path else Path("/nonexistent/short.csv")
        with patch.object(
            outages, "unit_outage_short_csv_for_iso", return_value=target
        ):
            return outages.unit_outage_short_derate_factors(year, iso="MISO")

    def _row(self, start: str, end: str, days: float, group: str = "COAL") -> dict:
        return {
            "facility_name": "Baldwin Energy Complex",
            "facility_id": self.PLANT,
            "unit_id": "1",
            "unit_capacity_mw": self.UNIT_MW,
            "plant_capacity_mw": 1259.6,
            "unit_pct_of_plant": 49.6,
            "plant_group": group,
            "capacity_source": "eia_exact",
            "outage_start": start,
            "outage_end": end,
            "duration_days": days,
            "peer_units_online": 1,
            "total_units_at_plant": 2,
        }

    def test_missing_file_is_a_noop(self):
        self.assertEqual(self._factors(None, 2025), {})

    def test_short_coal_window_derates_only_its_span(self):
        with tempfile.TemporaryDirectory() as td:
            csv = self._write_short_csv(
                td, [self._row("2025-07-28", "2025-07-29", 2.0)]
            )
            factors = self._factors(csv, 2025)
        key = (self.PLANT, "COAL")
        self.assertIn(key, factors)
        arr = factors[key]
        self.assertEqual(arr.shape, (HOURS_PER_YEAR,))
        jul28 = _hour_of_year(7, 28, 0)
        jul30 = _hour_of_year(7, 30, 0)
        # Derated by the unit's share of the plant bin inside the window...
        self.assertTrue((arr[jul28:jul30] < 1.0).all())
        self.assertGreater(arr[jul28], 0.0)
        # ...and untouched outside it.
        self.assertTrue((arr[:jul28] == 1.0).all())
        self.assertTrue((arr[jul30:] == 1.0).all())

    def test_rows_at_or_above_floor_and_non_coal_are_dropped(self):
        with tempfile.TemporaryDirectory() as td:
            csv = self._write_short_csv(
                td,
                [
                    # >= 5 days: belongs to the standard overlay, not here.
                    self._row("2025-03-01", "2025-03-10", 9.5),
                    # Non-coal: the mode never emits these; drop defensively.
                    self._row("2025-07-28", "2025-07-29", 2.0, group="ST_GAS"),
                ],
            )
            factors = self._factors(csv, 2025)
        self.assertEqual(factors, {})


class ShortGasUnitOutageDerateTest(unittest.TestCase):
    """The GAS-side scope of the short-window family (pjm-d4-4).

    ``ScenarioConfig.unit_outage_short_windows_gas`` adds
    ``campd-unit-outages-shortgas-<ISO>.csv`` alongside the coal-scoped extract.
    The contract under test: (a) OFF is byte-inert even when the gas file
    exists, (b) ON derates the gas bin on the same arithmetic as coal, (c) the
    two scopes are disjoint by plant group so neither leaks into the other, and
    (d) the >= 5-day floor still bounds the gas file too.
    """

    # Baldwin Energy Complex (MISO coal, in the fleet) + Elgin Energy Center's
    # CC bin, so both bins resolve through _iso_plant_capacity("MISO").
    COAL_PLANT = 889
    COAL_MW = 625.1

    def _paths(self, td: str, coal_rows: list[dict], gas_rows: list[dict]):
        cols = [
            "facility_name",
            "facility_id",
            "unit_id",
            "unit_capacity_mw",
            "plant_capacity_mw",
            "unit_pct_of_plant",
            "plant_group",
            "capacity_source",
            "outage_start",
            "outage_end",
            "duration_days",
            "peer_units_online",
            "total_units_at_plant",
        ]
        coal = Path(td) / "campd-unit-outages-short-MISO.csv"
        gas = Path(td) / "campd-unit-outages-shortgas-MISO.csv"
        pd.DataFrame(coal_rows, columns=cols).to_csv(coal, index=False)
        pd.DataFrame(gas_rows, columns=cols).to_csv(gas, index=False)
        return coal, gas

    def _row(self, plant, unit_mw, plant_mw, group, start, end, days) -> dict:
        return {
            "facility_name": "T",
            "facility_id": plant,
            "unit_id": "1",
            "unit_capacity_mw": unit_mw,
            "plant_capacity_mw": plant_mw,
            "unit_pct_of_plant": round(100.0 * unit_mw / plant_mw, 1),
            "plant_group": group,
            "capacity_source": "eia_exact",
            "outage_start": start,
            "outage_end": end,
            "duration_days": days,
            "peer_units_online": 1,
            "total_units_at_plant": 2,
        }

    def _factors(self, coal: Path, gas: Path, *, gas_scope: bool):
        from unittest.mock import patch

        from market_sim.data import outages

        outages.unit_outage_short_derate_factors.cache_clear()
        with (
            patch.object(outages, "unit_outage_short_csv_for_iso", return_value=coal),
            patch.object(
                outages, "unit_outage_short_gas_csv_for_iso", return_value=gas
            ),
        ):
            return outages.unit_outage_short_derate_factors(
                2025, iso="MISO", gas_scope=gas_scope
            )

    def _gas_bin(self):
        """A (plant_code, group) the MISO fleet actually carries on a gas bin."""
        from market_sim.data import outages

        cap = outages._iso_plant_capacity("MISO", False, False)
        for (code, group), mw in sorted(cap.items()):
            if group in outages._SHORT_GAS_GROUPS and mw > 100.0:
                return code, group, mw
        self.skipTest("no MISO gas bin in the fleet capacity index")

    def test_off_is_inert_even_when_the_gas_file_exists(self):
        code, group, mw = self._gas_bin()
        with tempfile.TemporaryDirectory() as td:
            coal, gas = self._paths(
                td,
                [
                    self._row(
                        self.COAL_PLANT,
                        self.COAL_MW,
                        1259.6,
                        "COAL",
                        "2025-07-28",
                        "2025-07-29",
                        2.0,
                    )
                ],
                [self._row(code, mw / 2.0, mw, group, "2025-07-28", "2025-07-29", 2.0)],
            )
            off = self._factors(coal, gas, gas_scope=False)
            on = self._factors(coal, gas, gas_scope=True)
        self.assertEqual(set(off), {(self.COAL_PLANT, "COAL")})
        self.assertEqual(set(on), {(self.COAL_PLANT, "COAL"), (code, group)})
        # The coal bin is untouched by arming the gas scope — the two scopes
        # are disjoint by plant group, so nothing stacks (rule 19).
        np.testing.assert_array_equal(
            off[(self.COAL_PLANT, "COAL")], on[(self.COAL_PLANT, "COAL")]
        )

    def test_gas_window_derates_only_its_span(self):
        code, group, mw = self._gas_bin()
        with tempfile.TemporaryDirectory() as td:
            coal, gas = self._paths(
                td,
                [],
                [self._row(code, mw / 2.0, mw, group, "2025-07-28", "2025-07-29", 2.0)],
            )
            factors = self._factors(coal, gas, gas_scope=True)
        arr = factors[(code, group)]
        jul28 = _hour_of_year(7, 28, 0)
        jul30 = _hour_of_year(7, 30, 0)
        self.assertTrue((arr[jul28:jul30] < 1.0).all())
        self.assertTrue((arr[:jul28] == 1.0).all())
        self.assertTrue((arr[jul30:] == 1.0).all())

    def test_floor_and_scope_still_bound_the_gas_file(self):
        code, group, mw = self._gas_bin()
        with tempfile.TemporaryDirectory() as td:
            coal, gas = self._paths(
                td,
                [],
                [
                    # >= the 5-day floor: belongs to the standard overlay.
                    self._row(
                        code, mw / 2.0, mw, group, "2025-03-01", "2025-03-10", 9.5
                    ),
                    # COAL rows never enter through the GAS file's scope.
                    self._row(
                        self.COAL_PLANT,
                        self.COAL_MW,
                        1259.6,
                        "COAL",
                        "2025-07-28",
                        "2025-07-29",
                        2.0,
                    ),
                ],
            )
            factors = self._factors(coal, gas, gas_scope=True)
        # The coal row DOES enter (both files feed one accumulator and COAL is
        # always in scope) — what must not happen is the >= 5-day gas row.
        self.assertNotIn((code, group), factors)

    def test_missing_gas_file_leaves_the_coal_scope_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            coal, _ = self._paths(
                td,
                [
                    self._row(
                        self.COAL_PLANT,
                        self.COAL_MW,
                        1259.6,
                        "COAL",
                        "2025-07-28",
                        "2025-07-29",
                        2.0,
                    )
                ],
                [],
            )
            missing = Path(td) / "nonexistent-shortgas.csv"
            on = self._factors(coal, missing, gas_scope=True)
            off = self._factors(coal, missing, gas_scope=False)
        self.assertEqual(set(on), {(self.COAL_PLANT, "COAL")})
        np.testing.assert_array_equal(
            on[(self.COAL_PLANT, "COAL")], off[(self.COAL_PLANT, "COAL")]
        )


class UnitPartialOutageDerateTest(unittest.TestCase):
    """The unit-grain partial-derate plateau overlay (LEG B).

    Windows come from ``campd-partial-outages-<ISO>.csv`` (derive script
    ``--partial-windows`` mode), each carrying a ``derate_factor`` = the
    measured availability fraction the unit ran at during the plateau. The
    consumer removes ``(1 - derate_factor) x unit_capacity`` from the plant's
    ``(plant_code, plant_group)`` bin — the same unit-capacity-share /
    concurrent-sum / clip-at-full aggregation as the >= 5-day overlay.
    """

    PLANT = 889  # Baldwin Energy Complex (MISO coal, in the model fleet)
    UNIT_MW = 625.1

    def _write_partial_csv(self, tmpdir: str, rows: list[dict]) -> Path:
        path = Path(tmpdir) / "campd-partial-outages-MISO.csv"
        cols = [
            "facility_name",
            "facility_id",
            "unit_id",
            "unit_capacity_mw",
            "plant_capacity_mw",
            "unit_pct_of_plant",
            "plant_group",
            "capacity_source",
            "outage_start",
            "outage_end",
            "duration_days",
            "peer_units_online",
            "total_units_at_plant",
            "derate_factor",
        ]
        pd.DataFrame(rows, columns=cols).to_csv(path, index=False)
        return path

    def _factors(self, csv_path: Path | None, year: int):
        from unittest.mock import patch

        from market_sim.data import outages

        outages.unit_partial_outage_derate_factors.cache_clear()
        target = csv_path if csv_path else Path("/nonexistent/partial.csv")
        with patch.object(
            outages, "unit_partial_outage_csv_for_iso", return_value=target
        ):
            return outages.unit_partial_outage_derate_factors(year, iso="MISO")

    def _row(
        self, start: str, end: str, derate_factor: float, unit_id: str = "1"
    ) -> dict:
        return {
            "facility_name": "Baldwin Energy Complex",
            "facility_id": self.PLANT,
            "unit_id": unit_id,
            "unit_capacity_mw": self.UNIT_MW,
            "plant_capacity_mw": 1259.6,
            "unit_pct_of_plant": 49.6,
            "plant_group": "COAL",
            "capacity_source": "eia_exact",
            "outage_start": start,
            "outage_end": end,
            "duration_days": 20.0,
            "peer_units_online": 1,
            "total_units_at_plant": 2,
            "derate_factor": derate_factor,
        }

    def test_missing_file_is_a_noop(self):
        self.assertEqual(self._factors(None, 2025), {})

    def test_partial_derate_removes_the_lost_fraction_only(self):
        # A unit at half its capability (derate_factor 0.5) removes half of its
        # capacity share from the plant bin inside the window, nothing outside.
        from market_sim.data.outages import _iso_plant_capacity

        with tempfile.TemporaryDirectory() as td:
            csv = self._write_partial_csv(
                td, [self._row("2025-07-10", "2025-07-29", 0.5)]
            )
            factors = self._factors(csv, 2025)
        key = (self.PLANT, "COAL")
        self.assertIn(key, factors)
        arr = factors[key]
        plant_cap = _iso_plant_capacity("MISO")[key]
        expected = 1.0 - 0.5 * self.UNIT_MW / plant_cap
        jul15 = _hour_of_year(7, 15, 0)
        jan1 = 0
        self.assertAlmostEqual(arr[jul15], expected, places=4)
        self.assertEqual(arr[jan1], 1.0)  # outside the window: full availability

    def test_full_derate_factor_is_a_noop(self):
        # derate_factor 1.0 = ran at full ceiling = nothing removed.
        with tempfile.TemporaryDirectory() as td:
            csv = self._write_partial_csv(
                td, [self._row("2025-07-10", "2025-07-29", 1.0)]
            )
            factors = self._factors(csv, 2025)
        # No capacity removed -> the bin either absent or all-ones.
        arr = factors.get((self.PLANT, "COAL"))
        if arr is not None:
            self.assertTrue((arr == 1.0).all())


class PartialOutageClassGrainTest(unittest.TestCase):
    """The ercot-173 C1 grain repair of ``partial_outage_derate_factors``.

    ``class_grain=True`` keys by the extract's own ``(oris_code, plant_group)``
    instead of ``oris_code`` alone (gated by
    ``ScenarioConfig.ercot_dam_availability_event_cap_reconciliation``). On the
    committed extract no plant code carries more than one group, so the two
    grains must induce identical per-plant factor arrays — the P-C1-INERT
    prediction of PRECOMMIT-ercot173 §5, asserted here at loader grain.
    """

    def test_default_keys_are_plant_codes(self):
        from market_sim.data.outages import partial_outage_derate_factors

        plant = partial_outage_derate_factors(2024, HOURS_PER_YEAR)
        if not plant:  # extract absent in a minimal checkout
            self.skipTest("no partial-outage extract on disk")
        self.assertTrue(all(isinstance(k, int) for k in plant))

    def test_class_grain_keys_and_inertness(self):
        from market_sim.data.outages import partial_outage_derate_factors

        for year in (2023, 2024, 2025):
            plant = partial_outage_derate_factors(year, HOURS_PER_YEAR)
            cls = partial_outage_derate_factors(year, HOURS_PER_YEAR, class_grain=True)
            if not plant:
                continue
            self.assertTrue(all(isinstance(k, tuple) and len(k) == 2 for k in cls))
            # one group per plant code on the committed extract ...
            codes = [k[0] for k in cls]
            self.assertEqual(len(set(codes)), len(codes))
            self.assertEqual(set(codes), set(plant))
            # ... and byte-identical factor arrays per plant (C1 inert).
            for (code, _group), arr in cls.items():
                self.assertTrue(np.array_equal(arr, plant[code]))


class UnitScopedEventCapCompositionTest(unittest.TestCase):
    """The ercot-174 unit-scoped event-cap composition's loader layer.

    The composition picks ``min()`` over the incumbent product only at hours
    where the window and partial layers share a CAMPD unit, so the correctness
    that matters is (a) the two unit-set loaders agree on unit ids and routing,
    (b) :func:`shared_unit_hours` is a true per-hour AND over shared ids, and
    (c) every absent-side case is fail-safe (no shared hours ⇒ the incumbent
    product survives).
    """

    def test_shared_unit_hours_is_a_per_hour_and(self):
        from market_sim.data.outages import shared_unit_hours

        h = 24
        w = {"U1": np.zeros(h, dtype=bool), "U2": np.zeros(h, dtype=bool)}
        p = {"U1": np.zeros(h, dtype=bool), "U3": np.ones(h, dtype=bool)}
        w["U1"][2:8] = True
        p["U1"][5:12] = True
        w["U2"][0:24] = True  # U2 is not in the partial layer at all
        shared = shared_unit_hours(w, p, h)
        # only U1's OVERLAP counts: hours 5,6,7
        self.assertEqual(list(np.flatnonzero(shared)), [5, 6, 7])

    def test_absent_side_is_fail_safe(self):
        from market_sim.data.outages import shared_unit_hours

        h = 12
        live = {"U1": np.ones(h, dtype=bool)}
        for a, b in ((None, live), (live, None), (None, None), ({}, live)):
            self.assertFalse(shared_unit_hours(a, b, h).any())

    def test_unit_ids_are_matched_after_normalisation(self):
        from market_sim.data.outages import shared_unit_hours

        h = 8
        w = {"CTG-1": np.ones(h, dtype=bool)}
        p = {"ctg1": np.ones(h, dtype=bool)}
        self.assertTrue(shared_unit_hours(w, p, h).all())

    def test_active_unit_sets_match_their_factor_layers(self):
        """A bin with a non-trivial factor must carry at least one unit."""
        from market_sim.data.outages import (
            partial_outage_active_units,
            partial_outage_derate_factors,
            unit_outage_active_units,
            unit_outage_derate_factors,
        )

        for year in (2023, 2024, 2025):
            w_fac = unit_outage_derate_factors(year, HOURS_PER_YEAR, iso="ERCOT")
            w_units = unit_outage_active_units(year, HOURS_PER_YEAR, iso="ERCOT")
            if not w_fac:
                continue
            # Every bin the window layer derates carries named units, and each
            # unit's active hours sit inside the bin's derated hours.
            for key, fac in w_fac.items():
                self.assertIn(key, w_units, msg=f"window bin {key} has no units")
                derated = fac < 1.0
                for uid, mask in w_units[key].items():
                    self.assertTrue(
                        bool((mask & ~derated).sum() == 0),
                        msg=f"{key} {uid} active outside its own derate",
                    )
            p_fac = partial_outage_derate_factors(
                year, HOURS_PER_YEAR, class_grain=True
            )
            p_units = partial_outage_active_units(year, HOURS_PER_YEAR, iso="ERCOT")
            # Carriers are indexed by the bin the UNIT routes to, which for a
            # split facility (W A Parish 3470 coal / 34702 gas-steam) can differ
            # from the bin its extract row keys. Those off-bin entries are inert
            # by construction — the composition consults the unit sets only for
            # a bin that carries a partial factor — and that is the invariant
            # asserted here, together with in-window containment.
            for key, units in p_units.items():
                if key not in p_fac:
                    continue  # unreachable: no partial factor on this bin
                derated = p_fac[key] < 1.0
                for uid, mask in units.items():
                    self.assertTrue(
                        bool((mask & ~derated).sum() == 0),
                        msg=f"{key} {uid} active outside its own plateau",
                    )
            self.assertTrue(
                any(k in p_fac for k in p_units),
                msg="no partial carrier lands on a bin the plateau derates",
            )

    def test_unit_attributed_extract_aggregates_to_the_plant_grain_file(self):
        """BE-3 on the COMMITTED files: the grain is the only difference."""
        from market_sim.data.outages import (
            PARTIAL_OUTAGE_CSV,
            PARTIAL_OUTAGE_UNITS_CSV,
        )

        if not (PARTIAL_OUTAGE_CSV.exists() and PARTIAL_OUTAGE_UNITS_CSV.exists()):
            self.skipTest("partial-outage extracts absent in a minimal checkout")
        plant = pd.read_csv(PARTIAL_OUTAGE_CSV)
        units = pd.read_csv(PARTIAL_OUTAGE_UNITS_CSV)
        cols = list(plant.columns)
        back = (
            units[cols]
            .drop_duplicates()
            .sort_values(["year", "oris_code", "outage_start"])
            .reset_index(drop=True)
        )
        pd.testing.assert_frame_equal(
            back,
            plant.sort_values(["year", "oris_code", "outage_start"]).reset_index(
                drop=True
            ),
        )


def _unit_outage_row(**over) -> dict:
    """Return one well-formed unit-outage event row, overridable per test."""
    row = {
        "facility_name": "Grain Test",
        "facility_id": 70002,
        "unit_id": "1",
        "unit_capacity_mw": 500.0,
        "plant_capacity_mw": 500.0,
        "unit_pct_of_plant": 100.0,
        "plant_group": "COAL",
        "capacity_source": "eia_exact",
        "outage_start": "2023-06-01",
        "outage_end": "2023-06-20",
        "duration_days": 20.0,
        "peer_units_online": 0,
        "total_units_at_plant": 1,
    }
    row.update(over)
    return row


class UnitOutageHourGrainTest(unittest.TestCase):
    """The OPTIONAL hour-grain carriage (caiso-183).

    The detector works in hours but the extract stored days, so the loader used
    to re-expand every window to ``outage_start`` 00:00 -> ``outage_end`` 23:00
    and assert up to 23 h per edge it never detected. These cover the three
    properties the repair rests on: the day-granular fallback is unchanged, the
    hour grain narrows the window to exactly what was detected, and a null hour
    falls back per row.
    """

    def _factors(self, rows: list[dict], year: int = 2023):
        from unittest.mock import patch

        from market_sim.data import outages

        with tempfile.TemporaryDirectory() as td:
            csv = Path(td) / "campd-unit-outages-MISO.csv"
            pd.DataFrame(rows).to_csv(csv, index=False)
            outages.unit_outage_derate_factors.cache_clear()
            with (
                patch.object(outages, "unit_outage_csv_for_iso", return_value=csv),
                patch.object(
                    outages,
                    "_iso_plant_capacity",
                    return_value={(70002, "COAL"): 500.0},
                ),
            ):
                return outages.unit_outage_derate_factors(
                    year, HOURS_PER_YEAR, iso="MISO"
                )

    def test_absent_hour_columns_reproduce_the_day_granular_window(self):
        # The fallback is the incumbent behaviour by IDENTITY: an absent grain
        # is exactly start_hour 0 / end_hour 23, and +(23+1) h == +1 day.
        without = self._factors([_unit_outage_row()])[(70002, "COAL")]
        with_zero_23 = self._factors(
            [_unit_outage_row(outage_start_hour=0, outage_end_hour=23)]
        )[(70002, "COAL")]
        np.testing.assert_array_equal(without, with_zero_23)
        # Jun 1 00:00 through Jun 20 23:00 inclusive = 20 days.
        self.assertEqual(int((1.0 - without).sum()), 20 * 24)

    def test_hour_grain_narrows_the_window_to_what_was_detected(self):
        arr = self._factors(
            [
                _unit_outage_row(
                    outage_start_hour=22, outage_end_hour=1, duration_days=18.2
                )
            ]
        )[(70002, "COAL")]
        # Detected span is Jun 1 22:00 -> Jun 20 01:00 inclusive = 19.2 days.
        self.assertEqual(int((1.0 - arr).sum()), 20 * 24 - 22 - 22)
        self.assertEqual(arr[_hour_of_year(6, 1, 21)], 1.0)  # still running
        self.assertEqual(arr[_hour_of_year(6, 1, 22)], 0.0)  # first detected hour
        self.assertEqual(arr[_hour_of_year(6, 20, 1)], 0.0)  # last detected hour
        self.assertEqual(arr[_hour_of_year(6, 20, 2)], 1.0)  # back in service

    def test_hour_grain_only_ever_narrows(self):
        # The monotone-subset invariant the deriver asserts, seen from the
        # loader: no hour grain can widen the day-granular window.
        day = self._factors([_unit_outage_row()])[(70002, "COAL")]
        for h0, h1 in ((0, 23), (5, 23), (0, 5), (23, 0)):
            arr = self._factors(
                [_unit_outage_row(outage_start_hour=h0, outage_end_hour=h1)]
            )[(70002, "COAL")]
            self.assertTrue(
                bool(np.all(arr >= day)),
                f"hour grain ({h0}, {h1}) widened the window",
            )

    def test_null_hours_fall_back_row_by_row(self):
        # A partially-populated extract degrades per row rather than raising.
        arr = self._factors(
            [
                _unit_outage_row(outage_start_hour=float("nan"), outage_end_hour=23),
                _unit_outage_row(
                    facility_id=70002,
                    unit_id="2",
                    outage_start="2023-09-01",
                    outage_end="2023-09-10",
                    duration_days=10.0,
                    outage_start_hour=6,
                    outage_end_hour=5,
                ),
            ]
        )[(70002, "COAL")]
        # Row 1 fell back to the full day-granular window...
        self.assertEqual(arr[_hour_of_year(6, 1, 0)], 0.0)
        # ...row 2 used its detected hours.
        self.assertEqual(arr[_hour_of_year(9, 1, 5)], 1.0)
        self.assertEqual(arr[_hour_of_year(9, 1, 6)], 0.0)


class DeriverHourGrainAssertionTest(unittest.TestCase):
    """The deriver's stop-the-line grain assertions (ercot-174 BE-3 class)."""

    def _assert_fn(self):
        import importlib

        mod = importlib.import_module("scripts.data.derive_campd_unit_outages")
        return mod.assert_hour_grain_consistent

    def _frame(self, **over) -> pd.DataFrame:
        # Jun 1 22:00 -> Jun 20 01:00 inclusive = 436 h = 18.2 d, which is what
        # the detector's own round((e - s) / 24, 1) would record.
        row = _unit_outage_row(outage_start_hour=22, outage_end_hour=1)
        row["duration_days"] = 18.2
        row.update(over)
        return pd.DataFrame([row])

    def test_accepts_a_consistent_frame(self):
        self._assert_fn()(self._frame())

    def test_rejects_an_hour_outside_the_day(self):
        with self.assertRaises(AssertionError):
            self._assert_fn()(self._frame(outage_start_hour=24))

    def test_rejects_a_window_that_disagrees_with_duration_days(self):
        with self.assertRaises(AssertionError):
            self._assert_fn()(self._frame(duration_days=20.0))

    def test_rejects_an_empty_window(self):
        with self.assertRaises(AssertionError):
            self._assert_fn()(
                self._frame(
                    outage_end="2023-06-01", outage_start_hour=10, outage_end_hour=5
                )
            )

    def test_netzero_rows_are_exempt_from_the_duration_check(self):
        # An EIA-923 net-zero window is a whole calendar year carrying a nominal
        # 365.0 duration_days, which a leap year would otherwise trip.
        self._assert_fn()(
            self._frame(
                capacity_source="eia923_netzero",
                outage_start="2024-01-01",
                outage_end="2024-12-31",
                outage_start_hour=0,
                outage_end_hour=23,
                duration_days=365.0,
            )
        )


class UnitOutageLpCapacityBasisTest(unittest.TestCase):
    """The derate DENOMINATOR on the LP's own capacity basis (caiso-184).

    ``ScenarioConfig.unit_outage_lp_capacity_basis``. The extract's
    ``unit_capacity_mw`` numerator is the EIA-860 NAMEPLATE the deriver writes;
    the denominator ``_iso_plant_capacity`` supplies is the fleet's NET-SUMMER
    pmax sum, and with ``cc_nameplate_summer_derate`` armed ``fleet_to_bins``
    additionally raises the CC bin to full nameplate for the LP. The removed
    FRACTION is then inflated by ``nameplate / net_summer``. These cover the four
    properties the repair rests on: it is OFF by default (BE-1), it reaches only
    the CC groups, it is MONOTONE (a denominator can only rise, so a removed
    fraction can only fall), and the raised denominator reproduces
    ``fleet_to_bins``' own arithmetic exactly.
    """

    ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP")

    def test_default_is_byte_identical_for_every_iso(self):
        # BE-1: the gate absent must be the incumbent map, exactly, everywhere.
        from market_sim.data.outages import _iso_plant_capacity

        for iso in self.ISOS:
            with self.subTest(iso=iso):
                self.assertEqual(
                    _iso_plant_capacity(iso), _iso_plant_capacity(iso, False, False)
                )

    def test_repair_reaches_only_the_cc_groups(self):
        # fleet_to_bins raises CC_REGULAR / CC_CHP and nothing else, so the
        # denominator repair must move exactly those bins and no others.
        from market_sim.data.outages import (
            _CC_NAMEPLATE_BASIS_GROUPS,
            _iso_plant_capacity,
        )

        for iso in self.ISOS:
            off = _iso_plant_capacity(iso)
            on = _iso_plant_capacity(iso, False, True)
            moved = [k for k in off if abs(on[k] - off[k]) > 1e-9]
            with self.subTest(iso=iso):
                self.assertTrue(moved, f"{iso} has no CC bin to raise")
                self.assertFalse(
                    [k for k in moved if k[1] not in _CC_NAMEPLATE_BASIS_GROUPS],
                    f"{iso} moved a non-CC bin",
                )

    def test_monotone_a_denominator_can_only_rise(self):
        # G-MONO: nameplate >= net summer, so no removed fraction can increase.
        # A falling denominator would be a stop-the-line event.
        from market_sim.data.outages import _iso_plant_capacity

        for iso in self.ISOS:
            off = _iso_plant_capacity(iso)
            on = _iso_plant_capacity(iso, False, True)
            with self.subTest(iso=iso):
                self.assertFalse([k for k in off if on[k] < off[k] - 1e-9])

    def test_raised_denominator_reproduces_fleet_to_bins_arithmetic(self):
        # G-CONSIST: the repaired denominator must be the SAME number
        # fleet_to_bins puts in the LP -- `cap / cc_summer_derate_ratio` on the
        # same published ratio, with the same absent-plant fallback.
        from market_sim.data.fleet.campd_bins import cc_summer_derate_ratio
        from market_sim.data.outages import (
            _CC_NAMEPLATE_BASIS_GROUPS,
            _iso_plant_capacity,
        )

        off = _iso_plant_capacity("CAISO")
        on = _iso_plant_capacity("CAISO", False, True)
        checked = 0
        for key, base in off.items():
            if key[1] not in _CC_NAMEPLATE_BASIS_GROUPS:
                continue
            ratio = cc_summer_derate_ratio(int(key[0]))
            expected = base / ratio if ratio is not None and ratio > 0.0 else base
            self.assertAlmostEqual(on[key], expected, places=9, msg=str(key))
            checked += 1
        self.assertGreater(checked, 0)

    def test_derate_share_falls_when_the_denominator_is_raised(self):
        # The end-to-end property: a two-unit plant with one unit out removes a
        # SMALLER fraction once the denominator is the capacity the multiplier
        # is applied to. 100 MW out of a 400 MW nameplate plant carried at 360 MW
        # net summer: 27.8 % removed today, 25.0 % after the repair.
        from unittest.mock import patch

        from market_sim.data import outages

        rows = [_unit_outage_row(plant_group="CC_REGULAR", unit_capacity_mw=100.0)]
        with tempfile.TemporaryDirectory() as td:
            csv = Path(td) / "campd-unit-outages-MISO.csv"
            pd.DataFrame(rows).to_csv(csv, index=False)
            out = {}
            for armed, cap in ((False, 360.0), (True, 400.0)):
                outages.unit_outage_derate_factors.cache_clear()
                with (
                    patch.object(outages, "unit_outage_csv_for_iso", return_value=csv),
                    patch.object(
                        outages,
                        "_iso_plant_capacity",
                        return_value={(70002, "CC_REGULAR"): cap},
                    ),
                ):
                    out[armed] = outages.unit_outage_derate_factors(
                        2023, HOURS_PER_YEAR, iso="MISO"
                    )[(70002, "CC_REGULAR")]
            outages.unit_outage_derate_factors.cache_clear()
        removed_now = 1.0 - out[False].min()
        removed_fix = 1.0 - out[True].min()
        self.assertAlmostEqual(removed_now, 100.0 / 360.0, places=9)
        self.assertAlmostEqual(removed_fix, 100.0 / 400.0, places=9)
        self.assertLess(removed_fix, removed_now)


class ShapedPartialOutageDerateTest(unittest.TestCase):
    """The ercot-185 fault-3 day-shaped partial-outage plateau construction.

    The repair replaces a plateau's single flat multi-week factor with a
    day-resolved profile over the SAME days. What must hold is (a) the
    construction is what it says it is, (b) it is median-preserving — a pure
    re-shaping, never a net lift or cut, which is what separates it from the
    adjudicated-dead restore-only composition arms — (c) the two plateau
    populations cannot drift apart, and (d) the loader gate is fail-safe.
    """

    @staticmethod
    def _cf_with_plateau() -> np.ndarray:
        """A synthetic baseload year: full output, then a SHAPED 20-day dip.

        The dip's daily ceiling ramps 0.30 -> 0.60 across the window, so a flat
        window-median ceiling provably forbids output the plant demonstrably
        reached on the window's later days — the fault-3 defect in miniature.
        """
        nd = 120
        daily = np.full(nd, 0.95)
        daily[50:70] = np.linspace(0.30, 0.60, 20)
        cf = np.repeat(daily, 24)
        # A within-day shape so daily MAX is the ceiling and daily MEAN stays
        # above _RUN_FLOOR_CF (the plant is running, not out).
        cf *= np.tile(np.linspace(0.8, 1.0, 24), nd)
        return cf

    def test_shaped_profile_is_the_stated_construction(self):
        from scripts.lib.outage_detect import (
            _plateau_state,
            _detect,
            detect_shaped,
        )

        cf = self._cf_with_plateau()
        flat, shaped = _detect(cf), detect_shaped(cf)
        self.assertTrue(flat, "the synthetic plateau must be detected at all")
        self.assertEqual(len(flat), len(shaped))
        dmax, ref, sm, _partial = _plateau_state(cf)
        for (i, j, f0), (si, sj, prof) in zip(flat, shaped):
            self.assertEqual((i, j), (si, sj))  # same days, no population change
            self.assertEqual(len(prof), j - i)
            want = np.round(np.clip(f0 * sm[i:j] / float(np.median(sm[i:j])), 0, 1), 3)
            np.testing.assert_allclose(prof, want, atol=1e-9)

    def test_shaped_profile_is_median_preserving(self):
        """SP-6: median(shaped) == the incumbent flat factor (rounding aside).

        This is the property that makes the repair a RE-SHAPING rather than a
        level change, so it can never be the restore-only rejected arm.
        """
        from scripts.lib.outage_detect import _detect, detect_shaped

        cf = self._cf_with_plateau()
        for (_i, _j, f0), (_si, _sj, prof) in zip(_detect(cf), detect_shaped(cf)):
            self.assertAlmostEqual(float(np.median(prof)), f0, delta=0.002)
            # Genuinely two-sided: the profile straddles the flat factor.
            self.assertGreater(prof.max(), f0)
            self.assertLess(prof.min(), f0)

    def test_shaped_detector_shares_the_plateau_population(self):
        """The flat and shaped detectors read spans from one _plateau_spans."""
        from scripts.lib.outage_detect import _detect, detect_shaped, detect_shaped_raw

        for cf in (self._cf_with_plateau(), np.zeros(24 * 60), np.full(24 * 60, 0.9)):
            spans = [(i, j) for i, j, _ in _detect(cf)]
            for fn in (detect_shaped, detect_shaped_raw):
                self.assertEqual([(i, j) for i, j, _ in fn(cf)], spans)

    def test_variant_raw_is_capped_by_the_membership_test(self):
        """Precommit §2a-bis: RAW is bounded by _CEILING_FRAC, the flat factor is not.

        This is why RAW changes the plateau LEVEL as well as its shape and is
        reported-only rather than armed.
        """
        from scripts.lib.outage_detect import _CEILING_FRAC, detect_shaped_raw

        for _i, _j, prof in detect_shaped_raw(self._cf_with_plateau()):
            self.assertLessEqual(float(prof.max()), _CEILING_FRAC + 1e-9)

    def test_loader_gate_is_fail_safe_when_the_extract_is_absent(self):
        """An absent shaped extract degrades to the incumbent flat factors."""
        from unittest.mock import patch

        from market_sim.data import outages

        outages.partial_outage_derate_factors.cache_clear()
        try:
            flat = outages.partial_outage_derate_factors(2024, HOURS_PER_YEAR)
            outages.partial_outage_derate_factors.cache_clear()
            with patch.object(
                outages, "PARTIAL_OUTAGE_SHAPED_CSV", Path("/nonexistent/shaped.csv")
            ):
                degraded = outages.partial_outage_derate_factors(
                    2024, HOURS_PER_YEAR, shaped=True
                )
            self.assertEqual(set(flat), set(degraded))
            for k in flat:
                np.testing.assert_array_equal(flat[k], degraded[k])
        finally:
            outages.partial_outage_derate_factors.cache_clear()

    def test_committed_shaped_extract_tiles_the_committed_flat_extract(self):
        """The shipped pair: same covered hours, same plateau spans, per year."""
        from market_sim.data.outages import (
            PARTIAL_OUTAGE_CSV,
            PARTIAL_OUTAGE_SHAPED_CSV,
        )

        if not PARTIAL_OUTAGE_SHAPED_CSV.exists():
            self.skipTest("shaped extract not present")
        flat = pd.read_csv(PARTIAL_OUTAGE_CSV)
        shaped = pd.read_csv(PARTIAL_OUTAGE_SHAPED_CSV)
        for year in (2023, 2024, 2025):
            for code in sorted(flat[flat["year"] == year]["oris_code"].unique()):

                def _cover(df):
                    m = np.zeros(HOURS_PER_YEAR, dtype=bool)
                    sub = df[(df["year"] == year) & (df["oris_code"] == code)]
                    for r in sub.itertuples(index=False):
                        m |= outage_hour_mask(
                            r.outage_start, r.outage_stop, year, HOURS_PER_YEAR
                        )
                    return m

                np.testing.assert_array_equal(
                    _cover(flat), _cover(shaped), f"{code} {year} covered hours differ"
                )


if __name__ == "__main__":
    unittest.main()
