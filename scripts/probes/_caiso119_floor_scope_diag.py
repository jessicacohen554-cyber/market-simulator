"""caiso-119 SCOPE DIAGNOSTIC: why is the measured min-load correction
(caiso_ra_min_load_frac 0.26 -> 0.570) near-inert in dispatch? NO LP — reads the
two solved arms' own committed P1 floor records.

The A/B (`_caiso119_ab_score.py`) showed the delta moves belly gas by only
-28 / +59 / +52 MW across 2023-25 (8-10 % of the gap at best) while more than
DOUBLING the floor level. Two explanations are possible and they lead to
different next lanes:

  H1  NARROW SCOPE — the RA bridge floors very few plant-hours, so the level is
      irrelevant. (Next lane: the bridge's gap-DETECTION rule.)
  H2  SLACK FLOOR — the bridge floors many plant-hours, but the LP was already
      dispatching those units ABOVE even the raised floor, so it never binds.
      (Next lane: not commitment at all — the belly gap is an economics/merit
      problem.)

`floors/<year>_P1.npz` carries the exact per-unit, per-hour `min_gen` the P1
solve was handed, plus a `mechanism` id per cell — so both hypotheses are
directly measurable rather than inferred:

  * floored plant-hours and floored MW, per arm (H1 vs H2 discriminator)
  * how much the floor LEVEL actually rose between arms
  * BINDING rate: cells where P1 dispatch sits at the floor (within tolerance)
    vs cells where the floor is slack — the quantity that decides whether a
    higher floor could ever have moved dispatch

Run:  .venv/bin/python scripts/probes/_caiso119_floor_scope_diag.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results" / "calibration"
ARMS = {"BASE": "caiso119_base_A", "MINLOAD": "caiso119_minload_B"}
YEARS = (2023, 2024, 2025)
BELLY = (10, 11, 12, 13, 14, 15)
TOL = 0.5  # MW; a cell counts as BINDING when dispatch <= floor + TOL


def load_floor(arm: str, year: int):
    p = CAL / ARMS[arm] / "floors" / f"{year}_P1.npz"
    if not p.exists():
        return None
    return np.load(p, allow_pickle=True)


def dispatch_matrix(arm: str, year: int, unit_ids: np.ndarray) -> np.ndarray | None:
    """Per-unit x hour P1 dispatch aligned to the floor record's unit order."""
    p = CAL / ARMS[arm] / "dispatch" / f"{year}_P1.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    cols = {c.lower(): c for c in df.columns}
    ucol = cols.get("unit_id") or cols.get("unit") or cols.get("gen_id")
    hcol = cols.get("hour")
    mcol = cols.get("mw") or cols.get("dispatch_mw") or cols.get("p")
    if not (ucol and hcol and mcol):
        return None
    piv = df.pivot_table(index=ucol, columns=hcol, values=mcol, aggfunc="sum")
    piv = piv.reindex(index=pd.Index(unit_ids))
    return piv.to_numpy(dtype=np.float32)


def main() -> None:
    print("=" * 96)
    print("caiso-119 FLOOR SCOPE — is the min-load correction inert because the "
          "scope is NARROW (H1) or because the floor is SLACK (H2)?")
    print("=" * 96)

    for year in YEARS:
        fa, fb = load_floor("BASE", year), load_floor("MINLOAD", year)
        if fa is None or fb is None:
            print(f"\n--- {year} ---  (floor record missing for an arm)")
            continue
        ga, gb = fa["min_gen"], fb["min_gen"]
        hod = np.arange(ga.shape[1]) % 24
        belly_cols = np.isin(hod, BELLY)

        print(f"\n--- {year} ---")
        for tag, g in (("BASE", ga), ("MINLOAD", gb)):
            cells = int((g > 0).sum())
            bcells = int((g[:, belly_cols] > 0).sum())
            mw = float(g.sum() / g.shape[1])          # annual-average floored MW
            bmw = float(g[:, belly_cols].sum() / belly_cols.sum())
            print(f"  {tag:<8} floored cells {cells:>9,}  (belly {bcells:>8,})   "
                  f"avg floored MW {mw:>8,.0f}  (belly {bmw:>8,.0f})")

        same_cells = int(((ga > 0) == (gb > 0)).all(axis=None))
        n_a, n_b = int((ga > 0).sum()), int((gb > 0).sum())
        lvl_a = float(ga[ga > 0].mean()) if n_a else 0.0
        lvl_b = float(gb[gb > 0].mean()) if n_b else 0.0
        print(f"  scope change: {n_a:,} -> {n_b:,} floored cells "
              f"({100*(n_b-n_a)/max(n_a,1):+.1f} %)   "
              f"level change: {lvl_a:,.1f} -> {lvl_b:,.1f} MW/cell "
              f"({100*(lvl_b-lvl_a)/max(lvl_a,1e-9):+.1f} %)")
        print(f"  identical floored-cell MASK: {bool(same_cells)}")

        # BINDING test — the H1/H2 discriminator.
        for tag, arm, g in (("BASE", "BASE", ga), ("MINLOAD", "MINLOAD", gb)):
            d = dispatch_matrix(arm, year, np.asarray(fa["unit_ids"]))
            if d is None:
                print(f"  {tag}: dispatch matrix unavailable — binding test skipped")
                continue
            m = g > 0
            n = int(m.sum())
            if not n:
                continue
            binding = int((d[m] <= g[m] + TOL).sum())
            print(f"  {tag}: of {n:,} floored cells, {binding:,} BIND "
                  f"({100*binding/n:.1f} %) — the rest are slack "
                  f"(LP already above the floor)")

        # Which mechanism owns the floored cells.
        mech = fb["mechanism"]
        ids, counts = np.unique(mech[gb > 0], return_counts=True)
        top = sorted(zip(ids.tolist(), counts.tolist()), key=lambda t: -t[1])[:6]
        print("  MINLOAD floored cells by mechanism id: " +
              ", ".join(f"{i}:{c:,}" for i, c in top))

    print("\n" + "=" * 96)
    print("READ: scope ~unchanged + LOW binding rate -> H2 (the floor is slack; "
          "the LP already runs those units above it, so NO min-load level could "
          "have moved the belly). Scope small + HIGH binding -> H1 (the "
          "gap-detection rule is the limiter).")


if __name__ == "__main__":
    main()
