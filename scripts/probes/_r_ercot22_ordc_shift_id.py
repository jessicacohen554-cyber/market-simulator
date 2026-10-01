"""R-ERCOT-22 phase 0 (zero LP): the scarcity-tail sensitivity and the ORDC shift vintage.

Four reads, all on committed artifacts:

1. **Tail decomposition, r-20 -> r-21.** For the hours the r-20 keeper priced above
   $200, split the load-weighted price change into the LP energy dual and the post-solve
   ORDC adder, and compare every reserve family's dual / held / shortfall. r-20's hourlies
   are read from git at the R-ERCOT-21 merge parent ``dfbbf599``.
2. **Gap by actual price band.** The r-21 keeper's demand-weighted price minus ERCOT's
   measured ``system_lambda + RTORPA + RTORDPA``, split into the energy and adder parts.
3. **RTORPA identification.** The published RTORPA formula
   (``results.scarcity.ordc_adder``) evaluated on ERCOT's own measured RTOLCAP / RTOFFCAP
   / system lambda, under the keeper's curve and under the PUCT 48551 shift vintage.
4. **2019 zero-LP estimate.** The r-21 2019 adder rescaled by the in-LP ORDC step ratio
   (0.25 vs 0.5 sigma) at the model's own held ORDC-total reserve.

Writes ``docs/handoffs/r-ercot/r_ercot22_phase0.json``.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.results.scarcity import (  # noqa: E402
    ercot_ordc_demand_steps,
    floor_active_mask,
    ordc_adder,
)

R20_SHA = "dfbbf599"
R20 = "results/calibration/r_ercot20_span/hourly"
R21 = ROOT / "results/calibration/r_ercot21_span/hourly"
MEAS = ROOT / "data/raw/ercot"
OUT = ROOT / "docs/handoffs/r-ercot/r_ercot22_phase0.json"
YEARS = range(2019, 2026)


def _r20(name: str) -> pd.DataFrame:
    """Read one r-20 hourly sidecar from git history."""
    blob = subprocess.run(
        ["git", "show", f"{R20_SHA}:{R20}/{name}"], cwd=ROOT, capture_output=True, check=True
    ).stdout
    return pd.read_parquet(io.BytesIO(blob))


def _r21(name: str) -> pd.DataFrame:
    """Read one r-21 keeper hourly sidecar."""
    return pd.read_parquet(R21 / name)


def _system(df: pd.DataFrame) -> pd.DataFrame:
    """Demand-weighted system price, energy dual and adders by hour (P1)."""
    d = df[df["pass"] == "P1"].copy()
    d["pw"] = d.price * d.demand
    g = d.groupby("hour").agg(
        pw=("pw", "sum"),
        dem=("demand", "sum"),
        slack=("slack", "sum"),
        ordc=("ordc_adder", "first"),
        ovl=("rtordpa_overlay", "first"),
    )
    g["lw"] = g.pw / g.dem
    g["ordc"] = g.ordc.fillna(0.0)
    g["ovl"] = g.ovl.fillna(0.0)
    g["energy"] = g.lw - g.ordc - g.ovl
    return g


def _bands(series: pd.Series, edges, labels) -> pd.Series:
    return pd.cut(series, edges, labels=labels)


def tail_decomposition(year: int) -> dict:
    """Read 1: where r-21's price change landed, split energy vs adder, plus reserve families."""
    a = _system(_r20(f"system_{year}.parquet"))
    b = _system(_r21(f"system_{year}.parquet"))
    w = b.dem / b.dem.sum()
    labels = ["<50", "50-100", "100-200", "200-1k", ">1k"]
    band = _bands(a.lw, [-1e9, 50, 100, 200, 1000, 1e9], labels)
    rows = {}
    for lab in labels:
        m = band == lab
        rows[lab] = {
            "hours": int(m.sum()),
            "dLW": round(float(((b.lw - a.lw) * w)[m].sum()), 3),
            "dEnergy": round(float(((b.energy - a.energy) * w)[m].sum()), 3),
            "dORDC": round(float(((b.ordc - a.ordc) * w)[m].sum()), 3),
        }
    tight = a.lw > 200
    fa = _r20(f"reserve_family_{year}.parquet")
    fb = _r21(f"reserve_family_{year}.parquet")
    fams = {}
    for fam in sorted(set(fa.family.astype(str))):
        xa = fa[(fa["pass"] == "P1") & (fa.family == fam)].set_index("hour")
        xb = fb[(fb["pass"] == "P1") & (fb.family == fam)].set_index("hour")
        idx = a.index[tight]
        fams[fam] = {
            k: [round(float(xa[k].reindex(idx).mean()), 1), round(float(xb[k].reindex(idx).mean()), 1)]
            for k in ("dual", "held_mw", "shortfall_mw")
        }
    ca = _r20(f"class_hourly_{year}.parquet")
    cb = _r21(f"class_hourly_{year}.parquet")
    pa = ca[ca["pass"] == "P1"].pivot_table(index="hour", columns="klass", values="mw", observed=True)
    pb = cb[cb["pass"] == "P1"].pivot_table(index="hour", columns="klass", values="mw", observed=True)
    dcls = (pb[tight.values] - pa[tight.values]).mean()
    return {
        "LW": [round(float((a.lw * w).sum()), 2), round(float((b.lw * w).sum()), 2)],
        "by_r20_band": rows,
        "r20_hours_gt200": int(tight.sum()),
        "still_gt200_in_r21": int((b.lw[tight] > 200).sum()),
        "reserve_families_on_r20_gt200_hours_[r20,r21]": fams,
        "class_mw_change_on_those_hours": {k: round(float(v), 0) for k, v in dcls.items() if abs(v) > 20},
        "slack_MWh_on_those_hours": [float(a.slack[tight].sum()), float(b.slack[tight].sum())],
    }


