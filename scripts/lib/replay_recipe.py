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
    return json.loads(json.dumps(value, sort_keys=True, default=_json_default))


def _json_default(value: object) -> object:
    """Serialise a set as its sorted members, as run_config records it; else str."""
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=str)
    return str(value)


def resolve_replay_config(bundle: Path, year: int) -> dict:
    """The ``ScenarioConfig`` (as a dict) ``replay_keeper --years year`` would solve."""
    from scripts.replay_keeper import (
        RUN_YEAR_NON_RECIPE,
        RUN_YEAR_REMAP,
        apply_config_overlay,
        build_kwargs,
        derived_run_year_inputs,
        enforce_single_recipe_partition,
        flipped_default_overlay,
    )
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = build_kwargs(meta)
    enforce_single_recipe_partition(meta, [int(year)], kwargs)
    apply_config_overlay(kwargs, flipped_default_overlay(bundle, [int(year)], meta))
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
    deleted = _rule26_inert_recorded(bundle, recorded)
    added = _registered_after_solve(recorded, replayed)
    return {
        key: (recorded.get(key), replayed.get(key))
        for key in sorted(set(recorded) | set(replayed))
        if key not in NON_RECIPE_FIELDS
        and key not in deleted
        and key not in added
        and _norm(recorded.get(key)) != _norm(replayed.get(key))
    }


def _registered_after_solve(recorded: dict, replayed: dict) -> set[str]:
    """Replayed fields absent from the recording that resolve to their absent-equivalent value.

    The mirror of :func:`_rule26_inert_recorded`. A field ADDED to
    ``ScenarioConfig`` after the bundle was solved is absent from its
    ``run_config_<Y>.json``; the replay resolves it to the registered default,
    which is the solved behaviour by construction (a new field ships default-off
    and byte-identical, the nyiso-119 registration discipline). The comparison
    value is :func:`~market_sim.config.scenarios.registration_time_default`, NOT
    today's default: a field whose default was flipped ON after the solve (the
    W0 ``seasonal_capacity_basis``) is absent-equivalent only at its pre-flip
    value. An absent field the replay resolves to anything else is still a
    mismatch, because then the replay arms something the solve never had.
    """
    from market_sim.config.scenarios import ScenarioConfig, registration_time_default

    out: set[str] = set()
    for f in dataclasses.fields(ScenarioConfig):
        if f.name in recorded or f.name not in replayed:
            continue
        try:
            absent_equivalent = registration_time_default(f.name)
        except KeyError:
            continue
        if _norm(replayed[f.name]) == _norm(absent_equivalent):
            out.add(f.name)
    return out


def _rule26_inert_recorded(bundle: Path, recorded: dict) -> set[str]:
    """Recorded keys of rule-26-DELETED fields whose recorded value is inert.

    A bundle solved before a rule-26 [R-DELETE] collapse still records the
    deleted field in its ``run_config_<Y>.json``; the field no longer exists
    at HEAD, so the replay side cannot carry it. ``replay_keeper``'s deletion
    registry already decides which recordings replay faithfully (outside the
    owning ISO, or a value in the declared inert set) — the same registry is
    applied here, so a stale-but-inert recording is not a replay mismatch
    while a recording of the deleted polarity still is.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from scripts.replay_keeper import _RULE26_DELETED_UNCONDITIONAL, _rule26_inert

    live = {f.name for f in dataclasses.fields(ScenarioConfig)}
    iso = str(json.loads((bundle / "meta.json").read_text()).get("iso", "")).upper()
    out: set[str] = set()
    for key, value in recorded.items():
        if key in live or key not in _RULE26_DELETED_UNCONDITIONAL:
            continue
        owner, unconditional = _RULE26_DELETED_UNCONDITIONAL[key]
        if iso != owner or value in _rule26_inert(unconditional):
            out.add(key)
    return out
