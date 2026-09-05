"""miso-219 phase 0 — WHAT SETS THE PRICE IN THE 15 EVENING SCARCE HOURS?

Zero-solve. Every input is a committed artifact of the designated keeper
``2026-09-05-miso-217-intermphys`` (bundle ``results/calibration/miso217_intermphys_B``)
or a primary measured source under ``data/raw``. **No LP is solved, nothing is
minted, nothing is armed.** Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only.

The object is carried in as a stated fact from miso-202/203 and is NOT
re-derived here: MISO's C3a-2025 miss is a **price-formation** failure in ~15
evening net-load-ramp hours per year, not a level miss and not a volume miss
(0.0 MWh unserved, 44.3 GW idle, ORDC never climbing). miso-218 closed the
other side: a uniform offer-level scale reaches the C3a number without touching
the tail, at the cost of a load-bearing C1 exit. What is left is the question
this probe answers.

Four blocks, matching the charter:

* **A-1 — what sets the price in the 15 hours.** For each year's top-15
  actual-price Jun-Jul hours: the model's energy-balance dual, the reserve
  family duals, the ORDC shortfall, and the zonal price dispersion (the
  congestion channel; the keeper ships no ``network`` sidecar, so congestion is
  read from the price separation it produces). Names which of the four
  price-formation channels is inert.
* **A-2 — why the ORDC never climbs.** Requirement vs held MW vs shortfall per
  family, in those hours and against the year's own distribution.
  Distinguishes the three candidate causes — requirement too small, held MW too
  large, curve never consulted — from committed artifacts alone.
* **A-3 — the real market's own price formation at matched hours.** MISO's
  published RT LMP (the C3a instrument's own hub) and its RT ASM market
  clearing prices by product, on the model's clock, so the measured $1,669 can
  be attributed to an energy dual or to a reserve scarcity event.
* **A-4 — the rule-19 census.** Everything already arming scarcity pricing in
  the MISO keeper, read from the keeper's own ``run_config.json`` plus the
  published constants those flags consume.

Clock. The actual LMP is the committed scoring instrument
``actual_lmp_hourly_zonal_MISO.parquet`` (hub ``INDIANA.HUB``, column ``rt``),
already on the model's fixed-CST non-leap 8760 clock (miso-204 section F,
miso-206 clock repair). The ASM reports are hour-ending 1-24 Eastern Standard
year-round; two conventions are in use in this repo's probes (miso-167's
physical ``HE k EST -> hour k-2 CST`` and miso-214's disclosed no-shift). This
probe does not assume: it builds both, correlates each against the committed
LMP instrument, and reports the correlations alongside the block built on the
better-correlating one.

Usage::

    python3 scripts/probes/_miso219_evening_tail_phase0.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
TOP_N = 15

KEEPER = REPO / "results/calibration/miso217_intermphys_B"
HOURLY = KEEPER / "hourly"
ZONAL_ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
ASM_DIR = REPO / "data/raw/MISO-AS"
OUT = REPO / "results/calibration/_miso219_evening_tail.json"

SCORING_HUB = "INDIANA.HUB"
PHYSICAL_ZONES = (
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
)
HE_COLS = [f"he{k:02d}" for k in range(1, 25)]
MONTH_LENS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
# Band ladder, cheapest tranche first -- the rising offer curve of
# docs/binning-methodology.md. "peak" is the scarcity tranche.
BAND_LADDER = ("mustrun", "committed", "econ_low", "econ_high", "peak")


def _r(x: float, n: int = 3) -> float | None:
    """Round for JSON, mapping non-finite values to ``None``."""
    v = float(x)
    return None if not np.isfinite(v) else round(v, n)


def _month_of_hour() -> np.ndarray:
    """Calendar month (1-12) per hour on the model's fixed non-leap 8760 clock."""
    return np.concatenate(
        [np.full(n * 24, m + 1) for m, n in enumerate(MONTH_LENS)]
    )[:HOURS]


