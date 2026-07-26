"""neiso-67 — STEP 2 of the freeze-lift lane: is the COMMITMENT test informative
where the MARGINAL test is not?

`FINDING-neiso66-overcount-rootcause-2026-07-26.md` settles what the residual
CAMPD outage over-count *is* — a definitional seam, available-but-not-committed
capacity (§5, confirmed against ISO-NE's own published uncommitted column, §5b).
Its §4 also shows the guard's marginal-cost discriminator has **no power** on that
population: the units sit fully stopped for a median ~10 days at an inframarginal
spread within $0.50-0.80/MWh of the spread they run on. On marginal cost, idle and
running are the same state.

§6 step 2 is the open question this probe answers, and it is a question about
POWER, not about the seam's existence:

    does the observed idle/run split track START-COST RECOVERY over the expected
    run (start cost vs spread x expected run hours), per unit?

The hypothesis is that the binding economics live *above* the margin. A unit in
merit at +$4/MWh recovers a $48.6/MW f-class start only if it can hold a ~12-hour
block; if the in-merit stretch is 4 hours it earns $16/MW and correctly declines.
The discriminating variable is then the INTEGRAL of the spread over the achievable
committed run — which is exactly what a per-hour marginal test integrates away.

Construction (measured inputs only; rules 11/13/26 clean — no LP solve, no LMP,
no cleared price, no cleared quantity, no dispatch outcome and no residual is an
INPUT anywhere):

* ``SRMC_u(t) = HR_u x px(u, t)`` — the charter D1 construction, reused verbatim
  from :mod:`scripts.lib.outage_detect` (measured CAMPD heat rate x delivered
  fuel price).
* ``RCC(t)`` — the charter D1 revealed clearing cost, the capacity-weighted
  ``MERIT_RCC_PCTL`` quantile of SRMC over the units measured running at ``t``,
  **recomputed LEAVE-ONE-OUT for every unit under test**. This is the one place
  the probe must go beyond the guard: the guard asks "was this window out of
  merit", where the unit is off and contributes nothing to its own reference. The
  probe compares idle days against RUNNING days, and on a running day the unit IS
  in its own RCC panel — a running in-merit unit adds weight below the p90 and so
  nudges the quantile up, biasing the measured spread on running hours *toward*
  the hypothesis. Leave-one-out removes that channel entirely.
* **start cost and minimum run** — the published NREL/SR-5500-55433 tables already
  in ``config/constants.py`` (``CC_/CT_/ST_GAS_STARTUP_PARAMS``,
  ``*_COMMITMENT_PARAMS``, ``BIN_STARTUP_COST_PER_MW['COAL']``), selected by the
  unit's CAMPD-reported ``unitType`` (a physical fact: combined cycle / combustion
  turbine / boiler) and then by its OWN MEASURED heat rate, which picks the class
  row (h-class / f-class / older). No class-name tuning knob and no fitted scalar
  enters (rules 17/20/24).
* the **expected run** — the maximum-sum contiguous block of at least
  ``min_run_hours`` inside a forward horizon of ``max(24, min_run_hours)`` hours
  from the day start (``DA_COMMITMENT_HORIZON_HOURS`` = 24: every US DAM commits
  one operating day at a time). O(H) prefix-sum scan, so the block is the one the
  unit would actually pick, not a fixed window.

  ``margin_d`` = sum of ``RCC_loo - SRMC_u`` over that block, in $/MW.
  ``R_d = margin_d / start_cost_u`` — the RECOVERY RATIO. ``R >= 1`` means the
  start pays for itself; ``R < 1`` means it does not.

Three reports:

* **A — head-to-head power.** AUC of ``R`` for predicting "the unit started on
  day d", over start-opportunity days (unit off at the previous hour), against
  the two marginal metrics on the identical population: the mean hourly spread
  and the guard's own out-of-merit share. This is the direct §4 rematch.
* **B — the seam population.** The §4 table re-run with the commitment metric:
  booked-out days the guard KEPT (the excess) versus the same units' running
  days. §4's marginal gap was +$0.47-0.82/MWh; the question is whether the
  commitment gap is wide.
* **C — NEISO published control.** Split idle capacity by the test into
  ``R < 1`` (declines to start: predicted UNCOMMITTED) and ``R >= 1`` (idle
  despite recovery: predicted MECHANICAL), and correlate each monthly against
  ISO-NE's two published columns, with a proportion-matched random placebo.
  This is the same identification standard the charter's D1 positive control
  met, applied to the commitment metric.

Caveats, stated up front because they bound the reading:

* **Perfect foresight.** The block is picked from realized RCC/SRMC; a real
  commitment uses a day-ahead forecast. This is an ex-post economic test, so it
  is an upper bound on the information a same-day forecast could carry.
* **Energy-only margin.** Capacity, ancillary and RMR revenues are omitted, and
  NEISO has all three. Every one of them is a reason a unit starts when
  ``R < 1``, so they can only DEPRESS the measured power — a positive result
  here is conservative.
* **Mechanical outages are noise in the dependent variable.** A unit that is
  genuinely broken does not start whatever ``R`` says. Same direction: it can
  only depress the AUC.
* Scope caveat unchanged from neiso-64/66: the extract is CEMS-thermal while the
  published columns are whole-fleet, so report C's robust axis is the monthly
  correlation, not the level.

Usage::

    python scripts/probes/_neiso67_startcost_recovery.py --iso NEISO
    python scripts/probes/_neiso67_startcost_recovery.py --iso NEISO CAISO --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import (  # noqa: E402
    CC_COMMITMENT_PARAMS,
    CC_STARTUP_PARAMS,
    CT_COMMITMENT_PARAMS,
    CT_STARTUP_PARAMS,
    DA_COMMITMENT_HORIZON_HOURS,
    ST_GAS_COMMITMENT_PARAMS,
    ST_GAS_STARTUP_PARAMS,
)
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet.eia860 import (  # noqa: E402
    BIN_STARTUP_COST_PER_MW,
    COAL_BIN_MIN_RUN_HOURS,
)
from scripts.lib.outage_detect import (  # noqa: E402
    MERIT_HR_MAX,
    MERIT_HR_MIN,
    MERIT_OOM_FRAC,
    MERIT_RCC_PCTL,
    MIN_REAL_RUN_HOURS,
    REAL_RUN_CF,
    _MERIT_COAL_FUELS,
    _MERIT_GAS_FUELS,
    _MERIT_UNIT_LEVEL_DIR,
    _delivered_coal_price_tables,
    delivered_gas_price_hourly,
)

NEISO_PUBLISHED = REPO / "data" / "raw" / "neiso-operable-capacity"
EXTRACT = REPO / "data" / "raw" / "campd-unit-outages-{iso}.csv"

# CAMPD-reported unitType -> commitment class. The unitType is the unit's
# PHYSICAL configuration as reported to EPA, not a model tuning class, so this
# map carries no free parameter (rule 17): it only routes each unit to the
# published NREL/SR-5500-55433 table for its own technology. Anything not
# matched here falls through to the boiler branch, which is the conservative
# assignment (the longest min-run and the largest start cost).
_CC_TYPES = ("combined cycle",)
_CT_TYPES = ("combustion turbine",)

# The share of a horizon's hours that must carry BOTH a finite unit SRMC and a
# finite leave-one-out RCC for the day to be evaluated at all. Below this the
# day is dropped rather than imputed — the probe never fabricates a price
# (charter D4, fail-safe).
MIN_PRICED_SHARE: float = 0.90


@dataclass(frozen=True)
class UnitSpec:
    """One identified unit's measured physics and its published start economics."""

    facility_id: int
    unit_id: str
    unit_type: str
    fuel: str
    heat_rate: float
    capacity_mw: float
    start_cost_per_mw: float
    min_run_hours: int
    commit_class: str


