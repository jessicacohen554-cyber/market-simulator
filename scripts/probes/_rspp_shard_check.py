"""R-SPP shard self-check: the leg == the incumbent recipe + EXACTLY the R-SPP arms.

Run by each R-SPP shard AFTER its solve and BEFORE it pushes (rule 32(c)(4) hard stops). Zero LP.
Pre-registered in ``docs/handoffs/PRECOMMIT-r-spp-2019-2025-inputs-2026-09-24.md``. Adapted from
``_spp78_shard_check.py``.

1. **recipe** — the leg's ``scenario_config`` differs from the incumbent bundle's for the year by
   EXACTLY the R-SPP arm set (each must read True in the leg): the five
   ``measured_*_heat_rates``, ``unit_partial_outage_windows``, ``mid_vintage_exit_carry`` (already
   True on the 2019-22 rung) and ``eia860_vintage_tracks_solve_year`` (already True everywhere).
   Any other changed field, or a new field away from its dataclass default, FAILS.
2. **gas price** — ``gas_price_override`` equals the hard-stop value.
3. **inputs** — the nine SPP input files' sha256 equal the pinned values (five measured heat-rate
   artifacts, three armed CAMPD outage extracts, the year's EIA-860 generator table).
4. **readout** — per-class P1 TWh (incumbent vs leg) and demand-weighted mean price.

Exit 0 only when (1)-(3) pass; a failing shard does not push.

Usage::

    python scripts/probes/_rspp_shard_check.py --year 2020 \\
        --keeper results/calibration/hydro5_spp_floor_rung --leg results/calibration/rspp_2020
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

ARMS = (
    "measured_ct_heat_rates",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "measured_chp_heat_rates",
    "unit_partial_outage_windows",
    "mid_vintage_exit_carry",
    "eia860_vintage_tracks_solve_year",
)
MUST_STAY = {
    "unit_outage_short_windows": True,
    "unit_outage_short_windows_gas": False,
    "hydro_min_flow_floor": True,
}
GAS = {
    2019: 2.57,
    2020: 2.03,
    2021: 3.72,
    2022: 6.45,
    2023: 2.54,
    2024: 2.19,
    2025: 3.52,
}
SHA = {
    "data/raw/_processed-legacy/campd_ct_heat_rates_SPP.csv": "212f8f33420220592fe6e54534402a9ede1c7f2d8f26d937204a8f3e2c7c3e78",
    "data/raw/_processed-legacy/campd_coal_heat_rates_SPP.csv": "db7a9bcd6cee41f96400e8e2db8d4e490e706935b0938ff51ce4acbbc963b6a1",
    "data/raw/_processed-legacy/campd_st_heat_rates_SPP.csv": "41d698db87b3ed80f80079ac25601fa2885f8fb86f8e53d8269c33643a8f141b",
    "data/raw/_processed-legacy/campd_cc_heat_rates_SPP.csv": "bed19b45368662370985f97b1faddc209f5e9c31cf177c578bd16722ae55bee8",
    "data/raw/_processed-legacy/chp_power_only_heat_rates_SPP.csv": "a29d2223e72ef769dc8132d38510237d952bbaca37397081e7d6e63955bd9fec",
    "data/raw/campd-unit-outages-SPP.csv": "05aced4ff69fe85d0ed8e4683520644a3b1717689a0be486216391f9383361ad",
    "data/raw/campd-unit-outages-short-SPP.csv": "82fca832aeeca6f14c0ee31542f0caf74efdf3856e8f4f5c65086ab2b8449f8f",
    "data/raw/campd-partial-outages-SPP.csv": "7acc39f6e21d7d5e9b37a03d3701a1ee65da7bc2b028afb5b15c2309ca8944b4",
}
EIA860 = {
    2019: (
        "vintage_2019",
        "81c471aba3ae7a7d006ab90ccb8ac9b2b5859336df34f3cc520c2d3544d00215",
    ),
    2020: (
        "vintage_2020",
        "1ec2b2005488200f9c98f9092e69a3e92dd4035960f16f2d554e35552be52144",
    ),
    2021: (
        "vintage_2021",
        "23621b5e4d48dd589973d5b4c8826ffbac6781d5238fd085f19b0dd7fa536513",
    ),
    2022: (
        "vintage_2022",
        "571c0f72a620715ff31196e85128e8dade984096ec9cfed1d5e84e512eab16ea",
    ),
    2023: (
        "vintage_2023",
        "99f2dadd39bc06d237a2351c7a2562db8e1d24df665fd99a90f6899633b321eb",
    ),
    2024: (
        "vintage_2024",
        "43f1fb8c9df64d33ab8f34b9c543454d75d6c2677d9ed222adcfa8ba9844cb68",
    ),
    2025: ("", "8149984897d7bdb15623a6d1ff03331d324bd1e6be601068982c5488739cb267"),
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--keeper", required=True)
    ap.add_argument("--leg", required=True)
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
    extra = {k: v for k, v in changed.items() if k not in ARMS}
    print(f"leg vs incumbent: changed {changed}  non-default new {new}")
    not_true = [f for f in ARMS if sl.get(f) is not True]
    stay_bad = {k: sl.get(k) for k, v in MUST_STAY.items() if sl.get(k) != v}
    if extra or new or not_true or stay_bad:
        print(
            f"RECIPE CHECK: FAIL — extra {extra} new {new} arms-not-True {not_true} "
            f"must-stay {stay_bad}"
        )
        ok = False
    else:
        print(
            f"RECIPE CHECK: PASS — arms True: {list(ARMS)}; changed vs incumbent: {sorted(changed)}"
        )
    gas = sl.get("gas_price_override")
    if gas is None or abs(float(gas) - GAS[a.year]) > 1e-9:
        print(f"GAS CHECK: FAIL — {gas} != {GAS[a.year]}")
        ok = False
    else:
        print(f"GAS CHECK: PASS — {gas}")
    sub, want = EIA860[a.year]
    files = dict(SHA)
    files[str(Path("data/raw/eia-860") / sub / "eia860_generators.parquet")] = want
    for rel, h in files.items():
        got = _sha(ROOT / rel)
        tag = "PASS" if got == h else "FAIL"
        ok &= got == h
        print(f"SHA {tag} {rel} {got[:16]}")
    rc = json.loads((lg / "run_config.json").read_text())
    ri = (rc.get("resolved_inputs") or {}).get("campd_unit_outages") or {}
    print(f"resolved campd_unit_outages: {ri.get('path')} {str(ri.get('sha256'))[:16]}")
    if ri.get("sha256") != SHA["data/raw/campd-unit-outages-SPP.csv"]:
        print("RESOLVED OUTAGE CHECK: FAIL")
        ok = False
    rk, rl = (
        readout(kp, a.year)
        if (kp / f"hourly/class_hourly_{a.year}.parquet").exists()
        else None,
        readout(lg, a.year),
    )
    print(json.dumps({"incumbent": rk, "leg": rl}, indent=1))
    if rk:
        d = {
            k: round(rl["twh"].get(k, 0.0) - rk["twh"].get(k, 0.0), 3)
            for k in sorted(set(rk["twh"]) | set(rl["twh"]))
        }
        print(f"class TWh leg - incumbent: {d}")
        print(
            f"price_mean_dw leg - incumbent: {rl['price_mean_dw'] - rk['price_mean_dw']:+.3f}"
        )
    print("SHARD CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
