#!/usr/bin/env python3
"""ERCOT-159 Phase 0: measure the slow-start-fossil ONLINE capability ceiling
and census where it would bind against the ercot158 keeper's own committed
sidecars — BEFORE any LP is built (the ERCOT-155/158 measure-first pattern).

Two phases, no solve, no LP, keeper untouched:

**Phase A (scan)** builds the measured hourly online-capability series from the
60-Day SCED Gen Resource corpus, per delivery year:

* delivery-2023: the full-year re-upload corpus ``data/raw/ercot/SCED/``
  (315 shards, all 365 delivery days — ERCOT-157), delivery-year filtered;
* delivery-2024/2025: the four committed sample-day extracts (ercot74/75/86),
  47 day-files, event/control never pooled downstream.

Per SCED interval it sums, over the **slow-start fossil** Resource Types
(combined cycle CCGT90/CCLE90, coal CLLIG/CLLIM, gas-steam GSREH/GSNONR/GSSUP
— the classes whose offline state ERCOT-155/158 adjudicated as the un-repriced
cushion) and separately over the **quick-start** types (SCGT90/SCLE90/RECIP/
DSL — the classes the keeper's fast-start pool already re-prices offline):
online HSL / HASL / Base Point and offline HSL, online/offline resource
counts, using the ERCOT-155 census's exact type/status taxonomy and CPT→CST
clock placement so the numbers reconcile with the committed
``ercot155_dispersion_census.json`` benchmarks. Hourly means land on the fixed
non-leap 8760 clock and are cached to
``results/calibration/_ercot159_sced_online_hourly_<year>.parquet``.

**Phase B (census)** reads the ercot158 keeper bundle's committed hourly
sidecars (rule 15: keepers carry ``class_hourly``/``system``/``reserve_family``
precisely so diagnostic sessions never replay the solve) and, for 2023,
measures where the model's slow-fossil energy + spinning-reserve point sits
against the measured online capability:

* raw margin: ``P_slow(t) + R_spin(t) − HSL_online_slow(t)`` — hours the
  keeper's dispatch exceeds what the real market had online (the phantom in
  use), cross-tabbed against the actual >$200/>$300 tail and the model-missed
  set;
* a first-cut CONDITIONAL ceiling (season × hour-block × net-load-decile cell
  p95 of the measured series, the rule-13 grain chartered for item 9) and the
  same census against it — the bistability check: a sound ceiling binds in the
  scarcity-adjacent evenings and ~never in ordinary hours (the ercot106/108
  in-LP envelope failure mode this mechanism must not reproduce).

Usage:
    .venv/bin/python scripts/probes/ercot159_capability_phase0.py --scan
    .venv/bin/python scripts/probes/ercot159_capability_phase0.py --census

Writes ``results/calibration/_ercot159_capability_phase0.json`` (census).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO / "scripts" / "data", REPO / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from derive_ercot_dam_cleared_share import _MONTH_START_HOUR  # noqa: E402
from derive_ercot_faststart_pool import _STD_TZ  # noqa: E402
from derive_ercot_sced_offer_wall import SCED_DIR  # noqa: E402

BUNDLE = REPO / "results/calibration/ercot158_poolarm_B"
HOURLY = BUNDLE / "hourly"
CORPUS_DIR = REPO / "data/raw/ercot/SCED"
CACHE_TPL = "results/calibration/_ercot159_sced_online_hourly_{year}.parquet"
OUT = REPO / "results/calibration/_ercot159_capability_phase0.json"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"

#: Slow-start fossil SCED Resource Types — the capped set. Combined cycle,
#: coal/lignite and gas steam: the classes whose OFFLINE state ERCOT-155
#: measured as the cushion and ERCOT-158 confirmed un-repriced (the CC offline
#: block). Same taxonomy family as ercot155_dispersion_census.SCED_THERMAL_TYPES
#: minus the quick-start types.
SLOW_TYPES = ("CCGT90", "CCLE90", "CLLIG", "CLLIM", "GSREH", "GSNONR", "GSSUP")

#: Quick-start SCED Resource Types — never capped by this mechanism: their
#: offline dispatchability is real (10-20 min starts) and their offline START
#: cost is already priced by the keeper's fast-start pool (ERCOT-158, cell K).
QUICK_TYPES = ("SCGT90", "SCLE90", "RECIP", "DSL")

#: Nuclear — in the fast-tier eligibility (RESERVE_FUEL_TYPES includes
#: "nuclear", QUICK_START does not), so its P is on the fast-row LHS and its
#: online HSL must join the measured ceiling.
NUC_TYPES = ("NUC",)

#: Online, commercially-offering telemetry states (Nodal Protocols §3.9.1) —
#: the ERCOT-154/155 population rule, verbatim.
ONLINE_STATES = ("ON", "ONREG", "ONFFRRRS", "FRRSUP", "ONRGL", "ONOS")

_READ_COLS = [
    "SCED Time Stamp",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "HSL",
    "HASL",
    "Base Point",
]

#: Model class labels (class_hourly ``klass``) that map onto SLOW_TYPES.
#: CC_REGULAR+CC_CHP ↔ CCGT90/CCLE90; COAL_PRB+COAL_LIGNITE ↔ CLLIG/CLLIM;
#: ST_GAS+ST_CHP ↔ GSREH/GSNONR/GSSUP.
MODEL_SLOW_CLASSES = ("CC_REGULAR", "CC_CHP", "COAL_PRB", "COAL_LIGNITE", "ST_GAS", "ST_CHP")

#: Spinning (online-held) reserve families on the keeper — RegUp/RRS/ECRS.
#: NonSpin is reported separately: its award can sit on offline quick-starts
#: (RTOFFCAP territory), outside the online-capability object.
SPIN_FAMILIES = ("RegUp_withheld", "RRS_withheld", "ECRS_withheld")

MONTH_TO_SEASON = np.array([0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 0])  # DJF/MAM/JJA(Sep)/ON
SEASON_NAMES = ("DJF", "MAM", "JJAS", "ON")
HOUR_BLOCKS = ((0, 5), (6, 9), (10, 13), (14, 16), (17, 21), (22, 23))
CEIL_PCTL = 95.0  # envelope statistic, first cut


def _prepare(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """CPT → fixed-CST clock + hour-of-year, ERCOT-155 pattern verbatim."""
    ts = pd.to_datetime(df["SCED Time Stamp"])
    cst = ts.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    yr = cst.dt.year.to_numpy()
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    ok = (yr == year) & ~((mo == 2) & (dy == 29))
    out = df.loc[np.asarray(ok)].copy()
    out["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    out["stat"] = out["Telemetered Resource Status"].astype(str).str.strip()
    out["_ts"] = ts.to_numpy()[np.asarray(ok)]
    return out


def _interval_sums(df: pd.DataFrame) -> pd.DataFrame:
    """Per-SCED-interval online/offline capability sums for slow + quick sets."""
    rt = df["Resource Type"].astype(str).str.strip()
    on = df["stat"].isin(ONLINE_STATES)
    frames = {}
    for tag, types in (("slow", SLOW_TYPES), ("quick", QUICK_TYPES), ("nuc", NUC_TYPES)):
        m = rt.isin(types)
        g_on = df[m & on].groupby("_ts")
        g_off = df[m & ~on].groupby("_ts")
        f = pd.DataFrame(
            {
                f"hsl_on_{tag}": g_on["HSL"].sum(),
                f"hasl_on_{tag}": g_on["HASL"].sum(),
                f"bp_on_{tag}": g_on["Base Point"].sum(),
                f"n_on_{tag}": g_on["Resource Name"].nunique(),
            }
        )
        f[f"hsl_off_{tag}"] = g_off["HSL"].sum()
        f[f"n_off_{tag}"] = g_off["Resource Name"].nunique()
        frames[tag] = f
    out = frames["slow"].join(frames["quick"], how="outer").join(frames["nuc"], how="outer")
    hoy = df.groupby("_ts")["hoy"].first()
    out["hoy"] = hoy
    return out.reset_index(drop=True)


def scan_year(year: int) -> pd.DataFrame:
    """Build the hourly measured series for one delivery year and cache it."""
    if year == 2023:
        paths = sorted(CORPUS_DIR.glob("*.parquet"))
    else:
        paths = sorted(
            SCED_DIR.glob(
                f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"
            )
        )
    if not paths:
        raise SystemExit(f"no SCED source files for {year}")
    chunks = []
    for i, p in enumerate(paths):
        df = pd.read_parquet(p, columns=_READ_COLS)
        rt = df["Resource Type"].astype(str).str.strip()
        df = df[rt.isin(SLOW_TYPES + QUICK_TYPES + NUC_TYPES)]
        for c in ("HSL", "HASL", "Base Point"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = _prepare(df, year)
        if df.empty:
            continue
        chunks.append(_interval_sums(df))
        if (i + 1) % 40 == 0:
            print(f"  {year}: {i + 1}/{len(paths)} shards", flush=True)
    iv = pd.concat(chunks, ignore_index=True)
    hourly = iv.groupby("hoy").mean(numeric_only=True)
    hourly["n_intervals"] = iv.groupby("hoy").size()
    hourly = hourly.reindex(range(8760))
    out = REPO / CACHE_TPL.format(year=year)
    hourly.reset_index(names="hoy").to_parquet(out, index=False)
    cov = int(hourly["hsl_on_slow"].notna().sum())
    print(f"{year}: {cov}/8760 hours covered -> {out}")
    return hourly


def _load_sidecars(year: int) -> dict:
    ch = pd.read_parquet(HOURLY / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    piv = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum", observed=True)
    p_slow = piv.reindex(columns=list(MODEL_SLOW_CLASSES)).fillna(0.0).sum(axis=1)
    sysd = pd.read_parquet(HOURLY / f"system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"] if "pass" in sysd.columns else sysd
    demand = sysd.groupby("hour")["demand"].sum()
    price = sysd.groupby("hour")["price"].apply(
        lambda s: np.average(s)  # zone-mean; load-weighting needs zonal demand which is in the same frame
    )
    lw = sysd.assign(pd_=sysd["price"] * sysd["demand"]).groupby("hour").agg(
        pd_=("pd_", "sum"), d=("demand", "sum")
    )
    price_lw = lw["pd_"] / lw["d"]
    rf = pd.read_parquet(HOURLY / f"reserve_family_{year}.parquet")
    rf = rf[rf["pass"] == "P1"] if "pass" in rf.columns else rf
    held = rf.pivot_table(index="hour", columns="family", values="held_mw", aggfunc="sum", observed=True)
    r_spin = held.reindex(columns=list(SPIN_FAMILIES)).fillna(0.0).sum(axis=1)
    r_nonspin = held.get("NonSpin", pd.Series(0.0, index=r_spin.index))
    nl = demand - piv.get("wind", 0.0) - piv.get("solar", 0.0)
    return {
        "p_slow": p_slow.to_numpy(dtype=float),
        "p_nuc": piv.get("nuclear", pd.Series(0.0, index=p_slow.index)).to_numpy(dtype=float),
        "demand": demand.to_numpy(dtype=float),
        "price_lw": price_lw.to_numpy(dtype=float),
        "r_spin": r_spin.to_numpy(dtype=float),
        "r_nonspin": r_nonspin.to_numpy(dtype=float),
        "net_load": nl.to_numpy(dtype=float),
    }


def _cells(net_load: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(season, hour_block, nl_decile) index arrays on the 8760 clock."""
    hoy = np.arange(8760)
    month = np.searchsorted(_MONTH_START_HOUR, hoy, side="right")  # 1..12
    season = MONTH_TO_SEASON[month - 1]
    hod = hoy % 24
    hb = np.zeros(8760, dtype=int)
    for b, (lo, hi) in enumerate(HOUR_BLOCKS):
        hb[(hod >= lo) & (hod <= hi)] = b
    edges = np.quantile(net_load, np.linspace(0, 1, 11)[1:-1])
    dec = np.searchsorted(edges, net_load, side="right")
    return season, hb, dec


