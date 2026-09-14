"""Renewable resource profiles (wind and solar capacity factors).

Derives hourly capacity-factor (CF) profiles for wind and solar from the
EIA-930 normalized generation distributions. The EIA ``value`` column for a
given ``(iso, year, fuel)`` group is a probability distribution that sums to
roughly 1.0 across the 8760 hours of the year; multiplying by the fleet's
annual-average CF and by the hour count rescales it into an hourly CF series
whose mean equals that annual-average CF.

Because the EIA generation series reflect *delivered* output, they already
embed real-world curtailment (roughly 5% for wind and solar in ERCOT and
CAISO), so for most ISO-years the derived CF profiles inherit that
curtailment and the dispatch does not separately re-curtail.

The exceptions are the backcasts with an hourly uncurtailed-potential (HSL)
dataset, where the CF profile is built from that instead (see
:func:`_hsl_cf_profile`) so the dispatch is handed the *uncurtailed*
potential and re-curtails wind and solar under the modeled transmission
limits, and the calibration report can compare the modeled curtailment
against the reported ``HSL - GEN``:

* ERCOT 2023/2024/2025 — all three buildable backcast years now carry a built
  HSL parquet (scripts/data/build_ercot_hsl.py; 2023 from the UMass 60-Day-SCED
  dataset, 2024/2025 from ERCOT's own published NP6 wind/solar production
  reports, landed 2026-07-06 — see data/raw/ercot-hsl/np6/README.md);
* CAISO 2023/2024/2025 (plus 2019-2021) — EIA-930 delivered generation plus
  CAISO's reported 5-minute wind/solar curtailment (scripts/data/build_caiso_hsl.py).
  CAISO solar curtailment is multi-TWh, so without this the model cannot re-curtail.

For a **high-curtailment ISO-year-tech with no HSL parquet** (any future ERCOT
year without an NP6 upload; MISO wind, which has no hourly series at all — see
:data:`_UNCURTAILED_FALLBACK_ISOS`), the dispatch is instead handed a
**forecast uncurtailed CF**: the EIA-930 weather-year delivered profile (its
real level and shape) grossed up by the per-tech *reference curtailment rate*
from a *different* source year — an HSL year (ERCOT/CAISO) or the Potomac
Economics measured annual wind curtailment rate (MISO) — via
:func:`_forecast_uncurtailed_cf`, *not* the delivered net-of-curtailment series
consumed as the upper bound. The LP then curtails endogenously and the
modeled-vs-reported curtailment gap is a diagnostic, never a fit target
(CLAUDE.md #11). The reference rate comes from a *different* year, so the
potential is never scaled so the target year's delivered output lands on
actuals.

All other ISOs use the delivered ``<BA> hourly`` net-generation series from
the EIA-930 hourly extract (see :func:`_eia_hourly_cf_profile`).  For NEISO
in particular, ISO-NE reported curtailment is sub-1 % of potential, so the
delivered EIA-930 ``ISNE hourly`` series is the documented default and no
uncurtailed-potential (HSL) parquet is built.  NEISO wind/solar profiles are
zone-shaped by EIA-860 plant-location capacity shares: ME/NH/VT onshore wind
concentrates in the North zone; CT and MA/RI utility solar distribute across
Connecticut and Central.

**NEISO solar accounting note** — ISO-NE's extensive net-metered solar
(rooftop + small commercial) is reported as a *reduction in net load* rather
than as explicit generation, so the EIA-930 ``ISNE hourly NG: SUN`` column
captures only grid-scale wholesale solar (~800–1 600 GWh/yr) while the
EIA-860 operable schedule includes all utility-scale plants ≥ 1 MW
(including distribution-connected, ~2.7 GW in 2023).  As a result the
mean CF of the EIA-930-derived solar profile relative to the EIA-860 total
installed capacity is approximately 0.04 — well below the physical
utility-PV CF of ~0.15 — but the dispatch energy balance is correct because
the EIA-930 net-load demand series already excludes BTM solar.  The wind
profile is unaffected (all NEISO wind is grid-connected), and its mean CF
benchmarks against the EIA-923 fleet average (~0.30).

If ISO-NE ever publishes granular curtailment data, a dedicated HSL parquet
can be built following the CAISO pattern in scripts/data/build_caiso_hsl.py — see
:func:`_hsl_file` for the data-needed marker.

NYISO wind and solar curtailment is modest and NYISO does not publish an
hourly uncurtailed-potential (or hourly curtailment) series comparable to
CAISO's 5-minute Production-and-Curtailment workbooks or ERCOT NP6 — only
annual + monthly + zonal *aggregate* estimates in its annual "NYCA
Renewables" presentation (nyiso.com/reports-information, "Real-Time Market
Curtailments"): NYCA wind curtailment was 66.6 GWh (1.1% of production) in
2024 and 76.6 GWh (1.1%) in 2025 (3.4% in 2023); FTM solar was 1.04 GWh
(0.2%) in 2024 and 20.18 GWh (2.1%) in 2025 (checked 2026-07-05; NYISO
re-examined as its own uncurtailed-basis decision 2026-07-21, see
docs/multi-iso/nyiso-uncurtailed-hsl-finding-2026-07.md). NYISO is a
**deliberate genuine-gap decision**, not merely a missing upload: the
documented default for NYISO backcasts remains the EIA-930 NYIS
delivered-generation series and NYISO stays OUT of
:data:`_UNCURTAILED_FALLBACK_ISOS` for two reasons sharper than "no hourly
series" (the reference-rate gross-up MISO wind takes needs only an annual
RATE, and the NYCA-wide annual wind % printed in the deck — ~1.9% mean over
2023-2025 — *would* technically supply one, so granularity alone is not the
bar):

1. **Immaterial magnitude.** ~1.1% of wind production (well under 1 TWh/yr)
   sits below the threshold where explicit re-curtailment moves dispatch.
   MISO qualifies at ~4.9% / multi-TWh (see above); NYISO does not.
2. **Driver misaligned to the reduced network (CLAUDE.md #12 exception).**
   NYISO's wind curtailment is dominated by North/Central Zone *local*
   transmission-upgrade outages — North+Central is 72-93% of zonal
   curtailment every reported year (2020 North alone = 85%), and the 2021
   deck annotates North curtailment as "coincident with several long-term
   facility outages related to transmission upgrades." That is a sub-zonal
   physical event the reduced 5-zone NYISO network does not represent, so
   grossing the delivered NYIS shape up by a uniform ~1% would hand the LP
   headroom it cannot endogenously re-curtail — phantom wind energy that
   makes results *less* reflective of reality. The NYCA-wide rate is a real
   number but the wrong instrument for a locally-driven, immaterial
   curtailment; using it literally would be the #12 "misaligned to our
   representation" failure, not an improvement over the measured delivered
   series.

Zone-shaping uses EIA-860 capacity shares: upstate NY counties (zones A–E)
hold the bulk of wind capacity, and solar spreads across upstate and
downstate zones.

MISO, by contrast, IS a fallback ISO for wind: MISO's IMM (Potomac Economics)
publishes measured annual/quarterly wind curtailment in its State-of-the-Market
reports — multi-TWh/yr (~4.9% of potential, ~500-660 MW average) — reachable
where misoenergy.org's hourly workbooks are allowlist-blocked. That aggregate is
also too coarse for an hourly HSL parquet, but it is enough for a measured
per-tech reference curtailment RATE, so MISO wind takes the forecast-uncurtailed
reference-rate gross-up (:func:`_miso_wind_reference_curtailment_rate`,
:func:`_forecast_uncurtailed_cf`). MISO solar has no published curtailment
series and keeps the delivered profile.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    HOURS_PER_YEAR,
    OFFSHORE_WIND_MIN_CF,
    OFFSHORE_WIND_PARAMS,
    OFFSHORE_WIND_SMOOTHING_HOURS,
    RENEWABLE_AVG_CF,
    RENEWABLE_INSTALLED_MW,
)
from market_sim.config.iso_configs import ISOConfig, get_iso_config
from market_sim.config.paths import (
    CAISO_HSL_DIR,
    ERCOT_HSL_DIR,
    MISO_HSL_DIR,
    NYISO_HSL_DIR,
    SPP_HSL_DIR,
    wind_shape_dir,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.cod_ramp import COD_FALLBACK_MONTH, monthly_online_mask
from market_sim.data.nyiso_market_solar import load_market_solar_monthly
from market_sim.data.eia_loader import (
    DATA_DIR,
    load_eia_hourly_renewable_gen,
    load_generation_profiles,
)
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    FleetArrays,
    _hour_to_month_index,
    operable_vintage_year as _operable_vintage_year,
)

logger = logging.getLogger(__name__)

# Capacity factors are physically bounded to the closed interval [0, 1].
# Bisection steps for the oversupply curtailment water-fill
# (:func:`_oversupply_curtailment_allocation`). The bracket is the net-load
# range (order 1e4 MW), so 200 halvings drive it far below float resolution --
# the annual-energy identity reproduces to machine precision. Not a tunable:
# any value that converges gives the same level.
_WATER_FILL_ITERS: int = 200

_CF_MIN: float = 0.0
_CF_MAX: float = 1.0

# Headroom epsilon (MW) for the capacity-aware per-zone redistribution: a zone
# whose allocation is within this of its online MW is treated as saturated and
# drops out of the next spill pass (see :func:`_redistribute_preserving_total`).
_REDISTRIBUTE_MW_EPS: float = 1.0e-6

# Renewable fuels for which CF profiles are derived, matching the ``fuel``
# values in the EIA-930 generation-profiles parquet.
_RENEWABLE_FUELS: tuple[str, str] = ("wind", "solar")

# ISOs whose reported wind/solar curtailment is material (multi-TWh/yr) so the
# dispatch must re-curtail an *uncurtailed* potential rather than inherit the
# curtailment baked into EIA-930 delivered output. For a backcast year these
# prefer a built HSL parquet (ERCOT NP6 all three years; CAISO
# delivered+reported-curtailment); when none covers the ISO-year-tech they fall
# back to the per-tech reference-rate gross-up (EIA-930 weather-year delivered
# shape ÷ (1 − reference curtailment rate)) — NOT the delivered
# net-of-curtailment series — so the LP still curtails endogenously and responds
# to changed build. The reference rate is a measured curtailment rate from a
# *different* source year (:func:`_reference_curtailment_rate`): a recent HSL
# year for ERCOT/CAISO, or — for MISO, which publishes no hourly HSL series —
# the Potomac Economics (MISO IMM) measured annual wind curtailment rate
# (:func:`_miso_wind_reference_curtailment_rate`). MISO qualifies because its
# wind curtailment is multi-TWh/yr (~4.9% of potential, ~500-660 MW average per
# the IMM's SOM reports); MISO solar has no published curtailment series so it
# stays on the delivered profile. Every ISO NOT listed keeps the delivered
# EIA-930 profile as its documented fallback — NYISO and NEISO curtailment is
# sub-1%/yr (below where explicit re-curtailment moves dispatch) and neither
# publishes a series granular enough to derive a rate from. The
# modeled-vs-reported curtailment gap is a diagnostic, never a fit target
# (CLAUDE.md #11).
#
# SPP joins on the same footing as MISO and for the same reason, only more so
# (SPP-32, 2026-09-07): SPP publishes no hourly HSL series either, but its MMU
# publishes an average hourly wind-curtailment MW in every Annual State of the
# Market report, and SPP's own 5-minute metered generation mix supplies the
# delivered leg — so BOTH legs of the rate are measured, from two independent
# SPP publications (:func:`_spp_wind_reference_curtailment_rate`). The measured
# 2023-2025 rate is ~9.7% of potential (~12 TWh/yr, ~1.1-1.5 GW hourly average),
# roughly twice MISO's ~4.9%, which is far past where explicit re-curtailment
# moves dispatch. SPP solar is ~0.73% of SPP's curtailment (ASOM 2025 p. 54) and
# has no separable published series, so SPP solar keeps the delivered profile
# exactly as MISO solar does.
_UNCURTAILED_FALLBACK_ISOS: frozenset[str] = frozenset(
    # NWPP (registered 2026-09-14, lane NWPP-20): no pool publishes a
    # separable curtailment series for this footprint (BPA's oversupply
    # curtailment is a BPAT-internal accounting, not a footprint HSL), so
    # NWPP wind and solar keep the delivered EIA-930 profile exactly as SPP
    # solar and MISO solar do.
    {"ERCOT", "CAISO", "MISO", "SPP", "NWPP"}
)

# Years probed (newest first) for an HSL-covered reference year when grossing a
# no-HSL year's delivered profile up to an uncurtailed potential (see
# :func:`_reference_curtailment_rate`). The most recent year with a built HSL
# parquet supplies the per-tech reference curtailment rate; the list extends
# automatically as new HSL years are added.
_REFERENCE_HSL_YEARS: tuple[int, ...] = (2025, 2024, 2023, 2022, 2021)

# Fallback single-zone allocation, by ISO and fuel. Used only when EIA-860
# plant-location data is unavailable for the ISO; otherwise capacity is
# distributed across zones from EIA-860 (see :func:`_eia860_zone_shares`).
# Each technology is assigned to the zone holding the bulk of its installed
# capacity; every other zone receives an all-zero profile.
# Source: ERCOT CDR Dec 2024 (West Texas wind/solar belt; offshore wind off
# the Houston/Galveston coast). CAISO zones follow the EIA-860 capacity
# distribution: onshore wind concentrates in ZP26 (the Tehachapi/Kern belt,
# ~52% of CISO wind), solar in SP15 (the southern desert, ~63% of CISO
# solar), and the BOEM offshore-wind lease areas (Morro Bay / Humboldt) sit
# on the NP15 coast.
RENEWABLE_ZONE_ALLOCATION: dict[str, dict[str, str]] = {
    "ERCOT": {"wind": "West", "solar": "West", "offshore_wind": "Houston"},
    "CAISO": {
        "wind": "ZP26",
        # Fallback only — the primary path sites solar by plant coordinates;
        # SP15 was split into LA_BASIN/SDGE/SP15_rest (2026-07-09).
        "solar": "SP15_rest",
        "offshore_wind": "NP15",
    },
    # Eastern-ISO siting zones: Tier 3, the zone holding the bulk of each
    # technology's current fleet / pipeline. PJM wind sits in the western
    # (ComEd, IL/IN belt) zone, PJM solar in Dominion (the VA build wave),
    # PJM offshore off the NJ coast (EMAAC). MISO wind is the MN/Dakotas
    # belt (West — the EIA-860 split lands 13.8 GW in Plains / 9.7 GW in
    # West, both wind-belt zones; West per the zonal-refinement scope) and
    # MISO solar is southern-weighted (South 4.8 GW is the largest EIA-860
    # zone). NYISO utility wind/solar
    # are upstate-west; offshore is the NY Bight off Long Island. NEISO
    # wind is Maine (North), solar CT, offshore the MA/RI lease areas.
    "PJM": {
        "wind": "PJM_ComEd",
        "solar": "PJM_Dominion",
        "offshore_wind": "PJM_EMAAC",
    },
    "MISO": {"wind": "MISO-West", "solar": "MISO-South"},
    "NYISO": {
        "wind": "Upstate_West",
        "solar": "Upstate_West",
        "offshore_wind": "Long_Island",
    },
    "NEISO": {
        "wind": "North",
        "solar": "Connecticut",
        "offshore_wind": "Boston",
    },
    # SPP (registered 2026-09-06, lane SPP-20): Tier 3, the zone holding the
    # bulk of each technology's EIA-860 2025 ER operable fleet under the P1
    # state map. Wind is nearly EVEN across the seam (North 17,664.3 MW vs
    # South 17,809.1 MW; Oklahoma alone is 12,945.0 MW, the largest single
    # state) and solar leans South (840.7 vs 601.1 MW; OK 423.5 / NM 279.5),
    # so both default to SPP-South. Fallback only — the primary path
    # distributes by plant coordinates (_eia860_zone_shares). No
    # ``offshore_wind`` key: the footprint is landlocked.
    "SPP": {"wind": "SPP-South", "solar": "SPP-South"},
    # NWPP (registered 2026-09-14, lane NWPP-20): fallback only — the primary
    # path distributes by each plant's balancing authority through the
    # BA-keyed zone lookup (zone_assignment._NWPP_BA_ZONES). Measured on the
    # EIA-860 2025 ER WECC-admitted footprint (PRECOMMIT-nwpp-20 §3.7): wind
    # NW 6,381.4 / EAST 4,574.8 / INLAND 2,147.7 / OR 1,206.4 / SNV 150.0 MW
    # of 14,460.3, so wind defaults to NWPP-NW; solar PV SNV 4,175.0 / EAST
    # 3,047.9 / INLAND 1,061.1 / NW 772.9 / OR 694.4 of 9,751.3, so solar
    # defaults to NWPP-SNV. No ``offshore_wind`` key: none in the footprint.
    "NWPP": {"wind": "NWPP-NW", "solar": "NWPP-SNV"},
}

# EIA-860 operable wind/solar generator parquets, used to distribute
# renewable capacity across ISO zones and to build the vintage monthly
# capacity ramp from each plant's commercial-operation date.
# Source: EIA-860 2024 (Generator_Operable, wind and solar schedules).
_EIA860_OPERABLE_FILES: dict[str, str] = {
    "wind": "eia860_wind_operable.parquet",
    "solar": "eia860_solar_operable.parquet",
}

# Proposed-plant file with planned commercial-operation dates. Used to
# include future-year wind/solar additions that are not yet in the
# operable schedule (e.g. 2025 plants not present in the Sep-2024
# operable snapshot). Filtered to high-confidence statuses below.
_EIA860_PROPOSED_FILE: str = "eia860_generator_proposed.parquet"

# EIA-860 status codes treated as high-confidence (likely to come online
# by the planned effective date). ``U`` / ``V`` are under construction
# (<50% / >50% complete), ``TS`` is test-mode pre-commercial, ``P`` is
# planned-with-permits. ``L`` (regulatory approvals only) and ``T``
# (regulatory pending) are excluded as paper-only proposals.
_PROPOSED_HIGH_CONFIDENCE: frozenset[str] = frozenset({"U", "V", "TS", "P"})

# Year the operable EIA-860 snapshot was last refreshed; proposed plants
# with an ``Effective Year`` strictly greater than this are pulled in as
# augmentations to the operable schedule. Single source of truth lives in
# data/fleet.py next to the thermal planned-additions loader. Resolved
# per-call from the ACTIVE snapshot dir (vintage-aware, FH-1 leak fix) so a
# vintage-seeded run augments from ITS OWN proposed sheet; the top-level
# snapshot resolves to the canonical constant, byte-identical.

_TECHNOLOGY_TO_FUEL: dict[str, str] = {
    "Solar Photovoltaic": "solar",
    "Onshore Wind Turbine": "wind",
}

# Home-state filter for proposed-plant augmentation. The lat/lon zone
# rules in :mod:`market_sim.data.zone_assignment` will happily assign
# any point in the country to one of the ISO's zones; the state
# allowlist is what actually bounds the proposed-plant pool to the
# ISO's geographic footprint. Only ISOs listed here support the
# augmentation; others fall back to the operable schedule only.
_ISO_HOME_STATES: dict[str, frozenset[str]] = {
    "ERCOT": frozenset({"TX"}),
}

_MONTHS_PER_YEAR: int = 12

# ISOs whose solar capacity is spread across geographically distinct zones
# with materially different tracking mixes, so a single ISO-wide hourly solar
# SHAPE applied to every zone is wrong (see :func:`_solar_zone_clearsky_shapes`
# and the CAISO NP15/ZP26/SP15 spread documented there). Gated per ISO so the
# per-zone redistribution cannot move any other ISO's derived outputs; every
# ISO not listed keeps the legacy single-shape behaviour.
_SOLAR_ZONE_SHAPE_ISOS: frozenset[str] = frozenset({"CAISO"})

# ISOs whose WIND capacity spans regions with materially different wind regimes,
# so a single ISO-wide hourly wind SHAPE applied to every zone is wrong. MISO is
# the case: the upper-plains North (MN/ND/SD/IA) is driven by the nocturnal
# low-level jet — a pronounced overnight wind maximum — while the lower-Midwest
# Central and the Entergy South have a flatter, more afternoon-weighted regime,
# so North's diurnal/seasonal shape differs materially from Central/South's.
# Each listed ISO gets a per-zone wind SHAPE from MERRA-2 reanalysis wind speed
# at its EIA-860 wind-plant locations passed through a turbine power curve (see
# :func:`_wind_zone_reanalysis_shapes` and scripts/data/build_miso_wind_shape.py),
# reconciled to the measured EIA-930 ISO-wide series exactly (system total and
# annual energy unchanged — only the inter-zone split moves). Gated per ISO so
# the redistribution cannot touch any other ISO's outputs; ISOs not listed keep
# the legacy single-shape behaviour.
#
# SPP joins as a MEMBERSHIP, not a new gate (SPP-32, 2026-09-07): SPP has no
# keeper yet, so there is no calibrated run for a per-zone split to perturb, and
# adding a ``ScenarioConfig`` field for it would move all six existing keepers'
# cache keys for nothing (plan §7 gate G8). SPP qualifies on the same test MISO
# does — its 35.5 GW wind fleet splits 17.7/17.8 GW across the North/South seam
# and the two halves peak at DIFFERENT hours. Measured night(00-06)/afternoon
# (12-18) ratio, 2023/2024/2025: SPP-South 1.04/1.06/1.03 (overnight-weighted)
# vs SPP-North 0.97/0.96/0.91 (afternoon-weighted). Note the sign: in SPP the
# SOUTH is the nocturnal zone, because the Great-Plains low-level jet's core
# sits over Oklahoma / Kansas / the Texas Panhandle and weakens northward — the
# opposite of the MISO contrast a reader might carry across. Built by
# scripts/data/build_spp_wind_shape.py; data/raw/spp-wind-shape/README.md.
_WIND_ZONE_SHAPE_ISOS: frozenset[str] = frozenset({"MISO", "SPP"})

# ISOs whose per-zone wind SHAPE is available but KEEPER-AFFECTING, so it is
# armed by a named ScenarioConfig gate instead of unconditionally. ERCOT is the
# case (ERCOT-113): the West/Panhandle CREZ corridor rides the Great-Plains
# nocturnal low-level jet (measured night/afternoon ratio 1.16/1.15/1.13 for
# West, 1.04/1.13/1.06 for Panhandle) while the South/Coastal fleet rides the
# Gulf sea breeze and peaks in the afternoon (0.89/0.84/0.84) — one ISO-wide
# profile averages the two together, so the model holds wind in the wrong zone
# at the wrong hour and the West/Panhandle curtailment ceiling and the zonal
# links bind at the wrong times. Because
# :func:`_redistribute_preserving_total` preserves the ISO aggregate EXACTLY in
# every hour, arming this can never move annual wind energy or the ISO-wide
# bound — only WHICH ZONE holds the wind. Mapping is field name, not a bool, so
# every armed ISO's gate is visible in ``run_config.json`` (rule 20).
_WIND_ZONE_SHAPE_GATES: dict[str, str] = {"ERCOT": "ercot_wind_zone_shape"}


def _wind_zone_shape_enabled(iso: str, config: ScenarioConfig | None) -> bool:
    """Return whether ``iso`` gets a per-zone wind SHAPE for this config.

    An ISO in :data:`_WIND_ZONE_SHAPE_ISOS` is unconditional; an ISO in
    :data:`_WIND_ZONE_SHAPE_GATES` is armed only when its named
    ``ScenarioConfig`` field is true, so a keeper-affecting ISO stays off by
    default and an unarmed run is byte-identical to its pre-gate self.

    Args:
        iso: ISO identifier.
        config: Scenario config carrying the per-ISO gate, or ``None``.

    Returns:
        ``True`` when the per-zone wind SHAPE should be applied.
    """
    if iso in _WIND_ZONE_SHAPE_ISOS:
        return True
    field = _WIND_ZONE_SHAPE_GATES.get(iso)
    return bool(field) and bool(getattr(config, field, False))


# EIA-860 solar tracking-technology flag columns (Generator_Operable solar
# schedule), each a ``Y``/``N`` indicator. A plant's nameplate capacity is
# attributed to the first flag it sets; the per-zone capacity-weighted mix of
# these three classes drives that zone's clear-sky solar SHAPE.
# Source: EIA-860 2024, Solar_Operable sheet.
_SOLAR_TRACKING_FLAGS: tuple[str, str, str] = (
    "Single-Axis Tracking?",
    "Fixed Tilt?",
    "Dual-Axis Tracking?",
)

# --- Clear-sky solar geometry (numpy-only, reproducible astronomy) ----------
# Standard textbook solar-position and clear-sky formulae (Cooper declination,
# Meinel clear-sky beam attenuation, isotropic-sky transposition). These derive
# only the RELATIVE hourly SHAPE difference between zones with different
# tracking mixes — never the absolute energy level, which always comes from the
# measured EIA-930 cf_profile via the aggregate-reconciliation step in
# :func:`_distribute_by_eia860`. Forward-valid: the same geometry regenerates
# for any future year and responds to a changed tracking mix.
_DECLINATION_MAX_DEG: float = 23.45  # Earth axial tilt — Cooper declination model
_CLEARSKY_TRANSMITTANCE: float = 0.7  # Meinel sea-level clear-sky beam transmittance
_CLEARSKY_AM_EXPONENT: float = 0.678  # Meinel air-mass exponent (Kasten form)
_DIFFUSE_FRACTION: float = (
    0.10  # isotropic clear-sky diffuse as a fraction of beam-horizontal
)
_COS_ZENITH_FLOOR: float = 1.0e-3  # guards the 1/cos(zenith) air-mass at the horizon

# ERCOT uncurtailed renewable potential (High Sustained Limit), one parquet
# per backcast year (``ercot_<year>_hsl_hourly.parquet``). When a year's file
# is present, the ERCOT backcast builds its CF profiles from the hourly HSL
# series rather than from EIA-930 delivered generation, so the dispatch
# re-curtails under modeled transmission limits. Built by
# scripts/data/build_ercot_hsl.py (2023 from the UMass 60-Day-SCED dataset;
# 2024+ from uploaded ERCOT NP6 wind/solar production reports).
_ERCOT_HSL_DIR: Path = ERCOT_HSL_DIR

# Columns every per-year HSL parquet must carry (hourly MW series).
_HSL_COLUMNS: tuple[str, ...] = (
    "hour",
    "wind_gen_mw",
    "wind_hsl_mw",
    "solar_gen_mw",
    "solar_hsl_mw",
)

# CAISO uncurtailed renewable potential (the HSL analogue: EIA-930 delivered
# + CAISO's reported wind/solar curtailment), one parquet per covered year
# with the same schema as the ERCOT file. Built by scripts/data/build_caiso_hsl.py;
# a year without a full-year curtailment workbook has no parquet here and
# falls back to the delivered EIA-930 hourly profile.
_CAISO_HSL_DIR: Path = CAISO_HSL_DIR

# NYISO curtailment parquet directory (does not exist on disk — a deliberate
# genuine gap, not a pending upload; re-examined 2026-07-21, see
# docs/multi-iso/nyiso-uncurtailed-hsl-finding-2026-07.md). NYISO publishes only
# annual/monthly/zonal AGGREGATE curtailment (data/raw/nyiso-renewable-curtailment/),
# never an hourly per-plant potential/HSL series. A NYCA-wide annual wind
# curtailment RATE (~1.9% mean 2023-2025) IS derivable — so, unlike the earlier
# "too coarse for even a rate" wording, granularity is not what disqualifies the
# reference-rate gross-up. NYISO stays OUT of :data:`_UNCURTAILED_FALLBACK_ISOS`
# because (1) its curtailment is immaterial (~1.1%/yr, well under 1 TWh, below
# the dispatch-moving threshold; cf. MISO ~4.9%/multi-TWh) and (2) it is
# dominated by North/Central Zone LOCAL transmission-upgrade outages
# (North+Central = 72-93% of zonal curtailment every year) — a sub-zonal driver
# the reduced 5-zone network cannot re-curtail, so a uniform NYCA gross-up would
# inject phantom wind (CLAUDE.md #12 "misaligned to our representation"). The
# backcast therefore uses EIA-930 NYIS delivered generation. DATA NEEDED to move
# NYISO onto an uncurtailed path: an HOURLY wind/solar curtailment or HSL series
# (NP6/CAISO-workbook granularity). If NYISO ever publishes one, build one
# parquet per year (schema: ``_HSL_COLUMNS``) here and extend :func:`_hsl_file`.
_NYISO_HSL_DIR: Path = NYISO_HSL_DIR

# MISO curtailment directory. No hourly ``miso_<year>_hsl_hourly.parquet`` is
# built (misoenergy.org's 5-minute workbooks stay allowlist-blocked; HTTP 403,
# see docs/multi-iso/miso-data-audit.md), so :func:`_hsl_file` returns ``None``
# for MISO. Instead this directory holds the Potomac Economics (MISO IMM) annual
# wind-curtailment table (``miso_wind_curtailment_annual.csv`` +
# quarterly/forecast-method CSVs, README/SOURCES.md), a measured AGGREGATE source
# from which :func:`_miso_wind_reference_curtailment_rate` derives MISO's
# forward-reproducible wind curtailment rate. MISO wind therefore takes the
# reference-rate gross-up (``forecast_uncurtailed`` provenance), while MISO solar
# — no published curtailment series — keeps the delivered EIA-930 profile. If the
# hourly workbooks ever become reachable, build per-year HSL parquets (schema:
# ``_HSL_COLUMNS``, HSL = delivered + reported curtailment) following
# scripts/data/build_caiso_hsl.py and :func:`_hsl_file` will pick them up,
# upgrading MISO wind from ``forecast_uncurtailed`` to ``measured_potential``.
_MISO_HSL_DIR: Path = MISO_HSL_DIR

# Provenance labels for :func:`renewable_bound_provenance` — the L1 finding's
# scoring hook (docs/model-legitimacy-audit-2026-07.md §4, D-10 free-class
# rescore): whether a (ISO, year, fuel) renewable CF upper bound is a real
# uncurtailed-potential measurement, a reference-rate-grossed forecast
# approximation, or the raw delivered outcome — the L1 leakage this exists to
# flag. Report-only: none of these change LP behavior or gate a keeper
# verdict (wind/solar are already advisory-only in calibration_verdict.py);
# they let the calibration report and dashboard label which renewable rows
# are "free" (measure real headroom, so a C1 pass reflects model skill) vs
# "pinned" (the bound rides the outcome, so a pass reflects plumbing).
RENEWABLE_BOUND_MEASURED_POTENTIAL = "measured_potential"
RENEWABLE_BOUND_FORECAST_UNCURTAILED = "forecast_uncurtailed"
RENEWABLE_BOUND_DELIVERED_PINNED = "delivered_pinned"


def renewable_bound_provenance(iso: str, year: int, fuel: str) -> str:
    """Return how the ``(iso, year, fuel)`` renewable CF upper bound was built.

    One of:

    * ``"measured_potential"`` — a built HSL parquet covers this ISO-year (a
      published NP6 upload, the 2023 UMass reconstruction, or CAISO's
      delivered+reported-curtailment analogue): the bound is a real
      uncurtailed-potential measurement, so wind/solar's C1 row measures
      actual model skill.
    * ``"forecast_uncurtailed"`` — no HSL parquet, but the ISO is a
      high-curtailment fallback ISO (:data:`_UNCURTAILED_FALLBACK_ISOS`) with
      a reference curtailment rate available: the bound is the delivered
      shape grossed up by a *different* year's measured rate
      (:func:`_forecast_uncurtailed_cf`) — real headroom, endogenously
      re-curtailed, but a weaker measurement than a published potential
      series. This is MISO wind (Potomac Economics measured annual rate) and
      any future ERCOT year lacking an NP6 upload.
    * ``"delivered_pinned"`` — neither of the above: the dispatch is handed
      the raw delivered EIA-930 profile as the upper bound (L1's HIGH-severity
      leakage, docs/model-legitimacy-audit-2026-07.md §4), so the LP rides the
      bound and the class's C1 row is scoring plumbing, not skill. This is
      NYISO/NEISO (sub-1% curtailment; for NYISO a NYCA-wide annual rate exists
      but is the wrong instrument — its curtailment is locally driven and the
      reduced network can't re-curtail a gross-up, see the module docstring),
      MISO solar (no published curtailment series), and any ERCOT/CAISO year
      where HSL coverage runs out AND no reference curtailment rate exists.
    """
    hsl_path = _hsl_file(iso, year)
    if hsl_path is not None and hsl_path.exists():
        return RENEWABLE_BOUND_MEASURED_POTENTIAL
    if iso in _UNCURTAILED_FALLBACK_ISOS and _reference_curtailment_rate(iso, fuel):
        return RENEWABLE_BOUND_FORECAST_UNCURTAILED
    return RENEWABLE_BOUND_DELIVERED_PINNED


def _hsl_file(iso: str, year: int) -> Path | None:
    """Return the uncurtailed-potential parquet for ``(iso, year)``, or ``None``.

    ``None`` when no HSL-style dataset covers the pair — the backcast then
    uses the delivered EIA-930 hourly profile (which embeds the historical
    curtailment) instead of an uncurtailed potential.
    """
    if iso == "ERCOT":
        return _ercot_hsl_path(year)
    if iso == "CAISO":
        return _CAISO_HSL_DIR / f"caiso_{year}_hsl_hourly.parquet"
    if iso == "NYISO":
        # DATA NEEDED: an HOURLY nyiso_<year>_hsl_hourly.parquet in
        # _NYISO_HSL_DIR. NYISO publishes only annual/monthly/zonal AGGREGATE
        # curtailment (~1.1%/yr, well under 1 TWh) — no hourly potential/HSL
        # series, and its curtailment is dominated by North/Central local
        # transmission-upgrade outages the reduced network can't re-curtail, so
        # NYISO is NOT in _UNCURTAILED_FALLBACK_ISOS and takes no reference-rate
        # gross-up either (see _NYISO_HSL_DIR and the module docstring). The
        # delivered EIA-930 NYIS profile is the documented default.
        candidate = _NYISO_HSL_DIR / f"nyiso_{year}_hsl_hourly.parquet"
        return candidate if candidate.exists() else None
    if iso == "MISO":
        # MISO publishes no hourly uncurtailed-potential series (misoenergy.org's
        # 5-minute workbooks are allowlist-blocked; see _MISO_HSL_DIR and the
        # audit doc), so no miso_<year>_hsl_hourly.parquet is built and this
        # returns None. MISO wind still re-curtails: it takes the forecast-
        # uncurtailed reference-rate gross-up from the Potomac Economics measured
        # annual rate (_UNCURTAILED_FALLBACK_ISOS / _forecast_uncurtailed_cf),
        # not this hourly path. The branch would pick up an hourly parquet
        # automatically if one were ever built.
        candidate = _MISO_HSL_DIR / f"miso_{year}_hsl_hourly.parquet"
        return candidate if candidate.exists() else None
    # NEISO: ISO-NE reported curtailment is sub-1 % of potential — the
    # delivered EIA-930 ISNE series is the documented default; no uncurtailed-
    # potential parquet is built.  To add one, follow the CAISO pattern in
    # scripts/data/build_caiso_hsl.py and wire a ``_NEISO_HSL_DIR`` constant above.
    # data-needed: requires ISO-NE to publish granular curtailment data.
    return None


# An HSL parquet records the hourly *uncurtailed potential* (HSL >= delivered);
# the dispatch curtails endogenously from it and the modeled-vs-reported
# curtailment gap is a *diagnostic*, never a fit target (claude.md: measured
# data is a reproducible physical input, never the answer — no pinning the
# backcast to actuals). The series is therefore consumed as-is, with ONE
# real-data reconciliation (see :func:`hsl_potential_mw`): a derived /
# partial-footprint source (e.g. the 2023 UMass nodal reconstruction) can cover
# fewer plants than the full ISO, so its annual delivered undercounts the
# authoritative EIA-930 system total — physically impossible for a potential,
# since HSL >= delivered >= EIA-930 delivered. There the series is scaled UP to
# the EIA-930 delivered footprint *preserving the dataset's own measured
# curtailment ratio* (delivered/HSL). That reconciles two real datasets (the
# parquet's hourly shape + curtailment ratio, the EIA-930 level); it references
# nothing about model output and is a no-op for authoritative full-footprint
# NP4-732/737 HSL uploads, whose delivered already matches EIA-930 within
# tolerance. Prefer replacing any derived source with the published ERCOT
# NP4-732/737 HSL (scripts/data/build_ercot_hsl.py, np6/ drop zone) so the
# reconciliation never fires.
_HSL_COVERAGE_RECONCILE_TOL = 0.98  # reconcile only a > 2% footprint undercount


def _ercot_hsl_path(year: int) -> Path:
    """Return the per-year ERCOT HSL parquet path (which may not exist)."""
    return _ERCOT_HSL_DIR / f"ercot_{year}_hsl_hourly.parquet"


def load_ercot_hsl_hourly(year: int) -> pd.DataFrame | None:
    """Return the ERCOT hourly HSL/GEN frame for ``year``, or ``None``.

    The frame is the per-year parquet built by ``scripts/data/build_ercot_hsl.py``,
    sorted by ``hour`` (the model's fixed non-leap 8760-hour clock): delivered
    generation (``<fuel>_gen_mw``) and uncurtailed potential
    (``<fuel>_hsl_mw``) for wind and solar, so ERCOT's *reported* curtailment
    is ``hsl - gen``. Returns ``None`` when the year's parquet is missing or
    malformed, signaling callers to fall back (profiles to EIA-930 delivered
    generation; calibration reports to a model-only curtailment table).
    Thin ERCOT wrapper over the ISO-generic :func:`load_hsl_hourly`.
    """
    return load_hsl_hourly("ERCOT", year)


def hsl_potential_mw(iso: str, year: int, fuel: str) -> np.ndarray | None:
    """Return the hourly uncurtailed potential (MW) the dispatch consumes.

    This is the year's HSL-style series (ERCOT NP4-732/737 HSL, or the CAISO
    delivered-plus-reported-curtailment analogue), consumed as-is apart from
    the real-data coverage reconciliation described on
    :data:`_HSL_COVERAGE_RECONCILE_TOL`: a partial-footprint source whose
    delivered (GEN) undercounts the EIA-930 system total is scaled UP to that
    level while preserving its own measured curtailment ratio (delivered/HSL),
    a no-op for full-footprint published uploads. The result is exactly the MW
    series :func:`_hsl_cf_profile` turns into the dispatch's CF profile, so
    calibration reports can reconstruct the model's hourly renewable potential
    (e.g. for the modeled-vs-reported curtailment metric) without re-deriving
    the fleet. Returns ``None`` when no HSL parquet covers ``(iso, year)``.
    """
    df = load_hsl_hourly(iso, year)
    if df is None:
        return None
    column = f"{fuel}_hsl_mw"
    if column not in df.columns:
        return None
    hsl_mw = df[column].to_numpy(dtype=float)
    hsl_total = float(hsl_mw.sum())
    gen_column = f"{fuel}_gen_mw"
    if hsl_total <= 0.0 or gen_column not in df.columns:
        return hsl_mw
    # Real-data coverage reconciliation (see _HSL_COVERAGE_RECONCILE_TOL). The
    # dataset's own delivered (GEN) vs the EIA-930 system delivered measures
    # footprint completeness; when the source materially undercounts, scale UP
    # to the EIA-930 level preserving the measured delivered/HSL ratio — never
    # a tune to model output. No-op for full-footprint published data.
    delivered_mwh = _eia930_delivered_mwh(iso, year, fuel)
    src_gen = float(df[gen_column].sum())
    if (
        delivered_mwh is not None
        and src_gen > 0.0
        and src_gen < _HSL_COVERAGE_RECONCILE_TOL * delivered_mwh
    ):
        delivered_to_hsl = src_gen / hsl_total  # the dataset's measured ratio
        target_hsl = delivered_mwh / delivered_to_hsl
        hsl_mw = hsl_mw * (target_hsl / hsl_total)
    return hsl_mw


def _eia930_delivered_mwh(iso: str, year: int, fuel: str) -> float | None:
    """Return the EIA-930 annual delivered generation (MWh) for the fuel.

    The reconciliation target for :func:`hsl_potential_mw` — the authoritative
    system delivered total an uncurtailed-potential series must sit at or above.
    Returns ``None`` when the ISO/year/fuel has no mapped hourly extract or the
    series sums to zero (a reporting gap, not genuine zero output).
    """
    gen = load_eia_hourly_renewable_gen(iso, year)
    if gen is None or fuel not in gen:
        return None
    total = float(gen[fuel].sum())
    return total if total > 0.0 else None


# Potomac Economics (MISO's FERC-designated Independent Market Monitor) annual
# wind-curtailment table — the reproducible aggregate MISO wind curtailment
# source, used because misoenergy.org's 5-minute curtailment workbooks stay
# allowlist-blocked (HTTP 403; see data/raw/miso-hsl/SOURCES.md and the audit
# doc). One row per year carries average delivered (real-time) wind output and
# average curtailed MW, so the annual curtailment RATE
# ``curtailed / (delivered + curtailed)`` is a measured, forward-reproducible
# market parameter (a new SOM report lands each June/July for the prior year).
# It is NOT an hourly series — MISO publishes none — so it feeds the
# reference-rate gross-up (:func:`_forecast_uncurtailed_cf`), never an
# uncurtailed-potential (HSL) parquet, and MISO wind's renewable bound is
# labelled ``forecast_uncurtailed``, not ``measured_potential``.
_MISO_WIND_CURTAILMENT_ANNUAL: Path = MISO_HSL_DIR / "miso_wind_curtailment_annual.csv"

# Training-window years (CLAUDE.md #22) whose firm (non-estimate) annual rows
# set the MISO wind reference curtailment rate. Restricted to 2023-2025 so the
# structural rate never reads a validation/locked holdout year (2019/2022/H1
# 2026); 2025 is currently a source-flagged estimate and is dropped by the
# non-estimate filter, so today the rate is the 2023+2024 firm mean (~4.9%).
_MISO_REFERENCE_RATE_YEARS: frozenset[int] = frozenset({2023, 2024, 2025})


def _miso_wind_reference_curtailment_rate() -> tuple[float, int] | None:
    """Return ``(rate, year)`` — MISO's measured annual wind curtailment rate.

    Reads the Potomac Economics (MISO IMM) annual wind-curtailment table
    (:data:`_MISO_WIND_CURTAILMENT_ANNUAL`) and returns the training-window
    (:data:`_MISO_REFERENCE_RATE_YEARS`) mean of the firm (``is_estimate`` false)
    annual rates ``curtailed / (delivered + curtailed)``, tagged with the latest
    contributing year. This is MISO's forward-reproducible reference curtailment
    rate: a measured aggregate market parameter — MISO does not publish an hourly
    curtailment series — used to gross the delivered EIA-930 wind profile up to
    an uncurtailed potential (:func:`_forecast_uncurtailed_cf`), the same
    forecast-uncurtailed construction ERCOT's no-HSL years use. It references no
    target-year dispatch outcome, so it cannot pin the backcast (CLAUDE.md
    #11/#13), and it re-derives only when the source table updates (#24). The
    2023-2025 restriction keeps it clear of every holdout year (#22).

    Returns ``None`` when the table is missing or carries no firm training-year
    row with both delivered and curtailed MW.
    """
    if not _MISO_WIND_CURTAILMENT_ANNUAL.exists():
        return None
    try:
        table = pd.read_csv(_MISO_WIND_CURTAILMENT_ANNUAL)
    except (OSError, ValueError):
        return None
    rates: list[float] = []
    latest_year = 0
    # itertuples (positional, name=None) instead of iterrows: the per-column
    # positions are resolved once here, which also preserves the ``.get``
    # semantics the loop relied on -- a column absent from the table reads as
    # ``None`` (or ``""`` for ``is_estimate``) exactly as before, rather than
    # raising.
    _pos = {name: i for i, name in enumerate(table.columns)}
    _i_year = _pos.get("year")
    _i_est = _pos.get("is_estimate")
    _i_curt = _pos.get("avg_wind_curtailed_mw")
    _i_out = _pos.get("avg_wind_output_rt_gw")
    for row in table.itertuples(index=False, name=None):
        year = _as_int(row[_i_year] if _i_year is not None else None)
        if year is None or year not in _MISO_REFERENCE_RATE_YEARS:
            continue
        if str(row[_i_est] if _i_est is not None else "").strip().upper() == "TRUE":
            continue
        curtailed = _as_float(row[_i_curt] if _i_curt is not None else None)
        delivered_gw = _as_float(row[_i_out] if _i_out is not None else None)
        if curtailed is None or curtailed < 0.0 or delivered_gw is None:
            continue
        potential_mw = delivered_gw * 1_000.0 + curtailed  # RT output is GW
        if potential_mw <= 0.0:
            continue
        rates.append(curtailed / potential_mw)
        latest_year = max(latest_year, year)
    if not rates:
        return None
    return sum(rates) / len(rates), latest_year


# SPP's measured annual wind-curtailment table (SPP MMU Annual State of the
# Market, transcribed by lane SPP-12; the metered delivered leg measured from
# SPP's own 5-minute generation mix by lane SPP-32). Same role as
# :data:`_MISO_WIND_CURTAILMENT_ANNUAL`: SPP publishes no hourly HSL series.
_SPP_WIND_CURTAILMENT_ANNUAL: Path = SPP_HSL_DIR / "spp_wind_curtailment_annual.csv"

# Training-window years (CLAUDE.md #22 ``[R-HOLDOUT]``) whose rows set the SPP
# wind reference curtailment rate. Restricted to 2023-2025 for exactly the
# reason the MISO set is: the structural rate must never read a validation or
# locked-test year (SPP's table also carries 2019 and 2022 rows, both holdout
# years, and both are excluded here by construction rather than by discipline).
_SPP_REFERENCE_RATE_YEARS: frozenset[int] = frozenset({2023, 2024, 2025})

# The two metric rows the SPP rate is formed from, both on an AVERAGE-MW basis.
# Pairing two average-MW quantities needs no hours-per-year assumption at all,
# which is why these are used in preference to the table's ``curtailed_energy_gwh``
# rows (those multiply by a flat 8760 and so are 0.27% off in a leap year).
_SPP_CURTAILED_METRIC: str = "avg_hourly_curtailment_mw"
_SPP_DELIVERED_METRIC: str = "avg_hourly_wind_delivered_mw"


def _spp_wind_reference_curtailment_rate() -> tuple[float, int] | None:
    """Return ``(rate, year)`` — SPP's measured annual wind curtailment rate.

    Reads SPP's annual wind-curtailment table
    (:data:`_SPP_WIND_CURTAILMENT_ANNUAL`) and returns the training-window
    (:data:`_SPP_REFERENCE_RATE_YEARS`) mean of the annual rates
    ``curtailed / (delivered + curtailed)``, tagged with the latest contributing
    year. Both legs are measured and they come from two INDEPENDENT SPP
    publications:

    * **curtailed** — ``avg_hourly_curtailment_mw``, printed verbatim in the SPP
      MMU's Annual State of the Market reports (2023 p. 55, 2024 p. 47, 2025
      p. 54);
    * **delivered** — ``avg_hourly_wind_delivered_mw``, the mean of SPP's own
      5-minute metered generation mix (``Wind Market`` + ``Wind Self``).

    Both are average MW over the year, so the ratio needs no hours-per-year
    convention and is leap-year-safe. This is SPP's forward-reproducible
    reference curtailment rate: a measured aggregate market parameter used to
    gross the delivered EIA-930 wind profile up to an uncurtailed potential
    (:func:`_forecast_uncurtailed_cf`) — the same construction MISO's rate and
    ERCOT's no-HSL years use. It references no target-year dispatch outcome, so
    it cannot pin the backcast (CLAUDE.md rules 13 ``[R-MEASURED]`` / 1
    ``[R-STRUCT]``), and it re-derives only when its source data updates (rule
    23 ``[R-FROZEN-DERIVE]``).

    Two properties of the source, stated rather than smoothed:

    * SPP's 2025 curtailment MW is published on a *variable energy resources*
      (wind + solar) basis where 2023/2024 are wind-only. The same ASOM page
      bounds the difference — solar is 0.73% of SPP's curtailment — so the
      series is comparable in practice and no adjustment is applied.
    * The rate is ~9.7% averaged over 2023-2025, about twice MISO's ~4.9%.

    Returns ``None`` when the table is missing, unreadable, or carries no
    training-year row with both legs present.
    """
    if not _SPP_WIND_CURTAILMENT_ANNUAL.exists():
        return None
    try:
        table = pd.read_csv(_SPP_WIND_CURTAILMENT_ANNUAL)
    except (OSError, ValueError):
        return None
    if not {"year", "metric", "value"} <= set(table.columns):
        return None
    legs: dict[int, dict[str, float]] = {}
    _pos = {name: i for i, name in enumerate(table.columns)}
    _i_year, _i_metric, _i_value = _pos["year"], _pos["metric"], _pos["value"]
    for row in table.itertuples(index=False, name=None):
        year = _as_int(row[_i_year])
        if year is None or year not in _SPP_REFERENCE_RATE_YEARS:
            continue
        metric = str(row[_i_metric]).strip()
        if metric not in (_SPP_CURTAILED_METRIC, _SPP_DELIVERED_METRIC):
            continue
        value = _as_float(row[_i_value])
        if value is None or value < 0.0:
            continue
        legs.setdefault(year, {})[metric] = value
    rates: list[float] = []
    latest_year = 0
    for year, leg in legs.items():
        curtailed = leg.get(_SPP_CURTAILED_METRIC)
        delivered = leg.get(_SPP_DELIVERED_METRIC)
        if curtailed is None or delivered is None:
            continue
        potential = delivered + curtailed
        if potential <= 0.0:
            continue
        rates.append(curtailed / potential)
        latest_year = max(latest_year, year)
    if not rates:
        return None
    return sum(rates) / len(rates), latest_year


# Per-(ISO, fuel) providers of a measured ANNUAL reference curtailment rate, for
# ISOs that publish no hourly HSL series but do publish an aggregate rate the
# gross-up can be built from. A registry rather than a branch (rule 24
# ``[R-REGISTRY]``) so a new ISO registers a callable instead of growing an
# ``if iso ==`` ladder inside :func:`_reference_curtailment_rate`.
#
# MISO's provider is reached by the explicit branch that predates this registry
# and is deliberately left where it is: lane SPP-32 owns SPP's rows in this
# module and not MISO's, so folding MISO in here is a one-line consolidation
# routed to SPP-DESK rather than taken unilaterally. Behaviour is identical
# either way — the registry is consulted only after every HSL year has missed.
_ANNUAL_REFERENCE_RATE_PROVIDERS: dict[
    tuple[str, str], Callable[[], tuple[float, int] | None]
] = {
    ("SPP", "wind"): _spp_wind_reference_curtailment_rate,
}


def _reference_curtailment_rate(iso: str, fuel: str) -> tuple[float, int] | None:
    """Return ``(rate, year)`` — the per-tech curtailment rate of a recent HSL year.

    Scans :data:`_REFERENCE_HSL_YEARS` newest-first for a year with a built HSL
    parquet covering ``(iso, fuel)`` and returns its reported curtailment rate
    ``1 - GEN/HSL`` (the same ``HSL - GEN`` the calibration report benchmarks
    against) and the year it came from. This is a real, forward-reproducible
    market parameter — a measured curtailment rate from a *different* year —
    used to gross a no-HSL year's delivered profile up to an uncurtailed
    potential; it never references the target year's own actuals, so it cannot
    pin the backcast (CLAUDE.md #11).

    MISO publishes no hourly HSL series, but its IMM (Potomac Economics)
    publishes a measured aggregate annual wind curtailment rate — a
    forward-reproducible market parameter that grosses the delivered wind
    profile up to an uncurtailed potential exactly as an HSL-year rate does — so
    MISO wind falls back to :func:`_miso_wind_reference_curtailment_rate`. MISO
    solar has no such published series, so it returns ``None`` and keeps the
    delivered profile.

    The same situation for any other ISO is served by
    :data:`_ANNUAL_REFERENCE_RATE_PROVIDERS`, a ``(iso, fuel) -> callable``
    registry consulted after every HSL year has missed — SPP wind is registered
    there (:func:`_spp_wind_reference_curtailment_rate`). An ISO-fuel with
    neither an HSL year nor a registered provider returns ``None`` and keeps the
    delivered profile, which is the documented fallback.

    Returns ``None`` when the ISO has no HSL-covered reference year (the caller
    then keeps the delivered profile, leaving curtailment unmodeled).
    """
    for ref_year in _REFERENCE_HSL_YEARS:
        df = load_hsl_hourly(iso, ref_year)
        if df is None:
            continue
        gen = float(df[f"{fuel}_gen_mw"].sum())
        hsl = float(df[f"{fuel}_hsl_mw"].sum())
        if hsl > 0.0 and 0.0 < gen <= hsl:
            return 1.0 - gen / hsl, ref_year
    if iso == "MISO" and fuel == "wind":
        return _miso_wind_reference_curtailment_rate()
    provider = _ANNUAL_REFERENCE_RATE_PROVIDERS.get((iso, fuel))
    if provider is not None:
        return provider()
    return None


def _forecast_uncurtailed_cf(
    iso: str,
    year: int,
    fuel: str,
    monthly_capacity: np.ndarray,
) -> np.ndarray | None:
    """Return an uncurtailed CF profile for a no-HSL backcast year, or ``None``.

    For a high-curtailment ISO-year-tech with no HSL parquet (MISO wind, which
    has no hourly series at all; any future ERCOT year lacking an NP6 upload),
    the dispatch still needs an *uncurtailed* renewable upper bound so it can
    re-curtail endogenously rather than inherit the curtailment baked into
    delivered output. This builds one the same way the CAISO HSL parquet does —
    delivered + curtailment — except the year's own hourly curtailment series is
    unavailable, so the EIA-930 weather-year delivered profile (its real level
    and shape) is grossed up by the per-tech **reference curtailment rate** from
    a *different* source year — a recent HSL year, or the Potomac Economics
    measured annual wind rate for MISO (:func:`_reference_curtailment_rate`)::

        uncurtailed_cf(t) = delivered_cf(t) / (1 - reference_rate)

    The result is therefore always >= delivered (a valid potential) with
    headroom equal to the reference rate, which the LP curtails endogenously.
    The reference rate is a measured parameter from a *different* year, the same
    quantity a forward run would assume, so the potential is never scaled to
    land delivered output on the target year's actuals — the modeled-vs-reported
    curtailment gap is a diagnostic, not a fit target (CLAUDE.md #11). In
    forecast mode (no measured delivered series) the loader keeps using the
    forecast :data:`RENEWABLE_AVG_CF` profile instead.

    Returns ``None`` when the year has no delivered EIA-930 series or the ISO
    has no HSL-covered reference year, signaling the caller to keep the
    delivered profile (curtailment then unmodeled for the year).
    """
    delivered_cf = _eia_hourly_cf_profile(iso, year, fuel, monthly_capacity)
    if delivered_cf is None:
        return None
    rate_info = _reference_curtailment_rate(iso, fuel)
    if rate_info is None:
        return None
    rate, _ = rate_info
    if not 0.0 <= rate < 1.0:
        return None
    return np.clip(delivered_cf / (1.0 - rate), _CF_MIN, _CF_MAX)


def _oversupply_curtailment_allocation(
    net_load_mw: np.ndarray,
    headroom_mw: np.ndarray,
    target_mwh: float,
) -> tuple[np.ndarray, float] | None:
    """Water-fill ``target_mwh`` onto the lowest-net-load hours, or ``None``.

    Solves for the unique level ``lambda`` at which

    ``sum_t min(max(0, lambda - net_load_mw[t]), headroom_mw[t]) == target_mwh``

    and returns ``(curtailment_mw, lambda)``. The level is **determined by that
    identity, never chosen** — it is the oversupply analogue of the flat rule's
    ``1 / (1 - rate)`` factor and carries no degree of freedom (rule 21
    ``[R-DOF]``). Its physical reading is the net-load level below which the
    system could not turn further down and had to spill.

    ``headroom_mw`` caps each hour at the fleet's own online capacity less its
    delivered output, so a reconstructed potential can never exceed nameplate.

    Args:
        net_load_mw: Hourly net load (load less delivered variable generation).
        headroom_mw: Hourly non-negative cap on reconstructed curtailment.
        target_mwh: The frozen annual curtailment energy to allocate.

    Returns:
        ``(curtailment_mw, lambda)``, or ``None`` when the capped headroom
        cannot hold ``target_mwh`` (no root — the caller must fall back rather
        than silently allocate less than the measured annual energy).
    """
    if target_mwh <= 0.0:
        return np.zeros_like(net_load_mw), float("nan")
    hi = float(net_load_mw.max()) + 1.0
    if (
        float(np.minimum(np.maximum(hi - net_load_mw, 0.0), headroom_mw).sum())
        < target_mwh
    ):
        return None
    lo = float(net_load_mw.min()) - 1.0
    for _ in range(_WATER_FILL_ITERS):
        mid = 0.5 * (lo + hi)
        filled = float(
            np.minimum(np.maximum(mid - net_load_mw, 0.0), headroom_mw).sum()
        )
        if filled < target_mwh:
            lo = mid
        else:
            hi = mid
    level = 0.5 * (lo + hi)
    return np.minimum(np.maximum(level - net_load_mw, 0.0), headroom_mw), level


def _oversupply_uncurtailed_cf(
    iso: str,
    year: int,
    fuel: str,
    monthly_capacity: np.ndarray,
    iso_config: ISOConfig,
) -> np.ndarray | None:
    """Return an OVERSUPPLY-allocated uncurtailed CF profile, or ``None``.

    The ``vre_curtailment_oversupply_allocation`` construction (SPP-51c). It
    distributes exactly the same annual curtailment energy
    :func:`_forecast_uncurtailed_cf` does — ``rate / (1 - rate)`` times annual
    delivered output, from the ISO's frozen measured reference rate — but
    across the hours the system had **nowhere to put the energy** instead of
    uniformly across all 8,760.

    Delivered generation is already net of curtailment, so a flat per-hour
    gross-up hands the LP its headroom everywhere *except* where the spill
    actually happened, and the dispatch cannot re-curtail where the market did.
    Real curtailment is availability meeting low net load and congestion, so the
    allocation is keyed on the ISO's own net load
    ``NL(t) = load(t) - delivered wind(t) - delivered solar(t)``: the frozen
    annual energy is water-filled onto the hours where ``NL`` sits lowest,
    capped per hour by the fleet's online-capacity headroom
    (:func:`_oversupply_curtailment_allocation`).

    **Zero new free parameters** (rule 21 ``[R-DOF]``): the rate is the frozen
    measured reference rate (rule 23 ``[R-FROZEN-DERIVE]``), the fill level is
    the unique root of the annual identity rather than a chosen threshold, the
    cap is measured EIA-860 capacity, and load and delivered output are inputs
    the LP already consumes. **Forward-native** (rule 13 ``[R-MEASURED]``): a
    forecast year has all three legs, so the construction regenerates and
    responds to changed conditions. It **replaces** the flat gross-up rather
    than stacking on it (rule 19 ``[R-ONE-MECH]``), and is ISO-agnostic — it
    fires wherever the reference-rate path fires (rule 25 ``[R-ISO-SCOPE]``).

    Returns ``None`` — signalling the caller to fall back to
    :func:`_forecast_uncurtailed_cf` — when any leg is unavailable: no delivered
    series, no reference rate, no EIA-860 monthly capacity, an unreadable demand
    array, a clock-length mismatch, or capped headroom too small to hold the
    annual energy.
    """
    rate_info = _reference_curtailment_rate(iso, fuel)
    if rate_info is None:
        return None
    rate, _ = rate_info
    if not 0.0 <= rate < 1.0:
        return None
    gen = load_eia_hourly_renewable_gen(iso, year)
    if gen is None or fuel not in gen:
        return None
    delivered = np.asarray(gen[fuel], dtype=float)
    if delivered.shape != (HOURS_PER_YEAR,) or delivered.sum() <= 0.0:
        return None

    # Net load on DELIVERED variable generation: the oversupply axis. Both legs
    # come off the ISO's own EIA-930 frame, the same clock the dispatch runs on.
    from market_sim.data.eia930.demand import load_demand

    try:
        zonal_demand = load_demand(iso, year, iso_config)
    except Exception:  # noqa: BLE001 - a missing/unreadable demand array no-ops
        return None
    if zonal_demand is None or zonal_demand.shape[-1] != HOURS_PER_YEAR:
        return None
    net_load = zonal_demand.sum(axis=0).astype(float)
    for other in ("wind", "solar"):
        series = gen.get(other)
        if series is not None and np.shape(series) == (HOURS_PER_YEAR,):
            net_load = net_load - np.asarray(series, dtype=float)

    online_cap = monthly_capacity.sum(axis=0)[_hour_to_month_index(HOURS_PER_YEAR)]
    headroom = np.maximum(online_cap - delivered, 0.0)
    target = float(delivered.sum()) * rate / (1.0 - rate)
    result = _oversupply_curtailment_allocation(net_load, headroom, target)
    if result is None:
        logger.warning(
            "%s %s %d: oversupply curtailment allocation has no root "
            "(capped headroom %.1f GWh < annual curtailment %.1f GWh); "
            "falling back to the flat reference-rate gross-up",
            iso,
            fuel,
            year,
            headroom.sum() / 1e3,
            target / 1e3,
        )
        return None
    curtailment, level = result

    # Arming proof, the ERCOT-113 silent-inertness discipline: an overlay that
    # no-ops through a full solve is invisible, so announce the level the
    # identity chose and the footprint it implies. Both are checkable against
    # the source data without a re-solve.
    allocated_hours = int((curtailment > 0.0).sum())
    logger.info(
        "%s %s %d oversupply curtailment allocation: %.1f GWh over %d hour(s) "
        "(%.1f%% of the year) at net-load level %.0f MW; annual potential "
        "%.3f TWh, unchanged from the flat gross-up",
        iso,
        fuel,
        year,
        curtailment.sum() / 1e3,
        allocated_hours,
        allocated_hours / HOURS_PER_YEAR * 100.0,
        level,
        (delivered.sum() + curtailment.sum()) / 1e6,
    )
    return _mw_to_cf(delivered + curtailment, monthly_capacity)


def _as_float(value: object) -> float | None:
    """Coerce ``value`` to a float, returning ``None`` for blanks or NaN."""
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return None if result != result else result


def _as_int(value: object) -> int | None:
    """Coerce ``value`` to an int, returning ``None`` for blanks or NaN."""
    result = _as_float(value)
    return None if result is None else int(result)


def _optional_numeric(df: pd.DataFrame, column: str) -> np.ndarray:
    """Return ``df[column]`` as a float array, or all-NaN if the column is absent.

    Column-safe access for optional EIA-860 fields (e.g. ``Planned Retirement
    Year`` / ``Month``): a vintage that does not carry the column yields an
    all-NaN array, which the per-plant reduction reads as "no retirement".
    """
    if column in df.columns:
        return pd.to_numeric(df[column], errors="coerce").to_numpy()
    return np.full(len(df), np.nan)


def _eia860_monthly_capacity(
    iso: str,
    fuel: str,
    zone_names: list[str],
    cal_year: int | None,
    data_dir: Path | None = None,
) -> np.ndarray | None:
    """Return an ``(n_zones, 12)`` array of operable capacity (MW) by month.

    Each EIA-860 operable wind/solar plant is placed in a model zone via the
    eGRID ORIS->zone lookup (see :mod:`market_sim.data.zone_assignment`) and
    contributes its nameplate capacity to the months it was online — the
    month-precise COD ON-ramp **and** planned-retirement OFF-ramp, evaluated by
    the shared :func:`market_sim.data.cod_ramp.monthly_online_mask`:

    * ``operating_year < cal_year`` -- online from January (subject to any
      retirement below);
    * ``operating_year == cal_year`` -- online from ``operating_month`` on;
    * ``operating_year > cal_year`` -- not yet online (zero);
    * ``retirement_year < cal_year`` -- already retired (zero all months);
    * ``retirement_year == cal_year`` -- online through ``retirement_month``.

    A missing ``operating_month`` falls back to
    :data:`market_sim.data.cod_ramp.COD_FALLBACK_MONTH` and a missing
    ``retirement_month`` to December, the one month-precise convention shared
    with the thermal/storage loaders.

    When ``cal_year`` is ``None`` every operable plant is treated as online
    in all twelve months (no vintage ramp).

    Source: EIA-860 2024, Generator_Operable sheet, ``Operating Month`` /
    ``Operating Year`` and ``Planned Retirement Month`` / ``Year`` columns.

    Returns ``None`` when the EIA-860 parquet is missing or the ISO has no
    eGRID geographic zone rules, signaling the caller to fall back to the
    hardcoded single-zone allocation.
    """
    file_name = _EIA860_OPERABLE_FILES.get(fuel)
    if file_name is None:
        return None
    if data_dir is None:
        from market_sim.config.paths import active_eia860_dir

        data_dir = active_eia860_dir()
    path = Path(data_dir) / file_name
    if not path.exists():
        return None

    from market_sim.data.zone_assignment import build_zone_lookup

    try:
        zone_lookup = build_zone_lookup(iso)
    except Exception:
        return None
    if not zone_lookup:
        return None

    df = pd.read_parquet(path)
    status = df["Status"].astype(str).str.strip().str.upper()
    df = df[status == "OP"]

    zone_to_idx = {name: i for i, name in enumerate(zone_names)}
    monthly = np.zeros((len(zone_names), _MONTHS_PER_YEAR), dtype=float)

    plant_code = df["Plant Code"].to_numpy()
    capacity = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce").to_numpy()
    op_year = pd.to_numeric(df["Operating Year"], errors="coerce").to_numpy()
    op_month = pd.to_numeric(df["Operating Month"], errors="coerce").to_numpy()
    # Planned-retirement OFF-ramp inputs, mirroring the COD ON-ramp. Absent on
    # a vintage that does not carry them -> all-NaN -> "no retirement".
    ret_year = _optional_numeric(df, "Planned Retirement Year")
    ret_month = _optional_numeric(df, "Planned Retirement Month")

    for code, cap, oy, om, ry, rm in zip(
        plant_code, capacity, op_year, op_month, ret_year, ret_month
    ):
        oris = _as_int(code)
        zone = zone_lookup.get(oris) if oris is not None else None
        z_idx = zone_to_idx.get(zone) if zone is not None else None
        if z_idx is None:
            continue
        if cap is None or cap != cap or cap <= 0.0:  # None / NaN / non-positive
            continue
        if cal_year is None:
            monthly[z_idx, :] += cap  # no vintage ramp -> online all year
            continue
        # Month-precise online window: COD ON-ramp + planned-retirement
        # OFF-ramp, the one convention shared with the thermal/storage loaders.
        mask = monthly_online_mask(
            _as_int(oy),
            (_as_int(om) or COD_FALLBACK_MONTH),
            _as_int(ry),
            _as_int(rm),
            cal_year,
        )
        if mask.any():
            monthly[z_idx] += cap * mask

    # Augment with high-confidence EIA-860 proposed plants when the
    # calibration year is past the operable snapshot vintage (Sep 2024).
    # These are 2025-and-later commercial-operation dates not yet
    # reflected in the operable file. We use plant lat/lon (rather than
    # the eGRID ORIS lookup, which doesn't cover newly-assigned plant
    # codes) to assign each plant to a model zone.
    if cal_year is not None and cal_year > _operable_vintage_year(data_dir):
        _add_proposed_capacity(monthly, iso, fuel, zone_to_idx, cal_year, data_dir)

    if monthly.sum() <= 0.0:
        return None
    return monthly


def _add_proposed_capacity(
    monthly: np.ndarray,
    iso: str,
    fuel: str,
    zone_to_idx: dict[str, int],
    cal_year: int,
    data_dir: Path,
) -> None:
    """Add EIA-860 proposed wind/solar plants to the monthly capacity tally.

    Each proposed plant (status ``U``/``V``/``TS``/``P``, the high-
    confidence subset) located in the ISO's home state(s), with an
    ``Effective Year`` strictly after the operable snapshot vintage and
    at-or-before ``cal_year``, contributes its nameplate capacity from
    its ``Effective Month`` onward (or all twelve months when the
    effective year is earlier than ``cal_year``). Plants are placed in
    a model zone from their lat/lon in ``eia860_plant.parquet`` via
    :func:`market_sim.data.zone_assignment.assign_zone_by_coords`.

    Only ISOs whose home state(s) are known here are augmented. State
    filtering is what bounds the proposed-plant pool to the ISO's
    geographic footprint; without it the lat/lon zone rule would
    incorrectly drag in projects from other regions of the country.
    """
    iso_states = _ISO_HOME_STATES.get(iso)
    if iso_states is None:
        return

    proposed_path = Path(data_dir) / _EIA860_PROPOSED_FILE
    if not proposed_path.exists():
        return
    from market_sim.data.zone_assignment import assign_zone_by_coords

    df = pd.read_parquet(proposed_path)
    df = df[df["State"].isin(iso_states)]
    df = df[df["Technology"].map(_TECHNOLOGY_TO_FUEL) == fuel]
    status = df["Status"].astype(str).str.strip().str.upper()
    df = df[status.isin(_PROPOSED_HIGH_CONFIDENCE)]
    eff_year = pd.to_numeric(df["Effective Year"], errors="coerce")
    df = df[(eff_year > _operable_vintage_year(data_dir)) & (eff_year <= cal_year)]
    if df.empty:
        return

    plant_path = Path(data_dir) / "eia860_plant.parquet"
    if not plant_path.exists():
        return
    plants = pd.read_parquet(plant_path)[
        ["Plant Code", "Latitude", "Longitude"]
    ].drop_duplicates("Plant Code")
    df = df.merge(plants, on="Plant Code", how="left")

    # itertuples over the five columns read, positionally (name=None): the
    # EIA-860 headers carry spaces and parentheses, so named tuples would
    # mangle them; positional access sidesteps that and the values still go
    # through _as_float/_as_int, which coerce identically.
    _cols = [
        "Nameplate Capacity (MW)",
        "Latitude",
        "Longitude",
        "Effective Year",
        "Effective Month",
    ]
    for cap_v, lat_v, lon_v, e_year_v, e_month_v in df[_cols].itertuples(
        index=False, name=None
    ):
        cap = _as_float(cap_v)
        if cap is None or cap <= 0.0:
            continue
        lat = _as_float(lat_v)
        lon = _as_float(lon_v)
        if lat is None or lon is None:
            continue
        zone = assign_zone_by_coords(lat, lon, "ERCOT")
        z_idx = zone_to_idx.get(zone)
        if z_idx is None:
            continue
        # Effective Year already filtered to (vintage, cal_year]. For an
        # earlier year, the plant is online all 12 months of cal_year;
        # for ``cal_year`` itself, online from Effective Month onward.
        e_year = _as_int(e_year_v)
        if e_year is not None and e_year < cal_year:
            monthly[z_idx, :] += cap
            continue
        month = _as_int(e_month_v) or 1
        start = min(max(month, 1), _MONTHS_PER_YEAR)
        monthly[z_idx, start - 1 :] += cap


# Federal §45 wind PTC credit period: 10 years (120 months) from the
# placed-in-service date (26 U.S.C. §45(a)(2)(A)(ii)).
_PTC_WINDOW_MONTHS: int = 120


def wind_ptc_eligible_monthly_share(
    iso: str,
    zone_names: list[str],
    cal_year: int,
    data_dir: Path | None = None,
) -> np.ndarray | None:
    """Return the ``(n_zones, 12)`` PTC-window-eligible share of online wind.

    For each model zone and calendar month of ``cal_year``, the fraction of
    online wind nameplate capacity still inside its federal §45 production
    tax credit window — 10 years (120 months, :data:`_PTC_WINDOW_MONTHS`)
    from the unit's placed-in-service month (26 U.S.C. §45(a)(2)(A)(ii)).
    Same source, zone assignment (eGRID ORIS -> zone), status filter and
    month-precise online conventions as :func:`_eia860_monthly_capacity`
    (EIA-860 Generator_Operable, ``Operating Year``/``Month``), so the share
    denominator is the exact fleet the capacity loader distributes.
    Measured, rule-13 admissible and forward-native: for a forward year the
    same registry ages vintages out of the window and the proposed-plant
    augmentation (all post-snapshot CODs, in-window by construction) ages
    new ones in — the share responds to fleet turnover, never to a residual.

    Conventions:

    * A unit with an unknown ``Operating Year`` stays online (the
      :func:`monthly_online_mask` convention) but is treated as PAST its
      window (not eligible) — eligibility cannot be established, and the
      unknown-vintage tail of the file is old capacity.
    * Repowered units requalify for a fresh 10-year window in reality (the
      IRS 80/20 rule), but EIA-860 keeps the original ``Operating Year``
      for most repowerings, so the share UNDERSTATES eligibility by the
      repowered fleet — a documented conservatism, not a knob.

    Returns ``None`` when the EIA-860 parquet or the ISO's zone rules are
    missing (callers fall back to the flat unscoped offer).
    """
    file_name = _EIA860_OPERABLE_FILES.get("wind")
    if file_name is None:
        return None
    if data_dir is None:
        from market_sim.config.paths import active_eia860_dir

        data_dir = active_eia860_dir()
    path = Path(data_dir) / file_name
    if not path.exists():
        return None

    from market_sim.data.zone_assignment import build_zone_lookup

    try:
        zone_lookup = build_zone_lookup(iso)
    except Exception:
        return None
    if not zone_lookup:
        return None

    df = pd.read_parquet(path)
    status = df["Status"].astype(str).str.strip().str.upper()
    df = df[status == "OP"]

    zone_to_idx = {name: i for i, name in enumerate(zone_names)}
    total = np.zeros((len(zone_names), _MONTHS_PER_YEAR), dtype=float)
    eligible = np.zeros((len(zone_names), _MONTHS_PER_YEAR), dtype=float)

    plant_code = df["Plant Code"].to_numpy()
    capacity = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce").to_numpy()
    op_year = pd.to_numeric(df["Operating Year"], errors="coerce").to_numpy()
    op_month = pd.to_numeric(df["Operating Month"], errors="coerce").to_numpy()
    ret_year = _optional_numeric(df, "Planned Retirement Year")
    ret_month = _optional_numeric(df, "Planned Retirement Month")

    months = np.arange(1, _MONTHS_PER_YEAR + 1)
    for code, cap, oy, om, ry, rm in zip(
        plant_code, capacity, op_year, op_month, ret_year, ret_month
    ):
        oris = _as_int(code)
        zone = zone_lookup.get(oris) if oris is not None else None
        z_idx = zone_to_idx.get(zone) if zone is not None else None
        if z_idx is None:
            continue
        if cap is None or cap != cap or cap <= 0.0:  # None / NaN / non-positive
            continue
        oy_i = _as_int(oy)
        om_i = _as_int(om) or COD_FALLBACK_MONTH
        mask = monthly_online_mask(oy_i, om_i, _as_int(ry), _as_int(rm), cal_year)
        if not mask.any():
            continue
        total[z_idx] += cap * mask
        if oy_i is None:
            continue  # vintage unknown -> not eligible (see docstring)
        months_since_cod = (cal_year - oy_i) * _MONTHS_PER_YEAR + (months - om_i)
        in_window = (months_since_cod >= 0) & (months_since_cod < _PTC_WINDOW_MONTHS)
        eligible[z_idx] += cap * (mask & in_window)

    # Post-snapshot proposed plants: augment BOTH tallies — a new COD is
    # inside its window for the whole backcast horizon by construction.
    if cal_year > _operable_vintage_year(data_dir):
        _add_proposed_capacity(total, iso, "wind", zone_to_idx, cal_year, data_dir)
        _add_proposed_capacity(eligible, iso, "wind", zone_to_idx, cal_year, data_dir)

    if total.sum() <= 0.0:
        return None
    return np.divide(eligible, total, out=np.zeros_like(eligible), where=total > 0.0)


def _eia860_zone_shares(
    iso: str, fuel_code: str, cal_year: int | None = None
) -> dict[str, float]:
    """Return ``{zone_name: fraction}`` of renewable capacity from EIA-860.

    Shares are the December (year-end) capacity of each model zone, derived
    from EIA-860 operable wind/solar plant locations. When ``cal_year`` is
    given, only plants online by the end of that year are counted; a plant
    commissioned during ``cal_year`` still contributes its full capacity to
    the December total, so late-year additions are reflected in the share.

    Source: EIA-860 2024 (``eia860_wind_operable`` / ``eia860_solar_operable``),
    zone assigned via :mod:`market_sim.data.zone_assignment` using the
    eGRID PLNT23 lat/lon/FIPS geography.

    Returns an empty dict when EIA-860 data is unavailable for the ISO.
    """
    zone_names = get_iso_config(iso).zone_names
    monthly = _eia860_monthly_capacity(iso, fuel_code, zone_names, cal_year)
    if monthly is None:
        return {}
    december = monthly[:, -1]
    total = december.sum()
    if total <= 0.0:
        return {}
    return {zone_names[i]: float(december[i] / total) for i in range(len(zone_names))}


def get_renewable_zone(iso: str, fuel: str) -> str:
    """Return the zone that absorbs new ``fuel`` capacity for ``iso``.

    New wind and solar built by capacity evolution are routed to the same
    single zone that holds the existing fleet (see
    :data:`RENEWABLE_ZONE_ALLOCATION`), so the build increments that zone's
    ``wind_cap`` / ``solar_cap`` rather than entering as a thermal unit.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        fuel: Renewable fuel, ``"wind"`` or ``"solar"``.

    Returns:
        The target zone name.

    Raises:
        KeyError: if ``iso`` or ``fuel`` has no allocation entry.
    """
    return RENEWABLE_ZONE_ALLOCATION[iso][fuel]


def derive_cf_profile(generation_values: np.ndarray, avg_cf: float) -> np.ndarray:
    """Convert an EIA generation distribution into an hourly CF profile.

    The EIA ``value`` series is a probability distribution summing to ~1.0
    over the year. Scaling it by the annual-average capacity factor and by
    ``HOURS_PER_YEAR`` rescales the distribution so that its hourly mean
    equals ``avg_cf``. The result is clipped to the physical CF bounds
    ``[0, 1]`` to guard against rounding noise and high-output outliers.

    Args:
        generation_values: A ``(HOURS_PER_YEAR,)`` array of normalized EIA
            generation values for one ISO/year/fuel group.
        avg_cf: Annual-average capacity factor of the fleet (fraction).

    Returns:
        A ``(HOURS_PER_YEAR,)`` array of hourly capacity factors in
        ``[0, 1]``.
    """
    cf = generation_values * avg_cf * HOURS_PER_YEAR
    return np.clip(cf, _CF_MIN, _CF_MAX)


def _mw_to_cf(hourly_mw: np.ndarray, monthly_capacity: np.ndarray) -> np.ndarray:
    """Convert an hourly system-wide MW series into a CF profile.

    Each hour's MW is divided by the capacity online in that hour's month
    (summed across zones in ``monthly_capacity``), giving a capacity factor
    per MW of online capacity. Passed to :func:`_distribute_by_eia860` with
    the vintage ramp, this reproduces the system MW total exactly while
    distributing it across zones by each zone's month-by-month capacity.
    """
    online_cap = monthly_capacity.sum(axis=0)[_hour_to_month_index(HOURS_PER_YEAR)]
    cf = np.divide(
        hourly_mw,
        online_cap,
        out=np.zeros_like(hourly_mw),
        where=online_cap > 0.0,
    )
    return np.clip(cf, _CF_MIN, _CF_MAX)


# Environment gate for sourcing the model's renewables inputs from the curated
# ``data/clean`` tree (via the shared read seam ``scripts.lib.clean_io``) rather
# than the raw HSL parquet tree. Default OFF: the raw GEN/HSL path is the
# shipped behavior and remains the fallback whenever a clean partition is
# absent. Flip ON (``MARKET_SIM_USE_CLEAN=1``) to read the schema-validated
# clean ``renewables`` table. The two sources are bit-identical — the curation
# (scripts/data/curate_renewables.py) is a pure unpivot of the wide HSL frame — so
# enabling the flag does not change model output (see tests/test_consume_renewables.py).
_USE_CLEAN_ENV: str = "MARKET_SIM_USE_CLEAN"
_USE_CLEAN_TRUE_TOKENS: frozenset[str] = frozenset({"1", "true", "yes", "on"})


def _use_clean() -> bool:
    """Whether to source renewables from ``data/clean`` (see ``MARKET_SIM_USE_CLEAN``)."""
    return os.environ.get(_USE_CLEAN_ENV, "").strip().lower() in _USE_CLEAN_TRUE_TOKENS


def _clean_io():  # type: ignore[no-untyped-def]
    """Lazily import the clean read seam (``scripts.lib.clean_io``).

    The seam lives at the repo root, outside the installed ``market_sim``
    package, so the repo root is added to ``sys.path`` if it is not already
    importable. Imported lazily so the default raw path never pays the cost.
    """
    try:
        from scripts.lib import clean_io
    except ModuleNotFoundError:
        import sys

        from market_sim.config.paths import REPO_ROOT

        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from scripts.lib import clean_io
    return clean_io


def _hsl_hourly_from_clean(iso: str, year: int) -> pd.DataFrame | None:
    """Rebuild the wide GEN/HSL frame from the clean ``renewables`` table.

    Reads the long, schema-validated clean partition
    (``data/clean/renewables/<iso>/renewables_<year>.parquet``) through
    :func:`scripts.lib.clean_io.read_clean` — loading wind/solar
    ``generation_mw``, ``hsl_mw`` and ``curtailment_mw`` — and pivots the
    ISO-wide (``zone == "SYSTEM"``) rows back to the wide ``_HSL_COLUMNS``
    layout the raw loader emits. Every downstream consumer (curtailment,
    :func:`hsl_potential_mw`, :func:`_hsl_cf_profile`) is therefore unchanged.

    Returns ``None`` when no clean partition covers ``(iso, year)`` (the caller
    then falls back to the raw parquet) or the partition is not a full year.
    """
    clean_io = _clean_io()
    if not clean_io.clean_exists("renewables", iso=iso, year=year):
        return None
    long = clean_io.read_clean(
        "renewables",
        iso=iso,
        year=year,
        columns=[
            "interval_start_utc",
            "zone",
            "fuel",
            "generation_mw",
            "hsl_mw",
            "curtailment_mw",
        ],
    )
    long = long[long["zone"] == "SYSTEM"]

    wide: dict[str, np.ndarray] = {}
    n_hours: int | None = None
    for fuel in _RENEWABLE_FUELS:
        rows = (
            long[long["fuel"] == fuel]
            .sort_values("interval_start_utc")
            .reset_index(drop=True)
        )
        if n_hours is None:
            n_hours = len(rows)
        elif len(rows) != n_hours:
            return None  # ragged per-fuel coverage — cannot form a wide frame
        wide[f"{fuel}_gen_mw"] = rows["generation_mw"].to_numpy(dtype=float)
        wide[f"{fuel}_hsl_mw"] = rows["hsl_mw"].to_numpy(dtype=float)
    if not n_hours:
        return None
    return pd.DataFrame({"hour": np.arange(n_hours), **wide})


def load_hsl_hourly(iso: str, year: int) -> pd.DataFrame | None:
    """Return the hourly GEN/HSL frame for ``(iso, year)``, or ``None``.

    The frame carries ``hour``, ``wind_gen_mw``, ``wind_hsl_mw``,
    ``solar_gen_mw`` and ``solar_hsl_mw`` — delivered generation and
    uncurtailed potential on the calibration's chronological clock — sorted
    by hour. ``hsl - gen`` is therefore the *reported* curtailment, the
    benchmark the calibration report compares modeled curtailment against.

    The frame is sourced from the raw per-year HSL parquet by default. When
    ``MARKET_SIM_USE_CLEAN`` is set (see :func:`_use_clean`) it is read from
    the curated ``data/clean`` tree instead, falling back to raw when no clean
    partition covers the pair.

    Returns ``None`` when no HSL-style source covers the pair or the source
    is not a clean full year.
    """
    df = None
    if _use_clean():
        df = _hsl_hourly_from_clean(iso, year)
    if df is None:
        df = _load_hsl_hourly_raw(iso, year)
    if df is None:
        return None
    if not set(_HSL_COLUMNS).issubset(df.columns) or len(df) != HOURS_PER_YEAR:
        return None
    return df.sort_values("hour").reset_index(drop=True)


def _load_hsl_hourly_raw(iso: str, year: int) -> pd.DataFrame | None:
    """Read the raw per-year GEN/HSL parquet under ``data/raw``, or ``None``.

    The shipped default source for :func:`load_hsl_hourly`: the wide HSL frame
    built by ``scripts/build_{ercot,caiso}_hsl.py``. Returns ``None`` when no
    parquet covers ``(iso, year)``; column/length validation is applied by the
    caller so the raw and clean sources are checked identically.
    """
    path = _hsl_file(iso, year)
    if path is None or not path.exists():
        return None
    return pd.read_parquet(path)


def _hsl_cf_profile(
    iso: str, year: int, fuel: str, monthly_capacity: np.ndarray
) -> np.ndarray | None:
    """Return an hourly uncurtailed-potential CF profile, or ``None``.

    An HSL-style dataset records the hourly wind/solar output available
    *before* curtailment — ERCOT's NP6 High Sustained Limit (per-year
    parquets), and the CAISO delivered-plus-reported-curtailment analogue
    (see :func:`_hsl_file`). Feeding that to the dispatch (rather than
    delivered generation) lets it re-curtail under the modeled transmission
    limits. Each series is chronological by the BA's local time on the fixed
    non-leap 8760-hour clock, matching the ``<BA> hourly`` demand.

    Returns ``None`` when no HSL data covers ``(iso, year, fuel)``.
    """
    hsl_mw = hsl_potential_mw(iso, year, fuel)
    if hsl_mw is None:
        return None
    return _mw_to_cf(hsl_mw, monthly_capacity)


def _eia_hourly_cf_profile(
    iso: str, year: int, fuel: str, monthly_capacity: np.ndarray
) -> np.ndarray | None:
    """Return a delivered-generation CF profile from the BA's hourly extract.

    For a backcast year the EIA-930 ``<BA> hourly`` net generation — resolved
    from the ISO to its balancing-authority extract by
    :func:`load_eia_hourly_renewable_gen` — supplies a wind/solar profile on
    the same chronological clock as the demand and interchange. It is
    delivered (already curtailed) output, so — like the EIA-930 generation
    distributions — the dispatch does not separately re-curtail it.

    Returns ``None`` when the ISO has no mapped hourly extract, no data
    covers the ``(year, fuel)`` pair, or the reported series sums to zero —
    all-zero signals a BA reporting gap rather than genuine zero generation
    (e.g., EIA-930 NYIS does not separately report solar), and the caller
    should fall back to the EIA-930 distribution-based profile.
    """
    gen = load_eia_hourly_renewable_gen(iso, year)
    if gen is None or fuel not in gen:
        return None
    mw = gen[fuel]
    if mw.sum() == 0.0:
        return None
    return _mw_to_cf(mw, monthly_capacity)


def _extract_fuel_values(profiles: pd.DataFrame, fuel: str) -> np.ndarray:
    """Return the hour-ordered EIA generation values for one fuel.

    Args:
        profiles: Generation-profile rows for a single ISO and year, as
            returned by :func:`load_generation_profiles`.
        fuel: Fuel identifier to extract, e.g. ``"wind"`` or ``"solar"``.

    Returns:
        A ``(HOURS_PER_YEAR,)`` array of normalized generation values,
        ordered by hour.

    Raises:
        AssertionError: if the fuel does not have a full year of hours.
    """
    rows = profiles[profiles["fuel"] == fuel].sort_values("hour")
    assert len(rows) == HOURS_PER_YEAR, (
        f"Expected {HOURS_PER_YEAR} hours for fuel '{fuel}', got {len(rows)}"
    )
    return rows["value"].to_numpy(dtype=float)


def _allocate_to_zones(
    cf_profile: np.ndarray,
    installed_mw: float,
    zone_names: list[str],
    target_zone: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Place a single CF profile and its capacity onto one ISO zone.

    All renewable output for the technology is assigned to ``target_zone``;
    every other zone receives a zero CF row and zero capacity.

    Args:
        cf_profile: A ``(HOURS_PER_YEAR,)`` hourly CF series.
        installed_mw: Installed nameplate capacity (MW) of the technology.
        zone_names: Ordered zone names of the ISO.
        target_zone: Name of the zone that absorbs the full fleet.

    Returns:
        A tuple ``(cf, cap)`` where ``cf`` is a ``(n_zones, HOURS_PER_YEAR)``
        array of hourly capacity factors and ``cap`` is a ``(n_zones,)``
        array of installed capacity in MW.

    Raises:
        ValueError: if ``target_zone`` is not among ``zone_names``.
    """
    if target_zone not in zone_names:
        raise ValueError(
            f"Allocation target zone '{target_zone}' not in ISO zones {zone_names}"
        )
    n_zones = len(zone_names)
    cf = np.zeros((n_zones, HOURS_PER_YEAR), dtype=float)
    cap = np.zeros(n_zones, dtype=float)
    idx = zone_names.index(target_zone)
    cf[idx] = cf_profile
    cap[idx] = installed_mw
    return cf, cap


def _clearsky_geometry(
    lat_deg: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return hourly clear-sky solar geometry at one latitude.

    Computes, for each of the ``HOURS_PER_YEAR`` hours, the solar declination,
    hour angle, cosine of the zenith angle, and a normalized clear-sky beam
    (DNI) series at the representative latitude ``lat_deg``. Standard formulae:
    Cooper's declination, the geometric hour angle about mid-hour solar noon,
    and the Meinel clear-sky beam attenuation ``τ**(AM**0.678)`` with a simple
    ``1/cos(zenith)`` air mass. The DNI is normalized to 1.0 at zenith and
    zeroed whenever the sun is below the horizon.

    Longitude/equation-of-time corrections are deliberately omitted: the SHAPE
    is only ever used *relatively* between zones at the same hour (the
    aggregate-reconciliation in :func:`_distribute_by_eia860` divides by the
    capacity-weighted mean shape), so a constant timing offset shared by all
    zones cancels. Latitude — which genuinely differs zone to zone — is kept.

    Args:
        lat_deg: Representative latitude in degrees north.

    Returns:
        ``(decl, omega, cos_zen, dni)`` each a ``(HOURS_PER_YEAR,)`` array:
        declination (rad), hour angle (rad), cosine of the zenith angle, and
        the normalized clear-sky beam.
    """
    hours = np.arange(HOURS_PER_YEAR)
    day_of_year = hours // 24 + 1  # 1..365
    solar_time = (hours % 24).astype(float) + 0.5  # mid-hour local solar time

    decl = np.deg2rad(_DECLINATION_MAX_DEG) * np.sin(
        2.0 * np.pi * (284 + day_of_year) / 365.0
    )
    omega = np.deg2rad(15.0 * (solar_time - 12.0))  # 15 deg per hour from noon
    phi = np.deg2rad(lat_deg)

    cos_zen = np.sin(phi) * np.sin(decl) + np.cos(phi) * np.cos(decl) * np.cos(omega)
    sun_up = cos_zen > 0.0

    air_mass = 1.0 / np.maximum(cos_zen, _COS_ZENITH_FLOOR)
    dni = _CLEARSKY_TRANSMITTANCE ** (air_mass**_CLEARSKY_AM_EXPONENT)
    dni = np.where(sun_up, dni, 0.0)
    return decl, omega, cos_zen, dni


def _clearsky_poa_by_tech(lat_deg: float) -> dict[str, np.ndarray]:
    """Return per-technology clear-sky plane-of-array output at one latitude.

    Builds a normalized hourly POA series (per MW of nameplate, in consistent
    clear-sky-DNI units) for the three EIA-860 solar tracking classes at
    ``lat_deg``:

    * **single_axis** — horizontal N–S axis tracker, ``cosθ = √(cos²z +
      cos²δ·sin²ω)`` (no backtracking): a wide midday plateau;
    * **fixed** — south-facing array tilted at the latitude,
      ``cosθ = cosδ·cosω``: a peaky midday cosine;
    * **dual_axis** — always normal to the sun, ``cosθ = 1``: the full DNI
      envelope, the broadest shape.

    Each adds a small isotropic clear-sky diffuse term so shoulder hours are
    non-zero. The three are intentionally *not* renormalized to equal annual
    energy — a tracker genuinely delivers more shoulder energy per nameplate
    MW than a fixed panel, and that physical difference is exactly what makes a
    high-tracking zone's shape flatter than a high-fixed-tilt zone's.

    Args:
        lat_deg: Representative latitude in degrees north.

    Returns:
        ``{tech: poa}`` where ``tech`` is one of ``single_axis`` / ``fixed`` /
        ``dual_axis`` and ``poa`` is a ``(HOURS_PER_YEAR,)`` array.
    """
    decl, omega, cos_zen, dni = _clearsky_geometry(lat_deg)
    sun_up = cos_zen > 0.0
    diffuse = _DIFFUSE_FRACTION * dni * np.maximum(cos_zen, 0.0)

    # Fixed tilt at latitude, south-facing: cosθ = cosδ·cosω (φ − β = 0).
    cos_aoi_fixed = np.cos(decl) * np.cos(omega)
    fixed = dni * np.maximum(cos_aoi_fixed, 0.0) + diffuse

    # Horizontal N–S single-axis tracker (ideal, no backtracking).
    cos_aoi_sat = np.sqrt(
        np.maximum(cos_zen, 0.0) ** 2 + np.cos(decl) ** 2 * np.sin(omega) ** 2
    )
    single_axis = dni * cos_aoi_sat + diffuse

    # Dual-axis: panel normal always tracks the sun (cosθ = 1).
    dual_axis = dni + diffuse

    return {
        "single_axis": np.where(sun_up, single_axis, 0.0),
        "fixed": np.where(sun_up, fixed, 0.0),
        "dual_axis": np.where(sun_up, dual_axis, 0.0),
    }


def _eia860_zone_solar_geometry(
    iso: str,
    zone_names: list[str],
    cal_year: int | None,
    data_dir: Path | None = None,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return per-zone solar tracking mix and capacity-weighted centroids.

    Reads the EIA-860 operable solar schedule, assigns each plant to a model
    zone (eGRID/EIA-860 ORIS→zone lookup, the same geography as
    :func:`_eia860_monthly_capacity`), and aggregates, weighted by nameplate
    capacity and restricted to plants online by ``cal_year``:

    * the tracking mix — the capacity fraction in each of single-axis / fixed /
      dual-axis (the three :data:`_SOLAR_TRACKING_FLAGS`); and
    * the representative latitude/longitude — the capacity-weighted centroid of
      the zone's plant coordinates (from ``eia860_plant.parquet``).

    Both are real, reproducible EIA-860 inputs that would regenerate for a
    forward year and respond to a changed fleet (rule #12).

    Args:
        iso: ISO identifier (only multi-zone solar ISOs are meaningful).
        zone_names: Ordered model-zone names of the ISO.
        cal_year: Calibration year; only plants online by its end are counted.
            ``None`` counts every operable plant.
        data_dir: EIA-860 directory; resolved from config when ``None``.

    Returns:
        ``(mix, centroid)`` where ``mix`` is ``(n_zones, 3)`` capacity
        fractions (single-axis, fixed, dual-axis) and ``centroid`` is
        ``(n_zones, 2)`` lat/lon, or ``None`` when the EIA-860 solar data or
        the ISO zone geography is unavailable.
    """
    file_name = _EIA860_OPERABLE_FILES.get("solar")
    if file_name is None:
        return None
    if data_dir is None:
        from market_sim.config.paths import active_eia860_dir

        data_dir = active_eia860_dir()
    path = Path(data_dir) / file_name
    plant_path = Path(data_dir) / "eia860_plant.parquet"
    if not path.exists() or not plant_path.exists():
        return None

    from market_sim.data.zone_assignment import build_zone_lookup

    try:
        zone_lookup = build_zone_lookup(iso)
    except Exception:
        return None
    if not zone_lookup:
        return None

    df = pd.read_parquet(path)
    df = df[df["Status"].astype(str).str.strip().str.upper() == "OP"]
    if cal_year is not None:
        op_year = pd.to_numeric(df["Operating Year"], errors="coerce")
        df = df[~(op_year > cal_year)]
    cap = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce")

    plants = pd.read_parquet(plant_path)[
        ["Plant Code", "Latitude", "Longitude"]
    ].drop_duplicates("Plant Code")
    lat = pd.to_numeric(
        df["Plant Code"].map(plants.set_index("Plant Code")["Latitude"]),
        errors="coerce",
    )
    lon = pd.to_numeric(
        df["Plant Code"].map(plants.set_index("Plant Code")["Longitude"]),
        errors="coerce",
    )
    zone = df["Plant Code"].map(
        lambda c: zone_lookup.get(_as_int(c)) if c == c else None
    )

    n_zones = len(zone_names)
    zone_to_idx = {name: i for i, name in enumerate(zone_names)}
    mix = np.zeros((n_zones, len(_SOLAR_TRACKING_FLAGS)), dtype=float)
    centroid = np.zeros((n_zones, 2), dtype=float)

    flags = {
        f: df[f].astype(str).str.strip().str.upper() == "Y"
        for f in _SOLAR_TRACKING_FLAGS
    }
    cap_arr = cap.to_numpy()
    lat_arr = lat.to_numpy()
    lon_arr = lon.to_numpy()
    zone_idx = np.array(
        [zone_to_idx.get(z, -1) if z is not None else -1 for z in zone], dtype=int
    )
    flag_cols = np.column_stack([flags[f].to_numpy() for f in _SOLAR_TRACKING_FLAGS])

    geo_weight = np.zeros(n_zones, dtype=float)  # capacity with valid lat/lon
    for z in range(n_zones):
        sel = zone_idx == z
        if not sel.any():
            continue
        zc = np.where(np.isnan(cap_arr[sel]), 0.0, cap_arr[sel])
        # Tracking mix: attribute each plant's capacity to the first flag set.
        for k in range(len(_SOLAR_TRACKING_FLAGS)):
            mix[z, k] = (zc * flag_cols[sel, k]).sum()
        # Capacity-weighted centroid over plants with coordinates.
        ll_ok = sel & ~np.isnan(lat_arr) & ~np.isnan(lon_arr) & ~np.isnan(cap_arr)
        w = np.where(np.isnan(cap_arr[ll_ok]), 0.0, cap_arr[ll_ok])
        if w.sum() > 0.0:
            centroid[z, 0] = np.average(lat_arr[ll_ok], weights=w)
            centroid[z, 1] = np.average(lon_arr[ll_ok], weights=w)
            geo_weight[z] = w.sum()

    # Normalize the tracking mix to fractions per zone (rows that have any
    # classified capacity); leave all-zero rows untouched (no solar there).
    row_sum = mix.sum(axis=1, keepdims=True)
    np.divide(mix, row_sum, out=mix, where=row_sum > 0.0)
    return mix, centroid


def _solar_zone_clearsky_shapes(
    iso: str,
    fuel: str,
    zone_names: list[str],
    cal_year: int | None,
    data_dir: Path | None = None,
) -> np.ndarray | None:
    """Return a per-zone clear-sky solar SHAPE matrix, or ``None`` (no-op).

    For a gated multi-zone solar ISO (see :data:`_SOLAR_ZONE_SHAPE_ISOS`) this
    blends the three clear-sky tracking-class shapes (see
    :func:`_clearsky_poa_by_tech`) at each zone's representative latitude by
    that zone's EIA-860 tracking mix (see
    :func:`_eia860_zone_solar_geometry`), giving each zone its own hourly solar
    SHAPE. The absolute level is irrelevant — the caller reconciles these
    shapes to the measured ISO-wide ``cf_profile`` — only the inter-zone
    differences (a higher-fixed-tilt zone peaks more sharply than a
    higher-tracking zone) survive.

    Returns ``None`` — signalling the caller to keep the legacy single-shape
    behaviour — for wind, for ISOs not in :data:`_SOLAR_ZONE_SHAPE_ISOS`, and
    whenever the EIA-860 tracking/geometry data is unavailable.

    Args:
        iso: ISO identifier.
        fuel: Renewable fuel; only ``"solar"`` is shaped.
        zone_names: Ordered model-zone names of the ISO.
        cal_year: Calibration year for the EIA-860 fleet snapshot.
        data_dir: EIA-860 directory; resolved from config when ``None``.

    Returns:
        A ``(n_zones, HOURS_PER_YEAR)`` clear-sky SHAPE array, or ``None``.
    """
    if fuel != "solar" or iso not in _SOLAR_ZONE_SHAPE_ISOS:
        return None
    geometry = _eia860_zone_solar_geometry(iso, zone_names, cal_year, data_dir)
    if geometry is None:
        return None
    mix, centroid = geometry

    n_zones = len(zone_names)
    shapes = np.zeros((n_zones, HOURS_PER_YEAR), dtype=float)
    # Cache POA by rounded latitude — neighbouring zones often share one.
    poa_cache: dict[float, dict[str, np.ndarray]] = {}
    tech_order = ("single_axis", "fixed", "dual_axis")
    for z in range(n_zones):
        if mix[z].sum() <= 0.0 or centroid[z, 0] == 0.0:
            continue  # no classified solar / no coordinates in this zone
        lat_key = round(float(centroid[z, 0]), 2)
        poa = poa_cache.get(lat_key)
        if poa is None:
            poa = _clearsky_poa_by_tech(lat_key)
            poa_cache[lat_key] = poa
        shapes[z] = sum(mix[z, k] * poa[tech_order[k]] for k in range(len(tech_order)))
    if not shapes.any():
        return None
    return shapes


# --- Degenerate EIA-930 distribution repair --------------------------------
# The EIA-930 generation-distribution parquet
# (data/raw/eia-930/eia_generation_profiles.parquet) is the last-resort profile
# source, taken only when a BA publishes no usable per-fuel hourly series (see
# :func:`_eia_hourly_cf_profile`). For one cell of the six-ISO grid that row is
# itself unusable: EIA-930 NYIS files `NG: SUN` as all zeros, so the NYISO solar
# distribution is a single repeated value over all 8760 hours — a CF that
# generates as much at 03:00 as at noon. Multiplied by the 12-step EIA-860
# monthly capacity ramp it yields the observed 12-distinct-value block.
#
# A flat 24-hour solar CF is physically impossible, so the row is repaired
# rather than consumed. The repair is applied to whichever ISO/fuel row is
# degenerate — this is a fallback-path defect, not a NYISO one — and is an exact
# no-op for every non-degenerate row (verified across all six ISOs x
# {wind, solar} x 2023-2025: NYISO solar is the only cell that both reaches this
# fallback and fails the test).
#
# A genuine measured 8760-hour series resolves hundreds to thousands of distinct
# values (the smallest observed in this parquet is 226). A year that resolves
# fewer distinct values than there are hours in a day carries no usable
# intra-day structure at all, which makes this an unambiguous defect test with a
# ~9x margin to the nearest real row.
_DEGENERATE_DISTINCT_VALUES: int = 24

# Donor ISO supplying the replacement SHAPE for a degenerate row. The donor must
# be an adjacent BA on the same local clock (so the measured diurnal timing
# transfers without a rotation) publishing a usable series for the same weather
# year. NEISO for NYISO: directly interconnected, both America/New_York, and
# capacity-weighted EIA-860 solar-fleet latitudes of 42.5 N (NYISO) vs 42.6 N
# (NEISO) — the same solar geometry to within a tenth of a degree.
_DEGENERATE_SHAPE_DONOR_ISO: dict[str, str] = {"NYISO": "NEISO"}

# Fraction of the donor's peak clear-sky POA below which the inter-ISO
# tracking-mix ratio is held at a neutral 1.0. Guards the ratio against a
# vanishing denominator in the deep-night hours where both fleets produce
# nothing, so the correction cannot amplify numerical dust into energy.
_POA_RATIO_FLOOR_FRACTION: float = 0.01


def _is_diurnally_degenerate(values: np.ndarray) -> bool:
    """Whether an EIA-930 distribution row carries no intra-day structure.

    Args:
        values: A ``(HOURS_PER_YEAR,)`` normalized EIA generation distribution.

    Returns:
        ``True`` when the row resolves fewer than
        :data:`_DEGENERATE_DISTINCT_VALUES` distinct values (a reporting gap
        filed as a constant), ``False`` for any genuine measured series.
    """
    if values.size == 0 or not np.isfinite(values).all() or values.sum() <= 0.0:
        return False
    return len(np.unique(values)) < _DEGENERATE_DISTINCT_VALUES


def _iso_clearsky_poa(
    iso: str, cal_year: int | None, data_dir: Path | None = None
) -> np.ndarray | None:
    """Return an ISO-wide capacity-weighted clear-sky solar POA series.

    Collapses :func:`_eia860_zone_solar_geometry`'s per-zone tracking mix and
    latitude centroids into one ISO-level clear-sky plane-of-array profile,
    weighting each zone by its year-end EIA-860 solar capacity. Used only as
    the numerator/denominator of a *ratio* between two ISOs (see
    :func:`_donor_shaped_distribution`), which is the sole contract
    :func:`_clearsky_geometry` supports — its omitted longitude/equation-of-time
    term is a constant offset shared by both ISOs and cancels in the ratio.

    Args:
        iso: ISO identifier.
        cal_year: Calibration year; only plants online by its end are counted.
        data_dir: EIA-860 directory; resolved from config when ``None``.

    Returns:
        A ``(HOURS_PER_YEAR,)`` POA array, or ``None`` when the ISO has no
        usable EIA-860 solar geometry or capacity.
    """
    zone_names = get_iso_config(iso).zone_names
    geometry = _eia860_zone_solar_geometry(iso, zone_names, cal_year, data_dir)
    if geometry is None:
        return None
    mix, centroid = geometry
    monthly = _eia860_monthly_capacity(iso, "solar", zone_names, cal_year)
    if monthly is None:
        return None
    weights = monthly[:, -1]  # year-end installed capacity per zone
    tech_order = ("single_axis", "fixed", "dual_axis")
    poa = np.zeros(HOURS_PER_YEAR, dtype=float)
    total = 0.0
    poa_cache: dict[float, dict[str, np.ndarray]] = {}
    for z in range(len(zone_names)):
        if weights[z] <= 0.0 or mix[z].sum() <= 0.0 or centroid[z, 0] == 0.0:
            continue
        lat_key = round(float(centroid[z, 0]), 2)
        by_tech = poa_cache.get(lat_key)
        if by_tech is None:
            by_tech = _clearsky_poa_by_tech(lat_key)
            poa_cache[lat_key] = by_tech
        poa += weights[z] * sum(
            mix[z, k] * by_tech[tech_order[k]] for k in range(len(tech_order))
        )
        total += weights[z]
    if total <= 0.0 or not poa.any():
        return None
    return poa / total


def _donor_shaped_distribution(
    iso: str, year: int, fuel: str, data_dir: Path = DATA_DIR
) -> np.ndarray | None:
    """Rebuild a degenerate distribution row from an adjacent BA's shape.

    Replaces the *shape* of an unusable EIA-930 distribution row while leaving
    its *level* untouched: the result is renormalized to sum to 1.0, so the
    downstream :func:`derive_cf_profile` still sets the annual mean CF from
    :data:`RENEWABLE_AVG_CF` exactly as before. Nothing here is fitted to a
    price or volume residual (CLAUDE.md rule 1 ``[R-STRUCT]``, rule 13
    ``[R-MEASURED]``).

    The donor's measured series supplies the diurnal timing, the day-to-day
    cloud variability and the seasonality, all on the same weather year and the
    same local clock. For solar it is additionally corrected for the two
    fleets' different EIA-860 tracking mixes by the clear-sky POA ratio
    ``POA_iso / POA_donor`` — NYISO is 30.5% single-axis tracking against
    NEISO's 13.3%, and a tracker genuinely delivers more shoulder-hour energy
    per nameplate MW than a fixed panel. Both POAs sit on one clock, so the
    ratio is phase-free (see :func:`_iso_clearsky_poa`).

    Forward-valid (rule 13): the donor series and the EIA-860 tracking mix both
    regenerate for any future year and respond to a changed fleet and a changed
    weather year.

    Args:
        iso: ISO whose distribution row is degenerate.
        year: Calendar year of the row.
        fuel: Fuel identifier, e.g. ``"solar"``.
        data_dir: EIA-930 directory holding the generation-profiles parquet.

    Returns:
        A ``(HOURS_PER_YEAR,)`` normalized distribution summing to 1.0, or
        ``None`` when no donor is registered or the donor is itself unusable —
        in which case the caller keeps the original row.
    """
    donor = _DEGENERATE_SHAPE_DONOR_ISO.get(iso)
    if donor is None:
        return None
    try:
        donor_rows = load_generation_profiles(donor, year, data_dir)
        shape = _extract_fuel_values(donor_rows, fuel)
    except (AssertionError, FileNotFoundError, KeyError, ValueError):
        logger.warning(
            "No usable %s donor row (%s %d) to repair degenerate %s %s profile",
            fuel,
            donor,
            year,
            iso,
            fuel,
        )
        return None
    if _is_diurnally_degenerate(shape) or shape.sum() <= 0.0:
        return None

    shape = shape.astype(float).copy()
    if fuel == "solar":
        poa_iso = _iso_clearsky_poa(iso, year)
        poa_donor = _iso_clearsky_poa(donor, year)
        if poa_iso is not None and poa_donor is not None:
            # The ratio is only meaningful where the donor's clear-sky envelope
            # is materially above zero; night hours keep a neutral 1.0 (both
            # series are ~0 there, so the choice cannot move energy).
            ratio = np.ones(HOURS_PER_YEAR, dtype=float)
            lit = poa_donor > _POA_RATIO_FLOOR_FRACTION * poa_donor.max()
            ratio[lit] = poa_iso[lit] / poa_donor[lit]
            shape = shape * ratio
    total = shape.sum()
    if total <= 0.0:
        return None
    return shape / total


# Columns of a per-year MISO wind-shape parquet: the hour index plus one
# relative-SHAPE column per model zone (the zone's MERRA-2-derived turbine CF on
# the model's 8760 clock). Absolute level is irrelevant — the caller reconciles
# these to the measured EIA-930 ISO-wide series — only the inter-zone shape
# differences survive. Built by scripts/data/build_miso_wind_shape.py.
_WIND_SHAPE_HOUR_COLUMN: str = "hour"


def _wind_zone_reanalysis_shapes(
    iso: str,
    fuel: str,
    zone_names: list[str],
    cal_year: int | None,
    data_dir: Path | None = None,
    config: ScenarioConfig | None = None,
) -> np.ndarray | None:
    """Return a per-zone reanalysis wind SHAPE matrix, or ``None`` (no-op).

    For a gated multi-zone wind ISO (see :data:`_WIND_ZONE_SHAPE_ISOS`) this
    reads the precomputed per-year wind-shape parquet (built offline by
    scripts/data/build_miso_wind_shape.py from MERRA-2 reanalysis wind speed at the
    ISO's EIA-860 wind-plant locations, run through a turbine power curve) and
    returns one relative hourly SHAPE per model zone. The absolute level is
    irrelevant — the caller reconciles these shapes to the measured ISO-wide
    ``cf_profile`` (see :func:`_redistribute_preserving_total`) — only the
    inter-zone differences (the upper-plains nocturnal-jet North vs the flatter
    Central/South) survive.

    Returns ``None`` — signalling the caller to keep the legacy single-shape
    behaviour — for non-wind fuels, for ISOs not in
    :data:`_WIND_ZONE_SHAPE_ISOS`, and whenever the parquet is absent or does
    not carry a column for every model zone.

    Args:
        iso: ISO identifier.
        fuel: Renewable fuel; only ``"wind"`` is shaped here.
        zone_names: Ordered model-zone names of the ISO.
        cal_year: Calibration year selecting the per-year parquet.
        data_dir: Wind-shape directory; resolved from the per-ISO path registry
            (:func:`market_sim.config.paths.wind_shape_dir`) when ``None``.
        config: Scenario config carrying the per-ISO gate for the
            keeper-affecting ISOs (see :data:`_WIND_ZONE_SHAPE_GATES`).

    Returns:
        A ``(n_zones, HOURS_PER_YEAR)`` relative wind SHAPE array, or ``None``.
    """
    if fuel != "wind" or cal_year is None:
        return None
    if not _wind_zone_shape_enabled(iso, config):
        return None
    if data_dir is None:
        # Per-ISO registry, not a hardcoded MISO default — an ISO with no
        # registered directory resolves to None and no-ops below.
        data_dir = wind_shape_dir(iso)
    if data_dir is None:
        return None
    path = Path(data_dir) / f"{iso.lower()}_{cal_year}_wind_zone_shape.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if not set(zone_names) <= set(df.columns) or len(df) != HOURS_PER_YEAR:
        return None
    # Order columns to match the model zone order; the parquet is hour-sorted.
    df = df.sort_values(_WIND_SHAPE_HOUR_COLUMN)
    shapes = df[zone_names].to_numpy(dtype=float).T  # (n_zones, HOURS_PER_YEAR)
    shapes = np.where(np.isfinite(shapes), shapes, 0.0)
    shapes = np.clip(shapes, 0.0, None)
    if not shapes.any():
        return None
    # Arming proof: an overlay that silently no-ops through a full solve is the
    # ERCOT-113 silent-inertness trap, so every fired per-zone wind SHAPE
    # announces itself with the ISO, year and the measured night/afternoon
    # ratio per zone — the same statistic the gate's provenance cites, so the
    # log line is directly checkable against the source data.
    night = shapes[:, _wind_shape_hour_mask(0, 6)].mean(axis=1)
    aft = shapes[:, _wind_shape_hour_mask(12, 18)].mean(axis=1)
    ratio = np.divide(night, aft, out=np.ones_like(night), where=aft > 0)
    logger.info(
        "%s per-zone wind SHAPE (%d): %d zone(s) from %s, "
        "measured night/afternoon ratio %s",
        iso,
        cal_year,
        shapes.shape[0],
        path.name,
        ", ".join(f"{z}={r:.2f}" for z, r in zip(zone_names, ratio)),
    )
    return shapes


def _wind_shape_hour_mask(start_hour: int, end_hour: int) -> np.ndarray:
    """Boolean mask over the 8760 clock for a daily hour-of-day window.

    Used only for the per-zone wind SHAPE's arming-proof log line, which
    reports each zone's night(00-06) vs afternoon(12-18) mean so an armed run
    can be checked against the measured ratios without a re-solve.

    Args:
        start_hour: Inclusive hour-of-day the window opens.
        end_hour: Exclusive hour-of-day the window closes.

    Returns:
        A ``(HOURS_PER_YEAR,)`` boolean mask.
    """
    hod = np.arange(HOURS_PER_YEAR) % 24
    return (hod >= start_hour) & (hod < end_hour)


def _zone_renewable_shapes(
    iso: str,
    fuel: str,
    zone_names: list[str],
    cal_year: int | None,
    config: ScenarioConfig | None = None,
) -> np.ndarray | None:
    """Return the per-zone relative SHAPE for a fuel, or ``None`` (no-op).

    Dispatches to the fuel-appropriate per-zone shaper: a clear-sky geometry
    SHAPE for solar in the gated solar ISOs (see
    :func:`_solar_zone_clearsky_shapes`) and a MERRA-2 reanalysis SHAPE for wind
    in the gated wind ISOs (see :func:`_wind_zone_reanalysis_shapes`). Returns
    ``None`` for any other (iso, fuel), so the caller keeps the legacy
    single-ISO-wide-shape behaviour. Both shapers preserve the measured
    ISO-wide aggregate exactly; only the inter-zone split changes.

    Args:
        iso: ISO identifier.
        fuel: Renewable fuel (``"wind"`` or ``"solar"``).
        zone_names: Ordered model-zone names of the ISO.
        cal_year: Calibration year for the per-zone snapshot.
        config: Scenario config carrying the per-ISO wind-shape gate.

    Returns:
        A ``(n_zones, HOURS_PER_YEAR)`` relative SHAPE array, or ``None``.
    """
    if fuel == "solar":
        return _solar_zone_clearsky_shapes(iso, fuel, zone_names, cal_year)
    if fuel == "wind":
        return _wind_zone_reanalysis_shapes(
            iso, fuel, zone_names, cal_year, config=config
        )
    return None


def _redistribute_preserving_total(
    cf_profile: np.ndarray,
    cap: np.ndarray,
    ramp_t: np.ndarray,
    zone_shapes: np.ndarray,
) -> np.ndarray:
    """Re-split the flat system renewable series across zones by relative shape.

    The flat path puts ``cf_profile · ramp_z`` on every online zone, for a
    system series ``M(t) = Σ_z cap_z·cf_profile·ramp_z``. This keeps that exact
    ``M(t)`` but re-splits it across zones in proportion to each zone's
    shape-weighted online capacity ``cap_z·ramp_z·SHAPE_z(t)``::

        m_z(t)  = M(t) · (cap_z·ramp_z·SHAPE_z) / Σ_k(cap_k·ramp_k·SHAPE_k)
        cf_z(t) = m_z(t) / cap_z

    so the capacity-weighted aggregate ``Σ_z cap_z·cf_z`` reproduces the flat
    path every hour (annual energy and the system shape unchanged) while a
    high-shape zone (a high-fixed-tilt CAISO zone, or MISO's nocturnal-jet
    North) peaks at a different time than a low-shape zone. Dark/calm hours —
    no shape-weighted potential anywhere — fall back to the flat split, which
    preserves the same total.

    The proportional split alone can drive a small-capacity zone's CF above 1
    when a large zone is becalmed (its share of ``M(t)`` is forced onto the
    others) — possible for wind, where zones' instantaneous shapes diverge
    sharply, but not for solar, where zones co-vary. To keep the aggregate
    exact *and* every CF ≤ 1, the split is done by capacity-aware water-filling:
    a zone is never allocated above its online MW (``cap_z·ramp_z``); any
    overflow spills to zones with remaining headroom over at most ``n_zones``
    passes. With no overflow (the solar case) the first pass allocates the full
    proportional split and the result is unchanged.

    Args:
        cf_profile: ``(HOURS_PER_YEAR,)`` ISO-wide hourly CF series.
        cap: ``(n_zones,)`` December nameplate capacity (MW) per zone.
        ramp_t: ``(n_zones, HOURS_PER_YEAR)`` online-capacity fraction per
            zone-hour (the vintage ramp; all ones when the ramp is off).
        zone_shapes: ``(n_zones, HOURS_PER_YEAR)`` relative per-zone SHAPE.

    Returns:
        A ``(n_zones, HOURS_PER_YEAR)`` per-zone CF array.
    """
    cap_present = cap[:, None] * ramp_t  # online MW per zone-hour
    system_mw = cf_profile * cap_present.sum(axis=0)  # M(t) to distribute
    weight = cap_present * zone_shapes  # shape-weighted online MW per zone
    wsum = weight.sum(axis=0)

    cf = cf_profile[None, :] * ramp_t  # flat fallback (also preserves M)
    lit = wsum > 0.0

    # Capacity-aware water-filling. n_zones is tiny (<= ~6); each pass spreads
    # the still-unallocated MW over zones that have not yet hit their online-MW
    # ceiling, in proportion to their shape weight, and caps each at headroom.
    # When the shape weight of every zone with headroom is exhausted but MW
    # remains (a zone with capacity but a near-zero shape that hour, e.g. a
    # becalmed wind zone), the residual spills by remaining headroom instead —
    # the measured EIA-930 aggregate is authoritative, so it is placed in the
    # zones that can physically carry it. One extra pass covers that fallback.
    n_zones = weight.shape[0]
    alloc = np.zeros_like(weight)
    remaining = np.where(lit, system_mw, 0.0)
    for _ in range(n_zones + 1):  # shape passes + one headroom-fallback pass
        headroom = cap_present - alloc
        spill_weight = np.where(headroom > _REDISTRIBUTE_MW_EPS, weight, 0.0)
        ws = spill_weight.sum(axis=0)
        # Hours whose shape weight is used up but still owe MW: weight by
        # remaining headroom so the residual lands where capacity exists.
        use_headroom = (ws <= 0.0) & (remaining > _REDISTRIBUTE_MW_EPS)
        spill_weight[:, use_headroom] = np.where(
            headroom[:, use_headroom] > _REDISTRIBUTE_MW_EPS,
            headroom[:, use_headroom],
            0.0,
        )
        ws = spill_weight.sum(axis=0)
        move = (ws > 0.0) & (remaining > _REDISTRIBUTE_MW_EPS)
        if not move.any():
            break
        proposed = np.zeros_like(weight)
        proposed[:, move] = remaining[move] * spill_weight[:, move] / ws[move]
        add = np.minimum(proposed, headroom)
        alloc += add
        remaining = remaining - add.sum(axis=0)

    with np.errstate(divide="ignore", invalid="ignore"):
        shaped = np.where(cap[:, None] > 0.0, alloc / cap[:, None], 0.0)
    cf[:, lit] = shaped[:, lit]
    return np.clip(cf, _CF_MIN, _CF_MAX)


def _distribute_by_eia860(
    cf_profile: np.ndarray,
    installed_mw: float,
    monthly_capacity: np.ndarray,
    vintage_capacity_ramp: bool,
    zone_shapes: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Spread one ISO-wide CF profile across zones using EIA-860 capacity.

    The total ISO ``installed_mw`` is split across zones in proportion to
    each zone's December (year-end) capacity from ``monthly_capacity`` (see
    :func:`_eia860_monthly_capacity`); that December split is returned as the
    static per-zone capacity array.

    When ``vintage_capacity_ramp`` is ``True`` the shared profile is scaled,
    per zone and per month, by the fraction of year-end capacity online that
    month (``monthly_cap[z, month(t)] / december_cap[z]``), so a zone's modeled
    output ramps up as its plants reach commercial operation; when ``False``
    every zone with capacity uses the flat year-end profile.

    The shared ``cf_profile`` is placed on each zone in one of two ways:

    * **flat** (default) — every online zone uses the identical ISO-wide
      profile (times its ramp); or
    * **shape-redistributed** — when ``zone_shapes`` is supplied, the same
      hourly system total is re-split across zones by their relative clear-sky
      shapes (see :func:`_redistribute_preserving_total`), giving e.g. CAISO's
      NP15 a sharper midday solar peak than the more-tracking SP15 *without*
      changing the validated capacity-weighted system series.

    Args:
        cf_profile: A ``(HOURS_PER_YEAR,)`` ISO-wide hourly CF series.
        installed_mw: Total ISO installed nameplate capacity (MW).
        monthly_capacity: ``(n_zones, 12)`` operable capacity by month.
        vintage_capacity_ramp: Whether to apply the monthly capacity ramp.
        zone_shapes: Optional ``(n_zones, HOURS_PER_YEAR)`` relative per-zone
            SHAPE; when given, the profile is spatially redistributed (system
            series preserved exactly) instead of applied flat.

    Returns:
        A tuple ``(cf, cap)`` where ``cf`` is ``(n_zones, HOURS_PER_YEAR)``
        and ``cap`` is ``(n_zones,)`` December capacity in MW.
    """
    n_zones = monthly_capacity.shape[0]
    hours = cf_profile.shape[0]
    december = monthly_capacity[:, -1]
    cap = installed_mw * december / december.sum()

    # Per-zone, per-hour online-capacity fraction (the vintage ramp). With the
    # ramp off every zone with capacity is online all year (fraction 1); zones
    # with no year-end capacity stay at 0. n_zones is small (<= ~6) — this is
    # not an hour loop.
    online = (december > 0.0).astype(float)
    if vintage_capacity_ramp:
        month_idx = _hour_to_month_index(hours)
        ramp_t = np.zeros((n_zones, hours), dtype=float)
        for z in range(n_zones):
            if december[z] > 0.0:
                ramp_t[z] = (monthly_capacity[z] / december[z])[month_idx]
    else:
        ramp_t = np.tile(online[:, None], (1, hours))

    if zone_shapes is not None:
        cf = _redistribute_preserving_total(cf_profile, cap, ramp_t, zone_shapes)
    else:
        cf = cf_profile[None, :] * ramp_t
    return cf, cap


def load_renewable_profiles(
    iso: str,
    year: int,
    iso_config: ISOConfig,
    config: ScenarioConfig,
    data_dir: Path = DATA_DIR,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load zonal wind and solar CF profiles and capacities for an ISO.

    Hourly CF profiles are derived from the EIA-930 generation
    distributions (see :func:`derive_cf_profile` and the module docstring),
    scaled by the calibration knob ``config.renewable_cf_adjustment`` and
    re-clipped to ``[0, 1]``. Backcasts instead use measured hourly profiles
    on the calibration's chronological clock: an uncurtailed HSL-style series
    where one covers the ISO-year — ERCOT years with a built NP6 HSL
    parquet, CAISO's delivered-plus-reported-curtailment analogue — so the
    dispatch re-curtails (see :func:`_hsl_cf_profile`). When no HSL parquet
    covers the ISO-year-tech, a high-curtailment fallback ISO
    (:data:`_UNCURTAILED_FALLBACK_ISOS`) instead gets a forecast uncurtailed CF
    (the weather-year delivered profile grossed up by the per-tech reference
    curtailment rate from a *different* source year — a recent HSL year, or the
    Potomac Economics measured annual wind rate for MISO — so the potential is
    always >= delivered; see :func:`_forecast_uncurtailed_cf`) so the dispatch
    still re-curtails, while every other ISO/tech uses the delivered
    ``<BA> hourly`` net generation for its balancing authority (see
    :func:`_eia_hourly_cf_profile`).

    Each technology's installed capacity is distributed across the ISO's
    zones from EIA-860 plant locations (see :func:`_eia860_zone_shares`),
    with the same ISO-wide CF profile applied to every zone holding
    capacity — except in the gated multi-zone ISOs, where each zone instead
    gets its own per-zone SHAPE (see :func:`_zone_renewable_shapes`): solar in
    CAISO from each zone's EIA-860 tracking mix and latitude
    (:func:`_solar_zone_clearsky_shapes`), and wind in MISO from MERRA-2
    reanalysis at each zone's EIA-860 wind-plant locations through a turbine
    power curve (:func:`_wind_zone_reanalysis_shapes`), so the nocturnal-jet
    North differs from Central/South. That redistribution preserves the
    measured ISO aggregate exactly, so annual energy and the system shape are
    unchanged. When
    ``config.vintage_capacity_ramp`` is enabled, the per-zone profile is
    additionally scaled month-by-month so a zone's output ramps up as its
    plants reach their EIA-860 commercial-operation dates. For ISOs without
    EIA-860 geographic data the loader falls back to the single-zone
    :data:`RENEWABLE_ZONE_ALLOCATION` mapping. Zones with no capacity —
    including CAISO's ``WECC_import`` node — receive zero CF and zero
    capacity.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calendar year to load; also the calibration year for the
            EIA-860 vintage capacity ramp.
        iso_config: Topology configuration supplying the ordered zones.
        config: Scenario configuration; ``renewable_cf_adjustment`` scales
            every derived CF and ``vintage_capacity_ramp`` toggles the
            month-varying capacity ramp.
        data_dir: Directory containing the EIA-930 parquet extracts.

    Returns:
        A tuple ``(wind_cf, wind_cap, solar_cf, solar_cap)`` where ``wind_cf``
        and ``solar_cf`` are ``(n_zones, HOURS_PER_YEAR)`` arrays of hourly
        capacity factors and ``wind_cap`` and ``solar_cap`` are
        ``(n_zones,)`` arrays of installed capacity in MW. All arrays are
        ordered to match ``iso_config.zones``.

    Raises:
        ValueError: if no EIA data matches ``(iso, year)`` or if a zone
            allocation target is unknown for the ISO.
    """
    zone_names = iso_config.zone_names
    profiles: pd.DataFrame | None = None

    def _eia930_cf(fuel: str) -> np.ndarray:
        """Build the EIA-930 delivered-generation CF profile for one fuel."""
        nonlocal profiles
        if profiles is None:
            profiles = load_generation_profiles(iso, year, data_dir)
        values = _extract_fuel_values(profiles, fuel)
        if _is_diurnally_degenerate(values):
            # The BA filed this fuel as a constant (a reporting gap, not a
            # measurement): rebuild the SHAPE from an adjacent BA on the same
            # clock, keeping the annual level. No-op for every genuine row.
            repaired = _donor_shaped_distribution(iso, year, fuel, data_dir)
            if repaired is not None:
                logger.info(
                    "Repaired degenerate %s %d %s distribution from donor %s",
                    iso,
                    year,
                    fuel,
                    _DEGENERATE_SHAPE_DONOR_ISO[iso],
                )
                values = repaired
        cf = derive_cf_profile(values, RENEWABLE_AVG_CF[iso][fuel])
        return np.clip(cf * config.renewable_cf_adjustment, _CF_MIN, _CF_MAX)

    def _monthly_capacity(fuel: str, cal_year: int | None) -> np.ndarray | None:
        """Return the ``(n_zones, 12)`` operable capacity for one fuel-year.

        Wraps :func:`_eia860_monthly_capacity` with the one ISO-specific
        capacity-basis swap that has to travel with it (NYISO market solar), so
        every caller resolves the same population.

        Args:
            fuel: ``"wind"`` or ``"solar"``.
            cal_year: Calendar year whose COD/retirement ramp is applied, or
                ``None`` to treat every operable plant as online all year.

        Returns:
            The monthly capacity array, or ``None`` when no EIA-860 capacity
            resolves for the ISO-fuel (the caller then falls back to the
            hardcoded single-zone allocation).
        """
        monthly = _eia860_monthly_capacity(iso, fuel, zone_names, cal_year)
        if (
            fuel == "solar"
            and iso == "NYISO"
            and getattr(config, "nyiso_solar_market_generator_basis", False)
        ):
            # Rule 14 [R-ACCURATE] basis swap: EIA-860's NY utility-scale solar
            # population includes ~2 GW of distribution-connected community
            # solar that is not a NYISO market generator and is already netted
            # out of the EIA-930 NYIS demand series used as load, so carrying it
            # here double-counts it. Replace the capacity basis with NYISO's own
            # Table III-2a registry; everything downstream (installed_mw, the
            # zone split, the vintage ramp) follows unchanged. See
            # data.nyiso_market_solar for the identification and the declared
            # CF-basis limitation.
            #
            # WHICH published in-service date starts each plant is settled and
            # UNCONDITIONAL since 2026-08-15 (nyiso-136, owner ruling; rule 26
            # [R-DELETE] collapse of the nyiso-133 gate, promoted to keeper at
            # nyiso-135). It is EIA-860's Operating Month — the plant's metered
            # commercial start, matching the first METERED month of output in 11
            # of 12 uncensored plants — never the Gold Book's own
            # registration / interconnection-service date, which LEADS it and is
            # signed BOTH ways (Darby -1, Stillwater -3 against Morris Ridge +2,
            # High River +1, East Point +1). Same membership, same published
            # nameplate — only the switch-on month. There is no longer a flag:
            # a default-off gate whose OFF position is the less accurate basis is
            # a re-armable wrong answer.
            registered = load_market_solar_monthly(
                iso,
                cal_year,
                zone_names,
                cod_basis=True,
            )
            if registered is not None:
                monthly = registered
        return monthly

    # A capacity hindcast (W2-P5) is ``mode="forecast"`` + ``hindcast=True``, so
    # it does NOT take the backcast branch below — yet it initialises from a
    # vintage EIA-860 snapshot and evolves forward from it exactly as a backcast
    # base year would. Before FFR-3V-FIX it therefore fell through to
    # RENEWABLE_INSTALLED_MW, the canonical PRESENT-DAY forward-projection base:
    # a vintage-2020 MISO hindcast seeded 7,000 MW of solar against the 2,048 MW
    # that existed at its own cutoff (3.4x), and ERCOT 38,000 against 4,864
    # (7.8x) — post-vintage information inside a run whose entire premise is the
    # vintage cutoff, and a base the evolution channels then ADD to
    # (runner.py wind_cap[z] += additions), so any injected/screened MW
    # double-counts on an already-inflated pool. Resolve the run's own vintage
    # once here; the pools are seeded from THAT year's measured EIA-860 fleet
    # instead (rule 13 [R-MEASURED]: the vintage sheet is exactly what a run at
    # that cutoff may know, and it regenerates for any vintage; rule 14
    # [R-ACCURATE]: measured beats the constant). ``None`` for a plain forecast
    # and for a hindcast carrying no vintage — both keep the constant, so the
    # production forecast path is untouched. See
    # docs/handoffs/ffr-3v-fix-2026-08-08.md.
    hindcast_vintage: int | None = None
    if (
        config.mode != "backcast"
        and getattr(config, "hindcast", False)
        and config.eia860_vintage_year is not None
    ):
        hindcast_vintage = int(config.eia860_vintage_year)

    allocated: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for fuel in _RENEWABLE_FUELS:
        monthly = _monthly_capacity(fuel, year)
        if monthly is not None:
            # A calibration backcast (config.mode == "backcast", set
            # explicitly — never inferred from gas_price_override) is
            # pinned to a historical year, so the installed capacity is
            # that year's EIA-860 year-end total rather than
            # RENEWABLE_INSTALLED_MW — the current-fleet base used as the
            # starting point for forward projections.
            is_backcast = config.mode == "backcast"
            # The hindcast seed is read at the VINTAGE year, not at the weather
            # year: ``year`` here is the fixed weather year (2024 by default for
            # a plain hindcast), and reading the vintage sheet at 2024 also
            # switches on _add_proposed_capacity, which grafts the vintage's own
            # 2021-2024 proposed pipeline onto the "base" fleet (ERCOT solar
            # 4,864 -> 12,831 MW) — precisely the post-vintage additions the
            # evolution pipeline is supposed to decide for itself. Seeding at
            # the vintage year takes the year-end measured fleet and nothing
            # else, and it carries the zone split with it so the base pool's
            # geography is the vintage's too.
            seed_monthly = (
                _monthly_capacity(fuel, hindcast_vintage)
                if (hindcast_vintage is not None and not is_backcast)
                else None
            )
            hindcast_seeded = False
            if is_backcast:
                installed_mw = float(monthly[:, -1].sum())
            elif seed_monthly is not None:
                monthly = seed_monthly
                installed_mw = float(seed_monthly[:, -1].sum())
                hindcast_seeded = True
            else:
                if hindcast_vintage is not None:
                    # The weather-year read resolved but the vintage-year read
                    # did not (no operable capacity for this ISO-fuel at the
                    # cutoff). Nothing measured to seed from, so the constant
                    # stands — the pre-FFR-3V-FIX behaviour — but say so, because
                    # an unnoticed fall-back here is the original defect.
                    logger.warning(
                        "%s %s: hindcast vintage %d has no operable EIA-860 "
                        "capacity; seeding from RENEWABLE_INSTALLED_MW "
                        "(%.0f MW) — a PRESENT-DAY base in a vintage run",
                        iso,
                        fuel,
                        hindcast_vintage,
                        RENEWABLE_INSTALLED_MW[iso][fuel],
                    )
                installed_mw = RENEWABLE_INSTALLED_MW[iso][fuel]
            # A backcast prefers a measured hourly profile on the
            # calibration's chronological clock: an uncurtailed HSL-style
            # series where one exists (ERCOT years with a built HSL parquet,
            # CAISO covered years). Both are normalized per MW of online
            # capacity, so the vintage ramp distributes them across zones, and
            # neither takes the CF knob tuned to EIA-930 data. When no HSL
            # parquet covers the ISO-year-tech the fallback splits by ISO and
            # tech: a high-curtailment fallback ISO
            # (:data:`_UNCURTAILED_FALLBACK_ISOS`) with a reference curtailment
            # rate for this tech (ERCOT/CAISO wind & solar, MISO wind) is handed
            # the *forecast* per-tech uncurtailed CF below so the dispatch
            # re-curtails endogenously; everything else (other ISOs, and MISO
            # solar — which has no published curtailment series) keeps the
            # delivered ``<BA> hourly`` net generation (its documented default —
            # sub-1%/yr or unmeasured curtailment that re-curtailment would not
            # move).
            measured_cf = None
            if is_backcast:
                measured_cf = _hsl_cf_profile(iso, year, fuel, monthly)
                if measured_cf is None and iso in _UNCURTAILED_FALLBACK_ISOS:
                    # No HSL parquet for a high-curtailment ISO-year: hand the
                    # dispatch the forecast uncurtailed CF — the weather-year
                    # delivered profile grossed up by the per-tech reference
                    # curtailment rate from the ISO's most recent HSL year — so
                    # the LP re-curtails endogenously instead of inheriting the
                    # curtailment baked into delivered output (see
                    # :func:`_forecast_uncurtailed_cf`).
                    #
                    # SPP-51c: when ``vre_curtailment_oversupply_allocation`` is
                    # armed the SAME frozen annual energy is instead allocated
                    # onto the hours the system had nowhere to put it, rather
                    # than uniformly across all 8,760 (rule 19 [R-ONE-MECH]: it
                    # REPLACES the flat gross-up, never stacks on it). Any
                    # unavailable leg returns ``None`` and falls back here, so
                    # an armed run can never silently lose the headroom.
                    #
                    # SPP-58, rule 19 [R-ONE-MECH] enforced IN CODE: the SPP
                    # curtailment ceiling (``spp_curtailment_ceiling``) is the
                    # THIRD answer to "where does the measured curtailment
                    # land", and it SUPERSEDES the oversupply allocation rather
                    # than stacking on it. When it is armed the basis reverts to
                    # the FLAT gross-up and the ceiling alone decides both where
                    # the curtailment falls and how much of it binds -- so the
                    # two can never both be live in one solve, whatever a recipe
                    # asks for. The ceiling itself is applied downstream, on the
                    # CF upper bound (data.curtailment_share).
                    measured_cf = None
                    _spp_ceiling = iso == "SPP" and getattr(
                        config, "spp_curtailment_ceiling", False
                    )
                    if (
                        getattr(config, "vre_curtailment_oversupply_allocation", False)
                        and not _spp_ceiling
                    ):
                        measured_cf = _oversupply_uncurtailed_cf(
                            iso, year, fuel, monthly, iso_config
                        )
                    if measured_cf is None:
                        measured_cf = _forecast_uncurtailed_cf(iso, year, fuel, monthly)
                if measured_cf is None:
                    # Every other ISO (and the high-curtailment ISOs when no
                    # reference rate exists) keeps the delivered EIA-930 profile.
                    measured_cf = _eia_hourly_cf_profile(iso, year, fuel, monthly)
            if measured_cf is not None:
                cf_profile = measured_cf
                vintage_ramp = True
            else:
                cf_profile = _eia930_cf(fuel)
                # The intra-year commissioning ramp is OFF for a hindcast seed:
                # ``monthly`` is now the VINTAGE year's array, and every plant
                # in it was already online before the run's first solve year
                # (vintage + 1), so ramping the base pool down through the
                # vintage year's own COD months would de-rate a fleet that is
                # fully in service for the whole horizon. The year-end split is
                # the base fleet; nothing commissions inside it.
                vintage_ramp = config.vintage_capacity_ramp and not hindcast_seeded
                if (
                    not is_backcast
                    and iso == "ERCOT"
                    and getattr(config, "ercot_wtx_curtailment_driver", False)
                ):
                    # Forecast leg of the WP-B West Texas curtailment driver
                    # (data.curtailment_share): the forecast profile rides the
                    # EIA-930 *delivered* distribution, which freezes the
                    # weather year's historical curtailment into the bound. So
                    # the LP can re-curtail endogenously (and the corridor
                    # ceiling is not double-counted on an already-curtailed
                    # series), gross the profile up to an uncurtailed potential
                    # with the per-tech reference curtailment rate from the
                    # most recent HSL year — exactly the
                    # :func:`_forecast_uncurtailed_cf` construction the ERCOT
                    # no-HSL backcast years use. Gated with the driver so
                    # driver-off forecasts stay byte-identical.
                    rate_info = _reference_curtailment_rate(iso, fuel)
                    if rate_info is not None and 0.0 <= rate_info[0] < 1.0:
                        cf_profile = np.clip(
                            cf_profile / (1.0 - rate_info[0]), _CF_MIN, _CF_MAX
                        )
            # Gated multi-zone ISOs get a per-zone SHAPE so geographically
            # distinct zones no longer share one ISO-wide hourly profile: solar
            # in CAISO (clear-sky geometry by tracking mix/latitude) and wind in
            # MISO (MERRA-2 reanalysis through a turbine power curve, so the
            # nocturnal-jet North differs from Central/South). This is a pure
            # spatial redistribution: the capacity-weighted zone sum still
            # equals the measured cf_profile every hour (aggregate preserved),
            # so the validated system shape and annual energy are unchanged —
            # only the inter-zone split moves, which matters as renewables grow
            # and congestion/entry signals bite under the transmission limits.
            zone_shapes = _zone_renewable_shapes(
                iso, fuel, zone_names, year, config=config
            )
            allocated[fuel] = _distribute_by_eia860(
                cf_profile, installed_mw, monthly, vintage_ramp, zone_shapes
            )
        else:
            allocated[fuel] = _allocate_to_zones(
                _eia930_cf(fuel),
                RENEWABLE_INSTALLED_MW[iso][fuel],
                zone_names,
                RENEWABLE_ZONE_ALLOCATION[iso][fuel],
            )

    wind_cf, wind_cap = allocated["wind"]
    solar_cf, solar_cap = allocated["solar"]
    return wind_cf, wind_cap, solar_cf, solar_cap


def derive_offshore_wind_profile(
    onshore_wind_cf: np.ndarray,
    target_avg_cf: float,
    smoothing_hours: int = OFFSHORE_WIND_SMOOTHING_HOURS,
    min_cf: float = OFFSHORE_WIND_MIN_CF,
) -> np.ndarray:
    """Derive an hourly offshore wind CF profile from the onshore wind profile.

    Offshore wind differs from onshore in three physical ways captured here:
    1. Less gusty — ocean fetch smooths out rapid variations. Applied as a
       centered rolling-mean window of ``smoothing_hours`` (default 6h).
    2. Rarely zero — there is almost always some wind offshore. Applied as
       a floor of ``min_cf`` (default 0.08).
    3. Higher average CF — stronger, more consistent resource. The smoothed
       and floored profile is rescaled so its mean matches ``target_avg_cf``.

    The onshore profile encodes real temporal patterns (diurnal, synoptic,
    seasonal) from EIA-930 data. Smoothing preserves these patterns while
    reducing the variance, which is physically correct for offshore.

    Args:
        onshore_wind_cf: (T,) hourly onshore wind CF profile for the ISO.
            This is the single-zone profile from the zone that holds wind
            (e.g. ERCOT West).
        target_avg_cf: Desired annual-average CF for offshore wind.
        smoothing_hours: Rolling-mean window width in hours. Larger values
            produce a smoother (less variable) profile. Default 6.
        min_cf: Minimum hourly CF floor — offshore rarely drops to zero.
            Default 0.08 (~8% of rated). Source: NREL offshore wind studies.

    Returns:
        (T,) hourly offshore wind CF profile, clipped to [0, 1].
    """
    kernel = np.ones(smoothing_hours, dtype=float) / smoothing_hours
    smoothed = np.convolve(onshore_wind_cf, kernel, mode="same")
    floored = np.maximum(smoothed, min_cf)
    rescaled = floored * (target_avg_cf / floored.mean())
    return np.clip(rescaled, _CF_MIN, _CF_MAX)


def inject_offshore_wind_availability(
    fleet_arrays: FleetArrays,
    onshore_wind_cf: np.ndarray,
    config: ScenarioConfig,
    iso: str,
) -> None:
    """Overwrite availability for offshore wind generators with hourly profiles.

    After :func:`generators_to_fleet_arrays` builds the fleet with flat
    availability, this function replaces the availability rows for any
    ``offshore_wind`` generators with a derived hourly profile.

    Modifies ``fleet_arrays.availability`` IN PLACE. If no offshore wind
    generators exist in the fleet, this is a no-op.

    Args:
        fleet_arrays: The vectorized fleet — availability is (n_gen, T).
        onshore_wind_cf: (n_zones, T) onshore wind CF array. The profile
            from the wind-holding zone is used as the basis.
        config: Scenario config for offshore CF override.
        iso: ISO identifier for zone allocation lookup.
    """
    offshore_code = FUEL_TYPE_MAP["offshore_wind"]
    offshore_idx = np.flatnonzero(fleet_arrays.fuel_type_idx == offshore_code)
    if offshore_idx.size == 0:
        return

    # Wind is allocated to a single zone (see RENEWABLE_ZONE_ALLOCATION), so
    # the wind-holding zone is the only non-zero row of onshore_wind_cf.
    wind_zone_idx = int(np.argmax(onshore_wind_cf.sum(axis=1)))
    onshore_profile = onshore_wind_cf[wind_zone_idx]

    key = "floating" if iso == "CAISO" else "fixed_bottom"
    target_cf = OFFSHORE_WIND_PARAMS[key]["base_cf"]
    if config.offshore_wind_cf_override is not None:
        target_cf = config.offshore_wind_cf_override

    offshore_profile = derive_offshore_wind_profile(onshore_profile, target_cf)
    for g_idx in offshore_idx:
        fleet_arrays.availability[g_idx, :] = offshore_profile
