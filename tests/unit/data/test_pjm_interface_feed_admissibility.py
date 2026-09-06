"""pjm-167: a published transfer limit is judged against its own measured flows.

Guards ``data.transfer_interface_limits.interface_series_admissibility`` and the
``pjm_interface_feed_admissibility_gate`` fall-through.

The defect (FINDING-pjm167-input-clock-2021-2022-2026-09-06.md §2): PJM's
"Average Eastern" posting changes basis across the 2023 boundary — a near-static
seasonal limit-set value before, the hourly-averaged TLC after — and the early
vintage, enforced verbatim as an LP bound, sits BELOW flows PJM actually carried
in 27.9 % of 2021 hours.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.data.transfer_interface_limits import (
    PJM_INTERFACE_FEED_MAX_EXCEEDANCE_FRAC,
    interface_series_admissibility,
)


def _frame(limits, flows, name="Average Eastern"):
    n = len(limits)
    return pd.DataFrame(
        {
            "interface": [name] * n,
            "hour": range(n),
            "limit_mw": limits,
            "transfer_mw": flows,
        }
    )


def test_a_limit_the_flow_never_exceeds_is_admissible() -> None:
    """The 2024/2025 shape: an hourly TLC the realized flow always respects."""
    ok, diag = interface_series_admissibility(
        _frame([8000.0] * 100, [7000.0] * 100), "Average Eastern"
    )
    assert ok
    assert diag["exceedance_frac"] == 0.0
    assert diag["n_hours"] == 100


def test_a_limit_the_flow_routinely_exceeds_is_inadmissible() -> None:
    """The 2021 shape: a static posting the realized flow blows through."""
    limits = [4971.0] * 100
    flows = [6000.0] * 28 + [4000.0] * 72  # 28 % exceedance, as measured in 2021
    ok, diag = interface_series_admissibility(_frame(limits, flows), "Average Eastern")
    assert not ok
    assert diag["exceedance_frac"] == pytest.approx(0.28)
    assert diag["max_excess_mw"] == pytest.approx(1029.0)


def test_the_bar_is_the_declared_five_percent() -> None:
    """Exactly at the bar passes; one hour past it fails. No sweeping."""
    assert PJM_INTERFACE_FEED_MAX_EXCEEDANCE_FRAC == 0.05
    at = _frame([100.0] * 100, [150.0] * 5 + [50.0] * 95)
    over = _frame([100.0] * 100, [150.0] * 6 + [50.0] * 94)
    assert interface_series_admissibility(at, "Average Eastern")[0]
    assert not interface_series_admissibility(over, "Average Eastern")[0]


def test_an_absent_series_is_not_refused_blind() -> None:
    """The caller's existing missing-series contract is untouched."""
    ok, diag = interface_series_admissibility(
        _frame([1.0], [1.0], name="Something Else"), "Average Eastern"
    )
    assert ok
    assert diag["n_hours"] == 0


def test_hours_missing_a_column_are_excluded_not_counted_as_passes() -> None:
    """A sparse series must not pass by absence."""
    limits = [100.0, 100.0, np.nan, 100.0]
    flows = [150.0, 150.0, 150.0, np.nan]
    ok, diag = interface_series_admissibility(_frame(limits, flows), "Average Eastern")
    assert diag["n_hours"] == 2  # only the two hours with BOTH columns
    assert diag["exceedance_frac"] == 1.0
    assert not ok


def test_no_measured_flow_at_all_keeps_the_pre_gate_behaviour() -> None:
    """Without flows the test cannot fire, so it must not refuse the series."""
    ok, diag = interface_series_admissibility(
        _frame([100.0] * 10, [np.nan] * 10), "Average Eastern"
    )
    assert ok
    assert diag["n_hours"] == 0
    assert diag["n_distinct_limits"] == 1.0


def test_distinct_limit_count_is_reported_but_never_gates() -> None:
    """Provenance only — one criterion decides (rule 19 [R-ONE-MECH])."""
    ok, diag = interface_series_admissibility(
        _frame([4971.0] * 50 + [7526.0] * 50, [1000.0] * 100), "Average Eastern"
    )
    assert diag["n_distinct_limits"] == 2.0
    assert ok  # a two-valued series the flow respects is still admissible
