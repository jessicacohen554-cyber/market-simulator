#!/usr/bin/env python3
"""Fetch the PJM neighbors' realized hourly marginal price for convexity.

``scripts/data/derive_neighbor_convexity.py`` regresses each neighbor's realized
hourly price on its own load to recover the ``load_shape_exponent`` (claude.md
rule #11 — a measured, regenerable market quantity, never tuned to PJM's
net-MWh target). NYISO's realized LMP is already shipped
(``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet``), but MISO and the
Carolinas are not, so this script downloads them into the same schema
(``year``, ``hour``, ``rt``, ``da`` on the model's dense 8760-hour local
calendar). It is the data-acquisition half of the convexity step; it needs open
internet, so it is meant to run in the ``fetch-neighbor-lmp`` GitHub Actions
workflow (the sandboxed dev container blocks docs.misoenergy.org / ferc.gov),
which commits the resulting parquet(s) back to the work branch.

Sources (both public, both regenerable for a forward year):

* **MISO** — real-time / day-ahead ex-post hourly LMP, the per-day market
  reports ``docs.misoenergy.org/marketreports/<YYYYMMDD>_rt_lmp_final.csv`` and
  ``..._da_expost_lmp.csv`` (columns ``Node, Type, Value, HE 1..HE 24``; all
  hours Eastern *Standard* time year-round). The ``INDIANA.HUB`` hub LMP is the
  PJM-border price the ComEd/AEP-Ohio/ATSI seam clears against. EST hours are
  carried through UTC into the model's US/Central MISO clock so they align
  hour-for-hour with the ``MISO`` EIA-930 load the convexity regresses on.
  -> ``data/raw/_validation-source/actual_lmp_hourly_MISO.parquet``

* **Carolinas (best-effort)** — the Southeast is not an organized market, so
  there is no LMP; the measured marginal-price proxy is the FERC Form 714
  Part II Schedule 6 *hourly system lambda* for Duke Energy Carolinas / Progress
  (the single incremental cost of energy from their economic dispatch). The
  clean bulk-CSV database runs through 2020 (2021+ is per-filing XBRL), so the
  Carolinas exponent is a *structural* estimate from the latest pre-2021 years
  — convexity is a shape, not a level, so that is still valid for the forward
  seam. This fetch scrapes the FERC data page for the database zip and is
  allowed to fail without blocking the MISO fetch.
  -> ``data/raw/_validation-source/actual_lmp_hourly_Carolinas.parquet``

Run (from the repo root)::

    python scripts/data/fetch_neighbor_lmp.py --source miso --years 2023 2024 2025
    python scripts/data/fetch_neighbor_lmp.py --source carolinas
    python scripts/data/fetch_neighbor_lmp.py --source all
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

# Reuse the canonical chronological 8760-hour calendar mapping (row k = k-th
# UTC hour after local standard midnight Jan 1, local-standard Feb 29 dropped)
# the other realized-LMP parquets are built on, so the MISO/Carolinas outputs
# are byte-comparable. (Until 2026-07-15 this was the prevailing-clock mapping
# — the all-ISO scoring-clock artifact, DIAGNOSIS-ercot-lmp-clock-artifact §1.)
from scripts.data.derive_actual_lmp import (  # noqa: E402
    _HOURS_PER_YEAR,
)

# Write alongside the other realized-LMP parquets (actual_lmp_hourly_<ISO>.parquet),
# which the W1 relocation moved from data/raw/_validation-source/ to data/raw/_validation-source/
# — the path derive_neighbor_convexity.py reads (config.paths.CALIBRATION_DIR). Kept as
# a literal REPO-relative path, not an import, because the fetch GitHub Actions job
# installs only pandas/numpy/etc. (not the market_sim package), so importing
# market_sim.config.paths there fails (ModuleNotFoundError). Keep this in sync with
# config.paths.CALIBRATION_DIR if that ever moves.
OUT_DIR = REPO / "data" / "raw" / "_validation-source"

MISO_REPORTS = "https://docs.misoenergy.org/marketreports"
MISO_HUB = "INDIANA.HUB"  # the PJM-border MISO hub (ComEd/AEP-Ohio/ATSI seam)
# MISO settles on Eastern Standard Time year-round (no DST shift), so each
# market hour is a fixed UTC-5 offset; UTC = EST + 5h.
MISO_EST_OFFSET = pd.Timedelta(hours=5)

FERC_714_PAGE = (
    "https://www.ferc.gov/industries-data/electric/general-information/"
    "electric-industry-forms/form-no-714-annual-electric/data"
)
# FERC respondent names whose system lambda represents the Carolinas seam.
DUKE_RESPONDENT_RE = re.compile(r"duke energy (carolinas|progress)", re.I)


def _session() -> requests.Session:
    """A requests session with polite retries/backoff for flaky public hosts."""
    sess = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry)
    sess.mount("https://", adapter)
    sess.headers["User-Agent"] = "market-sim convexity fetch (research use)"
    return sess


def _days(year: int) -> list[dt.date]:
    """Every calendar date in ``year``."""
    start = dt.date(year, 1, 1)
    end = dt.date(year, 12, 31)
    return [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]


# ---------------------------------------------------------------------------
# MISO
# ---------------------------------------------------------------------------
def _parse_miso_day(text: str) -> np.ndarray | None:
    """Return the 24 EST hour-ending ``INDIANA.HUB`` LMPs from one daily report.

    The report has a few metadata lines before the ``Node,Type,Value,HE 1,...``
    header; each node has three rows (LMP / MCC / MLC). Returns the hub's 24
    LMP values (HE 1..24), or ``None`` when the hub/LMP row is absent.
    """
    lines = text.splitlines()
    header = next(
        (i for i, ln in enumerate(lines) if ln.lstrip().startswith("Node,")),
        None,
    )
    if header is None:
        return None
    frame = pd.read_csv(io.StringIO("\n".join(lines[header:])))
    frame.columns = [c.strip() for c in frame.columns]
    he_cols = [c for c in frame.columns if re.fullmatch(r"HE\s*\d+", c)]
    if len(he_cols) != 24 or "Node" not in frame.columns:
        return None
    row = frame[
        (frame["Node"].astype(str).str.strip() == MISO_HUB)
        & (frame["Value"].astype(str).str.strip() == "LMP")
    ]
    if row.empty:
        return None
    return row.iloc[0][he_cols].to_numpy(dtype=float)


def _fetch_miso_series(
    sess: requests.Session, kind: str, years: tuple[int, ...]
) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Fetch one MISO price series (``kind`` = ``rt`` or ``da``) for ``years``.

    Returns ``{year: (utc_hour_starts, prices)}`` — the hourly hub price stamped
    at the UTC hour-beginning of each EST market hour (HE ``h`` -> EST hour
    beginning ``h-1`` -> UTC = that + 5h), pooled across the year's daily files.
    """
    suffix = "rt_lmp_final" if kind == "rt" else "da_expost_lmp"
    out: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for year in years:
        stamps: list[pd.Timestamp] = []
        prices: list[float] = []
        missing = 0
        for day in _days(year):
            url = f"{MISO_REPORTS}/{day:%Y%m%d}_{suffix}.csv"
            resp = sess.get(url, timeout=60)
            if resp.status_code != 200:
                missing += 1
                continue
            he = _parse_miso_day(resp.text)
            if he is None:
                missing += 1
                continue
            # HE h (1..24) is the EST hour ending h, i.e. beginning h-1.
            base = pd.Timestamp(day) + MISO_EST_OFFSET  # UTC of EST 00:00
            for h in range(24):
                stamps.append(base + pd.Timedelta(hours=h))
                prices.append(he[h])
        if stamps:
            out[year] = (
                pd.DatetimeIndex(stamps).tz_localize("UTC"),
                np.asarray(prices, dtype=float),
            )
            print(
                f"  MISO {kind} {year}: {len(stamps)} hours "
                f"({missing} day-files missing)"
            )
    return out


