"""NYISO phase 0 (zero LP): what fuel price does each class actually face, year over year?

Builds on the exact within-plant band identity (scripts/probes/nyiso241_fixed_wedge.py):

    energy(plant, hour) = (mc(b_hi) - mc(b_lo)) / (mult_hi - mult_lo) = HR_base(plant) * F(plant, hour)

Taking the SAME plant in two years cancels ``HR_base`` whenever the plant's binned heat rate is
stable, so the ratio is a clean read of the delivered fuel price the model charged that plant:

    energy(plant, 2023) / energy(plant, 2022)  =  F(plant, 2023) / F(plant, 2022)

The hub itself (Transco Zone 6 NY) fell 6.86 -> 1.98 $/MMBtu, a ratio of 0.289. A class whose
plants reproduce that ratio is being charged the hub. A class whose ratio is materially HIGHER is
being charged the hub PLUS something that does not fall with it — an LDC transport charge, a
CT-specific basis, or an oil cap — and that non-falling component is exactly the kind of term that
can reorder a merit stack when gas collapses, which a multiplicative band multiplier cannot.

This matters because the successor object is CT_PEAKER's collapse from 2023 (2.43 -> 0.25 TWh
against a flat actual) and the recommended lever is a multiplicative band. The probe asks whether
the lever is aimed at the term that actually moves.

Reads only committed artifacts (the nyiso-240 MER legs). No LP is solved; nothing is swept.

Usage:
    python3 scripts/probes/nyiso241_fuel_basis_ratio.py \
        --legs results/calibration/nyiso_mer_2026-09-19_{2022,2023,2024,2025} \
        --out results/calibration/_nyiso241_fuel_basis_ratio.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

# Widest band pair per class whose two bands both resolve to real LP rows. Quoted from the
# registered `_NYISO_OFFER_CURVE`; nothing is re-derived (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`).
IDENT_PAIRS: dict[str, tuple[str, str, float, float]] = {
    "CT_PEAKER": ("peak", "econlo", 4.00, 1.00),
    "ST_GAS": ("peak", "econhi", 4.20, 1.13),
    "CC_REGULAR": ("peak", "econc05", 2.25, 1.00),
    "CC_CHP": ("peak", "econc05", 2.25, 1.24),
}

# Delivered-gas hub the NYISO fossil fleet prices against, annual means from the committed
# daily series data/raw/gas-prices/transco_z6_ny_daily.csv. Quoted as the REFERENCE the class
# ratios are read against; no value from it enters any config.
HUB_ANNUAL = {2022: 6.860, 2023: 1.984, 2024: 2.104, 2025: 4.086}


def _is_plant_token(tok: str) -> bool:
    """True for the ``p<digits>`` plant segment of an LP row id.

    Tested on the digits rather than the leading ``p`` alone: the band name ``peak`` also
    starts with ``p``, and reading it as a plant token silently drops the entire peak band.
    """
    return len(tok) > 1 and tok[0] == "p" and tok[1:].isdigit()


def parse_parts(unit_id: str) -> tuple[str, str]:
    """Return (plant token, band) for an LP row id ``<CLASS>_<ZONE>_p<plant>_<band>``."""
    tail = unit_id.rsplit("_", 1)[-1]
    if _is_plant_token(tail):
        return tail, ""
    head = unit_id.rsplit("_", 2)
    return (head[-2] if len(head) >= 2 else ""), tail


def energy_per_plant(leg: Path, year: int) -> dict[str, pd.Series]:
    """Per class, the annual-mean ``HR_base * F`` for every plant with both identifying bands."""
    unit = pd.read_parquet(
        leg / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "plant_group", "zone", "hour", "mc", "cap_mw"],
    )
    unit = unit[unit["pass"] == "P1"].copy()
    parts = [parse_parts(uid) for uid in unit["unit_id"]]
    unit["plant"] = [p for p, _ in parts]
    unit["band"] = [b for _, b in parts]

    out: dict[str, pd.Series] = {}
    for klass, (b_hi, b_lo, m_hi, m_lo) in IDENT_PAIRS.items():
        sub = unit[unit["plant_group"] == klass]
        if sub.empty:
            continue
        wide = sub.pivot_table(index=["plant", "hour"], columns="band", values="mc")
        if b_hi not in wide.columns or b_lo not in wide.columns:
            continue
        pair = wide[[b_hi, b_lo]].dropna()
        if pair.empty:
            continue
        energy = (pair[b_hi] - pair[b_lo]) / (m_hi - m_lo)
        out[klass] = energy.groupby(level="plant").mean()
    return out


def zone_of_plants(leg: Path, year: int) -> pd.Series:
    """Map each plant token to the zone its LP rows sit in."""
    unit = pd.read_parquet(
        leg / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "zone", "hour"],
    )
    unit = unit[(unit["pass"] == "P1") & (unit["hour"] == 0)].copy()
    unit["plant"] = [parse_parts(uid)[0] for uid in unit["unit_id"]]
    return unit.groupby("plant")["zone"].first()


def main() -> None:
    """Compare each class's per-plant fuel charge against the hub, year over year."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    per_year: dict[int, dict[str, pd.Series]] = {}
    zones: dict[int, pd.Series] = {}
    for leg_str in args.legs:
        leg = Path(leg_str)
        year = int(leg.name.rsplit("_", 1)[-1])
        per_year[year] = energy_per_plant(leg, year)
        zones[year] = zone_of_plants(leg, year)

    years = sorted(per_year)
    base = years[0]
    report: dict[str, dict] = {
        "hub_annual_usd_mmbtu": HUB_ANNUAL,
        "base_year": base,
        "classes": {},
    }

    for klass in IDENT_PAIRS:
        rows: dict[str, dict] = {}
        b_series = per_year[base].get(klass)
        if b_series is None:
            continue
        for year in years:
            series = per_year[year].get(klass)
            if series is None:
                continue
            common = b_series.index.intersection(series.index)
            ratio = (
                (series[common] / b_series[common])
                .replace([np.inf, -np.inf], np.nan)
                .dropna()
            )
            hub_ratio = HUB_ANNUAL[year] / HUB_ANNUAL[base]
            rows[str(year)] = {
                "plants": int(len(ratio)),
                "energy_at_band_1_mean": float(series[common].mean()),
                "plant_ratio_median": float(ratio.median())
                if len(ratio)
                else float("nan"),
                "hub_ratio": hub_ratio,
                "excess_over_hub": float(ratio.median() / hub_ratio)
                if len(ratio) and hub_ratio
                else float("nan"),
            }
        report["classes"][klass] = rows

    # Zone cut for CT_PEAKER: a downstate LDC transport or CT basis charge would show up as a
    # zone-specific excess rather than a fleet-wide one.
    ct_zone: dict[str, dict] = {}
    if "CT_PEAKER" in per_year[base]:
        b_series = per_year[base]["CT_PEAKER"]
        for year in years:
            series = per_year[year].get("CT_PEAKER")
            if series is None:
                continue
            common = b_series.index.intersection(series.index)
            ratio = (series[common] / b_series[common]).replace(
                [np.inf, -np.inf], np.nan
            )
            zmap = zones[year].reindex(common)
            frame = pd.DataFrame(
                {"ratio": ratio.to_numpy(), "zone": zmap.to_numpy()}, index=common
            )
            hub_ratio = HUB_ANNUAL[year] / HUB_ANNUAL[base]
            ct_zone[str(year)] = {
                str(z): {
                    "plants": int(g["ratio"].notna().sum()),
                    "ratio_median": float(g["ratio"].median()),
                    "excess_over_hub": float(g["ratio"].median() / hub_ratio),
                }
                for z, g in frame.groupby("zone")
                if g["ratio"].notna().any()
            }
    report["ct_peaker_by_zone"] = ct_zone

    for klass, rows in report["classes"].items():
        print(f"=== {klass} ===")
        for year, row in rows.items():
            print(
                f"  {year}  HR*F {row['energy_at_band_1_mean']:>7.2f} $/MWh | plant ratio vs {base} "
                f"{row['plant_ratio_median']:.3f}  hub ratio {row['hub_ratio']:.3f}  "
                f"-> charged {row['excess_over_hub']:.2f}x the hub's move  (n={row['plants']})"
            )
    print("\n=== CT_PEAKER by zone (ratio vs base year) ===")
    for year, zrows in report["ct_peaker_by_zone"].items():
        parts = " ".join(
            f"{z}:{d['ratio_median']:.3f}({d['excess_over_hub']:.2f}x)"
            for z, d in sorted(zrows.items())
        )
        print(f"  {year}  {parts}")

    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