def _table_pick(table: list, heat_rate: float):
    """First row of an ascending heat-rate-keyed NREL table that covers ``heat_rate``."""
    for cutoff, val in table:
        if heat_rate <= cutoff:
            return val
    return table[-1][1]


def start_economics(
    unit_type: str, fuel: str, heat_rate: float
) -> tuple[float, int, str]:
    """Return ``(start_cost_$/MW, min_run_hours, class)`` for one measured unit.

    The unit's CAMPD ``unitType`` selects the technology's published table and
    its OWN MEASURED heat rate selects the row within it (h-class / f-class /
    older for CC; aero / frame / older for CT; efficient / subcritical for gas
    steam). Coal takes the CAMPD-binning constants, whose 36-hour minimum run is
    the physical boiler warm-up window.
    """
    ut = unit_type.strip().lower()
    if fuel in _MERIT_COAL_FUELS:
        return (
            float(BIN_STARTUP_COST_PER_MW["COAL"]),
            int(COAL_BIN_MIN_RUN_HOURS),
            "COAL",
        )
    if any(ut.startswith(t) for t in _CC_TYPES):
        return (
            float(_table_pick(CC_STARTUP_PARAMS, heat_rate)),
            int(_table_pick(CC_COMMITMENT_PARAMS, heat_rate)["min_run_hours"]),
            "CC",
        )
    if any(ut.startswith(t) for t in _CT_TYPES):
        return (
            float(_table_pick(CT_STARTUP_PARAMS, heat_rate)),
            int(_table_pick(CT_COMMITMENT_PARAMS, heat_rate)["min_run_hours"]),
            "CT",
        )
    return (
        float(_table_pick(ST_GAS_STARTUP_PARAMS, heat_rate)),
        int(_table_pick(ST_GAS_COMMITMENT_PARAMS, heat_rate)["min_run_hours"]),
        "ST",
    )


@dataclass
class ExtendedPanel:
    """The charter D1 merit panel plus everything the commitment test needs.

    ``srmc`` / ``running`` are ``(n_units, n_hours)``; ``rcc_loo`` is the same
    shape and holds each unit's OWN leave-one-out revealed clearing cost.
    """

    iso: str
    year: int
    units: list[UnitSpec]
    srmc: np.ndarray
    running: np.ndarray
    rcc: np.ndarray
    rcc_loo: np.ndarray


