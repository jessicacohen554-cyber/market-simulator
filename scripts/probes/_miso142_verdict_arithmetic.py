"""miso-142 — the counterfactual arithmetic that decides the session (G-C2).

No solve.  Reads the three committed miso-142 gate artifacts and combines them
into the one number each pre-registered branch turns on: **how much of the
summer price deficit could the measured quantity defect actually buy?**

    reach ($/MWh)  =  deltaQ (GW)  x  stack slope ($/MWh per GW)
    required (GW)  =  deficit ($/MWh)  /  stack slope ($/MWh per GW)

Both inputs are measured, neither is assumed: ``deltaQ`` is H1's own quantity
(``_miso142_supply_vs_eia930.json``, model minus EIA-930 over hydro + OTHER +
import) and the slope is the model's own observed supply curve
(``_miso142_marginal_and_slope.json``).  ``required`` is then bounded against
miso-139's idle cushion, reproduced to the MW by this session's own probe.

PREREG §4 branches:
  A  H1 SUPPORTED & SUFFICIENT   deltaQ >= +2 GW and reach >= 50 % of deficit
  B  H1 SUPPORTED, INSUFFICIENT  deltaQ >= +2 GW, reach < 50 %
  C  H1 REFUTED                  deltaQ < +2 GW
  D  INSTRUMENT-BLOCKED          deltaQ below the EIA-930 residual noise floor

Usage::

    .venv/bin/python scripts/probes/_miso142_verdict_arithmetic.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results/calibration"
OUT = CAL / "_miso142_verdict_arithmetic.json"
YEARS = ("2023", "2024", "2025")

H1_GW_BAR = 2.0  # PREREG P9
SUFFICIENT_FRAC = 0.50  # PREREG §4 branch A/B


def main() -> None:
    supply = json.loads((CAL / "_miso142_supply_vs_eia930.json").read_text())
    slope = json.loads((CAL / "_miso142_marginal_and_slope.json").read_text())
    stack = json.loads((CAL / "_miso142_stack_slope_vs_actual.json").read_text())

    out: dict = {
        "prereg": "results/calibration/PREREG-miso142-summer-supply-stack-2026-08-08.md",
        "gate": "G-C2 -- the counterfactual arithmetic",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "H1_gw_bar": H1_GW_BAR,
        "sufficiency_frac": SUFFICIENT_FRAC,
        "years": {},
    }

    for y in YEARS:
        sup = supply["years"][y]
        yr = {}
        for wkey, skey in (
            ("W1_jun_jul_h8_20", "W1_jun_jul_h8_20"),
            ("JJA_h12_17", "JJA_h12_17"),
        ):
            sl = slope["years"][y][skey]
            deficit = float(sl["deficit_usd_per_mwh"])  # negative
            # Model's own stack slope over the +2 GW step (the most stable of
            # the four reported steps: +1 GW is bin-noisy, +12 GW leaves the
            # observed range in 2025).  Cross-checked against the independent
            # OLS fit on the central 80 % of hours.
            step = sl["slope_usd_per_gw"].get("+2GW")
            ols = stack["years"][y][skey]["model"]["slope"]["slope_usd_per_gw"]
            act_ols = stack["years"][y][skey]["actual"]["slope"]["slope_usd_per_gw"]
            use = float(ols)  # the OLS fit: more hours, has a standard error

            dq_mw = float(sup["windows"][wkey]["H1_deltaQ_hydro_other_import_mw"])
            dq_gw = dq_mw / 1000.0
            reach = dq_gw * use
            required_gw = abs(deficit) / use
            cushion_key = (
                "ct_headroom_W1" if wkey == "W1_jun_jul_h8_20" else "ct_headroom_JJA_h12_17"
            )
            cushion_gw = float(slope["years"][y][cushion_key]["cushion_mw"]) / 1000.0
            floor_mw = float(
                sup["eia930_adjustment_residual_mw"]["median_abs_W1"]
            )

            yr[wkey] = {
                "deficit_usd_per_mwh": round(deficit, 3),
                "model_slope_usd_per_gw_ols": round(use, 4),
                "model_slope_usd_per_gw_binned_+2GW": step,
                "actual_slope_usd_per_gw_ols": round(float(act_ols), 4),
                "actual_over_model_slope": round(float(act_ols) / use, 2),
                "H1_deltaQ_gw": round(dq_gw, 4),
                "H1_deltaQ_vs_bar": f"{dq_gw:.3f} GW vs {H1_GW_BAR} GW bar",
                "H1_below_instrument_noise_floor": bool(abs(dq_mw) < floor_mw),
                "H1_reach_usd_per_mwh": round(reach, 4),
                "H1_reach_frac_of_deficit": round(abs(reach / deficit), 4),
                "required_gw_to_close_by_quantity": round(required_gw, 2),
                "idle_cushion_gw": round(cushion_gw, 2),
                "required_over_cushion": round(required_gw / cushion_gw, 2),
                "branch": (
                    "C -- H1 REFUTED"
                    if dq_gw < H1_GW_BAR
                    else (
                        "A -- SUPPORTED & SUFFICIENT"
                        if abs(reach / deficit) >= SUFFICIENT_FRAC
                        else "B -- SUPPORTED, INSUFFICIENT"
                    )
                ),
            }
        out["years"][y] = yr

    OUT.write_text(json.dumps(out, indent=1))

    print("=" * 84)
    print("miso-142 G-C2 -- can a QUANTITY repair reach the MISO summer price deficit?")
    print("=" * 84)
    hdr = (
        f"{'year/window':26s} {'deficit':>9s} {'slope':>8s} {'act/mdl':>8s} "
        f"{'dQ GW':>7s} {'reach':>8s} {'reach%':>7s} {'need GW':>8s} {'/cushion':>9s}"
    )
    print(hdr)
    print("-" * len(hdr))
    for y in YEARS:
        for wkey, r in out["years"][y].items():
            print(
                f"{y + ' ' + wkey:26s} {r['deficit_usd_per_mwh']:+9.2f} "
                f"{r['model_slope_usd_per_gw_ols']:8.3f} "
                f"{r['actual_over_model_slope']:7.2f}x "
                f"{r['H1_deltaQ_gw']:+7.3f} {r['H1_reach_usd_per_mwh']:+8.3f} "
                f"{100 * r['H1_reach_frac_of_deficit']:6.2f}% "
                f"{r['required_gw_to_close_by_quantity']:8.1f} "
                f"{r['required_over_cushion']:8.2f}x"
            )
    print()
    for y in YEARS:
        r = out["years"][y]["JJA_h12_17"]
        print(
            f"  {y} JJA h12-17 branch: {r['branch']}"
            + (
                "   [dQ is BELOW the EIA-930 noise floor -- not assertable]"
                if r["H1_below_instrument_noise_floor"]
                else ""
            )
        )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
