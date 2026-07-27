"""ERCOT-118 EP-basis rebasis of the measured CC DAM band multipliers.

Pins the mechanism seams the ercot-115 promotion taught us to pin
(``tests/test_coal_econ_marginal_hr_bound.py`` conventions): the committed
artifact's structure, the apply function's replace+delta composition (and its
peak_ladder / margin_anchor side-writes), the default-off byte-identity, the
ERCOT-only scoping, the tri-state CLI default, the cache-key neutrality at
default, and the per-tranche anchor override inside
``apply_gas_offer_margin``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from market_sim.config import paths
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.offer_curves import (
    apply_ercot_dam_hrmult_ep_rebasis,
    apply_gas_offer_margin,
    band_margin_anchor,
)

ARTIFACT = paths.CALIBRATION_DIR / "offer_curve_dam_hrmults_ep_yearly.json"
YEARS = ("2023", "2024", "2025")
CLASSES = ("CC_REGULAR", "CC_CHP")
# The measured energy-curve bands; committed is deliberately ABSENT (its Min
# Gen Cost source rows were dropped by the owner-ordered 2026-07-22 raw
# slimming and 2023 is unreachable on the free MIS path — see the artifact's
# _provenance.committed_band).
BANDS = ("econ_low", "econ_high", "peak")


class TestArtifact:
    def test_structure(self):
        doc = json.loads(ARTIFACT.read_text())
        assert doc["_provenance"]["iso"] == "ERCOT"
        assert "rule23_citation" in doc["_provenance"]
        assert "committed_band" in doc["_provenance"]
        for y in YEARS:
            table = doc[y]
            assert table["anchor_usd_mmbtu"] > 0
            for cls in CLASSES:
                bands = table[cls]
                assert set(bands) == set(BANDS)
                for v in bands.values():
                    assert 0.3 < v < 8.0
                assert "committed" not in bands

    def test_anchor_is_ep_delivered_mean(self):
        # anchor = mean(HH_monthly) + ep_basis — the EP series annual mean on
        # the model's own HH table (the identification fuel of the year's
        # multipliers).
        from market_sim.data.fuel._shared import _pkg_ns
        from market_sim.data.fuel.basis.ercot import (
            ercot_electric_power_gas_basis,
        )

        doc = json.loads(ARTIFACT.read_text())
        hh = _pkg_ns()._henry_hub_monthly(None)
        for y in YEARS:
            year = int(y)
            hh_mean = float(
                np.mean([hh[(year, m)] for m in range(1, 13) if (year, m) in hh])
            )
            expected = hh_mean + ercot_electric_power_gas_basis(year)
            assert doc[y]["anchor_usd_mmbtu"] == pytest.approx(expected, abs=1e-3)


class TestApply:
    CURVE = {
        "CC_REGULAR": {
            "committed": 0.998,
            "econ_low": 0.723,
            "econ_high": 1.324,
            "peak": 4.576,
            "phys_committed": 1.006,
            "peak_ladder": [[0.2, 4.576]] * 5,
        },
        "CC_CHP": {"econ_low": 0.946, "econ_high": 1.857, "peak": 3.748},
        "CT_PEAKER": {"committed": 1.1, "peak": 13.15},
    }
    DELTAS = {
        "CC_REGULAR": {
            "committed": -0.05,
            "econ_low": -0.24,
            "econ_high": -0.13,
            "peak": 0.25,
        },
        "CC_CHP": {"econ_high": 0.43, "peak": -0.5, "pct_peaking": -4.0},
    }

    def test_replace_plus_delta_composition(self):
        doc = json.loads(ARTIFACT.read_text())
        curve, replaced, anchor = apply_ercot_dam_hrmult_ep_rebasis(
            self.CURVE, 2024, self.DELTAS
        )
        t = doc["2024"]
        assert anchor == pytest.approx(t["anchor_usd_mmbtu"])
        # Rebased band = artifact value + the run's delta for that band.
        assert curve["CC_REGULAR"]["econ_high"] == pytest.approx(
            t["CC_REGULAR"]["econ_high"] - 0.13
        )
        assert curve["CC_REGULAR"]["econ_low"] == pytest.approx(
            t["CC_REGULAR"]["econ_low"] - 0.24
        )
        assert curve["CC_REGULAR"]["peak"] == pytest.approx(
            t["CC_REGULAR"]["peak"] + 0.25
        )
        assert curve["CC_CHP"]["econ_high"] == pytest.approx(
            t["CC_CHP"]["econ_high"] + 0.43
        )
        # committed is not in the artifact -> untouched keeper value.
        assert curve["CC_REGULAR"]["committed"] == 0.998
        # phys_* keys survive; non-rebased classes byte-identical.
        assert curve["CC_REGULAR"]["phys_committed"] == 1.006
        assert curve["CT_PEAKER"] == self.CURVE["CT_PEAKER"]
        # 3 bands x 2 classes audited.
        assert len(replaced) == 6

    def test_peak_ladder_restamped_and_anchor_threaded(self):
        doc = json.loads(ARTIFACT.read_text())
        curve, _, anchor = apply_ercot_dam_hrmult_ep_rebasis(
            self.CURVE, 2023, self.DELTAS
        )
        new_pk = doc["2023"]["CC_REGULAR"]["peak"] + 0.25
        assert curve["CC_REGULAR"]["peak_ladder"] == [[0.2, pytest.approx(new_pk)]] * 5
        for cls in CLASSES:
            assert curve[cls]["margin_anchor"] == pytest.approx(anchor)
        assert "margin_anchor" not in curve["CT_PEAKER"]

    def test_missing_year_hard_fails(self):
        with pytest.raises(KeyError):
            apply_ercot_dam_hrmult_ep_rebasis(self.CURVE, 1999, None)

    def test_input_curve_not_mutated(self):
        before = json.dumps(self.CURVE, sort_keys=True)
        apply_ercot_dam_hrmult_ep_rebasis(self.CURVE, 2025, self.DELTAS)
        assert json.dumps(self.CURVE, sort_keys=True) == before


class TestBandScope:
    """ERCOT-119 leg-split: the ``bands`` scope on the apply function."""

    ECON = ["econ_low", "econ_high"]

    def test_econ_scope_keeps_peak_wall(self):
        doc = json.loads(ARTIFACT.read_text())
        curve, replaced, anchor = apply_ercot_dam_hrmult_ep_rebasis(
            TestApply.CURVE, 2024, TestApply.DELTAS, bands=self.ECON
        )
        t = doc["2024"]
        # Econ bands rebased (artifact + delta), exactly as unscoped.
        assert curve["CC_REGULAR"]["econ_low"] == pytest.approx(
            t["CC_REGULAR"]["econ_low"] - 0.24
        )
        assert curve["CC_REGULAR"]["econ_high"] == pytest.approx(
            t["CC_REGULAR"]["econ_high"] - 0.13
        )
        # Peak (and its delta) untouched: the run's resolved standing wall.
        assert curve["CC_REGULAR"]["peak"] == TestApply.CURVE["CC_REGULAR"]["peak"]
        assert curve["CC_CHP"]["peak"] == TestApply.CURVE["CC_CHP"]["peak"]
        # peak_ladder rungs NOT re-stamped (peak out of scope).
        assert (
            curve["CC_REGULAR"]["peak_ladder"]
            == TestApply.CURVE["CC_REGULAR"]["peak_ladder"]
        )
        # committed keeps the keeper's resolved value; non-rebased classes
        # byte-identical.
        assert curve["CC_REGULAR"]["committed"] == 0.998
        assert curve["CT_PEAKER"] == TestApply.CURVE["CT_PEAKER"]
        # 2 bands x 2 classes audited.
        assert len(replaced) == 4
        assert {b for _, b, _, _ in replaced} == set(self.ECON)
        # Anchor threading is band-scoped: no class-wide margin_anchor, no
        # peak anchor — the un-rebased peak markup stays on the window anchor.
        for cls in CLASSES:
            assert "margin_anchor" not in curve[cls]
            assert "margin_anchor_peak" not in curve[cls]
            assert curve[cls]["margin_anchor_econ_low"] == pytest.approx(anchor)
            assert curve[cls]["margin_anchor_econ_high"] == pytest.approx(anchor)

    def test_peak_scope_restamps_ladder(self):
        doc = json.loads(ARTIFACT.read_text())
        curve, replaced, _ = apply_ercot_dam_hrmult_ep_rebasis(
            TestApply.CURVE, 2023, TestApply.DELTAS, bands=["peak"]
        )
        new_pk = doc["2023"]["CC_REGULAR"]["peak"] + 0.25
        assert curve["CC_REGULAR"]["peak"] == pytest.approx(new_pk)
        assert curve["CC_REGULAR"]["peak_ladder"] == [[0.2, pytest.approx(new_pk)]] * 5
        # Econ bands untouched.
        assert (
            curve["CC_REGULAR"]["econ_low"] == TestApply.CURVE["CC_REGULAR"]["econ_low"]
        )
        assert len(replaced) == 2
        assert "margin_anchor" not in curve["CC_REGULAR"]
        assert "margin_anchor_peak" in curve["CC_REGULAR"]

    def test_unknown_band_hard_fails(self):
        with pytest.raises(ValueError, match="not in the 2024 artifact"):
            apply_ercot_dam_hrmult_ep_rebasis(
                TestApply.CURVE, 2024, None, bands=["econ_low", "commited"]
            )

    def test_none_scope_is_ercot118_byte_identical(self):
        unscoped, r1, a1 = apply_ercot_dam_hrmult_ep_rebasis(
            TestApply.CURVE, 2025, TestApply.DELTAS
        )
        explicit, r2, a2 = apply_ercot_dam_hrmult_ep_rebasis(
            TestApply.CURVE, 2025, TestApply.DELTAS, bands=None
        )
        assert json.dumps(unscoped, sort_keys=True) == json.dumps(
            explicit, sort_keys=True
        )
        assert r1 == r2 and a1 == a2


class TestBandMarginAnchor:
    """Per-tranche anchor resolution against band-scoped and class-wide keys."""

    SCOPED = {
        "margin_anchor_econ_low": 2.1067,
        "margin_anchor_econ_high": 2.1067,
    }
    CLASSWIDE = {"margin_anchor": 3.0655}

    def test_scoped_keys_resolve_by_suffix(self):
        assert band_margin_anchor("econlo", self.SCOPED) == pytest.approx(2.1067)
        assert band_margin_anchor("econhi", self.SCOPED) == pytest.approx(2.1067)
        # Smoothing slices interpolate along the lo->hi ramp: both endpoint
        # anchors present -> the shared anchor.
        assert band_margin_anchor("econc50", self.SCOPED) == pytest.approx(2.1067)
        # Out-of-scope bands fall through to the window anchor (None).
        assert band_margin_anchor("peak", self.SCOPED) is None
        assert band_margin_anchor("peak_l3", self.SCOPED) is None
        assert band_margin_anchor("committed", self.SCOPED) is None

    def test_econ_slice_requires_both_endpoints(self):
        only_hi = {"margin_anchor_econ_high": 2.1067}
        assert band_margin_anchor("econc50", only_hi) is None
        assert band_margin_anchor("econhi", only_hi) == pytest.approx(2.1067)

    def test_classwide_fallback_and_absence(self):
        for sfx in ("econlo", "econhi", "econc25", "peak", "peak_l1", "committed"):
            assert band_margin_anchor(sfx, self.CLASSWIDE) == pytest.approx(3.0655)
            assert band_margin_anchor(sfx, {}) is None

    def test_scoped_key_precedes_classwide(self):
        offer = {**self.CLASSWIDE, **self.SCOPED}
        assert band_margin_anchor("econhi", offer) == pytest.approx(2.1067)
        # peak has no scoped key -> class-wide fallback.
        assert band_margin_anchor("peak", offer) == pytest.approx(3.0655)


class TestScoping:
    def test_default_off_and_cache_neutral(self):
        cfg = ScenarioConfig()
        assert cfg.ercot_offer_hrmult_ep_rebasis is False
        base_key = cfg.cache_key()
        # Registered in _CACHE_KEY_OPTIONAL_FIELDS: default drops from the
        # hash; an armed run enters as a distinct scenario.
        armed = cfg.with_overrides(ercot_offer_hrmult_ep_rebasis=True)
        assert armed.cache_key() != base_key
        from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS

        assert "ercot_offer_hrmult_ep_rebasis" in _CACHE_KEY_OPTIONAL_FIELDS

    def test_bands_default_none_and_cache_neutral(self):
        # ERCOT-119: the band scope defaults to None (all artifact bands) and
        # is cache-neutral at that default; a scoped run — and a scoped run
        # vs the unscoped armed run — enters as a distinct scenario.
        cfg = ScenarioConfig()
        assert cfg.ercot_offer_hrmult_ep_rebasis_bands is None
        base_key = cfg.cache_key()
        assert (
            cfg.with_overrides(
                ercot_offer_hrmult_ep_rebasis_bands=["econ_low", "econ_high"]
            ).cache_key()
            != base_key
        )
        armed = cfg.with_overrides(ercot_offer_hrmult_ep_rebasis=True)
        scoped = armed.with_overrides(
            ercot_offer_hrmult_ep_rebasis_bands=["econ_low", "econ_high"]
        )
        assert scoped.cache_key() != armed.cache_key()
        from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS

        assert "ercot_offer_hrmult_ep_rebasis_bands" in _CACHE_KEY_OPTIONAL_FIELDS

    def test_run_year_kwarg_is_tristate(self):
        import inspect
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
        import run_calibration as rc
        import run_calibration_full as rcf

        for fn in (rc.run_year, rcf.solve_and_persist):
            for name in (
                "ercot_offer_hrmult_ep_rebasis",
                "ercot_offer_hrmult_ep_rebasis_bands",
            ):
                p = inspect.signature(fn).parameters[name]
                assert p.default is None, (
                    "tri-state None default (the ercot-115 seam lesson: a "
                    "non-None default would pass an explicit scrub on every "
                    "invocation)"
                )

    def test_cli_default_is_none(self):
        # The hand-written run_calibration_full argparse must carry default
        # None for the flag (tri-state; the --no- form still forces it off)
        # and for the ERCOT-119 band-scope flag.
        import ast

        src = (
            Path(__file__).resolve().parents[3] / "scripts/run_calibration_full.py"
        ).read_text()
        tree = ast.parse(src)
        found = set()
        flags = {
            "--ercot-offer-hrmult-ep-rebasis",
            "--ercot-offer-hrmult-ep-rebasis-bands",
        }
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node.func, "attr", "") == "add_argument"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value in flags
            ):
                for kw in node.keywords:
                    if kw.arg == "default":
                        assert (
                            isinstance(kw.value, ast.Constant)
                            and kw.value.value is None
                        )
                        found.add(node.args[0].value)
        assert found == flags


class _Gen:
    def __init__(self, markup_hr, anchor=None):
        self.offer_markup_hr = markup_hr
        self.offer_margin_anchor = anchor


class TestPerTrancheAnchor:
    def test_override_prices_at_per_class_anchor(self):
        cfg = ScenarioConfig().with_overrides(
            gas_offer_net_revenue_margin=True, gas_offer_margin_anchor=2.2494
        )
        gens = [_Gen(0.0), _Gen(2.0), _Gen(2.0, anchor=3.0655)]
        mc = np.zeros((3, 4))
        fp = np.full((3, 4), 2.0)
        apply_gas_offer_margin(mc, gens, fp, cfg)
        assert np.allclose(mc[0], 0.0)
        assert np.allclose(mc[1], 2.0 * (2.2494 - 2.0))
        assert np.allclose(mc[2], 2.0 * (3.0655 - 2.0))

    def test_no_override_is_bit_identical_to_scalar_form(self):
        cfg = ScenarioConfig().with_overrides(
            gas_offer_net_revenue_margin=True, gas_offer_margin_anchor=2.2494
        )
        gens = [_Gen(1.7), _Gen(0.3)]
        rng = np.random.default_rng(7)
        fp = rng.uniform(1.0, 6.0, (2, 8))
        mc_new = np.zeros((2, 8))
        apply_gas_offer_margin(mc_new, gens, fp, cfg)
        markup = np.array([1.7, 0.3])
        mc_ref = markup[:, None] * (2.2494 - fp)
        assert (mc_new == mc_ref).all()
