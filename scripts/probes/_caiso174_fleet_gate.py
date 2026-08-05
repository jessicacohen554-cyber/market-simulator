"""caiso-174 — THE QUANTITY GATE. Run this BEFORE any price is read.

The caiso-162 standing lesson, which caiso-172 re-learned: **a ``run_config``
recording a mechanism as armed is NOT evidence the LP saw it.** This probe
verifies the two arms actually separate **on the fleet**, which is the quantity
the FFR-4D epoch field moves. If they do not separate, the session has a wiring
defect and must STOP rather than report a price result.

It walks the keeper's own storage chain — ``build_default_storage`` /
``load_eia860_storage`` → ``storage_units_to_arrays`` → ``storage_cap_profiles``
— at the keeper's own ``storage_vintage_ramp=True`` and
``caiso_storage_shape_anchor=True``, for each arm's resolved config. No LP, no
solve: this is arithmetic over the shipped storage path.

**PRECHECK DEPARTURE, recorded at first run (PRECHECK-caiso174 §4 was WRONG).**
§4 pre-registered the control at a flat **8,000 MW**. That is wrong, and this
probe found it before any price was read — which is what the gate is for.
**FFR-4D made TWO changes, and the precheck conflated them:**

1. it **re-vintaged the constant** ``STORAGE_BASE_FLEET_MW["CAISO"]``
   8,000 -> **15,450 MW** (mid) — always in effect, both modes, no flag; and
2. it **added** ``storage_measured_base_fleet`` — backcast-scoped, default-ON.

So a control at THIS head with the field off resolves the **new constant
(15,450)**, not the pre-epoch 8,000. The flat 8,000 exists only in the committed
keeper bundle, at a different HEAD, and **is not reproducible by any flag here**.
The corrected three-state ladder, which is what the finding decomposes:

===== ==================== ==================== =====================
year   keeper (PRE-epoch)   Arm A (new const)    Arm B (measured)
===== ==================== ==================== =====================
2023   flat 8,000.0         flat 15,450.0        7,492.4
2024   flat 8,000.0         flat 15,450.0        11,131.3
2025   flat 8,000.0         flat 15,450.0        15,448.4
===== ==================== ==================== =====================

**2025 is therefore expected to NEARLY COINCIDE between the arms** (15,450 vs
15,448.4, a 1.6 MW gap): FFR-4D set the constant to the 2025 measured value
rounded. That is a real property of the re-vintage, **not** a separation failure,
so the gate requires separation in **at least one** year rather than in every
year, and reports 2025's coincidence as a finding.

plus: Arm B's power-cap PROFILE is **2-D ``(6, 8760)`` and varies within the
year** (``storage_vintage_ramp`` live for batteries for the first time — it was a
DEAD FLAG while the fleet was a flat scalar, reaching pumped storage only), and
Arm B closes the ``caiso_storage_shape_caps`` basis mismatch (that envelope is a
per-MW-of-EIA-860-fleet rate multiplied by ``power_cap``; in Arm A the
denominator and the multiplicand are on different fleets).

Usage::

    PYTHONPATH=.:src python scripts/probes/_caiso174_fleet_gate.py
    PYTHONPATH=.:src python scripts/probes/_caiso174_fleet_gate.py --json out.json

Exit status is a REAL GATE here, unlike the reporting probes: non-zero if the
arms fail to separate as pre-registered.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
YEARS = (2023, 2024, 2025)

#: PRE-REGISTERED, from FFR-4D §5 (EIA-860 2025 Early Release). Year-end measured
#: CAISO battery fleet.
EXPECTED_TREATED_MW = {2023: 7492.4, 2024: 11131.3, 2025: 15448.4}

#: CORRECTED at first run — see the module docstring's PRECHECK DEPARTURE note.
#: FFR-4D made TWO changes, and PRECHECK-caiso174 §4 conflated them: it
#: re-vintaged the CONSTANT ``STORAGE_BASE_FLEET_MW["CAISO"]`` 8,000 -> 15,450 MW
#: (mid), AND it added the ``storage_measured_base_fleet`` field. So a control at
#: THIS head with the field off resolves the NEW constant (15,450), not the
#: pre-epoch 8,000. The flat 8,000 exists only in the committed keeper bundle,
#: which is a different HEAD and is not reproducible by a flag on this one.
EXPECTED_CONTROL_MW = 15450.0

#: The pre-epoch keeper's flat scalar. Recorded for the decomposition in §4 of
#: the finding; NOT reachable at this head by any flag.
PRE_EPOCH_KEEPER_MW = 8000.0

TOL_MW = 5.0


def _fleet_for(measured: bool, year: int) -> dict:
    """Resolve the CAISO storage fleet for one arm-year, MIRRORING THE RUNNER SEAM.

    This reproduces ``runner.py``'s ``measured_storage`` branch verbatim rather
    than approximating it: the measured leg calls ``load_eia860_storage`` (which
    appends pumped storage itself), the control leg calls
    ``build_default_storage`` and PREPENDS the EIA-860 PS fleet, exactly as the
    ``else`` branch does. Approximating the seam here would be the caiso-162
    failure mode in a new place — checking a quantity the solve does not use.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.storage import (
        build_default_storage,
        load_eia860_pumped_storage,
        load_eia860_storage,
        storage_units_to_arrays,
    )

    cfg = ScenarioConfig(
        iso="CAISO",
        mode="backcast",
        storage_measured_base_fleet=measured,
        storage_vintage_ramp=True,
        caiso_storage_shape_anchor=True,
        start_year=year,
        end_year=year,
    )
    iso_cfg = get_iso_config("CAISO")

    if measured:
        units = list(load_eia860_storage("CAISO", year, cfg))
    else:
        units = list(load_eia860_pumped_storage("CAISO", year, cfg)) + list(
            build_default_storage(iso_cfg, cfg)
        )

    def _is_battery(u) -> bool:
        return getattr(u, "tech_name", "") != "pumped_storage"

    batt_mw = sum(float(u.power_cap_mw) for u in units if _is_battery(u))
    tot_mw = sum(float(u.power_cap_mw) for u in units)

    zone_names = [z.name for z in iso_cfg.zones]
    arrays = storage_units_to_arrays(units, zone_names)

    # The 2-D vintage ramp is produced by storage_cap_profiles, NOT by
    # storage_units_to_arrays (whose power_cap is the flat per-unit vector).
    # Checking the wrong object here would be the caiso-162 failure mode in a
    # new place, so the profile is what the gate reads.
    from market_sim.model.storage import storage_cap_profiles

    power_prof, _energy_prof = storage_cap_profiles(units, arrays, 8760)
    shape = tuple(np.asarray(power_prof).shape)
    prof = np.asarray(power_prof, dtype=float)
    # "Ramped" means the profile actually varies within the year for at least one
    # unit — a 2-D array that is constant along the hour axis is still flat.
    varies = bool(prof.ndim == 2 and np.any(prof.max(axis=1) - prof.min(axis=1) > 1e-9))

    return {
        "battery_mw": round(batt_mw, 1),
        "total_mw": round(tot_mw, 1),
        "n_units": len(units),
        "n_battery_units": sum(1 for u in units if _is_battery(u)),
        "power_cap_profile_shape": shape,
        "power_cap_is_2d": len(shape) == 2,
        "power_cap_varies_within_year": varies,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    record: dict = {"probe": "caiso174_fleet_gate", "years": list(YEARS), "arms": {}}
    failures: list[str] = []

    print("=" * 78)
    print("caiso-174 QUANTITY GATE — do the arms separate ON THE FLEET?")
    print("(PRECHECK-caiso174 §4; run BEFORE any price is read)")
    print("=" * 78)
    print(f"{'year':6}{'arm':10}{'battery MW':>13}{'total MW':>11}{'units':>7}{'cap profile':>14}{'varies':>8}")

    for year in YEARS:
        for arm, measured in (("A control", False), ("B treated", True)):
            try:
                r = _fleet_for(measured, year)
            except Exception as exc:  # pragma: no cover - surfaced as a gate failure
                failures.append(f"{year} {arm}: resolution FAILED — {exc}")
                print(f"{year:<6}{arm:10}  RESOLUTION FAILED: {exc}")
                continue
            record["arms"].setdefault(str(year), {})[arm] = r
            print(
                f"{year:<6}{arm:10}{r['battery_mw']:>13,.1f}{r['total_mw']:>11,.1f}"
                f"{r['n_units']:>7}{str(r['power_cap_profile_shape']):>14}"
                f"{('yes' if r['power_cap_varies_within_year'] else 'flat'):>8}"
            )

            if measured:
                want = EXPECTED_TREATED_MW[year]
                if abs(r["battery_mw"] - want) > TOL_MW:
                    failures.append(
                        f"{year} treated battery {r['battery_mw']:,.1f} MW != "
                        f"pre-registered {want:,.1f} MW"
                    )
                if not r["power_cap_is_2d"]:
                    failures.append(
                        f"{year} treated power_cap profile is {r['power_cap_profile_shape']}, "
                        "expected 2-D (storage_vintage_ramp must be live for batteries)"
                    )
            else:
                if abs(r["battery_mw"] - EXPECTED_CONTROL_MW) > TOL_MW:
                    failures.append(
                        f"{year} control battery {r['battery_mw']:,.1f} MW != "
                        f"flat {EXPECTED_CONTROL_MW:,.1f} MW"
                    )

    # The separation itself — the point of the gate.
    print()
    print("separation (treated - control), battery MW:")
    for year in YEARS:
        a = record["arms"].get(str(year), {}).get("A control")
        b = record["arms"].get(str(year), {}).get("B treated")
        if not a or not b:
            continue
        d = b["battery_mw"] - a["battery_mw"]
        pct = 100.0 * d / b["battery_mw"] if b["battery_mw"] else float("nan")
        direction = "treated ABOVE control" if d > 0 else "treated BELOW control"
        print(f"  {year}  {d:>+10,.1f} MW  ({pct:>+6.1f}% of treated)   {direction}")
        record.setdefault("separation", {})[str(year)] = {
            "delta_mw": round(d, 1),
            "pct_of_treated": round(pct, 1),
        }
        if abs(d) < TOL_MW:
            # EXPECTED in 2025 — the re-vintaged constant IS the 2025 measured
            # value rounded. Reported, never a failure; the all-years check below
            # is what actually gates separation.
            print(
                f"        ^ arms coincide in {year}: the re-vintaged constant "
                f"({EXPECTED_CONTROL_MW:,.0f} MW) is the {year} measured fleet rounded. "
                "EXPECTED, not a defect."
            )
            record.setdefault("coincident_years", []).append(year)

    # The gate on separation: the arms must differ SOMEWHERE, not everywhere.
    deltas = [abs(v["delta_mw"]) for v in record.get("separation", {}).values()]
    if deltas and max(deltas) < TOL_MW:
        failures.append(
            f"arms do not separate in ANY year (max |delta| = {max(deltas):.1f} MW) "
            "— the field is not reaching the fleet"
        )

    print()
    if failures:
        print("=" * 78)
        print(f"GATE FAILED — {len(failures)} problem(s). This is a WIRING DEFECT; STOP.")
        print("=" * 78)
        for f in failures:
            print(f"  FAIL  {f}")
    else:
        print("=" * 78)
        print("GATE PASSED — the arms separate on the fleet exactly as pre-registered.")
        print("Proceed to the solve; prices may now be read.")
        print("=" * 78)
    record["failures"] = failures
    record["passed"] = not failures

    if args.json:
        args.json.write_text(json.dumps(record, indent=1, default=str))
        print(f"\nwrote {args.json}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
