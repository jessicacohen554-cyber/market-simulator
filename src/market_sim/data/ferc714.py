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
# ``docs/handoffs/r-soco/FINDING-soco-82-2026-09-27.md`` §2). The series feeds
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
        respondent_id: FERC Form 714 native respondent_id (a key of
            :data:`FERC714_SYSTEM_LAMBDA_FILES`); defaults to Southern Company.
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
        ValueError: the extract repeats an hour or carries another respondent.
    """
    if respondent_id not in FERC714_SYSTEM_LAMBDA_FILES:
        raise KeyError(
            f"no FERC 714 system-lambda extract registered for respondent_id {respondent_id}"
        )
    base = FERC_714_DIR if raw_dir is None else Path(raw_dir)
    path = base / FERC714_SYSTEM_LAMBDA_FILES[respondent_id]
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, usecols=list(SYSTEM_LAMBDA_COLUMNS))
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
    return out.sort_index()
