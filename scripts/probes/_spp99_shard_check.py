"""SPP-99 shard self-check: the SPP keeper replayed with ``campd_split_remap_companions`` armed.

Run by each SPP-99 shard AFTER its solve and BEFORE it pushes (rule 32(c)(4) hard stops). Zero LP.
Pre-registered in ``docs/records/spp/PRECOMMIT-spp-99-remap-rederive-2026-09-28.md``. Adapted from
``_spp98_shard_check.py``; the control is the committed keeper ``spp98_remap_span`` (rule 29(b)
form 4).

Hard checks (exit 1 on any failure; a failing shard does not push):

1. **recipe** -- the leg's ``scenario_config`` equals the keeper's ``run_config_<Y>.json`` plus
   EXACTLY ``campd_split_remap_companions = true`` (every other field added since the keeper was
   solved sits at its default).
2. **gas price** -- ``gas_price_override`` equals the keeper's own value for the year.
3. **inputs** -- the SPP incumbents, the four ``-splitremap-`` companions and the curtailment
   table carry their pinned sha256.
4. **resolved** -- the leg's ``run_config.json`` records the ``-netloadmask-splitremap-`` outage
   extract and the ``thermal_tranches-splitremap-SPP.csv`` tranche artifact.
5. **topology** -- ``system_<Y>.parquet`` carries exactly SPP-North / SPP-South.
6. **artifact** -- ``dispatch/<Y>_P1.parquet`` exists (rule 34(a)).
7. **remap** -- ``campd.CAMPD_UNIT_PLANT_REMAP`` carries (1416, CTG-6A/6B) -> 56565.

Reported (never a push blocker -- the parent adjudicates): per-class TWh, demand-weighted price,
slack MWh and max hourly |dprice|, leg vs keeper.

Usage::

    python scripts/probes/_spp99_shard_check.py --year 2021 --leg results/calibration/spp99_arm_2021
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

KEEPER = "results/calibration/spp98_remap_span"
ARM = {"campd_split_remap_companions": True}
REMAP_EXTRACT = "data/raw/campd-unit-outages-netloadmask-splitremap-SPP.csv"
REMAP_TRANCHES = "data/raw/_processed-legacy/thermal_tranches-splitremap-SPP.csv"
SHA = {
    REMAP_EXTRACT: "41ee31e02c60f55c75bdba5802cc10ecf70fb9a3bfaa4f30e10b3bcfd0614b73",
    REMAP_TRANCHES: "92ed67de6b5c80630c9f8e319882facb422cd411f96b496463ec6e003cb465f2",
    "data/raw/_processed-legacy/campd_cc_heat_rates-splitremap-SPP.csv": "c144ddd7f58e9ffb4d981e517cc024e2a3091b5ed78022e893b4953f8973d1dc",
    "data/raw/campd-unit-outages-splitremap-SPP.csv": "8cd6dbd9b4d84972af1ea116af48a5b6bdf9f9d7369fe63bafcf9f888de62dec",
    "data/raw/_processed-legacy/campd_cc_heat_rates_SPP.csv": "bed19b45368662370985f97b1faddc209f5e9c31cf177c578bd16722ae55bee8",
    "data/raw/campd-unit-outages-netloadmask-SPP.csv": "431613655433695e331c5d9986237127db4efc3455dbd7200fdafb00d1963012",
    "data/raw/campd-unit-outages-short-netloadmask-SPP.csv": "5c016785a746a9c9f7d6dcce060ba9fb81221d95526d02aaaa51fec8139535e7",
    "data/raw/campd-partial-outages-netloadmask-SPP.csv": "3792217d858dcb2c93711b6a8bbdb326cb801609e40721db30ba2831bb3d337e",
    "data/raw/_processed-legacy/thermal_tranches_SPP.csv": "fdeadb1ad4e561324c53fd02f83c83f01d1126c3c3c23328b457f44b43179e33",
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
    if changed or new != ARM:
        print(f"RECIPE CHECK: FAIL -- must be the keeper + exactly {ARM}")
        ok = False
    else:
        print(f"RECIPE CHECK: PASS -- keeper + exactly {ARM}")
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
    if ri.get("sha256") != SHA[REMAP_EXTRACT]:
        print(f"RESOLVED OUTAGE CHECK: FAIL -- {ri.get('path')}")
        ok = False
    else:
        print(f"RESOLVED OUTAGE CHECK: PASS -- {ri.get('path')}")
    rt = (rc.get("resolved_inputs") or {}).get("thermal_tranches") or {}
    if rt.get("sha256") != SHA[REMAP_TRANCHES]:
        print(f"RESOLVED TRANCHE CHECK: FAIL -- {rt.get('path')}")
        ok = False
    else:
        print(f"RESOLVED TRANCHE CHECK: PASS -- {rt.get('path')}")
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

    from market_sim.data import campd

    rm = {u: campd.CAMPD_UNIT_PLANT_REMAP.get((1416, u)) for u in ("CTG-6A", "CTG-6B")}
    if set(rm.values()) != {56565}:
        print(f"REMAP CHECK: FAIL -- {rm}")
        ok = False
    else:
        print("REMAP CHECK: PASS -- (1416, CTG-6A/6B) -> 56565")

    rk, rl = readout(kp, a.year), readout(lg, a.year)
    d = {
        k: round(rl["twh"].get(k, 0.0) - rk["twh"].get(k, 0.0), 4)
        for k in sorted(set(rk["twh"]) | set(rl["twh"]))
    }
    dp = float((pl - pk).abs().to_numpy().max())
    print(json.dumps({"keeper": rk, "leg": rl}, indent=1))
    print(f"class TWh leg - keeper: {d}")
    print(
        f"price_mean_dw leg - keeper: {rl['price_mean_dw'] - rk['price_mean_dw']:+.3f}"
    )
    print(
        f"max hourly |dprice| {dp:.6f}; slack MWh leg {slack_l:.1f} keeper {slack_k:.1f}"
    )
    print("SHARD CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
