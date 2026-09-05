"""nyiso-192 PHASE 0 (NO LP) — Sithe Independence 54547: the census rule, and the over-run decomposed.

nyiso-191 §6 item 1 handed forward "the largest single per-plant over-run in the
NYISO fleet" (+3.19 / +3.48 TWh, model CF 0.93 / 0.97 vs 0.62) with the
instruction to measure the ``chp_layup_duty_curve`` cohort-admission rule
against it before proposing anything. Four measurements, all on committed
bytes and the no-LP fleet reconstruction:

1. **The census rule**, read from the frozen population table: is Sithe a
   lay-up the rule missed, or an operating plant the rule correctly declines?
2. **The over-run, published vs corrected** — the published payload carries the
   35 % sector add-back (``nyiso192_payload_addback_audit``); the LP series is
   the payload minus that flat offset. Hours-on vs level-when-on split.
3. **Offer position** — Sithe's reconstructed tranche offers against the
   model's Upstate_West price and against the ACTUAL Zone-C RT LBMP: in-merit
   shares, and how much of the corrected gap sits in hours where the model was
   in merit but the market price was below the plant's own SRMC (the upstate
   trough / price-compression object, nyiso-109 / -167 / -168).
4. **Conduct signature** — from CAMPD unit-level: units-on distribution and
   the loading when all four trains are on.

Rule 13 [R-MEASURED]: diagnosis only. No lever is built or proposed here.
"""

from __future__ import annotations

import csv

import numpy as np
import pandas as pd

from _nyiso192_common import (
    KEEPER_ID,
    REPO,
    T,
    YEARS,
    actual_zone_price,
    bench_plants,
    keeper_payload,
    model_zone_price,
    plant_series,
    reconstructed,
    write_json,
)
from market_sim.data.chp import chp_btm_pct

PLANT = 54547
KEY = "54547"
ON_MW = 1.0  # "on" = gross > 1 MW, the dashboard's own convention
PART_LOAD_FRAC = 0.85  # descriptive only, not a bar


def census_row() -> dict:
    """Sithe's row in the frozen lay-up census population table (rule 23)."""
    path = REPO / "data/raw/_processed-legacy/chp_layup_census_NYISO_population.csv"
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if int(r["plant_code"]) == PLANT:
                return {
                    k: r[k]
                    for k in (
                        "plant_code",
                        "plant_name",
                        "cells",
                        "cells_zero",
                        "pooled_median_mw",
                        "observed_hsl_mw",
                        "online_share",
                        "laid_up",
                        "verdict",
                    )
                }
    raise SystemExit("Sithe row missing from the census population table")


def campd_units(year: int) -> dict:
    """Units-on distribution and 4-on loading from CAMPD unit-level NY."""
    df = pd.read_parquet(
        REPO / f"data/raw/campd-unit-level/NY_{year}.parquet",
        columns=["facilityId", "unitId", "date", "hour", "grossLoad", "heatInput"],
    )
    s = df[pd.to_numeric(df["facilityId"], errors="coerce") == PLANT]
    g = s.groupby(["date", "hour"]).agg(
        load=("grossLoad", "sum"),
        heat=("heatInput", "sum"),
        n_on=("grossLoad", lambda x: int((x > 0).sum())),
    )
    on = g[g.load > 0]
    hsl = float(np.percentile(g.load, 99.5))
    four = on[on.n_on == 4]
    return {
        "hours": int(len(g)),
        "on_hours": int(len(on)),
        "heat_rate_pooled": round(float(on.heat.sum() / on.load.sum()), 3),
        "hsl_p995_mw": round(hsl, 1),
        "units_on_share_of_on_hours": {
            int(k): round(float(v), 3)
            for k, v in on.n_on.value_counts(normalize=True).sort_index().items()
        },
        "mean_load_by_units_on_mw": {
            int(k): round(float(v), 0)
            for k, v in on.groupby("n_on").load.mean().items()
        },
        "four_on_hours": int(len(four)),
        "four_on_share_below_85pct_hsl": round(
            float((four.load < PART_LOAD_FRAC * hsl).mean()), 3
        )
        if len(four)
        else None,
    }


