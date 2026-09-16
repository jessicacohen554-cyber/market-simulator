"""Curate the ``demand-profile`` clean datatype from the legacy EIA-930 extract.

Repairs ``data/raw/eia-930/eia_demand_profiles.parquet`` (raw/ is immutable,
CLAUDE.md) at the curation seam: a per-``(iso, year)`` physical-bounds screen
flags hours whose ``raw_mw`` is non-positive or an order-of-magnitude spike,
then linear interpolation across each flagged run fills it from the nearest
valid hours. This is the sole system-total demand source
``market_sim.data.eia_loader.load_demand`` falls back to whenever an ISO has
no dedicated per-BA hourly extract for a year (every PJM year; 2021-2022 for
CAISO and MISO) — see the module docstring in
``data/dictionary/schema/demand-profile.schema.yaml`` for the full writeup and
the 2026-07-05 PJM capacity-hindcast finding that discovered the defect
(``docs/hindcast-reports/pjm-2021-2025-realized-2026-07-05.md``).

Physical-bounds screen (see :func:`screen_physical_bounds`): a real ISO/BA's
hourly system demand never departs from its own annual median by more than
~2.1x in either direction — verified empirically by sweeping every one of the
35 (iso, year) series in this raw file (7 ISOs incl. SPP x 2021-2025) outside
the flagged defects. A 5x-median ceiling and a ``<= 0`` floor are therefore
generous, unambiguous bounds that flag only genuine defects: three
9-to-10-digit spike hours (PJM 2021, SPP 2023) and a set of ``0.0`` "missing
data" sentinel hours (impossible for whole-BA demand) scattered across
CAISO/MISO/NEISO/NYISO/PJM/SPP, some in isolated hours and some in day-long
runs (several coincide with DST transition dates, suggesting a local-clock
parsing artifact in whatever legacy pipeline built this extract; others do
not, and are presumably genuine EIA-930 reporting gaps recorded as 0 rather
than NaN).

This script screens and reports on every (iso, year) series in the raw file and
repairs+writes every ISO the model registers (:data:`MODEL_ISOS`). SPP joined
that set on 2026-09-07 (lane SPP-31): it has been registered since SPP-20, and
until its partition was written ``load_demand_meta("SPP", 2023)`` fell through
to the corrupted legacy summary and reported a 3,621,097 MW peak — the
2023-06-12 21:00 unit slip this curator was already flagging and repairing for
SPP, then discarding (``[skip ] SPP 2023: 1 physically-impossible hour(s)``).

SOCO joined it on 2026-09-16 (lane SOCO-31), and needed more than membership:
the legacy extract is a FROZEN artifact with no live builder and carries no
SOCO rows at all, so walking its groups writes nothing for SOCO however many
registries name it. :func:`curate_unextracted` closes that — the in-window twin
of :func:`curate_pre_window`, sourcing the per-BA ``SOCO hourly`` extract
through the same ``load_demand`` adapter. Both are the same F3 repair on
different axes: pre-window on YEAR (PJM 2019, MISO 2020), unextracted on ISO.

The script is idempotent and reads only ``data/raw``; the clean Parquet is
overwritten on each run.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import EIA_930_DIR
from scripts.lib.clean_io import validate_clean, write_clean

# Legacy raw extract this script repairs (immutable; see module docstring).
_RAW_FILE = EIA_930_DIR / "eia_demand_profiles.parquet"

# Physical-bounds screen constants (see module docstring for the empirical
# derivation: every legitimate (iso, year) series in this file has
# max/median <= 2.1 and min/median >= 0.2).
MAX_MEDIAN_RATIO: float = 5.0

# ISOs this repo models (get_iso_config) — the seven of
# ``iso_configs.SUPPORTED_ISOS``, which is exactly the ISO set the raw extract
# carries. SPP was appended 2026-09-07 (lane SPP-31) after SPP-20 registered it:
# every consumer of ``load_demand_meta`` (build_calibration_reference's demand
# block among them) reads the repaired clean partition when one exists and the
# corrupted legacy summary when it does not, so a registered ISO missing from
# this set is served a 3.6 million MW peak.
# SOCO was appended 2026-09-16 (lane SOCO-31) after SOCO-20 registered it as
# the ninth region. SOCO is the FIRST member of this set the legacy extract
# carries NO rows for at all -- it predates SOCO's registration and has no live
# builder -- so membership alone writes nothing for it and
# ``load_demand_meta("SOCO", 2023)`` still raised. What closes it is
# :func:`curate_unextracted`, the in-window twin of :func:`curate_pre_window`:
# both source the per-BA EIA-930 hourly extract through the SAME
# ``load_demand`` adapter, so the partition summarises the identical series the
# LP dispatches (rule 19 ``[R-ONE-MECH]``, rule 14 ``[R-ACCURATE]``) rather
# than a second reconstruction of it.
MODEL_ISOS: frozenset[str] = frozenset(
    {"ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "SOCO"}
)

# Pre-window years the legacy extract does NOT carry, curated here from the
# per-BA EIA-930 hourly extracts instead (see :func:`curate_pre_window`). The
# span is the program's working span below the legacy file's 2021 floor: 2019
# (locked-test tier) and 2020 (the validation ladder's bottom rung after the
# owner's 2026-08-06 scope decision, which DROPPED 2018 and earlier).
PRE_WINDOW_YEARS: tuple[int, ...] = (2019, 2020)


def screen_physical_bounds(mw: np.ndarray) -> np.ndarray:
    """Return a boolean mask of physically-impossible hours in a demand series.

    Flags any hour whose value is non-positive (system demand cannot be zero
    or negative) or more than :data:`MAX_MEDIAN_RATIO` times the series'
    median (an order-of-magnitude spike well outside any legitimate seasonal
    peak/trough — see module docstring).
    """
    mw = np.asarray(mw, dtype=float)
    if mw.size == 0:
        return np.zeros(0, dtype=bool)
    med = float(np.median(mw))
    return (mw <= 0.0) | (mw > med * MAX_MEDIAN_RATIO)


def repair_by_interpolation(mw: np.ndarray, bad: np.ndarray) -> np.ndarray:
    """Linearly interpolate flagged hours from the nearest valid neighbors.

    ``bad`` hours at either end of the series (no valid neighbor on that side)
    fall back to the nearest valid value (``limit_direction="both"``).
    """
    mw = np.asarray(mw, dtype=float).copy()
    if not bad.any():
        return mw
    masked = pd.Series(mw)
    masked[bad] = np.nan
    return masked.interpolate(method="linear", limit_direction="both").to_numpy()


def repair_series(iso: str, year: int, g: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Repair one (iso, year) group; returns the repaired frame + bad-hour count."""
    g = g.sort_values("hour").reset_index(drop=True)
    mw = g["raw_mw"].to_numpy(dtype=float)
    bad = screen_physical_bounds(mw)
    repaired_mw = repair_by_interpolation(mw, bad)
    total = repaired_mw.sum()
    out = pd.DataFrame(
        {
            "iso": iso,
            "year": int(year),
            "hour": g["hour"].to_numpy(dtype="int64"),
            "raw_mw": repaired_mw,
            "normalized": repaired_mw / total if total > 0 else np.nan,
            "repaired": bad,
        }
    )
    return out, int(bad.sum())


