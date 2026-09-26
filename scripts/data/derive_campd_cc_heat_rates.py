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
sys.path.insert(0, str(REPO))

from market_sim.config.paths import (  # noqa: E402
    EIA_923_GENERATION_FUEL_PATH,
    PROCESSED_DIR,
    RAW_DIR,
)
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

#: THE GROSS-NET IDENTITY (R-CAISO-2, 2026-09-25). Gross generation is net
#: generation PLUS station service, so a plant whose whole CC output is in
#: CAMPD's meter cannot read ``gross/net < 1`` — the identity, not a fit. A
#: ratio in ``[_BOUNDARY_MIN, 1.0)`` therefore means CAMPD's gross load holds
#: only PART of the plant's output (one steam train of several dropped from the
#: meter), and ``heatInput / grossLoad`` over-states the plant's rate by the
#: missing share. The ``[0.75, 1.00]`` "empty gap" claim above was measured on
#: SOCO, which has no row there; CAISO does — Pastoria 55656 reads 1.029 in
#: 2019 and 0.927-0.946 in 2020-2025 with its output unchanged, because from
#: 2020 its CT001/CT002 gross stopped carrying their shared steam turbine (per
#: unit gross rate 7.1 -> 8.8 while CT004 holds 7.45). Such a row is flagged
#: and NOT applied, falling back like every other refused row (pooled row,
#: else eGRID). Physics-fixed ex ante, never swept (rules 14 / 21 / 23).
_GROSS_NET_IDENTITY_MIN: float = 1.0

#: THE EIA-923 IDENTITY FALLBACK (R-CAISO-3, 2026-09-25). A row refused by
#: the gross-net identity above has a CEMS record that is internally
#: inconsistent with the owner's own filing, so the measured rate that
#: replaces it is the one built ENTIRELY from that filing: EIA-923 total fuel
#: consumption / EIA-923 net generation over the plant's combined-cycle prime
#: movers (data/raw/eia-923-generation-fuel), numerator and denominator on one
#: boundary. The former terminal, eGRID, is CEMS heat input / EIA-923 net —
#: the same refused CEMS record in the numerator. Measured on Pastoria 55656:
#: CEMS heat input reads x1.090-1.093 of EIA-923 fuel in every year 2020-2025
#: (x1.041 in 2019; all three units step together in 2020, CT004 7.14 -> 7.50
#: gross with no steam-turbine change), so eGRID gives 7.69 while EIA-923 fuel
#: / net holds at 7.04-7.08. Applies ONLY to rows already flagged
#: ``gross_below_net``; no threshold, no parameter; the physical net band still
#: binds. Written with flag ``eia923_identity``, which the model applies
#: (data/fleet/campd_bins._APPLIED_MEASURED_FLAGS). Rules 14 / 19 / 23.
_EIA923_IDENTITY_FLAG: str = "eia923_identity"
_EIA923_IDENTITY_REFUSALS: frozenset[str] = frozenset({"gross_below_net"})
_CC_PRIME_MOVERS: tuple[str, ...] = ("CT", "CA", "CS")


def eia923_identity_rates(
    codes: set[int], years: list[int], path: Path = EIA_923_GENERATION_FUEL_PATH
) -> dict[int, dict[int, float]]:
    """Return ``{year: {plant: EIA-923 fuel / EIA-923 net}}``; ``year 0`` is pooled.

    Sums total fuel consumption (MMBtu) and net generation (MWh) over the
    plant's combined-cycle prime movers (``CT``/``CA``/``CS``) in the committed
    EIA-923 Page 1 intake. A plant-year with no positive fuel or generation is
    omitted. Empty when the intake is absent (the derive then behaves exactly
    as before this fallback existed).
    """
    if not Path(path).exists():
        return {}
    frame = pd.read_csv(path)
    frame = frame[
        frame["plant_id"].isin(codes)
        & frame["prime_mover"].isin(_CC_PRIME_MOVERS)
        & frame["year"].isin(years)
    ]
    cols = ["total_fuel_mmbtu", "net_generation_mwh"]
    out: dict[int, dict[int, float]] = {}
    for (year, code), r in frame.groupby(["year", "plant_id"])[cols].sum().iterrows():
        if r["total_fuel_mmbtu"] > 0.0 and r["net_generation_mwh"] > 0.0:
            out.setdefault(int(year), {})[int(code)] = float(
                r["total_fuel_mmbtu"] / r["net_generation_mwh"]
            )
    for code, r in frame.groupby("plant_id")[cols].sum().iterrows():
        if r["total_fuel_mmbtu"] > 0.0 and r["net_generation_mwh"] > 0.0:
            out.setdefault(0, {})[int(code)] = float(
                r["total_fuel_mmbtu"] / r["net_generation_mwh"]
            )
    return out


