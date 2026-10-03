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

Written as ``uc_uplift_<y>.parquet`` by the bench L3 harness and the compose
script from the stage's schedule and the P1 result.
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
        mc_base: ``(n_gen, T)`` base marginal cost.
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


#: Model plant group -> ``uc_class`` family token (mirrors ``params.FAMILY_BY_GROUP``).
def _family_of_group(group: str) -> str | None:
    from market_sim.model.uc.params import FAMILY_BY_GROUP

    return FAMILY_BY_GROUP.get(str(group))


def uplift_from_bundle(bundle: str, uc_dir: str, year: int) -> pd.DataFrame:
    """The ``uc_uplift_<y>`` frame from a bundle's committed sidecars (zero LP).

    Reads ``hourly/unit_marginal_<y>.parquet`` (per-unit P1 ``mw`` and the P1
    offer ``mc`` — which IS ``mc_base`` on the integer clusters, whose markup
    the stage zeroes), ``hourly/system_<y>.parquet`` (zonal P1 prices) and the
    stage's ``uc_schedule_<y>.parquet`` / ``uc_solve_log_<y>.json`` (``u``,
    ``v``, the no-load $/h per unit, ``su_per_mw`` x ``pbar_mw``). Members are
    the unit rows whose ``plant_code`` and plant-group family match the
    cluster's. Per cluster-day, as :func:`compute_uplift`.
    """
    import json
    from pathlib import Path

    bundle_p, uc_p = Path(bundle), Path(uc_dir)
    um = pd.read_parquet(
        bundle_p / "hourly" / f"unit_marginal_{year}.parquet",
        columns=["pass", "plant_code", "plant_group", "zone", "hour", "mw", "mc"],
    )
    um = um[um["pass"] == "P1"]
    sysf = pd.read_parquet(
        bundle_p / "hourly" / f"system_{year}.parquet",
        columns=["pass", "zone", "hour", "price"],
    )
    sysf = sysf[sysf["pass"] == "P1"]
    price = sysf.pivot_table(index="hour", columns="zone", values="price")
    sched = pd.read_parquet(uc_p / f"uc_schedule_{year}.parquet")
    log = json.loads((uc_p / f"uc_solve_log_{year}.json").read_text())
    start_cost = {
        int(c["cluster"]): float(c["su_per_mw"]) * float(c["pbar_mw"])
        for c in log["clusters"]
    }
    um = um.assign(family=um["plant_group"].map(_family_of_group))
    um["lam"] = (
        price.lookup(um["hour"].to_numpy(), um["zone"].to_numpy())
        if hasattr(price, "lookup")
        else [
            price.at[h, z] for h, z in zip(um["hour"].to_numpy(), um["zone"].to_numpy())
        ]
    )
    um["rev"] = um["mw"] * um["lam"]
    um["cost"] = um["mw"] * um["mc"]
    um["day"] = (um["hour"] // _DAY_HOURS).astype(int)
    agg = (
        um.groupby(["plant_code", "family", "day"])[["mw", "rev", "cost"]]
        .sum()
        .reset_index()
    )
    sched["day"] = (sched["hour"] // _DAY_HOURS).astype(int)
    sched["noload"] = sched["noload_usd_per_unit_h"] * sched["u"].clip(lower=0)
    sched["start"] = sched["cluster"].map(start_cost) * sched["v"].clip(lower=0)
    sd = (
        sched.groupby(["cluster", "plant_code", "uc_class", "day"])[["noload", "start"]]
        .sum()
        .reset_index()
    )
    out = sd.merge(
        agg.rename(columns={"family": "uc_class"}),
        on=["plant_code", "uc_class", "day"],
        how="left",
    ).fillna({"mw": 0.0, "rev": 0.0, "cost": 0.0})
    out["uplift_usd"] = (out["cost"] + out["noload"] + out["start"] - out["rev"]).clip(
        lower=0.0
    )
    return pd.DataFrame(
        {
            "year": np.full(len(out), int(year), dtype=np.int16),
            "day": out["day"].astype(np.int16),
            "cluster": out["cluster"].astype(np.int32),
            "plant_code": out["plant_code"].astype(np.int64),
            "uc_class": out["uc_class"].astype(str),
            "energy_mwh": out["mw"].astype(float),
            "revenue_usd": out["rev"].astype(float),
            "energy_cost_usd": out["cost"].astype(float),
            "noload_usd": out["noload"].astype(float),
            "start_usd": out["start"].astype(float),
            "uplift_usd": out["uplift_usd"].astype(float),
        }
    )
