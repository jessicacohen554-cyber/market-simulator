"""Central registry of on-disk data locations.

Every data path the model reads is resolved here, once, instead of being
recomputed with ``Path(__file__).parents[3] / ...`` in each data module,
script, and test. This removes the brittle "count the parents" idiom (which
silently breaks when a file moves between directory depths) and gives a single
place to see — and redirect — where the model's inputs live.

Single data root (W1)
---------------------
The repo's data used to live under two competing roots (``inputs/`` and
``data/``). The W1 relocation collapsed them into one tree under ``data/raw/``
via ``git mv`` (history-preserving, byte-identical contents). Every constant
below now points into ``data/raw``; only the locations and this file changed.

DATA_ROOT seam
--------------
``DATA_ROOT`` defaults to the repository root but can be overridden with the
``MARKET_SIM_DATA_ROOT`` environment variable. With the variable unset (the
default) ``DATA_ROOT == REPO_ROOT``; setting it relocates the whole data tree
in one move (e.g. to a mounted dataset).

Clean seam
----------
``CLEAN_DIR``, ``DICTIONARY_DIR`` and :func:`clean_path` describe the
``data/clean`` layout (curated, schema-validated Parquet — the write_clean/
read_clean contract). The seam is live: 10+ data modules read through it
(``data/fleet.py``, ``data/eia_loader.py``, ``data/campd.py``, etc.).
``RAW_DIR`` is also live and aliases :data:`RAW_DATA_DIR`.
"""

from __future__ import annotations

import os
from pathlib import Path

# Repository root. This file lives at src/market_sim/config/paths.py, so the
# root is three parents up (config -> market_sim -> src -> repo root). Matches
# the ``Path(__file__).parents[3]`` the data modules used individually.
REPO_ROOT: Path = Path(__file__).resolve().parents[3]

# DATA_ROOT seam: defaults to REPO_ROOT, overridable for relocating the data
# tree wholesale. With MARKET_SIM_DATA_ROOT unset this is exactly REPO_ROOT, so
# every path below is byte-identical to current behavior.
DATA_ROOT: Path = Path(os.environ.get("MARKET_SIM_DATA_ROOT", REPO_ROOT))

# ---------------------------------------------------------------------------
# Current data locations (everything the model reads today).
# ---------------------------------------------------------------------------

# Single consolidated data root (W1 relocation). The two historic roots
# (``inputs/`` + ``data/``) were collapsed into one tree under ``data/raw/``:
# ``inputs/raw-data`` -> ``data/raw``; the legacy ``data/{fleet,reference,
# eia_hourly}`` and ``inputs/{processed,calibration}`` were folded in as
# subdirectories (see below). Relocation was a pure ``git mv`` — file contents
# are byte-identical, only their location (and these constants) changed.
#
# There is no ``INPUTS_DIR``. The former ``DATA_ROOT / "inputs"`` export was
# kept "for backward compatibility" after W1 but had zero consumers repo-wide,
# so it was removed rather than zeroed — a dead path constant that still
# resolves is a re-armable dead path (rule 26 [R-DELETE]). Everything resolves
# under ``data/raw``.
RAW_DATA_DIR: Path = DATA_ROOT / "data" / "raw"
# inputs/processed and inputs/calibration were relocated under data/raw with
# leading-underscore names that sort them apart from the raw downloads and flag
# them as not-yet-curated (they get curated in W3).
PROCESSED_DIR: Path = RAW_DATA_DIR / "_processed-legacy"
CALIBRATION_DIR: Path = RAW_DATA_DIR / "_validation-source"


def cc_capacity_reconcile_path(iso: str) -> Path:
    """Canonical on-disk path of an ISO's CC demonstrated-peak reconcile table.

    ``PROCESSED_DIR/cc_capacity_reconcile_<ISO>.csv`` — the per-plant measured
    CAMPD demonstrated-peak table (:func:`scripts.data.derive_cc_capacity_reconcile`)
    consumed by the ``cc_capacity_reconcile`` hook and the ISO-agnostic CC
    summer-capacity guard (:func:`market_sim.data.fleet._reconcile_cc_pmax_to_nameplate`).
    Every table stays inside its own ISO (CLAUDE.md rule 24), so this is the
    single resolver both the ``ScenarioConfig`` default and the guard use — no
    literal ISO filename crosses an ISO boundary (rule 25). A missing file is a
    no-op at both call sites.
    """
    return PROCESSED_DIR / f"cc_capacity_reconcile_{iso.upper()}.csv"