def build_extended_panel(
    iso: str, year: int, n_hours: int, states: tuple[str, ...], rcc_pctl: float
) -> ExtendedPanel | None:
    """Build the leave-one-out merit panel for one ISO-year, or ``None``.

    The SRMC leg reproduces :func:`outage_detect.build_merit_order_panel`
    exactly — same running test, same clipped measured heat rate, same fuel
    routing, same cogeneration exclusion — so report B is measured on the
    identical population the guard scores. The additions are the retained
    ``running`` / capacity arrays, the ``unitType``-keyed start economics, and
    the leave-one-out RCC.
    """
    frames = []
    for st in states:
        path = _MERIT_UNIT_LEVEL_DIR / f"{st}_{year}.parquet"
        if path.exists():
            frames.append(
                pd.read_parquet(
                    path,
                    columns=[
                        "stateCode",
                        "facilityId",
                        "unitId",
                        "date",
                        "hour",
                        "grossLoad",
                        "steamLoad",
                        "heatInput",
                        "primaryFuelInfo",
                        "unitType",
                    ],
                )
            )
    if not frames:
        return None
    c = pd.concat(frames, ignore_index=True)
    c["facilityId"] = pd.to_numeric(c["facilityId"], errors="coerce")
    c = c.dropna(subset=["facilityId"])
    c["facilityId"] = c["facilityId"].astype(int)
    c["unitId"] = c["unitId"].astype(str)
    c["date"] = pd.to_datetime(c["date"])
    c["hour"] = pd.to_numeric(c["hour"], errors="coerce")
    c = c.dropna(subset=["hour"])
    for col in ("grossLoad", "steamLoad", "heatInput"):
        c[col] = pd.to_numeric(c[col], errors="coerce").fillna(0.0)
    c["_h"] = (
        (c["date"] - pd.Timestamp(f"{year}-01-01")).dt.days * 24 + c["hour"].astype(int)
    ).to_numpy()
    c = c[(c["_h"] >= 0) & (c["_h"] < n_hours)]
    if c.empty:
        return None

    gas_px = delivered_gas_price_hourly(iso, year, n_hours)
    coal_tables = _delivered_coal_price_tables(frozenset(str(s) for s in states), year)
    month_of = pd.date_range(
        f"{year}-01-01", periods=n_hours, freq="h"
    ).month.to_numpy()

    units: list[UnitSpec] = []
    srmc_rows: list[np.ndarray] = []
    run_rows: list[np.ndarray] = []
    for (fid, uid), g in c.groupby(["facilityId", "unitId"], observed=True):
        gross = np.zeros(n_hours, dtype=float)
        heat = np.zeros(n_hours, dtype=float)
        steam = np.zeros(n_hours, dtype=float)
        hi = g["_h"].to_numpy(dtype=int)
        np.add.at(gross, hi, g["grossLoad"].to_numpy(dtype=float))
        np.add.at(heat, hi, g["heatInput"].to_numpy(dtype=float))
        np.add.at(steam, hi, g["steamLoad"].to_numpy(dtype=float))
        if steam.any():
            continue  # cogeneration: heat-driven, carries no merit information
        peak = float(gross.max())
        if peak <= 0.0:
            continue
        run = (gross / peak) >= REAL_RUN_CF
        if int(run.sum()) < MIN_REAL_RUN_HOURS:
            continue
        gl = float(gross[run].sum())
        if gl <= 0.0:
            continue
        hr = float(np.clip(heat[run].sum() / gl, MERIT_HR_MIN, MERIT_HR_MAX))
        fuel = str(g["primaryFuelInfo"].iloc[0]).strip().lower()
        if fuel in _MERIT_COAL_FUELS:
            if coal_tables is None:
                continue
            plant_t, state_t, iso_t = coal_tables
            st = str(g["stateCode"].iloc[0])
            px = np.array(
                [
                    plant_t.get((int(fid), int(m)))
                    or state_t.get((st, int(m)))
                    or iso_t.get(int(m))
                    or np.nan
                    for m in month_of
                ],
                dtype=float,
            )
        elif fuel in _MERIT_GAS_FUELS:
            if gas_px is None:
                continue
            px = gas_px
        else:
            continue
        if not np.isfinite(px).any():
            continue
        ut = str(g["unitType"].iloc[0])
        sc, mrh, klass = start_economics(ut, fuel, hr)
        units.append(
            UnitSpec(
                facility_id=int(fid),
                unit_id=str(uid),
                unit_type=ut,
                fuel=fuel,
                heat_rate=hr,
                capacity_mw=peak,
                start_cost_per_mw=sc,
                min_run_hours=mrh,
                commit_class=klass,
            )
        )
        srmc_rows.append(hr * px)
        run_rows.append(run)
    if not units:
        return None

    s_mat = np.vstack(srmc_rows)
    r_mat = np.vstack(run_rows)
    w_vec = np.array([u.capacity_mw for u in units], dtype=float)
    n, T = s_mat.shape

    # Capacity-weighted quantile of SRMC over the RUNNING units, every hour at
    # once (the guard's own vectorised construction). Off/unpriced units are
    # pushed to the top with +inf and carry zero weight, so every positive-weight
    # row sorts ahead of every zero-weight row.
    on = r_mat & np.isfinite(s_mat)
    s_sort = np.where(on, s_mat, np.inf)
    order = np.argsort(s_sort, axis=0, kind="stable")
    s_sorted = np.take_along_axis(s_sort, order, axis=0)
    w_sorted = np.take_along_axis(np.where(on, w_vec[:, None], 0.0), order, axis=0)
    total = w_sorted.sum(axis=0)
    cum = np.cumsum(w_sorted, axis=0)
    live = total > 0.0
    hit = np.argmax(cum >= rcc_pctl * np.where(live, total, 1.0), axis=0)
    rcc = np.where(live, np.take_along_axis(s_sorted, hit[None, :], axis=0)[0], np.nan)

    # Leave-one-out. ranks[j, t] is unit j's position in hour t's sort, so
    # dropping its weight is cum -= w_j above its own rank. The unit can never be
    # SELECTED as its own reference: at k == rank_j the LOO cumulative equals the
    # value at k - 1, so the first-True argmax always lands at or before k - 1.
    ranks = np.empty_like(order)
    np.put_along_axis(
        ranks, order, np.arange(n)[:, None] + np.zeros(T, dtype=int), axis=0
    )
    rowidx = np.arange(n)[:, None]
    rcc_loo = np.empty_like(s_mat)
    for j in range(n):
        wj = np.where(on[j], w_vec[j], 0.0)
        tot_j = total - wj
        cum_j = cum - wj[None, :] * (rowidx >= ranks[j][None, :])
        live_j = tot_j > 0.0
        hit_j = np.argmax(cum_j >= rcc_pctl * np.where(live_j, tot_j, 1.0), axis=0)
        v = np.take_along_axis(s_sorted, hit_j[None, :], axis=0)[0]
        rcc_loo[j] = np.where(live_j & np.isfinite(v), v, np.nan)

    if not np.isfinite(rcc_loo).any():
        return None
    return ExtendedPanel(
        iso=iso.upper(),
        year=int(year),
        units=units,
        srmc=s_mat,
        running=r_mat,
        rcc=rcc,
        rcc_loo=rcc_loo,
    )


