"""nyiso-200 SCREEN GATES — the pre-registered gates of
``PREREG-nyiso200-bridge-run-screen.md`` §5, executed as written, for either
arm:

* ``--arm a1`` — the commitment-real run screen ALONE
  (``nyiso_gas_bridge_startup_aware``): S-1 bridge D-2 volume must not rise
  and falls inside the year's bound; S-2 census identity (floor moves only at
  units with dropped runs); S-3 confinement; S-4 no load-bearing flip, no new
  D-4 failure AT THE SPAN GUARD.
* ``--arm a3`` — the three-way pairing (+ ``nyiso_ct_peaker_bands_measured``
  + ``cc_duct_peaking_row_scoped``): the nyiso-199 §4 gates unchanged (S-1
  CT_PEAKER rises inside its own bound, S-2 gas-family confinement, S-3 no
  load-bearing flip incl. C1 CC_REGULAR, C3a-2025 the named risk) plus S-4
  the defect read directly: bridge-floored unit-hours at 7314 / 50978.

The screen is a rule-29 throwaway probe: it may KILL an arm and may never
promote one, and no gate reads the target residual. C1/C3a/C3b are scored with
the real scorer (``calibration_verdict``) on the keeper's committed payload
with the screen's class-energy and per-zone mean-price deltas substituted (the
nyiso-195..199 construction). D-4 is compared like-for-like on THIS year's
rows; the keeper's committed diagnostics already carry the span-guard union
and, since nyiso-200, so does a one-year screen bundle's.

Writes ``results/calibration/_nyiso200_screen_gates_<arm>_<year>.json``.

Usage::

    python scripts/probes/nyiso200_screen_gates.py --arm a1 --year 2023 \
        --screen results/calibration/nyiso200_screen_a1_2023 \
        [--census runs_dropped=N,units=M]
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts"):
    sys.path.insert(0, str(p))

import calibration_verdict as cv  # noqa: E402
from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402

KEEPER_ID = "2026-09-06-nyiso-196-extract-basis"
KEEPER = ROOT / "results/calibration/nyiso196_extract_basis"
PHASE0 = ROOT / "results/calibration/_nyiso200_bridge_phase0.json"
CT_PHASE0 = ROOT / "results/calibration/_nyiso199_ct_band_basis_phase0.json"
GAS_FAMILY = ("CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP", "CT_PEAKER", "CT_CHP")
MECH_BRIDGE = 20  # data.floor_mechanisms.MECH_NYISO_GAS_COMMITMENT_BRIDGE
NAMED_PLANTS = (7314, 50978)
NON_GAS_TOL_TWH = 0.05


def _r(x, n=4):
    return round(float(x), n)


def class_energy_twh(bundle: Path, year: int) -> pd.Series:
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return df.groupby("klass")["mw"].sum() / 1e6


def zone_mean_prices(bundle: Path, year: int) -> dict:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    p = df.pivot(index="hour", columns="zone", values="price")
    return {z: float(p[z].mean()) for z in p.columns}


def bridge_floor_hours_by_plant(bundle: Path, year: int) -> dict[int, dict]:
    """Per plant: bridge-floored unit-hours and floor MWh from floors/<Y>_P1.npz."""
    f = bundle / "floors" / f"{year}_P1.npz"
    if not f.exists():
        return {}
    z = np.load(f, allow_pickle=False)
    mg, mech, pc = z["min_gen"], z["mechanism"], z["plant_code"]
    sel = (mech == MECH_BRIDGE) & (mg > 0)
    out: dict[int, dict] = {}
    for code in np.unique(pc[sel.any(axis=1)]):
        rows = np.flatnonzero(pc == code)
        s = sel[rows]
        out[int(code)] = {
            "unit_hours": int(s.sum()),
            "floor_gwh": _r(float(mg[rows][s].sum()) / 1e3, 3),
        }
    return out


def d2_bridge_twh(bundle: Path, year: int) -> dict:
    f = bundle / "legitimacy_diagnostics.json"
    if not f.exists():
        return {}
    ld = json.loads(f.read_text())
    rows = ld.get("diagnostics", {}).get("D2", {}).get("rows", [])
    return {
        r["class"]: float(r["forced_twh"])
        for r in rows
        if int(r.get("year", -1)) == year
        and r.get("mechanism") == "nyiso_gas_commitment_bridge"
    }


def d4_block(bundle: Path, year: int) -> dict:
    f = bundle / "legitimacy_diagnostics.json"
    if not f.exists():
        return {}
    ld = json.loads(f.read_text())
    diag = ld.get("diagnostics") or {}
    d2, d4 = diag.get("D2") or {}, diag.get("D4") or {}
    return {
        "D2_passed": d2.get("passed"),
        "D2_failures": d2.get("failures") or [],
        "D2_forced_share_of_class": {
            f"{r.get('class')}|{r.get('mechanism')}": r.get("share_of_class")
            for r in (d2.get("rows") or [])
            if isinstance(r, dict) and str(r.get("year")) == str(year)
        },
        "D4_failures_this_year": [
            f for f in (d4.get("failures") or []) if str(f).startswith(str(year))
        ],
        "D4_guard_notes": [
            n
            for n in (d4.get("notes") or [])
            if "vintage guard" in str(n) and str(n).startswith(str(year))
        ],
        "cc_bridge_unit_conduct_rows": [
            r
            for r in (d4.get("rows") or [])
            if isinstance(r, dict)
            and str(r.get("year")) == str(year)
            and r.get("check") == "unit-conduct"
            and "nyiso_gas_commitment_bridge" in str(r.get("floor", ""))
        ],
    }


def parse_census(spec: str | None) -> dict:
    out = {}
    for part in (spec or "").split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = int(v)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=("a1", "a3"), required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--screen", type=Path, required=True)
    ap.add_argument(
        "--census", default=None, help="runs_dropped=N,units=M from the solve log"
    )
    ap.add_argument(
        "--log", type=Path, default=None, help="solve log to scrape the census from"
    )
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    Y, S, ARM = a.year, a.screen, a.arm
    out = a.out or ROOT / f"results/calibration/_nyiso200_screen_gates_{ARM}_{Y}.json"

    census = parse_census(a.census)
    if a.log is not None and a.log.exists():
        legs = {}
        for m in re.finditer(
            r"run screen, leg (\S+): (\d+) P0 runs detected, (\d+) dropped as phantom .* covering (\d+) P0 online hours at (\d+) unit",
            a.log.read_text(),
        ):
            legs[m.group(1)] = {
                "runs_detected": int(m.group(2)),
                "runs_dropped": int(m.group(3)),
                "dropped_hours": int(m.group(4)),
                "units_with_drops": int(m.group(5)),
            }
        census["legs"] = legs
        census["runs_dropped"] = sum(v["runs_dropped"] for v in legs.values())
        census["units"] = sum(v["units_with_drops"] for v in legs.values())
        census["armed_log_line_present"] = bool(legs)

    run = decode_run_js(
        (ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    )
    ypay = run["years"][str(Y)]
    bench = json.load(
        gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{Y}.json.gz")
    )["bench"]
    ph = json.load(PHASE0.open())["keeper_bridge_footprint"][str(Y)]

    ek, es = class_energy_twh(KEEPER, Y), class_energy_twh(S, Y)
    classes = sorted(set(ek.index) | set(es.index))
    energy = {
        k: {
            "keeper": _r(ek.get(k, 0.0), 3),
            "screen": _r(es.get(k, 0.0), 3),
            "delta": _r(float(es.get(k, 0.0)) - float(ek.get(k, 0.0)), 3),
        }
        for k in classes
    }
    gates: dict = {}

    # ---- bridge volume (both arms report; A1 gates on it) -------------------
    d2k, d2s = d2_bridge_twh(KEEPER, Y), d2_bridge_twh(S, Y)
    vol_k = sum(d2k.values())
    vol_s = sum(d2s.values())
    bound = float(ph["repair_reachability_bound_twh"])
    bridge = {
        "keeper_forced_twh_by_class": d2k,
        "screen_forced_twh_by_class": d2s,
        "keeper_total_twh": _r(vol_k),
        "screen_total_twh": _r(vol_s),
        "delta_twh": _r(vol_s - vol_k),
        "pre_solve_bound_twh": bound,
    }
    fk, fs = bridge_floor_hours_by_plant(KEEPER, Y), bridge_floor_hours_by_plant(S, Y)
    plants = sorted(set(fk) | set(fs))
    per_plant = {
        int(c): {
            "keeper": fk.get(c, {"unit_hours": 0, "floor_gwh": 0.0}),
            "screen": fs.get(c, {"unit_hours": 0, "floor_gwh": 0.0}),
        }
        for c in plants
    }
    bridge["floored_unit_hours_by_plant"] = per_plant
    bridge["keeper_floors_available"] = bool(fk)

    if ARM == "a1":
        gates["S1_direction_bound"] = {
            "bridge_volume_delta_twh": bridge["delta_twh"],
            "rises": bool(vol_s > vol_k + 1e-6),
            "fall_inside_bound": bool(vol_k - vol_s <= bound + 1e-6),
            "STOP": bool(vol_s > vol_k + 1e-6) or not (vol_k - vol_s <= bound + 1e-6),
            "note": "the screen can only remove anchors: volume must not rise, fall <= keeper's own bridge volume",
        }
        moved = [
            c
            for c, v in per_plant.items()
            if v["keeper"]["unit_hours"] != v["screen"]["unit_hours"]
        ]
        gates["S2_census_identity"] = {
            "census": census,
            "plants_with_floor_change": moved,
            "n_plants_with_floor_change": len(moved),
            "units_with_drops_from_census": census.get("units"),
            "STOP": bool(census.get("runs_dropped", 0) == 0 and moved and fk),
            "note": (
                "floor moves only where a run was dropped; with keeper floors "
                "unavailable (slim bundle) the plant-grain identity is reported, not gated"
                if not fk
                else "STOP if floors moved while the census dropped zero runs"
            ),
        }
        non_gas = {
            k: v["delta"]
            for k, v in energy.items()
            if k not in GAS_FAMILY and k != "import" and abs(v["delta"]) > 0.005
        }
        gates["S3_confinement"] = {
            "gas_family_total_delta_twh": _r(
                sum(energy.get(k, {}).get("delta", 0.0) for k in GAS_FAMILY), 3
            ),
            "import_delta_twh": energy.get("import", {}).get("delta", 0.0),
            "non_gas_non_import_deltas_twh": non_gas,
            "STOP": bool(
                max([abs(v) for v in non_gas.values()], default=0.0) > NON_GAS_TOL_TWH
            ),
        }
    else:
        d_ct = energy.get("CT_PEAKER", {}).get("delta", 0.0)
        ct_bound = float(
            json.load(CT_PHASE0.open())["years"][str(Y)][
                "D4_footprint_no_meter_no_residual"
            ]["newly_itm_twh"]
        )
        gates["S1_direction"] = {
            "ct_peaker_delta_twh": d_ct,
            "pre_solve_reachability_bound_twh": ct_bound,
            "rises": bool(d_ct > 0),
            "inside_bound": bool(0 < d_ct <= ct_bound + 1e-9),
            "STOP": not (0 < d_ct <= ct_bound + 1e-9),
        }
        gas_delta = sum(energy.get(k, {}).get("delta", 0.0) for k in GAS_FAMILY)
        nongas = {
            k: v["delta"]
            for k, v in energy.items()
            if k not in GAS_FAMILY and abs(v["delta"]) > 0.005
        }
        gates["S2_confinement"] = {
            "gas_family_total_delta_twh": _r(gas_delta, 3),
            "non_gas_class_deltas_twh": nongas,
            "STOP": bool(abs(gas_delta) > abs(d_ct)),
        }
        named = {
            str(c): per_plant.get(
                c, {"keeper": {"unit_hours": 0}, "screen": {"unit_hours": 0}}
            )
            for c in NAMED_PLANTS
        }
        gates["S4_named_plants"] = {
            "bridge_floored_unit_hours": named,
            "STOP": any(
                v["screen"]["unit_hours"] > v["keeper"]["unit_hours"]
                for v in named.values()
            ),
            "note": "the defect read directly: any bridge floor at 7314 / 50978 above the keeper's (0) is a STOP",
        }

    # ---- load-bearing companions (both arms) -------------------------------
    ypay2 = json.loads(json.dumps(ypay))
    for k, v in energy.items():
        if k in ypay2.get("gmModel", {}):
            ypay2["gmModel"][k] = float(ypay2["gmModel"][k]) + v["delta"]
    zk, zs = zone_mean_prices(KEEPER, Y), zone_mean_prices(S, Y)
    for z, e in (ypay2.get("lmp") or {}).items():
        if z in zs and z in zk and e.get("p") is not None:
            e["p"] = float(e["p"]) + (zs[z] - zk[z])
    c1_k = {r["key"]: r for r in cv.score_fuelmix(Y, ypay, bench, "NYISO")}
    c1_s = {r["key"]: r for r in cv.score_fuelmix(Y, ypay2, bench, "NYISO")}
    fld = ("status", "model", "actual", "share_pp", "magnitude")
    c1 = {
        k: {
            "keeper": {f: c1_k[k].get(f) for f in fld},
            "screen": {f: c1_s[k].get(f) for f in fld},
        }
        for k in c1_k
        if k in c1_s
    }
    bad = [k for k in c1 if c1_k[k]["status"] == "PASS" and c1_s[k]["status"] != "PASS"]
    pm_k, pm_s = (
        cv.score_price_mean(Y, ypay, bench),
        cv.score_price_mean(Y, ypay2, bench),
    )
    ps_k, ps_s = (
        cv.score_price_shape(Y, ypay, bench),
        cv.score_price_shape(Y, ypay2, bench),
    )
    sysk = pd.read_parquet(KEEPER / "hourly" / f"system_{Y}.parquet")
    syss = pd.read_parquet(S / "hourly" / f"system_{Y}.parquet")

    def _px(df):
        p = df.pivot(index="hour", columns="zone", values="price")
        m = p.mean(axis=1).to_numpy()
        return {
            "mean": _r(np.mean(m), 3),
            "p95": _r(np.percentile(m, 95), 2),
            "hours_gt_300": int((m > 300).sum()),
        }

    c8k, c8s = d4_block(KEEPER, Y), d4_block(S, Y)
    new_d4 = len(c8s.get("D4_failures_this_year", [])) > len(
        c8k.get("D4_failures_this_year", [])
    )
    new_d2 = len(c8s.get("D2_failures", [])) > len(c8k.get("D2_failures", []))
    gates["S_companions"] = {
        "C1_cells": c1,
        "C1_pass_to_fail_flips": bad,
        "C3a_price_mean": {
            "keeper": {
                k: pm_k.get(k) for k in ("status", "model", "actual", "magnitude")
            },
            "screen": {
                k: pm_s.get(k) for k in ("status", "model", "actual", "magnitude")
            },
        },
        "C3b_price_shape": {
            "keeper": {k: ps_k.get(k) for k in ("status", "model", "magnitude")},
            "screen": {k: ps_s.get(k) for k in ("status", "model", "magnitude")},
        },
        "system_price": {"keeper": _px(sysk), "screen": _px(syss)},
        "C8_D4": {
            "keeper": c8k,
            "screen": c8s,
            "new_D4_failure": new_d4,
            "new_D2_failure": new_d2,
        },
        "STOP": bool(
            bad
            or (pm_k.get("status") == "PASS" and pm_s.get("status") != "PASS")
            or (ps_k.get("status") == "PASS" and ps_s.get("status") != "PASS")
            or new_d4
            or new_d2
        ),
    }

    res = {
        "session": "nyiso-200",
        "arm": ARM,
        "year": Y,
        "keeper": KEEPER_ID,
        "screen_bundle": str(S),
        "prereg": "results/calibration/PREREG-nyiso200-bridge-run-screen.md",
        "class_energy_twh": energy,
        "bridge": bridge,
        "gates": gates,
        "VERDICT": "STOP" if any(g.get("STOP") for g in gates.values()) else "CLEAR",
    }
    out.write_text(json.dumps(res, indent=2))
    print(f"wrote {out}  VERDICT={res['VERDICT']}")
    for k, g in gates.items():
        print(f"  {k}: {'STOP' if g.get('STOP') else 'pass'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
