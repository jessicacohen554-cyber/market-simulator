"""Pin the multi-class bench attribution split (nyiso-88 §5 fix).

Two halves, per the lane charter:

* a synthetic two-class plant's measured energy lands in BOTH classes in
  proportion to the stated basis (unit-level hourly shares first, EIA-923
  monthly next, nameplate proration last), with the slice sum equal to the
  plant series in every hour;
* a single-class plant is BYTE-UNCHANGED — bare key, same entry, and a bench
  part containing only single-class plants round-trips byte-identically
  through the frozen codec (the important half).

Hermetic: pure functions of :mod:`scripts.lib.bench_multiclass` plus the
:mod:`scripts.lib.backcast_artifacts` codec — no repo data, no fleet build.
"""

import unittest

import numpy as np

from scripts.lib import backcast_artifacts as ba
from scripts.lib import bench_multiclass as bm

_T = 8760


class TestSliceKeys(unittest.TestCase):
    def test_round_trip(self):
        self.assertEqual(bm.slice_key(2500), "2500")
        self.assertEqual(bm.slice_key(2500, "ST_GAS"), "2500:ST_GAS")
        self.assertEqual(bm.parse_key("2500"), (2500, None))
        self.assertEqual(bm.parse_key("2500:ST_GAS"), (2500, "ST_GAS"))
        self.assertEqual(bm.plant_code_of_key("2500:CC_REGULAR"), 2500)


class TestUnitFamily(unittest.TestCase):
    def test_basic_families(self):
        self.assertEqual(bm.unit_family("Combined cycle", "Pipeline Natural Gas"), "CC")
        self.assertEqual(
            bm.unit_family("Combustion turbine", "Pipeline Natural Gas"), "CT"
        )
        self.assertEqual(bm.unit_family("Tangentially-fired", "Coal"), "ST_COAL")
        self.assertEqual(
            bm.unit_family("Dry bottom wall-fired boiler", "Pipeline Natural Gas"),
            "ST_GAS",
        )

    def test_midyear_conversion_takes_active_segment(self):
        s = "Combustion turbine (Started Jul 01, 2024), Combined cycle (Ended Jul 01, 2024)"
        self.assertEqual(bm.unit_family(s, "Pipeline Natural Gas"), "CT")