# inputs/raw-data/ subdirectories -----------------------------------------
EIA_860_DIR: Path = RAW_DATA_DIR / "eia-860"

# EIA-923 Schedules 2-5 Page 1 "Generation and Fuel Data", annual per plant x
# prime mover x reported fuel: total / electric fuel consumption (MMBtu) and
# net generation (MWh). R-CAISO-3 intake; the owner's own fuel filing, which is
# independent of CEMS heat input (scripts/data/fetch_eia923_generation_fuel.py).
EIA_923_GENERATION_FUEL_DIR: Path = RAW_DATA_DIR / "eia-923-generation-fuel"
EIA_923_GENERATION_FUEL_PATH: Path = (
    EIA_923_GENERATION_FUEL_DIR / "eia923_generation_fuel_2019_2025.csv"
)

# --- EIA-860 vintage selection -------------------------------------------
# The committed EIA-860 parquets in EIA_860_DIR are the 2025 Early Release
# (operating years through 2025) — a single recent snapshot the COD ramp
# filters to the solved year for backcasts. A *year-matched* vintage (the
# native EIA-860 annual release for the solved year, processed into
# ``EIA_860_DIR/vintage_<year>/``) removes the COD-ramp approximation (the
# capacity-weighted-mean COD smear of mixed-vintage plants) and the absence of
# units that retired between the solved year and the 2025 snapshot. Measured
# effect on installed ERCOT capacity is small (~0.4% vs the COD-ramped 2025ER
# fleet — see docs/cod-vintage-ramp.md), so this is a correctness/provenance
# refinement, not a scarcity driver; it is opt-in via
# ``ScenarioConfig.eia860_vintage_year`` (backcast-only). The active directory
# is a process-global set per year-solve through :func:`set_eia860_vintage`;
# loaders resolve their default data dir through :func:`active_eia860_dir`.
_ACTIVE_EIA_860_DIR: Path = EIA_860_DIR


def active_eia860_dir() -> Path:
    """Return the EIA-860 directory loaders should read from.

    Defaults to the canonical (2025 Early Release) ``EIA_860_DIR`` and is
    redirected to a ``vintage_<year>`` subdirectory by
    :func:`set_eia860_vintage`.
    """
    return _ACTIVE_EIA_860_DIR


def set_eia860_vintage(year: int | None) -> Path:
    """Point the EIA-860 loaders at a year-matched vintage (or the default).

    ``year=None`` (or a year with no committed ``vintage_<year>/`` directory)
    resets to the canonical ``EIA_860_DIR``. Returns the resolved directory.
    Caches keyed on the resolved directory (``fleet._chp_by_plant``,
    ``fleet.dual_fuel_plant_groups``, ``cod_ramp.load_cod_map``) pick the switch
    up automatically because the directory is part of their cache key.
    """
    global _ACTIVE_EIA_860_DIR
    if year is None:
        _ACTIVE_EIA_860_DIR = EIA_860_DIR
    else:
        candidate = EIA_860_DIR / f"vintage_{int(year)}"
        _ACTIVE_EIA_860_DIR = candidate if candidate.is_dir() else EIA_860_DIR
    return _ACTIVE_EIA_860_DIR


# --- EIA-860 operable status admission ------------------------------------
# The fleet keeps EIA-860 ``Status == "OP"`` generators only. ``SB`` is EIA's
# "Standby/Backup — available for service but not normally used for this
# reporting period": physically available capacity the OP filter drops (NWPP
# Fredonia 607 / Sun Peak 54854, FINDING-nwppnext2-standby-census-2026-09-25).
# ``ScenarioConfig.admit_standby_units`` (GATED default-off) widens the set to
# ``{"OP", "SB"}``. Process-global exactly like the vintage switch above and set
# at the same two entry points, so every fleet read path — the snapshot, the
# per-year vintages, the outage denominators built from the same fleet load —
# sees one admission rule (rule 19 ``[R-ONE-MECH]``).
_DEFAULT_OPERABLE_STATUSES: frozenset[str] = frozenset({"OP"})
_STANDBY_ADMITTED_STATUSES: frozenset[str] = frozenset({"OP", "SB"})
_ACTIVE_OPERABLE_STATUSES: frozenset[str] = _DEFAULT_OPERABLE_STATUSES