def pre_window_series(iso: str, year: int) -> np.ndarray | None:
    """Return the system demand (MW) for a pre-2021 ``(iso, year)``, or ``None``.

    Sourced from the **per-BA EIA-930 hourly extract**
    (``data/raw/eia-930-hourly/<BA> hourly.parquet``, which covers 2018-2026)
    through ``eia930.demand``'s own per-ISO adapter — i.e. the exact series
    :func:`market_sim.data.eia_loader.load_demand` already serves for these
    years, screens and all. Reusing the adapter rather than re-reading the
    frame here is what makes the curated pre-window partition consistent with
    the demand the LP would dispatch against, instead of a second, parallel
    reconstruction of it.

    Returns ``None`` when the ISO has no per-BA extract covering the year.
    """
    from market_sim.data.eia930.demand import DEMAND_LOADERS

    adapter = DEMAND_LOADERS.get(iso)
    if adapter is None:
        return None
    # The adapters share one signature; only CAISO reads these two keys, and
    # both take the ScenarioConfig defaults (this is a data-curation pass, not
    # a scenario, so no run-specific override can apply).
    from market_sim.config.scenarios import ScenarioConfig

    cfg = ScenarioConfig()
    raw_mw, _interchange = adapter(
        year,
        {
            "caiso_demand_clock_realign": cfg.caiso_demand_clock_realign,
            "caiso_supply_consistent_demand": cfg.caiso_supply_consistent_demand,
        },
    )
    return raw_mw


