"""nyiso-195 — evaluate the PREREG §4 screen gates for the 2024 econ-basis screen.

Differences the one-year screen bundle (``CC_REGULAR`` econ ramp offered at its
registered physical basis, ``econ_low 0.784 / econ_high 0.925``) against the
KEEPER'S COMMITTED ARTIFACTS — rule 29(b) form 4, the owner's "no control arm,
just use the last keeper". The keeper's ``dispatch/`` parquet is gitignored and
absent from this clone, so the control side is read from what IS committed:

* the per-plant / class loading rows nyiso-194 computed from the keeper's
  dispatch parquet (``_nyiso194_screen_gates_S.json``, keeper side — the same
  construction this script applies to the screen), its class energies and
  CAMPD rows;
* the keeper's ``hourly/system_2024.parquet`` (zonal price / demand) for the
  price companions;
* the keeper's committed run payload ``gmModel`` + the 2024 bench part, scored
  through ``calibration_verdict.score_fuelmix`` itself with the screen's class
  energy deltas applied — the C1-2024 cell at the scorer's own construction
  (reported at full magnitude, NEVER a gate — PREREG §4);
* zero-LP ``run_year(fleet_only=True)`` rebuilds of BOTH bundles for the
  footprint (E-1) and identity (E-2) gates: every unit's tranche pmax, heat
  rate and ``offer_markup_hr``, and the assembled ``mc_base`` the LP solved on.

Gates are structural and STOP-only (PREREG-nyiso195 §4): E-1 footprint, E-2
identity, E-3 direction of the class loading distribution, E-4 load-bearing
companions (approximate C2 / C3a / C3b, same-weights construction as
nyiso-194). Nothing here contributes to a determination.

Usage: ``python scripts/probes/nyiso195_screen_gates.py [results/calibration/nyiso195_screen_2024]``.
Writes ``results/calibration/_nyiso195_screen_gates.json``.
"""

from __future__ import annotations

import argparse
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
from market_sim.data.campd import load_campd_hourly  # noqa: E402
from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

KEEPER = ROOT / "results/calibration/nyiso192_astoria_panel"
KEEPER_ID = "2026-09-05-nyiso-192-astoria-panel"
CONTROL_JSON = ROOT / "results/calibration/_nyiso194_screen_gates_S.json"
YEAR = 2024
T = 8760
BINS = np.arange(0.0, 1.01, 0.1)
GAS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
WALL_PLANTS = (
    57664,
    56940,
    54574,
    50292,
)  # wall inside the 80-90 % bin (nyiso-194 PREREG §1)
CACHE = ROOT / ".cache" / "nyiso195"


def _tr(u: str) -> str:
    t = u.rsplit("_", 1)[1]
    return "econ" if t.startswith("econc") else t


