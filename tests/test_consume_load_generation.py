"""Parity tests for the clean-data consumption seam in ``eia_loader``.

When ``MARKET_SIM_USE_CLEAN`` is set, :func:`load_demand` sources the system
demand from the curated clean ``load`` dataset and
:func:`load_eia_hourly_benchmark` sources its per-fuel generation from the clean
``generation`` dataset, instead of the raw EIA-930 ``<BA> hourly`` extract. These
tests assert that, for one ISO/year, the clean-backed series reproduce the raw
loader within tolerance — the gate must be transparent where the clean feed is a
faithful reconstruction of the raw one.

Marked ``slow`` / ``integration`` because they read the full-size raw and clean
parquet for a year. They skip when the raw extract is absent (nothing to compare
against) or the clean partition has not been regenerated
(``python scripts/regenerate_clean.py load generation``); the clean tree is
gitignored, so a bare checkout legitimately has neither.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.paths import EIA_HOURLY_DIR
from market_sim.data import eia_loader as L
from tests.helpers import requires_raw

pytestmark = [pytest.mark.slow, pytest.mark.integration]

# One ISO/year whose clean ``load`` + ``generation`` feeds are reconstructed
# from the same EIA-930 ``ERCO hourly`` extract the raw loader reads, so the
# clean-backed and raw series are expected to match exactly. ERCOT 2023 is a
# clean, gap-free full year (no leap day, no missing meter hours).
_ISO = "ERCOT"
_BA = "ERCO"
_YEAR = 2023

# The clean ``load_mw`` / ``generation_mw`` are the raw EIA-930 values verbatim,
# so a tight tolerance is appropriate; a small absolute floor absorbs only
# float round-trip through Parquet.
_TOL = 1e-6


def _clean_absent(datatype: str) -> bool:
    """Whether the regenerated clean partition is missing (or the seam is)."""
    seam = L._read_clean_seam()
    if seam is None:
        return True
    _, clean_exists = seam
    return not clean_exists(datatype, iso=_ISO, year=_YEAR)


@requires_raw(EIA_HOURLY_DIR / f"{_BA} hourly.parquet")
@pytest.mark.skipif(
    _clean_absent("load"),
    reason="clean load partition absent (run scripts/regenerate_clean.py load)",
)
def test_clean_demand_matches_raw_loader(monkeypatch):
    """Clean-backed ``load_demand`` reproduces the raw loader within tolerance."""
    monkeypatch.delenv("MARKET_SIM_USE_CLEAN", raising=False)
    raw = L.load_demand(_ISO, _YEAR)

    # The clean path must actually engage, otherwise the parity is vacuous.
    assert L._clean_system_demand(_ISO, _YEAR) is not None

    monkeypatch.setenv("MARKET_SIM_USE_CLEAN", "1")
    clean = L.load_demand(_ISO, _YEAR)

    assert clean.shape == raw.shape
    np.testing.assert_allclose(clean, raw, rtol=0.0, atol=_TOL)


@requires_raw(EIA_HOURLY_DIR / f"{_BA} hourly.parquet")
@pytest.mark.skipif(
    _clean_absent("generation"),
    reason="clean generation partition absent (run scripts/regenerate_clean.py generation)",
)
def test_clean_generation_matches_raw_benchmark(monkeypatch):
    """Clean-backed per-fuel ``generation_mw`` matches the raw hourly benchmark."""
    monkeypatch.delenv("MARKET_SIM_USE_CLEAN", raising=False)
    raw = L.load_eia_hourly_benchmark(_ISO, _YEAR)
    assert raw is not None

    clean_fuels = L._clean_generation_by_fuel(_ISO, _YEAR)
    assert clean_fuels, "clean generation reshape returned no per-fuel series"

    # Every clean-mapped fuel the benchmark also reports must match per hour.
    compared = [f for f in clean_fuels if f in raw]
    assert compared, "no overlapping fuels between clean and raw benchmark"
    for fuel in compared:
        np.testing.assert_allclose(
            clean_fuels[fuel],
            raw[fuel],
            rtol=0.0,
            atol=_TOL,
            err_msg=f"clean generation_mw mismatch for fuel {fuel!r}",
        )

    # And the gated public path overrides only those fuels, leaving the
    # aggregate net-generation / interchange series from the raw extract intact.
    monkeypatch.setenv("MARKET_SIM_USE_CLEAN", "1")
    gated = L.load_eia_hourly_benchmark(_ISO, _YEAR)
    for fuel in compared:
        np.testing.assert_allclose(gated[fuel], clean_fuels[fuel], rtol=0.0, atol=_TOL)
    for series in ("net_gen", "interchange"):
        if series in raw:
            np.testing.assert_allclose(gated[series], raw[series], rtol=0.0, atol=_TOL)
