"""nyiso-194 PHASE 0 (NO LP) — the CC_REGULAR duct-burner peaking tranche: model
loading distribution vs CAMPD unit conduct, per plant, 2023–2025.

Owner ruling (2026-09-05, in session, verbatim): "tune the cc regular offer curve
up for the duct burner peaking tranche because it's merit order is wrong it runs
more often at lower CF and is running hot over 80% CF in all years". This probe
MEASURES that claim on the NEW keeper's committed P1 dispatch
(``results/calibration/nyiso192_astoria_panel/dispatch/<year>_P1.parquet``)
against CAMPD per-unit hourly gross load + heat input for the same plants, and
it measures the quantity an upward peak offer would be IDENTIFIED from (rule 13
``[R-MEASURED]`` / rule 21 ``[R-DOF]``): the plant's own measured incremental
heat rate in its top loading band (the duct-fired increment) relative to its
base-load band. It fits nothing to the residual, adopts nothing, and decides
no verdict — it is the zero-LP phase 0 rule 29 ``[R-SCREEN]`` requires before a
pre-registration.

Per plant-year it reports: model pmax and peak-tranche capacity, model vs
measured capacity factor, hours above 80 % / 90 % of the model pmax (both
sides), the loading histogram (10 % bins of pmax, share of online hours), the
model's peak-tranche hours and energy, and the measured band heat rates
(OLS slope of heat input on gross load in the 50–85 % base band and in the
90–100 % top band of the plant's own CAMPD p99.5 load, plus band-mean HR).

Usage: ``python scripts/probes/nyiso194_cc_peak_phase0.py [--bundle DIR]``.
Writes ``results/calibration/_nyiso194_cc_peak_phase0.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from market_sim.data.campd import load_campd_hourly  # noqa: E402

YEARS = (2023, 2024, 2025)
BINS = np.arange(0.0, 1.01, 0.1)
HI, VHI = 0.8, 0.9
BASE_BAND = (0.50, 0.85)  # of the plant's CAMPD p99.5 gross load
TOP_BAND = (0.90, 1.01)


def _tranche(unit_id: str) -> str:
    t = unit_id.rsplit("_", 1)[1]
    return "econ" if t.startswith("econc") else t


def _hist(mw: np.ndarray, cap: float) -> list[float]:
    on = mw[mw > 1.0]
    if on.size == 0:
        return [0.0] * (len(BINS) - 1)
    h, _ = np.histogram(np.clip(on / cap, 0, 1.0 - 1e-9), bins=BINS)
    return [round(float(x) / on.size, 4) for x in h]


def _band_hr(load: np.ndarray, heat: np.ndarray, p995: float, band: tuple[float, float]) -> dict:
    lo, hi = band[0] * p995, band[1] * p995
    m = (load >= lo) & (load < hi) & (heat > 0)
    if m.sum() < 50:
        return {"hours": int(m.sum()), "mean_hr": None, "slope_hr": None}
    x, y = load[m], heat[m]
    slope = float(np.polyfit(x, y, 1)[0])
    return {"hours": int(m.sum()), "mean_hr": round(float(y.sum() / x.sum()), 3), "slope_hr": round(slope, 3)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", default="results/calibration/nyiso192_astoria_panel")
    a = ap.parse_args()
    B = ROOT / a.bundle / "dispatch"
    out = {"session": "nyiso-194", "status": "PHASE 0 — NO LP, MEASUREMENT ONLY", "bundle": a.bundle,
           "basis": "model = keeper P1 dispatch per plant (sum of tranches), pmax = P1 fleet pmax; measured = CAMPD unit-level gross load (sum of units per EIA plant after CAMPD_UNIT_PLANT_REMAP), heat input MMBtu",
           "years": {}}
    for yr in YEARS:
        t = pq.read_table(B / f"{yr}_P1.parquet", columns=["unit_id", "plant_code", "klass_base", "hour", "mw"]).to_pandas()
        fl = pq.read_table(B / f"{yr}_P1_fleet.parquet").to_pandas().set_index("unit_id").pmax_mw
        cc = t[t.klass_base == "CC_REGULAR"].copy()
        cc["trk"] = cc.unit_id.map(_tranche)
        cap = cc.groupby(["plant_code", "unit_id"]).size().reset_index()[["plant_code", "unit_id"]]
        cap["pmax"] = cap.unit_id.map(fl)
        cap["trk"] = cap.unit_id.map(_tranche)
        capt = cap.pivot_table(index="plant_code", columns="trk", values="pmax", aggfunc="sum").fillna(0.0)
        for c in ("committed", "econ", "peak"):
            if c not in capt:
                capt[c] = 0.0
        plant = cc.groupby(["plant_code", "hour"]).mw.sum().unstack("hour")
        peak = cc[cc.trk == "peak"].groupby(["plant_code", "hour"]).mw.sum().unstack("hour")
        camp = load_campd_hourly(["NY"], [yr], prefer_unit_level=True)
        camp = camp[camp.plant_id.isin(plant.index)]
        g = camp.groupby(["plant_id", "hour_of_year"]).agg(gross=("gross_mw", "sum"), heat=("heat_mmbtu", "sum"))
        rows = []
        cls = {"pmax": 0.0, "peak_cap": 0.0, "model_twh": 0.0, "meas_twh": 0.0, "model_mwh_gt80": 0.0, "meas_mwh_gt80": 0.0,
               "model_mwh_gt90": 0.0, "meas_mwh_gt90": 0.0, "peak_twh": 0.0, "model_on_h": 0, "meas_on_h": 0,
               "model_h_gt80": 0, "meas_h_gt80": 0, "model_h_gt90": 0, "meas_h_gt90": 0, "meas_covered_plants": 0}
        for pc in plant.index:
            m = plant.loc[pc].to_numpy()
            pm = float(capt.loc[pc].sum())
            H = len(m)
            r = {"plant": int(pc), "pmax_mw": round(pm, 1), "committed_mw": round(capt.loc[pc, "committed"], 1),
                 "econ_mw": round(capt.loc[pc, "econ"], 1), "peak_mw": round(capt.loc[pc, "peak"], 1),
                 "pct_peak": round(100 * capt.loc[pc, "peak"] / pm, 1) if pm else None,
                 "model": {"cf": round(m.sum() / (pm * H), 4), "on_h": int((m > 1).sum()),
                           "h_gt80": int((m > HI * pm).sum()), "h_gt90": int((m > VHI * pm).sum()),
                           "mwh_gt80": round(float(m[m > HI * pm].sum())), "hist": _hist(m, pm),
                           "peak_h": int((peak.loc[pc].to_numpy() > 0.5).sum()) if pc in peak.index else 0,
                           "peak_gwh": round(float(peak.loc[pc].sum()) / 1e3, 2) if pc in peak.index else 0.0}}
            cls["pmax"] += pm; cls["peak_cap"] += capt.loc[pc, "peak"]; cls["model_twh"] += m.sum() / 1e6
            cls["model_mwh_gt80"] += m[m > HI * pm].sum(); cls["model_mwh_gt90"] += m[m > VHI * pm].sum()
            cls["model_on_h"] += int((m > 1).sum()); cls["model_h_gt80"] += r["model"]["h_gt80"]; cls["model_h_gt90"] += r["model"]["h_gt90"]
            cls["peak_twh"] += r["model"]["peak_gwh"] / 1e3
            if pc in g.index.get_level_values(0):
                gg = g.loc[pc].reindex(range(8760)).fillna(0.0)
                x = gg.gross.to_numpy(); hh = gg.heat.to_numpy()
                p995 = float(np.percentile(x[x > 1], 99.5)) if (x > 1).any() else 0.0
                r["measured"] = {"cf_gross_on_pmax": round(x.sum() / (pm * 8760), 4), "p995_gross_mw": round(p995, 1),
                                 "p995_over_pmax": round(p995 / pm, 3) if pm else None, "on_h": int((x > 1).sum()),
                                 "h_gt80": int((x > HI * pm).sum()), "h_gt90": int((x > VHI * pm).sum()),
                                 "h_gt80_own_p995": int((x > HI * p995).sum()), "h_gt90_own_p995": int((x > VHI * p995).sum()),
                                 "mwh_gt80": round(float(x[x > HI * pm].sum())), "hist": _hist(x, pm),
                                 "hr_base_band": _band_hr(x, hh, p995, BASE_BAND), "hr_top_band": _band_hr(x, hh, p995, TOP_BAND)}
                hb, ht = r["measured"]["hr_base_band"], r["measured"]["hr_top_band"]
                r["measured"]["top_over_base_slope"] = round(ht["slope_hr"] / hb["slope_hr"], 3) if ht["slope_hr"] and hb["slope_hr"] else None
                r["measured"]["top_over_base_mean"] = round(ht["mean_hr"] / hb["mean_hr"], 3) if ht["mean_hr"] and hb["mean_hr"] else None
                cls["meas_twh"] += x.sum() / 1e6; cls["meas_mwh_gt80"] += x[x > HI * pm].sum(); cls["meas_mwh_gt90"] += x[x > VHI * pm].sum()
                cls["meas_on_h"] += int((x > 1).sum()); cls["meas_h_gt80"] += r["measured"]["h_gt80"]; cls["meas_h_gt90"] += r["measured"]["h_gt90"]
                cls["meas_covered_plants"] += 1
            else:
                r["measured"] = None
            rows.append(r)
        rows.sort(key=lambda r: -r["pmax_mw"])
        cls = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in cls.items()}
        cls["n_plants"] = len(rows)
        out["years"][str(yr)] = {"class": cls, "plants": rows}
        print(f"\n=== {yr}: CC_REGULAR pmax {cls['pmax']:.0f} MW (peak tranche {cls['peak_cap']:.0f} MW); energy model {cls['model_twh']:.2f} vs CAMPD gross {cls['meas_twh']:.2f} TWh ({cls['meas_covered_plants']}/{cls['n_plants']} plants covered)")
        print(f"    MWh delivered above 80% of pmax: model {cls['model_mwh_gt80']/1e6:.2f} vs measured {cls['meas_mwh_gt80']/1e6:.2f} TWh; above 90%: {cls['model_mwh_gt90']/1e6:.2f} vs {cls['meas_mwh_gt90']/1e6:.2f} TWh")
        print(f"    plant-hours >80%: model {cls['model_h_gt80']} vs measured {cls['meas_h_gt80']}; >90%: {cls['model_h_gt90']} vs {cls['meas_h_gt90']}; online plant-hours {cls['model_on_h']} vs {cls['meas_on_h']}; peak-tranche energy {cls['peak_twh']:.3f} TWh")
        print(f"    {'plant':>6} {'pmax':>5} {'pk%':>5} | {'CF m':>5} {'CF c':>5} | {'>80 m':>6} {'>80 c':>6} | {'>90 m':>6} {'>90 c':>6} | {'on m':>5} {'on c':>5} | {'pk_h':>5} | {'HRbase':>6} {'HRtop':>6} {'top/base':>8} {'p995/pmax':>9}")
        for r in rows:
            ms = r["measured"] or {}
            hb = (ms.get("hr_base_band") or {}).get("mean_hr"); ht = (ms.get("hr_top_band") or {}).get("mean_hr")

            def f(v, w=6, d=3):
                return f"{v:{w}.{d}f}" if isinstance(v, float) else f"{str(v) if v is not None else '-':>{w}}"

            print(f"    {r['plant']:>6} {r['pmax_mw']:5.0f} {r['pct_peak'] or 0:5.1f} | {r['model']['cf']:5.3f} {f(ms.get('cf_gross_on_pmax'),5)} | {r['model']['h_gt80']:6d} {f(ms.get('h_gt80'),6)} | {r['model']['h_gt90']:6d} {f(ms.get('h_gt90'),6)} | {r['model']['on_h']:5d} {f(ms.get('on_h'),5)} | {r['model']['peak_h']:5d} | {f(hb,6,2)} {f(ht,6,2)} {f(ms.get('top_over_base_slope'),8)} {f(ms.get('p995_over_pmax'),9)}")
    dst = ROOT / "results/calibration/_nyiso194_cc_peak_phase0.json"
    def _py(o):
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        raise TypeError(type(o))

    dst.write_text(json.dumps(out, indent=1, default=_py))
    print(f"\nwrote {dst.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
