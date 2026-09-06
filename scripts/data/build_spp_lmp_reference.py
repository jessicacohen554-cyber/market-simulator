"""Build SPP's realized hub-LMP reference parquet from the SPP Integrated Marketplace.

SPP is a MISO neighbor on the reference-price seam (``INTERFACE_NEIGHBORS["MISO"]``).
Until now that seam used a FLAT structural ``marginal_heat_rate`` because there was
no realized SPP LMP in the repo (the ``DAMLZHBSPP_*`` / ``RTMLZHBSPP_*`` zips in
``data/raw/lmp-data`` are ERCOT "Settlement Point Prices" — HB_HOUSTON/HB_HUBAVG —
NOT Southwest Power Pool). This script fetches the real SPP system-hub LMP and
emits ``data/raw/_validation-source/actual_lmp_hourly_SPP.parquet`` in the exact
schema the other ISO sidecars use (``year`` int16, ``hour`` int16 0..8759,
``rt`` float32, ``da`` float32; 8760 rows/year), so
``scripts/data/derive_neighbor_hr_by_year.py --iso MISO`` can anchor the SPP seam to
the neighbor's OWN realized implied heat rate per backcast year (CLAUDE.md
rule #12 — measured neighbor price-formation input; never tuned to MISO's
interchange, rule #11).

Source — SPP Marketplace public file browser (``portal.spp.org``, the host
``marketplace.spp.org`` redirects to):

    https://portal.spp.org/file-browser-api/download/<fsName>?path=<path>

API FORM, re-discovered from the portal bundle 2026-09-06 (lane SPP-12).
``portal.spp.org`` is a React SPA; the authoritative definition of the two calls
is its own bundle, ``/static/js/main.<hash>.js`` (``e2bac944`` on 2026-09-06).
Re-read that bundle — never a memory of this docstring — if the calls stop
working. The grammar it encodes is UNCHANGED from the form above:

  * listing  ``GET /file-browser-api/?fsName=<fs>&path=<p>&type=folder``
    (``URLSearchParams``, so ``/`` arrives percent-encoded; the trailing slash on
    ``file-browser-api/`` is part of the route — dropping it 404s, and omitting
    ``type`` 404s). The SPA's first call is ``path=""``; a folder row's own
    ``path`` field drives navigation.
  * download ``GET /file-browser-api/download/<fsName>?path=<p>``
  * ``fsName`` is the page's ``pcValue``, readable at
    ``GET /api/pageConfig/by-slug/<page-slug>`` — for these two products it
    equals the slug (``rtbm-lmp-by-location``, ``da-lmp-by-settlement-location``).

What DID change is authorization: both calls now carry an ``X-SPP-UI-Token``
header (the SPA's ``userCookie``), and as of 2026-09-06 an anonymous caller —
which is what this script is — gets **no data** from either. Measured that day
against ``rtbm-lmp-by-location``, ``da-lmp-by-settlement-location``,
``hourly-load``, ``generation-mix-historical``, ``{da,rtbm}-binding-constraints``,
``{da,rtbm}-mcp``, ``capacity-of-generation-on-outage`` and ``ver-curtailments``:
every listing returns HTTP 200 with a literal ``[]`` at every path/type form, and
every download returns HTTP 404 — from SPP's own Tomcat (``JSESSIONID`` +
Spring-Security headers), not from an intermediary. The metadata endpoints stay
public and confirm the request is well-formed: ``/api/pageConfig/by-slug/<slug>``
returns ``isPublic: true`` for all of them, and an invented ``fsName`` 404s where
a real one 200s, so the 200-with-``[]`` is authorization, not a bad key.
``/api/principal`` reports ``unauthenticatedUser: true, uiTokenPresent: false``.
SPP's own "SPP Public Data Access" guide (Stakeholder Center > User Guides, APIs
& Integrations > Technical Reference Documents > Public Data) is the reference
for the Portal and FTP routes to the same products.

The consequence for this script: it cannot fetch until a Marketplace credential
supplies ``X-SPP-UI-Token`` (or the FTP route is wired). ``--per-hub`` below is
implemented and unit-tested against a fixture, but has never been run against
live SPP data. Blocked-URL table and the manual manifest:
``docs/handoffs/FINDING-spp-12-2026-09-06.md``.

  * System hub = simple mean of ``SPPNORTH_HUB`` and ``SPPSOUTH_HUB`` (the two
    SPP trading hubs), the price the MISO-West border sees from SPP.
  * Day-Ahead  (``da``): ``da-lmp-by-settlement-location`` (hourly).
  * Real-Time  (``rt``): ``rtbm-lmp-by-location`` — SPP's own hourly RTBM LMP
    rollup (the monthly file is hourly, not 5-minute).

Every year is read from the same product: the SPP monthly WIDE files
``{DA-LMP,RTBM-LMP}-MONTHLY-SL-YYYYMM.csv`` (Date, Settlement Location, PNODE,
Price Type, HE01..HE24 — already hourly on the local clock). The only
difference is where the 12 monthly files live, which the portal decides by a
~13-month rolling window:

  * 2025 (live window) — each monthly file is served directly at
    ``/<year>/<MM>/{prefix}-MONTHLY-SL-YYYYMM.csv``.
  * 2023/2024 (archived) — the daily window has aged out and the year is one
    big ``/<year>/<year>.zip`` (~290 MB DA, ~5 GB RT of 5-minute By_Interval
    files). The 12 monthly hourly files are ALSO stored inside that zip, so we
    read the zip's (zip64) central directory over HTTP range requests and
    range-fetch + inflate ONLY those 12 small members — never the multi-GB body.

Using the monthly hourly product for every year keeps the three backcast years
methodologically identical (no per-year 5-minute-vs-hourly seam) and avoids a
~10 GB download.

Hour calendar (identical to ``scripts/data/derive_actual_lmp.py`` so the SPP sidecar
lines up with every other ISO): the model's fixed non-leap 8760-hour LOCAL
clock. The monthly wide files are already local-clock hour-ending HE01..HE24
(SPP pre-folds the DST 23/25-hour days into 24 columns), mapped HE-nn ->
hour-beginning nn-1; Feb 29 is then dropped so a leap year still lands on 8760
rows. SPP runs on Central Prevailing Time, the model's dispatch clock.

The raw SPP exports for 2023-24 are NOT committed — like the ERCOT/NYISO DA
source zips, only the reduced sidecar parquet is the durable record. Re-run
this script to refresh it.

Two outputs, from the SAME parsed monthly frames and the SAME 8760 calendar:

  * default (system hub) — ``actual_lmp_hourly_SPP.parquet``,
    ``year``/``hour``/``rt``/``da``, the simple mean of the two hubs. This is the
    seam input ``derive_neighbor_hr_by_year.py`` reads and it is BYTE-FROZEN:
    ``--per-hub`` is purely additive and must never move it. Proof that this
    change does not (pre-change vs post-change parser over a fixture, and the
    system series equal to the NaN-skipping mean of the two hub series):
    ``docs/handoffs/FINDING-spp-12-2026-09-06.md`` §3. A permanent guard test
    belongs with the lane that owns ``tests/`` — SPP-12 does not.
  * ``--per-hub`` — ``actual_lmp_hourly_zonal_SPP.parquet``,
    ``year``/``hour``/``zone``/``rt``/``da`` with one row per hub per hour, the
    per-zone benchmark SPP-31 curates and the P1 topology card's N↔S hub-spread
    evidence. ``zone`` carries the SPP settlement-location name
    (``SPPNORTH_HUB`` / ``SPPSOUTH_HUB``) and NOT a model zone name: SPP has no
    registered topology yet, and inventing one here would pre-empt card P1. The
    lane that registers SPP re-keys ``zone`` onto model zones.

Usage:
    python scripts/data/build_spp_lmp_reference.py [--years 2023 2024 2025] \
        [--out data/raw/_validation-source/actual_lmp_hourly_SPP.parquet]
    python scripts/data/build_spp_lmp_reference.py --per-hub \
        [--out data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet]
"""

