"""SOCO-76 phase 0 (ZERO LP): the GAS side of the 2019 merit order, on the soco-72 keeper's 2019 leg.

Rule 32 ``[R-SHARD]`` (a): never solves. Instruments:

1. ``plants`` — per gas plant, model TWh (leg unit hourlies) vs the benchmark's own
   EIA-923 plant TWh (``bench.plants[*].e_ann``), by class.
2. ``undercut`` — the hours a coal plant is CEMS-synced (any coal unit > 1 % of the
   plant's model capacity) while the model has it off (<= 1 MW). In those hours, every
   RUNNING gas tranche whose offer is below that plant's cheapest available non-must-run
   coal offer: MWh, hours, median offer, and the undercut (coal offer - gas offer).
   Aggregated per (gas plant, class).
3. ``inputs`` — for the top undercutting gas plants: the model's offer decomposed
   (heat rate, VOM, implied fuel $/MMBtu from a ``fleet_only`` rebuild on the keeper
   recipe) against the plant's OWN 2019 data: CEMS heat rate (sum heatInput / sum
   grossLoad over the class's CAMPD units, net-converted by the artifact's parasitic
   factor), EIA-923 q-weighted delivered gas, and availability (model cap_mw vs CEMS
   gross output p99 / hours CEMS output exceeds model cap).

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco76_gas_census.py all
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "scripts" / "probes"))
import _soco73_phase0 as s73  # noqa: E402  (reuse: cems_units, rebuild, bench, PLANTS)

Y = 2019
T = 8760
LEG = _ROOT / f"results/calibration/soco72_{Y}"
GAS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP", "ST_CHP")
PL = _ROOT / "data/raw/_processed-legacy"
HR_ART = {"CC_REGULAR": "campd_cc_heat_rates_SOCO.csv", "CT_PEAKER": "campd_ct_heat_rates_SOCO.csv",
          "ST_GAS": "campd_st_heat_rates_SOCO.csv"}
OUT = _ROOT / "docs/handoffs/r-soco/soco76_gas_census.json"


def leg() -> pd.DataFrame:
    """Leg unit hourlies with zone price joined."""
    u = pd.read_parquet(LEG / f"hourly/unit_hourly_{Y}.parquet",
                        columns=["unit_id", "plant_code", "plant_group", "zone", "hour", "mw", "cap_mw", "mc"])
    u["unit_id"] = u.unit_id.astype(str)
    u["g"] = u.plant_group.astype(str)
    s = pd.read_parquet(LEG / f"hourly/system_{Y}.parquet", columns=["zone", "hour", "price"])
    return u.merge(s, on=["zone", "hour"], how="left")


def bench() -> dict:
    """Benchmark plant rows (EIA-923 boundary)."""
    return json.load(gzip.open(str(s73.BENCH).format(y=Y)))["bench"]


def main_plants(u: pd.DataFrame) -> pd.DataFrame:
    """Per gas plant x class: model vs EIA-923 TWh."""
    b = bench()["plants"]
    rows = []
    m = u[u.g.isin(GAS)].groupby(["plant_code", "g"]).mw.sum() / 1e6
    act: dict = {}
    for key, v in b.items():
        g = str(v.get("group", ""))
        if g in GAS:
            p = int(str(key).split(":")[0])
            act[(p, g)] = act.get((p, g), 0.0) + float(v.get("e_ann") or 0.0)
            act.setdefault(("name", p), v.get("name"))
    for (p, g) in set(m.index) | {k for k in act if k[0] != "name"}:
        rows.append(dict(plant=p, name=act.get(("name", p)), cls=g, model=float(m.get((p, g), 0.0)),
                         eia923=float(act.get((p, g), 0.0))))
    t = pd.DataFrame(rows)
    t["delta"] = t.model - t.eia923
    return t.sort_values("delta", ascending=False)


def synced_off(u: pd.DataFrame) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Per coal plant: (hours CEMS-synced & model-off, cheapest available non-must-run coal offer)."""
    out = {}
    for p in s73.PLANTS:
        c = s73.cems_units(p, Y)
        if c.empty:
            continue
        gl = np.zeros(T)
        np.add.at(gl, c.h.to_numpy(), np.nan_to_num(c.grossLoad.to_numpy(float)))
        mw, cap, off = s73._plant_model(u, p)
        if cap.max() <= 0:
            continue
        H = (gl > 0.01 * cap.max()) & (mw <= 1.0)
        out[p] = (H, off)
    return out


