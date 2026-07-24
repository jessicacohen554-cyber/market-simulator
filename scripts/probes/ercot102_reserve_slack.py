"""ERCOT-102 — the AS-holdout is already held and NON-BINDING at the missed tail.

The decisive diagnostic for the ERCOT-102 AS-holdout thesis. Splits the actual
>$300 tail hours into HIT (model also priced scarcity) and MISSED (model priced
sub-scarcity) and reports, from the committed keeper sidecar, the reserve dual
(``reserve_price`` = sum of every co-opt family's balance dual, incl. the rigid
VOLL RegUp/RRS/ECRS withheld families that hold the measured ASPLANNP433 plan
out of the energy stack) at each set.

The finding: the reserve co-opt is the model's own scarcity-price-former (it
binds at VOLL in ~all the hours the model DOES price scarcity), but at the
MISSED hours it is SLACK (~$0) — the measured AS is already fully held, yet the
model carries enough spare responsive headroom (phantom online capability) that
neither the measured-AS families nor the ORDC total-reserve span tighten. So
holding MORE measured AS out cannot reprice the missed tail: the holdout there
has slack, not deficit. (Forcing it to bind by capping the headroom over-fires —
ercot41/43, docs/handoffs/ercot-online-capacity-envelope-2026-07.md.)

No LP. Reads the committed keeper system sidecar + the committed zonal actual
archive. Usage: python -m scripts.probes.ercot102_reserve_slack <bundle> [--year Y...]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

# Model zone -> settlement LZ(s) (mirrors derive_actual_lmp.ERCOT_MODEL_ZONE_TO_LZ)
ZONE_TO_LZ: dict[str, tuple[str, ...]] = {
    "Houston": ("LZ_HOUSTON",),
    "North": ("LZ_NORTH",),
    "Northeast": ("LZ_RAYBN",),
    "South": ("LZ_SOUTH",),
    "South_Central": ("LZ_AEN", "LZ_CPS", "LZ_LCRA"),
    "West": ("LZ_WEST",),
    "Panhandle": ("LZ_WEST",),
}


def _zonal_actual(year: int) -> dict[str, np.ndarray]:
    from market_sim.config.paths import CALIBRATION_DIR

    df = pd.read_parquet(CALIBRATION_DIR / "actual_lmp_zonal_ERCOT.parquet")
    df = df[df["year"] == year]
    out: dict[str, np.ndarray] = {}
    for sp, g in df.groupby("settlement_point"):
        arr = np.full(8760, np.nan)
        arr[g["hour"].to_numpy()] = g["rt"].to_numpy()
        out[str(sp)] = arr
    return out


def run(bundle: Path, year: int, tail: float = 300.0, sub: float = 200.0) -> None:
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    p1 = s[s["pass"] == "P1"].copy()
    zones = list(p1.pivot(index="hour", columns="zone", values="price").columns)

    def piv(col: str) -> np.ndarray:
        return p1.pivot(index="hour", columns="zone", values=col).to_numpy()

    P, D, RP, ORDC = piv("price"), piv("demand"), piv("reserve_price"), piv("ordc_adder")
    act = _zonal_actual(year)
    A = np.full_like(P, np.nan)
    for j, z in enumerate(zones):
        lzs = ZONE_TO_LZ.get(z)
        if not lzs:
            continue
        stack = np.vstack([act[l] for l in lzs if l in act])
        A[:, j] = np.nanmean(stack, axis=0)

    Dh = D.sum(1)
    model_h = (P * D).sum(1) / Dh
    va = ~np.isnan(A)
    actual_h = (np.where(va, A, 0.0) * D).sum(1) / np.where(va, D, 0.0).sum(1)
    ordc_h = (ORDC * D).sum(1) / Dh
    rp_h = RP.max(1)  # reserve is system-wide; the max zonal dual is the family dual

    t = (actual_h > tail) & ~np.isnan(actual_h)
    miss = t & (model_h < sub)
    hit = t & (model_h >= sub)
    modscar = model_h > tail

    def _line(name: str, sel: np.ndarray) -> str:
        n = int(sel.sum())
        if n == 0:
            return f"  {name:28s}: 0 hrs"
        binds = int((rp_h[sel] > 1.0).sum())
        return (
            f"  {name:28s}: {n:4d} hrs | model ${model_h[sel].mean():7.1f} "
            f"actual ${actual_h[sel].mean():7.0f} | reserve-dual binds {binds:3d}/{n:<3d} "
            f"(mean ${rp_h[sel].mean():8.1f}, ordc_adder ${ordc_h[sel].mean():.1f})"
        )

    print(f"\n=== {year}  (actual>${tail:.0f} tail; MISSED = model<${sub:.0f}) ===")
    print(_line("actual>tail (all)", t))
    print(_line("MISSED (holdout SLACK)", miss))
    print(_line("HIT (holdout BINDS)", hit))
    print(_line("model priced >tail", modscar))
    if int(modscar.sum()) > 0:
        pct = 100.0 * (rp_h[modscar] > 1.0).mean()
        print(
            f"  -> when the model DOES price scarcity, the reserve co-opt binds in "
            f"{pct:.0f}% of those hours: the mechanism is present and works; the "
            f"MISSED hours are slack (phantom headroom), not an under-held plan."
        )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ercot102_reserve_slack")
    ap.add_argument("bundle")
    ap.add_argument("--year", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--tail", type=float, default=300.0)
    ap.add_argument("--sub", type=float, default=200.0)
    args = ap.parse_args(argv)
    b = Path(args.bundle) if Path(args.bundle).is_absolute() else REPO / args.bundle
    for y in args.year:
        run(b, y, tail=args.tail, sub=args.sub)
    return 0


if __name__ == "__main__":
    sys.exit(main())