def apply_eia923_identity(
    table: pd.DataFrame, rates: dict[int, dict[int, float]]
) -> pd.DataFrame:
    """Replace refused gross-net rows with the EIA-923 identity rate.

    Writes ``heat_rate_eia923_identity`` on every row (provenance) and, for a
    row whose flag is in :data:`_EIA923_IDENTITY_REFUSALS` and whose identity
    rate is inside the net physical band, sets ``heat_rate`` to that rate and
    ``flag`` to :data:`_EIA923_IDENTITY_FLAG`. Every other row is unchanged.
    """
    table = table.copy()
    ident = [
        rates.get(int(y), {}).get(int(c), float("nan"))
        for y, c in zip(table["year"], table["plant_code"])
    ]
    table["heat_rate_eia923_identity"] = np.round(np.asarray(ident, dtype=float), 4)
    swap = table["flag"].isin(_EIA923_IDENTITY_REFUSALS) & table[
        "heat_rate_eia923_identity"
    ].between(_HR_MIN_NET, _HR_MAX_NET)
    table.loc[swap, "heat_rate"] = table.loc[swap, "heat_rate_eia923_identity"]
    table.loc[swap, "model_over_measured"] = np.round(
        table.loc[swap, "model_heat_rate_egrid"] / table.loc[swap, "heat_rate"], 4
    )
    table.loc[swap, "flag"] = _EIA923_IDENTITY_FLAG
    return table


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
        # CEMS-to-EIA split-plant routing (campd.CAMPD_UNIT_PLANT_REMAP): a
        # repowered CC whose CTs still file CEMS under the legacy boiler ORIS
        # (El Segundo 330 -> 57901, Alamitos 315 -> 62115, Huntington Beach
        # 335 -> 62116, Astoria Energy II 55375 -> 57664) is re-keyed to the
        # EIA plant it belongs to BEFORE the fleet filter, exactly as the
        # outage and emissions derives already do. Without it El Segundo
        # (510 MW, no eGRID row in any vintage) matched no fleet plant and
        # stayed at the HEAT_RATE_BINS class table (R-CAISO phase 0,
        # docs/handoffs/r-caiso/PRECOMMIT-r-caiso-2026-09-24.md §2).
        fac = df["facilityId"].fillna(-1).astype(int)
        uid = df["unitId"].astype(str)
        at_split = fac.isin(campd.CAMPD_SPLIT_FACILITIES)
        if at_split.any():
            df.loc[at_split, "facilityId"] = [
                campd.CAMPD_UNIT_PLANT_REMAP.get((f, u), f)
                for f, u in zip(fac[at_split], uid[at_split])
            ]
        df = df[df["facilityId"].isin(codes)]
        df = df[_is_cc_unit(df["unitType"])]
        if not df.empty:
            df = df.copy()
            df["year"] = year
            frames.append(df)
    if not frames:
        raise SystemExit(f"{iso}: no CAMPD combined-cycle hours for {TARGET_CLASS}")
    return pd.concat(frames, ignore_index=True)


def boundary_ratios_by_year(
    iso: str, pooled: pd.DataFrame, years: list[int]
) -> dict[int, dict[int, float]]:
    """Return ``{year: {plant_code: CAMPD CC gross / EIA-923 CC net}}``.

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
        One mapping per year; a plant with no EIA-923 CC row in a year is
        absent from that year's mapping.
    """
    from market_sim.data import eia923

    spec = importlib.util.spec_from_file_location(
        "rcf_boundary", str(REPO / "scripts/run_calibration_full.py")
    )
    rcf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rcf)
    monthly = eia923.load_monthly_generation()

    out: dict[int, dict[int, float]] = {}
    for year in years:
        frame = rcf._eia923_frame(year, monthly, iso)
        net = frame[frame["klass"] == TARGET_CLASS].set_index("plant_id")["annual_mwh"]
        gross = pooled[pooled["year"] == year].groupby("facilityId")["grossLoad"].sum()
        for code, g in gross.items():
            n = float(net.get(int(code), float("nan")))
            if np.isfinite(n) and n > 0.0:
                out.setdefault(int(year), {})[int(code)] = float(g) / n
    return out


