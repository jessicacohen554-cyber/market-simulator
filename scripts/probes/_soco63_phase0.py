"""SOCO-63 phase 0 (ZERO LP): measured incremental-heat-rate bands for SOCO, and their reach.

Reuses the CEMS input-output construction of
``scripts/data/derive_campd_marginal_hr.py`` (``load_campd`` /
``derive_unit_bands``) unchanged, with two SOCO-specific differences declared
ex ante (PRECOMMIT-free: nothing here is solved or armed):

* **Class map at UNIT grain** from the committed per-unit heat-rate artifacts
  ``data/raw/_processed-legacy/campd_{ct,st,cc,coal}_heat_rates_SOCO_units.csv``
  -- the same (plant, unit) -> class attribution the model's measured heat
  rates already use, the ST file carrying the ST deriver's capacity-rank
  boiler pairing. The deriver's plant-grain ``map_unit_class`` needs a
  ``bin_assignments_SOCO.csv`` that does not exist, and plant grain is unsound
  at the multi-class sites (Greene County, Watson, Gaston, Barry).
* **Normalization to each unit's OWN measured average heat rate** (the
  ``hr_gross`` of that unit in the same artifact) rather than a class
  cap-weighted base. Under ``measured_{ct,st,cc,coal}_heat_rates`` the model's
  per-plant base IS that measured average, so a band multiplier expressed on
  it reproduces the unit's measured marginal HR exactly and never
  double-counts the base (rule 19). Both normalizations are reported.

Subcommands:

* ``derive [--out-csv PATH]`` -- phase 0 (a): per class, the cap-weighted
  p25/p50/p75 of ``avg_committed`` / ``marg_econ_low`` / ``marg_econ_high``
  (own-average basis and the deriver's class-base basis) and coverage (% of
  the model's class MW). Writes a SCRATCH csv only.
* ``reach --bands PATH`` -- phase 0 (c): re-price every SOCO thermal tranche
  of the keeper's per-plant legs under the derived bands (the keeper's own
  hourly ``mc`` x band ratio on the fuel part), then report per year:
  A) $/MWh distance CT-vs-ST before/after, B) greedy hourly re-stack with
  energy-limited classes excluded from headroom, E) predicted class TWh and
  share deltas on every scored row. ``--scale`` applies symmetric x0.5 / x2
  bands to the band DEVIATION from 1.0 (check D).
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

LEGACY = _ROOT / "data/raw/_processed-legacy"
LEG = _ROOT / "results/calibration/soco61_arm_{y}"
UNIT_FILES = {
    "CT_PEAKER": "campd_ct_heat_rates_SOCO_units.csv",
    "ST_GAS": "campd_st_heat_rates_SOCO_units.csv",
    "CC_REGULAR": "campd_cc_heat_rates_SOCO_units.csv",
    "COAL": "campd_coal_heat_rates_SOCO_units.csv",
}
YEARS = (2023, 2024, 2025)


def _deriver():
    spec = importlib.util.spec_from_file_location(
        "dmhr", str(_ROOT / "scripts/data/derive_campd_marginal_hr.py")
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def unit_class_map() -> pd.DataFrame:
    """(plant_code, unit_id) -> class + the unit's own measured gross average HR."""
    frames = []
    for cls, f in UNIT_FILES.items():
        u = pd.read_csv(LEGACY / f, dtype={"unit_id": str})
        frames.append(
            u[["plant_code", "unit_id", "cap_mw", "hr_gross"]].assign(cls=cls)
        )
    m = pd.concat(frames, ignore_index=True)
    dup = m.duplicated(["plant_code", "unit_id"], keep=False)
    if dup.any():
        raise SystemExit(f"unit attributed to two classes: {m[dup]}")
    return m


def model_class_mw() -> pd.Series:
    """Model class nameplate: sum over tranches of the tranche's max hourly cap (2023 leg)."""
    u = pd.read_parquet(
        Path(str(LEG).format(y=2023)) / "hourly/unit_hourly_2023.parquet",
        columns=["unit_id", "plant_group", "cap_mw"],
    )
    return u.groupby(["plant_group", "unit_id"]).cap_mw.max().groupby(level=0).sum()


