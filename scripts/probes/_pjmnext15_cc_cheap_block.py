"""PJM-NEXT-15 card 1 (zero LP): PJM's price-taking CC offer block, by year, and what it is.

Reads the DataMiner2 ``energy_market_offers`` corpus (``data/raw/pjm-energy-offers``) for
one year, segments units exactly as ``derive_pjm_offer_midcurve.py`` does (``_unit_physics``
on that year's files, then ``_segments``), and for every CC_LIKE unit-hour walks the step
offer curve: segment k covers MW ``(mw_{k-1}, mw_k]`` at price ``bid_k`` (the derive's own
"first breakpoint at or above the share" convention).

Per offered MW-hour it records
* the within-unit share band of the segment's upper edge (``mw_k / mw_max``);
* whether the segment's upper edge sits AT OR BELOW the unit's ``avg_ecomin`` (+0.5 %),
  i.e. the min-load block a committed unit must run whatever the LMP;
* its price against 6.5 x PRODUCTION gas (IMM Platts monthly, ``som-competitive-conduct``)
  and 6.5 x the model's DELIVERED-gas day series (HH + PJM basis, ``_pjm_fuel_daily``),
  plus <= $0.

And per unit (median over its hours): ``min_runtime``, ecomin/ecomax, ``no_load_cost``
($/h) divided by ecomin MW ($/MWh), and the share of its ecomax offered below
3.5 x delivered gas; units are split into CHEAP (that share >= 25 %) vs the rest so the
block's physics and three-part cost can be compared.

Writes ``results/phase0/pjm/_pjmnext15_cc_cheap_block.json`` (merged per year).
Run: ``python3 scripts/probes/_pjmnext15_cc_cheap_block.py <year> [...]``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
from scripts.data.derive_pjm_offer_midcurve import (  # noqa: E402
    _month_files,
    _segments,
    _unit_physics,
)
from scripts.data.derive_pjm_offer_surface import (  # noqa: E402
    _BID_COLS,
    _MW_COLS,
    _pjm_fuel_daily,
)

OUT = REPO / "results/phase0/pjm/_pjmnext15_cc_cheap_block.json"
SOM = REPO / "data/raw/som-competitive-conduct/som_competitive_conduct.csv"
BANDS = (0.0, 0.25, 0.45, 0.65, 0.85, 1.0001)
BAND_NAMES = ("0-25", "25-45", "45-65", "65-85", "85-100")
LOW_MULT = 6.5  # the NEXT-12/13/14 low-end definition (x gas)
CHEAP_MULT = 3.5  # NEXT-14 card 3's p25 level (x delivered gas)
CHEAP_UNIT_SHARE = 0.25


def _prod_gas_monthly(y: int) -> pd.Series:
    """IMM monthly production-area Platts spot, indexed by month."""
    d = pd.read_csv(SOM)
    d = d[
        (d.iso == "PJM")
        & (d.year == y)
        & (d.metric == "spot_price_digitized_usd_per_mmbtu")
        & (d.fleet_segment == "production_gas")
        & d.period.str.startswith("month_")
    ]
    return d.assign(mo=d.period.str[-2:].astype(int)).set_index("mo")["value"]


def run_year(y: int) -> dict:
    """Walk every CC_LIKE offer curve of year ``y``."""
    files, _ = _month_files([y])
    per_unit = _unit_physics(files)
    cc_units = set(_segments(per_unit)["CC_LIKE"])
    fuel = _pjm_fuel_daily()
    prod = _prod_gas_monthly(y)
    # accumulators: [band, below_ecomin(0/1)] -> MW-h by test
    keys = ("all", "lt_prod", "lt_deliv", "le0", "lt_cheap")
    acc = {k: np.zeros((len(BAND_NAMES), 2)) for k in keys}
    unit_rows = []
    for p in files:
        df = pd.read_parquet(
            p,
            columns=[
                "bid_datetime_beginning_ept",
                "unit_code",
                "avg_ecomin",
                "avg_ecomax",
                "min_runtime",
                "no_load_cost",
                "cold_start_cost",
            ]
            + _BID_COLS
            + _MW_COLS,
        )
        df = df[(df["avg_ecomax"] > 0.0) & df["unit_code"].astype(str).isin(cc_units)]
        if df.empty:
            continue
        ts = pd.to_datetime(
            df["bid_datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        dg = fuel.reindex(pd.DatetimeIndex(ts.dt.normalize())).to_numpy(float)
        pg = prod.reindex(ts.dt.month.to_numpy()).to_numpy(float)
        mws = df[_MW_COLS].to_numpy(float)
        bids = df[_BID_COLS].to_numpy(float)
        mw_max = np.nanmax(mws, axis=1)
        ok = np.isfinite(dg) & (dg > 0) & np.isfinite(pg) & (mw_max > 0)
        mws, bids, mw_max = mws[ok], bids[ok], mw_max[ok]
        dg, pg = dg[ok], pg[ok]
        emin = df["avg_ecomin"].to_numpy(float)[ok]
        prev = np.concatenate([np.zeros((len(mws), 1)), mws[:, :-1]], axis=1)
        seg = np.where(np.isfinite(mws), mws - np.nan_to_num(prev), 0.0)
        seg = np.clip(seg, 0.0, None)
        valid = np.isfinite(mws) & np.isfinite(bids) & (seg > 0)
        share = mws / mw_max[:, None]
        band = np.clip(np.searchsorted(BANDS, share, side="right") - 1, 0, 4)
        below = (mws <= emin[:, None] * 1.005).astype(int)
        tests = {
            "all": np.ones_like(bids, dtype=bool),
            "lt_prod": bids < LOW_MULT * pg[:, None],
            "lt_deliv": bids < LOW_MULT * dg[:, None],
            "le0": bids <= 0.0,
            "lt_cheap": bids < CHEAP_MULT * dg[:, None],
        }
        for k, m in tests.items():
            w = np.where(valid & m, seg, 0.0)
            np.add.at(acc[k], (band.ravel(), below.ravel()), w.ravel())
        cheap_mw = np.where(valid & tests["lt_cheap"], seg, 0.0).sum(axis=1)
        unit_rows.append(
            pd.DataFrame(
                {
                    "unit": df["unit_code"].astype(str).to_numpy()[ok],
                    "cheap_share": cheap_mw / mw_max,
                    "ecomin_ratio": emin / mw_max,
                    "mr": df["min_runtime"].to_numpy(float)[ok],
                    "nl_per_mwh": df["no_load_cost"].to_numpy(float)[ok]
                    / np.where(emin > 0, emin, np.nan),
                    "nl_per_mwh_x_gas": df["no_load_cost"].to_numpy(float)[ok]
                    / np.where(emin > 0, emin, np.nan)
                    / dg,
                    "cold_per_mw": df["cold_start_cost"].to_numpy(float)[ok] / mw_max,
                    "ecomax": mw_max,
                    "first_bid_x_gas": bids[:, 0] / dg,
                }
            )
        )
        print(f"  {p.name}", flush=True)
    u = pd.concat(unit_rows).groupby("unit").median()
    u["cheap"] = u["cheap_share"] >= CHEAP_UNIT_SHARE

    def usum(d: pd.DataFrame) -> dict:
        w = d["ecomax"]
        return {
            "n": int(len(d)),
            "ecomax_gw": round(float(w.sum()) / 1e3, 2),
            "cheap_share_capw": round(
                float(np.average(d["cheap_share"], weights=w)), 3
            ),
            "ecomin_ratio_capw": round(
                float(np.average(d["ecomin_ratio"], weights=w)), 3
            ),
            "min_runtime_med": round(float(d["mr"].median()), 1),
            "no_load_per_ecomin_mwh_med": round(float(d["nl_per_mwh"].median()), 2),
            "no_load_per_ecomin_x_gas_med": round(
                float(d["nl_per_mwh_x_gas"].median()), 2
            ),
            "cold_start_per_mw_med": round(float(d["cold_per_mw"].median()), 1),
            "first_bid_x_gas_med": round(float(d["first_bid_x_gas"].median()), 2),
        }

    tot = acc["all"]
    rec = {
        "n_cc_like_units": len(cc_units),
        "offered_twh": round(float(tot.sum()) / 1e6, 1),
        "share_below_ecomin_of_offered": round(float(tot[:, 1].sum() / tot.sum()), 3),
        "by_band": {},
        "units_cheap": usum(u[u["cheap"]]),
        "units_rest": usum(u[~u["cheap"]]),
    }
    for k in ("lt_prod", "lt_deliv", "le0", "lt_cheap"):
        a = acc[k]
        rec[f"{k}_share_of_offered"] = round(float(a.sum() / tot.sum()), 3)
        rec[f"{k}_below_ecomin_fraction"] = round(
            float(a[:, 1].sum() / max(a.sum(), 1e-9)), 3
        )
        rec[f"{k}_mid_25_65_share"] = round(
            float(a[1:3].sum() / max(tot[1:3].sum(), 1e-9)), 3
        )
        rec[f"{k}_mid_25_65_above_ecomin_share"] = round(
            float(a[1:3, 0].sum() / max(tot[1:3, 0].sum(), 1e-9)), 3
        )
    for i, b in enumerate(BAND_NAMES):
        rec["by_band"][b] = {
            "offered_twh": round(float(tot[i].sum()) / 1e6, 2),
            "below_ecomin_frac": round(float(tot[i, 1] / max(tot[i].sum(), 1e-9)), 3),
            **{
                k: round(float(acc[k][i].sum() / max(tot[i].sum(), 1e-9)), 3)
                for k in ("lt_prod", "lt_deliv", "le0", "lt_cheap")
            },
        }
    return rec


def main() -> None:
    """Run each requested year and merge into the JSON artifact."""
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for y in [int(a) for a in sys.argv[1:]]:
        rec = run_year(y)
        out[str(y)] = rec
        OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
        print(y, json.dumps(rec, indent=1), flush=True)


if __name__ == "__main__":
    main()
