"""Driver: CAISO 45 — startup bridge + bidirectional intertie export sink.

Combines the caiso-42 keeper recipe (corridor ATC forward + EIA-930 monthly
hydro) with the caiso-44 startup-cost-aware RA bridge, and enables the
midday EXPORT pathway via caiso_bidir_intertie so surplus (committed gas at
min-load + solar) flows out the intertie.

Root cause (caiso-44 diagnosis): the bridge added committed gas at min-load,
but with no export sink the surplus could not flow out, so it padded annual
gas past EIA-923. Real CAISO 2024 spring midday runs ~6.8 GW gas and
net-exports; the model ran ~1.8 GW gas and net-imported +0.7 GW, 0 export
hours, 0 negative-price hours. The bridge needs the export/curtail sink.

The bidir intertie (CAISO_BIDIR_EXPORT_CAP_MW = 3,500 MW) is grounded in
the measured EIA-930 CISO 2024 net export peak, not tuned to the price
residual. With the bridge holding gas committed midday and the export leg
open, the LP should reverse the tie to export in the midday solar glut,
setting sub-SRMC (negative) clearing prices — matching real CAISO behavior.

POST-SOLVE GUARDRAIL (CLAUDE.md rules #1/#11): annual gas TWh must NOT
exceed EIA-923 by more than +20% per year. If it does, the bridge is
over-committing and padding gas — flag the failure and do not promote.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from run_calibration_full import solve_and_persist, report_run  # noqa: E402

EIA923_GAS_TWH: dict[int, float] = {
    2023: 76.0,
    2024: 67.7,
    2025: 55.2,
}
GAS_GUARDRAIL_TOLERANCE = 0.20  # +20% max over EIA-923


def main() -> None:
    import pandas as pd

    years = [2023, 2024, 2025]
    iso = "CAISO"
    out_dir = REPO / "results" / "calibration" / "caiso_45_export_sink"

    run_dir = solve_and_persist(
        years=years,
        iso=iso,
        hours=8760,
        reference=json.loads(
            (
                REPO
                / "data"
                / "raw"
                / "_validation-source"
                / "calibration_reference.json"
            ).read_text()
        ),
        commitment=False,
        screen_coal=True,
        run_dir=out_dir,
        # --- locked caiso-42 keeper flags ---
        coal_prb_passthrough_sigmoid=True,
        coal_mustrun_per_plant=True,
        coal_drop_pof=True,
        coal_prb_passthrough_tiered=True,
        priced_interchange=True,
        hydro_eia930_monthly=True,
        caiso_corridor_atc_forward=True,
        # --- caiso-44 startup bridge ---
        caiso_ra_mustoffer=True,
        caiso_ra_startup_bridge=True,
        # --- NEW: bidirectional intertie export sink ---
        caiso_bidir_intertie=True,
        # --- existing structural flags (caiso-42 defaults) ---
        caiso_solar_endogenous_spill=True,
        negative_renewable_offers=True,
        gas_hub_basis_overlay=True,
        gas_monthly_actuals=True,
        note=(
            "CAISO 45: startup bridge + bidir-intertie export sink "
            "(fix caiso-44 gas padding). Combines caiso-42 keeper "
            "(corridor ATC forward + EIA-930 hydro) with the caiso-44 "
            "startup-cost-aware RA bridge, plus caiso_bidir_intertie "
            "(export cap 3,500 MW from measured EIA-930 peak). The export "
            "leg lets the LP reverse the tie midday so surplus "
            "(committed gas at min-load + solar) displaces imports / sets "
            "sub-SRMC (negative) clearing prices instead of padding "
            "annual gas past EIA-923."
        ),
    )

    # --- POST-SOLVE GUARDRAIL: gas TWh vs EIA-923 ---
    print("\n" + "=" * 80)
    print("  GAS TWh GUARDRAIL (CLAUDE.md rules #1/#11)")
    print("=" * 80)
    meta = json.loads((run_dir / "meta.json").read_text())
    guardrail_pass = True
    for year in years:
        pass_label = meta["passes"][-1]
        disp_path = run_dir / "dispatch" / f"{year}_{pass_label}.parquet"
        if not disp_path.exists():
            print(f"  {year}: dispatch not found — SKIP")
            continue
        dispatch = pd.read_parquet(disp_path)
        gas_fuels = {"gas_cc", "gas_ct", "gas_st", "gas_cc_ccs"}
        gas_mw = dispatch[dispatch["fuel"].isin(gas_fuels)]["mw"].sum()
        gas_twh = gas_mw / 1e6
        ref = EIA923_GAS_TWH.get(year, float("inf"))
        pct_over = 100.0 * (gas_twh - ref) / ref if ref else float("nan")
        status = "PASS" if pct_over <= GAS_GUARDRAIL_TOLERANCE * 100 else "FAIL"
        if status == "FAIL":
            guardrail_pass = False
        print(
            f"  {year}: model gas = {gas_twh:.1f} TWh, "
            f"EIA-923 = {ref:.1f} TWh, "
            f"delta = {pct_over:+.1f}% "
            f"(tolerance {GAS_GUARDRAIL_TOLERANCE * 100:.0f}%) → {status}"
        )

    if not guardrail_pass:
        print("\n  *** GUARDRAIL FAILED: bridge is over-committing gas. ***")
        print("  *** Do NOT promote to keeper — register as documented probe. ***")
    else:
        print("\n  GUARDRAIL PASSED: gas TWh within EIA-923 band.")

    # --- REPORT ---
    report_run(run_dir)

    return guardrail_pass


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
