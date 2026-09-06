"""nyiso-202 SCREEN GATES — the pre-registered gates of
``PREREG-nyiso202-bridge-startup-aware-2025-screen.md`` §5, executed as
written, for the arm ``nyiso_gas_bridge_startup_aware`` **ALONE** on 2025.

This is nyiso-201's ``nyiso201_screen_gates.py`` reused **AS IS** — its gate
(a), gate (b), the load-bearing companions and G-ENGAGE are byte-identical,
because those gates are arm-agnostic and they are the CORRECTED constructions
nyiso-201 established (see that file's header for the two corrections and why
each was needed).

**The ONE change is S-1, which had to be re-pointed, and the change is a
narrowing, not a loosening.** nyiso-201's S-1 reads *"``CT_PEAKER`` must RISE,
inside the CT band's own newly-in-the-money bound"* — the **CT arm's** own
arithmetic. This session's arm carries no CT band, so that gate has no subject
here. A1's own arithmetic is the opposite sign: the run screen can only
**REMOVE** bridge anchors, so its direction test is **"the bridge's D-2 forced
volume must NOT RISE"** and its bound is the keeper's own 2025 bridge volume,
**0.5701 TWh** (``_nyiso200_bridge_phase0.json``,
``keeper_bridge_footprint.2025.repair_reachability_bound_twh``). That is
nyiso-200's own A1 gate (``nyiso200_screen_gates.py::S1_direction_bound``),
reused verbatim, together with its A1 companions ``S2_census_identity``
(reported at plant grain, not gated — the committed keeper bundle is slim) and
``S3_confinement`` (non-gas, non-import class deltas within the lane's own
registered 0.05 TWh tolerance). Every bound is meter-free, residual-free and
fixed before the solve.

**2025 is scored differently from 2023 and the PREREG says so ex ante:** the
preliminary EIA-923 vintage SKIPS every C1 class cell and the C2 gas family, so
no volume criterion is gateable in 2025. The class deltas are reported at full
magnitude as structural evidence and the gate cannot fire on them; C3a and C3b
are the load-bearing criteria that bind, and a C3a PASS -> FAIL is a STOP.

The screen is a rule-29 throwaway probe: it may KILL the arm and may never
promote it, and no gate reads the target residual.

Writes ``results/calibration/_nyiso202_screen_gates_<arm>_<year>.json``.

Usage::

    python scripts/probes/nyiso202_screen_gates.py --arm a1 --year 2025 \
        --screen results/calibration/nyiso202_screen_a1_2025 \
        --log <solve log>
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
# MATERIALITY for gate (a), declared in the PREREG before the solve and used
# on BOTH its legs (aggregate rise and worst single-plant rise). It is the
# lane's OWN registered confinement tolerance -- nyiso200_screen_gates.py
# ``NON_GAS_TOL_TWH`` -- not a number invented for this screen and not one
# chosen against a result. Rationale, PREREG 5(a): the gate's subject is
# MATERIAL forcing at plants the meter says are dark; a sub-materiality
# reshuffle of a trivial row (the keeper's 2025 dark total is 0.0010 TWh at one
# 17-hour row) is reported at full magnitude and does not kill an arm, while a
# plant becoming dark-median while carrying real forced energy fires it hard.
TOL_TWH = 0.05


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
    """Per plant: bridge-floored unit-hours and floor GWh from floors/<Y>_P1.npz."""
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


def d4_rows(bundle: Path, year: int) -> list[dict]:
    f = bundle / "legitimacy_diagnostics.json"
    if not f.exists():
        return []
    ld = json.loads(f.read_text())
    d4 = (ld.get("diagnostics") or {}).get("D4") or {}
    return [
        r
        for r in (d4.get("rows") or [])
        if isinstance(r, dict)
        and str(r.get("year")) == str(year)
        and r.get("check") == "unit-conduct"
    ]


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
    }


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


def dark_plant_forced(rows: list[dict]) -> dict[str, float]:
    """Per plant: total D-4 unit-conduct forced TWh, for DARK-METER plants only.

    Dark = the plant's measured median output over the hours the floor actually
    binds for it is 0.0 MW — the D-4 rider's own definition of "the meter says
    it is offline in at least half the hours we force it on". Summed over EVERY
    mechanism at that plant, which is what makes the measure like-for-like when
    a conviction MIGRATES between two composed floors (nyiso-200 §5.1).
    """
    dark = {
        str(r.get("plant"))
        for r in rows
        if r.get("plant") and float(r.get("measured_median_mw") or 0.0) == 0.0
    }
    out: dict[str, float] = {}
    for r in rows:
        c = str(r.get("plant"))
        if c in dark:
            out[c] = out.get(c, 0.0) + float(r.get("floored_twh") or 0.0)
    return {k: _r(v) for k, v in out.items()}


def parse_log(log: Path | None) -> dict:
    """Scrape the detector's own census lines: per-leg and per-plant."""
    out: dict = {"armed_log_line_present": False}
    if log is None or not log.exists():
        return out
    txt = log.read_text()
    legs = {}
    for m in re.finditer(
        r"run screen, leg (\S+): (\d+) P0 runs detected, (\d+) dropped as phantom"
        r" .* covering (\d+) P0 online hours at (\d+) unit",
        txt,
    ):
        legs[m.group(1)] = {
            "runs_detected": int(m.group(2)),
            "runs_dropped": int(m.group(3)),
            "dropped_hours": int(m.group(4)),
            "units_with_drops": int(m.group(5)),
        }
    out["legs"] = legs
    out["runs_dropped"] = sum(v["runs_dropped"] for v in legs.values())
    out["runs_detected"] = sum(v["runs_detected"] for v in legs.values())
    out["armed_log_line_present"] = bool(legs)
    per_plant: dict[int, dict] = {}
    for m in re.finditer(r"run screen per-plant census: (\S+)", txt):
        for tok in m.group(1).split(";"):
            if not tok:
                continue
            code, rest = tok.split(":", 1)
            d, k, dr, dh = (int(x) for x in rest.split("/"))
            e = per_plant.setdefault(
                int(code),
                {"detected": 0, "kept": 0, "dropped": 0, "dropped_hours": 0},
            )
            e["detected"] += d
            e["kept"] += k
            e["dropped"] += dr
            e["dropped_hours"] += dh
    out["per_plant"] = per_plant
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="a1")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--screen", type=Path, required=True)
    ap.add_argument("--log", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    Y, S, ARM = a.year, a.screen, a.arm
    out = a.out or ROOT / f"results/calibration/_nyiso202_screen_gates_{ARM}_{Y}.json"

    census = parse_log(a.log)
    run = decode_run_js(
        (ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    )
    ypay = run["years"][str(Y)]
    bench = json.load(
        gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{Y}.json.gz")
    )["bench"]

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

    # ---- bridge volume / per-plant floors (reported) -----------------------
    d2k, d2s = d2_bridge_twh(KEEPER, Y), d2_bridge_twh(S, Y)
    fk, fs = bridge_floor_hours_by_plant(KEEPER, Y), bridge_floor_hours_by_plant(S, Y)
    bridge = {
        "keeper_forced_twh_by_class": d2k,
        "screen_forced_twh_by_class": d2s,
        "keeper_total_twh": _r(sum(d2k.values())),
        "screen_total_twh": _r(sum(d2s.values())),
        "delta_twh": _r(sum(d2s.values()) - sum(d2k.values())),
        "pre_solve_bound_twh": float(
            json.load(PHASE0.open())["keeper_bridge_footprint"][str(Y)][
                "repair_reachability_bound_twh"
            ]
        ),
        "screen_floored_unit_hours_by_plant": fs,
        "keeper_floors_available": bool(fk),
        "keeper_floors_note": (
            "the committed keeper bundle is SLIM (no floors/ sidecar): the "
            "keeper's per-plant bridge footprint is read from its committed "
            "D-4 unit-conduct rows instead, which is the same quantity in TWh"
        ),
        "keeper_bridge_unit_conduct_twh_by_plant": {
            str(r.get("plant")): _r(float(r.get("floored_twh") or 0.0))
            for r in d4_rows(KEEPER, Y)
            if "nyiso_gas_commitment_bridge" in str(r.get("floor", ""))
        },
    }

    # ---- S-1 DIRECTION AND BOUND, RE-POINTED FOR A1 (meter-free) -----------
    # nyiso-201's S-1 is the CT arm's gate: "CT_PEAKER rises, inside the CT
    # band's newly-in-the-money bound". For A1 -- the bridge run screen ALONE
    # -- that is the wrong object: this arm has no CT band and it can only
    # REMOVE bridge anchors, so its own arithmetic bound is the keeper's own
    # 2025 bridge volume (0.5701 TWh, _nyiso200_bridge_phase0.json) and its
    # direction test is "the bridge's D-2 volume must NOT RISE". This is
    # nyiso-200's own A1 gate (``S1_direction_bound``), reused verbatim; it is
    # meter-free, residual-free and pre-solve, exactly as rule 29 requires.
    vol_k, vol_s = sum(d2k.values()), sum(d2s.values())
    bound = bridge["pre_solve_bound_twh"]
    gates["S1_direction_bound"] = {
        "bridge_volume_delta_twh": bridge["delta_twh"],
        "keeper_total_twh": _r(vol_k),
        "screen_total_twh": _r(vol_s),
        "rises": bool(vol_s > vol_k + 1e-6),
        "fall_inside_bound": bool(vol_k - vol_s <= bound + 1e-6),
        "pre_solve_bound_twh": bound,
        "STOP": bool(vol_s > vol_k + 1e-6) or not (vol_k - vol_s <= bound + 1e-6),
        "note": (
            "the screen can only remove anchors: bridge volume must not rise, "
            "and its fall must sit inside the keeper's own bridge volume"
        ),
    }

    # ---- S-2 census identity (reported at plant grain) ---------------------
    moved = sorted(fs)
    gates["S2_census_identity"] = {
        "census": {k: v for k, v in census.items() if k != "per_plant"},
        "screen_plants_with_bridge_floor": moved,
        "n_screen_plants_with_bridge_floor": len(moved),
        "keeper_floors_available": bool(fk),
        "STOP": bool(census.get("runs_dropped", 0) == 0 and moved and fk),
        "note": (
            "floor moves only where a run was dropped; the committed keeper "
            "bundle is SLIM (no floors/ sidecar), so the plant-grain identity "
            "is REPORTED, not gated -- gate (b) carries the falsifiable "
            "per-plant leg via the F-1 census"
        ),
    }

    # ---- S-3 confinement ---------------------------------------------------
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
        "non_gas_tolerance_twh": TOL_TWH,
        "STOP": bool(max([abs(v) for v in non_gas.values()], default=0.0) > TOL_TWH),
    }
    # ---- GATE (a): C8 / D-4 forced energy at DARK-METER plants -------------
    rk, rs = d4_rows(KEEPER, Y), d4_rows(S, Y)
    dk, ds = dark_plant_forced(rk), dark_plant_forced(rs)
    plants = sorted(set(dk) | set(ds))
    per_plant_dark = {
        c: {
            "keeper_twh": dk.get(c, 0.0),
            "screen_twh": ds.get(c, 0.0),
            "delta_twh": _r(ds.get(c, 0.0) - dk.get(c, 0.0)),
        }
        for c in plants
    }
    tot_k, tot_s = sum(dk.values()), sum(ds.values())
    worst = max((v["delta_twh"] for v in per_plant_dark.values()), default=0.0)
    c8k, c8s = d4_block(KEEPER, Y), d4_block(S, Y)
    gates["A_dark_plant_forced_energy"] = {
        "construction": (
            "nyiso-200 FINDING 7(a): total D-4 unit-conduct floored_twh over "
            "EVERY mechanism at plants whose measured median over their own "
            "binding hours is 0.0 MW. NOT a failure-row count."
        ),
        "keeper_total_twh": _r(tot_k),
        "screen_total_twh": _r(tot_s),
        "delta_twh": _r(tot_s - tot_k),
        "per_plant": per_plant_dark,
        "worst_single_plant_rise_twh": _r(worst),
        "single_plant_tolerance_twh": TOL_TWH,
        "D2_new_failure": len(c8s.get("D2_failures", []))
        > len(c8k.get("D2_failures", [])),
        "D4_failure_rows_reported_not_gated": {
            "keeper": c8k.get("D4_failures_this_year", []),
            "screen": c8s.get("D4_failures_this_year", []),
        },
        "D4_guard_notes": {
            "keeper": c8k.get("D4_guard_notes", []),
            "screen": c8s.get("D4_guard_notes", []),
        },
        "aggregate_tolerance_twh": TOL_TWH,
        "STOP": bool(
            (tot_s - tot_k > TOL_TWH)
            or (worst > TOL_TWH)
            or (len(c8s.get("D2_failures", [])) > len(c8k.get("D2_failures", [])))
        ),
    }

    # ---- GATE (b): named plants 7314 / 50978 -------------------------------
    named = {}
    for c in NAMED_PLANTS:
        f = fs.get(c, {"unit_hours": 0, "floor_gwh": 0.0})
        cen = (census.get("per_plant") or {}).get(c)
        conv = [
            r
            for r in rs
            if str(r.get("plant")) == str(c) and str(r.get("verdict")).upper() == "FAIL"
        ]
        conv_k = [
            r
            for r in rk
            if str(r.get("plant")) == str(c) and str(r.get("verdict")).upper() == "FAIL"
        ]
        anchored_on_dropped = bool(f["unit_hours"] > 0 and cen and cen["kept"] == 0)
        named[str(c)] = {
            "screen_bridge_floored_unit_hours": f["unit_hours"],
            "screen_bridge_floor_gwh": f["floor_gwh"],
            "run_census": cen,
            "floor_with_zero_kept_runs": anchored_on_dropped,
            "new_D4_conviction": len(conv) > len(conv_k),
            "D4_convictions_screen": [
                {
                    k: r.get(k)
                    for k in (
                        "floor",
                        "floored_twh",
                        "binding_hours",
                        "measured_median_mw",
                        "measured_zero_share",
                    )
                }
                for r in conv
            ],
        }
    gates["B_named_plants"] = {
        "construction": (
            "nyiso-200 FINDING 7(b): a bridge floor ANCHORED ON A DROPPED RUN "
            "(zero by construction of the screen; falsified by a plant with "
            "floor and zero kept runs) OR a new D-4 conviction at the span "
            "guard. A floor on a run that repaid its start is the mechanism "
            "working, not the defect, and is REPORTED at full magnitude."
        ),
        "plants": named,
        "census_available": bool(census.get("per_plant")),
        "STOP": bool(
            any(
                v["floor_with_zero_kept_runs"] or v["new_D4_conviction"]
                for v in named.values()
            )
        ),
    }

    # ---- load-bearing companions ------------------------------------------
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
    c2_k = {r["key"]: r for r in cv.score_sysvol(Y, ypay, bench, "NYISO")}
    c2_s = {r["key"]: r for r in cv.score_sysvol(Y, ypay2, bench, "NYISO")}
    bad2 = [
        k
        for k in c2_k
        if k in c2_s and c2_k[k]["status"] == "PASS" and c2_s[k]["status"] != "PASS"
    ]
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

    gates["C_companions"] = {
        "C1_cells": c1,
        "C1_pass_to_fail_flips": bad,
        "C1_all_skipped_this_year": all(
            v["keeper"]["status"] == "SKIPPED" for v in c1.values()
        ),
        "C2_cells": {
            k: {
                "keeper": c2_k[k].get("status"),
                "screen": c2_s.get(k, {}).get("status"),
                "keeper_magnitude": c2_k[k].get("magnitude"),
                "screen_magnitude": c2_s.get(k, {}).get("magnitude"),
            }
            for k in c2_k
        },
        "C2_pass_to_fail_flips": bad2,
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
        "STOP": bool(
            bad
            or bad2
            or (pm_k.get("status") == "PASS" and pm_s.get("status") != "PASS")
            or (ps_k.get("status") == "PASS" and ps_s.get("status") != "PASS")
        ),
    }

    # ---- G-ENGAGE: the arm must have ARMED (fail-loud) ---------------------
    gates["G_engage"] = {
        "census": {k: v for k, v in census.items() if k != "per_plant"},
        "n_plants_in_per_plant_census": len(census.get("per_plant") or {}),
        "STOP": bool(a.log is not None and not census.get("armed_log_line_present")),
        "note": "a screen log with no run-screen census line did not arm the leg",
    }

    res = {
        "session": "nyiso-202",
        "arm": ARM,
        "year": Y,
        "keeper": KEEPER_ID,
        "screen_bundle": str(S),
        "prereg": "results/calibration/PREREG-nyiso202-bridge-startup-aware-2025-screen.md",
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
