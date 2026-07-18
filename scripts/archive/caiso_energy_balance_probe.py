"""CAISO energy-balance probe — localize the domestic over-generation drift.

Given a solved calibration bundle, decompose the system energy balance for each
year and reconcile it against the EIA-930 CISO measured series:

    domestic_gen + gross_import - gross_export - dump - storage_loss = demand

Reports model domestic gen, gross/net interchange, dump (curtailment), storage
round-trip loss, and demand, vs the EIA-930 measured demand and net interchange
(so the +4-5 TWh domestic over-gen of RC#1 can be attributed to a sink: dump,
exports, storage loss, or a demand-basis mismatch).

Usage:
    .venv/bin/python scripts/archive/caiso_energy_balance_probe.py BUNDLE_DIR \
        --year 2023 2024 2025 [--pass P1]
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

from market_sim.data.eia_loader import (  # noqa: E402
    _eia_hourly_frame_filled,
    _load_caiso_hourly_demand,
)

_TWH = 1e6  # MWh per TWh


def _caiso_net_interchange(year: int) -> np.ndarray | None:
    """Return EIA-930 CISO net interchange (MW, +ve = net export), or None."""
    frame = _eia_hourly_frame_filled("CISO", year)
    if frame is None or "Total interchange" not in frame.columns:
        return None
    ti = pd.to_numeric(frame["Total interchange"], errors="coerce")
    return ti.interpolate().bfill().ffill().to_numpy(dtype=float)


def _twh(series_mwh: np.ndarray) -> float:
    return float(np.asarray(series_mwh, dtype=float).sum()) / _TWH


def probe_year(bundle: Path, year: int, pass_label: str) -> None:
    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_{pass_label}.parquet")
    sys_path = bundle / "system.parquet"
    sysf = None
    if sys_path.exists():
        sysf = pd.read_parquet(sys_path)
        sysf = sysf[(sysf["year"] == year) & (sysf["pass"] == pass_label)]
        if not len(sysf):
            sysf = None

    is_import = disp["fuel"] == "import"
    imp = disp[is_import]
    dom = disp[~is_import]

    gross_import = _twh(imp["mw"].clip(lower=0.0))
    gross_export = _twh((-imp["mw"]).clip(lower=0.0))
    net_import = gross_import - gross_export  # +ve = net import

    # Domestic gen by fuel family.
    by_fuel = dom.groupby("fuel", observed=True)["mw"].sum() / _TWH
    domestic_gen = float(by_fuel.sum())

    # Storage round-trip loss (charge - discharge, all storage techs).
    stor_loss = 0.0
    stor_path = bundle / "storage.parquet"
    if stor_path.exists():
        st = pd.read_parquet(stor_path)
        st = st[(st["year"] == year) & (st["pass"] == pass_label)]
        if len(st):
            chg_col = "charge_mw" if "charge_mw" in st else "charge"
            dis_col = "discharge_mw" if "discharge_mw" in st else "discharge"
            stor_loss = _twh(st[chg_col]) - _twh(st[dis_col])

    if sysf is not None:
        demand = _twh(sysf["demand"])
        slack = _twh(sysf["slack"])
    else:
        # Fallback: model served demand == EIA-930 CISO net load (td_loss=0).
        _dem = _load_caiso_hourly_demand(year)
        demand = _twh(_dem) if _dem is not None else float("nan")
        slack = 0.0

    # Total injection from the dispatch frame already nets storage dis - chg only
    # if storage rows are present in dispatch; they are NOT (separate frame), so
    # add storage net injection (= -stor_loss net of throughput) via dump residual.
    total_inj = domestic_gen + net_import
    # Energy balance: total_inj + slack - dump - stor_loss = demand
    dump = total_inj + slack - stor_loss - demand

    # EIA-930 measured.
    eia_demand_mw = _load_caiso_hourly_demand(year)
    eia_demand = _twh(eia_demand_mw) if eia_demand_mw is not None else float("nan")
    eia_ix = _caiso_net_interchange(year)  # +ve = net export
    eia_net_import = -_twh(eia_ix) if eia_ix is not None else float("nan")
    # EIA implied domestic net gen = demand - net_import (curtailment small).
    eia_dom = eia_demand - eia_net_import

    print(f"\n=== CAISO {year} energy balance ({pass_label}) {bundle.name} ===")
    print(f"  MODEL demand (served)        {demand:8.2f} TWh")
    print(
        f"  EIA-930 demand (net load)    {eia_demand:8.2f} TWh   "
        f"Δ {demand - eia_demand:+.2f}"
    )
    print("  --")
    print(f"  MODEL domestic gen           {domestic_gen:8.2f} TWh")
    print(
        f"  EIA-930 implied domestic gen {eia_dom:8.2f} TWh   "
        f"Δ {domestic_gen - eia_dom:+.2f}  <<< RC#1 over-gen"
    )
    print("  --")
    print(f"  MODEL gross import           {gross_import:8.2f} TWh")
    print(f"  MODEL gross export           {gross_export:8.2f} TWh")
    print(f"  MODEL net import (+imp)      {net_import:8.2f} TWh")
    print(
        f"  EIA-930 net import (+imp)    {eia_net_import:8.2f} TWh   "
        f"Δ {net_import - eia_net_import:+.2f}"
    )
    print("  --")
    print(f"  MODEL dump (curtailment)     {dump:8.2f} TWh")
    print(f"  MODEL storage RT loss        {stor_loss:8.2f} TWh")
    print(f"  MODEL slack (unserved)       {slack:8.4f} TWh")
    print("  -- domestic gen by fuel --")
    for fuel, twh in by_fuel.sort_values(ascending=False).items():
        print(f"     {str(fuel):<14}{twh:8.2f} TWh")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--year", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--pass", dest="pass_label", default="P1")
    args = ap.parse_args()
    for y in args.year:
        try:
            probe_year(args.bundle, y, args.pass_label)
        except FileNotFoundError as e:
            print(f"\n[skip {y}] {e}")


if __name__ == "__main__":
    main()
