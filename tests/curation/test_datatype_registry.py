"""Tests for the shared IsoSpec-registry factory (scripts/lib/datatype_registry.py)."""

import unittest
from dataclasses import field, fields, is_dataclass
from pathlib import Path

import pandas as pd

from scripts.lib.datatype_registry import make_registry


def _make(**overrides):
    cfg = dict(
        datatype="demo-type",
        canonical_columns=("iso", "area", "value_mw", "point_index"),
        spec_fields=[
            ("iso", str),
            ("metric_aliases", dict, field(default_factory=dict)),
            ("kind", str, "planning"),
        ],
        package="scripts.lib.demo_type",
        iso_modules=("pjm", "miso"),
        raw_subpath=("demo-type",),
        string_cols=("iso", "area"),
        float_cols=("value_mw",),
        int_cols=("point_index",),
        sort_by=("area",),
    )
    cfg.update(overrides)
    return make_registry(
        cfg.pop("datatype"),
        cfg.pop("canonical_columns"),
        cfg.pop("spec_fields"),
        **cfg,
    )


class TestMakeRegistry(unittest.TestCase):
    def test_isospec_is_frozen_dataclass_with_fields_and_module(self):
        r = _make()
        self.assertTrue(is_dataclass(r.IsoSpec))
        self.assertEqual(
            [f.name for f in fields(r.IsoSpec)], ["iso", "metric_aliases", "kind"]
        )
        self.assertEqual(r.IsoSpec.__module__, "scripts.lib.demo_type")
        spec = r.IsoSpec(iso="PJM")
        with self.assertRaises(Exception):
            spec.iso = "MISO"  # frozen
        # Default factory yields an independent dict per instance.
        self.assertEqual(spec.metric_aliases, {})
        self.assertEqual(spec.kind, "planning")

    def test_register_and_check(self):
        seen = []
        r = _make(register_check=lambda s: seen.append(s.iso))
        spec = r.IsoSpec(iso="pjm")
        self.assertIs(r.register(spec), spec)
        self.assertEqual(r.REGISTRY["PJM"], spec)  # keyed upper-case
        self.assertEqual(seen, ["pjm"])

    def test_register_check_can_reject(self):
        def _reject(s):
            raise ValueError("nope")

        r = _make(register_check=_reject)
        with self.assertRaises(ValueError):
            r.register(r.IsoSpec(iso="PJM"))

    def test_raw_dir_for_nested(self):
        r = _make(raw_subpath=("capacity-market", "demand-curve"))
        self.assertEqual(
            r.raw_dir_for("PJM", Path("/data/raw")),
            Path("/data/raw/capacity-market/demand-curve/pjm"),
        )

    def test_load_registry_skips_missing_modules(self):
        # No sibling modules exist for the synthetic package -> empty, no error.
        r = _make()
        self.assertEqual(r.load_registry(), {})

    def test_finalize_dtypes_order_and_sort(self):
        r = _make()
        df = pd.DataFrame(
            {
                "area": ["b", "a"],
                "iso": ["PJM", "PJM"],
                "value_mw": ["2.5", "1.0"],
                "point_index": ["1", "0"],
            }
        )
        out = r.finalize(df)
        # Column order is canonical; rows sorted by area.
        self.assertEqual(list(out.columns), ["iso", "area", "value_mw", "point_index"])
        self.assertEqual(list(out["area"]), ["a", "b"])
        self.assertEqual(str(out["iso"].dtype), "string")
        self.assertEqual(str(out["value_mw"].dtype), "float64")
        self.assertEqual(str(out["point_index"].dtype), "float64")

    def test_finalize_fills_missing_columns(self):
        r = _make()
        out = r.finalize(pd.DataFrame({"iso": ["PJM"], "area": ["x"]}))
        self.assertTrue(out["value_mw"].isna().all())

    def test_na_position(self):
        r = _make(sort_by=("value_mw",), na_position="first")
        df = pd.DataFrame(
            {
                "iso": ["PJM", "PJM"],
                "area": ["a", "b"],
                "value_mw": ["1.0", None],
                "point_index": ["0", "1"],
            }
        )
        out = r.finalize(df)
        self.assertTrue(pd.isna(out["value_mw"].iloc[0]))


if __name__ == "__main__":
    unittest.main()
