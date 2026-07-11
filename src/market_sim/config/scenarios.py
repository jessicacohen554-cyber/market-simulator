"""Scenario definitions and loading for simulation runs."""

from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path

import yaml

from market_sim.config.paths import (
    CAMPD_BINS_CSV,
    EIA_860_DIR,
    PLANT_REGISTRY_CSV,
    PROCESSED_DIR,
)

# Config fields introduced after the results cache existed. ``cache_key`` omits
# each from its hash while it holds its default value, keeping every historical
# cache key byte-stable; a non-default value still enters the key.
_CACHE_KEY_OPTIONAL_FIELDS = (
    "start_year",
    "end_year",
    "hindcast",
    "hindcast_fuel_variant",
    # G-30 first-wave probes (default-off): dropped from the hash at default so
    # every pre-existing cached run keeps its key; a non-default value enters
    # the key (a distinct scenario).
    "staged_oversupply_thinning",
    "staged_thinning_max_gw_per_year",
    "limited_foresight_dispatch",
)
