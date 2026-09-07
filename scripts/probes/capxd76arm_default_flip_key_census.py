#!/usr/bin/env python3
"""capx D76-ARM key census — what a DEFAULT FLIP of
``capacity_screen_peak_measured_hindcast`` does to every committed cache key.

**The question this exists to answer.** Owner ruling **Q57** (capx ledger
§0ay.3(a)) arms the measured-hindcast capacity-screen peak "via the D50 (b′-1)
route": a declared default flip with the frozen drop value in
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`` left at ``"False"``, "so existing bundles
keep their keys". The ruling attaches a STOP the lane cannot argue with — *"do
not COMMIT the flip until zero key moves is verified; if it cannot be, STOP and
return to the owner"* — so the flip's key-move count has to be **measured**,
config by config, before ``scenarios.py`` is touched.

**The arithmetic being measured** (``scenarios.py::cache_key``). Since owner
ruling Q20 (capx D24, option (b′-1)) a registered field is dropped from the hash
iff it equals its **FROZEN DECLARATION**, not the live default. ``cache_key()``
hashes ``asdict(self)``, so a live config always carries the field. Hence, after
a flip:

* a config resolving the OLD value (explicitly, or by coercion) still equals the
  frozen ``False``, is dropped, and its key is **unmoved**;
* a config resolving the NEW default no longer equals it, **enters** the hash,
  and its key **moves**.

That second line is the route working as designed — it is what stops a post-flip
armed run being served the pre-flip unarmed bundle (D24 §4.1/§4.2) — so a
landing with *no* moves anywhere is a landing with a same-key collision. The
census therefore reports two numbers and never collapses them: **total moves**
and **off-target moves** (a move in a config the mechanism cannot reach, which
is a pure cache miss for byte-identical behaviour).

**Two variants, both measured, neither chosen here.**

``--variant a``
    the flip alone. Every payload lacking the field resolves the new default.

``--variant b``
    the flip plus the ``__post_init__`` coercion every sibling gate already
    ships (``capacity_no_default_cap_convention_by_iso``,
    ``capacity_market_supply_clearing_by_iso``,
    ``capacity_going_forward_bar_published_by_iso``,
    ``capacity_adequacy_requirement_published_by_iso``,
    ``retirement_sector_gate``): the field is forced back to the frozen
    ``False`` whenever ``not config.hindcast`` — the one predicate under which
    the gate is inert for the WHOLE run rather than year by year.

Variant b is measured because the two immediate precedents (D75-R-ARM, D78-ARM)
both report their arms that way — "every backcast config byte-identical, the
target's own configs move and are listed". Measuring it is not the same as
landing it, and this probe lands nothing.

**Instrument validation comes first, and it is not optional.** 148 of the
committed ``run_config.json`` payloads record their own ``cache_key``. Hashing
the payload under the live drop rules must reproduce that literal; a payload
that does not reproduce is reported under ``instrument_mismatch`` and **excluded
from the move counts**, never silently averaged in. Without that check the
census would be a hash of a hash of nothing in particular.

``--simulate-flip`` is the default posture and needs no flag: the probe never
reads the live default for the post-flip side, it applies the flip
arithmetically to each payload, so the ex-ante record (``scenarios.py``
untouched) and the ex-post record (after an edit) are produced by the same code
path and must agree exactly. ``--check-live`` additionally asserts that the live
dataclass default matches ``--expect-live-default``, so a post-edit run can
prove it is measuring the edited tree.

Usage::

    # ex ante, before scenarios.py is touched
    uv run python scripts/probes/capxd76arm_default_flip_key_census.py \
        --variant a --out docs/handoffs/d76arm/key-census-variant-a.json
    uv run python scripts/probes/capxd76arm_default_flip_key_census.py \
        --variant b --out docs/handoffs/d76arm/key-census-variant-b.json

Exit code 0 iff the instrument validates AND the total move count is zero; 2
when the instrument validates but keys move (the STOP the ruling names); 1 on an
instrument failure.
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

#: The field owner ruling Q57 flips. One name, stated once.
FIELD = "capacity_screen_peak_measured_hindcast"

#: The value the field is registered at in ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS``
#: — the FROZEN drop value (b′-1) forbids editing. Read back from the shipped
#: resolver rather than restated, so this probe cannot disagree with the code.
FROZEN_DROP_VALUE = cache_key_drop_defaults().get(FIELD)

#: The default before the flip, and the default after it.
PRE_FLIP_DEFAULT = False
POST_FLIP_DEFAULT = True


def _jsonable(value):
    """Round-trip a value through JSON so tuples and lists compare equal."""
    return json.loads(json.dumps(value, default=str))


def _key(payload: dict, drop_at: dict, roots) -> str:
    """Hash one config payload under the live cache-key rules.

    The same construction ``capxd78arm_iso_override_no_op_check._key`` uses, so
    the two lanes' censuses are comparable. It reproduces
    ``ScenarioConfig.cache_key`` for any payload that is a faithful
    ``asdict(config)`` — which the instrument-validation step verifies against
    the payloads' own recorded ``cache_key`` rather than assuming.
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


