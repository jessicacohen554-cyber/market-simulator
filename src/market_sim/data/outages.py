"""Historic generator-outage overlay for calibration backcasts.

Turns measured CAMPD unit outages into per-plant availability derates on the
model's fixed 8760-hour clock, applied by
:func:`market_sim.data.fleet.generators_to_fleet_arrays` only when a backcast
config sets ``outage_source == "historic"``; forward/forecast runs keep the
statistical WEFOR/POF availability model.

The **per-unit derate** (:func:`unit_outage_derate_factors`, from
``campd-unit-outages[-<ISO>].csv`` built by
``scripts/data/derive_campd_unit_outages.py``) is the SOLE CAMPD outage layer for
every ISO. The old facility-summed overlay (which built ``campd-outages*.csv``,
a hard ``availability = 0`` per plant; its detection primitives are now
consolidated in ``scripts/lib/outage_detect.py``) was removed
2026-07-17: summing a plant's units hid single-unit outages and folded
daily-cycling combined cycles into phantom summer outages
(``results/calibration/FINDING-ercot79-phantom-outage-2026-07.md``). Each unit
outage of at least :data:`UNIT_OUTAGE_MIN_DAYS` days derates its plant bin by the
unit's capacity share over the window; a genuinely single-unit plant (the unit's
capacity equals its plant-bin capacity) is fully zeroed. Combustion turbines
(``CT_PEAKER`` / ``CT_CHP``) carry no derate — they dispatch economically, and a
CT down-window cannot be certified a forced outage vs out-of-merit-at-peak
(unlike baseload coal/CC, where down-at-peak reliably implies an outage).

This module also carries the companion measured-availability overlays: short
(< 5-day) baseload-coal windows, unit-grain partial-derate plateaus, declared
max-gen-event derates, per-reactor nuclear refuel series, the ERCOT class-day
thermal DAM availability rescale, within-window retiree CEMS caps, and the
non-CAMPD ERCOT availability caps / reliability-deployment floors.

One mechanism here is NOT a backcast overlay: the correlated cold-event
forced-outage derate (:func:`apply_correlated_outage_derate`, FF-1B) is the
**forecast/hindcast** statistical counterpart of the measured windows — it
regenerates a Uri-class availability event from the weather-year temperature
series and the frozen measured excess-FOR curves, and is suppressed in
backcast mode precisely because the overlays above already carry the actual
events. See the section comment at the bottom of the module.
"""

from __future__ import annotations

