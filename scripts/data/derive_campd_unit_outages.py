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

``--hour-grain`` (default off) additionally emits ``outage_start_hour`` /
``outage_end_hour``, the DETECTED hour-of-day of each window's first and last
outage hour. Detection has always been hourly while the extract stored dates, so
``market_sim.data.outages`` had to re-expand every window to 00:00-23:00 and
asserted up to 23 h per edge the detector never detected — precisely where the
event-based contract guarantees the neighbouring hour was *running*
(``results/calibration/FINDING-caiso181-envelope-depth-2026-08-07.md`` section 2
measured this at 100 % of unit-grain CEMS contradictions). The two columns are
OPTIONAL and per-ISO adoptable: the loader consumes them when present and falls
back to the day-granular reconstruction when absent, and the flag-absent extract
is byte-identical, so an ISO adopts the finer grain by re-deriving its own
extract and nothing else (rule 25 ``[R-ISO-SCOPE]``). Zero DOF — no parameter,
threshold or detector constant is involved.
"""

from __future__ import annotations

import argparse
import json
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
from market_sim.config.plant_taxonomy import artifact_class  # noqa: E402
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
    MERIT_OOM_FRAC,
    MERIT_RCC_PCTL,
    MIN_INMERIT_HOURS,
    ST_GAS_CF_PEAK,
    WINDOW_DAYS,
    build_merit_order_panel,
    detect_outages,
    detect_outages_eventbased,
    filter_merit_order_layup,
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

# --short-window-groups: which model plant groups the SHORT (< 5-day) mode
# emits (pjm-d4-4). "coal" is the frozen baseload-coal scope; "gas" is the
# disjoint gas-side companion, whose windows go to their own extract so the
# coal file is never rewritten (the miso-200 / nyiso-175b separate-companion
# discipline). The two scopes never share a plant group, so the two extracts
# stack no capacity on each other (rule 19 [R-ONE-MECH]).
#
# The gas scope's identification is NOT the coal scope's. `SHORT_BASELOAD_CF`
# is a BASELOAD guard: it keeps economic idling out by admitting only units
# that normally run near their ceiling, which is a property coal has and a
# cycling CC does not. Applying it to gas would admit nothing; omitting it
# without a replacement would admit economic cycling. The gas scope therefore
# carries the MERIT-ORDER guard instead — the direct economic test (the unit's
# own measured SRMC against the revealed clearing cost of the capacity that WAS
# running, scripts/lib/outage_detect.filter_merit_order_layup) — which asks the
# economic question rather than proxying it by duty cycle. Declared ex ante and
# measured against interest: it removes 10.8 % of the recovered PJM 2022 annual
# mean and 5.1 % of its tail-hour family, i.e. it selects the SMALLER family,
# and both scopes clear the pre-registered gate either way
# (docs/RESULT-pjm-d4-4-forced-outage-composition-2026-09-10.md section 4).
SHORT_WINDOW_GAS_GROUPS: frozenset[str] = frozenset(
    {"CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP"}
)

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


def _union_vintage_membership(
    iso: str,
    iso_config,
    years,
    group_by_code: dict[int, str],
    groups_by_code: dict[int, set[str]],
    name_by_code: dict[int, str],
) -> None:
    """Union each derive year's OWN EIA-860 vintage fleet into the membership.

    The default membership is the canonical (latest) fleet plus the canonical
    within-window whole-plant retirees, so a PARTIAL-plant exit — coal units
    retired while the site's CTs survive (PJM: Morgantown 1573, Dickerson 1572,
    Wagner 1554, Indian River 594) — is keyed on its SURVIVING class (CT_PEAKER,
    or an empty oil group) and its coal units are never scanned, although the
    year's own vintage fleet dispatches them. This is the outage-extract twin of
    ``benchmark_membership_vintage_union``: the facility's class set becomes the
    union over the vintages of the years derived. The canonical primary group is
    kept where present (it only drives the fallback router); per-unit routing
    still reads the unit's own CAMPD fuel, so a coal unit routes to the coal
    family and a surviving CT to CT_PEAKER (skipped) exactly as before. Zero
    free parameters. Mutates the three maps in place; restores the canonical
    EIA-860 directory on exit.
    """
    from market_sim.config.paths import set_eia860_vintage
    from market_sim.config.plant_taxonomy import artifact_class
    from market_sim.data.fleet import load_fleet_from_csv

    try:
        for y in sorted({int(v) for v in years}):
            set_eia860_vintage(y)
            for g in load_fleet_from_csv(iso, iso_config):
                pc = int(g.plant_code)
                if pc <= 0 or not g.plant_group:
                    continue
                ag = artifact_class(g.plant_group)
                groups_by_code.setdefault(pc, set()).add(ag)
                group_by_code.setdefault(pc, ag)
                name_by_code.setdefault(pc, g.name)
    finally:
        set_eia860_vintage(None)


def _merit_member_facilities(
    detection_states: tuple[str, ...],
    panel_states: tuple[str, ...],
    years: list,
    group_by_code: dict[int, str],
) -> dict[str, tuple[int, ...]]:
    """Out-of-panel detection states' facilities that are the ISO's own fleet.

    The merit-panel MEMBERSHIP derivation
    (``campd.MERIT_PANEL_FLEET_MEMBER_ISOS``;
    PRECHECK-caiso200-panel-membership-2026-08-17.md §1–§2): a facility in a
    detection state outside the panel state list joins the panel iff its plant
    code — via the CEMS→EIA split-plant remap where one applies — resolves
    into the ISO's own fleet registry, the same ``group_by_code`` the
    detection path filters on. Derived, never enumerated (rule 24
    ``[R-REGISTRY]``); today CAISO resolves to exactly ``{NV: (55077,)}``.
    Admission is facility-grained, matching the caiso-198 run-Y construction
    the charter's sha pins were measured on.
    """
    panel = set(panel_states)
    out: dict[str, tuple[int, ...]] = {}
    for st in detection_states:
        if st in panel:
            continue
        members: set[int] = set()
        for year in years:
            path = UNIT_LEVEL_DIR / f"{st}_{int(year)}.parquet"
            if not path.exists():
                continue
            pairs = pd.read_parquet(path, columns=["facilityId", "unitId"])
            fid = pd.to_numeric(pairs["facilityId"], errors="coerce")
            pairs = pairs.assign(facilityId=fid).dropna(subset=["facilityId"])
            for f, u in pairs.drop_duplicates().itertuples(index=False):
                code = campd.CAMPD_UNIT_PLANT_REMAP.get((int(f), str(u)), int(f))
                if int(code) in group_by_code:
                    members.add(int(f))
        if members:
            out[st] = tuple(sorted(members))
    return out


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


def _unit_gross_years(
    states: tuple[str, ...] | list[str], years: list[int]
) -> set[tuple[int, str, int]]:
    """Return ``{(facility, unit_id, year)}`` with positive CAMPD gross output.

    Scans the run years plus one year either side (where a state-year extract
    exists), keyed on the SAME split-plant remapped facility id the detector
    loop uses. Feeds ``--dark-unit-years``: a unit dark for all of ``year`` is
    admitted only when this set shows its own id producing in ``year - 1`` or
    ``year + 1`` -- the evidence that the id is the unit's real monitoring
    location rather than a retired or re-keyed stack.
    """
    out: set[tuple[int, str, int]] = set()
    span = range(min(years) - 1, max(years) + 2)
    for state in states:
        for y in span:
            df = _load_unit_year(state, y)
            if df.empty or "grossLoad" not in df.columns:
                continue
            g = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
            pos = df.loc[g > 0.0, ["facilityId", "unitId"]].drop_duplicates()
            for f, u in zip(pos["facilityId"].astype(int), pos["unitId"].astype(str)):
                f = campd.CAMPD_UNIT_PLANT_REMAP.get((f, u), f)
                out.add((int(f), u.strip(), int(y)))
    return out


def _is_dark_unit_year(
    rows: pd.DataFrame,
    clock_len: int,
    fac_id: int,
    uid: object,
    year: int,
    unit_gross_years: set[tuple[int, str, int]],
    peers_ran: bool,
) -> bool:
    """Return True when ``uid`` was dark for the whole of ``year`` (SOCO-61).

    Every condition is categorical (no threshold, rules 21/24): CAMPD files a
    row for every hour of the year under this unit id; no hour carries
    positive ``opTime``; the SAME facility/unit id reported positive gross in
    ``year - 1`` or ``year + 1``; and at least one peer unit at the facility
    produced this year (a wholly dark PLANT belongs to the plant-grain
    ``eia923_netzero`` hook, not here).
    """
    if not peers_ran or len(rows) < clock_len:
        return False
    op = pd.to_numeric(rows["opTime"], errors="coerce").fillna(0.0)
    if float(op.max()) > 0.0:
        return False
    u = str(uid).strip()
    return (fac_id, u, year - 1) in unit_gross_years or (
        fac_id,
        u,
        year + 1,
    ) in unit_gross_years


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


# CAMPD ``primaryFuelInfo`` tokens that name LIQUID petroleum. The full CAMPD
# fuel vocabulary is closed and small — enumerated from every state-year in
# ``data/raw/campd-unit-level`` — and these three are its only liquid members
# (the rest are gas, coal, wood, process/other gas and petroleum coke).
_CAMPD_LIQUID_FUELS: frozenset[str] = frozenset(
    {"diesel oil", "residual oil", "other oil"}
)


def _is_liquid_only_fuel(primary_fuel: str) -> bool:
    """True when a CAMPD ``primaryFuelInfo`` names LIQUID petroleum and nothing else.

    The CAMPD vocabulary spells liquid petroleum as exactly
    :data:`_CAMPD_LIQUID_FUELS`; a dual-fuel machine carries its gas token in the
    SAME comma-separated string (e.g. ``"Natural Gas, Residual Oil"``), so
    requiring EVERY token to be liquid keeps dual-fuel gas units out of the
    population. Blank / unknown fuel is not liquid (fail-safe: the caller's
    existing routing stands).
    """
    toks = [t.strip().lower() for t in str(primary_fuel).split(",") if t.strip()]
    return bool(toks) and all(t in _CAMPD_LIQUID_FUELS for t in toks)


# The model bins a gas facility can carry. A facility holding TWO OR MORE of
# these is exactly where the ``fac_group`` short-circuit in
# :func:`_resolve_unit_group` loses its own stated premise ("single-group gas
# facilities are byte-identical"): ``group_by_code`` keeps ONE group per plant
# code by LAST-WRITER-WINS over the fleet rows, so at such a facility the group
# is whichever fleet row happened to come last, and the short-circuit then hands
# EVERY unit to that one bin (miso-200).
_GAS_BIN_GROUPS: frozenset[str] = frozenset(
    {"CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP"}
)


def _is_multi_gas_facility(fac_groups: set[str]) -> bool:
    """True when the facility carries two or more distinct model GAS bins."""
    return len(_GAS_BIN_GROUPS & set(fac_groups)) >= 2


def _resolve_unit_group(
    is_coal: bool,
    unit_type: str,
    fac_groups: set[str],
    fac_group: str | None,
    unit_fuel: str = "",
    mixed_gas_routing: bool = False,
    per_unit_crosswalk: bool = False,
    plant_model_groups: dict[str, float] | set[str] | None = None,
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

    THE LIQUID-FUEL COMBUSTION-TURBINE GUARD (neiso-99, rule 14
    ``[R-ACCURATE]``) runs BEFORE the ``fac_group`` short-circuit, because that
    short-circuit was a deliberate pjm-75 conservatism ("single-group gas
    facilities are byte-identical") rather than a physical claim, and at an
    oil-peaker-plus-gas-block facility it is WRONG: it hands the peaker's
    outage to the block. A CAMPD unit whose own ``unitType`` is a combustion
    turbine AND whose own ``primaryFuelInfo`` is LIQUID-ONLY is a separate
    simple-cycle machine, never a member of a sibling gas bin — a combined-cycle
    CT fires pipeline gas into the block's HRSG, and a gas-steam boiler burns its
    fuel in the boiler itself, so neither can be an oil-only CT. It routes to
    ``CT_PEAKER``, which is outside :data:`QUALIFYING_PLANT_GROUPS` and therefore
    drops the row — correct, because these machines carry NO model bin at all
    (they are ``fuel="oil"`` fleet rows with an empty ``plant_group``, or absent
    from the fleet entirely).

    The discriminator is ``primaryFuelInfo`` and not ``unitType`` alone because
    ``unitType`` does NOT separate the two populations: measured across all six
    ISOs' committed extracts (``scripts/probes/neiso99_routing_blast_radius.py``
    → ``results/calibration/_neiso99_routing_blast_radius.json``), 35 CAMPD units
    filed as "Combustion turbine" sit in a non-CT bin, and 27 of them are
    GAS-fired members of a genuine block that must keep inheriting it (ERCOT Sand
    Hill SH1-SH7, Colorado Bend CT-4A/4B, CAISO Glenarm GT3/GT4, MISO Zeeland
    CC1/CC2, NYISO Ravenswood CT0001/0010/0011, Bethpage GT3, …). The 8 that are
    liquid-only are exactly the mis-routed peakers: NEISO 6081 Stony Brook
    004/005 (Diesel Oil, 83 MW each), 568 Bridgeport Harbor BHB4 (Other Oil),
    1588 Mystic MJ-1, 1595 Kendall S6; PJM 593 Edge Moor 10; MISO 2001 New Ulm 7
    and 8056 Waterford 4; NYISO 2516 Northport UGT001.

    THE MULTI-GAS-GROUP GATE (miso-200, ``mixed_gas_routing``, GATED default
    False, rule 14 ``[R-ACCURATE]``). The ``fac_group`` short-circuit above is
    sound only where the facility carries ONE gas bin -- which is precisely what
    its own pjm-75 justification claims ("single-group gas facilities are
    byte-identical"). At a facility carrying TWO OR MORE gas bins the premise is
    false and the short-circuit is a defect, because ``group_by_code`` is
    LAST-WRITER-WINS over the fleet rows: the "facility group" is whichever
    fleet row came last, and every unit is handed to it. Measured at MISO
    (``_miso200_outage_routing_phase0.json``): Ninemile Point 1403 carries model
    bins ``ST_GAS`` 1,465.4 MW and ``CC_REGULAR`` 649.5 MW, the last writer is
    ``CC_REGULAR``, and its two gas-STEAM boilers (units 4 and 5, CAMPD
    ``unitType`` "Tangentially-fired", 1,658.1 MW combined) therefore dump their
    outage windows onto the 649.5 MW CC bin -- a pre-clip removed share peaking
    at 3.556 and exceeding 1.0 for 4,920-6,192 hours a year, so the CC bin is
    clipped to zero availability for most of every year -- while the ST_GAS bin
    that actually contains them receives NO rows at all and reads availability
    identically 1.0. Both halves are wrong, in opposite directions, at once.
    When ``mixed_gas_routing`` is True the short-circuit is SKIPPED at such a
    facility and the resolver falls through to its OWN existing per-unit
    ``unitType`` routing below -- no new logic, no new data source, no new
    threshold, ZERO free parameters (rule 21 ``[R-DOF]``), and the discriminator
    is CAMPD's own ``unitType``, a static unit attribute that regenerates for
    any forward year (rule 13 ``[R-MEASURED]``). Single-gas-group facilities are
    untouched by construction, so the flag is byte-inert everywhere else.

    THE PER-UNIT CROSSWALK (nyiso-175b, ``per_unit_crosswalk``, GATED default
    False, rule 14 ``[R-ACCURATE]``). ``mixed_gas_routing`` above repairs the
    short-circuit only where :data:`_GAS_BIN_GROUPS` sees two or more gas bins
    -- and that set EXCLUDES both CT classes, so a ``{CT_CHP, ST_CHP}`` cogen
    intersects it at size 1 and the gate never fires. Measured at East River
    (2493): all 93 of its windows, units 1 and 2 included, are written as
    ``ST_CHP``, so the EIA-860 ``GT`` machines' outages derate the 309.5 MW
    STEAM bin (nyiso-174 section 6 item 1) with the gate on or off. Worse, where
    the existing gate DOES fire it can be wrong: at Ravenswood (2500) it routes
    the combined-cycle block's CT0001/CT0010/CT0011 to ``CT_PEAKER`` -- dropping
    them from the overlay entirely -- although those are three of the 27 units
    the liquid-fuel guard's own evidence names as gas-fired members of a genuine
    block that must keep inheriting it.

    Both failures share one cause: the fallback routes on the bare ``unitType``
    STRING, which is a CEMS monitoring-configuration descriptor and not an EIA
    prime-mover code. ``per_unit_crosswalk`` replaces that string test with
    :func:`scripts.lib.campd_measured_classes.corrected_unit_class`, which keeps
    the unit's prime-mover FAMILY and lets the unit's own plant's model roster
    pick the class inside it -- so East River's turbines reach ``CT_CHP`` and
    Ravenswood's block CTs stay on ``CC_REGULAR``. Requires
    ``plant_model_groups``; without it the flag is inert by construction. ZERO
    free parameters, and the same crosswalk the tranche deriver's
    ``--per-unit-attribution`` uses, so the two repairs cannot disagree about
    which bin a machine belongs to.

    Module-level (not nested in :func:`main`) so the declared-event-window
    sibling deriver (``scripts/data/derive_campd_maxgen_outages.py``) reuses the
    SAME routing verbatim -- including this gate, which is why it lives here
    rather than in either deriver's own body.
    """
    if is_coal:
        return "COAL"
    if "combustion turbine" in str(unit_type).strip().lower() and _is_liquid_only_fuel(
        unit_fuel
    ):
        # Excluded downstream: peakers carry no overlay. See the guard's
        # rationale in this function's docstring.
        return "CT_CHP" if "CT_CHP" in fac_groups else "CT_PEAKER"
    if per_unit_crosswalk and plant_model_groups:
        # Seat the unit on a class its OWN plant's model fleet carries, by
        # prime-mover family. Ahead of the fac_group short-circuit because the
        # short-circuit is exactly what mis-routes a mixed cogen's turbines.
        from scripts.lib.campd_measured_classes import (
            campd_unittype_class,
            corrected_unit_class,
        )

        # is_chp comes from the plant's OWN model roster rather than a
        # separate EIA-860 read: the model's bins ARE that classification
        # (plant_taxonomy.classify_plant), so this cannot disagree with the
        # fleet the windows will be applied to.
        groups = set(plant_model_groups)
        seated = corrected_unit_class(
            campd_unittype_class(unit_type, any(g.endswith("_CHP") for g in groups)),
            groups,
        )
        if seated and seated in groups:
            return seated
    if (
        fac_group in QUALIFYING_PLANT_GROUPS
        and fac_group != "COAL"
        and not (mixed_gas_routing and _is_multi_gas_facility(fac_groups))
    ):
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


