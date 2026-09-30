"""soco-95 zero-LP C3b 2022 diagnosis: why does SOCO's monthly price shape fail in 2022
(NRMSE 0.275 vs <= 0.20) while the six other years pass?

Rule 32 ``[R-SHARD]`` (a): this never solves. It reads the keeper's committed hourly
sidecars (``results/calibration/soco93_span``), the bench's ``rt_lw_mon`` (the scorer's
own C3b actual) and Southern's FERC-714 lambda on the bench's dense CST 8760, and reuses
the soco-94 ``fleet_only`` rebuild + setter rule (``_soco94_year_pattern``) for the
setter attribution and the measured plant-month fuel counterfactual.

Per year it reports:

1. C3b reproduced from the sidecars with the scorer's ``_nrmse``, and its split into
   LEVEL (annual bias^2) and SHAPE (variance of the monthly error) shares of the MSE,
   plus the shape-only NRMSE (model rescaled to the actual annual mean);
2. each month's share of the squared error;
3. for every month, the load-weighted gap ``P - lambda`` split by lambda band
   (year quantiles low-40 % / mid / top-20 %) and by setter class;
4. counterfactual NRMSEs (first order, no re-stack, model side only):
   - ``elliott_at_lambda``: model price set to lambda in Dec 23-26 (Winter Storm Elliott);
   - ``dec_dropped``: the 11-month NRMSE;
   - ``top20_at_lambda``: model price set to lambda in the year's top-20 % lambda hours
     (the ledgered C3a peak premium, removed as an upper bound on its C3b reach);
   - ``setter_fuel_f923``: each setter-matched hour re-priced at the delivered fuel price
     its own plant paid that month (EIA-923 Sch. 2) - the only measured year-regenerable
     fuel input not already in the model at plant-month grain.

The model-side hourly weight is the model's demand (as in soco-94); the bench monthly is
the scorer's ``rt_lw_mon`` unchanged, so every counterfactual is scored exactly as C3b is.

Usage::

    uv run python scripts/probes/_soco95_c3b_2022.py --out DIR [--years ...]
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src"), str(ROOT)]

from calibration_verdict import _nrmse  # noqa: E402
from probes import _soco94_year_pattern as p94  # noqa: E402

SPAN = p94.SPAN
T = p94.T
MONTH = p94.MONTH
YEARS = p94.YEARS
BENCH = ROOT / "frontend/data/backcast/bench/SOCO"
# Winter Storm Elliott: Dec 23-26 on the dense 8760 (day-of-year 357-360, 0-based 356-359).
ELLIOTT = np.zeros(T, bool)
ELLIOTT[356 * 24 : 360 * 24] = True


def bench_mon(year: int) -> list[float]:
    """The scorer's own C3b actual: the bench ``avgLMP.rt_lw_mon`` vector."""
    with gzip.open(BENCH / f"{year}.json.gz", "rt") as fh:
        return json.load(fh)["bench"]["avgLMP"]["rt_lw_mon"]


def monthly(P: np.ndarray, D: np.ndarray) -> list[float]:
    """Demand-weighted monthly mean of an hourly price."""
    return [float(np.average(P[MONTH == m], weights=D[MONTH == m])) for m in range(12)]


def split(model: list[float], actual: list[float]) -> dict:
    """NRMSE and its level/shape decomposition (MSE = bias^2 + var(err))."""
    m, a = np.array(model), np.array(actual)
    e = m - a
    mse = float((e**2).mean())
    bias = float(e.mean())
    scaled = m * a.mean() / m.mean()
    return dict(
        nrmse=round(_nrmse(list(m), list(a)), 4),
        level_share=round(bias**2 / mse, 3),
        shape_share=round(float(e.var()) / mse, 3),
        bias=round(bias, 2),
        shape_only_nrmse=round(_nrmse(list(scaled), list(a)), 4),
        corr=round(float(np.corrcoef(m, a)[0, 1]), 3),
        month_sq_share=[round(float(x), 3) for x in e**2 / (e**2).sum()],
        err=[round(float(x), 2) for x in e],
    )


