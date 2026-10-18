"""Switch the EIA-930 stale-snapshot repair off for tests on synthetic frames.

The repair (``market_sim.data.stale_snapshot``, owner rulings R22 / R23) runs
on every SPP demand / weight / interchange / renewable read and needs the
curated ``iso-area-load`` / ``counterparty-interchange`` / ``iso-genmix``
partitions. A test that feeds a synthetic SWPP frame to exercise some OTHER
behaviour (a spike screen, a curation, a forecast basis) is not about the
repair: synthetic series repeat exactly by construction and would trip it.
Such tests unregister the specs for their duration. The repair itself is
covered by ``tests/unit/data/test_stale_snapshot.py``.
"""

from __future__ import annotations

import unittest
from unittest import mock

from market_sim.data import stale_snapshot


def disable_stale_snapshot_repair(testcase: unittest.TestCase) -> None:
    """Unregister every stale-snapshot spec until ``testcase`` cleans up."""
    patcher = mock.patch.dict(stale_snapshot.STALE_SNAPSHOT_SPECS, clear=True)
    patcher.start()
    stale_snapshot.reset_caches()
    testcase.addCleanup(stale_snapshot.reset_caches)
    testcase.addCleanup(patcher.stop)


def disable_stale_snapshot_repair_mp(monkeypatch) -> None:
    """The pytest ``monkeypatch`` form of :func:`disable_stale_snapshot_repair`."""
    for iso in list(stale_snapshot.STALE_SNAPSHOT_SPECS):
        monkeypatch.delitem(stale_snapshot.STALE_SNAPSHOT_SPECS, iso)
    stale_snapshot.reset_caches()
