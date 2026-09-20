"""Derive measured per-plant OPERATING heat rates for CC_REGULAR from CAMPD.

The combined-cycle sibling of :mod:`scripts.data.derive_campd_coal_heat_rates`
(nwpp-42), :mod:`scripts.data.derive_campd_gas_st_heat_rates` (soco-53e) and
:mod:`scripts.data.derive_campd_ct_heat_rates` (nyiso-88), built on the
identical identification and written to the identical schema. It is the
measured replacement for the eGRID **plant-average annual** heat rate — or,
at a multi-family site, the eGRID prime-mover-FAMILY rate
(``ScenarioConfig.egrid_family_heat_rates``) — that the fleet loader otherwise
gives every combined-cycle generator
(``market_sim.data.fleet.eia860._rows_to_generators``).

With this artifact CC_REGULAR stops being the last thermal class in the
footprint still priced off an unmeasured annual average: CT, ST_GAS and COAL
all took their own meter at soco-53, soco-53e and soco-53f respectively.

Why the eGRID figure is wrong for a combined cycle
--------------------------------------------------
eGRID's plant rate is ``PLHTIAN / PLNGENAN`` — annual heat input over annual
*net* generation — so it blends **startup fuel and shutdown tails** and the
**offline hours' fuel** into the number that sets the plant's offer. It is
also a *level* that moves with the plant's capacity factor in the vintage
year, and for a combined cycle there is a sharper version of that defect than
for any other class: **a unit commissioned IN the vintage year is published at
its commissioning-year average**, which carries first-fire, tuning and
acceptance-test fuel against a part-year denominator.

Measured on SOCO's own fleet (lane SOCO-57), that is not hypothetical. Lowman
Energy Center (plant 56) is a combined cycle whose CT *and* steam generator
both carry EIA-860 ``Operating Year`` **2023**; eGRID's 2023 vintage therefore
prices it at **8.105 MMBtu/MWh** — 42 % HHV efficiency, an F-class number —
while its own meter reads **6.30 net, stable to ±0.03 across three years**
(≈54 %, which is what a new H-class machine does). The model was pricing a
brand-new machine as a twenty-five-year-old one, by **$5.10/MWh**.

The error is a per-plant source defect, not a uniform bias — on SOCO the
capacity-weighted level barely moves while three plants move 0.70–1.80
MMBtu/MWh and nine move less than 0.15 — which is why no single multiplier can
stand in for the measurement.

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
window. A combined cycle is *committed* and then cycles between min-load and
HSL — the behaviour the model must reproduce, and the range the model
dispatches it over — so a near-HSL window would price it at its best point and
understate the rate at which it actually burns fuel. This is the coal
deriver's argument, and it holds here for the same physical reason.
``opTime >= _MIN_OPTIME`` removes exactly the partial clock hours that carry
startup and shutdown fuel, and removes nothing else. Both windows are REPORTED
(``heat_rate_gross`` and ``heat_rate_gross_hsl``) so a reader sees the range;
the APPLIED column is the operating-hour one, fixed here on the physical
argument above, before any solve, and never swept (rules 1 ``[R-STRUCT]`` /
23 ``[R-FROZEN-DERIVE]``).

**Why the technology tag is ``unitType`` and not ``primaryFuelInfo``.** The
coal deriver separates a mixed site's machines by ``primaryFuelInfo`` because
at its sites the coal units and the gas-converted units are both boilers.
That tag cannot do the job here, and SOCO is the proof: lane SOCO-56
established that Barry (plant 3) units 1, 2 and 4 are gas-fired **boilers**
whose ``primaryFuelInfo`` reads "Pipeline Natural Gas" exactly as the site's
five genuine combined-cycle units do. Only ``unitType`` — "Tangentially-fired"
against "Combined cycle" — separates them, and routing those three boilers
into the combined-cycle bin is the precise defect SOCO-56 repaired. The match
is a case-folded **prefix** so CAMPD's commissioning variants
("Combined cycle (Started Feb 19, 2023)") are caught with the plain string.

**THE BOUNDARY GUARD — and it is this deriver's load-bearing addition.**
``heatInput / grossLoad`` is the plant's combined-cycle heat rate **only if
CAMPD's gross load includes the steam turbine's output**. At some sites it
does not: the combustion turbines report and the unfired steam generator does
not, so the ratio is the **combustion-turbine** rate — roughly 1.5x the true
combined-cycle rate, because the steam tail is about a third of a CC's output
for none of its fuel. Applying that as a CC heat rate would price a healthy
plant out of merit on a metering artifact.

The guard is an **identity test against an independent source**: CAMPD's
pooled CC gross load over the SAME year's EIA-923 CC net generation, read
through the benchmark's own ``_eia923_frame`` so the comparator is exactly the
series the run is scored against. A plant whose steam is metered must read
``gross/net`` ≈ ``1/parasitic`` ≈ 1.03; a plant missing its steam reads ≈ 0.68.
Measured on SOCO the two clusters are **0.675 / 0.719 against 1.014 … 1.116**
— separated by a factor of 1.4 with nothing between 0.72 and 1.01 — so the
band :data:`_BOUNDARY_MIN` … :data:`_BOUNDARY_MAX` is fixed on physics well
inside an empty gap, and **no value in [0.75, 1.00] would change the
partition**. It is a DATA-INTEGRITY guard, not a tuning knob, and it is fixed
before any solve. Plants it refuses are written with a ``flag`` and are NOT
applied — they keep their existing eGRID behaviour.

**The net-basis conversion is not optional.** CAMPD meters GROSS load while
eGRID (and therefore the model's heat rate, the LP's dispatched MW, and the
benchmark's "actual") are all on a NET basis. The factor read here is the SAME
committed artifact the benchmark uses (``parasitic_load_factors.parquet``,
:func:`market_sim.data.campd.pooled_factor_map`), falling back to the
committed class default, so the derived heat rate and the actual it will be
scored against share one gross-to-net convention. Note the cross-check this
affords: for a plant whose steam IS metered the boundary ratio and the
class-default factor are two independent estimates of the same quantity, and
on SOCO they agree (E B Harris 1.023 against 1/0.975 = 1.0256).

Governance (CLAUDE.md rules 13 ``[R-MEASURED]`` / 14 ``[R-ACCURATE]`` /
21 ``[R-DOF]`` / 23 ``[R-FROZEN-DERIVE]`` / 25 ``[R-ISO-SCOPE]``): a unit's
operating heat rate is a physical characteristic of the machine, in the same
admissibility class as the CAMPD min-stable loads and the CT loaded heat
rates. It regenerates for a forward year from the same pipeline and responds
to changed conditions (a retrofit moves it; a repowered unit re-meters), so it
is rule-13 admissible as an INPUT — not a measured outcome fed back to close a
residual, and nothing in it is fitted to one. ZERO free parameters: every
applied number is ``sum(heatInput)/sum(grossLoad)`` over the plant's own
hours. Per rule 23 it re-derives ONLY when CAMPD publishes new or revised
vintages, and the re-derivation commit must cite that data change. Per rule 25
each ISO's lane derives its own artifact from its own market's plants.

Output: ``data/raw/_processed-legacy/campd_cc_heat_rates_{ISO}.csv``, one row
per plant, consumed by
:func:`market_sim.data.fleet.campd_bins.measured_cc_heat_rates` under
``ScenarioConfig.measured_cc_heat_rates``.

Usage::

    python scripts/data/derive_campd_cc_heat_rates.py --iso SOCO \\
        --egrid-family-heat-rates --measured-ct-heat-rates \\
        --measured-st-heat-rates --measured-coal-heat-rates --detail
"""