from __future__ import annotations

import argparse
import io
import struct
import subprocess
import sys
import urllib.parse
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402  (resolves the data root)

# The model's fixed non-leap local dispatch calendar (matches derive_actual_lmp).
_HOURS_PER_YEAR = 8760
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = tuple(int(sum(_DAYS_IN_MONTH[:m]) * 24) for m in range(12))

HUBS = ("SPPNORTH_HUB", "SPPSOUTH_HUB")  # SPP trading hubs -> simple-mean system hub

BASE = "https://portal.spp.org/file-browser-api/download/"
FS_DA = "da-lmp-by-settlement-location"
FS_RT = "rtbm-lmp-by-location"
HE_COLS = [f"HE{h:02d}" for h in range(1, 25)]


# ── HTTP / zip plumbing ──────────────────────────────────────────────────────
def _curl(url: str, byte_range: str | None = None, retries: int = 5) -> bytes:
    """GET ``url`` (optionally a byte range) via curl, retrying on transient error."""
    cmd = ["curl", "-sS", "-m", "300", "--fail"]
    if byte_range is not None:
        cmd += ["-r", byte_range]
    cmd.append(url)
    last = b""
    for _ in range(retries):
        p = subprocess.run(cmd, capture_output=True)
        if p.returncode == 0 and p.stdout:
            return p.stdout
        last = p.stderr
    raise RuntimeError(f"curl failed ({byte_range}) {url}: {last[:200]!r}")


