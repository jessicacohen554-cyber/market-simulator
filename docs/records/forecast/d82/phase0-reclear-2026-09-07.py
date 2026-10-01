"""capx D82 design read — zero-LP re-clear of the REGISTERED pjm-t1h stacks (key fb16fda2ddb0a94a).

Read-only instrument. It answers ONE question for the design read: under HEAD's own
requirement, is the CT plateau uncleared in any armable posture, and what per-class E&AS
would put each at-bar class AT the clearing price? Scenarios re-express every committed
offer through the code's own ``clear_capacity_supply_stack`` + ``capacity_supply_curve``:

* S0   — the committed stack as-is (reproduction gate; D57 / D61 / pjm-eas form).
* S62  — capx D62 posture: PJM's published default gross ACR as the bar (Manual 18 Rev 62
         §5.4.8.4(B), through-2025/26 column, nameplate) + the reactive offset
         ($2,199/MW-yr) inside E&AS. Steam Oil & Gas reads the first published value
         ($64/MW-day) — D62's fixed vintage rule.
* S74  — S62 + capx D74: Steam Oil & Gas leaves the stack and enters Q_0 at $0.

E&AS per unit is recovered from the committed offer exactly as D61 §1.1 did:
``EAS = bar − offer × 365 × af / 1000`` ($/kW-yr nameplate), censored at the bar when the
committed offer is 0 (such a unit stays at 0 under any LOWER bar; nuclear's HIGHER published
bar is treated as censored too, per FINDING-capx-d62 §9 item 4). ``af`` is the UCAP class
fraction the committed at-bar offers imply (1 − EFORd; verified: 21000/365/61.2066 = 0.9400).
Nothing here is an input to anything; no solve, no config, no field.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict

sys.path.insert(0, "src")
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.capacity_evolution.adequacy import (  # noqa: E402
    CapacityOffer,
    capacity_supply_curve,
    clear_capacity_supply_stack,
)

BUNDLE = (
    "results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm/PJM/fb16fda2ddb0a94a"
)
CFG = ScenarioConfig(iso="PJM", mode="forecast", hindcast=True)
# ATB going-forward bars the registered run screened on ($/kW-yr nameplate; ledger rows
# ``going_forward_bar_per_kw_yr`` = 35.0 gas_st / 30.0 gas_cc; D61 §1.1 for the rest).
ATB = {
    "coal": 58.5,
    "gas_cc": 30.0,
    "gas_ct": 21.0,
    "gas_st": 35.0,
    "oil": 25.0,
    "nuclear": 130.0,
}
# Published default gross ACR, $/MW-day nameplate → $/kW-yr (pjm.csv, through-2025/26 column;
# Steam Oil & Gas: D62's first_published rule = the 2026/27 value 64; nuclear: multi-unit 445).
PUB_MWDAY = {
    "coal": 80.0,
    "gas_cc": 56.0,
    "gas_ct": 50.0,
    "gas_st": 64.0,
    "oil": 64.0,
    "nuclear": 445.0,
}
PUB = {k: v * 365.0 / 1000.0 for k, v in PUB_MWDAY.items()}
REACTIVE_KW = 2199.0 / 1000.0  # $/kW-yr, pjm.csv reactive_offset row
# UCAP class accreditation fraction implied by the committed at-bar offers (2022–2024 screens).
AF = {
    "gas_ct": 0.94,
    "gas_st": 0.93,
    "oil": 0.90,
    "coal": 0.92,
    "gas_cc": 0.95,
    "nuclear": 0.97,
}
PUBLISHED_ROW = {
    2022: (50.00, 1.0510),
    2023: (34.13, 1.0552),
    2024: (28.92, 1.0555),
    2025: (269.92, 1.0049),
}


def _offer(uid, fuel, offer, a_mw):
    if hasattr(CapacityOffer, "_fields"):
        vals = {
            "unit_id": uid,
            "fuel": fuel,
            "offer_usd_per_mw_day": offer,
            "accredited_mw": a_mw,
            "firm_mw": a_mw,
            "pmax_mw": a_mw,
            "nameplate_mw": a_mw,
        }
        return CapacityOffer(*[vals.get(f, 0.0) for f in CapacityOffer._fields])
    return (uid, fuel, offer, a_mw, a_mw)


def reexpress(fuel, offer, af, bar_new, extra_eas):
    """Committed ATB offer → offer under (bar_new, EAS + extra_eas); censored at 0."""
    if offer <= 0.0:
        return 0.0
    eas = ATB[fuel] - offer * 365.0 * af / 1000.0
    return max(0.0, bar_new - (eas + extra_eas)) * 1000.0 / (af * 365.0)


def run(year, scenario):
    d = json.load(open(f"{BUNDLE}/evolution_{year}.json"))
    cc = d["capacity_clearing"]
    curve = capacity_supply_curve(CFG, "PJM", year)
    q0 = cc["price_takers_mw"]
    offers, raw = [], []
    # 2025 screens on the ELCC-class basis: recover each class's fraction from its
    # at-bar (max) committed offer; a class with no positive offer (nuclear) keeps
    # its UCAP fraction — it is censored at 0 in every scenario anyway.
    af_by_fuel = dict(AF)
    if year > 2024:
        for fuel in AF:
            mx = max([r[2] for r in cc["offer_stack"] if r[1] == fuel] or [0.0])
            if mx > 0.0:
                af_by_fuel[fuel] = ATB[fuel] * 1000.0 / 365.0 / mx
    for uid, fuel, offer, a_mw, _cleared in cc["offer_stack"]:
        af = af_by_fuel[fuel]
        if scenario == "S0":
            o = offer
        else:
            if scenario == "S74" and fuel in ("gas_st", "oil"):
                q0 += a_mw
                continue
            o = reexpress(fuel, offer, af, PUB[fuel], REACTIVE_KW)
        offers.append(_offer(uid, fuel, o, a_mw))
        raw.append((uid, fuel, o, a_mw, af))
    c = clear_capacity_supply_stack(offers, q0, cc["requirement_mw"], curve)
    p = c.price_usd_per_mw_day
    by = defaultdict(
        lambda: {"n": 0, "mw": 0.0, "unc_mw": 0.0, "max_offer": 0.0, "at_max": 0.0}
    )
    for _uid, fuel, o, a_mw, _af in raw:
        b = by[fuel]
        b["n"] += 1
        b["mw"] += a_mw
        if o > p + 1e-9:
            b["unc_mw"] += a_mw
        b["max_offer"] = max(b["max_offer"], o)
    for _uid, fuel, o, a_mw, _af in raw:
        if abs(o - by[fuel]["max_offer"]) < 1e-6:
            by[fuel]["at_max"] += a_mw
    # E&AS that puts a class's top-of-plateau offer AT the price ($/kW-yr nameplate; ≤0 = already clears)
    need = {}
    for fuel, b in by.items():
        need[fuel] = round((b["max_offer"] - p) * 365.0 * af_by_fuel[fuel] / 1000.0, 2)
    pub_p, pub_pos = PUBLISHED_ROW[year]
    # The marginal plateau: every offer AT the price, split cleared / uncleared from the
    # clearing's own cleared_mw (Q_0 + offers strictly below + the cleared part of the tie).
    total_supply = q0 + sum(a for _u, _f, _o, a, _af in raw)
    below = sum(a for _u, _f, o, a, _af in raw if o < p - 1e-9)
    at_price = defaultdict(float)
    for _u, fuel, o, a, _af in raw:
        if abs(o - p) <= 1e-9:
            at_price[fuel] += a
    at_price_total = sum(at_price.values())
    plateau_cleared = max(0.0, min(at_price_total, c.cleared_mw - q0 - below))
    return {
        "total_supply_mw": total_supply,
        "cleared_mw": c.cleared_mw,
        "uncleared_total_mw": total_supply - c.cleared_mw,
        "marginal_plateau": {
            "mw_at_price_by_fuel": {
                k: round(v, 1) for k, v in sorted(at_price.items())
            },
            "mw_at_price": round(at_price_total, 1),
            "cleared_part_mw": round(plateau_cleared, 1),
            "uncleared_part_mw": round(at_price_total - plateau_cleared, 1),
        },
        "year": year,
        "scenario": scenario,
        "committed_price": cc["price_usd_per_mw_day"],
        "committed_position": cc["cleared_position"],
        "price": p,
        "ratio_vs_published": p / pub_p,
        "position": c.cleared_position,
        "d_position_pt": 100.0 * (c.cleared_position - pub_pos),
        "how": c.how,
        "marginal_unit": getattr(c, "marginal_unit", None),
        "requirement_mw": cc["requirement_mw"],
        "price_takers_mw": q0,
        "n_offers": len(offers),
        "by_fuel": {
            k: {
                kk: round(vv, 4) if isinstance(vv, float) else vv
                for kk, vv in v.items()
            }
            for k, v in sorted(by.items())
        },
        "eas_to_reach_price_kw_yr": dict(sorted(need.items())),
    }


if __name__ == "__main__":
    out = []
    for year in (2022, 2023, 2024, 2025):
        for sc in ("S0", "S62", "S74"):
            r = run(year, sc)
            out.append(r)
            print(
                f"{year} {sc:3s} price {r['price']:8.4f} (committed {r['committed_price']:8.4f}) "
                f"ratio {r['ratio_vs_published']:.3f} pos {r['position']:.4f} ({r['d_position_pt']:+.2f} pt) "
                f"how={r['how']} marginal={r['marginal_unit']}"
            )
            mp = r["marginal_plateau"]
            print(
                f"      supply {r['total_supply_mw']:.1f} cleared {r['cleared_mw']:.1f} uncleared {r['uncleared_total_mw']:.1f} | "
                f"at-price plateau {mp['mw_at_price_by_fuel']} = {mp['mw_at_price']} MW: cleared {mp['cleared_part_mw']} / uncleared {mp['uncleared_part_mw']}"
            )
            for f, b in r["by_fuel"].items():
                print(
                    f"      {f:8s} n={b['n']:4d} firm={b['mw']:9.1f} uncleared={b['unc_mw']:9.1f} "
                    f"max_offer={b['max_offer']:8.4f} at_max_mw={b['at_max']:9.1f} "
                    f"E&AS-to-price={r['eas_to_reach_price_kw_yr'][f]:+.2f} $/kW-yr"
                )
    json.dump(
        out, open("docs/handoffs/d82/phase0-reclear-2026-09-07.json", "w"), indent=1
    )
