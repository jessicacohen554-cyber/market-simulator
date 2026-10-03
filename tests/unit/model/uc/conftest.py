"""Shared toy fixtures for the MILP UC stage tests (trivial cases first).

One zone, 24-48 hours, two or three generators: a combined-cycle plant that
is the one integer cluster (two 100 MW units, measured min-stable 0.5,
``ut = 6`` / ``dt = 4``, a positive no-load), a cheap baseload row and a
fast-start CT. The ``uc-params`` frame is injected through
``market_sim.model.uc.params.load_uc_params_frame`` (the clean-seam read is
covered by ``tests/test_curate_uc_params.py``).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.data.fleet import Generator, generators_to_fleet_arrays


def toy_generators(with_baseload: bool = True) -> list[Generator]:
    """The toy fleet: CC cluster (2 units), optional cheap baseload, a CT."""
    gens = [
        Generator(
            unit_id="CC1",
            name="cc",
            zone="Z0",
            fuel_type="gas_cc",
            pmax_mw=200.0,
            pmin_mw=0.0,
            heat_rate=7.0,
            vom=2.0,
            eford=0.0,
            plant_code=1,
            plant_group="CC_REGULAR",
        )
    ]
    if with_baseload:
        gens.append(
            Generator(
                unit_id="NUC",
                name="nuc",
                zone="Z0",
                fuel_type="nuclear",
                pmax_mw=60.0,
                pmin_mw=0.0,
                heat_rate=10.0,
                vom=1.0,
                eford=0.0,
                plant_code=9,
                plant_group="NUCLEAR",
            )
        )
    gens.append(
        Generator(
            unit_id="CT1",
            name="ct",
            zone="Z0",
            fuel_type="gas_ct",
            pmax_mw=150.0,
            pmin_mw=0.0,
            heat_rate=10.0,
            vom=5.0,
            eford=0.0,
            plant_code=2,
            plant_group="CT_PEAKER",
        )
    )
    return gens


def toy_uc_params(
    noload_mmbtu_h: float = 100.0, ut_h: int = 6, dt_h: int = 4
) -> pd.DataFrame:
    """The ``uc-params`` row of the CC plant (plus nothing else)."""
    return pd.DataFrame(
        [
            dict(
                plant_code=1,
                uc_class="cc",
                n_units=2,
                hsl_mw=200.0,
                lsl_mw=100.0,
                mlf=0.5,
                ut_h=ut_h,
                dt_h=dt_h,
                noload_mmbtu_h=noload_mmbtu_h,
                noload_units_fitted=2,
                noload_r2_median=0.99,
                online_frac=0.7,
                n_runs=100,
                years="2023-2025",
                source="toy",
            )
        ]
    )


def toy_inputs(
    T: int, with_baseload: bool = True, night_mw: float = 40.0, day_mw: float = 150.0
):
    """(generators, fleet_arrays, demand, mc_base, dispatch_kwargs) for ``T`` hours."""
    gens = toy_generators(with_baseload)
    fa = generators_to_fleet_arrays(gens, ["Z0"], hours=T)
    demand = np.full((1, T), day_mw)
    for d in range(T // 24 + 1):
        demand[0, d * 24 : min(d * 24 + 7, T)] = night_mw
    rows = [np.full(T, 25.0)]
    if with_baseload:
        rows.append(np.full(T, 5.0))
    rows.append(np.full(T, 60.0))
    mc_base = np.vstack(rows)
    dk = dict(
        wind_cf=np.zeros((1, T)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.zeros(1),
        voll=5000.0,
    )
    return gens, fa, demand, mc_base, dk


@pytest.fixture
def uc_params_frame(monkeypatch):
    """Inject the toy ``uc-params`` frame into the params loader; returns a setter."""
    import market_sim.model.uc.params as ucp

    holder = {"frame": toy_uc_params()}
    monkeypatch.setattr(ucp, "load_uc_params_frame", lambda iso: holder["frame"])

    def _set(frame: pd.DataFrame) -> None:
        holder["frame"] = frame

    return _set


@pytest.fixture
def uc_results_root(monkeypatch, tmp_path):
    """Redirect the stage's artifact root to a tempdir."""
    import market_sim.pipeline.uc as puc

    monkeypatch.setattr(puc, "RESULTS_ROOT", tmp_path / "results")
    return tmp_path / "results"
