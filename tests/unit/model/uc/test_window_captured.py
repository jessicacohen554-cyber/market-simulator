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

import pytest

from market_sim.config import paths
from tests.helpers import requires_raw

pytestmark = pytest.mark.slow


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