def rebuild(bundle: Path, tag: str) -> dict:
    """Zero-LP on-recipe fleet rebuild of ``bundle`` (cached per tag)."""
    f = CACHE / f"fleet_{tag}_{YEAR}.pkl"
    if f.exists():
        return pickle.load(open(f, "rb"))
    state, _meta = reconstruct_bundle_fleet(
        bundle, YEAR, required_flags=(), required_sequences=()
    )
    cfg = state["config"]
    anchor = float(getattr(cfg, "gas_offer_margin_anchor"))
    gens = state["fleet"]
    df = pd.DataFrame(
        {
            "unit_id": [g.unit_id for g in gens],
            "plant": [int(g.plant_code) for g in gens],
            "group": [str(getattr(g, "plant_group", "")) for g in gens],
            "zone": [str(g.zone) for g in gens],
            "pmax": [float(g.pmax_mw) for g in gens],
            "hr": [float(g.heat_rate) for g in gens],
            "vom": [float(getattr(g, "vom", 0.0)) for g in gens],
            "markup_hr": [float(getattr(g, "offer_markup_hr", 0.0)) for g in gens],
            "anchor": [
                float(getattr(g, "offer_margin_anchor", None) or anchor) for g in gens
            ],
        }
    )
    out = {
        "units": df,
        "mc": np.asarray(state["mc_base"], dtype=np.float32),
        "occ": dict(cfg.offer_curve_by_group["CC_REGULAR"]),
        "overrides": dict(getattr(cfg, "offer_curve_by_group", {}) or {}),
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    pickle.dump(out, open(f, "wb"))
    return out


def hist_share(mw: np.ndarray, cap: float) -> np.ndarray:
    on = mw[mw > 1.0]
    if on.size == 0:
        return np.zeros(len(BINS) - 1)
    h, _ = np.histogram(np.clip(on / cap, 0, 1 - 1e-9), bins=BINS)
    return h / on.size


def plant_frames(d: pd.DataFrame, fl: pd.Series):
    cc = d[d.klass_base == "CC_REGULAR"].copy()
    cc["trk"] = cc.unit_id.map(_tr)
    units = cc.drop_duplicates("unit_id")[["unit_id", "plant_code", "trk"]].copy()
    units["pmax"] = units.unit_id.map(fl)
    cap = units.pivot_table(
        index="plant_code", columns="trk", values="pmax", aggfunc="sum"
    ).fillna(0.0)
    for c in ("committed", "econ", "peak"):
        if c not in cap.columns:
            cap[c] = 0.0
    plant = cc.groupby(["plant_code", "hour"]).mw.sum().unstack("hour")
    peak = (
        cc[cc.trk == "peak"]
        .groupby(["plant_code", "hour"])
        .mw.sum()
        .unstack("hour")
        .reindex(plant.index)
        .fillna(0.0)
    )
    return cc, cap, plant, peak


def class_bins(plant: pd.DataFrame, cap: pd.DataFrame) -> np.ndarray:
    tot = np.zeros(len(BINS) - 1)
    for pc in plant.index:
        if pc == 2500:
            continue
        m = plant.loc[pc].to_numpy()
        pm = float(cap.loc[pc].sum())
        tot += hist_share(m, pm) * int((m > 1).sum()) * pm
    return tot / tot.sum()


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
        "bundle", nargs="?", default="results/calibration/nyiso195_screen_2024"
    )
    a = ap.parse_args()
    B = ROOT / a.bundle
    ctl = json.load(open(CONTROL_JSON))["gates"]
    res = {
        "session": "nyiso-195",
        "screen_bundle": a.bundle,
        "control": "keeper committed artifacts (rule 29(b) form 4; no control solve)",
        "control_sources": [
            str(CONTROL_JSON.relative_to(ROOT)),
            "results/calibration/nyiso192_astoria_panel/hourly/system_2024.parquet",
            f"frontend/data/backcast/runs/{KEEPER_ID}.js + bench/NYISO/2024.json.gz",
            "run_year(fleet_only=True) rebuilds of both bundles",
        ],
        "gates": {},
    }

    # ---- E-1 footprint + E-2 identity: zero-LP rebuilds of both bundles --------------------------
    K = rebuild(KEEPER, "keeper")
    A = rebuild(B, "arm")
    ku, au = K["units"].set_index("unit_id"), A["units"].set_index("unit_id")
    same_units = list(ku.index) == list(au.index)
    j = ku.join(au, lsuffix="_k", rsuffix="_a", how="outer")
    d_pmax = j[(j.pmax_k - j.pmax_a).abs() > 1e-6]
    d_hr = j[(j.hr_k - j.hr_a).abs() > 1e-9]
    d_mk = j[(j.markup_hr_k - j.markup_hr_a).abs() > 1e-9]
    mc_k, mc_a = K["mc"], A["mc"]
    dmc = (mc_a - mc_k) if mc_k.shape == mc_a.shape else None
    rows_changed = (
        np.nonzero(np.abs(dmc).max(axis=1) > 1e-3)[0]
        if dmc is not None
        else np.array([])
    )
    econ_cc = (ku.group == "CC_REGULAR") & ku.index.map(lambda u: _tr(u) == "econ")
    res["gates"]["E1_footprint"] = {
        "same_unit_order": bool(same_units),
        "units_with_pmax_change": int(len(d_pmax)),
        "units_with_heat_rate_change": int(len(d_hr)),
        "heat_rate_change_groups": sorted(set(d_hr.group_k.dropna())),
        "heat_rate_change_tranches": sorted({_tr(u) for u in d_hr.index}),
        "units_with_markup_change": int(len(d_mk)),
        "markup_change_groups": sorted(set(d_mk.group_k.dropna())),
        "mc_rows_changed": int(len(rows_changed)),
        "mc_rows_changed_all_cc_regular_econ": bool(
            np.all(econ_cc.to_numpy()[rows_changed])
        )
        if len(rows_changed)
        else None,
        "cc_regular_econ_rows_total": int(econ_cc.sum()),
        "arm_overrides_CC_REGULAR": {
            k: A["occ"].get(k)
            for k in (
                "committed",
                "econ_low",
                "econ_high",
                "peak",
                "phys_committed",
                "phys_econ_low",
                "phys_econ_high",
                "phys_peak",
                "econ_low_share",
                "pct_peaking",
            )
        },
        "other_classes_curves_identical": bool(
            all(
                K["overrides"].get(c) == A["overrides"].get(c)
                for c in K["overrides"]
                if c != "CC_REGULAR"
            )
        ),
    }
    # E-2: arm markup 0 on every CC_REGULAR econ slice; arm mc == keeper mc - markup_k x anchor_k hour for hour;
    #      arm slice heat rate == phys_k x base_HR (registered = physical); committed/peak byte-identical
    ek = ku[econ_cc.to_numpy()]
    ea = au.loc[ek.index]
    idx = np.array([ku.index.get_loc(u) for u in ek.index])
    pred = mc_k[idx] - (ek.markup_hr * ek.anchor).to_numpy()[:, None].astype(np.float32)
    ident_err = np.abs(mc_a[idx] - pred).max() if dmc is not None else None
    n = 6
    kpos = ek.index.map(lambda u: (int(u.rsplit("econc", 1)[1]) + 0.5) / n).to_numpy()
    mult_k = (
        float(K["occ"]["econ_low"])
        + (float(K["occ"]["econ_high"]) - float(K["occ"]["econ_low"])) * kpos
    )
    base_hr = ek.hr.to_numpy() / mult_k
    phys_k = (
        float(K["occ"]["phys_econ_low"])
        + (float(K["occ"]["phys_econ_high"]) - float(K["occ"]["phys_econ_low"])) * kpos
    )
    hr_err = float(np.abs(ea.hr.to_numpy() - base_hr * phys_k).max())
    nonecon = ~econ_cc.to_numpy()
    res["gates"]["E2_identity"] = {
        "arm_econ_markup_hr_max": round(float(ea.markup_hr.abs().max()), 9),
        "arm_mc_equals_keeper_minus_fixed_margin_max_abs_err": round(
            float(ident_err), 5
        )
        if ident_err is not None
        else None,
        "arm_econ_hr_equals_phys_x_baseHR_max_abs_err": round(hr_err, 9),
        "non_econ_rows_mc_max_abs_delta": round(float(np.abs(dmc[nonecon]).max()), 6)
        if dmc is not None
        else None,
        "fixed_margin_removed_$MWh_capw": {
            "bottom": round(float((ek.markup_hr * ek.anchor)[kpos < 0.2].mean()), 3),
            "top": round(float((ek.markup_hr * ek.anchor)[kpos > 0.8].mean()), 3),
        },
    }

    # ---- screen dispatch --------------------------------------------------------------------------
    ds = pq.read_table(
        B / "dispatch" / f"{YEAR}_P1.parquet",
        columns=["unit_id", "plant_code", "klass_base", "zone", "hour", "mw", "lmp"],
    ).to_pandas()
    fls = (
        pq.read_table(B / "dispatch" / f"{YEAR}_P1_fleet.parquet")
        .to_pandas()
        .set_index("unit_id")
        .pmax_mw
    )
    ccs, caps, ps, pks = plant_frames(ds, fls)
    # fleet parquet pmax vs the keeper rebuild (the persisted fleet is the rebuild's fleet)
    fp = fls.reindex(ku.index)
    res["gates"]["E1_footprint"][
        "screen_fleet_parquet_pmax_vs_keeper_rebuild_max_abs"
    ] = round(float((fp - ku.pmax).abs().max()), 6)

    # ---- E-3 direction ---------------------------------------------------------------------------
    cb_s = class_bins(ps, caps)
    cl_k = ctl["class_loading_bins_pct"]
    camp = load_campd_hourly(["NY"], [YEAR], prefer_unit_level=True)
    camp = camp[camp.plant_id.isin(ps.index)]
    g = camp.groupby(["plant_id", "hour_of_year"]).gross_mw.sum()
    s8, s9 = cb_s[8] * 100, cb_s[9] * 100
    k8, k9 = cl_k["share_80_90"]["keeper"], cl_k["share_90_100"]["keeper"]
    c8, c9 = cl_k["share_80_90"]["campd"], cl_k["share_90_100"]["campd"]
    res["gates"]["E3_direction"] = {
        "bins": cl_k["bins"],
        "keeper": cl_k["keeper"],
        "screen": [round(float(x) * 100, 1) for x in cb_s],
        "campd": cl_k["campd"],
        "share_80_90": {"keeper": k8, "screen": round(s8, 2), "campd": c8},
        "share_90_100": {"keeper": k9, "screen": round(s9, 2), "campd": c9},
        "share_80_90_fell": bool(s8 < k8),
        "moved_toward_campd_80_90": bool(abs(s8 - c8) < abs(k8 - c8)),
        "share_90_100_rose": bool(s9 > k9),
        "moved_toward_campd_90_100": bool(abs(s9 - c9) < abs(k9 - c9)),
    }
    res["gates"]["E3_direction"]["STOP"] = not res["gates"]["E3_direction"][
        "share_80_90_fell"
    ]
    ctl_plants = {r["plant"]: r for r in ctl["plants"]}
    rows = []
    for pc in ps.index:
        ms = ps.loc[pc].to_numpy()
        pm = float(caps.loc[pc].sum())
        kr = ctl_plants.get(int(pc))
        old_wall = (
            kr["old_wall_frac"]
            if kr
            else (1 - caps.loc[pc, "peak"] / pm if pm else 1.0)
        )
        x = (
            g.loc[pc].reindex(range(T)).fillna(0).to_numpy()
            if pc in g.index.get_level_values(0)
            else None
        )
        rows.append(
            {
                "plant": int(pc),
                "pmax": round(pm),
                "old_wall_frac": round(float(old_wall), 3),
                "h_above_old_wall": {
                    "keeper": kr["h_above_old_wall"]["keeper"] if kr else None,
                    "screen": int((ms > old_wall * pm + 0.5).sum()),
                    "campd": kr["h_above_old_wall"]["campd"]
                    if kr
                    else (int((x > old_wall * pm).sum()) if x is not None else None),
                },
                "h_gt80": {
                    "keeper": kr["h_gt80"]["keeper"] if kr else None,
                    "screen": int((ms > 0.8 * pm).sum()),
                    "campd": kr["h_gt80"]["campd"] if kr else None,
                },
                "h_gt90": {
                    "keeper": kr["h_gt90"]["keeper"] if kr else None,
                    "screen": int((ms > 0.9 * pm).sum()),
                    "campd": kr["h_gt90"]["campd"] if kr else None,
                },
                "on_h": {"screen": int((ms > 1).sum())},
                "share_80_90": {
                    "keeper": kr["share_80_90"]["keeper"] if kr else None,
                    "screen": round(hist_share(ms, pm)[8] * 100, 1),
                    "campd": kr["share_80_90"]["campd"] if kr else None,
                },
                "share_90_100": {
                    "keeper": kr["share_90_100"]["keeper"] if kr else None,
                    "screen": round(hist_share(ms, pm)[9] * 100, 1),
                    "campd": kr["share_90_100"]["campd"] if kr else None,
                },
                "energy_gwh": {
                    "keeper": round(kr["energy_gwh"]["keeper"], 1) if kr else None,
                    "screen": round(ms.sum() / 1e3, 1),
                    "campd_gross": kr["energy_gwh"]["campd_gross"] if kr else None,
                },
                "peak_tranche": {
                    "h_keeper": kr["peak_tranche"]["h_keeper"] if kr else None,
                    "h_screen": int((pks.loc[pc].to_numpy() > 0.5).sum()),
                    "gwh_keeper": round(kr["peak_tranche"]["gwh_keeper"], 2)
                    if kr
                    else None,
                    "gwh_screen": round(pks.loc[pc].sum() / 1e3, 2),
                },
            }
        )
    rows.sort(key=lambda r: -r["pmax"])
    res["gates"]["plants"] = rows
    wall = [r for r in rows if r["plant"] in WALL_PLANTS]
    res["gates"]["wall_plants_direction"] = {
        "plants": list(WALL_PLANTS),
        "h_above_old_wall": {
            "keeper": ctl["wall_plants_direction"]["h_above_old_wall_keeper"],
            "screen": sum(r["h_above_old_wall"]["screen"] for r in wall),
            "campd": ctl["wall_plants_direction"]["h_above_old_wall_campd"],
        },
        "share_80_90_mean": {
            "keeper": ctl["wall_plants_direction"]["share_80_90_keeper"],
            "screen": round(
                float(np.mean([r["share_80_90"]["screen"] for r in wall])), 1
            ),
            "campd": ctl["wall_plants_direction"]["share_80_90_campd"],
        },
    }

    # ---- class energies, C1-2024 at the scorer's construction (REPORTED, never gated) --------------
    es = ds.groupby("klass_base").mw.sum() / 1e6
    ek_ = {k: v["keeper"] for k, v in ctl["class_energy_twh"].items()}
    res["gates"]["class_energy_twh"] = {
        k: {
            "keeper": ek_.get(k, 0.0),
            "screen": round(float(es.get(k, 0)), 3),
            "delta": round(float(es.get(k, 0)) - ek_.get(k, 0.0), 3),
        }
        for k in sorted(set(es.index) | set(ek_))
    }
    res["gates"]["gas_family_twh"] = {
        "keeper": ctl["gas_family_twh"]["keeper"],
        "screen": round(float(sum(es.get(k, 0) for k in GAS)), 3),
    }
    res["gates"]["peak_tranche_cc_regular"] = {
        "gwh_keeper": ctl["peak_tranche_cc_regular"]["gwh_keeper"],
        "gwh_screen": round(float(pks.to_numpy().sum()) / 1e3, 1),
        "tranche_hours_keeper": ctl["peak_tranche_cc_regular"]["tranche_hours_keeper"],
        "tranche_hours_screen": int((pks.to_numpy() > 0.5).sum()),
    }
    run = decode_run_js(
        (ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    )
    ypay = json.loads(json.dumps(run["years"][str(YEAR)]))
    bench = json.load(
        gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{YEAR}.json.gz")
    )["bench"]
    deltas = {k: v["delta"] for k, v in res["gates"]["class_energy_twh"].items()}
    for k, dlt in deltas.items():
        if k in ypay["gmModel"]:
            ypay["gmModel"][k] = float(ypay["gmModel"][k]) + dlt
    c1_k = {
        r["key"]: r
        for r in cv.score_fuelmix(YEAR, run["years"][str(YEAR)], bench, "NYISO")
    }
    c1_a = {r["key"]: r for r in cv.score_fuelmix(YEAR, ypay, bench, "NYISO")}
    c1 = {
        k: {
            "keeper": {
                f: c1_k[k].get(f)
                for f in ("status", "model", "actual", "share_pp", "magnitude")
            },
            "screen": {
                f: c1_a[k].get(f)
                for f in ("status", "model", "actual", "share_pp", "magnitude")
            },
        }
        for k in c1_k
        if k in ("CC_REGULAR", "CC_CHP", "ST_GAS", "CT_PEAKER", "CT_CHP", "ST_CHP")
    }
    c1["construction"] = (
        "calibration_verdict.score_fuelmix on the keeper's committed payload gmModel with the screen's P1 "
        "class-energy deltas applied (approximate: the payload's grid-delivered basis vs the P1 sum differ by a constant per class)"
    )
    res["gates"]["C1_2024_reported_not_gated"] = c1
    res["gates"]["C1_2024_reported_not_gated"]["flips"] = [
        k for k in c1_k if k in c1_a and c1_k[k]["status"] != c1_a[k]["status"]
    ]

    # ---- E-4 price companions ------------------------------------------------------------------
    sys_s = pd.read_parquet(B / "hourly" / f"system_{YEAR}.parquet")
    sys_k = pd.read_parquet(KEEPER / "hourly" / f"system_{YEAR}.parquet")
    res["gates"]["E4_price_companions_2024"] = price_companions(sys_s, sys_k)
    res["gates"]["E4_price_companions_2024"]["nyiso194_keeper_row_reproduced"] = ctl[
        "price_companions_2024"
    ]["keeper"]
    lm = ds.groupby("hour").lmp.mean()
    res["gates"]["mean_unit_lmp"] = {
        "keeper": ctl["mean_unit_lmp"]["keeper"],
        "screen": round(float(lm.mean()), 3),
    }

    dst = ROOT / "results/calibration/_nyiso195_screen_gates.json"
    dst.write_text(
        json.dumps(
            res,
            indent=1,
            default=lambda o: (
                float(o)
                if isinstance(o, np.floating)
                else (int(o) if isinstance(o, np.integer) else bool(o))
            ),
        )
    )
    gt = res["gates"]
    print(f"nyiso-195 screen  {a.bundle}  vs keeper committed control")
    print(f"  E-1 footprint: {gt['E1_footprint']}")
    print(f"  E-2 identity: {gt['E2_identity']}")
    e3 = gt["E3_direction"]
    print(
        f"  E-3 bins keeper {e3['keeper']}\n               screen {e3['screen']}\n               campd  {e3['campd']}"
    )
    print(
        f"      80-90 {e3['share_80_90']} fell={e3['share_80_90_fell']} toward_campd={e3['moved_toward_campd_80_90']}; 90-100 {e3['share_90_100']} rose={e3['share_90_100_rose']} toward_campd={e3['moved_toward_campd_90_100']}  STOP={e3['STOP']}"
    )
    print(f"  wall plants: {gt['wall_plants_direction']}")
    print(f"  peak tranche: {gt['peak_tranche_cc_regular']}")
    print(
        f"  class energy deltas: { {k: v['delta'] for k, v in gt['class_energy_twh'].items() if abs(v['delta']) > 0.005} }"
    )
    print(f"  gas family TWh: {gt['gas_family_twh']}")
    print(
        f"  C1-2024 (reported): { {k: (v['keeper']['magnitude'], v['keeper']['status'], '->', v['screen']['magnitude'], v['screen']['status']) for k, v in gt['C1_2024_reported_not_gated'].items() if isinstance(v, dict)} } flips {gt['C1_2024_reported_not_gated']['flips']}"
    )
    print(f"  E-4 price companions: {gt['E4_price_companions_2024']}")
    print(
        f"  {'plant':>6} {'pmax':>5} {'wall':>5} | {'>wall k':>7} {'>wall s':>7} {'campd':>6} | {'80-90 k':>7} {'s':>5} {'c':>5} | {'90-100 k':>8} {'s':>5} {'c':>5} | {'GWh k':>7} {'s':>7} {'campd':>7} | {'pk_h k':>6} {'s':>6}"
    )
    for r in rows[:14]:
        print(
            f"  {r['plant']:>6} {r['pmax']:5d} {r['old_wall_frac']:5.3f} | {str(r['h_above_old_wall']['keeper']):>7} {r['h_above_old_wall']['screen']:7d} {str(r['h_above_old_wall']['campd']):>6} | {str(r['share_80_90']['keeper']):>7} {r['share_80_90']['screen']:5.1f} {str(r['share_80_90']['campd']):>5} | {str(r['share_90_100']['keeper']):>8} {r['share_90_100']['screen']:5.1f} {str(r['share_90_100']['campd']):>5} | {str(r['energy_gwh']['keeper']):>7} {r['energy_gwh']['screen']:7.1f} {str(r['energy_gwh']['campd_gross']):>7} | {str(r['peak_tranche']['h_keeper']):>6} {r['peak_tranche']['h_screen']:6d}"
        )
    print(f"wrote {dst.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
