"""Tests for the D-11 knob-perturbation Jacobian harness (scripts/knob_jacobian.py).

Trivial cases first per the repo testing pattern: the expensive solve/score
steps are dependency-injected (``solve_fn``/``score_fn``), so the whole
pipeline — knob discovery, +-10% perturbation, finite-difference ranking,
JSON schema, CLI wiring — is exercised on tiny synthetic fixtures with no LP
solve and no real calibration bundle. A real end-to-end run against a keeper
bundle is a separate, solve-expensive release-cadence task (see the module
docstring and CLAUDE.md rule 12); it is NOT exercised here.
"""

from __future__ import annotations

import json
import math

import pytest

from scripts import knob_jacobian as kj


# ---------------------------------------------------------------------------
# Knob discovery
# ---------------------------------------------------------------------------
def test_offer_band_knobs_restricted_to_price_bands():
    curves = {
        "CT_PEAKER": {
            "committed": 1.10,
            "econ_low": 0.90,
            "econ_high": 1.20,
            "peak": 1.30,
            "econ_low_share": 0.4,  # not a price band -> excluded
            "pct_peaking": 15.0,  # not a price band -> excluded
        },
        "CC_REGULAR": {"committed": 1.0},
    }
    knobs = kj.offer_band_knobs(curves)
    names = {k.name for k in knobs}
    assert names == {
        "offer_curve_by_group.CT_PEAKER.committed",
        "offer_curve_by_group.CT_PEAKER.econ_low",
        "offer_curve_by_group.CT_PEAKER.econ_high",
        "offer_curve_by_group.CT_PEAKER.peak",
        "offer_curve_by_group.CC_REGULAR.committed",
    }
    ct_peak = next(k for k in knobs if k.name.endswith("CT_PEAKER.peak"))
    assert ct_peak.klass == "CT_PEAKER"
    assert ct_peak.band == "peak"
    assert ct_peak.value == pytest.approx(1.30)


def test_scalar_knobs_only_engaged_at_nondefault():
    sc = {
        "wefor_multiplier": 1.0,  # default -> excluded
        "battery_dispatch_adder": 12.5,  # engaged -> included
        "pumped_storage_dispatch_adder": 0.0,  # default -> excluded
    }
    knobs = kj.scalar_knobs(sc)
    assert [k.name for k in knobs] == ["battery_dispatch_adder"]
    assert knobs[0].value == pytest.approx(12.5)
    assert knobs[0].klass is None and knobs[0].band is None


def test_discover_knobs_reads_ledger_and_run_config(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "run_config.json").write_text(
        json.dumps(
            {
                "scenario_config": {
                    "offer_curve_by_group": {
                        "CT_PEAKER": {"committed": 1.1, "peak": 1.3},
                    },
                    "battery_dispatch_adder": 10.0,
                }
            }
        )
    )
    knobs = kj.discover_knobs(bundle, "ERCOT")
    names = {k.name for k in knobs}
    assert "offer_curve_by_group.CT_PEAKER.committed" in names
    assert "offer_curve_by_group.CT_PEAKER.peak" in names
    assert "battery_dispatch_adder" in names


def test_discover_knobs_empty_curves_yields_no_offer_knobs(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "run_config.json").write_text(json.dumps({"scenario_config": {}}))
    assert kj.discover_knobs(bundle, "ERCOT") == []


# ---------------------------------------------------------------------------
# Perturbation
# ---------------------------------------------------------------------------
def test_perturbed_override_offer_band():
    knob = kj.Knob(
        name="offer_curve_by_group.CT_PEAKER.peak",
        field="offer_curve_by_group",
        value=1.30,
        klass="CT_PEAKER",
        band="peak",
    )
    plus = kj.perturbed_override(knob, +1, frac=0.10)
    minus = kj.perturbed_override(knob, -1, frac=0.10)
    assert plus == {"offer_curve_by_group": {"CT_PEAKER": {"peak": 1.43}}}
    assert minus == {"offer_curve_by_group": {"CT_PEAKER": {"peak": 1.17}}}


def test_perturbed_override_scalar():
    knob = kj.Knob(
        name="battery_dispatch_adder", field="battery_dispatch_adder", value=10.0
    )
    plus = kj.perturbed_override(knob, +1, frac=0.10)
    assert plus == {"battery_dispatch_adder": 11.0}


def test_perturbed_override_rejects_bad_direction():
    knob = kj.Knob(name="x", field="x", value=1.0)
    with pytest.raises(ValueError):
        kj.perturbed_override(knob, 0)


def test_safe_slug_is_filesystem_safe():
    assert kj._safe_slug("offer_curve_by_group.CT_PEAKER.peak") == (
        "offer_curve_by_group.CT_PEAKER.peak"
    )
    assert "/" not in kj._safe_slug("a/b c*d")


