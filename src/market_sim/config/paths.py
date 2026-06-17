"""Central registry of on-disk data locations.

Every data path the model reads is resolved here, once, instead of being
recomputed with ``Path(__file__).parents[3] / ...`` in each data module,
script, and test. This removes the brittle "count the parents" idiom (which
silently breaks when a file moves between directory depths) and gives a single
place to see — and redirect — where the model's inputs live.

Resolution is byte-identical to the historic per-module values: the data
modules live at ``src/market_sim/data/<mod>.py`` and resolved the repo root as
``Path(__file__).parents[3]``; this file lives at
``src/market_sim/config/paths.py`` and resolves it the same way, so every
constant below points exactly where it pointed before.

DATA_ROOT seam
--------------
``DATA_ROOT`` defaults to the repository root but can be overridden with the
``MARKET_SIM_DATA_ROOT`` environment variable. With the variable unset (the
default) ``DATA_ROOT == REPO_ROOT`` and all paths are unchanged; setting it
relocates the whole data tree in one move (e.g. to a mounted dataset).

Forward-looking helpers
-----------------------
``RAW_DIR``, ``CLEAN_DIR``, ``DICTIONARY_DIR`` and :func:`clean_path` describe
the *future* ``data/raw`` + ``data/clean`` layout. They are defined here so
later waves can migrate onto them, but nothing in the model reads them yet —
they are unused this session.
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

# inputs/ tree -------------------------------------------------------------
INPUTS_DIR: Path = DATA_ROOT / "inputs"
RAW_DATA_DIR: Path = INPUTS_DIR / "raw-data"
PROCESSED_DIR: Path = INPUTS_DIR / "processed"
CALIBRATION_DIR: Path = INPUTS_DIR / "calibration"

# inputs/raw-data/ subdirectories -----------------------------------------
EIA_860_DIR: Path = RAW_DATA_DIR / "eia-860"
EIA_930_DIR: Path = RAW_DATA_DIR / "eia-930"
ZONE_DEMAND_DIR: Path = RAW_DATA_DIR / "zone-specific-demand"
ISO_TRANSMISSION_DIR: Path = RAW_DATA_DIR / "iso-specific-transmission"
GAS_PRICES_DIR: Path = RAW_DATA_DIR / "gas-prices"
ERCOT_HSL_DIR: Path = RAW_DATA_DIR / "ercot-hsl"
CAISO_HSL_DIR: Path = RAW_DATA_DIR / "caiso-hsl"
NYISO_HSL_DIR: Path = RAW_DATA_DIR / "nyiso-hsl"

# data/ tree ---------------------------------------------------------------
FLEET_DIR: Path = DATA_ROOT / "data" / "fleet"
REFERENCE_DIR: Path = DATA_ROOT / "data" / "reference"
EIA_HOURLY_DIR: Path = DATA_ROOT / "data" / "eia_hourly"

# ---------------------------------------------------------------------------
# Forward-looking layout (data/raw + data/clean). Unused this session; defined
# so later migration waves can adopt it without re-touching every module.
# ---------------------------------------------------------------------------
RAW_DIR: Path = DATA_ROOT / "data" / "raw"
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