def eia860_operable_statuses() -> frozenset[str]:
    """Return the EIA-860 generator statuses the fleet admits as operable.

    ``{"OP"}`` by default; ``{"OP", "SB"}`` while
    :func:`set_eia860_standby_admission` is armed.
    """
    return _ACTIVE_OPERABLE_STATUSES


def eia860_standby_admitted() -> bool:
    """Return True while standby (``SB``) generators are admitted to the fleet."""
    return "SB" in _ACTIVE_OPERABLE_STATUSES


def set_eia860_standby_admission(admit_standby_units: bool) -> frozenset[str]:
    """Arm (or reset) standby-unit admission for the fleet loaders.

    Args:
        admit_standby_units: ``ScenarioConfig.admit_standby_units``.

    Returns:
        The active admitted status set.
    """
    global _ACTIVE_OPERABLE_STATUSES
    _ACTIVE_OPERABLE_STATUSES = (
        _STANDBY_ADMITTED_STATUSES
        if admit_standby_units
        else _DEFAULT_OPERABLE_STATUSES
    )
    return _ACTIVE_OPERABLE_STATUSES


def resolve_backcast_eia860_vintage(
    explicit_vintage: int | None,
    solve_year: int | None,
    tracks_solve_year: bool,
) -> int | None:
    """Return the EIA-860 vintage year a BACKCAST solve should read.

    One resolution, one place (rule 19 ``[R-ONE-MECH]``) for the two backcast
    entry points that arm the vintage — ``scripts/run_calibration.py::run_year``
    and ``runner.run_scenario_iso``. Precedence:

    1. an explicit ``ScenarioConfig.eia860_vintage_year`` always wins, so the
       existing pin keeps its exact meaning and its cache key;
    2. else, when ``ScenarioConfig.eia860_vintage_tracks_solve_year`` is armed,
       the **solved year** — each year of a rule-16 multi-year bundle reads its
       own annual release rather than one run-level scalar;
    3. else ``None`` — the canonical 2025-Early-Release snapshot, filtered to
       the solved year by the COD ramp, exactly as today.

    A year with no committed ``vintage_<year>/`` directory falls through to the
    canonical snapshot inside :func:`set_eia860_vintage`, so (2) degrades to (3)
    rather than failing. Selection is by calendar year only — nothing here reads
    a model output or a scoring target (rules 13/14).

    Args:
        explicit_vintage: ``ScenarioConfig.eia860_vintage_year``.
        solve_year: The year being solved, or ``None`` when the caller has no
            single year in hand.
        tracks_solve_year: ``ScenarioConfig.eia860_vintage_tracks_solve_year``.

    Returns:
        The vintage year to pass to :func:`set_eia860_vintage`, or ``None``.
    """
    if explicit_vintage is not None:
        return int(explicit_vintage)
    if tracks_solve_year and solve_year is not None:
        return int(solve_year)
    return None


