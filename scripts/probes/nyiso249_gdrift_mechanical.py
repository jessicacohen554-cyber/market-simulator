"""nyiso-249 — G-DRIFT-M: execute the one live-path hunk instead of reading it.

ZERO LP (rule 32 ``[R-SHARD]`` (a)). PRECOMMIT section 2.5.

The rule 29 ``[R-SCREEN]`` (b) form-4 audit classified all six files changed
between the keeper's basis sha ``42d75053`` and ``origin/main`` as INERT. Five of
the six are inert on grounds that need no execution (another ISO's registry key,
a gated branch, a new function with one gated caller, three default-``False``
fields absent from the keeper's recipe).

**One is not.** ``data/fleet/arrays.py``'s CHP min-gen hunk sits on a path NYISO
**does** execute -- the keeper's fleet carries CC_CHP, CT_CHP and ST_CHP rows --
and its inertness rests on a *value*: every generator must carry
``chp_grid_pmin_on_frac == 1.0``, which sends the loop through the branch that
executes the identical pre-change statement. Reading a branch is weaker than
executing it, so this executes it.

Four assertions, all of which must hold or form 4 is void and a control solve is
earned:

    1. config.chp_steam_duty_window            is False
    2. config.coal_mustrun_requires_measured_row is False
    3. config.vre_reference_rate_year_own      is False
    4. every assembled generator has chp_grid_pmin_on_frac == 1.0

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso249_gdrift_mechanical.py --year 2023
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "calibration" / "_nyiso249_gdrift_mechanical.json"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=[2023])
    args = ap.parse_args()

    from scripts.probes.nyiso242_tail_reachability import fleet_state

    result: dict = {"gate": "G-DRIFT-M", "session": "nyiso-249", "years": {}}
    all_ok = True

    for year in args.year:
        st = fleet_state(year)
        cfg, fleet = st["config"], st["fleet"]
        gens = getattr(fleet, "generators", fleet)
        fracs = [float(getattr(g, "chp_grid_pmin_on_frac", 1.0)) for g in gens]
        chp_rows = sum(1 for g in gens if float(getattr(g, "chp_grid_pmin_mw", 0.0)) > 0)
        checks = {
            "chp_steam_duty_window_is_False": (
                getattr(cfg, "chp_steam_duty_window", False) is False
            ),
            "coal_mustrun_requires_measured_row_is_False": (
                getattr(cfg, "coal_mustrun_requires_measured_row", False) is False
            ),
            "vre_reference_rate_year_own_is_False": (
                getattr(cfg, "vre_reference_rate_year_own", False) is False
            ),
            "every_gen_chp_on_frac_is_1.0": all(f == 1.0 for f in fracs),
        }
        ok = all(checks.values())
        all_ok &= ok
        result["years"][str(year)] = {
            "n_generators": len(fracs),
            "n_with_chp_grid_pmin_mw_gt0": chp_rows,
            "min_chp_on_frac": min(fracs) if fracs else None,
            "max_chp_on_frac": max(fracs) if fracs else None,
            "checks": checks,
            "passed": ok,
        }
        print(f"{year}: gens={len(fracs)} chp_floored={chp_rows} "
              f"on_frac=[{min(fracs):.4f}, {max(fracs):.4f}] -> {'PASS' if ok else 'FAIL'}")
        for k, v in checks.items():
            print(f"    {'OK ' if v else 'FAIL'} {k}")

    result["form4_valid"] = bool(all_ok)
    print(f"\nG-DRIFT-M: form 4 valid = {all_ok}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
