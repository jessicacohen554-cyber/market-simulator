#!/usr/bin/env python3
"""Build the SOCO footprint hourly price index from FERC EQR transactions — STOP-gated.

Lane SOCO-13 (``docs/multi-iso/soco-addition-plan-2026-09.md`` §8 W1; owner
ruling card S2, both limbs, 2026-09-13). Southern Company publishes no LMP, no
day-ahead price and no hourly index, and SEEM publishes no price. The one
public, transaction-level, measured price source covering the footprint is
FERC's Electric Quarterly Report (EQR): every jurisdictional seller files, per
transaction, product, delivery point, begin/end datetime, quantity and price.
This script streams the quarterly bulk EQR files, keeps the rows delivered
inside the ``SOCO`` balancing authority, builds a footprint-hourly
volume-weighted price of short-term wholesale energy, and runs the STOP gate
that decides whether the result may be committed as
``actual_lmp_hourly_SOCO.parquet``.

EVERY filter, allocation rule and threshold below was fixed in
``docs/handoffs/PRECOMMIT-soco-13-2026-09-13.md`` (pushed at ``ee32cf75``)
BEFORE any price or quantity value was read. Nothing here reads a model
residual — no SOCO model run exists (CLAUDE.md rule 1 ``[R-STRUCT]``). The gate
can refuse the series; it can never promote a run.

What is built (``data/raw/ferc-eqr/``, the committed raw store; every path
resolves through ``config/paths.py``):

* ``eqr_soco_pod_transactions.parquet`` — every EQR transaction row whose
  ``point_of_delivery_balancing_authority`` is ``SOCO``, 2023–2025, all 26
  fields plus the filing member and quarter it came from: the footprint's raw
  extract, so everything below regenerates without a 43 GB re-fetch.
* ``soco_eqr_hourly_utc.parquet`` — the per-UTC-hour product
  (``hour_utc · price · mwh · n_rows · n_sellers · mwh_15min``).
* ``seem_auditor_monthly_prices.csv`` — the SEEM Independent Market Auditor's
  monthly clearing prices (gate D3's anchor), text-borne where a monthly report
  states one and digitised from the annual reports' *Monthly Clearing Prices*
  figure otherwise, with source, page and method per row.
* ``fuel_cost_anchor_monthly.csv`` — gate D4's fuel-cost stack from the
  committed EIA delivered-gas series.
* ``filter_ledger.json`` — the MWh and rows excluded by every rule of the
  PRECOMMIT's §2–§4, so the reader can see what the index is not made of.
* ``gate.json`` — every measured cell of the PRECOMMIT's §5 gate table.

Source (PRECOMMIT §8): the EQR Report Viewer's *Downloads → Quarterly Filings →
All Companies* bulk files,
``https://eqrreportviewer.ferc.gov/DownloadRepositoryProd/<token>/BulkNew/CSV/CSV_<year>_Q<q>.zip``
— a zip of per-filing zips, each carrying ``*_ident``, ``*_contracts``,
``*_transactions`` and ``*_indexPub`` CSVs. The token-bearing links are read
from the viewer's Downloads tab (an ASP.NET postback) at fetch time. Measured
2026-09-13: HTTP 200 anonymous, 3.3–3.9 GB per quarter, ``Accept-Ranges``,
~10 MB/s through this egress; ``www.ferc.gov`` 403, ``eqrds.ferc.gov`` CONNECT
502, ``data.ferc.gov`` carries no EQR dataset. Disk allows one quarter at a
time, so ``extract`` streams: read every filing's transactions CSV, keep the
SOCO rows, hash and delete the zip.

Usage::

    python scripts/data/build_soco_eqr_price_index.py links
    python scripts/data/build_soco_eqr_price_index.py extract [--quarter 2024_Q3 ...] [--keep-zip]
    python scripts/data/build_soco_eqr_price_index.py fetch-seem
    python scripts/data/build_soco_eqr_price_index.py build
    python scripts/data/build_soco_eqr_price_index.py gate [--land]

``gate --land`` writes ``data/raw/_validation-source/actual_lmp_hourly_SOCO.parquet``
ONLY when every gate cell passes. Raw pulls live in ``data/raw/ferc-eqr/_pulls/``
and are deliberately not committed; ``SHA256SUMS.txt`` records their identity.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import io
import json
import re
import struct
import sys
import zipfile
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
from market_sim.config import paths  # noqa: E402
from market_sim.config.constants import HEAT_RATE_BINS  # noqa: E402
from market_sim.data.fuel.electric_power import MCF_TO_MMBTU  # noqa: E402
from scripts.calibration_verdict import PRICE_MONTH_COVERAGE_MIN  # noqa: E402
from scripts.data.derive_actual_lmp import (  # noqa: E402
    _HOURS_PER_YEAR,
    _std_hour_index,
)

# --------------------------------------------------------------------------- #
# Registry — every value cited to the PRECOMMIT (rule 5 [R-NO-MAGIC]).
# --------------------------------------------------------------------------- #
VIEWER_URL = "https://eqrreportviewer.ferc.gov/"
RAW_DIR: Path = paths.RAW_DATA_DIR / "ferc-eqr"
PULL_DIR: Path = RAW_DIR / "_pulls"
LAND_PATH: Path = paths.CALIBRATION_DIR / "actual_lmp_hourly_SOCO.parquet"
DEMAND_PATH: Path = paths.EIA_HOURLY_DIR / "SOCO hourly.parquet"
GAS_DIR: Path = paths.RAW_DATA_DIR / "gas-prices"
SEEM_PLANNING_DIR: Path = paths.RAW_DATA_DIR / "soco-planning"
PRECOMMIT = "docs/handoffs/PRECOMMIT-soco-13-2026-09-13.md"

YEARS: tuple[int, ...] = (2023, 2024, 2025)
QUARTERS: tuple[str, ...] = tuple(f"{y}_Q{q}" for y in YEARS for q in (1, 2, 3, 4))

#: PRECOMMIT §4 — the model clock: Central STANDARD time, fixed all year (the
#: SOCO BA files EIA-930 on the Central clock, SOCO-10 gate G19).
STD_TZ = "Etc/GMT+6"
#: Prevailing Central time, used ONLY to locate the on-peak block (§5 D5).
PREVAILING_TZ = "America/Chicago"

#: PRECOMMIT §2 — the footprint is the delivery-point balancing authority.
POD_BA = "SOCO"
#: PRECOMMIT §2 — intra-corporate rows (seller AND customer both Southern).
SOUTHERN_FAMILY_RE = re.compile(
    r"ALABAMA POWER|GEORGIA POWER|MISSISSIPPI POWER|SOUTHERN POWER|"
    r"SOUTHERN COMPANY SERVICES|SOUTHERN ELECTRIC GENERATING",
    re.I,
)
#: PRECOMMIT §3 — the product filter, on upper-cased stripped values.
PRODUCTS = {"ENERGY"}
CLASSES = {"F", "NF"}
TERMS = {"ST"}
INCREMENTS = {"5", "15", "H", "D"}
RATE_TYPES_EXCLUDED = {"ELECTRIC INDEX", "RTO/ISO"}
RATE_UNITS = {"$/MWH", "$/KWH"}
#: PRECOMMIT §4 — time-zone codes → conversion.
TZ_MAP: dict[str, str] = {
    "CP": "America/Chicago",
    "EP": "America/New_York",
    "MP": "America/Denver",
    "CS": "Etc/GMT+6",
    "CD": "Etc/GMT+5",
    "ES": "Etc/GMT+5",
    "ED": "Etc/GMT+4",
    "PS": "Etc/GMT+8",
}
#: PRECOMMIT §4 — a row spanning more than this is a weekly/monthly aggregate.
MAX_SPAN_HOURS = 25
#: PRECOMMIT §4 — thin-hour NaN rule.
MIN_ROWS_PER_HOUR = 2
MIN_MWH_PER_HOUR = 20.0

#: PRECOMMIT §5 — the gate, as numbers.
D1_FULL_YEAR_MIN_HOURS = 8_322  # 95 % of 8,760
D1_MONTH_MIN = PRICE_MONTH_COVERAGE_MIN  # 0.90, the scorer's own month bar
D2_THIN_ROWS = 5
D2_THIN_SHARE_MAX = 0.25
D2_MIN_VOLUME_SHARE = 0.05
D3_LEVEL_TOL = 0.15
D3_MIN_CORR = 0.80
D3_MIN_MONTHS = 30
D4_MIN_CORR = 0.70
D4_RATIO_RANGE = (0.8, 2.0)
D4_CC_HEAT_RATE = HEAT_RATE_BINS["gas_cc"]["f_class"]  # 6.7 MMBtu/MWh
D5_PRICE_RANGE = (-100.0, 3000.0)
D5_MEAN_RANGE = (0.0, 250.0)
#: WSPP 6×16 on-peak block: hour-beginning 06:00–21:59 prevailing time.
PEAK_HOURS_BEGINNING = tuple(range(6, 22))

#: SEEM auditor annual weighted-average clearing prices as STATED IN TEXT by
#: the annual reports (SOCO-12 §0.2; transcriptions under soco-planning).
SEEM_ANNUAL_TEXT_URLS = {
    2023: "https://southeastenergymarket.com/wp-content/uploads/SEEM-Audit-Report-Annual-Rpt-2023FINAL.pdf",
    2024: "https://southeastenergymarket.com/wp-content/uploads/SEEM-Audit-Report-Annual-2024-F.pdf",
    2025: "https://southeastenergymarket.com/wp-content/uploads/SEEM-Audit-Report-Annual-2025-Final.pdf",
}
SEEM_AUDITOR_PAGE = "https://southeastenergymarket.com/auditor-reports/"
EQR_COLUMNS = [
    "transaction_unique_id",
    "seller_company_name",
    "customer_company_name",
    "ferc_tariff_reference",
    "contract_service_agreement",
    "transaction_unique_identifier",
    "transaction_begin_date",
    "transaction_end_date",
    "trade_date",
    "exchange_brokerage_service",
    "type_of_rate",
    "time_zone",
    "point_of_delivery_balancing_authority",
    "point_of_delivery_specific_location",
    "class_name",
    "term_name",
    "increment_name",
    "increment_peaking_name",
    "product_name",
    "transaction_quantity",
    "price",
    "rate_units",
    "standardized_quantity",
    "standardized_price",
    "total_transmission_charge",
    "total_transaction_charge",
]


def _log(msg: str) -> None:
    """Timestamped progress line on stderr."""
    print(f"[{dt.datetime.utcnow():%H:%M:%S}] {msg}", file=sys.stderr, flush=True)


def _sha256(path: Path) -> str:
    """Streaming sha256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# links — the token-bearing bulk URLs, from the viewer's Downloads tab