EIA_930_DIR: Path = RAW_DATA_DIR / "eia-930"
# FERC Form 714 Part III Schedule 2 hourly planning-area demand, per respondent
# (PUDL ``out_ferc714__hourly_planning_area_demand``). The measured substitute
# for an NWPP pool member whose EIA-930 demand is missing (lane NWPP-NEXT).
FERC_714_DIR: Path = RAW_DATA_DIR / "ferc-714"
ZONE_DEMAND_DIR: Path = RAW_DATA_DIR / "zone-specific-demand"
# PJM Day-Ahead energy market offers from DataMiner2 (energy_market_offers feed).
# Monthly raw parquets: pjm_energy_offers_YYYY_MM.parquet.  Files are gitignored
# because the 3-year corpus is ~4 GB; re-fetch with scripts/data/fetch_pjm_energy_offers.py.
PJM_ENERGY_OFFERS_DIR: Path = RAW_DATA_DIR / "pjm-energy-offers"
# CAISO OASIS DAM Public Bid Data (PUB_DAM_GRP GroupZip, 90-day-lag masked
# bid curves).  Daily zips under zips/: <YYYYMMDD>_PUB_BID_DAM_v3_csv.zip.
# Gitignored (pjm-energy-offers precedent); re-fetch with
# scripts/data/fetch_caiso_public_bids.py.
CAISO_PUBLIC_BIDS_DIR: Path = RAW_DATA_DIR / "caiso-public-bids"
# MISO masked submitted energy-offer corpus (Market Reports *_da_co / *_rt_co,
# ~90-day lag): daily zips under <market>/, <YYYYMMDD>_<market>_co.zip, plus a
# manifest.json of per-file sha256/size.  Gitignored (pjm-energy-offers
# precedent); re-fetch with scripts/data/fetch_miso_energy_offers.py.
MISO_ENERGY_OFFERS_DIR: Path = RAW_DATA_DIR / "miso-energy-offers"
PJM_DA_VIRTUALS_DIR: Path = RAW_DATA_DIR / "pjm-da-virtuals"
# PJM ancillary-services / reserve-market DataMiner2 exports (reserve_market_
# results, da_reserve_market_results, ancillary_services, da_ancillary_services,
# and the derived pjm_<year>_as_up_mw withholding series). See
# data/raw/PJM-AS/README.md; fetched by scripts/data/fetch_pjm_as.py.
PJM_AS_DIR: Path = RAW_DATA_DIR / "PJM-AS"
ISO_TRANSMISSION_DIR: Path = RAW_DATA_DIR / "iso-specific-transmission"
GAS_PRICES_DIR: Path = RAW_DATA_DIR / "gas-prices"
# Measured petroleum-product spot series. Today: the EIA daily New York Harbor
# ULSD spot (scripts/data/fetch_ny_harbor_distillate_daily.py), which supplies
# the within-month SHAPE of the dual-fuel oil-parity cap — the delivered LEVEL
# stays the monthly EIA-923 receipt (data.fuel.oil_daily_shape_factors).
OIL_PRICES_DIR: Path = RAW_DATA_DIR / "oil-prices"
COAL_PRICES_DIR: Path = RAW_DATA_DIR / "coal-prices"
ERCOT_HSL_DIR: Path = RAW_DATA_DIR / "ercot-hsl"
CAISO_HSL_DIR: Path = RAW_DATA_DIR / "caiso-hsl"
# CAISO Production-and-Curtailments workbooks (5-minute), the source for the
# CAISO HSL build (delivered + reported curtailment). Built by
# scripts/data/build_caiso_hsl.py.
CAISO_CURTAILMENT_DIR: Path = RAW_DATA_DIR / "caiso-curtailment"
NYISO_HSL_DIR: Path = RAW_DATA_DIR / "nyiso-hsl"
MISO_HSL_DIR: Path = RAW_DATA_DIR / "miso-hsl"
# SPP's curtailed leg. Like MISO, SPP publishes no hourly HSL series, so this
# directory holds the MMU's Annual-State-of-the-Market wind-curtailment table
# rather than an hourly parquet — the same shape MISO_HSL_DIR takes for the
# Potomac Economics table. Landed by lane SPP-12; read by
# market_sim.data.renewables for SPP's reference curtailment rate.
SPP_HSL_DIR: Path = RAW_DATA_DIR / "spp-hsl"
# Per-zone wind SHAPE (NASA POWER MERRA-2 reanalysis → power curve), one parquet
# per backcast year. Built by scripts/data/build_miso_wind_shape.py; read by
# market_sim.data.renewables to give MISO's three regions distinct wind diurnal/
# seasonal shapes (the upper-plains nocturnal-jet north vs the lower-Midwest
# central/south) while preserving the EIA-930 MISO-wide aggregate.
MISO_WIND_SHAPE_DIR: Path = RAW_DATA_DIR / "miso-wind-shape"
# ERCOT analogue (ERCOT-112): the West/Panhandle CREZ corridor rides the
# Great-Plains nocturnal low-level jet while the South/Coastal fleet rides the
# Gulf sea breeze, and those two peak at different hours — so one ISO-wide
# hourly profile averages them together. Same builder, same parquet schema.
ERCOT_WIND_SHAPE_DIR: Path = RAW_DATA_DIR / "ercot-wind-shape"
# SPP analogue (SPP-32): SPP's 35.5 GW wind fleet splits almost exactly in half
# across the North/South seam (EIA-860 operable: 17.7 GW / 135 plants North,
# 17.8 GW / 119 plants South), and the two halves peak at different hours.
# Measured night(00-06)/afternoon(12-18) ratio, 2023/2024/2025: SPP-South
# 1.04/1.06/1.03 (overnight-weighted) vs SPP-North 0.97/0.96/0.91
# (afternoon-weighted) — the SOUTH is the nocturnal zone here, because the
# Great-Plains low-level jet's core sits over Oklahoma / Kansas / the Texas
# Panhandle and weakens northward. (The MISO contrast points the other way; do
# not carry that intuition across.) One SWPP-wide hourly profile averages the
# two together.
# Same builder pattern, same parquet schema; built by
# scripts/data/build_spp_wind_shape.py.
SPP_WIND_SHAPE_DIR: Path = RAW_DATA_DIR / "spp-wind-shape"

