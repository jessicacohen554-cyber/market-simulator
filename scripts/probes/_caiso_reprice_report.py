"""Compact CAISO reprice acceptance metrics for a solved bundle.

Reads a calibration bundle and prints, per year: modeled net interchange (TWh)
vs EIA-930 and %, import-hour share vs measured, negative-price-hour count,
gas TWh vs EIA-923/930, and the load-weighted average price. Used to track the
P9/P12 import-reprice iteration.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


# EIA benchmarks from the calibration log (CAISO 2 priced-ix entry).
EIA930_IX = {2023: -28.87, 2024: -32.38, 2025: -36.16}  # net interchange TWh
MEAS_IMPORT_SHARE = {2023: 85.9, 2024: 89.0, 2025: 90.9}  # % of hours importing
EIA923_GAS = {2023: 76.04, 2024: 67.68, 2025: 55.18}
EIA930_GAS = {2023: 88.01, 2024: 85.37, 2025: 79.03}


def analyze(bundle: Path) -> None:
    system = pd.read_parquet(bundle / "system.parquet")
    print(f"\n{'=' * 78}\nbundle: {bundle}\n{'=' * 78}")
    print(
        f"  {'yr':>4} {'net ix TWh':>11} {'vs930':>7} {'%':>5} "
        f"{'imp%':>6} {'meas':>5} {'neg-hrs':>7} {'gas TWh':>8} "
        f"{'v923%':>6} {'avgP':>6}"
    )
    for year in sorted(system["year"].unique()):
        sysd = system[system["year"] == year]
        last = sorted(sysd["pass"].unique())[-1]
        sysd = sysd[sysd["pass"] == last]
        disp_path = bundle / "dispatch" / f"{year}_{last}.parquet"
        disp = pd.read_parquet(disp_path)

        node = disp[disp["fuel"] == "import"]
        model_ix = -(
            node.groupby("hour", observed=True)["mw"]
            .sum()
            .sort_index()
            .to_numpy(dtype=float)
        )
        m_twh = model_ix.sum() / 1e6
        imp_share = 100.0 * (model_ix < 0).mean()

        gas = disp[disp["fuel"].isin(["gas_cc", "gas_ct", "gas_st"])]["mw"].sum() / 1e6

        # load-weighted price + negative-hour count (min zonal price < 0)
        p = sysd.pivot_table(
            index="hour", columns="zone", values="price", observed=True
        )
        d = sysd.pivot_table(
            index="hour", columns="zone", values="demand", observed=True
        )
        lwp = (p * d).sum(axis=1) / d.sum(axis=1)
        neg_hrs = int((p.min(axis=1) < 0).sum())

        ix930 = EIA930_IX.get(int(year))
        pct = 100.0 * m_twh / ix930 if ix930 else float("nan")
        g923 = EIA923_GAS.get(int(year))
        gpct = 100.0 * (gas - g923) / g923 if g923 else float("nan")
        print(
            f"  {int(year):>4} {m_twh:>+11.2f} {ix930:>+7.1f} {pct:>5.0f} "
            f"{imp_share:>6.1f} {MEAS_IMPORT_SHARE.get(int(year), 0):>5.1f} "
            f"{neg_hrs:>7d} {gas:>8.2f} {gpct:>+6.1f} {lwp.mean():>6.1f}"
        )


if __name__ == "__main__":
    for b in sys.argv[1:] or ["results/calibration/caiso_1_priced_ix"]:
        analyze(Path(b))