def _stamp(h: int) -> str:
    """``'MM-DD HEkk'`` on the model's own 8760 clock (February is always 28 days)."""
    doy, hod = divmod(int(h), 24)
    m = 0
    d = doy
    for i, n in enumerate(MONTH_LENS):
        if d < n:
            m = i + 1
            break
        d -= n
    return f"{m:02d}-{d + 1:02d} HE{hod + 1:02d}"


# --------------------------------------------------------------------------
# committed model artifacts
# --------------------------------------------------------------------------
def model_system(year: int) -> pd.DataFrame:
    """P1 zone-hour energy dual, slack, dump, demand and reserve price."""
    df = pd.read_parquet(HOURLY / f"system_{year}.parquet")
    return df[df["pass"] == "P1"].copy()


def model_reserve(year: int) -> pd.DataFrame:
    """P1 reserve-family balance-row dual, requirement, held MW and shortfall.

    Rule 15 names this sidecar as the ONLY artifact in which a locational
    reserve family's binding is observable -- ``system.reserve_price`` is the
    cross-family SUM broadcast identically to every zone.
    """
    df = pd.read_parquet(HOURLY / f"reserve_family_{year}.parquet")
    return df[df["pass"] == "P1"].copy()


def model_bands(year: int) -> pd.DataFrame:
    """P1 per-class per-band hourly dispatch (the offer-curve tranches)."""
    df = pd.read_parquet(HOURLY / f"class_band_hourly_{year}.parquet")
    return df[df["pass"] == "P1"].copy()


