"""The window pins monthly-banded import links to their P0 flows.

``import_link_band`` (NYISO landing links) is a monthly MWh band on link
flows. A 36-hour window cannot meet a month's band (the UC-2-NYISO L1 gate:
48 contradictory rows, LP relaxation infeasible), so the window treats it
like the import-node band: drop the rows and pin the banded links' flows to
P0 over ``[t0, t1)`` (DESIGN section 2.1).
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.model.uc.window import BUDGET_KWARGS, slice_window_inputs

from .conftest import toy_inputs


def _band_kwargs(T: int, dk: dict) -> tuple[dict, np.ndarray]:
    n_links = 3
    lo = np.full((2, 12), 1e6)
    hi = np.full((2, 12), 2e6)
    flows = np.vstack([np.arange(T, dtype=float) + 1.0 for _ in range(n_links)])
    flows[2] *= -1.0
    dk = {
        **dk,
        "ttc": np.array([500.0, 600.0, 700.0]),
        "link_bidirectional": np.array([False, True, True]),
        "import_link_band": (np.array([0, 2]), lo, hi),
    }
    return dk, flows


def test_band_is_a_budget_kwarg() -> None:
    assert "import_link_band" in BUDGET_KWARGS


def test_banded_links_pinned_to_p0_flow() -> None:
    T, t0, t1 = 48, 6, 18
    _gens, fa, demand, _mc, dk = toy_inputs(T)
    dk, flows = _band_kwargs(T, dk)
    inputs = slice_window_inputs(fa, demand, dk, t0, t1, p0_flows=flows)
    kw = inputs.kwargs
    assert "import_link_band" not in kw
    ttc, imp = kw["ttc"], kw["ttc_import"]
    assert ttc.shape == imp.shape == (t1 - t0, 3)
    for link in (0, 2):  # lower = -ttc_import = upper = ttc = P0 flow
        np.testing.assert_array_equal(ttc[:, link], flows[link, t0:t1])
        np.testing.assert_array_equal(-imp[:, link], flows[link, t0:t1])
    np.testing.assert_array_equal(ttc[:, 1], 600.0)  # unbanded link untouched
    np.testing.assert_array_equal(imp[:, 1], 600.0)
    assert kw["link_bidirectional"].all()  # the one-way floor cannot loosen a pin
    assert not dk["link_bidirectional"][0]  # the year's kwargs are not mutated


def test_band_without_p0_flows_refused() -> None:
    T = 48
    _gens, fa, demand, _mc, dk = toy_inputs(T)
    dk, _flows = _band_kwargs(T, dk)
    with pytest.raises(ValueError, match="P0 flows"):
        slice_window_inputs(fa, demand, dk, 0, 12)


def test_free_budget_units_drops_band_without_pinning() -> None:
    T = 48
    _gens, fa, demand, _mc, dk = toy_inputs(T)
    dk, _flows = _band_kwargs(T, dk)
    inputs = slice_window_inputs(fa, demand, dk, 0, 12, free_budget_units=True)
    assert "import_link_band" not in inputs.kwargs
    np.testing.assert_array_equal(inputs.kwargs["ttc"], dk["ttc"])
