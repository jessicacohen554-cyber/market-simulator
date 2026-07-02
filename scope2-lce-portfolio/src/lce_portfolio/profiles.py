"""Hourly capacity-factor (CF) profiles for generation resources.

Produces an ``(n_res, T)`` CF matrix in ``[0, 1]`` for the active resources.
Storage resources carry a zero CF row (their availability is governed by SOC
dynamics, not a CF ceiling).

Two shape sources feed the single seam :func:`build_cf_matrix`:

* **Synthetic** (default for ``iso="SAMPLE"`` and the explicit fallback): a
  deterministic diurnal solar curve, an anti-correlated wind series, and flat
  baseload for firm clean — so the LP runs end-to-end with no external data and
  the tests stay data-free.
* **Real** (per-ISO Parquet under ``data/profiles/<ISO>_<year>.parquet``): the
  ISO-wide wind/solar/offshore shapes built by ``scripts/build_profiles.py``
  from the market simulator's EIA-930 data (vendored shape logic in
  :mod:`lce_portfolio.vendored.renewable_shapes`). When a profile file is
  missing, :func:`build_cf_matrix` warns and falls back to synthetic rather
  than crashing, so a run never hard-fails on absent data.

Real profiles are ISO-wide (single node) — the zonal->ISO capacity-weighted
collapse (ADR 0011) is performed at build time; see the builder script.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np

from lce_portfolio.config import HOURS_PER_YEAR
from lce_portfolio.resources import ResourceArrays

# Real per-ISO profiles live alongside the packaged data, resolved without any
# dependence on market_sim paths (mirrors ``resources._PKG_ROOT``).
_PKG_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILES_DIR = _PKG_ROOT / "data" / "profiles"

# The sentinel ISO that always uses synthetic shapes (demo + tests). Any other
# ISO attempts the real-data path and falls back to synthetic with a warning.
SAMPLE_ISO = "SAMPLE"

# Deterministic synthetic shapes: no Date.now / RNG seeding surprises, so runs
# and tests are reproducible. Keyed by resource name; anything not listed and
# non-storage falls back to a flat profile at its assumed capacity factor.
_DIURNAL_HOURS = np.arange(HOURS_PER_YEAR) % 24


def _solar_shape() -> np.ndarray:
    """Deterministic diurnal solar CF: a clipped sinusoid peaking at midday."""
    # Daylight bump centered on hour 13, zero at night.
    bump = np.sin((_DIURNAL_HOURS - 6) / 12.0 * np.pi)
    shape = np.clip(bump, 0.0, None)
    # Mild seasonal envelope (summer stronger) via day-of-year.
    doy = np.arange(HOURS_PER_YEAR) // 24
    seasonal = 0.85 + 0.15 * np.sin((doy - 80) / 365.0 * 2 * np.pi)
    return shape * seasonal


def _wind_shape() -> np.ndarray:
    """Deterministic wind CF: anti-correlated with solar, with multi-day lulls.

    A synoptic (~weekly) weather cycle that drops to near zero produces genuine
    calm spells, so covering trough hours requires storage or over-build — which
    is what makes the matching-vs-premium frontier non-trivial (and pulls storage
    into the mix at higher premiums). Real ISO shapes replace this via the
    vendored loader.
    """
    hours = np.arange(HOURS_PER_YEAR)
    diurnal = 0.6 + 0.4 * np.cos((_DIURNAL_HOURS - 6) / 12.0 * np.pi)
    doy = hours // 24
    seasonal = 0.9 + 0.2 * np.sin((doy - 300) / 365.0 * 2 * np.pi)  # windier winter
    # Synoptic weather cycle in [0,1] that bottoms out (calm spells) ~every 6.5 d.
    synoptic = np.clip(np.sin(hours / (24 * 6.5) * 2 * np.pi) + 0.15, 0.0, None)
    return np.clip(diurnal * seasonal * synoptic, 0.0, 1.5)


def _normalize_to_cf(shape: np.ndarray, target_cf: float) -> np.ndarray:
    """Scale a non-negative shape so its annual mean equals ``target_cf``."""
    mean = shape.mean()
    if mean <= 0:
        return np.full_like(shape, target_cf)
    return np.clip(shape * (target_cf / mean), 0.0, 1.0)


def _synthetic_cf_matrix(resources: ResourceArrays) -> np.ndarray:
    """Return the ``(n_res, T)`` synthetic CF matrix (the data-free default)."""
    T = HOURS_PER_YEAR
    cf = np.zeros((resources.n_res, T), dtype=float)
    for r, name in enumerate(resources.names):
        if resources.is_storage[r]:
            continue
        target = resources.cf_assumed[r]
        if name == "solar_pv":
            cf[r] = _normalize_to_cf(_solar_shape(), target)
        elif name in ("onshore_wind", "offshore_wind"):
            cf[r] = _normalize_to_cf(_wind_shape(), target)
        else:
            # Firm clean (nuclear, geothermal, hydro placeholder): flat at CF.
            cf[r] = np.full(T, min(target, 1.0))
    return cf


def profile_path(iso: str, year: int, profiles_dir: Path | None = None) -> Path:
    """Return the expected Parquet path for an ISO-year real profile."""
    base = profiles_dir if profiles_dir is not None else DEFAULT_PROFILES_DIR
    return Path(base) / f"{iso.upper()}_{year}.parquet"


def _load_real_profiles(path: Path) -> dict[str, np.ndarray]:
    """Load ``{resource: (T,) cf}`` from a per-ISO profile Parquet.

    The file carries long-format rows ``(hour, resource, cf)`` — one full 8760
    series per real-shaped resource (wind/solar/offshore). Firm-clean and
    storage resources are intentionally absent (they take flat/zero rows in
    :func:`build_cf_matrix`).

    Raises:
        ValueError: if a resource does not carry exactly ``HOURS_PER_YEAR``
            hours (a truncated/ragged file is a build error, not a silent gap).
    """
    import pandas as pd  # local import: keeps the synthetic path pandas-free

    df = pd.read_parquet(path)
    out: dict[str, np.ndarray] = {}
    for name, grp in df.groupby("resource"):
        series = grp.sort_values("hour")["cf"].to_numpy(dtype=float)
        if series.shape[0] != HOURS_PER_YEAR:
            raise ValueError(
                f"profile {path.name}: resource {name!r} has {series.shape[0]} "
                f"hours, expected {HOURS_PER_YEAR}"
            )
        out[str(name)] = np.clip(series, 0.0, 1.0)
    return out


def build_cf_matrix(
    resources: ResourceArrays,
    iso: str,
    year: int,
    *,
    profiles_dir: Path | None = None,
    required: bool = False,
) -> np.ndarray:
    """Return the ``(n_res, T)`` hourly CF matrix for ``resources``.

    Selection of the shape source is keyed by ``iso``:

    * ``iso == "SAMPLE"`` -> synthetic shapes (the data-free demo/test default),
      always, regardless of ``required``.
    * any other ISO -> load ``data/profiles/<ISO>_<year>.parquet`` (real
      market-sim-derived shapes). Resources present in the file take their real
      series; firm-clean resources not in the file stay flat at ``cf_assumed``;
      storage rows are zero. If the file is missing: warn and fall back to the
      full synthetic matrix when ``required=False`` (never crash); raise
      ``FileNotFoundError`` when ``required=True``.

    ``required`` defaults to ``False`` (the historical warn-and-fallback
    behavior). Callers that pinned an explicit shape vintage
    (``PortfolioConfig.profile_shape_year``) should pass ``required=True`` so a
    real run never silently substitutes synthetic shapes for a missing file.

    ``profiles_dir`` overrides the default profile directory (used by tests to
    point at committed fixtures, keeping CI data-free).

    Storage rows are always zero (availability is governed by SOC dynamics).
    """
    if iso == SAMPLE_ISO:
        return _synthetic_cf_matrix(resources)

    path = profile_path(iso, year, profiles_dir)
    if not path.exists():
        if required:
            raise FileNotFoundError(
                f"required CF profile missing at {path} for ISO={iso!r} "
                f"year={year} (profile_shape_year was set explicitly; build it "
                "with scripts/build_profiles.py, or unset profile_shape_year "
                "to allow the synthetic fallback)"
            )
        warnings.warn(
            f"no real CF profile at {path} for ISO={iso!r} year={year}; "
            "falling back to synthetic shapes",
            stacklevel=2,
        )
        return _synthetic_cf_matrix(resources)

    real = _load_real_profiles(path)
    T = HOURS_PER_YEAR
    cf = np.zeros((resources.n_res, T), dtype=float)
    for r, name in enumerate(resources.names):
        if resources.is_storage[r]:
            continue  # storage: zero CF row
        if name in real:
            cf[r] = real[name]
        else:
            # Firm clean (nuclear, geothermal, hydro) carries no measured wind/
            # solar shape -> flat at its assumed capacity factor, matching the
            # synthetic firm-clean treatment.
            cf[r] = np.full(T, min(resources.cf_assumed[r], 1.0))
    return cf