def derive(out_csv: Path) -> pd.DataFrame:
    """Phase 0 (a): per-class measured band multipliers (own-average and class-base)."""
    dm = _deriver()
    cmap = unit_class_map()
    camp = dm.load_campd("SOCO", YEARS)
    camp["unitId"] = camp["unitId"].astype(str)
    camp = camp.merge(
        cmap, left_on=["facilityId", "unitId"], right_on=["plant_code", "unit_id"],
        how="inner",
    )
    mw = model_class_mw()
    rows = []
    for cls, d in camp.groupby("cls"):
        cu = cmap[cmap.cls == cls]
        class_base = float(np.average(cu.hr_gross, weights=cu.cap_mw))
        own, cb = [], []
        for (_p, _u), g in d.groupby(["plant_code", "unit_id"]):
            hr_own = float(g.hr_gross.iloc[0])
            r1 = dm.derive_unit_bands(g, hr_own)
            r2 = dm.derive_unit_bands(g, class_base)
            if r1 is None:
                continue
            r1["cap_mw"] = float(g.cap_mw.iloc[0])
            own.append(r1)
            cb.append(r2)
        po, pc = pd.DataFrame(own), pd.DataFrame(cb)
        row = {"class": cls, "class_base_hr_gross": round(class_base, 3),
               "n_units": len(po), "n_units_listed": len(cu)}
        for tag, pu in (("own", po), ("cls", pc)):
            for col in ("avg_committed", "marg_committed", "marg_econ_low", "marg_econ_high"):
                q = dm._capwt(pu, col)
                for k, v in q.items():
                    row[f"{tag}_{col}_{k}"] = v
        fitted_cap = float(po.dropna(subset=["marg_econ_low", "marg_econ_high"]).cap_mw.sum())
        grp = "COAL" if cls == "COAL" else cls
        row["fitted_cap_mw"] = round(fitted_cap, 1)
        row["model_class_mw"] = round(float(mw.get(grp, np.nan)), 1)
        row["coverage_pct"] = round(100 * fitted_cap / float(mw.get(grp, np.nan)), 1)
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(out_csv, index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 80)
    keep = ["class", "n_units", "n_units_listed", "fitted_cap_mw", "model_class_mw",
            "coverage_pct"]
    for tag in ("own", "cls"):
        keep += [f"{tag}_avg_committed_p50", f"{tag}_marg_econ_low_p50",
                 f"{tag}_marg_econ_high_p50"]
    print(out[keep].to_string(index=False))
    print("\n[p25,p75] own basis:")
    for _, r in out.iterrows():
        print(f"  {r['class']:11s} avg_comm [{r.own_avg_committed_p25},{r.own_avg_committed_p75}]"
              f"  marg_lo [{r.own_marg_econ_low_p25},{r.own_marg_econ_low_p75}]"
              f"  marg_hi [{r.own_marg_econ_high_p25},{r.own_marg_econ_high_p75}]")
    print(f"\nwrote {out_csv}")
    return out


def fleet_side(year: int, out: Path) -> None:
    """``run_year(fleet_only=True)`` off the keeper leg's own recipe; save unit-grain arrays.

    One year per process (several loaders are ``@lru_cache``d -- SOCO-59 P14).
    The control only: the arm field does not exist (owner ruling blank), so the
    arm side is the analytical re-price in :func:`reach`.
    """
    import json

    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = Path(str(LEG).format(y=year))
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    r = run_year(year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)
    fa = r["fleet_arrays"]
    np.savez(
        out,
        ids=np.array([str(g.unit_id) for g in r["fleet"]]),
        groups=np.array([str(g.plant_group) for g in r["fleet"]]),
        plants=np.array([int(getattr(g, "plant_code", -1) or -1) for g in r["fleet"]]),
        fuel_prices=np.asarray(r["fuel_prices"], float),
        mc_base=np.asarray(r["mc_base"], float),
        vom=np.asarray(getattr(fa, "vom", np.zeros(len(r["fleet"]))), float),
        heat_rate=np.asarray(fa.heat_rate, float),
        pmax=np.asarray(fa.pmax, float),
        availability=np.asarray(fa.availability, float),
    )
    print(f"wrote {out}")


