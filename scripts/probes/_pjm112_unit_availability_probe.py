"""pjm-112 probe driver: the pjm-111 keeper recipe + the completed measured
unit-availability overlay (the C3c summer-tail solve).

Replays the ``pjm111_cc_reconcile`` keeper byte-faithfully via
``replay_keeper.build_kwargs`` (its meta.json carries the full pjm-105/107/110/
111 flag stack — gas_daily_shape, the CC-capacity reconcile, the measured
interface/seam ladders, the offer surface, etc.) and applies EXACTLY the two
measured unit-availability flags on top, via the generic ``prb_overrides``
channel:

    ScenarioConfig.unit_outage_short_windows   : False -> True   (LEG A)
    ScenarioConfig.unit_partial_outage_windows : False -> True   (LEG B)

LEG A arms the existing short (< 5-day) baseload-coal full-stop overlay for PJM,
now derived on the WHEN-OPERABLE baseload guard (a unit with a documented
multi-month outage is baseload by its running capability — the identification
correction cited to docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md §7, not to a
price residual). LEG B adds the new unit-grain partial-derate plateau overlay
(the plant-level partial detector's frozen constants, run at unit grain, the
same when-operable guard + in-merit filter). Both read the PJM per-ISO extracts
(campd-unit-outages-short-PJM.csv, campd-partial-outages-PJM.csv); ERCOT's
plant-grain partial path is untouched. Zero fitted scalars — measured physical
availability events, forecast-native (WEFOR/derate-rate analogue), the miso-66
"by construction" precedent (rules 1/13/20/23).

Build-time provenance (gate #4, verified BEFORE this solve):
scripts/probes/_pjm112_provenance_check.py — the two extracts recover 1502 MW
mean across the 22 summer 2025 DA-tail hours (>= 800 MW required).

Usage:
    python scripts/probes/_pjm112_unit_availability_probe.py \
        [--bundle results/calibration/pjm111_cc_reconcile] \
        [--out-dir results/calibration/pjm112_unit_availability] \
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
        default=REPO / "results" / "calibration" / "pjm112_unit_availability",
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
    # --- pjm-112 delta: the two measured unit-availability flags on top of the
    #     pjm-111 replay. The prb_overrides channel (which build_kwargs already
    #     populated with the pjm-111 stack — gas_daily_shape, CC reconcile, ...)
    #     is the recorded override path; run_config records exactly what the LP
    #     solves with, so both flags must appear True there (the ERCOT-65
    #     lesson: prb_overrides stomps direct kwargs — verify the recorder).
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"]["unit_outage_short_windows"] = True
    kwargs["prb_overrides"]["unit_partial_outage_windows"] = True
    kwargs["note"] = (
        "PJM 112: the pjm-111 CC-reconcile keeper recipe (full pjm-105/107/110/"
        "111 flag stack via meta replay) with EXACTLY the two measured "
        "unit-availability overlays armed — unit_outage_short_windows (LEG A, "
        "short < 5-day baseload-coal full stops, re-derived on the when-operable "
        "baseload guard) and unit_partial_outage_windows (LEG B, new unit-grain "
        "partial-derate plateaus at the plant-level partial detector's frozen "
        "constants). Completes the measured unit-availability family for PJM at "
        "unit grain to recover the C3c summer-tail phantom coal (+3.0 GW in the "
        "22 Jun 23-25 / Jul 28-29 DA-tail hours the >= 5-day zero-run extract is "
        "blind to). Zero fitted scalars; build-time provenance 1502 MW >= 800 MW "
        "(gate #4). docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md §7-8."
    )

    print(f"solving {kwargs['iso']} {kwargs['years']} -> {kwargs['run_dir']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
