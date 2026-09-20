"""``build_constraints`` bound-vector assembly — the collect-once rewrite.

PERF-C S2 (``docs/handoffs/FINDING-perfc-s2-p0-slim-2026-09-20.md`` §3). The
``row_lower`` / ``row_upper`` vectors used to grow by ~20 successive
``np.concatenate([row_lower, block_lower])`` calls, each re-copying the whole
accumulated vector; they are now collected as per-block pieces and joined once
at the return, the same shape ``_vstack_csr_free`` already gives the matrix.

The rewrite is a pure re-association of the same pieces in the same order, so
what these tests pin is exactly the three ways such a rewrite can go wrong:
a piece dropped or mis-ordered (caught by the row-count and per-block value
checks), the running row counter drifting from the parts list (caught by the
reported ``iface_row_offset`` / ``lcr_row_offset`` landing on the right rows),
and the two vectors aliasing each other or an input (caught directly).

Trivial case first per CLAUDE.md, then a system carrying the optional families
whose appends the rewrite actually touched.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from market_sim.model.lp.layout import VariableLayout
from market_sim.model.lp.rows import build_constraints
from tests.helpers.builders import make_fleet

T = 24


def _layout_and_fleet(zones, gens_in, *, n_links=0, n_storage=0, **layout_kw):
    fleet = make_fleet(gens_in, zones, hours=T, pmax=200.0, pmin=0.0)
    layout = VariableLayout(
        n_gen=int(len(fleet.pmax)),
        n_zones=len(zones),
        n_storage=n_storage,
        n_links=n_links,
        T=T,
        **layout_kw,
    )
    return layout, fleet


def test_trivial_bounds_are_the_energy_balance_rhs():
    """1 gen / 1 zone / 24 h: the only rows are the energy balance equalities."""
    layout, fleet = _layout_and_fleet(["Z0"], ["Z0"])
    demand = np.full((1, T), 50.0)

    A, lower, upper, *_ = build_constraints(layout, fleet, demand)

    assert A.shape[0] == lower.size == upper.size == T
    assert lower.dtype == upper.dtype == np.float64
    # Equality rows carrying that hour's demand, hour-major.
    assert np.array_equal(lower, demand.T.ravel())
    assert np.array_equal(upper, demand.T.ravel())
    # Two independent vectors — a caller may clip one without moving the other.
    assert lower is not upper
    assert not np.shares_memory(lower, upper)
    assert not np.shares_memory(lower, demand)


def test_row_count_and_block_order_with_storage_and_interface():
    """Every appended family lands at its own rows, in build order.

    Row order is ``[energy balance | storage SOC | interface]`` here, and each
    family's bounds are checkable on their face: the balance rows are equalities
    at demand, the SOC dynamics are equalities at zero, and the interface rows
    are the two-sided ``[-cap, +cap]`` band. A dropped or mis-ordered piece
    moves at least one of the three.
    """
    zones = ["Z0", "Z1"]
    layout, fleet = _layout_and_fleet(zones, ["Z0", "Z1"], n_links=1, n_storage=1)
    demand = np.vstack([np.full(T, 40.0), np.full(T, 90.0)])
    incidence = np.array([[-1.0], [1.0]])
    cap = 60.0

    A, lower, upper, lcr_off, n_lcr, iface_off, n_iface = build_constraints(
        layout,
        fleet,
        demand,
        incidence=incidence,
        storage_zone_idx=np.array([0]),
        interface_groups=[(np.array([0]), cap, True)],
    )

    n_eb = len(zones) * T
    n_soc = T  # one storage unit
    assert A.shape[0] == lower.size == upper.size == n_eb + n_soc + T
    assert lower.dtype == upper.dtype == np.float64

    # Energy balance: equalities at demand, hour-major zone-minor.
    assert np.array_equal(lower[:n_eb], demand.T.ravel())
    assert np.array_equal(upper[:n_eb], demand.T.ravel())
    # SOC dynamics: equalities at zero.
    soc = slice(n_eb, n_eb + n_soc)
    assert np.array_equal(lower[soc], np.zeros(n_soc))
    assert np.array_equal(upper[soc], np.zeros(n_soc))
    # Interface: the reported offset is the running row count, so it must index
    # the band rows themselves.
    assert n_iface == 1
    assert iface_off == n_eb + n_soc
    band = slice(iface_off, iface_off + T)
    assert np.array_equal(lower[band], np.full(T, -cap))
    assert np.array_equal(upper[band], np.full(T, cap))
    # No LCR family was requested.
    assert (lcr_off, n_lcr) == (-1, 0)


def test_bounds_length_tracks_the_matrix_across_optional_families():
    """The row count stays in step with the matrix as families are added.

    The parts list and the running counter are two records of the same thing;
    this walks a family in and out and asserts the matrix and both vectors move
    together every time. A counter that drifted would still produce vectors of
    the right length (they are joined from the parts, not the counter) — so the
    check that catches drift is the offset one above; this one catches a piece
    appended to only ONE of the two lists.
    """
    zones = ["Z0"]
    demand = np.full((1, T), 50.0)

    def _rows(**kw):
        n_storage = 1 if "storage_zone_idx" in kw else 0
        layout, fleet = _layout_and_fleet(zones, ["Z0"], n_storage=n_storage)
        A, lower, upper, *_ = build_constraints(layout, fleet, demand, **kw)
        assert A.shape[0] == lower.size == upper.size
        return A.shape[0]

    base = _rows()
    with_storage = _rows(storage_zone_idx=np.array([0]))
    with_rps = _rows(rps_target=0.1, rps_eligible_fuels=("wind",))

    assert with_storage == base + T  # one SOC row per hour
    assert with_rps == base + 1  # the single ISO-wide RPS row


def test_matrix_is_still_one_csr_of_the_right_shape():
    """The bound rewrite left ``_vstack_csr_free``'s output untouched."""
    layout, fleet = _layout_and_fleet(["Z0"], ["Z0"])
    A, lower, _, *_ = build_constraints(layout, fleet, np.full((1, T), 50.0))
    assert sp.issparse(A)
    assert A.shape == (lower.size, layout.total_columns)
