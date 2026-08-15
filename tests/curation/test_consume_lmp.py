"""Parity test for the clean-backed neighbor-LMP read path.

:func:`market_sim.data.neighbor_price.neighbor_lmp_hourly` loads a modeled
neighbor's realized hourly system LMP through one of two interchangeable
backends — the committed realized-LMP product under ``paths.CALIBRATION_DIR``
(default) or the curated ``data/clean`` tree via ``clean_io.read_clean``,
selected by the ``MARKET_SIM_USE_CLEAN`` environment flag. This asserts the two
backends return the same ``lmp_usd_per_mwh`` series within float tolerance.

What it actually guards is that the clean-backed reduction still reproduces the
realized product's **clock** (``interval_start_utc`` on the ISO's fixed standard
offset, not the DST-prevailing ``interval_start_local``) and its **hub
definition** (per-ISO node set and weights). It is the only instrument in the
repo that can detect either drifting — a one-hour clock shift shows up here as a
several-hundred-$/MWh disagreement, which is exactly how F6 was found
(docs/FINDING-f6-lmp-backend-parity-2026-08-11.md).

Marked slow/integration: it reads full-year data products rather than a
synthetic fixture, and is skipped when either backend's inputs are absent (the
raw realized product, or the clean partition — regenerate the latter with
``python scripts/regenerate_clean.py lmp``).
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config import paths
from market_sim.data import neighbor_price
from market_sim.data.neighbor_price import USE_CLEAN_ENV, neighbor_lmp_hourly
from tests.helpers import requires_raw

pytestmark = [pytest.mark.slow, pytest.mark.integration]

# One iso/market/year where both backends have full-year coverage: PJM's clean
# LMP carries exactly the trading hubs the realized product hub-averages.
_ISO = "PJM"
_RUN = "rt"  # real-time -> clean RTM partition
_MARKET = "RTM"
_YEAR = 2024

# The two reductions agree on this partition to 1.4e-05 — float32 storage in the
# realized product, and nothing else. The tolerance sits ~700x above that
# deliberately: it is sized to CATCH a clock or
# hub-definition mismatch, never to absorb one. A clock shift lands at
# $408/MWh here, so anything that fails this test is a real defect — fix the
# reduction, do not widen ``_TOL`` (F6 option C, rejected on that ground).
#
# It has not always read this way. Until 2026-08-13 the comment claimed float32
# was "the only source of disagreement", which was true when written
# (2026-06-19) and stopped being true on 2026-07-15 when the realized product
# moved to the standard clock and this consumer did not — by then float32
# accounted for 0.0000033% of the gap.
_TOL = 1e-2


def _clean_available() -> bool:
    return paths.clean_path("lmp", iso=_ISO, market=_MARKET, year=_YEAR).is_file()


@requires_raw(paths.CALIBRATION_DIR / f"actual_lmp_hourly_{_ISO}.parquet")
@pytest.mark.skipif(
    not _clean_available(),
    reason="clean lmp partition absent (run scripts/regenerate_clean.py lmp)",
)
def test_clean_backed_lmp_matches_raw_loader(monkeypatch):
    """Clean-backed lmp_usd_per_mwh matches the existing raw loader within tol."""
    # Default backend (raw realized product).
    monkeypatch.delenv(USE_CLEAN_ENV, raising=False)
    assert not neighbor_price._use_clean()
    raw = neighbor_lmp_hourly(_ISO, _YEAR, _RUN)
    assert raw is not None, "raw backend returned no series"

    # Clean-backed backend, opted in via the environment flag.
    monkeypatch.setenv(USE_CLEAN_ENV, "1")
    assert neighbor_price._use_clean()
    clean = neighbor_lmp_hourly(_ISO, _YEAR, _RUN, market=_MARKET)
    assert clean is not None, "clean backend returned no series"

    assert raw.shape == clean.shape == (neighbor_price._LMP_HOURS_PER_YEAR,)
    assert not np.isnan(clean).any()
    assert np.allclose(raw, clean, atol=_TOL, rtol=0.0), (
        f"max |raw-clean| = {np.nanmax(np.abs(raw - clean)):.6g} exceeds {_TOL}"
    )


def test_clean_path_off_by_default(monkeypatch):
    """The clean backend stays gated OFF unless MARKET_SIM_USE_CLEAN is truthy."""
    monkeypatch.delenv(USE_CLEAN_ENV, raising=False)
    assert neighbor_price._use_clean() is False
    for falsy in ("", "0", "false", "no", "off"):
        monkeypatch.setenv(USE_CLEAN_ENV, falsy)
        assert neighbor_price._use_clean() is False
    for truthy in ("1", "true", "YES", "On"):
        monkeypatch.setenv(USE_CLEAN_ENV, truthy)
        assert neighbor_price._use_clean() is True
