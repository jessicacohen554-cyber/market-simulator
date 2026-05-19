"""Calibration of simulated results against published benchmarks.

Adapted from the old repo's ``calibrate_lmp_model.py`` framework structure
and ``validate_market_forecasts.py`` benchmark-comparison approach -- the
diagnostic ordering and comparison scaffolding only, not the dispatch logic.

A calibration run loads one cached scenario-year, aggregates it to annual
headline numbers, and walks four diagnostics in a fixed order:

1. generation mix by fuel type (TWh)
2. price duration curve shape (P10/P50/P90/mean)
3. average price
4. per-fuel capacity factors

Each diagnostic yields a pass/fail, or ``skipped`` when the caller supplies
no benchmark for it. The run passes only when every non-skipped diagnostic
passes. Diagnostics run in this order so an upstream failure explains the
ones below it: wrong dispatch volumes invalidate the price checks, and a
wrong price shape invalidates the average-price level check.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from market_sim.config.constants import START_YEAR
from market_sim.results import cache
from market_sim.results.export import _summarize_year

# Default calibration tolerance: ±5% of benchmark for every diagnostic.
# Source: market-sim-build-plan.md Phase 7 calibration targets.
DEFAULT_TOLERANCE: float = 0.05

# Below this magnitude a benchmark value is treated as exactly zero.
_ZERO_TOL: float = 1e-9

# Diagnostic status values.
PASS: str = "pass"
FAIL: str = "fail"
SKIPPED: str = "skipped"


def _pct_diff(model: float, benchmark: float) -> float:
    """Return the signed fractional difference ``(model - benchmark) / benchmark``.

    When the benchmark is zero, returns ``0.0`` if the model is also zero
    and ``inf`` otherwise, so a quantity that the benchmark expects to be
    absent but the model produces always fails.

    Args:
        model: The simulated value.
        benchmark: The published benchmark value.

    Returns:
        The signed fractional difference, or ``inf`` for a zero-benchmark
        mismatch.
    """
    if abs(benchmark) < _ZERO_TOL:
        return 0.0 if abs(model) < _ZERO_TOL else float("inf")
    return (model - benchmark) / benchmark


def _compare(model: float, benchmark: float, tolerance: float) -> dict:
    """Compare one scalar against a benchmark.

    Args:
        model: The simulated value.
        benchmark: The published benchmark value.
        tolerance: Maximum allowed absolute fractional difference.

    Returns:
        A dict with ``model``, ``benchmark``, ``pct_diff`` and ``pass_fail``.
    """
    diff = _pct_diff(float(model), float(benchmark))
    return {
        "model": round(float(model), 4),
        "benchmark": round(float(benchmark), 4),
        "pct_diff": round(diff, 4),
        "pass_fail": PASS if abs(diff) <= tolerance else FAIL,
    }


def _as_generation_twh(result) -> dict[str, float]:
    """Coerce a calibration input into a ``{fuel: TWh}`` mapping.

    Accepts either a bare ``{fuel: TWh}`` mapping or an annual-summary dict
    carrying a ``generation_twh`` key (as produced by the export
    aggregation), so both raw mixes and full summaries can be passed.

    Args:
        result: A ``{fuel: TWh}`` mapping or a summary dict containing one.

    Returns:
        The generation-by-fuel mapping, in TWh.

    Raises:
        TypeError: When ``result`` is not a mapping.
    """
    if not isinstance(result, Mapping):
        raise TypeError(
            f"expected a mapping of fuel -> TWh, got {type(result).__name__}"
        )
    if "generation_twh" in result:
        return {str(k): float(v) for k, v in result["generation_twh"].items()}
    return {str(k): float(v) for k, v in result.items()}


def check_generation_mix(
    result, benchmark, tolerance: float = DEFAULT_TOLERANCE
) -> dict:
    """Compare generation by fuel type against a benchmark.

    Args:
        result: The model's generation by fuel type, in TWh -- either a
            ``{fuel: TWh}`` mapping or an annual-summary dict carrying a
            ``generation_twh`` key.
        benchmark: The benchmark generation by fuel type, ``{fuel: TWh}``.
        tolerance: Maximum allowed absolute fractional deviation per fuel.

    Returns:
        ``{fuel: {model, benchmark, pct_diff, pass_fail}}`` for every fuel
        appearing in either the model mix or the benchmark.
    """
    model_mix = _as_generation_twh(result)
    benchmark = {str(k): float(v) for k, v in dict(benchmark).items()}
    fuels = sorted(set(model_mix) | set(benchmark))
    return {
        fuel: _compare(
            model_mix.get(fuel, 0.0), benchmark.get(fuel, 0.0), tolerance
        )
        for fuel in fuels
    }


def _sorted_desc(prices) -> np.ndarray:
    """Return a flattened price array sorted high-to-low (a duration curve).

    Args:
        prices: A price array of any shape; flattened before sorting.

    Returns:
        The flattened prices sorted in descending order.

    Raises:
        ValueError: When ``prices`` is empty.
    """
    arr = np.asarray(prices, dtype=float).ravel()
    if arr.size == 0:
        raise ValueError("price array is empty")
    return np.sort(arr)[::-1]


def check_price_duration_curve(prices, benchmark_prices) -> dict:
    """Compare the shape of two price duration curves.

    Both inputs are flattened and sorted high-to-low, then summarized by
    the P10, P50, P90 and mean of the price distribution. ``P10`` is the
    10th percentile (a low price) and ``P90`` the 90th (a high price), so
    a well-formed curve has ``P10 <= P50 <= P90``.

    Args:
        prices: The model's prices, any shape (e.g. ``(n_zones, T)``).
        benchmark_prices: The benchmark prices, any shape.

    Returns:
        ``{metric: {model, benchmark, pct_diff}}`` for ``P10``, ``P50``,
        ``P90`` and ``mean``.
    """
    model_curve = _sorted_desc(prices)
    bench_curve = _sorted_desc(benchmark_prices)

    metrics: dict[str, dict] = {}
    for name, percentile in (("P10", 10.0), ("P50", 50.0), ("P90", 90.0)):
        m = float(np.percentile(model_curve, percentile))
        b = float(np.percentile(bench_curve, percentile))
        metrics[name] = {
            "model": round(m, 2),
            "benchmark": round(b, 2),
            "pct_diff": round(_pct_diff(m, b), 4),
        }
    m_mean = float(model_curve.mean())
    b_mean = float(bench_curve.mean())
    metrics["mean"] = {
        "model": round(m_mean, 2),
        "benchmark": round(b_mean, 2),
        "pct_diff": round(_pct_diff(m_mean, b_mean), 4),
    }
    return metrics


def _pearson_r(model: np.ndarray, actual: np.ndarray) -> float:
    """Return the Pearson correlation of two equal-length series.

    Returns ``nan`` when either series is constant (zero variance), as the
    correlation is then undefined.
    """
    m = np.asarray(model, dtype=float)
    a = np.asarray(actual, dtype=float)
    if m.std() < _ZERO_TOL or a.std() < _ZERO_TOL:
        return float("nan")
    return float(np.corrcoef(m, a)[0, 1])


def check_hourly_dispatch_correlation(
    model_hourly: Mapping[str, np.ndarray],
    eia_hourly: Mapping[str, np.ndarray],
) -> dict:
    """Compare modeled against EIA-930 hourly dispatch shape, per fuel.

    Annual-total checks confirm a fuel produces the right *amount* of
    energy but say nothing about *when*. This check compares the two
    hourly series directly, so a model that hits the annual total by
    running flat when the real fleet cycled is still caught. Three
    statistics are reported per fuel:

    * ``pearson_r`` -- correlation of the modeled and EIA-930 hourly
      series; how well the model reproduces the timing of ramps, peaks and
      troughs. Scale-free, so a pure level offset does not depress it.
    * ``nrmse`` -- root-mean-square error normalized by mean EIA
      generation; magnitude error, including any level bias ``pearson_r``
      ignores.
    * ``model_twh`` / ``eia_twh`` -- annual totals, for context.

    Args:
        model_hourly: ``{fuel: (T,) array}`` of modeled hourly generation,
            in MW -- e.g. ``"coal"`` and ``"gas"`` (the whole gas fleet).
        eia_hourly: ``{fuel: (T,) array}`` of EIA-930 hourly generation, MW.

    Returns:
        ``{fuel: {pearson_r, nrmse, model_twh, eia_twh}}`` for every fuel
        present in both mappings.

    Raises:
        ValueError: when a fuel's two series differ in length.
    """
    out: dict[str, dict] = {}
    for fuel in sorted(set(model_hourly) & set(eia_hourly)):
        m = np.asarray(model_hourly[fuel], dtype=float).ravel()
        a = np.asarray(eia_hourly[fuel], dtype=float).ravel()
        if m.shape != a.shape:
            raise ValueError(
                f"{fuel}: model series length {m.size} does not match "
                f"EIA series length {a.size}"
            )
        mean_a = float(a.mean())
        rmse = float(np.sqrt(np.mean((m - a) ** 2)))
        out[fuel] = {
            "pearson_r": round(_pearson_r(m, a), 4),
            "nrmse": (
                round(rmse / mean_a, 4)
                if abs(mean_a) > _ZERO_TOL
                else float("inf")
            ),
            "model_twh": round(float(m.sum()) / 1e6, 2),
            "eia_twh": round(float(a.sum()) / 1e6, 2),
        }
    return out


@dataclass(frozen=True)
class DiagnosticResult:
    """The outcome of one calibration diagnostic.

    Attributes:
        name: Diagnostic identifier, e.g. ``"generation_mix"``.
        status: One of :data:`PASS`, :data:`FAIL` or :data:`SKIPPED`.
        details: Per-diagnostic comparison detail. Empty when skipped.
    """

    name: str
    status: str
    details: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Whether this diagnostic passed."""
        return self.status == PASS


