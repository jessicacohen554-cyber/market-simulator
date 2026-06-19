"""Parity test for the opt-in clean-backed delivered fuel-price read path.

The model can source delivered fuel prices from the curated ``data/clean`` tree
(:func:`scripts.lib.clean_io.read_clean`) instead of the raw
``data/raw/gas-prices`` CSVs, gated behind the ``MARKET_SIM_USE_CLEAN``
environment flag (OFF by default). This asserts the two paths agree on the real
Henry Hub series — the only curated hub today (scripts/curate_fuel_prices.py):

  * the clean-backed daily loader reproduces the existing raw loader exactly;
  * the env-gated dispatch in :func:`market_sim.data.fuel._henry_hub_daily`
    routes to clean only when the flag is set, and to raw by default; and
  * the public daily-shape consumer (:func:`~market_sim.data.fuel.gas_daily_shape_factors`)
    is byte-identical under raw vs clean.

Marked slow/integration (reads the real data tree and curates a clean slice from
it) and skipped when the raw ``henry_hub_daily.csv`` is absent. The clean slice
is built into a redirected, temporary ``CLEAN_DIR`` so the test never writes the
repo's gitignored ``data/clean`` tree.
"""
from __future__ import annotations

import numpy as np
import pytest

from market_sim.config import paths
from market_sim.data import fuel
from scripts import curate_fuel_prices

pytestmark = [pytest.mark.slow, pytest.mark.integration]

_RAW_HH_DAILY = paths.GAS_PRICES_DIR / "henry_hub_daily.csv"

requires_raw = pytest.mark.skipif(
    not _RAW_HH_DAILY.is_file(),
    reason=f"raw Henry Hub daily series absent at {_RAW_HH_DAILY}",
)


@pytest.fixture()
def clean_tree(tmp_path, monkeypatch):
    """Curate the fuel-prices clean slice from the *real* raw CSV in a tmp tree.

    Redirects ``CLEAN_DIR`` (mirroring tests/test_curate_fuel_prices.py) so the
    curation and every clean read land in a temp dir, never the repo's
    ``data/clean``. Curates the real ``data/raw/gas-prices`` into it and clears
    fuel.py's clean cache so the redirect takes effect.
    """
    monkeypatch.setattr(paths, "CLEAN_DIR", tmp_path / "clean")
    fuel._HH_DAILY_CLEAN_CACHE.clear()
    fuel._HH_DAILY_CACHE.clear()
    # Default gas_dir == the real data/raw/gas-prices (skipif guards its absence).
    curate_fuel_prices.curate()
    yield
    fuel._HH_DAILY_CLEAN_CACHE.clear()
    fuel._HH_DAILY_CACHE.clear()


@requires_raw
def test_clean_daily_matches_raw_loader(clean_tree, monkeypatch):
    """The clean-backed daily Henry Hub series equals the raw-CSV loader."""
    monkeypatch.delenv(fuel._USE_CLEAN_ENV, raising=False)  # raw default
    raw = fuel._henry_hub_daily(None)  # reads raw henry_hub_daily.csv
    clean = fuel._clean_fuel_price_daily(*fuel._HENRY_HUB_CLEAN_KEY)

    assert clean, "expected a non-empty real Henry Hub daily series"
    assert clean == raw


@requires_raw
def test_default_is_raw_not_clean(clean_tree, monkeypatch):
    """With the flag unset, _henry_hub_daily serves raw, not the clean tree."""
    monkeypatch.delenv(fuel._USE_CLEAN_ENV, raising=False)
    fuel._HH_DAILY_CACHE.clear()
    fuel._HH_DAILY_CLEAN_CACHE.clear()

    out = fuel._henry_hub_daily(None)

    # The raw path caches under the raw CSV path; the clean cache stays untouched.
    assert fuel.HENRY_HUB_DAILY_PATH in fuel._HH_DAILY_CACHE
    assert not fuel._HH_DAILY_CLEAN_CACHE
    assert out == fuel._HH_DAILY_CACHE[fuel.HENRY_HUB_DAILY_PATH]


@requires_raw
def test_env_flag_routes_to_clean(clean_tree, monkeypatch):
    """With MARKET_SIM_USE_CLEAN set, _henry_hub_daily serves the clean series."""
    clean = fuel._clean_fuel_price_daily(*fuel._HENRY_HUB_CLEAN_KEY)

    monkeypatch.setenv(fuel._USE_CLEAN_ENV, "1")
    fuel._HH_DAILY_CLEAN_CACHE.clear()
    routed = fuel._henry_hub_daily(None)

    assert routed == clean


@requires_raw
def test_gas_daily_shape_factors_parity(clean_tree, monkeypatch):
    """The public daily-shape consumer is byte-identical under raw vs clean."""
    year, hours = 2024, fuel.HOURS_PER_YEAR

    monkeypatch.delenv(fuel._USE_CLEAN_ENV, raising=False)
    fuel._HH_DAILY_CACHE.clear()
    raw_factors = fuel.gas_daily_shape_factors(year, hours)

    monkeypatch.setenv(fuel._USE_CLEAN_ENV, "1")
    fuel._HH_DAILY_CLEAN_CACHE.clear()
    clean_factors = fuel.gas_daily_shape_factors(year, hours)

    np.testing.assert_array_equal(raw_factors, clean_factors)