# --------------------------------------------------------------------------- #
def cmd_links() -> dict[str, str]:
    """``links``: resolve the quarterly bulk-zip URLs and write ``bulk_links.json``.

    The viewer is an ASP.NET WebForms page whose *Quarterly Filings* panel is
    rendered only after a postback that activates the Downloads tab, so the
    page is fetched once, its hidden form fields replayed with the outer tab
    container's ``ActiveTabIndex`` set to 1, and the ``CSV_<year>_Q<q>.zip``
    anchors parsed from the response.
    """
    import requests

    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 market-simulator SOCO-13"})
    page = s.get(VIEWER_URL, timeout=120).text
    form = {
        m.group(1): html.unescape(m.group(2))
        for m in re.finditer(
            r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', page
        )
    }
    form["__EVENTTARGET"] = "TabContainerReportViewer"
    form["__EVENTARGUMENT"] = "activeTabChanged:1"
    form["TabContainerReportViewer_ClientState"] = (
        '{"ActiveTabIndex":1,"TabEnabledState":[true,true],'
        '"TabWasLoadedOnceState":[true,false]}'
    )
    resp = s.post(VIEWER_URL, data=form, timeout=180).text
    links = {}
    for m in re.finditer(
        r'href="(https://[^"]+/BulkNew/CSV/CSV_(\d{4})_Q([1-4])\.zip)"', resp
    ):
        links[f"{m.group(2)}_Q{m.group(3)}"] = m.group(1)
    PULL_DIR.mkdir(parents=True, exist_ok=True)
    (PULL_DIR / "bulk_links.json").write_text(
        json.dumps(links, indent=1, sort_keys=True)
    )
    _log(f"{len(links)} bulk links resolved")
    return links


# --------------------------------------------------------------------------- #
# extract — stream one quarter's bulk zip, keep the SOCO rows
# --------------------------------------------------------------------------- #
def _salvage_members(raw: bytes) -> tuple[dict[str, bytes], bool]:
    """Walk the local file headers of a zip whose central directory is missing.

    One inner zip per quarter or so is truncated by the filer (2024 Q3:
    ``CSV_2024_Q3_5596771_1561913.ZIP`` — no end-of-central-directory record).
    Its local headers are intact, so each deflate stream is inflated up to
    where it ends; a member cut mid-stream yields what was recoverable and the
    salvage is flagged. Returns ``({name: bytes}, truncated)``.
    """
    out: dict[str, bytes] = {}
    pos = 0
    truncated = False
    while True:
        i = raw.find(b"PK\x03\x04", pos)
        if i < 0 or i + 30 > len(raw):
            break
        method = struct.unpack("<H", raw[i + 8 : i + 10])[0]
        csize, usize = struct.unpack("<II", raw[i + 18 : i + 26])
        nlen, elen = struct.unpack("<HH", raw[i + 26 : i + 30])
        name = raw[i + 30 : i + 30 + nlen].decode("latin1")
        start = i + 30 + nlen + elen
        if method == 8:
            d = zlib.decompressobj(-15)
            try:
                data = d.decompress(raw[start:])
            except zlib.error:
                data = b""
                truncated = True
            consumed = len(raw) - start - len(d.unused_data)
            if not d.eof:
                truncated = True
            pos = start + max(consumed, 1)
        else:
            data = raw[start : start + usize]
            pos = start + max(usize, 1)
            if len(data) < usize:
                truncated = True
        out[name] = data
    return out, truncated


def _read_transactions(csv_bytes: bytes) -> pd.DataFrame | None:
    """Parse the ``SOCO``-bearing lines of a filing's transactions CSV.

    A quarter is ~4 GB of CSV and a single ISO filing runs to gigabytes, so
    the header plus only the lines containing the literal ``SOCO`` are handed
    to pandas (all columns as text); the exact POD-column test then follows.
    A quoted field carrying an embedded newline would split a row across two
    lines and misalign it — such rows are skipped by ``on_bad_lines`` and
    counted by the caller through the row-count difference.
    """
    try:
        lines = csv_bytes.splitlines(keepends=True)
        if not lines:
            return None
        picked = [ln for ln in lines[1:] if b"SOCO" in ln]
        if not picked:
            return None
        return pd.read_csv(
            io.BytesIO(lines[0] + b"".join(picked)),
            dtype=str,
            keep_default_na=False,
            encoding_errors="replace",
            on_bad_lines="skip",
        )
    except Exception as exc:  # noqa: BLE001 — a defective filing is logged, never fatal
        _log(f"READ-FAIL {exc!r}")
        return None