def _dl(fs_name: str, path: str, byte_range: str | None = None) -> bytes:
    """Fetch a file (or byte range) from the SPP portal file browser."""
    url = BASE + fs_name + "?path=" + urllib.parse.quote(path, safe="")
    return _curl(url, byte_range)


def _try_dl(fs_name: str, path: str) -> bytes | None:
    """Fetch a whole file, returning ``None`` if it is absent (404) or fails."""
    try:
        return _dl(fs_name, path)
    except RuntimeError:
        return None


def _remote_size(fs_name: str, path: str) -> int:
    """Total byte length of a remote file, via the file-browser directory listing."""
    import json

    parent = path.rsplit("/", 1)[0] or "/"
    name = path.rsplit("/", 1)[-1]
    url = (
        "https://portal.spp.org/file-browser-api/?fsName="
        + urllib.parse.quote(fs_name, safe="")
        + "&path="
        + urllib.parse.quote(parent, safe="")
        + "&type=folder"
    )
    for item in json.loads(_curl(url)):
        if item.get("name") == name:
            return int(item["size"])
    raise RuntimeError(f"{path} not found in listing of {parent}")


def _central_directory(fs_name: str, path: str, size: int):
    """Parse a (zip64) zip's central directory via range requests.

    Returns ``[(name, comp_size, local_header_offset, method), ...]`` for every
    member, read without downloading the archive body.
    """
    tail_n = min(size, 1 << 20)
    tail = _dl(fs_name, path, f"{size - tail_n}-{size - 1}")
    j = tail.rfind(b"PK\x06\x07")  # zip64 EOCD locator
    if j >= 0:
        z64_off = struct.unpack("<Q", tail[j + 8 : j + 16])[0]
        z = _dl(fs_name, path, f"{z64_off}-{z64_off + 55}")
        cd_size = struct.unpack("<Q", z[40:48])[0]
        cd_off = struct.unpack("<Q", z[48:56])[0]
    else:
        i = tail.rfind(b"PK\x05\x06")
        eocd = tail[i : i + 22]
        cd_size = struct.unpack("<I", eocd[12:16])[0]
        cd_off = struct.unpack("<I", eocd[16:20])[0]
    cd = _dl(fs_name, path, f"{cd_off}-{cd_off + cd_size - 1}")
    out = []
    p = 0
    while p < len(cd) - 46 and cd[p : p + 4] == b"PK\x01\x02":
        method = struct.unpack("<H", cd[p + 10 : p + 12])[0]
        comp = struct.unpack("<I", cd[p + 20 : p + 24])[0]
        uncomp = struct.unpack("<I", cd[p + 24 : p + 28])[0]
        nlen = struct.unpack("<H", cd[p + 28 : p + 30])[0]
        elen = struct.unpack("<H", cd[p + 30 : p + 32])[0]
        clen = struct.unpack("<H", cd[p + 32 : p + 34])[0]
        lho = struct.unpack("<I", cd[p + 42 : p + 46])[0]
        name = cd[p + 46 : p + 46 + nlen].decode("latin1")
        extra = cd[p + 46 + nlen : p + 46 + nlen + elen]
        if 0xFFFFFFFF in (comp, uncomp, lho):  # zip64 extra overrides placeholders
            q = 0
            while q < len(extra) - 4:
                tag = struct.unpack("<H", extra[q : q + 2])[0]
                sz = struct.unpack("<H", extra[q + 2 : q + 4])[0]
                if tag == 0x0001:
                    vals = extra[q + 4 : q + 4 + sz]
                    k = 0
                    if uncomp == 0xFFFFFFFF:
                        k += 8
                    if comp == 0xFFFFFFFF:
                        comp = struct.unpack("<Q", vals[k : k + 8])[0]
                        k += 8
                    if lho == 0xFFFFFFFF:
                        lho = struct.unpack("<Q", vals[k : k + 8])[0]
                    break
                q += 4 + sz
        out.append((name, comp, lho, method))
        p += 46 + nlen + elen + clen
    return out


