#!/usr/bin/env python3
"""capx D67-ARM — grade the re-solve against the PRECOMMIT's pre-declared P-A..P-E.

ONE solve (rule 29(b): the earned control buys no decision, because the
three-leg decomposition already closes). The two other legs are committed
records, not re-solves:

* **D67 §7.1** — the CLEAN arm effect, both legs at one base, so capx D81 and
  D65-B are absent from both and cancel exactly. Its numbers are transcribed
  here from the merged FINDING, which is the record (the bundles themselves
  were deleted before merge under rule 29(c)).
* **the committed `pjm-t1h-pre-d67` sidecar** — the shipped prior.

Therefore ``(re-solve) − (D67 §7.1 arm)`` IS the capx D81 measurement under the
arm, obtained free. D65-B is provably inert on it (PRECOMMIT §3.1: the CCS
family returns at ``apply_ccs_retrofit``'s first line below 2028).
"""

import json
from pathlib import Path

ARM = Path("results/capacity-hindcast/pjm_d67arm/PJM/a9c66d8ea25acb9d")

# FINDING-capx-d67-2026-09-06.md §7.1, transcribed verbatim. Both legs were
# solved at ONE base, so D81 and D65-B cancel between them.
D67_CONTROL_R = {2022: 146816.460, 2023: 156782.028, 2024: 166810.017, 2025: 152912.298}
D67_ARM_R = {2022: 163268.900, 2023: 163166.200, 2024: 164107.600, 2025: 144450.000}
D67_ARM_POS = {2022: 1.111265, 2023: 1.055476, 2024: 1.051736, 2025: 0.993091}
D67_CTRL_POS = {2022: 1.235795, 2023: 1.118225, 2024: 1.039347, 2025: 0.942260}
PUBLISHED_RR = {
    2021: 166355.1,
    2022: 163268.9,
    2023: 163166.2,
    2024: 164107.6,
    2025: 144450.0,
}
# PRECOMMIT §5 P-C: the signs, unchanged from D67.
DECLARED_SIGN = {2022: "FALL", 2023: "FALL", 2024: "RISE", 2025: "RISE"}


def load(y):
    return json.loads((ARM / f"evolution_{y}.json").read_text())


