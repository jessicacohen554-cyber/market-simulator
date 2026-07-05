"""Tests for the PB-3 structural-error prior (``market_sim.structural_prior``).

Covers the plan-§3 hard constraints: the prior is wider than the plug-in
normal, the parametric P50 point path is never shifted (rule 13 — no
recentering), the convolution recovers the input spread when eps = 0 and is
asymmetric around the model path when the bias is non-zero, the emitted rows
round-trip through the landed ``compute_bands`` schema, and the rule-22 year
guard refuses quarantined fit years.
"""

import base64
import gzip
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, t as student_t

from market_sim.config.constants import (
    PUBLISHED_BAND_QUANTILES,
    STRUCTURAL_PRIOR_YEARS,
)
from market_sim.ensemble import compute_bands
from market_sim.structural_prior import (
    STRUCTURAL_LAYER,
    IsoPrior,
    StructuralPrior,
    append_structural_layer,
    convolve,
    fit_prior,
)


def _write_run_payload(runs_dir: Path, run_id: str, payload: dict) -> None:
    """Write a payload in the committed ``runs/<id>.js`` gzip+base64 form."""
    b64 = base64.b64encode(gzip.compress(json.dumps(payload).encode())).decode()
    (runs_dir / f"{run_id}.js").write_text(
        "window.BC=window.BC||{};window.BC.runGz=window.BC.runGz||{};"
        f'window.BC.runGz["{run_id}"]="{b64}";'
    )


def _write_bench_part(bench_dir: Path, iso: str, year: int, part: dict) -> None:
    """Write a bench part in the committed ``bench/<ISO>/<year>.json.gz`` form."""
    d = bench_dir / iso
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{year}.json.gz").write_bytes(gzip.compress(json.dumps(part).encode()))


def _synthetic_inputs(tmp: Path, model_by_year: dict[int, float], carbon: bool):
    """Build one-ISO committed-artifact fixtures with a consistent CO2 basis.

    The model side is ``gmModel = model/0.4`` TWh at intensity 0.4 t/MWh so the
    carbon-zero re-score reproduces the committed number exactly; the actual is
    pinned at 100 Mt so eps = ln(model/100).
    """
    runs_dir = tmp / "runs"
    bench_dir = tmp / "bench"
    runs_dir.mkdir(parents=True, exist_ok=True)
    years = {}
    for year, model in model_by_year.items():
        years[str(year)] = {
            "co2": {"model": model},
            "gmModel": {"CC_REGULAR": model / 0.4},
        }
        _write_bench_part(
            bench_dir,
            "TESTISO",
            year,
            {
                "meta": {},
                "bench": {
                    "classFull": {"CC_REGULAR": 250.0, "solar": 50.0},
                    "co2": {
                        "egrid": 100.0,
                        "intensity": {"CC_REGULAR": 0.4},
                    },
                },
            },
        )
    _write_run_payload(runs_dir, "test-run", {"label": "t", "years": years})
    fit_inputs = {
        "TESTISO": {
            "run_id": "test-run",
            "bundle": "results/calibration/test",
            "carbon_priced": carbon,
        }
    }
    return fit_inputs, runs_dir, bench_dir


def _degenerate_prior(bias: float, scale: float, iso: str = "ERCOT") -> StructuralPrior:
    """A hand-built prior for convolution tests (no fitting involved)."""
    return StructuralPrior(
        schema_version=1,
        nu=2,
        scale_inflation=4.0 / 3.0,
        s_pooled=scale,
        years=STRUCTURAL_PRIOR_YEARS,
        lambda_h=0.0,
        lambda_h_status="UNMEASURED",
        emissions_basis={"label": "test"},
        isos={
            iso: IsoPrior(
                iso=iso,
                eps_by_year={y: bias for y in STRUCTURAL_PRIOR_YEARS},
                model_mt_by_year={y: 1.0 for y in STRUCTURAL_PRIOR_YEARS},
                actual_mt_by_year={y: 1.0 for y in STRUCTURAL_PRIOR_YEARS},
                bias=bias,
                noise=scale,
                scale=scale,
                carbon_priced=False,
                basis_stale=False,
                rescore="verified-identical",
                run_id="test",
                bundle="test",
            )
        },
    )


def _metrics_frame(values_by_year: dict[int, list[float]]) -> pd.DataFrame:
    rows = []
    for year, vals in values_by_year.items():
        for j, v in enumerate(vals):
            rows.append(
                {
                    "draw_id": f"draw-{j}",
                    "year": year,
                    "metric": "emissions_mt",
                    "value": v,
                }
            )
    return pd.DataFrame(rows)