def _densify_central(utc: pd.DatetimeIndex, price: np.ndarray, year: int) -> np.ndarray:
    """Map a UTC-stamped hourly price onto MISO's chronological 8760 clock.

    Indexes on fixed Central STANDARD time (``Etc/GMT+6``) — the model's MISO
    calendar is chronological (``eia_loader._eia_hourly_frame`` sorts by UTC
    from the CST Jan-1 midnight anchor), NOT the prevailing clock the EIA-930
    extract stamps — so the result aligns row-for-row with the dispatch series
    the convexity regresses on. Under fixed offsets every EST market hour maps
    to a unique slot: no fall-back averaging, no spring-forward NaN.
    """
    hour = _std_hour_index(utc, year, "Etc/GMT+6")
    grouped = pd.Series(price).groupby(hour).mean()
    grouped = grouped[grouped.index >= 0]
    return grouped.reindex(range(_HOURS_PER_YEAR)).to_numpy(dtype=float)


def fetch_miso(years: tuple[int, ...]) -> Path:
    """Build ``actual_lmp_hourly_MISO.parquet`` from the MISO market reports."""
    sess = _session()
    rt = _fetch_miso_series(sess, "rt", years)
    da = _fetch_miso_series(sess, "da", years)
    frames = []
    for year in years:
        if year not in rt and year not in da:
            continue
        rt_h = (
            _densify_central(*rt[year], year)
            if year in rt
            else np.full(_HOURS_PER_YEAR, np.nan)
        )
        da_h = (
            _densify_central(*da[year], year)
            if year in da
            else np.full(_HOURS_PER_YEAR, np.nan)
        )
        frames.append(
            pd.DataFrame(
                {
                    "year": np.int16(year),
                    "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
                    "rt": rt_h.astype(np.float32),
                    "da": da_h.astype(np.float32),
                }
            )
        )
    if not frames:
        raise SystemExit("MISO: no data fetched (all day-files missing?)")
    out = OUT_DIR / "actual_lmp_hourly_MISO.parquet"
    pd.concat(frames, ignore_index=True).to_parquet(out, index=False)
    print(f"  -> wrote {out.relative_to(REPO)}")
    return out


