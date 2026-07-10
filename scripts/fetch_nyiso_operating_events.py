"""Fetch NYISO operational message logs (P-25 OperMessages, P-35 RealTimeEvents).

Downloads the monthly CSV zip archives from the NYISO MIS public site and
re-serializes them into one valid CSV per (dataset, year) under
``data/raw/NYISO-AS/requirements/``:

    realtime-events/NYISO_realtime_events_<year>.csv   (P-35 Real-Time Events)
    oper-messages/NYISO_oper_messages_<year>.csv       (P-25 Operational Messages)

These are the Ask-B2 event logs of `docs/handoffs/nyiso-data-asks-2026-07.md`:
Thunderstorm Alert declarations, system state changes (normal / alert / major
emergency), reserve pick-ups, emergency energy transactions and out-of-merit
commitment requests — the measured inputs from which the condition-varying
downstate reserve requirement (issue #1344) is reconstructed, since NYISO does
not publish the as-enforced requirement as a continuous historical series
(confirmed 2026-07-10; the Dynamic Reserves market design will post one
forward, but it is not deployed for the backcast window).

Source URL pattern (no authentication):
    http://mis.nyiso.com/public/csv/RealTimeEvents/<yyyymm01>RealTimeEvents_csv.zip
    http://mis.nyiso.com/public/csv/OperMessages/<yyyymm01>OperMessages_csv.zip

Notes
-----
* Timestamps in both feeds are Eastern prevailing wall-clock with no EDT/EST
  marker; they are preserved verbatim here (raw is immutable). The curation
  script (`scripts/curate_nyiso_reserve_requirements.py`) resolves them to UTC.
* The upstream OperMessages CSVs are malformed (doubled quotes + embedded
  newlines), so this script parses them with a tolerant line-accumulating
  reader and re-serializes valid CSV; message text is preserved byte-for-byte.
* Year range: 2018 through H1-2026. Out-of-training years (2018-2022, 2026)
  are intaken under the session-logged owner authorization of 2026-07-10
  (CLAUDE.md rule 22; itemized in docs/out-of-sample-results-2026-07.md §1).
  Nothing past 2026-06 is fetched: --end-month enforces the H1-2026 cap.

Run: ``python scripts/fetch_nyiso_operating_events.py [--cache-dir DIR]``
"""

from __future__ import annotations

import argparse
import io
import re
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = REPO_ROOT / "data" / "raw" / "NYISO-AS" / "requirements"

MIS_BASE = "http://mis.nyiso.com/public/csv"

# (MIS dataset directory, output subdirectory, output file stem)
DATASETS = (
    ("RealTimeEvents", "realtime-events", "NYISO_realtime_events"),
    ("OperMessages", "oper-messages", "NYISO_oper_messages"),
)

# Authorized acquisition window (rule 22; owner authorization 2026-07-10).
START_MONTH = "2018-01"
END_MONTH = "2026-06"  # H1-2026 hard cap — never extend without authorization

# OperMessages data row: "DD-Mon-YYYY HH:MM",<rest of (possibly broken) line>
_OM_ROW = re.compile(r'^"(\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2})",(.*)$')


def _month_range(start: str, end: str) -> list[str]:
    """Inclusive list of YYYYMM month tokens between two YYYY-MM bounds."""
    return [p.strftime("%Y%m") for p in pd.period_range(start=start, end=end, freq="M")]


def _download(url: str, dest: Path, retries: int = 4) -> None:
    """Download ``url`` to ``dest`` unless already cached; simple retry loop."""
    if dest.is_file() and dest.stat().st_size > 0:
        return
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                dest.write_bytes(resp.read())
            return
        except OSError as exc:  # includes URLError / timeouts
            last = exc
    raise RuntimeError(f"failed to download {url}: {last}")


def _parse_realtime_events(text: str) -> pd.DataFrame:
    """Parse one daily RealTimeEvents CSV (well-formed two-column file).

    Days with no events post an empty (or header-only) file; return an empty
    frame for those.
    """
    try:
        df = pd.read_csv(io.StringIO(text))
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=["timestamp_local", "message"])
    df.columns = ["timestamp_local", "message"]
    return df


def _parse_oper_messages(text: str) -> pd.DataFrame:
    """Parse one daily OperMessages CSV, tolerating its malformed quoting.

    Rows open with ``"DD-Mon-YYYY HH:MM",``; anything until the next such
    opener (including newlines) belongs to the current message. Surrounding
    quote runs are stripped; interior text is preserved.
    """
    rows: list[tuple[str, str]] = []
    cur: list[str] | None = None
    for line in text.split("\n")[1:]:  # skip "Insert Time, Message" header
        m = _OM_ROW.match(line)
        if m:
            if cur is not None:
                rows.append((cur[0], cur[1]))
            cur = [m.group(1), m.group(2)]
        elif cur is not None:
            cur[1] += "\n" + line
    if cur is not None:
        rows.append((cur[0], cur[1]))
    out = pd.DataFrame(rows, columns=["timestamp_local", "message"])
    out["message"] = out["message"].str.strip().str.replace(r'^"+|"+$', "", regex=True)
    return out


def fetch(
    cache_dir: Path, start: str = START_MONTH, end: str = END_MONTH
) -> list[Path]:
    """Download all monthly archives and write per-year raw CSVs.

    Parameters
    ----------
    cache_dir:
        Scratch directory for the monthly zips (kept out of the repo; the
        per-year CSVs under ``data/raw`` are the committed artifact).
    start, end:
        YYYY-MM month bounds; ``end`` may never exceed the H1-2026
        authorization cap (enforced).

    Returns the list of per-year CSV paths written.
    """
    if end > END_MONTH:
        raise ValueError(
            f"end month {end} exceeds the authorized acquisition cap {END_MONTH} "
            "(CLAUDE.md rule 22 holdout quarantine)"
        )
    cache_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for mis_name, subdir, stem in DATASETS:
        parser = (
            _parse_realtime_events
            if mis_name == "RealTimeEvents"
            else _parse_oper_messages
        )
        frames: dict[int, list[pd.DataFrame]] = {}
        for month in _month_range(start, end):
            fname = f"{month}01{mis_name}_csv.zip"
            zpath = cache_dir / fname
            _download(f"{MIS_BASE}/{mis_name}/{fname}", zpath)
            with zipfile.ZipFile(zpath) as zf:
                for member in sorted(zf.namelist()):
                    text = zf.read(member).decode("utf-8", errors="replace")
                    df = parser(text)
                    df.insert(0, "source_file", member)
                    frames.setdefault(int(month[:4]), []).append(df)
        out_dir = OUT_ROOT / subdir
        out_dir.mkdir(parents=True, exist_ok=True)
        for year, parts in sorted(frames.items()):
            df = pd.concat(parts, ignore_index=True)
            out = out_dir / f"{stem}_{year}.csv"
            df.to_csv(out, index=False)
            written.append(out)
            print(f"wrote {out}  ({len(df)} rows)")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("/tmp/nyiso-mis-cache"),
        help="scratch directory for the downloaded monthly zips",
    )
    parser.add_argument("--start-month", default=START_MONTH, help="YYYY-MM")
    parser.add_argument(
        "--end-month", default=END_MONTH, help="YYYY-MM (capped at H1-2026)"
    )
    args = parser.parse_args(argv)
    fetch(args.cache_dir, args.start_month, args.end_month)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
