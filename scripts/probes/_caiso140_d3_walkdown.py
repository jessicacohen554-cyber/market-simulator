"""caiso-140 D3 — the belly walk-down: what happens to CA lambda when S MW of
price-taking CA supply is added in the 2025 Sep-Dec low-price hours. NO SOLVE.

The D3 gate demands an analytic E1/E2 prediction BEFORE any solve. The candidate
family (a committed-gas ride-through floor / drag) adds price-taking supply in
the Sep-Dec belly and overnight; this probe prices that counterfactual on the
keeper's own committed bytes plus the ``run_year(fleet_only=True)`` offer
reconstruction (the caiso-131/134 machinery — no LP is built, no solver runs).

The walk-down logic per hour, holding storage/hydro allocations fixed
(conservatism stated: PS pumping and battery charging are elastic and would
absorb part of the addition, so the printed lambda drop is an UPPER bound on
the drop; the import back-out is correspondingly a LOWER bound):

1. Added supply first displaces the marginal ECONOMIC import (never the firm
   self-scheduled blocks) — at constant lambda while the corridor is unbound
   and the tranche is interior; when the corridor group is bound the same
   displacement instead relieves the congestion component (lambda falls toward
   delivered-import parity).
2. Once economic import in the hour is exhausted, lambda falls down the
   CA-side dispatched stack: the new lambda is the offer of the rung that
   becomes marginal after removing the remaining MW from economically
   dispatched (above-floor) CA units, cheapest-from-the-top.

Output, per year (2025 then 2024, the E2 spillover year): the defect-hour
state (economic import depth, plateau share) and lambda(S) for S in
{0.5 .. 3.0} GW over the defect / Sep-Dec belly / Sep-Dec overnight hour
sets, with the implied annual C3a move on the rubric's rt_lw weights.

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_caiso140_d3_walkdown.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
HOURS = 8760
T = HOURS
BUNDLE = REPO / "results/calibration/caiso139_dumpguard_B"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
SCRATCH = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "295cb96e-f45f-5939-90a6-2e6a09958862/scratchpad"
)

_META_RENAME = {
    "coal_prb_passthrough_sigmoid": "prb_sigmoid",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
GAS_KLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")
# the two firm self-scheduled tranches (must-flow, pmin == pmax — cannot move)
FIRM_TRANCHES = ("DSW_solar_PV", "PNW_hydro_base")
SGRID = (500.0, 1000.0, 1500.0, 2000.0, 2500.0, 3000.0)


def actual_rt(year: int) -> np.ndarray:
    a = pd.read_parquet(ACTUAL_LMP)
    return a[a["year"] == year].set_index("hour")["rt"].reindex(range(HOURS)).to_numpy()


def month_of_hour(year: int) -> np.ndarray:
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(
        np.arange(HOURS + 24), unit="h"
    )
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    return stamps.month.to_numpy()


def rubric_weights(year: int) -> np.ndarray:
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia_loader import load_demand

    return np.asarray(load_demand(ISO, year, get_iso_config(ISO))).sum(axis=0)[:HOURS]


def fleet_state(year: int) -> dict:
    import inspect

    from run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {
        _META_RENAME.get(k, k): v
        for k, v in meta.items()
        if _META_RENAME.get(k, k) in params and _META_RENAME.get(k, k) not in skip
    }
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    return run_year(
        year, meta["iso"], int(meta.get("hours", HOURS)), gas, {}, fleet_only=True,
        **kwargs,
    )


def recon(year: int) -> dict:
    """Per-unit (mw, cap, min_gen, mc, klass, zone) aligned to the unit sidecar.

    Cached in the scratchpad as npz — deterministic in the bundle meta.
    """
    p = SCRATCH / f"caiso140_recon_{year}.npz"
    if p.exists():
        z = np.load(p, allow_pickle=True)
        return {k: z[k] for k in z.files}
    state = fleet_state(year)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], T, axis=1)
    ids = [str(u) for u in fa.unit_ids]
    pos = {u: i for i, u in enumerate(ids)}
    u = pd.read_parquet(
        BUNDLE / "hourly" / f"unit_hourly_{year}.parquet",
        columns=[
            "pass", "unit_id", "plant_group", "fuel", "zone", "hour", "mw",
        ],
    )
    u = u[u["pass"] == "P1"]
    mw = u.pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum")
    meta_cols = u.drop_duplicates("unit_id").set_index("unit_id")[
        ["plant_group", "fuel", "zone"]
    ]
    keep = [uid for uid in mw.index if uid in pos]
    mw = mw.loc[keep]
    meta_cols = meta_cols.loc[keep]
    sel = np.array([pos[uid] for uid in keep])
    cap = (fa.pmax[:, None] * fa.availability)[sel]
    min_gen = np.asarray(fa.min_gen, dtype=float)
    if min_gen.ndim == 1:
        min_gen = np.repeat(min_gen[:, None], T, axis=1)
    group = meta_cols["plant_group"].to_numpy().astype(str)
    fuel = meta_cols["fuel"].to_numpy().astype(str)
    out = {
        "mw": mw.to_numpy(),
        "cap": cap,
        "min_gen": min_gen[sel],
        "mc": mc[sel],
        "uid": np.array(keep, dtype=object),
        "zone": meta_cols["zone"].to_numpy().astype(str),
        "klass": np.where(group != "", group, fuel),
        "fuel": fuel,
    }
    np.savez_compressed(p, **out)
    return out


def hour_sets(year: int) -> dict:
    a = actual_rt(year)
    mo = month_of_hour(year)
    hd = np.arange(HOURS) % 24
    sepdec = np.isin(mo, (9, 10, 11, 12))
    return {
        "defect": sepdec
        & np.isin(hd, (10, 11, 12, 13, 14, 15))
        & (np.nan_to_num(a, nan=1e9) <= 20.0),
        "belly": sepdec & np.isin(hd, (10, 11, 12, 13, 14, 15)),
        "night": sepdec & np.isin(hd, (0, 1, 2, 3, 4, 5, 6)),
    }


def ca_lambda_and_prices(year: int) -> tuple[np.ndarray, pd.DataFrame]:
    d = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    price = d.pivot_table(index="hour", columns="zone", values="price")
    dem = d.pivot_table(index="hour", columns="zone", values="demand")
    ca = [z for z in price.columns if not str(z).startswith("WECC")]
    lam = ((price[ca] * dem[ca]).sum(axis=1) / dem[ca].sum(axis=1)).to_numpy()
    return lam, price


def walkdown(year: int, sgrid=SGRID) -> dict:
    """Counterfactual lambda(S) per hour for added price-taking CA supply S.

    Two regimes per hour (identified from the committed sidecars):

    * **corridor-priced** (SP15 lambda − WECC_DSW node lambda > $0.50 — the
      congestion component the caiso-131 §7 split measured): added supply
      walks straight down the CA dispatched stack (imports are at cap and
      cannot back out), floored at the node parity — once lambda reaches
      parity the corridor unbinds and the remaining plateau re-engages.
    * **parity-priced** (spread ≈ 0): the marginal economic import backs out
      at constant lambda first; only the excess over the hour's economic
      import walks the CA stack.

    Elasticity caveat, stated: battery charging (interior vs its shape-anchor
    cap) and PS pumping would absorb part of the addition at falling lambda,
    so the printed drop is an UPPER bound on the true drop in BOTH regimes.
    """
    r = recon(year)
    lam, price = ca_lambda_and_prices(year)
    sp15 = price["SP15_rest"].to_numpy()
    dsw = price["WECC_DSW"].to_numpy()
    spread = sp15 - dsw
    corridor_priced = spread > 0.5
    is_import = r["klass"] == "import"
    # firm must-flow rows: pmin == pmax (identified by tranche name membership)
    uid = np.array([str(x) for x in r["uid"]])
    firm = np.zeros(len(uid), bool)
    for t_name in FIRM_TRANCHES:
        firm |= np.char.find(uid.astype(str), t_name) >= 0
    econ_import = is_import & ~firm
    ca_row = ~np.char.startswith(r["zone"].astype(str), "WECC")
    mwm = np.nan_to_num(r["mw"], nan=0.0)
    # economically dispatched CA MW above the row's own floor
    floor = np.minimum(r["min_gen"], mwm)
    free_above_floor = np.where(ca_row[:, None], mwm - floor, 0.0)
    econ_imp_mw = np.where(econ_import[:, None], mwm, 0.0).sum(axis=0)
    out = {"econ_import_mw": econ_imp_mw, "corridor_priced": corridor_priced}
    lam_s = {}
    for S in sgrid:
        newlam = lam.copy()
        rem = np.where(corridor_priced, S, np.maximum(S - econ_imp_mw, 0.0))
        idxs = np.where(rem > 0)[0]
        for h in idxs:
            take = rem[h]
            rows = np.where(free_above_floor[:, h] > 1e-6)[0]
            if rows.size == 0:
                continue
            mc_h = r["mc"][rows, h]
            order = np.argsort(-mc_h)  # from the top of the dispatched stack
            cum = np.cumsum(free_above_floor[rows[order], h])
            k = np.searchsorted(cum, take)
            cand = float(mc_h[order[min(k, order.size - 1)]])
            if corridor_priced[h]:
                # descent floored at node parity: there the corridor unbinds
                # and the hour joins the plateau (economic import still >> 0)
                cand = max(cand, float(dsw[h]))
            # added supply can never RAISE lambda: clip at the incumbent price
            newlam[h] = min(newlam[h], cand)
        lam_s[S] = newlam
    out["lam"] = lam
    out["lam_s"] = lam_s
    return out


def main() -> int:
    for year in (2025, 2024):
        r = recon(year)
        sets = hour_sets(year)
        w = rubric_weights(year)
        wd = walkdown(year)
        lam = wd["lam"]
        print("=" * 78)
        print(f"{year}: defect n={int(sets['defect'].sum())}")
        m = sets["defect"]
        print(
            f"  defect hrs: lam mean {lam[m].mean():6.2f}  econ import mean "
            f"{wd['econ_import_mw'][m].mean():7.0f} MW  p25/p50/p75 "
            f"{np.percentile(wd['econ_import_mw'][m], [25, 50, 75])}"
        )
        for name, mask in sets.items():
            plateau = float(
                (wd["econ_import_mw"][mask] >= max(SGRID)).mean()
            )
            print(
                f"  -- {name} (n={int(mask.sum())}), lam mean {lam[mask].mean():.2f}"
                f"  econ import mean {wd['econ_import_mw'][mask].mean():7.0f} MW"
                f"  (share of hours still on the import plateau at S=3GW: "
                f"{plateau:.2f})"
            )
            for S in SGRID:
                nl = wd["lam_s"][S]
                dl = nl[mask] - lam[mask]
                # annual C3a move on rt_lw weights if applied in THIS set only
                dc3a = float((w * np.where(mask, nl - lam, 0.0)).sum() / w.sum())
                print(
                    f"     S={S:6.0f} MW: dlam mean {dl.mean():+7.2f}  "
                    f"(p50 {np.median(dl):+7.2f})  annual C3a move {dc3a:+.3f} $/MWh"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
