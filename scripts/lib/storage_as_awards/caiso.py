"""CAISO storage-AS-award intake: Daily Energy Storage Report quarterly xlsx.

Source: CAISO "Daily Energy Storage Report" underlying data, posted quarterly
(https://www.caiso.com/library/daily-energy-storage-reports; release notice
"Daily Energy Storage Report for 1/1/23–9/30/24 data posted"; field definitions
https://www.caiso.com/documents/data-release-and-definitions.pdf). Each file's
``market_output`` sheet carries system-level storage market results:

    TRADE_DATE | HOUR (1..25, DST-aware hour-ending) | INTERVAL |
    MARKET (IFM/RUC/RTPD/RTD) | RES_TYPE (LESR/HYBD) |
    TYPE (EN/SOC/RU/RD/SR/NR) | VALUE (MW)

This parser keeps only the ANCILLARY-SERVICE AWARD rows — TYPE in RU/RD/SR/NR
(EN is the energy schedule and SOC the state of charge, not awards) — for the
IFM (hourly day-ahead, → market "DAM") and RTPD (15-minute real-time
commitment run, hourly-averaged → market "RTM") runs, both storage resource
classes (LESR → "battery": standalone + co-located; HYBD → "hybrid").

Clock: TRADE_DATE + HOUR are prevailing-Pacific hour-ending labels counting
the local day's PHYSICAL hours (spring-forward days run 1..23, fall-back days
1..25 — verified against the 2023–2025 files), so the UTC interval start is
``utc(midnight local of TRADE_DATE) + (HOUR-1) hours`` with no further DST
branching.

Cross-validation anchor (intake assertion in the curation test): the DA
battery award means match DMM-published averages — battery avg hourly AS
procurement ~1,040 MW (2023) and ~1,500 MW (2024) (DMM 2023 Annual Report on
Market Issues & Performance ch. 11; DMM 2024 Annual Report ch. 12 /
2024 Special Report on Battery Storage) — the quarterly files reproduce those
to within ~1 %.
"""

from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from . import CANONICAL_COLUMNS, IsoSpec, register

#: Raw drop location under the shared raw root (immutable, never edited).
RAW_SUBDIR = Path("storage-as-awards") / "CAISO"

#: The published quarterly files (both caiso.com naming patterns: 2023/2024
#: use ``storage-report-<year>q<q>.xlsx``, 2025 uses
#: ``storage-report-q<q>-<year>.xlsx``).
_GLOB = "storage-report-*.xlsx"

_TZ = ZoneInfo("America/Los_Angeles")

#: CAISO AS product → canonical taxonomy (same map as `ancillary-services`).
_PRODUCT: dict[str, str] = {
    "RU": "reg_up",
    "RD": "reg_down",
    "SR": "spin",
    "NR": "nonspin",
}

#: CAISO storage resource type → canonical resource class.
_RES_CLASS: dict[str, str] = {"LESR": "battery", "HYBD": "hybrid"}

#: CAISO market run → canonical market label. IFM is the hourly day-ahead
#: co-optimization (the award that holds through the operating day); RTPD is
#: the 15-minute real-time commitment run (hourly-averaged on the way in).
#: RUC carries no AS rows and RTD's AS follow RTPD; both are dropped.
_MARKET: dict[str, str] = {"IFM": "DAM", "RTPD": "RTM"}


def _files(raw_root: Path) -> list[Path]:
    """The quarterly xlsx files present under the raw drop (sorted)."""
    return sorted((raw_root / RAW_SUBDIR).glob(_GLOB))


def years(raw_root: Path) -> list[int]:
    """Calendar years covered by the raw drop, parsed from the filenames."""
    out: set[int] = set()
    for f in _files(raw_root):
        for tok in f.stem.replace("storage-report-", "").split("-"):
            if tok[:4].isdigit():
                out.add(int(tok[:4]))
            elif tok[-4:].isdigit():
                out.add(int(tok[-4:]))
    return sorted(out)


def parse(raw_root: Path) -> pd.DataFrame:
    """Parse every quarterly file into the canonical tidy award frame."""
    frames = [_parse_file(f) for f in _files(raw_root)]
    if not frames:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))
    df = pd.concat(frames, ignore_index=True)
    return df.sort_values(
        ["interval_start_utc", "resource_class", "market", "product"]
    ).reset_index(drop=True)


def _parse_file(path: Path) -> pd.DataFrame:
    """Parse one quarterly xlsx's ``market_output`` sheet to the tidy frame."""
    raw = pd.read_excel(path, sheet_name="market_output")
    raw = raw[
        raw["TYPE"].isin(_PRODUCT)
        & raw["MARKET"].isin(_MARKET)
        & raw["RES_TYPE"].isin(_RES_CLASS)
    ].copy()
    if raw.empty:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))

    # Hourly-mean MW per (trade_date, hour, market, class, product): IFM rows
    # are already hourly (one INTERVAL), RTPD rows are 15-minute (four
    # INTERVALs) — the groupby-mean puts both on one hourly grain.
    g = (
        raw.groupby(["TRADE_DATE", "HOUR", "MARKET", "RES_TYPE", "TYPE"])["VALUE"]
        .mean()
        .reset_index()
    )

    # HOUR carries prevailing-clock hour-ending labels: ordinary days run
    # 1..24, the spring-forward day 1,2,4..24 (the nonexistent HE3 label is
    # skipped), the fall-back day 1..25 (sequential through the repeated
    # 01:00-02:00). The dense rank of HOUR within each trade date is therefore
    # the day's physical hour index under all three day types, and
    # UTC start = utc(local midnight) + rank hours, DST-free.
    midnight_utc = (
        pd.to_datetime(g["TRADE_DATE"]).dt.tz_localize(_TZ).dt.tz_convert("UTC")
    )
    physical = g.groupby("TRADE_DATE")["HOUR"].rank(method="dense") - 1
    g["interval_start_utc"] = midnight_utc + pd.to_timedelta(physical, unit="h")
    g["interval_start_local"] = (
        g["interval_start_utc"].dt.tz_convert(_TZ).dt.tz_localize(None)
    )
    g["iso"] = "CAISO"
    g["resource_class"] = g["RES_TYPE"].map(_RES_CLASS)
    g["market"] = g["MARKET"].map(_MARKET)
    g["product"] = g["TYPE"].map(_PRODUCT)
    g["award_mw"] = g["VALUE"].astype(float)
    return g[list(CANONICAL_COLUMNS)]


register(
    IsoSpec(
        iso="CAISO",
        parse=parse,
        years=years,
        source=(
            "CAISO Daily Energy Storage Report quarterly data "
            "(caiso.com/library/daily-energy-storage-reports), market_output "
            "sheet; system-level LESR/HYBD AS awards RU/RD/SR/NR, IFM + RTPD"
        ),
    )
)
