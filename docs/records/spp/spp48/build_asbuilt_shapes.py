"""SPP-48 instrument: rebuild wind shapes under the RETIRED six-largest-plants rule.

The "before" side of this lane's comparison needs shapes built the way the
builders built them before R-LEVEL. For SPP's TWO-zone map those are committed
(``data/raw/spp-wind-shape/``), but SPP-54's THREE-zone shapes were deliberately
not committed — the lane restored its solve path to ``origin/main``'s bytes — so
the three-zone baseline has to be regenerated here.

This reproduces the retired construction exactly: the largest
:data:`SAMPLES_PER_ZONE` plants per zone by nameplate, capacity-weighted, over
the shared module's unchanged physics (same shear law, same power curve, same
clock, same reanalysis memo). It is a COUNTERFACTUAL INSTRUMENT and lives here
rather than in the builders, which no longer carry a sample-count knob
(rule 26 ``[R-DELETE]``: a retained knob is a re-armable answer key).

Cross-check: run against SPP's two-zone map it must reproduce the committed
parquets, and against the three-zone map at design commit ``8d427adc`` it must
reproduce FINDING-spp-54 §4.2's annual potentials.

usage: python docs/handoffs/spp48/build_asbuilt_shapes.py --iso SPP --out-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from scripts.lib import wind_shape as ws  # noqa: E402

# The retired constant, kept HERE (a throwaway instrument) and nowhere in the
# builders — see the module docstring.
SAMPLES_PER_ZONE = 6


def main() -> int:
    """Rebuild every requested year under the retired sampling rule."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()

    iso = args.iso.upper()
    zones = list(get_iso_config(iso).zone_names)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for year in args.years:
        utc_index = ws.model_utc_index(year, iso)
        if utc_index is None:
            print(f"SKIP {year}: no {iso} clock")
            continue
        fleets = ws.load_zone_wind_fleet(year, zones, iso)
        data: dict[str, np.ndarray] = {
            ws.WIND_SHAPE_HOUR_COLUMN: np.arange(HOURS_PER_YEAR, dtype="int64")
        }
        empty: list[str] = []
        for zone in zones:
            # load_zone_wind_fleet returns plants ordered by descending
            # nameplate, so the head IS the retired nlargest selection.
            sample = fleets[zone][:SAMPLES_PER_ZONE]
            print(
                f"  {zone}: {len(sample)} of {len(fleets[zone])} plants sampled, "
                f"{sum(p[2] for p in sample):,.1f} of "
                f"{sum(p[2] for p in fleets[zone]):,.1f} MW"
            )
            shape = ws.build_zone_shape(sample, utc_index, year)
            if shape is None:
                empty.append(zone)
                continue
            data[zone] = shape
        populated = [z for z in zones if z not in empty]
        if not populated:
            continue
        mean_shape = np.mean([data[z] for z in populated], axis=0)
        for zone in empty:
            data[zone] = mean_shape
        df = pd.DataFrame(data)
        print(f"\n=== {iso} {year} per-zone shape (RETIRED six-largest rule) ===")
        hod = np.arange(HOURS_PER_YEAR) % 24
        for zone in zones:
            cf = df[zone].to_numpy()
            night = cf[hod < 6].mean()
            aft = cf[(hod >= 12) & (hod < 18)].mean()
            print(
                f"  {zone:<15} mean={cf.mean():.3f}  night={night:.3f}  "
                f"aft={aft:.3f}  night/aft={night / aft:.2f}"
            )
        table = pa.Table.from_pandas(df, preserve_index=False)
        table = table.replace_schema_metadata(
            {
                "level_rule": (
                    f"RETIRED six-largest-plants sampling (_SAMPLES_PER_ZONE="
                    f"{SAMPLES_PER_ZONE}); SPP-48 counterfactual baseline only"
                ),
                "year": str(year),
            }
        )
        out = args.out_dir / f"{iso.lower()}_{year}_wind_zone_shape.parquet"
        pq.write_table(table, out)
        print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