from __future__ import annotations

import argparse
import importlib.util
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

#: The model class this artifact prices. Only CC_REGULAR: a cogenerating
#: combined cycle classes CC_CHP in the model fleet and is priced by the CHP
#: path, whose host-steam boundary no unfired-plant meter can speak for. That
#: exclusion is deliberate and matches soco-53c, which refused five
#: cogeneration plants whose eGRID families would not recompose.
TARGET_CLASS = "CC_REGULAR"

#: CAMPD ``unitType`` prefix counted as a combined-cycle machine, matched
#: case-folded on the PREFIX so the commissioning variants CAMPD publishes
#: ("Combined cycle (Started Feb 19, 2023)") are caught without enumerating
#: them. See the module docstring for why this tag and not ``primaryFuelInfo``.
CC_UNIT_TYPE_PREFIX = "combined cycle"

#: Steady-state screen: a full clock hour at load. Below this the hour is a
#: partial operating hour — a start, a trip or a shutdown tail — and its fuel
#: is exactly what the eGRID annual average wrongly folds into the offer.
_MIN_OPTIME: float = 0.99

#: Minimum qualifying hours before a unit's operating rate is trusted. A unit
#: that cleared fewer than this across three pooled vintages has no measured
#: rate and falls back to the loader's existing eGRID behaviour.
_MIN_STEADY_HOURS: int = 200

