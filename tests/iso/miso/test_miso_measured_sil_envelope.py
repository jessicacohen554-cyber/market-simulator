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


def test_the_backcast_path_consumes_the_flag_not_only_the_forecast_path():
    """The consumer must exist on run_calibration's OWN interface-group seam.

    THE DEFECT THIS GUARDS (miso-255): the flag was first wired only into
    ``runner.run_scenario_iso``, which is the FORECAST/scenario front end. The
    backcast/calibration path builds its own ``interface_groups`` in
    ``scripts/run_calibration.py`` and never enters that function, so a screen
    shard solved with the flag set and the arm silently inert — the same trap
    ``run_calibration.py``'s own ``caiso_endogenous_wecc_node`` comment records.
    A gated mechanism that no backcast reads is an unregistered tuning channel
    in spirit (rule 24 ``[R-REGISTRY]``).

    Asserted structurally rather than by solving: both entry points must
    reference the injector, and the backcast one must key it off the EFFECTIVE
    limit list (the MISO seasonal block rebuilds the groups from
    ``static_limits``, so indexing ``iso_config.interface_limits`` there would
    replace the wrong row).
    """
    import ast
    from pathlib import Path

    repo = Path(__file__).resolve().parents[3]
    backcast = (repo / "scripts/run_calibration.py").read_text()
    forecast = (repo / "src/market_sim/runner.py").read_text()

    assert "apply_miso_measured_sil_envelope" in backcast, (
        "the BACKCAST path (scripts/run_calibration.py) does not consume "
        "miso_import_sil_measured_envelope — a replay would solve with the "
        "arm silently inert"
    )
    assert "apply_miso_measured_sil_envelope" in forecast

    # the backcast call must pass the effective limit list, never the config's
    tree = ast.parse(backcast)
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and getattr(n.func, "id", getattr(n.func, "attr", None))
        == "apply_miso_measured_sil_envelope"
    ]
    assert len(calls) == 1, f"expected one backcast call site, found {len(calls)}"
    second = calls[0].args[1]
    assert isinstance(second, ast.Name) and second.id == "effective_interface_limits", (
        "the backcast call must key the named group off the list that BUILT "
        "the groups (effective_interface_limits), not iso_config.interface_limits"
    )


def test_accepts_a_bare_limit_list_the_backcast_form(miso_groups):
    """The backcast passes a LIST, the forecast an ISOConfig — both must work.

    The first repair of the wrong-path defect changed the call site to pass
    ``effective_interface_limits`` (a list) while the injector still did
    ``iso_config.interface_limits``, which would have raised AttributeError on
    every armed backcast replay. Both forms are exercised here so neither can
    regress alone.
    """
    cfg, groups = miso_groups
    out_list, info_list = apply_miso_measured_sil_envelope(
        groups, list(cfg.interface_limits), 2021, T, None, True
    )
    out_cfg, info_cfg = apply_miso_measured_sil_envelope(
        groups, cfg, 2021, T, None, True
    )
    assert info_list is not None and info_cfg is not None
    assert info_list == info_cfg
    idx = [lim.name for lim in cfg.interface_limits].index(SIL_NAME)
    assert np.array_equal(np.asarray(out_list[idx][1]), np.asarray(out_cfg[idx][1]))
    assert np.array_equal(np.asarray(out_list[idx][3]), np.asarray(out_cfg[idx][3]))
