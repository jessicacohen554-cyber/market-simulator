#!/usr/bin/env python3
"""capx D75-R-ARM byte-identity gate — the PJM VRE-vintage arm moves PJM
FORECAST keys and NOTHING else.

**What this checks.** Owner ruling **Q55** (capx ledger §3, r#51) arms
``pjm_vre_accreditation_vintage`` for PJM the D57/Q44 way — through
``config/iso_configs.py::_pjm_config``'s ``default_scenario_overrides``, leaving
the shared ``ScenarioConfig`` dataclass default **False**. The property that
makes that posture safe is narrow and testable:

* **every non-PJM committed run config: ZERO key moves** — the override lives on
  PJM's ``ISOConfig`` and no other ISO reads it (rule 25 ``[R-ISO-SCOPE]``);
* **every BACKCAST committed run config, PJM's included: ZERO key moves** —
  ``ScenarioConfig.__post_init__`` coerces the field back to its dataclass
  default in ``mode="backcast"``, so no backcast keeper can be re-keyed;
* **PJM FORECAST configs move**, and are listed rather than counted, because a
  moved key is the *intended* effect and must be inspectable.

Any other pattern is a STOP, not a number to record. In particular a non-PJM or
backcast move would mean the arm had been landed as a shared-default flip
(``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS``) instead of an ISO override — the
variant that orphans all six backcast keepers and was never licensed.

**Method** — the ``capxd79_solve_surface_no_op_check`` probe's shape, one axis
over. Both keys are taken on the SAME committed ``scenario_config`` payload, so
the comparison isolates the arm and nothing else:

* **pre** — the payload hashed as committed;
* **post** — the payload with ``pjm_vre_accreditation_vintage`` set to the value
  the arm RESOLVES for that payload's ``(iso, mode)``, then hashed identically.

The resolved value is never hand-written: it is read back from the shipped
``apply_iso_scenario_defaults`` → ``ScenarioConfig.__post_init__`` path, so the
probe inherits the real override semantics (including the backcast coercion and
the OVERRIDE-FIX explicit-caller rule) rather than restating them.

``--simulate-arm`` injects the override into ``_pjm_config``'s resolved
``ISOConfig`` **in memory** instead of reading it off disk, so this one
instrument produces both records: the **ex-ante expectation** recorded in
``PRECOMMIT-capx-d75r-arm-2026-09-06.md`` before ``iso_configs.py`` was touched,
and the **ex-post measurement** taken after the edit with the flag omitted. The
two must agree exactly; that they do is the gate.

Usage::

    # ex ante, before the edit
    uv run python scripts/probes/capxd75rarm_iso_override_no_op_check.py \
        --simulate-arm --out docs/handoffs/d75rarm/no-op-expectation.json

    # ex post, after the edit
    uv run python scripts/probes/capxd75rarm_iso_override_no_op_check.py \
        --out docs/handoffs/d75rarm/no-op-measured.json

Exit code 0 iff the pattern holds: zero non-PJM moves, zero backcast moves.
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

from market_sim.config import iso_configs  # noqa: E402
from market_sim.config.scenarios import (  # noqa: E402
    _CACHE_KEY_OPTIONAL_FIELDS,
    _CACHE_KEY_RETIRED_FIELDS,
    ScenarioConfig,
    _cache_key_path_roots,
    _normalize_cache_key_paths,
    cache_key_drop_defaults,
)

#: The field owner ruling Q55 arms. One name, stated once.
FIELD = "pjm_vre_accreditation_vintage"

#: The ISO the ruling arms it for (rule 25 ``[R-ISO-SCOPE]``).
ARMED_ISO = "PJM"


def _jsonable(value):
    """Round-trip a value through JSON so tuples and lists compare equal."""
    return json.loads(json.dumps(value, default=str))


def _key(payload: dict, drop_at: dict, roots) -> str:
    """Hash one config payload under the live cache-key rules."""
    out = dict(payload)
    for name in _CACHE_KEY_OPTIONAL_FIELDS:
        if name in drop_at and name in out and out[name] == drop_at[name]:
            out.pop(name)
    for name, retired_default in _CACHE_KEY_RETIRED_FIELDS.items():
        out.setdefault(name, _jsonable(retired_default))
    out = _normalize_cache_key_paths(out, roots)
    return hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()[:16]


def _install_simulated_arm() -> None:
    """Inject the Q55 override into PJM's ``ISOConfig`` in memory.

    Lets the probe measure the arm's effect BEFORE ``iso_configs.py`` is edited,
    so the PRECOMMIT's expectation and the post-edit measurement come off one
    instrument. Wraps ``get_iso_config`` rather than rewriting the module, so
    every other ISO's config is returned untouched.
    """
    inner = iso_configs.get_iso_config

    def patched(iso: str):
        cfg = inner(iso)
        if iso.upper() == ARMED_ISO and FIELD not in cfg.default_scenario_overrides:
            cfg.default_scenario_overrides[FIELD] = True
        return cfg

    iso_configs.get_iso_config = patched


def _resolved_value(iso: str, mode: str, hindcast: bool) -> bool:
    """The value the ARM resolves for one ``(iso, mode)``, off the shipped path.

    Runs ``apply_iso_scenario_defaults`` on a bare config for that ISO and mode,
    so the backcast coercion in ``ScenarioConfig.__post_init__`` and the
    override's own explicit-caller rule both apply exactly as they do in a real
    build. Nothing about the semantics is restated here.
    """
    base = ScenarioConfig(iso=iso, mode=mode, hindcast=hindcast)
    resolved = iso_configs.apply_iso_scenario_defaults(base, iso)
    return bool(getattr(resolved, FIELD, False))


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


def _recipe_legs() -> dict[str, dict[str, object]]:
    """The bare T1-H recipe key per ISO, plus PJM's plain-backcast key.

    The committed-payload sweep answers "does an existing bundle re-key"; this
    answers "does a future run of the shipped recipe re-key", which is the
    question the arm is actually about. Both are reported.
    """
    from scripts.run_capacity_hindcast import build_config

    legs: dict[str, dict[str, object]] = {}
    for iso in ("PJM", "MISO", "NYISO", "NEISO", "CAISO", "ERCOT"):
        cfg = build_config(
            iso, 2021, 2025, "realized", vintage=2020, entry_screen_diagnostics=True
        )
        resolved = iso_configs.apply_iso_scenario_defaults(cfg, iso)
        legs[f"{iso.lower()}-t1h-bare"] = {
            "cache_key": resolved.cache_key(),
            FIELD: bool(getattr(resolved, FIELD, False)),
        }
    back = ScenarioConfig(iso=ARMED_ISO, mode="backcast")
    resolved_back = iso_configs.apply_iso_scenario_defaults(back, ARMED_ISO)
    legs["pjm-plain-backcast"] = {
        "cache_key": resolved_back.cache_key(),
        "unresolved_cache_key": back.cache_key(),
        "unmoved": resolved_back.cache_key() == back.cache_key(),
        FIELD: bool(getattr(resolved_back, FIELD, False)),
    }
    return legs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="write the JSON record here")
    ap.add_argument(
        "--simulate-arm",
        action="store_true",
        help="inject the Q55 override in memory (use BEFORE iso_configs.py is edited)",
    )
    args = ap.parse_args(argv)

    if args.simulate_arm:
        _install_simulated_arm()

    armed_live = (
        FIELD in iso_configs.get_iso_config(ARMED_ISO).default_scenario_overrides
    )
    roots = _cache_key_path_roots()
    drop_at = {name: _jsonable(v) for name, v in cache_key_drop_defaults().items()}

    rows: list[dict] = []
    resolved_cache: dict[tuple[str, str, bool], bool] = {}
    for path in _committed_run_configs():
        record = json.loads(path.read_text())
        payload = record.get("scenario_config")
        if not isinstance(payload, dict):
            continue
        payload = _jsonable(payload)
        iso = str(payload.get("iso"))
        mode = str(payload.get("mode"))
        hindcast = bool(payload.get("hindcast", False))
        ck = (iso, mode, hindcast)
        if ck not in resolved_cache:
            resolved_cache[ck] = _resolved_value(iso, mode, hindcast)
        pre_key = _key(payload, drop_at, roots)
        after = dict(payload)
        after[FIELD] = resolved_cache[ck]
        post_key = _key(after, drop_at, roots)
        rows.append(
            {
                "run_config": str(path.relative_to(_REPO)),
                "mode": mode,
                "iso": iso,
                "recorded_cache_key": record.get("cache_key"),
                "committed_field_value": payload.get(FIELD),
                "resolved_field_value": resolved_cache[ck],
                "key_pre_arm": pre_key,
                "key_post_arm": post_key,
                "moved": pre_key != post_key,
            }
        )

    moved = [r for r in rows if r["moved"]]
    off_target = [r for r in moved if r["iso"] != ARMED_ISO or r["mode"] != "forecast"]
    by_bucket: dict[str, dict[str, int]] = {}
    for row in rows:
        bucket = by_bucket.setdefault(
            f"{row['iso']}/{row['mode']}", {"configs": 0, "moved": 0}
        )
        bucket["configs"] += 1
        bucket["moved"] += int(row["moved"])

    record = {
        "probe": "capxd75rarm_iso_override_no_op_check",
        "ruling": "Q55 (capx ledger §3, r#51) — ARM pjm_vre_accreditation_vintage for PJM",
        "field": FIELD,
        "armed_iso": ARMED_ISO,
        "simulated": bool(args.simulate_arm),
        "override_present_on_disk": armed_live,
        "configs_checked": len(rows),
        "keys_moved": len(moved),
        "keys_moved_off_target": len(off_target),
        "by_bucket": dict(sorted(by_bucket.items())),
        "recipe_legs": _recipe_legs(),
        "moved_detail": moved,
        "off_target_detail": off_target,
        "rows": rows,
    }
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(record, indent=2, sort_keys=False) + "\n")

    print(
        "{} committed run configs; override {} on disk{}".format(
            len(rows),
            "PRESENT" if armed_live else "ABSENT",
            " (SIMULATED in memory)" if args.simulate_arm else "",
        )
    )
    for name, counts in record["by_bucket"].items():
        print(
            "  {:18s} {:3d} configs, {:3d} moved".format(
                name, counts["configs"], counts["moved"]
            )
        )
    for leg, info in record["recipe_legs"].items():
        print(
            "  recipe {:22s} {}  {}={}".format(
                leg, info["cache_key"], FIELD, info[FIELD]
            )
        )
    if off_target:
        print(
            "STOP: {} key(s) moved outside {}/forecast — the arm is not an ISO "
            "override:".format(len(off_target), ARMED_ISO)
        )
        for row in off_target:
            print("  {} {} {}".format(row["iso"], row["mode"], row["run_config"]))
        return 1
    print(
        "ok: {} key(s) moved, ALL of them {}/forecast; every non-{} and every "
        "backcast config byte-identical".format(len(moved), ARMED_ISO, ARMED_ISO)
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
