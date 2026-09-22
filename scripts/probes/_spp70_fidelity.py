"""SPP-70 — is the HEAD reconstruction the KEEPER's stack?  (rule 29(b) G-DRIFT, form 4)

The keeper solved at ``40eeb43a``; this lane reconstructs at HEAD, and fourteen
solve-path files changed in between.  A code-level classification is one answer;
this is the empirical one, and it is stronger: the reconstructed fleet must be
able to have produced the bundle's COMMITTED dispatch.  Per class and hour, the
committed ``class_hourly`` MW must not exceed the reconstructed available MW
(``pmax * availability``).  A drift in binning, availability, derates or the
fleet vintage shows up here immediately.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

BUNDLES = {
    2019: "spp67_yearown_rung",
    2020: "spp67_yearown_rung",
    2021: "spp67_yearown_rung",
    2022: "spp67_yearown_rung",
    2023: "spp67_yearown_span",
    2024: "spp67_yearown_span",
    2025: "spp67_yearown_span",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()
    y = args.year
    bundle = REPO / "results/calibration" / BUNDLES[y]

    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet
    from scripts.run_calibration_full import _coal_supply_class

    state, _ = reconstruct_bundle_fleet(bundle, y, verbose=False)
    fa = state["fleet_arrays"]
    pmax = np.asarray(fa.pmax, float)
    avail = np.asarray(fa.availability, float)
    T = np.asarray(state["mc_base"]).shape[1]
    if avail.ndim == 1:
        avail = np.broadcast_to(avail[:, None], (len(pmax), T))
    cap = pmax[:, None] * avail

    groups, codes = fa.plant_group, np.asarray(fa.plant_code)
    klass = np.array(
        [
            _coal_supply_class(int(codes[i]))
            if str(groups[i]) == "COAL"
            else str(groups[i])
            for i in range(len(fa.unit_ids))
        ],
        dtype=object,
    )

    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{y}.parquet")
    ch = ch[ch["pass"] == "P1"]

    print(
        f"\n=== SPP {y} fidelity: committed dispatch vs HEAD-reconstructed availability ==="
    )
    print(
        f"{'class':<16} {'recon GW':>9} {'disp max GW':>12} {'worst excess MW':>16} {'h over':>7}"
    )
    worst = 0.0
    for kk in sorted(set(klass.tolist())):
        m = klass == kk
        if not m.any():
            continue
        sub = ch[ch["klass"] == kk]
        if sub.empty:
            continue
        disp = (
            sub.groupby("hour")["mw"].sum().reindex(range(T), fill_value=0.0).to_numpy()
        )
        avail_h = cap[m].sum(axis=0)
        exc = disp - avail_h
        over = int((exc > 1.0).sum())
        worst = max(worst, float(exc.max()))
        print(
            f"{kk:<16} {avail_h.max() / 1000:>9.2f} {disp.max() / 1000:>12.2f} "
            f"{exc.max():>16.1f} {over:>7}"
        )
    print(
        f"\nVERDICT: worst class-hour excess {worst:.1f} MW "
        f"({'FIDELITY OK — no class ever dispatches above the reconstructed fleet' if worst <= 1.0 else 'DRIFT — the reconstruction is NOT the keeper fleet'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
