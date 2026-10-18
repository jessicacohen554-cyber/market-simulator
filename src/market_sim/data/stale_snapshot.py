"""EIA-930 stale-snapshot repair: measured replacements for frozen hours.

For stretches of hours EIA-930 repeats one stale snapshot of a BA's whole
record — ``Demand``, ``Net generation``, ``Total interchange``, every ``NG:``
fuel column and all sub-BA demands freeze together while the real system
moves (``docs/records/spp/FINDING-spp-south-demand-flatruns-2026-10-18.md``).
This module detects those hours and serves the ISO's OWN measurement in them,
under owner rulings R22 (demand, zonal weights, interchange) and R23 (wind,
solar), UC-DESK r20 (lane UC-SPP-DATAFIX).

**Detection** (:func:`market_sim.data.stale_runs.stale_run_mask`, threshold
from the spec, cited in ``constants.py``):

* the *demand mask*: the BA ``Demand`` OR the sub-BA demand vector repeats
  exactly for >= ``min_run`` hours (measured on the raw values, before any
  gap fill — a forward fill would manufacture repeats);
* a *fuel mask* per ``NG:`` column: the column repeats exactly for >=
  ``min_run`` hours at a NONZERO value, or at any value inside the demand
  mask. A zero run outside it is a physical state (night solar), not a
  snapshot; inside a whole-record freeze it is the snapshot's own zero.

**Replacement** in masked hours, each from a curated clean datatype read on
the BA frame's own clock (row ``k`` = the hour ending at the frame's
``UTC time[k]``):

* system demand = sum of the ISO's area loads (``iso-area-load``);
* zonal weights = those area loads grouped to the model zones;
* net interchange = the measured seam legs (``counterparty-interchange``):
  per counterparty, the counterparty-reported leg, else the BA's own report;
* wind / solar = the ISO's generation mix (``iso-genmix``).

**Where no measured replacement exists** the desk rulings inside R22 / R23
apply — measured beats stale beats estimated, never interpolate — and each is
a DECLARED gap in the spec (values in ``constants.py``): a tie-bounded leg
neither side reports is left out (``omitted_legs``); in a ruled hour the
BA's stale interchange is kept (``kept_stale_interchange_hours``); in a ruled
window where the generation mix is blank the stale wind / solar is kept
(``kept_stale_renewable_windows``). Every such hour is flagged in
:func:`stale_snapshot_provenance`. Any OTHER masked hour without its
replacement raises (``StaleSnapshotDataError``); a missing clean partition
raises ``FileNotFoundError`` with the regenerate command. ISOs are wired
through :data:`STALE_SNAPSHOT_SPECS` — no ISO branching in the callers; an
ISO without a spec is passed through unchanged (bit-identical).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    HOURS_PER_YEAR,
    SPP_STALE_KEPT_INTERCHANGE_HOURS_UTC,
    SPP_STALE_KEPT_RENEWABLE_WINDOWS_UTC,
    SPP_STALE_OMITTED_LEGS,
    SPP_STALE_RUN_MIN_HOURS,
)
from market_sim.data.eia930.frames import _eia_hourly_frame_filled, logger
from market_sim.data.stale_runs import stale_run_mask


class StaleSnapshotDataError(RuntimeError):
    """A stale-masked hour has no measured replacement in the curated source."""


@dataclass(frozen=True)
class StaleSnapshotSpec:
    """One ISO's stale-snapshot repair wiring.

    Attributes:
        iso: Model ISO label.
        ba: EIA-930 balancing-authority code of the ISO's hourly frame.
        min_run: Exact-repeat run length (hours) that marks a stale snapshot.
        subba_vector: ``year -> (HOURS_PER_YEAR, k)`` raw sub-BA demand on the
            frame clock (NaN where absent, never gap-filled), or ``None``.
        area_groups: ``zone_names -> {area: zone}`` for the ISO's area loads.
        genmix_area: ``area`` label of the ISO's ``iso-genmix`` rows.
        omitted_legs: Counterparties whose leg is LEFT OUT where neither side
            reports it (tie-bounded, ruled); any other unreported leg raises
            unless its hour is in ``kept_stale_interchange_hours``.
        kept_stale_interchange_hours: Hour-ending UTC stamps (ISO strings)
            where the BA's own stale interchange is kept, flagged (ruled).
        kept_stale_renewable_windows: Inclusive hour-ending UTC windows where
            the generation mix is blank and the stale EIA-930 wind / solar is
            kept, flagged (ruled); any other blank masked hour raises.
    """

    iso: str
    ba: str
    min_run: int
    subba_vector: Callable[[int], np.ndarray | None]
    area_groups: Callable[[list[str]], dict[str, str]]
    genmix_area: str
    omitted_legs: tuple[str, ...] = ()
    kept_stale_interchange_hours: tuple[str, ...] = ()
    kept_stale_renewable_windows: tuple[tuple[str, str], ...] = ()


# --------------------------------------------------------------------------
# SPP wiring
# --------------------------------------------------------------------------


def _spp_subba_vector(year: int) -> np.ndarray | None:
    """SPP's 17 EIA-930 sub-BA demands on the SWPP frame clock, raw (unfilled).

    Reads the same raw files and UTC -> hour-of-year map as
    ``scripts.data.curate_zonal_shares.parse_spp_shares`` but keeps absent
    rows NaN: that parser's ``ffill`` would turn a missing hour into a repeat.
    """
    from scripts.data.curate_zonal_shares import (
        _SPP_SUBBA_ZONE_GROUPS,
        ZONE_DEMAND_DIR,
        _spp_utc_to_local_hoy,
    )

    spp_dir = ZONE_DEMAND_DIR / "SPP"
    path = spp_dir / f"spp_subba_demand_{year}.csv"
    if not path.exists():
        path = spp_dir / "spp_subba_demand_2023-2025.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, usecols=["period", "subba", "value"], dtype={"subba": str})
    df = df[df["subba"].isin(_SPP_SUBBA_ZONE_GROUPS)]
    period = pd.to_datetime(df["period"], format="%Y-%m-%dT%H", errors="coerce")
    hoy = _spp_utc_to_local_hoy(period, year)
    if hoy is None:
        return None
    df = df.assign(hoy=hoy.to_numpy(), mw=pd.to_numeric(df["value"], errors="coerce"))
    df = df.dropna(subset=["hoy"]).drop_duplicates(["period", "subba"], keep="first")
    wide = df.pivot_table(index="hoy", columns="subba", values="mw", aggfunc="first")
    wide = wide.reindex(index=np.arange(HOURS_PER_YEAR, dtype=float))
    wide = wide.reindex(columns=sorted(_SPP_SUBBA_ZONE_GROUPS))
    return wide.to_numpy(dtype=float)


def _spp_area_groups(zone_names: list[str]) -> dict[str, str]:
    """The sub-BA -> zone grouping ``parse_spp_shares`` uses for ``zone_names``."""
    from scripts.data.curate_zonal_shares import (
        _SPP_SUBBA_ZONE_GROUPS,
        _SPP_SUBBA_ZONE_GROUPS_WEST_EAST,
    )

    return (
        _SPP_SUBBA_ZONE_GROUPS_WEST_EAST
        if "SPP-West" in zone_names
        else _SPP_SUBBA_ZONE_GROUPS
    )


#: ISO -> stale-snapshot wiring. Only SPP is registered (owner rulings R22 /
#: R23); every other ISO's inputs are untouched by this module.
STALE_SNAPSHOT_SPECS: dict[str, StaleSnapshotSpec] = {
    "SPP": StaleSnapshotSpec(
        iso="SPP",
        ba="SWPP",
        min_run=SPP_STALE_RUN_MIN_HOURS,
        subba_vector=_spp_subba_vector,
        area_groups=_spp_area_groups,
        genmix_area="SPP",
        omitted_legs=SPP_STALE_OMITTED_LEGS,
        kept_stale_interchange_hours=SPP_STALE_KEPT_INTERCHANGE_HOURS_UTC,
        kept_stale_renewable_windows=SPP_STALE_KEPT_RENEWABLE_WINDOWS_UTC,
    ),
}


# --------------------------------------------------------------------------
# Masks
# --------------------------------------------------------------------------


@lru_cache(maxsize=32)
def _frame_utc_end(ba: str, year: int) -> pd.DatetimeIndex | None:
    """The BA frame's hour-ending UTC stamps (row ``k`` = model hour ``k``)."""
    frame = _eia_hourly_frame_filled(ba, year)
    if frame is None:
        return None
    return pd.DatetimeIndex(pd.to_datetime(frame["UTC time"])).tz_localize("UTC")