import calendar
import logging
import os
import re
from collections.abc import Sequence
from functools import lru_cache, partial
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import (
    CALIBRATION_DIR,
    CAMPD_BINS_CSV,
    RAW_DATA_DIR,
    REFERENCE_DIR,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Clean-data read seam (MARKET_SIM_USE_CLEAN, default OFF)
# ---------------------------------------------------------------------------
# When this env flag is set, the facility-outage overlay sources its windows
# from the curated clean tree (data/clean/outages, written by
# scripts/data/curate_outages.py through the frozen scripts/lib/clean_io.py seam)
# instead of re-deriving them from raw here. The raw/derive path below stays the
# default and is left fully intact; the flag is a migration gate, not a switch
# we flip in code. See data/README.md and data/dictionary/schema/outages.schema.yaml.
_USE_CLEAN_ENV = "MARKET_SIM_USE_CLEAN"
_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _use_clean() -> bool:
    """Whether to read outages from the clean tree (MARKET_SIM_USE_CLEAN)."""
    return os.environ.get(_USE_CLEAN_ENV, "").strip().lower() in _TRUTHY


def _clean_io():
    """Import the frozen clean-data read seam (``scripts/lib/clean_io.py``).

    The model package does not put the repo root — where the ``scripts``
    package lives — on ``sys.path``, so add it before importing. This module is
    the contract; we only ever read through it (never edit it).
    """
    try:
        import scripts.lib.clean_io as clean_io
    except ModuleNotFoundError:
        import sys

        from market_sim.config import paths

        repo = str(paths.REPO_ROOT)
        if repo not in sys.path:
            sys.path.insert(0, repo)
        import scripts.lib.clean_io as clean_io
    return clean_io


# Default CAMPD bin-assignment CSV, the plant_code -> Plant_Group source used
# to decide which plants are coal/CC. Matches ScenarioConfig.campd_bins_path.
BINS_CSV_DEFAULT: str = str(CAMPD_BINS_CSV)


# Plant groups whose CAMPD outages are derived (coal + combined cycle + gas
# steam, regular and CHP). ``scripts/data/derive_campd_unit_outages.py`` detects unit
# outages for plants in these groups; the per-unit derate then routes each unit
# to its plant bin (CTs are dropped at routing — they dispatch economically). A
# plant qualifies if it has any bin in this set (e.g. Barney M Davis carries both
# a CC and an ST_GAS bin — each unit routes to the matching bin).
QUALIFYING_PLANT_GROUPS: frozenset[str] = frozenset(
    {"COAL", "CC_REGULAR", "CC_CHP", "CT_CHP", "ST_GAS", "ST_CHP"}
)

# Peaker-class ST_GAS plants: patchy / spiky run rate (run only when called),
# so they get NO outage overlay (and no reliability min-gen floor in
# fleet.generators_to_fleet_arrays) — they dispatch purely economically. The
# remaining ST_GAS units run sustained idling / drag patterns and DO get the
# outage + reliability treatment. Excluded from the overlay below.
ST_GAS_PEAKER_PLANTS: frozenset[int] = frozenset(
    {
        # ERCOT
        3504,  # Stryker Creek
        3453,  # Mountain Creek
        3490,  # Graham
        3507,  # Trinidad (TX)
        3576,  # Ray Olinger
        4266,  # Spencer
        # CAISO — the last once-through-cooling steamers, kept on OTC compliance
        # extensions as RMR-style reliability units. CAMPD 2024-25 shows them
        # online only 0.4-2.5% of hours (spiky, run-when-called), so the
        # event-based outage rule would flood them with economic-idleness
        # windows; they dispatch purely economically instead.
        315,  # AES Alamitos LLC units 3-5 (legacy boilers; the colocated
        #   CCGT reports under this ORIS too but is remapped to EIA
        #   62115 — campd.CAMPD_UNIT_PLANT_REMAP)
        335,  # AES Huntington Beach LLC unit 2 (CCGT remapped to 62116)
        350,  # Ormond Beach units 1-2
        # PJM (session pjm-d4-2, 2026-09-10). Admitted on the SAME criterion
        # the registry's existing members satisfy, derived from THEIR measured
        # duty rather than from PJM's residual (rules 1 [R-STRUCT] / 13
        # [R-MEASURED] / 25 [R-ISO-SCOPE]) and declared in
        # docs/PRECOMMIT-pjm-d4-2-stgas-membership-2026-09-10.md before any
        # solve. Qualifying test: CAMPD meter-online share of the plant's
        # ST_GAS slice (>1% of nameplate), pooled over EVERY bench year whose
        # own e_ann/c_ann <= 1.1 (the benchmark's own trust test, applied at
        # slice granularity), < 35%.
        #
        # WHY 35%, AND WHY IT CANNOT BE SWEPT: the threshold is read off the
        # registry's OWN revealed membership in the two ISOs that authored it,
        # with PJM never consulted -- ERCOT admits up to 34.7% (Mountain Creek)
        # and excludes from 36.9% (Lake Hubbard) up; CAISO admits up to 31.0%
        # and excludes from 45.1% up. Both gaps are empty, so any T in
        # (34.7, 36.9] reproduces the pre-existing registry exactly. PJM's own
        # duty distribution has an empty interval from 30.8% to 48.6%, which
        # strictly contains that window: the PJM membership below is IDENTICAL
        # for every threshold in (30.8, 48.6], so the value carries no leverage
        # (rule 21 [R-DOF]: not a free parameter). The competing window --
        # pooling only the two most recent years, which is the evidence the
        # CAISO comment above happens to cite -- is FALSIFIED by this same
        # test: it makes ERCOT's admitted set overlap its excluded set
        # (3504 at 46.3% admitted vs 3491 at 31.2% excluded), so no threshold
        # on that window reproduces the registry at all.
        #
        # FORWARD STORY (rule 13 [R-MEASURED]): peaker-vs-baseload character is
        # a standing attribute of a steam plant -- its duty follows from its
        # heat rate and age against the fleet it bids into, not from any one
        # year's outcome -- so the same census regenerates for a forward year
        # from that year's CAMPD vintage and re-classifies a plant whose
        # economics change. It is an input to the offer/commitment treatment,
        # never a target the dispatch is fitted to.
        #
        # A plant with NO trusted bench year is NOT admitted (fail-closed:
        # character cannot be established from a meter the benchmark distrusts).
        # Pooled duty %, all trusted bench years 2020-2025:
        50279,  # Archbald Power Station     0.0%
        874,  # Joliet 9                     0.7%
        3809,  # Yorktown                    1.6%
        599,  # McKee Run                    1.6%
        3161,  # Eddystone Generating Sta.   1.8%
        3775,  # Clinch River               13.2%
        1571,  # Chalk Point LLC            17.1%
        384,  # Joliet 29                   18.4%
        593,  # Edge Moor                   20.5%
        3148,  # TalenEnergy Martins Creek  22.8%
        3149,  # TalenEnergy Montour        30.8%
        # NOT admitted, and reported rather than argued around: 3138 Brunner
        # Island 48.6%, 3131 New Castle 51.0%, 1353 Shawville 59.8%, 3140
        # Hatfields Ferry 67.6%. 3138 and 3131 carry D-4 per-unit conduct
        # convictions on the committed keeper at ~50% duty, so this change is
        # the LARGEST part of that defect and provably not all of it
        # (docs/RESULT-pjm-d4-1-stgas-merit-order-2026-09-09.md section 9).
    }
)


# Days before each 1-based month in a NON-leap year, so _DAYS_BEFORE_MONTH[m]
# is the 0-based day-of-year of month m's first day ([1]=0 for Jan 1, [2]=31
# for Feb 1, ..., [12]=334 for Dec 1). Index 0 is unused. The model runs on a
# fixed 8760-hour clock keyed to ERCOT-local date with Feb 29 dropped (see
# eia_loader._ercot_hourly_frame), so outage timestamps map onto a non-leap
# calendar.
_DAYS_BEFORE_MONTH: list[int] = [0] * 13
for _m in range(2, 13):
    _DAYS_BEFORE_MONTH[_m] = (
        _DAYS_BEFORE_MONTH[_m - 1] + calendar.monthrange(2023, _m - 1)[1]
    )


def _hour_of_year(month: int, day: int, hour: int) -> int:
    """Map an ERCOT-local (month, day, hour) to a 0-based hour on the clock.

    Uses a non-leap calendar (Feb has 28 days) to match the model's fixed
    8760-hour year. Feb 29 — dropped from the clock in leap years — maps to
    the Mar 1 00:00 boundary (the next hour that exists on the clock); no
    qualifying outage window begins or ends exactly on Feb 29.
    """
    if month == 2 and day >= 29:
        return _DAYS_BEFORE_MONTH[3] * 24  # Mar 1 00:00
    return (_DAYS_BEFORE_MONTH[month] + (day - 1)) * 24 + hour


def outage_hour_mask(
    start: object, stop: object, year: int, hours: int = HOURS_PER_YEAR
) -> np.ndarray:
    """Return a length-``hours`` bool mask of hours covered by ``[start, stop)``.

    ``start`` / ``stop`` are ERCOT-local timestamps (anything pandas can
    coerce). The window is clipped to calendar ``year`` on the model's fixed
    clock: a window that begins in a prior year is covered from hour 0, and
    one that ends in a later year is covered through hour ``hours`` (so a
    year-straddling window such as 2024-12-16 -> 2025-01-03 splits cleanly
    across the two run years). ``stop`` is the return-to-service hour, so the
    interval is half-open and the stop hour itself is not masked. Returns an
    all-False mask when the window does not overlap ``year``.
    """
    mask = np.zeros(hours, dtype=bool)
    start = pd.Timestamp(start)
    stop = pd.Timestamp(stop)
    if stop <= start or start.year > year or stop.year < year:
        return mask
    lo = 0 if start.year < year else _hour_of_year(start.month, start.day, start.hour)
    hi = hours if stop.year > year else _hour_of_year(stop.month, stop.day, stop.hour)
    lo = max(0, min(lo, hours))
    hi = max(0, min(hi, hours))
    if hi > lo:
        mask[lo:hi] = True
    return mask


# Unit-level outage derate. Each unit outage of at least this many days
# derates its model bin's availability by the unit's share of that bin's
# capacity over the window.
#
# Default source is the CAMPD-derived unit-outage extract
# (scripts/data/derive_campd_unit_outages.py): outages detected on each *unit's*
# own CAMPD gross output for the full year, both 2023 and 2024. This replaces
# the hand-maintained data/raw/reference/tx-jan-aug23-unit-outages.csv (kept in the repo
# for reference), which covered only Jan-Aug 2023. The unit-level layer's
# unique job is to catch single-unit outages the facility-summed overlay
# hides: a coal-unit outage at a mixed coal/gas facility (W A Parish 5-8), or
# one unit out at a multi-unit baseload plant. The derivation flags coal
# (baseload) units when their output gaps below ~5% CF, and load-following
# CC/gas-steam units only when they go genuinely dead (event-based), so an
# economically idle CC turbine is not mistaken for an outage. Rows carry full
# (year, start, end) windows; outage_hour_mask clips each to the run year.
UNIT_OUTAGE_CSV: Path = RAW_DATA_DIR / "campd-unit-outages.csv"
UNIT_OUTAGE_MIN_DAYS: int = 5
# W A Parish (3470) coal units; the rest of its units are gas steam, modeled
# under the split code 34702. Combustion turbines (CT_PEAKER / CT_CHP) are
# excluded from the derate entirely, per the unit-availability convention.
_WAP_COAL_UNITS: frozenset[str] = frozenset({"WAP5", "WAP6", "WAP7", "WAP8"})


def _unit_outage_target(
    facility_id: int, unit_id: object, group: object
) -> tuple[int, str] | None:
    """Map a unit-outage row to a model ``(plant_code, plant_group)`` bin.

    Returns ``None`` to skip the row: combustion turbines are excluded, and
    the split plants (W A Parish, Barney M Davis) route each unit to the right
    asset-class bin (coal vs the gas-steam split code 34702 / 49392). A blank
    or ``OTHER`` group is treated as gas steam.
    """
    g = (
        ""
        if group is None or (isinstance(group, float) and np.isnan(group))
        else str(group)
    )
    if g in ("CT_PEAKER", "CT_CHP"):
        return None
    if facility_id == 3470:  # W A Parish: coal units vs gas-steam (code 34702)
        return (3470, "COAL") if str(unit_id) in _WAP_COAL_UNITS else (34702, "ST_GAS")
    if facility_id == 4939:  # Barney M Davis: steam unit 1 (49392) vs CC
        return (49392, "ST_GAS") if str(unit_id) == "1" else (4939, "CC_REGULAR")
    if g in ("CC_REGULAR", "CC_CHP", "COAL"):
        return (facility_id, g)
    return (facility_id, "ST_GAS")


# Mixed CC/ST facilities whose CAMPD unit-outage rows are tagged with a different
# asset class than the model's bin. Ravenswood (2500) is combined-cycle dominant,
# so CAMPD tags every unit CC_REGULAR, but our NYISO fleet carries plant 2500 as a
# single ST_GAS bin (with an HR correction, fleet.MIXED_FACILITY_STEAM_HR). Without
# this override its outage rows route to a (2500, CC_REGULAR) bin that does not
# exist, so the ST_GAS bin reads near-fully-available and over-runs (and the steam
# reliability floor, frac x pmax x availability, over-forces it). Route the plant's
# outages to its ST_GAS bin so the model availability reflects the real downtime.
_FLEET_GROUP_OVERRIDE: dict[int, str] = {2500: "ST_GAS"}


def _generic_unit_outage_target(
    facility_id: int,
    unit_id: object,
    group: object,
    per_unit_crosswalk: bool = False,
) -> tuple[int, str] | None:
    """Map a non-ERCOT unit-outage row to its ``(plant_code, plant_group)``.

    Non-ERCOT ISOs run a per-plant fleet with no split facilities, so each
    unit routes straight to its plant's model group. Combustion turbines are
    excluded from the derate (they dispatch economically), matching the
    ERCOT convention. A handful of mixed CC/ST facilities whose CAMPD class tag
    disagrees with the model bin are remapped via :data:`_FLEET_GROUP_OVERRIDE`.

    ``per_unit_crosswalk`` DISARMS that remap (nyiso-177, rule 19
    ``[R-ONE-MECH]``). The override exists ONLY because the incumbent extract's
    ``_resolve_unit_group`` short-circuit tags every unit at a mixed plant with
    one facility group, so a plant's real per-unit split is unrecoverable at
    read time and has to be enumerated per plant here. The ``-perunit-``
    companion carries that split in the file, which makes the override
    REDUNDANT and, worse, WRONG: it still fires on the repaired rows and drags
    the plant's correctly-routed CC units onto the steam bin, so the CC bin gets
    no derate at all. Measured at Ravenswood (2500) over 2023-2025 (probe
    ``scripts/probes/nyiso177_degradation_root_cause.py``): with the override
    armed on the repaired routing, ``(2500, CC_REGULAR)`` reads availability
    1.000 in every year against the repaired routing's own 0.823 / 0.918 /
    0.923, while ``(2500, ST_GAS)`` moves by at most 0.012 -- i.e. the override
    contributes almost nothing the crosswalk does not already do, and
    everything it does contribute is a mis-route. Two mechanisms for one
    phenomenon: the general one REPLACES the enumeration rather than stacking
    on it.

    It is disarmed ONLY on that path. On the incumbent extract the override is
    load-bearing exactly as its comment says -- there ``(2500, ST_GAS)`` reads
    1.000 without it and the whole plant's downtime lands on a 222.2 MW CC bin
    -- so the off path stays byte-inert.
    """
    g = (
        ""
        if group is None or (isinstance(group, float) and np.isnan(group))
        else str(group)
    )
    if g in ("CT_PEAKER", "CT_CHP"):
        return None
    if facility_id in _FLEET_GROUP_OVERRIDE and not per_unit_crosswalk:
        return (facility_id, _FLEET_GROUP_OVERRIDE[facility_id])
    if not g or g == "OTHER":
        return None
    return (facility_id, g)


def unit_outage_csv_for_iso(
    iso: str | None,
    mixed_gas_routing: bool = False,
    per_unit_crosswalk: bool = False,
    merit_order_guard: bool = False,
    hour_grain: bool = False,
) -> Path:
    """Return the CAMPD unit-outage CSV path for an ISO.

    ERCOT uses the canonical ``campd-unit-outages.csv``; every other ISO uses
    ``campd-unit-outages-<ISO>.csv``, both written by
    ``scripts/data/derive_campd_unit_outages.py --iso <ISO>``.

    ``mixed_gas_routing`` (``ScenarioConfig.unit_outage_mixed_gas_routing``,
    GATED default False; miso-200) selects the ``-unitroute-`` companion written
    by that deriver's ``--mixed-gas-routing`` mode, in which
    :func:`~scripts.data.derive_campd_unit_outages._resolve_unit_group`'s
    ``fac_group`` short-circuit is skipped at a facility carrying two or more
    model gas bins and each unit routes by its own CAMPD ``unitType`` instead.
    A SEPARATE path, never an overwrite, so the off path is byte-inert and the
    two routings are a clean single delta. Falls back to the incumbent extract
    when the companion has not been derived for the ISO.

    ``per_unit_crosswalk`` (``ScenarioConfig.campd_per_unit_attribution``,
    GATED default False; nyiso-175b/176) selects the ``-perunit-`` companion
    written by that deriver's ``--per-unit-crosswalk`` mode, in which EVERY
    unit routes by the shared ``scripts/lib/campd_measured_classes`` crosswalk
    rather than by the plant-level ``fac_group`` short-circuit — the wider
    repair, and the one the tranche artifact's own ``--per-unit-attribution``
    companion is derived against, which is why a single
    ``ScenarioConfig`` field gates both (rule 19 ``[R-ONE-MECH]``). It takes
    precedence over ``mixed_gas_routing``, whose ``-unitroute-`` companion
    repairs a strict subset of the same object and is measurably WRONG where
    the two disagree (nyiso-175b K3: it routes Ravenswood's gas-fired block
    CTs to ``CT_PEAKER`` and drops them from the overlay). Same fallback: the
    incumbent extract when the companion has not been derived.

    ``merit_order_guard`` (``ScenarioConfig.campd_outage_merit_order_guard``,
    GATED default False; nyiso-177) selects the ``-perunitmerit-`` companion:
    the SAME per-unit routing, derived with the deriver's
    ``--merit-order-guard``, so a detected window whose unit's measured SRMC sat
    above the revealed clearing cost of the capacity that WAS running is
    classified as ECONOMIC LAY-UP and leaves the availability envelope (an
    economically idle unit is AVAILABLE; the LP declines it on its own
    economics). Zero free parameters -- ``MERIT_OOM_FRAC`` and
    ``MERIT_RCC_PCTL`` are the deriver's committed constants. It has no meaning
    without ``per_unit_crosswalk`` and is ignored without it, so the two flags
    are one selector over one artifact family. Same discipline again: a
    separate file, never an overwrite, and the incumbent extract when the
    companion is absent.

    ``hour_grain`` (``ScenarioConfig.unit_outage_window_hour_grain``, GATED
    default False; nyiso-229) selects the ``-perunitmerithour-`` companion: the
    SAME per-unit merit-guarded detection, derived with the deriver's
    ``--hour-grain``, so each window carries :data:`_UNIT_OUTAGE_HOUR_COLUMNS`
    and :func:`unit_outage_event_window` reconstructs the DETECTED window
    instead of re-expanding it to 00:00-23:00. It has no meaning without BOTH
    ``per_unit_crosswalk`` and ``merit_order_guard`` and is ignored without
    either, so all three flags are one selector over one artifact family
    (rule 19 ``[R-ONE-MECH]``). Zero free parameters -- the deriver's two
    stop-the-line assertions prove the grain change cannot MOVE a detected
    window, only narrow it. Same discipline once more: a separate file, never an
    overwrite, and the ``-perunitmerit-`` extract when the companion is absent.
    """
    base = (
        UNIT_OUTAGE_CSV
        if (iso is None or iso.upper() == "ERCOT")
        else UNIT_OUTAGE_CSV.with_name(f"campd-unit-outages-{iso.upper()}.csv")
    )
    if per_unit_crosswalk:
        if merit_order_guard:
            if hour_grain:
                # nyiso-229: the detected HOUR grain of the same merit-guarded
                # per-unit windows. Falls through to the day-grain companion
                # when it has not been derived for the ISO, so an ISO adopts the
                # finer grain by deriving its own file and nothing else.
                alt = base.with_name(
                    f"campd-unit-outages-perunitmerithour-"
                    f"{(iso or 'ERCOT').upper()}.csv"
                )
                if alt.exists():
                    return alt
            alt = base.with_name(
                f"campd-unit-outages-perunitmerit-{(iso or 'ERCOT').upper()}.csv"
            )
            if alt.exists():
                return alt
        alt = base.with_name(
            f"campd-unit-outages-perunit-{(iso or 'ERCOT').upper()}.csv"
        )
        if alt.exists():
            return alt
    if not mixed_gas_routing:
        return base
    alt = base.with_name(f"campd-unit-outages-unitroute-{(iso or 'ERCOT').upper()}.csv")
    return alt if alt.exists() else base


def unit_outage_short_csv_for_iso(iso: str | None) -> Path:
    """Return the SHORT (< 5-day) unit-outage CSV path for an ISO.

    Written by ``scripts/data/derive_campd_unit_outages.py --short-windows``:
    baseload-coal full stops of 1-5 days that the standard >= 5-day floor
    excludes, kept only when they survive the derive script's identification
    guards (coal-only detector, unit annual CF >= 0.55, revealed-availability
    in-merit filter). Consumed by :func:`unit_outage_short_derate_factors`
    under ``ScenarioConfig.unit_outage_short_windows``.
    """
    if iso is None or iso.upper() == "ERCOT":
        return UNIT_OUTAGE_CSV.with_name("campd-unit-outages-short.csv")
    return UNIT_OUTAGE_CSV.with_name(f"campd-unit-outages-short-{iso.upper()}.csv")


def unit_outage_short_gas_csv_for_iso(iso: str | None) -> Path:
    """Return the SHORT (< 5-day) GAS unit-outage CSV path for an ISO.

    Written by ``scripts/data/derive_campd_unit_outages.py --short-windows
    --short-window-groups gas --merit-order-guard`` (pjm-d4-4): full stops of
    1-5 days on the gas-side model groups
    (:data:`_SHORT_GAS_GROUPS`) that the standard >= 5-day floor excludes and
    that the coal-scoped short extract has never carried. Consumed by
    :func:`unit_outage_short_derate_factors` under
    ``ScenarioConfig.unit_outage_short_windows_gas``.

    A SEPARATE file from :func:`unit_outage_short_csv_for_iso`, deliberately:
    the coal extract is never rewritten, so the gas family is an independently
    gated object and the coal-only path stays byte-identical.

    Identification differs from the coal scope's and the difference is the
    point (rule 18 ``[R-PHYSICS]``: gate on conduct, not on a class name).
    ``SHORT_BASELOAD_CF`` is a BASELOAD guard — it keeps economic idling out by
    admitting only units that normally run near their ceiling, which a cycling
    combined cycle is not — so the gas scope carries the MERIT-ORDER guard
    instead: the unit's own measured SRMC against the revealed clearing cost of
    the capacity that WAS running. The detector is the event-based dead-span
    rule the >= 5-day gas extract already uses, never the coal sustained-gap
    rule.
    """
    if iso is None or iso.upper() == "ERCOT":
        return UNIT_OUTAGE_CSV.with_name("campd-unit-outages-shortgas.csv")
    return UNIT_OUTAGE_CSV.with_name(f"campd-unit-outages-shortgas-{iso.upper()}.csv")


# Model plant groups the GAS short-window extract covers — the disjoint
# complement of the coal-scoped extract's ``plant_group == "COAL"``. The two
# scopes never share a group, so the two overlays place no capacity on the same
# bin-hour twice (rule 19 ``[R-ONE-MECH]``); combustion turbines are absent
# because :func:`_unit_outage_target` drops them at routing anyway.
_SHORT_GAS_GROUPS: frozenset[str] = frozenset(
    {"CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP"}
)


# Columns unit_outage_derate_factors reads (event-grain; the same columns the
# raw CAMPD unit-outage CSV and the clean unit-outage-events table both carry).
_UNIT_OUTAGE_EVENT_COLUMNS: tuple[str, ...] = (
    "facility_id",
    "unit_id",
    "plant_group",
    "outage_start",
    "outage_end",
    "duration_days",
    "unit_capacity_mw",
)

# OPTIONAL hour-grain columns (caiso-183). The CAMPD unit-outage detector works
# in HOURS (`start = clock[s]`, `last = clock[e - 1]` in
# scripts/data/derive_campd_unit_outages.py) but the extract has always stored
# DAYS, so the reconstruction below re-expanded every window to
# `outage_start` 00:00 -> `outage_end` 23:00 and asserted up to 23 h at each edge
# that the detector never detected — exactly where the event-based contract
# guarantees the neighbouring hour was RUNNING. caiso-181 confirmed that seam at
# 100 % of unit-grain CEMS contradictions, with every contradicted hour within
# 22 h (< 24) of a window boundary in all three years
# (results/calibration/FINDING-caiso181-envelope-depth-2026-08-07.md section 2).
#
# An extract that carries these two columns states the DETECTED hour-of-day of
# its first and last outage hour, and :func:`unit_outage_event_window` uses them.
# They are OPTIONAL because this loader serves all six ISOs and each adopts the
# finer grain by re-deriving its own extract (`--hour-grain`) — an extract
# without them reconstructs exactly as before (rule 25 [R-ISO-SCOPE]).
_UNIT_OUTAGE_HOUR_COLUMNS: tuple[str, ...] = ("outage_start_hour", "outage_end_hour")


def unit_outage_event_window(
    row: object, has_hour_grain: bool
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return one unit-outage event's half-open ``[start, stop)`` window.

    ``stop`` is the return-to-service instant :func:`outage_hour_mask` expects
    (the interval is half-open, so the stop hour itself is not masked).

    With ``has_hour_grain`` and both hours present, the window is the DETECTED
    one — ``[outage_start + start_hour, outage_end + end_hour + 1h)``. Otherwise
    it is the incumbent day-granular reconstruction,
    ``[outage_start, outage_end + 1 day)``.

    The fallback is the incumbent behaviour by **identity**, not approximation:
    an absent grain is exactly ``start_hour = 0`` / ``end_hour = 23``, and
    ``+ (23 + 1) hours`` is ``+ 1 day``. A row whose hours are null falls back
    on its own, so a partially-populated extract degrades per row rather than
    raising.

    Args:
        row: An ``itertuples`` row carrying ``outage_start`` / ``outage_end``.
        has_hour_grain: Whether the source frame carries
            :data:`_UNIT_OUTAGE_HOUR_COLUMNS` (checked once per frame, not per
            row).
    """
    start = pd.Timestamp(row.outage_start)
    end = pd.Timestamp(row.outage_end)
    if has_hour_grain:
        h0, h1 = row.outage_start_hour, row.outage_end_hour
        if not (pd.isna(h0) or pd.isna(h1)):
            return (
                start + pd.Timedelta(hours=int(h0)),
                end + pd.Timedelta(hours=int(h1) + 1),
            )
    return start, end + pd.Timedelta(days=1)


def _has_hour_grain(df: pd.DataFrame) -> bool:
    """Whether an event frame carries both optional hour-grain columns."""
    return all(c in df.columns for c in _UNIT_OUTAGE_HOUR_COLUMNS)


def _load_unit_outage_events(csv_path: Path, iso: str) -> pd.DataFrame | None:
    """Return the ISO's unit-outage events, or ``None`` when no source exists.

    Reads the curated ``unit-outage-events`` clean table (written by
    ``scripts/data/curate_unit_outage_events.py``) when :func:`_use_clean` is set and
    the ISO's partition exists; otherwise reads ``csv_path`` (the raw CAMPD
    unit-outage CSV) directly, returning ``None`` when neither is available.
    """
    if _use_clean():
        clean_io = _clean_io()
        if clean_io.clean_exists("unit-outage-events", iso=iso):
            import pyarrow.parquet as pq

            path = clean_io.paths.clean_path("unit-outage-events", iso=iso)
            # The hour-grain columns are OPTIONAL in the schema (caiso-183), so
            # project them only when this ISO's partition actually carries them
            # — requesting an absent column would raise.
            present = set(pq.read_schema(path).names)
            wanted = ["plant_id", *_UNIT_OUTAGE_EVENT_COLUMNS[1:]]
            wanted += [c for c in _UNIT_OUTAGE_HOUR_COLUMNS if c in present]
            df = clean_io.read_clean("unit-outage-events", iso=iso, columns=wanted)
            return df.rename(columns={"plant_id": "facility_id"})
    if not csv_path.exists():
        return None
    return pd.read_csv(csv_path)


# The bin groups whose LP capacity fleet_to_bins raises to full EIA-860
# nameplate under ScenarioConfig.cc_nameplate_summer_derate — and therefore the
# only groups the ``cc_nameplate_basis`` denominator repair moves. Kept next to
# the consumer so the two lists cannot drift.
_CC_NAMEPLATE_BASIS_GROUPS: tuple[str, ...] = ("CC_REGULAR", "CC_CHP")

# The bin groups the ST-side capacity-basis alignment covers
# (ScenarioConfig.unit_outage_st_capacity_basis, miso-201). These are EXACTLY
# the groups _CC_NAMEPLATE_BASIS_GROUPS above cannot reach, which is why the
# CC-only flag leaves a steam bin's numerator/denominator basis gap open.
_ST_CAPACITY_BASIS_GROUPS: tuple[str, ...] = ("ST_GAS", "ST_CHP")


def _iso_plant_unit_capacity(
    iso: str,
    cc_steam_part_reclass: bool = False,
    retiree_year: int | None = None,
    mid_vintage_exit_carry: bool = False,
) -> dict[tuple[int, str], dict[str, float]]:
    """Vintage-keyed shim over :func:`_iso_plant_unit_capacity_cached`.

    See that function for the contract. The active EIA-860 directory enters the
    cache key here because the fleet this map is built from is vintage-dependent
    (rule 14 ``[R-ACCURATE]``; SPP-38 / ``FINDING-spp-37-order-sensitivity``).
    """
    from market_sim.config.paths import active_eia860_dir

    if not mid_vintage_exit_carry:
        # SPP-48: original arity while off, so the lru_cache key tuple is
        # unchanged and the off path is cache- and byte-identical.
        return _iso_plant_unit_capacity_cached(
            str(active_eia860_dir()), iso, cc_steam_part_reclass
        )
    return _iso_plant_unit_capacity_cached(
        str(active_eia860_dir()),
        iso,
        cc_steam_part_reclass,
        retiree_year,
        mid_vintage_exit_carry,
    )


@lru_cache(maxsize=None)
def _iso_plant_unit_capacity_cached(
    eia860_dir: str,
    iso: str,
    cc_steam_part_reclass: bool = False,
    retiree_year: int | None = None,
    mid_vintage_exit_carry: bool = False,
) -> dict[tuple[int, str], dict[str, float]]:
    """Return ``{(plant_code, plant_group): {normalised_gen_id: pmax_mw}}``.

    ``eia860_dir`` is a **cache key only** — the fleet loaders below resolve the
    active vintage themselves. It is in the signature so a span run that moves
    :data:`~market_sim.config.paths._ACTIVE_EIA_860_DIR` between years cannot
    serve year 1's roster to year 2.

    The PER-UNIT companion of :func:`_iso_plant_capacity`, built from the SAME
    fleet load so the roster and the bin denominator can never disagree about
    what is in the bin (``_iso_plant_capacity`` is literally this map summed).
    Fleet unit ids are ``"<plant_code>_<EIA generator id>"``; the plant prefix is
    stripped and the generator id normalised with
    :func:`_norm_partial_unit_id`, so the key is what a CAMPD unit id has to
    match. Consumed only by :func:`_st_basis_pairmap`.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import (
        load_fleet_from_csv,
        load_retired_within_window,
    )

    iso_config = get_iso_config(iso)
    fleet = load_fleet_from_csv(
        iso, iso_config, cc_steam_part_reclass=cc_steam_part_reclass
    ) + load_retired_within_window(
        iso,
        iso_config,
        year=retiree_year if mid_vintage_exit_carry else None,
        mid_vintage_exit_carry=mid_vintage_exit_carry,
    )
    out: dict[tuple[int, str], dict[str, float]] = {}
    for g in fleet:
        code = int(g.plant_code)
        if code <= 0 or not g.plant_group:
            continue
        uid = str(getattr(g, "unit_id", "") or "")
        gid = uid.split("_", 1)[1] if "_" in uid else uid
        key = _norm_partial_unit_id(gid)
        if not key:
            continue
        bin_units = out.setdefault((code, str(g.plant_group)), {})
        bin_units[key] = bin_units.get(key, 0.0) + float(g.pmax_mw)
    return out


def _st_basis_pairmap(
    df: pd.DataFrame,
    cap: dict[tuple[int, str], float],
    iso: str,
    cc_steam_part_reclass: bool,
    retiree_year: int | None = None,
    mid_vintage_exit_carry: bool = False,
) -> dict[tuple[int, str, str], float]:
    """Return ``{(plant, group, extract_unit_id): fleet pmax_mw}`` for ALIGNED bins.

    ``ScenarioConfig.unit_outage_st_capacity_basis`` (miso-201). The steam-side
    member of the same consistency-repair family as
    ``unit_outage_lp_capacity_basis`` — but where that flag raises the
    DENOMINATOR to meet a numerator the LP had already raised, this one puts the
    NUMERATOR on the basis the LP actually applies it to, because for a steam bin
    nothing raises the denominator in the first place.

    **The defect.** The accumulator derates a bin by
    ``unit_capacity_mw / cap[bin]``. For a steam bin the numerator is the
    extract's per-unit EIA-860 **nameplate** (``capacity_source == eia_exact``)
    or a CEMS **observed peak**, while ``cap[bin]`` is the fleet's **net-summer**
    pmax sum. The removed FRACTION is inflated by ``nameplate / net_summer``, so
    the model removes more MW than went out — the Stony Brook arithmetic
    (NEISO 6081, caiso-184) on the side ``_CC_NAMEPLATE_BASIS_GROUPS`` excludes.
    Measured at Ninemile Point 1403 generator ``5``: nameplate 895.1 MW against
    net summer 742.6 MW, so unit 5 alone out removes ``895.1/1465.4 = 0.611`` of
    the bin against a correct ``742.6/1465.4 = 0.507``.

    **The repair.** Each row's removed MW becomes the fleet unit's own
    ``pmax_mw``. Numerator and denominator then sit on one basis by construction,
    so a bin all of whose units are out lands on EXACTLY 1.0 — never 1.13, never
    0.94.

    **ALL-OR-NOTHING per bin.** A bin is aligned only when EVERY extract unit
    appearing in it resolves 1-1 onto a DISTINCT fleet unit of that bin, by three
    zero-DOF routes in order: an exact normalised-id hit; an UNAMBIGUOUS
    trailing-digit hit (a single fleet unit in the bin carries those digits — the
    deriver's own ``build_capacity_index`` rule); and a unique 1-1 RESIDUAL
    pairing where exactly one extract unit and exactly one fleet unit are left
    over, so the pairing is FORCED rather than chosen (this is what resolves 1403,
    whose CAMPD unit ``4`` cannot match EIA generator ``6(4)`` on digits). A bin
    with any unresolved unit is left ENTIRELY untouched: a half-aligned bin —
    some units on the LP basis, some on nameplate — is less coherent than either
    basis alone, so partial application is REFUSED rather than counted.

    Eligibility is computed over every row this layer sees, so it is a static
    property of the bin and does not shift with the years solved. **Zero free
    parameters** (rule 21 ``[R-DOF]``): every capacity is the fleet's own.
    **Rule 13 ``[R-MEASURED]`` forward-regenerable** — the fleet's pmax and the
    extract's unit ids both exist for a forecast year, and the alignment responds
    to changed conditions because the fleet does.

    Measured coverage at MISO (miso-201 phase 0): 32 of 55 steam bins eligible,
    8,553 of 12,291 MW (69.6 %); the refusals are dominated by an extract/fleet
    UNIT-SET mismatch and by the whole-plant ``eia923_netzero`` synthetic rows,
    both separate open defects this flag deliberately does not touch.
    """
    roster = (  # vintage-keyed
        _iso_plant_unit_capacity(
            iso, cc_steam_part_reclass, retiree_year, mid_vintage_exit_carry
        )
        if mid_vintage_exit_carry
        else _iso_plant_unit_capacity(iso, cc_steam_part_reclass)
    )
    # Every extract unit id that ever appears in each steam bin.
    bin_units: dict[tuple[int, str], set[str]] = {}
    for r in df.itertuples(index=False):
        tgt = _generic_unit_outage_target(int(r.facility_id), r.unit_id, r.plant_group)
        if tgt is None or tgt not in cap:
            continue
        if tgt[1] not in _ST_CAPACITY_BASIS_GROUPS:
            continue
        bin_units.setdefault(tgt, set()).add(str(r.unit_id))

    pairmap: dict[tuple[int, str, str], float] = {}
    for (plant, group), uids in bin_units.items():
        fleet_units = roster.get((plant, group), {})
        if not fleet_units:
            continue
        by_digits: dict[str, list[str]] = {}
        for gid in fleet_units:
            digits = re.sub(r"\D", "", gid)
            if digits:
                by_digits.setdefault(digits, []).append(gid)
        local: dict[str, str] = {}
        unresolved: list[str] = []
        for uid in uids:
            full = _norm_partial_unit_id(uid)
            if full in fleet_units:
                local[uid] = full
                continue
            digits = re.sub(r"\D", "", full)
            cands = by_digits.get(digits) if digits else None
            if cands is not None and len(cands) == 1:
                local[uid] = cands[0]
            else:
                unresolved.append(uid)
        # A fleet unit may be claimed by at most one extract unit; a collision
        # means the join is not 1-1 and the bin is refused.
        claimed = list(local.values())
        if len(set(claimed)) != len(claimed):
            continue
        unmatched = [gid for gid in fleet_units if gid not in set(claimed)]
        if len(unresolved) == 1 and len(unmatched) == 1:
            local[unresolved[0]] = unmatched[0]
            unresolved = []
        if unresolved:
            continue  # fail closed: the whole bin keeps the production basis
        for uid, gid in local.items():
            pairmap[(plant, group, str(uid))] = fleet_units[gid]
    return pairmap


def _iso_plant_capacity(
    iso: str,
    cc_steam_part_reclass: bool = False,
    cc_nameplate_basis: bool = False,
    retiree_year: int | None = None,
    mid_vintage_exit_carry: bool = False,
) -> dict[tuple[int, str], float]:
    """Vintage-keyed shim over :func:`_iso_plant_capacity_cached`.

    See that function for the contract. The active EIA-860 directory enters the
    cache key here because this map is the outage derate DENOMINATOR and the
    fleet it is summed from is vintage-dependent: under
    ``eia860_vintage_tracks_solve_year`` a span run re-points
    :data:`~market_sim.config.paths._ACTIVE_EIA_860_DIR` every year, and a
    vintage-blind key served year 1's denominator against years 2+'s LP fleet —
    the exact numerator/denominator basis split the cached function's own
    docstring says must never happen (rule 14 ``[R-ACCURATE]``; measured in
    ``docs/handoffs/FINDING-spp-37-order-sensitivity-2026-09-12.md``, repaired
    by SPP-38).
    """
    from market_sim.config.paths import active_eia860_dir

    if not mid_vintage_exit_carry:
        # SPP-48: original arity while off — see _iso_plant_unit_capacity.
        return _iso_plant_capacity_cached(
            str(active_eia860_dir()), iso, cc_steam_part_reclass, cc_nameplate_basis
        )
    return _iso_plant_capacity_cached(
        str(active_eia860_dir()),
        iso,
        cc_steam_part_reclass,
        cc_nameplate_basis,
        retiree_year,
        mid_vintage_exit_carry,
    )


@lru_cache(maxsize=None)
def _iso_plant_capacity_cached(
    eia860_dir: str,
    iso: str,
    cc_steam_part_reclass: bool = False,
    cc_nameplate_basis: bool = False,
    retiree_year: int | None = None,
    mid_vintage_exit_carry: bool = False,
) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, plant_group): nameplate_mw}`` for a non-ERCOT ISO.

    ``eia860_dir`` is a **cache key only** — the fleet loaders below resolve the
    active vintage themselves. Call through the :func:`_iso_plant_capacity`
    shim, never directly.

    Non-ERCOT ISOs run a per-plant EIA-860 fleet (no CAMPD bin sheet), so the
    derate denominator — the plant's capacity in its model group — comes from
    the fleet's nameplate summed per ``(plant_code, plant_group)``.

    ``cc_steam_part_reclass`` is forwarded to the fleet load because this
    denominator has to be THE SAME capacity the derate multiplier is applied to
    in the LP. It is not a second mechanism: a flag that moves a generator into
    a ``(plant_code, plant_group)`` bin necessarily moves that bin's capacity,
    and reading the denominator off an un-armed fleet while the LP holds an
    armed one would remove the wrong absolute MW for a given outage (measured at
    NEISO 6081 Stony Brook: a 152 MW 2024 outage against a 209.1 MW un-armed
    denominator removes 72.7 % of an armed 305.1 MW bin = 221.8 MW, i.e. 46 %
    more than actually went out). Default ``False`` keeps every existing caller
    — including PJM's and MISO's own outage loaders — on the identical cache key
    and the identical map.

    ``cc_nameplate_basis`` (``ScenarioConfig.unit_outage_lp_capacity_basis``,
    default ``False``) closes the SAME class of defect for the other flag that
    moves a bin's LP capacity, ``cc_nameplate_summer_derate``. Under that flag
    :func:`~market_sim.data.fleet.campd_bins.fleet_to_bins` divides a CC bin's
    summed net-summer capacity by ``cc_summer_derate_ratio`` so **the LP carries
    full nameplate**, while this map — the denominator the derate share divides
    into — stays on net summer. Numerator and denominator then sit on different
    bases: the extract's ``unit_capacity_mw`` is the EIA-860 **nameplate**
    (``scripts.data.derive_campd_unit_outages.build_capacity_index``, whose own
    docstring states it is written on "the same basis as the model bin
    denominator the derate divides into"), so the removed FRACTION is inflated by
    ``nameplate / net_summer`` and the model removes more MW than went out —
    exactly the Stony Brook arithmetic above, for a different flag. When True the
    CC bins are raised by the same ``cc_summer_derate_ratio`` ``fleet_to_bins``
    uses, so the share is taken against the capacity it is applied to. Measured
    (EIA-860 published net-summer and nameplate), **zero fitted scalars**, and
    monotone: nameplate >= net summer, so a removed fraction can only fall.
    Verified at CAISO (caiso-184): across every EIA-sourced CC bin the extract's
    own ``plant_capacity_mw`` equals this raised denominator EXACTLY (median
    ratio 1.000, against 1.072 on the unraised one).
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import (
        load_fleet_from_csv,
        load_retired_within_window,
    )

    iso_config = get_iso_config(iso)
    # Within-window plant exits dispatch in the backcast fleet, so their
    # capacity must be in the derate denominator — else their unit-outage rows
    # route to a (plant_code, plant_group) absent from this map and are skipped,
    # leaving the injected retiree (e.g. Mystic) un-capped.
    fleet = load_fleet_from_csv(
        iso, iso_config, cc_steam_part_reclass=cc_steam_part_reclass
    ) + load_retired_within_window(
        iso,
        iso_config,
        year=retiree_year if mid_vintage_exit_carry else None,
        mid_vintage_exit_carry=mid_vintage_exit_carry,
    )
    cap: dict[tuple[int, str], float] = {}
    for g in fleet:
        code = int(g.plant_code)
        if code <= 0 or not g.plant_group:
            continue
        cap[(code, g.plant_group)] = cap.get((code, g.plant_group), 0.0) + float(
            g.pmax_mw
        )
    if cc_nameplate_basis:
        # Reproduce fleet_to_bins' CC nameplate raise EXACTLY (campd_bins.py,
        # `cap = cap / _ratio` under cc_nameplate_summer_derate) so this
        # denominator is the capacity the derate multiplier is applied to. Same
        # published ratio, same clamp, same absent-plant fallback — a bin whose
        # plant is missing from the EIA-860 CC sheet is left untouched in BOTH
        # places, so the two can never disagree.
        from market_sim.data.fleet.campd_bins import cc_summer_derate_ratio

        for key in list(cap):
            if key[1] not in _CC_NAMEPLATE_BASIS_GROUPS:
                continue
            ratio = cc_summer_derate_ratio(int(key[0]))
            if ratio is not None and ratio > 0.0:
                cap[key] = cap[key] / ratio
    return cap


#: Plant groups EXCLUDED from ``unit_outage_dispatched_bin_denominator``
#: (miso-266). At these bins the LP's capacity is a DELIBERATE CARVE-OUT of the
#: plant rather than the plant's dispatchable capacity: a CHP bin's tranches
#: carry only the GRID-FACING residual after the behind-the-meter host steam is
#: held out (``fleet/assembly.py``'s ``grid_cap``), so ``cap_LP`` is a fraction
#: of the plant by construction. Measured on the MISO keeper's own 2020 fleet
#: (``scripts/probes/_miso266_routed_bin_exposure.py``): over the bins that
#: actually carry routed extract rows, **every** CC_CHP bin (16 of 16) and
#: **every** ST_CHP bin (27 of 27) has ``denom / cap_LP`` above 1.02, quantized
#: on 1.538 = 1/0.65 and 3.333 = 1/0.30 — the grid shares themselves — up to
#: 10.0 at ST_CHP 1393, whose LP bin is the ``committed`` tranche alone (42.5 MW
#: against a 424.7 MW plant).
#:
#: **AND THE INCUMBENT DENOMINATOR IS RIGHT THERE.** If a CHP unit's output is
#: split host/grid in the same proportion as its plant's, then the grid MW its
#: outage removes is ``ucap x grid_frac``, and the share of the grid bin that is
#: ``ucap x grid_frac / (nameplate x grid_frac) = ucap / nameplate`` — the
#: plant-nameplate denominator the accumulator already uses. Substituting
#: ``cap_LP`` would over-remove by ``1 / grid_frac``, i.e. by up to 10x.
#:
#: So this is TWO PHENOMENA that both present as ``denom != cap_LP``, and rule 19
#: ``[R-ONE-MECH]`` says one mechanism addresses one of them. The flag's identity
#: argument covers a bin whose ``cap_LP`` IS the plant's dispatchable capacity;
#: it does not cover a bin whose ``cap_LP`` is a held-out share, and the scoping
#: is decided on that construction — from a census taken BEFORE any solve, never
#: from a residual (rule 1 ``[R-STRUCT]``). The CHP denominator question is
#: ROUTED, not absorbed: it needs its own identification of how a host/grid split
#: moves under an outage, which no measurement in this repo yet supplies.
#:
#: Mirrors ``fleet.campd_bins._CHP_GROUPS`` and
#: ``model.reserves.spec._ERCOT_POSTURE_CHP_GROUPS``, which enumerate the same
#: three groups for their own reasons.
_DISPATCHED_DENOM_EXCLUDED_GROUPS: frozenset[str] = frozenset(
    {"CC_CHP", "CT_CHP", "ST_CHP"}
)


def _dispatched_denominator(
    reconstructed: dict[tuple[int, str], float],
    lp_bin_capacity: tuple[tuple[tuple[int, str], float], ...],
) -> dict[tuple[int, str], float]:
    """Merge the dispatched roster over the reconstructed one, CHP bins excepted.

    ``ScenarioConfig.unit_outage_dispatched_bin_denominator`` (miso-266). Every
    group outside :data:`_DISPATCHED_DENOM_EXCLUDED_GROUPS` takes its membership
    AND its denominator from the LP's own roster; the CHP groups keep the
    reconstructed entry they have today, unchanged, so the flag is the identity
    on them.

    Args:
        reconstructed: :func:`_iso_plant_capacity`'s map.
        lp_bin_capacity: :func:`lp_bin_capacity_index`'s sorted roster.

    Returns:
        The merged ``{(plant_code, plant_group): MW}`` denominator.
    """
    merged = {
        k: v
        for k, v in reconstructed.items()
        if k[1] in _DISPATCHED_DENOM_EXCLUDED_GROUPS
    }
    merged.update(
        {
            k: v
            for k, v in lp_bin_capacity
            if k[1] not in _DISPATCHED_DENOM_EXCLUDED_GROUPS
        }
    )
    return merged


def lp_bin_capacity_index(
    generators: Sequence[object],
    pmax: np.ndarray | None = None,
) -> tuple[tuple[tuple[int, str], float], ...]:
    """Return the DISPATCHED fleet's own ``(plant_code, plant_group) -> MW`` roster.

    ``ScenarioConfig.unit_outage_dispatched_bin_denominator`` (miso-266). The
    derate denominator this builds is the capacity the derate multiplier is
    ACTUALLY applied to — summed off the very ``generators`` / ``pmax`` the
    overlay then multiplies — rather than :func:`_iso_plant_capacity`'s
    independently-rebuilt map.

    **Why a second construction of the denominator was always a defect.**
    :func:`_iso_plant_capacity`'s own docstring states the invariant: *"this
    denominator has to be THE SAME capacity the derate multiplier is applied to
    in the LP ... reading the denominator off an un-armed fleet while the LP
    holds an armed one would remove the wrong absolute MW"*. It states it about
    one FLAG (``cc_steam_part_reclass``) and patches a second channel by hand
    (``mid_vintage_exit_carry``, SPP-48's Oklaunion case). The invariant is
    general, and the map cannot honour it by reconstruction: it is built from
    ``load_fleet_from_csv`` + ``load_retired_within_window`` alone and is
    therefore blind to every other way the dispatched fleet differs from that
    pair — above all the EXIT-COHORT bins :func:`~market_sim.data.fleet.
    assembly` synthesizes with an ``_r{yyyy}{mm}`` tag (miso-191), which carry
    real dispatched capacity under the SAME ``(plant_code, plant_group)`` key
    the overlay is looked up by and appear in no fleet the map loads.

    The arithmetic that follows is an identity, not a preference. The
    accumulator removes ``share = sum_u ucap_u / denom`` and the LP applies
    ``1 - share`` to ``cap_LP``, so the MW actually removed is
    ``share x cap_LP``; that equals the MW that went out iff
    ``denom == cap_LP``. Measured on the MISO keeper's own 2020 fleet
    (``scripts/probes/_miso266_denominator_vs_lp.py``): ten COAL bins carry
    ``denom / cap_LP`` between 0.414 and 0.814 — R M Schahfer 722.0 MW against
    the LP's 1,625.0 — so one 432 MW unit out removes 60 % of the plant instead
    of 27 %, and three concurrent units remove 242 % and clip a running plant to
    zero (FINDING-miso265 §3: 5.318 TWh metered at ``availability == 0``).

    **Zero free parameters** (rule 21 ``[R-DOF]``) — every MW is the fleet's own
    ``pmax``. **Rule 13 ``[R-MEASURED]`` forward-regenerable**: a forecast fleet
    has ``pmax`` exactly as a backcast one does, and the roster responds to
    changed conditions because the fleet does. **Year-correct by construction**:
    the map is read off the year's own fleet, so a cohort that has retired out
    of a later year leaves the denominator on its own.

    Args:
        generators: The LP's generator objects, in fleet-array row order.
        pmax: Row-aligned ``pmax`` MW. Defaults to each generator's own
            ``pmax_mw``, which is what the fleet arrays are built from.

    Returns:
        A SORTED tuple of ``((plant_code, plant_group), mw)`` pairs — hashable,
        so it crosses the loaders' ``lru_cache`` boundary and keys the cache on
        the fleet it was built from.
    """
    acc: dict[tuple[int, str], float] = {}
    for i, gen in enumerate(generators):
        code = int(getattr(gen, "plant_code", 0) or 0)
        group = str(getattr(gen, "plant_group", "") or "")
        if code <= 0 or not group:
            continue
        mw = float(pmax[i]) if pmax is not None else float(getattr(gen, "pmax_mw", 0.0))
        if not mw > 0.0:
            continue
        acc[(code, group)] = acc.get((code, group), 0.0) + mw
    return tuple(sorted(acc.items()))


@lru_cache(maxsize=None)
def unit_outage_derate_factors(
    year: int,
    hours: int = HOURS_PER_YEAR,
    bins_path: str | Path = BINS_CSV_DEFAULT,
    iso: str = "ERCOT",
    cc_steam_part_reclass: bool = False,
    cc_nameplate_basis: bool = False,
    fleet_status_scope: bool = False,
    st_capacity_basis: bool = False,
    mixed_gas_routing: bool = False,
    per_unit_crosswalk: bool = False,
    merit_order_guard: bool = False,
    per_unit_clip: bool = False,
    extract_basis_share: bool = False,
    hour_grain: bool = False,
    mid_vintage_exit_carry: bool = False,
    lp_bin_capacity: tuple[tuple[tuple[int, str], float], ...] | None = None,
) -> dict[tuple[int, str], np.ndarray]:
    """Return ``{(plant_code, plant_group): (hours,) availability multiplier}``.

    Built from the ISO's unit-level outage extract (ERCOT's
    :data:`UNIT_OUTAGE_CSV` ``campd-unit-outages.csv``, or
    ``campd-unit-outages-<ISO>.csv`` for other ISOs — see
    :func:`unit_outage_csv_for_iso`): every unit outage of at least
    :data:`UNIT_OUTAGE_MIN_DAYS` days whose window overlaps ``year`` derates
    its plant's availability by ``unit_capacity_mw / plant_capacity_mw`` over
    the outage window (concurrent units sum, clipped at full derate). Each
    row's window — the detected hour grain when the extract carries it, else the
    day-granular reconstruction (:func:`unit_outage_event_window`) — is clipped
    to ``year`` on the model clock, so a single multi-year file feeds every
    backcast year. Combustion
    turbines are excluded and rows without a matching plant or capacity are
    skipped. Years the file does not cover get an empty dict.

    The plant-capacity denominator and the unit->plant routing differ by ISO:
    ERCOT reads capacities from its CAMPD bin sheet and routes its split
    facilities (W A Parish, Barney M Davis) to the right asset class; other
    ISOs read per-plant nameplate from the EIA-860 fleet
    (:func:`_iso_plant_capacity`) and route each unit straight to its
    ``(plant_code, plant_group)`` (no split plants, CTs still excluded).
    """
    iso = (iso or "ERCOT").upper()
    csv_path = unit_outage_csv_for_iso(
        iso, mixed_gas_routing, per_unit_crosswalk, merit_order_guard, hour_grain
    )
    df = _load_unit_outage_events(csv_path, iso)
    if df is None:
        return {}
    # Extract-own-basis share (nyiso-196): the bin basis is indexed over the
    # UNFILTERED extract so every unit at the facility counts toward it,
    # whatever its own windows' durations. Non-ERCOT only (see the accumulator).
    basis = (
        _extract_basis_index(df) if (extract_basis_share and iso != "ERCOT") else None
    )
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    return _unit_outage_factors_from_events(
        df,
        year,
        hours,
        bins_path,
        iso,
        cc_steam_part_reclass,
        cc_nameplate_basis,
        fleet_status_scope,
        per_unit_crosswalk=per_unit_crosswalk,
        st_capacity_basis=st_capacity_basis,
        per_unit_clip=per_unit_clip,
        extract_basis=basis,
        mid_vintage_exit_carry=mid_vintage_exit_carry,
        lp_bin_capacity=lp_bin_capacity,
    )


def _fleet_status_index(iso: str) -> dict[int, dict[str, str]] | None:
    """Vintage-keyed shim over :func:`_fleet_status_index_cached`.

    See that function for the contract. The active EIA-860 directory enters the
    cache key here so the docstring's own promise — "a vintage switch is
    honoured" — is true across a span run as well as a single-year one
    (rule 14 ``[R-ACCURATE]``; SPP-38).
    """
    from market_sim.config.paths import active_eia860_dir

    return _fleet_status_index_cached(str(active_eia860_dir()), iso)


@lru_cache(maxsize=None)
def _fleet_status_index_cached(
    eia860_dir: str, iso: str
) -> dict[int, dict[str, str]] | None:
    """Return ``{plant_code: {GENERATOR_ID: STATUS}}`` from the active EIA-860
    operable snapshot, or ``None`` when the parquet is unavailable.

    ``eia860_dir`` is BOTH the cache key and the directory read, so a stale
    global can never desync from the key. Call through the
    :func:`_fleet_status_index` shim, which supplies the active vintage.

    Support for the ``fleet_status_scope`` event filter (miso-186,
    ``unit_outage_fleet_status_scope``): the dispatch fleet keeps only
    ``Status == "OP"`` generators (``fleet/eia860.py``), so this index lets the
    outage accumulator recognize event rows whose unit the fleet does NOT
    model. Reads the SAME active snapshot the fleet loader resolves
    (:func:`market_sim.config.paths.active_eia860_dir`), so the scope always
    matches the fleet's own capacity basis, vintage runs included. Ids are
    normalized ``strip().upper()``. ``iso`` participates in the cache key only
    (the snapshot is ISO-agnostic).
    """
    del iso  # cache-key only; the snapshot is shared across ISOs

    path = Path(eia860_dir) / "eia860_generator_operable.parquet"
    if not path.exists():
        return None
    try:
        df = pd.read_parquet(path, columns=["Plant Code", "Generator ID", "Status"])
    except Exception:  # pragma: no cover - schema drift falls open
        logger.warning("fleet-status index unavailable (%s); filter inert", path)
        return None
    out: dict[int, dict[str, str]] = {}
    for code, gid, st in zip(df["Plant Code"], df["Generator ID"], df["Status"]):
        try:
            c = int(code)
        except (TypeError, ValueError):
            continue
        out.setdefault(c, {})[str(gid).strip().upper()] = str(st).strip().upper()
    return out


def _extract_basis_index(
    df: pd.DataFrame,
) -> dict[tuple[int, str], tuple[bool, float]]:
    """Return ``{(facility_id, plant_group): (single_group, group_basis_mw)}``.

    The extract's OWN capacity basis for each ``(facility, group)`` bin, built
    from the UNFILTERED extract (every row, every year) so a unit whose
    windows all fall below the caller's duration filter still counts toward
    its bin's basis. ``single_group`` is True when the facility carries exactly
    one model group in the extract — then the row's own ``plant_capacity_mw``
    (the deriver's ``fac_cap``, the sum over EVERY CAMPD unit at the facility
    that year, written on every row) is the exact bin basis and
    ``unit_capacity_mw / plant_capacity_mw`` is the published
    ``unit_pct_of_plant``. ``group_basis_mw`` is the fallback for a
    multi-group facility: the sum over the group's DISTINCT unit ids of each
    unit's capacity (max over its rows). Consumed by
    :func:`_unit_outage_factors_from_events` under
    ``ScenarioConfig.unit_outage_extract_basis_share``.
    """
    out: dict[tuple[int, str], tuple[bool, float]] = {}
    if df is None or df.empty:
        return out
    groups_at: dict[int, set[str]] = {}
    unit_cap: dict[tuple[int, str], dict[str, float]] = {}
    for r in df.itertuples(index=False):
        f = int(r.facility_id)
        g = str(r.plant_group)
        groups_at.setdefault(f, set()).add(g)
        ucap = r.unit_capacity_mw
        if pd.isna(ucap) or float(ucap) <= 0.0:
            continue
        d = unit_cap.setdefault((f, g), {})
        u = str(r.unit_id)
        d[u] = max(d.get(u, 0.0), float(ucap))
    for key, d in unit_cap.items():
        out[key] = (len(groups_at[key[0]]) == 1, float(sum(d.values())))
    return out


def _unit_outage_factors_from_events(
    df: pd.DataFrame,
    year: int,
    hours: int,
    bins_path: str | Path,
    iso: str,
    cc_steam_part_reclass: bool = False,
    cc_nameplate_basis: bool = False,
    fleet_status_scope: bool = False,
    per_unit_crosswalk: bool = False,
    st_capacity_basis: bool = False,
    per_unit_clip: bool = False,
    extract_basis: dict[tuple[int, str], tuple[bool, float]] | None = None,
    mid_vintage_exit_carry: bool = False,
    lp_bin_capacity: tuple[tuple[tuple[int, str], float], ...] | None = None,
) -> dict[tuple[int, str], np.ndarray]:
    """Accumulate unit-outage event rows into per-bin availability factors.

    Shared core of :func:`unit_outage_derate_factors` (>= 5-day full stops),
    :func:`unit_outage_short_derate_factors` (< 5-day baseload-coal full stops)
    and :func:`unit_partial_outage_derate_factors` (unit-grain partial-derate
    plateaus): each row derates its plant's ``(plant_code, plant_group)`` bin by
    its removed-capacity share ``removed_mw / plant_capacity_mw`` over the window
    clipped to ``year`` on the model clock; concurrent units sum, clipped at
    full derate.

    A full-stop row removes the unit's whole ``unit_capacity_mw``. A partial
    row carries a ``derate_factor`` column (the measured availability fraction
    the unit ran at during the plateau) and removes only
    ``(1 - derate_factor) x unit_capacity_mw`` — so a plant with two units each
    at half capability derates to half, exactly like two full stops of half the
    plant. The two paths share this accumulator so the partial derate uses the
    identical unit-capacity-share / concurrent-sum / clip-at-full aggregation
    as the >= 5-day overlay.

    ``fleet_status_scope`` (GATED default-off; miso-186,
    ``ScenarioConfig.unit_outage_fleet_status_scope``): drop event rows whose
    unit the dispatch fleet does not model — the unit's EIA-860 operable
    ``Status`` is non-``OP`` in the SAME active snapshot the fleet loader
    keeps ``OP``-only rows from — before accumulating shares. Without it, a
    mothballed (``OA``) unit's terminal CEMS darkness is charged as an outage
    of the plant's OPERATING capacity: the numerator is the dark unit's
    capacity while ``cap[tgt]`` already excludes it, a double-count that can
    zero a running plant (Cottonwood 55358, 2025: the two OA trains' windows
    sum to 1.23 of the modeled OP half and clip it to 0.0 through the scarce
    set, against the plant's own CAMPD record of 526 MW in all 47 scarce
    hours — FINDING-miso186). Unmatched unit ids fail OPEN (row kept), so
    retirees dispatched from the retired-within-window sheet — absent from
    the operable parquet — keep their legitimate windows. Non-ERCOT only (the
    ERCOT branch caps on its own CAMPD bin sheet, a different basis).

    ``per_unit_clip`` (GATED default-off; miso-202,
    ``ScenarioConfig.unit_outage_per_unit_clip``): enforce the invariant that
    ONE UNIT CANNOT BE MORE THAN 100 % OUT OF SERVICE before the units are
    summed into the bin. :func:`unit_outage_event_window` reconstructs a
    day-granular row as ``[outage_start, outage_end + 1 day)``, so two windows
    of the SAME unit that share a boundary date both cover that day and this
    accumulator — which sums row shares rather than unioning them — subtracts
    the unit's capacity TWICE for 24 h. Across MISO's committed extracts every
    one of the 845 same-unit window overlaps is EXACTLY 24.0 h (std5d 648,
    lay-up 197, short 0), the fingerprint of the ``+ 1 day`` artifact and of
    nothing else. With the flag on, each unit's removed MW accumulates into its
    own array, is clipped at that unit's own capacity, and only then enters the
    bin — a ceiling on a sum, not a window-merging heuristic, so it is the
    identity except in the physically impossible case and can only ever remove
    LESS. Zero free parameters (rule 21 ``[R-DOF]``).

    ``extract_basis`` (GATED default-off; nyiso-196,
    ``ScenarioConfig.unit_outage_extract_basis_share``): take the removed
    FRACTION on the extract's OWN capacity basis — ``unit_capacity_mw`` over
    the bin's basis from :func:`_extract_basis_index` (the row's
    ``plant_capacity_mw`` at a single-group facility, i.e. the published
    ``unit_pct_of_plant``) — instead of over the fleet's ``cap[bin]``. The
    numerator and the denominator then come from ONE construction (the
    deriver's ``build_capacity_index`` / ``fac_cap``), so the fraction no
    longer depends on how the extract's per-unit capacity relates to the
    fleet's net-summer bin sum. Measured at Cricket Valley 57185 (NYISO): the
    CAMPD stack ids ``U001``-``U003`` match EIA-860 generator ids ``U001``-
    ``U003``, which are the plant's STEAM turbines (prime mover CA, 174.2 MW
    each) — the id collision skips the CT steam-coupling augmentation, so the
    extract books each 1x1 block at 174.2 MW (``eia_exact``, plant 522.6) and
    the LP accumulator divides that by the 1,016.8 MW net-summer bin: one block
    out removes 17.1 % of the plant against the physical 33.3 %, and all three
    blocks out leave 48.6 % available at a dark plant. On the extract's own
    basis the same row reads 174.2 / 522.6 = 33.3 %. COMBINED-CYCLE bins only
    (:data:`_CC_NAMEPLATE_BASIS_GROUPS`): a CEMS unit at a combined cycle is a
    1x1 block or a steam-coupled CT whose share of the plant the deriver's
    ``fac_cap`` states, which is the physics this share encodes; steam bins
    keep their own numerator alignment (``st_capacity_basis``, whose bins are
    disjoint from these — rule 19 ``[R-ONE-MECH]``). Non-ERCOT only (the ERCOT
    branch caps on its CAMPD bin sheet and routes split facilities, a basis the
    extract's ``facility_id`` does not address); a bin absent from the index
    keeps ``cap[bin]``. Mutually exclusive with ``cc_nameplate_basis``, which
    acts on the same CC bins' share (two constructions of one share never
    stack).
    ``lp_bin_capacity`` (GATED default-off; miso-266,
    ``ScenarioConfig.unit_outage_dispatched_bin_denominator``): REPLACE the
    reconstructed ``cap`` map with the DISPATCHED fleet's own per-bin capacity
    (:func:`lp_bin_capacity_index`), which is the capacity this factor is then
    applied to — **at every group except the CHP bins, whose ``cap_LP`` is a
    held-out grid share rather than the plant's dispatchable capacity and whose
    incumbent nameplate denominator is the correct one**
    (:data:`_DISPATCHED_DENOM_EXCLUDED_GROUPS`; the merge is
    :func:`_dispatched_denominator`). One map for the roster and for the divide,
    because they are the same object: a bin the LP does not dispatch has nothing
    to derate, and a bin it does dispatch must be derated against what it
    dispatches. That closes the two halves of one defect at once —

    * the DENOMINATOR, where the reconstructed map is blind to the exit-cohort
      bins ``fleet.assembly`` synthesizes under the SAME ``(plant_code,
      plant_group)`` key the overlay is looked up by (miso-191's
      ``_r{yyyy}{mm}`` tag). Measured on the MISO 2020 keeper fleet: ten COAL
      bins at ``cap / cap_LP`` of 0.414-0.814, which over-remove by up to 2.4x
      and clip running plants to zero (FINDING-miso265 §3);
    * MEMBERSHIP, where a bin the LP dispatches but the reconstructed map lacks
      is SKIPPED and rides un-derated through its own measured outage — the
      pathology SPP-48 patched for one channel by hand
      (``mid_vintage_exit_carry``'s Oklaunion 127).

    Non-ERCOT only, like every sibling basis flag (the ERCOT branch caps on its
    own CAMPD bin sheet and routes split facilities). Mutually exclusive with
    ``cc_nameplate_basis`` and ``extract_basis``: all three set the denominator,
    and two constructions of one denominator never stack (rule 19
    ``[R-ONE-MECH]``) — ``cc_nameplate_basis`` in particular reconstructs the
    very ``fleet_to_bins`` raise that is ALREADY inside the ``pmax`` this flag
    reads, so stacking them would double-apply it.
    """
    if lp_bin_capacity is not None and (
        cc_nameplate_basis or extract_basis is not None
    ):
        raise ValueError(
            "unit_outage_dispatched_bin_denominator is mutually exclusive with "
            "unit_outage_lp_capacity_basis and unit_outage_extract_basis_share "
            "(rule 19 [R-ONE-MECH]): all three set the derate denominator — arm "
            "exactly one construction"
        )
    if extract_basis is not None and cc_nameplate_basis:
        raise ValueError(
            "unit_outage_extract_basis_share is mutually exclusive with "
            "unit_outage_lp_capacity_basis (rule 19 [R-ONE-MECH]): both act on "
            "the combined-cycle bins' removed share — arm exactly one construction"
        )
    if iso == "ERCOT":
        from market_sim.data.fleet import load_campd_bins

        bins = load_campd_bins(str(bins_path))
        cap = {
            (int(c), str(g)): float(m)
            for c, g, m in zip(
                bins["Plant_Code"], bins["Plant_Group"], bins["capacity_mw"]
            )
            if m and m > 0
        }
        target_fn = _unit_outage_target
    else:
        cap = (
            _iso_plant_capacity(
                iso,
                cc_steam_part_reclass,
                cc_nameplate_basis,
                int(year),
                mid_vintage_exit_carry,
            )
            if mid_vintage_exit_carry
            else _iso_plant_capacity(iso, cc_steam_part_reclass, cc_nameplate_basis)
        )
        # rule 19 [R-ONE-MECH]: the per-plant _FLEET_GROUP_OVERRIDE enumeration
        # is DISARMED on the per-unit-crosswalk path, where the file already
        # carries each unit's own bin (nyiso-177).
        if lp_bin_capacity is not None:
            # miso-266: the DISPATCHED fleet's own roster REPLACES the
            # reconstructed map — for membership and for the divide alike, since
            # they are one object (see the docstring). Built from the very
            # generators/pmax this factor is applied to, so `denom == cap_LP`
            # holds by construction rather than by reconstruction.
            #
            # EXCEPT at the CHP bins, where `cap_LP` is a held-out grid share
            # rather than the plant's dispatchable capacity and the incumbent
            # nameplate denominator is the correct one — see
            # `_DISPATCHED_DENOM_EXCLUDED_GROUPS`. Those bins keep `cap[bin]`
            # exactly, so the flag is the identity on them and a CHP bin absent
            # from the roster is still skipped exactly as it is today.
            cap = _dispatched_denominator(cap, lp_bin_capacity)
        target_fn = partial(
            _generic_unit_outage_target, per_unit_crosswalk=per_unit_crosswalk
        )
    # ST-side capacity-basis alignment (ScenarioConfig.unit_outage_st_capacity_basis,
    # miso-201). Non-ERCOT only: the ERCOT branch caps on its own CAMPD bin sheet,
    # a different basis with no per-unit fleet roster to align onto. Built AFTER
    # target_fn so it shares whichever routing this call is using — including the
    # nyiso-177 per-unit-crosswalk path.
    st_pairmap: dict[tuple[int, str, str], float] = {}
    if st_capacity_basis and iso != "ERCOT":
        st_pairmap = (
            # SPP-48: original arity while off, so the off path is unchanged.
            _st_basis_pairmap(
                df, cap, iso, cc_steam_part_reclass, int(year), mid_vintage_exit_carry
            )
            if mid_vintage_exit_carry
            else _st_basis_pairmap(df, cap, iso, cc_steam_part_reclass)
        )
    has_derate = "derate_factor" in df.columns
    # Checked once per frame: an extract re-derived with --hour-grain states the
    # detected window in hours, otherwise the day-granular reconstruction stands
    # (caiso-183; see :func:`unit_outage_event_window`).
    has_hours = _has_hour_grain(df)
    status_idx = (
        _fleet_status_index(iso) if (fleet_status_scope and iso != "ERCOT") else None
    )
    sums: dict[tuple[int, str], np.ndarray] = {}
    # miso-202 per-unit clip: {(bin, unit_id): [removed_mw array, unit capacity]}.
    # Populated INSTEAD of writing straight into ``sums`` when the flag is on, so
    # the off path allocates nothing and stays byte-inert.
    per_unit: dict[tuple[tuple[int, str], str], list] = {}
    for r in df.itertuples(index=False):
        tgt = target_fn(int(r.facility_id), r.unit_id, r.plant_group)
        if tgt is None or tgt not in cap:
            continue
        if status_idx is not None:
            st = status_idx.get(int(r.facility_id), {}).get(
                str(r.unit_id).strip().upper()
            )
            if st is not None and st != "OP":
                continue  # unit not in the fleet's OP capacity basis
        ucap = r.unit_capacity_mw
        if pd.isna(ucap) or float(ucap) <= 0.0:
            continue
        # Put the removed MW on the LP's own basis where this bin is aligned.
        # Absent from the pairmap => the bin was refused (or the flag is off) and
        # the production numerator stands, so the change is strictly scoped.
        aligned = st_pairmap.get((tgt[0], tgt[1], str(r.unit_id)))
        if aligned is not None:
            ucap = aligned
        # Fraction of the unit's capacity removed over the window: a full stop
        # removes all of it; a partial plateau removes (1 - derate_factor).
        removed_frac = 1.0
        if has_derate:
            dfac = r.derate_factor
            if pd.isna(dfac):
                continue
            removed_frac = min(max(1.0 - float(dfac), 0.0), 1.0)
            if removed_frac <= 0.0:
                continue
        w_start, w_stop = unit_outage_event_window(r, has_hours)
        mask = outage_hour_mask(w_start, w_stop, year, hours)
        if not mask.any():
            continue
        # Denominator of the removed share: the fleet bin by default; under
        # ``extract_basis`` a COMBINED-CYCLE bin's capacity on the extract's
        # OWN basis (the row's ``plant_capacity_mw`` at a single-group
        # facility, else the group's distinct-unit sum) — see the docstring.
        # CC bins only (_CC_NAMEPLATE_BASIS_GROUPS): a CEMS unit at a combined
        # cycle is a block whose share of the plant the deriver's fac_cap
        # states; steam bins keep their own numerator alignment
        # (st_capacity_basis, rule 19). A bin the index does not carry keeps
        # ``cap[tgt]``.
        denom = cap[tgt]
        if extract_basis is not None and tgt[1] in _CC_NAMEPLATE_BASIS_GROUPS:
            ebasis = extract_basis.get((int(r.facility_id), str(r.plant_group)))
            if ebasis is not None:
                single_group, group_basis = ebasis
                row_pc = getattr(r, "plant_capacity_mw", None)
                if (
                    single_group
                    and row_pc is not None
                    and not pd.isna(row_pc)
                    and float(row_pc) > 0.0
                ):
                    denom = float(row_pc)
                elif group_basis > 0.0:
                    denom = group_basis
        if per_unit_clip:
            # Hold this unit's removed MW apart from the bin so it can be capped
            # at the unit's own capacity below. ``ucap`` is the same value the
            # unclipped path divides by ``denom``, so the two paths differ ONLY
            # where a unit's own rows overlap — the boundary-day double-count.
            slot = per_unit.setdefault(
                (tgt, str(r.unit_id)), [np.zeros(hours), 0.0, denom]
            )
            slot[0][mask] += removed_frac * float(ucap)
            # A unit is at most fully out. Rows for one unit can differ in
            # ``ucap`` (a partial plateau carries the same unit capacity but a
            # fractional ``removed_frac``; an extract spanning a re-rating can
            # carry two capacities), so the ceiling is the LARGEST capacity the
            # unit's own rows claim — never a smaller one, which would clip a
            # legitimate single window.
            slot[1] = max(slot[1], float(ucap))
            slot[2] = denom
            sums.setdefault(tgt, np.zeros(hours))
            continue
        arr = sums.setdefault(tgt, np.zeros(hours))
        arr[mask] += removed_frac * float(ucap) / denom
    for (tgt, _uid), (removed_mw, unit_cap, denom) in per_unit.items():
        if unit_cap <= 0.0:
            continue
        sums[tgt] += np.minimum(removed_mw, unit_cap) / denom
    return {k: np.clip(1.0 - v, 0.0, 1.0) for k, v in sums.items()}


@lru_cache(maxsize=None)
def unit_outage_short_derate_factors(
    year: int,
    hours: int = HOURS_PER_YEAR,
    bins_path: str | Path = BINS_CSV_DEFAULT,
    iso: str = "ERCOT",
    cc_steam_part_reclass: bool = False,
    cc_nameplate_basis: bool = False,
    fleet_status_scope: bool = False,
    st_capacity_basis: bool = False,
    per_unit_clip: bool = False,
    extract_basis_share: bool = False,
    gas_scope: bool = False,
    mid_vintage_exit_carry: bool = False,
    lp_bin_capacity: tuple[tuple[tuple[int, str], float], ...] | None = None,
) -> dict[tuple[int, str], np.ndarray]:
    """Return short-window (< 5-day) unit-outage availability multipliers.

    The sub-floor companion of :func:`unit_outage_derate_factors`, gated by
    ``ScenarioConfig.unit_outage_short_windows``: baseload-coal full stops of
    1-5 days from ``campd-unit-outages-short-<ISO>.csv`` (built by
    ``scripts/data/derive_campd_unit_outages.py --short-windows``, which enforces
    the identification guards — coal-only detector, unit annual CF >= 0.55,
    revealed-availability in-merit filter — so economic idling never enters).
    Defensively re-filters to ``plant_group == "COAL"`` and
    ``duration_days < UNIT_OUTAGE_MIN_DAYS`` so the two overlays stay disjoint
    (a window >= the floor belongs to the standard overlay and is dropped
    here). ISOs without the file get an empty dict (no effect).

    ``gas_scope`` (``ScenarioConfig.unit_outage_short_windows_gas``, pjm-d4-4)
    additionally reads the GAS companion
    (:func:`unit_outage_short_gas_csv_for_iso`) and concatenates its rows before
    the shared accumulator runs, so the gas family enters on exactly the same
    arithmetic and the same capacity denominator as the coal one. The two
    scopes are disjoint by PLANT GROUP (``COAL`` vs :data:`_SHORT_GAS_GROUPS`)
    and both are disjoint from the >= 5-day overlay by DURATION, so nothing is
    counted twice (rule 19 ``[R-ONE-MECH]``). ``gas_scope`` widens a DISCARD; it
    stacks nothing on the coal scope. An ISO without the gas file gets the coal
    scope unchanged.
    """
    iso = (iso or "ERCOT").upper()
    csv_path = unit_outage_short_csv_for_iso(iso)
    gas_path = unit_outage_short_gas_csv_for_iso(iso) if gas_scope else None
    have_gas = gas_path is not None and gas_path.exists()
    if not csv_path.exists() and not have_gas:
        return {}
    frames: list[pd.DataFrame] = []
    if csv_path.exists():
        frames.append(pd.read_csv(csv_path))
    if have_gas:
        frames.append(pd.read_csv(gas_path))
    df = frames[0] if len(frames) == 1 else pd.concat(frames, ignore_index=True)
    # Built over the UNFILTERED frame, exactly as the coal-only path built it
    # over the unfiltered coal extract (nyiso-196) — so the off path, whose
    # frame IS that file, is byte-inert.
    basis = (
        _extract_basis_index(df) if (extract_basis_share and iso != "ERCOT") else None
    )
    scopes = {"COAL"} | (set(_SHORT_GAS_GROUPS) if gas_scope else set())
    df = df[
        (df["duration_days"] < UNIT_OUTAGE_MIN_DAYS) & (df["plant_group"].isin(scopes))
    ]
    return _unit_outage_factors_from_events(
        df,
        year,
        hours,
        bins_path,
        iso,
        cc_steam_part_reclass,
        cc_nameplate_basis,
        fleet_status_scope,
        st_capacity_basis=st_capacity_basis,
        per_unit_clip=per_unit_clip,
        extract_basis=basis,
        mid_vintage_exit_carry=mid_vintage_exit_carry,
        lp_bin_capacity=lp_bin_capacity,
    )


def unit_layup_csv_for_iso(iso: str | None) -> Path:
    """Return the ECONOMIC-LAYUP companion CSV path for an ISO.

    Written by ``scripts/data/derive_campd_unit_outages.py --merit-order-guard``
    (``campd-unit-outages-layup[-<ISO>].csv``): detected >= 5-day full-stop
    windows the merit-order guard RECLASSIFIED as economic lay-up — the unit's
    own measured SRMC sat above the revealed clearing cost for >=
    ``MERIT_OOM_FRAC`` of the window (scripts/lib/outage_detect.py). These
    windows deliberately stay OUT of the availability envelope (an economically
    idle unit is available; the LP declines it on its own economics); the sole
    engine consumer is the must-run floor mask
    (``ScenarioConfig.mustrun_layup_window_mask``), which reads them as the
    measured hours in which the plant's self-commitment driver is absent.
    """
    if iso is None or iso.upper() == "ERCOT":
        return UNIT_OUTAGE_CSV.with_name("campd-unit-outages-layup.csv")
    return UNIT_OUTAGE_CSV.with_name(f"campd-unit-outages-layup-{iso.upper()}.csv")


@lru_cache(maxsize=None)
def unit_layup_removed_fractions(
    year: int,
    hours: int = HOURS_PER_YEAR,
    bins_path: str | Path = BINS_CSV_DEFAULT,
    iso: str = "ERCOT",
    cc_steam_part_reclass: bool = False,
    cc_nameplate_basis: bool = False,
    st_capacity_basis: bool = False,
    per_unit_clip: bool = False,
    extract_basis_share: bool = False,
    lp_bin_capacity: tuple[tuple[tuple[int, str], float], ...] | None = None,
) -> dict[tuple[int, str], np.ndarray]:
    """Return ``{(plant_code, plant_group): (hours,) laid-up capacity fraction}``.

    The measured LAY-UP share of each plant's capacity by hour, from the
    merit-order guard's economic-lay-up companion extract
    (:func:`unit_layup_csv_for_iso`). Built through the SAME accumulator as
    :func:`unit_outage_derate_factors` — identical unit->plant routing
    (CTs excluded), identical model-fleet capacity denominator, identical
    window clipping and concurrent-unit summing — so a lay-up share and an
    outage share for the same plant sit on the same basis and are additive
    (a >= 5-day gap window is classified as exactly one of the two by the
    derive script). NOT an availability layer: the sole consumer is the
    must-run floor mask (``ScenarioConfig.mustrun_layup_window_mask``), which
    subtracts this share from the floor's ``pmax x availability`` clip basis.
    ISOs or years without the file get an empty dict (no effect).
    """
    iso = (iso or "ERCOT").upper()
    csv_path = unit_layup_csv_for_iso(iso)
    if not csv_path.exists():
        return {}
    df = pd.read_csv(csv_path)
    # Same duration floor as the standard overlay: the lay-up companion is a
    # reclassification of the >= 5-day detector output, re-filtered defensively.
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    # st_capacity_basis moves with the standard overlay by necessity, not by
    # choice: this loader's contract is that "a lay-up share and an outage share
    # for the same plant sit on the same basis and are additive". Aligning one
    # numerator and not the other would break exactly that invariant, so the two
    # layers share the flag (rule 19 [R-ONE-MECH]).
    factors = _unit_outage_factors_from_events(
        df,
        year,
        hours,
        bins_path,
        iso,
        cc_steam_part_reclass,
        cc_nameplate_basis,
        False,
        st_capacity_basis=st_capacity_basis,
        # Same rule-19 [R-ONE-MECH] reasoning as st_capacity_basis above: this
        # loader's contract is that a lay-up share and an outage share for the
        # same plant sit on the same basis and are additive, so clipping one
        # layer's per-unit removal and not the other would break exactly that
        # invariant. Phase-0 N-2 measures 197 same-unit overlaps in MISO's
        # lay-up extract, so the layer is not merely eligible — it is live.
        per_unit_clip=per_unit_clip,
        # nyiso-196: the extract-basis share moves with the standard overlay for
        # the same additivity contract — the lay-up companion is written by the
        # same deriver on the same fac_cap basis, so its share must be taken
        # over the same denominator as the outage share it adds to.
        extract_basis=(
            _extract_basis_index(df)
            if (extract_basis_share and iso != "ERCOT")
            else None
        ),
        lp_bin_capacity=lp_bin_capacity,
    )
    # The accumulator returns availability multipliers (1 - removed share);
    # this loader's contract is the REMOVED (laid-up) share itself.
    return {k: 1.0 - v for k, v in factors.items()}


def unit_partial_outage_csv_for_iso(iso: str | None) -> Path:
    """Return the UNIT-GRAIN partial-derate plateau CSV path for an ISO.

    Distinct from the ERCOT PLANT-grain :data:`PARTIAL_OUTAGE_CSV`
    (``campd-partial-outages.csv``): this is the unit-grain partial-plateau
    extract (``campd-partial-outages-<ISO>.csv``, written by
    ``scripts/data/derive_campd_unit_outages.py --partial-windows``), consumed by
    :func:`unit_partial_outage_derate_factors` under
    ``ScenarioConfig.unit_partial_outage_windows``. Always ISO-suffixed —
    ERCOT keeps the plant-grain path and has no unit-grain partial file, so
    ``ERCOT`` resolves to a name that does not collide with the plant-grain
    file and simply does not exist (empty derate).
    """
    return UNIT_OUTAGE_CSV.with_name(
        f"campd-partial-outages-{(iso or 'ERCOT').upper()}.csv"
    )


@lru_cache(maxsize=None)
def unit_partial_outage_derate_factors(
    year: int,
    hours: int = HOURS_PER_YEAR,
    bins_path: str | Path = BINS_CSV_DEFAULT,
    iso: str = "ERCOT",
    cc_steam_part_reclass: bool = False,
    cc_nameplate_basis: bool = False,
    fleet_status_scope: bool = False,
    st_capacity_basis: bool = False,
    per_unit_clip: bool = False,
    extract_basis_share: bool = False,
    lp_bin_capacity: tuple[tuple[tuple[int, str], float], ...] | None = None,
) -> dict[tuple[int, str], np.ndarray]:
    """Return unit-grain partial-derate plateau availability multipliers.

    The partial-derate companion of :func:`unit_outage_short_derate_factors`,
    gated by ``ScenarioConfig.unit_partial_outage_windows``: sustained
    CF-ceiling plateaus (a unit running at a depressed ceiling — half its
    capability out — which never reaches zero, so no full-stop window can
    represent it) from ``campd-partial-outages-<ISO>.csv`` (built by
    ``scripts/data/derive_campd_unit_outages.py --partial-windows``, which enforces
    the same identification guards as the short windows — coal-only detector,
    the when-operable baseload CF >= 0.55 screen, the revealed-availability
    in-merit filter — plus the plant-level partial detector's frozen plateau
    constants). Each row carries a ``derate_factor`` (the measured availability
    fraction during the plateau); the shared accumulator removes
    ``(1 - derate_factor) x unit_capacity`` from the plant bin, aggregated by
    unit-capacity share with concurrent units summed and clipped at full derate
    — identical to the >= 5-day overlay. Returns ``{(plant_code, plant_group):
    (hours,) multiplier}``. ISOs without the file get an empty dict (no effect).

    Keyed and applied per ``(plant_code, plant_group)`` like the unit-outage
    derate, NOT per ``plant_code`` like the ERCOT-only plant-grain
    :func:`partial_outage_derate_factors` — the plant-grain path over-fires on
    a cycling fleet and stays ERCOT-scoped in ``fleet.py``.
    """
    iso = (iso or "ERCOT").upper()
    csv_path = unit_partial_outage_csv_for_iso(iso)
    if not csv_path.exists():
        return {}
    df = pd.read_csv(csv_path)
    return _unit_outage_factors_from_events(
        df,
        year,
        hours,
        bins_path,
        iso,
        cc_steam_part_reclass,
        cc_nameplate_basis,
        fleet_status_scope,
        st_capacity_basis=st_capacity_basis,
        per_unit_clip=per_unit_clip,
        extract_basis=(
            _extract_basis_index(df)
            if (extract_basis_share and iso != "ERCOT")
            else None
        ),
        lp_bin_capacity=lp_bin_capacity,
    )


def unit_outage_maxgen_csv_for_iso(
    iso: str | None, mixed_gas_routing: bool = False
) -> Path:
    """Return the declared-event-window (maxgen) unit-derate CSV path.

    Written by ``scripts/data/derive_campd_maxgen_outages.py --iso <ISO>``: CAMPD
    revealed unit derates inside the ISO's declared capacity-emergency windows
    (the ``maxgen-events`` registry), consumed by
    :func:`unit_outage_maxgen_derate_factors` under
    ``ScenarioConfig.unit_outage_maxgen_events``. Always ISO-suffixed.

    ``mixed_gas_routing`` (miso-200) selects the ``-unitroute-`` companion, for
    the same reason and on the same terms as
    :func:`unit_outage_csv_for_iso`: this layer shares the SAME
    ``_resolve_unit_group`` routing, so it carries the SAME mis-attribution and
    must move with it -- a unit routed to ``ST_GAS`` in one layer and
    ``CC_REGULAR`` in the other would leave the object half-repaired
    (rule 19 ``[R-ONE-MECH]``).
    """
    iso_u = (iso or "ERCOT").upper()
    base = UNIT_OUTAGE_CSV.with_name(f"campd-unit-outages-maxgen-{iso_u}.csv")
    if not mixed_gas_routing:
        return base
    alt = base.with_name(f"campd-unit-outages-maxgen-unitroute-{iso_u}.csv")
    return alt if alt.exists() else base


@lru_cache(maxsize=None)
def unit_outage_maxgen_derate_factors(
    year: int,
    hours: int = HOURS_PER_YEAR,
    iso: str = "ERCOT",
    cc_steam_part_reclass: bool = False,
    cc_nameplate_basis: bool = False,
    mixed_gas_routing: bool = False,
    mid_vintage_exit_carry: bool = False,
    lp_bin_capacity: tuple[tuple[tuple[int, str], float], ...] | None = None,
) -> dict[tuple[int, str], np.ndarray]:
    """Return declared-event-window revealed-derate availability multipliers.

    The third window shape of the measured unit-availability family, gated by
    ``ScenarioConfig.unit_outage_maxgen_events``: per-unit MW derates revealed
    by each unit's own CAMPD trace inside the ISO's *declared* capacity-
    emergency windows (``campd-unit-outages-maxgen-<ISO>.csv``, built by
    ``scripts/data/derive_campd_maxgen_outages.py``, which enforces the frozen
    identification guards — registry-window scope clipped to the declared
    start/end, the $150 DA in-merit certificate, the ±45-day capability
    basis with best-event-hour credit, and disjointness vs the std/short
    extracts).

    Unlike the std/short/partial loaders this one is CLASS-AGNOSTIC — no
    CT_PEAKER/CT_CHP exclusion — because the declared-window + in-merit
    certificate is precisely the identification under which an idle peaker is
    evidence of unavailability rather than economics (the deriver's guards, not
    this loader, carry that logic), and the registry channel is the only one
    that can represent the measured CT/CC event-window leg. Rows carry a
    ``derate_mw`` (the removed MW — NOT a full-stop unit capacity) over an
    hour-granular half-open ``[window_start, window_end)`` on the model clock;
    each row derates its plant's ``(plant_code, plant_group)`` bin by
    ``derate_mw / plant_capacity``; concurrent units sum, clipped at full
    derate. ISOs without the file get an empty dict (no effect).
    """
    iso = (iso or "ERCOT").upper()
    csv_path = unit_outage_maxgen_csv_for_iso(iso, mixed_gas_routing)
    if not csv_path.exists():
        return {}
    df = pd.read_csv(csv_path)
    if lp_bin_capacity is not None and cc_nameplate_basis:
        raise ValueError(
            "unit_outage_dispatched_bin_denominator is mutually exclusive with "
            "unit_outage_lp_capacity_basis (rule 19 [R-ONE-MECH]): both set the "
            "derate denominator — arm exactly one construction"
        )
    cap = (
        _iso_plant_capacity(
            iso,
            cc_steam_part_reclass,
            cc_nameplate_basis,
            int(year),
            mid_vintage_exit_carry,
        )
        if mid_vintage_exit_carry
        else _iso_plant_capacity(iso, cc_steam_part_reclass, cc_nameplate_basis)
    )
    if lp_bin_capacity is not None and iso != "ERCOT":
        # miso-266: the DISPATCHED fleet's own per-bin roster, CHP bins excepted
        # (_DISPATCHED_DENOM_EXCLUDED_GROUPS). This layer keeps its own
        # accumulator loop but divides by the same cap[bin] on the same key, so
        # it carries the identical denominator defect and must move with the
        # shared accumulator (rule 19 [R-ONE-MECH]). Non-ERCOT only, matching
        # the accumulator's own scoping.
        cap = _dispatched_denominator(cap, lp_bin_capacity)
    sums: dict[tuple[int, str], np.ndarray] = {}
    for r in df.itertuples(index=False):
        code = int(r.facility_id)
        g = (
            ""
            if r.plant_group is None
            or (isinstance(r.plant_group, float) and np.isnan(r.plant_group))
            else str(r.plant_group)
        )
        if code in _FLEET_GROUP_OVERRIDE:
            tgt = (code, _FLEET_GROUP_OVERRIDE[code])
        elif not g or g == "OTHER":
            continue
        else:
            tgt = (code, g)
        if tgt not in cap:
            continue
        removed = float(r.derate_mw)
        if not removed > 0.0 or pd.isna(removed):
            continue
        # Hour-granular, half-open: window_end is the return-to-normal hour
        # (the deriver ceils the declared end to the next hour boundary), so
        # no +1-day inflation like the date-grain std extract.
        mask = outage_hour_mask(r.window_start, r.window_end, year, hours)
        if not mask.any():
            continue
        arr = sums.setdefault(tgt, np.zeros(hours))
        arr[mask] += removed / cap[tgt]
    return {k: np.clip(1.0 - v, 0.0, 1.0) for k, v in sums.items()}


# Partial (unit-level) outage derates approximated from CAMPD CF-ceiling
# plateaus (scripts/data/derive_partial_outages.py). A multiplicative availability
# factor per plant: 1.0 outside detected windows, derate_factor within.
PARTIAL_OUTAGE_CSV: Path = RAW_DATA_DIR / "campd-partial-outages.csv"

# DAY-SHAPED partial-outage plateaus (ercot-185, the fault-3 construction
# repair): the SAME plateaus over the SAME day spans as PARTIAL_OUTAGE_CSV,
# emitted as consecutive day sub-windows carrying a day-resolved derate profile
# instead of one flat multi-week factor (scripts/data/derive_partial_outages.py
# --emit-shaped, whose in-deriver SP-2/SP-6 assertions prove the covered hour
# set is identical and the profile is median-preserving — only the WITHIN-window
# SHAPE changes, rule 23 [R-FROZEN-DERIVE]). Identical 7-column schema, so this
# file is consumed by the same loader and needs no separate accumulator.
# Raw-only, like campd-partial-outages-units.csv: no curated datatype is minted.
PARTIAL_OUTAGE_SHAPED_CSV: Path = RAW_DATA_DIR / "campd-partial-outages-shaped.csv"


@lru_cache(maxsize=None)
def partial_outage_derate_factors(
    year: int,
    hours: int = HOURS_PER_YEAR,
    iso: str = "ERCOT",
    class_grain: bool = False,
    shaped: bool = False,
) -> dict[int, np.ndarray] | dict[tuple[int, str], np.ndarray]:
    """Return the CAMPD-derived partial-outage plateau availability multipliers.

    1.0 outside detected ceiling plateaus, the window's derate factor within
    (deepest wins where they overlap). Keyed ``{plant_code: (hours,)}`` by
    default; with ``class_grain=True`` (the ercot-173 C1 grain repair, gated by
    ``ScenarioConfig.ercot_dam_availability_event_cap_reconciliation``) keyed
    ``{(plant_code, plant_group): (hours,)}`` using the extract's OWN
    ``plant_group`` column — the plant-code-only keying discards it, so a
    facility-wide plateau lands on every class bin of that plant code
    (FINDING-ercot172 §4 fault 2). On the current bins sheet no partial-extract
    plant code carries more than one class bin, so the two grains induce
    identical per-bin factors today; the repair is wiring correctness, asserted
    inert by the ercot-173 seam proof.

    With ``shaped=True`` (the ercot-185 fault-3 construction repair, gated by
    ``ScenarioConfig.ercot_partial_outage_shaped_derate``) reads
    :data:`PARTIAL_OUTAGE_SHAPED_CSV` instead — the same plateaus over the same
    day spans, split into consecutive day sub-windows carrying a day-resolved
    derate profile, so a multi-week MEDIAN of daily maxima is no longer imposed
    as an HOURLY ceiling (`FINDING-ercot172` §4 fault 3). No accumulator change
    is needed: the per-row ``np.minimum`` below already composes many windows
    per plant, and the shaped sub-windows tile their plateau exactly. Falls back
    to the flat extract when the shaped file is absent, so the gate is
    fail-safe. The curated ``partial-outages`` clean partition carries the FLAT
    extract only, so the shaped path deliberately does not read it.

    When ``MARKET_SIM_USE_CLEAN`` is set and the ISO's curated
    ``partial-outages`` clean partition exists (written by
    ``scripts/data/curate_partial_outages.py``), reads from there; otherwise reads
    :data:`PARTIAL_OUTAGE_CSV` (ERCOT-only) directly.
    """
    iso = (iso or "ERCOT").upper()
    df = None
    cols = ["plant_id", "year", "outage_start", "outage_stop", "derate_factor"]
    if class_grain:
        cols.insert(1, "plant_group")
    if shaped and PARTIAL_OUTAGE_SHAPED_CSV.exists():
        df = pd.read_csv(PARTIAL_OUTAGE_SHAPED_CSV)
    if df is None and _use_clean():
        clean_io = _clean_io()
        if clean_io.clean_exists("partial-outages", iso=iso):
            df = clean_io.read_clean(
                "partial-outages",
                iso=iso,
                columns=cols,
            ).rename(columns={"plant_id": "oris_code"})
    if df is None:
        if not PARTIAL_OUTAGE_CSV.exists():
            return {}
        df = pd.read_csv(PARTIAL_OUTAGE_CSV)
    df = df[df["year"] == year]
    out: dict = {}
    for r in df.itertuples(index=False):
        mask = outage_hour_mask(r.outage_start, r.outage_stop, year, hours)
        if not mask.any():
            continue
        key: int | tuple[int, str] = int(r.oris_code)
        if class_grain:
            key = (int(r.oris_code), str(r.plant_group))
        arr = out.setdefault(key, np.ones(hours))
        arr[mask] = np.minimum(arr[mask], float(r.derate_factor))
    return out


# Unit-ATTRIBUTED partial-outage plateaus (ercot-174): the same plateaus as
# PARTIAL_OUTAGE_CSV, carrying which CAMPD units carry each one (written by
# scripts/data/derive_partial_outages.py --emit-units, whose BE-3 assertion proves
# the plant-grain aggregation is byte-identical to the file above — only the
# GRAIN differs, rule 23 [R-FROZEN-DERIVE]). Raw-only, like its siblings
# campd-unit-outages-short-<ISO>.csv and campd-partial-outages-<ISO>.csv: no
# curated datatype is minted for it.
PARTIAL_OUTAGE_UNITS_CSV: Path = RAW_DATA_DIR / "campd-partial-outages-units.csv"


@lru_cache(maxsize=None)
def partial_outage_active_units(
    year: int, hours: int = HOURS_PER_YEAR, iso: str = "ERCOT"
) -> dict[tuple[int, str], dict[str, np.ndarray]]:
    """Return ``{(plant_code, plant_group): {unit_id: (hours,) bool}}``.

    Which CAMPD units carry an active partial-outage plateau at each hour, from
    the unit-attributed extract :data:`PARTIAL_OUTAGE_UNITS_CSV`. Each row is
    routed to its model bin by the SAME :func:`_unit_outage_target` the window
    layer uses, so the two layers' unit sets are directly comparable; rows with
    an empty ``unit_id`` (a plateau no single unit's own ceiling resolves) are
    dropped, which leaves the bin's partial unit set empty and makes the
    consumer fall back to the incumbent composition — fail-safe.

    Consumed only by the unit-scoped event-cap composition
    (``ScenarioConfig.ercot_dam_availability_event_cap_unit_scoped``). ERCOT-only
    (the extract is keyed to ERCOT plant codes); a missing file or an
    uncovered year returns an empty dict, so the gate is inert.
    """
    if (iso or "ERCOT").upper() != "ERCOT" or not PARTIAL_OUTAGE_UNITS_CSV.exists():
        return {}
    df = pd.read_csv(PARTIAL_OUTAGE_UNITS_CSV)
    df = df[(df["year"] == year) & df["unit_id"].notna()]
    out: dict[tuple[int, str], dict[str, np.ndarray]] = {}
    for r in df.itertuples(index=False):
        uid = str(r.unit_id).strip()
        if not uid:
            continue
        tgt = _unit_outage_target(int(r.oris_code), uid, r.plant_group)
        if tgt is None:
            continue
        mask = outage_hour_mask(r.outage_start, r.outage_stop, year, hours)
        if not mask.any():
            continue
        per_unit = out.setdefault(tgt, {})
        arr = per_unit.setdefault(uid, np.zeros(hours, dtype=bool))
        arr |= mask
    return out


@lru_cache(maxsize=None)
def unit_outage_active_units(
    year: int,
    hours: int = HOURS_PER_YEAR,
    iso: str = "ERCOT",
) -> dict[tuple[int, str], dict[str, np.ndarray]]:
    """Return ``{(plant_code, plant_group): {unit_id: (hours,) bool}}``.

    The window-layer companion of :func:`partial_outage_active_units`: which
    CAMPD units are inside a ``>= UNIT_OUTAGE_MIN_DAYS`` full-stop window at
    each hour, from the same events and under the same duration filter and
    :func:`_unit_outage_target` routing :func:`unit_outage_derate_factors` uses
    to build its factors — so a unit present here is exactly a unit whose
    downtime that factor removed.

    The window mask matches the factor's own convention exactly — both route
    through :func:`unit_outage_event_window`, so the two layers adopt the
    optional hour grain together or not at all. Consumed only by the
    unit-scoped event-cap composition.
    """
    iso = (iso or "ERCOT").upper()
    df = _load_unit_outage_events(unit_outage_csv_for_iso(iso), iso)
    if df is None:
        return {}
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    has_hours = _has_hour_grain(df)
    out: dict[tuple[int, str], dict[str, np.ndarray]] = {}
    for r in df.itertuples(index=False):
        uid = str(r.unit_id).strip()
        tgt = _unit_outage_target(int(r.facility_id), uid, r.plant_group)
        if tgt is None or not uid:
            continue
        w_start, w_stop = unit_outage_event_window(r, has_hours)
        mask = outage_hour_mask(w_start, w_stop, year, hours)
        if not mask.any():
            continue
        per_unit = out.setdefault(tgt, {})
        arr = per_unit.setdefault(uid, np.zeros(hours, dtype=bool))
        arr |= mask
    return out


def shared_unit_hours(
    window_units: dict[str, np.ndarray] | None,
    partial_units: dict[str, np.ndarray] | None,
    hours: int = HOURS_PER_YEAR,
) -> np.ndarray:
    """Return the ``(hours,)`` bool mask where the two layers share a unit.

    ``True`` at hour ``t`` iff at least one CAMPD unit is simultaneously inside
    a window-layer full stop AND carrying a partial-outage plateau at ``t`` —
    i.e. the two measured layers are removing the SAME unit's downtime, so
    multiplying them double-counts it (rule 19 `[R-ONE-MECH]`). ``False``
    everywhere when either side is absent, which keeps the incumbent product.

    Unit ids are matched after :func:`_norm_partial_unit_id` normalisation;
    both sides originate in the same CAMPD ``unitId``, so raw equality is the
    expected case and normalisation only guards a punctuation/case difference.
    """
    if not window_units or not partial_units:
        return np.zeros(hours, dtype=bool)
    w = {_norm_partial_unit_id(u): m for u, m in window_units.items()}
    p = {_norm_partial_unit_id(u): m for u, m in partial_units.items()}
    shared = np.zeros(hours, dtype=bool)
    for uid in w.keys() & p.keys():
        shared |= w[uid][:hours] & p[uid][:hours]
    return shared


def _norm_partial_unit_id(uid: object) -> str:
    """Return an upper-cased alphanumeric-only unit id (drop spaces/dashes).

    Mirrors ``scripts.data.derive_campd_unit_outages._norm_unit_id`` so the two
    layers' CAMPD unit ids join the same way the derivers label them.
    """
    return re.sub(r"[^0-9A-Za-z]", "", str(uid)).upper()


# ERCOT per-reactor DAILY nuclear availability (60-Day DAM disclosure NUC
# Resource Status, monthly energy reconciled to the EIA-923 anchor) — the
# window-grain replacement for the NUCLEAR_MONTHLY_CF_BY_YEAR fleet-month
# smear, gated by ScenarioConfig.ercot_nuclear_unit_availability. Derived by
# scripts/data/derive_ercot_nuclear_availability.py (provenance + admissibility in
# its docstring); a refuel window is a physical availability event, the
# nuclear analogue of the CAMPD fossil outage windows above.
ERCOT_NUCLEAR_AVAILABILITY_CSV: Path = RAW_DATA_DIR / "ercot-nuclear-availability.csv"


@lru_cache(maxsize=None)
def ercot_nuclear_unit_availability_series(
    year: int, hours: int = HOURS_PER_YEAR
) -> dict[tuple[int, int], np.ndarray]:
    """Return ``{(plant_code, unit_no): (hours,) availability}`` for ``year``.

    Each covered delivery date contributes a flat 24-hour block of its daily
    ``avail`` fraction on the model's fixed non-leap clock (real-calendar
    month/day mapped through :func:`_hour_of_year`; a leap year's Feb 29 row
    is dropped, matching the archive convention). Hours the disclosure does
    not cover are ``NaN`` — the caller keeps its existing (monthly-smear)
    availability there. Returns an empty dict when the CSV is absent or the
    year has no rows, so callers degrade to the smear unchanged.
    """
    if not ERCOT_NUCLEAR_AVAILABILITY_CSV.exists():
        return {}
    df = pd.read_csv(ERCOT_NUCLEAR_AVAILABILITY_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year == int(year)]
    if df.empty:
        return {}
    out: dict[tuple[int, int], np.ndarray] = {}
    for r in df.itertuples(index=False):
        mo, dy = int(r.date.month), int(r.date.day)
        if mo == 2 and dy == 29:
            continue  # non-leap model clock (ERCOT-54 convention)
        lo = _hour_of_year(mo, dy, 0)
        hi = min(lo + 24, hours)
        arr = out.setdefault(
            (int(r.plant_code), int(r.unit_no)), np.full(hours, np.nan)
        )
        arr[lo:hi] = float(r.avail)
    return out


# Per-ISO per-reactor DAILY nuclear availability (NRC daily Power Reactor
# Status, monthly energy reconciled to the same EIA-923 anchor the smear
# uses) — the ISO-generic sibling of the ERCOT-specific series above, gated
# by ScenarioConfig.nuclear_unit_availability (PJM first; ERCOT keeps its own
# flag/file). Derived by scripts/data/derive_nuclear_availability.py (provenance,
# admissibility and the winter thermal-vs-net wedge fallback in its
# docstring); a refuel window / reactor power state is a physical
# availability event, the same rule-13 class as the CAMPD fossil outage
# windows.
def _nuclear_availability_csv(iso: str) -> Path:
    """Path of an ISO's derived per-reactor daily availability extract."""
    return RAW_DATA_DIR / f"nuclear-availability-{iso.upper()}.csv"


@lru_cache(maxsize=None)
def nuclear_unit_availability_series(
    iso: str, year: int, hours: int = HOURS_PER_YEAR
) -> dict[tuple[int, int], np.ndarray]:
    """Return ``{(plant_code, unit_no): (hours,) availability}`` for ``year``.

    ISO-generic generalization of
    :func:`ercot_nuclear_unit_availability_series` (identical semantics):
    each covered date contributes a flat 24-hour block of its daily ``avail``
    fraction on the model's fixed non-leap clock; uncovered dates are ``NaN``
    — the caller keeps its existing (monthly-smear) availability there,
    including the uprate-season months the deriver drops for the
    thermal-vs-net wedge. Returns an empty dict when the ISO has no extract
    or the year has no rows, so callers degrade to the smear unchanged.
    """
    path = _nuclear_availability_csv(iso)
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year == int(year)]
    if df.empty:
        return {}
    out: dict[tuple[int, int], np.ndarray] = {}
    for r in df.itertuples(index=False):
        mo, dy = int(r.date.month), int(r.date.day)
        if mo == 2 and dy == 29:
            continue  # non-leap model clock (ERCOT-54 convention)
        lo = _hour_of_year(mo, dy, 0)
        hi = min(lo + 24, hours)
        arr = out.setdefault(
            (int(r.plant_code), int(r.unit_no)), np.full(hours, np.nan)
        )
        arr[lo:hi] = float(r.avail)
    return out


