"""pjm-h18 phase 0 — where the 2020/2022 mean-LMP error lives. ZERO LP.

Rule 32 ``[R-SHARD]`` (a): the parent runs no LP. Reads only the PJM keeper's
committed ``hourly/system_<year>.parquet`` sidecars and the measured RT hub
series, and splits each year's load-weighted C3a error ($/MWh) by season,
by actual-price decile, by Eastern-hub gas-spike day (Transco Z6 NY vs Henry
Hub, each normalised to its own month mean) and by input-glitch hour. Also
reports the monthly load-weighted C3b NRMSE with and without the two localised
objects (Winter Storm Elliott 2022-12-23..26; the 2020 demand-spike hours).

Nothing is swept and no parameter is constructed (rules 1 ``[R-STRUCT]`` /
21 ``[R-DOF]``). Record: ``docs/FINDING-pjm-h18-price-object-localised-2026-09-23.md``.

Run: ``python3 scripts/probes/pjm_h18_price_split_phase0.py``
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SPAN = REPO / "results/calibration/hydro2_pjm_ror_span"
TOUCH = REPO / "results/calibration/hydro2_pjm_ror_touchpoint"
ELLIOTT_DOY = (357, 360)  # 2022-12-23 .. 2022-12-26
GLITCH_2020 = (5003, 5031, 5383)  # demand-spike hours, neighbour ratio 1.46/1.25/1.40


def load_year(y: int, act: pd.DataFrame) -> pd.DataFrame:
    """Hourly load-weighted model price, measured demand and RT hub actual."""
    b = SPAN if y >= 2023 else TOUCH
    s = pd.read_parquet(b / "hourly" / f"system_{y}.parquet")
    s = s[(s["pass"] == "P1") & (s.zone != "PJM_external")]
    s = s.assign(pdm=s.price * s.demand)
    g = s.groupby("hour")[["pdm", "demand", "slack"]].sum()
    g["p"] = g.pdm / g.demand
    g["a"] = act[act.year == y].sort_values("hour").rt.to_numpy(float)[: len(g)]
    t = pd.to_datetime(f"{y}-01-01") + pd.to_timedelta(g.index, unit="h")
    g["m"], g["doy"], g["date"] = t.month, t.dayofyear, t.date
    return g


def contrib(g: pd.DataFrame, mask) -> float:
    """Load-weighted contribution of ``mask`` hours to the annual error, $/MWh."""
    return float(((g.p - g.a) * g.demand)[mask].sum() / g.demand.sum())


def nrmse(g: pd.DataFrame) -> float:
    """Monthly load-weighted price NRMSE (the C3b statistic)."""
    mm = g.groupby("m").apply(
        lambda d: pd.Series(
            {"p": np.average(d.p, weights=d.demand), "a": np.average(d.a, weights=d.demand)}
        ),
        include_groups=False,
    )
    return float(np.sqrt(((mm.p - mm.a) ** 2).mean()) / mm.a.mean())


def pct(g: pd.DataFrame) -> float:
    """C3a magnitude, % (model lw mean / actual lw mean - 1)."""
    return float(100 * ((g.p * g.demand).sum() / (g.a * g.demand).sum() - 1))


def main() -> None:
    """Write ``results/calibration/_pjm_h18_price_split.json`` and print the table."""
    act = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet")
    z = pd.read_csv(REPO / "data/raw/gas-prices/transco_z6_ny_daily.csv", parse_dates=["date"]).dropna()
    ym = z.date.dt.to_period("M")
    z["s"] = (z.transco_z6_ny_usd_mmbtu / z.groupby(ym).transco_z6_ny_usd_mmbtu.transform("mean")) / (
        z.henry_hub_usd_mmbtu / z.groupby(ym).henry_hub_usd_mmbtu.transform("mean")
    )
    spike = z.set_index(z.date.dt.date).s
    out = {}
    for y in range(2020, 2026):
        g = load_year(y, act)
        q = pd.qcut(g.a.rank(method="first"), 10, labels=False)
        s = g.date.map(spike).ffill().fillna(1.0)
        ell = (g.m == 12) & g.doy.between(*ELLIOTT_DOY) if y == 2022 else pd.Series(False, index=g.index)
        gl = g.index.isin(GLITCH_2020) if y == 2020 else np.zeros(len(g), bool)
        r = {
            "c3a_pct": pct(g),
            "err_usd": contrib(g, g.index >= 0),
            "season": {
                "winter": contrib(g, g.m.isin([12, 1, 2])),
                "shoulder": contrib(g, g.m.isin([3, 4, 5, 9, 10, 11])),
                "summer": contrib(g, g.m.isin([6, 7, 8])),
            },
            "actual_price_decile": [contrib(g, q == k) for k in range(10)],
            "bottom50": contrib(g, g.a <= g.a.quantile(0.5)),
            "p50_p95": contrib(g, (g.a > g.a.quantile(0.5)) & (g.a < g.a.quantile(0.95))),
            "top5": contrib(g, g.a >= g.a.quantile(0.95)),
            "gas_spike_days_ge2x": {"days": float((s >= 2).sum() / 24), "contrib": contrib(g, s >= 2)},
            "elliott_contrib": contrib(g, ell),
            "glitch_contrib": contrib(g, gl),
            "slack_hours": int((g.slack > 1).sum()),
            "c3b_nrmse": nrmse(g),
        }
        if y == 2022:
            r["c3a_pct_ex_elliott"] = pct(g[~ell])
            r["c3b_nrmse_ex_elliott"] = nrmse(g[~ell])
        if y == 2020:
            r["c3a_pct_ex_glitch"] = pct(g[~gl])
            r["c3b_nrmse_ex_glitch"] = nrmse(g[~gl])
        out[y] = r
        print(
            f"{y} C3a {r['c3a_pct']:+5.1f}% err {r['err_usd']:+6.2f} | bottom50 {r['bottom50']:+5.2f} "
            f"p50-95 {r['p50_p95']:+5.2f} top5 {r['top5']:+6.2f} | spike-days {r['gas_spike_days_ge2x']['contrib']:+5.2f} "
            f"| C3b {r['c3b_nrmse']:.3f}"
        )
    dest = REPO / "results/calibration/_pjm_h18_price_split.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