def extract_quarter(zip_path: Path, quarter: str) -> dict:
    """Stream one bulk quarter; write ``_pulls/soco_pod_<quarter>.parquet``.

    Every filing's transactions CSV is scanned as bytes for the literal
    ``SOCO`` first (the POD code is upper-case in the file); only filings that
    contain it are parsed, and the exact column filter is then applied. Row
    totals of every filing are counted from the bytes so the manifest carries
    the quarter's whole-file row count.
    """
    outer = zipfile.ZipFile(zip_path)
    names = outer.namelist()
    frames: list[pd.DataFrame] = []
    n_rows_total = 0
    n_filings = 0
    n_with_tx = 0
    bad: list[dict] = []
    for i, n in enumerate(names):
        raw = outer.read(n)
        members: dict[str, bytes]
        salvaged = False
        try:
            inner = zipfile.ZipFile(io.BytesIO(raw))
            members = {m: None for m in inner.namelist()}  # lazy
            getter = inner.read
        except zipfile.BadZipFile:
            members, truncated = _salvage_members(raw)
            getter = members.__getitem__
            salvaged = True
            bad.append(
                {
                    "member": n,
                    "bytes": len(raw),
                    "truncated": truncated,
                    "salvaged_members": sorted(members),
                }
            )
        n_filings += 1
        tx = [m for m in members if m.lower().endswith("_transactions.csv")]
        if not tx:
            continue
        n_with_tx += 1
        csv_bytes = getter(tx[0])
        n_rows_total += max(csv_bytes.count(b"\n") - 1, 0)
        if b"SOCO" not in csv_bytes:
            continue
        df = _read_transactions(csv_bytes)
        if df is None:
            continue
        missing = [c for c in EQR_COLUMNS if c not in df.columns]
        if missing:
            _log(f"{n}: missing columns {missing} — skipped")
            bad.append({"member": n, "missing_columns": missing})
            continue
        pod = df["point_of_delivery_balancing_authority"].str.strip().str.upper()
        keep = df.loc[pod == POD_BA, EQR_COLUMNS].copy()
        if len(keep):
            keep["filing_member"] = n
            keep["quarter"] = quarter
            keep["salvaged"] = salvaged
            frames.append(keep)
        if i % 500 == 0:
            _log(
                f"{quarter}: {i}/{len(names)} filings, {n_rows_total:,} rows, "
                f"{sum(len(f) for f in frames):,} SOCO rows"
            )
    soco = (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame(
            columns=EQR_COLUMNS + ["filing_member", "quarter", "salvaged"]
        )
    )
    out = PULL_DIR / f"soco_pod_{quarter}.parquet"
    soco.to_parquet(out, index=False)
    manifest = {
        "quarter": quarter,
        "zip": zip_path.name,
        "zip_bytes": zip_path.stat().st_size,
        "zip_sha256": _sha256(zip_path),
        "n_filings": n_filings,
        "n_filings_with_transactions": n_with_tx,
        "n_rows_total": int(n_rows_total),
        "n_rows_soco_pod": int(len(soco)),
        "bad_inner_zips": bad,
        "extracted_utc": dt.datetime.utcnow().isoformat(timespec="seconds"),
    }
    (PULL_DIR / f"manifest_{quarter}.json").write_text(json.dumps(manifest, indent=1))
    _log(
        f"{quarter}: {len(soco):,} SOCO rows of {n_rows_total:,}; {len(bad)} defective inner zips"
    )
    return manifest


def cmd_extract(quarters: list[str] | None, keep_zip: bool, wait: bool) -> None:
    """``extract``: stream each quarter's zip present in ``_pulls`` (or wait for it)."""
    import time

    PULL_DIR.mkdir(parents=True, exist_ok=True)
    todo = list(quarters) if quarters else list(QUARTERS)
    for q in todo:
        if (PULL_DIR / f"manifest_{q}.json").exists():
            _log(f"{q}: already extracted")
            continue
        zp = PULL_DIR / f"CSV_{q}.zip"
        while not zp.exists():
            if not wait:
                raise SystemExit(
                    f"{zp} not present (run the download loop, or pass --wait)"
                )
            time.sleep(30)
        extract_quarter(zp, q)
        if not keep_zip:
            zp.unlink()
            (PULL_DIR / f"done_{q}").write_text("extracted\n")
            _log(f"{q}: zip deleted")


# --------------------------------------------------------------------------- #
# fetch-seem — the D3 anchor: text-borne monthly prices + digitised figure
# --------------------------------------------------------------------------- #
MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def _pdf_text_pages(path: Path) -> list[str]:
    """Text of every page (pdfminer.six; a local import, only this stage needs it)."""
    from pdfminer.high_level import extract_text

    return extract_text(str(path)).split("\x0c")


def _monthly_text_prices(pdf_paths: list[Path]) -> list[dict]:
    """The 'average clearing price … was $X/MWh' sentence of each monthly report."""
    rows = []
    for p in pdf_paths:
        m = re.search(r"Report-(20\d\d)_(\d{1,2})", p.name)
        if not m:
            continue
        year, month = int(m.group(1)), int(m.group(2))
        for pno, page in enumerate(_pdf_text_pages(p), 1):
            flat = " ".join(page.split())
            hit = re.search(
                r"average clearing price(?: in \w+)? was \$(\d+(?:\.\d+)?)\s*/\s*(\w+)",
                flat,
                re.I,
            )
            if hit:
                rows.append(
                    {
                        "year": year,
                        "month": month,
                        "block": "all",
                        "price_usd_mwh": float(hit.group(1)),
                        "unit_as_printed": hit.group(2),
                        "method": "text",
                        "source": p.name,
                        "page": pno,
                        "sentence": flat[max(0, hit.start() - 60) : hit.end() + 20],
                    }
                )
                break
    return rows


def _bars_in_raster(a: np.ndarray) -> list[tuple[float, int, int]]:
    """Locate the bars of a chart raster: ``(x_centre_px, top_row, bottom_row)`` each.

    Bar pixels are the blue fill (blue exceeds red by 25 levels and is above
    120): that admits the 2024 light-blue bevelled bars and the 2025 solid
    blue, and rejects the gridlines (grey), the gas-price line (green), the
    whiskers, axes and text (black) and the transparent background. Contiguous
    bar columns are one bar; runs narrower than 4 px are ignored; and a run
    whose bottom is not on the common baseline (the modal bottom row, ±5 px)
    is a legend swatch, not a bar.
    """
    r, b = a[..., 0], a[..., 2]
    blue = (b > r + 25) & (b > 120)
    col_has = blue.sum(axis=0) > 3
    runs = []
    x = 0
    w = len(col_has)
    while x < w:
        if not col_has[x]:
            x += 1
            continue
        x1 = x
        while x1 < w and col_has[x1]:
            x1 += 1
        if x1 - x >= 4:
            band = blue[:, x + 1 : x1 - 1]
            lit_rows = np.where(band.any(axis=1))[0]
            if not len(lit_rows):
                x = x1
                continue
            bottom = int(lit_rows.max())
            # the bar's own columns are those lit at its foot; a legend swatch
            # sharing the run is wider and higher and must not set the top
            foot = band[max(bottom - 3, 0) : bottom + 1].any(axis=0)
            band = band[:, foot] if foot.any() else band
            filled = band.mean(axis=1) >= 0.5
            rows = np.where(filled)[0]
            if len(rows):
                bottom = int(rows.max())
                # the bar is the filled run that ends at the bottom; a legend
                # swatch higher up the same column is separated by a gap
                top = bottom
                gap = 0
                while top > 0:
                    if filled[top - 1]:
                        gap = 0
                    else:
                        gap += 1
                        if (
                            gap >= 15
                        ):  # a bevel/highlight band is a few px; a legend swatch sits far above
                            top += gap - 1
                            break
                    top -= 1
                runs.append(((x + x1 - 1) / 2.0, int(top), bottom))
        x = x1
    if not runs:
        return []
    bottoms = np.array([r_[2] for r_ in runs])
    vals, counts = np.unique(bottoms, return_counts=True)
    base = vals[np.argmax(counts)]
    return [r_ for r_ in runs if abs(r_[2] - base) <= 5]


