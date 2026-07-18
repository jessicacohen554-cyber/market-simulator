"""Derive *unit-level* outage windows from EPA CAMPD hourly gross generation.

This per-unit detector is the SOLE CAMPD outage source for every ISO. The old
facility-summed detector (``scripts/derive_campd_outages.py``, deleted
2026-07-17) summed every unit at a plant into one CEMS series, so a single-unit
outage at a multi-unit plant — and, critically, a *coal*-unit outage at a mixed
coal/gas facility (W A Parish, Barney M Davis) — was masked by the units that
keep running and never detected, and a daily-cycling combined cycle's
overnight-down gaps folded into phantom summer outages
(``results/calibration/FINDING-ercot79-phantom-outage-2026-07.md``). This script
reads the per-unit CAMPD extracts in
``data/raw/campd-unit-level/{STATE}_{YEAR}.parquet`` (one row per
``unit``-hour, carrying ``unitId``) and detects an outage for each *unit*
independently, on the unit's own gross output. The detection primitives live in
``scripts/lib/outage_detect.py``.

For every sustained unit outage (>= ``--min-outage-days``) it writes one row to
``data/raw/campd-unit-outages.csv`` in the schema the unit-level derate
overlay (:func:`market_sim.data.outages.unit_outage_derate_factors`) consumes:
each row removes the unit's capacity share of its model bin from availability
over the outage window. The unit's capacity is the EIA-860 generator nameplate
(matched on plant code + normalised unit id), falling back to the unit's
observed CAMPD peak gross when no EIA-860 generator matches.

The detector is chosen by the *unit's own fuel*, because what a per-unit output
gap means depends on how the unit is run:

* **Coal** units are baseload — they run continuously when available, so a
  sustained CF below :data:`~scripts.lib.outage_detect.REAL_RUN_CF` genuinely
  marks an outage. They use the averaged real-run rule. This is the layer's core
  job: catch coal-unit outages a facility-summed series would hide behind a
  mixed facility's running gas units (W A Parish 5-8) or behind other coal units
  at a multi-unit plant.
* **Everything else** (combined cycle, gas-steam) is load-following: an idle
  hour is usually economics, not a forced outage, so the averaged rule would
  badly over-flag a merchant CC turbine that simply isn't dispatched. These use
  the **event-based** rule — a window is broken by *any* single hour above
  :data:`~scripts.lib.outage_detect.ST_GAS_CF_PEAK` — so a unit is flagged
  only when it produced essentially nothing for the whole span (a genuine dead
  period), while an economically-idle-but-occasionally-firing unit is left to
  the economic dispatch.

Detection is per calendar year, matching the facility detector; a window
straddling Dec 31 is clipped at the year boundary and each side must
independently clear the duration floor.

Combustion-turbine peakers carry no outage overlay (they dispatch
economically), so plants whose model bin is ``CT_PEAKER`` — and the
``ST_GAS`` peaker plants in
:data:`market_sim.data.outages.ST_GAS_PEAKER_PLANTS` — are skipped, matching the
overlay's convention.

``--short-windows`` derives the companion SHORT extract instead
(``campd-unit-outages-short[-{ISO}].csv``): baseload-coal full stops of 1-5
days, which the standard 5-day duration floor excludes but which concentrate
exactly in stressed periods (MISO Jul 28-29 2025: ~2.8 GW of coal capability
offline at the peak block invisibly to the standard overlay). Identification
guards: coal-only detector + unit annual CF >= :data:`SHORT_BASELOAD_CF` +
the revealed-availability in-merit filter (never bypassed — the full-stop
override cannot engage below 5 days). Windows are capped strictly below the
standard floor so the two extracts are disjoint. Consumed by
``market_sim.data.outages.unit_outage_short_derate_factors`` under
``ScenarioConfig.unit_outage_short_windows`` (default off).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import (  # noqa: E402
    CAMPD_BINS_CSV,
    EIA_860_DIR,
    PROCESSED_DIR,
    RAW_DATA_DIR,
)
from market_sim.data import campd  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    QUALIFYING_PLANT_GROUPS,
    ST_GAS_PEAKER_PLANTS,
    UNIT_OUTAGE_MIN_DAYS,
    unit_outage_csv_for_iso,
)

# Shared CAMPD outage detectors + ERCOT-79-tightened params (the facility-summed
# detector scripts/derive_campd_outages.py was deleted 2026-07-17; this per-unit
# detector is now the sole CAMPD outage source for every ISO).
from scripts.lib.outage_detect import (  # noqa: E402
    FULL_STOP_OVERRIDE_CF,
    FULL_STOP_OVERRIDE_DAYS,
    HIGH_LOAD_PCTL,
    MIN_INMERIT_HOURS,
    ST_GAS_CF_PEAK,
    WINDOW_DAYS,
    detect_outages,
    detect_outages_eventbased,
    filter_revealed_outages,
    high_load_mask,
)

# --partial-windows mode reuses the shared partial-plateau detector and its
# frozen constants VERBATIM (rule 23: measured-behaviour parameters re-derive
# only on source-data change, never on a residual). The only difference is the
# grain — this script feeds the detector each UNIT's own CEMS gross instead of
# the plant sum, so PJM's cycling fleet (whose plant sum over-fires the
# plant-grain detector by ~43 TWh/yr — the plant-grain path stays ERCOT-scoped
# in fleet.py) is read at the grain the phenomenon actually lives at. See
# docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md §7 (leg B).
from scripts.lib.outage_detect import (  # noqa: E402
    _detect as _detect_partial_plateaus,
)


def _partial_plateau_windows(
    gross: np.ndarray, detect_cap: float
) -> tuple[list[tuple[int, int]], dict[tuple[int, int], float]]:
    """Detect unit-grain partial-derate plateaus on one unit's CEMS gross.

    Wraps the plant-level partial-outage deriver's frozen plateau detector
    (:func:`scripts.data.derive_partial_outages._detect`, constants ``_MIN_DAYS`` /
    ``_SMOOTH_DAYS`` / ``_CEILING_FRAC`` / ``_RUN_FLOOR_CF`` VERBATIM) on the
    unit's own capacity factor (``gross / detect_cap``). Returns the plateau
    spans as ``[(start_hour, stop_hour_excl), ...]`` (day boundaries x 24, so
    they slot straight into the same in-merit revealed-availability filter the
    full-stop windows use) alongside ``{(start_hour, stop_hour): derate_factor}``
    — the deriver's measured availability fraction during the plateau (median
    daily-max ceiling / normal-ceiling). The removed capacity written to the
    CSV is ``(1 - derate_factor) x unit_capacity`` over the span.
    """
    if detect_cap <= 0:
        return [], {}
    cf = gross / detect_cap
    windows: list[tuple[int, int]] = []
    factors: dict[tuple[int, int], float] = {}
    for s_day, e_day, factor in _detect_partial_plateaus(cf):
        win = (s_day * 24, e_day * 24)
        windows.append(win)
        factors[win] = factor
    return windows, factors


# CAMPD unit-level extracts live in their own subdirectory; the flat raw-data
# files are facility-summed and carry no unitId.
UNIT_LEVEL_DIR: Path = RAW_DATA_DIR / "campd-unit-level"

# --short-windows mode: the standard overlay's duration floor
# (outages.UNIT_OUTAGE_MIN_DAYS = 5) is this mode's hard CAP, so the short
# extract and the standard extract are disjoint by construction.
SHORT_WINDOW_MAX_DAYS: int = 5
# Baseload guard for short windows — same constant/philosophy as the
# partial-outage detector's _BASELOAD_CF (scripts/data/derive_partial_outages.py):
# only units that normally run near their ceiling qualify, because a cycling
# unit's brief stop can be economic dispatch while a baseload unit's 1-5 day
# full stop (given 10+ h starts and take-or-pay fuel) is a forced event.
SHORT_BASELOAD_CF: float = 0.55

# The revealed-availability (high-load) filter and its constants
# (HIGH_LOAD_PCTL, MIN_INMERIT_HOURS, high_load_mask) are the shared detector
# primitives — imported above from scripts.lib.outage_detect.


def _norm_unit_id(uid: object) -> str:
    """Return an upper-cased alphanumeric-only unit id (drop spaces/dashes)."""
    return re.sub(r"[^0-9A-Za-z]", "", str(uid)).upper()


# EIA-860 prime movers for the combined-cycle steam coupling. A combined
# cycle's combustion turbines (``CT``) exhaust into a heat-recovery boiler that
# drives a separate steam turbine, reported as its own ``CA`` generator. The
# steam turbine burns no fuel, so it has no CAMPD CEMS series and can never be
# detected as an outage on its own — yet when a feeding CT goes down it loses
# that CT's share of steam. Single-shaft combined cycles (``CS``) put the CT and
# its steam turbine on one shaft under a single generator id whose nameplate
# already includes the steam, so they carry no orphaned ``CA`` and must NOT be
# augmented (that would double-count their steam).
_CC_COMBUSTION_PM: str = "CT"
_CC_STEAM_PM: str = "CA"


# A capacity-index entry: ``(detect_mw, derate_mw, cc_augmented)``. ``detect_mw``
# is the unit's own physical nameplate — the CF denominator the outage detector
# thresholds on, so detection is unchanged by the steam coupling. ``derate_mw``
# is the unit's block share written to the CSV (steam-augmented for CC CTs), the
# numerator the availability derate divides into the model bin. They differ only
# for a combined-cycle combustion turbine, where ``derate_mw`` folds in steam.
CapEntry = tuple[float, float, bool]


def build_capacity_index(
    eia860_path: Path,
) -> tuple[
    dict[tuple[int, str], CapEntry],
    dict[tuple[int, str], list[CapEntry]],
]:
    """Return ``(exact, by_digits)`` EIA-860 capacity lookups.

    CAMPD unit ids and EIA-860 generator ids label the same units differently
    (CAMPD ``WAP5`` vs EIA ``5``; CAMPD ``1`` vs EIA ``OG1``), so two lookups
    are built keyed by EIA plant code, each mapping to a :data:`CapEntry`
    ``(detect_mw, derate_mw, cc_augmented)``:

    * ``exact``: ``(plant, NORMALISED_ID) -> CapEntry`` — a direct hit when the
      ids already agree once punctuation/case are normalised.
    * ``by_digits``: ``(plant, DIGITS) -> [CapEntry, ...]`` — matched only when
      a single generator at the plant carries those trailing digits, so
      ``WAP5``/``5`` and ``1``/``OG1`` join without colliding.

    **Combined-cycle steam coupling.** ``detect_mw`` is always the EIA-860
    nameplate (the CF basis for the detector — detection is *not* changed by
    this fix). ``derate_mw`` equals the nameplate too, except a combined-cycle
    combustion turbine (``prime_mover == CT``) at a plant that also carries
    combined-cycle steam (``prime_mover == CA``) is *augmented* by its pro-rata
    share of that steam:

        derate_mw = CT_nameplate * (1 + Σ CA_nameplate / Σ CT_nameplate)

    so the plant's CT shares sum back to the full block (CT + steam) — the same
    basis as the model bin denominator the derate divides into — and one CT out
    derates its turbine *plus* the steam it fed, not the CT alone. The steam
    sums are taken per plant over ``CT``/``CA`` prime movers, so the allocation
    never crosses a split facility (W A Parish's coal/gas ``ST`` units and
    Barney M Davis's gas-steam ``ST`` unit are not ``CT``/``CA`` and neither
    receive nor donate steam) and single-shaft (``CS``) blocks — which carry no
    separate ``CA`` — are left at their steam-inclusive nameplate. The boolean
    flags the augmented entries so :func:`unit_capacity_mw` can label them.
    """
    gens = pd.read_parquet(
        eia860_path,
        columns=["plant_id", "generator_id", "nameplate_capacity_mw", "prime_mover"],
    ).dropna(subset=["generator_id"])
    gens = gens.copy()
    gens["nameplate_capacity_mw"] = pd.to_numeric(
        gens["nameplate_capacity_mw"], errors="coerce"
    )
    gens = gens[gens["nameplate_capacity_mw"] > 0.0]
    # Per-plant combined-cycle steam-allocation factor (1 + ΣCA/ΣCT), built only
    # where the plant carries both a combustion turbine and a distinct steam
    # turbine; absent (factor 1.0) for pure-CT, single-shaft (CS) and non-CC
    # plants.
    ct_sum = (
        gens[gens["prime_mover"] == _CC_COMBUSTION_PM]
        .groupby("plant_id")["nameplate_capacity_mw"]
        .sum()
    )
    ca_sum = (
        gens[gens["prime_mover"] == _CC_STEAM_PM]
        .groupby("plant_id")["nameplate_capacity_mw"]
        .sum()
    )
    steam_factor: dict[int, float] = {}
    for plant_id, cts in ct_sum.items():
        cas = float(ca_sum.get(plant_id, 0.0))
        if float(cts) > 0.0 and cas > 0.0:
            steam_factor[int(plant_id)] = 1.0 + cas / float(cts)

    exact: dict[tuple[int, str], CapEntry] = {}
    by_digits: dict[tuple[int, str], list[CapEntry]] = {}
    for plant_id, gen_id, cap, pm in gens[
        ["plant_id", "generator_id", "nameplate_capacity_mw", "prime_mover"]
    ].itertuples(index=False):
        pid = int(plant_id)
        nameplate = float(cap)
        factor = steam_factor.get(pid, 1.0) if str(pm) == _CC_COMBUSTION_PM else 1.0
        augmented = factor > 1.0
        value: CapEntry = (nameplate, nameplate * factor, augmented)
        full = _norm_unit_id(gen_id)
        exact[(pid, full)] = value
        digits = re.sub(r"\D", "", full)
        if digits:
            by_digits.setdefault((pid, digits), []).append(value)
    return exact, by_digits


def plant_nameplate_index(eia860_path: Path) -> dict[int, float]:
    """Return ``plant_id -> total generator nameplate MW`` from EIA-860."""
    gens = pd.read_parquet(
        eia860_path, columns=["plant_id", "nameplate_capacity_mw"]
    ).dropna()
    out: dict[int, float] = {}
    for plant_id, cap in gens.itertuples(index=False):
        if float(cap) > 0.0:
            out[int(plant_id)] = out.get(int(plant_id), 0.0) + float(cap)
    return out


def unit_capacity_mw(
    plant_id: int,
    unit_id: object,
    exact: dict[tuple[int, str], CapEntry],
    by_digits: dict[tuple[int, str], list[CapEntry]],
    observed_peak: float,
) -> tuple[float, float, str]:
    """Return ``(detect_mw, derate_mw, source)`` for a CAMPD unit.

    Prefers the EIA-860 capacity (exact id match, then a unique trailing-digit
    match); falls back to the unit's observed CAMPD peak gross when no generator
    matches. ``detect_mw`` is the unit's own nameplate — the CF denominator the
    outage detector thresholds on (unchanged by the steam fix) — and
    ``derate_mw`` is the block share written to the CSV. They differ only for a
    combined-cycle combustion turbine, whose ``derate_mw`` folds in its allocated
    steam (see :func:`build_capacity_index`); those rows are labelled
    ``eia_exact_cc`` / ``eia_digits_cc`` so the steam-coupled derates are
    auditable. The observed-peak fallback already folds the CT's steam into its
    CAMPD gross, so its detect and derate capacities are the same.
    """
    full = _norm_unit_id(unit_id)
    if (plant_id, full) in exact:
        detect, derate, augmented = exact[(plant_id, full)]
        return detect, derate, "eia_exact_cc" if augmented else "eia_exact"
    digits = re.sub(r"\D", "", full)
    if digits:
        hits = by_digits.get((plant_id, digits))
        if hits and len(hits) == 1:
            detect, derate, augmented = hits[0]
            return detect, derate, "eia_digits_cc" if augmented else "eia_digits"
    return observed_peak, observed_peak, "observed_peak"


def _unit_year_grid(
    sub: pd.DataFrame,
    year: int,
    col: str = "grossLoad",
    end: pd.Timestamp | None = None,
) -> np.ndarray:
    """Return one unit-year's hourly gross on the calendar-year clock.

    CAMPD omits non-operating hours, so the unit's reported hours are placed on
    a gap-free hourly index spanning the year and missing hours are zero-filled
    (missing = no activity = offline), matching the facility detector.

    ``end`` clips the clock at the year's CAMPD publication horizon (the last
    published date, 23:00): for an in-progress year (e.g. 2026 with only Q1
    posted) the unpublished remainder must NOT be zero-filled, or every unit
    grows a phantom outage from the horizon to Dec 31. Returns the gross-MW
    array (length = hours through ``end``, or the whole year).
    """
    ts = sub["date"] + pd.to_timedelta(sub["hour"], unit="h")
    series = pd.Series(sub[col].to_numpy(dtype=float), index=ts)
    series = series.groupby(level=0).sum().sort_index()
    full = pd.date_range(f"{year}-01-01", end or f"{year}-12-31 23:00:00", freq="h")
    return series.reindex(full).fillna(0.0).to_numpy(dtype=float)


def _load_unit_year(state: str, year: int) -> pd.DataFrame:
    """Load one unit-level state-year extract, or empty when absent."""
    path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
    if not path.exists():
        print(f"  (no unit-level extract for {state} {year}: {path.name})")
        return pd.DataFrame()
    df = pd.read_parquet(
        path,
        columns=[
            "facilityId",
            "facilityName",
            "unitId",
            "date",
            "hour",
            "grossLoad",
            "opTime",
            "primaryFuelInfo",
            "unitType",
        ],
    )
    df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
    df = df.dropna(subset=["facilityId"])
    df["facilityId"] = df["facilityId"].astype(int)
    df["date"] = pd.to_datetime(df["date"])
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce").astype("Int64")
    df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce")
    df["opTime"] = pd.to_numeric(df["opTime"], errors="coerce")
    return df.dropna(subset=["hour"])


def _load_standard_windows(
    path: Path,
) -> dict[tuple[int, str, int], list[tuple[pd.Timestamp, pd.Timestamp]]]:
    """Load the ISO's >= 5-day standard extract keyed for the when-operable guard.

    Returns ``{(facility_id, unit_id, year): [(outage_start, outage_end), ...]}``
    for every ``duration_days >= UNIT_OUTAGE_MIN_DAYS`` window in
    ``campd-unit-outages[-<ISO>].csv`` — the authority on each unit's own long
    outages. The short/partial baseload guard measures a unit's capacity factor
    over the hours it is OPERABLE (outside these windows), so a unit with a
    documented multi-month outage is still recognised as baseload by its running
    capability. Keyed by the window's calendar year (the detector clips each
    window to one calendar year), so the mask only ever removes hours from the
    year being scanned. Empty when the file is absent — the guard then degrades
    to the raw-annual basis (the pre-correction behaviour).
    """
    windows: dict[tuple[int, str, int], list[tuple[pd.Timestamp, pd.Timestamp]]] = {}
    if not path.exists():
        print(
            f"  (no standard extract at {path.name}: when-operable guard falls "
            "back to raw-annual CF)"
        )
        return windows
    df = pd.read_csv(path, parse_dates=["outage_start", "outage_end"])
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    for r in df.itertuples(index=False):
        key = (int(r.facility_id), str(r.unit_id), int(r.outage_start.year))
        windows.setdefault(key, []).append((r.outage_start, r.outage_end))
    return windows


def _operable_mask(
    standard_windows: dict[
        tuple[int, str, int], list[tuple[pd.Timestamp, pd.Timestamp]]
    ],
    facility_id: int,
    unit_id: object,
    year: int,
    n_hours: int,
) -> np.ndarray:
    """Boolean ``(n_hours,)`` mask of WHEN-OPERABLE hours on the year clock.

    ``True`` everywhere except inside the unit's own >= 5-day standard outage
    windows (from :func:`_load_standard_windows`), which are removed so the
    baseload guard measures the unit's capacity factor while it is actually
    operable. Windows are reconstructed day-granular (the CSV stores dates) —
    from the start of ``outage_start`` through the end of ``outage_end`` — the
    same reconstruction the standard loader and the C3c probe use. A unit with
    no standard windows this year yields an all-``True`` mask (raw-annual CF).
    """
    mask = np.ones(n_hours, dtype=bool)
    base = pd.Timestamp(f"{year}-01-01")
    for start, end in standard_windows.get(
        (int(facility_id), str(unit_id), int(year)), ()
    ):
        lo = max(0, int((start - base).total_seconds() // 3600))
        hi = min(
            n_hours,
            int((end + pd.Timedelta(days=1) - base).total_seconds() // 3600),
        )
        if hi > lo:
            mask[lo:hi] = False
    return mask


def _when_operable_cf(
    gross: np.ndarray,
    detect_cap: float,
    standard_windows: dict[
        tuple[int, str, int], list[tuple[pd.Timestamp, pd.Timestamp]]
    ],
    facility_id: int,
    unit_id: object,
    year: int,
) -> float:
    """Return a unit's capacity factor over the hours it is OPERABLE.

    The mean gross output over the hours OUTSIDE the unit's own >= 5-day
    standard outage windows, divided by ``detect_cap`` (the CF denominator the
    baseload guard thresholds on). This is the identification basis for the
    short/partial baseload guard (:data:`SHORT_BASELOAD_CF`): a unit with a
    documented multi-month outage is baseload by its running capability even
    though its raw-annual CF is dragged down by the outage (diagnosis §7). A
    unit with no standard windows this year has an all-operable clock, so this
    reduces to the raw-annual CF. Returns ``0.0`` when there are no operable
    hours or ``detect_cap <= 0``.
    """
    operable = _operable_mask(standard_windows, facility_id, unit_id, year, len(gross))
    oper_gross = gross[operable]
    if not oper_gross.size or detect_cap <= 0:
        return 0.0
    return float(np.mean(oper_gross)) / detect_cap


def _resolve_unit_group(
    is_coal: bool,
    unit_type: str,
    fac_groups: set[str],
    fac_group: str | None,
) -> str:
    """Route a CAMPD unit's outage row to the model bin matching the UNIT.

    ``group_by_code`` keeps ONE group per plant code, so at a mixed
    facility every unit's window landed on that single bin — Chesterfield
    (3797): 1,036 MW of coal units 5/6, out Apr-Dec 2023 for their
    retirement, were tagged CC_REGULAR and blocked the surviving 386 MW
    gas-CC plant for most of 2023 (the pjm-75 2023 CC under-run
    root-cause finding, ~2.35 TWh). Resolution: a solid-fuel unit is
    always COAL; a non-coal unit at a facility whose primary group is
    COAL (or non-qualifying) is routed by its CAMPD ``unitType`` to the
    facility's matching gas bin; otherwise the facility group stands
    (single-group gas facilities are byte-identical). A row routed to a
    ``(plant_code, group)`` bin absent from the model fleet is skipped by
    the overlay (outages.unit_outage_derate_factors) — correct: a retired
    coal unit's window must not derate the surviving gas plant.

    Module-level (not nested in :func:`main`) so the declared-event-window
    sibling deriver (``scripts/data/derive_campd_maxgen_outages.py``) reuses the
    SAME routing verbatim.
    """
    if is_coal:
        return "COAL"
    if fac_group in QUALIFYING_PLANT_GROUPS and fac_group != "COAL":
        return str(fac_group)
    ut = str(unit_type).strip().lower()
    if "combined cycle" in ut:
        for g in ("CC_REGULAR", "CC_CHP"):
            if g in fac_groups:
                return g
        return "CC_REGULAR"
    if "combustion turbine" in ut:
        if "CT_CHP" in fac_groups:
            return "CT_CHP"
        return "CT_PEAKER"  # excluded downstream: peakers carry no overlay
    for g in ("ST_GAS", "ST_CHP"):
        if g in fac_groups:
            return g
    return str(fac_group or "")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument("--min-outage-days", type=float, default=5.0)
    ap.add_argument(
        "--short-windows",
        action="store_true",
        help="Derive the SHORT (< 5-day) baseload-coal window companion file "
        "instead of the standard >= 5-day extract: coal units only, unit "
        "annual CF >= 0.55 (the partial-outage detector's baseload guard — a "
        "cycling unit's brief stop can be economics; a baseload unit's cannot), "
        "windows capped below the standard overlay's 5-day floor so the two "
        "files are disjoint, and the revealed-availability in-merit filter "
        "always enforced (the full-stop override never engages below 5 days). "
        "min-outage-days defaults to 1.0 in this mode; output defaults to "
        "campd-unit-outages-short[-{ISO}].csv.",
    )
    ap.add_argument(
        "--partial-windows",
        action="store_true",
        help="Derive the UNIT-GRAIN partial-derate plateau file "
        "(campd-partial-outages-{ISO}.csv) instead of any full-stop extract: "
        "coal units only, the same WHEN-OPERABLE baseload guard (CF >= 0.55 "
        "outside the unit's own >= 5-day windows) and the same "
        "revealed-availability in-merit filter, but the plateau detector "
        "(scripts/data/derive_partial_outages._detect, constants VERBATIM: 5-day "
        "plateau / 7-day median / ceiling < 0.65x normal / 0.06 run-floor) run "
        "on each UNIT's own CEMS gross. Emits one row per (unit, plateau) with a "
        "derate_factor; consumed by outages.unit_partial_outage_derate_factors "
        "under ScenarioConfig.unit_partial_outage_windows. Mutually exclusive "
        "with --short-windows.",
    )
    ap.add_argument(
        "--no-inmerit-filter",
        action="store_true",
        help="Disable the revealed-availability filter (keep every detected "
        "down span as an outage, the pre-fix behaviour).",
    )
    ap.add_argument(
        "--high-load-pctl",
        type=float,
        default=HIGH_LOAD_PCTL,
        help=f"System-load percentile above which an hour is 'high load' (a "
        f"down unit was needed) (default {HIGH_LOAD_PCTL}).",
    )
    ap.add_argument(
        "--min-inmerit-hours",
        type=int,
        default=MIN_INMERIT_HOURS,
        help=f"High-load hours a span must overlap to count as a real outage "
        f"(default {MIN_INMERIT_HOURS}).",
    )
    ap.add_argument(
        "--high-load-window-days",
        type=int,
        default=WINDOW_DAYS,
        help=f"Centered window (days) the high-load percentile is measured over "
        f"— the LOCAL/seasonal band that keeps real shoulder outages. 0 = legacy "
        f"single-annual percentile (default {WINDOW_DAYS}).",
    )
    ap.add_argument(
        "--fullstop-override-days",
        type=int,
        default=FULL_STOP_OVERRIDE_DAYS,
        help=f"A sustained full-stop (CF<override-cf) lasting >= this many days is "
        f"kept as a mechanical outage regardless of net-load overlap "
        f"(default {FULL_STOP_OVERRIDE_DAYS}).",
    )
    ap.add_argument(
        "--fullstop-override-cf",
        type=float,
        default=FULL_STOP_OVERRIDE_CF,
        help=f"Span mean-CF below which the full-stop override treats a long down "
        f"span as a mechanical outage (default {FULL_STOP_OVERRIDE_CF}).",
    )
    ap.add_argument(
        "--no-fullstop-override",
        action="store_true",
        help="Disable the full-stop duration override (keep only the net-load "
        "revealed-availability test).",
    )
    ap.add_argument(
        "--bins",
        default=str(CAMPD_BINS_CSV),
        help="Per-plant bin CSV; supplies each facility's model plant group.",
    )
    ap.add_argument(
        "--eia860",
        default=str(EIA_860_DIR / "eia860_generators.parquet"),
        help="EIA-860 generator parquet, for per-unit nameplate capacity.",
    )
    ap.add_argument(
        "--out",
        default=None,
        help="Output CSV; defaults to data/raw/campd-unit-outages.csv "
        "(ERCOT) or campd-unit-outages-{ISO}.csv.",
    )
    args = ap.parse_args()
    if args.short_windows and args.partial_windows:
        raise SystemExit("--short-windows and --partial-windows are mutually exclusive")
    if args.no_fullstop_override:
        args.fullstop_override_days = 10**9
    if args.short_windows and args.min_outage_days == 5.0:
        args.min_outage_days = 1.0  # the mode's floor; the 5-day cap is fixed
    if args.short_windows and args.min_inmerit_hours == MIN_INMERIT_HOURS:
        # The parent gate's 24 h floor is sized for >= 5-day (>= 120 h) spans —
        # a ~20% overlap fraction. Keep the same fraction for the mode's
        # minimum span (24 h): 6 high-net-load hours. Explicit
        # --min-inmerit-hours still wins.
        args.min_inmerit_hours = 6
    # Partial mode keeps the parent >= 5-day plateau length (the detector's own
    # _MIN_DAYS = 5), so the default 24 h in-merit floor applies unchanged.
    min_outage_hours = int(round(args.min_outage_days * 24))
    # Short mode: windows must stay strictly below the standard overlay's
    # UNIT_OUTAGE_MIN_DAYS floor so the two extracts are disjoint by
    # construction (outages.unit_outage_short_derate_factors re-enforces it).
    short_max_hours = SHORT_WINDOW_MAX_DAYS * 24 if args.short_windows else None
    if args.short_windows and min_outage_hours >= (short_max_hours or 0):
        raise SystemExit(
            "--short-windows requires --min-outage-days < "
            f"{SHORT_WINDOW_MAX_DAYS} (got {args.min_outage_days})"
        )
    iso = args.iso.upper()
    if args.out is None:
        if args.partial_windows:
            # The unit-grain partial file is ALWAYS ISO-suffixed (ERCOT
            # included) so it never collides with the plant-grain ERCOT
            # campd-partial-outages.csv (a different datatype, ERCOT-scoped in
            # fleet.py). Matches outages.unit_partial_outage_csv_for_iso.
            fname = f"campd-partial-outages-{iso}.csv"
        elif args.short_windows:
            fname = (
                "campd-unit-outages-short.csv"
                if iso == "ERCOT"
                else f"campd-unit-outages-short-{iso}.csv"
            )
        else:
            fname = (
                "campd-unit-outages.csv"
                if iso == "ERCOT"
                else f"campd-unit-outages-{iso}.csv"
            )
        args.out = str(RAW_DATA_DIR / fname)

    # Each facility's model plant group (the LP bin the derate routes into).
    # Split facilities (W A Parish 3470, Barney M Davis 4939) carry their
    # primary group here; the overlay's _unit_outage_target re-routes their
    # gas-steam units to the split code by unit id, so the group passed for
    # them is immaterial.
    #
    # ERCOT sources the plant->group map from the CAMPD bin sheet
    # (custom-bin-assignments.csv); other ISOs have no bin sheet and run a
    # per-plant EIA-860 fleet, so their group map comes from the fleet's
    # plant_group (the same source _fleet_group_by_code / the benchmark backfill
    # use). Without this every non-ERCOT facility missed the bin sheet, fell
    # through QUALIFYING_PLANT_GROUPS, and produced zero unit-outage windows.
    name_by_code: dict[int, str] = {}
    # ALL model plant groups at a plant code (a mixed coal/CC facility like
    # Chesterfield 3797 carries several) — the per-unit group resolver below
    # routes each CAMPD unit's outage to the bin matching the UNIT's own
    # class, not whichever group the last fleet row happened to carry.
    groups_by_code: dict[int, set[str]] = {}
    # Per-plant MODELED steam (ST_GAS / ST_CHP) nameplate — the capacity basis
    # for the orphaned gross-blank steam-host boiler fallback below (non-ERCOT).
    steam_np_by_code: dict[int, float] = {}

    if iso == "ERCOT":
        bins = pd.read_csv(args.bins)
        group_by_code = {
            int(c): str(g) for c, g in zip(bins["Plant_Code"], bins["Plant_Group"])
        }
    else:
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.fleet import (
            load_fleet_from_csv,
            load_retired_within_window,
        )

        iso_config = get_iso_config(iso)
        group_by_code = {}
        # Within-window plant exits dispatch in the backcast fleet too, so they
        # need their observed CEMS outage windows derived — else an injected
        # retiree (e.g. Mystic) runs uncapped at its full economic merit.
        fleet = load_fleet_from_csv(iso, iso_config) + load_retired_within_window(
            iso, iso_config
        )
        for g in fleet:
            if int(g.plant_code) > 0 and g.plant_group:
                group_by_code[int(g.plant_code)] = g.plant_group
                name_by_code[int(g.plant_code)] = g.name
                groups_by_code.setdefault(int(g.plant_code), set()).add(g.plant_group)
                if g.plant_group in ("ST_GAS", "ST_CHP"):
                    steam_np_by_code[int(g.plant_code)] = steam_np_by_code.get(
                        int(g.plant_code), 0.0
                    ) + float(g.pmax_mw)
    # Facility names for units re-keyed by the CEMS->EIA split-plant remap
    # (their CAMPD facilityName is the legacy plant's).
    remap_names = {
        c: name_by_code[c]
        for c in set(campd.CAMPD_UNIT_PLANT_REMAP.values())
        if c in name_by_code
    }

    exact, by_digits = build_capacity_index(Path(args.eia860))
    npl_by_plant = plant_nameplate_index(Path(args.eia860))

    # When-operable baseload guard (short + partial modes): load the ISO's
    # >= 5-day standard extract so a unit's CF is measured over the hours it is
    # OPERABLE (outside its own long outages). A unit with a documented
    # multi-month outage is baseload by its running capability, which the
    # raw-annual CF hides (diagnosis §7: event-unit when-operable CF 0.58-0.72
    # vs raw-annual 0.09-0.36). Identification correction cited to that
    # measurement, not to a price residual; empty when the standard file is
    # absent (guard degrades to raw-annual).
    standard_windows = (
        _load_standard_windows(unit_outage_csv_for_iso(iso))
        if (args.short_windows or args.partial_windows)
        else {}
    )

    states = campd.states_for_iso(iso)
    rows: list[dict] = []
    summary: list[tuple] = []
    # (year, clock length) -> in-merit (system-tight) hour mask.
    inmerit_cache: dict[tuple[int, int], np.ndarray | None] = {}
    # (facility, year) -> any non-null CAMPD grossLoad seen; feeds the
    # net-zero-to-grid rule below (mirrors the benchmark's CAMPD backfill).
    campd_gross_seen: set[tuple[int, int]] = set()
    for state in states:
        for year in args.years:
            df = _load_unit_year(state, year)
            if df.empty:
                continue
            # Publication horizon: last date this state-year extract covers.
            # A completed year runs to Dec 31 (clock unchanged); an
            # in-progress year (CAMPD posts quarterly) is clipped here so the
            # unpublished remainder is never scanned as a phantom outage.
            horizon_end = df["date"].max() + pd.Timedelta(hours=23)
            for fac_id, has in (
                df.groupby("facilityId", observed=True)["grossLoad"]
                .apply(lambda s: s.notna().any())
                .items()
            ):
                if has:
                    campd_gross_seen.add((int(fac_id), year))
            # CEMS->EIA split-plant remap (campd.CAMPD_UNIT_PLANT_REMAP):
            # re-key units that report under a legacy ORIS to the EIA plant
            # the model fleet carries (AES Alamitos / Huntington Beach CCGTs),
            # BEFORE the group lookup and the peaker-exclusion check, so the
            # new CC plants get their own windows and the legacy steamers'
            # exclusion does not swallow them.
            df["facilityId"] = [
                campd.CAMPD_UNIT_PLANT_REMAP.get((f, u), f)
                for f, u in zip(df["facilityId"].astype(int), df["unitId"].astype(str))
            ]
            for fac_id, fac in df.groupby("facilityId", observed=True):
                group = group_by_code.get(int(fac_id))
                fac_groups = groups_by_code.get(
                    int(fac_id), {group} if group else set()
                )
                # Only the coal/CC/gas-steam fleet carries an outage overlay;
                # peakers (CT and the listed ST_GAS peakers) dispatch
                # economically and are skipped, matching the overlay. A
                # facility qualifies when ANY of its model bins does — a
                # mixed plant whose primary lookup lands on CT_PEAKER can
                # still carry derivable coal/CC units (per-unit resolution
                # below routes and skips unit-by-unit).
                if not (fac_groups & QUALIFYING_PLANT_GROUPS):
                    continue
                if int(fac_id) in ST_GAS_PEAKER_PLANTS:
                    continue
                fac_name = remap_names.get(
                    int(fac_id), str(fac["facilityName"].iloc[0])
                )
                units = {
                    uid: _unit_year_grid(u, year, end=horizon_end)
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                # A unit is coal (baseload) when its primary fuel is solid;
                # CAMPD labels every solid fuel — including ERCOT's lignite —
                # as "Coal".
                unit_is_coal = {
                    uid: str(u["primaryFuelInfo"].iloc[0]).strip().lower()
                    in ("coal", "coal refuse")
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                unit_type = {
                    uid: str(u["unitType"].iloc[0])
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                # Per-unit (detect_mw, derate_mw, source) — the detector's CF
                # basis and the CSV's block share — plus the facility derate
                # total for the informational pct column.
                peaks = {uid: float(g.max()) for uid, g in units.items()}
                caps: dict[object, tuple[float, float, str]] = {
                    uid: unit_capacity_mw(
                        int(fac_id), uid, exact, by_digits, peaks[uid]
                    )
                    for uid in units
                }
                # Gross-silent facility fallback (non-ERCOT): some units
                # report opTime but never grossLoad (Seward's CFB boilers),
                # so the gross-based detector is blind to them in every year.
                # When NO unit at the facility reports any gross, rebuild the
                # unit series as a BINARY operated/idle proxy x an equal
                # share of the EIA-860 plant nameplate: a boiler that
                # operated at all in an hour was available (fractional
                # opTime is cycling, not an outage — scaling by the fraction
                # over-flags sustained part-load spans as outages under the
                # coal rule). Boiler<->generator id matching is unreliable
                # at such plants, so the equal split (not the per-unit EIA
                # match) is the capacity basis: one boiler down at a
                # two-boiler CFB derates half the plant.
                if iso != "ERCOT" and all(p <= 0.0 for p in peaks.values()):
                    npl = npl_by_plant.get(int(fac_id), 0.0)
                    ot_units = {
                        uid: u
                        for uid, u in fac.groupby("unitId", observed=True)
                        if float(
                            pd.to_numeric(u["opTime"], errors="coerce")
                            .fillna(0.0)
                            .max()
                        )
                        > 0.0
                    }
                    if npl > 0.0 and ot_units:
                        share = npl / len(ot_units)
                        units = {
                            uid: np.where(
                                _unit_year_grid(u, year, col="opTime", end=horizon_end)
                                > 0.0,
                                share,
                                0.0,
                            )
                            for uid, u in ot_units.items()
                        }
                        peaks = {uid: float(g.max()) for uid, g in units.items()}
                        caps = {uid: (share, share, "optime_proxy") for uid in units}
                # Orphaned gross-blank STEAM-HOST boiler fallback (non-ERCOT,
                # MIXED facilities). The facility-wide opTime proxy above only
                # fires when EVERY unit is gross-blank. A steam-CHP host boiler
                # (ST_CHP / ST_GAS) that logs opTime but never grossLoad — its
                # output serves the host behind the meter — is otherwise skipped
                # (peaks<=0 -> continue below) whenever it shares a facility with
                # a gross-reporting unit, so its outages go uncaptured and the
                # flat chp_grid_pmin_mw steam floor force-generates it. Rebuild
                # ONLY such units from their own binary opTime proxy (operated =
                # available) x an equal share of the plant's MODELED steam (ST_*)
                # nameplate, so a genuine multi-day boiler stop is caught while a
                # host that keeps running yields no outage. Tightly gated to be
                # over-detection-proof:
                #   * a MODELED steam bin must exist at the plant (steam_grp in
                #     fac_groups) — this alone excludes every auxiliary/startup
                #     boiler at a COAL or CC_CHP plant (those carry no ST_* bin,
                #     so their aux boilers — idle most of the year — are never
                #     turned into a phantom full-year outage that would derate
                #     the running plant; verified: Gavin 8102, Cardinal 2828,
                #     Rockport 6166, the WV coal plants all carry {COAL} only),
                #   * the unit's CAMPD unitType must be a fired steam boiler
                #     (not a combustion turbine / combined-cycle block), and
                #   * only whole-year gross-blank units (peaks<=0) are rebuilt,
                #     so a gross-reporting unit with a data gap is untouched.
                # Capacity = the plant's ST_* nameplate split equally across its
                # blank steam boilers (per-unit EIA id matching is unreliable for
                # behind-the-meter boilers and can mis-grab a large main-unit
                # generator — the equal steam split mirrors the facility-wide
                # fallback). Event-break fragmentation (a looser CF break for
                # ST_CHP) was measured and REJECTED: a +48 h spike tolerance
                # recovers only ~1.5 % more outage-days and 0 net windows on the
                # PJM ST_CHP opTime-proxy set, so the strict ST_GAS_CF_PEAK break
                # stays (a looser break would relabel steam-following economic
                # cycling as outage for no real gain). Evidence: PJM Grays Ferry
                # (54785) unit 25 (56.6 MW ST_CHP wall-fired boiler; opTime
                # ~8.5k h/yr, no grossLoad any year) shares the plant with the
                # gross-reporting 114 MW CT (unit 2); it takes one genuine 6-9 d
                # maintenance stop each year (2023/24/25) this fallback now
                # captures, relieving the ST_CHP floor over the plant-wide outage.
                forced_group: dict[object, str] = {}
                if iso != "ERCOT" and not all(p <= 0.0 for p in peaks.values()):
                    steam_grp = (
                        "ST_CHP"
                        if "ST_CHP" in fac_groups
                        else ("ST_GAS" if "ST_GAS" in fac_groups else None)
                    )
                    steam_np = steam_np_by_code.get(int(fac_id), 0.0)
                    if steam_grp is not None and steam_np > 0.0:
                        blank_boilers: dict[object, np.ndarray] = {}
                        for uid, u in fac.groupby("unitId", observed=True):
                            if peaks.get(uid, 0.0) > 0.0:
                                continue
                            ut = str(u["unitType"].iloc[0]).strip().lower()
                            if "turbine" in ut or "combined cycle" in ut:
                                continue
                            if not any(
                                k in ut
                                for k in ("fired", "boiler", "stoker", "cyclone")
                            ):
                                continue
                            ot = _unit_year_grid(u, year, col="opTime", end=horizon_end)
                            if (ot > 0.0).any():
                                blank_boilers[uid] = ot
                        if blank_boilers:
                            share = steam_np / len(blank_boilers)
                            for uid, ot in blank_boilers.items():
                                proxy = np.where(ot > 0.0, share, 0.0)
                                units[uid] = proxy
                                peaks[uid] = float(proxy.max())
                                caps[uid] = (share, share, "optime_proxy_steam")
                                forced_group[uid] = steam_grp
                fac_cap = sum(derate for _, derate, _ in caps.values()) or 0.0
                ran = {uid for uid, pk in peaks.items() if pk > 0.0}
                for uid, gross in units.items():
                    detect_cap, derate_cap, cap_src = caps[uid]
                    # A unit that never reported gross output this year is
                    # left to the statistical/facility layers — we cannot
                    # distinguish a real full-year outage from a unit monitored
                    # under another id, and have no capacity basis for it.
                    if peaks[uid] <= 0.0 or derate_cap <= 0.0:
                        continue
                    # Route this unit's window to ITS model bin (non-ERCOT;
                    # ERCOT keeps the bin-sheet group verbatim and reroutes
                    # its split plants downstream in _unit_outage_target).
                    # A steam-host boiler rebuilt by the orphaned-blank fallback
                    # above carries an explicit forced steam group (the resolver's
                    # fac_group short-circuit would otherwise mis-route it to a
                    # sibling CT_CHP bin at a mixed CT/ST plant like Grays Ferry).
                    ugroup = (
                        group
                        if iso == "ERCOT"
                        else forced_group.get(uid)
                        or _resolve_unit_group(
                            unit_is_coal[uid],
                            unit_type.get(uid, ""),
                            fac_groups,
                            group,
                        )
                    )
                    if ugroup not in QUALIFYING_PLANT_GROUPS:
                        continue
                    # Short/partial modes: baseload coal only, WHEN-OPERABLE
                    # basis. A cycling unit's brief stop can be economics; a
                    # baseload coal unit's cannot (10+ h starts, take-or-pay
                    # fuel) — the same 0.55 guard (SHORT_BASELOAD_CF) the
                    # partial-outage detector uses (_BASELOAD_CF). The CF is
                    # measured over the hours the unit is OPERABLE (excluding its
                    # own >= 5-day standard windows), NOT over raw annual hours,
                    # so a unit with a documented multi-month outage is still
                    # recognised as baseload by its running capability. The
                    # raw-annual basis contradicted the guard's own stated intent
                    # ("units that normally run near their ceiling"): diagnosis §7
                    # measured 9 of 11 event units spuriously failing on
                    # raw-annual CF (0.09-0.36) that pass on when-operable CF
                    # (0.58-0.72). Identification correction cited to that
                    # measurement, not to a price residual (rule 23), applied
                    # uniformly to any ISO's re-derive.
                    if args.short_windows or args.partial_windows:
                        if not unit_is_coal[uid]:
                            continue
                        oper_cf = _when_operable_cf(
                            gross, detect_cap, standard_windows, int(fac_id), uid, year
                        )
                        if oper_cf < SHORT_BASELOAD_CF:
                            continue
                    # Partial mode: unit-grain CF-ceiling plateaus (>= 5-day
                    # sustained derates) from the plant-level detector's frozen
                    # rule, run on THIS unit's own CEMS (the guard above has
                    # already restricted to baseload coal). Full-stop modes:
                    # coal (baseload) uses the sustained-low-output-gap rule;
                    # everything else (load-following CC / gas-steam) only a
                    # genuine dead span — no output at all — via the event-based
                    # rule, so economic idleness is not over-flagged. The
                    # detector thresholds on the unit's own nameplate
                    # (detect_cap), so the CC steam allocation — which lifts only
                    # the derate share — leaves every detected window unchanged.
                    plateau_factors: dict[tuple[int, int], float] = {}
                    if args.partial_windows:
                        windows, plateau_factors = _partial_plateau_windows(
                            gross, detect_cap
                        )
                    elif unit_is_coal[uid]:
                        windows = detect_outages(gross, detect_cap, min_outage_hours)
                    else:
                        windows = detect_outages_eventbased(
                            gross, detect_cap, min_outage_hours, ST_GAS_CF_PEAK
                        )
                    if short_max_hours is not None:
                        # Keep only sub-floor windows; >= 5-day spans belong to
                        # the standard extract (disjointness by construction).
                        # The cap tests the ROUNDED duration the loader filters
                        # on (< UNIT_OUTAGE_MIN_DAYS), so a 119.5 h span that
                        # would round to 5.0 days is not emitted into a crack
                        # where both loaders drop it.
                        windows = [
                            (s, e)
                            for s, e in windows
                            if (e - s) < short_max_hours
                            and round((e - s) / 24.0, 1) < SHORT_WINDOW_MAX_DAYS
                        ]
                    if not windows:
                        continue
                    clock = pd.date_range(f"{year}-01-01", horizon_end, freq="h")
                    # Revealed-availability filter: drop down spans that never
                    # overlap an in-merit (system-tight) hour — those are
                    # economic idling, not mechanical outages, so the unit is
                    # left available (not removed from energy or the co-opt
                    # reserve pool). Real outages coincide with tight hours and
                    # survive. No-op when --no-inmerit-filter or no price file.
                    if not args.no_inmerit_filter:
                        # Keyed on (year, clock length): an in-progress year's
                        # clipped clock must not reuse a full-year mask.
                        mkey = (year, len(clock))
                        if mkey not in inmerit_cache:
                            inmerit_cache[mkey] = high_load_mask(
                                iso,
                                year,
                                len(clock),
                                args.high_load_pctl,
                                args.high_load_window_days,
                            )
                        mask = inmerit_cache[mkey]
                        cf = (
                            gross / detect_cap
                            if detect_cap > 0
                            else np.zeros_like(gross)
                        )
                        windows = filter_revealed_outages(
                            windows,
                            mask,
                            cf,
                            args.min_inmerit_hours,
                            args.fullstop_override_days,
                            args.fullstop_override_cf,
                        )
                        if not windows:
                            continue
                    out_days = 0.0
                    for s, e in windows:
                        start = clock[s]
                        last = clock[e - 1]
                        duration_days = round((e - s) / 24.0, 1)
                        out_days += duration_days
                        peers = sum(1 for o in ran if o != uid)
                        row = {
                            "facility_name": fac_name,
                            "facility_id": int(fac_id),
                            "unit_id": uid,
                            "unit_capacity_mw": round(derate_cap, 1),
                            "plant_capacity_mw": round(fac_cap, 1),
                            "unit_pct_of_plant": (
                                round(100.0 * derate_cap / fac_cap, 1)
                                if fac_cap
                                else None
                            ),
                            "plant_group": ugroup,
                            "capacity_source": cap_src,
                            "outage_start": start.strftime("%Y-%m-%d"),
                            "outage_end": last.strftime("%Y-%m-%d"),
                            "duration_days": duration_days,
                            "peer_units_online": peers,
                            "total_units_at_plant": len(units),
                        }
                        if args.partial_windows:
                            # The measured availability fraction the unit ran at
                            # during the plateau: the consumer removes
                            # (1 - derate_factor) x unit_capacity from the plant
                            # bin over the window (partial derate, not a full
                            # stop).
                            row["derate_factor"] = round(plateau_factors[(s, e)], 3)
                        rows.append(row)
                    if out_days > 0:
                        summary.append(
                            (
                                int(fac_id),
                                fac_name,
                                uid,
                                ugroup,
                                year,
                                len(windows),
                                out_days,
                            )
                        )

    # Net-zero-to-grid years (non-ERCOT). A fleet plant that reported real
    # grid generation in an earlier EIA-923 year but, in a target year, has
    # no F923 filing AND no CAMPD gross output (so the benchmark's CAMPD
    # backfill can't see it either) delivered nothing the benchmark counts —
    # even when CAMPD opTime shows its boilers running (the PA waste-coal
    # behind-the-meter crypto conversions: Gilberton, Panther Creek,
    # Scrubgrass, Grant Town). An explicit ~zero F923 filing counts too.
    # Plants that stopped filing F923 but still report CAMPD gross (Colver,
    # Cordova) are NOT flagged: the benchmark backfills them and they
    # genuinely serve the grid. One full-year window per plant-year.
    if iso != "ERCOT" and not args.short_windows and not args.partial_windows:
        # The net-zero full-year fallback belongs to the standard extract
        # only — the short file carries nothing but sub-5-day windows, and the
        # partial file carries nothing but detected CF-ceiling plateaus.
        e923 = pd.read_parquet(
            PROCESSED_DIR / "eia923_monthly_generation.parquet",
            columns=["plant_id", "netgen_annual_mwh", "year"],
        )
        tot = e923.groupby(["plant_id", "year"])["netgen_annual_mwh"].sum(min_count=1)
        years_in_923 = sorted(e923["year"].unique())
        for fac_id, group in sorted(group_by_code.items()):
            if group not in QUALIFYING_PLANT_GROUPS:
                continue
            if int(fac_id) in ST_GAS_PEAKER_PLANTS:
                continue
            npl = npl_by_plant.get(int(fac_id), 0.0)
            if npl <= 0.0:
                continue
            for year in args.years:
                if year not in years_in_923:
                    continue
                t = tot.get((fac_id, year))
                prior = [tot.get((fac_id, y)) for y in years_in_923 if y < year]
                ran_before = any(
                    p is not None and not pd.isna(p) and p > 10_000.0 for p in prior
                )
                filed = t is not None and not pd.isna(t)
                zero_now = (filed and t < 1_000.0) or (
                    not filed and (int(fac_id), year) not in campd_gross_seen
                )
                if not (ran_before and zero_now):
                    continue
                rows.append(
                    {
                        "facility_name": name_by_code.get(int(fac_id), ""),
                        "facility_id": int(fac_id),
                        "unit_id": "NET0-923",
                        "unit_capacity_mw": round(npl, 1),
                        "plant_capacity_mw": round(npl, 1),
                        "unit_pct_of_plant": 100.0,
                        "plant_group": group,
                        "capacity_source": "eia923_netzero",
                        "outage_start": f"{year}-01-01",
                        "outage_end": f"{year}-12-31",
                        "duration_days": 365.0,
                        "peer_units_online": 0,
                        "total_units_at_plant": 1,
                    }
                )
                summary.append(
                    (
                        int(fac_id),
                        name_by_code.get(int(fac_id), ""),
                        "NET0-923",
                        group,
                        year,
                        1,
                        365.0,
                    )
                )

    cols = [
        "facility_name",
        "facility_id",
        "unit_id",
        "unit_capacity_mw",
        "plant_capacity_mw",
        "unit_pct_of_plant",
        "plant_group",
        "capacity_source",
        "outage_start",
        "outage_end",
        "duration_days",
        "peer_units_online",
        "total_units_at_plant",
    ]
    if args.partial_windows:
        # Unit-grain partial file carries the measured availability fraction the
        # unit ran at during each plateau (the extra column vs the full-stop
        # extracts); the consumer removes (1 - derate_factor) x unit_capacity.
        cols.append("derate_factor")
    out = pd.DataFrame(rows, columns=cols).sort_values(
        ["facility_id", "unit_id", "outage_start"]
    )
    out.to_csv(args.out, index=False)

    label = "partial-derate plateau" if args.partial_windows else "unit-outage"
    print(f"\nwrote {len(out)} {label} windows to {args.out}\n")
    print(
        f"{'code':>6} {'plant':<24}{'unit':<8}{'group':<11}{'yr':>5}"
        f"{'#win':>5}{'out d':>8}"
    )
    for code, nm, uid, g, yr, n, td in sorted(
        summary, key=lambda r: (r[0], str(r[2]), r[4])
    ):
        print(f"{code:>6} {nm[:23]:<24}{str(uid):<8}{g:<11}{yr:>5}{n:>5}{td:>8.0f}")


if __name__ == "__main__":
    main()
