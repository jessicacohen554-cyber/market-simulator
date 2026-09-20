"""pjm-h12 card D-3 PHASE 0 — footprint census for mustrun_commitment_feasibility_clip on PJM.

ZERO LP (rule 32 ``[R-SHARD]`` (a), and rule 29 ``[R-SCREEN]`` clause (0) as
practice): rebuilds the PJM keeper pair's fleet via ``run_year(fleet_only=True)``
from each bundle's own ``meta.json``, then applies the clip's OWN test
(``src/market_sim/data/fleet/arrays.py`` ~3417) verbatim to count what it would
release. Nothing is solved and nothing is armed.

The clip's level operand ``cc_mustrun_pmin_mw`` is not carried on ``FleetArrays``,
so the census uses the identity the mechanism's own docstring states -- "the
committed tranche's ``cc_mustrun_pmin_mw`` IS its own ``pmax``" -- over the rows
carrying ``MECH_CC_MUSTRUN_PER_PLANT`` / ``MECH_ST_GAS_MUSTRUN_PER_PLANT``.
Gate G2 of ``docs/handoffs/PRECOMMIT-pjm-h12-2026-09-20.md`` checks this offline
census against the armed solver's own log line, so the identity is verified
rather than assumed.

Usage::

    uv run python scripts/probes/pjm_h12_clip_census.py
"""

import logging
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, ".")
sys.path.insert(0, "scripts")
logging.basicConfig(level=logging.ERROR)
from scripts.legitimacy_diagnostics import _rebuild_fleet_arrays
from market_sim.data.fleet.arrays import (
    MECH_CC_MUSTRUN_PER_PLANT as CC,
    MECH_ST_GAS_MUSTRUN_PER_PLANT as ST,
)

BUN = {
    2020: "pjm_h11_touchpoint_span",
    2021: "pjm_h11_touchpoint_span",
    2022: "pjm_h11_touchpoint_span",
    2023: "pjm_h11_keeper_span",
    2024: "pjm_h11_keeper_span",
    2025: "pjm_h11_keeper_span",
}
print("mustrun_commitment_feasibility_clip -- PJM footprint census (ZERO LP)")
print(
    "identity used: the committed tranche's cc_mustrun_pmin_mw IS its own pmax (arrays.py docstring)"
)
print(
    f"{'yr':5} {'groups':>7} {'infeas grp':>11} {'infeas hrs':>11} {'RELEASED TWh':>13} {'of floor TWh':>13} {'%':>7}"
)
for y in sorted(BUN):
    fa = _rebuild_fleet_arrays(Path("results/calibration") / BUN[y], "PJM", y)
    mech = np.asarray(fa.min_gen_mechanism)
    mg = np.asarray(fa.min_gen, dtype=float)
    pmax = np.asarray(fa.pmax, dtype=float)
    av = np.asarray(fa.availability, dtype=float)
    pc = np.asarray(fa.plant_code)
    pg = np.asarray(fa.plant_group)
    own_any = np.isin(mech, (CC, ST)).any(axis=1)  # committed-tranche rows
    keys = [(int(pc[i]), str(pg[i])) for i in range(len(pmax))]
    lvl = {}
    rows = {}
    for i, k in enumerate(keys):
        rows.setdefault(k, []).append(i)
        if own_any[i]:
            lvl[k] = lvl.get(k, 0.0) + float(pmax[i])
    nbadh = 0
    nbadg = 0
    rel = 0.0
    for k, lv in lvl.items():
        r = np.asarray(rows[k], dtype=int)
        cap = (pmax[r][:, None] * av[r, :]).sum(axis=0)
        bad = cap < lv - 1e-9
        if not bad.any():
            continue
        nbadg += 1
        nbadh += int(bad.sum())
        c = np.flatnonzero(bad)
        blk = mg[np.ix_(r, c)]
        ow = np.isin(mech[np.ix_(r, c)], (CC, ST))
        rel += float(blk[ow].sum())
    tot = float(mg[np.isin(mech, (CC, ST))].sum())
    print(
        f"{y:5} {len(lvl):7d} {nbadg:11d} {nbadh:11d} {rel / 1e6:13.4f} {tot / 1e6:13.4f} {100 * rel / tot if tot else 0:6.2f}%"
    )
