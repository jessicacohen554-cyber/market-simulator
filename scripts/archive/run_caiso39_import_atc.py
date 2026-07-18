"""Driver: CAISO 39 — corridor forward-ATC re-grounding (import deliverability).

Builds on caiso 38 (caiso38_delivered_gas, the current keeper) with ONE change
and nothing else: the WECC corridor forward-ATC base fractions
(`CAISO_PER_HUB_NEIGHBORS`) are re-grounded to the measured per-(month ×
hour-of-day) p95 overnight net-import deliverability — PNW 0.30 -> 0.43, DSW
0.50 -> 0.56 — closing the import-ATC compression the caiso 38 finding exposed
(model import diurnal swing 2,321 MW vs actual 4,596 MW; the forward ATC ceiling
sat below actual peak deliverability). Every caiso 38 lever (offer curve, the
reference-price seam, the coal recipe, priced interchange, the citygate gas
overlay) is carried verbatim.

Why (caiso 38 finding §2 + this session's offer-curve + import diagnosis):

  The caiso 38 session established that the CAISO body over-price is NOT the gas
  offer curve (the CAMPD/DMM-grounded curve is spent; lowering CC bands only
  steals capped imports and barely moves price) and NOT the seam import PRICE
  (anchored to the measured Palo Verde/Malin hub means). It is the structural
  import-ATC: the model imports in ~98% of hours but cannot reach the measured
  high-import hours, its import diurnal swing compressed below actual peak
  deliverability.

  This session confirmed it hour-by-hour: the body over-price is concentrated
  MIDDAY (~$51 model vs ~$15 actual; the evening ramp is already accurate), where
  domestic gas-CC is marginal at its true ~$51 SRMC because cheaper supply is
  capped. The fix re-grounds the corridor forward-ATC base fraction — the
  overnight (un-collapsed) ATC ceiling as a share of physical TTC — to the
  measured p95 deliverability the corridor demonstrably carried (rule #11/#12: a
  capability re-grounding to measured DELIVERABILITY, regenerable for a forward
  year and responsive to a TTC upgrade, NOT a tune to net-import volume or the
  price residual). The midday solar floor stays 0.30: the forward formula is a
  ceiling the LP clears below, and the measured p95 midday/night ratio overstates
  the *typical* midday deliverability — raising the floor over-imported midday and
  inverted the interchange diurnal shape.

  ERCOT / PJM / NYISO / NEISO stay byte-identical (the change is in the CAISO-only
  CAISO_PER_HUB_NEIGHBORS spec).
"""

from __future__ import annotations

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
    out_dir = Path("results/calibration/caiso39_import_atc")
    reference = _load_reference()
    run_dir = solve_and_persist(
        [2023, 2024, 2025],
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
        note=(
            "caiso 39 import-ATC re-grounding: re-ground the WECC corridor "
            "forward-ATC base fractions (CAISO_PER_HUB_NEIGHBORS) to the measured "
            "p95 overnight net-import deliverability (PNW 0.30->0.43, DSW "
            "0.50->0.56), closing the import-ATC compression the caiso 38 finding "
            "exposed (model import swing 2,321 vs actual 4,596 MW). Midday solar "
            "floor stays 0.30 (the p95 midday ratio overstates the typical "
            "ceiling and inverts the diurnal). Measured-deliverability grounded "
            "(rule #11/#12), NOT residual-tuned. All caiso 38 levers verbatim; "
            "ERCOT/PJM/NYISO/NEISO byte-identical."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
