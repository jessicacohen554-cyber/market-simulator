"""PJM close-out census 0c (ZERO LP): does real PJM coal hold synchronized
reserve / regulation, and does the keeper's coal hold ~0?

Plan: docs/backcast-closeout-plan-2026-10.md §3.6 step 0c; research shard
docs/records/governance/closeout-2026-10/SHARD-PJM-closeout-research-2026-10-02.md
§4 L1. Pre-fixed reading: charter L1 iff coal >= 25 % of REAL synchronized
reserve AND ~0 in the model.

MODEL side (no solve): the keeper ``results/calibration/pjmnext16_A_span``
arms ``energy_reserve_coopt + pjm_reserve_pergen`` (sync split off). Pool
membership is ``_reserve_eligible`` (fuel in ``RESERVE_FUEL_TYPES``, which
contains ``coal``) AND ``FleetArrays.ramp10 > 0`` (``RAMP10_FRAC_BY_GROUP``
gives every COAL_* subclass 0.15) -> coal IS a pool member by construction.
The bundle commits only pooled ``held_mw`` (``hourly/reserve_family_<y>``),
so per-class held is not identified; this probe bounds it per hour from the
committed ``hourly/unit_marginal_<y>`` slim layer:

* pool (zone, fuel) capability_t = min(sum ramp10_frac * cap_mw,
  sum (cap_mw - mw))  -- the pergen R bound and joint P+R row
  (cap_mw is the availability-scaled pmax; the class fraction stands in for
  the measured_ramp_capability reconciliation, whose raw data is not in this
  partial clone -- an approximation, flagged in the JSON);
* forced coal held_t = max(0, held_RTO - noncoal_cap_all,
  held_MAD - noncoal_cap_MAD)   (minimum coal R any optimum must carry);
* coal capability_t = sum over coal pools (maximum coal R).

REAL side: IMM State of the Market §10 (2019-2025), digitized below with
table / PDF page per row (see ``IMM_ROWS``); written to
``results/phase0/pjm/_pjmco_0c_som_sec10_reserve_by_unit_type.csv``.
Pre-Oct-2022 synchronized reserve = Tier 1 (estimated online headroom, the
fuel split is of CREDITED tier-1 MW) + Tier 2 (cleared); coal share =
(T1_avg*coal_T1% + T2_avg*coal_T2%) / (T1_avg + T2_avg) with T1/T2 RTO
averages from the same report. Post-reform: coal share of real-time capped
synchronized-reserve MWh.

Run: ``.venv/bin/python scripts/probes/_pjmco_0c_reserve_census.py``
Writes ``results/phase0/pjm/_pjmco_0c_reserve_census.json`` and the CSV.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.fleet.withholding import (
    RAMP10_FRAC_BY_FUEL,
    RAMP10_FRAC_BY_GROUP,
)
from market_sim.model.reserves.spec import PJM_MAD_ZONES, RESERVE_FUEL_TYPES

ROOT = Path(__file__).resolve().parents[2]
KEEPER = ROOT / "results/calibration/pjmnext16_A_span"
OUT_DIR = ROOT / "results/phase0/pjm"
OUT_JSON = OUT_DIR / "_pjmco_0c_reserve_census.json"
OUT_CSV = OUT_DIR / "_pjmco_0c_som_sec10_reserve_by_unit_type.csv"
YEARS = list(range(2019, 2026))
FAIL_YEARS = [2019, 2020, 2021, 2025]  # COAL_BIT C1 over-run years
THRESHOLD = 0.25  # pre-fixed charter reading

URL = (
    "https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/"
    "{y}/{y}-som-pjm-sec10.pdf"
)

# ---------------------------------------------------------------------------
# REAL side: IMM SOM §10 digitization. (year, metric, category, value, unit,
# table, pdf_page, printed_page). Percent values are as printed.
# ---------------------------------------------------------------------------
IMM_ROWS: list[tuple] = [
    # 2019 report
    (2019, "rto_avg_tier1_mw", "all", 2121.8, "MW", "Table 10-7 Average monthly reserves used to satisfy the primary reserve requirement, RTO Zone", 14, None),
    (2019, "rto_avg_tier2_mw", "all", 567.2, "MW", "Table 10-7 (same)", 14, None),
    (2019, "tier1_pct_by_mw", "Steam - Coal", 32.1, "%", "Table 10-9 Supply of tier 1 synchronized reserve by unit and fuel type: 2019", 17, 465),
    (2019, "tier2_pct_by_mw", "Steam - Coal", 2.4, "%", "Table 10-15 Supply of Generation Tier 2 Synchronized Reserve by Unit Type and Fuel Type: 2019", 22, 470),
    (2019, "regulation_settled_mw", "Coal", 371954.1, "MW-h settled", "Table 10-37 PJM regulation by source: 2015 through 2019", 50, 498),
    (2019, "regulation_settled_mw", "Total", 4533478.5, "MW-h settled", "Table 10-37 (same)", 50, 498),
    # 2020 report
    (2020, "rto_avg_tier1_mw", "all", 2039.2, "MW", "Table 10-7 Average monthly reserves used to satisfy the primary reserve requirement, RTO Zone", 16, None),
    (2020, "rto_avg_tier2_mw", "all", 450.9, "MW", "Table 10-7 (same)", 16, None),
    (2020, "tier1_pct_by_mw", "Steam - Coal", 56.9, "%", "Table 10-9 Supply of tier 1 synchronized reserve by unit and fuel type: 2020", 18, 476),
    (2020, "tier2_pct_by_mw", "Steam - Coal", 3.6, "%", "Table 10-14 Supply of Generation Tier 2 Synchronized Reserve by Unit Type and Fuel Type: 2020", 23, 481),
    (2020, "regulation_settled_mw", "Coal", 344862.0, "MW-h settled", "Table 10-37 PJM regulation by source: 2019 and 2020", 52, 510),
    (2020, "regulation_settled_mw", "Total", 4625428.8, "MW-h settled", "Table 10-37 (same)", 52, 510),
    # 2021 report
    (2021, "rto_avg_tier1_mw", "all", 1568.7, "MW", "Table 10-7 Average monthly reserves used to satisfy the primary reserve requirement, RTO Zone", 15, 503),
    (2021, "rto_avg_tier2_mw", "all", 669.1, "MW", "Table 10-7 (same)", 15, 503),
    (2021, "tier1_pct_by_mw", "Steam - Coal", 22.6, "%", "Table 10-8 Supply of tier 1 synchronized reserve by resource and fuel type: 2021", 17, 505),
    (2021, "tier2_pct_by_mw", "Steam - Coal", 2.2, "%", "Table 10-14 Supply of Tier 2 Synchronized Reserve by Resource Type and Fuel Type: 2021", 22, 510),
    (2021, "regulation_settled_mw", "Coal", 329515.0, "MW-h settled", "Table 10-46 PJM regulation by source: 2020 and 2021", 55, 543),
    (2021, "regulation_settled_mw", "Total", 4616116.0, "MW-h settled", "Table 10-46 (same)", 55, 543),
    # 2022 report (Jan-Sep tiered; Oct-Dec consolidated SR)
    (2022, "rto_avg_tier1_mw_jan_sep", "all", 1531.4, "MW", "Table 10-9 Average monthly reserves used ..., RTO Zone (hour-weighted mean of the Jan-Sep monthly rows; matches the text figure 1,531.4 MW)", 18, 554),
    (2022, "rto_avg_tier2_mw_jan_sep", "all", 515.7, "MW", "Table 10-9 (hour-weighted mean of the Jan-Sep monthly rows)", 18, 554),
    (2022, "tier1_pct_by_mw_jan_sep", "Steam - Coal", 19.5, "%", "Table 10-11 Supply of tier 1 synchronized reserve by resource and fuel type: January through September, 2022", 20, 556),
    (2022, "tier2_pct_by_mw_jan_sep", "Steam - Coal", 1.8, "%", "Table 10-17 Supply of Tier 2 Synchronized Reserve by Resource Type and Fuel Type: January through September, 2022", 25, 561),
    (2022, "sr_rt_capped_mwh_oct_dec", "Steam - Coal", 698938.0, "MWh", "Table 10-26 Day-ahead and Real-time Synchronized Reserve by Resource Type and Fuel Type: October through December, 2022", 33, 569),
    (2022, "sr_rt_capped_mwh_oct_dec", "Total", 3906127.0, "MWh", "Table 10-26 (sum of resource rows)", 33, 569),
    (2022, "sr_da_mwh_oct_dec", "Steam - Coal", 396596.0, "MWh", "Table 10-26 (same)", 33, 569),
    (2022, "sr_da_mwh_oct_dec", "Total", 4561400.0, "MWh", "Table 10-26 (sum of resource rows)", 33, 569),
    (2022, "regulation_settled_mw", "Coal", 218050.0, "MW-h settled", "Table 10-57 PJM regulation by source: 2021 and 2022", 65, 601),
    (2022, "regulation_settled_mw", "Total", 4471303.7, "MW-h settled", "Table 10-57 (same)", 65, 601),
    # 2023 report
    (2023, "sr_rt_capped_mwh", "Steam - Coal", 4697152.0, "MWh", "Table 10-18 Day-ahead and real-time synchronized reserve by resource type and fuel type: 2023", 25, 555),
    (2023, "sr_rt_capped_mwh", "Total", 19553465.0, "MWh", "Table 10-18 (sum of resource rows)", 25, 555),
    (2023, "sr_da_mwh", "Steam - Coal", 5005010.0, "MWh", "Table 10-18 (same)", 25, 555),
    (2023, "sr_da_mwh", "Total", 21672451.0, "MWh", "Table 10-18 (sum of resource rows)", 25, 555),
    (2023, "regulation_settled_mw", "Coal", 212412.0, "MW-h settled", "Table 10-46 PJM regulation by source: 2022 and 2023", 62, 592),
    (2023, "regulation_settled_mw", "Total", 4525717.6, "MW-h settled", "Table 10-46 (same)", 62, 592),
    # 2024 report
    (2024, "sr_rt_capped_mwh", "Steam - Coal", 5255510.0, "MWh", "Table 10-19 Day-ahead and real-time synchronized reserve by resource type and fuel type: 2024", 27, 549),
    (2024, "sr_rt_capped_mwh", "Total", 22394728.0, "MWh", "Table 10-19 (sum of resource rows)", 27, 549),
    (2024, "sr_da_mwh", "Steam - Coal", 5327995.0, "MWh", "Table 10-19 (same)", 27, 549),
    (2024, "sr_da_mwh", "Total", 23779656.0, "MWh", "Table 10-19 (sum of resource rows)", 27, 549),
    (2024, "regulation_settled_mw", "Coal", 229226.0, "MW-h settled", "Table 10-45 PJM regulation by source: 2023 and 2024", 65, 587),
    (2024, "regulation_settled_mw", "Total", 4557537.6, "MW-h settled", "Table 10-45 (same)", 65, 587),
    # 2025 report
    (2025, "sr_rt_capped_mwh", "Steam - Coal", 3656794.0, "MWh", "Table 10-19 Day-ahead and real-time synchronized reserve by resource type and fuel type: 2025", 32, 596),
    (2025, "sr_rt_capped_mwh", "Total", 25891149.0, "MWh", "Table 10-19 (sum of resource rows)", 32, 596),
    (2025, "sr_da_mwh", "Steam - Coal", 3209546.0, "MWh", "Table 10-19 (same)", 32, 596),
    (2025, "sr_da_mwh", "Total", 23048638.0, "MWh", "Table 10-19 (sum of resource rows)", 32, 596),
    (2025, "regulation_settled_mw_jan_sep", "Coal", 202223.0, "MW-h settled", "Table 10-52 PJM regulation by source: January through September, 2024 and the first nine months of 2025", 79, 643),
    (2025, "regulation_settled_mw_jan_sep", "Total", 4651644.8, "MW-h settled", "Table 10-52 (same)", 79, 643),
    (2025, "regulation_settled_mw_oct_dec", "Coal", 27572.0, "MW-h settled", "Table 10-54 PJM regulation by source: October through December, 2024 and 2025", 80, 644),
    (2025, "regulation_settled_mw_oct_dec", "Total", 1454024.2, "MW-h settled", "Table 10-54 (same)", 80, 644),
]

# Resource rows behind the post-reform totals (RT capped MWh, DA MWh), as
# printed, so the sums above are reproducible.
SR_TABLE_ROWS: dict[int, dict[str, tuple[float, float]]] = {
    2022: {  # Oct-Dec; (DA, RT capped)
        "CT - Natural Gas": (1026381, 1039432), "Steam - Coal": (396596, 698938),
        "DSR": (50396, 310121), "Steam - Natural Gas": (84216, 82997),
        "Steam - Other": (7369, 5801), "RICE - Natural Gas": (450, 1977),
        "CT - Other": (4, 4), "RICE - Oil": (360, 33), "Steam - Oil": (1011, 1558),
        "RICE - Other": (105746, 10799), "Hydro - Run of River": (288965, 142414),
        "CT - Oil": (28974, 33855), "Hydro - Pumped Storage": (368167, 169306),
        "Combined Cycle": (2202765, 1408892),
    },
    2023: {
        "Combined Cycle": (8313674, 5696086), "CT - Natural Gas": (3978699, 4200732),
        "Steam - Coal": (5005010, 4697152), "DSR": (525530, 2150191),
        "CT - Oil": (628944, 769626), "Hydro - Pumped Storage": (1167783, 459649),
        "Hydro - Run of River": (1111434, 876697), "Steam - Natural Gas": (495532, 509080),
        "RICE - Other": (303823, 145349), "RICE - Natural Gas": (42804, 12216),
        "Steam - Other": (85255, 16405), "Steam - Oil": (11011, 13201),
        "Solar": (2864, 4464), "RICE - Oil": (77, 0), "Battery": (0, 2611),
        "CT - Other": (11, 6),
    },
    2024: {
        "Combined Cycle": (11293671, 7467937), "CT - Natural Gas": (2021203, 3022332),
        "DSR": (1462985, 3433960), "Steam - Coal": (5327995, 5255510),
        "CT - Oil": (417126, 523362), "Hydro - Run of River": (1006597, 928017),
        "Hydro - Pumped Storage": (1234145, 746633), "Steam - Natural Gas": (519438, 746741),
        "RICE - Other": (309829, 181736), "Steam - Other": (101694, 19702),
        "RICE - Natural Gas": (42157, 12728), "Other": (42816, 56070),
    },
    2025: {
        "Combined Cycle": (11134445, 10388649), "CT - Natural Gas": (1855554, 3580078),
        "DSR": (2733174, 4200370), "Steam - Coal": (3209546, 3656794),
        "CT - Oil": (449077, 667848), "Hydro - Pumped Storage": (1269494, 1659861),
        "Steam - Natural Gas": (603339, 705801), "Hydro - Run of River": (1288618, 750556),
        "RICE - Other": (301679, 174872), "RICE - Natural Gas": (70040, 34723),
        "Steam - Other": (76199, 10914), "Other": (57473, 60683),
    },
}
# 2022 Jan-Sep RTO monthly (tier-1 MW, tier-2 MW), Table 10-9 p.554.
RTO_2022_JAN_SEP = [
    (1711.1, 358.8), (1949.3, 256.6), (1513.4, 448.2), (1152.3, 596.2),
    (1471.1, 606.4), (1532.6, 654.4), (1464.7, 592.0), (1428.9, 657.7),
    (1589.2, 450.8),
]
DAYS_2022 = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _imm(year: int, metric: str, cat: str) -> float:
    """Return one digitized IMM value."""
    for r in IMM_ROWS:
        if r[0] == year and r[1] == metric and r[2] == cat:
            return float(r[3])
    raise KeyError((year, metric, cat))


def real_side() -> dict:
    """Coal share of real synchronized reserve and regulation per year."""
    for y, rows in SR_TABLE_ROWS.items():  # self-check the digitized sums
        rt = sum(v[1] for v in rows.values())
        da = sum(v[0] for v in rows.values())
        key = "_oct_dec" if y == 2022 else ""
        assert abs(rt - _imm(y, f"sr_rt_capped_mwh{key}", "Total")) < 1, (y, rt)
        assert abs(da - _imm(y, f"sr_da_mwh{key}", "Total")) < 1, (y, da)
    out: dict = {}
    for y in YEARS:
        rec: dict = {}
        if y <= 2021:
            t1, t2 = _imm(y, "rto_avg_tier1_mw", "all"), _imm(y, "rto_avg_tier2_mw", "all")
            c1 = _imm(y, "tier1_pct_by_mw", "Steam - Coal") / 100
            c2 = _imm(y, "tier2_pct_by_mw", "Steam - Coal") / 100
            coal_mw = t1 * c1 + t2 * c2
            rec.update(
                basis="pre-reform: RTO avg tier1*coal%T1(credited) + tier2*coal%T2",
                tier1_avg_mw=t1, tier2_avg_mw=t2,
                coal_pct_tier1=c1, coal_pct_tier2=c2,
                coal_sr_avg_mw=coal_mw, sr_avg_mw=t1 + t2,
                coal_share_sr=coal_mw / (t1 + t2),
            )
        elif y == 2022:
            w = np.array(DAYS_2022[:9], dtype=float) * 24
            arr = np.array(RTO_2022_JAN_SEP)
            t1 = float((arr[:, 0] * w).sum() / w.sum())
            t2 = float((arr[:, 1] * w).sum() / w.sum())
            c1 = _imm(y, "tier1_pct_by_mw_jan_sep", "Steam - Coal") / 100
            c2 = _imm(y, "tier2_pct_by_mw_jan_sep", "Steam - Coal") / 100
            h = float(w.sum())
            coal_js = (t1 * c1 + t2 * c2) * h
            tot_js = (t1 + t2) * h
            coal_q4 = _imm(y, "sr_rt_capped_mwh_oct_dec", "Steam - Coal")
            tot_q4 = _imm(y, "sr_rt_capped_mwh_oct_dec", "Total")
            rec.update(
                basis="Jan-Sep tiered (hour-weighted) + Oct-Dec RT capped MWh",
                tier1_avg_mw_jan_sep=t1, tier2_avg_mw_jan_sep=t2,
                coal_share_sr_jan_sep=coal_js / tot_js,
                coal_share_sr_oct_dec=coal_q4 / tot_q4,
                coal_sr_avg_mw=(coal_js + coal_q4) / 8760,
                coal_share_sr=(coal_js + coal_q4) / (tot_js + tot_q4),
            )
        else:
            c = _imm(y, "sr_rt_capped_mwh", "Steam - Coal")
            t = _imm(y, "sr_rt_capped_mwh", "Total")
            rec.update(
                basis="post-reform: RT capped synchronized-reserve MWh",
                coal_sr_mwh=c, sr_mwh=t, coal_sr_avg_mw=c / 8760,
                coal_share_sr=c / t,
                coal_share_sr_da=_imm(y, "sr_da_mwh", "Steam - Coal")
                / _imm(y, "sr_da_mwh", "Total"),
            )
        if y == 2025:
            cr = _imm(y, "regulation_settled_mw_jan_sep", "Coal") + _imm(
                y, "regulation_settled_mw_oct_dec", "Coal"
            )
            tr = _imm(y, "regulation_settled_mw_jan_sep", "Total") + _imm(
                y, "regulation_settled_mw_oct_dec", "Total"
            )
            rec["regulation_note"] = (
                "Table 10-52 (labelled Jan-Sep) + Table 10-54 (Oct-Dec, new design)"
            )
        else:
            cr = _imm(y, "regulation_settled_mw", "Coal")
            tr = _imm(y, "regulation_settled_mw", "Total")
        rec["coal_share_regulation"] = cr / tr
        rec["coal_regulation_avg_mw"] = cr / 8760
        rec["coal_sr_plus_reg_twh_equiv"] = (rec["coal_sr_avg_mw"] + cr / 8760) * 8760 / 1e6
        rec["real_leg_ge_25pct"] = bool(rec["coal_share_sr"] >= THRESHOLD)
        out[str(y)] = rec
    return out


def _frac(pg: pd.Series, fuel: pd.Series) -> np.ndarray:
    """Class 10-min ramp fraction exactly as fleet._ramp10_capability (pre-measured)."""
    f = pg.map(RAMP10_FRAC_BY_GROUP)
    f = f.fillna(fuel.map(RAMP10_FRAC_BY_FUEL)).fillna(0.0)
    return f.to_numpy(dtype=float)


def model_side_year(y: int) -> dict:
    """Bound the keeper's coal-held reserve for one year from committed artifacts."""
    um = pd.read_parquet(
        KEEPER / f"hourly/unit_marginal_{y}.parquet",
        columns=["plant_group", "fuel", "zone", "hour", "mw", "cap_mw"],
    )
    um = um[um["fuel"].astype(str).isin(RESERVE_FUEL_TYPES)]
    pg = um["plant_group"].astype(str)
    fuel = um["fuel"].astype(str)
    frac = _frac(pg, fuel)
    keep = frac > 0.0  # pjm_pergen_structure: eligible & ramp10 > 0
    um = um.loc[keep].copy()
    um["ramp"] = frac[keep] * um["cap_mw"].to_numpy()
    um["head"] = np.clip(um["cap_mw"].to_numpy() - um["mw"].to_numpy(), 0.0, None)
    um["is_coal"] = um["fuel"].astype(str) == "coal"
    um["mad"] = um["zone"].astype(str).isin(PJM_MAD_ZONES)
    members = um.groupby(um["fuel"].astype(str)).size() / 8760
    pool = (
        um.groupby([um["zone"].astype(str), um["fuel"].astype(str), "hour"], observed=True)[
            ["ramp", "head"]
        ]
        .sum()
        .reset_index()
    )
    pool["cap"] = np.minimum(pool["ramp"], pool["head"])
    pool["is_coal"] = pool["fuel"] == "coal"
    pool["mad"] = pool["zone"].isin(PJM_MAD_ZONES)
    H = 8760

    def _h(mask: pd.Series) -> np.ndarray:
        s = pool.loc[mask].groupby("hour")["cap"].sum()
        return s.reindex(range(H), fill_value=0.0).to_numpy()

    coal_cap = _h(pool["is_coal"])
    nc_all = _h(~pool["is_coal"])
    nc_mad = _h(~pool["is_coal"] & pool["mad"])
    ct_oil = _h(pool["fuel"].isin(["gas_ct", "oil"]))
    rf = pd.read_parquet(KEEPER / f"hourly/reserve_family_{y}.parquet")
    rf = rf[rf["pass"].astype(str) == "P1"]
    rto = rf[rf["family"].astype(str) == "pjm_primary"].sort_values("hour")
    mad = rf[rf["family"].astype(str) == "pjm_primary_mad"].sort_values("hour")
    held_rto = rto["held_mw"].to_numpy()[:H]
    held_mad = mad["held_mw"].to_numpy()[:H] if len(mad) else np.zeros(H)
    forced = np.maximum.reduce(
        [np.zeros(H), held_rto - nc_all, held_mad - nc_mad]
    )
    coal_max = np.minimum(coal_cap, held_rto)
    coal_units = um.loc[um["is_coal"]]
    coal_head = coal_units.groupby("hour")["head"].sum().reindex(range(H), fill_value=0).to_numpy()
    return {
        "pool_member_units_by_fuel": {k: round(float(v), 1) for k, v in members.items()},
        "coal_is_pool_member": bool(members.get("coal", 0) > 0),
        "held_rto_avg_mw": float(held_rto.mean()),
        "held_mad_avg_mw": float(held_mad.mean()),
        "rto_dual_hours_gt0": int((rto["dual"].to_numpy()[:H] > 1e-6).sum()),
        "mad_dual_hours_gt0": int((mad["dual"].to_numpy()[:H] > 1e-6).sum()) if len(mad) else 0,
        "rto_dual_avg": float(rto["dual"].to_numpy()[:H].mean()),
        "rto_shortfall_hours": int((rto["shortfall_mw"].to_numpy()[:H] > 1e-6).sum()),
        "noncoal_capability_avg_mw": float(nc_all.mean()),
        "noncoal_capability_min_mw": float(nc_all.min()),
        "noncoal_mad_capability_min_mw": float(nc_mad.min()),
        "ct_oil_capability_avg_mw": float(ct_oil.mean()),
        "coal_capability_avg_mw": float(coal_cap.mean()),
        "coal_headroom_avg_mw": float(coal_head.mean()),
        "forced_coal_held_avg_mw": float(forced.mean()),
        "forced_coal_held_max_mw": float(forced.max()),
        "forced_coal_held_hours_gt0": int((forced > 1e-6).sum()),
        "forced_coal_held_twh": float(forced.sum() / 1e6),
        "coal_held_upper_avg_mw": float(coal_max.mean()),
        "coal_held_upper_twh": float(coal_max.sum() / 1e6),
    }


