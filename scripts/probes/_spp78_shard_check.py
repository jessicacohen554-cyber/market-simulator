"""SPP-78 shard self-check: control == bundle recipe, arm == control + the three measured-HR fields.

Run by each SPP-78 shard AFTER both solves and BEFORE it pushes (rule 32(c)(4) hard stops).
Zero LP. Pre-registered in ``docs/handoffs/PRECOMMIT-spp-78-measured-heat-rates-2026-09-24.md`` §4
and its ADDENDUM. Adapted from ``_spp75_shard_check.py`` (same recipe diff, same readout frame).

1. **recipe** — the control's ``scenario_config`` equals the keeper/rung bundle's for the year
   (fields added since allowed only at their dataclass default); the arm's differs from the
   control's by EXACTLY ``measured_{cc,st,coal}_heat_rates: False -> True``.
2. **gas price** — the recorded ``gas_price_override`` equals the lane's hard-stop value.
3. **artifacts** — the three SPP heat-rate artifacts' sha256 equal the pinned values.
4. **readout** — per-class P1 TWh (bundle / control / arm), demand-weighted mean price, and the
   arm-minus-control deltas the PRECOMMIT predicts.

Exit 0 only when (1)-(3) pass; a failing shard does not push.

Usage::

    python scripts/probes/_spp78_shard_check.py --year 2020 \\
        --keeper results/calibration/hydro5_spp_floor_rung \\
        --control results/calibration/spp78_ctl_2020 --arm results/calibration/spp78_hr_2020
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import hashlib

FLAGS = ("measured_cc_heat_rates", "measured_st_heat_rates", "measured_coal_heat_rates")
GAS = {2019: 2.57, 2020: 2.03, 2021: 3.72, 2022: 6.45, 2023: 2.54, 2024: 2.19, 2025: 3.52}
ARTIFACT_SHA256 = {
    "campd_cc_heat_rates_SPP.csv": "59dd580d25b9dfbe72b814a8083b0864c2b60eba92d25fdb4b8f55071607f461",
    "campd_st_heat_rates_SPP.csv": "ef71c147ff858dbdb1e9c377a4a702b997527c4011277c3a62eda08e7fa6d40e",
    "campd_coal_heat_rates_SPP.csv": "8f501813e178d62adcfb02be0c0007dac8b6eb760a1857dd33092da48143ef03",
}


def _scenario(bundle: Path, year: int) -> dict:
    """A bundle's recorded ScenarioConfig for one year."""
    per_year = bundle / f"run_config_{year}.json"
    rc = per_year if per_year.exists() else bundle / "run_config.json"
    return json.loads(rc.read_text())["scenario_config"]


def _diff(base: dict, other: dict, defaults: dict) -> tuple[dict, dict]:
    """(changed keys, non-default keys present only in ``other``)."""
    changed = {
        k: (base[k], other[k])
        for k in sorted(set(base) & set(other))
        if base[k] != other[k]
    }
    bad_new = {
        k: other[k]
        for k in sorted(set(other) - set(base))
        if k in defaults
        and json.dumps(other[k]) != json.dumps(defaults[k], default=str)
    }
    return changed, bad_new


def readout(bundle: Path, year: int) -> dict:
    """Class TWh and demand-weighted mean price for one bundle-year (P1)."""
    c = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    c["klass"] = c["klass"].astype(str)
    pv = c.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
    pv = pv.reindex(range(8760), fill_value=0.0).fillna(0.0)
    s = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    d = s.pivot(index="hour", columns="zone", values="demand").sort_index()
    p = s.pivot(index="hour", columns="zone", values="price").sort_index()
    price = ((p * d).sum(axis=1) / d.sum(axis=1)).to_numpy()
    return {
        "twh": {k: round(float(pv[k].sum()) / 1e6, 4) for k in pv.columns},
        "price_mean_dw": round(
            float((price * d.sum(axis=1).to_numpy()).sum() / d.sum(axis=1).sum()), 3
        ),
        "price_mean": round(float(price.mean()), 3),
    }


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--keeper", required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--arm", required=True)
    a = ap.parse_args()
    from market_sim.config.scenarios import ScenarioConfig

    defaults = {
        f.name: f.default
        for f in dataclasses.fields(ScenarioConfig)
        if f.default is not dataclasses.MISSING
    }
    kp, ct, ar = ROOT / a.keeper, ROOT / a.control, ROOT / a.arm
    sk, sc, sa = _scenario(kp, a.year), _scenario(ct, a.year), _scenario(ar, a.year)
    ok = True
    d_ck, new_ck = _diff(sk, sc, defaults)
    print(f"control vs keeper: changed {d_ck}  non-default new {new_ck}")
    if d_ck or new_ck:
        print("CONTROL RECIPE CHECK: FAIL — the control is not the keeper recipe")
        ok = False
    else:
        print("CONTROL RECIPE CHECK: PASS")
    d_ac, new_ac = _diff(sc, sa, defaults)
    print(f"arm vs control: changed {d_ac}  non-default new {new_ac}")
    if d_ac != {f: (False, True) for f in FLAGS} or new_ac:
        print("ARM RECIPE CHECK: FAIL — the arm is not the control plus exactly the three fields")
        ok = False
    else:
        print("ARM RECIPE CHECK: PASS")
    for name, s in (("control", sc), ("arm", sa)):
        g = s.get("gas_price_override")
        if g is None or abs(float(g) - GAS[a.year]) > 0.005:
            print(f"GAS PRICE CHECK ({name}): FAIL — {g} != {GAS[a.year]}")
            ok = False
    proc = ROOT / "data/raw/_processed-legacy"
    for fn, want in ARTIFACT_SHA256.items():
        got = hashlib.sha256((proc / fn).read_bytes()).hexdigest()
        if got != want:
            print(f"ARTIFACT CHECK: FAIL — {fn} sha256 {got}")
            ok = False
    print("GAS/ARTIFACT CHECKS:", "PASS" if ok else "FAIL")

    out = {"year": a.year}
    for name, b in (("keeper", kp), ("control", ct), ("arm", ar)):
        try:
            out[name] = readout(b, a.year)
        except FileNotFoundError as e:
            out[name] = f"missing: {e}"
    if isinstance(out["arm"], dict) and isinstance(out["control"], dict):
        A, C = out["arm"], out["control"]
        out["arm_minus_control"] = {
            k: round(A[k] - C[k], 4) for k in ("price_mean_dw", "price_mean")
        }
        out["arm_minus_control"]["class_twh"] = {
            k: round(A["twh"].get(k, 0) - C["twh"].get(k, 0), 4)
            for k in sorted(set(A["twh"]) | set(C["twh"]))
            if abs(A["twh"].get(k, 0) - C["twh"].get(k, 0)) >= 0.001
        }
    if isinstance(out["keeper"], dict) and isinstance(out["control"], dict):
        out["control_minus_keeper_max_abs_class_twh"] = max(
            abs(out["control"]["twh"].get(k, 0) - out["keeper"]["twh"].get(k, 0))
            for k in set(out["control"]["twh"]) | set(out["keeper"]["twh"])
        )
    print(json.dumps(out, indent=1))
    (ar / f"spp78_readout_{a.year}.json").write_text(json.dumps(out, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
