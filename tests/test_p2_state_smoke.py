"""Smoke test: the committed ``p2_state`` pickles still gunzip + unpickle.

Load-only, no LP solve. This is the end-to-end complement to
``test_persisted_identity`` (which checks class paths without touching the
bytes): it proves an actual committed pickle round-trips through the current
class definitions. If a refactor moves a pickle-borne class off its frozen path,
this fails at ``pickle.load`` with an ``AttributeError``/``ModuleNotFoundError``.

Reads the smallest committed pickle across the four pickle-bearing bundles that
survived the retention sweep. Skips (rather than fails) when none are on disk,
so a sparse/shallow checkout without the ~10 MB bundles still collects.
"""

from __future__ import annotations

import gzip
import pickle
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent

# The bundles carrying committed p2_state pickles (retention sweep, current
# main). Any one proves the round-trip; we load the smallest available.
_PICKLE_BUNDLES = (
    "stgas_netload_drag_v1",
    "ctharcut_3yr",
    "ctharcut_pp_3yr",
    "coalprb_foll078_3yr",
)


def _smallest_committed_pickle() -> Path | None:
    candidates: list[Path] = []
    for bundle in _PICKLE_BUNDLES:
        candidates.extend(
            (_REPO / "results" / "calibration" / bundle / "p2_state").glob("*.pkl.gz")
        )
    existing = [p for p in candidates if p.is_file()]
    if not existing:
        return None
    return min(existing, key=lambda p: p.stat().st_size)


def test_p2_state_pickle_loads() -> None:
    """gunzip + unpickle the smallest committed p2_state pickle (no LP)."""
    pkl = _smallest_committed_pickle()
    if pkl is None:
        pytest.skip("no committed p2_state pickles on disk (sparse checkout)")

    with gzip.open(pkl, "rb") as fh:
        state = pickle.load(fh)

    assert isinstance(state, dict), f"{pkl} did not unpickle to a dict"
    # The keys run_p2_layer relies on must survive the load.
    for key in ("config", "context", "year", "fleet_arrays"):
        assert key in state, f"{pkl} p2_state is missing {key!r}"

    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet import FleetArrays

    assert isinstance(state["config"], ScenarioConfig)
    assert isinstance(state["fleet_arrays"], FleetArrays)