#: Physical plausibility band (MMBtu per GROSS MWh) for a combined cycle. A
#: DATA-INTEGRITY guard on the meter, not a tuning knob: below 5.0 the row
#: implies > 68 % HHV efficiency, which no combined cycle in service reaches
#: (the best H-class machines sit near 5.7 gross at full load), and above 20.0
#: it is 17 % efficiency — below any operating point a CC holds, so the row is
#: a broken heat-input or gross-load channel. Applied at BOTH grains — per
#: steady HOUR inside :func:`unit_operating_heat_rates` (the caiso-156 rule-14
#: lesson: an out-of-band hour cannot inform the rate, and screening only the
#: aggregate lets impossible hours dilute the sums while the plant still flags
#: ``ok``) and to the resulting PLANT aggregate on a NET basis, whose
#: out-of-band rows are written with a ``flag`` and excluded from the applied
#: map.
_HR_MIN_GROSS: float = 5.0
_HR_MAX_GROSS: float = 20.0
_HR_MIN_NET: float = 5.0
_HR_MAX_NET: float = 22.0

#: THE BOUNDARY GUARD (module docstring). CAMPD pooled CC gross load over
#: EIA-923 CC net generation. A plant whose steam turbine is metered reads
#: ~1/parasitic ~ 1.03; one whose steam is missing reads ~0.68. The band sits
#: inside the empty gap between those clusters and is fixed on physics ex
#: ante — never swept, and no value in [0.75, 1.00] moves the partition.
_BOUNDARY_MIN: float = 0.90
_BOUNDARY_MAX: float = 1.25

#: Reported-only comparison window: the near-HSL rate, for the reader's sense
#: of the plant's range. NEVER the applied column (see the module docstring).
_HSL_PCTILE: float = 90.0


def provenance_fleet(
    iso: str,
    egrid_family_heat_rates: bool = False,
    measured_ct_heat_rates: bool = False,
    measured_st_heat_rates: bool = False,
    measured_coal_heat_rates: bool = False,
) -> list:
    """Return the ISO's model fleet under a stated PROVENANCE recipe.

    The flags move ``heat_rate`` on rows this artifact REPORTS against
    (``model_heat_rate_egrid`` — what the swap replaces) and nothing that is
    applied: the measured rate comes from CAMPD alone, and plant membership is
    the model's own :data:`TARGET_CLASS` assignment, which no heat-rate flag
    touches. They exist because an ISO whose keeper already carries them (SOCO
    carries all four) would otherwise have its artifact report a delta against
    a fleet nobody solves — the loader defaults — and a reader could not tell
    what ``model_heat_rate_egrid`` meant.

    Of the four, only ``egrid_family_heat_rates`` can reach a
    :data:`TARGET_CLASS` row at all: the other three are each gated on their
    own group (CT_PEAKER / ST_GAS / COAL), which is disjoint from this one by
    construction, since a row resolves to exactly one group.

    Args:
        iso: ISO identifier, e.g. ``"SOCO"``.
        egrid_family_heat_rates: Arm ``ScenarioConfig.egrid_family_heat_rates``.
        measured_ct_heat_rates: Arm ``ScenarioConfig.measured_ct_heat_rates``.
        measured_st_heat_rates: Arm ``ScenarioConfig.measured_st_heat_rates``.
        measured_coal_heat_rates: Arm ``ScenarioConfig.measured_coal_heat_rates``.

    Returns:
        The loaded generator list.
    """
    return load_fleet_from_csv(
        iso,
        get_iso_config(iso),
        egrid_family_heat_rates=egrid_family_heat_rates,
        measured_ct_heat_rates=measured_ct_heat_rates,
        measured_st_heat_rates=measured_st_heat_rates,
        measured_coal_heat_rates=measured_coal_heat_rates,
    )


