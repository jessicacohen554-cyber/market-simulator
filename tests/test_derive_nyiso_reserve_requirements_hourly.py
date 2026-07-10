"""Tests for the hourly reserve-requirement derive (Ask B reconstruction).

Exercises the pure construction functions on synthetic frames — version
selection, the TSA start/end state machine (duplicate starts, end-without-
start, start-of-day continuation, cross-midnight windows), the hourly step
base, time-weighted TSA zeroing, the non-leap 8760 clock — and one
end-to-end check: a derived synthetic year loads through
``load_nyiso_reserve_requirements`` with the family keys the LP channel
expects. No real data tree is touched.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from market_sim.data.nyiso_reserve_requirements import (
    load_nyiso_reserve_requirements,
)
from scripts.derive_nyiso_reserve_requirements_hourly import (
    build_hourly_base,
    build_tsa_windows,
    derive_year,
    hourly_clock,
    select_version,
    tsa_fraction,
)


def _schedule() -> pd.DataFrame:
    """Synthetic v2021-shaped schedule: SENY steps + NYC flat + one LI row."""
    rows = [
        # version, region, product, period_label, hb_start, hb_end, mw, tsa_zero
        ("v2021", "SENY", "total_30", "hb_range", 0, 5, 1300.0, True),
        ("v2021", "SENY", "total_30", "hb_range", 6, 6, 1550.0, True),
        ("v2021", "SENY", "total_30", "hb_range", 7, 21, 1800.0, True),
        ("v2021", "SENY", "total_30", "hb_range", 22, 22, 1550.0, True),
        ("v2021", "SENY", "total_30", "hb_range", 23, 23, 1300.0, True),
        ("v2021", "NYC", "total_10", "all", 0, 23, 500.0, True),
        ("v2021", "NYCA", "total_30", "all", 0, 23, 2620.0, False),
        ("v2021", "LI", "total_10", "all", 0, 23, 120.0, False),
        ("v2020", "NYC", "total_10", "all", 0, 23, 500.0, False),
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "version",
            "region",
            "product",
            "period_label",
            "hb_start",
            "hb_end",
            "requirement_mw",
            "tsa_reduced_to_zero",
        ],
    )
    df["evidence_start"] = np.where(
        df["version"] == "v2021", pd.Timestamp("2021-12-04"), pd.Timestamp("2020-10-29")
    )
    df["evidence_end"] = np.where(
        df["version"] == "v2021", pd.Timestamp("2026-02-14"), pd.Timestamp("2021-12-04")
    )
    return df


def _events(rows: list[tuple]) -> pd.DataFrame:
    """Synthetic TSA event frame from (timestamp_local, action[, start_of_day])."""
    return pd.DataFrame(
        {
            "timestamp_local": pd.to_datetime([r[0] for r in rows]),
            "action": [r[1] for r in rows],
            "start_of_day": [bool(r[2]) if len(r) > 2 else False for r in rows],
            "event_type": "thunderstorm_alert",
            "seq": range(len(rows)),
        }
    )


class TestVersionSelection(unittest.TestCase):
    def test_covering_version_selected(self) -> None:
        rows = select_version(_schedule(), 2024)
        self.assertEqual(set(rows["version"]), {"v2021"})

    def test_uncovered_year_raises(self) -> None:
        # 2021 straddles the v2020 -> v2021 evidence boundary.
        with self.assertRaises(ValueError):
            select_version(_schedule(), 2021)


class TestTsaWindows(unittest.TestCase):
    def test_plain_pairing_and_attested_cross_midnight(self) -> None:
        windows, anomalies = build_tsa_windows(
            _events(
                [
                    ("2024-07-05 19:00", "start"),
                    ("2024-07-05 22:30", "end"),
                    ("2024-08-01 23:00", "start"),
                    ("2024-08-02 00:00", "start", True),  # attested sod continuation
                    ("2024-08-02 01:30", "end"),
                ]
            )
        )
        self.assertEqual(
            windows,
            [
                (pd.Timestamp("2024-07-05 19:00"), pd.Timestamp("2024-07-05 22:30")),
                (pd.Timestamp("2024-08-01 23:00"), pd.Timestamp("2024-08-02 01:30")),
            ],
        )
        self.assertEqual(anomalies, [])  # sod continuation is the normal case

    def test_missing_end_closes_at_unattested_midnight(self) -> None:
        # The 2025-06-19 raw-log shape: a start with no end message and no
        # sod-ACTIVE at the next midnight; a later TSA pairs normally.
        windows, anomalies = build_tsa_windows(
            _events(
                [
                    ("2025-06-19 14:30", "start"),
                    ("2025-06-22 06:15", "start"),
                    ("2025-06-22 06:20", "end"),
                ]
            )
        )
        self.assertEqual(
            windows,
            [
                (pd.Timestamp("2025-06-19 14:30"), pd.Timestamp("2025-06-20 00:00")),
                (pd.Timestamp("2025-06-22 06:15"), pd.Timestamp("2025-06-22 06:20")),
            ],
        )
        self.assertTrue(any("unattested midnight" in a for a in anomalies))

    def test_end_without_start_skipped(self) -> None:
        windows, anomalies = build_tsa_windows(_events([("2024-07-05 12:00", "end")]))
        self.assertEqual(windows, [])
        self.assertEqual(len(anomalies), 1)

    def test_unclosed_start_closes_at_corpus_end(self) -> None:
        windows, anomalies = build_tsa_windows(
            _events(
                [("2024-07-05 19:00", "start"), ("2024-07-05 21:00", "system_state")]
            )
        )
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0][1], pd.Timestamp("2024-07-05 21:00"))
        self.assertTrue(any("unclosed" in a for a in anomalies))


class TestHourlyConstruction(unittest.TestCase):
    def test_clock_is_8760_and_drops_feb29(self) -> None:
        clock = hourly_clock(2024)  # leap year
        self.assertEqual(len(clock), 8760)
        self.assertFalse(((clock.month == 2) & (clock.day == 29)).any())
        self.assertEqual(len(hourly_clock(2023)), 8760)

    def test_step_base(self) -> None:
        seny = _schedule().query("region == 'SENY' and version == 'v2021'")
        base = build_hourly_base(seny)
        np.testing.assert_array_equal(
            base[[0, 5, 6, 7, 21, 22, 23]], [1300, 1300, 1550, 1800, 1800, 1550, 1300]
        )

    def test_tsa_fraction_time_weighted(self) -> None:
        clock = hourly_clock(2024)
        windows = [(pd.Timestamp("2024-07-05 19:30"), pd.Timestamp("2024-07-05 21:15"))]
        frac = tsa_fraction(clock, windows)
        day_hours = (clock.month == 7) & (clock.day == 5)
        hb = clock.hour[day_hours]
        by_hb = dict(zip(hb, frac[day_hours]))
        self.assertAlmostEqual(by_hb[19], 0.5)
        self.assertAlmostEqual(by_hb[20], 1.0)
        self.assertAlmostEqual(by_hb[21], 0.25)
        self.assertAlmostEqual(frac.sum(), 1.75)


class TestDeriveYearEndToEnd(unittest.TestCase):
    def test_derived_csv_loads_through_the_lp_loader(self) -> None:
        events = _events([("2024-07-05 19:00", "start"), ("2024-07-05 21:00", "end")])
        frame, log = derive_year(_schedule(), events, 2024)
        # 3 mapped pairs (SENY 30T, NYC 10T, NYCA 30T); LI dropped with a log line.
        self.assertEqual(len(frame), 3 * 8760)
        self.assertTrue(
            any("dropped published row LI/total_10" in line for line in log)
        )

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "NYISO_reserve_requirements_2024.csv"
            frame.to_csv(path, index=False)
            out = load_nyiso_reserve_requirements(2024, hours=8760, path=path)

        self.assertEqual(
            set(out), {"seny_30min_total", "nyc_10min_total", "nyca_30min_total"}
        )
        seny = out["seny_30min_total"]
        # HB7 on Jul 5 (leap year: Feb 29 dropped, so hour-of-year matches the
        # non-leap clock): day-of-year without Feb 29 = 31+28+31+30+31+30+4 = 185.
        jul5 = 185 * 24
        self.assertAlmostEqual(seny[jul5 + 7], 1800.0)  # untouched peak step
        self.assertAlmostEqual(seny[jul5 + 19], 0.0)  # zeroed during TSA
        self.assertAlmostEqual(seny[jul5 + 20], 0.0)
        self.assertAlmostEqual(seny[jul5 + 21], 1800.0)  # window ends 21:00
        self.assertAlmostEqual(out["nyc_10min_total"][jul5 + 20], 0.0)
        self.assertAlmostEqual(
            out["nyca_30min_total"][jul5 + 20], 2620.0
        )  # no TSA flag
        self.assertAlmostEqual(seny[0], 1300.0)  # overnight base, Jan 1 HB0


if __name__ == "__main__":
    unittest.main()