@dataclass(frozen=True)
class CalibrationReport:
    """The result of a calibration run, with one diagnostic per check.

    Attributes:
        scenario_cache_key: Cache key of the calibrated scenario.
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: The calibration (benchmark) year compared.
        generation_mix: Diagnostic (1) -- generation by fuel type.
        price_duration_curve: Diagnostic (2) -- price duration curve shape.
        avg_price: Diagnostic (3) -- average price level.
        capacity_factors: Diagnostic (4) -- per-fuel capacity factors.
    """

    scenario_cache_key: str
    iso: str
    year: int
    generation_mix: DiagnosticResult
    price_duration_curve: DiagnosticResult
    avg_price: DiagnosticResult
    capacity_factors: DiagnosticResult

    @property
    def diagnostics(self) -> list[DiagnosticResult]:
        """The four diagnostics in fixed diagnostic order."""
        return [
            self.generation_mix,
            self.price_duration_curve,
            self.avg_price,
            self.capacity_factors,
        ]

    @property
    def passed(self) -> bool:
        """Whether every non-skipped diagnostic passed.

        A run with no failing diagnostic passes; skipped diagnostics (no
        benchmark supplied) do not count against it.
        """
        return all(d.status != FAIL for d in self.diagnostics)


def _capacity_factors(result, summary: dict) -> dict[str, float]:
    """Return realized per-fuel capacity factors from an annual summary.

    Capacity factor is annual generation divided by the energy a fuel's
    nameplate capacity could produce running flat out for the year.

    Args:
        result: The year's dispatch result, used for the hour count.
        summary: The annual summary dict from the export aggregation.

    Returns:
        ``{fuel: capacity_factor}`` for every fuel with non-zero capacity.
    """
    hours = result.dispatch.shape[1]
    factors: dict[str, float] = {}
    for fuel, twh in summary["generation_twh"].items():
        cap_mw = summary["capacity_gw"].get(fuel, 0.0) * 1e3
        denom = cap_mw * hours
        if denom > 0.0:
            factors[fuel] = (twh * 1e6) / denom
    return factors


