#!/usr/bin/env python3
"""capx D79 merge gate — prove the solve-surface fingerprint moves ZERO keys.

**What this checks, and why it is the merge gate.** Owner ruling Q54 adopted the
hybrid (d) of `docs/handoffs/DESIGN-capx-d79-2026-09-06.md` §6 in its
**FROZEN-HASH** landing form (card row 2, "frozen-hash, now"): every surface name
is declared at its LIVE hash, so ``moved_rows(iso) == {}`` for all six ISOs and
``SOLVE_EPOCHS`` is empty, so neither ``__solve_surface__`` nor
``__solve_epochs__`` reaches any payload and **no committed run's key moves**.

**Any key that MOVES means the EXPLICIT form was implemented instead** — the
fingerprint always in the payload, no frozen declarations (design §5.4). That
variant moves every forecast and backcast key in the program, orphans every
on-disk cache including all six backcast keepers, and was **not** licensed: it
was the alternative the owner declined in favour of landing now. So a non-zero
move count is a stop, not a number to record.

**Method** — the D24-R probe's shape, one layer down. Both rules are applied to
the SAME committed ``scenario_config`` payload, so the comparison isolates the
surface and nothing else:

* **old rule** — the pre-D79 algorithm: drop registered fields at their frozen
  declaration, re-insert retired fields, fold paths, hash;
* **new rule** — identical, plus ``__solve_surface__`` = ``moved_rows(iso)`` and
  ``__solve_epochs__`` = ``applicable_epochs(config)`` when either is non-empty.

The recorded key is NOT expected to equal either: it was hashed against the
schema of its own solve day and ``ScenarioConfig`` has grown since (D24 §1.1).
The probe asks the narrower answerable question — *does MY change move it*.

Values are compared JSON-normalized for the same reason D24-R's probe is: six
``*_pcts`` / ``*_bins`` fields are tuples in ``asdict`` and lists in the
committed JSON, and a naive ``==`` leaves them in the hash so no key reproduces.

Usage::

    uv run python scripts/probes/capxd79_solve_surface_no_op_check.py \
        --out docs/handoffs/capxd79-solve-surface-no-op-record.json

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
    ScenarioConfig,
    _cache_key_path_roots,
    _normalize_cache_key_paths,
    cache_key_drop_defaults,
)
from market_sim.config.solve_surface import (  # noqa: E402
    SOLVE_EPOCHS,
    SURFACE_ISOS,
    applicable_epochs,
    moved_rows,
    surface_fingerprint,
)
from market_sim.config.solve_surface_declared import DECLARED  # noqa: E402


class _ConfigView:
    """The three attributes ``applicable_epochs`` reads, off a stored payload."""

    def __init__(self, payload: dict):
        self.mode = payload.get("mode")
        self.iso = payload.get("iso")
        self.end_year = payload.get("end_year")


def _jsonable(value):
    """Round-trip a value through JSON so tuples and lists compare equal."""
    return json.loads(json.dumps(value, default=str))


def _key(payload: dict, drop_at: dict, roots, *, with_surface: bool) -> str:
    """Hash one config payload, with or without the solve surface."""
    out = dict(payload)
    for name in _CACHE_KEY_OPTIONAL_FIELDS:
        if name in drop_at and name in out and out[name] == drop_at[name]:
            out.pop(name)
    for name, retired_default in _CACHE_KEY_RETIRED_FIELDS.items():
        out.setdefault(name, _jsonable(retired_default))
    if with_surface:
        moved = moved_rows(payload.get("iso"))
        if moved:
            out["__solve_surface__"] = moved
        epochs = applicable_epochs(_ConfigView(payload))
        if epochs:
            out["__solve_epochs__"] = epochs
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
    drop_at = {name: _jsonable(v) for name, v in cache_key_drop_defaults().items()}

    rows: list[dict] = []
    moved: list[dict] = []
    isos_seen: dict[str, int] = {}
    for path in _committed_run_configs():
        record = json.loads(path.read_text())
        payload = record.get("scenario_config")
        if not isinstance(payload, dict):
            continue
        payload = _jsonable(payload)
        old_key = _key(payload, drop_at, roots, with_surface=False)
        new_key = _key(payload, drop_at, roots, with_surface=True)
        iso = str(payload.get("iso"))
        isos_seen[iso] = isos_seen.get(iso, 0) + 1
        row = {
            "run_config": str(path.relative_to(_REPO)),
            "mode": payload.get("mode"),
            "iso": iso,
            "recorded_cache_key": record.get("cache_key"),
            "fields": len(payload),
            "key_pre_d79": old_key,
            "key_post_d79": new_key,
            "moved": old_key != new_key,
        }
        rows.append(row)
        if row["moved"]:
            moved.append(row)

    # The two bare configs: the keys every pinned literal and every epoch-ledger
    # citation is written against.
    bare = {}
    for label, cfg in (
        ("forecast", ScenarioConfig()),
        ("backcast", ScenarioConfig(mode="backcast")),
    ):
        payload = _jsonable({f: getattr(cfg, f) for f in cfg.__dataclass_fields__})
        bare[label] = {
            "key_pre_d79": _key(payload, drop_at, roots, with_surface=False),
            "key_post_d79": _key(payload, drop_at, roots, with_surface=True),
            "live_cache_key": cfg.cache_key(),
        }

    by_mode: dict[str, dict[str, int]] = {}
    for row in rows:
        bucket = by_mode.setdefault(str(row["mode"]), {"configs": 0, "moved": 0})
        bucket["configs"] += 1
        bucket["moved"] += int(row["moved"])

    fingerprint = surface_fingerprint()
    record = {
        "probe": "capxd79_solve_surface_no_op_check",
        "ruling": "Q54 (r#50 amendment 1) — hybrid (d), FROZEN-HASH landing",
        "surface_names": len(fingerprint),
        "surface_names_by_iso_tables": sum(
            1 for v in fingerprint.values() if isinstance(v, dict)
        ),
        "declared_names": len(DECLARED),
        "undeclared_names": sorted(set(fingerprint) - set(DECLARED)),
        "solve_epochs": [e.id for e in SOLVE_EPOCHS],
        "moved_rows_by_iso": {iso: sorted(moved_rows(iso)) for iso in SURFACE_ISOS},
        "configs_checked": len(rows),
        "keys_moved": len(moved),
        "by_mode": by_mode,
        "by_iso": dict(sorted(isos_seen.items())),
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
    print(
        f"{len(fingerprint)} surface names, {len(DECLARED)} declared, "
        f"{len(record['undeclared_names'])} undeclared; "
        f"{len(SOLVE_EPOCHS)} solve epoch(s)"
    )
    for iso in SURFACE_ISOS:
        print(f"  moved_rows({iso}) = {sorted(moved_rows(iso))}")
    print(f"checked {len(rows)} committed run configs ({breakdown})")
    for label, keys in bare.items():
        print(
            f"  bare {label}: {keys['key_pre_d79']} -> {keys['key_post_d79']}"
            f"  (live cache_key {keys['live_cache_key']})"
        )
    if moved:
        print(f"\nFAIL: {len(moved)} key(s) MOVED — that is the EXPLICIT form:")
        for row in moved[:20]:
            print(
                f"  {row['run_config']}: {row['key_pre_d79']} -> "
                f"{row['key_post_d79']}"
            )
        return 1
    print(
        f"ok: 0 of {len(rows)} keys moved — the frozen-hash landing is a no-op "
        "on every committed run"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
