"""nyiso-214 PHASE 0 (NO LP) — is the EIA-860 ``nameplate - net_summer`` gap read
TWICE inside ``CC_REGULAR``?

Measures the four predictions pre-registered in
``results/calibration/PREREG-nyiso214-duct-gap-double-reading.md`` (pushed before
any number below was read), on the keeper's own committed recipe and its own
active EIA-860 vintage:

* **P1** — how many NYISO ``CC_REGULAR`` plants BOTH receive a nonzero
  ``cc_duct_peaking_pct`` peak band AND take a Jun-Sep
  ``cc_nameplate_summer_derate`` multiplier ``< 1``, and how much peak-band MW
  those plants carry.
* **P2** — the EIA-860 capability gap ``100 x (SUM np - SUM ns) / SUM np`` at the
  two material plants that receive a **zero** peak band (55405 Athens, 56196
  Zeltmann): is their zero band a property of the flag or of the physics?
* **P3** — the share of 57185's total gap carried by the ``Duct Burners == Y``
  rows alone (a REPRODUCTION of nyiso-198's census; ``> 50 %`` VOIDS the run).
* **P4** — that both mechanisms provably read one EIA-860 pair at 57185:
  ``peak_MW / carried == pct/100`` and the summer multiplier
  ``== min(1, net_summer / carried)``.

It then SIZES the candidate membership forms for the owner decision card (pure
arithmetic on the census above plus the plants' own CAMPD demonstrated peak — no
new identification, no residual consulted, no form selected here) and measures
each plant's own measured REACH above its published net-summer rating.

Writes ``results/calibration/_nyiso214_duct_gap_census.json``.

Usage::

    python scripts/probes/nyiso214_duct_gap_census.py [--year 2025]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.lib.bundle_fleet import (  # noqa: E402
    bundle_gas_price,
    clear_fleet_caches,
    ensure_probe_path,
    full_run_year_kwargs,
)

BUNDLE = ROOT / "results/calibration/nyiso213_summer_seam"
OUT = ROOT / "results/calibration/_nyiso214_duct_gap_census.json"
CV = 57185
#: The two material (>= 350 MW) CC_REGULAR plants the keeper gives a ZERO peak
#: band — P2's subjects, named in the PREREG before their gaps were read.
ZERO_BAND_MATERIAL = (55405, 56196)
#: Jun-Sep, the window cc_nameplate_summer_derate applies.
SUMMER_HOURS = slice(
    int(np.cumsum([0, 31, 28, 31, 30, 31])[-1]) * 24,
    int(np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31])[-1]) * 24,
)


def _eia860_cc_rows() -> pd.DataFrame:
    """Return the keeper vintage's operable combined-cycle generator rows."""
    from market_sim.data.fleet.campd_bins import active_eia860_dir

    path = active_eia860_dir() / "eia860_generator_operable.parquet"
    df = pd.read_parquet(
        path,
        columns=[
            "Plant Code",
            "Technology",
            "Prime Mover",
            "Duct Burners",
            "Nameplate Capacity (MW)",
            "Summer Capacity (MW)",
        ],
    )
    df = df[pd.to_numeric(df["Plant Code"], errors="coerce").notna()]
    cc = df[df["Technology"] == "Natural Gas Fired Combined Cycle"].copy()
    cc["plant_code"] = cc["Plant Code"].astype(float).astype(int)
    cc["np_mw"] = pd.to_numeric(cc["Nameplate Capacity (MW)"], errors="coerce")
    cc["ns_mw"] = pd.to_numeric(cc["Summer Capacity (MW)"], errors="coerce")
    cc["duct"] = cc["Duct Burners"].astype(str).str.strip()
    return cc[["plant_code", "Prime Mover", "duct", "np_mw", "ns_mw"]]


def _gap_pct(rows: pd.DataFrame) -> float:
    """Return ``100 x (SUM nameplate - SUM net_summer) / SUM nameplate``."""
    np_sum = float(rows["np_mw"].sum())
    if np_sum <= 0.0:
        return float("nan")
    return 100.0 * max(0.0, np_sum - float(rows["ns_mw"].sum())) / np_sum


