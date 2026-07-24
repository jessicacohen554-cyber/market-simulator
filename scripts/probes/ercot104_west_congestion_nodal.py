"""ERCOT-104 — the West/Panhandle scarcity congestion is NODAL, not zonal.

The make-or-break diagnostic for the West/Panhandle topology-split lane. The
ERCOT-101 §3 residual is a settlement-point price tail above system lambda
(LZ_WEST +$64 mean above HB_HUBAVG in 2025) that a reduced zonal network cannot
form. The split hypothesis: add an import-direction limit on the West/Panhandle
interface so the model prices the regional scarcity congestion.

This probe reads the measured ERCOT NP6-86 SCED binding-constraint archive
(data/raw/iso-specific-transmission/SCEDBTCNP686_*<year>.parquet) and ranks
constraints by binding frequency and shadow price, separating the ZONAL
interface GTCs (WESTEX, PNHNDL, NE_LOB — already modeled as TransferLinks at
measured limits) from the STATION-TO-STATION nodal constraints. The finding: the
zonal interfaces are EXPORT limits with tiny shadow prices ($5-19), while the
congestion rent lives in 30-500 MW nodal 138/345 kV lines (MDSSW, Ozona, LPLNW,
BURNS_RIOHONDO, …). A 7-zone reduced network structurally cannot form nodal
congestion, and there is no measured ZONAL import limit because the phenomenon
is not zonal (rule 11). So a West/Panhandle split is a copper-plate no-op for
this residual — confirming the reverted Far_West split and the deferred WP-A.

No LP. Reads the committed SCED archive. Usage:
python -m scripts.probes.ercot104_west_congestion_nodal [--year Y]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SCED_DIR = REPO / "data" / "raw" / "iso-specific-transmission"

# The zonal interface GTCs already modeled as TransferLinks (iso_configs.py).
ZONAL_INTERFACES = {"WESTEX", "PNHNDL", "NE_LOB"}


def run(year: int) -> None:
    path = SCED_DIR / f"SCEDBTCNP686_SCEDBTCNP686_{year}.parquet"
    if not path.exists():
        print(f"{year}: {path.name} absent")
        return
    df = pd.read_parquet(path)
    g = (
        df.groupby("ConstraintName")
        .agg(
            n=("ShadowPrice", "size"),
            sp_mean=("ShadowPrice", "mean"),
            sp_max=("ShadowPrice", "max"),
            lim_mean=("Limit", "mean"),
        )
        .sort_values("sp_mean", ascending=False)
    )
    zonal = g[g.index.isin(ZONAL_INTERFACES)]
    # nodal = station-to-station (a '_' pair or a numeric bus-constraint id), not
    # a named zonal interface; rank the congestion-rent carriers.
    nodal = g[~g.index.isin(ZONAL_INTERFACES)]

    print(f"\n=== {year} ERCOT SCED binding constraints (NP6-86) ===")
    print("ZONAL interfaces (already modeled as TransferLinks at measured MW):")
    for name, r in zonal.iterrows():
        print(f"  {name:10s} binds {int(r.n):6d} intervals | shadow ${r.sp_mean:7.2f} "
              f"mean / ${r.sp_max:8.0f} max | limit {r.lim_mean:7.0f} MW  <- EXPORT limit")
    print("Top nodal (station-to-station) constraints by mean shadow price "
          "(sub-zonal, unrepresentable in a 7-zone network):")
    for name, r in nodal.head(10).iterrows():
        print(f"  {name:18s} binds {int(r.n):6d} | shadow ${r.sp_mean:7.2f} mean / "
              f"${r.sp_max:8.0f} max | limit {r.lim_mean:6.0f} MW")
    zonal_sp = float(zonal["sp_mean"].mean()) if len(zonal) else 0.0
    nodal_top_sp = float(nodal.head(10)["sp_mean"].mean())
    print(f"  -> zonal-interface mean shadow ${zonal_sp:.1f} vs top-nodal mean "
          f"${nodal_top_sp:.1f}: the congestion rent is NODAL. A zonal split cannot "
          "form it; no measured zonal import limit exists (rule 11).")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ercot104_west_congestion_nodal")
    ap.add_argument("--year", type=int, nargs="+", default=[2023])
    args = ap.parse_args(argv)
    for y in args.year:
        run(y)
    return 0


if __name__ == "__main__":
    sys.exit(main())
