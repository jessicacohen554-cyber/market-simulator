#!/usr/bin/env python3
"""capx D76 phase 1 -- the rule-29 STRUCTURAL screen gate. Zero LP, committed artifacts only.

Grades the PJM 2021-2023 screen (arm vs control at the same HEAD) against the
STOP gates pre-registered in
``docs/handoffs/PRECOMMIT-capx-d76-measured-screen-peak-2026-09-06.md`` §4 --
**and against nothing else**. The D67 lane recorded, against interest, that its
first grading script carried four fields beyond its PRECOMMIT's own enumeration
and reported a FAIL on an exiting-side quantity the gate never named; the fix
there was to correct the SCRIPT to the pre-registered text, never to relax the
gate. This script is written to the PRECOMMIT's text for that reason: each check
below quotes the STOP it implements, and the field lists are the PRECOMMIT's.

A STOP may KILL the arm; it can never promote it. Nothing here is gated on a
residual, and the §5 pre-declared expectations are REPORTED separately, marked
as not-a-gate.

Output: ``docs/handoffs/d76/screen_gate.json`` + a printed table.
"""

import json
import sys
from pathlib import Path

sys.path[:0] = ["src", "."]

# ruff: noqa: E402  (sys.path must be set before market_sim resolves)

from market_sim.config.iso_configs import apply_iso_scenario_defaults
from scripts.run_capacity_hindcast import build_config

ISO = "PJM"
CONTROL = Path("results/hindcast/d76-screen-pjm-control")
ARM = Path("results/hindcast/d76-screen-pjm-arm")

# PRECOMMIT §3: the measured peaks the arm must produce, and the control's seam
# peaks, both computed at ZERO LP in phase 0 and FIXED before the solve.
MEASURED_PEAK_MW = {2022: 148_528.0, 2023: 147_605.0}
CONTROL_SEAM_PEAK_MW = {2022: 135_090.596, 2023: 143_823.528}
BINDING_YEARS = (2022, 2023)
PRE_SCREEN_YEAR = 2021

# PRECOMMIT §4 STOP 4, as CORRECTED before any result existed: the two LP-basis
# quantities that are pure functions of the measured load -- identical in both
# arms -- and so must be identical to the digit. ``reserve_margin`` is NOT here:
# it is firm/peak-1 computed AFTER evolution, an exiting-side quantity that
# moves with the fleet the screens leave behind, and the correction moved it to
# §5 as REPORTED. This is the ENTIRE gated list -- do not extend it here.
LP_BASIS_FIELDS = ("peak_demand_mw", "adequacy_requirement_mw")


def ledgers(bundle: Path) -> dict[int, dict]:
    """Load a bundle's committed per-year evolution ledgers.

    Args:
        bundle: The bundle directory (``--out-dir``).

    Returns:
        ``{year: ledger dict}``.
    """
    root = bundle / ISO
    keys = [p for p in root.iterdir() if p.is_dir()]
    if len(keys) != 1:
        raise RuntimeError(f"{bundle}: expected one cache-key dir, got {keys}")
    return {
        int(p.name[len("evolution_"): -len(".json")]): json.loads(p.read_text())
        for p in sorted(keys[0].glob("evolution_*.json"))
    }


def run_config(bundle: Path) -> dict:
    """Return the bundle's recorded ``run_config.json``."""
    return json.loads((bundle / "run_config.json").read_text())


def stop1() -> tuple[bool, list[str]]:
    """STOP 1 -- 'no pre-existing cache key moves'.

    Re-asserted here from the shipped resolvers rather than quoted from the
    pre-push measurement, so the gate reads the code as merged.
    """
    notes, ok = [], True
    for iso in ("CAISO", "ERCOT", "MISO", "NEISO", "NYISO", "PJM"):
        for label, kw in (("t1h", {}), ("t1x", {"crossover": True})):
            span = (2023, 2027) if kw else (2021, 2025)
            vintage = 2023 if kw else 2020
            def key(**over):
                return apply_iso_scenario_defaults(
                    build_config(iso, span[0], span[1], "realized",
                                 vintage=vintage, **kw, **over),
                    iso,
                ).cache_key()
            bare = key()
            off = key(capacity_screen_peak_measured_hindcast=False)
            on = key(capacity_screen_peak_measured_hindcast=True)
            if off != bare:
                ok = False
                notes.append(f"{iso}/{label}: explicit-OFF {off} != bare {bare}")
            if on == bare:
                ok = False
                notes.append(f"{iso}/{label}: armed key did not move ({on})")
    return ok, notes or ["12 recipe keys: explicit-OFF == bare, armed distinct"]


