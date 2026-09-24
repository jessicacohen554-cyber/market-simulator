"""SOCO-64 phase 0 (ZERO LP): measured no-load, start conduct and start cost for SOCO,
and the reach of a start-cost carrier on the keeper legs.

Builds the MEASURED evidence case for ``tranche_startup_amortization`` (G for
SOCO, FINDING-soco-53 §2.4) and states whether it answers the G reason. Nothing
is armed, no field is added, no LP is solved. Reuses ``_soco63_phase0`` (unit
class map, fleet arrays, ``year_frames``, ``greedy``, ``rescore``) unchanged.

EX-ANTE DECLARATIONS (written before any reach number was computed):

* **No-load heat input (a).** ``derive_unit_bands``' normalized-quadratic fit
  ``heatInput = c2 x^2 + c1 x + c0`` with ``x = (P - LSL)/(HSL - LSL)`` puts
  ``c0`` at P = LSL, NOT at P = 0, so ``c0`` is the heat input at minimum stable
  load, not the no-load term. The no-load heat input is the SAME fitted curve
  evaluated at P = 0 (``x0 = -LSL/range``). Reported alongside: the literal
  ``c0`` (at LSL) and a linear IO intercept, as checks only. Share =
  no-load / (HSL x the unit's own average HR ``hr_gross``).
* **Start cost (c).** The NREL/SR-5500-55433 ``BIN_STARTUP_COST_PER_MW`` table
  the model already carries (CT 20 / ST 35 / CC 50 / coal 100 $/MW). Reason:
  it is the one registered start-cost constant, already on the CT and CC
  ``_committed`` tranches, so the same unit is never priced at two start costs
  (rule 19), and it includes the wear component a fuel-only construction
  omits. The CEMS fuel-only start (measured warm-up heat) is REPORTED as a
  lower bound, never selected.
* **Amortization horizon (d).** The legs carry only P1 dispatch, not P0, so the
  horizon is the control's own P1 tranche run length per month with
  ``compute_monthly_markup``'s exact semantics (on = mw > 5 % pmax; no run in
  the month -> startup / 1). Sensitivity: the v3 measured ceiling
  (min(model run, CEMS plant-class median)).
* **Arms.** A = non-selective: every econ*/peak* tranche of CT_PEAKER, ST_GAS,
  CC_REGULAR and COAL (every class with conduct data). B = the registered
  field's own scope (CT econ + peak, CC peak). J = A plus SOCO-63's incremental
  bands with the measured no-load share re-added on the econ bands
  (``marg + nl_share``). Z (added after the keeper-mc census, before its reach
  was computed) = the G cell applied consistently: remove the NREL start markup
  the keeper ALREADY charges on CT/CC ``_committed``. ``_committed`` tranches are untouched in every arm
  (CT/CC already pay; coal is exempt under coal_warm_committed; ST is owned by
  soco_gas_st_campaign_commitment / gas_st_startup_cost).

Subcommands: ``noload --out-csv``, ``conduct --out-csv``, ``reach``, ``c4``.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.probes import _soco63_phase0 as s63  # noqa: E402

YEARS = s63.YEARS
CLASSES = ("CT_PEAKER", "ST_GAS", "CC_REGULAR", "COAL")
SHORT_RUN_H = 12


def _deriver():
    spec = importlib.util.spec_from_file_location(
        "dmhr", str(_ROOT / "scripts/data/derive_campd_marginal_hr.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _wq(v, w, q):
    v, w = np.asarray(v, float), np.asarray(w, float)
    m = np.isfinite(v) & np.isfinite(w) & (w > 0)
    return _deriver()._wquantile(v[m], w[m], q) if m.any() else float("nan")


def noload(out_csv: Path) -> pd.DataFrame:
    """(a) per-unit no-load heat input and its share of full-load input, pooled 2023-2025."""
    dm = _deriver()
    cmap = s63.unit_class_map()
    camp = dm.load_campd("SOCO", YEARS)
    camp["unitId"] = camp["unitId"].astype(str)
    camp = camp.merge(cmap, left_on=["facilityId", "unitId"],
                      right_on=["plant_code", "unit_id"], how="inner")
    rows = []
    for (p, u, cls), g in camp.groupby(["plant_code", "unit_id", "cls"]):
        gl, hi = g.grossLoad.to_numpy(float), g.heatInput.to_numpy(float)
        if len(gl) < dm.MIN_UNIT_HOURS:
            continue
        lsl, hsl = np.percentile(gl, dm.LSL_PCT), np.percentile(gl, dm.HSL_PCT)
        if hsl <= lsl:
            continue
        rng = hsl - lsl
        c2, c1, c0 = np.polyfit((gl - lsl) / rng, hi, 2)
        x0 = -lsl / rng
        nl_q = c2 * x0 * x0 + c1 * x0 + c0
        b1, a_lin = np.polyfit(gl, hi, 1)
        hr_own = float(g.hr_gross.iloc[0])
        full = hsl * hr_own
        bands = dm.derive_unit_bands(g, hr_own) or {}
        rows.append({"plant_code": p, "unit_id": u, "cls": cls, "hsl": hsl, "lsl": lsl,
                     "lsl_frac": lsl / hsl, "hr_own": hr_own, "n_h": len(gl),
                     "nl_quad": nl_q, "c0_at_lsl": c0, "nl_lin": a_lin,
                     "share_quad": nl_q / full, "share_c0": c0 / full, "share_lin": a_lin / full,
                     "marg_lo": bands.get("marg_econ_low"), "marg_hi": bands.get("marg_econ_high"),
                     "avg_comm": bands.get("avg_committed")})
    d = pd.DataFrame(rows)
    d["joint_lo"] = d.marg_lo + d.share_quad
    d["joint_hi"] = d.marg_hi + d.share_quad
    d.to_csv(out_csv, index=False)
    print("no-load share of full-load heat input, cap-weighted by HSL [p25 p50 p75]")
    for cls, g in d.groupby("cls"):
        w = g.hsl
        f = lambda c: "[" + " ".join(f"{_wq(g[c], w, q):.3f}" for q in (.25, .5, .75)) + "]"  # noqa: E731
        print(f"  {cls:11s} n={len(g):3d} quad@P0 {f('share_quad')}  c0@LSL {f('share_c0')}"
              f"  linear {f('share_lin')}  neg_quad {int((g.share_quad < 0).sum())}"
              f"  nl_quad MMBtu/h p50 {_wq(g.nl_quad, w, .5):.1f}  LSL/HSL p50 {_wq(g.lsl_frac, w, .5):.2f}"
              f"  joint lo/hi p50 {_wq(g.joint_lo, w, .5):.3f}/{_wq(g.joint_hi, w, .5):.3f}")
    print(f"wrote {out_csv}")
    return d


def _runs(on: np.ndarray) -> list[tuple[int, int]]:
    from market_sim.model.commitment import find_runs
    return find_runs(on)


def conduct(out_csv: Path, fuel_usd: float) -> pd.DataFrame:
    """(b)+(c) CEMS opTime conduct per unit-year: starts, run lengths, warm-up heat."""
    from market_sim.data.campd import states_for_iso
    cmap = s63.unit_class_map()
    rows = []
    for y in YEARS:
        fr = []
        for st in states_for_iso("SOCO"):
            p = _ROOT / f"data/raw/campd-unit-level/{st}_{y}.parquet"
            if p.exists():
                fr.append(pd.read_parquet(p, columns=["facilityId", "unitId", "date", "hour",
                                                      "opTime", "grossLoad", "heatInput"]))
        c = pd.concat(fr)
        c["facilityId"] = c.facilityId.astype(int)
        c["unitId"] = c.unitId.astype(str)
        c = c.merge(cmap, left_on=["facilityId", "unitId"], right_on=["plant_code", "unit_id"])
        c = c.sort_values(["plant_code", "unit_id", "date", "hour"])
        for (p, u, cls), g in c.groupby(["plant_code", "unit_id", "cls"]):
            on = g.opTime.fillna(0).to_numpy() > 0
            gl = g.grossLoad.fillna(0).to_numpy(float)
            hi = g.heatInput.fillna(0).to_numpy(float)
            runs = _runs(on)
            if not runs:
                rows.append({"year": y, "plant_code": p, "unit_id": u, "cls": cls, "starts": 0})
                continue
            steady = gl[on & (g.opTime.fillna(0).to_numpy() >= 0.95) & (gl > 0)]
            lsl = np.percentile(steady, 3) if len(steady) > 20 else np.nan
            hsl = np.percentile(steady, 97) if len(steady) > 20 else np.nan
            L = np.array([e - s for s, e in runs])
            E = np.array([gl[s:e].sum() for s, e in runs])
            warm_h, warm_q = [], []
            for s, e in runs:
                k = 0
                while s + k < e and not (gl[s + k] >= lsl):
                    k += 1
                warm_h.append(k)
                warm_q.append(hi[s:s + k].sum() - 0.0)
            rows.append({"year": y, "plant_code": p, "unit_id": u, "cls": cls,
                         "starts": len(runs), "run_med": float(np.median(L)),
                         "run_mean": float(L.mean()), "on_h": int(L.sum()),
                         "mwh": float(gl.sum()), "mwh_short": float(E[L < SHORT_RUN_H].sum()),
                         "hsl": hsl, "lsl": lsl, "warm_h_med": float(np.median(warm_h)),
                         "warm_mmbtu_med": float(np.median(warm_q)),
                         "warm_mmbtu_per_mw": float(np.median(warm_q)) / hsl if hsl else np.nan})
    d = pd.DataFrame(rows)
    d.to_csv(out_csv, index=False)
    nrel = {"CT_PEAKER": 20.0, "ST_GAS": 35.0, "CC_REGULAR": 50.0, "COAL": 100.0}
    print(f"CEMS conduct (opTime>0 runs), fuel-only start at ${fuel_usd:.2f}/MMBtu")
    for cls in CLASSES:
        g = d[(d.cls == cls) & (d.starts > 0)]
        w = g.hsl.fillna(0)
        print(f"  {cls:11s} unit-yrs {len(g):3d}  starts/unit-yr p50 {_wq(g.starts, w, .5):6.1f}"
              f"  run_med p50 {_wq(g.run_med, w, .5):6.1f} h  mean-run p50 {_wq(g.run_mean, w, .5):6.1f}"
              f"  energy in runs<{SHORT_RUN_H}h {100 * g.mwh_short.sum() / g.mwh.sum():5.1f}%"
              f"  warm-up p50 {_wq(g.warm_h_med, w, .5):.1f} h"
              f"  warm heat {_wq(g.warm_mmbtu_per_mw, w, .5):.2f} MMBtu/MW"
              f" -> fuel-only ${fuel_usd * _wq(g.warm_mmbtu_per_mw, w, .5):.1f}/MW vs NREL ${nrel[cls]:.0f}/MW")
        for y in YEARS:
            gy = g[g.year == y]
            print(f"      {y}: starts total {int(gy.starts.sum()):5d}  units {len(gy):3d}"
                  f"  energy<{SHORT_RUN_H}h {100 * gy.mwh_short.sum() / max(gy.mwh.sum(), 1):5.1f}%")
    print(f"wrote {out_csv}")
    return d


def model_runs(year: int) -> pd.DataFrame:
    """Control P1 tranche run lengths (compute_monthly_markup semantics), per tranche-month."""
    from market_sim.model.commitment import _month_bounds
    meta, mw, cap, _mc, _f = s63.year_frames(year, FLEET / f"fleet_{year}.npz")
    pmax = np.nanmax(np.nan_to_num(cap), axis=1)
    mw = np.nan_to_num(mw)
    out = []
    for i, r in meta.iterrows():
        for m, (a, b) in enumerate(_month_bounds(mw.shape[1])):
            rn = _runs(mw[i, a:b] > 0.05 * pmax[i])
            out.append({"i": i, "group": r.group, "suffix": r.suffix, "plant": r.plant, "month": m,
                        "a": a, "b": b, "avg_run": float(np.mean([e - s for s, e in rn])) if rn else 0.0,
                        "n_runs": len(rn), "mwh": mw[i, a:b].sum()})
    return pd.DataFrame(out)


NREL = {"CT_PEAKER": 20.0, "ST_GAS": 35.0, "CC_REGULAR": 50.0, "COAL": 100.0}
SCOPES = {"A": {c: ("econlo", "econhi", "peak") for c in CLASSES},
          "B": {"CT_PEAKER": ("econlo", "econhi", "peak"), "CC_REGULAR": ("peak",)}}
FLEET = Path(".")


def markup(year: int, scope: str, scale: float, v3: pd.DataFrame | None) -> np.ndarray:
    """(n_tranche, T) $/MWh start amortization on the arm's tranches, control P1 horizon."""
    meta, mw, _cap, _mc, _f = s63.year_frames(year, FLEET / f"fleet_{year}.npz")
    mr = model_runs(year)
    med = ({(int(r.plant_code), r.cls): r.run_med for r in v3.itertuples()} if v3 is not None else {})
    out = np.zeros(mw.shape)
    for r in mr.itertuples():
        grp = meta.at[r.i, "group"]
        suf = meta.at[r.i, "suffix"]
        if grp not in SCOPES[scope] or not any(suf.startswith(s) for s in SCOPES[scope][grp]):
            continue
        S = NREL[grp] * scale
        h = r.avg_run
        if v3 is not None:
            mh = med.get((int(r.plant), grp), 0.0)
            if mh > 0:
                h = min(h, mh) if h > 0 else mh
        out[r.i, r.a:r.b] = S / max(h, 1.0)
    return out