def _tab(margin: np.ndarray, mask_sets: dict[str, np.ndarray]) -> dict:
    bind = margin > 0
    out = {
        "bind_hours": int(bind.sum()),
        "bind_margin_gw_p50": round(float(np.median(margin[bind]) / 1e3), 3) if bind.any() else None,
        "bind_margin_gw_max": round(float(margin[bind].max() / 1e3), 3) if bind.any() else None,
    }
    for name, m in mask_sets.items():
        out[f"bind_in_{name}"] = int((bind & m).sum())
        out[f"hours_{name}"] = int(m.sum())
    hod = np.arange(8760) % 24
    out["bind_by_hourblock"] = {
        f"h{lo}-{hi}": int((bind & (hod >= lo) & (hod <= hi)).sum()) for lo, hi in HOUR_BLOCKS
    }
    return out


def census(year: int = 2023) -> dict:
    cache = REPO / CACHE_TPL.format(year=year)
    if not cache.exists():
        raise SystemExit(f"run --scan first ({cache} missing)")
    meas = pd.read_parquet(cache).set_index("hoy")
    side = _load_sidecars(year)
    act = pd.read_parquet(ACTUAL_LMP)
    act = act[act["year"] == year].sort_values("hour")
    actual = act["rt"].to_numpy(dtype=float)[:8760]

    # Fast-tier LHS analogue: slow-fossil P + nuclear P + spinning reserve;
    # measured ceiling analogue: slow-fossil + nuclear online HSL.
    hsl_on = (
        meas["hsl_on_slow"].to_numpy(dtype=float)
        + meas["hsl_on_nuc"].fillna(0.0).to_numpy(dtype=float)
    )
    covered = ~np.isnan(hsl_on)
    point = side["p_slow"] + side["p_nuc"] + side["r_spin"]
    margin_raw = np.where(covered, point - hsl_on, -np.inf)

    model_p = side["price_lw"]
    sets = {
        "actual_gt200": actual > 200,
        "actual_gt300": actual > 300,
        # The ERCOT-158 Phase-0 split, re-derived on the keeper's own prices:
        # actual > $300 with model < $200 -> the 91 missed hours (2023).
        "missed_gt300": (actual > 300) & (model_p < 200),
        "ordinary_lt150": actual < 150,
    }

    # Quick-start online HEADROOM (HSL − BP): capability reality holds for
    # spinning products on online CTs — credited to the ceiling, since the LP's
    # fast-product R can only sit on slow+nuclear headroom while reality splits
    # its spin across slow AND online-quick units. Quick P itself never enters
    # (netted by BP).
    q_head = np.clip(
        meas["hsl_on_quick"].fillna(0.0).to_numpy(dtype=float)
        - meas["bp_on_quick"].fillna(0.0).to_numpy(dtype=float),
        0.0,
        None,
    )
    hsl_aug = hsl_on + q_head

    season, hb, dec = _cells(side["net_load"])

    def _cond(series: np.ndarray, key: np.ndarray, stat: str, n_floor: int = 0) -> np.ndarray:
        """Cell-conditional ceiling with optional small-cell merge into the
        next-lower net-load bin of the same (season, block)."""
        ceil = np.full(8760, np.nan)
        for k in np.unique(key[covered]):
            m = covered & (key == k)
            vals = series[m]
            if n_floor and vals.size < n_floor:
                d = int(k % 100)
                while vals.size < n_floor and d > 0:
                    d -= 1
                    m2 = covered & (key == (k // 100) * 100 + d)
                    vals = np.concatenate([vals, series[m2]])
            v = float(np.max(vals)) if stat == "max" else float(np.percentile(vals, float(stat)))
            ceil[key == k] = v
        return ceil

    # Extreme-style net-load axis: deciles below the top, the top decile split
    # at 2-percentile grain (the ercot43 lesson: the pooled decile-9 median
    # collapses the extreme tail where reality musters near-max capability).
    nl = side["net_load"]
    edges_lo = np.quantile(nl, np.linspace(0.1, 0.9, 9))
    edges_hi = np.quantile(nl, [0.92, 0.94, 0.96, 0.98])
    edges14 = np.concatenate([edges_lo, edges_hi])
    dec14 = np.searchsorted(edges14, nl, side="right")

    ev = (np.arange(8760) % 24 >= 17) & (np.arange(8760) % 24 <= 21)
    key10 = season * 1000 + hb * 100 + dec
    key14 = season * 1000 + hb * 100 + dec14
    res = {
        "year": year,
        "bundle": str(BUNDLE.name),
        "slow_types": list(SLOW_TYPES),
        "model_slow_classes": list(MODEL_SLOW_CLASSES),
        "spin_families": list(SPIN_FAMILIES),
        "coverage_hours": int(covered.sum()),
        "measured": {
            "hsl_on_slow_gw_mean": round(float(np.nanmean(hsl_on)) / 1e3, 3),
            "hsl_on_slow_gw_evening_mean": round(float(np.nanmean(hsl_on[ev])) / 1e3, 3),
            "hsl_off_slow_gw_evening_mean": round(
                float(np.nanmean(meas["hsl_off_slow"].to_numpy(dtype=float)[ev])) / 1e3, 3
            ),
            "bp_on_slow_gw_evening_mean": round(
                float(np.nanmean(meas["bp_on_slow"].to_numpy(dtype=float)[ev])) / 1e3, 3
            ),
        },
        "model": {
            "p_slow_gw_evening_mean": round(float(side["p_slow"][ev].mean()) / 1e3, 3),
            "r_spin_gw_evening_mean": round(float(side["r_spin"][ev].mean()) / 1e3, 3),
            "r_nonspin_gw_evening_mean": round(float(side["r_nonspin"][ev].mean()) / 1e3, 3),
        },
        "raw_ceiling": _tab(margin_raw, sets),
        "raw_ceiling_aug": _tab(np.where(covered, point - hsl_aug, -np.inf), sets),
        "variants": {},
    }
    # Weekday axis: 2023-01-01 was a Sunday; weekend commitment is genuinely
    # thinner (Mon=0.. so dow>=5 → Sat/Sun). Calendar-regenerable driver.
    dow = ((np.arange(8760) // 24) + 6) % 7  # Jan 1 2023 = Sunday = 6
    wknd = (dow >= 5).astype(int)
    key14w = key14 * 10 + wknd
    key10w = key10 * 10 + wknd

    for name, series, key, stat, nf in (
        ("p95_dec10", hsl_on, key10, "95", 0),
        ("aug_p95_dec10", hsl_aug, key10, "95", 0),
        ("aug_p98_dec10", hsl_aug, key10, "98", 0),
        ("aug_max_dec10", hsl_aug, key10, "max", 0),
        ("aug_max_dec14_nf24", hsl_aug, key14, "max", 24),
        ("aug_p98_dec14_nf24", hsl_aug, key14, "98", 24),
        ("max_dec14_nf24", hsl_on, key14, "max", 24),
        ("aug_max_dec14", hsl_aug, key14, "max", 0),
        ("aug_max_dec14_wk", hsl_aug, key14w, "max", 0),
        ("aug_max_dec10_wk", hsl_aug, key10w, "max", 0),
        ("aug_p98_dec14_wk", hsl_aug, key14w, "98", 0),
    ):
        ceil = _cond(series, key, stat, nf)
        margin = np.where(~np.isnan(ceil), point - ceil, -np.inf)
        t = _tab(margin, sets)
        # Bind-depth anatomy at the missed tail vs ordinary binds — depth into
        # the reserve ladder predicts the formed price.
        mm = margin[sets["missed_gt300"] & (margin > 0)]
        oo = margin[sets["ordinary_lt150"] & (margin > 0)]
        t["missed_bind_depth_gw"] = {
            "p50": round(float(np.median(mm)) / 1e3, 3) if mm.size else None,
            "p90": round(float(np.percentile(mm, 90)) / 1e3, 3) if mm.size else None,
        }
        t["ordinary_bind_depth_gw"] = {
            "p50": round(float(np.median(oo)) / 1e3, 3) if oo.size else None,
            "p90": round(float(np.percentile(oo, 90)) / 1e3, 3) if oo.size else None,
        }
        res["variants"][name] = t
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "cell_stats"}, indent=1))
    print(f"-> {OUT}")
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scan", action="store_true", help="build measured hourly series caches")
    ap.add_argument("--census", action="store_true", help="census vs keeper sidecars (2023)")
    ap.add_argument("--years", type=int, nargs="*", default=[2023, 2024, 2025])
    a = ap.parse_args(argv)
    if a.scan:
        for y in a.years:
            scan_year(y)
    if a.census:
        census(2023)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
