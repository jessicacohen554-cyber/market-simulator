#!/usr/bin/env python3
"""Rebuild Southern Company's FERC Form 714 hourly SYSTEM LAMBDA extract from the PUDL raw archive.

Reproduces ``data/raw/ferc-714/soco_hourly_system_lambda_2019_2025.csv`` (the
re-fetch route named in ``data/raw/ferc-714/README.md``). The series is
REPORTED-ONLY (owner ruling 2026-09-27, "Intake, reported-only"; lane soco-83):
it feeds no gate, no scorer and no LP.

Source (verified by lane soco-82, ``docs/handoffs/r-soco/FINDING-soco-82-2026-09-27.md`` §2):
Catalyst Cooperative's PUDL raw FERC-714 archive, Zenodo record 21738524
(v32.0.0). ``www.ferc.gov`` returns 403 from this environment, so the Zenodo
copy of the same filings is the reachable route.

* **CSV era (report years <= 2020)** — ``ferc714.zip`` member
  ``Part 2 Schedule 6 - Balancing Authority Hourly System Lambda.csv``, rows
  with ``respondent_id == 253`` (Southern Company). One row per day, columns
  ``hour01`` .. ``hour25`` plus a ``timezone`` code.
* **XBRL era (report years >= 2021)** — ``ferc714-xbrl-<year>.zip``, the
  instance document(s) whose filename starts with
  ``Southern_Company_Services,_Inc._(as_Agent)_form714`` and whose entity CID is
  ``C003610``; facts ``ferc:SystemLambda`` (unit USDPerMWh) on instant contexts.
  Where a zip holds a resubmission, the latest filing (largest epoch suffix)
  is used and its values are checked against the earlier one.

The values are the filer's own numbers, unmodified; no PUDL-processed or
imputed table is read (rule 13 [R-MEASURED]).

Clock (see the README "Clock handling" section for the evidence):

* Both eras label hours by their END: CSV ``hourNN`` = hour ending NN:00, XBRL
  instant ``YYYY-MM-DDTHH:00`` = hour ending HH:00 (the day's 24th hour is the
  next day's ``T00:00``). The extract labels each hour by its BEGINNING, the
  PUDL ``datetime_utc`` convention the committed PSEI file already follows.
* The timezone field reads ``CPT`` (Central Prevailing Time) on every day of
  2019-2022 and ``CST`` on every day of 2023-2025, yet in EVERY year Southern
  files exactly 24 values per day — including the 23-hour spring-forward day —
  and never uses ``hour25`` on the 25-hour fall-back day. A prevailing clock
  cannot produce that; a fixed offset can, and the 2023+ filings name it. The
  extract therefore reads every year as Central Standard Time, a fixed UTC-6
  all year, and the script REFUSES to build if any day breaks the 24-value
  pattern or a timezone code outside {CPT, CST} appears.

Usage::

    python scripts/data/fetch_ferc714_system_lambda.py --cache-dir /tmp/ferc714
    python scripts/data/fetch_ferc714_system_lambda.py --cache-dir /tmp/ferc714 --check
"""

from __future__ import annotations

import argparse
import hashlib
import io
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import FERC_714_DIR  # noqa: E402
from market_sim.data.ferc714 import (  # noqa: E402
    FERC714_SYSTEM_LAMBDA_FILES,
    SOCO_EIA_UTILITY_ID,
    SOCO_FERC714_RESPONDENT_ID,
    SOCO_FERC714_XBRL_CID,
    SYSTEM_LAMBDA_COLUMNS,
)

#: PUDL raw FERC-714 archive on Zenodo (v32.0.0; ``datapackage.json`` title
#: "PUDL Raw FERC Form 714"), verified by soco-82.
ZENODO_RECORD = 21738524
ZENODO_FILE_URL = "https://zenodo.org/api/records/{record}/files/{name}/content"

FIRST_YEAR = 2019
LAST_YEAR = 2025
#: Last report year FERC distributed as CSV (``ferc714.zip`` README.txt:
#: "The raw FERC Form 714 data from 2006 to 2020").
LAST_CSV_YEAR = 2020

