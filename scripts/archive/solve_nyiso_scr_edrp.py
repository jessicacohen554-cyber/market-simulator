"""nyiso-65 keeper solve: the nyiso-64 recipe + SCR/EDRP demand response.

Replays the nyiso-62 keeper meta.json (the authoritative recipe snapshot) at
HEAD, so it inherits the on-disk corrected state that defines nyiso-64:

  * the corrected 2,641-row ``campd-unit-outages-NYISO.csv`` extract
    (``scripts/data/derive_campd_unit_outages.py --iso NYISO``) + the ST
    reliability-floor coefficients re-derived on it (already committed), and
  * the eastern AC seam landing split (``IMPORT_NODE_LINKS`` Capital_Hudson
    1,600 MW) — a code change already on main.

and ADDS the single new lever:

  * ``nyiso_scr_edrp=True`` — NYISO SCR/EDRP emergency demand response as
    price-responsive supply blocks (data.nyiso_demand_response). One block per
    model zone at the published EDRP compensation-floor strike ($500/MWh); it
    clears the energy balance endogenously in the scarcity tail, replacing the
    invented downstate VOLL prints. Rule-13/17-admissible structural lever
    (Gold-Book-registered capability, market-design strike, forward story).

Everything else (offer curves, LI/NYC LCR-TSL, downstate CT gas basis/daily,
measured plant CO2 rates v2, reserve co-opt, gas hub basis) is the nyiso-64
recipe carried verbatim through the meta replay — no residual tuning.

Usage:
  python scripts/solve_nyiso_scr_edrp.py [--years 2023 2024 2025] [--out-dir DIR]
  python scripts/solve_nyiso_scr_edrp.py --dry-run   # build kwargs only, no solve
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import replay_keeper as rk  # noqa: E402
import run_calibration_full as rcf  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "nyiso62_cc_hr_regate"
DEFAULT_OUT = REPO / "results" / "calibration" / "nyiso65_scr_edrp"


def build() -> dict:
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    # The new lever — a dedicated solve_and_persist gate (not an off-registry
    # channel): threads to run_year -> config.nyiso_scr_edrp -> the DR fleet
    # build. Strike stays at the ScenarioConfig default ($500/MWh EDRP floor).
    kwargs["nyiso_scr_edrp"] = True
    kwargs["note"] = (
        "nyiso-65: nyiso-64 corrected-envelope recipe (2,641-row outage "
        "extract + re-derived ST floors + eastern AC seam Capital_Hudson "
        "1,600 MW) + SCR/EDRP demand response (nyiso_scr_edrp, $500/MWh EDRP "
        "strike) as endogenous price-responsive supply blocks replacing the "
        "invented downstate VOLL prints. Rule-13/17-admissible; no residual tuning."
    )
    return kwargs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--out-dir", default=None)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and print the replayed kwargs (no solve).",
    )
    args = ap.parse_args()

    kwargs = build()
    kwargs["years"] = args.years
    out = Path(args.out_dir) if args.out_dir else DEFAULT_OUT
    kwargs["run_dir"] = out

    if args.dry_run:
        printable = {k: v for k, v in kwargs.items() if k not in ("reference",)}
        print(json.dumps(printable, indent=1, default=str))
        return

    kwargs["reference"] = rcf._load_reference()
    print(f"solving {out.name} years {kwargs['years']} (nyiso_scr_edrp=True)")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
