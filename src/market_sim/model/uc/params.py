"""Cluster parameters for the MILP unit-commitment stage (struct-of-arrays).

Builds :class:`UcClusterParams` — the per-cluster arrays the window builder
consumes (rule 6: arrays and scalars only reach LP construction) — from the
fleet, the frozen ``uc-params`` derive (``data/clean/uc-params/<ISO>``,
``scripts/data/derive_uc_cluster_params.py``) and the published class tables.
Every value is measured or published (rules 13/14/21/23); the resolution
order of each parameter is DESIGN section 1.2 and the source each cluster
resolved to is recorded in ``src_*`` so the fallback share is auditable from
the ``uc_solve_log`` sidecar.

Clusters (DESIGN section 1): one per ``(plant_code, class family)`` for the
per-plant fleets (every tranche row of the plant is a member), one per row for
legacy bins (``plant_code == 0``). The candidate set is the thermal non-CHP
fleet (``gas_cc`` / ``gas_ct`` / ``gas_st`` / coal); the E1 gate
(:func:`integer_gate`) decides which clusters carry an integer: the posture
family's fast-start exemption inverted (rule 18 physics, never class names).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from market_sim.config.constants import MIN_STABLE_PCT_PHYSICAL
from market_sim.config.plant_taxonomy import COAL_CLASSES
from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays
from market_sim.data.fleet.eia860 import (
    BIN_STARTUP_COST_PER_MW,
    COAL_BIN_MIN_DOWN_HOURS,
    COAL_BIN_MIN_RUN_HOURS,
)
from market_sim.model.commitment import COMMITMENT_PARAMS_BY_FUEL
from market_sim.model.reserves.spec import (
    POSTURE_FAST_START_MIN_DOWN_H,
    POSTURE_FAST_START_STARTUP_PER_MW,
)

#: The ``uc-params`` datatype (schema ``data/dictionary/schema/uc-params.schema.yaml``).
UC_PARAMS_DATATYPE = "uc-params"

#: Fleet fuel type -> CAMPD family token of the ``uc-params`` contract.
FAMILY_BY_FUEL: dict[str, str] = {
    "gas_cc": "cc",
    "gas_ct": "ct",
    "gas_st": "st_gas",
    "coal": "coal",
}

#: Model plant group -> family token (the per-plant fleets carry a group).
#: CHP groups are deliberately absent: their committed state is owned by the
#: steam-host floors (rule 19), so they are never a cluster.
FAMILY_BY_GROUP: dict[str, str] = {
    "CC_REGULAR": "cc",
    "CT_PEAKER": "ct",
    "ST_GAS": "st_gas",
    **{c: "coal" for c in COAL_CLASSES},
}

#: Representative model group per family for the WWSIS-2 min-stable fallback
#: (``MIN_STABLE_PCT_PHYSICAL``) when a fleet carries no ``plant_group``.
GROUP_FOR_FAMILY: dict[str, str] = {
    "cc": "CC_REGULAR",
    "ct": "CT_PEAKER",
    "st_gas": "ST_GAS",
    "coal": COAL_CLASSES[0],
}

# Pre-fixing margins (plan E5; DESIGN section 2.3). Solver heuristics that can
# move no solution when correct — ladder rung L2's schedule-hash equality
# across arms is the proof — and armed only by ``uc_prefixing`` (default off).
#: Fix-ON load threshold: the cluster's P0 output over every window hour at or
#: above this share of its available capacity reads as "ran at full output"
#: (one tranche step below full, the posture family's reading).
UC_PREFIX_ON_LOAD_FRAC: float = 0.95
#: Fix-OFF price margin ($/MWh) above the window's maximum P0 dual: about the
#: largest amortized P1 start markup a slow-start class carries
#: (``compute_monthly_markup`` on a 5-hour CC run at the NREL table cost), so a
#: cluster this far out of merit at base cost cannot enter at bid cost either.
UC_PREFIX_OFF_MARGIN_USD_PER_MWH: float = 10.0


@dataclass(frozen=True)
class UcClusterParams:
    """Struct-of-arrays cluster parameters (one entry per cluster).

    Attributes:
        member_gen: ``(n_members,)`` fleet row index of every cluster member.
        member_cluster: ``(n_members,)`` cluster index of each member.
        cluster_of_gen: ``(n_gen,)`` cluster index per fleet row, ``-1`` for a
            row that belongs to no cluster.
        plant_code: ``(n_c,)`` EIA plant code (0 for a legacy-bin cluster).
        family: ``(n_c,)`` family token (``cc`` / ``ct`` / ``st_gas`` / ``coal``).
        n_units: ``(n_c,)`` integer range of ``u`` (physical units).
        pbar_mw: ``(n_c,)`` MW per unit, fleet capacity / ``n_units``.
        mlf: ``(n_c,)`` minimum stable fraction when online.
        su_per_mw: ``(n_c,)`` start cost $/MW (capacity-weighted members).
        ut_h / dt_h: ``(n_c,)`` minimum up / down hours (``dt_h`` always the
            published class value; ``ut_h`` measured where a plant row exists).
        noload_mmbtu_h: ``(n_c,)`` plant no-load heat input per UNIT (MMBtu/h).
        anchor_gen: ``(n_c,)`` the largest member — its implied $/MMBtu prices
            the no-load fuel.
        integer: ``(n_c,)`` bool, the E1 gate.
        src_n / src_mlf / src_utdt / src_noload: ``(n_c,)`` object arrays
            naming the source each parameter resolved to.
    """

    member_gen: np.ndarray
    member_cluster: np.ndarray
    cluster_of_gen: np.ndarray
    plant_code: np.ndarray
    family: np.ndarray
    n_units: np.ndarray
    pbar_mw: np.ndarray
    mlf: np.ndarray
    su_per_mw: np.ndarray
    ut_h: np.ndarray
    dt_h: np.ndarray
    noload_mmbtu_h: np.ndarray
    anchor_gen: np.ndarray
    integer: np.ndarray
    src_n: np.ndarray
    src_mlf: np.ndarray
    src_utdt: np.ndarray
    src_noload: np.ndarray

    @property
    def n_clusters(self) -> int:
        """Number of clusters (candidate set, integer or not)."""
        return int(self.plant_code.size)

    @property
    def integer_clusters(self) -> np.ndarray:
        """Indices of the clusters that carry an integer ``u``."""
        return np.flatnonzero(self.integer)

    @property
    def integer_member_gens(self) -> np.ndarray:
        """Fleet rows belonging to an integer cluster (the markup-zeroed set)."""
        return self.member_gen[self.integer[self.member_cluster]]

    def cluster_capacity(self, fleet: FleetArrays) -> np.ndarray:
        """``(n_c,)`` summed member ``pmax``."""
        cap = np.zeros(self.n_clusters)
        np.add.at(
            cap,
            self.member_cluster,
            np.asarray(fleet.pmax, dtype=float)[self.member_gen],
        )
        return cap

    def cluster_availability(
        self, fleet: FleetArrays, t0: int = 0, t1: int | None = None
    ) -> np.ndarray:
        """``(n_c, t1 - t0)`` capacity-weighted member availability."""
        pmax = np.asarray(fleet.pmax, dtype=float)[self.member_gen]
        avail = np.asarray(fleet.availability, dtype=float)[self.member_gen, t0:t1]
        num = np.zeros((self.n_clusters, avail.shape[1]))
        np.add.at(num, self.member_cluster, pmax[:, None] * avail)
        cap = self.cluster_capacity(fleet)
        with np.errstate(invalid="ignore", divide="ignore"):
            out = np.where(cap[:, None] > 0.0, num / cap[:, None], 0.0)
        return np.clip(out, 0.0, 1.0)

    def noload_cost_per_unit_h(
        self, fleet: FleetArrays, mc_base: np.ndarray
    ) -> np.ndarray:
        """``(n_c, T)`` no-load cost $/h per unit at the anchor's implied $/MMBtu.

        ``noload_mmbtu_h * (mc_base[anchor, t] - vom[anchor]) / heat_rate[anchor]``
        — fuel plus every per-MMBtu emission charge, hourly (DESIGN section 1.2).
        A zero heat rate (an import pseudo-unit cannot be a cluster, but a
        legacy bin may carry none) prices the no-load at zero and is recorded
        in ``src_noload``.
        """
        hr = np.asarray(fleet.heat_rate, dtype=float)[self.anchor_gen]
        vom = np.asarray(fleet.vom, dtype=float)[self.anchor_gen]
        mc = np.asarray(mc_base, dtype=float)[self.anchor_gen, :]
        with np.errstate(invalid="ignore", divide="ignore"):
            per_mmbtu = np.where(
                hr[:, None] > 0.0, (mc - vom[:, None]) / hr[:, None], 0.0
            )
        per_mmbtu = np.maximum(per_mmbtu, 0.0)
        return self.noload_mmbtu_h[:, None] * per_mmbtu


def integer_gate(dt_h: np.ndarray, su_per_mw: np.ndarray) -> np.ndarray:
    """The E1 gate: ``min-down > 2 h or start >= $30/MW`` (posture gate inverted).

    The two constants are the posture family's fast-start exemption
    (``model.reserves.spec.POSTURE_FAST_START_*``), read from the same names
    so the two mechanisms cannot drift apart (rule 18).
    """
    dt = np.asarray(dt_h, dtype=float)
    su = np.asarray(su_per_mw, dtype=float)
    return (dt > POSTURE_FAST_START_MIN_DOWN_H) | (
        su >= POSTURE_FAST_START_STARTUP_PER_MW
    )


def _member_class_physics(
    fleet: FleetArrays, gidx: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-member (startup $/MW, min_run h, min_down h) from the published tables.

    The capacity-weighted member lookup of
    ``model.reserves.spec._posture_pool_params``: coal rows take the one coal
    startup cost (``BIN_STARTUP_COST_PER_MW``) and the coal bin durations; gas
    rows take ``COMMITMENT_PARAMS_BY_FUEL[fuel]`` by heat rate (NREL
    SR-5500-55433); a fuel with no table (oil) is fast-start by physics.
    """
    fuels = np.array(
        [FUEL_TYPE_NAMES[i] for i in np.asarray(fleet.fuel_type_idx)[gidx]]
    )
    hr = np.asarray(fleet.heat_rate, dtype=float)[gidx]
    su = np.zeros(gidx.size)
    ut = np.zeros(gidx.size)
    dt = np.zeros(gidx.size)
    for j in range(gidx.size):
        f = fuels[j]
        if f == "coal":
            su[j] = float(BIN_STARTUP_COST_PER_MW[COAL_CLASSES[0]])
            ut[j] = float(COAL_BIN_MIN_RUN_HOURS)
            dt[j] = float(COAL_BIN_MIN_DOWN_HOURS)
            continue
        table = COMMITMENT_PARAMS_BY_FUEL.get(f)
        if table is None:
            continue
        params = table[-1][1]
        for cutoff, p in table:
            if hr[j] < cutoff:
                params = p
                break
        su[j] = float(params["startup_per_mw"])
        ut[j] = float(params["min_run_hours"])
        dt[j] = float(params["min_down_hours"])
    return su, ut, dt


