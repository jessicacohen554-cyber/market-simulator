"""Validate the parameter citation registry against the model code.

Cross-checks that every constant in ``src/market_sim/config/constants.py`` and
every ``ScenarioConfig`` dataclass default has a matching entry in
``frontend/data/parameters.json``.

Prints any missing entries and exits non-zero if the registry is incomplete.
Also reports parameters flagged as model-sourced (not empirical) or stale
(primary source older than three years) so they can be queued for review.

Run: ``python scripts/validate_parameters.py``
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from dataclasses import fields
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO / "frontend/data/parameters.json"
STALE_YEARS = 3

sys.path.insert(0, str(REPO / "src"))

from market_sim.config import constants  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402


def _is_year_keyed(value: dict) -> bool:
    """Return True if a dict's keys are all integers (a year-indexed trajectory)."""
    return bool(value) and all(isinstance(k, int) for k in value)


def _flatten(prefix: str, value: object):
    """Yield leaf ``param_id`` strings for a constant.

    String-keyed dicts recurse with dotted paths; year-keyed dicts, dicts with
    non-string keys (e.g. tuple-keyed interface tables, which a dotted path
    cannot address), lists and scalars are treated as single leaves.
    """
    if (
        isinstance(value, dict)
        and not _is_year_keyed(value)
        and all(isinstance(k, str) for k in value)
    ):
        for key, sub in value.items():
            yield from _flatten(f"{prefix}.{key}", sub)
    else:
        yield prefix


def expected_param_ids() -> dict[str, object]:
    """Return the ``param_id`` -> value mapping required by the model code."""
    expected: dict[str, object] = {}

    for name, value in vars(constants).items():
        if name.startswith("_") or not name.isupper():
            continue
        if not isinstance(value, (int, float, str, dict, list)):
            continue
        for leaf in _flatten(name.lower(), value):
            expected[leaf] = _value_at(value, leaf, name.lower())

    defaults = ScenarioConfig()
    for f in fields(defaults):
        expected[f"scenario.{f.name}"] = getattr(defaults, f.name)

    return expected


def _value_at(root: object, param_id: str, root_name: str) -> object:
    """Walk the dotted ``param_id`` into ``root`` and return the leaf value."""
    node = root
    for key in param_id[len(root_name) :].split(".")[1:]:
        node = node[key]
    return node


def _normalize(value: object) -> object:
    """Make registry and code values comparable (JSON turns int keys into str)."""
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, float):
        return round(value, 9)
    return value


def main() -> int:
    if not REGISTRY_PATH.exists():
        print(f"ERROR: registry not found at {REGISTRY_PATH}")
        return 1

    registry = json.loads(REGISTRY_PATH.read_text())
    entries = registry["parameters"] if isinstance(registry, dict) else registry
    by_id = {e["param_id"]: e for e in entries}

    expected = expected_param_ids()

    missing = sorted(pid for pid in expected if pid not in by_id)
    orphan = sorted(pid for pid in by_id if pid not in expected)
    mismatched: list[str] = []
    for pid, code_value in expected.items():
        entry = by_id.get(pid)
        if entry is None:
            continue
        if _normalize(entry["value"]) != _normalize(code_value):
            mismatched.append(f"{pid}: code={code_value!r} registry={entry['value']!r}")

    print(f"Registry:    {len(by_id)} entries in {REGISTRY_PATH.name}")
    print(
        f"Code:        {len(expected)} parameters "
        f"(constants.py + ScenarioConfig defaults)"
    )
    print()

    if missing:
        print(f"MISSING — {len(missing)} parameter(s) have no registry entry:")
        for pid in missing:
            print(f"  - {pid}")
        print()

    if orphan:
        print(f"WARNING — {len(orphan)} registry entr(ies) match no code parameter:")
        for pid in orphan:
            print(f"  - {pid}")
        print()

    if mismatched:
        print(
            f"WARNING — {len(mismatched)} value mismatch(es) between code and registry:"
        )
        for line in sorted(mismatched):
            print(f"  - {line}")
        print()

    modeled = sorted(e["param_id"] for e in entries if "modeled" in e.get("flags", []))
    if modeled:
        print(
            f"FLAG — {len(modeled)} parameter(s) sourced from a model, not "
            "empirical data (review the assumption):"
        )
        for pid in modeled:
            print(f"  - {pid}  [{by_id[pid]['source']}]")
        print()

    cutoff = (dt.date.today() - dt.timedelta(days=365 * STALE_YEARS)).strftime("%Y-%m")
    stale = sorted(
        e["param_id"] for e in entries if str(e.get("source_date", "")) < cutoff
    )
    if stale:
        print(
            f"FLAG — {len(stale)} parameter(s) with a primary source older "
            f"than {STALE_YEARS} years (refresh review, cutoff {cutoff}):"
        )
        for pid in stale:
            print(f"  - {pid}  [{by_id[pid]['source']}, {by_id[pid]['source_date']}]")
        print()

    if missing:
        print(f"FAIL: {len(missing)} parameter(s) missing a citation entry.")
        return 1

    print("OK: every constant and ScenarioConfig default has a citation entry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
