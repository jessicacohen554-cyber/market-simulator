"""SPP-57: pull the 36 monthly RT LMP-by-settlement-location files (2023-2025) through the
SPP-14 LMP builder's own plumbing (range-reads of the archived year zips for 2023/24, the live
per-month path for 2025) into the scratchpad. Bytes only; parsing is build_area_price.py."""

import sys
from pathlib import Path

sys.path.insert(0, "/home/user/market-simulator/scripts/data")
import build_spp_lmp_reference as b  # noqa: E402

OUT = Path(sys.argv[1]) / "rt_sl"
OUT.mkdir(parents=True, exist_ok=True)
for year in (2023, 2024, 2025):
    have = {int(p.name[-10:-8]) for p in OUT.glob(f"RTBM-LMP-MONTHLY-SL-{year}*.csv")}
    if len(have) == 12:
        print(year, "already complete", flush=True)
        continue
    months = b._monthly_bytes(b.FS_RT, "RTBM-LMP", year)
    for m, data in months.items():
        (OUT / f"RTBM-LMP-MONTHLY-SL-{year}{m:02d}.csv").write_bytes(data)
    print(
        year,
        "months",
        sorted(months),
        "bytes",
        sum(len(v) for v in months.values()),
        flush=True,
    )
print("done", flush=True)
