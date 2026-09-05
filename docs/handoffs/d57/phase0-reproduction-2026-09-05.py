"""capx D57 Phase 0: reproduce the D54 pre-declaration instrument with the CODE's clearing function.

Zero solves. Feeds the SAME stack the committed D54 instruments built (per-unit offers from the
committed T1-H ledgers' ``pipeline_events`` rows on the D48 class-EFORd basis / HEAD's ELCC basis,
``Q_0`` = the D48 position instrument's firm minus the failing firm, ``R`` = its requirement) to
``market_sim.model.capacity_evolution.adequacy.clear_capacity_supply_stack`` with the demand side
built by ``capacity_supply_curve`` on a hindcast PJM ScenarioConfig (the registry vintage curves
through the SAME MarketDesign.capacity_price_per_firm_mw_yr seam the solve prices), and compares
the price / cleared position per delivery year against the committed
``docs/handoffs/d54/clearing-predecl[-headbasis]-2026-09-05.json`` outputs.

STOP 1 (DESIGN-capx-d54 §7.7 item 1): |Δprice| > $1/MW-day or |Δposition| > 0.1 pt in any year.
Design invariant I5. The published BRA record is printed beside as a VALIDATION OBSERVABLE only.

Run from the repo root: ``uv run python docs/handoffs/d57/phase0-reproduction-2026-09-05.py [out.json]``
"""

import glob
import json
import sys

sys.path.insert(0, "src")
from market_sim.config.capacity_market import THERMAL_ELCC_CLASS_RATING_BY_ISO
from market_sim.config.constants import EFORD
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.capacity_evolution.adequacy import (
    capacity_supply_curve,
    clear_capacity_supply_stack,
)

D48 = json.load(open("docs/handoffs/d48/devintage-positions-d45r-2026-09-04.json"))[
    "years"
]
PUB = {
    r["delivery_year"]: r
    for r in json.load(open("docs/handoffs/d45/published-positions-2026-09-03.json"))[
        "pjm"
    ]
}
DY = {2022: "2022/2023", 2023: "2023/2024", 2024: "2024/2025", 2025: "2025/2026"}
ELCC = THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"]
BUNDLES = (
    ("results/hindcast/pjm-2021-2025-realized-t1h-d45r", "control pjm-t1h"),
    (
        "results/hindcast/pjm-2021-2025-realized-t1h-d48-devintage",
        "arm pjm-t1h-d48-devintage",
    ),
)
BASES = {
    "d48": ("BOTH", "docs/handoffs/d54/clearing-predecl-2026-09-05.json"),
    "head": ("OFF", "docs/handoffs/d54/clearing-predecl-headbasis-2026-09-05.json"),
}
TOL_PRICE, TOL_POS_PTS = 1.0, 0.1
# The curve-gate-ON hindcast config: capacity_market_clearing_by_iso ships PJM True, so
# capacity_supply_curve prices the registry vintage curve exactly as the solve does.
CFG = ScenarioConfig(iso="PJM", mode="forecast", hindcast=True)


def accr(fuel, year, basis):
    """The instrument's per-class accreditation: UCAP through DY 2024/25 on the D48 basis,
    ELCC class from 2025/26; ELCC class in every year on HEAD's basis."""
    ucap = 1.0 - EFORD.get(fuel, 0.08)
    if basis == "d48":
        return ucap if year <= 2024 else ELCC.get(fuel, ucap)
    return ELCC.get(fuel, ucap)


