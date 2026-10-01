"""capx D37 pre-declaration instrument: project the D40 Net ICR lever onto the
committed NEISO **T1-H** baseline ledgers (2021-2025), which are a DIFFERENT
fleet trajectory from the 2023-2027 crossover ledgers D40 measured on.

ZERO solves. Every OFF row is read from the committed
``neiso-2021-2025-realized-mystic-rescore`` evolution ledgers; every ON row is
computed by evaluating HEAD's own committed resolvers on those ledgers. The
output is the OFF baseline + the artifact-contaminated ON bound that the D37
pre-declaration's predictions are stated against.
"""

from __future__ import annotations

import json
from pathlib import Path

from market_sim.config.capacity_market import (
    ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
    NET_ICR_REQUIREMENT_MW_BY_ISO,
    evaluate_demand_curve,
    resolve_demand_curve_vintage,
)
from market_sim.config.constants import PLANNING_RESERVE_MARGIN_BY_ISO

REPO = Path(__file__).resolve().parents[3]
BUNDLE = (
    REPO
    / "results/hindcast/neiso-2021-2025-realized-mystic-rescore/NEISO/e118e887b306da37"
)

F_DR = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]
PRM = PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"]
COMPOSITE = (1.0 - F_DR) * (1.0 + PRM)  # HEAD's OFF requirement factor
NET_ICR = NET_ICR_REQUIREMENT_MW_BY_ISO["NEISO"]

# Real FCA rows (committed R2 intake, quoted in D33 §2 / D40 §2).
REAL = {  # year -> (cleared MW, Net ICR MW, clearing $/kW-yr)
    2023: (33956.0, 32490.0, 24.01),
    2024: (34621.0, 33270.0, 31.33),
    2025: (32810.0, 31645.0, 31.09),
}


def ccp(year: int) -> str:
    return f"{year}/{year + 1}"


def rows():
    out = []
    for year in (2021, 2023, 2024, 2025):
        led = json.loads((BUNDLE / f"evolution_{year}.json").read_text())
        peak = led["peak_demand_mw"]
        rm = led["reserve_margin"]
        firm = peak * (1.0 + rm)  # post-evolution accredited firm (D33 §2 identity)
        req_off = peak * COMPOSITE
        net_icr = NET_ICR.get(ccp(year))
        req_on = net_icr * (1.0 - F_DR) if net_icr else None
        pos_off_net = firm / req_off
        pos_on_net = firm / req_on if req_on else None
        # R-B: raw-convention position = f + (1 - f) * pos_net
        pos_off_raw = F_DR + (1.0 - F_DR) * pos_off_net
        pos_on_raw = F_DR + (1.0 - F_DR) * pos_on_net if pos_on_net else None
        real = REAL.get(year)
        pos_real = real[0] / real[1] if real else None
        out.append(
            dict(
                year=year,
                peak=peak,
                reserve_margin=rm,
                firm=firm,
                req_off=req_off,
                req_on=req_on,
                d_req=(req_on - req_off) if req_on else None,
                net_icr=net_icr,
                pos_off_net=pos_off_net,
                pos_off_raw=pos_off_raw,
                pos_on_raw=pos_on_raw,
                pos_real=pos_real,
                budget_off=firm - req_off,
                budget_on=(firm - req_on) if req_on else None,
                thermal_before=sum(led.get("fleet_by_fuel_before", {}).values()),
                thermal_after=sum(led.get("fleet_by_fuel_after", {}).values()),
            )
        )
    return out


def price(iso: str, year: int, pos: float) -> float:
    """Capacity revenue $/kW-yr at a raw-convention position, HEAD's own curves."""
    vintage = resolve_demand_curve_vintage(iso, year)
    frac = evaluate_demand_curve(vintage.demand_curve, pos)
    return frac * vintage.net_cone_curve_per_kw_yr


if __name__ == "__main__":
    # Self-check (D33 §2 cross-validation): HEAD's curves evaluated at the REAL
    # FCA positions must reproduce the real clearing prices to the cent.
    for _y, (_cl, _icr, _px) in REAL.items():
        _got = price("NEISO", _y, _cl / _icr)
        assert abs(_got - _px) < 0.02, (_y, _got, _px)
    print("self-check OK: HEAD curves reproduce the real FCA clearing prices at the real positions")

    data = rows()
    print(f"HEAD OFF composite factor = {COMPOSITE:.6f}  (f_DR={F_DR:.8f}, PRM={PRM:.8f})")
    print()
    hdr = (
        f"{'yr':>5} {'peak':>9} {'rm':>9} {'firm':>9} {'reqOFF':>9} {'reqON':>9} "
        f"{'dReq':>8} {'NetICR':>8} {'posOFFraw':>10} {'posONraw':>9} {'real':>8} "
        f"{'budOFF':>9} {'budON':>9}"
    )
    print(hdr)
    for r in data:
        f = lambda v, w=9, p=1: (f"{v:>{w},.{p}f}" if v is not None else " " * w)
        print(
            f"{r['year']:>5} {f(r['peak'])} {r['reserve_margin']:>9.6f} {f(r['firm'])} "
            f"{f(r['req_off'])} {f(r['req_on'])} {f(r['d_req'],8)} {f(r['net_icr'],8,0)} "
            f"{f(r['pos_off_raw'],10,4)} {f(r['pos_on_raw'],9,4)} {f(r['pos_real'],8,4)} "
            f"{f(r['budget_off'])} {f(r['budget_on'])}"
        )
    print()
    print(f"{'yr':>5} {'gapOFF(pts)':>12} {'gapON(pts)':>11} {'$OFF':>8} {'$ON':>8} {'$real':>8}")
    for r in data:
        if r["pos_real"] is None:
            continue
        g_off = 100.0 * (r["pos_off_raw"] - r["pos_real"])
        g_on = 100.0 * (r["pos_on_raw"] - r["pos_real"])
        p_off = price("NEISO", r["year"], r["pos_off_raw"])
        p_on = price("NEISO", r["year"], r["pos_on_raw"])
        print(
            f"{r['year']:>5} {g_off:>+12.2f} {g_on:>+11.2f} {p_off:>8.2f} {p_on:>8.2f} "
            f"{REAL[r['year']][2]:>8.2f}"
        )
    (Path(__file__).with_suffix(".json")).write_text(json.dumps(data, indent=1))
