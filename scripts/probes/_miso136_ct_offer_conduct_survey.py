"""miso-136 probe — survey of a within-day MISO CT offer-conduct identification.

Executes PREREG-miso136-ct-offer-conduct-survey-2026-08-06.md §5: adjudicates
whether a public identification for within-day MISO CT offer conduct exists
that is NOT the C7 residual, against the pre-registered gates G-0..G-3.

STRUCTURAL CHECKS ONLY (PREREG K4): headers, unit counts, hour grain, region
counts, masked-ID persistence, attribute presence, selection scope (are
uncleared units in the file?), and the grain-existence count of units whose
submitted curve varies across the hours of one day. NO conduct statistic is
computed — no offer level, no class split, no hour-of-day profile. Measuring
CT conduct is the chartered successor's job, not this survey's.

Rule 22: only 2023-2025-dated report files are fetched (sample days plus the
two 2023/2025 boundary existence checks — all inside the training span).
Nothing is written under data/raw/ (assessment, not intake).

Sources:
  S1  MISO Market Reports daily masked cleared-offer files
      https://docs.misoenergy.org/marketreports/YYYYMMDD_da_co.zip  (DA)
      https://docs.misoenergy.org/marketreports/YYYYMMDD_rt_co.zip  (RT)
  S2  MISO Data Exchange (catalog reachability only)
  S3  Potomac Economics MISO SOM page (document listing only)
  S4  FERC EQR — adjudicated on the miso-135 purpose test, no fetch

Usage:
    python scripts/probes/_miso136_ct_offer_conduct_survey.py \
        [--out results/calibration/_miso136_ct_offer_conduct_survey.json]
"""

from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://docs.misoenergy.org/marketreports"

# Sample days: one mid-summer day per adjacent-day pair (ID persistence), one
# 2023 and one 2025 day; boundary existence checks at the training-span edges.
# All dates are inside 2023-2025 (rule 22 / PREREG T5).
DA_SAMPLES = ["20230715", "20240715", "20240716", "20250115"]
RT_SAMPLES = ["20240715"]
EXISTENCE_CHECKS = ["20230102_da_co.zip", "20251231_da_co.zip"]

S2_URL = "https://www.misoenergy.org/markets-and-operations/market-data/data-exchange/"
S3_URL = "https://www.potomaceconomics.com/markets-monitored/miso/"

SEG_COLS = [f"{p}{i}" for i in range(1, 11) for p in ("Price", "MW")]

# Offer-side (conduct) columns vs outcome columns, per PREREG G-1: the file
# mixes both; only the offer-side columns are the identification candidate.
OFFER_SIDE_COLS = {
    "Economic Max", "Economic Min", "Emergency Max", "Emergency Min",
    "Economic Flag", "Emergency Flag", "Must Run Flag", "Unit Available Flag",
    "Self Scheduled MW", "Target MW Reduction", "Curtailment Offer Price",
    "Slope",
} | set(SEG_COLS)
OUTCOME_COLS_DA = {"MW"}  # cleared DA MW
OUTCOME_COLS_RT = {f"Cleared MW{i}" for i in range(1, 13)}


