"""Tests for the non-fossil / imports hourly Charts-tab panels (``nonfossilHr``).

The panels (``render_calibration_html.build_nonfossil_hourly``) close the Charts
tab's fossil-only blind spot: nuclear, hydro, the renewables, oil, "other" and
net interchange had no hourly actual anywhere in the payload, only annual
scalars, so a class could pass the annual-volume gate while being wrong in every
hour and nothing on the dashboard could show it.

Four things here are load-bearing enough to be worth a guard, because each fails
SILENTLY — the map still renders, it just lies:

  1. **Crosswalk coverage** — every non-fossil taxonomy class must route into a
     panel, or a class quietly gets no view (and a bucket must never double-count
     a class into two panels).
  2. **Imports sign convention** — the model's ``import`` klass is positive INTO
     the ISO, EIA-930 "Total interchange" is positive EXPORT. Get it backwards
     and the heatmap is exactly inverted: magnitudes right, every color flipped.
  3. **MW-space delta** — the panel's model and actual series must decode on ONE
     shared scale. A CF%-vs-CF% difference (each series normalized to its own
     max) produces a beautiful, meaningless map.
  4. **Clock alignment** — a one-hour pairing error manufactures a fake diurnal
     band, which is exactly what happened to the LMP delta map (see
     docs/DIAGNOSIS-ercot-lmp-clock-artifact-and-summer-residuals-2026-07.md).

Trivial cases first (1 class, 24 hours), then the real committed keeper payload.
"""

from __future__ import annotations

import base64
import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[1]


