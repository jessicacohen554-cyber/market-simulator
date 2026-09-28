"""Tests for the FERC Form 714 Part II Sch. 6 system-lambda intake (lane soco-83).

Covers the loader :func:`market_sim.data.ferc714.load_ferc714_system_lambda`
on tmp-dir fixtures (trivial one-row case first, then a small multi-hour
file), and the rebuild script's two parsers
(``scripts/data/fetch_ferc714_system_lambda.py``) on synthetic CSV-era and
XBRL-era zips — including the fixed-UTC-6, hour-ending -> hour-beginning clock
conversion and the guards that refuse a clock the reading cannot support.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd
import pytest

from market_sim.data.ferc714 import (
    FERC714_SYSTEM_LAMBDA_FILES,
    SOCO_EIA_UTILITY_ID,
    SOCO_FERC714_RESPONDENT_ID,
    SOCO_FERC714_XBRL_CID,
    SYSTEM_LAMBDA_COLUMNS,
    load_ferc714_system_lambda,
)
from scripts.data import fetch_ferc714_system_lambda as fetch

SOCO_FILE = FERC714_SYSTEM_LAMBDA_FILES[SOCO_FERC714_RESPONDENT_ID]


def _write_extract(tmp_path: Path, rows: list[tuple]) -> Path:
    """Write a committed-shape extract with ``rows`` of (year, utc, lambda, source)."""
    df = pd.DataFrame(
        [
            (y, ts, lam, SOCO_FERC714_RESPONDENT_ID, SOCO_EIA_UTILITY_ID, src)
            for y, ts, lam, src in rows
        ],
        columns=list(SYSTEM_LAMBDA_COLUMNS),
    )
    path = tmp_path / SOCO_FILE
    df.to_csv(path, index=False)
    return path


# --------------------------------------------------------------------- loader


def test_loader_trivial_one_row(tmp_path):
    _write_extract(tmp_path, [(2019, "2019-01-01 06:00:00", 18.63, "csv")])
    out = load_ferc714_system_lambda(raw_dir=tmp_path)
    assert list(out.columns) == ["system_lambda_usd_mwh", "report_year", "source"]
    assert out.index.name == "datetime_utc"
    assert out.index[0] == pd.Timestamp("2019-01-01 06:00:00")
    assert out.index.tz is None
    assert out["system_lambda_usd_mwh"].iloc[0] == pytest.approx(18.63)
    assert out["report_year"].iloc[0] == 2019
    assert out["source"].iloc[0] == "csv"


def test_loader_sorts_and_keeps_both_eras(tmp_path):
    _write_extract(
        tmp_path,
        [
            (2021, "2021-01-01 06:00:00", 16.43, "xbrl"),
            (2020, "2020-12-31 05:00:00", 20.0, "csv"),
            (2020, "2020-12-31 04:00:00", 19.0, "csv"),
        ],
    )
    out = load_ferc714_system_lambda(raw_dir=tmp_path)
    assert out.index.is_monotonic_increasing
    assert list(out["source"]) == ["csv", "csv", "xbrl"]
    assert out["system_lambda_usd_mwh"].tolist() == [19.0, 20.0, 16.43]


def test_loader_unregistered_respondent_raises(tmp_path):
    with pytest.raises(KeyError):
        load_ferc714_system_lambda(respondent_id=999_999, raw_dir=tmp_path)


def test_loader_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_ferc714_system_lambda(raw_dir=tmp_path)


def test_loader_rejects_duplicate_hours(tmp_path):
    _write_extract(
        tmp_path,
        [
            (2019, "2019-01-01 06:00:00", 1.0, "csv"),
            (2019, "2019-01-01 06:00:00", 2.0, "csv"),
        ],
    )
    with pytest.raises(ValueError, match="duplicate"):
        load_ferc714_system_lambda(raw_dir=tmp_path)


def test_loader_rejects_foreign_respondent(tmp_path):
    path = _write_extract(tmp_path, [(2019, "2019-01-01 06:00:00", 1.0, "csv")])
    df = pd.read_csv(path)
    df["respondent_id_ferc714"] = SOCO_FERC714_RESPONDENT_ID + 1
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match="foreign"):
        load_ferc714_system_lambda(raw_dir=tmp_path)


def test_committed_extract_if_present():
    """The committed file loads, is hourly and unique, and matches soco-82's 2019/2020 stats."""
    try:
        out = load_ferc714_system_lambda()
    except FileNotFoundError:
        pytest.skip("committed extract not hydrated")
    assert out.index.is_unique
    assert (out.index.to_series().diff().dropna() == pd.Timedelta(hours=1)).all()
    stats = out.groupby("report_year")["system_lambda_usd_mwh"].agg(["mean", "median"])
    # soco-82 FINDING §2: 2019 $25.72 / $26.27, 2020 $20.90 / $18.75.
    assert stats.loc[2019, "mean"] == pytest.approx(25.72, abs=0.005)
    assert stats.loc[2019, "median"] == pytest.approx(26.265, abs=0.005)
    assert stats.loc[2020, "mean"] == pytest.approx(20.90, abs=0.005)
    assert stats.loc[2020, "median"] == pytest.approx(18.75, abs=0.005)


