"""caiso-168 PHASE 0 — is the CAISO belly dual held UP by the storage charging bid? NO LP, NO SOLVE.

The question caiso-167 §7 handed forward as an explicit **pointer, not a
verdict**: with the whole corridor/export-path family closed, the surplus-regime
belly residual is in-state by elimination, and caiso-121's physical stack put
**storage charging +1,967/+2,049/+2,244 MW over measured** at the top of it.
Whether the CA belly dual is *set* by that charging is untested. This probe
establishes or refutes it on committed artifacts only.

The LP fact the whole question turns on. With the balance row written
``Σ P + W + S + Dis − Chg + flow + slack − dump = D`` (dual ``λ``) and the SOC
row ``SOC_t − SOC_{t−1} − η_c·Chg_t + Dis_t/η_d = 0`` (dual ``ν``), the charge
column's reduced cost is ``ε + λ_t + η_c·ν_t``. So:

* **charging strictly interior** ⇒ rc = 0 ⇒ ``λ_t = −ε − η_c·ν_t``. The battery
  is the marginal buyer and **its bid sets the zone's dual**;
* **charging at its upper bound** ⇒ rc ≤ 0 ⇒ ``λ_t`` is *below* the battery's
  willingness to pay: the battery is a **pinned demand** and cannot set λ;
* **charging at zero** ⇒ rc ≥ 0 ⇒ λ is *above* it; also not the setter.

So the hypothesis is decidable by a bound census, and the census has a third
state here because the keeper **arms** ``caiso_storage_shape_anchor``: a battery
row's charge bound is ``env_p95_chg[year, hod] × power_cap[s, t]``
(``model/storage.py::caiso_storage_shape_caps``), not nameplate. That measured
envelope is an already-adjudicated object (caiso-99, matrix cell armed), so
rule 19 ``[R-ONE-MECH]`` requires separating hours it owns (at-cap) from hours
it does not (interior) before anything new is proposed.

Reconstructing that bound from committed artifacts, exactly. ``power_cap`` is
**piecewise-constant by month** (``storage.storage_cap_profiles`` maps the
EIA-860 monthly COD profile through ``_hour_to_month_index``), and the envelope
CSV is committed, so inverting the keeper's own hourly dispatch against the
envelope recovers the monthly fleet cap:
``cap[m] = max_{t∈m} max(chg_t / f_chg[hod], dis_t / f_dis[hod])``. Stage A
prints the recovered staircase and its **year-boundary self-consistency check**
(December of one solve against January of the next, independent solves).

Sources, all committed:

* keeper bundle ``results/calibration/caiso164_zonal_loss_surface/hourly/``
  — ``storage_<y>.parquet`` (the sidecar this lane has never used),
  ``system_<y>.parquet`` (zonal duals + demand);
* ``data/raw/reference/caiso-storage-shape-envelope.csv`` — the armed anchor's
  own committed envelope (rule 23; read, never re-derived);
* ``data/raw/lmp-data/CAISO/CAISO_dam_hourly_<y>.csv`` — the measured CA hub,
  the same day-ahead series caiso-164/165/167 decomposed.

Stages:

``A`` bound census — the charge state (zero / interior / at-anchor-cap) by year,
      window and month, li_ion and pumped storage kept **strictly separate**
      (the C3a-2025 PS object is walled; landing on it is a stop-and-report).
``B`` λ conditioned on state — model zonal duals and the model−measured defect
      split by charge state on the belly-surplus mask, by month × zone.
``C`` the arbitrage identity — in interior belly-charge hours, test whether λ is
      literally the battery's water value, ``λ_chg = RTE·(λ_dis − adder)``,
      against the same day's own evening discharge dual.
``C2`` flatness — the common-``ν`` signature: is the dual CONSTANT across a
      day's interior-charge hours, as it must be if the battery sets it?
``D`` reach — how much of the CA belly over-price sits in each state, i.e. the
      most any charge-side mechanism could move.
``E`` matched control — the same contrast within month × measured-hub decile, so
      the state/tightness confound is bounded rather than assumed away.
``F`` limb attribution — battery vs the WALLED pumped-storage object, jointly.
``G`` volume — model vs measured (EIA-930 ``NG: OTH``) battery charge, against
      the armed anchor's own p95 cap.
``H`` the caiso-121 storage row re-based onto a like-for-like battery basis.

Rule 13 ``[R-MEASURED]``: every number is a measurement of committed inputs and
committed model output. Nothing is fitted, nothing is tuned, no value computed
here is fed back into any model input, and no residual motivates a re-derive
(rule 23 ``[R-FROZEN-DERIVE]``).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/caiso164_zonal_loss_surface/hourly"
ENVELOPE = REPO / "data/raw/reference/caiso-storage-shape-envelope.csv"
DAM = REPO / "data/raw/lmp-data/CAISO"
EIA930 = REPO / "data/raw/eia-930-hourly/CISO hourly.parquet"
OUT = REPO / "results/calibration/_caiso168_storage_bid_phase0.json"

YEARS = (2023, 2024, 2025)  # rule 22 [R-HOLDOUT]: training years ONLY, fail closed.
HOURS = 8760

# Regime cut carried VERBATIM from caiso-165 §2 / caiso-120 / caiso-167 — chosen
# by prior lanes, not here: belly = Pacific [09, 16), surplus = measured CA
# day-ahead hub <= $20/MWh.
BELLY = (9, 16)
EVENING = (17, 22)
SURPLUS_MAX = 20.0
CA_HUB = "TH_SP15_GEN-APND"

# Storage physics as the keeper's own run_config records them: RTE 0.85
# (ScenarioConfig.storage_rte_4hr, split evenly into one-way efficiencies,
# storage.py::_storage_rte ** 0.5) and a 5 $/MWh discharged throughput adder
# (battery_dispatch_adder). ε is CLAUDE.md rule 9's 0.001 tiebreaker.
RTE = 0.85
DIS_ADDER = 5.0
EPS = 0.001

# A dispatch within this fraction of its own upper bound is AT the bound; a
# dispatch below this many MW is zero. Both are numerical-tolerance calls on a
# HiGHS solution, not tuned thresholds.
AT_BOUND_FRAC = 0.995
ZERO_MW = 1.0


# Hours per month of the model's FIXED NON-LEAP 8760 calendar. The solve frame
# drops Feb-29 (repo convention, _caiso102/_caiso105/_caiso140), and
# storage.storage_cap_profiles indexes the monthly COD ramp through
# data.fleet._hour_to_month_index on exactly this calendar -- so a
# pd.date_range clock would mis-label every 2024 hour after Feb-28 by a day and
# silently shift the recovered cap staircase by a month.
DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH = np.repeat(np.arange(1, 13), np.array(DAYS_IN_MONTH) * 24)[:HOURS]
_HOD = np.arange(HOURS) % 24


def _clock() -> tuple[np.ndarray, np.ndarray]:
    """``(hod, month)`` on the model's non-leap 8760 frame."""
    return _HOD, _MONTH


