"""Structural-error prior + convolution (PB-3, probability-bounds program).

The parametric band (:mod:`market_sim.uncertainty` + :mod:`market_sim.ensemble`,
PB-2) answers "we don't know the *inputs*." It does **not** answer "given the
inputs, the model itself is wrong by this much." This module owns that second
term and convolves the two into the *published* emissions band.

Design source: ``docs/handoffs/probability-bounds-plan-2026-07.md`` §3. The prior
is fit from the committed **D-7 statistical-mode probes**
(``docs/statistical-mode-results-2026-07.md``). Statistical mode strips every
measured backcast overlay but keeps realized annual gas price, load and weather,
so its emissions error is exactly *model error given true inputs* -- the term
that convolves with §2's *input* uncertainty without double-counting (§3.1).

What this module does, and does not, do (CLAUDE.md rules 1/13, plan §3.2):

* **Fits, never tunes.** ``eps_{i,y} = ln(emissions_model / emissions_actual)``
  is read straight off the committed statmode run payloads and bench actuals --
  a measured, reproducible source that re-derives only when those probes update
  (rule 23). No distribution parameter is chosen to make a band a particular
  width.
* **Widens, never recenters.** ``eps`` enters the convolution with its non-zero
  per-ISO mean ``b_i``, so the published band is *asymmetric around the model
  path* and honestly covers the known dispatch bias. It does **not** subtract
  ``b_i`` from the point forecast -- that would feed a measured outcome back into
  the forecast (rule 13's forbidden side). The headline point forecast stays the
  parametric-layer P50; the structural layer is added alongside it, never over
  it.
* **Declares what it cannot yet cover.** The horizon term ``lambda(h)`` (§3.4
  item 1) is pinned to 0 and flagged UNMEASURED until the PP-0.3 capacity
  hindcast supplies a number, so every published band is labelled
  *dispatch-conditional -- excludes fleet-path structural error*.

The public surface is pure (unit-testable, no solves): :func:`fit_prior`
(computation) sits behind :func:`load_statmode_residuals` (I/O), and
:func:`convolve` produces the ``parametric_plus_structural`` band rows against
the frozen PB-2 ``bands.parquet`` schema.
"""

from __future__ import annotations

import base64
import gzip
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from market_sim.config import paths
from market_sim.config.constants import (
    START_YEAR,
    STATMODE_PROBE_RUNS,
    STRUCTURAL_PRIOR_CONVOLUTION_K,
    STRUCTURAL_PRIOR_FIT_YEARS,
    STRUCTURAL_PRIOR_HORIZON_LAMBDA,
    STRUCTURAL_PRIOR_STUDENT_T_NU,
    STRUCTURAL_PRIOR_VERSION,
)

# The metric the structural prior applies to: it is a prior over *emissions*
# dispatch skill, so it convolves onto the emissions band only. Other metrics
# stay parametric (their structural error is not measured by D-7 CO2 residuals).
EMISSIONS_METRIC: str = "emissions_mt"

# The structural layer name in bands.parquet (§4.1), alongside "parametric"
# (PB-2) and "scenario_envelope" (PB-0).
STRUCTURAL_LAYER: str = "parametric_plus_structural"

# Published quantiles for the structural band (§3.3). Wider than PB-2's
# P10/P50/P90 so the published fan shows the full P5..P95 spread.
PUBLISHED_QUANTILES: tuple[float, ...] = (0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95)


