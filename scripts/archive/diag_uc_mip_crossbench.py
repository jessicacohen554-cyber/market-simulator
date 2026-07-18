"""DIAGNOSTIC ONLY — MIP unit-commitment cross-benchmark of the LP dispatch.

Audit prompt PP-3.4 (``docs/model-audit-prompt-pack-2026-06.md``): production
stays **pure LP** (CLAUDE.md stack rule — HiGHS via highspy, no MIP in the
solve path). This one-time script quantifies the *LP-relaxation commitment
bias* by taking the exact production LP for one ISO-month, adding true integer
unit-commitment (binary on/off + min-load + min-up/min-down + explicit startup
cost) on the CAMPD "committed" tranches, and solving it as a MIP.

**Nothing in ``src/`` imports this module.** It is a standalone script; it
reuses the production builders read-only (it captures the already-built LP off
a real ``run_scenario_iso`` solve via a local monkeypatch and never mutates the
model). Do not wire it into any production path.

## What it measures

Three solutions on the same one-month horizon, compared on the committed
tranches (and system CO2):

  1. **P1-LP** — the production forecast/scored path exactly as
     ``runner.run_scenario_iso`` produces it (amortized-startup bids, ``pmin=0``
     on every tranche → min-load is *emergent*, DP-1).
  2. **MIP-UC** — base energy cost + explicit per-start cost, with integer
     commitment ``u[g,t]`` forcing each committed tranche to 0 or its min-load
     block once synced, plus min-up / min-down.
  3. **LP-relax** — the *same* model as MIP-UC with ``u/su/sd`` relaxed to
     ``[0,1]``. The **MIP-UC − LP-relax** gap is the pure integrality bias
     (same objective, same constraints — only integrality differs).

Reported per solution: committed-tranche min-load energy (MWh), start counts
(``commitment.find_runs``), and total system CO2 (t). The deltas quantify how
much the LP relaxation under-books min-load energy and over-books cycling.

## Scope / tractability

Per-plant CAMPD committed tranches × 744 h × 3 UC vars is a large MIP, so the
integer set is restricted to a fuel class (``--fuel gas_cc`` by default) and the
solve carries a ``--time-limit`` and ``--mip-gap``; the achieved gap is reported.
Everything is a knob so the scope can be widened when runtime allows.

Usage::

    python scripts/archive/diag_uc_mip_crossbench.py --iso ERCOT --year 2026 \
        --hours 744 --fuel gas_cc --time-limit 300 --mip-gap 0.01 \
        --out docs/handoffs
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import scipy.sparse as sp

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import highspy  # noqa: E402

logger = logging.getLogger("uc_mip_crossbench")

_INF = highspy.kHighsInf


# --------------------------------------------------------------------------- #
# Capture: build the production LP for one ISO-month and grab its pieces
# --------------------------------------------------------------------------- #
@dataclass
class CapturedLP:
    """Everything pulled off one instrumented month solve."""

    layout: object
    n_gen: int
    n_zones: int
    T: int
    vars_per_hour: int
    total_columns: int
    # LP arrays (from the built Highs model, P1 objective):
    A: sp.csr_matrix
    col_lower: np.ndarray
    col_upper: np.ndarray
    row_lower: np.ndarray
    row_upper: np.ndarray
    p1_cost: np.ndarray
    # Base-cost energy vector (mc_base on thermal P columns):
    mc_base: np.ndarray  # (n_gen, T)
    # Fleet:
    pmax: np.ndarray
    availability: np.ndarray  # (n_gen, T)
    emission_rate: np.ndarray
    unit_ids: list
    fuel_types: list
    # UC params per generator row (aligned to fleet_arrays):
    min_run_hours: np.ndarray
    min_down_hours: np.ndarray
    startup_cost_per_mw: np.ndarray
    # P1 LP solution:
    p1_dispatch: np.ndarray  # (n_gen, T)
    p1_prices: np.ndarray


def capture_month_lp(iso: str, year: int, hours: int) -> CapturedLP:
    """Run one instrumented ISO-month forecast solve and capture its LP.

    The production model is built and solved unchanged; a local monkeypatch on
    ``runner.generators_to_fleet_arrays`` and ``runner.DispatchModel`` records
    the aligned generator list, the fleet arrays, the built Highs model, the
    base marginal-cost vector, and the P1 dispatch — nothing is mutated.

    Args:
        iso: ISO to build (needs CAMPD per-plant bins for committed tranches).
        year: Forecast year to solve (single-year horizon).
        hours: Sub-annual horizon in hours (e.g. 744 = January).

    Returns:
        The :class:`CapturedLP` bundle.
    """
    from market_sim import runner
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.results import cache

    captured: dict = {}

    orig_g2fa = runner.generators_to_fleet_arrays

    def _wrap_g2fa(generators, *a, **k):
        fa = orig_g2fa(generators, *a, **k)
        captured["generators"] = list(generators)
        captured["fleet_arrays"] = fa
        return fa

    orig_model_cls = runner.DispatchModel

    class _CapturingModel(orig_model_cls):
        def __init__(self, fleet, demand, **kw):
            super().__init__(fleet, demand, **kw)
            captured["model"] = self
            captured["demand"] = np.asarray(demand, dtype=float)

        def solve(self, mc=None, **kw):
            # First solve of the year is P0 (base MC); record it once.
            if "mc_base" not in captured and mc is not None:
                captured["mc_base"] = np.array(mc, dtype=float)
            res = super().solve(mc=mc, **kw)
            captured["last_result"] = res  # final call = P1 (bid MC)
            return res

    # Isolated disposable cache so we never touch the repo results tree.
    import tempfile

    cache.CACHE_ROOT = Path(tempfile.mkdtemp(prefix="uc_mip_cache_"))
    runner.START_YEAR = year
    runner.END_YEAR = year
    runner.generators_to_fleet_arrays = _wrap_g2fa
    runner.DispatchModel = _CapturingModel
    try:
        config = ScenarioConfig(iso=iso, use_campd_bins=True, hours=hours)
        runner.run_scenario_iso(config, iso)
    finally:
        runner.generators_to_fleet_arrays = orig_g2fa
        runner.DispatchModel = orig_model_cls

    model = captured["model"]
    fa = captured["fleet_arrays"]
    generators = captured["generators"]
    p1 = captured["last_result"]
    mc_base = captured["mc_base"]

    # Alignment guard: fleet_arrays rows must match the generator list order.
    ua = list(fa.unit_ids)
    ug = [g.unit_id for g in generators]
    if ua != ug:
        raise RuntimeError(
            "fleet_arrays / generator order mismatch — cannot map UC params"
        )

    layout = model.layout
    lp = model._h.getLp()
    nc, nr = lp.num_col_, lp.num_row_
    am = lp.a_matrix_
    start = np.asarray(am.start_, dtype=np.int64)
    index = np.asarray(am.index_, dtype=np.int64)
    value = np.asarray(am.value_, dtype=np.float64)
    if am.format_ == highspy.MatrixFormat.kRowwise:
        A = sp.csr_matrix((value, index, start), shape=(nr, nc))
    else:
        A = sp.csc_matrix((value, index, start), shape=(nr, nc)).tocsr()

    n_gen = fa.n_gen
    fuel_names = _fuel_type_names()

    return CapturedLP(
        layout=layout,
        n_gen=n_gen,
        n_zones=captured["demand"].shape[0],
        T=hours,
        vars_per_hour=layout.vars_per_hour,
        total_columns=layout.total_columns,
        A=A,
        col_lower=np.asarray(lp.col_lower_, dtype=float),
        col_upper=np.asarray(lp.col_upper_, dtype=float),
        row_lower=np.asarray(lp.row_lower_, dtype=float),
        row_upper=np.asarray(lp.row_upper_, dtype=float),
        p1_cost=np.asarray(lp.col_cost_, dtype=float),
        mc_base=mc_base,
        pmax=np.asarray(fa.pmax, dtype=float),
        availability=np.asarray(fa.availability, dtype=float),
        emission_rate=np.asarray(fa.emission_rate, dtype=float),
        unit_ids=ua,
        fuel_types=[fuel_names[i] for i in np.asarray(fa.fuel_type_idx)],
        min_run_hours=np.array([g.min_run_hours for g in generators], dtype=int),
        min_down_hours=np.array([g.min_down_hours for g in generators], dtype=int),
        startup_cost_per_mw=np.array(
            [g.startup_cost_per_mw for g in generators], dtype=float
        ),
        p1_dispatch=np.asarray(p1.dispatch, dtype=float),
        p1_prices=np.asarray(p1.prices, dtype=float),
    )


def _fuel_type_names() -> list:
    from market_sim.data.fleet import FUEL_TYPE_NAMES

    return list(FUEL_TYPE_NAMES)


# --------------------------------------------------------------------------- #
# MIP assembly
# --------------------------------------------------------------------------- #
def committed_tranche_rows(cap: CapturedLP, fuels: set[str]) -> list[int]:
    """Return generator rows that are a plant's first committed tranche.

    The CAMPD binner encodes the tranche in the ``unit_id`` suffix
    (``..._committed`` or ``..._committed00`` when ramp-spread is on); those are
    the units the UC binaries attach to (``docs/binning-methodology.md``,
    ``commitment.py``). Restricted to ``fuels`` for tractability.
    """
    rows = []
    for g in range(cap.n_gen):
        suffix = cap.unit_ids[g].rpartition("_")[2]
        if suffix.startswith("committed") and cap.fuel_types[g] in fuels:
            rows.append(g)
    return rows


@dataclass
class MIPModel:
    """Assembled extended system (LP block + UC columns/rows)."""

    NC: int  # total columns
    NR: int  # total rows
    A: sp.csr_matrix
    col_lower: np.ndarray
    col_upper: np.ndarray
    row_lower: np.ndarray
    row_upper: np.ndarray
    cost: np.ndarray
    integer_cols: np.ndarray  # u columns (binary)
    u_cols: np.ndarray  # (nu, T) index of u[gi,t]
    su_cols: np.ndarray  # (nu, T)
    committed: list  # generator rows, aligned to u_cols rows
    minload: np.ndarray  # (nu, T) min-load block MW when committed


def build_mip(cap: CapturedLP, committed: list[int], min_load_frac: float) -> MIPModel:
    """Extend the captured LP with integer commitment on ``committed`` rows.

    Adds per committed generator ``g`` and hour ``t``: ``u[g,t]`` (binary,
    on/off), ``su[g,t]`` and ``sd[g,t]`` (start/stop, ``[0,1]``). Linking rows:

    * ``P - cap*u <= 0`` (no energy unless committed),
    * ``P - minload*u >= 0`` (min stable load once committed;
      ``minload = min_load_frac * cap``),
    * ``su >= u_t - u_{t-1}``, ``sd >= u_{t-1} - u_t`` (start / stop detection),
    * min-up ``Σ_{t-UT+1..t} su <= u_t``, min-down ``Σ_{t-DT+1..t} sd + u_t <= 1``.

    Objective = base energy cost (``mc_base`` on thermal P columns, original
    cost elsewhere) + ``startup_cost_per_mw*pmax`` on each ``su``.

    Args:
        cap: The captured LP bundle.
        committed: Generator rows to make integer.
        min_load_frac: Min-load block as a fraction of available capacity
            (1.0 = full committed block, the strongest min-load enforcement).

    Returns:
        The assembled :class:`MIPModel`.
    """
    T = cap.T
    vph = cap.vars_per_hour
    nc = cap.total_columns
    nu = len(committed)

    # --- base-cost objective on all thermal P columns ---------------------- #
    cost = cap.p1_cost.copy()
    p_off = 0  # thermal P block starts each hour (VariableLayout._p_off == 0)
    for g in range(cap.n_gen):
        cols = np.arange(T) * vph + p_off + g
        cost[cols] = cap.mc_base[g, :]

    # --- new UC columns: u | su | sd, each (nu*T) -------------------------- #
    u0 = nc
    su0 = u0 + nu * T
    sd0 = su0 + nu * T
    NC = sd0 + nu * T

    u_cols = (u0 + np.arange(nu * T)).reshape(nu, T)
    su_cols = (su0 + np.arange(nu * T)).reshape(nu, T)
    sd_cols = (sd0 + np.arange(nu * T)).reshape(nu, T)

    col_lower = np.concatenate([cap.col_lower, np.zeros(3 * nu * T)])
    col_upper = np.concatenate([cap.col_upper, np.ones(3 * nu * T)])
    cost = np.concatenate([cost, np.zeros(3 * nu * T)])

    minload = np.zeros((nu, T))
    for gi, g in enumerate(committed):
        capgt = cap.pmax[g] * cap.availability[g, :]  # (T,)
        minload[gi, :] = min_load_frac * capgt
        # startup cost on su columns: $/MW * MW block
        cost[su_cols[gi, :]] = cap.startup_cost_per_mw[g] * cap.pmax[g]

    # --- linking rows (COO triplets) --------------------------------------- #
    rows_i: list[int] = []
    cols_j: list[int] = []
    vals: list[float] = []
    rlo: list[float] = []
    rhi: list[float] = []
    r = 0

    def add_entry(col, val):
        rows_i.append(r)
        cols_j.append(col)
        vals.append(val)

    for gi, g in enumerate(committed):
        UT = max(1, int(cap.min_run_hours[g]))
        DT = max(1, int(cap.min_down_hours[g]))
        for t in range(T):
            p_col = int(np.arange(T)[t] * vph + p_off + g)
            capgt = cap.pmax[g] * cap.availability[g, t]
            u_c = int(u_cols[gi, t])
            su_c = int(su_cols[gi, t])
            sd_c = int(sd_cols[gi, t])

            # 1) P - cap*u <= 0
            add_entry(p_col, 1.0)
            add_entry(u_c, -capgt)
            rlo.append(-_INF)
            rhi.append(0.0)
            r += 1
            # 2) P - minload*u >= 0
            add_entry(p_col, 1.0)
            add_entry(u_c, -minload[gi, t])
            rlo.append(0.0)
            rhi.append(_INF)
            r += 1
            if t >= 1:
                u_prev = int(u_cols[gi, t - 1])
                # 3) su - u_t + u_{t-1} >= 0
                add_entry(su_c, 1.0)
                add_entry(u_c, -1.0)
                add_entry(u_prev, 1.0)
                rlo.append(0.0)
                rhi.append(_INF)
                r += 1
                # 4) sd - u_{t-1} + u_t >= 0
                add_entry(sd_c, 1.0)
                add_entry(u_prev, -1.0)
                add_entry(u_c, 1.0)
                rlo.append(0.0)
                rhi.append(_INF)
                r += 1
            # 5) min-up: Σ_{τ=t-UT+1..t} su_τ - u_t <= 0
            if UT > 1 and t >= UT - 1:
                for tau in range(t - UT + 1, t + 1):
                    add_entry(int(su_cols[gi, tau]), 1.0)
                add_entry(u_c, -1.0)
                rlo.append(-_INF)
                rhi.append(0.0)
                r += 1
            # 6) min-down: Σ_{τ=t-DT+1..t} sd_τ + u_t <= 1
            if DT > 1 and t >= DT - 1:
                for tau in range(t - DT + 1, t + 1):
                    add_entry(int(sd_cols[gi, tau]), 1.0)
                add_entry(u_c, 1.0)
                rlo.append(-_INF)
                rhi.append(1.0)
                r += 1

    n_link = r
    link = sp.coo_matrix((vals, (rows_i, cols_j)), shape=(n_link, NC)).tocsr()

    # top block: original A widened to NC columns
    top = sp.hstack([cap.A, sp.csr_matrix((cap.A.shape[0], NC - nc))], format="csr")
    A_ext = sp.vstack([top, link], format="csr")
    row_lower = np.concatenate([cap.row_lower, np.array(rlo)])
    row_upper = np.concatenate([cap.row_upper, np.array(rhi)])

    return MIPModel(
        NC=NC,
        NR=A_ext.shape[0],
        A=A_ext,
        col_lower=col_lower,
        col_upper=col_upper,
        row_lower=row_lower,
        row_upper=row_upper,
        cost=cost,
        integer_cols=u_cols.ravel(),
        u_cols=u_cols,
        su_cols=su_cols,
        committed=committed,
        minload=minload,
    )


def solve_model(
    mip: MIPModel, integer: bool, time_limit: float, mip_gap: float
) -> dict:
    """Solve the extended system as a MIP (``integer=True``) or its LP relax.

    Args:
        mip: The assembled model.
        integer: Set the ``u`` columns integer when True; continuous otherwise.
        time_limit: HiGHS time limit in seconds.
        mip_gap: Relative MIP gap tolerance.

    Returns:
        Dict with ``col_value`` (primal), ``objective``, ``status``, ``gap``.
    """
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    h.setOptionValue("time_limit", float(time_limit))
    if integer:
        h.setOptionValue("mip_rel_gap", float(mip_gap))
    n = mip.NC
    h.addCols(
        n,
        mip.cost,
        mip.col_lower,
        mip.col_upper,
        0,
        np.array([], np.int32),
        np.array([], np.int32),
        np.array([], np.float64),
    )
    Acsr = mip.A.tocsr()
    h.addRows(
        mip.NR,
        mip.row_lower,
        mip.row_upper,
        len(Acsr.data),
        Acsr.indptr[:-1].astype(np.int32),
        Acsr.indices.astype(np.int32),
        Acsr.data.astype(np.float64),
    )
    if integer:
        ints = mip.integer_cols.astype(np.int32)
        h.changeColsIntegrality(
            len(ints),
            ints,
            np.full(len(ints), highspy.HighsVarType.kInteger),
        )
    h.run()
    info = h.getInfo()
    sol = h.getSolution()
    gap = getattr(info, "mip_gap", float("nan")) if integer else 0.0
    return {
        "col_value": np.asarray(sol.col_value, dtype=float),
        "objective": float(h.getObjectiveValue()),
        "status": str(h.getModelStatus()),
        "gap": float(gap),
    }


# --------------------------------------------------------------------------- #
# Comparison metrics
# --------------------------------------------------------------------------- #
def _dispatch_from_cols(col_value: np.ndarray, cap: CapturedLP) -> np.ndarray:
    """Reshape a primal vector back into the ``(n_gen, T)`` dispatch block."""
    block = col_value[: cap.total_columns].reshape(cap.T, cap.vars_per_hour)
    return block[:, 0 : cap.n_gen].T


def _count_starts(profile: np.ndarray, pmax: float) -> int:
    """Start count of one generator's MW profile via ``commitment.find_runs``."""
    from market_sim.model.commitment import find_runs

    thr = 0.05 * pmax
    return len(find_runs(profile > thr))


