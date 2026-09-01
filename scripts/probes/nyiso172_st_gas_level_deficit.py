#!/usr/bin/env python3
"""nyiso-172 phase 0 — identify the NYISO ST_GAS level deficit.

ZERO SOLVE. Every series is a committed artifact or a raw measured record.

The object (handed forward by nyiso-170 §4 as the "third thing" — a composition
error that is NOT an hour-local swap): the keeper's ST_GAS runs 9.7866 TWh
against a 13.7121 TWh benchmark in 2025, −28.63 %, the largest absolute class
error in the failing year, negative in all twelve months, and already the most
heavily floored merchant class in NYISO.

Phase 0 answers three questions BEFORE any parameter is touched:

  (a) is the deficit PRICE-CONDITIONAL — does it widen as fuel gets expensive
      relative to power (the "exits too readily" signature), or is it flat in
      price (a capacity/availability object, a different lane)?
  (b) is it CAPACITY or CONDUCT — can the model's ST_GAS even reach the
      measured level at full availability?
  (c) what already forces or shapes ST_GAS today — a full rule 19 [R-ONE-MECH]
      D-2 attribution, so any change REPLACES rather than stacks.

Plus the brief's named trap, adjudicated two independent ways: whether
``gas_st_startup_cost`` is grounded in NYISO's own measured start conduct (S4),
and whether it could move ST_GAS volume in the needed direction at all (S5).

Pre-registered gates (see PREREG-nyiso172-st-gas-level-deficit.md, committed
with this file BEFORE it was run):

  S1  rule 19 attribution, complete and unambiguous
  S2  THE STOP CONDITION — price-conditional (proceed) vs flat (stop, say so)
  S3  capacity vs conduct
  S4  gas_st_startup_cost grounding in measured NYISO start conduct
  S5  gas_st_startup_cost DIRECTION, proven on the code ex ante
  S6  does the deficit track gas price within sample (monthly, n=36)

Rule 13 [R-MEASURED]: CAMPD enters ONLY as conduct identification. Nothing is
pinned to observed generation and no statistic is tuned to a residual.
Rule 22 [R-HOLDOUT]: 2023/2024/2025 only.
"""

from __future__ import annotations

import gzip
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
BENCH = REPO / "frontend/data/backcast/bench/NYISO"
GAS_CSV = REPO / "data/raw/gas-prices/transco_z6_ny_daily.csv"
ACTUAL_HOURLY = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
TRANCHES = RAW_DATA_DIR / "_processed-legacy/thermal_tranches_NYISO.csv"
OUT = REPO / "results/calibration/_nyiso172_st_gas_level_deficit.json"

#: Fixed standard-time clock, as nyiso169b/170/171 (America/New_York raises a
#: DST nonexistent-time error on 2023-03-12 02:00).
STD_TZ = "Etc/GMT+5"

#: CAMPD unitType predicate per model class — the nyiso-170 construction,
#: unchanged. Steam is every boiler form the NY vocabulary carries.
UNIT_KIND = {
    "CC_CHP": ("Combined cycle", True),
    "CC_REGULAR": ("Combined cycle", False),
    "CT_CHP": ("Combustion turbine", True),
    "CT_PEAKER": ("Combustion turbine", False),
    "ST_CHP": ("STEAM", True),
    "ST_GAS": ("STEAM", False),
}

#: ST_GAS_COMMITMENT_PARAMS, mirrored here for the S4 admissibility check only
#: (constants.py is the source of truth; this is read, never written).
ST_GAS_MIN_RUN_H = (24, 48)
ST_GAS_MIN_DOWN_H = (8, 12)
ST_GAS_STARTUP_PER_MW = (55.0, 75.0)

#: A unit/class is "on" above this many MW. CAMPD reports small nonzero values
#: for a unit coming up or down; 1 MW is the floor every prior NYISO probe used.
ON_MW = 1.0

#: S2 gate thresholds.
S2_SPREAD_FRAC = 0.20
N_DECILES = 10


# ----------------------------------------------------------------- loaders --


def chp_plants() -> set[int]:
    """EIA-860 CHP plant codes — the model's own CHP determination."""
    flags = _chp_by_plant(RAW_DATA_DIR / "eia-860", 2025)
    return {int(k) for k, v in flags.items() if str(v).strip().upper() == "Y"}