class TestTwoClassSplit(unittest.TestCase):
    """A two-class plant's energy lands in both classes per the basis."""

    def _net(self):
        rng = np.random.default_rng(7)
        return rng.uniform(0, 100, _T)

    def test_unit_hourly_basis_proportional(self):
        net = self._net()
        # CT runs only hours 0-99, ST runs everywhere: the split must follow
        # the measured per-hour shares exactly.
        ct = np.zeros(_T)
        ct[:100] = 50.0
        st = np.full(_T, 50.0)
        series, basis = bm.split_measured_series(
            net,
            ["CT_PEAKER", "ST_GAS"],
            {"CT_PEAKER": 100.0, "ST_GAS": 300.0},
            {"CT_PEAKER": ct, "ST_GAS": st},
            None,
        )
        self.assertEqual(basis, "unit_hourly")
        np.testing.assert_allclose(
            series["CT_PEAKER"] + series["ST_GAS"], net, rtol=1e-12
        )
        # Hours 0-99: 50/50 split; later hours: all ST.
        np.testing.assert_allclose(series["CT_PEAKER"][:100], net[:100] / 2)
        np.testing.assert_allclose(series["CT_PEAKER"][100:], 0.0)
        self.assertGreater(series["CT_PEAKER"].sum(), 0.0)
        self.assertGreater(series["ST_GAS"].sum(), 0.0)

    def test_e923_monthly_fallback(self):
        net = np.full(_T, 100.0)
        monthly = {
            "CC_REGULAR": np.full(12, 75_000.0),
            "ST_GAS": np.full(12, 25_000.0),
        }
        series, basis = bm.split_measured_series(
            net,
            ["CC_REGULAR", "ST_GAS"],
            {"CC_REGULAR": 200.0, "ST_GAS": 100.0},
            None,
            monthly,
        )
        self.assertEqual(basis, "e923_monthly")
        np.testing.assert_allclose(
            series["CC_REGULAR"] + series["ST_GAS"], net, rtol=1e-12
        )
        np.testing.assert_allclose(series["CC_REGULAR"], net * 0.75)

    def test_capacity_last_resort(self):
        net = np.full(_T, 90.0)
        series, basis = bm.split_measured_series(
            net,
            ["CT_PEAKER", "ST_GAS"],
            {"CT_PEAKER": 30.0, "ST_GAS": 60.0},
            None,
            None,
        )
        self.assertEqual(basis, "capacity")
        np.testing.assert_allclose(series["CT_PEAKER"], net / 3.0)
        np.testing.assert_allclose(
            series["CT_PEAKER"] + series["ST_GAS"], net, rtol=1e-12
        )

    def test_zero_gross_hours_fall_back_to_annual_share(self):
        net = np.full(_T, 10.0)
        ct = np.zeros(_T)
        st = np.zeros(_T)
        ct[: _T // 2] = 25.0  # annual gross share 25%
        st[: _T // 2] = 75.0
        series, _ = bm.split_measured_series(
            net,
            ["CT_PEAKER", "ST_GAS"],
            {"CT_PEAKER": 100.0, "ST_GAS": 100.0},
            {"CT_PEAKER": ct, "ST_GAS": st},
            None,
        )
        # Second half-year has zero total gross: hours take the annual share.
        np.testing.assert_allclose(series["CT_PEAKER"][_T // 2 :], 2.5)
        np.testing.assert_allclose(
            series["CT_PEAKER"] + series["ST_GAS"], net, rtol=1e-12
        )


class TestNameplateShares(unittest.TestCase):
    def test_sum_preserved(self):
        out = bm.nameplate_shares(
            {"CC_REGULAR": 268.5, "ST_GAS": 1724.8},
            ["CC_REGULAR", "ST_GAS"],
            2096.0,
        )
        self.assertEqual(out["CC_REGULAR"] + out["ST_GAS"], 2096.0)
        self.assertEqual(out["CC_REGULAR"], round(2096.0 * 268.5 / 1993.3))

    def test_all_zero_caps_split_equally(self):
        out = bm.nameplate_shares({}, ["A", "B"], 100.0)
        self.assertEqual(out["A"] + out["B"], 100.0)


class TestE923Mapping(unittest.TestCase):
    def test_exact_family_and_largest_fallback(self):
        got = bm.map_e923_to_model_classes(
            {
                "ST_GAS": np.array([10.0] * 12),
                "CT_PEAKER": np.array([2.0] * 12),  # family CT: no model CT
                "oil": np.array([1.0] * 12),  # no family: largest class
            },
            ["CC_REGULAR", "ST_GAS"],
            {"CC_REGULAR": 50.0, "ST_GAS": 200.0},
        )
        np.testing.assert_allclose(got["ST_GAS"], np.array([13.0] * 12))
        np.testing.assert_allclose(got["CC_REGULAR"], 0.0)


class TestSingleClassByteIdentity(unittest.TestCase):
    """The important half: single-class plants and parts are byte-unchanged."""

    def _part(self):
        cn = np.clip(np.sin(np.arange(_T) / 24.0) * 50 + 50, 0, None)
        camp = np.clip(np.nan_to_num(100.0 * cn / 100.0), 0, 250).round()
        import base64

        b64 = base64.b64encode(camp.astype(np.uint8).tobytes()).decode()
        return {
            "plants": {
                "100": {
                    "name": "Single",
                    "zone": "Z",
                    "group": "CC_REGULAR",
                    "npl": 100,
                    "nodata": False,
                    "campd": b64,
                    "c_ann": round(float(cn.sum()) / 1e6, 4),
                    "c_mon": [1.0] * 12,
                    "e_ann": 0.5,
                    "btm": 0.0,
                    "e_mon": [41.7] * 12,
                }
            },
            "e930": {"gas": 1.0, "coal": 0.0},
            "classFull": {"CC_REGULAR": 0.5},
        }

    def test_part_codec_round_trip_is_byte_identical(self, tmp_dir=None):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            bench_dir = Path(td)
            meta = {"iso": "TESTISO", "years": [2023]}
            p1 = ba.write_bench_part(bench_dir, "TESTISO", 2023, meta, self._part())
            b1 = p1.read_bytes()
            part = ba.load_bench_part(p1)
            p2 = ba.write_bench_part(
                bench_dir, "TESTISO", 2023, part["meta"], part["bench"]
            )
            self.assertEqual(b1, p2.read_bytes())

    def test_migration_passthrough_keeps_single_class_entries(self):
        # A composition where the benched plant is single-class: the split
        # returns the SAME entries object untouched (no re-encode, no re-key).
        from scripts.migrate_bench_multiclass import split_bench_plants

        part = self._part()
        comp = {100: {"CC_REGULAR": 120.0}, 200: {"CT_PEAKER": 40.0, "ST_GAS": 60.0}}
        plants, old_group, slices = split_bench_plants(
            "NYISO", 2023, part["plants"], comp
        )
        self.assertEqual(old_group, {})
        self.assertEqual(slices, {})
        self.assertIs(plants, part["plants"])


if __name__ == "__main__":
    unittest.main()


class TestEmptyE923VectorLength(unittest.TestCase):
    """A multi-class plant with NO EIA-923 rows must honour the caller's length.

    ``render_calibration_html.build_payload`` builds ``e923_pk`` as the
    13-vector ``[annual, m01..m12]`` and every consumer reads ``[1:]`` as
    twelve months. When a plant has no EIA-923 rows there is no input array
    to take the length from, and the pre-fix default of 12 produced an
    11-month slice that ran the month loop off the end (IndexError, first
    seen registering a MISO 2025 bundle).
    """

    def test_default_is_unchanged_for_twelve_vector_callers(self) -> None:
        got = bm.map_e923_to_model_classes({}, ["CC_CHP", "CT_CHP"], {})
        self.assertEqual(
            {k: len(v) for k, v in got.items()}, {"CC_CHP": 12, "CT_CHP": 12}
        )

    def test_thirteen_vector_caller_gets_thirteen(self) -> None:
        got = bm.map_e923_to_model_classes({}, ["CC_CHP", "CT_CHP"], {}, empty_len=13)
        self.assertEqual(
            {k: len(v) for k, v in got.items()}, {"CC_CHP": 13, "CT_CHP": 13}
        )
        for arr in got.values():
            self.assertEqual(len(arr[1:]), 12, "must yield twelve months")

    def test_populated_input_still_drives_the_length(self) -> None:
        """``empty_len`` is only the no-data fallback, never an override."""
        got = bm.map_e923_to_model_classes(
            {"CC_CHP": np.zeros(13)}, ["CC_CHP"], {"CC_CHP": 1.0}, empty_len=12
        )
        self.assertEqual(len(got["CC_CHP"]), 13)
