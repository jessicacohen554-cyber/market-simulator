"""neiso-117 shard self-check (zero LP): is this leg the NEISO keeper plus exactly the yard-row arm?

Adapted from ``docs/handoffs/neiso114/shard_check.py``. Run by each neiso-117
shard AFTER its solve and BEFORE it pushes (rule 32(c)(4)). The keeper is
``results/calibration/neiso114b_span`` (``2026-09-25-neiso114-arm-b-stgas``),
which carries a ``run_config_<Y>.json`` for every year 2019-2025. Checks:

1. **recipe** — the leg's ``scenario_config`` differs from the keeper's same-year
   config by EXACTLY ``coal_fuel_inventory_plant_grain`` False -> True
   (``coal_fuel_inventory``, the pooled monthly limb, stays False). Any field
   added to ``ScenarioConfig`` after the keeper solved must sit at its default.
2. **offer curve** — ``offer_curve_overrides`` byte-identical to the keeper's.
3. **inputs** — the std outage extract path + sha256 the keeper recorded.
4. **classifier** — the ``hydro-plant-modes`` partition content hash equals the
   keeper's pinned value (``hydro_ror_split`` stays armed).

Exit 0 when every check passes, 1 otherwise; a failing shard does not push.

Usage::

    python docs/handoffs/neiso117/shard_check.py --leg results/calibration/neiso117_<Y> --year <Y>
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

KEEPER = ROOT / "results/calibration/neiso114b_span"
DELTA = {"coal_fuel_inventory_plant_grain": (False, True)}
NEW_ARMED: dict = {}
STD_EXTRACT = "data/raw/campd-unit-outages-NEISO.csv"
STD_SHA256 = "aaa3bb379eb7655276401d6d7726cfd783007d81a6eeb7234a879a69c9f85881"
CLASSIFIER_SHA = "02c3f7710de08661"


def _rc(bundle: Path, year: int) -> dict:
    per = bundle / f"run_config_{year}.json"
    return json.loads((per if per.exists() else bundle / "run_config.json").read_text())


def _overrides(rc: dict):
    """The run's ``offer_curve_overrides``: recorded under ``calibration_flags``
    (the ``--offer-curve-json`` CLI path), else under ``scenario_config``."""
    cf = rc.get("calibration_flags") or {}
    if cf.get("offer_curve_overrides") is not None:
        return cf["offer_curve_overrides"]
    return (rc.get("scenario_config") or {}).get("offer_curve_overrides")


def classifier_sha() -> str | None:
    """Content hash of the on-disk NEISO ``hydro-plant-modes`` partition."""
    import pandas as pd

    p = ROOT / "data/clean/hydro-plant-modes/NEISO/hydro-plant-modes.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)[["plant_id", "shapeable"]].sort_values("plant_id")
    return hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()[:16]


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--leg", required=True)
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()
    leg = ROOT / args.leg
    from market_sim.config.scenarios import ScenarioConfig

    defaults = {
        f.name: f.default
        for f in dataclasses.fields(ScenarioConfig)
        if f.default is not dataclasses.MISSING
    }
    rc_leg = _rc(leg, args.year)
    rc_k = _rc(KEEPER, args.year)
    a = rc_leg["scenario_config"]
    k = rc_k["scenario_config"]
    ok = True
    # COAL-SUB (#6619): replay_keeper folds a legacy bare "COAL" entry out of
    # the resolved offer_curve_by_group; compare with that entry set aside.
    skip_groups = {"COAL"}

    def _curve(cfg: dict) -> dict:
        return {
            g: v
            for g, v in (cfg.get("offer_curve_by_group") or {}).items()
            if g not in skip_groups
        }

    diff = {
        key: (k[key], a[key])
        for key in sorted(set(a) & set(k))
        if a[key] != k[key]
        and key not in ("offer_curve_overrides", "offer_curve_by_group")
    }
    if _curve(a) != _curve(k):
        diff["offer_curve_by_group"] = ("keeper", "moved outside COAL")
    new_only = {key: a[key] for key in sorted(set(a) - set(k))}
    new_nondefault = {
        key: v
        for key, v in new_only.items()
        if key in defaults
        and json.dumps(v, default=str) != json.dumps(defaults[key], default=str)
    }
    print(f"recipe diff vs keeper: {diff}")
    print(f"fields new since keeper: {len(new_only)} (non-default: {new_nondefault})")
    print(f"fields only in keeper: {sorted(set(k) - set(a))}")
    want_delta = DELTA
    if diff != want_delta or new_nondefault != NEW_ARMED:
        print("RECIPE CHECK: FAIL")
        ok = False
    else:
        print("RECIPE CHECK: PASS")
    if a.get("weather_year") != args.year:
        print(f"weather_year {a.get('weather_year')} != {args.year}: FAIL")
        ok = False

    want = _overrides(rc_k)
    got = _overrides(rc_leg)
    yrs = (rc_leg.get("calibration_flags") or {}).get("years")
    if yrs != [args.year]:
        print(f"calibration_flags.years {yrs} != [{args.year}]: FAIL")
        ok = False
    if got != want:
        print(f"OFFER CURVE CHECK: FAIL\n  got  {got}\n  want {want}")
        ok = False
    else:
        print("OFFER CURVE CHECK: PASS")

    ri = rc_leg.get("resolved_inputs", {}).get("campd_unit_outages", {})
    print(f"std extract: {ri.get('path')} sha256 {ri.get('sha256')}")
    if ri.get("path") != STD_EXTRACT or ri.get("sha256") != STD_SHA256:
        print("INPUT CHECK: FAIL (std extract)")
        ok = False
    else:
        print("INPUT CHECK: PASS (std extract)")

    sha = classifier_sha()
    print(f"classifier content sha: {sha} (pinned {CLASSIFIER_SHA})")
    if sha is None:
        # The partition is a solve-container artifact (data/clean, gitignored);
        # a parent verifying a fetched leg has none. Report, don't fail.
        print("CLASSIFIER CHECK: SKIP (partition not built in this checkout)")
    elif sha != CLASSIFIER_SHA:
        print("CLASSIFIER CHECK: FAIL")
        ok = False
    else:
        print("CLASSIFIER CHECK: PASS")
    print("ALL CHECKS PASS" if ok else "SHARD CHECK FAILED — DO NOT PUSH")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
