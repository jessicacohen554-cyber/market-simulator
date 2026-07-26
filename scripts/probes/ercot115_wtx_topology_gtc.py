"""ERCOT-115 Task B: is there an interface-scale GTC behind the West/Panhandle
wind corridor that the model does not already carry?

No-LP. Reads the committed NP6-86 SCED binding-constraint archive
(``data/raw/iso-specific-transmission/SCEDBTCNP686_SCEDBTCNP686_<year>.parquet``)
and answers three questions the ERCOT-115 charter's topology task depends on:

1. **Interface inventory** — every *generic transmission constraint* (GTC: an
   aggregate zonal interface, identified by an empty ``FromStation``), its
   binding frequency as a share of SCED intervals, and its median
   **limit-at-bind**, per year. This is the comparator for the ``ttc_mw``
   literals in ``config/iso_configs._ercot_config``.

2. **The limit basis** — a GTC's median ``Limit`` over ALL rows is *not* its
   transfer limit; the binding rows carry a materially lower limit (the
   constraint's limit in the intervals where it actually constrained). Reported
   side by side because the 2026-07-07 topology scope doc quoted the all-rows
   figure for PNHNDL (3,239 MW) against the model's limit-at-bind value
   (2,680 MW), which reads as a 17 % under-representation and is not one.

3. **The nodal tail** — the share of SCED intervals in which a
   *station-to-station* constraint binds while **no** interface GTC binds at
   all. That congestion is invisible to a zonal topology at any interface
   granularity, so it bounds what any zone split can recover.

Usage:
    python scripts/probes/ercot115_wtx_topology_gtc.py
    python scripts/probes/ercot115_wtx_topology_gtc.py --years 2024 2025
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ARCHIVE_DIR = REPO / "data" / "raw" / "iso-specific-transmission"

# Columns the archive is read with — the whole file is ~1.1 M rows/year, so
# projecting at the parquet layer keeps the scan light.
_USECOLS = [
    "SCEDTimeStamp",
    "ConstraintName",
    "ShadowPrice",
    "Limit",
    "FromStation",
]

# GTCs already wired to a model link in ``_ercot_config`` (config/iso_configs.py).
MODELLED_GTCS: dict[str, str] = {
    "WESTEX": "West->North + West->South_Central (7,300 + 2,700)",
    "PNHNDL": "Panhandle->North (2,680)",
    "NE_LOB": "Northeast->North (1,300 export / 1,788 import)",
    "N_TO_H": "North->Houston (8,000 — deliberate carve-out, parallel paths)",
}

# GTCs whose name places them in the West Texas / Permian / Far West geography,
# i.e. the candidates for an interface a West/Panhandle zone split could sit
# behind. MCCAMY = McCamey (Permian), CULBSN = Culberson County (Far West),
# I_FW_N / I_FW_S = Far West North / South.
WEST_TEXAS_GTCS = ("WESTEX", "PNHNDL", "MCCAMY", "CULBSN", "I_FW_N", "I_FW_S")


def _archive(year: int) -> Path:
    """Return the NP6-86 parquet for ``year``, or raise with a clear message."""
    path = ARCHIVE_DIR / f"SCEDBTCNP686_SCEDBTCNP686_{year}.parquet"
    if not path.exists():
        raise SystemExit(f"missing NP6-86 archive: {path}")
    return path


def _is_gtc(from_station: pd.Series) -> pd.Series:
    """True where the row is an interface GTC (empty/absent ``FromStation``).

    ``FromStation`` is NULL for GTCs and a station name for station-to-station
    constraints. The null check must run BEFORE any string coercion: under
    pandas 3 ``astype(str)`` renders a missing value as ``<NA>``, so a naive
    ``== "nan"`` test silently classifies every GTC row as nodal.
    """
    blank = from_station.astype("string").fillna("").str.strip() == ""
    return from_station.isna() | blank


def scan(year: int) -> dict:
    """Return the interface/nodal decomposition and per-GTC stats for one year."""
    df = pd.read_parquet(_archive(year), columns=_USECOLS)
    n_intervals = df["SCEDTimeStamp"].nunique()
    binding = df[df["ShadowPrice"] > 0]
    gtc_mask = _is_gtc(binding["FromStation"])
    gtc, nodal = binding[gtc_mask], binding[~gtc_mask]
    iv_gtc = set(gtc["SCEDTimeStamp"])
    iv_nodal = set(nodal["SCEDTimeStamp"])

    per_gtc = {}
    all_rows_median = df[_is_gtc(df["FromStation"])].groupby("ConstraintName")["Limit"]
    all_rows_median = all_rows_median.median()
    for name, g in gtc.groupby("ConstraintName"):
        per_gtc[str(name)] = {
            "bind_pct": 100.0 * g["SCEDTimeStamp"].nunique() / n_intervals,
            "limit_at_bind_median": float(g["Limit"].median()),
            "limit_all_rows_median": float(all_rows_median.get(name, float("nan"))),
        }
    return {
        "year": year,
        "n_intervals": n_intervals,
        "any_bind_pct": 100.0 * len(iv_gtc | iv_nodal) / n_intervals,
        "gtc_bind_pct": 100.0 * len(iv_gtc) / n_intervals,
        "nodal_bind_pct": 100.0 * len(iv_nodal) / n_intervals,
        "nodal_only_pct": 100.0 * len(iv_nodal - iv_gtc) / n_intervals,
        "n_gtc": int(gtc["ConstraintName"].nunique()),
        "n_nodal": int(nodal["ConstraintName"].nunique()),
        "per_gtc": per_gtc,
    }


def main() -> None:
    """Scan each year and print the three tables the charter's task turns on."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    scans = [scan(y) for y in args.years]

    print("=== 1. congestion decomposition (share of SCED intervals) ===")
    print(
        f"{'year':>6} {'intervals':>10} {'any bind':>9} {'interface':>10} "
        f"{'nodal':>8} {'NODAL-ONLY':>11} {'#GTC':>5} {'#nodal':>7}"
    )
    for s in scans:
        print(
            f"{s['year']:>6} {s['n_intervals']:>10,} {s['any_bind_pct']:>8.1f}% "
            f"{s['gtc_bind_pct']:>9.1f}% {s['nodal_bind_pct']:>7.1f}% "
            f"{s['nodal_only_pct']:>10.1f}% {s['n_gtc']:>5} {s['n_nodal']:>7}"
        )
    print(
        "  NODAL-ONLY = a station-to-station constraint binds and NO interface\n"
        "  GTC binds — congestion no zonal topology can represent at any\n"
        "  interface granularity. It bounds what a zone split can recover."
    )

    print("\n=== 2. West Texas corridor interfaces: bind % / limit-at-bind MW ===")
    header = "  ".join(f"{y}" for y in args.years)
    print(f"{'GTC':<8} {header:>42}   modelled as")
    for name in WEST_TEXAS_GTCS:
        cells = []
        for s in scans:
            st = s["per_gtc"].get(name)
            cells.append(
                f"{st['bind_pct']:>5.1f}% {st['limit_at_bind_median']:>8,.0f}"
                if st
                else f"{'—':>5}  {'—':>8}"
            )
        print(f"{name:<8} {'  '.join(cells):>42}   {MODELLED_GTCS.get(name, '—')}")

    print("\n=== 3. limit basis: all-rows median vs limit-at-bind (modelled GTCs) ===")
    print(f"{'GTC':<8} {'year':>6} {'all-rows MW':>12} {'at-bind MW':>11} {'gap':>8}")
    for name in MODELLED_GTCS:
        for s in scans:
            st = s["per_gtc"].get(name)
            if not st:
                continue
            a, b = st["limit_all_rows_median"], st["limit_at_bind_median"]
            print(f"{name:<8} {s['year']:>6} {a:>12,.0f} {b:>11,.0f} {a - b:>8,.0f}")


if __name__ == "__main__":
    main()
