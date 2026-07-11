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

_CACHE_KEY_OPTIONAL_FIELDS = (
    "start_year",
    "end_year",
    "hindcast",
    "hindcast_fuel_variant",
    "staged_oversupply_thinning",
    "staged_thinning_max_gw_per_year",
    "limited_foresight_dispatch",
)


@dataclass
class ScenarioConfig:
    """PLACEHOLDER_INCOMPLETE_DO_NOT_USE - reconstruction in progress"""
    pass