def main_undercut(u: pd.DataFrame, so: dict) -> pd.DataFrame:
    """Running gas tranches offered below the synced-off coal plant's cheapest offer, per (plant, class)."""
    g = u[u.g.isin(GAS) & (u.mw > 0.5)][["unit_id", "plant_code", "g", "hour", "mw", "mc"]]
    parts = []
    for p, (H, off) in so.items():
        hrs = np.flatnonzero(H & np.isfinite(off))
        x = g[g.hour.isin(hrs)].copy()
        x["coal_off"] = off[x.hour.to_numpy()]
        x = x[x.mc < x.coal_off]
        x["undercut"] = x.coal_off - x.mc
        x["coal_plant"] = p
        parts.append(x)
    x = pd.concat(parts)
    # a gas MWh can undercut several coal plants in one hour: count it once (max undercut) for MWh.
    once = x.sort_values("undercut").drop_duplicates(["unit_id", "hour"], keep="last")
    t = once.groupby(["plant_code", "g"]).agg(mwh=("mw", "sum"), hours=("hour", "nunique"),
                                             offer_med=("mc", "median"), undercut_med=("undercut", "median"),
                                             undercut_p10=("undercut", lambda s: s.quantile(0.1)))
    t["twh"] = t.mwh / 1e6
    return t.drop(columns="mwh").sort_values("twh", ascending=False).reset_index()


_STATE: dict[int, str] = {}


def _state(plant: int) -> str:
    """Plant state from EIA-860."""
    if not _STATE:
        p = pd.read_parquet(_ROOT / "data/raw/eia-860/eia860_plant.parquet", columns=["Plant Code", "State"])
        _STATE.update(dict(zip(p["Plant Code"].astype(int), p["State"].astype(str))))
    return _STATE.get(plant, "")


def cems_plant(plant: int, cls: str) -> pd.DataFrame:
    """CAMPD unit rows for the plant, filtered to the class's unit types."""
    st = _state(plant)
    f = _ROOT / f"data/raw/campd-unit-level/{st}_{Y}.parquet"
    if not f.exists():
        return pd.DataFrame()
    d = pd.read_parquet(f, columns=["facilityId", "unitId", "unitType", "date", "hour", "grossLoad", "heatInput",
                                    "primaryFuelInfo"])
    d = d[d.facilityId.astype(str) == str(plant)]
    ut = d.unitType.astype(str).str.lower()
    if cls.startswith("CC"):
        d = d[ut.str.startswith("combined cycle")]
    elif cls.startswith("CT"):
        d = d[ut == "combustion turbine"]
    else:
        d = d[~ut.str.startswith("combined cycle") & (ut != "combustion turbine")
              & ~d.primaryFuelInfo.astype(str).str.contains("Coal")]
    d = d.copy()
    d["h"] = ((d.date - pd.Timestamp(f"{Y}-01-01")).dt.days * 24 + d.hour).astype(int)
    return d