def main() -> int:
    run = keeper_payload()
    rec = {
        "session": "nyiso-192",
        "object": "1 — Sithe Independence 54547 duty object (phase 0, no LP, no lever)",
        "run": KEEPER_ID,
        "census_rule": census_row(),
        "by_year": {},
    }
    sector = chp_btm_pct(PLANT, "CC_CHP", iso="NYISO") / 100.0
    for year in YEARS:
        bench = bench_plants(year)
        m, c = plant_series(run, bench, KEY, year)
        e_ann = float(bench[KEY]["e_ann"])
        offset = e_ann * 1e6 * sector / T
        lp = np.clip(m - offset, 0.0, None)
        rc = reconstructed(year)
        st = rc["static"]
        rows = st.index[st.plant_code == PLANT].to_numpy()
        names = st.loc[rows, "unit_id"].tolist()
        mc = rc["mc"][rows]
        avail = rc["avail"][rows][0]
        cap = float(st.loc[rows, "pmax"].sum())
        mp = model_zone_price(year)["Upstate_West"].to_numpy()
        act = actual_zone_price(year)
        ap_c = act["zone_C"].to_numpy()
        ap_uw = act["Upstate_West"].to_numpy()
        i_comm = [i for i, n in enumerate(names) if n.endswith("_committed")][0]
        i_econ = [i for i, n in enumerate(names) if n.endswith("_econc05")][0]
        i_peak = [i for i, n in enumerate(names) if n.endswith("_peak")][0]
        both = (lp > ON_MW) & (c > ON_MW)
        flip = (mc[i_econ] < mp) & (mc[i_econ] >= ap_c)
        part = (c > ON_MW) & (c < PART_LOAD_FRAC * float(np.percentile(c, 99.5)))
        y = {
            "published": {
                "m_ann_twh": round(float(m.sum()) / 1e6, 3),
                "campd_twh": round(float(c.sum()) / 1e6, 3),
                "over_twh": round(float(m.sum() - c.sum()) / 1e6, 3),
                "hourly_max_mw": round(float(m.max()), 0),
            },
            "sector_addback_mw": round(offset, 1),
            "lp_capacity_mw": round(cap, 1),
            "lp_avail_max": round(float(avail.max()), 3),
            "corrected": {
                "lp_twh": round(float(lp.sum()) / 1e6, 3),
                "campd_twh": round(float(c.sum()) / 1e6, 3),
                "over_twh": round(float(lp.sum() - c.sum()) / 1e6, 3),
                "lp_hourly_max_mw": round(float(lp.max()), 0),
                "campd_hourly_max_mw": round(float(c.max()), 0),
                "lp_cf_on_available_cap": round(
                    float(lp.sum() / (cap * avail).sum()), 3
                ),
                "campd_cf_on_available_cap": round(
                    float(c.sum() / (cap * avail).sum()), 3
                ),
                "on_share_lp": round(float((lp > ON_MW).mean()), 3),
                "on_share_campd": round(float((c > ON_MW).mean()), 3),
                "gap_meas_off_lp_on_twh": round(
                    float(lp[(c <= ON_MW) & (lp > ON_MW)].sum()) / 1e6, 3
                ),
                "gap_both_on_level_twh": round(
                    float((lp[both] - c[both]).sum()) / 1e6, 3
                ),
                "gap_lp_off_meas_on_twh": round(
                    -float(c[(lp <= ON_MW) & (c > ON_MW)].sum()) / 1e6, 3
                ),
                "loading_when_on_p50_lp": round(
                    float(np.percentile(lp[lp > ON_MW], 50)), 0
                ),
                "loading_when_on_p50_campd": round(
                    float(np.percentile(c[c > ON_MW], 50)), 0
                ),
            },
            "offer_position": {
                "mc_mean_committed": round(float(mc[i_comm].mean()), 2),
                "mc_mean_econ05": round(float(mc[i_econ].mean()), 2),
                "mc_mean_peak": round(float(mc[i_peak].mean()), 2),
                "in_merit_econ05_vs_model_uw": round(
                    float((mc[i_econ] < mp).mean()), 3
                ),
                "in_merit_econ05_vs_actual_zone_c": round(
                    float((mc[i_econ] < ap_c).mean()), 3
                ),
                "in_merit_econ05_vs_actual_uw_mean": round(
                    float((mc[i_econ] < ap_uw).mean()), 3
                ),
                "price_mean_model_uw": round(float(mp.mean()), 2),
                "price_mean_actual_zone_c": round(float(ap_c.mean()), 2),
                "share_hours_actual_c_below_20": round(float((ap_c < 20).mean()), 3),
                "share_hours_model_uw_below_20": round(float((mp < 20).mean()), 3),
                "p05_actual_c": round(float(np.percentile(ap_c, 5)), 1),
                "p05_model_uw": round(float(np.percentile(mp, 5)), 1),
                "trough_flip_hours": int(flip.sum()),
                "corrected_gap_in_trough_flip_hours_twh": round(
                    float((lp - c)[flip].sum()) / 1e6, 3
                ),
                "corrected_gap_in_other_hours_twh": round(
                    float((lp - c)[~flip].sum()) / 1e6, 3
                ),
                "campd_part_load_share_of_on_hours": round(
                    float(part.sum() / (c > ON_MW).sum()), 3
                ),
                "actual_c_mean_in_part_load_hours": round(float(ap_c[part].mean()), 2),
                "share_part_load_hours_actual_c_above_econ05": round(
                    float((ap_c[part] > mc[i_econ][part]).mean()), 3
                ),
            },
            "campd_conduct": campd_units(year),
        }
        rec["by_year"][str(year)] = y
        cor, op = y["corrected"], y["offer_position"]
        print(
            f"{year}: published over {y['published']['over_twh']:+.3f} -> corrected {cor['over_twh']:+.3f} TWh "
            f"(LP {cor['lp_twh']} vs CAMPD {cor['campd_twh']}); CF {cor['lp_cf_on_available_cap']} vs {cor['campd_cf_on_available_cap']}; "
            f"level {cor['gap_both_on_level_twh']:+.3f} / hours-on {cor['gap_meas_off_lp_on_twh']:+.3f}"
        )
        print(
            f"   econ05 mc {op['mc_mean_econ05']} in-merit vs model UW {op['in_merit_econ05_vs_model_uw']} vs actual C {op['in_merit_econ05_vs_actual_zone_c']}; "
            f"actual C<20 {op['share_hours_actual_c_below_20']} vs model {op['share_hours_model_uw_below_20']}; trough-flip share of gap "
            f"{op['corrected_gap_in_trough_flip_hours_twh']:+.3f} of {cor['over_twh']:+.3f}"
        )
    print("census:", rec["census_rule"])
    write_json("_nyiso192_sithe_duty_phase0.json", rec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
