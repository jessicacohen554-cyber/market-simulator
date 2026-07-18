"""Tests for EIA-930 demand loading, including the T&D loss gross-up."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_sim.config.iso_configs import get_iso_config
from market_sim.data.eia_loader import (
    load_demand,
    neiso_net_interchange,
    nyiso_net_interchange,
    pjm_net_interchange,
    pjm_zonal_interchange,
)
from scripts.data.curate_zonal_shares import parse_pjm_shares as pjm_zonal_load_shares

_TEST_YEAR = 2023


def test_pjm_net_interchange_is_export_positive():
    """PJM's measured interchange loads as a large positive net export."""
    ix = pjm_net_interchange(_TEST_YEAR)
    assert ix is not None
    assert ix.shape == (8760,)
    assert not np.isnan(ix).any()
    # PJM exported ~40 TWh (≈ +4,564 MW avg) in 2023 — export-positive.
    assert 3000.0 < ix.mean() < 6000.0


def test_pjm_demand_includes_net_export():
    """PJM demand carries internal load *plus* the measured net export.

    The fleet must generate the ~40 TWh PJM actually exported, so total demand
    exceeds the internal-load-only allocation by the net interchange.
    """
    pjm = get_iso_config("PJM")
    demand = load_demand("PJM", _TEST_YEAR, pjm).sum(axis=0)
    ix = pjm_net_interchange(_TEST_YEAR)
    # Total served ≈ internal load + net export; the export is a real uplift.
    assert demand.mean() > 90_000.0  # ~94 GW incl. export vs ~89 GW load-only
    np.testing.assert_allclose(demand.mean(), 89_400 + ix.mean(), rtol=0.03)


def test_pjm_demand_can_exclude_interchange():
    """``include_interchange=False`` returns internal load only.

    Callers serving interchange through the priced import/export node
    (forward scenarios, ``--priced-interchange`` backcasts) must keep the
    measured schedule out of demand or the export would be counted twice.
    """
    pjm = get_iso_config("PJM")
    with_ix = load_demand("PJM", _TEST_YEAR, pjm).sum(axis=0)
    without = load_demand("PJM", _TEST_YEAR, pjm, include_interchange=False).sum(axis=0)
    # load_demand applies the per-border-zone attribution, so the uplift it
    # removes is the zonal series (which, unlike the scalar, leaves the DST
    # gap hour at zero).
    zx = pjm_zonal_interchange(_TEST_YEAR, pjm.zone_names).sum(axis=0)
    np.testing.assert_allclose(with_ix - without, zx, atol=1e-6)


def test_nyiso_net_interchange_is_import_negative():
    """NYISO's measured interchange loads as a steady net import (negative).

    EIA's ``Total interchange`` is already export-positive, so a net importer
    like NYISO (~16% of load in 2023) reads negative with no sign flip.
    """
    ix = nyiso_net_interchange(_TEST_YEAR)
    assert ix is not None
    assert ix.shape == (8760,)
    assert not np.isnan(ix).any()
    # NYISO imported ~23 TWh (≈ −2,677 MW avg) in 2023 — import-negative.
    assert -4000.0 < ix.mean() < -1500.0


def test_neiso_net_interchange_is_import_negative():
    """NEISO's measured interchange loads as a steady net import (negative)."""
    ix = neiso_net_interchange(2024)
    assert ix is not None
    assert ix.shape == (8760,)
    assert not np.isnan(ix).any()
    # ISO-NE imported ~10 TWh (≈ −1,175 MW avg) in 2024 — import-negative.
    assert -2500.0 < ix.mean() < -500.0


def test_nyiso_demand_serves_measured_import_by_default():
    """NYISO demand nets the measured import wedge, lowering served load.

    A net importer's schedule is negative, so serving it reduces the residual
    the in-state fleet must generate (the import wedge that would otherwise be
    over-generated as internal gas — P9 / playbook §8.2).
    """
    nyiso = get_iso_config("NYISO")
    with_ix = load_demand("NYISO", _TEST_YEAR, nyiso).sum(axis=0)
    without = load_demand("NYISO", _TEST_YEAR, nyiso, include_interchange=False).sum(
        axis=0
    )
    ix = nyiso_net_interchange(_TEST_YEAR)
    # The default path serves *less* than internal load by the import wedge.
    assert with_ix.sum() < without.sum()
    np.testing.assert_allclose(with_ix - without, ix, atol=1e-6)


def test_neiso_demand_serves_measured_import_by_default():
    """NEISO demand nets the measured import wedge, lowering served load."""
    neiso = get_iso_config("NEISO")
    with_ix = load_demand("NEISO", 2024, neiso).sum(axis=0)
    without = load_demand("NEISO", 2024, neiso, include_interchange=False).sum(axis=0)
    ix = neiso_net_interchange(2024)
    assert with_ix.sum() < without.sum()
    np.testing.assert_allclose(with_ix - without, ix, atol=1e-6)


def test_pjm_zonal_shares_sum_to_one_each_hour():
    """The per-zone hourly load shares partition system load every hour."""
    pjm = get_iso_config("PJM")
    shares = pjm_zonal_load_shares(_TEST_YEAR, pjm.zone_names)
    assert shares.shape == (pjm.n_zones, 8760)
    np.testing.assert_allclose(shares.sum(axis=0), 1.0, atol=1e-9)


def test_loss_factor_applied():
    """Demand with td_loss_factor > 0 is scaled up by (1 + factor)."""
    # CAISO's load_demand is a pure load-share split, so the gross-up is a
    # clean proportional scaling. ERCOT additionally nets DC-tie
    # interchange, a transmission flow that is not loss-grossed.
    base = load_demand("CAISO", _TEST_YEAR)
    grossed = load_demand("CAISO", _TEST_YEAR, td_loss_factor=0.058)
    np.testing.assert_allclose(grossed, base * 1.058)


def test_loss_factor_zero_is_noop():
    """A zero loss factor leaves demand unchanged."""
    base = load_demand("ERCOT", _TEST_YEAR)
    same = load_demand("ERCOT", _TEST_YEAR, td_loss_factor=0.0)
    np.testing.assert_array_equal(base, same)
