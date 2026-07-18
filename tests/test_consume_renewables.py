"""Parity test for the clean-backed renewables read path.

The model's hourly GEN/HSL frame (:func:`market_sim.data.renewables.load_hsl_hourly`)
can be sourced from the raw per-year HSL parquet (the shipped default) or, when
``MARKET_SIM_USE_CLEAN`` is set, from the curated ``data/clean/renewables``
tree via the shared read seam ``scripts.lib.clean_io.read_clean``. The clean
table is a pure unpivot of the wide HSL frame, so the two sources must agree
bit-for-bit; this test asserts that for one ISO/year.

Marked slow/integration because it touches the real ``data/raw`` and
``data/clean`` trees rather than a synthetic fixture. It is skipped when the
raw HSL parquet is absent (no data to compare) or when the clean partition has
not been regenerated (run ``python scripts/regenerate_clean.py renewables``).
"""

from __future__ import annotations

import numpy as np
import pytest

import market_sim.data.renewables as renewables
from market_sim.config.constants import HOURS_PER_YEAR

# One ISO/year for the parity assertion. CAISO 2024 ships a full-footprint HSL
# parquet (scripts/data/build_caiso_hsl.py), so the GEN/HSL series flow through the
# loader without the partial-footprint coverage reconciliation.
PARITY_ISO: str = "CAISO"
PARITY_YEAR: int = 2024

# MW tolerance: the clean path is an exact round-trip of the same float64
# values, so equality is expected; the tolerance only guards parquet/float
# round-trip noise.
_TOL_MW: float = 1e-6


def _raw_hsl_present(iso: str, year: int) -> bool:
    path = renewables._hsl_file(iso, year)
    return path is not None and path.exists()


def _clean_present(iso: str, year: int) -> bool:
    return renewables._clean_io().clean_exists("renewables", iso=iso, year=year)


@pytest.mark.slow
@pytest.mark.integration
def test_clean_hsl_matches_raw_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clean-backed GEN/HSL equals the raw loader for one ISO/year."""
    if not _raw_hsl_present(PARITY_ISO, PARITY_YEAR):
        pytest.skip(
            f"raw HSL parquet absent for {PARITY_ISO} {PARITY_YEAR}; nothing to compare"
        )
    if not _clean_present(PARITY_ISO, PARITY_YEAR):
        pytest.skip(
            f"clean renewables partition absent for {PARITY_ISO} {PARITY_YEAR}; "
            "run `python scripts/regenerate_clean.py renewables`"
        )

    # Raw path (flag OFF) is the reference.
    monkeypatch.delenv(renewables._USE_CLEAN_ENV, raising=False)
    raw = renewables.load_hsl_hourly(PARITY_ISO, PARITY_YEAR)
    assert raw is not None and len(raw) == HOURS_PER_YEAR

    # Clean-backed path (flag ON).
    monkeypatch.setenv(renewables._USE_CLEAN_ENV, "1")
    clean = renewables.load_hsl_hourly(PARITY_ISO, PARITY_YEAR)
    assert clean is not None and len(clean) == HOURS_PER_YEAR

    # Same wide schema (hour + wind/solar gen & hsl), same values per column.
    assert list(clean.columns) == list(raw.columns)
    for col in raw.columns:
        np.testing.assert_allclose(
            clean[col].to_numpy(dtype=float),
            raw[col].to_numpy(dtype=float),
            atol=_TOL_MW,
            rtol=0.0,
            err_msg=f"{PARITY_ISO} {PARITY_YEAR}: clean/raw disagree on {col!r}",
        )


@pytest.mark.slow
@pytest.mark.integration
def test_clean_hsl_potential_matches_raw_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The dispatch's uncurtailed-potential series is identical under both sources."""
    if not _raw_hsl_present(PARITY_ISO, PARITY_YEAR):
        pytest.skip(f"raw HSL parquet absent for {PARITY_ISO} {PARITY_YEAR}")
    if not _clean_present(PARITY_ISO, PARITY_YEAR):
        pytest.skip(
            f"clean renewables partition absent for {PARITY_ISO} {PARITY_YEAR}; "
            "run `python scripts/regenerate_clean.py renewables`"
        )

    for fuel in renewables._RENEWABLE_FUELS:
        monkeypatch.delenv(renewables._USE_CLEAN_ENV, raising=False)
        raw_mw = renewables.hsl_potential_mw(PARITY_ISO, PARITY_YEAR, fuel)
        monkeypatch.setenv(renewables._USE_CLEAN_ENV, "1")
        clean_mw = renewables.hsl_potential_mw(PARITY_ISO, PARITY_YEAR, fuel)
        assert raw_mw is not None and clean_mw is not None
        np.testing.assert_allclose(
            clean_mw,
            raw_mw,
            atol=_TOL_MW,
            rtol=0.0,
            err_msg=f"{PARITY_ISO} {PARITY_YEAR} {fuel}: hsl_potential_mw mismatch",
        )


@pytest.mark.slow
@pytest.mark.integration
def test_flag_off_uses_raw_when_clean_absent() -> None:
    """With the flag OFF the raw loader is used regardless of the clean tree."""
    if not _raw_hsl_present(PARITY_ISO, PARITY_YEAR):
        pytest.skip(f"raw HSL parquet absent for {PARITY_ISO} {PARITY_YEAR}")
    # Default (unset) must not raise and must return the raw full-year frame.
    raw = renewables.load_hsl_hourly(PARITY_ISO, PARITY_YEAR)
    assert raw is not None and len(raw) == HOURS_PER_YEAR
