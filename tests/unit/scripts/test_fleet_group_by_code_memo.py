"""``_fleet_group_by_code`` per-process memo — observable equivalence.

PERF-C S2 (``docs/handoffs/FINDING-perfc-s2-p0-slim-2026-09-20.md`` §4). The
helper re-reads and re-assembles the whole EIA-860 per-plant fleet through the
uncached ``load_fleet_from_csv`` to keep two fields, so a repeat call for the
same ``(iso, iso_config, year)`` is now served from a per-process memo.

The memo is admissible only if it is invisible, which is what these tests pin:
the mapping a hit returns equals the one a miss computes, a hit returns a FRESH
dict (so a caller mutating the result cannot reach the memo or a later year),
and the key discriminates on all three arguments. No solve and no real data are
needed — ``load_fleet_from_csv`` is stubbed so the call count is observable,
which is the property under test.
"""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass

import pytest

rcf = pytest.importorskip("scripts.run_calibration_full")


@dataclass
class _Gen:
    plant_code: int
    plant_group: str


class _Cfg:
    """Stand-in for an ISOConfig — identity is all the memo key uses."""


@pytest.fixture
def stub_loader(monkeypatch):
    """Replace ``market_sim.data.fleet.load_fleet_from_csv`` and count calls.

    ``_fleet_group_by_code`` imports the symbol from the package INSIDE the
    function body, so patching the attribute on the module object is what the
    call actually resolves against.
    """
    calls: list[tuple] = []
    fleet_mod = sys.modules.get("market_sim.data.fleet")
    if fleet_mod is None:  # pragma: no cover - import for the patch target
        import market_sim.data.fleet as fleet_mod  # noqa: F401

        fleet_mod = sys.modules["market_sim.data.fleet"]
    assert isinstance(fleet_mod, types.ModuleType)

    def _fake(iso, iso_config=None, *, year=None, **kw):
        calls.append((iso, id(iso_config), year))
        # A plant_code <= 0 and a blank group are both dropped by the helper;
        # including them pins that the memo stores the FILTERED mapping.
        return [
            _Gen(101, "COAL"),
            _Gen(202, "CC_REGULAR"),
            _Gen(0, "CT_PEAKER"),
            _Gen(303, ""),
        ]

    monkeypatch.setattr(fleet_mod, "load_fleet_from_csv", _fake, raising=True)
    monkeypatch.setattr(rcf, "_FLEET_GROUP_BY_CODE_MEMO", {}, raising=True)
    return calls


def test_hit_equals_miss_and_loads_once(stub_loader):
    """dict == dict on one ISO-year, with the second call served from the memo."""
    cfg = _Cfg()
    first = rcf._fleet_group_by_code("NEISO", cfg, 2023)
    second = rcf._fleet_group_by_code("NEISO", cfg, 2023)

    assert first == {101: "COAL", 202: "CC_REGULAR"}
    assert second == first
    assert len(stub_loader) == 1, "the repeat call must not re-load the fleet"


def test_hit_returns_a_fresh_dict(stub_loader):
    """Mutating a returned mapping cannot reach the memo or a later caller."""
    cfg = _Cfg()
    first = rcf._fleet_group_by_code("NEISO", cfg, 2023)
    first[101] = "TAMPERED"
    first[999] = "INJECTED"

    second = rcf._fleet_group_by_code("NEISO", cfg, 2023)
    assert second == {101: "COAL", 202: "CC_REGULAR"}
    assert first is not second


@pytest.mark.parametrize(
    "second_call",
    [
        pytest.param(("MISO", "same", 2023), id="iso-differs"),
        pytest.param(("NEISO", "other", 2023), id="config-differs"),
        pytest.param(("NEISO", "same", 2024), id="year-differs"),
    ],
)
def test_key_discriminates_on_every_argument(stub_loader, second_call):
    """A different ISO, config object or vintage is a MISS, never a stale hit."""
    cfg = _Cfg()
    other = _Cfg()
    rcf._fleet_group_by_code("NEISO", cfg, 2023)

    iso, which_cfg, year = second_call
    rcf._fleet_group_by_code(iso, cfg if which_cfg == "same" else other, year)

    assert len(stub_loader) == 2