# ---------------------------------------------------------------------------
# EIA-923 non-CAMPD fallback (default-OFF; separate companion file)
# ---------------------------------------------------------------------------
# A fleet plant with NO CAMPD unit-level record (a non-CEMS unit — below the
# CEMS reporting threshold, or otherwise unmonitored) is invisible to the
# gross-based detector above, so the outage layer is blind to it in every year.
# The --eia923-noncampd-fallback mode infers monthly availability for exactly
# those plants from EIA-923 monthly net generation: a month whose net gen is at
# or below EIA923_FALLBACK_OUTAGE_RATIO x the plant's OWN normal monthly output
# (the median of its positive-output months across every filed EIA-923 year) is
# treated as a full-stop availability window. This is a measured PHYSICAL
# quantity — the plant produced essentially nothing that month — that would
# regenerate for a forward year and respond to changed conditions (rules 13/14):
# a fixed per-plant ratio against the plant's OWN history, never an ISO-crossing
# scalar and never tuned to a price/volume residual. The rows are tagged
# capacity_source="eia923" (distinct from the pre-existing plant-grain
# "eia923_netzero" full-year hook) and written to a SEPARATE companion file the
# loader does NOT read by default — landed as backup only. 0.10 = "ran at <= 10%
# of its own normal month".
EIA923_FALLBACK_OUTAGE_RATIO: float = 0.10