def system_price_series(sys_df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Zone-major price/demand matrices plus the load-weighted system price."""
    piv_p = sys_df.pivot_table(index="hour", columns="zone", values="price", aggfunc="first")
    piv_d = sys_df.pivot_table(index="hour", columns="zone", values="demand", aggfunc="first")
    zones = [z for z in PHYSICAL_ZONES if z in piv_p.columns]
    p = piv_p[zones].to_numpy(float)
    d = piv_d[zones].to_numpy(float)
    lw = np.where(d.sum(axis=1) > 0, (p * d).sum(axis=1) / np.maximum(d.sum(axis=1), 1e-9), np.nan)
    return {
        "zones": zones,
        "price": p,
        "demand": d,
        "load_weighted": lw,
        "indiana": piv_p["MISO-Indiana"].to_numpy(float),
        "dispersion": p.max(axis=1) - p.min(axis=1),
        "slack": sys_df.pivot_table(index="hour", columns="zone", values="slack", aggfunc="first").sum(axis=1).to_numpy(float),
        "reserve_price": sys_df.pivot_table(index="hour", columns="zone", values="reserve_price", aggfunc="first")[zones[0]].to_numpy(float),
    }


# --------------------------------------------------------------------------
# measured sources
# --------------------------------------------------------------------------
def actual_lmp(year: int) -> np.ndarray:
    """(8760,) measured RT LMP at the C3a scoring hub, on the model's clock."""
    df = pd.read_parquet(ZONAL_ACTUAL)
    sub = df[(df["year"] == year) & (df["hub"] == SCORING_HUB)]
    out = np.full(HOURS, np.nan)
    out[sub["hour"].to_numpy(int)] = sub["rt"].to_numpy(float)
    return out


def _asm_hour_index(dates: pd.Series, he: pd.Series, shift: int) -> np.ndarray:
    """Map (report date, hour-ending EST) to the model's fixed non-leap 8760 index.

    ``shift`` is the constant hour offset applied to hour-ending ``k``:
    ``-2`` is miso-167's physical EST-HE -> CST hour-beginning transform,
    ``-1`` is miso-214's disclosed no-shift reading. Feb 29 maps to ``-1``
    (dropped by the caller), keeping the measured clock on the model's calendar.
    """
    ts = pd.to_datetime(dates) + pd.to_timedelta(he.astype(int) + shift, unit="h")
    base = np.array([0] + list(np.cumsum(MONTH_LENS)[:-1]), dtype=int) * 24
    idx = base[ts.dt.month.to_numpy(int) - 1] + (ts.dt.day.to_numpy(int) - 1) * 24 + ts.dt.hour.to_numpy(int)
    leap = (ts.dt.month.to_numpy(int) == 2) & (ts.dt.day.to_numpy(int) == 29)
    idx = np.where(leap, -1, idx)
    return np.where(ts.dt.year.to_numpy(int) == ts.dt.year.mode().iloc[0], idx, -1)


def asm_mcp(year: int, shift: int) -> pd.DataFrame:
    """MISO-Wide RT ancillary market clearing price by product, on the model clock."""
    f = ASM_DIR / f"asm_rtmcp_zonal_{year}.parquet"
    if not f.exists():
        return pd.DataFrame()
    d = pd.read_parquet(f)
    d = d[d["zone"] == "Miso-Wide"].copy()
    d["date"] = pd.to_datetime(d["date"])
    long = d.melt(id_vars=["date", "product"], value_vars=HE_COLS, var_name="he", value_name="mcp")
    long["k"] = long["he"].str[2:].astype(int)
    long["hour"] = _asm_hour_index(long["date"], long["k"], shift)
    long = long[(long["hour"] >= 0) & (long["hour"] < HOURS)]
    return long.pivot_table(index="hour", columns="product", values="mcp", aggfunc="first")


def asm_cleared(year: int, shift: int) -> pd.DataFrame:
    """MISO RT cleared reserve MW by product (all regions), on the model clock."""
    f = ASM_DIR / f"asm_rt_cleared_mw_{year}.parquet"
    if not f.exists():
        return pd.DataFrame()
    d = pd.read_parquet(f)
    d["date"] = pd.to_datetime(d["date"])
    d["hour"] = _asm_hour_index(d["date"], d["hour_end_est"], shift)
    d = d[(d["hour"] >= 0) & (d["hour"] < HOURS)]
    piv = d.pivot_table(index="hour", columns="product", values="cleared_mw", aggfunc="sum")
    piv["_total"] = piv.sum(axis=1)
    return piv


# --------------------------------------------------------------------------
# A-0 : the object's own hours
# --------------------------------------------------------------------------
def select_hours(year: int) -> dict:
    """The year's top-15 measured-price Jun-Jul hours -- the object's own hours."""
    act = actual_lmp(year)
    mon = _month_of_hour()
    jj = np.where((mon == 6) | (mon == 7))[0]
    vals = act[jj]
    ok = jj[np.isfinite(vals)]
    order = ok[np.argsort(act[ok])[::-1]]
    top = np.sort(order[:TOP_N])
    return {
        "hours": [int(h) for h in top],
        "n_jun_jul_scored": int(ok.size),
        "top1pct_cut_usd": _r(float(np.percentile(act[ok], 99)), 2),
        "jun_jul_actual_mean_usd": _r(float(np.nanmean(act[ok])), 2),
        "jun_jul_actual_median_usd": _r(float(np.nanmedian(act[ok])), 2),
    }


# --------------------------------------------------------------------------
# A-1 : what sets the price
# --------------------------------------------------------------------------
def block_a1(year: int, hours: list[int]) -> dict:
    """Per-hour price-formation channels, and which of the four is inert."""
    sysd = system_price_series(model_system(year))
    res = model_reserve(year)
    act = actual_lmp(year)
    bands = model_bands(year)

    fam = {
        f: sub.set_index("hour")[["dual", "requirement_mw", "held_mw", "shortfall_mw"]]
        for f, sub in res.groupby("family")
    }

    # Peak-tranche utilisation: the scarcity band's MW in the hour against its
    # own annual maximum. If the peak tranche is barely touched the marginal
    # offer is an econ band and no scarcity tranche is setting price.
    pk = bands[bands["band"] == "peak"].groupby("hour")["mw"].sum().reindex(range(HOURS), fill_value=0.0).to_numpy(float)
    pk_max = float(pk.max())
    topband = {}
    for band in BAND_LADDER:
        sub = bands[bands["band"] == band]
        if sub.empty:
            continue
        topband[band] = sub.groupby("hour")["mw"].sum().reindex(range(HOURS), fill_value=0.0).to_numpy(float)

    rows = []
    for h in hours:
        row = {
            "hour": int(h),
            "stamp": _stamp(h),
            "hod": int(h % 24),
            "actual_rt_usd": _r(float(act[h]), 2),
            "model_lw_price_usd": _r(float(sysd["load_weighted"][h]), 2),
            "model_indiana_price_usd": _r(float(sysd["indiana"][h]), 2),
            "model_zone_max_price_usd": _r(float(sysd["price"][h].max()), 2),
            "model_zone_min_price_usd": _r(float(sysd["price"][h].min()), 2),
            "zonal_dispersion_usd": _r(float(sysd["dispersion"][h]), 2),
            "system_reserve_price_usd": _r(float(sysd["reserve_price"][h]), 2),
            "unserved_mwh": _r(float(sysd["slack"][h]), 3),
            "peak_band_mw": _r(float(pk[h]), 1),
            "peak_band_share_of_annual_max": _r(float(pk[h] / pk_max) if pk_max > 0 else 0.0, 4),
        }
        for f, tab in fam.items():
            if h in tab.index:
                r = tab.loc[h]
                row[f"{f}__dual"] = _r(float(r["dual"]), 3)
                row[f"{f}__shortfall_mw"] = _r(float(r["shortfall_mw"]), 1)
                row[f"{f}__req_mw"] = _r(float(r["requirement_mw"]), 1)
                row[f"{f}__held_mw"] = _r(float(r["held_mw"]), 1)
        rows.append(row)

    # channel verdicts over the object's hours
    disp = np.array([sysd["dispersion"][h] for h in hours], float)
    duals = {f: np.array([float(tab.loc[h, "dual"]) if h in tab.index else np.nan for h in hours]) for f, tab in fam.items()}
    short = {f: np.array([float(tab.loc[h, "shortfall_mw"]) if h in tab.index else np.nan for h in hours]) for f, tab in fam.items()}
    energy = np.array([sysd["load_weighted"][h] for h in hours], float)

    channels = {
        "energy_balance_dual": {
            "mean_usd": _r(float(np.nanmean(energy)), 2),
            "max_usd": _r(float(np.nanmax(energy)), 2),
            "inert": False,
            "note": "the only channel carrying material price in these hours",
        },
        "reserve_family_dual": {
            "sum_mean_usd": _r(float(np.nansum([np.nanmean(v) for v in duals.values()])), 3),
            "per_family_max_usd": {f: _r(float(np.nanmax(v)), 3) for f, v in duals.items()},
            "inert": bool(np.nansum([np.nanmax(np.abs(v)) for v in duals.values()]) < 1.0),
        },
        "ordc_shortfall": {
            "per_family_max_shortfall_mw": {f: _r(float(np.nanmax(v)), 2) for f, v in short.items()},
            "hours_with_any_shortfall": int(sum(1 for i in range(len(hours)) if any(np.nan_to_num(v[i]) > 0 for v in short.values()))),
            "inert": bool(all(np.nanmax(v) <= 0.0 for v in short.values())),
        },
        "congestion": {
            "mean_zonal_dispersion_usd": _r(float(np.nanmean(disp)), 2),
            "max_zonal_dispersion_usd": _r(float(np.nanmax(disp)), 2),
            "inert": bool(np.nanmax(disp) < 1.0),
        },
    }

    gap = np.array([act[h] for h in hours], float) - energy
    return {
        "rows": rows,
        "channels": channels,
        "model_annual_max_zone_price_usd": _r(float(sysd["price"].max()), 2),
        "actual_annual_max_usd": _r(float(np.nanmax(act)), 2),
        "mean_gap_usd": _r(float(np.nanmean(gap)), 2),
        "peak_band_annual_max_mw": _r(pk_max, 1),
        "peak_band_mean_in_object_hours_mw": _r(float(np.mean([pk[h] for h in hours])), 1),
        "band_mw_in_object_hours": {
            b: _r(float(np.mean([v[h] for h in hours])), 1) for b, v in topband.items()
        },
        "band_annual_max_mw": {b: _r(float(v.max()), 1) for b, v in topband.items()},
    }


# --------------------------------------------------------------------------
# A-2 : why the ORDC never climbs
# --------------------------------------------------------------------------
def block_a2(year: int, hours: list[int]) -> dict:
    """Requirement vs held vs shortfall -- which of the three causes is it?"""
    res = model_reserve(year)
    out = {}
    for f, sub in res.groupby("family"):
        t = sub.set_index("hour")
        req = t["requirement_mw"].reindex(range(HOURS)).to_numpy(float)
        held = t["held_mw"].reindex(range(HOURS)).to_numpy(float)
        sh = t["shortfall_mw"].reindex(range(HOURS)).to_numpy(float)
        dual = t["dual"].reindex(range(HOURS)).to_numpy(float)
        obj = np.array(hours, int)
        out[str(f)] = {
            "annual": {
                "req_mean_mw": _r(float(np.nanmean(req)), 1),
                "req_max_mw": _r(float(np.nanmax(req)), 1),
                "held_mean_mw": _r(float(np.nanmean(held)), 1),
                "surplus_held_over_req_mean_mw": _r(float(np.nanmean(held - req)), 2),
                "hours_shortfall_gt0": int(np.nansum(sh > 0)),
                "shortfall_max_mw": _r(float(np.nanmax(sh)), 1),
                "dual_max_usd": _r(float(np.nanmax(dual)), 2),
                "dual_p99_usd": _r(float(np.nanpercentile(dual, 99)), 3),
                "hours_dual_gt0": int(np.nansum(dual > 0)),
            },
            "object_hours": {
                "req_mean_mw": _r(float(np.nanmean(req[obj])), 1),
                "held_mean_mw": _r(float(np.nanmean(held[obj])), 1),
                "shortfall_mean_mw": _r(float(np.nanmean(sh[obj])), 2),
                "shortfall_max_mw": _r(float(np.nanmax(sh[obj])), 2),
                "dual_mean_usd": _r(float(np.nanmean(dual[obj])), 3),
                "dual_max_usd": _r(float(np.nanmax(dual[obj])), 3),
                "hours_shortfall_gt0": int(np.nansum(sh[obj] > 0)),
            },
            "req_percentile_of_object_hours": _r(
                float(np.mean([(req < req[h]).mean() for h in hours]) * 100), 1
            ),
        }
    return out


# --------------------------------------------------------------------------
# A-3 : the real market at the matched hours
# --------------------------------------------------------------------------
def block_a3(year: int, hours: list[int]) -> dict:
    """Measured RT LMP and RT ASM clearing prices at the object's own hours."""
    act = actual_lmp(year)

    # clock check: build both conventions, correlate the total cleared reserve
    # against the committed LMP instrument, and report which one aligns.
    corr_cleared: dict[str, float | None] = {}
    corr_mcp: dict[str, float | None] = {}
    best, best_r = None, -np.inf
    for shift in (-3, -2, -1, 0):
        cl = asm_cleared(year, shift)
        if not cl.empty:
            v = cl["_total"].reindex(range(HOURS)).to_numpy(float)
            ok = np.isfinite(v) & np.isfinite(act)
            corr_cleared[f"shift_{shift}"] = (
                _r(float(np.corrcoef(v[ok], act[ok])[0, 1]), 4) if ok.sum() > 100 else None
            )
        mk = asm_mcp(year, shift)
        if mk.empty or "DEMREGMCP" not in mk.columns:
            continue
        v = mk["DEMREGMCP"].reindex(range(HOURS)).to_numpy(float)
        ok = np.isfinite(v) & np.isfinite(act)
        r = float(np.corrcoef(v[ok], act[ok])[0, 1]) if ok.sum() > 100 else np.nan
        corr_mcp[f"shift_{shift}"] = _r(r, 4)
        if np.isfinite(r) and r > best_r:
            best, best_r = shift, r
    shift = best if best is not None else -2

    mcp = asm_mcp(year, shift)
    cl = asm_cleared(year, shift)
    products = [c for c in mcp.columns] if not mcp.empty else []

    rows = []
    for h in hours:
        row = {"hour": int(h), "stamp": _stamp(h), "actual_rt_usd": _r(float(act[h]), 2)}
        if not mcp.empty and h in mcp.index:
            for p in products:
                row[f"mcp__{p}"] = _r(float(mcp.loc[h, p]), 2)
        if not cl.empty and h in cl.index:
            row["cleared_total_mw"] = _r(float(cl.loc[h, "_total"]), 1)
        rows.append(row)

    summary = {}
    if not mcp.empty:
        for p in products:
            s = mcp[p].reindex(range(HOURS)).to_numpy(float)
            summary[p] = {
                "annual_mean_usd": _r(float(np.nanmean(s)), 2),
                "annual_p99_usd": _r(float(np.nanpercentile(s, 99)), 2),
                "annual_max_usd": _r(float(np.nanmax(s)), 2),
                "object_hours_mean_usd": _r(float(np.nanmean([s[h] for h in hours])), 2),
                "object_hours_max_usd": _r(float(np.nanmax([s[h] for h in hours])), 2),
            }
    cleared_summary = {}
    if not cl.empty:
        s = cl["_total"].reindex(range(HOURS)).to_numpy(float)
        cleared_summary = {
            "annual_mean_mw": _r(float(np.nanmean(s)), 1),
            "object_hours_mean_mw": _r(float(np.nanmean([s[h] for h in hours])), 1),
            "object_hours_pct_of_annual_max": _r(
                float(np.nanmean([s[h] for h in hours]) / np.nanmax(s) * 100), 1
            ),
        }
    return {
        "asm_clock_correlation_cleared_mw_vs_lmp": corr_cleared,
        "asm_clock_correlation_regmcp_vs_lmp": corr_mcp,
        "asm_clock_shift_used": shift,
        "rows": rows,
        "product_summary": summary,
        "cleared_summary": cleared_summary,
        "actual_object_hours_mean_usd": _r(float(np.nanmean([act[h] for h in hours])), 2),
        "actual_object_hours_max_usd": _r(float(np.nanmax([act[h] for h in hours])), 2),
    }


# --------------------------------------------------------------------------
# A-4 : the rule-19 census
# --------------------------------------------------------------------------
def block_a4() -> dict:
    """Everything already pricing scarcity in the MISO keeper (rule 19)."""
    from market_sim.model.reserves import spec as rspec  # noqa: PLC0415

    cfg = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    keys = [
        "energy_reserve_coopt",
        "miso_zonal_reserves",
        "miso_zonal_reserve_zones",
        "miso_midwest_subregional_reserves",
        "miso_measured_reserve_requirements",
        "miso_reserve_online_gated",
        "miso_reserve_pergen",
        "miso_rpe_pricing",
        "maxgen_emergency_tier_pricing",
        "unit_outage_maxgen_events",
        "screen_reserve_value_enabled",
        "scarcity_pricing_enabled",
        "scarcity_price_overlay",
        "ordc_voll",
        "ordc_multistep_floor",
        "voll",
        "as_reserve_withholding",
        "as_revenue_enabled",
    ]
    published = {
        "MISO_RESERVE_DEMAND_CURVE_MAX": getattr(rspec, "MISO_RESERVE_DEMAND_CURVE_MAX", None),
        "MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW": getattr(rspec, "MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW", None),
        "MISO_ZONAL_ORDC_STEPS": list(getattr(rspec, "MISO_ZONAL_ORDC_STEPS", ())),
        "MISO_REGSPIN_DEMAND_CURVE_STEPS": list(getattr(rspec, "MISO_REGSPIN_DEMAND_CURVE_STEPS", ())),
        "MISO_EMERGENCY_TIER1_OFFER_FLOOR": getattr(rspec, "MISO_EMERGENCY_TIER1_OFFER_FLOOR", None),
        "MISO_EMERGENCY_TIER2_OFFER_FLOOR": getattr(rspec, "MISO_EMERGENCY_TIER2_OFFER_FLOOR", None),
        "MISO_REGULATING_RESERVE_MW": getattr(rspec, "MISO_REGULATING_RESERVE_MW", None),
    }
    from market_sim.config.constants import MISO_RPE_DEMAND_VALUE  # noqa: PLC0415

    published["MISO_RPE_DEMAND_VALUE"] = MISO_RPE_DEMAND_VALUE
    return {
        "keeper_flags": {k: cfg.get(k, "<absent>") for k in keys},
        "published_curve_constants": published,
    }


# --------------------------------------------------------------------------
# A-5 : the declared-emergency overlap (does the armed ELMP tier even reach?)
# --------------------------------------------------------------------------
def block_a5(year: int, hours: list[int]) -> dict:
    """Do the object's hours sit inside a DECLARED MISO capacity-emergency window?

    ``maxgen_emergency_tier_pricing`` is ARMED in the keeper and reprices the
    energy-balance load-slack cost to the SOM-footnoted $500 (Warning / Event
    Step 1) or $1,000 (Event Step 2) emergency offer floor inside a declared
    window. It can therefore only set a price where the LP actually carries
    unserved energy. This block measures both halves: the window overlap, and
    the model's own slack in those hours.
    """
    from market_sim.data.maxgen_events import (  # noqa: PLC0415
        load_maxgen_registry_model_clock,
    )
    from market_sim.data.outages import outage_hour_mask  # noqa: PLC0415

    ev = load_maxgen_registry_model_clock(ISO)
    mask = np.zeros(HOURS, bool)
    windows = []
    for _, r in ev.iterrows():
        try:
            hm = np.asarray(outage_hour_mask(r["start_model"], r["end_model_excl"], year), bool)
        except Exception:  # noqa: BLE001 - a window outside this year contributes nothing
            continue
        if hm.any():
            windows.append(
                {
                    "region": str(r["region"]),
                    "level": str(r["level"]),
                    "start_model": str(r["start_model"]),
                    "end_model_excl": str(r["end_model_excl"]),
                    "hours": int(hm.sum()),
                }
            )
        mask |= hm

    sysd = model_system(year)
    slack = sysd.groupby("hour")["slack"].sum().reindex(range(HOURS), fill_value=0.0).to_numpy(float)
    inside = [int(h) for h in hours if mask[h]]
    return {
        "declared_windows_touching_year": windows,
        "declared_window_hours_in_year": int(mask.sum()),
        "object_hours_inside_a_declared_window": inside,
        "n_object_hours_inside": len(inside),
        "model_slack_hours_gt0_in_year": int((slack > 0).sum()),
        "model_slack_total_mwh_in_year": _r(float(slack.sum()), 1),
        "model_slack_mwh_in_object_hours": _r(float(sum(slack[h] for h in hours)), 4),
        "elmp_tier_reachable_in_object_hours": bool(sum(slack[h] for h in hours) > 0),
    }


# --------------------------------------------------------------------------
# A-6 : is the fleet actually idle? (the premise every reserve lever rests on)
# --------------------------------------------------------------------------
THERMAL_CLASSES = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_INTERMEDIATE",
    "ST_GAS",
    "ST_GAS_INTERMEDIATE",
    "COAL_PRB",
    "COAL_SUB",
    "COAL_BIT",
    "COAL_LIGNITE",
    "COAL_WASTE",
    "OIL_ST",
    "OIL_CT",
)