# ERCOT measured CLASS-day thermal availability (60-Day DAM disclosure
# Gen_Resource HSL + Resource Status, config-collapsed to physical CC trains)
# — the measured replacement for the statistical WEFOR/EFOR estimate of the
# same quantity on the covered gas classes, gated by
# ScenarioConfig.ercot_thermal_dam_availability. Derived by
# scripts/data/derive_ercot_thermal_dam_availability.py (provenance, class scope and
# admissibility in its docstring); the June/Sep-2023 scarcity-formation
# forensics measured the statistical stack 13-22 % derated at the summer
# reserve margin where this disclosure shows the same fleet at its ratings.
#: NP6-905-CD hourly reserve/λ series (fetch_ercot_ordc_reserves.py output) —
#: the stage-1 reconciliation reads ONLY the ``rtolhsl`` quantity column.
ERCOT_ORDC_RESERVES_TMPL: str = "ercot/ercot_{year}_ordc_reserves_hourly.parquet"
#: Measured wind/solar HSL hourly series (quantity-only).
ERCOT_HSL_HOURLY_TMPL: str = "ercot-hsl/ercot_{year}_hsl_hourly.parquet"
#: Measured online storage capability series — the same committed series the
#: armed ``ercot_storage_capability_measured`` mechanism uses.
ERCOT_STORAGE_CAPABILITY_CSV: Path = RAW_DATA_DIR / "ercot-storage-capability.csv"