# EIA-923 monthly net-generation columns, January..December in calendar order.
_EIA923_MONTH_COLS: list[str] = [
    "netgen_january_mwh",
    "netgen_february_mwh",
    "netgen_march_mwh",
    "netgen_april_mwh",
    "netgen_may_mwh",
    "netgen_june_mwh",
    "netgen_july_mwh",
    "netgen_august_mwh",
    "netgen_september_mwh",
    "netgen_october_mwh",
    "netgen_november_mwh",
    "netgen_december_mwh",
]


def campd_plant_codes(states: tuple[str, ...], years: list[int]) -> set[int]:
    """Return the plant (facility) codes present in the CAMPD unit-level extracts.

    Scans only the ``facilityId`` column of each state-year extract for the ISO's
    states over ``years`` — the CEMS fleet the standard detector already covers.
    A fleet plant absent from this set has no CAMPD series (non-CEMS) and is a
    candidate for the EIA-923 fallback.
    """
    codes: set[int] = set()
    for state in states:
        for year in years:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            fid = pd.to_numeric(
                pd.read_parquet(path, columns=["facilityId"])["facilityId"],
                errors="coerce",
            ).dropna()
            codes.update(int(c) for c in fid.unique())
    return codes


def _eia923_month_windows(
    monthly: dict[int, float], reference: float, year: int, ratio: float
) -> list[tuple[pd.Timestamp, pd.Timestamp, float]]:
    """Merge a plant-year's contiguous near-zero months into full-stop windows.

    ``monthly`` maps month number (1-12) -> net gen MWh for months that were
    FILED (a NaN/absent month is not a signal and is never treated as zero). A
    month is 'out' when its net gen <= ``ratio`` x ``reference``. Contiguous
    out-months merge into one window; each is clipped to the calendar year (no
    Dec->Jan carry), matching the CAMPD detector convention. Returns
    ``[(start_ts, end_ts, duration_days), ...]``.
    """
    out_months = sorted(m for m, v in monthly.items() if v <= ratio * reference)
    runs: list[list[int]] = []
    for m in out_months:
        if runs and m == runs[-1][-1] + 1:
            runs[-1].append(m)
        else:
            runs.append([m])
    result: list[tuple[pd.Timestamp, pd.Timestamp, float]] = []
    for run in runs:
        start = pd.Timestamp(year=year, month=run[0], day=1)
        end = pd.Timestamp(year=year, month=run[-1], day=1) + pd.offsets.MonthEnd(0)
        duration = float((end - start).days + 1)
        result.append((start, end, duration))
    return result


