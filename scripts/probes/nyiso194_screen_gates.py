"""nyiso-194 — evaluate the PREREG §2 screen gates for one 2024 screen bundle.

Differences a one-year screen bundle (Arm S ``cc_duct_peaking_cap_pct=8.0`` or
Arm D ``CC_REGULAR.peak 2.50``) against the keeper's committed 2024 dispatch
(``results/calibration/nyiso192_astoria_panel``, rule 29(b) form 4 — the keeper
IS the control) and against CAMPD conduct, on exactly the pre-registered gates:
footprint (S-1 / D-1), the cap identity (S-2), the direction of the loading
distribution (S-3 / D-2), and the 2024 load-bearing companions (S-4: gas-family
volume, load-weighted mean RT price, monthly price NRMSE — computed here from the
system parquet against MIS RT zonal LBMP with the model's own zonal demand as
weights, an APPROXIMATION of the scorer's C2/C3a/C3b used only as a STOP gate;
the full-span registration is the scored record). Structural, stop-only;
nothing here contributes to a determination.

Usage: ``python scripts/probes/nyiso194_screen_gates.py <screen_bundle> [--arm S|D]``.
Writes ``results/calibration/_nyiso194_screen_gates_<arm>.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/probes"))
sys.path.insert(0, str(ROOT / "scripts/data"))
from market_sim.data.campd import load_campd_hourly  # noqa: E402
from market_sim.data.fleet.campd_bins import cc_duct_peaking_pct  # noqa: E402

KEEPER = ROOT / "results/calibration/nyiso192_astoria_panel"
YEAR = 2024
BINS = np.arange(0.0, 1.01, 0.1)
GAS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
WALL_PLANTS = (57664, 56940, 54574, 50292)  # wall inside the 80-90 % bin (PREREG §1)


def _tr(u: str) -> str:
    t = u.rsplit("_", 1)[1]
    return "econ" if t.startswith("econc") else t


def load(bundle: Path):
    d = pq.read_table(bundle / "dispatch" / f"{YEAR}_P1.parquet",
                      columns=["unit_id", "plant_code", "klass_base", "zone", "hour", "mw", "lmp"]).to_pandas()
    fl = pq.read_table(bundle / "dispatch" / f"{YEAR}_P1_fleet.parquet").to_pandas().set_index("unit_id").pmax_mw
    sysp = pd.read_parquet(bundle / "hourly" / f"system_{YEAR}.parquet") if (bundle / "hourly" / f"system_{YEAR}.parquet").exists() else None
    return d, fl, sysp


def plant_frames(d: pd.DataFrame, fl: pd.Series):
    cc = d[d.klass_base == "CC_REGULAR"].copy()
    cc["trk"] = cc.unit_id.map(_tr)
    units = cc.drop_duplicates("unit_id")[["unit_id", "plant_code", "trk"]].copy()
    units["pmax"] = units.unit_id.map(fl)
    cap = units.pivot_table(index="plant_code", columns="trk", values="pmax", aggfunc="sum").fillna(0.0)
    for c in ("committed", "econ", "peak"):
        if c not in cap.columns:
            cap[c] = 0.0
    plant = cc.groupby(["plant_code", "hour"]).mw.sum().unstack("hour")
    peak = cc[cc.trk == "peak"].groupby(["plant_code", "hour"]).mw.sum().unstack("hour").reindex(plant.index).fillna(0.0)
    return cc, cap, plant, peak


def hist_share(mw: np.ndarray, cap: float) -> np.ndarray:
    on = mw[mw > 1.0]
    if on.size == 0:
        return np.zeros(len(BINS) - 1)
    h, _ = np.histogram(np.clip(on / cap, 0, 1 - 1e-9), bins=BINS)
    return h / on.size


def class_bins(plant: pd.DataFrame, cap: pd.DataFrame) -> np.ndarray:
    tot = np.zeros(len(BINS) - 1)
    for pc in plant.index:
        if pc == 2500:
            continue
        m = plant.loc[pc].to_numpy(); pm = float(cap.loc[pc].sum())
        on = int((m > 1).sum())
        tot += hist_share(m, pm) * on * pm
    return tot / tot.sum()


def price_gates(sysp_s, sysp_k):
    from _nyiso192_common import actual_zone_price
    px = actual_zone_price(YEAR)
    out = {}
    for tag, sp in (("screen", sysp_s), ("keeper", sysp_k)):
        p = sp.pivot(index="hour", columns="zone", values="price").iloc[:8760]
        w = sp.pivot(index="hour", columns="zone", values="demand").iloc[:8760]
        zones = [z for z in p.columns if z in px.columns]
        p, w, a = p[zones], w[zones], px[zones].iloc[:8760]
        w = w.clip(lower=0)
        lw_model = float((p * w).sum().sum() / w.sum().sum()); lw_act = float((a.to_numpy() * w.to_numpy()).sum() / w.sum().sum())
        mo = pd.date_range("2023-01-01", periods=8760, freq="h").month
        pm = p.groupby(mo).mean(); am = pd.DataFrame(a.to_numpy(), columns=zones).groupby(mo).mean()
        nrmse = float(np.sqrt(((pm.to_numpy() - am.to_numpy()) ** 2).mean()) / am.to_numpy().mean())
        out[tag] = {"lw_mean_model": round(lw_model, 3), "lw_mean_actual_same_weights": round(lw_act, 3),
                    "c3a_like_pct": round(100 * (lw_model / lw_act - 1), 2), "c3b_like_monthly_nrmse": round(nrmse, 4)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle")
    ap.add_argument("--arm", default="S")
    a = ap.parse_args()
    B = ROOT / a.bundle
    ds, fls, sys_s = load(B)
    dk, flk, sys_k = load(KEEPER)
    res = {"arm": a.arm, "screen_bundle": a.bundle, "control": "keeper committed 2024 (form 4)", "gates": {}}
    # --- footprint: tranche pmax diffs
    fd = pd.concat([flk.rename("keeper"), fls.rename("screen")], axis=1).fillna(0.0)
    fd["d"] = fd.screen - fd.keeper
    moved = fd[fd.d.abs() > 1e-6]
    kl = dk.drop_duplicates("unit_id").set_index("unit_id").klass_base
    moved = moved.assign(klass=moved.index.map(kl), plant=moved.index.map(dk.drop_duplicates("unit_id").set_index("unit_id").plant_code))
    duct = cc_duct_peaking_pct()
    res["gates"]["footprint_fleet"] = {
        "units_with_pmax_change": int(len(moved)),
        "plants": sorted({int(p) for p in moved.plant.dropna()}),
        "all_changed_plants_have_860_gap_gt_8": bool(all((duct.get(int(p)) or 0) > 8 for p in moved.plant.dropna())) if len(moved) else None,
        "classes": sorted(set(moved.klass.dropna())),
        "rows": [{"unit": u, "keeper": round(r.keeper, 2), "screen": round(r.screen, 2)} for u, r in moved.iterrows()][:80],
    }
    ccs, caps, ps, pks = plant_frames(ds, fls)
    cck, capk, pk_, pkk = plant_frames(dk, flk)
    # --- S-2 identity at capped CC_REGULAR plants
    ident = []
    for pc in caps.index:
        gap = duct.get(int(pc)) or 0.0
        if gap > 8 and pc in capk.index and abs(caps.loc[pc, "peak"] - capk.loc[pc, "peak"]) > 1e-6:
            grid = float(caps.loc[pc].sum())
            ident.append({"plant": int(pc), "gap_860": gap, "peak_mw_keeper": round(capk.loc[pc, "peak"], 1), "peak_mw_screen": round(caps.loc[pc, "peak"], 1),
                          "peak_pct_of_plant_screen": round(100 * caps.loc[pc, "peak"] / grid, 2)})
    res["gates"]["identity_cap8"] = ident
    # --- direction: class bins, per-plant hours, peak energy
    cb_s, cb_k = class_bins(ps, caps), class_bins(pk_, capk)
    camp = load_campd_hourly(["NY"], [YEAR], prefer_unit_level=True)
    camp = camp[camp.plant_id.isin(ps.index)]
    g = camp.groupby(["plant_id", "hour_of_year"]).gross_mw.sum()
    tot = np.zeros(len(BINS) - 1)
    for pc in ps.index:
        if pc == 2500 or pc not in g.index.get_level_values(0):
            continue
        x = g.loc[pc].reindex(range(8760)).fillna(0).to_numpy(); pm = float(capk.loc[pc].sum())
        tot += hist_share(x, pm) * int((x > 1).sum()) * pm
    cb_c = tot / tot.sum()
    def s(v): return [round(float(x) * 100, 1) for x in v]
    res["gates"]["class_loading_bins_pct"] = {"bins": "0-10 .. 90-100 % of pmax, MW-weighted share of online plant-hours (2500 excluded)",
                                             "keeper": s(cb_k), "screen": s(cb_s), "campd": s(cb_c),
                                             "share_80_90": {"keeper": round(cb_k[8] * 100, 2), "screen": round(cb_s[8] * 100, 2), "campd": round(cb_c[8] * 100, 2)},
                                             "share_90_100": {"keeper": round(cb_k[9] * 100, 2), "screen": round(cb_s[9] * 100, 2), "campd": round(cb_c[9] * 100, 2)},
                                             "moved_toward_campd_80_90": bool(abs(cb_s[8] - cb_c[8]) < abs(cb_k[8] - cb_c[8])),
                                             "moved_toward_campd_90_100": bool(abs(cb_s[9] - cb_c[9]) < abs(cb_k[9] - cb_c[9]))}
    rows = []
    for pc in ps.index:
        ms, mk = ps.loc[pc].to_numpy(), pk_.loc[pc].to_numpy(); pm = float(capk.loc[pc].sum())
        old_wall = 1 - capk.loc[pc, "peak"] / pm if pm else 1.0
        x = g.loc[pc].reindex(range(8760)).fillna(0).to_numpy() if pc in g.index.get_level_values(0) else None
        rows.append({"plant": int(pc), "pmax": round(pm), "old_wall_frac": round(old_wall, 3),
                     "h_above_old_wall": {"keeper": int((mk > old_wall * pm + 0.5).sum()), "screen": int((ms > old_wall * pm + 0.5).sum()), "campd": int((x > old_wall * pm).sum()) if x is not None else None},
                     "h_gt80": {"keeper": int((mk > 0.8 * pm).sum()), "screen": int((ms > 0.8 * pm).sum()), "campd": int((x > 0.8 * pm).sum()) if x is not None else None},
                     "h_gt90": {"keeper": int((mk > 0.9 * pm).sum()), "screen": int((ms > 0.9 * pm).sum()), "campd": int((x > 0.9 * pm).sum()) if x is not None else None},
                     "share_80_90": {"keeper": round(hist_share(mk, pm)[8] * 100, 1), "screen": round(hist_share(ms, pm)[8] * 100, 1), "campd": round(hist_share(x, pm)[8] * 100, 1) if x is not None else None},
                     "share_90_100": {"keeper": round(hist_share(mk, pm)[9] * 100, 1), "screen": round(hist_share(ms, pm)[9] * 100, 1), "campd": round(hist_share(x, pm)[9] * 100, 1) if x is not None else None},
                     "energy_gwh": {"keeper": round(mk.sum() / 1e3, 1), "screen": round(ms.sum() / 1e3, 1), "campd_gross": round(x.sum() / 1e3, 1) if x is not None else None},
                     "peak_tranche": {"h_keeper": int((pkk.loc[pc].to_numpy() > 0.5).sum()), "h_screen": int((pks.loc[pc].to_numpy() > 0.5).sum()),
                                      "gwh_keeper": round(pkk.loc[pc].sum() / 1e3, 2), "gwh_screen": round(pks.loc[pc].sum() / 1e3, 2)}})
    rows.sort(key=lambda r: -r["pmax"])
    res["gates"]["plants"] = rows
    wall = [r for r in rows if r["plant"] in WALL_PLANTS]
    res["gates"]["wall_plants_direction"] = {
        "plants": list(WALL_PLANTS),
        "h_above_old_wall_keeper": sum(r["h_above_old_wall"]["keeper"] for r in wall), "h_above_old_wall_screen": sum(r["h_above_old_wall"]["screen"] for r in wall),
        "h_above_old_wall_campd": sum(r["h_above_old_wall"]["campd"] or 0 for r in wall),
        "share_80_90_keeper": round(np.mean([r["share_80_90"]["keeper"] for r in wall]), 1), "share_80_90_screen": round(np.mean([r["share_80_90"]["screen"] for r in wall]), 1),
        "share_80_90_campd": round(np.mean([r["share_80_90"]["campd"] or 0 for r in wall]), 1)}
    # class energy + gas family volume (C2-like) + peak energy
    def cls_energy(d):
        return d.groupby("klass_base").mw.sum() / 1e6
    es, ek = cls_energy(ds), cls_energy(dk)
    res["gates"]["class_energy_twh"] = {k: {"keeper": round(float(ek.get(k, 0)), 3), "screen": round(float(es.get(k, 0)), 3), "delta": round(float(es.get(k, 0) - ek.get(k, 0)), 3)} for k in sorted(set(es.index) | set(ek.index))}
    res["gates"]["gas_family_twh"] = {"keeper": round(float(sum(ek.get(k, 0) for k in GAS)), 3), "screen": round(float(sum(es.get(k, 0) for k in GAS)), 3)}
    res["gates"]["peak_tranche_cc_regular"] = {"gwh_keeper": round(float(pkk.to_numpy().sum()) / 1e3, 1), "gwh_screen": round(float(pks.to_numpy().sum()) / 1e3, 1),
                                               "tranche_hours_keeper": int((pkk.to_numpy() > 0.5).sum()), "tranche_hours_screen": int((pks.to_numpy() > 0.5).sum())}
    # price companions
    if sys_s is not None and sys_k is not None:
        res["gates"]["price_companions_2024"] = price_gates(sys_s, sys_k)
        lm = ds.groupby("hour").lmp.mean(); lk = dk.groupby("hour").lmp.mean()
        res["gates"]["mean_unit_lmp"] = {"keeper": round(float(lk.mean()), 3), "screen": round(float(lm.mean()), 3)}
    dst = ROOT / f"results/calibration/_nyiso194_screen_gates_{a.arm}.json"
    dst.write_text(json.dumps(res, indent=1, default=lambda o: float(o) if isinstance(o, np.floating) else int(o)))
    gt = res["gates"]
    print(f"ARM {a.arm}  {a.bundle}")
    print(f"  footprint: {gt['footprint_fleet']['units_with_pmax_change']} tranche pmax changes at plants {gt['footprint_fleet']['plants']} classes {gt['footprint_fleet']['classes']} all_gap>8={gt['footprint_fleet']['all_changed_plants_have_860_gap_gt_8']}")
    print(f"  identity (cap8): {[(i['plant'], i['peak_pct_of_plant_screen']) for i in gt['identity_cap8']]}")
    cl = gt["class_loading_bins_pct"]
    print(f"  class bins keeper {cl['keeper']}\n             screen {cl['screen']}\n             campd  {cl['campd']}")
    print(f"  80-90 share keeper/screen/campd {cl['share_80_90']}  toward_campd={cl['moved_toward_campd_80_90']}; 90-100 {cl['share_90_100']} toward_campd={cl['moved_toward_campd_90_100']}")
    print(f"  wall plants: {gt['wall_plants_direction']}")
    print(f"  peak tranche: {gt['peak_tranche_cc_regular']}")
    print(f"  class energy deltas: { {k: v['delta'] for k, v in gt['class_energy_twh'].items() if abs(v['delta']) > 0.005} }")
    print(f"  gas family TWh: {gt['gas_family_twh']}")
    if "price_companions_2024" in gt:
        print(f"  price companions: {gt['price_companions_2024']}")
    print(f"wrote {dst.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