def _gen_mix_diagnostic(summary: dict, benchmarks: Mapping, tolerance: float):
    """Build the generation-mix diagnostic (1)."""
    if "generation_twh" not in benchmarks:
        return DiagnosticResult("generation_mix", SKIPPED)
    mix = check_generation_mix(
        summary["generation_twh"], benchmarks["generation_twh"], tolerance
    )
    status = (
        PASS if all(v["pass_fail"] == PASS for v in mix.values()) else FAIL
    )
    return DiagnosticResult("generation_mix", status, mix)


def _pdc_diagnostic(result, benchmarks: Mapping, tolerance: float):
    """Build the price-duration-curve diagnostic (2)."""
    if "prices" not in benchmarks:
        return DiagnosticResult("price_duration_curve", SKIPPED)
    # Collapse zonal prices to a system price series before comparing.
    system_price = np.asarray(result.prices, dtype=float).mean(axis=0)
    pdc = check_price_duration_curve(system_price, benchmarks["prices"])
    status = (
        PASS
        if all(abs(v["pct_diff"]) <= tolerance for v in pdc.values())
        else FAIL
    )
    return DiagnosticResult("price_duration_curve", status, pdc)


def _avg_price_diagnostic(summary: dict, benchmarks: Mapping, tolerance: float):
    """Build the average-price diagnostic (3)."""
    if "avg_price" not in benchmarks:
        return DiagnosticResult("avg_price", SKIPPED)
    cmp = _compare(summary["avg_price"], benchmarks["avg_price"], tolerance)
    return DiagnosticResult("avg_price", cmp["pass_fail"], cmp)