def arm_mc(year: int, arm: str, scale: float, v3, joint_csv: Path | None):
    """Control and arm hourly offer for the restack set."""
    meta, mw, cap, mc, fuel = s63.year_frames(year, FLEET / f"fleet_{year}.npz")
    if arm == "Z":
        # Z = the G cell applied CONSISTENTLY: strip the live NREL start markup the
        # keeper already charges on CT/CC _committed (solved mc minus fleet mc_base).
        f = np.load(FLEET / f"fleet_{year}.npz")
        fidx = {x: i for i, x in enumerate(f["ids"])}
        base = f["mc_base"][[fidx[i] for i in meta.unit_id], : mc.shape[1]]
        m = (meta.group.isin(("CT_PEAKER", "CC_REGULAR")) & (meta.suffix == "committed")).values
        mc1 = mc.copy()
        mc1[m] = base[m]
        return meta, mw, cap, mc, mc1
    add = markup(year, "A" if arm == "J" else arm, scale, v3)
    mc1 = mc + add
    if arm == "J":
        j = pd.read_csv(joint_csv)
        cl = {}
        for c, g in j.groupby("cls"):
            cl[c] = {"committed": _wq(g.avg_comm, g.hsl, .5), "econlo": _wq(g.joint_lo, g.hsl, .5),
                     "econhi": _wq(g.joint_hi, g.hsl, .5)}
        mult = np.array([cl.get(r.group, {}).get(r.suffix, 1.0) for r in meta.itertuples()])
        mc1 = mc1 + (mult[:, None] - 1.0) * fuel
    return meta, mw, cap, mc, mc1


