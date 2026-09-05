"""nyiso-196 SCREEN GATES — evaluate the 2024 screen bundle of
``unit_outage_extract_basis_share`` against the keeper's committed 2024
(rule 29 ``[R-SCREEN]``; control = form 4, no control solve).

Gates are the PREREG's (``PREREG-nyiso196-cc-outage-share-basis-screen.md`` §6),
structural and STOP-only:

* **F-1 / F-2** — carried from the zero-LP rebuild checks
  (``_nyiso196_rebuild_checks_2024.json``), plus: the screen's persisted fleet
  parquet has the keeper rebuild's ``pmax`` on every unit, and the screen's
  ``run_config.json`` differs from the keeper's ``scenario_config`` in exactly
  the one flag (G-DELTA).
* **S-3 direction** — from the screen's ``dispatch/2024_P1.parquet``: Cricket
  Valley's energy in the extract's all-blocks-out windows is 0; its energy
  above the arm's availability envelope is 0; its annual energy falls by at
  least half of the 512 GWh the keeper dispatched from capacity the extract
  says was out; Selkirk's energy falls. Reported: every moved plant's energy
  vs the keeper payload and vs its meter; the class buckets at Cricket Valley.
* **S-4 load-bearing companions** — the same-weights price companions
  (C2 / C3a-like / C3b-like) and every C1 class cell through
  ``calibration_verdict.score_fuelmix`` on the keeper's committed payload with
  the screen's P1 class-energy deltas applied (the nyiso-195 construction;
  C1-2024 ``CC_REGULAR`` REPORTED at full magnitude, never gated); no flip
  PASS -> FAIL on a load-bearing cell.
* **C8 / D-4** — the screen's regenerated ``legitimacy_diagnostics.json``
  forced shares and D-4 failures vs the keeper's.

Writes ``results/calibration/_nyiso196_screen_gates.json``.

Usage: ``python scripts/probes/nyiso196_screen_gates.py [results/calibration/nyiso196_screen_2024]``
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
for p in (
    ROOT,
    ROOT / "src",
    ROOT / "scripts",
    ROOT / "scripts/probes",
    ROOT / "scripts/data",
):
    sys.path.insert(0, str(p))
import calibration_verdict as cv  # noqa: E402
from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402
from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402

KEEPER = ROOT / "results/calibration/nyiso192_astoria_panel"
KEEPER_ID = "2026-09-05-nyiso-192-astoria-panel"
YEAR = 2024
T = 8760
CV = 57185
SELKIRK = 10725
FLAG = "unit_outage_extract_basis_share"
GAS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
LOAD_BEARING_C1 = (
    "CC_REGULAR",
    "CC_CHP",
    "ST_GAS",
    "CT_PEAKER",
    "CT_CHP",
    "ST_CHP",
    "nuclear",
    "hydro",
    "import",
    "wind",
    "solar",
)
REBUILD_CHECKS = ROOT / "results/calibration/_nyiso196_rebuild_checks_2024.json"
DECOMP = ROOT / "results/calibration/_nyiso196_cc_overrun_decomp.json"
ARM_REBUILD = ROOT / ".cache/nyiso196/rebuild_2024_arm.pkl"
KEEPER_REBUILD = ROOT / ".cache/nyiso196/rebuild_2024_keeper.pkl"


def _dec(b64: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def _series(entry: dict, key_bytes: str, key_ann: str, npl: float) -> np.ndarray | None:
    raw_b64 = entry.get(key_bytes)
    if not raw_b64:
        return None
    raw = _dec(raw_b64)[:T]
    ann = entry.get(key_ann)
    if ann not in (None, "", "None") and raw.sum() > 0:
        return raw * (float(ann) * 1e6 / raw.sum())
    return raw * npl / 100.0 if npl > 0 else None


def price_companions(sysp_s: pd.DataFrame, sysp_k: pd.DataFrame) -> dict:
    from _nyiso192_common import actual_zone_price

    px = actual_zone_price(YEAR)
    out = {}
    for tag, sp in (("screen", sysp_s), ("keeper", sysp_k)):
        p = sp.pivot(index="hour", columns="zone", values="price").iloc[:T]
        w = (
            sp.pivot(index="hour", columns="zone", values="demand")
            .iloc[:T]
            .clip(lower=0)
        )
        zones = [z for z in p.columns if z in px.columns]
        p, w, a = p[zones], w[zones], px[zones].iloc[:T]
        lw_model = float((p * w).sum().sum() / w.sum().sum())
        lw_act = float((a.to_numpy() * w.to_numpy()).sum() / w.sum().sum())
        mo = pd.date_range("2023-01-01", periods=T, freq="h").month
        pm = p.groupby(mo).mean()
        am = pd.DataFrame(a.to_numpy(), columns=zones).groupby(mo).mean()
        nrmse = float(
            np.sqrt(((pm.to_numpy() - am.to_numpy()) ** 2).mean())
            / am.to_numpy().mean()
        )
        out[tag] = {
            "lw_mean_model": round(lw_model, 3),
            "lw_mean_actual_same_weights": round(lw_act, 3),
            "c3a_like_pct": round(100 * (lw_model / lw_act - 1), 2),
            "c3b_like_monthly_nrmse": round(nrmse, 4),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "bundle", nargs="?", default="results/calibration/nyiso196_screen_2024"
    )
    a = ap.parse_args()
    B = ROOT / a.bundle
    res = {
        "session": "nyiso-196",
        "screen_bundle": a.bundle,
        "control": "keeper committed artifacts (rule 29(b) form 4; no control solve)",
        "gates": {},
    }
    rc_s = json.loads((B / "run_config.json").read_text())
    rc_k = json.loads((KEEPER / "run_config.json").read_text())
    sc_s, sc_k = rc_s["scenario_config"], rc_k["scenario_config"]
    raw_delta = {
        k: (sc_k.get(k), sc_s.get(k))
        for k in set(sc_k) | set(sc_s)
        if sc_k.get(k) != sc_s.get(k)
    }
    # G-DELTA classification (the gen_nyiso192_attestation.g_delta convention):
    # (a) per-year solve parameters — the keeper's run_config records its FIRST
    #     solve year's weather_year / gas_price_override, the single-year screen
    #     records 2024's; (b) a field the keeper never serialised (None) or
    #     recorded at a since-flipped default, which the arm records at
    #     ScenarioConfig's HEAD default — a field added or re-defaulted after the
    #     keeper solved (backcast-inert per PREREG §5 G-DRIFT), not a recipe
    #     delta. What remains must be exactly the flag.
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    head_defaults = {
        f.name: (f.default if f.default is not dataclasses.MISSING else None)
        for f in dataclasses.fields(ScenarioConfig)
    }
    per_year = {"weather_year", "gas_price_override"}
    head_default = sorted(
        k
        for k, (kv, av) in raw_delta.items()
        if k != FLAG
        and k not in per_year
        and k in head_defaults
        and av == head_defaults[k]
    )
    delta = {
        k: v
        for k, v in raw_delta.items()
        if k not in per_year and k not in head_default
    }
    rb = json.loads(REBUILD_CHECKS.read_text())
    arm = pickle.load(open(ARM_REBUILD, "rb"))
    kee = pickle.load(open(KEEPER_REBUILD, "rb"))
    U = arm["units"]
    fls = (
        pq.read_table(B / "dispatch" / f"{YEAR}_P1_fleet.parquet")
        .to_pandas()
        .set_index("unit_id")
        .pmax_mw
    )
    # The persisted fleet parquet carries the LP's dispatchable units (the
    # rebuild also lists zero-capacity / pseudo rows); compare on the join.
    kp = kee["units"].set_index("unit_id").pmax
    common = fls.index.intersection(kp.index)
    res["gates"]["F1_F2_carried"] = {
        "rebuild_checks": {
            k: rb[k].get("PASS") for k in ("F1_footprint", "F2_identity")
        },
        "units_availability_moved": rb["F1_footprint"]["units_availability_moved"],
        "non_cc_units_moved": rb["F1_footprint"]["non_cc_units_moved"],
        "mc_base_max_abs_delta": rb["F1_footprint"]["mc_base_max_abs_delta"],
        "screen_fleet_parquet_units": int(len(fls)),
        "screen_fleet_parquet_units_matched_to_keeper_rebuild": int(len(common)),
        "screen_fleet_parquet_pmax_vs_keeper_rebuild_max_abs": round(
            float((fls.loc[common] - kp.loc[common]).abs().max()), 6
        ),
        "g_delta_raw": {k: list(v) for k, v in raw_delta.items()},
        "g_delta_per_year_solve_parameters": sorted(
            k for k in raw_delta if k in per_year
        ),
        "g_delta_head_defaults_not_recipe": head_default,
        "g_delta_recipe": {k: list(v) for k, v in delta.items()},
        "g_delta_is_exactly_the_flag": bool(
            set(delta) == {FLAG} and sc_s.get(FLAG) is True
        ),
        "PASS": bool(
            rb["F1_footprint"]["PASS"]
            and rb["F2_identity"]["PASS"]
            and set(delta) == {FLAG}
            and len(common) == len(fls)
            and float((fls.loc[common] - kp.loc[common]).abs().max()) < 1e-6
        ),
    }

    # ---- screen dispatch --------------------------------------------------------------
    ds = pq.read_table(
        B / "dispatch" / f"{YEAR}_P1.parquet",
        columns=["unit_id", "plant_code", "klass_base", "zone", "hour", "mw"],
    ).to_pandas()
    ds = ds[ds.hour < T]
    plant_mw = (
        ds.groupby(["plant_code", "klass_base", "hour"])
        .mw.sum()
        .unstack("hour")
        .reindex(columns=range(T))
        .fillna(0.0)
    )

    # keeper payload + bench (the control per-plant rows) and the decomposition
    run = decode_run_js(
        (ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    )
    ypay = run["years"][str(YEAR)]
    bench = json.load(
        gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{YEAR}.json.gz")
    )["bench"]
    bplants = bench["plants"]
    on = unit_outage_derate_factors(
        YEAR,
        iso="NYISO",
        per_unit_crosswalk=True,
        merit_order_guard=True,
        extract_basis_share=True,
    )
    off = unit_outage_derate_factors(
        YEAR, iso="NYISO", per_unit_crosswalk=True, merit_order_guard=True
    )
    dec = json.loads(DECOMP.read_text())["years"][str(YEAR)]
    dec_cv = next(r for r in dec["plants"] if r["plant"] == CV)

    # ---- S-3 direction at Cricket Valley ------------------------------------------------
    cv_rows = U[(U.plant == CV) & (U.group == "CC_REGULAR")]
    env_arm = (
        arm["avail"][cv_rows.i.to_numpy()][:, :T] * cv_rows.pmax.to_numpy()[:, None]
    ).sum(axis=0)
    m_s = (
        plant_mw.loc[(CV, "CC_REGULAR")].to_numpy()
        if (CV, "CC_REGULAR") in plant_mw.index
        else np.zeros(T)
    )
    k_on = on[(CV, "CC_REGULAR")][:T]
    dark = k_on <= 1e-9
    b = bplants[str(CV)]
    npl = float(b["npl"])
    c = _series(b, "campd", "c_ann", npl)
    thr = 0.01 * npl + 1.0
    on_s, on_c = m_s > thr, c > thr
    buckets_s = {
        "a_model_on_meter_off": round(float(m_s[on_s & ~on_c].sum()) / 1e3, 1),
        "b_plus": round(float((m_s - c)[on_s & on_c & (m_s > c)].sum()) / 1e3, 1),
        "b_minus": round(float((c - m_s)[on_s & on_c & (m_s < c)].sum()) / 1e3, 1),
        "c_meter_on_model_off": round(float(c[~on_s & on_c].sum()) / 1e3, 1),
        "online_h": int(on_s.sum()),
    }
    keeper_cv_gwh = float(ypay["plants"][str(CV)]["m_ann"]) * 1e3
    fall = keeper_cv_gwh - m_s.sum() / 1e3
    above_env = float(np.clip(m_s - env_arm, 0.0, None).sum()) / 1e3
    s3 = {
        "cv_dark_window_hours": int(dark.sum()),
        "cv_energy_in_dark_windows_gwh": {
            "keeper": dec_cv["availability"]["dark_window_model_gwh"],
            "screen": round(float(m_s[dark].sum()) / 1e3, 3),
        },
        "cv_energy_above_arm_envelope_gwh": round(above_env, 3),
        "cv_energy_gwh": {
            "keeper_payload": round(keeper_cv_gwh, 1),
            "screen": round(float(m_s.sum()) / 1e3, 1),
            "meter_campd": round(float(c.sum()) / 1e3, 1),
        },
        "cv_fall_gwh": round(fall, 1),
        "cv_required_fall_gwh": round(
            0.5 * dec_cv["availability"]["model_energy_above_extract_availability_gwh"],
            1,
        ),
        "cv_online_h": {
            "keeper": dec_cv["online_h_model"],
            "screen": buckets_s["online_h"],
            "meter": dec_cv["online_h_campd"],
        },
        "cv_buckets_gwh": {"keeper": dec_cv["buckets_gwh"], "screen": buckets_s},
    }
    sel = (
        plant_mw.loc[(SELKIRK, "CC_CHP")].to_numpy().sum() / 1e3
        if (SELKIRK, "CC_CHP") in plant_mw.index
        else 0.0
    )
    sel_k = (
        float(ypay["plants"][str(SELKIRK)]["m_ann"]) * 1e3
        if str(SELKIRK) in ypay["plants"]
        else None
    )
    s3["selkirk_energy_gwh"] = {
        "keeper_payload": sel_k,
        "screen": round(float(sel), 1),
        "meter_campd": float(bplants[str(SELKIRK)]["c_ann"]) * 1e3
        if str(SELKIRK) in bplants
        else None,
    }
    s3["selkirk_fell"] = bool(sel_k is not None and sel < sel_k)
    s3["STOP"] = bool(
        s3["cv_energy_in_dark_windows_gwh"]["screen"] > 0.5
        or above_env > 0.5
        or fall < s3["cv_required_fall_gwh"]
        or not s3["selkirk_fell"]
    )
    # every moved plant: energy keeper -> screen vs meter (reported)
    moved = []
    for plant in rb["F1_footprint"]["plants_moved"]:
        for grp in ("CC_REGULAR", "CC_CHP"):
            key = (plant, grp)
            if key not in plant_mw.index:
                continue
            pkey = str(plant) if str(plant) in ypay["plants"] else f"{plant}:{grp}"
            if pkey not in ypay["plants"] or pkey not in bplants:
                continue
            kk = float(ypay["plants"][pkey]["m_ann"]) * 1e3
            mm = float(plant_mw.loc[key].sum()) / 1e3
            met = float(bplants[pkey].get("c_ann") or 0.0) * 1e3
            moved.append(
                {
                    "plant": plant,
                    "group": grp,
                    "keeper_gwh": round(kk, 1),
                    "screen_gwh": round(mm, 1),
                    "meter_gwh": round(met, 1),
                    "avail_off_mean": round(float(off[key].mean()), 4)
                    if key in off
                    else None,
                    "avail_on_mean": round(float(on[key].mean()), 4)
                    if key in on
                    else None,
                    "moved_toward_meter": bool(abs(mm - met) < abs(kk - met)),
                }
            )
    s3["moved_plants"] = sorted(
        moved, key=lambda r: -abs(r["screen_gwh"] - r["keeper_gwh"])
    )
    res["gates"]["S3_direction"] = s3

    # ---- class energies + C1 (REPORTED) ------------------------------------------------
    ch_s = pd.read_parquet(B / "hourly" / f"class_hourly_{YEAR}.parquet")
    ch_k = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{YEAR}.parquet")
    es = ch_s[ch_s["pass"] == "P1"].groupby("klass").mw.sum() / 1e6
    ek = ch_k[ch_k["pass"] == "P1"].groupby("klass").mw.sum() / 1e6
    classes = sorted(set(es.index) | set(ek.index))
    res["gates"]["class_energy_twh"] = {
        k: {
            "keeper": round(float(ek.get(k, 0)), 3),
            "screen": round(float(es.get(k, 0)), 3),
            "delta": round(float(es.get(k, 0)) - float(ek.get(k, 0)), 3),
        }
        for k in classes
    }
    res["gates"]["gas_family_twh"] = {
        "keeper": round(float(sum(ek.get(k, 0) for k in GAS)), 3),
        "screen": round(float(sum(es.get(k, 0) for k in GAS)), 3),
    }
    ypay2 = json.loads(json.dumps(ypay))
    for k, v in res["gates"]["class_energy_twh"].items():
        if k in ypay2["gmModel"]:
            ypay2["gmModel"][k] = float(ypay2["gmModel"][k]) + v["delta"]
    c1_k = {r["key"]: r for r in cv.score_fuelmix(YEAR, ypay, bench, "NYISO")}
    c1_s = {r["key"]: r for r in cv.score_fuelmix(YEAR, ypay2, bench, "NYISO")}
    fields = ("status", "model", "actual", "share_pp", "magnitude")
    res["gates"]["C1_2024_reported_not_gated"] = {
        k: {
            "keeper": {f: c1_k[k].get(f) for f in fields},
            "screen": {f: c1_s[k].get(f) for f in fields},
        }
        for k in c1_k
        if k in c1_s
    }
    flips = [k for k in c1_k if k in c1_s and c1_k[k]["status"] != c1_s[k]["status"]]
    res["gates"]["C1_2024_reported_not_gated"]["flips"] = flips
    res["gates"]["C1_2024_reported_not_gated"]["construction"] = (
        "calibration_verdict.score_fuelmix on the keeper's committed payload gmModel with the screen's P1 class-energy "
        "deltas applied (approximate: the payload's grid-delivered basis vs the P1 sum differ by a constant per class)"
    )

    # ---- S-4 companions ----------------------------------------------------------------
    sys_s = pd.read_parquet(B / "hourly" / f"system_{YEAR}.parquet")
    sys_k = pd.read_parquet(KEEPER / "hourly" / f"system_{YEAR}.parquet")
    pc = price_companions(sys_s, sys_k)
    bad_flips = [
        k
        for k in flips
        if k in LOAD_BEARING_C1
        and c1_k[k]["status"] == "PASS"
        and c1_s[k]["status"] != "PASS"
        and k != "CC_REGULAR"
    ]
    res["gates"]["S4_companions"] = {
        "price": pc,
        "c1_load_bearing_pass_to_fail_flips": bad_flips,
        "STOP": bool(len(bad_flips) > 0),
    }

    # ---- C8 / D-4 -----------------------------------------------------------------------
    ld_s = (
        json.loads((B / "legitimacy_diagnostics.json").read_text())
        if (B / "legitimacy_diagnostics.json").exists()
        else None
    )
    ld_k = json.loads((KEEPER / "legitimacy_diagnostics.json").read_text())

    def _d2(ld):
        return {
            f"{r['year']}:{r['class']}": (r["forced_share"], r["verdict"])
            for r in ld["diagnostics"]["D2"]["summary"]
            if int(r["year"]) == YEAR
        }

    res["gates"]["C8_D4"] = {
        "d2_keeper": _d2(ld_k),
        "d2_screen": _d2(ld_s) if ld_s else None,
        "d4_failures_keeper_2024": [
            f for f in ld_k["diagnostics"]["D4"]["failures"] if f.startswith(str(YEAR))
        ],
        "d4_failures_screen_2024": [
            f for f in ld_s["diagnostics"]["D4"]["failures"] if f.startswith(str(YEAR))
        ]
        if ld_s
        else None,
    }
    res["verdict"] = {
        "F1_F2": "PASS" if res["gates"]["F1_F2_carried"]["PASS"] else "STOP",
        "S3": "STOP" if s3["STOP"] else "PASS",
        "S4": "STOP" if res["gates"]["S4_companions"]["STOP"] else "PASS",
        "screen": "CLEARED"
        if (
            res["gates"]["F1_F2_carried"]["PASS"]
            and not s3["STOP"]
            and not res["gates"]["S4_companions"]["STOP"]
        )
        else "KILLED",
    }
    dst = ROOT / "results/calibration/_nyiso196_screen_gates.json"
    dst.write_text(
        json.dumps(
            res,
            indent=1,
            default=lambda o: (
                float(o)
                if isinstance(o, np.floating)
                else int(o)
                if isinstance(o, np.integer)
                else bool(o)
                if isinstance(o, np.bool_)
                else str(o)
            ),
        )
    )
    print(json.dumps(res["verdict"]))
    print("F1/F2:", json.dumps(res["gates"]["F1_F2_carried"], default=str)[:600])
    print(
        "S3:",
        json.dumps({k: v for k, v in s3.items() if k != "moved_plants"}, default=str),
    )
    for r in s3["moved_plants"]:
        print("   ", r)
    print(
        "class energies:",
        {
            k: v
            for k, v in res["gates"]["class_energy_twh"].items()
            if k in GAS or k == "import"
        },
    )
    print("gas family:", res["gates"]["gas_family_twh"])
    print(
        "C1:",
        json.dumps(
            {
                k: v
                for k, v in res["gates"]["C1_2024_reported_not_gated"].items()
                if k in GAS or k == "flips"
            },
            default=str,
        ),
    )
    print("S4:", json.dumps(res["gates"]["S4_companions"], default=str))
    print("C8/D4:", json.dumps(res["gates"]["C8_D4"], default=str)[:1500])
    print(f"wrote {dst.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