def _candidate_rows(fleet: FleetArrays) -> tuple[np.ndarray, np.ndarray]:
    """Candidate fleet rows and their family tokens (DESIGN section 1)."""
    n = fleet.n_gen
    pmax = np.asarray(fleet.pmax, dtype=float)
    pmin = np.asarray(fleet.pmin, dtype=float)
    fuels = np.array([FUEL_TYPE_NAMES[i] for i in np.asarray(fleet.fuel_type_idx)])
    groups = (
        np.asarray(fleet.plant_group).astype(object)
        if getattr(fleet, "plant_group", None) is not None
        else np.array([None] * n, dtype=object)
    )
    fam = np.array([None] * n, dtype=object)
    for g in range(n):
        if pmax[g] <= 0.0 or pmin[g] < 0.0:
            continue  # export sinks / absorption rows are never a cluster
        grp = groups[g]
        if grp is not None and str(grp) not in ("", "None"):
            fam[g] = FAMILY_BY_GROUP.get(str(grp))  # CHP -> None
        else:
            fam[g] = FAMILY_BY_FUEL.get(str(fuels[g]))
    rows = np.flatnonzero([f is not None for f in fam])
    return rows, fam


def load_uc_params_frame(iso: str) -> pd.DataFrame:
    """Read the ISO's ``uc-params`` partition; fail loudly when absent."""
    try:
        from scripts.lib.clean_io import read_clean

        return read_clean(UC_PARAMS_DATATYPE, iso=str(iso).upper())
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "unit_commitment_milp is on but no clean uc-params partition covers "
            f"{iso} — run scripts/regenerate_clean.py --solve-profile {iso} "
            "(the stage never silently no-ops)"
        ) from exc


