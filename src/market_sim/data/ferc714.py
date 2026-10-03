"""FERC Form 714 hourly planning-area demand — the measured member substitute.

FERC Form 714 Part III Schedule 2 is each planning area's own hourly load
report, filed annually and independent of EIA-930. It is the measured source
the NWPP pool frame falls back to when a member balancing authority's EIA-930
``Demand (Adjusted)`` series carries a hole longer than the pool is allowed to
bridge by interpolation
(:func:`market_sim.data.eia930.frames._pool_hourly_frame`, lane NWPP-NEXT).

The committed store is ``data/raw/ferc-714/`` (README + SHA256SUMS): one CSV
per respondent, extracted verbatim from Catalyst Cooperative's PUDL
``out_ferc714__hourly_planning_area_demand`` table — ``demand_reported_mwh``
only, never PUDL's ``demand_imputed_pudl_mwh`` (an imputation is a model, not a
measurement, rule 13). Timestamps are PUDL's ``datetime_utc``, which lands on
the EIA-930 ``UTC time`` stamp at lag 0 wherever the two report one basis
(PSEI 2021-2024: median ratio 0.996-0.999, first-difference r 0.956-0.972 at
lag 0 against 0.79-0.83 at ±1 h).

The module also reads FERC Form 714 Part II Schedule 6 — a balancing
authority's own reported hourly **system lambda** — through
:func:`load_ferc714_system_lambda`. That series is REPORTED-ONLY (owner ruling
2026-09-27): a diagnostic reference, never a gate, a scorer input or an LP
input.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from market_sim.config.paths import FERC_714_DIR

# EIA-930 balancing-authority code -> committed FERC 714 respondent extract.
# PSEI = Puget Sound Energy, Inc., FERC 714 respondent_id 129 (csv id 240,
# XBRL C000171, EIA utility code 15500) — PUDL ``core_ferc714__respondent_id``.
FERC714_MEMBER_FILES: dict[str, str] = {
    "PSEI": "psei_hourly_planning_area_demand_2018_2024.csv",
}


@lru_cache(maxsize=8)
def load_ferc714_hourly_demand(ba_code: str) -> pd.Series | None:
    """Return a member's FERC 714 hourly demand (MW) indexed by UTC, or ``None``.

    Args:
        ba_code: EIA-930 balancing-authority code (a key of
            :data:`FERC714_MEMBER_FILES`).

    Returns:
        ``demand_reported_mwh`` as a float Series on a naive-UTC
        ``DatetimeIndex`` (duplicates dropped, sorted), or ``None`` when the
        member has no registered extract or its file is absent.
    """
    name = FERC714_MEMBER_FILES.get(ba_code)
    if name is None:
        return None
    path = FERC_714_DIR / name
    if not path.exists():
        return None
    df = pd.read_csv(path, usecols=["datetime_utc", "demand_reported_mwh"])
    idx = pd.DatetimeIndex(pd.to_datetime(df["datetime_utc"]))
    s = pd.Series(df["demand_reported_mwh"].to_numpy(dtype=float), index=idx)
    return s[~s.index.duplicated()].sort_index()


# ---------------------------------------------------------------------------
# Part II Schedule 6 — hourly SYSTEM LAMBDA (reported-only reference series)
# ---------------------------------------------------------------------------
#
# REPORTED-ONLY (owner ruling 2026-09-27, "Intake, reported-only"; intake lane
# soco-83, source verified by soco-82,
# ``docs/records/soco/r-soco/FINDING-soco-82-2026-09-27.md`` §2). The series feeds
# NO gate, NO scorer and NO LP: it is a balancing authority's own reported
# marginal cost, read by diagnostics only. It is a measured *outcome*, so
# rule 13 [R-MEASURED] forbids pinning it into a solve.

#: FERC Form 714 native respondent_id of Southern Company — the CSV-era
#: ``Respondent IDs.csv`` row "253, Southern Company, 18195" in the PUDL raw
#: FERC-714 archive (Zenodo record 21738524, ``ferc714.zip``). FERC's own id,
#: not PUDL's ``respondent_id_ferc714`` surrogate.
SOCO_FERC714_RESPONDENT_ID: int = 253

#: EIA utility id of Southern Company (the same ``Respondent IDs.csv`` row).
SOCO_EIA_UTILITY_ID: int = 18195

#: FERC eCollection company identifier (CID) of the XBRL-era filer
#: "Southern Company Services, Inc. (as Agent)" — the ``xbrl:identifier`` of
#: every context in its 2021-2025 Form 714 instance documents.
SOCO_FERC714_XBRL_CID: str = "C003610"

#: FERC 714 respondent_id -> committed Part II Sch. 6 system-lambda extract.
FERC714_SYSTEM_LAMBDA_FILES: dict[int, str] = {
    SOCO_FERC714_RESPONDENT_ID: "soco_hourly_system_lambda_2019_2025.csv",
}

#: Columns of a committed system-lambda extract, in file order.
SYSTEM_LAMBDA_COLUMNS: tuple[str, ...] = (
    "report_year",
    "datetime_utc",
    "system_lambda_usd_mwh",
    "respondent_id_ferc714",
    "eia_utility_id",
    "source",
)


# ---------------------------------------------------------------------------
# SOCO's neighbours — Part II Sch. 6 system lambdas (REPORTED-ONLY, soco-97)
# ---------------------------------------------------------------------------
#
# Owner ruling soco-97 option (d), data step 1 of
# ``docs/records/soco/r-soco/FINDING-soco-97-interchange-rule14-phase0-2026-10-01.md``
# §5: intake the hourly system lambdas of the balancing authorities that border
# SOCO, REPORTED-ONLY. A neighbour's lambda is a measured *outcome*; rule 13
# [R-MEASURED] admits it later only as a per-year ``hr_by_year`` anchor in the
# forecast lane, never as a gate, a scorer input or an LP input.


@dataclass(frozen=True)
class Ferc714LambdaRespondent:
    """Identity and reported clock of one FERC Form 714 Part II Sch. 6 filer.

    Attributes:
        ba_code: EIA-930 balancing-authority code the extract is keyed by.
        respondent_id: FERC's native Form 714 respondent id (CSV-era
            ``Respondent IDs.csv``), not PUDL's surrogate id.
        eia_utility_id: EIA utility code from the same ``Respondent IDs.csv`` row.
        xbrl_cid: FERC eCollection CID, the ``xbrl:identifier`` of the filer's
            2021+ Form 714 instance documents.
        xbrl_filer_prefix: Instance-document filename prefix inside the
            ``ferc714-xbrl-<year>.zip`` archives.
        prevailing_zone: IANA zone used when a year's filing pattern reads as a
            prevailing (DST-observing) clock, and to locate the transition days.
        standard_utc_offset_hours: Standard-time offset from UTC (hours, negative
            west of Greenwich), used when a year's filing pattern reads as fixed.
        timezone_codes: Every timezone code the filer reports on Sch. 6 in
            2019-2025 (whitespace-stripped); any other code refuses the build.
    """

    ba_code: str
    respondent_id: int
    eia_utility_id: int
    xbrl_cid: str
    xbrl_filer_prefix: str
    prevailing_zone: str
    standard_utc_offset_hours: int
    timezone_codes: frozenset[str]


_EASTERN = "America/New_York"
_CENTRAL = "America/Chicago"
#: EST = UTC-5, CST = UTC-6 (hours).
_EST_UTC_OFFSET_HOURS = -5
_CST_UTC_OFFSET_HOURS = -6

#: SOCO's FERC 714 Sch. 6 neighbours, keyed by EIA-930 BA code. Ids and EIA codes
#: are the ``Respondent IDs.csv`` rows of the PUDL raw FERC-714 archive (Zenodo
#: record 21738524, ``ferc714.zip``); CIDs are the ``xbrl:identifier`` of each
#: filer's 2021-2025 instance documents in ``ferc714-xbrl-<year>.zip`` (verified
#: by soco-97 against every year's filing). Timezone codes are the set observed
#: in 2019-2025 (CSV ``timezone`` column / XBRL ``ferc:TimeZone`` facts).
#: Dominion Energy South Carolina (SCEG; respondent 250, CID C000241) is NOT
#: registered: it files 0.00 in every hour of every year (README "Neighbours").
SOCO_NEIGHBOR_LAMBDA_RESPONDENTS: dict[str, Ferc714LambdaRespondent] = {
    # "263, Tennessee Valley Authority, 18642".
    "TVA": Ferc714LambdaRespondent(
        "TVA",
        263,
        18642,
        "C004480",
        "Tennessee_Valley_Authority_form714",
        _CENTRAL,
        _CST_UTC_OFFSET_HOURS,
        frozenset({"CST", "CDT"}),
    ),
    # "157, Duke Energy Carolinas, LLC, 5416".
    "DUK": Ferc714LambdaRespondent(
        "DUK",
        157,
        5416,
        "C000290",
        "Duke_Energy_Carolinas,_LLC_form714",
        _EASTERN,
        _EST_UTC_OFFSET_HOURS,
        frozenset({"EST", "EDT", "EPT"}),
    ),
    # "233, Progress Energy (Carolina Power & Light Company), 3046" = Duke Energy Progress.
    "CPLE": Ferc714LambdaRespondent(
        "CPLE",
        233,
        3046,
        "C000135",
        "Duke_Energy_Progress,_LLC_form714",
        _EASTERN,
        _EST_UTC_OFFSET_HOURS,
        frozenset({"EST", "EDT", "EPT"}),
    ),
    # "234, Progress Energy (Florida Power Corp.), 6455" = Duke Energy Florida.
    "FPC": Ferc714LambdaRespondent(
        "FPC",
        234,
        6455,
        "C000136",
        "Duke_Energy_Florida,_LLC_form714",
        _EASTERN,
        _EST_UTC_OFFSET_HOURS,
        frozenset({"EST", "EDT", "EST/EDT", "EDT/EST"}),
    ),
    # "171, Florida Power & Light Company, 6452".
    "FPL": Ferc714LambdaRespondent(
        "FPL",
        171,
        6452,
        "C001030",
        "Florida_Power_&_Light_Company_form714",
        _EASTERN,
        _EST_UTC_OFFSET_HOURS,
        frozenset({"EST", "EDT"}),
    ),
    # "251, South Carolina Public Service Authority, 17543" = Santee Cooper.
    "SC": Ferc714LambdaRespondent(
        "SC",
        251,
        17543,
        "C011420",
        "Santee_Cooper_form714",
        _EASTERN,
        _EST_UTC_OFFSET_HOURS,
        frozenset({"EST", "EDT"}),
    ),
    # "140, City of Tallahassee, 18445". Its 2021 filing codes every day "UTC";
    # that code is measured NOT literal (README "Neighbours", clock section).
    "TAL": Ferc714LambdaRespondent(
        "TAL",
        140,
        18445,
        "C011474",
        "City_of_Tallahassee_Utilities_form714",
        _EASTERN,
        _EST_UTC_OFFSET_HOURS,
        frozenset({"EST", "EDT", "UTC"}),
    ),
    # "186, JEA, 9617".
    "JEA": Ferc714LambdaRespondent(
        "JEA",
        186,
        9617,
        "C011421",
        "JEA_form714",
        _EASTERN,
        _EST_UTC_OFFSET_HOURS,
        frozenset({"EST", "EDT"}),
    ),
    # "321, MISO, 56669". MISO files Sch. 6 in BOTH eras (CSV 2009-2020, XBRL 2021+).
    "MISO": Ferc714LambdaRespondent(
        "MISO",
        321,
        56669,
        "C001344",
        "Midcontinent_Independent_System_Operator,_Inc._form714",
        _EASTERN,
        _EST_UTC_OFFSET_HOURS,
        frozenset({"EST"}),
    ),
}

#: Committed long-form extract holding every registered neighbour's lambda.
FERC714_NEIGHBOR_SYSTEM_LAMBDA_FILE: str = (
    "soco_neighbor_hourly_system_lambda_2019_2025.csv"
)

#: Columns of the neighbour extract, in file order (the Southern columns plus
#: the EIA-930 ``ba_code``).
NEIGHBOR_SYSTEM_LAMBDA_COLUMNS: tuple[str, ...] = ("ba_code", *SYSTEM_LAMBDA_COLUMNS)

#: Process-local memo of :func:`load_ferc714_system_lambda` results keyed by
#: ``(resolved path, mtime_ns, size, respondent_id)``; values are never handed
#: out directly (the loader returns a copy).
_SYSTEM_LAMBDA_CACHE: dict[tuple[str, int, int, int], pd.DataFrame] = {}


def load_ferc714_system_lambda(
    respondent_id: int = SOCO_FERC714_RESPONDENT_ID,
    raw_dir: Path | None = None,
) -> pd.DataFrame:
    """Return a respondent's reported hourly system lambda on an hourly UTC index.

    The committed extract (``data/raw/ferc-714/``, see its README) carries the
    respondent's FERC Form 714 Part II Schedule 6 values exactly as filed
    (CSV era 2019-2020, XBRL era 2021+), with the reported clock already
    converted to UTC when the file was built
    (``scripts/data/fetch_ferc714_system_lambda.py``). REPORTED-ONLY: never an
    LP input, never a gate (owner ruling 2026-09-27).

    Args:
        respondent_id: FERC Form 714 native respondent_id — a key of
            :data:`FERC714_SYSTEM_LAMBDA_FILES` (a single-respondent extract;
            the default, Southern Company) or the ``respondent_id`` of a
            :data:`SOCO_NEIGHBOR_LAMBDA_RESPONDENTS` entry, whose rows are read
            from the long-form :data:`FERC714_NEIGHBOR_SYSTEM_LAMBDA_FILE`.
        raw_dir: Directory holding the extract; defaults to
            :data:`market_sim.config.paths.FERC_714_DIR` (tests pass a tmp dir).

    Returns:
        DataFrame indexed by a naive-UTC, hour-beginning ``DatetimeIndex``
        named ``datetime_utc`` (sorted, unique), with columns
        ``system_lambda_usd_mwh`` (float, $/MWh), ``report_year`` (int64) and
        ``source`` (``"csv"`` or ``"xbrl"``).

    Raises:
        KeyError: ``respondent_id`` has no registered extract.
        FileNotFoundError: the registered extract is absent from ``raw_dir``.
        ValueError: the extract repeats an hour, carries another respondent
            (single-respondent file) or holds no row for a registered
            neighbour (long-form file).
    """
    neighbor_ids = {r.respondent_id for r in SOCO_NEIGHBOR_LAMBDA_RESPONDENTS.values()}
    if respondent_id in FERC714_SYSTEM_LAMBDA_FILES:
        name = FERC714_SYSTEM_LAMBDA_FILES[respondent_id]
    elif respondent_id in neighbor_ids:
        name = FERC714_NEIGHBOR_SYSTEM_LAMBDA_FILE
    else:
        raise KeyError(
            f"no FERC 714 system-lambda extract registered for respondent_id {respondent_id}"
        )
    base = FERC_714_DIR if raw_dir is None else Path(raw_dir)
    path = base / name
    if not path.exists():
        raise FileNotFoundError(path)
    # Same bytes in, same frame out: the parsed extract is memoised on the
    # file's identity (path, mtime, size) and respondent, and a fresh copy is
    # handed back, so a caller that reads every neighbour never re-parses the
    # one long-form CSV. A rewritten file (new mtime/size) is re-read.
    stat = path.stat()
    key = (str(path.resolve()), stat.st_mtime_ns, stat.st_size, int(respondent_id))
    cached = _SYSTEM_LAMBDA_CACHE.get(key)
    if cached is not None:
        return cached.copy()
    df = pd.read_csv(path, usecols=list(SYSTEM_LAMBDA_COLUMNS))
    if respondent_id in neighbor_ids:
        df = df[df["respondent_id_ferc714"] == respondent_id]
        if df.empty:
            raise ValueError(f"{path.name}: no rows for respondent_id {respondent_id}")
    foreign = set(df["respondent_id_ferc714"].unique()) - {respondent_id}
    if foreign:
        raise ValueError(f"{path.name}: foreign respondent ids {sorted(foreign)}")
    idx = pd.DatetimeIndex(pd.to_datetime(df["datetime_utc"]), name="datetime_utc")
    if idx.has_duplicates:
        raise ValueError(f"{path.name}: duplicate datetime_utc stamps")
    out = pd.DataFrame(
        {
            "system_lambda_usd_mwh": df["system_lambda_usd_mwh"].to_numpy(dtype=float),
            "report_year": df["report_year"].to_numpy(dtype="int64"),
            "source": df["source"].astype(str).to_numpy(),
        },
        index=idx,
    )
    out = out.sort_index()
    _SYSTEM_LAMBDA_CACHE[key] = out.copy()
    return out
