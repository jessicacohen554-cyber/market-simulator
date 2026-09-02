"""D40 screen-grain consequence + leave-one-year-out score of the NEISO Net ICR
requirement lever (zero solves).

Reads the committed ``neiso-2023-2027-crossover-rcrepair`` evolution ledgers
and the committed published FCA record, and evaluates HEAD's OWN resolver
(``resolve_adequacy_requirement_mw``), position transform
(``curve_convention_position``) and vintage curves with the
``neiso_net_icr_requirement`` gate OFF and ON — pure config evaluation, no LP.
The D33 instrument (docs/handoffs/d33/position-decomposition-2026-09-02.py) is
the arithmetic this reproduces for the OFF arm; every published number cites
data/raw/capacity-market/demand-curve/neiso/neiso.csv +
data/raw/capacity-market/icr-ara/neiso/ara_requirement_values.csv.

Run from the repo root: ``uv run python docs/handoffs/d40/devintage-screen-grain-2026-09-02.py``.
"""

import json
import sys

sys.path.insert(0, "src")
from market_sim.config.capacity_market import (  # noqa: E402
    ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
    MARKET_DESIGN,
    NET_ICR_HOLD_LAST_RATIO_BY_ISO,
    NET_ICR_REQUIREMENT_MW_BY_ISO,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    evaluate_demand_curve,
    resolve_demand_curve_vintage,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.capacity_evolution.adequacy import (  # noqa: E402
    curve_convention_position,
)
from market_sim.model.capacity_evolution.retirements import (  # noqa: E402
    resolve_adequacy_requirement_mw,
)

BASE = "results/hindcast/neiso-2023-2027-crossover-rcrepair/NEISO/07e416f3f8072e7c"
OUT = "docs/handoffs/d40/devintage-screen-grain-rows-2026-09-02.json"

# Published record (committed rows; $ = $/kW-mo). Real position = cleared/Net
# ICR, the FCA's own (raw, DR-in) convention.
REAL = {
    2023: dict(fca=14, net_icr=32490.0, cleared=33956.0, price_mo=2.001),
    2024: dict(fca=15, net_icr=33270.0, cleared=34621.0, price_mo=2.611),
    2025: dict(fca=16, net_icr=31645.0, cleared=32810.0, price_mo=2.591),
    2026: dict(fca=17, net_icr=30305.0, cleared=31370.0, price_mo=2.590),
    2027: dict(fca=18, net_icr=30550.0, cleared=31556.0, price_mo=3.580),
}
TRAIN = (2023, 2024, 2025)  # rule 22: the only years a verdict may be fitted on

ISO = "NEISO"
F_DR = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO[ISO]
COMPOSITE = (1.0 - F_DR) * (1.0 + PLANNING_RESERVE_MARGIN_BY_ISO[ISO])
HOLD = NET_ICR_HOLD_LAST_RATIO_BY_ISO[ISO]
md = MARKET_DESIGN[ISO]
cfg_off = ScenarioConfig(iso=ISO, mode="forecast", hindcast=True)
cfg_on = ScenarioConfig(
    iso=ISO, mode="forecast", hindcast=True, neiso_net_icr_requirement=True
)
assert cfg_on.neiso_net_icr_requirement and not cfg_off.neiso_net_icr_requirement


def vintage_pay(year: int, pos: float) -> float:
    """$/kW-yr the HEAD vintage curve pays at reserve position ``pos``."""
    v = resolve_demand_curve_vintage(ISO, year)
    curve = v.demand_curve if v is not None else md.demand_curve
    anchor = (
        v.net_cone_curve_per_kw_yr if v is not None else md.net_cone_curve_per_kw_yr
    )
    return evaluate_demand_curve(curve, pos) * anchor


print(f"f_DR={F_DR:.6f}  composite={COMPOSITE:.6f}  hold ratio={HOLD:.6f}")
print("Net ICR series:", NET_ICR_REQUIREMENT_MW_BY_ISO[ISO])

led = {y: json.load(open(f"{BASE}/evolution_{y}.json")) for y in range(2023, 2028)}
rows = []
prev_post = None
for y in range(2023, 2028):
    d = led[y]
    peak = float(d["peak_demand_mw"])
    firm_post = peak * (1.0 + float(d["reserve_margin"]))
    firm_enter = prev_post if prev_post is not None else firm_post
    prev_post = firm_post
    r = REAL[y]
    price_real = r["price_mo"] * 12.0
    pos_real = r["cleared"] / r["net_icr"]

    req_off = resolve_adequacy_requirement_mw(cfg_off, ISO, peak, y)
    req_on = resolve_adequacy_requirement_mw(cfg_on, ISO, peak, y)
    assert abs(req_off - peak * COMPOSITE) < 1e-6
    assert abs(req_on - r["net_icr"] * (1.0 - F_DR)) < 1e-6

    # Positions. OFF = HEAD (net convention, what D28/D33 reported and what
    # the curve was evaluated at); ON = the armed lever (R-A denominator + the
    # R-B raw-convention transform, i.e. exactly what capacity_reserve_position
    # would return). Both on the post-evolution fleet (comparable to the real
    # cleared quantity in the delivery year) and on the entering fleet (what
    # the year's screens actually priced).
    pos_off_post = curve_convention_position(cfg_off, ISO, firm_post / req_off)
    pos_on_post = curve_convention_position(cfg_on, ISO, firm_post / req_on)
    pos_off_enter = curve_convention_position(cfg_off, ISO, firm_enter / req_off)
    pos_on_enter = curve_convention_position(cfg_on, ISO, firm_enter / req_on)
    # R-A alone (net convention, no R-B), for the decomposition.
    pos_ra_only_post = firm_post / req_on

    # Floor exit budget: firm the floor lets exit before it binds, on the
    # entering fleet (negative = the floor already binds at entry).
    budget_off = firm_enter - req_off
    budget_on = firm_enter - req_on
    binds_off_post = firm_post < req_off
    binds_on_post = firm_post < req_on

    rows.append(
        dict(
            y=y,
            fca=r["fca"],
            peak=peak,
            firm_enter=firm_enter,
            firm_post=firm_post,
            req_off=req_off,
            req_on=req_on,
            req_delta=req_on - req_off,
            net_icr=r["net_icr"],
            cleared=r["cleared"],
            pos_real=pos_real,
            pos_off_post=pos_off_post,
            pos_on_post=pos_on_post,
            pos_ra_only_post=pos_ra_only_post,
            pos_off_enter=pos_off_enter,
            pos_on_enter=pos_on_enter,
            gap_off_post=pos_off_post - pos_real,
            gap_on_post=pos_on_post - pos_real,
            gap_off_enter=pos_off_enter - pos_real,
            gap_on_enter=pos_on_enter - pos_real,
            pay_off_post=vintage_pay(y, pos_off_post),
            pay_on_post=vintage_pay(y, pos_on_post),
            pay_off_enter=vintage_pay(y, pos_off_enter),
            pay_on_enter=vintage_pay(y, pos_on_enter),
            pay_real=price_real,
            budget_off=budget_off,
            budget_on=budget_on,
            floor_binds_off_post=binds_off_post,
            floor_binds_on_post=binds_on_post,
        )
    )

print("\nREQUIREMENT (net convention, MW)")
print("yr FCA |  peak   | req OFF  req ON   delta   | NetICR  | firmEnter firmPost")
for r in rows:
    print(
        f"{r['y']} {r['fca']:2d} | {r['peak']:7.0f} | {r['req_off']:7.0f} {r['req_on']:7.0f} "
        f"{r['req_delta']:+7.0f} | {r['net_icr']:7.0f} | {r['firm_enter']:8.0f} {r['firm_post']:8.0f}"
    )

print("\nPOSITIONS vs REAL (post-evolution fleet; ON is on the curve's raw convention)")
print(
    "yr FCA | real   | OFF    gap(pts) | ON     gap(pts) | R-A only(net) | ENTER: OFF gap  ON gap"
)
for r in rows:
    print(
        f"{r['y']} {r['fca']:2d} | {r['pos_real']:.4f} | {r['pos_off_post']:.4f} {r['gap_off_post'] * 100:+6.2f} | "
        f"{r['pos_on_post']:.4f} {r['gap_on_post'] * 100:+6.2f} | {r['pos_ra_only_post']:.4f} | "
        f"{r['pos_off_enter']:.4f} {r['gap_off_enter'] * 100:+6.2f}  {r['pos_on_enter']:.4f} {r['gap_on_enter'] * 100:+6.2f}"
    )

print(
    "\nCAPACITY REVENUE $/kW-yr (HEAD vintage curves) — post fleet / entering fleet / real"
)
print("yr FCA | OFF post  ON post | OFF enter ON enter | real")
for r in rows:
    print(
        f"{r['y']} {r['fca']:2d} | {r['pay_off_post']:8.2f} {r['pay_on_post']:8.2f} | "
        f"{r['pay_off_enter']:8.2f} {r['pay_on_enter']:8.2f} | {r['pay_real']:6.2f}"
    )

print(
    "\nFLOOR EXIT BUDGET at entry (firm_enter − requirement, MW) and binding on the as-solved post fleet"
)
for r in rows:
    print(
        f"{r['y']}: budget OFF {r['budget_off']:+8.0f}  ON {r['budget_on']:+8.0f}  "
        f"(ratio {r['budget_on'] / r['budget_off'] if r['budget_off'] else float('nan'):.2f}); "
        f"floor binds post-fleet: OFF {r['floor_binds_off_post']}  ON {r['floor_binds_on_post']}"
    )

# Hold-last edge: the requirement ratio at 2027 (last CCP, absolute) vs 2028
# (held ratio) at the 2027 ledger peak, and vs the composite.
peak27 = rows[-1]["peak"]
req28_on = resolve_adequacy_requirement_mw(cfg_on, ISO, peak27, 2028)
req28_off = resolve_adequacy_requirement_mw(cfg_off, ISO, peak27, 2028)
print(
    f"\nHOLD-LAST EDGE at the 2027 ledger peak {peak27:.0f}: 2027 ON {rows[-1]['req_on']:.0f} → "
    f"2028 ON (held ratio) {req28_on:.0f} ({(req28_on / rows[-1]['req_on'] - 1) * 100:+.2f} %); "
    f"2028 OFF (composite) {req28_off:.0f}; ON/OFF beyond table = {req28_on / req28_off:.5f}"
)


# ---- Leave-one-year-out (rule 22) over the training years 2023-2025 -------
# The lever carries ZERO fitted parameters, so a fold's "training" decision is
# the sign test on the two training years — does arming reduce the absolute
# position error (and the absolute capacity-revenue error) in both? — and the
# held-out year is then scored on the same criterion. In-sample gain with
# held-out degradation is overfitting, not skill.
def better(r, key_off, key_on, real_key=None):
    off = abs(r[key_off] - (r[real_key] if real_key else 0.0))
    on = abs(r[key_on] - (r[real_key] if real_key else 0.0))
    return on < off, off, on


loyo = []
by_year = {r["y"]: r for r in rows}
for metric, k_off, k_on, real_key in (
    ("position_post", "pos_off_post", "pos_on_post", "pos_real"),
    ("position_enter", "pos_off_enter", "pos_on_enter", "pos_real"),
    ("capacity_revenue_post", "pay_off_post", "pay_on_post", "pay_real"),
    ("capacity_revenue_enter", "pay_off_enter", "pay_on_enter", "pay_real"),
):
    for held in TRAIN:
        train = [t for t in TRAIN if t != held]
        train_ok = all(better(by_year[t], k_off, k_on, real_key)[0] for t in train)
        h_ok, h_off, h_on = better(by_year[held], k_off, k_on, real_key)
        loyo.append(
            dict(
                metric=metric,
                held_out=held,
                train=train,
                train_arms=train_ok,
                held_out_improves=h_ok,
                held_out_abs_err_off=h_off,
                held_out_abs_err_on=h_on,
                fold_pass=(not train_ok) or h_ok,
            )
        )

print(
    "\nLEAVE-ONE-YEAR-OUT (train 2023-2025; fold passes iff a train-armed lever also improves the held-out year)"
)
print("metric                 held | train arms | held-out |err| OFF → ON | fold")
for f in loyo:
    print(
        f"{f['metric']:22s} {f['held_out']} | {str(f['train_arms']):5s}      | "
        f"{f['held_out_abs_err_off']:8.4f} → {f['held_out_abs_err_on']:8.4f} | {'PASS' if f['fold_pass'] else 'FAIL'}"
        + ("" if f["held_out_improves"] else "  (held-out DEGRADES)")
    )
n_fail = sum(not f["fold_pass"] for f in loyo)
print(f"\nfolds: {len(loyo)}  failing: {n_fail}")

json.dump(
    dict(
        f_dr=F_DR,
        composite=COMPOSITE,
        hold_ratio=HOLD,
        net_icr_series=NET_ICR_REQUIREMENT_MW_BY_ISO[ISO],
        rows=rows,
        hold_last_edge=dict(
            peak_2027=peak27,
            req_2027_on=rows[-1]["req_on"],
            req_2028_on=req28_on,
            req_2028_off=req28_off,
        ),
        loyo=loyo,
        loyo_failing_folds=n_fail,
        cache_keys=dict(off=cfg_off.cache_key(), on=cfg_on.cache_key()),
        bundle=BASE,
    ),
    open(OUT, "w"),
    indent=1,
)
print("rows dumped to", OUT)
