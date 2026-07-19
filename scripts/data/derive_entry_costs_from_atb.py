#!/usr/bin/env python3
"""Derive ``NEW_ENTRY_COSTS`` / ``TECH_COST_MULTIPLIERS`` from the ATB parquet.

Closes the FF-0D audit's ``NEW_ENTRY_COSTS`` "STALE + UNWIRED" and
``TECH_COST_MULTIPLIERS`` "self-flagged" findings
(``docs/handoffs/ff-inputs-currency-audit-2026-07.md`` §3.2/§3.3, routed to
FF-1E in §7.2). Before FF-1E those two dicts were hand-transcribed round
numbers labelled "NREL ATB 2024" that matched no single ATB projection year
(wind ≈ ATB-2037, solar ≈ 2032, gas_cc ≈ 2049, nuclear_smr ≈ 2039 in the
Moderate case) — a decorative citation, never read from the ATB extract on
disk. This module makes the two dicts a *deterministic function* of the
committed ATB 2024 extract so they carry a real, testable provenance
(``tests/test_atb_entry_cost_consistency.py`` asserts the committed constants
equal this module's output — CLAUDE.md rule 23 source-consistency).

**Derivation (single documented basis).** For each entry technology the base
snapshot is ATB's own projection at a documented *base year* — 2026 (the model
start year / ``constants.REAL_DOLLAR_BASE_YEAR``) for the techs ATB publishes
from 2022, and 2030 for new nuclear (ATB's earliest published nuclear year;
ATB does not cost new nuclear before 2030). Values are read from ATB's
``Moderate`` cost case and converted from ATB 2024's 2022-USD basis to the
model's constant-2026-USD basis with the model's own documented long-run
deflator ``constants.INFLATION_RATE`` (2.2 %/yr), so every number traces to
(ATB value) × (1 + INFLATION_RATE) ** (2026 − 2022):

* ``NEW_ENTRY_COSTS[tech]["capex_per_kw"]`` = ATB Moderate CAPEX @ base year × F
* ``NEW_ENTRY_COSTS[tech]["fom_per_kw_yr"]`` = ATB Moderate Fixed O&M @ base year × F
* ``TECH_COST_MULTIPLIERS[tech]["low"]["capex_per_kw"]``  = Advanced/Moderate CAPEX @ base year
* ``TECH_COST_MULTIPLIERS[tech]["high"]["capex_per_kw"]`` = Conservative/Moderate CAPEX @ base year

The tech-cost multiplier ratios are dimensionless (the 2022→2026 deflator and
the dollar year cancel), so they are read directly from ATB's three cost cases
at the same base year — ATB's *actual* near-year Advanced/Conservative spread,
replacing the engineering-judgment magnitudes the dict's own comment flagged.

**Out of scope (kept on their existing citations).** ``base_cf``,
``learning_rate`` and ``lifetime_yr`` are NOT ATB CAPEX/Fixed-O&M quantities —
ATB's CF/heat-rate parameters and the Wright's-Law learning rates are
deliberately excluded from the committed extract
(``data/raw/nrel-atb/README.md``) — so this module does not touch them, and the
``learning_rate`` entries of ``TECH_COST_MULTIPLIERS`` (the trajectory-
divergence channel of the tech-cost lever) keep their documented judgment
basis. ``gas_cc_ccs`` is derived from ATB's 95 % CCS class (the nearest
published new-CCGT-CCS cost to the model's 90 % capture — see
``ENTRY_TECH_MAP``); its dispatch physics stay on CCUS_PARAMS' 90 %-capture
basis, only the capex/FOM cost basis is ATB's.

Reads only the committed raw ATB extract (via
:func:`scripts.data.curate_nrel_atb.parse`, which reads
``data/raw/nrel-atb/atb_2024_electricity_filtered*.csv``), so it runs in CI
with no clean-build step. Run ``python scripts/data/derive_entry_costs_from_atb.py``
to print the regenerated constant blocks.
"""

from __future__ import annotations

import argparse

import pandas as pd

from market_sim.config.constants import INFLATION_RATE, REAL_DOLLAR_BASE_YEAR
from scripts.data import curate_nrel_atb
from scripts.lib.clean_io import paths

# ATB edition and its published dollar-year basis (ATB 2024 v3.0.0 = 2022 USD;
# data/raw/nrel-atb/README.md "Network note" — the 2022$ basis is confirmed via
# NREL's ATB documentation, flagged there for browser re-verification).
ATB_EDITION_YEAR = 2024
ATB_DOLLAR_YEAR = 2022

# tech key -> (ATB technology, ATB techdetail, base projection year). The
# techdetail selections match data/raw/nrel-atb/README.md (each an ATB
# `default`=1 representative class, or an explicit verified string where ATB
# has no default). Base year is 2026 (= constants.REAL_DOLLAR_BASE_YEAR / the
# model start year) except new nuclear, whose earliest ATB projection year is
# 2030 (ATB does not cost new nuclear before 2030).
#
# gas_cc_ccs uses ATB's 95 % CCS class as the *cost* proxy for the model's
# 90 %-capture CCS: ATB 2024 publishes only 95 %/97 % CCS (no 90 %), 95 % is
# the nearest and slightly conservative on cost. This keeps every
# NEW_ENTRY_COSTS entry on one consistent ATB 2026-USD basis (leaving the host
# gas_cc on ATB but gas_cc_ccs on its older-dollar NETL basis made the capture
# island look nearly free). The unit's dispatch physics — heat-rate penalty and
# emission rate — still come from CCUS_PARAMS["gas_cc_ccs_90"] (90 % capture);
# only the capex/FOM cost basis is ATB's 95 % class.
ENTRY_TECH_MAP: dict[str, tuple[str, str, int]] = {
    "wind": ("LandbasedWind", "Class4", 2026),
    "solar": ("UtilityPV", "Class5", 2026),
    "gas_cc": ("NaturalGas_FE", "NG 2-on-1 Combined Cycle (F-Frame)", 2026),
    "gas_ct": ("NaturalGas_FE", "NG Combustion Turbine (F-Frame)", 2026),
    "nuclear_large": ("Nuclear", "Nuclear - Large", 2030),
    "nuclear_smr": ("Nuclear", "Nuclear - Small", 2030),
    "gas_cc_ccs": ("NaturalGas_FE", "NG 2-on-1 Combined Cycle (F-Frame) 95% CCS", 2026),
}

