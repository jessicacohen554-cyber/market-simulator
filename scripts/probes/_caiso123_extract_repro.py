"""caiso-123 drift-attribution probe: keeper recipe at HEAD code with a
pinned CAISO unit-outage extract state.

Solves the ``caiso_netrev_margin`` keeper recipe (via
``replay_keeper.build_kwargs`` — the only sanctioned recipe reconstruction)
with ``market_sim.data.outages.unit_outage_csv_for_iso`` pointed at an
arbitrary on-disk copy of ``campd-unit-outages-CAISO.csv``, WITHOUT touching
``data/raw/`` (immutable). This is the caiso-122 §5 "diff the constructed
inputs, then solve once to confirm" confirmation step: the input diff
identified the 642 in-window rows inserted by PR #2844 (merge ``c95f98c``)
as the only CAISO-solve-relevant data change in the drift window, so the
keeper-era extract blob (``git show c95f98c^:data/raw/campd-unit-outages-
CAISO.csv``, blob ``e40847c``) at HEAD code should reproduce the keeper's
2025 λ if — and only if — the attribution is right.

Throwaway diagnostic probe (rule 16 single-year clause): out-dirs default
under the gitignored ``results/probes/``; never registered.

Usage:
    .venv/bin/python scripts/probes/_caiso123_extract_repro.py \
        --extract /path/to/extract_state.csv \
        --out-dir results/probes/caiso123_keeper_extract --years 2025
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

# replay_keeper pins MARKET_SIM_WARMSTART_XYEAR=0 at import time (before it
# imports run_calibration_full), which this probe inherits for byte
# comparability with the cold-solved committed keeper.
import replay_keeper  # noqa: E402
import run_calibration_full as rcf  # noqa: E402

KEEPER_BUNDLE = REPO / "results" / "calibration" / "caiso_netrev_margin"


def main() -> None:
    """Solve the keeper recipe with the outage extract pinned to a file."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--extract",
        default=None,
        help="path to the campd-unit-outages-CAISO.csv content to solve on "
        "(default: the repo HEAD file, i.e. a plain same-HEAD control)",
    )
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2025])
    ap.add_argument("--note", default=None)
    args = ap.parse_args()

    if args.extract is not None:
        extract = Path(args.extract).resolve()
        if not extract.is_file():
            raise SystemExit(f"--extract {extract}: not a file")
        import market_sim.data.outages as outages

        # unit_outage_derate_factors resolves unit_outage_csv_for_iso from
        # the outages module globals (single call site), so this rebind pins
        # every ISO=CAISO read of the extract for the whole process. Non-CAISO
        # ISOs keep the real path resolution.
        real = outages.unit_outage_csv_for_iso

        def _pinned(iso: str | None) -> Path:
            if (iso or "").upper() == "CAISO":
                return extract
            return real(iso)

        outages.unit_outage_csv_for_iso = _pinned
        print(f"pinned CAISO unit-outage extract -> {extract}")

    meta = json.loads((KEEPER_BUNDLE / "meta.json").read_text())
    kwargs = replay_keeper.build_kwargs(meta)
    kwargs["years"] = [int(y) for y in args.years]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(args.out_dir)
    kwargs["note"] = args.note or (
        "caiso-123 drift-attribution probe: keeper recipe at HEAD with the "
        f"CAISO unit-outage extract pinned to {args.extract or 'HEAD bytes'}"
    )
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