out, stops = {}, []
for basis, (arm_key, predecl_path) in BASES.items():
    predecl = json.load(open(predecl_path))
    print(
        f"\n===== basis {basis} (D48 instrument arm {arm_key}; reference {predecl_path}) ====="
    )
    out[basis] = {}
    for bundle, label in BUNDLES:
        out[basis][label] = {}
        ref_rows = predecl[label]
        for year in (2022, 2023, 2024, 2025):
            led = json.load(open(glob.glob(f"{bundle}/PJM/*/evolution_{year}.json")[0]))
            rows = [
                e
                for e in (led.get("pipeline_events") or [])
                if e["event"] in ("decided", "entry_capped", "re_confirmed")
            ]
            base = D48[str(year)]["arms"][arm_key]
            req, firm = base["requirement_mw"], base["firm_mw"]
            curve = capacity_supply_curve(CFG, "PJM", year)
            offers, fail_firm = [], 0.0
            for e in rows:
                a = accr(e["fuel"], year, basis)
                fmw = e["mw"] * a
                fail_firm += fmw
                eas = e["net_revenue_usd"] - e.get("capacity_revenue_usd", 0.0)
                offers.append(
                    (
                        e["unit_id"],
                        e["fuel"],
                        max(0.0, e["going_forward_cost_usd"] - eas) / (fmw * 365.0)
                        if fmw > 0
                        else 0.0,
                        fmw,
                        e["mw"],
                    )
                )
            q0 = firm - fail_firm
            c = clear_capacity_supply_stack(offers, q0, req, curve)
            ref = ref_rows[str(year)]
            ref_price, ref_pos = ref["price_mw_day"], ref["position"]
            d_price, d_pos = (
                c.price_usd_per_mw_day - ref_price,
                100.0 * (c.cleared_position - ref_pos),
            )
            hit = abs(d_price) <= TOL_PRICE and abs(d_pos) <= TOL_POS_PTS
            if not hit:
                stops.append((basis, label, year, d_price, d_pos))
            pub = PUB[DY[year]]
            pub_day = pub["real_price_kw_yr"] * 1000.0 / 365.0
            print(
                f"{label:28s} {year} DY {DY[year]}: CODE price {c.price_usd_per_mw_day:7.2f} $/MW-day  pos {c.cleared_position:.4f}"
                f"  [{c.how}]  | INSTRUMENT {ref_price:7.2f} / {ref_pos:.4f}  Δ {d_price:+.3f} $ / {d_pos:+.3f} pt  -> {'HIT' if hit else 'STOP-1'}"
                f"  | published {pub_day:6.2f} at {pub['pos_cleared']:.4f}  | uncleared firm "
                + ", ".join(
                    f"{k} {v:,.0f}"
                    for k, v in sorted(c.uncleared_firm_mw_by_fuel.items())
                )
            )
            out[basis][label][year] = {
                "code": {
                    "price_mw_day": c.price_usd_per_mw_day,
                    "cleared_mw": c.cleared_mw,
                    "position": c.cleared_position,
                    "how": c.how,
                    "price_takers_mw": c.price_takers_mw,
                    "n_offers": c.n_offers,
                    "n_uncleared": c.n_uncleared,
                    "uncleared_firm_by_fuel": c.uncleared_firm_mw_by_fuel,
                    "marginal_unit": c.marginal_unit_id,
                },
                "instrument": {
                    "price_mw_day": ref_price,
                    "position": ref_pos,
                    "how": ref.get("how"),
                },
                "delta": {"price_mw_day": d_price, "position_pts": d_pos, "hit": hit},
                "published": {
                    "price_mw_day": pub_day,
                    "pos_cleared": pub["pos_cleared"],
                },
            }
print(
    "\nSTOP-1 tolerance: |Δprice| <= $1/MW-day and |Δposition| <= 0.1 pt in every year."
)
print(
    "RESULT:",
    "ALL HIT — the code's clearing reproduces the instrument (I5)"
    if not stops
    else f"STOP-1: {stops}",
)
if len(sys.argv) > 1:
    json.dump(
        {
            "tolerance": {"price_mw_day": TOL_PRICE, "position_pts": TOL_POS_PTS},
            "stops": stops,
            "years": out,
        },
        open(sys.argv[1], "w"),
        indent=1,
    )
sys.exit(1 if stops else 0)
