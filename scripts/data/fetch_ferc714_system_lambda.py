#!/usr/bin/env python3
"""Rebuild Southern Company's FERC Form 714 hourly SYSTEM LAMBDA extract from the PUDL raw archive.

Reproduces ``data/raw/ferc-714/soco_hourly_system_lambda_2019_2025.csv`` (the
re-fetch route named in ``data/raw/ferc-714/README.md``). The series is
REPORTED-ONLY (owner ruling 2026-09-27, "Intake, reported-only"; lane soco-83):
it feeds no gate, no scorer and no LP.

Source (verified by lane soco-82, ``docs/records/soco/r-soco/FINDING-soco-82-2026-09-27.md`` §2):
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

Neighbour mode (``--set neighbors``; owner ruling soco-97 option (d), data
step 1 of ``docs/handoffs/r-soco/FINDING-soco-97-interchange-rule14-phase0-2026-10-01.md``
§5) builds ``data/raw/ferc-714/soco_neighbor_hourly_system_lambda_2019_2025.csv``
— the same columns plus ``ba_code``, long form — for every filer in
:data:`market_sim.data.ferc714.SOCO_NEIGHBOR_LAMBDA_RESPONDENTS`, from the same
six archive files. Also REPORTED-ONLY. The Southern clock reading is NOT
transferred: each respondent-year is classified from its OWN filing pattern on
the spring-forward day (:func:`classify_clock`) — 24 real values reads as a
fixed standard-time clock (Southern's own argument), 23 real values (an omitted
instant, or a 0/blank placeholder in the non-existent slot) reads as a
prevailing clock and is converted through the respondent's IANA zone — and any
other pattern, an ``hour25`` value, a day with more than 24 values, a fall-back
day without 24, or a timezone code outside the respondent's registered set
REFUSES the build.

Usage::

    python scripts/data/fetch_ferc714_system_lambda.py --cache-dir /tmp/ferc714
    python scripts/data/fetch_ferc714_system_lambda.py --cache-dir /tmp/ferc714 --check
    python scripts/data/fetch_ferc714_system_lambda.py --cache-dir /tmp/ferc714 --set neighbors
    python scripts/data/fetch_ferc714_system_lambda.py --cache-dir /tmp/ferc714 --set neighbors --check
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

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import FERC_714_DIR  # noqa: E402
from market_sim.data.ferc714 import (  # noqa: E402
    FERC714_NEIGHBOR_SYSTEM_LAMBDA_FILE,
    FERC714_SYSTEM_LAMBDA_FILES,
    NEIGHBOR_SYSTEM_LAMBDA_COLUMNS,
    SOCO_EIA_UTILITY_ID,
    SOCO_FERC714_RESPONDENT_ID,
    SOCO_FERC714_XBRL_CID,
    SOCO_NEIGHBOR_LAMBDA_RESPONDENTS,
    SYSTEM_LAMBDA_COLUMNS,
    Ferc714LambdaRespondent,
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


def parse_instant(text: str) -> pd.Timestamp:
    """Parse an XBRL ``instant`` into a naive local hour-ending stamp.

    Filers write the day's 24th hour three ways, all meaning midnight ending
    that day: ``<next day>T00:00:00`` (Southern), ``<day>T24:00:00`` (JEA,
    Tallahassee, MISO) and a date-only ``<day>`` (TVA, Duke, FPL, Santee
    Cooper) — an XBRL date-only instant is the END of that day (XBRL 2.1
    §4.7.2). Every other instant is ``YYYY-MM-DDTHH:MM:SS``.
    """
    text = text.strip()
    if "T" not in text:
        return pd.Timestamp(text) + pd.Timedelta(days=1)
    day, clock = text.split("T", 1)
    if clock.startswith("24"):
        return pd.Timestamp(day) + pd.Timedelta(days=1)
    return pd.Timestamp(text)


def _xbrl_lambda(
    doc: bytes, allowed_tz: frozenset[str] = REPORTED_TIMEZONES
) -> tuple[str, dict[pd.Timestamp, float], frozenset[str]]:
    """Return (entity CID, {local hour-ending instant: lambda}, timezone codes) from one instance doc."""
    root = ET.fromstring(doc)
    ns = XBRL_INSTANCE_NS
    cids = {e.text for e in root.iter(f"{ns}identifier")}
    if len(cids) != 1:
        raise SystemExit(f"XBRL: expected one entity CID, found {sorted(cids)}")
    instants = {}
    for ctx in root.iter(f"{ns}context"):
        inst = ctx.find(f"{ns}period/{ns}instant")
        if inst is not None:
            instants[ctx.get("id")] = parse_instant(inst.text)
    out: dict[pd.Timestamp, float] = {}
    for el in root:
        if el.tag.rsplit("}", 1)[-1] != XBRL_LAMBDA_LOCAL_NAME:
            continue
        stamp = instants[el.get("contextRef")]
        if stamp in out:
            raise SystemExit(f"XBRL: duplicate SystemLambda instant {stamp}")
        out[stamp] = float(el.text) if el.text not in (None, "") else float("nan")
    tz = frozenset(
        (e.text or "").strip()
        for e in root.iter()
        if e.tag.rsplit("}", 1)[-1] == "TimeZone"
    )
    if tz - allowed_tz:
        raise SystemExit(f"XBRL: unexpected TimeZone values {sorted(tz)}")
    return cids.pop(), out, tz


def parse_xbrl_year(
    zip_path: Path,
    year: int,
    filer_prefix: str = XBRL_FILER_PREFIX,
    expected_cid: str = SOCO_FERC714_XBRL_CID,
    allowed_tz: frozenset[str] = REPORTED_TIMEZONES,
) -> tuple[pd.DataFrame, str]:
    """Return one XBRL report year's rows and a provenance note naming the filing used.

    Defaults read Southern's filing; neighbour mode passes the respondent's
    filename prefix, CID and timezone codes. The rows carry the filing's
    timezone codes in ``df.attrs["timezones"]``.
    """
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if n.startswith(filer_prefix)]
        if not names:
            return pd.DataFrame(
                columns=["report_year", "local_hour_ending", "value"]
            ), "absent"

        def epoch(n: str) -> int:
            return int(re.search(r"_(\d+)\.xbrl$", n).group(1))

        names.sort(key=epoch)
        parsed = [(n, *_xbrl_lambda(z.read(n), allowed_tz)) for n in names]
    chosen, cid, values, tz = parsed[-1]
    if cid != expected_cid:
        raise SystemExit(f"{chosen}: CID {cid} != {expected_cid}")
    note = chosen
    for n, _c, v, _tz in parsed[:-1]:
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
    df.attrs["timezones"] = tz
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


# --------------------------------------------------------------- neighbours

#: Clock verdicts :func:`classify_clock` can return.
CLOCK_FIXED = "fixed"
CLOCK_PREVAILING = "prevailing"
#: Hour-ending slots on the spring-forward day that can hold the non-existent
#: hour (filers label it either way: TVA 2022+ omits 02:00, TVA 2021 and Duke
#: Florida omit 03:00; Duke 2020 zero-fills 02:00, Duke 2019/2023+ 03:00).
SPRING_FORWARD_SLOTS_HE = (2, 3)
#: Elliott window for the README table (UTC days, inclusive).
ELLIOTT_UTC = ("2022-12-23 00:00", "2022-12-26 23:00")


def _transition_days(zone: str, year: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return (spring-forward day, fall-back day) of ``year`` in ``zone``."""
    noon = pd.date_range(
        f"{year}-01-01 12:00", f"{year}-12-31 12:00", freq="D", tz=zone
    )
    off = pd.Series(
        [t.utcoffset() for t in noon], index=noon.tz_localize(None).normalize()
    )
    step = off.diff()
    return step[step > pd.Timedelta(0)].index[0], step[step < pd.Timedelta(0)].index[0]