def compare(
    cap: CapturedLP,
    mip: MIPModel,
    sol_lp_relax: dict,
    sol_mip: dict,
) -> dict:
    """Compute the committed-tranche + system-CO2 comparison across solutions."""
    committed = mip.committed
    disp = {
        "P1-LP": cap.p1_dispatch,
        "LP-relax": _dispatch_from_cols(sol_lp_relax["col_value"], cap),
        "MIP-UC": _dispatch_from_cols(sol_mip["col_value"], cap),
    }

    def block(name):
        d = disp[name]
        minload_mwh = float(sum(d[g, :].sum() for g in committed))
        starts = int(sum(_count_starts(d[g, :], cap.pmax[g]) for g in committed))
        co2_t = float((d * cap.emission_rate[:, None]).sum())
        return {
            "committed_energy_mwh": round(minload_mwh, 1),
            "committed_starts": starts,
            "system_co2_t": round(co2_t, 1),
        }

    out = {name: block(name) for name in disp}
    base = out["LP-relax"]
    out["deltas_MIP_vs_LPrelax"] = {
        "committed_energy_mwh": round(
            out["MIP-UC"]["committed_energy_mwh"] - base["committed_energy_mwh"], 1
        ),
        "committed_starts": out["MIP-UC"]["committed_starts"]
        - base["committed_starts"],
        "system_co2_t": round(out["MIP-UC"]["system_co2_t"] - base["system_co2_t"], 1),
    }
    p1 = out["P1-LP"]
    out["deltas_MIP_vs_P1"] = {
        "committed_energy_mwh": round(
            out["MIP-UC"]["committed_energy_mwh"] - p1["committed_energy_mwh"], 1
        ),
        "committed_starts": out["MIP-UC"]["committed_starts"] - p1["committed_starts"],
        "system_co2_t": round(out["MIP-UC"]["system_co2_t"] - p1["system_co2_t"], 1),
    }
    return out


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def render_report(
    iso, year, hours, fuels, min_load_frac, cap, mip, sol_mip, cmp, run_date, elapsed
) -> str:
    """Render the committed markdown report for the MIP cross-benchmark."""
    L: list[str] = []
    a = L.append
    a(f"# MIP unit-commitment cross-benchmark — {iso} {year}, first {hours}h")
    a("")
    a(
        f"*Generated {run_date} by `scripts/archive/diag_uc_mip_crossbench.py` "
        "(PP-3.4). **DIAGNOSTIC ONLY — production stays pure LP.***"
    )
    a("")
    a(
        "Quantifies the LP-relaxation commitment bias: the production P1 LP has "
        "`pmin=0` on every tranche (DP-1), so min-load is emergent, not enforced. "
        "This adds true integer commitment (binary on/off + min-load + "
        "min-up/min-down + explicit startup cost) on the CAMPD committed tranches "
        "and compares."
    )
    a("")
    a("## Configuration")
    a("")
    a(f"- **ISO / year / horizon:** {iso} / {year} / first {hours} h")
    a(f"- **Integer fuel class(es):** {', '.join(sorted(fuels))}")
    a(f"- **Committed tranches made integer:** {len(mip.committed)}")
    a(f"- **Min-load block:** {min_load_frac:.2f} x available committed capacity")
    a(
        f"- **MIP columns / rows:** {mip.NC:,} / {mip.NR:,} "
        f"({len(mip.integer_cols):,} binaries)"
    )
    a(f"- **MIP status / gap:** {sol_mip['status']} / {sol_mip['gap']:.3g}")
    a(f"- **Wall clock:** {elapsed:.0f}s")
    a("")
    a("## Results — committed tranches + system CO2")
    a("")
    a("| Solution | Committed energy (MWh) | Committed starts | System CO2 (t) |")
    a("|---|---:|---:|---:|")
    for name in ("P1-LP", "LP-relax", "MIP-UC"):
        r = cmp[name]
        a(
            f"| {name} | {r['committed_energy_mwh']:,.0f} | "
            f"{r['committed_starts']:,} | {r['system_co2_t']:,.0f} |"
        )
    a("")
    a("### Integrality bias (MIP-UC − LP-relax, same objective & constraints)")
    a("")
    d = cmp["deltas_MIP_vs_LPrelax"]
    a(f"- **Committed min-load energy:** {d['committed_energy_mwh']:+,.0f} MWh")
    a(f"- **Committed starts:** {d['committed_starts']:+,}")
    a(f"- **System CO2:** {d['system_co2_t']:+,.0f} t")
    a("")
    a("### Versus production P1 (MIP-UC − P1-LP)")
    a("")
    d = cmp["deltas_MIP_vs_P1"]
    a(f"- **Committed min-load energy:** {d['committed_energy_mwh']:+,.0f} MWh")
    a(f"- **Committed starts:** {d['committed_starts']:+,}")
    a(f"- **System CO2:** {d['system_co2_t']:+,.0f} t")
    a("")
    a("## Reading the sign")
    a("")
    a(
        "- **Min-load energy up under the MIP** ⇒ the LP under-books the energy a "
        "committed unit must produce once synced (it ramps continuously from 0). "
        "That energy displaces marginal generation and shifts the CO2 tally."
    )
    a(
        "- **Starts down under the MIP** ⇒ min-up/min-down suppress the fast "
        "on/off cycling the LP relaxation allows for free, so the LP over-books "
        "cycling (and under-books the startup fuel/CO2 that EM-5 notes is unmodeled)."
    )
    a(
        "- The **MIP−LP-relax** row is the clean integrality bias (identical "
        "economics); the **MIP−P1** row also folds in the base-cost vs "
        "amortized-bid difference and is the 'vs what production ships' view."
    )
    a("")
    a("## Caveats")
    a("")
    a(
        "- Integer set restricted to one fuel class for tractability; a bounded "
        "MIP gap means the reported MIP is near- not provably-optimal (gap above)."
    )
    a(
        "- One month is a commitment snapshot, not an annual bias; widen `--hours` "
        "/ `--fuel` when runtime allows."
    )
    a(
        "- `min_load_frac=1.0` treats the committed tranche as a full sync block "
        "(the strongest min-load); lower it to model partial min-stable-load."
    )
    a(
        "- **This never enters production** (CLAUDE.md pure-LP stack rule); nothing "
        "in `src/` imports this script."
    )
    a("")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--iso", default="ERCOT")
    p.add_argument("--year", type=int, default=2026)
    p.add_argument("--hours", type=int, default=744, help="Horizon hours (744=Jan).")
    p.add_argument(
        "--fuel",
        nargs="+",
        default=["gas_cc"],
        help="Fuel class(es) whose committed tranches become integer.",
    )
    p.add_argument("--min-load-frac", type=float, default=1.0)
    p.add_argument("--time-limit", type=float, default=300.0)
    p.add_argument("--mip-gap", type=float, default=0.01)
    p.add_argument("--out", default="docs/handoffs")
    return p


