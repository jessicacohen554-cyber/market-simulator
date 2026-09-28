"""Download ISO-NE hourly DA / RT-final LMP at the NY-facing external nodes.

WHY THIS EXISTS (NYISO-NEXT-10, 2026-09-28).  NEXT-7
(``docs/FINDING-nyiso-next7-star-node-2026-09-27.md`` §3(c)) refused a
per-neighbour NYISO seam construction because the repo held no measured price on
the ISO-NE side of the NY ties: SMD carries only the eight load zones and the
hub.  ISO-NE's own hourly LMP report prices every external node, including the
three that face New York:

    4011  .I.ROSETON 345 1   -- the NY AC interface (Roseton / Pleasant Valley)
    4014  .I.SHOREHAM138 99  -- the Cross-Sound Cable (CSC) to Long Island
    4017  .I.NRTHPORT138 5   -- the Northport-Norwalk 1385 line to Long Island

The hub (4000) is carried alongside as the ISO-NE reference price.  The source
is the same ungated static report tree ``fetch_neiso_smd_zonal_lmp`` reads, one
operating day per file (DA ``WW_DALMP_ISO_<YYYYMMDD>.csv``, RT-final
``lmp_rt_final_<YYYYMMDD>.csv``); this script only swaps the location set and the
output stem, so the DST handling (position-keyed ``seq``) and the DA/RT
cross-check are the tested ones.

Output: ``data/raw/seam-neighbour-price/neiso/NEISO_ny_ext_node_lmp_<year>.csv``,
columns ``date, hour_ending, seq, location_id, location, da_lmp, rt_lmp`` (USD).

Usage:
    uv run python scripts/data/fetch_seam_neighbour_price_neiso.py --start 2021-01-01 --end 2025-12-31
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

from scripts.data.fetch_neiso_smd_zonal_lmp import (  # noqa: E402
    DEFAULT_WORKERS,
    fetch_days,
    write_year_csv,
)

RAW_DIR = RAW_DATA_DIR / "seam-neighbour-price" / "neiso"
STEM = "NEISO_ny_ext_node_lmp"

#: ISO-NE location id -> report name, as printed in the hourly LMP report
#: (verified against WW_DALMP_ISO_20210105.csv, 2026-09-28).
NY_EXTERNAL_NODES: dict[str, str] = {
    "4000": ".H.INTERNAL_HUB",
    "4011": ".I.ROSETON 345 1",
    "4014": ".I.SHOREHAM138 99",
    "4017": ".I.NRTHPORT138 5",
}


def main(argv: list[str] | None = None) -> int:
    """Download and reduce the requested operating days to the NY-facing nodes."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", type=dt.date.fromisoformat, required=True)
    p.add_argument("--end", type=dt.date.fromisoformat, required=True)
    p.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    p.add_argument("--out-dir", type=Path, default=RAW_DIR)
    args = p.parse_args(argv)
    if args.end < args.start:
        p.error("--end precedes --start")
    days = [
        args.start + dt.timedelta(days=i)
        for i in range((args.end - args.start).days + 1)
    ]
    print(f"fetching {len(days)} operating day(s) x 2 markets", flush=True)
    rows = fetch_days(days, workers=args.workers, locations=NY_EXTERNAL_NODES)
    if not rows:
        print("no rows fetched")
        return 1
    by_year: dict[int, list[dict]] = {}
    for r in rows:
        by_year.setdefault(int(r["date"][:4]), []).append(r)
    for year, yr_rows in sorted(by_year.items()):
        path = write_year_csv(yr_rows, year, dest_dir=args.out_dir, stem=STEM)
        print(
            f"wrote {path} (+{len(yr_rows)} rows over {len({r['date'] for r in yr_rows})} days)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