def best_block_margin(spread: np.ndarray, min_len: int) -> float:
    """Max sum over contiguous sub-blocks of ``spread`` of length >= ``min_len``.

    The block the unit would actually pick out of the horizon: an O(H)
    prefix-sum scan (running minimum of the prefix at least ``min_len`` behind),
    not a fixed window. ``NaN`` when the horizon is shorter than ``min_len``.
    """
    h = spread.size
    if min_len > h or min_len < 1:
        return float("nan")
    pre = np.concatenate(([0.0], np.cumsum(spread)))
    best = -np.inf
    run_min = np.inf
    for j in range(min_len, h + 1):
        run_min = min(run_min, pre[j - min_len])
        best = max(best, pre[j] - run_min)
    return float(best)


def auc(score: np.ndarray, label: np.ndarray) -> float:
    """Mann-Whitney AUC: P(score of a positive > score of a negative), ties at 0.5."""
    score = np.asarray(score, dtype=float)
    label = np.asarray(label, dtype=bool)
    ok = np.isfinite(score)
    score, label = score[ok], label[ok]
    npos, nneg = int(label.sum()), int((~label).sum())
    if npos == 0 or nneg == 0:
        return float("nan")
    r = pd.Series(score).rank().to_numpy()
    return float((r[label].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))


def unit_day_table(
    panel: ExtendedPanel, horizon_floor: int = DA_COMMITMENT_HORIZON_HOURS
) -> pd.DataFrame:
    """One row per identified unit-day with the commitment and marginal metrics.

    Columns: the recovery ratio ``R`` and its parts, the two marginal metrics on
    the identical horizon (``mean_spread``, ``oom_share`` — the guard's own),
    and the observed operation (``ran``, ``started``, ``off_at_dawn``).
    """
    T = panel.srmc.shape[1]
    n_days = T // 24
    rows = []
    for j, u in enumerate(panel.units):
        spread_full = panel.rcc_loo[j] - panel.srmc[j]
        run = panel.running[j]
        horizon = max(int(horizon_floor), int(u.min_run_hours))
        for d in range(n_days):
            a = d * 24
            b = min(a + horizon, T)
            if b - a < u.min_run_hours:
                continue
            sp = spread_full[a:b]
            finite = np.isfinite(sp)
            if finite.mean() < MIN_PRICED_SHARE:
                continue
            # Unpriced hours contribute nothing rather than an imputed price.
            sp_z = np.where(finite, sp, 0.0)
            margin = best_block_margin(sp_z, int(u.min_run_hours))
            day = slice(a, min(a + 24, T))
            rows.append(
                {
                    "facility_id": u.facility_id,
                    "unit_id": u.unit_id,
                    "commit_class": u.commit_class,
                    "capacity_mw": u.capacity_mw,
                    "start_cost_per_mw": u.start_cost_per_mw,
                    "min_run_hours": u.min_run_hours,
                    "day": d,
                    "margin_per_mw": margin,
                    "R": margin / u.start_cost_per_mw,
                    "mean_spread": float(np.nanmean(sp[finite])),
                    "oom_share": float((sp[finite] < 0).mean()),
                    "ran": bool(run[day].any()),
                    "off_at_dawn": bool(a == 0 or not run[a - 1]),
                }
            )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["started"] = df["ran"] & df["off_at_dawn"]
        df["date"] = pd.Timestamp(f"{panel.year}-01-01") + pd.to_timedelta(
            df["day"], "D"
        )
    return df