def curate_pre_window() -> list:
    """Write ``demand-profile`` partitions for :data:`PRE_WINDOW_YEARS`.

    THE F3 GAP, STATED PRECISELY. The legacy ``eia_demand_profiles.parquet``
    starts at 2021 for every ISO, and so does its ``eia_demand_meta.parquet``
    summary. The *hourly demand driver* has not depended on that file since
    every ISO gained a per-BA extract adapter — ``load_demand(iso, 2019)``
    works today for all six — but :func:`load_demand_meta` still reads the
    legacy summary whenever no clean partition exists, so it raises
    ``ValueError: No EIA-930 data for ISO '<iso>' in year 2019``. That single
    raise is what blocks ``build_calibration_reference._demand_totals``, and
    through it the ``calibration_reference.json`` block and
    ``<ISO>_<year>_renewable_capacity.csv`` for every pre-2021 year.

    Writing the partition here closes it at the curation seam:
    ``load_demand_meta`` prefers the clean partition, recomputes
    peak/min/avg/total from it, and never reaches the legacy summary. ``raw/``
    is untouched (it is immutable, CLAUDE.md), no new raw artifact is invented,
    and the pre-window meta is by construction the summary of the *same* series
    ``load_demand`` serves — which the legacy 2021-2025 summary is not
    (rule 14 ``[R-ACCURATE]``: the accurate source wins).

    Rule 22: this is data preparation, not a spend. Building the partition
    solves, scores and registers nothing; the holdout freeze's
    ``frozen_operations`` are solve/score/registration and its ``not_frozen``
    list names data intake explicitly.
    """
    written = []
    for year in PRE_WINDOW_YEARS:
        for iso in sorted(MODEL_ISOS):
            path = _write_per_ba_partition(iso, year, "pre-window")
            if path is not None:
                written.append(path)
    return written


def _write_per_ba_partition(iso: str, year: int, label: str) -> str | None:
    """Write one ``demand-profile`` partition from the per-BA hourly extract.

    Shared by :func:`curate_pre_window` (years below the legacy extract's 2021
    floor) and :func:`curate_unextracted` (a registered ISO the legacy extract
    has no rows for at all). Both take the SAME series through the SAME
    ``load_demand`` adapter and the SAME physical-bounds screen, so a partition
    written by either is the summary of the array the LP dispatches, never a
    second reconstruction of it (rule 19 ``[R-ONE-MECH]``). Returns the written
    path, or ``None`` when the ISO has no usable 8,760-hour series for the year.
    """
    mw = pre_window_series(iso, year)
    if mw is None or len(mw) != HOURS_PER_YEAR or np.isnan(mw).any():
        print(
            f"  [skip ] {iso} {year}: no usable per-BA hourly series "
            "— partition not written"
        )
        return None
    bad = screen_physical_bounds(mw)
    repaired_mw = repair_by_interpolation(mw, bad)
    total = repaired_mw.sum()
    frame = pd.DataFrame(
        {
            "iso": iso,
            "year": int(year),
            "hour": np.arange(HOURS_PER_YEAR, dtype="int64"),
            "raw_mw": repaired_mw,
            "normalized": repaired_mw / total if total > 0 else np.nan,
            "repaired": bad,
        }
    )
    path = write_clean(
        frame,
        "demand-profile",
        iso=iso,
        year=int(year),
        source="data/raw/eia-930-hourly/<BA> hourly.parquet",
        extra_provenance={
            "n_repaired_hours": int(bad.sum()),
            "basis": "per-BA EIA-930 hourly extract (load_demand adapter)",
        },
    )
    validate_clean(path)
    print(
        f"  [write] {iso} {year}: {label} partition from the per-BA "
        f"extract ({int(bad.sum())} hour(s) repaired, "
        f"peak {repaired_mw.max():,.0f} MW, "
        f"total {total / 1e6:,.1f} TWh)"
    )
    return path