def parse_csv_era_respondent(
    raw: pd.DataFrame, resp: Ferc714LambdaRespondent, years: list[int]
) -> dict[int, pd.DataFrame]:
    """Return {report year: local hour-ending rows} for one neighbour's CSV-era Sch. 6.

    Rows keep every ``hour01``..``hour24`` slot as filed (zeros included, so
    :func:`classify_clock` can see a spring-forward placeholder); ``hour25``
    must be blank or zero on every day. ``df.attrs["timezones"]`` carries the
    year's timezone codes.
    """
    s = raw[(raw["respondent_id"] == resp.respondent_id) & raw["report_yr"].isin(years)]
    out: dict[int, pd.DataFrame] = {}
    last = f"hour{HOURS_PER_REPORTED_DAY + 1:02d}"
    hour_cols = [f"hour{h:02d}" for h in range(1, HOURS_PER_REPORTED_DAY + 1)]
    for year, g in s.groupby("report_yr"):
        if (g[last].fillna(0) != 0).any():
            raise SystemExit(
                f"{resp.ba_code} {year}: {last} populated — clock unclassifiable"
            )
        if g.duplicated(["lambda_date"]).any():
            raise SystemExit(f"{resp.ba_code} {year}: duplicate lambda_date rows")
        tz = frozenset(g["timezone"].fillna("").str.strip())
        if tz - resp.timezone_codes:
            raise SystemExit(
                f"{resp.ba_code} {year}: unexpected timezone codes {sorted(tz)}"
            )
        day = pd.to_datetime(g["lambda_date"].str.split().str[0], format="%m/%d/%Y")
        long = g.assign(day=day.to_numpy()).melt(
            id_vars=["day"], value_vars=hour_cols, var_name="h", value_name="value"
        )
        long["local_hour_ending"] = long["day"] + pd.to_timedelta(
            long["h"].str[4:].astype(int), unit="h"
        )
        df = long[["local_hour_ending", "value"]].assign(report_year=int(year))
        df.attrs["timezones"] = tz
        out[int(year)] = df
    return out