# ------------------------------------------------------------ CSV-era parser


def _csv_zip(
    tmp_path: Path, days: list[tuple[str, list[float], float]], tz: str = "CPT"
) -> Path:
    """Build a ``ferc714.zip`` holding the Sch. 6 CSV with Southern day rows."""
    hours = [f"hour{h:02d}" for h in range(1, 26)]
    rows = []
    for date, vals, h25 in days:
        rows.append(
            {
                "respondent_id": SOCO_FERC714_RESPONDENT_ID,
                "report_yr": int(date.split("/")[-1]),
                "report_prd": 12,
                "spplmnt_num": 0,
                "row_num": 100,
                "lambda_date": f"{date} 0:00:00",
                "timezone": tz,
                **dict(zip(hours, [*vals, h25])),
            }
        )
    # A foreign respondent the parser must ignore.
    rows.append({**rows[0], "respondent_id": 1})
    path = tmp_path / "ferc714.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(fetch.CSV_MEMBER, pd.DataFrame(rows).to_csv(index=False))
    return path


def test_csv_parser_clock_trivial_day(tmp_path):
    vals = [float(h) for h in range(1, 25)]
    z = _csv_zip(tmp_path, [("1/1/2019", vals, 0.0)])
    long = fetch.parse_csv_era(z, [2019])
    assert len(long) == 24
    long = long.sort_values("local_hour_ending")
    utc = fetch.local_to_utc(long["local_hour_ending"]).reset_index(drop=True)
    # hour01 (00:00-01:00 CST) begins at 06:00 UTC; hour24 begins at 05:00 UTC next day.
    assert utc.iloc[0] == pd.Timestamp("2019-01-01 06:00:00")
    assert utc.iloc[-1] == pd.Timestamp("2019-01-02 05:00:00")
    assert long["value"].tolist() == vals


def test_csv_parser_summer_day_is_fixed_offset(tmp_path):
    """No DST shift: a July hour01 also begins at 06:00 UTC."""
    z = _csv_zip(tmp_path, [("7/1/2019", [1.0] * 24, 0.0)])
    long = fetch.parse_csv_era(z, [2019])
    first = fetch.local_to_utc(long["local_hour_ending"]).min()
    assert first == pd.Timestamp("2019-07-01 06:00:00")


def test_csv_parser_refuses_hour25(tmp_path):
    z = _csv_zip(tmp_path, [("11/3/2019", [1.0] * 24, 5.0)])
    with pytest.raises(SystemExit, match="hour25"):
        fetch.parse_csv_era(z, [2019])


def test_csv_parser_refuses_unknown_timezone(tmp_path):
    z = _csv_zip(tmp_path, [("1/1/2019", [1.0] * 24, 0.0)], tz="EST")
    with pytest.raises(SystemExit, match="timezone"):
        fetch.parse_csv_era(z, [2019])


# ----------------------------------------------------------- XBRL-era parser


