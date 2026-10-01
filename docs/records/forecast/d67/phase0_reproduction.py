#!/usr/bin/env python3
"""Phase 0 (capx D67) — reproduce D66's requirement arithmetic THROUGH THE CODE PATH.

Zero LP. Four checks, all to 0.000 MW (charter step 2 / PRECOMMIT §8 STOP 1):

  A. **Requirement path is unmoved at HEAD.** With the gate OFF, the resolver
     reproduces the D57 arm A committed ``screen_adequacy_requirement_mw`` when
     fed arm A's own committed ``screen_peak_demand_mw``. This is the TARGETED
     G-DRIFT check: it isolates the requirement path from the demand path the
     G-DRIFT probe already measured LIVE, and shows the operand's own code has
     not drifted.
  B. **D66's decomposition reproduces.** ``FPR × (peak_model − peak_implied)``
     equals ``R_model − R_published`` to 0.000 MW, where ``peak_implied`` is
     ``R_published ÷ FPR`` — D66 §3.1's zero-residual identity, re-derived here
     through the shipped resolvers rather than restated.
  C. **The gate returns the published MW**, exactly, in every in-table
     delivery year, independent of the peak it is handed.
  D. **The gate is inert outside the table** — the in-table gap (2026/27,
     2027/28) and every year past the 2028/29 forward edge fall through to the
     FPR path byte-identically (PRECOMMIT §4).
"""

import json
import sys
from pathlib import Path

sys.path[:0] = ["src", "."]

# ruff: noqa: E402  (sys.path must be set before market_sim resolves)

from market_sim.config.capacity_market import RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO
from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.model.capacity_evolution.retirements import (
    gross_adequacy_requirement_mw,
    resolve_adequacy_requirement_mw,
    resolve_forecast_pool_requirement,
    resolve_pre_reform_pool_requirement,
)
from scripts.run_capacity_hindcast import build_config

ARM_A = Path(
    "results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a"
)
ISO = "PJM"
TOL = 5e-4


def main() -> int:
    off = apply_iso_scenario_defaults(
        build_config(ISO, 2021, 2025, "realized", vintage=2020,
                     entry_screen_diagnostics=True), ISO)
    on = off.with_overrides(
        capacity_adequacy_requirement_published_by_iso={ISO: True}
    )
    out, fails = {}, []

    print("A. requirement path at HEAD, gate OFF, on arm A's own committed peak")
    hdr = f"{'yr':>5} {'armA peak':>12} {'R @HEAD(off)':>14} {'armA R':>12} {'delta':>9}"
    print(hdr); print("-" * len(hdr))
    for year in range(2021, 2026):
        led = json.loads((ARM_A / f"evolution_{year}.json").read_text())
        pk, ref = led.get("screen_peak_demand_mw"), led.get("screen_adequacy_requirement_mw")
        if pk is None or ref is None:
            print(f"{year:>5} {pk if pk else 0:>12.3f} {'—':>14} {'null':>12} "
                  f"{'skip':>9}  (no screen: first solved year has no prior_results)")
            continue
        got = resolve_adequacy_requirement_mw(off, ISO, float(pk), year)
        d = got - float(ref)
        if abs(d) > TOL:
            fails.append(f"A/{year}: {d:+.3f} MW")
        print(f"{year:>5} {pk:>12.3f} {got:>14.3f} {ref:>12.3f} {d:>9.3f}")

    print("\nB. D66's decomposition, re-derived through the shipped resolvers")
    hdr = (f"{'yr':>5} {'FPR':>7} {'R_pub':>11} {'implied pk':>11} {'model pk':>11} "
           f"{'R_model':>11} {'FPRxdPk':>10} {'dR':>10} {'resid':>8}")
    print(hdr); print("-" * len(hdr))
    for year in range(2021, 2026):
        led = json.loads((ARM_A / f"evolution_{year}.json").read_text())
        pk = led.get("screen_peak_demand_mw")
        fpr = (resolve_pre_reform_pool_requirement(off, ISO, year)
               or resolve_forecast_pool_requirement(ISO, year))
        pub = RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO[ISO].get(f"{year}/{year + 1}")
        if pk is None or fpr is None or pub is None:
            continue
        implied = pub / fpr
        r_model = gross_adequacy_requirement_mw(off, ISO, float(pk), year)
        resid = fpr * (float(pk) - implied) - (r_model - pub)
        if abs(resid) > TOL:
            fails.append(f"B/{year}: residual {resid:+.3f} MW")
        out.setdefault("decomposition", {})[year] = {
            "fpr": fpr, "r_published": pub, "implied_peak": implied,
            "model_peak": float(pk), "r_model": r_model,
            "delta_peak": float(pk) - implied, "delta_r": r_model - pub,
            "residual": resid,
        }
        print(f"{year:>5} {fpr:>7.4f} {pub:>11.1f} {implied:>11.1f} {pk:>11.1f} "
              f"{r_model:>11.1f} {fpr * (float(pk) - implied):>10.1f} "
              f"{r_model - pub:>10.1f} {resid:>8.3f}")

    print("\nC. gate ON returns the published MW, independent of the peak")
    for dy, pub in sorted(RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO[ISO].items()):
        year = int(dy[:4])
        got = {round(gross_adequacy_requirement_mw(on, ISO, p, year), 6)
               for p in (100_000.0, 158_633.356, 250_000.0)}
        ok = got == {round(pub, 6)}
        if not ok:
            fails.append(f"C/{dy}: {got} != {pub}")
        print(f"  {dy}  published {pub:>12.5f}  ->  {sorted(got)}  {'OK' if ok else 'FAIL'}")

    print("\nD. gap + forward edge fall through to the FPR path, byte-identically")
    for year in (2019, 2020, 2026, 2027, 2029, 2035, 2050):
        a = gross_adequacy_requirement_mw(on, ISO, 158_633.356, year)
        b = gross_adequacy_requirement_mw(off, ISO, 158_633.356, year)
        ok = abs(a - b) < 1e-9
        if not ok:
            fails.append(f"D/{year}: {a} != {b}")
        print(f"  {year}  on {a:>12.3f}  off {b:>12.3f}  {'identical' if ok else 'FAIL'}")

    print()
    if fails:
        print("PHASE 0 FAILED (PRECOMMIT §8 STOP 1):")
        for f in fails:
            print("  -", f)
    else:
        print("PHASE 0 PASSED — all four checks to 0.000 MW.")
    Path("docs/handoffs/d67/phase0_reproduction.json").write_text(
        json.dumps({"passed": not fails, "failures": fails, **out}, indent=2) + "\n")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