def classify_clock(
    local: pd.DataFrame, year: int, resp: Ferc714LambdaRespondent
) -> tuple[str, pd.Series, str]:
    """Classify one respondent-year's reported clock from its own filing pattern.

    The evidence is the spring-forward day, where a prevailing clock has 23
    hours and a fixed one 24 (Southern's argument, module docstring):

    * 24 slots, all real (non-zero, non-blank) -> ``fixed`` (standard time);
    * 23 real values — one of the hour-ending 02:00/03:00 instants omitted, or
      present as a 0/blank placeholder -> ``prevailing`` (the placeholder is
      dropped, never published as a lambda);
    * anything else -> REFUSE.

    It also refuses a day with more than 24 values and a fall-back day without
    exactly 24 (no filer uses ``hour25``, and an XBRL instant cannot carry the
    repeated hour). Other days may be short (a filing gap, e.g. MISO
    2023-08-17 HE04); the gap is reported as missing hours, never filled.

    Args:
        local: Rows with ``local_hour_ending`` (naive) and ``value``.
        year: Report year.
        resp: The respondent.

    Returns:
        (verdict, keep mask over ``local`` rows, one-line evidence string).
    """
    he = pd.DatetimeIndex(local["local_hour_ending"])
    day = (he - pd.Timedelta(hours=HOUR_ENDING_TO_BEGINNING_HOURS)).normalize()
    per_day = pd.Series(1, index=day).groupby(level=0).size()
    if (per_day > HOURS_PER_REPORTED_DAY).any():
        raise SystemExit(f"{resp.ba_code} {year}: a day carries more than 24 values")
    spring, fall = _transition_days(resp.prevailing_zone, year)
    if per_day.get(fall, 0) != HOURS_PER_REPORTED_DAY:
        raise SystemExit(
            f"{resp.ba_code} {year}: fall-back day {fall.date()} carries "
            f"{per_day.get(fall, 0)} values — clock unclassifiable"
        )
    slots = [spring + pd.Timedelta(hours=h) for h in SPRING_FORWARD_SLOTS_HE]
    in_slot = he.isin(slots)
    v = local["value"].to_numpy(dtype=float)
    placeholder = in_slot & (pd.isna(v) | (v == 0))
    n_spring = int(per_day.get(spring, 0))
    n_placeholder = int(placeholder.sum())
    keep = pd.Series(~placeholder, index=local.index)
    n_in_slot = int(in_slot.sum())
    if n_spring == HOURS_PER_REPORTED_DAY and n_placeholder == 0:
        verdict = CLOCK_FIXED
        how = "24 real values"
    elif (
        n_spring == HOURS_PER_REPORTED_DAY
        and n_placeholder == 1
        and n_in_slot == len(SPRING_FORWARD_SLOTS_HE)
    ) or (
        n_spring == HOURS_PER_REPORTED_DAY - 1
        and n_placeholder == 0
        and n_in_slot == len(SPRING_FORWARD_SLOTS_HE) - 1
    ):
        verdict = CLOCK_PREVAILING
        how = f"23 real values (HE{slots_he(he, in_slot, placeholder)} " + (
            "placeholder dropped)" if n_placeholder else "instant omitted)"
        )
    else:
        raise SystemExit(
            f"{resp.ba_code} {year}: spring-forward day {spring.date()} carries "
            f"{n_spring} values ({n_placeholder} placeholders) — clock unclassifiable"
        )
    return verdict, keep, f"spring {spring.date()}: {how}"


