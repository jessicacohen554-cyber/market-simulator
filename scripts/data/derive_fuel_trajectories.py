"""Derive AEO-grounded fuel-price trajectories: gas, coal, oil, and a
$/MMBtu nuclear fuel-cycle cost — CLAUDE.md rule 23 re-derivation triggered by
the P-0C data intake (data/raw/eia-aeo/, data/raw/uranium-marketing/).

VINTAGE (FF-G2, 2026-07-20): the default edition is now **AEO2026** (released
2026-04-08), bumped from AEO2025 under rule 23 — the trigger is the source-data
edition change, not a residual. Two edition differences the code handles: (a)
AEO2026 is published in real **2025$** (AEO2025 was 2024$), carried into the
printed block labels; (b) AEO2026 renamed its central case "Reference" ->
"Counterfactual Baseline" (scenario id ``ref2025`` -> ``cb2026``), still the
central projection the model's "mid" path tracks (EIA AEO2026 narrative).
Re-derive an earlier edition with ``--aeo-year 2025``. Nuclear fuel is NOT
re-derived by the AEO bump (its EIA-UMAR source is unchanged) and stays in
2024$.

WHY THIS SCRIPT EXISTS: ``HENRY_HUB_TRAJECTORIES`` (constants.py) carried a
standing "TODO: verify against AEO Table 13" since it was hand-typed from
"published AEO2025 charts and text" rather than the AEO data tables (D2,
docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md). P-0C
landed the real API-fetched AEO2025 series
(data/raw/eia-aeo/eia_aeo2025_fuel_prices.part*.csv) plus the EIA Uranium
Marketing Annual Report front-end fuel-cycle prices
(data/raw/uranium-marketing/eia_umar_uranium_price.csv). This script re-derives
every fuel trajectory FROM that data (never from a residual) and prints
paste-ready literals for ``constants.py`` — the same paste-from-derive-script
convention as ``derive_coal_sigmoid.py``.

GAS: AEO2025 Table 13 Henry Hub spot, real 2024$/MMBtu. AEO scenario ->
model path: highogs -> "low" (more supply, lower price), ref2025 -> "mid",
lowogs -> "high" (less supply, higher price) — same mapping the prior
hand-typed table used (constants.py comment above HENRY_HUB_TRAJECTORIES).
The 2023-2025 historical-actual entries are UNCHANGED (they are measured
spot averages, not AEO projections, and predate the AEO's 2024-2050 window).

COAL: AEO2025 Table 15 delivered-to-electric-power, national, real
2024$/MMBtu. The model's ``COAL_PRICE_BASE`` stays a per-ISO delivered-cost
ANCHOR (ERCOT lignite/PRB vs PJM Appalachian vs MISO PRB+ILB blend are
genuinely different basins the one national AEO series can't resolve — the
CLAUDE.md rule-14 misalignment exception) — but the flat, uncited
``COAL_PRICE_ESCALATION`` (1%/yr) forward-YEAR SHAPE is replaced by the AEO's
own real growth path, applied as a ratio to each ISO's anchor
(``COAL_PRICE_TRAJECTORIES[path][year] / COAL_PRICE_TRAJECTORIES[path]
[ISO_ANCHOR_YEAR]``) so each ISO keeps its own level while tracking the AEO's
real trend instead of a guessed constant rate.

OIL: AEO2025 Table 12 electric-power distillate + residual, real
2024$/MMBtu, averaged (matching ``OIL_PRICE_PER_MMBTU``'s existing "distillate
~$20 + residual ~$14, averaged" documented construction) per AEO scenario.

NUCLEAR FUEL ($/MMBtu): the EIA Uranium Marketing Annual Report publishes no
$/MMBtu nuclear fuel series — only front-end U3O8 and SWU (enrichment)
prices (nominal $, per data/raw/uranium-marketing/README.md). This script
builds up a $/MMBtu delivered fuel cost from the standard LWR fuel-cycle
physical constants (World Nuclear Association, "Nuclear Fuel Cycle" —
producing 1 kg of ~4.4% LEU at a 0.25-0.3% tails assay takes ~8.9 kg natural
U3O8 and ~7.3 SWU of enrichment work; U3O8 is 84.8% U by mass, so the
elemental-U feed is ~7.55 kgU/kgLEU) plus published conversion
(~$10/kgU, WNA "The Economics of Nuclear Power", conversion-services range)
and fabrication (~$300/kgLEU, WNA fabrication cost range) costs — neither of
which the UMAR publishes a time series for (documented in the README as this
script's job) — held flat in real terms since no AEO or EIA forward series
exists for either. The heat content divisor uses a representative U.S. LWR
burnup of 45,000 MWd/tHM (NRC/EIA-cited current-fleet average) converted to
MWh-thermal per kg, then to $/MMBtu at 3.412142 MMBtu/MWh. UMAR prices are
NOMINAL (not inflation-adjusted, per its own footnote); this script deflates
each year to real 2024$ using the model's own ``INFLATION_RATE`` (2.2%/yr)
before applying the fuel-cycle formula, so the output is directly comparable
to the real-2024$ AEO series.

EXTRAPOLATION: fuel.py:178's forward extrapolation beyond a trajectory's last
knot year used the LAST YEAR-OVER-YEAR RATIO compounded indefinitely — a
silent, unbounded driver with no citation. This script does not change that
code (see market_sim.data.fuel._extrapolate_flat, the fix in the same P-1D
session); every trajectory table below carries an explicit final-year entry
so hold-flat extrapolation has a real anchor.
"""