#: sha256 of every archive file this script reads, measured 2026-09-28 (the
#: Zenodo md5s also match the record's ``checksum`` fields).
ARCHIVE_SHA256: dict[str, str] = {
    "ferc714.zip": "a2797ab2fdc3900d14930ab2b6436d49a2522ededa9069208df75cc7fb9d2d67",
    "ferc714-xbrl-2021.zip": "f1efc570d1476caa1664cc19c9de51eb4d10b7a70ab98463a4a4381cd7627060",
    "ferc714-xbrl-2022.zip": "a210091233942bdf6b1b204732efe0065e8d8604815d449d310d3aa6b84cb1e4",
    "ferc714-xbrl-2023.zip": "44a57e807ba5080c3dc5a41082f973bb7793de865deeaff31b41bc5cb6ac9bf8",
    "ferc714-xbrl-2024.zip": "5cf2c5b60a29d7aba5480c1455e95ec9faf468498f15358daeccb899b15a75fa",
    "ferc714-xbrl-2025.zip": "72aa79b0358e154fa767f6212234ea42de4a65191445699a2b4df4919324530b",
}

CSV_MEMBER = "Part 2 Schedule 6 - Balancing Authority Hourly System Lambda.csv"
XBRL_FILER_PREFIX = "Southern_Company_Services,_Inc._(as_Agent)_form714"
XBRL_INSTANCE_NS = "{http://www.xbrl.org/2003/instance}"
XBRL_LAMBDA_LOCAL_NAME = "SystemLambda"

#: Timezone codes Southern files on Sch. 6 in 2019-2025: ``CPT`` on every day
#: of 2019-2022, ``CST`` on every day of 2023-2025 (the XBRL ``ferc:TimeZone``
#: fact). Both are read as the same fixed UTC-6 clock; see the module docstring.
REPORTED_TIMEZONES = frozenset({"CPT", "CST"})
#: Hours per reported day: every Southern day carries exactly this many
#: values (``hour25`` unused), which is the fixed-offset evidence.
HOURS_PER_REPORTED_DAY = 24
#: Central Standard Time offset from UTC (hours): UTC = CST + 6 h.
CST_TO_UTC_HOURS = 6
#: Hour-ending -> hour-beginning label shift (hours).
HOUR_ENDING_TO_BEGINNING_HOURS = 1


def sha256_of(path: Path) -> str:
    """Return the hex sha256 of a file."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch_archive(name: str, cache_dir: Path) -> Path:
    """Download one archive file into ``cache_dir`` (if absent) and verify its sha256."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / name
    if not path.exists():
        url = ZENODO_FILE_URL.format(record=ZENODO_RECORD, name=name)
        print(f"downloading {url}")
        urllib.request.urlretrieve(url, path)
    got = sha256_of(path)
    if got != ARCHIVE_SHA256[name]:
        raise SystemExit(f"{name}: sha256 {got} != expected {ARCHIVE_SHA256[name]}")
    return path


def local_to_utc(local_hour_ending: pd.Series) -> pd.Series:
    """Convert fixed-CST hour-ending stamps to naive-UTC hour-beginning stamps."""
    return local_hour_ending + pd.Timedelta(
        hours=CST_TO_UTC_HOURS - HOUR_ENDING_TO_BEGINNING_HOURS
    )


