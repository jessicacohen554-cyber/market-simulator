"""Tests for the forecast-bands payload exporter (PB-4).

Pure unit tests against hand-built parquet/JSON in the frozen PB-2/PB-0
schemas -- no solves. Covers the schema round-trip (parquet+JSON in ->
payload JS out, inflatable back to the original values), the label/caveat
logic (dispatch-conditional default, synthetic banner), and graceful
degradation when a layer (or the matrix) is absent.
"""

import base64
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import export_forecast_bands as efb  # noqa: E402


def _bands_df(rows):
    return pd.DataFrame(
        rows,
        columns=[
            "year",
            "metric",
            "layer",
            "quantile",
            "value",
            "n",
            "bootstrap_lo",
            "bootstrap_hi",
        ],
    )


def _write_ensemble(tmpdir, bands_rows, meta):
    d = Path(tmpdir) / "ens"
    d.mkdir(parents=True, exist_ok=True)
    _bands_df(bands_rows).to_parquet(d / "bands.parquet", index=False)
    (d / "ensemble_meta.json").write_text(json.dumps(meta))
    return d


def _write_matrix(tmpdir):
    d = Path(tmpdir) / "matrix"
    d.mkdir(parents=True, exist_ok=True)
    matrix_rows = [
        {
            "case": "REF",
            "year": 2026,
            "emissions_mt": 140.0,
            "cache_key": "k",
            "label": "L",
        },
        {
            "case": "REF",
            "year": 2027,
            "emissions_mt": 138.0,
            "cache_key": "k",
            "label": "L",
        },
        {
            "case": "GAS-HI",
            "year": 2026,
            "emissions_mt": 130.0,
            "cache_key": "k",
            "label": "L",
        },
        {
            "case": "GAS-HI",
            "year": 2027,
            "emissions_mt": 128.0,
            "cache_key": "k",
            "label": "L",
        },
    ]
    pd.DataFrame(matrix_rows).to_parquet(d / "matrix.parquet", index=False)
    envelope_rows = [
        {
            "year": 2026,
            "min_mt": 130.0,
            "min_case": "GAS-HI",
            "max_mt": 140.0,
            "max_case": "REF",
            "label": "L",
        },
        {
            "year": 2027,
            "min_mt": 128.0,
            "min_case": "GAS-HI",
            "max_mt": 138.0,
            "max_case": "REF",
            "label": "L",
        },
    ]
    pd.DataFrame(envelope_rows).to_parquet(d / "envelope.parquet", index=False)
    (d / "meta.json").write_text(
        json.dumps(
            {
                "matrix_id": "m1",
                "iso": "ERCOT",
                "label": "deterministic scenario range -- NOT a probability band",
                "matrix_path": "x",
                "cases": {"REF": "k", "GAS-HI": "k"},
                "base_config": {},
                "years_present": [2026, 2027],
            }
        )
    )
    return d


_BASE_META = {
    "iso": "ercot",
    "sampler": {"n": 4},
    "members": {f"draw-{i:04d}": "k" for i in range(4)},
    "label": "parametric probability band (PB-2)",
    "quantile_estimator": "numpy HF7",
}


def _parametric_rows():
    rows = []
    for year in (2026, 2027):
        for q, val in ((0.1, 90.0), (0.5, 100.0), (0.9, 110.0)):
            rows.append(
                (year, "emissions_mt", "parametric", q, val, 4, val - 2, val + 2)
            )
    return rows


