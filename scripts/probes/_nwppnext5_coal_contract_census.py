"""NWPP-NEXT-5 phase 0: coal period fuel-take obligation census. ZERO LP.

Tests the RESULT-nwppnext4 §3 hypothesis that NWPP coal (PacifiCorp Utah/Wyoming,
Colstrip, North Valmy, TS Power, ...) runs under a PERIOD FUEL-TAKE OBLIGATION —
contracted / captive mine-mouth tonnage that must be burned over an accounting
period — and that such an obligation, acting as an energy budget shaped into the
highest-price hours, would repair C4 coal hourly correlation.

Three parts:

1. **Admissible obligation estimate** (rule 13 [R-MEASURED]). For solve year Y,
   ONLY EIA-923 Schedule 5 rows of year Y-1 are read: contract tonnage
   (Purchase Type C / NC / T) whose ``Contract Expiration Date`` (MMYY) is still
   in force during Y, pro-rated by the months of Y it covers
   (expiry Dec Y-or-later = 12/12; expiry month m of Y = m/12). Tons ->
   MMBtu by the Y-1 lot heat content -> MWh by the model's own measured plant
   heat rate (``measured_coal_heat_rates``, the coefficient an LP row
   ``sum HR*P >= budget`` would carry). Undated contract lots are reported,
   never silently included. Mine-mouth captive supply is flagged mechanically by
   ``Primary Transportation Mode == "TC"`` (tramway/conveyor). Year Y's own
   receipts are computed ONLY as a comparison column labelled
   ``outcome_not_admissible``.
2. **Binding census.** Obligation vs keeper #10's exact per-plant model energy
   (``_nwppnext4_coal_census.json``), keeper #11's per-plant energy ESTIMATED by
   scaling #10's plants by the class-level #11/#10 ratio (keeper #11 has no
   per-plant hourly on disk), and CAMPD gross plant energy.
3. **Zero-LP C4 prediction.** On keeper #11's class hourly sidecars, emulate the
   shadow-priced budget: per coal class and period (month or year), add each
   plant's deficit (obligation - model, summed over plants, never netted
   against another plant's surplus) into the class's highest model-price hours,
   capped at class headroom (sum of the plants' mean available cap from the #10
   census minus dispatch). Variant ``eq`` additionally removes plant surplus
   from the lowest-price hours down to the class must-run band (a budget
   EQUALITY). The class price is the cap-weighted zonal price of its plants
   (zone by the plant's EIA-923 BA code). C4 coal r is recomputed against the
   same EIA-930 pool series the scorer uses (keeper r reproduced exactly).

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwppnext5_coal_contract_census.py \
        [--json results/calibration/_nwppnext5_coal_contract_census.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.coal import coal_subclass
from market_sim.data.fleet.campd_bins import measured_coal_heat_rates

YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
N = 8760
RECEIPTS = Path("data/raw/coal-receipts")
BUNDLE = Path("results/calibration/nwppnext4_span/hourly")
CENSUS = Path("results/calibration/_nwppnext4_coal_census.json")
CONTRACT_TYPES = ("C", "NC", "T")
# A: Y-1 contract tonnage still in force in Y, pro-rated by months covered.
# B: all Y-1 contract tonnage (assumes renewal at the same volume).
# A_net / B_net: the BURN floor the take implies once the yard may absorb the
# take into stock — take + Dec(Y-1) stock - max prior-years month-end stock
# (EIA-923 Page 2, years <= Y-1), floored at 0. Zero free parameters.
ESTIMATORS = {
    "A": "obligation_twh",
    "B": "prior_contract_twh",
    "A_net": "burn_floor_A_twh",
    "B_net": "burn_floor_B_twh",
}
STOCKS = Path("data/raw/coal-stocks")
_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _stocks(years: list[int], plants: set[int]) -> pd.DataFrame:
    """Month-end coal stock (tons) per plant for ``years`` (EIA-923 Page 2)."""
    out = []
    for y in years:
        f = STOCKS / f"coal_stocks_{y}.csv"
        if not f.exists():
            continue
        d = pd.read_csv(f, low_memory=False)
        d = d[d["Plant Id"].isin(plants)]
        q = d[[f"Quantity {m}" for m in _MONTHS]].apply(pd.to_numeric, errors="coerce")
        q.columns = range(1, 13)
        q["plant"] = d["Plant Id"].to_numpy()
        q = q.groupby("plant").sum(min_count=1)
        q["year"] = y
        out.append(q)
    return pd.concat(out) if out else pd.DataFrame()
# EIA-930 BA -> NWPP model zone (iso_configs NWPP docstring / zone_assignment).
BA_ZONE = {
    "PACE": "NWPP-EAST",
    "NWMT": "NWPP-INLAND",
    "IPCO": "NWPP-INLAND",
    "AVA": "NWPP-INLAND",
    "WAUW": "NWPP-INLAND",
    "NEVP": "NWPP-SNV",
    "BPAT": "NWPP-NW",
    "PGE": "NWPP-OR",
    "PACW": "NWPP-OR",
}


def _receipts(year: int, plants: set[int]) -> pd.DataFrame:
    """Return the year's coal receipt lots for ``plants`` (verbatim EIA-923 rows)."""
    f = RECEIPTS / f"coal_receipts_{year}.csv"
    if not f.exists():
        return pd.DataFrame()
    d = pd.read_csv(f, low_memory=False)
    d = d[d["Plant Id"].isin(plants)].copy()
    d["tons"] = pd.to_numeric(d["QUANTITY"], errors="coerce").fillna(0.0)
    d["hc"] = pd.to_numeric(d["Average Heat Content"], errors="coerce")
    d["mmbtu"] = d["tons"] * d["hc"].fillna(0.0)
    d["cost"] = pd.to_numeric(d["FUEL_COST"], errors="coerce")
    exp = d["Contract Expiration Date"].astype(str).str.strip()
    ok = exp.str.fullmatch(r"\d{3,4}")
    e4 = exp.where(ok).str.zfill(4)
    d["exp_month"] = pd.to_numeric(e4.str[:2], errors="coerce")
    d["exp_year"] = 2000 + pd.to_numeric(e4.str[2:], errors="coerce")
    return d


