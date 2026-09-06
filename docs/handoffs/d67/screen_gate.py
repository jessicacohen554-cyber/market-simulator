#!/usr/bin/env python3
"""capx D67 SCREEN GATE — grade G1-G5 on the 2025 screen, arm vs the HEAD control.

STRUCTURAL and a STOP GATE ONLY (PRECOMMIT-capx-d67 §6): it may kill the arm, it
may never promote one, it contributes to no determination, and it is never read
against the target residual. Both arms solved at HEAD, because the G-DRIFT audit
measured the demand path LIVE and G-CTRL form 4 is therefore void.
"""

import json
from pathlib import Path

CTRL = Path("results/hindcast/pjm-d67-screen-control/PJM/6d058c186839457b")
ARM = Path("results/hindcast/pjm-d67-screen-arm/PJM/4bdd3e7cfdc6ceee")
PUBLISHED_2025_26 = 144_450.0
DECLARED_DELTA = 8_462.3
TOL = 5e-4

# G3 is graded on the PRECOMMIT's OWN ENUMERATION (§6 G3), verbatim: the
# ENTERING side, which is what "the gate changes the requirement operand and
# nothing else" can coherently mean. It cannot mean the solve produces an
# identical fleet -- G2 *requires* the requirement to change, and §7's P1/P2
# pre-declare that the position moves -- so a gate reading "nothing downstream
# moved" would contradict the rest of the pre-registration. The EXITING side is
# therefore reported at full magnitude below rather than gated.
#
# RECORDED AGAINST INTEREST: this list initially carried four fields beyond the
# PRECOMMIT's enumeration (peak_demand_mw, firm_clean_*, storage_power_mw and
# reserve_margin). Three were byte-identical anyway; reserve_margin was not, and
# it is `firm_mw / peak - 1` computed AFTER evolution (runner.py:4760) -- an
# exiting-side quantity. The SCRIPT was corrected to the pre-registered text.
# The gate text was NOT relaxed to fit the result, and the movement that
# over-specified list caught is reported in full under "exiting side" below.
CONFINED = [
    "screen_peak_demand_mw", "screen_entering_firm_mw", "fleet_by_fuel_before",
    "wind_cap_mw", "solar_cap_mw", "storage_firm_mw",
]
EXITING = ["reserve_margin", "fleet_by_fuel_after", "retirements",
           "floor_retained", "thermal_additions", "entry_decided_mw_by_tech"]


def main() -> int:
    c = json.loads((CTRL / "evolution_2025.json").read_text())
    a = json.loads((ARM / "evolution_2025.json").read_text())
    rows, fails = [], []

    def grade(gid, desc, ok, detail):
        rows.append((gid, "PASS" if ok else "FAIL", desc, detail))
        if not ok:
            fails.append(f"{gid}: {detail}")

    # G1 -- identity
    got = float(a["screen_adequacy_requirement_mw"])
    grade("G1", "arm requirement == published 2025/26 RTO Reliability Requirement",
          abs(got - PUBLISHED_2025_26) < TOL,
          f"{got:.3f} vs {PUBLISHED_2025_26:.3f} (delta {got - PUBLISHED_2025_26:+.4f})")

    # G2 -- direction & magnitude against the pre-solve arithmetic
    rc = float(c["screen_adequacy_requirement_mw"])
    d = rc - got
    grade("G2", "arm requirement is DECLARED_DELTA below the control",
          abs(d - DECLARED_DELTA) < 0.05,
          f"control {rc:.3f} - arm {got:.3f} = {d:.3f} MW; declared {DECLARED_DELTA:.1f} "
          f"(miss {d - DECLARED_DELTA:+.4f})")

    # G3 -- confinement
    diffs = [k for k in CONFINED if c.get(k) != a.get(k)]
    grade("G3", "entering side byte-identical to the control", not diffs,
          "all identical" if not diffs else f"MOVED: {diffs}")

    # G4 -- one requirement
    ok4 = (abs(float(a["capacity_clearing"]["requirement_mw"]) - got) < TOL
           and abs(float(a["adequacy_requirement_mw"]) - got) < TOL
           and abs(float(c["capacity_clearing"]["requirement_mw"]) - rc) < TOL)
    grade("G4", "clearing + ledger requirement == screen requirement, both arms", ok4,
          f"arm clearing {a['capacity_clearing']['requirement_mw']}, ledger "
          f"{a['adequacy_requirement_mw']}; control clearing "
          f"{c['capacity_clearing']['requirement_mw']}")

    # G5 -- no collateral flip: the 2024 screen (no prior_results) is null in
    # BOTH arms, and 2024's evolution must be identical since the gate cannot
    # act before a screen exists.
    c24 = json.loads((CTRL / "evolution_2024.json").read_text())
    a24 = json.loads((ARM / "evolution_2024.json").read_text())
    moved24 = [k for k in CONFINED + ["screen_adequacy_requirement_mw", "retirements",
                                      "fleet_by_fuel_after", "reserve_margin"]
               if c24.get(k) != a24.get(k)]
    grade("G5", "the pre-screen year (2024) is identical in both arms", not moved24,
          "identical" if not moved24 else f"MOVED: {moved24}")

    w = max(len(r[2]) for r in rows)
    print(f"{'gate':<5} {'verdict':<7} {'what':<{w}}  detail")
    print("-" * (5 + 8 + w + 2 + 60))
    for gid, v, desc, detail in rows:
        print(f"{gid:<5} {v:<7} {desc:<{w}}  {detail}")

    # Reported beside the gate, NEVER as a gate.
    print("\nEXITING side -- the mechanism's intended downstream channel, reported "
          "at full magnitude, not gated:")
    for k in EXITING:
        print(f"  {k:26s} identical={c.get(k) == a.get(k)}")
    fa_c, fa_a = c.get("fleet_by_fuel_after") or {}, a.get("fleet_by_fuel_after") or {}
    for k in sorted(set(fa_c) | set(fa_a)):
        d = float(fa_a.get(k, 0)) - float(fa_c.get(k, 0))
        if abs(d) > 1e-6:
            print(f"    fleet_by_fuel_after[{k}] {d:+.3f} MW (arm - control)")

    print("\nreported, not gated (the position response the full span will grade):")
    for label, node in (("control", c), ("arm", a)):
        cc = node["capacity_clearing"]
        print(f"  {label:<8} census_position {cc['census_position']:.6f}  "
              f"cleared {cc['cleared_position']:.6f}  "
              f"price/firm-MW-yr {cc['price_per_firm_mw_yr']:.2f}  "
              f"uncleared {cc['n_uncleared']}  how={cc['how']}")
    dpos = (a["capacity_clearing"]["census_position"]
            - c["capacity_clearing"]["census_position"]) * 100.0
    print(f"  2025/26 census position moves {dpos:+.2f} pt "
          f"(PRECOMMIT §7 P2 pre-declared ~+5.6 pt)")

    print()
    print("SCREEN VERDICT: " + ("PASS -- the arm survives; the full span may be spent."
                                if not fails else "FAIL -- the arm is KILLED:"))
    for f in fails:
        print("  -", f)
    Path("docs/handoffs/d67/screen_gate.json").write_text(json.dumps(
        {"passed": not fails, "failures": fails,
         "rows": [{"gate": g, "verdict": v, "what": d, "detail": t} for g, v, d, t in rows],
         "position_delta_pt": dpos}, indent=2) + "\n")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
