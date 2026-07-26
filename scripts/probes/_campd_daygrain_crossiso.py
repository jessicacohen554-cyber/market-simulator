"""CAMPD economic-layup charter, LANE B — cross-ISO validation of the DAY-GRAIN
marginal cut as a REPLACEMENT for the merit-order guard's window-grain cut.

`FINDING-neiso67-commitment-test-2026-07-26.md` §6 item 2 flagged an observation
it deliberately did not act on:

    the day-grain best-block ``R < 0`` cut (out of merit across the best feasible
    >= min-run block in the DA horizon) tracked ISO-NE's published UNCOMMITTED
    series at +0.63 to +0.79, where the guard's own window-grain out-of-merit
    share reaches +0.08 to +0.31 (charter D1, KEPT windows).

That is a **marginal**-test refinement inside the guard's existing lane, so
rule 19 ``[R-ONE-MECH]`` makes it a candidate REPLACEMENT for the window-grain
cut and never an addition. neiso-67 measured it on ONE ISO, on the idle-capacity
grain rather than the window grain the guard actually operates on. This probe
validates it where the guard lives — per window, on every ISO that carries a
published instrument — before anything is proposed.

**The two cuts, stated so the head-to-head is exactly like-for-like.** Both are
applied to the SAME window population (the committed guard-on extract UNION its
layup companion — i.e. the guard-off baseline reconstructed from committed
bytes), against the SAME merit panel, with the SAME structural threshold
``MERIT_OOM_FRAC``. Only the grain of the out-of-merit test changes:

* **window-grain (the guard, incumbent)** — a window's out-of-merit share is the
  fraction of its HOURS with ``SRMC_u(t) > RCC(t)``; veto at ``>= MERIT_OOM_FRAC``.
  This re-implements :func:`outage_detect.MeritOrderPanel.is_economic_layup`
  against the same panel, and the run reports how exactly it reproduces the
  committed kept/layup split as a machinery control.
* **day-grain (the candidate)** — a window's out-of-merit share is the fraction
  of its DAYS whose best feasible commitment block is out of merit: the maximum-
  sum contiguous block of at least the unit's published ``min_run_hours`` inside
  a forward horizon of ``max(--horizon, min_run_hours)`` from the day start has
  NEGATIVE energy margin. Veto at the same ``>= MERIT_OOM_FRAC``.

  Note what this is NOT: ``R = margin / start_cost`` and start cost is strictly
  positive, so ``R < 0`` is exactly ``margin < 0`` and the published start-cost
  table drops out of the cut entirely. The cut carries NO start-cost parameter —
  it is a pure marginal condition evaluated over a physically-bounded block,
  which is precisely why it belongs in the guard's existing lane rather than
  stacking a commitment mechanism on it. ``min_run_hours`` (measured
  ``unitType`` x measured heat rate -> the published NREL/SR-5500-55433 row) is
  the only new physical input, and it carries no free parameter.

**The reference price is the FULL-PANEL RCC, not neiso-67's leave-one-out.**
That is not a simplification, it is an identity on this population: LOO removes
unit ``j``'s weight from hour ``t``'s quantile only where ``on[j, t]`` is true
(the unit is measured RUNNING and priced), and every hour scored here is an hour
the extract books the unit as DOWN. With zero weight to remove, ``rcc_loo[j] ==
rcc`` exactly. Using the full-panel RCC therefore reproduces neiso-67's numbers
while also being what the guard itself uses, so the head-to-head is clean.

**Scoring — the full charter D1 standard, per ISO-year, on the same populations:**

* vetoed-by-cut capacity vs the published series (level ratio + monthly r),
* kept-vs-vetoed separation (the kept series is what the model actually reads),
* proportion-matched placebo p95 (same GW-days dropped at random from the same
  baseline, 30 draws) — a cut that does not clear it has subtracted, not
  discriminated,
* the no-split reference (the baseline itself): a cut that does not beat "do
  nothing" has nothing to explain,
* NEISO additionally scores both cuts against ISO-NE's published
  ``uncommitted_available_gen_nonfast_mw`` — the layup population itself — and
  reproduces neiso-67 §2's idle-capacity band control as a port check.

**Level/shape caveat (charter §4, binding on every number here).** The CAMPD
extract is CEMS-thermal (coal / CC / gas-steam) while several published series
are whole-fleet, so a level RATIO is only interpretable where the thermal-only
extract EXCEEDS a whole-fleet published total. The robust cross-ISO axis is the
**monthly correlation**, plus the placebo.

**Published instruments (charter §4).** NEISO ISO-NE Morning Report Section 3;
MISO native outage source; PJM Data Miner 2 DAM availability; ERCOT 60-day DAM
disclosure (with the stated offered-vs-available caveat: DAM offered capacity
conflates mechanical unavailability with a unit that simply did not offer, so it
carries some layup itself and is a conservative instrument for a layup cut);
CAISO CNOG on the reviewed resource->plant crosswalk, built **revision-aware**
(`_neiso65_cnog_revision_rebuild.build_revision`) — ``tail(1)`` and raw-sum are
both wrong and inflate/deflate every ratio (neiso-66 §1). **NYISO has no
published anchor and is excluded**; none is improvised for it.

No LP solve. No guard change. No extract re-derive. No keeper is touched. Every
input is a committed artifact.

Usage::

    python scripts/probes/_campd_daygrain_crossiso.py --iso NEISO
    python scripts/probes/_campd_daygrain_crossiso.py \\
        --iso NEISO CAISO MISO PJM ERCOT \\
        --rcc-pctl 0.50 0.75 0.90 0.99 --horizon 24 48 72 --json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import DA_COMMITMENT_HORIZON_HOURS  # noqa: E402
from market_sim.data import campd  # noqa: E402
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
from scripts.probes._neiso65_cnog_revision_rebuild import (  # noqa: E402
    _segments,
    build_revision,
)
from scripts.probes._neiso67_startcost_recovery import (  # noqa: E402
    MIN_PRICED_SHARE,
    start_economics,
)

RAW = REPO / "data" / "raw"

# The committed guard-on extract and its layup companion, per ISO. Their UNION
# is the guard-off baseline population, reconstructed from committed bytes —
# no re-derive is run (charter: measurement only).
_EXTRACTS: dict[str, tuple[str, str]] = {
    "ERCOT": ("campd-unit-outages.csv", "campd-unit-outages-layup.csv"),
    "NEISO": ("campd-unit-outages-NEISO.csv", "campd-unit-outages-layup-NEISO.csv"),
    "CAISO": ("campd-unit-outages-CAISO.csv", "campd-unit-outages-layup-CAISO.csv"),
    "MISO": ("campd-unit-outages-MISO.csv", "campd-unit-outages-layup-MISO.csv"),
    "PJM": ("campd-unit-outages-PJM.csv", "campd-unit-outages-layup-PJM.csv"),
}
# ISOs carrying a published anchor (charter §4). NYISO is deliberately absent.
DEFAULT_ISOS = ("NEISO", "CAISO", "MISO", "PJM", "ERCOT")


# --------------------------------------------------------------------------- #
# measured unit panel                                                          #
# --------------------------------------------------------------------------- #
@dataclass
class UnitArrays:
    """Every identified unit's measured year arrays, independent of any knob.

    Built once per ISO-year and reused across the whole ``rcc_pctl`` x
    ``horizon`` sweep: nothing here depends on either knob, so re-reading the
    CAMPD parquet per configuration would only burn time.
    """

    iso: str
    year: int
    keys: list[tuple[int, str]]
    srmc: np.ndarray  # (n_units, n_hours)
    running: np.ndarray  # (n_units, n_hours) bool
    capacity: np.ndarray  # (n_units,)
    min_run: np.ndarray  # (n_units,) int
    commit_class: list[str]
    n_hours: int
    index: dict[tuple[int, str], int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.index = {k: j for j, k in enumerate(self.keys)}


def load_units(iso: str, year: int, states: tuple[str, ...]) -> UnitArrays | None:
    """Build the charter D1 merit panel's unit side for one ISO-year.

    Reproduces :func:`outage_detect.build_merit_order_panel` exactly — same
    running test, same clipped measured heat rate, same fuel routing, same
    cogeneration exclusion — and additionally retains the running mask, the
    capacity and the unit's published ``min_run_hours`` (measured ``unitType`` x
    measured heat rate), which the day-grain cut needs to size its block.
    """
    n_hours = 8784 if pd.Timestamp(f"{year}-12-31").dayofyear == 366 else 8760
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

    keys: list[tuple[int, str]] = []
    srmc_rows: list[np.ndarray] = []
    run_rows: list[np.ndarray] = []
    caps: list[float] = []
    mruns: list[int] = []
    klasses: list[str] = []
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
        _, mrh, klass = start_economics(str(g["unitType"].iloc[0]), fuel, hr)
        keys.append((int(fid), str(uid)))
        srmc_rows.append(hr * px)
        run_rows.append(run)
        caps.append(peak)
        mruns.append(int(mrh))
        klasses.append(klass)
    if not keys:
        return None
    return UnitArrays(
        iso=iso.upper(),
        year=int(year),
        keys=keys,
        srmc=np.vstack(srmc_rows),
        running=np.vstack(run_rows),
        capacity=np.asarray(caps, dtype=float),
        min_run=np.asarray(mruns, dtype=int),
        commit_class=klasses,
        n_hours=n_hours,
    )


def revealed_clearing_cost(u: UnitArrays, rcc_pctl: float) -> np.ndarray:
    """The charter D1 ``RCC(t)``: capacity-weighted quantile of SRMC over the
    units measured RUNNING at ``t``. Vectorised exactly as the guard builds it."""
    on = u.running & np.isfinite(u.srmc)
    s_sort = np.where(on, u.srmc, np.inf)
    order = np.argsort(s_sort, axis=0, kind="stable")
    s_sorted = np.take_along_axis(s_sort, order, axis=0)
    w_sorted = np.take_along_axis(np.where(on, u.capacity[:, None], 0.0), order, axis=0)
    total = w_sorted.sum(axis=0)
    cum = np.cumsum(w_sorted, axis=0)
    live = total > 0.0
    hit = np.argmax(cum >= rcc_pctl * np.where(live, total, 1.0), axis=0)
    rcc = np.where(live, np.take_along_axis(s_sorted, hit[None, :], axis=0)[0], np.nan)
    return np.where(np.isfinite(rcc), rcc, np.nan)


def daily_best_block(
    spread: np.ndarray, min_len: int, horizon: int, n_days: int
) -> np.ndarray:
    """Per-day best feasible commitment-block margin, vectorised over the year.

    For day ``d`` starting at hour ``a = 24d``, the value is
    ``max over blocks [i, j) with a <= i < j <= min(a + horizon, T) and
    j - i >= min_len of sum(spread[i:j])`` — the block the unit would actually
    pick out of the day-ahead horizon, not a fixed window.

    Semantics are identical to neiso-67's scalar ``best_block_margin`` scan:
    unpriced hours contribute 0 rather than an imputed price, a day whose
    horizon carries less than ``MIN_PRICED_SHARE`` priced hours is ``NaN``
    (never fabricated), and the horizon truncates at the year end so a day with
    fewer than ``min_len`` remaining hours is ``NaN`` too. The scan is the same
    prefix-sum/running-minimum argument, evaluated for every day at once on a
    ``(n_days, horizon + 1)`` gather.
    """
    t_len = spread.size
    if min_len > horizon or min_len < 1:
        return np.full(n_days, np.nan)
    finite = np.isfinite(spread)
    sp = np.where(finite, spread, 0.0)
    pre = np.concatenate(([0.0], np.cumsum(sp)))  # (T+1,)
    fpre = np.concatenate(([0.0], np.cumsum(finite.astype(float))))  # (T+1,)

    starts = np.arange(n_days, dtype=int) * 24
    k = np.arange(horizon + 1, dtype=int)
    idx = starts[:, None] + k[None, :]  # (D, H+1)
    valid = idx <= t_len
    gathered = pre[np.minimum(idx, t_len)]

    # running minimum of the prefix over the block's admissible start points
    run_min = np.minimum.accumulate(np.where(valid, gathered, np.inf), axis=1)
    cand = np.where(
        valid[:, min_len:],
        gathered[:, min_len:] - run_min[:, : horizon + 1 - min_len],
        -np.inf,
    )
    best = cand.max(axis=1)

    # priced-share gate over the (truncated) horizon
    hi = np.minimum(starts + horizon, t_len)
    span = (hi - starts).astype(float)
    priced = np.divide(
        fpre[hi] - fpre[starts], span, out=np.zeros(n_days), where=span > 0
    )
    return np.where(
        np.isfinite(best) & (priced >= MIN_PRICED_SHARE) & (span >= min_len),
        best,
        np.nan,
    )


# --------------------------------------------------------------------------- #
# window population                                                            #
# --------------------------------------------------------------------------- #
@dataclass
class WindowSet:
    """The guard-off baseline window population for one ISO, on a shared day clock."""

    frame: pd.DataFrame
    day0: pd.Timestamp
    n_days: int
    a_day: np.ndarray
    b_day: np.ndarray
    mw: np.ndarray
    was_layup: np.ndarray  # committed classification, for the machinery control


def load_windows(
    iso: str, years: list[int], plant_filter: set[int] | None
) -> WindowSet:
    """Reconstruct the guard-off baseline: the committed extract UNION its layup
    companion, clipped to the scored day range (and to a plant scope if given)."""
    kept_name, layup_name = _EXTRACTS[iso.upper()]

    def _rd(name: str, flag: bool) -> pd.DataFrame:
        d = pd.read_csv(RAW / name, parse_dates=["outage_start", "outage_end"])
        d = d[d["outage_start"].dt.year.isin(years)].copy()
        d["was_layup"] = flag
        return d

    d = pd.concat([_rd(kept_name, False), _rd(layup_name, True)], ignore_index=True)
    if plant_filter is not None:
        d = d[d["facility_id"].isin(plant_filter)].copy()
    day0 = pd.Timestamp(f"{min(years)}-01-01")
    last = pd.Timestamp(f"{max(years)}-12-31")
    n_days = int((last - day0).days) + 1
    a = np.clip((d["outage_start"] - day0).dt.days.to_numpy(dtype=int), 0, n_days - 1)
    b = np.clip((d["outage_end"] - day0).dt.days.to_numpy(dtype=int), 0, n_days - 1)
    return WindowSet(
        frame=d.reset_index(drop=True),
        day0=day0,
        n_days=n_days,
        a_day=a,
        b_day=np.maximum(a, b),
        mw=d["unit_capacity_mw"].to_numpy(dtype=float),
        was_layup=d["was_layup"].to_numpy(dtype=bool),
    )


def daily_series(ws: WindowSet, mask: np.ndarray) -> pd.Series:
    """Daily outage MW implied by a window subset — O(n) difference-array
    accumulation, so the placebo's repeated re-scoring is cheap."""
    diff = np.zeros(ws.n_days + 1, dtype=float)
    np.add.at(diff, ws.a_day[mask], ws.mw[mask])
    np.add.at(diff, ws.b_day[mask] + 1, -ws.mw[mask])
    idx = pd.date_range(ws.day0, periods=ws.n_days, freq="D")
    return pd.Series(np.cumsum(diff)[: ws.n_days], index=idx)


