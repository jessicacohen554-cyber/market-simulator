"""SPP ``counterparty-interchange`` spec: both sides of every SWPP seam leg.

Two raw files under ``data/raw/eia-930-interchange`` (README there):

* ``SWPP counterparty interchange hourly.parquet`` — every EIA-930 row whose
  DIBA is SWPP (``scripts/data/fetch_eia930_counterparty_interchange.py``):
  columns ``ba`` (the reporting counterparty), ``mw`` (EIA sign: + = the
  REPORTER exports, i.e. into SWPP) and ``utc_time`` (UTC hour end). Negated
  here onto SWPP's export-positive sign.
* ``SWPP interchange hourly.parquet`` — SWPP's own legs: ``diba``, ``mw``
  (+ = SWPP exports) and ``local_time``, the hour end on SWPP's Central
  prevailing clock (the fall-back hour appears twice, in chronological order;
  the spring-forward hour is absent). Localized per DIBA with
  ``ambiguous="infer"``.

Ten of SWPP's eleven DIBAs report the leg themselves; SaskPower (``SPC``) is
not an EIA-930 respondent, so its leg exists only as SWPP reports it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import IsoSpec, register

SPP_TZ = "America/Chicago"
SPP_BA = "SWPP"

COUNTERPARTY_FILE = f"{SPP_BA} counterparty interchange hourly.parquet"
OWN_FILE = f"{SPP_BA} interchange hourly.parquet"


def _counterparty_rows(path: Path) -> pd.DataFrame:
    """Counterparty-reported legs on SWPP's export-positive sign."""
    raw = pd.read_parquet(path)
    out = pd.DataFrame(
        {
            "counterparty": raw["ba"].astype(str),
            "reporter": "counterparty",
            "interval_end_utc": pd.to_datetime(raw["utc_time"]).dt.tz_localize("UTC"),
            "export_mw": -raw["mw"].astype(float),
        }
    )
    return out.dropna(subset=["export_mw"])


def _own_rows(path: Path, tz: str) -> pd.DataFrame:
    """SWPP's own legs, local hour-end stamps localized to UTC per DIBA."""
    raw = pd.read_parquet(path)
    frames = []
    for diba, leg in raw.groupby("diba", observed=True, sort=True):
        leg = leg.sort_values("local_time", kind="stable")
        local = pd.DatetimeIndex(pd.to_datetime(leg["local_time"]))
        utc = local.tz_localize(tz, ambiguous="infer").tz_convert("UTC")
        frames.append(
            pd.DataFrame(
                {
                    "counterparty": str(diba),
                    "reporter": "own",
                    "interval_end_utc": utc,
                    "export_mw": leg["mw"].astype(float).to_numpy(),
                }
            )
        )
    return pd.concat(frames, ignore_index=True).dropna(subset=["export_mw"])


def parse(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Both reporting sides of every SWPP leg as one tidy frame."""
    cp_path, own_path = raw_dir / COUNTERPARTY_FILE, raw_dir / OWN_FILE
    if not cp_path.exists():
        raise FileNotFoundError(
            f"{cp_path} missing — fetch it with scripts/data/"
            "fetch_eia930_counterparty_interchange.py --diba SWPP --years ..."
        )
    parts = [_counterparty_rows(cp_path)]
    if own_path.exists():
        parts.append(_own_rows(own_path, spec.tz))
    df = pd.concat(parts, ignore_index=True)
    df = df.drop_duplicates(
        ["counterparty", "reporter", "interval_end_utc"], keep="first"
    )
    return df.assign(iso=spec.iso, ba=spec.ba)


SPEC = register(
    IsoSpec(
        iso="SPP",
        ba=SPP_BA,
        raw_subdir="eia-930-interchange",
        tz=SPP_TZ,
        parse=parse,
        description="EIA-930 SWPP seam legs, own- and counterparty-reported",
    )
)