def _months_in_force(d: pd.DataFrame, y: int) -> pd.Series:
    """Months of year ``y`` each lot's contract covers (NaN = undated)."""
    m = np.where(
        d.exp_year > y, 12.0, np.where(d.exp_year == y, d.exp_month, 0.0)
    ).astype(float)
    return pd.Series(np.where(d.exp_year.isna(), np.nan, m), index=d.index)


def obligation(y: int, plants: set[int]) -> dict[int, dict]:
    """Per-plant admissible obligation for solve year ``y`` from Y-1 receipts."""
    prior = _receipts(y - 1, plants)
    same = _receipts(y, plants)
    hr = measured_coal_heat_rates("NWPP", y)
    st = _stocks(list(range(2018, y)), plants)
    out: dict[int, dict] = {}
    for pc in sorted(plants):
        p = prior[prior["Plant Id"] == pc] if not prior.empty else prior
        s = same[same["Plant Id"] == pc] if not same.empty else same
        if p.empty and s.empty:
            continue
        rec: dict = {}
        if not p.empty:
            tot = p.tons.sum()
            con = p[p["Purchase Type"].isin(CONTRACT_TYPES)]
            mif = _months_in_force(con, y)
            dated = con[mif.notna()]
            frac = (mif[mif.notna()] / 12.0).clip(0, 1)
            obl_tons = float((dated.tons * frac).sum())
            obl_mmbtu = float((dated.mmbtu * frac).sum())
            und = con[mif.isna()]
            h = hr.get(pc)
            exp_prof = (
                con.assign(ey=con.exp_year.fillna(-1).astype(int))
                .groupby("ey")
                .tons.sum()
                .div(max(con.tons.sum(), 1))
                .round(3)
            )
            hc = float(p.mmbtu.sum() / max(p.tons.sum(), 1))
            sp = st[st.index == pc] if not st.empty else st
            dec = (
                float(sp[sp.year == y - 1][12].sum())
                if not sp.empty and (sp.year == y - 1).any()
                else None
            )
            smax = float(np.nanmax(sp[list(range(1, 13))].to_numpy())) if not sp.empty else None
            for tag, tons in (("A", obl_tons), ("B", float(con.tons.sum()))):
                if dec is not None and smax is not None and h:
                    rec[f"burn_floor_{tag}_twh"] = round(
                        max(tons + dec - smax, 0.0) * hc / h / 1e6, 3
                    )
            rec.update(
                opening_stock_kt=round(dec / 1e3, 1) if dec is not None else None,
                max_prior_stock_kt=round(smax / 1e3, 1) if smax is not None else None,
                ba=str(p["Balancing Authority Code"].dropna().iloc[0])
                if p["Balancing Authority Code"].notna().any()
                else None,
                prior_total_kt=round(tot / 1e3, 1),
                prior_contract_share=round(con.tons.sum() / max(tot, 1), 3),
                prior_spot_share=round(
                    p[p["Purchase Type"] == "S"].tons.sum() / max(tot, 1), 3
                ),
                prior_minemouth_TC_share=round(
                    p[p["Primary Transportation Mode"] == "TC"].tons.sum()
                    / max(tot, 1),
                    3,
                ),
                contract_expiry_year_share={str(k): v for k, v in exp_prof.items()},
                undated_contract_kt=round(und.tons.sum() / 1e3, 1),
                obligation_kt=round(obl_tons / 1e3, 1),
                obligation_mmbtu=round(obl_mmbtu),
                prior_total_mmbtu=round(float(p.mmbtu.sum())),
                prior_cost_c_per_mmbtu=round(
                    float((p.cost * p.mmbtu).sum() / max(p.mmbtu.sum(), 1)), 1
                ),
                model_hr=h,
                obligation_twh=round(obl_mmbtu / h / 1e6, 3) if h else None,
                prior_contract_twh=round(float(con.mmbtu.sum()) / h / 1e6, 3)
                if h
                else None,
                prior_total_twh=round(float(p.mmbtu.sum()) / h / 1e6, 3)
                if h
                else None,
            )
        if not s.empty and hr.get(pc):
            rec["outcome_not_admissible_sameyear_receipts_twh"] = round(
                float(s.mmbtu.sum()) / hr[pc] / 1e6, 3
            )
            rec["outcome_not_admissible_sameyear_cost_c_per_mmbtu"] = round(
                float((s.cost * s.mmbtu).sum() / max(s.mmbtu.sum(), 1)), 1
            )
        if not rec.get("ba") and not s.empty and s["Balancing Authority Code"].notna().any():
            rec["ba"] = str(s["Balancing Authority Code"].dropna().iloc[0])
        out[pc] = rec
    return out


