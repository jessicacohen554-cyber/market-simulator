#!/usr/bin/env python3
"""capx D24-R merge gate — prove option (b′-1) moves ZERO cache keys.

**What this checks, and why it is the merge gate.** Owner ruling Q20 licensed
option **(b′-1)** of
``docs/handoffs/FINDING-capx-d24-cache-key-defect-2026-09-01.md`` §7: freeze
``cache_key``'s drop comparison against the DECLARED default in
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`` instead of the live one, re-baselined at
**today's** declarations. Re-baselined that way the change is a measured no-op —
0 forecast keys, 0 backcast keys — because guard check 3
(``scripts/check_cache_key_registration.py``) already forces declared == live for
every registered field.

**Any key that MOVES means (b′-2) was implemented instead**, i.e. the comparison
was re-baselined at each field's *registration-time* default. That variant moves
98/99 forecast and 63/63 backcast keys (D24 §7), orphans every on-disk cache in
both lanes including all six backcast keepers, and was **not licensed**. So a
non-zero move count is a stop, not a number to record.

**Method.** Both rules are applied to the SAME committed ``scenario_config``
payload, so the comparison isolates the drop rule and nothing else:

* **old rule** — drop a registered field at ``getattr(ScenarioConfig(), name)``,
  the live default (the pre-repair algorithm);
* **new rule** — drop it at the frozen declaration
  (``cache_key_drop_defaults()``).

Everything downstream of the drop (retired-field re-insertion, path folding,
``json.dumps(sort_keys=True)``, ``sha256[:16]``) is identical between the two, so
an equal key under both rules IS the no-op claim for that config.

The key printed here is NOT expected to equal the run's recorded ``cache_key``:
the recorded key was hashed against the schema of its own solve day, and
``ScenarioConfig`` has grown since. This probe deliberately asks a narrower and
answerable question — *does MY change move it* — rather than reproducing history
(which D24 §1.1 already did, 94/98).

Values are compared JSON-normalized (``json.dumps`` round-trip) because six
``*_offer_surface_netload_pcts`` / ``*_position_bins`` fields are tuples in
``asdict`` and lists in the committed JSON; a naive ``==`` leaves them in the
hash and no key reproduces (D24 §1.1). Both rules get the same normalization, so
the comparison stays exact.

Usage::

    uv run python scripts/probes/capxd24r_cache_key_no_op_check.py \
        --out docs/handoffs/capxd24r-cache-key-no-op-record.json

Exit code 0 iff every committed config hashes identically under both rules.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from market_sim.config.scenarios import (  # noqa: E402
    _CACHE_KEY_OPTIONAL_FIELDS,
    _CACHE_KEY_RETIRED_FIELDS,
    _cache_key_path_roots,
    _normalize_cache_key_paths,
    ScenarioConfig,
    cache_key_drop_defaults,
)


def _jsonable(value):
    """Round-trip a value through JSON so tuples and lists compare equal."""
    return json.loads(json.dumps(value, default=str))


def _key(payload: dict, drop_at: dict, roots) -> str:
    """Hash one config payload under a given drop rule.

    Args:
        payload: The run's ``scenario_config`` dict.
        drop_at: Registered field name -> the value it is dropped at.
        roots: Path sentinels from ``_cache_key_path_roots``.

    Returns:
        The 16-hex cache key.
    """
    out = dict(payload)
    for name in _CACHE_KEY_OPTIONAL_FIELDS:
        if name in drop_at and name in out and out[name] == drop_at[name]:
            out.pop(name)
    for name, retired_default in _CACHE_KEY_RETIRED_FIELDS.items():
        out.setdefault(name, _jsonable(retired_default))
    out = _normalize_cache_key_paths(out, roots)
    return hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()[:16]


def _committed_run_configs() -> list[Path]:
    """Every ``run_config.json`` tracked by git, forecast and backcast alike."""
    out = subprocess.run(
        ["git", "ls-files", "*run_config.json"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [_REPO / rel for rel in sorted(out)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="write the JSON record here")
    args = ap.parse_args(argv)

    roots = _cache_key_path_roots()
    live = ScenarioConfig()
    old_rule = {
        name: _jsonable(getattr(live, name))
        for name in _CACHE_KEY_OPTIONAL_FIELDS
        if hasattr(live, name)
    }
    new_rule = {name: _jsonable(v) for name, v in cache_key_drop_defaults().items()}

    rows: list[dict] = []
    moved: list[dict] = []
    for path in _committed_run_configs():
        record = json.loads(path.read_text())
        payload = record.get("scenario_config")
        if not isinstance(payload, dict):
            continue
        payload = _jsonable(payload)
        old_key = _key(payload, old_rule, roots)
        new_key = _key(payload, new_rule, roots)
        row = {
            "run_config": str(path.relative_to(_REPO)),
            "mode": payload.get("mode"),
            "iso": payload.get("iso"),
            "recorded_cache_key": record.get("cache_key"),
            "fields": len(payload),
            "key_old_rule": old_key,
            "key_new_rule": new_key,
            "moved": old_key != new_key,
        }
        rows.append(row)
        if row["moved"]:
            moved.append(row)

    # The two bare configs as well: they are the keys every pinned literal and
    # every epoch-ledger citation is written against.
    bare = {}
    for label, cfg in (
        ("forecast", ScenarioConfig()),
        ("backcast", ScenarioConfig(mode="backcast")),
    ):
        payload = _jsonable({f: getattr(cfg, f) for f in cfg.__dataclass_fields__})
        bare[label] = {
            "key_old_rule": _key(payload, old_rule, roots),
            "key_new_rule": _key(payload, new_rule, roots),
            "live_cache_key": cfg.cache_key(),
        }

    by_mode: dict[str, dict[str, int]] = {}
    for row in rows:
        bucket = by_mode.setdefault(str(row["mode"]), {"configs": 0, "moved": 0})
        bucket["configs"] += 1
        bucket["moved"] += int(row["moved"])

    record = {
        "probe": "capxd24r_cache_key_no_op_check",
        "ruling": "Q20 (r#25) — option (b′-1) + (c′)",
        "registered_fields": len(_CACHE_KEY_OPTIONAL_FIELDS),
        "declared_defaults_differing_from_live": sorted(
            name
            for name in _CACHE_KEY_OPTIONAL_FIELDS
            if name in new_rule
            and name in old_rule
            and new_rule[name] != old_rule[name]
        ),
        "configs_checked": len(rows),
        "keys_moved": len(moved),
        "by_mode": by_mode,
        "bare_configs": bare,
        "moved_detail": moved,
        "rows": rows,
    }
    if args.out:
        Path(args.out).write_text(json.dumps(record, indent=2, sort_keys=False) + "\n")

    breakdown = ", ".join(
        "{}: {}".format(mode, counts["configs"])
        for mode, counts in sorted(by_mode.items())
    )
    print(f"checked {len(rows)} committed run configs ({breakdown})")
    for label, keys in bare.items():
        print(
            f"  bare {label}: {keys['key_old_rule']} -> {keys['key_new_rule']}"
            f"  (live cache_key {keys['live_cache_key']})"
        )
    if moved:
        print(f"\nFAIL: {len(moved)} key(s) MOVED — that is option (b′-2), not (b′-1):")
        for row in moved[:20]:
            print(
                f"  {row['run_config']}: {row['key_old_rule']} -> {row['key_new_rule']}"
            )
        return 1
    print(f"ok: 0 of {len(rows)} keys moved — (b′-1) is a no-op on every committed run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
