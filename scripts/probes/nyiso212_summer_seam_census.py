"""nyiso-212 POST-HOC (NOT pre-registered) — the summer-capability seam between
``cc_capacity_reconcile`` (mode ``cap``) and ``cc_nameplate_summer_derate``.

Zero-LP. The pre-registered decomposition
(``scripts/probes/nyiso212_overceiling_decomposition.py``) found the Cricket
Valley over-ceiling excess carried entirely by ``T_stat`` — the statistical
overlay riding on the outage windows — with a SUMMER level far below the
off-summer level. This probe characterises that leg:

1. **The 57185 statistical factor by month**, read off the keeper rebuild's own
   availability array divided by the loader's unit-outage factor (window-free),
   against the two published constants it should equal: ``1 - WEFOR`` off-summer
   and ``(1 - WEFOR) x net_summer / nameplate`` in Jun-Sep.
2. **The construction, plant by plant, for every NYISO CC_REGULAR plant**:
   ``fleet_to_bins`` rescales a CC plant to NAMEPLATE (``cap / ratio``,
   ``campd_bins.py`` ~L2295), ``_reconcile_cc_capacity`` then CAPS it to the
   CAMPD p99.9 demonstrated peak (~L2462, "applied after the nameplate
   rescale"), and the availability builder multiplies Jun-Sep by
   ``ratio = net_summer / nameplate`` (``arrays.py`` ~L834) — a ratio whose
   denominator is no longer the capacity it multiplies once a ``cap`` row has
   moved it. The constructed summer capability is therefore
   ``reconciled x net_summer / nameplate`` instead of the design's
   ``net_summer``; the two differ by ``ratio x (nameplate - reconciled)`` at
   every ``cap`` plant. Each plant's constructed summer capability is set
   beside its MEASURED CAMPD summer p99.9 / p99 gross (facility-level, Jun-Sep,
   2023-2025) so the over-derate is read against the plant's own record, never
   a residual.
3. **Post-hoc I2 in sum form**: the pre-registered window reconstruction
   UNIONED a unit's rows and failed its 1e-9 bar by exactly 1/3 on three
   boundary days; the loader SUMS rows. The sum-form reconstruction is reported
   here as a post-hoc instrument repair, not as a pass of I2 as declared.
4. **57185 summer hours above ceiling** under the constructed and the design
   summer capability, price-free.

Run (after the decomposition probe has populated ``.cache/nyiso212``)::

    uv run python scripts/probes/nyiso212_summer_seam_census.py
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))

import nyiso212_overceiling_decomposition as D  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet.campd_bins import cc_summer_capacity  # noqa: E402

RECON = ROOT / "data/raw/_processed-legacy/cc_capacity_reconcile_NYISO.csv"
SUMMER_MONTHS = (6, 7, 8, 9)
T = 8760


def summer_mask() -> np.ndarray:
    m = np.zeros(T, dtype=bool)
    for mo in SUMMER_MONTHS:
        m[D.MONTH_STARTS[mo - 1] : D.MONTH_STARTS[mo]] = True
    return m


def facility_gross(plant: int, year: int) -> np.ndarray:
    raw = pd.read_parquet(
        D.FAC_DIR / f"NY_{year}.parquet", columns=["facilityId", "date", "hour", "grossLoad"]
    )
    raw = raw[pd.to_numeric(raw.facilityId, errors="coerce") == plant]
    if raw.empty:
        return np.zeros(T)
    ts = raw["date"] + pd.to_timedelta(raw["hour"], unit="h")
    hoy = D.hour_index_8760(ts, year)
    arr = np.zeros(T)
    g = np.nan_to_num(raw.grossLoad.to_numpy(dtype=float), nan=0.0)
    ok = hoy >= 0
    np.add.at(arr, hoy[ok], g[ok])
    return arr


def main() -> None:
    sm = summer_mask()
    out: dict = {
        "session": "nyiso-212",
        "status": "POST-HOC characterisation — decides no pre-registered verdict, arms nothing, moves no default",
        "keeper": D.KEEPER_ID,
        "seam": "fleet_to_bins nameplate rescale (cap/ratio) -> _reconcile_cc_capacity cap to CAMPD p99.9 -> availability x ratio in Jun-Sep; ratio = net_summer/nameplate no longer matches the capacity it multiplies",
    }
    # ---- 1. the 57185 statistical factor by month, from the rebuild itself
    stat_by_year = {}
    for year in D.YEARS:
        st = pickle.load(open(D.CACHE / f"keeper_{year}.pkl", "rb"))
        avail = st["plant_avail"][0]  # tranche-flat per I2's spread check (0.0)
        ufac = D.loader_ufac(year)
        with np.errstate(divide="ignore", invalid="ignore"):
            stat = np.where(ufac > 0, avail / ufac, np.nan)
        stat_by_year[str(year)] = [
            round(float(np.nanmean(stat[D.MONTH_STARTS[m] : D.MONTH_STARTS[m + 1]])), 6)
            for m in range(12)
        ]
    caps = cc_summer_capacity()
    npl, ns = caps[D.PLANT]
    ratio = min(1.0, ns / npl)
    off = float(np.nanmean([v for y in stat_by_year.values() for v in y[:5] + y[9:]]))
    summ = float(np.nanmean([v for y in stat_by_year.values() for v in y[5:9]]))
    out["cricket_valley_statistical_factor"] = {
        "by_month": stat_by_year,
        "off_summer_mean": round(off, 6),
        "summer_mean": round(summ, 6),
        "summer_over_off_summer": round(summ / off, 6),
        "eia860_nameplate_mw": round(npl, 1),
        "eia860_net_summer_mw": round(ns, 1),
        "ratio_net_summer_over_nameplate": round(ratio, 6),
        "identity_summer_eq_off_x_ratio_abs_diff": round(abs(summ - off * ratio), 6),
    }
    # ---- 2. plant-by-plant construction census, NYISO CC_REGULAR
    st = pickle.load(open(D.CACHE / "keeper_2024.pkl", "rb"))
    units = st["units"]
    cc = units[units.group == "CC_REGULAR"].groupby("plant").pmax.sum()
    groups_at = units.groupby("plant").group.agg(lambda g: sorted(set(g)))
    recon = pd.read_csv(RECON).set_index("plant_code")
    # The bench's own basis per plant: facility gross x the pooled parasitic
    # factor (1.0 where the plant has no row, e.g. 57185) — the SAME net the
    # reconcile deriver took its p99.9 from, so pmax and meter are comparable.
    pfac = campd.pooled_factor_map(
        pd.read_parquet(ROOT / "data/raw/_processed-legacy/parasitic_load_factors.parquet")
    )
    rows = []
    for plant, pmax_lp in cc.items():
        plant = int(plant)
        multi_bin = len(groups_at.get(plant, [])) > 1
        pf = float(pfac.get(plant, 1.0))
        cap = caps.get(plant)
        if cap is None:
            r = None
            npl_p = ns_p = None
        else:
            npl_p, ns_p = cap
            r = min(1.0, ns_p / npl_p) if npl_p > 0 else None
        mode = str(recon.loc[plant, "mode"]) if plant in recon.index else "none"
        reconciled = float(recon.loc[plant, "reconciled_mw"]) if plant in recon.index else None
        constructed_summer = pmax_lp * r if r is not None else pmax_lp
        design_summer = min(ns_p, pmax_lp) if ns_p is not None else pmax_lp
        g = np.concatenate([facility_gross(plant, y) for y in D.YEARS]) * pf
        s = np.concatenate([sm, sm, sm])
        gs, go = g[s], g[~s]
        rows.append(
            {
                "plant": plant,
                "name": str(recon.loc[plant, "plant_name"]) if plant in recon.index else "",
                "pmax_lp_mw": round(float(pmax_lp), 1),
                "eia860_nameplate_mw": None if npl_p is None else round(npl_p, 1),
                "eia860_net_summer_mw": None if ns_p is None else round(ns_p, 1),
                "ratio": None if r is None else round(r, 4),
                "reconcile_mode": mode,
                "multi_bin_facility (facility meter NOT comparable)": bool(multi_bin),
                "bench_parasitic_factor": round(pf, 4),
                "reconciled_mw": reconciled,
                "constructed_summer_mw": round(float(constructed_summer), 1),
                "design_summer_mw": round(float(design_summer), 1),
                "summer_mw_lost_to_seam": round(float(design_summer - constructed_summer), 1),
                "campd_summer_p999_bench_net_mw": round(float(np.percentile(gs, 99.9)), 1) if gs.any() else None,
                "campd_summer_p99_bench_net_mw": round(float(np.percentile(gs, 99.0)), 1) if gs.any() else None,
                "campd_offsummer_p999_bench_net_mw": round(float(np.percentile(go, 99.9)), 1) if go.any() else None,
                "summer_hours_gross_above_constructed": int((gs > constructed_summer).sum()),
                "summer_hours_gross_above_design": int((gs > design_summer).sum()),
                "summer_gwh_above_constructed": round(float(np.clip(gs - constructed_summer, 0, None).sum()) / 1e3, 2),
            }
        )
    df = pd.DataFrame(rows).sort_values("summer_mw_lost_to_seam", ascending=False)
    out["cc_regular_census_2023_2025"] = df.to_dict(orient="records")
    out["census_totals"] = {
        "plants": int(len(df)),
        "cap_plants": int((df.reconcile_mode == "cap").sum()),
        "raise_plants": int((df.reconcile_mode == "raise").sum()),
        "summer_mw_lost_to_seam_total": round(float(df.summer_mw_lost_to_seam.clip(lower=0).sum()), 1),
        "single_bin_plants_with_summer_meter_above_constructed": int(((df.summer_hours_gross_above_constructed > 0) & ~df["multi_bin_facility (facility meter NOT comparable)"]).sum()),
        "single_bin_plants_with_summer_meter_above_design": int(((df.summer_hours_gross_above_design > 0) & ~df["multi_bin_facility (facility meter NOT comparable)"]).sum()),
        "multi_bin_facilities_excluded_from_meter_comparison": [int(p) for p in df[df["multi_bin_facility (facility meter NOT comparable)"]].plant],
    }
    # ---- 3. post-hoc I2 in SUM form
    win = D.extract_windows()
    worst = 0.0
    for year in D.YEARS:
        uf = D.loader_ufac(year)
        clock = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
        idx = D.hour_index_8760(pd.Series(clock), year)
        removed = np.zeros(T)
        for r in win.itertuples(index=False):
            m = (clock >= r.start) & (clock < r.end_excl) & (idx >= 0)
            removed[idx[m]] += 1.0 / 3.0
        recon_sum = 1.0 - np.clip(removed, 0.0, 1.0)
        worst = max(worst, float(np.abs(recon_sum - uf).max()))
    out["post_hoc_I2_sum_form"] = {
        "worst_abs_diff_recon_sum_vs_loader": worst,
        "note": "POST-HOC instrument repair: union -> sum. The declared I2 (union form) FAILED at 0.3333 on 2023-11-22, 2024-02-04, 2025-02-21 — the boundary-day row double-count unit_outage_per_unit_clip names; none of the three days is in a scored month.",
    }
    # ---- 4. 57185 summer over-ceiling hours, constructed vs design
    per_year = {}
    for year in D.YEARS:
        g = facility_gross(D.PLANT, year)
        stt = pickle.load(open(D.CACHE / f"keeper_{year}.pkl", "rb"))
        ceiling_lp = (stt["plant_avail"] * stt["plant_units"].pmax.to_numpy()[:, None]).sum(axis=0)
        # Design counterfactual: same windows and WEFOR, summer multiplier
        # min(1, net_summer / pmax_lp) instead of net_summer / nameplate.
        uf = D.loader_ufac(year)
        with np.errstate(divide="ignore", invalid="ignore"):
            stat = np.where(uf > 0, stt["plant_avail"][0] / uf, np.nan)
        offw = float(np.nanmean(stat[~sm]))
        pmax_lp = float(stt["plant_units"].pmax.sum())
        design_mult = np.where(sm, min(1.0, ns / pmax_lp), 1.0)
        ceiling_design = pmax_lp * uf * offw * design_mult
        per_year[str(year)] = {
            "summer_hours_gross_above_lp_ceiling": int((g[sm] > ceiling_lp[sm] + 1e-6).sum()),
            "summer_gwh_above_lp_ceiling": round(float(np.clip(g[sm] - ceiling_lp[sm], 0, None).sum()) / 1e3, 2),
            "summer_hours_gross_above_design_ceiling": int((g[sm] > ceiling_design[sm] + 1e-6).sum()),
            "summer_gwh_above_design_ceiling": round(float(np.clip(g[sm] - ceiling_design[sm], 0, None).sum()) / 1e3, 2),
            "offsummer_hours_gross_above_lp_ceiling": int((g[~sm] > ceiling_lp[~sm] + 1e-6).sum()),
            "months_meter_over_design_ceiling": [
                m + 1
                for m in range(12)
                if g[D.MONTH_STARTS[m] : D.MONTH_STARTS[m + 1]].sum()
                > ceiling_design[D.MONTH_STARTS[m] : D.MONTH_STARTS[m + 1]].sum()
            ],
            "design_summer_multiplier": round(min(1.0, ns / pmax_lp), 6),
        }
    out["cricket_valley_ceiling_counterfactual"] = per_year
    dest = ROOT / "results/calibration/_nyiso212_summer_seam_census.json"
    dest.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out["cricket_valley_statistical_factor"], indent=1))
    print(json.dumps(out["census_totals"], indent=1))
    print(json.dumps(out["post_hoc_I2_sum_form"], indent=1))
    print(json.dumps(out["cricket_valley_ceiling_counterfactual"], indent=1))
    cols = ["plant", "name", "pmax_lp_mw", "eia860_nameplate_mw", "eia860_net_summer_mw", "ratio",
            "reconcile_mode", "constructed_summer_mw", "design_summer_mw", "summer_mw_lost_to_seam",
            "campd_summer_p999_bench_net_mw", "campd_summer_p99_bench_net_mw", "summer_hours_gross_above_constructed",
            "summer_hours_gross_above_design", "summer_gwh_above_constructed"]
    print(df[cols].to_string(index=False))


if __name__ == "__main__":
    main()
