"""hydro-1: read the solved arms against their committed controls (zero LP).

Differences each returned shard bundle against the keeper bundle it was solved
from (rule 29(b) form 4 — the committed keeper IS the control), on the three
statistics the PRECOMMIT's gates are written in:

* **G2, the invariant** — annual hydro TWh must move < 0.1 %. The family
  redistributes WHEN water is turbined and must never move a monthly total.
* **the trough** — hourly p05 / p50 / p95, and the count of hours the fleet
  sits below 1 % of its own annual max (the "0 hydro hours" defect).
* **the concentration** — the share of each month's hydro energy delivered in
  that month's top-decile gross-load hours, averaged over months.

Each is reported ARM vs CONTROL vs the ISO's own published hourly actual, so a
move can be read as toward or away from reality rather than merely as a move.

Run: ``uv run --no-sync python3 scripts/probes/_hydro1_arm_readout.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

from _hydro_phase0_pjm_nyiso import actual_nyiso, actual_pjm  # noqa: E402

from market_sim.data.fleet import _hour_to_month_index  # noqa: E402

# (arm bundle, control bundle, ISO, year)
ARMS = [
    ("hydro1_pjm_ror_2025", "pjm_h13_meritalloc_span", "PJM", 2025),
    ("hydro1_nyiso_ror_2022", "nyiso247_fuelinv_span", "NYISO", 2022),
    ("hydro1_nyiso_ror_2023", "nyiso247_fuelinv_span", "NYISO", 2023),
    ("hydro1_nyiso_ror_2024", "nyiso247_fuelinv_span", "NYISO", 2024),
]


def hydro_mw(bundle: str, year: int) -> np.ndarray | None:
    """Return a bundle's P1 hourly conventional-hydro MW, or ``None``."""
    p = ROOT / "results/calibration" / bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    sub = df[(df["klass"] == "hydro") & (df["pass"] == "P1")].sort_values("hour")
    out = np.zeros(8760, dtype=float)
    out[sub["hour"].to_numpy(dtype=int)] = sub["mw"].to_numpy(dtype=float)
    return out


def load_mw(bundle: str, year: int) -> np.ndarray | None:
    """Return a bundle's P1 ISO-total hourly demand, or ``None``."""
    p = ROOT / "results/calibration" / bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    tot = df.groupby("hour")["demand"].sum().sort_index()
    out = np.zeros(8760, dtype=float)
    out[tot.index.to_numpy(dtype=int)] = tot.to_numpy(dtype=float)
    return out


def top_decile_share(series: np.ndarray, load: np.ndarray) -> float:
    """Mean over months of the share of the month's energy in its top-10 % load hours."""
    mi = _hour_to_month_index(8760)
    out = []
    for m in range(12):
        sel = mi == m
        s, l = series[sel], load[sel]
        if s.sum() <= 0:
            continue
        n = max(1, int(0.10 * len(s)))
        out.append(float(s[np.argsort(l)[-n:]].sum() / s.sum()))
    return float(np.mean(out))


def row(series: np.ndarray, load: np.ndarray) -> dict:
    mx = float(series.max())
    return {
        "twh": round(float(series.sum()) / 1e6, 4),
        "p05": round(float(np.percentile(series, 5)), 1),
        "p50": round(float(np.percentile(series, 50)), 1),
        "p95": round(float(np.percentile(series, 95)), 1),
        "hours_below_1pct_of_own_max": int((series < 0.01 * mx).sum()),
        "top_decile_share": round(top_decile_share(series, load), 4),
    }


def main() -> None:
    out: dict = {}
    for arm_b, ctl_b, iso, year in ARMS:
        arm, ctl = hydro_mw(arm_b, year), hydro_mw(ctl_b, year)
        if arm is None or ctl is None:
            out[f"{iso} {year}"] = {"error": "bundle or control sidecar missing"}
            continue
        load = load_mw(arm_b, year)
        if load is None:
            load = load_mw(ctl_b, year)
        a_hourly = actual_pjm(year) if iso == "PJM" else actual_nyiso(year)
        rec = {
            "arm_bundle": arm_b,
            "control_bundle": ctl_b,
            "arm": row(arm, load),
            "control": row(ctl, load),
        }
        if a_hourly is not None:
            act = np.nan_to_num(a_hourly, nan=0.0)
            rec["actual_published"] = row(act, load)
            if iso == "PJM":
                rec["actual_CAVEAT"] = (
                    "PJM Data Miner 'Hydro' FOLDS pumped storage (5,046 MW of "
                    "PS over five plants; 15.5 TWh vs 8.9 TWh of EIA-923 HY). "
                    "Its LEVEL and its top-decile share are NOT like-for-like "
                    "against a conventional-only model class; only its "
                    "one-sided floor is admissible."
                )
        d_twh = rec["arm"]["twh"] - rec["control"]["twh"]
        rec["G2_invariant"] = {
            "delta_twh": round(d_twh, 5),
            "delta_pct": round(100.0 * d_twh / max(rec["control"]["twh"], 1e-9), 4),
            "passes_0p1pct": abs(d_twh) / max(rec["control"]["twh"], 1e-9) < 0.001,
        }
        rec["moves"] = {
            "p05": round(rec["arm"]["p05"] - rec["control"]["p05"], 1),
            "p95": round(rec["arm"]["p95"] - rec["control"]["p95"], 1),
            "hours_below_1pct": (
                rec["arm"]["hours_below_1pct_of_own_max"]
                - rec["control"]["hours_below_1pct_of_own_max"]
            ),
            "top_decile_share": round(
                rec["arm"]["top_decile_share"] - rec["control"]["top_decile_share"], 4
            ),
        }
        out[f"{iso} {year}"] = rec
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
