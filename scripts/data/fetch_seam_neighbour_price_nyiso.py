"""Download NYISO day-ahead LBMP at its external proxy buses and internal zones.

WHY THIS EXISTS (NYISO-NEXT-10, 2026-09-28).  The seam-spread test NEXT-7
(``docs/records/nyiso/FINDING-nyiso-next7-star-node-2026-09-27.md`` §3(c)) asks for needs the
NY end of every seam as well as the neighbour's.  The repo holds only the
NYISO system-mean DA price (``_validation-source/actual_lmp_hourly_NYISO``).
NYISO's public MIS prices every scheduling point:

* ``damlbmp/<YYYYMM>01damlbmp_zone_csv.zip`` -- the eleven load zones plus the
  four AC proxy "zones" ``H Q``, ``O H``, ``PJM``, ``NPX``;
* ``damlbmp/<YYYYMM>01damlbmp_gen_csv.zip`` -- every generator bus, incl. the
  controllable-line and scheduled-line proxy buses kept below.

Kept rows (names as published; verified in the 2023-01-01 files):

    zone file: all 15 rows
    gen file : HQ_GEN_CEDARS_PROXY, HQ_GEN_IMPORT, NPX_GEN_CSC, NPX_GEN_1385_PROXY,
               PJM_GEN_KEYSTONE, PJM_GEN_HTP_PROXY, PJM_GEN_VFT_PROXY,
               PJM_GEN_NEPTUNE_PROXY

``Time Stamp`` is hour-beginning, Eastern prevailing time; the fall-back hour
appears twice, so each (day, name) row is given its publication ``seq`` within
the day -- the ISO-NE fetcher's DST construction.

Output: ``data/raw/seam-neighbour-price/nyiso/NYISO_dam_proxy_lbmp_<year>.csv.gz``,
columns ``date, seq, time_stamp, name, ptid, lbmp, losses, congestion`` (USD).

Usage:
    uv run python scripts/data/fetch_seam_neighbour_price_nyiso.py --years 2021 2022 2023 2024 2025
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

RAW_DIR = RAW_DATA_DIR / "seam-neighbour-price" / "nyiso"
STEM = "NYISO_dam_proxy_lbmp"
URL = "http://mis.nyiso.com/public/csv/damlbmp/{ym}01damlbmp_{kind}_csv.zip"

#: Generator-file proxy buses kept (the zone file is kept whole).
GEN_PROXIES = frozenset(
    {
        "HQ_GEN_CEDARS_PROXY",
        "HQ_GEN_IMPORT",
        "NPX_GEN_CSC",
        "NPX_GEN_1385_PROXY",
        "PJM_GEN_KEYSTONE",
        "PJM_GEN_HTP_PROXY",
        "PJM_GEN_VFT_PROXY",
        "PJM_GEN_NEPTUNE_PROXY",
    }
)
COLUMNS = ("date", "seq", "time_stamp", "name", "ptid", "lbmp", "losses", "congestion")


def _get(url: str, retries: int = 4) -> bytes:
    """GET ``url`` with back-off on transient failures."""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=300) as resp:
                return resp.read()
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if attempt == retries:
                raise
            time.sleep(2 ** (attempt + 1))
    raise AssertionError("unreachable")


def reduce_month(body: bytes, keep: frozenset[str] | None) -> list[dict]:
    """Reduce one monthly zip (one CSV per day) to the kept names.

    ``keep=None`` keeps every row (the zone file).  ``seq`` counts each name's
    rows within its day in publication order, so the doubled fall-back hour
    stays two distinct rows.
    """
    out: list[dict] = []
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        for member in sorted(zf.namelist()):
            seen: dict[str, int] = {}
            text = zf.read(member).decode("utf-8-sig")
            for r in csv.DictReader(io.StringIO(text)):
                name = r["Name"]
                if keep is not None and name not in keep:
                    continue
                seq = seen.get(name, 0)
                seen[name] = seq + 1
                ts = r["Time Stamp"]
                out.append(
                    {
                        "date": f"{ts[6:10]}-{ts[0:2]}-{ts[3:5]}",
                        "seq": seq,
                        "time_stamp": ts,
                        "name": name,
                        "ptid": r["PTID"],
                        "lbmp": r["LBMP ($/MWHr)"],
                        "losses": r["Marginal Cost Losses ($/MWHr)"],
                        "congestion": r["Marginal Cost Congestion ($/MWHr)"],
                    }
                )
    return out


def fetch_year(year: int, dest_dir: Path = RAW_DIR) -> Path:
    """Fetch the twelve monthly zone + gen zips for ``year``; write one CSV."""
    rows: list[dict] = []
    for m in range(1, 13):
        ym = f"{year}{m:02d}"
        rows += reduce_month(_get(URL.format(ym=ym, kind="zone")), None)
        rows += reduce_month(_get(URL.format(ym=ym, kind="gen")), GEN_PROXIES)
        print(f"  {ym}: {len(rows)} rows cumulative", flush=True)
    rows.sort(key=lambda r: (r["name"], r["date"], r["seq"]))
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{STEM}_{year}.csv.gz"
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(COLUMNS), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    # mtime=0 keeps the gzip byte-deterministic, so SHA256SUMS is stable.
    path.write_bytes(gzip.compress(buf.getvalue().encode(), mtime=0))
    return path


def main(argv: list[str] | None = None) -> int:
    """Fetch the requested years."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--years", nargs="+", type=int, required=True)
    p.add_argument("--out-dir", type=Path, default=RAW_DIR)
    args = p.parse_args(argv)
    for y in args.years:
        print(f"wrote {fetch_year(y, args.out_dir)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
