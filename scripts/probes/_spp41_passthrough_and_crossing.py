"""spp-41 phase 0b (ZERO LP): the PRB passthrough actually applied, and the crossing price.

Two measurements over the cached ``fleet_only`` offer arrays:

**A. The implied per-row coal passthrough.** ``coal_passthrough_series`` is
claimed here to resolve to the FLAT fallback for SPP (no ``("SPP", *)`` entry
in ``COAL_SIGMOID_DEFAULTS``, no explicit ``coal_prb_passthrough_*`` field on
the keeper), which would make the keeper's armed ``coal_prb_passthrough_sigmoid``
/ ``_tiered`` gates inert. That claim is checked against the arrays rather than
read off the source: back out ``(mc - nonfuel) / (band x fuel x HR)`` per PRB
row and test whether it is gas-INVARIANT across the four built years.

**B. The crossing gas price.** Decompose each row's marginal cost into the
part that scales with its fuel index and the part that does not, then sweep a
hypothetical gas multiplier and report, per year, the gas price at which the
CC_REGULAR econ stack crosses the COAL_PRB econ stack. Reported as the
gas price at which 50% of CC econ MW sits above the PRB econ median -- the
same displacement statistic the dispatch expresses.

Run: ``python3 scripts/probes/_spp41_passthrough_and_crossing.py``
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

CACHE = Path(
    os.environ.get(
        "SPP41_CACHE",
        "/tmp/claude-0/-home-user-market-simulator/"
        "d1272d6d-a347-5fa8-85cd-cf88fd75dd3e/scratchpad/spp41",
    )
)
YEARS = [2024, 2023, 2021, 2022]
ECON = ("econlo", "econ", "econhi")


def load(year: int) -> dict:
    z = np.load(CACHE / f"rows_{year}.npz", allow_pickle=True)
    d = {k: z[k] for k in z.files}
    for k in ("klass", "band", "coal_supply", "fuel_type", "unit_id"):
        d[k] = d[k].astype(str)
    return d


def main() -> None:
    print("=" * 78)
    print("A. IMPLIED PRB PASSTHROUGH  —  is the armed sigmoid doing anything?")
    print("   implied = (mc_mean - vom) / (0.93 x fuel_mean x heat_rate)")
    print("   0.93 is SPP's COAL_PRB band multiplier, identical on all four bands.")
    print("=" * 78)
    for y in YEARS:
        d = load(y)
        m = (d["klass"] == "COAL_PRB") & np.isin(d["band"], ECON) & (d["pmax"] > 1.0)
        denom = 0.93 * d["fuel_mean"][m] * d["heat_rate"][m]
        ok = denom > 1e-9
        implied = (d["mc_mean"][m][ok] - d["vom"][m][ok]) / denom[ok]
        w = d["pmax"][m][ok]
        print(
            f"  {y}  gas ${float(d['meta_gas']):.2f}  n={ok.sum():3d}  "
            f"cw-mean implied passthrough = {np.average(implied, weights=w):.4f}   "
            f"[p05 {np.percentile(implied, 5):.4f} .. p50 {np.median(implied):.4f} "
            f".. p95 {np.percentile(implied, 95):.4f}]"
        )
    print(
        "\n  A gas-keyed sigmoid would make this number RISE with the gas price\n"
        "  (ERCOT's PRB curve runs floor 0.78 -> ceil 1.50 about gas_mid 2.85).\n"
        "  A flat, gas-invariant value IS the flat fallback."
    )

    print("\n" + "=" * 78)
    print("B. THE CROSSING GAS PRICE")
    print("   Each row's MC is split into the fuel-indexed part and the rest;")
    print("   the gas rows' fuel index is then swept while coal's is held, which")
    print("   is what the model itself does (coal fuel does not track gas).")
    print("=" * 78)
    for y in YEARS:
        d = load(y)
        gas0 = float(d["meta_gas"])
        prb = (d["klass"] == "COAL_PRB") & np.isin(d["band"], ECON) & (d["pmax"] > 1.0)
        cc = (d["klass"] == "CC_REGULAR") & np.isin(d["band"], ECON) & (d["pmax"] > 1.0)

        # Fuel-indexed component of each CC row, at the year's own gas price.
        cc_fuel = 0.93 * d["fuel_mean"][cc] * d["heat_rate"][cc]
        cc_rest = d["mc_mean"][cc] - cc_fuel
        cc_w = d["pmax"][cc]
        prb_med = float(np.median(d["mc_mean"][prb]))

        def frac_above(gas: float) -> float:
            mc = cc_fuel * (gas / gas0) + cc_rest
            return float(cc_w[mc > prb_med].sum() / cc_w.sum())

        lo, hi = 0.5, 12.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if frac_above(mid) < 0.5:
                lo = mid
            else:
                hi = mid
        print(
            f"  {y}: PRB econ median MC ${prb_med:6.3f}/MWh (gas-invariant)  |  "
            f"50% of CC econ MW crosses it at gas = ${0.5 * (lo + hi):5.2f}/MMBtu  "
            f"(year's own gas ${gas0:.2f}; CC MW above PRB median now "
            f"{100 * frac_above(gas0):5.1f}%)"
        )
        for g in (2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.5):
            print(f"        gas ${g:4.2f} -> {100 * frac_above(g):5.1f}% of CC econ MW above the PRB econ median")


if __name__ == "__main__":
    main()