@lru_cache(maxsize=32)
def demand_stale_mask(iso: str, year: int) -> np.ndarray | None:
    """``(HOURS_PER_YEAR,)`` demand mask for a registered ISO-year, else ``None``.

    True where the raw BA ``Demand`` or the raw sub-BA vector repeats exactly
    for at least the spec's ``min_run`` hours. ``None`` when the ISO has no
    spec or its frame is unavailable (forecast years): nothing is repaired.
    """
    spec = STALE_SNAPSHOT_SPECS.get(iso)
    if spec is None:
        return None
    frame = _eia_hourly_frame_filled(spec.ba, year)
    if frame is None or len(frame) != HOURS_PER_YEAR:
        return None
    mask = stale_run_mask(frame["Demand"].to_numpy(dtype=float), spec.min_run)
    subba = spec.subba_vector(year)
    if subba is not None:
        mask = mask | stale_run_mask(subba, spec.min_run)
    mask.setflags(write=False)
    return mask


@lru_cache(maxsize=64)
def fuel_stale_mask(iso: str, year: int, column: str) -> np.ndarray | None:
    """``(HOURS_PER_YEAR,)`` stale mask of one EIA-930 ``NG:`` column, else ``None``.

    True inside an exact-repeat run of at least ``min_run`` hours whose value
    is nonzero, or inside any exact-repeat run that falls in the demand mask
    (a whole-record freeze also freezes a zero). ``None`` when unregistered,
    the frame is unavailable, or the column is absent.
    """
    spec = STALE_SNAPSHOT_SPECS.get(iso)
    if spec is None:
        return None
    frame = _eia_hourly_frame_filled(spec.ba, year)
    if frame is None or len(frame) != HOURS_PER_YEAR or column not in frame.columns:
        return None
    values = frame[column].to_numpy(dtype=float)
    runs = stale_run_mask(values, spec.min_run)
    demand = demand_stale_mask(iso, year)
    in_record_freeze = demand if demand is not None else np.zeros_like(runs)
    mask = runs & ((values != 0.0) | in_record_freeze)
    mask.setflags(write=False)
    return mask