def campd_frame(year: int) -> pd.DataFrame:
    """CAMPD NY unit-level hourly, stamped onto the model's 8760 clock."""
    d = pd.read_parquet(
        RAW_DATA_DIR / f"campd-unit-level/NY_{year}.parquet",
        columns=["facilityId", "unitId", "unitType", "date", "hour", "grossLoad"],
    )
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    return d.assign(
        _h=_std_hour_index(pd.DatetimeIndex(ts).tz_localize(STD_TZ), year, STD_TZ),
        _fid=d["facilityId"].astype(int),
        _ut=d["unitType"].fillna(""),
    )


def class_mask(d: pd.DataFrame, klass: str, chpset: set[int]) -> pd.Series:
    """Row mask selecting one model class out of the CAMPD frame."""
    kind, is_chp = UNIT_KIND[klass]
    ut = d["_ut"]
    sel = (
        ut.str.contains("fired|boiler", case=False)
        if kind == "STEAM"
        else ut.str.contains(kind)
    )
    inchp = d["_fid"].isin(chpset)
    return sel & (inchp if is_chp else ~inchp)


def measured_hourly(d: pd.DataFrame, klass: str, chpset: set[int]) -> np.ndarray:
    """Measured GROSS hourly MW for one model class, on the 8760 clock."""
    sel = class_mask(d, klass, chpset)
    s = pd.Series(d.loc[sel, "grossLoad"].to_numpy())
    g = s.groupby(d.loc[sel, "_h"].to_numpy()).sum()
    return g.reindex(range(8760)).fillna(0.0).to_numpy(dtype=float)


def model_hourly(year: int, klass: str) -> np.ndarray:
    """The keeper's own P1 hourly MW for one class (rule 15: read, don't replay)."""
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & (c["klass"] == klass)]
    s = c.set_index("hour")["mw"].reindex(range(8760)).fillna(0.0)
    return s.to_numpy(dtype=float)


def bench_classes(year: int) -> dict[str, float]:
    """Committed grid-delivered class volumes, TWh."""
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]["classFull"]


def actual_price(year: int, basis: str = "da") -> np.ndarray:
    """NYCA reference actual price on the 8760 clock."""
    d = pd.read_parquet(ACTUAL_HOURLY)
    d = d[d["year"] == year]
    s = d.set_index("hour")[basis].reindex(range(8760))
    return s.ffill().bfill().to_numpy(dtype=float)


def hourly_gas(year: int) -> np.ndarray:
    """Daily Transco Z6 NY spot broadcast to the year's 8760 standard hours."""
    gas = pd.read_csv(GAS_CSV, parse_dates=["date"]).set_index("date")
    ser = gas["transco_z6_ny_usd_mmbtu"].astype(float)
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    ser = ser.reindex(days).ffill().bfill()
    return np.repeat(ser.to_numpy(dtype=float), 24)[:8760]


def month_of_hour() -> np.ndarray:
    """Calendar month (1-12) for each of the 8760 standard hours."""
    days = pd.date_range("2023-01-01", "2023-12-31", freq="D")
    return np.repeat(days.month.to_numpy(), 24)[:8760]


# ----------------------------------------------------------------- helpers --


def runs_of(mask: np.ndarray) -> list[int]:
    """Lengths of the contiguous True segments of ``mask``."""
    m = np.asarray(mask, dtype=bool)
    if not m.any():
        return []
    padded = np.concatenate([[False], m, [False]])
    edges = np.diff(padded.astype(np.int8))
    return (np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)).tolist()


