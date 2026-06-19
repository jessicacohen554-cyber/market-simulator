"""CAISO RA must-offer floor — before/after diagnostics from a dispatch bundle.

Reads a calibration bundle's ``dispatch/<year>_P2.parquet`` and prints the
metrics the floor targets: gas TWh (vs EIA-923), spring-midday gas MW (vs the
measured EIA-930 NG: NG), net import / export-hour share, and the monthly /
spring-tail LMP (vs the actual RT). Pass two bundles to print a side-by-side.

Usage:
    python scripts/_caiso_floor_ab.py <bundle_dir> [<bundle_dir2>] --year 2024
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia_loader import measured_gas_floor_profile  # noqa: E402

GAS_FUELS = ("gas_cc", "gas_ct", "gas_st")
SPRING = (4, 5)
MIDDAY = (9, 16)  # [start, end)


def _clock(hours: int, year: int):
    c = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    return c.month.to_numpy(), c.hour.to_numpy()


def analyze(bundle: Path, year: int) -> dict:
    df = pd.read_parquet(bundle / "dispatch" / f"{year}_P2.parquet")
    hours = int(df["hour"].max()) + 1
    month, hod = _clock(hours, year)

    # System LMP (internal zones share one price under the uncongested pipe).
    zl = df[df.zone != "WECC_import"][["zone", "hour", "lmp"]].drop_duplicates()
    lmp = zl.groupby("hour")["lmp"].mean().reindex(range(hours)).to_numpy()

    # Gas generation by hour (MW) and annual TWh.
    gas = df[df.fuel.isin(GAS_FUELS)]
    gas_hourly = gas.groupby("hour")["mw"].sum().reindex(
        range(hours), fill_value=0.0
    ).to_numpy()
    gas_twh = float(gas["mw"].sum()) / 1e6

    # Net interchange at the priced node: +import / -export (MW/hour).
    imp = df[(df.zone == "WECC_import") & (df.fuel == "import")]
    net_import = imp.groupby("hour")["mw"].sum().reindex(
        range(hours), fill_value=0.0
    ).to_numpy()

    spring_mid = np.isin(month, SPRING) & (hod >= MIDDAY[0]) & (hod < MIDDAY[1])
    monthly_lmp = [float(lmp[month == m].mean()) for m in range(1, 13)]

    ng = measured_gas_floor_profile("CAISO", year, hours, 50.0)
    eia930_spring_mid = (
        float(np.asarray(ng)[spring_mid].mean()) if ng is not None else float("nan")
    )

    return {
        "year": year,
        "gas_twh": gas_twh,
        "net_import_twh": float(net_import.sum()) / 1e6,
        "export_hours_pct": 100.0 * float((net_import < 0).mean()),
        "spring_mid_gas_mw": float(gas_hourly[spring_mid].mean()),
        "spring_mid_import_mw": float(net_import[spring_mid].mean()),
        "eia930_spring_mid_ng_mw": eia930_spring_mid,
        "lmp_mean": float(lmp.mean()),
        "lmp_min": float(lmp.min()),
        "lmp_p5": float(np.percentile(lmp, 5)),
        "spring_lmp_mean": float(lmp[np.isin(month, SPRING)].mean()),
        "spring_lmp_min": float(lmp[np.isin(month, SPRING)].min()),
        "spring_lmp_p5": float(np.percentile(lmp[np.isin(month, SPRING)], 5)),
        "monthly_lmp": monthly_lmp,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bundles", nargs="+", type=Path)
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()

    al = json.load(open(REPO / "data/raw/_validation-source/actual_lmp.json"))["CAISO"]
    cr = json.load(open(REPO / "data/raw/_validation-source/calibration_reference.json"))
    ref_gas = sum(
        cr["isos"]["CAISO"][str(args.year)]["generation_twh"].get(f, 0.0)
        for f in GAS_FUELS
    )
    rt_mon = al.get(str(args.year), {}).get("rt_mon")
    da_pct = al.get(str(args.year), {}).get("da_pct", {})

    results = [analyze(b, args.year) for b in args.bundles]
    labels = [b.name for b in args.bundles]

    print(f"\n=== CAISO {args.year} — RA floor A/B ===")
    print(f"EIA-923 gas (TWh): {ref_gas:.1f}")
    if da_pct:
        print(f"actual da_pct: min {da_pct.get('min')}, p5 {da_pct.get('p5')}")

    def row(name, key, fmt="{:.1f}"):
        vals = "  ".join(fmt.format(r[key]) for r in results)
        print(f"  {name:<26} " + vals)

    print("  " + " " * 26 + "  ".join(f"{l[:18]:>18}" for l in labels))
    row("gas TWh (vs %.1f)" % ref_gas, "gas_twh")
    row("net import TWh", "net_import_twh")
    row("export hours %", "export_hours_pct")
    row("spring-mid gas MW", "spring_mid_gas_mw")
    row("spring-mid import MW", "spring_mid_import_mw")
    print(f"  (EIA-930 spring-mid NG: NG MW: "
          f"{results[0]['eia930_spring_mid_ng_mw']:.0f})")
    row("LMP mean", "lmp_mean")
    row("LMP min", "lmp_min")
    row("LMP p5", "lmp_p5")
    row("spring LMP mean", "spring_lmp_mean")
    row("spring LMP min", "spring_lmp_min")
    row("spring LMP p5", "spring_lmp_p5")

    if rt_mon:
        print("\n  monthly LMP vs actual RT:")
        mons = "JFMAMJJASOND"
        hdr = "  mon  " + "  ".join(f"{l[:10]:>10}" for l in labels) + "    actual"
        print(hdr)
        for i in range(12):
            cells = "  ".join(f"{r['monthly_lmp'][i]:>10.1f}" for r in results)
            print(f"   {mons[i]}   {cells}    {rt_mon[i]:>6.1f}")


if __name__ == "__main__":
    main()