@dataclass(frozen=True)
class IsoResidual:
    """One ISO's fitted structural-error residuals from the D-7 statmode probe.

    ``eps`` is the per-year ``ln(model / actual)`` emissions log-ratio over
    :data:`~market_sim.config.constants.STRUCTURAL_PRIOR_FIT_YEARS`; ``bias`` is
    its mean (persistent across years within an ISO, D-7 §3.2) and ``noise_sd``
    its sample standard deviation (``ddof=1``). ``model_co2`` / ``actual_co2``
    are kept so the fit is fully reconstructable from the artifact.
    """

    iso: str
    years: tuple[int, ...]
    model_co2: tuple[float, ...]
    actual_co2: tuple[float, ...]
    eps: tuple[float, ...]
    bias: float
    noise_sd: float
    statmode_run_id: str

    def as_dict(self) -> dict:
        """Return a JSON-serialisable view for the prior artifact / meta."""
        return {
            "iso": self.iso,
            "years": list(self.years),
            "model_co2": list(self.model_co2),
            "actual_co2": list(self.actual_co2),
            "eps": list(self.eps),
            "bias": self.bias,
            "noise_sd": self.noise_sd,
            "statmode_run_id": self.statmode_run_id,
        }


@dataclass(frozen=True)
class StructuralPrior:
    """A fitted, cited prior over the model's emissions dispatch-skill error.

    Per ISO the error is ``eps_i ~ Student-t(nu) * scale + b_i`` where ``b_i`` is
    that ISO's measured bias, ``scale = sqrt(pooled_noise_var * (1 + 1/n))``
    pools the noise across ISOs and carries the ``n=3`` parameter uncertainty
    (the ``+1/n`` predictive-variance inflation), and ``nu=2`` gives fat tails
    (plan §3.2). Both the inflation and the fat tails make the prior strictly
    *wider* than the plug-in normal ``N(b_i, s_pooled)`` -- never narrower.

    ``horizon_lambda`` is the fleet-path variance multiplier, 0 and UNMEASURED
    until PP-0.3, so :meth:`is_dispatch_conditional` is True and every band it
    produces is labelled dispatch-conditional (§3.4 item 1).
    """

    version: str
    nu: float
    fit_years: tuple[int, ...]
    small_sample_inflation: float
    pooled_noise_var: float
    horizon_lambda: float
    per_iso: dict[str, IsoResidual] = field(default_factory=dict)

    def scale(self, horizon: int = 0) -> float:
        """Return the structural-error scale, optionally horizon-widened.

        The base scale is ``sqrt(pooled_noise_var * small_sample_inflation)``.
        With ``horizon_lambda == 0`` (the UNMEASURED default) the horizon has no
        effect; a future non-zero ``lambda`` multiplies the *variance* by
        ``(1 + lambda * horizon)`` (plan §3.4 item 1).

        Args:
            horizon: Years past :data:`START_YEAR` (0 for the first forecast
                year). Ignored while ``horizon_lambda == 0``.

        Returns:
            The scale (a standard deviation in log space).
        """
        base_var = self.pooled_noise_var * self.small_sample_inflation
        return math.sqrt(base_var * (1.0 + self.horizon_lambda * max(0, horizon)))

    def bias(self, iso: str) -> float:
        """Return the measured emissions log-bias ``b_i`` for ``iso``."""
        return self.per_iso[iso.upper()].bias

    def is_dispatch_conditional(self) -> bool:
        """Return True while the fleet-path term is UNMEASURED (``lambda==0``)."""
        return self.horizon_lambda == 0.0

    def label(self) -> str:
        """Return the coverage caveat for ``ensemble_meta.json`` / the fan chart.

        Driven by :meth:`is_dispatch_conditional` so the band never claims
        coverage the metadata cannot defend (plan §4.2, cross-cutting note).
        """
        base = (
            f"published probability band (PB-3, prior {self.version}): the "
            "parametric input band (PB-2) convolved with the D-7 statistical-mode "
            "structural-error prior (fit on "
            f"{'/'.join(str(y) for y in self.fit_years)})"
        )
        if self.is_dispatch_conditional():
            return (
                base + "; dispatch-conditional -- excludes fleet-path structural "
                "error until PP-0.3 (lambda(h)=0, UNMEASURED)"
            )
        return base

    def sample(
        self, iso: str, size, rng: np.random.Generator, horizon: int = 0
    ) -> np.ndarray:
        """Draw structural-error ``eps`` values for ``iso``.

        ``eps = b_i + scale(horizon) * T`` with ``T ~ standard Student-t(nu)``.
        The location ``b_i`` is the measured bias (non-zero mean, no recentering,
        §3.2); the fat-tailed ``T`` and inflated scale make the draw wider than a
        plug-in normal.

        Args:
            iso: ISO whose bias to centre on.
            size: Shape passed to the generator (int or tuple).
            rng: Seeded generator -- deterministic given the caller's seed.
            horizon: Years past :data:`START_YEAR` (see :meth:`scale`).

        Returns:
            An array of ``eps`` draws of shape ``size``.
        """
        b = self.bias(iso)
        t = rng.standard_t(self.nu, size=size)
        return b + self.scale(horizon) * t

    def plugin_normal_scale(self) -> float:
        """Return the plug-in normal scale ``s_pooled`` (no small-sample term).

        The naive estimator the fitted prior must beat for width: same pooled
        noise, but with thin normal tails and *no* parameter-uncertainty
        inflation (plan §3.2's "must be wider than the plug-in normal").
        """
        return math.sqrt(self.pooled_noise_var)

    def as_dict(self) -> dict:
        """Return the full prior as a JSON-serialisable artifact block.

        Everything a reader needs to reproduce and attack the fit (rule 24): the
        version, estimator parameters, pooled noise, per-ISO residuals with their
        statmode run ids, and the dispatch-conditional flag.
        """
        return {
            "version": self.version,
            "estimator": (
                f"per-ISO Student-t(nu={self.nu:g}) location b_i (measured bias, "
                "not recentered) scale sqrt(pooled_within_ISO_var * "
                f"(1 + 1/n)); n={len(self.fit_years)} backcast years; fit from the "
                "committed D-7 statistical-mode probes (plan §3.2)"
            ),
            "nu": self.nu,
            "fit_years": list(self.fit_years),
            "small_sample_inflation": self.small_sample_inflation,
            "pooled_noise_var": self.pooled_noise_var,
            "pooled_scale": self.scale(0),
            "plugin_normal_scale": self.plugin_normal_scale(),
            "horizon_lambda": self.horizon_lambda,
            "horizon_lambda_status": (
                "UNMEASURED (0) -- dispatch-conditional until PP-0.3 capacity "
                "hindcast (plan §3.4 item 1)"
            ),
            "dispatch_conditional": self.is_dispatch_conditional(),
            "per_iso": {iso: r.as_dict() for iso, r in sorted(self.per_iso.items())},
        }


