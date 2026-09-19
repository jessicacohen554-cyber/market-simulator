"""Derive measured gas-STEAM CAMPAIGN commitment parameters from CAMPD.

The measured-conduct basis for the P1-native gas-steam campaign commitment
floor (``ScenarioConfig.soco_gas_st_campaign_commitment`` and the ISO-neutral
detector :func:`market_sim.model.commitment.caiso_ra_mustoffer_min_gen`). It is
the CAMPAIGN sibling of ``derive_campd_gas_commitment_params.py``: that script
measures the *gap-bridge* statistics a two-shifting fleet needs, this one
measures the *campaign* statistics a fleet that synchronizes for weeks at a
time needs.

WHY A SEPARATE DERIVE, and why plant grain is measured as a UNION of units
-------------------------------------------------------------------------
``derive_campd_gas_commitment_params.py`` keys on the CAMPD **facility**, and
drops a facility whose model rows span more than one target class as
AMBIGUOUS. On a vertically-integrated southeastern fleet that convention is
unusable: Barry (3), E C Gaston (26), Greene County (10) and Jack Watson
(2049) each carry gas boilers, coal boilers and/or combustion turbines under
ONE CEMS facility id, so the facility-grain artifact reports TURBINE conduct
for the steam class (measured on SOCO: ``min_load_frac`` 0.0848 and a run p50
of 6 h, against 0.066-0.163 and 286-546 h for the boilers alone).

This script therefore

1. selects CAMPD units by ``unitType`` (the boiler types), the same device
   ``derive_campd_ct_heat_rates.py`` uses to pull turbines out of a mixed
   facility; then
2. pairs those boiler units to the plant's OWN model boiler rows by capacity
   rank (CAMPD p99.5 gross load against the fleet row's ``pmax_mw``) and keeps
   only the units paired to a ``gas_st`` row. **The model's class assignment
   governs**, deliberately: the floor is applied to model rows, so the
   measurement must be of the units those rows represent. On SOCO the pairing
   is unambiguous at every plant (within 5-10 % on all fifteen units) and it
   resolves the one place CAMPD's own ``primaryFuelInfo`` disagrees with the
   model — Barry unit 4, which CAMPD files as Pipeline Natural Gas and the
   model carries as a 362 MW coal row. That disagreement is REPORTED by
   ``--detail`` and routed, never silently adopted.
3. measures the plant as **synchronized** in any hour at least one of its kept
   units is online by that unit's own threshold (the union of the per-unit
   masks), not by a threshold on the plant sum. A threshold on the sum
   fragments a multi-unit plant whose units cycle independently around it — on
   Gaston 2023 it reports 56 campaigns of median 5 h where the union reports
   10 of median 305 h, which is the same turbine-conduct artifact one layer
   down.

THE TWO PARAMETERS
------------------
``min_load_frac`` — the PLANT-basis minimum stable load: p5 of the plant's own
summed output over its synchronized hours, over its p99.5 (the "loading-when-
on" construction of ``derive_campd_gas_commitment_params.py``, taken on the
plant basis because the consumer floors ``min_load_frac × plant_pmax``). It is
the plant's minimum stable CONFIGURATION — on SOCO's four campaign plants it
lands at 0.066-0.137, close to one unit at its own turndown, which is what a
minimum configuration is.

``min_run_hours`` — the p25 of the plant's pooled campaign-length distribution.
The LOW order statistic, deliberately: an observed run bounds a minimum-run
CONSTRAINT from above, so the p25 is the conservative identification (the
nyiso-90 / SPP-44 convention, ``NYISO_..._MIN_RUN_HOURS`` and
``SPP_GAS_BRIDGE_MIN_RUN_HOURS``). The median would assert a constraint a
quarter of the plant's own observed campaigns violate.

MEMBERSHIP — ``sync_share`` and the ``flag`` column
---------------------------------------------------
A commitment floor must not bind in hours its own driver evidence says the
class is offline (CLAUDE.md rule 17 ``[R-FLOOR-WINDOW]``). A plant that is
synchronized a few per cent of the year is not running campaigns at all — it
is standby/reserve iron — and holding it at minimum load would be exactly that
defect. Membership is therefore the plant's own measured synchronized share
against :data:`CAMPAIGN_DUTY_MIN_SYNC_SHARE`, and a plant below it is written
with ``flag == "not_campaign_duty"`` and never applied (the consumer reads only
``flag == "ok"``, the ``derive_egrid_family_heat_rates.py`` convention).

:data:`CAMPAIGN_DUTY_MIN_SYNC_SHARE` is 0.50 — "synchronized more often than
not", the plain meaning of campaign duty. It is declared ex ante and **never
swept** (rule 1 ``[R-STRUCT]`` condition (c) applied to a scope): on SOCO the
population separates by an order of magnitude — 0.063 for Barry against
0.639 / 0.752 / 0.843 / 0.920 for the other four — so **every value in
(0.07, 0.63) yields the identical partition**, in all three years. It selects
nothing; it names a gap the data already has.

GOVERNANCE (CLAUDE.md rules 13 ``[R-MEASURED]`` / 23 ``[R-FROZEN-DERIVE]`` /
25 ``[R-ISO-SCOPE]``)
---------------------------------------------------------------------------
All three statistics are unit-CONDUCT properties in the same admissibility
class as the CAMPD committed shares, min-stable loads and CT run horizons:
each would be produced identically for a forward year from the then-current
CAMPD vintage, and each responds to changed conditions (a fleet that cycles
more shortens its measured campaigns and drops out of the population). None is
a measured OUTCOME fed back to close a residual — the floor's PLACEMENT comes
from the model's own P0 run pattern, never from the meter. The artifact
re-derives ONLY when its source vintages update, and it is written per ISO
from that ISO's own plants, so no number crosses an ISO boundary.

Output: ``data/raw/_processed-legacy/campd_gas_st_campaign_params_{ISO}.csv``
(one row per covered plant; ``--detail`` adds the per-unit pairing table).

Usage::

    python scripts/data/derive_campd_gas_st_campaign_params.py --iso SOCO
    python scripts/data/derive_campd_gas_st_campaign_params.py --iso SOCO --detail
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

#: CAMPD ``unitType`` prefixes (casefolded) that are BOILERS. The complement of
#: ``derive_campd_ct_heat_rates.CT_UNIT_TYPE``: CEMS unit ids carry no model
#: class, but CAMPD's own ``unitType`` says which units are steam boilers, so a
#: mixed facility contributes only its boilers instead of being dropped as
#: unattributable.
BOILER_UNIT_TYPES: tuple[str, ...] = (
    "tangentially-fired",
    "dry bottom wall-fired boiler",
    "cell burner boiler",
    "circulating fluidized bed boiler",
    "wet bottom wall-fired boiler",
    "cyclone boiler",
    "stoker",
    "dry bottom turbo-fired boiler",
    "arch-fired boiler",
    "bubbling fluidized bed boiler",
)

#: Model fuel types whose rows are BOILERS at a plant — the pairing universe on
#: the model side (the CAMPD side is :data:`BOILER_UNIT_TYPES`).
MODEL_BOILER_FUELS: tuple[str, ...] = ("gas_st", "coal")

#: The model fuel type this artifact describes.
TARGET_FUEL: str = "gas_st"

#: Robust maximum-sustained-load percentile (the HSL proxy), matching
#: ``derive_campd_gas_commitment_params._HSL_PCTILE``.
_HSL_PCTILE: float = 99.5

#: Online threshold as a fraction of a unit's OWN HSL proxy, floored at the
#: CAMPD online convention. Matches ``_ONLINE_FRAC`` in the sibling derive.
_ONLINE_FRAC: float = 0.05

#: Percentile of the synchronized-hours loading distribution taken as the
#: plant's minimum stable load. Matches ``_LSL_PCTILE`` in the sibling derive.
_LSL_PCTILE: float = 5.0

#: Order statistic of the pooled campaign-length distribution taken as the
#: minimum-run identification. LOW by construction: an observed run bounds a
#: min-run CONSTRAINT from above (nyiso-90 / SPP-44).
_MIN_RUN_PCTILE: float = 25.0

#: Membership gate: the measured share of hours the plant is synchronized,
#: below which it is not in the day-ahead campaign-commitment population at
#: all. Declared ex ante and never swept — see the module docstring.
CAMPAIGN_DUTY_MIN_SYNC_SHARE: float = 0.50

#: Provenance string written on every row.
SOURCE: str = (
    "EPA CAMPD unit-level hourly grossLoad (data/raw/campd-unit-level), boiler "
    "unitTypes only, paired to the plant's own model boiler rows by capacity "
    "rank and restricted to the units paired to a gas_st row. Plant is "
    "SYNCHRONIZED in any hour at least one kept unit is online by its own "
    "threshold max(1.0 MW, 0.05 x its p99.5 gross load); min_load_frac = p5 of "
    "the plant's summed output over synchronized hours / its p99.5 (PLANT "
    "basis, the basis a floor multiplied by plant pmax requires), taken as the "
    "median across years; min_run_hours = p25 of the pooled campaign-length "
    "distribution (the low order statistic — an observed run bounds a min-run "
    "constraint from above); sync_share = mean across years. flag == 'ok' only "
    "where sync_share >= 0.50 (campaign duty); a plant below it is standby "
    "iron and is never floored (rule 17 [R-FLOOR-WINDOW])."
)


def campaign_lengths(on: np.ndarray) -> np.ndarray:
    """Return the lengths (hours) of maximal True-blocks in ``on``."""
    d = np.diff(np.concatenate([[0], on.astype(np.int8), [0]]))
    return np.where(d == -1)[0] - np.where(d == 1)[0]


def load_campd(iso: str, years: tuple[int, ...]) -> pd.DataFrame:
    """Return the pooled CAMPD boiler-unit hourly frame for *iso*'s states."""
    frames = []
    for state in states_for_iso(iso):
        for year in years:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            frame = pd.read_parquet(
                path,
                columns=[
                    "facilityId",
                    "unitId",
                    "date",
                    "hour",
                    "grossLoad",
                    "unitType",
                ],
            )
            frame["year"] = year
            frames.append(frame)
    if not frames:
        raise SystemExit(f"no CAMPD unit-level files for {iso} {years}")
    out = pd.concat(frames, ignore_index=True)
    kind = out["unitType"].str.lower().str.strip()
    out = out[kind.str.startswith(BOILER_UNIT_TYPES)].copy()
    out["gl"] = out["grossLoad"].fillna(0.0)
    out["ts"] = pd.to_datetime(out["date"]) + pd.to_timedelta(out["hour"], unit="h")
    return out


