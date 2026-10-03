"""Measured CAISO DAM ancillary-service regional requirement series (OASIS AS_REQ).

The locational reserve-requirement channel for the CAISO in-LP energy+reserve
co-optimization (:func:`market_sim.config.reserve_config._caiso_design`): when
``ScenarioConfig.caiso_locational_as_families`` is on, the CAISO design adds
zone-masked spin/non-spin reserve families whose hourly requirement is the
MEASURED must-procure-within-region **minimum** CAISO scheduled in the DAM for
each AS region south / north of Path 26 (``AS_SP26`` → model zones
LA_BASIN/SDGE/SP15_rest, ``AS_NP26`` → NP15/ZP26).

The measured regional minimum is a market-design *input* (CLAUDE.md rule #13
admissible: it regenerates for a forward year from the published BPM regional
AS-requirement rules applied to forward states — largest-source, regional
transfer capability — and it responds to changed conditions). The regional
**maximum** is the anti-concentration cap; both are retained by the loader. The
measured AS *prices* are never read here.

Data contract (``data/raw/CAISO-AS/README.md``): windowed OASIS ``AS_REQ`` DAM
CSVs, immutable raw. Key columns ``ANC_REGION`` / ``ANC_TYPE`` (``SR`` spin,
``NR`` non-spin, ``RU``/``RD`` regulation) / ``XML_DATA_ITEM``
(``{SP,NS,RU,RD}_REQ_{MIN,MAX}_MW``) / ``MW`` / ``INTERVALSTARTTIME_GMT``
(one row per region×product×item×hour). Train years 2023-2025 only (rule #22).

Honesty note (``docs/records/caiso/FINDING-caiso71-locational-as-inert-2026-07-10.md``):
the SP26 regional minimum (~318 MW in the evening) is ~15× smaller than SoCal's
own un-postured in-region reserve supply (~4.8 GW), so these families are
**ex-ante inert** on the split topology — the flag ships default-off and is not
part of any keeper. The loader exists so the measured requirement is available
if a materially larger locational constraint (finer LA-Basin pockets, RMR /
local-capacity) is later grounded.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

#: Immutable raw drop (scripts/data/fetch_caiso_oasis.py --datasets asreq).
CAISO_AS_REQ_DIR: Path = RAW_DATA_DIR / "CAISO-AS"

#: One raw drop is ``asreq_ALL_<start>_<end>.csv`` with ``start`` the inclusive
#: and ``end`` the exclusive OPR_DT (Pacific trade date) of the fetch window
#: (``scripts/data/fetch_caiso_oasis.py::fetch_dataset``).
_WINDOW_RE = re.compile(r"asreq_ALL_(\d{8})_(\d{8})\.csv$")

#: Days the filename window is widened on EACH side before a drop is skipped
#: for a requested GMT year. Filenames carry Pacific trade dates while the rows
#: are GMT-stamped: every drop's rows run from ``start`` 08:00Z through ``end``
#: 07:00Z (the fetch stamps ``T08:00-0000``; measured over all 126 drops,
#: 2026-10-03), so a drop named to end on Dec 31 of Y holds Jan-1 Y+1 GMT rows
#: and one starting Jan 1 of Y+1 cannot hold Dec Y rows — one day covers the
#: 8-hour offset three times over.
_WINDOW_SLACK_DAYS: int = 1

#: Columns the loader reads from a drop (the rest are never used).
_USECOLS: tuple[str, ...] = (
    "ANC_REGION",
    "ANC_TYPE",
    "XML_DATA_ITEM",
    "MW",
    "INTERVALSTARTTIME_GMT",
)

#: AS region -> the model zones that must serve its regional minimum. Path 26
#: is the regional boundary (data/raw/CAISO-AS/README.md); the WECC_import node
#: is deliberately excluded (out-of-footprint intertie capacity cannot count
#: toward an in-region must-procure floor).
REGION_ZONES: dict[str, tuple[str, ...]] = {
    "AS_SP26": ("LA_BASIN", "SDGE", "SP15_rest"),
    # FSNO (caiso-224 sub-zonal partition, carved from NP15) is north of
    # Path 26 by construction; listing it here is inert whenever the zone is
    # not in the active topology (zone-name matching finds nothing).
    "AS_NP26": ("NP15", "FSNO", "ZP26"),
}

#: (ANC_TYPE, bound) -> XML_DATA_ITEM. Spin/non-spin only — the upward
#: contingency products the pergen headroom row models (regulation is a
#: separate AGC product with no upward-headroom analogue, matching
#: _caiso_design's existing spin/non-spin scope).
_ITEM: dict[tuple[str, str], str] = {
    ("SR", "min"): "SP_REQ_MIN_MW",
    ("SR", "max"): "SP_REQ_MAX_MW",
    ("NR", "min"): "NS_REQ_MIN_MW",
    ("NR", "max"): "NS_REQ_MAX_MW",
}

#: Canonical product key per ANC_TYPE (the reserve family suffix).
PRODUCT: dict[str, str] = {"SR": "spin", "NR": "nonspin"}

#: Max missing hours filled by nearest-value before the loader hard-errors.
#: Sized just above the one observed artifact (2023's ~8 UTC year-boundary
#: hours); anything larger signals a real coverage hole, not DST/boundary.
_MAX_BOUNDARY_FILL_HOURS: int = 48


def _window_candidates(files: list[Path], year: int) -> list[Path]:
    """Drops whose filename window could hold a row GMT-stamped in ``year``.

    The exact overlap test is ``start <= Dec-31 Y and end >= Jan-1 Y`` (rows
    span ``start`` 08:00Z .. ``end`` 07:00Z); it is widened by
    :data:`_WINDOW_SLACK_DAYS` on each side so the prune can only
    over-include, never drop a contributor. A filename that does not parse is
    kept (the prune never silently discards a drop it cannot date).
    """
    lo = dt.date(year, 1, 1) - dt.timedelta(days=_WINDOW_SLACK_DAYS)
    hi = dt.date(year, 12, 31) + dt.timedelta(days=_WINDOW_SLACK_DAYS)
    keep: list[Path] = []
    for f in files:
        m = _WINDOW_RE.search(f.name)
        if m is None:
            keep.append(f)
            continue
        try:
            start = dt.datetime.strptime(m.group(1), "%Y%m%d").date()
            end = dt.datetime.strptime(m.group(2), "%Y%m%d").date()
        except ValueError:
            keep.append(f)
            continue
        if start <= hi and end >= lo:
            keep.append(f)
    return keep


def _read_matching(path: Path, items: set[str]) -> pd.DataFrame:
    """Read one drop and keep its SP26/NP26 rows for the requested data items."""
    df = pd.read_csv(path, usecols=list(_USECOLS))
    return df[df["ANC_REGION"].isin(REGION_ZONES) & df["XML_DATA_ITEM"].isin(items)]


def load_caiso_as_requirements(
    year: int,
    hours: int,
    bound: str = "min",
    raw_dir: Path | None = None,
) -> dict[str, np.ndarray]:
    """Load the measured hourly CAISO regional AS-requirement series for ``year``.

    Args:
        year: Backcast year (fleet-clock year the solve runs on); train years
            2023-2025 only.
        hours: LP horizon length T; each series is trimmed/validated to exactly
            this many hour-beginning values (GMT-indexed, ascending).
        bound: ``"min"`` (must-procure-within-region floor — the locational
            driver) or ``"max"`` (anti-concentration cap). NOTE: for the
            SP26/NP26 spin/non-spin products CAISO publishes the MAX rows as a
            uniform 0 sentinel (no regional cap), so only ``"min"`` carries a
            usable locational requirement.
        raw_dir: Optional raw directory override (tests); defaults to
            :data:`CAISO_AS_REQ_DIR`.

    Returns:
        ``{"<region_key>_<product>": (hours,) float MW}`` for every
        (region, product) covered, where ``region_key`` is ``sp26`` / ``np26``.
        E.g. ``{"sp26_spin", "sp26_nonspin", "np26_spin", "np26_nonspin"}``.

    Only the drops whose filename window — widened by
    :data:`_WINDOW_SLACK_DAYS` on each side, because the names carry Pacific
    trade dates while the rows are GMT-stamped (``start`` 08:00Z .. ``end``
    07:00Z) — can hold a row of the requested GMT year are read; the rest
    would be discarded by the year filter, so the prune is output-identical
    (parity probe 2026-10-03, every year 2017-2027 incl. the empty-year and
    partial-year paths) and cuts a call from ~4.5 s to ~0.6 s.

    Raises:
        FileNotFoundError: no AS_REQ CSVs present — the
            ``caiso_locational_as_families`` flag hard-errors rather than
            silently solving without the requirement it claims to add.
        ValueError: a present (region, product) series does not cover the full
            horizon, or carries non-finite / negative values.
    """
    if bound not in ("min", "max"):
        raise ValueError(f"bound must be 'min' or 'max', got {bound!r}")
    src = raw_dir if raw_dir is not None else CAISO_AS_REQ_DIR
    files = sorted(src.glob("asreq_ALL_*.csv"))
    if not files:
        raise FileNotFoundError(
            f"caiso_locational_as_families=True but no OASIS AS_REQ CSVs found "
            f"in {src}. Fetch with scripts/data/fetch_caiso_oasis.py --datasets asreq."
        )

    items = {_ITEM[(t, bound)] for t in PRODUCT}
    # Read only the drops whose filename window (widened by _WINDOW_SLACK_DAYS
    # on each side) can hold a row of this GMT year — every other drop's rows
    # would be discarded by the year filter below anyway (parity probe
    # 2026-10-03: identical output for every year with data, 2018-2026).
    candidates = _window_candidates(files, int(year))
    frames = []
    for f in candidates:
        df = _read_matching(f, items)
        if len(df):
            frames.append(df)
    if not frames:
        # Degenerate path (a year outside the drops, or candidates without
        # SP26/NP26 rows): the unpruned loader decided between "no rows in any
        # drop" (FileNotFoundError) and "rows exist, none in this year" (an
        # empty dict) by reading every drop — do the same here so the prune
        # never changes which path is taken.
        skipped = set(candidates)
        for f in files:
            if f in skipped:
                continue
            df = _read_matching(f, items)
            if len(df):
                frames.append(df)
    if not frames:
        raise FileNotFoundError(
            f"AS_REQ CSVs in {src} carry no SP26/NP26 spin/non-spin {bound} rows."
        )
    allrows = pd.concat(frames, ignore_index=True)
    ts = pd.to_datetime(allrows["INTERVALSTARTTIME_GMT"], utc=True)
    allrows = allrows.assign(_hour=ts)
    allrows = allrows[allrows["_hour"].dt.year == int(year)]

    # Reindex onto the full UTC hour range of the calendar year, so the series
    # is aligned to a fixed hour ordinal. A leap year carries 8784 UTC hours;
    # the LP horizon is a fixed ``hours`` (8760), so we trim the tail. The only
    # observed gap is 2023's first ~8 UTC hours (Dec-31 Pacific evening, before
    # the OPR_DT fetch window began) — a bounded year-boundary artifact filled
    # by nearest-value, never silent interior gap-filling.
    full = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h", tz="UTC")
    out: dict[str, np.ndarray] = {}
    for region, grp in allrows.groupby("ANC_REGION", sort=False):
        region_key = "sp26" if region == "AS_SP26" else "np26"
        for anc_type, sub in grp.groupby("ANC_TYPE", sort=False):
            product = PRODUCT[str(anc_type)]
            hourly = sub.groupby("_hour", sort=True)["MW"].mean().reindex(full)
            n_missing = int(hourly.isna().sum())
            if n_missing > _MAX_BOUNDARY_FILL_HOURS:
                raise ValueError(
                    f"{src}: {region}/{anc_type} {bound} missing {n_missing} "
                    f"hours in {year} (> {_MAX_BOUNDARY_FILL_HOURS} tolerated) — "
                    f"not a mere year-boundary artifact."
                )
            hourly = hourly.ffill().bfill()
            series = np.asarray(hourly.to_numpy(dtype=float)[:hours], dtype=float)
            if series.shape[0] < hours:
                raise ValueError(
                    f"{src}: {region}/{anc_type} {bound} yields "
                    f"{series.shape[0]} hours < horizon {hours} for {year}."
                )
            if not np.all(np.isfinite(series)) or np.any(series < 0):
                raise ValueError(
                    f"{src}: {region}/{anc_type} {bound} has non-finite or negative MW."
                )
            out[f"{region_key}_{product}"] = series
    return out