@lru_cache(maxsize=None)
def ercot_capability_reconciliation_target(
    year: int, hours: int = HOURS_PER_YEAR
) -> np.ndarray:
    """Return the ``(hours,)`` telemetered all-thermal capability target T_tel.

    The ercot-219 stage-1 aggregate-capability reconciliation target (B-1;
    PRECOMMIT-ercot219 §1.1):

        ``T_tel(t) = rtolhsl(t) − wind_hsl(t) − solar_hsl(t) − storage_cap(t)``

    — the published NP6-905 real-time online-HSL aggregate net of the measured
    non-thermal components, i.e. the telemetered ALL-THERMAL online
    dispatchable capability on the NP6-905 population boundary. Every input is
    a committed quantity series on the fixed non-leap 8760 clock; **no price
    column is ever read** (the parquet reads are column-scoped, so the audit
    is mechanical). Hours where any input is missing return NaN — the caller
    treats them as reconciliation-inert (notably the 2025 post-RTC+B tail,
    hours 8112-8759, where the ORDC-era series honestly ends). Rule 13: a
    measured physical/market input applied consistently across all backcast
    years under the B-1 signature, never an outcome fed back.
    """
    ordc = pd.read_parquet(
        RAW_DATA_DIR / ERCOT_ORDC_RESERVES_TMPL.format(year=year),
        columns=["rtolhsl"],
    )
    rtolhsl = ordc["rtolhsl"].to_numpy(dtype=float)[:hours]
    hsl = pd.read_parquet(
        RAW_DATA_DIR / ERCOT_HSL_HOURLY_TMPL.format(year=year),
        columns=["wind_hsl_mw", "solar_hsl_mw"],
    )
    wind = hsl["wind_hsl_mw"].to_numpy(dtype=float)[:hours]
    solar = hsl["solar_hsl_mw"].to_numpy(dtype=float)[:hours]
    stor = pd.read_csv(ERCOT_STORAGE_CAPABILITY_CSV)
    stor = (
        stor[stor["year"] == year]
        .sort_values("hour")["capability_mw"]
        .to_numpy(dtype=float)[:hours]
    )
    out = np.full(hours, np.nan)
    n = min(hours, rtolhsl.size, wind.size, solar.size, stor.size)
    out[:n] = rtolhsl[:n] - wind[:n] - solar[:n] - stor[:n]
    return out