def reach(arm: str, scale: float, v3csv: Path | None, joint_csv: Path | None) -> None:
    """(d) greedy restack, arm minus greedy control; C1 rescore; per-plant F; distance A."""
    from scripts.probes._soco62_phase0 import bench_plant_twh
    v3 = None
    if v3csv is not None:
        c = pd.read_csv(v3csv)
        c = c[c.starts > 0]
        v3 = c.groupby(["plant_code", "cls"]).run_med.median().reset_index()
    print(f"\n######## arm {arm}  start x{scale}  horizon {'v3 measured ceiling' if v3 is not None else 'control P1 (v2)'}")
    deltas = {}
    for year in YEARS:
        meta, mw, cap, mc, mc1 = arm_mc(year, arm, scale, v3, joint_csv)
        cap = np.maximum(np.nan_to_num(cap), 0.0)
        mwz = np.nan_to_num(mw)
        dem = mwz.sum(axis=0)
        g0 = s63.greedy(dem, cap, np.nan_to_num(mc, nan=1e6))
        g1 = s63.greedy(dem, cap, np.nan_to_num(mc1, nan=1e6))
        meta["model"], meta["d"] = mwz.sum(1) / 1e6, (g1 - g0).sum(1) / 1e6
        dist = []
        for grp in CLASSES:
            m = (meta.group == grp).values
            if mwz[m].sum() > 0:
                dist.append(f"{grp} {(mc[m] * mwz[m]).sum() / mwz[m].sum():.2f}->"
                            f"{(mc1[m] * mwz[m]).sum() / mwz[m].sum():.2f}")
        print(f"-- {year} A: gen-wtd offer $/MWh " + "  ".join(dist))
        byk = meta.groupby("klass")["d"].sum()
        print("   class delta TWh: " + "  ".join(f"{k} {v:+.3f}" for k, v in byk.items() if abs(v) > 5e-4))
        deltas[year] = {str(k): float(v) for k, v in byk.items() if str(k) in s63.BENCH_CLASSES}
        bt = bench_plant_twh(year)
        for grp in ("CT_PEAKER", "ST_GAS", "CC_REGULAR"):
            pm = meta[meta.group == grp].groupby("plant")[["model", "d"]].sum()
            a = np.array([bt.get((grp, int(p)), 0.0) for p in pm.index])
            print(f"   F {grp:10s} per-plant sum|model-923| {np.abs(pm.model.values - a).sum():.3f}"
                  f" -> {np.abs(pm.model.values + pm.d.values - a).sum():.3f} TWh")
    print("   C1 rows (committed scorer on shifted gmModel):")
    for r in s63.rescore(deltas):
        print(f"     {r['year']} {r['key']:11s} {r['status']:5s} {r['magnitude']:28s}"
              f" margin {3 - abs(r['share_pp']):.2f} pp")


