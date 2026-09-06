"""capx D62 PHASE 0 (zero LP, a STOP gate).

Reproduce S0 (the committed arm-A clearing) and S6 (every class bar at PJM's
published default gross ACR) of ``docs/handoffs/d61/reclear-2026-09-05.py``
**through the code path** -- the new
``retirements.resolve_going_forward_bar_per_kw_yr`` feeding the code's own
``clear_capacity_supply_stack`` / ``capacity_supply_curve`` -- against the
committed D57 arm-A ledgers. Tolerance 0.000 $/MW-day and 0.000 pt in all four
delivery years, both scenarios (PRECOMMIT-capx-d62 §3). Any mismatch is a STOP.

Two things this instrument does that D61's could not, both strengthening the
reproduction rather than loosening it:

* the accreditation fraction is the LEDGER'S OWN ``a_mw / pmax`` per unit, not
  a reconstructed EFORD/ELCC table lookup -- the ledger row carries both, so no
  accreditation assumption enters at all;
* the bars on both sides come from the CODE's resolver under a real
  ``ScenarioConfig`` (gate off -> S0's ATB bars, gate on -> S6's published
  bars), so a divergence between the instrument's arithmetic and the model's is
  impossible by construction.

Run from the repo root:
    PYTHONPATH=.:src python docs/handoffs/d62/phase0-2026-09-06.py [out.json]
"""

from __future__ import annotations

import glob
import json
import sys

from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.model.capacity_evolution.adequacy import (
    capacity_supply_curve,
    clear_capacity_supply_stack,
)
from market_sim.config.constants import EFORD
from market_sim.data.avoidable_cost_rate import reactive_offset_per_mw_yr
from market_sim.model.capacity_evolution.retirements import (
    resolve_going_forward_bar_per_kw_yr,
    thermal_accreditation_fraction,
)

BUNDLE = glob.glob(
    "results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/*/"
)[0]
SCREEN_YEARS = (2022, 2023, 2024, 2025)

# The published record, VALIDATION OBSERVABLES only (rule 13): nothing below
# enters the model. (price $/MW-day, cleared position) per delivery year.
PUBLISHED = {
    2022: (50.00, 1.0510),
    2023: (34.13, 1.0552),
    2024: (28.92, 1.0555),
    2025: (269.92, 1.0049),
}

# D61 reclear-2026-09-05.json, the rows this gate must land on exactly (S0) and
# the rows it must reproduce (S6): (price $/MW-day, cleared position).
D61_S0 = {2022: (76.10, 1.0462), 2023: (82.81, 1.0454), 2024: (165.84, 1.0276)}
D61_S6_RATIO = {2022: 1.06, 2023: 1.56, 2024: 5.04}


def _configs():
    """Return the (gate OFF, gate ON) PJM T1-H configs, seam-resolved."""
    import importlib.util

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
    off = apply_iso_scenario_defaults(rch.build_config(**common), "PJM")
    on = apply_iso_scenario_defaults(
        rch.build_config(**common, capacity_going_forward_bar_published=True), "PJM"
    )
    return off, on


_AF_CACHE: dict = {}


def _accreditation_fraction(config, fuel: str, year: int) -> float:
    """The class accreditation fraction the ledger's ``accredited_mw`` used.

    ``thermal_accreditation_fraction`` on the class EFORd — the same resolver
    ``retirements._thermal_firm_mw`` prices a unit's firm MW through, so this
    inverts the ledger's own construction instead of reconstructing it from a
    hand table.
    """
    key = (fuel, year)
    if key not in _AF_CACHE:
        _AF_CACHE[key] = float(
            thermal_accreditation_fraction(
                fuel, EFORD.get(fuel, 0.08), "PJM", config, year
            )
        )
    return _AF_CACHE[key]


