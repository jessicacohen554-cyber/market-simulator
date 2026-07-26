"""NYISO measured-neighbor import pricing (``nyiso_import_hub_prices``).

The priced import node's non-firm tranches reprice at the measured hourly
neighbor Day-Ahead system LMP (PJM_west→PJM, ISONE_tie→NEISO, import_scarcity→
hourly max, export_surplus→hourly min − hurdle), replacing the static per-year
fitted ladder; HQ/IESO contract tranches and non-node rows are untouched, and
the injector is a byte-identical no-op for non-NYISO ISOs or when the measured
neighbor series are unavailable (forecast years).
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.model.transmission import (
    NYISO_IMPORT_HUB_HURDLE,
    inject_nyiso_import_hub_prices,
)

HOURS = 48


class _FA:
    """Minimal FleetArrays stand-in: the injector only reads unit_ids."""

    def __init__(self, unit_ids: list[str]):
        self.unit_ids = unit_ids


def _node_fleet() -> _FA:
    return _FA(
        [
            "NYISO_external_HQ_hydro",
            "NYISO_external_IESO_Ontario",
            "NYISO_external_PJM_west",
            "NYISO_external_ISONE_tie",
            "NYISO_external_import_scarcity",
            "NYISO_external_export_surplus",
            "ravenswood_st_1",
        ]
    )


@pytest.fixture()
def neighbor_series(monkeypatch):
    """Patch the neighbor-LMP loader with two distinct synthetic series."""
    pjm = np.linspace(20.0, 60.0, HOURS)
    ne = np.linspace(70.0, 30.0, HOURS)  # crosses PJM so max/min differ per hour

    def fake(iso, year, run="rt", **kwargs):
        if run != "da":
            return None  # exercise the DA-first path
        return {"PJM": pjm, "NEISO": ne}.get(iso)

    monkeypatch.setattr("market_sim.data.neighbor_price.neighbor_lmp_hourly", fake)
    return pjm, ne


def test_reprices_nonfirm_tranches_and_sink(neighbor_series):
    pjm, ne = neighbor_series
    fa = _node_fleet()
    mc = np.full((len(fa.unit_ids), HOURS), 99.0)
    assert inject_nyiso_import_hub_prices(fa, mc, "NYISO", 2024)
    h = NYISO_IMPORT_HUB_HURDLE
    np.testing.assert_allclose(mc[2], pjm + h)
    np.testing.assert_allclose(mc[3], ne + h)
    np.testing.assert_allclose(mc[4], np.maximum(pjm, ne) + h)
    np.testing.assert_allclose(mc[5], np.minimum(pjm, ne) - h)
    # Contract tranches (HQ/IESO) and the in-state generator stay on their mc.
    assert (mc[0] == 99.0).all() and (mc[1] == 99.0).all()
    assert (mc[6] == 99.0).all()


def test_seam_is_arbitrage_free(neighbor_series):
    """Export willingness-to-pay never exceeds any repriced import offer."""
    fa = _node_fleet()
    mc = np.full((len(fa.unit_ids), HOURS), 99.0)
    inject_nyiso_import_hub_prices(fa, mc, "NYISO", 2024)
    for import_row in (2, 3, 4):
        assert (mc[5] < mc[import_row]).all()


def test_noop_for_other_iso(neighbor_series):
    fa = _node_fleet()
    mc = np.full((len(fa.unit_ids), HOURS), 99.0)
    assert not inject_nyiso_import_hub_prices(fa, mc, "PJM", 2024)
    assert (mc == 99.0).all()


def test_noop_without_measured_series(monkeypatch):
    monkeypatch.setattr(
        "market_sim.data.neighbor_price.neighbor_lmp_hourly",
        lambda *a, **k: None,
    )
    fa = _node_fleet()
    mc = np.full((len(fa.unit_ids), HOURS), 99.0)
    assert not inject_nyiso_import_hub_prices(fa, mc, "NYISO", 2035)
    assert (mc == 99.0).all()


def test_rt_fallback_when_da_absent(monkeypatch):
    rt = np.full(HOURS, 42.0)

    def fake(iso, year, run="rt", **kwargs):
        return rt if run == "rt" else None

    monkeypatch.setattr("market_sim.data.neighbor_price.neighbor_lmp_hourly", fake)
    fa = _node_fleet()
    mc = np.full((len(fa.unit_ids), HOURS), 99.0)
    assert inject_nyiso_import_hub_prices(fa, mc, "NYISO", 2024)
    np.testing.assert_allclose(mc[2], rt + NYISO_IMPORT_HUB_HURDLE)


def test_real_parquets_resolve_backcast_years():
    """The committed neighbor LMP products cover every NYISO backcast year."""
    from market_sim.data.neighbor_price import neighbor_lmp_hourly

    for neighbor in ("PJM", "NEISO"):
        for year in (2023, 2024, 2025):
            s = neighbor_lmp_hourly(neighbor, year, "da")
            assert s is not None and s.shape[0] == 8760, (neighbor, year)
