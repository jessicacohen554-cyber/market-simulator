"""Curation of ``flowgate-limits-at-bind`` (SPP RTBM effective limits) on a tiny fixture."""

from __future__ import annotations

import gzip

from scripts.data import curate_flowgate_limits_at_bind as curate_mod
from tests.helpers import assert_clean_valid, read_clean_or_fail
from tests.helpers.base import CleanDirTestCase

_HEADER = (
    "Interval,GMTIntervalEnd,Constraint Name,Constraint Type,NERCID,TLR Level,State,"
    "Shadow Price,Monitored Facility,Contingent Facility, Source Limit,"
    " Realtime Effective Limit, Initial Effective Limit\n"
)


def _row(
    end_utc: str, state: str, sp: str, src: str, eff: str, name: str = "FG1"
) -> str:
    """One RTBM-EFFLIMIT data line (interval-end stamps, as SPP posts them)."""
    return f"x,{end_utc},{name},FG,1,CME,{state},{sp},LN A - B,BASE,{src},{eff},\n"


class TestCurateFlowgateLimitsAtBind(CleanDirTestCase):
    """Interval -> hour collapse, state filter and limit statistics."""

    def _write(self, lines: list[str]) -> None:
        raw = self.tmp_path / "raw" / "spp-effective-limits"
        raw.mkdir(parents=True)
        with gzip.open(raw / "rtbm_efflimit_bound_2023.csv.gz", "wt") as fh:
            fh.write(_HEADER + "".join(lines))

    def test_single_interval(self) -> None:
        """One binding interval -> one row with its own limits."""
        self._write([_row("08/10/2023 15:05:00", "BINDING", "-10", "100", "95")])
        curate_mod.curate(raw_root=self.tmp_path / "raw", isos=["SPP"], years=[2023])
        assert_clean_valid("flowgate-limits-at-bind", iso="SPP", year=2023, market="rt")
        df = read_clean_or_fail(
            "flowgate-limits-at-bind", iso="SPP", year=2023, market="rt"
        )
        self.assertEqual(len(df), 1)
        r = df.iloc[0]
        self.assertEqual(str(r.hour_start_utc), "2023-08-10 15:00:00+00:00")
        self.assertEqual((r.n_binding_intervals, r.n_breached_intervals), (1, 0))
        self.assertEqual((r.source_limit_mw, r.effective_limit_mw), (100.0, 95.0))

    def test_interval_end_and_states(self) -> None:
        """An interval ending on the hour belongs to the hour before; ACTIVATED is dropped."""
        self._write(
            [
                _row("08/10/2023 15:05:00", "BINDING", "-10", "100", "90"),
                _row("08/10/2023 16:00:00", "BREACHED", "-30", "100", "80"),
                _row("08/10/2023 16:05:00", "ACTIVATED", "0", "100", "70"),
                _row("08/10/2023 16:05:00", "BINDING", "-5", "200", "150", name="FG2"),
            ]
        )
        curate_mod.curate(raw_root=self.tmp_path / "raw", isos=["SPP"], years=[2023])
        df = read_clean_or_fail(
            "flowgate-limits-at-bind", iso="SPP", year=2023, market="rt"
        )
        self.assertEqual(len(df), 2)
        fg1 = df[df.constraint_name == "FG1"].iloc[0]
        self.assertEqual(str(fg1.hour_start_utc), "2023-08-10 15:00:00+00:00")
        self.assertEqual((fg1.n_binding_intervals, fg1.n_breached_intervals), (1, 1))
        self.assertEqual(
            (fg1.effective_limit_mw, fg1.effective_limit_min_mw), (85.0, 80.0)
        )
        self.assertEqual(fg1.shadow_price_mean_usd_mwh, -20.0)
        fg2 = df[df.constraint_name == "FG2"].iloc[0]
        self.assertEqual(str(fg2.hour_start_utc), "2023-08-10 16:00:00+00:00")

    def test_exact_repeat_counts_once(self) -> None:
        """A line SPP posted twice is one interval."""
        line = _row("08/10/2023 15:05:00", "BINDING", "-10", "100", "95")
        self._write([line, line])
        curate_mod.curate(raw_root=self.tmp_path / "raw", isos=["SPP"], years=[2023])
        df = read_clean_or_fail(
            "flowgate-limits-at-bind", iso="SPP", year=2023, market="rt"
        )
        self.assertEqual(int(df.iloc[0].n_binding_intervals), 1)

    def test_missing_year_is_skipped(self) -> None:
        """No raw extraction for the year -> nothing written."""
        self._write([_row("08/10/2023 15:05:00", "BINDING", "-10", "100", "95")])
        out = curate_mod.curate(
            raw_root=self.tmp_path / "raw", isos=["SPP"], years=[2024]
        )
        self.assertEqual(out, [])
