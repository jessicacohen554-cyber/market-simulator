"""Score the nyiso-99 demand-dropout repair against its pre-registered gates.

The single delta is ``_screen_demand_dropouts``
(``src/market_sim/data/eia930/demand.py``): EIA-930 posts some reporting gaps
as exactly 0.0 MW in the ``Demand`` column, which survives the NaN reindex and
every loader's ``interpolate().bfill().ffill()`` and is handed to the LP as
real load. On the NYISO keeper that is 2024 h403/6760/6761 and 2025 h354/355 —
five hours in which the model serves 0 MW against a true ~17-22 GW.

Both bundles are keeper replays of the SAME recipe (``replay_keeper.py``
reads the keeper's own ``meta.json``), so the only difference is the code fix.
The screen is a **proven no-op on 2023**, which makes the arm's own 2023 year a
same-recipe zero-delta control — a stronger control than a separate run,
because it shares the arm's container, fleet cache and basis.

Gates, from ``docs/PREREG-nyiso99-import-audit-demand-dropout-2026-07-29.md``
§4:

* **G1 control identity** — arm 2023 vs the control bundle's 2023, per-class
  hourly MW and per-zone hourly prices, < 1e-6. A miss voids everything below.
* **G2 repair landed** — no hour with total served demand == 0.0, any year.
* **G3 level neutrality** — annual served energy rises by the repaired wedge
  only (+0.0562 TWh 2024, +0.0435 TWh 2025), within +-1 %.
* **G4 C1 protection** — per-class energy deltas, with the knife-edge 2023
  ``CC_REGULAR`` cell (-2.79 of +-2.94) called out.
* **G5/G6** — reported: hours over $300 (C3c) and the import statistic, so a
  move in either is visible rather than assumed absent.

Usage::

    python scripts/probes/nyiso99_ab_compare.py \\
        --control results/calibration/nyiso98_nucavail \\
        --arm     results/calibration/nyiso99_demandfix
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes.nyiso99_import_benchmark_provenance import (  # noqa: E402
    YEARS,
    _r,
    measured_import,
    model_import,
)

# The pre-registered repaired wedge (TWh), measured off the loaders before the
# solve: the energy the dropout hours were serving as 0 MW.
EXPECTED_WEDGE_TWH = {2023: 0.0, 2024: 0.05624, 2025: 0.04345}
WEDGE_TOL = 0.01  # +-1 % of the expected wedge (G3)
IDENTITY_TOL = 1e-6  # G1
C1_BAND = {"CC_REGULAR": 2.94}


def class_hourly(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """Model per-class hourly MW from a bundle's P1 class sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return {
        k: g.sort_values("hour")["mw"].to_numpy(float)[:8760]
        for k, g in df.groupby("klass")
    }


