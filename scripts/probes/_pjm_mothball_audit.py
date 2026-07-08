"""DIAGNOSTIC (data-only): PJM phantom-capacity audit via EIA-923 zero-gen.

Cross the model's operable PJM fossil fleet against EIA-923 annual net
generation to list fossil units carried at full capacity that generated ~0 in
2024/2025 (mothballed / economic-idle-all-year) or have an EIA-860 planned
retirement inside the year. Quantifies phantom MW at summer peak. Throwaway.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

FOSSIL_TECH = (
    "Conventional Steam Coal",
    "Natural Gas Fired Combined Cycle",
    "Natural Gas Fired Combustion Turbine",
    "Natural Gas Steam Turbine",
    "Petroleum Liquids",
    "Natural Gas Internal Combustion Engine",
)


def _operable() -> pd.DataFrame:
    df = pd.read_parquet(_REPO / "data/raw/eia-860/eia860_generators.parquet")
    df = df[df["balancing_authority_code"].astype(str).str.strip() == "PJM"].copy()
    df["nameplate"] = pd.to_numeric(df["nameplate_capacity_mw"], errors="coerce")
    df["net_summer"] = pd.to_numeric(df.get("net_summer_capacity_mw"), errors="coerce")
    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce")
    return df


def _gen923() -> pd.DataFrame:
    g = pd.read_parquet(
        _REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
    )
    return g


def main() -> int:
    op = _operable()
    foss = op[op["technology"].isin(FOSSIL_TECH)].copy()
    print(
        f"PJM operable fossil gens: {len(foss)}, "
        f"nameplate {foss['nameplate'].sum() / 1e3:,.1f} GW, "
        f"net-summer {foss['net_summer'].sum() / 1e3:,.1f} GW"
    )
    # planned retirements within backcast window
    foss["ry"] = pd.to_numeric(foss["planned_retirement_year"], errors="coerce")
    for y in (2023, 2024, 2025):
        sub = foss[foss["ry"] == y]
        print(
            f"  planned_retirement_year=={y}: {len(sub)} gens, "
            f"{sub['nameplate'].sum() / 1e3:.2f} GW (would be COD-ramped off mid-year)"
        )

    g = _gen923()
    ycol = "year" if "year" in g.columns else [c for c in g.columns if "year" in c][0]
    plant_cap = foss.groupby("plant_id")["net_summer"].sum()
    for year in (2024, 2025):
        gy = g[pd.to_numeric(g[ycol], errors="coerce") == year]
        # PJM plants only, sum annual net gen per plant
        gy = gy[gy["ba_code"].astype(str).str.strip() == "PJM"]
        ann = gy.groupby("plant_id")["netgen_annual_mwh"].sum()
        print(f"\n=== {year}: fossil PLANTS with ~0 EIA-923 net gen ===")
        rows = []
        for pid, cap in plant_cap.items():
            if cap <= 5.0:
                continue
            gen = float(ann.get(pid, 0.0))
            cf = gen / (cap * 8760.0) if cap > 0 else 0.0
            if cf < 0.01:  # <1% CF all year → mothball / idle candidate
                nm = foss[foss["plant_id"] == pid]["plant_name"].iloc[0]
                rows.append((pid, nm, cap, gen, cf))
        rows.sort(key=lambda r: -r[2])
        total_mw = sum(r[2] for r in rows)
        print(f"  {len(rows)} plants, {total_mw / 1e3:.2f} GW net-summer, CF<1%:")
        for pid, nm, cap, gen, cf in rows[:40]:
            print(
                f"    plant {int(pid):>6} {str(nm)[:34]:34s} "
                f"cap={cap:7.1f}MW gen={gen / 1e3:8.1f}GWh CF={cf * 100:4.2f}%"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
