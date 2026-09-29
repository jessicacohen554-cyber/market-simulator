"""SPP-102 stage 1 (copy of _spp89_stack_dump.py on the SPP-100 keeper) (ZERO LP): dump the keeper's thermal offer stack for one year.

Rebuilds ``results/calibration/spp100_arm_span``'s ``year`` fleet with no LP
(``reconstruct_bundle_fleet``, one interpreter per year: it holds per-process
caches) and writes, for every thermal row, the hourly offer ``mc_base``, the
available MW ``pmax x availability``, the hourly offer fuel price, class and plant.
Stage 2 (``_spp89_coal_cc_swap.py``) reads these ``.npz`` files.

Usage: ``python scripts/probes/_spp89_stack_dump.py --year 2022 --out-dir <dir>``
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

BUNDLE = REPO / "results/calibration/spp100_arm_span"
THERMAL_PREFIXES = ("COAL", "CC_", "CT_", "ST_")


def main() -> int:
    """Rebuild one year and dump its thermal stack."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    a = ap.parse_args()
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, _ = reconstruct_bundle_fleet(BUNDLE, a.year, verbose=True)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], float)
    n = len(mc)
    fuel = np.broadcast_to(np.asarray(state["fuel_prices"], float).reshape(n, -1), mc.shape)
    avail = np.broadcast_to(np.asarray(fa.availability, float).reshape(n, -1), mc.shape)
    pmax = np.asarray(fa.pmax, float)
    klass = np.asarray(fa.plant_group).astype(str)
    hr = np.asarray(fa.heat_rate, float)
    th = np.flatnonzero([k.startswith(THERMAL_PREFIXES) for k in klass])
    a.out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        a.out_dir / f"stack_{a.year}.npz",
        mc=mc[th].astype(np.float32),
        cap=(pmax[:, None] * avail)[th].astype(np.float32),
        fuel=fuel[th].astype(np.float32),
        pmax=pmax[th], hr=hr[th],
        klass=klass[th], codes=np.asarray(fa.plant_code).astype(int)[th],
        gas=float(state["config"].gas_price) if hasattr(state["config"], "gas_price") else np.nan,
    )
    print(a.year, "rows", len(th), "classes", sorted(set(klass[th].tolist())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