def system_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """Model hourly system frame (price/demand/slack/dump) from a P1 sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"]


def served_demand(bundle: Path, year: int) -> np.ndarray:
    """Total served demand MW per hour, summed over zones."""
    df = system_hourly(bundle, year)
    return df.groupby("hour")["demand"].sum().reindex(range(8760)).to_numpy(float)


def main(argv: list[str] | None = None) -> int:
    """Print the G1-G6 verdicts from the two bundles' committed sidecars."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--arm", type=Path, required=True)
    args = parser.parse_args(argv)

    print(f"control = {args.control}\narm     = {args.arm}")

    # ---- G1: 2023 is the zero-delta control (the screen is a no-op there) ----
    print("\n=== G1 — control identity (2023: the screen is a proven no-op) ===")
    g1_ok = True
    for year in YEARS:
        ctl, arm = class_hourly(args.control, year), class_hourly(args.arm, year)
        worst_class, worst = 0.0, ""
        for klass in sorted(set(ctl) | set(arm)):
            a = arm.get(klass, np.zeros(8760))
            c = ctl.get(klass, np.zeros(8760))
            d = float(np.abs(a - c).max())
            if d > worst_class:
                worst_class, worst = d, klass
        cs, as_ = system_hourly(args.control, year), system_hourly(args.arm, year)
        key = ["zone", "hour"]
        merged = cs[[*key, "price"]].merge(as_[[*key, "price"]], on=key, suffixes=("_c", "_a"))
        dprice = float((merged["price_a"] - merged["price_c"]).abs().max())
        tag = ""
        if year == 2023:
            ok = worst_class < IDENTITY_TOL and dprice < IDENTITY_TOL
            g1_ok &= ok
            tag = "   <- CONTROL YEAR: " + ("PASS" if ok else "**FAIL**")
        print(
            f"  {year}: max |d class MW| {worst_class:12.6f} ({worst or '-'})"
            f"   max |d price| {dprice:10.6f} $/MWh{tag}"
        )
    print(f"  G1 = {'PASS' if g1_ok else 'FAIL — everything below is void'}")

    # ---- G2: no zero-load hours remain ----
    print("\n=== G2 — repair landed (hours with total served demand == 0) ===")
    g2_ok = True
    for year in YEARS:
        nc = int((served_demand(args.control, year) == 0.0).sum())
        na = int((served_demand(args.arm, year) == 0.0).sum())
        g2_ok &= na == 0
        print(f"  {year}: control {nc} -> arm {na}")
    print(f"  G2 = {'PASS' if g2_ok else 'FAIL'}")

    # ---- G3: level neutrality ----
    print("\n=== G3 — level neutrality (served energy rises by the wedge only) ===")
    g3_ok = True
    for year in YEARS:
        dc = served_demand(args.control, year).sum() / 1e6
        da = served_demand(args.arm, year).sum() / 1e6
        exp = EXPECTED_WEDGE_TWH[year]
        got = da - dc
        ok = abs(got - exp) <= max(WEDGE_TOL * max(exp, 1e-9), 1e-6)
        g3_ok &= ok
        print(
            f"  {year}: served {dc:8.4f} -> {da:8.4f} TWh   d {got:+.5f}"
            f"   expected {exp:+.5f}   {'PASS' if ok else '**FAIL**'}"
        )
    print(f"  G3 = {'PASS' if g3_ok else 'FAIL'}")

    # ---- G4: per-class energy, C1 protection ----
    print("\n=== G4 — per-class energy TWh (C1 protection) ===")
    for year in YEARS:
        ctl, arm = class_hourly(args.control, year), class_hourly(args.arm, year)
        print(f"  -- {year}")
        for klass in sorted(set(ctl) | set(arm)):
            c = ctl.get(klass, np.zeros(8760)).sum() / 1e6
            a = arm.get(klass, np.zeros(8760)).sum() / 1e6
            if abs(a - c) < 5e-5 and klass not in C1_BAND:
                continue
            note = f"   (C1 band +-{C1_BAND[klass]})" if klass in C1_BAND else ""
            print(f"     {klass:<12}{c:8.4f} -> {a:8.4f}   d {a - c:+.5f}{note}")

    # ---- G5/G6: reported, not gated ----
    print("\n=== G5/G6 — reported (C3c tail, scarcity, and the item-9 statistic) ===")
    for year in YEARS:
        rows = []
        for name, b in (("control", args.control), ("arm", args.arm)):
            s = system_hourly(b, year)
            over = int((s.groupby("hour")["price"].max() > 300.0).sum())
            rows.append(
                (name, over, float(s["slack"].sum()), float(s["dump"].sum()),
                 _r(model_import(b, year), measured_import(year)))
            )
        (_, oc, sc, dc, rc), (_, oa, sa, da, ra) = rows
        print(
            f"  {year}: h>$300 {oc} -> {oa}   slack {sc:.1f} -> {sa:.1f} MWh"
            f"   dump {dc:.1f} -> {da:.1f} MWh   import r_hr {rc:.3f} -> {ra:.3f}"
        )

    print(
        f"\nVERDICT: G1 {'PASS' if g1_ok else 'FAIL'} | "
        f"G2 {'PASS' if g2_ok else 'FAIL'} | G3 {'PASS' if g3_ok else 'FAIL'}"
    )
    return 0 if (g1_ok and g2_ok and g3_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
