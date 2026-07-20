"""Fetch CAISO's daily Curtailed and Non-Operational Generator reports.

The DAM-published outage/derate instrument (owner-directed intake,
caiso-104): CAISO publishes, each morning for the PRIOR trade date, the
unit-level list of curtailed and non-operational generators — OUTAGE MRID,
RESOURCE NAME/ID, OUTAGE TYPE (FORCED/PLANNED/...), NATURE OF WORK,
CURTAILMENT START/END DATE TIME, CURTAILMENT MW, RESOURCE PMAX MW, NET
QUALIFYING CAPACITY MW (sheet ``PREV_DAY_OUTAGES``). This is the measured
counterpart of the CAMPD-inferred outage windows
(``data/raw/campd-unit-outages-CAISO.csv``): a published outage schedule vs
an inference from emissions gaps (CLAUDE.md rule 14 — prefer measured; rule
13 — a physical availability event with a forward analogue).

Source: https://www.caiso.com/library/curtailed-and-non-operational-generator-reports
URL pattern (one xlsx per trade date):
  https://www.caiso.com/documents/curtailed-non-operational-generator-prior-trade-date-report-YYYYMMDD.xlsx

Files land in ``data/raw/caiso-dam-outages/daily/`` (one file per trade
date, named by the URL's date suffix). Missing days (the occasional 404,
e.g. 2024-12-31) are recorded in ``missing-days.txt`` — coverage gaps fall
back to the CAMPD windows in the loader, per the owner directive. Already-
present files are skipped, so the fetch is resumable.

Usage:
  python scripts/data/fetch_caiso_dam_outages.py [START [END]]
Defaults: 2023-01-01 .. 2025-12-31 (the rule-22 training window; no
out-of-training year is fetched by default).
"""

import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "data" / "raw" / "caiso-dam-outages" / "daily"
# Two published filename conventions for the same daily report: the compact
# YYYYMMDD suffix (2023 through ~May 2024, and again from ~mid-2025) and the
# mon-DD-YYYY suffix (~Jun 2024 .. early 2025, e.g. ...report-jun-10-2024
# .xlsx — the monthly library pages carry the authoritative names). The fetch
# tries both; a day missing under BOTH is a real publication gap.
URL_PATTERNS = (
    "https://www.caiso.com/documents/"
    "curtailed-non-operational-generator-prior-trade-date-report-{compact}.xlsx",
    "https://www.caiso.com/documents/"
    "curtailed-non-operational-generator-prior-trade-date-report-{mon}-{dd}-{yyyy}.xlsx",
)


def main() -> int:
    start = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date(2023, 1, 1)
    end = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date(2025, 12, 31)
    OUT.mkdir(parents=True, exist_ok=True)
    missing_path = OUT.parent / "missing-days.txt"
    missing: list[str] = []
    n_ok = n_skip = 0
    d = start
    while d <= end:
        stamp = d.strftime("%Y%m%d")
        dest = OUT / f"cnog-{stamp}.xlsx"
        if dest.exists() and dest.stat().st_size > 0:
            n_skip += 1
            d += timedelta(days=1)
            continue
        urls = [
            pat.format(
                compact=stamp,
                mon=d.strftime("%b").lower(),
                dd=d.strftime("%d"),
                yyyy=d.strftime("%Y"),
            )
            for pat in URL_PATTERNS
        ]
        blob = None
        last_exc: Exception | None = None
        for url in urls:
            try:
                with urllib.request.urlopen(url, timeout=60) as resp:
                    blob = resp.read()
                if len(blob) < 1000:
                    raise OSError(f"suspiciously small payload ({len(blob)} B)")
                break
            except Exception as exc:  # try the next filename convention
                blob = None
                last_exc = exc
        if blob is not None:
            dest.write_bytes(blob)
            n_ok += 1
        else:  # missing under every convention: a real publication gap
            missing.append(f"{stamp}\t{last_exc}")
            print(f"MISS {stamp}: {last_exc}", flush=True)
        if (n_ok + len(missing)) % 50 == 0:
            print(f"... {d} fetched={n_ok} missing={len(missing)}", flush=True)
        time.sleep(0.3)  # be polite to caiso.com
        d += timedelta(days=1)
    if missing:
        missing_path.write_text("\n".join(missing) + "\n")
    print(f"DONE fetched={n_ok} skipped={n_skip} missing={len(missing)} -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