def build_uc_cluster_params(
    fleet: FleetArrays,
    iso: str,
    uc_params: pd.DataFrame | None = None,
) -> UcClusterParams:
    """Build the cluster struct-of-arrays for ``fleet`` (DESIGN sections 1.1-1.2).

    Args:
        fleet: The dispatch fleet (the P0/P1 ``FleetArrays``).
        iso: The ISO whose ``uc-params`` partition supplies the measured rows.
        uc_params: The ``uc-params`` frame (tests pass one; ``None`` reads the
            clean partition through :func:`load_uc_params_frame`).
    """
    frame = load_uc_params_frame(iso) if uc_params is None else uc_params
    measured: dict[tuple[int, str], pd.Series] = {}
    fallback: dict[str, pd.Series] = {}
    for row in frame.itertuples(index=False):
        if int(row.plant_code) > 0:
            measured[(int(row.plant_code), str(row.uc_class))] = row
        else:
            fallback[str(row.uc_class)] = row

    rows, fam = _candidate_rows(fleet)
    plant = np.asarray(fleet.plant_code, dtype=int)
    pmax = np.asarray(fleet.pmax, dtype=float)
    groups = (
        np.asarray(fleet.plant_group).astype(object)
        if getattr(fleet, "plant_group", None) is not None
        else None
    )
    # Cluster keys: (plant_code, family) for per-plant rows, (-(row+1), family)
    # for legacy bins so every such row is its own cluster.
    keys: list[tuple[int, str]] = []
    key_index: dict[tuple[int, str], int] = {}
    member_cluster = np.zeros(rows.size, dtype=int)
    for j, g in enumerate(rows):
        key = (int(plant[g]) if plant[g] > 0 else -(int(g) + 1), str(fam[g]))
        if key not in key_index:
            key_index[key] = len(keys)
            keys.append(key)
        member_cluster[j] = key_index[key]
    n_c = len(keys)
    su_m, ut_m, dt_m = _member_class_physics(fleet, rows)
    cap_m = pmax[rows]
    cap = np.zeros(n_c)
    np.add.at(cap, member_cluster, cap_m)
    su = np.zeros(n_c)
    ut_tab = np.zeros(n_c)
    dt_tab = np.zeros(n_c)
    np.add.at(su, member_cluster, cap_m * su_m)
    np.add.at(ut_tab, member_cluster, cap_m * ut_m)
    np.add.at(dt_tab, member_cluster, cap_m * dt_m)
    with np.errstate(invalid="ignore", divide="ignore"):
        su = np.where(cap > 0, su / cap, 0.0)
        ut_tab = np.where(cap > 0, ut_tab / cap, 0.0)
        dt_tab = np.where(cap > 0, dt_tab / cap, 0.0)
    # Anchor member: the largest-capacity row of each cluster.
    anchor = np.full(n_c, -1, dtype=int)
    best = np.full(n_c, -1.0)
    for j, g in enumerate(rows):
        c = member_cluster[j]
        if cap_m[j] > best[c]:
            best[c] = cap_m[j]
            anchor[c] = int(g)

    plant_code = np.zeros(n_c, dtype=int)
    family = np.empty(n_c, dtype=object)
    n_units = np.ones(n_c, dtype=int)
    mlf = np.zeros(n_c)
    ut_h = np.zeros(n_c, dtype=int)
    dt_h = np.zeros(n_c, dtype=int)
    noload = np.zeros(n_c)
    src_n = np.empty(n_c, dtype=object)
    src_mlf = np.empty(n_c, dtype=object)
    src_utdt = np.empty(n_c, dtype=object)
    src_noload = np.empty(n_c, dtype=object)
    for c, (pc, fm) in enumerate(keys):
        plant_code[c] = pc if pc > 0 else 0
        family[c] = fm
        row = measured.get((pc, fm)) if pc > 0 else None
        group = (
            str(groups[anchor[c]])
            if groups is not None and groups[anchor[c]] is not None
            else GROUP_FOR_FAMILY[fm]
        )
        if row is not None:
            n_units[c] = max(int(row.n_units), 1)
            src_n[c] = "uc-params"
            mlf[c] = float(np.clip(float(row.mlf), 0.0, 1.0))
            src_mlf[c] = "uc-params"
            # Measured minimum RUN (p25 of the plant's on-runs: an observed run
            # bounds a min-run constraint from above, the nyiso-90 / SPP-44
            # convention). The minimum DOWN time stays the PUBLISHED class
            # value: a measured off-gap is how long a unit chose to stay off
            # (a peaker's idle week), not the physical restart bar, and the E1
            # gate reads the physical bar (rule 18) — the posture family's own
            # source. ``uc-params.dt_h`` is kept as a diagnostic column.
            ut_h[c] = max(int(row.ut_h), 1)
            dt_h[c] = max(int(round(dt_tab[c])), 1)
            src_utdt[c] = "uc-params(ut)/class-table(dt)"
        else:
            src_n[c] = "fleet-row" if pc <= 0 else "none->1"
            mlf[c] = float(MIN_STABLE_PCT_PHYSICAL.get(group, 0.0))
            src_mlf[c] = f"MIN_STABLE_PCT_PHYSICAL[{group}]"
            ut_h[c] = max(int(round(ut_tab[c])), 1)
            dt_h[c] = max(int(round(dt_tab[c])), 1)
            src_utdt[c] = "class-table"
        if row is not None and row.noload_mmbtu_h == row.noload_mmbtu_h:
            noload[c] = float(row.noload_mmbtu_h) / n_units[c]
            src_noload[c] = "uc-params"
        elif fm in fallback and float(fallback[fm].hsl_mw) > 0.0:
            fb = fallback[fm]
            noload[c] = (
                float(fb.noload_mmbtu_h) / float(fb.hsl_mw) * cap[c] / n_units[c]
            )
            src_noload[c] = "class-fallback"
        else:
            noload[c] = 0.0
            src_noload[c] = "none->0"
    pbar = np.where(n_units > 0, cap / n_units, 0.0)
    integer = integer_gate(dt_h, su)
    return UcClusterParams(
        member_gen=rows.astype(int),
        member_cluster=member_cluster,
        cluster_of_gen=_cluster_of_gen(fleet.n_gen, rows, member_cluster),
        plant_code=plant_code,
        family=family,
        n_units=n_units,
        pbar_mw=pbar,
        mlf=mlf,
        su_per_mw=su,
        ut_h=ut_h,
        dt_h=dt_h,
        noload_mmbtu_h=noload,
        anchor_gen=anchor,
        integer=integer,
        src_n=src_n,
        src_mlf=src_mlf,
        src_utdt=src_utdt,
        src_noload=src_noload,
    )


