#!/usr/bin/env python3
"""nyiso-173 phase 0 — anatomy of the NYISO CC availability over-statement.

ZERO SOLVE. Every series here is a committed artifact or a raw measured record;
no parameter is touched and nothing is written outside
``results/calibration/_nyiso173_cc_availability_anatomy.json``.

THE OBJECT. nyiso-172 §3.4 established with a ONE-SIDED PROOF that the measured
CC fleet's maximum output WITHIN A MONTH is a strict lower bound on what that
fleet could have produced that month, and that the model's CC exceeds it in
93 / 773 / 1,211 hours of 2023 / 2024 / 2025. It NAMED a cause and explicitly
declined to establish it: ``UNIT_OUTAGE_MIN_DAYS = 5``
(:mod:`market_sim.data.outages`) makes sub-5-day derates invisible to the armed
overlay, and the companion partial-plateau overlay is a sustained-ceiling
construction. This probe tests that hypothesis and two things the bound needs
before it can carry a lever.

THE PRE-REGISTERED GATES (``results/calibration/PREREG-nyiso173-cc-availability-anatomy.md``,
committed WITH this file and BEFORE either ran):

* **P1a** — in the violation hours, does the MAJORITY of the measured CC
  fleet's shortfall from its own demonstrated capability sit in states the
  armed overlay cannot see? PASS iff share(B) + share(C) > 0.50 in all three
  years.
* **P1b** — given P1a, is the §3.4 NAMED carrier (sub-5-day FULL STOPS, state
  B) dominant over partial derates (state C)? PASS iff share(B) > share(C) in
  all three years. A P1b FAIL leaves the input gap real but re-names its
  carrier.
* **P2** — availability or shape? PASS iff in 2025 the mean model-minus-measured
  CC gap is positive in the top three actual-price deciles, the top three load
  deciles, AND every quintile of the measured fleet's own online-unit count.
* **P3** — per-plant or portfolio artifact? PASS iff the model's CC exceeds the
  ADDITIVE per-plant bound ``Σ_p M_p,m`` (strictly looser than the fleet bound,
  so strictly stronger a claim) in ≥ 1 % of 2025's hours.
* **P4** — rule 19 [R-ONE-MECH] attribution of everything shaping CC
  availability in the keeper today. Reported, never gated.

CONSTRUCTION NOTES, all declared in the prereg before running:

* ``cap_u``, a unit's capability reference, is its own WITHIN-YEAR MAXIMUM
  gross. That is availability-INCLUSIVE, so every shortfall statistic here is
  CONSERVATIVE (a unit derated all year measures a depressed ``cap_u``).
* The state thresholds are the DETECTOR'S OWN, read and never chosen (rule 23
  [R-FROZEN-DERIVE]): ``ST_GAS_CF_PEAK`` 0.02 is the event-based off threshold
  the CC/gas-steam detector uses, ``ST_GAS_MIN_OUTAGE_HOURS`` 120 its duration
  floor, and ``_CEILING_FRAC`` 0.65 the frozen plateau detector's
  depressed-ceiling fraction.
* Rule 13 [R-MEASURED]: CAMPD enters as conduct identification only. The
  within-month bound is a measured OUTCOME used as evidence and is never fed
  back as an input.
* Rule 22 [R-HOLDOUT]: every year read is 2023, 2024 or 2025.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.chp import _chp_by_plant  # noqa: E402
from scripts.data.derive_actual_lmp import _std_hour_index  # noqa: E402

YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/nyiso159_lossarm_B"
ACTUAL_HOURLY = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
UNIT_OUTAGE_CSV = RAW_DATA_DIR / "campd-unit-outages-NYISO.csv"
LAYUP_CSV = RAW_DATA_DIR / "campd-unit-outages-layup-NYISO.csv"
OUT = REPO / "results/calibration/_nyiso173_cc_availability_anatomy.json"

#: Fixed standard-time clock, as nyiso169b/170/171/172 (America/New_York raises
#: a DST nonexistent-time error on 2023-03-12 02:00).
STD_TZ = "Etc/GMT+5"

#: The CC classes of the nyiso-172 §3.4 bound, unchanged.
CC_CLASSES = ("CC_CHP", "CC_REGULAR")

#: Detector constants, MIRRORED from scripts/lib/outage_detect.py for the state
#: classification only (that module is the source of truth; these are read,
#: never written, and never swept — rule 23 [R-FROZEN-DERIVE]).
CF_OFF = 0.02  # outage_detect.ST_GAS_CF_PEAK — the event-based off threshold
MIN_OUTAGE_HOURS = 120  # outage_detect.ST_GAS_MIN_OUTAGE_HOURS == 5 days
CEILING_FRAC = 0.65  # derive_partial_outages._CEILING_FRAC

#: East River — CC_CHP under the shared CAMPD unitType construction but ST_CHP
#: in thermal_tranches_NYISO.csv (nyiso-171 §5, carried unrepaired). Its
#: presence INFLATES the measured CC series and therefore LOOSENS the bound.
EAST_RIVER = 2493

#: P3 bar: the model must exceed the additive per-plant bound in this share of
#: 2025's hours for the object to read PER-PLANT GROUNDED.
P3_MIN_SHARE = 0.01


# ----------------------------------------------------------------- loaders --


def chp_plants() -> set[int]:
    """EIA-860 CHP plant codes — the model's own CHP determination."""
    flags = _chp_by_plant(RAW_DATA_DIR / "eia-860", 2025)
    return {int(k) for k, v in flags.items() if str(v).strip().upper() == "Y"}


