"""Validate the hour-of-day frame of the CAISO seam's measured flow sources.

Guard for the 2026-07-07 seam-clock forensics
(``results/calibration/FINDING-caiso-seam-tz-correction-2026-07-07.md``). Two
distinct clock defects were found and are pinned here:

1. The 07-07 seam FINDING's "measured actual" hod table was bucketed on the
   **UTC** hour of the EIA-930 ``period`` timestamp (an 8-hour phase error that
   inverted the model-vs-actual attribution).
2. The CISO per-DIBA interchange parquet's ``local_time`` stamps lag the
   model's hourly frame (the ``<BA> hourly`` extract row clock, verified
   wall-true by solar astronomy and the 2024-04-08 eclipse dip) by **1 h in
   standard time and 2 h in daylight time** — consistent with prevailing-local
   hour-ending stamps whose DST offset was applied twice at fetch time.
   ``eia_loader._caiso_interchange_model_clock`` corrects this at the read
   seam for the corridor deliverability envelope.

This script re-measures the per-regime lag from the source files and FAILS
when it no longer equals the correction constants baked into ``eia_loader``
(``_CAISO_INTERCHANGE_LAG_STD_H`` / ``_CAISO_INTERCHANGE_LAG_DST_H``) — so a
future re-fetch of the parquet with honest stamps cannot be silently
double-shifted, and a regression back to uncorrected consumption cannot hide.
It also checks the duck-mirror orientation of the corrected profile. Reads
only measured inputs (rule 23 — no model output, no residual).

Run:  python scripts/validate_caiso_seam_hod_frame.py
Exit: 0 on pass; 1 with a diagnostic table on any failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402
from market_sim.data import eia_loader  # noqa: E402

INTERCHANGE_PARQUET = (
    paths.RAW_DATA_DIR / "eia-930-interchange" / "CISO interchange hourly.parquet"
)
EXTRACT_PARQUET = paths.RAW_DATA_DIR / "eia-930-hourly" / "CISO hourly.parquet"

# Calibration years only — 2022 / H1-2026 are holdout periods (rule 22).
YEARS = (2023, 2024, 2025)

# The lag scan must prefer the pinned constants by at least this correlation
# margin over every other lag in ±4 h (measured 2026-07-07: PST −1 beats the
# runner-up 0.972 vs 0.930; PDT −2 beats it 0.961 vs 0.919).
MIN_LAG_MARGIN = 0.01


def _model_clock_ti() -> pd.Series:
    """CISO net import on the model clock, from the extract's own TI column."""
    e = pd.read_parquet(EXTRACT_PARQUET)
    out = []
    for yr in YEARS:
        ey = e[e["Local date"].dt.year == yr].sort_values("UTC time")
        ey = ey[~((ey["Local date"].dt.month == 2) & (ey["Local date"].dt.day == 29))]
        base = pd.Timestamp(f"{yr}-01-01 00:00")
        idx = base + pd.to_timedelta(np.arange(len(ey)), unit="h")
        out.append(
            pd.Series(
                -pd.to_numeric(ey["Total interchange"], errors="coerce").to_numpy(),
                index=idx,
            )
        )
    return pd.concat(out)


def _diba_ti() -> pd.Series:
    """CISO net import summed over DIBAs, on the parquet's raw stamps."""
    ic = pd.read_parquet(INTERCHANGE_PARQUET)
    return ic.groupby("local_time", observed=True)["mw"].sum().mul(-1).sort_index()


