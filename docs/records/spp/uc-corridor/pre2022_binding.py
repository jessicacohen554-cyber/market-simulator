"""UC-SPP-CORRIDOR: did SPP-53's 12 identified corridor elements bind in 2019-2025 RTBM?

Reads SPP's RTBM binding-constraint roll-ups (data/raw/spp-binding-constraints,
10-column, no limits) and counts, per year, the hours in which each element
(SPP-53's monitored-facility key) carried a BINDING/BREACHED interval, plus the
static NormLimit/EmerLimit SPP's Temp_Flowgate_Archive.csv records for that
element. Context only: no limit is inferred for 2019-2021.

Usage: python docs/records/spp/uc-corridor/pre2022_binding.py data/raw/spp-effective-limits/Temp_Flowgate_Archive.csv <out.csv>
"""
import csv, io, re, sys, zipfile, glob
from collections import defaultdict
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[4]
RAW = REPO / "data/raw/spp-binding-constraints"
T53 = pd.read_csv(REPO / "docs/records/spp/spp53/tstar_table.csv"); T53 = T53[T53.identified]


def key(s):
    """SPP-53's monitored-facility element key (aggregate_ttc.py, verbatim)."""
    s = str(s).upper(); s = re.sub(r"^(XFMR|XF|LN)\s+", "", s); s = re.sub(r"\s+\d+(/\d+)?\s*KV$", "", s)
    a = [re.sub(r"\d+$", "", x.strip()) for x in s.split(" - ")]
    if len(a) == 1: return a[0]
    if len(a) == 2 and a[0] == a[1]: return a[0]
    return " - ".join(sorted(a)) if len(a) == 2 else s


KEYS = {key(m): m for m in T53["Monitored Facility"]}
hours = defaultdict(set)
files = {y: [RAW / f"RTBM-BC-YEARLY-{y}.csv.zip"] for y in (2019, 2020, 2021, 2023, 2024)}
files[2022] = [RAW / "RTBM-BC-YEARLY-2022.zip"]
files[2025] = sorted(RAW.glob("RTBM-BC-MONTHLY-2025*.csv.zip"))
for y, fs in files.items():
    for f in fs:
        z = zipfile.ZipFile(f)
        for n in z.namelist():
            with z.open(n) as fh:
                r = csv.reader(io.TextIOWrapper(fh, newline=""))
                h = next(r, None)
                if h is None: continue
                iS, iM, iG = h.index("State"), h.index("Monitored Facility"), h.index("GMTIntervalEnd")
                for row in r:
                    if len(row) <= iM or row[iS] not in ("BINDING", "BREACHED"): continue
                    k = key(row[iM])
                    if k in KEYS: hours[(y, k)].add(row[iG][:13])
arch = pd.read_csv(sys.argv[1], dtype=str, index_col=False, on_bad_lines="warn")
arch["k"] = arch.MonitoredElement.str.replace("Monitored: ", "", regex=False).str.split(" LN:| XF:| XFMR:").str[0].map(key)
out = []
for k, m in KEYS.items():
    a = arch[arch.k == k]
    rec = {"element": m, "archive_flowgates": len(a),
           "archive_norm_limits": "|".join(sorted(set(a.NormLimit.dropna()))),
           "archive_created_first": str(pd.to_datetime(a.CreatedTime, format="%m/%d/%Y %H:%M", errors="coerce").min()) if len(a) else ""}
    for y in range(2019, 2026): rec[f"h{y}"] = len(hours[(y, k)])
    out.append(rec)
O = pd.DataFrame(out); O.to_csv(sys.argv[2], index=False)
pd.set_option("display.width", 250); print(O.to_string(index=False, max_colwidth=40))
