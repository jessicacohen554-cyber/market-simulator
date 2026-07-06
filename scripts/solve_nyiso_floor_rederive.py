"""One-delta gate solves for the NYISO CT/ST reliability-floor re-derivation.

Replays the nyiso-41 keeper meta.json at HEAD (so it inherits HEAD's de-leaked
offer curve, exactly like nyiso-48 head-regate — the one-delta baseline) under
the re-derived floors now on disk:

  * NYC CT_PEAKER 24h hot step (tmax 31.7 / 0.1833) DISABLED (r1_disabled) in
    data/raw/reference/reliability_floor_coeffs_NYISO.csv — the D-4 off-window
    binder; one mechanism per phenomenon is the windowed NYC_CT_ev ramp.
  * Long Island local self-supply floor NARROWED to the HB14-21 peak window
    (transmission.NYISO_SELFSUPPLY_FLOOR_HOURS) — no overnight forcing.

Two configs, selected by --config:
  * ``floors``    — re-derived floors alone.
  * ``floors_gas``— re-derived floors + nyiso_downstate_ct_gas_basis=True
                    (the PR #1427 delivered-fuel input, kept default-off).

Usage:
  python scripts/solve_nyiso_floor_rederive.py --config floors      [--years 2024]
  python scripts/solve_nyiso_floor_rederive.py --config floors_gas  [--years 2024]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import replay_keeper as rk  # noqa: E402
import run_calibration_full as rcf  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "nyiso41_hubprices"
OUT_BY_CONFIG = {
    "floors": REPO / "results" / "calibration" / "nyiso51_floor_rederive",
    "floors_gas": REPO / "results" / "calibration" / "nyiso52_floor_rederive_ctgas",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", choices=list(OUT_BY_CONFIG), required=True)
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = args.years or [int(y) for y in meta["years"]]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    out = Path(args.out_dir) if args.out_dir else OUT_BY_CONFIG[args.config]
    kwargs["run_dir"] = out

    note = (
        "NYISO CT/ST reliability-floor re-derivation (rule 17/18/23): NYC CT 24h "
        "hot step disabled (D-4 off-window binder) + LI local self-supply narrowed "
        "to the HB14-21 peak window. One-delta vs nyiso-48 head-regate."
    )
    if args.config == "floors_gas":
        kwargs.setdefault("prb_overrides", {})["nyiso_downstate_ct_gas_basis"] = True
        note += " + nyiso_downstate_ct_gas_basis=True (PR #1427 delivered-fuel input)."
    kwargs["note"] = note

    print(f"solving {out.name} [{args.config}] years {kwargs['years']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
