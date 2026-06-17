"""Central registry of on-disk data locations.

Every data path the model reads is resolved here, once, instead of being
recomputed with ``Path(__file__).parents[3] / ...`` in each data module,
script, and test. This removes the brittle "count the parents" idiom (which
silently breaks when a file moves between directory depths) and gives a single
place to see — and redirect — where the model's inputs live.

Single data root: every input now lives under ``data/raw``. The historic two
roots — ``inputs/`` and a second ``data/{fleet,reference,eia_hourly}`` tree —
were collapsed into ``data/raw`` with ``git mv`` (file contents byte-identical;
only their location and the constants in this file changed). This module is the
one place those new locations are spelled out, so the relocation touched the
registry rather than every call site.

DATA_ROOT seam
--------------
``DATA_ROOT`` defaults to the repository root but can be overridden with the
``MARKET_SIM_DATA_ROOT`` environment variable. With the variable unset (the
default) ``DATA_ROOT == REPO_ROOT``; setting it relocates the whole data tree
in one move (e.g. to a mounted dataset).

Forward-looking helpers
-----------------------
``CLEAN_DIR``, ``DICTIONARY_DIR`` and :func:`clean_path` describe the *future*
``data/clean`` layout for derived artifacts. They are defined here so later
waves can migrate onto them, but nothing in the model reads them yet. ``RAW_DIR``
now simply aliases the live :data:`RAW_DATA_DIR`.
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
# Current data locations. As of the "collapse the two data roots" relocation,
# everything the model reads lives under a single root, ``data/raw``. The old
# ``inputs/`` tree and the second ``data/{fleet,reference,eia_hourly}`` root
# were folded in here with ``git mv`` (contents byte-identical; only their
# location and the constants below changed).
# ---------------------------------------------------------------------------

# Single raw-data root -----------------------------------------------------
RAW_DATA_DIR: Path = DATA_ROOT / "data" / "raw"  # was inputs/raw-data

# Legacy curation buckets, relocated intact under data/raw (curated later).
PROCESSED_DIR: Path = RAW_DATA_DIR / "_processed-legacy"  # was inputs/processed
CALIBRATION_DIR: Path = RAW_DATA_DIR / "_validation-source"  # was inputs/calibration

# data/raw subdirectories (names unchanged, new root) ----------------------
EIA_860_DIR: Path = RAW_DATA_DIR / "eia-860"

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
EIA_930_DIR: Path = RAW_DATA_DIR / "eia-930"
ZONE_DEMAND_DIR: Path = RAW_DATA_DIR / "zone-specific-demand"
ISO_TRANSMISSION_DIR: Path = RAW_DATA_DIR / "iso-specific-transmission"
GAS_PRICES_DIR: Path = RAW_DATA_DIR / "gas-prices"
ERCOT_HSL_DIR: Path = RAW_DATA_DIR / "ercot-hsl"
CAISO_HSL_DIR: Path = RAW_DATA_DIR / "caiso-hsl"
NYISO_HSL_DIR: Path = RAW_DATA_DIR / "nyiso-hsl"

# Measured ancillary-service withholding inputs (system-wide hourly AS held
# out of energy; consumed by data.fleet, model.storage, results.scarcity).
ERCOT_AS_DIR: Path = RAW_DATA_DIR / "ercot-AS"
PJM_AS_DIR: Path = RAW_DATA_DIR / "PJM-AS"

# Second legacy root, folded into data/raw under collision-free names ------
FLEET_DIR: Path = RAW_DATA_DIR / "fleet-egrid"          # was data/fleet
REFERENCE_DIR: Path = RAW_DATA_DIR / "reference"        # was data/reference
EIA_HOURLY_DIR: Path = RAW_DATA_DIR / "eia-930-hourly"  # was data/eia_hourly

# Curated reference CSVs that used to sit loose at the inputs/ root; relocated
# into data/raw/reference/ alongside the other reference material.
PLANT_REGISTRY_CSV: Path = REFERENCE_DIR / "master-plant-registry.csv"
CAMPD_BINS_CSV: Path = REFERENCE_DIR / "custom-bin-assignments.csv"

# ---------------------------------------------------------------------------
# Forward-looking layout (the data/raw + data/clean split). ``RAW_DIR`` now
# coincides with the live :data:`RAW_DATA_DIR`; ``CLEAN_DIR`` / ``DICTIONARY_DIR``
# remain future locations no module reads yet.
# ---------------------------------------------------------------------------
RAW_DIR: Path = RAW_DATA_DIR
CLEAN_DIR: Path = DATA_ROOT / "data" / "clean"
DICTIONARY_DIR: Path = DATA_ROOT / "data" / "dictionary"


def clean_path(
    datatype: str,
    iso: str | None = None,
    year: int | None = None,
    market: str | None = None,
) -> Path:
    """Return the future ``data/clean`` location for a derived dataset.

    Forward-looking helper for the upcoming raw/clean split: it composes a
    canonical path under :data:`CLEAN_DIR` from a dataset ``datatype`` and the
    optional ``iso`` / ``market`` partition keys, with ``year`` (when given)
    folded into the file stem. Nothing in the model calls this yet — it exists
    so later waves can route cleaned artifacts through one helper rather than
    hand-building paths.

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