BAND_COLS = {"committed": "own_avg_committed_p50", "econlo": "own_marg_econ_low_p50",
             "econhi": "own_marg_econ_high_p50"}
#: Restacked (economic thermal) groups. Energy-limited / non-thermal resources
#: (nuclear, hydro, storage, wind, solar, imports) are EXCLUDED from headroom
#: and held at their solved dispatch; ``_mustrun`` tranches are held too.
RESTACK_GROUPS = ("CT_PEAKER", "ST_GAS", "CC_REGULAR", "CC_CHP", "CT_CHP", "ST_CHP", "COAL", "oil")
BENCH_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP", "COAL_PRB", "COAL_BIT")


def band_table(bands_csv: Path, scale: float, only: tuple[str, ...] | None) -> dict:
    """{class: {suffix: multiplier}} from the scratch derivation; deviation scaled by ``scale``."""
    b = pd.read_csv(bands_csv).set_index("class")
    out = {}
    for cls in b.index:
        if only and cls not in only:
            continue
        out[cls] = {suf: 1.0 + scale * (float(b.loc[cls, col]) - 1.0) for suf, col in BAND_COLS.items()}
    return out


def _suffix(uid: str) -> str:
    s = uid.rsplit("_", 1)[-1]
    return "econlo" if s.startswith("econlo") else "econhi" if s.startswith("econhi") else s


def year_frames(year: int, fleet_npz: Path) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray, list]:
    """Solved dispatch (tranche x hour) for the restack set, plus the fuel part HR x fuel."""
    u = pd.read_parquet(Path(str(LEG).format(y=year)) / f"hourly/unit_hourly_{year}.parquet",
                        columns=["unit_id", "plant_code", "plant_group", "hour", "mw", "cap_mw", "mc"])
    k = pd.read_parquet(Path(str(LEG).format(y=year)) / f"dispatch/{year}_P1.parquet",
                        columns=["unit_id", "klass"]).drop_duplicates("unit_id").set_index("unit_id").klass
    u = u[u.plant_group.isin(RESTACK_GROUPS) & ~u.unit_id.str.endswith("_mustrun")]
    ids = sorted(u.unit_id.unique())
    T = int(u.hour.max()) + 1
    piv = {c: u.pivot(index="unit_id", columns="hour", values=c).reindex(ids).to_numpy(float)
           for c in ("mw", "cap_mw", "mc")}
    f = np.load(fleet_npz)
    fidx = {x: i for i, x in enumerate(f["ids"])}
    rows = np.array([fidx[i] for i in ids])
    fuel = f["heat_rate"][rows, None] * f["fuel_prices"][rows, :T]
    meta = pd.DataFrame({"unit_id": ids,
                         "group": u.drop_duplicates("unit_id").set_index("unit_id").plant_group.reindex(ids).values,
                         "plant": u.drop_duplicates("unit_id").set_index("unit_id").plant_code.reindex(ids).values,
                         "klass": k.reindex(ids).values})
    meta["suffix"] = meta.unit_id.map(_suffix)
    return meta, piv["mw"], piv["cap_mw"], piv["mc"], fuel


def greedy(demand: np.ndarray, cap: np.ndarray, mc: np.ndarray) -> np.ndarray:
    """Merit-order fill of ``demand[t]`` over tranches by ascending ``mc[:, t]`` (vectorized over t)."""
    order = np.argsort(mc, axis=0, kind="stable")
    cs = np.take_along_axis(cap, order, axis=0)
    cum = np.cumsum(cs, axis=0)
    prev = cum - cs
    fill = np.clip(demand[None, :] - prev, 0.0, cs)
    out = np.zeros_like(cap)
    np.put_along_axis(out, order, fill, axis=0)
    return out