def pair_units_to_model_rows(
    campd: pd.DataFrame, fleet: pd.DataFrame, plant_code: int
) -> tuple[list[str], list[tuple[str, float, str, float]]]:
    """Pair a plant's CAMPD boiler units to its model boiler rows by capacity rank.

    Returns ``(kept_unit_ids, detail_rows)`` where a detail row is
    ``(campd_unit_id, campd_hsl, model_fuel_type, model_pmax_mw)``.
    """
    rows = fleet[
        (fleet["plant_id"] == plant_code)
        & (fleet["fuel_type"].isin(MODEL_BOILER_FUELS))
    ].sort_values("pmax_mw", ascending=False)
    hsl = (
        campd[campd["facilityId"] == str(plant_code)]
        .groupby("unitId")["gl"]
        .quantile(_HSL_PCTILE / 100.0)
        .sort_values(ascending=False)
    )
    kept: list[str] = []
    detail: list[tuple[str, float, str, float]] = []
    for (unit_id, unit_hsl), (_, row) in zip(hsl.items(), rows.iterrows()):
        detail.append(
            (unit_id, float(unit_hsl), str(row.fuel_type), float(row.pmax_mw))
        )
        if row.fuel_type == TARGET_FUEL:
            kept.append(unit_id)
    return kept, detail