def _read_member(fs_name: str, path: str, comp: int, lho: int, method: int) -> bytes:
    """Range-fetch and inflate one zip member from its central-directory record."""
    hdr = _dl(fs_name, path, f"{lho}-{lho + 29}")
    nlen = struct.unpack("<H", hdr[26:28])[0]
    elen = struct.unpack("<H", hdr[28:30])[0]
    start = lho + 30 + nlen + elen
    raw = _dl(fs_name, path, f"{start}-{start + comp - 1}")
    return raw if method == 0 else zlib.decompress(raw, -15)


# ── monthly-wide source → dense 8760 ─────────────────────────────────────────
def _monthly_bytes(fs_name: str, prefix: str, year: int) -> dict[int, bytes]:
    """Return ``{month: csv_bytes}`` for a year's 12 monthly wide hub files.

    Tries the live per-month path first (recent years); if absent, falls back to
    the archived ``/<year>/<year>.zip`` and range-fetches only the MONTHLY members.
    """
    out: dict[int, bytes] = {}
    for month in range(1, 13):
        path = f"/{year}/{month:02d}/{prefix}-MONTHLY-SL-{year}{month:02d}.csv"
        data = _try_dl(fs_name, path)
        if data is not None:
            out[month] = data
    if len(out) == 12:
        return out
    # Archived year: pull the 12 monthly members straight out of the zip.
    zip_path = f"/{year}/{year}.zip"
    size = _remote_size(fs_name, zip_path)
    for name, comp, lho, method in _central_directory(fs_name, zip_path, size):
        base = name.rsplit("/", 1)[-1].upper()
        if not (base.startswith(prefix.upper()) and "MONTHLY-SL" in base):
            continue
        month = int(base[-6:-4])  # ...-YYYYMM.csv
        out.setdefault(month, _read_member(fs_name, zip_path, comp, lho, method))
    return out