def target_plant_codes(iso: str, fleet: list | None = None) -> dict[int, float]:
    """Return ``{plant_code: CC_REGULAR capacity MW}`` from the ISO's fleet.

    A plant qualifies on having ANY :data:`TARGET_CLASS` generator, so a site
    whose other units are boilers or peakers is included — its combined-cycle
    machines are separated from them downstream by CAMPD ``unitType``.

    Args:
        iso: ISO identifier, e.g. ``"SOCO"``.
        fleet: An already-loaded fleet (see :func:`provenance_fleet`). ``None``
            loads the ISO's loader-default fleet.

    Returns:
        Mapping of plant code to the class capacity the model carries there.
    """
    fleet = load_fleet_from_csv(iso, get_iso_config(iso)) if fleet is None else fleet
    caps: dict[int, float] = {}
    for gen in fleet:
        if gen.plant_group != TARGET_CLASS:
            continue
        code = int(gen.plant_code or 0)
        if code:
            caps[code] = caps.get(code, 0.0) + float(gen.pmax_mw)
    return caps


def model_heat_rates(iso: str, fleet: list | None = None) -> dict[int, float]:
    """Return the ISO's CURRENT capacity-weighted eGRID heat rate per plant.

    Written to the artifact alongside the measured rate so the table records
    what it replaces and by how much — the provenance a later reader needs to
    judge the swap without re-running anything.

    Args:
        iso: ISO identifier.
        fleet: An already-loaded fleet (see :func:`provenance_fleet`). ``None``
            loads the ISO's loader-default fleet.

    Returns:
        Mapping of plant code to its capacity-weighted model heat rate.
    """
    fleet = load_fleet_from_csv(iso, get_iso_config(iso)) if fleet is None else fleet
    num: dict[int, float] = {}
    den: dict[int, float] = {}
    for gen in fleet:
        if gen.plant_group != TARGET_CLASS:
            continue
        code = int(gen.plant_code or 0)
        if not code:
            continue
        num[code] = num.get(code, 0.0) + float(gen.pmax_mw) * float(gen.heat_rate)
        den[code] = den.get(code, 0.0) + float(gen.pmax_mw)
    return {c: num[c] / den[c] for c in num if den[c] > 0}


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


def _is_cc_unit(series: pd.Series) -> pd.Series:
    """Boolean mask of rows whose CAMPD ``unitType`` is a combined cycle."""
    return (
        series.astype(str)
        .str.strip()
        .str.casefold()
        .str.startswith(CC_UNIT_TYPE_PREFIX)
    )


def _campd_cc_hours(iso: str, years: list[int], codes: set[int]) -> pd.DataFrame:
    """Return every pooled CAMPD combined-cycle hour at the ISO's own plants.

    Each state-year extract is read once and immediately narrowed to the ISO's
    own target-class plants, so a shared state file cannot leak another ISO's
    units in (rule 25 ``[R-ISO-SCOPE]``).
    """
    frames: list[pd.DataFrame] = []
    for path in sorted(UNIT_LEVEL_DIR.glob("*.parquet")):
        stem = path.stem
        if "_" not in stem:
            continue
        try:
            year = int(stem.rsplit("_", 1)[1])
        except ValueError:
            continue
        if year not in years:
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
                "unitType",
            ],
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(codes)]
        df = df[_is_cc_unit(df["unitType"])]
        if not df.empty:
            df = df.copy()
            df["year"] = year
            frames.append(df)
    if not frames:
        raise SystemExit(f"{iso}: no CAMPD combined-cycle hours for {TARGET_CLASS}")
    return pd.concat(frames, ignore_index=True)