# --------------------------------------------------------------------------- #
# published instruments                                                        #
# --------------------------------------------------------------------------- #
@dataclass
class Published:
    outages: pd.Series
    label: str
    plant_filter: set[int] | None = None
    uncommitted: pd.Series | None = None


def published(iso: str, years: list[int]) -> Published | None:
    """The ISO's published anchor (charter §4). ``None`` for an ISO with none."""
    iso = iso.upper()
    if iso == "NEISO":
        d = pd.concat(
            [
                pd.read_csv(
                    RAW
                    / "neiso-operable-capacity"
                    / f"neiso_operable_capacity_{y}.csv",
                    parse_dates=["report_date"],
                )
                for y in years
            ]
        ).set_index("report_date")
        return Published(
            outages=d["gen_outages_reductions_mw"].astype(float),
            label="ISO-NE Morning Report Section 3 gen_outages_reductions_mw",
            uncommitted=d["uncommitted_available_gen_nonfast_mw"].astype(float),
        )
    if iso == "MISO":
        d = pd.concat(
            [
                pd.read_csv(
                    RAW / "miso-generation-outages" / f"miso_outages_estimated_{y}.csv",
                    parse_dates=["interval_date"],
                )
                for y in years
            ]
        ).set_index("interval_date")
        return Published(
            outages=(d["MISO_Forced"] + d["MISO_Planned"] + d["MISO_Unplanned"]).astype(
                float
            ),
            label="MISO native outage source (Forced+Planned+Unplanned)",
        )
    if iso == "PJM":
        d = pd.concat(
            [
                pd.read_csv(
                    RAW / "pjm-outages" / "by-year" / f"gen_outages_by_type_{y}.csv",
                    parse_dates=["forecast_date"],
                )
                for y in years
            ]
        )
        d = d[(d["region"] == "PJM RTO") & (d["lead_days"] == 0)]
        return Published(
            outages=d.groupby("forecast_date")["total_outages_mw"].mean().astype(float),
            label="PJM Data Miner 2 gen_outages_by_type, PJM RTO lead_days=0",
        )
    if iso == "ERCOT":
        d = pd.read_csv(
            RAW / "ercot-thermal-dam-availability.csv", parse_dates=["date"]
        )
        d = d[d["date"].dt.year.isin(years)]
        return Published(
            outages=(
                d.assign(out=d["rating_mw"] - d["live_mw"])
                .groupby("date")["out"]
                .sum()
                .astype(float)
            ),
            label="ERCOT 60-day DAM disclosure rating_mw - live_mw "
            "(offered-vs-available caveat: carries some layup itself)",
        )
    if iso == "CAISO":
        # REVISION-AWARE ONLY (neiso-66 §1): tail(1) discards 72 % of segments and
        # raw-sum double-counts overlapping revisions. Both sides are restricted to
        # the reviewed crosswalk's plants, which is what makes CAISO's level ratio
        # interpretable at all.
        seg = _segments(years)
        by_plant = build_revision(seg, years)
        return Published(
            outages=by_plant.sum(axis=1),
            label="CAISO CNOG, reviewed resource->plant crosswalk, revision-aware build",
            plant_filter=set(int(c) for c in by_plant.columns),
        )
    return None