# Rounding applied to the committed constants (and to this module's output, so
# the source-consistency test compares like for like). Capex/FOM to 0.1 $/kW,
# ratios to 4 decimals — precision far below ATB's own significance, chosen so
# the constants read as derived (not round-number estimates) yet stay legible.
_CAPEX_DP = 1
_FOM_DP = 1
_RATIO_DP = 4


def inflation_factor() -> float:
    """ATB 2022-USD -> model 2026-USD deflator, from the model's own rate.

    Uses ``constants.INFLATION_RATE`` (the model's documented long-run
    deflator) over ``REAL_DOLLAR_BASE_YEAR - ATB_DOLLAR_YEAR`` years, so the
    conversion is internally consistent with every other real-dollar quantity
    in the model and needs no external CPI series.
    """
    return (1.0 + INFLATION_RATE) ** (REAL_DOLLAR_BASE_YEAR - ATB_DOLLAR_YEAR)


def load_atb(raw_root=None) -> pd.DataFrame:
    """Return the schema-shaped committed ATB extract (long/tidy frame)."""
    raw_root = raw_root if raw_root is not None else paths.RAW_DIR
    df = curate_nrel_atb.parse(raw_root)
    if df.empty:
        raise FileNotFoundError(
            "ATB raw extract not found under "
            f"{raw_root}/nrel-atb/ — run scripts/data/fetch_nrel_atb.py"
        )
    return df


def _value(
    df: pd.DataFrame, tech: str, detail: str, param: str, case: str, year: int
) -> float:
    """Return the single ATB value for one (tech, detail, param, case, year)."""
    row = df[
        (df["technology"] == tech)
        & (df["techdetail"] == detail)
        & (df["parameter"] == param)
        & (df["cost_case"] == case)
        & (df["year"] == year)
    ]
    if len(row) != 1:
        raise ValueError(
            f"expected exactly one ATB row for {tech}/{detail}/{param}/"
            f"{case}/{year}, found {len(row)}"
        )
    return float(row["value"].iloc[0])


def derive_new_entry_costs(
    df: pd.DataFrame | None = None,
) -> dict[str, dict[str, float]]:
    """Return ATB-derived ``{tech: {capex_per_kw, fom_per_kw_yr}}`` in 2026 USD."""
    if df is None:
        df = load_atb()
    factor = inflation_factor()
    out: dict[str, dict[str, float]] = {}
    for tech, (technology, detail, base_year) in ENTRY_TECH_MAP.items():
        capex = _value(df, technology, detail, "CAPEX", "Moderate", base_year)
        fom = _value(df, technology, detail, "Fixed O&M", "Moderate", base_year)
        out[tech] = {
            "capex_per_kw": round(capex * factor, _CAPEX_DP),
            "fom_per_kw_yr": round(fom * factor, _FOM_DP),
        }
    return out


def derive_tech_cost_multipliers(
    df: pd.DataFrame | None = None,
) -> dict[str, dict[str, dict[str, float]]]:
    """Return ATB-derived capex low/mid/high multipliers per entry tech.

    ``low`` = Advanced/Moderate CAPEX ratio, ``high`` = Conservative/Moderate
    CAPEX ratio (both at the tech's base year); ``mid`` is 1.0 by construction
    (the Moderate case is the base snapshot). ``learning_rate`` multipliers are
    NOT emitted here — they are not an ATB CAPEX/FOM quantity (see the module
    docstring) and keep their judgment basis in constants.py.
    """
    if df is None:
        df = load_atb()
    out: dict[str, dict[str, dict[str, float]]] = {}
    for tech, (technology, detail, base_year) in ENTRY_TECH_MAP.items():
        mod = _value(df, technology, detail, "CAPEX", "Moderate", base_year)
        adv = _value(df, technology, detail, "CAPEX", "Advanced", base_year)
        con = _value(df, technology, detail, "CAPEX", "Conservative", base_year)
        out[tech] = {
            "low": {"capex_per_kw": round(adv / mod, _RATIO_DP)},
            "mid": {"capex_per_kw": 1.0},
            "high": {"capex_per_kw": round(con / mod, _RATIO_DP)},
        }
    return out


def main(argv: list[str] | None = None) -> int:
    """Print the regenerated constant blocks for a copy into constants.py."""
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    df = load_atb()
    print(f"# inflation factor (2022$->2026$) = {inflation_factor():.6f}")
    print("\nNEW_ENTRY_COSTS capex/fom (2026$):")
    for tech, vals in derive_new_entry_costs(df).items():
        print(
            f"  {tech:14} capex_per_kw={vals['capex_per_kw']:>9} "
            f"fom_per_kw_yr={vals['fom_per_kw_yr']:>6}"
        )
    print("\nTECH_COST_MULTIPLIERS capex low/high (Advanced/Mod, Conservative/Mod):")
    for tech, vals in derive_tech_cost_multipliers(df).items():
        print(
            f"  {tech:14} low={vals['low']['capex_per_kw']:>7} "
            f"high={vals['high']['capex_per_kw']:>7}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
