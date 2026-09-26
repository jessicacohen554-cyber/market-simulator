"""SPP-85 shard self-check: the arm leg == its control + EXACTLY ``unit_outage_netload_mask_repair``.

Run by each SPP-85 shard AFTER its solve and BEFORE it pushes (rule 32(c)(4) hard stops). Zero LP.
Pre-registered in ``docs/handoffs/PRECOMMIT-spp-85-netload-mask-repair-2026-09-26.md``. Adapted
from ``_rspp_shard_check.py``.

1. **recipe** -- the arm leg's ``scenario_config`` differs from its OWN CONTROL leg (the keeper
   recipe replayed at the same pinned SHA, ``--control``) by EXACTLY ``unit_outage_netload_mask_repair``.
   Any other changed field, or a new field away from its dataclass default, FAILS. (Diffing against
   the COMMITTED keeper instead is wrong at HEAD: ``replay_keeper`` translates the keeper's bare
   ``COAL`` offer-curve key to its subclasses, so control and arm both differ from the committed
   recipe by that key. The control-vs-keeper diff is printed for the record.)
2. **gas price** -- ``gas_price_override`` equals the keeper's own value for the year.
3. **inputs** -- the three ``-netloadmask-`` companions and the three incumbent SPP CAMPD extracts
   carry the pinned sha256.
4. **resolved** -- the leg's ``run_config.json`` records the ``-netloadmask-`` standard extract as
   the CAMPD path it actually read.
5. **readout** -- per-class P1 TWh (keeper vs leg) and demand-weighted mean price.

Exit 0 only when (1)-(4) pass; a failing shard does not push.

Usage::

    python scripts/probes/_spp85_shard_check.py --year 2020 --leg results/calibration/spp85_2020
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

KEEPER = "results/calibration/rspp_span"
ARM = "unit_outage_netload_mask_repair"
MUST_STAY = {
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
    ap.add_argument(
        "--control", help="the same year's control leg (default spp85_ctl_<Y>)"
    )
    a = ap.parse_args()
    from market_sim.config.scenarios import ScenarioConfig

    defaults = {
        f.name: f.default
        for f in dataclasses.fields(ScenarioConfig)
        if f.default is not dataclasses.MISSING
    }
    kp, lg = ROOT / a.keeper, ROOT / a.leg
    ct = ROOT / (a.control or f"results/calibration/spp85_ctl_{a.year}")
    sk, sl, sc = _scenario(kp, a.year), _scenario(lg, a.year), _scenario(ct, a.year)
    ok = True
    kc_changed, kc_new = _diff(sk, sc, defaults)
    print(
        f"control vs committed keeper (record only): changed {sorted(kc_changed)} new {kc_new}"
    )
    changed, new = _diff(sc, sl, defaults)
    extra = {k: v for k, v in changed.items() if k != ARM}
    new_extra = {k: v for k, v in new.items() if k != ARM}
    stay_bad = {k: sl.get(k) for k, v in MUST_STAY.items() if sl.get(k) != v}
    print(f"arm vs control: changed {changed}  non-default new {new}")
    if extra or new_extra or sl.get(ARM) is not True or stay_bad:
        print(
            f"RECIPE CHECK: FAIL -- extra {extra} new {new_extra} arm={sl.get(ARM)} "
            f"must-stay {stay_bad}"
        )
        ok = False
    else:
        print(f"RECIPE CHECK: PASS -- only {ARM}=True differs from the control")
    gk, gl = sc.get("gas_price_override"), sl.get("gas_price_override")
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
    rk = readout(ct, a.year)
    rl = readout(lg, a.year)
    print(json.dumps({"control": rk, "arm": rl}, indent=1))
    if rk:
        d = {
            k: round(rl["twh"].get(k, 0.0) - rk["twh"].get(k, 0.0), 3)
            for k in sorted(set(rk["twh"]) | set(rl["twh"]))
        }
        print(f"class TWh arm - control: {d}")
        print(
            f"price_mean_dw arm - control: {rl['price_mean_dw'] - rk['price_mean_dw']:+.3f}"
        )
    print("SHARD CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
