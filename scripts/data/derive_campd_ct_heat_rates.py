"""Derive measured per-plant LOADED heat rates for the CT_PEAKER class from CAMPD.

The measured replacement for the eGRID **plant-average annual** heat rate the
non-ERCOT fleet loader currently gives every combustion turbine
(``market_sim.data.fleet.eia860._rows_to_generators``). Two things are wrong
with the eGRID figure for a peaker, and this artifact fixes both:

1. **It is an annual average, not a loaded rate.** A peaker's annual average
   blends startup fuel, part-load hours and shutdown tails into the number that
   sets its offer. The rate that sets an offer is the rate at load.
2. **At a mixed facility it is not even the right technology's rate.** eGRID
   publishes one heat rate per PLANT, so E F Barrett's 1970-vintage FT4 gas
   turbines and its 188 MW steam boilers share a single 11.08 MMBtu/MWh figure.
   Measured separately, the turbines run 16.69 and the model undercharges them;
   at Bayswater the model charges 21.68 against a measured 10.74 and
   overcharges by 2x. The error is source NOISE in both directions, not a
   uniform bias, which is why no single multiplier can stand in for it.

Method — per unit, over the pooled window:

    cap       = p95 of that unit's gross load
    loaded    = hours with grossLoad >= _LOADED_FRAC x cap
    valid     = loaded hours whose OWN heatInput/grossLoad is inside
                [_HR_MIN, _HR_MAX]                     (>= _MIN_LOADED_HOURS)
    hr_gross  = sum(heatInput) / sum(grossLoad) over ``valid``
    hr_net    = hr_gross / parasitic_factor(plant)

The hour-grain band screen (caiso-156) is what makes ``valid`` narrower than
``loaded``. The physical band is a meter guard, so it is applied per hour and
not only to the plant aggregate: an hour whose implied rate is physically
impossible for a simple cycle is a broken heat-input channel, and before the
screen such hours silently diluted the sums while the plant still flagged
``ok``. It introduces no new parameter.

and the plant value is the generation-weighted mean of its units' ``hr_net``.

**The net-basis conversion is not optional.** CAMPD meters GROSS load while
eGRID (and therefore the model's heat rate, and the LP's dispatched MW, and the
benchmark's "actual" — built as ``gross x parasitic_factor`` by
``run_calibration_full._campd_hourly_frame``) are all on a NET basis. Comparing
a gross-basis measured rate against a net-basis model rate overstates the
correction by the station-service fraction, which is 1 % for a bare CT but
10.2 % at Bayonne — the largest plant in the NYISO class. The factor read here
is the SAME committed artifact the benchmark uses
(``parasitic_load_factors.parquet``, :func:`market_sim.data.campd.pooled_factor_map`),
so the derived heat rate and the actual it will be scored against share one
gross-to-net convention.

Unit-level attribution is what makes the mixed-facility case tractable: CAMPD's
own ``unitType`` says which units are combustion turbines, so a plant whose
model fleet spans CT_PEAKER and ST_GAS contributes only its turbines here
instead of being dropped as unattributable (the choice
``derive_campd_gas_commitment_params.py`` must make, because *its* statistic has
no equivalent technology tag).

Scope: plants carrying at least one ``CT_PEAKER`` generator in the ISO's own
model fleet, over :func:`market_sim.data.campd.states_for_iso` — for NYISO that
includes NJ, where Bayonne Energy Center sits physically while delivering into
Zone J over a dedicated tie (41 % of the class's measured energy; dropping it
would gut the artifact).

Output: ``data/raw/_processed-legacy/campd_ct_heat_rates_{ISO}.csv``, one row
per plant, consumed by
:func:`market_sim.data.fleet.campd_bins.measured_ct_heat_rates` under
``ScenarioConfig.measured_ct_heat_rates``.

Governance (CLAUDE.md rules 13 [R-MEASURED] / 14 [R-ACCURATE] / 24
[R-FROZEN-DERIVE]): a unit's loaded heat rate is a physical characteristic of
the machine, in the same admissibility class as the CAMPD min-stable loads and
CT run horizons. It regenerates for a forward year from the same pipeline and
responds to changed conditions (a retrofit moves it; a new unit carries its
design rate), so it is rule-13 admissible as an INPUT — it is not a measured
outcome fed back to close a residual, and nothing in it is fitted to one. Per
rule 24 it re-derives ONLY when CAMPD publishes new or revised vintages, and
the re-derivation commit must cite that data change.

Usage::

    python scripts/data/derive_campd_ct_heat_rates.py --iso NYISO
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

#: The model class this artifact prices. CT_CHP is deliberately excluded: a
#: cogen turbine's metered heat input serves process steam as well as power, so
#: its "heat rate" is not the electric rate that sets an offer.
TARGET_CLASS = "CT_PEAKER"

#: CAMPD ``unitType`` values counted as simple-cycle combustion turbines. The
#: technology tag is what lets a mixed steam/CT facility contribute only its
#: turbines rather than being dropped as unattributable.
CT_UNIT_TYPE = "Combustion turbine"

#: Loaded-window threshold as a fraction of the unit's own p95 gross load. p95
#: rather than the raw max so one over-range meter sample cannot define "full
#: output"; 0.8 of it is the near-full-output band whose heat rate sets the
#: offer, excluding start, part-load and shutdown fuel.
_LOADED_FRAC: float = 0.80
_CAP_PCTILE: float = 95.0

#: Minimum qualifying hours before a unit's loaded rate is trusted. A peaker
#: that never reached its own loaded band in three years has no measured rate.
_MIN_LOADED_HOURS: int = 50

#: Physical plausibility band (MMBtu/MWh, HHV, net) for a simple-cycle gas
#: turbine. This is a DATA-INTEGRITY guard on the meter, not a tuning knob:
#: below ~6.0 the row is a mis-tagged combined cycle, above ~25.0 it is a
#: broken heat-input or gross-load channel. Applied at BOTH grains: per loaded
#: HOUR inside :func:`unit_loaded_heat_rates` (an out-of-band hour cannot inform
#: the rate, caiso-156) and to the resulting PLANT aggregate, whose rows outside
#: the band are written with their measured value and a ``flag`` and excluded
#: from the applied map (the loader reads ``flag == "ok"``). Screening only the
#: aggregate was the caiso-146 §2.4 meter defect: impossible hours diluted the
#: sums while the plant still flagged ok. Bounds bracket the published
#: simple-cycle range with margin: an aeroderivative LM6000 sits near 9,
#: 1960s-70s FT4 peaking twin-pacs near 16-17.
_HR_MIN: float = 6.0
_HR_MAX: float = 25.0


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


def unit_loaded_heat_rates(iso: str, years: list[int], codes: set[int]) -> pd.DataFrame:
    """Return one row per CAMPD combustion-turbine unit with its loaded rate.

    Each state-year extract is read once and immediately narrowed to the ISO's
    own target-class plants, so a shared state file (NJ feeds both NYISO and
    PJM) cannot leak another ISO's units in. Hours are pooled across years
    before the percentile, so a unit that barely ran in one year still reaches
    :data:`_MIN_LOADED_HOURS`.

    Args:
        iso: ISO identifier.
        years: CAMPD vintages to pool.
        codes: Plant codes to keep (the target class's plants across the
            backcast fleet union, :func:`scripts.lib.heat_rate_years.union_fleet`).

    Returns:
        Columns ``plant_code``, ``plant_name``, ``unit_id``, ``gross_mwh``,
        ``loaded_hours``, ``cap_mw``, ``hr_gross``.
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
                    "unitType",
                    "grossLoad",
                    "heatInput",
                ],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            df = df[
                df["unitType"].astype(str).str.strip().str.casefold()
                == CT_UNIT_TYPE.casefold()
            ]
            if not df.empty:
                frames.append(df)
    if not frames:
        raise SystemExit(f"{iso}: no CAMPD {CT_UNIT_TYPE} hours for {TARGET_CLASS}")

    pooled = pd.concat(frames, ignore_index=True).dropna(
        subset=["grossLoad", "heatInput"]
    )
    pooled = pooled[(pooled["grossLoad"] > 0.0) & (pooled["heatInput"] > 0.0)]

    rows: list[dict] = []
    for (code, unit), g in pooled.groupby(["facilityId", "unitId"], sort=True):
        cap = float(np.percentile(g["grossLoad"], _CAP_PCTILE))
        loaded = g[g["grossLoad"] >= _LOADED_FRAC * cap]
        # caiso-156 rule 14 [R-ACCURATE]: apply the physical band at the grain
        # the meter defect lives at -- the HOUR. The band below is a
        # data-integrity guard on the meter, so a loaded hour whose own implied
        # rate falls outside it is a broken heat-input channel by this module's
        # own declaration and cannot inform the rate. Screening only the plant
        # aggregate (below) let such hours dilute sum(heatInput)/sum(grossLoad)
        # while the plant still flagged "ok": Delano Energy Center (58122) has
        # loaded-hour rates at p05 = 0.81 and p25 = 3.20 against a 7.89 median
        # -- physically impossible for a simple cycle (> 56 % HHV efficiency)
        # -- dragging the plant to 6.5725, under every real machine yet over
        # the 6.0 plant floor. Measured bias across the six committed
        # artifacts: CAISO +0.176, NYISO +0.359, NEISO +0.171, PJM +0.069
        # cap-weighted (PROBE-caiso156-band-screen-2026-08-02.txt). ZERO new
        # parameters -- the same _HR_MIN/_HR_MAX the aggregate already uses.
        hourly_hr = loaded["heatInput"] / loaded["grossLoad"]
        loaded = loaded[(hourly_hr >= _HR_MIN) & (hourly_hr <= _HR_MAX)]
        # The trust gate is evaluated on the IN-BAND hours: a unit whose meter
        # is so defective that fewer than _MIN_LOADED_HOURS trustworthy loaded
        # hours remain has no measured rate and drops, exactly as a unit that
        # never reached its loaded window drops. Its plant falls back to eGRID
        # (the loader's existing behaviour for an absent row).
        if len(loaded) < _MIN_LOADED_HOURS:
            continue
        rows.append(
            {
                "plant_code": int(code),
                "plant_name": str(g["facilityName"].iloc[0]),
                "unit_id": str(unit),
                # All-hours generation weight, deliberately NOT screened: it
                # weights units within a plant, it does not price them.
                "gross_mwh": float(g["grossLoad"].sum()),
                # In-band count -- the hours actually backing hr_gross.
                "loaded_hours": int(len(loaded)),
                "cap_mw": cap,
                "hr_gross": float(
                    loaded["heatInput"].sum() / loaded["grossLoad"].sum()
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
    """Aggregate the per-unit loaded rates to one measured row per plant.

    The plant value is GENERATION-weighted across its turbines: a unit that
    produced most of the plant's energy should dominate the rate the plant
    offers at. Weighting by capacity instead would let a rarely-run spare
    define the offer of a plant that runs on its other machines.

    The gross-to-net conversion is applied per unit before aggregation, using
    the unit's own plant factor (units of one plant share it), so the column
    ``hr_net`` is directly comparable to ``model_hr``.
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
        model = model_hr.get(int(code))
        if hr_net < _HR_MIN:
            flag = "below_physical_band"
        elif hr_net > _HR_MAX:
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
                "loaded_hours": int(g["loaded_hours"].sum()),
                "parasitic_factor": round(float(g["parasitic_factor"].iloc[0]), 6),
                "heat_rate_gross": round(hr_gross, 4),
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
        "EPA CAMPD unit-level hourly grossLoad + heatInput "
        f"(data/raw/campd-unit-level), unitType == '{CT_UNIT_TYPE}'; per unit "
        f"heat_rate = sum(heatInput)/sum(grossLoad) over hours >= {_LOADED_FRAC} "
        f"x p{_CAP_PCTILE} of that unit's gross load whose OWN implied rate is "
        f"inside the physical band [{_HR_MIN}, {_HR_MAX}] MMBtu/MWh "
        f"(>= {_MIN_LOADED_HOURS} such qualifying hours), converted to a NET basis by the committed "
        "parasitic factor (parasitic_load_factors.parquet, the same map the "
        "benchmark's net actual uses; class default "
        f"{campd.DEFAULT_PARASITIC_LOAD_PCT[TARGET_CLASS]}); plant value is the "
        f"generation-weighted mean across its turbines. The same physical band "
        "also flags the plant aggregate; only flag=='ok' rows are applied."
    )
    return out


def main(argv: list[str] | None = None) -> int:
    """Derive and write the measured CT loaded-heat-rate artifact.

    F1 D4 (docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md
    §5.1 item 3): the target population is the UNION of the ISO's backcast
    fleets over every year in ``--years`` (default 2019-2025, the program span)
    — the year-matched EIA-860 vintage plus the retiree channel, as the
    backcast default loads them — so a plant retired before 2023 is covered.
    The artifact stacks the POOLED rate (``year == 0``) over every year with a
    PER-YEAR rate (``year == Y``) wherever that year's hours ALONE clear the
    unchanged :data:`_MIN_LOADED_HOURS` trust gate — no new threshold.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO name, e.g. NYISO")
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
        help="ALSO write the per-unit table (pooled) alongside the plant summary",
    )
    args = parser.parse_args(argv)
    iso = args.iso.upper()
    years = sorted(args.years)

    fleets = backcast_fleets(iso, years)
    union = union_fleet(fleets)
    caps = class_capacity(union, TARGET_CLASS)
    if not caps:
        raise SystemExit(f"{iso}: model fleet has no {TARGET_CLASS} plants")
    factors = parasitic_factors()
    units = unit_loaded_heat_rates(iso, years, set(caps))
    if units.empty:
        raise SystemExit(f"{iso}: no unit cleared the loaded-window screen")
    pooled = plant_table(
        units, iso, years, caps, class_heat_rates(union, TARGET_CLASS), factors
    )

    def _year_table(year: int) -> pd.DataFrame | None:
        year_units = unit_loaded_heat_rates(iso, [year], set(caps))
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

    out_path = (
        Path(args.out)
        if args.out
        else (PROCESSED_DIR / f"campd_ct_heat_rates_{iso}.csv")
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
                "parasitic_factor",
                "heat_rate_gross",
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