from __future__ import annotations

import argparse
import glob
import logging

import pandas as pd

from market_sim.config.constants import INFLATION_RATE
from market_sim.config.paths import RAW_DATA_DIR

logger = logging.getLogger(__name__)

AEO_DIR = RAW_DATA_DIR / "eia-aeo"
URANIUM_CSV = RAW_DATA_DIR / "uranium-marketing" / "eia_umar_uranium_price.csv"

# The AEO edition this script re-derives against by default. Bumped
# 2025 -> 2026 for the FF-G2 vintage refresh (CLAUDE.md rule 23: source-data
# change is the AEO2025 -> AEO2026 edition bump). AEO2026 (released 2026-04-08)
# is in real **2025$** (AEO2025 was 2024$) and renamed its central case
# "Reference" -> "Counterfactual Baseline" (cb2026); see the module docstring.
DEFAULT_AEO_YEAR: int = 2026

# AEO edition -> {scenario id: model gas/coal/oil price-path lever}. The
# central-case scenario id is edition-specific (ref2025 -> cb2026); the
# High/Low Oil and Gas Supply side cases keep their ids. Mirrors
# scripts/data/fetch_eia_aeo.py::SCENARIOS_BY_AEO so the two stay in lockstep.
_SCENARIO_TO_PATH_BY_AEO: dict[int, dict[str, str]] = {
    2025: {"highogs": "low", "ref2025": "mid", "lowogs": "high"},
    2026: {"highogs": "low", "cb2026": "mid", "lowogs": "high"},
}

# --- Nuclear fuel-cycle physical constants (World Nuclear Association,
# "Nuclear Fuel Cycle" / "Economics of Nuclear Power", ~4.4% LEU / 0.25-0.3%
# tails assay reference cycle) ---
_KG_U3O8_PER_KG_LEU: float = 8.9
_SWU_PER_KG_LEU: float = 7.3
_U3O8_URANIUM_MASS_FRACTION: float = 0.848  # U3O8 is 84.8% U by mass
_LB_PER_KG: float = 2.20462
_CONVERSION_COST_PER_KGU: float = 10.0  # $/kgU, WNA conversion-services range
_FABRICATION_COST_PER_KG_LEU: float = 300.0  # $/kgLEU, WNA fabrication range
_BURNUP_MWD_PER_TU: float = 45_000.0  # NRC/EIA-cited current US LWR average
_MMBTU_PER_MWH: float = 3.412142

# EIA heat content of fuel oil delivered to the electric power sector
# (MMBtu/gal) — the AEO Table 12 series is priced in $/gal, not $/MMBtu.
# Source: EIA Monthly Energy Review, Appendix A3/A5 fuel heat contents.
_DISTILLATE_MMBTU_PER_GAL: float = 0.1385  # No. 2 distillate fuel oil
_RESIDUAL_MMBTU_PER_GAL: float = 0.1497  # No. 6 residual fuel oil