# ---------------------------------------------------------------------------
# Finite-difference ranking
# ---------------------------------------------------------------------------
def _score(gas_twh, coal_twh, price_nrmse, shape_gas, shape_coal):
    return {
        "twh": {"CC_REGULAR": gas_twh, "COAL_PRB": coal_twh},
        "shape": {"gas": shape_gas, "coal": shape_coal},
        "price_nrmse": price_nrmse,
    }


def test_jacobian_row_finite_difference_math():
    knob = kj.Knob(
        name="k", field="offer_curve_by_group", value=1.0, klass="C", band="peak"
    )
    plus = _score(
        gas_twh=11.0, coal_twh=5.0, price_nrmse=0.20, shape_gas=0.30, shape_coal=0.10
    )
    minus = _score(
        gas_twh=9.0, coal_twh=5.0, price_nrmse=0.10, shape_gas=0.20, shape_coal=0.10
    )
    row = kj.jacobian_row(knob, plus, minus, frac=0.10)
    # step = 2 * |value| * frac = 0.2
    assert row["c2_gas_twh_per_unit"] == pytest.approx((11.0 - 9.0) / 0.2)
    assert row["c2_coal_twh_per_unit"] == pytest.approx(0.0)
    assert row["c3b_price_nrmse_per_unit"] == pytest.approx((0.20 - 0.10) / 0.2)
    assert row["c4_shape_gas_nrmse_per_unit"] == pytest.approx((0.30 - 0.20) / 0.2)
    assert row["twh_per_unit"]["CC_REGULAR"] == pytest.approx((11.0 - 9.0) / 0.2)
    assert row["max_abs_sensitivity"] == pytest.approx(
        max(
            abs(v)
            for v in (
                row["c2_gas_twh_per_unit"],
                row["c2_coal_twh_per_unit"],
                row["c3b_price_nrmse_per_unit"],
                row["c4_shape_gas_nrmse_per_unit"],
                row["c4_shape_coal_nrmse_per_unit"],
            )
        )
    )


def test_jacobian_row_handles_missing_metrics_gracefully():
    knob = kj.Knob(name="k", field="battery_dispatch_adder", value=10.0)
    plus = _score(1.0, 1.0, None, None, None)
    minus = _score(1.0, 1.0, None, None, None)
    row = kj.jacobian_row(knob, plus, minus, frac=0.10)
    assert row["c3b_price_nrmse_per_unit"] is None
    assert row["c4_shape_gas_nrmse_per_unit"] is None
    assert row["max_abs_sensitivity"] == 0.0


def test_finite_diff_none_on_nan_or_zero_step():
    assert kj._finite_diff(1.0, 0.5, 0.0) is None
    assert kj._finite_diff(None, 0.5, 1.0) is None
    assert kj._finite_diff(float("nan"), 0.5, 1.0) is None
    assert kj._finite_diff(1.5, 0.5, 2.0) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# compute_jacobian orchestration (fully stubbed solve/score — no LP, no I/O
# beyond the temp dirs pytest gives us)
# ---------------------------------------------------------------------------
def _stub_solve(bundle, iso, year, overrides, out_dir, reference):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "overrides.json").write_text(json.dumps(overrides))
    return out_dir


def _stub_score_factory():
    """Return a score_fn whose output varies deterministically with the
    overrides written by ``_stub_solve``, so the finite differences are
    non-trivial and knob-dependent (exercises real ranking, not all-zeros)."""

    def _score(out_dir, year):
        overrides = json.loads((out_dir / "overrides.json").read_text())
        # Turn the (single) override value into a small numeric perturbation
        # so different knobs produce different sensitivities.
        magnitude = 0.0
        for v in overrides.values():
            if isinstance(v, dict):
                for vv in v.values():
                    if isinstance(vv, dict):
                        magnitude += sum(vv.values())
                    else:
                        magnitude += vv
            else:
                magnitude += v
        return {
            "twh": {"CC_REGULAR": 10.0 + magnitude, "COAL_PRB": 5.0},
            "shape": {"gas": 0.2 + magnitude * 0.01, "coal": 0.1},
            "price_nrmse": 0.15 + magnitude * 0.001,
        }

    return _score


