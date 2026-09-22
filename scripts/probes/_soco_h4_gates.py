"""SOCO hydro-4 (ZERO LP): score gates G1-G3 for one leg against its control.

Reads only committed sidecars — ``hourly/class_hourly_<y>.parquet`` of the leg
and of its control (the keeper bundle for 2023/2024, the ``fix_2025`` leg for
2025, per PRECOMMIT addendum A) — plus the measured EIA-930 ``NG: WAT`` series
and the zero-LP stamped mechanism level from ``build_hydro_fleet``. Gates are
the ones fixed in ``docs/handoffs/PRECOMMIT-soco-hydro-4-2026-09-22.md`` §4.

Usage::

    python3 scripts/probes/_soco_h4_gates.py <leg_bundle> <control_bundle> \\
        --arm mff|ror|fix --year 2023
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data.hydro import build_hydro_fleet, hours_per_month  # noqa: E402

ZONES = ["SOCO_AL", "SOCO_GA", "SOCO_MS"]
#: PRECOMMIT §4 G2 threshold (relative annual hydro TWh move).
G2_TOL = 0.001


def hydro_hourly(bundle: Path, year: int) -> np.ndarray:
    """Hourly P1 conventional-hydro MW (8760) from a bundle's class sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[(df.klass == "hydro") & (df["pass"] == "P1")].sort_values("hour")
    return df.mw.to_numpy(dtype=float)


def month_index(year: int, n: int) -> np.ndarray:
    """Model-clock month index (0-11) for each of ``n`` hours."""
    return np.repeat(np.arange(12), hours_per_month().astype(int))[:n]


def measured(year: int) -> pd.DataFrame:
    """EIA-930 SOCO hourly demand + WAT for ``year`` in model-clock order."""
    df = pd.read_parquet(RAW_DIR / "eia-930-hourly" / "SOCO hourly.parquet")
    t = pd.to_datetime(df["Local time"])
    return df[t.dt.year == year].reset_index(drop=True)


def top_decile_share(gen: np.ndarray, load: np.ndarray, month: np.ndarray) -> float:
    """Share of each month's energy produced in that month's top-10 % load hours."""
    top = tot = 0.0
    ok = np.isfinite(gen) & np.isfinite(load)
    for m in range(12):
        sel = (month == m) & ok
        if not sel.any():
            continue
        thr = np.quantile(load[sel], 0.9)
        top += gen[sel][load[sel] >= thr].sum()
        tot += gen[sel].sum()
    return top / tot


def stamped_level(arm: str, year: int) -> np.ndarray | None:
    """Monthly fleet MW the arm stamps (floor or RoR flat base), zero LP."""
    if arm not in ("mff", "ror"):
        return None
    kw = {"min_flow_floor": arm == "mff", "ror_split": arm == "ror"}
    units, _ = build_hydro_fleet(
        "SOCO", year, ZONES, backfill_year=2024 if year == 2025 else None, **kw
    )
    attr = "hydro_min_flow_monthly_mw" if arm == "mff" else "hydro_ror_flat_monthly_mw"
    lv = np.zeros(12)
    for u in units:
        v = getattr(u, attr, None)
        if v:
            lv += np.asarray(v, dtype=float)
    return lv


def score(leg: Path, ctl: Path, arm: str, year: int) -> dict:
    """Return the G1-G3 numbers for one leg."""
    h, c = hydro_hourly(leg, year), hydro_hourly(ctl, year)
    meas = measured(year)
    n = min(len(h), len(meas))
    mon = month_index(year, n)
    load = meas["Demand"].to_numpy(dtype=float)[:n]
    wat = meas["NG: WAT"].to_numpy(dtype=float)[:n]
    out: dict = {"year": year, "arm": arm}
    out["twh_leg"], out["twh_ctl"] = float(h.sum() / 1e6), float(c.sum() / 1e6)
    out["g2_rel"] = float((h.sum() - c.sum()) / c.sum())
    out["g2_pass"] = bool(abs(out["g2_rel"]) < G2_TOL)
    # EIA-930 SOCO WAT has gaps (2024-11-25..12-31, 1,343 h; 2025-01 121 h):
    # measured statistics are over the reported hours only.
    out["meas_missing_hours"] = int(np.isnan(wat).sum())
    for tag, s in (("leg", h[:n]), ("ctl", c[:n]), ("meas", wat)):
        out[f"zero_{tag}"] = int((s[np.isfinite(s)] < 1.0).sum())
        out[f"p05_{tag}"] = float(np.nanquantile(s, 0.05))
        out[f"p95_{tag}"] = float(np.nanquantile(s, 0.95))
        out[f"topdec_{tag}"] = float(top_decile_share(s, load, mon))
    lv = stamped_level(arm, year)
    if lv is not None:
        hpm = hours_per_month().astype(float)
        mmin = np.array([h[:n][mon == m].min() for m in range(12)])
        out["g1_stamped_mw_avg"] = float((lv * hpm).sum() / hpm.sum())
        out["g1_month_min_minus_level"] = (mmin - lv).round(1).tolist()
        out["g1_pass"] = bool(np.all(mmin >= lv - 1.0))
    return out


def main() -> None:
    """CLI: print the gate dict as JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("leg")
    ap.add_argument("ctl")
    ap.add_argument("--arm", required=True, choices=("mff", "ror", "fix"))
    ap.add_argument("--year", required=True, type=int)
    a = ap.parse_args()
    print(json.dumps(score(Path(a.leg), Path(a.ctl), a.arm, a.year), indent=1))


if __name__ == "__main__":
    main()
