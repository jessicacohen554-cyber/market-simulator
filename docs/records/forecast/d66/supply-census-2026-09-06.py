"""capx D66 — PJM supply-census reconciliation instrument (ZERO LP).

Reconstructs the model's offered supply for DY 2022/23–2025/26 from the
COMMITTED D57 arm-A ledgers, places PJM's OWN published BRA supply beside it,
and decomposes the position gap into additive, named buckets.

Two sides, both read-only:

* MODEL — ``results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/
  f0e050e820c1159a/evolution_<year>.json`` (``capacity_clearing`` +
  ``screen_*`` fields), plus the renewable / storage pools recorded by the
  D45-R control bundle's ledgers (``c6091bd5b62bbc3f``; the same recipe up to
  the three D48 / clearing gates, which move the THERMAL accreditation basis
  and the DR term only — never the VRE / storage pools), plus the two registry
  constants the price-taker block carries verbatim
  (``ADEQUACY_EXTERNAL_TIE_FIRM_MW['PJM']``,
  ``DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO['PJM']``).
* PUBLISHED — PJM's Base Residual Auction Reports (sha256-verified against the
  identities recorded in ``data/raw/capacity-market/auction-supply/pjm/
  README.md``) and the in-repo ``data/raw/capacity-market/demand-curve/pjm/
  pjm.csv`` / ``auction-price/pjm/pjm.csv``.

Rule 13: every published figure is an observable compared against; none is an
input. Rule 14: the published number is preferred and every discrepancy is
reported at full magnitude on its own row.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ARM_A = REPO / (
    "results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a"
)
CONTROL = REPO / "results/hindcast/pjm-2021-2025-realized-t1h-d45r/PJM/c6091bd5b62bbc3f"
DEMAND_CURVE_CSV = REPO / "data/raw/capacity-market/demand-curve/pjm/pjm.csv"
AUCTION_PRICE_CSV = REPO / "data/raw/capacity-market/auction-price/pjm/pjm.csv"

SCREEN_TO_DY = {2022: "2022/2023", 2023: "2023/2024", 2024: "2024/2025", 2025: "2025/2026"}

# --- registry constants the price-taker block carries verbatim -------------- #
# src/market_sim/config/capacity_market.py
PJM_FIRM_IMPORT_MW = 1_281.7  # ADEQUACY_EXTERNAL_TIE_FIRM_MW["PJM"]
PJM_DR_SUPPLY_UCAP = {  # DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO["PJM"]
    "2022/2023": 10_513.0,
    "2023/2024": 10_116.7,
    "2024/2025": 10_146.4,
    "2025/2026": 6_084.8,
}

# --- PUBLISHED: Table 9 (2024/25 BRA Report, p.14) "Offered and Cleared MWs by
# Type for RPM and committed FRR for previous BRAs", UCAP.  The 2025/26 column
# is the 2027/28 BRA Report Table 6 (p.11), the same table one report later —
# the 2025/26 report's own copy is an IMAGE and does not extract.  Where the two
# vintages overlap (2024/25) they agree to <=15 MW per row; the restatement is
# recorded in `PUBLISHED_RESTATEMENTS` and never reconciled away.
PUBLISHED_RPM_PLUS_FRR = {  # (offered UCAP, cleared UCAP)
    "2022/2023": {
        "Coal": (45_754, 39_230), "Distillate Oil (No.2)": (3_178, 2_897),
        "Gas": (85_562, 79_329), "Nuclear": (31_944, 26_140), "Oil": (2_674, 2_527),
        "Solar": (2_633, 2_096), "Water": (6_917, 6_749), "Wind": (2_595, 1_839),
        "Battery/Hybrid": (0, 0), "Other": (1_205, 1_168),
        "Demand Response": (10_604, 8_903), "Aggregate Resource": (484, 386),
        "TOTAL_NO_EE": (193_551, 171_263), "Energy Efficiency": (5_057, 4_811),
    },
    "2023/2024": {
        "Coal": (37_164, 31_811), "Distillate Oil (No.2)": (2_894, 2_855),
        "Gas": (85_217, 81_643), "Nuclear": (31_960, 31_960), "Oil": (2_350, 2_269),
        "Solar": (2_945, 2_935), "Water": (6_375, 6_375), "Wind": (1_608, 1_416),
        "Battery/Hybrid": (16, 16), "Other": (1_185, 1_185),
        "Demand Response": (10_652, 8_631), "Aggregate Resource": (511, 511),
        "TOTAL_NO_EE": (182_875, 171_605), "Energy Efficiency": (5_471, 5_471),
    },
    "2024/2025": {
        "Coal": (35_114, 31_532), "Distillate Oil (No.2)": (2_776, 2_674),
        "Gas": (85_469, 83_243), "Nuclear": (31_835, 31_629), "Oil": (2_493, 2_242),
        "Solar": (4_234, 4_232), "Water": (6_137, 6_137), "Wind": (1_396, 1_396),
        "Battery/Hybrid": (46, 46), "Other": (1_153, 1_153),
        "Demand Response": (10_334, 8_173), "Aggregate Resource": (503, 503),
        "TOTAL_NO_EE": (181_491, 172_961), "Energy Efficiency": (8_417, 7_667),
    },
    "2025/2026": {  # 2027/2028 BRA Report Table 6, 2025/26 column
        "Coal": (30_081, 30_081), "Distillate Oil (No.2)": (2_408, 2_408),
        "Gas": (66_354, 66_354), "Nuclear": (30_549, 30_549), "Oil": (578, 578),
        "Solar": (1_337, 1_337), "Water": (5_365, 5_361), "Wind": (2_618, 1_676),
        "Battery/Hybrid": (14, 14), "Other": (911, 911),
        "Demand Response": (6_363, 6_342), "Aggregate Resource": (327, 273),
        "TOTAL_NO_EE": (146_905, 145_883), "Energy Efficiency": (1_460, 1_460),
    },
}

# 2024/25 read from BOTH vintages — the restatement, recorded not reconciled.
PUBLISHED_RESTATEMENTS = {
    "2024/2025 Gas cleared": ("2024/25 report Table 9", 83_243, "2027/28 report Table 6", 83_258),
    "2024/2025 Battery/Hybrid offered": ("2024/25 report Table 9 (Battery 36 + Hybrid 10)", 46, "2027/28 report Table 6", 36),
    "2024/2025 DR cleared": ("2024/25 report Table 6/9", 7_985.2, "2027/28 report Table 5", 7_992.7),
    "2024/2025 TOTAL_NO_EE cleared": ("2024/25 report Table 9", 172_961, "2027/28 report Table 6", 172_951),
}

# PUBLISHED RPM-only cleared, the D57/D61 comparator (Table 1/2 RTO row, via the
# in-repo auction-price CSV — read below, not hardcoded).

# Model fuel class -> published resource-type row.
MODEL_TO_PUBLISHED = {
    "coal": "Coal",
    "gas_cc": "Gas", "gas_ct": "Gas", "gas_st": "Gas",
    "nuclear": "Nuclear",
    "oil": "Distillate Oil (No.2)+Oil",
}


def _published_params() -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for row in csv.DictReader(DEMAND_CURVE_CSV.open()):
        if row["metric"] in {
            "reliability_requirement", "reliability_requirement_frr_adj",
            "ee_addback", "forecast_pool_requirement", "irm",
        }:
            out.setdefault(row["delivery_year"], {})[row["metric"]] = float(row["y_value"])
    return out


def _published_rpm_cleared() -> dict[str, tuple[float, float]]:
    out: dict[str, tuple[float, float]] = {}
    for row in csv.DictReader(AUCTION_PRICE_CSV.open()):
        if row["area"] == "RTO" and row["auction_round"] == "base_residual_auction" and row["cleared_mw"]:
            out[row["delivery_year"]] = (float(row["clearing_price"]), float(row["cleared_mw"]))
    return out


def _model_rows() -> dict[str, dict]:
    """Model census by fuel, from the committed arm-A ledgers."""
    out: dict[str, dict] = {}
    # VRE / storage pools: the D45-R control ledgers record them at year END, so
    # the pool ENTERING screen year Y is the base year's pool plus every
    # addition decided in 2021..Y-1.
    base = json.loads((CONTROL / "evolution_2021.json").read_text())
    pools = {"wind": base["wind_cap_mw"], "solar": base["solar_cap_mw"]}
    credits = base["renewable_credit_applied"]
    storage_firm = base["storage_firm_mw"]
    for screen_year, dy in sorted(SCREEN_TO_DY.items()):
        led = json.loads((ARM_A / f"evolution_{screen_year}.json").read_text())
        cc = led["capacity_clearing"]
        by_fuel: dict[str, dict[str, float]] = {}
        for _uid, fuel, offer, mw, cleared in cc["offer_stack"]:
            r = by_fuel.setdefault(fuel, {"n": 0, "accredited_mw": 0.0, "cleared_mw": 0.0})
            r["n"] += 1
            r["accredited_mw"] += mw
            if cleared:
                r["cleared_mw"] += mw
        pinned = {
            "demand_response": PJM_DR_SUPPLY_UCAP[dy],
            "firm_imports": PJM_FIRM_IMPORT_MW,
            "storage": storage_firm,
            "wind": pools["wind"] * credits["wind"],
            "solar": pools["solar"] * credits["solar"],
        }
        out[dy] = {
            "screen_year": screen_year,
            "requirement_mw": cc["requirement_mw"],
            "census_mw": cc["census_mw"],
            "census_position": cc["census_position"],
            "cleared_mw": cc["cleared_mw"],
            "cleared_position": cc["cleared_position"],
            "offered_mw": cc["offered_mw"],
            "price_takers_mw": cc["price_takers_mw"],
            "price_usd_per_mw_day": cc["price_usd_per_mw_day"],
            "how": cc["how"],
            "n_offers": cc["n_offers"],
            "n_uncleared": cc["n_uncleared"],
            "screen_peak_demand_mw": led["screen_peak_demand_mw"],
            "by_fuel": by_fuel,
            "price_taker_pinned": pinned,
            # Everything in Q_0 the committed artifacts do NOT pin: the hydro
            # pool (data/clean, gitignored) and biomass at its thermal basis.
            "price_taker_unpinned": cc["price_takers_mw"] - sum(pinned.values()),
            "vre_pools": dict(pools),
        }
        # Roll this year's additions into next year's entering pools.
        for add in led.get("renewable_additions") or []:
            if add["tech"] in pools:
                pools[add["tech"]] += float(add["mw"])
    return out



# --- the additive bucket decomposition (charter step 3) --------------------- #
# The identity, exact:
#     (pos_published - pos_model) * R_m  =  (C_p - C_m)  +  C_p * (R_m - R_p) / R_p
#                                            \_ SUPPLY _/    \___ REQUIREMENT ___/
# The SUPPLY leg is then split by resource type; the REQUIREMENT leg is split by
# its own operands.  Every row is a difference of two measured quantities; the
# row that cannot be attributed is carried as its own residual, at full
# magnitude (rule 14).
def buckets(dy: str, report: dict) -> dict:
    y = report["years"][dy]
    m, pub = y["model"], y["published"]["by_type"]
    p = y["published"]
    r_m, r_p = m["requirement_mw"], p["rto_requirement_mw"]
    c_m, c_p = m["census_mw"], p["rto_cleared_no_ee_mw"]
    scale = c_p / r_p  # converts a requirement-MW into a position-MW at R_m

    def _c(key: str) -> float:  # published CLEARED MW for a type row
        return float(pub[key][1])

    pt = m["price_taker_pinned"]
    stack = {f: v["accredited_mw"] for f, v in m["by_fuel"].items()}
    rows = [
        # (bucket, model MW, published MW, note)
        ("Coal", stack.get("coal", 0.0), _c("Coal"), "offer stack vs Table 9/6 Coal"),
        ("Gas (CC+CT+ST)", sum(stack.get(f, 0.0) for f in ("gas_cc", "gas_ct", "gas_st")),
         _c("Gas"), "offer stack vs Table 9/6 Gas"),
        ("Nuclear", stack.get("nuclear", 0.0), _c("Nuclear"), "offer stack vs Table 9/6 Nuclear"),
        ("Oil (distillate + residual)", stack.get("oil", 0.0),
         _c("Distillate Oil (No.2)") + _c("Oil"), "offer stack vs Table 9/6 two oil rows"),
        ("Wind", pt["wind"], _c("Wind"), "pool x ELCC credit vs Table 9/6 Wind"),
        ("Solar", pt["solar"], _c("Solar"), "pool x ELCC credit vs Table 9/6 Solar"),
        ("Demand response", pt["demand_response"], _c("Demand Response"),
         "DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO['PJM'] vs Table 9/6 DR"),
        ("Storage + hydro + biomass + screen-exempt thermal",
         pt["storage"] + m["price_taker_unpinned"],
         _c("Water") + _c("Battery/Hybrid") + _c("Other"),
         "model side NOT decomposable from committed artifacts (residual row)"),
        ("Firm imports (double-count adjustment)", pt["firm_imports"], 0.0,
         "model credits imports separately; PJM books them INSIDE its type rows"),
        ("Aggregate Resource", 0.0, _c("Aggregate Resource"),
         "PJM's mixed-type aggregation; the model has no analogue"),
    ]
    supply = [
        {"bucket": b, "model_mw": mm, "published_mw": pp, "gap_mw": pp - mm, "note": n}
        for b, mm, pp, n in rows
    ]
    supply_total = sum(r["gap_mw"] for r in supply)
    peak_delta = m["screen_peak_demand_mw"] - p["implied_pjm_peak_mw"]
    requirement = [{
        "bucket": "Peak-forecast difference x FPR",
        "model_mw": m["screen_peak_demand_mw"], "published_mw": p["implied_pjm_peak_mw"],
        "gap_mw": peak_delta * p["forecast_pool_requirement"] * scale,
        "note": (f"model screen peak {m['screen_peak_demand_mw']:,.1f} vs PJM implied peak "
                 f"{p['implied_pjm_peak_mw']:,.1f}; x FPR {p['forecast_pool_requirement']} "
                 f"x C_p/R_p {scale:.5f}"),
    }]
    requirement_total = sum(r["gap_mw"] for r in requirement)
    exact_supply = c_p - c_m
    exact_requirement = c_p * (r_m - r_p) / r_p
    return {
        "supply_rows": supply, "supply_total_mw": supply_total,
        "supply_exact_mw": exact_supply,
        "supply_unattributed_mw": exact_supply - supply_total,
        "requirement_rows": requirement, "requirement_total_mw": requirement_total,
        "requirement_exact_mw": exact_requirement,
        "requirement_unattributed_mw": exact_requirement - requirement_total,
        "gap_total_mw": exact_supply + exact_requirement,
        "gap_position_pts": (c_p / r_p - c_m / r_m) * 100.0,
        "published_offered_mw": p["rto_offered_no_ee_mw"],
        "model_census_vs_published_OFFERED_mw": c_m - p["rto_offered_no_ee_mw"],
    }


def main() -> dict:
    params = _published_params()
    rpm_cleared = _published_rpm_cleared()
    model = _model_rows()
    report: dict = {"instrument_check": {}, "years": {}, "restatements": PUBLISHED_RESTATEMENTS}

    # --- instrument check (charter step 1): the D62 screen's 2022/23 row ----- #
    m22 = model["2022/2023"]
    report["instrument_check"] = {
        "requirement_mw": {"expected": 155_048, "measured": m22["requirement_mw"]},
        "price_takers_mw": {"expected": 30_578, "measured": m22["price_takers_mw"]},
        "census_position": {"expected": 1.17019, "measured": m22["census_position"]},
        "passes": (
            abs(m22["requirement_mw"] - 155_048) < 1.0
            and abs(m22["price_takers_mw"] - 30_578) < 1.0
            and abs(m22["census_position"] - 1.17019) < 5e-6
        ),
    }

    for dy, m in model.items():
        p = params[dy]
        pub = PUBLISHED_RPM_PLUS_FRR[dy]
        r_rpm = p["reliability_requirement_frr_adj"] + p["ee_addback"]
        c_rpm = rpm_cleared[dy][1]
        r_rto = p["reliability_requirement"]
        c_rto_off, c_rto_clr = pub["TOTAL_NO_EE"]

        def _gap(c_p: float, r_p: float) -> dict:
            pos_p, pos_m = c_p / r_p, m["census_mw"] / m["requirement_mw"]
            # Exact additive split of (pos_p - pos_m) * R_m into a SUPPLY leg
            # (MW) and a REQUIREMENT leg (MW-equivalent at the model's R):
            #   (pos_p - pos_m) * R_m = (C_p - C_m) + C_p * (R_m - R_p) / R_p
            supply = c_p - m["census_mw"]
            requirement = c_p * (m["requirement_mw"] - r_p) / r_p
            return {
                "published_position": pos_p, "model_census_position": pos_m,
                "gap_position_pts": (pos_p - pos_m) * 100.0,
                "gap_mw_at_model_R": (pos_p - pos_m) * m["requirement_mw"],
                "leg_supply_mw": supply,
                "leg_requirement_mw": requirement,
                "identity_residual_mw": (pos_p - pos_m) * m["requirement_mw"] - supply - requirement,
                "published_supply_mw": c_p, "published_requirement_mw": r_p,
                "model_supply_mw": m["census_mw"], "model_requirement_mw": m["requirement_mw"],
            }

        # Model fuel classes -> published rows (accredited/offered MW).
        model_by_pub: dict[str, float] = {}
        for fuel, row in m["by_fuel"].items():
            model_by_pub[MODEL_TO_PUBLISHED[fuel]] = (
                model_by_pub.get(MODEL_TO_PUBLISHED[fuel], 0.0) + row["accredited_mw"]
            )
        pub_by_row = {
            "Coal": pub["Coal"][0], "Gas": pub["Gas"][0], "Nuclear": pub["Nuclear"][0],
            "Distillate Oil (No.2)+Oil": pub["Distillate Oil (No.2)"][0] + pub["Oil"][0],
        }
        thermal_rows = {
            k: {"model": model_by_pub.get(k, 0.0), "published_offered": v,
                "delta": model_by_pub.get(k, 0.0) - v}
            for k, v in pub_by_row.items()
        }
        nonthermal_published = (
            pub["Solar"][0] + pub["Water"][0] + pub["Wind"][0] + pub["Battery/Hybrid"][0]
            + pub["Other"][0] + pub["Demand Response"][0] + pub["Aggregate Resource"][0]
        )
        report["years"][dy] = {
            "model": m,
            "published": {
                "rpm_only_cleared_mw": c_rpm, "rpm_only_requirement_mw": r_rpm,
                "rpm_only_position": c_rpm / r_rpm, "rpm_only_price": rpm_cleared[dy][0],
                "rto_offered_no_ee_mw": c_rto_off, "rto_cleared_no_ee_mw": c_rto_clr,
                "rto_requirement_mw": r_rto, "rto_position": c_rto_clr / r_rto,
                "by_type": pub, "irm_pct": p["irm"],
                "forecast_pool_requirement": p["forecast_pool_requirement"],
                "frr_carveout_mw": p["reliability_requirement"] - p["reliability_requirement_frr_adj"],
                "ee_addback_mw": p["ee_addback"],
                "implied_pjm_peak_mw": p["reliability_requirement"] / p["forecast_pool_requirement"],
            },
            "frame_A_rpm_only": _gap(c_rpm, r_rpm),
            "frame_B_rto_wide": _gap(c_rto_clr, r_rto),
            "thermal_rows": thermal_rows,
            "nonthermal": {
                "model_price_takers_mw": m["price_takers_mw"],
                "published_nonthermal_offered_mw": nonthermal_published,
                "delta": m["price_takers_mw"] - nonthermal_published,
            },
        }
    for dy in report["years"]:
        report["years"][dy]["buckets"] = buckets(dy, report)
    return report


if __name__ == "__main__":
    out = main()
    dest = Path(__file__).with_suffix(".json")
    dest.write_text(json.dumps(out, indent=1, sort_keys=True))
    ic = out["instrument_check"]
    print("INSTRUMENT CHECK (2022/23):", "PASS" if ic["passes"] else "FAIL")
    for k, v in ic.items():
        if k != "passes":
            print(f"   {k:20} expected {v['expected']:>12,}  measured {v['measured']:>14,.5f}")
    print(f"\nwrote {dest.relative_to(REPO)}")