def _digitise_monthly_figure(pdf_path: Path, report_year: int) -> list[dict]:
    """Digitise the annual report's *Monthly Clearing Prices* figure.

    Two figure constructions exist. **2024 and 2025**: the bars are a raster
    placed over a vector axis — gridlines at the left-axis ticks (``$0``,
    ``$10``, … in the text layer, $10 apart), two category boxes (Peak,
    Off-Peak) and a whisker line (daily min/max) per month. The price of a bar
    is its height in points divided by the gridline spacing, times the tick
    step; the whisker nearest each bar gives the daily min/max as a check.
    **2023**: the whole figure is one raster with no text layer. Its gridlines
    are detected as the light rows spanning the plot, its bars as the blue
    columns, and the tick step is $10 per gridline as the figure's own axis
    labels read ($0–$70; they live in the image's alpha mask, not the text
    layer, and were verified by eye). Its categories are Jan 2023 – Apr 2024
    with no ``Avg.`` bar. The basis is recorded on every row (``scale_basis``).
    Resolution ≈ $0.2–0.3/MWh per pixel; every row records it.
    """
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTImage, LTLine, LTTextLineHorizontal
    from PIL import Image

    def walk(obj):
        yield obj
        if hasattr(obj, "_objs"):
            for o in obj._objs:
                yield from walk(o)

    for pno, page in enumerate(extract_pages(str(pdf_path)), 1):
        objs = list(walk(page))
        texts = [
            (o.get_text().strip(), o)
            for o in objs
            if isinstance(o, LTTextLineHorizontal)
        ]
        if not any("Monthly Clearing Prices" in t for t, _ in texts):
            continue
        img = max(
            (o for o in objs if isinstance(o, LTImage)),
            key=lambda o: o.srcsize[0] * o.srcsize[1],
        )
        w, h = img.srcsize
        try:
            im = Image.open(io.BytesIO(img.stream.get_rawdata()))
        except Exception:  # noqa: BLE001 — Flate-encoded samples: rebuild from raw
            im = Image.frombytes("RGB", (w, h), img.stream.get_data())
        a = np.asarray(im.convert("RGB")).astype(int)
        pt_per_px_y = (img.y1 - img.y0) / h
        lines = [o for o in objs if isinstance(o, LTLine)]
        grid_pt = sorted(
            {
                round(o.y0, 1)
                for o in lines
                if abs(o.y1 - o.y0) < 0.5
                and (o.x1 - o.x0) > 0.8 * (img.x1 - img.x0)
                and abs(o.x0 - img.x0) < 6.0  # the plot's own gridlines, not page rules
            }
        )
        vector_axis = len(grid_pt) >= 3
        tick_vals = sorted(
            {
                float(t[1:].replace(",", ""))
                for t, o in texts
                if re.fullmatch(r"\$\d+", t) and o.x1 < img.x0 + 5
            }
        )
        dollars_per_step = (
            float(np.median(np.diff(tick_vals))) if len(tick_vals) > 1 else 10.0
        )
        if vector_axis:
            step_px = float(np.median(np.diff(grid_pt))) / pt_per_px_y
            scale_basis = (
                f"vector gridlines {len(grid_pt)} at {np.median(np.diff(grid_pt)):.2f} pt; "
                f"tick step ${dollars_per_step:g} from the text layer"
            )
        else:
            # raster gridlines: light rows spanning most of the plot width
            grey = (a.min(axis=2) > 60) & (np.ptp(a, axis=2) < 25)
            row_share = grey.mean(axis=1)
            rows = np.where(row_share > 0.5)[0]
            # collapse adjacent rows
            grid_rows = []
            for r in rows:
                if not grid_rows or r - grid_rows[-1][-1] > 2:
                    grid_rows.append([r])
                else:
                    grid_rows[-1].append(r)
            grid_c = [float(np.mean(g)) for g in grid_rows]
            step_px = float(np.median(np.diff(grid_c)))
            scale_basis = (
                f"raster gridlines {len(grid_c)} at {step_px:.1f} px; tick step $10 as "
                "labelled on the figure ($0-$70 left axis, read from the image's alpha "
                "mask and verified by eye - FINDING)"
            )
        bars = _bars_in_raster(a)
        if len(bars) % 2:
            _log(
                f"{pdf_path.name}: {len(bars)} bars found (odd) — cannot split into Peak / Off-Peak"
            )
            return []
        half = len(bars) // 2
        groups = [bars[:half], bars[half:]]
        # categories per group: Avg. + 12 months of the report year (13), or
        # Avg. + the prior December + 12 months (14, the 2025 construction).
        if half == 13:
            cats = [(report_year, 0)] + [(report_year, m) for m in range(1, 13)]
        elif half == 14:
            cats = [(report_year, 0), (report_year - 1, 12)] + [
                (report_year, m) for m in range(1, 13)
            ]
        elif half == 16:
            # the 2023 construction: no Avg. bar; Jan-Dec of the report year, then Jan-Apr of the next
            cats = [(report_year, m) for m in range(1, 13)] + [
                (report_year + 1, m) for m in range(1, 5)
            ]
        else:
            _log(f"{pdf_path.name}: {half} bars per group — no category rule")
            return []
        whisk = [
            (o.x0, o.y0, o.y1)
            for o in lines
            if abs(o.x1 - o.x0) < 0.5
            and o.y0 > img.y0 - 1
            and img.x0 < o.x0 < img.x1
            and (o.y1 - o.y0) > 2
        ]
        px_per_pt_x = w / (img.x1 - img.x0)
        out = []
        for gi, gbars in enumerate(groups):
            gname = ("Peak", "Off-Peak")[gi]
            for (cx, top, bot), (yy, mm) in zip(gbars, cats):
                height_px = bot - top + 1
                price = height_px / step_px * dollars_per_step
                lo = hi = None
                if vector_axis:
                    cx_pt = img.x0 + cx / px_per_pt_x
                    near = [(y0, y1) for x, y0, y1 in whisk if abs(x - cx_pt) < 4.0]
                    if near:
                        base_pt = grid_pt[0]
                        step_pt = np.median(np.diff(grid_pt))
                        lo = round(
                            (near[0][0] - base_pt) / step_pt * dollars_per_step, 2
                        )
                        hi = round(
                            (near[0][1] - base_pt) / step_pt * dollars_per_step, 2
                        )
                out.append(
                    {
                        "year": yy,
                        "month": mm,
                        "block": gname,
                        "price_usd_mwh": round(float(price), 2),
                        "daily_min_usd_mwh": lo,
                        "daily_max_usd_mwh": hi,
                        "method": "digitised",
                        "source": pdf_path.name,
                        "page": pno,
                        "resolution_usd_mwh": round(dollars_per_step / step_px, 3),
                        "scale_basis": scale_basis,
                        "bar_px": [round(cx, 1), top, bot],
                    }
                )
        return out
    return []


