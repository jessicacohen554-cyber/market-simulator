"""Derive measured per-plant OPERATING heat rates for the ST_GAS class from CAMPD.

The gas-steam sibling of :mod:`scripts.data.derive_campd_ct_heat_rates` (nyiso-88)
and :mod:`scripts.data.derive_campd_coal_heat_rates` (nwpp-42), built on the
identical identification and written to the identical schema. It is the measured
replacement for the eGRID **plant-average annual** heat rate the non-ERCOT fleet
loader otherwise gives every gas-fired steam boiler
(``market_sim.data.fleet.eia860._rows_to_generators``).

Why the eGRID figure is wrong for a gas steam boiler
----------------------------------------------------
Exactly the reasons the coal sibling records, plus one that is specific to this
class. eGRID's plant rate is ``PLHTIAN / PLNGENAN`` — annual heat input over
annual *net* generation — so it blends **startup fuel, shutdown tails and the
offline hours' fuel** into the number that sets the plant's offer, and its
*level* moves with the plant's capacity factor in the vintage year. The rate
that sets an offer is the rate at which the machine burns fuel **while it is
running**.

The class-specific defect is that a southeastern steam station is very often
**a coal boiler and a gas boiler behind one ORIS code**. eGRID's plant rate
blends the two, and so does the prime-mover-FAMILY rate
(``ScenarioConfig.egrid_family_heat_rates``), because both boilers are prime
mover ``ST`` and a family construction cannot separate two machines inside one
family. Measured on SOCO's own fleet (lane SOCO-53e), that is the whole of the
E C Gaston error: its ST family rate 11.5505 is a blend of one 832 MW coal
boiler with four ~255 MW gas boilers, and the gas boilers' own metered rate is
11.075 — so the model prices 1,020 MW of gas steam 0.475 MMBtu/MWh too dear
while pricing the coal boiler beside it too cheap. A per-unit meter is the only
source that separates them.

The error is a per-plant source defect and not a uniform bias, which is why no
single multiplier can stand in for the measurement: against the model's assigned
rate SOCO's plants run **−0.475 (Gaston), −0.053 (Jack Watson), −0.049 (Greene
County), −0.017 (Yates) and +1.374 (Barry)**. Barry moves the other way and is
applied at full magnitude: its two 1954-vintage 80 MW boilers are metered at
13.98 MMBtu per net MWh across 2,521 steady hours in three years, which is a
genuinely poor machine run 1.6 % of the time, not a meter artifact (98 % of its
operating hours sit inside the physical band). It corroborates the independent
SOCO-53d finding that those units are standby iron rather than campaign iron.

Method — per unit, over the pooled window::

    steady    = hours with opTime >= _MIN_OPTIME and grossLoad > 0, heatInput > 0
    valid     = steady hours whose OWN heatInput/grossLoad is inside
                [_HR_MIN_GROSS, _HR_MAX_GROSS]          (>= _MIN_STEADY_HOURS)
    hr_gross  = sum(heatInput) / sum(grossLoad) over ``valid``
    hr_net    = hr_gross / parasitic_factor(plant)

and the plant value is the generation-weighted mean of its units' ``hr_net``.

**Why the screen is an operating-hour screen and not the CT deriver's
``>= 0.8 x p95`` loaded window.** The coal sibling's argument transfers
verbatim: a steam boiler's *normal* operating range is part load — it is
committed and then cycles between min-load and HSL, which is precisely the
behaviour the model must reproduce — so a near-HSL window would price the plant
at its best point and understate the rate at which it actually burns fuel
across the range the model dispatches it over. ``opTime >= _MIN_OPTIME`` removes
exactly the partial clock hours that carry startup and shutdown fuel, and
removes nothing else. Both windows are REPORTED (``heat_rate_gross`` and
``heat_rate_gross_hsl``) so a reader sees the range; the APPLIED column is the
operating-hour one, fixed here on the physical argument above, before any solve,
and never swept (rules 1 ``[R-STRUCT]`` / 23 ``[R-FROZEN-DERIVE]``).

**Why membership is a capacity-rank PAIRING and not a fuel tag.** The coal
sibling separates a mixed site's machines by CAMPD ``primaryFuelInfo``, and that
tag cannot do the job here. At SOCO's Barry (plant 3) CAMPD files unit 4 —
a 330 MW tangentially-fired boiler — as *Pipeline Natural Gas*, while the model
carries it as a 362 MW ``COAL`` row; a fuel-tag selection would therefore price
the model's two 80 MW ``ST_GAS`` rows off a boiler the model dispatches as coal.
``unitType`` alone cannot do it either, since a coal boiler and a gas boiler
carry the same boiler tags. **The model's own class assignment governs, because
the rate is applied to model rows** (rule 19 ``[R-ONE-MECH]``: one mechanism per
row, and the COAL rows are the coal sibling's population, not this one's). So
each plant's CAMPD boiler units are paired to that plant's own model BOILER rows
(``COAL`` ∪ ``ST_GAS``) by descending capacity, and only the units paired to an
``ST_GAS`` row are kept — the device SOCO-53d established and measured
unambiguous at every SOCO plant.

**The pairing cannot change an applied number, and that is checked, not
asserted.** The artifact is at PLANT grain, so a permutation of the pairing
*within* one plant's ``ST_GAS`` rows leaves the generation-weighted plant value
identical; the only thing the pairing decides is plant MEMBERSHIP — whether a
given boiler is in the gas-steam population at all. At SOCO every such decision
is separated by a factor of 2.8 or more in capacity (Barry: 330 MW unit 4
against 80 MW model rows; Gaston: an 816 MW coal boiler against 256 MW gas
rows). ``--check-pairing`` re-runs the membership under an exact
generator-id-first rule and fails if any plant's applied row moves.

**The net-basis conversion is not optional.** CAMPD meters GROSS load while
eGRID (and therefore the model's heat rate, the LP's dispatched MW, and the
benchmark's "actual") are all on a NET basis. Comparing a gross-basis measured
rate against a net-basis model rate would overstate the correction by the whole
station-service fraction. The factor read here is the SAME committed artifact
the benchmark uses (``parasitic_load_factors.parquet``,
:func:`market_sim.data.campd.pooled_factor_map`), falling back to the committed
class default ``1 - DEFAULT_PARASITIC_LOAD_PCT["ST_GAS"]`` = 0.95, so the
derived heat rate and the actual it will be scored against share one
gross-to-net convention. **Getting the class right matters more here than
anywhere**: SOCO's gas-steam fleet measures a net/gross of 0.938-0.943 on its
unambiguous plant-years (EIA-923 ST/NG net over CAMPD gas-boiler gross), which
the committed ST_GAS default 0.95 reproduces to 1.2 % — while the CT_PEAKER
default 0.99 would understate every rate by 4.2 % and is the wrong class for a
boiler.

Output: ``data/raw/_processed-legacy/campd_st_heat_rates_{ISO}.csv``, one row
per plant, consumed by
:func:`market_sim.data.fleet.campd_bins.measured_st_heat_rates` under
``ScenarioConfig.measured_st_heat_rates``.

Governance (CLAUDE.md rules 13 ``[R-MEASURED]`` / 14 ``[R-ACCURATE]`` /
21 ``[R-DOF]`` / 23 ``[R-FROZEN-DERIVE]`` / 25 ``[R-ISO-SCOPE]``): a unit's
operating heat rate is a physical characteristic of the machine, in the same
admissibility class as the CAMPD min-stable loads, the CT loaded heat rates, the
coal operating heat rates and the CT run horizons. It regenerates for a forward
year from the same pipeline and responds to changed conditions (a retrofit moves
it; a re-powered unit changes class and drops out of the population), so it is
rule-13 admissible as an INPUT — it is not a measured outcome fed back to close
a residual, and nothing in it is fitted to one. ZERO free parameters: every
applied number is ``sum(heatInput)/sum(grossLoad)`` over the plant's own hours.
Per rule 23 it re-derives ONLY when CAMPD publishes new or revised vintages, and
the re-derivation commit must cite that data change. Per rule 25 each ISO's lane
derives its own artifact from its own market's plants.

Usage::

    python scripts/data/derive_campd_gas_st_heat_rates.py --iso SOCO --detail
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

#: The model class this artifact prices. Only ST_GAS: the coal boiler beside it
#: is :mod:`scripts.data.derive_campd_coal_heat_rates`' population, and the
#: turbines are the CT deriver's.
TARGET_CLASS = "ST_GAS"

#: The model boiler classes the pairing ranks over. A CAMPD boiler unit is
#: matched against the plant's rows in BOTH classes and kept only when its
#: partner is :data:`TARGET_CLASS`, so a coal boiler at a mixed site can never
#: be absorbed into the gas-steam rate merely because no coal row was offered
#: to pair with it (the Barry unit-4 case, module docstring).
BOILER_CLASSES: tuple[str, ...] = ("COAL", "ST_GAS")

#: CAMPD ``unitType`` substrings that identify a BOILER, matched case-folded on
#: containment so every published firing configuration ("Tangentially-fired",
#: "Dry bottom wall-fired boiler", "Cell burner boiler", "Cyclone boiler",
#: "Stoker", ...) is caught without enumerating CAMPD's full vocabulary.
BOILER_TYPE_TOKENS: tuple[str, ...] = ("fired", "boiler", "stoker", "cyclone")

#: CAMPD ``unitType`` substrings that are NEVER a boiler however they match
#: above. "Combined cycle" units are the CC block's machines and "Combustion
#: turbine" units are the CT deriver's population.
NON_BOILER_TYPE_TOKENS: tuple[str, ...] = ("combined cycle", "combustion turbine")

#: Steady-state screen: a full clock hour at load. Below this the hour is a
#: partial operating hour — a start, a trip or a shutdown tail — and its fuel
#: is exactly what the eGRID annual average wrongly folds into the offer.
_MIN_OPTIME: float = 0.99

#: Minimum qualifying hours before a unit's operating rate is trusted. A boiler
#: that cleared fewer than this across three pooled vintages has no measured
#: rate and falls back to the loader's existing eGRID behaviour.
_MIN_STEADY_HOURS: int = 200

#: Physical plausibility band (MMBtu per GROSS MWh) for a gas-fired steam
#: boiler. A DATA-INTEGRITY guard on the meter, not a tuning knob: below 7.0 the
#: row implies > 48 % HHV efficiency, which no Rankine steam cycle reaches, and
#: above 25.0 it is a broken heat-input or gross-load channel. The floor sits
#: below the coal sibling's 8.0 because a gas boiler is the more efficient
#: machine and a real 8.5 MMBtu/MWh hour must not be screened out. Applied at
#: BOTH grains — per steady HOUR inside :func:`unit_operating_heat_rates` (the
#: caiso-156 rule-14 lesson: an out-of-band hour cannot inform the rate, and
#: screening only the aggregate lets impossible hours dilute the sums while the
#: plant still flags ``ok``) and to the resulting PLANT aggregate on a NET
#: basis, whose out-of-band rows are written with a ``flag`` and excluded from
#: the applied map. Measured on SOCO: every plausible band in
#: [6, 30] x [20, 30] moves the capacity-weighted result by less than
#: 0.03 MMBtu/MWh, so the band does no work and is not a degree of freedom.
_HR_MIN_GROSS: float = 7.0
_HR_MAX_GROSS: float = 25.0
_HR_MIN_NET: float = 7.0
_HR_MAX_NET: float = 27.0

#: Capacity-pairing integrity guard: a matched pair whose measured p95 operating
#: load over the model row's ``pmax`` falls outside this band is written with a
#: ``flag`` and excluded from the applied map. Wide on purpose — it catches a
#: pairing that is structurally wrong (a 330 MW boiler against an 80 MW row,
#: ratio 4.1) and never a derated machine (SOCO's widest true pair is Barry at
#: 0.75, a 1954 unit whose 1.6 % duty means its p95 never reaches nameplate).
_PAIR_RATIO_MIN: float = 0.5
_PAIR_RATIO_MAX: float = 2.0

#: Reported-only comparison window: the near-HSL rate, for the reader's sense
#: of the plant's range. NEVER the applied column (see the module docstring).
_HSL_PCTILE: float = 90.0


def model_boiler_rows(
    iso: str,
    egrid_family_heat_rates: bool = False,
    measured_ct_heat_rates: bool = False,
) -> pd.DataFrame:
    """Return the ISO's model BOILER rows, one per generator.

    Columns ``plant_code``, ``unit_id``, ``generator_id``, ``plant_group``,
    ``pmax_mw``, ``heat_rate``. ``generator_id`` is the suffix of the loader's
    ``unit_id`` (``"<plant>_<generator>"``), which is the EIA-860 generator
    code and is frequently — but not always — the CAMPD ``unitId`` as well.

    Args:
        iso: ISO identifier, e.g. ``"SOCO"``.
        egrid_family_heat_rates: Load the fleet with
            ``ScenarioConfig.egrid_family_heat_rates`` armed. PROVENANCE ONLY —
            it moves ``heat_rate``, which this artifact reports as
            ``model_heat_rate_egrid`` (what the swap replaces), and NOTHING
            that is applied. The measured rate comes from CAMPD alone, and the
            pairing ranks on ``pmax_mw``, which no heat-rate flag touches.
        measured_ct_heat_rates: Same, for
            ``ScenarioConfig.measured_ct_heat_rates``. It cannot reach a boiler
            row at all (it is gated on ``group == "CT_PEAKER"``); it is
            accepted so the provenance load can reproduce an ISO's whole recipe
            rather than a subset of it.

    Returns:
        One row per generator in :data:`BOILER_CLASSES`.
    """
    fleet = load_fleet_from_csv(
        iso,
        get_iso_config(iso),
        egrid_family_heat_rates=egrid_family_heat_rates,
        measured_ct_heat_rates=measured_ct_heat_rates,
    )
    rows: list[dict] = []
    for gen in fleet:
        if gen.plant_group not in BOILER_CLASSES:
            continue
        code = int(gen.plant_code or 0)
        if not code:
            continue
        unit_id = str(gen.unit_id)
        rows.append(
            {
                "plant_code": code,
                "unit_id": unit_id,
                "generator_id": unit_id.split("_", 1)[1] if "_" in unit_id else "",
                "plant_group": str(gen.plant_group),
                "pmax_mw": float(gen.pmax_mw),
                "heat_rate": float(gen.heat_rate),
            }
        )
    return pd.DataFrame(rows)


def target_plant_codes(iso: str, boilers: pd.DataFrame) -> dict[int, float]:
    """Return ``{plant_code: TARGET_CLASS capacity MW}`` from the model fleet.

    Args:
        iso: ISO identifier (for the error message only).
        boilers: The frame from :func:`model_boiler_rows`.

    Returns:
        Mapping of plant code to the class capacity the model carries there.
    """
    st = boilers[boilers["plant_group"] == TARGET_CLASS]
    return {
        int(code): float(g["pmax_mw"].sum()) for code, g in st.groupby("plant_code")
    }


def model_heat_rates(boilers: pd.DataFrame) -> dict[int, float]:
    """Return the CURRENT capacity-weighted assigned heat rate per plant.

    Written to the artifact alongside the measured rate so the table records
    what it replaces and by how much — the provenance a later reader needs to
    judge the swap without re-running anything. Weighted over the plant's
    :data:`TARGET_CLASS` rows only, which is the population the swap touches.
    """
    st = boilers[boilers["plant_group"] == TARGET_CLASS]
    out: dict[int, float] = {}
    for code, g in st.groupby("plant_code"):
        den = float(g["pmax_mw"].sum())
        if den > 0.0:
            out[int(code)] = float((g["pmax_mw"] * g["heat_rate"]).sum() / den)
    return out


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


def _is_boiler(series: pd.Series) -> pd.Series:
    """Boolean mask of rows whose CAMPD ``unitType`` is a boiler."""
    s = series.astype(str).str.casefold()
    mask = pd.Series(False, index=s.index)
    for token in BOILER_TYPE_TOKENS:
        mask |= s.str.contains(token, regex=False)
    for token in NON_BOILER_TYPE_TOKENS:
        mask &= ~s.str.contains(token, regex=False)
    return mask


def campd_boiler_units(iso: str, years: list[int], codes: set[int]) -> pd.DataFrame:
    """Return the pooled CAMPD boiler-unit hours at the ISO's target plants.

    Each state-year extract is read once and immediately narrowed to the ISO's
    own target-class plants, so a shared state file cannot leak another ISO's
    units in. Hours are pooled across years before the screens, so a unit that
    barely ran in one year still reaches :data:`_MIN_STEADY_HOURS`.

    Args:
        iso: ISO identifier.
        years: CAMPD vintages to pool.
        codes: Plant codes to keep (from :func:`target_plant_codes`).

    Returns:
        The pooled hourly frame, boiler units only, positive load and heat
        input only.
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
                    "unitType",
                ],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            df = df[_is_boiler(df["unitType"])]
            if not df.empty:
                frames.append(df)
    if not frames:
        raise SystemExit(f"{iso}: no CAMPD boiler hours at any {TARGET_CLASS} plant")
    pooled = pd.concat(frames, ignore_index=True).dropna(
        subset=["grossLoad", "heatInput"]
    )
    return pooled[(pooled["grossLoad"] > 0.0) & (pooled["heatInput"] > 0.0)]


