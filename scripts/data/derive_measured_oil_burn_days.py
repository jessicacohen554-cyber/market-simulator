"""Derive measured plant-day oil burn (oil share of gas-unit heat input) from CAMPD.

The measured input behind ``ScenarioConfig.dual_fuel_measured_oil_burn``
(soco-96, owner ruling 2026-09-30, decision card answer verbatim: "Oil price at
measured burn"). The consumer,
:func:`market_sim.data.fuel.apply_measured_oil_burn_pricing`, prices each gas
generator on a covered plant-day at ``f * oil + (1 - f) * gas``; this script
produces ``f``.

Construction (zero free parameters — no threshold, no scaling; rules 5 / 21):

1. **Scope.** The ISO's gas plants: every EIA plant code carrying a gas
   generator (``gas_cc`` / ``gas_ct`` / ``gas_st`` / ``gas_cc_ccs``) in the
   ISO's model fleet, the union of the solve year's own EIA-860 vintage fleet
   and the canonical fleet (so a plant retired before the canonical release is
   still covered in the years it ran). Within those facilities a CAMPD unit is
   ELIGIBLE iff its ``primaryFuelInfo`` names natural gas and names no coal or
   wood, **and it is not coal-capable** (step 2).
2. **Coal-capable exclusion** (coordinator ruling, soco-96 follow-up). The
   identity below is two-fuel (gas/oil); a unit that can burn coal reads coal
   CO2 as "oil" (measured: E C Gaston, plant 26, units 1-4 carry BIT as EIA-860
   Energy Source 2 and report hours at the coal signature — 28-50 % of the
   2022-2025 "oil" before this exclusion). A unit is coal-capable iff an EIA-860
   generator it maps to carries a coal code (:data:`COAL_ENERGY_SOURCES`) in
   ANY of ``Energy Source 1..6`` at the solve year's own vintage (operable and
   retired-and-canceled sheets). The unit -> generator map is the EPA CAMD-EIA
   Power Sector Data Crosswalk (``data/raw/reference/camd-eia-crosswalk``),
   generator match first and boiler match second (the unit's crosswalk
   ``EIA_BOILER_ID`` associated, via the vintage's boiler-generator association
   sheet, with a coal-capable generator). A unit with NO crosswalk row falls
   back to the boiler association only: it is excluded iff an EIA boiler with
   the SAME id at the same plant is associated with a coal-capable generator.
   No plant-wide exclusion is ever applied. No ratio threshold.
3. **Plant-day oil share** — the two-fuel mixing identity applied ONCE per
   plant-day to the aggregate ratio (coordinator ruling: removes the one-sided
   bias of clipping each hour's rounding noise):
   ``f_day = clip((sum co2Mass / sum heatInput - R_GAS) / (R_OIL - R_GAS), 0, 1)``
   over the plant's eligible unit-hours with positive heat input and a
   reported CO2 mass (:func:`market_sim.data.fuel.oil_heat_share_from_co2` on
   the sums), with the 40 CFR Part 75 App. G Eq. G-4 signatures CAMPD books
   ``co2Mass`` on (``constants.CAMPD_CO2_SHORT_TONS_PER_MMBTU_GAS`` / ``_OIL``).
   Days are CAMPD calendar dates (local standard time). Only plant-days with
   ``f_day > 0`` are written; an absent day reads as 0.

Output: :func:`market_sim.config.paths.measured_oil_burn_days_path` —
``data/raw/_processed-legacy/campd_measured_oil_burn_days_<ISO>.csv`` with
columns ``iso, year, plant_code, date, oil_heat_share`` plus the plant-day's
eligible ``heat_input_mmbtu`` and ``gross_load_mwh`` (provenance; the consumer
reads only the first five).

Governance: rule 13 [R-MEASURED] — this is a same-year measured CONDUCT record
with no forward edition, so the consumer is backcast-only (the scenarios
``_BACKCAST_ONLY_OVERLAY_FIELDS`` family); its forward substitute is the
``dual_fuel_switching`` price-parity switch. Rule 23 [R-FROZEN-DERIVE]:
re-derives only when the CAMPD extracts, the crosswalk, EIA-860 or the fleet
change, never because a residual moved. Rule 25 [R-ISO-SCOPE]: one file per ISO.

Usage::

    uv run python scripts/data/derive_measured_oil_burn_days.py --iso SOCO
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import CAMPD_CO2_SHORT_TONS_PER_MMBTU_OIL  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import (  # noqa: E402
    CAMPD_UNIT_LEVEL_DIR,
    REFERENCE_DIR,
    active_eia860_dir,
    measured_oil_burn_days_path,
    set_eia860_vintage,
)
from market_sim.data.campd import states_for_iso  # noqa: E402
from market_sim.data.fleet import _COAL_ENERGY_SOURCES, load_fleet_from_csv  # noqa: E402
from market_sim.data.fuel import oil_heat_share_from_co2  # noqa: E402

#: Model fuel types that burn natural gas (mirrors data.fuel._shared._GAS_FUEL_IDX).
GAS_FUEL_TYPES: frozenset[str] = frozenset({"gas_cc", "gas_ct", "gas_st", "gas_cc_ccs"})

#: CAMPD ``primaryFuelInfo`` tokens that take a gas-listing unit OUT of scope
#: (a third fuel the two-fuel gas/oil identity cannot represent).
NON_GAS_PRIMARY_TOKENS: tuple[str, ...] = ("Coal", "Wood")

#: EIA-860 coal energy-source codes: the fleet loader's coal set
#: (SUB/BIT/LIG/ANT/RC/WC) plus the two remaining coal-derived codes in the
#: EIA-860 Form Instructions' energy-source table, SC (coal-based synfuel) and
#: SGC (coal-derived synthesis gas).
COAL_ENERGY_SOURCES: frozenset[str] = frozenset(_COAL_ENERGY_SOURCES | {"SC", "SGC"})

#: EPA CAMD-EIA Power Sector Data Crosswalk (static identifier map).
CAMD_EIA_CROSSWALK_CSV: Path = (
    REFERENCE_DIR / "camd-eia-crosswalk" / "epa_eia_crosswalk.csv"
)

_ENERGY_SOURCE_COLUMNS = [f"Energy Source {i}" for i in range(1, 7)]
_GENERATOR_SHEETS = (
    "eia860_generator_operable.parquet",
    "eia860_generator_retired_and_canceled.parquet",
)
_BOILER_GENERATOR_SHEET = "eia860_enviro_assoc_boiler_generator.parquet"

_CAMPD_COLUMNS = [
    "facilityId",
    "unitId",
    "date",
    "hour",
    "grossLoad",
    "co2Mass",
    "heatInput",
    "primaryFuelInfo",
]

#: Rounding of the written share (display precision only; 1e-6 of heat input).
SHARE_DECIMALS: int = 6


def _norm_id(value: object) -> str:
    """Normalize an EIA/CAMD unit, boiler or generator id for matching."""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text.upper()


def gas_plant_codes(iso: str, year: int) -> set[int]:
    """Return the EIA plant codes carrying a gas generator in the ISO's fleet.

    Union of the solve year's own EIA-860 vintage fleet and the canonical fleet.
    """
    cfg = get_iso_config(iso)
    codes: set[int] = set()
    for vintage in (year, None):
        set_eia860_vintage(vintage)
        try:
            fleet = load_fleet_from_csv(iso, cfg, year=vintage)
        finally:
            set_eia860_vintage(None)
        codes |= {
            int(g.plant_code)
            for g in fleet
            if g.fuel_type in GAS_FUEL_TYPES and int(g.plant_code or 0)
        }
    return codes


def coal_capable_keys(year: int) -> tuple[set[tuple[int, str]], set[tuple[int, str]]]:
    """Return ``(coal-capable generators, their boilers)`` at the year's vintage.

    A generator is coal-capable iff any ``Energy Source 1..6`` carries a code
    in :data:`COAL_ENERGY_SOURCES`; read from the operable and
    retired-and-canceled sheets of the solve year's EIA-860 vintage (canonical
    release when the year has no vintage directory). Boilers are those the
    vintage's boiler-generator association links to a coal-capable generator.
    """
    set_eia860_vintage(year)
    try:
        eia_dir = active_eia860_dir()
    finally:
        set_eia860_vintage(None)
    gens: set[tuple[int, str]] = set()
    for name in _GENERATOR_SHEETS:
        path = eia_dir / name
        if not path.exists():
            continue
        d = pd.read_parquet(path)
        cols = [c for c in _ENERGY_SOURCE_COLUMNS if c in d.columns]
        codes = d[cols].astype(str).apply(lambda s: s.str.strip().str.upper())
        coal = codes.isin(COAL_ENERGY_SOURCES).any(axis=1)
        plant = pd.to_numeric(d["Plant Code"], errors="coerce")
        sel = coal & plant.notna()
        gens |= {
            (int(p), _norm_id(g))
            for p, g in zip(plant[sel], d.loc[sel, "Generator ID"], strict=True)
        }
    boilers: set[tuple[int, str]] = set()
    assoc_path = eia_dir / _BOILER_GENERATOR_SHEET
    if assoc_path.exists():
        a = pd.read_parquet(assoc_path)
        plant = pd.to_numeric(a["Plant Code"], errors="coerce")
        for p, b, g in zip(plant, a["Boiler ID"], a["Generator ID"], strict=True):
            if pd.notna(p) and (int(p), _norm_id(g)) in gens:
                boilers.add((int(p), _norm_id(b)))
    return gens, boilers


def coal_capable_units(
    units: pd.DataFrame,
    gens: set[tuple[int, str]],
    boilers: set[tuple[int, str]],
    crosswalk: pd.DataFrame,
) -> tuple[set[tuple[int, str]], dict[str, int]]:
    """Return the coal-capable CAMPD ``(facilityId, unitId)`` keys among *units*.

    Crosswalk generator match, then crosswalk boiler match; a unit with no
    crosswalk row uses the same-id boiler fallback (see module docstring).
    Also returns counts of how each exclusion was decided.
    """
    xw = crosswalk.groupby(["plant", "unit"])
    excluded: set[tuple[int, str]] = set()
    how = {"generator": 0, "boiler": 0, "fallback_boiler": 0, "no_crosswalk": 0}
    for plant, unit in (
        units[["facilityId", "unitId"]].drop_duplicates().itertuples(index=False)
    ):
        key = (int(plant), _norm_id(unit))
        if key in xw.groups:
            rows = xw.get_group(key)
            if any((int(p), g) in gens for p, g in zip(rows.eia_plant, rows.gen)):
                excluded.add(key)
                how["generator"] += 1
            elif any(
                (int(p), b) in boilers for p, b in zip(rows.eia_plant, rows.boiler)
            ):
                excluded.add(key)
                how["boiler"] += 1
        else:
            how["no_crosswalk"] += 1
            if key in boilers:
                excluded.add(key)
                how["fallback_boiler"] += 1
    return excluded, how


def load_crosswalk() -> pd.DataFrame:
    """Return the CAMD-EIA crosswalk as normalized (plant, unit) -> EIA ids."""
    x = pd.read_csv(CAMD_EIA_CROSSWALK_CSV, encoding="utf-8-sig", low_memory=False)
    x = x[x["CAMD_PLANT_ID"].notna() & x["CAMD_UNIT_ID"].notna()]
    eia_plant = pd.to_numeric(x["EIA_PLANT_ID"], errors="coerce").fillna(
        x["CAMD_PLANT_ID"]
    )
    return pd.DataFrame(
        {
            "plant": x["CAMD_PLANT_ID"].astype(int).to_numpy(),
            "unit": [_norm_id(u) for u in x["CAMD_UNIT_ID"]],
            "eia_plant": eia_plant.astype(int).to_numpy(),
            "gen": [_norm_id(g) if pd.notna(g) else "" for g in x["EIA_GENERATOR_ID"]],
            "boiler": [_norm_id(b) if pd.notna(b) else "" for b in x["EIA_BOILER_ID"]],
        }
    )


def read_gas_unit_hours(iso: str, year: int, plants: set[int]) -> pd.DataFrame:
    """Return the gas-listing CAMPD unit-hours at the ISO's gas plants."""
    frames = []
    for state in states_for_iso(iso):
        path = CAMPD_UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        d = pd.read_parquet(path, columns=_CAMPD_COLUMNS)
        d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
        frames.append(d[d["facilityId"].isin(plants)])
    if not frames:
        return pd.DataFrame(columns=_CAMPD_COLUMNS)
    d = pd.concat(frames, ignore_index=True)
    fuel = d["primaryFuelInfo"].fillna("")
    in_scope = fuel.str.contains("Natural Gas")
    for token in NON_GAS_PRIMARY_TOKENS:
        in_scope &= ~fuel.str.contains(token)
    return d[in_scope].copy()


