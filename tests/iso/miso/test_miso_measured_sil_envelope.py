"""miso-255 ``miso_import_sil_measured_envelope``: the aggregate-SIL replacement.

The 8,700 MW bidirectional ``MISO_simultaneous_import`` scalar is MISO's
published Capacity Import Limit — a PRA/LOLE accreditation construct — used as
the hourly energy bound in both directions. The flag REPLACES it with MISO's own
measured coincident boundary transfer envelope, per direction (rule 14
``[R-ACCURATE]``, rule 19 ``[R-ONE-MECH]``).
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia930.envelopes import measured_boundary_transfer_envelope
from market_sim.model.interchange.core import build_interface_groups
from market_sim.model.interchange.import_nodes import extend_with_import_node
from market_sim.model.interchange.miso import apply_miso_measured_sil_envelope
from market_sim.model.interchange.spec import EXTERNAL_SIMULTANEOUS_LIMITS

T = 8760
SIL_NAME, SIL_MW, _ = EXTERNAL_SIMULTANEOUS_LIMITS["MISO"]


@pytest.fixture(scope="module")
def miso_groups():
    cfg = extend_with_import_node(get_iso_config("MISO"))
    return cfg, build_interface_groups(cfg.links, cfg.interface_limits)


def test_default_is_off_and_registered():
    """Default off, so every pre-existing bundle replays byte-identically."""
    assert ScenarioConfig(iso="MISO").miso_import_sil_measured_envelope is False


def test_replaces_exactly_one_group_and_leaves_the_others_untouched(miso_groups):
    """Rule 19 [R-ONE-MECH]: it REPLACES the aggregate limit, never stacks."""
    cfg, groups = miso_groups
    out, info = apply_miso_measured_sil_envelope(
        groups, cfg, 2021, T, percentile=None, hour_ending_key=True
    )
    assert info is not None
    assert len(out) == len(groups)
    idx = [lim.name for lim in cfg.interface_limits].index(SIL_NAME)
    for i, (before, after) in enumerate(zip(groups, out)):
        if i == idx:
            continue
        assert np.array_equal(before[0], after[0])
        assert np.array_equal(np.atleast_1d(before[1]), np.atleast_1d(after[1]))
    # the replaced group carries per-hour bounds and an explicit reverse cap
    link_idx, cap, two_way, lower, signs = out[idx]
    assert np.array_equal(link_idx, groups[idx][0])
    assert np.asarray(cap).shape == (T,)
    assert np.asarray(lower).shape == (T,)
    assert two_way is False  # the explicit reverse bound overrides it
    assert np.asarray(signs).size == np.asarray(link_idx).size


def test_the_envelope_is_the_measured_one_not_a_new_number(miso_groups):
    """Zero free parameters: the group's bounds ARE the estimator's output."""
    cfg, groups = miso_groups
    out, _ = apply_miso_measured_sil_envelope(
        groups, cfg, 2021, T, percentile=None, hour_ending_key=True
    )
    imp, exp = measured_boundary_transfer_envelope(
        "MISO", 2021, T, percentile=None, hour_ending_key=True
    )
    idx = [lim.name for lim in cfg.interface_limits].index(SIL_NAME)
    assert np.array_equal(np.asarray(out[idx][1]), imp)
    assert np.array_equal(np.asarray(out[idx][3]), exp)


def test_coincident_is_tighter_than_the_summed_per_seam_envelope():
    """The whole point of aggregating coincidently: the seams do not co-peak."""
    from market_sim.data.eia930.envelopes import measured_seam_import_envelope

    per_seam = measured_seam_import_envelope(
        "MISO", 2021, T, percentile=None, direction="import", hour_ending_key=True
    )
    coincident, _ = measured_boundary_transfer_envelope(
        "MISO", 2021, T, percentile=None, hour_ending_key=True
    )
    summed = np.sum([v[:T] for v in per_seam.values()], axis=0)
    assert coincident.sum() < summed.sum()


def test_envelope_is_a_ceiling_not_a_pin():
    """Rule 13 [R-MEASURED]: the measured flow must CLEAR BELOW the envelope.

    An envelope the measured flow never exceeds would be the flow itself
    wearing a capability name. It is exceeded in >5 % of the hours of every
    scored year, with positive mean headroom.
    """
    from market_sim.data.eia930.actuals import load_eia_hourly_benchmark

    for year in (2021, 2023, 2025):
        imp, _ = measured_boundary_transfer_envelope(
            "MISO", year, T, percentile=None, hour_ending_key=True
        )
        meas = -np.asarray(
            load_eia_hourly_benchmark("MISO", year)["interchange"], dtype=float
        )[:T]
        assert (meas > imp).mean() > 0.05, year
        assert imp.mean() > meas.mean(), year


def test_non_miso_iso_is_a_noop():
    """MISO-only: no seam-DIBA map -> None, so the caller keeps its scalar."""
    assert measured_boundary_transfer_envelope("PJM", 2023, T) is None
    cfg = extend_with_import_node(get_iso_config("PJM"))
    groups = build_interface_groups(cfg.links, cfg.interface_limits)
    out, info = apply_miso_measured_sil_envelope(groups, cfg, 2023, T)
    assert info is None
    assert out is groups


def test_unresolvable_year_keeps_the_declared_scalar(miso_groups):
    """A forecast year has no measured record -> byte-identical passthrough."""
    cfg, groups = miso_groups
    out, info = apply_miso_measured_sil_envelope(groups, cfg, 2099, T)
    assert info is None
    assert out is groups


def test_arming_moves_the_cache_key():
    """A different interface row is a different dispatch and must re-key."""
    base = ScenarioConfig(iso="MISO", mode="backcast", hindcast=True)
    armed = base.with_overrides(miso_import_sil_measured_envelope=True)
    assert base.cache_key() != armed.cache_key()