def _power_block(op: pd.DataFrame, label: str) -> None:
    """One AUC head-to-head over a start-opportunity population."""
    print(
        f"      {label}: {len(op):,} start-opportunity unit-days, {int(op['started'].sum()):,} started"
    )
    if op.empty or op["started"].nunique() < 2:
        print("        (degenerate population — no contrast)")
        return
    y = op["started"].to_numpy()
    print(
        f"        AUC   commitment R {auc(op['R'].to_numpy(), y):.3f}"
        f" | margin $/MW {auc(op['margin_per_mw'].to_numpy(), y):.3f}"
        f" | marginal mean spread {auc(op['mean_spread'].to_numpy(), y):.3f}"
        f" | guard in-merit share {auc(-op['oom_share'].to_numpy(), y):.3f}"
    )
    a, b = op.loc[op["started"], "R"], op.loc[~op["started"], "R"]
    print(
        f"        median R  started {a.median():7.2f}  declined {b.median():7.2f}"
        f"   |  share R>=1  started {float((a >= 1).mean()):5.1%}  declined {float((b >= 1).mean()):5.1%}"
    )


def report_a(df: pd.DataFrame, year: int) -> None:
    """Head-to-head power: does the commitment metric separate what the marginal
    metric cannot?

    Reported on two populations. ALL start-opportunity days includes days the
    unit was booked out, where it could not have started whatever its economics
    — pure noise in the dependent variable. AVAILABLE days drop those, and are
    the population the question is actually about.
    """
    print(
        f"\n  {year}  A. START-OPPORTUNITY DISCRIMINATION (unit off at the previous hour)"
    )
    op = df[df["off_at_dawn"]]
    _power_block(op, "ALL      ")
    _power_block(op[~op["booked_any"]], "AVAILABLE")
    q = df["R"].quantile([0.05, 0.25, 0.5, 0.75, 0.95])
    print(
        "      R distribution over all evaluable unit-days:  "
        + "  ".join(f"p{int(k * 100)} {v:.2f}" for k, v in q.items())
        + f"   |  share R>=1 {float((df['R'] >= 1).mean()):.1%}"
    )
    report_a_per_unit(df)


def report_a_per_unit(df: pd.DataFrame, min_each: int = 20) -> None:
    """PER-UNIT discrimination — the form §6 step 2 actually asks for.

    Pooling across units mixes very different start costs and heat rates, so a
    pooled AUC can be diluted by cross-unit heterogeneity alone. This scores each
    unit against ITS OWN start/decline days and reports the distribution, which
    is immune to that. Units need ``min_each`` days on both sides to be scored.
    """
    op = df[df["off_at_dawn"] & ~df["booked_any"]]
    rows = []
    for (fid, uid), g in op.groupby(["facility_id", "unit_id"], observed=True):
        npos, nneg = int(g["started"].sum()), int((~g["started"]).sum())
        if npos < min_each or nneg < min_each:
            continue
        y = g["started"].to_numpy()
        rows.append(
            {
                "cap": float(g["capacity_mw"].iloc[0]),
                "klass": g["commit_class"].iloc[0],
                "auc_R": auc(g["R"].to_numpy(), y),
                "auc_spread": auc(g["mean_spread"].to_numpy(), y),
            }
        )
    if not rows:
        print("      per-unit: no unit carries >= 20 start and 20 decline days")
        return
    u = pd.DataFrame(rows)
    w = u["cap"] / u["cap"].sum()
    print(
        f"      PER-UNIT AUC over {len(u)} units ({u['cap'].sum():,.0f} MW):"
        f"  R  median {u['auc_R'].median():.3f}  cap-wtd {float((u['auc_R'] * w).sum()):.3f}"
        f"  |  mean spread  median {u['auc_spread'].median():.3f}"
        f"  cap-wtd {float((u['auc_spread'] * w).sum()):.3f}"
    )
    print(
        f"        units where R beats 0.55: {int((u['auc_R'] > 0.55).sum())}/{len(u)}"
        f"   |  R below 0.45 (anti-predictive): {int((u['auc_R'] < 0.45).sum())}/{len(u)}"
        f"   |  by class "
        + ", ".join(
            f"{k} {v:.3f}" for k, v in u.groupby("klass")["auc_R"].median().items()
        )
    )