def main() -> None:
    """Measure P1-P4 and write the machine record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2025)
    args = ap.parse_args()
    year = args.year

    ensure_probe_path()
    import scripts.run_calibration as rc
    from market_sim.data.fleet.campd_bins import cc_duct_peaking_pct

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = full_run_year_kwargs(meta)
    clear_fleet_caches()
    built = rc.run_year(year, "NYISO", 8760, bundle_gas_price(meta, year), **kwargs)
    fa = built["fleet_arrays"]

    fleet = pd.DataFrame(
        {
            "uid": fa.unit_ids,
            "plant": fa.plant_code,
            "pmax": fa.pmax,
            "group": fa.plant_group,
        }
    )
    cc = fleet[fleet["group"] == "CC_REGULAR"]
    carried = cc.groupby("plant")["pmax"].sum()
    peak_mw = (
        cc[cc["uid"].str.endswith("_peak")].groupby("plant")["pmax"].sum().reindex(
            carried.index
        ).fillna(0.0)
    )

    # The Jun-Sep availability multiplier the keeper's own fleet carries, per
    # plant: summer mean availability / off-summer mean availability on the
    # plant's committed tranche (the tranche the derate multiplies).
    avail = fa.availability
    idx = {u: i for i, u in enumerate(fa.unit_ids)}
    summer_ratio: dict[int, float] = {}
    for plant in carried.index:
        rows = cc[(cc["plant"] == plant) & cc["uid"].str.endswith("_committed")]
        if rows.empty:
            rows = cc[cc["plant"] == plant]
        i = idx[rows["uid"].iloc[0]]
        a = avail[i]
        off = np.concatenate([a[: SUMMER_HOURS.start], a[SUMMER_HOURS.stop :]])
        summer_ratio[int(plant)] = (
            float(a[SUMMER_HOURS].max() / off.max()) if off.max() > 0 else float("nan")
        )

    pct_plant = cc_duct_peaking_pct(row_scoped=False)
    pct_rows = cc_duct_peaking_pct(row_scoped=True)
    e860 = _eia860_cc_rows()

    # ---- the per-plant census -------------------------------------------
    census = []
    for plant in carried.index:
        p = int(plant)
        rows = e860[e860["plant_code"] == p]
        y_rows = rows[rows["duct"] == "Y"]
        census.append(
            {
                "plant": p,
                "carried_mw": round(float(carried[plant]), 3),
                "peak_mw": round(float(peak_mw[plant]), 3),
                "peak_pct_of_carried": round(100.0 * float(peak_mw[plant] / carried[plant]), 3),
                "duct_pct_plant_form": pct_plant.get(p),
                "duct_pct_row_form": pct_rows.get(p),
                "has_Y_row": bool(len(y_rows) > 0),
                "e860_np_mw": round(float(rows["np_mw"].sum()), 3) if len(rows) else None,
                "e860_ns_mw": round(float(rows["ns_mw"].sum()), 3) if len(rows) else None,
                "e860_gap_pct": round(_gap_pct(rows), 3) if len(rows) else None,
                "summer_multiplier": round(summer_ratio[p], 4),
                "summer_derated": bool(summer_ratio[p] < 0.999),
            }
        )
    census.sort(key=lambda r: -r["carried_mw"])

    # ---- P1 --------------------------------------------------------------
    both = [r for r in census if r["peak_mw"] > 0.0 and r["summer_derated"]]
    p1 = {
        "declared": "n_plants >= 6 AND peak_mw_at_those >= 400",
        "n_plants": len(both),
        "peak_mw_total": round(sum(r["peak_mw"] for r in both), 3),
        "plants": [r["plant"] for r in both],
        "fires": len(both) >= 6 and sum(r["peak_mw"] for r in both) >= 400.0,
    }

    # ---- P2 --------------------------------------------------------------
    p2_rows = {}
    for p in ZERO_BAND_MATERIAL:
        rows = e860[e860["plant_code"] == p]
        rec = next((r for r in census if r["plant"] == p), None)
        p2_rows[str(p)] = {
            "e860_np_mw": round(float(rows["np_mw"].sum()), 3),
            "e860_ns_mw": round(float(rows["ns_mw"].sum()), 3),
            "e860_gap_pct": round(_gap_pct(rows), 3),
            "duct_flags": sorted(rows["duct"].unique().tolist()),
            "peak_mw": rec["peak_mw"] if rec else None,
            "summer_multiplier": rec["summer_multiplier"] if rec else None,
        }
    gaps = [v["e860_gap_pct"] for v in p2_rows.values()]
    if all(g >= 8.0 for g in gaps):
        p2_outcome = "FIRES — flag artifact (both >= 8.0 %)"
    elif any(g < 4.0 for g in gaps):
        p2_outcome = "REFUTED — the rule tracks the physics (one plant < 4.0 %)"
    else:
        p2_outcome = "INDETERMINATE — third outcome, a gap in [4.0, 8.0)"
    p2 = {
        "declared": ">= 8.0 % at EACH of 55405 and 56196; < 4.0 % REFUTES; [4,8) INDETERMINATE",
        "plants": p2_rows,
        "outcome": p2_outcome,
    }

    # ---- P3 --------------------------------------------------------------
    cv = e860[e860["plant_code"] == CV]
    cv_y = cv[cv["duct"] == "Y"]
    gap_all = float(cv["np_mw"].sum() - cv["ns_mw"].sum())
    gap_y = float(cv_y["np_mw"].sum() - cv_y["ns_mw"].sum())
    y_share = 100.0 * gap_y / gap_all if gap_all > 0 else float("nan")
    p3 = {
        "declared": "< 40 % (nyiso-198 reproduction); > 50 % VOIDS the census",
        "gap_all_mw": round(gap_all, 3),
        "gap_on_Y_rows_mw": round(gap_y, 3),
        "gap_on_non_Y_rows_mw": round(gap_all - gap_y, 3),
        "Y_row_share_pct": round(y_share, 3),
        "rows": [
            {
                "prime_mover": r["Prime Mover"],
                "duct": r["duct"],
                "np_mw": float(r["np_mw"]),
                "ns_mw": float(r["ns_mw"]),
            }
            for _, r in cv.iterrows()
        ],
        "fires": y_share < 40.0,
        "VOID": y_share > 50.0,
    }

    # ---- P4 --------------------------------------------------------------
    cv_rec = next(r for r in census if r["plant"] == CV)
    from market_sim.data.fleet.campd_bins import cc_summer_capacity

    ns_pair = cc_summer_capacity().get(CV)
    implied = (
        min(1.0, float(ns_pair[1]) / cv_rec["carried_mw"]) if ns_pair else float("nan")
    )
    d_i = abs(cv_rec["peak_pct_of_carried"] - float(cv_rec["duct_pct_plant_form"]))
    d_ii = abs(cv_rec["summer_multiplier"] - implied)
    p4 = {
        "declared": "|peak_pct_of_carried - duct_pct| <= 0.2 pp AND "
        "|summer_mult - min(1, net_summer/carried)| <= 0.001",
        "peak_pct_of_carried": cv_rec["peak_pct_of_carried"],
        "duct_pct_plant_form": cv_rec["duct_pct_plant_form"],
        "delta_i_pp": round(d_i, 4),
        "cc_summer_capacity_net_summer_mw": float(ns_pair[1]) if ns_pair else None,
        "carried_mw": cv_rec["carried_mw"],
        "implied_summer_multiplier": round(implied, 4),
        "measured_summer_multiplier": cv_rec["summer_multiplier"],
        "delta_ii": round(d_ii, 5),
        "fires": d_i <= 0.2 and d_ii <= 0.001,
    }

    # ---- candidate membership forms + measured reach (decision card) -----
    demonstrated: dict[int, dict] = {}
    for yr in (2023, 2024, 2025):
        raw = pd.read_parquet(
            ROOT / f"data/raw/campd-unit-level/NY_{yr}.parquet",
            columns=["facilityId", "unitId", "date", "hour", "grossLoad"],
        )
        raw["facilityId"] = pd.to_numeric(raw["facilityId"], errors="coerce")
        plant_h = (
            raw.groupby(["facilityId", "date", "hour"])["grossLoad"].sum().reset_index()
        )
        for p_code, grp in plant_h.groupby("facilityId"):
            if pd.isna(p_code):
                continue
            key = int(p_code)
            load = grp["grossLoad"].to_numpy(dtype=float)
            load = load[~np.isnan(load)]
            if load.size == 0:
                continue
            demonstrated.setdefault(key, {})[yr] = {
                "p999_mw": float(np.quantile(load, 0.999)),
                "hours_reported": int(load.size),
            }

    forms = []
    for r in census:
        p_code = r["plant"]
        car, ns = r["carried_mw"], r["e860_ns_mw"]
        if ns is None:
            continue
        peaks = [v["p999_mw"] for v in demonstrated.get(p_code, {}).values()]
        demo = max(peaks) if peaks else None
        reach = {}
        for yr in (2023, 2024, 2025):
            raw = None
            d_yr = demonstrated.get(p_code, {}).get(yr)
            reach[str(yr)] = d_yr["hours_reported"] if d_yr else 0
        forms.append(
            {
                "plant": p_code,
                "carried_mw": car,
                "e860_ns_mw": ns,
                "single_peak_tranche": r["peak_pct_of_carried"] > 99.9,
                "A_status_quo_mw": round(car * (r["duct_pct_plant_form"] or 0.0) / 100.0, 2),
                "B_row_scoped_mw": round(car * (r["duct_pct_row_form"] or 0.0) / 100.0, 2),
                "C_symmetric_none_mw": 0.0,
                "D_symmetric_all_mw": round(car * (r["e860_gap_pct"] or 0.0) / 100.0, 2),
                "E_carried_minus_ns_mw": round(max(0.0, car - ns), 2),
                "E_prime_demonstrated_minus_ns_mw": (
                    round(max(0.0, demo - ns), 2) if demo is not None else None
                ),
                "campd_demonstrated_peak_mw": round(demo, 2) if demo is not None else None,
                "carried_is_nameplate": bool(
                    r["e860_np_mw"] is not None and abs(car - r["e860_np_mw"]) < 0.05
                ),
            }
        )

    # measured reach: share of the plant's own reporting hours above net_summer
    reach_rows = []
    for yr in (2023, 2024, 2025):
        raw = pd.read_parquet(
            ROOT / f"data/raw/campd-unit-level/NY_{yr}.parquet",
            columns=["facilityId", "unitId", "date", "hour", "grossLoad"],
        )
        raw["facilityId"] = pd.to_numeric(raw["facilityId"], errors="coerce")
        plant_h = (
            raw.groupby(["facilityId", "date", "hour"])["grossLoad"].sum().reset_index()
        )
        for r in census:
            p_code = r["plant"]
            ns = r["e860_ns_mw"]
            if ns is None:
                continue
            g = plant_h[plant_h["facilityId"] == p_code]["grossLoad"].to_numpy(float)
            g = g[~np.isnan(g)]
            on = g[g > 0.01]
            if on.size == 0:
                continue
            reach_rows.append(
                {
                    "plant": p_code,
                    "year": yr,
                    "online_h": int(on.size),
                    "h_above_net_summer": int((on > ns).sum()),
                    "pct_online_h_above_ns": round(100.0 * float((on > ns).mean()), 2),
                    "max_mw": round(float(on.max()), 1),
                    "net_summer_mw": ns,
                }
            )

    # ---- boundary test + the allocator-vs-reach relationship -------------
    # A plant's CAMPD facility is comparable to the model plant only when its
    # demonstrated peak does not overrun the carried capacity by more than the
    # reconcile's own tolerance; where it does, the facility spans more than the
    # model plant (nyiso-194 named 2500; nyiso-186 named the 55375/57664 merged
    # identity) and every measured-side statistic at that plant is contaminated.
    BOUNDARY_TOL = 1.15
    clean, contaminated = [], []
    for r in forms:
        demo = r["campd_demonstrated_peak_mw"]
        if demo is None:
            contaminated.append({"plant": r["plant"], "why": "no CAMPD facility"})
        elif demo > BOUNDARY_TOL * r["carried_mw"]:
            contaminated.append(
                {
                    "plant": r["plant"],
                    "why": "CAMPD facility spans more than the model plant",
                    "demo_over_carried": round(demo / r["carried_mw"], 3),
                }
            )
        else:
            clean.append(r["plant"])

    material_clean = [
        r["plant"]
        for r in forms
        if r["plant"] in clean
        and not r["single_peak_tranche"]
        and r["carried_mw"] >= 350.0
    ]
    pairs = []
    for p_code in material_clean:
        rec = next(x for x in census if x["plant"] == p_code)
        yrs = [x for x in reach_rows if x["plant"] == p_code]
        if not yrs:
            continue
        pairs.append(
            {
                "plant": p_code,
                "peak_pct_of_carried": rec["peak_pct_of_carried"],
                "mean_reach_pct": round(
                    float(np.mean([y["pct_online_h_above_ns"] for y in yrs])), 3
                ),
                "reach_by_year": {str(y["year"]): y["pct_online_h_above_ns"] for y in yrs},
            }
        )
    if len(pairs) >= 3:
        xr = pd.Series([q["peak_pct_of_carried"] for q in pairs]).rank()
        yr_ = pd.Series([q["mean_reach_pct"] for q in pairs]).rank()
        rho = float(xr.corr(yr_, method="pearson"))
    else:
        rho = float("nan")
    allocator = {
        "question": "does the peak band's SIZE track the plants' own demonstrated "
        "reach above the published net-summer rating it is derived from?",
        "boundary_clean_material_plants": material_clean,
        "pairs": pairs,
        "spearman_rho": round(rho, 4),
        "reading": "no relationship" if abs(rho) < 0.3 else "related",
    }

    record = {
        "session": "nyiso-214",
        "year": year,
        "keeper": "2026-09-07-nyiso-213-summer-seam",
        "bundle_control": str(BUNDLE.relative_to(ROOT)),
        "prereg": "results/calibration/PREREG-nyiso214-duct-gap-double-reading.md",
        "P1": p1,
        "P2": p2,
        "P3": p3,
        "P4": p4,
        "census": census,
        "candidate_forms": forms,
        "measured_reach_above_net_summer": reach_rows,
        "boundary_clean_plants": clean,
        "boundary_contaminated_plants": contaminated,
        "allocator_vs_reach": allocator,
        "instrument_caveats": [
            "peak_pct_of_carried is meaningful only at multi-tranche plants; the "
            "seven small plants flagged single_peak_tranche are represented by ONE "
            "tranche labelled _peak, so the column reads 100.0 by construction.",
            "carried_mw equals the CAMPD demonstrated peak only where a "
            "cc_capacity_reconcile row exists; elsewhere carried_mw IS nameplate, "
            "so form E degenerates to form D at those plants (carried_is_nameplate).",
            "Form E' (CAMPD demonstrated peak - net_summer) is REFUTED as "
            "constructed: at the boundary-contaminated plants the CAMPD facility "
            "spans more than the model plant, so E' reads 694.0 MW at 55375 and "
            "1,669.5 MW at 2500. It is reported, not proposed.",
            "No form is selected here. The sizing is arithmetic on the census and "
            "the plants' own meters; no residual was consulted (rule 1 [R-STRUCT]).",
        ],
    }
    OUT.write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({k: record[k] for k in ("P1", "P2", "P3", "P4")}, indent=1))
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
