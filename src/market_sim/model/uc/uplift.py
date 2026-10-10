"""The make-whole (uplift) sidecar of the MILP unit-commitment stage — zero LP, post-P1.

Integer clusters bid ``mc_base`` in the scored P1 (their start and no-load
were paid once, in the UC objective; DESIGN section 2.6), so a committed
cluster may not recover those costs from the LMP. That shortfall is REPORTED
here, per cluster and operating day, and never priced (rule 4; owner card D-3
default):

    uplift = max(0, energy_cost + noload + start - revenue)
    revenue     = sum_t lambda[z(c), t] * P1[c, t]
    energy_cost = sum_t mc_base[g, t] * P1[g, t]      over the members
    noload      = sum_t nl[c, t] * u[c, t]
    start       = sum_t su_c * pbar_c * v[c, t]

Cost basis: ``mc_base``, the P0 cost the stage was handed (heat rate x fuel +
VOM + emissions, with the authorized offer bands where an ISO's tranches carry
them in their heat rate), never the P1 bid (DESIGN section 2.6 / section 4).
It is the integer clusters' as-offered energy curve without the amortized start
markup (paid in ``start``) and without any P1-only bid adjustment — the
make-whole convention of an as-offered, cost-capped three-part offer.

Computed in-process only, by :meth:`market_sim.pipeline.uc.UcStage.artifacts`
from the P1 result the orchestrator holds, and written into the bundle as
``uc_uplift_<y>.parquet``. A bundle's sidecars carry the P1 offer, not
``mc_base``, so no bundle-side recomputation exists (the former
``uplift_from_bundle`` priced at the P1 offer and was deleted, rule 26;
FINDING-ucmilp-fix4-floor-merit-2026-10-10).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.model.uc.params import UcClusterParams

#: Hours per operating day (the make-whole settlement period).
_DAY_HOURS = 24


def compute_uplift(
    params: UcClusterParams,
    u: np.ndarray,
    v: np.ndarray,
    dispatch_p1: np.ndarray,
    prices_p1: np.ndarray,
    zone_idx: np.ndarray,
    mc_base: np.ndarray,
    noload_per_unit: np.ndarray,
    year: int,
) -> pd.DataFrame:
    """Per cluster-day make-whole frame (DESIGN section 4 ``uc_uplift``).

    Args:
        params: The cluster struct-of-arrays.
        u, v: ``(n_int, T)`` kept schedule of the integer clusters (units on,
            starts) in ``params.integer_clusters`` order.
        dispatch_p1: ``(n_gen, T)`` scored P1 dispatch.
        prices_p1: ``(n_zones, T)`` P1 zonal prices (the duals).
        zone_idx: ``(n_gen,)`` zone of every fleet row.
        mc_base: ``(n_gen, T)`` base marginal cost — the P0 cost, never the
            P1 bid (the module docstring's cost basis).
        noload_per_unit: ``(n_int, T)`` no-load $/h per unit.
        year: The year stamped on every row.
    """
    k = params.integer_clusters
    n_int = int(k.size)
    T = int(dispatch_p1.shape[1])
    n_days = int(np.ceil(T / _DAY_HOURS))
    if n_int == 0:
        return pd.DataFrame(
            columns=[
                "year",
                "day",
                "cluster",
                "plant_code",
                "uc_class",
                "energy_mwh",
                "revenue_usd",
                "energy_cost_usd",
                "noload_usd",
                "start_usd",
                "uplift_usd",
            ]
        )
    int_local = np.full(params.n_clusters, -1)
    int_local[k] = np.arange(n_int)
    mem_mask = int_local[params.member_cluster] >= 0
    mem_gen = params.member_gen[mem_mask]
    mem_k = int_local[params.member_cluster[mem_mask]]
    P = np.asarray(dispatch_p1, dtype=float)[mem_gen, :]  # (n_mem, T)
    lam = np.asarray(prices_p1, dtype=float)[
        np.asarray(zone_idx, dtype=int)[mem_gen], :
    ]
    mc = np.asarray(mc_base, dtype=float)[mem_gen, :]
    energy = np.zeros((n_int, T))
    revenue = np.zeros((n_int, T))
    cost = np.zeros((n_int, T))
    np.add.at(energy, mem_k, P)
    np.add.at(revenue, mem_k, lam * P)
    np.add.at(cost, mem_k, mc * P)
    noload = np.asarray(noload_per_unit, dtype=float) * np.maximum(
        np.asarray(u, dtype=float), 0.0
    )
    start = (params.su_per_mw[k] * params.pbar_mw[k])[:, None] * np.maximum(
        np.asarray(v, dtype=float), 0.0
    )

    def _by_day(x: np.ndarray) -> np.ndarray:
        pad = n_days * _DAY_HOURS - T
        xp = np.concatenate([x, np.zeros((n_int, pad))], axis=1) if pad else x
        return xp.reshape(n_int, n_days, _DAY_HOURS).sum(axis=2)

    e_d, r_d, c_d, n_d, s_d = (
        _by_day(x) for x in (energy, revenue, cost, noload, start)
    )
    uplift = np.maximum(0.0, c_d + n_d + s_d - r_d)
    days = np.tile(np.arange(n_days, dtype=np.int16), n_int)
    return pd.DataFrame(
        {
            "year": np.full(days.size, int(year), dtype=np.int16),
            "day": days,
            "cluster": np.repeat(k.astype(np.int32), n_days),
            "plant_code": np.repeat(params.plant_code[k].astype(np.int64), n_days),
            "uc_class": np.repeat(params.family[k].astype(str), n_days),
            "energy_mwh": e_d.ravel(),
            "revenue_usd": r_d.ravel(),
            "energy_cost_usd": c_d.ravel(),
            "noload_usd": n_d.ravel(),
            "start_usd": s_d.ravel(),
            "uplift_usd": uplift.ravel(),
        }
    )