def report_sensitivity(df: pd.DataFrame) -> None:
    """Does the START-COST normalisation carry any information at all?

    Scaling every unit's start cost by one global multiple is a monotone
    transform of ``R``, so it cannot move an AUC — that is arithmetic, not
    evidence, and no sweep over it is reported. The lever that CAN matter is
    whether dividing by the published, class-and-heat-rate-varying start cost
    beats not dividing at all. If ``R`` scores below the bare ``margin``, the
    commitment normalisation is subtracting information rather than adding it.
    """
    op = df[df["off_at_dawn"] & ~df["booked_any"]]
    if op.empty or op["started"].nunique() < 2:
        return
    y = op["started"].to_numpy()
    a_m = auc(op["margin_per_mw"].to_numpy(), y)
    a_r = auc(op["R"].to_numpy(), y)
    print(
        f"      start-cost normalisation:  bare margin AUC {a_m:.3f}"
        f"  ->  divided by published start cost {a_r:.3f}"
        f"   ({'ADDS' if a_r > a_m else 'SUBTRACTS'} {abs(a_r - a_m):.3f})"
    )


def report_b(df: pd.DataFrame, year: int) -> None:
    """The §4 rematch on the seam population: booked-out days the guard KEPT
    versus the same units' running days."""
    out = df[df["booked_kept"] & ~df["ran"]]
    ran = df[~df["booked_any"] & df["ran"]]
    both = df[df["booked_kept"] | (~df["booked_any"] & df["ran"])]
    units_out = set(zip(out["facility_id"], out["unit_id"]))
    ran = ran[[k in units_out for k in zip(ran["facility_id"], ran["unit_id"])]]
    print(
        f"\n  {year}  B. SEAM POPULATION (kept booked-out days vs the SAME units' running days)"
    )
    if out.empty or ran.empty:
        print("      insufficient population")
        return
    print(
        f"      booked-OUT unit-days {len(out):6,}  median R {out['R'].median():8.2f}"
        f"   median spread {out['mean_spread'].median():+7.2f} $/MWh   share R>=1 {float((out['R'] >= 1).mean()):5.1%}"
    )
    print(
        f"      RUNNING    unit-days {len(ran):6,}  median R {ran['R'].median():8.2f}"
        f"   median spread {ran['mean_spread'].median():+7.2f} $/MWh   share R>=1 {float((ran['R'] >= 1).mean()):5.1%}"
    )
    print(
        f"      GAP                            R x{ran['R'].median() / out['R'].median() if out['R'].median() > 0 else float('nan'):8.2f}"
        f"   spread {ran['mean_spread'].median() - out['mean_spread'].median():+7.2f} $/MWh"
        "   <- §4 measured the spread column at +0.47 to +0.82"
    )
    lab = both["ran"].to_numpy()
    print(
        f"      AUC over this population:  R {auc(both['R'].to_numpy(), lab):.3f}"
        f"   mean spread {auc(both['mean_spread'].to_numpy(), lab):.3f}"
    )


