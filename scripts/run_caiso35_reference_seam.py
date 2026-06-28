"""Driver: CAISO 35 — WECC reference-price seam (over-import / export fix), 2023-25.

Builds on caiso 34 (caiso_step6_ixshape) with ONE structural seam change: replace
the measured per-hub OASIS hub-LMP ladder (`caiso_per_hub_intertie`) with the
forward-native reference-price seam (`caiso_reference_price_seam`,
INTERFACE_NEIGHBORS["CAISO"]) — the same gas × heat-rate × load-shape construction
the PJM/MISO seams use, specialized to CAISO's two WECC corridors.

Why (caiso 34 residuals):

  caiso 34 prices each corridor at the measured OASIS hub LMP (Palo Verde / Malin),
  which works for backcast shape but has no forward analogue — 2023 falls back to
  the static $28-180 ladder (Jan-Feb OASIS aged out). The export side was a fixed
  $0/$8 WTP far below the WECC hub price a neighbor would pay, so the model exports
  in only 1-3% of hours vs 9-14% actual and over-imports 8.7-15.8 TWh.

  The reference-price seam prices BOTH legs per corridor from
  (henry_hub[year] + gas_basis) × marginal_heat_rate × load_shape ± hurdle, with
  the CARB border carbon on the import leg. The export tranches clear at
  hub − hurdle (the price a WECC neighbor pays for CAISO's midday solar surplus),
  the structural fix for "model never exports" that drives the over-import; and the
  seam stays live in every year (no OASIS gap, e.g. 2023).

  Per-corridor HR anchors (scripts/derive_caiso_seam_hr_by_year.py — measured
  Malin / Palo-Verde annual-mean RT LMP / delivered gas, blind to CAISO's flow,
  rule #11/#12):
    WECC_DSW (Palo Verde, net-load): hr_by_year 17.01/13.39/8.50, struct 12.97
    WECC_PNW (Malin, gross-load):    hr_by_year 22.50/21.20/11.80, struct 18.50

  The per-hub corridor split and the measured p95 corridor ATC envelope
  (caiso_corridor_flow_limit) still apply — the reference price sets the PRICE, the
  ATC envelope the FLOW LIMIT. All other caiso 34 levers are carried verbatim.
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
    out_dir = Path("results/calibration/caiso35_reference_seam")
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
        # caiso 34 coal recipe (minimal CAISO coal, carried verbatim).
        coal_prb_passthrough=1.0,
        coal_prb_passthrough_sigmoid=True,
        coal_mustrun_per_plant=True,
        coal_drop_pof=True,
        coal_prb_passthrough_tiered=True,
        priced_interchange=True,
        # The seam change: forward reference price replaces the measured per-hub
        # OASIS ladder. The corridor ATC cap remains (task #5) but uses the
        # FORWARD, one-sided import envelope (TTC × ATC-frac × solar derate)
        # rather than the measured two-sided p95 — the measured EXPORT-direction
        # cap collapses DSW export to ~0 and would mechanically forbid the very
        # midday solar export the reference seam is built to enable. The forward
        # ATC is consistent with the forward-native seam and leaves the export
        # direction at the physical corridor TTC so the reference price governs.
        caiso_reference_price_seam=True,
        caiso_per_hub_intertie=False,
        caiso_corridor_atc_forward=True,
        note=(
            "caiso 35 reference-price seam: replace the measured per-hub OASIS "
            "hub-LMP ladder (caiso_per_hub_intertie) with the forward-native "
            "reference-price seam (caiso_reference_price_seam, "
            "INTERFACE_NEIGHBORS['CAISO']) — both legs of each WECC corridor "
            "priced from (HH + gas_basis) x HR x load-shape +/- hurdle, CARB "
            "border carbon on the import leg, export at hub - hurdle. HR anchors "
            "from measured Malin/Palo-Verde annual-mean RT LMP / delivered gas "
            "(derive_caiso_seam_hr_by_year.py; rule #11/#12). Fixes the over- "
            "import / never-export bias and the 2023 OASIS gap. Per-hub corridor "
            "split retained; corridor ATC uses the FORWARD one-sided import "
            "envelope (caiso_corridor_atc_forward) so the export direction is "
            "free to the physical TTC (the measured two-sided p95 collapses DSW "
            "export to ~0 and would block the midday solar export). All other "
            "caiso 34 levers verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
