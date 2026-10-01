"""SPP-94 shard self-check: the leg == the committed keeper's recipe, solved on the 2020/2021 curtailment rows.

Run by each SPP-94 shard AFTER its solve and BEFORE it pushes (rule 32(c)(4) hard stops). Zero LP.
Pre-registered in ``docs/records/spp/PRECOMMIT-spp-94-curtail-rows-2026-09-27.md``. Adapted from
``_spp93_shard_check.py``; the control is the committed keeper ``spp86_arm_span`` (rule 29(b) form 4).

The arm is a DATA change (two published rows in ``spp_wind_curtailment_annual.csv``), not a config
field, so the recipe must be IDENTICAL to the keeper's.

Hard checks (exit 1 on any failure; a failing shard does not push):

1. **recipe** -- the leg's ``scenario_config`` differs from the keeper's ``run_config_<Y>.json`` by
   NOTHING (every field added since the keeper was solved sits at its default).
2. **gas price** -- ``gas_price_override`` equals the keeper's own value for the year.
3. **inputs** -- the six SPP CAMPD outage extracts and the curtailment table carry their pinned sha256.
4. **resolved** -- the leg's ``run_config.json`` records the ``-netloadmask-`` standard extract.
5. **topology** -- ``system_<Y>.parquet`` carries exactly SPP-North / SPP-South.
6. **artifact** -- ``dispatch/<Y>_P1.parquet`` exists (rule 34(a)).

Reported (never a push blocker -- the parent adjudicates):

7. **identity** (2019, 2022-2025) -- per-class P1 TWh and every zonal hourly price equal the keeper's.
8. **arming** (2020, 2021) -- P1 wind TWh below the keeper's.
9. **readout** -- per-class TWh, demand-weighted price, slack MWh, arm vs keeper.

Usage::

    python scripts/probes/_spp94_shard_check.py --year 2021 --leg results/calibration/spp94_arm_2021
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.probes._spp78_shard_check import _diff, _scenario, readout  # noqa: E402

KEEPER = "results/calibration/spp86_arm_span"
ARM_YEARS = (2020, 2021)
SHA = {
    "data/raw/campd-unit-outages-netloadmask-SPP.csv": "431613655433695e331c5d9986237127db4efc3455dbd7200fdafb00d1963012",
    "data/raw/campd-unit-outages-short-netloadmask-SPP.csv": "5c016785a746a9c9f7d6dcce060ba9fb81221d95526d02aaaa51fec8139535e7",
    "data/raw/campd-partial-outages-netloadmask-SPP.csv": "3792217d858dcb2c93711b6a8bbdb326cb801609e40721db30ba2831bb3d337e",
    "data/raw/campd-unit-outages-SPP.csv": "05aced4ff69fe85d0ed8e4683520644a3b1717689a0be486216391f9383361ad",
    "data/raw/campd-unit-outages-short-SPP.csv": "82fca832aeeca6f14c0ee31542f0caf74efdf3856e8f4f5c65086ab2b8449f8f",
    "data/raw/campd-partial-outages-SPP.csv": "7acc39f6e21d7d5e9b37a03d3701a1ee65da7bc2b028afb5b15c2309ca8944b4",
    "data/raw/spp-hsl/spp_wind_curtailment_annual.csv": "dd6c289839987d01689ffc4c2f1351d7a260e13fad096c770f191787336116fe",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prices(bundle: Path, year: int):
    import pandas as pd

    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return (
        s.pivot(index="hour", columns="zone", values="price").sort_index(),
        float(s["slack"].sum()),
    )


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--leg", required=True)
    ap.add_argument("--keeper", default=KEEPER)
    a = ap.parse_args()
    from market_sim.config.scenarios import ScenarioConfig

    defaults = {
        f.name: f.default
        for f in dataclasses.fields(ScenarioConfig)
        if f.default is not dataclasses.MISSING
    }
    kp, lg = ROOT / a.keeper, ROOT / a.leg
    sk, sl = _scenario(kp, a.year), _scenario(lg, a.year)
    ok = True
    changed, new = _diff(sk, sl, defaults)
    print(f"leg vs committed keeper: changed {changed}  non-default new {new}")
    if changed or new:
        print("RECIPE CHECK: FAIL -- the recipe must be the keeper's, unchanged")
        ok = False
    else:
        print("RECIPE CHECK: PASS -- identical to the keeper")
    gk, gl = sk.get("gas_price_override"), sl.get("gas_price_override")
    if gk is None or gl is None or abs(float(gl) - float(gk)) > 1e-9:
        print(f"GAS CHECK: FAIL -- leg {gl} vs keeper {gk}")
        ok = False
    else:
        print(f"GAS CHECK: PASS -- {gl}")
    for rel, h in SHA.items():
        got = _sha(ROOT / rel)
        ok &= got == h
        print(f"SHA {'PASS' if got == h else 'FAIL'} {rel} {got[:16]}")
    rc = json.loads((lg / "run_config.json").read_text())
    ri = (rc.get("resolved_inputs") or {}).get("campd_unit_outages") or {}
    if ri.get("sha256") != SHA["data/raw/campd-unit-outages-netloadmask-SPP.csv"]:
        print(f"RESOLVED OUTAGE CHECK: FAIL -- {ri.get('path')}")
        ok = False
    else:
        print("RESOLVED OUTAGE CHECK: PASS")
    pl, slack_l = _prices(lg, a.year)
    pk, slack_k = _prices(kp, a.year)
    zs = sorted(pl.columns)
    if zs != ["SPP-North", "SPP-South"]:
        print(f"TOPOLOGY CHECK: FAIL -- zones {zs}")
        ok = False
    else:
        print("TOPOLOGY CHECK: PASS -- SPP-North / SPP-South")
    disp = lg / "dispatch" / f"{a.year}_P1.parquet"
    if not disp.exists():
        print(f"ARTIFACT CHECK: FAIL -- {disp} missing")
        ok = False
    else:
        print(f"ARTIFACT CHECK: PASS -- {disp.name} {disp.stat().st_size} bytes")

    rk, rl = readout(kp, a.year), readout(lg, a.year)
    d = {
        k: round(rl["twh"].get(k, 0.0) - rk["twh"].get(k, 0.0), 4)
        for k in sorted(set(rk["twh"]) | set(rl["twh"]))
    }
    dp = float((pl - pk).abs().to_numpy().max())
    print(json.dumps({"keeper": rk, "leg": rl}, indent=1))
    print(f"class TWh leg - keeper: {d}")
    print(f"price_mean_dw leg - keeper: {rl['price_mean_dw'] - rk['price_mean_dw']:+.3f}")
    print(f"max hourly |dprice| {dp:.6f}; slack MWh leg {slack_l:.1f} keeper {slack_k:.1f}")
    if a.year in ARM_YEARS:
        dw = d.get("WIND", d.get("wind", 0.0))
        print(f"ARMING (reported): wind TWh leg - keeper {dw:+.4f} -> {'PASS' if dw < 0 else 'FAIL'}")
    else:
        same = all(abs(v) <= 1e-4 for v in d.values()) and dp <= 1e-6
        print(f"IDENTITY (reported): {'PASS' if same else 'FAIL'} -- max |dTWh| "
              f"{max((abs(v) for v in d.values()), default=0.0):.4f}, max |dprice| {dp:.6f}")
    print("SHARD CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
