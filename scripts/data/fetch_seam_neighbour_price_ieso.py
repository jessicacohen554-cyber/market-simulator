"""Download IESO (Ontario) hourly prices and the Bank of Canada USD/CAD rate.

WHY THIS EXISTS (NYISO-NEXT-10, 2026-09-28).  NEXT-7
(``docs/records/nyiso/FINDING-nyiso-next7-star-node-2026-09-27.md`` §3(c)) found the repo held
no Ontario price, so the NYISO-IESO seam could not be tested against its own
spread.  Two IESO public reports carry it, pre-Market-Renewal:

* ``PriceHOEPPredispOR/PUB_PriceHOEPPredispOR_<year>.csv`` -- the hourly
  Ontario energy price (HOEP), one row per EST hour.
* ``RealtimeMktPriceYear/PUB_RealtimeMktPriceYear_<year>.csv`` -- the 5-minute
  real-time market clearing price (MCP) by pricing zone, incl. ``Ontario`` and
  the ``New-York`` intertie zone (which departs from Ontario only when the NY
  intertie is congested).  Reduced here to the hourly mean of the twelve
  intervals -- HOEP's own construction.

**Coverage stops at 2025-04-30 HE24.**  The IESO Market Renewal Program went
live 2025-05-01; HOEP and the MCP ceased, and their successors (Ontario Zonal
Price, intertie LMPs) are published only as daily/hourly XML on a rolling
~90-day public archive (checked 2026-09-28: the oldest ``DAHourlyIntertieLMP``
file is 2026-06-29; no yearly file exists on reports-public, its sandbox, the
IESO Data Directory, or the Wayback Machine).  May-Dec 2025 is therefore a
DATA GAP, recorded in the README.

IESO prices are CAD and IESO hours are EST all year (no DST).  The Bank of
Canada Valet series ``FXUSDCAD`` (daily average, CAD per USD; business days
only) is fetched alongside so the curation can convert to USD.

Outputs under ``data/raw/seam-neighbour-price/ieso/``:
``IESO_hourly_price_<year>.csv`` (``date, hour_ending_est, hoep_cad,
ontario_mcp_cad, new_york_mcp_cad``) and ``BOC_FXUSDCAD.csv``
(``date, usd_cad``).

Usage:
    uv run python scripts/data/fetch_seam_neighbour_price_ieso.py --years 2021 2022 2023 2024 2025
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

RAW_DIR = RAW_DATA_DIR / "seam-neighbour-price" / "ieso"
BASE = "https://reports-public.ieso.ca/public"
USER_AGENT = "Mozilla/5.0 (market-sim seam-neighbour-price intake)"
HOEP_URL = BASE + "/PriceHOEPPredispOR/PUB_PriceHOEPPredispOR_{year}.csv"
MCP_URL = BASE + "/RealtimeMktPriceYear/PUB_RealtimeMktPriceYear_{year}.csv"
FX_URL = (
    "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/csv"
    "?start_date={start}&end_date={end}"
)
#: The MCP report's zone header labels this reducer keeps (row 4 of the file).
MCP_ZONES = {"Ontario": "ontario_mcp_cad", "New-York": "new_york_mcp_cad"}
COLUMNS = ("date", "hour_ending_est", "hoep_cad", "ontario_mcp_cad", "new_york_mcp_cad")


def _get(url: str, retries: int = 4) -> str:
    """GET ``url`` and return the body as text (BOM stripped).

    Sends a browser-like ``User-Agent`` (the IESO host drops urllib's default
    agent with an empty reply) and retries transient disconnects with back-off.
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return resp.read().decode("utf-8-sig")
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if attempt == retries:
                raise
            time.sleep(2 ** (attempt + 1))
    raise AssertionError("unreachable")


def parse_hoep(text: str) -> dict[tuple[str, int], float]:
    """Parse the yearly HOEP report into ``{(date, hour_ending): hoep}``."""
    out: dict[tuple[str, int], float] = {}
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 3 or not row[0][:4].isdigit() or row[2] == "":
            continue
        out[(row[0], int(row[1]))] = float(row[2])
    return out


def parse_mcp(text: str) -> dict[tuple[str, int], dict[str, float]]:
    """Reduce the 5-min MCP report to the hourly mean ENGY price per kept zone.

    The zone label sits on the row above the ``DELIVERY_DATE`` header and the
    ``ENGY`` column is located under it, so a column-order change in a vintage
    fails loudly (a missing zone raises) rather than mis-reading a column.
    """
    rows = list(csv.reader(io.StringIO(text)))
    hdr = next(i for i, r in enumerate(rows) if r and r[0] == "DELIVERY_DATE")
    zones, fields = rows[hdr - 1], rows[hdr]
    col = {}
    for j, (z, f) in enumerate(zip(zones, fields)):
        if z in MCP_ZONES and f == "ENGY":
            col[MCP_ZONES[z]] = j
    if set(col) != set(MCP_ZONES.values()):
        raise RuntimeError(f"MCP report missing ENGY columns: {col}")
    acc: dict[tuple[str, int], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for r in rows[hdr + 1 :]:
        if len(r) <= max(col.values()) or not r[0][:4].isdigit():
            continue
        for name, j in col.items():
            if r[j] != "":
                acc[(r[0], int(r[1]))][name].append(float(r[j]))
    return {k: {n: sum(v) / len(v) for n, v in d.items()} for k, d in acc.items()}


def fetch_year(year: int, dest_dir: Path = RAW_DIR) -> Path:
    """Fetch and join one year's HOEP and hourly MCP; write one CSV."""
    hoep = parse_hoep(_get(HOEP_URL.format(year=year)))
    mcp = parse_mcp(_get(MCP_URL.format(year=year)))
    keys = sorted(set(hoep) | set(mcp))
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"IESO_hourly_price_{year}.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for d, h in keys:
            m = mcp.get((d, h), {})
            w.writerow(
                [
                    d,
                    h,
                    hoep.get((d, h), ""),
                    round(m["ontario_mcp_cad"], 4) if "ontario_mcp_cad" in m else "",
                    round(m["new_york_mcp_cad"], 4) if "new_york_mcp_cad" in m else "",
                ]
            )
    return path


def fetch_fx(start: str, end: str, dest_dir: Path = RAW_DIR) -> Path:
    """Fetch the Bank of Canada daily USD/CAD series for ``[start, end]``."""
    text = _get(FX_URL.format(start=start, end=end))
    rows = list(csv.reader(io.StringIO(text)))
    i = next(k for k, r in enumerate(rows) if r[:2] == ["date", "FXUSDCAD"])
    path = dest_dir / "BOC_FXUSDCAD.csv"
    dest_dir.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "usd_cad"])
        for r in rows[i + 1 :]:
            if len(r) == 2 and r[1]:
                w.writerow(r)
    return path


def main(argv: list[str] | None = None) -> int:
    """Fetch the requested years plus the FX series spanning them."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--years", nargs="+", type=int, required=True)
    p.add_argument("--out-dir", type=Path, default=RAW_DIR)
    args = p.parse_args(argv)
    for y in args.years:
        print(f"wrote {fetch_year(y, args.out_dir)}", flush=True)
    fx = fetch_fx(
        f"{min(args.years) - 1}-12-01", f"{max(args.years)}-12-31", args.out_dir
    )
    print(f"wrote {fx}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