def fit_prior(
    statmode_bundles: dict[str, dict[int, float]],
    actuals: dict[str, dict[int, float]],
    run_ids: dict[str, str] | None = None,
    nu: float = STRUCTURAL_PRIOR_STUDENT_T_NU,
    fit_years: tuple[int, ...] = STRUCTURAL_PRIOR_FIT_YEARS,
    horizon_lambda: float = STRUCTURAL_PRIOR_HORIZON_LAMBDA,
    version: str = STRUCTURAL_PRIOR_VERSION,
) -> StructuralPrior:
    """Fit the structural-error prior from statmode model vs actual emissions.

    For each ISO, ``eps_{i,y} = ln(model / actual)`` over ``fit_years`` (§3.2);
    ``b_i`` is its mean and ``s_i`` its sample sd (``ddof=1``). The noise scale is
    **pooled** across ISOs -- ``s_pooled^2 = sum_i (n_i-1) s_i^2 / sum_i (n_i-1)``
    -- and carried with the ``n``-year parameter uncertainty as the
    ``(1 + 1/n)`` predictive-variance inflation, so the per-ISO prior is
    ``Student-t(nu)`` located at ``b_i`` with scale
    ``sqrt(s_pooled^2 * (1 + 1/n))``. Pure: no I/O (see
    :func:`load_statmode_residuals` for the committed inputs).

    Args:
        statmode_bundles: ``{ISO: {year: model_co2_mt}}`` from the statmode
            probes (the model side of the residual).
        actuals: ``{ISO: {year: actual_co2_mt}}`` (the bench actual side).
        run_ids: Optional ``{ISO: statmode_run_id}`` provenance stamped into each
            :class:`IsoResidual`.
        nu: Student-t degrees of freedom (default from constants, plan §3.2).
        fit_years: Backcast years to fit on (2023-2025; 2022/H1-2026 stay
            quarantined, rule 22).
        horizon_lambda: Fleet-path variance multiplier (0/UNMEASURED default).
        version: Version tag for the fitted artifact.

    Returns:
        The fitted :class:`StructuralPrior`.

    Raises:
        ValueError: When an ISO is missing a fit year in either input, or when a
            year is outside ``fit_years`` (rule 22 guard -- the prior must never
            ingest a quarantined year), or when fewer than two years are present
            (a pooled variance needs ``ddof=1``).
    """
    run_ids = run_ids or {}
    fit_years = tuple(int(y) for y in fit_years)
    if len(fit_years) < 2:
        raise ValueError(f"fit needs >=2 years for ddof=1, got {fit_years!r}")

    per_iso: dict[str, IsoResidual] = {}
    weighted_var_num = 0.0
    weighted_var_den = 0.0
    for iso in sorted(statmode_bundles):
        iso_u = iso.upper()
        model_map = statmode_bundles[iso]
        actual_map = actuals.get(iso, actuals.get(iso_u, {}))
        # Rule 22: reject any year outside the fit window before it can bias b_i.
        stray = set(model_map) - set(fit_years)
        if stray:
            raise ValueError(
                f"{iso_u}: statmode bundle carries non-fit years {sorted(stray)} "
                f"outside {fit_years} -- the structural prior only fits "
                "2023-2025 (CLAUDE.md rule 22)."
            )
        model = []
        actual = []
        for y in fit_years:
            if y not in model_map or y not in actual_map:
                raise ValueError(
                    f"{iso_u}: missing year {y} (model={y in model_map}, "
                    f"actual={y in actual_map})"
                )
            model.append(float(model_map[y]))
            actual.append(float(actual_map[y]))
        eps = np.log(np.asarray(model) / np.asarray(actual))
        bias = float(eps.mean())
        noise_sd = float(eps.std(ddof=1))
        per_iso[iso_u] = IsoResidual(
            iso=iso_u,
            years=fit_years,
            model_co2=tuple(model),
            actual_co2=tuple(actual),
            eps=tuple(float(e) for e in eps),
            bias=bias,
            noise_sd=noise_sd,
            statmode_run_id=run_ids.get(iso, run_ids.get(iso_u, "")),
        )
        # Pooled within-ISO variance: weight each ISO's sample variance by its
        # degrees of freedom (n_i - 1), so ISOs with more years count more.
        dof = len(fit_years) - 1
        weighted_var_num += dof * noise_sd**2
        weighted_var_den += dof

    if not per_iso:
        raise ValueError("fit_prior received no ISOs")

    pooled_var = weighted_var_num / weighted_var_den
    n = len(fit_years)
    inflation = 1.0 + 1.0 / n
    return StructuralPrior(
        version=version,
        nu=float(nu),
        fit_years=fit_years,
        small_sample_inflation=inflation,
        pooled_noise_var=pooled_var,
        horizon_lambda=float(horizon_lambda),
        per_iso=per_iso,
    )


