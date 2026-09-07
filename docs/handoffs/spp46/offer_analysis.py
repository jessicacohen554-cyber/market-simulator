"""SPP-46 phase 0.2 (zero-LP): what the LP's OWN offer arrays say about the gas split.

Reads rows_<year>.csv + the scratch arrays (offer_arrays.py) and keeper-3's committed
sidecars. Four parts, none of which reads a criterion:

A. FUEL PROVENANCE — per gas class, the cap-weighted delivered gas price of the rows
   priced from their OWN EIA-923 report vs the rows GAP-FILLED from the zone pool, beside
   the EIA state delivered-to-electric-power means (N3045KS3/OK3/TX3, $/Mcf / 1.037).
B. MERIT-ORDER OVERLAP — the availability-weighted mc distribution per class and the
   CC / CT / ST_GAS crossover (share of CT capacity cheaper than the CC median, etc.).
C. IN-MERIT RECONSTRUCTION at keeper-3's own P1 zonal prices — strict in-merit and
   marginal capacity per class vs the keeper's class dispatch (the LP's dispatch must sit
   between the two), and for the under-run classes the cap-weighted distribution of
   price / mc over their OUT-of-merit row-hours (the multiplier that would admit them at
   an unchanged price — a bound, since the price falls as they enter).
D. RE-CLEARING PREDICTOR — per hour, the thermal quantity the keeper cleared is
   re-cleared against re-priced rows (band multipliers scale the FUEL component only:
   mc' = vom + (mc - vom) x m, the HR_Mult construction), zones pooled when the keeper's
   zonal prices agree, else separately. A REACH test for candidate (B): the class-energy
   response a per-class multiplier set implies. It selects nothing; the candidate's values,
   if any, come from the declared conduct construction, never from this table.

Usage: uv run python docs/handoffs/spp46/offer_analysis.py <scratch_dir>
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs/handoffs/spp46"
SCR = Path(sys.argv[1])
BUNDLE = REPO / "results/calibration/spp43_screened_B"
YEARS = (2023, 2024, 2025)
GAS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP", "ST_CHP")
THERMAL = ["CC_CHP", "CC_REGULAR", "COAL_LIGNITE", "COAL_PRB", "CT_CHP", "CT_PEAKER", "OTHER", "ST_CHP", "ST_GAS", "biomass", "nuclear", "oil"]
TOL = 0.25
STATE_DELIVERED = {"KS": {2023: 3.202, 2024: 2.817, 2025: 4.492}, "OK": {2023: 2.848, 2024: 2.944, 2025: np.nan},
                   "TX": {2023: 2.538, 2024: 2.105, 2025: 3.063}}
SETS = {
    "CT x1.1": {"CT_PEAKER": 1.1}, "CT x1.2": {"CT_PEAKER": 1.2}, "CT x1.3": {"CT_PEAKER": 1.3},
    "CT x1.5": {"CT_PEAKER": 1.5}, "CT x2.0": {"CT_PEAKER": 2.0},
    "ST x0.9": {"ST_GAS": 0.9}, "ST x0.8": {"ST_GAS": 0.8}, "ST x0.7": {"ST_GAS": 0.7}, "ST x0.6": {"ST_GAS": 0.6}, "ST x0.5": {"ST_GAS": 0.5},
    "CC x0.9": {"CC_REGULAR": 0.9}, "CC x0.8": {"CC_REGULAR": 0.8}, "CC x0.7": {"CC_REGULAR": 0.7},
    "merit-order lane B": {"CC_REGULAR": 0.8028, "CT_PEAKER": 0.888, "ST_GAS": 0.8949, "COAL_PRB": 0.7838, "COAL_LIGNITE": 0.8152, "CT_CHP": 0.8019, "ST_CHP": 0.8271},
}


def wq(x, w, qs):
    o = np.argsort(x); x, w = x[o], w[o]; c = np.cumsum(w) / w.sum()
    return [float(np.interp(q, c, x)) for q in qs]


def scoring_class(row):
    # the scorer's class: COAL rows score as COAL_PRB / COAL_LIGNITE by supply; keep plant_group elsewhere
    return row.plant_group if row.plant_group else row.fuel_type


def main() -> None:
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 60)
    for year in YEARS:
        print(f"\n\n================ {year} ================")
        rows = pd.read_csv(OUT / f"rows_{year}.csv")
        z = np.load(SCR / f"arrays_{year}.npz")
        mc, av = z["mc"].astype(float), z["avail"].astype(float)
        n, T = mc.shape
        cap = rows.pmax.to_numpy()[:, None] * av
        vom = rows.vom.to_numpy()[:, None]
        klass = rows.plant_group.where(rows.plant_group != "", rows.fuel_type).to_numpy()
        zone = rows.zone.to_numpy()
        ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet"); ch = ch[ch["pass"] == "P1"]
        D = ch.pivot_table(index="hour", columns="klass", values="mw").sort_index()
        sysp = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet"); sysp = sysp[sysp["pass"] == "P1"]
        P = sysp.pivot_table(index="hour", columns="zone", values="price").sort_index()
        pN, pS = P["SPP-North"].to_numpy(), P["SPP-South"].to_numpy()
        p_row = np.where(zone[:, None] == "SPP-North", pN[None, :], pS[None, :])
        aw = cap.mean(axis=1)  # availability-weighted MW per row

        # ---- A. fuel provenance
        print("\n--- A. delivered gas price by provenance (cap-weighted, $/MMBtu; MW = avail-wtd)")
        rec = []
        for k in GAS:
            m = klass == k
            for prov, mm in (("own", m & (rows.own_months > 0)), ("gapfill", m & (rows.own_months == 0))):
                if mm.sum() == 0:
                    continue
                w = aw[mm]
                rec.append(dict(klass=k, prov=prov, rows=int(mm.sum()), plants=int(rows.plant_code[mm].nunique()), mw=round(w.sum(), 0),
                                fuel=round(float(np.average(rows.fuel_mean[mm], weights=w)), 3),
                                hr=round(float(np.average(rows.heat_rate[mm], weights=w)), 2),
                                mc=round(float(np.average(rows.mc_avail_mean[mm], weights=w)), 2)))
        print(pd.DataFrame(rec).to_string(index=False))
        print("EIA state delivered-to-EP means:", {s: v[year] for s, v in STATE_DELIVERED.items()})
        # top own-reported plants per class
        for k in ("ST_GAS", "CT_PEAKER", "CC_REGULAR"):
            sub = rows[(klass == k)].groupby("plant_code").agg(name=("name", "first"), zone=("zone", "first"), mw=("pmax", "sum"), own_months=("own_months", "first"),
                                                              fuel=("fuel_mean", "mean"), hr=("heat_rate", "mean"), mc=("mc_avail_mean", "mean")).sort_values("mw", ascending=False)
            print(f"\n{k} plants (top 12 by MW):"); print(sub.head(12).round(2).to_string())

        # ---- B. merit-order overlap
        print("\n--- B. availability-weighted annual-mean mc per class (p10/p25/p50/p75/p90) and crossover")
        med = {}
        for k in ("COAL", "CC_REGULAR", "CT_PEAKER", "ST_GAS"):
            m = klass == k; q = wq(rows.mc_avail_mean.to_numpy()[m], aw[m], [0.1, 0.25, 0.5, 0.75, 0.9]); med[k] = q[2]
            print(f"{k:12s} MW {aw[m].sum():8.0f}  " + " ".join(f"{v:6.2f}" for v in q))
        for a, b in (("CT_PEAKER", "CC_REGULAR"), ("CT_PEAKER", "ST_GAS"), ("CC_REGULAR", "ST_GAS")):
            ma, mb = klass == a, klass == b
            sa = aw[ma][rows.mc_avail_mean.to_numpy()[ma] < med[b]].sum() / aw[ma].sum()
            sb = aw[mb][rows.mc_avail_mean.to_numpy()[mb] > med[a]].sum() / aw[mb].sum()
            print(f"  share of {a} MW cheaper than {b} median: {sa:.3f};  share of {b} MW dearer than {a} median: {sb:.3f}")

        # ---- C. in-merit reconstruction at keeper prices
        print("\n--- C. in-merit capacity at keeper-3's own zonal prices vs keeper dispatch (TWh)")
        strict = mc < p_row - TOL; marg = np.abs(mc - p_row) <= TOL; outm = mc > p_row + TOL
        rec = []
        for k in ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL_PRB", "COAL_LIGNITE"):
            m = klass == ("COAL" if k.startswith("COAL") else k)
            if k.startswith("COAL"):  # split COAL rows by scoring class through the keeper's own dispatch ratio: report COAL total instead
                continue
            s = (cap[m] * strict[m]).sum() / 1e6; g = (cap[m] * marg[m]).sum() / 1e6; o = (cap[m] * outm[m]).sum() / 1e6
            d = D[k].sum() / 1e6 if k in D else np.nan
            # hours where D outside [strict, strict+marg] by > 100 MW
            sh = (cap[m] * strict[m]).sum(axis=0); gh = (cap[m] * marg[m]).sum(axis=0); dh = D[k].to_numpy()
            viol = int(((dh < sh - 100) | (dh > sh + gh + 100)).sum())
            rec.append(dict(klass=k, strict_twh=round(s, 3), marginal_twh=round(g, 3), out_twh=round(o, 3), keeper_twh=round(d, 3), hours_outside_band=viol,
                            avail_twh=round(cap[m].sum() / 1e6, 3)))
            if k in ("CC_REGULAR", "ST_GAS"):
                r = (p_row[m] / mc[m])[outm[m]]; w = cap[m][outm[m]]
                q = wq(r, w, [0.1, 0.25, 0.5, 0.75, 0.9])
                print(f"  {k}: OUT-of-merit row-hours: price/mc cap-wtd p10/p25/p50/p75/p90 = " + " ".join(f"{v:.3f}" for v in q)
                      + f"; share of out-of-merit MWh with price/mc >= 0.9: {w[r >= 0.9].sum() / w.sum():.3f}, >= 0.8: {w[r >= 0.8].sum() / w.sum():.3f}, >= 0.7: {w[r >= 0.7].sum() / w.sum():.3f}")
        coalm = klass == "COAL"
        rec.append(dict(klass="COAL(all)", strict_twh=round((cap[coalm] * strict[coalm]).sum() / 1e6, 3), marginal_twh=round((cap[coalm] * marg[coalm]).sum() / 1e6, 3),
                        out_twh=round((cap[coalm] * outm[coalm]).sum() / 1e6, 3), keeper_twh=round((D["COAL_PRB"].sum() + D["COAL_LIGNITE"].sum()) / 1e6, 3), hours_outside_band=-1, avail_twh=round(cap[coalm].sum() / 1e6, 3)))
        print(pd.DataFrame(rec).to_string(index=False))
        # CT dispatch by price band: how much CT energy the keeper runs at prices below the CC/ST medians
        ctm = klass == "CT_PEAKER"
        print(f"  CT_PEAKER strict in-merit energy at hours where the zonal price < {med['CC_REGULAR']:.1f} (CC median mc): "
              f"{(cap[ctm] * strict[ctm] * (p_row[ctm] < med['CC_REGULAR'])).sum() / 1e6:.3f} TWh")
        # who is marginal (cap-weighted within tol)
        mg = {k: float((cap[klass == k] * marg[klass == k]).sum()) for k in ("COAL", "CC_REGULAR", "CT_PEAKER", "ST_GAS")}
        tot = sum(mg.values()); print("  marginal-capacity share (|mc-p|<=tol):", {k: round(v / tot, 3) for k, v in mg.items()})

        # ---- D. re-clearing predictor
        print("\n--- D. re-clearing predictor (reach test) — dE per class (TWh) and LW price ratio")
        thermal_rows = np.isin(rows.fuel_type.to_numpy(), ["hydro", "wind", "solar"], invert=True) & (rows.fuel_type.to_numpy() != "storage")
        Dth = D[[c for c in THERMAL if c in D]].sum(axis=1).to_numpy()
        pooled = np.abs(pN - pS) < 0.01
        isN = zone == "SPP-North"
        sN = (cap[isN] * strict[isN]).sum(axis=0); sS = (cap[~isN] * strict[~isN]).sum(axis=0)
        gN = (cap[isN] * marg[isN]).sum(axis=0); gS = (cap[~isN] * marg[~isN]).sum(axis=0)
        r = np.clip((Dth - sN - sS) / np.maximum(gN + gS, 1e-9), 0, 1)
        QN, QS = sN + r * gN, sS + r * gS
        load_w = D.sum(axis=1).to_numpy()
        capT = cap * thermal_rows[:, None]

        def clear(mc_arm):
            def run(mask_rows, Q):
                c = capT * mask_rows[:, None]
                order = np.argsort(mc_arm, axis=0, kind="stable")
                cs = np.take_along_axis(c, order, axis=0); ms = np.take_along_axis(mc_arm, order, axis=0)
                cum = np.cumsum(cs, axis=0); before = cum - cs
                alloc_s = np.clip(Q[None, :] - before, 0, cs)
                alloc = np.empty_like(alloc_s); np.put_along_axis(alloc, order, alloc_s, axis=0)
                idx = np.argmax(cum >= Q[None, :], axis=0)
                price = ms[idx, np.arange(T)]
                return alloc, price
            a_all, p_all = run(np.ones(n, bool), Dth)
            a_N, p_N = run(isN, QN); a_S, p_S = run(~isN, QS)
            alloc = np.where(pooled[None, :], a_all, a_N + a_S)
            price_avg = np.where(pooled, p_all, 0.5 * (p_N + p_S))
            return alloc, price_avg

        base_alloc, base_price = clear(mc)
        E0 = {k: base_alloc[klass == k].sum(axis=0) for k in ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL")}
        Dcoal = (D["COAL_PRB"] + D["COAL_LIGNITE"]).to_numpy()
        keep = np.ones(T, bool)
        for k, dk in (("CC_REGULAR", D["CC_REGULAR"].to_numpy()), ("CT_PEAKER", D["CT_PEAKER"].to_numpy()), ("ST_GAS", D["ST_GAS"].to_numpy()), ("COAL", Dcoal)):
            keep &= np.abs(E0[k] - dk) <= 250
        print(f"  self-check at 1.0: recon vs keeper TWh — " + ", ".join(f"{k} {E0[k].sum() / 1e6:.2f}/{v.sum() / 1e6:.2f}" for k, v in (("CC_REGULAR", D['CC_REGULAR']), ("CT_PEAKER", D['CT_PEAKER']), ("ST_GAS", D['ST_GAS']), ("COAL", Dcoal)))
              + f"; retained hours (all four within 250 MW): {keep.sum()} of {T}; LW price recon/keeper {np.average(base_price, weights=load_w) / np.average(0.5 * (pN + pS), weights=load_w):.3f}")
        rec = []
        for name, mults in SETS.items():
            m_row = np.ones(n)
            for k, v in mults.items():
                m_row[klass == k] = v
            mc_arm = vom + (mc - vom) * m_row[:, None]
            alloc, price = clear(mc_arm)
            E1 = {k: alloc[klass == k].sum(axis=0) for k in E0}
            d = {k: dict(all=(E1[k] - E0[k]).sum() / 1e6, kept=(E1[k] - E0[k])[keep].sum() / 1e6 * T / keep.sum()) for k in E0}
            rec.append(dict(set=name, **{f"d{k.split('_')[0]}_all": round(d[k]["all"], 2) for k in E0}, **{f"d{k.split('_')[0]}_kept": round(d[k]["kept"], 2) for k in E0},
                            lw_price_ratio=round(float(np.average(price, weights=load_w) / np.average(base_price, weights=load_w)), 3)))
        print(pd.DataFrame(rec).to_string(index=False))
        print("  (kept = retained-hour delta scaled to 8760; target 2024 object: CT -9.94 / CC +8.60 TWh)")


if __name__ == "__main__":
    main()