def boundary_ratios(
    iso: str, pooled: pd.DataFrame, years: list[int]
) -> dict[int, float]:
    """Return ``{plant_code: mean CAMPD CC gross / EIA-923 CC net}``.

    THE BOUNDARY GUARD (module docstring): the identity test that decides
    whether CAMPD's gross load speaks for the whole combined cycle or only for
    its combustion turbines. The EIA-923 comparator is read through
    ``run_calibration_full._eia923_frame`` — the benchmark's OWN construction —
    so the guard tests against exactly the series the run is scored on.

    Args:
        iso: ISO identifier.
        pooled: Output of :func:`_campd_cc_hours`.
        years: The CAMPD vintages pooled.

    Returns:
        Mapping of plant code to its across-year mean ratio. A plant with no
        EIA-923 CC row in any year is absent, and is flagged downstream.
    """
    from market_sim.data import eia923

    spec = importlib.util.spec_from_file_location(
        "rcf_boundary", str(REPO / "scripts/run_calibration_full.py")
    )
    rcf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rcf)
    monthly = eia923.load_monthly_generation()

    per_year: dict[int, list[float]] = {}
    for year in years:
        frame = rcf._eia923_frame(year, monthly, iso)
        net = frame[frame["klass"] == TARGET_CLASS].set_index("plant_id")["annual_mwh"]
        gross = pooled[pooled["year"] == year].groupby("facilityId")["grossLoad"].sum()
        for code, g in gross.items():
            n = float(net.get(int(code), float("nan")))
            if np.isfinite(n) and n > 0.0:
                per_year.setdefault(int(code), []).append(float(g) / n)
    return {c: float(np.mean(v)) for c, v in per_year.items() if v}


