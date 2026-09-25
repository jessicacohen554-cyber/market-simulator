"""neiso-114 shard self-check (zero LP): is this leg the NEISO keeper plus exactly the declared arm?

Run by each neiso-114 shard AFTER its solve and BEFORE it pushes (rule 32(c)(4):
self-checkable hard stops). The keeper is ``results/calibration/rneiso_span``
(``2026-09-24-r-neiso-inputs-2019``), which carries a ``run_config_<Y>.json`` for
every year 2019-2025. Checks:

1. **recipe** — the leg's ``scenario_config`` differs from the keeper's same-year
   config by EXACTLY the arm's delta: ``coal_mustrun_requires_measured_row``
   False -> True (arms A and B); NO delta for the control arm C (the keeper
   recipe at HEAD, 2019/2020 only — the G-DRIFT LIVE years). Any field added to
   ``ScenarioConfig`` after the keeper solved must sit at its dataclass default.
2. **offer curve** — arms A and C: ``offer_curve_overrides`` byte-identical to the
   keeper's. Arm B: equal to ``docs/handoffs/neiso114/arm_b_offer_curve.json``
   (the ST_GAS re-derivation, PRECOMMIT §3), every other class byte-identical.
3. **inputs** — the std outage extract path + sha256 the keeper recorded.
4. **classifier** — the ``hydro-plant-modes`` partition content hash equals the
   keeper's pinned value (``hydro_ror_split`` stays armed).

Exit 0 when every check passes, 1 otherwise; a failing shard does not push.

Usage::

    python docs/handoffs/neiso114/shard_check.py --arm A --leg results/calibration/neiso114a_<Y> --year <Y>
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

KEEPER = ROOT / "results/calibration/rneiso_span"
DELTA = {"coal_mustrun_requires_measured_row": (False, True)}
NEW_ARMED: dict = {}
ARM_B_CURVE = ROOT / "docs/handoffs/neiso114/arm_b_offer_curve.json"
STD_EXTRACT = "data/raw/campd-unit-outages-NEISO.csv"
STD_SHA256 = "aaa3bb379eb7655276401d6d7726cfd783007d81a6eeb7234a879a69c9f85881"
CLASSIFIER_SHA = "02c3f7710de08661"


def _rc(bundle: Path, year: int) -> dict:
    per = bundle / f"run_config_{year}.json"
    return json.loads((per if per.exists() else bundle / "run_config.json").read_text())


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
    ap.add_argument("--arm", choices=("A", "B", "C"), required=True)
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
    a = rc_leg["scenario_config"]
    k = _rc(KEEPER, args.year)["scenario_config"]
    ok = True
    # COAL-SUB (#6619): replay_keeper folds the keeper's legacy bare "COAL"
    # entry out of the resolved offer_curve_by_group (G-DRIFT, PRECOMMIT §2),
    # and arm B's ST_GAS entry differs by design (checked via the overrides
    # below). Compare the resolved curve with those two entries set aside.
    skip_groups = {"COAL"} | ({"ST_GAS"} if args.arm == "B" else set())

    def _curve(cfg: dict) -> dict:
        return {g: v for g, v in (cfg.get("offer_curve_by_group") or {}).items() if g not in skip_groups}

    diff = {
        key: (k[key], a[key])
        for key in sorted(set(a) & set(k))
        if a[key] != k[key] and key not in ("offer_curve_overrides", "offer_curve_by_group")
    }
    if _curve(a) != _curve(k):
        diff["offer_curve_by_group"] = ("keeper", "moved outside COAL/ST_GAS")
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
    want_delta = {} if args.arm == "C" else DELTA
    if diff != want_delta or new_nondefault != NEW_ARMED:
        print("RECIPE CHECK: FAIL")
        ok = False
    else:
        print("RECIPE CHECK: PASS")
    if a.get("weather_year") != args.year:
        print(f"weather_year {a.get('weather_year')} != {args.year}: FAIL")
        ok = False

    want = k.get("offer_curve_overrides")
    if args.arm == "B":
        want = json.loads(ARM_B_CURVE.read_text())
    got = a.get("offer_curve_overrides")
    if got != want:
        print(f"OFFER CURVE CHECK: FAIL\n  got  {got}\n  want {want}")
        ok = False
    else:
        print(f"OFFER CURVE CHECK: PASS (arm {args.arm})")

    ri = rc_leg.get("resolved_inputs", {}).get("campd_unit_outages", {})
    print(f"std extract: {ri.get('path')} sha256 {ri.get('sha256')}")
    if ri.get("path") != STD_EXTRACT or ri.get("sha256") != STD_SHA256:
        print("INPUT CHECK: FAIL (std extract)")
        ok = False
    else:
        print("INPUT CHECK: PASS (std extract)")

    sha = classifier_sha()
    print(f"classifier content sha: {sha} (pinned {CLASSIFIER_SHA})")
    if sha != CLASSIFIER_SHA:
        print("CLASSIFIER CHECK: FAIL")
        ok = False
    else:
        print("CLASSIFIER CHECK: PASS")
    print("ALL CHECKS PASS" if ok else "SHARD CHECK FAILED — DO NOT PUSH")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