# Per-ISO wind-shape directory registry (no ``if iso ==`` ladder at the call
# sites). An ISO absent here has no per-zone wind SHAPE, which the renewable
# loader treats as a no-op — it keeps the legacy single-ISO-wide profile.
WIND_SHAPE_DIRS: dict[str, Path] = {
    "MISO": MISO_WIND_SHAPE_DIR,
    "ERCOT": ERCOT_WIND_SHAPE_DIR,
    "SPP": SPP_WIND_SHAPE_DIR,
}


def wind_shape_dir(iso: str) -> Path | None:
    """Return the per-zone wind-shape directory for ``iso``, or ``None``.

    ``None`` means the ISO has no per-zone wind SHAPE registered, and the
    renewable loader keeps its legacy single-ISO-wide wind profile.
    """
    return WIND_SHAPE_DIRS.get(iso.upper())


# SOCO per-zone SOLAR-shape directory (SOCO-32, 2026-09-16). The solar analogue
# of the wind registry above, and the first of its kind: every other region's
# per-zone solar shape is the CLEAR-SKY construction
# ``renewables._solar_zone_clearsky_shapes`` computes from latitude and tracking
# mix with no file at all. SOCO needs a file because its zones are separated by
# LONGITUDE (centroids -83.63 / -86.35 / -89.16 E, a 5.53 deg span = 22 minutes
# of solar time) and that path deliberately omits longitude — see
# ``data/raw/soco-solar-shape/README.md``. Built by
# scripts/data/build_soco_solar_shape.py from NASA POWER all-sky irradiance at
# each EIA-860 solar plant; same parquet schema as the wind tables.
SOCO_SOLAR_SHAPE_DIR: Path = RAW_DATA_DIR / "soco-solar-shape"

# Per-ISO SOLAR-shape directory registry (no ``if iso ==`` ladder at the call
# sites). An ISO absent here has no measured per-zone solar SHAPE, which the
# renewable loader treats as a no-op — it keeps whichever solar path it already
# had (the clear-sky one for CAISO, the single ISO-wide profile for everyone
# else). ``data/raw/nwpp-solar-shape`` exists on disk but is deliberately NOT
# registered: NWPP-33 landed it as data and routed ARMING to NWPP-DESK, which is
# that region's call to make, not this registry's (rule 25 ``[R-ISO-SCOPE]``).
SOLAR_SHAPE_DIRS: dict[str, Path] = {
    "SOCO": SOCO_SOLAR_SHAPE_DIR,
}


def solar_shape_dir(iso: str) -> Path | None:
    """Return the per-zone solar-shape directory for ``iso``, or ``None``.

    ``None`` means the ISO has no measured per-zone solar SHAPE registered, and
    the renewable loader keeps its existing solar behaviour.
    """
    return SOLAR_SHAPE_DIRS.get(iso.upper())