def analyse(year: int, cache: Path, deep: bool) -> dict:
    """C3b decomposition and counterfactuals for one year."""
    f = p94.rebuild(year, cache)
    st = p94.setters(year, f)
    P, D, iu, label = st["P"], st["D"], st["iu"], st["label"]
    lam = p94.p91.lambda_cst(year)
    act = bench_mon(year)
    base = monthly(P, D)
    res = dict(
        year=year,
        model_mon=[round(x, 2) for x in base],
        bench_mon=[round(x, 2) for x in act],
        lam_mon_model_w=[round(x, 2) for x in monthly(lam, D)],
        base=split(base, act),
    )
    q40, q80 = np.quantile(lam, [0.4, 0.8])
    bands = {"low40": lam <= q40, "mid": (lam > q40) & (lam <= q80), "top20": lam > q80}

    # --- counterfactuals -------------------------------------------------------------
    cf = {}
    cf["elliott_at_lambda"] = split(monthly(np.where(ELLIOTT, lam, P), D), act)
    cf["dec_dropped"] = round(_nrmse(base[:11], act[:11]), 4)
    cf["top20_at_lambda"] = split(monthly(np.where(bands["top20"], lam, P), D), act)
    cf["top20_and_elliott_at_lambda"] = split(
        monthly(np.where(bands["top20"] | ELLIOTT, lam, P), D), act
    )
    cf["low40_at_lambda"] = split(monthly(np.where(bands["low40"], lam, P), D), act)
    # measured plant-month delivered fuel at the setter (soco-94 construction)
    has = iu >= 0
    iuc = np.where(has, iu, 0)
    ar = np.arange(T)
    hr = np.where(has, f["hr"][iuc], np.nan)
    fuel_m = np.where(has, f["fuel"][iuc, ar].astype(float), np.nan)
    grp = np.array([p94._fuel_group(str(k)) for k in f["klass"]], dtype=object)
    fg = np.where(has, grp[iuc], None)
    plant = np.where(has, f["plant"][iuc], -1)
    pm = p94.f923_plant_month(year)
    key = {
        (int(r.plant_id), int(r.month), r.fuel_group): float(r.price)
        for r in pm.itertuples()
    }
    fuel_meas = np.full(T, np.nan)
    for h in np.flatnonzero(has & (fg != None)):  # noqa: E711
        fuel_meas[h] = key.get((int(plant[h]), int(MONTH[h]) + 1, fg[h]), np.nan)
    fuel_err = np.nan_to_num(hr * (fuel_m - fuel_meas))
    cf["setter_fuel_f923"] = split(monthly(P - fuel_err, D), act)
    cf["setter_fuel_f923_cover"] = round(
        float(D[np.isfinite(fuel_meas)].sum() / D.sum()), 3
    )
    res["cf"] = cf

    if deep:
        W = D / D.sum()
        gap = P - lam
        per = []
        for m in range(12):
            mm = MONTH == m
            wm = D[mm] / D[mm].sum()
            row = dict(
                month=m + 1,
                model=round(base[m], 2),
                bench=round(act[m], 2),
                lam_model_w=round(float(np.average(lam[mm], weights=D[mm])), 2),
                gap=round(float((wm * gap[mm]).sum()), 2),
                by_band={},
                by_setter={},
            )
            for b, bm in bands.items():
                row["by_band"][b] = dict(
                    hours=int((bm & mm).sum()),
                    contrib=round(float((wm * gap[mm] * bm[mm]).sum()), 2),
                )
            lab = label[mm]
            for c in pd.unique(lab):
                s = lab == c
                row["by_setter"][str(c)] = dict(
                    share=round(float(wm[s].sum()), 3),
                    contrib=round(float((wm * gap[mm])[s].sum()), 2),
                )
            row["by_setter"] = dict(
                sorted(row["by_setter"].items(), key=lambda kv: kv[1]["contrib"])
            )
            per.append(row)
        res["months"] = per
        el = ELLIOTT
        res["elliott"] = dict(
            hours=int(el.sum()),
            P=round(float(np.average(P[el], weights=D[el])), 2),
            lam=round(float(np.average(lam[el], weights=D[el])), 2),
            lam_max=round(float(lam[el].max()), 1),
            P_max=round(float(P[el].max()), 1),
            dec_gap_share_from_elliott=round(
                float(
                    (D[el] * (P[el] - lam[el])).sum()
                    / (D[MONTH == 11] * (P[MONTH == 11] - lam[MONTH == 11])).sum()
                ),
                3,
            ),
        )
        res["year_gap_share_by_band"] = {
            b: round(float((W * gap)[bm].sum()), 3) for b, bm in bands.items()
        }
    return res


def main() -> None:
    """Run the diagnosis for the requested years and write JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    ap.add_argument("--deep", type=int, nargs="*", default=[2022])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for y in a.years:
        r = analyse(y, out, y in a.deep)
        (out / f"c3b_{y}.json").write_text(json.dumps(r, indent=1))
        c = r["cf"]
        print(
            f"{y}: C3b {r['base']['nrmse']:.3f} (level {r['base']['level_share']:.2f}, "
            f"shape-only {r['base']['shape_only_nrmse']:.3f}, r {r['base']['corr']:.2f}) | "
            f"Elliott@lam {c['elliott_at_lambda']['nrmse']:.3f} | Dec-dropped "
            f"{c['dec_dropped']:.3f} | top20@lam {c['top20_at_lambda']['nrmse']:.3f} | "
            f"top20+Ell@lam {c['top20_and_elliott_at_lambda']['nrmse']:.3f} | "
            f"low40@lam {c['low40_at_lambda']['nrmse']:.3f} | setterF923 "
            f"{c['setter_fuel_f923']['nrmse']:.3f} (cover {c['setter_fuel_f923_cover']})"
        )


if __name__ == "__main__":
    main()
