"""Balancing-authority membership rules shared by the LP fleet and the benchmark.

Two registries in :mod:`market_sim.config.constants` decide which plants belong
to a modelled region beyond its plain EIA-860 ``Balancing Authority Code``
filter. Both are read HERE, and nowhere else, so the LP fleet, the EIA-923
benchmark and the must-run injection stay on the one boundary EIA-930 measures
the region's load on (rule 19 [R-ONE-MECH]; lane R-SOCO-B, 2026-09-25):

* :data:`~market_sim.config.constants.ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE` —
  plants the CURRENT EIA-860 plant file codes to another BA leave the region
  (:func:`current_ba_recoded_plants`, :func:`drop_current_ba_recoded_rows`).
  SOCO: the former Gulf Power plants, which EIA-930's SOCO series has excluded
  in every year although vintages 2019-2023 code them SOCO.
* :data:`~market_sim.config.constants.ISO_BA_JOINS` — a BA that joined the
  region part-way through a backcast year (:func:`joining_ba_codes`,
  :func:`ba_join_first_month`). SOCO: PowerSouth (``AEC``), 2021-09-01.
* :data:`~market_sim.config.constants.ISO_BA_EXITS` — the twin for an EXIT: it
  DATES the recode partition, so a recoded plant whose destination BA is
  registered stays a member until the registered hour
  (:func:`exit_member_plants`, :func:`ba_exit_first_outside_row`,
  :func:`ba_exit_month_share`). SOCO: the former Gulf Power plants, to FPL at
  hour-ending UTC 2022-07-13 12:00 (lane R-SOCO-B2, owner ruling (C)).

* :data:`~market_sim.config.constants.ISO_PLANT_ENTRIES` — a single PLANT
  that entered the region at a dated hour, with no BA code to key on
  (:func:`plant_entry_stamps`, :func:`plant_entry_non_members`,
  :func:`plant_entry_first_inside_row`, :func:`plant_entry_month_share`,
  :func:`zero_pre_entry_campd`). ERCOT: Frontera 55098, 2023-04-13 (lane
  R-ERCOT-12).

Every function is a pure read of committed EIA-860 parquet keyed on its
arguments (no ``ScenarioConfig``, no process global), and every one returns an
empty result for a region neither registry names, so every other region is
byte-identical.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    ISO_BA_EXITS,
    ISO_BA_JOINS,
    ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE,
    ISO_PLANT_ENTRIES,
    ISO_PLANT_EXITS,
)

#: Returned by :func:`ba_join_first_month` for a plant whose BA has not yet
#: joined in the year asked about: no month of that year is inside the region.
NOT_A_MEMBER_THIS_YEAR: int = 13


def drops_current_ba_recode(iso: str) -> bool:
    """Return whether ``iso`` drops plants the current EIA-860 recodes elsewhere."""
    return bool(ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE.get(iso.upper(), False))


@lru_cache(maxsize=8)
def current_ba_recode_map(iso: str) -> dict[int, str]:
    """``{plant: current other BA code}`` for the plants recoded out of ``iso``.

    The selection :func:`current_ba_recoded_plants` returns (see there), keyed
    to the BA code the CURRENT EIA-860 plant file gives each plant (its first
    other-BA row). :data:`ISO_BA_EXITS` reads the code to date the exit.
    """
    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.zone_assignment import _iso_ba_codes

    path = EIA_860_DIR / "eia860_plant.parquet"
    codes = set(_iso_ba_codes(iso))
    if not codes or not path.exists():
        return {}
    df = pd.read_parquet(path, columns=["Plant Code", "Balancing Authority Code"])
    ba = df["Balancing Authority Code"].astype(str).str.strip()
    other = df[(ba != "") & ~ba.isin(["nan", "None"]) & ~ba.isin(codes)]
    ours = set(
        pd.to_numeric(df[ba.isin(codes)]["Plant Code"], errors="coerce")
        .dropna()
        .astype(int)
    )
    plants = pd.to_numeric(other["Plant Code"], errors="coerce")
    out: dict[int, str] = {}
    for p, b in zip(plants, ba[other.index]):
        if pd.notna(p) and int(p) not in ours:
            out.setdefault(int(p), str(b))
    return out


def current_ba_recoded_plants(iso: str) -> frozenset[int]:
    """Plants the CURRENT EIA-860 plant file codes to a BA other than ``iso``'s.

    Read only for an ISO in ``ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE`` (see that
    constant for the measurement). A plant absent from the current file, or
    carrying no BA code there, is NOT returned: only an explicit recode to
    another balancing authority removes a plant from ``iso``'s membership. A
    plant with rows coded to BOTH this ISO and another stays in.

    Moved here from ``scripts/run_calibration_full.py`` (lane R-SOCO-B) so the
    fleet loaders and the benchmark read the same function; since lane
    R-SOCO-B2 it is the key set of :func:`current_ba_recode_map` (same
    selection).
    """
    return frozenset(current_ba_recode_map(iso.upper()))


def ba_exit_stamps(iso: str) -> dict[int, pd.Timestamp]:
    """``{plant: first hour OUTSIDE iso}`` for recoded plants with a dated exit.

    A recoded plant whose current BA is registered in ``ISO_BA_EXITS[iso]``
    carries that BA's stamp (the region's EIA-930 extract's own hour-ending
    ``UTC time`` of the first row outside the region). Empty for any region
    ``ISO_BA_EXITS`` does not name, or that does not drop recodes.
    """
    exits = ISO_BA_EXITS.get(iso.upper(), {})
    if not exits or not drops_current_ba_recode(iso):
        return {}
    stamps = {ba: pd.Timestamp(t) for ba, t in exits.items()}
    out: dict[int, pd.Timestamp] = {}
    for p, b in current_ba_recode_map(iso.upper()).items():
        if b in stamps and p in _coded_to_region_by(iso.upper(), stamps[b].year):
            out[p] = stamps[b]
    return out


@lru_cache(maxsize=16)
def _coded_to_region_by(iso: str, last_year: int) -> frozenset[int]:
    """Plants some EIA-860 vintage up to ``last_year`` codes to ``iso``'s BAs.

    Bounds :func:`ba_exit_stamps` to plants that were actually the region's:
    the current recode map also names every plant that was ALWAYS another BA's
    (e.g. FPL's own fleet), which must never be admitted.
    """
    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.zone_assignment import _iso_ba_codes

    codes = set(_iso_ba_codes(iso))
    found: set[int] = set()
    for d in sorted(EIA_860_DIR.glob("vintage_*")):
        try:
            vy = int(d.name.split("_", 1)[1])
        except ValueError:
            continue
        f = d / "eia860_plant.parquet"
        if vy > int(last_year) or not f.exists():
            continue
        df = pd.read_parquet(f, columns=["Plant Code", "Balancing Authority Code"])
        ba = df["Balancing Authority Code"].astype(str).str.strip()
        found |= set(
            pd.to_numeric(df.loc[ba.isin(codes), "Plant Code"], errors="coerce")
            .dropna()
            .astype(int)
        )
    return frozenset(found)


def exit_member_plants(iso: str, year: int | None) -> frozenset[int]:
    """Recoded plants that are still ``iso`` members for part or all of ``year``.

    A plant is a member in every year up to and including its exit stamp's
    year; the exit year's later hours are masked by
    :func:`ba_exit_first_outside_row` (fleet) and :func:`ba_exit_month_share`
    (benchmark). ``year=None`` (no solve year known) returns none, so the
    undated recode drop applies exactly as before.
    """
    if year is None:
        return frozenset()
    return frozenset(p for p, s in ba_exit_stamps(iso).items() if int(year) <= s.year)


def _region_clock(iso: str, year: int) -> pd.DataFrame | None:
    """The region's EIA-930 local-year frame (the LP's own hour rows)."""
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    frame = _eia_hourly_frame_filled(iso.upper(), int(year))
    if frame is None or "UTC time" not in frame.columns:
        return None
    return frame.reset_index(drop=True)


@lru_cache(maxsize=32)
def ba_exit_first_outside_row(iso: str, year: int) -> dict[int, int]:
    """``{plant: first LP row outside iso}`` for plants exiting IN ``year``.

    The row index is the count of the region's local-year frame rows whose
    hour-ending ``UTC time`` precedes the plant's exit stamp — the same rows
    the LP dispatches. Plants whose stamp falls in a later year are members all
    year and are omitted; so is every plant of an unregistered region.
    """
    live = {p: s for p, s in ba_exit_stamps(iso).items() if s.year == int(year)}
    if not live:
        return {}
    frame = _region_clock(iso, year)
    if frame is None:
        return {}
    utc = pd.to_datetime(frame["UTC time"]).to_numpy()
    return {p: int((utc < s.to_datetime64()).sum()) for p, s in live.items()}


@lru_cache(maxsize=32)
def ba_exit_month_share(iso: str, year: int) -> dict[int, tuple[int, float]]:
    """``{plant: (split month, in-region share)}`` for plants exiting IN ``year``.

    The monthly EIA-923 benchmark keeps each exiting plant's months before the
    split month, drops the months after it, and scales the split month by the
    plant's own measured share of that month's CAMPD gross load before the
    stamp (owner ruling (C), hour grain). A plant CAMPD does not carry (or with
    no gross load that month) takes the share of the month's LP rows before
    the stamp. CAMPD hours are local STANDARD time; they are put on UTC with
    the region clock's own standard offset (the largest ``UTC time - Local
    time`` of its frame), which is exact for plants on the region's clock
    (SOCO's Gulf plants sit in the Central-time Florida panhandle).
    """
    live = {p: s for p, s in ba_exit_stamps(iso).items() if s.year == int(year)}
    if not live:
        return {}
    frame = _region_clock(iso, year)
    if frame is None:
        return {}
    utc = pd.to_datetime(frame["UTC time"])
    local = pd.to_datetime(frame["Local time"])
    std_offset = (utc - local).max()
    # EIA-930 stamps are hour-ending: a row belongs to the local month one
    # hour before its local stamp.
    row_month = (local - pd.Timedelta(hours=1)).dt.month.to_numpy()
    out: dict[int, tuple[int, float]] = {}
    cems = _exit_plant_cems(iso, int(year), tuple(sorted(live)))
    for p, s in live.items():
        at = utc >= s
        month = int(row_month[at.to_numpy()][0]) if at.any() else 12
        in_month = row_month == month
        share = float((~at.to_numpy() & in_month).sum() / max(in_month.sum(), 1))
        c = cems.get(p) if cems is not None else None
        if c is not None:
            he = c.index + pd.Timedelta(hours=1) + std_offset
            m = c.index.month == month
            tot = float(c[m].sum())
            if tot > 0:
                share = float(c[m & (he < s)].sum()) / tot
        out[p] = (month, share)
    return out


def _exit_plant_cems(
    iso: str, year: int, plants: tuple[int, ...]
) -> dict[int, pd.Series] | None:
    """Hourly CAMPD gross load (local standard, hour-beginning) per exiting plant.

    Reads only the states the plants sit in (their EIA-860 plant-file state).
    Returns ``None`` when nothing is on disk.
    """
    from market_sim.config.paths import CAMPD_UNIT_LEVEL_DIR, EIA_860_DIR

    pf = EIA_860_DIR / "eia860_plant.parquet"
    if not pf.exists():
        return None
    meta = pd.read_parquet(pf, columns=["Plant Code", "State"])
    code = pd.to_numeric(meta["Plant Code"], errors="coerce")
    states = sorted(set(meta.loc[code.isin(plants), "State"].astype(str)))
    frames = []
    for st in states:
        f = CAMPD_UNIT_LEVEL_DIR / f"{st}_{int(year)}.parquet"
        if f.exists():
            c = pd.read_parquet(f, columns=["facilityId", "date", "hour", "grossLoad"])
            c["facilityId"] = pd.to_numeric(c["facilityId"], errors="coerce")
            frames.append(c[c["facilityId"].isin(plants)])
    if not frames:
        return None
    c = pd.concat(frames)
    c["t"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
    g = c.groupby(["facilityId", "t"])["grossLoad"].sum()
    return {
        int(p): g.xs(p, level=0).fillna(0.0)
        for p in g.index.get_level_values(0).unique()
    }


def drop_current_ba_recoded_rows(
    df: pd.DataFrame, iso: str, plant_col: str = "plant_id", year: int | None = None
) -> pd.DataFrame:
    """Drop fleet rows whose plant the current EIA-860 recodes out of ``iso``.

    The LP-fleet half of ``ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE``: applied
    right after each fleet loader's BA filter (operable, within-window retiree,
    mothball re-carry). Returns ``df`` itself — the same object — when ``iso``
    is not registered, when the frame is empty or lacks ``plant_col``, or when
    no row is dropped, so every other region and every clean year is
    byte-identical.

    ``year`` DATES the drop (``ISO_BA_EXITS``, lane R-SOCO-B2): a recoded plant
    still a member for part of ``year`` (:func:`exit_member_plants`) is kept,
    and the exit year's later hours are masked in ``fleet.arrays``.
    """
    if df.empty or plant_col not in df.columns or not drops_current_ba_recode(iso):
        return df
    recoded = current_ba_recoded_plants(iso.upper()) - exit_member_plants(iso, year)
    if not recoded:
        return df
    plant = pd.to_numeric(df[plant_col], errors="coerce")
    drop = plant.isin(recoded).to_numpy(dtype=bool)
    if not drop.any():
        return df
    return df[~drop]


def joining_ba_codes(iso: str, year: int | None) -> tuple[str, ...]:
    """Return the BAs that have joined ``iso`` by ``year`` (join year included).

    A fleet loader admits rows coded to these BAs in addition to ``iso``'s own
    codes. ``year=None`` (no solve year known) admits none. In a year after the
    join the vintages already code the plants to ``iso``, so the extra codes
    select nothing there; only the join year's vintage carries them.
    """
    if year is None:
        return ()
    joins = ISO_BA_JOINS.get(iso.upper(), {})
    return tuple(ba for ba, (jy, _jm) in joins.items() if int(year) >= jy)


@lru_cache(maxsize=64)
def ba_join_first_month(iso: str, year: int) -> dict[int, int]:
    """Return ``{plant_code: first calendar month inside iso}`` for ``year``.

    Covers only plants coded to a registered JOINING BA
    (``ISO_BA_JOINS[iso]``) in the EIA-860 vintage that covers ``year``
    (``vintage_<year>/eia860_plant.parquet``, holding last to the canonical
    file): the month is the join month in the join year, and
    :data:`NOT_A_MEMBER_THIS_YEAR` in an earlier year. A year after the join
    returns ``{}`` (the vintages code the plants to ``iso`` and they are
    members all year). Empty for any unregistered region.
    """
    joins = ISO_BA_JOINS.get(iso.upper(), {})
    live = {ba: jm for ba, (jy, jm) in joins.items() if int(year) == jy}
    live.update(
        {ba: NOT_A_MEMBER_THIS_YEAR for ba, (jy, _jm) in joins.items() if year < jy}
    )
    if not live:
        return {}
    from market_sim.config.paths import EIA_860_DIR

    path = EIA_860_DIR / f"vintage_{int(year)}" / "eia860_plant.parquet"
    if not path.exists():
        path = EIA_860_DIR / "eia860_plant.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path, columns=["Plant Code", "Balancing Authority Code"])
    ba = df["Balancing Authority Code"].astype(str).str.strip()
    plant = pd.to_numeric(df["Plant Code"], errors="coerce")
    out: dict[int, int] = {}
    for code, b in zip(plant, ba):
        if pd.notna(code) and b in live:
            out[int(code)] = int(live[b])
    return out


# --- plant-grain ENTRY (constants.ISO_PLANT_ENTRIES, lane R-ERCOT-12) --------


def _entry_clock(iso: str, year: int) -> pd.DataFrame:
    """The region clock for an entry, keyed on the ISO's own EIA-930 BA code.

    :func:`_region_clock` reads the frame named by the ISO string, which is the
    BA code only where the two coincide (SOCO); ERCOT's EIA-930 BA is ``ERCO``.
    Raises rather than guessing: a registered entry that cannot be placed on
    the region's clock must fail loudly, never silently drop the correction.
    """
    from market_sim.data.zone_assignment import _iso_ba_codes

    for code in (iso.upper(), *_iso_ba_codes(iso)):
        frame = _region_clock(code, year)
        if frame is not None:
            return frame
    raise RuntimeError(
        f"ISO_PLANT_ENTRIES[{iso}] needs the {iso} {year} EIA-930 region clock, "
        "which is not on disk"
    )


def plant_entry_stamps(iso: str) -> dict[int, pd.Timestamp]:
    """``{plant: first hour INSIDE iso}`` from ``ISO_PLANT_ENTRIES[iso]``.

    The stamp is the region's EIA-930 hour-ending ``UTC time`` of the plant's
    first in-region row. Empty for any region the registry does not name.
    """
    return {
        int(p): pd.Timestamp(t)
        for p, t in ISO_PLANT_ENTRIES.get(iso.upper(), {}).items()
    }


def plant_entry_non_members(iso: str, year: int | None) -> frozenset[int]:
    """Registered entering plants that are outside ``iso`` for ALL of ``year``.

    A plant is outside in every year before its entry stamp's year; the entry
    year itself is split at hour grain (:func:`plant_entry_first_inside_row`,
    :func:`plant_entry_month_share`). ``year=None`` returns none.
    """
    if year is None:
        return frozenset()
    return frozenset(
        p for p, s in plant_entry_stamps(iso).items() if int(year) < s.year
    )


def _entry_std_offset(iso: str, year: int) -> pd.Timedelta:
    """The region clock's standard ``UTC time - Local time`` offset for ``year``."""
    frame = _entry_clock(iso, year)
    return (
        pd.to_datetime(frame["UTC time"]) - pd.to_datetime(frame["Local time"])
    ).max()