def t50(imh_mid: np.ndarray, out: np.ndarray) -> float | None:
    """The IMH at which ``out`` first reaches 50 % of its own p95, interpolated.

    ``out`` is the per-decile mean output and ``imh_mid`` the decile's mean IMH,
    both ordered by decile. Returns ``None`` when the series never crosses.
    """
    target = 0.5 * float(np.percentile(out, 95))
    for i in range(1, len(out)):
        if out[i - 1] < target <= out[i]:
            span = out[i] - out[i - 1]
            frac = (target - out[i - 1]) / span if span > 0 else 0.0
            return float(imh_mid[i - 1] + frac * (imh_mid[i] - imh_mid[i - 1]))
    return float(imh_mid[0]) if out[0] >= target else None


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman rank correlation, no scipy (rule: stdlib + numpy only here)."""
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    den = float(np.sqrt((ra**2).sum() * (rb**2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else 0.0


def ols(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """``(slope, intercept, r2)`` of a simple least-squares fit."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xm, ym = x.mean(), y.mean()
    sxx = float(((x - xm) ** 2).sum())
    if sxx <= 0:
        return 0.0, float(ym), 0.0
    slope = float(((x - xm) * (y - ym)).sum() / sxx)
    icept = float(ym - slope * xm)
    pred = slope * x + icept
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - ym) ** 2).sum())
    return slope, icept, (1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0


# ------------------------------------------------------------------ gates ---


def s1_attribution() -> dict:
    """S1 — rule 19 [R-ONE-MECH]: everything forcing ST_GAS, from committed D-2."""
    with open(KEEPER / "legitimacy_diagnostics.json") as fh:
        diag = json.load(fh)
    rows = [r for r in diag["diagnostics"]["D2"]["rows"] if r["class"] == "ST_GAS"]
    by_year: dict[str, dict] = {}
    for r in rows:
        y = str(r["year"])
        blk = by_year.setdefault(y, {"mechanisms": {}, "d2_class_total_twh": None})
        blk["mechanisms"][r["mechanism"]] = {
            "forced_twh": r["forced_twh"],
            "share_of_class": r["share_of_class"],
        }
        blk["d2_class_total_twh"] = r["class_total_twh"]
    for y, blk in by_year.items():
        blk["total_forced_twh"] = round(
            sum(m["forced_twh"] for m in blk["mechanisms"].values()), 4
        )
        blk["total_forced_share_d2_basis"] = round(
            sum(m["share_of_class"] for m in blk["mechanisms"].values()), 4
        )
    return {
        "rows": rows,
        "by_year": by_year,
        "mechanisms": sorted({r["mechanism"] for r in rows}),
        "note": (
            "D-2's class_total_twh is the LP dispatch frame summed over rows "
            "labelled ST_GAS; the P1 class_hourly sidecar is a different basis. "
            "Both are reported; shares on the D-2 basis are the committed ones."
        ),
    }


def s2_price_conditional(
    model: np.ndarray, meas_anch: np.ndarray, imh: np.ndarray
) -> dict:
    """S2 — THE STOP CONDITION: is the deficit price-conditional?"""
    order = np.argsort(imh, kind="mergesort")
    dec = np.zeros(len(imh), dtype=int)
    dec[order] = np.minimum(
        (np.arange(len(imh)) * N_DECILES) // len(imh), N_DECILES - 1
    )
    rows = []
    for d in range(N_DECILES):
        sel = dec == d
        rows.append(
            {
                "decile": d,
                "n": int(sel.sum()),
                "imh_mean": round(float(imh[sel].mean()), 3),
                "model_mw": round(float(model[sel].mean()), 1),
                "measured_mw": round(float(meas_anch[sel].mean()), 1),
                "deficit_mw": round(float((model[sel] - meas_anch[sel]).mean()), 1),
            }
        )
    imh_mid = np.array([r["imh_mean"] for r in rows])
    mod = np.array([r["model_mw"] for r in rows])
    mea = np.array([r["measured_mw"] for r in rows])
    dfc = np.array([r["deficit_mw"] for r in rows])
    t_model, t_meas = t50(imh_mid, mod), t50(imh_mid, mea)
    spread = float(dfc.max() - dfc.min())
    mean_abs = float(np.abs(dfc).mean())
    return {
        "deciles": rows,
        "t50_model": t_model,
        "t50_measured": t_meas,
        "t50_model_right_of_measured": (
            bool(t_model > t_meas) if (t_model is not None and t_meas is not None)
            else None
        ),
        "deficit_spread_mw": round(spread, 1),
        "deficit_mean_abs_mw": round(mean_abs, 1),
        "spread_frac": round(spread / mean_abs, 3) if mean_abs > 0 else None,
        "spread_passes": bool(mean_abs > 0 and spread / mean_abs >= S2_SPREAD_FRAC),
        "spearman_decile_vs_deficit": round(spearman(np.arange(N_DECILES), dfc), 3),
    }


def s3_capacity(
    model: np.ndarray, meas_raw: np.ndarray, bench_twh: float, nameplate: float
) -> dict:
    """S3 — capacity or conduct?"""
    req_cf = bench_twh * 1e6 / (nameplate * 8760.0)
    return {
        "model_nameplate_mw": round(nameplate, 1),
        "benchmark_twh": round(bench_twh, 4),
        "required_annual_cf": round(req_cf, 4),
        "model_annual_cf": round(float(model.sum()) / (nameplate * 8760.0), 4),
        "model_max_mw": round(float(model.max()), 1),
        "model_p95_mw": round(float(np.percentile(model, 95)), 1),
        "model_peak_util_of_nameplate": round(float(model.max()) / nameplate, 4),
        "measured_max_mw": round(float(meas_raw.max()), 1),
        "measured_p95_mw": round(float(np.percentile(meas_raw, 95)), 1),
        "measured_peak_util_of_nameplate": round(float(meas_raw.max()) / nameplate, 4),
        "headroom_at_model_peak_mw": round(nameplate - float(model.max()), 1),
    }


def s4_start_conduct(
    d: pd.DataFrame, chpset: set[int], model: np.ndarray, meas_raw: np.ndarray
) -> dict:
    """S4 — measured NYISO ST_GAS start conduct, and the model's class analogue."""
    sel = class_mask(d, "ST_GAS", chpset)
    sub = d.loc[sel, ["_fid", "unitId", "_h", "grossLoad"]].copy()
    sub["_uid"] = sub["_fid"].astype(str) + ":" + sub["unitId"].astype(str)
    per_unit = []
    for uid, grp in sub.groupby("_uid"):
        ser = (
            grp.groupby("_h")["grossLoad"]
            .sum()
            .reindex(range(8760))
            .fillna(0.0)
            .to_numpy(dtype=float)
        )
        on = ser > ON_MW
        if not on.any():
            continue
        on_runs = runs_of(on)
        off_runs = runs_of(~on)
        per_unit.append(
            {
                "unit": uid,
                "on_share": round(float(on.mean()), 4),
                "starts": len(on_runs),
                "run_median_h": float(np.median(on_runs)),
                "run_mean_h": round(float(np.mean(on_runs)), 1),
                "run_p90_h": round(float(np.percentile(on_runs, 90)), 1),
                "off_median_h": float(np.median(off_runs)) if off_runs else None,
            }
        )
    per_unit.sort(key=lambda r: -r["on_share"])
    med_runs = [r["run_median_h"] for r in per_unit]
    starts = [r["starts"] for r in per_unit]
    # Class-aggregate on/off — the one direction-safe model/measured comparison.
    mod_on, mea_on = model > ON_MW, meas_raw > ON_MW
    mod_runs, mea_runs = runs_of(mod_on), runs_of(mea_on)
    in_band = [
        r for r in per_unit if ST_GAS_MIN_RUN_H[0] <= r["run_median_h"]
    ]
    return {
        "n_units": len(per_unit),
        "per_unit": per_unit,
        "unit_run_median_of_medians_h": float(np.median(med_runs)) if med_runs else None,
        "unit_starts_median": float(np.median(starts)) if starts else None,
        "unit_starts_total": int(sum(starts)),
        "units_median_run_ge_24h": len(in_band),
        "units_median_run_ge_24h_share": (
            round(len(in_band) / len(per_unit), 3) if per_unit else None
        ),
        "class_aggregate": {
            "model_on_share": round(float(mod_on.mean()), 4),
            "measured_on_share": round(float(mea_on.mean()), 4),
            "model_starts": len(mod_runs),
            "measured_starts": len(mea_runs),
            "model_run_median_h": float(np.median(mod_runs)) if mod_runs else None,
            "measured_run_median_h": float(np.median(mea_runs)) if mea_runs else None,
            "model_cycles_more": (
                bool(len(mod_runs) > len(mea_runs)) if mea_runs else None
            ),
        },
        "constants_checked": {
            "min_run_hours": list(ST_GAS_MIN_RUN_H),
            "min_down_hours": list(ST_GAS_MIN_DOWN_H),
            "startup_per_mw": list(ST_GAS_STARTUP_PER_MW),
        },
    }


def s5_direction(s4: dict, gas_mean: float) -> dict:
    """S5 — the code-proven direction of ``gas_st_startup_cost`` on ST_GAS.

    ``compute_monthly_markup`` returns ``startup / max(avg_run, 1.0) >= 0`` and
    ``run_energy_solve`` forms ``mc_bid = mc_base + markup``, P1-only. Raising a
    generator's own bid cost in a pure LP weakly decreases its dispatch, and P0
    (hence every injected ``min_gen`` floor) is untouched. So the mechanism can
    only lower ST_GAS output.
    """
    agg = s4["class_aggregate"]
    run = agg["model_run_median_h"] or 1.0
    sized = {
        f"startup_{int(s)}_per_mw": round(s / max(run, 1.0), 3)
        for s in ST_GAS_STARTUP_PER_MW
    }
    # A representative ST_GAS marginal cost for scale: heat rate ~10.9 (the NY
    # steam class) at the year's mean Transco Z6, VOM excluded.
    mc_ref = 10.9 * gas_mean
    return {
        "markup_is_nonnegative": True,
        "applies_to": "P1 bid cost only (mc_bid = mc_base + markup); P0 unchanged",
        "floors_unchanged": True,
        "effect_on_st_gas_output": "weakly DECREASES",
        "model_class_run_median_h": run,
        "markup_usd_per_mwh_at_class_run": sized,
        "reference_st_gas_mc_usd_per_mwh": round(mc_ref, 2),
        "markup_share_of_mc": {
            k: (round(v / mc_ref, 4) if mc_ref > 0 else None)
            for k, v in sized.items()
        },
        "direction_admissible": False,
    }


def s6_monthly_gas(
    model: np.ndarray, meas_anch: np.ndarray, gas: np.ndarray, mon: np.ndarray
) -> list[dict]:
    """S6 — monthly ST_GAS relative error against that month's gas price."""
    out = []
    for m in range(1, 13):
        sel = mon == m
        mod = float(model[sel].sum())
        mea = float(meas_anch[sel].sum())
        out.append(
            {
                "month": m,
                "gas_usd_mmbtu": round(float(gas[sel].mean()), 3),
                "model_gwh": round(mod / 1e3, 1),
                "measured_gwh": round(mea / 1e3, 1),
                "rel_error": round((mod - mea) / mea, 4) if mea > 0 else None,
            }
        )
    return out



# ------------------------------------------- post-hoc, after the S2 failure --
# S7-S10 are NOT pre-registered gates. S2 failed (the deficit is not a
# year-invariant price-conditional dropout: the sign flips), so these locate
# what the object actually is. They are reported IN ADDITION to the registered
# gates, never in place of them -- the nyiso-171 A5b discipline.


def s7_population(chpset: set[int]) -> dict:
    """S7 — is the model's ST_GAS population the measured one?

    A missing-plant input defect would make every conduct statistic meaningless,
    so it is checked before anything is concluded from the deficit.
    """
    tranche = pd.read_csv(TRANCHES)
    model_plants = set(
        tranche.loc[tranche["plant_group"] == "ST_GAS", "plant_code"].astype(int)
    )
    out: dict = {"model_plants": sorted(model_plants), "by_year": {}}
    for year in YEARS:
        d = campd_frame(year)
        sel = class_mask(d, "ST_GAS", chpset)
        g = d.loc[sel].groupby(d.loc[sel, "_fid"])["grossLoad"].sum() / 1e6
        off = {int(k): round(float(v), 4) for k, v in g.items() if int(k) not in model_plants}
        out["by_year"][str(year)] = {
            "campd_plants": int(len(g)),
            "campd_total_twh": round(float(g.sum()), 4),
            "off_model_plants": off,
            "off_model_twh": round(float(sum(off.values())), 4),
            "off_model_share": (
                round(float(sum(off.values()) / g.sum()), 5) if g.sum() > 0 else None
            ),
        }
    return out


def s8_composition_trend(chpset: set[int]) -> dict:
    """S8 — the year-over-year composition trend, model vs measured.

    The S2 failure says the object is not within-year price response. This asks
    whether it is a BETWEEN-year response: does the market lean progressively on
    gas steam while the model leans off it?
    """
    classes = list(UNIT_KIND)
    meas: dict[str, dict[str, float]] = {}
    mod: dict[str, dict[str, float]] = {}
    for year in YEARS:
        d = campd_frame(year)
        meas[str(year)] = {
            k: round(float(measured_hourly(d, k, chpset).sum()) / 1e6, 4)
            for k in classes
        }
        mod[str(year)] = {
            k: round(float(model_hourly(year, k).sum()) / 1e6, 4) for k in classes
        }
    def share(tbl: dict[str, dict[str, float]], y: str) -> float:
        tot = sum(tbl[y].values())
        return round(tbl[y]["ST_GAS"] / tot, 4) if tot > 0 else 0.0
    return {
        "measured_twh": meas,
        "model_twh": mod,
        "measured_total_gas_twh": {y: round(sum(v.values()), 4) for y, v in meas.items()},
        "model_total_gas_twh": {y: round(sum(v.values()), 4) for y, v in mod.items()},
        "measured_st_gas_share_of_gas": {y: share(meas, y) for y in meas},
        "model_st_gas_share_of_gas": {y: share(mod, y) for y in mod},
        "measured_st_gas_growth_23_25": round(
            meas["2025"]["ST_GAS"] / meas["2023"]["ST_GAS"] - 1, 4
        ),
        "model_st_gas_growth_23_25": round(
            mod["2025"]["ST_GAS"] / mod["2023"]["ST_GAS"] - 1, 4
        ),
    }


def s9_zonal(chpset: set[int]) -> dict:
    """S9 — where the measured ST_GAS growth sits, by model zone.

    Model-side zonal dispatch is NOT observable: ``class_hourly`` carries no zone
    column, so only the measured side is split here. That asymmetry is the
    finding's instrument limit, stated rather than worked around.
    """
    from market_sim.data.zone_assignment import assign_zone

    tranche = pd.read_csv(TRANCHES)
    st = tranche[tranche["plant_group"] == "ST_GAS"]
    zone_of = {int(r["plant_code"]): assign_zone(int(r["plant_code"]), "NYISO")
               for _, r in st.iterrows()}
    nameplate_by_zone: dict[str, float] = {}
    for _, r in st.iterrows():
        z = zone_of[int(r["plant_code"])]
        nameplate_by_zone[z] = nameplate_by_zone.get(z, 0.0) + float(r["nameplate_mw"])
    by_year: dict[str, dict[str, float]] = {}
    for year in YEARS:
        d = campd_frame(year)
        sel = class_mask(d, "ST_GAS", chpset)
        g = d.loc[sel].groupby(d.loc[sel, "_fid"])["grossLoad"].sum() / 1e6
        acc: dict[str, float] = {}
        for fid, twh in g.items():
            z = zone_of.get(int(fid), "OFF_MODEL")
            acc[z] = acc.get(z, 0.0) + float(twh)
        by_year[str(year)] = {k: round(v, 4) for k, v in sorted(acc.items())}
    growth = {
        z: round(by_year["2025"].get(z, 0.0) - by_year["2023"].get(z, 0.0), 4)
        for z in set(by_year["2023"]) | set(by_year["2025"])
    }
    tot = sum(v for v in growth.values())
    return {
        "zone_of_plant": {str(k): v for k, v in sorted(zone_of.items())},
        "nameplate_mw_by_zone": {k: round(v, 1) for k, v in sorted(nameplate_by_zone.items())},
        "measured_twh_by_zone": by_year,
        "growth_2023_to_2025_twh": dict(sorted(growth.items(), key=lambda kv: -kv[1])),
        "growth_share_by_zone": (
            {k: round(v / tot, 4) for k, v in sorted(growth.items(), key=lambda kv: -kv[1])}
            if tot
            else None
        ),
        "instrument_limit": (
            "measured side only — class_hourly carries no zone column, so the "
            "model's zonal ST_GAS dispatch is not observable without a re-solve"
        ),
    }


def s10_cc_availability(chpset: set[int]) -> dict:
    """S10 — a ONE-SIDED bound on the model's CC availability.

    The measured CC fleet's maximum output WITHIN a month is a strict lower
    bound on what that fleet could have produced that month, so any hour in
    which the model's CC output exceeds it is a proven over-statement of CC
    availability. The bound is conservative twice over: CAMPD ``grossLoad`` is
    gross while the model's ``class_hourly`` is on the delivered basis (gross >=
    net), and a monthly maximum is the loosest within-month bound available.
    """
    mon = month_of_hour()
    cc = ["CC_CHP", "CC_REGULAR"]
    out: dict[str, dict] = {}
    for year in YEARS:
        d = campd_frame(year)
        mo = sum(model_hourly(year, k) for k in cc)
        me = sum(measured_hourly(d, k, chpset) for k in cc)
        per_month, total = {}, 0
        for m in range(1, 13):
            sel = mon == m
            ex = int((mo[sel] > me[sel].max()).sum())
            per_month[str(m)] = ex
            total += ex
        mo_st = model_hourly(year, "ST_GAS")
        me_st = measured_hourly(d, "ST_GAS", chpset)
        st_total = sum(
            int((mo_st[mon == m] > me_st[mon == m].max()).sum()) for m in range(1, 13)
        )
        out[str(year)] = {
            "cc_hours_above_measured_monthly_max": total,
            "cc_share_of_year": round(total / 8760, 4),
            "cc_per_month": per_month,
            "cc_model_mean_mw": round(float(mo.mean()), 1),
            "cc_measured_mean_mw": round(float(me.mean()), 1),
            "cc_mean_gap_mw": round(float(mo.mean() - me.mean()), 1),
            "cc_model_max_mw": round(float(mo.max()), 1),
            "cc_measured_max_mw": round(float(me.max()), 1),
            "cc_model_p95_mw": round(float(np.percentile(mo, 95)), 1),
            "cc_measured_p95_mw": round(float(np.percentile(me, 95)), 1),
            "st_gas_hours_above_measured_monthly_max": st_total,
        }
    return out


# ------------------------------------------------------------------- main ---


def main() -> None:
    chpset = chp_plants()
    tranche = pd.read_csv(TRANCHES)
    nameplate = float(
        tranche.loc[tranche["plant_group"] == "ST_GAS", "nameplate_mw"].sum()
    )
    mon = month_of_hour()
    result: dict = {
        "probe": "nyiso172_st_gas_level_deficit",
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "bundle": str(KEEPER.relative_to(REPO)),
        "years": list(YEARS),
        "S1_attribution": s1_attribution(),
        "by_year": {},
    }

    for year in YEARS:
        d = campd_frame(year)
        model = model_hourly(year, "ST_GAS")
        meas_raw = measured_hourly(d, "ST_GAS", chpset)
        bench = bench_classes(year)
        bench_twh = float(bench["ST_GAS"])
        campd_twh = float(meas_raw.sum()) / 1e6
        anchor = bench_twh / campd_twh if campd_twh > 0 else float("nan")
        meas_anch = meas_raw * anchor

        gas = hourly_gas(year)
        price = actual_price(year, "da")
        imh = price / np.maximum(gas, 1e-6)

        s2 = s2_price_conditional(model, meas_anch, imh)
        s3 = s3_capacity(model, meas_raw, bench_twh, nameplate)
        s4 = s4_start_conduct(d, chpset, model, meas_raw)
        s5 = s5_direction(s4, float(gas.mean()))
        s6 = s6_monthly_gas(model, meas_anch, gas, mon)

        result["by_year"][str(year)] = {
            "model_twh": round(float(model.sum()) / 1e6, 4),
            "benchmark_twh": round(bench_twh, 4),
            "campd_gross_twh": round(campd_twh, 4),
            "anchor": round(anchor, 4),
            "rel_error": round(
                (float(model.sum()) / 1e6 - bench_twh) / bench_twh, 4
            ),
            "gas_mean_usd_mmbtu": round(float(gas.mean()), 3),
            "S2_price_conditional": s2,
            "S3_capacity": s3,
            "S4_start_conduct": s4,
            "S5_direction": s5,
            "S6_monthly": s6,
        }

        print(f"\n=== {year}  ST_GAS {result['by_year'][str(year)]['rel_error']:+.2%}"
              f"  model {float(model.sum())/1e6:.4f} vs bench {bench_twh:.4f} TWh"
              f"  (anchor {anchor:.3f}, gas ${gas.mean():.2f})")
        print("  S2 deficit by implied-marginal-HR decile (model - anchored measured):")
        for r in s2["deciles"]:
            print(f"     d{r['decile']}  IMH {r['imh_mean']:>6.2f}  model {r['model_mw']:>7.1f}"
                  f"  meas {r['measured_mw']:>7.1f}  deficit {r['deficit_mw']:>+8.1f} MW")
        print(f"     T50 model {s2['t50_model']}  measured {s2['t50_measured']}"
              f"  model-right-of-measured {s2['t50_model_right_of_measured']}")
        print(f"     spread {s2['deficit_spread_mw']} MW = {s2['spread_frac']}x mean|deficit|"
              f"  (>= {S2_SPREAD_FRAC} ? {s2['spread_passes']})"
              f"   spearman {s2['spearman_decile_vs_deficit']}")
        print(f"  S3 nameplate {s3['model_nameplate_mw']} MW; required CF {s3['required_annual_cf']}"
              f" vs model CF {s3['model_annual_cf']}; model peak {s3['model_max_mw']} MW"
              f" ({s3['model_peak_util_of_nameplate']:.1%} of nameplate),"
              f" measured peak {s3['measured_max_mw']} MW")
        agg = s4["class_aggregate"]
        print(f"  S4 units {s4['n_units']}; median-of-median run {s4['unit_run_median_of_medians_h']} h;"
              f" median starts/unit {s4['unit_starts_median']};"
              f" units with median run >= 24h: {s4['units_median_run_ge_24h']}/{s4['n_units']}")
        print(f"     class aggregate: model on {agg['model_on_share']:.3f} starts {agg['model_starts']}"
              f" run-median {agg['model_run_median_h']} h  |  measured on {agg['measured_on_share']:.3f}"
              f" starts {agg['measured_starts']} run-median {agg['measured_run_median_h']} h"
              f"  -> model cycles more: {agg['model_cycles_more']}")
        print(f"  S5 markup would be {s5['markup_usd_per_mwh_at_class_run']} $/MWh"
              f" on a ${s5['reference_st_gas_mc_usd_per_mwh']} MC"
              f" -> effect on ST_GAS output: {s5['effect_on_st_gas_output']}")

    # S6 pooled across all 36 training months.
    xs, ys = [], []
    per_year_slope = {}
    for year in YEARS:
        rows = result["by_year"][str(year)]["S6_monthly"]
        gx = [r["gas_usd_mmbtu"] for r in rows if r["rel_error"] is not None]
        gy = [r["rel_error"] for r in rows if r["rel_error"] is not None]
        xs += gx
        ys += gy
        sl, ic, r2 = ols(np.array(gx), np.array(gy))
        per_year_slope[str(year)] = {
            "slope": round(sl, 4), "intercept": round(ic, 4), "r2": round(r2, 4)
        }
    sl, ic, r2 = ols(np.array(xs), np.array(ys))
    same_sign = len({np.sign(v["slope"]) for v in per_year_slope.values()}) == 1
    result["S6_pooled"] = {
        "n_months": len(xs),
        "slope_rel_error_per_usd_mmbtu": round(sl, 4),
        "intercept": round(ic, 4),
        "r2": round(r2, 4),
        "per_year": per_year_slope,
        "all_years_same_sign": bool(same_sign),
        "supported": bool(sl < 0 and same_sign),
    }

    # Verdict roll-up against the pre-registration.
    yrs = [result["by_year"][str(y)] for y in YEARS]
    s2_pass = all(
        v["S2_price_conditional"]["t50_model_right_of_measured"] is True
        and v["S2_price_conditional"]["spread_passes"]
        for v in yrs
    )
    s3_input_defect = any(
        v["S3_capacity"]["required_annual_cf"] >= 1.0
        or v["S3_capacity"]["model_max_mw"] >= v["S3_capacity"]["model_nameplate_mw"]
        for v in yrs
    )
    s4_arm = all(
        v["S4_start_conduct"]["class_aggregate"]["model_cycles_more"] is True
        and (v["S4_start_conduct"]["units_median_run_ge_24h_share"] or 0) >= 0.5
        for v in yrs
    )
    result["VERDICT"] = {
        "S2_price_conditional_all_years": bool(s2_pass),
        "S3_input_defect": bool(s3_input_defect),
        "S4_startup_cost_grounded": bool(s4_arm),
        "S5_direction_admissible": False,
        "S6_gas_tracking_supported": result["S6_pooled"]["supported"],
        "proceed_to_arm": bool(s2_pass and not s3_input_defect and s4_arm and False),
    }

    # Post-hoc, after the S2 failure (reported in addition to the gates).
    result["S7_population"] = s7_population(chpset)
    result["S8_composition_trend"] = s8_composition_trend(chpset)
    result["S9_zonal"] = s9_zonal(chpset)
    result["S10_cc_availability"] = s10_cc_availability(chpset)

    s7, s8, s9, s10 = (
        result["S7_population"], result["S8_composition_trend"],
        result["S9_zonal"], result["S10_cc_availability"],
    )
    print("\n=== POST-HOC (after the S2 failure) ===")
    print("  S7 population: off-model measured ST_GAS volume share by year:",
          {y: v["off_model_share"] for y, v in s7["by_year"].items()})
    print(f"  S8 measured ST_GAS {s8['measured_st_gas_growth_23_25']:+.1%} 2023->2025"
          f" vs model {s8['model_st_gas_growth_23_25']:+.1%}")
    print("     ST_GAS share of gas  measured", s8["measured_st_gas_share_of_gas"],
          " model", s8["model_st_gas_share_of_gas"])
    print("  S9 measured growth by zone (TWh):", s9["growth_2023_to_2025_twh"])
    print("  S10 model CC above measured within-month max:")
    for y, v in s10.items():
        print(f"     {y}: {v['cc_hours_above_measured_monthly_max']:>5} h"
              f" ({v['cc_share_of_year']:.2%});  CC mean gap {v['cc_mean_gap_mw']:+.0f} MW;"
              f" ST_GAS excess hours {v['st_gas_hours_above_measured_monthly_max']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1))
    print("\n  S6 pooled:", json.dumps(result["S6_pooled"], indent=1))
    print("\n  VERDICT", json.dumps(result["VERDICT"], indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
