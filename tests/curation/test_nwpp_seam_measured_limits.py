"""NWPP-NEXT-22 seam headroom: BPA intertie spec, the seam-cap loader, the group builder.

Tiny synthetic BPA OPI and CAISO TRNS_USAGE folds are curated into a tmp
CLEAN_DIR, then ``nwpp_seam_limits_hourly`` is checked hour by hour:
fixed-PST clock, published-sign handling, the CAISO-share fallback before
OASIS coverage, and fail-closed on a missing partition. The group builder is
checked on a toy topology (orientation into the footprint, anchored-years
gate).
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from scripts.data import curate_transfer_interface_limits as cur
from scripts.lib.clean_io import validate_clean
from tests.helpers.base import CleanDirTestCase


def _bpa_year(year: int, coi_ns: float, coi_sn: float, bc_sn: float, bc_ns: float):
    """One calendar year of 15-minute BPA rows, Pacific prevailing period-ending stamps."""
    start = pd.Timestamp(f"{year}-01-01 00:15")
    stamps = pd.date_range(start, pd.Timestamp(f"{year + 1}-01-01 00:00"), freq="15min")
    # Prevailing wall clock as published: drop the spring-forward stamps that
    # never occur locally (02:15-03:00 on the DST start date).
    aware = stamps.tz_localize(
        "America/Los_Angeles", ambiguous=False, nonexistent="NaT"
    )
    stamps = stamps[~aware.isna()]
    ac = pd.DataFrame(
        {
            "path": "AC",
            "ts_end_local": stamps,
            "actual_mw": 1000.0,
            "ns_ttc_mw": coi_ns,
            "sn_ttc_mw": coi_sn,
            "loop_mw": 0.0,
        }
    )
    bc = pd.DataFrame(
        {
            "path": "BC",
            "ts_end_local": stamps,
            "actual_mw": 500.0,
            "ns_ttc_mw": bc_ns,
            "sn_ttc_mw": bc_sn,
            "loop_mw": np.nan,
        }
    )
    out = pd.concat([ac, bc], ignore_index=True)
    out["path"] = out["path"].astype("string")
    return out


def _caiso_year(year: int, start: str, otc: dict[tuple[str, str], float]):
    """CAISO TRNS_USAGE fold: given ITC/direction OTCs, hourly over Pacific [start, Jan 1)."""
    from scripts.data.fetch_caiso_trns_usage import ITEMS

    hours = pd.date_range(
        pd.Timestamp(start, tz="America/Los_Angeles"),
        pd.Timestamp(f"{year + 1}-01-01", tz="America/Los_Angeles"),
        freq="h",
        inclusive="left",
    ).tz_convert("UTC")
    frames = []
    for (ti, d), value in otc.items():
        w = pd.DataFrame(
            {
                "interval_start_utc": hours,
                "ti_id": ti,
                "ti_constraint_id": ti,
                "direction": d,
            }
        )
        for item in ITEMS:
            w[item] = 0.0
        w["OTC_MW"] = value
        frames.append(w)
    return pd.concat(frames, ignore_index=True)


class NwppSeamLimitsTest(CleanDirTestCase):
    """BPA spec curation + ``nwpp_seam_limits_hourly``."""

    def setUp(self):
        super().setUp()
        self.raw_root = self.tmp_path / "raw"
        (self.raw_root / "nwpp-intertie-otc").mkdir(parents=True)
        (self.raw_root / "caiso-trns-usage").mkdir(parents=True)

    def _bpa(self, year: int, **kw) -> None:
        args = dict(coi_ns=4500.0, coi_sn=-3000.0, bc_sn=2200.0, bc_ns=-2400.0)
        args.update(kw)
        _bpa_year(year, **args).to_parquet(
            self.raw_root / "nwpp-intertie-otc" / f"bpa_intertie_otc_{year}.parquet"
        )
        cur.curate(raw_root=self.raw_root, isos=["NWPP"])

    def _caiso(self, year: int, start: str) -> None:
        otc = {
            ("MALIN500_ISL", "I"): 2667.0,
            ("CASCADE_ITC", "I"): 80.0,
            ("MALIN500_ISL", "E"): 1700.0,
            ("CASCADE_ITC", "E"): 40.0,
        }
        _caiso_year(year, start, otc).to_parquet(
            self.raw_root / "caiso-trns-usage" / f"caiso_trns_usage_dam_{year}.parquet"
        )
        cur.curate(raw_root=self.raw_root, isos=["CAISO"])

    def test_bpa_spec_curates_four_series_on_fixed_pst(self):
        """Trivial: one year -> four dense series, faithful signs, hour = fixed PST."""
        self._bpa(2021)
        path = self.tmp_path / "clean" / "transfer-interface-limits" / "NWPP"
        files = sorted(path.glob("*.parquet"))
        self.assertEqual(
            [f.name for f in files], ["transfer-interface-limits_2021.parquet"]
        )
        validate_clean(files[0])
        df = pd.read_parquet(files[0])
        self.assertEqual(
            sorted(df["interface"].unique()),
            ["BC|NS|OTC", "BC|SN|OTC", "COI|NS|OTC", "COI|SN|OTC"],
        )
        self.assertTrue((df.groupby("interface").size() == 8760).all())
        sn = df[df["interface"] == "COI|SN|OTC"]
        self.assertTrue(np.allclose(sn["limit_mw"], -3000.0))
        # Fixed PST has no DST: no spring-forward fill, one source hour each
        # (a July hour is NOT shifted against a January one).
        self.assertTrue((df["n_source_rows"] >= 1).all())

    def test_share_fallback_without_caiso_partition(self):
        """Pre-2023 year: COI = 2/3 x BPA path; BC from BPA, signs to magnitudes."""
        from market_sim.data.transfer_interface_limits import nwpp_seam_limits_hourly

        self._bpa(2021)
        caps = nwpp_seam_limits_hourly(2021, 8760)
        coi_imp, coi_exp = caps["CAISO_COI"]
        bc_imp, bc_exp = caps["WECC_CAN"]
        self.assertTrue(np.allclose(coi_exp, 3000.0))  # 2/3 x 4500 N-S
        self.assertTrue(np.allclose(coi_imp, 2000.0))  # 2/3 x |-3000| S-N
        self.assertTrue(np.allclose(bc_exp, 2200.0))
        self.assertTrue(np.allclose(bc_imp, 2400.0))
        self.assertNotIn("CAISO_NEVP", caps)

    def test_caiso_otc_where_covered_share_elsewhere(self):
        """2024: CAISO OTC from its first hour (Mar 1 = PST hour 1416), share before."""
        from market_sim.data.transfer_interface_limits import nwpp_seam_limits_hourly

        self._bpa(2024)
        self._caiso(2024, "2024-03-01")
        coi_imp, coi_exp = nwpp_seam_limits_hourly(2024, 8760)["CAISO_COI"]
        self.assertAlmostEqual(coi_exp[1415], 3000.0)
        self.assertAlmostEqual(coi_exp[1416], 2747.0)  # MALIN 2667 + CASCADE 80
        self.assertAlmostEqual(coi_imp[1416], 1740.0)  # MALIN 1700 + CASCADE 40
        # A July hour lands on the fixed-PST clock (no gap from the DST shift).
        self.assertTrue(np.allclose(coi_exp[1416:], 2747.0))

    def test_positive_value_on_a_negative_published_limit_clamps_to_zero(self):
        """A sign-flipped posting never becomes a negative (forcing) cap."""
        from market_sim.data.transfer_interface_limits import nwpp_seam_limits_hourly

        self._bpa(2021, bc_ns=5.0)
        bc_imp, _ = nwpp_seam_limits_hourly(2021, 8760)["WECC_CAN"]
        self.assertTrue(np.allclose(bc_imp, 0.0))

    def test_missing_partitions_raise(self):
        """No NWPP partition, or a 2023+ year with no CAISO partition: fail closed."""
        from market_sim.data.transfer_interface_limits import nwpp_seam_limits_hourly

        with self.assertRaises(FileNotFoundError):
            nwpp_seam_limits_hourly(2021, 8760)
        self._bpa(2024)
        with self.assertRaises(FileNotFoundError):
            nwpp_seam_limits_hourly(2024, 8760)


def _links(*pairs):
    return [SimpleNamespace(from_zone=a, to_zone=b) for a, b in pairs]


def test_group_builder_orients_into_footprint_and_gates_unpriced_years():
    """COI: two border links (+1 from the seam zone, -1 into it); BC unpriced pre-2023."""
    from market_sim.model.interchange.spec import build_seam_limit_groups

    links = _links(
        ("NWPP-NW", "NWPP-OR"),
        ("NWPP_ext_COI", "NWPP-NW"),
        ("NWPP-OR", "NWPP_ext_COI"),
        ("NWPP_ext_BC", "NWPP-NW"),
    )
    T = 24
    caps = {
        "CAISO_COI": (np.full(T, 1800.0), np.full(T, 2700.0)),
        "WECC_CAN": (np.full(T, 2400.0), np.full(T, 2200.0)),
    }
    groups = build_seam_limit_groups("NWPP", links, caps, 2024)
    assert len(groups) == 2
    idx, upper, two_way, lower, signs = groups[0]
    assert idx.tolist() == [1, 2] and signs.tolist() == [1.0, -1.0]
    assert two_way is False
    assert np.allclose(upper, 1800.0) and np.allclose(lower, 2700.0)
    # 2021: WECC_CAN is priced only in anchored years -> no BC group.
    groups_2021 = build_seam_limit_groups("NWPP", links, caps, 2021)
    assert len(groups_2021) == 1 and groups_2021[0][0].tolist() == [1, 2]


def test_group_builder_refuses_an_unregistered_seam():
    """A cap for a seam with no zone of its own is a configuration error."""
    from market_sim.model.interchange.spec import build_seam_limit_groups

    with pytest.raises(ValueError):
        build_seam_limit_groups(
            "NWPP", _links(), {"WECC_SW": (np.zeros(1), np.zeros(1))}, 2024
        )


def test_group_rows_bound_net_seam_flow_both_ways():
    """Through the LP row builder: lower = -export cap, upper = import cap."""
    from market_sim.model.interchange.spec import build_seam_limit_groups
    from market_sim.model.lp.rows import _build_interface_rows

    T = 24
    links = _links(("NWPP_ext_COI", "NWPP-NW"), ("NWPP-OR", "NWPP_ext_COI"))
    caps = {"CAISO_COI": (np.arange(T, dtype=float), np.full(T, 2700.0))}
    groups = build_seam_limit_groups("NWPP", links, caps, 2024)
    layout = SimpleNamespace(T=T, vars_per_hour=5, _flow_off=3)
    block, lo, hi = _build_interface_rows(layout, groups)
    assert block.shape == (T, T * 5)
    assert np.allclose(hi, np.arange(T)) and np.allclose(lo, -2700.0)
    first = block.getrow(0).toarray().ravel()
    assert first[3] == 1.0 and first[4] == -1.0