class TestReadEnsemble(unittest.TestCase):
    def test_layers_present_derived_from_bands_not_meta(self):
        """layers_present must reflect the actual parquet contents, not meta's
        (possibly stale) layers_present field."""
        with tempfile.TemporaryDirectory() as tmp:
            meta = {
                **_BASE_META,
                "layers_present": ["parametric", "parametric_plus_structural"],
            }
            d = _write_ensemble(tmp, _parametric_rows(), meta)
            out = efb.read_ensemble(d)
            self.assertEqual(out["layers_present"], ["parametric"])

    def test_bands_round_trip_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _write_ensemble(tmp, _parametric_rows(), _BASE_META)
            out = efb.read_ensemble(d)
            p50 = out["bands"]["parametric"]["emissions_mt"]["2026"]["0.5"]
            self.assertEqual(p50["value"], 100.0)
            self.assertEqual(p50["n"], 4)
            self.assertEqual(p50["bootstrap_lo"], 98.0)
            self.assertEqual(p50["bootstrap_hi"], 102.0)

    def test_n_draws_from_sampler_meta(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _write_ensemble(tmp, _parametric_rows(), _BASE_META)
            out = efb.read_ensemble(d)
            self.assertEqual(out["n_draws"], 4)

    def test_missing_files_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                efb.read_ensemble(Path(tmp) / "nope")


class TestDispatchConditional(unittest.TestCase):
    def test_defaults_true_with_no_info(self):
        self.assertTrue(efb.is_dispatch_conditional({}))

    def test_defaults_true_when_status_unmeasured(self):
        self.assertTrue(efb.is_dispatch_conditional({"lambda_h_status": "UNMEASURED"}))

    def test_false_only_when_explicitly_measured(self):
        self.assertFalse(efb.is_dispatch_conditional({"lambda_h_status": "measured"}))
        self.assertFalse(
            efb.is_dispatch_conditional(
                {"structural_prior": {"lambda_h_status": "Measured"}}
            )
        )

    def test_nested_field_also_defaults_conservative(self):
        self.assertTrue(efb.is_dispatch_conditional({"structural_prior": {}}))


class TestMatrixAndPayload(unittest.TestCase):
    def test_read_matrix_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _write_matrix(tmp)
            out = efb.read_matrix(d)
            self.assertEqual(out["envelope"]["2026"]["max_case"], "REF")
            self.assertEqual(out["trajectories"]["GAS-HI"]["2027"], 128.0)
            self.assertIn("NOT a probability band", out["label"])

    def test_payload_without_matrix_is_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _write_ensemble(tmp, _parametric_rows(), _BASE_META)
            ensemble = efb.read_ensemble(d)
            payload = efb.build_payload("id1", ensemble, matrix=None)
            self.assertIsNone(payload["matrix"])
            self.assertEqual(payload["default_metric"], "emissions_mt")

    def test_default_metric_falls_back_when_requested_metric_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = [(2026, "avg_price", "parametric", 0.5, 40.0, 4, 39, 41)]
            d = _write_ensemble(tmp, rows, _BASE_META)
            ensemble = efb.read_ensemble(d)
            payload = efb.build_payload(
                "id1", ensemble, matrix=None, default_metric="emissions_mt"
            )
            self.assertEqual(payload["default_metric"], "avg_price")


class TestWritePayload(unittest.TestCase):
    def test_payload_js_inflates_to_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _write_ensemble(tmp, _parametric_rows(), _BASE_META)
            ensemble = efb.read_ensemble(d)
            payload = efb.build_payload("my-id", ensemble, matrix=None)
            out_dir = Path(tmp) / "fe"
            path = efb.write_payload_js(payload, "my-id", frontend_dir=out_dir)
            text = path.read_text()
            marker = 'window.FB.bandsGz["my-id"]='
            self.assertIn(marker, text)
            # Extract the JSON-string literal between the assignment and trailing ';'
            b64_literal = text.split(marker, 1)[-1].rstrip(";")
            b64 = json.loads(b64_literal)
            raw = gzip.decompress(base64.b64decode(b64))
            roundtripped = json.loads(raw)
            self.assertEqual(roundtripped["ensemble_id"], "my-id")
            self.assertEqual(
                roundtripped["bands"]["parametric"]["emissions_mt"]["2026"]["0.5"][
                    "value"
                ],
                100.0,
            )

    def test_manifest_upserts_without_clobbering_other_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _write_ensemble(tmp, _parametric_rows(), _BASE_META)
            ensemble = efb.read_ensemble(d)
            out_dir = Path(tmp) / "fe"
            efb.update_manifest(efb.build_payload("a", ensemble, None), out_dir)
            efb.update_manifest(efb.build_payload("b", ensemble, None), out_dir)
            manifest = json.loads((out_dir / "manifest.json").read_text())
            self.assertEqual(set(manifest["ensembles"]), {"a", "b"})


class TestMarkdownTable(unittest.TestCase):
    def test_probability_layer_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _write_ensemble(tmp, _parametric_rows(), _BASE_META)
            ensemble = efb.read_ensemble(d)
            payload = efb.build_payload("id1", ensemble, matrix=None)
            out_path = Path(tmp) / "table.md"
            efb.write_markdown_table(payload, out_path)
            text = out_path.read_text()
            self.assertIn("| Year | P10 | P50 | P90 |", text)
            self.assertIn("| 2026 | 90.00 | 100.00 | 110.00 |", text)
            self.assertNotIn("SYNTHETIC", text)

    def test_synthetic_banner_in_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta = {**_BASE_META, "synthetic": True}
            d = _write_ensemble(tmp, _parametric_rows(), meta)
            ensemble = efb.read_ensemble(d)
            payload = efb.build_payload("id1", ensemble, matrix=None)
            out_path = Path(tmp) / "table.md"
            efb.write_markdown_table(payload, out_path)
            self.assertIn("SYNTHETIC FIXTURE", out_path.read_text())

    def test_envelope_only_when_no_probability_layer(self):
        """A metric with only scenario_envelope rows (no parametric quantiles)
        must render min/max, explicitly labelled NOT a probability band --
        never mislabeled as P10/P90."""
        with tempfile.TemporaryDirectory() as tmp:
            rows = [
                (
                    2026,
                    "emissions_mt",
                    "scenario_envelope",
                    0.0,
                    130.0,
                    0,
                    130.0,
                    130.0,
                ),
            ]
            d = _write_ensemble(tmp, rows, _BASE_META)
            ensemble = efb.read_ensemble(d)
            matrix_dir = _write_matrix(tmp)
            matrix = efb.read_matrix(matrix_dir)
            payload = efb.build_payload("id1", ensemble, matrix)
            out_path = Path(tmp) / "table.md"
            efb.write_markdown_table(payload, out_path)
            text = out_path.read_text()
            self.assertIn("NOT a probability band", text)
            self.assertIn("Min case", text)
            self.assertNotIn("P10", text)

    def test_missing_metric_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _write_ensemble(tmp, _parametric_rows(), _BASE_META)
            ensemble = efb.read_ensemble(d)
            payload = efb.build_payload("id1", ensemble, matrix=None)
            with self.assertRaises(ValueError):
                efb.write_markdown_table(
                    payload, Path(tmp) / "t.md", metric="nonexistent"
                )


if __name__ == "__main__":
    unittest.main()
