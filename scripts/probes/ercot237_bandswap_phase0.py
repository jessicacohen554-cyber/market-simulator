"""ercot-237: Phase-0 characterization of the keeper's band-structure residual.

ZERO-SOLVE. Reads only committed artifacts — the keeper sidecar
``results/calibration/ercot236_k33_clip/hourly/system_2023.parquet`` and the
committed actuals ``data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet``
— and characterizes WHICH hours/months swap price bands behind the keeper's
reported residual ([500,1000) model 18 vs actual 43; [200,500) model 103 vs
actual 77). No lever, no gate change, no matrix stamp: measurement only, per
``docs/PRECOMMIT-ercot237-bandswap-phase0-2026-08-26.md`` (pushed and
blob-verified before this probe ran).

Constructions are byte-identical to the ercot-236 point scorer
(``scripts/probes/ercot236_h4097_repair.py::_lw`` / ``score_point``):
model = per-hour demand-weighted zonal ``price`` of the P1 pass, NaN -> 0;
actual = the validation parquet's 2023 ``rt`` column; bands
[200,500) / [500,1000) / >=1000, residual band <200.

V-0 identity gate: the recomputed counts must reproduce the keeper's
registered ``model_band_hours_vs_actual`` EXACTLY (model 103/18/59,
actual 77/43/59) or the probe hard-stops with no result written
(precommit section 1 item 1).

Run:
    python scripts/probes/ercot237_bandswap_phase0.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER_BUNDLE = REPO / "results" / "calibration" / "ercot236_k33_clip"
ACTUALS = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
OUT_JSON = REPO / "results" / "calibration" / "ercot237_bandswap_phase0.json"

#: The keeper's registered band counts (ercot236_point_score.json,
#: ``model_band_hours_vs_actual``) — the V-0 identity expectation.
#: ACTUAL ge_1000 corrected 59 -> 61 by PRECOMMIT-ercot237 Amendment 1:
#: the registered 59 was a constant hardcoded in ercot235_offer2023_sweep
#: and never computed from data; 77+43+61 = 181 = actual_tail.json rt_gt.
EXPECT_MODEL = {"200_500": 103, "500_1000": 18, "ge_1000": 59}
EXPECT_ACTUAL = {"200_500": 77, "500_1000": 43, "ge_1000": 61}

#: Band edges (the point scorer's), labels ordered low -> high.
BANDS = ["lt_200", "200_500", "500_1000", "ge_1000"]

#: Non-leap cumulative month-start hours (render_calibration_html._CUM).
_CUM = np.cumsum([0] + [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24


def _band(x: np.ndarray) -> np.ndarray:
    """Band index 0..3 per hour for the point scorer's edges."""
    return np.digitize(x, [200.0, 500.0, 1000.0])


def _series():
    """(model lw price NaN->0, actual rt, max zonal lambda) for 2023, len 8760."""
    df = pd.read_parquet(KEEPER_BUNDLE / "hourly" / "system_2023.parquet")
    df = df[(df["year"] == 2023) & (df["pass"] == "P1")]
    g = df.groupby("hour")
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = g["demand"].sum()
    rng = range(8760)
    m = np.nan_to_num((num / den).reindex(rng).to_numpy(float))
    lam = (
        g["price"].max().reindex(rng).to_numpy(float)
        - g["ordc_adder"].max().reindex(rng).fillna(0.0).to_numpy(float)
    )
    a = pd.read_parquet(ACTUALS)
    a = a[a["year"] == 2023].sort_values("hour")["rt"].to_numpy(float)[:8760]
    return m, a, lam


def _rows(hours: np.ndarray, m: np.ndarray, a: np.ndarray) -> list[dict]:
    """Per-hour detail rows (hour, month, hour-of-day, model $, actual $)."""
    mon = np.searchsorted(_CUM, hours, side="right")
    return [
        {
            "h": int(h),
            "month": int(mo),
            "hod": int(h % 24),
            "model": round(float(m[h]), 2),
            "actual": round(float(a[h]), 2),
        }
        for h, mo in zip(hours, mon)
    ]


def _hist(hours: np.ndarray) -> dict:
    """Month and hour-of-day histograms for an hour set."""
    mon = np.searchsorted(_CUM, hours, side="right")
    hod = hours % 24
    return {
        "by_month": {int(mo): int((mon == mo).sum()) for mo in sorted(set(mon))},
        "by_hod": {int(hh): int((hod == hh).sum()) for hh in sorted(set(hod))},
    }