def _model_hour(ts: pd.Series, year: int) -> np.ndarray:
    """Map local timestamps onto the model's non-leap 8760 hour index.

    Feb-29 rows are dropped by the caller's mask; every later day of a leap year
    shifts back one day so the measured series stays hour-aligned to the solve.
    """
    dt = pd.DatetimeIndex(ts)
    doy = dt.dayofyear.to_numpy()
    if year % 4 == 0:
        doy = np.where(dt.month.to_numpy() > 2, doy - 1, doy)
    return (doy - 1) * 24 + dt.hour.to_numpy()


def _storage(year: int) -> dict[str, dict[str, np.ndarray]]:
    """P1 fleet charge/discharge MW per tech from the keeper's own sidecar."""
    s = pd.read_parquet(BUNDLE / f"storage_{year}.parquet")
    s = s[s["pass"] == "P1"]
    chg = s.pivot_table(index="hour", columns="tech", values="charge_mw")
    dis = s.pivot_table(index="hour", columns="tech", values="discharge_mw")
    return {
        t: {"chg": chg[t].to_numpy(), "dis": dis[t].to_numpy()} for t in chg.columns
    }


def _system(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = pd.read_parquet(BUNDLE / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return (
        d.pivot_table(index="hour", columns="zone", values="price"),
        d.pivot_table(index="hour", columns="zone", values="demand"),
    )


def _ca_lambda(price: pd.DataFrame, demand: pd.DataFrame) -> np.ndarray:
    """CA demand-weighted model dual — the C3a construction, WECC nodes excluded."""
    ca = [z for z in price.columns if not str(z).startswith("WECC")]
    return ((price[ca] * demand[ca]).sum(axis=1) / demand[ca].sum(axis=1)).to_numpy()


def _hub(year: int) -> np.ndarray:
    """Measured CA day-ahead hub on the model's 0-based local-calendar index."""
    f = pd.read_csv(
        DAM / f"CAISO_dam_hourly_{year}.csv", parse_dates=["interval_start_gmt"]
    )
    local = f["interval_start_gmt"].dt.tz_convert("America/Los_Angeles")
    f = f[f["node"] == CA_HUB].assign(local=local[f["node"] == CA_HUB])
    keep = ~((f["local"].dt.month == 2) & (f["local"].dt.day == 29))
    f = f[keep]
    h = _model_hour(f["local"], year)
    out = np.full(HOURS, np.nan)
    ok = (h >= 0) & (h < HOURS)
    out[h[ok]] = f["LMP"].to_numpy(dtype=float)[ok]
    return out


def _envelope(year: int) -> tuple[np.ndarray, np.ndarray]:
    """The armed anchor's committed p95 hod fractions (read, never re-derived)."""
    env = pd.read_csv(ENVELOPE)
    years = sorted(env["year"].unique())
    use = max((y for y in years if y <= year), default=years[0])
    ey = env[env["year"] == use].sort_values("hod")
    return (
        ey["chg_frac_p95"].to_numpy(dtype=float),
        ey["dis_frac_p95"].to_numpy(dtype=float),
    )


def _monthly_power_cap(
    chg: np.ndarray,
    dis: np.ndarray,
    f_chg: np.ndarray,
    f_dis: np.ndarray,
    month: np.ndarray,
) -> np.ndarray:
    """Recover the battery fleet's monthly power cap by inverting the envelope.

    ``storage_cap_profiles`` makes ``power_cap`` piecewise-constant by month, and
    the anchor sets the battery charge/discharge bound to ``frac[hod] × cap``. So
    over a month, ``max(chg/f_chg, dis/f_dis)`` equals the cap in any hour the
    bound binds and is below it otherwise — the month max is therefore the cap
    whenever the fleet reaches its bound at least once in the month, and a strict
    lower bound if it never does (which would UNDER-state the cap and so
    OVER-state at-bound hours; stage A's staircase and year-boundary check test
    that it does not happen).
    """
    hod = np.arange(len(chg)) % 24
    with np.errstate(divide="ignore", invalid="ignore"):
        rc = np.where(
            f_chg[hod] > 1e-9,
            chg / np.where(f_chg[hod] > 1e-9, f_chg[hod], 1.0),
            np.nan,
        )
        rd = np.where(
            f_dis[hod] > 1e-9,
            dis / np.where(f_dis[hod] > 1e-9, f_dis[hod], 1.0),
            np.nan,
        )
    r = np.fmax(rc, rd)
    cap = np.zeros(len(chg))
    for m in range(1, 13):
        k = month == m
        cap[k] = np.nanmax(r[k])
    return cap


def _states(chg: np.ndarray, bound: np.ndarray) -> dict[str, np.ndarray]:
    """The three charge states the reduced-cost argument distinguishes."""
    at = (bound > ZERO_MW) & (chg >= AT_BOUND_FRAC * bound)
    zero = chg <= ZERO_MW
    return {"zero": zero, "interior": ~at & ~zero, "at_cap": at & ~zero}


# ---------------------------------------------------------------- stage A
def stage_a() -> tuple[list[dict], list[dict], dict]:
    """Bound census: which state is the charge column in, and who owns it."""
    rows: list[dict] = []
    month_rows: list[dict] = []
    caps: dict[int, list[float]] = {}
    for year in YEARS:
        hod, month = _clock()
        st = _storage(year)
        f_chg, f_dis = _envelope(year)
        hub = _hub(year)
        belly = (hod >= BELLY[0]) & (hod < BELLY[1])
        surplus = belly & np.isfinite(hub) & (hub <= SURPLUS_MAX)

        cap = _monthly_power_cap(
            st["li_ion"]["chg"], st["li_ion"]["dis"], f_chg, f_dis, month
        )
        caps[year] = [float(cap[month == m][0]) for m in range(1, 13)]
        bound = cap * f_chg[hod]
        chg = st["li_ion"]["chg"]
        states = _states(chg, bound)

        for window, mask in (
            ("all", np.ones(HOURS, bool)),
            ("belly", belly),
            ("belly_surplus", surplus),
        ):
            row = {
                "year": year,
                "tech": "li_ion",
                "window": window,
                "n": int(mask.sum()),
                "chg_mean_mw": float(chg[mask].mean()),
                "bound_mean_mw": float(bound[mask].mean()),
            }
            for name, s in states.items():
                row[f"pct_{name}"] = float(100 * s[mask].mean())
                row[f"twh_{name}"] = float(chg[mask & s].sum() / 1e6)
            rows.append(row)

        for m in range(1, 13):
            mm = surplus & (month == m)
            if mm.sum() < 24:
                continue
            month_rows.append(
                {
                    "year": year,
                    "month": m,
                    "n": int(mm.sum()),
                    "chg_mean_mw": float(chg[mm].mean()),
                    "bound_mean_mw": float(bound[mm].mean()),
                    **{
                        f"pct_{k}": float(100 * v[mm].mean()) for k, v in states.items()
                    },
                }
            )

        # Pumped storage, kept strictly separate — it is EXEMPT from the anchor
        # (its bound is nameplate) and it is the walled C3a-2025 object.
        ps = st["pumped_storage"]
        ps_cap = float(np.maximum(ps["chg"], ps["dis"]).max())
        ps_at = ps["chg"] >= AT_BOUND_FRAC * ps_cap
        for window, mask in (
            ("all", np.ones(HOURS, bool)),
            ("belly", belly),
            ("belly_surplus", surplus),
        ):
            rows.append(
                {
                    "year": year,
                    "tech": "pumped_storage",
                    "window": window,
                    "n": int(mask.sum()),
                    "chg_mean_mw": float(ps["chg"][mask].mean()),
                    "bound_mean_mw": ps_cap,
                    "pct_zero": float(100 * (ps["chg"][mask] <= ZERO_MW).mean()),
                    "pct_at_cap": float(100 * ps_at[mask].mean()),
                    "pct_interior": float(
                        100 * ((ps["chg"][mask] > ZERO_MW) & ~ps_at[mask]).mean()
                    ),
                    "twh_zero": 0.0,
                    "twh_interior": float(
                        ps["chg"][mask & (ps["chg"] > ZERO_MW) & ~ps_at].sum() / 1e6
                    ),
                    "twh_at_cap": float(ps["chg"][mask & ps_at].sum() / 1e6),
                }
            )

    boundary = {
        f"{a}Dec_vs_{b}Jan": [caps[a][11], caps[b][0]]
        for a, b in ((2023, 2024), (2024, 2025))
    }
    return rows, month_rows, {"monthly_power_cap_mw": caps, "year_boundary": boundary}


# ---------------------------------------------------------------- stage B
def stage_b() -> list[dict]:
    """λ and the model−measured defect, conditioned on the charge state."""
    rows: list[dict] = []
    for year in YEARS:
        hod, month = _clock()
        price, demand = _system(year)
        lam = _ca_lambda(price, demand)
        hub = _hub(year)
        st = _storage(year)
        f_chg, f_dis = _envelope(year)
        cap = _monthly_power_cap(
            st["li_ion"]["chg"], st["li_ion"]["dis"], f_chg, f_dis, month
        )
        bound = cap * f_chg[hod]
        states = _states(st["li_ion"]["chg"], bound)
        belly = (hod >= BELLY[0]) & (hod < BELLY[1])
        surplus = belly & np.isfinite(hub) & (hub <= SURPLUS_MAX)

        zones = [z for z in price.columns if not str(z).startswith("WECC")]
        for name, s in list(states.items()) + [("ALL", np.ones(HOURS, bool))]:
            k = surplus & s
            if k.sum() == 0:
                continue
            row = {
                "year": year,
                "state": name,
                "n": int(k.sum()),
                "share_of_surplus_pct": float(100 * k.sum() / surplus.sum()),
                "ca_lambda_model": float(lam[k].mean()),
                "ca_hub_measured": float(hub[k].mean()),
                "defect": float((lam[k] - hub[k]).mean()),
                "defect_twh_weighted": float((lam[k] - hub[k]).sum()),
            }
            for z in zones:
                row[f"lam_{z}"] = float(price[z].to_numpy()[k].mean())
            rows.append(row)
    return rows


# ---------------------------------------------------------------- stage C
def stage_c() -> list[dict]:
    """The arbitrage identity: is the interior belly dual the battery water value?

    With SOC interior across an episode the SOC-row dual ``ν`` is common, so an
    interior charge hour and an interior discharge hour of the same episode
    satisfy ``λ_dis = adder + ε + (λ_chg + ε)/RTE``, i.e.
    ``λ_chg = RTE·(λ_dis − adder − ε) − ε``. Tested per DAY: the day's mean
    interior-charge belly dual against the prediction from the same day's mean
    interior-discharge evening dual.
    """
    rows: list[dict] = []
    for year in YEARS:
        hod, month = _clock()
        day = np.arange(HOURS) // 24
        price, demand = _system(year)
        lam = _ca_lambda(price, demand)
        st = _storage(year)
        f_chg, f_dis = _envelope(year)
        cap = _monthly_power_cap(
            st["li_ion"]["chg"], st["li_ion"]["dis"], f_chg, f_dis, month
        )
        chg, dis = st["li_ion"]["chg"], st["li_ion"]["dis"]
        chg_bound, dis_bound = cap * f_chg[hod], cap * f_dis[hod]
        chg_int = (chg > ZERO_MW) & (chg < AT_BOUND_FRAC * chg_bound)
        dis_int = (dis > ZERO_MW) & (dis < AT_BOUND_FRAC * dis_bound)
        belly = (hod >= BELLY[0]) & (hod < BELLY[1])
        eve = (hod >= EVENING[0]) & (hod < EVENING[1])
        hub = _hub(year)
        surplus = belly & np.isfinite(hub) & (hub <= SURPLUS_MAX)

        obs, pred, keep = [], [], []
        for d in range(365):
            kc = (day == d) & belly & chg_int & surplus
            kd = (day == d) & eve & dis_int
            if kc.sum() == 0 or kd.sum() == 0:
                continue
            obs.append(lam[kc].mean())
            pred.append(RTE * (lam[kd].mean() - DIS_ADDER - EPS) - EPS)
            keep.append(d)
        if not obs:
            continue
        o, p = np.asarray(obs), np.asarray(pred)
        rows.append(
            {
                "year": year,
                "days": len(o),
                "obs_mean": float(o.mean()),
                "pred_mean": float(p.mean()),
                "mean_abs_err": float(np.abs(o - p).mean()),
                "r": float(np.corrcoef(o, p)[0, 1]),
                "within_1_pct": float(100 * (np.abs(o - p) <= 1.0).mean()),
                "within_5_pct": float(100 * (np.abs(o - p) <= 5.0).mean()),
            }
        )
    return rows


# ---------------------------------------------------------------- stage C2
def stage_c2() -> list[dict]:
    """Flatness: is the belly dual CONSTANT across a day's interior-charge hours?

    A second, independent signature of the same LP fact, and one that needs no
    cross-window episode assumption. Where SOC is interior the SOC-row dual is
    common across the episode, so every interior-charge hour of that episode
    carries the SAME ``λ = −ε − η_c·ν``. A dual set by the thermal/import stack
    instead tracks net load and varies hour to hour. So compare the within-day
    spread of the model dual across interior-charge belly hours against (a) the
    same statistic on at-cap belly hours — where the battery is pinned and
    cannot set λ — and (b) the measured hub's own within-day spread over the
    interior hours, which says how much the real market moved those same hours.
    """
    rows: list[dict] = []
    for year in YEARS:
        hod, month = _clock()
        day = np.arange(HOURS) // 24
        price, demand = _system(year)
        lam = _ca_lambda(price, demand)
        hub = _hub(year)
        st = _storage(year)
        f_chg, f_dis = _envelope(year)
        cap = _monthly_power_cap(
            st["li_ion"]["chg"], st["li_ion"]["dis"], f_chg, f_dis, month
        )
        bound = cap * f_chg[hod]
        states = _states(st["li_ion"]["chg"], bound)
        belly = (hod >= BELLY[0]) & (hod < BELLY[1])
        surplus = belly & np.isfinite(hub) & (hub <= SURPLUS_MAX)

        out: dict[str, list[float]] = {"interior": [], "at_cap": [], "hub_interior": []}
        for d in range(365):
            for name in ("interior", "at_cap"):
                k = (day == d) & surplus & states[name]
                if k.sum() < 3:
                    continue
                out[name].append(float(lam[k].max() - lam[k].min()))
                if name == "interior":
                    out["hub_interior"].append(float(hub[k].max() - hub[k].min()))
        row = {"year": year}
        for name, vals in out.items():
            row[f"n_{name}"] = len(vals)
            row[f"range_{name}"] = float(np.mean(vals)) if vals else float("nan")
            row[f"flat_pct_{name}"] = (
                float(100 * np.mean(np.asarray(vals) <= 0.05)) if vals else float("nan")
            )
        rows.append(row)
    return rows


# ---------------------------------------------------------------- stage E
def stage_e() -> list[dict]:
    """Matched control: interior vs at-cap defect WITHIN month × measured-hub decile.

    The raw state contrast in stage B is confounded — at-cap hours are, by
    construction, hours the battery wanted MORE energy in, so they are deeper in
    surplus. This pairs the two states inside the same month and the same decile
    of the measured hub, uses only cells where BOTH states have >= 3 hours, and
    reports the hour-weighted paired difference. That difference is the reach
    bound: the most a mechanism that pins the charge column could remove, given
    that the at-cap hours show what the dual does when the battery is pinned.
    """
    rows: list[dict] = []
    for year in YEARS:
        hod, month = _clock()
        price, demand = _system(year)
        lam = _ca_lambda(price, demand)
        hub = _hub(year)
        st = _storage(year)
        f_chg, f_dis = _envelope(year)
        cap = _monthly_power_cap(
            st["li_ion"]["chg"], st["li_ion"]["dis"], f_chg, f_dis, month
        )
        bound = cap * f_chg[hod]
        states = _states(st["li_ion"]["chg"], bound)
        belly = (hod >= BELLY[0]) & (hod < BELLY[1])
        surplus = belly & np.isfinite(hub) & (hub <= SURPLUS_MAX)

        defect = lam - hub
        idx = np.where(surplus)[0]
        dec = np.full(HOURS, -1)
        dec[idx] = pd.qcut(hub[idx], 10, labels=False, duplicates="drop")

        pairs, wts = [], []
        cells = 0
        for m in range(1, 13):
            for q in range(10):
                cell = surplus & (month == m) & (dec == q)
                a = cell & states["interior"]
                b = cell & states["at_cap"]
                if a.sum() < 3 or b.sum() < 3:
                    continue
                cells += 1
                pairs.append(defect[a].mean() - defect[b].mean())
                wts.append(min(a.sum(), b.sum()))
        if not pairs:
            rows.append(
                {
                    "year": year,
                    "cells": 0,
                    "matched_hours": 0,
                    "paired_diff": float("nan"),
                    "unmatched_diff": float("nan"),
                }
            )
            continue
        p, w = np.asarray(pairs), np.asarray(wts, dtype=float)
        raw = (
            defect[surplus & states["interior"]].mean()
            - defect[surplus & states["at_cap"]].mean()
        )
        rows.append(
            {
                "year": year,
                "cells": cells,
                "matched_hours": int(w.sum()),
                "paired_diff": float((p * w).sum() / w.sum()),
                "paired_pos_pct": float(100 * (p > 0).mean()),
                "unmatched_diff": float(raw),
            }
        )
    return rows


# ---------------------------------------------------------------- stage F
def stage_f() -> list[dict]:
    """Which limb is marginal — the battery, or the WALLED pumped-storage object?

    Pumped storage is EXEMPT from the shape anchor (its bound is nameplate), so
    a PS charge column can be interior too, and an interior PS column sets λ by
    the same reduced-cost argument. The C3a-2025 PS object is walled by owner
    ledger (non-public hourly PS data), so if the λ-setting hours are carried by
    the PS limb this lane is inside the wall and must stop. This cross-tabs the
    two limbs jointly on the belly-surplus mask and attributes the defect.
    """
    rows: list[dict] = []
    for year in YEARS:
        hod, month = _clock()
        price, demand = _system(year)
        lam = _ca_lambda(price, demand)
        hub = _hub(year)
        st = _storage(year)
        f_chg, f_dis = _envelope(year)
        cap = _monthly_power_cap(
            st["li_ion"]["chg"], st["li_ion"]["dis"], f_chg, f_dis, month
        )
        batt = _states(st["li_ion"]["chg"], cap * f_chg[hod])["interior"]
        ps_chg = st["pumped_storage"]["chg"]
        ps_cap = float(np.maximum(ps_chg, st["pumped_storage"]["dis"]).max())
        ps = (ps_chg > ZERO_MW) & (ps_chg < AT_BOUND_FRAC * ps_cap)
        belly = (hod >= BELLY[0]) & (hod < BELLY[1])
        surplus = belly & np.isfinite(hub) & (hub <= SURPLUS_MAX)
        defect = lam - hub
        total = defect[surplus].sum()

        for label, k in (
            ("battery_only", surplus & batt & ~ps),
            ("ps_only", surplus & ~batt & ps),
            ("both", surplus & batt & ps),
            ("neither", surplus & ~batt & ~ps),
        ):
            rows.append(
                {
                    "year": year,
                    "marginal_limb": label,
                    "n": int(k.sum()),
                    "hours_pct": float(100 * k.sum() / surplus.sum()),
                    "defect_mean": float(defect[k].mean()) if k.sum() else float("nan"),
                    "defect_share_pct": float(100 * defect[k].sum() / total)
                    if k.sum()
                    else 0.0,
                    "batt_chg_mw": float(st["li_ion"]["chg"][k].mean())
                    if k.sum()
                    else float("nan"),
                    "ps_chg_mw": float(ps_chg[k].mean()) if k.sum() else float("nan"),
                }
            )
    return rows


# ---------------------------------------------------------------- stage G
def stage_g() -> list[dict]:
    """Model vs MEASURED battery charge volume — is the defect volume or shape?

    The measured battery net is EIA-930 CISO ``NG: OTH`` (discharge +, charge −),
    the same series the armed anchor's own envelope is derived from
    (``scripts/derive_caiso_storage_shape.py``), read here on the model's
    non-leap 8760 frame. Pumped storage is absent from OTH by construction, so
    this is a battery-limb measurement and says nothing about the walled PS
    object. Reported both as MW in the belly and as a fleet-normalized rate, so
    the model's own position can be placed against the p95 capability statistic
    the anchor caps it at.
    """
    d = pd.read_parquet(EIA930, columns=["Local date", "Hour", "NG: OTH"])
    d["Local date"] = pd.to_datetime(d["Local date"])
    rows: list[dict] = []
    for year in YEARS:
        hod, month = _clock()
        dy = d[d["Local date"].dt.year == year].sort_values(["Local date", "Hour"])
        dy = dy[~((dy["Local date"].dt.month == 2) & (dy["Local date"].dt.day == 29))]
        h = _model_hour(dy["Local date"], year) + 0  # date carries the day; hour below
        h = h - dy["Local date"].dt.hour.to_numpy() + (dy["Hour"].to_numpy() - 1)
        meas = np.full(HOURS, np.nan)
        ok = (h >= 0) & (h < HOURS)
        meas[h[ok]] = np.nan_to_num(dy["NG: OTH"].to_numpy(dtype=float))[ok]
        meas_chg = np.clip(-meas, 0.0, None)

        st = _storage(year)
        f_chg, f_dis = _envelope(year)
        cap = _monthly_power_cap(
            st["li_ion"]["chg"], st["li_ion"]["dis"], f_chg, f_dis, month
        )
        model_chg = st["li_ion"]["chg"]
        hub = _hub(year)
        belly = (hod >= BELLY[0]) & (hod < BELLY[1])
        surplus = belly & np.isfinite(hub) & (hub <= SURPLUS_MAX)
        for window, mask in (
            ("all", np.ones(HOURS, bool)),
            ("belly", belly),
            ("belly_surplus", surplus),
        ):
            k = mask & np.isfinite(meas_chg)
            rows.append(
                {
                    "year": year,
                    "window": window,
                    "n": int(k.sum()),
                    "model_mw": float(model_chg[k].mean()),
                    "measured_mw": float(meas_chg[k].mean()),
                    "excess_mw": float((model_chg - meas_chg)[k].mean()),
                    "model_rate": float((model_chg[k] / cap[k]).mean()),
                    "measured_rate": float((meas_chg[k] / cap[k]).mean()),
                    "anchor_p95_rate": float(f_chg[hod][k].mean()),
                }
            )
    return rows


# ---------------------------------------------------------------- stage H
def stage_h() -> list[dict]:
    """The caiso-121 storage row, re-based — a BASIS correction, not a re-measure.

    caiso-121 §3 recorded "storage net (charging +) +1967/+2049/+2244 MW" and
    caiso-167 §7 forwarded it as the top of the in-state stack. That row is the
    model's ALL-TECH storage net against the measured EIA-930 ``NG: OTH`` term —
    and OTH **excludes pumped storage by construction**, as the anchor's own
    derive script states ("EIA-930 OTH does not carry Helms pumping"). So the
    model's PS pumping is differenced against a series that has no PS in it.
    This splits the row on a like-for-like battery basis. Nothing is re-derived
    and no residual is consulted; only the comparator is put on one basis, the
    same correction caiso-167 §1 made to caiso-121's price comparator.
    """
    d = pd.read_parquet(EIA930, columns=["Local date", "Hour", "NG: OTH"])
    d["Local date"] = pd.to_datetime(d["Local date"])
    hod, month = _clock()
    rows: list[dict] = []
    for year in YEARS:
        dy = d[d["Local date"].dt.year == year].sort_values(["Local date", "Hour"])
        dy = dy[~((dy["Local date"].dt.month == 2) & (dy["Local date"].dt.day == 29))]
        doy = pd.DatetimeIndex(dy["Local date"]).dayofyear.to_numpy()
        if year % 4 == 0:
            doy = np.where(
                pd.DatetimeIndex(dy["Local date"]).month.to_numpy() > 2, doy - 1, doy
            )
        h = (doy - 1) * 24 + (dy["Hour"].to_numpy() - 1)
        meas = np.full(HOURS, np.nan)
        ok = (h >= 0) & (h < HOURS)
        meas[h[ok]] = np.nan_to_num(dy["NG: OTH"].to_numpy(dtype=float))[ok]
        meas_chg = -meas  # charging positive, the caiso-121 sign convention

        st = _storage(year)
        batt = st["li_ion"]["chg"] - st["li_ion"]["dis"]
        ps = st["pumped_storage"]["chg"] - st["pumped_storage"]["dis"]
        hub = _hub(year)
        k = (
            (hod >= BELLY[0])
            & (hod < BELLY[1])
            & np.isfinite(hub)
            & (hub <= SURPLUS_MAX)
            & np.isfinite(meas_chg)
        )
        alltech = float((batt + ps - meas_chg)[k].mean())
        rows.append(
            {
                "year": year,
                "n": int(k.sum()),
                "caiso121_basis_mw": alltech,
                "battery_like_for_like_mw": float((batt - meas_chg)[k].mean()),
                "model_ps_net_mw": float(ps[k].mean()),
                "ps_share_of_row_pct": float(100 * ps[k].mean() / alltech),
            }
        )
    return rows


# ---------------------------------------------------------------- stage D
def stage_d(b_rows: list[dict]) -> list[dict]:
    """Reach: the share of the belly-surplus over-price that each state carries."""
    rows: list[dict] = []
    for year in YEARS:
        yr = [r for r in b_rows if r["year"] == year]
        total = next(r for r in yr if r["state"] == "ALL")
        for r in yr:
            if r["state"] == "ALL":
                continue
            rows.append(
                {
                    "year": year,
                    "state": r["state"],
                    "hours_pct": r["share_of_surplus_pct"],
                    "defect_mean": r["defect"],
                    "defect_share_pct": float(
                        100 * r["defect_twh_weighted"] / total["defect_twh_weighted"]
                    ),
                }
            )
    return rows


def _table(rows: list[dict], cols: list[str]) -> None:
    if not rows:
        print("   (no rows)")
        return
    widths = {c: max(len(c), *(len(f"{r.get(c, '')}") for r in rows)) for c in cols}
    print("   " + "  ".join(c.rjust(widths[c]) for c in cols))
    for r in rows:
        cells = []
        for c in cols:
            v = r.get(c, "")
            cells.append(
                (f"{v:.3f}" if isinstance(v, float) else f"{v}").rjust(widths[c])
            )
        print("   " + "  ".join(cells))


def main() -> None:
    print("=" * 78)
    print("caiso-168 PHASE 0 — is the CA belly dual held up by the storage bid?")
    print(
        "NO LP. Committed artifacts only. Keeper 2026-08-04-caiso164-zonal-loss-surface."
    )
    print("=" * 78)

    a_rows, a_months, caps = stage_a()
    print("\nA. BOUND CENSUS — recovered monthly battery fleet power cap (MW)")
    for y, c in caps["monthly_power_cap_mw"].items():
        print(f"   {y}: " + " ".join(f"{v:6.0f}" for v in c))
    print("   year-boundary self-consistency (independent solves):")
    for k, (dec, jan) in caps["year_boundary"].items():
        print(f"     {k}: {dec:.0f} -> {jan:.0f}  (delta {jan - dec:+.0f} MW)")

    print("\nA. charge state by window (li_ion vs pumped storage, kept separate)")
    _table(
        a_rows,
        [
            "year",
            "tech",
            "window",
            "n",
            "chg_mean_mw",
            "bound_mean_mw",
            "pct_zero",
            "pct_interior",
            "pct_at_cap",
            "twh_interior",
            "twh_at_cap",
        ],
    )

    print("\nA. belly-surplus charge state by month (li_ion)")
    _table(
        a_months,
        [
            "year",
            "month",
            "n",
            "chg_mean_mw",
            "bound_mean_mw",
            "pct_zero",
            "pct_interior",
            "pct_at_cap",
        ],
    )

    b_rows = stage_b()
    print("\nB. λ AND DEFECT BY CHARGE STATE (belly-surplus hours)")
    zcols = [c for c in b_rows[0] if c.startswith("lam_")]
    _table(
        b_rows,
        [
            "year",
            "state",
            "n",
            "share_of_surplus_pct",
            "ca_lambda_model",
            "ca_hub_measured",
            "defect",
        ]
        + zcols,
    )

    c_rows = stage_c()
    print("\nC. ARBITRAGE IDENTITY — λ_chg vs RTE·(λ_dis − adder), per day")
    _table(
        c_rows,
        [
            "year",
            "days",
            "obs_mean",
            "pred_mean",
            "mean_abs_err",
            "r",
            "within_1_pct",
            "within_5_pct",
        ],
    )

    c2_rows = stage_c2()
    print("\nC2. FLATNESS — within-day spread of the dual across belly-surplus hours")
    _table(
        c2_rows,
        [
            "year",
            "n_interior",
            "range_interior",
            "flat_pct_interior",
            "n_at_cap",
            "range_at_cap",
            "flat_pct_at_cap",
            "range_hub_interior",
        ],
    )

    d_rows = stage_d(b_rows)
    print("\nD. REACH — share of the belly-surplus over-price carried by each state")
    _table(d_rows, ["year", "state", "hours_pct", "defect_mean", "defect_share_pct"])

    g_rows = stage_g()
    print("\nG. VOLUME — model vs MEASURED (EIA-930 NG: OTH) battery charge")
    _table(
        g_rows,
        [
            "year",
            "window",
            "n",
            "model_mw",
            "measured_mw",
            "excess_mw",
            "model_rate",
            "measured_rate",
            "anchor_p95_rate",
        ],
    )

    h_rows = stage_h()
    print(
        "\nH. caiso-121 STORAGE ROW RE-BASED — model all-tech net vs a PS-excluding series"
    )
    _table(
        h_rows,
        [
            "year",
            "n",
            "caiso121_basis_mw",
            "battery_like_for_like_mw",
            "model_ps_net_mw",
            "ps_share_of_row_pct",
        ],
    )

    f_rows = stage_f()
    print("\nF. LIMB ATTRIBUTION — battery vs the WALLED pumped-storage object")
    _table(
        f_rows,
        [
            "year",
            "marginal_limb",
            "n",
            "hours_pct",
            "defect_mean",
            "defect_share_pct",
            "batt_chg_mw",
            "ps_chg_mw",
        ],
    )

    e_rows = stage_e()
    print(
        "\nE. MATCHED CONTROL — interior minus at-cap defect, within month x hub decile"
    )
    _table(
        e_rows,
        [
            "year",
            "cells",
            "matched_hours",
            "paired_diff",
            "paired_pos_pct",
            "unmatched_diff",
        ],
    )

    OUT.write_text(
        json.dumps(
            {
                "keeper": "2026-08-04-caiso164-zonal-loss-surface",
                "bundle": "results/calibration/caiso164_zonal_loss_surface",
                "regime": {
                    "belly": BELLY,
                    "evening": EVENING,
                    "surplus_max": SURPLUS_MAX,
                    "ca_hub": CA_HUB,
                },
                "physics": {
                    "rte": RTE,
                    "battery_dispatch_adder": DIS_ADDER,
                    "eps": EPS,
                },
                "recovered_caps": caps,
                "A_states": a_rows,
                "A_months": a_months,
                "B_lambda_by_state": b_rows,
                "C_arbitrage_identity": c_rows,
                "C2_flatness": c2_rows,
                "D_reach": d_rows,
                "E_matched_control": e_rows,
                "F_limb_attribution": f_rows,
                "G_volume": g_rows,
                "H_caiso121_rebased": h_rows,
            },
            indent=1,
        )
        + "\n"
    )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