@lru_cache(maxsize=32)
def plant_entry_first_inside_row(iso: str, year: int) -> dict[int, int]:
    """``{plant: first LP row inside iso}`` for registered entering plants.

    In the entry year the row is the count of the region's local-year frame
    rows whose hour-ending ``UTC time`` precedes the stamp (the rows the LP
    dispatches, as :func:`ba_exit_first_outside_row`); in an earlier year it
    is ``2**31 - 1`` (never inside). Plants already inside all year are
    omitted, as is every plant of an unregistered region.
    """
    stamps = plant_entry_stamps(iso)
    out: dict[int, int] = {
        p: 2**31 - 1 for p, s in stamps.items() if int(year) < s.year
    }
    live = {p: s for p, s in stamps.items() if s.year == int(year)}
    if live:
        frame = _entry_clock(iso, year)
        utc = pd.to_datetime(frame["UTC time"]).to_numpy()
        out.update({p: int((utc < s.to_datetime64()).sum()) for p, s in live.items()})
    return out


# --- plant-grain EXIT (constants.ISO_PLANT_EXITS, lane R-ERCOT-14) ----------


def plant_exit_stamps(iso: str) -> dict[int, pd.Timestamp]:
    """``{plant: first hour OUTSIDE iso}`` from ``ISO_PLANT_EXITS[iso]``.

    Same clock as :func:`plant_entry_stamps`. Empty for any region the
    registry does not name.
    """
    return {
        int(p): pd.Timestamp(t) for p, t in ISO_PLANT_EXITS.get(iso.upper(), {}).items()
    }