def _load_aeo(aeo_year: int = DEFAULT_AEO_YEAR) -> pd.DataFrame:
    single = AEO_DIR / f"eia_aeo{aeo_year}_fuel_prices.csv"
    if single.exists():
        return pd.read_csv(single)
    files = sorted(glob.glob(str(AEO_DIR / f"eia_aeo{aeo_year}_fuel_prices.part*.csv")))
    if not files:
        raise FileNotFoundError(
            f"no AEO{aeo_year} fuel-price CSV found under {AEO_DIR}"
        )
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def derive_gas_trajectory(
    aeo: pd.DataFrame, scenario_to_path: dict[str, str]
) -> dict[str, dict[int, float]]:
    """Return ``{path: {year: $/MMBtu}}`` from AEO Table 13 Henry Hub spot."""
    rows = aeo[(aeo["fuel"] == "gas") & (aeo["metric"] == "henry_hub_spot")]
    out: dict[str, dict[int, float]] = {}
    for scenario, path in scenario_to_path.items():
        sub = rows[rows["scenario"] == scenario].sort_values("year")
        out[path] = {
            int(y): round(float(v), 2) for y, v in zip(sub["year"], sub["value"])
        }
    return out


def derive_coal_trajectory(
    aeo: pd.DataFrame, scenario_to_path: dict[str, str]
) -> dict[str, dict[int, float]]:
    """Return ``{path: {year: $/MMBtu}}`` from AEO Table 15 national delivered coal."""
    rows = aeo[
        (aeo["fuel"] == "coal")
        & (aeo["metric"] == "delivered_electric_power")
        & (aeo["region"] == "usa")
    ]
    out: dict[str, dict[int, float]] = {}
    for scenario, path in scenario_to_path.items():
        sub = rows[rows["scenario"] == scenario].sort_values("year")
        out[path] = {
            int(y): round(float(v), 4) for y, v in zip(sub["year"], sub["value"])
        }
    return out


def derive_oil_trajectory(
    aeo: pd.DataFrame, scenario_to_path: dict[str, str]
) -> dict[str, dict[int, float]]:
    """Return ``{path: {year: $/MMBtu}}`` averaging AEO distillate + residual
    electric-power fuel oil prices (matching ``OIL_PRICE_PER_MMBTU``'s
    existing documented blend construction).

    The AEO series is priced in $/gal (Table 12); each is converted to
    $/MMBtu via its EIA heat content (:data:`_DISTILLATE_MMBTU_PER_GAL`,
    :data:`_RESIDUAL_MMBTU_PER_GAL`) before averaging.
    """
    dist = aeo[(aeo["fuel"] == "oil") & (aeo["metric"] == "electric_power_distillate")]
    resid = aeo[(aeo["fuel"] == "oil") & (aeo["metric"] == "electric_power_residual")]
    out: dict[str, dict[int, float]] = {}
    for scenario, path in scenario_to_path.items():
        d = (
            dist[dist["scenario"] == scenario].set_index("year")["value"]
            / _DISTILLATE_MMBTU_PER_GAL
        )
        r = (
            resid[resid["scenario"] == scenario].set_index("year")["value"]
            / _RESIDUAL_MMBTU_PER_GAL
        )
        years = sorted(set(d.index) & set(r.index))
        out[path] = {int(y): round(float((d[y] + r[y]) / 2.0), 2) for y in years}
    return out


def derive_nuclear_fuel_trajectory() -> dict[int, float]:
    """Return ``{year: $/MMBtu}`` real-2024$ nuclear fuel cost, 2006-2024.

    Only years with BOTH a U3O8 price and a SWU price are resolvable (SWU
    series starts 2006, per the README); years before that are not derived
    (no guessing, CLAUDE.md rule).
    """
    df = pd.read_csv(URANIUM_CSV)
    u3o8_nominal = df[df["metric"] == "total_purchased_price"].set_index(
        "delivery_year"
    )["value"]
    swu_nominal = df[df["metric"] == "enrichment_services_price"].set_index(
        "delivery_year"
    )["value"]
    years = sorted(set(u3o8_nominal.index) & set(swu_nominal.index))
    out: dict[int, float] = {}
    for year in years:
        deflator = (1.0 + INFLATION_RATE) ** (2024 - year)
        u3o8_real = float(u3o8_nominal[year]) * deflator
        swu_real = float(swu_nominal[year]) * deflator

        kg_u_per_kg_leu = _KG_U3O8_PER_KG_LEU * _U3O8_URANIUM_MASS_FRACTION
        uranium_cost = u3o8_real * _KG_U3O8_PER_KG_LEU * _LB_PER_KG
        conversion_cost = _CONVERSION_COST_PER_KGU * kg_u_per_kg_leu
        enrichment_cost = swu_real * _SWU_PER_KG_LEU
        total_per_kg_leu = (
            uranium_cost
            + conversion_cost
            + enrichment_cost
            + _FABRICATION_COST_PER_KG_LEU
        )

        mwh_thermal_per_kg = _BURNUP_MWD_PER_TU * 24.0 / 1000.0  # MWd/tU -> MWh_th/kgU
        mmbtu_per_kg = mwh_thermal_per_kg * _MMBTU_PER_MWH
        out[int(year)] = round(total_per_kg_leu / mmbtu_per_kg, 4)
    return out


