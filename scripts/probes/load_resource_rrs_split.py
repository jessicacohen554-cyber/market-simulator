"""Print the measured-vs-modeled ERCOT load-resource RRS-UFR MW (G4 validation).

Reports, per year, the **measured** NP3-911 cleared RRS-UFR series (the load-side
Responsive Reserve only Load Resources provide, ``ercot_load_resource_reserve_mw``)
against the **forward enrollment forecast** the model would use in a forecast year
(``ercot_load_resource_reserve_forward_mw`` = enrolled_DR_MW(year) x mean-1
availability shape). The measured series is the backcast realization the forward
enrollment trajectory is validated against — the honesty gate is that the forecast
comes from a forward DR-enrollment trend, NOT the measured cleared MW pinned to a
price (CLAUDE.md #12). In a backcast run the credit applied to the LP IS the
measured series; this probe shows the forward analogue tracks its present level.

Usage: python scripts/probes/load_resource_rrs_split.py [YEAR ...]
       (default 2023 2024 2025)
"""

import sys


from market_sim.results.scarcity import (
    ercot_load_resource_reserve_forward_mw,
    ercot_load_resource_reserve_mw,
    ercot_lr_rrs_enrolled_mw,
)

years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
HOURS = 8760

print("\nERCOT load-resource RRS-UFR — measured (NP3-911) vs forward enrollment\n")
print(
    f"{'year':>4} | {'measured mean':>13} | {'measured peak':>13} | "
    f"{'enrolled fcst':>13} | {'fcst mean':>10} | {'fcst/meas':>9}"
)
print("-" * 78)
for year in years:
    meas = ercot_load_resource_reserve_mw(year, HOURS)
    fwd = ercot_load_resource_reserve_forward_mw(year, HOURS)
    meas_mean = float(meas.mean())
    ratio = float(fwd.mean()) / meas_mean if meas_mean > 0 else float("nan")
    print(
        f"{year:>4} | {meas_mean:>10.0f} MW | {float(meas.max()):>10.0f} MW | "
        f"{ercot_lr_rrs_enrolled_mw(year):>10.0f} MW | {float(fwd.mean()):>7.0f} MW | "
        f"{ratio:>8.2f}x"
    )

# A few forward years to show the enrollment trajectory growing toward the cap.
print("\nforward enrollment trajectory (no measured series exists forward):")
for year in (2026, 2030, 2035, 2040):
    fwd = ercot_load_resource_reserve_forward_mw(year, HOURS)
    print(
        f"{year:>4} | enrolled {ercot_lr_rrs_enrolled_mw(year):>6.0f} MW | "
        f"credit mean {float(fwd.mean()):>6.0f} MW | "
        f"peak {float(fwd.max()):>6.0f} MW"
    )
print(
    "\n(mean/peak MW across 8760h. measured = NP3-911 cleared RRS-UFR (the "
    "validation target, never pinned). enrolled fcst = the forward DR-enrollment "
    "trajectory; the forecast credit is enrolled x mean-1 availability shape, so "
    "its annual mean equals the enrolled level and it grows toward the ~1.4 GW "
    "protocol cap as enrollment rises — fewer scarcity hours forward.)"
)