def _measured(year: int) -> pd.DataFrame:
    return pd.read_parquet(MEAS / f"ercot_{year}_ordc_reserves_hourly.parquet").set_index("hour").iloc[:8760]


def gap_by_actual_band(year: int) -> dict:
    """Read 2: r-21 minus measured, by actual price band, split energy vs adder."""
    b = _system(_r21(f"system_{year}.parquet"))
    m = _measured(year)
    w = b.dem / b.dem.sum()
    act = m.system_lambda + m.rtorpa + m.rtordpa
    g_e = (b.energy - m.system_lambda) * w
    g_a = (b.ordc + b.ovl - m.rtorpa - m.rtordpa) * w
    labels = ["<100", "100-200", "200-1k", ">1k"]
    band = _bands(act, [-1e9, 100, 200, 1000, 1e9], labels)
    act_lw = float((act * w).sum())
    out = {
        "model_LW": round(float((b.lw * w).sum()), 2),
        "actual_LW": round(act_lw, 2),
        "proxy_C3a": round(float((g_e + g_a).sum()) / act_lw, 4),
        "bands": {},
    }
    for lab in labels:
        k = band == lab
        out["bands"][lab] = {
            "hours": int(k.sum()),
            "gap": round(float((g_e + g_a)[k].sum()), 2),
            "gap_energy": round(float(g_e[k].sum()), 2),
            "gap_adder": round(float(g_a[k].sum()), 2),
            "model_energy_mean": round(float(b.energy[k].mean()), 1),
            "actual_lambda_mean": round(float(m.system_lambda[k].mean()), 1),
            "model_adder_mean": round(float(b.ordc[k].mean()), 1),
            "actual_rtorpa_mean": round(float(m.rtorpa[k].mean()), 1),
            "actual_prc_mean": round(float(m.prc[k].mean()), 0),
        }
    return out


def published_shift(year: int, idx: pd.DatetimeIndex) -> np.ndarray:
    """PUCT 48551 LOLP shift (sigma units) in force at each hour."""
    if year < 2019:
        return np.zeros(len(idx))
    if year == 2019:
        return np.where(idx >= pd.Timestamp("2019-03-01"), 0.25, 0.0)
    if year == 2020:
        return np.where(idx >= pd.Timestamp("2020-03-01"), 0.5, 0.25)
    return np.full(len(idx), 0.5)