def report_c(df: pd.DataFrame, year: int, rng: np.random.Generator, draws: int) -> None:
    """NEISO published control: split idle capacity by the test and correlate each
    half against ISO-NE's two published columns."""
    pub_path = NEISO_PUBLISHED / f"neiso_operable_capacity_{year}.csv"
    if not pub_path.exists():
        print(f"\n  {year}  C. published control — {pub_path.name} absent, skipped")
        return
    pub = pd.read_csv(pub_path, parse_dates=["report_date"]).set_index("report_date")
    idle = df[~df["ran"]].copy()
    idle["declines"] = idle["R"] < 1.0
    g = idle.groupby(["date", "declines"])["capacity_mw"].sum().unstack(fill_value=0.0)
    pred_unc = g.get(True, pd.Series(0.0, index=g.index))
    pred_mech = g.get(False, pd.Series(0.0, index=g.index))
    j = (
        pd.DataFrame({"pred_uncommitted": pred_unc, "pred_mechanical": pred_mech})
        .join(
            pub[["gen_outages_reductions_mw", "uncommitted_available_gen_nonfast_mw"]],
            how="inner",
        )
        .dropna()
    )
    if j.empty:
        print(f"\n  {year}  C. published control — no overlapping dates")
        return
    m = j.groupby(j.index.month).mean()
    print(
        f"\n  {year}  C. NEISO PUBLISHED CONTROL (monthly r; idle capacity split by the test)"
    )
    print(
        f"      idle & R<1  (predicted UNCOMMITTED) {j['pred_uncommitted'].mean():6,.0f} MW"
        f"   vs published OUTAGES {m['pred_uncommitted'].corr(m['gen_outages_reductions_mw']):+.2f}"
        f"   vs published UNCOMMITTED {m['pred_uncommitted'].corr(m['uncommitted_available_gen_nonfast_mw']):+.2f}"
    )
    print(
        f"      idle & R>=1 (predicted MECHANICAL)  {j['pred_mechanical'].mean():6,.0f} MW"
        f"   vs published OUTAGES {m['pred_mechanical'].corr(m['gen_outages_reductions_mw']):+.2f}"
        f"   vs published UNCOMMITTED {m['pred_mechanical'].corr(m['uncommitted_available_gen_nonfast_mw']):+.2f}"
    )
    # Reference 1 — no split at all. If total idle capacity already carries the
    # correlation, the split has nothing left to explain.
    tot = j["pred_uncommitted"] + j["pred_mechanical"]
    mt = tot.groupby(tot.index.month).mean()
    print(
        f"      NO SPLIT   total idle capacity        {tot.mean():6,.0f} MW"
        f"   vs published OUTAGES {mt.corr(m['gen_outages_reductions_mw']):+.2f}"
        f"   vs published UNCOMMITTED {mt.corr(m['uncommitted_available_gen_nonfast_mw']):+.2f}"
    )
    # Reference 2 — placebo: same daily idle capacity, same daily declining
    # SHARE, units drawn at random. Anything the split achieves above this band
    # is discrimination rather than the arithmetic of splitting a series in two.
    share = idle.groupby("date")["declines"].mean()
    best = []
    for _ in range(draws):
        idle["_p"] = rng.random(len(idle)) < idle["date"].map(share).to_numpy()
        gp = idle.groupby(["date", "_p"])["capacity_mw"].sum().unstack(fill_value=0.0)
        pu = gp.get(True, pd.Series(0.0, index=gp.index))
        jp = (
            pd.DataFrame({"p": pu})
            .join(pub[["uncommitted_available_gen_nonfast_mw"]], how="inner")
            .dropna()
        )
        if jp.empty:
            continue
        mp = jp.groupby(jp.index.month).mean()
        best.append(mp["p"].corr(mp["uncommitted_available_gen_nonfast_mw"]))
    if best:
        print(
            f"      placebo p95 (same daily idle MW & declining share, {len(best)} draws)"
            f"   vs published UNCOMMITTED {np.nanpercentile(best, 95):+.2f}"
        )
    # Reference 3 — the BEST threshold, not just R = 1. The disposition question
    # is whether ANY commitment-aware cut yields a usable discriminator, so the
    # whole R distribution is swept and the best monthly r is reported. A best-of
    # sweep is optimistically biased by construction; if even that fails to clear
    # the placebo band, no threshold choice rescues the test.
    cuts = np.nanquantile(idle["R"], np.linspace(0.05, 0.95, 19))
    scored = []
    for c in cuts:
        s = idle[idle["R"] < c].groupby("date")["capacity_mw"].sum()
        js = (
            pd.DataFrame({"s": s})
            .join(pub[["uncommitted_available_gen_nonfast_mw"]], how="inner")
            .dropna()
        )
        if len(js) < 60:
            continue
        ms = js.groupby(js.index.month).mean()
        scored.append(
            (ms["s"].corr(ms["uncommitted_available_gen_nonfast_mw"]), float(c))
        )
    if scored:
        r_best, c_best = max(scored)
        print(
            f"      BEST-OF threshold sweep (19 cuts over the R distribution):"
            f"   best monthly r {r_best:+.2f} at R < {c_best:.2f}"
            f"   [{'MARGINAL band — the guard already owns this cut' if c_best <= 0 else 'commitment band'}]"
        )
    # The decisive decomposition for the STEP 3 disposition. R splits into two
    # bands that mean completely different things:
    #   R < 0            the best feasible block has NEGATIVE energy margin, i.e.
    #                    the unit is out of merit across the horizon. This is a
    #                    MARGINAL condition and the merit-order guard already
    #                    owns it (rule 19 [R-ONE-MECH]).
    #   0 <= R < 1       the unit is IN merit yet the best block does not repay
    #                    the start. This band, and only this band, is what a
    #                    commitment-aware second discriminator would contribute.
    bands = {
        "R < 0        (marginal: guard's own cut)": idle["R"] < 0,
        "0 <= R < 1   (COMMITMENT band — the new information)": (idle["R"] >= 0)
        & (idle["R"] < 1),
        "R >= 1       (start repays; idle anyway)": idle["R"] >= 1,
    }
    print(
        "      band decomposition — which cut carries the published-uncommitted shape?"
    )
    for name, sel in bands.items():
        s = idle[sel].groupby("date")["capacity_mw"].sum()
        jb = (
            pd.DataFrame({"s": s})
            .join(
                pub[
                    [
                        "uncommitted_available_gen_nonfast_mw",
                        "gen_outages_reductions_mw",
                    ]
                ],
                how="inner",
            )
            .dropna()
        )
        if len(jb) < 60:
            print(f"        {name:54s}  (too few days)")
            continue
        mb = jb.groupby(jb.index.month).mean()
        print(
            f"        {name:54s} {s.mean():6,.0f} MW"
            f"   r vs UNCOMMITTED {mb['s'].corr(mb['uncommitted_available_gen_nonfast_mw']):+.2f}"
            f"   r vs OUTAGES {mb['s'].corr(mb['gen_outages_reductions_mw']):+.2f}"
        )