def _split_ymd(date_str: str) -> tuple[int, int, int]:
    """``(year, month, day)`` from an SPP date cell — ``YYYY/MM/DD`` or ``M/D/YYYY``."""
    a = date_str.strip().split("/")
    if len(a[0]) == 4:  # YYYY/MM/DD
        return int(a[0]), int(a[1]), int(a[2])
    return int(a[2]), int(a[0]), int(a[1])  # M/D/YYYY (US order)


def _parse_monthly(bytes_by_month: dict[int, bytes], year: int) -> np.ndarray:
    """Dense fixed-8760 system-hub series from a year's monthly wide files.

    Each file is wide (Date, Settlement Location Name, PNODE Name, Price Type,
    HE01..HE24). Only ``Price Type == LMP`` rows for the two hubs are used; the
    two hubs are simple-averaged per (date, HE), HE-nn maps to hour-beginning
    nn-1, and the result lands on the model's non-leap local calendar (Feb 29
    dropped). Missing HE cells stay NaN (e.g. the DST spring-forward hour).
    Rows from a neighbouring year (the monthly files carry a next-day spillover,
    e.g. a ``2026/01/01`` row in the December file) are dropped so they cannot
    collide onto ``year``'s own calendar.
    """
    if not bytes_by_month:
        return np.full(_HOURS_PER_YEAR, np.nan)
    df = _monthly_frame(bytes_by_month)
    # Simple-mean the two hubs per day, keeping the 24 HE columns.
    grp = df.groupby("Date")[HE_COLS].mean()
    return _dense_from_daily(grp, year)


def _monthly_frame(bytes_by_month: dict[int, bytes]) -> pd.DataFrame:
    """Concatenated hub ``LMP`` rows of a year's monthly wide files.

    Shared by the system-hub and per-hub parsers so both see byte-identical
    input rows; only the aggregation that follows differs.
    """
    frames = []
    for data in bytes_by_month.values():
        df = pd.read_csv(io.BytesIO(data), skipinitialspace=True)
        df.columns = [c.strip() for c in df.columns]
        df = df[
            (df["Price Type"] == "LMP") & (df["Settlement Location Name"].isin(HUBS))
        ]
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def _parse_monthly_by_hub(
    bytes_by_month: dict[int, bytes], year: int
) -> dict[str, np.ndarray]:
    """``{hub: dense 8760}`` from a year's monthly wide files.

    Identical to :func:`_parse_monthly` except that the per-day mean is taken
    within one hub instead of across both, so the system-hub series is exactly
    the (NaN-skipping) mean of these two — which is what the byte-identity test
    asserts. A hub absent from the source lands as an all-NaN series rather than
    a missing key, so the emitted frame is rectangular.
    """
    if not bytes_by_month:
        return {hub: np.full(_HOURS_PER_YEAR, np.nan) for hub in HUBS}
    df = _monthly_frame(bytes_by_month)
    out: dict[str, np.ndarray] = {}
    for hub in HUBS:
        rows = df[df["Settlement Location Name"] == hub]
        if rows.empty:
            out[hub] = np.full(_HOURS_PER_YEAR, np.nan)
            continue
        out[hub] = _dense_from_daily(rows.groupby("Date")[HE_COLS].mean(), year)
    return out


def _dense_from_daily(grp: pd.DataFrame, year: int) -> np.ndarray:
    """Map a ``Date`` x ``HE01..HE24`` frame onto the model's non-leap 8760."""
    # SPP's monthly Date format drifts across years ("YYYY/MM/DD" in 2023/2025,
    # "M/D/YYYY" in 2024), so parse Y/M/D by hand rather than a fixed strptime
    # format, and keep only this build year's rows (drop the next-year spillover).
    ymd = [_split_ymd(s) for s in grp.index]
    keep = [i for i, (y, _, _) in enumerate(ymd) if y == year]
    arr = grp.to_numpy(float)[keep]  # (n_days, 24)
    month = np.array([ymd[i][1] for i in keep])
    day = np.array([ymd[i][2] for i in keep])
    # Hour-of-year for HE01 (hour-beginning 0) of each day; +0..23 across the row.
    base = np.array([_MONTH_START_HOUR[m - 1] for m in month]) + (day - 1) * 24
    base = np.where((month == 2) & (day == 29), -1, base)  # drop Feb 29
    dense = np.full(_HOURS_PER_YEAR, np.nan)
    for i in range(len(arr)):
        if base[i] < 0:
            continue
        hoy = base[i] + np.arange(24)
        valid = hoy < _HOURS_PER_YEAR
        dense[hoy[valid]] = arr[i, :24][valid]
    return dense