def rtorpa_identification(year: int) -> dict:
    """Read 3: published RTORPA formula on measured reserves vs published RTORPA."""
    m = _measured(year)
    voll, mcl = (9000.0, 2000.0) if year < 2022 else (5000.0, 3000.0)
    fa = floor_active_mask(year, 8760)
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    full = (m.rtolcap + m.rtoffcap).to_numpy()
    on = m.rtolcap.to_numpy()
    lam = m.system_lambda.to_numpy()
    act = m.rtorpa.to_numpy()
    if not np.isfinite(act).all():
        return {"skipped": "non-finite RTORPA in the measured series"}

    def run(shift) -> np.ndarray:
        shift = np.broadcast_to(np.asarray(shift, dtype=float), (8760,))
        out = np.zeros(8760)
        for v in np.unique(shift):
            k = shift == v
            out[k] = ordc_adder(
                full[k], lam[k], voll=voll, mcl_mw=mcl, mu_mw=0.0, sigma_mw=1400.0,
                shift_sigma=float(v), floor_active=fa[k], reserves_online_mw=on[k],
            )
        return out

    jf = idx < pd.Timestamp(f"{year}-03-01")
    res = {"actual_sum": round(float(act.sum()), 0), "actual_share_jan_feb": round(float(act[jf].sum() / act.sum()), 4)}
    for name, sh in (("keeper_0.5", 0.5), ("published_hourly", published_shift(year, idx)),
                     ("year_flat_0.25", 0.25), ("year_flat_0.0", 0.0)):
        v = run(sh)
        res[name] = {"sum": round(float(v.sum()), 0), "ratio": round(float(v.sum() / act.sum()), 3),
                     "r": round(float(np.corrcoef(v, act)[0, 1]), 3)}
    return res


def estimate_2019() -> dict:
    """Read 4: r-21 2019 adder rescaled by the in-LP step ratio at the model's held reserve."""
    b = _system(_r21("system_2019.parquet"))
    fam = _r21("reserve_family_2019.parquet")
    fam = fam[(fam["pass"] == "P1") & (fam.family == "ercot_ordc_total")].set_index("hour")
    held = fam.held_mw.reindex(b.index).to_numpy()
    w = (b.dem / b.dem.sum()).to_numpy()

    def step(r, sh):
        req, pen, _ = ercot_ordc_demand_steps(voll=9000.0, mcl_mw=2000.0, mu_mw=0.0, sigma_mw=1400.0,
                                             shift_sigma=sh, multistep_floor=True)
        grid = np.linspace(req, 0.0, len(pen) + 1)
        j = np.clip(np.searchsorted(-grid[1:], -r, side="left"), 0, len(pen) - 1)
        return pen[j]

    r05, r025 = step(held, 0.5), step(held, 0.25)
    ratio = np.where(r05 > 0, r025 / np.maximum(r05, 1e-9), 1.0)
    new = b.ordc.to_numpy() * ratio
    d_lw = float(((new - b.ordc.to_numpy()) * w).sum())
    m = _measured(2019)
    act_lw = float(((m.system_lambda + m.rtorpa + m.rtordpa).to_numpy() * w).sum())
    lw = float((b.lw.to_numpy() * w).sum())
    return {
        "dw_adder": [round(float((b.ordc.to_numpy() * w).sum()), 2), round(float((new * w).sum()), 2)],
        "dLW": round(d_lw, 2),
        "LW": [round(lw, 2), round(lw + d_lw, 2)],
        "proxy_C3a": [round(lw / act_lw - 1, 4), round((lw + d_lw) / act_lw - 1, 4)],
    }


def main() -> None:
    """Run the four reads and write the JSON record."""
    rec = {
        "tail_decomposition": {y: tail_decomposition(y) for y in (2019, 2023, 2024)},
        "gap_by_actual_band": {y: gap_by_actual_band(y) for y in YEARS},
        "rtorpa_identification": {y: rtorpa_identification(y) for y in YEARS},
        "estimate_2019_shift_0.25": estimate_2019(),
    }
    OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(json.dumps(rec["rtorpa_identification"], indent=1))
    print(json.dumps(rec["estimate_2019_shift_0.25"], indent=1))


if __name__ == "__main__":
    main()