def booked_out_days(
    iso: str, year: int, panel: ExtendedPanel
) -> tuple[set[tuple[int, str, int]], set[tuple[int, str, int]]]:
    """Return ``(every booked unit-day, the subset the merit guard KEEPS)``.

    The guard's own veto is re-applied against the SAME panel, so the second set
    is exactly §4's EXCESS-carrying population: windows the guard is correct to
    keep because the unit was in merit. The first set is every extract window
    regardless of verdict, which is what carves the AVAILABLE population — a
    unit-day the detector books as out is a day the unit could not have started
    for reasons outside its economics (mechanical or otherwise), so it is noise
    in a test of the start decision and is excluded rather than modelled.
    """
    path = Path(str(EXTRACT).format(iso=iso.upper()))
    if not path.exists():
        return set(), set()
    e = pd.read_csv(path, parse_dates=["outage_start", "outage_end"])
    y0 = pd.Timestamp(f"{year}-01-01")
    y1 = pd.Timestamp(f"{year}-12-31")
    e = e[(e["outage_end"] >= y0) & (e["outage_start"] <= y1)]
    idx = {(u.facility_id, u.unit_id): j for j, u in enumerate(panel.units)}
    every: set[tuple[int, str, int]] = set()
    kept: set[tuple[int, str, int]] = set()
    for r in e.itertuples(index=False):
        j = idx.get((int(r.facility_id), str(r.unit_id)))
        if j is None:
            continue
        a = int(max((r.outage_start - y0).days, 0))
        b = int(min((r.outage_end - y0).days, panel.srmc.shape[1] // 24 - 1))
        if b < a:
            continue
        sp = panel.rcc[a * 24 : (b + 1) * 24] - panel.srmc[j][a * 24 : (b + 1) * 24]
        ok = np.isfinite(sp)
        # Guard semantics: out of merit is SRMC > RCC, i.e. a negative spread.
        vetoed = bool(ok.any()) and float((sp[ok] < 0).mean()) >= MERIT_OOM_FRAC
        for d in range(a, b + 1):
            every.add((int(r.facility_id), str(r.unit_id), d))
            if not vetoed:
                kept.add((int(r.facility_id), str(r.unit_id), d))
    return every, kept


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="+", default=["NEISO"])
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--rcc-pctl", type=float, default=MERIT_RCC_PCTL)
    ap.add_argument(
        "--horizon",
        type=int,
        default=DA_COMMITMENT_HORIZON_HOURS,
        help="commitment-horizon FLOOR in hours; the actual horizon is "
        "max(this, the unit's min_run_hours)",
    )
    ap.add_argument("--placebo-draws", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20260726)
    ap.add_argument(
        "--dump", type=Path, default=None, help="write the unit-day table here"
    )
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    dumps = []
    for iso in [s.upper() for s in args.iso]:
        states = campd.states_for_iso(iso)
        print(
            f"\n===== {iso} — start-cost recovery vs the observed idle/run split ====="
        )
        print(
            f"  panel: RCC p{args.rcc_pctl:.0%} leave-one-out | horizon max({args.horizon}, min_run) h"
            f" | start costs NREL/SR-5500-55433 by measured unitType x heat rate"
        )
        for year in sorted(args.years):
            n_hours = 8784 if pd.Timestamp(f"{year}-12-31").dayofyear == 366 else 8760
            panel = build_extended_panel(iso, year, n_hours, states, args.rcc_pctl)
            if panel is None:
                print(f"\n  {year}: unidentifiable (no priceable CEMS unit) — skipped")
                continue
            df = unit_day_table(panel, args.horizon)
            if df.empty:
                print(f"\n  {year}: no evaluable unit-days — skipped")
                continue
            byc = (
                pd.DataFrame([u.__dict__ for u in panel.units])
                .groupby("commit_class")
                .agg(units=("unit_id", "size"), mw=("capacity_mw", "sum"))
            )
            print(
                f"\n  {year}: {len(panel.units)} identified units "
                f"({', '.join(f'{k} {int(v.units)}/{v.mw:,.0f} MW' for k, v in byc.iterrows())})"
                f" | {len(df):,} evaluable unit-days"
            )
            every, kept = booked_out_days(iso, year, panel)
            key = list(zip(df["facility_id"], df["unit_id"], df["day"]))
            df["booked_any"] = [k in every for k in key]
            df["booked_kept"] = [k in kept for k in key]
            d_loo = np.abs(panel.rcc_loo - panel.rcc[None, :])
            fin = np.isfinite(d_loo)
            print(
                f"      leave-one-out RCC vs full-panel RCC: mean |delta| "
                f"{float(d_loo[fin].mean()):.3f} $/MWh, p95 {float(np.nanpercentile(d_loo[fin], 95)):.3f}"
                f" (RCC median {float(np.nanmedian(panel.rcc)):.2f} $/MWh)"
            )
            report_a(df, year)
            report_sensitivity(df)
            report_b(df, year)
            if iso == "NEISO":
                report_c(df, year, rng, args.placebo_draws)
            if args.dump is not None:
                dumps.append(df.assign(iso=iso, year=year))
    if args.dump is not None and dumps:
        args.dump.parent.mkdir(parents=True, exist_ok=True)
        pd.concat(dumps, ignore_index=True).to_parquet(args.dump, index=False)
        print(f"\n  unit-day table -> {args.dump}")


if __name__ == "__main__":
    main()
