"""Raw <-> clean parity for the model's fleet + AS-withholding consumption seam.

The model can source its generator fleet attributes and its ancillary-service
reserve-withholding inputs either from ``data/raw`` (default) or from the curated
``data/clean`` tree, gated on the ``MARKET_SIM_USE_CLEAN`` environment variable
(see :func:`market_sim.data.fleet._use_clean`). These tests assert the two paths
agree on a small slice — the whole point of the migration is that flipping the
switch changes the *source*, not the numbers.

They are integration tests over the committed raw extracts and a regenerated
clean tree, so they are marked ``slow``/``integration`` and skip cleanly when
either side is absent (the clean tree is gitignored — regenerate it first with
``python scripts/regenerate_clean.py fleet ancillary-services``).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.paths import RAW_DATA_DIR, active_eia860_dir
from market_sim.data import fleet
from market_sim.data.fleet import (
    EIA_860_PARQUET_NAME,
    load_as_reserve_withholding_mw,
    load_fleet_from_csv,
)
from scripts.lib import clean_io
from tests.helpers import requires_raw

pytestmark = [pytest.mark.slow, pytest.mark.integration]

# Slice under test. PJM goes through the EIA-860 generator-parquet path on both
# raw and clean sides (ERCOT uses the CAMPD-bin fleet, a different source), and
# ERCOT 2025 is the year whose clean cleared-MW coverage overlaps the committed
# raw ``ercot_<year>_as_up_mw`` withholding series.
_FLEET_ISO = "PJM"
_AS_ISO = "ERCOT"
_AS_YEAR = 2025
_HOURS = 8760

_CLEAN_FLEET_YEAR = fleet._clean_fleet_year(active_eia860_dir())


# ---------------------------------------------------------------------------
# fleet attributes: clean vs raw
# ---------------------------------------------------------------------------
@requires_raw(active_eia860_dir() / EIA_860_PARQUET_NAME)
@pytest.mark.skipif(
    not clean_io.clean_exists("fleet", year=_CLEAN_FLEET_YEAR),
    reason="clean fleet slice absent — run scripts/regenerate_clean.py fleet",
)
def test_fleet_nameplate_and_fuel_parity(monkeypatch):
    """Clean fleet matches the raw loader on nameplate + fuel/prime-mover mapping.

    Both sides go through the same ``_rows_to_generators`` pipeline, so the
    clean-derived ``Generator`` objects must agree with the raw ones on
    ``pmax_mw`` (nameplate/summer capacity) and the fuel/prime-mover-driven
    classification (``fuel_type`` and ``plant_group``) for every unit the two
    fleets share.
    """
    # The raw loader writes a binned-fleet side cache into data/raw; neuter it so
    # the test never mutates data/raw.
    monkeypatch.setattr(fleet, "_cache_binned_fleet", lambda *a, **k: None)

    monkeypatch.delenv(fleet.USE_CLEAN_ENV, raising=False)
    raw = {g.unit_id: g for g in load_fleet_from_csv(_FLEET_ISO)}

    monkeypatch.setenv(fleet.USE_CLEAN_ENV, "1")
    clean = {g.unit_id: g for g in load_fleet_from_csv(_FLEET_ISO)}

    common = sorted(set(raw) & set(clean))
    # A real, substantial overlap (not a degenerate empty intersection).
    assert len(common) > 500

    nameplate_mismatch = [
        u for u in common if abs(raw[u].pmax_mw - clean[u].pmax_mw) > 1e-6
    ]
    fuel_mismatch = [u for u in common if raw[u].fuel_type != clean[u].fuel_type]
    group_mismatch = [u for u in common if raw[u].plant_group != clean[u].plant_group]
    assert not nameplate_mismatch, f"nameplate differs for {nameplate_mismatch[:5]}"
    assert not fuel_mismatch, f"fuel_type differs for {fuel_mismatch[:5]}"
    assert not group_mismatch, f"plant_group differs for {group_mismatch[:5]}"


# ---------------------------------------------------------------------------
# AS-withholding: clean vs raw
# ---------------------------------------------------------------------------
def _model_clock_fold(local_ts: pd.Series, values: np.ndarray, year: int) -> np.ndarray:
    """Fold a local-time MW series onto the fleet's non-leap 8760-hour clock.

    The same reduction the clean reader and ``build_ercot_as_withholding`` apply
    — used here to place a single raw product column on the clock for a per-
    product comparison.
    """
    work = pd.DataFrame(
        {"ts": pd.to_datetime(local_ts), "mw": np.asarray(values, float)}
    )
    keep = (work["ts"].dt.year == year) & ~(
        (work["ts"].dt.month == 2) & (work["ts"].dt.day == 29)
    )
    work = work[keep]
    grouped = work.groupby(
        [work["ts"].dt.month, work["ts"].dt.day, work["ts"].dt.hour]
    )["mw"].mean()
    grouped.index.names = ["month", "day", "hour"]
    return grouped.reindex(fleet._AS_MODEL_INDEX).to_numpy(dtype=float)


@requires_raw(RAW_DATA_DIR / "ercot-AS" / f"ercot_{_AS_YEAR}_as_up_mw.parquet")
@pytest.mark.skipif(
    not clean_io.clean_exists(
        "ancillary-services", iso=_AS_ISO, market="DAM", year=_AS_YEAR
    ),
    reason="clean AS slice absent — run scripts/regenerate_clean.py ancillary-services",
)
def test_as_reserve_withholding_total_parity(monkeypatch):
    """Clean upward-AS reconstruction matches the raw ``as_up_mw`` loader.

    On the hours the clean cleared-MW table covers, the clean-reconstructed
    system-wide upward-AS series equals the raw withholding series the model
    consumes today (the raw ``ercot_<year>_as_up_mw`` parquet).
    """
    load_as_reserve_withholding_mw.cache_clear()
    monkeypatch.delenv(fleet.USE_CLEAN_ENV, raising=False)
    raw = load_as_reserve_withholding_mw(_AS_YEAR, _HOURS, _AS_ISO)

    load_as_reserve_withholding_mw.cache_clear()
    monkeypatch.setenv(fleet.USE_CLEAN_ENV, "1")
    clean = load_as_reserve_withholding_mw(_AS_YEAR, _HOURS, _AS_ISO)
    load_as_reserve_withholding_mw.cache_clear()

    assert raw is not None and clean is not None
    assert raw.shape == clean.shape == (_HOURS,)

    covered = clean > 0.0
    assert covered.sum() >= 24, "too few clean-covered hours to compare"
    np.testing.assert_allclose(clean[covered], raw[covered], rtol=1e-6, atol=1e-3)


@requires_raw(RAW_DATA_DIR / "ercot-AS" / f"ercot_{_AS_YEAR}_as_up_mw.parquet")
@pytest.mark.skipif(
    not clean_io.clean_exists(
        "ancillary-services", iso=_AS_ISO, market="DAM", year=_AS_YEAR
    ),
    reason="clean AS slice absent — run scripts/regenerate_clean.py ancillary-services",
)
def test_as_single_product_spin_parity():
    """One AS product (spin) matches between clean and the raw per-tag columns.

    The clean schema's ``spin_mw`` (ERCOT RRS family) must equal the raw
    withholding parquet's responsive-reserve columns (``rrspfr + rrsffr +
    rrsufr``) on the clean-covered hours, on the shared model clock.
    """
    clean_df = clean_io.read_clean(
        "ancillary-services", iso=_AS_ISO, market="DAM", year=_AS_YEAR
    )
    clean_df = clean_df[clean_df["zone"].astype("string").str.strip() == "SYSTEM"]
    spin = clean_df["spin_mw"]
    covered = clean_df.loc[spin.notna()]
    assert len(covered) >= 24, "too few clean-covered spin hours to compare"
    clean_spin = _model_clock_fold(
        covered["interval_start_local"], covered["spin_mw"].to_numpy(float), _AS_YEAR
    )

    raw = pd.read_parquet(
        RAW_DATA_DIR / "ercot-AS" / f"ercot_{_AS_YEAR}_as_up_mw.parquet"
    )
    raw_spin = (raw["rrspfr_mw"] + raw["rrsffr_mw"] + raw["rrsufr_mw"]).to_numpy(
        dtype=float
    )

    hours = ~np.isnan(clean_spin)
    assert hours.sum() >= 24
    np.testing.assert_allclose(clean_spin[hours], raw_spin[hours], rtol=1e-6, atol=1e-3)
