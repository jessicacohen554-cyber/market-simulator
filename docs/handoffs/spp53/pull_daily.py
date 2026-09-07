"""SPP-53: pull every RTBM-DAILY-BC-YYYYMMDD.csv from 2026-01-28 -> latest via SPP-14's producer."""
import sys, time
from pathlib import Path
sys.path.insert(0, "/home/user/market-simulator/scripts/data")
from fetch_spp_alt_portal import listing, download
OUT = Path(sys.argv[1]); OUT.mkdir(exist_ok=True)
FS = "rtbm-binding-constraints"
names = []
for mm in range(1, 13):
    try:
        items = listing(FS, f"/2026/{mm:02d}/By_Day")
    except Exception as e:
        print("no month", mm, e); continue
    for it in items:
        n = it["name"]
        if n.startswith("RTBM-DAILY-BC-") and n.endswith(".csv") and n[14:22] >= "20260128":
            names.append((f"/2026/{mm:02d}/By_Day/{n}", n, int(it["size"])))
print("files to pull:", len(names), flush=True)
fail = []
for path, n, size in names:
    dest = OUT / n
    if dest.exists() and dest.stat().st_size == size:
        continue
    try:
        b = download(FS, path)
        if len(b) != size:
            print("SIZE MISMATCH", n, len(b), size, flush=True)
        dest.write_bytes(b)
    except Exception as e:
        fail.append(n); print("FAIL", n, e, flush=True)
print("done; failed:", fail, flush=True)
