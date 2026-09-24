"""nwpp-51: evaluate the PRE-REGISTERED stop conditions for arming
``eia860_vintage_tracks_solve_year`` on NWPP. ZERO LP.

WRITTEN AND COMMITTED BEFORE ANY LEG EXISTS, and before the owner has ruled
on whether any leg will be solved (the ``_nwpp49_gates.py`` discipline). Every
number below is transcribed from ``scripts/probes/_nwpp51_predict.py``'s
output as recorded in ``docs/handoffs/PRECOMMIT-nwpp-51-2026-09-24.md`` §3
and nothing else.

THIS IS A RULE-14 ACCURACY FIX, NOT A C4 LEVER. Nothing here selects the arm
by a gate. The limbs below only answer "did the change the census predicts
reach dispatch, and nothing else?" — they can STOP a leg as broken, never
promote one. C1 and C4 are REPORTED against their prediction, never gated
(rule 1 [R-STRUCT]; a C1 flip is not a reason to withhold a rule-14 fix).

Two variants are pre-registered (``--variant``):

* ``repaired`` (DEFAULT, the recommended arm): the vintage_2023 /
  vintage_2024 EIA-860 directories carry their own ``eia860_utility``
  sheet, so the cost-of-service ownership leg is live and Colstrip's
  committed band is unchanged. Only Jim Bridger 1-2 (2023) and North
  Valmy 1 (2023, 2024) change fuel.
* ``as_is``: the vintage dirs as committed today (no utility sheet), which
  also re-prices Colstrip's 709 MW committed band from $4.50 to $29.48
  in 2023 and 2024. Recorded so the prediction is on file; NOT recommended.

LIMBS (each measured against the keeper ``nwpp49_ror_span``):

  INERT (STOP, plumbing): model coal (sum of COAL_* classes) moves by LESS
    than the variant's ``lo`` in any armed year, OR a Jim Bridger (8066)
    ``ST_GAS`` row still dispatches in 2023, OR a North Valmy (8224)
    ``ST_GAS`` row still dispatches in 2023 or 2024.
  OVERSHOOT (STOP, something else moved): model coal moves by MORE than the
    variant's ``hi`` in any armed year, OR NWPP hydro annual energy moves by
    more than 1.0 TWh in any year (monthly budgets are fixed inputs).
  IDENTITY (STOP, drift): 2025's fleet is byte-identical (census digest),
    so any class's 2025 annual energy moving by more than 0.001 TWh means
    the leg is not the keeper's recipe at HEAD — the G-DRIFT audit is wrong
    or the solve path is non-deterministic. Not a verdict on the mechanism.

REPORTED, NEVER GATED: C1 CC_REGULAR 2023 against the -8.00 TWh edge
(keeper -7.213; flips if CC_REGULAR loses more than 0.787 TWh), coal r and
r_intra against their brackets.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwpp51_gates.py --bundle <composed bundle> \
        [--variant repaired|as_is] [--verdict-json <calibration_verdict --json output>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib.bundle_io import require_bundle_input  # noqa: E402

KEEPER = Path("results/calibration/nwpp49_ror_span")
COAL = ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE", "COAL")
HYDRO = ("hydro", "HYDRO")
#: PRECOMMIT §3: added model coal, TWh, (lo, hi), per variant and armed year.
D_COAL_BRACKET: dict[str, dict[int, tuple[float, float]]] = {
    "repaired": {2023: (0.629, 5.045), 2024: (0.000, 0.667)},
    "as_is": {2023: (-0.903, 3.513), 2024: (-2.585, -1.917)},
}
#: PRECOMMIT §3, reported not gated: coal r / r_intra brackets (lo-case, hi-case).
COAL_R_BRACKET: dict[str, dict[int, tuple[float, float]]] = {
    "repaired": {2023: (0.655, 0.662), 2024: (0.618, 0.625)},
    "as_is": {2023: (0.640, 0.651), 2024: (0.580, 0.582)},
}
COAL_R_INTRA_BRACKET: dict[str, dict[int, tuple[float, float]]] = {
    "repaired": {2023: (0.330, 0.395), 2024: (0.404, 0.471)},
    "as_is": {2023: (0.333, 0.395), 2024: (0.422, 0.469)},
}
HYDRO_TWH_BUDGET: float = 1.0
IDENTITY_TWH: float = 0.001
#: Keeper C1 CC_REGULAR 2023 (model - actual, TWh) and the band edge.
CC_REG_2023_KEEPER: float = -7.213
C1_BAND_TWH: float = 8.00
#: Plants whose ST_GAS rows the arm converts to coal, and the years it does.
FUEL_SWITCH: dict[int, tuple[int, ...]] = {8066: (2023,), 8224: (2023, 2024)}


def _class_twh(bundle: Path, year: int) -> pd.Series:
    """Annual P1 TWh by class from a bundle's committed class_hourly sidecar."""
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    return ch.groupby("klass", observed=True).mw.sum() / 1e6