# ---------------------------------------------------------------------------
# Remaining raw-download subdirectories (registered 2026-07-26, the scripts/
# path-registry routing pass). One constant per ``data/raw`` subdirectory that
# code resolves at runtime, so call sites compose on the registry instead of
# re-deriving repo-root math (CLAUDE.md directory map: every path resolves
# through config/paths.py). Loose single-consumer FILES under the data/raw
# root compose as ``RAW_DATA_DIR / "<name>"`` at their call site — the same
# idiom the data modules already use — rather than growing a one-line file
# constant each.
# ---------------------------------------------------------------------------
# ERCOT MIS market-report disclosure exports (60/2-Day AS disclosure
# aggregates, NP4-series report parquets) — the bulk ``data/raw/ercot`` tree.
ERCOT_MIS_DIR: Path = RAW_DATA_DIR / "ercot"
# Per-ISO ancillary-service market exports (awards/requirements/prices).
ERCOT_AS_DIR: Path = RAW_DATA_DIR / "ercot-AS"
NYISO_AS_DIR: Path = RAW_DATA_DIR / "NYISO-AS"
NEISO_AS_DIR: Path = RAW_DATA_DIR / "NEISO-AS"
# NYISO planning publications (Gold Books + NYCA generator workbooks, ATC/TTC).
NYISO_DIR: Path = RAW_DATA_DIR / "NYISO"
# Settlement-point LMP archives (per-ISO subdirs + ERCOT SPP zips at the root).
LMP_DATA_DIR: Path = RAW_DATA_DIR / "lmp-data"
CAISO_DAM_OUTAGES_DIR: Path = RAW_DATA_DIR / "caiso-dam-outages"
# Parent of the by-year tree data.pjm_outages reads (PJM_OUTAGE_BYYEAR_DIR).
PJM_OUTAGES_DIR: Path = RAW_DATA_DIR / "pjm-outages"
MISO_GENERATION_OUTAGES_DIR: Path = RAW_DATA_DIR / "miso-generation-outages"
NRC_REACTOR_STATUS_DIR: Path = RAW_DATA_DIR / "nrc-reactor-status"
NUCLEAR_LICENSE_STATUS_DIR: Path = RAW_DATA_DIR / "nuclear-license-status"
NEISO_OPERABLE_CAPACITY_DIR: Path = RAW_DATA_DIR / "neiso-operable-capacity"
# CAMPD hourly emissions/operations extracts (unit- and facility-level).
CAMPD_UNIT_LEVEL_DIR: Path = RAW_DATA_DIR / "campd-unit-level"
CAMPD_FACILITY_LEVEL_DIR: Path = RAW_DATA_DIR / "campd-facility-level"
STORAGE_AS_AWARDS_DIR: Path = RAW_DATA_DIR / "storage-as-awards"
NEW_BUILD_COST_BENCHMARKS_DIR: Path = RAW_DATA_DIR / "new-build-cost-benchmarks"
FUEL_FORWARD_BENCHMARKS_DIR: Path = RAW_DATA_DIR / "fuel-forward-benchmarks"
EIA_AEO_DIR: Path = RAW_DATA_DIR / "eia-aeo"
EIA_930_INTERCHANGE_DIR: Path = RAW_DATA_DIR / "eia-930-interchange"
TRANSFER_CONSTRAINT_BINDING_DIR: Path = RAW_DATA_DIR / "transfer-constraint-binding"
MISO_REGIONAL_BALANCE_DIR: Path = RAW_DATA_DIR / "miso-regional-balance"
TRANSMISSION_EXPANSION_DIR: Path = RAW_DATA_DIR / "transmission-expansion"
NREL_ATB_DIR: Path = RAW_DATA_DIR / "nrel-atb"
ERCOT_WEATHER_DIR: Path = RAW_DATA_DIR / "ercot-weather"

# Legacy data/ tree, folded into data/raw/ (W1). The directory names were
# disambiguated on the way in so they don't collide with existing data/raw
# subdirs: data/fleet -> data/raw/fleet-egrid (eGRID workbook),
# data/reference -> data/raw/reference, data/eia_hourly -> data/raw/eia-930-hourly.
FLEET_DIR: Path = RAW_DATA_DIR / "fleet-egrid"
REFERENCE_DIR: Path = RAW_DATA_DIR / "reference"
EIA_HOURLY_DIR: Path = RAW_DATA_DIR / "eia-930-hourly"

# Loose curated reference files that used to sit at the inputs/ root; relocated
# into data/raw/reference/ (W1). Centralized here so the modules that read them
# (config.scenarios, data.cod_ramp, data.outages, data.fleet) resolve one path
# instead of hardcoding a CWD-relative ``inputs/...`` string.
PLANT_REGISTRY_CSV: Path = REFERENCE_DIR / "master-plant-registry.csv"
CAMPD_BINS_CSV: Path = REFERENCE_DIR / "custom-bin-assignments.csv"

# Measured CAISO generator->trading-hub membership crosswalk (caiso-217,
# FINDING-caiso216 §F.1g): derived by
# scripts/data/derive_caiso_plant_hub_membership.py from the committed OASIS
# ATL_PNODE_MAP atlas; read by data.zone_assignment as the CAISO first-check
# over the geographic lat/county estimate [R-ACCURATE].
CAISO_HUB_MEMBERSHIP_CSV: Path = REFERENCE_DIR / "caiso-plant-hub-membership.csv"