class TestFitPrior(unittest.TestCase):
    def test_fit_on_committed_repo_artifacts(self):
        """The real fit runs on the committed statmode payloads + bench parts."""
        prior = fit_prior()
        self.assertEqual(
            set(prior.isos), {"ERCOT", "CAISO", "PJM", "NYISO", "NEISO", "MISO"}
        )
        self.assertEqual(prior.years, STRUCTURAL_PRIOR_YEARS)
        # Carbon split per W0-P4 §3.2: solves stale only where carbon is priced.
        for iso in ("ERCOT", "PJM", "MISO"):
            self.assertFalse(prior.isos[iso].basis_stale)
            self.assertEqual(prior.isos[iso].rescore, "verified-identical")
        for iso in ("CAISO", "NYISO", "NEISO"):
            self.assertTrue(prior.isos[iso].basis_stale)
        # D-7 magnitudes (statistical-mode-results doc): PJM's +22.6-26.6%
        # CO2 gap is a large positive bias; ERCOT is near zero.
        self.assertGreater(prior.isos["PJM"].bias, 0.18)
        self.assertLess(abs(prior.isos["ERCOT"].bias), 0.02)
        self.assertIn("stale_isos_pending_w3p1", prior.emissions_basis)

    def test_prior_wider_than_plugin_normal_every_iso(self):
        """Hard PB-3 requirement: every central interval beats Normal(b, s)."""
        prior = fit_prior()
        for iso, p in prior.isos.items():
            for q in (0.75, 0.90, 0.95):
                t_half = float(student_t.ppf(q, prior.nu)) * p.scale
                n_half = float(norm.ppf(q)) * p.noise
                self.assertGreater(
                    t_half, n_half, f"{iso} P{int(q * 100)} interval not wider"
                )

    def test_bias_is_carried_not_subtracted(self):
        """eps keeps its non-zero mean (rule 13): sample mean tracks the bias."""
        prior = _degenerate_prior(bias=0.2, scale=1e-6)
        rng = np.random.default_rng(0)
        draws = prior.sample("ERCOT", 4000, rng)
        self.assertAlmostEqual(float(np.median(draws)), 0.2, places=3)

    def test_rule22_year_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            fit_inputs, runs_dir, bench_dir = _synthetic_inputs(
                tmp, {2022: 90.0, 2023: 95.0, 2024: 100.0}, carbon=False
            )
            with self.assertRaisesRegex(ValueError, "rule 22"):
                fit_prior(fit_inputs, runs_dir=runs_dir, bench_dir=bench_dir)

    def test_synthetic_fit_and_carbon_zero_rescore(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            model = {2023: 90.0, 2024: 100.0, 2025: 110.0}
            fit_inputs, runs_dir, bench_dir = _synthetic_inputs(
                tmp, model, carbon=False
            )
            prior = fit_prior(fit_inputs, runs_dir=runs_dir, bench_dir=bench_dir)
            p = prior.isos["TESTISO"]
            eps = np.log(np.array([90.0, 100.0, 110.0]) / 100.0)
            self.assertAlmostEqual(p.bias, float(eps.mean()), places=9)
            self.assertAlmostEqual(p.noise, float(eps.std(ddof=1)), places=9)
            # Single ISO: pooled == own noise; scale inflated by sqrt(4/3).
            self.assertAlmostEqual(
                p.scale, float(eps.std(ddof=1)) * np.sqrt(4.0 / 3.0), places=9
            )
            self.assertEqual(p.rescore, "verified-identical")

    def test_carbon_zero_rescore_mismatch_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            fit_inputs, runs_dir, bench_dir = _synthetic_inputs(
                tmp, {2023: 90.0, 2024: 100.0, 2025: 110.0}, carbon=False
            )
            # Corrupt the committed model CO2 so it no longer matches gmModel
            # under the stored intensity.
            payload = {
                "label": "t",
                "years": {
                    str(y): {
                        "co2": {"model": m + 5.0},
                        "gmModel": {"CC_REGULAR": m / 0.4},
                    }
                    for y, m in {2023: 90.0, 2024: 100.0, 2025: 110.0}.items()
                },
            }
            _write_run_payload(runs_dir, "test-run", payload)
            with self.assertRaisesRegex(ValueError, "re-score"):
                fit_prior(fit_inputs, runs_dir=runs_dir, bench_dir=bench_dir)

    def test_save_load_round_trip(self):
        prior = fit_prior()
        with tempfile.TemporaryDirectory() as tmp:
            path = prior.save(Path(tmp) / "prior.json")
            self.assertEqual(StructuralPrior.load(path), prior)


class TestConvolve(unittest.TestCase):
    def test_recovers_input_spread_when_eps_zero(self):
        """With bias=0 and scale=0 the convolved band is the parametric band."""
        values = {2026: [float(x) for x in range(1, 11)]}
        prior = _degenerate_prior(bias=0.0, scale=0.0)
        rows = convolve(
            _metrics_frame(values),
            prior,
            "ERCOT",
            seed=1,
            k=25,
            quantiles=(0.1, 0.5, 0.9),
        )
        parametric = {
            r["quantile"]: r["value"]
            for r in compute_bands(
                {y: {"emissions_mt": v} for y, v in values.items()},
                seed=1,
                quantiles=(0.1, 0.5, 0.9),
            )
        }
        for r in rows:
            self.assertAlmostEqual(r["value"], parametric[r["quantile"]], places=6)

    def test_p50_point_path_not_shifted_and_band_asymmetric(self):
        """Rule 13: the parametric P50 is untouched; the structural layer's
        band is asymmetric around it, covering the bias (not recentered)."""
        values = {2026: list(np.linspace(90.0, 110.0, 40))}
        bias = 0.2
        prior = _degenerate_prior(bias=bias, scale=0.01)
        metrics = _metrics_frame(values)
        band_values = {y: {"emissions_mt": v} for y, v in values.items()}
        parametric_rows = compute_bands(band_values, seed=3, quantiles=(0.1, 0.5, 0.9))
        p50_before = next(r for r in parametric_rows if r["quantile"] == 0.5)["value"]
        rows = convolve(metrics, prior, "ERCOT", seed=3, k=50)
        s50 = next(r for r in rows if r["quantile"] == 0.5)["value"]
        # The parametric point path is what it always was...
        parametric_after = compute_bands(band_values, seed=3, quantiles=(0.1, 0.5, 0.9))
        self.assertEqual(parametric_rows, parametric_after)
        # ...and the published band sits around model*exp(b): the bias is
        # covered by the band, never subtracted from the point forecast.
        self.assertAlmostEqual(s50 / p50_before, float(np.exp(bias)), delta=0.02)
        lo = next(r for r in rows if r["quantile"] == 0.05)["value"]
        hi = next(r for r in rows if r["quantile"] == 0.95)["value"]
        # Asymmetric around the model path: with b>0 far more of the band
        # sits above the parametric P50 than below it.
        self.assertGreater(hi - p50_before, p50_before - lo)

    def test_symmetric_when_bias_zero(self):
        """Counterpart: zero bias leaves the convolved P50 on the model path."""
        values = {2026: list(np.linspace(90.0, 110.0, 40))}
        prior = _degenerate_prior(bias=0.0, scale=0.05)
        rows = convolve(_metrics_frame(values), prior, "ERCOT", seed=5, k=200)
        s50 = next(r for r in rows if r["quantile"] == 0.5)["value"]
        p50 = float(np.quantile(np.asarray(values[2026]), 0.5))
        self.assertAlmostEqual(s50 / p50, 1.0, delta=0.01)

    def test_deterministic_in_seed_and_schema(self):
        values = {2026: [100.0, 105.0], 2027: [98.0, 101.0]}
        prior = _degenerate_prior(bias=0.1, scale=0.05)
        a = convolve(_metrics_frame(values), prior, "ERCOT", seed=11)
        b = convolve(_metrics_frame(values), prior, "ERCOT", seed=11)
        self.assertEqual(a, b)
        for r in a:
            self.assertEqual(
                set(r),
                {
                    "year",
                    "metric",
                    "layer",
                    "quantile",
                    "value",
                    "n",
                    "bootstrap_lo",
                    "bootstrap_hi",
                },
            )
            self.assertEqual(r["layer"], STRUCTURAL_LAYER)
            self.assertEqual(r["metric"], "emissions_mt")
            self.assertEqual(r["n"], 2 * 25)
            self.assertLessEqual(r["bootstrap_lo"], r["bootstrap_hi"])
        self.assertEqual(
            [r["quantile"] for r in a if r["year"] == 2026],
            list(PUBLISHED_BAND_QUANTILES),
        )

    def test_unknown_iso_and_missing_metric(self):
        prior = _degenerate_prior(bias=0.0, scale=0.01)
        with self.assertRaises(KeyError):
            convolve(_metrics_frame({2026: [1.0]}), prior, "PJM", seed=1)
        empty = pd.DataFrame({"draw_id": [], "year": [], "metric": [], "value": []})
        with self.assertRaises(ValueError):
            convolve(empty, prior, "ERCOT", seed=1)


class TestAppendStructuralLayer(unittest.TestCase):
    def _seed_ensemble_dir(self, tmp: Path) -> Path:
        """Write a minimal landed PB-2 output surface (schema-faithful)."""
        out = tmp / "ensemble"
        out.mkdir()
        values = {2026: [100.0, 104.0, 96.0, 101.0], 2027: [99.0, 103.0, 97.0, 100.0]}
        metrics = _metrics_frame(values)
        # Add a non-emissions metric to prove it is left un-convolved.
        extra = metrics[metrics.year == 2026].assign(metric="avg_price", value=40.0)
        pd.concat([metrics, extra], ignore_index=True).to_parquet(
            out / "metrics.parquet", index=False
        )
        pd.DataFrame(
            compute_bands({y: {"emissions_mt": v} for y, v in values.items()}, seed=7)
        ).to_parquet(out / "bands.parquet", index=False)
        (out / "ensemble_meta.json").write_text(
            json.dumps(
                {
                    "iso": "ERCOT",
                    "spec": {"n": 4, "seed": 7},
                    "layers_present": ["parametric"],
                    "label": "parametric probability band (PB-2)",
                }
            )
        )
        return out

    def test_appends_layer_without_touching_parametric_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self._seed_ensemble_dir(Path(tmp))
            before = pd.read_parquet(out / "bands.parquet")
            prior = _degenerate_prior(bias=0.15, scale=0.03)
            append_structural_layer(out, prior)
            after = pd.read_parquet(out / "bands.parquet")
            # Landed schema round-trip: same columns, both layers present.
            self.assertEqual(set(after.columns), set(before.columns))
            self.assertEqual(
                set(after.layer.unique()), {"parametric", STRUCTURAL_LAYER}
            )
            # Rule 13: the parametric rows (and with them the P50 point path)
            # are byte-identical after the append.
            param_after = after[after.layer == "parametric"].reset_index(drop=True)
            pd.testing.assert_frame_equal(param_after, before)
            struct = after[after.layer == STRUCTURAL_LAYER]
            self.assertEqual(set(struct.metric.unique()), {"emissions_mt"})
            self.assertEqual(sorted(struct.year.unique()), [2026, 2027])
            self.assertTrue((struct.n == 4 * 25).all())

    def test_idempotent_and_meta_updated(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self._seed_ensemble_dir(Path(tmp))
            prior = _degenerate_prior(bias=0.15, scale=0.03)
            append_structural_layer(out, prior)
            first = pd.read_parquet(out / "bands.parquet")
            append_structural_layer(out, prior)  # re-run replaces, not stacks
            second = pd.read_parquet(out / "bands.parquet")
            pd.testing.assert_frame_equal(
                first.reset_index(drop=True), second.reset_index(drop=True)
            )
            meta = json.loads((out / "ensemble_meta.json").read_text())
            self.assertIn(STRUCTURAL_LAYER, meta["layers_present"])
            self.assertEqual(meta["structural_prior"]["lambda_h"], 0.0)
            self.assertEqual(meta["structural_prior"]["lambda_h_status"], "UNMEASURED")
            self.assertIn("dispatch-conditional", meta["label"])
            self.assertIn("fleet-path structural error", meta["label"])

    def test_stale_iso_label_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self._seed_ensemble_dir(Path(tmp))
            prior = _degenerate_prior(bias=0.1, scale=0.05)
            stale = StructuralPrior.from_dict(
                {
                    **prior.to_dict(),
                    "isos": {
                        "ERCOT": {
                            **prior.to_dict()["isos"]["ERCOT"],
                            "basis_stale": True,
                            "rescore": "stale-registration-basis",
                        }
                    },
                }
            )
            append_structural_layer(out, stale)
            meta = json.loads((out / "ensemble_meta.json").read_text())
            self.assertIn("BASIS-STALE", meta["label"])
            self.assertTrue(meta["structural_prior"]["iso_basis_stale"])


if __name__ == "__main__":
    unittest.main()
