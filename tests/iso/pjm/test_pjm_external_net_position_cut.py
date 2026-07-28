"""pjm-135 star-node NET-position cut (``pjm_external_net_position_cut``).

Pins the three properties the delta's PREREG gates on structurally: the group
spans exactly the star links (so no border can be re-routed around it), it is
one-sided in the import direction (so net export is never forced), and the flag
is byte-identical off.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.interchange_config import IMPORT_NODE_LINKS, IMPORT_ZONE
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.transmission import (
    build_pjm_external_net_position_cut_groups,
    extend_with_import_node,
    pjm_external_star_cut_links,
)


@pytest.fixture(scope="module")
def pjm_links():
    """The import-node-extended PJM topology's transfer links."""
    return extend_with_import_node(get_iso_config("PJM")).links


def test_star_cut_links_track_the_registry():
    """The cut spans every ``PJM_external→border`` link, derived not re-listed."""
    ext = IMPORT_ZONE["PJM"]
    assert pjm_external_star_cut_links() == tuple(
        (ext, border) for border, _ in IMPORT_NODE_LINKS["PJM"]
    )


def test_group_spans_exactly_the_star_links(pjm_links):
    """One group, all five star links, all at sign +1 (the net position)."""
    limit = np.full(24, -1000.0)
    groups = build_pjm_external_net_position_cut_groups(pjm_links, limit)
    assert len(groups) == 1
    idx, cap, bidirectional, lower, signs = groups[0]
    expected = [
        i for i, link in enumerate(pjm_links) if link.from_zone == IMPORT_ZONE["PJM"]
    ]
    assert sorted(idx.tolist()) == sorted(expected)
    assert len(expected) == len(IMPORT_NODE_LINKS["PJM"])
    assert np.array_equal(signs, np.ones(len(expected)))
    assert np.array_equal(cap, limit)


def test_cut_is_one_sided_and_passes_negative_caps_through(pjm_links):
    """Net export is never bounded, and a negative ceiling survives verbatim.

    PJM is a measured net exporter in 92.5-98.1 % of hours, so the envelope is
    normally negative: the row must read ``Σ Flow ≤ -X`` (a ceiling on net
    import), never clamp to zero and never gain a reverse-direction floor.
    """
    limit = np.array([-2207.0, -1310.0, 1887.0])
    idx, cap, bidirectional, lower, signs = build_pjm_external_net_position_cut_groups(
        pjm_links, limit
    )[0]
    assert bidirectional is False
    assert lower is None
    assert np.array_equal(cap, limit)  # no clamp at 0


def test_no_star_link_is_a_noop():
    """A topology without the import node yields no group (LP byte-identical)."""
    assert (
        build_pjm_external_net_position_cut_groups(
            get_iso_config("PJM").links, np.zeros(24)
        )
        == []
    )


def test_flag_defaults_off_and_keeps_the_cache_key():
    """Default-off, and registered in ``_CACHE_KEY_OPTIONAL_FIELDS``."""
    assert ScenarioConfig().pjm_external_net_position_cut is False
    assert (
        ScenarioConfig(pjm_external_net_position_cut=False).cache_key()
        == ScenarioConfig().cache_key()
    )
    assert (
        ScenarioConfig(pjm_external_net_position_cut=True).cache_key()
        != ScenarioConfig().cache_key()
    )