def _get(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "market-sim-probe"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _head_status(url: str) -> int:
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "market-sim-probe"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status
    except urllib.error.HTTPError as e:  # noqa: PERF203
        return e.code
    except Exception:
        return -1


def _fetch_co(ymd: str, market: str) -> tuple[list[str], list[dict]]:
    """Download one YYYYMMDD_{da,rt}_co.zip and return (columns, rows)."""
    raw = _get(f"{BASE}/{ymd}_{market}_co.zip")
    zf = zipfile.ZipFile(io.BytesIO(raw))
    name = zf.namelist()[0]
    text = zf.read(name).decode("utf-8", errors="replace")
    rdr = csv.DictReader(io.StringIO(text))
    return list(rdr.fieldnames or []), list(rdr)


def _day_structure(cols: list[str], rows: list[dict]) -> dict:
    """Structural facts for one day file (PREREG K4 scope)."""
    units: set[str] = set()
    hours: set[str] = set()
    regions: collections.Counter = collections.Counter()
    curves: dict[str, set] = collections.defaultdict(set)
    decls: dict[str, set] = collections.defaultdict(set)
    zero_hours: collections.Counter = collections.Counter()
    unit_hours: collections.Counter = collections.Counter()
    tcol = "Date/Time Beginning (EST)" if "Date/Time Beginning (EST)" in cols \
        else "Mkthour Begin (EST)"
    for row in rows:
        u = row["Unit Code"]
        units.add(u)
        unit_hours[u] += 1
        hours.add(row[tcol])
        regions[row["Region"].strip() or "(blank)"] += 1
        curves[u].add(tuple(row.get(c, "") for c in SEG_COLS))
        decls[u].add((row.get("Unit Available Flag", ""),
                      row.get("Economic Max", "")))
        if "MW" in row and (row["MW"] or "").strip() in ("", "0"):
            zero_hours[u] += 1
    n = len(units)
    return {
        "rows": len(rows),
        "units": n,
        "distinct_hours": len(hours),
        "region_rowcounts": dict(regions),
        "units_with_hour_varying_curve": sum(1 for u in curves if len(curves[u]) > 1),
        "units_with_hour_varying_declarations": sum(1 for u in decls if len(decls[u]) > 1),
        "units_cleared_zero_all_day": sum(
            1 for u in units if zero_hours.get(u, 0) == unit_hours[u]),
        "_units": units,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path,
                    default=Path("results/calibration/_miso136_ct_offer_conduct_survey.json"))
    args = ap.parse_args()

    out: dict = {"prereg": "PREREG-miso136-ct-offer-conduct-survey-2026-08-06.md"}

    # ---- S1: the daily masked cleared-offer corpus -------------------------
    s1: dict = {"base_url": BASE, "da_days": {}, "rt_days": {}}
    day_units: dict[str, set[str]] = {}
    for ymd in DA_SAMPLES:
        cols, rows = _fetch_co(ymd, "da")
        st = _day_structure(cols, rows)
        day_units[ymd] = st.pop("_units")
        typeish = [c for c in cols if re.search(r"fuel|type|technolog", c, re.I)]
        st["columns"] = cols
        st["type_or_fuel_columns"] = typeish
        st["offer_side_columns_present"] = sorted(OFFER_SIDE_COLS & set(cols))
        st["outcome_columns_present"] = sorted(
            (OUTCOME_COLS_DA | OUTCOME_COLS_RT) & set(cols))
        s1["da_days"][ymd] = st
    for ymd in RT_SAMPLES:
        cols, rows = _fetch_co(ymd, "rt")
        st = _day_structure(cols, rows)
        st.pop("_units")
        st["columns"] = cols
        s1["rt_days"][ymd] = st
    s1["existence_checks"] = {
        f: _head_status(f"{BASE}/{f}") for f in EXISTENCE_CHECKS}
    u_23, u_24, u_24b, u_25 = (day_units[d] for d in DA_SAMPLES)
    s1["masked_id_persistence"] = {
        "day_over_day_20240715_vs_16": {
            "overlap": len(u_24 & u_24b), "a": len(u_24), "b": len(u_24b)},
        "cross_year_2023_vs_2024": len(u_23 & u_24),
        "cross_year_2024_vs_2025": len(u_24 & u_25),
        "cross_year_2023_vs_2025": len(u_23 & u_25),
    }
    out["S1_miso_market_reports_co"] = s1

    # ---- S2: Data Exchange (reachability only) -----------------------------
    try:
        _get(S2_URL, timeout=60)
        s2_status = 200
    except urllib.error.HTTPError as e:
        s2_status = e.code
    except Exception:
        s2_status = -1
    out["S2_data_exchange"] = {
        "url": S2_URL, "status": s2_status,
        "closure": "catalog page not enumerable from this environment "
                   "(WAF); immaterial to the verdict — S1 is the offer "
                   "publication of record, and an API product would serve "
                   "the same masked data",
    }

    # ---- S3: Potomac SOM (document listing only) ---------------------------
    try:
        html = _get(S3_URL, timeout=60).decode("utf-8", errors="replace")
        docs = re.findall(
            r'href="([^"]+\.pdf)"[^>]*>([^<]{0,120}(?:Report|Appendix)[^<]{0,60})<',
            html)
        s3 = {"url": S3_URL, "status": 200,
              "documents_seen": [f"{t.strip()} :: {u}" for u, t in docs[:12]]}
    except Exception as e:  # noqa: BLE001
        s3 = {"url": S3_URL, "status": str(e)}
    s3["closure"] = ("purpose test: IMM monitoring -> aggregate analytics in "
                     "PDF form (markup/output-gap built on confidential "
                     "reference-level estimates = PREREG T2; figures are "
                     "class/market aggregates = T4). No unit-hour corpus. "
                     "Right kind at best, wrong grain — closed.")
    out["S3_potomac_som"] = s3

    # ---- S4: FERC EQR (purpose test, no fetch) -----------------------------
    out["S4_ferc_eqr"] = {
        "closure": "purpose test: EQR exists for public utilities to report "
                   "jurisdictional SALES — contract and transaction-level "
                   "quantities/prices, quarterly. It records transactions, "
                   "not offers into the RTO market; fails G-1 kind on its "
                   "face at any grain. Closed on purpose, no fetch needed.",
    }

    args.out.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