def derive_eia923_noncampd_fallback(
    iso: str,
    years: list[int],
    group_by_code: dict[int, str],
    npl_by_plant: dict[int, float],
    campd_codes: set[int],
    out_path: str,
    ratio: float,
) -> None:
    """Write the EIA-923 monthly-availability fallback for non-CAMPD fleet plants.

    Only plants in a :data:`QUALIFYING_PLANT_GROUPS` bin (peakers excluded,
    matching the overlay) that are ABSENT from ``campd_codes`` are considered —
    the overlay routes derates by ``plant_group``, so a non-qualifying group
    would be ignored anyway. One row per (plant, contiguous outage-month run) in
    the standard 13-column schema, tagged ``capacity_source="eia923"``.
    """
    e923 = pd.read_parquet(
        PROCESSED_DIR / "eia923_monthly_generation.parquet",
        columns=["plant_id", "plant_name", "year"] + _EIA923_MONTH_COLS,
    )
    years_in_923 = sorted(int(y) for y in e923["year"].unique())
    # plant -> year -> {month: summed net gen over the plant's prime-mover rows}
    by_plant: dict[int, dict[int, dict[int, float]]] = {}
    name_by_plant: dict[int, str] = {}
    for row in e923.itertuples(index=False):
        code = int(row.plant_id)
        name_by_plant.setdefault(code, str(row.plant_name))
        months = by_plant.setdefault(code, {}).setdefault(int(row.year), {})
        for i, col in enumerate(_EIA923_MONTH_COLS, start=1):
            v = getattr(row, col)
            if pd.notna(v):
                months[i] = months.get(i, 0.0) + float(v)

    # Candidate fleet plants: qualifying group, non-peaker, NOT in CAMPD.
    candidates = sorted(
        code
        for code, group in group_by_code.items()
        if group in QUALIFYING_PLANT_GROUPS
        and int(code) not in ST_GAS_PEAKER_PLANTS
        and int(code) not in campd_codes
    )
    rows: list[dict] = []
    summary: list[tuple] = []
    n_no_npl = 0
    n_no_923 = 0  # plants with no 923 history at all (no reference derivable)
    # Per requested year: plants that had no 923 filing that year (no window ->
    # assumed available). Logged, never silently dropped (rule: no silent caps).
    no_filing_by_year: dict[int, int] = {y: 0 for y in years}
    for code in candidates:
        npl = npl_by_plant.get(int(code), 0.0)
        if npl <= 0.0:
            n_no_npl += 1
            continue
        plant_years = by_plant.get(int(code))
        if not plant_years:
            n_no_923 += 1
            continue
        # The plant's OWN normal monthly output: median of its positive-output
        # months across every filed year. No positive month -> no reference.
        pos = [v for yr in plant_years.values() for v in yr.values() if v > 0.0]
        if not pos:
            n_no_923 += 1
            continue
        reference = float(np.median(pos))
        group = group_by_code[int(code)]
        name = name_by_plant.get(int(code), "")
        out_days = 0.0
        n_win = 0
        for year in years:
            if year not in years_in_923:
                continue
            months = plant_years.get(year)
            if not months:
                # No 923 filing for this plant-year (e.g. the 2025/2026 filing
                # lag): no availability signal -> assume available, count it.
                no_filing_by_year[year] += 1
                continue
            for start, end, duration in _eia923_month_windows(
                months, reference, year, ratio
            ):
                rows.append(
                    {
                        "facility_name": name,
                        "facility_id": int(code),
                        "unit_id": "E923",
                        "unit_capacity_mw": round(npl, 1),
                        "plant_capacity_mw": round(npl, 1),
                        "unit_pct_of_plant": 100.0,
                        "plant_group": group,
                        "capacity_source": "eia923",
                        "outage_start": start.strftime("%Y-%m-%d"),
                        "outage_end": end.strftime("%Y-%m-%d"),
                        "duration_days": round(duration, 1),
                        "peer_units_online": 0,
                        "total_units_at_plant": 1,
                    }
                )
                out_days += duration
                n_win += 1
        if n_win:
            summary.append((int(code), name, group, n_win, out_days))

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
    out = pd.DataFrame(rows, columns=cols).sort_values(
        ["facility_id", "unit_id", "outage_start"]
    )
    out.to_csv(out_path, index=False)

    print(
        f"\nEIA-923 non-CAMPD fallback [{iso}] ratio={ratio}: "
        f"wrote {len(out)} windows for {len(summary)} plants to {out_path}"
    )
    print(
        f"  candidates (qualifying non-CAMPD fleet plants): {len(candidates)}; "
        f"skipped {n_no_npl} (no EIA-860 nameplate), {n_no_923} (no EIA-923 "
        f"history / no positive month)"
    )
    for year in years:
        print(
            f"  {year}: {no_filing_by_year.get(year, 0)} candidate plants had NO "
            f"EIA-923 filing -> no window (assumed available)"
        )
    print(f"{'code':>6} {'plant':<28}{'group':<11}{'#win':>5}{'out d':>8}")
    for code, nm, g, n, td in sorted(summary):
        print(f"{code:>6} {str(nm)[:27]:<28}{g:<11}{n:>5}{td:>8.0f}")


# ---------------------------------------------------------------------------
# Optional hour-grain carriage (caiso-183)
# ---------------------------------------------------------------------------
# The detector works in HOURS (`start = clock[s]`, `last = clock[e - 1]`) but the
# extract has always been written in DAYS, and the loader re-expands
# `outage_start` 00:00 -> `outage_end` 23:00 — asserting up to 23 h at each edge
# that the detector never detected, exactly where the event-based contract
# guarantees the neighbouring hour was RUNNING. caiso-181 confirmed that seam at
# 100 % of unit-grain CEMS contradictions (max distance from a window boundary
# 22 h < 24, every year) and filed the repair as its own charter:
# results/calibration/FINDING-caiso181-envelope-depth-2026-08-07.md section 5
# item 1, pre-registered here as PRECHECK-caiso183-hedge-grain-2026-08-08.md.
#
# These two columns carry the DETECTED hour-of-day through the schema so the
# loader can stop widening the window. They are OPTIONAL and emitted only under
# --hour-grain, because this writer and market_sim.data.outages serve ALL SIX
# ISOs: the flag-absent extract stays byte-identical, and an ISO adopts the finer
# grain by re-deriving its own extract and nothing else (rule 25 [R-ISO-SCOPE]).
# Zero DOF: no parameter, no threshold, no detector constant is involved.
HOUR_GRAIN_COLUMNS: tuple[str, str] = ("outage_start_hour", "outage_end_hour")

#: capacity_source of the EIA-923 net-zero fallback rows, whose window is a whole
#: calendar year by construction and so carries a nominal 365.0 duration_days
#: even in a leap year. Excluded from the duration cross-check below.
_NETZERO_SOURCE: str = "eia923_netzero"