def main() -> int:
    out, verdicts = {}, {}

    # ---- P-A: the requirement rows reproduce D67 §7.1 byte-identically -----
    print("P-A (UNCONDITIONAL) — the requirement operand vs D67 §7.1")
    h = (
        f"{'DY':>10} {'arm R @HEAD':>13} {'D67 §7.1 arm R':>15} {'delta':>10} "
        f"{'published':>12} {'arm-pub':>9}"
    )
    print(h)
    print("-" * len(h))
    pa_ok = True
    for y in (2022, 2023, 2024, 2025):
        ra = load(y).get("screen_adequacy_requirement_mw")
        if ra is None:
            print(f"{f'{y}/{y + 1}':>10} {'NO SCREEN':>13}")
            pa_ok = False
            continue
        d67, pub = D67_ARM_R[y], PUBLISHED_RR[y]
        ok = abs(ra - d67) < 5e-4 and abs(ra - pub) < 5e-4
        pa_ok &= ok
        print(
            f"{f'{y}/{y + 1}':>10} {ra:>13.3f} {d67:>15.3f} {ra - d67:>+10.3f} "
            f"{pub:>12.1f} {ra - pub:>+9.3f} {'OK' if ok else '*** DEPART ***'}"
        )
        out.setdefault("requirement", {})[y] = {
            "arm_head": ra,
            "d67_arm": d67,
            "published": pub,
            "delta_vs_d67": ra - d67,
            "arm_minus_published": ra - pub,
        }
    verdicts["P-A"] = "HIT" if pa_ok else "FALSIFIED (STOP)"
    print(f"  => P-A {verdicts['P-A']}\n")

    # ---- P-B / P-E: census positions ---------------------------------------
    print("P-B / P-E — census position vs D67 §7.1's arm (the capx D81 measurement)")
    h = (
        f"{'DY':>10} {'arm pos @HEAD':>14} {'D67 §7.1 arm':>13} {'delta pt':>9} "
        f"{'D81 effect':>12}"
    )
    print(h)
    print("-" * len(h))
    for y in (2022, 2023, 2024, 2025):
        ca = load(y).get("capacity_clearing") or {}
        pa = ca.get("census_position")
        if pa is None:
            print(f"{f'{y}/{y + 1}':>10} {'—':>14}")
            continue
        d = (pa - D67_ARM_POS[y]) * 100.0
        tag = "identical" if abs(d) < 5e-5 else f"{d:+.4f} pt"
        print(
            f"{f'{y}/{y + 1}':>10} {pa:>14.6f} {D67_ARM_POS[y]:>13.6f} {d:>+9.4f} {tag:>12}"
        )
        out.setdefault("position", {})[y] = {
            "arm_head": pa,
            "d67_arm": D67_ARM_POS[y],
            "delta_pt": d,
            "implied_move_vs_d67_control_pt": (pa - D67_CTRL_POS[y]) * 100.0,
        }
    pb = out.get("position", {}).get(2022, {})
    verdicts["P-B"] = (
        "HIT"
        if abs(pb.get("delta_pt", 9e9)) < 5e-3
        else f"DEPARTS {pb.get('delta_pt'):+.4f} pt"
    )
    print(f"  => P-B (2022/23 byte-identical) {verdicts['P-B']}\n")

    # ---- P-C: the signs ----------------------------------------------------
    print("P-C — the pre-declared signs, vs D67 §7.1's own control")
    for y in (2022, 2023, 2024, 2025):
        r = out.get("position", {}).get(y)
        if not r:
            continue
        mv = r["implied_move_vs_d67_control_pt"]
        want = DECLARED_SIGN[y]
        ok = (mv > 0) == (want == "RISE")
        print(
            f"  {y}/{y + 1}: {mv:+7.2f} pt vs the D67 control  declared {want:>4}  "
            f"{'OK' if ok else '*** WRONG ***'}"
        )
        r["sign_declared"] = want
        r["sign_ok"] = ok
    verdicts["P-C"] = (
        "HIT"
        if all(v.get("sign_ok") for v in out.get("position", {}).values())
        else "FALSIFIED"
    )
    print(f"  => P-C {verdicts['P-C']}\n")

    # ---- P-D: 2021 has no screen -------------------------------------------
    e21 = load(2021)
    no_screen = e21.get("screen_adequacy_requirement_mw") is None
    verdicts["P-D"] = "HIT" if no_screen else "DEPARTS"
    print(f"P-D — 2021 runs no screen (no prior_results): {verdicts['P-D']}\n")

    # ---- clearing detail, reported at full magnitude ------------------------
    print("CLEARING — reported at full magnitude, gated on nothing")
    for y in (2022, 2023, 2024, 2025):
        ca = load(y).get("capacity_clearing") or {}
        if not ca:
            continue
        print(
            f"  {y}/{y + 1}: price {ca.get('price_per_firm_mw_yr', float('nan')):>12.2f} "
            f"$/firm-MW-yr  uncleared {ca.get('n_uncleared')}  how={ca.get('how')}"
        )
        out["position"][y]["price_per_firm_mw_yr"] = ca.get("price_per_firm_mw_yr")
        out["position"][y]["n_uncleared"] = ca.get("n_uncleared")
        out["position"][y]["how"] = ca.get("how")

    print("\nFLEET / EXITS — the arm at HEAD")
    for y in range(2021, 2026):
        e = load(y)
        rets = e.get("retirements") or []
        out.setdefault("fleet", {})[y] = {
            "n_retirements": len(rets),
            "fleet_by_fuel_after": e.get("fleet_by_fuel_after"),
        }
        print(f"  {y}: {len(rets)} retirement row(s)")

    out["verdicts"] = verdicts
    Path("docs/handoffs/d67arm/grade_resolve.json").write_text(
        json.dumps(out, indent=2, default=str) + "\n"
    )
    print("\nVERDICTS: " + ", ".join(f"{k}={v}" for k, v in verdicts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