ERCOT_THERMAL_DAM_AVAILABILITY_CSV: Path = (
    RAW_DATA_DIR / "ercot-thermal-dam-availability.csv"
)


@lru_cache(maxsize=None)
def ercot_thermal_dam_availability_series(
    year: int, hours: int = HOURS_PER_YEAR
) -> dict[str, np.ndarray]:
    """Return ``{plant_group: (hours,) measured class availability}`` for ``year``.

    Each covered delivery date contributes a flat 24-hour block of the class's
    measured day availability fraction (live config-collapsed HSL / site
    ratings) on the model's fixed non-leap clock (:func:`_hour_of_year`; a leap
    year's Feb 29 row dropped, the archive convention). Hours the disclosure
    does not cover — the Oct-2023 publication hole, Nov-Dec 2025 until the 2026
    files land — are ``NaN``: the caller keeps the statistical availability
    there. Returns an empty dict when the CSV is absent or the year has no
    rows, so callers degrade to the statistical model unchanged.
    """
    if not ERCOT_THERMAL_DAM_AVAILABILITY_CSV.exists():
        return {}
    df = pd.read_csv(ERCOT_THERMAL_DAM_AVAILABILITY_CSV)
    # "class" is a Python keyword — itertuples would positionalize it.
    df = df.rename(columns={"class": "klass"})
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year == int(year)]
    if df.empty:
        return {}
    out: dict[str, np.ndarray] = {}
    for r in df.itertuples(index=False):
        mo, dy = int(r.date.month), int(r.date.day)
        if mo == 2 and dy == 29:
            continue  # non-leap model clock (ERCOT-54 convention)
        lo = _hour_of_year(mo, dy, 0)
        hi = min(lo + 24, hours)
        arr = out.setdefault(str(r.klass), np.full(hours, np.nan))
        arr[lo:hi] = float(r.avail)
    return out


