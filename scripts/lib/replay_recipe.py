"""Replay-recipe fidelity: a keeper's replay must reproduce each year's solved config.

A composed keeper records ONE base recipe in ``meta.json`` plus, for a bundle
whose years solved under different recipes, a per-year
``config_partition_overrides`` block (``scripts/stamp_config_partition.py``).
``replay_keeper.py <bundle> --years Y`` rebuilds year ``Y`` from exactly those
two. If the composer took ``meta.json`` from the wrong leg, or never stamped
the block, the replay silently solves a different recipe than the one scored —
the W0 phase-3 ERCOT defect (``w0_ercot_span`` recorded its 2019 validation
recipe as the base, so every year replayed the validation config).

This module checks the property at zero LP: for each year carrying a
``run_config_<Y>.json``, reconstruct what ``replay_keeper --years Y`` hands
``run_year`` (``build_kwargs`` + the partition overlay + the derived inputs +
the year's gas print), resolve it with ``run_year(fleet_only=True)``, and diff
the resolved ``ScenarioConfig`` against the recorded one. Resolved, not raw:
``meta.json`` legitimately records values that resolve differently (a W0 field
that yields to an armed alternative, a flag a later run_year stage re-sets),
so only the resolved config is a faithful test.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
from pathlib import Path
from typing import Callable

#: Bookkeeping fields that are not part of the recipe.
NON_RECIPE_FIELDS = frozenset({"_explicitly_set_fields"})


def _norm(value: object) -> object:
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def resolve_replay_config(bundle: Path, year: int) -> dict:
    """The ``ScenarioConfig`` (as a dict) ``replay_keeper --years year`` would solve."""
    from scripts.replay_keeper import (
        RUN_YEAR_NON_RECIPE,
        RUN_YEAR_REMAP,
        build_kwargs,
        derived_run_year_inputs,
        enforce_single_recipe_partition,
    )
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = build_kwargs(meta)
    enforce_single_recipe_partition(meta, [int(year)], kwargs)
    params = set(inspect.signature(run_year).parameters)
    run_kwargs = {}
    for key, value in kwargs.items():
        target = RUN_YEAR_REMAP.get(key, key)
        if target in params and target not in RUN_YEAR_NON_RECIPE:
            run_kwargs[target] = value
    run_kwargs.update(derived_run_year_inputs(bundle, int(year)))
    gas = (meta.get("gas_prices") or {}).get(str(year), meta.get("gas_price"))
    result = run_year(
        int(year), meta["iso"], 8760, gas, {}, fleet_only=True, **run_kwargs
    )
    config = result["config"]
    return {f.name: getattr(config, f.name) for f in dataclasses.fields(config)}


def replay_config_diffs(
    bundle: Path,
    year: int,
    resolve: Callable[[Path, int], dict] = resolve_replay_config,
) -> dict[str, tuple[object, object]]:
    """``{field: (recorded, replayed)}`` for every field the replay gets wrong.

    Empty when the bundle has no ``run_config_<year>.json`` (nothing recorded
    to compare against) or when the replay reproduces it exactly.
    """
    path = bundle / f"run_config_{int(year)}.json"
    if not path.is_file():
        return {}
    recorded = json.loads(path.read_text()).get("scenario_config") or {}
    replayed = resolve(bundle, int(year))
    return {
        key: (recorded.get(key), replayed.get(key))
        for key in sorted(set(recorded) | set(replayed))
        if key not in NON_RECIPE_FIELDS
        and _norm(recorded.get(key)) != _norm(replayed.get(key))
    }
