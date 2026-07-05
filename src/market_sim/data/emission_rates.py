"""Forward per-plant CO2-rate estimator from measured CAMPD history.

For an existing unit, the forecast-year CO2 intensity is *derived from* its own
multi-year measured CAMPD performance rather than a frozen pooled value or a
generic heat-rate constant — a rule-13-admissible measured input (it regenerates
from forward drivers and responds to changed operation). The design and its
empirical validation are in
``docs/handoffs/emissions-co2-rate-plan-2026-07.md`` (§2); the free parameters
live in :mod:`market_sim.config.constants` (``CO2_RATE_*``), chosen once from the
leave-one-year-out harness ``scripts/loyo_co2_rates.py`` and frozen against
backcast residuals (CLAUDE.md rules 23/24).

:func:`forward_plant_co2_rate` composes four pieces:

* **(a) gen-weighted trailing average** of annual net CO2 intensity over the
  available history (the base — beats simple/recency means, plan §2.2);
* **(b) envelope-gated nearest-neighbor conditioning** on the model's simulated
  operation for the target year — fires only when that operation leaves the
  plant's historical envelope, replacing the base with the nearest historical
  year's rate (plan §2.1 step 2);
* **(c) unit-composition mask** — the per-year plant rate is aggregated over
  only the CEMS units present in the target-year fleet, so a retired unit (or a
  Parish-style coal+gas facility whose bins split by fuel) gets a forward rate
  from the surviving/matching units, not the blended facility rate (plan §2.1
  step 3 — this replaces the old mixed-plant exclusion);
* **(d) class-distribution fallback** — CEMS-uncovered plants and new entrants
  get the gen-weighted class (plant_group × fuel) median rate (plan §2.1 step 4).

Mode policy (resolves EM-3): backcast years consume the *target year's* measured
rate directly (a reproducible physical input); forecast years consume this
estimator. The merit-order rate is the base (a); the conditioned refinement (b)
is applied post-solve for reporting, so there is no fixed-point iteration.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from market_sim.config import constants

# Number of CF-duration bands in an operating-point descriptor (0-0.1, …, 0.9-1).
CF_BANDS: int = 10


@dataclass(frozen=True)
class OperatingPoint:
    """A plant-year operating descriptor for nearest-neighbor conditioning.

    ``gen_mwh`` and ``starts`` are raw annual quantities (normalized internally
    against the plant's own history); ``cf_band`` is the 10-bin CF-duration
    histogram normalized to sum 1.
    """

    gen_mwh: float
    starts: float
    cf_band: np.ndarray

    def vector(self, gen_norm: float, starts_norm: float) -> np.ndarray:
        """Return the normalized descriptor [gen/gen_norm, starts/starts_norm, cf...]."""
        g = self.gen_mwh / gen_norm if gen_norm > 0 else 0.0
        s = self.starts / starts_norm if starts_norm > 0 else 0.0
        cf = np.asarray(self.cf_band, dtype=float)
        cf = cf / cf.sum() if cf.sum() > 0 else np.zeros(CF_BANDS)
        return np.concatenate([[g, s], cf])


@dataclass
class PlantHistory:
    """One plant's measured CAMPD history, at unit-year grain.

    Attributes
    ----------
    unit_years:
        Frame with columns ``unit_id, year, net_mwh, co2_kg`` (one row per CEMS
        unit-year). The unit-composition mask filters on ``unit_id``.
    ops:
        ``{year: OperatingPoint}`` plant-level operating descriptors (for the
        NN gate). Optional — absent years simply cannot be NN-matched.
    group, fuel:
        Plant class labels, for the class-distribution fallback.
    """

    unit_years: pd.DataFrame
    ops: dict[int, OperatingPoint] = field(default_factory=dict)
    group: str = ""
    fuel: str = ""


@dataclass(frozen=True)
class RateResult:
    """Estimator output: the forward net CO2 rate (kg/MWh) and how it was set."""

    rate_kg_per_mwh_net: float
    method: str  # "trailing_avg" | "nn_conditioned" | "class_fallback"
    n_years: int


def _masked_year_rates(
    unit_years: pd.DataFrame, fleet_units: set[str] | None
) -> pd.DataFrame:
    """Aggregate unit-year rows to per-year plant totals over matching units.

    ``fleet_units`` restricts to the units present in the target-year fleet (the
    composition mask); ``None`` keeps every unit. Returns a frame indexed by
    ``year`` with ``net_mwh`` and ``co2_kg`` sums, dropping years with no net
    generation (rate undefined).
    """
    df = unit_years
    if fleet_units is not None:
        df = df[df["unit_id"].astype(str).isin({str(u) for u in fleet_units})]
    if df.empty:
        return pd.DataFrame(columns=["year", "net_mwh", "co2_kg"]).set_index("year")
    agg = df.groupby("year", observed=True)[["net_mwh", "co2_kg"]].sum()
    return agg[agg["net_mwh"] > 0.0]


def _trailing(agg: pd.DataFrame, window: int) -> tuple[float, int]:
    """Return ``(gen_weighted_rate, n_years)`` over the trailing ``window``.

    ``window <= 0`` uses all available years. Gen-weighting sums CO2 and net
    MWh across years before dividing, so high-output years dominate.
    """
    years = sorted(agg.index)
    if window and window > 0:
        years = years[-window:]
    sub = agg.loc[years]
    net = float(sub["net_mwh"].sum())
    co2 = float(sub["co2_kg"].sum())
    return (co2 / net if net > 0 else 0.0), len(years)


def _envelope_l1(target: np.ndarray, points: list[np.ndarray]) -> float:
    """Return the L1 distance from ``target`` to the historical box envelope.

    Distance is the summed per-dimension overshoot beyond the [min, max] range
    of the historical ``points`` (0 when the target is inside the box on every
    dimension). This is the gate quantity compared against
    ``CO2_RATE_ENVELOPE_GATE_L1``.
    """
    if not points:
        return np.inf
    stack = np.vstack(points)
    lo = stack.min(axis=0)
    hi = stack.max(axis=0)
    below = np.clip(lo - target, 0.0, None)
    above = np.clip(target - hi, 0.0, None)
    return float((below + above).sum())


def forward_plant_co2_rate(
    history: PlantHistory,
    sim_op: OperatingPoint | None,
    fleet_units: set[str] | None,
    *,
    class_median: float | None = None,
    window: int | None = None,
    envelope_gate_l1: float | None = None,
    conditioning_enabled: bool | None = None,
) -> RateResult:
    """Return the forward net CO2 rate (kg/MWh) for one plant.

    Parameters
    ----------
    history:
        The plant's measured CAMPD history (:class:`PlantHistory`).
    sim_op:
        The model's simulated operating point for the target forecast year, or
        ``None`` to skip conditioning (returns the pure base).
    fleet_units:
        Unit ids present in the target-year fleet (composition mask), or ``None``
        to use every historical unit.
    class_median:
        The plant's class (group × fuel) gen-weighted median rate, used when the
        masked history is empty (uncovered plant / new entrant). ``None`` and no
        history yields a zero rate flagged ``class_fallback``.
    window, envelope_gate_l1, conditioning_enabled:
        Overrides for the corresponding ``CO2_RATE_*`` constants (the harness
        passes sweep values; production leaves them ``None`` to read the frozen
        constants).

    Returns
    -------
    RateResult
    """
    window = constants.CO2_RATE_TRAILING_WINDOW_YEARS if window is None else window
    gate = (
        constants.CO2_RATE_ENVELOPE_GATE_L1
        if envelope_gate_l1 is None
        else envelope_gate_l1
    )
    cond_on = (
        constants.CO2_RATE_CONDITIONING_ENABLED
        if conditioning_enabled is None
        else conditioning_enabled
    )

    agg = _masked_year_rates(history.unit_years, fleet_units)

    # (d) Class fallback — no measured history for the fleet's unit composition.
    if agg.empty:
        return RateResult(float(class_median or 0.0), "class_fallback", 0)

    # (a) Gen-weighted trailing average — the base and the merit-order rate.
    base, n_years = _trailing(agg, window)

    # (b) Envelope-gated nearest-neighbor conditioning (reporting refinement).
    if cond_on and sim_op is not None and history.ops:
        hist_years = [y for y in agg.index if y in history.ops]
        pts = [history.ops[y] for y in hist_years]
        if pts:
            gen_norm = max((p.gen_mwh for p in pts), default=0.0)
            starts_norm = max((p.starts for p in pts), default=0.0)
            hist_vecs = [p.vector(gen_norm, starts_norm) for p in pts]
            target_vec = sim_op.vector(gen_norm, starts_norm)
            if _envelope_l1(target_vec, hist_vecs) > gate:
                # Outside the envelope: adopt the nearest historical year's rate.
                dists = [float(np.abs(target_vec - v).sum()) for v in hist_vecs]
                nn_year = hist_years[int(np.argmin(dists))]
                row = agg.loc[nn_year]
                nn_rate = float(row["co2_kg"] / row["net_mwh"])
                return RateResult(nn_rate, "nn_conditioned", n_years)

    return RateResult(base, "trailing_avg", n_years)


def fuel_class(label: str) -> str:
    """Map a CAMPD ``primary_fuel`` or a model ``fuel_type`` to a coarse class.

    The composition mask matches CEMS units to dispatch bins by this coarse
    class — so a Parish-style coal+gas facility's coal units feed its coal bin
    and its gas units feed its gas bin, giving separate measured rates.
    """
    s = str(label).lower()
    if "coal" in s or "lignite" in s or "pet" in s and "coke" in s:
        return "coal"
    if "gas" in s or "lng" in s:
        return "gas"
    if "oil" in s or "diesel" in s or "petroleum" in s or "distillate" in s:
        return "oil"
    if "wood" in s or "biomass" in s:
        return "biomass"
    return "other"


# Measured pollutant mass columns in the v2 artifact, keyed by pollutant name.
# The rate for each is Σ mass_kg / Σ net_mwh over the composition-masked units,
# converted kg/MWh → tonnes/MWh at the boundary (the model's canonical unit for
# every emission rate — CO2, NOx, SO2 alike).
_POLLUTANT_MASS_COL: dict[str, str] = {
    "co2": "co2_kg",
    "nox": "nox_kg",
    "so2": "so2_kg",
}


def measured_plant_rates(
    v2: pd.DataFrame,
    iso: str,
    target_year: int,
    mode: str,
    *,
    window: int | None = None,
    pollutant: str = "co2",
) -> dict[tuple[int, str], float]:
    """Return ``{(plant_id, fuel_class): rate_tonnes_per_mwh_net}`` for a pollutant.

    Mode-aware source (resolves EM-3): a **backcast** year consumes that year's
    own measured rate; a **forecast** year consumes the estimator base — the
    gen-weighted trailing average over the available measured history. Rates are
    aggregated over CEMS units of the same coarse fuel class (the composition
    mask), so retiring or splitting a unit moves the rate. Built from the v2
    artifact (``derive_plant_emissions_v2.py``); returns tonnes/MWh net.

    ``pollutant`` selects the mass column (``"co2"`` / ``"nox"`` / ``"so2"``);
    the mode/window/composition-mask policy is identical for all three (NOx/SO2
    ride the same path as CO2 — plan §5 R7 / §7). A pollutant whose mass column
    is absent (e.g. a legacy CO2-only v2) yields ``{}``.
    """
    mass_col = _POLLUTANT_MASS_COL[str(pollutant).lower()]
    window = constants.CO2_RATE_TRAILING_WINDOW_YEARS if window is None else window
    df = v2[v2["iso"].astype(str) == str(iso)].copy()
    if df.empty or mass_col not in df.columns:
        return {}
    if str(mode).lower() == "backcast":
        df = df[df["year"] == int(target_year)]
    else:
        years = sorted(df["year"].unique())
        if window and window > 0:
            years = years[-window:]
        df = df[df["year"].isin(years)]
    if df.empty:
        return {}
    df["fuel_class"] = df["primary_fuel"].map(fuel_class)
    out: dict[tuple[int, str], float] = {}
    grouped = df.groupby(["plant_id", "fuel_class"], observed=True)[
        [mass_col, "net_mwh"]
    ]
    for (plant_id, fc), agg in grouped.sum().iterrows():
        net = float(agg["net_mwh"])
        if net > 0:
            out[(int(plant_id), str(fc))] = float(agg[mass_col]) / net / 1000.0
    return out


def class_median_rates(
    annual: pd.DataFrame,
    *,
    percentile: float | None = None,
    pollutant: str = "co2",
) -> dict[tuple[str, str], float]:
    """Return ``{(group, fuel): rate_kg_per_mwh_net}`` class-distribution rates.

    Built from the same per-plant-year CAMPD observations the estimator uses:
    each plant-year contributes its net pollutant intensity, weighted by net
    MWh, and the class rate is the (default gen-weighted median) percentile of
    that distribution. Feeds the entrant / uncovered-plant fallback (plan §2.1
    step 4), replacing generic ``heat_rate × FUEL_*_FACTOR`` constants — never a
    generic heat-rate constant (CLAUDE.md rule 3/13).

    ``pollutant`` selects the mass column (``"co2"`` / ``"nox"`` / ``"so2"``);
    the gen-weighted-median policy and the shared
    ``CO2_RATE_CLASS_MEDIAN_PERCENTILE`` are identical across pollutants (NOx/SO2
    mirror CO2 — plan §5 R7). ``annual`` needs columns ``group, fuel, net_mwh``
    and the selected ``<pollutant>_kg`` (one row per plant-year). Years/rows with
    no net generation are dropped.
    """
    mass_col = _POLLUTANT_MASS_COL[str(pollutant).lower()]
    pct = (
        constants.CO2_RATE_CLASS_MEDIAN_PERCENTILE if percentile is None else percentile
    )
    df = annual[annual["net_mwh"] > 0.0].copy()
    df["rate"] = df[mass_col] / df["net_mwh"]
    out: dict[tuple[str, str], float] = {}
    for (group, fuel), sub in df.groupby(["group", "fuel"], observed=True):
        out[(str(group), str(fuel))] = _weighted_percentile(
            sub["rate"].to_numpy(), sub["net_mwh"].to_numpy(), pct
        )
    return out


def _weighted_percentile(
    values: np.ndarray, weights: np.ndarray, percentile: float
) -> float:
    """Return the weight-interpolated ``percentile`` of ``values``.

    A gen-weighted percentile: sorts by value, accumulates the weight fraction,
    and interpolates at ``percentile/100``. Falls back to the unweighted value
    when all weights are zero.
    """
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    order = np.argsort(values)
    values, weights = values[order], weights[order]
    total = weights.sum()
    if total <= 0:
        return float(np.percentile(values, percentile)) if values.size else 0.0
    cum = np.cumsum(weights) - 0.5 * weights
    cum /= total
    return float(np.interp(percentile / 100.0, cum, values))
