"""capx D74 — G1 in its structural form: re-clear the SAME-HEAD control-P ledger
with the no-default-cap class moved into Q_0 (the arm's own arithmetic, zero
LP) and compare with the solved arm, delivery year by delivery year.

Usage (repo root):
  PYTHONPATH=.:src .venv/bin/python docs/handoffs/d74/screen-reclear-2026-09-06.py \
      --ctlp <control-P out-dir> --arm <arm out-dir> [--years 2022 ...] [--out out.json]
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json

from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.data.avoidable_cost_rate import no_default_cap_class
from market_sim.model.capacity_evolution.adequacy import (
    capacity_supply_curve,
    clear_capacity_supply_stack,
)


def _cfg():
    spec = importlib.util.spec_from_file_location(
        "rch", "scripts/run_capacity_hindcast.py"
    )
    rch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rch)
    return apply_iso_scenario_defaults(
        rch.build_config(
            iso="PJM",
            start_year=2021,
            end_year=2025,
            variant="realized",
            vintage=2020,
            arm="realized",
            entry_screen_diagnostics=True,
            capacity_going_forward_bar_published=True,
        ),
        "PJM",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctlp", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2022])
    ap.add_argument("--out")
    a = ap.parse_args()
    cfg = _cfg()
    cb, ab = glob.glob(f"{a.ctlp}/PJM/*/")[0], glob.glob(f"{a.arm}/PJM/*/")[0]
    out = {}
    for y in a.years:
        cc = json.load(open(f"{cb}/evolution_{y}.json"))["capacity_clearing"]
        ca = json.load(open(f"{ab}/evolution_{y}.json"))["capacity_clearing"]
        q0, offers, moved = float(cc["price_takers_mw"]), [], 0.0
        for uid, fuel, offer, a_mw, _c in cc["offer_stack"]:
            if no_default_cap_class("PJM", fuel, y):
                q0 += a_mw
                moved += a_mw
                continue
            offers.append((uid, fuel, offer, a_mw, 0.0))
        cl = clear_capacity_supply_stack(
            offers, q0, cc["requirement_mw"], capacity_supply_curve(cfg, "PJM", y)
        )
        unc = {}
        for uid, fuel, o, a_mw, _p in offers:
            if uid not in cl.cleared_unit_ids:
                unc[fuel] = unc.get(fuel, 0.0) + a_mw
        row = {
            "ctlP_price": cc["price_usd_per_mw_day"],
            "ctlP_pos": cc["cleared_position"],
            "ctlP_how": cc["how"],
            "reclear_price": cl.price_usd_per_mw_day,
            "reclear_pos": cl.cleared_position,
            "reclear_how": cl.how,
            "arm_price": ca["price_usd_per_mw_day"],
            "arm_pos": ca["cleared_position"],
            "arm_how": ca["how"],
            "dprice_arm_vs_reclear": ca["price_usd_per_mw_day"]
            - cl.price_usd_per_mw_day,
            "dpos_arm_vs_reclear": ca["cleared_position"] - cl.cleared_position,
            "q0_ctlP": cc["price_takers_mw"],
            "q0_reclear": q0,
            "q0_arm": ca["price_takers_mw"],
            "class_moved_mw": moved,
            "requirement_mw": cc["requirement_mw"],
            "reclear_uncleared": {k: round(v, 1) for k, v in sorted(unc.items())},
            "arm_uncleared": ca["uncleared_mw_by_fuel"],
            "ctlP_uncleared": cc["uncleared_mw_by_fuel"],
        }
        out[y] = row
        print(
            f"DY {y}/{y + 1 - 2000:02d}: control-P {row['ctlP_price']:.4f} @ {row['ctlP_pos']:.4f} [{row['ctlP_how']}] -> "
            f"re-clear {row['reclear_price']:.4f} @ {row['reclear_pos']:.4f} [{row['reclear_how']}] vs ARM "
            f"{row['arm_price']:.4f} @ {row['arm_pos']:.4f} [{row['arm_how']}]  dprice {row['dprice_arm_vs_reclear']:+.4f} dpos {row['dpos_arm_vs_reclear']:+.5f}"
        )
        print(
            f"   Q0 ctlP {row['q0_ctlP']:.1f} + class {moved:.1f} = {q0:.1f} vs arm {row['q0_arm']:.1f}; R {row['requirement_mw']:.1f}"
        )
        print(
            f"   uncleared re-clear {row['reclear_uncleared']} | arm {row['arm_uncleared']} | ctlP {row['ctlP_uncleared']}"
        )
    if a.out:
        json.dump(out, open(a.out, "w"), indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