def _print_dict_literal(name: str, table: dict) -> None:
    print(f"{name}: dict[int, float] = {{")
    for year, value in table.items():
        print(f"    {year}: {value},")
    print("}")


def _print_path_literal(name: str, table: dict[str, dict[int, float]]) -> None:
    print(f"{name}: dict[str, dict[int, float]] = {{")
    for path, series in table.items():
        print(f'    "{path}": {{')
        for year, value in series.items():
            print(f"        {year}: {value},")
        print("    },")
    print("}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--aeo-year",
        type=int,
        default=DEFAULT_AEO_YEAR,
        help=(
            "AEO edition to derive against (default "
            f"{DEFAULT_AEO_YEAR}); reads data/raw/eia-aeo/eia_aeo<year>_"
            "fuel_prices.csv"
        ),
    )
    args = parser.parse_args()

    aeo_year = args.aeo_year
    scenario_to_path = _SCENARIO_TO_PATH_BY_AEO[aeo_year]
    aeo = _load_aeo(aeo_year)
    # AEO2026 is published in 2025$; AEO2025 was 2024$. Label the printed
    # blocks with the edition's own real-dollar basis so the paste carries the
    # correct citation. Coal enters the model as a dollar-year-invariant RATIO
    # to each ISO's own anchor (resolve_annual_coal_price), so its dollar basis
    # never affects a delivered price; gas and oil enter as absolute levels.
    dollar_year = {2025: 2024, 2026: 2025}[aeo_year]
    tag = f"AEO{aeo_year}"

    print(
        f"# --- HENRY_HUB_TRAJECTORIES ({tag} Table 13, real {dollar_year}$/MMBtu) ---"
    )
    _print_path_literal(
        f"HENRY_HUB_{tag}", derive_gas_trajectory(aeo, scenario_to_path)
    )
    print()
    print(
        f"# --- COAL_PRICE_TRAJECTORIES ({tag} Table 15 national delivered, "
        f"real {dollar_year}$/MMBtu) ---"
    )
    _print_path_literal(
        "COAL_PRICE_TRAJECTORIES", derive_coal_trajectory(aeo, scenario_to_path)
    )
    print()
    print(
        f"# --- OIL_PRICE_TRAJECTORIES ({tag} Table 12 distillate+residual "
        f"average, real {dollar_year}$/MMBtu) ---"
    )
    _print_path_literal(
        "OIL_PRICE_TRAJECTORIES", derive_oil_trajectory(aeo, scenario_to_path)
    )
    print()
    # Nuclear fuel is NOT re-derived by the AEO bump: its source (EIA Uranium
    # Marketing Annual Report) is unchanged, so under CLAUDE.md rule 23 it is
    # not re-triggered and stays in its own real-2024$ basis. Printed here for
    # completeness only; the FF-G2 refresh leaves NUCLEAR_FUEL_PRICE_HISTORICAL
    # byte-identical.
    print(
        "# --- NUCLEAR_FUEL_PRICE_HISTORICAL (EIA UMAR-derived fuel-cycle "
        "cost, real 2024$/MMBtu — UNCHANGED by the AEO bump; source not updated) ---"
    )
    _print_dict_literal(
        "NUCLEAR_FUEL_PRICE_HISTORICAL", derive_nuclear_fuel_trajectory()
    )


if __name__ == "__main__":
    main()