def reach(bands_csv: Path, fleet_dir: Path, scale: float, only: tuple[str, ...] | None) -> dict:
    """Checks A/B/D/E/F: re-price, greedy re-stack (arm minus greedy control), predicted rows."""
    bt = band_table(bands_csv, scale, only)
    res = {}
    for year in YEARS:
        meta, mw, cap, mc, fuel = year_frames(year, fleet_dir / f"fleet_{year}.npz")
        mult = np.ones(len(meta))
        for i, r in meta.iterrows():
            cls = "COAL" if r.group == "COAL" else r.group
            mult[i] = bt.get(cls, {}).get(r.suffix, 1.0)
        mc_arm = mc + (mult[:, None] - 1.0) * fuel
        cap = np.maximum(np.nan_to_num(cap), 0.0)
        dem = np.nan_to_num(mw).sum(axis=0)
        g0 = greedy(dem, cap, np.nan_to_num(mc, nan=1e6))
        g1 = greedy(dem, cap, np.nan_to_num(mc_arm, nan=1e6))
        meta["model"] = np.nan_to_num(mw).sum(axis=1) / 1e6
        meta["g0"] = g0.sum(axis=1) / 1e6
        meta["g1"] = g1.sum(axis=1) / 1e6
        meta["d"] = meta.g1 - meta.g0
        # A: generation-weighted mean offer by class, control vs arm
        w = np.nan_to_num(mw)
        dist = {}
        for grp in ("CT_PEAKER", "ST_GAS", "CC_REGULAR", "COAL"):
            m = (meta.group == grp).values
            if w[m].sum() > 0:
                dist[grp] = (float((mc[m] * w[m]).sum() / w[m].sum()),
                             float((mc_arm[m] * w[m]).sum() / w[m].sum()))
        res[year] = {"meta": meta.copy(), "dist": dist}
    return res


def c4_coal(bands_csv: Path, fleet_dir: Path, scale: float) -> None:
    """C4 coal r / NRMSE per year: reproduce the keeper's, then add the restack's hourly coal delta."""
    from market_sim.config.iso_configs import get_iso_config
    from scripts.probes._soco61_phase0 import _rcf

    rcf = _rcf()
    res = reach(bands_csv, fleet_dir, scale, None)
    for year in YEARS:
        e = rcf._eia930_frame(year, "SOCO", get_iso_config("SOCO"))
        ob = e[e["series"] == "coal"].sort_values("hour")["mw"].to_numpy(float)
        ch = pd.read_parquet(Path(str(LEG).format(y=year)) / f"hourly/class_hourly_{year}.parquet")
        ch = ch[(ch["pass"] == "P1") & ch.klass.astype(str).str.startswith("COAL")]
        ms = ch.groupby("hour").mw.sum().reindex(range(len(ob)), fill_value=0.0).to_numpy()
        meta, mw, cap, mc, fuel = year_frames(year, fleet_dir / f"fleet_{year}.npz")
        bt = band_table(bands_csv, scale, None)
        mult = np.array([bt.get("COAL" if r.group == "COAL" else r.group, {}).get(r.suffix, 1.0)
                         for r in meta.itertuples()])
        cap = np.maximum(np.nan_to_num(cap), 0.0)
        dem = np.nan_to_num(mw).sum(axis=0)
        g0 = greedy(dem, cap, np.nan_to_num(mc, nan=1e6))
        g1 = greedy(dem, cap, np.nan_to_num(mc + (mult[:, None] - 1.0) * fuel, nan=1e6))
        coal = (meta.group == "COAL").values
        d = (g1[coal] - g0[coal]).sum(axis=0)[: len(ob)]

        def fit(m):
            return (round(float(np.corrcoef(m, ob)[0, 1]), 3),
                    round(float(np.sqrt(((m - ob) ** 2).mean()) / ob.mean()), 3))

        print(f"  C4 {year} coal: keeper r,NRMSE {fit(ms)} -> arm {fit(ms + d)}  (delta {d.sum() / 1e6:+.3f} TWh)")