def cmd_fetch_seem() -> None:
    """``fetch-seem``: build ``seem_auditor_monthly_prices.csv`` from the auditor's PDFs."""
    import requests

    PULL_DIR.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 market-simulator SOCO-13"})
    page = s.get(SEEM_AUDITOR_PAGE, timeout=120).text
    links = sorted(
        set(
            re.findall(
                r'href="(https://southeastenergymarket\.com/wp-content/uploads/'
                r'SEEM-Audit-Report-(?:2023|2024|2025)_\d+[^"]*\.pdf)"',
                page,
            )
        )
    )
    monthly_paths = []
    for u in links:
        dst = PULL_DIR / u.rsplit("/", 1)[-1]
        if not dst.exists():
            dst.write_bytes(s.get(u, timeout=120).content)
        monthly_paths.append(dst)
    annual_paths = {}
    for y, u in SEEM_ANNUAL_TEXT_URLS.items():
        dst = PULL_DIR / u.rsplit("/", 1)[-1]
        if not dst.exists():
            local = SEEM_PLANNING_DIR / "SEEM_Auditor_Annual_Report_2025.pdf"
            if y == 2025 and local.exists():
                dst.write_bytes(local.read_bytes())
            else:
                dst.write_bytes(s.get(u, timeout=120).content)
        annual_paths[y] = dst
    text_rows = _monthly_text_prices(monthly_paths)
    _log(f"{len(text_rows)} text-borne monthly prices")
    fig_rows = []
    for y, p in annual_paths.items():
        r = _digitise_monthly_figure(p, y)
        _log(f"annual {y}: {len(r)} digitised bars")
        fig_rows += r
    # annual weighted-average sentences
    annual_rows = []
    for y, p in annual_paths.items():
        for pno, pg in enumerate(_pdf_text_pages(p), 1):
            flat = " ".join(pg.split())
            m = re.search(r"average price was about \$(\d+)/MWh for all segments", flat)
            if m:
                annual_rows.append(
                    {
                        "year": y,
                        "price_usd_mwh": float(m.group(1)),
                        "source": p.name,
                        "page": pno,
                    }
                )
                break
    pd.DataFrame(text_rows).to_csv(PULL_DIR / "seem_monthly_text.csv", index=False)
    pd.DataFrame(fig_rows).to_csv(
        PULL_DIR / "seem_annual_figure_digitised.csv", index=False
    )
    pd.DataFrame(annual_rows).to_csv(PULL_DIR / "seem_annual_text.csv", index=False)
    _log(f"annual text values: {annual_rows}")


# --------------------------------------------------------------------------- #
# build — filters, allocation, the hourly index, the anchors
# --------------------------------------------------------------------------- #
def _to_utc(stamp: pd.Series, tz: pd.Series) -> pd.Series:
    """``YYYYMMDDHHMM`` wall-clock in the row's EQR time-zone code → UTC instants."""
    out = pd.Series(pd.NaT, index=stamp.index, dtype="datetime64[ns, UTC]")
    naive = pd.to_datetime(stamp, format="%Y%m%d%H%M", errors="coerce")
    for code, zone in TZ_MAP.items():
        m = (tz == code) & naive.notna()
        if not m.any():
            continue
        loc = naive[m].dt.tz_localize(
            zone,
            ambiguous=np.ones(int(m.sum()), dtype=bool),
            nonexistent="shift_forward",
        )
        out[m] = loc.dt.tz_convert("UTC")
    return out


