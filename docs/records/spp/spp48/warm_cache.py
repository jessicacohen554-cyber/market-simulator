"""SPP-48 instrument: warm the shared reanalysis memo for every plant R-LEVEL needs.

R-LEVEL (``scripts/lib/wind_shape.py``) reads NASA POWER at EVERY operable wind
plant rather than six per zone, so a first build is hundreds of point-years at
~1.1 s each. The builder's own fetch is serial by design; this warmer pulls the
same point-years concurrently into the same memo
(:data:`scripts.lib.wind_shape.REANALYSIS_CACHE_DIR`), after which every build in
this lane — SPP two-zone, SPP three-zone at design commit ``8d427adc``, MISO —
reads from disk.

It changes NO value: it calls the builder's own
:func:`~scripts.lib.wind_shape.fetch_nasa_power_ws50m` with the builder's own
cache directory, so warm output is byte-identical to cold output (PRECOMMIT P7).

usage: python docs/handoffs/spp48/warm_cache.py SPP MISO --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from scripts.lib import wind_shape  # noqa: E402


def main() -> int:
    """Fetch every (plant, year) point the requested ISOs need into the memo."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("isos", nargs="+")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    points: set[tuple[float, float, int]] = set()
    for iso in args.isos:
        zones = list(get_iso_config(iso).zone_names)
        for year in args.years:
            fleets = wind_shape.load_zone_wind_fleet(year, zones, iso)
            n = sum(len(v) for v in fleets.values())
            print(f"{iso} {year}: {n} plants over {len(zones)} zones")
            for plants in fleets.values():
                for lat, lon, _cap, _hub in plants:
                    points.add((round(lat, 4), round(lon, 4), year))

    todo = [
        p
        for p in sorted(points)
        if not wind_shape._cache_path(
            p[0], p[1], p[2], wind_shape.REANALYSIS_CACHE_DIR
        ).exists()
    ]
    print(f"\n{len(points)} distinct point-years; {len(todo)} not yet memoised")
    t0 = time.time()
    done = failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {
            pool.submit(wind_shape.fetch_nasa_power_ws50m, lat, lon, yr): (lat, lon, yr)
            for lat, lon, yr in todo
        }
        for fut in as_completed(futs):
            try:
                fut.result()
                done += 1
            except Exception as exc:  # noqa: BLE001 — report and continue
                failed += 1
                print(f"  FAILED {futs[fut]}: {exc}")
            if done % 50 == 0 and done:
                print(f"  {done}/{len(todo)} in {time.time() - t0:.0f}s")
    print(f"\nwarmed {done}, failed {failed}, {time.time() - t0:.0f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