def _post_flip_value(payload: dict, variant: str) -> bool:
    """The value the post-flip shipped path resolves for one committed payload.

    An EXPLICIT value is unaffected by a default flip and is carried through
    unchanged — that is the whole property (b′-1) buys ("an explicit False still
    selects the pre-flip construction and keeps its key"). Only an ABSENT field
    picks up the new default. Variant ``b`` then applies the non-hindcast
    coercion described in the module docstring.
    """
    if FIELD in payload:
        return bool(payload[FIELD])
    if variant == "b" and not bool(payload.get("hindcast", False)):
        return PRE_FLIP_DEFAULT
    return POST_FLIP_DEFAULT


def _pre_flip_value(payload: dict) -> bool:
    """The value the PRE-flip shipped path resolves for one committed payload."""
    if FIELD in payload:
        return bool(payload[FIELD])
    return PRE_FLIP_DEFAULT


def _recipe_legs(variant: str, drop_at: dict, roots) -> dict:
    """The bare recipe keys a FUTURE run would take, per ISO.

    The committed-payload sweep answers "does an existing bundle re-key"; this
    answers "does the shipped recipe re-key", which is the question a lane
    re-solving a frontier bundle actually hits. Both are reported. Built off
    ``asdict`` of a resolved config so the flip is applied by the same
    arithmetic as the sweep and the two cannot disagree.
    """
    from dataclasses import asdict

    from market_sim.config import iso_configs

    legs: dict[str, dict[str, object]] = {}

    def _leg(name: str, cfg: ScenarioConfig) -> None:
        payload = _jsonable(asdict(cfg))
        pre = dict(payload)
        pre[FIELD] = _pre_flip_value({k: v for k, v in payload.items() if k != FIELD})
        post = dict(payload)
        post[FIELD] = _post_flip_value(
            {k: v for k, v in payload.items() if k != FIELD}, variant
        )
        legs[name] = {
            "key_pre_flip": _key(pre, drop_at, roots),
            "key_post_flip": _key(post, drop_at, roots),
            "moved": _key(pre, drop_at, roots) != _key(post, drop_at, roots),
            "hindcast": bool(payload.get("hindcast", False)),
            "mode": payload.get("mode"),
        }

    try:
        from scripts.run_capacity_hindcast import build_config
    except Exception as exc:  # pragma: no cover - harness import guard
        legs["__hindcast_recipes_unavailable__"] = {"reason": repr(exc)}
        build_config = None

    for iso in iso_configs.SUPPORTED_ISOS:
        if build_config is not None:
            try:
                cfg = build_config(
                    iso,
                    2021,
                    2025,
                    "realized",
                    vintage=2020,
                    entry_screen_diagnostics=True,
                )
                _leg(
                    f"{iso.lower()}-t1h-bare",
                    iso_configs.apply_iso_scenario_defaults(cfg, iso),
                )
            except Exception as exc:  # pragma: no cover - per-ISO recipe guard
                legs[f"{iso.lower()}-t1h-bare"] = {"unavailable": repr(exc)}
        back = ScenarioConfig(iso=iso, mode="backcast")
        _leg(
            f"{iso.lower()}-plain-backcast",
            iso_configs.apply_iso_scenario_defaults(back, iso),
        )
    return legs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="write the JSON record here")
    ap.add_argument(
        "--variant",
        choices=("a", "b"),
        default="a",
        help="a = the flip alone; b = the flip plus the non-hindcast coercion",
    )
    ap.add_argument(
        "--expect-live-default",
        choices=("true", "false"),
        help="assert the live dataclass default is this, and fail if it is not",
    )
    args = ap.parse_args(argv)

    live_default = bool(getattr(ScenarioConfig(), FIELD))
    if args.expect_live_default is not None:
        want = args.expect_live_default == "true"
        if live_default is not want:
            print(
                "FAIL: live default is {}, expected {}".format(live_default, want),
                file=sys.stderr,
            )
            return 1

    roots = _cache_key_path_roots()
    drop_at = {name: _jsonable(v) for name, v in cache_key_drop_defaults().items()}

    rows: list[dict] = []
    mismatches: list[dict] = []
    for path in _committed_run_configs():
        record = json.loads(path.read_text())
        payload = record.get("scenario_config")
        if not isinstance(payload, dict):
            continue
        payload = _jsonable(payload)
        recorded = record.get("cache_key")
        pre_val = _pre_flip_value(payload)
        post_val = _post_flip_value(payload, args.variant)
        before = dict(payload)
        before[FIELD] = pre_val
        after = dict(payload)
        after[FIELD] = post_val
        pre_key = _key(before, drop_at, roots)
        post_key = _key(after, drop_at, roots)
        # INSTRUMENT VALIDATION: the pre-flip key computed here must reproduce
        # the key the bundle recorded for itself. A payload with no recorded key
        # cannot validate and is marked, not assumed.
        reproduces = None
        if isinstance(recorded, str) and recorded:
            reproduces = recorded == pre_key
        row = {
            "run_config": str(path.relative_to(_REPO)),
            "iso": payload.get("iso"),
            "mode": payload.get("mode"),
            "hindcast": bool(payload.get("hindcast", False)),
            "committed_field_value": payload.get(FIELD, None),
            "field_recorded": FIELD in payload,
            "resolved_pre_flip": pre_val,
            "resolved_post_flip": post_val,
            "recorded_cache_key": recorded,
            "key_pre_flip": pre_key,
            "key_post_flip": post_key,
            "reproduces_recorded_key": reproduces,
            "moved": pre_key != post_key,
        }
        rows.append(row)
        if reproduces is False:
            mismatches.append(row)

    validated = [r for r in rows if r["reproduces_recorded_key"] is True]
    unvalidatable = [r for r in rows if r["reproduces_recorded_key"] is None]
    counted = [r for r in rows if r["reproduces_recorded_key"] is not False]
    moved = [r for r in counted if r["moved"]]
    # OFF TARGET = a move in a config the mechanism cannot reach. The gate's own
    # predicate is ``config.hindcast and not is_crossover_forward_year(year)``,
    # so a non-hindcast config is inert for its whole horizon: a key move there
    # buys nothing and orphans a cache for byte-identical behaviour.
    off_target = [r for r in moved if not r["hindcast"]]
    # A row's MOVE verdict does not depend on the instrument reproducing its
    # recorded key: under (b'-1) a row moves iff its resolved value stops
    # equalling the frozen drop value, which is a property of the payload's
    # field, not of the hash. So the mismatched rows are excluded from the
    # VALIDATED counts above and reported again here at full population, and the
    # two numbers must be read together rather than one being quoted alone.
    moved_all = [r for r in rows if r["moved"]]
    off_target_all = [r for r in moved_all if not r["hindcast"]]

    by_bucket: dict[str, dict[str, int]] = {}
    for row in counted:
        name = "{}/{}".format(
            row["mode"], "hindcast" if row["hindcast"] else "not-hindcast"
        )
        bucket = by_bucket.setdefault(name, {"configs": 0, "moved": 0})
        bucket["configs"] += 1
        bucket["moved"] += int(row["moved"])

    out_record = {
        "probe": "capxd76arm_default_flip_key_census",
        "ruling": "Q57 (capx ledger §0ay.3(a)) — ARM capacity_screen_peak_measured_hindcast "
        "via the D50 (b'-1) route",
        "field": FIELD,
        "variant": args.variant,
        "frozen_drop_value": FROZEN_DROP_VALUE,
        "live_dataclass_default": live_default,
        "pre_flip_default": PRE_FLIP_DEFAULT,
        "post_flip_default": POST_FLIP_DEFAULT,
        "configs_checked": len(rows),
        "instrument_validated": len(validated),
        "instrument_unvalidatable_no_recorded_key": len(unvalidatable),
        "instrument_mismatch": len(mismatches),
        "keys_moved": len(moved),
        "keys_moved_off_target": len(off_target),
        "keys_moved_all_rows": len(moved_all),
        "keys_moved_off_target_all_rows": len(off_target_all),
        "by_bucket": dict(sorted(by_bucket.items())),
        "recipe_legs": _recipe_legs(args.variant, drop_at, roots),
        "moved_detail": moved,
        "instrument_mismatch_detail": mismatches,
        "rows": rows,
    }
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out_record, indent=2, sort_keys=False) + "\n")

    print(
        "variant {}: {} committed run configs; live default {}; frozen drop value {}".format(
            args.variant, len(rows), live_default, FROZEN_DROP_VALUE
        )
    )
    print(
        "  instrument: {} reproduce their recorded key, {} have none to check, "
        "{} MISMATCH".format(len(validated), len(unvalidatable), len(mismatches))
    )
    for name, counts in out_record["by_bucket"].items():
        print(
            "  {:24s} {:3d} configs, {:3d} moved".format(
                name, counts["configs"], counts["moved"]
            )
        )
    print(
        "  TOTAL moved {} of {} counted; OFF TARGET (non-hindcast) {}".format(
            len(moved), len(counted), len(off_target)
        )
    )
    print(
        "  ALL ROWS (mismatched included, whose move verdict is hash-independent): "
        "moved {} of {}; OFF TARGET {}".format(
            len(moved_all), len(rows), len(off_target_all)
        )
    )
    if mismatches:
        print(
            "FAIL: the instrument does not reproduce {} recorded key(s)".format(
                len(mismatches)
            )
        )
        return 1
    if moved:
        print(
            "STOP (owner ruling Q57): {} key(s) move — the flip is NOT a zero-key-move "
            "landing. Do not commit it; return to the owner.".format(len(moved))
        )
        return 2
    print("ok: zero key moves")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