def reset_caches() -> None:
    """Clear the per-year mask and clock caches (tests redirect the raw roots)."""
    _frame_utc_end.cache_clear()
    demand_stale_mask.cache_clear()
    fuel_stale_mask.cache_clear()


# --------------------------------------------------------------------------
# Curated replacements on the frame clock
# --------------------------------------------------------------------------


def _read_partition(datatype: str, iso: str, year: int) -> pd.DataFrame:
    """Read one clean partition, raising with the regenerate command when absent."""
    from scripts.lib.clean_io import clean_exists, read_clean

    if not clean_exists(datatype, iso=iso, year=year):
        raise FileNotFoundError(
            f"no clean {datatype} partition for {iso} {year}, needed by the "
            f"stale-snapshot repair: run `python scripts/regenerate_clean.py "
            f"--solve-profile {iso}` (or scripts/data/curate_"
            f"{datatype.replace('-', '_')}.py)"
        )
    return read_clean(datatype, iso=iso, year=year, validate=False)


def _on_clock(
    rows: pd.DataFrame, key: str, value: str, keys: list[str], clock: pd.DatetimeIndex
) -> np.ndarray:
    """``(len(clock), len(keys))`` values pivoted onto the frame's hour-end clock."""
    wide = rows.pivot_table(
        index="interval_end_utc", columns=key, values=value, aggfunc="first"
    )
    wide.index = pd.DatetimeIndex(wide.index).tz_convert("UTC")
    return wide.reindex(index=clock, columns=keys).to_numpy(dtype=float)


def _area_load(spec: StaleSnapshotSpec, year: int, areas: list[str]) -> np.ndarray:
    """``(HOURS_PER_YEAR, len(areas))`` ISO-published area load on the frame clock."""
    clock = _frame_utc_end(spec.ba, year)
    rows = _read_partition("iso-area-load", spec.iso, year)
    return _on_clock(rows, "area", "load_mw", areas, clock)


def _require(values: np.ndarray, mask: np.ndarray, what: str, iso: str, year: int):
    """Raise when any masked hour lacks a finite replacement value."""
    bad = mask & ~np.isfinite(values)
    if bad.any():
        raise StaleSnapshotDataError(
            f"{iso} {year}: {int(bad.sum())} stale-masked hour(s) have no "
            f"measured {what} (first hours {np.flatnonzero(bad)[:10].tolist()})"
        )