@lru_cache(maxsize=32)
def plant_exit_first_outside_row(iso: str, year: int) -> dict[int, int]:
    """``{plant: first LP row OUTSIDE iso}`` for registered exiting plants.

    In the exit year the row is the count of the region's local-year frame
    rows whose hour-ending ``UTC time`` precedes the stamp; in a later year
    it is ``0`` (outside all year). Plants still inside all year are omitted,
    as is every plant of an unregistered region.
    """
    stamps = plant_exit_stamps(iso)
    out: dict[int, int] = {p: 0 for p, s in stamps.items() if int(year) > s.year}
    live = {p: s for p, s in stamps.items() if s.year == int(year)}
    if live:
        frame = _entry_clock(iso, year)
        utc = pd.to_datetime(frame["UTC time"]).to_numpy()
        out.update({p: int((utc < s.to_datetime64()).sum()) for p, s in live.items()})
    return out


def _campd_hour_ending_utc(iso: str, year: int, hours: np.ndarray) -> pd.DatetimeIndex:
    """Hour-ending UTC stamps of CAMPD hour-of-year indices (local standard)."""
    start = pd.Timestamp(f"{int(year)}-01-01")
    return (
        start
        + pd.to_timedelta(np.asarray(hours, dtype=np.int64), unit="h")
        + pd.Timedelta(hours=1)
        + _entry_std_offset(iso, year)
    )