def _coal_hourly(bundle: Path, year: int) -> np.ndarray:
    """Hourly P1 coal MW (all coal classes)."""
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & ch.klass.isin(COAL)]
    return ch.groupby("hour").mw.sum().reindex(range(8760), fill_value=0).to_numpy(float)


def _intra(x: np.ndarray) -> np.ndarray:
    """Within-day deviation from the daily mean."""
    x = x[: len(x) // 24 * 24].reshape(-1, 24)
    return (x - x.mean(1, keepdims=True)).ravel()


def main() -> int:
    """Score a composed bundle; exit 0 (in bracket) / 1 (INERT) / 2 (OVERSHOOT) / 3 (IDENTITY)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, type=Path)
    ap.add_argument("--variant", choices=sorted(D_COAL_BRACKET), default="repaired")
    ap.add_argument("--verdict-json", type=Path, default=None)
    args = ap.parse_args()
    b, v = args.bundle, args.variant
    e930 = pd.read_parquet(require_bundle_input(b, "eia930"))
    inert, over, ident = [], [], []
    print(f"nwpp-51 PRE-REGISTERED GATES — variant {v} — {b}\n")
    for year in (2023, 2024, 2025):
        arm, keep = _class_twh(b, year), _class_twh(KEEPER, year)
        d = arm.subtract(keep, fill_value=0.0)
        d_coal = float(d[d.index.isin(COAL)].sum())
        d_hyd = float(d[d.index.isin(HYDRO)].sum())
        cm = _coal_hourly(b, year)
        ca = e930[(e930.year == year) & (e930.series == "coal")].sort_values("hour").mw.to_numpy(float)[:8760]
        r, ri = float(np.corrcoef(cm, ca)[0, 1]), float(np.corrcoef(_intra(cm), _intra(ca))[0, 1])
        line = f"  {year}  dCoal {d_coal:+.3f} TWh  dHydro {d_hyd:+.3f}  coal r {r:.3f}  r_intra {ri:.3f}"
        if year in D_COAL_BRACKET[v]:
            lo, hi = D_COAL_BRACKET[v][year]
            rlo, rhi = COAL_R_BRACKET[v][year]
            ilo, ihi = COAL_R_INTRA_BRACKET[v][year]
            line += f"  [pred dCoal {lo:+.3f}..{hi:+.3f}; r {rlo:.3f}-{rhi:.3f}; r_intra {ilo:.3f}-{ihi:.3f}]"
            if d_coal < lo:
                inert.append(f"{year}: dCoal {d_coal:+.3f} < lo {lo:+.3f}")
            if d_coal > hi:
                over.append(f"{year}: dCoal {d_coal:+.3f} > hi {hi:+.3f}")
        else:
            worst = float(d.abs().max()) if len(d) else 0.0
            line += f"  [identity: max |dClass| {worst:.4f} TWh]"
            if worst > IDENTITY_TWH:
                ident.append(f"{year}: max |dClass| {worst:.4f} > {IDENTITY_TWH}")
        if abs(d_hyd) > HYDRO_TWH_BUDGET:
            over.append(f"{year}: hydro moved {d_hyd:+.3f} TWh")
        print(line)
        disp = b / "dispatch" / f"{year}_P1.parquet"
        if disp.exists():
            u = pd.read_parquet(disp, columns=["unit_id", "plant_code", "mw"])
            for plant, yrs in FUEL_SWITCH.items():
                if year in yrs:
                    st = u[(u.plant_code == plant) & u.unit_id.str.startswith("ST_GAS")]
                    if len(st):
                        inert.append(f"{year}: plant {plant} still has {st.unit_id.nunique()} ST_GAS rows "
                                     f"({st.mw.sum() / 1e6:.3f} TWh)")
        elif year in (2023, 2024):
            inert.append(f"{year}: {disp} absent — the fuel-switch rows cannot be checked")

    if args.verdict_json is not None:
        vj = json.loads(args.verdict_json.read_text())
        for rec in vj["criteria"]["fuelmix"]["records"]:
            if rec["key"] == "CC_REGULAR" and rec["year"] == 2023:
                gap = rec["model"] - rec["actual"]
                print(f"\n  REPORTED: C1 CC_REGULAR 2023 {gap:+.3f} TWh (keeper {CC_REG_2023_KEEPER:+.3f}; "
                      f"band ±{C1_BAND_TWH:.2f}) -> {rec['status']}")
    print("\n" + "=" * 72)
    if ident:
        print("  STOP — IDENTITY limb (not a verdict on the mechanism):")
        for h in ident:
            print(f"    - {h}")
        return 3
    if over:
        print("  STOP — OVERSHOOT limb:")
        for h in over:
            print(f"    - {h}")
        return 2
    if inert:
        print("  STOP — INERT limb:")
        for h in inert:
            print(f"    - {h}")
        return 1
    print("  Every armed year inside its pre-registered bracket; 2025 identical. "
          "Score with calibration_verdict and report C1 / C4 at full magnitude.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
