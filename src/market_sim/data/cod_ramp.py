"""Commercial-operation-date (COD) vintage ramp — the single COD source.

A backcast solves a single historical year, but the dispatch fleet snapshot
(the curated ERCOT CAMPD bins / the EIA-860 generator parquet) is a *recent*
vintage that includes units commissioned **after** the year being solved. Left
unfiltered, a 2023 backcast dispatches GWs of capacity that were not yet built —
inflating reserve headroom and suppressing the scarcity prices the LP can set.

Renewables and storage already respect their commercial-operation dates
(:func:`market_sim.data.renewables` ramps wind/solar by ``Operating Month`` /
``Operating Year``; storage enters by vintage). This module extends the **same
month-precise rule to every thermal/nuclear/oil generator** so the default
backcast fleet reflects only what was actually online in the solved year.

The mechanism is a single :func:`monthly_online_mask` applied inside
:func:`market_sim.data.fleet.generators_to_fleet_arrays` (gated on
``config.cod_ramp_enabled``, default on for backcasts). Each dispatched
generator's commercial-operation / retirement date drives a 12-month online
mask: a unit that came online (or retired) part-way through the solved year is
available **only in the months it actually operated**, with ``min_gen`` (the
hard must-run floor) zeroed in the offline months so the LP lower bound cannot
force a not-yet-built / retired unit to run.

The COD date is sourced from EIA-860, the authoritative commissioning record —
``eia860_generator_operable.parquet`` carries a month-precise ``Operating
Month`` / ``Operating Year`` (and ``Planned Retirement Month`` / ``Year``) for
~every operable generator. Two reductions of that one sheet serve the two
grains an LP unit can have (SOCO-15, owner card S12, 2026-09-13):

* :func:`load_cod_map` — the per-plant
  ``{plant_code: (online_year, online_month, retirement_year, retirement_month)}``
  map: the capacity-weighted mean of the plant's units' CODs, and a retirement
  only when the *whole* plant retires. This is the **fallback** record — the
  best single date for a plant-level object that carries no unit record of its
  own (the ERCOT curated CAMPD bins, a synthesized ``(plant, group)`` bin whose
  constituents cannot be resolved, a registry-only plant).
* :func:`load_unit_cod_map` — the per-``(plant_code, fuel_type)`` list of the
  plant's own operable units ``(nameplate_mw, online_year, online_month)``,
  from which :func:`bin_online_fraction` builds a ``(plant, group)`` bin's
  **measured monthly online-capacity fraction**: the share of the bin's
  nameplate that had actually reached commercial operation in each month.

:func:`generator_online_mask` is the single resolver every fleet path goes
through. A raw EIA-860 :class:`Generator` (one LP unit per unit) prefers its
**own** ``Operating Year`` / ``Operating Month`` over the plant-collapsed date
— rule 14 ``[R-ACCURATE]``: the unit's own date is the measured input, the
plant mean is the estimate — exactly as :func:`effective_cod` already
preferred a unit's own retirement (the Homer City seam). A plant-level bin takes
the online fraction of its own constituents, so a brownfield addition at a
multi-vintage plant (Vogtle 3/4, Barry A3) ramps in on its real month instead
of being online from the plant mean. The plant-collapsed date is kept ONLY
where a unit has no own date (owner ruling, card S12).
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

import numpy as np
import pandas as pd

from market_sim.config.paths import PLANT_REGISTRY_CSV

logger = logging.getLogger(__name__)

_REGISTRY = PLANT_REGISTRY_CSV

# Opt-in clean-data read path (mirrors market_sim.data.fuel / outages /
# zone_assignment). When MARKET_SIM_USE_CLEAN is truthy, the registry-only
# year_built back-fill reads the curated reference/plant-registry table
# instead of the raw master-plant-registry.csv. OFF by default; falls back to
# raw when the clean partition is absent.
_USE_CLEAN_ENV = "MARKET_SIM_USE_CLEAN"
_USE_CLEAN_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _use_clean() -> bool:
    """Whether the opt-in clean-data read path is enabled (default ``False``)."""
    return os.environ.get(_USE_CLEAN_ENV, "").strip().lower() in _USE_CLEAN_TRUTHY


def _registry_year_built() -> pd.DataFrame:
    """Return the plant registry's ``(plant_id, year_built)`` rows, no nulls.

    Reads the curated ``reference/plant-registry`` clean table when
    :func:`_use_clean` is set and the partition exists (written by
    ``scripts/data/curate_reference.py``); otherwise reads ``_REGISTRY`` (the raw
    ``master-plant-registry.csv``) directly. Returns an empty frame when
    neither source is available.
    """
    if _use_clean():
        from scripts.lib.clean_io import clean_exists, read_clean

        if clean_exists("reference", market="plant-registry"):
            df = read_clean(
                "reference", market="plant-registry", columns=["plant_id", "year_built"]
            )
            return df.dropna(subset=["plant_id", "year_built"])
    if not _REGISTRY.exists():
        return pd.DataFrame(columns=["plant_id", "year_built"])
    reg = pd.read_csv(_REGISTRY, usecols=["plantid", "year_built"])
    reg = reg.rename(columns={"plantid": "plant_id"})
    return reg.dropna(subset=["plant_id", "year_built"])


# The month-precise generator-level EIA-860 operable schedule (Operating Month /
# Year, Planned Retirement Month / Year per generator) is read from the active
# vintage directory (paths.active_eia860_dir) inside _load_cod_map, so a
# year-matched vintage switch is honored and the cache keys on the directory.
#
# Alongside the operable schedule, the same directory's within-window retiree
# parquet (eia860_generator_retired_within_window.parquet, built by
# ``scripts/data/process_eia860.py --retired-window-from`` from the final EIA-860
# vintages' "Retired and Canceled" sheets) is unioned into the COD map so the
# ramp can age out whole plants that retired mid-window and so are absent from
# the default recent operable vintage (e.g. Mystic, plant 1588, retired
# mid-2024). It carries the actual retirement in ``planned_retirement_*``. The
# fleet loader injects the matching generators (the snapshot can only drop a
# unit it contains). A year-matched native vintage carries those exits in its
# own operable file and ships no retiree parquet, so the union is a no-op there
# (no double-count).
_RETIRED_WINDOW_NAME = "eia860_generator_retired_within_window.parquet"

# Month assumed for a unit whose COD *year* is known but whose month is not
# (e.g. a plant carried only by the master registry's year-only ``year_built``,
# absent from the month-precise EIA-860 operable schedule). A mid-year default
# keeps a same-year unit online for roughly half the year — the neutral
# assumption, matching the half-year prorate the year-only ramp used to apply.
COD_FALLBACK_MONTH = 7

# A ``Generator.online_year`` at or below this sentinel means "vintage unknown"
# (the model default is 2000 for fleets that never set a real commissioning
# year), so it must not drop a genuinely pre-existing unit.
_ONLINE_YEAR_SENTINEL = 2000

# One per-plant COD record: month-precise online and (optional) retirement date.
CodEntry = tuple[int, int, int | None, int | None]


def _cod_work_frame(path, columns: dict[str, str]) -> "pd.DataFrame | None":
    """Read an EIA-860 generator parquet into the COD reducer's column frame.

    ``columns`` maps the reducer's short names (``pc``/``oy``/``om``/``cap``/
    ``ry``/``rm``) to the source parquet's actual column names, so the operable
    sheet (raw EIA-860 headers) and the within-window retiree parquet (canonical
    schema) feed the same per-plant reduction. Returns ``None`` when the file is
    absent.
    """
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    frame = pd.DataFrame(
        {
            short: pd.to_numeric(df.get(src), errors="coerce")
            for short, src in columns.items()
        }
    )
    return frame.dropna(subset=["pc", "oy"])


def _reduce_cod_groups(work: "pd.DataFrame") -> dict[int, CodEntry]:
    """Reduce the prepared COD work frame to ``{plant_code: CodEntry}``.

    The vectorized equivalent of the former ``for code, grp in
    work.groupby("pc")`` loop (14,330 groups on the live vintage, each paying a
    ``DataFrame.dropna`` / ``sort_values`` / ``iloc``): one stable sort on
    ``pc`` plus flat numpy segment reductions over the resulting contiguous
    per-plant slices. The per-plant arithmetic is unchanged — same
    capacity-weighted continuous COD, same ``floor`` / half-to-even ``round``
    split back into ``(year, month)``, same all-units-retire test, and the same
    ``sort_values(["ry", "rm"]).iloc[-1]`` winner (reproduced with a stable
    ``np.lexsort`` that sorts a NaN ``rm`` last, matching pandas'
    ``na_position="last"``). Wall-clock only, byte-identical by construction and
    gated on dict equality against the shipped loop in
    ``tests/unit/data/test_cod_ramp.py`` (wall-clock item A-1,
    ``docs/handoffs/wallclock-opportunities-2026-09.md`` §2 A-1).

    ``work`` must already carry the reducer's short columns (``pc``/``oy``/
    ``om``/``cap``/``ry``/``rm``) plus the ``w`` weight column, with ``pc`` and
    ``oy`` non-null and ``om`` filled/clipped — i.e. the frame
    :func:`_load_cod_map` hands it.
    """

    def _col(name: str) -> np.ndarray:
        return work[name].to_numpy(dtype="float64", na_value=np.nan)

    pc, oy, om = _col("pc"), _col("oy"), _col("om")
    ry, rm, w = _col("ry"), _col("rm"), _col("w")

    # Stable sort on the plant code, so each plant's rows are one contiguous
    # slice in their original frame order — the same key-sorted, within-group
    # stable iteration groupby("pc") produced.
    order = np.argsort(pc, kind="stable")
    pc, oy, om, ry, rm, w = (a[order] for a in (pc, oy, om, ry, rm, w))

    starts = np.flatnonzero(np.concatenate(([True], pc[1:] != pc[:-1])))
    ends = np.concatenate((starts[1:], [pc.size]))
    counts = ends - starts

    def _segment_sums(*arrays: np.ndarray) -> "list[np.ndarray]":
        """Per-plant sums, bit-identical to a contiguous per-plant ``.sum()``.

        ``np.average`` summed each plant's slice with numpy's own *pairwise*
        algorithm, whose block structure depends on the slice length — so
        ``np.add.reduceat`` (sequential) is NOT a drop-in: it lands on the other
        side of the ``round`` boundary for the handful of plants whose exact
        mean is a half-integer (measured: 15 of 14,334 on the live vintage).
        Reducing a ``(n_plants_of_that_size, size)`` gather along its contiguous
        axis runs the identical inner loop, so the bits match exactly.
        """
        outs = [np.empty(starts.size, dtype="float64") for _ in arrays]
        for size in np.unique(counts):
            sel = np.flatnonzero(counts == size)
            rows = starts[sel][:, None] + np.arange(size)
            for arr, out in zip(arrays, outs):
                out[sel] = arr[rows].sum(axis=1)
        return outs

    # Continuous COD (year + (month-1)/12), capacity-weighted per plant. Every
    # weight is >= 0 (``cap.where(cap > 0, 0)``), so a segment sums to exactly
    # 0.0 iff every unit reports no capacity — the equal-weight fallback branch.
    cont = oy + (om - 1.0) / 12.0
    wsum, weighted, plain = _segment_sums(w, cont * w, cont)
    has_w = wsum > 0.0
    mean = np.where(has_w, weighted / np.where(has_w, wsum, 1.0), plain / counts)

    online_year = np.floor(mean)
    online_month = np.clip(np.rint((mean - online_year) * 12.0) + 1.0, 1.0, 12.0)

    # Retire the plant only when *every* unit of it carries a planned
    # retirement year; the latest (ry, rm) then wins.
    all_retire = np.add.reduceat((~np.isnan(ry)).astype(np.int64), starts) == counts
    # np.lexsort is stable and takes keys least-significant-first, so this is
    # sort_values(["ry", "rm"], na_position="last") applied within each plant
    # (the group index is the primary key, so group spans are unchanged).
    gidx = np.repeat(np.arange(starts.size), counts)
    winner = np.lexsort((np.where(np.isnan(rm), np.inf, rm), ry, gidx))[ends - 1]
    ret_year = np.where(
        all_retire, np.where(np.isnan(ry[winner]), 0.0, ry[winner]), 0.0
    )
    ret_month = np.where(np.isnan(rm[winner]), 12.0, rm[winner])

    # ``int()`` on the scalars truncated toward zero; ``astype(np.int64)`` does
    # the same. Built in ascending ``pc`` order, so two distinct float plant
    # codes truncating to one int resolve to the later one, as before.
    return {
        code: (o_y, o_m, (r_y if retires else None), (r_m if retires else None))
        for code, o_y, o_m, r_y, r_m, retires in zip(
            pc[starts].astype(np.int64).tolist(),
            online_year.astype(np.int64).tolist(),
            online_month.astype(np.int64).tolist(),
            ret_year.astype(np.int64).tolist(),
            ret_month.astype(np.int64).tolist(),
            all_retire.tolist(),
        )
    }


def load_cod_map() -> dict[int, CodEntry]:
    """Public entry point: build the COD map for the active EIA-860 vintage.

    Resolves the directory through :func:`paths.active_eia860_dir` (so a
    ``ScenarioConfig.eia860_vintage_year`` switch is honored) and defers to the
    directory-keyed cache below.

    When the clean seam is on (``MARKET_SIM_USE_CLEAN``), the COD map is built
    from the curated clean ``fleet`` registry instead (:func:`_load_cod_map_clean`),
    routing the active vintage directory to its clean partition year so the same
    ``eia860_vintage_year`` switch is honored end to end.
    """
    from market_sim.config.paths import active_eia860_dir

    # Lazy import to dodge the fleet <-> cod_ramp module-load cycle (fleet imports
    # cod_ramp at module top); both are fully imported by the time this is called.
    from market_sim.data.fleet import _clean_fleet_year, _use_clean

    if _use_clean():
        return _load_cod_map_clean(_clean_fleet_year(active_eia860_dir()))
    return _load_cod_map(active_eia860_dir())


@lru_cache(maxsize=4)
def _load_cod_map_clean(partition_year: int) -> dict[int, CodEntry]:
    """Build the COD map from the curated clean ``fleet`` registry.

    The clean counterpart of :func:`_load_cod_map`. The frozen clean ``fleet``
    schema carries ``plant_id``, ``nameplate_capacity_mw`` and ``operating_year``
    but NOT the month-precise ``Operating Month`` / ``Planned Retirement
    Month``/``Year`` columns the raw reducer uses, so this is necessarily a
    **year-precise** COD map: each plant's online year is the capacity-weighted
    mean of its units' ``operating_year`` (rounded), its online month defaults to
    :data:`COD_FALLBACK_MONTH`, and it carries **no** planned retirement.
    Recovering month precision and plant retirements through the clean seam would
    require a fleet-schema contract change — raise one rather than editing the
    frozen YAML. The master-registry ``year_built`` back-fill is applied exactly
    as on the raw path (the registry is a raw reference file, not part of the
    clean contract).

    Raises ``FileNotFoundError`` (with a regenerate hint) when the clean fleet
    partition is absent — regenerate it with
    ``python scripts/regenerate_clean.py fleet``.
    """
    from scripts.lib import clean_io

    cod: dict[int, CodEntry] = {}

    df = clean_io.read_clean(
        "fleet",
        year=partition_year,
        columns=["plant_id", "nameplate_capacity_mw", "operating_year"],
    )
    work = pd.DataFrame(
        {
            "pc": pd.to_numeric(df.get("plant_id"), errors="coerce"),
            "cap": pd.to_numeric(df.get("nameplate_capacity_mw"), errors="coerce"),
            "oy": pd.to_numeric(df.get("operating_year"), errors="coerce"),
        }
    ).dropna(subset=["pc", "oy"])

    if not work.empty:
        # Positive nameplate weights the COD; equal-weight a plant that reports
        # no capacity so it still gets a representative year.
        work["w"] = work["cap"].where(work["cap"] > 0.0, 0.0)
        for code, grp in work.groupby("pc"):
            code = int(code)
            weights = grp["w"].to_numpy()
            if weights.sum() <= 0.0:
                weights = np.ones(len(grp))
            online_year = int(
                round(float(np.average(grp["oy"].to_numpy(), weights=weights)))
            )
            # Month unknown in the clean schema -> mid-year default; no retirement.
            cod[code] = (online_year, COD_FALLBACK_MONTH, None, None)

    # Registry-only back-fill (year-only -> mid-year default), never overriding
    # a clean-fleet record — mirrors the raw reducer.
    reg = _registry_year_built()
    for code, year in zip(reg["plant_id"], reg["year_built"]):
        code = int(code)
        if code not in cod:
            cod[code] = (int(year), COD_FALLBACK_MONTH, None, None)

    return cod


@lru_cache(maxsize=4)
def _load_cod_map(eia860_dir) -> dict[int, CodEntry]:
    """Build the ``{plant_code: (online_year, online_month, ret_year, ret_month)}`` map.

    Reduced from the month-precise EIA-860 operable generator schedule:

    * the plant's online date is the **capacity-weighted** mean of its units'
      ``(Operating Year, Operating Month)`` — a representative COD that tracks
      where the bulk of the plant's nameplate actually came online, so a plant
      whose capacity is dominated by a recent build ramps in the solved year
      while one with a small recent addition to an old base does not. (A scalar
      per-plant COD necessarily approximates a genuinely mixed-vintage plant; the
      capacity weighting is the closest single date to the true per-unit
      online-capacity fraction — see docs/cod-vintage-ramp.md.)
    * a **retirement** date is recorded only when *every* unit of the plant
      carries a planned retirement (the whole plant goes away); the latest such
      date is used, so capacity is kept until the last unit retires. A partial
      retirement leaves the plant online (``None``).

    Plants present only in the curated master registry (``year_built``) — not in
    the EIA-860 operable schedule — are back-filled at :data:`COD_FALLBACK_MONTH`
    so an ERCOT plant the registry knows but EIA-860 omits still ramps by year.
    The result is cached (the underlying files are static within a process).
    """
    cod: dict[int, CodEntry] = {}

    # The operable schedule (raw EIA-860 headers) plus the active directory's
    # within-window retiree parquet (canonical schema) feed the same per-plant
    # reduction. The retiree file is absent from a year-matched native vintage
    # dir (which carries its exits in the operable file already), so the union
    # is a no-op there.
    frames = [
        _cod_work_frame(
            eia860_dir / "eia860_generator_operable.parquet",
            {
                "pc": "Plant Code",
                "oy": "Operating Year",
                "om": "Operating Month",
                "cap": "Nameplate Capacity (MW)",
                "ry": "Planned Retirement Year",
                "rm": "Planned Retirement Month",
            },
        ),
        _cod_work_frame(
            eia860_dir / _RETIRED_WINDOW_NAME,
            {
                "pc": "plant_id",
                "oy": "operating_year",
                "om": "operating_month",
                "cap": "nameplate_capacity_mw",
                "ry": "planned_retirement_year",
                "rm": "planned_retirement_month",
            },
        ),
    ]
    frames = [f for f in frames if f is not None]
    work = pd.concat(frames, ignore_index=True) if frames else None

    if work is not None and not work.empty:
        work["om"] = work["om"].fillna(COD_FALLBACK_MONTH).clip(1, 12)
        # Positive nameplate weights the COD; fall back to equal weight when a
        # plant reports no capacity so it still gets a representative date.
        work["w"] = work["cap"].where(work["cap"] > 0.0, 0.0)
        # Continuous COD (year + (month-1)/12), capacity-weighted, then split
        # back into an integer (year, month); plus the whole-plant retirement.
        cod.update(_reduce_cod_groups(work))

    # Registry-only back-fill (year-only -> mid-year default), never overriding
    # the month-precise EIA-860 record.
    reg = _registry_year_built()
    for code, year in zip(reg["plant_id"], reg["year_built"]):
        code = int(code)
        if code not in cod:
            cod[code] = (int(year), COD_FALLBACK_MONTH, None, None)

    return cod


# One constituent unit of a (plant, fuel) bin: (nameplate MW, online year,
# online month). Retirement is deliberately NOT carried — the bin's retirement
# stays whatever :func:`effective_cod` resolves (plant-collapsed, or the exit
# cohort's own under ``partial_plant_exit_carry``), so this repair moves the
# ONLINE half of the seam only (rule 19 [R-ONE-MECH]: the partial-exit cohort
# is the one mechanism for unit-grain retirement under binning).
CodUnit = tuple[float, int, int]

# EIA-860 generator status admitted to the bin-constituent list — the same
# filter the fleet loader applies (``eia860._rows_to_generators`` keeps status
# ``OP`` only), so a bin and its constituents are the same population.
_OPERABLE_STATUS = "OP"


def load_unit_cod_map() -> dict[tuple[int, str], tuple[CodUnit, ...]]:
    """Public entry point: per-``(plant_code, fuel_type)`` constituent CODs.

    Resolves the directory through :func:`paths.active_eia860_dir` exactly as
    :func:`load_cod_map` does, so the two reductions of the operable sheet are
    always read from the same vintage. Under the clean seam
    (``MARKET_SIM_USE_CLEAN``) the frozen clean ``fleet`` schema carries no
    ``operating_month``, so no unit record can be built there and the map is
    empty — every bin then falls back to the plant-collapsed date exactly as
    before this seam existed (a schema contract change is the route to month
    precision on that path, not an edit here).
    """
    from market_sim.config.paths import active_eia860_dir

    from market_sim.data.fleet import _use_clean

    if _use_clean():
        return {}
    return _load_unit_cod_map(active_eia860_dir())


@lru_cache(maxsize=4)
def _load_unit_cod_map(eia860_dir) -> dict[tuple[int, str], tuple[CodUnit, ...]]:
    """Build ``{(plant_code, fuel_type): ((nameplate_mw, online_year, online_month), ...)}``.

    The unit-grain companion of :func:`_load_cod_map`, read from the SAME two
    parquets (the operable schedule plus the within-window retiree parquet) so
    a bin's constituents and its plant-collapsed fallback never disagree about
    which units exist. Each operable (status ``OP``) generator is classified
    with the fleet loader's own ``_map_fuel_type`` (technology / energy source /
    prime mover -> ``gas_cc`` / ``gas_ct`` / ``gas_st`` / ``coal`` / ``oil`` /
    ``biomass`` / ``nuclear``), which is the fuel a ``(plant, group)`` bin maps
    to through ``BIN_GROUP_TO_FUEL`` — so ``(3, "gas_cc")`` is exactly Barry's
    combined-cycle units, and Barry's coal bin never sees Barry A3's 2023-11
    COD. Units the loader cannot classify (solar, wind, hydro, storage — which
    ramp on their own vintage paths) are not recorded.

    The weight is EIA-860 nameplate, the same basis :func:`_load_cod_map`
    weights the plant mean with; a unit with a missing or non-positive
    nameplate carries weight 0 and :func:`bin_online_fraction` falls back to
    equal weights when a whole bin reports none. A missing ``Operating Month``
    takes :data:`COD_FALLBACK_MONTH`.
    """
    # Lazy import to dodge the fleet <-> cod_ramp module-load cycle (fleet
    # imports cod_ramp at module top); the loader's classifier is the ONE
    # source of the fuel bucket so the bin and its constituents agree.
    from market_sim.data.fleet.eia860 import _map_fuel_type

    columns = [
        ("pc", "Plant Code", "plant_id"),
        ("oy", "Operating Year", "operating_year"),
        ("om", "Operating Month", "operating_month"),
        ("cap", "Nameplate Capacity (MW)", "nameplate_capacity_mw"),
        ("status", "Status", "status"),
        ("tech", "Technology", "technology"),
        ("src", "Energy Source 1", "energy_source"),
        ("pm", "Prime Mover", "prime_mover"),
    ]
    frames = []
    for name, col_idx in (
        ("eia860_generator_operable.parquet", 0),
        (_RETIRED_WINDOW_NAME, 1),
    ):
        path = eia860_dir / name
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        df.columns = [str(c).strip() for c in df.columns]
        frames.append(
            pd.DataFrame({short: df.get(spec[col_idx]) for short, *spec in columns})
        )
    if not frames:
        return {}
    work = pd.concat(frames, ignore_index=True)
    work["pc"] = pd.to_numeric(work["pc"], errors="coerce")
    work["oy"] = pd.to_numeric(work["oy"], errors="coerce")
    work = work.dropna(subset=["pc", "oy"])
    work = work[work["status"].astype(str).str.strip().str.upper() == _OPERABLE_STATUS]
    work["om"] = (
        pd.to_numeric(work["om"], errors="coerce")
        .fillna(COD_FALLBACK_MONTH)
        .clip(1, 12)
    )
    work["cap"] = (
        pd.to_numeric(work["cap"], errors="coerce").fillna(0.0).clip(lower=0.0)
    )
    work["fuel"] = [
        _map_fuel_type(t, s, p)
        for t, s, p in zip(work["tech"], work["src"], work["pm"])
    ]
    work = work.dropna(subset=["fuel"])

    out: dict[tuple[int, str], list[CodUnit]] = {}
    for pc, fuel, cap, oy, om in zip(
        work["pc"].astype(np.int64).tolist(),
        work["fuel"].tolist(),
        work["cap"].astype(float).tolist(),
        work["oy"].astype(np.int64).tolist(),
        work["om"].astype(np.int64).tolist(),
    ):
        out.setdefault((pc, str(fuel)), []).append((cap, oy, om))
    return {key: tuple(units) for key, units in out.items()}


def bin_online_fraction(
    units: "tuple[CodUnit, ...] | list[CodUnit]", run_year: int
) -> np.ndarray:
    """Return the ``(12,)`` measured online-capacity fraction of a bin in ``run_year``.

    Element ``m`` is the share of the bin's nameplate that had reached
    commercial operation by calendar month ``m + 1``: the nameplate-weighted
    mean of each constituent unit's own :func:`monthly_online_mask` (online
    half only — retirement is ``None`` here by design, see :data:`CodUnit`).
    A bin whose every unit predates ``run_year`` is all ones (no change from
    the plant-collapsed path); a greenfield bin whose units all came online in
    September is ``0`` through August and ``1`` from September, exactly the
    step the plant-collapsed date produced; a brownfield bin — old units plus a
    new one — takes the intermediate fraction the mean date could only round to
    one side of. Equal weights when the bin reports no nameplate; an empty
    ``units`` returns all ones (the caller keeps the plant-collapsed record).
    """
    if not units:
        return np.ones(12, dtype=float)
    weights = np.array([float(u[0]) for u in units], dtype=float)
    if weights.sum() <= 0.0:
        weights = np.ones(len(units), dtype=float)
    masks = np.array(
        [
            monthly_online_mask(int(u[1]), int(u[2]), None, None, run_year)
            for u in units
        ],
        dtype=float,
    )
    return (weights[:, None] * masks).sum(axis=0) / weights.sum()


def monthly_online_mask(
    online_year: int | None,
    online_month: int,
    retirement_year: int | None,
    retirement_month: int | None,
    run_year: int,
) -> np.ndarray:
    """Return the ``(12,)`` boolean online mask for one unit in ``run_year``.

    Element ``m`` (0-based month) is ``True`` when the unit is commissioned and
    not yet retired in calendar month ``m + 1``:

    * ``online_year > run_year`` → not yet built (all ``False``);
    * ``online_year == run_year`` → online from ``online_month`` on;
    * ``retirement_year < run_year`` → already gone (all ``False``);
    * ``retirement_year == run_year`` → online through ``retirement_month``.

    ``online_year`` of ``None`` (vintage unknown) keeps the unit fully online.
    """
    months = np.arange(1, 13)
    on = np.ones(12, dtype=bool)
    if online_year is not None:
        if online_year > run_year:
            on[:] = False
        elif online_year == run_year:
            on &= months >= online_month
    if retirement_year is not None:
        if retirement_year < run_year:
            on[:] = False
        elif retirement_year == run_year:
            on &= months <= (retirement_month if retirement_month is not None else 12)
    return on


def class_cod_coverage(
    class_labels: "list[str]",
    online_years: "list[int | None]",
) -> dict[str, tuple[int, int]]:
    """Tabulate per-class COD-date coverage for a fleet.

    ``class_labels[i]`` is generator ``i``'s resource class (its ``plant_group``,
    or fuel type when the group is blank) and ``online_years[i]`` is the
    ``online_year`` :func:`effective_cod` resolved for it (``None`` = vintage
    unknown → the unit is held fully online with no ramp). Returns
    ``{class_label: (n_units, n_with_cod)}``.

    The audit guardrail: a resource class whose units all resolve to a known
    EIA-860 COD is month-precision ramped; a class with ``n_with_cod == 0`` is
    silently skipping the vintage ramp (a future fleet vintage that drops a
    class's build dates, or a new fuel that never reaches the COD map, shows up
    here as 0-of-N covered). See :func:`log_class_cod_coverage`.
    """
    cov: dict[str, list[int]] = {}
    for label, oy in zip(class_labels, online_years):
        rec = cov.setdefault(str(label or "unknown"), [0, 0])
        rec[0] += 1
        if oy is not None:
            rec[1] += 1
    return {k: (v[0], v[1]) for k, v in cov.items()}


def log_class_cod_coverage(
    coverage: dict[str, tuple[int, int]], iso: str, run_year: int
) -> list[str]:
    """Log per-class COD coverage and WARN on any class with no COD dates.

    Emits one DEBUG line per class and a single WARNING naming every class that
    resolved **zero** EIA-860 COD dates across all its units — the signal that a
    resource class is silently bypassing the month-precise vintage ramp. Returns
    the list of fully-uncovered class labels (empty when every class is covered),
    so callers/tests can assert on it.
    """
    uncovered: list[str] = []
    for label in sorted(coverage):
        n, n_cod = coverage[label]
        logger.debug(
            "COD coverage (%s %s): %s %d/%d units have an EIA-860 COD",
            iso,
            run_year,
            label,
            n_cod,
            n,
        )
        if n > 0 and n_cod == 0:
            uncovered.append(label)
    if uncovered:
        logger.warning(
            "COD ramp (%s %s): %d resource class(es) have NO EIA-860 COD date "
            "and skip the vintage ramp entirely: %s — a fleet vintage may have "
            "dropped this class's build dates (check load_cod_map / "
            "_map_fuel_type coverage)",
            iso,
            run_year,
            len(uncovered),
            ", ".join(uncovered),
        )
    return uncovered


def effective_cod(
    plant_code: int,
    online_year: int,
    online_month: int,
    retirement_year: int | None,
    retirement_month: int | None,
    cod_map: dict[int, CodEntry],
    is_plant_level: bool = False,
) -> CodEntry:
    """Resolve a generator's COD: its own measured record first, the plant map second.

    **Online date.** A generator that is a real EIA-860 unit
    (``is_plant_level=False``) carrying its own known commissioning year
    (``online_year`` above the ``2000`` "vintage unknown" sentinel) keeps its
    **own** ``online_year`` / ``online_month`` — the measured record — whether
    or not its plant is in ``cod_map``. The plant-collapsed date applies ONLY
    where the generator has no own date: a plant-level synthesized object
    (``is_plant_level=True`` — a CAMPD bin, whose ``online_year`` is a registry
    / COD-year estimate stamped by ``bins_to_fleet``, never a unit's own
    record), or a unit whose own year is unknown. *(SOCO-15, owner card S12,
    2026-09-13, rule 14 [R-ACCURATE]. Before this ruling the map ALWAYS won the
    online date, so a brownfield unit at a multi-vintage plant — Vogtle 3,
    plant 649, own COD 2023-07 against a plant mean of 2005-05 — was online
    all twelve months of 2023, 12.98 TWh of phantom nuclear, while a
    greenfield plant, whose mean IS its units' date, ramped correctly.)*
    Without a map entry the generator's own attributes apply as before, the
    sentinel reading as "unknown" so a real pre-existing unit is never dropped.

    **Retirement.** The map's retirement is a plant-level reduction:
    ``_load_cod_map`` collapses a plant's heterogeneous unit retirements to the
    **latest** one, which keeps a winding-down plant fully online past the
    months its earlier units actually left (e.g. Homer City, plant 3122 — its
    three coal units retired 2023-07 / 2023-08 / 2024-04, yet the collapse held
    all 2012 MW online through 2024-04, ~2 GW of phantom H2-2023 capacity the
    cost-based LP then dispatched as baseload). So when the generator carries
    its **own** per-unit retirement, it is preferred over the plant-collapsed
    date — each within-window retiree unit ages out on its true EIA-860
    retirement month. The online-date rule above is the same preference
    applied symmetrically to the other end of the unit's life. The ERCOT CAMPD
    bins carry neither, so they keep the plant-map record unchanged.
    """
    entry = cod_map.get(int(plant_code)) if plant_code else None
    own_online_known = online_year > _ONLINE_YEAR_SENTINEL
    if entry is not None:
        entry_oy, entry_om, entry_ry, entry_rm = entry
        if not is_plant_level and own_online_known:
            # Rule 14 [R-ACCURATE] (card S12): the unit's own measured date.
            oy, om = online_year, online_month
        else:
            oy, om = entry_oy, entry_om
        if retirement_year is not None:
            return (oy, om, retirement_year, retirement_month)
        return (oy, om, entry_ry, entry_rm)
    oy = online_year if own_online_known else None
    return (oy, online_month, retirement_year, retirement_month)


def generator_online_mask(
    plant_code: int,
    plant_group: str | None,
    online_year: int,
    online_month: int,
    retirement_year: int | None,
    retirement_month: int | None,
    is_plant_level: bool,
    cod_map: dict[int, CodEntry],
    unit_cod_map: dict[tuple[int, str], tuple[CodUnit, ...]],
    run_year: int,
) -> tuple[np.ndarray, int | None]:
    """Resolve one LP unit's ``(12,)`` online-capacity mask for ``run_year``.

    The single resolver behind the COD ramp, at the grain the LP unit actually
    has (SOCO-15, card S12 — one shared seam, the same construction on every
    fleet path, rule 25 [R-ISO-SCOPE]):

    * a **raw EIA-860 unit** (``is_plant_level=False``) — its own measured
      ``Operating Year`` / ``Operating Month`` through :func:`effective_cod`, a
      0/1 mask;
    * a **plant-level bin** (``is_plant_level=True``) whose ``(plant_code,
      BIN_GROUP_TO_FUEL[plant_group])`` constituents are in ``unit_cod_map`` —
      the constituents' nameplate-weighted online fraction
      (:func:`bin_online_fraction`), a mask in ``[0, 1]``, times the
      retirement half :func:`effective_cod` resolves for the bin (the
      plant-collapsed retirement, or an exit cohort's own);
    * anything else — the plant-collapsed record exactly as before.

    Returns ``(mask, online_year)``; ``online_year`` is the value the COD
    coverage audit (:func:`class_cod_coverage`) counts, ``None`` meaning the
    unit's vintage is unknown and it is held fully online.
    """
    oy, om, ry, rm = effective_cod(
        plant_code,
        online_year,
        online_month,
        retirement_year,
        retirement_month,
        cod_map,
        is_plant_level=is_plant_level,
    )
    if is_plant_level and plant_code and unit_cod_map:
        # Lazy import: the group -> fuel table lives beside the classifier the
        # unit map was built with, in the fleet package that imports this one.
        from market_sim.data.fleet.eia860 import BIN_GROUP_TO_FUEL

        fuel = BIN_GROUP_TO_FUEL.get(str(plant_group or ""))
        units = unit_cod_map.get((int(plant_code), fuel)) if fuel else None
        if units:
            online = bin_online_fraction(units, run_year)
            retire = monthly_online_mask(None, 1, ry, rm, run_year).astype(float)
            return online * retire, oy
    return monthly_online_mask(oy, om, ry, rm, run_year).astype(float), oy
