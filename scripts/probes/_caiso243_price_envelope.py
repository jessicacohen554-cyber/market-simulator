"""caiso-243 — the pre-solve PRICE-LEG envelope for the F923 fallback repair, zero LP.

NO LP, NOTHING ARMED. Reads the per-variant rebuilds cached by
``_caiso243_fallback_footprint.py`` (the ASSEMBLED P0 offers ``mc`` the LP is
handed, not a fuel-only re-derivation) and the keeper's committed 2025 hourly
sidecar (``system_2025.parquet``: zonal price + demand), and registers a
two-sided envelope on the annual load-weighted mean-price move ``ΔC3a`` for
each variant, per year:

  * LOWER limb (most negative): in EVERY live-month hour where the keeper's
    zonal price exceeds the cheapest repriced tranche's NEW offer, the price
    falls all the way to that offer — i.e. the repaired capacity sets the price
    in every hour it could. The keeper's own residual demand, imports and the
    other 11 GW of CC are ignored, so this overstates the fall.
  * UPPER limb (most positive): in every live-month hour, the price rises by
    the largest POSITIVE offer move of any repriced tranche — i.e. a tranche
    whose offer went UP (September: 3.849 -> ~4.19 $/MMBtu) was marginal in
    every hour and passes its full uplift into the price.

Both limbs are loose by construction and declared as such; caiso-241 §8.1
established that the price leg of this family is CONSERVATIVE (the measured
move came in at 9 % of the ceiling) while its volume leg is anti-conservative,
so NO volume falsifier is attached (caiso-242 PRECOMMIT §0.5(1)).

Inert years (2023, 2024: 12/12 hub-overlay coverage, footprint measured at
ZERO rows) carry the envelope [0, 0] — the falsifier there is byte-identity.

Writes ``results/calibration/_caiso243_price_envelope.json``.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso243_price_envelope.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/caiso241_b1_ctpeaker_committed"
CACHE = Path(
    "/tmp/claude-0/-home-user-market-simulator/8996884f-b2f8-5b4c-a42b-d6af63597aea/scratchpad/c243"
)
OUT = REPO / "results/calibration/_caiso243_price_envelope.json"
HOURS = 8760
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH_OF_HOUR = np.concatenate([np.full(d * 24, m + 1) for m, d in enumerate(_DAYS)])[:HOURS]
VARIANTS = ("a", "c", "ac", "b_0.05_3.0")


def _load(year: int, name: str) -> dict:
    z = np.load(CACHE / f"{name}_{year}.npz", allow_pickle=True)
    return {k: z[k] for k in z.files}


def _system(year: int) -> pd.DataFrame:
    df = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    return df[(df["year"] == year) & (df["pass"] == "P1")]


def envelope(year: int, name: str, zone_names: list[str]) -> dict:
    base, var = _load(year, "keeper"), _load(year, name)
    dmc = var["mc"] - base["mc"]
    moved = ~np.isclose(dmc, 0.0, atol=1e-9)
    rows = moved.any(axis=1)
    sys_ = _system(year)
    total_load = float(sys_["demand"].sum())
    if not rows.any():
        return {"rows": 0, "lower": 0.0, "upper": 0.0, "note": "inert — byte-identical offers; falsifier is identity"}
    # per zone-hour: the keeper's price and demand
    live_months = sorted(int(m) for m in np.unique(MONTH_OF_HOUR[moved.any(axis=0)]))
    lower_num = 0.0
    upper_num = 0.0
    detail = {}
    for z_idx, zname in enumerate(zone_names):
        zr = rows & (base["zone_idx"] == z_idx)
        if not zr.any():
            continue
        sz = sys_[sys_["zone"] == zname].sort_values("hour")
        if sz.empty:
            continue
        price = sz["price"].to_numpy()
        load = sz["demand"].to_numpy()
        hours = sz["hour"].to_numpy().astype(int)
        # cheapest NEW offer among this zone's repriced rows, per hour
        new_min = var["mc"][zr].min(axis=0)[hours]
        old_min = base["mc"][zr].min(axis=0)[hours]
        pos_up = np.maximum(dmc[zr], 0.0).max(axis=0)[hours]
        live = np.isin(MONTH_OF_HOUR[hours], live_months)
        fall = np.where(live, np.maximum(0.0, price - new_min), 0.0)
        rise = np.where(live, pos_up, 0.0)
        lower_num += float((fall * load).sum())
        upper_num += float((rise * load).sum())
        detail[zname] = {
            "repriced_rows": int(zr.sum()),
            "repriced_mw": round(float(base["pmax"][zr].sum()), 1),
            "live_hours_price_above_new_offer": int(((price > new_min) & live).sum()),
            "live_hours_price_above_old_offer": int(((price > old_min) & live).sum()),
            "keeper_live_lw_price": round(float(np.average(price[live], weights=load[live])), 2) if live.any() else None,
            "new_min_offer_live_mean": round(float(new_min[live].mean()), 2) if live.any() else None,
            "old_min_offer_live_mean": round(float(old_min[live].mean()), 2) if live.any() else None,
        }
    return {
        "rows": int(rows.sum()),
        "live_months": live_months,
        "lower": round(-lower_num / total_load, 4),
        "upper": round(upper_num / total_load, 4),
        "by_zone": detail,
    }


def main() -> None:
    import sys

    sys.path.insert(0, str(REPO / "src"))
    from market_sim.config.iso_configs import get_iso_config

    zone_names = list(get_iso_config("CAISO").zone_names)
    out = {
        "_provenance": {
            "session": "caiso-243",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "offers": "assembled P0 mc from run_year(fleet_only=True) per variant (fuel + VOM + carbon + NOx + margin reform)",
            "price": "keeper system_<year>.parquet zonal P1 price, load-weighted by zonal demand",
            "note": "two-sided envelope on the annual load-weighted mean price move; lower limb assumes the repaired capacity sets price in every live hour it undercuts, upper limb assumes the largest positive offer move passes fully into every live hour. Volume: NO falsifier (caiso-241 §8.1).",
        },
        "years": {},
    }
    for year in (2023, 2024, 2025):
        out["years"][str(year)] = {}
        for name in VARIANTS:
            if not (CACHE / f"{name}_{year}.npz").exists():
                continue
            out["years"][str(year)][name] = envelope(year, name, zone_names)
            e = out["years"][str(year)][name]
            print(year, name, "rows", e["rows"], "envelope", [e["lower"], e["upper"]])
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
