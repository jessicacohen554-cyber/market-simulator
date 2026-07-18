"""Driver: CAISO offer-curve probe/baseline runner (caiso 38 recipe + delta).

Reproduces the caiso 38 (caiso38_delivered_gas) keeper recipe verbatim and lets a
caller layer an ``offer_curve_deltas`` band move on top, so the offer-curve
Jacobian can be re-derived on the current (citygate-gas) baseline. Every caiso 38
lever is carried verbatim; the ONLY thing that varies between invocations is the
offer-curve band delta (and the out-dir / years).

Usage:
  python scripts/archive/run_caiso_offer_probe.py OUT_DIR YEAR[,YEAR...] [DELTA_JSON]

  DELTA_JSON is an optional ``offer_curve_deltas`` dict, e.g.
  '{"CC_REGULAR": {"econ_high": -0.05}}'. Omit (or pass '{}') for the baseline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import (  # noqa: E402
    _load_reference,
    report_run,
    solve_and_persist,
)


def main() -> int:
    out_dir = Path(sys.argv[1])
    years = [int(y) for y in sys.argv[2].split(",")]
    deltas = json.loads(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else {}
    reference = _load_reference()
    run_dir = solve_and_persist(
        years,
        "CAISO",
        8760,
        reference,
        commitment=False,
        screen_coal=True,
        run_dir=out_dir,
        outage_source="historic",
        coal_prb_passthrough=1.0,
        coal_prb_passthrough_sigmoid=True,
        coal_mustrun_per_plant=True,
        coal_drop_pof=True,
        coal_prb_passthrough_tiered=True,
        priced_interchange=True,
        caiso_reference_price_seam=True,
        caiso_per_hub_intertie=False,
        caiso_corridor_atc_forward=True,
        offer_curve_deltas=deltas or None,
        note=(
            "caiso offer-curve probe on the caiso 38 (citygate delivered-gas) "
            f"baseline; offer_curve_deltas={json.dumps(deltas)}. All caiso 38 "
            "levers carried verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
