"""Tests for the ``seam-neighbour-price`` curation (NYISO-NEXT-10).

Trivial case first (one node, one hour per market), then the clock cases that
decide whether a spread is aligned at all: NYISO's doubled fall-back hour,
IESO's EST-only clock, and the CAD -> USD conversion.
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.data.curate_seam_neighbour_price import curate  # noqa: E402
from tests.helpers.base import RawFixtureTestCase  # noqa: E402
from tests.helpers.clean_asserts import (  # noqa: E402
    assert_clean_valid,
    read_clean_or_fail,
)

DT = "seam-neighbour-price"


def _utc(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz="UTC")


class SeamNeighbourPriceCurationTest(RawFixtureTestCase):
    """Curate a hand-built raw tree for each registered market."""

    def setUp(self) -> None:
        super().setUp()
        root = self.raw_dir / "seam-neighbour-price"
        for sub in ("nyiso", "pjm", "neiso", "ieso"):
            (root / sub).mkdir(parents=True)
        self.root = root

    def _nyiso(self, text: str, year: int = 2023) -> None:
        p = self.root / "nyiso" / f"NYISO_dam_proxy_lbmp_{year}.csv.gz"
        p.write_bytes(gzip.compress(text.encode()))

    def test_trivial_one_hour_each_market(self) -> None:
        self._nyiso(
            "date,seq,time_stamp,name,ptid,lbmp,losses,congestion\n"
            "2023-01-01,0,01/01/2023 00:00,NPX,61845,30.0,0.5,-1.0\n"
        )
        (self.root / "pjm" / "PJM_ny_interface_lmp_2023.csv").write_text(
            "datetime_beginning_utc,datetime_beginning_ept,pnode_id,pnode_name,market,"
            "total_lmp,congestion_price,marginal_loss_price\n"
            "2023-01-01T05:00:00,2023-01-01T00:00:00,5413134,NYIS,DA,25.0,0.0,0.1\n"
        )
        (self.root / "neiso" / "NEISO_ny_ext_node_lmp_2023.csv").write_text(
            "date,hour_ending,seq,location_id,location,da_lmp,rt_lmp\n"
            "2023-01-01,01,0,4011,.I.ROSETON 345 1,28.0,29.0\n"
        )
        (self.root / "ieso" / "IESO_hourly_price_2023.csv").write_text(
            "date,hour_ending_est,hoep_cad,ontario_mcp_cad,new_york_mcp_cad\n"
            "2023-01-01,1,27.0,27.0,27.0\n"
        )
        (self.root / "ieso" / "BOC_FXUSDCAD.csv").write_text(
            "date,usd_cad\n2022-12-30,1.35\n2023-01-03,1.36\n"
        )
        written = curate(raw_root=self.raw_dir)
        self.assertEqual(len(written), 4)
        for iso in ("NYISO", "PJM", "NEISO", "IESO"):
            assert_clean_valid(DT, iso=iso, year=2023)

        ny = read_clean_or_fail(DT, iso="NYISO", year=2023)
        self.assertEqual(ny["interval_start_utc"].iloc[0], _utc("2023-01-01 05:00"))
        self.assertEqual(ny["seam_group"].iloc[0], "NE_AC")

        ne = read_clean_or_fail(DT, iso="NEISO", year=2023)
        self.assertEqual(sorted(ne["market"]), ["DA", "RT"])
        self.assertTrue((ne["interval_start_utc"] == _utc("2023-01-01 05:00")).all())

        pj = read_clean_or_fail(DT, iso="PJM", year=2023)
        self.assertEqual(pj["interval_start_utc"].iloc[0], _utc("2023-01-01 05:00"))

        ie = read_clean_or_fail(DT, iso="IESO", year=2023)
        hoep = ie[ie["node"] == "HOEP"].iloc[0]
        # HE1 EST begins 00:00 EST = 05:00 UTC; 2023-01-01 is a holiday, so the
        # 2022-12-30 rate carries forward.
        self.assertEqual(hoep["interval_start_utc"], _utc("2023-01-01 05:00"))
        self.assertAlmostEqual(hoep["price_usd"], 27.0 / 1.35)
        self.assertEqual(hoep["currency"], "CAD")

    def test_nyiso_fall_back_hour_is_two_distinct_utc_hours(self) -> None:
        self._nyiso(
            "date,seq,time_stamp,name,ptid,lbmp,losses,congestion\n"
            "2023-11-05,0,11/05/2023 00:00,WEST,61752,20.0,0,0\n"
            "2023-11-05,1,11/05/2023 01:00,WEST,61752,21.0,0,0\n"
            "2023-11-05,2,11/05/2023 01:00,WEST,61752,22.0,0,0\n"
            "2023-11-05,3,11/05/2023 02:00,WEST,61752,23.0,0,0\n"
        )
        curate(raw_root=self.raw_dir, isos=["NYISO"])
        ny = read_clean_or_fail(DT, iso="NYISO", year=2023)
        got = list(ny.sort_values("price")["interval_start_utc"])
        self.assertEqual(
            got,
            [_utc("2023-11-05 04:00"), _utc("2023-11-05 05:00"),
             _utc("2023-11-05 06:00"), _utc("2023-11-05 07:00")],
        )  # fmt: skip
        self.assertTrue(ny["seam_group"].isna().all())

    def test_absent_year_is_skipped_not_fatal(self) -> None:
        self.assertEqual(curate(raw_root=self.raw_dir, isos=["PJM"]), [])