def _fetch_year(fs_name: str, prefix: str, year: int) -> np.ndarray:
    """Dense 8760 system-hub series for one year/market."""
    return _parse_monthly(_monthly_bytes(fs_name, prefix, year), year)


def _fetch_year_by_hub(fs_name: str, prefix: str, year: int) -> dict[str, np.ndarray]:
    """``{hub: dense 8760}`` for one year/market."""
    return _parse_monthly_by_hub(_monthly_bytes(fs_name, prefix, year), year)


# ── assembly ─────────────────────────────────────────────────────────────────
def build(years) -> pd.DataFrame:
    """Return the dense SPP hub-LMP sidecar frame for ``years``."""
    frames = []
    for year in years:
        da = _fetch_year(FS_DA, "DA-LMP", year)
        rt = _fetch_year(FS_RT, "RTBM-LMP", year)
        frames.append(
            pd.DataFrame(
                {
                    "year": np.int16(year),
                    "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
                    "rt": rt.astype(np.float32),
                    "da": da.astype(np.float32),
                }
            )
        )
        print(
            f"  SPP {year}: da ${np.nanmean(da):.2f} rt ${np.nanmean(rt):.2f} "
            f"(da nan {int(np.isnan(da).sum())}, rt nan {int(np.isnan(rt).sum())})",
            flush=True,
        )
    return pd.concat(frames, ignore_index=True)


def build_per_hub(years) -> pd.DataFrame:
    """Return the per-hub SPP LMP frame for ``years``.

    One row per (year, hour, hub): ``year``/``hour``/``zone``/``rt``/``da`` on the
    same fixed non-leap 8760 local calendar the system-hub sidecar uses. ``zone``
    is the SPP settlement-location name, not a model zone (see module docstring).
    """
    frames = []
    for year in years:
        da = _fetch_year_by_hub(FS_DA, "DA-LMP", year)
        rt = _fetch_year_by_hub(FS_RT, "RTBM-LMP", year)
        for hub in HUBS:
            frames.append(
                pd.DataFrame(
                    {
                        "year": np.int16(year),
                        "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
                        "zone": hub,
                        "rt": rt[hub].astype(np.float32),
                        "da": da[hub].astype(np.float32),
                    }
                )
            )
            print(
                f"  SPP {year} {hub}: da ${np.nanmean(da[hub]):.2f} "
                f"rt ${np.nanmean(rt[hub]):.2f} "
                f"(da nan {int(np.isnan(da[hub]).sum())}, "
                f"rt nan {int(np.isnan(rt[hub]).sum())})",
                flush=True,
            )
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--per-hub",
        action="store_true",
        help=(
            "emit one row per SPP trading hub (year/hour/zone/rt/da) instead of "
            "the simple-mean system hub; changes the default --out to "
            "actual_lmp_hourly_zonal_SPP.parquet"
        ),
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output parquet (default depends on --per-hub)",
    )
    args = ap.parse_args()
    out = args.out
    if out is None:
        name = (
            "actual_lmp_hourly_zonal_SPP.parquet"
            if args.per_hub
            else "actual_lmp_hourly_SPP.parquet"
        )
        out = paths.CALIBRATION_DIR / name
    frame = build_per_hub(args.years) if args.per_hub else build(args.years)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out, index=False)
    print(f"wrote {out} ({len(frame)} rows, {frame['year'].nunique()} years)")


if __name__ == "__main__":
    main()