def unit_operating_heat_rates(pooled: pd.DataFrame) -> pd.DataFrame:
    """Return one row per CAMPD combined-cycle unit with its operating rate.

    Hours are pooled across years before the screens, so a unit that barely ran
    in one year still reaches :data:`_MIN_STEADY_HOURS`.

    Args:
        pooled: Output of :func:`_campd_cc_hours`.

    Returns:
        Columns ``plant_code``, ``plant_name``, ``unit_id``, ``gross_mwh``,
        ``steady_hours``, ``cap_mw``, ``hr_gross``, ``hr_gross_hsl``.
    """
    pooled = pooled.dropna(subset=["grossLoad", "heatInput"])
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
    boundary: dict[int, float],
) -> pd.DataFrame:
    """Aggregate the per-unit operating rates to one measured row per plant.

    The plant value is GENERATION-weighted across its units: a unit that
    produced most of the plant's energy should dominate the rate the plant
    offers at. Weighting by capacity instead would let a rarely-run spare
    define the offer of a plant that runs on its other machines.

    The gross-to-net conversion is applied per unit before aggregation, using
    the unit's own plant factor (units of one plant share it), so the column
    ``heat_rate`` is directly comparable to ``model_heat_rate_egrid``.

    The flag precedence is BOUNDARY FIRST: a plant whose steam turbine is not
    metered has no combined-cycle rate to be in or out of band, so reporting
    it as a band failure would name the wrong defect.
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
        ratio = boundary.get(int(code))
        if ratio is None or not np.isfinite(ratio):
            flag = "no_eia923_comparator"
        elif ratio < _BOUNDARY_MIN:
            # The steam turbine is not in CAMPD's gross load, so hr_gross is
            # the COMBUSTION-TURBINE rate, not this plant's CC rate.
            flag = "steam_not_metered"
        elif ratio > _BOUNDARY_MAX:
            flag = "boundary_above_band"
        elif hr_net < _HR_MIN_NET:
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
                # THE BOUNDARY GUARD's own measurement, always written so a
                # reader can see why a plant was refused without re-deriving.
                "boundary_gross_over_net": (
                    round(float(ratio), 4) if ratio is not None else float("nan")
                ),
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
        "(data/raw/campd-unit-level), unitType prefix "
        f"'{CC_UNIT_TYPE_PREFIX}' (case-folded, so the commissioning variants "
        "are caught); per unit heat_rate = sum(heatInput)/sum(grossLoad) over "
        f"hours with opTime >= {_MIN_OPTIME} whose OWN implied rate is inside "
        f"the physical band [{_HR_MIN_GROSS}, {_HR_MAX_GROSS}] MMBtu per gross "
        f"MWh (>= {_MIN_STEADY_HOURS} such qualifying hours), converted to a "
        "NET basis by the committed parasitic factor "
        "(parasitic_load_factors.parquet, the same map the benchmark's net "
        "actual uses; class default "
        f"{campd.DEFAULT_PARASITIC_LOAD_PCT[TARGET_CLASS]}); plant value is "
        "the generation-weighted mean across its units. heat_rate_gross_hsl "
        f"is REPORTED ONLY (the >= p{_HSL_PCTILE} near-HSL window) and is "
        "never applied. THE BOUNDARY GUARD refuses any plant whose pooled "
        "CAMPD CC gross over EIA-923 CC net (the benchmark's own "
        f"_eia923_frame) falls outside [{_BOUNDARY_MIN}, {_BOUNDARY_MAX}] — "
        "its steam turbine is not in the meter, so the ratio is the "
        f"combustion-turbine rate. The net band [{_HR_MIN_NET}, {_HR_MAX_NET}] "
        "also flags the plant aggregate; only flag=='ok' rows are applied."
    )
    return out


def main(argv: list[str] | None = None) -> int:
    """Derive and write the measured combined-cycle operating-rate artifact."""
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
    for flag, helptext in (
        ("egrid-family-heat-rates", "the ONE provenance flag that can reach a CC row"),
        ("measured-ct-heat-rates", "PROVENANCE ONLY (cannot reach a CC row)"),
        ("measured-st-heat-rates", "PROVENANCE ONLY (cannot reach a CC row)"),
        ("measured-coal-heat-rates", "PROVENANCE ONLY (cannot reach a CC row)"),
    ):
        parser.add_argument(
            f"--{flag}",
            action="store_true",
            help=(
                f"Load the PROVENANCE fleet with ScenarioConfig."
                f"{flag.replace('-', '_')} armed: {helptext}. It moves "
                "model_heat_rate_egrid and nothing that is applied"
            ),
        )
    args = parser.parse_args(argv)

    iso = args.iso.upper()
    years = sorted(args.years)
    fleet = provenance_fleet(
        iso,
        egrid_family_heat_rates=args.egrid_family_heat_rates,
        measured_ct_heat_rates=args.measured_ct_heat_rates,
        measured_st_heat_rates=args.measured_st_heat_rates,
        measured_coal_heat_rates=args.measured_coal_heat_rates,
    )
    caps = target_plant_codes(iso, fleet)
    if not caps:
        raise SystemExit(f"{iso}: model fleet carries no {TARGET_CLASS} generator")
    print(f"{iso}: {len(caps)} {TARGET_CLASS} plants, {sum(caps.values()):,.1f} MW")

    pooled = _campd_cc_hours(iso, years, set(caps))
    boundary = boundary_ratios(iso, pooled, years)
    units = unit_operating_heat_rates(pooled)
    if units.empty:
        raise SystemExit(f"{iso}: no unit cleared the steady-hour screens")
    table = plant_table(
        units,
        iso,
        years,
        caps,
        model_heat_rates(iso, fleet),
        parasitic_factors(),
        boundary,
    )

    out = (
        Path(args.out) if args.out else PROCESSED_DIR / f"campd_cc_heat_rates_{iso}.csv"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out, index=False)
    ok = table[table["flag"] == "ok"]
    covered = float(ok["class_capacity_mw"].sum())
    total = float(sum(caps.values()))
    print(f"wrote {out}  ({len(table)} plants, {len(ok)} applied)")
    print(
        f"  applied capacity {covered:,.1f} of {total:,.1f} MW "
        f"({100.0 * covered / total:.1f} %)"
    )
    for _, r in table.iterrows():
        mark = " " if r["flag"] == "ok" else "*"
        print(
            f"  {mark}{int(r['plant_code']):>6d} {str(r['plant_name'])[:26]:26s} "
            f"model {r['model_heat_rate_egrid']:7.4f} -> meas {r['heat_rate']:7.4f} "
            f"(x{r['model_over_measured']:.4f})  bnd {r['boundary_gross_over_net']:.3f}"
            f"  {r['flag']}"
        )
    if args.detail:
        det = out.with_name(out.stem + "_units.csv")
        units.sort_values(["plant_code", "unit_id"]).to_csv(det, index=False)
        print(f"wrote {det}  ({len(units)} units)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
