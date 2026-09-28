#!/usr/bin/env python3
"""miso-280 shard check (ZERO LP): verify one arm leg before it composes.

Copy of ``_miso279_shard_check.py`` re-pointed at the current MISO keeper
(``results/calibration/miso279_span``, 2026-09-27-miso-279-stcov, every year
2019-2025). The arm's delta is ONE new field, ``campd_split_remap_companions``
False -> True (docs/PRECOMMIT-miso280-split-remap-2026-09-28.md). HARD 1b now
requires the solve to have READ all seven '-splitremap-' companions (std /
short-gas / maxgen outage extracts, CC heat rates, four tranche files) at their
pinned shas.

Inherited from miso-279: the recipe check, vintage, inputs, classifier and log
checks, unchanged.
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

KEEPER = ROOT / "results/calibration/miso279_span"
#: Filled by main(): the arm's pre-registered delta (PRECOMMIT §4), empty for --control.
EXPECTED: dict[str, tuple] = {}
ARM_GROUPS: list[str] = []  # set from --groups (the PRECOMMIT's G-IDENT scope, sorted)
YEAR_DRIVEN = {
    "gas_offer_margin_anchor",
    "gas_price_override",
    "weather_year",
    "ordc_mcl_mw",
    "ordc_voll",
}
INPUT_SHA: dict[str, str] = {
    # Pinned at the PRECOMMIT (docs/PRECOMMIT-rmiso-corrected-inputs-2019-2025-2026-09-24.md §3).
    "data/raw/campd-unit-outages-unitroute-MISO.csv": "a91706662b335e34984c567029843bb46e0a8889f02a20792d987b698206873b",
    # miso-273 arm inputs (PRECOMMIT §4): regenerated extract + the screened set.
    "data/raw/campd-unit-outages-short-MISO.csv": "0a02ad1d3a77fd66c00557c738ea952eac38f01df126c2ce801f791617f61161",
    "data/raw/campd-unit-outages-short-screened-MISO.csv": "f44c669518e59bda5113f58f968dee09cad2910eaa9d5dd74f9719d3f76bef23",
    "data/raw/campd-unit-outages-shortgas-MISO.csv": "3bac354606270ee7c1094f5fa19c26bac8e9c2ec45cbc96700adafd440af44bc",
    "data/raw/campd-partial-outages-MISO.csv": "3792217d858dcb2c93711b6a8bbdb326cb801609e40721db30ba2831bb3d337e",
    "data/raw/campd-unit-outages-maxgen-unitroute-MISO.csv": "7fe45df18bc5072ad1424af7b80e955a29b37232be635c50918c7a594c9761ef",
    "data/raw/campd-unit-outages-layup-MISO.csv": "39c07740c5f43c2439e6e59c88149fd396e6819477d3e56ac0ba180229cfbbfd",
    "data/raw/eia-930-interchange/MISO interchange hourly.parquet": "ca5fb48db2b44285efb5a5b90cdfc85f156638b069e902af25234a44bf575fcc",
    "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet": "57a5d9e4c08eca0290eb902e4d3724d3f48a2967112dc4ff1345b7678a7c1a1c",
    "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet": "8c6bdf27e813491c7bddaaecab28d4b02ed3c0e7518bc1cb8337d2d16a2ffabd",
    "data/raw/coal-receipts/coal_receipts_2017.csv": "8c1d54c273e8f0b8d46363ef3e72b028fd01880f3c6e40d62f6746ed1a314b90",
    "data/raw/_processed-legacy/coal_sigmoid_params.csv": "9697169e613f0dc97868a97e9a601c029d308e745a2a197df9239a06289bae47",
    # miso-276 arm inputs: the daily hubs, the ruled transport table, the zone->hub map.
    "data/raw/gas-prices/miso_citygate_daily.csv": "c6801756c4cb4e43b8bc11f37b75da84234cacad3c9b0c9be04855bd29664707",
    "data/raw/gas-prices/henry_hub_daily.csv": "7c2787a4001e0a6c2d7f468a77e4c2faadeb1df5d9214d9da990bfab162a4ad3",
    "data/raw/reference/miso_gas_variable_transport.csv": "ac8da759270851c39593e7a26efa7558b6521e95f717b42bc1c9066e6eb8c0ae",
    "data/raw/reference/miso_gas_variable_transport.pool.csv": "04214b258733152a73506b048a945b746d2f08308bd9d0600e25459bf059e713",
    # miso-278 arm inputs: the incumbent tranche family and its four
    # '-fuelsplit-' companions (derive_thermal_tranches.py --unit-fuel-split).
    "data/raw/_processed-legacy/thermal_tranches_MISO.csv": "31949ee5e13475db7611c2c6f15175626e17d414df534fab9179be66614280d8",
    "data/raw/_processed-legacy/thermal_tranches_online_frac_by_year_MISO.csv": "f932aa40e50f9cf6fe29a87b0d5bcad3f99f18f6a936ac58ab79dc51598a4c64",
    "data/raw/_processed-legacy/thermal_tranches_p25_level_mw_MISO.csv": "e8a96dbdfc091acc10134cf72b4f6c5a2fe537b21401b4e1a9ed0df0087008a7",
    "data/raw/_processed-legacy/thermal_tranches_oom_level_mw_MISO.csv": "b8c39f95c07d5f423e4fd2f03920814b42f510299dcf116a037d33db5bf3132f",
    "data/raw/_processed-legacy/thermal_tranches-fuelsplit-MISO.csv": "6792b3f9ab3619b3a70f6895e14258ec2913745b79758258a3460d40d12851f7",
    "data/raw/_processed-legacy/thermal_tranches_online_frac_by_year-fuelsplit-MISO.csv": "9961b432d3ed16b635ce2023d7bf747443182e418bd135c07fe8ea7fbddddd00",
    "data/raw/_processed-legacy/thermal_tranches_p25_level_mw-fuelsplit-MISO.csv": "55511bcbb98c8a5703792c421385b10a878e7725a012fad1439ab138b1f98ce7",
    "data/raw/_processed-legacy/thermal_tranches_oom_level_mw-fuelsplit-MISO.csv": "ad5b052299abb4e63bf62626a01da00d11446e524c43a51920d5486c421b0d37",
    # miso-279 arm inputs: the four '-fuelsplit-stcov-' companions
    # (derive_thermal_tranches.py --st-gas-span-coverage).
    "data/raw/_processed-legacy/thermal_tranches-fuelsplit-stcov-MISO.csv": "19f185be1ffec528e0a457979f326d7f65041f2bd4bf3966d855ec1ffcca5e04",
    "data/raw/_processed-legacy/thermal_tranches_online_frac_by_year-fuelsplit-stcov-MISO.csv": "532e72f135987a25f87fbac43d32b1a81282169cd8566c0b62bfe2f1ae7a5a12",
    "data/raw/_processed-legacy/thermal_tranches_p25_level_mw-fuelsplit-stcov-MISO.csv": "69e7c80ac2a9105b8aa7157ebc0e67ea19ad5ea142ea759cefefa2c3906fd9ee",
    "data/raw/_processed-legacy/thermal_tranches_oom_level_mw-fuelsplit-stcov-MISO.csv": "2d26face2c1b9d882c063d338309682491cf553297317d98f67fbac46ecc3260",
    # miso-280 arm inputs: the seven '-splitremap-' companions
    # (scripts/data/build_campd_split_remap_companions.py).
    "data/raw/campd-unit-outages-unitroute-splitremap-MISO.csv": "76c0ebb09fdef8de08639f8c5f7712c9a035eddc107834ea0af8bfaa61a9a834",
    "data/raw/campd-unit-outages-shortgas-splitremap-MISO.csv": "147b9b197e310d9586c3025b151fae4741c584564be98822b7dfcb5d5e83afca",
    "data/raw/campd-unit-outages-maxgen-unitroute-splitremap-MISO.csv": "67886b6572c4b7d34a89e524c94d1c470df47a55348bb7d7d48b48b714e1bb1f",
    "data/raw/_processed-legacy/campd_cc_heat_rates-splitremap-MISO.csv": "0c140f0487054fa2d5310ea82dd7bcdbf3b19703277de026bb99a7f3566b1799",
    "data/raw/_processed-legacy/thermal_tranches-fuelsplit-stcov-splitremap-MISO.csv": "d6a3c9e497f42a8d637d75df5c25dc00bbbc715a6bd455fcd972f2921d3d9f54",
    "data/raw/_processed-legacy/thermal_tranches_online_frac_by_year-fuelsplit-stcov-splitremap-MISO.csv": "88b00ce785166c71aed9a970716df850876ac8d47240bf30f26bc82371ce6298",
    "data/raw/_processed-legacy/thermal_tranches_p25_level_mw-fuelsplit-stcov-splitremap-MISO.csv": "a7393d7a6f373f7a9b077ec9b97d7907aa59ed8356986f5347c847b8015cb1b4",
    "data/raw/_processed-legacy/thermal_tranches_oom_level_mw-fuelsplit-stcov-splitremap-MISO.csv": "c61daea77720eb8bf7a1b68e25a05ac9b2c43d3c1ef7072973731594f346a0fb",
    "data/raw/miso_zonal_gas_hub.csv": "c987b6c3f41a2c70187463cf09e82fd53937d82567a8ed4e5cb8dd3605b682eb",
}
LOG_MARKERS = (
    "unit-outage derate (MISO",
    "short unit-outage derate (MISO",
    "coal per-yard budget",
    "seam bands repriced to the MEASURED per-seam",
    "simultaneous-transfer limit REPLACED",
    "CC block summer rating (plant 1004)",
    "short-screened coal WEFOR relief (MISO",
    "MISO winter daily delivered gas (",
    "MISO-South=henry",
)
#: miso-276: superseded by the arm (rule 19), and the neiso-117 yard reconcile
#: (G-DRIFT: must never fire on MISO, PRECOMMIT §3a / S-4).
ABSENT_MARKERS = (
    "MISO winter citygate daily (",
    "floors scaled",
)
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
        f.name: f.default
        for f in dataclasses.fields(ScenarioConfig)
        if f.default is not dataclasses.MISSING
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

    diff = {
        key: (_n(k[key]), _n(a[key]))
        for key in sorted(set(a) & set(k))
        if _n(a[key]) != _n(k[key]) and key not in skip
    }
    new_only = {key: a[key] for key in sorted(set(a) - set(k))}
    bad_new = {
        key: v
        for key, v in new_only.items()
        if key in defaults
        and json.dumps(v, default=str) != json.dumps(defaults[key], default=str)
        and key not in EXPECTED
    }
    got = dict(diff)
    for key in EXPECTED:
        if key in new_only:
            got[key] = (EXPECTED[key][0], new_only[key])
    print(f"recipe diff vs keeper {kyear}: {got}")
    print(
        f"fields new since keeper: {len(new_only)} (non-default, unexpected: {bad_new})"
    )
    ok = got == EXPECTED and not bad_new
    print("RECIPE CHECK:", "PASS" if ok else "FAIL")
    return ok


def check_resolved(leg: Path, year: int) -> bool:
    """HARD 1b: the solve READ all seven '-splitremap-' companions (no silent fallback)."""
    per_year = leg / f"run_config_{year}.json"
    rc = json.loads(
        (per_year if per_year.exists() else leg / "run_config.json").read_text()
    )
    ri = rc.get("resolved_inputs") or {}
    pl = "data/raw/_processed-legacy/"
    blk = ri.get("thermal_tranches") or {}
    base = "thermal_tranches-fuelsplit-stcov-splitremap-MISO.csv"
    ok = str(blk.get("path", "")).endswith(base) and (
        blk.get("sha256") == INPUT_SHA[pl + base]
    )
    print(f"  tranche path {blk.get('path')} sha {str(blk.get('sha256'))[:16]}")
    comp = blk.get("fuel_split_companions") or {}
    for name in ("online_frac_by_year", "p25_level_mw", "oom_level_mw"):
        rel = f"{pl}thermal_tranches_{name}-fuelsplit-stcov-splitremap-MISO.csv"
        c = comp.get(name) or {}
        good = c.get("sha256") == INPUT_SHA[rel] and "splitremap" in str(c.get("path"))
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} companion {name}: {c}")
    uo = ri.get("campd_unit_outages") or {}
    rel = "data/raw/campd-unit-outages-unitroute-splitremap-MISO.csv"
    good = (
        str(uo.get("path", "")).endswith(Path(rel).name)
        and uo.get("sha256") == INPUT_SHA[rel]
    )
    ok &= good
    print(f"  {'ok ' if good else 'BAD'} std outages {uo.get('path')}")
    sr = (ri.get("campd_split_remap") or {}).get("companions") or {}
    for name, rel in (
        (
            "unit_outages_short_gas",
            "data/raw/campd-unit-outages-shortgas-splitremap-MISO.csv",
        ),
        (
            "unit_outages_maxgen",
            "data/raw/campd-unit-outages-maxgen-unitroute-splitremap-MISO.csv",
        ),
        ("cc_heat_rates", pl + "campd_cc_heat_rates-splitremap-MISO.csv"),
    ):
        c = sr.get(name) or {}
        good = c.get("path") == Path(rel).name and c.get("sha256") == INPUT_SHA[rel]
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {c}")
    print("RESOLVED CHECK:", "PASS" if ok else "FAIL")
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
        bad = n == 0 or "NOT APPLIED" in "".join(
            ln for ln in text.splitlines() if m in ln
        )
        ok &= not bad
        print(f"  {'ok ' if not bad else 'BAD'} {n:3d} x '{m}'")
    for m in ABSENT_MARKERS:
        n = text.count(m)
        ok &= n == 0
        print(f"  {'ok ' if n == 0 else 'BAD'} {n:3d} x '{m}' (must be ABSENT)")
    print("LOG CHECK:", "PASS" if ok else "FAIL")
    return ok


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--leg", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--log", required=True, help="the leg's solve log")
    ap.add_argument(
        "--control",
        action="store_true",
        help="control leg: expect NO delta vs the keeper",
    )
    args = ap.parse_args()
    if args.control:
        raise SystemExit(
            "miso-280 has no control legs (G-DRIFT all INERT; PRECOMMIT §3)"
        )
    # The single delta: a new field, absent from the keeper recipe (default False).
    EXPECTED["campd_split_remap_companions"] = (False, True)
    leg = ROOT / args.leg
    ok = check_recipe(leg, args.year)
    ok &= check_resolved(leg, args.year)
    ok &= check_vintage(args.year)
    ok &= check_inputs()
    sha = classifier_sha("MISO")
    c_ok = sha == CLASSIFIER_SHA["MISO"]
    print(
        f"hydro classifier sha {sha} (keeper {CLASSIFIER_SHA['MISO']}) CLASSIFIER CHECK:",
        "PASS" if c_ok else "FAIL",
    )
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
            print(
                f"load-weighted internal price: keeper {pk:.3f} -> leg {pa:.3f} ({pa - pk:+.3f} $/MWh)"
            )
        except FileNotFoundError as exc:
            print(f"readout: sidecar missing ({exc})")
    print("OVERALL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
