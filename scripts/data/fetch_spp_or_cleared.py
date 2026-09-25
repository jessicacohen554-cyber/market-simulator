"""Fetch SPP RTBM operating-reserve CLEARED MW, hourly, SPP system-wide, 2019-2025.

Lane SPP-81 (``docs/handoffs/FINDING-spp-81-residual-upper-tercile-2026-09-25.md``).
``data/raw/spp-or-mcp`` carries the RTBM reserve *prices* (MCP); SPP-81's ramp-product
leg also needs the *quantities* each product cleared, to test whether ramp procurement
(launched 2022-03-01) changed which units set the marginal energy price.

Source: SPP Marketplace portal file-browser, product ``operating-reserves`` (anonymous
HTTPS, the SPP-14 route documented in ``data/raw/spp-or-mcp/SOURCES.md``). Each year is
one ``/<yr>/<yr>.zip`` (~40-50 MB) holding ~103k five-minute
``<yr>/<MM>/<DD>/RTBM-OR-<yyyymmddHHMM>.csv`` members with header
``Interval,GMTIntervalEnd,Reserve Zone,RegUP_Clr,RegDN_Clr,RampUP_Clr,RampDN_Clr,
Spin_Clr,Supp_Clr`` (later vintages may append more ``*_Clr`` columns). The zip is
range-read (the portal honours ``Range:``): its central directory once, then one
contiguous byte range per operating day, so the 47 MB body is never downloaded whole
and no member is modified. The current year (2025 at this writing) has no year zip; it
is served per day and is SAMPLED one interval per local hour (``sampled_year``).

Reduction (the only transformation): per five-minute interval, the SPP system-wide
cleared MW per product — the ``SPP`` reserve-zone row where published, else the sum of
the numbered reserve zones — then the hourly mean on the model clock. The clock is
SPP-80's (``scripts/probes/_spp80_upper_tercile_premium.model_hour``): GMT interval
end minus 5 min minus 6 h (fixed CST), Feb 29 dropped, non-leap 8760.

Output: ``data/raw/_validation-source/spp_rtbm_or_cleared_hourly.parquet``, long form
``year`` int16, ``hour`` int16 (0..8759), one float32 column per ``*_Clr`` product
(MW, lower-cased, ``_clr`` stripped), ``n_int`` (five-minute intervals averaged),
``src`` (``spp_row`` / ``zone_sum``).

Usage:
    python scripts/data/fetch_spp_or_cleared.py [--years 2019 ... 2025] [--workers 8]
    # or one process per year, then merge:
    python scripts/data/fetch_spp_or_cleared.py --years 2024 --part-dir <dir>
    python scripts/data/fetch_spp_or_cleared.py --merge <dir>
"""

from __future__ import annotations

import argparse
import collections
import io
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402

URL = "https://portal.spp.org/file-browser-api/download/operating-reserves?path=%2F{y}%2F{y}.zip"
FILE_URL = "https://portal.spp.org/file-browser-api/download/operating-reserves?path="
OUT_NAME = "spp_rtbm_or_cleared_hourly.parquet"
GMT_TO_MODEL_H = 6  # build_spp_lmp_reference._GMT_TO_MODEL_CLOCK_HOURS (SPP-51c)
_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MSTART = np.cumsum((0,) + _DAYS[:-1])


def _get(url: str, a: int, b: int) -> bytes:
    """Bytes ``a..b`` (inclusive) of ``url`` via an HTTP Range request, 4 retries."""
    for k in range(5):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={a}-{b}"})
            return urllib.request.urlopen(req, timeout=120).read()
        except Exception:  # noqa: BLE001 — transient portal/proxy errors
            if k == 4:
                raise
    raise RuntimeError("unreachable")


