"""Tests for the winter-fuel-inventory intake on tiny synthetic fixtures.

Writes a minimal EIA-860 pair (multifuel + boiler design) and a study CSV into a
tmp raw tree, runs ``curate``, and asserts the written Parquet is schema-valid
and the tidy reconciliation is correct: EIA-860 per-plant oil-limb MW +
petroleum firing-rate derivation (state filter, switch-capable filter, the 0.1
bbl/hr rescale, per-plant summation) unioned with the hand-curated study rows.
NOT a full-data run: CLEAN_DIR is redirected to a tmp dir (as in
tests/test_curate_capacity_deliverability.py) so it never touches the real tree.
Also covers the metric<->unit vocabulary guard and the skip-empty path.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_winter_fuel_inventory as curate_wfi
from scripts.lib import clean_io
from scripts.lib import winter_fuel_inventory as wfi
from scripts.lib.clean_io import validate_clean

# Two ME plants (in the ISO-NE footprint) + one TX plant (out of footprint) to
# exercise the state filter. Plant 100: two switch-capable gens (30+20=50 MW oil
# limb) and one non-switch gen that must be excluded. Plant 200: one gen. Plant
# 999 (TX): must be filtered out entirely.
_MULTIFUEL = pd.DataFrame(
    {
        "Plant Code": [100, 100, 100, 200, 999],
        "State": ["ME", "ME", "ME", "NH", "TX"],
        "Switch Between Oil and Natural Gas?": ["Y", "Y", "N", "Y", "Y"],
        "Net Winter Capacity with Oil (MW)": [30.0, 20.0, 15.0, 40.0, 500.0],
    }
)
# Boiler design: field is in tenths of a barrel/hour. Plant 100 has two boilers
# (150 + 50 = 200 -> 20.0 bbl/hr); plant 200 one boiler (100 -> 10.0 bbl/hr);
# plant 999 (TX) filtered out; a zero-rate boiler contributes nothing.
_BOILER = pd.DataFrame(
    {
        "Plant Code": [100, 100, 200, 200, 999],
        "State": ["ME", "ME", "NH", "NH", "TX"],
        "Firing Rate Using Petroleum (0.1 Barrels per Hour)": [
            150.0,
            50.0,
            100.0,
            0.0,
            900.0,
        ],
    }
)
# A minimal study CSV: one fleet row and one bad-unit row is NOT included here
# (that path is tested separately via validate_tidy).
_STUDY_CSV = """iso,entity,entity_type,plant_code,season,delivery_year,metric,value,unit,fuel_kind,source_doc,source_page
ISONE,OIL_DUAL_FUEL,fleet,,winter,2018,tank_capacity,10,days,oil,ISO-NE OFSA 2018,p.34
ISONE,LNG_SYSTEM,system,,winter,2018,delivery_rate,1.0,bcf_per_day,lng,ISO-NE OFSA 2018,p.34
"""


def _write_fixture(raw_root: Path) -> None:
    edir = wfi.eia860_dir(raw_root)
    edir.mkdir(parents=True, exist_ok=True)
    _MULTIFUEL.to_parquet(edir / "eia860_multifuel_operable.parquet")
    _BOILER.to_parquet(
        edir / "eia860_enviro_equip_boiler_info_design_parameters.parquet"
    )
    sdir = wfi.raw_dir_for("ISONE", raw_root)
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / "isone.csv").write_text(_STUDY_CSV)


class TestCurateWinterFuelInventory(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate(self) -> pd.DataFrame:
        _write_fixture(self.raw_root)
        written = curate_wfi.curate(raw_root=self.raw_root, isos=["ISONE"])
        self.assertEqual(len(written), 1, "expected one ISONE partition")
        path = written[0]
        self.assertTrue(path.exists())
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "winter-fuel-inventory")
        return pd.read_parquet(path)

    def test_schema_valid_and_columns(self) -> None:
        df = self._curate()
        self.assertEqual(set(df["iso"]), {"ISONE"})
        self.assertEqual(list(df.columns), list(wfi.CANONICAL_COLUMNS))

    def test_oil_limb_capacity_summed_and_state_filtered(self) -> None:
        df = self._curate()
        oc = df[df["metric"] == "oil_limb_capacity"].set_index("plant_code")["value"]
        # Plant 100: only the two switch-capable gens (30+20), NOT the N gen.
        self.assertAlmostEqual(oc[100], 50.0)
        self.assertAlmostEqual(oc[200], 40.0)
        # TX plant 999 is outside the ISO-NE state filter.
        self.assertNotIn(999, oc.index)

    def test_firing_rate_rescaled_and_summed(self) -> None:
        df = self._curate()
        fr = df[df["metric"] == "firing_rate"].set_index("plant_code")["value"]
        # 0.1-bbl/hr units: plant 100 (150+50)*0.1 = 20.0; plant 200 100*0.1=10.0.
        self.assertAlmostEqual(fr[100], 20.0)
        self.assertAlmostEqual(fr[200], 10.0)
        self.assertNotIn(999, fr.index)
        self.assertEqual(set(df[df["metric"] == "firing_rate"]["unit"]), {"bbl_per_hr"})

    def test_study_rows_unioned(self) -> None:
        df = self._curate()
        study = df[df["entity_type"].isin({"fleet", "system"})]
        self.assertEqual(set(study["metric"]), {"tank_capacity", "delivery_rate"})
        tank = study[study["metric"] == "tank_capacity"].iloc[0]
        self.assertEqual(tank["unit"], "days")
        self.assertAlmostEqual(tank["value"], 10.0)

    def test_empty_iso_is_skipped(self) -> None:
        # No EIA-860 tables and no study CSV -> curate writes nothing, no raise.
        written = curate_wfi.curate(raw_root=self.raw_root, isos=["ISONE"])
        self.assertEqual(written, [])

    def test_unregistered_iso_raises(self) -> None:
        with self.assertRaises(ValueError):
            curate_wfi.curate(raw_root=self.raw_root, isos=["NOTANISO"])

    def test_metric_unit_guard_rejects_bad_pairing(self) -> None:
        bad = pd.DataFrame(
            {
                "iso": ["ISONE"],
                "entity": ["X"],
                "entity_type": ["fleet"],
                "plant_code": [pd.NA],
                "season": ["winter"],
                "delivery_year": ["2018"],
                "metric": ["oil_limb_capacity"],  # only mw is legal
                "value": [1.0],
                "unit": ["bbl"],  # illegal for oil_limb_capacity
                "fuel_kind": ["oil"],
                "source_doc": ["x"],
                "source_page": ["y"],
            }
        )
        with self.assertRaises(ValueError):
            wfi.validate_tidy(wfi.finalize(bad))

    def test_isone_registered(self) -> None:
        registry = wfi.load_registry()
        self.assertIn("ISONE", registry)
        self.assertEqual(
            registry["ISONE"].eia_states, ("ME", "NH", "VT", "MA", "RI", "CT")
        )


if __name__ == "__main__":
    unittest.main()
