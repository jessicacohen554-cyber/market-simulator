"""SPP-86 shard self-check: the arm leg == the committed keeper + EXACTLY ``unit_outage_coal_extract_basis_share``.

Run by each SPP-86 shard AFTER its solve and BEFORE it pushes (rule 32(c)(4) hard stops). Zero LP.
Pre-registered in ``docs/handoffs/PRECOMMIT-spp-86-coal-extract-basis-2026-09-26.md``. Adapted
from ``_spp85_shard_check.py``.

NO CONTROL SOLVE (rule 29(b) form 4): the G-DRIFT audit ``0ff620d1`` -> the pinned SHA classifies
every backcast-path hunk INERT for SPP, so the committed keeper ``spp85_arm_span`` IS the control.
Its per-year ``run_config_<Y>.json`` was written AFTER the COAL-SUB key translation (it was solved
at ``0ff620d1``, which already carried it), so the SPP-85 bare-``COAL`` false alarm cannot recur;
if any other field differs the shard STOPS.

1. **recipe** -- the arm leg's ``scenario_config`` differs from the keeper's ``run_config_<Y>.json``
   by EXACTLY ``unit_outage_coal_extract_basis_share`` (fields added to ``ScenarioConfig`` since the
   keeper was solved must sit at their dataclass default).
2. **gas price** -- ``gas_price_override`` equals the keeper's own value for the year.
3. **inputs** -- the three ``-netloadmask-`` companions and the three incumbent SPP CAMPD extracts
   carry the keeper's pinned sha256 (the arm reads the SAME extracts; only the share basis moves).
4. **resolved** -- the leg's ``run_config.json`` records the ``-netloadmask-`` standard extract.
5. **readout** -- per-class P1 TWh and demand-weighted mean price, arm vs keeper.

Exit 0 only when (1)-(4) pass; a failing shard does not push.

Usage::

    python scripts/probes/_spp86_shard_check.py --year 2021 --leg results/calibration/spp86_arm_2021
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

KEEPER = "results/calibration/spp85_arm_span"
ARM = "unit_outage_coal_extract_basis_share"
MUST_STAY = {
    "unit_outage_netload_mask_repair": True,
    "unit_outage_extract_basis_share": False,
    "unit_outage_dispatched_bin_denominator": False,
    "unit_outage_short_windows": True,
    "unit_outage_short_windows_gas": False,
    "unit_partial_outage_windows": True,
    "outage_source": "historic",
}
SHA = {
    "data/raw/campd-unit-outages-netloadmask-SPP.csv": "431613655433695e331c5d9986237127db4efc3455dbd7200fdafb00d1963012",
    "data/raw/campd-unit-outages-short-netloadmask-SPP.csv": "5c016785a746a9c9f7d6dcce060ba9fb81221d95526d02aaaa51fec8139535e7",
    "data/raw/campd-partial-outages-netloadmask-SPP.csv": "3792217d858dcb2c93711b6a8bbdb326cb801609e40721db30ba2831bb3d337e",
    "data/raw/campd-unit-outages-SPP.csv": "05aced4ff69fe85d0ed8e4683520644a3b1717689a0be486216391f9383361ad",
    "data/raw/campd-unit-outages-short-SPP.csv": "82fca832aeeca6f14c0ee31542f0caf74efdf3856e8f4f5c65086ab2b8449f8f",
    "data/raw/campd-partial-outages-SPP.csv": "7acc39f6e21d7d5e9b37a03d3701a1ee65da7bc2b028afb5b15c2309ca8944b4",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    extra = {k: v for k, v in changed.items() if k != ARM}
    new_extra = {k: v for k, v in new.items() if k != ARM}
    stay_bad = {k: sl.get(k) for k, v in MUST_STAY.items() if sl.get(k) != v}
    print(f"arm vs committed keeper: changed {changed}  non-default new {new}")
    if extra or new_extra or sl.get(ARM) is not True or stay_bad:
        print(
            f"RECIPE CHECK: FAIL -- extra {extra} new {new_extra} arm={sl.get(ARM)} "
            f"must-stay {stay_bad}"
        )
        ok = False
    else:
        print(f"RECIPE CHECK: PASS -- only {ARM}=True differs from the keeper")
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
    print(f"resolved campd_unit_outages: {ri.get('path')} {str(ri.get('sha256'))[:16]}")
    if ri.get("sha256") != SHA["data/raw/campd-unit-outages-netloadmask-SPP.csv"]:
        print("RESOLVED OUTAGE CHECK: FAIL")
        ok = False
    else:
        print("RESOLVED OUTAGE CHECK: PASS")
    rk = readout(kp, a.year)
    rl = readout(lg, a.year)
    print(json.dumps({"keeper": rk, "arm": rl}, indent=1))
    d = {
        k: round(rl["twh"].get(k, 0.0) - rk["twh"].get(k, 0.0), 3)
        for k in sorted(set(rk["twh"]) | set(rl["twh"]))
    }
    print(f"class TWh arm - keeper: {d}")
    print(f"price_mean_dw arm - keeper: {rl['price_mean_dw'] - rk['price_mean_dw']:+.3f}")
    print("SHARD CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
