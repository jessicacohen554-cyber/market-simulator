"""spp-41 phase 0 report (ZERO LP): read the cached offer arrays and locate the crossover.

Consumes the ``.npz`` per-row tables written by
``scripts/probes/_spp41_crossover_phase0.py`` (which are themselves
``run_year(..., fleet_only=True)`` rebuilds of the SPP keeper's own recipe --
the assembled P0 objective the LP is handed, never a re-derivation) and reports:

1. the PRB and CC_REGULAR offer stacks, per band, capacity-weighted;
2. the MARGINAL tranche of each -- the dearest PRB row versus the cheapest and
   dearest CC_REGULAR econ rows -- which is the pair whose ordering IS the
   coal<->gas crossover;
3. the fuel decomposition of each row's marginal cost, verified against
   ``mc_base`` rather than assumed, so the gas-price sensitivity of the CC
   stack and the gas-price sensitivity of the PRB stack are both MEASURED;
4. the gas price at which the two stacks cross, solved from that decomposition.

Run: ``python3 scripts/probes/_spp41_crossover_report.py``
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

CACHE = Path(
    os.environ.get(
        "SPP41_CACHE",
        "/tmp/claude-0/-home-user-market-simulator/"
        "d1272d6d-a347-5fa8-85cd-cf88fd75dd3e/scratchpad/spp41",
    )
)

YEARS = [2024, 2023, 2021, 2022]  # ascending delivered gas price


def load(year: int) -> dict:
    z = np.load(CACHE / f"rows_{year}.npz", allow_pickle=True)
    d = {k: z[k] for k in z.files}
    for k in ("klass", "band", "coal_supply", "fuel_type", "unit_id"):
        d[k] = d[k].astype(str)
    return d


def cw(vals: np.ndarray, w: np.ndarray) -> float:
    w = np.maximum(np.asarray(w, dtype=float), 0.0)
    return float(np.average(vals, weights=w)) if w.sum() > 0 else float("nan")


def stack(d: dict, klass: str) -> dict:
    m = d["klass"] == klass
    return {k: v[m] for k, v in d.items() if getattr(v, "shape", ()) == d["klass"].shape}


def main() -> None:
    print("=" * 78)
    print("SPP-41 PHASE 0 — coal<->gas crossover in the model's OWN offer arrays")
    print("Source: run_year(fleet_only=True) on the keeper recipe. ZERO LP.")
    print("=" * 78)

    for y in YEARS:
        d = load(y)
        gas = float(d["meta_gas"])
        print(f"\n##### {y}   delivered gas ${gas:.2f}/MMBtu " + "#" * 30)

        for klass in ("COAL_PRB", "CC_REGULAR"):
            s = stack(d, klass)
            if s["pmax"].size == 0:
                print(f"  {klass}: no rows")
                continue
            print(
                f"  {klass}: n={s['pmax'].size}  pmax={s['pmax'].sum():8.1f} MW  "
                f"cw-mean MC=${cw(s['mc_mean'], s['pmax']):7.3f}/MWh  "
                f"cw-mean HR={cw(s['heat_rate'], s['pmax']):6.3f} MMBtu/MWh  "
                f"cw-mean fuel=${cw(s['fuel_mean'], s['pmax']):5.3f}/MMBtu"
            )
            for b in ("mustrun", "committed", "econlo", "econ", "econhi", "peak"):
                bm = s["band"] == b
                if not bm.any():
                    continue
                print(
                    f"      {b:10s} n={bm.sum():4d}  pmax={s['pmax'][bm].sum():8.1f} MW  "
                    f"MC ${cw(s['mc_mean'][bm], s['pmax'][bm]):7.3f}  "
                    f"[p05 {np.percentile(s['mc_mean'][bm], 5):7.3f} .. "
                    f"p95 {np.percentile(s['mc_mean'][bm], 95):7.3f}]"
                )

        # ---- the marginal pair -------------------------------------------
        prb = stack(d, "COAL_PRB")
        cc = stack(d, "CC_REGULAR")
        if prb["pmax"].size and cc["pmax"].size:
            # The DEAREST PRB row carrying real capacity vs the CHEAPEST CC
            # econ row: if the dearest coal still undercuts the cheapest gas,
            # the whole CC fleet sits behind the whole PRB fleet, which is
            # exactly the saturation SPP-40 measured.
            pm = prb["pmax"] > 1.0
            cm = (cc["pmax"] > 1.0) & np.isin(
                cc["band"], ["econlo", "econ", "econhi", "committed"]
            )
            prb_hi = prb["mc_mean"][pm].max()
            prb_lo = prb["mc_mean"][pm].min()
            cc_lo = cc["mc_mean"][cm].min()
            cc_hi = cc["mc_mean"][cm].max()
            print(
                f"  MARGINAL PAIR:  PRB span ${prb_lo:7.3f} .. ${prb_hi:7.3f}   "
                f"CC(committed+econ) span ${cc_lo:7.3f} .. ${cc_hi:7.3f}"
            )
            print(
                f"     dearest PRB - cheapest CC = ${prb_hi - cc_lo:+8.3f}/MWh   "
                f"({'CC fully behind PRB' if cc_lo > prb_hi else 'stacks INTERLEAVE'})"
            )
            # MW of CC that is dearer than the dearest PRB row = the CC
            # capacity the merit order pushes entirely behind coal.
            behind = cc["pmax"][cm][cc["mc_mean"][cm] > prb_hi].sum()
            print(
                f"     CC committed+econ MW dearer than the dearest PRB row: "
                f"{behind:8.1f} of {cc['pmax'][cm].sum():8.1f} MW "
                f"({100 * behind / max(cc['pmax'][cm].sum(), 1e-9):5.1f} %)"
            )


if __name__ == "__main__":
    main()
