"""miso-144 SUPPLEMENTARY (post-hoc, labelled as such in the PREREG's terms):
does the SAME-UNIVERSE copperplate clear reproduce the keeper P1 price?

miso-143's G-A0 footing gate cleared the ALL-CLASS stack (nuclear + hydro +
import + biomass capability included) against the THERMAL_COLS requirement
(injected OTHER/biomass included) and under-priced the keeper by $8.7–12.8/MWh
— the gate FAILED and BRANCH-INSTRUMENT-FAIL fired.  miso-144's G-A1 measured
that subtraction's universe mismatch at ~97 % of the idle block.  This probe
completes the construction-error account from the price side, two-sided: if
the corrected clear still under-prices badly, part of the footing failure is
NOT the universe artifact and that is reported at magnitude.

Two variants, both at ``lo``/``hi`` offer brackets:

* **v1** — thermal-fleet stack vs fleet-thermal need (sidecar THERMAL_COLS
  minus the OTHER/biomass injections).
* **v2** — v1 with the physical reserve holding (rbdc ``held_mw``) ADDED to the
  need: the energy+reserve co-opt reserves held MW on the same stack, so the
  marginal energy unit sits higher by roughly the held MW below the margin.
  An upper-bias bracket, labelled, never averaged with v1.

Usage::

    .venv/bin/python scripts/probes/_miso144_footing_corrected.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso143_stack import (  # noqa: E402
    HOURS,
    KEEPER,
    THERMAL_COLS,
    YEARS,
    clear_many,
    fleet_state,
    hygiene,
    klass_of,
    markup_ceiling,
    sidecar_classes,
    sidecar_price,
    windows,
)
from _miso144_attribution import INJECTED, THERMAL_FLEET, reserve_held  # noqa: E402

OUT = REPO / "results/calibration/_miso144_footing_corrected.json"


def year_block(year: int) -> dict:
    st = fleet_state(year)
    gens, fa = st["fleet"], st["fleet_arrays"]
    mc0 = np.asarray(st["mc_base"], dtype=float)
    mk = markup_ceiling(gens, fa, st["config"])
    cap = fa.pmax[:, None] * fa.availability
    kl = klass_of(gens)
    thermal_rows = np.isin(kl, THERMAL_FLEET)

    piv = sidecar_classes(year)
    need_all = piv[list(THERMAL_COLS)].sum(axis=1).to_numpy(float)
    inj = sum(piv[c].to_numpy(float) for c in INJECTED)
    need_fleet = need_all - inj
    price, _den = sidecar_price(year)
    held, _dev = reserve_held(year)

    yr: dict = {}
    for wname, sel in windows().items():
        ok = sel & np.isfinite(price) & np.isfinite(need_all) & (need_all > 0)
        hrs = np.nonzero(ok)[0]
        blk: dict = {"n_hours": int(hrs.size)}
        for tag, off in (("lo", mc0), ("hi", mc0 + mk[:, None])):
            o = off[thermal_rows]
            c = cap[thermal_rows]
            row_block = {}
            for vname, need in (
                ("v1_thermal_need", need_fleet[hrs]),
                ("v2_plus_reserve", need_fleet[hrs] + held[hrs]),
            ):
                p_hat, _rows = clear_many(o, c, need, hrs)
                d = price[hrs] - p_hat  # positive = clear under-prices keeper
                row_block[vname] = {
                    "bias_mean": round(float(np.mean(d)), 3),
                    "median_abs_err": round(float(np.median(np.abs(d))), 3),
                    "r": round(float(np.corrcoef(p_hat, price[hrs])[0, 1]), 4),
                }
            blk[tag] = row_block
        yr[wname] = blk
    return yr


def main() -> None:
    hygiene()
    res = {
        "prereg": "results/calibration/PREREG-miso144-inmerit-idle-attribution-2026-08-08.md",
        "status": "SUPPLEMENTARY / POST-HOC -- not among the pre-registered "
        "predictions; two-sided completion of the construction-error account "
        "(the miso-143 footing bar 4.00 median|err| is carried for reference, "
        "not re-adjudicated)",
        "miso143_footing_reference": {
            "construction": "ALL-CLASS stack vs THERMAL_COLS need",
            "result": "median|err| 9.66-10.00, bias -10.6 to -10.9 (2025 JJA), FAIL",
        },
        "years": {},
    }
    for y in YEARS:
        res["years"][str(y)] = year_block(y)
    OUT.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