def campd_cc_units(year: int, chpset: set[int]) -> pd.DataFrame:
    """Measured CC unit-hour frame on the 8760 clock.

    Returns one row per (unit, hour) carrying ``_fid`` (plant code), ``unitId``,
    ``_h`` (hour of the model clock) and ``grossLoad``, restricted to the CC
    classes by the identical nyiso-170/172 ``unitType`` × EIA-860 construction.
    """
    d = pd.read_parquet(
        RAW_DATA_DIR / f"campd-unit-level/NY_{year}.parquet",
        columns=["facilityId", "unitId", "unitType", "date", "hour", "grossLoad"],
    )
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    d = d.assign(
        _h=_std_hour_index(pd.DatetimeIndex(ts).tz_localize(STD_TZ), year, STD_TZ),
        _fid=d["facilityId"].astype(int),
        _ut=d["unitType"].fillna(""),
    )
    # CC_CHP + CC_REGULAR together are every combined-cycle unit, CHP or not,
    # so the EIA-860 CHP split does not enter here (it does in nyiso-172's
    # per-class construction; this probe sums the two classes exactly as its
    # §3.4 bound does).
    del chpset
    sel = d["_ut"].str.contains("Combined cycle")
    d = d[sel & d["_h"].between(0, 8759)].copy()
    # CAMPD reports grossLoad as NULL for a non-operating unit-hour (52 % of NY
    # CC unit-hours in 2025). nyiso-172 read the series through
    # ``groupby().sum()``, which skips nulls, i.e. treats them as ZERO output —
    # reproduced here explicitly so this probe's fleet series is identical to
    # the one the §3.4 bound was computed on.
    d["grossLoad"] = d["grossLoad"].fillna(0.0)
    return d[["_fid", "unitId", "_h", "grossLoad"]]


def unit_matrix(d: pd.DataFrame) -> tuple[np.ndarray, list[tuple[int, str]]]:
    """Return ``(gen[n_units, 8760], keys)`` from the CC unit-hour frame."""
    d = d.copy()
    d["_key"] = list(zip(d["_fid"].to_numpy(), d["unitId"].astype(str)))
    keys = sorted(set(d["_key"]))
    idx = {k: i for i, k in enumerate(keys)}
    gen = np.zeros((len(keys), 8760), dtype=float)
    rows = np.fromiter((idx[k] for k in d["_key"]), dtype=int, count=len(d))
    np.add.at(gen, (rows, d["_h"].to_numpy(dtype=int)), d["grossLoad"].to_numpy(float))
    return gen, keys


