"""SCN-WS1b-r2 Phase 0 RE-CENSUS — the ``carbon_price_path=mid`` form, post-WS-1c.

Rule 29 [R-SCREEN] clause (0): the zero-LP gate an arm must clear BEFORE it
reaches a solve. The original census (``phase0-census-2026-09-06.py``) measured
the RETIRED reduced form ``carbon_price_delta=25``. The relaunch charter
replaces it with the charter's full form ``carbon_price_path=mid``, because
SCN-WS1c landed the D-1 FLOOR repair (``b1996141``): ``effective = max(RFF path,
program trajectory)``.

This instrument re-asks the ONE question that decides whether leg 1 may spend
LP at all: what is ``resolve_carbon_price(ARM, y) - resolve_carbon_price(REF, y)``
per ISO, under the repaired resolver, at the T0 year 2026?

Same builder as the solves (``run_full_horizon.reference_config(iso, ..., cmc=False)``),
so this is the config the arms would actually receive.

Run:  PYTHONPATH=. .venv/bin/python docs/handoffs/scn-ws1b/phase0-recensus-path-2026-09-06.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.fuel_trajectories import CARBON_PRICE_PATHS  # noqa: E402
from market_sim.policy.carbon import resolve_carbon_price, rff_path_price  # noqa: E402
from scripts.run_full_horizon import reference_config  # noqa: E402

ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]
YEARS = [2026, 2027, 2028, 2029, 2030]


def main() -> int:
    out: dict = {
        "form": "carbon_price_path=mid",
        "head_note": "post-SCN-WS1c floor repair b1996141",
        "rff_mid_knots": {str(k): v for k, v in CARBON_PRICE_PATHS["mid"].items()},
        "years": YEARS,
        "isos": {},
    }

    print("=" * 84)
    print("RFF 'mid' PATH KNOTS (config/fuel_trajectories.py CARBON_PRICE_PATHS)")
    print("=" * 84)
    print("  ", CARBON_PRICE_PATHS["mid"])
    print("  interpolated:", {y: round(rff_path_price("mid", y), 4) for y in YEARS})
    print()

    print("=" * 84)
    print("RESOLVED CARBON SIGNAL, $/tCO2 — REF vs ARM(carbon_price_path='mid')")
    print("=" * 84)
    print(f"{'ISO':7s} {'arm':6s} " + " ".join(f"{y:>9d}" for y in YEARS))
    for iso in ISOS:
        ref = reference_config(iso, 2026, 2030, False)
        arm = replace(ref, carbon_price_path="mid")
        ref_p = [resolve_carbon_price(ref, y) for y in YEARS]
        arm_p = [resolve_carbon_price(arm, y) for y in YEARS]
        dlt = [a - r for a, r in zip(arm_p, ref_p)]
        print(f"{iso:7s} {'REF':6s} " + " ".join(f"{p:9.4f}" for p in ref_p))
        print(f"{iso:7s} {'ARM':6s} " + " ".join(f"{p:9.4f}" for p in arm_p))
        print(f"{iso:7s} {'DELTA':6s} " + " ".join(f"{d:9.4f}" for d in dlt))
        print()
        out["isos"][iso] = {
            "ref_path": getattr(ref, "carbon_price_path", None),
            "policy_bundle": getattr(ref, "policy_bundle", None),
            "state_carbon_pricing": bool(getattr(ref, "state_carbon_pricing", False)),
            "ref_carbon": dict(zip(map(str, YEARS), ref_p)),
            "arm_carbon": dict(zip(map(str, YEARS), arm_p)),
            "delta_carbon": dict(zip(map(str, YEARS), dlt)),
            "delta_2026": dlt[0],
            "live_2026": abs(dlt[0]) > 1e-9,
        }

    print("=" * 84)
    print("THE 2026 T0 GATE — is the arm live at the screen year?")
    print("=" * 84)
    live = [i for i in ISOS if out["isos"][i]["live_2026"]]
    for iso in ISOS:
        d = out["isos"][iso]["delta_2026"]
        print(f"  {iso:7s} delta(2026) = {d:9.4f} $/tCO2   -> "
              f"{'LIVE' if abs(d) > 1e-9 else 'INERT (arms are identical configs)'}")
    print()
    print(f"  ISOs LIVE at 2026: {live if live else 'NONE — all six pairs are identical'}")
    out["live_2026_isos"] = live

    dest = Path(__file__).with_suffix(".json")
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"\nwrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