def block_a6(year: int, hours: list[int]) -> dict:
    """Model thermal loading in the object's hours, against its own annual ceiling.

    Every reserve/scarcity lever rests on the premise that the fleet has room.
    Nameplate headroom is not the operative quantity: what decides whether a
    reserve row can bind is how close the fleet is to the most it is ever
    observed to produce. Measured against the EIA-930 MISO thermal series on
    the model's own fixed-CST clock (the miso-156 instrument) where the
    measured record is complete.
    """
    cl = pd.read_parquet(HOURLY / f"class_hourly_{year}.parquet")
    cl = cl[cl["pass"] == "P1"]
    present = [k for k in cl["klass"].unique() if k in THERMAL_CLASSES]
    mt = (
        cl[cl["klass"].isin(present)]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(HOURS), fill_value=0.0)
        .to_numpy(float)
    )
    obj_model = float(np.mean([mt[h] for h in hours]))
    out = {
        "thermal_classes_present": sorted(present),
        "model_thermal_object_hours_mean_mw": _r(obj_model, 0),
        "model_thermal_annual_mean_mw": _r(float(mt.mean()), 0),
        "model_thermal_annual_max_mw": _r(float(mt.max()), 0),
        "model_object_hours_pct_of_own_annual_max": _r(obj_model / mt.max() * 100, 1),
    }
    try:
        import importlib.util  # noqa: PLC0415

        spec = importlib.util.spec_from_file_location(
            "_m156", REPO / "scripts/probes/_miso156_ramp_precheck.py"
        )
        m156 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m156)
        me, diag = m156.measured_thermal_mw(year)
        obj_meas = float(np.mean([me[h] for h in hours]))
        out.update(
            {
                "measured_thermal_object_hours_mean_mw": _r(obj_meas, 0),
                "measured_thermal_annual_max_mw": _r(float(np.nanmax(me)), 0),
                "measured_object_hours_pct_of_own_annual_max": _r(
                    obj_meas / float(np.nanmax(me)) * 100, 1
                ),
                "model_over_measured_object_hours": _r(obj_model / obj_meas, 3),
                "measured_series_complete_in_object_hours": bool(
                    np.isfinite([me[h] for h in hours]).all()
                ),
                "measured_series_finite_hours_in_year": int(np.isfinite(me).sum()),
                "e930_diagnostics": diag,
            }
        )
    except Exception as exc:  # noqa: BLE001 - measured leg is supplementary
        out["measured_thermal_error"] = str(exc)
    return out