def main() -> None:
    """Run the census and write the JSON and CSV outputs."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    real = real_side()
    model = {str(y): model_side_year(y) for y in YEARS}
    per_year = {}
    for y in YEARS:
        r, m = real[str(y)], model[str(y)]
        model_zero = m["forced_coal_held_hours_gt0"] == 0
        per_year[str(y)] = {
            "coal_share_sr_real": round(r["coal_share_sr"], 4),
            "coal_share_reg_real": round(r["coal_share_regulation"], 4),
            "model_coal_member": m["coal_is_pool_member"],
            "model_forced_coal_held_avg_mw": round(m["forced_coal_held_avg_mw"], 2),
            "model_coal_held_upper_avg_mw": round(m["coal_held_upper_avg_mw"], 1),
            "real_leg": r["real_leg_ge_25pct"],
            "model_leg_strict_excluded": not m["coal_is_pool_member"],
            "model_leg_forced_zero": model_zero,
            "charter_L1": bool(r["real_leg_ge_25pct"] and model_zero),
        }
    fail_pass = [per_year[str(y)]["charter_L1"] for y in FAIL_YEARS]
    result = {
        "census": "PJM close-out 0c reserve-holding census (zero LP)",
        "keeper": str(KEEPER.relative_to(ROOT)),
        "threshold_coal_share_sr": THRESHOLD,
        "membership": {
            "rule": "pjm_pergen_structure: gen_idx = _reserve_eligible & ramp10>0",
            "reserve_fuel_types": sorted(RESERVE_FUEL_TYPES),
            "coal_ramp10_frac": {k: v for k, v in RAMP10_FRAC_BY_GROUP.items() if k.startswith("COAL")},
            "coal_excluded_by_construction": False,
            "register_row31_gas_oil": (
                "refers to the as_reserve_withholding probe pool _AS_PJM_GROUPS "
                "(data/fleet/withholding.py), OFF in the keeper; not the pergen co-opt"
            ),
            "approximation": (
                "ramp10 uses class fractions; keeper also arms measured_ramp_capability "
                "(per-plant reconciliation, raw data not hydrated) -- bounds are approximate"
            ),
        },
        "aggregation": (
            "Per year: charter_L1 = real coal share of SR >= 25% AND model forced coal held = 0 "
            "in every hour. Overall call made on the COAL_BIT fail years 2019/2020/2021/2025: "
            "PASS only if every fail year passes."
        ),
        "fail_years": FAIL_YEARS,
        "fail_year_pass": dict(zip(map(str, FAIL_YEARS), fail_pass)),
        "overall": "PASS" if all(fail_pass) else "FAIL",
        "per_year": per_year,
        "real": real,
        "model": model,
        "sources": {str(y): URL.format(y=y) for y in YEARS},
    }
    OUT_JSON.write_text(json.dumps(result, indent=2))
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year", "metric", "category", "value", "unit", "table", "pdf_page", "printed_page", "source_url"])
        for r in IMM_ROWS:
            w.writerow([*r, URL.format(y=r[0])])
        for y, rows in SR_TABLE_ROWS.items():
            tbl = next(t[5] for t in IMM_ROWS if t[0] == y and t[1].startswith("sr_rt"))
            pdfp = next(t[6] for t in IMM_ROWS if t[0] == y and t[1].startswith("sr_rt"))
            prp = next(t[7] for t in IMM_ROWS if t[0] == y and t[1].startswith("sr_rt"))
            sfx = "_oct_dec" if y == 2022 else ""
            for cat, (da, rt) in rows.items():
                w.writerow([y, f"sr_da_mwh{sfx}", cat, da, "MWh", tbl, pdfp, prp, URL.format(y=y)])
                w.writerow([y, f"sr_rt_capped_mwh{sfx}", cat, rt, "MWh", tbl, pdfp, prp, URL.format(y=y)])
    print(json.dumps({"per_year": per_year, "overall": result["overall"]}, indent=1))


if __name__ == "__main__":
    main()
