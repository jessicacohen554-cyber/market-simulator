"""Derive the Southeast (Carolinas/TVA/LGEE) gas-INELASTIC affine heat-rate.

PJM's Southeast reference-price seams (Carolinas/TVA/LGEE) are coal/nuclear-set
regions with **no organized-market nodal LMP** to anchor a per-year heat rate to
(unlike the MISO/NYISO seams, which carry a measured ``hr_by_year``). Priced at a
flat ``gas x 11.6`` they ride Henry Hub up in a dear-gas year — in 2025 the seam
priced to ~$40.8, only ~$2 below PJM's $42.9, so the diurnal swing flipped the
seam to a *wrong-direction* export (+2.0 TWh model vs the measured −5.9 net
import). A coal/nuclear region's price is **weakly gas-elastic**: most of its
level is a coal- and nuclear-set fixed component that does not move with Henry
Hub.

This script fits that price formation as an affine-in-gas relation,

    SE_LMP(gas) = hr_phys * gas + hr_adder

by OLS of the Southeast's **own documented hub price level** (Into-Southern /
SERC blended on/off-peak wholesale, the neighbor's measured price-formation
series) on the Henry Hub annual average. It is **blind to PJM's net interchange**
(claude.md rule #11) and anchors to a measured neighbor price (rule #12) — the
same standard as ``derive_neighbor_hr_by_year.py``, except SERC has no nodal LMP
so a published hub index supplies the level. The implied effective heat rate is
``hr_phys + hr_adder / gas``; it is consumed by
``neighbor_price._HR_GAS_ELASTIC`` for the Carolinas/TVA/LGEE seams in every year
(backcast and forward — fully forecast-native).

``--check`` asserts the committed constants still match the fit, mirroring
``derive_interface_limits.py``.

Sources (documented hub-price levels; flow-blind):
- ICE / S&P Global (SNL) Into-Southern and VACAR-South wholesale power indices,
  calendar-year blended on/off-peak averages, 2023-2025.
- EIA Henry Hub annual spot average (the gas driver the fit regresses on).
"""

from __future__ import annotations

import argparse

# Documented Southeast (SERC: Duke/Progress Carolinas + TVA + LGEE) blended
# wholesale hub price level by year ($/MWh), and the Henry Hub annual average gas
# price ($/MMBtu) for the same year. These are the neighbor's OWN measured price
# formation — never PJM's interchange. The gas points match
# constants.HENRY_HUB_TRAJECTORIES backcast anchors.
SE_HUB_LMP_BY_YEAR: dict[int, float] = {
    2023: 28.5,  # cheap-shoulder year, Into-Southern blended ~$28-30
    2024: 26.5,  # cheapest gas of the three; SERC blended ~$26-28
    2025: 34.0,  # dear-gas + SERC load growth; blended ~$33-36
}
HENRY_HUB_BY_YEAR: dict[int, float] = {2023: 2.54, 2024: 2.19, 2025: 3.52}

# Committed coefficients (this script's output, rounded), used in
# src/market_sim/data/neighbor_price.py::_HR_GAS_ELASTIC for Carolinas/TVA/LGEE.
COMMITTED_HR_PHYS = 5.6
COMMITTED_HR_ADDER = 14.2
_TOL = 0.15  # rounding tolerance for --check


def fit_affine() -> tuple[float, float]:
    """OLS fit of SE hub LMP on Henry Hub: returns ``(hr_phys, hr_adder)``."""
    years = sorted(SE_HUB_LMP_BY_YEAR)
    xs = [HENRY_HUB_BY_YEAR[y] for y in years]
    ys = [SE_HUB_LMP_BY_YEAR[y] for y in years]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / n
    var = sum((x - mx) ** 2 for x in xs) / n
    slope = cov / var  # hr_phys ($/MWh per $/MMBtu = effective gas-slope HR)
    intercept = my - slope * mx  # hr_adder ($/MWh, the coal/nuclear-set fixed $)
    return slope, intercept


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="assert the committed constants still match the fit (exit 1 if not)",
    )
    args = ap.parse_args()

    hr_phys, hr_adder = fit_affine()
    print("Southeast affine-in-gas price fit  LMP = hr_phys*gas + hr_adder")
    print(f"  hr_phys (gas-slope HR)      = {hr_phys:.3f}")
    print(f"  hr_adder (coal/nuclear $)   = {hr_adder:.3f}")
    print("  reproduced level vs documented hub:")
    for y in sorted(SE_HUB_LMP_BY_YEAR):
        gas = HENRY_HUB_BY_YEAR[y]
        fit = hr_phys * gas + hr_adder
        flat = gas * 11.6  # the old flat-HR price, for contrast
        print(
            f"    {y}: fit ${fit:5.1f}  vs doc ${SE_HUB_LMP_BY_YEAR[y]:5.1f}  "
            f"(flat-11.6 was ${flat:5.1f})"
        )

    if args.check:
        if (
            abs(hr_phys - COMMITTED_HR_PHYS) > _TOL
            or abs(hr_adder - COMMITTED_HR_ADDER) > _TOL
        ):
            print(
                f"CHECK FAILED: committed ({COMMITTED_HR_PHYS}, {COMMITTED_HR_ADDER}) "
                f"!= fit ({hr_phys:.3f}, {hr_adder:.3f})"
            )
            return 1
        print(
            f"CHECK OK: committed ({COMMITTED_HR_PHYS}, {COMMITTED_HR_ADDER}) matches fit"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
