"""F1-45U stage-1 (no-solve) measurement: §45U before/after on the MISO nuclear fleet.

Re-computes the IRA §45U existing-nuclear PTC per unit, in $/MWh and
$/kW-yr, under the PRE-FIX ordering (the 5x folded into the 0.3-cent rate,
then an unmultiplied §45U(b)(2)(A) reduction) and the POST-FIX statutory
ordering (§45U(d)(1)'s 5x applied to the subsection-(a) net), at the price
basis committed in docs/handoffs/d28-45u-composition-memo-2026-08-08.md
§2.2 -- MISO RT ATC $30.80/MWh (2024) and $42.85/MWh (2025).

It then places each unit's pro-forma going-forward margin against the
``fixed_om_nuclear`` $130/kW-yr bar under both orderings, which is the
stage-1 gate: stage 2 (a paired MISO forecast solve) fires ONLY if the fix
moves a unit across that bar.

Read-only. No solve, no LP, no clean-data dependency -- the fleet comes
from the raw EIA-860 operable file and every cost input from the shipped
config. Run::

    uv run python scripts/probes/_f1_45u_stage1_margin.py
"""

from __future__ import annotations

import pandas as pd

from market_sim.config.constants import NUCLEAR_MONTHLY_CF_BY_YEAR, VOM
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fuel import resolve_nuclear_fuel_price
from market_sim.policy.ira import (
    SECTION_45U_PHASE_DOWN_RATE,
    SECTION_45U_PREVAILING_WAGE_MULTIPLIER,
    section_45u_applicable_amounts_cents_per_kwh,
    section_45u_credit_per_mwh,
)

HOURS_PER_YEAR = 8760

# The 10-plant / 13-unit EIA-860 operable MISO nuclear fleet, by EIA plant
# code -- the same fleet constants.py's NUCLEAR_MONTHLY_CF["MISO"] entry
# describes (11,519 MW nameplate). Model zone per memo §2.1 table.
MISO_NUCLEAR_PLANTS: dict[int, tuple[str, str]] = {
    1922: ("Monticello", "MISO-West"),
    1925: ("Prairie Island", "MISO-West"),
    4046: ("Point Beach", "MISO-West"),
    204: ("Clinton", "MISO-Illinois"),
    1729: ("Fermi", "MISO-East"),
    6153: ("Callaway", "MISO-Plains"),
    6072: ("Grand Gulf", "MISO-South"),
    4270: ("Waterford 3", "MISO-South"),
    6462: ("River Bend", "MISO-South"),
    8055: ("Arkansas Nuclear One", "MISO-South"),
}

# Memo §2.2, all committed: MISO RT ATC price from the backcast bench
# sidecars (bench.avgLMP.rt), and the going-forward bar from the shipped
# ScenarioConfig.fixed_om_nuclear.
_NOMINAL_AMOUNT_YEAR = 2024  # (c)(1) factor 1.0000 -> the nominal 0.3c/2.5c pair

PRICE_BASIS: dict[int, float] = {2024: 30.80, 2025: 42.85}
GOING_FORWARD_BAR_USD_PER_KW_YR = ScenarioConfig().fixed_om_nuclear


def prefix_45u_credit_per_mwh(year: int, avg_price_per_mwh: float) -> float:
    """Return the PRE-FIX §45U credit: the 5x folded into the 0.3c rate.

    Reproduces the ordering this charter replaces (``ira.py`` before the
    F-1 fix): a 1.5-cent/kWh rate less an UNMULTIPLIED 16 % reduction, so
    the phase-down slope is 0.16 $/$ rather than 0.80 and the credit
    survives to $118.75/MWh. Nominal amounts only -- the pre-fix code had
    no §45U(c)(1) adjustment either (finding F-3).

    Args:
        year: Sale calendar year (unused; kept for call symmetry with the
            post-fix function, which is year-dependent through (c)(1)).
        avg_price_per_mwh: Gross-receipts basis in $/MWh.

    Returns:
        The pre-fix credit in $/MWh.
    """
    del year
    rate_cents = 0.3 * SECTION_45U_PREVAILING_WAGE_MULTIPLIER  # the folded 1.5c
    excess = max(0.0, avg_price_per_mwh / 10.0 - 2.5)
    return max(0.0, rate_cents - SECTION_45U_PHASE_DOWN_RATE * excess) * 10.0


def load_fleet() -> pd.DataFrame:
    """Return the MISO nuclear fleet with nameplate MW, one row per unit.

    Returns:
        DataFrame with plant/unit identity, model zone and nameplate MW.
    """
    df = pd.read_parquet("data/raw/eia-860/eia860_generator_operable.parquet")
    df = df[df["Plant Code"].isin(MISO_NUCLEAR_PLANTS)]
    df = df[df["Energy Source 1"].astype(str).str.upper() == "NUC"]
    # Summer capacity is the model's pmax convention: summing it over these
    # 13 units reproduces the 11,519 MW fleet nameplate that
    # constants.py's NUCLEAR_MONTHLY_CF_BY_YEAR["MISO"] comment cites.
    df = df.assign(
        plant=df["Plant Code"].map(lambda c: MISO_NUCLEAR_PLANTS[c][0]),
        zone=df["Plant Code"].map(lambda c: MISO_NUCLEAR_PLANTS[c][1]),
        pmax_mw=pd.to_numeric(df["Summer Capacity (MW)"], errors="coerce"),
    )
    return df[["plant", "zone", "Generator ID", "State", "pmax_mw"]].sort_values(
        ["zone", "plant", "Generator ID"]
    )


