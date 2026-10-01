"""SPP-92 (ZERO LP): fetch SPP RTBM hourly LMP at every LOAD settlement location + the two hubs.

Derived from scripts/probes/_spp91_node_lmp_fetch.py (same anonymous range-read route); only the
location filter differs: all SETLOCTYPE == LOAD rows of data/raw/spp-planning/SL_to_Pnode_to_Zone_with_Area.csv.
Used to build actual model-bubble-average prices (EIA-930 sub-BA load weights) for the seam FINDING
``docs/records/spp/FINDING-spp-92-seam-2026-09-27.md``. Clock: HE label is GMT hour-ending (SPP-91 §2).

Original SPP-91 docstring follows.

SPP-91 (ZERO LP): fetch SPP RTBM hourly LMP at the keeper's large coal plants' settlement locations.

Record: ``docs/records/spp/FINDING-spp-91-flat-coal-headroom-2026-09-27.md``.

Source: SPP Marketplace portal, product ``rtbm-lmp-by-location`` (anonymous HTTPS, the SPP-14 route,
``data/raw/spp-lmp-alt/SOURCES.md``). Each year ``/<yr>/<yr>.zip`` (4-5 GB) holds, beside the 5-min
files, twelve ``RTBM-LMP-MONTHLY-SL-<yyyymm>.csv`` members (hourly HE01..HE24 per settlement location,
Price Type LMP / MCC / MLC / MEC). Only those twelve members are range-read; 2025 (no year zip) is read
from ``/2025/<MM>/RTBM-LMP-MONTHLY-SL-2025MM.csv``. Rows are kept for the plant locations in ``PLANTS``
(EIA-860 plant code -> SPP settlement locations, matched by name/PNODE) and the two hubs. Output is a
scratch parquet (not a data contract): date, HE (1..24, hour-ending CPT as published), loc, ptype, value.

Usage: ``python scripts/probes/_spp91_node_lmp_fetch.py --years 2019 ... --out <parquet>``
"""
from __future__ import annotations

import argparse
import io
import json
import struct
import subprocess
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

BASE = "https://portal.spp.org/file-browser-api"
PLANTS = {  # EIA-860 plant code -> SPP settlement location names (PNODE confirms the unit)
    6068: ["WR.JEC.1", "WR.JEC.2", "WR.JEC.3"],                 # Jeffrey EC, KS
    6194: ["SPS.TOLK1", "SPS.TOLK2"],                           # Tolk, TX
    6096: ["NEBRASKA_CITY_1", "NEBRASKA_CITY_2"],               # Nebraska City, NE
    6065: ["KCPLIATANUNIAT1", "KCPLIATANUNIAT2"],               # Iatan, MO
    6193: ["SPS.HARRNGTN1", "SPS.HARRNGTN2", "SPS.HARRNGTN3"],  # Harrington, TX
    1241: ["KCPLLACYGNEUNLAC1", "KCPLLACYGNEUNLAC2"],           # La Cygne, KS
    6077: ["NPPD_GGS1", "NPPD_GGS2"],                           # Gerald Gentleman, NE
    6139: ["CSWWELSH1", "CSWWELSH3"],                           # Welsh, TX
    7902: ["CSWPIRKEY1"],                                       # Pirkey, TX
    2952: ["OKGEMK4", "OKGEMK5", "OKGEMK6"],                    # Muskogee, OK
    2817: ["WAUE.BEPM.LOS1", "WAUE.BEPM.LOS2"],                 # Leland Olds, ND
    108: ["SECIHOLCOM1UN1"],                                    # Holcomb, KS
    2963: ["CSWNORTHEASTERN3"],                                 # Northeastern 3, OK
    2291: ["NORTH_OMAHA_4", "NORTH_OMAHA_5"],                   # North Omaha, NE
    2277: ["NPPD_SHLD_1", "NPPD_SHLD_2"],                       # Sheldon, NE
    165: ["GRDA.GREC2"],                                        # GRDA, OK
}
HUBS = ["SPPNORTH_HUB", "SPPSOUTH_HUB"]
_SL = pd.read_csv(Path(__file__).resolve().parents[2] / "data/raw/spp-planning/SL_to_Pnode_to_Zone_with_Area.csv",
                  dtype=str, usecols=["SETLOCNAME", "SETLOCTYPE"])