def zip_members(url: str) -> list[tuple[str, int, int, int]]:
    """(name, method, compressed size, local-header offset) of every member (ZIP64-aware)."""
    with urllib.request.urlopen(
        urllib.request.Request(url, method="HEAD"), timeout=60
    ) as h:
        n = int(h.headers["Content-Length"])
    tail = _get(url, max(0, n - 65536), n - 1)
    i = tail.rfind(b"PK\x05\x06")
    cd_size, cd_off = struct.unpack("<II", tail[i + 12 : i + 20])
    if cd_off == 0xFFFFFFFF:
        j = tail.rfind(b"PK\x06\x06")
        cd_size, cd_off = struct.unpack("<QQ", tail[j + 40 : j + 56])
    cd, p, out = _get(url, cd_off, cd_off + cd_size - 1), 0, []
    while cd[p : p + 4] == b"PK\x01\x02":
        (meth,) = struct.unpack("<H", cd[p + 10 : p + 12])
        (csz,) = struct.unpack("<I", cd[p + 20 : p + 24])
        fl, el, cl = struct.unpack("<HHH", cd[p + 28 : p + 34])
        (off,) = struct.unpack("<I", cd[p + 42 : p + 46])
        name = cd[p + 46 : p + 46 + fl].decode()
        extra, q = cd[p + 46 + fl : p + 46 + fl + el], 0
        while q < len(extra):  # ZIP64 extended info (csz / offset overflow)
            hid, hl = struct.unpack("<HH", extra[q : q + 4])
            if hid == 1:
                vals = list(
                    struct.unpack("<" + "Q" * (hl // 8), extra[q + 4 : q + 4 + hl])
                )
                (usz,) = struct.unpack("<I", cd[p + 24 : p + 28])
                if usz == 0xFFFFFFFF:
                    vals.pop(0)
                if csz == 0xFFFFFFFF:
                    csz = vals.pop(0)
                if off == 0xFFFFFFFF:
                    off = vals.pop(0)
            q += 4 + hl
        if name.lower().endswith(".csv"):
            out.append((name, meth, csz, off))
        p += 46 + fl + el + cl
    return out


def day_rows(url: str, members: list[tuple[str, int, int, int]]) -> list[pd.DataFrame]:
    """Parse every member of one operating day from a single contiguous range read."""
    members = sorted(members, key=lambda m: m[3])
    a = members[0][3]
    b = members[-1][3] + members[-1][2] + 30 + 512  # + local header + name/extra slack
    blob, frames = _get(url, a, b), []
    for _name, meth, csz, off in members:
        o = off - a
        fl, el = struct.unpack("<HH", blob[o + 26 : o + 30])
        raw = blob[o + 30 + fl + el : o + 30 + fl + el + csz]
        data = raw if meth == 0 else zlib.decompress(raw, -15)
        frames.append(
            pd.read_csv(
                io.BytesIO(data), skipinitialspace=True, dtype={"Reserve Zone": str}
            )
        )
    return frames


def model_hour(gmt_interval_end: pd.Series, year: int) -> np.ndarray:
    """Model-clock hour (0..8759, -1 off-calendar); identical to SPP-80's probe."""
    t = pd.to_datetime(gmt_interval_end, format="mixed")
    t = t - pd.Timedelta(minutes=5) - pd.Timedelta(hours=GMT_TO_MODEL_H)
    m, d, h = t.dt.month.to_numpy(), t.dt.day.to_numpy(), t.dt.hour.to_numpy()
    idx = (_MSTART[m - 1] + d - 1) * 24 + h
    bad = (t.dt.year.to_numpy() != year) | ((m == 2) & (d == 29))
    return np.where(bad, -1, idx)


def sampled_year(year: int, workers: int) -> pd.DataFrame:
    """One five-minute file per local hour (the :30 interval) for a year with no year zip.

    The portal serves the not-yet-archived year as ``/<yr>/<MM>/<DD>/RTBM-OR-<stamp>.csv``
    (288 files a day; the stamp is the local interval end). Fetching all ~105k files is
    avoidable: this takes the interval ending at local HH:30 of every local hour, so each
    model hour is a ONE-interval sample rather than a 12-interval mean (``n_int`` = 1
    records it). A missing file (404) is skipped.
    """
    stamps = pd.date_range(f"{year}-01-01 00:30", f"{year}-12-31 23:30", freq="h")

    def one(ts: pd.Timestamp) -> pd.DataFrame | None:
        path = f"/{ts:%Y}/{ts:%m}/{ts:%d}/RTBM-OR-{ts:%Y%m%d%H%M}.csv"
        u = FILE_URL + urllib.parse.quote(path, safe="")
        for k in range(5):
            try:
                data = urllib.request.urlopen(u, timeout=60).read()
                return pd.read_csv(io.BytesIO(data), skipinitialspace=True, dtype={"Reserve Zone": str})
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if k == 4:
                    raise
            except Exception:  # noqa: BLE001 — transient portal/proxy errors
                if k == 4:
                    raise
        return None

    with ThreadPoolExecutor(workers) as ex:
        parts = [f for f in ex.map(one, stamps) if f is not None]
    return pd.concat(parts, ignore_index=True)


def fetch_year(year: int, workers: int) -> pd.DataFrame:
    """Hourly SPP-wide cleared MW per product for ``year``."""
    url = URL.format(y=year)
    try:
        members = zip_members(url)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        members = None  # the current year is served per day, not as a year zip
    if members is None:
        df = sampled_year(year, workers)
    else:
        by_day = collections.defaultdict(list)
        for m in members:
            by_day[m[0].rsplit("/", 1)[0]].append(m)
        with ThreadPoolExecutor(workers) as ex:
            parts = [
                f
                for fs in ex.map(lambda k: day_rows(url, by_day[k]), sorted(by_day))
                for f in fs
            ]
        df = pd.concat(parts, ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    clr = [c for c in df.columns if c.endswith("_Clr")]
    df["Reserve Zone"] = df["Reserve Zone"].astype(str).str.strip()
    iv = df.drop_duplicates(["GMTIntervalEnd", "Reserve Zone"], keep="last")
    spp = iv[iv["Reserve Zone"] == "SPP"].set_index("GMTIntervalEnd")[clr]
    zs = iv[iv["Reserve Zone"] != "SPP"].groupby("GMTIntervalEnd")[clr].sum(min_count=1)
    sys_iv = zs.copy()
    sys_iv["src"] = "zone_sum"
    if len(spp):
        sys_iv.loc[spp.index, clr] = spp
        sys_iv.loc[spp.index, "src"] = "spp_row"
    sys_iv = sys_iv.reset_index()
    sys_iv["hour"] = model_hour(sys_iv["GMTIntervalEnd"], year)
    sys_iv = sys_iv[sys_iv.hour >= 0]
    agg = {c: "mean" for c in clr}
    agg.update(src="first", GMTIntervalEnd="count")
    out = sys_iv.groupby("hour").agg(agg).rename(columns={"GMTIntervalEnd": "n_int"})
    out.columns = [c.lower().removesuffix("_clr") for c in out.columns]
    out = out.reset_index()
    out.insert(0, "year", year)
    return out


def main() -> None:
    """Fetch the requested years and write the long-form hourly parquet."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument(
        "--part-dir",
        type=Path,
        help="write one <year>.parquet per year here instead of the combined output "
        "(lets years run as parallel processes); --merge then combines them",
    )
    ap.add_argument(
        "--merge", type=Path, help="combine <year>.parquet parts from this dir"
    )
    a = ap.parse_args()
    if a.merge:
        parts = sorted(a.merge.glob("*.parquet"))
        out = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    else:
        frames = []
        for y in a.years:
            f = fetch_year(y, a.workers)
            print(
                y,
                len(f),
                "hours;",
                f.n_int.sum(),
                "intervals;",
                f.src.value_counts().to_dict(),
                flush=True,
            )
            if a.part_dir:
                a.part_dir.mkdir(parents=True, exist_ok=True)
                f.to_parquet(a.part_dir / f"{y}.parquet", index=False)
            frames.append(f)
        if a.part_dir:
            return
        out = pd.concat(frames, ignore_index=True)
    num = [c for c in out.columns if c not in ("year", "hour", "src", "n_int")]
    out = out.astype(
        {
            "year": "int16",
            "hour": "int16",
            "n_int": "int16",
            **{c: "float32" for c in num},
        }
    )
    path = paths.RAW_DATA_DIR / "_validation-source" / OUT_NAME
    out.to_parquet(path, index=False)
    print("wrote", path, path.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
