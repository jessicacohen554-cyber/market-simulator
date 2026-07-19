"""miso-76 A/B scorer — pre-registered bands B1/B2/R2/R3 + B4 (charter §5-§6).

Reads the two solved bundles' system.parquet (main = loss surface on, base =
same-box miso-75 replica), computes each benchmarked Midwest pair-year's model
annual-mean separation vs Indiana, and gates it against the measured mean dMLC
(B1, DA basis — the derive source) within [0.5x, 1.5x]; R2 caps model
separation at 1.0x the measured RT TOTAL mean separation; R3 rejects inertness
(every pair-year move < $0.30). B2 reports total separation (incl. knock-on)
vs measured total dLMP — report-only. B4 reports the January per-zone MAE in
Indiana/East/West vs the D6 zonal actuals (miso-72's disclosed +$2 broadening)
— report-only. R1 (C3b veto) and B3 (|dC3a| <= 1.5pp watch) come from the
registration scorer, not this probe.

Run: .venv/bin/python <this> --main <bundle> --base <bundle>
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.lib import clean_io

YEARS = (2023, 2024, 2025)
REF_ZONE = "MISO-Indiana"
PAIR_ZONES = ("MISO-West", "MISO-Illinois", "MISO-East")
ZONE_HUBS = {
    "MISO-West": ["MINN.HUB"],
    "MISO-Illinois": ["ILLINOIS.HUB"],
    "MISO-Indiana": ["INDIANA.HUB"],
    "MISO-East": ["MICHIGAN.HUB"],
}
B1_BAND = (0.5, 1.5)
R3_INERT_USD = 0.30

# Fixed non-leap calendar: January = hours [0, 744).
JAN_HOURS = 31 * 24


def zone_means(bundle: Path, year: int) -> pd.Series:
    """Model per-zone annual mean price (P1) for one bundle-year."""
    df = pd.read_parquet(bundle / "system.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    return df.groupby("zone")["price"].mean()


def measured_dmlc(year: int, market: str) -> dict[str, float]:
    """Measured mean d(MLC) per pair zone vs Indiana (clean lmp-components)."""
    df = clean_io.read_clean("lmp-components", iso="MISO", year=year, market=market)
    hub_mean = df.groupby("node")["mlc_usd_per_mwh"].mean()
    out = {}
    for zone, hubs in ZONE_HUBS.items():
        out[zone] = float(np.mean([hub_mean[h] for h in hubs]))
    return {z: out[z] - out[REF_ZONE] for z in PAIR_ZONES}


def measured_dlmp(year: int, market: str) -> dict[str, float]:
    """Measured mean TOTAL LMP separation per pair zone vs Indiana."""
    df = clean_io.read_clean("lmp-components", iso="MISO", year=year, market=market)
    hub_mean = df.groupby("node")["lmp_usd_per_mwh"].mean()
    out = {}
    for zone, hubs in ZONE_HUBS.items():
        out[zone] = float(np.mean([hub_mean[h] for h in hubs]))
    return {z: out[z] - out[REF_ZONE] for z in PAIR_ZONES}


def january_mae(bundle: Path, year: int) -> dict[str, float]:
    """Model January per-zone MAE vs the D6 zonal RT actuals (B4 zones)."""
    act = pd.read_parquet(
        "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
    )
    act = act[(act["year"] == year) & (act["hour"] < JAN_HOURS)]
    act_zone = act.groupby(["zone", "hour"])["rt"].mean()
    df = pd.read_parquet(bundle / "system.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1") & (df["hour"] < JAN_HOURS)]
    out = {}
    for zone in ("MISO-Indiana", "MISO-East", "MISO-West"):
        m = df[df["zone"] == zone].set_index("hour")["price"]
        a = act_zone.loc[zone]
        joined = pd.concat([m, a], axis=1, keys=["m", "a"]).dropna()
        out[zone] = float((joined["m"] - joined["a"]).abs().mean())
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--main", type=Path, required=True)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    args = ap.parse_args()

    b1_all, r2_all, moves = True, True, []
    print(
        f"{'pair':<15}{'yr':<5}{'base':>8}{'main':>8}{'move':>8}{'dMLC(DA)':>10}"
        f"{'ratio':>7}{'B1':>6}{'RTtot':>8}{'R2':>5}"
    )
    for year in args.years:
        zm_main = zone_means(args.main, year)
        zm_base = zone_means(args.base, year)
        dmlc = measured_dmlc(year, "da")
        rt_total = measured_dlmp(year, "rt")
        for zone in PAIR_ZONES:
            sep_main = float(zm_main[zone] - zm_main[REF_ZONE])
            sep_base = float(zm_base[zone] - zm_base[REF_ZONE])
            move = sep_main - sep_base
            moves.append(abs(move))
            target = dmlc[zone]
            ratio = sep_main / target if target != 0 else np.inf
            b1 = B1_BAND[0] <= ratio <= B1_BAND[1]
            b1_all &= b1
            # R2: model separation magnitude must not exceed the measured RT
            # TOTAL mean separation magnitude for the pair-year.
            r2 = abs(sep_main) <= abs(rt_total[zone]) + 1e-9
            r2_all &= r2
            print(
                f"{zone.replace('MISO-', ''):<15}{year:<5}{sep_base:>8.3f}"
                f"{sep_main:>8.3f}{move:>8.3f}{target:>10.3f}{ratio:>7.2f}"
                f"{'PASS' if b1 else 'FAIL':>6}{rt_total[zone]:>8.3f}"
                f"{'ok' if r2 else 'FAIL':>5}"
            )

    r3_inert = all(m < R3_INERT_USD for m in moves)
    print("\n=== B2 (report-only): model total separation vs measured total dLMP")
    for year in args.years:
        zm_main = zone_means(args.main, year)
        da_t, rt_t = measured_dlmp(year, "da"), measured_dlmp(year, "rt")
        for zone in PAIR_ZONES:
            print(
                f"  {zone.replace('MISO-', ''):<10}{year}  model "
                f"{float(zm_main[zone] - zm_main[REF_ZONE]):+7.3f}   "
                f"measured DA {da_t[zone]:+7.3f} / RT {rt_t[zone]:+7.3f}"
            )

    print("\n=== B4 (report-only): January MAE vs D6 zonal RT actuals")
    for year in args.years:
        mm, mb = january_mae(args.main, year), january_mae(args.base, year)
        for zone in mm:
            print(
                f"  {zone.replace('MISO-', ''):<10}{year}  base {mb[zone]:6.2f}"
                f"  main {mm[zone]:6.2f}  d {mm[zone] - mb[zone]:+.2f}"
            )

    print(
        f"\nB1 (deliverable): {'PASS' if b1_all else 'FAIL'}   "
        f"R2 (no fabricated separation): {'PASS' if r2_all else 'FAIL'}   "
        f"R3 (inert if all moves < $0.30): "
        f"{'TRIPPED - REJECT' if r3_inert else 'not inert (ok)'}"
    )


if __name__ == "__main__":
    main()