def reclear(cfg_source, cfg_target, label, censored="d61", reactive=0.0):
    """Re-clear every screen year's committed stack on ``cfg_target``'s bars.

    ``cfg_source`` supplies the bars the committed offers were BUILT from (so
    each unit's pre-capacity E&AS can be inverted out of its offer exactly);
    ``cfg_target`` supplies the bars to re-offer on. Passing the same config
    for both is the S0 identity check.

    THE ONE APPROXIMATION IN THIS RECONSTRUCTION, and it is the reconstruction's
    alone -- the SOLVE has none, because the model never inverts an offer: it
    computes each unit's E&AS in the screen and applies the bar directly.

    A unit that offered **0** is CENSORED: all the ledger tells us is
    ``EAS >= GFC_source``. Under a target bar at or below the source bar it is
    still a price taker, exactly. Under a target bar ABOVE the source bar it
    may not be, and its offer is bounded by
    ``max(0, GFC_target - GFC_source) / (A_g x 365)``. On this horizon exactly
    one class has a published bar above its ATB bar -- **nuclear**, 162.43 vs
    130.0 $/kW-yr -- so the question is nuclear's alone.

    ``censored="d61"`` keeps D61's own convention (censored -> 0) so S6
    reproduces ``reclear-2026-09-05.json`` row for row; ``censored="bound"``
    re-clears with the upper bound instead, which brackets the effect. Both are
    reported: a bracket that does not move the price is a disclosure, not a
    caveat.
    """
    out = {}
    print(f"\n### {label}")
    print(
        f"{'DY':9s} {'price':>9s} {'pub':>8s} {'ratio':>6s} {'pos':>8s} "
        f"{'pub':>8s} {'dpt':>6s}  uncleared firm MW by fuel"
    )
    for year in SCREEN_YEARS:
        with open(f"{BUNDLE}/evolution_{year}.json") as fh:
            cc = json.load(fh)["capacity_clearing"]
        offers = []
        censored_raised: dict[str, int] = {}
        for uid, fuel, offer, a_mw, _cleared in cc["offer_stack"]:
            # The ledger row is [uid, fuel, offer, ACCREDITED_MW, cleared] --
            # element 4 is a bool, not nameplate. The unit's nameplate is
            # recovered through the CODE's own class accreditation resolver
            # (``thermal_accreditation_fraction`` on the class EFORd), which is
            # exactly what ``_thermal_firm_mw`` priced ``a_mw`` with, so
            # ``pmax = a_mw / af`` is the ledger's own construction inverted
            # rather than a reconstructed table (D61's EFORD/ELCC dicts).
            af = _accreditation_fraction(cfg_source, fuel, year)
            pmax = a_mw / af if af > 0.0 else 0.0
            src_bar, _ = resolve_going_forward_bar_per_kw_yr(cfg_source, fuel, year)
            tgt_bar, _ = resolve_going_forward_bar_per_kw_yr(cfg_target, fuel, year)
            if offer <= 0.0:
                # Censored (see the docstring). Exact when the target bar does
                # not rise; otherwise D61's convention or the upper bound.
                if tgt_bar <= src_bar + 1e-9 or censored == "d61":
                    new_offer = 0.0
                else:
                    new_offer = (tgt_bar - src_bar) * pmax * 1000.0 / (a_mw * 365.0)
                    censored_raised[fuel] = censored_raised.get(fuel, 0) + 1
            else:
                gfc_src = src_bar * pmax * 1000.0
                eas = gfc_src - offer * a_mw * 365.0
                # capx D62 seam 2: the published reactive component enters the
                # unit's pre-capacity E&AS once, as ``pmax x rate``, exactly as
                # the screen credits it -- so the re-offered stack is the arm's
                # own arithmetic, not the bar alone.
                eas += float(reactive) * pmax
                gfc_tgt = tgt_bar * pmax * 1000.0
                new_offer = max(0.0, gfc_tgt - eas) / (a_mw * 365.0)
            offers.append((uid, fuel, new_offer, a_mw, pmax))
        clearing = clear_capacity_supply_stack(
            offers,
            cc["price_takers_mw"],
            cc["requirement_mw"],
            capacity_supply_curve(cfg_target, "PJM", year),
        )
        unc = {}
        for _uid, fuel, o, a_mw, _p in offers:
            if o > clearing.price_usd_per_mw_day + 1e-9:
                unc[fuel] = unc.get(fuel, 0.0) + a_mw
        pub_p, pub_pos = PUBLISHED[year]
        dpt = 100.0 * (clearing.cleared_position - pub_pos)
        print(
            f"{year}/{year + 1 - 2000:02d}  {clearing.price_usd_per_mw_day:9.2f} "
            f"{pub_p:8.2f} {clearing.price_usd_per_mw_day / pub_p:6.2f} "
            f"{clearing.cleared_position:8.4f} {pub_pos:8.4f} {dpt:+6.2f}  "
            f"{ {k: round(v) for k, v in sorted(unc.items())} }"
        )
        out[year] = {
            "price": clearing.price_usd_per_mw_day,
            "ratio": clearing.price_usd_per_mw_day / pub_p,
            "pos": clearing.cleared_position,
            "dpos_pt": dpt,
            "how": clearing.how,
            "uncleared_firm_mw": {k: round(v, 1) for k, v in sorted(unc.items())},
            "n_offers": clearing.n_offers,
            "n_uncleared": clearing.n_uncleared,
            "censored_units_re_offered": censored_raised,
        }
    return out


