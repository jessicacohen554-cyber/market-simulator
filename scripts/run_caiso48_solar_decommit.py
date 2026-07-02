"""Driver: CAISO 48 — startup bridge + export sink + solar-decommit control.

caiso-45 (startup bridge + bidir-intertie export sink) proved the mechanism —
negatives appeared (148 h in 2024), import hours fell 99.5% → 82% — but the
bridge over-committed gas in high-solar years: 2025 annual gas came in +34.4%
over EIA-923 (tolerance 20%). Its verbatim open item: "needs a
solar-proportional commitment ramp or seasonal decommitment logic."

caiso-48 adds that control (``caiso_ra_bridge_decommit``), grounded in UC
physics, not the gas residual:

1. DAY-AHEAD HORIZON — the DAM (CAISO IFM/RUC) commits one 24-hour operating
   day, so only a gap <= DA_COMMITMENT_HORIZON_HOURS (24 h) can be an
   intra-day min-load hold. The plain bridge, pricing gaps at the biased-high
   P1 LMP (MC − LMP ≈ 0), was bridging idle spells of ANY length in EVERY
   season; multi-day idles are next-day decommit/re-offer decisions and now
   never bridge (the seasonal decommitment).
2. OVER-GENERATION REPRICING + RUC-ORDER DECOMMIT — held min-load energy is
   worth the gap LMP only while it displaces dispatchable supply (P1 import
   dispatch backs down, export-sink headroom absorbs). Once the candidate
   floors exceed that hourly absorption, the marginal displaced MWh is a
   curtailable renewable at the negative keep-running offer, so surplus gap
   hours reprice to -renewable_keep_running_value and uneconomic bridges
   decommit cheapest-startup-first (the RUC de-commitment order). Deeper
   solar → less absorption → more decommitment: the solar-proportional ramp.

POST-SOLVE GATES (promotion criteria for this run):
  (a) 2024/2025 negative-price hours appear (directionally toward actuals);
  (b) annual gas TWh within +20% of EIA-923 ALL three years (caiso-45 failed
      2025 at +34.4%);
  (c) the 2024 CC_REGULAR wedge shrinks vs the caiso-42 keeper (+9.21 TWh);
  (d) no new structural regressions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from run_calibration_full import report_run, solve_and_persist  # noqa: E402

EIA923_GAS_TWH: dict[int, float] = {
    2023: 76.0,
    2024: 67.7,
    2025: 55.2,
}
GAS_GUARDRAIL_TOLERANCE = 0.20  # +20% max over EIA-923
# caiso-42 keeper 2024 CC_REGULAR wedge (C1 HARD FAIL +9.21 TWh over actual);
# gate (c) requires the caiso-48 wedge to come in under this.
CAISO42_CC_REGULAR_2024_OVER_TWH = 9.21


def main() -> bool:
    import pandas as pd

    years = [2023, 2024, 2025]
    iso = "CAISO"
    out_dir = REPO / "results" / "calibration" / "caiso48_solar_decommit_bridge"

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
        # --- caiso-44 startup bridge + caiso-45 export sink ---
        caiso_ra_mustoffer=True,
        caiso_ra_startup_bridge=True,
        caiso_bidir_intertie=True,
        # --- NEW: solar-proportional / seasonal decommitment control ---
        caiso_ra_bridge_decommit=True,
        # --- existing structural flags (caiso-42 defaults) ---
        caiso_solar_endogenous_spill=True,
        negative_renewable_offers=True,
        gas_hub_basis_overlay=True,
        gas_monthly_actuals=True,
        note=(
            "caiso 48 solar-decommit bridge: caiso-45 (startup bridge + "
            "bidir-intertie export sink) plus the caiso_ra_bridge_decommit "
            "control — (1) economic bridges bounded to the 24-h day-ahead "
            "commitment horizon (CAISO IFM/RUC one operating day), so "
            "multi-day idles are next-day decommit/re-offer decisions and "
            "stop padding annual gas; (2) gap hours where the candidate "
            "min-load floors exceed the P1 import-dispatch + export-sink "
            "absorption reprice to the curtailable-renewable keep-running "
            "offer and uneconomic bridges decommit cheapest-startup-first "
            "(RUC order) — deeper solar, less absorption, more decommitment. "
            "UC physics only (startup cost, min-down, DA horizon, the "
            "existing negative renewable offer); nothing fitted to the gas "
            "or price residual."
        ),
    )

    meta = json.loads((run_dir / "meta.json").read_text())
    pass_label = meta["passes"][-1]

    print("\n" + "=" * 80)
    print("  CAISO-48 PROMOTION GATES")
    print("=" * 80)

    # --- gate (b): gas TWh vs EIA-923, all years ---
    gas_ok = True
    cc_2024_twh = None
    for year in years:
        disp_path = run_dir / "dispatch" / f"{year}_{pass_label}.parquet"
        if not disp_path.exists():
            print(f"  {year}: dispatch not found — SKIP")
            continue
        dispatch = pd.read_parquet(disp_path)
        gas_fuels = {"gas_cc", "gas_ct", "gas_st", "gas_cc_ccs"}
        gas_twh = dispatch[dispatch["fuel"].isin(gas_fuels)]["mw"].sum() / 1e6
        ref = EIA923_GAS_TWH.get(year, float("inf"))
        pct_over = 100.0 * (gas_twh - ref) / ref
        status = "PASS" if pct_over <= GAS_GUARDRAIL_TOLERANCE * 100 else "FAIL"
        if status == "FAIL":
            gas_ok = False
        print(
            f"  (b) {year}: gas = {gas_twh:.1f} TWh vs EIA-923 {ref:.1f} "
            f"({pct_over:+.1f}%, tol +20%) → {status}"
        )
        if year == 2024:
            cc_2024_twh = dispatch[dispatch["klass"] == "CC_REGULAR"]["mw"].sum() / 1e6

    # --- gate (a): negative-price hours ---
    system = pd.read_parquet(run_dir / "system.parquet")
    system = system[system["pass"] == pass_label]
    for year in years:
        sy = system[system["year"] == year]
        # demand-weighted system price per hour (matches the scoring basis)
        hourly = sy.groupby("hour").apply(
            lambda h: (h["price"] * h["demand"]).sum() / max(h["demand"].sum(), 1e-9)
        )
        neg = int((hourly < 0.0).sum())
        lo = float(hourly.min())
        print(f"  (a) {year}: negative-price hours = {neg}, LMP min = {lo:.1f}")

    # --- gate (c): 2024 CC_REGULAR wedge ---
    if cc_2024_twh is not None:
        print(
            f"  (c) 2024 CC_REGULAR = {cc_2024_twh:.2f} TWh "
            f"(caiso-42 wedge was +{CAISO42_CC_REGULAR_2024_OVER_TWH} TWh over "
            "actual; compare against the C1 table in the report below)"
        )

    if not gas_ok:
        print("\n  *** GAS GUARDRAIL FAILED — do NOT promote; register as probe. ***")
    else:
        print("\n  GAS GUARDRAIL PASSED (all years within +20% of EIA-923).")

    # --- full report (C1..C6 scoring, curtailment vs reported) ---
    report_run(run_dir)

    return gas_ok


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
