"""Tests for scripts/data/curate_transfer_interface_limits.py (PJM spec).

Builds a tiny synthetic Data Miner 2 ``transfer_limits_and_flows`` CSV, runs
``curate`` against a tmp raw root with CLEAN_DIR redirected (as in
tests/test_clean_io.py), and asserts the written Parquet is schema-valid and
the clock reconciliation is correct: UTC -> EPT wall clock, the DST
fall-back repeat merged (n_source_rows = 2, mean limit), the spring-forward
hour filled by interpolation (n_source_rows = 0, transfer null), Feb 29
dropped, and the frame dense (8760 rows per interface).
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from scripts.data import curate_transfer_interface_limits as cur
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_HEADER = (
    "datetime_beginning_utc,datetime_beginning_ept,datetime_ending_utc,"
    "datetime_ending_ept,transfer_limit_area,transfers,transfer_limit"
)


def _csv(rows: list[tuple[str, str, float, float]]) -> str:
    """Data Miner 2 CSV text from (utc_ts, area, transfers, limit) rows.

    The EPT / ending columns are carried in the real feed but unused by the
    parser; blank them.
    """
    lines = [_HEADER]
    for ts, area, xfer, lim in rows:
        lines.append(f"{ts},,,,{area},{xfer},{lim}")
    return "\n".join(lines) + "\n"


def _full_year_rows(
    year: int, area: str, limit: float
) -> list[tuple[str, str, float, float]]:
    """One row per UTC hour spanning the EPT calendar year (like the feed)."""
    # EPT (America/New_York) midnight Jan 1 in UTC through the following
    # midnight — exactly what the committed PJM drops span.
    start = pd.Timestamp(f"{year}-01-01", tz="America/New_York")
    end = pd.Timestamp(f"{year + 1}-01-01", tz="America/New_York")
    hours = pd.date_range(start, end, freq="h", inclusive="left").tz_convert("UTC")
    return [(ts.strftime("%m/%d/%Y %I:%M:%S %p"), area, 100.0, limit) for ts in hours]


class CurateTransferInterfaceLimitsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        (self.raw_root / "iso-specific-transmission").mkdir(parents=True)
        # Redirect CLEAN_DIR so writes never touch the repo.
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _write_raw(self, year: int, text: str) -> None:
        path = (
            self.raw_root
            / "iso-specific-transmission"
            / f"PJM_{year}_transfer_limits_and_flows.csv"
        )
        path.write_text(text)

    def test_trivial_single_interface_year(self):
        """1 interface, constant limit: dense 8760 rows, schema-valid."""
        self._write_raw(
            2023, _csv(_full_year_rows(2023, "AEP/DOM Post-Contingency", 4000.0))
        )
        written = cur.curate(raw_root=self.raw_root, isos=["PJM"])
        self.assertEqual(len(written), 1)
        validate_clean(written[0])
        df = pd.read_parquet(written[0])
        self.assertEqual(len(df), 8760)
        self.assertEqual(df["iso"].unique().tolist(), ["PJM"])
        self.assertTrue((df["hour"].to_numpy() == np.arange(8760)).all())
        self.assertTrue(np.allclose(df["limit_mw"], 4000.0))

    def test_dst_merge_fill_and_leap_drop(self):
        """DST fall-back merges (n=2), spring-forward fills (n=0), Feb 29 drops."""
        rows = _full_year_rows(2024, "AP-South Pre-Contingency", 5000.0)
        # Make the two UTC hours mapping to the EPT fall-back repeat (Nov 3
        # 2024 01:00 EDT + 01:00 EST = 05:00 + 06:00 UTC) distinguishable.
        utc = pd.to_datetime([r[0] for r in rows], format="%m/%d/%Y %I:%M:%S %p")
        rows = [
            (
                ts_s,
                area,
                xfer,
                6000.0
                if ts
                in (
                    pd.Timestamp("2024-11-03 05:00:00"),
                    pd.Timestamp("2024-11-03 06:00:00"),
                )
                else lim,
            )
            for (ts_s, area, xfer, lim), ts in zip(rows, utc)
        ]
        self._write_raw(2024, _csv(rows))
        written = cur.curate(raw_root=self.raw_root, isos=["PJM"])
        self.assertEqual(len(written), 1)
        validate_clean(written[0])
        df = pd.read_parquet(written[0]).set_index("hour")
        self.assertEqual(len(df), 8760)  # leap source year still lands on 8760

        # Feb 29 dropped: the local calendar column never shows Feb 29.
        local = df["interval_start_local"]
        self.assertFalse(((local.dt.month == 2) & (local.dt.day == 29)).any())

        # Fall-back: Nov 3 2024 01:00 EPT carries both source rows, merged.
        fb = df[(local.dt.month == 11) & (local.dt.day == 3) & (local.dt.hour == 1)]
        self.assertEqual(fb["n_source_rows"].tolist(), [2])
        self.assertAlmostEqual(fb["limit_mw"].iloc[0], 6000.0)

        # Spring-forward: Mar 10 2024 02:00 EPT never occurs — filled row.
        sf = df[(local.dt.month == 3) & (local.dt.day == 10) & (local.dt.hour == 2)]
        self.assertEqual(sf["n_source_rows"].tolist(), [0])
        self.assertAlmostEqual(sf["limit_mw"].iloc[0], 5000.0)  # interpolated
        self.assertTrue(sf["transfer_mw"].isna().all())

        # Everything else is a plain 1-source hour.
        self.assertEqual(int((df["n_source_rows"] == 1).sum()), 8758)

    def test_iso_filter_no_op(self):
        """Requesting an ISO with no registered spec writes nothing."""
        self._write_raw(2023, _csv(_full_year_rows(2023, "Cleveland", 3000.0)))
        self.assertEqual(cur.curate(raw_root=self.raw_root, isos=["ERCOT"]), [])


class PjmInterfaceTtcHourlyTest(unittest.TestCase):
    """Consumer seam: market_sim.data.transfer_interface_limits."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        (self.raw_root / "iso-specific-transmission").mkdir(parents=True)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate_fixture(self, year: int) -> None:
        """Two mapped series (AP-South pre+post, min applies) + one negative."""
        rows = (
            _full_year_rows(year, "AP-South Pre-Contingency", 4000.0)
            + _full_year_rows(year, "AP-South Post-Contingency", 4500.0)
            + _full_year_rows(year, "Bedington-BlackOak Pre-Contingency", -50.0)
            + _full_year_rows(year, "Bedington-BlackOak Post-Contingency", 1900.0)
        )
        path = (
            self.raw_root
            / "iso-specific-transmission"
            / f"PJM_{year}_transfer_limits_and_flows.csv"
        )
        path.write_text(_csv(rows))
        cur.curate(raw_root=self.raw_root, isos=["PJM"])

    def test_mapped_links_hourly_unmapped_static(self):
        """Mapped links follow min(pre,post) clamped at 0; the rest static."""
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.transfer_interface_limits import (
            pjm_interface_ttc_hourly,
        )

        self._curate_fixture(2023)
        cfg = get_iso_config("PJM")
        ttc = np.array([link.ttc_mw for link in cfg.links])
        out = pjm_interface_ttc_hourly(ttc, cfg, 2023, 8760)
        self.assertIsNotNone(out)
        ttc_hourly, ttc_import = out
        self.assertEqual(ttc_hourly.shape, (8760, len(cfg.links)))
        # The reverse-direction bound is exactly the static array.
        self.assertTrue(np.array_equal(ttc_import, ttc))

        idx = {(l.from_zone, l.to_zone): i for i, l in enumerate(cfg.links)}
        # AP-South -> West_APS->SWMAAC rides min(4000, 4500) = 4000.
        ap = idx[("PJM_West_APS", "PJM_SWMAAC")]
        self.assertTrue(np.allclose(ttc_hourly[:, ap], 4000.0))
        # Bedington-BlackOak: min(-50, 1900) = -50, clamped to 0 (no secure
        # forward transfer), never a negative bound.
        bb = idx[("PJM_West_APS", "PJM_Central_PA")]
        self.assertTrue(np.allclose(ttc_hourly[:, bb], 0.0))
        # A series absent from the fixture (Average Eastern) leaves its link
        # at the static rating; so do the unmapped links.
        east = idx[("PJM_Central_PA", "PJM_EMAAC")]
        self.assertTrue(np.allclose(ttc_hourly[:, east], ttc[east]))
        unmapped = idx[("PJM_SWMAAC", "PJM_EMAAC")]
        self.assertTrue(np.allclose(ttc_hourly[:, unmapped], ttc[unmapped]))

    def test_missing_partition_returns_none(self):
        """No clean partition -> None, so callers keep the static path."""
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.transfer_interface_limits import (
            pjm_interface_ttc_hourly,
        )

        cfg = get_iso_config("PJM")
        ttc = np.array([link.ttc_mw for link in cfg.links])
        self.assertIsNone(pjm_interface_ttc_hourly(ttc, cfg, 2023, 8760))