def parse_csv_era(zip_path: Path, years: list[int]) -> pd.DataFrame:
    """Return the CSV-era rows (hour-ending local stamps) for ``years``."""
    with zipfile.ZipFile(zip_path) as z:
        raw = pd.read_csv(io.BytesIO(z.read(CSV_MEMBER)), low_memory=False)
    s = raw[
        (raw["respondent_id"] == SOCO_FERC714_RESPONDENT_ID)
        & raw["report_yr"].isin(years)
    ]
    if s.empty:
        return pd.DataFrame(columns=["report_year", "local_hour_ending", "value"])
    bad_tz = set(s["timezone"].str.strip()) - REPORTED_TIMEZONES
    if bad_tz:
        raise SystemExit(f"CSV era: unexpected timezone codes {sorted(bad_tz)}")
    last = f"hour{HOURS_PER_REPORTED_DAY + 1:02d}"
    if (s[last].fillna(0) != 0).any():
        raise SystemExit(
            f"CSV era: {last} populated — the fixed-offset clock reading no longer holds"
        )
    if s.duplicated(["report_yr", "lambda_date"]).any():
        raise SystemExit("CSV era: duplicate (report_yr, lambda_date) rows")
    hour_cols = [f"hour{h:02d}" for h in range(1, HOURS_PER_REPORTED_DAY + 1)]
    day = pd.to_datetime(s["lambda_date"].str.split().str[0], format="%m/%d/%Y")
    long = s.assign(day=day.to_numpy()).melt(
        id_vars=["report_yr", "day"],
        value_vars=hour_cols,
        var_name="h",
        value_name="value",
    )
    long["local_hour_ending"] = long["day"] + pd.to_timedelta(
        long["h"].str[4:].astype(int), unit="h"
    )
    return long.rename(columns={"report_yr": "report_year"})[
        ["report_year", "local_hour_ending", "value"]
    ]


def _xbrl_lambda(doc: bytes) -> tuple[str, dict[pd.Timestamp, float]]:
    """Return (entity CID, {local hour-ending instant: lambda}) from one instance doc."""
    root = ET.fromstring(doc)
    ns = XBRL_INSTANCE_NS
    cids = {e.text for e in root.iter(f"{ns}identifier")}
    if len(cids) != 1:
        raise SystemExit(f"XBRL: expected one entity CID, found {sorted(cids)}")
    instants = {}
    for ctx in root.iter(f"{ns}context"):
        inst = ctx.find(f"{ns}period/{ns}instant")
        if inst is not None:
            instants[ctx.get("id")] = pd.Timestamp(inst.text)
    out: dict[pd.Timestamp, float] = {}
    for el in root:
        if el.tag.rsplit("}", 1)[-1] != XBRL_LAMBDA_LOCAL_NAME:
            continue
        stamp = instants[el.get("contextRef")]
        if stamp in out:
            raise SystemExit(f"XBRL: duplicate SystemLambda instant {stamp}")
        out[stamp] = float(el.text) if el.text not in (None, "") else float("nan")
    tz = {e.text for e in root.iter() if e.tag.rsplit("}", 1)[-1] == "TimeZone"}
    if tz - REPORTED_TIMEZONES:
        raise SystemExit(f"XBRL: unexpected TimeZone values {sorted(tz)}")
    return cids.pop(), out


def parse_xbrl_year(zip_path: Path, year: int) -> tuple[pd.DataFrame, str]:
    """Return one XBRL report year's rows and a provenance note naming the filing used."""
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if n.startswith(XBRL_FILER_PREFIX)]
        if not names:
            return pd.DataFrame(
                columns=["report_year", "local_hour_ending", "value"]
            ), "absent"

        def epoch(n: str) -> int:
            return int(re.search(r"_(\d+)\.xbrl$", n).group(1))

        names.sort(key=epoch)
        parsed = [(n, *_xbrl_lambda(z.read(n))) for n in names]
    chosen, cid, values = parsed[-1]
    if cid != SOCO_FERC714_XBRL_CID:
        raise SystemExit(f"{chosen}: CID {cid} != {SOCO_FERC714_XBRL_CID}")
    note = chosen
    for n, _c, v in parsed[:-1]:
        same = v == values
        note += f"; earlier filing {n} {'identical' if same else 'DIFFERS'}"
    df = pd.DataFrame(
        {
            "report_year": year,
            "local_hour_ending": list(values),
            "value": list(values.values()),
        }
    )
    # The report year's hours end on Jan-1 01:00 .. next Jan-1 00:00.
    first = pd.Timestamp(year=year, month=1, day=1, hour=HOUR_ENDING_TO_BEGINNING_HOURS)
    last = pd.Timestamp(year=year + 1, month=1, day=1)
    if df["local_hour_ending"].min() != first or df["local_hour_ending"].max() != last:
        raise SystemExit(f"{chosen}: instants do not span report year {year}")
    return df, note