def _hf7_quantile(values: np.ndarray, q: float) -> float:
    """Return the ``q`` quantile via numpy's Hyndman-Fan type-7 estimator.

    The same estimator PB-2's band machinery uses (``numpy.quantile`` default,
    ``method="linear"``) so the parametric and published layers are comparable
    (plan §2.4).
    """
    return float(np.quantile(values, q, method="linear"))


def _structural_sample(
    parametric_values: np.ndarray,
    prior: StructuralPrior,
    iso: str,
    rng: np.random.Generator,
    k: int,
    horizon: int,
) -> np.ndarray:
    """Return the flat ``n*K`` structural sample ``emissions * exp(eps)`` (§3.3).

    Each of the ``n`` parametric emissions values is paired with ``K``
    independent structural draws; the product lives in log space
    (``value * exp(eps)``) and is flattened for pooled quantiles.
    """
    n = parametric_values.size
    eps = prior.sample(iso, size=(n, k), rng=rng, horizon=horizon)
    return (parametric_values[:, None] * np.exp(eps)).ravel()


def convolve(
    values: dict[int, dict[str, list[float]]],
    prior: StructuralPrior,
    iso: str,
    seed: int,
    k: int = STRUCTURAL_PRIOR_CONVOLUTION_K,
    quantiles: tuple[float, ...] = PUBLISHED_QUANTILES,
    metric: str = EMISSIONS_METRIC,
    n_boot: int = 1000,
    ci: float = 0.9,
) -> list[dict]:
    """Convolve the parametric emissions band with the structural prior (§3.3).

    For each forecast year, pairs the ``n`` parametric emissions values with
    ``K`` structural draws (:func:`_structural_sample`), then reads the published
    quantiles off the pooled ``n*K`` sample. Emits rows against the frozen
    ``bands.parquet`` schema with ``layer == parametric_plus_structural``; the
    bootstrap CI resamples the ``n`` *members* (re-drawing structural noise each
    resample) so it reflects the member-count uncertainty, not the cheap-to-add
    Monte-Carlo ``K`` noise.

    Args:
        values: ``values[year][metric] -> member values`` (PB-2's per-member
            metric index).
        prior: The fitted structural prior.
        iso: ISO whose bias to centre the structural draws on.
        seed: RNG seed -- deterministic given the sampler spec's seed.
        k: Structural draws per parametric draw (plan §3.3).
        quantiles: Published quantiles.
        metric: Metric to convolve (emissions only; §3 is an emissions prior).
        n_boot: Bootstrap resample count per quantile.
        ci: Bootstrap CI width.

    Returns:
        Band rows with keys ``year, metric, layer, quantile, value, n,
        bootstrap_lo, bootstrap_hi`` in a deterministic (year, quantile) order.
    """
    iso = iso.upper()
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for year in sorted(values):
        if metric not in values[year]:
            continue
        arr = np.asarray(values[year][metric], dtype=float)
        horizon = year - START_YEAR
        flat = _structural_sample(arr, prior, iso, rng, k, horizon)
        # Bootstrap over members: resample the n parametric values, re-draw K
        # structural eps, recompute the quantile (§2.4-style CI, member-level).
        boot_q: dict[float, np.ndarray] = {q: np.empty(n_boot) for q in quantiles}
        if arr.size >= 2:
            for b in range(n_boot):
                idx = rng.integers(0, arr.size, size=arr.size)
                bflat = _structural_sample(arr[idx], prior, iso, rng, k, horizon)
                for q in quantiles:
                    boot_q[q][b] = _hf7_quantile(bflat, q)
        tail = (1.0 - ci) / 2.0
        for q in quantiles:
            if arr.size >= 2:
                lo = float(np.quantile(boot_q[q], tail))
                hi = float(np.quantile(boot_q[q], 1.0 - tail))
            else:
                lo = hi = _hf7_quantile(flat, q)
            rows.append(
                {
                    "year": year,
                    "metric": metric,
                    "layer": STRUCTURAL_LAYER,
                    "quantile": q,
                    "value": _hf7_quantile(flat, q),
                    "n": int(flat.size),
                    "bootstrap_lo": lo,
                    "bootstrap_hi": hi,
                }
            )
    return rows