# ERCOT measured CLASS-hour thermal availability — the ERCOT-96 grain refinement
# of the class-day series above, from the SAME 60-Day DAM disclosure rows
# (scripts/data/derive_ercot_thermal_dam_availability.py --hourly-out). Keeps
# the hourly ambient-derate shape the day mean discards: the ERCOT-95 diagnosis
# (docs/handoffs/ercot95-scarcity-tail-diagnosis-2026-07.md Finding 6) measured
# the day-flat overlay handing the model a +216 MW mean (+433 p90) CC+CT
# phantom on the 181 actual 2023 RT tail hours (hod 13-19), and an equal
# under-credit overnight. Gated by
# ScenarioConfig.ercot_thermal_dam_availability_hourly on top of the class-day
# flag (the grain switch of the SAME mechanism, not a second overlay).
ERCOT_THERMAL_DAM_AVAILABILITY_HOURLY_CSV: Path = (
    RAW_DATA_DIR / "ercot-thermal-dam-availability-hourly.csv"
)


@lru_cache(maxsize=None)
def ercot_thermal_dam_availability_hourly_series(
    year: int, hours: int = HOURS_PER_YEAR
) -> dict[str, np.ndarray]:
    """Return ``{plant_group: (hours,) measured class-HOUR availability}``.

    Each covered delivery date contributes its 24 per-``Hour Ending`` measured
    fractions (config-collapsed live HSL over the sites present at that HE) on
    the model's fixed non-leap clock (:func:`_hour_of_year`; a leap year's
    Feb 29 row dropped, the archive convention). Hours the disclosure does not
    cover — the Oct-2023 publication hole, Nov-Dec 2025 until the 2026 files
    land, an uncovered HE — are ``NaN``: the caller keeps the statistical
    availability there, hour by hour. Returns an empty dict when the CSV is
    absent or the year has no rows, so callers degrade to the class-day grain
    (and from there to the statistical model) unchanged.
    """
    if not ERCOT_THERMAL_DAM_AVAILABILITY_HOURLY_CSV.exists():
        return {}
    df = pd.read_csv(ERCOT_THERMAL_DAM_AVAILABILITY_HOURLY_CSV)
    df = df.rename(columns={"class": "klass"})
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year == int(year)]
    if df.empty:
        return {}
    he_cols = [f"he{h:02d}" for h in range(1, 25)]
    out: dict[str, np.ndarray] = {}
    for r in df.itertuples(index=False):
        mo, dy = int(r.date.month), int(r.date.day)
        if mo == 2 and dy == 29:
            continue  # non-leap model clock (ERCOT-54 convention)
        lo = _hour_of_year(mo, dy, 0)
        hi = min(lo + 24, hours)
        arr = out.setdefault(str(r.klass), np.full(hours, np.nan))
        vals = np.array([getattr(r, c) for c in he_cols], dtype=float)
        arr[lo:hi] = vals[: hi - lo]
    return out


