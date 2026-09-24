"""SPP-75 shard self-check: control == keeper recipe, arm == control + chp_steam_floor_p25.

Run by each SPP-75 shard AFTER both solves and BEFORE it pushes (rule 32(c)(4) hard stops).
Zero LP. Pre-registered in ``docs/handoffs/PRECOMMIT-spp-75-gas-low-side-2026-09-23.md`` §5.

1. **recipe** — the control's ``scenario_config`` equals the keeper bundle's for the year
   (fields added since the keeper allowed only at their dataclass default); the arm's differs
   from the control's by EXACTLY ``chp_steam_floor_p25: False -> True``.
2. **readout** — per-class P1 TWh (keeper / control / arm), CHP MW in measured RT<=0 hours,
   demand-weighted mean price, and the arm-minus-control deltas the PRECOMMIT predicts.

Exit 0 only when (1) passes; a failing shard does not push.

Usage::

    python scripts/probes/_spp75_shard_check.py --year 2020 \\
        --keeper results/calibration/hydro5_spp_floor_rung \\
        --control results/calibration/spp75_ctl_2020 --arm results/calibration/spp75_chp_2020
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

FLAG = "chp_steam_floor_p25"
CHP = ("CC_CHP", "CT_CHP", "ST_CHP")


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


def readout(bundle: Path, year: int, neg: np.ndarray) -> dict:
    """Class TWh, CHP MW in RT<=0 hours, mean price for one bundle-year (P1)."""
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
    chp = pv[[k for k in CHP if k in pv]].sum(axis=1).to_numpy()
    gas = pv[[k for k in pv.columns if k.startswith(("CC_", "CT_", "ST_"))]].sum(axis=1)
    return {
        "twh": {k: round(float(pv[k].sum()) / 1e6, 4) for k in pv.columns},
        "chp_twh": round(float(chp.sum()) / 1e6, 4),
        "gas_twh": round(float(gas.sum()) / 1e6, 4),
        "chp_mw_neg": round(float(chp[neg].mean()), 1),
        "gas_mw_neg": round(float(gas.to_numpy()[neg].mean()), 1),
        "wind_mw_neg": round(float(pv["wind"].to_numpy()[neg].mean()), 1),
        "price_neg": round(float(price[neg].mean()), 3),
        "price_mean_dw": round(
            float((price * d.sum(axis=1).to_numpy()).sum() / d.sum(axis=1).sum()), 3
        ),
        "hours_price_le0": int((price <= 0).sum()),
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
    if d_ac != {FLAG: (False, True)} or new_ac:
        print(
            "ARM RECIPE CHECK: FAIL — the arm is not the control plus exactly one flag"
        )
        ok = False
    else:
        print("ARM RECIPE CHECK: PASS")

    lmp = pd.read_parquet(
        ROOT / "data/raw/_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    rt = lmp[lmp["year"] == a.year].sort_values("hour")["rt"].to_numpy(float)
    neg = np.isfinite(rt) & (rt <= 0)
    out = {"year": a.year, "n_rt_le0": int(neg.sum())}
    for name, b in (("keeper", kp), ("control", ct), ("arm", ar)):
        try:
            out[name] = readout(b, a.year, neg)
        except FileNotFoundError as e:
            out[name] = f"missing: {e}"
    if isinstance(out["arm"], dict) and isinstance(out["control"], dict):
        A, C = out["arm"], out["control"]
        out["arm_minus_control"] = {
            k: round(A[k] - C[k], 4)
            for k in (
                "chp_twh",
                "gas_twh",
                "chp_mw_neg",
                "gas_mw_neg",
                "wind_mw_neg",
                "price_neg",
                "price_mean_dw",
                "hours_price_le0",
            )
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
    (ar / f"spp75_readout_{a.year}.json").write_text(json.dumps(out, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