# Measured CAISO plant->sub-zone membership for the FSNO sub-zonal partition
# (caiso-223 §B recut of the caiso-217 crosswalk — the committed
# results/calibration/_caiso223_membership_recut.csv rows with subzone in
# {FSNO, NP15, ZP26}; SP15-side rows are hub-unchanged by construction).
# Read by data.zone_assignment ONLY when ScenarioConfig
# caiso_fsno_subzonal_topology is armed (config.topology_variant)
# [R-MEASURED; PRECOMMIT-caiso224-fsno-arm-2026-08-30.md §1].
CAISO_FSNO_SUBZONE_CSV: Path = REFERENCE_DIR / "caiso-fsno-subzone-membership.csv"

# Supply-consistent CAISO backcast demand series (caiso-80, owner-signed
# Option A; FINDING-caiso80-demand-basis-wedge-2026-07-13). Derived measured
# artifact written by scripts/data/derive_caiso_supply_consistent_demand.py, read
# by eia_loader._load_caiso_hourly_demand under
# ScenarioConfig.caiso_supply_consistent_demand.
CAISO_SUPPLY_CONSISTENT_DEMAND_DIR: Path = (
    REFERENCE_DIR / "caiso-supply-consistent-demand"
)

# CAISO "Today's Outlook" historical 5-minute fuel mix (large/small hydro, ...),
# raw yearly CSVs fetched by scripts/data/fetch_caiso_outlook_fuelsource.py. The
# measured source for the EIA-930 CISO NG: WAT gap (2019-10 .. 2020-08), read by
# data.eia930.caiso_hydro_backfill (i-caiso, 2026-09-24).
CAISO_OUTLOOK_FUELSOURCE_DIR: Path = RAW_DATA_DIR / "caiso-outlook-fuelsource"

# ---------------------------------------------------------------------------
# Raw/clean layout. ``RAW_DIR`` is now live and identical to ``RAW_DATA_DIR``
# (the W1 relocation made data/raw the single raw root). ``CLEAN_DIR`` /
# ``DICTIONARY_DIR`` are also live: the write_clean/read_clean seam
# (``scripts/lib/clean_io.py``) reads/writes under ``CLEAN_DIR`` and is
# already exercised by 15+ data modules (``data/campd.py``, ``data/chp.py``,
# ``data/capacity_deliverability.py``, ``data/fleet.py``, etc.).
# ---------------------------------------------------------------------------
RAW_DIR: Path = RAW_DATA_DIR
CLEAN_DIR: Path = DATA_ROOT / "data" / "clean"
DICTIONARY_DIR: Path = DATA_ROOT / "data" / "dictionary"

# Hand-off extracts: DERIVED, human-facing CSV cuts of a raw archive, produced
# on request and committed so the exact bytes handed to a reader are on the
# record. NOT a model input — nothing under ``src/market_sim/`` reads this
# tree, and no curator writes it; the clean tree (``CLEAN_DIR``) remains the
# only derived input surface. Each subdirectory carries a README naming its
# raw source and the script that regenerates it.
EXPORTS_DIR: Path = DATA_ROOT / "data" / "exports"

# ---------------------------------------------------------------------------
# Results tree (derived, disposable) and its ensemble subtree. Both were
# previously reached with cwd-relative literals (``Path("results")`` in
# ``results/cache.py``, ``Path("results/ensemble")`` in ``matrix.py``), which
# silently forks the results tree when the process runs from a directory other
# than the repo root. Rooting them here (under DATA_ROOT, = REPO_ROOT by
# default, so byte-identical for the normal invocation) removes that fork and
# gives one place to redirect the whole tree. Not input data — disposable
# solve/ensemble output — but co-located with DATA_ROOT for a single override.
RESULTS_ROOT: Path = DATA_ROOT / "results"
ENSEMBLE_DIR: Path = RESULTS_ROOT / "ensemble"

# Committed backcast-dashboard payloads (the measured, reproducible source the
# structural-error prior fits on): per-run gzip+base64 run payloads under
# ``runs/`` and per-ISO/per-year actual "bench" totals under ``bench/``.
FRONTEND_BACKCAST_DIR: Path = DATA_ROOT / "frontend" / "data" / "backcast"

# Committed fitted structural-prior artifacts (one JSON per prior version):
# the auditable record of each PB-3 fit, so a re-fit (e.g. W3-P1 swapping the
# stale carbon-priced statmode inputs) lands as a new versioned file.
STRUCTURAL_PRIOR_ARTIFACT_DIR: Path = ENSEMBLE_DIR / "structural-prior"