# ERCOT measured PLANT-hour thermal availability (ERCOT-97 plant grain) — the
# same 60-Day DAM disclosure site-hour intermediate
# (scripts/data/derive_ercot_thermal_dam_availability.py --site-hourly-out),
# but resolved to EIA plant codes through the reviewed, accepted-gated
# DAM-site -> EIA-plant crosswalk (build_ercot_dam_resource_crosswalk.py). For
# each crosswalked plant, its measured availability fraction at a delivery hour
# is Σ live_HSL / Σ site-rating over the DAM sites (physical trains) mapped onto
# that plant. Only ``accepted=1`` crosswalk rows are consumed, so an unreviewed
# guess never enters a solve (CLAUDE.md rules 1/11 — crosswalk rows are
# identification metadata, not a tuning channel). Gated by
# ScenarioConfig.ercot_thermal_dam_availability_plant on top of the class-hour
# flag; the plant caps redistribute WHICH plant is derated inside a class while
# the class-hour water-fill still lands the class total on the measured class
# fraction (ERCOT-96 Finding: per-plant misallocation ~259 MW mean on the 2023
# tail hours; net-zero on the class total — a merit-mix/zonal channel).
ERCOT_THERMAL_DAM_AVAILABILITY_SITE_HOURLY: Path = (
    RAW_DATA_DIR / "ercot-thermal-dam-availability-site-hourly.parquet"
)
ERCOT_DAM_PLANT_CROSSWALK_CSV: Path = REFERENCE_DIR / "ercot-dam-plant-crosswalk.csv"


@lru_cache(maxsize=None)
def _ercot_dam_plant_frames(
    year: int, hours: int = HOURS_PER_YEAR
) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
    """Shared builder for the plant-grain fraction AND covered-rating series.

    Returns ``(frac, rating)`` — both keyed by EIA ``plant_code`` over the
    ``accepted=1`` crosswalk rows: ``frac[pc][h]`` = Σ live / Σ rating over the
    plant's mapped sites at that delivery hour, ``rating[pc][h]`` = that same
    Σ rating (the plant's MEASURED covered MW at the hour — the ruling-#10
    coverage denominator, PRECOMMIT-ercot191 §1d). One file read serves both
    consumers; both dicts are empty under exactly the conditions the public
    fraction loader documents.
    """
    if not (
        ERCOT_THERMAL_DAM_AVAILABILITY_SITE_HOURLY.exists()
        and ERCOT_DAM_PLANT_CROSSWALK_CSV.exists()
    ):
        return {}, {}
    xw = pd.read_csv(ERCOT_DAM_PLANT_CROSSWALK_CSV)
    xw = xw[xw["accepted"] == 1][["site", "plant_code"]]
    if xw.empty:
        return {}, {}
    site2plant = {str(s): int(p) for s, p in zip(xw["site"], xw["plant_code"])}

    sh = pd.read_parquet(
        ERCOT_THERMAL_DAM_AVAILABILITY_SITE_HOURLY,
        columns=["date", "site", "he", "live_mw", "rating_mw"],
    )
    sh = sh[sh["site"].isin(site2plant)].copy()
    if sh.empty:
        return {}, {}
    sh["date"] = pd.to_datetime(sh["date"])
    sh = sh[sh["date"].dt.year == int(year)]
    if sh.empty:
        return {}, {}
    sh["plant_code"] = sh["site"].map(site2plant).astype(int)
    # One crosswalked plant may aggregate several DAM sites (physical trains):
    # sum live + rating over its mapped sites at each (date, HE) before dividing.
    agg = sh.groupby(["plant_code", "date", "he"], as_index=False)[
        ["live_mw", "rating_mw"]
    ].sum()
    agg["frac"] = np.where(
        agg["rating_mw"] > 0.0,
        np.clip(agg["live_mw"] / agg["rating_mw"], 0.0, 1.0),
        np.nan,
    )
    frac: dict[int, np.ndarray] = {}
    rating: dict[int, np.ndarray] = {}
    for r in agg.itertuples(index=False):
        mo, dy = int(r.date.month), int(r.date.day)
        if mo == 2 and dy == 29:
            continue  # non-leap model clock (ERCOT-54 convention)
        he = int(r.he)
        if he < 1 or he > 24:
            continue
        h = _hour_of_year(mo, dy, he - 1)
        if h >= hours:
            continue
        pc = int(r.plant_code)
        arr = frac.setdefault(pc, np.full(hours, np.nan))
        arr[h] = float(r.frac)
        rarr = rating.setdefault(pc, np.full(hours, np.nan))
        rarr[h] = float(r.rating_mw)
    return frac, rating


def ercot_thermal_dam_availability_plant_series(
    year: int, hours: int = HOURS_PER_YEAR
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) measured plant availability fraction}``.

    Keyed by EIA ``plant_code`` for the plants an ``accepted=1`` crosswalk row
    maps a DAM site onto; the fraction is Σ live / Σ rating over that plant's
    mapped sites, per delivery hour, on the model's fixed non-leap clock
    (:func:`_hour_of_year`). Hours the disclosure does not cover for a plant
    (an all-OUT day still carries rows -> fraction 0; a genuinely missing
    (date, HE) -> ``NaN``) let the caller keep the class-hour treatment for
    that plant-hour. Returns an empty dict when either the site-hour parquet or
    the crosswalk is absent, has no accepted rows, or the year has no rows — so
    callers degrade to the class-hour grain unchanged.
    """
    return _ercot_dam_plant_frames(year, hours)[0]


def ercot_thermal_dam_availability_plant_rating_series(
    year: int, hours: int = HOURS_PER_YEAR
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) covered DAM rating MW}`` (ruling #10).

    The Σ ``rating_mw`` over a crosswalked plant's accepted sites with rows at
    each hour — the MEASURED share of the plant the DAM disclosure actually
    covers. The plant pin's REMOVE direction dilutes its target to this
    coverage so an accepted-subset outage cannot drag the plant's unmeasured
    remainder (ercot-149 §6.3, V H Braunig; signature A1,
    PRECOMMIT-ercot191 §1d). Same keys/NaN semantics as
    :func:`ercot_thermal_dam_availability_plant_series`.
    """
    return _ercot_dam_plant_frames(year, hours)[1]


# ERCOT CAMPD-blind per-plant availability (EIA-923 zero-month outage windows;
# scripts/data/derive_ercot_noncampd_availability.py). Restores measured
# availability for the ERCOT gas plants ABSENT from the TX CAMPD extract
# (Kiamichi 55501, Hidalgo 55545, Arthur Von Rosenberg 7512, EG178 56233 — the
# ERCOT-70 phantom-CC blind spot: the model dispatches them on flat statistical
# availability while EIA-923 shows a real full-plant outage month). The
# CAMPD-derived outage overlay cannot see them (no CEMS rows -> no windows).
# Backcast-only, gated by ScenarioConfig.ercot_noncampd_plant_availability;
# forecast keeps the statistical stack (the mode-aware seam).
ERCOT_NONCAMPD_AVAILABILITY_CSV: Path = RAW_DATA_DIR / "ercot-noncampd-availability.csv"


@lru_cache(maxsize=None)
def ercot_noncampd_availability_caps(
    year: int, hours: int = HOURS_PER_YEAR
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) availability cap}`` for the CAMPD-blind
    ERCOT gas plants, from the EIA-923 zero-month outage windows.

    Each window ``[outage_start, outage_end)`` (a full-plant EIA-923 zero
    month; ``outage_end`` is the exclusive return-to-service instant) zeroes
    the plant's availability over its hours on the model's fixed non-leap clock
    (:func:`outage_hour_mask`); every other hour stays at 1.0, so the cap only
    ever REMOVES the plant in its measured-offline months and leaves the
    statistical availability untouched elsewhere (a zero-month availability
    event, never a monthly-level pin — rule 14). Plant-keyed so the fleet
    builder applies each cap to every dispatch tranche of the (possibly binned)
    plant, exactly like :func:`retiree_availability_caps`. Empty when the CSV is
    absent or the year has no windows, so callers degrade to the statistical
    model unchanged.
    """
    if not ERCOT_NONCAMPD_AVAILABILITY_CSV.exists():
        return {}
    df = pd.read_csv(ERCOT_NONCAMPD_AVAILABILITY_CSV)
    df = df[df["year"] == int(year)]
    if df.empty:
        return {}
    caps: dict[int, np.ndarray] = {}
    for r in df.itertuples(index=False):
        mask = outage_hour_mask(r.outage_start, r.outage_end, int(year), hours)
        if not mask.any():
            continue
        cap = caps.setdefault(int(r.plant_code), np.ones(hours))
        # MIN-combine so the most-conservative measured availability wins where
        # windows overlap (a daily DAM row and an EIA-923 zero-month backstop).
        cap[mask] = np.minimum(cap[mask], float(r.avail))
    return caps


# Within-window retiree measured-availability cap (CAMPD unit-level CEMS).
# A within-window retiree (fleet.load_retired_within_window) is a whole-plant
# exit the COD ramp ages out on its EIA-860 planned retirement date. But a unit
# winding down to retirement runs at LOW capacity factor — or stops generating
# months before its official date — for retirement-logistics / out-of-market
# (RMR-type) reasons a cost-based merit order cannot see: the LP keeps it
# dispatched at its coal must-run floor as baseload while reality barely ran it.
# Homer City (plant 3122) is the type case: model ~4.1 TWh vs CEMS 1.2 TWh in
# 2023 (its three coal units stopping generation Mar/May 2023 though officially
# retiring 2023-07 / 2023-08 / 2024-04, the middle unit never running at all),
# and ~2.8 TWh modeled in 2024 against zero actual. The per-plant binning
# (fleet.fleet_to_bins) merges the units before the COD ramp, so per-unit
# planned-date aging cannot resolve it; the measured envelope can.
#
# This caps each retiree plant's availability to its MEASURED monthly CEMS
# envelope — the peak hourly plant-total gross load the plant actually
# demonstrated that month, as a fraction of its nameplate, and zero in months it
# did not run. It is an AVAILABILITY measurement (the LP still chooses dispatch,
# and the must-run floor, clamped to availability, scales with it), not an
# energy target, and is plant-keyed so it reaches every dispatch tranche of the
# binned plant. Scoped to the within-window retiree plants — capping the bulk
# operable fleet to CEMS would be circular (it would reproduce EIA-930).
# Backcast-only, mirroring the measured CAMPD outage overlay; the forecast path
# ages retirees out on planned dates instead.
CAMPD_UNIT_LEVEL_DIR: Path = RAW_DATA_DIR / "campd-unit-level"

# Hour-of-year (0-based) -> calendar month (1-12) on the fixed non-leap 8760
# clock, so a per-month envelope broadcasts to hours without per-call calendar
# work.
_MONTH_OF_HOUR: np.ndarray = np.empty(HOURS_PER_YEAR, dtype=np.int64)
for _mm in range(1, 13):
    _lo_h = _DAYS_BEFORE_MONTH[_mm] * 24
    _hi_h = (_DAYS_BEFORE_MONTH[_mm] + calendar.monthrange(2023, _mm)[1]) * 24
    _MONTH_OF_HOUR[_lo_h:_hi_h] = _mm


def _plant_cems_envelope(
    state: str, year: int, plant_code: int, nameplate_mw: float, hours: int
) -> np.ndarray | None:
    """Monthly CEMS availability envelope for one retiree plant, or ``None``.

    Reads ``campd-unit-level/{STATE}_{YEAR}.parquet``, sums the plant's units to
    an hourly plant-total gross load, and returns a length-``hours`` cap in
    [0, 1] = each month's peak plant-total hour / ``nameplate_mw`` (clipped to
    1), zero in months with no generation. ``None`` when the state extract or
    the plant is absent (no measurement -> the COD ramp's planned-date aging
    stands). Gross load over net nameplate clips to 1 in full-output months, so
    the cap only bites where the plant's demonstrated peak has fallen — i.e.
    where it is winding down.

    A within-window retiree absent from an extract that *exists* did not run that
    year at all (it had retired / was decommissioned), so it is capped to zero
    rather than skipped — the binned plant's planned retirement (e.g. Homer City
    held online through 2024-04 by the collapsed plant date) is then overridden
    by the measured "did not run" fact. Only a missing state extract returns
    ``None`` (a genuine data gap).
    """
    if nameplate_mw <= 0.0:
        return None
    path = CAMPD_UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["facilityId", "date", "hour", "grossLoad"])
    sub = df[df["facilityId"].astype(str) == str(int(plant_code))]
    if sub.empty:
        return np.zeros(hours)
    sub = sub.copy()
    sub["grossLoad"] = pd.to_numeric(sub["grossLoad"], errors="coerce").fillna(0.0)
    # Plant-total per hour (units summed), then the peak hour within each month.
    plant_hourly = sub.groupby(["date", "hour"], as_index=False)["grossLoad"].sum()
    plant_hourly["month"] = pd.to_datetime(plant_hourly["date"]).dt.month
    monthly_peak = plant_hourly.groupby("month")["grossLoad"].max()
    frac = np.zeros(13)  # 1-indexed; index 0 unused
    for m in range(1, 13):
        peak = monthly_peak.get(m, 0.0)
        if pd.isna(peak):
            peak = 0.0
        frac[m] = min(1.0, max(0.0, float(peak) / nameplate_mw))
    idx = np.arange(hours) % HOURS_PER_YEAR
    return frac[_MONTH_OF_HOUR[idx]]


@lru_cache(maxsize=None)
def retiree_availability_caps(
    iso: str, year: int, hours: int = HOURS_PER_YEAR
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) availability cap}`` for within-window
    retiree plants, from the CAMPD unit-level CEMS envelope.

    Plant-keyed so the fleet builder applies each cap to every dispatch tranche
    of the (possibly binned) plant. The denominator is the plant's nameplate
    summed over its retiree units. Plants with no CEMS extract, or whose
    envelope never falls below full capacity, are omitted. Empty for an ISO with
    no within-window retiree parquet.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_retired_within_window

    try:
        iso_config = get_iso_config(iso)
    except ValueError:
        iso_config = None
    plants: dict[int, list] = {}
    for g in load_retired_within_window(iso, iso_config):
        pc = int(g.plant_code)
        if pc <= 0 or not g.state:
            continue
        rec = plants.setdefault(pc, [g.state, 0.0])
        rec[1] += float(g.pmax_mw)
    caps: dict[int, np.ndarray] = {}
    for pc, (state, nameplate) in plants.items():
        cap = _plant_cems_envelope(state, year, pc, nameplate, hours)
        if cap is not None and (cap < 1.0).any():
            caps[pc] = cap
    return caps


# CT_PEAKER AS/RUC-deployment energy floor (scripts/data/derive_ct_deployment.py).
# A per-plant *hourly* minimum-generation floor on the model's 8760-hour clock:
# in the out-of-merit hours where CEMS shows a simple-cycle peaker generating
# below its marginal energy cost (the IMM-documented ancillary-service /
# reliability-unit-commitment deployment + reserve-adequacy wedge), the floor is
# the plant's *measured* net output; zero everywhere else. Applied as a min-gen
# bound by fleet.generators_to_fleet_arrays when ScenarioConfig
# .ct_deployment_overlay is set (backcast only, any ISO — the artifact is keyed
# per ISO via ct_deployment_csv) so the LP reproduces the out-of-merit CT energy
# an energy-only merit order omits,
# WITHOUT flooring CT to its full CEMS output (the in-merit hours stay
# economic). Unlike the CT reliability must-run floor (which covers all hours
# and so exempts its units from WEFOR/POF), this floor is sparse and well below
# pmax in its hours, so the units keep the statistical availability model and
# the floor is simply availability-capped where they ever coincide.
_CT_DEPLOYMENT_DIR: Path = CALIBRATION_DIR


def ct_deployment_csv(iso: str = "ERCOT") -> Path:
    """Return the per-ISO CT deployment-floor artifact path.

    ``scripts/data/derive_ct_deployment.py`` writes one parquet per ISO
    (``ct_deployment_floor_<ISO>.parquet``); the overlay reads the file for
    the ISO it is dispatching so every ISO's out-of-merit wedge is sourced
    from its own CEMS + LMP measurement.
    """
    return _CT_DEPLOYMENT_DIR / f"ct_deployment_floor_{iso.upper()}.parquet"


@lru_cache(maxsize=None)
def ct_deployment_floor_for_year(
    year: int, hours: int = HOURS_PER_YEAR, iso: str = "ERCOT"
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) deployment floor MW}`` for ``year``.

    Reads the per-plant out-of-merit deployment-hour floors written by
    ``scripts/data/derive_ct_deployment.py`` (long: ``year, plant_code, hour,
    floor_mw``) for ``iso`` and rebuilds each plant's dense 8760-hour floor
    (zero outside its deployment hours). Returns an empty dict when the
    artifact is missing (the overlay then degrades to the unmodified
    energy-only dispatch) or when the year is absent. The arrays are shared
    read-only via the cache.
    """
    path = ct_deployment_csv(iso)
    if not path.exists():
        logger.warning(
            "CT deployment-floor artifact not found at %s; "
            "the CT deployment overlay is a no-op for %s %d",
            path,
            iso.upper(),
            year,
        )
        return {}
    df = pd.read_parquet(path)
    df = df[df["year"] == year]
    out: dict[int, np.ndarray] = {}
    for code, sub in df.groupby("plant_code", observed=True):
        arr = np.zeros(hours, dtype=float)
        hoy = sub["hour"].to_numpy()
        valid = (hoy >= 0) & (hoy < hours)
        arr[hoy[valid]] = sub["floor_mw"].to_numpy(dtype=float)[valid]
        out[int(code)] = arr
    return out