def rescore(deltas: dict[int, dict[str, float]]) -> list[dict]:
    """Re-run the committed C1 scorer with class TWh shifted by the predicted deltas."""
    import copy

    import calibration_verdict as cv

    art = cv.load_artifacts("2026-09-24-soco61-dark-unit")
    out = []
    for year in YEARS:
        ypay = copy.deepcopy(art["payload"]["years"][str(year)])
        for c, dv in deltas.get(year, {}).items():
            ypay["gmModel"][c] = float(ypay["gmModel"].get(c, 0.0)) + dv
        out += [r for r in cv.score_fuelmix(year, ypay, art["bench"].get(year, {}), "SOCO")
                if r["status"] != "SKIPPED"]
    return out


def report_reach(bands_csv: Path, fleet_dir: Path, scale: float, only) -> None:
    """Print A / B / E / F for one band variant."""
    from scripts.probes._soco62_phase0 import bench_plant_twh

    tag = f"scale={scale}" + (f" ONLY={only}" if only else " (non-selective)")
    print(f"\n######## {tag}")
    res = reach(bands_csv, fleet_dir, scale, only)
    deltas = {}
    for year, r in res.items():
        m = r["meta"]
        print(f"-- {year}  A: gen-weighted offer $/MWh control -> arm: "
              + "  ".join(f"{k} {a:.2f}->{b:.2f}" for k, (a, b) in r["dist"].items()))
        byk = m.groupby("klass")[["model", "g0", "g1", "d"]].sum()
        print("   B/E: TWh by class (solved | greedy ctl | greedy arm | arm-ctl)")
        print(byk.round(3).to_string())
        deltas[year] = {str(k): float(v) for k, v in byk.d.items() if str(k) in BENCH_CLASSES}
        bt = bench_plant_twh(year)
        for grp in ("CT_PEAKER", "ST_GAS", "CC_REGULAR"):
            pm = m[m.group == grp].groupby("plant")[["model", "d"]].sum()
            a = np.array([bt.get((grp, int(p)), 0.0) for p in pm.index])
            e0 = np.abs(pm.model.values - a).sum()
            e1 = np.abs(pm.model.values + pm.d.values - a).sum()
            print(f"   F: {grp} per-plant sum|model-923| {e0:.3f} -> {e1:.3f} TWh")
    print("   C1 rows predicted (share_pp, margin to 3.00):")
    for r in rescore(deltas):
        print(f"     {r['year']} {r['key']:11s} {r['status']:5s} {r['magnitude']:28s} margin {3 - abs(r['share_pp']):.2f} pp")


def main() -> None:
    """CLI dispatch."""
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    d = sp.add_parser("derive")
    d.add_argument("--out-csv", type=Path, required=True)
    f = sp.add_parser("fleet")
    f.add_argument("--year", type=int, required=True)
    f.add_argument("--out", type=Path, required=True)
    rc = sp.add_parser("reach")
    rc.add_argument("--bands", type=Path, required=True)
    rc.add_argument("--fleet-dir", type=Path, required=True)
    rc.add_argument("--scale", type=float, nargs="+", default=[1.0])
    rc.add_argument("--only", nargs="*", default=None)
    c4 = sp.add_parser("c4")
    c4.add_argument("--bands", type=Path, required=True)
    c4.add_argument("--fleet-dir", type=Path, required=True)
    c4.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    if a.cmd == "derive":
        derive(a.out_csv)
    elif a.cmd == "fleet":
        fleet_side(a.year, a.out)
    elif a.cmd == "c4":
        c4_coal(a.bands, a.fleet_dir, a.scale)
    elif a.cmd == "reach":
        for sc in a.scale:
            report_reach(a.bands, a.fleet_dir, sc, tuple(a.only) if a.only else None)


if __name__ == "__main__":
    main()
