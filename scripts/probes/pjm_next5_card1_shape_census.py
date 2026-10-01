"""PJM-NEXT-5 card 1 zero-LP census — the shape-on-own-cost form vs the keeper. ZERO LP.

Fleet-only rebuild of the keeper recipe; the mid-curve markup is built twice with
the model's own builder — as recorded (floor form) and with
``pjm_offer_midcurve_shape_segments=("CC_LIKE",)`` in a local config copy — and
the cap-weighted CC_REGULAR econ bid (``mc_base + markup``, ex startup
amortization) is reported by rung and by zone, beside COAL_BIT econ.

Run: ``python3 scripts/probes/pjm_next5_card1_shape_census.py 2019 ... 2025``
Writes ``results/phase0/pjm/_pjm_next5_card1_shape_census.json``.
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


def main() -> None:
    """Census the shape form per requested year."""
    logging.disable(logging.CRITICAL)
    from market_sim.data.fleet.offer_surfaces import (
        build_pjm_offer_midcurve_conditional_markup,
    )
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    out: dict = {"what": __doc__.splitlines()[0], "years": {}}
    for y in [int(a) for a in sys.argv[1:]] or list(range(2019, 2026)):
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(BUNDLE, y))
        kw["pjm_da_virtual_bids"] = False
        r = run_year(y, "PJM", 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)
        cfg, fleet, fa = r["config"], r["fleet"], r["fleet_arrays"]
        zn = list(r["iso_config"].zone_names)
        mc = np.asarray(r["mc_base"], float)
        net = np.asarray(
            r["demand"].sum(0)
            - (r["solar_cap"][:, None] * r["solar_cf"]).sum(0)
            - (r["wind_cap"][:, None] * r["wind_cf"]).sum(0),
            float,
        )
        k = build_pjm_offer_midcurve_conditional_markup(fa, fleet, mc, net, cfg, y)
        cs = cfg.with_overrides(pjm_offer_midcurve_shape_segments=("CC_LIKE",))
        a = build_pjm_offer_midcurve_conditional_markup(fa, fleet, mc, net, cs, y)
        k = np.zeros_like(mc) if k is None else k
        a = np.zeros_like(mc) if a is None else a
        cls = np.asarray(fa.plant_group).astype(str)
        tr = np.array([u.rpartition("_")[2] for u in fa.unit_ids])
        zone = np.array([zn[i] for i in np.asarray(fa.zone_idx, int)])
        av = np.asarray(fa.availability, float)
        av = av if av.ndim == 2 else av[:, None] * np.ones((1, mc.shape[1]))
        w = np.asarray(fa.pmax, float)[:, None] * av

        def cw(sel: np.ndarray, arr: np.ndarray) -> float:
            """Cap-weighted mean of ``arr`` over rows ``sel``."""
            return float((arr[sel] * w[sel]).sum() / max(w[sel].sum(), 1e-9))

        cce = (cls == "CC_REGULAR") & np.char.startswith(tr, "econ")
        coal = (cls == "COAL_BIT") & np.char.startswith(tr, "econ")
        other = ~(cls == "CC_REGULAR")
        yr = {
            "cc_econ_keeper": cw(cce, mc + k),
            "cc_econ_shape": cw(cce, mc + a),
            "coal_econ_keeper": cw(coal, mc + k),
            "non_cc_rows_byte_identical": bool(np.array_equal(k[other], a[other])),
            "by_rung": {
                t: [round(cw(cce & (tr == t), mc + k), 2), round(cw(cce & (tr == t), mc + a), 2)]
                for t in sorted(set(tr[cce]))
            },
            "by_zone": {
                z: [round(cw(cce & (zone == z), mc + k), 2), round(cw(cce & (zone == z), mc + a), 2)]
                for z in sorted(set(zone[cce]))
            },
        }
        out["years"][str(y)] = yr
        print(y, json.dumps(yr), flush=True)
    dest = REPO / "results/phase0/pjm/_pjm_next5_card1_shape_census.json"
    dest.write_text(json.dumps(out, indent=1))
    print("wrote", dest)


if __name__ == "__main__":
    main()