# Disposable content-addressed cold-solve cache (PERF-C S6,
# ``model/lp/p0_cache.py``): one NPZ per LP-content key, bucketed by structural
# digest, gitignored. Anchored here for the same reason as
# STRUCTURAL_PRIOR_ARTIFACT_DIR — a single DATA_ROOT override relocates it with
# everything else. Deletable at any time; the next solve of the same LP
# recaptures it.
P0_CACHE_DIR: Path = RESULTS_ROOT / "p0-cache"

# ---------------------------------------------------------------------------
# ERCOT 60-Day DAM Disclosure extracts live in TWO raw directories under two
# filename conventions, and every consumer needs both:
#
#   ERCOT_MIS_DIR   data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_<family>_<y>_*.parquet
#                   the MIS-fetcher lane (2023-2026), written by
#                   scripts/data/fetch_ercot_60day_gen_resource.py
#   ERCOT_AS_DIR    data/raw/ercot-AS/60d_DAM_<family>_<y>_*.parquet
#                   the annual-archive lane (2018-2022), landed by the AS
#                   back-year intake
#
# Same ERCOT product, same consumed schema (Delivery Date / Hour Ending /
# Resource Name / Resource Type / HSL / Resource Status / Settlement Point
# Name are present in every file of both lanes); only the filename prefix and
# the fragment split differ. Registered here rather than re-globbed per script
# so "where does the 60-Day DAM disclosure live" has ONE answer that a new
# directory extends for every consumer at once (CLAUDE.md directory map: every
# path resolves through config/paths.py).
ERCOT_DAM_DISCLOSURE_DIRS: tuple[Path, ...] = (ERCOT_MIS_DIR, ERCOT_AS_DIR)


def ercot_dam_disclosure_files(
    family: str = "Gen_Resource_Data", label_year: int | str = "*"
) -> list[Path]:
    """Return the committed 60-Day DAM Disclosure parquets for one family/label.

    ``family`` is the ERCOT report family (``Gen_Resource_Data``,
    ``ESR_Data``, ...); ``label_year`` the year in the FILENAME, which is the
    ARCHIVE label, not the delivery year — ERCOT's 60-day publication lag makes
    a label-``y`` archive span deliveries ``y-1``-11-02 .. ``y``-11-01. Callers
    therefore scan label ``y`` AND ``y+1`` and filter on the Delivery Date
    column; this function only resolves files, it never filters by date.

    Both registered directories (:data:`ERCOT_DAM_DISCLOSURE_DIRS`) are
    searched under both filename conventions via a leading-wildcard pattern, so
    a file is matched by its family + label year alone — no per-file list, and
    a new archive drop is picked up by existing in place.

    Returned sorted by (filename, directory) so the read order is stable and
    independent of which directory a fragment happens to sit in.
    """
    seen: dict[tuple[str, str], Path] = {}
    for d in ERCOT_DAM_DISCLOSURE_DIRS:
        if not d.is_dir():
            continue
        for p in d.glob(f"*60d_DAM_{family}_{label_year}_*.parquet"):
            seen[(p.name, str(d))] = p
    return [seen[k] for k in sorted(seen)]


def clean_path(
    datatype: str,
    iso: str | None = None,
    year: int | None = None,
    market: str | None = None,
) -> Path:
    """Return the ``data/clean`` location for a derived dataset.

    Composes a canonical path under :data:`CLEAN_DIR` from a dataset
    ``datatype`` and the optional ``iso`` / ``market`` partition keys, with
    ``year`` (when given) folded into the file stem. Live: e.g.
    ``data/eia_loader.py`` calls this to resolve its weather clean-Parquet
    path. Most other clean-seam modules instead go through
    ``scripts/lib/clean_io.read_clean``/``write_clean``, which resolve their
    own per-datatype paths under :data:`CLEAN_DIR` directly.

    Examples
    --------
    ``clean_path("demand", iso="ERCOT", year=2024)`` ->
    ``<CLEAN_DIR>/demand/ERCOT/demand_2024.parquet``
    """
    base = CLEAN_DIR / datatype
    if iso is not None:
        base = base / iso
    if market is not None:
        base = base / market
    stem = datatype if year is None else f"{datatype}_{year}"
    return base / f"{stem}.parquet"