# --------------------------------------------------------------------------
# Repairs (called by the loaders; identity for unregistered ISOs)
# --------------------------------------------------------------------------


def repair_system_demand(iso: str, year: int, demand: np.ndarray) -> np.ndarray:
    """Replace stale-masked system demand with the sum of the ISO's area loads."""
    spec = STALE_SNAPSHOT_SPECS.get(iso)
    mask = demand_stale_mask(iso, year)
    if spec is None or mask is None or not mask.any():
        return demand
    areas = sorted(spec.area_groups([]))
    loads = _area_load(spec, year, areas)
    total = np.where(np.isfinite(loads).all(axis=1), loads.sum(axis=1), np.nan)
    _require(total, mask, "area load", iso, year)
    out = np.array(demand, dtype=float, copy=True)
    fill = mask & np.isfinite(total)
    out[fill] = total[fill]
    logger.info(
        "%s %d: stale-snapshot repair of system demand in %d h (mean %+.0f MW)",
        iso,
        year,
        int(mask.sum()),
        float((out - demand)[mask].mean()),
    )
    return out


def repair_zone_shares(
    iso: str, year: int, shares: np.ndarray, zone_names: list[str]
) -> np.ndarray:
    """Replace stale-masked ``(n_zones, T)`` weights with area-load zone shares."""
    spec = STALE_SNAPSHOT_SPECS.get(iso)
    mask = demand_stale_mask(iso, year)
    if spec is None or mask is None or not mask.any():
        return shares
    groups = spec.area_groups(zone_names)
    areas = sorted(groups)
    loads = _area_load(spec, year, areas)
    zone_load = np.zeros((len(zone_names), HOURS_PER_YEAR), dtype=float)
    for j, area in enumerate(areas):
        zone_load[zone_names.index(groups[area])] += loads[:, j]
    total = zone_load.sum(axis=0)
    _require(total, mask, "area load", iso, year)
    out = np.array(shares, dtype=float, copy=True)
    fill = mask & np.isfinite(total)
    out[:, fill] = zone_load[:, fill] / total[fill]
    return out


def _on_stamps(clock: pd.DatetimeIndex, stamps: tuple[str, ...]) -> np.ndarray:
    """``(T,)`` mask of the clock hours equal to any hour-ending UTC stamp."""
    if not stamps:
        return np.zeros(len(clock), dtype=bool)
    want = pd.DatetimeIndex([pd.Timestamp(t) for t in stamps]).tz_convert("UTC")
    return np.asarray(clock.isin(want))


def _in_windows(
    clock: pd.DatetimeIndex, windows: tuple[tuple[str, str], ...]
) -> np.ndarray:
    """``(T,)`` mask of the clock hours inside any inclusive hour-ending UTC window."""
    out = np.zeros(len(clock), dtype=bool)
    for lo, hi in windows:
        out |= np.asarray(
            (clock >= pd.Timestamp(lo).tz_convert("UTC"))
            & (clock <= pd.Timestamp(hi).tz_convert("UTC"))
        )
    return out


@dataclass(frozen=True)
class InterchangeLegs:
    """The measured seam legs of one ISO-year on the frame clock.

    Attributes:
        parties: Counterparty labels, column order of ``omitted``.
        total: ``(T,)`` sum of the measured legs (counterparty-reported, else
            the BA's own; omitted legs contribute nothing).
        omitted: ``(T, n)`` masked hours whose (ruled-omittable) leg is left out.
        kept_stale: ``(T,)`` masked hours where the BA's stale interchange is
            kept (ruled).
    """

    parties: tuple[str, ...]
    total: np.ndarray
    omitted: np.ndarray
    kept_stale: np.ndarray