KEEP = set(_SL.loc[_SL.SETLOCTYPE == "LOAD", "SETLOCNAME"]) | set(HUBS)


def _curl(url: str, rng: str | None = None) -> bytes:
    cmd = ["curl", "-sS", "-m", "600"] + (["-r", rng] if rng else []) + [url]
    for _ in range(5):
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout
    raise RuntimeError(f"{url} {rng}: {r.stderr[:200]!r}")


def _listing(path: str) -> list[dict]:
    q = path.replace("/", "%2F")
    return json.loads(_curl(f"{BASE}/?fsName=rtbm-lmp-by-location&path={q}&type=folder"))


def _monthly_members(y: int) -> list[tuple[str, int, int, int]]:
    """Central directory of the year zip, reduced to the twelve MONTHLY-SL members."""
    size = next(i["size"] for i in _listing(f"/{y}") if i["name"] == f"{y}.zip")
    url = f"{BASE}/download/rtbm-lmp-by-location?path=%2F{y}%2F{y}.zip"
    tail = _curl(url, f"{size - 65536}-{size - 1}")
    i = tail.rfind(b"PK\x05\x06")
    cd_size, cd_off = struct.unpack("<II", tail[i + 12:i + 20])
    j = tail.rfind(b"PK\x06\x06")
    if j >= 0:
        cd_size, cd_off = struct.unpack("<QQ", tail[j + 40:j + 56])
    cd = _curl(url, f"{cd_off}-{cd_off + cd_size - 1}")
    out, p = [], 0
    while cd[p:p + 4] == b"PK\x01\x02":
        meth, = struct.unpack("<H", cd[p + 10:p + 12])
        csz, usz = struct.unpack("<II", cd[p + 20:p + 28])
        fl, el, cl = struct.unpack("<HHH", cd[p + 28:p + 34])
        off, = struct.unpack("<I", cd[p + 42:p + 46])
        name = cd[p + 46:p + 46 + fl].decode()
        ex, q = cd[p + 46 + fl:p + 46 + fl + el], 0
        while q + 4 <= len(ex):
            hid, hl = struct.unpack("<HH", ex[q:q + 4])
            if hid == 1:
                v = list(struct.unpack("<" + "Q" * (hl // 8), ex[q + 4:q + 4 + hl]))
                if usz == 0xFFFFFFFF:
                    usz = v.pop(0)
                if csz == 0xFFFFFFFF:
                    csz = v.pop(0)
                if off == 0xFFFFFFFF:
                    off = v.pop(0)
            q += 4 + hl
        if "MONTHLY-SL" in name:
            out.append((url, name, off, csz, meth))
        p += 46 + fl + el + cl
    return out


def _read(m) -> pd.DataFrame:
    if isinstance(m, str):
        raw = _curl(m)
    else:
        url, _, off, csz, meth = m
        h = _curl(url, f"{off}-{off + 30 + 1024 + csz}")
        fl, el = struct.unpack("<HH", h[26:30])
        d = h[30 + fl + el:30 + fl + el + csz]
        raw = zlib.decompress(d, -15) if meth == 8 else d
    df = pd.read_csv(io.BytesIO(raw), skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    df = df[df["Settlement Location Name"].isin(KEEP) & df["Price Type"].isin(["LMP"])]
    he = [c for c in df.columns if c.startswith("HE")]
    long = df.melt(id_vars=["Date", "Settlement Location Name", "Price Type"], value_vars=he, var_name="he")
    long["he"] = long["he"].str[2:].astype(int)
    return long.rename(columns={"Date": "date", "Settlement Location Name": "loc", "Price Type": "ptype"})


def main() -> int:
    """Fetch the requested years into one parquet."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    jobs = []
    for y in a.years:
        if y >= 2025:
            for mm in range(1, 13):
                f = [i for i in _listing(f"/{y}/{mm:02d}") if i["name"].startswith("RTBM-LMP-MONTHLY-SL")]
                jobs += [f"{BASE}/download/rtbm-lmp-by-location?path=" + f[0]["path"].replace("/", "%2F")] if f else []
        else:
            jobs += _monthly_members(y)
    with ThreadPoolExecutor(6) as ex:
        frames = list(ex.map(_read, jobs))
    out = pd.concat(frames, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"], format="mixed")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(a.out)
    print(len(jobs), "files;", len(out), "rows;", out["loc"].nunique(), "locations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
