"""F2-45U stage-1 (no-solve) measurement: the §45U composition grid.

Extends the F-1 stage-1 probe (``_f1_45u_stage1_margin.py``, whose fleet
loader, capacity-factor reader and crossing-band algebra this module
imports rather than restates) from the §45U *ordering* question to the
§45U *composition* question -- owner decision D-28,
``docs/handoffs/d28-45u-composition-memo-2026-08-08.md`` §2.3.

Four compositions of a clean-attribute dual ``D`` with the credit, at an
energy price ``P``:

* **(a) naive add** -- ``§45U(P) + D`` on an ENERGY-ONLY basis.
* **(b) max -- HEAD before this charter** -- ``max(§45U(P), D)``.
* **(c) statute branch (i)** -- ``D + §45U(P + D)``: a state
  zero-emission-program payment is INSIDE the gross-receipts base
  (26 U.S.C. §45U(b)(2)(B)(i)). The composition this charter adopts for
  LSE-paid compliance certificates (Arm 3, the federal CES, the RPS row).
* **(d) statute branch (iii)** -- ``max(D, §45U(P))``: the state program
  itself nets the federal credit out, so its payment leaves the base
  (§45U(b)(2)(B)(iii)). What ``eac_price_nuclear`` (NY ZEC / IL CMC) is.

Each grid is printed on TWO curves, because F-1 and F-3 landed between the
memo and this charter and moved the credit:

* the **nominal** curve, reproducing the memo's §2.3 table as published --
  (a)/(b) on the PRE-F-1 credit that was HEAD when the memo was written,
  (c)/(d) on the statutory ordering at the nominal 0.3c/2.5c amounts;
* the **post-F-1/F-3** curve -- all four compositions on the credit the
  repo actually ships today, including the §45U(c)(1) applicable amounts
  for the sale year.

Read-only. No solve, no LP, no clean-data dependency. Run::

    uv run python scripts/probes/_f2_45u_stage1_composition.py
"""

from __future__ import annotations

from market_sim.config.constants import VOM
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fuel import resolve_nuclear_fuel_price
from market_sim.policy.ira import (
    section_45u_applicable_amounts_cents_per_kwh,
    section_45u_credit_per_mwh,
)

# Sibling probe in this same directory, which Python puts on sys.path[0] when
# the module is run as a script (the documented invocation below).
from _f1_45u_stage1_margin import (
    GOING_FORWARD_BAR_USD_PER_KW_YR,
    HOURS_PER_YEAR,
    PRICE_BASIS,
    _NOMINAL_AMOUNT_YEAR,
    _crossing_cf_band,
    fleet_capacity_factor,
    load_fleet,
    prefix_45u_credit_per_mwh,
)

# The dual levels the memo's §2.3 table walks: no clean row, an interior
# dual, and the MISO clean-row alternative-compliance-payment ceiling
# (STATE_RPS_ACP["MISO"], config/capacity_market.py) -- the level Arm 3 is
# most likely to actually produce, since an ACP caps the dual.
DUAL_LEVELS_USD_PER_MWH: tuple[float, ...] = (0.0, 10.0, 30.0)
MISO_CLEAN_ROW_ACP_USD_PER_MWH = 30.0


def compositions(
    price: float, dual: float, credit_of
) -> tuple[float, float, float, float]:
    """Return ``(a, b, c, d)`` total attribute+credit revenue in $/MWh.

    Args:
        price: Energy price ``P`` in $/MWh.
        dual: Clean-attribute price ``D`` in $/MWh.
        credit_of: Callable mapping a gross-receipts basis in $/MWh to the
            §45U credit in $/MWh. Passing the pre-fix or the shipped credit
            is what selects the nominal or the post-F-1/F-3 curve.

    Returns:
        The four compositions in the order (a) naive add, (b) max,
        (c) branch (i), (d) branch (iii).
    """
    return (
        credit_of(price) + dual,
        max(credit_of(price), dual),
        dual + credit_of(price + dual),
        max(dual, credit_of(price)),
    )


