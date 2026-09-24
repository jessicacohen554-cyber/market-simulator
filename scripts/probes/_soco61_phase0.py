"""SOCO-61 phase 0 (ZERO LP): measure the three routed leads before claiming a lever.

Reads the keeper's per-year legs ``results/calibration/soco60_armB_<Y>`` (the
per-plant layer of ``2026-09-23-soco60-boundary-span``, recovered at zero LP),
CAMPD hourly unit data and the benchmark's EIA-923 frame.

Subcommands:

* ``cc``   -- lead (1): per-plant CC capability. For every CC_REGULAR plant:
  model energy, model availability energy (sum of hourly ``cap_mw``), EIA-923
  net, CAMPD gross, and the MONTHLY hourly-gross p99 against the model's
  monthly mean availability cap. The question is whether the model lets a
  plant run above what it physically delivered.
* ``coal`` -- lead (2): per-plant coal availability vs CAMPD operating hours
  and gross output, same construction.
* ``st``   -- lead (3): model ST_GAS vs CC delivered fuel price per plant, to
  test whether a measured fuel separation exists in the inputs at all.
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

STATES = ("AL", "GA", "MS")
LEG = "results/calibration/soco60_armB_{y}"


def _rcf():
    spec = importlib.util.spec_from_file_location(
        "rcf", str(_ROOT / "scripts/run_calibration_full.py")
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def eia923_by_plant(year: int, klasses: tuple[str, ...]) -> pd.Series:
    """Benchmark EIA-923 net MWh per plant for the given classes (keeper boundary)."""
    from market_sim.data import eia923

    fr = _rcf()._eia923_frame(year, eia923.load_monthly_generation(), "SOCO")
    fr = fr[fr.klass.isin(klasses)]
    return fr.groupby("plant_id")["annual_mwh"].sum()


def campd_hourly(year: int, codes: set[int], unit_prefix: tuple[str, ...]) -> pd.DataFrame:
    """CAMPD hourly gross MW per facility (sum over matching units), 8760-aligned."""
    frames = []
    for st in STATES:
        f = _ROOT / f"data/raw/campd-unit-level/{st}_{year}.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(
            f, columns=["facilityId", "unitId", "date", "hour", "grossLoad", "unitType"]
        )
        d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
        d = d[d.facilityId.isin(codes)]
        ut = d.unitType.astype(str).str.strip().str.casefold()
        d = d[ut.str.startswith(unit_prefix)]
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d["ts"] = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    g = d.groupby(["facilityId", "ts"]).grossLoad.sum(min_count=1).fillna(0.0)
    return g.reset_index()


def model_plant_hourly(year: int, group: str) -> pd.DataFrame:
    """Model hourly MW and cap MW per plant for one plant_group."""
    u = pd.read_parquet(
        _ROOT / LEG.format(y=year) / f"hourly/unit_hourly_{year}.parquet",
        columns=["plant_code", "plant_group", "hour", "mw", "cap_mw", "mc"],
    )
    u = u[u.plant_group == group]
    return u.groupby(["plant_code", "hour"]).agg(mw=("mw", "sum"), cap=("cap_mw", "sum")).reset_index()


def capability(year: int, group: str, klasses: tuple[str, ...], prefix: tuple[str, ...]) -> pd.DataFrame:
    """Per-plant capability table: model vs EIA-923 vs CAMPD."""
    m = model_plant_hourly(year, group)
    codes = set(int(c) for c in m.plant_code.unique())
    act = eia923_by_plant(year, klasses)
    c = campd_hourly(year, codes, prefix)
    mon_m = (pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(m.hour, unit="h")).dt.month
    m["month"] = mon_m.values
    c["month"] = c.ts.dt.month
    rows = []
    for p in sorted(codes):
        mp, cp = m[m.plant_code == p], c[c.facilityId == p]
        cap_m = mp.groupby("month").cap.mean()
        p99_m = cp.groupby("month").grossLoad.quantile(0.99) if len(cp) else pd.Series(dtype=float)
        over = (cap_m - p99_m.reindex(cap_m.index).fillna(0.0)).clip(lower=0)
        # Energy the model could produce above the plant's own measured monthly p99.
        hpm = mp.groupby("month").size()
        rows.append(
            {
                "plant": p,
                "model_TWh": mp.mw.sum() / 1e6,
                "avail_TWh": mp.cap.sum() / 1e6,
                "e923_TWh": float(act.get(p, np.nan)) / 1e6,
                "campd_gross_TWh": cp.grossLoad.sum() / 1e6 if len(cp) else np.nan,
                "model_util": mp.mw.sum() / max(mp.cap.sum(), 1.0),
                "campd_CF_vs_cap": (cp.grossLoad.sum() / max(mp.cap.sum(), 1.0)) if len(cp) else np.nan,
                "cap_mean_MW": mp.cap.mean(),
                "campd_p99_MW": float(cp.grossLoad.quantile(0.99)) if len(cp) else np.nan,
                "campd_max_MW": float(cp.grossLoad.max()) if len(cp) else np.nan,
                "months_cap_gt_p99": int((over > 0).sum()),
                "TWh_cap_above_p99": float((over * hpm).sum() / 1e6),
            }
        )
    t = pd.DataFrame(rows)
    t["model_minus_923"] = t.model_TWh - t.e923_TWh
    return t.sort_values("model_minus_923", ascending=False)


def fuel_sep(year: int) -> pd.DataFrame:
    """Model delivered fuel price and mc by class, per plant (lead 3)."""
    u = pd.read_parquet(
        _ROOT / LEG.format(y=year) / f"hourly/unit_hourly_{year}.parquet",
        columns=["plant_code", "plant_group", "mw", "mc"],
    )
    u = u[u.plant_group.isin(["ST_GAS", "CC_REGULAR", "CT_PEAKER"])]
    u = u[u.mw > 0]
    return u.groupby(["plant_group"]).apply(
        lambda d: pd.Series({"gen_TWh": d.mw.sum() / 1e6, "mc_gen_wtd": (d.mc * d.mw).sum() / d.mw.sum()}),
        include_groups=False,
    )


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=("cc", "coal", "st", "fleet", "fleetcmp", "restack", "c4"))
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024])
    ap.add_argument("--side", choices=("ctl", "arm"))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--files", nargs=2, type=Path)
    a = ap.parse_args()
    if a.cmd == "fleet":
        fleet_side(a.years[0], a.side == "arm", a.out)
        return
    if a.cmd == "fleetcmp":
        fleet_compare(*a.files)
        return
    if a.cmd == "restack":
        restack_2024(*a.files)
        return
    if a.cmd == "c4":
        c4_coal_2024(*a.files)
        return
    pd.set_option("display.width", 250)
    for y in a.years:
        print(f"\n===== {y} =====")
        if a.cmd == "cc":
            t = capability(y, "CC_REGULAR", ("CC_REGULAR",), ("combined cycle",))
        elif a.cmd == "coal":
            t = capability(y, "COAL", ("COAL_PRB", "COAL_BIT"), ("tangentially", "wall", "cell", "cyclone", "dry bottom", "stoker", "other boiler"))
        else:
            print(fuel_sep(y).round(3))
            continue
        print(t.round(3).to_string(index=False))
        print(f"  sum|model-923| {t.model_minus_923.abs().sum():.3f} TWh; "
              f"TWh above measured monthly p99 {t.TWh_cap_above_p99.sum():.3f}")



def dark_units(years=(2022, 2023, 2024, 2025)) -> pd.DataFrame:
    """Units with CAMPD rows but ZERO gross all year, that produced gross in an adjacent year."""
    per = []
    for st in STATES:
        for y in years:
            f = _ROOT / f"data/raw/campd-unit-level/{st}_{y}.parquet"
            if not f.exists():
                continue
            d = pd.read_parquet(f, columns=["facilityId", "facilityName", "unitId", "grossLoad", "opTime", "unitType", "primaryFuelInfo"])
            g = d.groupby(["facilityId", "unitId"], observed=True).agg(
                name=("facilityName", "first"), ut=("unitType", "first"), fuel=("primaryFuelInfo", "first"),
                rows=("opTime", "size"), op_h=("opTime", lambda s: int((s > 0).sum())),
                gwh=("grossLoad", lambda s: s.sum() / 1e3), p99=("grossLoad", lambda s: s.quantile(0.99)),
            ).reset_index()
            g["year"] = y
            per.append(g)
    t = pd.concat(per, ignore_index=True)
    t["facilityId"] = pd.to_numeric(t.facilityId, errors="coerce").astype(int)
    key = t.set_index(["facilityId", "unitId", "year"])
    out = []
    for (fid, uid, y), r in key.iterrows():
        if y not in (2023, 2024, 2025) or r.gwh > 0:
            continue
        adj = [key.gwh.get((fid, uid, yy), 0.0) for yy in (y - 1, y + 1)]
        adj_p99 = [key.p99.get((fid, uid, yy), np.nan) for yy in (y - 1, y + 1)]
        if max(adj) <= 0:
            continue
        out.append({"facility": fid, "name": r["name"], "unit": uid, "year": y, "type": r.ut, "fuel": r.fuel,
                    "rows": r.rows, "op_h": r.op_h, "adj_gwh": adj, "adj_p99_MW": np.nanmax(adj_p99)})
    return pd.DataFrame(out)


def fleet_side(year: int, arm: bool, out: Path) -> None:
    """``run_year(fleet_only=True)`` off the keeper leg's recipe; save unit-grain arrays.

    Run ONE side per process (SOCO-59 P14: several loaders are ``@lru_cache``d).
    The arm adds ``campd_dark_unit_year_windows=True`` through the same
    ``prb_overrides`` channel ``replay_keeper --set`` routes a config field.
    """
    import json

    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = _ROOT / LEG.format(y=year)
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if arm:
        kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), "campd_dark_unit_year_windows": True}
    r = run_year(year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)
    fa = r["fleet_arrays"]
    np.savez(
        out,
        ids=np.array([str(g.unit_id) for g in r["fleet"]]),
        groups=np.array([str(g.plant_group) for g in r["fleet"]]),
        plants=np.array([int(getattr(g, "plant_code", -1) or -1) for g in r["fleet"]]),
        fuel_prices=np.asarray(r["fuel_prices"], float),
        mc_base=np.asarray(r["mc_base"], float),
        pmax=np.asarray(fa.pmax, float),
        availability=np.asarray(fa.availability, float),
        heat_rate=np.asarray(fa.heat_rate, float),
        min_gen=np.asarray(getattr(fa, "min_gen", np.zeros(1)), float),
    )
    print(f"wrote {out}")


def fleet_compare(ctl: Path, arm: Path) -> None:
    """Rule 19 at the unit_id grain: which keys move, on which grain."""
    c, r = np.load(ctl), np.load(arm)
    uc, ur = list(c["ids"]), list(r["ids"])
    assert uc == ur, "unit list differs"
    grp = dict(zip(uc, c["groups"]))
    plant = dict(zip(uc, c["plants"]))
    for key in ("fuel_prices", "mc_base", "pmax", "availability", "heat_rate", "min_gen"):
        x, y = c[key], r[key]
        if x.shape != y.shape:
            print(f"  {key}: shape {x.shape} vs {y.shape}")
            continue
        d = np.abs(x - y).reshape(len(uc), -1).max(axis=1) if x.size >= len(uc) else np.abs(x - y)
        moved = [uc[i] for i in np.where(d > 0)[0]] if x.size >= len(uc) else []
        print(f"  {key:12s} max|d| {float(d.max()):.12f}  keys moved {len(moved)}/{len(uc)}"
              + (f"  -> {[(u, grp[u], int(plant[u])) for u in moved]}" if moved else ""))
    av_c = c["availability"].reshape(len(uc), -1)
    av_r = r["availability"].reshape(len(uc), -1)
    pm = c["pmax"]
    dmwh = ((av_c - av_r) * pm[:, None]).sum(axis=1)
    idx = np.where(np.abs(dmwh) > 0)[0]
    for i in idx:
        print(f"    {uc[i]} ({grp[uc[i]]}) availability energy {av_c[i].dot(np.full(av_c.shape[1], pm[i])) / 1e6:.4f}"
              f" -> {av_r[i].dot(np.full(av_r.shape[1], pm[i])) / 1e6:.4f} TWh")
    print(f"  total availability energy removed {dmwh.sum() / 1e6:.4f} TWh")



def restack_2024(ctl: Path, arm: Path) -> None:
    """Greedy zero-LP re-stack of the energy the arm's 55271 cap removes (2024).

    Removed MW per hour = max(0, model mw - arm cap) at each 55271 tranche; it
    is re-served by idle headroom (cap_mw - mw) of every OTHER unit in
    ascending hourly ``mc`` (the ``cheap`` allocation) -- the LP's first-order
    re-dispatch. Storage and floors held; a bracket, not a forecast.
    """
    c, r = np.load(ctl), np.load(arm)
    ids = list(c["ids"])
    pm = c["pmax"]
    av_r = r["availability"].reshape(len(ids), -1)
    mg = c["min_gen"].reshape(len(ids), -1) if c["min_gen"].size >= len(ids) else None
    u = pd.read_parquet(
        _ROOT / LEG.format(y=2024) / "hourly/unit_hourly_2024.parquet",
        columns=["unit_id", "plant_group", "hour", "mw", "cap_mw", "mc"],
    )
    u["unit_id"] = u.unit_id.astype(str)
    cls = pd.read_parquet(_ROOT / LEG.format(y=2024) / "dispatch/2024_P1.parquet", columns=["unit_id", "klass"]).drop_duplicates()
    cls["unit_id"] = cls.unit_id.astype(str)
    u = u.merge(cls, on="unit_id", how="left")
    tgt = [i for i, x in enumerate(ids) if "p55271" in x]
    newcap = {ids[i]: av_r[i] * pm[i] for i in tgt}
    if mg is not None:
        for i in tgt:
            viol = int((mg[i] > newcap[ids[i]] + 1e-6).sum())
            print(f"  {ids[i]}: min_gen > arm cap in {viol} h (max min_gen {mg[i].max():.1f} MW)")
    rem = np.zeros(8784 if u.hour.max() >= 8760 else 8760)
    for uid, cap in newcap.items():
        s = u[u.unit_id == uid].sort_values("hour")
        cut = np.clip(s.mw.to_numpy() - cap[: len(s)], 0, None)
        rem[s.hour.to_numpy()] += cut
    print(f"  removed at 55271: {rem.sum() / 1e6:.3f} TWh in {(rem > 0.5).sum()} h")
    # Energy-limited / must-run classes cannot re-serve (hydro budgets, VRE CF,
    # nuclear and biomass at their own availability).
    firm = ~u["klass"].astype(str).isin(["hydro", "solar", "wind", "nuclear", "biomass", "OTHER"])
    o = u[firm & ~u.unit_id.str.contains("p55271") & (u.cap_mw - u.mw > 1e-6)].copy()
    o["head"] = o.cap_mw - o.mw
    o = o.sort_values(["hour", "mc"])
    add = {}
    unmet = 0.0
    for h, g in o.groupby("hour", sort=False):
        need = rem[h]
        if need <= 0:
            continue
        cum = g["head"].cumsum().to_numpy()
        take = np.minimum(g["head"].to_numpy(), np.clip(need - (cum - g["head"].to_numpy()), 0, None))
        for k, t in zip(g["klass"].astype(str), take):
            if t > 0:
                add[k] = add.get(k, 0.0) + t
        unmet += max(0.0, need - cum[-1] if len(cum) else need)
    print("  re-served by class (TWh):", {k: round(v / 1e6, 3) for k, v in sorted(add.items(), key=lambda kv: -kv[1])})
    print(f"  unmet {unmet / 1e3:.1f} GWh")



def c4_coal_2024(ctl: Path, arm: Path) -> None:
    """C4 2024 coal r / NRMSE: reproduce the keeper's, then apply the restack's coal delta.

    Same construction as render_calibration_html's fuelRows: model = hourly sum of
    the coal classes, actual = the EIA-930 ``coal`` series from
    ``run_calibration_full._eia930_frame``.
    """
    from market_sim.config.iso_configs import get_iso_config

    rcf = _rcf()
    e = rcf._eia930_frame(2024, "SOCO", get_iso_config("SOCO"))
    ob = e[e["series"] == "coal"].sort_values("hour")["mw"].to_numpy(float)
    ch = pd.read_parquet(_ROOT / LEG.format(y=2024) / "hourly/class_hourly_2024.parquet")
    ch = ch[(ch["pass"] == "P1") & ch.klass.astype(str).str.startswith("COAL")]
    ms = ch.groupby("hour").mw.sum().reindex(range(len(ob)), fill_value=0.0).to_numpy()

    def fit(m):
        return round(float(np.corrcoef(m, ob)[0, 1]), 3), round(float(np.sqrt(((m - ob) ** 2).mean()) / ob.mean()), 3)

    print(f"  keeper reproduced: r, NRMSE = {fit(ms)}  (committed 0.847 / 0.240)")
    d = _restack_coal_delta(ctl, arm, len(ob))
    for k in (0.5, 1.0, 2.0):
        print(f"  coal delta x{k}: +{k * d.sum() / 1e6:.3f} TWh -> r, NRMSE = {fit(ms + k * d)}")


def _restack_coal_delta(ctl: Path, arm: Path, n: int) -> np.ndarray:
    """Hourly MW the cheap-first restack puts on COAL units (see restack_2024)."""
    c, r = np.load(ctl), np.load(arm)
    ids = list(c["ids"])
    pm = c["pmax"]
    av_r = r["availability"].reshape(len(ids), -1)
    u = pd.read_parquet(_ROOT / LEG.format(y=2024) / "hourly/unit_hourly_2024.parquet",
                        columns=["unit_id", "plant_group", "hour", "mw", "cap_mw", "mc"])
    u["unit_id"] = u.unit_id.astype(str)
    rem = np.zeros(n)
    for i, x in enumerate(ids):
        if "p55271" not in x:
            continue
        s = u[u.unit_id == x].sort_values("hour")
        rem[s.hour.to_numpy()] += np.clip(s.mw.to_numpy() - av_r[i][: len(s)] * pm[i], 0, None)
    firm = ~u.plant_group.astype(str).isin(["hydro", ""])
    o = u[firm & ~u.unit_id.str.contains("p55271") & (u.cap_mw - u.mw > 1e-6)].copy()
    o["head"] = o.cap_mw - o.mw
    o = o.sort_values(["hour", "mc"])
    out = np.zeros(n)
    for h, g in o.groupby("hour", sort=False):
        need = rem[h]
        if need <= 0:
            continue
        head = g["head"].to_numpy()
        cum = head.cumsum()
        take = np.minimum(head, np.clip(need - (cum - head), 0, None))
        out[h] = take[g.plant_group.astype(str).str.startswith("COAL").to_numpy()].sum()
    return out


if __name__ == "__main__":
    main()