def _load(mod_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(
        mod_name, str(_REPO / "scripts" / filename)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rch = _load("rch_nfhr", "render_calibration_html.py")

# The committed NYISO keeper: the run this instrument was built to read, and the
# only bundle guaranteed to carry the hourly/ sidecars these tests need.
_KEEPER_BUNDLE = _REPO / "results" / "calibration" / "nyiso72_netrev_margin"
_CALIB_YEARS = (2023, 2024, 2025)  # rule 22 in-sample window; NEVER widen here


def _decode(entry: dict, key: str = "m") -> np.ndarray:
    """Decode a panel series back to MW, exactly as the browser's decAffine does."""
    raw = np.frombuffer(base64.b64decode(entry[key]), dtype=np.uint8).astype(float)
    lo, hi = float(entry["lo"]), float(entry["hi"])
    return lo + raw / rch._B64_SCALE * (hi - lo)


# --------------------------------------------------------------------------- #
# 1. Crosswalk coverage (taxonomy-driven, no per-ISO branching)
# --------------------------------------------------------------------------- #
class TestCrosswalkCoverage(unittest.TestCase):
    def test_every_nonfossil_class_routes_into_exactly_one_panel(self):
        """No non-fossil class may be unreachable or land in two panels."""
        seen: dict[str, list[str]] = {}
        for panel in rch.NONFOSSIL_930_SERIES:
            for klass in rch.classes_for_fuel930(panel):
                if klass in rch._NONFOSSIL_KLASS:
                    seen.setdefault(klass, []).append(panel)
        missing = sorted(rch._NONFOSSIL_KLASS - set(seen))
        self.assertEqual(
            missing,
            [],
            f"non-fossil classes with no Charts-tab panel: {missing}. Add the "
            "class's EIA-930 fuel bucket to NONFOSSIL_930_SERIES (with its "
            "NG: XXX citation) — otherwise it silently has no hourly view.",
        )
        dupes = {k: v for k, v in seen.items() if len(v) > 1}
        self.assertEqual(dupes, {}, f"classes double-counted across panels: {dupes}")

    def test_panels_are_nonfossil_buckets_only(self):
        """A fossil bucket must never appear — those are the CAMPD-backed path."""
        for panel in rch.NONFOSSIL_930_SERIES:
            classes = rch.classes_for_fuel930(panel)
            self.assertTrue(
                classes, f"panel {panel!r} maps to no taxonomy class at all"
            )
            self.assertFalse(
                any(c in rch.FOSSIL_GROUPS for c in classes),
                f"panel {panel!r} includes fossil classes {classes} — fossil "
                "classes are scored against CAMPD CEMS, not EIA-930.",
            )

    def test_every_panel_has_a_display_label(self):
        for panel in (*rch.NONFOSSIL_930_SERIES, rch.IMPORT_PANEL):
            self.assertIn(panel, rch.NONFOSSIL_PANEL_LABEL)

    def test_wind_bucket_sums_both_wind_classes(self):
        """Regression: the bucket, not one leg, is compared to the NG: WND meter."""
        self.assertEqual(
            set(rch.classes_for_fuel930("wind")), {"wind", "offshore_wind"}
        )
        mh = {
            "wind": np.full(24, 100.0),
            "offshore_wind": np.full(24, 50.0),
        }
        panels = rch.build_nonfossil_hourly(mh, {"wind": np.full(24, 120.0)}, hours=24)
        self.assertEqual(set(panels["wind"]["classes"]), {"wind", "offshore_wind"})
        self.assertAlmostEqual(panels["wind"]["mTwh"], 24 * 150.0 / 1e6, places=6)


# --------------------------------------------------------------------------- #
# 2. Imports sign convention
# --------------------------------------------------------------------------- #
class TestImportsSign(unittest.TestCase):
    def test_930_export_positive_is_negated_to_import_positive(self):
        """Trivial case: 24 h of steady net import, both sides.

        Model ``import`` klass = +1000 MW (into the ISO). EIA-930 reports the
        same physical flow as -1000 MW (export-positive). The panel must publish
        BOTH as +1000 MW, and the delta must be ~zero — not 2000 MW.
        """
        panels = rch.build_nonfossil_hourly(
            {"import": np.full(24, 1000.0)},
            {"interchange": np.full(24, -1000.0)},
            hours=24,
        )
        imp = panels[rch.IMPORT_PANEL]
        self.assertGreater(imp["mTwh"], 0, "model imports must be import-positive")
        self.assertGreater(
            imp["aTwh"], 0, "930 interchange must be NEGATED to import-positive"
        )
        m, a = _decode(imp, "m"), _decode(imp, "a")
        np.testing.assert_allclose(m, 1000.0, atol=1.0)
        np.testing.assert_allclose(a, 1000.0, atol=1.0)
        self.assertLess(
            float(np.abs(m - a).max()),
            5.0,
            "an inverted interchange sign shows up here as a ~2x delta",
        )

    def test_net_exporter_stays_negative(self):
        """A genuinely exporting hour must read NEGATIVE in the import-positive
        convention — the codec's signed handling, not an absolute value."""
        panels = rch.build_nonfossil_hourly(
            {"import": np.full(24, -500.0)},
            {"interchange": np.full(24, 500.0)},
            hours=24,
        )
        imp = panels[rch.IMPORT_PANEL]
        self.assertLess(imp["mTwh"], 0)
        self.assertLess(imp["aTwh"], 0)
        np.testing.assert_allclose(_decode(imp, "m"), -500.0, atol=1.0)

    def test_reconciler_rejects_an_inverted_import_panel(self):
        """The build-time guard must FAIL a payload whose import sign is flipped.

        This is the assertion that protects the render path, so it needs its own
        negative test: a hand-inverted panel against a correct ``fuelRows``
        interchange row (export-positive) must raise.
        """
        mh = {"import": np.full(24, 1000.0)}
        panels = rch.build_nonfossil_hourly(
            mh, {"interchange": np.full(24, -1000.0)}, hours=24
        )
        fuel_rows = [{"fuel": "interchange", "m": -0.024, "b": -0.024}]
        # Correct payload passes.
        rch._assert_nonfossil_hourly_reconciles(
            panels, mh, fuel_rows, iso="TEST", year=2023, hours=24
        )
        # Inverted payload must not.
        bad = {k: dict(v) for k, v in panels.items()}
        bad[rch.IMPORT_PANEL]["mTwh"] = -bad[rch.IMPORT_PANEL]["mTwh"]
        with self.assertRaises(AssertionError):
            rch._assert_nonfossil_hourly_reconciles(
                bad, mh, fuel_rows, iso="TEST", year=2023, hours=24
            )

    def test_reconciler_rejects_a_mis_summed_bucket(self):
        mh = {"nuclear": np.full(24, 1000.0)}
        panels = rch.build_nonfossil_hourly(
            mh, {"nuclear": np.full(24, 900.0)}, hours=24
        )
        bad = {k: dict(v) for k, v in panels.items()}
        bad["nuclear"]["mTwh"] = bad["nuclear"]["mTwh"] * 2
        with self.assertRaises(AssertionError):
            rch._assert_nonfossil_hourly_reconciles(
                bad, mh, [], iso="TEST", year=2023, hours=24
            )


# --------------------------------------------------------------------------- #
# 3. Codec round-trip and the MW-space (not CF-space) delta
# --------------------------------------------------------------------------- #
class TestAffineCodec(unittest.TestCase):
    def test_roundtrip_within_quantization(self):
        """Decoded MW must be within one quantization step of the input."""
        rng = np.random.default_rng(0)
        mw = rng.uniform(-2000.0, 6000.0, 24)
        lo, hi = float(mw.min()), float(mw.max())
        enc = rch._b64_affine(mw, lo, hi)
        got = _decode({"m": enc, "lo": lo, "hi": hi})
        step = (hi - lo) / rch._B64_SCALE
        np.testing.assert_allclose(got, mw, atol=step)

    def test_degenerate_flat_series_decodes_exactly(self):
        enc = rch._b64_affine(np.full(24, 700.0), 700.0, 700.0)
        got = _decode({"m": enc, "lo": 700.0, "hi": 700.0})
        np.testing.assert_allclose(got, 700.0)

    def test_model_and_actual_share_one_decode_window(self):
        """THE MW-space guarantee.

        Model peaks at 1000 MW, actual at 100 MW — a 10x scale gap. Decoded on
        the panel's shared window their difference is the true ~900 MW delta.
        Normalizing each to its OWN max (what the CF heatmaps do, which is why
        the delta is NOT computed from them) would make both peak at "100%" and
        report a delta of zero — a beautiful, wrong map.
        """
        model = np.concatenate([np.full(12, 1000.0), np.zeros(12)])
        actual = np.concatenate([np.full(12, 100.0), np.zeros(12)])
        panels = rch.build_nonfossil_hourly(
            {"nuclear": model}, {"nuclear": actual}, hours=24
        )
        e = panels["nuclear"]
        self.assertEqual(e["lo"], 0.0)
        self.assertEqual(e["hi"], 1000.0, "window must span BOTH series")
        delta = _decode(e, "m") - _decode(e, "a")
        np.testing.assert_allclose(delta[:12], 900.0, atol=5.0)
        np.testing.assert_allclose(delta[12:], 0.0, atol=5.0)
        # The CF-space trap, asserted explicitly so nobody "simplifies" into it.
        cf_delta = (model / model.max() * 100) - (actual / actual.max() * 100)
        self.assertAlmostEqual(
            float(np.abs(cf_delta).max()),
            0.0,
            places=6,
            msg="CF-space delta is identically zero here — this is the bug the "
            "shared [lo, hi] window exists to prevent.",
        )


# --------------------------------------------------------------------------- #
# 4. Absent actuals are never a zero
# --------------------------------------------------------------------------- #
class TestAbsentActual(unittest.TestCase):
    def test_all_zero_series_is_absent_not_zero(self):
        """NYISO files no utility-scale solar: its NG: SUN cell reads 0.0.

        That is 'not reported', not 'zero generation' — comparing ~2 TWh of
        modelled solar against it would manufacture a -100% error and a fully
        saturated delta map.
        """
        panels = rch.build_nonfossil_hourly(
            {"solar": np.full(24, 500.0)}, {"solar": np.zeros(24)}, hours=24
        )
        e = panels["solar"]
        self.assertIsNone(e["a"], "an all-zero 930 series must be treated absent")
        self.assertIsNone(e["aTwh"])
        self.assertIsNone(e["r"])
        self.assertIsNotNone(e["note"], "the absence must carry a labelled reason")

    def test_missing_series_is_absent(self):
        panels = rch.build_nonfossil_hourly({"hydro": np.full(24, 500.0)}, {}, hours=24)
        self.assertIsNone(panels["hydro"]["a"])

    def test_undispatched_class_yields_no_panel(self):
        panels = rch.build_nonfossil_hourly(
            {"nuclear": np.full(24, 100.0)}, {"hydro": np.full(24, 50.0)}, hours=24
        )
        self.assertNotIn("hydro", panels, "a class the run never dispatched")
        self.assertNotIn(rch.IMPORT_PANEL, panels)


# --------------------------------------------------------------------------- #
# 5. Clock alignment + reconciliation against the real committed keeper
# --------------------------------------------------------------------------- #
@unittest.skipUnless(
    (_KEEPER_BUNDLE / "hourly").is_dir(),
    f"needs the committed keeper hourly/ sidecars at {_KEEPER_BUNDLE}",
)
class TestAgainstCommittedKeeper(unittest.TestCase):
    """End-to-end on the NYISO keeper, restricted to the rule-22 window."""

    @classmethod
    def setUpClass(cls):
        import sys

        sys.path.insert(0, str(_REPO / "src"))
        from market_sim.data.eia930.actuals import load_eia_hourly_benchmark

        cls._load930 = staticmethod(load_eia_hourly_benchmark)

    def _model_hourly(self, year: int) -> dict[str, np.ndarray]:
        df = pd.read_parquet(_KEEPER_BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
        df = df[df["pass"].astype(str) == "P1"]
        return {
            str(k): g.set_index("hour")["mw"]
            .reindex(range(8760), fill_value=0.0)
            .to_numpy(float)
            for k, g in df.groupby("klass", observed=True)
        }

    def test_only_in_sample_years_are_present(self):
        """Rule 22: the keeper bundle must carry no out-of-training year.

        A heatmap of a quarantined year is a scoring event, so this guards the
        input side of the instrument as well as the renderer's own year gate.
        """
        have = sorted(
            int(p.stem.rsplit("_", 1)[1])
            for p in (_KEEPER_BUNDLE / "hourly").glob("class_hourly_*.parquet")
        )
        self.assertEqual(have, list(_CALIB_YEARS))

    def test_clock_alignment_lag_zero_dominates(self):
        """Model and EIA-930 must be on the SAME hourly clock.

        Cross-correlate the model's own demand against the 930 demand implied by
        the BA's net generation and interchange. Lag 0 must win; a +/-1 h winner
        means every panel is paired one hour off and would show a manufactured
        diurnal band.
        """
        for year in _CALIB_YEARS:
            sysf = _KEEPER_BUNDLE / "hourly" / f"system_{year}.parquet"
            if not sysf.exists():
                self.skipTest(f"no system sidecar for {year}")
            sy = pd.read_parquet(sysf)
            sy = sy[sy["pass"].astype(str) == "P1"]
            model = (
                sy.groupby("hour")["demand"]
                .sum()
                .reindex(range(8760), fill_value=0.0)
                .to_numpy(float)
            )
            b = self._load930("NYISO", year)
            actual = b["net_gen"] - b["interchange"]
            scores = {}
            for lag in (-2, -1, 0, 1, 2):
                x = model[lag:] if lag > 0 else model[: 8760 + lag or None]
                y = actual[: 8760 - lag] if lag > 0 else actual[-lag or None :]
                n = min(len(x), len(y))
                scores[lag] = float(np.corrcoef(x[:n], y[:n])[0, 1])
            best = max(scores, key=lambda k: scores[k])
            self.assertEqual(
                best,
                0,
                f"NYISO {year}: clock misaligned, best lag {best:+d} "
                f"(r={scores[best]:.4f}) beats lag 0 (r={scores[0]:.4f})",
            )

    def test_panels_reconcile_to_the_class_dispatch(self):
        for year in _CALIB_YEARS:
            mh = self._model_hourly(year)
            b = self._load930("NYISO", year)
            panels = rch.build_nonfossil_hourly(mh, b)
            self.assertIn("nuclear", panels)
            self.assertIn(rch.IMPORT_PANEL, panels)
            # Raises on a mis-summed bucket or an inverted import sign.
            rch._assert_nonfossil_hourly_reconciles(
                panels, mh, [], iso="NYISO", year=year
            )
            for panel, e in panels.items():
                decoded = _decode(e, "m")
                step = (e["hi"] - e["lo"]) / rch._B64_SCALE
                want = sum(mh[c] for c in e["classes"])
                np.testing.assert_allclose(
                    decoded,
                    want,
                    atol=max(step, 1.0),
                    err_msg=f"{year} {panel}: decoded model series drifted",
                )

    def test_known_nyiso_signatures(self):
        """Pin the evidence this instrument was built to show (2023).

        Not a tuning target — a canary: if the keeper bundle or the 930 extract
        is ever swapped underneath, these move and the finding doc's numbers
        (docs/FINDING-nyiso-class-delta-shape-2026-07-24.md) go stale silently.
        """
        mh = self._model_hourly(2023)
        panels = rch.build_nonfossil_hourly(mh, self._load930("NYISO", 2023))
        self.assertAlmostEqual(panels["nuclear"]["mTwh"], 27.489, places=2)
        self.assertAlmostEqual(panels["nuclear"]["aTwh"], 23.998, places=2)
        self.assertAlmostEqual(panels["nuclear"]["r"], 0.831, places=2)
        # Imports: right on annual volume (~2%), wrong in every hour (r ~0.47).
        self.assertAlmostEqual(panels[rch.IMPORT_PANEL]["mTwh"], 23.923, places=2)
        self.assertAlmostEqual(panels[rch.IMPORT_PANEL]["aTwh"], 23.454, places=2)
        self.assertLess(panels[rch.IMPORT_PANEL]["r"], 0.6)
        # NYISO files no utility-scale solar series.
        self.assertIsNone(panels["solar"]["a"])


if __name__ == "__main__":
    unittest.main()