class PjmEastInterfaceCutTest(unittest.TestCase):
    """The measured joint EMAAC-import cut (pjm_east_interface_cut) seam."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        (self.raw_root / "iso-specific-transmission").mkdir(parents=True)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate_fixture(self, year: int, limit: float) -> None:
        rows = _full_year_rows(year, "Average Eastern", limit)
        path = (
            self.raw_root
            / "iso-specific-transmission"
            / f"PJM_{year}_transfer_limits_and_flows.csv"
        )
        path.write_text(_csv(rows))
        cur.curate(raw_root=self.raw_root, isos=["PJM"])

    def test_eastern_series_hourly(self):
        """The joint-cut cap is the published Average Eastern series."""
        from market_sim.data.transfer_interface_limits import (
            pjm_eastern_interface_hourly,
        )

        self._curate_fixture(2023, 8200.0)
        lim = pjm_eastern_interface_hourly(2023, 8760)
        self.assertIsNotNone(lim)
        self.assertEqual(lim.shape, (8760,))
        self.assertTrue(np.allclose(lim, 8200.0))

    def test_negative_limit_clamps_to_zero(self):
        from market_sim.data.transfer_interface_limits import (
            pjm_eastern_interface_hourly,
        )

        self._curate_fixture(2023, -100.0)
        lim = pjm_eastern_interface_hourly(2023, 8760)
        self.assertIsNotNone(lim)
        self.assertTrue(np.allclose(lim, 0.0))

    def test_missing_series_returns_none(self):
        """A partition without Average Eastern -> None (group skipped)."""
        from market_sim.data.transfer_interface_limits import (
            pjm_eastern_interface_hourly,
        )

        rows = _full_year_rows(2023, "AP-South Pre-Contingency", 4000.0)
        path = (
            self.raw_root
            / "iso-specific-transmission"
            / "PJM_2023_transfer_limits_and_flows.csv"
        )
        path.write_text(_csv(rows))
        cur.curate(raw_root=self.raw_root, isos=["PJM"])
        self.assertIsNone(pjm_eastern_interface_hourly(2023, 8760))
        # No partition at all -> also None.
        clean_io.paths.CLEAN_DIR = Path(self._tmp.name) / "empty-clean"
        self.assertIsNone(pjm_eastern_interface_hourly(2023, 8760))

    def test_group_builder_indices_signs_one_sided(self):
        """One one-sided group over exactly the two EMAAC import links."""
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.model.transmission import (
            PJM_EAST_CUT_LINKS,
            build_pjm_east_interface_cut_groups,
        )

        cfg = get_iso_config("PJM")
        lim = np.full(8760, 8200.0)
        groups = build_pjm_east_interface_cut_groups(cfg.links, lim)
        self.assertEqual(len(groups), 1)
        idx, cap, two_way, lower, signs = groups[0]
        pairs = {(cfg.links[i].from_zone, cfg.links[i].to_zone) for i in idx}
        self.assertEqual(pairs, set(PJM_EAST_CUT_LINKS))
        self.assertTrue(np.allclose(cap, 8200.0))
        self.assertFalse(two_way)  # one-sided: never caps westward flow
        self.assertIsNone(lower)
        self.assertTrue(np.allclose(signs, 1.0))  # both links point into EMAAC

    def test_group_builder_empty_without_cut_links(self):
        """A topology without the cut links yields no group (byte-identical)."""
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.model.transmission import (
            build_pjm_east_interface_cut_groups,
        )

        cfg = get_iso_config("ERCOT")
        self.assertEqual(
            build_pjm_east_interface_cut_groups(cfg.links, np.full(8760, 1.0)),
            [],
        )

    def test_comed_5004_5005_mis_attribution_removed(self):
        """Regression pin (pjm-cong-1): PJM Manual 03 §3.8 defines 5004/5005
        as the Keystone/Conemaugh–Juniata 500 kV corridor (Pennsylvania) — it
        must never again be applied to the ComEd boundary."""
        from market_sim.config.constants import (
            PJM_INTERFACE_LINK_MAP,
            PJM_MEASURED_INTERNAL_TTC,
        )

        self.assertNotIn(("PJM_ComEd", "PJM_AEP_Ohio"), PJM_INTERFACE_LINK_MAP)
        self.assertNotIn(("PJM_ComEd", "PJM_AEP_Ohio"), PJM_MEASURED_INTERNAL_TTC)
        for series in {s for v in PJM_INTERFACE_LINK_MAP.values() for s in v}:
            self.assertNotIn("50045005", series)


if __name__ == "__main__":
    unittest.main()
