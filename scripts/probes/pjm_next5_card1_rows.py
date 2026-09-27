"""PJM-NEXT-5 card 1 — per-row CC_REGULAR dump (ZERO LP) for the operand read.

Writes one parquet per year: every CC_REGULAR row's unit id, plant, tranche,
pmax, heat rate, VOM, NOx/CO2 rates, and its availability-weighted mean
delivered fuel, mc_base and measured CC_LIKE target (surface helpers).
Run: ``python3 scripts/probes/pjm_next5_card1_rows.py 2019 2024``.
"""
from __future__ import annotations
import json, logging, sys
from pathlib import Path
import numpy as np, pandas as pd
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src"))
BUNDLE = REPO / "results/calibration/pjmnext4_c1_span"


def main() -> None:
    """Dump CC_REGULAR rows per requested year."""
    logging.disable(logging.CRITICAL)
    from market_sim.data.fleet.offer_surfaces import _pjm_midcurve_context, _pjm_midcurve_row_target
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year
    meta = json.loads((BUNDLE / "meta.json").read_text())
    for y in [int(a) for a in sys.argv[1:]]:
        kw = run_year_kwargs(meta); kw.update(derived_run_year_inputs(BUNDLE, y)); kw["pjm_da_virtual_bids"] = False
        r = run_year(y, "PJM", 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)
        cfg, fleet, fa = r["config"], r["fleet"], r["fleet_arrays"]
        zn = list(r["iso_config"].zone_names)
        mc = np.asarray(r["mc_base"], float); T = mc.shape[1]
        fuel = np.asarray(r["fuel_prices"], float)
        fuel = fuel if fuel.ndim == 2 else fuel[:, None] * np.ones((1, T))
        net = np.asarray(r["demand"].sum(0) - (r["solar_cap"][:, None] * r["solar_cf"]).sum(0) - (r["wind_cap"][:, None] * r["wind_cf"]).sum(0), float)
        ctx = _pjm_midcurve_context(fa, fleet, mc, net, cfg, y, {"CC_LIKE"})
        share = {g: s for g, s, sfx, seg in ctx.rows}
        av = np.asarray(fa.availability, float); av = av if av.ndim == 2 else av[:, None] * np.ones((1, T))
        cls = np.asarray(fa.plant_group).astype(str)
        rows = []
        for g in np.where(cls == "CC_REGULAR")[0]:
            w = av[g]; W = max(w.sum(), 1e-9)
            tgt = _pjm_midcurve_row_target(ctx, "CC_LIKE", share[g]) if g in share else np.full(T, np.nan)
            m = np.isfinite(tgt)
            rows.append(dict(unit_id=fa.unit_ids[g], plant_code=int(fa.plant_code[g]), zone=zn[int(fa.zone_idx[g])],
                             state=str(fa.state[g]) if fa.state is not None else "", tranche=fa.unit_ids[g].rpartition("_")[2],
                             pmax=float(fa.pmax[g]), hr=float(fa.heat_rate[g]), vom=float(fa.vom[g]),
                             co2=float(fa.emission_rate[g]), nox=float(fa.nox_rate[g]), share=share.get(g, np.nan),
                             fuel=float((fuel[g] * w).sum() / W), mc=float((mc[g] * w).sum() / W),
                             target=float((tgt[m] * w[m]).sum() / max(w[m].sum(), 1e-9)) if m.any() else np.nan,
                             avail=float(w.mean())))
        df = pd.DataFrame(rows)
        dest = REPO / f"results/calibration/_pjm_next5_card1_rows_{y}.parquet"
        df.to_parquet(dest); print("wrote", dest, len(df), flush=True)


if __name__ == "__main__":
    main()
