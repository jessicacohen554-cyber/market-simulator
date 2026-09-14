"""EPA CAMPD (CEMS) hourly emissions and gross-generation loader.

The uploaded ``data/raw/{STATE}_{YEAR}.parquet`` files are EPA Clean
Air Markets Program Data hourly extracts, one row per
``(facility, unit-hour)`` with columns:

* ``facilityId`` — the ORISPL / EIA plant code (a string), which joins to
  the EIA-923 ``plant_id`` and the master registry ``plantid``.
* ``grossLoad`` — gross electrical output for the hour, MW (≈ MWh/h).
* ``steamLoad`` — process-steam load, 1000 lb/hr (CHP host steam).
* ``co2Mass`` — CO2 mass, **short tons**.
* ``so2Mass`` / ``noxMass`` — SO2 / NOx mass, **pounds**.
* ``heatInput`` — fuel heat input, MMBtu.

This module is ISO-agnostic. It loads the raw extracts, normalizes units to
kg, builds an 8760-hour calendar index aligned with the model's dispatch
clock (Feb 29 is dropped, matching ``run_calibration_full._hour_to_month``),
and exposes the three derivations the calibration pipeline needs:

* :func:`annual_plant_totals` — annual gross/heat/emissions per plant, the
  numerator/denominator inputs to the parasitic-load and emission-rate work.
* :func:`compute_parasitic_factors` — given annual CAMPD gross and EIA-923
  net generation per plant, the net/gross scale factor used to convert
  measured gross output to net output.
* :func:`plant_emission_rates` — per-plant kg CO2/NOx/SO2 per MWh **net**,
  marginal/no-load decomposition, and start/stop emission factors.
* :func:`plant_hourly_net` — per-plant 8760-hour **net** generation series,
  the observed benchmark for the per-plant hourly dispatch correlation.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

logger = logging.getLogger(__name__)

# Default location of the raw CAMPD state-year extracts (re-exported from the
# central path registry).

# --- Clean-backed read path (opt-in) ----------------------------------------
# By default this module parses the raw CAMPD state-year extracts under
# ``data/raw`` (the path below). Set ``MARKET_SIM_USE_CLEAN`` to a truthy value
# to instead route :func:`load_campd_hourly` through the curated ``emissions``
# clean datatype via ``scripts.lib.clean_io.read_clean`` — the standardized
# consumption seam. The switch is read from the environment per call (so tests
# and callers can toggle it without reimport) and defaults OFF: with it unset
# the raw path is used and behavior is byte-for-byte unchanged.
_USE_CLEAN_ENV: str = "MARKET_SIM_USE_CLEAN"
_TRUTHY: frozenset[str] = frozenset({"1", "true", "yes", "on"})


def _use_clean() -> bool:
    """Whether the clean-backed emissions read path is enabled (env-gated, default OFF)."""
    return os.environ.get(_USE_CLEAN_ENV, "").strip().lower() in _TRUTHY


# Unit conversions to kilograms (the canonical mass unit for derived rates).
SHORT_TON_TO_KG: float = 907.18474
LB_TO_KG: float = 0.45359237
# The dispatch model carries emission rates in metric tonnes per MWh and
# prices in $/tonne; divide kg by this to reach the model's internal unit.
KG_PER_TONNE: float = 1000.0

# Hours in the model's fixed (non-leap) dispatch calendar.
HOURS_PER_YEAR: int = 8760
_DAYS_IN_MONTH: tuple[int, ...] = (
    31,
    28,
    31,
    30,
    31,
    30,
    31,
    31,
    30,
    31,
    30,
    31,
)
# Cumulative hours before the first of each 1-based month, non-leap calendar.
_MONTH_START_HOUR: tuple[int, ...] = tuple(
    int(sum(_DAYS_IN_MONTH[:m]) * 24) for m in range(12)
)

# States feeding each ISO, for the convenience ISO → state lookup. ERCOT is
# approximated by Texas (the EIA-923 ``ERCO`` balancing-authority footprint);
# extend as more ISOs are calibrated.
ISO_STATES: dict[str, tuple[str, ...]] = {
    "ERCOT": ("TX",),
    # CA plus NV: Desert Star Energy Center (EIA 55077, 370.1 MW CC_REGULAR,
    # Clark County NV) is a CAISO-fleet plant whose CEMS history files under
    # Nevada, so the CA-only state list left it unobservable by the unit-level
    # intake — the FINDING-caiso193 §2 state-scope gap (2.42 % of the class,
    # the residual CC_REGULAR G-COV miss after the caiso-196 remap repair).
    # The NYISO NY+NJ template applies verbatim: ``load_campd_hourly`` and the
    # outage derivation filter every loaded state to the ISO's own fleet, so
    # listing NV here cannot leak non-CAISO NV plants into CAISO.
    "CAISO": ("CA", "NV"),
    # NY plus NJ: a handful of qualifying NYISO-fleet plants sit physically in
    # New Jersey (EIA-860 balancing authority ``NYIS``), so their unit-level
    # extract feeds NYISO too. ``load_campd_hourly`` and the outage derivation
    # filter every loaded state to the ISO's own fleet, so listing NJ here
    # cannot leak PJM-side NJ plants into NYISO.
    "NYISO": ("NY", "NJ"),
    # Keyed "NEISO" to match the iso_configs registry name (was "ISONE",
    # which no fleet loader recognised, so the lookup always came back empty).
    "NEISO": ("ME", "NH", "MA", "CT", "RI", "VT"),
    # Full PJM footprint. ``load_campd_hourly`` warns and skips any state
    # whose ``{STATE}_{YEAR}.parquet`` is not present, so listing the whole
    # footprint lets the outage derivation widen automatically as more CAMPD
    # extracts land. Unit-level extracts now present for every PJM-fleet state
    # (PA, NJ, MD, DE, IL, OH, IN, KY, WV, VA, TN, MI, DC) across 2023-2025;
    # NC is retained for completeness though no qualifying PJM-fleet plant
    # currently sits there.
    "PJM": (
        "PA",
        "NJ",
        "MD",
        "DE",
        "IL",
        "OH",
        "IN",
        "KY",
        "WV",
        "VA",
        "NC",
        "TN",
        "MI",
        "DC",
    ),
    # Full MISO footprint. The MISO fleet (EIA-860 BA ``MISO``) carries
    # qualifying plants across all of these states, and unit-level CAMPD
    # extracts for each now exist, so the unit-outage derivation covers the
    # whole fleet rather than the IL-only probe it began as. States overlap
    # PJM (IL, IN, KY, MI) and ERCOT (TX, MISO South / Entergy Texas); the
    # per-ISO fleet filter keeps each ISO's windows to its own plants.
    "MISO": (
        "AR",
        "IA",
        "IL",
        "IN",
        "KY",
        "LA",
        "MI",
        "MN",
        "MO",
        "MS",
        "ND",
        "SD",
        "TX",
        "WI",
    ),
    # Full SPP footprint — the 14 states carrying an EIA-860 plant with
    # balancing authority SWPP (docs/multi-iso/spp-data-audit.md §2.4 / §5
    # row 21; owner ruling P1, 2026-09-06). WY is deliberately EXCLUDED (no
    # SWPP plant — Wyoming SPP-adjacent generation files under WAUW, a WECC
    # BA); CO is retained on the PJM-``NC`` / NYISO-``NJ`` "for completeness"
    # precedent although its eight SWPP sites are 19.5 MW of solar with no
    # CEMS unit. States overlap MISO (AR, IA, LA, MN, MO, MT, ND, SD, TX) and
    # ERCOT (TX); the per-ISO fleet filter keeps each ISO's windows to its own
    # plants. Unit-level CAMPD extracts exist for every state with a CEMS
    # unit (OK/NE/NM landed by SPP-11, 2023-2026).
    "SPP": (
        "AR",
        "CO",
        "IA",
        "KS",
        "LA",
        "MN",
        "MO",
        "MT",
        "ND",
        "NE",
        "NM",
        "OK",
        "SD",
        "TX",
    ),
    # NWPP (registered 2026-09-14, lane NWPP-20): the seven states carrying a
    # CEMS-eligible footprint unit (docs/multi-iso/nwpp-data-audit.md §8 —
    # "ISO_STATES["NWPP"] = (ID, MT, NV, OR, UT, WA, WY)"). Unit-level CAMPD
    # extracts exist for every one: MT/NV/WY/CA on disk before the program,
    # ID/OR/UT/WA x 2023-2026 landed by NWPP-11 (16 files). CO excluded — its
    # one footprint plant is 7.5 MW of HYDRO (James W. Broderick, PACE), zero
    # CEMS-eligible units; CA excluded — 50.8 MW of which 15.0 is combustion
    # and NONE appears in the committed CA_2024 extract (the CA files are
    # inert for NWPP, exactly as WY's were for SPP); TX excluded by the
    # §2.8(a) rejection of plant 68906. CEMS reaches 30.98 % of footprint
    # nameplate / 41.8-43.6 % of energy (owner ruling N8 — legacy bins first).
    "NWPP": ("ID", "MT", "NV", "OR", "UT", "WA", "WY"),
}

# States feeding an ISO's MERIT-ORDER PANEL — the identification scope of the
# economic-layup classifier — pinned INDEPENDENTLY of :data:`ISO_STATES`, which
# is the DETECTION-coverage scope.
#
# The two lists answer different questions and must be free to move apart
# (CLAUDE.md rule 23 ``[R-FROZEN-DERIVE]``: an instrument is re-identified only
# when its own source data changes):
#
# * :data:`ISO_STATES` = "which CAMPD state files must be READ so every plant in
#   the ISO's fleet is observable?" Widening it is pure coverage — the loaders
#   and the outage derivation filter every loaded state back to the ISO's own
#   fleet, so a new state adds plants and removes nothing.
# * this map = "whose running capacity SETS the revealed clearing cost the layup
#   classifier scores each window against?" That object is the ISO's own
#   market, so a detection widening must NOT re-identify it.
#
# ``scripts.lib.outage_detect.build_merit_order_panel`` is fleet-blind by design
# (self-contained, no EIA-860 join), so before this pin it inherited the
# detection list verbatim and a coverage widening silently moved the classifier
# for every already-covered plant. Measured at caiso-198: adding NV for one
# CAISO-fleet plant (Desert Star, EIA 55077) put 59-64 units of 13-14 NON-CAISO
# NV Energy facilities into CAISO's panel, lifting the RCC in 87-97 % of hours
# (mean +3.45 $/MWh in 2024) and reclassifying 275 CA-facility windows that the
# widening has no business touching (FINDING-caiso198-desertstar-extract-2026-08-16.md
# §3; owner ruling caiso-199 §5 option 1).
#
# An ISO absent from this map falls back to :data:`ISO_STATES` — the pre-pin
# behaviour, so no other ISO's committed extract moves (rule 25
# ``[R-ISO-SCOPE]``). The same fleet-blindness exists at NYISO (NY+NJ), PJM and
# MISO (shared states); those are each their own lane's measurement and this pin
# adjudicates none of them.
#
# NOTE ON SCOPE: this is a STATE-LIST pin, not a fleet filter. The committed
# CA-only panel already contains non-CAISO CA units (LADWP and municipal
# utilities file CEMS under CA), and that is the panel the caiso-192 gates
# adjudicated the guard on. Making the panel fleet-PURE would move the committed
# extract and needs its own baseline measurement; it is not done here.
ISO_MERIT_PANEL_STATES: dict[str, tuple[str, ...]] = {
    # CAISO's panel stays CA-only — the scope every committed CAISO extract
    # through sha 5f3e35c5.. was identified on, and the scope under which the
    # Desert Star re-derive is STRICTLY ADDITIVE (candidate sha da33e509..,
    # layup companion byte-identical). NV is read for DETECTION only.
    "CAISO": ("CA",),
}

# CEMS-to-EIA split-plant remap: units that report CAMPD under a *legacy*
# ORIS code but belong to a different EIA plant in the model fleet. AES
# repowered Alamitos and Huntington Beach with new CCGTs that EIA lists as
# their own plants (62115 / 62116) while their CEMS monitors kept filing
# under the legacy boiler ORIS codes (315 / 335) alongside the remaining
# once-through-cooling steamers. Keyed ``(facilityId, unitId)`` exactly as
# the CAMPD unit-level extracts label them; the value is the EIA plant code
# the unit's history belongs to. Applied wherever unit identity is known
# (the unit-level extracts); the facility-level loader substitutes the
# unit-level rows for these facilities so the split holds there too.
CAMPD_UNIT_PLANT_REMAP: dict[tuple[int, str], int] = {
    (315, "CT1"): 62115,  # AES Alamitos Energy Center (CC_REGULAR)
    (315, "CT2"): 62115,
    (335, "CT1"): 62116,  # AES Huntington Beach Energy Project (CC_REGULAR)
    (335, "CT2"): 62116,
    # El Segundo Energy Center (CC_REGULAR): the 2013 repower's two CTs file
    # CEMS under the legacy El Segundo steam-plant ORIS 330 as units "5"/"7"
    # (every CA extract 2018-2025), while EIA lists the plant as 57901 with
    # the same generator IDs. Unlike 315/335, the legacy EIA plant (330)
    # fully retired in 2015, so nothing remained in the fleet to collide
    # with and the missing entry failed SILENTLY: facility 330 matched no
    # fleet plant and the outage derivation skipped it before detection.
    # [R-ACCURATE] FINDING-caiso193-wefor-residual-2026-08-15.md §2;
    # PRECHECK-caiso196-elsegundo-remap-2026-08-15.md §1.
    (330, "5"): 57901,
    (330, "7"): 57901,
    # Astoria Energy II (NYISO, CC_REGULAR): CEMS files the whole Astoria
    # Energy site under facility 55375 (four CTs), while EIA-860 carries the
    # 2011 block's CT3 / CT4 / ST2 under its own plant 57664 and eGRID has no
    # row for 57664 in any vintage. The identity is exact: eGRID
    # PLNGENAN(55375) == EIA-923 netgen(55375) + netgen(57664) to < 0.5 MWh in
    # all seven vintages 2018-2024 (the merged-identity row of
    # egrid_identity_heat_rates_NYISO.csv). Without the entry the outage derive
    # booked CT3 / CT4 against plant 55375 (a 1,221 MW denominator), so 57664
    # was never derated and 55375 was derated for its sibling's outages, and
    # the tranche derive read 55375 at a 150 % median CF.
    # [R-ACCURATE] FINDING-nyiso186-cc-regular-2024-class-2026-09-04.md §3;
    # PREREG-nyiso187-ct-steam-merit-position.md §1 Object 2.
    (55375, "CT3"): 57664,
    (55375, "CT4"): 57664,
}

# Facilities with at least one remapped unit (split facilities).
CAMPD_SPLIT_FACILITIES: frozenset[int] = frozenset(f for f, _ in CAMPD_UNIT_PLANT_REMAP)

# Same ids as an array, so a normalizer can select the remap-eligible rows with
# one vectorized ``np.isin`` instead of a per-row dict lookup (PERF-B).
_CAMPD_REMAP_FACILITY_IDS: np.ndarray = np.array(
    sorted(CAMPD_SPLIT_FACILITIES), dtype=np.int64
)

# Common-generator stack pairs: ONE generating unit whose flue gas is monitored
# on two separate paths, which CEMS files as two "units". CAMPD repeats the
# generator's FULL ``grossLoad`` on BOTH rows while splitting ``heatInput`` and
# the emission masses between them, so summing a facility's units double-counts
# generation while heat and mass sum correctly. The value is the set of
# DUPLICATE unit ids whose ``grossLoad`` must be dropped; the primary twin
# carries the generator's output. Heat and masses are never touched -- they are
# genuinely per-path and must keep summing.
#
# The mapping is ``{facilityId: {duplicate_unit: primary_unit}}``: consumers
# working at PLANT grain only need the duplicate's grossLoad dropped, while
# consumers working at UNIT grain must additionally re-label the duplicate onto
# its primary so the pair aggregates into the ONE generator it physically is.
#
# Astoria Generating Station (ORIS 8906, NYISO/NYC, ST_GAS) files units 30 and
# 50 as reheat/superheat pairs ``31RH``/``32SH`` and ``51RH``/``52SH``.
# Identified at nyiso-141 on three independent channels, none of them a
# residual (rule 13 ``[R-MEASURED]``, rule 14 ``[R-ACCURATE]``):
#   1. INTERNAL -- 51RH/52SH ``grossLoad`` is byte-identical in all 4,327 fired
#      hours of 2025 (max |diff| exactly 0.000, corr 1.000000); 31RH/32SH in
#      99.98 %. Genuine twin units dispatched in lockstep do NOT do this: the
#      Gowanus / Narrows / Holtsville / Barrett peaker banks reach 95-100 %
#      identical hours yet each carries its OWN full heat input.
#   2. PHYSICAL -- counted separately each row implies 5,172-5,512 Btu/kWh,
#      impossible for a wall-/tangentially-fired BOILER (better than a modern
#      combined cycle). Counted once against the pair's summed heat input it is
#      10,436-10,764 Btu/kWh, exactly its NYISO gas-steam peers (Arthur Kill
#      10,033, Northport 9,983, Bowline 9,665).
#   3. EXTERNAL -- EIA-923 net over CAMPD gross is 0.472 / 0.471 in 2023 / 2024
#      (~one half) where every genuine NY gas-steam peer sits at 0.92-0.96.
#      Dropping the duplicate ``grossLoad`` lands Astoria at 0.935 / 0.937,
#      inside the peer band. The old ratio was OUTSIDE
#      ``_PARASITIC_MIN``.. ``_PARASITIC_MAX``, so ``compute_parasitic_factors``
#      already flagged it as implausible and silently substituted the ST_GAS
#      class default -- detecting the anomaly and then papering over it.
# Blast radius the correction repairs: the plant's parasitic factor; its
# unit-level CEMS emission rates (279-322 kg CO2/MWh against a 520-575 peer
# band -- a fired boiler cannot emit that little); and, in any year EIA-923 has
# not yet published the plant, the class benchmark itself via
# ``_backfill_eia923_with_campd``. That last one fired for NYISO 2025 and put
# 2.672 TWh of ST_GAS actuals on the books where the metered value is ~1.27.
# FINDING-nyiso141-astoria-stack-duplication-2026-08-17.md.
CAMPD_STACK_DUPLICATE_UNITS: dict[int, dict[str, str]] = {
    8906: {"32SH": "31RH", "52SH": "51RH"},
}

# Facilities carrying at least one duplicate-reporting stack row.
CAMPD_STACK_DUPLICATE_FACILITIES: frozenset[int] = frozenset(
    CAMPD_STACK_DUPLICATE_UNITS
)

# Facilities whose correct plant-level series can only be built from unit
# identity, so a facility-level extract must be replaced by its unit-level
# companion: the split-plant remaps plus the stack-duplicate drops.
_FACILITIES_NEEDING_UNIT_ROWS: frozenset[int] = (
    CAMPD_SPLIT_FACILITIES | CAMPD_STACK_DUPLICATE_FACILITIES
)


def _to_numeric_by_uniques(s: pd.Series) -> pd.Series:
    """``pd.to_numeric(s, errors="coerce")`` evaluated over ``s``'s uniques.

    CAMPD's ``facilityId`` arrives as a string column of ~1M rows carrying a
    few dozen distinct ORIS codes, and parsing it row-by-row is the single
    largest cost in :func:`_normalize_campd` (PERF-B: ~0.95 s per state-year
    extract, paid again inside :func:`stack_duplicate_mask`). Parsing the
    uniques and gathering by factorize code is the same computation on 10^2
    values instead of 10^6.

    Value- and dtype-identical to the direct call by construction: the unique
    set carries the same values, so ``to_numeric``'s integer-vs-float dtype
    choice is the same, and the gather preserves it. Degenerate inputs (empty,
    already numeric, or too few repeats to pay for the factorize) fall through
    to the direct call unchanged.
    """
    if s.dtype.kind in "iufc" or len(s) < 1024:
        return pd.to_numeric(s, errors="coerce")
    codes, uniques = pd.factorize(s, use_na_sentinel=True)
    if len(uniques) * 4 >= len(s):
        return pd.to_numeric(s, errors="coerce")
    vals = pd.to_numeric(pd.Series(uniques), errors="coerce")
    if vals.dtype.kind in "iu" and not (codes < 0).any() and not vals.isna().any():
        # No NA anywhere, so the integer dtype ``to_numeric`` chose survives
        # the gather (a NaN sentinel would force the whole column to float).
        return pd.Series(vals.to_numpy()[codes], index=s.index)
    gathered = np.concatenate([vals.to_numpy(dtype="float64"), [np.nan]])
    return pd.Series(gathered[codes], index=s.index)


def stack_duplicate_mask(facility: pd.Series, unit: pd.Series) -> pd.Series:
    """Return a boolean mask of duplicate-reporting stack rows.

    A ``True`` row's ``grossLoad`` repeats its primary twin's and must be
    dropped before generation is summed; its heat input and emission masses are
    genuinely its own and must be kept. See
    :data:`CAMPD_STACK_DUPLICATE_UNITS` for the identification.

    Args:
        facility: CAMPD ``facilityId`` values (numeric or string).
        unit: CAMPD ``unitId`` values, exactly as the extract labels them.

    Returns:
        Boolean Series aligned to ``facility``/``unit``.
    """
    fac = _to_numeric_by_uniques(facility).fillna(-1).astype(int)
    uid = unit.astype(str)
    mask = pd.Series(False, index=fac.index)
    for fid, pairs in CAMPD_STACK_DUPLICATE_UNITS.items():
        mask |= (fac == fid) & uid.isin(pairs)
    return mask


def merge_stack_duplicate_units(facility: pd.Series, unit: pd.Series) -> pd.Series:
    """Return ``unit`` with duplicate stack rows re-labelled onto their primary.

    For consumers that aggregate at UNIT grain. Combined with dropping the
    duplicate's ``grossLoad`` (:func:`stack_duplicate_mask`), a group-by on the
    relabelled unit id sums the pair into the single generator it physically
    is: generation counted once, heat input and emission masses summed over
    both monitored paths.

    Args:
        facility: CAMPD ``facilityId`` values (numeric or string).
        unit: CAMPD ``unitId`` values, exactly as the extract labels them.

    Returns:
        Series of unit ids, aligned to the input, duplicates re-labelled.
    """
    fac = _to_numeric_by_uniques(facility).fillna(-1).astype(int)
    out = unit.astype(str).copy()
    for fid, pairs in CAMPD_STACK_DUPLICATE_UNITS.items():
        at = fac == fid
        if at.any():
            out = out.where(~at, out.replace(pairs))
    return out


# EIA-923 ``fuel_type`` codes burned by coal-class units.
_COAL_EIA_FUELS: frozenset[str] = frozenset(
    {"SUB", "BIT", "LIG", "ANT", "RC", "WC", "SC"}
)

# EIA-923 ``fuel_type`` codes that are NOT stack-monitored combustion fuels,
# excluded when summing the net generation that CAMPD's gross output should
# reconcile against (renewables, nuclear, hydro, storage, purchases).
_NON_COMBUSTION_FUELS: frozenset[str] = frozenset(
    {
        "WND",
        "SUN",
        "WAT",
        "NUC",
        "MWH",
        "GEO",
        "PUR",
        "OTH",
        "WH",
        "HPS",
    }
)

# Plausible band for a net/gross parasitic factor. Outside this, the CAMPD
# gross and EIA-923 net almost certainly cover different unit sets at the
# plant; such plants fall back to a class default.
_PARASITIC_MIN: float = 0.80
_PARASITIC_MAX: float = 1.00

# Class-default parasitic-load fractions (1 − net/gross) keyed by the
# registry ``plant_group``, used when a plant's measured factor is missing
# or implausible. Sources: EPRI / EIA station-service typicals by technology.
DEFAULT_PARASITIC_LOAD_PCT: dict[str, float] = {
    "COAL": 0.070,
    "ST_GAS": 0.050,
    "ST_CHP": 0.050,
    "CC_REGULAR": 0.025,
    "CC_CHP": 0.025,
    "CT_PEAKER": 0.010,
    "CT_CHP": 0.010,
    "OTHER": 0.030,
}
# Fallback when even the plant_group is unknown.
_DEFAULT_PARASITIC_LOAD_PCT: float = 0.03

# Minimum gross load (MW) treated as "online" when detecting start/stop
# events, to ignore sensor noise around zero.
_ONLINE_MW: float = 1.0

# EPA default CO2 emission factor for natural gas, kg CO2 per MMBtu (117.0
# lb/MMBtu). Used to backfill CO2 mass for units that report NOx and heat
# input but not CO2 — common for gas peakers in CEMS. A plant that reports
# CO2 for *some* hours is instead backfilled at its own measured intensity.
DEFAULT_CO2_KG_PER_MMBTU: float = 53.06


def states_for_iso(iso: str) -> tuple[str, ...]:
    """Return the CAMPD state codes feeding an ISO (see :data:`ISO_STATES`)."""
    return ISO_STATES.get(iso.upper(), ())


def merit_panel_states_for_iso(iso: str) -> tuple[str, ...]:
    """Return the CAMPD state codes feeding an ISO's merit-order panel.

    The panel's identification scope, pinned independently of the detection
    scope :func:`states_for_iso` — see :data:`ISO_MERIT_PANEL_STATES` for why
    the two must be free to move apart. An ISO with no pin falls back to its
    detection list, which is the pre-pin behaviour.
    """
    key = iso.upper()
    pinned = ISO_MERIT_PANEL_STATES.get(key)
    return pinned if pinned is not None else ISO_STATES.get(key, ())


# ISOs whose merit-order panel ALSO admits the ISO's own OUT-OF-STATE fleet
# members — the caiso-199 §3b narrowing of the state-list pin above. Under a
# bare state pin, a fleet plant filing CEMS outside the panel states is not a
# member of the panel its own spans are scored against (out_of_merit_share ->
# None, is_economic_layup -> False fail-safe for every window). Membership
# closes that asymmetry WITHOUT re-admitting the non-fleet units the pin
# exists to exclude: a facility qualifies iff it appears in an out-of-panel
# DETECTION state's CAMPD files AND its plant code resolves into the ISO's own
# fleet registry — derived at derive time from the same group_by_code the
# detection path filters on, never enumerated per plant (rule 24
# [R-REGISTRY]). Today CAISO's derived set is exactly {NV: (55077,)} — Desert
# Star Energy Center, the one CAISO-fleet plant filing CEMS in NV.
# [R-FROZEN-DERIVE] charter: PRECHECK-caiso200-panel-membership-2026-08-17.md
# §1-§2 (the caiso-199 §3b named option, measured at caiso-198 run Y).
# An ISO absent from this set admits no out-of-state members — the pre-charter
# behaviour, so no other ISO's committed extract moves (rule 25 [R-ISO-SCOPE]).
MERIT_PANEL_FLEET_MEMBER_ISOS: frozenset[str] = frozenset({"CAISO"})


def merit_panel_admits_fleet_members(iso: str) -> bool:
    """True when the ISO's merit panel admits its own out-of-state fleet members.

    See :data:`MERIT_PANEL_FLEET_MEMBER_ISOS` — the membership itself is
    derived by the outage deriver from the fleet registry and the detection
    state list; this predicate only arms the derivation for the ISO.
    """
    return iso.upper() in MERIT_PANEL_FLEET_MEMBER_ISOS


def _hour_index_8760(
    month: np.ndarray, day: np.ndarray, hour: np.ndarray
) -> np.ndarray:
    """Map ``(month, day, hour)`` to a non-leap hour-of-year index.

    Returns an int array in ``[0, 8760)``; Feb 29 maps to ``-1`` so callers
    can drop it, keeping the CAMPD clock aligned with the model's fixed
    8760-hour calendar.
    """
    month = np.asarray(month, dtype=int)
    day = np.asarray(day, dtype=int)
    hour = np.asarray(hour, dtype=int)
    base = np.array(_MONTH_START_HOUR, dtype=int)[month - 1]
    idx = base + (day - 1) * 24 + hour
    leap_day = (month == 2) & (day == 29)
    idx = np.where(leap_day, -1, idx)
    return idx


def _read_one(
    state: str, year: int, raw_dir: Path, prefer_unit_level: bool = False
) -> pd.DataFrame | None:
    """Load and normalize one ``{STATE}_{YEAR}.parquet`` extract, or ``None``.

    Resolves the file from the facility-level subdirectory
    (``campd-facility-level/``) first, then the unit-level one
    (``campd-unit-level/``) — so the older facility-summed extracts (e.g. the
    ERCOT TX file and the PJM PA/NJ/MD/DE/IL files) are used unchanged, while a
    state present *only* as a newer unit-level upload (one row per unit-hour,
    with a ``unitId`` column; e.g. OH/WV/KY/VA/IN/DC) loads from the unit
    directory. Facility-first deliberately keeps ERCOT and the existing PJM
    states bit-for-bit, even where a state appears in both. Unit-level rows are
    summed to the facility per hour downstream (:func:`plant_hourly_grid`,
    :func:`plant_hourly_net`), so the extra granularity is transparent here.

    The only exception is the split facilities in
    :data:`CAMPD_UNIT_PLANT_REMAP` (CA only): their rows are re-keyed (or, for
    a facility-level file, substituted from the companion unit-level extract)
    so each unit's history lands on the EIA plant the model fleet carries.
    """
    fname = f"{state}_{year}.parquet"
    # ``prefer_unit_level`` inverts the first two candidates for a caller that
    # NEEDS per-unit identity (campd.plant_group_hourly_net). The default order
    # is unchanged and deliberately facility-first, which keeps ERCOT and the
    # existing PJM states bit-for-bit; a state present in BOTH directories (NY
    # is) otherwise silently yields a frame whose units the publisher already
    # summed away.
    candidates = (
        raw_dir / "campd-facility-level" / fname,
        raw_dir / "campd-unit-level" / fname,
        raw_dir / fname,  # legacy flat layout (tests / old data)
    )
    if prefer_unit_level:
        candidates = (candidates[1], candidates[0], candidates[2])
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        logger.warning(
            "CAMPD extract not found for %s %d (looked in %s/"
            "campd-facility-level, /campd-unit-level, and the flat dir)",
            state,
            year,
            raw_dir,
        )
        return None
    raw = pd.read_parquet(path)
    out = _normalize_campd(raw, year)
    # Unit-identity repairs, facility-level case. A unit-level file carries
    # unit identity, so both repairs apply row-by-row in _normalize_campd. A
    # facility-level file has already summed the facility's units into one
    # series, which destroys the identity BOTH repairs key on:
    #   * split plants (CAMPD_UNIT_PLANT_REMAP) need it to re-key each unit's
    #     history onto the EIA plant the model fleet carries;
    #   * stack-duplicate plants (CAMPD_STACK_DUPLICATE_UNITS) need it to drop
    #     the repeated grossLoad -- the facility-level sum has the
    #     double-count already baked in and no way to see it.
    # Substitute the unit-level rows for those facilities when the companion
    # extract exists. Without a companion file the facility stays summed under
    # the legacy code (e.g. CA 2023 until U1 lands).
    if "unitId" not in raw.columns:
        split = sorted(_FACILITIES_NEEDING_UNIT_ROWS & set(out["plant_id"].unique()))
        if split:
            unit_path = raw_dir / "campd-unit-level" / fname
            if unit_path.exists():
                unit_raw = pd.read_parquet(unit_path)
                unit_raw = unit_raw[
                    pd.to_numeric(unit_raw["facilityId"], errors="coerce").isin(split)
                ]
                out = pd.concat(
                    [
                        out[~out["plant_id"].isin(split)],
                        _normalize_campd(unit_raw, year),
                    ],
                    ignore_index=True,
                )
            else:
                logger.warning(
                    "CAMPD %s %d: facilities %s need unit identity (split-plant "
                    "remap or stack-duplicate drop) but have no unit-level "
                    "extract; their units stay summed under the legacy code",
                    state,
                    year,
                    split,
                )
    return out


def _normalize_campd(raw: pd.DataFrame, year: int) -> pd.DataFrame:
    """Normalize one raw CAMPD extract to the model's hourly schema.

    When the extract carries unit identity (``unitId``), units in
    :data:`CAMPD_UNIT_PLANT_REMAP` are re-keyed to the EIA plant their
    history belongs to before any facility summing happens downstream.
    """
    plant_id = _to_numeric_by_uniques(raw["facilityId"])
    gross = pd.to_numeric(raw["grossLoad"], errors="coerce")
    if "unitId" in raw.columns and len(raw):
        fac = plant_id.fillna(-1).astype(int).to_numpy()
        uid = raw["unitId"].astype(str).to_numpy()
        # Only rows at a split facility can remap, and the remap table is CA-only
        # (:data:`CAMPD_UNIT_PLANT_REMAP`), so restrict the per-row dict lookup to
        # those rows: every other row's ``.get`` returns its own ``f`` unchanged.
        # PERF-B: the unrestricted comprehension ran 7M dict lookups per PJM year
        # to remap nothing at all (~4.4 s of the phase).
        remapped = fac.copy()
        at_split = np.flatnonzero(np.isin(fac, _CAMPD_REMAP_FACILITY_IDS))
        for i in at_split:
            remapped[i] = CAMPD_UNIT_PLANT_REMAP.get((fac[i], uid[i]), fac[i])
        plant_id = pd.Series(remapped, index=raw.index, dtype=float).where(
            plant_id.notna()
        )
        # Common-generator stack pairs repeat the generator's grossLoad on both
        # monitored paths. Drop the duplicate's copy so units sum to the
        # generator's real output; heat and emission masses are per-path and
        # stay untouched so they keep summing correctly.
        dup = stack_duplicate_mask(raw["facilityId"], raw["unitId"])
        if dup.any():
            gross = gross.mask(dup)
    out = pd.DataFrame(
        {
            "plant_id": plant_id,
            # Unit identity, carried through for the per-unit attribution seam
            # (nyiso-175b): a mixed facility's CEMS rows can only be split
            # across the model's bins if the unit each row belongs to survives
            # normalization. Purely additive — every existing consumer selects
            # columns by name — and present ONLY on the raw path, because the
            # curated ``emissions`` clean datatype does not carry unit identity
            # at all. :func:`plant_group_hourly_net` therefore RAISES rather
            # than silently falling back when they are absent.
            "unit_id": (
                raw["unitId"].astype(str)
                if "unitId" in raw.columns
                else pd.Series([""] * len(raw), index=raw.index)
            ),
            "unit_type": (
                raw["unitType"].astype(str)
                if "unitType" in raw.columns
                else pd.Series([""] * len(raw), index=raw.index)
            ),
            "facility_name": raw["facilityName"].astype(str),
            "state": raw["stateCode"].astype(str),
            "year": np.int16(year),
            "date": pd.to_datetime(raw["date"]),
            "hour": pd.to_numeric(raw["hour"], errors="coerce").astype("Int64"),
            "gross_mw": gross,
            "steam_load": pd.to_numeric(raw["steamLoad"], errors="coerce"),
            "co2_kg": pd.to_numeric(raw["co2Mass"], errors="coerce") * SHORT_TON_TO_KG,
            "nox_kg": pd.to_numeric(raw["noxMass"], errors="coerce") * LB_TO_KG,
            "so2_kg": pd.to_numeric(raw["so2Mass"], errors="coerce") * LB_TO_KG,
            "heat_mmbtu": pd.to_numeric(raw["heatInput"], errors="coerce"),
        }
    )
    out = out.dropna(subset=["plant_id", "hour"])
    out["plant_id"] = out["plant_id"].astype(int)
    out["hour"] = out["hour"].astype(int)
    return out


def _import_clean_io():
    """Import the shared ``scripts.lib.clean_io`` reader seam, lazily.

    ``clean_io`` lives under ``scripts/`` (not an installed package), so the
    repo root is put on ``sys.path`` the way the curation scripts do before the
    import. Done lazily — only the opt-in clean path pays this cost, and the
    raw path never imports it.
    """
    import sys

    from market_sim.config import paths

    root = str(paths.REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from scripts.lib import clean_io  # noqa: E402

    return clean_io


def _clean_to_model_frame(clean: pd.DataFrame, year: int) -> pd.DataFrame:
    """Map a clean ``emissions`` frame onto this module's hourly model schema.

    Rebuilds the columns the raw normalizer (:func:`_normalize_campd`) emits so
    every downstream derivation works unchanged: ``date`` / ``hour`` come from
    the local wall-clock (``interval_start_local``, which is the same Local
    Standard Time the raw extract carries), masses pass through in kg, and the
    non-leap ``hour_of_year`` index is recomputed (Feb 29 dropped). Columns the
    clean schema deliberately does not carry — ``facility_name``, ``state``,
    ``steam_load`` — are filled with empty/NaN placeholders.
    """
    local = pd.to_datetime(clean["interval_start_local"])
    out = pd.DataFrame(
        {
            "plant_id": pd.to_numeric(clean["plant_id"], errors="coerce"),
            "facility_name": "",
            "state": "",
            "year": np.int16(year),
            "date": local.dt.normalize(),
            "hour": local.dt.hour.astype("Int64"),
            "gross_mw": pd.to_numeric(clean["gross_mw"], errors="coerce"),
            "steam_load": np.nan,
            "co2_kg": pd.to_numeric(clean["co2_kg"], errors="coerce"),
            "nox_kg": pd.to_numeric(clean["nox_kg"], errors="coerce"),
            "so2_kg": pd.to_numeric(clean["so2_kg"], errors="coerce"),
            "heat_mmbtu": pd.to_numeric(clean["heat_input_mmbtu"], errors="coerce"),
        }
    )
    out = out.dropna(subset=["plant_id", "hour", "date"])
    out["plant_id"] = out["plant_id"].astype(int)
    out["hour"] = out["hour"].astype(int)
    idx = _hour_index_8760(out["date"].dt.month, out["date"].dt.day, out["hour"])
    out["hour_of_year"] = idx
    return out[idx >= 0].reset_index(drop=True)


def load_campd_hourly_clean(
    years: list[int] | tuple[int, ...],
    *,
    plant_ids: set[int] | None = None,
) -> pd.DataFrame:
    """Load hourly emissions from the curated clean tree (the clean-backed path).

    Mirror of :func:`load_campd_hourly`, but sourced from
    ``clean_io.read_clean("emissions", year=...)`` rather than the raw CAMPD
    state-year extracts. The clean ``emissions`` datatype is partitioned by year
    only — its schema standardizes the two CAMPD grains and drops ``stateCode``
    — so this reads whole years; pass ``plant_ids`` to restrict to a known set
    of plants (e.g. an ISO fleet, or, as the parity test does, exactly the
    plants a raw state-slice covers).

    Returns the same model-facing schema as :func:`load_campd_hourly`
    (``plant_id``, ``gross_mw``, masses in kg, ``heat_mmbtu``, ``hour_of_year``,
    …), so downstream derivations are unaffected by the source switch. Years
    with no clean partition are warned and skipped; the result is empty when no
    partition is found.
    """
    clean_io = _import_clean_io()
    frames: list[pd.DataFrame] = []
    for year in years:
        year = int(year)
        if not clean_io.clean_exists("emissions", year=year):
            logger.warning(
                "no clean emissions partition for %d; regenerate with "
                "`python scripts/regenerate_clean.py emissions`",
                year,
            )
            continue
        clean = clean_io.read_clean("emissions", year=year, validate=False)
        frames.append(_clean_to_model_frame(clean, year))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    if plant_ids is not None:
        wanted = {int(p) for p in plant_ids}
        df = df[df["plant_id"].isin(wanted)].reset_index(drop=True)
    return df


def load_campd_hourly(
    states: list[str] | tuple[str, ...],
    years: list[int] | tuple[int, ...],
    raw_dir: str | Path | None = None,
    prefer_unit_level: bool = False,
) -> pd.DataFrame:
    """Load and normalize CAMPD hourly extracts for states and years.

    Args:
        states: CAMPD ``stateCode`` values, e.g. ``["TX"]`` for ERCOT.
        years: Calendar years, e.g. ``[2023, 2024, 2025]``.
        raw_dir: Directory holding ``{STATE}_{YEAR}.parquet``; ``None`` uses
            :data:`RAW_DATA_DIR`.
        prefer_unit_level: Read the ``campd-unit-level`` extract in preference
            to the facility-level one, for a caller that needs per-unit
            identity (:func:`plant_group_hourly_net`). Default ``False`` keeps
            the facility-first resolution order every existing caller relies
            on. Ignored on the clean path, which carries no unit identity at
            all.

    Returns:
        One row per ``(plant, unit-hour)`` with masses in kg, gross load in
        MW, heat input in MMBtu, plus an ``hour_of_year`` column in
        ``[0, 8760)`` (Feb 29 rows are dropped). Empty when no extract is
        found.

    When the ``MARKET_SIM_USE_CLEAN`` switch is enabled (see :func:`_use_clean`)
    the hourly rows are read from the curated ``emissions`` clean datatype via
    :func:`load_campd_hourly_clean` instead of the raw extracts. The clean
    datatype is partitioned by year (not state), so ``states`` is not applied in
    that mode and ``raw_dir`` is ignored; consumers narrow to their own fleet by
    ``plant_id`` downstream, exactly as they already do. The switch defaults
    OFF, leaving the raw path below unchanged.
    """
    if _use_clean():
        return load_campd_hourly_clean(years)
    base = Path(raw_dir) if raw_dir is not None else RAW_DATA_DIR
    frames = [
        df
        for state in states
        for year in years
        if (df := _read_one(state, int(year), base, prefer_unit_level)) is not None
    ]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    idx = _hour_index_8760(df["date"].dt.month, df["date"].dt.day, df["hour"])
    df["hour_of_year"] = idx
    if (idx >= 0).all():
        # Nothing to drop — the only negative index is Feb 29, so in a non-leap
        # year the boolean take below copies the whole (multi-million-row) frame
        # to reproduce it exactly. ``concat(ignore_index=True)`` already left a
        # clean RangeIndex, so ``reset_index(drop=True)`` is a no-op here too.
        # PERF-B: ~5 s per non-leap ISO-year.
        return df
    return df[idx >= 0].reset_index(drop=True)


def annual_plant_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Return annual gross / heat / emissions per ``(plant_id, year)``.

    Args:
        df: A frame from :func:`load_campd_hourly`.

    Returns:
        One row per ``(plant_id, year)`` with ``gross_mwh`` (sum of hourly
        gross MW), ``heat_mmbtu``, ``co2_kg``, ``nox_kg``, ``so2_kg``,
        ``op_hours`` (hours with gross load > 0) and ``facility_name``.
    """
    if df.empty:
        return pd.DataFrame()
    g = df.groupby(["plant_id", "year"], observed=True)
    out = g.agg(
        gross_mwh=("gross_mw", "sum"),
        heat_mmbtu=("heat_mmbtu", "sum"),
        co2_kg=("co2_kg", "sum"),
        nox_kg=("nox_kg", "sum"),
        so2_kg=("so2_kg", "sum"),
        facility_name=("facility_name", "first"),
    ).reset_index()
    op = (
        df[df["gross_mw"] > 0.0]
        .groupby(["plant_id", "year"], observed=True)["gross_mw"]
        .size()
        .rename("op_hours")
        .reset_index()
    )
    return out.merge(op, on=["plant_id", "year"], how="left").fillna({"op_hours": 0})


