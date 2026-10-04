"""closeout-SOCO-w3 zero-LP reach: the host-steam/BTM holdout of SOCO's injected biomass/OTHER must-run.

Mechanism: the existing ``ScenarioConfig.mustrun_chp_btm_holdout`` (miso-253; SOCO cell U). It drops chp=Y rows
from the injected residual classes at the single seam both the must-run injection and the benchmark read
(``run_calibration_full._eia923_frame``), so the model's demand net of must-run rises by the held-out MW and the
bench's biomass/OTHER fall by the same energy.

Method (fixed ex ante in docs/records/soco/closeout-soco-w3/PRECOMMIT-phase0-closeout-soco-w3-2026-10-04.md):

1. per year, the hourly system must-run MW with and without the holdout, from ``_must_run_profiles`` on the
   keeper's own zone demand (dD[t] = removed MW);
2. hourly copperplate restack of the keeper's econ/peak tranches (everything else, hydro and floor-bound coal held
   at keeper mw) at E[t] and at E[t] + dD[t] (the closeout-SOCO-w2 restack, same validity gate);
3. delta method onto the keeper's class energies and prices; the bench's biomass/OTHER and the payload's injected
   biomass/OTHER both drop by the held-out energy; C1 via ``calibration_verdict.score_fuelmix``, C3a/C3b via
   ``score_price_mean`` / ``score_price_shape``.

Keeper: results/calibration/closeout_soco_3_span (2026-10-03-closeout-soco-3-coalpile). No LP.
Output: docs/records/soco/closeout-soco-w3/btm_reach.csv, btm_footprint.csv.
"""

from __future__ import annotations

