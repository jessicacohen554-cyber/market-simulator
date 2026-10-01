"""NWPP-NEXT-14 phase 0 (ZERO LP): Jim Bridger 8066 in the C4 coal 2023 record.

Keeper #17 vs #18 coal-class hourly (committed sidecars; #17 from git history at
5100d6d2) against the EIA-930 coal series, with Jim Bridger's per-plant payload
series swapped for #17's or for its CEMS series. Inputs are staged in a scratch
dir (argv[1]): ``e930coal2023.npy`` (run_calibration_full._eia930_frame),
``k17_ch2023.parquet`` and ``k17.js`` (git show). Record:
docs/records/nwpp/FINDING-nwppnext14-bridger-and-clark-phase0-2026-09-30.md §1.
"""

import sys
import re
import base64
import gzip
import json
import numpy as np
import pandas as pd

S = sys.argv[1]
T = 8760
ob = np.load(f"{S}/e930coal2023.npy")


def load(p):
    t = open(p).read()
    b = re.search(r'="([^"]+)"', t).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b)))


def coal_hr(p):
    d = pd.read_parquet(p)
    d = d[(d["pass"] == "P1") & d.klass.str.startswith("COAL")]
    return d.groupby("hour").mw.sum().reindex(range(T), fill_value=0).to_numpy(float)


def pr(m, o):
    r = np.corrcoef(m, o)[0, 1]
    n = np.sqrt(((m - o) ** 2).mean()) / o.mean()
    return round(r, 3), round(n, 3)


m18 = coal_hr("results/calibration/nwppnext13pu_span/hourly/class_hourly_2023.parquet")
m17 = coal_hr(f"{S}/k17_ch2023.parquet")
print("fleet #17", pr(m17, ob), m17.sum() / 1e6, " #18", pr(m18, ob), m18.sum() / 1e6)
p18 = load("frontend/data/backcast/runs/2026-09-30-nwppnext13-per-unit-attribution.js")[
    "years"
]["2023"]["plants"]
p17 = load(f"{S}/k17.js")["years"]["2023"]["plants"]
bb = json.loads(
    gzip.decompress(open("frontend/data/backcast/bench/NWPP/2023.json.gz", "rb").read())
)["bench"]["plants"]


def ser(b64, cap):
    return (
        np.frombuffer(base64.b64decode(b64)[:T], dtype=np.uint8).astype(float)
        * cap
        / 100
    )


coalp = [c for c, b in bb.items() if b["group"].startswith("COAL")]
rows = []
for c in coalp:
    cap = float(bb[c]["npl"])
    a = ser(bb[c]["campd"], cap) if bb[c].get("campd") else np.zeros(T)
    x18 = ser(p18[c]["m"], cap) if c in p18 and p18[c].get("m") else np.zeros(T)
    x17 = ser(p17[c]["m"], cap) if c in p17 and p17[c].get("m") else np.zeros(T)
    rows.append(
        (
            c,
            bb[c]["name"],
            bb[c]["group"],
            cap,
            x17.sum() / 1e6,
            x18.sum() / 1e6,
            a.sum() / 1e6,
            round(np.corrcoef(x17, a)[0, 1], 3)
            if x17.std() > 0 and a.std() > 0
            else None,
            round(np.corrcoef(x18, a)[0, 1], 3)
            if x18.std() > 0 and a.std() > 0
            else None,
        )
    )
    if c == "8066":
        B17, B18, BA = x17, x18, a
df = pd.DataFrame(
    rows, columns=["code", "name", "grp", "cap", "m17", "m18", "cems", "r17", "r18"]
)
df["d"] = df.m18 - df.m17
print(df.sort_values("d").round(3).to_string())
# swaps
print("#18 with Bridger<-#17 :", pr(m18 - B18 + B17, ob))
print("#17 with Bridger<-#18 :", pr(m17 - B17 + B18, ob))
sc = B18.sum() / BA.sum()
print("#18 with Bridger<-CEMS(scaled to model TWh):", pr(m18 - B18 + BA * sc, ob))
print("#18 with Bridger<-CEMS raw:", pr(m18 - B18 + BA, ob))
# monthly
idx = pd.date_range("2023-01-01", periods=T, freq="h")


def mm(x):
    """Monthly GWh of an hourly MW series."""
    return (pd.Series(x, index=idx).resample("MS").sum() / 1e3).round(0).tolist()


print("Bridger #17 GWh", mm(B17))
print("Bridger #18 GWh", mm(B18))
print("Bridger CEMS", mm(BA))
print("fleet #17", mm(m17))
print("fleet #18", mm(m18))
print("930", mm(ob))
np.savez(f"{S}/bridger.npz", B17=B17, B18=B18, BA=BA, m17=m17, m18=m18, ob=ob)