def c4(arm: str, scale: float, v3csv: Path | None, joint_csv: Path | None) -> None:
    """C4 coal r / NRMSE per year: keeper reproduced, then plus the restack's hourly coal delta."""
    from market_sim.config.iso_configs import get_iso_config
    from scripts.probes._soco61_phase0 import _rcf
    rcf = _rcf()
    v3 = None
    if v3csv is not None:
        c = pd.read_csv(v3csv)
        v3 = c[c.starts > 0].groupby(["plant_code", "cls"]).run_med.median().reset_index()
    for year in YEARS:
        e = rcf._eia930_frame(year, "SOCO", get_iso_config("SOCO"))
        ob = e[e["series"] == "coal"].sort_values("hour")["mw"].to_numpy(float)
        ch = pd.read_parquet(Path(str(s63.LEG).format(y=year)) / f"hourly/class_hourly_{year}.parquet")
        ch = ch[(ch["pass"] == "P1") & ch.klass.astype(str).str.startswith("COAL")]
        ms = ch.groupby("hour").mw.sum().reindex(range(len(ob)), fill_value=0.0).to_numpy()
        meta, mw, cap, mc, mc1 = arm_mc(year, arm, scale, v3, joint_csv)
        cap = np.maximum(np.nan_to_num(cap), 0.0)
        dem = np.nan_to_num(mw).sum(axis=0)
        g0 = s63.greedy(dem, cap, np.nan_to_num(mc, nan=1e6))
        g1 = s63.greedy(dem, cap, np.nan_to_num(mc1, nan=1e6))
        coal = (meta.group == "COAL").values
        d = (g1[coal] - g0[coal]).sum(axis=0)[: len(ob)]

        def fit(m):
            return (round(float(np.corrcoef(m, ob)[0, 1]), 3),
                    round(float(np.sqrt(((m - ob) ** 2).mean()) / ob.mean()), 3))
        print(f"  C4 {year} coal arm {arm} x{scale}: keeper {fit(ms)} -> arm {fit(ms + d)}"
              f" (delta {d.sum() / 1e6:+.3f} TWh)")


