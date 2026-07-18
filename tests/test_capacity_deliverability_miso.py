"""Tests for the MISO capacity-deliverability intake against the real fixture.

Copies the committed ``data/raw/capacity-deliverability/miso/miso.csv`` into a
tmp raw tree (CLEAN_DIR redirected, as in ``test_curate_capacity_deliverability.py``)
and runs ``curate`` end to end. This proves the normalized CSV — area labels
"LRZ 1".."LRZ 10", area_type lrz/rto, lowercase season, "2023/2024"-style
delivery_year, canonical metric names — is actually in-vocab and round-trips
through ``validate_clean``, not just eyeballed.
"""

import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_capacity_deliverability as curate_cd
from scripts.lib import capacity_deliverability as cd
from scripts.lib.clean_io import paths, validate_clean

_REAL_MISO_CSV = paths.REPO_ROOT / "data/raw/capacity-deliverability/miso/miso.csv"


class TestCapacityDeliverabilityMiso(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        self._orig_clean = paths.CLEAN_DIR
        paths.CLEAN_DIR = root / "clean"

        d = cd.raw_dir_for("MISO", self.raw_root)
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(_REAL_MISO_CSV, d / "miso.csv")

    def tearDown(self) -> None:
        paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate_miso(self) -> pd.DataFrame:
        written = curate_cd.curate(raw_root=self.raw_root, isos=["MISO"])
        self.assertEqual(len(written), 1, "expected one MISO partition")
        path = written[0]
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "capacity-deliverability")
        return pd.read_parquet(path)

    def test_validate_clean_passes(self) -> None:
        # Proves area_type/season/metric are all in-vocab post-normalization
        # (validate_tidy runs inside parse_iso; validate_clean re-checks on disk).
        self._curate_miso()

    def test_all_four_seasons_present(self) -> None:
        # Seasonal PYs (PY2023-24 onward) carry all four seasons; PY2022-23
        # predates MISO's seasonal construct and carries a single "annual" set.
        df = self._curate_miso()
        seasonal = df[df["delivery_year"] != "2022/2023"]
        self.assertEqual(
            set(seasonal["season"]), {"summer", "fall", "winter", "spring"}
        )
        pre_seasonal = df[df["delivery_year"] == "2022/2023"]
        self.assertEqual(set(pre_seasonal["season"]), {"annual"})

    def test_py2022_23_annual_rows(self) -> None:
        # The PY2022-23 LOLE Study Report (D5) publishes one annual CIL/CEL/ZIA/
        # LRR set per LRZ (pre-seasonal). Spot-check LRZ 1 CIL (Table 3-3 p.13)
        # and that the two "No Limit Found" CELs (LRZ 4/5, Table 3-4 p.15) were
        # dropped as blank, never written as 0.
        df = self._curate_miso()
        py = df[df["delivery_year"] == "2022/2023"]
        self.assertEqual(set(py["area"]), {f"LRZ {z}" for z in range(1, 11)})
        cil = py[(py["metric"] == "import_limit") & (py["area"] == "LRZ 1")]
        self.assertEqual(float(cil["value_mw"].iloc[0]), 4629.0)
        cel = py[py["metric"] == "export_limit"]
        self.assertEqual(
            set(cel["area"]), {f"LRZ {z}" for z in (1, 2, 3, 6, 7, 8, 9, 10)}
        )
        self.assertFalse((cel["value_mw"] == 0).any())

    def test_requirement_row_carries_value_pu(self) -> None:
        df = self._curate_miso()
        requirement = df[df["metric"] == "requirement"]
        self.assertFalse(requirement.empty)
        self.assertTrue((requirement["value_pu"].notna()).all())

    def test_rto_system_row_exists(self) -> None:
        df = self._curate_miso()
        rto_rows = df[df["area_type"] == "rto"]
        self.assertFalse(rto_rows.empty)
        self.assertEqual(set(rto_rows["area"]), {"RTO", "North", "South"})

    def test_miso_registered(self) -> None:
        registry = cd.load_registry()
        self.assertIn("MISO", registry)
        self.assertEqual(registry["MISO"].default_area_type, "lrz")

    def test_seasonal_caps_read_py2022_23_for_jan_may_2023(self) -> None:
        # Wiring check for scope decision D5: with the PY2022-23 extraction
        # landed, the seasonal interface-cap builder resolves Jan–May 2023
        # (winter/spring of the pre-seasonal PY2022-23) to that PY's ANNUAL
        # CIL/CEL row — never to another planning year's seasonal row — while
        # Jun 2023 onward keeps reading PY2023-24 seasonal values.
        self._curate_miso()
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.model.transmission import build_miso_deliverability_groups

        cfg = get_iso_config("MISO")
        groups = build_miso_deliverability_groups(cfg.links, 2023, 8760)
        self.assertTrue(groups)
        caps = {}
        for idx, cil, _, cel, signs in groups:
            (zone,) = {
                cfg.links[i].to_zone if s > 0 else cfg.links[i].from_zone
                for i, s in zip(idx, signs)
            }
            caps[zone] = (cil, cel)
        jan, jul = 0, 24 * 200  # hour in Jan (PY2022-23) / Jul (PY2023-24)
        west_cil, west_cel = caps["MISO-West"]
        # LRZ 1: PY2022-23 annual CIL 4629 / CEL 3273 (LOLE Tables 3-3/3-4);
        # PY2023-24 summer CIL 5301 / CEL 3959.
        self.assertEqual(west_cil[jan], 4629.0)
        self.assertEqual(west_cel[jan], 3273.0)
        self.assertEqual(west_cil[jul], 5301.0)
        self.assertEqual(west_cel[jul], 3959.0)
        # Union zone (Plains = LRZ 3+5): documented member-sum ceiling,
        # 5626 + 6072 for PY2022-23 annual.
        self.assertEqual(caps["MISO-Plains"][0][jan], 5626.0 + 6072.0)


if __name__ == "__main__":
    unittest.main()