def zero_pre_entry_campd(
    campd_year: pd.DataFrame | None, iso: str, year: int
) -> pd.DataFrame | None:
    """Zero CAMPD net of registered entering plants in hours before entry.

    ``campd_year`` is the benchmark's per-plant hourly CAMPD net frame
    (``plant_id``, ``hour`` = local-standard hour-of-year). Both CAMPD
    backfills read it and never consult the EIA-923 membership, so without
    this they re-book a non-member plant from its CEMS meter. Returns the
    input object unchanged when nothing is zeroed (byte-identical elsewhere).
    """
    if campd_year is None or campd_year.empty:
        return campd_year
    stamps = plant_entry_stamps(iso)
    if not stamps:
        return campd_year
    pid = pd.to_numeric(campd_year["plant_id"], errors="coerce")
    drop = pid.isin(plant_entry_non_members(iso, year)).to_numpy(dtype=bool).copy()
    live = {p: s for p, s in stamps.items() if s.year == int(year)}
    for p, s in live.items():
        m = (pid == p).to_numpy(dtype=bool)
        if m.any():
            he = _campd_hour_ending_utc(iso, year, campd_year.loc[m, "hour"].to_numpy())
            pre = np.zeros(len(campd_year), dtype=bool)
            pre[np.where(m)[0]] = he < s
            drop |= pre
    if not drop.any():
        return campd_year
    # ZERO, never drop: the missing-month fill reads each plant's series by
    # position on the hour-of-year clock, so removing rows would shift months.
    out = campd_year.copy()
    out.loc[drop, "net_mw"] = 0.0
    return out


