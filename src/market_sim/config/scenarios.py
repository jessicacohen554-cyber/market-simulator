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