def model_hourly(year: int, klass: str) -> np.ndarray:
    """The keeper's own P1 hourly MW for one class (rule 15: read, don't replay)."""
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & (c["klass"] == klass)]
    s = c.set_index("hour")["mw"].reindex(range(8760)).fillna(0.0)
    return s.to_numpy(dtype=float)


def model_cc(year: int) -> np.ndarray:
    """Model CC = CC_CHP + CC_REGULAR, the nyiso-172 §3.4 construction."""
    return sum(model_hourly(year, k) for k in CC_CLASSES)


def system_load(year: int) -> np.ndarray:
    """Total NYCA model demand by hour, summed over zones (P1 system sidecar)."""
    s = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    ser = s.groupby("hour")["demand"].sum().reindex(range(8760))
    return ser.ffill().bfill().to_numpy(dtype=float)


def actual_price(year: int, basis: str = "da") -> np.ndarray:
    """NYCA reference actual price on the 8760 clock."""
    d = pd.read_parquet(ACTUAL_HOURLY)
    d = d[d["year"] == year]
    s = d.set_index("hour")[basis].reindex(range(8760))
    return s.ffill().bfill().to_numpy(dtype=float)


def month_of_hour() -> np.ndarray:
    """Calendar month (1-12) for each of the 8760 standard hours."""
    days = pd.date_range("2023-01-01", "2023-12-31", freq="D")
    return np.repeat(days.month.to_numpy(), 24)[:8760]


def hour_of_year(ts: pd.Timestamp, year: int) -> int:
    """0-based hour of the model's fixed 8760 clock for a timestamp."""
    base = pd.Timestamp(year=year, month=1, day=1)
    off = (ts.normalize() - base).days
    if ts.month > 2 or (ts.month == 2 and ts.day >= 29):
        # Feb 29 is dropped from the clock; a leap-year date after it shifts back.
        if pd.Timestamp(year=year, month=12, day=31).dayofyear == 366:
            off -= 1
    return int(off) * 24 + int(ts.hour)


def window_mask(csv: Path, keys: list[tuple[int, str]], year: int) -> np.ndarray:
    """``[n_units, 8760]`` bool mask of the CSV's windows, per unit.

    Reproduces :func:`market_sim.data.outages.unit_outage_event_window`'s
    day-granular reconstruction — ``[outage_start, outage_end + 1 day)`` — and
    clips to ``year`` on the model clock, exactly as the engine's loader does.
    """
    m = np.zeros((len(keys), 8760), dtype=bool)
    if not csv.exists():
        return m
    df = pd.read_csv(csv)
    idx = {(int(f), str(u)): i for i, (f, u) in enumerate(keys)}
    for r in df.itertuples(index=False):
        i = idx.get((int(r.facility_id), str(r.unit_id)))
        if i is None:
            continue
        start = pd.Timestamp(r.outage_start)
        stop = pd.Timestamp(r.outage_end) + pd.Timedelta(days=1)
        if stop <= start or start.year > year or stop.year < year:
            continue
        lo = 0 if start.year < year else hour_of_year(start, year)
        hi = 8760 if stop.year > year else hour_of_year(stop, year)
        lo, hi = max(0, min(lo, 8760)), max(0, min(hi, 8760))
        if hi > lo:
            m[i, lo:hi] = True
    return m


# ----------------------------------------------------------------- helpers --


def run_bounds(mask: np.ndarray) -> list[tuple[int, int]]:
    """``[(start, stop)]`` half-open bounds of the contiguous True segments."""
    m = np.asarray(mask, dtype=bool)
    if not m.any():
        return []
    padded = np.concatenate([[False], m, [False]])
    edges = np.diff(padded.astype(np.int8))
    return list(
        zip(np.flatnonzero(edges == 1).tolist(), np.flatnonzero(edges == -1).tolist())
    )


