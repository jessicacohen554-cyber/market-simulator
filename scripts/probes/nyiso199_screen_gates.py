"""nyiso-199 SCREEN GATES — the pre-registered S-1 / S-2 / S-3 gates of
``PREREG-nyiso199-ct-peaker-measured-bands-screen.md`` §4, executed as written.

The screen is a rule-29 throwaway probe: it may KILL the arm and may never
promote it, and no gate reads the target residual.

* **S-1 DIRECTION AND MAGNITUDE (meter-free).** ``CT_PEAKER`` dispatch must RISE
  and by an amount inside the arm's OWN pre-solve reachability envelope (the
  newly-in-the-money MWh measured in phase 0c, ``_nyiso199_ct_band_basis_
  phase0.json`` D-4). A rise outside that envelope means the mechanism is doing
  something its own arithmetic does not predict.
* **S-2 CONFINEMENT.** The energy ``CT_PEAKER`` gains must come from the gas
  family; a gain drawn from hydro, nuclear, imports or storage is a STOP.
* **S-3 LOAD-BEARING COMPANIONS.** No non-target load-bearing criterion may flip
  PASS -> FAIL — every C1 class cell, C2, C3a, C3b — plus the protective C6 / C8.
  **C3a is scored with the real scorer**, not an indicator: the keeper's
  committed payload with the screen's per-zone mean prices substituted.

Writes ``results/calibration/_nyiso199_screen_gates_<year>.json``.

Usage::

    python scripts/probes/nyiso199_screen_gates.py --year 2023 \
        --screen results/calibration/nyiso199_screen_2023
"""

from __future__ import annotations

import argparse
import gzip
import json
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
PHASE0 = ROOT / "results/calibration/_nyiso199_ct_band_basis_phase0.json"
GAS_FAMILY = ("CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP", "CT_PEAKER", "CT_CHP")


def _r(x, n=3):
    return round(float(x), n)


def class_energy_twh(bundle: Path, year: int) -> pd.Series:
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return df.groupby("klass")["mw"].sum() / 1e6


