"""Fetch SPP's published hourly capacity of generation on outage, by fuel, into one CSV.

Source: the SPP Marketplace portal product ``capacity-of-generation-on-outage``.
- Year zips: ``https://portal.spp.org/file-browser-api/download/capacity-of-generation-on-outage?path=%2F<Y>%2F<Y>.zip``.
- Where a year zip downloads empty (2025, measured 2026-09-26 and 2026-09-30), the per-day CSVs are
  fetched instead: ``?path=%2F<Y>%2F<MM>%2FCapacity-Gen-Outage-<YYYYMMDD>.csv``.

The daily files overlap at the day seam, so the LAST snapshot of each ``Market Hour`` is kept (SPP-84's
convention, ``scripts/probes/_spp84_published_outage_rebasis.py::load_outage_zips``). Output:
``data/raw/spp-gen-outage/spp_capacity_gen_outage_hourly.csv`` with the portal's own column names
(stripped of whitespace). Read by ``market_sim.data.spp_gas_outage`` under
``ScenarioConfig.spp_gas_crow_residual_outage`` (SPP-105).

Usage: ``python scripts/data/fetch_spp_capacity_gen_outage.py [--years 2019 ... 2025] [--from-dir <dir>]``.
``--from-dir`` reads already-downloaded ``o<Y>.zip`` files (and any ``<Y>/*.csv`` dailies) instead of
fetching.
"""

from __future__ import annotations

import argparse
import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from market_sim.config.paths import SPP_GEN_OUTAGE_CSV

BASE = "https://portal.spp.org/file-browser-api/download/capacity-of-generation-on-outage?path="


def _get(url: str) -> bytes:
    """Download ``url`` (empty bytes on a missing daily file)."""
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read()
    except Exception:  # noqa: BLE001 - a missing day is reported by coverage, not raised
        return b""


def _frames_from_zip(raw: bytes) -> list[pd.DataFrame]:
    """Every CSV inside one year zip."""
    z = zipfile.ZipFile(io.BytesIO(raw))
    return [
        pd.read_csv(io.BytesIO(z.read(n)))
        for n in sorted(z.namelist())
        if n.endswith(".csv")
    ]


def year_frames(y: int, from_dir: Path | None) -> list[pd.DataFrame]:
    """One year's portal CSVs: the year zip, else the per-day files."""
    if from_dir is not None:
        zp = from_dir / f"o{y}.zip"
        raw = zp.read_bytes() if zp.exists() else b""
    else:
        raw = _get(f"{BASE}%2F{y}%2F{y}.zip")
    if raw:
        return _frames_from_zip(raw)
    out = []
    for d in pd.date_range(f"{y}-01-01", f"{y}-12-31"):
        name = f"Capacity-Gen-Outage-{d:%Y%m%d}.csv"
        if from_dir is not None:
            p = from_dir / str(y) / name
            b = p.read_bytes() if p.exists() else b""
        else:
            b = _get(f"{BASE}%2F{y}%2F{d:%m}%2F{name}")
        if len(b) > 100:
            out.append(pd.read_csv(io.BytesIO(b)))
    return out


def main() -> None:
    """Fetch the requested years and write the one hourly CSV."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument("--from-dir", type=Path)
    ap.add_argument("--out", type=Path, default=SPP_GEN_OUTAGE_CSV)
    a = ap.parse_args()
    frames = []
    for y in a.years:
        fs = year_frames(y, a.from_dir)
        if not fs:
            raise SystemExit(f"{y}: no portal data")
        frames.extend(fs)
    for f in frames:  # the portal's header whitespace varies by file
        f.columns = [c.strip() for c in f.columns]
    d = pd.concat(frames)
    t = pd.to_datetime(d["Market Hour"], format="%m/%d/%Y %H:%M:%S", errors="coerce")
    d = d.assign(_t=t).dropna(subset=["_t"])
    d = d[d._t.dt.year.isin(a.years)]
    d = d.drop_duplicates("_t", keep="last").sort_values("_t").drop(columns="_t")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(a.out, index=False)
    print(f"wrote {a.out}: {len(d)} market hours, years {a.years}")


if __name__ == "__main__":
    main()
