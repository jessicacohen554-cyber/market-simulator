"""``DispatchModel.solve(full_extract=False)`` — the P0 slim extraction.

PERF-C S2 (``docs/handoffs/FINDING-perfc-s2-p0-slim-2026-09-20.md``). The P0
pass is a commitment-discovery solve whose result is read for the primal
blocks, ``prices``, ``objective_value``, ``status`` and the two timings and for
nothing else, so it asks the model for exactly those and skips the diagnostic
extraction (the whole-``col_dual`` conversion, the ``row_value`` conversion and
the float32 ``gen_mc`` copy).

``marginal_emission_rate`` is the ONE optional field a slim result still
carries, and that exclusion is load-bearing rather than an oversight: gating it
too was measured WARM-START-CLASS on the route where P1 re-solves the same live
model (FINDING §2), so it stays unconditional and is pinned here as an explicit
exception — a future "tidy-up" that folds it into the skip set re-breaks the
NEISO byte gate.

What these tests pin is the property that makes the trim admissible: the slim
result's populated attributes are **equal to the full result's**, value for
value, and the skipped ones are exactly the optional ``DispatchResult`` fields.
Nothing here is a tolerance comparison — the LP built and solved is identical,
so the shared values are bit-identical.

CLAUDE.md testing pattern: the trivial case first (1 gen, 1 zone, 24 h), then
a second system carrying the blocks the trivial one has none of (two zones, a
link, storage, reserve co-optimization) so the skip is exercised where it
actually skips something.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from market_sim.model.lp import DispatchResult
from tests.helpers.builders import make_fleet
from tests.helpers.solve import solve_tiny

# The REQUIRED DispatchResult fields — the ones with no default. They are
# exactly the slim set, which is why the union is expressible as "the dataclass
# fields that must be supplied".
_REQUIRED = tuple(
    f.name
    for f in dataclasses.fields(DispatchResult)
    if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
)
# Timings are wall-clock and never equal across two solves; they are still
# POPULATED on a slim result, which is what the consumer needs.
_TIMINGS = ("build_time", "solve_time")
# Optional fields a slim extract still populates. See the module docstring:
# skipping the marginal emission rate is warm-start-class, not byte-neutral.
_SLIM_EXCEPTIONS = ("marginal_emission_rate",)


def _assert_slim_matches_full(full: DispatchResult, slim: DispatchResult) -> None:
    """Every required field equal (timings excepted), every optional one None."""
    for name in _REQUIRED:
        if name in _TIMINGS:
            assert isinstance(getattr(slim, name), float), name
            continue
        got, ref = getattr(slim, name), getattr(full, name)
        if ref is None:
            assert got is None, name
        elif isinstance(ref, np.ndarray):
            assert np.array_equal(np.asarray(got), ref), name
        else:
            assert got == ref, name

    optional = [f.name for f in dataclasses.fields(DispatchResult)]
    for name in optional:
        if name in _REQUIRED or name in _SLIM_EXCEPTIONS:
            continue
        assert getattr(slim, name) is None, (
            f"{name} should be skipped on a slim extract"
        )

    # The exceptions are EQUAL, not merely present: same live model, same
    # basis, same rate.
    for name in _SLIM_EXCEPTIONS:
        got, ref = getattr(slim, name), getattr(full, name)
        if ref is None:
            assert got is None, name
        else:
            assert np.array_equal(np.asarray(got), ref), name


def test_slim_matches_full_trivial_lp():
    """1 gen / 1 zone / 24 h: the slim result reproduces the full one."""
    fleet = make_fleet(["Z0"], ["Z0"], hours=24)
    kw = dict(demand_by_zone={"Z0": 50.0}, hours=24, mc=20.0)

    full = solve_tiny(fleet, **kw)
    slim = solve_tiny(fleet, **kw, full_extract=False)

    assert slim.status == full.status == "Optimal"
    _assert_slim_matches_full(full, slim)
    # gen_mc is the one optional field the full result always carries, so it is
    # the sharpest check that the skip actually happened.
    assert full.gen_mc is not None and slim.gen_mc is None


def test_slim_matches_full_with_links_storage_and_reserve():
    """Two zones + a link + storage + reserve co-opt: the skipped blocks exist.

    On the trivial LP most optional fields are ``None`` even under a full
    extract (no links, no storage, no reserve rows), so the equality above is
    partly vacuous. Here ``flows``/storage are populated primal blocks (kept)
    while ``flow_dual``, ``gen_reduced_cost`` and ``reserve_*`` are populated
    diagnostics (skipped), and ``marginal_emission_rate`` is the populated
    diagnostic that is deliberately KEPT.
    """
    T = 24
    zones = ["Z0", "Z1"]
    fleet = make_fleet(["Z0", "Z1"], zones, hours=T, pmax=200.0, pmin=0.0)
    n_gen = int(len(fleet.pmax))

    # One link Z0 -> Z1, hour-major incidence as build_constraints expects.
    incidence = np.zeros((len(zones), 1))
    incidence[0, 0] = -1.0
    incidence[1, 0] = 1.0

    mc = np.tile(np.array([15.0, 45.0])[:, None], (1, T))
    kw = dict(
        demand_by_zone={"Z0": 40.0, "Z1": 90.0},
        hours=T,
        mc=mc,
        incidence=incidence,
        ttc=np.array([60.0]),
        storage_power_cap=np.array([25.0]),
        storage_energy_cap=np.array([100.0]),
        storage_zone_idx=np.array([0]),
        reserve_requirement=np.full(T, 20.0),
    )

    full = solve_tiny(fleet, **kw)
    slim = solve_tiny(fleet, **kw, full_extract=False)

    # The blocks that must SURVIVE the trim, present and equal.
    assert full.flows is not None and full.storage_soc is not None
    assert np.array_equal(slim.flows, full.flows)
    assert np.array_equal(slim.storage_soc, full.storage_soc)
    assert np.array_equal(slim.prices, full.prices)

    # The blocks that must be SKIPPED — populated on the full result, so their
    # absence on the slim one is a real skip and not an empty LP.
    assert full.flow_dual is not None
    assert full.gen_reduced_cost is not None and full.gen_reduced_cost.shape == (
        n_gen,
        T,
    )
    assert full.reserve_price is not None
    assert full.reserve_held_by_family is not None

    # The exception: kept, and equal, on the slim result too.
    assert full.marginal_emission_rate is not None
    assert slim.marginal_emission_rate is not None
    assert np.array_equal(slim.marginal_emission_rate, full.marginal_emission_rate)

    _assert_slim_matches_full(full, slim)


def test_full_extract_is_the_default():
    """An unqualified solve is unchanged — every diagnostic still extracted."""
    fleet = make_fleet(["Z0"], ["Z0"], hours=24)
    res = solve_tiny(fleet, demand_by_zone={"Z0": 50.0}, hours=24, mc=20.0)
    assert res.gen_mc is not None
    assert res.marginal_emission_rate is not None
