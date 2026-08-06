"""ercot-174 SEAM PROOF (no LP; PRECOMMIT-ercot174 §4a, SP-1..SP-5).

Verifies, at the availability seam and before any solve, that the default-off
unit-scoped gate is INERT at its default and produces EXACTLY the intended
composition when armed:

* **SP-1** — on every layered scoped tranche, the armed capture ``R`` equals
  ``min(B, ceil_unit_scoped)``, where ``B`` is the PRE-CAP capture (both
  event-cap gates off) and ``ceil_unit_scoped`` is recomputed independently
  from the loaders by the PRECOMMIT §3b rule (``min`` where the window and
  partial layers share a CAMPD unit at that hour, the incumbent product where
  they do not). The cap is a pure ``np.minimum`` applied last, so capping the
  pre-cap capture by the intended ceiling must reproduce the arm exactly.
  ``B`` is required rather than ``A``: the unit-scoped ceiling RESTORES
  (it sits at or above the product), so ``min(A, ceil)`` would collapse to
  ``A`` and the check would be vacuous.
* **SP-2** — every tranche outside ``_evcap_scope`` is byte-identical A vs R.
* **SP-3** — C1 inertness: the class-grain and plant-grain partial dicts induce
  identical per-bin factors on the current bins sheet.
* **SP-4** — gate-off no-op: the control capture ``A`` is taken with the new
  flag at its DEFAULT, so it must equal ``min(B, ceil_product)`` exactly — the
  incumbent product composition, unchanged by this session's code.
* **SP-5** — strict-subset bracket: pointwise
  ``ceil_product <= ceil_unit_scoped <= ceil_min`` on every scoped bin-hour,
  and ``ceil_unit_scoped`` takes only those two values.

Usage::

    PYTHONPATH=.:src python scripts/probes/ercot174_seam_proof.py \
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
    """Run SP-1..SP-5 on a captured control/arm availability pair."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()
    yr = args.year

    A = np.load(args.work / f"avail_{yr}_A.npz", allow_pickle=True)
    B = np.load(args.work / f"avail_{yr}_B.npz", allow_pickle=True)
    R = np.load(args.work / f"avail_{yr}_R.npz", allow_pickle=True)
    for k in ("plant_code", "group", "name"):
        assert (A[k] == R[k]).all() and (A[k] == B[k]).all(), f"axis mismatch: {k}"
    a = A["availability"].astype(np.float64)
    b = B["availability"].astype(np.float64)
    r = R["availability"].astype(np.float64)
    codes = A["plant_code"].astype(int)
    groups = np.array([str(g) for g in A["group"]])
    hours = a.shape[1]

    from market_sim.config.paths import CAMPD_BINS_CSV
    from market_sim.data.outages import (
        partial_outage_active_units,
        partial_outage_derate_factors,
        shared_unit_hours,
        unit_outage_active_units,
        unit_outage_derate_factors,
    )

    fwin = unit_outage_derate_factors(yr, hours, str(CAMPD_BINS_CSV), iso="ERCOT")
    fpar_c = partial_outage_derate_factors(yr, hours, class_grain=True)
    fpar_p = partial_outage_derate_factors(yr, hours)
    w_units = unit_outage_active_units(yr, hours, iso="ERCOT")
    p_units = partial_outage_active_units(yr, hours, iso="ERCOT")

    # SP-3 — C1 inertness at bin grain.
    assert set(k[0] for k in fpar_c) == set(fpar_p), "SP-3: plant sets differ"
    for (code, _g), arr in fpar_c.items():
        assert np.array_equal(arr, fpar_p[code]), f"SP-3: {code} factors differ"
    print(f"SP-3 PASS: C1 inert on {len(fpar_c)} partial-extract bins")

    # SP-1 / SP-5 — the composed ceiling, rebuilt independently.
    n_layered = n_shared_bins = 0
    max_dev = 0.0
    bracket_ok = True
    for g_idx in range(a.shape[0]):
        grp = groups[g_idx]
        if grp not in SCOPE:
            continue
        key = (int(codes[g_idx]), grp)
        fw = fwin.get(key)
        fp = fpar_c.get(key)
        if fw is None and fp is None:
            continue
        if fw is None or fp is None:
            # single-layer bin: the composition is that layer, both arms alike
            ceil = (fw if fp is None else fp)[:hours]
        else:
            n_layered += 1
            prod = fw[:hours] * fp[:hours]
            mn = np.minimum(fw[:hours], fp[:hours])
            shared = shared_unit_hours(w_units.get(key), p_units.get(key), hours)
            ceil = np.where(shared, mn, prod)
            if shared.any():
                n_shared_bins += 1
            # SP-5 — bracket and two-valuedness.
            if not (
                (ceil >= prod - TOL).all()
                and (ceil <= mn + TOL).all()
                and (np.isclose(ceil, prod) | np.isclose(ceil, mn)).all()
            ):
                bracket_ok = False
        dev = float(np.abs(r[g_idx, :hours] - np.minimum(b[g_idx, :hours], ceil)).max())
        max_dev = max(max_dev, dev)
    assert bracket_ok, "SP-5 FAILED: ceiling outside [product, min] or not two-valued"
    print(
        f"SP-5 PASS: product <= unit-scoped <= min on every scoped bin-hour "
        f"({n_layered} layered bins, {n_shared_bins} with a shared unit)"
    )
    assert max_dev <= TOL, f"SP-1 FAILED: max |R - min(B, ceil)| = {max_dev:.3e}"
    print(f"SP-1 PASS: arm == min(pre-cap, intended ceiling), max dev {max_dev:.3e}")

    # SP-2 — out-of-scope tranches byte-identical.
    out_scope = ~np.isin(groups, SCOPE)
    assert np.array_equal(a[out_scope], r[out_scope]), "SP-2 FAILED"
    print(f"SP-2 PASS: {int(out_scope.sum())} out-of-scope tranche(s) byte-identical")

    # SP-4 — the control capture was taken at the gate's DEFAULT, so it must
    # reproduce the incumbent PRODUCT composition exactly: A == min(B, prod).
    n_prod = 0
    max_prod_dev = 0.0
    for g_idx in range(a.shape[0]):
        grp = groups[g_idx]
        key = (int(codes[g_idx]), grp)
        if grp not in SCOPE or key not in fwin or key not in fpar_c:
            continue
        prod = fwin[key][:hours] * fpar_c[key][:hours]
        max_prod_dev = max(
            max_prod_dev,
            float(np.abs(a[g_idx, :hours] - np.minimum(b[g_idx, :hours], prod)).max()),
        )
        n_prod += 1
    assert max_prod_dev <= TOL, f"SP-4 FAILED: |A - min(B, product)| = {max_prod_dev}"
    print(
        f"SP-4 PASS: control (gate at default) == min(pre-cap, incumbent "
        f"product) on all {n_prod} layered scoped tranche(s), "
        f"max dev {max_prod_dev:.3e}"
    )

    # Measured movement at the seam, for the record.
    diff = r - a
    moved = int((np.abs(diff) > TOL).any(axis=1).sum())
    print(
        f"\nseam movement: {moved} tranche(s) changed; "
        f"max +{float(diff.max()):.4f} / min {float(diff.min()):.4f}; "
        f"mean restored MW-fraction-hours {float(diff.sum()):.1f}"
    )


if __name__ == "__main__":
    main()