def plant_day_shares(hours: pd.DataFrame) -> pd.DataFrame:
    """Aggregate eligible unit-hours to plant-day oil shares (identity on sums).

    Only unit-hours with positive heat input AND a reported CO2 mass enter
    either sum, so numerator and denominator cover the same hours.
    """
    co2 = pd.to_numeric(hours["co2Mass"], errors="coerce")
    hi = pd.to_numeric(hours["heatInput"], errors="coerce")
    ok = co2.notna() & hi.notna() & (hi > 0)
    h = hours[ok].copy()
    h["day"] = pd.to_datetime(h["date"]).dt.normalize()
    agg = h.groupby(["facilityId", "day"], as_index=False).agg(
        co2_short_tons=("co2Mass", "sum"),
        heat_input_mmbtu=("heatInput", "sum"),
        gross_load_mwh=("grossLoad", "sum"),
    )
    agg["oil_heat_share"] = oil_heat_share_from_co2(
        agg["co2_short_tons"].to_numpy(float), agg["heat_input_mmbtu"].to_numpy(float)
    )
    return agg[np.isfinite(agg["oil_heat_share"])]


def derive_year(
    iso: str, year: int, crosswalk: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    """Return (the written plant-day rows, a stats dict) for one ISO-year."""
    plants = gas_plant_codes(iso, year)
    hours = read_gas_unit_hours(iso, year, plants)
    if hours.empty:
        return pd.DataFrame(), {"year": year, "unit_hours": 0}
    gens, boilers = coal_capable_keys(year)
    excluded, how = coal_capable_units(hours, gens, boilers, crosswalk)
    unit_key = list(
        zip(hours["facilityId"].astype(int), hours["unitId"].map(_norm_id), strict=True)
    )
    coal_mask = np.fromiter((k in excluded for k in unit_key), bool, len(hours))
    hi_all = pd.to_numeric(hours["heatInput"], errors="coerce").clip(lower=0)
    ratio = hours["co2Mass"] / hours["heatInput"].where(hours["heatInput"] > 0)
    eligible = hours[~coal_mask]
    agg = plant_day_shares(eligible)
    agg["oil_heat_share"] = agg["oil_heat_share"].round(SHARE_DECIMALS)
    gl = agg["gross_load_mwh"].fillna(0.0)
    hi = agg["heat_input_mmbtu"]
    kept = agg[agg["oil_heat_share"] > 0].copy()
    oil_mmbtu = kept["oil_heat_share"] * kept["heat_input_mmbtu"]
    stats = {
        "year": year,
        "gas_plants_in_fleet": len(plants),
        "units_excluded_coal_capable": len(excluded),
        "exclusion_route": how,
        "excluded_units": sorted(f"{p}:{u}" for p, u in excluded),
        "hi_excluded_share": float(hi_all[coal_mask].sum() / hi_all.sum()),
        "plant_days_total": len(agg),
        "plant_days_f_gt_0": len(kept),
        "plants_f_gt_0": int(kept["facilityId"].nunique()),
        "plant_days_f_ge_0p01": int((agg["oil_heat_share"] >= 0.01).sum()),
        "plant_days_f_ge_0p5": int((agg["oil_heat_share"] >= 0.5).sum()),
        "mean_f_kept": float(kept["oil_heat_share"].mean()) if len(kept) else 0.0,
        "oil_mmbtu": float(oil_mmbtu.sum()),
        "oil_mmbtu_plant26": float(oil_mmbtu[kept["facilityId"] == 26].sum()),
        "hi_weighted_oil_share": float((agg["oil_heat_share"] * hi).sum() / hi.sum()),
        "mwh_weighted_oil_share": float((agg["oil_heat_share"] * gl).sum() / gl.sum()),
        "eligible_hi_above_oil_signature_share": float(
            hi_all[(~coal_mask) & (ratio > CAMPD_CO2_SHORT_TONS_PER_MMBTU_OIL)].sum()
            / hi_all[~coal_mask].sum()
        ),
    }
    kept["iso"] = iso
    kept["year"] = year
    kept["plant_code"] = kept["facilityId"].astype(int)
    kept["date"] = kept["day"].dt.strftime("%Y-%m-%d")
    kept["heat_input_mmbtu"] = kept["heat_input_mmbtu"].round(3)
    kept["gross_load_mwh"] = kept["gross_load_mwh"].round(3)
    out = kept[
        [
            "iso",
            "year",
            "plant_code",
            "date",
            "oil_heat_share",
            "heat_input_mmbtu",
            "gross_load_mwh",
        ]
    ].sort_values(["plant_code", "date"])
    return out, stats


def main() -> None:
    """Derive and write the measured plant-day oil-burn artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO name, e.g. SOCO")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(range(2019, 2026)),
        help="CAMPD years to derive (default 2019-2025)",
    )
    parser.add_argument("--out", default=None, help="Output CSV path override")
    args = parser.parse_args()
    iso = args.iso.upper()

    crosswalk = load_crosswalk()
    frames = []
    for year in args.years:
        rows, stats = derive_year(iso, year, crosswalk)
        print(stats, flush=True)
        if not rows.empty:
            frames.append(rows)
    if not frames:
        raise SystemExit(f"{iso}: no in-scope CAMPD gas-unit hours — nothing to write")
    out = pd.concat(frames, ignore_index=True)
    out_path = Path(args.out) if args.out else measured_oil_burn_days_path(iso)
    out.to_csv(out_path, index=False)
    print(f"wrote {len(out)} plant-day rows -> {out_path}")


if __name__ == "__main__":
    main()
