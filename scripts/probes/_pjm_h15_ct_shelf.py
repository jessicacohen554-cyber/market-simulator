"""pjm-h15 phase 0, part 2 — the CT_FAST shelf against PJM's OWN offers. ZERO LP.

Rule 29 ``[R-SCREEN]`` clause 0, rule 32 ``[R-SHARD]`` (a): the parent runs no LP.

Part 1 (``_pjm_h15_top_of_stack.py``) refuted the lane's proposed TOP-of-curve
lever on three grounds and located the idle block: in the market's top-1 %
hours the keeper's CC is 93.6-95.6 % loaded and its coal 82.5-98.5 %, while
**CT_PEAKER runs at 36.5 / 52.4 / 65.8 %** with 13.6 / 10.3 / 7.4 GW still
available above the clearing point.

This measures what PJM's OWN published offers say that same shelf should bid.
The keeper arms ``pjm_offer_midcurve_segments = ('LONG_RUN', 'CC_LIKE')``, so
CT_FAST is out of the measured surface's scope entirely — the pjm-103 rule-19
decision that ``tranche_startup_amortization`` owns the CT stack. The target
here is built by the model's OWN
``build_pjm_ct_measured_max_target`` (``pjm_ct_measured_max_reprice``, default
off, armed in ZERO bundles), so it is byte-for-byte the level that mechanism
would apply.

STATED LIMIT, not buried: the reported lift is an **UPPER BOUND**. It is taken
against ``mc_base`` (the P0 base cost), whereas the mechanism applies
``max(bid, target)`` at the ``p1_bid_max_target`` seam AFTER the startup
amortization, which already raises CT bids and absorbs an unmeasured part of
it. The number is a footprint, NEVER a predicted price effect.

Nothing is swept and no parameter is constructed (rules 1 ``[R-STRUCT]`` /
21 ``[R-DOF]``).

Run: ``python3 scripts/probes/_pjm_h15_ct_shelf.py 2023 2024 2025``
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/pjm_h14_coalmustrun_span"


def main() -> None:
    logging.disable(logging.CRITICAL)
    from market_sim.data.fleet.offer_surfaces import build_pjm_ct_measured_max_target
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
    act = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
    )
    out: dict = {"what": __doc__.splitlines()[0], "years": {}}

    meta = json.loads((BUNDLE / "meta.json").read_text())
    for y in years:
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(BUNDLE, y))
        kw["pjm_da_virtual_bids"] = False  # declared simplification, pjm-h8 §2
        res = run_year(
            y, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
        cfg, fleet, fa = res["config"], res["fleet"], res["fleet_arrays"]
        mc = np.asarray(res["mc_base"], float)
        if mc.ndim == 1:
            mc = mc[:, None] * np.ones((1, 8760))
        net = (
            res["demand"].sum(axis=0)
            - (res["solar_cap"][:, None] * res["solar_cf"]).sum(axis=0)
            - (res["wind_cap"][:, None] * res["wind_cf"]).sum(axis=0)
        )
        # The mechanism's own target, built with its own gate flipped on. The
        # flip lives ONLY in this probe's local config copy — nothing is armed.
        cfg_on = cfg.with_overrides(pjm_ct_measured_max_reprice=True)
        tgt = build_pjm_ct_measured_max_target(
            fa, fleet, mc, np.asarray(net, float), cfg_on, y
        )
        if tgt is None:
            out["years"][str(y)] = {"error": "no measured CT target resolved"}
            continue

        pmax = np.asarray(fa.pmax, float)
        avail = np.asarray(fa.availability, float)
        if avail.ndim == 1:
            avail = avail[:, None] * np.ones((1, mc.shape[1]))
        a = act[act.year == y].sort_values("hour")["rt"].to_numpy(float)
        hi = np.argsort(a)[-88:]  # the market's top-1 % hours, the lane's window

        rows = np.where(tgt.any(axis=1))[0]
        av_cap = pmax[:, None] * avail
        w = av_cap[rows][:, hi]
        base = mc[rows][:, hi]
        meas = tgt[rows][:, hi]
        lift = np.maximum(0.0, meas - base)  # UPPER BOUND — see the docstring
        tot = w.sum()
        out["years"][str(y)] = {
            "n_ct_rows_priced": int(rows.size),
            "ct_mw_priced": float(pmax[rows].sum()),
            "market_top1pct_mean_lmp": float(a[hi].mean()),
            "tight_hours_mc_base_capwtd": float((base * w).sum() / tot),
            "tight_hours_measured_capwtd": float((meas * w).sum() / tot),
            "tight_hours_upper_bound_lift_capwtd": float((lift * w).sum() / tot),
            "share_of_ct_mwh_where_measured_exceeds_mc_base": float(
                (w * (meas > base)).sum() / tot
            ),
        }
        print(f"[{y}] done", flush=True)

    hdr = f"{'yr':<6}{'CT rows':>9}{'CT MW':>9}{'mc_base':>10}{'measured':>10}"
    print("\n" + hdr + f"{'UB lift':>9}{'%MWh bind':>11}")
    for y, r in out["years"].items():
        if "error" in r:
            print(f"{y:<6} {r['error']}")
            continue
        print(
            f"{y:<6}{r['n_ct_rows_priced']:>9}{r['ct_mw_priced']:>9.0f}"
            f"{r['tight_hours_mc_base_capwtd']:>10.1f}"
            f"{r['tight_hours_measured_capwtd']:>10.1f}"
            f"{r['tight_hours_upper_bound_lift_capwtd']:>9.1f}"
            f"{100 * r['share_of_ct_mwh_where_measured_exceeds_mc_base']:>10.0f}%"
        )
    dest = REPO / "results/calibration/_pjm_h15_ct_shelf.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