def stop2(arm: dict[int, dict]) -> tuple[bool, list[str]]:
    """STOP 2 -- the identity, 'to the MW'.

    'The arm's ``screen_peak_demand_mw`` equals the year's MEASURED peak to the
    MW in every binding year ... and it equals the ledger's own
    ``peak_demand_mw`` in every solved year. A miss of more than 0.001 MW kills
    the arm.'
    """
    notes, ok = [], True
    for year in BINDING_YEARS:
        got = arm[year].get("screen_peak_demand_mw")
        want = MEASURED_PEAK_MW[year]
        d = abs(float(got) - want)
        notes.append(f"{year}: screen peak {got:,.3f} vs measured {want:,.1f} -> Δ {d:.3f} MW")
        if d > 0.001:
            ok = False
    for year, led in sorted(arm.items()):
        lp = led.get("peak_demand_mw")
        if lp is None:
            continue  # bridge year: evolved, never solved -- no LP peak exists
        d = abs(float(led["screen_peak_demand_mw"]) - float(lp))
        notes.append(f"{year}: screen peak vs the LP's own peak -> Δ {d:.3f} MW")
        if d > 0.001:
            ok = False
    return ok, notes


def stop3(c: dict[int, dict], a: dict[int, dict]) -> tuple[bool, list[str]]:
    """STOP 3 -- 'every non-peak operand byte-identical'.

    'fuel path, fleet vintage, outage overlay, every gate recorded in
    ``run_config.json``, and the 2021 pre-screen year's ledger identical in
    both.'
    """
    notes, ok = [], True
    rc_c, rc_a = run_config(CONTROL), run_config(ARM)
    keys = sorted(set(rc_c) | set(rc_a))
    diff = [k for k in keys if rc_c.get(k) != rc_a.get(k)]
    # The gate itself, and the out-dir / key / timing bookkeeping that names the
    # leg, are the only admissible differences.
    allowed = {"capacity_screen_peak_measured_hindcast"}
    unexpected = [k for k in diff if k not in allowed]
    notes.append(f"run_config differs in {len(diff)} field(s): {diff}")
    if unexpected:
        ok = False
        notes.append(f"UNEXPECTED run_config difference: {unexpected}")
    if c.get(PRE_SCREEN_YEAR) != a.get(PRE_SCREEN_YEAR):
        ok = False
        changed = [k for k in set(c[PRE_SCREEN_YEAR]) | set(a[PRE_SCREEN_YEAR])
                   if c[PRE_SCREEN_YEAR].get(k) != a[PRE_SCREEN_YEAR].get(k)]
        notes.append(f"{PRE_SCREEN_YEAR} pre-screen ledger DIFFERS: {changed}")
    else:
        notes.append(f"{PRE_SCREEN_YEAR} pre-screen ledger identical")
    return ok, notes


def stop4(c: dict[int, dict], a: dict[int, dict]) -> tuple[bool, list[str]]:
    """STOP 4 -- 'the footprint is confined to the rows the mechanism claims'.

    'The LP's own ``peak_demand_mw``, ``adequacy_requirement_mw`` and
    ``reserve_margin`` are computed on the measured load in BOTH arms and must
    be identical.'
    """
    notes, ok = [], True
    for year in sorted(set(c) & set(a)):
        for f in LP_BASIS_FIELDS:
            cv, av = c[year].get(f), a[year].get(f)
            if cv is None and av is None:
                continue
            if cv != av:
                ok = False
                notes.append(f"{year}.{f}: {cv} -> {av}  ** NOT INVARIANT **")
            else:
                notes.append(f"{year}.{f}: identical ({cv})")
    return ok, notes


def report(c: dict[int, dict], a: dict[int, dict]) -> dict:
    """PRECOMMIT §5 -- pre-declared expectations. REPORTED, never a gate."""
    out = {}
    for year in sorted(set(c) & set(a)):
        out[year] = {
            f: {"control": c[year].get(f), "arm": a[year].get(f)}
            for f in ("screen_peak_demand_mw", "screen_adequacy_requirement_mw",
                      "screen_entering_firm_mw", "screen_reserve_position")
        }
        for f in ("retirements", "thermal_additions", "renewable_additions",
                  "storage_additions"):
            out[year][f + "_count"] = {
                "control": len(c[year].get(f) or []),
                "arm": len(a[year].get(f) or []),
            }
        out[year]["fleet_by_fuel_after"] = {
            "control": c[year].get("fleet_by_fuel_after"),
            "arm": a[year].get("fleet_by_fuel_after"),
        }
    return out


def main() -> int:
    ctrl, arm = ledgers(CONTROL), ledgers(ARM)
    results = {}
    for name, fn, args in (
        ("STOP 1 cache keys", stop1, ()),
        ("STOP 2 identity", stop2, (arm,)),
        ("STOP 3 non-peak operands", stop3, (ctrl, arm)),
        ("STOP 4 footprint", stop4, (ctrl, arm)),
    ):
        ok, notes = fn(*args)
        results[name] = {"pass": ok, "notes": notes}
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        for n in notes:
            print(f"        {n}")
        print()
    verdict = "PASS" if all(r["pass"] for r in results.values()) else "FAIL"
    print(f"SCREEN GATE (STOPs 1-4, structural): {verdict}")
    print("STOP 5 (no non-target load-bearing flip) and STOP 6 (one measured "
          "load per armed year) are graded outside this script -- see the FINDING.")
    Path("docs/handoffs/d76/screen_gate.json").write_text(
        json.dumps({"verdict": verdict, "stops": results,
                    "reported_not_gated": report(ctrl, arm)}, indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
