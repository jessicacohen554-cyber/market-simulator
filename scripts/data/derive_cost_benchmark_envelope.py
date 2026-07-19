#!/usr/bin/env python3
"""Derive the cross-source literature envelope for new-build capital costs.

The capacity-cost-grounding session (2026-07-19; methodology + citations in
``docs/new-build-cost-methodology-2026-07.md``) widened the basis of the PB-1
tech-cost lever: ``constants.TECH_COST_MULTIPLIERS``' low/high capex ratios are
no longer NREL ATB's *internal* Advanced/Conservative spread alone (which is
near-degenerate at the 2026 base year for mature techs — the gas CT was
literally 1.0/1.0, an inert uncertainty lever) but the **published-cost
literature envelope**: the min/max across every in-envelope point of

* the pinned NREL ATB 2024 basis itself (Moderate mid + Advanced/Conservative
  points, from the committed ``data/raw/nrel-atb`` extract), and
* the cross-source benchmark table
  ``data/raw/new-build-cost-benchmarks/benchmarks_2026.csv`` (EIA/Sargent &
  Lundy Jan-2024 study, EIA AEO2026 EMM assumptions, Lazard LCOE+ v18.0,
  Brattle 2025 PJM CONE report; rows with ``in_envelope=1`` and ``verified=1``
  only),

each normalized to the model's constant-2026-USD basis with the model's own
``INFLATION_RATE`` convention (identical deflator rule to
``derive_entry_costs_from_atb.py``; the Brattle nominal-2028-online rows carry
``dollar_year=2028`` and deflate back). The **mid stays the pinned ATB 2024
Moderate value** (``NEW_ENTRY_COSTS``, unchanged — the anchor every default
run uses), so the envelope only changes what ``tech_cost_path="low"/"high"``
(and the PB-2 percentile sampler between them) can express. Mid=1.0 by
construction.

Also derives the ATB-based storage li-ion costs (4/8 hr read directly from the
committed battery rows at the 2026 base year; 12 hr from ATB's own exactly
linear power/energy cost split across its 2–10 hr classes), the offshore-wind
class costs (Class3 fixed-bottom @2026; Class12 floating @2030, its earliest
ATB year — same convention as nuclear), and the hydrogen-turbine costs (ATB
gas-turbine basis × the AEO2026-measured H2/frame-CT capex and FOM premium
ratios). ``tests/test_cost_benchmark_envelope.py`` asserts the committed
constants equal these derivations (CLAUDE.md rule 23).

Run ``python scripts/data/derive_cost_benchmark_envelope.py`` to print the
regenerated constant blocks and the per-technology envelope/validation table.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd

from market_sim.config.constants import INFLATION_RATE, REAL_DOLLAR_BASE_YEAR
from scripts.data import curate_nrel_atb
from scripts.data.derive_entry_costs_from_atb import (
    derive_new_entry_costs,
    derive_tech_cost_multipliers,
    inflation_factor,
    load_atb,
)
from scripts.lib.clean_io import paths

BENCHMARKS_CSV = paths.RAW_DIR / "new-build-cost-benchmarks" / "benchmarks_2026.csv"

# benchmarks_2026.csv model_tech key -> TECH_COST_MULTIPLIERS tech key. Only
# the entry techs the PB-1 lever covers participate; the storage / offshore /
# EGS / H2 envelope rows are reported (and documented in the methodology doc)
# but have no multiplier lever wired.
_ENVELOPE_TECHS: tuple[str, ...] = (
    "wind",
    "solar",
    "gas_cc",
    "gas_ct",
    "nuclear_smr",
    "nuclear_large",
    "gas_cc_ccs",
)

_RATIO_DP = 4
_COST_DP = 1

# AEO2026 EMM Table 3 (2025$/kW and 2025$/kW-yr, total overnight): the
# hydrogen-turbine and industrial-frame-CT rows, used as the measured
# H2-vs-gas premium ratios (dimensionless — the dollar year cancels).
# benchmarks_2026.csv rows aeo2026_h2_ct / aeo2026_gas_ct carry the same
# figures with their table citation; the consistency test cross-checks these
# literals against that CSV so the two records cannot drift apart.
_AEO2026_H2_CT_CAPEX = 1215.0
_AEO2026_FRAME_CT_CAPEX = 1158.0
_AEO2026_H2_CT_FOM = 8.59
_AEO2026_FRAME_CT_FOM = 7.18


def _deflator(dollar_year: int) -> float:
    """Published-dollar-year -> model 2026-USD factor (model convention)."""
    return (1.0 + INFLATION_RATE) ** (REAL_DOLLAR_BASE_YEAR - dollar_year)


def load_benchmarks(path: Path | None = None) -> list[dict]:
    """Return benchmarks_2026.csv rows as dicts (numeric fields floated)."""
    path = path if path is not None else BENCHMARKS_CSV
    rows: list[dict] = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            for k in list(row):
                if k.startswith(("capex_per_kw", "fom_per_kw_yr")):
                    row[k] = float(row[k]) if row[k] else None
            row["dollar_year"] = int(row["dollar_year"])
            row["in_envelope"] = row["in_envelope"] == "1"
            row["verified"] = row["verified"] == "1"
            rows.append(row)
    return rows


def envelope_points_2026(rows: list[dict], model_tech: str) -> list[tuple[str, float]]:
    """Return (source_id, capex 2026$/kW) for every enforced envelope point."""
    pts: list[tuple[str, float]] = []
    for row in rows:
        if row["model_tech"] != model_tech:
            continue
        if not (row["in_envelope"] and row["verified"]):
            continue
        f = _deflator(row["dollar_year"])
        for field in ("capex_per_kw_low", "capex_per_kw_mid", "capex_per_kw_high"):
            if row[field] is not None:
                pts.append((row["source_id"], row[field] * f))
    return pts


def derive_envelope_multipliers(
    df: pd.DataFrame | None = None, rows: list[dict] | None = None
) -> dict[str, dict[str, dict[str, float]]]:
    """Return the literature-envelope low/mid/high capex multipliers.

    low = (envelope min)/(ATB Moderate mid), high = (envelope max)/(mid); the
    envelope always contains the pinned ATB Advanced/Moderate/Conservative
    points, so it can never be narrower than ATB's own cost-case spread.
    """
    if df is None:
        df = load_atb()
    if rows is None:
        rows = load_benchmarks()
    mids = derive_new_entry_costs(df)
    atb_ratios = derive_tech_cost_multipliers(df)
    out: dict[str, dict[str, dict[str, float]]] = {}
    for tech in _ENVELOPE_TECHS:
        mid = mids[tech]["capex_per_kw"]
        pts = [v for _, v in envelope_points_2026(rows, tech)]
        pts += [
            mid * atb_ratios[tech]["low"]["capex_per_kw"],
            mid,
            mid * atb_ratios[tech]["high"]["capex_per_kw"],
        ]
        out[tech] = {
            "low": {"capex_per_kw": round(min(pts) / mid, _RATIO_DP)},
            "mid": {"capex_per_kw": 1.0},
            "high": {"capex_per_kw": round(max(pts) / mid, _RATIO_DP)},
        }
    return out


def derive_storage_li_ion(df: pd.DataFrame | None = None) -> dict[str, dict]:
    """ATB-derived li-ion storage costs (2026$): 4/8 hr read, 12 hr extended.

    ATB 2024's battery CAPEX is exactly linear in duration across its 2–10 hr
    classes (a fixed power component + a $/kWh energy slope; residual == 0 on
    the committed extract), so the 12 hr point is the same line evaluated at
    12 h — ATB's own cost structure, not a judgment extrapolation. FOM is
    linear the same way. ``capex_per_kwh`` is the bundled ``capex_per_kw /
    duration`` convention the storage screen's degradation term uses.
    """
    if df is None:
        df = load_atb()
    factor = inflation_factor()

    def val(det: str, param: str) -> float:
        r = df[
            (df["technology"] == "Utility-Scale Battery Storage")
            & (df["techdetail"] == det)
            & (df["parameter"] == param)
            & (df["cost_case"] == "Moderate")
            & (df["year"] == REAL_DOLLAR_BASE_YEAR)
        ]
        if len(r) != 1:
            raise ValueError(f"expected one ATB row for {det}/{param}, got {len(r)}")
        return float(r["value"].iloc[0])

    caps = {h: val(f"{h}Hr Battery Storage", "CAPEX") for h in (2, 4, 6, 8, 10)}
    foms = {h: val(f"{h}Hr Battery Storage", "Fixed O&M") for h in (2, 4, 6, 8, 10)}
    # Exact linear split (2022$): slope per added hour, intercept at 0 h.
    c_slope = (caps[10] - caps[2]) / 8.0
    c_int = caps[2] - 2.0 * c_slope
    f_slope = (foms[10] - foms[2]) / 8.0
    f_int = foms[2] - 2.0 * f_slope
    for h in (4, 6, 8):  # the split must reproduce every published class
        if abs(c_int + h * c_slope - caps[h]) > 1e-6:
            raise ValueError("ATB battery CAPEX is no longer linear in duration")
        if abs(f_int + h * f_slope - foms[h]) > 1e-6:
            raise ValueError("ATB battery FOM is no longer linear in duration")

    out: dict[str, dict] = {}
    for name, h in (("li_ion_4hr", 4), ("li_ion_8hr", 8), ("li_ion_12hr", 12)):
        capex22 = c_int + h * c_slope if h > 10 else caps[h]
        fom22 = f_int + h * f_slope if h > 10 else foms[h]
        capex = round(capex22 * factor, _COST_DP)
        out[name] = {
            "capex_per_kw": capex,
            "capex_per_kwh": round(capex / h, _COST_DP),
            "fom_per_kw_yr": round(fom22 * factor, _COST_DP),
        }
    return out


def derive_offshore_wind(df: pd.DataFrame | None = None) -> dict[str, dict]:
    """ATB-derived offshore costs (2026$): Class3 @2026, Class12 @2030."""
    if df is None:
        df = load_atb()
    factor = inflation_factor()
    out: dict[str, dict] = {}
    for key, det, base_year in (
        ("fixed_bottom", "Class3", REAL_DOLLAR_BASE_YEAR),
        ("floating", "Class12", 2030),  # ATB's earliest floating year
    ):
        r = df[
            (df["technology"] == "OffShoreWind")
            & (df["techdetail"] == det)
            & (df["cost_case"] == "Moderate")
            & (df["year"] == base_year)
        ]
        capex = float(r[r["parameter"] == "CAPEX"]["value"].iloc[0])
        fom = float(r[r["parameter"] == "Fixed O&M"]["value"].iloc[0])
        out[key] = {
            "capex_kw": round(capex * factor, _COST_DP),
            "fom_kw_yr": round(fom * factor, _COST_DP),
        }
    return out


def derive_egs_fom(df: pd.DataFrame | None = None) -> float:
    """ATB-derived EGS fixed O&M (2026$): NF-EGS Flash Moderate @2026.

    The cheapest published EGS-class FOM (the near-field flash class ATB
    treats as the first-mover EGS configuration) — a conservative-low choice
    coherent with ``GEOTHERMAL_PARAMS``' DOE-Liftoff-level capex sitting
    below ATB's EGS capex band. Requires the EGS rows added to the committed
    extract at the 2026-07-19 intake (``data/raw/nrel-atb`` part11+).
    """
    if df is None:
        df = load_atb()
    r = df[
        (df["technology"] == "Geothermal")
        & (df["techdetail"] == "NFEGSFlash")
        & (df["parameter"] == "Fixed O&M")
        & (df["cost_case"] == "Moderate")
        & (df["year"] == REAL_DOLLAR_BASE_YEAR)
    ]
    if len(r) != 1:
        raise ValueError(f"expected one NFEGSFlash FOM row, got {len(r)}")
    return round(float(r["value"].iloc[0]) * inflation_factor(), _COST_DP)


def derive_hydrogen_turbines() -> dict[str, dict]:
    """H2-turbine costs: ATB gas basis × AEO2026 measured H2/frame-CT ratios.

    ATB has no hydrogen-turbine class; the AEO2026 EMM (Table 3) publishes the
    only US-agency H2-turbine capex/FOM found ($1,215/kW, $8.59/kW-yr, 2025$,
    vs the industrial-frame CT's $1,158/$7.18). Applying those dimensionless
    premium ratios to the model's ATB-derived gas CT/CC costs keeps the
    H2-vs-gas entry competition on one ATB cost basis (mixing AEO's absolute
    FOM convention with ATB's would make H2 artificially cheap against its
    direct gas competitor — the two publishers' FOM scopes differ ~4×).
    """
    from market_sim.config.constants import NEW_ENTRY_COSTS

    r_capex = _AEO2026_H2_CT_CAPEX / _AEO2026_FRAME_CT_CAPEX
    r_fom = _AEO2026_H2_CT_FOM / _AEO2026_FRAME_CT_FOM
    out: dict[str, dict] = {}
    for key, host in (("h2_ct", "gas_ct"), ("h2_ccgt", "gas_cc")):
        out[key] = {
            "capex_kw": round(
                NEW_ENTRY_COSTS[host]["capex_per_kw"] * r_capex, _COST_DP
            ),
            "fom_kw_yr": round(
                NEW_ENTRY_COSTS[host]["fom_per_kw_yr"] * r_fom, _COST_DP
            ),
        }
    return out


def validation_table(
    df: pd.DataFrame | None = None, rows: list[dict] | None = None
) -> list[dict]:
    """Per-tech envelope + in/out verdict for the operative mid values."""
    if df is None:
        df = load_atb()
    if rows is None:
        rows = load_benchmarks()
    mids = derive_new_entry_costs(df)
    mults = derive_envelope_multipliers(df, rows)
    table = []
    for tech in _ENVELOPE_TECHS:
        mid = mids[tech]["capex_per_kw"]
        lo = mid * mults[tech]["low"]["capex_per_kw"]
        hi = mid * mults[tech]["high"]["capex_per_kw"]
        table.append(
            {
                "tech": tech,
                "mid_2026usd_per_kw": mid,
                "envelope_low": round(lo, _COST_DP),
                "envelope_high": round(hi, _COST_DP),
                "mid_within_envelope": lo <= mid <= hi,
            }
        )
    return table


def main(argv: list[str] | None = None) -> int:
    """Print the envelope table and regenerated constant blocks."""
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    df = curate_nrel_atb.parse(paths.RAW_DIR)
    rows = load_benchmarks()

    print("Literature envelope (2026$/kW) — mid = pinned ATB 2024 Moderate:")
    for line in validation_table(df, rows):
        print(
            f"  {line['tech']:14s} mid={line['mid_2026usd_per_kw']:>9} "
            f"env=[{line['envelope_low']:>9}, {line['envelope_high']:>9}] "
            f"{'OK' if line['mid_within_envelope'] else 'OUT OF ENVELOPE'}"
        )

    print("\nTECH_COST_MULTIPLIERS capex low/high (envelope/mid ratios):")
    for tech, cases in derive_envelope_multipliers(df, rows).items():
        print(
            f"  {tech:14s} low={cases['low']['capex_per_kw']:>7} "
            f"high={cases['high']['capex_per_kw']:>7}"
        )

    print("\nSTORAGE_TECHS li-ion (ATB Moderate @2026, 2026$):")
    for name, vals in derive_storage_li_ion(df).items():
        print(f"  {name:11s} {vals}")

    print("\nOFFSHORE_WIND_PARAMS (ATB Moderate, 2026$):")
    for name, vals in derive_offshore_wind(df).items():
        print(f"  {name:12s} {vals}")

    print("\nHYDROGEN_TURBINE_PARAMS (ATB gas basis × AEO2026 premium):")
    for name, vals in derive_hydrogen_turbines().items():
        print(f"  {name:8s} {vals}")

    print(f"\nGEOTHERMAL_PARAMS egs fom_kw_yr (ATB NF-EGS Flash): {derive_egs_fom(df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