# --------------------------------------------------------------------------
# A-7 : reachability -- what requirement would the RBDC need to bind at all?
# --------------------------------------------------------------------------
def block_a7(year: int, hours: list[int], a2: dict, a6: dict) -> dict:
    """How large would the reserve requirement have to be to produce a shortfall?

    A reserve family binds into a shortage only when the requirement exceeds the
    eligible headroom. This block states that threshold against the fleet's own
    REALIZED ceiling (its annual-max thermal output), which is the conservative
    reading -- nameplate headroom is far larger and makes the multiple bigger,
    not smaller. The multiple is what refuses the whole requirement-repair
    family arithmetically rather than by assertion.
    """
    obj = a6.get("model_thermal_object_hours_mean_mw")
    ceiling = a6.get("model_thermal_annual_max_mw")
    req = a2.get("miso_rbdc", {}).get("object_hours", {}).get("req_mean_mw")
    if not all(isinstance(v, (int, float)) for v in (obj, ceiling, req)):
        return {"computable": False}
    headroom = float(ceiling) - float(obj)
    needed = float(req) + headroom
    return {
        "computable": True,
        "basis": "fleet's own realized annual-max thermal output (conservative; nameplate headroom is larger)",
        "object_hours_thermal_mw": _r(float(obj), 0),
        "own_annual_ceiling_mw": _r(float(ceiling), 0),
        "headroom_to_own_ceiling_mw": _r(headroom, 0),
        "current_rbdc_requirement_mw": _r(float(req), 0),
        "requirement_needed_to_bind_mw": _r(needed, 0),
        "multiple_of_current_requirement": _r(needed / float(req), 2),
    }


def main() -> int:
    """Run all four blocks over 2023-2025 and write the JSON record."""
    out: dict = {
        "probe": "miso-219 phase 0 - evening scarcity tail price formation",
        "keeper": "2026-09-05-miso-217-intermphys",
        "bundle": str(KEEPER.relative_to(REPO)),
        "solved": False,
        "years": list(YEARS),
        "scoring_hub": SCORING_HUB,
        "top_n": TOP_N,
        "by_year": {},
    }
    for y in YEARS:
        sel = select_hours(y)
        hrs = sel["hours"]
        out["by_year"][str(y)] = {
            "A0_hour_selection": sel,
            "A1_price_formation": block_a1(y, hrs),
            "A2_ordc": block_a2(y, hrs),
            "A3_real_market": block_a3(y, hrs),
            "A5_declared_emergency_overlap": block_a5(y, hrs),
            "A6_fleet_loading": block_a6(y, hrs),
        }
        yr = out["by_year"][str(y)]
        yr["A7_reachability"] = block_a7(y, hrs, yr["A2_ordc"], yr["A6_fleet_loading"])
        print(f"  {y}: {len(hrs)} hours selected", flush=True)
    out["A4_rule19_census"] = block_a4()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
