"""neiso-114 phase 0 (zero LP): per-unit offer census for NEISO coal and ST_GAS vs CC.

Rebuilds each year's fleet with ``run_year(fleet_only=True)`` on the NEISO
keeper's own recipe (``results/calibration/rneiso_span/meta.json``) — the
calibration prep path stops after the fleet/offer arrays, so no LP is built
(rule 32 ``[R-SHARD]`` (a)). ``mc_base`` is the assembled P0 objective the LP
is handed (fuel + VOM + carbon + NOx + tranche multipliers), so the monthly
offer read here is the offer the keeper solved on.

Per year it writes one row per coal / ST_GAS / CC_REGULAR / CC_CHP unit-tranche:
plant, group, coal supply class, pmax, heat rate, min_gen (floor) MW and
mechanism, mean availability, and the 12 monthly mean offers and fuel prices.

Usage::

    uv run python docs/handoffs/neiso114/phase0_offer_census.py --out <dir>
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import set_eia860_vintage  # noqa: E402

BUNDLE = REPO / "results/calibration/rneiso_span"
RENAMES = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_sigmoid_overrides": "bit_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
}
SKIP = {
    "year",
    "iso",
    "hours",
    "gas_price",
    "ttc_overrides",
    "fleet_only",
    "xyear_cache",
    "must_run_mw",
}
KEEP_GROUPS = ("COAL", "ST_GAS", "CC_REGULAR", "CC_CHP")


def build(year: int, overrides: dict | None = None, offer: dict | None = None):
    """Return the fleet_only state for one year on the keeper recipe (+ overrides)."""
    from scripts import run_calibration_full as rcf
    from scripts.run_calibration import run_year

    from market_sim.pipeline.reference import henry_hub_actual

    meta = json.loads((BUNDLE / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    kw = {}
    for k, v in meta.items():
        k2 = RENAMES.get(k, k)
        if k2 in params and k2 not in SKIP:
            kw[k2] = v
    kw["inject_biomass_mustrun"] = True
    if overrides:
        kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), **overrides}
    if offer:
        kw["offer_curve_overrides"] = offer
    gas = henry_hub_actual(rcf._load_reference(), year)
    return run_year(year, "NEISO", 8760, gas, {}, fleet_only=True, **kw)


def month_index(T: int = 8760) -> np.ndarray:
    """Calendar-month index (0..11) per hour of a non-leap 8760 year."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.repeat(np.arange(12), np.array(days) * 24)[:T]


def census(
    year: int, overrides: dict | None = None, offer: dict | None = None
) -> pd.DataFrame:
    """Per unit-tranche offer census for one year."""
    from market_sim.data.coal import coal_supply_class

    st = build(year, overrides, offer)
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], float)
    fp = np.asarray(st["fuel_prices"], float)
    grp = np.asarray(fa.plant_group).astype(str)
    mi = month_index(mc.shape[1])
    rows = []
    avail = np.asarray(fa.availability, float)
    mg = fa.min_gen
    mech = fa.min_gen_mechanism
    for g in range(len(fa.pmax)):
        if not any(grp[g].startswith(k) for k in KEEP_GROUPS):
            continue
        r = {
            "year": year,
            "unit_id": fa.unit_ids[g],
            "plant": int(fa.plant_code[g]),
            "group": grp[g],
            "supply": coal_supply_class(int(fa.plant_code[g]))
            if grp[g].startswith("COAL")
            else "",
            "pmax": float(fa.pmax[g]),
            "hr": float(fa.heat_rate[g]),
            "avail": float(avail[g].mean()) if avail.ndim == 2 else float(avail[g]),
            "min_gen_mw": float(np.asarray(mg[g]).mean()) if mg is not None else 0.0,
            "min_gen_mech": str(mech[g]) if mech is not None else "",
        }
        for m in range(12):
            r[f"mc{m + 1:02d}"] = float(mc[g, mi == m].mean())
            r[f"fp{m + 1:02d}"] = (
                float(fp[g, mi == m].mean()) if fp.ndim == 2 else float(fp[g])
            )
        rows.append(r)
    set_eia860_vintage(None)
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--tag", default="keeper")
    ap.add_argument(
        "--set", action="append", default=[], help="flag=true|false override"
    )
    ap.add_argument(
        "--offer-curve-json", default=None, help="path: replaces offer_curve_overrides"
    )
    args = ap.parse_args()
    ov = {}
    for s in args.set:
        k, v = s.split("=", 1)
        ov[k] = v.lower() == "true"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for y in args.years:
        offer = (
            json.loads(Path(args.offer_curve_json).read_text())
            if args.offer_curve_json
            else None
        )
        df = census(y, ov or None, offer)
        df.to_parquet(out / f"census_{args.tag}_{y}.parquet")
        print(y, len(df), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