def assert_hour_grain_consistent(frame: pd.DataFrame) -> None:
    """Assert the emitted hour columns agree with the day columns they accompany.

    Stop-the-line by design (the ercot-174 BE-3 discipline): a grain change may
    express a window more precisely, but it may never move one. Three checks,
    all on the frame exactly as it will be written:

    1. every emitted hour is an integer in ``[0, 23]``;
    2. the reconstructed window ``[start + h0, end + h1 + 1h)`` is non-empty and
       a **subset** of the incumbent day-granular window ``[start, end + 1 day)``
       — so the repair can only ever REMOVE asserted unavailability, never
       invent it;
    3. the reconstructed window's length in hours reproduces the detector's own
       ``duration_days`` (which is ``round((e - s) / 24, 1)``), which ties the
       hours back to the detection pass rather than to a re-derivation.

    Args:
        frame: The extract as built, carrying :data:`HOUR_GRAIN_COLUMNS`.

    Raises:
        AssertionError: If any row's hour grain is inconsistent with its days.
    """
    if frame.empty:
        return
    h0, h1 = (frame[c] for c in HOUR_GRAIN_COLUMNS)
    bad_range = ~(h0.between(0, 23) & h1.between(0, 23))
    assert not bad_range.any(), (
        f"hour-grain: {int(bad_range.sum())} row(s) carry an hour outside [0, 23]"
    )

    start = pd.to_datetime(frame["outage_start"]) + pd.to_timedelta(
        h0.astype(int), unit="h"
    )
    stop = pd.to_datetime(frame["outage_end"]) + pd.to_timedelta(
        h1.astype(int) + 1, unit="h"
    )
    day_stop = pd.to_datetime(frame["outage_end"]) + pd.Timedelta(days=1)
    empty = stop <= start
    assert not empty.any(), (
        f"hour-grain: {int(empty.sum())} row(s) reconstruct to an empty window"
    )
    outside = (start < pd.to_datetime(frame["outage_start"])) | (stop > day_stop)
    assert not outside.any(), (
        f"hour-grain: {int(outside.sum())} row(s) reconstruct OUTSIDE the "
        f"day-granular window — the repair must only ever narrow it"
    )

    detected = frame["capacity_source"].astype(str) != _NETZERO_SOURCE
    hours = (stop - start).dt.total_seconds() / 3600.0
    mismatch = detected & (
        (hours / 24.0).round(1) != frame["duration_days"].astype(float)
    )
    assert not mismatch.any(), (
        f"hour-grain: {int(mismatch.sum())} row(s) whose reconstructed window "
        f"length disagrees with the detector's own duration_days"
    )


