"""Derive the breakeven EAC ($/MWh) that clears a project's IRR hurdle (ADR 0021).

The clean premium a buyer must pay for an attribute-basis (``lmp_ppa``) resource
is NOT a free parameter — it is the residual $/MWh the project needs *after every
other revenue stream* to recover its capital at the developer's hurdle rate. This
is exactly how a wind/solar PPA strike is set, so one calculation serves wind,
solar, and CCS::

    required all-in ($/MWh) = CRF(hurdle, term) x capex($/kW) x 1000 / (8760 x CF)
                            + FOM($/kW-yr) x 1000 / (8760 x CF)
                            + VOM + fuel

    revenue offsets ($/MWh) = expected LMP capture           # merchant energy sale
                            + 45Q / MWh   (CCS only)          # accrues to project
                            + capacity revenue / MWh          # where a market exists

    EAC_breakeven = max(0, required all-in - revenue offsets)

Key modeling choices (matching the owner's direction):

* **45Q accrues to the project owner**, so it is a *revenue offset* here (it
  lowers the EAC the buyer pays) — it is NOT netted into the resource VOM in the
  LP (that model prices CCS as LMP + EAC; ``resources.py`` lmp_ppa basis).
* **Capacity revenue** offsets the EAC only in ISOs that run a capacity market;
  ERCOT is energy-only (0), mirroring the market simulator's ``MARKET_DESIGN``.
* The output is the flat/annual EAC you feed into ``data/eac/eac_prices.csv`` — a
  reproducible forward-driver-derived input, never a residual-fitted knob.

This is a **default-off derivation helper**: it never runs inside the LP. Import
:func:`breakeven_eac` or run the module as a CLI.
"""

from __future__ import annotations

import argparse

from lce_portfolio.resources import (
    NG_CO2_TON_PER_MMBTU,
    capital_recovery_factor,
)

HOURS_PER_YEAR = 8760.0

# Per-ISO firm capacity price ($/kW-yr) credited as a revenue offset (ADR 0021).
# Mirrors the market simulator's MARKET_DESIGN split: ERCOT is energy-only (no
# capacity market -> 0); the RTO/ISO capacity constructs pay a net-CONE-style
# clearing price. These are ILLUSTRATIVE planning anchors (net-CONE order of
# magnitude); override with --capacity-kw-yr for a specific auction result.
CAPACITY_PRICE_KW_YR: dict[str, float] = {
    "ERCOT": 0.0,  # energy-only, no capacity market
    "PJM": 100.0,  # ~net-CONE order of magnitude (BRA clearing varies widely)
    "NYISO": 90.0,  # ICAP/UCAP spot demand-curve anchor
    "NEISO": 60.0,  # FCA clearing anchor
    "MISO": 80.0,  # PRA/seasonal anchor (zone-dependent)
    "CAISO": 40.0,  # RA capacity value anchor (bilateral RA market)
}


def credit_45q_per_mwh(
    capture_rate: float, heat_rate_mmbtu_mwh: float, price_45q_per_ton: float
) -> float:
    """Return the §45Q credit in $/MWh for a capture-equipped fuel-burner.

    ``captured tCO2/MWh = capture_rate x NG_CO2_TON_PER_MMBTU x heat_rate``; the
    credit is that tonnage x ``price_45q_per_ton`` (ADR 0012/0021). Zero for a
    non-fuel resource (``heat_rate == 0``).
    """
    captured_ton_mwh = capture_rate * NG_CO2_TON_PER_MMBTU * heat_rate_mmbtu_mwh
    return captured_ton_mwh * price_45q_per_ton