def _cluster_of_gen(
    n_gen: int, rows: np.ndarray, member_cluster: np.ndarray
) -> np.ndarray:
    """``(n_gen,)`` cluster index per fleet row (``-1`` outside the set)."""
    out = np.full(n_gen, -1, dtype=int)
    out[rows] = member_cluster
    return out


def params_log_rows(params: UcClusterParams) -> list[dict]:
    """Per-cluster rows for ``uc_solve_log_<y>.json`` (``clusters[]``)."""
    out = []
    for c in range(params.n_clusters):
        out.append(
            {
                "cluster": int(c),
                "plant_code": int(params.plant_code[c]),
                "uc_class": str(params.family[c]),
                "n": int(params.n_units[c]),
                "pbar_mw": float(params.pbar_mw[c]),
                "mlf": float(params.mlf[c]),
                "su_per_mw": float(params.su_per_mw[c]),
                "ut_h": int(params.ut_h[c]),
                "dt_h": int(params.dt_h[c]),
                "noload_mmbtu_h": float(params.noload_mmbtu_h[c]),
                "integer": bool(params.integer[c]),
                "members": int(np.sum(params.member_cluster == c)),
                "src": {
                    "n": str(params.src_n[c]),
                    "mlf": str(params.src_mlf[c]),
                    "ut_dt": str(params.src_utdt[c]),
                    "noload": str(params.src_noload[c]),
                },
            }
        )
    return out