# Spatial reliability-deployment energy floor (scripts/derive_reliability_
# deployment.py). The generalization of the CT deployment overlay to the
# load-pocket thermal fleet (CC_REGULAR, COAL, ST_GAS, CC_CHP) in the
# under-running zones (South_Central, West, Northeast). Same per-plant *hourly*
# floor artifact and dense format as the CT overlay, but scoped on the load-zone
# congestion subset: the measured CEMS net in hours where the plant was economic
# at its LOCAL load-zone price yet out of merit at the system hub — the
# intra-zonal congestion energy a single-system-price LP cannot dispatch.
# Applied as a sparse min-gen bound by fleet.generators_to_fleet_arrays when
# ScenarioConfig.reliability_deployment_overlay is set (ERCOT backcast only).
def reliability_deployment_csv(iso: str = "ERCOT") -> Path:
    """Return the per-ISO reliability-deployment-floor artifact path."""
    return _CT_DEPLOYMENT_DIR / f"reliability_deployment_floor_{iso.upper()}.parquet"


@lru_cache(maxsize=None)
def reliability_deployment_floor_for_year(
    year: int, hours: int = HOURS_PER_YEAR, iso: str = "ERCOT"
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) deployment floor MW}`` for ``year``.

    Reads the per-plant out-of-merit-at-hub-but-economic-locally floors written
    by ``scripts/data/derive_reliability_deployment.py`` (long: ``year, plant_code,
    hour, floor_mw``) for ``iso`` and rebuilds each plant's dense 8760-hour
    floor (zero outside its deployment hours). Returns an empty dict when the
    artifact is missing (the overlay then degrades to the unmodified
    energy-only dispatch) or when the year is absent. Mirrors
    :func:`ct_deployment_floor_for_year`; the arrays are shared read-only via
    the cache.
    """
    path = reliability_deployment_csv(iso)
    if not path.exists():
        logger.warning(
            "reliability deployment-floor artifact not found at %s; "
            "the reliability deployment overlay is a no-op for %s %d",
            path,
            iso.upper(),
            year,
        )
        return {}
    df = pd.read_parquet(path)
    df = df[df["year"] == year]
    out: dict[int, np.ndarray] = {}
    for code, sub in df.groupby("plant_code", observed=True):
        arr = np.zeros(hours, dtype=float)
        hoy = sub["hour"].to_numpy()
        valid = (hoy >= 0) & (hoy < hours)
        arr[hoy[valid]] = sub["floor_mw"].to_numpy(dtype=float)[valid]
        out[int(code)] = arr
    return out


# ---------------------------------------------------------------------------
# NYSDEC 6 NYCRR Subpart 227-3 "peaker rule" availability overlay (NYISO)
# ---------------------------------------------------------------------------
# The regulation caps ozone-season (May 1 - Sep 30) NOx from simple-cycle
# turbines in two phases (2023-05-01 / 2025-05-01). Units whose compliance
# plan is ozone-season shutdown or reliability-only operation are unavailable
# to the energy market inside the window — an exogenous regulatory
# availability event in the same rule-#12 admissibility class as the CAMPD
# unit-outage windows (availability only, never an offer/price change; the
# schedule regenerates from the regulation, not from observed CF). Curated
# unit schedule: data/raw/reference/nysdec-227-3-peaker-compliance.csv
# (NYISO Gold Book Tables IV-3..IV-6, 2023/2024/2025 vintages; per-unit
# citations in the CSV rows).
NYSDEC_PEAKER_CSV: Path = (
    RAW_DATA_DIR / "reference" / "nysdec-227-3-peaker-compliance.csv"
)

# Ozone-season bounds on the model's fixed non-leap 8760 clock: May 1 00:00 is
# hour 2880, Sep 30 24:00 is hour 6552 (same span as the ST_GAS seasonal
# amortization window in model/commitment.py).
OZONE_SEASON_HOURS: tuple[int, int] = (2880, 6552)

# Restriction kinds the overlay APPLIES. Designated / record-only kinds
# (ozone_season_oos_star_designated, statutory_phaseout_2030, retired,
# none_documented) are carried in the CSV for the audit record but never
# restrict availability: the STAR designation kept the Gowanus/Narrows barges
# in operation, retirements are the fleet vintage's job, and the NYPA statute
# binds after 2030.
_NYSDEC_APPLIED_KINDS: frozenset[str] = frozenset({"ozone_season_oos"})


@lru_cache(maxsize=8)
def _nysdec_peaker_rows(csv_path: str) -> tuple:
    """Parse the curated 227-3 schedule into applicable restriction rows."""
    path = Path(csv_path)
    if not path.exists():
        return ()
    df = pd.read_csv(path)
    rows = []
    for r in df.itertuples(index=False):
        if str(r.restriction).strip() not in _NYSDEC_APPLIED_KINDS:
            continue
        eff = pd.to_datetime(r.effective_date)
        end = pd.to_datetime(r.end_date) if pd.notna(r.end_date) else None
        unit_ids = (
            tuple(u.strip() for u in str(r.unit_ids).split(";") if u.strip())
            if pd.notna(r.unit_ids)
            else ()
        )
        mw = float(r.restricted_mw) if pd.notna(r.restricted_mw) else None
        rows.append(
            (
                int(r.plant_code),
                str(r.scope).strip(),
                unit_ids,
                eff,
                end,
                mw,
            )
        )
    return tuple(rows)


def nysdec_peaker_restrictions(
    year: int, hours: int, csv_path: Path | None = None
) -> list[dict]:
    """Return the 227-3 restrictions active in ``year`` as hour windows.

    Each item: ``{"plant_code", "scope", "unit_ids", "restricted_mw",
    "h_lo", "h_hi"}`` — the ozone-window slice of the model year during which
    the row's units are out of the energy market. A row whose effective date
    falls inside the year's ozone window starts there (the 227-3 compliance
    dates are May 1, which is the window start); one that ends mid-window
    (e.g. a retirement) stops there.
    """
    o_lo, o_hi = OZONE_SEASON_HOURS
    o_hi = min(o_hi, hours)

    def _doy_nonleap(ts: pd.Timestamp) -> int:
        """Day-of-year on the model's fixed non-leap 8760 clock (Feb 29 -> 28)."""
        day = min(ts.day, 28) if ts.month == 2 else ts.day
        return int(pd.Timestamp(2023, ts.month, day).dayofyear)

    out: list[dict] = []
    for code, scope, unit_ids, eff, end, mw in _nysdec_peaker_rows(
        str(csv_path or NYSDEC_PEAKER_CSV)
    ):
        if eff.year > year:
            continue
        if end is not None and end.year < year:
            continue
        h_lo = o_lo
        if eff.year == year:
            h_lo = max(o_lo, min((_doy_nonleap(eff) - 1) * 24, hours))
        h_hi = o_hi
        if end is not None and end.year == year:
            h_hi = min(o_hi, max((_doy_nonleap(end) - 1) * 24, 0))
        if h_hi <= h_lo:
            continue
        out.append(
            {
                "plant_code": code,
                "scope": scope,
                "unit_ids": unit_ids,
                "restricted_mw": mw,
                "h_lo": h_lo,
                "h_hi": h_hi,
            }
        )
    return out


# ---------------------------------------------------------------------------
# Correlated cold-event forced-outage derate (forecast/hindcast; FF-1B)
# ---------------------------------------------------------------------------
# The forecast-mode statistical WEFOR forced-outage model is per-unit
# INDEPENDENT and weather-blind, so it never concentrates outages into a
# correlated deep-cold event: the in-year LP clears every hour with ample
# reserve and the post-solve ORDC overlay prints $0 even through a Uri-scale
# event (the G-31 finding). This section is the measured-admissible correlated
# derate that closes that gap (design charter
# docs/handoffs/ercot-retirement-composition-2026-07-16.md Part D): per plant
# class, excess(T) = clip(slope * (t0 - TMIN_sys), 0, cap) on the system daily
# MIN temperature, with the era's climatological winter event share ADDED BACK
# first so the mechanism relocates the cold-event share embedded in the flat
# GADS-based WEFOR rather than stacking on it. Curves are frozen measured
# constants (constants.CORRELATED_OUTAGE_CURVE, derived by
# scripts/data/derive_correlated_outage_curve.py); the gate and anchors are
# ScenarioConfig fields (correlated_forced_outage & co.). Backcast runs are
# excluded — the measured CAMPD overlays above already carry the actual events
# (charter D.5) — and ISOs without a curve entry are a no-op (rule 25).

# Winter months (Dec-Feb) whose flat-WEFOR availability carries the add-back;
# matches the fleet builder's non-summer/non-shoulder season.
_CORRELATED_OUTAGE_WINTER_MONTHS: frozenset[int] = frozenset({12, 1, 2})


def correlated_outage_system_tmin(
    iso: str, year: int, hours: int = HOURS_PER_YEAR
) -> np.ndarray | None:
    """Return the system daily MIN temperature (deg C) broadcast per run hour.

    The plain mean of ``tmin_c`` across the ISO's weather zones (the same
    construction as the derive script's fit driver), read through
    :func:`market_sim.data.eia_loader.load_weather` (clean Parquet primary,
    raw CSV fallback) and broadcast to the model's fixed non-leap clock via
    :func:`_hour_of_year` (a leap year's Feb 29 rows are dropped, the archive
    convention). Hours the archive does not cover are ``NaN`` — the caller
    treats them as no-derate. Returns ``None`` when the ISO/year has no
    weather coverage at all, so callers degrade to a logged no-op.
    """
    from market_sim.data.eia_loader import load_weather

    df = load_weather(iso, int(year))
    if df is None or "tmin_c" not in df.columns:
        return None
    df = df.dropna(subset=["tmin_c"])
    if df.empty:
        return None
    daily = df.groupby("date")["tmin_c"].mean()
    out = np.full(hours, np.nan)
    for d, t in daily.items():
        ts = pd.Timestamp(d)
        if ts.month == 2 and ts.day == 29:
            continue  # non-leap model clock (ERCOT-54 convention)
        lo = _hour_of_year(ts.month, ts.day, 0)
        hi = min(lo + 24, hours)
        out[lo:hi] = float(t)
    if not np.any(np.isfinite(out)):
        return None
    return out


def correlated_outage_excess_by_class(
    iso: str,
    weather_year: int,
    hours: int,
    *,
    t0_c: float,
    winterized_year: int,
) -> tuple[dict[str, np.ndarray], dict[str, float]] | None:
    """Return ``({class: (hours,) excess fraction}, {class: winter share})``.

    Applies the ISO's frozen era curve (``constants.CORRELATED_OUTAGE_CURVE``)
    to the weather year's system daily TMIN: per class,
    ``excess = clip(slope * (t0 - TMIN), 0, cap)`` wherever the archive covers
    the day (uncovered/NaN days carry zero excess). The era is selected from
    the WEATHER-DRIVER year against ``winterized_year`` (PUCT 16 TAC 25.55):
    a pre-weatherization weather year exercises the unhardened fleet's curve.
    Returns ``None`` when the ISO has no curve (mechanism not derived for it
    — rule 25) or no weather coverage.
    """
    from market_sim.config.constants import CORRELATED_OUTAGE_CURVE

    iso_curves = CORRELATED_OUTAGE_CURVE.get((iso or "").upper())
    if not iso_curves:
        return None
    era = "pre" if int(weather_year) < int(winterized_year) else "post"
    curves = iso_curves.get(era)
    if not curves:
        return None
    tmin = correlated_outage_system_tmin(iso, weather_year, hours)
    if tmin is None:
        return None
    depth = np.where(np.isfinite(tmin), float(t0_c) - tmin, 0.0)
    excess: dict[str, np.ndarray] = {}
    shares: dict[str, float] = {}
    for group, c in curves.items():
        excess[group] = np.clip(float(c["slope_per_c"]) * depth, 0.0, float(c["cap"]))
        shares[group] = float(c.get("winter_event_share", 0.0))
    return excess, shares


def apply_correlated_outage_derate(
    fleet_arrays,
    config,
    iso: str,
    year: int,
) -> bool:
    """Apply the correlated cold-event forced-outage derate (gated).

    The gate-and-log wrapper called at the runner's availability seam (next to
    the NEISO cold-snap derate, before the reserve/scarcity inputs are built).
    Gated on ``config.correlated_forced_outage`` and **forecast/hindcast mode
    only**: in a backcast the measured CAMPD outage overlays already carry the
    actual cold-event outages, so applying the statistical event model too
    would double-count the same events (charter D.5).

    Weather-driver resolution: the SOLVE year's own weather when the archive
    covers it (a hindcast leg reads its realized TMIN — 2021 sees Uri), else
    the pinned ``config.weather_year`` sample (a forecast year re-experiences
    the sampled weather year's cold events on the current fleet). Per covered
    class the derate is ADDITIVE on availability — the excess is measured
    over the same NERC-GADS EFORd baseline the statistical WEFOR model is
    built on — after adding back the era's climatological Dec-Feb winter
    event share (in-fleet double-count guard, charter D.3/D.6), clipped to
    [0, 1].

    ORDC seam (charter D.6): this changes ONLY the deterministic mean
    availability. The post-solve ORDC point reserve reads
    ``pmax x availability`` and therefore sees the derate additively and
    correctly; the LOLP convolution's sigma keeps carrying the stochastic
    reserve-error spread (``correlated_outage_sigma_scale`` stays 1.0 unless
    a re-derived reserve-error decomposition identifies otherwise).

    Modifies ``fleet_arrays.availability`` in place. Returns ``True`` when
    any capacity was derated; ``False`` (byte-identical) when gated off, in
    backcast mode, or when the ISO has no curve/weather coverage.
    """
    if not getattr(config, "correlated_forced_outage", False):
        return False
    if getattr(config, "mode", "forecast") != "forecast":
        return False
    if getattr(config, "outage_source", "statistical") == "historic":
        return False  # measured overlays own the events (belt and braces)
    if fleet_arrays.plant_group is None:
        return False
    hours = int(fleet_arrays.availability.shape[1])
    t0_c = float(getattr(config, "correlated_outage_t0_c", -7.0))
    winterized = int(getattr(config, "correlated_outage_winterized_year", 2022))

    weather_year = int(year)
    built = correlated_outage_excess_by_class(
        iso, weather_year, hours, t0_c=t0_c, winterized_year=winterized
    )
    if built is None:
        weather_year = int(getattr(config, "weather_year", year))
        if weather_year != int(year):
            built = correlated_outage_excess_by_class(
                iso, weather_year, hours, t0_c=t0_c, winterized_year=winterized
            )
    if built is None:
        logger.info(
            "%s %d: correlated forced-outage derate armed but no curve/weather "
            "coverage — no-op",
            iso,
            year,
        )
        return False
    excess, shares = built

    month = _MONTH_OF_HOUR[np.arange(hours) % HOURS_PER_YEAR]
    winter = np.isin(month, list(_CORRELATED_OUTAGE_WINTER_MONTHS))
    groups = np.asarray(fleet_arrays.plant_group)
    touched = False
    peak_mw = 0.0
    peak_hour = -1
    for group, ex in excess.items():
        rows = np.flatnonzero((groups == group) & (fleet_arrays.pmax > 0.0))
        if rows.size == 0:
            continue
        adj = shares.get(group, 0.0) * winter.astype(float) - ex
        if not np.any(adj != 0.0):
            continue
        avail = fleet_arrays.availability[rows, :]
        fleet_arrays.availability[rows, :] = np.clip(avail + adj[None, :], 0.0, 1.0)
        touched = True
        derated = (avail - fleet_arrays.availability[rows, :]) * fleet_arrays.pmax[
            rows
        ][:, None]
        by_hour = derated.sum(axis=0)
        h = int(by_hour.argmax())
        if by_hour[h] > peak_mw:
            peak_mw, peak_hour = float(by_hour[h]), h
    if touched and peak_mw > 0.0:
        logger.info(
            "%s %d: correlated forced-outage derate (weather year %d, era %s) — "
            "peak %.0f MW removed at hour %d",
            iso,
            year,
            weather_year,
            "pre" if weather_year < winterized else "post",
            peak_mw,
            peak_hour,
        )
    elif touched:
        logger.info(
            "%s %d: correlated forced-outage derate (weather year %d, era %s) — "
            "no cold event below t0 in the weather year; winter event-share "
            "add-back only",
            iso,
            year,
            weather_year,
            "pre" if weather_year < winterized else "post",
        )
    return touched
