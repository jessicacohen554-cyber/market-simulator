"""soco-84 zero-LP probe: where SOCO's model price departs from Southern's system lambda.

Reads committed artifacts only (keeper payload + bench parts + hourly sidecars +
the committed lambda sidecar). No LP, no fleet rebuild.

1. ``gap`` — per year: lambda vs model (load-weighted), and the gap split by
   system-load quintile and by season, plus the hours the model price sits
   more than $5 above / below the lambda.
2. ``coal`` — the "same conduct" test (soco-82/83 found the real system runs
   out-of-merit coal). Hourly coal gap = CEMS actual - model, over the same
   CEMS-covered plants (bench ``plants[].campd`` / payload ``plants[].m``).
   The model's own price response to gas output is read per month as a
   nonparametric curve (binned median price vs model gas MW); shifting model
   gas output down by the hourly coal gap and re-reading that curve gives a
   first-order counterfactual price. A reading, not a solve.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_soco84_price_gap.py
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src"), str(ROOT)]
import calibration_verdict as cv  # noqa: E402

# Repointed soco-85 (2026-09-28): soco83_span was pruned at the soco-85 promotion (rule 35);
# the incumbent keeper is soco85_span (the soco-83 recipe + gas_daily_shape).
# Repointed soco-87 (2026-09-29): soco85_span was pruned at the soco-87 promotion (rule 35);
# the incumbent keeper is soco92_span (the soco-85 recipe + gas_hh_monthly_shape).
KEEPER = "2026-09-28-soco85-gas-daily-shape"
SPAN = (
    ROOT / "results/calibration/soco92_span"
)  # repointed soco-92 (rule 35 prune of soco92_span)
LAM = ROOT / "data/raw/_validation-source/actual_lmp_hourly_SOCO.parquet"
BENCH = ROOT / "frontend/data/backcast/bench/SOCO"
GAS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
COAL = ("COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC")
T = 8760
MONTH = np.searchsorted(
    np.cumsum([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])[:-1] * 24,
    np.arange(T),
    side="right",
)  # 0..11


def _hourly_coal(ypay: dict, ybench: dict) -> tuple[np.ndarray, np.ndarray]:
    """(actual, model) hourly MW over the CEMS-covered coal plants."""
    act, mod = np.zeros(T), np.zeros(T)
    pp = ypay["plants"]
    for code, bp in ybench["plants"].items():
        if bp.get("group") not in COAL or bp.get("nodata"):
            continue
        cap = float(bp.get("npl") or 0.0)
        m = (pp.get(str(code)) or {}).get("m")
        if cap <= 0 or not bp.get("campd") or not m:
            continue
        act += np.frombuffer(base64.b64decode(bp["campd"])[:T], np.uint8) * cap / 100
        mod += np.frombuffer(base64.b64decode(m)[:T], np.uint8) * cap / 100
    return act, mod


def _curve_price(price: np.ndarray, gas: np.ndarray, gas_new: np.ndarray) -> np.ndarray:
    """Per month: monotone price-vs-gas-MW curve (binned medians), read at gas_new."""
    out = price.copy()
    for mo in range(12):
        sel = MONTH == mo
        g, p = gas[sel], price[sel]
        edges = np.unique(np.quantile(g, np.linspace(0, 1, 21)))
        if edges.size < 3:
            continue
        idx = np.clip(np.searchsorted(edges, g, side="right") - 1, 0, edges.size - 2)
        xs = np.array(
            [g[idx == i].mean() for i in range(edges.size - 1) if (idx == i).any()]
        )
        ys = np.array(
            [np.median(p[idx == i]) for i in range(edges.size - 1) if (idx == i).any()]
        )
        ys = np.maximum.accumulate(ys)  # a supply curve is non-decreasing
        # shift each hour's own price by the curve's change (keeps hourly noise)
        out[sel] = p + np.interp(gas_new[sel], xs, ys) - np.interp(g, xs, ys)
    return out


def main() -> None:
    """Print the gap decomposition and the coal-conduct counterfactual per year."""
    pay = cv.load_artifacts(KEEPER)["payload"]
    lam_all = pd.read_parquet(LAM)
    rows = []
    for y in range(2019, 2026):
        ypay = pay["years"][str(y)]
        ybench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
        s = pd.read_parquet(SPAN / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        dem = s.groupby("hour")["demand"].sum().sort_index().to_numpy()
        price = (
            (
                (s.price * s.demand).groupby(s.hour).sum()
                / s.groupby("hour")["demand"].sum()
            )
            .sort_index()
            .to_numpy()
        )
        lam = lam_all[lam_all.year == y].sort_values("hour")["rt"].to_numpy(float)
        ch = pd.read_parquet(SPAN / f"hourly/class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        gas = (
            ch[ch.klass.isin(GAS)]
            .groupby("hour")["mw"]
            .sum()
            .reindex(range(T), fill_value=0)
            .to_numpy()
        )
        act_c, mod_c = _hourly_coal(ypay, ybench)
        dcoal = act_c - mod_c
        cf = _curve_price(price, gas, np.maximum(gas - dcoal, 0.0))

        def lw(v, m=None):
            m = np.ones(T, bool) if m is None else m
            return float((v[m] * dem[m]).sum() / dem[m].sum())

        q = np.quantile(dem, [0.2, 0.4, 0.6, 0.8])
        quint = np.searchsorted(q, dem)
        summer = np.isin(MONTH, [5, 6, 7, 8])
        rows.append(
            dict(
                year=y,
                lam=lw(lam),
                model=lw(price),
                gap_pct=100 * (lw(price) / lw(lam) - 1),
                **{
                    f"q{i + 1}": lw(price, quint == i) - lw(lam, quint == i)
                    for i in range(5)
                },
                summer=lw(price, summer) - lw(lam, summer),
                other=lw(price, ~summer) - lw(lam, ~summer),
                h_above5=int((price - lam > 5).sum()),
                h_below5=int((lam - price > 5).sum()),
                coal_gap_twh=dcoal.sum() / 1e6,
                cf_model=lw(cf),
                cf_gap_pct=100 * (lw(cf) / lw(lam) - 1),
            )
        )
    df = pd.DataFrame(rows).set_index("year")
    pd.set_option("display.width", 200)
    print(df.round(2).to_string())


if __name__ == "__main__" and len(sys.argv) == 1:
    main()


# ---------------------------------------------------------------------------
# ``setter`` — which class's offer sits at the model's price, by load quintile
# ---------------------------------------------------------------------------
RECIPE_SETS = (
    "eia860_vintage_tracks_solve_year",
    "measured_chp_heat_rates",
    "unit_outage_short_windows",
    "unit_outage_short_windows_gas",
    "unit_partial_outage_windows",
    "unit_outage_precod_clip",
    "summer_derate_basis_aware",
    "coal_mustrun_requires_measured_row",
    "egrid_identity_heat_rates",
    "coal_econ_marginal_hr_two_sided",
    "st_gas_mustrun_per_plant",
    "st_gas_mustrun_p25_level",
    "st_gas_mustrun_oom_level",
    "gas_daily_shape",
)


def fleet(year: int) -> dict:
    """fleet_only rebuild on the soco83 keeper recipe (PRECOMMIT-soco-83 §5)."""
    import contextlib
    import io

    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year

    meta = json.loads((SPAN / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(SPAN), year))
    kw.setdefault("prb_overrides", {}).update({k: True for k in RECIPE_SETS})
    with (
        contextlib.redirect_stderr(io.StringIO()),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        st = run_year(
            year,
            meta["iso"],
            T,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kw,
        )
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], float)
    return dict(
        klass=np.asarray(fa.plant_group).astype(str),
        zone=np.asarray(fa.zone_idx),
        hr=np.asarray(fa.heat_rate, float),
        mc=mc if mc.ndim == 2 else np.repeat(mc[:, None], T, axis=1),
        pmax=np.asarray(fa.pmax, float),
    )


def main_setter(years=(2019, 2022, 2023)) -> None:
    """Per load quintile: share of hours whose price sits within $0.25 of a class's offer."""
    lam_all = pd.read_parquet(LAM)
    for y in years:
        f = fleet(y)
        s = pd.read_parquet(SPAN / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        dem = s.groupby("hour")["demand"].sum().sort_index().to_numpy()
        pz = s.pivot(index="hour", columns="zone", values="price").sort_index()
        price = pz.mean(axis=1).to_numpy()
        lam = lam_all[lam_all.year == y].sort_values("hour")["rt"].to_numpy(float)
        quint = np.searchsorted(np.quantile(dem, [0.2, 0.4, 0.6, 0.8]), dem)
        near = np.abs(f["mc"] - price[None, :]) <= 0.25  # units x hours
        classes = sorted(set(f["klass"]))
        print(
            f"\n{y}: zone price spread p95 ${np.percentile(pz.max(1) - pz.min(1), 95):.2f}"
        )
        hdr = (
            "quint  model  lambda  "
            + " ".join(f"{c[:9]:>9}" for c in classes)
            + "   none"
        )
        print(hdr)
        for qi in range(5):
            h = quint == qi
            shares = []
            for c in classes:
                shares.append(near[f["klass"] == c][:, h].any(axis=0).mean())
            none = (~near[:, h].any(axis=0)).mean()
            print(
                f"  q{qi + 1}  {price[h].mean():6.2f} {lam[h].mean():6.2f}  "
                + " ".join(f"{v:9.2f}" for v in shares)
                + f"  {none:5.2f}"
            )
        # the off-peak setters' heat rates (q1): mean HR of units near the price
        h = quint == 0
        for c in classes:
            u = (f["klass"] == c) & near[:, h].any(axis=1)
            if u.any():
                print(
                    f"    q1 {c}: {int(u.sum())} units near price, HR mean "
                    f"{np.average(f['hr'][u], weights=f['pmax'][u]):.2f} MMBtu/MWh, "
                    f"mc median ${np.median(f['mc'][u][:, h]):.2f}"
                )


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "setter":
    main_setter()