# ---------------------------------------------------------------------------
# Carolinas (best-effort FERC Form 714 system lambda)
# ---------------------------------------------------------------------------
def _find_714_zip(sess: requests.Session) -> str | None:
    """Scrape the FERC Form 714 data page for the bulk-CSV database zip URL."""
    resp = sess.get(FERC_714_PAGE, timeout=60)
    if resp.status_code != 200:
        return None
    hrefs = re.findall(r'href="([^"]+\.zip)"', resp.text, flags=re.I)
    cand = [h for h in hrefs if "714" in h.lower()]
    if not cand:
        return None
    url = cand[0]
    return url if url.startswith("http") else "https://www.ferc.gov" + url


def fetch_carolinas() -> Path | None:
    """Best-effort build of the Carolinas system-lambda parquet from FERC 714.

    Scrapes the FERC data page for the database zip, finds the Part II Sched 6
    *system lambda* CSV, filters Duke Carolinas/Progress respondents and writes
    their hourly lambda on the dense 8760 calendar. Returns ``None`` (with a
    warning) rather than raising if any step's layout does not match — the
    MISO fetch is the load-bearing one, and the Carolinas exponent can be
    sourced manually if this needs hand-tuning against the real files.
    """
    sess = _session()
    zip_url = _find_714_zip(sess)
    if zip_url is None:
        print(
            "  Carolinas: could not locate FERC-714 zip on the data page; "
            "skipping (source it manually — see module docstring)"
        )
        return None
    resp = sess.get(zip_url, timeout=300)
    if resp.status_code != 200:
        print(f"  Carolinas: FERC-714 zip {zip_url} -> {resp.status_code}; skipping")
        return None
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = zf.namelist()
        lambda_csv = next(
            (
                n
                for n in names
                if re.search(r"lambda", n, re.I)
                or re.search(r"part\s*2.*sched.*6", n, re.I)
            ),
            None,
        )
        ids_csv = next((n for n in names if re.search(r"respondent", n, re.I)), None)
        if lambda_csv is None or ids_csv is None:
            print(
                f"  Carolinas: system-lambda/respondent CSV not found in zip "
                f"(have {names[:8]}...); skipping"
            )
            return None
        lam = pd.read_csv(zf.open(lambda_csv))
        ids = pd.read_csv(zf.open(ids_csv))
    print(
        f"  Carolinas: parsed {lambda_csv} ({len(lam)} rows) — "
        "Duke respondent extraction is best-effort; verify before use"
    )
    # Layout varies across vintages; do not guess silently if the expected
    # respondent/name columns are absent.
    name_col = next((c for c in ids.columns if "name" in c.lower()), None)
    rid_col = next(
        (c for c in ids.columns if "respondent" in c.lower() and "id" in c.lower()),
        None,
    )
    if name_col is None or rid_col is None:
        print("  Carolinas: respondent id/name columns not recognised; skipping")
        return None
    duke = ids[ids[name_col].astype(str).str.contains(DUKE_RESPONDENT_RE)]
    print(
        f"  Carolinas: matched Duke respondents -> "
        f"{duke[[rid_col, name_col]].to_dict('records')}"
    )
    print(
        "  Carolinas: hourly-lambda reshape to 8760 is vintage-specific and "
        "left for a verified follow-up; not writing a parquet blind"
    )
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", choices=("miso", "carolinas", "all"), default="all")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    years = tuple(args.years)

    # The output dir may be absent on a fresh/stripped checkout (e.g. a branch
    # whose inputs tree is recovered separately); create it before writing.
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.source in ("miso", "all"):
        print(f"Fetching MISO {MISO_HUB} ex-post LMP for {years} ...")
        fetch_miso(years)
    if args.source in ("carolinas", "all"):
        print("Fetching Carolinas (FERC-714 system lambda, best-effort) ...")
        fetch_carolinas()
    return 0


if __name__ == "__main__":
    sys.exit(main())
