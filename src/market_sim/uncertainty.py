"""Multivariate forecast-uncertainty sampler (PB-2, probability-bounds program).

The weather-year ensemble (:mod:`market_sim.ensemble`) propagates one source of
forecast risk -- the weather shape -- across three draws. That leaves gas price,
load growth, technology cost and the policy path all pinned at their "mid"
selectors, so any "+/-N%" emissions headline carries no confidence statement.
This module turns the ensemble's member axis into a *multivariate draw* over the
input uncertainty, so the ensemble reports a genuine parametric probability band.

Design source: ``docs/handoffs/probability-bounds-plan-2026-07.md`` §2 (the
parametric band). This module owns §2.1-§2.5:

* **What is sampled** (§2.1): three continuous dims -- gas price *level*
  (``gas_price_factor``), load growth (``demand_growth_percentile``) and tech
  cost (``tech_cost_percentile``) -- plus three discrete dims -- weather year,
  hydro year and policy bundle. Every one is an existing PB-1 ``ScenarioConfig``
  lever, neutral at its default, so a draw is admissible forecast input (it
  regenerates for a forward year and responds to changed conditions), never a
  measured outcome fed back to the model (CLAUDE.md rules 1/11/13).
* **The gas marginal** (§2.2): a lognormal level shock ``factor = exp(sigma*z)``
  with a two-anchor ``sigma`` schedule -- front from NYMEX/STEO implied vol, back
  from the AEO low/high cases as the 2050 P10/P90 -- floored at the AEO-case
  spread so the band never narrows below the deterministic scenario range. One
  ``z`` per draw is a perfectly persistent path shock (assumption A-7).
* **The correlation structure** (§2.3): a Gaussian copula whose target rank
  (Spearman) correlations are stated explicitly in the spec, converted to Pearson
  by ``r_P = 2*sin(pi*rho_S/6)`` and induced with a Cholesky factor.
* **The draw count and estimator** (§2.4): Latin-hypercube stratification; the
  published quantiles use numpy's Hyndman-Fan type-7 linear interpolation with a
  bootstrap CI attached (band machinery lives in :mod:`market_sim.ensemble`).

The public surface is three pure functions and their dataclasses:
:func:`sample_draws` (I/O-free, fully unit-testable), :func:`draw_to_config`, and
:meth:`UncertaintySpec.from_yaml`. No solves happen here.

CLAUDE.md rule 2 (no Python loops over hours) does not apply -- there are no
8760-hour arrays here; the sampling is over draws, and every array op is
vectorised across the ``n`` draws at once.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import norm, qmc

from market_sim.config.constants import END_YEAR, HENRY_HUB_TRAJECTORIES, START_YEAR
from market_sim.config.scenarios import ScenarioConfig

# The continuous dims carry a Gaussian-copula correlation structure (§2.3); the
# discrete dims draw independently through weighted bins (§2.1). Ordering is the
# contract for the Spearman/Pearson matrices and the LHS column layout, so it is
# frozen here and never re-derived from a dict iteration order.
CONTINUOUS_DIMS: tuple[str, ...] = ("gas", "load", "tech")
DISCRETE_DIMS: tuple[str, ...] = ("weather", "hydro", "policy")

# Phi^-1(0.9): the standard-normal quantile that maps the AEO low/high cases onto
# the P10/P90 of the gas marginal (§2.2, assumption A-1).
_Z90: float = float(norm.ppf(0.9))


@dataclass(frozen=True)
class GasMarginal:
    """Parameters of the lognormal gas-price level shock (plan §2.2).

    The shock is ``gas_price_factor = exp(sigma_ref * z)`` with a single
    standard-normal ``z`` per draw (a persistent path shock, A-7). ``sigma_ref``
    is the maximum over the forecast horizon of a two-anchor schedule: flat at
    ``sigma_front`` across ``front_year_start..front_year_end`` (NYMEX/STEO
    near-term implied vol), linearly interpolated to ``sigma_back`` at
    ``back_year`` (AEO low/high as the 2050 P10/P90), and -- when
    ``floor_to_aeo`` -- floored each year at the AEO-case-implied spread so the
    parametric band never narrows below the deterministic scenario range.

    Taking the horizon max collapses the year-varying schedule onto the single
    scalar ``gas_price_factor`` lever (the level shock is applied identically to
    every forecast year, PB-1) while guaranteeing the never-narrow-below-range
    property holds in *every* year -- the conservative (widest) reading, matching
    A-7. The full year-by-year schedule is still recorded in the sampler metadata
    for audit.
    """

    sigma_front: float
    sigma_back: float
    front_year_start: int = 2026
    front_year_end: int = 2028
    back_year: int = 2050
    floor_to_aeo: bool = True
    low_path: str = "low"
    mid_path: str = "mid"
    high_path: str = "high"

    def sigma_schedule(self) -> dict[int, float]:
        """Return the per-year gas sigma over ``START_YEAR..END_YEAR``.

        Returns:
            A dict mapping each forecast year to its ``sigma_y`` (front-flat,
            interpolated to the back anchor, AEO-floored when enabled).
        """
        return {y: self._sigma_year(y) for y in range(START_YEAR, END_YEAR + 1)}

    def sigma_reference(self) -> float:
        """Return the single scalar sigma applied to ``gas_price_factor``.

        The horizon maximum of :meth:`sigma_schedule`; see the class docstring
        for why the schedule is collapsed to its max.
        """
        return max(self.sigma_schedule().values())

    def _sigma_year(self, year: int) -> float:
        """Return ``sigma_y`` for one forecast year (schedule + AEO floor)."""
        if year <= self.front_year_end:
            sigma = self.sigma_front
        elif year >= self.back_year:
            sigma = self.sigma_back
        else:
            frac = (year - self.front_year_end) / (self.back_year - self.front_year_end)
            sigma = self.sigma_front + (self.sigma_back - self.sigma_front) * frac
        if self.floor_to_aeo:
            sigma = max(sigma, self._aeo_floor(year))
        return sigma

    def _aeo_floor(self, year: int) -> float:
        """Return the AEO-case-implied sigma floor for ``year`` (§2.2, A-1).

        Treats the AEO low/high Henry Hub cases as the P10/P90 of the year's
        marginal and returns the wider of the two implied half-spreads, so the
        floor covers the whole scenario range. Years past the trajectory table
        reuse its final entry (the table already runs to ``END_YEAR``).
        """
        low = _henry_hub(self.low_path, year)
        mid = _henry_hub(self.mid_path, year)
        high = _henry_hub(self.high_path, year)
        up = math.log(high / mid) / _Z90
        down = math.log(mid / low) / _Z90
        return max(up, down)


@dataclass(frozen=True)
class UncertaintySpec:
    """A committed, cited specification of the forecast-uncertainty sampler.

    All of §2.1-§2.4's inputs in one immutable object: the gas marginal, the
    Spearman rank-correlation matrix over :data:`CONTINUOUS_DIMS`, the
    probability weights for each discrete dim, and the draw count / seed. Loaded
    from a YAML file (:meth:`from_yaml`) so every number is version-controlled
    and cited (rule 5); echoed verbatim into ``ensemble_meta.json`` (rule 3).

    The continuous load and tech marginals are uniform on ``[0, 1]`` (the
    published low/high are treated as the range bounds, A-3) and so need no
    stored parameters -- only the gas marginal is parametric.
    """

    n: int
    seed: int
    gas: GasMarginal
    # Spearman rank correlations over CONTINUOUS_DIMS, row/col in that order.
    spearman: tuple[tuple[float, ...], ...]
    # Probability weights per discrete dim: weather (int year keys), hydro and
    # policy (str level keys). Weights need not be normalised -- the sampler
    # normalises them and preserves the given key order for binning.
    discrete_weights: dict[str, dict] = field(default_factory=dict)

    def spearman_matrix(self) -> np.ndarray:
        """Return the Spearman matrix as a ``(3, 3)`` float array."""
        return np.asarray(self.spearman, dtype=float)

    def spec_hash(self) -> str:
        """Return a deterministic 16-char hash of the full spec.

        Hashes the canonical JSON of every field, so two specs with identical
        parameters -- regardless of dict insertion order -- hash the same, and
        any change to a marginal, correlation or weight changes the id.
        """
        payload = json.dumps(self._canonical(), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def _canonical(self) -> dict:
        """Return an order-independent plain-dict view for hashing/metadata."""
        return {
            "n": self.n,
            "seed": self.seed,
            "gas": {
                "sigma_front": self.gas.sigma_front,
                "sigma_back": self.gas.sigma_back,
                "front_year_start": self.gas.front_year_start,
                "front_year_end": self.gas.front_year_end,
                "back_year": self.gas.back_year,
                "floor_to_aeo": self.gas.floor_to_aeo,
                "low_path": self.gas.low_path,
                "mid_path": self.gas.mid_path,
                "high_path": self.gas.high_path,
            },
            "continuous_dims": list(CONTINUOUS_DIMS),
            "discrete_dims": list(DISCRETE_DIMS),
            "spearman": [list(row) for row in self.spearman],
            "discrete_weights": {
                dim: {str(k): float(v) for k, v in self.discrete_weights[dim].items()}
                for dim in sorted(self.discrete_weights)
            },
        }

    @classmethod
    def from_yaml(cls, path) -> "UncertaintySpec":
        """Load an :class:`UncertaintySpec` from a committed YAML spec file.

        The ``spearman`` block is a nested mapping keyed by dim name (e.g.
        ``{gas: {gas: 1.0, load: 0.3, tech: 0.0}, ...}``); it is read into a
        matrix in :data:`CONTINUOUS_DIMS` order and validated for a unit
        diagonal and symmetry. Discrete weights are read for every dim in
        :data:`DISCRETE_DIMS`.

        Args:
            path: Path to the YAML spec.

        Returns:
            The parsed spec.

        Raises:
            ValueError: When the spearman matrix is missing an entry, is not
                symmetric, or has a non-unit diagonal, or when a discrete dim's
                weights are missing or non-positive.
        """
        data = yaml.safe_load(Path(path).read_text()) or {}
        gas = GasMarginal(**data["gas"])
        spearman = _spearman_from_mapping(data.get("spearman", {}))
        weights = {dim: dict(data["discrete_weights"][dim]) for dim in DISCRETE_DIMS}
        for dim, w in weights.items():
            if not w or any(float(v) <= 0.0 for v in w.values()):
                raise ValueError(
                    f"discrete_weights[{dim!r}] must be non-empty with positive "
                    f"weights, got {w!r}"
                )
        return cls(
            n=int(data["n"]),
            seed=int(data["seed"]),
            gas=gas,
            spearman=spearman,
            discrete_weights=weights,
        )


@dataclass(frozen=True)
class DrawRecord:
    """One member draw: the resolved PB-1 lever values plus provenance.

    ``draw_id`` is the ensemble member identity (a string, replacing the
    weather-year int of the legacy ensemble). ``lhs_row`` is this draw's raw
    stratified Latin-hypercube row (one uniform per dim, in
    ``CONTINUOUS_DIMS + DISCRETE_DIMS`` order) -- recorded so the full sampling
    matrix, and hence the stratification, is auditable from the returned draws.
    ``gas_z`` is the correlated standard normal behind the gas factor.
    """

    draw_id: str
    index: int
    gas_price_factor: float
    demand_growth_percentile: float
    tech_cost_percentile: float
    weather_year: int
    hydro_year: str
    policy_bundle: str
    gas_z: float
    lhs_row: tuple[float, ...]


@dataclass(frozen=True)
class SamplerMeta:
    """Deterministic sampler provenance returned alongside the draws.

    Everything needed to reproduce and audit a sample: the ``seed`` and
    ``spec_hash``, the full stratified LHS ``lhs_matrix`` (n x d), the target
    Spearman and induced Pearson matrices, and the gas sigma schedule and the
    scalar reference derived from it.
    """

    seed: int
    n: int
    spec_hash: str
    continuous_dims: tuple[str, ...]
    discrete_dims: tuple[str, ...]
    spearman: list[list[float]]
    pearson: list[list[float]]
    gas_sigma_reference: float
    gas_sigma_schedule: dict[int, float]
    discrete_weights: dict[str, dict]
    lhs_matrix: list[list[float]]

    def as_dict(self) -> dict:
        """Return a JSON-serialisable view for ``ensemble_meta.json``."""
        return {
            "seed": self.seed,
            "n": self.n,
            "spec_hash": self.spec_hash,
            "continuous_dims": list(self.continuous_dims),
            "discrete_dims": list(self.discrete_dims),
            "spearman": self.spearman,
            "pearson": self.pearson,
            "gas_sigma_reference": self.gas_sigma_reference,
            "gas_sigma_schedule": {
                str(y): s for y, s in self.gas_sigma_schedule.items()
            },
            "discrete_weights": {
                dim: {str(k): float(v) for k, v in w.items()}
                for dim, w in self.discrete_weights.items()
            },
            "lhs_matrix": self.lhs_matrix,
        }


class DrawSet:
    """A sequence of :class:`DrawRecord` with attached :class:`SamplerMeta`.

    Behaves like the ``list[DrawRecord]`` callers expect (iteration, ``len``,
    indexing) while also carrying ``.meta`` so the seed, full LHS matrix and
    correlation matrices travel with the draws (plan §2.3's "seed, spec hash and
    the full matrix recorded" requirement).
    """

    def __init__(self, draws: list[DrawRecord], meta: SamplerMeta):
        self.draws = draws
        self.meta = meta

    def __iter__(self):
        return iter(self.draws)

    def __len__(self) -> int:
        return len(self.draws)

    def __getitem__(self, index):
        return self.draws[index]


def _henry_hub(path: str, year: int) -> float:
    """Return the AEO Henry Hub value for a path/year, extrapolating past 2050."""
    trajectory = HENRY_HUB_TRAJECTORIES[path]
    if year in trajectory:
        return trajectory[year]
    last = max(trajectory)
    growth = trajectory[last] / trajectory[last - 1]
    return trajectory[last] * growth ** (year - last)


def _spearman_from_mapping(mapping: dict) -> tuple[tuple[float, ...], ...]:
    """Build a validated Spearman matrix (CONTINUOUS_DIMS order) from a mapping."""
    rows: list[tuple[float, ...]] = []
    for i in CONTINUOUS_DIMS:
        row = mapping.get(i, {})
        rows.append(tuple(float(row.get(j, 0.0)) for j in CONTINUOUS_DIMS))
    matrix = np.asarray(rows, dtype=float)
    if not np.allclose(np.diag(matrix), 1.0):
        raise ValueError(f"spearman diagonal must be 1.0, got {np.diag(matrix)}")
    if not np.allclose(matrix, matrix.T):
        raise ValueError("spearman matrix must be symmetric")
    return tuple(tuple(r) for r in rows)


def _weighted_bins(column: np.ndarray, weights: dict) -> list:
    """Map a stratified uniform column through weighted categorical bins.

    Each uniform in ``[0, 1)`` falls into the level whose cumulative-weight
    interval contains it, so with LHS stratification the level frequencies track
    the weights (up to the bin the stratum boundary lands in). Key order defines
    the bin order and is preserved.

    Args:
        column: The stratified uniforms for this dim (one per draw).
        weights: ``{level: weight}``; weights are normalised internally.

    Returns:
        The chosen level per draw, in draw order.
    """
    levels = list(weights)
    w = np.asarray([float(weights[k]) for k in levels], dtype=float)
    edges = np.cumsum(w / w.sum())
    idx = np.clip(np.searchsorted(edges, column, side="right"), 0, len(levels) - 1)
    return [levels[i] for i in idx]


def sample_draws(spec: UncertaintySpec) -> DrawSet:
    """Draw ``spec.n`` correlated members -- pure sampling, no I/O (plan §2.3).

    Mechanics, exactly as §2.3 specifies:

    1. A single :class:`scipy.stats.qmc.LatinHypercube` produces a stratified
       ``U`` of shape ``(n, 6)`` -- one column per continuous then discrete dim.
    2. Continuous block: ``z = Phi^-1(U)``; the Spearman matrix is converted to
       Pearson via ``r_P = 2*sin(pi*rho_S/6)``; a Cholesky factor induces the
       correlation (``z @ L.T``); ``Phi`` maps back to correlated uniforms which
       pass through each marginal's ppf (gas lognormal, load/tech uniform).
    3. Discrete block: each raw LHS column maps through its weighted bins.

    The result is deterministic in ``spec.seed`` -- two calls with the same spec
    return bit-identical draws.

    Args:
        spec: The uncertainty specification.

    Returns:
        A :class:`DrawSet` of ``spec.n`` :class:`DrawRecord` with attached
        :class:`SamplerMeta` (seed, full LHS matrix, Spearman/Pearson, gas
        schedule).
    """
    n = spec.n
    d = len(CONTINUOUS_DIMS) + len(DISCRETE_DIMS)
    lhs = qmc.LatinHypercube(d=d, seed=spec.seed).random(n)

    # --- continuous block: Gaussian copula over CONTINUOUS_DIMS ---
    z = norm.ppf(lhs[:, : len(CONTINUOUS_DIMS)])  # (n, 3) stratified normals
    spearman = spec.spearman_matrix()
    pearson = 2.0 * np.sin(np.pi * spearman / 6.0)
    chol = np.linalg.cholesky(pearson)
    z_corr = z @ chol.T  # (n, 3) correlated standard normals
    u_corr = norm.cdf(z_corr)  # correlated uniforms for the uniform marginals

    sigma_ref = spec.gas.sigma_reference()
    gas_z = z_corr[:, 0]
    gas_factor = np.exp(sigma_ref * gas_z)  # lognormal ppf, mu = 0
    load_pct = u_corr[:, 1]  # uniform marginal -> percentile is the uniform itself
    tech_pct = u_corr[:, 2]

    # --- discrete block: independent weighted bins on the raw LHS columns ---
    weather = _weighted_bins(lhs[:, 3], spec.discrete_weights["weather"])
    hydro = _weighted_bins(lhs[:, 4], spec.discrete_weights["hydro"])
    policy = _weighted_bins(lhs[:, 5], spec.discrete_weights["policy"])

    draws: list[DrawRecord] = []
    for i in range(n):
        draws.append(
            DrawRecord(
                draw_id=f"draw-{i:04d}",
                index=i,
                gas_price_factor=float(gas_factor[i]),
                demand_growth_percentile=float(load_pct[i]),
                tech_cost_percentile=float(tech_pct[i]),
                weather_year=int(weather[i]),
                hydro_year=str(hydro[i]),
                policy_bundle=str(policy[i]),
                gas_z=float(gas_z[i]),
                lhs_row=tuple(float(x) for x in lhs[i]),
            )
        )

    meta = SamplerMeta(
        seed=spec.seed,
        n=n,
        spec_hash=spec.spec_hash(),
        continuous_dims=CONTINUOUS_DIMS,
        discrete_dims=DISCRETE_DIMS,
        spearman=[list(row) for row in spec.spearman],
        pearson=[[float(x) for x in row] for row in pearson],
        gas_sigma_reference=float(sigma_ref),
        gas_sigma_schedule=spec.gas.sigma_schedule(),
        discrete_weights=spec.discrete_weights,
        lhs_matrix=[[float(x) for x in row] for row in lhs],
    )
    return DrawSet(draws, meta)


def draw_to_config(base_config: ScenarioConfig, draw: DrawRecord) -> ScenarioConfig:
    """Apply one draw's sampled values to a base config via the PB-1 levers.

    Overrides only the six sampled levers -- ``gas_price_factor``,
    ``demand_growth_percentile``, ``tech_cost_percentile``, ``weather_year``,
    ``hydro_year``, ``policy_bundle`` -- and leaves every other field of
    ``base_config`` untouched. The ``policy_bundle`` label is left for
    ``runner.run_scenario_iso`` to resolve to its underlying fields at
    config-build time (rule 24), so the resolved fields land in ``run_config``.

    Args:
        base_config: The forecast scenario every draw perturbs.
        draw: The draw to apply.

    Returns:
        A copy of ``base_config`` carrying the draw's lever values.

    Raises:
        ValueError: When ``base_config`` is not in forecast mode -- the sampler
            perturbs forecast-only uncertainty levers (``gas_price_factor`` is
            asserted 1.0 in backcast mode, rule 13), so a backcast base is a
            usage error.
    """
    if base_config.mode != "forecast":
        raise ValueError(
            "the uncertainty sampler is a forecast tool; base config mode must "
            f"be 'forecast', got {base_config.mode!r}. Its levers (gas_price_"
            "factor et al.) are forecast-only uncertainty inputs (rule 13)."
        )
    return base_config.with_overrides(
        gas_price_factor=draw.gas_price_factor,
        demand_growth_percentile=draw.demand_growth_percentile,
        tech_cost_percentile=draw.tech_cost_percentile,
        weather_year=draw.weather_year,
        hydro_year=draw.hydro_year,
        policy_bundle=draw.policy_bundle,
    )
