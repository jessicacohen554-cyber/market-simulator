"""SCN-WS1b Phase 0 — zero-LP census behind the PRECOMMIT (rule 29 [R-SCREEN] step 0).

Establishes, WITHOUT solving anything, the per-ISO facts the PRECOMMIT's expected
sign / magnitude / footprint predictions rest on:

  1. The resolved carbon signal in 2026 under REF and under the reduced arm
     ``--set carbon_price_delta=25`` — the proof that the arm is a genuine
     +$25/t INCREASE in every one of the six ISOs (which a ``carbon_price_path``
     arm would not be: SCN-WS1a proved it is a CUT of $16-$102/t on
     CAISO/NYISO/NEISO, FINDING-scn-ws1a-2026-09-05.md §0.1).
  2. The marginal fossil CO2 rates the price prediction multiplies against.
  3. Which ISOs carry an import node at all — i.e. which ones CAN leak, and
     which ones must read ``import_co2_mt_reported`` = 0.0 by construction
     (SCN-WS0's leakage duty, FINDING-scn-ws0-2026-09-05.md §5 item 2).
  4. The CCS retrofit availability year, which decides whether the T0 (2026)
     can show a retrofit response at all.

Run:  PYTHONPATH=src python docs/handoffs/scn-ws1b/phase0-census-2026-09-06.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.model.interchange.import_nodes import build_import_generators  # noqa: E402
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.results.emissions import import_tranche_ef  # noqa: E402
from scripts.run_full_horizon import reference_config  # noqa: E402

ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]
YEARS = [2026, 2027, 2028, 2029, 2030]
DELTA = 25.0


def base_config(iso: str, start: int = 2026, end: int = 2030):
    """The campaign REF posture for one ISO, built by the runner's OWN builder.

    ``reference_config(..., cmc=False)`` is exactly what
    ``scripts/run_full_horizon.py`` constructs for the REF arm, so this census
    reads the config the solves will actually receive, not a reconstruction.
    """
    return reference_config(iso, start, end, False)


def main() -> int:
    out: dict = {"delta": DELTA, "years": YEARS, "isos": {}}

    print("=" * 78)
    print("1. RESOLVED CARBON SIGNAL, $/tCO2 — REF vs the reduced arm (delta=+25)")
    print("=" * 78)
    header = f"{'ISO':7s} {'arm':5s} " + " ".join(f"{y:>8d}" for y in YEARS)
    print(header)
    for iso in ISOS:
        ref = base_config(iso)
        arm = replace(ref, carbon_price_delta=DELTA)
        ref_p = [resolve_carbon_price(ref, y) for y in YEARS]
        arm_p = [resolve_carbon_price(arm, y) for y in YEARS]
        print(f"{iso:7s} {'REF':5s} " + " ".join(f"{p:8.4f}" for p in ref_p))
        print(f"{iso:7s} {'ARM':5s} " + " ".join(f"{p:8.4f}" for p in arm_p))
        print(
            f"{iso:7s} {'DELTA':5s} "
            + " ".join(f"{a - r:8.4f}" for a, r in zip(arm_p, ref_p))
        )
        out["isos"][iso] = {
            "ref_carbon": dict(zip(map(str, YEARS), ref_p)),
            "arm_carbon": dict(zip(map(str, YEARS), arm_p)),
            "delta_carbon": dict(zip(map(str, YEARS), [a - r for a, r in zip(arm_p, ref_p)])),
            "state_carbon_pricing": bool(getattr(ref, "state_carbon_pricing", False)),
            "carbon_price_path": getattr(ref, "carbon_price_path", None),
            "policy_bundle": getattr(ref, "policy_bundle", None),
            "ccs_retrofit_available_year": getattr(ref, "ccs_retrofit_available_year", None),
        }

    print()
    print("=" * 78)
    print("2. ZONES, IMPORT NODES AND THE LEAKAGE SURFACE (which ISOs CAN leak)")
    print("=" * 78)
    for iso in ISOS:
        ic = get_iso_config(iso)
        zones = list(getattr(ic, "zones", []) or [])
        znames = [getattr(z, "name", str(z)) for z in zones]
        import_zones = [
            n for n in znames if "import" in n.lower() or n in ("HQ_import", "WECC_import")
        ]
        out["isos"][iso]["zones"] = znames
        out["isos"][iso]["import_zones"] = import_zones
        print(f"{iso:7s} zones={len(znames):2d} import_zones={import_zones or '[]'}")
        print(f"{'':7s} {znames}")

    print()
    print("=" * 78)
    print("3. CCS retrofit availability year (decides whether a 2026 T0 can respond)")
    print("=" * 78)
    for iso in ISOS:
        print(f"{iso:7s} ccs_retrofit_available_year={out['isos'][iso]['ccs_retrofit_available_year']}")

    print()
    print("=" * 78)
    print("4. THE LEAKAGE SURFACE — every import pseudo-generator and its REPORTED EF")
    print("=" * 78)
    print("(EF is the disclosure-line factor results.emissions.import_tranche_ef")
    print(" returns; the LP itself holds every import emission_rate at zero.)")
    for iso in ISOS:
        gens = build_import_generators(iso, border_carbon_per_mwh=0.0, year=2026)
        rows = []
        for g in gens:
            uid = getattr(g, "unit_id", getattr(g, "name", "?"))
            zone = getattr(g, "zone", "?")
            cap = float(getattr(g, "pmax_mw", 0.0) or 0.0)
            vom = float(getattr(g, "vom", 0.0) or 0.0)
            ef = import_tranche_ef(uid, zone)
            rows.append({"unit_id": uid, "zone": zone, "capacity_mw": cap,
                         "vom": vom, "reported_ef_t_per_mwh": ef})
        out["isos"][iso]["import_tranches"] = rows
        carbon_bearing = [r for r in rows if r["reported_ef_t_per_mwh"] > 0 and r["capacity_mw"] > 0]
        out["isos"][iso]["n_carbon_bearing_import_tranches"] = len(carbon_bearing)
        print(f"\n{iso}: {len(rows)} import pseudo-generators, "
              f"{len(carbon_bearing)} carbon-bearing")
        for r in rows:
            print(f"   {r['unit_id']:38s} zone={r['zone']:15s} "
                  f"cap={r['capacity_mw']:8.1f} vom={r['vom']:8.2f} EF={r['reported_ef_t_per_mwh']:.3f}")
        if not rows:
            print("   (none — this ISO has NO import node: its reported import CO2 "
                  "line is 0.0 by construction)")

    dest = Path(__file__).with_suffix(".json")
    dest.write_text(json.dumps(out, indent=2, sort_keys=True))
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