def _month_of_hour(y: int) -> np.ndarray:
    """Calendar month (1..12) of each of the model's 8760 hours."""
    return pd.date_range(f"{y}-01-01", periods=N, freq="h").month.to_numpy()


def _r(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r."""
    return float(np.corrcoef(a, b)[0, 1])


def _shape(
    mw: np.ndarray,
    floor: np.ndarray,
    cap: float,
    price: np.ndarray,
    groups: np.ndarray,
    add: dict,
    sub: dict,
) -> np.ndarray:
    """Add ``add[g]`` MWh into the highest-price hours of each period ``g``
    (up to ``cap``) and remove ``sub[g]`` MWh from the lowest-price hours
    (down to ``floor``) — the within-period shaping a budget dual produces."""
    x = mw.copy()
    for g in np.unique(groups):
        idx = np.nonzero(groups == g)[0]
        a = add.get(g, 0.0)
        if a > 0:
            for h in idx[np.argsort(-price[idx], kind="stable")]:
                room = max(cap - x[h], 0.0)
                d = min(room, a)
                x[h] += d
                a -= d
                if a <= 1e-6:
                    break
        s = sub.get(g, 0.0)
        if s > 0:
            for h in idx[np.argsort(price[idx], kind="stable")]:
                room = max(x[h] - floor[h], 0.0)
                d = min(room, s)
                x[h] -= d
                s -= d
                if s <= 1e-6:
                    break
    return x


def main() -> None:
    """Run the three-part census and dump JSON."""
    from scripts.data.build_calibration_reference import _pool_hourly_benchmark

    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    cen = json.loads(CENSUS.read_text())["census"]
    result: dict = {"per_year": {}}
    for y in YEARS:
        cy = {int(k): v for k, v in cen[str(y)].items()}
        cls = {}
        for pc in cy:
            try:
                cls[pc] = coal_subclass(pc)
            except Exception:  # noqa: BLE001 — unresolved rank: reported, not invented
                cls[pc] = None
        obl = obligation(y, set(cy))
        ch = pd.read_parquet(BUNDLE / f"class_hourly_{y}.parquet")
        cb = pd.read_parquet(BUNDLE / f"class_band_hourly_{y}.parquet")
        sysd = pd.read_parquet(BUNDLE / f"system_{y}.parquet")
        zp = {
            z: g.sort_values("hour").price.to_numpy(float)[:N]
            for z, g in sysd.groupby("zone")
        }
        coal_classes = sorted(
            c for c in ch.klass.astype(str).unique() if c.startswith("COAL")
        )
        cls_hourly = {
            c: ch[ch.klass.astype(str) == c]
            .groupby("hour")
            .mw.sum()
            .reindex(range(N), fill_value=0.0)
            .to_numpy(float)
            for c in coal_classes
        }
        cls_mustrun = {
            c: cb[(cb.klass.astype(str) == c) & (cb.band.astype(str) == "mustrun")]
            .groupby("hour")
            .mw.sum()
            .reindex(range(N), fill_value=0.0)
            .to_numpy(float)
            for c in coal_classes
        }
        k10 = {c: sum(v["model_twh"] for p, v in cy.items() if cls[p] == c) for c in coal_classes}
        k11 = {c: cls_hourly[c].sum() / 1e6 for c in coal_classes}
        ratio = {c: (k11[c] / k10[c]) if k10[c] > 0 else 1.0 for c in coal_classes}
        plants: dict = {}
        for pc, v in cy.items():
            o = obl.get(pc, {})
            m10 = v["model_twh"]
            m11 = m10 * ratio.get(cls[pc], 1.0)
            row = {
                "class": cls[pc],
                "cap_mean_mw": round(sum(b["cap_mean_mw"] for b in v["bands"].values()), 1),
                "model10_twh": m10,
                "model11_est_twh": round(m11, 3),
                "campd_gross_twh": v.get("campd_twh"),
                **o,
            }
            for tag, key in ESTIMATORS.items():
                ot = o.get(key)
                row[f"bind_{tag}_vs_k11_twh"] = (
                    round(max(ot - m11, 0.0), 3) if ot is not None else None
                )
                row[f"bind_{tag}_vs_k10_twh"] = (
                    round(max(ot - m10, 0.0), 3) if ot is not None else None
                )
            plants[pc] = row
        # --- emulation on keeper #11 class sidecars
        bench = _pool_hourly_benchmark("NWPP", y)
        act = np.asarray(bench["coal"], float)[:N]
        month = _month_of_hour(y)
        base = sum(cls_hourly.values())
        variants = {}
        for tag, key in ESTIMATORS.items():
            for period, mode in (
                ("month", "floor"),
                ("year", "floor"),
                ("month", "eq"),
                ("year", "eq"),
                ("year", "prop"),
            ):
                groups = month if period == "month" else np.zeros(N, int)
                tot = np.zeros(N)
                for c in coal_classes:
                    members = [p for p in plants if plants[p]["class"] == c]
                    cap = sum(plants[p]["cap_mean_mw"] for p in members)
                    w = {}
                    for p in members:
                        z = BA_ZONE.get(plants[p].get("ba") or "", "NWPP-EAST")
                        w[z] = w.get(z, 0.0) + plants[p]["cap_mean_mw"]
                    price = sum(zp[z] * wt for z, wt in w.items()) / max(
                        sum(w.values()), 1e-9
                    )
                    mw = cls_hourly[c]
                    add, sub = {}, {}
                    for g in np.unique(groups):
                        share = (groups == g).sum() / N
                        cls_share = mw[groups == g].sum() / max(mw.sum(), 1e-9)
                        for p in members:
                            q = plants[p]
                            if q.get(key) is None:
                                continue
                            # plant's model energy in period ~ class period share
                            m_p = q["model11_est_twh"] * 1e6 * cls_share
                            o_p = q[key] * 1e6 * share
                            if o_p > m_p:
                                add[g] = add.get(g, 0.0) + (o_p - m_p)
                            elif mode == "eq":
                                sub[g] = sub.get(g, 0.0) + (m_p - o_p)
                    if mode == "prop":
                        # shape-preserving bracket: deficit spread pro rata on
                        # the class's own dispatch shape, capped at headroom.
                        f = 1.0 + add.get(0, 0.0) / max(mw.sum(), 1e-9)
                        tot += np.minimum(mw * f, np.maximum(cap, mw))
                    else:
                        tot += _shape(mw, cls_mustrun[c], cap, price, groups, add, sub)
                variants[f"{tag}_{period}_{mode}"] = {
                    "r": round(_r(tot, act), 3),
                    "coal_twh": round(tot.sum() / 1e6, 3),
                    "added_twh": round(np.maximum(tot - base, 0).sum() / 1e6, 3),
                    "removed_twh": round(np.maximum(base - tot, 0).sum() / 1e6, 3),
                }
        wprice = sum(
            zp[z] * sysd[sysd.zone == z].demand.sum() for z in zp
        ) / sysd.demand.sum()
        result["per_year"][y] = {
            "keeper11_r": round(_r(base, act), 3),
            "keeper11_coal_twh": round(base.sum() / 1e6, 3),
            "eia930_coal_twh": round(float(act.sum()) / 1e6, 3),
            "r_actualcoal_vs_loadweighted_model_price": round(_r(wprice, act), 3),
            "r_actualcoal_vs_model_demand": round(
                _r(sysd.groupby("hour").demand.sum().to_numpy(float)[:N], act), 3
            ),
            "r_keeper11coal_vs_loadweighted_model_price": round(_r(wprice, base), 3),
            "class_k11_over_k10": {c: round(r, 3) for c, r in ratio.items()},
            **{
                f"{tag}_{what}": round(
                    sum((p.get(k) or 0) for p in plants.values()), 3
                )
                for tag, key in ESTIMATORS.items()
                for what, k in (
                    ("obligation_twh_total", key),
                    ("binding_twh_vs_k11_est", f"bind_{tag}_vs_k11_twh"),
                    ("binding_twh_vs_k10", f"bind_{tag}_vs_k10_twh"),
                )
            },
            **{
                f"{tag}_n_binding_plants_vs_k11_est": sum(
                    1 for p in plants.values() if (p.get(f"bind_{tag}_vs_k11_twh") or 0) > 0.05
                )
                for tag in ESTIMATORS
            },
            "outcome_not_admissible_sameyear_receipts_twh_total": round(
                sum(
                    (p.get("outcome_not_admissible_sameyear_receipts_twh") or 0)
                    for p in plants.values()
                ),
                3,
            ),
            "campd_gross_twh_total": round(
                sum(p["campd_gross_twh"] or 0 for p in plants.values()), 3
            ),
            "emulation": variants,
            "plants": {str(k): v for k, v in plants.items()},
        }
        r = result["per_year"][y]
        print(
            y,
            "k11 r",
            r["keeper11_r"],
            {k: v for k, v in r.items() if "binding_twh_vs_k11" in k or "obligation_twh_total" in k},
            {k: (v["r"], v["coal_twh"]) for k, v in variants.items()},
        )
    if a.json:
        a.json.write_text(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