def test_compute_jacobian_two_sided_ranks_and_labels_diagnostic(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    knobs = [
        kj.Knob(
            name="offer_curve_by_group.CT_PEAKER.peak",
            field="offer_curve_by_group",
            value=1.30,
            klass="CT_PEAKER",
            band="peak",
        ),
        kj.Knob(
            name="offer_curve_by_group.CC_REGULAR.committed",
            field="offer_curve_by_group",
            value=1.00,
            klass="CC_REGULAR",
            band="committed",
        ),
    ]
    result = kj.compute_jacobian(
        bundle,
        "ERCOT",
        year=2024,
        knobs=knobs,
        solve_fn=_stub_solve,
        score_fn=_stub_score_factory(),
        out_root=tmp_path / "solves",
    )
    assert result["diagnostic"] is True
    assert result["schema"] == "knob-jacobian/v1"
    assert result["year"] == 2024
    assert result["one_sided"] is False
    assert result["n_knobs"] == 2
    assert len(result["rows"]) == 2
    # Two solves per knob (plus + minus), no baseline solve needed.
    solved = sorted(p.name for p in (tmp_path / "solves").iterdir())
    assert solved == [
        "offer_curve_by_group.CC_REGULAR.committed_minus",
        "offer_curve_by_group.CC_REGULAR.committed_plus",
        "offer_curve_by_group.CT_PEAKER.peak_minus",
        "offer_curve_by_group.CT_PEAKER.peak_plus",
    ]
    # Sorted descending by |sensitivity|.
    sens = [r["max_abs_sensitivity"] for r in result["rows"]]
    assert sens == sorted(sens, reverse=True)


def test_compute_jacobian_one_sided_solves_once_plus_shared_baseline(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    knobs = [
        kj.Knob(
            name="offer_curve_by_group.CT_PEAKER.peak",
            field="offer_curve_by_group",
            value=1.30,
            klass="CT_PEAKER",
            band="peak",
        ),
        kj.Knob(
            name="offer_curve_by_group.CC_REGULAR.committed",
            field="offer_curve_by_group",
            value=1.00,
            klass="CC_REGULAR",
            band="committed",
        ),
    ]
    result = kj.compute_jacobian(
        bundle,
        "ERCOT",
        knobs=knobs,
        one_sided=True,
        solve_fn=_stub_solve,
        score_fn=_stub_score_factory(),
        out_root=tmp_path / "solves",
    )
    assert result["one_sided"] is True
    solved = sorted(p.name for p in (tmp_path / "solves").iterdir())
    # One "plus" solve per knob, plus a single shared baseline solve.
    assert solved == [
        "_baseline",
        "offer_curve_by_group.CC_REGULAR.committed_plus",
        "offer_curve_by_group.CT_PEAKER.peak_plus",
    ]


def test_compute_jacobian_max_knobs_limits_population(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    knobs = [
        kj.Knob(name=f"k{i}", field="battery_dispatch_adder", value=1.0 + i)
        for i in range(5)
    ]
    result = kj.compute_jacobian(
        bundle,
        "ERCOT",
        knobs=knobs,
        max_knobs=2,
        solve_fn=_stub_solve,
        score_fn=_stub_score_factory(),
        out_root=tmp_path / "solves",
    )
    assert result["n_knobs"] == 2
    assert len(result["rows"]) == 2


def test_compute_jacobian_discovers_knobs_when_none_passed(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "run_config.json").write_text(
        json.dumps(
            {"scenario_config": {"offer_curve_by_group": {"CT_PEAKER": {"peak": 1.3}}}}
        )
    )
    result = kj.compute_jacobian(
        bundle,
        "ERCOT",
        solve_fn=_stub_solve,
        score_fn=_stub_score_factory(),
        out_root=tmp_path / "solves",
    )
    assert result["n_knobs"] == 1
    assert result["rows"][0]["knob"] == "offer_curve_by_group.CT_PEAKER.peak"


# ---------------------------------------------------------------------------
# CLI (compute_jacobian itself stubbed — this only checks the argparse/output
# wiring, not the real solve path)
# ---------------------------------------------------------------------------
def test_main_writes_default_output_path(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    canned = {"diagnostic": True, "n_knobs": 1, "rows": [{"knob": "k1"}]}
    monkeypatch.setattr(kj, "compute_jacobian", lambda *a, **kw: canned)
    monkeypatch.setattr("sys.argv", ["knob_jacobian.py", str(bundle), "--iso", "ERCOT"])
    kj.main()
    out = json.loads((bundle / "knob_jacobian.json").read_text())
    assert out == canned


def test_main_writes_to_explicit_out_path(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    out_path = tmp_path / "custom.json"
    canned = {"diagnostic": True, "n_knobs": 0, "rows": []}
    monkeypatch.setattr(kj, "compute_jacobian", lambda *a, **kw: canned)
    monkeypatch.setattr(
        "sys.argv",
        ["knob_jacobian.py", str(bundle), "--iso", "ERCOT", "--out", str(out_path)],
    )
    kj.main()
    assert json.loads(out_path.read_text()) == canned
    assert not (bundle / "knob_jacobian.json").exists()


def test_module_constants_enforce_one_year_diagnostic_scope():
    """D-11 spec: one year (2024) only, +-10% — pin the defaults so a future
    edit can't silently widen the quarantine-adjacent probe scope."""
    assert kj.DEFAULT_YEAR == 2024
    assert math.isclose(kj.PERTURB_FRAC, 0.10)
