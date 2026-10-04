"""Tests for the ``uc-params`` derive (scripts/lib/uc_params, lane UC-1).

Trivial case first: one synthetic CAMPD extract with a two-unit combined
cycle that runs a known on/off pattern with an affine heat-input curve, so
every statistic the derive measures has a hand-computable answer. The
``CleanDirTestCase`` base redirects ``paths.CLEAN_DIR`` to a tempdir.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.data import derive_uc_cluster_params as duc
from scripts.lib import uc_params as up
from tests.helpers import CleanDirTestCase, assert_clean_valid, read_clean_or_fail

_STATE = "ZZ"
_ISO = "ZZTEST"


def _write_fixture(raw_root, year: int, n_hours: int = 24 * 20) -> None:
    """Two CC units at facility 777: on 14 h / off 10 h daily, heat = 50 + 8·load."""
    hours = np.arange(n_hours)
    on = (hours % 24) < 14
    rows = []
    for unit, cap in (("U1", 100.0), ("U2", 150.0)):
        load = np.where(on, cap * (0.6 + 0.4 * ((hours % 14) / 13.0)), 0.0)
        heat = np.where(on, 50.0 + 8.0 * load, 0.0)
        rows.append(
            pd.DataFrame(
                {
                    "stateCode": _STATE,
                    "facilityName": "Toy CC",
                    "facilityId": "777",
                    "unitId": unit,
                    "date": pd.Timestamp(f"{year}-01-01")
                    + pd.to_timedelta(hours // 24, "D"),
                    "hour": hours % 24,
                    "opTime": np.where(on, 1.0, 0.0),
                    "grossLoad": np.where(on, load, np.nan),
                    "steamLoad": np.nan,
                    "so2Mass": np.nan,
                    "co2Mass": np.nan,
                    "noxMass": np.nan,
                    "heatInput": np.where(on, heat, np.nan),
                    "primaryFuelInfo": "Pipeline Natural Gas",
                    "unitType": "Combined cycle",
                    "programCodeInfo": "ARP",
                }
            )
        )
    # A coal boiler always on, so the family vocabulary is exercised too.
    rows.append(
        pd.DataFrame(
            {
                "stateCode": _STATE,
                "facilityName": "Toy Coal",
                "facilityId": "888",
                "unitId": "1",
                "date": pd.Timestamp(f"{year}-01-01")
                + pd.to_timedelta(hours // 24, "D"),
                "hour": hours % 24,
                "opTime": 1.0,
                "grossLoad": 400.0 + 100.0 * np.sin(hours / 7.0),
                "steamLoad": np.nan,
                "so2Mass": np.nan,
                "co2Mass": np.nan,
                "noxMass": np.nan,
                "heatInput": 1000.0 + 9.5 * (400.0 + 100.0 * np.sin(hours / 7.0)),
                "primaryFuelInfo": "Coal",
                "unitType": "Tangentially-fired",
                "programCodeInfo": "ARP",
            }
        )
    )
    out = raw_root / "campd-unit-level"
    out.mkdir(parents=True, exist_ok=True)
    pd.concat(rows, ignore_index=True).to_parquet(
        out / f"{_STATE}_{year}.parquet", index=False
    )


class TestClassify(CleanDirTestCase):
    def test_family_vocabulary(self):
        self.assertEqual(
            up.classify_unit("Combined cycle", "Pipeline Natural Gas"), "cc"
        )
        self.assertEqual(up.classify_unit("Combustion turbine", "Diesel Oil"), "ct")
        self.assertEqual(up.classify_unit("Tangentially-fired", "Coal"), "coal")
        self.assertEqual(
            up.classify_unit("Dry bottom wall-fired boiler", "Pipeline Natural Gas"),
            "st_gas",
        )

    def test_runs_and_gaps(self):
        mask = np.array([0, 1, 1, 1, 0, 0, 1, 1, 0], dtype=bool)
        runs, gaps = up._runs_and_gaps(mask)
        self.assertEqual(runs.tolist(), [3, 2])
        self.assertEqual(gaps.tolist(), [2])


class TestDerive(CleanDirTestCase):
    def setUp(self):
        super().setUp()
        up.load_registry()
        up.register(up.IsoSpec(iso=_ISO, campd_states=(_STATE,)))
        self.raw = self.tmp_path / "raw"
        _write_fixture(self.raw, up.POOLED_VINTAGES[0])

    def test_trivial_two_unit_cc(self):
        written = duc.curate(raw_root=self.raw, isos=[_ISO])
        self.assertEqual(len(written), 1)
        assert_clean_valid(up.DATATYPE, iso=_ISO)
        df = read_clean_or_fail(up.DATATYPE, iso=_ISO)
        cc = df[(df["plant_code"] == 777) & (df["uc_class"] == "cc")].iloc[0]
        self.assertEqual(int(cc["n_units"]), 2)
        # HSL ~ 250 MW (both units at full output), LSL ~ 150 MW (both at 60 %).
        self.assertAlmostEqual(float(cc["hsl_mw"]), 250.0, delta=2.0)
        self.assertAlmostEqual(float(cc["mlf"]), 0.6, delta=0.02)
        # 14 h on, 10 h off every day.
        self.assertEqual(int(cc["ut_h"]), 14)
        self.assertEqual(int(cc["dt_h"]), 10)
        self.assertEqual(int(cc["n_runs"]), 20)
        # Two intercepts of 50 MMBtu/h each, a perfect fit.
        self.assertEqual(int(cc["noload_units_fitted"]), 2)
        self.assertAlmostEqual(float(cc["noload_mmbtu_h"]), 100.0, delta=1e-6)
        self.assertAlmostEqual(float(cc["noload_r2_median"]), 1.0, delta=1e-9)
        coal = df[(df["plant_code"] == 888) & (df["uc_class"] == "coal")].iloc[0]
        self.assertEqual(int(coal["n_runs"]), 1)
        self.assertAlmostEqual(float(coal["noload_mmbtu_h"]), 1000.0, delta=1e-6)
        # One class-fallback row per family present.
        fallback = df[df["plant_code"] == 0]
        self.assertEqual(sorted(fallback["uc_class"]), ["cc", "coal"])

    def test_rerun_is_idempotent(self):
        first = duc.curate(raw_root=self.raw, isos=[_ISO])
        a = read_clean_or_fail(up.DATATYPE, iso=_ISO)
        duc.curate(raw_root=self.raw, isos=[_ISO])
        b = read_clean_or_fail(up.DATATYPE, iso=_ISO)
        pd.testing.assert_frame_equal(a, b)
        self.assertTrue(first[0].is_file())

    def test_missing_footprint_skips(self):
        up.register(up.IsoSpec(iso="ZZNONE", campd_states=("QQ",)))
        self.assertEqual(duc.curate(raw_root=self.raw, isos=["ZZNONE"]), [])