def _interchange_legs(spec: StaleSnapshotSpec, year: int, mask: np.ndarray):
    """Assemble the measured legs; raise on an unreported leg nobody ruled on."""
    clock = _frame_utc_end(spec.ba, year)
    rows = _read_partition("counterparty-interchange", spec.iso, year)
    parties = sorted(rows["counterparty"].unique())
    by_side = {
        side: _on_clock(
            rows[rows["reporter"] == side], "counterparty", "export_mw", parties, clock
        )
        for side in ("counterparty", "own")
    }
    legs = np.where(
        np.isfinite(by_side["counterparty"]), by_side["counterparty"], by_side["own"]
    )
    reported = np.isfinite(by_side["counterparty"]) | np.isfinite(by_side["own"])
    residual = _residual_legs(reported, mask)
    omittable = np.array([p in spec.omitted_legs for p in parties], dtype=bool)
    kept = _on_stamps(clock, spec.kept_stale_interchange_hours) & mask
    unruled = residual[:, ~omittable].any(axis=1) & ~kept
    if unruled.any():
        hours = np.flatnonzero(unruled)
        missing = sorted({p for j, p in enumerate(parties) if residual[hours, j].any()})
        raise StaleSnapshotDataError(
            f"{spec.iso} {year}: {hours.size} stale-masked hour(s) have an "
            f"unreported, non-omittable seam leg {missing} (first hours "
            f"{hours[:10].tolist()}); no measured replacement and no ruling"
        )
    return InterchangeLegs(
        parties=tuple(parties),
        total=np.nansum(legs, axis=1),
        omitted=residual & omittable[None, :] & ~kept[:, None],
        kept_stale=kept,
    )


def repair_net_interchange(iso: str, year: int, interchange: np.ndarray) -> np.ndarray:
    """Replace stale-masked net export with the sum of the measured seam legs.

    Per counterparty and hour: the counterparty-reported leg, else the BA's
    own report (owner ruling R22). A leg with neither, from its first reported
    hour of the year on (a BA that did not yet exist is not a gap), is a
    residual. A ruled-omittable leg (``spec.omitted_legs``, tie-bounded) is
    left out and logged; in a ruled hour (``spec.kept_stale_interchange_hours``)
    the BA's own stale value is kept; any other residual raises
    (:class:`StaleSnapshotDataError`). Never interpolated.
    """
    spec = STALE_SNAPSHOT_SPECS.get(iso)
    mask = demand_stale_mask(iso, year)
    if spec is None or mask is None or not mask.any():
        return interchange
    legs = _interchange_legs(spec, year, mask)
    out = np.array(interchange, dtype=float, copy=True)
    fill = mask & ~legs.kept_stale
    out[fill] = legs.total[fill]
    if legs.omitted.any() or legs.kept_stale.any():
        counts = {
            p: int(n) for p, n in zip(legs.parties, legs.omitted.sum(axis=0)) if n
        }
        logger.warning(
            "%s %d: stale-snapshot interchange repair — omitted legs (h) %s; "
            "%d h keep the stale BA value (ruled)",
            iso,
            year,
            counts,
            int(legs.kept_stale.sum()),
        )
    return out


