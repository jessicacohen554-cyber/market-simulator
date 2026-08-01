"""Unit tests for the shared dam-public-bids RLE expander (caiso-152).

``scripts.lib.dam_public_bids.expand_rle`` is the ISO-generic seam that turns
each ISO's run-length-encoded ``[start, stop)`` bid rows into the datatype's
declared per-hour grain. These cases pin the properties every ISO parser
relies on: single-hour rows are untouched, multi-hour rows repeat their
payload once per hour in ascending order, a missing or degenerate stop stamp
degrades to one hour rather than dropping the row, and payload columns are
never split or rescaled across the expansion.
"""

import unittest

import pandas as pd

from scripts.lib.dam_public_bids import expand_rle


def _frame(starts: list[str], mw: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "interval_start_utc": pd.to_datetime(pd.Series(starts), utc=True),
            "segment_mw": mw,
        }
    )


class TestExpandRle(unittest.TestCase):
    def test_single_hour_rows_are_unchanged(self) -> None:
        f = _frame(["2024-01-10T00:00:00Z", "2024-01-10T01:00:00Z"], [5.0, 6.0])
        out = expand_rle(
            f, pd.to_datetime(["2024-01-10T01:00Z", "2024-01-10T02:00Z"], utc=True)
        )
        self.assertEqual(len(out), 2)
        self.assertEqual(list(out.segment_mw), [5.0, 6.0])
        self.assertEqual(str(out.interval_start_utc.dt.tz), "UTC")

    def test_multi_hour_row_repeats_its_payload_per_hour(self) -> None:
        f = _frame(["2024-01-10T00:00:00Z"], [7.5])
        out = expand_rle(f, pd.to_datetime(["2024-01-10T04:00Z"], utc=True))
        self.assertEqual(len(out), 4)
        # The quantity repeats — it is never summed or spread across the range.
        self.assertEqual(list(out.segment_mw), [7.5] * 4)
        self.assertEqual(
            [str(t) for t in out.interval_start_utc],
            [
                "2024-01-10 00:00:00+00:00",
                "2024-01-10 01:00:00+00:00",
                "2024-01-10 02:00:00+00:00",
                "2024-01-10 03:00:00+00:00",
            ],
        )

    def test_a_range_keeps_its_hours_adjacent_and_ordered(self) -> None:
        f = _frame(
            ["2024-01-10T00:00:00Z", "2024-01-10T10:00:00Z", "2024-01-10T20:00:00Z"],
            [1.0, 2.0, 3.0],
        )
        stop = pd.to_datetime(
            ["2024-01-10T02:00Z", "2024-01-10T11:00Z", "2024-01-10T23:00Z"], utc=True
        )
        out = expand_rle(f, stop)
        self.assertEqual(list(out.segment_mw), [1.0, 1.0, 2.0, 3.0, 3.0, 3.0])

    def test_missing_or_degenerate_stop_keeps_one_hour_never_drops(self) -> None:
        f = _frame(
            ["2024-01-10T00:00:00Z", "2024-01-10T05:00:00Z", "2024-01-10T09:00:00Z"],
            [1.0, 2.0, 3.0],
        )
        # null stop; stop == start (zero span); stop BEFORE start (negative span)
        stop = pd.to_datetime(
            [None, "2024-01-10T05:00Z", "2024-01-10T08:00Z"], utc=True
        )
        out = expand_rle(f, stop)
        self.assertEqual(len(out), 3)
        self.assertEqual(list(out.segment_mw), [1.0, 2.0, 3.0])
        self.assertEqual(
            [str(t) for t in out.interval_start_utc],
            [
                "2024-01-10 00:00:00+00:00",
                "2024-01-10 05:00:00+00:00",
                "2024-01-10 09:00:00+00:00",
            ],
        )

    def test_expansion_crosses_a_dst_boundary_on_the_utc_clock(self) -> None:
        # 2024-03-10 is the US spring-forward. OASIS stamps are exact UTC and
        # spans are whole UTC hours, so expansion walks the UTC clock and can
        # neither skip nor repeat an hour — the caiso-151 clock discipline
        # (convert to US/Pacific downstream, never expand on local time).
        f = _frame(["2024-03-10T08:00:00Z"], [4.0])
        out = expand_rle(f, pd.to_datetime(["2024-03-11T08:00Z"], utc=True))
        self.assertEqual(len(out), 24)
        self.assertEqual(
            str(out.interval_start_utc.iloc[-1]), "2024-03-11 07:00:00+00:00"
        )
        gaps = out.interval_start_utc.diff().dropna().unique()
        self.assertEqual(list(gaps), [pd.Timedelta(hours=1)])
        # Local wall time on that day skips 02:00 PST -> 03:00 PDT: 24 UTC
        # hours therefore span 23 distinct local hours-of-day, not 24.
        local = out.interval_start_utc.dt.tz_convert("US/Pacific")
        self.assertEqual(local.dt.hour.nunique(), 23)

    def test_empty_frame_round_trips(self) -> None:
        f = _frame([], [])
        out = expand_rle(f, pd.to_datetime(pd.Series([], dtype="object"), utc=True))
        self.assertEqual(len(out), 0)


if __name__ == "__main__":
    unittest.main()