def slots_he(he: pd.DatetimeIndex, in_slot, placeholder) -> str:
    """Name the spring-forward slot a prevailing filer left empty (for the evidence string)."""
    if placeholder.any():
        return f"{he[placeholder][0].hour:02d}"
    present = {t.hour for t in he[in_slot]}
    missing = [h for h in SPRING_FORWARD_SLOTS_HE if h not in present]
    return f"{missing[0]:02d}" if missing else "??"


def neighbor_to_utc(
    local: pd.DataFrame, verdict: str, resp: Ferc714LambdaRespondent
) -> pd.Series:
    """Convert kept local hour-ending stamps to naive-UTC hour-beginning stamps.

    ``fixed``: ``utc = local - standard offset``. ``prevailing``: localize
    each hour-ENDING instant in the respondent's zone — the non-existent
    02:00 on the spring-forward day shifts forward to 03:00 (the end of the
    one real hour 01:00-03:00), and the ambiguous 01:00 on the fall-back day is
    read as daylight time (the end of hour 00:00-01:00); the single value a
    filer gives for the repeated 01:00-02:00 hour lands on the second
    occurrence, leaving the first unreported. Then shift to hour-beginning.
    """
    he = pd.DatetimeIndex(local["local_hour_ending"])
    if verdict == CLOCK_FIXED:
        utc = he - pd.Timedelta(hours=resp.standard_utc_offset_hours)
    else:
        aware = he.tz_localize(
            resp.prevailing_zone,
            ambiguous=np.ones(len(he), dtype=bool),
            nonexistent="shift_forward",
        )
        utc = aware.tz_convert("UTC").tz_localize(None)
    return pd.Series(
        utc - pd.Timedelta(hours=HOUR_ENDING_TO_BEGINNING_HOURS), index=local.index
    )


def build_neighbors(
    cache_dir: Path, years: list[int]
) -> tuple[pd.DataFrame, list[str], pd.DataFrame]:
    """Assemble the long-form neighbour extract.

    Returns:
        (extract, provenance notes, per respondent-year clock table with the
        verdict, timezone codes, evidence and source).
    """
    raw = None
    csv_years = [y for y in years if y <= LAST_CSV_YEAR]
    if csv_years:
        with zipfile.ZipFile(fetch_archive("ferc714.zip", cache_dir)) as z:
            raw = pd.read_csv(io.BytesIO(z.read(CSV_MEMBER)), low_memory=False)
    xbrl = {
        y: fetch_archive(f"ferc714-xbrl-{y}.zip", cache_dir)
        for y in years
        if y > LAST_CSV_YEAR and f"ferc714-xbrl-{y}.zip" in ARCHIVE_SHA256
    }
    frames, notes, clocks = [], [], []
    for resp in SOCO_NEIGHBOR_LAMBDA_RESPONDENTS.values():
        per_year: dict[int, tuple[pd.DataFrame, str]] = {}
        if raw is not None:
            for y, df in parse_csv_era_respondent(raw, resp, csv_years).items():
                per_year[y] = (df, "csv")
            notes.append(
                f"{resp.ba_code} csv {csv_years}: respondent_id {resp.respondent_id}"
            )
        for y, path in xbrl.items():
            df, note = parse_xbrl_year(
                path, y, resp.xbrl_filer_prefix, resp.xbrl_cid, resp.timezone_codes
            )
            notes.append(f"{resp.ba_code} xbrl {y}: {path.name} :: {note}")
            if note != "absent":
                per_year[y] = (df, "xbrl")
        for y in years:
            if y not in per_year:
                raise SystemExit(
                    f"{resp.ba_code}: no Sch. 6 filing for report year {y}"
                )
            df, source = per_year[y]
            df = df.reset_index(drop=True)
            verdict, keep, evidence = classify_clock(df, y, resp)
            kept = df[keep.to_numpy()].copy()
            kept["datetime_utc"] = neighbor_to_utc(kept, verdict, resp)
            if kept["datetime_utc"].duplicated().any():
                raise SystemExit(
                    f"{resp.ba_code} {y}: duplicate UTC hour after conversion"
                )
            kept["source"] = source
            frames.append(
                kept.assign(
                    ba_code=resp.ba_code,
                    respondent_id_ferc714=resp.respondent_id,
                    eia_utility_id=resp.eia_utility_id,
                )
            )
            clocks.append(
                {
                    "ba_code": resp.ba_code,
                    "report_year": y,
                    "source": source,
                    "timezone_codes": "/".join(sorted(df.attrs.get("timezones", ()))),
                    "clock": verdict,
                    "evidence": evidence,
                    "dropped_placeholders": int((~keep).sum()),
                }
            )
    df = pd.concat(frames, ignore_index=True)
    df["system_lambda_usd_mwh"] = df["value"].astype(float)
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"])
    out = (
        df[list(NEIGHBOR_SYSTEM_LAMBDA_COLUMNS)]
        .sort_values(["ba_code", "datetime_utc"])
        .reset_index(drop=True)
    )
    if out.duplicated(["ba_code", "datetime_utc"]).any():
        raise SystemExit("duplicate (ba_code, datetime_utc) after conversion")
    return out, notes, pd.DataFrame(clocks)