def daily_max(gen_u: np.ndarray) -> np.ndarray:
    """Per-hour broadcast of the unit's own daily maximum output."""
    dm = gen_u.reshape(365, 24).max(axis=1)
    return np.repeat(dm, 24)


def decile_means(x: np.ndarray, by: np.ndarray, n: int = 10) -> list[float]:
    """Mean of ``x`` within each of ``n`` equal-count bins of ``by``."""
    order = np.argsort(by, kind="stable")
    out = []
    for chunk in np.array_split(order, n):
        out.append(round(float(x[chunk].mean()), 1) if len(chunk) else float("nan"))
    return out


# ------------------------------------------------------- the state machine --


def unit_states(
    gen: np.ndarray, keys: list[tuple[int, str]], year: int
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Classify every (unit, hour) into the four shortfall states A/B/D/C.

    Returns ``(states, shortfall)`` where ``states`` maps each label to a
    ``[n_units, 8760]`` bool mask and ``shortfall`` is
    ``max(0, cap_u - gen_u,t)`` in MW. States are assigned A -> B -> D -> C, so
    they partition the shortfall exactly (see the prereg §2 table):

    A  inside a detected >= 5-day window in the ARMED extract     VISIBLE
    B  off (< 0.02 x cap_u) in an off episode < 120 h, not in A   INVISIBLE
    D  inside a lay-up window, not in A or B                      excluded (economic)
    C  on and below cap_u, not in A/B/D                           INVISIBLE
    """
    cap = gen.max(axis=1)
    cap_safe = np.where(cap > 0.0, cap, 1.0)
    shortfall = np.maximum(0.0, cap[:, None] - gen)

    off = gen < (CF_OFF * cap_safe)[:, None]
    a = window_mask(UNIT_OUTAGE_CSV, keys, year)
    layup = window_mask(LAYUP_CSV, keys, year)

    # B: an off HOUR whose contiguous off EPISODE is shorter than the detector's
    # own 120 h floor. Episode length is measured on the unit's raw off mask,
    # independently of A, so the classification never depends on what the
    # extract happened to catch.
    b_short = np.zeros_like(off)
    for i in range(off.shape[0]):
        for lo, hi in run_bounds(off[i]):
            if (hi - lo) < MIN_OUTAGE_HOURS:
                b_short[i, lo:hi] = True

    st_a = a
    st_b = b_short & ~st_a
    st_d = layup & ~st_a & ~st_b
    st_c = ~st_a & ~st_b & ~st_d & (shortfall > 0.0)
    return {"A": st_a, "B": st_b, "C": st_c, "D": st_d}, shortfall


# ------------------------------------------------------------------ gates ---


def p1_states(
    gen: np.ndarray,
    keys: list[tuple[int, str]],
    year: int,
    violation: np.ndarray,
) -> dict:
    """P1 — the shortfall decomposition in the violation hours, plus histograms."""
    states, shortfall = unit_states(gen, keys, year)
    cap = gen.max(axis=1)

    def share(mask_hours: np.ndarray) -> dict:
        tot = float(shortfall[:, mask_hours].sum())
        out = {"total_mwh": round(tot, 0)}
        for lab, m in states.items():
            v = float((shortfall * m)[:, mask_hours].sum())
            out[f"{lab}_mwh"] = round(v, 0)
            out[f"{lab}_share"] = round(v / tot, 4) if tot > 0 else 0.0
        return out

    all_h = np.ones(8760, dtype=bool)
    viol = share(violation)
    whole = share(all_h)

    # Duration histogram of measured CC off episodes (reported, not gated).
    cap_safe = np.where(cap > 0.0, cap, 1.0)
    off = gen < (CF_OFF * cap_safe)[:, None]
    buckets = {"lt_24h": 0, "24_72h": 0, "72_120h": 0, "ge_120h": 0}
    bucket_mwh = dict.fromkeys(buckets, 0.0)
    for i in range(off.shape[0]):
        for lo, hi in run_bounds(off[i]):
            n = hi - lo
            key = (
                "lt_24h"
                if n < 24
                else "24_72h"
                if n < 72
                else "72_120h"
                if n < MIN_OUTAGE_HOURS
                else "ge_120h"
            )
            buckets[key] += 1
            bucket_mwh[key] += float(cap[i]) * n

    # Depressed-ceiling plateaus: on, but the unit's own daily max sits below
    # CEILING_FRAC of its demonstrated capability (the frozen plateau basis).
    plateau_days = 0
    plateau_mwh = 0.0
    for i in range(gen.shape[0]):
        if cap[i] <= 0:
            continue
        dm = gen[i].reshape(365, 24).max(axis=1)
        dmean = gen[i].reshape(365, 24).mean(axis=1)
        low = (dm < CEILING_FRAC * cap[i]) & (dmean > CF_OFF * cap[i])
        plateau_days += int(low.sum())
        hourly_low = np.repeat(low, 24)
        plateau_mwh += float(np.maximum(0.0, cap[i] - gen[i])[hourly_low].sum())

    return {
        "violation_hours": int(violation.sum()),
        "shortfall_in_violation_hours": viol,
        "shortfall_all_hours": whole,
        "off_episode_histogram_count": buckets,
        "off_episode_capacity_mwh": {k: round(v, 0) for k, v in bucket_mwh.items()},
        "depressed_ceiling_unit_days": plateau_days,
        "depressed_ceiling_shortfall_mwh": round(plateau_mwh, 0),
        "n_units": int(gen.shape[0]),
        "fleet_cap_mw": round(float(cap.sum()), 1),
    }


def p2_availability_or_shape(
    year: int, gen: np.ndarray, mo: np.ndarray, me: np.ndarray
) -> dict:
    """P2 — does the mean gap survive conditioning on price, load and on-count?"""
    gap = mo - me
    price = actual_price(year, "da")
    load = system_load(year)
    cap = gen.max(axis=1)
    cap_safe = np.where(cap > 0.0, cap, 1.0)
    on_count = (gen >= (CF_OFF * cap_safe)[:, None]).sum(axis=0).astype(float)

    by_price = decile_means(gap, price)
    by_load = decile_means(gap, load)
    by_on = decile_means(gap, on_count, n=5)
    return {
        "mean_gap_mw": round(float(gap.mean()), 1),
        "gap_by_actual_price_decile": by_price,
        "gap_by_load_decile": by_load,
        "gap_by_online_unit_count_quintile": by_on,
        "top3_price_deciles_positive": bool(all(v > 0 for v in by_price[-3:])),
        "top3_load_deciles_positive": bool(all(v > 0 for v in by_load[-3:])),
        "all_on_count_quintiles_positive": bool(all(v > 0 for v in by_on)),
        "mean_online_units": round(float(on_count.mean()), 2),
    }


def p3_per_plant(
    year: int, d: pd.DataFrame, mo: np.ndarray, mon: np.ndarray, chpset: set[int]
) -> dict:
    """P3 — the additive per-plant bound, coverage, and the East River sensitivity."""
    del chpset
    plants = sorted(d["_fid"].unique().tolist())
    pg = np.zeros((len(plants), 8760), dtype=float)
    pidx = {p: i for i, p in enumerate(plants)}
    rows = np.fromiter((pidx[p] for p in d["_fid"]), dtype=int, count=len(d))
    np.add.at(pg, (rows, d["_h"].to_numpy(dtype=int)), d["grossLoad"].to_numpy(float))

    fleet = pg.sum(axis=0)
    add_bound = np.zeros(8760)
    fleet_bound = np.zeros(8760)
    coverage = {}
    for m in range(1, 13):
        sel = mon == m
        add_bound[sel] = float(pg[:, sel].max(axis=1).sum())
        fleet_bound[sel] = float(fleet[sel].max())
        cov = fleet_bound[sel][0] / add_bound[sel][0] if add_bound[sel][0] > 0 else 0.0
        coverage[str(m)] = round(float(cov), 4)

    add_viol = mo > add_bound
    fleet_viol = mo > fleet_bound

    # East River sensitivity: 2493 is CC_CHP under the shared CAMPD
    # construction but ST_CHP in the model artifact, so its measured MW inflate
    # this series and LOOSEN the bound. Removing it can only raise the count.
    keep = [i for i, p in enumerate(plants) if p != EAST_RIVER]
    fleet_noer = pg[keep].sum(axis=0)
    bound_noer = np.zeros(8760)
    for m in range(1, 13):
        sel = mon == m
        bound_noer[sel] = float(fleet_noer[sel].max())
    noer_viol = mo > bound_noer

    # Which plants carry the violation-hour shortfall.
    cap_p = pg.max(axis=1)
    short_p = np.maximum(0.0, cap_p[:, None] - pg)[:, fleet_viol].sum(axis=1)
    order = np.argsort(-short_p)[:8]
    top = [
        {
            "plant": int(plants[i]),
            "cap_mw": round(float(cap_p[i]), 1),
            "violation_hour_shortfall_gwh": round(float(short_p[i]) / 1000.0, 2),
        }
        for i in order
    ]

    return {
        "n_plants": len(plants),
        "hours_above_fleet_bound": int(fleet_viol.sum()),
        "hours_above_additive_per_plant_bound": int(add_viol.sum()),
        "additive_share_of_year": round(float(add_viol.sum()) / 8760, 4),
        "coverage_fleet_over_additive_by_month": coverage,
        "coverage_mean": round(float(np.mean(list(coverage.values()))), 4),
        "east_river_present": EAST_RIVER in plants,
        "hours_above_fleet_bound_ex_east_river": int(noer_viol.sum()),
        "top_violation_hour_shortfall_plants": top,
    }


def p4_attribution() -> dict:
    """P4 — rule 19 [R-ONE-MECH]: everything shaping CC availability today."""
    cfg = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    fields = [
        "outage_source",
        "historic_outage_overlay",
        "unit_outage_short_windows",
        "unit_partial_outage_windows",
        "unit_outage_maxgen_events",
        "unit_outage_lp_capacity_basis",
        "unit_outage_fleet_status_scope",
        "mustrun_layup_window_mask",
        "cc_nameplate_summer_derate",
        "cc_winter_capability_basis",
        "cc_outage_derate_from_top",
        "temp_dependent_derate",
        "gt_ambient_derate",
        "correlated_forced_outage",
        "nuclear_unit_availability",
        "nysdec_peaker_rule_availability",
        "wefor_residual",
    ]
    armed = {f: cfg.get(f, "<absent>") for f in fields}

    extracts = {}
    for name in (
        "campd-unit-outages-NYISO.csv",
        "campd-unit-outages-short-NYISO.csv",
        "campd-partial-outages-NYISO.csv",
        "campd-unit-outages-layup-NYISO.csv",
        "campd-unit-outages-maxgen-NYISO.csv",
    ):
        p = RAW_DATA_DIR / name
        if not p.exists():
            extracts[name] = {"exists": False, "data_rows": 0}
            continue
        n = sum(1 for _ in p.open()) - 1
        cc_rows = 0
        if n > 0:
            df = pd.read_csv(p)
            if "plant_group" in df.columns:
                cc_rows = int(df["plant_group"].isin(CC_CLASSES).sum())
        extracts[name] = {"exists": True, "data_rows": n, "cc_rows": cc_rows}

    diag = json.loads((KEEPER / "legitimacy_diagnostics.json").read_text())
    d2 = {}
    for row in diag["diagnostics"]["D2"]["rows"]:
        if str(row.get("class")) in CC_CLASSES:
            d2.setdefault(str(row.get("year")), []).append(
                {
                    "klass": row.get("class"),
                    "mechanism": row.get("mechanism"),
                    "forced_twh": row.get("forced_twh"),
                    "share_of_class": row.get("share_of_class"),
                }
            )
    return {
        "armed_availability_config": armed,
        "nyiso_outage_extracts": extracts,
        "d2_rows_forcing_cc": d2,
    }


# ------------------------------------------------------------------- main ---


def main() -> None:
    chpset = chp_plants()
    mon = month_of_hour()
    result: dict = {
        "prereg": "results/calibration/PREREG-nyiso173-cc-availability-anatomy.md",
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "solves": 0,
        "by_year": {},
    }

    for year in YEARS:
        d = campd_cc_units(year, chpset)
        gen, keys = unit_matrix(d)
        mo = model_cc(year)
        me = gen.sum(axis=0)

        bound = np.zeros(8760)
        for m in range(1, 13):
            sel = mon == m
            bound[sel] = float(me[sel].max())
        violation = mo > bound

        y = {
            "P1": p1_states(gen, keys, year, violation),
            "P2": p2_availability_or_shape(year, gen, mo, me),
            "P3": p3_per_plant(year, d, mo, mon, chpset),
            "model_cc_twh": round(float(mo.sum()) / 1e6, 4),
            "measured_cc_twh": round(float(me.sum()) / 1e6, 4),
        }
        result["by_year"][str(year)] = y

        p1 = y["P1"]["shortfall_in_violation_hours"]
        print(f"\n=== {year}   violation hours {y['P1']['violation_hours']}")
        print(
            f"  P1 shortfall in violation hours: "
            f"A(>=5d, ARMED) {p1['A_share']:.3f}  "
            f"B(<5d off, INVISIBLE) {p1['B_share']:.3f}  "
            f"C(partial, INVISIBLE) {p1['C_share']:.3f}  "
            f"D(lay-up) {p1['D_share']:.3f}"
        )
        print(f"     off-episode counts {y['P1']['off_episode_histogram_count']}")
        print(
            f"     depressed-ceiling unit-days {y['P1']['depressed_ceiling_unit_days']}"
            f"  shortfall {y['P1']['depressed_ceiling_shortfall_mwh']:.0f} MWh"
        )
        p2 = y["P2"]
        print(f"  P2 mean gap {p2['mean_gap_mw']:+.1f} MW")
        print(f"     by actual-price decile {p2['gap_by_actual_price_decile']}")
        print(f"     by load decile         {p2['gap_by_load_decile']}")
        print(f"     by on-count quintile   {p2['gap_by_online_unit_count_quintile']}")
        p3 = y["P3"]
        print(
            f"  P3 fleet bound {p3['hours_above_fleet_bound']} h  "
            f"ADDITIVE per-plant bound {p3['hours_above_additive_per_plant_bound']} h "
            f"({p3['additive_share_of_year']:.2%})  "
            f"coverage {p3['coverage_mean']:.3f}  "
            f"ex-East-River {p3['hours_above_fleet_bound_ex_east_river']} h"
        )

    # ------------------------------------------------------------- verdicts --
    yr = result["by_year"]
    p1a = all(
        yr[str(y)]["P1"]["shortfall_in_violation_hours"]["B_share"]
        + yr[str(y)]["P1"]["shortfall_in_violation_hours"]["C_share"]
        > 0.50
        for y in YEARS
    )
    p1b = all(
        yr[str(y)]["P1"]["shortfall_in_violation_hours"]["B_share"]
        > yr[str(y)]["P1"]["shortfall_in_violation_hours"]["C_share"]
        for y in YEARS
    )
    g = yr["2025"]["P2"]
    p2 = bool(
        g["top3_price_deciles_positive"]
        and g["top3_load_deciles_positive"]
        and g["all_on_count_quintiles_positive"]
    )
    p3 = yr["2025"]["P3"]["additive_share_of_year"] >= P3_MIN_SHARE

    result["P4_attribution"] = p4_attribution()
    result["verdict"] = {
        "P1a_overlay_blind_majority_all_years": bool(p1a),
        "P1b_sub5day_fullstop_dominant_all_years": bool(p1b),
        "P2_availability_not_shape_2025": p2,
        "P3_per_plant_grounded_2025": bool(p3),
        "proceed_to_phase_2": bool(p1a and p2 and p3),
    }

    OUT.write_text(json.dumps(result, indent=1))
    print("\n  VERDICT " + json.dumps(result["verdict"], indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