def breakeven_eac(
    *,
    capex_kw: float,
    fom_kw_yr: float,
    cf: float,
    hurdle_rate: float,
    term_years: float,
    expected_lmp_mwh: float,
    vom_mwh: float = 0.0,
    fuel_mwh: float = 0.0,
    credit_45q_mwh: float = 0.0,
    capacity_kw_yr: float = 0.0,
) -> float:
    """Return the breakeven EAC ($/MWh) clearing the IRR hurdle (ADR 0021).

    All-in required revenue per MWh (capital at the hurdle CRF + FOM, spread over
    ``8760 x CF``, plus VOM and fuel) minus the revenue offsets (expected LMP
    capture, the §45Q credit, and the capacity payment spread over the same MWh),
    floored at zero. ``capacity_kw_yr`` and ``credit_45q_mwh`` default to 0 so a
    plain renewable (no capacity market, no 45Q) needs only capex/FOM/LMP.

    Raises:
        ValueError: on a non-positive CF or term (both would divide by zero or
            invert the annualization).
    """
    if cf <= 0.0:
        raise ValueError(f"cf must be positive, got {cf}")
    if term_years <= 0.0:
        raise ValueError(f"term_years must be positive, got {term_years}")
    mwh_per_mw_yr = HOURS_PER_YEAR * cf
    crf = capital_recovery_factor(hurdle_rate, term_years)
    fixed_mwh = (crf * capex_kw + fom_kw_yr) * 1000.0 / mwh_per_mw_yr
    capacity_offset_mwh = capacity_kw_yr * 1000.0 / mwh_per_mw_yr
    required = fixed_mwh + vom_mwh + fuel_mwh
    offsets = expected_lmp_mwh + credit_45q_mwh + capacity_offset_mwh
    return max(0.0, required - offsets)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--capex-kw", type=float, required=True, help="overnight capex $/kW")
    p.add_argument("--fom-kw-yr", type=float, default=0.0, help="fixed O&M $/kW-yr")
    p.add_argument("--cf", type=float, required=True, help="capacity factor (0,1]")
    p.add_argument(
        "--hurdle-rate", type=float, default=0.09, help="developer IRR hurdle"
    )
    p.add_argument("--term-years", type=float, default=20.0, help="cost-recovery term")
    p.add_argument(
        "--expected-lmp", type=float, required=True, help="expected LMP capture $/MWh"
    )
    p.add_argument("--vom", type=float, default=0.0, help="variable O&M $/MWh")
    p.add_argument("--fuel", type=float, default=0.0, help="delivered fuel $/MWh")
    p.add_argument(
        "--iso", type=str, default=None, help="credit that ISO's capacity price"
    )
    p.add_argument(
        "--capacity-kw-yr",
        type=float,
        default=None,
        help="override the capacity revenue $/kW-yr (else the --iso registry value)",
    )
    # CCS 45Q inputs (optional): supply capture_rate + heat_rate to credit 45Q.
    p.add_argument("--capture-rate", type=float, default=0.0)
    p.add_argument("--heat-rate", type=float, default=0.0, help="MMBtu/MWh")
    p.add_argument("--price-45q", type=float, default=85.0, help="$/tCO2 (0 disables)")
    return p


def main(argv: list[str] | None = None) -> None:
    """CLI: print the breakeven EAC and its component breakdown."""
    args = _build_parser().parse_args(argv)
    if args.capacity_kw_yr is not None:
        capacity_kw_yr = args.capacity_kw_yr
    elif args.iso is not None:
        capacity_kw_yr = CAPACITY_PRICE_KW_YR.get(args.iso.strip().upper(), 0.0)
    else:
        capacity_kw_yr = 0.0
    credit = credit_45q_per_mwh(args.capture_rate, args.heat_rate, args.price_45q)
    eac = breakeven_eac(
        capex_kw=args.capex_kw,
        fom_kw_yr=args.fom_kw_yr,
        cf=args.cf,
        hurdle_rate=args.hurdle_rate,
        term_years=args.term_years,
        expected_lmp_mwh=args.expected_lmp,
        vom_mwh=args.vom,
        fuel_mwh=args.fuel,
        credit_45q_mwh=credit,
        capacity_kw_yr=capacity_kw_yr,
    )
    print(f"breakeven_eac_mwh: {eac:.4f}")
    print(f"  capacity_credit_kw_yr: {capacity_kw_yr:.2f}")
    print(f"  credit_45q_mwh:        {credit:.4f}")


if __name__ == "__main__":  # pragma: no cover
    main()
