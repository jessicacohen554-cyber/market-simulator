"""ercot-173 SEAM PROOF (no LP; PRECOMMIT-ercot173 §5, SP-1..SP-4).

Verifies, before any solve, that the armed reconciliation flag produces
EXACTLY the intended composition at the availability seam:

* SP-1 — on every scoped tranche, capture R (keeper + reconciliation) equals
  ``min(capture B, ceil_min)`` where ``ceil_min`` is the min-composed
  class-grain ceiling computed independently from the loaders (tol 1e-6,
  float32 capture grain).
* SP-2 — every tranche outside the event-cap scope is byte-identical A vs R.
* SP-3 — C1 inertness: the class-grain and plant-grain partial dicts induce
  identical per-bin factors on the current bins sheet (P-C1-INERT).
* (SP-4, gate-off no-op, is carried by the loader equivalence test in
  tests/unit/data/test_outages.py plus the control solve's fresh-replay
  drift check — recorded here for completeness, not recomputed.)

Usage::

    PYTHONPATH=.:src python scripts/probes/_ercot173_seam_proof.py \
        --work <capture dir> --year 2024
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

SCOPE = ("COAL", "CC_REGULAR", "ST_GAS", "CT_PEAKER")  # arrays.py _evcap_scope
TOL = 1e-6


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()
    yr = args.year

    A = np.load(args.work / f"avail_{yr}_A.npz", allow_pickle=True)
    B = np.load(args.work / f"avail_{yr}_B.npz", allow_pickle=True)
    R = np.load(args.work / f"avail_{yr}_R.npz", allow_pickle=True)
    for k in ("plant_code", "group"):
        assert (A[k] == B[k]).all() and (A[k] == R[k]).all(), f"axis mismatch on {k}"
    a = A["availability"].astype(np.float64)
    b = B["availability"].astype(np.float64)
    r = R["availability"].astype(np.float64)
    codes = A["plant_code"].astype(int)
    groups = np.array([str(g) for g in A["group"]])
    hours = a.shape[1]

    from market_sim.data.outages import (
        partial_outage_derate_factors,
        unit_outage_derate_factors,
    )

    fwin = unit_outage_derate_factors(yr, hours, iso="ERCOT")
    fpar_c = partial_outage_derate_factors(yr, hours, class_grain=True)
    fpar_p = partial_outage_derate_factors(yr, hours)

    # SP-3 — C1 inertness at bin grain.
    assert set(k[0] for k in fpar_c) == set(fpar_p), "SP-3: plant sets differ"
    for (code, _g), arr in fpar_c.items():
        assert np.array_equal(arr, fpar_p[code]), f"SP-3: {code} factors differ"
    print(f"SP-3 PASS: class-grain == plant-grain per plant ({len(fpar_p)} plants)")

    in_scope = np.isin(groups, SCOPE)
    # SP-2 — out-of-scope byte-identical A vs R.
    d2 = np.abs(a[~in_scope] - r[~in_scope]).max() if (~in_scope).any() else 0.0
    assert d2 == 0.0, f"SP-2 FAIL: out-of-scope max delta {d2}"
    print(f"SP-2 PASS: {int((~in_scope).sum())} out-of-scope tranches byte-identical")

    # SP-1 — scoped tranches: R == min(B, ceil_min); no-layer tranches R == B.
    worst, n_layered = 0.0, 0
    for i in np.where(in_scope)[0]:
        key = (int(codes[i]), groups[i])
        layers = []
        f = fwin.get(key)
        if f is not None:
            layers.append(np.asarray(f, dtype=float)[:hours])
        fp = fpar_c.get(key)
        if fp is not None:
            layers.append(np.asarray(fp, dtype=float)[:hours])
        if layers:
            ceil_min = layers[0] if len(layers) == 1 else np.minimum(*layers)
            exp = np.minimum(b[i], ceil_min)
            n_layered += 1
        else:
            exp = b[i]
        worst = max(worst, float(np.abs(r[i] - exp).max()))
    assert worst <= TOL, f"SP-1 FAIL: max |R - min(B, ceil_min)| = {worst}"
    print(
        f"SP-1 PASS: {n_layered} layered scoped tranches match min(B, ceil_min) "
        f"to {worst:.2e} (tol {TOL})"
    )

    # Report the restored capability at the two 2024 shed hours when scoring 2024.
    if yr == 2024:
        pmax = A["pmax"].astype(float)
        for h, label in ((2827, "2024-04-28 19:00"), (3067, "2024-05-08 19:00")):
            d = ((r[:, h] - a[:, h]) * pmax).sum()
            print(f"  restored capability at {label}: {d:,.1f} MW (R - A, all tranches)")


if __name__ == "__main__":
    main()