def compute_parasitic_factors(
    campd_annual: pd.DataFrame,
    eia923_net_by_plant_year: pd.DataFrame,
    plant_groups: dict[int, str] | None = None,
) -> pd.DataFrame:
    """Reconcile CAMPD gross against EIA-923 net to get parasitic factors.

    The parasitic-load factor is annual net generation divided by annual
    gross generation — the fraction of gross output delivered after station
    service. The dispatch model and the hourly correlation use it to scale
    CAMPD's measured gross down to net.

    Per ``(plant_id, year)`` the factor is ``net/gross``; a plant's pooled
    factor sums net and gross across years before dividing, so high-output
    years dominate. Factors outside :data:`_PARASITIC_MIN`..\
    :data:`_PARASITIC_MAX` (where the gross and net unit sets clearly differ)
    are flagged and replaced by the plant-group class default from
    :data:`DEFAULT_PARASITIC_LOAD_PCT`.

    Args:
        campd_annual: Output of :func:`annual_plant_totals`.
        eia923_net_by_plant_year: Columns ``plant_id``, ``year`` and
            ``net_mwh`` — EIA-923 net generation summed over the plant's
            combustion units (see :func:`eia923_combustion_net`).
        plant_groups: Optional ``{plant_id: plant_group}`` for class-default
            fallback.

    Returns:
        One row per ``(plant_id, year)`` plus a pooled ``year == 0`` summary
        row per plant, with ``gross_mwh``, ``net_mwh``, ``parasitic_factor``
        (net/gross, used for scaling), ``parasitic_load_pct`` (``1 −
        factor``), ``source`` (``measured`` / ``class_default``) and
        ``flag``.
    """
    groups = plant_groups or {}
    merged = campd_annual.merge(
        eia923_net_by_plant_year, on=["plant_id", "year"], how="left"
    )
    rows: list[dict] = []

    def _resolve(plant_id: int, gross: float, net: float) -> dict:
        raw = net / gross if gross > 0.0 and net > 0.0 else float("nan")
        group = groups.get(int(plant_id), "")
        if np.isnan(raw) or raw < _PARASITIC_MIN or raw > _PARASITIC_MAX:
            pct = DEFAULT_PARASITIC_LOAD_PCT.get(group, _DEFAULT_PARASITIC_LOAD_PCT)
            factor = 1.0 - pct
            source = "class_default"
            flag = "no_net" if np.isnan(raw) else "out_of_band"
        else:
            factor = raw
            pct = 1.0 - factor
            source = "measured"
            flag = "ok"
        return {
            "gross_mwh": round(float(gross), 3),
            "net_mwh": round(float(net), 3) if net == net else 0.0,
            "parasitic_factor": round(float(factor), 6),
            "parasitic_load_pct": round(float(pct), 6),
            "source": source,
            "flag": flag,
        }

    for _, r in merged.iterrows():
        rec = {"plant_id": int(r["plant_id"]), "year": int(r["year"])}
        rec.update(_resolve(r["plant_id"], r["gross_mwh"], r.get("net_mwh", np.nan)))
        rows.append(rec)

    # Pooled per-plant factor (year == 0): sum net and gross across years.
    pooled = merged.groupby("plant_id", observed=True).agg(
        gross_mwh=("gross_mwh", "sum"), net_mwh=("net_mwh", "sum")
    )
    for plant_id, p in pooled.iterrows():
        rec = {"plant_id": int(plant_id), "year": 0}
        rec.update(_resolve(plant_id, p["gross_mwh"], p["net_mwh"]))
        rows.append(rec)

    cols = [
        "plant_id",
        "year",
        "gross_mwh",
        "net_mwh",
        "parasitic_factor",
        "parasitic_load_pct",
        "source",
        "flag",
    ]
    return (
        pd.DataFrame(rows, columns=cols)
        .sort_values(["plant_id", "year"])
        .reset_index(drop=True)
    )