def caiso_active_scope(
    pub: Published, ws_all: WindowSet, years: list[int]
) -> tuple[pd.Series, set[int]]:
    """Restrict CAISO to plants where the CAMPD baseline carries any signal.

    CNOG's non-operational bucket includes long-term mothball / seasonal-RMR
    states the model owns through fleet status, not the outage overlay, and for
    which the detector has no windows at all. Both sides are restricted
    identically (the neiso-65 active-plant scope).
    """
    seg = _segments(years)
    by_plant = build_revision(seg, years)
    active = sorted(
        {int(p) for p in ws_all.frame["facility_id"].unique()}
        & set(int(c) for c in by_plant.columns)
    )
    return by_plant[[p for p in by_plant.columns if int(p) in set(active)]].sum(
        axis=1
    ), set(active)


# --------------------------------------------------------------------------- #
# scoring                                                                      #
# --------------------------------------------------------------------------- #
def level_and_r(model: pd.Series, pub: pd.Series, year: int) -> tuple[float, float]:
    """(level ratio, monthly correlation) for one year on the overlapping days."""
    j = pd.concat([model.rename("m"), pub.rename("p")], axis=1).dropna()
    j = j[(j.index.year == year) & (j["p"] > 0)]
    if j.empty or j["p"].mean() <= 0:
        return float("nan"), float("nan")
    mm = j.groupby(j.index.month)[["m", "p"]].mean()
    return float(j["m"].mean() / j["p"].mean()), float(mm["m"].corr(mm["p"]))


