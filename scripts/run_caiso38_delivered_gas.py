"""Driver: CAISO 38 — CA delivered-gas fidelity (citygate overlay), 2023-25.

Builds on caiso 37 (caiso37_offer_curve, the current keeper) with ONE domestic
change and nothing else: CAISO now prices its gas off the measured SoCal / PG&E
Citygate trading hub (the `gas_hub_basis_overlay`, already used for NEISO),
instead of the volume-weighted EIA-923 ISO-month series across only ~7 reporting
plants. Every caiso 37 lever (the offer curve, the reference-price seam, the
coal recipe, priced interchange, forward corridor ATC) is carried verbatim.

Why (caiso 37 finding + this session's delivered-gas diagnosis):

  caiso 37 proved the remaining ~2x CA-zone body over-price is the DOMESTIC
  gas_cc marginal bid (CC_REGULAR is marginal in essentially every hour), NOT
  the offer-curve econ band, the seam shape, or a midday-solar problem. The bid
  decomposes as delivered_gas x eff_HR(~9) + CARB_carbon + VOM. Working back from
  the 2024 body ($61) the model assigns the marginal CC ~$4.45/MMBtu delivered
  gas.

  That $4.45 is set by the EIA-923 ISO-month series, which for CAISO is
  volume-weighted across only ~7 plants that report Schedule-5 gas receipts
  (Gateway / Colusa / Lodi — PG&E + NCPA NorCal — plus SDGE Palomar): a
  NorCal/SDGE-skewed sample. The authoritative full-census CA electric-power
  delivered gas (EIA N3045CA3, 2024 = $3.98/Mcf = $3.84/MMBtu) is ~$0.6/MMBtu
  lower, and the measured CA citygate the SP15-dominated marginal CC actually
  prices off (EIA N3050CA3) is lower still ($3.38/MMBtu in 2024) — SoCal border
  gas fell to a *discount* to Henry Hub in summer 2024. The 7-plant sample
  misses that cheap SoCal bulk and overstates the marginal CC's fuel.

  The fix re-grounds CAISO gas to the measured SoCal / PG&E Citygate spot via the
  doc-08 trading-hub overlay (the marginal unit's opportunity cost is the hub
  price it could resell into, not the contract-laden plant-average delivered
  cost), using the in-repo measured basis rows
  (data/raw/gas_basis_by_iso_month.csv, EIA N3050CA3 - Henry Hub). This is a
  measured, forward-reproducible input (it regenerates each year and already
  carries both the Jan-2023 western gas crisis, +$24/MMBtu basis, and the
  summer-2024 SoCal discount) that supersedes the skewed 7-plant sample
  (CLAUDE.md rule #11: prefer accurate measured data; reconcile a misaligned
  sample to the representative hub) — NOT a haircut to the price residual.

  The overlay applies automatically inside _calibration_config on iso=="CAISO"
  (the same NEISO mechanism, now keyed on the CAISO citygate rows). ERCOT / PJM /
  NYISO / NEISO stay byte-identical. The seam, offer curve and all other caiso 37
  levers are carried verbatim. Per the diagnosis the seam import price is already
  correctly anchored to the measured Palo Verde ($33) / Malin ($40) hub means
  and imports are ATC-capped, so the gas fix trims the body but the residual
  above target is the structurally-real CA-CC SRMC floor (gas + CARB carbon),
  not a seam or import-price defect.
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
    out_dir = Path("results/calibration/caiso38_delivered_gas")
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
        # it reproduces the measured Palo Verde / Malin hub means). Keep every flag.
        caiso_reference_price_seam=True,
        caiso_per_hub_intertie=False,
        caiso_corridor_atc_forward=True,
        note=(
            "caiso 38 delivered-gas: reprice CAISO gas off the measured SoCal / "
            "PG&E Citygate trading hub (gas_hub_basis_overlay, the doc-08 NEISO "
            "mechanism, now keyed on the in-repo CAISO citygate basis rows in "
            "gas_basis_by_iso_month.csv: EIA N3050CA3 - Henry Hub) instead of the "
            "EIA-923 ISO-month series volume-weighted across only ~7 NorCal/SDGE- "
            "skewed reporting plants. caiso 37 proved the ~2x CA-zone body over- "
            "price is the domestic gas_cc marginal bid; the 7-plant sample "
            "assigns the marginal CC ~$4.45/MMBtu (2024) vs the full-census CA "
            "electric-power delivered gas (EIA N3045CA3 $3.84) and the citygate "
            "($3.38) the SP15 marginal CC actually prices off (SoCal border fell "
            "to a discount to Henry Hub in summer 2024). The citygate overlay is "
            "the measured marginal opportunity-cost price (captures the Jan-2023 "
            "western gas crisis and the summer-2024 SoCal discount) and supersedes "
            "the skewed 7-plant sample — measured, forward-reproducible (rule #11), "
            "NOT residual-tuned. Per the diagnosis the seam is already anchored to "
            "the measured Palo Verde/Malin means and imports are ATC-capped, so the "
            "residual above target is the structurally-real CA-CC SRMC floor (gas + "
            "CARB carbon). All caiso 37 offer-curve + seam levers carried verbatim; "
            "ERCOT/PJM/NYISO/NEISO byte-identical."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
