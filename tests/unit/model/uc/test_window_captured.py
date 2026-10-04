"""The one ``slow`` UC test on a captured production window (DESIGN section 6).

NEISO 2023 (the smallest ISO-year and a UC-2 control): the keeper recipe's LP
inputs are captured at the ``run_energy_solve`` seam with ZERO LP solved
(``scripts.lib.uc_bench.capture_year(..., solve=False)``), the first 36-hour
window is built from them with the window's own LP relaxation standing in for
P0, the MILP solves to the declared gap, and the integer set is a strict
subset of the candidate clusters. Needs ``data/raw`` and the NEISO clean
profile (``regenerate_clean.py --solve-profile NEISO``), so it is
``requires_raw`` and ``slow``.
"""

from __future__ import annotations

import os

import pytest

from market_sim.config import paths
from tests.helpers import requires_raw

pytestmark = pytest.mark.slow

# The env keys ``capture_year`` writes and never restores: the solve-container
# pins (``scripts/lib/solve_container.py``) and ``replay_keeper``'s determinism
# pins (FINDING-ucmilp-golden-nwpp-pjm-zero-lp-2026-10-04.md section 5).
_LEAKED_ENV = (
    "MARKET_SIM_HIGHS_THREADS",
    "OMP_NUM_THREADS",
    "MALLOC_ARENA_MAX",
    "MARKET_SIM_WARMSTART_XYEAR",
    "MARKET_SIM_P1_BASIS_SEED",
)


@pytest.fixture(autouse=True)
def _isolate_highs_threads(monkeypatch):
    """Restore the pinned env and reset HiGHS's process-global scheduler.

    HiGHS fixes its scheduler's thread count at the first solve in a process;
    a later run at a different ``threads`` value ends "Not Set". Resetting on
    both sides lets this test run after (and before) tests that solved at the
    default thread count.
    """
    import highspy

    for key in _LEAKED_ENV:
        if key in os.environ:
            monkeypatch.setenv(key, os.environ[key])
        else:
            monkeypatch.delenv(key, raising=False)
    highspy.Highs.resetGlobalScheduler(True)
    yield
    highspy.Highs.resetGlobalScheduler(True)


@requires_raw(paths.RAW_DIR / "campd-unit-level", paths.RAW_DIR / "ISNE_region.parquet")
def test_neiso_2023_first_window_builds_and_solves(tmp_path):
    from scripts.lib import uc_bench
    from scripts.lib.clean_io import clean_exists

    if not clean_exists("uc-params", iso="NEISO"):
        pytest.skip(
            "data/clean/uc-params/NEISO absent — run regenerate_clean.py --solve-profile NEISO"
        )
    bundle = uc_bench.keeper_bundle("NEISO")
    if not (bundle / "meta.json").is_file():
        pytest.skip(f"keeper bundle {bundle} absent")
    cap = uc_bench.capture_year(
        "NEISO", 2023, tmp_path / "cap", solve=False, bundle=bundle
    )
    assert cap.r0 is None and cap.demand.shape[1] == 8760
    res = uc_bench.rung_l1(cap, tmp_path / "l1")
    n_int = res["integer_clusters"]
    assert n_int > 0
    assert res["milp"]["status"] == "Optimal"
    assert res["milp"]["gap"] <= float(cap.config.uc_mip_rel_gap) + 1e-9
    horizon = int(cap.config.uc_window_hours) + int(cap.config.uc_lookahead_hours)
    assert res["milp"]["integers"] == n_int * horizon
    # The relaxation never exceeds the MILP (a lower bound on the same window).
    assert res["relaxation"]["objective"] <= res["milp"]["objective"] + 1e-6 * abs(
        res["milp"]["objective"]
    )
    assert res["integrality_gap"] >= -1e-6 * abs(res["milp"]["objective"])
    # Fast-start CTs stay continuous: the candidate set is larger than the integer set.
    from market_sim.model.uc.params import build_uc_cluster_params

    params = build_uc_cluster_params(cap.fleet_arrays, "NEISO")
    assert params.n_clusters > n_int
    assert set(params.family[params.integer]) <= {"cc", "st_gas", "coal"}
    assert "ct" in set(params.family)  # CTs are candidates that fail the gate