def placebo_p95(
    ws: WindowSet,
    target_gwd: float,
    pub: pd.Series,
    years: list[int],
    draws: int,
    seed: int,
) -> dict[int, float]:
    """p95 monthly r when the SAME GW-days are dropped at random from baseline.

    The null the charter D1 standard requires: would removing this much capacity
    have improved the shape anyway? A cut inside the placebo band has subtracted
    MW, not discriminated between populations.
    """
    gwd = ws.frame["unit_capacity_mw"].to_numpy(dtype=float) * ws.frame[
        "duration_days"
    ].to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    acc: dict[int, list[float]] = {y: [] for y in years}
    n = len(ws.frame)
    for _ in range(draws):
        drop = np.zeros(n, dtype=bool)
        tot = 0.0
        for i in rng.permutation(n):
            if tot >= target_gwd:
                break
            drop[i] = True
            tot += gwd[i]
        s = daily_series(ws, ~drop)
        for y in years:
            _, r = level_and_r(s, pub, y)
            if np.isfinite(r):
                acc[y].append(r)
    return {y: float(np.percentile(v, 95)) for y, v in acc.items() if v}


# --------------------------------------------------------------------------- #
# the two cuts                                                                 #
# --------------------------------------------------------------------------- #
def window_shares(
    ws: WindowSet,
    u: UnitArrays,
    rcc: np.ndarray,
    day_oom: np.ndarray | None,
    year: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Both cuts' out-of-merit shares for every window of ``year``.

    Returns ``(hourly_share, daily_share)``; ``NaN`` where the unit is
    unidentified or the span carries no evaluable hour/day, which is the guard's
    own fail-safe (the window is then KEPT by both cuts — a cut can only ever
    remove windows it has positive measured evidence against, charter D4).
    """
    n = len(ws.frame)
    h_share = np.full(n, np.nan)
    d_share = np.full(n, np.nan)
    y0 = pd.Timestamp(f"{year}-01-01")
    year_day0 = int((y0 - ws.day0).days)
    n_year_days = u.n_hours // 24
    fids = ws.frame["facility_id"].to_numpy(dtype=int)
    uids = ws.frame["unit_id"].astype(str).to_numpy()
    in_year = ws.frame["outage_start"].dt.year.to_numpy() == year
    for i in range(n):
        if not in_year[i]:
            continue
        j = u.index.get((int(fids[i]), str(uids[i])))
        if j is None:
            continue
        a_d = ws.a_day[i] - year_day0
        b_d = ws.b_day[i] - year_day0
        a_d = max(a_d, 0)
        b_d = min(b_d, n_year_days - 1)
        if b_d < a_d:
            continue
        lo, hi = a_d * 24, min((b_d + 1) * 24, u.n_hours)
        unit, ref = u.srmc[j][lo:hi], rcc[lo:hi]
        ok = np.isfinite(unit) & np.isfinite(ref)
        if int(ok.sum()) > 0:
            h_share[i] = float((unit[ok] > ref[ok]).sum()) / int(ok.sum())
        if day_oom is not None:
            dd = day_oom[j][a_d : b_d + 1]
            fin = np.isfinite(dd)
            if int(fin.sum()) > 0:
                d_share[i] = float((dd[fin] < 0.0).sum()) / int(fin.sum())
    return h_share, d_share


def veto_mask(share: np.ndarray, frac: float) -> np.ndarray:
    """Fail-safe veto: an unevaluable window (NaN) is KEPT."""
    return np.isfinite(share) & (share >= frac)


# --------------------------------------------------------------------------- #
# NEISO port control                                                           #
# --------------------------------------------------------------------------- #
def neiso_band_control(
    u: UnitArrays, day_oom: np.ndarray, unc: pd.Series, year: int
) -> tuple[float, int]:
    """Reproduce neiso-67 §2: idle capacity in the ``R < 0`` band vs published
    UNCOMMITTED, monthly r. This is the port check — the ported machinery must
    land on neiso-67's published numbers before any cross-ISO reading is taken."""
    n_days = u.n_hours // 24
    ran = u.running[:, : n_days * 24].reshape(len(u.keys), n_days, 24).any(axis=2)
    idle = ~ran
    band = idle & np.isfinite(day_oom) & (day_oom < 0.0)
    mw = (band * u.capacity[:, None]).sum(axis=0)
    idx = pd.date_range(f"{year}-01-01", periods=n_days, freq="D")
    s = pd.Series(mw, index=idx)
    j = pd.concat([s.rename("m"), unc.rename("p")], axis=1).dropna()
    if j.empty:
        return float("nan"), 0
    mm = j.groupby(j.index.month)[["m", "p"]].mean()
    return float(mm["m"].corr(mm["p"])), int(round(float(s.mean())))


# --------------------------------------------------------------------------- #
# driver                                                                       #
# --------------------------------------------------------------------------- #
def run_iso(
    iso: str,
    years: list[int],
    pctls: list[float],
    horizons: list[int],
    frac: float,
    draws: int,
    seed: int,
) -> list[dict]:
    """Score both cuts across the knob sweep for one ISO. Returns result rows."""
    iso = iso.upper()
    pub = published(iso, years)
    print(
        f"\n{'=' * 78}\n===== {iso} — day-grain vs window-grain out-of-merit cut ====="
    )
    if pub is None:
        print("  NO PUBLISHED ANCHOR — excluded by the charter §4 protocol.")
        return []
    print(f"  anchor: {pub.label}")

    ws_all = load_windows(iso, years, None)
    if iso == "CAISO":
        pub_series, scope = caiso_active_scope(pub, ws_all, years)
        pub = Published(outages=pub_series, label=pub.label, plant_filter=scope)
        ws = load_windows(iso, years, scope)
        print(
            f"  crosswalked active-plant scope: {len(scope)} plants; "
            f"windows in scope {len(ws.frame)} of {len(ws_all.frame)}"
        )
    else:
        ws = ws_all
    print(
        f"  baseline windows {len(ws.frame):,} "
        f"(committed kept {int((~ws.was_layup).sum()):,} + layup {int(ws.was_layup.sum()):,})"
        f"   published mean {pub.outages.mean():,.0f} MW"
    )

    rows: list[dict] = []
    states = campd.states_for_iso(iso)
    for year in years:
        u = load_units(iso, year, states)
        if u is None:
            print(f"\n  {year}: unidentifiable (no priceable CEMS unit) — skipped")
            continue
        n_days = u.n_hours // 24
        print(
            f"\n  {year}: {len(u.keys)} identified units, "
            f"{u.capacity.sum():,.0f} MW; day clock {n_days} d"
        )
        base_s = daily_series(ws, np.ones(len(ws.frame), dtype=bool))
        b_lv, b_r = level_and_r(base_s, pub.outages, year)
        print(
            f"    NO-SPLIT reference (guard-off baseline): level {b_lv:5.2f}x  "
            f"monthly r {b_r:+.2f}"
        )
        for pctl in pctls:
            rcc = revealed_clearing_cost(u, pctl)
            h_share, _ = window_shares(ws, u, rcc, None, year)
            v_win = veto_mask(h_share, frac)
            # machinery control: does the re-applied window cut reproduce the
            # committed kept/layup split on this ISO-year?
            in_year = ws.frame["outage_start"].dt.year.to_numpy() == year
            agree = int((v_win[in_year] == ws.was_layup[in_year]).sum())
            gwd_all = ws.frame["unit_capacity_mw"].to_numpy(dtype=float) * ws.frame[
                "duration_days"
            ].to_numpy(dtype=float)
            for horizon in horizons:
                day_oom = np.full((len(u.keys), n_days), np.nan)
                for j in range(len(u.keys)):
                    h = max(int(horizon), int(u.min_run[j]))
                    day_oom[j] = daily_best_block(
                        rcc - u.srmc[j], int(u.min_run[j]), h, n_days
                    )
                _, d_share = window_shares(ws, u, rcc, day_oom, year)
                v_day = veto_mask(d_share, frac)

                cells = {}
                for tag, v in (("window", v_win), ("day", v_day)):
                    keep = ~v
                    k_lv, k_r = level_and_r(daily_series(ws, keep), pub.outages, year)
                    x_lv, x_r = level_and_r(daily_series(ws, v), pub.outages, year)
                    gwd = float(gwd_all[v & in_year].sum())
                    p95 = placebo_p95(ws, gwd, pub.outages, years, draws, seed).get(
                        year, float("nan")
                    )
                    cell = {
                        "vetoed_windows": int((v & in_year).sum()),
                        "vetoed_gwdays": gwd / 1000.0,
                        "kept_level": k_lv,
                        "kept_r": k_r,
                        "vetoed_level": x_lv,
                        "vetoed_r": x_r,
                        "placebo_p95": p95,
                        "beats_placebo": bool(np.isfinite(k_r) and k_r > p95),
                        "beats_nosplit": bool(np.isfinite(k_r) and k_r > b_r),
                    }
                    if pub.uncommitted is not None:
                        _, ku = level_and_r(
                            daily_series(ws, keep), pub.uncommitted, year
                        )
                        _, xu = level_and_r(daily_series(ws, v), pub.uncommitted, year)
                        cell["kept_r_unc"] = ku
                        cell["vetoed_r_unc"] = xu
                    cells[tag] = cell

                # Why the two cuts score alike: how far apart are their veto
                # SETS at all? A cut that selects nearly the same windows cannot
                # score differently, whatever its construction.
                iy = in_year
                both = int((v_win & v_day & iy).sum())
                either = int(((v_win | v_day) & iy).sum())
                overlap = {
                    "agree_windows": int((v_win[iy] == v_day[iy]).sum()),
                    "jaccard": (both / either) if either else float("nan"),
                    "win_only": int((v_win & ~v_day & iy).sum()),
                    "day_only": int((v_day & ~v_win & iy).sum()),
                    "h_share_p25": float(np.nanpercentile(h_share[iy], 25)),
                    "h_share_p75": float(np.nanpercentile(h_share[iy], 75)),
                    "d_share_p25": float(np.nanpercentile(d_share[iy], 25)),
                    "d_share_p75": float(np.nanpercentile(d_share[iy], 75)),
                }

                band_r, band_mw = (float("nan"), 0)
                if pub.uncommitted is not None:
                    band_r, band_mw = neiso_band_control(
                        u, day_oom, pub.uncommitted, year
                    )
                rows.append(
                    {
                        "iso": iso,
                        "year": year,
                        "rcc_pctl": pctl,
                        "horizon": horizon,
                        "nosplit_level": b_lv,
                        "nosplit_r": b_r,
                        "window_agrees_committed": agree,
                        "windows_in_year": int(in_year.sum()),
                        "band_r_uncommitted": band_r,
                        "band_mw": band_mw,
                        **overlap,
                        **{
                            f"{t}_{k}": v
                            for t, c in cells.items()
                            for k, v in c.items()
                        },
                    }
                )
                w, d = cells["window"], cells["day"]
                print(
                    f"             {'':9s}| veto-set overlap: agree "
                    f"{overlap['agree_windows']:,}/{int(iy.sum()):,} windows, "
                    f"Jaccard {overlap['jaccard']:.2f} "
                    f"(window-only {overlap['win_only']}, day-only {overlap['day_only']})"
                    f" | share IQR hourly [{overlap['h_share_p25']:.2f}, {overlap['h_share_p75']:.2f}]"
                    f" daily [{overlap['d_share_p25']:.2f}, {overlap['d_share_p75']:.2f}]"
                )
                print(
                    f"    p{pctl:.0%} h{horizon:<3d}"
                    f" | WINDOW veto {w['vetoed_windows']:4d}w"
                    f" {w['vetoed_gwdays']:6.1f}GWd kept r {w['kept_r']:+.2f}"
                    f" lv {w['kept_level']:4.2f}x vet r {w['vetoed_r']:+.2f}"
                    f" plc {w['placebo_p95']:+.2f}"
                    f" | DAY veto {d['vetoed_windows']:4d}w"
                    f" {d['vetoed_gwdays']:6.1f}GWd kept r {d['kept_r']:+.2f}"
                    f" lv {d['kept_level']:4.2f}x vet r {d['vetoed_r']:+.2f}"
                    f" plc {d['placebo_p95']:+.2f}"
                    f" | DAY-WIN {d['kept_r'] - w['kept_r']:+.2f}"
                )
                if pub.uncommitted is not None:
                    print(
                        f"             {'':9s}| vs published UNCOMMITTED:"
                        f" WINDOW kept {w['kept_r_unc']:+.2f} vetoed {w['vetoed_r_unc']:+.2f}"
                        f" | DAY kept {d['kept_r_unc']:+.2f} vetoed {d['vetoed_r_unc']:+.2f}"
                        f" | neiso-67 idle R<0 band {band_mw:,} MW r {band_r:+.2f}"
                    )
            print(
                f"    [control] re-applied WINDOW cut reproduces the committed "
                f"kept/layup split on {agree:,}/{int(in_year.sum()):,} windows "
                f"at p{pctl:.0%}"
            )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="+", default=list(DEFAULT_ISOS))
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--rcc-pctl", nargs="+", type=float, default=[MERIT_RCC_PCTL])
    ap.add_argument(
        "--horizon",
        nargs="+",
        type=int,
        default=[DA_COMMITMENT_HORIZON_HOURS],
        help="commitment-horizon FLOOR in hours; the horizon actually used is "
        "max(this, the unit's published min_run_hours)",
    )
    ap.add_argument("--oom-frac", type=float, default=MERIT_OOM_FRAC)
    ap.add_argument("--placebo-draws", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20260726)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    years = sorted(args.years)
    rows: list[dict] = []
    for iso in [s.upper() for s in args.iso]:
        if iso not in _EXTRACTS:
            print(f"\n===== {iso} — no committed extract pair; skipped =====")
            continue
        rows.extend(
            run_iso(
                iso,
                years,
                sorted(args.rcc_pctl),
                sorted(args.horizon),
                args.oom_frac,
                args.placebo_draws,
                args.seed,
            )
        )
    if not rows:
        return

    df = pd.DataFrame(rows)
    print(
        f"\n{'=' * 78}\n===== CROSS-ISO VERDICT: does the DAY-grain cut BEAT the "
        "WINDOW-grain cut? ====="
    )
    print("  (monthly r of the KEPT extract vs the ISO's published outage series;")
    print("   a replacement must win in nearly every cell across ISOs)")
    df["delta"] = df["day_kept_r"] - df["window_kept_r"]
    for iso, g in df.groupby("iso", sort=False):
        win = int((g["delta"] > 0).sum())
        tie = int((g["delta"].abs() < 1e-9).sum())
        print(
            f"    {iso:6s} day-grain better in {win}/{len(g)} cells"
            f" (ties {tie}); median delta {g['delta'].median():+.3f};"
            f" day beats placebo {int(g['day_beats_placebo'].sum())}/{len(g)},"
            f" window {int(g['window_beats_placebo'].sum())}/{len(g)};"
            f" day beats no-split {int(g['day_beats_nosplit'].sum())}/{len(g)},"
            f" window {int(g['window_beats_nosplit'].sum())}/{len(g)}"
        )
    tot = int((df["delta"] > 0).sum())
    print(
        f"    ALL    day-grain better in {tot}/{len(df)} cells; "
        f"median delta {df['delta'].median():+.3f}"
    )
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(rows, indent=1, default=float))
        print(f"\n  rows -> {args.json}")


if __name__ == "__main__":
    main()