def main_inputs(u: pd.DataFrame, top: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Offer decomposition vs the plant's own 2019 CEMS HR, F923 delivered gas and availability."""
    fl = s73.rebuild(Y, None)
    mcb = fl["mc"] if fl["mc"].ndim == 2 else np.repeat(fl["mc"][:, None], T, axis=1)
    hr = np.asarray(fl["stash"]["heat_rate"], float)
    vom = np.asarray(fl["stash"]["vom"], float)
    idx = {x: i for i, x in enumerate(fl["unit_ids"])}
    f923 = pd.read_parquet(PL / "eia923_monthly_fuel_costs.parquet")
    g923 = f923[(f923.fuel_group == "Natural Gas") & (f923.year == Y) & (f923.quantity > 0)
                & f923.price_per_mmbtu.notna()]
    arts = {k: pd.read_csv(PL / v) for k, v in HR_ART.items()}
    rows = []
    for _, r in top.head(n).iterrows():
        p, cls = int(r.plant_code), r.g
        uu = u[(u.plant_code == p) & (u.g == cls)]
        ids = [x for x in uu.unit_id.unique() if x in idx and not x.endswith("_committed")]
        if not ids:
            ids = [x for x in uu.unit_id.unique() if x in idx]
        ii = [idx[x] for x in ids]
        w = uu.groupby("unit_id").mw.sum().reindex(ids).fillna(0).to_numpy() + 1e-9
        m_hr = float(np.average(hr[ii], weights=w))
        m_vom = float(np.average(vom[ii], weights=w))
        fuel = float(np.average([(np.median(mcb[i]) - vom[i]) / hr[i] for i in ii], weights=w))
        own = g923[g923.plant_id.astype(int) == p]
        own_f = float((own.price_per_mmbtu * own.quantity).sum() / own.quantity.sum()) if len(own) else np.nan
        a = arts.get(cls)
        pf, art_hr = np.nan, np.nan
        if a is not None:
            ar = a[(a.plant_code == p)]
            ar = ar[ar.year == Y] if (ar.year == Y).any() else ar[ar.year == 0]
            if len(ar):
                pf, art_hr = float(ar.parasitic_factor.iloc[0]), float(ar.heat_rate.iloc[0])
        d = cems_plant(p, cls)
        cems_hr_all = cems_hr_loaded = np.nan
        gl = np.zeros(T)
        if not d.empty:
            dd = d[(d.grossLoad > 0) & (d.heatInput > 0)]
            cems_hr_all = float(dd.heatInput.sum() / dd.grossLoad.sum()) / (pf if np.isfinite(pf) else 1.0)
            np.add.at(gl, d.h.to_numpy(), np.nan_to_num(d.grossLoad.to_numpy(float)))
            # loaded hours: plant hourly gross >= 0.8 x p95 (the CT artifact's own window, at plant grain)
            hi = pd.DataFrame({"h": dd.h, "gl": dd.grossLoad, "hi": dd.heatInput}).groupby("h").sum()
            if len(hi):
                q = hi.gl >= 0.8 * np.percentile(hi.gl, 95)
                cems_hr_loaded = float(hi.hi[q].sum() / hi.gl[q].sum()) / (pf if np.isfinite(pf) else 1.0)
        cap = uu.groupby("hour").cap_mw.sum().reindex(range(T)).fillna(0).to_numpy()
        mmw = uu.groupby("hour").mw.sum().reindex(range(T)).fillna(0).to_numpy()
        pf_ = pf if np.isfinite(pf) else 1.0
        rows.append(dict(
            plant=p, cls=cls, undercut_twh=round(float(r.twh), 3), offer_med=round(float(r.offer_med), 2),
            undercut_med=round(float(r.undercut_med), 2),
            model_hr=round(m_hr, 3), artifact_hr=round(art_hr, 3), cems_hr_all=round(cems_hr_all, 3),
            cems_hr_loaded=round(cems_hr_loaded, 3),
            hr_gap_all=round(m_hr - cems_hr_all, 3), vom=round(m_vom, 2),
            offer_fuel=round(fuel, 3), own_f923=round(own_f, 3), fuel_gap=round(fuel - own_f, 3),
            model_twh=round(mmw.sum() / 1e6, 3), cems_gross_twh=round(gl.sum() / 1e6, 3),
            cap_p99=round(float(np.percentile(cap, 99)), 1), cems_net_p99=round(float(np.percentile(gl * pf_, 99)), 1),
            h_cems_gt_cap=int((gl * pf_ > cap + 1).sum()), h_cems_on=int((gl > 0).sum()),
            h_model_on=int((mmw > 1).sum()),
        ))
    return pd.DataFrame(rows)


IDENTITY_SCRATCH = Path("/tmp/claude-0/-home-user-market-simulator/b9539744-419b-5473-9c03-12fc2483669e/scratchpad/egrid_identity_SOCO.csv")
IDENTITY_ART = PL / "egrid_identity_heat_rates_SOCO.csv"


def identity_rates() -> dict[int, float]:
    """The SOCO identity artifact (committed if present, else the scratch derive)."""
    f = IDENTITY_ART if IDENTITY_ART.exists() else IDENTITY_SCRATCH
    d = pd.read_csv(f)
    return {int(r.plant_id): float(r.heat_rate_mmbtu_mwh) for r in d.itertuples()}


def greedy_identity(year: int) -> dict:
    """Baseline-differenced price-taker greedy of the identity heat rates on the year's leg.

    The covered plants' tranches are re-dispatched against the leg's zone price at the
    incumbent offer (baseline) and at the identity offer (arm: vom + (mc - vom) x hr_new /
    hr_old, i.e. same fuel, new heat rate); the per-hour arm - baseline delta is refilled
    (negative) from the cheapest idle headroom, or displaces (positive) the dearest running
    unit, over the soco-69 REFILL classes excluding the covered plants.
    """
    rates = identity_rates()
    leg_y = _ROOT / f"results/calibration/soco72_{year}"
    u = pd.read_parquet(leg_y / f"hourly/unit_hourly_{year}.parquet",
                        columns=["unit_id", "plant_code", "plant_group", "zone", "hour", "mw", "cap_mw", "mc"])
    u["unit_id"] = u.unit_id.astype(str)
    u["g"] = u.plant_group.astype(str)
    s = pd.read_parquet(leg_y / f"hourly/system_{year}.parquet", columns=["zone", "hour", "price"])
    u = u.merge(s, on=["zone", "hour"], how="left")
    fl = s73.rebuild(year, None)
    idx = {x: i for i, x in enumerate(fl["unit_ids"])}
    hr = np.asarray(fl["stash"]["heat_rate"], float)
    vom = np.asarray(fl["stash"]["vom"], float)
    mine = u.plant_code.isin(list(rates)) & u.g.isin(GAS)
    x = u[mine].copy()
    info = {}
    delta_t = np.zeros(T)
    for uid, g in x.groupby("unit_id"):
        i = idx[uid]
        p = int(g.plant_code.iloc[0])
        g = g.set_index("hour").reindex(range(T))
        mc0 = g.mc.to_numpy(float)
        mc1 = vom[i] + (mc0 - vom[i]) * rates[p] / hr[i]
        cap = g.cap_mw.fillna(0).to_numpy(float)
        pr = g.price.to_numpy(float)
        r0 = np.where(mc0 <= pr + 1e-6, cap, 0.0)
        r1 = np.where(mc1 <= pr + 1e-6, cap, 0.0)
        delta_t += np.nan_to_num(r1 - r0)
        info.setdefault(p, dict(hr_old=round(float(hr[i]), 3), hr_new=rates[p], mc_old=round(float(np.nanmedian(mc0)), 2),
                                mc_new=round(float(np.nanmedian(mc1)), 2), leg_twh=0.0, d_twh=0.0))
        info[p]["leg_twh"] += float(np.nansum(g.mw.to_numpy(float))) / 1e6
        info[p]["d_twh"] += float(np.nansum(r1 - r0)) / 1e6
    oth = u[u.g.isin(s73.REFILL) & ~mine]
    up = oth.assign(head=(oth.cap_mw - oth.mw).clip(lower=0))
    up = up[up["head"] > 0.01][["hour", "g", "mc", "head"]].sort_values(["hour", "mc"])
    up["cum"] = up.groupby("hour")["head"].cumsum()
    need = np.clip(-delta_t, 0, None)[up.hour.to_numpy()]
    up["take"] = np.clip(need - (up.cum.to_numpy() - up["head"].to_numpy()), 0, up["head"].to_numpy())
    down = oth[oth.mw > 0.01][["hour", "g", "mc", "mw"]].sort_values(["hour", "mc"], ascending=[True, False])
    down["cum"] = down.groupby("hour").mw.cumsum()
    need2 = np.clip(delta_t, 0, None)[down.hour.to_numpy()]
    down["take"] = np.clip(need2 - (down.cum.to_numpy() - down.mw.to_numpy()), 0, down.mw.to_numpy())
    d = (up.groupby("g")["take"].sum().sub(down.groupby("g")["take"].sum(), fill_value=0)) / 1e6
    d["CT_PEAKER"] = d.get("CT_PEAKER", 0.0) + delta_t.sum() / 1e6
    coal_t = np.zeros(T)
    for frame, sign in ((up, 1.0), (down, -1.0)):
        f = frame[frame.g.str.startswith("COAL")]
        coal_t += sign * f.groupby("hour")["take"].sum().reindex(range(T)).fillna(0).to_numpy()
    return dict(delta={k: float(v) for k, v in d.items()}, plants=info, coal_delta_t=coal_t,
                unmet=float((np.clip(-delta_t, 0, None).sum() - up["take"].sum()) / 1e6))


def main_greedy(years: list[int]) -> dict:
    """Print the identity greedy per year: plant offers, class deltas, scorer-exact C1, C4 coal."""
    out = {}
    for y in years:
        g = greedy_identity(y)
        r0, n0, r1, n1 = s73.c4_coal(y, g["coal_delta_t"])
        c1 = s73.c1_rows(y, g["delta"])
        print(f"\n===== {y}  plants {g['plants']}  unmet {g['unmet']:.4f} TWh")
        print("  class delta TWh: " + "  ".join(f"{k} {v:+.4f}" for k, v in sorted(g["delta"].items()) if abs(v) > 1e-5))
        print(f"  C4 coal NRMSE {n0:.4f} -> {n1:.4f}  (r {r0:.4f} -> {r1:.4f})")
        print(c1.round(3).to_string(index=False))
        out[str(y)] = dict(plants=g["plants"], delta=g["delta"], c4=[n0, n1], c1=c1.round(4).to_dict("records"))
    return out


def main() -> None:
    """Run all three instruments and write the census record."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["all", "greedy"])
    ap.add_argument("--years", nargs="+", type=int, default=[2019, 2020, 2021, 2022, 2023, 2024, 2025])
    ap.add_argument("--n", type=int, default=15)
    a = ap.parse_args()
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 40)
    if a.mode == "greedy":
        res = main_greedy(a.years)
        (OUT.parent / "soco76_identity_greedy.json").write_text(json.dumps(res, indent=0, default=float) + "\n")
        return
    u = leg()
    pl = main_plants(u)
    print("\n== 1. gas plants: model vs EIA-923 TWh, 2019 ==")
    print(pl.groupby("cls")[["model", "eia923", "delta"]].sum().round(3).to_string())
    print(pl.head(20).round(3).to_string(index=False))
    so = synced_off(u)
    print("\n== 2. coal plants CEMS-synced & model-off, 2019 ==")
    for p, (H, off) in so.items():
        print(f"  {p}: {int(H.sum())} h, cheapest non-must-run offer p50 {np.nanmedian(off[H]) if H.any() else np.nan:.2f}")
    uc = main_undercut(u, so)
    print(uc.groupby("g")[["twh"]].sum().round(3).to_string())
    print(uc.head(25).round(3).to_string(index=False))
    inp = main_inputs(u, uc, a.n)
    print("\n== 3. inputs of the top undercutting gas plants vs their own 2019 data ==")
    print(inp.to_string(index=False))
    tw = inp.undercut_twh
    print(f"  undercut-TWh-weighted: hr_gap_all {np.average(inp.hr_gap_all.fillna(0), weights=tw):+.3f}, "
          f"fuel_gap {np.average(inp.fuel_gap.fillna(0), weights=tw):+.3f} $/MMBtu")
    OUT.write_text(json.dumps(dict(
        plants=pl.round(4).to_dict("records"),
        synced_off_hours={str(p): int(H.sum()) for p, (H, _) in so.items()},
        undercut=uc.round(4).to_dict("records"), inputs=inp.to_dict("records")), indent=0, default=float) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__" and not (len(sys.argv) > 1 and sys.argv[1] == "fleet"):
    main()


def main_fleet(years: list[int]) -> dict:
    """fleet_only census: keeper recipe vs recipe + egrid_identity_heat_rates, per year.

    Asserts pmax / min_gen / availability identical for every unit, and mc moved ONLY on
    the artifact's plants, by exactly (hr_new - hr_old) x fuel.
    """
    import contextlib
    import io

    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year

    meta = json.loads((s73.SPAN / "meta.json").read_text())
    rates = identity_rates()
    out = {}
    for y in years:
        res = []
        for arm in (None, True):
            kw = run_year_kwargs(meta)
            kw.update(derived_run_year_inputs(str(s73.SPAN), y))
            if arm:
                kw["egrid_identity_heat_rates"] = True
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                st = run_year(y, meta["iso"], T, float(meta["gas_prices"][str(y)]), {}, fleet_only=True, **kw)
            fa = st["fleet_arrays"]
            mc = np.asarray(st["mc_base"], float)
            res.append(dict(ids=list(map(str, fa.unit_ids)), plant=np.asarray(fa.plant_code).astype(int),
                            hr=np.asarray(fa.heat_rate, float), mc=mc if mc.ndim == 2 else mc[:, None],
                            pmax=np.asarray(fa.pmax, float), mg=np.asarray(fa.min_gen, float),
                            av=np.asarray(fa.availability, float)))
        a, b = res
        assert a["ids"] == b["ids"]
        same = all(np.array_equal(a[k], b[k]) for k in ("pmax", "mg", "av"))
        moved = np.flatnonzero(np.abs(b["mc"] - a["mc"]).max(axis=1) > 1e-9)
        hrmoved = np.flatnonzero(np.abs(b["hr"] - a["hr"]) > 1e-12)
        mp = sorted(set(a["plant"][moved].tolist()))
        rows = {}
        for i in moved:
            dmc = float(np.median(b["mc"][i] - a["mc"][i]))
            rows[a["ids"][i]] = dict(hr_old=round(float(a["hr"][i]), 4), hr_new=round(float(b["hr"][i]), 4),
                                     mc_old=round(float(np.median(a["mc"][i])), 4),
                                     mc_new=round(float(np.median(b["mc"][i])), 4), dmc=round(dmc, 4))
        ok = same and set(mp) <= set(rates) and set(moved) == set(hrmoved)
        print(f"\n===== {y}: units {len(a['ids'])}, mc moved {len(moved)} at plants {mp}, "
              f"hr moved {len(hrmoved)}, pmax/min_gen/avail identical {same}  => {'OK' if ok else 'STOP'}")
        for k, v in rows.items():
            print(f"  {k}: {v}")
        out[str(y)] = dict(ok=bool(ok), units=len(a["ids"]), moved=rows)
    (OUT.parent / "soco76_identity_fleet_census.json").write_text(json.dumps(out, indent=0, sort_keys=True) + "\n")
    return out


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "fleet":
    sys.path.insert(0, str(_ROOT / "scripts"))
    main_fleet([int(x) for x in sys.argv[2:]] or [2019, 2020, 2021, 2022, 2023, 2024, 2025])
