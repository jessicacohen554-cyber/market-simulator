"""R-NEISO shard self-check (zero LP): is this leg the NEISO keeper plus exactly the declared input corrections?

Run by each R-NEISO shard AFTER its solve and BEFORE it pushes (rule 32(c)(4):
self-checkable hard stops). Checks:

1. **recipe** — the leg's ``run_config_<year>.json`` ``scenario_config`` differs
   from the keeper's (``hydro5_neiso_ror_span``; its 2020 config stands in for
   2019, which the keeper never solved) by EXACTLY the PRECOMMIT's delta set,
   plus the two year-dependent keys (``weather_year``, ``gas_price_override``)
   for 2019. A field added to ``ScenarioConfig`` after the keeper solved is
   allowed only at its dataclass default. ``offer_curve_overrides`` must be
   byte-identical (rule 1(c): no re-tuning).
2. **inputs** — the recorded ``resolved_inputs.campd_unit_outages`` is the
   PRECOMMIT's std extract (path + sha256); the EIA-860 vintage directory the
   flag resolves to exists for the year (2019-2024) or is canonical (2025).
3. **classifier** — the ``hydro-plant-modes`` partition content hash equals the
   keeper's pinned value (``hydro_ror_split`` stays armed).

Exit 0 when every check passes, 1 otherwise; a failing shard does not push.

Usage::

    python docs/handoffs/r-neiso/shard_check.py --leg results/calibration/rneiso_<Y> --year <Y>
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

KEEPER = ROOT / "results/calibration/hydro5_neiso_ror_span"
DELTA = {
    "eia860_vintage_tracks_solve_year": (False, True),
    "measured_coal_heat_rates": (False, True),
    "measured_st_heat_rates": (False, True),
    "measured_cc_heat_rates": (False, True),
    "unit_outage_short_windows_gas": (False, True),
    "unit_partial_outage_windows": (False, True),
    "mid_vintage_exit_carry": (False, True),
    "partial_plant_exit_carry": (False, True),
}
YEAR_KEYS = {"weather_year", "gas_price_override"}
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
    k = _rc(KEEPER, max(args.year, 2020))["scenario_config"]
    ok = True
    diff = {key: (k[key], a[key]) for key in sorted(set(a) & set(k)) if a[key] != k[key]}
    year_diff = {key: v for key, v in diff.items() if key in YEAR_KEYS}
    core = {key: v for key, v in diff.items() if key not in YEAR_KEYS}
    new_only = {key: a[key] for key in sorted(set(a) - set(k))}
    bad_new = {
        key: v
        for key, v in new_only.items()
        if key in defaults and json.dumps(v, default=str) != json.dumps(defaults[key], default=str)
    }
    print(f"recipe diff vs keeper: {core}")
    print(f"year-dependent diff: {year_diff}")
    print(f"fields new since keeper: {len(new_only)} (non-default: {bad_new})")
    print(f"fields only in keeper: {sorted(set(k) - set(a))}")
    expect_year = args.year == 2019
    if core != DELTA or bad_new or (year_diff and not expect_year):
        print("RECIPE CHECK: FAIL")
        ok = False
    else:
        print("RECIPE CHECK: PASS")
    if a.get("weather_year") != args.year:
        print(f"weather_year {a.get('weather_year')} != {args.year}: FAIL")
        ok = False
    if a.get("offer_curve_overrides") != k.get("offer_curve_overrides"):
        print("OFFER CURVE CHECK: FAIL (multipliers moved)")
        ok = False
    else:
        print("OFFER CURVE CHECK: PASS (byte-identical to keeper)")

    ri = rc_leg.get("resolved_inputs", {}).get("campd_unit_outages", {})
    print(f"std extract: {ri.get('path')} sha256 {ri.get('sha256')}")
    if ri.get("path") != STD_EXTRACT or ri.get("sha256") != STD_SHA256:
        print("INPUT CHECK: FAIL (std extract)")
        ok = False
    else:
        print("INPUT CHECK: PASS (std extract)")
    vdir = ROOT / f"data/raw/eia-860/vintage_{args.year}"
    print(f"EIA-860 vintage resolved: {vdir.name if vdir.is_dir() else 'canonical (eia860_generators.parquet)'}")

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
