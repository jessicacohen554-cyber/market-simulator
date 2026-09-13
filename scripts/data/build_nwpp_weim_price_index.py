#!/usr/bin/env python3
"""Build the NWPP footprint hourly price index from CAISO WEIM prices — STOP-gated.

Lane NWPP-13 (``docs/multi-iso/nwpp-addition-plan-2026-09.md`` §8 W1; owner
ruling card N2, both limbs). The Northwest Power Pool publishes no LMP and had
no day-ahead market in 2023–2025. The one market that clears any of this
footprint's energy is CAISO's Western Energy Imbalance Market (WEIM), a
15-minute imbalance market, and its prices are published anonymously on CAISO
OASIS. This script fetches them, aggregates them to the model's hourly clock,
demand-weights them to the footprint, and runs the STOP gate that decides
whether the result may be committed as ``actual_lmp_hourly_NWPP.parquet``.

EVERY rule and EVERY threshold below was fixed in
``docs/handoffs/PRECOMMIT-nwpp-13-2026-09-13.md`` BEFORE any price, transfer or
Mid-C value was read. Nothing here reads a model residual — no NWPP model run
exists (CLAUDE.md rule 1 ``[R-STRUCT]``). The gate can refuse the series; it can
never promote a run.

What is built (``data/raw/nwpp-weim/``, the committed raw store; every path
resolves through ``config/paths.py``):

* ``weim_rtpd_lmp_15min.parquet`` — OASIS ``PRC_RTPD_LMP`` (the 15-minute
  market's LMP) at the ``DEPZ``-type default EIM load aggregation point
  ``ELAP_<BAA>-APND`` of each footprint WEIM BAA, all four components.
* ``weim_transfer_15min.parquet`` — OASIS ``ENE_EIM_TRANSFER`` (``version=2``,
  ``RTPD``): each WEIM BAA's 15-minute EIM transfer MW, the market's own
  settled cross-BAA quantity. Feeds gate D2.
* ``weim_hourly_by_ba.parquet`` — the per-BA hourly LMP on the model's fixed
  non-leap 8760 clock (Pacific STANDARD time, ``Etc/GMT+8`` — the CAISO sidecar's
  ``derive_actual_lmp._STD_TZ`` convention) plus the UTC hour it came from.
* ``midc_peak_daily.parquet`` — the ``Mid C Peak`` rows of EIA's ICE workbooks
  (the independent anchor; daily, peak-only; never the benchmark).
* ``weim_benefits_appendix2_transfers.csv`` — the per-pair monthly WEIM transfer
  volumes transcribed from Appendix 2 of CAISO's WEIM quarterly benefits
  reports (the published cross-check on D2), with report + page per row.
* ``gate.json`` — every measured cell of the PRECOMMIT's §5 gate table.

Node-set rule (PRECOMMIT §2): the ``DEPZ`` apnode for every footprint BA that
has one — 12 nodes, all effective before 2023-06-01, so the set is constant
across the window. ``EIMT`` transfer nodes price inter-BAA transfers, ``CASP``
``CGAP_*_MIDC`` nodes are CAISO scheduling points (gate G17), and the ``EPZ``
``ELAP_{CHPD,DOPD,GCPD,WAUW}`` nodes belong to non-participants and publish no
price (probed 2026-09-13) — none is used. Their load (4.07 % of the 2024
footprint) is UNPRICED and reported as such.

Weighting (PRECOMMIT §3): BA → footprint as the demand-weighted mean over the
11 load-carrying priced BAs, weights = EIA-930 ``Demand (MW) (Adjusted)`` from
the committed ``EIA930_BALANCE_*`` parquets — the same construction as the
rubric's ``rt_lw``. An hour whose priced BAs carry < 90 % of the 11-BA demand is
NaN. Nothing is carried forward or interpolated.

Aggregation (PRECOMMIT §4): the simple mean of the four 15-minute settlement
intervals in the UTC hour; an hour with fewer than 3 of 4 intervals is NaN.

Retention (PRECOMMIT §5 D1): OASIS serves ~39 months and the edge slides one
day per calendar day. Measured 2026-09-13: no data at or before 2023-05-31,
data from 2023-06-01, for both products. 2023 is therefore a PARTIAL year by
retention (at most Jun 1 – Dec 31), declared before the fetch. The committed
parquets are the durable record (the ERCOT / NYISO / SPP precedent: raw pulls
are not committed); a forward year regenerates from the same query (rule 13).

Usage::

    python scripts/data/build_nwpp_weim_price_index.py fetch-lmp
    python scripts/data/build_nwpp_weim_price_index.py fetch-transfer
    python scripts/data/build_nwpp_weim_price_index.py fetch-midc
    python scripts/data/build_nwpp_weim_price_index.py transcribe-benefits
    python scripts/data/build_nwpp_weim_price_index.py reconcile-ties
    python scripts/data/build_nwpp_weim_price_index.py build
    python scripts/data/build_nwpp_weim_price_index.py gate [--land]

``gate --land`` writes ``data/raw/_validation-source/actual_lmp_hourly_NWPP.parquet``
ONLY when every gate cell passes. Raw pulls live in ``data/raw/nwpp-weim/_pulls/``
and are deliberately not committed; ``SHA256SUMS.txt`` records their identity.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import hashlib
import io
import json
import re
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
from market_sim.config import paths  # noqa: E402
from scripts.data.derive_actual_lmp import (  # noqa: E402
    _HOURS_PER_YEAR,
    _std_hour_index,
)

# --------------------------------------------------------------------------- #
# Registry — every value cited to the PRECOMMIT (rule 5 [R-NO-MAGIC]).
# --------------------------------------------------------------------------- #
OASIS_BASE = "https://oasis.caiso.com/oasisapi/SingleZip"
RAW_DIR: Path = paths.RAW_DATA_DIR / "nwpp-weim"
PULL_DIR: Path = RAW_DIR / "_pulls"
LAND_PATH: Path = paths.CALIBRATION_DIR / "actual_lmp_hourly_NWPP.parquet"
EIA930_DIR: Path = paths.EIA_930_DIR

#: The model clock for the sidecar — Pacific STANDARD time, fixed all year
#: (PRECOMMIT §4; ``derive_actual_lmp._STD_TZ["CAISO"]``).
STD_TZ = "Etc/GMT+8"
#: Prevailing Pacific time, used ONLY to locate the Mid-C on-peak block.
PREVAILING_TZ = "America/Los_Angeles"
YEARS: tuple[int, ...] = (2023, 2024, 2025)

#: PRECOMMIT §2 — the DEPZ node per footprint WEIM BAA (OASIS ATL_APNODE,
#: pulled 2026-09-13; effective dates all precede the window).
NODES: dict[str, str] = {
    "BPAT": "ELAP_BPAT-APND",
    "PSEI": "ELAP_PSEI-APND",
    "SCL": "ELAP_SCL-APND",
    "TPWR": "ELAP_TPWR-APND",
    "PGE": "ELAP_PGE-APND",
    "PACW": "ELAP_PACW-APND",
    "IPCO": "ELAP_IPCO-APND",
    "AVA": "ELAP_AVA-APND",
    "NWMT": "ELAP_NWMT-APND",
    "PACE": "ELAP_PACE-APND",
    "NEVP": "ELAP_NEVP-APND",
    "AVRN": "ELAP_AVRN-APND",
}
#: The 11 load-carrying priced BAs (AVRN is generation-only: zero weight).
LOAD_BAS: tuple[str, ...] = (
    "BPAT",
    "PSEI",
    "SCL",
    "TPWR",
    "PGE",
    "PACW",
    "IPCO",
    "AVA",
    "NWMT",
    "PACE",
    "NEVP",
)
#: Ruled N1 footprint — all 17 BAs (plan §3 card N1).
FOOTPRINT_BAS: tuple[str, ...] = LOAD_BAS + (
    "CHPD",
    "DOPD",
    "GCPD",
    "WAUW",
    "AVRN",
    "GRID",
)
#: Non-participant BAs whose load is UNPRICED (PRECOMMIT §2).
UNPRICED_BAS: tuple[str, ...] = ("CHPD", "DOPD", "GCPD", "WAUW")
#: The Mid-C reconciliation group (PRECOMMIT §5 D3) — the mid-Columbia hub's
#: own BAs under card N5's recommended NWPP-NW grouping.
NW_GROUP: tuple[str, ...] = ("BPAT", "PSEI", "SCL", "TPWR")
#: Card N5's RECOMMENDED (unruled) zone grouping — used for a FINDING table
#: only; the committed store is per BA so N5 is not pre-empted.
N5_ZONES: dict[str, tuple[str, ...]] = {
    "NWPP-NW": ("BPAT", "PSEI", "SCL", "TPWR"),
    "NWPP-OR": ("PGE", "PACW"),
    "NWPP-INLAND": ("IPCO", "AVA", "NWMT"),
    "NWPP-EAST": ("PACE",),
    "NWPP-SNV": ("NEVP",),
}

#: PRECOMMIT §3 — an hour's footprint price needs priced BAs carrying this
#: share of the 11-BA demand.
HOUR_WEIGHT_MIN_SHARE = 0.90
#: PRECOMMIT §4 — an hour needs this many of its 4 settlement intervals.
MIN_INTERVALS_PER_HOUR = 3
#: PRECOMMIT §5 D3 — the WSPP/WECC on-peak block HE07–HE22 = hour-beginning
#: 06:00–21:59 prevailing time.
PEAK_HOURS_BEGINNING = tuple(range(6, 22))

#: PRECOMMIT §5 — the gate, as numbers.
D1_NODE_WINDOW_COVERAGE_MIN = 0.95
D1_FULL_YEAR_MIN_HOURS = 8_322  # 95 % of 8,760 (2024, 2025)
D1_2023_MIN_HOURS = 4_380  # 50 % of the year (partial-by-retention)
D2_MIN_SHARE = 0.05
D2_XCHECK_TOL = 0.10
D3_LEVEL_TOL = 0.10  # calibration_verdict.PRICE_MEAN_TOL
D3_MIN_CORR = 0.80
D3_MIN_DAYS = {2023: 60, 2024: 100, 2025: 100}
D4_PRICE_RANGE = (-500.0, 2000.0)
D4_MEAN_RANGE = (0.0, 250.0)

#: D2 cross-check reconciliation month (PRECOMMIT §5 D2): one month of tie-level
#: transfers establishes what ``ENE_EIM_TRANSFER`` IS relative to Appendix 2.
#: July 2024 is the month the charter-era probes used; the identities are
#: definitional, so any fully-covered month serves.
TIE_RECONCILE_START = dt.datetime(2024, 7, 1, 7, 0)
TIE_RECONCILE_END = dt.datetime(2024, 8, 1, 7, 0)
TIE_RECONCILE_TOL = 0.10
#: The retention walk-back starts here (measured edge, 2026-09-13).
RETENTION_PROBE_START = dt.date(2023, 6, 1)
#: Fetch end: the fixed-PST 2025 year ends 2026-01-01 08:00 UTC (= 00:00 PST).
FETCH_END_UTC = dt.datetime(2026, 1, 1, 8, 0)
OASIS_SLEEP_S = 6.0

ICE_URL = "https://www.eia.gov/electricity/wholesale/xls/archive/ice_electric-{year}final.xlsx"
ICE_HUB = "Mid C Peak"
BENEFITS_URL = (
    "https://www.westerneim.com/documents/"
    "iso-western-energy-imbalance-market-benefits-report-q{q}-{year}.pdf"
)
BENEFITS_QUARTERS: tuple[tuple[int, int], ...] = tuple(
    (y, q) for y in YEARS for q in (1, 2, 3, 4)
)
MONTHS = {m: i for i, m in enumerate(calendar.month_name) if m}


# --------------------------------------------------------------------------- #
# OASIS transport
# --------------------------------------------------------------------------- #
def _stamp(ts: dt.datetime) -> str:
    """OASIS datetime literal, UTC (``YYYYMMDDTHH:MM-0000``)."""
    return ts.strftime("%Y%m%dT%H:%M-0000")


def oasis_get(
    params: dict, *, sleep_s: float = OASIS_SLEEP_S, retries: int = 5
) -> tuple[str | None, str]:
    """One OASIS SingleZip call. Returns ``(csv_text, note)``; csv is None on error.

    429 backs off ``15 s × attempt``; every call is followed by ``sleep_s`` so
    nothing here ever bursts against OASIS (its rate limit is strict).
    """
    p = {"resultformat": 6, "version": 1}
    p.update(params)
    last = ""
    for attempt in range(retries):
        try:
            r = requests.get(OASIS_BASE, params=p, timeout=600)
        except requests.RequestException as exc:  # transport
            last = f"transport {exc}"
            time.sleep(15 * (attempt + 1))
            continue
        if r.status_code == 429:
            last = "429"
            time.sleep(15 * (attempt + 1))
            continue
        if r.status_code != 200:
            last = f"http {r.status_code}"
            time.sleep(15 * (attempt + 1))
            continue
        try:
            z = zipfile.ZipFile(io.BytesIO(r.content))
        except zipfile.BadZipFile:
            last = "not-zip"
            time.sleep(15 * (attempt + 1))
            continue
        name = z.namelist()[0]
        data = z.read(name).decode("utf-8", "replace")
        time.sleep(sleep_s)
        if name.endswith(".xml"):
            m = re.search(r"<m:ERR_CODE>(\d+)</m:ERR_CODE>\s*<m:ERR_DESC>([^<]*)", data)
            return None, f"ERR {m.group(1)} {m.group(2)}" if m else "xml-unknown"
        return data, name
    return None, last


def _month_windows(start: dt.datetime, end: dt.datetime):
    """Yield ``(a, b)`` naive-UTC windows, one prevailing-Pacific calendar month each.

    OASIS's "31 days only" limit (``ERR 1004``, measured 2026-09-13) counts
    LOCAL calendar days, so a UTC-midnight month window spans 32 Pacific days
    and is refused; windows are therefore cut at Pacific-prevailing midnight
    and converted to UTC.
    """
    tz = PREVAILING_TZ
    a_loc = pd.Timestamp(start, tz="UTC").tz_convert(tz)
    end_utc = pd.Timestamp(end, tz="UTC")
    while True:
        a_utc = a_loc.tz_convert("UTC")
        if a_utc >= end_utc:
            return
        nxt_loc = (
            a_loc.tz_localize(None).normalize().replace(day=1) + pd.DateOffset(months=1)
        ).tz_localize(tz)
        b_utc = min(nxt_loc.tz_convert("UTC"), end_utc)
        yield (
            a_utc.tz_localize(None).to_pydatetime(),
            b_utc.tz_localize(None).to_pydatetime(),
        )
        a_loc = b_utc.tz_convert(tz)


def _pull_path(kind: str, a: dt.datetime, b: dt.datetime) -> Path:
    return PULL_DIR / f"{kind}_{a:%Y%m%dT%H%M}_{b:%Y%m%dT%H%M}.csv"


def find_first_served_day(kind: str) -> tuple[dt.date, dt.date | None]:
    """Walk back from the measured edge until OASIS returns ERR 1000.

    Returns ``(first_served_day, last_empty_day)``; ``last_empty_day`` is None
    if the walk-back limit was hit without finding the edge (reported, never
    assumed).
    """
    day = RETENTION_PROBE_START
    first_served: dt.date | None = None
    for _ in range(40):
        a = dt.datetime.combine(day, dt.time(7, 0))  # 00:00 PDT on the day
        b = a + dt.timedelta(days=1)
        if kind == "lmp":
            params = {
                "queryname": "PRC_RTPD_LMP",
                "market_run_id": "RTPD",
                "node": NODES["PACW"],
                "startdatetime": _stamp(a),
                "enddatetime": _stamp(b),
            }
        else:
            params = {
                "queryname": "ENE_EIM_TRANSFER",
                "version": 2,
                "market_run_id": "RTPD",
                "baa_grp_id": "ALL",
                "startdatetime": _stamp(a),
                "enddatetime": _stamp(b),
            }
        csv_text, note = oasis_get(params)
        if csv_text is None:
            if "ERR 1000" in note:
                if first_served is None:
                    # the measured edge itself has moved forward: walk forward
                    day += dt.timedelta(days=1)
                    continue
                return first_served, day
            raise RuntimeError(f"walk-back probe failed at {day}: {note}")
        first_served = day
        day -= dt.timedelta(days=1)
    return first_served or RETENTION_PROBE_START, None


def fetch_windows(kind: str, first_day: dt.date, log) -> list[dict]:
    """Fetch every calendar-month window from ``first_day`` to ``FETCH_END_UTC``.

    Each response is checked against its expected row count; a window whose
    rows are below half the expectation is halved (the truncation signature
    ``fetch_caiso_oasis.py`` documents), and a shortfall is logged, never
    filled. Existing pull files are reused (resume-safe).
    """
    # first served day at 00:00 prevailing Pacific (= 07:00 UTC in PDT months)
    start = (
        pd.Timestamp(dt.datetime.combine(first_day, dt.time(0, 0)), tz=PREVAILING_TZ)
        .tz_convert("UTC")
        .tz_localize(None)
        .to_pydatetime()
    )
    manifest: list[dict] = []
    node_list = ",".join(NODES.values())
    todo = list(_month_windows(start, FETCH_END_UTC))
    while todo:
        a, b = todo.pop(0)
        out = _pull_path(kind, a, b)
        days = (b - a).total_seconds() / 86400.0
        if kind == "lmp":
            params = {
                "queryname": "PRC_RTPD_LMP",
                "market_run_id": "RTPD",
                "node": node_list,
                "startdatetime": _stamp(a),
                "enddatetime": _stamp(b),
            }
            expected = len(NODES) * days * 96 * 4
        else:
            params = {
                "queryname": "ENE_EIM_TRANSFER",
                "version": 2,
                "market_run_id": "RTPD",
                "baa_grp_id": "ALL",
                "startdatetime": _stamp(a),
                "enddatetime": _stamp(b),
            }
            expected = None  # BAA count varies; logged, not gated here
        if out.exists():
            rows = sum(1 for _ in open(out, encoding="utf-8")) - 1
            log(f"reuse {out.name} rows={rows}")
            manifest.append(
                {"file": out.name, "rows": rows, "expected": expected, "note": "reused"}
            )
            continue
        csv_text, note = oasis_get(params)
        if csv_text is None:
            if "ERR 1000" in note and a.date() < RETENTION_PROBE_START + dt.timedelta(
                days=45
            ):
                log(
                    f"EMPTY {a:%Y-%m-%d}→{b:%Y-%m-%d}: {note} (inside the retention head)"
                )
                manifest.append(
                    {"file": out.name, "rows": 0, "expected": expected, "note": note}
                )
                continue
            raise RuntimeError(f"fetch failed {a}→{b}: {note}")
        rows = csv_text.count("\n") - 1
        if expected and rows < 0.5 * expected and days > 1:
            mid = a + dt.timedelta(days=int(days // 2))
            log(
                f"SHORT {a:%Y-%m-%d}→{b:%Y-%m-%d}: rows={rows} expected={expected:.0f}; halving"
            )
            todo[:0] = [(a, mid), (mid, b)]
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(csv_text, encoding="utf-8")
        flag = "" if not expected or rows >= 0.99 * expected else " SHORTFALL"
        log(f"pulled {out.name} rows={rows} expected={expected}{flag}")
        manifest.append(
            {"file": out.name, "rows": rows, "expected": expected, "note": note + flag}
        )
    return manifest


# --------------------------------------------------------------------------- #
# Fetch subcommands
# --------------------------------------------------------------------------- #
def cmd_fetch(kind: str) -> None:
    """``fetch-lmp`` / ``fetch-transfer``: walk back the edge, then page monthly."""
    PULL_DIR.mkdir(parents=True, exist_ok=True)
    logf = open(PULL_DIR / f"fetch_{kind}.log", "a", encoding="utf-8")

    def log(msg: str) -> None:
        line = f"{dt.datetime.utcnow():%Y-%m-%dT%H:%M:%SZ} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    first, last_empty = find_first_served_day(kind)
    log(
        f"retention edge ({kind}): first served day {first}, last empty day {last_empty}"
    )
    manifest = fetch_windows(kind, first, log)
    meta = {
        "kind": kind,
        "fetched_utc": dt.datetime.utcnow().isoformat(timespec="seconds"),
        "first_served_day": str(first),
        "last_empty_day": str(last_empty),
        "windows": manifest,
    }
    (PULL_DIR / f"fetch_{kind}_manifest.json").write_text(json.dumps(meta, indent=1))
    log("done")


def cmd_fetch_midc() -> None:
    """``fetch-midc``: the three ICE workbooks → ``midc_peak_daily.parquet``.

    Only ``Mid C Peak`` rows are read. The SP15 / NP15 / Palo Verde hubs in the
    same sheet are NOT read into any artifact (plan §2.6 gate G17).
    """
    PULL_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    for year in YEARS:
        dst = PULL_DIR / f"ice_electric-{year}final.xlsx"
        if not dst.exists():
            r = requests.get(ICE_URL.format(year=year), timeout=300)
            r.raise_for_status()
            dst.write_bytes(r.content)
        raw = pd.read_excel(dst, sheet_name=0, header=0)
        raw.columns = [str(c).replace("\n", " ").strip() for c in raw.columns]
        col = {
            "Price hub": "hub",
            "Trade date": "trade_date",
            "Delivery start date": "delivery_start",
            "Delivery  end date": "delivery_end",
            "Delivery end date": "delivery_end",
            "High price $/MWh": "high",
            "Low price $/MWh": "low",
            "Wtd avg price $/MWh": "wavg",
            "Daily volume MWh": "volume_mwh",
            "Number of trades": "n_trades",
            "Number of counterparties": "n_counterparties",
        }
        df = raw.rename(columns=col)
        df = df[df["hub"].astype(str).str.strip() == ICE_HUB].copy()
        for c in ("trade_date", "delivery_start", "delivery_end"):
            df[c] = pd.to_datetime(df[c]).dt.date
        for c in ("high", "low", "wavg", "volume_mwh", "n_trades", "n_counterparties"):
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(",", "").str.strip(), errors="coerce"
            )
        df["single_day"] = df["delivery_start"] == df["delivery_end"]
        df["source_file"] = dst.name
        frames.append(
            df[
                [
                    "hub",
                    "trade_date",
                    "delivery_start",
                    "delivery_end",
                    "high",
                    "low",
                    "wavg",
                    "volume_mwh",
                    "n_trades",
                    "n_counterparties",
                    "single_day",
                    "source_file",
                ]
            ]
        )
    out = (
        pd.concat(frames)
        .sort_values(["delivery_start", "trade_date"])
        .reset_index(drop=True)
    )
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out.to_parquet(RAW_DIR / "midc_peak_daily.parquet", index=False)
    print(
        f"midc rows={len(out)} single_day={int(out.single_day.sum())} "
        f"by year={out.delivery_start.map(lambda d: d.year).value_counts().sort_index().to_dict()}"
    )


_ROW_RE = re.compile(
    r"(?:(January|February|March|April|May|June|July|August|September|October|November|December)\s+)?"
    r"([A-Z]{2,6})\s+([A-Z]{2,6})\s+([\d,]+)\s+([\d,]+)\s*$"
)


def cmd_transcribe_benefits() -> None:
    """``transcribe-benefits``: Appendix 2 of each quarterly report → CSV.

    Appendix 2 ("WEIM Transfer Volume (MWh)") lists, per month and per ordered
    BAA pair, the 15-minute and 5-minute WEIM transfer volumes with base-schedule
    transfers excluded. The month label is printed only every ~20 rows and is
    carried forward. Reports before Q3-2023 do not carry the appendix (Q1-2023
    none; Q2-2023 a one-page summary), which is recorded, not padded.
    """
    from pypdf import PdfReader  # local import: only this subcommand needs it

    PULL_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    coverage: list[dict] = []
    for year, q in BENEFITS_QUARTERS:
        dst = PULL_DIR / f"weim-benefits-q{q}-{year}.pdf"
        if not dst.exists():
            r = requests.get(BENEFITS_URL.format(q=q, year=year), timeout=300)
            r.raise_for_status()
            dst.write_bytes(r.content)
        pages = [(p.extract_text() or "") for p in PdfReader(dst).pages]
        start = [
            i
            for i, t in enumerate(pages)
            if "APPENDIX 2: WEIM Transfer Volume" in t and not re.search(r"\.{6,}", t)
        ]
        if not start:
            coverage.append({"report": dst.name, "appendix2_pages": None, "rows": 0})
            continue
        s = start[0]
        ends = [
            i
            for i, t in enumerate(pages)
            if i > s and re.search(r"APPENDIX 3", t) and not re.search(r"\.{6,}", t)
        ]
        e = ends[0] if ends else len(pages)
        month = None
        n0 = len(rows)
        for i in range(s, e):
            for line in pages[i].splitlines():
                m = _ROW_RE.search(line.strip())
                if not m:
                    continue
                if m.group(1):
                    month = MONTHS[m.group(1)]
                if month is None:
                    continue
                rows.append(
                    {
                        "report": dst.name,
                        "page": i + 1,
                        "month": f"{year}-{month:02d}",
                        "from_baa": m.group(2),
                        "to_baa": m.group(3),
                        "mwh_15min": int(m.group(4).replace(",", "")),
                        "mwh_5min": int(m.group(5).replace(",", "")),
                    }
                )
        coverage.append(
            {"report": dst.name, "appendix2_pages": [s + 1, e], "rows": len(rows) - n0}
        )
    df = pd.DataFrame(rows)
    df.to_csv(RAW_DIR / "weim_benefits_appendix2_transfers.csv", index=False)
    (PULL_DIR / "benefits_transcription_coverage.json").write_text(
        json.dumps(coverage, indent=1)
    )
    print(json.dumps(coverage, indent=1))
    print(f"rows={len(df)} months={sorted(df.month.unique()) if len(df) else []}")


def cmd_reconcile_ties() -> None:
    """``reconcile-ties``: what ``ENE_EIM_TRANSFER`` is, measured against the ties.

    Pulls one month of ``ENE_EIM_TRANSFER_TIE`` (``version=4``, ``RTPD``: per tie,
    per direction E/I, per BAA, 15-minute MW) and tests two identities, per BA
    and in total, each within ``TIE_RECONCILE_TOL``:

    * **gross**: Σ over ties and directions of tie MW × 0.25 h  ==  the Appendix-2
      published ``mwh_15min`` (from_baa = BA) + (to_baa = BA) for the same month;
    * **net**: Σ_intervals |Σ_ties(I) − Σ_ties(E)| × 0.25 h  ==  the store's
      Σ_intervals |EIM_XFER_MW| × 0.25 h for the same BA and month.

    If both hold, ``ENE_EIM_TRANSFER`` is the BA's NET transfer position per
    interval and Appendix 2 is the pairwise GROSS per direction, so the literal
    cross-check ratio in gate D2 is Σ|net| / Σ gross — netting of simultaneous
    imports and exports across different ties (wheel-through), not a data
    defect. A physical tie carries rows for several (FROM_BAA, TO_BAA) pairs —
    the six-field key (interval, tie, direction, BAA, from, to) is unique
    (measured: 0 duplicates) and nothing is dropped. Rows under a BAA where
    that BAA is neither FROM nor TO are its WHEEL-THROUGH volume (the reports'
    Table 2 quantity); they are excluded from its pairwise gross, reported
    separately, and net to zero in its position by construction.
    Writes ``d2_tie_reconciliation.json``; gate D2 reads it.
    """
    a, b = TIE_RECONCILE_START, TIE_RECONCILE_END
    pull = PULL_DIR / f"tie_rtpd_{a:%Y%m%dT%H%M}_{b:%Y%m%dT%H%M}.parquet"
    if pull.exists():
        tie = pd.read_parquet(pull)
    else:
        csv_text, note = oasis_get(
            {
                "queryname": "ENE_EIM_TRANSFER_TIE",
                "version": 4,
                "market_run_id": "RTPD",
                "baa_grp_id": "ALL",
                "startdatetime": _stamp(a),
                "enddatetime": _stamp(b),
            }
        )
        if csv_text is None:
            raise RuntimeError(f"tie pull failed: {note}")
        tie = pd.read_csv(io.StringIO(csv_text))
        PULL_DIR.mkdir(parents=True, exist_ok=True)
        tie.to_parquet(pull, index=False)
    tie["ts"] = pd.to_datetime(tie["INTERVAL_START_GMT"], utc=True)
    n_raw = len(tie)
    n_dup6 = int(
        tie.duplicated(
            ["ts", "TIE_NAME", "DIRECTION", "BAA_GRP_ID", "FROM_BAA", "TO_BAA"]
        ).sum()
    )
    tie["mwh"] = tie["VALUE"].astype(float) * 0.25
    tie["own"] = (tie["FROM_BAA"] == tie["BAA_GRP_ID"]) | (
        tie["TO_BAA"] == tie["BAA_GRP_ID"]
    )
    month = pd.Timestamp(a, tz="UTC").tz_convert(PREVAILING_TZ).strftime("%Y-%m")
    bench = pd.read_csv(RAW_DIR / "weim_benefits_appendix2_transfers.csv")
    bench = bench[bench["month"] == month]
    store = pd.read_parquet(RAW_DIR / "weim_transfer_15min.parquet")
    store["ts"] = pd.to_datetime(store["interval_start_utc"], utc=True)
    store = store[(store["ts"] >= tie["ts"].min()) & (store["ts"] <= tie["ts"].max())]
    gross = (
        tie[tie["own"]]
        .groupby(["BAA_GRP_ID", "DIRECTION"])["mwh"]
        .sum()
        .unstack()
        .fillna(0.0)
    )
    wheel = tie[~tie["own"]].groupby("BAA_GRP_ID")["mwh"].sum()
    net = tie.pivot_table(
        index=["BAA_GRP_ID", "ts"], columns="DIRECTION", values="mwh", aggfunc="sum"
    ).fillna(0.0)
    net["net"] = net.get("I", 0.0) - net.get("E", 0.0)
    absnet = net.groupby("BAA_GRP_ID")["net"].apply(lambda v: float(v.abs().sum()))
    store_absnet = store.groupby("baa")["xfer_mw"].apply(
        lambda v: float((v.abs() * 0.25).sum())
    )
    per: dict = {}
    tg = tp = tn = ts_ = 0.0
    for ba in LOAD_BAS + ("AVRN",):
        g = float(gross.loc[ba].sum()) if ba in gross.index else float("nan")
        p_ = float(
            bench.loc[bench["from_baa"] == ba, "mwh_15min"].sum()
            + bench.loc[bench["to_baa"] == ba, "mwh_15min"].sum()
        )
        n_ = float(absnet.get(ba, float("nan")))
        s_ = float(store_absnet.get(ba, float("nan")))
        per[ba] = {
            "tie_wheel_through_gwh": round(float(wheel.get(ba, 0.0)) / 1e3, 1),
            "tie_gross_gwh": round(g / 1e3, 1),
            "published_gross_gwh": round(p_ / 1e3, 1),
            "gross_ratio": round(g / p_, 4) if p_ else None,
            "tie_absnet_gwh": round(n_ / 1e3, 1),
            "store_absnet_gwh": round(s_ / 1e3, 1),
            "net_ratio": round(s_ / n_, 4) if n_ else None,
        }
        if ba in LOAD_BAS:
            tg += g
            tp += p_
            tn += n_
            ts_ += s_
    out = {
        "month": month,
        "tie_rows": int(n_raw),
        "duplicates_on_six_field_key": n_dup6,
        "ties": int(tie["TIE_NAME"].nunique()),
        "per_ba": per,
        "gross_identity": {
            "tie_gwh": round(tg / 1e3, 1),
            "published_gwh": round(tp / 1e3, 1),
            "ratio": round(tg / tp, 4),
            "tol": TIE_RECONCILE_TOL,
            "pass": bool(abs(tg / tp - 1) <= TIE_RECONCILE_TOL),
        },
        "net_identity": {
            "store_gwh": round(ts_ / 1e3, 1),
            "tie_gwh": round(tn / 1e3, 1),
            "ratio": round(ts_ / tn, 4),
            "tol": TIE_RECONCILE_TOL,
            "pass": bool(abs(ts_ / tn - 1) <= TIE_RECONCILE_TOL),
        },
        "meaning": (
            "ENE_EIM_TRANSFER = per-BAA NET transfer position per interval; Appendix 2 = "
            "pairwise GROSS per direction. The D2 literal cross-check ratio is sum|net| / sum gross."
        ),
    }
    out["pass"] = out["gross_identity"]["pass"] and out["net_identity"]["pass"]
    (RAW_DIR / "d2_tie_reconciliation.json").write_text(json.dumps(out, indent=1))
    print(
        json.dumps(
            {k: out[k] for k in ("month", "gross_identity", "net_identity", "pass")},
            indent=1,
        )
    )


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #
def _read_pulls(kind: str) -> pd.DataFrame:
    files = sorted(PULL_DIR.glob(f"{kind}_*.csv"))
    if not files:
        raise SystemExit(f"no {kind} pulls in {PULL_DIR}; run fetch-{kind} first")
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def build_lmp_store() -> pd.DataFrame:
    """Raw pulls → ``weim_rtpd_lmp_15min.parquet`` (one row per BA per interval)."""
    df = _read_pulls("lmp")
    df["baa"] = (
        df["NODE"]
        .str.replace("ELAP_", "", regex=False)
        .str.replace("-APND", "", regex=False)
    )
    df["interval_start_utc"] = pd.to_datetime(df["INTERVALSTARTTIME_GMT"], utc=True)
    wide = (
        df.pivot_table(
            index=["interval_start_utc", "baa"],
            columns="LMP_TYPE",
            values="PRC",
            aggfunc="mean",
        )
        .rename(columns={"LMP": "lmp", "MCE": "mce", "MCC": "mcc", "MCL": "mcl"})
        .reset_index()
        .sort_values(["baa", "interval_start_utc"])
        .reset_index(drop=True)
    )
    wide = wide.drop_duplicates(["interval_start_utc", "baa"])
    for c in ("lmp", "mce", "mcc", "mcl"):
        wide[c] = wide[c].astype("float32")
    wide.to_parquet(RAW_DIR / "weim_rtpd_lmp_15min.parquet", index=False)
    return wide


def build_transfer_store() -> pd.DataFrame:
    """Raw pulls → ``weim_transfer_15min.parquet``."""
    df = _read_pulls("transfer")
    df["interval_start_utc"] = pd.to_datetime(df["INTERVAL_START_GMT"], utc=True)
    out = (
        df.rename(columns={"BAA_GRP_ID": "baa", "EIM_XFER_MW": "xfer_mw"})[
            ["interval_start_utc", "baa", "xfer_mw"]
        ]
        .drop_duplicates(["interval_start_utc", "baa"])
        .sort_values(["baa", "interval_start_utc"])
        .reset_index(drop=True)
    )
    out["xfer_mw"] = out["xfer_mw"].astype("float32")
    out.to_parquet(RAW_DIR / "weim_transfer_15min.parquet", index=False)
    return out


def hourly_utc_by_ba(store: pd.DataFrame) -> pd.DataFrame:
    """15-min → UTC-hour mean per BA; < ``MIN_INTERVALS_PER_HOUR`` intervals → NaN."""
    s = store.assign(hour_utc=store["interval_start_utc"].dt.floor("h"))
    g = s.groupby(["baa", "hour_utc"])["lmp"].agg(["mean", "count"]).reset_index()
    g["lmp"] = np.where(g["count"] >= MIN_INTERVALS_PER_HOUR, g["mean"], np.nan)
    return g.rename(columns={"count": "n_intervals"})[
        ["baa", "hour_utc", "lmp", "n_intervals"]
    ]


def load_demand_hourly() -> pd.DataFrame:
    """EIA-930 ``Demand (MW) (Adjusted)`` for the 17 footprint BAs, UTC hour-beginning.

    Read from the committed ``EIA930_BALANCE_<yr>_<half>.parquet`` files (plan
    §2.5); the Adjusted column already carries the defect screen (gate G20).
    Includes the 2026 H1 file so the fixed-PST 2025 year's last 8 UTC hours exist.
    """
    files = sorted(EIA930_DIR.glob("EIA930_BALANCE_202[3-6]_*.parquet"))
    cols = ["Balancing Authority", "UTC Time at End of Hour", "Demand (MW) (Adjusted)"]
    parts = []
    for f in files:
        d = pd.read_parquet(f, columns=cols)
        d = d[d["Balancing Authority"].isin(FOOTPRINT_BAS)]
        parts.append(d)
    d = pd.concat(parts, ignore_index=True)
    end = pd.to_datetime(
        d["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p", utc=True
    )
    return pd.DataFrame(
        {
            "baa": d["Balancing Authority"].to_numpy(),
            "hour_utc": (end - pd.Timedelta(hours=1)).to_numpy(),
            "demand_mw": d["Demand (MW) (Adjusted)"].to_numpy(float),
        }
    ).drop_duplicates(["baa", "hour_utc"])


def weighted_group_price(
    hourly: pd.DataFrame, demand: pd.DataFrame, group: tuple[str, ...]
) -> pd.DataFrame:
    """Demand-weighted mean over ``group`` per UTC hour, with the 90 % member rule.

    Returns ``hour_utc, price, priced_share`` — ``price`` NaN where the priced
    members carry < ``HOUR_WEIGHT_MIN_SHARE`` of the group's demand.
    """
    h = hourly[hourly["baa"].isin(group)][["baa", "hour_utc", "lmp"]]
    w = demand[demand["baa"].isin(group)][["baa", "hour_utc", "demand_mw"]]
    m = w.merge(h, on=["baa", "hour_utc"], how="left")
    m["w"] = m["demand_mw"].clip(lower=0).fillna(0.0)
    m["priced"] = m["lmp"].notna()
    m["wp"] = np.where(m["priced"], m["w"], 0.0)
    m["wxp"] = np.where(m["priced"], m["w"] * m["lmp"], 0.0)
    g = m.groupby("hour_utc").agg(w=("w", "sum"), wp=("wp", "sum"), wxp=("wxp", "sum"))
    share = np.where(g["w"] > 0, g["wp"] / g["w"], 0.0)
    price = np.where(
        (share >= HOUR_WEIGHT_MIN_SHARE) & (g["wp"] > 0), g["wxp"] / g["wp"], np.nan
    )
    return pd.DataFrame(
        {"hour_utc": g.index, "price": price, "priced_share": share}
    ).reset_index(drop=True)


def to_model_clock(series: pd.DataFrame, value_col: str, year: int) -> np.ndarray:
    """Dense 8760 array on the fixed-PST non-leap clock for ``year``."""
    idx = pd.DatetimeIndex(series["hour_utc"])
    hour = _std_hour_index(idx, year, STD_TZ)
    s = pd.Series(series[value_col].to_numpy(float)).groupby(hour).mean()
    s = s[s.index >= 0]
    return s.reindex(range(_HOURS_PER_YEAR)).to_numpy(float)


def cmd_build() -> None:
    """``build``: stores + per-BA hourly + footprint/NW candidate series (to gate)."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    lmp = build_lmp_store()
    xfer = build_transfer_store()
    hourly = hourly_utc_by_ba(lmp)
    demand = load_demand_hourly()

    # per-BA product on the model clock
    rows = []
    for year in YEARS:
        for ba in NODES:
            h = hourly[hourly["baa"] == ba]
            dense = to_model_clock(h, "lmp", year)
            rows.append(
                pd.DataFrame(
                    {
                        "year": np.int16(year),
                        "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
                        "baa": ba,
                        "lmp": dense.astype("float32"),
                    }
                )
            )
    by_ba = pd.concat(rows, ignore_index=True)
    by_ba.to_parquet(RAW_DIR / "weim_hourly_by_ba.parquet", index=False)

    # candidate footprint + NW-group + N5 zone series, UTC-hourly (kept for gate)
    cand = {
        "footprint": weighted_group_price(hourly, demand, LOAD_BAS),
        "nw_group": weighted_group_price(hourly, demand, NW_GROUP),
    }
    for z, bas in N5_ZONES.items():
        cand[z] = weighted_group_price(hourly, demand, bas)
    cand_df = None
    for k, v in cand.items():
        v = v.rename(columns={"price": f"price_{k}", "priced_share": f"share_{k}"})
        cand_df = v if cand_df is None else cand_df.merge(v, on="hour_utc", how="outer")
    cand_df = cand_df.sort_values("hour_utc").reset_index(drop=True)
    cand_df.to_parquet(PULL_DIR / "candidate_hourly_utc.parquet", index=False)
    hourly.to_parquet(PULL_DIR / "hourly_utc_by_ba.parquet", index=False)
    demand.to_parquet(PULL_DIR / "eia930_demand_hourly_utc.parquet", index=False)
    print(
        f"lmp store rows={len(lmp)} bas={lmp.baa.nunique()} "
        f"span={lmp.interval_start_utc.min()}→{lmp.interval_start_utc.max()}"
    )
    print(f"transfer store rows={len(xfer)} bas={xfer.baa.nunique()}")
    print(f"by_ba rows={len(by_ba)}; candidate hours={len(cand_df)}")