def horizons() -> None:
    """(b) the model side: control P1 run lengths the markup would amortize over, per class."""
    for year in YEARS:
        mr = model_runs(year)
        mr = mr[mr.n_runs > 0]
        for grp in CLASSES:
            for sfx in ("committed", "econlo", "econhi", "peak"):
                g = mr[(mr.group == grp) & (mr.suffix.str.startswith(sfx))]
                if len(g):
                    w = g.mwh
                    print(f"  {year} {grp:11s} {sfx:9s} tranche-months {len(g):4d}"
                          f"  avg-run p50 (MWh-wtd) {_wq(g.avg_run, w, .5):7.1f} h"
                          f"  runs/tranche-month p50 {_wq(g.n_runs, w, .5):5.1f}")


def main() -> None:
    """CLI dispatch."""
    global FLEET
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fleet-dir", type=Path, default=Path("."))
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("noload").add_argument("--out-csv", type=Path, required=True)
    c = sp.add_parser("conduct")
    c.add_argument("--out-csv", type=Path, required=True)
    c.add_argument("--fuel", type=float, required=True, help="$/MMBtu for the fuel-only start")
    sp.add_parser("horizons")
    for name in ("reach", "c4"):
        r = sp.add_parser(name)
        r.add_argument("--arm", choices=("A", "B", "J", "Z"), required=True)
        r.add_argument("--scale", type=float, nargs="+", default=[1.0])
        r.add_argument("--v3", type=Path, default=None, help="conduct csv -> measured ceiling")
        r.add_argument("--joint", type=Path, default=None, help="noload csv (arm J)")
    a = ap.parse_args()
    FLEET = a.fleet_dir
    if a.cmd == "noload":
        noload(a.out_csv)
    elif a.cmd == "conduct":
        conduct(a.out_csv, a.fuel)
    elif a.cmd == "horizons":
        horizons()
    else:
        for sc in a.scale:
            (reach if a.cmd == "reach" else c4)(a.arm, sc, a.v3, a.joint)


if __name__ == "__main__":
    main()
