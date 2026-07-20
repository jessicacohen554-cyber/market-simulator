"""CAISO-104 §2 adjudication probe: are the firm import blocks PINNED?

FINDING-caiso104 §2 (pre-registered): the keeper's recorded scenario_config
carries ``caiso_firm_import_selfschedule = True`` — the caiso-77 must-flow
floor, which sets each firm block's ``min_gen`` to its full shaped
capability ``pmax x availability``. If that pin holds on the solved bytes,
the granted M-EVE-1 bid change ($28/$48 -> price-taking constant) is
provably inert (a variable fixed at equal bounds never sets lambda), and
FINDING-caiso103 §3's interior/withheld attribution was a proxy artifact.

Per year, from the bundle's own persisted arrays:
  * ``floors/<year>_P1.npz`` — the min_gen the P1 LP actually saw;
  * ``dispatch/<year>_P1.parquet`` — the solved mw per unit-hour;
for each firm-block pseudo-unit (WECC_PNW_PNW_hydro_base,
WECC_DSW_DSW_solar_PV): share of hours with ``mw == min_gen`` (rel tol
1e-6), min_gen > 0 share, and the mean/max mw-vs-min_gen gap. The
pre-registered pin criterion: dispatch == min_gen in >= 99.9 % of hours
with a positive floor (dispatch can never exceed the floor when the floor
IS the availability cap, so mw == min_gen == cap).

Usage: python scripts/probes/_caiso104_firm_pin_check.py <bundle_dir>
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2023, 2024, 2025)
FIRM_UNITS = ("WECC_PNW_PNW_hydro_base", "WECC_DSW_DSW_solar_PV")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bundle = Path(sys.argv[1])
    verdicts = []
    for year in YEARS:
        npz = np.load(bundle / "floors" / f"{year}_P1.npz")
        unit_ids = list(npz["unit_ids"])
        min_gen = npz["min_gen"]
        disp = pd.read_parquet(
            bundle / "dispatch" / f"{year}_P1.parquet",
            columns=["unit_id", "hour", "mw"],
        )
        print(f"\n===== {year} =====")
        for fu in FIRM_UNITS:
            if fu not in unit_ids:
                print(f"  {fu}: NOT IN FLEET")
                continue
            r = unit_ids.index(fu)
            mg = np.asarray(min_gen[r], dtype=float)
            d = disp[disp.unit_id == fu]
            mw = np.zeros(mg.size)
            mw[d.hour.to_numpy(int)] = d.mw.to_numpy(float)
            pos = mg > 1e-6
            at_floor = np.isclose(mw, mg, rtol=1e-6, atol=1e-3)
            pin_share = float(at_floor[pos].mean()) if pos.any() else float("nan")
            gap = mw - mg
            print(
                f"  {fu}: floor>0 in {pos.mean():.3f} of hours | "
                f"dispatch==floor in {pin_share:.4f} of floored hours | "
                f"gap mean {gap[pos].mean() if pos.any() else float('nan'):+.2f} MW "
                f"max {gap[pos].max() if pos.any() else float('nan'):+.1f} | "
                f"floor mean {mg.mean():.0f} MW, dispatch mean {mw.mean():.0f} MW"
            )
            verdicts.append((year, fu, pin_share))
    print("\n===== PRE-REGISTERED CRITERION (pin >= 0.999) =====")
    pinned = all(v >= 0.999 for _, _, v in verdicts if np.isfinite(v))
    for year, fu, v in verdicts:
        print(f"  {year} {fu}: {v:.4f}")
    print(
        "  VERDICT: "
        + (
            "PINNED — M-EVE-1 bid change adjudicated INERT (FINDING-caiso104 §2)"
            if pinned and verdicts
            else "NOT pinned — M-EVE-1 proceeds as granted (FINDING-caiso104 §4)"
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