def _xbrl_doc(
    year: int,
    values: dict[str, float],
    cid: str = SOCO_FERC714_XBRL_CID,
    tz: str = "CST",
) -> str:
    """A minimal Form 714 instance with SystemLambda facts on instant contexts."""
    ctx, facts = [], []
    for inst, v in values.items():
        cid_ = "Asof" + inst.replace("-", "").replace(":", "")
        ctx.append(
            f'<xbrl:context id="{cid_}"><xbrl:entity><xbrl:identifier scheme="http://www.ferc.gov/CID">{cid}'
            f"</xbrl:identifier></xbrl:entity><xbrl:period><xbrl:instant>{inst}</xbrl:instant>"
            f"</xbrl:period></xbrl:context>"
        )
        facts.append(
            f'<ferc:SystemLambda contextRef="{cid_}" unitRef="USDPerMWh" decimals="INF">{v}</ferc:SystemLambda>'
        )
    day = f"From{year}-01-01To{year}-01-01"
    ctx.append(
        f'<xbrl:context id="{day}"><xbrl:entity><xbrl:identifier scheme="http://www.ferc.gov/CID">{cid}'
        f"</xbrl:identifier></xbrl:entity><xbrl:period><xbrl:startDate>{year}-01-01</xbrl:startDate>"
        f"<xbrl:endDate>{year}-01-01</xbrl:endDate></xbrl:period></xbrl:context>"
    )
    facts.append(f'<ferc:TimeZone contextRef="{day}">{tz}</ferc:TimeZone>')
    return (
        '<?xml version="1.0" encoding="us-ascii"?>'
        '<xbrl:xbrl xmlns:xbrl="http://www.xbrl.org/2003/instance" xmlns:ferc="http://ferc.gov/form/2022-01-01/ferc">'
        + "".join(ctx)
        + "".join(facts)
        + "</xbrl:xbrl>"
    )


def _xbrl_zip(tmp_path: Path, year: int, docs: dict[str, str]) -> Path:
    path = tmp_path / f"ferc714-xbrl-{year}.zip"
    with zipfile.ZipFile(path, "w") as z:
        for name, doc in docs.items():
            z.writestr(name, doc)
    return path


def _span(year: int) -> dict[str, float]:
    """First and last hour-ending instants of a report year."""
    return {f"{year}-01-01T01:00:00": 16.43, f"{year + 1}-01-01T00:00:00": 20.5}


def test_xbrl_parser_trivial(tmp_path):
    name = f"{fetch.XBRL_FILER_PREFIX}_Q4_100.xbrl"
    z = _xbrl_zip(
        tmp_path,
        2025,
        {name: _xbrl_doc(2025, _span(2025)), "Other_Co_form714_Q4_1.xbrl": "<x/>"},
    )
    df, note = fetch.parse_xbrl_year(z, 2025)
    assert note == name
    df = df.sort_values("local_hour_ending")
    utc = fetch.local_to_utc(df["local_hour_ending"]).tolist()
    assert utc == [
        pd.Timestamp("2025-01-01 06:00:00"),
        pd.Timestamp("2026-01-01 05:00:00"),
    ]
    assert df["value"].tolist() == [16.43, 20.5]


def test_xbrl_parser_uses_latest_resubmission(tmp_path):
    old = f"{fetch.XBRL_FILER_PREFIX}_Q4_100.xbrl"
    new = f"{fetch.XBRL_FILER_PREFIX}_Q4_200.xbrl"
    changed = {**_span(2023), "2023-01-01T01:00:00": 99.0}
    z = _xbrl_zip(
        tmp_path,
        2023,
        {old: _xbrl_doc(2023, _span(2023)), new: _xbrl_doc(2023, changed)},
    )
    df, note = fetch.parse_xbrl_year(z, 2023)
    assert note.startswith(new) and "DIFFERS" in note
    assert 99.0 in df["value"].tolist()


def test_xbrl_parser_refuses_wrong_cid(tmp_path):
    name = f"{fetch.XBRL_FILER_PREFIX}_Q4_100.xbrl"
    z = _xbrl_zip(tmp_path, 2021, {name: _xbrl_doc(2021, _span(2021), cid="C999999")})
    with pytest.raises(SystemExit, match="CID"):
        fetch.parse_xbrl_year(z, 2021)


def test_xbrl_parser_absent_filer(tmp_path):
    z = _xbrl_zip(tmp_path, 2021, {"Other_Co_form714_Q4_1.xbrl": "<x/>"})
    df, note = fetch.parse_xbrl_year(z, 2021)
    assert df.empty and note == "absent"
