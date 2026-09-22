"""hydro-5 shard self-check: is this arm the keeper plus exactly one hydro flag?

Run by each hydro-5 shard AFTER its solve and BEFORE it pushes (rule 32(c)(4):
self-checkable hard stops). Zero LP. Three checks, then the arm's hydro
statistics against the committed keeper for the same year:

1. **recipe** — the arm's ``run_config_<year>.json`` ``scenario_config``
   differs from the keeper's by EXACTLY the one arm flag (``False -> True``).
   A field present only in the arm (added to ``ScenarioConfig`` after the
   keeper solved) is allowed only at its dataclass default. A field present
   only in the keeper is reported (a deleted field, rule 26).
2. **classifier** — for a ``hydro_ror_split`` arm, the ``hydro-plant-modes``
   partition the solve read has the content hash the PRECOMMIT pinned
   (sha256 over the sorted ``plant_id,shapeable`` CSV, first 16 hex).
3. **liveness** — the arm's P1 hourly hydro class never sits below 1 MW
   where the mechanism predicts it cannot.

Exit status 0 when 1 and 2 pass, 1 otherwise; a failing shard does not push.

Usage::

    python scripts/probes/_hydro5_shard_check.py \\
        --arm results/calibration/hydro5_spp_ror_2023 \\
        --keeper results/calibration/spp67_yearown_span \\
        --year 2023 --flag hydro_ror_split
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

from _hydro5_phase0 import class_mw, load_mw, stats  # noqa: E402

# Content hashes of the reviewed classifier partitions (PRECOMMIT §2).
CLASSIFIER_SHA: dict[str, str] = {
    "SPP": "f7fc0b2a2beb0411",
    "NEISO": "02c3f7710de08661",
    "MISO": "dc2a9d4be30a0727",
}


def _scenario(bundle: Path, year: int) -> dict:
    """Return a bundle's recorded ScenarioConfig for one year."""
    per_year = bundle / f"run_config_{year}.json"
    rc = per_year if per_year.exists() else bundle / "run_config.json"
    return json.loads(rc.read_text())["scenario_config"]


def classifier_sha(iso: str) -> str | None:
    """Content hash of the on-disk ``hydro-plant-modes`` partition for ``iso``."""
    import pandas as pd

    p = ROOT / "data/clean/hydro-plant-modes" / iso / "hydro-plant-modes.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)[["plant_id", "shapeable"]].sort_values("plant_id")
    return hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()[:16]


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--arm", required=True)
    ap.add_argument("--keeper", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument(
        "--flag", required=True, choices=["hydro_ror_split", "hydro_min_flow_floor"]
    )
    args = ap.parse_args()
    arm, keeper = ROOT / args.arm, ROOT / args.keeper
    from market_sim.config.scenarios import ScenarioConfig

    defaults = {
        f.name: f.default
        for f in dataclasses.fields(ScenarioConfig)
        if f.default is not dataclasses.MISSING
    }
    a, k = _scenario(arm, args.year), _scenario(keeper, args.year)
    ok = True
    diff = {
        key: (k[key], a[key]) for key in sorted(set(a) & set(k)) if a[key] != k[key]
    }
    new_only = {key: a[key] for key in sorted(set(a) - set(k))}
    gone = sorted(set(k) - set(a))
    bad_new = {
        key: v
        for key, v in new_only.items()
        if key in defaults and json.dumps(v) != json.dumps(defaults[key], default=str)
    }
    print(f"recipe diff vs keeper: {diff}")
    print(f"fields new since keeper: {len(new_only)} (non-default: {bad_new})")
    print(f"fields only in keeper: {gone}")
    if diff != {args.flag: (False, True)} or bad_new:
        print("RECIPE CHECK: FAIL — the arm is not the keeper plus exactly one flag")
        ok = False
    else:
        print("RECIPE CHECK: PASS")

    iso = json.loads((arm / "meta.json").read_text())["iso"]
    if args.flag == "hydro_ror_split":
        sha = classifier_sha(iso)
        print(f"classifier content sha: {sha} (pinned {CLASSIFIER_SHA.get(iso)})")
        if sha != CLASSIFIER_SHA.get(iso):
            print("CLASSIFIER CHECK: FAIL")
            ok = False
        else:
            print("CLASSIFIER CHECK: PASS")

    h_arm, h_k = class_mw(arm.name, args.year), class_mw(keeper.name, args.year)
    load = load_mw(arm.name, args.year)
    if load is None:
        load = load_mw(keeper.name, args.year)
    if h_arm is None or h_k is None or load is None:
        print("hydro stats: sidecar missing")
        return 0 if ok else 1
    sa, sk = stats(h_arm, load), stats(h_k, load)
    print(json.dumps({"arm": sa, "keeper": sk}, indent=1))
    d = sa["twh"] - sk["twh"]
    print(f"G2 annual: {d:+.5f} TWh = {100 * d / sk['twh']:+.4f} %")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