def _write_outage_sidecar(
    out_path: Path, args: argparse.Namespace, frame: pd.DataFrame
) -> Path:
    """Write ``<artifact>.meta.json`` recording how the extract was derived.

    nyiso-176: the incumbent NYISO extract could not be reproduced at HEAD and
    nothing on disk said what invocation had produced it — its tranche sibling's
    sidecar carries ``derive_invocation: null`` and states in terms that it
    "makes no claim about what HEAD would emit". The whole 4,423-vs-2,632-window
    comparison that blocked a session turned on a ``--years`` span nobody had
    recorded (the committed extract spans 2018-2026; this deriver's default is
    2023-2025), and the detector settings that carry the largest remaining
    channel — the full-stop duration override — were equally unrecorded.

    So every emit now states its own provenance: the year span, the detector
    thresholds that change which windows survive, the row count and the observed
    year histogram. A successor comparing two extracts can read the two sidecars
    and see immediately whether it is looking at drift or at a different
    invocation. Descriptive only — no loader reads it, and it never gates.
    """
    try:
        years = (
            sorted({int(y) for y in pd.to_datetime(frame["outage_start"]).dt.year})
            if len(frame)
            else []
        )
        by_year = (
            {
                str(int(k)): int(v)
                for k, v in pd.to_datetime(frame["outage_start"])
                .dt.year.value_counts()
                .sort_index()
                .items()
            }
            if len(frame)
            else {}
        )
    except Exception:  # pragma: no cover - an empty/odd frame never blocks the emit
        years, by_year = [], {}
    side = out_path.with_suffix(".meta.json")
    side.write_text(
        json.dumps(
            {
                "artifact": out_path.name,
                "artifact_rows": int(len(frame)),
                "deriver": "scripts/data/derive_campd_unit_outages.py",
                "sidecar_schema_version": 1,
                "derive_invocation": {
                    "iso": str(args.iso).upper(),
                    "years": [int(y) for y in args.years],
                    "min_outage_days": float(args.min_outage_days),
                    "per_unit_crosswalk": bool(
                        getattr(args, "per_unit_crosswalk", False)
                    ),
                    "mixed_gas_routing": bool(
                        getattr(args, "mixed_gas_routing", False)
                    ),
                    "short_windows": bool(getattr(args, "short_windows", False)),
                    "partial_windows": bool(getattr(args, "partial_windows", False)),
                    "merit_order_guard": bool(
                        getattr(args, "merit_order_guard", False)
                    ),
                    # SOCO-61: recorded only when set, so every pre-existing
                    # sidecar re-derives byte-identical.
                    **(
                        {"dark_unit_years": True}
                        if getattr(args, "dark_unit_years", False)
                        else {}
                    ),
                    # R-ERCOT-5: recorded only when set, same discipline, so a
                    # --hour-grain companion's sidecar says so and every
                    # pre-existing sidecar re-derives byte-identical.
                    **(
                        {"hour_grain": True}
                        if getattr(args, "hour_grain", False)
                        else {}
                    ),
                    "no_inmerit_filter": bool(
                        getattr(args, "no_inmerit_filter", False)
                    ),
                    "min_inmerit_hours": int(args.min_inmerit_hours),
                    "high_load_pctl": float(args.high_load_pctl),
                    "fullstop_override_days": int(args.fullstop_override_days),
                    "fullstop_override_cf": float(args.fullstop_override_cf),
                },
                "observed_years": years,
                "windows_by_start_year": by_year,
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(f"wrote provenance sidecar {side}")
    return side


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
        "--short-window-groups",
        default="coal",
        choices=("coal", "gas"),
        help="Which model plant groups --short-windows emits. 'coal' (default) "
        "is the frozen baseload-coal scope and is byte-identical. 'gas' emits "
        "the DISJOINT gas-side companion "
        "(campd-unit-outages-shortgas[-{ISO}].csv, consumed under "
        "ScenarioConfig.unit_outage_short_windows_gas): the event-based "
        "dead-span detector (never the coal sustained-gap rule), no "
        "SHORT_BASELOAD_CF baseload guard (a coal guard a cycling CC cannot "
        "pass), and the MERIT-ORDER guard as its economic-idling separator "
        "instead — so --merit-order-guard is REQUIRED with it. Ignored by "
        "--partial-windows, which stays coal-only.",
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
        "--mixed-gas-routing",
        action="store_true",
        help=(
            "miso-200 (rule 14 [R-ACCURATE]): at a facility carrying TWO OR "
            "MORE model gas bins, skip _resolve_unit_group's fac_group "
            "short-circuit -- whose own premise is that the facility carries "
            "ONE gas group -- and route each unit by its OWN CAMPD unitType. "
            "Writes to the '-unitroute-' companion file so the incumbent "
            "extract is never overwritten and the two can be A/B'd."
        ),
    )
    ap.add_argument(
        "--per-unit-crosswalk",
        action="store_true",
        help=(
            "nyiso-175b (rule 14 [R-ACCURATE]): route each unit by the "
            "prime-mover-family crosswalk (campd_measured_classes."
            "corrected_unit_class) instead of the bare CAMPD unitType string, "
            "so a unit lands on a bin its own plant's model fleet carries. "
            "Repairs the East River case mixed_gas_routing cannot reach "
            "(_GAS_BIN_GROUPS excludes both CT classes) and the Ravenswood "
            "case it gets wrong. Writes the '-perunit-' companion."
        ),
    )
    ap.add_argument(
        "--dark-unit-years",
        action="store_true",
        help=(
            "SOCO-61 (rule 14 [R-ACCURATE]), DEFAULT-OFF, requires "
            "--per-unit-crosswalk: emit ONE full-year window for a unit that is "
            "DARK for a whole calendar year -- CAMPD files a row for EVERY hour "
            "of the year under that unit id with opTime 0 and no gross -- while "
            "the SAME facility/unit id reported gross output in an adjacent "
            "year and at least one peer unit at the facility ran that year. "
            "Without this the unit falls through both layers: the per-unit "
            "detector skips a never-producing unit (it cannot tell a real "
            "full-year outage from a unit monitored under another id -- the "
            "adjacent-year same-id record is what settles that), and the "
            "eia923_netzero hook works at PLANT grain, so a running plant "
            "hides it. Zero free parameters. Writes the '-perunitdark-' "
            "companion, never an overwrite."
        ),
    )
    ap.add_argument(
        "--out",
        default=None,
        help="Output CSV; defaults to data/raw/campd-unit-outages.csv "
        "(ERCOT) or campd-unit-outages-{ISO}.csv.",
    )
    ap.add_argument(
        "--membership-vintage-union",
        action="store_true",
        help="DEFAULT-OFF: union each derived year's own EIA-860 vintage fleet "
        "into the facility membership (non-ERCOT), so partial-plant exits whose "
        "surviving class is a CT still have their retired coal/steam units "
        "scanned. The flag-absent extract is unchanged.",
    )
    ap.add_argument(
        "--hour-grain",
        action="store_true",
        help="DEFAULT-OFF: also emit outage_start_hour / outage_end_hour, the "
        "DETECTED hour-of-day of the window's first and last outage hour. The "
        "detector has always worked in hours while the extract stored days, so "
        "market_sim.data.outages re-expanded every window to 00:00-23:00 and "
        "asserted up to 23 h per edge it never detected — precisely where the "
        "event-based contract guarantees the neighbouring hour was RUNNING "
        "(caiso-181 measured this at 100%% of unit-grain CEMS contradictions, "
        "max 22 h from a boundary). The loader consumes the two columns when "
        "present and falls back to the day-granular reconstruction when absent, "
        "so this is per-ISO adoptable and the flag-absent extract is "
        "BYTE-IDENTICAL. Zero DOF: no parameter, threshold or detector constant "
        "is involved. See PRECHECK-caiso183-hedge-grain-2026-08-08.md.",
    )
    ap.add_argument(
        "--eia923-noncampd-fallback",
        action="store_true",
        help="DEFAULT-OFF alternate mode: instead of the CAMPD detector, infer "
        "monthly availability windows from EIA-923 monthly net generation for "
        "fleet plants that have NO CAMPD unit-level record (non-CEMS units the "
        "gross-based detector is blind to). Writes a SEPARATE companion file "
        "campd-unit-outages-e923-{ISO}.csv (all ISOs suffixed) tagged "
        'capacity_source="eia923" that the outage loader does NOT read by '
        "default — landed as backup only. The standard extract is byte-unchanged "
        "when this flag is absent.",
    )
    ap.add_argument(
        "--merit-order-guard",
        action="store_true",
        help="DEFAULT-OFF: apply the merit-order guard, which reclassifies a "
        "detected window as ECONOMIC LAYUP (not a mechanical outage) when the "
        "unit's measured SRMC — CAMPD heat rate x delivered fuel price — sat "
        "above the revealed marginal cost of the capacity that WAS running for "
        "at least --merit-oom-frac of the window. Layup windows leave the "
        "availability envelope (an economically idle unit is AVAILABLE; the LP "
        "declines it on its own economics) and are written to the labelled "
        "companion campd-unit-outages-layup[-{ISO}].csv, which no loader reads "
        "by default. Fixes the detector booking 23-46%% of every ISO's CC "
        "capacity-year as outage against a real EFOR+planned norm of ~10-15%% "
        "(docs/handoffs/campd-economic-layup-fix-charter-2026-07.md). The "
        "standard extract is byte-identical when this flag is absent.",
    )
    ap.add_argument(
        "--merit-oom-frac",
        type=float,
        default=MERIT_OOM_FRAC,
        help="Merit-order guard: share of a window's hours that must be out of "
        f"merit for it to be reclassified as layup (default {MERIT_OOM_FRAC}).",
    )
    ap.add_argument(
        "--merit-rcc-pctl",
        type=float,
        default=MERIT_RCC_PCTL,
        help="Merit-order guard: capacity-weighted quantile of running-unit "
        "SRMC that stands for the revealed clearing cost (default "
        f"{MERIT_RCC_PCTL}).",
    )
    ap.add_argument(
        "--eia923-outage-ratio",
        type=float,
        default=EIA923_FALLBACK_OUTAGE_RATIO,
        help="EIA-923 fallback: a month at or below this fraction of the plant's "
        "own normal monthly output (median of its positive months across all "
        "filed years) is a full-stop window (default "
        f"{EIA923_FALLBACK_OUTAGE_RATIO}).",
    )
    ap.add_argument(
        "--emit-screened-set",
        action="store_true",
        help="DEFAULT-OFF, --short-windows coal scope only (miso-273): also "
        "write the companion campd-unit-outages-short-screened[-{ISO}].csv, one "
        "row per coal unit-year that PASSED the SHORT_BASELOAD_CF when-operable "
        "guard, events or not. The window extract is byte-identical with or "
        "without it. Consumed under ScenarioConfig."
        "wefor_residual_short_screened_coal.",
    )
    args = ap.parse_args()
    if args.short_windows and args.partial_windows:
        raise SystemExit("--short-windows and --partial-windows are mutually exclusive")
    if args.dark_unit_years and (
        not args.per_unit_crosswalk or args.short_windows or args.partial_windows
    ):
        raise SystemExit(
            "--dark-unit-years requires --per-unit-crosswalk and the standard "
            "(>= 5-day) extract (not --short-windows / --partial-windows)"
        )
    short_gas = args.short_windows and args.short_window_groups == "gas"
    if args.short_window_groups == "gas" and not args.short_windows:
        raise SystemExit("--short-window-groups gas requires --short-windows")
    if short_gas and not args.merit_order_guard:
        # The gas scope has no baseload guard, so the merit-order test IS its
        # economic-idling separator. Emitting it unguarded would ship a strictly
        # less-identified extract than its own coal sibling.
        raise SystemExit(
            "--short-window-groups gas requires --merit-order-guard "
            "(the gas scope's economic-idling separator)"
        )
    if args.emit_screened_set and (not args.short_windows or short_gas):
        raise SystemExit(
            "--emit-screened-set requires --short-windows with the coal scope "
            "(the screened set is the baseload guard's admission list)"
        )
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
        elif short_gas:
            # A SEPARATE companion path: the coal short extract is never
            # overwritten, so the coal-only off path stays byte-identical and
            # the gas family is a single, independently-gated object.
            fname = (
                "campd-unit-outages-shortgas.csv"
                if iso == "ERCOT"
                else f"campd-unit-outages-shortgas-{iso}.csv"
            )
        elif args.short_windows:
            fname = (
                "campd-unit-outages-short.csv"
                if iso == "ERCOT"
                else f"campd-unit-outages-short-{iso}.csv"
            )
        elif getattr(args, "per_unit_crosswalk", False):
            # SEPARATE companion (nyiso-175b), same discipline as the
            # -unitroute- path: never an overwrite, so the control leg keeps
            # reading byte-identical input and the delta is a single object.
            fname = (
                # SOCO-61: the dark-unit-year windows ride their own
                # companion so the '-perunit-' control stays byte-identical.
                f"campd-unit-outages-perunitdark-{iso}.csv"
                if args.dark_unit_years
                else f"campd-unit-outages-perunit-{iso}.csv"
            )
        elif args.mixed_gas_routing:
            # A SEPARATE companion path (miso-200): the incumbent extract is
            # never overwritten, so the two routings can be A/B'd as a single
            # delta and the control leg keeps reading byte-identical input.
            fname = f"campd-unit-outages-unitroute-{iso}.csv"
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
            int(c): artifact_class(str(g))
            for c, g in zip(bins["Plant_Code"], bins["Plant_Group"])
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
        from market_sim.config.plant_taxonomy import artifact_class

        for g in fleet:
            if int(g.plant_code) > 0 and g.plant_group:
                # COAL-SUB (2026-09-25): the fleet carries coal SUBCLASSES
                # (COAL_BIT / COAL_PRB / ...), but this map feeds the artifact
                # vocabulary (QUALIFYING_PLANT_GROUPS, the extract's
                # plant_group), where coal is the family token. Without the
                # translation every coal-only facility fails the qualifying
                # test and its windows vanish (miso-273: short-coal MISO 2023
                # regenerated 6 of 109 committed rows).
                pgroup = artifact_class(g.plant_group)
                group_by_code[int(g.plant_code)] = pgroup
                name_by_code[int(g.plant_code)] = g.name
                groups_by_code.setdefault(int(g.plant_code), set()).add(pgroup)
                if g.plant_group in ("ST_GAS", "ST_CHP"):
                    steam_np_by_code[int(g.plant_code)] = steam_np_by_code.get(
                        int(g.plant_code), 0.0
                    ) + float(g.pmax_mw)
        if getattr(args, "membership_vintage_union", False):
            _union_vintage_membership(
                iso, iso_config, args.years, group_by_code, groups_by_code, name_by_code
            )
    # Facility names for units re-keyed by the CEMS->EIA split-plant remap
    # (their CAMPD facilityName is the legacy plant's).
    remap_names = {
        c: name_by_code[c]
        for c in set(campd.CAMPD_UNIT_PLANT_REMAP.values())
        if c in name_by_code
    }

    exact, by_digits = build_capacity_index(Path(args.eia860))
    npl_by_plant = plant_nameplate_index(Path(args.eia860))

    # EIA-923 non-CAMPD fallback: a SEPARATE default-off layer written to its own
    # companion file (never merged into the default-read extract), so it returns
    # before the CAMPD detector runs and the standard output path is untouched.
    if args.eia923_noncampd_fallback:
        states = campd.states_for_iso(iso)
        campd_codes = campd_plant_codes(states, args.years)
        e923_out = str(RAW_DATA_DIR / f"campd-unit-outages-e923-{iso}.csv")
        derive_eia923_noncampd_fallback(
            iso=iso,
            years=args.years,
            group_by_code=group_by_code,
            npl_by_plant=npl_by_plant,
            campd_codes=campd_codes,
            out_path=e923_out,
            ratio=args.eia923_outage_ratio,
        )
        return

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
    # The merit-order panel's IDENTIFICATION scope, pinned independently of the
    # detection scope above (CLAUDE.md rule 23 ``[R-FROZEN-DERIVE]``): widening
    # `states` for coverage must never re-identify the layup classifier for the
    # plants already covered. Falls back to `states` for any ISO with no pin, so
    # this is a no-op everywhere but CAISO (rule 25 ``[R-ISO-SCOPE]``). See
    # `campd.ISO_MERIT_PANEL_STATES` and FINDING-caiso198 §3 for the measurement
    # that identified the coupling.
    merit_panel_states = campd.merit_panel_states_for_iso(iso)
    # The ISO's own OUT-OF-STATE fleet members join the panel (the caiso-199
    # §3b narrowing; PRECHECK-caiso200 §2): a fleet plant filing CEMS outside
    # the pinned panel states must be a member of the panel its own spans are
    # scored against. Membership is derived from the fleet registry, never
    # enumerated — {NV: (55077,)} for CAISO today — and admits nothing that
    # is not the ISO's own fleet.
    merit_member_facilities = (
        _merit_member_facilities(states, merit_panel_states, args.years, group_by_code)
        if campd.merit_panel_admits_fleet_members(iso)
        else {}
    )
    rows: list[dict] = []
    # Windows the merit-order guard reclassifies as economic layup. Always
    # defined so the row sink below is unconditional; stays empty (and no
    # companion file is written) unless --merit-order-guard is passed.
    layup_rows: list[dict] = []
    # --emit-screened-set (miso-273): every coal unit-year that passed the
    # short-window baseload guard. Stays empty unless the flag is passed.
    screened_rows: list[dict] = []
    # year -> MeritOrderPanel. Built once per year from the measured CAMPD
    # operation of the WHOLE ISO fleet (not just the units with windows), so the
    # revealed marginal cost is set by the capacity that was actually running.
    merit_panels: dict[int, object] = {}
    summary: list[tuple] = []
    # (year, clock length) -> in-merit (system-tight) hour mask.
    inmerit_cache: dict[tuple[int, int], np.ndarray | None] = {}
    # (facility, year) -> any non-null CAMPD grossLoad seen; feeds the
    # net-zero-to-grid rule below (mirrors the benchmark's CAMPD backfill).
    campd_gross_seen: set[tuple[int, int]] = set()
    # SOCO-61 --dark-unit-years: (facility, unit id, year) that reported ANY
    # positive gross, over the run years AND one year either side, so a unit
    # dark all of year Y can be matched to its own same-id output in Y-1/Y+1.
    unit_gross_years: set[tuple[int, str, int]] = (
        _unit_gross_years(states, args.years) if args.dark_unit_years else set()
    )
    for state in states:
        for year in args.years:
            df = _load_unit_year(state, year)
            if df.empty:
                continue
            # Merit-order panel for the ISO-year, built once and shared across
            # every state pass. Indexed from Jan 1 on the FULL calendar year, so
            # it stays aligned under a state's clipped in-progress-year clock
            # (hour i means the same wall-clock hour in both).
            merit_panel = None
            if args.merit_order_guard and not args.partial_windows:
                if year not in merit_panels:
                    n_full = len(
                        pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
                    )
                    merit_panels[year] = build_merit_order_panel(
                        iso,
                        year,
                        n_full,
                        merit_panel_states,
                        args.merit_rcc_pctl,
                        member_facilities=merit_member_facilities or None,
                    )
                    member_note = "".join(
                        f" +members {st}:{','.join(str(f) for f in fs)}"
                        for st, fs in sorted(merit_member_facilities.items())
                    )
                    print(
                        f"  merit-order panel {iso} {year} "
                        f"[scope {'+'.join(merit_panel_states)}{member_note}]: "
                        + (
                            "UNIDENTIFIED (guard inert this year)"
                            if merit_panels[year] is None
                            else f"{len(merit_panels[year].srmc)} priced units"
                        )
                    )
                merit_panel = merit_panels[year]
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
                # The unit's OWN CEMS-reported primary fuel, for the liquid-fuel
                # combustion-turbine guard in :func:`_resolve_unit_group`.
                unit_fuel = {
                    uid: str(u["primaryFuelInfo"].iloc[0])
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
                    # SOCO-61 --dark-unit-years settles exactly that doubt for
                    # one case: the unit's OWN id files every hour dark this
                    # year and produced in an adjacent year, with an EIA-860
                    # capacity basis (derate_cap) and a peer that ran.
                    dark_year = bool(
                        args.dark_unit_years
                        and peaks[uid] <= 0.0
                        and derate_cap > 0.0
                        and _is_dark_unit_year(
                            fac[fac["unitId"].astype(str) == str(uid)],
                            len(pd.date_range(f"{year}-01-01", horizon_end, freq="h")),
                            int(fac_id),
                            uid,
                            year,
                            unit_gross_years,
                            any(o != uid for o in ran),
                        )
                    )
                    if not dark_year and (peaks[uid] <= 0.0 or derate_cap <= 0.0):
                        continue
                    if dark_year:
                        cap_src = "campd_dark_unit_year"
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
                            unit_fuel.get(uid, ""),
                            mixed_gas_routing=bool(args.mixed_gas_routing),
                            per_unit_crosswalk=bool(
                                getattr(args, "per_unit_crosswalk", False)
                            ),
                            plant_model_groups=fac_groups,
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
                    if short_gas:
                        # Gas scope: the disjoint complement of the coal one.
                        # No SHORT_BASELOAD_CF (see SHORT_WINDOW_GAS_GROUPS) —
                        # the merit-order guard below is this scope's
                        # economic-idling separator, and it is mandatory.
                        if unit_is_coal[uid] or ugroup not in SHORT_WINDOW_GAS_GROUPS:
                            continue
                    elif args.short_windows or args.partial_windows:
                        if not unit_is_coal[uid]:
                            continue
                        oper_cf = _when_operable_cf(
                            gross, detect_cap, standard_windows, int(fac_id), uid, year
                        )
                        if oper_cf < SHORT_BASELOAD_CF:
                            continue
                        if args.short_windows and args.emit_screened_set:
                            # miso-273: the unit-year PASSED the baseload
                            # guard, so the short family measures its < 5-day
                            # full stops whether or not it had any. Recorded
                            # HERE, before detection, because a screened unit
                            # with zero events is otherwise indistinguishable
                            # from one the guard never admitted.
                            screened_rows.append(
                                {
                                    "facility_name": fac_name,
                                    "facility_id": int(fac_id),
                                    "unit_id": uid,
                                    "year": int(year),
                                    "unit_capacity_mw": round(derate_cap, 1),
                                    "plant_group": ugroup,
                                    "capacity_source": cap_src,
                                    "when_operable_cf": round(oper_cf, 4),
                                }
                            )
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
                    if dark_year:
                        # One window over the whole published year: the unit
                        # never operated, so there is nothing to detect.
                        windows = [
                            (
                                0,
                                len(
                                    pd.date_range(
                                        f"{year}-01-01", horizon_end, freq="h"
                                    )
                                ),
                            )
                        ]
                    elif args.partial_windows:
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
                    # Merit-order guard (charter campd-economic-layup-fix,
                    # section 3a): split off the spans the unit spent OUT OF
                    # MERIT — measured SRMC (CAMPD heat rate x delivered fuel
                    # price) above the revealed marginal cost of the capacity
                    # that WAS running, for >= MERIT_OOM_FRAC of the span. Those
                    # are economic LAYUP, not mechanical unavailability: the unit
                    # is available and the LP must decline it on its own
                    # economics, so they leave the availability envelope and are
                    # written to the labelled companion file instead. No-op (and
                    # byte-inert) without --merit-order-guard, and fail-safe for
                    # any unit the panel could not identify.
                    layup_windows: list[tuple[int, int]] = []
                    if merit_panel is not None:
                        windows, layup_windows = filter_merit_order_layup(
                            windows, merit_panel, int(fac_id), uid, args.merit_oom_frac
                        )
                        if not windows and not layup_windows:
                            continue
                    out_days = 0.0
                    for s, e, sink in [(s, e, rows) for s, e in windows] + [
                        (s, e, layup_rows) for s, e in layup_windows
                    ]:
                        start = clock[s]
                        last = clock[e - 1]
                        duration_days = round((e - s) / 24.0, 1)
                        if sink is rows:
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
                            # caiso-183: the DETECTED hour-of-day, taken from the
                            # SAME `start` / `last` the day strings above are
                            # formatted from, so the two grains can never
                            # disagree. Always computed; emitted only when
                            # HOUR_GRAIN_COLUMNS is in `cols` (--hour-grain),
                            # which is what keeps the default extract byte-inert
                            # for all six ISOs.
                            "outage_start_hour": int(start.hour),
                            "outage_end_hour": int(last.hour),
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
                        if sink is layup_rows:
                            # The measured evidence for the reclassification, so
                            # the companion file is auditable on its own.
                            row["out_of_merit_share"] = round(
                                merit_panel.out_of_merit_share((int(fac_id), uid), s, e)
                                or 0.0,
                                3,
                            )
                        sink.append(row)
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
                        # caiso-183: an EIA-923 net-zero fallback window spans a
                        # whole calendar year by construction, so its hour grain
                        # IS its day grain (00:00 through 23:00). Written
                        # explicitly rather than left null so the column is fully
                        # populated wherever it is emitted.
                        "outage_start_hour": 0,
                        "outage_end_hour": 23,
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
    base_cols = list(cols)
    if args.hour_grain:
        # caiso-183: appended AFTER the incumbent header, so every existing
        # column and value keeps its position. Without the flag these keys are
        # simply not selected out of `rows`, which is what makes the default
        # extract byte-identical for all six ISOs.
        cols += list(HOUR_GRAIN_COLUMNS)
    if args.partial_windows:
        # Unit-grain partial file carries the measured availability fraction the
        # unit ran at during each plateau (the extra column vs the full-stop
        # extracts); the consumer removes (1 - derate_factor) x unit_capacity.
        cols.append("derate_factor")
        base_cols.append("derate_factor")
    sort_by = ["facility_id", "unit_id", "outage_start"]
    out = pd.DataFrame(rows, columns=cols).sort_values(sort_by)
    if args.hour_grain:
        # Stop-the-line (ercot-174 BE-3 discipline): the hour columns must agree
        # with the day columns they accompany, and the base-column projection
        # must be exactly the frame this run would write WITHOUT the flag — the
        # in-process statement that the two columns are additive and coupled to
        # nothing. A failure here means the grain change reached detection.
        assert_hour_grain_consistent(out)
        base_frame = pd.DataFrame(rows, columns=base_cols).sort_values(sort_by)
        assert out[base_cols].equals(base_frame), (
            "hour-grain: the base-column projection is not identical to the "
            "flag-absent frame — the grain change moved a detected window"
        )
    out.to_csv(args.out, index=False)
    _write_outage_sidecar(Path(str(args.out)), args, out)

    if args.emit_screened_set:
        out_p = Path(str(args.out))
        scr_name = (
            out_p.name.replace(
                "campd-unit-outages-short", "campd-unit-outages-short-screened", 1
            )
            if "campd-unit-outages-short" in out_p.name
            else f"{out_p.stem}-screened{out_p.suffix}"
        )
        scr_path = out_p.with_name(scr_name)
        if scr_path.resolve() == out_p.resolve():
            raise SystemExit(f"screened-set path collides with --out ({out_p})")
        scr = pd.DataFrame(
            screened_rows,
            columns=[
                "facility_name",
                "facility_id",
                "unit_id",
                "year",
                "unit_capacity_mw",
                "plant_group",
                "capacity_source",
                "when_operable_cf",
            ],
        ).sort_values(["year", "facility_id", "unit_id"])
        scr.to_csv(scr_path, index=False)
        print(f"\nscreened set: {len(scr)} coal unit-years -> {scr_path}")

    if args.merit_order_guard:
        # Labelled companion: the windows the guard reclassified as economic
        # layup, same schema plus the measured out-of-merit share that carried
        # the call. No loader reads it — it is the audit trail and the
        # validation series (charter D2), so the reclassification is never a
        # silent deletion.
        out_p = Path(str(args.out))
        # Canonical name -> campd-unit-outages-layup[-{ISO}].csv; any other
        # --out (a probe path) just gets a "-layup" suffix. Never the same file
        # as the extract: a collision would silently overwrite the deliverable.
        layup_name = (
            out_p.name.replace("campd-unit-outages", "campd-unit-outages-layup", 1)
            if "campd-unit-outages" in out_p.name
            else f"{out_p.stem}-layup{out_p.suffix}"
        )
        layup_path = out_p.with_name(layup_name)
        if layup_path.resolve() == out_p.resolve():
            raise SystemExit(
                f"merit-order guard: layup companion path collides with --out "
                f"({out_p}); refusing to overwrite the extract"
            )
        lay = pd.DataFrame(layup_rows, columns=[*cols, "out_of_merit_share"])
        lay = lay.sort_values(["facility_id", "unit_id", "outage_start"])
        if args.hour_grain:
            # The companion carries the same windows at the same grain, so it
            # answers to the same invariant.
            assert_hour_grain_consistent(lay)
        lay.to_csv(layup_path, index=False)
        print(
            f"\nmerit-order guard: reclassified {len(lay)} windows as economic "
            f"layup -> {layup_path}"
        )

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