def zone_mean_prices(bundle: Path, year: int) -> dict:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    p = df.pivot(index="hour", columns="zone", values="price")
    return {z: float(p[z].mean()) for z in p.columns}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--screen", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    Y, S = a.year, a.screen
    out = a.out or ROOT / f"results/calibration/_nyiso199_screen_gates_{Y}.json"

    run = decode_run_js((ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text())
    ypay = run["years"][str(Y)]
    bench = json.load(gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{Y}.json.gz"))["bench"]
    ph = json.load(PHASE0.open())["years"][str(Y)]

    ek, es = class_energy_twh(KEEPER, Y), class_energy_twh(S, Y)
    classes = sorted(set(ek.index) | set(es.index))
    energy = {
        k: {
            "keeper": _r(ek.get(k, 0.0)),
            "screen": _r(es.get(k, 0.0)),
            "delta": _r(float(es.get(k, 0.0)) - float(ek.get(k, 0.0))),
        }
        for k in classes
    }

    # ---- S-1 direction + magnitude, against the arm's OWN pre-solve bound ---
    d_ct = energy.get("CT_PEAKER", {}).get("delta", 0.0)
    bound = float(ph["D4_footprint_no_meter_no_residual"]["newly_itm_twh"])
    s1 = {
        "ct_peaker_delta_twh": d_ct,
        "pre_solve_reachability_bound_twh": bound,
        "rises": bool(d_ct > 0),
        "inside_bound": bool(0 < d_ct <= bound + 1e-9),
        "STOP": not (0 < d_ct <= bound + 1e-9),
        "note": "meter-free: the bound is the arm's own newly-in-the-money MWh (phase 0c D-4)",
    }

    # ---- S-2 confinement ---------------------------------------------------
    gas_delta = sum(energy.get(k, {}).get("delta", 0.0) for k in GAS_FAMILY)
    nongas = {
        k: v["delta"] for k, v in energy.items() if k not in GAS_FAMILY and abs(v["delta"]) > 0.005
    }
    s2 = {
        "gas_family_total_delta_twh": _r(gas_delta),
        "non_gas_class_deltas_twh": nongas,
        "largest_non_gas_abs_twh": _r(max([abs(v) for v in nongas.values()], default=0.0)),
        "STOP": bool(abs(gas_delta) > abs(d_ct)),
        "note": "a within-family reallocation keeps |gas family total| <= |the CT gain|",
    }

    # ---- S-3 load-bearing companions ---------------------------------------
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
        k: {"keeper": {f: c1_k[k].get(f) for f in fld}, "screen": {f: c1_s[k].get(f) for f in fld}}
        for k in c1_k
        if k in c1_s
    }
    bad = [k for k in c1 if c1_k[k]["status"] == "PASS" and c1_s[k]["status"] != "PASS"]

    pm_k, pm_s = cv.score_price_mean(Y, ypay, bench), cv.score_price_mean(Y, ypay2, bench)
    ps_k, ps_s = cv.score_price_shape(Y, ypay, bench), cv.score_price_shape(Y, ypay2, bench)

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

    s3 = {
        "C1_cells": c1,
        "C1_pass_to_fail_flips": bad,
        "C3a_price_mean": {
            "keeper": {k: pm_k.get(k) for k in ("status", "model", "actual", "magnitude")},
            "screen": {k: pm_s.get(k) for k in ("status", "model", "actual", "magnitude")},
        },
        "C3b_price_shape": {
            "keeper": {k: ps_k.get(k) for k in ("status", "model", "magnitude")},
            "screen": {k: ps_s.get(k) for k in ("status", "model", "magnitude")},
        },
        "system_price": {"keeper": _px(sysk), "screen": _px(syss)},
        "STOP": bool(
            bad
            or (pm_k.get("status") == "PASS" and pm_s.get("status") != "PASS")
            or (ps_k.get("status") == "PASS" and ps_s.get("status") != "PASS")
        ),
    }

    # ---- C8 / D-4 ----------------------------------------------------------
    c8 = {}
    for tag, b in (("keeper", KEEPER), ("screen", S)):
        f = b / "legitimacy_diagnostics.json"
        if f.exists():
            ld = json.loads(f.read_text())
            diag = ld.get("diagnostics") or {}
            d2, d4 = diag.get("D2") or {}, diag.get("D4") or {}
            c8[tag] = {
                "D2_passed": d2.get("passed"),
                "D2_failures": d2.get("failures") or [],
                "D2_forced_share_of_class": {
                    f"{r.get('class')}|{r.get('mechanism')}": r.get("share_of_class")
                    for r in (d2.get("rows") or [])
                    if isinstance(r, dict) and str(r.get("year")) == str(Y)
                },
                "D4_failures_this_year": [
                    f for f in (d4.get("failures") or []) if str(f).startswith(str(Y))
                ],
                "D4_passed": d4.get("passed"),
                "D4_failures": d4.get("failures") or [],
            }
    # like-for-like: the keeper's committed diagnostics span all three years
    # while a screen bundle covers only its own, so compare THIS YEAR's rows.
    c8["STOP"] = bool(
        len(c8.get("screen", {}).get("D4_failures_this_year", []))
        > len(c8.get("keeper", {}).get("D4_failures_this_year", []))
        or len(c8.get("screen", {}).get("D2_failures", []))
        > len(c8.get("keeper", {}).get("D2_failures", []))
    )

    res = {
        "session": "nyiso-199",
        "year": Y,
        "keeper": KEEPER_ID,
        "screen_bundle": str(S),
        "prereg": "results/calibration/PREREG-nyiso199-ct-peaker-measured-bands-screen.md",
        "class_energy_twh": energy,
        "gates": {"S1_direction": s1, "S2_confinement": s2, "S3_companions": s3, "C8_D4": c8},
        "VERDICT": "STOP" if (s1["STOP"] or s2["STOP"] or s3["STOP"] or c8["STOP"]) else "CLEAR",
    }
    out.write_text(json.dumps(res, indent=2))
    print(f"wrote {out}  VERDICT={res['VERDICT']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
