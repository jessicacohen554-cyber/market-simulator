"""PJM-NEXT-5 card 1 phase 0 — the model's CC econ bid against PJM's measured CC_LIKE offers. ZERO LP.

Rule 32 ``[R-SHARD]`` (a): the parent runs no LP. For each year a ``fleet_only``
rebuild of the keeper recipe (``pjmnext4_c1_span``, through the sanctioned
``replay_keeper.run_year_kwargs``) supplies the SAME ``mc_base`` and per-unit
delivered ``fuel_prices`` the LP solved on. For every CC econ tranche row the
measured target is read with the model's OWN surface helpers
(``_pjm_midcurve_context`` / ``_pjm_midcurve_row_target``) at the row's own
within-plant share:

    target[g, t] = mult(CC_LIKE, year, bin(t), share_g) x gas_day(t)
    gas_day(t)   = Henry Hub daily + GAS_BASIS_DIFFERENTIAL["PJM"]

so the bid-minus-measured gap decomposes EXACTLY into named operands:

    mc_base - target = HR x (fuel - gas_day)         [delivered-gas basis]
                     + gas_day x (HR - mult)          [heat rate vs implied]
                     + VOM
                     + (mc_base - HR x fuel - VOM)    [carbon (RGGI) + NOx + overlays]

Weights are ``pmax x availability`` over hours with a finite target.

STATED LIMITS: (1) the P1 bid also carries the startup amortization, which
needs the P0 dispatch (an LP) — every bid here is ``mc_base`` and the gap is a
LOWER bound on the P1 gap; (2) the measured CC_LIKE ladder is PJM-wide (the
DataMiner offers are masked, no location), so a "zone above measured" reading
compares a zone against the RTO-wide measured distribution, never against a
zonal measured offer; (3) net load is demand minus wind/solar potential
(pjm-h17's construction), not LP-served net load.

Run: ``python3 scripts/probes/pjm_next5_card1_cc_phase0.py 2019 2020 2021 2022 2023 2024 2025``
Writes ``results/phase0/pjm/_pjm_next5_card1_cc_phase0.json``.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/pjmnext4_c1_span"
CLASSES = ("CC_REGULAR", "CC_CHP", "COAL_BIT")


def _wavg(x: np.ndarray, w: np.ndarray) -> float:
    """Weighted mean, NaN-safe on ``x``."""
    m = np.isfinite(x) & (w > 0)
    return float((x[m] * w[m]).sum() / max(w[m].sum(), 1e-9))


def main() -> None:
    """Run the card-1 phase 0 for the requested years and write the JSON."""
    logging.disable(logging.CRITICAL)
    from market_sim.data.fleet.offer_surfaces import (
        _pjm_midcurve_context,
        _pjm_midcurve_row_target,
    )
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    out: dict = {"what": __doc__.splitlines()[0], "bundle": str(BUNDLE.name), "years": {}}
    for y in [int(a) for a in sys.argv[1:]] or [2019, 2020, 2021, 2022, 2023, 2024, 2025]:
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(BUNDLE, y))
        kw["pjm_da_virtual_bids"] = False  # demand-side overlay, inert for offers (pjm-h8 §2)
        r = run_year(y, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)
        cfg, fleet, fa = r["config"], r["fleet"], r["fleet_arrays"]
        zn = list(r["iso_config"].zone_names)
        mc = np.asarray(r["mc_base"], float)
        T = mc.shape[1]
        fuel = np.asarray(r["fuel_prices"], float)
        if fuel.ndim == 1:
            fuel = fuel[:, None] * np.ones((1, T))
        net = np.asarray(
            r["demand"].sum(axis=0)
            - (r["solar_cap"][:, None] * r["solar_cf"]).sum(axis=0)
            - (r["wind_cap"][:, None] * r["wind_cf"]).sum(axis=0),
            float,
        )
        ctx = _pjm_midcurve_context(fa, fleet, mc, net, cfg, y, {"CC_LIKE", "LONG_RUN"})
        hr = np.asarray(fa.heat_rate, float)
        vom = np.asarray(fa.vom, float)
        cls = np.asarray(fa.plant_group).astype(str)
        st = np.asarray(fa.state).astype(str) if fa.state is not None else np.full(len(cls), "?")
        zone = np.array([zn[i] for i in np.asarray(fa.zone_idx, int)])
        avail = np.asarray(fa.availability, float)
        if avail.ndim == 1:
            avail = avail[:, None] * np.ones((1, T))
        av = np.asarray(fa.pmax, float)[:, None] * avail

        seg_of = {"CC_REGULAR": "CC_LIKE", "CC_CHP": "CC_LIKE", "COAL_BIT": "LONG_RUN"}
        recs = []
        for g, s_g, sfx, seg in ctx.rows:
            if cls[g] not in CLASSES or not sfx.startswith("econ") or seg not in ctx.tables:
                continue
            if seg != seg_of[cls[g]]:
                continue
            tgt = _pjm_midcurve_row_target(ctx, seg, s_g)
            mult = tgt / ctx.gas_day
            recs.append((g, s_g, sfx, tgt, mult))

        yr: dict = {"year_table": sorted(ctx.year_tables), "classes": {}}
        for c in CLASSES:
            rows = [rc for rc in recs if cls[rc[0]] == c]
            if not rows:
                continue
            G = np.array([rc[0] for rc in rows])
            TG = np.vstack([rc[3] for rc in rows])
            MU = np.vstack([rc[4] for rc in rows])
            W = av[G] * np.isfinite(TG)
            gd = ctx.gas_day[None, :]
            basis = hr[G][:, None] * (fuel[G] - gd)
            hrop = gd * (hr[G][:, None] - MU)
            vomop = np.broadcast_to(vom[G][:, None], TG.shape)
            other = mc[G] - hr[G][:, None] * fuel[G] - vom[G][:, None]
            gap = mc[G] - TG

            def summ(sel: np.ndarray) -> dict:
                """Cap-weighted operand summary over the row subset ``sel``."""
                w = W[sel]
                return {
                    "gw": float(np.asarray(fa.pmax, float)[G][sel].sum() / 1e3),
                    "fuel": _wavg(fuel[G][sel], w),
                    "gas_day": _wavg(np.broadcast_to(gd, TG.shape)[sel], w),
                    "hr": _wavg(np.broadcast_to(hr[G][:, None], TG.shape)[sel], w),
                    "mult_implied_hr": _wavg(MU[sel], w),
                    "mc_base": _wavg(mc[G][sel], w),
                    "measured": _wavg(TG[sel], w),
                    "gap": _wavg(gap[sel], w),
                    "op_basis": _wavg(basis[sel], w),
                    "op_heat_rate": _wavg(hrop[sel], w),
                    "op_vom": _wavg(vomop[sel], w),
                    "op_carbon_other": _wavg(other[sel], w),
                    "above_measured_share": float((w * (gap[sel] > 0)).sum() / max(w.sum(), 1e-9)),
                }

            allsel = np.ones(len(G), bool)
            cd = {"all": summ(allsel), "by_zone": {}, "by_state": {}}
            for z in np.unique(zone[G]):
                cd["by_zone"][z] = summ(zone[G] == z)
            for s in np.unique(st[G]):
                sel = st[G] == s
                if np.asarray(fa.pmax, float)[G][sel].sum() >= 500:
                    cd["by_state"][s] = summ(sel)
            yr["classes"][c] = cd
        out["years"][str(y)] = yr
        a = yr["classes"].get("CC_REGULAR", {}).get("all", {})
        b = yr["classes"].get("COAL_BIT", {}).get("all", {})
        print(y, "CC", {k: round(v, 2) for k, v in a.items()}, "\n     COAL", {k: round(v, 2) for k, v in b.items()}, flush=True)
    dest = REPO / "results/phase0/pjm/_pjm_next5_card1_cc_phase0.json"
    dest.write_text(json.dumps(out, indent=1))
    print("wrote", dest)


if __name__ == "__main__":
    main()