def max_composition_gap(price: float, credit_of) -> tuple[float, float]:
    """Return the largest ``(c) - (b)`` gap over all duals, and where it is.

    Scans ``D`` on a fine grid rather than solving the kink algebra: both
    compositions are piecewise linear in ``D`` with breakpoints only where
    the credit dies or where ``D`` overtakes the credit, so a 1-cent grid
    resolves the maximum exactly to the cent -- which is the precision the
    charter asks the coincidence check to hold to.

    Args:
        price: Energy price ``P`` in $/MWh.
        credit_of: Gross-receipts basis -> §45U credit, in $/MWh.

    Returns:
        ``(gap, dual_at_gap)`` in $/MWh.
    """
    best = (0.0, 0.0)
    for step in range(0, 6001):  # D from $0 to $60 in 1-cent steps
        dual = step / 100.0
        _, b, c, _ = compositions(price, dual, credit_of)
        if c - b > best[0]:
            best = (c - b, dual)
    return best


def main() -> None:
    """Print the composition grid, the coincidence checks and the bar test."""
    config = ScenarioConfig()
    fleet = load_fleet()
    fuel = resolve_nuclear_fuel_price(config, 2026)
    heat_rate = 10.0  # MMBtu/MWh, constants.py (IAEA 2025)
    mc = fuel * heat_rate + VOM["nuclear"]
    bar = GOING_FORWARD_BAR_USD_PER_KW_YR

    print(f"MISO nuclear fleet: {len(fleet)} units, {fleet.pmax_mw.sum():,.0f} MW")
    print(f"nuclear mc = ${mc:.2f}/MWh;  bar = ${bar}/kW-yr")
    print(
        "compositions: (a) naive add | (b) max = HEAD | "
        "(c) branch (i) = ADOPTED | (d) branch (iii)"
    )

    for year, price in PRICE_BASIS.items():
        cf = fleet_capacity_factor(year)
        mwh_per_kw_yr = cf * HOURS_PER_YEAR / 1000.0
        rate_c, thresh_c = section_45u_applicable_amounts_cents_per_kwh(year)

        # The memo's table as published: (a)/(b) on the pre-F-1 credit that
        # was HEAD when it was written, (c)/(d) statutory at the NOMINAL
        # amounts. Reproduced, not re-baselined (charter).
        def nominal_credit(basis: float) -> float:
            return section_45u_credit_per_mwh(_NOMINAL_AMOUNT_YEAR, basis, config)

        # The curve the repo actually ships after F-1 + F-3.
        def shipped_credit(basis: float, _year: int = year) -> float:
            return section_45u_credit_per_mwh(_year, basis, config)

        print(f"\n=== {year}: P = ${price}/MWh, fleet CF {cf:.4f} ===")
        print(f"  (c)(1) amounts: rate {rate_c}c  threshold {thresh_c}c")
        print(f"  $1/MWh = ${mwh_per_kw_yr:.2f}/kW-yr")

        print("\n  -- memo curve (as published: (a)/(b) pre-F-1) --")
        print("     D      (a)      (b)      (c)      (d)   (b)-(c)")
        for dual in DUAL_LEVELS_USD_PER_MWH:
            a = prefix_45u_credit_per_mwh(year, price) + dual
            b = max(prefix_45u_credit_per_mwh(year, price), dual)
            _, _, c, d = compositions(price, dual, nominal_credit)
            print(f"  {dual:5.1f} {a:8.2f} {b:8.2f} {c:8.2f} {d:8.2f} {b - c:9.2f}")

        print("\n  -- shipped curve (post-F-1/F-3, all four on today's credit) --")
        print("     D      (a)      (b)      (c)      (d)   (c)-(b)   $/kW-yr")
        for dual in DUAL_LEVELS_USD_PER_MWH:
            a, b, c, d = compositions(price, dual, shipped_credit)
            print(
                f"  {dual:5.1f} {a:8.2f} {b:8.2f} {c:8.2f} {d:8.2f} "
                f"{c - b:9.2f} {(c - b) * mwh_per_kw_yr:9.2f}"
            )

        # Charter check 1: (b) and (c) coincide at the ACP ceiling to the cent.
        _, b_acp, c_acp, d_acp = compositions(
            price, MISO_CLEAN_ROW_ACP_USD_PER_MWH, shipped_credit
        )
        print(
            f"\n  ACP ceiling D=${MISO_CLEAN_ROW_ACP_USD_PER_MWH:.0f}: "
            f"(b)={b_acp:.2f} (c)={c_acp:.2f} (d)={d_acp:.2f} -> "
            f"{'COINCIDE to the cent' if round(b_acp - c_acp, 2) == 0.0 else 'DIVERGE'}"
        )

        # Charter check 2: what the composition choice alone is worth, over
        # ALL duals, not just the three tabulated levels.
        gap, at_dual = max_composition_gap(price, shipped_credit)
        print(
            f"  composition (c)-(b) over all D: max ${gap:.2f}/MWh at D=${at_dual:.2f}"
            f"  = ${gap * mwh_per_kw_yr:.2f}/kW-yr"
        )

        # Charter check 3: margin vs the $130/kW-yr bar, settled in CF space
        # rather than at the two tabulated price points. (c) >= (b) always, so
        # a crossing is a unit that retires under (b) and survives under (c).
        print(f"  crossing vs the ${bar}/kW-yr bar, by dual:")
        for dual in DUAL_LEVELS_USD_PER_MWH:
            _, b, c, _ = compositions(price, dual, shipped_credit)
            lo, hi = _crossing_cf_band(price, mc, c, b, bar)
            if lo is None:
                print(
                    f"    D={dual:5.1f}: (b)={b:.2f} == (c)={c:.2f} -> "
                    "no crossing at ANY capacity factor"
                )
                continue
            inside = lo <= cf < hi
            print(
                f"    D={dual:5.1f}: crossing CF band {lo:.3f} <= CF < {hi:.3f}"
                f"  (fleet CF {cf:.3f} -> {'INSIDE' if inside else 'outside'})"
            )

        # Charter scope guard: eac_price_nuclear's branch. The memo's §5 CARD
        # puts it in branch (i) alongside the compliance certificates; the
        # memo's own §5 "right for the wrong reason" bullet documents it as a
        # NY-ZEC / IL-CMC netting contract, i.e. branch (iii). This charter
        # adopts branch (iii); the two differ only where the credit is still
        # live ON TOP of the contract, i.e. where P + ZEC is under the
        # credit's zero-out basis.
        zec = ScenarioConfig().eac_price_nuclear or 17.0  # documented NY/IL level
        adopted = max(zec, shipped_credit(price))
        card = zec + shipped_credit(price + zec)
        rate_usd = rate_c * 10.0
        zero_out_basis = thresh_c * 10.0 + rate_usd / 0.16
        print(
            f"\n  eac_price_nuclear branch check at the documented ${zec:.0f} ZEC:"
            f" adopted (iii) = ${adopted:.2f}/MWh, memo card (i) = ${card:.2f}/MWh"
            f" -> {'IDENTICAL' if round(adopted - card, 2) == 0.0 else 'DIVERGE'}"
        )
        print(
            f"    they can only diverge below P = ${zero_out_basis - zec:.2f}/MWh"
            f" (credit zero-out basis ${zero_out_basis:.2f} less the ZEC);"
            f" committed basis is P = ${price}/MWh"
        )
        lo, hi = _crossing_cf_band(price, mc, card, adopted, bar)
        print(
            "    bar crossing between the two readings: "
            + (
                "none at ANY capacity factor"
                if lo is None
                else f"CF band {lo:.3f} <= CF < {hi:.3f} (fleet CF {cf:.3f})"
            )
        )


if __name__ == "__main__":
    main()
