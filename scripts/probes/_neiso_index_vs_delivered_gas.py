"""Reproducer for ``docs/FINDING-neiso-index-vs-delivered-gas-2026-09-09.md``.

Checks four committed measured sources against each other to settle whether
NEISO's 3.2x January-2023 gap between the ISO-NE published Algonquin Citygate
index and EIA ``N3045`` delivered-to-electric-power is a real level defect in
the keeper or an artifact of the EIA survey's respondent panel.

The decisive test is physical: monthly mean realised RT LMP divided by the
candidate gas price is the **implied marginal heat rate**, and a value below
NEISO's most efficient combined cycle (~6.3 MMBtu/MWh) cannot be produced by
any heat engine. ZERO LP; nothing under ``data/raw`` is written.

Usage::

    python3 scripts/probes/_neiso_index_vs_delivered_gas.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

GAS = ROOT / "data/raw/gas-prices"
# EIA heat content of natural gas, 1.036 MMBtu/Mcf (FINDING-xiso-fuelvintage §3).
MCF_TO_MMBTU = 1.036
# ISO-860 gas-capacity footprint weights, data/raw/reference/iso-gas-capacity-state-weights.csv.
NE_WEIGHTS = {"MA": 0.376, "CT": 0.325, "RI": 0.120, "ME": 0.095, "NH": 0.084}
# NEISO's most efficient combined cycle, the physical floor for a marginal heat rate.
CC_FLOOR_MMBTU_PER_MWH = 6.3
# EIA-930 gas fleet average heat rate, used only to size the F923 sample share.
FLEET_HEAT_RATE = 7.8
YEARS = range(2019, 2026)


def ne_blend() -> pd.Series:
    """Return the capacity-weighted New England N3045 monthly level, $/MMBtu.

    Returns:
        A Series indexed by ``(year, month)``.
    """
    n = pd.read_csv(GAS / "eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv")
    wide = (
        n[n.state.isin(NE_WEIGHTS)]
        .pivot_table(index=["year", "month"], columns="state", values="price_usd_mcf")
        / MCF_TO_MMBTU
    )
    out = {}
    for key, row in wide.iterrows():
        present = {s: row[s] for s in NE_WEIGHTS if s in row and pd.notna(row[s])}
        if not present:
            continue
        total_w = sum(NE_WEIGHTS[s] for s in present)
        out[key] = sum(row[s] * NE_WEIGHTS[s] for s in present) / total_w
    return pd.Series(out)


def monthly_rt_lmp() -> pd.Series:
    """Return the ISO-NE hub monthly mean RT LMP, $/MWh.

    Returns:
        A Series indexed by ``(year, month)``.
    """
    out = {}
    for year in YEARS:
        d = pd.read_excel(
            ROOT / f"data/raw/lmp-data/NEISO/{year}_smd_hourly.xlsx", sheet_name="ISO NE CA"
        )
        d["m"] = pd.to_datetime(d["Date"]).dt.month
        for m, v in d.groupby("m")["RT_LMP"].mean().items():
            out[(year, int(m))] = float(v)
    return pd.Series(out)


def main() -> None:
    """Run every check in the finding and print the tables it cites."""
    index = pd.read_csv(GAS / "isone_ma_gas_index_monthly.csv").set_index(["year", "month"])[
        "ma_gas_index_usd_mmbtu"
    ]
    blend = ne_blend()
    lmp = monthly_rt_lmp()
    keys = [k for k in blend.index if k in index.index and k in lmp.index and 2019 <= k[0] <= 2025]

    ihr_idx = np.array([lmp[k] / index[k] for k in keys])
    ihr_n30 = np.array([lmp[k] / blend[k] for k in keys])

    print("=== SECTION 2 — implied marginal heat rate, MMBtu/MWh (84 months) ===")
    print(f"physical floor (NEISO best CC) = {CC_FLOOR_MMBTU_PER_MWH}")
    for lab, x in (("ISO-NE AGT index", ihr_idx), ("EIA N3045 blend", ihr_n30)):
        print(
            f"  {lab:18s} median {np.median(x):6.2f}  p05 {np.quantile(x, .05):6.2f}"
            f"  p95 {np.quantile(x, .95):6.2f}   below floor: {(x < CC_FLOOR_MMBTU_PER_MWH).sum():2d}"
            f"/{len(x)}   below 4.0: {(x < 4.0).sum()}"
        )
    k = (2023, 1)
    print(
        f"\n  {k}: LMP {lmp[k]:.2f} / index {index[k]:.2f} = {lmp[k] / index[k]:.2f}"
        f"   |   / N3045 {blend[k]:.2f} = {lmp[k] / blend[k]:.2f}  <-- IMPOSSIBLE"
    )
    print(
        "  log-price correlation:  index"
        f" {np.corrcoef(np.log([lmp[k] for k in keys]), np.log([index[k] for k in keys]))[0, 1]:.4f}"
        f"   N3045 {np.corrcoef(np.log([lmp[k] for k in keys]), np.log([blend[k] for k in keys]))[0, 1]:.4f}"
    )

    print("\n=== SECTION 3a — January 2023 vs January 2025 ===")
    gen = pd.read_parquet(ROOT / "data/raw/ISNE_fueltype.parquet")
    gen["y"], gen["m"] = gen.period.dt.year, gen.period.dt.month
    for year in (2023, 2025, 2022):
        jan = gen[(gen.y == year) & (gen.m == 1)]
        ng = jan[jan.type_name == "Natural Gas"].value_mwh.sum()
        print(
            f"  {year}-01  N3045 {blend[(year, 1)]:6.3f}  index {index[(year, 1)]:6.2f}"
            f"  LMP {lmp[(year, 1)]:7.2f}  gas share {ng / jan.value_mwh.sum() * 100:5.1f}%"
        )

    print("\n=== SECTION 3b — Algonquin daily prints, January 2023 ===")
    agt = pd.read_csv(GAS / "algonquin_citygate_daily.csv")
    print(agt[agt.date.str.startswith("2023-01")].to_string(index=False))

    print("\n=== SECTION 3c — the disclosed EIA-923 New England gas receipt sample ===")
    f923 = pd.read_parquet(ROOT / "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet")
    ne = f923[
        f923.state.isin(["MA", "CT", "RI", "ME", "NH", "VT"]) & (f923.fuel_group == "Natural Gas")
    ]
    jan23 = ne[(ne.year == 2023) & (ne.month == 1)]
    print(jan23.to_string(index=False))
    burn = (
        gen[(gen.y == 2023) & (gen.m == 1) & (gen.type_name == "Natural Gas")].value_mwh.sum()
        * FLEET_HEAT_RATE
    )
    print(f"  sample {jan23.quantity.sum():,.0f} MMBtu = {jan23.quantity.sum() / burn * 100:.4f}% of the ~{burn:,.0f} MMBtu ISO-NE burned")
    nat = f923[(f923.fuel_group == "Natural Gas") & (f923.year == 2023) & (f923.month == 1)]
    print(f"  national same month: {nat.plant_id.nunique()} plants / {nat.quantity.sum():,.0f} MMBtu")

    print("\n=== SECTION 3d — cross-state dispersion and the sign of the wedge ===")
    n = pd.read_csv(GAS / "eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv")
    wide = (
        n[n.state.isin(NE_WEIGHTS)]
        .pivot_table(index=["year", "month"], columns="state", values="price_usd_mcf")
        / MCF_TO_MMBTU
    )
    for key in [(2023, 1), (2023, 5), (2024, 3)]:
        r = wide.loc[key]
        print(f"  {key}  MA {r.MA:6.2f}  CT {r.CT:5.2f}  RI {r.RI:5.2f}   MA/CT {r.MA / r.CT:.2f}x")
    ratio = np.array([blend[k] / index[k] for k in keys])
    print(f"  median blend/index {np.median(ratio):.3f}; months BELOW the spot index: {(ratio < 1).sum()}/{len(ratio)}")


if __name__ == "__main__":
    main()
