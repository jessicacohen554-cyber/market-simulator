"""NYISO-NEXT-26 phase 0 (ZERO LP): which constraint prices Long Island, and when.

Three reads, no LP:

1. **Attribution.** Regress the hourly DA LONGIL-over-N.Y.C. congestion
   (``-(cong_K - cong_J)``, NYISO convention) on the hourly shadow cost of every
   facility in NYISO's DAM limiting-constraint posting that binds >= 40 h in the
   year. The coefficients are implied shift-factor differences; ``coef x mean
   shadow`` attributes the mean spread by facility, grouped as the Zone-K import
   set, LI-internal facilities, or other.
2. **Window census.** For the Zone-K import set (Y50 Dunwoodie-Shore Road, Y49
   Sprain Brook-East Garden City, the ConEd-LIPA interface, the Shore Road
   345/138 transformer): binding hours by season and the share outside HB14-21,
   the window the armed cap (``nyiso_li_lcr_tsl``) applies in.
3. **Static cap estimate.** On the keeper's committed legs: hours the model's
   NYC->Long_Island net flow exceeds the published 940 MW N-1-1 limit, and a
   first-order Zone K price if the excess were met by the next LI unit in the
   keeper's own merit order (no redispatch elsewhere; a bracket, not a forecast).

Inputs: ``fetch_nyiso_zonal_lmp.py --kind dlc`` / ``--kind da`` archives (gitignored,
regenerable); the NEXT-21 keeper legs' ``unit_hourly`` / ``network`` parquet, read
from the shard branches into ``--legs``. Diagnostics only (rule 13).

Usage: uv run python scripts/probes/nyisonext26_li_dlc.py --legs <dir> --out <json>
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nyisonext26_li_gap import (  # noqa: E402
    DAM_DIR,
    REPO,
    SEASONS,
    YEARS,
    da_components,
    keeper_bundle,
    measured_balance,
    model_balance,
    model_prices,
)

AC_SECURITY_SET = {
    "DUNWODIE 345 SHORE_RD 345 1",
    "SPRNBRK  345 EGRDNCTR 345 1",
    "CONED - LIPA",
    "SHORE_RD 345 SHORE_RD 138 1",
}
ZONE_K_IMPORT = AC_SECURITY_SET | {
    "SCH - NPX_1385",
    "SCH - NPX_CSC",
    "SCH - PJM_NEPTUNE",
}
LI_INTERNAL_KEYS = ("NRTHPORT", "PILGRIM", "VALLYSTR", "EGRDNCTY", "ELWOOD", "PULASKLI",
                    "INDIANHD", "DEPOSIT", "HOLTS", "YAPHNK", "BARRETT", "STEWRTAV")  # fmt: skip
TSL_MW = 940.0  # published N-1-1 (data/raw/capacity-deliverability/nyiso/nyiso.csv)
HB14_21 = range(13, 21)  # hour-beginning 0-based index of HB14..HB21


def load_dlc() -> pd.DataFrame:
    """All staged DAM limiting-constraint rows."""
    fr = []
    for f in sorted(DAM_DIR.glob("20????01DAMLimitingConstraints_csv.zip")):
        z = zipfile.ZipFile(f)
        fr += [pd.read_csv(z.open(n)) for n in z.namelist()]
    d = pd.concat(fr)
    d.columns = ["ts", "tz", "fac", "ptid", "cont", "cost"]
    d["ts"] = pd.to_datetime(d.ts)
    d["year"] = d.ts.dt.year
    return d


def _cls(f: str) -> str:
    if f in ZONE_K_IMPORT:
        return "zone_k_import"
    if any(k in f for k in LI_INTERNAL_KEYS):
        return "li_internal"
    return "other"


def attribution(d: pd.DataFrame, year: int) -> dict:
    """OLS of the DA K-over-J congestion on facility shadow costs."""
    c = da_components(year)
    ckj = (-(c["cong"]["LONGIL"] - c["cong"]["N.Y.C."])).to_numpy()
    grid = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    w = d[d.year == year].groupby(["ts", "fac"]).cost.sum().unstack(fill_value=0)
    w = w[~w.index.duplicated()].reindex(grid).fillna(0)
    keep = [f for f in w.columns if (w[f] > 0).sum() >= 40]
    x = w[keep].to_numpy()
    coef, *_ = np.linalg.lstsq(x, ckj, rcond=None)
    pred = x @ coef
    r2 = 1 - ((ckj - pred) ** 2).sum() / ((ckj - ckj.mean()) ** 2).sum()
    contrib = pd.Series((x * coef).mean(0), index=keep)
    cls = pd.Series([_cls(f) for f in keep], index=keep)
    top = contrib.reindex(contrib.abs().sort_values(ascending=False).index[:8])
    return {
        "mean_da_cong_kj": round(float(ckj.mean()), 2),
        "fitted_mean": round(float(pred.mean()), 2),
        "r2": round(float(r2), 3),
        "by_class": {
            k: round(float(v), 2) for k, v in contrib.groupby(cls).sum().items()
        },
        "top": {
            f: {
                "coef": round(float(coef[keep.index(f)]), 3),
                "contrib": round(float(v), 3),
            }
            for f, v in top.items()
        },  # fmt: skip
    }


def window_census(d: pd.DataFrame) -> dict:
    """Binding hours of the Zone-K AC security set by season; share outside HB14-21."""
    x = d[d.fac.isin(AC_SECURITY_SET)].copy()
    x["off"] = ~x.ts.dt.hour.isin(list(HB14_21))
    mo = x.ts.dt.month
    x["season"] = np.select([mo.isin([12, 1, 2]), mo.isin([3, 4, 5]), mo.isin([6, 7, 8])],
                            ["winter", "spring", "summer"], "fall")  # fmt: skip
    out = {}
    for y, g in x.groupby("year"):
        h = g.drop_duplicates("ts")
        out[int(y)] = {
            "binding_hours": int(len(h)),
            "share_hours_outside_hb14_21": round(float(h.off.mean()), 3),
            "share_cost_outside_hb14_21": round(
                float(g.cost[g.off].sum() / g.cost.sum()), 3
            ),
            "hours_by_season": {s: int(n) for s, n in h.season.value_counts().items()},
            "contingency_hours": int((g.cont.str.strip() != "BASE CASE").sum()),
            "base_case_hours": int((g.cont.str.strip() == "BASE CASE").sum()),
        }
    return out


def cap_estimate(year: int, leg: Path) -> dict:
    """Static first-order Zone K price under an all-hours 940 MW net import cap."""
    m = model_balance(year, leg)
    x = measured_balance(year, m["plants"])
    meas_ac = x["load"] - x["campd_gross"] - x["seams"]
    u = pd.read_parquet(leg / f"unit_hourly_{year}.parquet",
                        columns=["zone", "hour", "mw", "cap_mw", "mc", "fuel"])  # fmt: skip
    u = u[(u.zone == "Long_Island") & (u.fuel != "demand_response")]
    pk = model_prices(keeper_bundle(year), year)["Long_Island"]
    a = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_NYISO.parquet"
    )
    dak = (
        a[(a.year == year) & (a.zone == "Long_Island")]
        .sort_values("hour")
        .da.to_numpy()[:8760]
    )
    ex = np.maximum(m["ac_import"] - TSL_MW, 0.0)
    u = u[u.hour.isin(np.nonzero(ex > 0)[0])].copy()
    u["head"] = (u.cap_mw - u.mw).clip(lower=0)
    est, short = pk.copy(), 0
    for h, g in u.groupby("hour"):
        g = g[g["head"] > 0.1].sort_values("mc")
        k = np.searchsorted(g["head"].cumsum().to_numpy(), ex[h])
        if k >= len(g):
            short += 1
            continue
        est[h] = max(pk[h], g.mc.to_numpy()[k])
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    mo, hr = idx.month.to_numpy(), idx.hour.to_numpy()

    def err(p, mk):
        return round(100 * (p[mk].mean() / dak[mk].mean() - 1), 1)

    allm = np.ones(8760, bool)
    return {
        "hours_model_net_import_gt_940": int((ex > 0).sum()),
        "of_which_outside_hb14_21": int(((ex > 0) & ~np.isin(hr, list(HB14_21))).sum()),
        "mean_excess_mw": round(float(ex[ex > 0].mean()), 0) if (ex > 0).any() else 0.0,
        "hours_measured_implied_gt_940": int((meas_ac > TSL_MW).sum()),
        "hours_li_headroom_short": short,
        "K_err_pct_keeper": err(pk, allm),
        "K_err_pct_static_estimate": err(est, allm),
        "season": {
            s: {
                "err_keeper": err(pk, np.isin(mo, ms)),
                "err_est": err(est, np.isin(mo, ms)),
                "meas_implied_p99": round(
                    float(np.percentile(meas_ac[np.isin(mo, ms)], 99)), 0
                ),
                "model_p99": round(
                    float(np.percentile(m["ac_import"][np.isin(mo, ms)], 99)), 0
                ),
            }
            for s, ms in SEASONS.items()
        },  # fmt: skip
    }


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--legs",
        required=True,
        help="dir holding <year>/{unit_hourly,network}_<year>.parquet",
    )
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = load_dlc()
    res = {
        "attribution": {y: attribution(d, y) for y in YEARS},
        "window_census": window_census(d),
        "cap_estimate": {y: cap_estimate(y, Path(a.legs) / str(y)) for y in YEARS},
    }
    Path(a.out).write_text(json.dumps(res, indent=1, default=float))
    for y in YEARS:
        at, ce = res["attribution"][y], res["cap_estimate"][y]
        print(y, at["r2"], at["by_class"], res["window_census"][y]["share_hours_outside_hb14_21"],
              ce["hours_model_net_import_gt_940"], ce["K_err_pct_keeper"], ce["K_err_pct_static_estimate"])  # fmt: skip


if __name__ == "__main__":
    main()