def _residual_legs(reported: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """``(T, n_legs)`` masked hours whose leg has no report on either side.

    A leg counts only from its first reported hour of the year: a BA that did
    not yet exist (SIKE before 2025-06-01) is structurally absent, not a gap.
    There is no end bound — a submission that stops before the year ends
    (SWPP's own legs in late December 2025) is a gap.
    """
    idx = np.arange(reported.shape[0])[:, None]
    first = np.where(reported.any(axis=0), reported.argmax(axis=0), reported.shape[0])
    return ~reported & (idx >= first) & mask[:, None]


#: EIA-930 ``NG:`` column -> ``iso-genmix`` fuel family, per renewable key.
_RENEWABLE_COLUMNS: dict[str, tuple[str, str]] = {
    "wind": ("NG: WND", "wind"),
    "solar": ("NG: SUN", "solar"),
}


def _renewable_replacement(
    spec: StaleSnapshotSpec, year: int, fuel: str, rows: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(mask, generation-mix MW, kept-stale mask)`` for one renewable fuel.

    Raises when a masked hour has no generation-mix value outside the ruled
    ``kept_stale_renewable_windows``.
    """
    column, mix_fuel = _RENEWABLE_COLUMNS[fuel]
    mask = fuel_stale_mask(spec.iso, year, column)
    clock = _frame_utc_end(spec.ba, year)
    mix = _on_clock(rows, "fuel", "generation_mw", [mix_fuel], clock)[:, 0]
    ruled = _in_windows(clock, spec.kept_stale_renewable_windows)
    _require(mix, mask & ~ruled, f"{mix_fuel} generation mix", spec.iso, year)
    kept = mask & ~np.isfinite(mix)
    return mask, mix, kept


def repair_renewable_gen(
    iso: str, year: int, gen: dict[str, np.ndarray]
) -> dict[str, np.ndarray]:
    """Replace stale-masked wind / solar MW with the ISO's own generation mix.

    In a ruled window where the generation mix is itself blank
    (``spec.kept_stale_renewable_windows``) the stale EIA-930 value is kept and
    flagged; any other blank masked hour raises. Never interpolated.
    """
    spec = STALE_SNAPSHOT_SPECS.get(iso)
    if spec is None:
        return gen
    out = dict(gen)
    rows = None
    for fuel, series in gen.items():
        if fuel not in _RENEWABLE_COLUMNS:
            continue
        mask = fuel_stale_mask(iso, year, _RENEWABLE_COLUMNS[fuel][0])
        if mask is None or not mask.any():
            continue
        if rows is None:
            rows = _read_partition("iso-genmix", iso, year)
            rows = rows[rows["area"] == spec.genmix_area]
        mask, mix, kept = _renewable_replacement(spec, year, fuel, rows)
        repaired = np.array(series, dtype=float, copy=True)
        fill = mask & ~kept
        repaired[fill] = mix[fill]
        out[fuel] = repaired
        logger.info(
            "%s %d: stale-snapshot repair of %s in %d h (mean %+.0f MW); %d h "
            "keep the stale value (ruled)",
            iso,
            year,
            fuel,
            int(fill.sum()),
            float((repaired - series)[mask].mean()),
            int(kept.sum()),
        )
    return out


def stale_snapshot_provenance(iso: str, year: int) -> pd.DataFrame:
    """Per-hour provenance of every stale-masked hour of a registered ISO-year.

    One row per hour where any mask is set: ``hour`` (model row),
    ``interval_end_utc``, ``demand_source`` / ``interchange_source`` /
    ``wind_source`` / ``solar_source`` (``""`` = EIA-930 unmasked;
    ``"iso_measured"`` = the ISO's own measurement; ``"eia_stale_kept"`` =
    EIA-930's stale value kept by ruling) and ``interchange_legs_omitted``
    (``;``-joined counterparties left out). Empty for an unregistered ISO or a
    year with no frame.
    """
    cols = [
        "hour",
        "interval_end_utc",
        "demand_source",
        "interchange_source",
        "interchange_legs_omitted",
        "wind_source",
        "solar_source",
    ]
    spec = STALE_SNAPSHOT_SPECS.get(iso)
    mask = demand_stale_mask(iso, year)
    if spec is None or mask is None:
        return pd.DataFrame(columns=cols)
    clock = _frame_utc_end(spec.ba, year)
    n = HOURS_PER_YEAR
    demand_src = np.where(mask, "iso_measured", "")
    ix_src = demand_src.copy()
    omitted = np.full(n, "", dtype=object)
    if mask.any():
        legs = _interchange_legs(spec, year, mask)
        ix_src = np.where(legs.kept_stale, "eia_stale_kept", ix_src)
        for j, party in enumerate(legs.parties):
            hit = legs.omitted[:, j]
            omitted[hit] = [f"{o};{party}" if o else party for o in omitted[hit]]
    any_mask = mask.copy()
    fuel_src: dict[str, np.ndarray] = {}
    rows = None
    for fuel in ("wind", "solar"):
        fmask = fuel_stale_mask(iso, year, _RENEWABLE_COLUMNS[fuel][0])
        src = np.full(n, "", dtype=object)
        if fmask is not None and fmask.any():
            if rows is None:
                rows = _read_partition("iso-genmix", iso, year)
                rows = rows[rows["area"] == spec.genmix_area]
            fmask, _, kept = _renewable_replacement(spec, year, fuel, rows)
            src[fmask] = "iso_measured"
            src[kept] = "eia_stale_kept"
            any_mask |= fmask
        fuel_src[fuel] = src
    hours = np.flatnonzero(any_mask)
    return pd.DataFrame(
        {
            "hour": hours,
            "interval_end_utc": clock[hours],
            "demand_source": demand_src[hours],
            "interchange_source": ix_src[hours],
            "interchange_legs_omitted": omitted[hours],
            "wind_source": fuel_src["wind"][hours],
            "solar_source": fuel_src["solar"][hours],
        },
        columns=cols,
    )
