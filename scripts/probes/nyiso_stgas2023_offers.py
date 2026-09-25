"""NYISO-STGAS-2023 phase 0b (zero LP): the ST_GAS offer stack against the NYC price.

Fleet-only rebuild of the keeper recipe (``replay_keeper.run_year_kwargs`` ->
``run_calibration.run_year(fleet_only=True)``, the sanctioned path) per year. For every
ST_GAS plant it records the MW-weighted offer (``mc_base``, the assembled P0 objective the
LP solved on) per tranche, availability, min-gen floor MW by mechanism, and compares the
plant's offer against the keeper's committed hourly zonal price (``hourly/system_<y>``) and
the measured NYISO RT zonal price (clean ``lmp``). Writes
``results/calibration/_nyiso_stgas2023_offers.json``.

2021 inputs (``results/calibration/rnyiso_2021``, run payload ``2026-09-25-nyiso-r-inputs-2021``
and ``bench/NYISO/2021.json.gz``) come from R-NYISO-2021's branch head
``8671806374d1c08a945f497769b65783cc2fc70e`` (PR #6636, closed unmerged); check them out from
that SHA to re-run 2021. They are not on ``main``.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLES = {2021: "results/calibration/rnyiso_2021"}
DEFAULT_BUNDLE = "results/calibration/rnyiso_span"


def build(year: int, arm: bool = False) -> dict:
    """Rebuild one year and summarise the ST_GAS offers (``arm``: the LDC leg on)."""
    from scripts.replay_keeper import run_year_kwargs
    from scripts.run_calibration import run_year
    from scripts import run_calibration_full as rcf

    bdir = REPO / BUNDLES.get(year, DEFAULT_BUNDLE)
    meta = json.loads((bdir / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    if arm:
        prb = dict(kw.get("prb_overrides") or {})
        prb["nyiso_ldc_generator_delivered_gas"] = True
        kw["prb_overrides"] = prb
    ref = rcf._load_reference()
    gp = rcf._henry_hub_actual(ref, year)
    b = run_year(year, meta["iso"], 8760, gp, {}, fleet_only=True, **kw)
    assert bool(getattr(b["config"], "nyiso_ldc_generator_delivered_gas", False)) == arm
    fa = b["fleet_arrays"]
    mc = np.asarray(b["mc_base"])
    zones = list(b["iso_config"].zone_names)
    T = 8760
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], T, axis=1)
    pg = np.asarray(fa.plant_group).astype(str)
    av = np.asarray(fa.availability)
    if av.ndim == 1:
        av = np.repeat(av[:, None], T, axis=1)
    mg = None if fa.min_gen is None else np.asarray(fa.min_gen)
    mech = None if fa.min_gen_mechanism is None else np.asarray(fa.min_gen_mechanism)
    sysd = pd.read_parquet(bdir / f"hourly/system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    mprice = {
        z: g.sort_values("hour")["price"].to_numpy() for z, g in sysd.groupby("zone")
    }
    out = {
        "shapes": {
            "mc": list(mc.shape),
            "avail": list(av.shape),
            "min_gen": None if mg is None else list(mg.shape),
        },
        "hh": gp,
        "plants": {},
    }
    idx = np.where(pg == "ST_GAS")[0]
    by_plant = defaultdict(list)
    for i in idx:
        by_plant[int(fa.plant_code[i])].append(i)
    for pc, ii in by_plant.items():
        ii = np.array(ii)
        z = zones[int(fa.zone_idx[ii[0]])]
        cap = fa.pmax[ii][:, None] * av[ii]
        wmc = (mc[ii] * cap).sum(0) / np.maximum(cap.sum(0), 1e-9)
        mp = mprice.get(z)
        rec = {
            "zone": z,
            "n_tranches": int(ii.size),
            "unit_ids": [fa.unit_ids[i] for i in ii],
            "pmax_mw": round(float(fa.pmax[ii].sum()), 1),
            "tranche_pmax": [round(float(x), 1) for x in fa.pmax[ii]],
            "tranche_hr": [round(float(x), 3) for x in fa.heat_rate[ii]],
            "tranche_mc_mean": [round(float(x), 2) for x in mc[ii].mean(1)],
            "avail_mean": round(
                float((fa.pmax[ii][:, None] * av[ii]).sum() / (fa.pmax[ii].sum() * T)),
                4,
            ),
            "avail_mon": [
                round(float(x), 3)
                for x in pd.Series(
                    (fa.pmax[ii][:, None] * av[ii]).sum(0) / fa.pmax[ii].sum(),
                    index=pd.date_range(f"{year}-01-01", periods=T, freq="h"),
                )
                .resample("MS")
                .mean()
            ],
            "offer_mean": round(float(np.nanmean(wmc)), 2),
            "offer_min_tranche_mon": [
                round(float(x), 2)
                for x in pd.Series(
                    mc[ii].min(0),
                    index=pd.date_range(f"{year}-01-01", periods=T, freq="h"),
                )
                .resample("MS")
                .mean()
            ],
        }
        if mg is not None:
            fl = mg[ii] if mg.ndim == 2 else np.repeat(mg[ii][:, None], T, axis=1)
            rec["floor_mwh_twh"] = round(float(fl.sum()) / 1e6, 4)
            if mech is not None:
                ms = defaultdict(float)
                mm = (
                    mech[ii]
                    if mech.ndim == 2
                    else np.repeat(mech[ii][:, None], T, axis=1)
                )
                for m, v in zip(mm.ravel(), fl.ravel()):
                    if v > 0:
                        ms[str(m)] += float(v)
                rec["floor_by_mech_twh"] = {k: round(v / 1e6, 4) for k, v in ms.items()}
        if mp is not None:
            cheapest = mc[ii].min(0)
            rec["model_zone_price_mean"] = round(float(mp.mean()), 2)
            rec["hours_cheapest_tranche_below_model_price"] = int((cheapest < mp).sum())
            rec["hours_weighted_offer_below_model_price"] = int((wmc < mp).sum())
        out["plants"][pc] = rec
    # CC_REGULAR / CT marginal band in the same zones, for context
    for cls in ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP"):
        ii = np.where(pg == cls)[0]
        if ii.size:
            w = fa.pmax[ii]
            out.setdefault("class_offer", {})[cls] = {
                "mw": round(float(w.sum()), 1),
                "mw_weighted_mc": round(float((mc[ii].mean(1) * w).sum() / w.sum()), 2),
                "mw_weighted_hr": round(
                    float((fa.heat_rate[ii] * w).sum() / w.sum()), 3
                ),
            }
            for z in ("NYC", "Long_Island", "Capital_Hudson"):
                jj = [i for i in ii if zones[int(fa.zone_idx[i])] == z]
                if jj:
                    w2 = fa.pmax[jj]
                    out["class_offer"][cls][z] = {
                        "mw": round(float(w2.sum()), 1),
                        "mc": round(float((mc[jj].mean(1) * w2).sum() / w2.sum()), 2),
                        "hr": round(float((fa.heat_rate[jj] * w2).sum() / w2.sum()), 3),
                    }
    return out


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--years", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025]
    )
    ap.add_argument(
        "--out", default=str(REPO / "results/calibration/_nyiso_stgas2023_offers.json")
    )
    ap.add_argument(
        "--arm", action="store_true", help="arm nyiso_ldc_generator_delivered_gas"
    )
    a = ap.parse_args()
    logging.basicConfig(level=logging.WARNING)
    p = Path(a.out)
    res = json.loads(p.read_text()) if p.exists() else {}
    for y in a.years:
        res[str(y)] = build(y, a.arm)
        p.write_text(json.dumps(res, indent=1, default=str))
        r = res[str(y)]
        print(y, "HH", r["hh"], r["shapes"], flush=True)
        print("  class", r.get("class_offer"), flush=True)
        for pc in (2500, 8906, 2490, 2516, 2511, 2625, 8006):
            if pc in r["plants"]:
                q = r["plants"][pc]
                print(
                    f"  {pc} {q['zone']} mw={q['pmax_mw']} hr={q['tranche_hr']} mc={q['tranche_mc_mean']} "
                    f"avail={q['avail_mean']} floor={q.get('floor_by_mech_twh')} "
                    f"hrs<price={q.get('hours_cheapest_tranche_below_model_price')}/{q.get('hours_weighted_offer_below_model_price')} "
                    f"zp={q.get('model_zone_price_mean')}",
                    flush=True,
                )
                print("     avail_mon", q["avail_mon"], flush=True)


if __name__ == "__main__":
    main()
