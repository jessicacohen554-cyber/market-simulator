"""nyiso-198 SCREEN GATES — evaluate the 2024 screen bundle of
``cc_duct_peaking_row_scoped`` against the keeper's committed 2024
(rule 29 ``[R-SCREEN]``; control = form 4, no control solve).

Gates are the PREREG's (``PREREG-nyiso198-duct-peaking-row-scope-screen.md``
§6 as amended by Addendum A §A.3), structural and STOP-only:

* **F-1' / F-2'** — carried from the zero-LP rebuild checks
  (``_nyiso198_rebuild_checks_2024.json``) and re-asserted as the Set-A / Set-B
  prediction: every override-cohort plant's peak band unchanged, every other CC
  plant's peak band on the builder's own ratio; ``pmax`` conserved except where
  a released tranche falls below the builder's minimum band size, reported.
  Plus the G-DELTA assertion against the keeper's ``scenario_config``.
* **S-3 direction and magnitude bound (meter-free)** — Cricket Valley's 2024
  dispatch RISES against the keeper's committed 2024, and the rise is bounded by
  the mechanism's own arithmetic (that plant's footprint capacity-hours,
  622.1 GWh); fleet combined-cycle energy likewise rises within the fleet
  footprint bound (3,047.0 GWh). Reported, never gated: every moved plant's
  energy against the keeper payload and against its meter.
* **S-4 load-bearing companions** — every C1 class cell through
  ``calibration_verdict.score_fuelmix`` on the keeper's committed payload with
  the screen's P1 class-energy deltas applied (the nyiso-195/196 construction),
  plus the same-weights price companions. STOP on any load-bearing PASS -> FAIL
  flip. Unlike nyiso-196 this session does NOT exempt ``CC_REGULAR``: the arm is
  not offered as a fix for that cell, so breaking it is a real cost and the
  PREREG gates it.
* **C8 / D-4** — the screen's regenerated ``legitimacy_diagnostics.json``
  forced shares and D-4 failures vs the keeper's.

Writes ``results/calibration/_nyiso198_screen_gates.json``.

Usage: ``python scripts/probes/nyiso198_screen_gates.py [results/calibration/nyiso198_screen_2024]``
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))
import calibration_verdict as cv  # noqa: E402
from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402

KEEPER_ID = "2026-09-06-nyiso-196-extract-basis"
KEEPER = ROOT / "results/calibration/nyiso196_extract_basis"
YEAR = 2024
FLAG = "cc_duct_peaking_row_scoped"
CV = 57185
T = 8760
GAS = ("CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP", "CT_CHP", "CT_PEAKER")
CC = ("CC_REGULAR", "CC_CHP")
#: PREREG §6 / Addendum A §A.4 — the mechanism's own arithmetic bounds.
CV_FOOTPRINT_GWH = 622.1
FLEET_FOOTPRINT_GWH = 3047.0
#: Load-bearing C1 cells: every free (scored) class cell. C3c is not here.
LOAD_BEARING_C1_PREFIX = "C1"


def _dec(b64: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def _ann(entry: dict, key_ann: str) -> float:
    v = entry.get(key_ann)
    return float(v) * 1e3 if v not in (None, "", "None") else 0.0


def price_companions(sys_s: pd.DataFrame, sys_k: pd.DataFrame) -> dict:
    """Same-weights C2 / C3a-like / C3b-like companions, screen vs keeper."""
    out = {}
    for tag, df in (("keeper", sys_k), ("screen", sys_s)):
        p = df.pivot(index="hour", columns="zone", values="price")
        m = p.mean(axis=1).to_numpy()
        out[tag] = {
            "mean_price": round(float(np.mean(m)), 3),
            "p95": round(float(np.percentile(m, 95)), 2),
            "hours_gt_300": int((m > 300).sum()),
            "cv_of_hourly": round(float(np.std(m) / max(np.mean(m), 1e-9)), 4),
        }
    out["delta_mean_price_pct"] = round(
        100.0
        * (out["screen"]["mean_price"] - out["keeper"]["mean_price"])
        / max(out["keeper"]["mean_price"], 1e-9),
        2,
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", nargs="?", default="results/calibration/nyiso198_screen_2024")
    a = ap.parse_args()
    B = ROOT / a.bundle
    res = {
        "session": "nyiso-198",
        "flag": FLAG,
        "year": YEAR,
        "keeper": KEEPER_ID,
        "screen_bundle": a.bundle,
        "note": "rule 29 screen — THROWAWAY, never registered, deleted before merge",
        "gates": {},
    }

    # ---- F-1' / F-2' carried from the zero-LP rebuild ----------------------
    rb = json.loads(
        (ROOT / f"results/calibration/_nyiso198_rebuild_checks_{YEAR}.json").read_text()
    )
    sc_s = json.loads((B / "run_config.json").read_text())["scenario_config"]
    sc_k = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    # Year-indexed scalars differ because the screen solves ONE year and the
    # keeper's run_config records the span's FIRST year — a category error, not
    # a recipe delta. Fields absent from the keeper's config and present at
    # their HEAD default in the screen are the nyiso-196 `head_defaults_not_
    # recipe` class (added after the keeper solved), reported separately.
    YEAR_FIELDS = ("weather_year", "gas_price_override", "year", "start_year")
    gdelta_raw = {
        k: [sc_k.get(k), sc_s.get(k)]
        for k in set(sc_k) | set(sc_s)
        if sc_k.get(k) != sc_s.get(k)
    }
    head_defaults = {
        k: v for k, v in gdelta_raw.items()
        if k not in YEAR_FIELDS and k != FLAG and v[0] is None
    }
    gdelta = {
        k: v for k, v in gdelta_raw.items()
        if k not in YEAR_FIELDS and k not in head_defaults
    }
    res["gates"]["F1_F2_presolve"] = {
        "moved_plants_mw": rb["moved_plants_mw"],
        "total_moved_mw": rb["F1_footprint"]["total_peak_band_moved_mw"],
        "pmax_drift": rb["F2_identity"]["plants_with_total_pmax_drift"],
        "g_delta_run_config": gdelta,
        "g_delta_raw": gdelta_raw,
        "year_fields_excluded": list(YEAR_FIELDS),
        "head_defaults_not_recipe": head_defaults,
        "g_delta_is_exactly_the_flag": list(gdelta) == [FLAG],
        "STOP": bool(list(gdelta) != [FLAG]),
    }

    # ---- S-3 direction, meter-free ----------------------------------------
    run = decode_run_js(
        (ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    )
    ypay = run["years"][str(YEAR)]
    bench = json.load(
        gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{YEAR}.json.gz")
    )["bench"]
    bplants = bench["plants"]

    dsp = pd.read_parquet(B / "dispatch" / f"{YEAR}_P1.parquet")
    col = "plant_code" if "plant_code" in dsp.columns else "plant"
    grp_col = "plant_group" if "plant_group" in dsp.columns else "klass"
    plant_mw = dsp.groupby([col, grp_col]).mw.sum()

    def screen_gwh(plant: int) -> float:
        tot = 0.0
        for g in CC:
            if (plant, g) in plant_mw.index:
                tot += float(plant_mw.loc[(plant, g)])
        return tot / 1e3

    def keeper_gwh(plant: int) -> float:
        """Keeper energy on the SAME basis as the screen's dispatch parquet.

        The dashboard payload renders a CHP plant as *LP grid dispatch + the
        measured flat BTM add-back*, while the dispatch parquet is LP grid
        alone. Comparing the two directly fabricates a fall at exactly the
        plants carrying a hold-out — the nyiso-197 defect
        (docs/FINDING-nyiso197-linden-addback-basis-2026-09-06.md §8 item 4,
        which asks for this assertion in the screen-gate probe pattern). The
        add-back is removed here so both sides are LP grid.
        """
        btm_gwh = float((bplants.get(str(plant)) or {}).get("btm") or 0.0) * 1e3
        for pk in (str(plant), f"{plant}:CC_REGULAR", f"{plant}:CC_CHP"):
            if pk in ypay["plants"]:
                return max(0.0, _ann(ypay["plants"][pk], "m_ann") - btm_gwh)
        return 0.0

    cv_k, cv_s = keeper_gwh(CV), screen_gwh(CV)
    ch_s = pd.read_parquet(B / "hourly" / f"class_hourly_{YEAR}.parquet")
    ch_k = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{YEAR}.parquet")
    es = ch_s[ch_s["pass"] == "P1"].groupby("klass").mw.sum() / 1e6
    ek = ch_k[ch_k["pass"] == "P1"].groupby("klass").mw.sum() / 1e6
    cc_k = float(sum(ek.get(k, 0) for k in CC)) * 1e3
    cc_s = float(sum(es.get(k, 0) for k in CC)) * 1e3

    s3 = {
        "cricket_valley": {
            "keeper_gwh": round(cv_k, 1),
            "screen_gwh": round(cv_s, 1),
            "delta_gwh": round(cv_s - cv_k, 1),
            "meter_gwh": round(float(bplants[str(CV)].get("c_ann") or 0) * 1e3, 1),
            "footprint_bound_gwh": CV_FOOTPRINT_GWH,
            "rose": bool(cv_s > cv_k),
            "within_bound": bool(0 < (cv_s - cv_k) <= CV_FOOTPRINT_GWH),
        },
        "fleet_cc": {
            "keeper_gwh": round(cc_k, 1),
            "screen_gwh": round(cc_s, 1),
            "delta_gwh": round(cc_s - cc_k, 1),
            "footprint_bound_gwh": FLEET_FOOTPRINT_GWH,
            "within_bound": bool(abs(cc_s - cc_k) <= FLEET_FOOTPRINT_GWH),
        },
    }
    s3["STOP"] = bool(
        not s3["cricket_valley"]["within_bound"] or not s3["fleet_cc"]["within_bound"]
    )
    moved = []
    for p_s in rb["moved_plants_mw"]:
        p = int(p_s)
        kk, ss = keeper_gwh(p), screen_gwh(p)
        met = float((bplants.get(str(p)) or {}).get("c_ann") or 0.0) * 1e3
        moved.append(
            {
                "plant": p,
                "name": (bplants.get(str(p)) or {}).get("name"),
                "rebanded_mw": rb["moved_plants_mw"][p_s],
                "keeper_gwh": round(kk, 1),
                "screen_gwh": round(ss, 1),
                "delta_gwh": round(ss - kk, 1),
                "meter_gwh": round(met, 1),
                "btm_addback_gwh_removed": round(
                    float((bplants.get(str(p)) or {}).get("btm") or 0.0) * 1e3, 1
                ),
                "meter_basis": "CAMPD gross (bench c_ann); model side is LP grid",
                "moved_toward_meter": (
                    None
                    if met <= 0
                    else bool(abs(ss - met) < abs(kk - met))
                ),
            }
        )
    s3["moved_plants"] = sorted(moved, key=lambda r: -abs(r["delta_gwh"]))
    res["gates"]["S3_direction"] = s3

    # ---- class energies + C1 ----------------------------------------------
    classes = sorted(set(es.index) | set(ek.index))
    res["gates"]["class_energy_twh"] = {
        k: {
            "keeper": round(float(ek.get(k, 0)), 3),
            "screen": round(float(es.get(k, 0)), 3),
            "delta": round(float(es.get(k, 0)) - float(ek.get(k, 0)), 3),
        }
        for k in classes
    }
    ypay2 = json.loads(json.dumps(ypay))
    for k, v in res["gates"]["class_energy_twh"].items():
        if k in ypay2.get("gmModel", {}):
            ypay2["gmModel"][k] = float(ypay2["gmModel"][k]) + v["delta"]
    c1_k = {r["key"]: r for r in cv.score_fuelmix(YEAR, ypay, bench, "NYISO")}
    c1_s = {r["key"]: r for r in cv.score_fuelmix(YEAR, ypay2, bench, "NYISO")}
    fields = ("status", "model", "actual", "share_pp", "magnitude")
    res["gates"]["C1_cells"] = {
        k: {
            "keeper": {f: c1_k[k].get(f) for f in fields},
            "screen": {f: c1_s[k].get(f) for f in fields},
        }
        for k in c1_k
        if k in c1_s
    }
    flips = [k for k in c1_k if k in c1_s and c1_k[k]["status"] != c1_s[k]["status"]]
    bad_flips = [
        k
        for k in flips
        if c1_k[k]["status"] == "PASS" and c1_s[k]["status"] != "PASS"
    ]
    res["gates"]["C1_cells"]["flips"] = flips
    res["gates"]["C1_cells"]["construction"] = (
        "calibration_verdict.score_fuelmix on the keeper's committed payload "
        "gmModel with the screen's P1 class-energy deltas applied (the "
        "nyiso-195/196 construction; approximate at the constant per-class "
        "grid-delivered-vs-P1 basis offset)"
    )

    # ---- S-4 companions ----------------------------------------------------
    sys_s = pd.read_parquet(B / "hourly" / f"system_{YEAR}.parquet")
    sys_k = pd.read_parquet(KEEPER / "hourly" / f"system_{YEAR}.parquet")
    res["gates"]["S4_companions"] = {
        "price": price_companions(sys_s, sys_k),
        "c1_load_bearing_pass_to_fail_flips": bad_flips,
        "STOP": bool(len(bad_flips) > 0),
        "note": (
            "CC_REGULAR is NOT exempted here (nyiso-196 exempted its own target "
            "cell): this arm is not offered as a fix for any residual, so a "
            "PASS -> FAIL there is a real cost and the PREREG gates it."
        ),
    }

    # ---- C8 / D-4 ----------------------------------------------------------
    ld_k = json.loads((KEEPER / "legitimacy_diagnostics.json").read_text())
    ld_s = (
        json.loads((B / "legitimacy_diagnostics.json").read_text())
        if (B / "legitimacy_diagnostics.json").exists()
        else None
    )

    def _d4_fail(ld):
        if not ld:
            return None
        rows = ld.get("diagnostics", {}).get("D4", {}).get("rows", [])
        return sorted(
            f"{r.get('year')}|{r.get('floor')}|{r.get('plant')}"
            for r in rows
            if str(r.get("verdict", "")).lower() not in ("pass", "")
        )

    def _c8(ld):
        if not ld:
            return None
        g = ld.get("gates", {})
        return {k: v for k, v in g.items() if "forc" in k.lower() or "C8" in k}

    d4_k, d4_s = _d4_fail(ld_k), _d4_fail(ld_s)
    new_d4 = [x for x in (d4_s or []) if x not in (d4_k or [])]
    res["gates"]["C8_D4"] = {
        "d4_failures_keeper": d4_k,
        "d4_failures_screen": d4_s,
        "new_d4_failures": new_d4,
        "c8_keeper": _c8(ld_k),
        "c8_screen": _c8(ld_s),
        "STOP": bool(new_d4),
    }

    stops = {
        k: res["gates"][k].get("STOP")
        for k in ("F1_F2_presolve", "S3_direction", "S4_companions", "C8_D4")
    }
    res["STOPS"] = stops
    res["VERDICT"] = "STOP" if any(stops.values()) else "CLEARED"
    dest = ROOT / "results/calibration/_nyiso198_screen_gates.json"
    dest.write_text(json.dumps(res, indent=1))
    print("VERDICT:", res["VERDICT"], json.dumps(stops))
    print("S3:", json.dumps(
        {k: v for k, v in s3.items() if k != "moved_plants"}, indent=1))
    print("S4:", json.dumps(res["gates"]["S4_companions"], indent=1))
    print("class deltas:", json.dumps(
        {k: v["delta"] for k, v in res["gates"]["class_energy_twh"].items()
         if abs(v["delta"]) > 0.01}))
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