def main(argv: list[str] | None = None) -> None:
    """Run the one-time MIP UC cross-benchmark and write the report."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    args = _parser().parse_args(argv)
    iso = args.iso.upper()
    fuels = set(args.fuel)

    t0 = time.perf_counter()
    logger.info("capturing production LP: %s %d first %dh", iso, args.year, args.hours)
    cap = capture_month_lp(iso, args.year, args.hours)

    committed = committed_tranche_rows(cap, fuels)
    if not committed:
        raise SystemExit(f"no committed tranches for fuels {fuels} in {iso}")
    logger.info("committed tranches (integer set): %d", len(committed))

    mip = build_mip(cap, committed, args.min_load_frac)
    logger.info(
        "MIP: %d cols / %d rows / %d binaries", mip.NC, mip.NR, len(mip.integer_cols)
    )

    logger.info("solving LP relaxation ...")
    sol_lp = solve_model(
        mip, integer=False, time_limit=args.time_limit, mip_gap=args.mip_gap
    )
    logger.info("LP-relax: %s obj=%.3g", sol_lp["status"], sol_lp["objective"])

    logger.info("solving MIP ...")
    sol_mip = solve_model(
        mip, integer=True, time_limit=args.time_limit, mip_gap=args.mip_gap
    )
    logger.info(
        "MIP: %s obj=%.3g gap=%.3g",
        sol_mip["status"],
        sol_mip["objective"],
        sol_mip["gap"],
    )

    cmp = compare(cap, mip, sol_lp, sol_mip)
    elapsed = time.perf_counter() - t0

    out_dir = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_date = date.today().isoformat()
    fuel_tag = "-".join(sorted(fuels))
    frac_tag = f"mlf{args.min_load_frac:.2f}".replace(".", "")
    stem = (
        f"mip-uc-crossbench-{iso.lower()}-{args.year}-{fuel_tag}-{frac_tag}-{run_date}"
    )
    report = render_report(
        iso,
        args.year,
        args.hours,
        fuels,
        args.min_load_frac,
        cap,
        mip,
        sol_mip,
        cmp,
        run_date,
        elapsed,
    )
    (out_dir / f"{stem}.md").write_text(report)
    (out_dir / f"{stem}.json").write_text(
        json.dumps(
            {
                "iso": iso,
                "year": args.year,
                "hours": args.hours,
                "fuels": sorted(fuels),
                "min_load_frac": args.min_load_frac,
                "n_committed": len(committed),
                "mip_cols": mip.NC,
                "mip_rows": mip.NR,
                "mip_status": sol_mip["status"],
                "mip_gap": sol_mip["gap"],
                "elapsed_s": round(elapsed, 1),
                "comparison": cmp,
            },
            indent=2,
        )
    )
    logger.info("wrote %s", out_dir / f"{stem}.md")
    print(f"MIP cross-benchmark report: {out_dir / f'{stem}.md'}")


if __name__ == "__main__":
    main()
