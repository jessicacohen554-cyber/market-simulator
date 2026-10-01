"""capx D74 PHASE 0 (zero LP, a STOP gate) -- the no-default-cap price-taker
convention for PJM's "Steam Oil & Gas" class, re-cleared through the CODE path.

S0  reproduces the committed D62 arm clearing (pjm-t1h-d62-pubbar,
    b98060898fceb3da) from its own ledger through the code's own
    clear_capacity_supply_stack / capacity_supply_curve: 0.000 $/MW-day and
    0.000 pt in every delivery year, or STOP.
S74 moves every unit whose published class carries NO default gross ACR for
    the delivery year (basis "first_published" on the D62 vintage rule --
    Steam Oil & Gas through DY 2025/26) out of the offer stack and into the
    price-taking block Q_0 at $0 on its accredited MW, leaving every other
    offer byte-identical. That is the arm's own arithmetic before any solve.
Also reads the D62 arm's 2022 admission-cap outcome (decided vs entry_capped
MW by fuel) so the composition consequence can be pre-declared.

Run from the repo root:
    PYTHONPATH=.:src .venv/bin/python docs/handoffs/d74/phase0-2026-09-06.py [out.json]
"""

from __future__ import annotations

import glob
import importlib.util
import json
import sys

from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.data.avoidable_cost_rate import published_bar_per_kw_yr
from market_sim.model.capacity_evolution.adequacy import (
    capacity_supply_curve,
    clear_capacity_supply_stack,
)

D62 = glob.glob("results/hindcast/pjm-2021-2025-realized-t1h-d62-pubbar/PJM/*/")[0]
D57 = glob.glob("results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/*/")[0]
SCREEN_YEARS = (2022, 2023, 2024, 2025)
PUBLISHED = {
    2022: (50.00, 1.0510),
    2023: (34.13, 1.0552),
    2024: (28.92, 1.0555),
    2025: (269.92, 1.0049),
}


def _cfg(**extra):
    spec = importlib.util.spec_from_file_location(
        "rch", "scripts/run_capacity_hindcast.py"
    )
    rch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rch)
    common = dict(
        iso="PJM",
        start_year=2021,
        end_year=2025,
        variant="realized",
        vintage=2020,
        arm="realized",
        entry_screen_diagnostics=True,
    )
    return apply_iso_scenario_defaults(rch.build_config(**common, **extra), "PJM")


def no_default_cap(fuel: str, year: int) -> bool:
    """The class has no published default gross ACR for DY year/year+1."""
    hit = published_bar_per_kw_yr("PJM", fuel, year)
    return hit is not None and hit[1] == "first_published"


def reclear(bundle, cfg, label, price_take_no_default: bool):
    out = {}
    print(f"\n### {label}")
    print(
        f"{'DY':9s} {'price':>9s} {'pub':>8s} {'ratio':>6s} {'pos':>8s} {'pub':>8s} {'dpt':>6s} {'Q0':>10s} {'how':>34s}  uncleared firm MW by fuel"
    )
    for year in SCREEN_YEARS:
        with open(f"{bundle}/evolution_{year}.json") as fh:
            cc = json.load(fh)["capacity_clearing"]
        offers, moved = [], {}
        q0 = float(cc["price_takers_mw"])
        for uid, fuel, offer, a_mw, _cleared in cc["offer_stack"]:
            if price_take_no_default and no_default_cap(fuel, year):
                q0 += a_mw
                moved[fuel] = moved.get(fuel, 0.0) + a_mw
                continue
            offers.append((uid, fuel, offer, a_mw, 0.0))
        clearing = clear_capacity_supply_stack(
            offers, q0, cc["requirement_mw"], capacity_supply_curve(cfg, "PJM", year)
        )
        unc = {}
        for uid, fuel, o, a_mw, _p in offers:
            if uid not in clearing.cleared_unit_ids:
                unc[fuel] = unc.get(fuel, 0.0) + a_mw
        pub_p, pub_pos = PUBLISHED[year]
        dpt = 100.0 * (clearing.cleared_position - pub_pos)
        print(
            f"{year}/{year + 1 - 2000:02d}  {clearing.price_usd_per_mw_day:9.4f} {pub_p:8.2f} "
            f"{clearing.price_usd_per_mw_day / pub_p:6.3f} {clearing.cleared_position:8.4f} {pub_pos:8.4f} {dpt:+6.2f} "
            f"{q0:10.1f} {clearing.how:>34s}  { {k: round(v) for k, v in sorted(unc.items())} }"
        )
        out[year] = {
            "price": clearing.price_usd_per_mw_day,
            "ratio": clearing.price_usd_per_mw_day / pub_p,
            "pos": clearing.cleared_position,
            "dpos_pt": dpt,
            "how": clearing.how,
            "price_takers_mw": q0,
            "moved_to_price_takers_mw_by_fuel": {
                k: round(v, 1) for k, v in sorted(moved.items())
            },
            "uncleared_firm_mw": {k: round(v, 1) for k, v in sorted(unc.items())},
            "n_offers": clearing.n_offers,
            "n_uncleared": clearing.n_uncleared,
            "ledger_price": cc["price_usd_per_mw_day"],
            "ledger_pos": cc["cleared_position"],
            "requirement_mw": cc["requirement_mw"],
            "census_mw": cc["census_mw"],
        }
    return out


def admission(bundle, year):
    with open(f"{bundle}/evolution_{year}.json") as fh:
        pe = json.load(fh)["pipeline_events"]
    agg = {}
    for r in pe:
        k = (r["event"], r["fuel"])
        agg[k] = agg.get(k, 0.0) + float(r["mw"])
    return {f"{e}:{f}": round(v, 1) for (e, f), v in sorted(agg.items())}


def main():
    cfg_on = _cfg(capacity_going_forward_bar_published=True)
    print("D62 arm cache key at HEAD (published bar ON):", cfg_on.cache_key())
    print("bare pjm-t1h cache key at HEAD:", _cfg().cache_key())
    res = {"d62_bundle": D62, "d57_bundle": D57}
    res["S0_d62_reproduced"] = reclear(
        D62,
        cfg_on,
        "S0 -- the committed D62 arm, reproduced through the code path",
        False,
    )
    stop = False
    for y, r in res["S0_d62_reproduced"].items():
        dp, dq = abs(r["price"] - r["ledger_price"]), abs(r["pos"] - r["ledger_pos"])
        print(
            f"  S0 {y}: dprice {dp:.6f} dpos {dq:.6f}",
            "STOP" if (dp > 5e-4 or dq > 5e-5) else "ok",
        )
        stop |= dp > 5e-4 or dq > 5e-5
    res["S74_no_default_cap_price_takers"] = reclear(
        D62,
        cfg_on,
        "S74 -- no-default-cap classes (Steam Oil & Gas through DY 2025/26) as $0 price takers",
        True,
    )
    res["admission_d62_2022"] = admission(D62, 2022)
    res["admission_d62_2023"] = admission(D62, 2023)
    res["admission_d57_2022"] = admission(D57, 2022)
    print("\nD62 arm 2022 pipeline_events MW by event:fuel:", res["admission_d62_2022"])
    print("D62 arm 2023 pipeline_events MW by event:fuel:", res["admission_d62_2023"])
    print("D57 ctl 2022 pipeline_events MW by event:fuel:", res["admission_d57_2022"])
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w") as fh:
            json.dump(res, fh, indent=1, sort_keys=True)
    return 1 if stop else 0


if __name__ == "__main__":
    sys.exit(main())