def summarize_neighbors(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per respondent-year coverage and the per-respondent README table.

    Returns:
        (per (ba_code, report_year): rows, NaN, zero, negative, missing UTC
        hours, mean; per ba_code: rows, NaN, zero, mean, max and the Elliott
        2022-12-23..26 UTC mean / max).
    """
    rows = []
    for (ba, y), g in df.groupby(["ba_code", "report_year"]):
        resp = SOCO_NEIGHBOR_LAMBDA_RESPONDENTS[ba]
        v = g["system_lambda_usd_mwh"]
        start = pd.Timestamp(year=int(y), month=1, day=1) - pd.Timedelta(
            hours=resp.standard_utc_offset_hours
        )
        n_hours = (
            len(pd.date_range(f"{y}-01-01", f"{y}-12-31")) * HOURS_PER_REPORTED_DAY
        )
        expected = pd.date_range(start, periods=n_hours, freq="h")
        got = pd.DatetimeIndex(pd.to_datetime(g["datetime_utc"]))
        rows.append(
            {
                "ba_code": ba,
                "report_year": int(y),
                "rows": len(g),
                "nan": int(v.isna().sum()),
                "zero": int((v == 0).sum()),
                "negative": int((v < 0).sum()),
                "missing_hours": len(expected.difference(got)),
                "outside_year": len(got.difference(expected)),
                "mean": round(float(v.mean()), 2),
            }
        )
    per_year = pd.DataFrame(rows)
    a, b = (pd.Timestamp(t) for t in ELLIOTT_UTC)
    tot = []
    for ba, g in df.groupby("ba_code", sort=False):
        v = g["system_lambda_usd_mwh"]
        t = pd.to_datetime(g["datetime_utc"])
        e = v[(t >= a) & (t <= b)]
        tot.append(
            {
                "ba_code": ba,
                "rows": len(g),
                "nan": int(v.isna().sum()),
                "zero": int((v == 0).sum()),
                "mean": round(float(v.mean()), 2),
                "max": round(float(v.max()), 2),
                "elliott_hours": len(e),
                "elliott_mean": round(float(e.mean()), 2),
                "elliott_max": round(float(e.max()), 2),
            }
        )
    return per_year, pd.DataFrame(tot)


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
        "--set",
        choices=("soco", "neighbors"),
        default="soco",
        help="soco: Southern's own extract (default); neighbors: SOCO's neighbours, long form",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output CSV (default: the committed file of --set)",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="rebuild and compare to --out; write nothing",
    )
    a = ap.parse_args(argv)
    years = list(range(a.first_year, a.last_year + 1))
    if a.set == "neighbors":
        out = a.out or FERC_714_DIR / FERC714_NEIGHBOR_SYSTEM_LAMBDA_FILE
        df, notes, clocks = build_neighbors(a.cache_dir, years)
        for n in notes:
            print(n)
        per_year, per_ba = summarize_neighbors(df)
        with pd.option_context("display.width", 250, "display.max_colwidth", 80):
            print(clocks.to_string(index=False))
            print(per_year.to_string(index=False))
            print(per_ba.to_string(index=False))
    else:
        out = (
            a.out
            or FERC_714_DIR / FERC714_SYSTEM_LAMBDA_FILES[SOCO_FERC714_RESPONDENT_ID]
        )
        df, notes = build(a.cache_dir, years)
        for n in notes:
            print(n)
        print(summarize(df).to_string(index=False))
    if a.check:
        committed = pd.read_csv(out)
        fresh = pd.read_csv(io.StringIO(df.to_csv(index=False)))
        same = committed.equals(fresh)
        print("check:", "IDENTICAL" if same else "DIFFERS")
        return 0 if same else 1
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"wrote {out} ({len(df)} rows) sha256 {sha256_of(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