def pair_units_to_rows(
    pooled: pd.DataFrame, boilers: pd.DataFrame, exact_id_first: bool = False
) -> pd.DataFrame:
    """Pair each plant's CAMPD boiler units to its model boiler rows.

    Descending capacity on both sides, 1:1, up to the shorter side — the
    SOCO-53d device (``FINDING-soco-53d-2026-09-19.md`` §2). The CAMPD side's
    capacity is the p95 of the unit's own OPERATING gross load, which is the
    only capacity CAMPD publishes; the model side's is ``pmax_mw``.

    Args:
        pooled: The frame from :func:`campd_boiler_units`.
        boilers: The frame from :func:`model_boiler_rows`.
        exact_id_first: When True, pair generator ids that match exactly before
            ranking the remainder by capacity. The ALTERNATIVE construction
            used by ``--check-pairing`` to prove the applied plant rows do not
            depend on the within-plant pairing; never the default.

    Returns:
        Columns ``plant_code``, ``plant_name``, ``unit_id`` (CAMPD),
        ``campd_fuel``, ``p95_op``, ``model_unit_id``, ``model_group``,
        ``model_pmax_mw``, ``pair_ratio``.
    """
    cap = (
        pooled.groupby(["facilityId", "unitId"])
        .agg(
            p95_op=("grossLoad", lambda s: float(np.percentile(s, 95.0))),
            plant_name=("facilityName", "first"),
            campd_fuel=("primaryFuelInfo", "first"),
        )
        .reset_index()
    )
    rows: list[dict] = []
    for code, cu in cap.groupby("facilityId"):
        mr = boilers[boilers["plant_code"] == int(code)]
        cu = cu.sort_values("p95_op", ascending=False).reset_index(drop=True)
        mr = mr.sort_values("pmax_mw", ascending=False).reset_index(drop=True)
        taken_c: set[int] = set()
        taken_m: set[int] = set()
        matched: list[tuple[int, int]] = []
        if exact_id_first:
            by_gen = {str(r.generator_id): i for i, r in mr.iterrows()}
            for i, r in cu.iterrows():
                j = by_gen.get(str(r.unitId))
                if j is not None and j not in taken_m:
                    matched.append((i, j))
                    taken_c.add(i)
                    taken_m.add(j)
        rest_c = [i for i in range(len(cu)) if i not in taken_c]
        rest_m = [j for j in range(len(mr)) if j not in taken_m]
        matched.extend(zip(rest_c, rest_m))
        for i, j in matched:
            rows.append(
                {
                    "plant_code": int(code),
                    "plant_name": str(cu.plant_name[i]),
                    "unit_id": str(cu.unitId[i]),
                    "campd_fuel": str(cu.campd_fuel[i]),
                    "p95_op": float(cu.p95_op[i]),
                    "model_unit_id": str(mr.unit_id[j]),
                    "model_group": str(mr.plant_group[j]),
                    "model_pmax_mw": float(mr.pmax_mw[j]),
                    "pair_ratio": float(cu.p95_op[i]) / float(mr.pmax_mw[j]),
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["plant_code", "p95_op"], ascending=[True, False]
    )


def unit_operating_heat_rates(
    pooled: pd.DataFrame, pairs: pd.DataFrame
) -> pd.DataFrame:
    """Return one row per kept gas-steam boiler with its operating heat rate.

    Args:
        pooled: The frame from :func:`campd_boiler_units`.
        pairs: The frame from :func:`pair_units_to_rows`.

    Returns:
        Columns ``plant_code``, ``plant_name``, ``unit_id``, ``gross_mwh``,
        ``steady_hours``, ``cap_mw``, ``pair_ratio``, ``hr_gross``,
        ``hr_gross_hsl``.
    """
    kept = pairs[pairs["model_group"] == TARGET_CLASS]
    keep = set(zip(kept["plant_code"].astype(int), kept["unit_id"].astype(str)))
    ratios = {
        (int(r.plant_code), str(r.unit_id)): float(r.pair_ratio)
        for r in kept.itertuples()
    }
    rows: list[dict] = []
    for (code, unit), g in pooled.groupby(["facilityId", "unitId"], sort=True):
        key = (int(code), str(unit))
        if key not in keep:
            continue
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
                "pair_ratio": ratios[key],
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
        ratios = g["pair_ratio"].to_numpy(dtype=float)
        model = model_hr.get(int(code))
        if hr_net < _HR_MIN_NET:
            flag = "below_physical_band"
        elif hr_net > _HR_MAX_NET:
            flag = "above_physical_band"
        elif (ratios < _PAIR_RATIO_MIN).any() or (ratios > _PAIR_RATIO_MAX).any():
            flag = "capacity_pairing_mismatch"
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
                "pair_ratio_min": round(float(ratios.min()), 4),
                "pair_ratio_max": round(float(ratios.max()), 4),
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
        "(data/raw/campd-unit-level), boiler unitType paired to the plant's own "
        f"model {list(BOILER_CLASSES)} rows by descending capacity and kept "
        f"where the partner is {TARGET_CLASS}; per unit heat_rate = "
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
        f"applied. The net band [{_HR_MIN_NET}, {_HR_MAX_NET}] and the pairing "
        f"band [{_PAIR_RATIO_MIN}, {_PAIR_RATIO_MAX}] also flag the plant "
        "aggregate; only flag=='ok' rows are applied."
    )
    return out


