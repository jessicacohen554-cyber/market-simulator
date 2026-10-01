#!/usr/bin/env python3
"""capx D67 FULL SPAN — grade the PRECOMMIT §7 pre-declared signs at full magnitude.

Both arms solved at HEAD over 2021-2025 (G-CTRL form 4 is void; §2.2). The
control's key is the shipped bare `pjm-t1h`, so the control IS the shipped
posture. Nothing here is a gate: the screen already ran and passed, and this
section reports what the card does, at full magnitude, including where it makes
a year worse.
"""

import json
from pathlib import Path

CTRL = Path("results/hindcast/pjm-d67-full-control/PJM/aef81c84c4609c76")
ARM = Path("results/hindcast/pjm-d67-full-arm/PJM/3f4070767f29472a")
# PRECOMMIT §7, computed pre-solve and frozen there.
DECLARED = {2022: ("FALL", -9.7), 2023: ("FALL", -3.8),
            2024: ("RISE", +1.6), 2025: ("RISE", +5.6)}
PUBLISHED_RR = {2021: 166355.1, 2022: 163268.9, 2023: 163166.2,
                2024: 164107.6, 2025: 144450.0}


def load(d, y):
    return json.loads((d / f"evolution_{y}.json").read_text())


def main() -> int:
    print("REQUIREMENT — the operand, arm vs control (MW)")
    h = f"{'yr':>5} {'DY':>10} {'control R':>12} {'arm R':>12} {'published':>12} {'arm-pub':>9} {'dR':>11}"
    print(h); print("-" * len(h))
    for y in range(2021, 2026):
        c, a = load(CTRL, y), load(ARM, y)
        rc, ra = c.get("screen_adequacy_requirement_mw"), a.get("screen_adequacy_requirement_mw")
        if rc is None or ra is None:
            print(f"{y:>5} {f'{y}/{y+1}':>10} {'—':>12} {'—':>12} "
                  f"{PUBLISHED_RR[y]:>12.1f} {'—':>9} {'no screen':>11}")
            continue
        print(f"{y:>5} {f'{y}/{y+1}':>10} {rc:>12.3f} {ra:>12.3f} {PUBLISHED_RR[y]:>12.1f} "
              f"{ra - PUBLISHED_RR[y]:>9.3f} {ra - rc:>+11.3f}")

    print("\nPOSITION — the pre-declared signs, graded at full magnitude")
    h = (f"{'DY':>10} {'ctrl census':>12} {'arm census':>12} {'move pt':>9} "
         f"{'declared':>10} {'sign':>6} {'grade':>8}")
    print(h); print("-" * len(h))
    grades, rows = [], {}
    for y in (2022, 2023, 2024, 2025):
        c, a = load(CTRL, y), load(ARM, y)
        cc, ca = c.get("capacity_clearing") or {}, a.get("capacity_clearing") or {}
        pc, pa = cc.get("census_position"), ca.get("census_position")
        if pc is None or pa is None:
            print(f"{f'{y}/{y+1}':>10} {'—':>12} {'—':>12} {'—':>9}")
            continue
        move = (pa - pc) * 100.0
        want_sign, want_mag = DECLARED[y]
        sign_ok = (move > 0) == (want_sign == "RISE")
        mag_ok = abs(move - want_mag) <= max(1.0, 0.25 * abs(want_mag))
        g = "HIT" if (sign_ok and mag_ok) else ("SIGN OK" if sign_ok else "MISS")
        grades.append((y, g))
        rows[y] = {"control": pc, "arm": pa, "move_pt": move,
                   "declared_pt": want_mag, "grade": g}
        print(f"{f'{y}/{y+1}':>10} {pc:>12.6f} {pa:>12.6f} {move:>+9.2f} "
              f"{want_mag:>+10.1f} {'OK' if sign_ok else 'WRONG':>6} {g:>8}")

    print("\nG6 — the D62 invariant: the 2024/25 price must not move on the census")
    c24, a24 = load(CTRL, 2024), load(ARM, 2024)
    cc, ca = c24["capacity_clearing"], a24["capacity_clearing"]
    print(f"  control: price {cc['price_per_firm_mw_yr']:>12.2f}  census "
          f"{cc['census_position']:.6f}  uncleared {cc['n_uncleared']}  how={cc['how']}")
    print(f"  arm    : price {ca['price_per_firm_mw_yr']:>12.2f}  census "
          f"{ca['census_position']:.6f}  uncleared {ca['n_uncleared']}  how={ca['how']}")
    dprice = ca["price_per_firm_mw_yr"] - cc["price_per_firm_mw_yr"]
    print(f"  price moves {dprice:+.2f} $/firm-MW-yr")

    print("\nFLEET — where the effect lands (arm - control, MW)")
    for y in range(2021, 2026):
        c, a = load(CTRL, y), load(ARM, y)
        fc, fa = c.get("fleet_by_fuel_after") or {}, a.get("fleet_by_fuel_after") or {}
        d = {k: float(fa.get(k, 0)) - float(fc.get(k, 0))
             for k in set(fc) | set(fa) if abs(float(fa.get(k, 0)) - float(fc.get(k, 0))) > 1e-6}
        rc = [r.get("plant_id") for r in (c.get("retirements") or [])]
        ra = [r.get("plant_id") for r in (a.get("retirements") or [])]
        print(f"  {y}: fleet {d if d else 'identical'};  retirements "
              f"{'identical' if rc == ra else f'{len(rc)} -> {len(ra)} rows'}")

    Path("docs/handoffs/d67/fullspan_grade.json").write_text(
        json.dumps({"position": rows, "g6_price_delta": dprice,
                    "grades": dict(grades)}, indent=2) + "\n")
    print("\nGRADES: " + ", ".join(f"{y}/{y+1- 2000}: {g}" for y, g in grades))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