# --------------------------------------------------------------------------- #
# Gate
# --------------------------------------------------------------------------- #
def _year_of_pst(hour_utc: pd.Series) -> pd.Series:
    return pd.DatetimeIndex(hour_utc).tz_convert(STD_TZ).year


def gate_d1(hourly: pd.DataFrame, cand: pd.DataFrame, first_served: dt.date) -> dict:
    """D1: per-node coverage inside the served window; footprint hours per year."""
    out: dict = {
        "first_served_day": str(first_served),
        "per_node": {},
        "footprint_hours": {},
        "pass": True,
    }
    served_start = pd.Timestamp(
        dt.datetime.combine(first_served, dt.time(7, 0)), tz="UTC"
    )
    for year in YEARS:
        y0 = pd.Timestamp(f"{year}-01-01 08:00", tz="UTC")  # fixed-PST year start
        y1 = pd.Timestamp(f"{year + 1}-01-01 08:00", tz="UTC")
        w0 = max(y0, served_start)
        window_hours = int((y1 - w0).total_seconds() // 3600) if y1 > w0 else 0
        out["per_node"][year] = {}
        for ba in NODES:
            h = hourly[
                (hourly["baa"] == ba)
                & (hourly["hour_utc"] >= w0)
                & (hourly["hour_utc"] < y1)
            ]
            n = int(h["lmp"].notna().sum())
            cov = n / window_hours if window_hours else 0.0
            ok = cov >= D1_NODE_WINDOW_COVERAGE_MIN
            out["per_node"][year][ba] = {
                "hours": n,
                "window_hours": window_hours,
                "coverage": round(cov, 4),
                "pass": ok,
            }
            if ba in LOAD_BAS and not ok:
                out["pass"] = False
        # count on the MODEL clock (fixed-PST, Feb 29 dropped) — the hours the sidecar carries
        nf = int(np.isfinite(to_model_clock(cand, "price_footprint", year)).sum())
        bar = D1_2023_MIN_HOURS if year == 2023 else D1_FULL_YEAR_MIN_HOURS
        ok = nf >= bar
        out["footprint_hours"][year] = {
            "hours": nf,
            "bar": bar,
            "share_of_year": round(nf / 8760, 4),
            "pass": ok,
        }
        if not ok:
            out["pass"] = False
    return out


def gate_d2(
    xfer: pd.DataFrame,
    demand: pd.DataFrame,
    cand: pd.DataFrame,
    bench: pd.DataFrame | None,
) -> dict:
    """D2: gross WEIM transfer energy of the 11 load BAs vs footprint demand energy."""
    out: dict = {"years": {}, "xcheck": {}, "pass": True}
    x = xfer.copy()
    x["hour_utc"] = x["interval_start_utc"].dt.floor("h")
    x["abs_mwh"] = x["xfer_mw"].abs() * 0.25
    x["year"] = _year_of_pst(x["hour_utc"])
    d = demand.copy()
    d["year"] = _year_of_pst(d["hour_utc"])
    for year in YEARS:
        xy = x[x["year"] == year]
        hrs = set(xy["hour_utc"])
        dy = d[(d["year"] == year) & d["hour_utc"].isin(hrs)]
        gross11 = float(xy[xy["baa"].isin(LOAD_BAS)]["abs_mwh"].sum())
        gross_avrn = float(xy[xy["baa"] == "AVRN"]["abs_mwh"].sum())
        dem17 = float(
            dy[dy["baa"].isin(FOOTPRINT_BAS)]["demand_mw"].clip(lower=0).sum()
        )
        dem11 = float(dy[dy["baa"].isin(LOAD_BAS)]["demand_mw"].clip(lower=0).sum())
        share17 = gross11 / dem17 if dem17 else float("nan")
        share11 = gross11 / dem11 if dem11 else float("nan")
        per_ba = {
            ba: round(float(xy[xy["baa"] == ba]["abs_mwh"].sum()) / 1e3, 1)
            for ba in LOAD_BAS
        }
        ok = share17 >= D2_MIN_SHARE
        out["years"][year] = {
            "hours_with_transfer_data": len(hrs),
            "gross_transfer_gwh_11ba": round(gross11 / 1e3, 1),
            "gross_transfer_gwh_avrn": round(gross_avrn / 1e3, 1),
            "footprint_demand_gwh_17ba": round(dem17 / 1e3, 1),
            "demand_gwh_11ba": round(dem11 / 1e3, 1),
            "share_of_17ba_demand": round(share17, 4),
            "share_of_11ba_demand": round(share11, 4),
            "per_ba_gross_gwh": per_ba,
            "bar": D2_MIN_SHARE,
            "pass": bool(ok),
        }
        if not ok:
            out["pass"] = False
    # cross-check against the published Appendix-2 volumes, per BA, same months
    if bench is not None and len(bench):
        x["month"] = (
            pd.DatetimeIndex(x["hour_utc"]).tz_convert(PREVAILING_TZ).strftime("%Y-%m")
        )
        months = sorted(set(bench["month"]) & set(x["month"]))
        xm = x[x["month"].isin(months)]
        bm = bench[bench["month"].isin(months)]
        rows = {}
        tot_o = tot_p = 0.0
        for ba in LOAD_BAS + ("AVRN",):
            o = float(xm[xm["baa"] == ba]["abs_mwh"].sum())
            p_out = float(bm[bm["from_baa"] == ba]["mwh_15min"].sum())
            p_in = float(bm[bm["to_baa"] == ba]["mwh_15min"].sum())
            p = p_out + p_in
            rows[ba] = {
                "oasis_abs_net_gwh": round(o / 1e3, 1),
                "published_out_gwh": round(p_out / 1e3, 1),
                "published_in_gwh": round(p_in / 1e3, 1),
                "ratio_oasis_over_published": round(o / p, 4) if p else None,
            }
            if ba in LOAD_BAS:
                tot_o += o
                tot_p += p
        ratio = tot_o / tot_p if tot_p else float("nan")
        ok = abs(ratio - 1.0) <= D2_XCHECK_TOL
        out["xcheck"] = {
            "months": months,
            "per_ba": rows,
            "total_oasis_gwh": round(tot_o / 1e3, 1),
            "total_published_gwh": round(tot_p / 1e3, 1),
            "ratio": round(ratio, 4),
            "tol": D2_XCHECK_TOL,
            "literal_pass": bool(ok),
        }
        # the published GROSS basis, for the record (same months, 17-BA demand)
        dm = d.assign(
            month=pd.DatetimeIndex(d["hour_utc"])
            .tz_convert(PREVAILING_TZ)
            .strftime("%Y-%m")
        )
        dem = float(
            dm[dm["month"].isin(months) & dm["baa"].isin(FOOTPRINT_BAS)]["demand_mw"]
            .clip(lower=0)
            .sum()
        )
        out["xcheck"]["published_gross_share_of_17ba_demand"] = (
            round(tot_p / dem, 4) if dem else None
        )
        out["xcheck"]["oasis_net_share_of_17ba_demand_same_months"] = (
            round(tot_o / dem, 4) if dem else None
        )
        # PRECOMMIT §5 D2: a literal miss means the lane must RECONCILE what the
        # OASIS quantity is before D2 is scored — ``reconcile-ties`` does that.
        rec_p = RAW_DIR / "d2_tie_reconciliation.json"
        rec = json.loads(rec_p.read_text()) if rec_p.exists() else None
        out["xcheck"]["reconciliation"] = rec
        if ok:
            out["xcheck"]["pass"] = True
        elif rec and rec.get("pass"):
            out["xcheck"]["pass"] = True
            out["xcheck"]["note"] = (
                "literal ratio failed; reconciled by the tie-level identities "
                "(net vs pairwise gross) — see d2_tie_reconciliation.json"
            )
        else:
            out["xcheck"]["pass"] = False
            out["pass"] = False
    else:
        out["xcheck"] = {"pass": False, "note": "no Appendix-2 transcription available"}
        out["pass"] = False
    return out


def _peak_block_daily(series: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Per prevailing-Pacific calendar day: mean over HE07–HE22 when all 16 hours are priced."""
    s = series[["hour_utc", value_col]].copy()
    loc = pd.DatetimeIndex(s["hour_utc"]).tz_convert(PREVAILING_TZ)
    s["day"] = loc.date
    s["hb"] = loc.hour
    s = s[s["hb"].isin(PEAK_HOURS_BEGINNING)]
    g = s.groupby("day")[value_col].agg(["mean", "count"])
    g = g[g["count"] == len(PEAK_HOURS_BEGINNING)]
    return g.rename(columns={"mean": "w"})[["w"]]


def gate_d3(cand: pd.DataFrame, midc: pd.DataFrame, hourly: pd.DataFrame) -> dict:
    """D3: NW-group on-peak daily mean vs Mid-C Peak single-day rows, per year."""
    out: dict = {"years": {}, "diagnostics": {}, "pass": True}
    m = midc[midc["single_day"]].copy()
    m["day"] = m["delivery_start"]
    m = m.groupby("day")[
        "wavg"
    ].mean()  # one row per delivery day (duplicates averaged)
    wk = (
        pd.Series([pd.Timestamp(d).dayofweek for d in m.index])
        .value_counts()
        .sort_index()
        .to_dict()
    )
    out["single_day_rows_weekday_census(0=Mon)"] = {
        int(k): int(v) for k, v in wk.items()
    }
    series = {
        "nw_group": _peak_block_daily(cand, "price_nw_group"),
        "footprint": _peak_block_daily(cand, "price_footprint"),
    }
    bpat = hourly[hourly["baa"] == "BPAT"][["hour_utc", "lmp"]]
    series["bpat"] = _peak_block_daily(bpat, "lmp")
    # defect-screen diagnostics: the prevailing-hour diurnal profile of the NW
    # group (a wrong clock would flatten or shift it) and the peak/off-peak order
    loc = pd.DatetimeIndex(cand["hour_utc"]).tz_convert(PREVAILING_TZ)
    prof = cand.assign(hb=loc.hour).groupby("hb")["price_nw_group"].mean()
    out["diagnostics"]["nw_group_mean_by_prevailing_hour"] = {
        int(k): round(float(v), 2) for k, v in prof.items()
    }
    in_peak = pd.Series(loc.hour).isin(PEAK_HOURS_BEGINNING).to_numpy()
    out["diagnostics"]["nw_group_peak_block_mean"] = round(
        float(cand.loc[in_peak, "price_nw_group"].mean()), 2
    )
    out["diagnostics"]["nw_group_offpeak_mean"] = round(
        float(cand.loc[~in_peak, "price_nw_group"].mean()), 2
    )
    for key, s in series.items():
        j = s.join(m.rename("m"), how="inner")
        j["year"] = [d.year for d in j.index]
        if key == "nw_group":
            jj = j.assign(
                ym=[f"{d.year}-{d.month:02d}" for d in j.index], ratio=j["w"] / j["m"]
            )
            out["diagnostics"]["nw_group_monthly"] = {
                ym: {
                    "n_days": int(len(g)),
                    "weim": round(float(g["w"].mean()), 2),
                    "midc": round(float(g["m"].mean()), 2),
                    "gap_pct": round(
                        100
                        * float(g["w"].mean() - g["m"].mean())
                        / float(g["m"].mean()),
                        1,
                    ),
                    "corr": round(float(g["w"].corr(g["m"])), 3)
                    if len(g) > 2
                    else None,
                }
                for ym, g in jj.groupby("ym")
            }
            out["diagnostics"]["nw_group_daily_ratio_quantiles"] = {
                str(q): round(float(jj["ratio"].quantile(q)), 3)
                for q in (0.1, 0.25, 0.5, 0.75, 0.9)
            }
            out["diagnostics"]["nw_group_share_days_below_midc"] = round(
                float((jj["w"] < jj["m"]).mean()), 4
            )
            lo = jj[jj["m"] < 100.0]
            out["diagnostics"]["nw_group_excluding_midc_ge_100"] = {
                "n_days": int(len(lo)),
                "weim": round(float(lo["w"].mean()), 2),
                "midc": round(float(lo["m"].mean()), 2),
                "gap_pct": round(
                    100
                    * float(lo["w"].mean() - lo["m"].mean())
                    / float(lo["m"].mean()),
                    1,
                ),
            }
        per = {}
        for year in YEARS:
            jy = j[j["year"] == year]
            n = len(jy)
            if n < 3:
                per[year] = {"n_days": n, "pass": False, "note": "no overlap"}
                continue
            mw, mm = float(jy["w"].mean()), float(jy["m"].mean())
            level = (mw - mm) / mm if mm else float("nan")
            corr = float(np.corrcoef(jy["w"], jy["m"])[0, 1])
            mae = float((jy["w"] - jy["m"]).abs().mean())
            ok = (
                (abs(level) <= D3_LEVEL_TOL)
                and (corr >= D3_MIN_CORR)
                and (n >= D3_MIN_DAYS[year])
            )
            per[year] = {
                "n_days": n,
                "weim_peak_mean": round(mw, 2),
                "midc_peak_mean": round(mm, 2),
                "level_gap_pct": round(100 * level, 2),
                "corr": round(corr, 4),
                "mae": round(mae, 2),
                "bar": {
                    "level_pct": 100 * D3_LEVEL_TOL,
                    "corr": D3_MIN_CORR,
                    "n_days": D3_MIN_DAYS[year],
                },
                "pass": bool(ok),
            }
        if key == "nw_group":
            out["years"] = per
            if not all(v.get("pass") for v in per.values()):
                out["pass"] = False
        else:
            out["diagnostics"][key] = per
    return out


def gate_d4(hourly: pd.DataFrame, cand: pd.DataFrame, demand: pd.DataFrame) -> dict:
    """D4: structural sanity — parse defects, not fits."""
    out: dict = {"pass": True, "ba_annual_mean": {}, "footprint": {}}
    h = hourly.copy()
    h["year"] = _year_of_pst(h["hour_utc"])
    for year in YEARS:
        out["ba_annual_mean"][year] = {}
        for ba in NODES:
            v = h[(h["year"] == year) & (h["baa"] == ba)]["lmp"]
            mean = float(v.mean()) if v.notna().any() else float("nan")
            out["ba_annual_mean"][year][ba] = round(mean, 2)
            if ba in LOAD_BAS and not np.isnan(mean) and mean < 0:
                out["pass"] = False
    c = cand.copy()
    c["year"] = _year_of_pst(c["hour_utc"])
    d = (
        demand[demand["baa"].isin(LOAD_BAS)]
        .groupby("hour_utc")["demand_mw"]
        .sum()
        .rename("dem")
    )
    c = c.merge(d, left_on="hour_utc", right_index=True, how="left")
    for year in YEARS:
        cy = c[(c["year"] == year) & c["price_footprint"].notna()]
        p = cy["price_footprint"]
        lw = float((p * cy["dem"]).sum() / cy["dem"].sum()) if len(cy) else float("nan")
        rng_ok = (
            bool(((p >= D4_PRICE_RANGE[0]) & (p <= D4_PRICE_RANGE[1])).all())
            if len(cy)
            else False
        )
        mean_ok = bool(D4_MEAN_RANGE[0] < lw <= D4_MEAN_RANGE[1]) if len(cy) else False
        out["footprint"][year] = {
            "hours": int(len(cy)),
            "min": round(float(p.min()), 2) if len(cy) else None,
            "max": round(float(p.max()), 2) if len(cy) else None,
            "mean": round(float(p.mean()), 2) if len(cy) else None,
            "load_weighted_mean": round(lw, 2) if len(cy) else None,
            "range_pass": rng_ok,
            "mean_pass": mean_ok,
        }
        if not (rng_ok and mean_ok):
            out["pass"] = False
    return out


def zone_table(cand: pd.DataFrame, demand: pd.DataFrame) -> dict:
    """FINDING table: per N5-recommended zone, hours and load-weighted mean per year."""
    c = cand.copy()
    c["year"] = _year_of_pst(c["hour_utc"])
    out: dict = {}
    for z, bas in N5_ZONES.items():
        d = (
            demand[demand["baa"].isin(bas)]
            .groupby("hour_utc")["demand_mw"]
            .sum()
            .rename("dem")
        )
        cz = c.merge(d, left_on="hour_utc", right_index=True, how="left")
        out[z] = {}
        for year in YEARS:
            cy = cz[(cz["year"] == year) & cz[f"price_{z}"].notna()]
            if not len(cy):
                out[z][year] = {"hours": 0}
                continue
            p = cy[f"price_{z}"]
            out[z][year] = {
                "hours": int(len(cy)),
                "mean": round(float(p.mean()), 2),
                "load_weighted_mean": round(
                    float((p * cy["dem"]).sum() / cy["dem"].sum()), 2
                ),
                "p50": round(float(p.quantile(0.5)), 2),
                "p95": round(float(p.quantile(0.95)), 2),
            }
    return out


def cmd_gate(land: bool) -> None:
    """``gate``: score D1–D4 → ``gate.json``; ``--land`` writes the sidecar iff all pass."""
    hourly = pd.read_parquet(PULL_DIR / "hourly_utc_by_ba.parquet")
    hourly["hour_utc"] = pd.to_datetime(hourly["hour_utc"], utc=True)
    cand = pd.read_parquet(PULL_DIR / "candidate_hourly_utc.parquet")
    cand["hour_utc"] = pd.to_datetime(cand["hour_utc"], utc=True)
    demand = pd.read_parquet(PULL_DIR / "eia930_demand_hourly_utc.parquet")
    demand["hour_utc"] = pd.to_datetime(demand["hour_utc"], utc=True)
    xfer = pd.read_parquet(RAW_DIR / "weim_transfer_15min.parquet")
    xfer["interval_start_utc"] = pd.to_datetime(xfer["interval_start_utc"], utc=True)
    midc = pd.read_parquet(RAW_DIR / "midc_peak_daily.parquet")
    bench_p = RAW_DIR / "weim_benefits_appendix2_transfers.csv"
    bench = pd.read_csv(bench_p) if bench_p.exists() else None
    meta = json.loads((PULL_DIR / "fetch_lmp_manifest.json").read_text())
    first_served = dt.date.fromisoformat(meta["first_served_day"])

    gate = {
        "precommit": "docs/handoffs/PRECOMMIT-nwpp-13-2026-09-13.md",
        "scored_utc": dt.datetime.utcnow().isoformat(timespec="seconds"),
        "D1": gate_d1(hourly, cand, first_served),
        "D2": gate_d2(xfer, demand, cand, bench),
        "D3": gate_d3(cand, midc, hourly),
        "D4": gate_d4(hourly, cand, demand),
        "n5_zone_table": zone_table(cand, demand),
    }
    gate["verdict"] = (
        "SERIES LANDED"
        if all(gate[k]["pass"] for k in ("D1", "D2", "D3", "D4"))
        else "NO"
    )
    (RAW_DIR / "gate.json").write_text(json.dumps(gate, indent=1, default=str))
    print(
        json.dumps({k: gate[k]["pass"] for k in ("D1", "D2", "D3", "D4")}),
        "→",
        gate["verdict"],
    )
    if land:
        if gate["verdict"] != "SERIES LANDED":
            raise SystemExit(
                "gate did not pass — nothing written to _validation-source"
            )
        rows = []
        for year in YEARS:
            dense = to_model_clock(cand, "price_footprint", year)
            rows.append(
                pd.DataFrame(
                    {
                        "year": np.int16(year),
                        "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
                        "rt": dense.astype("float32"),
                        "da": np.full(_HOURS_PER_YEAR, np.nan, dtype="float32"),
                    }
                )
            )
        out = pd.concat(rows, ignore_index=True)
        out.to_parquet(LAND_PATH, index=False)
        print(
            f"landed {LAND_PATH} rows={len(out)} sha256={hashlib.sha256(LAND_PATH.read_bytes()).hexdigest()}"
        )


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch-lmp")
    sub.add_parser("fetch-transfer")
    sub.add_parser("fetch-midc")
    sub.add_parser("transcribe-benefits")
    sub.add_parser("reconcile-ties")
    sub.add_parser("build")
    g = sub.add_parser("gate")
    g.add_argument(
        "--land",
        action="store_true",
        help="write the sidecar iff every gate cell passes",
    )
    a = ap.parse_args(argv)
    if a.cmd == "fetch-lmp":
        cmd_fetch("lmp")
    elif a.cmd == "fetch-transfer":
        cmd_fetch("transfer")
    elif a.cmd == "fetch-midc":
        cmd_fetch_midc()
    elif a.cmd == "transcribe-benefits":
        cmd_transcribe_benefits()
    elif a.cmd == "reconcile-ties":
        cmd_reconcile_ties()
    elif a.cmd == "build":
        cmd_build()
    elif a.cmd == "gate":
        cmd_gate(a.land)


if __name__ == "__main__":
    main()
