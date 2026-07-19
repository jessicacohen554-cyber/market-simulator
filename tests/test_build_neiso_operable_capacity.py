"""Tests for the NEISO operable-capacity intake (Morning Report Section 3).

Trivial-case first: one synthetic Morning Report CSV through the parser/builder,
then the availability-series loader math. No network, no LP solve (CLAUDE.md
rule 22 no-LP validation).
"""

from __future__ import annotations

import importlib

import numpy as np
import pandas as pd

import scripts.data.build_neiso_operable_capacity as build_mod

# A minimal Morning Report with the exact row shapes the parser keys on. The
# first fixture (blank planned/forced split) mimics the pre-2025 format; the
# builder must still resolve every headline field.
_REPORT_20240115 = """\
"C","ISO New England Inc. Morning Report"
"C","Filename: morning_report_20240115.csv"
"C","Report for 01/15/2024"
"H","Section 2. Prior Day Peak","Hour Ending","MW"
"D","01/14/2024","18","16282"
"H","Section 3. Operable Capacity Analysis"
"H","Description","MW"
"D","A. Capacity Supply Obligation (CSO)",28664
"D","B. Capacity Additions EcoMax > CSO",1806
"D","C. Generation Outages and Reductions (Planned + Forced)",3326
"D","Generation Planned Outages and Reductions",
"D","Generation Forced Outages and Reductions",
"D","D. Uncommitted Available Generation (Non-fast start)",8509
"D","E. DRR Capacity",208
"D","F. Uncommitted Available DRR",12
"D","G. Capacity Deliveries: Net Purchases = (-) Net Sales = (+)"
"D","Highgate",-225
"D","Net Deliveries",-2634
"D","H. Total Available Capacity (A+B-C-D+E-F-G)",21465
"D","I. Peak Load Forecast For Hour Ending18",17400
"D","J. Total Operating Reserve Requirement",2781
"D","K. Capacity Required = I + J",20181
"D","L. Surplus = (+) Deficiency = (-) (H - K)",1284
"D","M. Replacement Reserve Requirement",180
"D","N. Excess Commitment Surplus = (+) Deficiency = (-) (L - M)",1104
"D","Section 4. Largest First Contingency MW",1674
"D","Section 5. Annual Maintenance Schedule (A.M.S) Peak Load Exposure MW",20269
"""


def _write_fixture(daily_dir):
    daily_dir.mkdir(parents=True, exist_ok=True)
    (daily_dir / "morning_report_20240115.csv").write_text(_REPORT_20240115)


def test_build_parses_headline_fields_and_identity(tmp_path):
    daily = tmp_path / "daily"
    _write_fixture(daily)
    written = build_mod.build(daily_dir=daily, out_dir=tmp_path)

    # One 2024 row -> one per-year file neiso_operable_capacity_2024.csv.
    assert [p.name for p in written] == ["neiso_operable_capacity_2024.csv"]
    df = pd.read_csv(written[0])
    assert len(df) == 1
    row = df.iloc[0]
    assert pd.Timestamp(row["report_date"]) == pd.Timestamp("2024-01-15")
    assert row["cso_mw"] == 28664
    assert row["capacity_additions_ecomax_gt_cso_mw"] == 1806
    assert row["gen_outages_reductions_mw"] == 3326
    assert row["total_available_capacity_mw"] == 21465
    assert row["net_capacity_deliveries_mw"] == -2634
    assert row["prior_day_peak_mw"] == 16282
    assert row["prior_day_peak_hour_ending"] == 18
    assert row["largest_first_contingency_mw"] == 1674
    # Blank planned/forced split (pre-2025 format) parses to NaN, not 0.
    assert pd.isna(row["gen_planned_outages_mw"])
    # Published accounting identity reconciles exactly.
    identity = (
        row["cso_mw"]
        + row["capacity_additions_ecomax_gt_cso_mw"]
        - row["gen_outages_reductions_mw"]
        - row["uncommitted_available_gen_nonfast_mw"]
        + row["drr_capacity_mw"]
        - row["uncommitted_available_drr_mw"]
        - row["net_capacity_deliveries_mw"]
    )
    assert abs(identity - row["total_available_capacity_mw"]) < 1e-6


def test_availability_series_fraction_and_hour_block(tmp_path, monkeypatch):
    daily = tmp_path / "daily"
    _write_fixture(daily)
    build_mod.build(daily_dir=daily, out_dir=tmp_path)

    # Point the loader at the fixture per-year CSV dir and clear its caches.
    noc = importlib.import_module("market_sim.data.neiso_operable_capacity")
    monkeypatch.setattr(noc, "NEISO_OPERABLE_CAPACITY_DIR", tmp_path)
    noc.load_operable_capacity_frame.cache_clear()
    noc.neiso_thermal_availability_series.cache_clear()

    series = noc.neiso_thermal_availability_series(2024)
    # frac = 1 - C/(A+B) = 1 - 3326/(28664+1806)
    expected = 1.0 - 3326.0 / (28664.0 + 1806.0)
    # Jan-15 (non-leap clock) -> hours [14*24, 15*24); flat block of `expected`.
    lo = 14 * 24
    assert np.isclose(series[lo], expected)
    assert np.isclose(series[lo + 23], expected)
    # Everything outside the covered day is NaN (caller keeps its own model).
    assert np.isnan(series[0])
    assert np.isnan(series[lo + 24])
    # Only the 24 covered hours are finite.
    assert int(np.isfinite(series).sum()) == 24
