"""PJM's EIA-930 per-DIBA ``local_time`` label is the UTC hour-beginning."""

import importlib.util
from pathlib import Path

import pandas as pd


def _script():
    path = (
        Path(__file__).resolve().parents[3] / "scripts/data/derive_pjm_seam_ladders.py"
    )
    spec = importlib.util.spec_from_file_location("_derive_pjm_seam_label", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_utc_0500_label_is_est_midnight() -> None:
    out = _script().pjm_eia930_label_to_est(pd.Series(["2023-01-01 05:00"]))
    assert out.iloc[0] == pd.Timestamp("2023-01-01 00:00")


def test_label_before_0500_utc_jan_1_belongs_to_prior_year() -> None:
    out = _script().pjm_eia930_label_to_est(pd.Series(["2020-01-01 04:00"]))
    assert out.iloc[0] == pd.Timestamp("2019-12-31 23:00")


def test_summer_label_is_fixed_offset_not_dst() -> None:
    out = _script().pjm_eia930_label_to_est(pd.Series(["2023-07-01 12:00"]))
    assert out.iloc[0] == pd.Timestamp("2023-07-01 07:00")


def test_24_utc_labels_map_to_24_distinct_chronological_hours() -> None:
    labels = pd.Series(pd.date_range("2023-03-12 05:00", periods=24, freq="h"))
    out = _script().pjm_eia930_label_to_est(labels)
    assert out.is_monotonic_increasing and out.nunique() == 24
    assert out.iloc[0] == pd.Timestamp("2023-03-12 00:00")