# ---------------------------------------------------------------------------
# I/O: the committed measured source (D-7 statmode probes + bench actuals).
# Kept separate from fit_prior so the fit itself stays pure/unit-testable.
# ---------------------------------------------------------------------------


def _load_run_model_co2(run_id: str, runs_dir: Path) -> dict[int, float]:
    """Return ``{year: model_system_CO2_mt}`` from a committed run payload.

    The run payloads are ``window.BC.runGz["<id>"] = "<base64(gzip(json))>"``;
    this decodes that single string and pulls ``years[<y>].co2.model`` (the
    model's system fossil CO2 in Mt).
    """
    text = (runs_dir / f"{run_id}.js").read_text()
    match = re.search(r'=\s*"([^"]+)"', text)
    if match is None:
        raise ValueError(f"could not find payload string in run file {run_id}.js")
    payload = json.loads(gzip.decompress(base64.b64decode(match.group(1))))
    return {int(y): float(rec["co2"]["model"]) for y, rec in payload["years"].items()}


def _load_bench_actual_co2(iso: str, year: int, bench_dir: Path) -> float:
    """Return the actual system fossil CO2 (Mt) for ``iso``/``year`` from bench.

    The bench actual is ``bench.co2.egrid`` -- the committed system fossil total
    the dashboard's C5a CO2 criterion is scored against.
    """
    data = json.loads(gzip.open(bench_dir / iso.upper() / f"{year}.json.gz").read())
    return float(data["bench"]["co2"]["egrid"])