@lru_cache(maxsize=32)
def plant_entry_month_share(iso: str, year: int) -> dict[int, tuple[int, float]]:
    """``{plant: (split month, in-region share)}`` for plants entering IN ``year``.

    The mirror of :func:`ba_exit_month_share`: the monthly EIA-923 benchmark
    zeroes the plant's months before the split month and scales the split
    month by the plant's own CAMPD gross-load share at or after the stamp
    (hour share of the month for a plant CAMPD does not carry).
    """
    live = {p: s for p, s in plant_entry_stamps(iso).items() if s.year == int(year)}
    if not live:
        return {}
    std_offset = _entry_std_offset(iso, year)
    cems = _exit_plant_cems(iso, int(year), tuple(sorted(live)))
    out: dict[int, tuple[int, float]] = {}
    for p, s in live.items():
        local = s - std_offset - pd.Timedelta(hours=1)
        month = int(local.month)
        m_start = pd.Timestamp(year=int(year), month=month, day=1)
        m_end = m_start + pd.offsets.MonthBegin(1)
        share = float((m_end - local) / (m_end - m_start))
        c = cems.get(p) if cems is not None else None
        if c is not None:
            he = c.index + pd.Timedelta(hours=1) + std_offset
            mm = c.index.month == month
            tot = float(c[mm].sum())
            if tot > 0:
                share = float(c[mm & (he >= s)].sum()) / tot
        out[p] = (month, share)
    return out
