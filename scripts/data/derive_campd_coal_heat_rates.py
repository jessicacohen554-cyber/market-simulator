"""Derive measured per-plant OPERATING heat rates for the COAL class from CAMPD.

The coal sibling of :mod:`scripts.data.derive_campd_ct_heat_rates` (nyiso-88),
built on the identical identification and written to the identical schema. It is
the measured replacement for the eGRID **plant-average annual** heat rate the
non-ERCOT fleet loader otherwise gives every coal generator
(``market_sim.data.fleet.eia860._rows_to_generators``).

Why the eGRID figure is wrong for a coal steam unit
---------------------------------------------------
eGRID's plant rate is ``PLHTIAN / PLNGENAN`` — annual heat input over annual
*net* generation — so it blends **startup fuel and shutdown tails**, and the
**offline hours' unit-heater / bank fuel**, into the number that sets the
plant's offer. It is also a *level* that moves with the plant's capacity factor
in the vintage year: a low-CF vintage inflates the published rate, the model
then prices the plant out of merit, and its modelled CF falls further. The rate
that sets an offer is the rate at which the machine burns fuel **while it is
running**.

Measured on NWPP's own fleet (lane NWPP-42), the assigned rate is above the
plant's own metered operating rate at **every one of the 12 CEMS-covered coal
plants**, by a capacity-weighted 7 % on a net basis — and the overstatement is
largest exactly where it is not smallest: Hunter +30.7 %, North Valmy +24.1 %,
Hardin +19.0 %, Wyodak +17.0 % on a gross basis, against Colstrip +10.0 % and
Jim Bridger +9.1 %. The error is a per-plant source defect, not a uniform bias,
which is why no single multiplier can stand in for the measurement.

Method — per unit, over the pooled window::

    steady    = hours with opTime >= _MIN_OPTIME and grossLoad > 0, heatInput > 0
    valid     = steady hours whose OWN heatInput/grossLoad is inside
                [_HR_MIN_GROSS, _HR_MAX_GROSS]          (>= _MIN_STEADY_HOURS)
    hr_gross  = sum(heatInput) / sum(grossLoad) over ``valid``
    hr_net    = hr_gross / parasitic_factor(plant)

and the plant value is the generation-weighted mean of its units' ``hr_net``.

**Why the screen is an operating-hour screen and not the CT deriver's
``>= 0.8 x p95`` loaded window.** A simple-cycle peaker either runs at full
output or does not run, so for it "at load" and "operating" are the same
window and the part-load hours it excludes are startup / shutdown transients.
A coal steam unit's *normal* operating range is part load — it is committed and
then cycles between min-load and HSL, which is precisely the behaviour the
model must reproduce — so a near-HSL window would price the plant at its best
point and understate the rate at which it actually burns fuel across the range
the model dispatches it over. ``opTime >= _MIN_OPTIME`` removes exactly the
partial clock hours that carry startup and shutdown fuel, which is the defect
named above, and removes nothing else. Both windows are REPORTED
(``heat_rate_gross`` and ``heat_rate_gross_hsl``) so a reader sees the range;
the APPLIED column is the operating-hour one, fixed here on the physical
argument above, before any solve, and never swept (rules 1 ``[R-STRUCT]`` /
23 ``[R-FROZEN-DERIVE]``).

**Why the technology tag is ``primaryFuelInfo`` and not ``unitType``.** The CT
deriver separates a mixed facility's turbines from its boilers by CAMPD's
``unitType``. That tag cannot do the job here: at Jim Bridger, Naughton and
North Valmy the coal units *and* the gas-converted units are both boilers, so
``unitType`` maps all of them to one family. CAMPD's own ``primaryFuelInfo``
does separate them, and it is the tag that matches what this artifact prices —
the fuel the machine actually burns. A unit whose primary fuel is not a coal
is excluded, so a converted unit contributes to neither the coal rate nor the
coal capacity.

**The net-basis conversion is not optional.** CAMPD meters GROSS load while
eGRID (and therefore the model's heat rate, the LP's dispatched MW, and the
benchmark's "actual", built as ``gross x parasitic_factor`` by
``run_calibration_full._campd_hourly_frame``) are all on a NET basis. Comparing
a gross-basis measured rate against a net-basis model rate would overstate the
correction by the whole station-service fraction — for coal ~7 %, which is most
of the correction this artifact makes. The factor read here is the SAME
committed artifact the benchmark uses (``parasitic_load_factors.parquet``,
:func:`market_sim.data.campd.pooled_factor_map`), falling back to the committed
class default, so the derived heat rate and the actual it will be scored
against share one gross-to-net convention.

Output: ``data/raw/_processed-legacy/campd_coal_heat_rates_{ISO}.csv``, one row
per plant, consumed by
:func:`market_sim.data.fleet.campd_bins.measured_coal_heat_rates` under
``ScenarioConfig.measured_coal_heat_rates``.

Governance (CLAUDE.md rules 13 ``[R-MEASURED]`` / 14 ``[R-ACCURATE]`` /
21 ``[R-DOF]`` / 23 ``[R-FROZEN-DERIVE]`` / 25 ``[R-ISO-SCOPE]``): a unit's
operating heat rate is a physical characteristic of the machine, in the same
admissibility class as the CAMPD min-stable loads, the CT loaded heat rates and
the CT run horizons. It regenerates for a forward year from the same pipeline
and responds to changed conditions (a retrofit moves it; a converted unit drops
out of the coal population), so it is rule-13 admissible as an INPUT — it is
not a measured outcome fed back to close a residual, and nothing in it is
fitted to one. ZERO free parameters: every applied number is
``sum(heatInput)/sum(grossLoad)`` over the plant's own hours. Per rule 23 it
re-derives ONLY when CAMPD publishes new or revised vintages, and the
re-derivation commit must cite that data change. Per rule 25 each ISO's lane
derives its own artifact from its own market's plants.

Usage::

    python scripts/data/derive_campd_coal_heat_rates.py --iso NWPP
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from scripts.lib.heat_rate_years import (  # noqa: E402
    BACKCAST_YEARS,
    backcast_fleets,
    class_capacity,
    class_heat_rates,
    per_year_tables,
    stack_year_tables,
    union_fleet,
)

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

#: The model class this artifact prices. Only COAL: a gas-converted boiler at a
#: coal site classes ST_GAS in the model fleet and is priced by the gas path.
TARGET_CLASS = "COAL"

#: CAMPD ``primaryFuelInfo`` substrings counted as coal. Matched case-folded on
#: containment so every published rank string ("Coal", "Bituminous Coal",
#: "Subbituminous", "Coal Refuse", "Lignite", ...) is caught without
#: enumerating CAMPD's full vocabulary, while "Pipeline Natural Gas" and the
#: oil strings are not.
COAL_FUEL_TOKENS: tuple[str, ...] = (
    "coal",
    "bituminous",
    "lignite",
    "anthracite",
    "petroleum coke",
)

#: Steady-state screen: a full clock hour at load. Below this the hour is a
#: partial operating hour — a start, a trip or a shutdown tail — and its fuel
#: is exactly what the eGRID annual average wrongly folds into the offer.
_MIN_OPTIME: float = 0.99

#: Minimum qualifying hours before a unit's operating rate is trusted. A coal
#: unit that cleared fewer than this across three pooled vintages has no
#: measured rate and falls back to the loader's existing eGRID behaviour.
_MIN_STEADY_HOURS: int = 200

#: Physical plausibility band (MMBtu per GROSS MWh) for a coal steam unit. A
#: DATA-INTEGRITY guard on the meter, not a tuning knob: below 8.0 the row
#: implies > 42 % HHV efficiency, which no subcritical coal boiler reaches, and
#: above 25.0 it is a broken heat-input or gross-load channel. Applied at BOTH
#: grains — per steady HOUR inside :func:`unit_operating_heat_rates` (the
#: caiso-156 rule-14 lesson: an out-of-band hour cannot inform the rate, and
#: screening only the aggregate lets impossible hours dilute the sums while the
#: plant still flags ``ok``) and to the resulting PLANT aggregate on a NET
#: basis, whose out-of-band rows are written with a ``flag`` and excluded from
#: the applied map.
_HR_MIN_GROSS: float = 8.0
_HR_MAX_GROSS: float = 25.0
_HR_MIN_NET: float = 8.0
_HR_MAX_NET: float = 27.0

#: Reported-only comparison window: the near-HSL rate, for the reader's sense
#: of the plant's range. NEVER the applied column (see the module docstring).
_HSL_PCTILE: float = 90.0


def parasitic_factors() -> dict[int, float]:
    """Return the committed ``{plant_id: net/gross}`` map, or ``{}`` if absent.

    The SAME artifact ``run_calibration_full._parasitic_factor_map`` reads to
    build the benchmark's per-plant net actual, so a heat rate derived with it
    is on the identical basis as the generation it will be scored against.
    """
    path = PROCESSED_DIR / "parasitic_load_factors.parquet"
    if not path.exists():
        return {}
    return campd.pooled_factor_map(pd.read_parquet(path))


def _is_coal_fuel(series: pd.Series) -> pd.Series:
    """Boolean mask of rows whose CAMPD ``primaryFuelInfo`` is a coal."""
    s = series.astype(str).str.casefold()
    mask = pd.Series(False, index=s.index)
    for token in COAL_FUEL_TOKENS:
        mask |= s.str.contains(token, regex=False)
    return mask


def unit_operating_heat_rates(
    iso: str, years: list[int], codes: set[int]
) -> pd.DataFrame:
    """Return one row per CAMPD coal-fired unit with its operating heat rate.

    Each state-year extract is read once and immediately narrowed to the ISO's
    own target-class plants, so a shared state file cannot leak another ISO's
    units in. Hours are pooled across years before the screens, so a unit that
    barely ran in one year still reaches :data:`_MIN_STEADY_HOURS`.

    Args:
        iso: ISO identifier.
        years: CAMPD vintages to pool.
        codes: Plant codes to keep (the target class across the backcast
            fleet union, :func:`scripts.lib.heat_rate_years.union_fleet`).

    Returns:
        Columns ``plant_code``, ``plant_name``, ``unit_id``, ``gross_mwh``,
        ``steady_hours``, ``cap_mw``, ``hr_gross``, ``hr_gross_hsl``.
    """
    frames: list[pd.DataFrame] = []
    for state in campd.states_for_iso(iso):
        for year in years:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                print(f"  (skip {path.name}: not on disk)")
                continue
            df = pd.read_parquet(
                path,
                columns=[
                    "facilityId",
                    "facilityName",
                    "unitId",
                    "opTime",
                    "grossLoad",
                    "heatInput",
                    "primaryFuelInfo",
                ],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            df = df[_is_coal_fuel(df["primaryFuelInfo"])]
            if not df.empty:
                frames.append(df)
    if not frames:
        raise SystemExit(f"{iso}: no CAMPD coal-fuel hours for {TARGET_CLASS}")

    pooled = pd.concat(frames, ignore_index=True).dropna(
        subset=["grossLoad", "heatInput"]
    )
    pooled = pooled[(pooled["grossLoad"] > 0.0) & (pooled["heatInput"] > 0.0)]

    rows: list[dict] = []
    for (code, unit), g in pooled.groupby(["facilityId", "unitId"], sort=True):
        steady = g[g["opTime"].astype(float) >= _MIN_OPTIME]
        if steady.empty:
            continue
        hourly_hr = steady["heatInput"] / steady["grossLoad"]
        steady = steady[(hourly_hr >= _HR_MIN_GROSS) & (hourly_hr <= _HR_MAX_GROSS)]
        if len(steady) < _MIN_STEADY_HOURS:
            continue
        hsl_thresh = float(np.percentile(steady["grossLoad"], _HSL_PCTILE))
        hsl = steady[steady["grossLoad"] >= hsl_thresh]
        rows.append(
            {
                "plant_code": int(code),
                "plant_name": str(g["facilityName"].iloc[0]),
                "unit_id": str(unit),
                # All-hours generation weight, deliberately NOT screened: it
                # weights units within a plant, it does not price them.
                "gross_mwh": float(g["grossLoad"].sum()),
                # In-band steady count -- the hours actually backing hr_gross.
                "steady_hours": int(len(steady)),
                "cap_mw": float(np.percentile(g["grossLoad"], 95.0)),
                "hr_gross": float(
                    steady["heatInput"].sum() / steady["grossLoad"].sum()
                ),
                # REPORTED ONLY (module docstring): the near-HSL rate.
                "hr_gross_hsl": (
                    float(hsl["heatInput"].sum() / hsl["grossLoad"].sum())
                    if len(hsl)
                    else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows)


def plant_table(
    units: pd.DataFrame,
    iso: str,
    years: list[int],
    caps: dict[int, float],
    model_hr: dict[int, float],
    factors: dict[int, float],
) -> pd.DataFrame:
    """Aggregate the per-unit operating rates to one measured row per plant.

    The plant value is GENERATION-weighted across its units: a unit that
    produced most of the plant's energy should dominate the rate the plant
    offers at. Weighting by capacity instead would let a rarely-run spare
    define the offer of a plant that runs on its other machines.

    The gross-to-net conversion is applied per unit before aggregation, using
    the unit's own plant factor (units of one plant share it), so the column
    ``heat_rate`` is directly comparable to ``model_heat_rate_egrid``.
    """
    default_factor = 1.0 - campd.DEFAULT_PARASITIC_LOAD_PCT[TARGET_CLASS]
    units = units.copy()
    units["parasitic_factor"] = (
        units["plant_code"].map(factors).fillna(default_factor).astype(float)
    )
    units["hr_net"] = units["hr_gross"] / units["parasitic_factor"]

    rows: list[dict] = []
    for code, g in units.groupby("plant_code", sort=True):
        weight = float(g["gross_mwh"].sum())
        if weight <= 0.0:
            continue
        hr_net = float((g["gross_mwh"] * g["hr_net"]).sum() / weight)
        hr_gross = float((g["gross_mwh"] * g["hr_gross"]).sum() / weight)
        hsl = g["hr_gross_hsl"].to_numpy(dtype=float)
        w = g["gross_mwh"].to_numpy(dtype=float)
        finite = np.isfinite(hsl)
        hr_hsl = (
            float(np.average(hsl[finite], weights=w[finite]))
            if finite.any() and w[finite].sum() > 0
            else float("nan")
        )
        model = model_hr.get(int(code))
        if hr_net < _HR_MIN_NET:
            flag = "below_physical_band"
        elif hr_net > _HR_MAX_NET:
            flag = "above_physical_band"
        else:
            flag = "ok"
        rows.append(
            {
                "plant_code": int(code),
                "plant_name": str(g["plant_name"].iloc[0]),
                "n_units": int(len(g)),
                "class_capacity_mw": round(float(caps.get(int(code), 0.0)), 3),
                "gross_mwh": round(weight, 1),
                "steady_hours": int(g["steady_hours"].sum()),
                "parasitic_factor": round(float(g["parasitic_factor"].iloc[0]), 6),
                "heat_rate_gross": round(hr_gross, 4),
                # REPORTED ONLY -- never applied (see the module docstring).
                "heat_rate_gross_hsl": round(hr_hsl, 4),
                # The applied column: MMBtu per NET MWh, the basis the model's
                # heat rate and the benchmark's actual generation both use.
                "heat_rate": round(hr_net, 4),
                "model_heat_rate_egrid": (
                    round(float(model), 4) if model is not None else float("nan")
                ),
                "model_over_measured": (
                    round(float(model) / hr_net, 4)
                    if model is not None and hr_net > 0.0
                    else float("nan")
                ),
                "flag": flag,
            }
        )
    out = pd.DataFrame(rows).sort_values("class_capacity_mw", ascending=False)
    out["iso"] = iso
    out["years"] = "-".join(str(y) for y in years)
    out["source"] = (
        "EPA CAMPD unit-level hourly opTime + grossLoad + heatInput "
        "(data/raw/campd-unit-level), primaryFuelInfo matching "
        f"{list(COAL_FUEL_TOKENS)}; per unit heat_rate = "
        f"sum(heatInput)/sum(grossLoad) over hours with opTime >= {_MIN_OPTIME} "
        f"whose OWN implied rate is inside the physical band "
        f"[{_HR_MIN_GROSS}, {_HR_MAX_GROSS}] MMBtu per gross MWh "
        f"(>= {_MIN_STEADY_HOURS} such qualifying hours), converted to a NET "
        "basis by the committed parasitic factor "
        "(parasitic_load_factors.parquet, the same map the benchmark's net "
        f"actual uses; class default "
        f"{campd.DEFAULT_PARASITIC_LOAD_PCT[TARGET_CLASS]}); plant value is the "
        "generation-weighted mean across its units. heat_rate_gross_hsl is "
        f"REPORTED ONLY (the >= p{_HSL_PCTILE} near-HSL window) and is never "
        f"applied. The net band [{_HR_MIN_NET}, {_HR_MAX_NET}] also flags the "
        "plant aggregate; only flag=='ok' rows are applied."
    )
    return out


def main(argv: list[str] | None = None) -> int:
    """Derive and write the measured coal operating-heat-rate artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO name, e.g. NWPP")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(BACKCAST_YEARS),
        help="CAMPD vintages to pool and slice (default 2019-2025)",
    )
    parser.add_argument("--out", default=None, help="Output CSV path override")
    parser.add_argument(
        "--detail",
        action="store_true",
        help="ALSO write the per-unit table alongside the plant summary",
    )
    parser.add_argument(
        "--egrid-family-heat-rates",
        action="store_true",
        help=(
            "Load the PROVENANCE fleet with ScenarioConfig."
            "egrid_family_heat_rates armed. PROVENANCE ONLY: it moves "
            "model_heat_rate_egrid and nothing that is applied"
        ),
    )
    parser.add_argument(
        "--measured-ct-heat-rates",
        action="store_true",
        help=(
            "Load the PROVENANCE fleet with ScenarioConfig."
            "measured_ct_heat_rates armed. PROVENANCE ONLY (and it cannot "
            "reach a COAL row at all)"
        ),
    )
    parser.add_argument(
        "--measured-st-heat-rates",
        action="store_true",
        help=(
            "Load the PROVENANCE fleet with ScenarioConfig."
            "measured_st_heat_rates armed. PROVENANCE ONLY (and it cannot "
            "reach a COAL row at all)"
        ),
    )
    args = parser.parse_args(argv)
    iso = args.iso.upper()

    years = sorted(args.years)
    # F1 D4: the target population is the UNION of the backcast fleets over
    # every year (year-matched vintage + retiree channel), so a coal plant that
    # retired before 2023 is covered; the provenance recipe is loaded per year.
    recipe_flags = {
        "egrid_family_heat_rates": args.egrid_family_heat_rates,
        "measured_ct_heat_rates": args.measured_ct_heat_rates,
        "measured_st_heat_rates": args.measured_st_heat_rates,
    }
    fleets = backcast_fleets(iso, years, **recipe_flags)
    union = union_fleet(fleets)
    caps = class_capacity(union, TARGET_CLASS)
    if not caps:
        raise SystemExit(f"{iso}: model fleet has no {TARGET_CLASS} plants")
    # The provenance recipe must not move the POPULATION — only the reported
    # rate. Asserted rather than assumed: a silent membership change would move
    # an APPLIED number (the gas-steam sibling's guard, soco-53e section 1.3).
    if any(recipe_flags.values()):
        plain_caps = class_capacity(
            union_fleet(backcast_fleets(iso, years)), TARGET_CLASS
        )
        if plain_caps != caps:
            raise SystemExit(f"{iso}: the provenance recipe moved the plant population")
    factors = parasitic_factors()
    units = unit_operating_heat_rates(iso, years, set(caps))
    if units.empty:
        raise SystemExit(f"{iso}: no unit cleared the steady-state screen")
    pooled = plant_table(
        units, iso, years, caps, class_heat_rates(union, TARGET_CLASS), factors
    )

    def _year_table(year: int) -> pd.DataFrame | None:
        # The SAME estimator on year Y's hours alone: a per-year row exists
        # only where the unchanged _MIN_STEADY_HOURS gate clears on them.
        year_units = unit_operating_heat_rates(iso, [year], set(caps))
        if year_units.empty:
            return None
        return plant_table(
            year_units,
            iso,
            [year],
            caps,
            class_heat_rates(fleets.get(year, []), TARGET_CLASS),
            factors,
        )

    table = stack_year_tables(pooled, per_year_tables(years, _year_table))
    # Record WHICH fleet recipe the provenance columns were read under, so a
    # later reader can tell what "model_heat_rate_egrid" means without guessing.
    recipe = [
        name
        for name, on in (
            ("egrid_family_heat_rates", args.egrid_family_heat_rates),
            ("measured_ct_heat_rates", args.measured_ct_heat_rates),
            ("measured_st_heat_rates", args.measured_st_heat_rates),
        )
        if on
    ]
    table["model_recipe"] = "+".join(recipe) if recipe else "loader_defaults"

    out_path = (
        Path(args.out)
        if args.out
        else (PROCESSED_DIR / f"campd_coal_heat_rates_{iso}.csv")
    )
    table.to_csv(out_path, index=False)
    print(f"wrote {out_path} ({len(table)} plant rows)")
    print(
        "  per-year rows: "
        + ", ".join(
            f"{y}:{int((table['year'] == y).sum())}" for y in sorted(set(table["year"]))
        )
    )
    table = table[table["year"] == 0]

    ok = table[table["flag"] == "ok"]
    covered = float(ok["class_capacity_mw"].sum())
    total = float(sum(caps.values()))
    print(
        f"  coverage: {len(ok)}/{len(caps)} plants, "
        f"{covered:.0f}/{total:.0f} MW ({100.0 * covered / total:.1f} % of "
        f"{iso} {TARGET_CLASS} capacity)"
    )
    if (table["flag"] != "ok").any():
        print("  FLAGGED (not applied):")
        print(
            table[table["flag"] != "ok"][
                ["plant_code", "plant_name", "heat_rate", "flag"]
            ].to_string(index=False)
        )
    w_cap = ok["class_capacity_mw"].to_numpy(dtype=float)
    w_gen = ok["gross_mwh"].to_numpy(dtype=float)
    meas = ok["heat_rate"].to_numpy(dtype=float)
    model = ok["model_heat_rate_egrid"].to_numpy(dtype=float)
    finite = np.isfinite(model)
    if finite.any() and w_cap[finite].sum() > 0:
        print(
            "  capacity-weighted   model %.3f -> measured %.3f (%+.1f %%)"
            % (
                np.average(model[finite], weights=w_cap[finite]),
                np.average(meas[finite], weights=w_cap[finite]),
                100.0
                * (
                    np.average(meas[finite], weights=w_cap[finite])
                    / np.average(model[finite], weights=w_cap[finite])
                    - 1.0
                ),
            )
        )
        print(
            "  generation-weighted model %.3f -> measured %.3f (%+.1f %%)"
            % (
                np.average(model[finite], weights=w_gen[finite]),
                np.average(meas[finite], weights=w_gen[finite]),
                100.0
                * (
                    np.average(meas[finite], weights=w_gen[finite])
                    / np.average(model[finite], weights=w_gen[finite])
                    - 1.0
                ),
            )
        )
    print(
        table[
            [
                "plant_code",
                "plant_name",
                "class_capacity_mw",
                "n_units",
                "steady_hours",
                "parasitic_factor",
                "heat_rate_gross",
                "heat_rate_gross_hsl",
                "heat_rate",
                "model_heat_rate_egrid",
                "model_over_measured",
                "flag",
            ]
        ].to_string(index=False)
    )
    if args.detail:
        detail_path = out_path.with_name(out_path.stem + "_units.csv")
        units.sort_values(["plant_code", "unit_id"]).to_csv(detail_path, index=False)
        print(f"wrote {detail_path} ({len(units)} unit rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