def pooled_factor_map(parasitic: pd.DataFrame) -> dict[int, float]:
    """Return ``{plant_id: parasitic_factor}`` from the pooled (year 0) rows."""
    pooled = parasitic[parasitic["year"] == 0]
    return dict(
        zip(pooled["plant_id"].astype(int), pooled["parasitic_factor"].astype(float))
    )


def _ols_intercept_slope(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Return ``(intercept, slope)`` of ``y = a + b·x`` by least squares.

    Returns ``(nan, nan)`` when ``x`` has no spread (a slope is undefined).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size < 3 or x.std() < 1e-9:
        return float("nan"), float("nan")
    b, a = np.polyfit(x, y, 1)
    return float(a), float(b)


def _full_hourly_grid(sub: pd.DataFrame) -> pd.DataFrame:
    """Return one plant-year's unit-summed hourly series on a gap-free clock.

    CAMPD omits non-operating hours, so off-hours are reconstructed as zeros
    over the contiguous hourly span the plant reported in, giving a series
    where ``gross_mw == 0`` marks genuine downtime (needed for start/stop
    detection). Multiple units at the plant are summed per hour.
    """
    by_hour = (
        sub.assign(ts=sub["date"] + pd.to_timedelta(sub["hour"], unit="h"))
        .groupby("ts", as_index=True)[
            ["gross_mw", "co2_kg", "nox_kg", "so2_kg", "heat_mmbtu"]
        ]
        .sum()
        .sort_index()
    )
    full = pd.date_range(by_hour.index.min(), by_hour.index.max(), freq="h")
    return by_hour.reindex(full, fill_value=0.0)


def plant_hourly_grid(df: pd.DataFrame, plant_id: int, year: int) -> pd.DataFrame:
    """Return one plant-year's unit-summed hourly series on a gap-free clock.

    Off-hours that CAMPD omits are reconstructed as zeros over the contiguous
    span the plant reported in, indexed by actual timestamps — the input to
    capacity-factor and outage analyses that need real calendar dates.

    Args:
        df: A frame from :func:`load_campd_hourly`.
        plant_id: EIA plant code to extract.
        year: Calendar year to extract.

    Returns:
        A ``DatetimeIndex``-ed frame with ``gross_mw``, ``co2_kg``, ``nox_kg``,
        ``so2_kg`` and ``heat_mmbtu``; empty when the plant-year is absent.
    """
    sub = df[(df["plant_id"] == int(plant_id)) & (df["year"] == int(year))]
    if sub.empty:
        return pd.DataFrame()
    return _full_hourly_grid(sub)


def _startup_factors(grid: pd.DataFrame) -> dict[str, float]:
    """Return start counts and per-start incremental emission adders.

    A start is an off→on transition (``gross_mw`` crossing
    :data:`_ONLINE_MW`). For each pollutant and heat input, the per-start
    adder is the mean over starts of the start hour's mass minus the
    steady-state mass predicted by the no-load + marginal fit on the
    plant's non-start operating hours — i.e. the extra burned warming the
    unit up. Negative residuals are clipped to zero.
    """
    gross = grid["gross_mw"].to_numpy()
    online = gross > _ONLINE_MW
    if online.sum() < 3:
        return {
            "starts": 0,
            "startup_co2_kg": 0.0,
            "startup_nox_kg": 0.0,
            "startup_so2_kg": 0.0,
            "startup_heat_mmbtu": 0.0,
        }
    prev = np.concatenate([[False], online[:-1]])
    start_mask = online & ~prev
    non_start_op = online & ~start_mask

    out: dict[str, float] = {"starts": int(start_mask.sum())}
    for col, key in (
        ("co2_kg", "startup_co2_kg"),
        ("nox_kg", "startup_nox_kg"),
        ("so2_kg", "startup_so2_kg"),
        ("heat_mmbtu", "startup_heat_mmbtu"),
    ):
        mass = grid[col].to_numpy()
        a, b = _ols_intercept_slope(gross[non_start_op], mass[non_start_op])
        if np.isnan(a):
            out[key] = 0.0
            continue
        predicted = a + b * gross[start_mask]
        residual = np.clip(mass[start_mask] - predicted, 0.0, None)
        out[key] = round(float(residual.mean()), 4) if residual.size else 0.0
    return out


def plant_emission_rates(df: pd.DataFrame, factors: dict[int, float]) -> pd.DataFrame:
    """Return per-plant emission rates and start/stop factors.

    For each ``(plant_id, year)`` and a pooled ``year == 0`` row:

    * ``*_kg_per_mwh_net`` — average emission rate per MWh **net** generation
      (gross scaled by the plant's parasitic factor): the headline figure for
      tuning per-MWh emission prices.
    * ``*_marginal_kg_per_mwh_gross`` / ``*_noload_kg_per_hr`` — the
      least-squares decomposition of hourly mass against gross load, so the
      marginal (load-following) and fixed (committed) emissions are separable.
    * ``starts`` and ``startup_*`` — the per-start incremental emissions, for
      tuning cycling-emission penalties.

    Args:
        df: A frame from :func:`load_campd_hourly`.
        factors: ``{plant_id: parasitic_factor}`` (net/gross), e.g. from
            :func:`pooled_factor_map`.

    Returns:
        One row per ``(plant_id, year)`` plus the pooled ``year == 0`` row.
    """
    if df.empty:
        return pd.DataFrame()

    def _co2_total(sub: pd.DataFrame, heat_total: float) -> tuple[float, str]:
        """Return ``(co2_kg_total, source)``, backfilling unmonitored hours.

        A plant reporting CO2 for some hours is scaled up to its full heat
        input at its own measured kg/MMBtu; one reporting none uses the EPA
        natural-gas default factor.
        """
        measured = float(sub["co2_kg"].sum())
        heat_with_co2 = float(sub.loc[sub["co2_kg"].notna(), "heat_mmbtu"].sum())
        if heat_with_co2 <= 0.0:
            return DEFAULT_CO2_KG_PER_MMBTU * heat_total, "heat_backfilled"
        if heat_with_co2 >= 0.999 * heat_total:
            return measured, "measured"
        factor = measured / heat_with_co2
        return factor * heat_total, "partial_backfill"

    def _rates(sub: pd.DataFrame, plant_id: int) -> dict:
        gross_mwh = float(sub["gross_mw"].sum())
        factor = float(factors.get(int(plant_id), 1.0))
        net_mwh = gross_mwh * factor
        heat_total = float(sub["heat_mmbtu"].sum())
        co2_total, co2_source = _co2_total(sub, heat_total)
        rec: dict = {
            "gross_mwh": round(gross_mwh, 3),
            "net_mwh": round(net_mwh, 3),
            "parasitic_factor": round(factor, 6),
            "heat_mmbtu": round(heat_total, 3),
            "heat_rate_mmbtu_per_mwh_net": (
                round(heat_total / net_mwh, 4) if net_mwh > 0 else 0.0
            ),
            "co2_kg_per_mwh_net": (
                round(co2_total / net_mwh, 6) if net_mwh > 0 else 0.0
            ),
            "co2_source": co2_source,
        }
        op = sub[sub["gross_mw"] > 0.0]
        a, b = _ols_intercept_slope(op["gross_mw"].to_numpy(), op["co2_kg"].to_numpy())
        rec["co2_marginal_kg_per_mwh_gross"] = round(b, 6) if not np.isnan(b) else 0.0
        rec["co2_noload_kg_per_hr"] = round(a, 4) if not np.isnan(a) else 0.0
        for col, mwh_key, marg_key, nl_key in (
            (
                "nox_kg",
                "nox_kg_per_mwh_net",
                "nox_marginal_kg_per_mwh_gross",
                "nox_noload_kg_per_hr",
            ),
            (
                "so2_kg",
                "so2_kg_per_mwh_net",
                "so2_marginal_kg_per_mwh_gross",
                "so2_noload_kg_per_hr",
            ),
        ):
            total = float(sub[col].sum())
            rec[mwh_key] = round(total / net_mwh, 6) if net_mwh > 0 else 0.0
            a, b = _ols_intercept_slope(op["gross_mw"].to_numpy(), op[col].to_numpy())
            rec[marg_key] = round(b, 6) if not np.isnan(b) else 0.0
            rec[nl_key] = round(a, 4) if not np.isnan(a) else 0.0
        return rec

    rows: list[dict] = []
    for (plant_id, year), sub in df.groupby(["plant_id", "year"], observed=True):
        rec = {
            "plant_id": int(plant_id),
            "year": int(year),
            "facility_name": str(sub["facility_name"].iloc[0]),
        }
        rec.update(_rates(sub, plant_id))
        rec.update(_startup_factors(_full_hourly_grid(sub)))
        rows.append(rec)

    for plant_id, sub in df.groupby("plant_id", observed=True):
        rec = {
            "plant_id": int(plant_id),
            "year": 0,
            "facility_name": str(sub["facility_name"].iloc[0]),
        }
        rec.update(_rates(sub, plant_id))
        # Pool starts across years; emission adders averaged over years seen.
        per_year = [
            _startup_factors(_full_hourly_grid(s))
            for _, s in sub.groupby("year", observed=True)
        ]
        rec["starts"] = int(sum(p["starts"] for p in per_year))
        for k in (
            "startup_co2_kg",
            "startup_nox_kg",
            "startup_so2_kg",
            "startup_heat_mmbtu",
        ):
            vals = [p[k] for p in per_year if p["starts"] > 0]
            rec[k] = round(float(np.mean(vals)), 4) if vals else 0.0
        rows.append(rec)

    return pd.DataFrame(rows).sort_values(["plant_id", "year"]).reset_index(drop=True)


def plant_hourly_net(
    df: pd.DataFrame,
    factors: dict[int, float],
    year: int,
    hours: int = HOURS_PER_YEAR,
) -> dict[int, np.ndarray]:
    """Return per-plant 8760-hour **net** generation series for one year.

    Each plant's hourly gross load is summed across its units, placed on the
    model's fixed hour-of-year clock, and scaled by the plant's parasitic
    factor to net. Hours the plant did not report are zero (offline).

    Args:
        df: A frame from :func:`load_campd_hourly`.
        factors: ``{plant_id: parasitic_factor}`` (net/gross).
        year: Calendar year to extract.
        hours: Length of the output series (model dispatch horizon).

    Returns:
        ``{plant_id: (hours,) net MW}`` for every plant operating that year.
    """
    out: dict[int, np.ndarray] = {}
    if df.empty:
        return out
    yr = df[df["year"] == year]
    for plant_id, sub in yr.groupby("plant_id", observed=True):
        series = np.zeros(hours, dtype=float)
        hoy = sub["hour_of_year"].to_numpy()
        # NaN gross == an offline unit-hour (CAMPD writes NaN, not 0, for a
        # non-operating unit on the *unit*-level extracts). It must be treated
        # as zero MW BEFORE accumulation: np.add.at propagates NaN, so a single
        # offline unit at a multi-unit plant would poison the whole hour, and
        # the NaN then vanishes downstream (groupby.sum skips it, the bundle's
        # nan_to_num floors it to 0) — silently dropping every hour any unit was
        # down. That undercounts multi-unit coal plants ~2x (e.g. PJM Gavin,
        # Amos, Cardinal on the OH/WV/IN unit-level files), wrecking the per-
        # class CAMPD r / NRMSE. Facility-level ISOs (ERCOT) pre-sum units so
        # never hit it; nansum at the annual aggregates already did the same.
        gross = np.nan_to_num(sub["gross_mw"].to_numpy(), nan=0.0)
        valid = (hoy >= 0) & (hoy < hours)
        np.add.at(series, hoy[valid], gross[valid])
        out[int(plant_id)] = series * float(factors.get(int(plant_id), 1.0))
    return out


def plant_group_hourly_net(
    df: pd.DataFrame,
    factors: dict[int, float],
    year: int,
    group_of: Callable[[int, str, str], str | None],
    hours: int = HOURS_PER_YEAR,
) -> dict[tuple[int, str], np.ndarray]:
    """Return per-``(plant, model group)`` 8760-hour **net** series for a year.

    The per-unit analogue of :func:`plant_hourly_net`. That function sums a
    plant's units into ONE facility series, which the callers then attribute
    wholesale to a single model bin — correct at a single-bin plant and wrong
    at a mixed one, where it hands one bin the whole facility's conduct (the
    nyiso-175 §4.4 object: 13.76 TWh across six NYISO plants, decided at East
    River by a 3.5 MW nameplate margin). Here each unit's gross is routed by
    ``group_of`` to the bin that actually contains it, so a mixed plant's bins
    each get their own measured series over their own denominator.

    Args:
        df: A frame from :func:`load_campd_hourly` **on the raw path** — it
            must carry ``unit_id`` / ``unit_type``.
        factors: ``{plant_id: parasitic_factor}`` (net/gross).
        year: Calendar year to extract.
        group_of: ``(plant_id, unit_id, unit_type) -> model group or None``.
            A unit mapped to ``None`` is dropped. The caller owns the crosswalk
            (and the decision of what to do with a unit whose family the plant
            carries no bin for), so nothing here needs to know about classes.
        hours: Length of the output series.

    Returns:
        ``{(plant_id, group): (hours,) net MW}``.

    Raises:
        ValueError: When ``df`` lacks unit identity. This is deliberate: the
            curated ``emissions`` clean datatype does not carry ``unitId`` /
            ``unitType``, so under ``MARKET_SIM_USE_CLEAN`` a silent fallback
            to facility attribution would reinstate exactly the defect this
            function exists to repair, and would do it invisibly.
    """
    out: dict[tuple[int, str], np.ndarray] = {}
    if df.empty:
        return out
    missing = {"unit_id", "unit_type"} - set(df.columns)
    if missing:
        raise ValueError(
            "plant_group_hourly_net needs per-unit identity but the frame is "
            f"missing {sorted(missing)}. The curated 'emissions' clean datatype "
            "does not carry unit identity, so this attribution cannot be built "
            "under MARKET_SIM_USE_CLEAN — use the raw CAMPD path."
        )
    if not (df["unit_id"].astype(str).str.len() > 0).any():
        # The columns exist but every row is blank: this is a FACILITY-level
        # extract, whose units the publisher already summed away. Loading it
        # here would silently reproduce facility attribution under a per-unit
        # name — the exact defect this function repairs, invisible. Callers
        # must request the unit-level extract explicitly
        # (``load_campd_hourly(..., prefer_unit_level=True)``).
        raise ValueError(
            "plant_group_hourly_net was given a FACILITY-level CAMPD frame "
            "(unit_id blank on every row), in which per-unit identity has "
            "already been summed away. Per-unit attribution is impossible on "
            "it; load with prefer_unit_level=True."
        )
    yr = df[df["year"] == year]
    for (plant_id, unit_id, unit_type), sub in yr.groupby(
        ["plant_id", "unit_id", "unit_type"], observed=True
    ):
        group = group_of(int(plant_id), str(unit_id), str(unit_type))
        if not group:
            continue
        key = (int(plant_id), str(group))
        series = out.get(key)
        if series is None:
            series = np.zeros(hours, dtype=float)
            out[key] = series
        hoy = sub["hour_of_year"].to_numpy()
        # NaN gross == an offline unit-hour: CAMPD writes NaN, not 0, for a
        # non-operating unit on the unit-level extracts (52 % of NY CC
        # unit-hours in 2025). It MUST be zeroed before accumulation because
        # np.add.at PROPAGATES NaN — the same trap plant_hourly_net documents.
        gross = np.nan_to_num(sub["gross_mw"].to_numpy(), nan=0.0)
        valid = (hoy >= 0) & (hoy < hours)
        np.add.at(series, hoy[valid], gross[valid])
    factor_by_plant = {k: float(v) for k, v in factors.items()}
    return {
        (code, group): series * factor_by_plant.get(code, 1.0)
        for (code, group), series in out.items()
    }


def coal_share_by_plant(
    generation: pd.DataFrame, years: list[int] | None = None
) -> dict[int, float]:
    """Return ``{plant_id: coal share of net generation}`` from EIA-923.

    The share flags plants whose facility-level CEMS gross blends coal and gas
    units: a plant with ``0.1 < coal_share < 0.9`` cannot have a single
    facility emission rate cleanly assigned to its (separate) coal and gas
    dispatch bins. Plants near 0 or 1 burn effectively one fuel.

    Args:
        generation: The EIA-923 Page-1 frame.
        years: Optional subset of years to pool; ``None`` uses all.

    Returns:
        ``{plant_id: coal_share}`` for every plant with positive generation.
    """
    g = generation if years is None else generation[generation["year"].isin(years)]
    is_coal = g["fuel_type"].astype(str).str.upper().isin(_COAL_EIA_FUELS)
    total = g.groupby("plant_id")["netgen_annual_mwh"].sum()
    coal = (
        g[is_coal]
        .groupby("plant_id")["netgen_annual_mwh"]
        .sum()
        .reindex(total.index)
        .fillna(0.0)
    )
    return {int(p): float(coal[p] / total[p]) for p in total.index if total[p] > 0}


def eia923_combustion_net(generation: pd.DataFrame) -> pd.DataFrame:
    """Return EIA-923 net generation summed over combustion units per plant.

    Filters out non-stack-monitored fuels (renewables, nuclear, hydro,
    storage; see :data:`_NON_COMBUSTION_FUELS`) so the net generation lines
    up with what CAMPD's gross output covers, then sums over the plant's
    prime movers and fuels.

    Args:
        generation: The EIA-923 Page-1 frame from
            :func:`market_sim.data.eia923.load_monthly_generation`.

    Returns:
        Columns ``plant_id``, ``year``, ``net_mwh``.
    """
    fuels = generation["fuel_type"].astype(str).str.upper()
    combustion = generation[~fuels.isin(_NON_COMBUSTION_FUELS)]
    out = (
        combustion.groupby(["plant_id", "year"], observed=True)["netgen_annual_mwh"]
        .sum()
        .rename("net_mwh")
        .reset_index()
    )
    out["plant_id"] = out["plant_id"].astype(int)
    out["year"] = out["year"].astype(int)
    return out


# --- heat-input -> MWh proxy for grossLoad-blank coal units ------------------
# CAMPD's ``grossLoad`` column is NaN for circulating-fluidized-bed, waste-coal
# (culm) and industrial-cogen coal units (Virginia City 56808, Seward 3130, the
# PA culm fleet, Eastman 50481, ...): they report ``heatInput`` + ``steamLoad``
# instead. A grossLoad-based hourly series therefore treats them as offline all
# year. :func:`fill_heatinput_proxy` reconstructs their hourly **net** MW from
# the measured heat input and a per-plant effective heat rate anchored to
# EIA-923 net generation — the LEVEL comes from the measured EIA-923 netgen, the
# SHAPE from the measured hourly heatInput, nothing from the MWh/LMP residual.
#
# Twelve calendar-month EIA-923 net-generation column names (the monthly-survey
# release used to anchor the proxy LEVEL and gate its reconciliation). Kept
# local so this module does not depend on :mod:`market_sim.data.eia923`.
_EIA923_MONTH_COLUMNS: tuple[str, ...] = (
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
)
# A reconstructed plant is accepted only when its CAMPD-heat-derived monthly MWh
# tracks the EIA-923 monthly netgen to within this net-generation-weighted mean
# absolute error. Plants where the CAMPD stack only partially covers the plant's
# generation (e.g. Eastman: CAMPD heat present May-Sep only against year-round
# EIA-923 netgen) blow past this and are left blank (offline, as before) rather
# than reconstructed wrong.
HEATPROXY_RECONCILE_TOL: float = 0.15
# Effective heat rate must be physically plausible (MMBtu per net MWh). A CFB or
# steam-extraction cogen runs high (Virginia City 11.4, St Nicholas 15.8); below
# ~6 or above ~40 the EIA-923 netgen and CAMPD heat cover different unit sets and
# the plant is not reconstructed.
_HEATPROXY_HR_MIN: float = 6.0
_HEATPROXY_HR_MAX: float = 40.0
# Scope guard: the proxy targets grossLoad-blank COAL units (CFB / waste-coal /
# coal cogen). A plant must burn at least this share of coal (of its EIA-923
# combustion netgen) to be reconstructed — biomass (WDS) cogens, refinery /
# petcoke units and other heat-only industrial generators are left blank.
_HEATPROXY_COAL_MIN: float = 0.50


def _eia923_combustion_annual_by_plant(
    eia_monthly: pd.DataFrame, year: int
) -> "pd.Series":
    """Annual EIA-923 combustion net generation (MWh) per plant for ``year``.

    Sums ``netgen_annual_mwh`` over the plant's stack-monitored combustion fuels
    (drops :data:`_NON_COMBUSTION_FUELS`), so the numerator of the proxy heat
    rate matches what CAMPD's heat input covers.
    """
    df = eia_monthly[eia_monthly["year"] == year]
    fuels = df["fuel_type"].astype(str).str.upper()
    df = df[~fuels.isin(_NON_COMBUSTION_FUELS)]
    return df.groupby("plant_id")["netgen_annual_mwh"].sum()


def _eia923_coal_share_by_plant(eia_monthly: pd.DataFrame, year: int) -> "pd.Series":
    """Coal share of EIA-923 combustion net generation per plant for ``year``.

    Coal-fuel (:data:`_COAL_EIA_FUELS`) netgen over total combustion netgen —
    the scope guard that keeps the heat-input proxy on coal units.
    """
    df = eia_monthly[eia_monthly["year"] == year]
    fuels = df["fuel_type"].astype(str).str.upper()
    combustion = df[~fuels.isin(_NON_COMBUSTION_FUELS)]
    total = combustion.groupby("plant_id")["netgen_annual_mwh"].sum()
    is_coal = combustion["fuel_type"].astype(str).str.upper().isin(_COAL_EIA_FUELS)
    coal = (
        combustion[is_coal]
        .groupby("plant_id")["netgen_annual_mwh"]
        .sum()
        .reindex(total.index)
        .fillna(0.0)
    )
    return (coal / total.where(total != 0.0)).fillna(0.0)


def _eia923_combustion_monthly_by_plant(
    eia_monthly: pd.DataFrame, year: int
) -> pd.DataFrame:
    """Monthly EIA-923 combustion net generation per plant, indexed by plant.

    Columns are 1-based calendar months of combustion-fuel netgen for ``year``
    — the reconciliation target for the monthly proxy gate.
    """
    df = eia_monthly[eia_monthly["year"] == year]
    fuels = df["fuel_type"].astype(str).str.upper()
    df = df[~fuels.isin(_NON_COMBUSTION_FUELS)]
    have = [c for c in _EIA923_MONTH_COLUMNS if c in df.columns]
    monthly = df.groupby("plant_id")[have].sum()
    monthly.columns = [i + 1 for i, c in enumerate(_EIA923_MONTH_COLUMNS) if c in have]
    return monthly


def heatinput_proxy_report(
    df: pd.DataFrame,
    eia_monthly: pd.DataFrame,
    year: int,
) -> pd.DataFrame:
    """Per-plant reconciliation of the heat-input -> MWh proxy for ``year``.

    For every plant that reports ``heatInput`` but no ``grossLoad`` for any
    hour, computes the effective heat rate (annual EIA-923 combustion netgen /
    annual CAMPD heat), reconstructs the monthly MWh (annual HR applied to each
    month's measured heat), and scores it against the EIA-923 monthly netgen.

    Returns one row per candidate plant: ``plant_id``, ``net_mwh`` (EIA-923
    annual combustion), ``heat_mmbtu`` (CAMPD annual), ``heat_rate``
    (MMBtu/MWh), ``recon_wmae`` (net-generation-weighted mean absolute monthly
    error), ``accepted`` (heat rate in band and ``recon_wmae`` within
    :data:`HEATPROXY_RECONCILE_TOL`) and ``facility_name``. The gate /
    diagnostic; :func:`fill_heatinput_proxy` applies exactly the accepted rows.
    """
    cols = [
        "plant_id",
        "net_mwh",
        "heat_mmbtu",
        "heat_rate",
        "coal_share",
        "recon_wmae",
        "accepted",
        "facility_name",
    ]
    if df.empty:
        return pd.DataFrame(columns=cols)
    yr = df[df["year"] == year]
    net_annual = _eia923_combustion_annual_by_plant(eia_monthly, year)
    net_monthly = _eia923_combustion_monthly_by_plant(eia_monthly, year)
    coal_share = _eia923_coal_share_by_plant(eia_monthly, year)
    rows: list[dict] = []
    for plant_id, sub in yr.groupby("plant_id", observed=True):
        gross = sub["gross_mw"].to_numpy()
        heat = sub["heat_mmbtu"].to_numpy()
        # Candidate = reports heat but never gross (the grossLoad-blank fleet).
        if np.isfinite(gross).any() or not np.nansum(heat) > 0.0:
            continue
        pid = int(plant_id)
        heat_annual = float(np.nansum(heat))
        net_mwh = float(net_annual.get(pid, 0.0))
        share = float(coal_share.get(pid, 0.0))
        hr = heat_annual / net_mwh if net_mwh > 0.0 else float("nan")
        # Monthly reconciliation: reconstructed month MWh = month heat / HR.
        months = pd.to_datetime(sub["date"]).dt.month.to_numpy()
        heat_by_month = pd.Series(heat, dtype=float).groupby(months).sum()
        recon_wmae = float("nan")
        if pid in net_monthly.index and np.isfinite(hr) and hr > 0.0:
            tgt = net_monthly.loc[pid]
            num = denom = 0.0
            for m in range(1, 13):
                net_m = float(tgt.get(m, 0.0))
                recon_m = float(heat_by_month.get(m, 0.0)) / hr
                num += abs(recon_m - net_m)
                denom += abs(net_m)
            recon_wmae = num / denom if denom > 0.0 else float("nan")
        accepted = bool(
            np.isfinite(hr)
            and _HEATPROXY_HR_MIN <= hr <= _HEATPROXY_HR_MAX
            and share >= _HEATPROXY_COAL_MIN
            and np.isfinite(recon_wmae)
            and recon_wmae <= HEATPROXY_RECONCILE_TOL
        )
        rows.append(
            {
                "plant_id": pid,
                "net_mwh": round(net_mwh, 1),
                "heat_mmbtu": round(heat_annual, 1),
                "heat_rate": round(hr, 3) if np.isfinite(hr) else float("nan"),
                "coal_share": round(share, 3),
                "recon_wmae": round(recon_wmae, 4)
                if np.isfinite(recon_wmae)
                else float("nan"),
                "accepted": accepted,
                "facility_name": str(sub["facility_name"].iloc[0]),
            }
        )
    return pd.DataFrame(rows, columns=cols)


def fill_heatinput_proxy(
    df: pd.DataFrame,
    eia_monthly: pd.DataFrame,
    year: int,
) -> tuple[pd.DataFrame, set[int]]:
    """Fill ``gross_mw`` for grossLoad-blank coal units from measured heat input.

    Where a plant reports ``heatInput`` but never ``grossLoad`` and reconciles
    to EIA-923 (see :func:`heatinput_proxy_report`), each blank-``gross_mw`` hour
    is filled with ``heat_mmbtu / HR`` — the measured hourly heat shape scaled by
    the plant's measured effective heat rate. Because ``HR`` is anchored to
    EIA-923 **net** generation, the reconstructed series is already net, so the
    caller must treat these plants with a parasitic factor of 1.0 (the returned
    plant-id set flags them). A ``mw_source`` column is added to the whole frame
    so downstream can tell measured MW (``"measured"``) from heat-derived MW
    (``"heat_proxy"``). Rows that already carry ``grossLoad`` are byte-identical.

    Returns ``(filled_df, proxy_plant_ids)``. When no plant qualifies the frame
    is returned with only the ``mw_source`` column added (all ``"measured"``).
    """
    out = df.copy()
    out["mw_source"] = "measured"
    if out.empty:
        return out, set()
    report = heatinput_proxy_report(out, eia_monthly, year)
    accepted = report[report["accepted"]] if not report.empty else report
    proxy_ids: set[int] = set()
    if accepted.empty:
        return out, proxy_ids
    hr_by_plant = dict(zip(accepted["plant_id"].astype(int), accepted["heat_rate"]))
    is_year = out["year"] == year
    for pid, hr in hr_by_plant.items():
        if not (hr and hr > 0.0):
            continue
        mask = (
            is_year
            & (out["plant_id"] == pid)
            & out["gross_mw"].isna()
            & (out["heat_mmbtu"].fillna(0.0) > 0.0)
        )
        if not mask.any():
            continue
        out.loc[mask, "gross_mw"] = out.loc[mask, "heat_mmbtu"] / float(hr)
        out.loc[mask, "mw_source"] = "heat_proxy"
        proxy_ids.add(int(pid))
    if proxy_ids:
        logger.info(
            "CAMPD %d: heat-input MWh proxy applied to %d grossLoad-blank "
            "coal plant(s): %s",
            year,
            len(proxy_ids),
            sorted(proxy_ids),
        )
    return out, proxy_ids