def main() -> int:
    off, on = _configs()
    result = {}

    # --- S0: the committed clearing, reproduced from the ledgers themselves --
    ledger = {}
    for year in SCREEN_YEARS:
        with open(f"{BUNDLE}/evolution_{year}.json") as fh:
            cc = json.load(fh)["capacity_clearing"]
        ledger[year] = (float(cc["price_usd_per_mw_day"]), float(cc["cleared_position"]))
    result["ledger"] = {y: {"price": p, "pos": q} for y, (p, q) in ledger.items()}
    # --- The inversion's own identity check, unit by unit ------------------
    # Before any re-clearing: with the recovered nameplate and the ATB bar,
    # ``max(0, GFC - EAS)/(A x 365)`` must return each unit's OWN committed
    # offer for every unit that offered above zero (E&AS is defined as the
    # residual, so this is a tautology per unit) -- what it actually tests is
    # that the PLATEAU units, whose E&AS is exactly 0, land on
    # ``bar x 1000 / (af x 365)``. A plateau that does not reproduce means the
    # accreditation inversion is wrong, and every re-cleared number after it
    # would be too.
    plateau = {}
    for year in SCREEN_YEARS:
        with open(f"{BUNDLE}/evolution_{year}.json") as fh:
            cc = json.load(fh)["capacity_clearing"]
        worst = 0.0
        for _uid, fuel, offer, a_mw, _c in cc["offer_stack"]:
            af = _accreditation_fraction(off, fuel, year)
            bar, _ = resolve_going_forward_bar_per_kw_yr(off, fuel, year)
            want = bar * 1000.0 / (af * 365.0)
            if offer > 0.0 and abs(offer - want) < 1e-3:  # a plateau unit
                worst = max(worst, abs(offer - want))
        plateau[year] = worst
    print("### Inversion identity: max |plateau offer - bar/(af x 365)| by year")
    print("   ", {y: round(v, 6) for y, v in plateau.items()})
    result["inversion_plateau_max_abs_err"] = plateau

    result["S0"] = reclear(off, off, "S0 -- committed arm-A clearing, re-cleared on the SAME (ATB) bars")
    result["S6"] = reclear(
        off, on, "S6 -- every class bar at PJM's PUBLISHED default gross ACR"
    )
    result["S6R"] = reclear(
        off,
        on,
        "S6R -- THE ARM's OWN ARITHMETIC: published bars PLUS the published "
        "reactive component ($2,199/MW-yr), the pre-solve prediction the screen "
        "gate G1 grades the solve's direction and magnitude against",
        reactive=reactive_offset_per_mw_yr("PJM") or 0.0,
    )
    result["S6_censored_bound"] = reclear(
        off,
        on,
        "S6b -- same, with the censored-unit UPPER BOUND instead of D61's zero "
        "(nuclear is the only class whose published bar rises: 130.0 -> 162.43)",
        censored="bound",
    )

    print("\n### PHASE 0 GATE (tolerance 0.000 $/MW-day, 0.000 pt)")
    fails = []
    for year in SCREEN_YEARS:
        lp, lq = ledger[year]
        s0 = result["S0"][year]
        dp = abs(s0["price"] - lp)
        dq = abs(100.0 * (s0["pos"] - lq))
        ok = dp < 5e-4 and dq < 5e-4
        print(
            f"  S0 {year}/{year + 1 - 2000:02d}: ledger {lp:9.4f} / {lq:.6f}  "
            f"code {s0['price']:9.4f} / {s0['pos']:.6f}  "
            f"dprice {dp:.4f} $/MW-day  dpos {dq:.4f} pt  {'PASS' if ok else 'FAIL'}"
        )
        if not ok:
            fails.append(f"S0 {year}")
    for year, want in D61_S0.items():
        got = result["S0"][year]
        ok = abs(got["price"] - want[0]) < 5e-3 and abs(got["pos"] - want[1]) < 5e-5
        print(
            f"  S0 vs D61 {year}: want {want[0]:.2f} / {want[1]:.4f}  "
            f"got {got['price']:.2f} / {got['pos']:.4f}  {'PASS' if ok else 'FAIL'}"
        )
        if not ok:
            fails.append(f"S0-vs-D61 {year}")
    for year, want in D61_S6_RATIO.items():
        got = result["S6"][year]["ratio"]
        ok = abs(got - want) < 5e-3
        print(
            f"  S6 vs D61 {year}: want ratio {want:.2f}  got {got:.4f}  "
            f"{'PASS' if ok else 'FAIL'}"
        )
        if not ok:
            fails.append(f"S6-vs-D61 {year}")

    print("\n### The reconstruction's one approximation, bracketed (S6 vs S6b)")
    for year in SCREEN_YEARS:
        a, b = result["S6"][year], result["S6_censored_bound"][year]
        raised = b["censored_units_re_offered"]
        print(
            f"  {year}/{year + 1 - 2000:02d}: price {a['price']:.4f} vs "
            f"{b['price']:.4f} $/MW-day  |  pos {a['pos']:.6f} vs {b['pos']:.6f}"
            f"  |  censored units re-offered {raised}"
        )

    result["gate"] = {"failures": fails, "verdict": "PASS" if not fails else "STOP"}
    print(f"\nPHASE 0 VERDICT: {result['gate']['verdict']}"
          + (f"  ({', '.join(fails)})" if fails else ""))
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w") as fh:
            json.dump(result, fh, indent=1)
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