def measure_plant(
    campd: pd.DataFrame, plant_code: int, units: list[str], years: tuple[int, ...]
) -> dict | None:
    """Return the measured campaign statistics for one plant, or ``None``."""
    sub = campd[
        (campd["facilityId"] == str(plant_code)) & (campd["unitId"].isin(units))
    ]
    fracs: list[float] = []
    shares: list[float] = []
    campaigns: list[int] = []
    per_year: list[tuple[int, int, int]] = []
    for year in years:
        year_frame = sub[sub["year"] == year]
        if year_frame.empty:
            continue
        index = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
        total = np.zeros(len(index))
        synced = np.zeros(len(index), dtype=bool)
        for _, unit_frame in year_frame.groupby("unitId", observed=True):
            series = (
                unit_frame.groupby("ts")["gl"].sum().reindex(index, fill_value=0.0)
            ).to_numpy()
            unit_hsl = float(np.percentile(series, _HSL_PCTILE))
            if unit_hsl <= 0.0:
                continue
            synced |= series >= max(_ONLINE_MW, _ONLINE_FRAC * unit_hsl)
            total += series
        plant_hsl = float(np.percentile(total, _HSL_PCTILE))
        if plant_hsl <= 0.0 or int(synced.sum()) < 10:
            continue
        plant_lsl = float(np.percentile(total[synced], _LSL_PCTILE))
        lengths = campaign_lengths(synced)
        fracs.append(plant_lsl / plant_hsl)
        shares.append(float(synced.mean()))
        campaigns.extend(int(x) for x in lengths)
        per_year.append((year, int(synced.sum()), int(lengths.size)))
    if not fracs or not campaigns:
        return None
    sync_share = float(np.mean(shares))
    return {
        "plant_code": plant_code,
        "n_units": len(units),
        "min_load_frac": round(float(np.median(fracs)), 4),
        "min_run_hours": int(round(float(np.percentile(campaigns, _MIN_RUN_PCTILE)))),
        "campaign_p50_hours": int(round(float(np.percentile(campaigns, 50.0)))),
        "sync_share": round(sync_share, 4),
        "campaigns_per_year": round(len(campaigns) / max(len(per_year), 1), 1),
        "flag": "ok"
        if sync_share >= CAMPAIGN_DUTY_MIN_SYNC_SHARE
        else "not_campaign_duty",
        "per_year": ";".join(f"{y}:{h}h/{n}c" for y, h, n in per_year),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True)
    parser.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    parser.add_argument("--detail", action="store_true", help="print the pairing table")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    iso = args.iso.upper()
    years = tuple(args.years)
    fleet = pd.read_parquet(
        RAW_DIR / "_processed-legacy" / f"{iso.lower()}_fleet_binned.parquet"
    )
    plants = sorted(
        int(code)
        for code in fleet.loc[fleet["fuel_type"] == TARGET_FUEL, "plant_id"].unique()
    )
    campd = load_campd(iso, years)

    rows: list[dict] = []
    for plant_code in plants:
        units, detail = pair_units_to_model_rows(campd, fleet, plant_code)
        if args.detail:
            for unit_id, unit_hsl, fuel, pmax in detail:
                mark = "KEEP" if fuel == TARGET_FUEL else "drop"
                print(
                    f"  p{plant_code:<6} campd {unit_id:<6} HSL {unit_hsl:>7.1f}"
                    f"  <->  model {fuel:<7} pmax {pmax:>7.1f}  {mark}"
                )
        if not units:
            continue
        measured = measure_plant(campd, plant_code, units, years)
        if measured is None:
            continue
        name = fleet.loc[fleet["plant_id"] == plant_code, "plant_name"].iloc[0]
        measured["plant_name"] = name
        measured["class_capacity_mw"] = round(
            float(
                fleet.loc[
                    (fleet["plant_id"] == plant_code)
                    & (fleet["fuel_type"] == TARGET_FUEL),
                    "pmax_mw",
                ].sum()
            ),
            1,
        )
        measured["iso"] = iso
        measured["years"] = "-".join(str(y) for y in years)
        measured["source"] = SOURCE
        rows.append(measured)

    if not rows:
        raise SystemExit(f"{iso}: no covered gas_st plants")
    out_frame = pd.DataFrame(rows)[
        [
            "plant_code",
            "plant_name",
            "n_units",
            "class_capacity_mw",
            "min_load_frac",
            "min_run_hours",
            "campaign_p50_hours",
            "sync_share",
            "campaigns_per_year",
            "per_year",
            "flag",
            "iso",
            "years",
            "source",
        ]
    ].sort_values("class_capacity_mw", ascending=False)
    out_path = args.out or (PROCESSED_DIR / f"campd_gas_st_campaign_params_{iso}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_frame.to_csv(out_path, index=False)
    print(out_frame.drop(columns=["source", "per_year"]).to_string(index=False))
    applied = out_frame[out_frame["flag"] == "ok"]
    print(
        f"\n{iso}: {len(out_frame)} covered gas_st plant(s), {len(applied)} applied "
        f"({applied['class_capacity_mw'].sum():.1f} of "
        f"{out_frame['class_capacity_mw'].sum():.1f} MW) -> {out_path}"
    )


if __name__ == "__main__":
    main()