def fleet_capacity_factor(year: int) -> float:
    """Return the MISO nuclear fleet capacity factor for a measured year.

    Hours-weighted mean of the measured EIA-923 monthly CF overlay the
    model already ships (``NUCLEAR_MONTHLY_CF["MISO"]``), so the $/kW-yr
    conversion uses the same availability the LP would.

    Args:
        year: Measured year present in the overlay.

    Returns:
        The annual fleet capacity factor.
    """
    monthly = NUCLEAR_MONTHLY_CF_BY_YEAR["MISO"][year]
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return sum(cf * d for cf, d in zip(monthly, days)) / sum(days)


def main() -> None:
    """Print the stage-1 credit and margin-vs-bar tables."""
    config = ScenarioConfig()
    fleet = load_fleet()
    fuel = resolve_nuclear_fuel_price(config, 2026)
    heat_rate = 10.0  # MMBtu/MWh, constants.py:3245 (IAEA 2025)
    mc = fuel * heat_rate + VOM["nuclear"]

    print(f"MISO nuclear fleet: {len(fleet)} units, {fleet.pmax_mw.sum():,.0f} MW")
    print(f"nuclear mc = {fuel:.3f} $/MMBtu x {heat_rate} + {VOM['nuclear']} VOM")
    print(
        f"           = ${mc:.2f}/MWh;  bar = ${GOING_FORWARD_BAR_USD_PER_KW_YR}/kW-yr"
    )

    bar = GOING_FORWARD_BAR_USD_PER_KW_YR
    for year, price in PRICE_BASIS.items():
        cf = fleet_capacity_factor(year)
        mwh_per_kw_yr = cf * HOURS_PER_YEAR / 1000.0
        rate_c, thresh_c = section_45u_applicable_amounts_cents_per_kwh(year)
        before = prefix_45u_credit_per_mwh(year, price)
        # F-1 alone: the statutory ordering at the NOMINAL amounts, which is
        # the column the memo §2.3 table reports. F-1+F-3 additionally
        # applies the year's published (c)(1) amounts.
        f1_only = section_45u_credit_per_mwh(_NOMINAL_AMOUNT_YEAR, price, config)
        after = section_45u_credit_per_mwh(year, price, config)
        energy = (price - mc) * mwh_per_kw_yr

        print(f"\n=== {year}: RT ATC ${price}/MWh, fleet CF {cf:.4f} ===")
        print(f"  (c)(1) amounts: rate {rate_c}c  threshold {thresh_c}c")
        print(f"  $1/MWh = ${mwh_per_kw_yr:.2f}/kW-yr")
        for label, value in (
            ("before (HEAD)", before),
            ("F-1 only    ", f1_only),
            ("F-1+F-3     ", after),
        ):
            print(
                f"  §45U {label} {value:6.2f} $/MWh ="
                f" {value * mwh_per_kw_yr:7.2f} $/kW-yr"
            )
        for label, value in (("F-1 only", f1_only), ("F-1+F-3 ", after)):
            d = (before - value) * mwh_per_kw_yr
            print(
                f"  recovered vs HEAD, {label}: {before - value:6.2f} $/MWh ="
                f" {d:7.2f} $/kW-yr"
            )
        print(f"  energy margin (flat-price lower bound) {energy:.1f} $/kW-yr")
        print("  unit                 zone            MW   before    after  vs bar")
        for _, r in fleet.iterrows():
            m_before = energy + before * mwh_per_kw_yr
            m_after = energy + after * mwh_per_kw_yr
            crossed = (m_before >= bar) != (m_after >= bar)
            print(
                f"  {r.plant + ' ' + str(r['Generator ID']):<21}{r.zone:<13}"
                f"{r.pmax_mw:7.1f} {m_before:8.1f} {m_after:8.1f}"
                f"  {'CROSSES' if crossed else 'no'}"
            )

        # The two point evaluations above only test the committed price
        # basis. The crossing question is settled for ALL prices and ALL
        # capacity factors by asking where the POST-fix margin sits below
        # the bar while the PRE-fix margin sits above it: a crossing needs
        # m_after < bar <= m_before, and both are linear in the unit's CF.
        lo, hi = _crossing_cf_band(price, mc, before, after, bar)
        if lo is None:
            print("  crossing CF band: none at any capacity factor")
        else:
            print(
                f"  crossing CF band: {lo:.3f} <= CF < {hi:.3f}"
                f"  (modelled fleet CF {cf:.3f} -> {'INSIDE' if lo <= cf < hi else 'outside'})"
            )


def _crossing_cf_band(
    price: float, mc: float, before: float, after: float, bar: float
) -> tuple[float | None, float | None]:
    """Return the capacity-factor interval in which the fix crosses the bar.

    Going-forward margin is ``CF x 8760/1000 x (price - mc + credit)``, so
    it is linear in CF with a known slope under each ordering. A unit
    crosses the ``bar`` because of this fix exactly when its CF puts the
    post-fix margin below the bar and the pre-fix margin at or above it.

    Args:
        price: Energy price basis in $/MWh.
        mc: Nuclear variable cost in $/MWh.
        before: Pre-fix §45U credit in $/MWh.
        after: Post-fix §45U credit in $/MWh.
        bar: Going-forward cost bar in $/kW-yr.

    Returns:
        ``(lo, hi)`` capacity factors bounding the crossing band, or
        ``(None, None)`` when the two orderings coincide.
    """
    per_cf_before = (price - mc + before) * HOURS_PER_YEAR / 1000.0
    per_cf_after = (price - mc + after) * HOURS_PER_YEAR / 1000.0
    if per_cf_before <= 0.0 or per_cf_after <= 0.0 or before == after:
        return None, None
    return bar / per_cf_before, bar / per_cf_after


if __name__ == "__main__":
    main()