import json
import gzip
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts/probes"))
import calibration_verdict as cv  # noqa: E402
import run_calibration_full as rcf  # noqa: E402
from _closeout_socow2_spot_reach import (  # noqa: E402
    COAL,
    FLEX,
    FLOOR_TOL,
    KEEPER,
    load_payload,
    restack,
    score_year,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402

OUT = REPO / "docs/records/soco/closeout-soco-w3"
YEARS = range(2019, 2026)
ISO = "SOCO"


def removed_mw(y: int, gen: pd.DataFrame, s: pd.DataFrame) -> tuple[np.ndarray, dict]:
    """Return (hourly system MW the holdout removes from the injection, per-class held-out TWh)."""
    zones = sorted(s.zone.unique())
    dem = np.vstack(
        [s[s.zone == z].set_index("hour").demand.reindex(range(8760)).to_numpy() for z in zones]
    )
    e930 = rcf._eia930_frame(y, ISO, get_iso_config(ISO))
    off = rcf._must_run_profiles(y, gen, ISO, dem, e930=e930, mustrun_chp_btm_holdout=False)
    on = rcf._must_run_profiles(y, gen, ISO, dem, e930=e930, mustrun_chp_btm_holdout=True)
    d = np.zeros(8760)
    per = {}
    for k in set(off) | set(on):
        a = off.get(k, np.zeros_like(dem)).sum(axis=0)
        b = on.get(k, np.zeros_like(dem)).sum(axis=0)
        d += a - b
        per[k] = (a.sum() - b.sum()) / 1e6
    return d, per


def reach(y: int, dD: np.ndarray) -> dict:
    """Restack the keeper's flexible stack at E and E + dD; return validity, class dE (TWh) and hourly dp."""
    u = pd.read_parquet(
        KEEPER / f"unit_marginal_{y}.parquet",
        columns=["unit_id", "plant_code", "plant_group", "hour", "mw", "cap_mw", "mc"],
    )
    u["tr"] = u.unit_id.astype(str).str.extract(r"_([a-z]+)$")[0]
    s = pd.read_parquet(KEEPER / f"system_{y}.parquet")
    zp = s.groupby("hour").price.mean().reindex(range(8760)).to_numpy()
    flex = u[u.tr.isin(FLEX) & ~u.plant_group.isin(["hydro", ""])].copy()
    iscoal = flex.plant_group.isin(COAL).to_numpy()
    bound = iscoal & (flex.mw.to_numpy() > 0) & (flex.mc.to_numpy() > zp[flex.hour.to_numpy()] + FLOOR_TOL)
    flex = flex[~bound]
    units = sorted(flex.unit_id.astype(str).unique())
    idx = {k: i for i, k in enumerate(units)}
    ui = flex.unit_id.astype(str).map(idx).to_numpy()
    h = flex.hour.to_numpy()
    MC = np.full((len(units), 8760), 1e4)
    CAP = np.zeros((len(units), 8760))
    MW = np.zeros((len(units), 8760))
    MC[ui, h], CAP[ui, h], MW[ui, h] = flex.mc, flex.cap_mw, flex.mw
    cls = flex.drop_duplicates("unit_id").set_index(flex.drop_duplicates("unit_id").unit_id.astype(str)).plant_group.astype(str).reindex(units).to_numpy()
    E = MW.sum(axis=0)
    headroom = CAP.sum(axis=0) - E
    disp0, p0 = restack(MC, CAP, E)
    disp1, p1 = restack(MC, CAP, E + dD)
    dem = s.groupby("hour").demand.sum().reindex(range(8760)).to_numpy()
    lw_k = (zp * dem).sum() / dem.sum()
    lw_r = (p0 * dem).sum() / dem.sum()
    valid = dict(
        year=y,
        lw_keeper=lw_k,
        lw_restack=lw_r,
        err_pct=100 * (lw_r / lw_k - 1),
        r_hourly=float(np.corrcoef(p0, zp)[0, 1]),
        short_hours=int((headroom < dD).sum()),
    )
    valid["ok"] = abs(valid["err_pct"]) <= 5.0 and valid["r_hourly"] >= 0.85
    dE = {}
    night = (np.arange(8760) % 24 < 6) | (np.arange(8760) % 24 >= 22)
    dE_night = {}
    for c in np.unique(cls):
        sel = cls == c
        dE[c] = float((disp1[sel] - disp0[sel]).sum() / 1e6)
        dE_night[c] = float((disp1[sel][:, night] - disp0[sel][:, night]).sum() / 1e6)
    return dict(valid=valid, dE=dE, dE_night=dE_night, dp=p1 - p0, s=s)


def edit_bench(yb: dict, per: dict) -> dict:
    """Return a copy of the bench with the held-out injected-class energy removed (lockstep seam)."""
    b = json.loads(json.dumps(yb))
    for k, v in per.items():
        if k in b["classFull"]:
            b["classFull"][k] = b["classFull"][k] - v
    return b


def main() -> None:
    """Write the footprint and the reach for every keeper year."""
    logging.disable(logging.WARNING)
    OUT.mkdir(parents=True, exist_ok=True)
    gen = rcf.load_monthly_generation()
    P = load_payload()
    rows, foot = [], []
    for y in YEARS:
        s = pd.read_parquet(KEEPER / f"system_{y}.parquet")
        dD, per = removed_mw(y, gen, s)
        yb = json.load(gzip.open(REPO / f"frontend/data/backcast/bench/SOCO/{y}.json.gz"))["bench"]
        r = reach(y, dD)
        foot.append(
            dict(
                year=y,
                held_out_twh=round(dD.sum() / 1e6, 3),
                **{f"held_{k}": round(v, 3) for k, v in per.items()},
                mean_mw=round(dD.mean(), 1),
                e930_other_twh=round(yb["e930"]["other"], 3),
                inject_before=round(sum(yb["classFull"].get(k, 0.0) for k in per), 3),
                inject_after=round(sum(yb["classFull"].get(k, 0.0) - v for k, v in per.items()), 3),
                **{f"v_{k}": v for k, v in r["valid"].items() if k != "year"},
            )
        )
        base = score_year(y, P, yb, s, None, None)
        yb2 = edit_bench(yb, per)
        dE = {k: v for k, v in r["dE"].items() if r["valid"]["ok"]}
        dE.update({k: -v for k, v in per.items()})
        arm = score_year(y, P, yb2, s, r["dp"], dE)
        for k in base:
            rows.append(
                dict(year=y, crit=k[0], key=k[1], keeper=base[k][0], keeper_mag=base[k][1],
                     arm=arm.get(k, (None, None))[0], arm_mag=arm.get(k, (None, None))[1])
            )
        rows.append(dict(year=y, crit="dE_TWh", key=json.dumps({c: round(v, 3) for c, v in r["dE"].items()}),
                         keeper=None, keeper_mag=None, arm=None, arm_mag=None))
        rows.append(dict(year=y, crit="dE_night_TWh", key=json.dumps({c: round(v, 3) for c, v in r["dE_night"].items()}),
                         keeper=None, keeper_mag=None, arm=None, arm_mag=None))
        print(y, foot[-1], flush=True)
    pd.DataFrame(foot).to_csv(OUT / "btm_footprint.csv", index=False)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "btm_reach.csv", index=False)
    pd.set_option("display.width", 250, "display.max_rows", 500, "display.max_colwidth", 200)
    print(df[(df.crit != "C1") | (df.keeper != df.arm) | df.key.isin(["CC_REGULAR", "COAL_BIT", "COAL_PRB", "ST_GAS", "CT_PEAKER"])].to_string(index=False))


if __name__ == "__main__":
    main()