def boundary_ratios(by_year: dict[int, dict[int, float]]) -> dict[int, float]:
    """Return ``{plant_code: across-year mean ratio}`` from the per-year table.

    The pooled row's guard. A plant with no EIA-923 CC row in any year is
    absent, and is flagged downstream.
    """
    per_code: dict[int, list[float]] = {}
    for mapping in by_year.values():
        for code, ratio in mapping.items():
            per_code.setdefault(code, []).append(ratio)
    return {c: float(np.mean(v)) for c, v in per_code.items() if v}


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
        elif ratio < _GROSS_NET_IDENTITY_MIN:
            # Gross below net is impossible for a fully metered plant: part
            # of the output is missing from CAMPD's gross load (see the
            # constant), so hr_gross over-states the plant's CC rate.
            flag = "gross_below_net"
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
        default=list(BACKCAST_YEARS),
        help="CAMPD vintages to pool and slice (default 2019-2025)",
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
    # F1 D4: the population is the UNION of the backcast fleets over every
    # year (year-matched vintage + retiree channel), so a combined cycle that
    # retired before 2023 is covered; the provenance recipe loads per year.
    fleets = backcast_fleets(
        iso,
        years,
        egrid_family_heat_rates=args.egrid_family_heat_rates,
        measured_ct_heat_rates=args.measured_ct_heat_rates,
        measured_st_heat_rates=args.measured_st_heat_rates,
        measured_coal_heat_rates=args.measured_coal_heat_rates,
    )
    union = union_fleet(fleets)
    caps = class_capacity(union, TARGET_CLASS)
    if not caps:
        raise SystemExit(f"{iso}: model fleet carries no {TARGET_CLASS} generator")
    print(f"{iso}: {len(caps)} {TARGET_CLASS} plants, {sum(caps.values()):,.1f} MW")

    pooled = _campd_cc_hours(iso, years, set(caps))
    by_year = boundary_ratios_by_year(iso, pooled, years)
    units = unit_operating_heat_rates(pooled)
    if units.empty:
        raise SystemExit(f"{iso}: no unit cleared the steady-hour screens")
    factors = parasitic_factors()
    table = plant_table(
        units,
        iso,
        years,
        caps,
        class_heat_rates(union, TARGET_CLASS),
        factors,
        boundary_ratios(by_year),
    )

    def _year_table(year: int) -> pd.DataFrame | None:
        # The SAME estimator on year Y's hours alone (the unchanged
        # _MIN_STEADY_HOURS gate), guarded by year Y's OWN boundary ratio.
        year_units = unit_operating_heat_rates(pooled[pooled["year"] == year])
        if year_units.empty:
            return None
        return plant_table(
            year_units,
            iso,
            [year],
            caps,
            class_heat_rates(fleets.get(year, []), TARGET_CLASS),
            factors,
            by_year.get(year, {}),
        )

    table = stack_year_tables(table, per_year_tables(years, _year_table))
    table = apply_eia923_identity(table, eia923_identity_rates(set(caps), years))

    out = (
        Path(args.out) if args.out else PROCESSED_DIR / f"campd_cc_heat_rates_{iso}.csv"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out, index=False)
    print(
        "  per-year rows: "
        + ", ".join(
            f"{y}:{int((table['year'] == y).sum())}" for y in sorted(set(table["year"]))
        )
    )
    table = table[table["year"] == 0]
    ok = table[table["flag"].isin(("ok", _EIA923_IDENTITY_FLAG))]
    covered = float(ok["class_capacity_mw"].sum())
    total = float(sum(caps.values()))
    print(f"wrote {out}  ({len(table)} plants, {len(ok)} applied)")
    print(
        f"  applied capacity {covered:,.1f} of {total:,.1f} MW "
        f"({100.0 * covered / total:.1f} %)"
    )
    for _, r in table.iterrows():
        mark = " " if r["flag"] in ("ok", _EIA923_IDENTITY_FLAG) else "*"
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
