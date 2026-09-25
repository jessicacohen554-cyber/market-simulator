#!/usr/bin/env python3
"""miso-271 shard self-check: is this leg the rmiso-arm-b-mid keeper recipe + EXACTLY the miso-271 delta?

Copy of ``_rmiso_shard_check.py`` re-pointed at the current MISO keeper
(``results/calibration/rmiso_b_span``, every year 2019-2025 has a keeper leg).
The arm's delta is the pre-registered statistical-WEFOR retirement
(``wefor_residual`` None -> 0.0 scoped by ``wefor_residual_groups``,
docs/PRECOMMIT-miso271-*.md); ``--control`` expects NO delta. Input sha256s are
re-pinned at the miso-271 PRECOMMIT SHA.

Inherited header (R-MISO): run by each R-MISO shard AFTER its single-year solve and BEFORE it pushes (rule 32
``[R-SHARD]`` (c)(4)). Zero LP. Exit 0 only when every HARD check passes.

HARD checks:

1. **recipe** — the leg's recorded ``scenario_config`` for ``--year`` differs from
   the keeper's per-year recipe by EXACTLY :data:`EXPECTED` (miso-271: the
   two wefor fields for an arm leg, nothing for a control leg). Year-driven fields
   (:data:`YEAR_DRIVEN`) are excluded for 2019 only. A field present only in the
   leg (added after the keeper solved) is allowed only at its dataclass default.
2. **vintage** — ``resolve_backcast_eia860_vintage`` resolves the solve year and
   ``data/raw/eia-860/vintage_<Y>/`` exists for 2019-2024 (2025 reads canonical).
3. **inputs** — every pinned input file's sha256 equals :data:`INPUT_SHA` (the
   outage families, the interchange and hub-LMP inputs this lane landed).
4. **hydro classifier** — same partition sha the keeper solved on.
5. **log** — the solve log carries each armed mechanism's application line
   (:data:`LOG_MARKERS`), so no armed flag silently no-opped.

Reported (never a stop): per-class TWh and load-weighted internal price, leg
minus the committed keeper (2019: no keeper year, skipped).

Usage::

    python scripts/probes/_miso271_shard_check.py --leg results/calibration/miso271_arm_2021 \\
        --year 2021 --log solve_2021.log --groups CC_REGULAR ST_CHP ST_GAS
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

from _hydro5_shard_check import CLASSIFIER_SHA, classifier_sha  # noqa: E402

KEEPER = ROOT / "results/calibration/rmiso_b_span"
#: Filled by main(): the arm's pre-registered delta (PRECOMMIT §4), empty for --control.
EXPECTED: dict[str, tuple] = {}
ARM_GROUPS: list[str] = []  # set from --groups (the PRECOMMIT's G-IDENT scope, sorted)
YEAR_DRIVEN = {"gas_offer_margin_anchor", "gas_price_override", "weather_year", "ordc_mcl_mw", "ordc_voll"}
INPUT_SHA: dict[str, str] = {
    # Pinned at the PRECOMMIT (docs/PRECOMMIT-rmiso-corrected-inputs-2019-2025-2026-09-24.md §3).
    "data/raw/campd-unit-outages-unitroute-MISO.csv": "a91706662b335e34984c567029843bb46e0a8889f02a20792d987b698206873b",
    "data/raw/campd-unit-outages-short-MISO.csv": "becfd7bdd042f97d407decc2d4b737f015bcd948704f73a3bb827749a2093a1a",
    "data/raw/campd-unit-outages-shortgas-MISO.csv": "3bac354606270ee7c1094f5fa19c26bac8e9c2ec45cbc96700adafd440af44bc",
    "data/raw/campd-partial-outages-MISO.csv": "3792217d858dcb2c93711b6a8bbdb326cb801609e40721db30ba2831bb3d337e",
    "data/raw/campd-unit-outages-maxgen-unitroute-MISO.csv": "7fe45df18bc5072ad1424af7b80e955a29b37232be635c50918c7a594c9761ef",
    "data/raw/campd-unit-outages-layup-MISO.csv": "39c07740c5f43c2439e6e59c88149fd396e6819477d3e56ac0ba180229cfbbfd",
    "data/raw/eia-930-interchange/MISO interchange hourly.parquet": "ca5fb48db2b44285efb5a5b90cdfc85f156638b069e902af25234a44bf575fcc",
    "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet": "57a5d9e4c08eca0290eb902e4d3724d3f48a2967112dc4ff1345b7678a7c1a1c",
    "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet": "8c6bdf27e813491c7bddaaecab28d4b02ed3c0e7518bc1cb8337d2d16a2ffabd",
    "data/raw/coal-receipts/coal_receipts_2017.csv": "8c1d54c273e8f0b8d46363ef3e72b028fd01880f3c6e40d62f6746ed1a314b90",
    "data/raw/_processed-legacy/coal_sigmoid_params.csv": "9697169e613f0dc97868a97e9a601c029d308e745a2a197df9239a06289bae47",
}
LOG_MARKERS = (
    "unit-outage derate (MISO",
    "short unit-outage derate (MISO",
    "coal per-yard budget",
    "seam bands repriced to the MEASURED per-seam",
    "simultaneous-transfer limit REPLACED",
)
INTERNAL = ("MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana", "MISO-East", "MISO-South")


def _scenario(bundle: Path, year: int) -> dict:
    per_year = bundle / f"run_config_{year}.json"
    rc = per_year if per_year.exists() else bundle / "run_config.json"
    return json.loads(rc.read_text())["scenario_config"]


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    ch = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    return (ch.groupby("klass", observed=True)["mw"].sum() / 1e6).round(4).to_dict()


def _lw_price(bundle: Path, year: int) -> float:
    s = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    s = s[(s["pass"] == "P1") & (s["zone"].isin(INTERNAL))]
    return float((s["price"] * s["demand"]).sum() / s["demand"].sum())


def check_recipe(leg: Path, year: int) -> bool:
    """HARD 1: the leg is the keeper recipe plus exactly :data:`EXPECTED`."""
    from market_sim.config.scenarios import ScenarioConfig

    defaults = {
        f.name: f.default for f in dataclasses.fields(ScenarioConfig) if f.default is not dataclasses.MISSING
    }
    kyear = year if (KEEPER / f"run_config_{year}.json").exists() else 2020
    a, k = _scenario(leg, year), _scenario(KEEPER, kyear)
    # COAL-SUB (declared LIVE in PRECOMMIT §3): HEAD folds the keeper's bare
    # ``COAL`` offer curve away. Tolerated ONLY when it equals ``COAL_BIT`` (the
    # recipe's own identity), so a real multiplier move still FAILS.
    kc = dict(k.get("offer_curve_by_group") or {})
    if "COAL" in kc and "COAL" not in (a.get("offer_curve_by_group") or {}):
        if kc["COAL"] != kc.get("COAL_BIT"):
            print("COAL fold: keeper COAL != COAL_BIT -> not tolerated")
        else:
            kc.pop("COAL")
            k = {**k, "offer_curve_by_group": kc}
    skip = YEAR_DRIVEN if kyear != year else set()
    def _n(v):
        return sorted(v) if isinstance(v, (list, tuple, set, frozenset)) else v

    diff = {key: (_n(k[key]), _n(a[key])) for key in sorted(set(a) & set(k)) if _n(a[key]) != _n(k[key]) and key not in skip}
    new_only = {key: a[key] for key in sorted(set(a) - set(k))}
    bad_new = {
        key: v
        for key, v in new_only.items()
        if key in defaults and json.dumps(v, default=str) != json.dumps(defaults[key], default=str)
        and key not in EXPECTED
    }
    got = dict(diff)
    for key in EXPECTED:
        if key in new_only:
            got[key] = (EXPECTED[key][0], new_only[key])
    print(f"recipe diff vs keeper {kyear}: {got}")
    print(f"fields new since keeper: {len(new_only)} (non-default, unexpected: {bad_new})")
    ok = got == EXPECTED and not bad_new
    print("RECIPE CHECK:", "PASS" if ok else "FAIL")
    return ok


def check_vintage(year: int) -> bool:
    """HARD 2: the EIA-860 vintage resolves to the solve year and exists."""
    from market_sim.config.paths import EIA_860_DIR, resolve_backcast_eia860_vintage

    v = resolve_backcast_eia860_vintage(None, year, True)
    d = EIA_860_DIR / f"vintage_{year}"
    ok = v == year and (d.is_dir() if year <= 2024 else True)
    print(f"eia860 vintage resolved {v}; dir {d.name} exists={d.is_dir()}")
    print("VINTAGE CHECK:", "PASS" if ok else "FAIL")
    return ok


def check_inputs() -> bool:
    """HARD 3: pinned input sha256s."""
    ok = True
    for rel, want in INPUT_SHA.items():
        got = _sha(ROOT / rel)
        flag = got == want
        ok &= flag
        print(f"  {'ok ' if flag else 'BAD'} {rel} {got[:16]}")
    print("INPUTS CHECK:", "PASS" if ok else "FAIL")
    return ok


def check_log(log: Path) -> bool:
    """HARD 5: every armed mechanism logged its application line."""
    text = log.read_text(errors="replace")
    ok = True
    for m in LOG_MARKERS:
        n = text.count(m)
        bad = n == 0 or "NOT APPLIED" in "".join(ln for ln in text.splitlines() if m in ln)
        ok &= not bad
        print(f"  {'ok ' if not bad else 'BAD'} {n:3d} x '{m}'")
    print("LOG CHECK:", "PASS" if ok else "FAIL")
    return ok


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--leg", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--log", required=True, help="the leg's solve log")
    ap.add_argument("--control", action="store_true", help="control leg: expect NO delta vs the keeper")
    ap.add_argument("--groups", nargs="*", default=[], help="arm: the pre-registered wefor_residual_groups")
    args = ap.parse_args()
    if not args.control:
        if not args.groups:
            raise SystemExit("arm leg needs --groups (PRECOMMIT §4 scope)")
        EXPECTED["wefor_residual"] = (None, 0.0)
        EXPECTED["wefor_residual_groups"] = (None, sorted(args.groups))
    leg = ROOT / args.leg
    ok = check_recipe(leg, args.year)
    ok &= check_vintage(args.year)
    ok &= check_inputs()
    sha = classifier_sha("MISO")
    c_ok = sha == CLASSIFIER_SHA["MISO"]
    print(f"hydro classifier sha {sha} (keeper {CLASSIFIER_SHA['MISO']}) CLASSIFIER CHECK:", "PASS" if c_ok else "FAIL")
    ok &= c_ok
    ok &= check_log(Path(args.log))
    if (KEEPER / f"hourly/class_hourly_{args.year}.parquet").exists():
        try:
            ca, ck = _class_twh(leg, args.year), _class_twh(KEEPER, args.year)
            delta = {
                c: round(ca.get(c, 0.0) - ck.get(c, 0.0), 3)
                for c in sorted(set(ca) | set(ck))
                if abs(ca.get(c, 0.0) - ck.get(c, 0.0)) >= 0.001
            }
            pa, pk = _lw_price(leg, args.year), _lw_price(KEEPER, args.year)
            print(json.dumps({"class_twh_leg_minus_keeper": delta}, indent=1))
            print(f"load-weighted internal price: keeper {pk:.3f} -> leg {pa:.3f} ({pa - pk:+.3f} $/MWh)")
        except FileNotFoundError as exc:
            print(f"readout: sidecar missing ({exc})")
    print("OVERALL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
