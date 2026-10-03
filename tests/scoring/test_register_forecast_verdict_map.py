"""``register_forecast_run.VERDICT_MAP`` — the D107 re-point (capx D107, 2026-10-03).

A registered forecast run must never render a verdict its own score
contradicts. When a re-solve moves an ISO's bare ``<iso>-t1f`` key onto the
new run (the LIVE-vintage convention), the superseded run's row is re-pointed
to the preserved ``-pre-<lane>`` key written in the same commit. These tests
pin the D105 (NEISO) / D106 (NYISO) instance of that chain against the
committed ``frontend/data/forecast/ff-verdicts.json``: every key the four
rows resolve to exists, the superseded rows no longer resolve to the live
key, and the live rows do. They read the committed verdict file for its KEY
SET only — never a verdict's value.
"""

from __future__ import annotations

import json

import pytest

from scripts import register_forecast_run as R
from tests.helpers import REPO_ROOT

VERDICTS = REPO_ROOT / "frontend" / "data" / "forecast" / "ff-verdicts.json"

#: (superseded run id, preserved key, live key, live run id)
D107_CHAIN = [
    (
        "neiso-2026-2030-d50-ccscapex",
        "neiso-t1f-pre-d105",
        "neiso-t1f",
        "neiso-2026-2030-d105-w0neiso",
    ),
    (
        "nyiso-2026-2030-d60-arm",
        "nyiso-t1f-pre-d106",
        "nyiso-t1f",
        "nyiso-2026-2030-d106-w0nyiso",
    ),
]


@pytest.fixture(scope="module")
def verdict_keys() -> set[str]:
    """The committed verdict KEY set (values are never read)."""
    return set(json.loads(VERDICTS.read_text()))


@pytest.mark.parametrize("superseded, preserved, live, live_run", D107_CHAIN)
def test_superseded_row_points_at_its_preserved_key(
    superseded, preserved, live, live_run, verdict_keys
):
    assert R.VERDICT_MAP[superseded] == preserved
    assert R.VERDICT_MAP[superseded] != live
    assert preserved in verdict_keys


@pytest.mark.parametrize("superseded, preserved, live, live_run", D107_CHAIN)
def test_live_row_points_at_the_bare_key(
    superseded, preserved, live, live_run, verdict_keys
):
    assert R.VERDICT_MAP[live_run] == live
    assert live in verdict_keys


@pytest.mark.parametrize("superseded, preserved, live, live_run", D107_CHAIN)
def test_verdict_key_resolution_prefers_meta_then_the_map(
    superseded, preserved, live, live_run, verdict_keys
):
    # The map is the fallback; a sidecar's own meta.verdict_key wins.
    assert R._verdict_key(superseded, {}) == preserved
    assert R._verdict_key(live_run, {}) == live
    assert R._verdict_key(superseded, {"verdict_key": "explicit"}) == "explicit"


def test_the_two_preserved_keys_are_distinct_from_the_live_ones(verdict_keys):
    keys = {R.VERDICT_MAP[s] for s, *_ in D107_CHAIN}
    lives = {live for _, _, live, _ in D107_CHAIN}
    assert keys.isdisjoint(lives)
    assert keys <= verdict_keys
