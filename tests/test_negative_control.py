"""Tests for the D-14 negative-control harness (scripts/negative_control.py).

Trivial cases first per the repo testing pattern. The two pure corruption
functions (:func:`corrupt_gas_price`, :func:`shuffle_outages_within_year`) are
exercised directly on synthetic data; the solve+score orchestration is
exercised with injected stand-ins (``solve_clean_fn``/``solve_corrupt_fn``/
``score_fn``) — no LP solve, no real calibration bundle. A real end-to-end
control against a keeper bundle is a solve-expensive release-cadence task
(module docstring; CLAUDE.md rule 12), not exercised here.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from scripts import negative_control as nc


# ---------------------------------------------------------------------------
# corrupt_gas_price
# ---------------------------------------------------------------------------
def test_corrupt_gas_price_scales_existing_reference_year():
    reference = {"henry_hub_actual": {"2024": 2.00}}
    corrupted = nc.corrupt_gas_price(reference, 2024, factor=1.5)
    assert corrupted["henry_hub_actual"]["2024"] == pytest.approx(3.00)
    # Original dict is untouched (pure function).
    assert reference["henry_hub_actual"]["2024"] == 2.00


def test_corrupt_gas_price_falls_back_to_model_table_when_year_absent():
    corrupted = nc.corrupt_gas_price({}, 2024, factor=2.0)
    import scripts.run_calibration as rc

    expected = rc._HENRY_HUB_FALLBACK[2024] * 2.0
    assert corrupted["henry_hub_actual"]["2024"] == pytest.approx(expected)


def test_corrupt_gas_price_leaves_other_years_untouched():
    reference = {"henry_hub_actual": {"2023": 2.19, "2024": 2.00, "2025": 3.52}}
    corrupted = nc.corrupt_gas_price(reference, 2024, factor=1.5)
    assert corrupted["henry_hub_actual"]["2023"] == 2.19
    assert corrupted["henry_hub_actual"]["2025"] == 3.52
    assert corrupted["henry_hub_actual"]["2024"] == pytest.approx(3.00)


# ---------------------------------------------------------------------------
# shuffle_outages_within_year
# ---------------------------------------------------------------------------
def _outage_df():
    return pd.DataFrame(
        {
            "facility_id": [1, 1, 2, 3, 4],
            "unit_id": ["A", "A", "B", "C", "D"],
            "outage_start": [
                "2024-01-01",
                "2023-06-01",  # different year — must stay untouched
                "2024-03-01",
                "2024-05-01",
                "2024-07-01",
            ],
            "outage_end": [
                "2024-01-10",
                "2023-06-05",
                "2024-03-20",
                "2024-05-15",
                "2024-07-30",
            ],
            "duration_days": [9.0, 4.0, 19.0, 14.0, 29.0],
        }
    )


def test_shuffle_outages_preserves_total_duration_for_the_year():
    df = _outage_df()
    shuffled = nc.shuffle_outages_within_year(df, 2024, seed=1)
    year_mask = pd.to_datetime(df["outage_start"]).dt.year == 2024
    assert shuffled.loc[year_mask, "duration_days"].sum() == pytest.approx(
        df.loc[year_mask, "duration_days"].sum()
    )
    # The multiset of windows for 2024 is exactly preserved.
    orig_windows = sorted(
        df.loc[year_mask, ["outage_start", "outage_end", "duration_days"]]
        .apply(tuple, axis=1)
        .tolist()
    )
    new_windows = sorted(
        shuffled.loc[year_mask, ["outage_start", "outage_end", "duration_days"]]
        .apply(tuple, axis=1)
        .tolist()
    )
    assert orig_windows == new_windows


def test_shuffle_outages_leaves_other_years_byte_identical():
    df = _outage_df()
    shuffled = nc.shuffle_outages_within_year(df, 2024, seed=1)
    other_mask = pd.to_datetime(df["outage_start"]).dt.year != 2024
    pd.testing.assert_frame_equal(
        shuffled.loc[other_mask].reset_index(drop=True),
        df.loc[other_mask].reset_index(drop=True),
    )


def test_shuffle_outages_actually_permutes_unit_assignment():
    df = _outage_df()
    shuffled = nc.shuffle_outages_within_year(df, 2024, seed=7)
    year_mask = pd.to_datetime(df["outage_start"]).dt.year == 2024
    # facility_id/unit_id columns (the identity) are untouched; only the
    # window columns move, so SOME row's window must differ from the
    # original for a non-trivial permutation to have occurred.
    before = df.loc[year_mask, list(nc._WINDOW_COLS)].to_numpy()
    after = shuffled.loc[year_mask, list(nc._WINDOW_COLS)].to_numpy()
    assert not np.array_equal(before, after)
    pd.testing.assert_series_equal(
        shuffled.loc[year_mask, "facility_id"], df.loc[year_mask, "facility_id"]
    )


def test_shuffle_outages_noop_on_fewer_than_two_rows():
    df = _outage_df().iloc[[0]]  # single 2024 row
    shuffled = nc.shuffle_outages_within_year(df, 2024, seed=3)
    pd.testing.assert_frame_equal(shuffled, df)


# ---------------------------------------------------------------------------
# find_suspected_compensator
# ---------------------------------------------------------------------------
def test_find_suspected_compensator_ranks_by_metric(tmp_path):
    jac = {
        "rows": [
            {"knob": "a", "c3b_price_nrmse_per_unit": 0.001},
            {"knob": "b", "c3b_price_nrmse_per_unit": 0.050},
            {"knob": "c", "c3b_price_nrmse_per_unit": None},
            {"knob": "d", "c3b_price_nrmse_per_unit": -0.030},
        ]
    }
    path = tmp_path / "knob_jacobian.json"
    path.write_text(json.dumps(jac))
    top = nc.find_suspected_compensator(path, "c3b_price_nrmse_per_unit", top_n=2)
    assert [r["knob"] for r in top] == ["b", "d"]


def test_find_suspected_compensator_missing_file_returns_empty(tmp_path):
    assert nc.find_suspected_compensator(tmp_path / "nope.json", "x") == []


# ---------------------------------------------------------------------------
# Orchestration (fully stubbed solve/score)
# ---------------------------------------------------------------------------
def _stub_clean(bundle, iso, year, out_dir, reference):
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _stub_corrupt_sensitive(bundle, iso, year, out_dir, reference):
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _stub_score_sensitive(bundle_dir, year, cache=None):
    # The corrupted dir name distinguishes clean vs corrupt.
    worse = "_corrupt" in bundle_dir.name
    return {
        "c2_gas_abs_err_twh": 3.0 if worse else 1.0,
        "c2_coal_abs_err_twh": 0.5,
        "c3b_price_nrmse": 0.10 if worse else 0.09,
    }


def test_run_negative_control_sensitive_case_passes(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    result = nc.run_negative_control(
        bundle,
        "ERCOT",
        "gas_price",
        out_root=tmp_path / "solves",
        solve_clean_fn=_stub_clean,
        solve_corrupt_fn=_stub_corrupt_sensitive,
        score_fn=_stub_score_sensitive,
        reference={},
    )
    assert result["diagnostic"] is True
    assert result["sensitive"] is True
    assert result["verdict"].startswith("PASS")
    assert result["suspected_compensators"] == {}


def _stub_score_insensitive(bundle_dir, year, cache=None):
    # Corrupted run scores IDENTICALLY to clean -> insensitive.
    return {
        "c2_gas_abs_err_twh": 1.0,
        "c2_coal_abs_err_twh": 0.5,
        "c3b_price_nrmse": 0.09,
    }


def test_run_negative_control_insensitive_case_fails_and_reports_compensator(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    jac_path = bundle / "knob_jacobian.json"
    jac_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "knob": "offer_curve_by_group.CT_PEAKER.peak",
                        "c2_gas_twh_per_unit": 12.0,
                        "c2_coal_twh_per_unit": 0.1,
                        "c3b_price_nrmse_per_unit": 0.02,
                    },
                ]
            }
        )
    )
    result = nc.run_negative_control(
        bundle,
        "ERCOT",
        "outage_shuffle",
        out_root=tmp_path / "solves",
        solve_clean_fn=_stub_clean,
        solve_corrupt_fn=_stub_corrupt_sensitive,
        score_fn=_stub_score_insensitive,
        reference={},
    )
    assert result["sensitive"] is False
    assert result["verdict"].startswith("FAIL")
    assert "c2_gas_abs_err_twh" in result["suspected_compensators"]
    assert result["suspected_compensators"]["c2_gas_abs_err_twh"][0]["knob"] == (
        "offer_curve_by_group.CT_PEAKER.peak"
    )


def test_run_negative_control_rejects_unknown_control(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    with pytest.raises(ValueError):
        nc.run_negative_control(
            bundle,
            "ERCOT",
            "bogus_control",
            out_root=tmp_path / "solves",
            solve_clean_fn=_stub_clean,
            score_fn=_stub_score_sensitive,
            reference={},
        )


# ---------------------------------------------------------------------------
# CLI (run_negative_control stubbed — only checks argparse/output wiring)
# ---------------------------------------------------------------------------
def test_main_writes_default_output_and_exit_code_on_fail(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    canned = {
        "diagnostic": True,
        "sensitive": False,
        "verdict": "FAIL: insensitive",
    }
    monkeypatch.setattr(nc, "run_negative_control", lambda *a, **kw: canned)
    monkeypatch.setattr(
        "sys.argv",
        [
            "negative_control.py",
            str(bundle),
            "--iso",
            "ERCOT",
            "--control",
            "gas_price",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        nc.main()
    assert exc.value.code == 1
    out = json.loads((bundle / "negative_control_gas_price.json").read_text())
    assert out == canned


def test_main_exit_zero_on_pass(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    canned = {"diagnostic": True, "sensitive": True, "verdict": "PASS"}
    monkeypatch.setattr(nc, "run_negative_control", lambda *a, **kw: canned)
    monkeypatch.setattr(
        "sys.argv",
        [
            "negative_control.py",
            str(bundle),
            "--iso",
            "NYISO",
            "--control",
            "outage_shuffle",
        ],
    )
    nc.main()  # must not raise / exit nonzero
    assert (
        json.loads((bundle / "negative_control_outage_shuffle.json").read_text())
        == canned
    )