def load_statmode_residuals(
    isos: list[str] | None = None,
    fit_years: tuple[int, ...] = STRUCTURAL_PRIOR_FIT_YEARS,
    runs_dir: Path | None = None,
    bench_dir: Path | None = None,
) -> tuple[dict[str, dict[int, float]], dict[str, dict[int, float]], dict[str, str]]:
    """Read the committed statmode model + bench actual CO2 for the prior fit.

    The measured, reproducible source (plan §3.1/§3.2): per-ISO model CO2 from
    the committed D-7 statmode run payloads (:data:`STATMODE_PROBE_RUNS`), and
    actual CO2 from the committed bench totals. Only ``fit_years`` are read --
    2022/H1-2026 never enter (rule 22). This is the I/O boundary; the returned
    dicts feed the pure :func:`fit_prior`.

    Args:
        isos: ISOs to load; defaults to every ISO in :data:`STATMODE_PROBE_RUNS`.
        fit_years: Years to read (2023-2025).
        runs_dir: Override for the committed ``runs/`` directory (tests).
        bench_dir: Override for the committed ``bench/`` directory (tests).

    Returns:
        ``(statmode_bundles, actuals, run_ids)`` ready for :func:`fit_prior`.

    Raises:
        KeyError: When an ISO has no registered statmode probe run.
    """
    runs_dir = runs_dir or (paths.FRONTEND_BACKCAST_DIR / "runs")
    bench_dir = bench_dir or (paths.FRONTEND_BACKCAST_DIR / "bench")
    isos = [i.upper() for i in (isos or list(STATMODE_PROBE_RUNS))]
    fit_years = tuple(int(y) for y in fit_years)

    statmode_bundles: dict[str, dict[int, float]] = {}
    actuals: dict[str, dict[int, float]] = {}
    run_ids: dict[str, str] = {}
    for iso in isos:
        run_id = STATMODE_PROBE_RUNS[iso]
        run_ids[iso] = run_id
        model = _load_run_model_co2(run_id, runs_dir)
        statmode_bundles[iso] = {y: model[y] for y in fit_years if y in model}
        actuals[iso] = {y: _load_bench_actual_co2(iso, y, bench_dir) for y in fit_years}
    return statmode_bundles, actuals, run_ids


def default_prior(isos: list[str] | None = None) -> StructuralPrior:
    """Fit the structural prior from the committed D-7 statmode probes.

    Convenience composition of :func:`load_statmode_residuals` and
    :func:`fit_prior` using the frozen provenance and constants -- the prior a
    production band run folds in. Pooling the noise across ISOs, it fits every
    registered ISO by default even when a single-ISO band is being convolved
    (the pooled scale is stronger with all six).

    Args:
        isos: ISOs to fit on; defaults to all of :data:`STATMODE_PROBE_RUNS`.

    Returns:
        The fitted :class:`StructuralPrior`.
    """
    bundles, actuals, run_ids = load_statmode_residuals(isos)
    return fit_prior(bundles, actuals, run_ids=run_ids)
