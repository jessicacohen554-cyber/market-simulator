#!/usr/bin/env python3
"""miso-268 shard self-check: is this leg the MISO keeper plus EXACTLY one flag?

Copied from ``_miso267_shard_check.py`` and repointed: KEEPER is the miso-267
keeper, FLAG is ``coal_fuel_inventory_plant_grain``, and check 4 requires the
solve log to show the per-yard rows were actually built (``--log``).

Run by each miso-268 shard AFTER its single-year solve and BEFORE it pushes
(rule 32 ``[R-SHARD]`` (c)(4): self-checkable hard stops). Zero LP.

1. **recipe** — the leg's recorded ``scenario_config`` for ``--year`` differs from
   the keeper's per-year recipe by EXACTLY
   ``coal_fuel_inventory_plant_grain: False -> True``. A field present
   only in the leg (added to ``ScenarioConfig`` after the keeper solved) is
   allowed only at its dataclass default.
2. **classifier** — the keeper arms ``hydro_ror_split``, so the leg must have
   read the SAME ``hydro-plant-modes`` partition the keeper did: its content
   hash must equal the MISO value ``scripts/probes/_hydro5_shard_check.py``
   pinned (``CLASSIFIER_SHA["MISO"]``).
3. **readout** (reported, never a stop) — per-class TWh and the load-weighted
   internal price, leg minus the committed keeper, from both bundles' own
   ``hourly/`` sidecars. The keeper's committed bundle is the control (rule 29
   ``[R-SCREEN]`` (b), form 4; the PRECOMMIT's G-DRIFT audit is what licenses it).

Exit 0 only when 1 and 2 pass; a failing shard does not push.

Usage::

    python scripts/probes/_miso267_shard_check.py \\
        --leg results/calibration/miso268_yard_2020 --year 2020 --log solve_2020.log
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

from _hydro5_shard_check import CLASSIFIER_SHA, classifier_sha  # noqa: E402

KEEPER = ROOT / "results/calibration/miso267_dbd_span"
FLAG = "coal_fuel_inventory_plant_grain"
INTERNAL = (
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
)


def _scenario(bundle: Path, year: int) -> dict:
    per_year = bundle / f"run_config_{year}.json"
    rc = per_year if per_year.exists() else bundle / "run_config.json"
    return json.loads(rc.read_text())["scenario_config"]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    ch = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    return (ch.groupby("klass", observed=True)["mw"].sum() / 1e6).round(4).to_dict()


def _lw_price(bundle: Path, year: int) -> float:
    s = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    s = s[(s["pass"] == "P1") & (s["zone"].isin(INTERNAL))]
    return float((s["price"] * s["demand"]).sum() / s["demand"].sum())


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--leg", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--log", required=True, help="the leg's solve log")
    args = ap.parse_args()
    leg = ROOT / args.leg
    from market_sim.config.scenarios import ScenarioConfig

    defaults = {
        f.name: f.default
        for f in dataclasses.fields(ScenarioConfig)
        if f.default is not dataclasses.MISSING
    }
    a, k = _scenario(leg, args.year), _scenario(KEEPER, args.year)
    diff = {
        key: (k[key], a[key]) for key in sorted(set(a) & set(k)) if a[key] != k[key]
    }
    new_only = {key: a[key] for key in sorted(set(a) - set(k))}
    bad_new = {
        key: v
        for key, v in new_only.items()
        if key in defaults and json.dumps(v) != json.dumps(defaults[key], default=str)
    }
    ok = True
    print(f"recipe diff vs keeper: {diff}")
    print(f"fields new since keeper: {len(new_only)} (non-default: {bad_new})")
    if diff != {FLAG: (False, True)} or bad_new:
        print("RECIPE CHECK: FAIL — the leg is not the keeper plus exactly one flag")
        ok = False
    else:
        print("RECIPE CHECK: PASS")

    sha = classifier_sha("MISO")
    print(f"hydro classifier sha: {sha} (keeper pinned {CLASSIFIER_SHA['MISO']})")
    if sha != CLASSIFIER_SHA["MISO"]:
        print("CLASSIFIER CHECK: FAIL")
        ok = False
    else:
        print("CLASSIFIER CHECK: PASS")

    rows = [ln for ln in Path(args.log).read_text(errors="replace").splitlines()
            if "coal per-yard budget" in ln]
    print(f"per-yard budget log lines: {rows[-1:] if rows else rows}")
    if not rows or any("NOT APPLIED" in ln for ln in rows):
        print("ROWS CHECK: FAIL — the per-yard rows were not built")
        ok = False
    else:
        print("ROWS CHECK: PASS")

    try:
        ca, ck = _class_twh(leg, args.year), _class_twh(KEEPER, args.year)
        delta = {
            c: round(ca.get(c, 0.0) - ck.get(c, 0.0), 3)
            for c in sorted(set(ca) | set(ck))
            if abs(ca.get(c, 0.0) - ck.get(c, 0.0)) >= 0.001
        }
        pa, pk = _lw_price(leg, args.year), _lw_price(KEEPER, args.year)
        print(json.dumps({"class_twh_leg_minus_keeper": delta}, indent=1))
        print(
            f"load-weighted internal price: keeper {pk:.3f} -> leg {pa:.3f} ({pa - pk:+.3f} $/MWh)"
        )
        print(f"total generation delta: {sum(delta.values()):+.4f} TWh")
    except FileNotFoundError as exc:
        print(f"readout: sidecar missing ({exc})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