def check_lag_constants() -> list[str]:
    """Re-measure the per-regime lag and compare to the eia_loader constants."""
    errors: list[str] = []
    model_ti = _model_clock_ti()
    diba = _diba_ti()
    lt = pd.DatetimeIndex(diba.index)
    pac = lt.tz_localize("US/Pacific", ambiguous=False, nonexistent="shift_forward")
    is_dst = (pac.tz_convert("UTC").tz_localize(None) - lt) == pd.Timedelta(hours=7)
    pinned = {
        "PST": eia_loader._CAISO_INTERCHANGE_LAG_STD_H,
        "PDT": eia_loader._CAISO_INTERCHANGE_LAG_DST_H,
    }
    for regime, mask in [("PST", ~is_dst), ("PDT", is_dst)]:
        sub = diba[np.asarray(mask)]
        corr_by_lag: dict[int, float] = {}
        for lag in range(-4, 5):
            s2 = sub.copy()
            s2.index = s2.index + pd.Timedelta(hours=lag)
            j = pd.concat([s2, model_ti], axis=1, join="inner").dropna()
            if len(j) > 800:
                corr_by_lag[lag] = float(j.iloc[:, 0].corr(j.iloc[:, 1]))
        if not corr_by_lag:
            errors.append(f"lag[{regime}]: no overlapping hours")
            continue
        best_lag = max(corr_by_lag, key=corr_by_lag.get)
        expected = -pinned[regime]
        if best_lag != expected:
            errors.append(
                f"lag[{regime}]: measured best lag {best_lag:+d} h (corr "
                f"{corr_by_lag[best_lag]:.4f}) != pinned correction "
                f"{expected:+d} h — the parquet's stamps changed; update or "
                "remove eia_loader._CAISO_INTERCHANGE_LAG_*_H"
            )
            continue
        runner_up = max(v for k, v in corr_by_lag.items() if k != best_lag)
        if corr_by_lag[best_lag] - runner_up < MIN_LAG_MARGIN:
            errors.append(
                f"lag[{regime}]: best lag {best_lag:+d} (corr "
                f"{corr_by_lag[best_lag]:.4f}) does not beat the runner-up "
                f"({runner_up:.4f}) by ≥{MIN_LAG_MARGIN} — frame ambiguous"
            )
    return errors


def check_duck_orientation() -> list[str]:
    """Corrected-frame profile must trough in the belly, peak overnight/evening."""
    errors: list[str] = []
    diba = _diba_ti()
    corrected = eia_loader._caiso_interchange_model_clock(pd.DatetimeIndex(diba.index))
    frame = pd.DataFrame(
        {
            "net_import": diba.to_numpy(),
            "year": corrected.year,
            "hod": corrected.hour,
        }
    )
    frame = frame[frame["year"].isin(YEARS)]
    for year, sub in frame.groupby("year"):
        if len(sub) < 8000:
            continue
        hod_mean = sub.groupby("hod")["net_import"].mean()
        overnight = float(hod_mean.loc[0:6].mean())
        belly = float(hod_mean.loc[10:16].mean())
        evening = float(hod_mean.loc[19:21].mean())
        if not (overnight > belly and evening > belly):
            errors.append(
                f"orientation {year}: overnight {overnight:.0f} / belly "
                f"{belly:.0f} / evening {evening:.0f} MW — the corrected "
                "frame must trough in the belly (duck-mirror)"
            )
    return errors


def main() -> int:
    """Run the lag-constant and orientation checks; print the corrected table."""
    errors = check_lag_constants() + check_duck_orientation()
    diba = _diba_ti()
    corrected = eia_loader._caiso_interchange_model_clock(pd.DatetimeIndex(diba.index))
    frame = pd.DataFrame(
        {
            "net_import": diba.to_numpy(),
            "year": corrected.year,
            "hod": corrected.hour,
        }
    )
    frame = frame[frame["year"].isin(YEARS)]
    table = frame.groupby(["year", "hod"])["net_import"].mean().unstack("year").round(0)
    print("CISO net import on the MODEL clock, hod means (MW):")
    print(table.loc[[0, 3, 6, 9, 12, 15, 18, 19, 20, 21]].to_string())
    if errors:
        print("\nFAIL:")
        for e in errors:
            print(" -", e)
        return 1
    print(
        "\nPASS: per-DIBA lag matches the pinned correction "
        f"(std −{eia_loader._CAISO_INTERCHANGE_LAG_STD_H} h / "
        f"dst −{eia_loader._CAISO_INTERCHANGE_LAG_DST_H} h); "
        "corrected profile is duck-oriented."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