def _apply_filters(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """PRECOMMIT §2–§4 row filters, with an exclusion ledger (rows and MWh)."""
    df = raw.copy()
    up = lambda c: df[c].astype(str).str.strip().str.upper()  # noqa: E731
    df["_q"] = pd.to_numeric(df["standardized_quantity"], errors="coerce")
    df["_p"] = pd.to_numeric(df["standardized_price"], errors="coerce")
    ledger: dict[str, dict] = {
        "start": {
            "rows": int(len(df)),
            "mwh": float(df["_q"].clip(lower=0).sum(skipna=True)),
        }
    }

    def step(name: str, keep: pd.Series) -> None:
        nonlocal df
        dropped = df[~keep]
        ledger[name] = {
            "rows_excluded": int(len(dropped)),
            "mwh_excluded": float(dropped["_q"].clip(lower=0).sum(skipna=True)),
            "rows_kept": int(keep.sum()),
        }
        df = df[keep]

    step(
        "standardized_fields_numeric_positive",
        df["_q"].notna() & df["_p"].notna() & (df["_q"] > 0),
    )
    step("product_ENERGY", up("product_name").isin(PRODUCTS))
    step("class_F_NF", up("class_name").isin(CLASSES))
    step("term_ST", up("term_name").isin(TERMS))
    step("increment_5_15_H_D", up("increment_name").isin(INCREMENTS))
    step("rate_type_not_index_not_rto", ~up("type_of_rate").isin(RATE_TYPES_EXCLUDED))
    step("rate_units_energy", up("rate_units").isin(RATE_UNITS))
    both_southern = df["seller_company_name"].str.contains(SOUTHERN_FAMILY_RE) & df[
        "customer_company_name"
    ].str.contains(SOUTHERN_FAMILY_RE)
    step("intra_southern_family", ~both_southern)
    step("time_zone_code_known", up("time_zone").isin(TZ_MAP))
    before = len(df)
    df = df.drop_duplicates(subset=EQR_COLUMNS)
    ledger["exact_duplicates_collapsed"] = {"rows": int(before - len(df))}
    df["begin_utc"] = _to_utc(df["transaction_begin_date"], up("time_zone"))
    df["end_utc"] = _to_utc(df["transaction_end_date"], up("time_zone"))
    step("datetimes_parse", df["begin_utc"].notna() & df["end_utc"].notna())
    # end adjustment (PRECOMMIT §4): :59/:14/:29/:44 → +1 min; end == begin → +1 h
    end_min = df["end_utc"].dt.minute
    df.loc[end_min.isin([59, 14, 29, 44]), "end_utc"] += pd.Timedelta(minutes=1)
    df.loc[df["end_utc"] <= df["begin_utc"], "end_utc"] = df[
        "begin_utc"
    ] + pd.Timedelta(hours=1)
    span_h = (df["end_utc"] - df["begin_utc"]).dt.total_seconds() / 3600.0
    df["span_h"] = span_h
    step("span_le_25h", span_h <= MAX_SPAN_HOURS)
    ledger["end"] = {"rows": int(len(df)), "mwh": float(df["_q"].sum())}
    return df, ledger


def _allocate_hours(df: pd.DataFrame) -> pd.DataFrame:
    """Expand each row into its clock hours, MWh split uniformly (PRECOMMIT §4)."""
    begin_h = df["begin_utc"].dt.floor("h").dt.tz_convert("UTC").dt.tz_localize(None)
    end_ceiled = df["end_utc"].dt.ceil("h").dt.tz_convert("UTC").dt.tz_localize(None)
    n = (
        ((end_ceiled - begin_h).dt.total_seconds() / 3600.0)
        .round()
        .astype(int)
        .clip(lower=1)
    )
    idx = np.repeat(np.arange(len(df)), n.to_numpy())
    offsets = np.concatenate([np.arange(k) for k in n.to_numpy()])
    out = pd.DataFrame(
        {
            "hour_utc": begin_h.to_numpy("datetime64[ns]")[idx]
            + offsets.astype("timedelta64[h]"),
            "price": df["_p"].to_numpy()[idx],
            "mwh": df["_q"].to_numpy()[idx] / n.to_numpy()[idx],
            "seller": df["seller_company_name"].to_numpy()[idx],
            "increment": df["increment_name"].str.strip().to_numpy()[idx],
            "rate_type": df["type_of_rate"].str.strip().str.upper().to_numpy()[idx],
        }
    )
    out["hour_utc"] = pd.to_datetime(out["hour_utc"], utc=True)
    return out


def _hourly_index(alloc: pd.DataFrame) -> pd.DataFrame:
    """Volume-weighted price per UTC hour with the thin-hour NaN rule."""
    alloc = alloc.assign(
        pq=alloc["price"] * alloc["mwh"], is15=(alloc["increment"] == "15")
    )
    g = alloc.groupby("hour_utc")
    out = pd.DataFrame(
        {
            "mwh": g["mwh"].sum(),
            "pq": g["pq"].sum(),
            "n_rows": g.size(),
            "n_sellers": g["seller"].nunique(),
            "mwh_15min": alloc[alloc["is15"]].groupby("hour_utc")["mwh"].sum(),
        }
    )
    out["mwh_15min"] = out["mwh_15min"].fillna(0.0)
    out["price"] = out["pq"] / out["mwh"]
    thin = (out["n_rows"] < MIN_ROWS_PER_HOUR) | (out["mwh"] < MIN_MWH_PER_HOUR)
    out.loc[thin, "price"] = np.nan
    out["thin"] = thin
    full = pd.date_range(
        f"{YEARS[0]}-01-01",
        f"{YEARS[-1] + 1}-01-01T06:00",
        freq="h",
        tz="UTC",
        inclusive="left",
    )
    out = out.reindex(full)
    out.index.name = "hour_utc"
    return out.reset_index().drop(columns=["pq"])


def _fuel_cost_anchor() -> pd.DataFrame:
    """D4: F-class CC fuel cost from the committed EIA delivered-gas series."""
    frames = []
    for st in ("AL", "GA", "MS"):
        p = GAS_DIR / f"eia_delivered_gas_{st}_monthly_2023-2025.csv"
        g = pd.read_csv(p)
        g["state"] = st
        g["usd_per_mmbtu"] = g["value"] / MCF_TO_MMBTU
        g["cc_fuel_cost_usd_mwh"] = g["usd_per_mmbtu"] * D4_CC_HEAT_RATE
        frames.append(
            g[["period", "state", "value", "usd_per_mmbtu", "cc_fuel_cost_usd_mwh"]]
        )
    out = pd.concat(frames, ignore_index=True).rename(columns={"value": "usd_per_mcf"})
    out["heat_rate_mmbtu_mwh"] = D4_CC_HEAT_RATE
    out["mcf_to_mmbtu"] = MCF_TO_MMBTU
    return out


def cmd_build() -> None:
    """``build``: raw extract → filters → hourly index → anchors → committed store."""
    parts = []
    for q in QUARTERS:
        p = PULL_DIR / f"soco_pod_{q}.parquet"
        if not p.exists():
            raise SystemExit(f"missing {p}: extract every quarter first")
        parts.append(pd.read_parquet(p))
    raw = pd.concat(parts, ignore_index=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw.to_parquet(RAW_DIR / "eqr_soco_pod_transactions.parquet", index=False)
    _log(f"raw extract: {len(raw):,} SOCO-POD rows")
    df, ledger = _apply_filters(raw)
    alloc = _allocate_hours(df)
    hourly = _hourly_index(alloc)
    hourly.to_parquet(RAW_DIR / "soco_eqr_hourly_utc.parquet", index=False)
    alloc.to_parquet(PULL_DIR / "allocated_rows.parquet", index=False)
    # seller concentration on indexed MWh
    by_seller = alloc.groupby("seller")["mwh"].sum().sort_values(ascending=False)
    share = by_seller / by_seller.sum()
    ledger["seller_concentration"] = {
        "top5_share": float(share.head(5).sum()),
        "hhi": float((share**2).sum() * 10_000),
        "top10": {k: round(float(v), 4) for k, v in share.head(10).items()},
    }
    ledger["by_rate_type_mwh_share"] = {
        k: round(float(v), 4)
        for k, v in (
            alloc.groupby("rate_type")["mwh"].sum() / alloc["mwh"].sum()
        ).items()
    }
    ledger["by_increment_mwh_share"] = {
        k: round(float(v), 4)
        for k, v in (
            alloc.groupby("increment")["mwh"].sum() / alloc["mwh"].sum()
        ).items()
    }
    (RAW_DIR / "filter_ledger.json").write_text(
        json.dumps(ledger, indent=1, default=str)
    )
    _fuel_cost_anchor().to_csv(RAW_DIR / "fuel_cost_anchor_monthly.csv", index=False)
    # the SEEM anchor table
    seem_parts = []
    for name in ("seem_monthly_text.csv", "seem_annual_figure_digitised.csv"):
        p = PULL_DIR / name
        if p.exists() and p.stat().st_size > 0:
            seem_parts.append(pd.read_csv(p))
    if seem_parts:
        pd.concat(seem_parts, ignore_index=True).to_csv(
            RAW_DIR / "seem_auditor_monthly_prices.csv", index=False
        )
    _log(
        f"hourly index: {int(hourly['price'].notna().sum()):,} priced hours of {len(hourly):,}"
    )


# --------------------------------------------------------------------------- #
# gate — PRECOMMIT §5, scored as written
# --------------------------------------------------------------------------- #
def _load_demand_hourly() -> pd.DataFrame:
    """SOCO EIA-930 demand per UTC hour (the series the model dispatches)."""
    d = pd.read_parquet(DEMAND_PATH, columns=["UTC time", "Demand"])
    d["hour_utc"] = pd.to_datetime(d["UTC time"], utc=True)
    return d[["hour_utc", "Demand"]]


def _std_year(hour_utc: pd.Series) -> pd.Series:
    """Fixed-CST calendar year of each UTC hour."""
    return hour_utc.dt.tz_convert(STD_TZ).dt.year


def _weighted_mean(price: pd.Series, mwh: pd.Series) -> float:
    m = price.notna() & mwh.notna()
    if not m.any() or float(mwh[m].sum()) <= 0:
        return float("nan")
    return float((price[m] * mwh[m]).sum() / mwh[m].sum())


def gate_d1(hourly: pd.DataFrame) -> dict:
    """D1: annual ≥ 8,322 priced hours; every month ≥ PRICE_MONTH_COVERAGE_MIN."""
    h = hourly.copy()
    std = h["hour_utc"].dt.tz_convert(STD_TZ)
    h["year"], h["month"] = std.dt.year, std.dt.month
    h = h[h["year"].isin(YEARS)]
    ok = h["price"].notna()
    annual = {int(y): int(ok[h["year"] == y].sum()) for y in YEARS}
    monthly = ok.groupby([h["year"], h["month"]]).mean().rename("cov").reset_index()
    monthly["pass"] = monthly["cov"] >= D1_MONTH_MIN
    diurnal_nan = (~ok).groupby(std.dt.hour[h.index]).mean()
    return {
        "annual_priced_hours": annual,
        "annual_bar": D1_FULL_YEAR_MIN_HOURS,
        "monthly_coverage": monthly.to_dict("records"),
        "monthly_bar": D1_MONTH_MIN,
        "nan_share_by_std_hour": {
            int(k): round(float(v), 4) for k, v in diurnal_nan.items()
        },
        "pass_annual": all(v >= D1_FULL_YEAR_MIN_HOURS for v in annual.values()),
        "pass_monthly": bool(monthly["pass"].all()) and len(monthly) == 36,
        "pass": all(v >= D1_FULL_YEAR_MIN_HOURS for v in annual.values())
        and bool(monthly["pass"].all())
        and len(monthly) == 36,
    }


def gate_d2(hourly: pd.DataFrame, demand: pd.DataFrame) -> dict:
    """D2: thin-hour share ≤ 25 %; indexed MWh ≥ 5 % of SOCO demand, each year."""
    h = hourly.copy()
    h["year"] = _std_year(h["hour_utc"])
    dm = demand.copy()
    dm["year"] = _std_year(dm["hour_utc"])
    out = {
        "years": {},
        "thin_rows_bar": D2_THIN_ROWS,
        "thin_share_max": D2_THIN_SHARE_MAX,
        "volume_share_min": D2_MIN_VOLUME_SHARE,
    }
    ok_all = True
    for y in YEARS:
        hy = h[(h["year"] == y) & h["price"].notna()]
        thin_share = (
            float((hy["n_rows"] < D2_THIN_ROWS).mean()) if len(hy) else float("nan")
        )
        indexed_mwh = float(h.loc[h["year"] == y, "mwh"].fillna(0).sum())
        demand_mwh = float(dm.loc[dm["year"] == y, "Demand"].sum())
        share = indexed_mwh / demand_mwh if demand_mwh else float("nan")
        p = (thin_share <= D2_THIN_SHARE_MAX) and (share >= D2_MIN_VOLUME_SHARE)
        ok_all &= bool(p)
        out["years"][int(y)] = {
            "thin_share": round(thin_share, 4),
            "indexed_mwh": round(indexed_mwh, 1),
            "demand_mwh": round(demand_mwh, 1),
            "volume_share": round(share, 5),
            "median_rows_per_priced_hour": float(hy["n_rows"].median())
            if len(hy)
            else None,
            "pass": bool(p),
        }
    out["pass"] = bool(ok_all)
    return out


def _monthly_index(hourly: pd.DataFrame, block: str | None = None) -> pd.DataFrame:
    """MWh-weighted monthly mean of the hourly index (UTC month), optionally by peak block."""
    h = hourly.copy()
    prev = h["hour_utc"].dt.tz_convert(PREVAILING_TZ)
    if block == "Peak":
        h = h[prev.dt.hour.isin(PEAK_HOURS_BEGINNING)]
    elif block == "Off-Peak":
        h = h[~prev.dt.hour.isin(PEAK_HOURS_BEGINNING)]
    h = h[h["price"].notna()]
    h["ym"] = h["hour_utc"].dt.strftime("%Y-%m")
    g = h.groupby("ym")
    return pd.DataFrame(
        {
            "I": g.apply(lambda s: _weighted_mean(s["price"], s["mwh"])),
            "mwh": g["mwh"].sum(),
        }
    )


def _corr(a: pd.Series, b: pd.Series) -> float:
    j = pd.concat([a, b], axis=1).dropna()
    return float(j.iloc[:, 0].corr(j.iloc[:, 1])) if len(j) > 2 else float("nan")


def gate_d3(
    hourly: pd.DataFrame, seem: pd.DataFrame | None, seem_annual: pd.DataFrame | None
) -> dict:
    """D3: level within 15 % of the auditor's annual price; monthly r ≥ 0.80; ≥ 30 months."""
    h = hourly.copy()
    h["year"] = _std_year(h["hour_utc"])
    out = {
        "level_tol": D3_LEVEL_TOL,
        "min_corr": D3_MIN_CORR,
        "min_months": D3_MIN_MONTHS,
        "years": {},
    }
    annual_pass = True
    for y in YEARS:
        hy = h[h["year"] == y]
        I_y = _weighted_mean(hy["price"], hy["mwh"])
        S_y = None
        if seem_annual is not None and (seem_annual["year"] == y).any():
            S_y = float(
                seem_annual.loc[seem_annual["year"] == y, "price_usd_mwh"].iloc[0]
            )
        gap = (I_y - S_y) / S_y if S_y else None
        p = gap is not None and abs(gap) <= D3_LEVEL_TOL
        annual_pass &= bool(p)
        out["years"][int(y)] = {
            "I_year": round(I_y, 3),
            "S_year": S_y,
            "gap": None if gap is None else round(gap, 4),
            "pass_level": bool(p),
        }
    # monthly shape — text-borne (all-hours) rows, and digitised peak/off-peak rows
    mi_all = _monthly_index(hourly)
    shape = {}
    if seem is not None and len(seem):
        text = seem[seem["method"] == "text"].copy()
        if len(text):
            text["ym"] = text.apply(
                lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1
            )
            # November 2025 was published three times (-Rev-RL, -Rev, base), all
            # stating the same value; keep the latest revision (sorts first)
            text = text.sort_values("source").drop_duplicates("ym", keep="first")
            j = text.set_index("ym")["price_usd_mwh"]
            shape["text_all_hours"] = {
                "n_months": int(j.index.isin(mi_all.index).sum()),
                "corr": _corr(mi_all["I"], j),
                "pairs": {
                    k: [round(float(mi_all["I"].get(k, np.nan)), 2), float(v)]
                    for k, v in j.items()
                },
            }
        dig = seem[seem["method"] == "digitised"].copy()
        if len(dig):
            dig = dig[dig["month"].astype(int) > 0]  # drop the Avg. bars
            dig["ym"] = dig.apply(
                lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1
            )
            # the figures overlap (2023's carries Jan-Apr 2024; 2025's carries
            # Dec 2024): keep the report of the month's own year, and record
            # the cross-report agreement on the overlap as a digitisation check
            dig["own_report"] = [
                str(y) in src for y, src in zip(dig["year"].astype(int), dig["source"])
            ]
            dup = dig[dig.duplicated(["ym", "block"], keep=False)].sort_values(
                ["ym", "block", "source"]
            )
            shape["cross_report_overlap"] = [
                {
                    "ym": r["ym"],
                    "block": r["block"],
                    "source": r["source"],
                    "price": r["price_usd_mwh"],
                }
                for _, r in dup.iterrows()
            ]
            dig = dig.sort_values(
                ["ym", "block", "own_report"], ascending=[True, True, False]
            ).drop_duplicates(["ym", "block"], keep="first")
            frames = []
            for blk in ("Peak", "Off-Peak"):
                mi_b = _monthly_index(hourly, blk)
                jb = dig[dig["block"] == blk].set_index("ym")["price_usd_mwh"]
                shape[f"digitised_{blk}"] = {
                    "n_months": int(jb.index.isin(mi_b.index).sum()),
                    "corr": _corr(mi_b["I"], jb),
                    "pairs": {
                        k: [round(float(mi_b["I"].get(k, np.nan)), 2), float(v)]
                        for k, v in jb.items()
                    },
                }
                frames.append(pd.DataFrame({"I": mi_b["I"], "S": jb}))
            both = pd.concat(frames).dropna()
            shape["digitised_pooled"] = {
                "n_points": int(len(both)),
                "corr": _corr(both["I"], both["S"]),
            }
            # the text-borne 2025 months against the digitised bars: a check on the digitisation
            if "text_all_hours" in shape:
                pk = dig[dig["block"] == "Peak"].set_index("ym")["price_usd_mwh"]
                op = dig[dig["block"] == "Off-Peak"].set_index("ym")["price_usd_mwh"]
                shape["digitised_vs_text_2025"] = {
                    k: {
                        "text": v,
                        "peak": float(pk.get(k, np.nan)),
                        "offpeak": float(op.get(k, np.nan)),
                    }
                    for k, v in shape["text_all_hours"]["pairs"].items()
                    for v in [v[1]]
                }
    out["shape"] = shape
    n_text = shape.get("text_all_hours", {}).get("n_months", 0)
    n_dig = shape.get("digitised_Peak", {}).get("n_months", 0)
    corr_text = shape.get("text_all_hours", {}).get("corr", float("nan"))
    corr_dig = shape.get("digitised_pooled", {}).get("corr", float("nan"))
    out["support_text_months"] = n_text
    out["support_digitised_months"] = n_dig
    out["pass_support_as_precommitted_text_only"] = n_text >= D3_MIN_MONTHS
    out["pass_support_with_digitised"] = max(n_text, n_dig) >= D3_MIN_MONTHS
    out["pass_shape_text"] = (
        bool(corr_text >= D3_MIN_CORR) if corr_text == corr_text else False
    )
    out["pass_shape_digitised"] = (
        bool(corr_dig >= D3_MIN_CORR) if corr_dig == corr_dig else False
    )
    out["pass_level"] = bool(annual_pass)
    out["pass"] = bool(
        annual_pass
        and out["pass_support_with_digitised"]
        and (out["pass_shape_digitised"] or out["pass_shape_text"])
    )
    out["pass_letter_of_precommit"] = bool(
        annual_pass
        and out["pass_support_as_precommitted_text_only"]
        and out["pass_shape_text"]
    )
    return out


def gate_d4(hourly: pd.DataFrame, fuel: pd.DataFrame) -> dict:
    """D4: monthly r(index, CC fuel cost) ≥ 0.70; annual ratio within [0.8, 2.0]."""
    mi = _monthly_index(hourly)
    al = fuel[fuel["state"] == "AL"].set_index("period")["cc_fuel_cost_usd_mwh"]
    corr = _corr(mi["I"], al)
    h = hourly.copy()
    h["year"] = _std_year(h["hour_utc"])
    years = {}
    ok = corr >= D4_MIN_CORR
    for y in YEARS:
        hy = h[h["year"] == y]
        I_y = _weighted_mean(hy["price"], hy["mwh"])
        fc = float(al[[p.startswith(str(y)) for p in al.index]].mean())
        ratio = I_y / fc
        p = D4_RATIO_RANGE[0] <= ratio <= D4_RATIO_RANGE[1]
        ok &= bool(p)
        years[int(y)] = {
            "I_year": round(I_y, 3),
            "FC_year": round(fc, 3),
            "ratio": round(ratio, 4),
            "pass": bool(p),
        }
    return {
        "corr_monthly_AL": round(corr, 4),
        "min_corr": D4_MIN_CORR,
        "ratio_range": D4_RATIO_RANGE,
        "years": years,
        "pairs": {
            k: [round(float(mi["I"].get(k, np.nan)), 2), round(float(v), 2)]
            for k, v in al.items()
        },
        "pass": bool(ok),
    }


def gate_d5(hourly: pd.DataFrame) -> dict:
    """D5: price range, annual mean range, on-peak > off-peak each year."""
    h = hourly[hourly["price"].notna()].copy()
    h["year"] = _std_year(h["hour_utc"])
    prev_hour = h["hour_utc"].dt.tz_convert(PREVAILING_TZ).dt.hour
    h["peak"] = prev_hour.isin(PEAK_HOURS_BEGINNING)
    years = {}
    ok = True
    for y in YEARS:
        hy = h[h["year"] == y]
        mean = _weighted_mean(hy["price"], hy["mwh"])
        pk = _weighted_mean(hy.loc[hy["peak"], "price"], hy.loc[hy["peak"], "mwh"])
        op = _weighted_mean(hy.loc[~hy["peak"], "price"], hy.loc[~hy["peak"], "mwh"])
        p = (D5_MEAN_RANGE[0] < mean <= D5_MEAN_RANGE[1]) and (pk > op)
        ok &= bool(p)
        years[int(y)] = {
            "mean": round(mean, 3),
            "on_peak": round(pk, 3),
            "off_peak": round(op, 3),
            "min": round(float(hy["price"].min()), 2),
            "max": round(float(hy["price"].max()), 2),
            "pass": bool(p),
        }
    rng_ok = bool(
        (h["price"] >= D5_PRICE_RANGE[0]).all()
        and (h["price"] <= D5_PRICE_RANGE[1]).all()
    )
    diurnal = h.groupby(prev_hour[h.index])["price"].mean()
    return {
        "years": years,
        "price_range_ok": rng_ok,
        "price_range": D5_PRICE_RANGE,
        "mean_range": D5_MEAN_RANGE,
        "diurnal_prevailing_mean": {
            int(k): round(float(v), 2) for k, v in diurnal.items()
        },
        "pass": bool(ok and rng_ok),
    }


def to_model_clock(hourly: pd.DataFrame, year: int) -> np.ndarray:
    """Dense 8760 on the fixed-CST non-leap clock (a pure re-indexing)."""
    idx = _std_hour_index(pd.DatetimeIndex(hourly["hour_utc"]), year, STD_TZ)
    dense = np.full(_HOURS_PER_YEAR, np.nan)
    ok = idx >= 0
    dense[idx[ok]] = hourly["price"].to_numpy(float)[ok]
    return dense


def cmd_gate(land: bool) -> None:
    """``gate``: score D1–D5 → ``gate.json``; ``--land`` writes the sidecar iff all pass."""
    hourly = pd.read_parquet(RAW_DIR / "soco_eqr_hourly_utc.parquet")
    hourly["hour_utc"] = pd.to_datetime(hourly["hour_utc"], utc=True)
    demand = _load_demand_hourly()
    fuel = pd.read_csv(RAW_DIR / "fuel_cost_anchor_monthly.csv")
    seem_p = RAW_DIR / "seem_auditor_monthly_prices.csv"
    seem = pd.read_csv(seem_p) if seem_p.exists() else None
    ann_p = PULL_DIR / "seem_annual_text.csv"
    seem_annual = pd.read_csv(ann_p) if ann_p.exists() else None
    gate = {
        "precommit": PRECOMMIT,
        "scored_utc": dt.datetime.utcnow().isoformat(timespec="seconds"),
        "D1": gate_d1(hourly),
        "D2": gate_d2(hourly, demand),
        "D3": gate_d3(hourly, seem, seem_annual),
        "D4": gate_d4(hourly, fuel),
        "D5": gate_d5(hourly),
    }
    keys = ("D1", "D2", "D3", "D4", "D5")
    gate["verdict"] = "SERIES LANDED" if all(gate[k]["pass"] for k in keys) else "NO"
    (RAW_DIR / "gate.json").write_text(json.dumps(gate, indent=1, default=str))
    print(json.dumps({k: gate[k]["pass"] for k in keys}), "→", gate["verdict"])
    if land:
        if gate["verdict"] != "SERIES LANDED":
            raise SystemExit(
                "gate did not pass — nothing written to _validation-source"
            )
        rows = []
        for year in YEARS:
            rows.append(
                pd.DataFrame(
                    {
                        "year": np.int16(year),
                        "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
                        "rt": to_model_clock(hourly, year).astype("float32"),
                        "da": np.full(_HOURS_PER_YEAR, np.nan, dtype="float32"),
                    }
                )
            )
        out = pd.concat(rows, ignore_index=True)
        out.to_parquet(LAND_PATH, index=False)
        print(f"landed {LAND_PATH} rows={len(out)} sha256={_sha256(LAND_PATH)}")


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("links")
    e = sub.add_parser("extract")
    e.add_argument("--quarter", nargs="*", default=None)
    e.add_argument("--keep-zip", action="store_true")
    e.add_argument(
        "--wait", action="store_true", help="wait for each quarter's zip to appear"
    )
    sub.add_parser("fetch-seem")
    sub.add_parser("build")
    g = sub.add_parser("gate")
    g.add_argument(
        "--land",
        action="store_true",
        help="write the sidecar iff every gate cell passes",
    )
    a = ap.parse_args(argv)
    if a.cmd == "links":
        cmd_links()
    elif a.cmd == "extract":
        cmd_extract(a.quarter, a.keep_zip, a.wait)
    elif a.cmd == "fetch-seem":
        cmd_fetch_seem()
    elif a.cmd == "build":
        cmd_build()
    elif a.cmd == "gate":
        cmd_gate(a.land)


if __name__ == "__main__":
    main()