def units_online_from_dispatch(
    params: UcClusterParams, dispatch_rows: np.ndarray
) -> np.ndarray:
    """``(n_c,)`` units needed to carry a cluster dispatch, ``ceil(P / pbar)`` clipped.

    ``dispatch_rows`` is the ``(n_gen,)`` dispatch of one hour (P0's, or a kept
    window's). Used for the first window's initial state and the warm start.
    """
    tot = np.zeros(params.n_clusters)
    np.add.at(
        tot,
        params.member_cluster,
        np.asarray(dispatch_rows, dtype=float)[params.member_gen],
    )
    with np.errstate(invalid="ignore", divide="ignore"):
        units = np.where(
            params.pbar_mw > 0.0, np.ceil(tot / params.pbar_mw - 1e-9), 0.0
        )
    return np.clip(units, 0, params.n_units).astype(int)


def units_needed_for_floor(
    params: UcClusterParams, fleet: FleetArrays, t0: int, t1: int
) -> np.ndarray:
    """``(n_c, t1 - t0)`` lower bound on ``u`` implied by structural member floors.

    A floor on a member (nuclear / CHP / coal must-run / reliability floors,
    all upstream of the hook) is an input the UC respects: ``u >=
    ceil(sum_members floor / pbar)`` (DESIGN section 2.2, last row), where the
    floor is the member's EFFECTIVE P lower bound — ``min_gen`` clipped to
    ``pmax * availability`` — exactly the clip ``model.lp.bounds.build_variable_
    bounds`` applies to the P column (``col_lower = min(col_lower,
    col_upper)``), so the UC never asks for a unit the LP's own floor does
    not (a floor above the available capacity is already released by that
    clip in P0, P1 and the window alike).
    """
    n_t = t1 - t0
    min_gen = getattr(fleet, "min_gen", None)
    if min_gen is None:
        return np.zeros((params.n_clusters, n_t), dtype=int)
    rows = params.member_gen
    floor = np.asarray(min_gen, dtype=float)[rows, t0:t1]
    ceiling = (
        np.asarray(fleet.pmax, dtype=float)[rows][:, None]
        * np.asarray(fleet.availability, dtype=float)[rows, t0:t1]
    )
    tot = np.zeros((params.n_clusters, n_t))
    np.add.at(
        tot,
        params.member_cluster,
        np.maximum(np.minimum(floor, ceiling), 0.0),
    )
    with np.errstate(invalid="ignore", divide="ignore"):
        need = np.where(
            params.pbar_mw[:, None] > 0.0,
            np.ceil(tot / params.pbar_mw[:, None] - 1e-9),
            0.0,
        )
    return np.clip(need, 0, params.n_units[:, None]).astype(int)


def ceil_div_units(x: float, pbar: float, n: int) -> int:
    """``ceil(x / pbar)`` clipped to ``[0, n]`` (scalar helper for tests)."""
    if pbar <= 0.0:
        return 0
    return int(min(max(math.ceil(x / pbar - 1e-9), 0), n))


def units_online_profile(params: UcClusterParams, dispatch: np.ndarray) -> np.ndarray:
    """``(n_c, T)`` units needed to carry a cluster dispatch profile, ``ceil(P / pbar)`` clipped.

    The hourly form of :func:`units_online_from_dispatch` (the warm start's
    ``u`` guess from the P0 dispatch slice).
    """
    d = np.asarray(dispatch, dtype=float)
    tot = np.zeros((params.n_clusters, d.shape[1]))
    np.add.at(tot, params.member_cluster, d[params.member_gen, :])
    with np.errstate(invalid="ignore", divide="ignore"):
        units = np.where(
            params.pbar_mw[:, None] > 0.0,
            np.ceil(tot / params.pbar_mw[:, None] - 1e-9),
            0.0,
        )
    return np.clip(units, 0, params.n_units[:, None]).astype(int)
