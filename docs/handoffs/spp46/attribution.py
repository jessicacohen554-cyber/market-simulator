"""SPP-46 phase 0.2b (zero-LP): attribute the gas split PLANT BY PLANT to the LP's own
input rows, and compute the offer-array delta of the object phase 0 actually found —
a plausibility screen on the EIA-923 plant-month gas price seam.

Per year and merchant gas class (CC_REGULAR / CT_PEAKER / ST_GAS), per plant:
  model in-merit energy at keeper-3's own zonal prices (strict + half the marginal
  band — ST_GAS and CT dispatch sit inside that band in >97 % of hours, part C of
  offer_analysis.py), CAMPD measured gross generation (campd_census.py), the
  difference, and three INPUT flags read off the row itself:
    fuel_low  — an own-reported F923 month below 0.5 x the state's EIA
                delivered-to-electric-power price that month (N3045<ST>3, $/Mcf/1.037)
    fuel_high — an own-reported month above 2.0 x that reference
    hr_flag   — a CT row whose PLANT-level heat rate is < 6 MMBtu/MWh (physically
                impossible for a simple-cycle unit) or a CC row whose plant-level heat
                rate is > 10 (a mixed CC/ST/coal plant carrying the plant average)
The split is then summed by flag group, so the record says how much of the 2024
object sits on rows whose own input is outside its plausibility band.

The SCREEN ARITHMETIC (declared here, one rule): an own-reported month outside
[0.5 R_m, 2.0 R_m] is replaced by R_m (the state reference); mc' = mc + HR x (fuel' -
fuel) on that row; the keeper's cleared thermal quantity is re-cleared against the
re-priced rows (offer_analysis.py's predictor). Reported: plant-months screened, MW
touched, dE per class, LW price ratio. A second band [0.6, 1.67] is reported as a
robustness line. Gap-filled rows are left untouched (the pool they draw from would
also move under a screen; that effect is stated, not modelled).

Usage: uv run python docs/handoffs/spp46/attribution.py <scratch_dir>
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
from market_sim.data.fuel.plant_prices import _load_monthly_cache  # noqa: E402
from market_sim.data.eia923 import plant_month_price_grid  # noqa: E402

OUT = REPO / "docs/handoffs/spp46"; SCR = Path(sys.argv[1])
BUNDLE = REPO / "results/calibration/spp43_screened_B"
YEARS = (2023, 2024, 2025); TOL = 0.25
CLASSES = {"CC_REGULAR": "cc", "CT_PEAKER": "ct", "ST_GAS": "st"}
THERMAL = ["CC_CHP", "CC_REGULAR", "COAL_LIGNITE", "COAL_PRB", "CT_CHP", "CT_PEAKER", "OTHER", "ST_CHP", "ST_GAS", "biomass", "nuclear", "oil"]
ZONE_STATE = {"SPP-North": "KS", "SPP-South": "OK"}
MONTH_H = np.repeat(np.arange(12), [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744])


def state_ref() -> dict[str, dict[int, np.ndarray]]:
    out = {}
    for st in ("KS", "OK", "TX", "NM"):
        x = pd.read_excel(REPO / f"data/raw/gas-prices/eia_N3045{st}3m_2026-09-06.xls", sheet_name=None)
        for k, v in x.items():
            if "Data" in k:
                v = v.iloc[2:].copy(); v.columns = ["date", "price"]
                v["date"] = pd.to_datetime(v.date); v["price"] = pd.to_numeric(v.price, errors="coerce") / 1.037
                v["ym"] = v.date.dt.year * 100 + v.date.dt.month
                s = v.groupby("ym")["price"].mean()
                out[st] = {y: s.reindex([y * 100 + m for m in range(1, 13)]).to_numpy(dtype=float) for y in YEARS}
    # OK 2025 is not yet published: fall back to the mean of the published SPP states, and say so
    for y in YEARS:
        for st in out:
            if np.isnan(out[st][y]).all():
                others = [out[o][y] for o in out if not np.isnan(out[o][y]).all()]
                out[st][y] = np.nanmean(np.vstack(others), axis=0)
                print(f"  NOTE: {st} {y} state series absent -> mean of published SPP states used as its reference")
    return out


def main() -> None:
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
    costs = _load_monthly_cache(None)
    plant_state = costs.groupby("plant_id")["state"].first()
    ref = state_ref()
    for year in YEARS:
        print(f"\n\n================ {year} ================")
        rows = pd.read_csv(OUT / f"rows_{year}.csv")
        z = np.load(SCR / f"arrays_{year}.npz"); mc, av, fuel = z["mc"].astype(float), z["avail"].astype(float), z["fuel"].astype(float)
        n, T = mc.shape
        cap = rows.pmax.to_numpy()[:, None] * av
        klass = rows.plant_group.where(rows.plant_group != "", rows.fuel_type).to_numpy()
        zone = rows.zone.to_numpy()
        ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet"); ch = ch[ch["pass"] == "P1"]
        D = ch.pivot_table(index="hour", columns="klass", values="mw").sort_index()
        sysp = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet"); sysp = sysp[sysp["pass"] == "P1"]
        P = sysp.pivot_table(index="hour", columns="zone", values="price").sort_index()
        pN, pS = P["SPP-North"].to_numpy(), P["SPP-South"].to_numpy()
        p_row = np.where(zone[:, None] == "SPP-North", pN[None, :], pS[None, :])
        strict = mc < p_row - TOL; marg = np.abs(mc - p_row) <= TOL
        e_row = (cap * (strict + 0.5 * marg)).sum(axis=1) / 1e3  # GWh in-merit energy per row
        grid = plant_month_price_grid(costs, year, "Natural Gas")
        # per-row flags and screened fuel
        fuel_s = fuel.copy(); flag_low = np.zeros(n, bool); flag_high = np.zeros(n, bool); n_screened = {}
        fuel_s2 = fuel.copy(); n_screened2 = {}
        for g in range(n):
            if not str(rows.fuel_type[g]).startswith("gas"):
                continue
            pc = int(rows.plant_code[g]); own = grid.get(pc)
            if own is None:
                continue
            st = plant_state.get(pc, ZONE_STATE[rows.zone[g]])
            R = ref.get(st, ref[ZONE_STATE[rows.zone[g]]])[year]
            for m in range(12):
                if np.isnan(own[m]):
                    continue
                if own[m] < 0.5 * R[m]:
                    flag_low[g] = True
                if own[m] > 2.0 * R[m]:
                    flag_high[g] = True
                if own[m] < 0.5 * R[m] or own[m] > 2.0 * R[m]:
                    fuel_s[g, MONTH_H == m] = R[m]; n_screened[(pc, m)] = 1
                if own[m] < 0.6 * R[m] or own[m] > R[m] / 0.6:
                    fuel_s2[g, MONTH_H == m] = R[m]; n_screened2[(pc, m)] = 1
        hr = rows.heat_rate.to_numpy()
        flag_hr = ((klass == "CT_PEAKER") & (hr < 6.0)) | ((klass == "CC_REGULAR") & (hr > 10.0))
        rows["e_model_gwh"] = e_row; rows["flag_low"] = flag_low; rows["flag_high"] = flag_high; rows["flag_hr"] = flag_hr
        rows["aw_mw"] = cap.mean(axis=1)
        tot = []
        for grp, tag in CLASSES.items():
            cen = pd.read_csv(OUT / f"census_{year}_{tag}.csv").set_index("plant_code")
            sub = rows[klass == grp]
            pl = sub.groupby("plant_code").agg(name=("name", "first"), zone=("zone", "first"), mw=("pmax", "sum"), aw_mw=("aw_mw", "sum"),
                                              own_months=("own_months", "first"), fuel=("fuel_mean", "mean"), hr=("heat_rate", "first"),
                                              e_model=("e_model_gwh", "sum"), flag_low=("flag_low", "any"), flag_high=("flag_high", "any"), flag_hr=("flag_hr", "any"))
            pl["e_campd"] = cen["gen_gwh"].reindex(pl.index)
            pl["has_campd"] = pl.e_campd.notna()
            pl["delta"] = pl.e_model - pl.e_campd.fillna(0.0)
            pl["flag"] = np.select([pl.flag_hr, pl.flag_low, pl.flag_high], ["HR", "fuel_low", "fuel_high"], "clean")
            pl = pl.sort_values("delta", ascending=False)
            print(f"\n--- {grp}: model in-merit vs CAMPD, GWh (top/bottom 8 by delta)")
            show = pd.concat([pl.head(8), pl.tail(8)]).round(2)
            print(show[["name", "zone", "mw", "own_months", "fuel", "hr", "e_model", "e_campd", "delta", "flag"]].to_string())
            grpsum = pl.groupby("flag").agg(plants=("mw", "size"), mw=("mw", "sum"), e_model=("e_model", "sum"), e_campd=("e_campd", "sum"), delta=("delta", "sum")).round(1)
            print(f"{grp} by flag group (GWh):\n{grpsum.to_string()}")
            print(f"{grp} totals: model {pl.e_model.sum() / 1e3:.2f} TWh (keeper {D[grp].sum() / 1e6:.2f}), CAMPD {pl.e_campd.sum() / 1e3:.2f} TWh, plants without a CAMPD series: {int((~pl.has_campd).sum())} ({pl[~pl.has_campd].mw.sum():.0f} MW, {pl[~pl.has_campd].e_model.sum():.0f} GWh model)")
            pl.to_csv(OUT / f"attribution_{year}_{tag}.csv")
            tot.append(pl.assign(klass=grp))
        # ---- screen arithmetic (re-clearing predictor)
        thermal_rows = ~np.isin(rows.fuel_type.to_numpy(), ["hydro", "wind", "solar"])
        Dth = D[[c for c in THERMAL if c in D]].sum(axis=1).to_numpy()
        pooled = np.abs(pN - pS) < 0.01; isN = zone == "SPP-North"
        sN = (cap[isN] * strict[isN]).sum(axis=0); sS = (cap[~isN] * strict[~isN]).sum(axis=0)
        gN = (cap[isN] * marg[isN]).sum(axis=0); gS = (cap[~isN] * marg[~isN]).sum(axis=0)
        r = np.clip((Dth - sN - sS) / np.maximum(gN + gS, 1e-9), 0, 1); QN, QS = sN + r * gN, sS + r * gS
        capT = cap * thermal_rows[:, None]; load_w = D.sum(axis=1).to_numpy()

        def clear(mc_arm):
            def run(mask_rows, Q):
                c = capT * mask_rows[:, None]; order = np.argsort(mc_arm, axis=0, kind="stable")
                cs = np.take_along_axis(c, order, axis=0); ms = np.take_along_axis(mc_arm, order, axis=0)
                cum = np.cumsum(cs, axis=0); before = cum - cs
                alloc_s = np.clip(Q[None, :] - before, 0, cs); alloc = np.empty_like(alloc_s); np.put_along_axis(alloc, order, alloc_s, axis=0)
                idx = np.argmax(cum >= Q[None, :], axis=0); return alloc, ms[idx, np.arange(T)]
            a_all, p_all = run(np.ones(n, bool), Dth); a_N, p_N = run(isN, QN); a_S, p_S = run(~isN, QS)
            return np.where(pooled[None, :], a_all, a_N + a_S), np.where(pooled, p_all, 0.5 * (p_N + p_S))

        base_alloc, base_price = clear(mc)
        print("\n--- screen arithmetic: re-clearing with the F923 own-month plausibility screen (dE TWh vs the 1.0 reconstruction)")
        for label, fs, ns in (("band [0.5, 2.0]", fuel_s, n_screened), ("band [0.6, 1.67]", fuel_s2, n_screened2)):
            mc_arm = mc + hr[:, None] * (fs - fuel)
            alloc, price = clear(mc_arm)
            touched = np.any(fs != fuel, axis=1)
            d = {k: (alloc[klass == k].sum() - base_alloc[klass == k].sum()) / 1e6 for k in ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL", "CC_CHP", "CT_CHP", "ST_CHP")}
            print(f"  {label}: plant-months screened {len(ns)}, rows touched {int(touched.sum())} ({rows.pmax[touched].sum():.0f} MW; low-side rows {int((touched & flag_low).sum())}, high-side {int((touched & flag_high).sum())}); "
                  + ", ".join(f"{k} {v:+.2f}" for k, v in d.items()) + f"; LW price ratio {np.average(price, weights=load_w) / np.average(base_price, weights=load_w):.3f}")
        # combined: price screen [0.5, 2.0] + the CT physical heat-rate floor (HEAT_RATE_BINS["gas_ct"]["aero"] = 9.0,
        # the simple-cycle analogue of EGRID_CC_HR_PHYSICAL_CEILING) on CT rows whose plant-level eGRID rate is < 6
        hr_fix = np.where((klass == "CT_PEAKER") & (hr < 6.0), 9.0, hr)
        mc_arm = mc + hr[:, None] * (fuel_s - fuel) + (hr_fix - hr)[:, None] * fuel_s
        alloc, price = clear(mc_arm)
        d = {k: (alloc[klass == k].sum() - base_alloc[klass == k].sum()) / 1e6 for k in ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL", "CC_CHP", "CT_CHP", "ST_CHP")}
        print("  band [0.5, 2.0] + CT HR floor 9.0 on HR<6 rows: " + ", ".join(f"{k} {v:+.2f}" for k, v in d.items()) + f"; LW price ratio {np.average(price, weights=load_w) / np.average(base_price, weights=load_w):.3f}")
        # HR flag energy
        for k in ("CT_PEAKER", "CC_REGULAR"):
            m = (klass == k) & flag_hr
            print(f"  HR-flagged {k}: {int(m.sum())} rows / {rows.pmax[m].sum():.0f} MW / model in-merit {e_row[m].sum() / 1e3:.2f} TWh, plants {sorted(set(rows.plant_code[m]))}")
        pd.concat(tot).to_csv(OUT / f"attribution_{year}_all.csv")


if __name__ == "__main__":
    main()
