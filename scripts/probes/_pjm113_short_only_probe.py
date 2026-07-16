"""pjm-113 probe driver: the pjm-111 keeper recipe + LEG A ONLY (short windows).

Owner-requested isolation run (2026-07-15): pjm-112 armed BOTH measured
unit-availability legs (short full stops + unit-grain partial derates) and
missed the C3c gate #1 by +8 h. This run isolates the STRONG, unambiguous leg —
LEG A, the short (<5-day) baseload-coal full-stop overlay on the corrected
when-operable guard (1314 of the 1502 MW recovered in the summer tail hours) —
by omitting the more debatable LEG B partial-derate overlay, to see whether
leg A alone is the cleaner keeper-worthy structural improvement.

Replays the pjm-111 keeper via replay_keeper.build_kwargs and applies EXACTLY
ONE flag on top (via prb_overrides):

    ScenarioConfig.unit_outage_short_windows : False -> True   (LEG A only)

unit_partial_outage_windows is deliberately LEFT OFF (default False). Same
already-derived campd-unit-outages-short-PJM.csv, same recipe, zero constants
touched. docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md §7-8.

Usage:
    python scripts/probes/_pjm113_short_only_probe.py \
        [--bundle results/calibration/pjm111_cc_reconcile] \
        [--out-dir results/calibration/pjm113_short_only] \
        [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import replay_keeper as rk  # noqa: E402
import run_calibration_full as rcf  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--bundle",
        type=Path,
        default=REPO / "results" / "calibration" / "pjm111_cc_reconcile",
        help="base keeper bundle whose meta.json supplies the recipe",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=REPO / "results" / "calibration" / "pjm113_short_only",
    )
    ap.add_argument("--years", nargs="*", type=int, default=None)
    args = ap.parse_args()

    meta = json.loads((args.bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["iso"] = meta["iso"]
    kwargs["years"] = [int(y) for y in (args.years or meta["years"])]
    kwargs["hours"] = int(meta.get("hours", 8760))
    rcf.enforce_holdout_year_gate(kwargs["years"], kwargs["iso"], False)
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = args.out_dir
    # --- pjm-113 delta: LEG A only. Partial overlay deliberately left OFF. ---
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"]["unit_outage_short_windows"] = True
    # NB: unit_partial_outage_windows intentionally NOT set (stays default False).
    kwargs["note"] = (
        "PJM 113: the pjm-111 CC-reconcile keeper recipe with EXACTLY the LEG A "
        "measured unit-availability overlay armed — unit_outage_short_windows "
        "(short < 5-day baseload-coal full stops, re-derived on the when-operable "
        "baseload guard). The unit-grain partial-derate overlay "
        "(unit_partial_outage_windows) is deliberately LEFT OFF to isolate the "
        "strong, unambiguous structural leg (1314 of the 1502 MW recovered in the "
        "22 summer tail hours) from the more debatable partial-derate detection. "
        "Owner-requested isolation run vs pjm-112 (both legs). Zero fitted "
        "scalars; same already-derived short PJM extract, no constant touched. "
        "docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md §7-8."
    )

    print(f"solving {kwargs['iso']} {kwargs['years']} -> {kwargs['run_dir']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
