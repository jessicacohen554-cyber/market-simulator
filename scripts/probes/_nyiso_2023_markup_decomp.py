"""NYISO 2023 P0-vs-P1 (base-MC vs startup-markup) decomposition probe.

Throwaway 2023-only diagnostic (rule 16): reproduces the keeper's 2023 solve
byte-faithfully (first year is warm-start-independent) and captures, via a
monkeypatch on the shared energy solve, the P0 base-cost prices, the P1
bid-cost prices, and the per-generator startup-amortization markup + base MC.
This isolates how much of the C3a 2023 level (+15.9%) is the startup markup
vs the base marginal cost. NOT registered; not a keeper.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import scripts.replay_keeper as rk  # noqa: E402
import scripts.run_calibration as rc  # noqa: E402
import scripts.run_calibration_full as rcf  # noqa: E402
from market_sim.pipeline.solve import run_energy_solve as _orig_solve  # noqa: E402

BUNDLE = "results/calibration/nyiso70_scr_edrp_reserve"
OUT_NPZ = "/tmp/nyiso_2023_markup_decomp.npz"
_CAP = {}


def _capturing_solve(fleet, fleet_arrays, demand, mc_base, dispatch_kwargs, config,
                     **kw):
    res = _orig_solve(fleet, fleet_arrays, demand, mc_base, dispatch_kwargs, config,
                      **kw)
    # Only capture the first (2023) solve.
    if _CAP:
        return res
    pg = np.array([getattr(g, "plant_group", "?") for g in fleet])
    ft = np.array([getattr(g, "fuel_type", "?") for g in fleet])
    markup = np.asarray(res.markup)          # (n_gen, T)
    mc_bid = np.asarray(res.mc_bid)          # (n_gen, T)
    p1_disp = np.asarray(res.p1.dispatch)    # (n_gen, T)
    mc_base_a = np.asarray(mc_base)          # (n_gen, T)
    # Aggregate per class × month to keep the npz small.
    T = markup.shape[1]
    hpm = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    moh = np.repeat(np.arange(1, 13), [h * 24 for h in hpm])[:T]
    classes = sorted(set(pg.tolist()))
    n_c = len(classes)
    wmarkup = np.full((n_c, 12), np.nan)   # dispatch-weighted mean markup
    wbase = np.full((n_c, 12), np.nan)     # dispatch-weighted mean base MC
    wbid = np.full((n_c, 12), np.nan)      # dispatch-weighted mean bid MC
    twh = np.zeros((n_c, 12))              # MWh dispatched
    for ci, c in enumerate(classes):
        rows = np.where(pg == c)[0]
        if len(rows) == 0:
            continue
        d = p1_disp[rows]           # (k, T)
        mk = markup[rows]
        bs = mc_base_a[rows]
        bd = mc_bid[rows]
        for mo in range(1, 13):
            sel = moh == mo
            w = d[:, sel]
            wsum = w.sum()
            twh[ci, mo - 1] = wsum / 1000.0
            if wsum > 0:
                wmarkup[ci, mo - 1] = float((mk[:, sel] * w).sum() / wsum)
                wbase[ci, mo - 1] = float((bs[:, sel] * w).sum() / wsum)
                wbid[ci, mo - 1] = float((bd[:, sel] * w).sum() / wsum)
    np.savez_compressed(
        OUT_NPZ,
        p0_prices=np.asarray(res.r0.prices),
        p1_prices=np.asarray(res.p1.prices),
        demand=np.asarray(demand),
        classes=np.array(classes),
        wmarkup=wmarkup,
        wbase=wbase,
        wbid=wbid,
        twh=twh,
        # per-gen arrays for exact per-hour marginal-unit identification
        pg=pg,
        ft=ft,
        mc_base_gen=mc_base_a.astype(np.float32),
        p0_disp=np.asarray(res.r0.dispatch).astype(np.float32),
        pmax=np.asarray(fleet_arrays.pmax).astype(np.float32),
        heat_rate=np.asarray(fleet_arrays.heat_rate).astype(np.float32),
        availability=np.asarray(fleet_arrays.availability).astype(np.float32),
        vom=np.asarray(fleet_arrays.vom).astype(np.float32),
        emission_rate=np.asarray(fleet_arrays.emission_rate).astype(np.float32),
        unit_ids=np.asarray(fleet_arrays.unit_ids),
    )
    _CAP["done"] = True
    print(f"[probe] captured decomposition -> {OUT_NPZ}", flush=True)
    return res


def main():
    rc.run_energy_solve = _capturing_solve  # module-global lookup in run_year
    meta = json.loads((Path(BUNDLE) / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [2023]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(
        "/tmp/nyiso2023_decomp_throwaway"
    )
    kwargs["note"] = "THROWAWAY 2023 markup-decomposition diagnostic probe"
    print(f"[probe] solving NYISO 2023 (decomp) ...", flush=True)
    rcf.solve_and_persist(**kwargs)
    print("[probe] done.", flush=True)


if __name__ == "__main__":
    main()