def unextracted_iso_years(raw: pd.DataFrame) -> list[tuple[str, int]]:
    """Return the ``(iso, year)`` pairs the legacy extract omits, in its own span.

    Data-driven on the raw file itself — never an ``iso == "SOCO"`` ladder — so
    a tenth region registers here with no edit: the candidate years are exactly
    the years the legacy extract carries for *somebody*, and a pair is returned
    only when this ISO has no row of its own for that year. For the seven ISOs
    the extract was built around the result is EMPTY (each carries all of
    2021-2025), which is why their committed partitions cannot move.
    """
    years = sorted({int(y) for y in raw["year"].unique()})
    have = {(str(i), int(y)) for i, y in zip(raw["iso"], raw["year"], strict=True)}
    return [
        (iso, year)
        for iso in sorted(MODEL_ISOS)
        for year in years
        if (iso, year) not in have
    ]


def curate_unextracted(raw: pd.DataFrame) -> list:
    """Write partitions for registered ISOs the legacy extract never carried.

    THE SOCO GAP, STATED PRECISELY (lane SOCO-31, 2026-09-16). The legacy
    ``eia_demand_profiles.parquet`` is a frozen artifact with no live builder:
    it was written before SOCO existed as a region and carries rows for seven
    ISOs only. :func:`curate_all` walks that file's own groups, so a registered
    ISO absent from it gets no partition however many registries name it — and
    ``load_demand_meta`` then falls through to the equally frozen
    ``eia_demand_meta.parquet`` summary and raises ``No EIA-930 data for ISO
    'SOCO'``. That single raise blocks
    ``build_calibration_reference._demand_totals``, and through it SOCO's whole
    ``calibration_reference.json`` block and its per-year renewable-capacity
    CSVs — the same F3 failure mode :func:`curate_pre_window` closed for PJM
    2019 and MISO 2020, one axis over (ISO rather than year).

    The repair is the same one, for the same reason (rule 14 ``[R-ACCURATE]``):
    source the series from the per-BA EIA-930 hourly extract the LP itself
    dispatches instead of back-filling a legacy summary that is known corrupt
    where it does exist. ``raw/`` is untouched, no raw artifact is invented, and
    a year with no usable series is SKIPPED and reported rather than padded
    (rule 13 ``[R-MEASURED]``) — SOCO 2021 and 2022 skip on exactly that branch,
    because ``SOCO hourly.parquet`` starts in 2023.
    """
    written = []
    for iso, year in unextracted_iso_years(raw):
        path = _write_per_ba_partition(iso, year, "in-window")
        if path is not None:
            written.append(path)
    return written


def curate_all() -> list:
    """Screen + repair every (iso, year) series; write clean Parquet for modeled ISOs.

    Returns the list of clean Parquet paths written. Prints a report of every
    (iso, year) series the physical-bounds screen flagged, including any
    non-modeled ISO the extract carries (screened and reported, never written).

    Covers two sources: the legacy raw extract (2021-2025, repaired in place at
    this seam) and the pre-window years the legacy extract omits (see
    :func:`curate_pre_window`).
    """
    if not _RAW_FILE.is_file():
        print(f"no raw demand-profiles extract at {_RAW_FILE}; nothing to curate")
        return []

    raw = pd.read_parquet(_RAW_FILE)
    written = []
    print(f"screening {_RAW_FILE} ({len(raw):,} rows)")
    for (iso, year), g in raw.groupby(["iso", "year"]):
        cleaned, n_bad = repair_series(str(iso), int(year), g)
        if n_bad:
            hours = cleaned.loc[cleaned["repaired"], "hour"].tolist()
            print(
                f"  [{'write' if iso in MODEL_ISOS else 'skip '}] {iso} {year}: "
                f"{n_bad} physically-impossible hour(s) repaired: {hours}"
            )
        if iso not in MODEL_ISOS:
            continue
        path = write_clean(
            cleaned,
            "demand-profile",
            iso=str(iso),
            year=int(year),
            source=f"data/raw/eia-930/{_RAW_FILE.name}",
            extra_provenance={"n_repaired_hours": n_bad},
        )
        validate_clean(path)
        written.append(path)

    print(f"\npre-window years ({', '.join(str(y) for y in PRE_WINDOW_YEARS)})")
    written.extend(curate_pre_window())

    missing = unextracted_iso_years(raw)
    print(
        f"\nregistered ISOs the legacy extract omits "
        f"({len(missing)} (iso, year) pair(s))"
    )
    written.extend(curate_unextracted(raw))
    return written


def main() -> None:
    paths_written = curate_all()
    print(
        f"\ndemand-profile curation complete: {len(paths_written)} clean file(s) written."
    )


if __name__ == "__main__":
    main()
