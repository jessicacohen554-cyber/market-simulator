"""Driver: CAISO 37 — CAISO-specific gas offer curve (midday/body LMP fix), 2023-25.

Builds on caiso 35 (caiso35_reference_seam, the current keeper) with ONE domestic
change and nothing else: CAISO now gets its own ISO-specific thermal gas offer
curve (`_CAISO_OFFER_CURVE` in run_calibration.py) instead of silently inheriting
the ERCOT-derived heat-rate multipliers and the ERCOT CT $5,000-ORDC `peak` 13.15x
wall. Every caiso 35 seam flag is carried verbatim.

Why (caiso 35 / caiso 36 diagnosis,
results/calibration/DIAGNOSIS-caiso36-body-overprice-domestic-2026-06-28.md):

  The CA-zone LMP over-price (caiso 35 body 100.0/62.8/68.5 vs actual 43.8/33.0/33.6)
  is DOMESTIC, not a seam-shape problem — the caiso 36 seam-convexity probe was
  tested and REJECTED (it did not move the body and regressed interchange). The
  dispatch evidence shows CA midday is set by ~6.5 GW of economic gas_cc (solar is
  fully used, not curtailed; imports are already at the forward-ATC cap), so the
  gas_cc offer LEVEL — not the seam, not imports — sets the body. CAISO had no
  ISO-specific offer curve and fell through every per-band ternary to the generic
  ERCOT-fitted `else` branch (CC econ_low 1.06 / econ_high 1.27 over-pricing the
  midday CC body; CT_PEAKER peak 13.15x driving the 2023 > $200 tail: 744 h vs 21
  actual).

  The fix gives CAISO its own gas offer curve, grounded in CAISO market structure
  (CLAUDE.md rules #1/#11), NOT the price residual:
    - CC_REGULAR re-grounded to the measured CAMPD CC marginal-HR shape
      (econ_low 1.06 -> 0.95 flat body, econ_high 1.27 -> 1.21 SRMC reach), the
      same fit ERCOT/NYISO keepers use, removing the ERCOT level premium on the
      midday body. The physical F-class duct-burner peak (2.25) is unchanged.
    - CT_PEAKER `peak` capped 13.15 -> 4.0 (CAISO's $1,000-2,000 soft cap, not
      ERCOT's $5,000 ORDC — PJM's reasoning/value), with the econ band re-grounded
      to the DMM Default-Energy-Bid cost-plus-adder shape (econ_low 1.27 -> 1.10,
      econ_high 1.98 -> 1.50) and the start hurdle lowered (committed 1.55 -> 1.35,
      NYISO-grounded) so CAISO's fast-start CTs serve the evening ramp.

  The curve applies automatically inside _calibration_config on iso=="CAISO" (deep-
  merged onto the generic branch, so only the named gas classes change; CC_CHP /
  CT_CHP / ST_GAS / coal keep the generic defaults). ERCOT/PJM/other ISOs stay
  byte-identical. All other caiso 35 levers (the reference-price seam, the coal
  recipe, priced interchange, forward corridor ATC) are carried verbatim.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import (  # noqa: E402
    _load_reference,
    report_run,
    solve_and_persist,
)


def main() -> int:
    out_dir = Path("results/calibration/caiso37_offer_curve")
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
        # caiso 34/35 coal recipe (minimal CAISO coal, carried verbatim).
        coal_prb_passthrough=1.0,
        coal_prb_passthrough_sigmoid=True,
        coal_mustrun_per_plant=True,
        coal_drop_pof=True,
        coal_prb_passthrough_tiered=True,
        priced_interchange=True,
        # caiso 35 reference-price seam, carried verbatim (the seam is correct;
        # the over-price is domestic — see the diagnosis doc). Keep every flag.
        caiso_reference_price_seam=True,
        caiso_per_hub_intertie=False,
        caiso_corridor_atc_forward=True,
        note=(
            "caiso 37 offer-curve: give CAISO its own ISO-specific gas offer "
            "curve (_CAISO_OFFER_CURVE) instead of the silently-inherited ERCOT "
            "heat-rate multipliers + ERCOT CT 13.15x $5,000-ORDC wall. The fix "
            "for the DOMESTIC CA-zone midday/body LMP over-price diagnosed in "
            "caiso 36 (the seam is fine; gas_cc offer level sets the midday "
            "body). CC_REGULAR re-grounded to the measured CAMPD CC marginal-HR "
            "shape (econ 1.06/1.27 -> 0.95/1.21, physical duct-fire peak 2.25 "
            "kept); CT_PEAKER peak capped 13.15 -> 4.0 (CAISO $1,000-2,000 soft "
            "cap, PJM's reasoning), econ re-grounded to the DMM DEB cost-plus- "
            "adder shape (1.27/1.98 -> 1.10/1.50), committed start hurdle 1.55 "
            "-> 1.35 (NYISO-grounded, CTs serve the evening ramp). Grounded in "
            "CAISO DMM market structure + measured CAMPD heat rates, NOT the "
            "price residual (rules #1/#11). CC_CHP/CT_CHP/ST_GAS/coal keep the "
            "generic defaults; ERCOT/PJM/other ISOs byte-identical. All caiso 35 "
            "seam levers verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