def _capacity_factor_diagnostic(
    result, summary: dict, benchmarks: Mapping, tolerance: float
):
    """Build the capacity-factor diagnostic (4)."""
    if "capacity_factors" not in benchmarks:
        return DiagnosticResult("capacity_factors", SKIPPED)
    model_cf = _capacity_factors(result, summary)
    detail = {
        fuel: _compare(model_cf.get(fuel, 0.0), bench_cf, tolerance)
        for fuel, bench_cf in benchmarks["capacity_factors"].items()
    }
    status = (
        PASS if all(v["pass_fail"] == PASS for v in detail.values()) else FAIL
    )
    return DiagnosticResult("capacity_factors", status, detail)


def run_calibration_check(
    scenario_cache_key: str, iso: str, benchmarks: Mapping
) -> CalibrationReport:
    """Calibrate one cached scenario-year against published benchmarks.

    Loads the cached dispatch result and fleet context, aggregates them to
    annual headline numbers, and runs the four diagnostics in order:
    (1) generation mix, (2) price duration curve, (3) average price,
    (4) capacity factors. Any diagnostic whose benchmark is absent from
    ``benchmarks`` is reported as :data:`SKIPPED`.

    Args:
        scenario_cache_key: Deterministic config hash of the cached run.
        iso: ISO identifier, e.g. ``"ERCOT"`` (case-insensitive).
        benchmarks: Benchmark values keyed as follows -- all optional
            except that supplying none skips every diagnostic:

            * ``generation_twh``: ``{fuel: TWh}`` benchmark mix.
            * ``prices``: benchmark hourly price series.
            * ``avg_price``: benchmark average price, $/MWh.
            * ``capacity_factors``: ``{fuel: capacity_factor}`` benchmark.
            * ``year``: cached year to compare (default :data:`START_YEAR`).
            * ``tolerance``: fractional tolerance (default
              :data:`DEFAULT_TOLERANCE`).

    Returns:
        The assembled :class:`CalibrationReport`.

    Raises:
        FileNotFoundError: When the cached scenario-year does not exist.
        ValueError: When the cached result carries no fleet context.
    """
    iso = iso.upper()
    tolerance = float(benchmarks.get("tolerance", DEFAULT_TOLERANCE))
    year = int(benchmarks.get("year", START_YEAR))

    result = cache.load_result(iso, scenario_cache_key, year)
    context = cache.load_fleet_context(iso, scenario_cache_key, year)
    summary = _summarize_year(result, context)

    return CalibrationReport(
        scenario_cache_key=scenario_cache_key,
        iso=iso,
        year=year,
        generation_mix=_gen_mix_diagnostic(summary, benchmarks, tolerance),
        price_duration_curve=_pdc_diagnostic(result, benchmarks, tolerance),
        avg_price=_avg_price_diagnostic(summary, benchmarks, tolerance),
        capacity_factors=_capacity_factor_diagnostic(
            result, summary, benchmarks, tolerance
        ),
    )