def build(cache_dir: Path, years: list[int]) -> tuple[pd.DataFrame, list[str]]:
    """Assemble the extract for ``years`` and return it with provenance notes."""
    frames, notes = [], []
    csv_years = [y for y in years if y <= LAST_CSV_YEAR]
    if csv_years:
        f = parse_csv_era(fetch_archive("ferc714.zip", cache_dir), csv_years)
        f["source"] = "csv"
        frames.append(f)
        notes.append(f"csv {csv_years}: ferc714.zip :: {CSV_MEMBER}")
    for y in (y for y in years if y > LAST_CSV_YEAR):
        name = f"ferc714-xbrl-{y}.zip"
        if name not in ARCHIVE_SHA256:
            notes.append(f"{y}: no archive registered — not in record {ZENODO_RECORD}")
            continue
        f, note = parse_xbrl_year(fetch_archive(name, cache_dir), y)
        f["source"] = "xbrl"
        frames.append(f)
        notes.append(f"xbrl {y}: {name} :: {note}")
    df = pd.concat(frames, ignore_index=True)
    per_day = df.groupby(
        df["local_hour_ending"].sub(pd.Timedelta(hours=1)).dt.normalize()
    ).size()
    if (per_day != HOURS_PER_REPORTED_DAY).any():
        raise SystemExit(
            "a reported day does not carry exactly 24 values — clock reading invalid"
        )
    df["datetime_utc"] = local_to_utc(df["local_hour_ending"])
    df["system_lambda_usd_mwh"] = df["value"].astype(float)
    df["respondent_id_ferc714"] = SOCO_FERC714_RESPONDENT_ID
    df["eia_utility_id"] = SOCO_EIA_UTILITY_ID
    out = (
        df[list(SYSTEM_LAMBDA_COLUMNS)]
        .sort_values("datetime_utc")
        .reset_index(drop=True)
    )
    if out["datetime_utc"].duplicated().any():
        raise SystemExit("duplicate datetime_utc after conversion")
    return out, notes


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Per-report-year rows, NaN / zero / negative counts, missing hours, mean and median."""
    rows = []
    for y, g in df.groupby("report_year"):
        v = g["system_lambda_usd_mwh"]
        start = pd.Timestamp(year=int(y), month=1, day=1) + pd.Timedelta(
            hours=CST_TO_UTC_HOURS
        )
        expected = pd.date_range(
            start, periods=len(pd.date_range(f"{y}-01-01", f"{y}-12-31")) * 24, freq="h"
        )
        missing = len(
            expected.difference(pd.DatetimeIndex(pd.to_datetime(g["datetime_utc"])))
        )
        rows.append(
            {
                "report_year": int(y),
                "rows": len(g),
                "nan": int(v.isna().sum()),
                "zero": int((v == 0).sum()),
                "negative": int((v < 0).sum()),
                "missing_hours": missing,
                "mean": round(float(v.mean()), 2),
                "median": round(float(v.median()), 2),
            }
        )
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: build (or ``--check``) the committed extract."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument(
        "--cache-dir", type=Path, required=True, help="where the Zenodo zips are cached"
    )
    ap.add_argument("--first-year", type=int, default=FIRST_YEAR)
    ap.add_argument("--last-year", type=int, default=LAST_YEAR)
    ap.add_argument(
        "--out",
        type=Path,
        default=FERC_714_DIR / FERC714_SYSTEM_LAMBDA_FILES[SOCO_FERC714_RESPONDENT_ID],
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="rebuild and compare to --out; write nothing",
    )
    a = ap.parse_args(argv)
    df, notes = build(a.cache_dir, list(range(a.first_year, a.last_year + 1)))
    for n in notes:
        print(n)
    print(summarize(df).to_string(index=False))
    if a.check:
        committed = pd.read_csv(a.out)
        fresh = pd.read_csv(io.StringIO(df.to_csv(index=False)))
        same = committed.equals(fresh)
        print("check:", "IDENTICAL" if same else "DIFFERS")
        return 0 if same else 1
    a.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False)
    print(f"wrote {a.out} ({len(df)} rows) sha256 {sha256_of(a.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
