#!/usr/bin/env python3
"""miso-283 phase 0 (ZERO LP): which offer sets the keeper's MISO-South / Illinois price, by hour of day.

Fleet-only rebuild of the designated keeper's recipe (``results/calibration/
miso280_span``) for one year, joined to the keeper's committed P1 zone prices.
Per zone and hour, the MARGINAL-CANDIDATE class is the class of the unit whose
assembled P0 offer (``mc_base``) sits closest to the zone price, counted only
when within ``TOL`` $/MWh (offer-matching; the bundle carries no per-unit
dispatch). Also reports the South gas units' delivered fuel price against the
Henry Hub daily print (the Gulf traded hub) by month.

Output: ``<out-dir>/marginal_<Y>.json``.  Rule 13: nothing here feeds a solve.

Usage::

    uv run python scripts/probes/_miso283_marginal_census.py --year 2023 --out-dir X
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402

KEEPER = REPO / "results/calibration/miso280_span"
TOL = 0.5  # $/MWh offer-match tolerance (probe resolution, not a model value)
ZONES = ("MISO-South", "MISO-Illinois")


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    y = args.year
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    hh = _henry_hub_actual(_load_reference(), y)
    st = run_year(y, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(y, {}))
    fa, isoc = st["fleet_arrays"], st["iso_config"]
    n = len(fa.pmax)
    pmax = np.asarray(fa.pmax, dtype=float)
    mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
    if mc.shape[1] == 1:
        mc = np.repeat(mc, 8760, axis=1)
    zone_names = list(isoc.zone_names)
    zone = np.array([zone_names[i] for i in np.asarray(fa.zone_idx).astype(int)])
    groups = np.asarray(list(fa.plant_group))
    sysd = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
    sysd = (
        sysd[sysd["pass"] == "P1"]
        .pivot(index="hour", columns="zone", values="price")
        .sort_index()
    )
    hod = np.arange(8760) % 24
    res: dict = {"year": y, "tol": TOL}
    for z in ZONES:
        m = (zone == z) & (pmax > 0)
        p = sysd[z].to_numpy()
        gap = np.abs(mc[m] - p[None, :])
        best = gap.argmin(axis=0)
        hit = gap[best, np.arange(8760)] <= TOL
        cls = np.where(hit, groups[m][best], "none")
        df = pd.DataFrame({"hod": hod, "cls": cls, "p": p})
        night = df[df.hod < 6]
        # Decompose the matched night offer: heat rate x delivered fuel vs everything else.
        fpa = np.asarray(st.get("fuel_prices"), dtype=float)
        hr = np.asarray(fa.heat_rate, dtype=float)[m]
        gi = np.where(m)[0][best]
        t = np.arange(8760)
        fuel_h = fpa[gi, t] if fpa.ndim == 2 else fpa[gi]
        dec_df = pd.DataFrame(
            {
                "hod": hod,
                "cls": cls,
                "p": p,
                "hr": hr[best],
                "fuel": fuel_h,
                "fuelcost": hr[best] * fuel_h,
                "other": mc[m][best, t] - hr[best] * fuel_h,
            }
        )
        uid = np.asarray(list(fa.unit_ids))[m][best]
        dec_df["uid"] = uid
        dec_df["vom"] = np.asarray(fa.vom, dtype=float)[m][best]
        nd = dec_df[(dec_df.hod < 6) & (dec_df.cls != "none")]
        res[f"{z}_night_top_units"] = (
            nd.groupby(["cls", "uid"])
            .agg(
                n=("p", "size"),
                p=("p", "mean"),
                hr=("hr", "mean"),
                fuel=("fuel", "mean"),
                vom=("vom", "mean"),
                other=("other", "mean"),
            )
            .sort_values("n", ascending=False)
            .head(15)
            .round(2)
            .reset_index()
            .to_dict("records")
        )
        res[f"{z}_night_offer_decomp"] = (
            nd.groupby("cls")[["p", "hr", "fuel", "fuelcost", "other"]]
            .mean()
            .round(2)
            .to_dict("index")
        )
        res[z] = {
            "night_share": night.cls.value_counts(normalize=True).round(3).to_dict(),
            "all_share": df.cls.value_counts(normalize=True).round(3).to_dict(),
            "night_price_by_cls": night.groupby("cls").p.mean().round(2).to_dict(),
        }
    # South gas delivered fuel vs Henry Hub daily.
    fp = np.asarray(st.get("fuel_prices"), dtype=float)

    gas = (
        (zone == "MISO-South")
        & np.isin(groups, ["CC_REGULAR", "CC_CHP", "ST_GAS", "CT_PEAKER", "ST_CHP"])
        & (pmax > 0)
    )
    if fp.ndim == 2 and fp.shape[0] == n:
        w = pmax[gas]
        g_h = (fp[gas] * w[:, None]).sum(axis=0) / w.sum()
        ts = pd.date_range(f"{y}-01-01", periods=8760, freq="h")
        hhd = (
            pd.read_csv(
                REPO / "data/raw/gas-prices/henry_hub_daily.csv", parse_dates=["date"]
            )
            .set_index("date")
            .price_usd_mmbtu
        )
        hh_h = hhd.reindex(pd.date_range(f"{y}-01-01", f"{y}-12-31")).ffill().bfill()
        hh_h = hh_h.reindex(ts.normalize()).to_numpy()
        mo = pd.DataFrame({"m": ts.month, "model": g_h, "hh": hh_h}).groupby("m").mean()
        res["south_gas_vs_hh_monthly"] = mo.round(3).to_dict("list")
        res["south_gas_vs_hh_annual"] = {
            "model": round(float(g_h.mean()), 3),
            "hh": round(float(np.nanmean(hh_h)), 3),
        }

    (out / f"marginal_{y}.json").write_text(json.dumps(res, indent=1, default=str))
    print(
        json.dumps(
            {k: v for k, v in res.items() if k != "south_gas_vs_hh_monthly"},
            indent=1,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