def main() -> None:
    m, a, lam = _series()
    mb, ab = _band(m), _band(a)

    counts_model = {BANDS[i]: int((mb == i).sum()) for i in range(1, 4)}
    counts_actual = {BANDS[i]: int((ab == i).sum()) for i in range(1, 4)}
    # V-0 identity gate — hard stop on any drift from the registered keeper
    # values (precommit section 1 item 1: no result is written on mismatch).
    assert counts_model == {
        "200_500": EXPECT_MODEL["200_500"],
        "500_1000": EXPECT_MODEL["500_1000"],
        "ge_1000": EXPECT_MODEL["ge_1000"],
    }, f"V-0 FAIL model {counts_model} != {EXPECT_MODEL}"
    assert counts_actual == {
        "200_500": EXPECT_ACTUAL["200_500"],
        "500_1000": EXPECT_ACTUAL["500_1000"],
        "ge_1000": EXPECT_ACTUAL["ge_1000"],
    }, f"V-0 FAIL actual {counts_actual} != {EXPECT_ACTUAL}"

    # 4x4 joint band matrix (model band x actual band), hour lists for every
    # off-diagonal cell touching [200,500) or [500,1000).
    matrix = {}
    cell_hours = {}
    for i, mlab in enumerate(BANDS):
        for j, alab in enumerate(BANDS):
            k = np.where((mb == i) & (ab == j))[0]
            matrix[f"{mlab}|{alab}"] = int(len(k))
            if i != j and len(k) and (i in (1, 2) or j in (1, 2)):
                cell_hours[f"{mlab}|{alab}"] = _rows(k, m, a)

    # Populations (precommit section 1 item 3).
    pop_a = np.where(ab == 2)[0]                       # actual [500,1000): 43 h
    pop_b = np.where((mb == 1) & (a < 200.0))[0]       # model [200,500), actual < 200
    pop_c = np.where((mb == 1) & (a >= 500.0))[0]      # model [200,500), actual >= 500

    # Known-object overlaps (precommit section 1 item 4). Spur uses the
    # G-SPUR banded rule verbatim (ercot236 scorer: actual NaN -> +inf).
    aa = np.nan_to_num(a, nan=1e9)
    spur = np.where((m >= 150) & (m <= 500) & (aa < 150))[0]
    clip_sat = np.where(np.nan_to_num(lam) >= 4999.0)[0]

    res = {
        "session": "ercot-237",
        "keeper": "2026-08-25-236-swcap-clip-k33",
        "precommit": "docs/PRECOMMIT-ercot237-bandswap-phase0-2026-08-26.md",
        "v0_identity": {"model": counts_model, "actual": counts_actual, "pass": True},
        "joint_band_matrix": matrix,
        "populations": {
            "a_actual_500_1000": {
                "n": int(len(pop_a)),
                "model_band_of": {
                    BANDS[i]: int((mb[pop_a] == i).sum()) for i in range(4)
                },
                "hist": _hist(pop_a),
                "rows": _rows(pop_a, m, a),
            },
            "b_model_200_500_actual_lt200": {
                "n": int(len(pop_b)),
                "hist": _hist(pop_b),
                "rows": _rows(pop_b, m, a),
            },
            "c_model_200_500_actual_ge500": {
                "n": int(len(pop_c)),
                "rows": _rows(pop_c, m, a),
            },
        },
        "overlaps": {
            "spur68_hours": int(len(spur)),
            "spur68_in_pop_b": int(len(np.intersect1d(spur, pop_b))),
            "clip_sat_hours": int(len(clip_sat)),
            "clip_sat_in_pop_a": int(len(np.intersect1d(clip_sat, pop_a))),
        },
        "cell_hours": cell_hours,
    }
    OUT_JSON.write_text(json.dumps(res, indent=1))
    headline = {
        k: res[k] for k in ("v0_identity", "joint_band_matrix", "overlaps")
    }
    headline["pop_a_model_band_of"] = res["populations"]["a_actual_500_1000"][
        "model_band_of"
    ]
    headline["pop_sizes"] = {
        p: res["populations"][p]["n"] for p in res["populations"]
    }
    print(json.dumps(headline, indent=1))


if __name__ == "__main__":
    main()