def main(argv: list[str] | None = None) -> int:
    """Derive and write the measured gas-steam operating-heat-rate artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO name, e.g. SOCO")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025],
        help="CAMPD vintages to pool (default 2023 2024 2025)",
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
            "Load the provenance fleet with ScenarioConfig."
            "egrid_family_heat_rates armed (the SOCO keeper's recipe). "
            "PROVENANCE ONLY: it moves model_heat_rate_egrid and nothing that "
            "is applied"
        ),
    )
    parser.add_argument(
        "--measured-ct-heat-rates",
        action="store_true",
        help=(
            "Load the provenance fleet with ScenarioConfig."
            "measured_ct_heat_rates armed. PROVENANCE ONLY (and it cannot "
            "reach a boiler row at all)"
        ),
    )
    parser.add_argument(
        "--check-pairing",
        action="store_true",
        help=(
            "Re-run membership under an exact generator-id-first pairing and "
            "FAIL if any applied plant row moves (proves the within-plant "
            "pairing cannot change an applied number)"
        ),
    )
    args = parser.parse_args(argv)
    iso = args.iso.upper()

    boilers = model_boiler_rows(
        iso,
        egrid_family_heat_rates=args.egrid_family_heat_rates,
        measured_ct_heat_rates=args.measured_ct_heat_rates,
    )
    # The pairing must not depend on the provenance recipe. It ranks on pmax,
    # which no heat-rate flag touches — asserted rather than assumed, because
    # a silent membership change would move an APPLIED number.
    plain = model_boiler_rows(iso)
    if not plain[["plant_code", "unit_id", "pmax_mw", "plant_group"]].equals(
        boilers[["plant_code", "unit_id", "pmax_mw", "plant_group"]]
    ):
        raise SystemExit(f"{iso}: the provenance recipe moved the pairing population")
    caps = target_plant_codes(iso, boilers)
    if not caps:
        raise SystemExit(f"{iso}: model fleet has no {TARGET_CLASS} plants")
    pooled = campd_boiler_units(iso, args.years, set(caps))
    pairs = pair_units_to_rows(pooled, boilers)
    units = unit_operating_heat_rates(pooled, pairs)
    if units.empty:
        raise SystemExit(f"{iso}: no unit cleared the steady-state screen")
    model_hr = model_heat_rates(boilers)
    factors = parasitic_factors()
    table = plant_table(units, iso, args.years, caps, model_hr, factors)
    # Record WHICH fleet recipe the provenance columns were read under, so a
    # later reader can tell what "model_heat_rate_egrid" means without guessing.
    recipe = [
        name
        for name, on in (
            ("egrid_family_heat_rates", args.egrid_family_heat_rates),
            ("measured_ct_heat_rates", args.measured_ct_heat_rates),
        )
        if on
    ]
    table["model_recipe"] = "+".join(recipe) if recipe else "loader_defaults"

    print(f"=== {iso}: capacity-rank pairing, CAMPD boilers -> model boiler rows ===")
    print(
        pairs[
            [
                "plant_code",
                "plant_name",
                "unit_id",
                "campd_fuel",
                "p95_op",
                "model_unit_id",
                "model_group",
                "model_pmax_mw",
                "pair_ratio",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )

    if args.check_pairing:
        alt_pairs = pair_units_to_rows(pooled, boilers, exact_id_first=True)
        alt_units = unit_operating_heat_rates(pooled, alt_pairs)
        alt = plant_table(alt_units, iso, args.years, caps, model_hr, factors)
        cols = ["plant_code", "heat_rate", "flag"]
        same = (
            table[cols].reset_index(drop=True).equals(alt[cols].reset_index(drop=True))
        )
        print(f"\n  --check-pairing: applied plant rows identical: {same}")
        if not same:
            print(table[cols].to_string(index=False))
            print(alt[cols].to_string(index=False))
            raise SystemExit(f"{iso}: the within-plant pairing CHANGES an applied row")

    out_path = (
        Path(args.out)
        if args.out
        else (PROCESSED_DIR / f"campd_st_heat_rates_{iso}.csv")
    )
    table.to_csv(out_path, index=False)
    print(f"\nwrote {out_path} ({len(table)} plant rows)")

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
            "  capacity-weighted   model %.4f -> measured %.4f (%+.1f %%)"
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
            "  generation-weighted model %.4f -> measured %.4f (%+.1f %%)"
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
                "pair_ratio_min",
                "pair_ratio_max",
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
