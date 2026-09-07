"""nyiso-212 phase 0 (ZERO LP) — decompose the Cricket Valley 57185 over-ceiling
months into their construction terms.

Pre-registered in
``results/calibration/PREREG-nyiso212-cricket-valley-outage-window-construction.md``
(§3 identity, §4 identity checks, §5 predictions) BEFORE any plant-grain number
was read. For each month of 2023-2025, on the GROSS basis:

    X       = M - C2                       over-ceiling excess (meter minus LP ceiling)
    T_stat  = C1 - C2                      statistical overlay riding on the windows
    T_bench = M - sum_u E_u                facility-level meter minus unit-level sum
    T_in    = sum_u E_u,in                 energy "out" units reported inside their windows
    T_cap   = sum_u (E_u,out - s h_out,u)  running units vs their 362.3 MW LP share

with M the bench ``c_mon`` (facility-level CAMPD gross x 1.0 at this plant), C2
the LP ceiling from an on-recipe ``fleet_only`` rebuild of the keeper
``2026-09-06-nyiso-202-startup-aware`` (``scripts.lib.bundle_fleet``, the same
instrument nyiso-196/211 used), C1 the window-only ceiling from the loader's
``unit_outage_derate_factors``, and E_u the unit-level CAMPD gross of U001-U003.

Identity checks I1-I4 are computed and reported with their measured values;
their consequences are the PREREG's, not this script's.

Run::

    uv run python scripts/probes/nyiso212_overceiling_decomposition.py
"""

from __future__ import annotations

import gzip
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))

from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402
from scripts.lib.bundle_fleet import (  # noqa: E402
    bundle_gas_price,
    clear_fleet_caches,
    ensure_probe_path,
    full_run_year_kwargs,
)
from scripts.lib.outage_detect import detect_outages_eventbased  # noqa: E402

KEEPER_ID = "2026-09-06-nyiso-202-startup-aware"
BUNDLE = ROOT / "results/calibration/nyiso202_startup_aware"
PLANT = 57185
GROUP = "CC_REGULAR"
UNITS = ("U001", "U002", "U003")
YEARS = (2023, 2024, 2025)
T = 8760
# Rule 8 [R-8760]: the LP clock is a flat non-leap calendar; Feb 29 is dropped.
MONTH_STARTS = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
CACHE = ROOT / ".cache/nyiso212"
BENCH = ROOT / "frontend/data/backcast/bench/NYISO"
EXTRACT = ROOT / "data/raw/campd-unit-outages-perunitmerit-NYISO.csv"
UNIT_DIR = ROOT / "data/raw/campd-unit-level"
FAC_DIR = ROOT / "data/raw/campd-facility-level"
PRIOR = ROOT / "results/calibration/_nyiso211_overderate_test.json"
# The deriver's CF basis for these units (EIA-860 exact match on the CA rows)
# and its event-based detector constants (scripts/lib/outage_detect.py).
DETECT_CAP_MW = 174.2
CF_PEAK = 0.02
MIN_OUTAGE_HOURS = 5 * 24
# The keeper's over-ceiling months (nyiso-211 §5, arm basis), 1-based.
SCORED = {2023: [7], 2024: [7, 8, 9], 2025: [6, 7, 8]}
CONTROL_MONTH = (2023, 7)


def hour_index_8760(ts: pd.Series, year: int) -> np.ndarray:
    """Map calendar timestamps to the flat 8760 clock; Feb 29 -> -1."""
    leap = (ts.dt.month == 2) & (ts.dt.day == 29)
    # Day-of-year on a non-leap calendar: shift post-Feb-29 days back by one in
    # a leap year so Mar 1 is always day 60.
    doy = ts.dt.dayofyear.to_numpy().copy()
    if pd.Timestamp(f"{year}-12-31").dayofyear == 366:
        doy = np.where(ts.dt.month.to_numpy() > 2, doy - 1, doy)
    idx = (doy - 1) * 24 + ts.dt.hour.to_numpy()
    return np.where(leap.to_numpy(), -1, idx)


def monthly(arr_mw: np.ndarray) -> list[float]:
    """12 monthly GWh totals of an hourly-MW series on the 8760 clock."""
    return [float(arr_mw[MONTH_STARTS[m] : MONTH_STARTS[m + 1]].sum()) / 1e3 for m in range(12)]


def rebuild(year: int) -> dict:
    """On-recipe ``run_year(fleet_only=True)`` rebuild of the keeper; cached."""
    cache = CACHE / f"keeper_{year}.pkl"
    if cache.exists():
        return pickle.load(open(cache, "rb"))
    ensure_probe_path()
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = full_run_year_kwargs(meta)
    clear_fleet_caches()
    state = run_year(
        year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, year), **kwargs
    )
    fa = state["fleet_arrays"]
    rows = [
        {
            "i": i,
            "unit_id": str(g.unit_id),
            "plant": int(getattr(g, "plant_code", 0) or 0),
            "group": str(getattr(g, "plant_group", "") or ""),
            "pmax": float(g.pmax_mw),
        }
        for i, g in enumerate(state["fleet"])
    ]
    units = pd.DataFrame(rows)
    sel = units[(units.plant == PLANT) & (units.group == GROUP)]
    st = {
        "units": units,
        "plant_units": sel,
        # float64 for the plant's own rows (I2 needs 1e-9), float32 elsewhere.
        "plant_avail": np.asarray(fa.availability, dtype=np.float64)[sel.i.to_numpy(), :T],
        "extract_basis": bool(getattr(state["config"], "unit_outage_extract_basis_share", False)),
        "weather_year": int(getattr(state["config"], "weather_year", year)),
    }
    cache.parent.mkdir(parents=True, exist_ok=True)
    pickle.dump(st, open(cache, "wb"))
    return st


def loader_ufac(year: int) -> np.ndarray:
    """The loader's unit-outage factor for (57185, CC_REGULAR) on the keeper's flags."""
    from market_sim.config.paths import CAMPD_BINS_CSV

    fac = unit_outage_derate_factors(
        year,
        T,
        str(CAMPD_BINS_CSV),
        iso="NYISO",
        per_unit_crosswalk=True,
        merit_order_guard=True,
        extract_basis_share=True,
    )
    f = fac.get((PLANT, GROUP))
    return np.ones(T) if f is None else np.asarray(f, dtype=float)[:T]


def extract_windows() -> pd.DataFrame:
    df = pd.read_csv(EXTRACT)
    df = df[(df.facility_id == PLANT) & (df.duration_days >= 5.0)].copy()
    df["start"] = pd.to_datetime(df.outage_start)
    df["end_excl"] = pd.to_datetime(df.outage_end) + pd.Timedelta(days=1)
    return df


def window_masks(win: pd.DataFrame, year: int) -> dict[str, np.ndarray]:
    """Per-unit boolean hour masks on the 8760 clock: inside one of the unit's windows."""
    clock = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
    idx = hour_index_8760(pd.Series(clock), year)
    out = {u: np.zeros(T, dtype=bool) for u in UNITS}
    for r in win.itertuples(index=False):
        m = (clock >= r.start) & (clock < r.end_excl)
        keep = m & (idx >= 0)
        out.setdefault(str(r.unit_id), np.zeros(T, dtype=bool))[idx[keep]] = True
    return out


def campd_unit_gross(year: int) -> tuple[dict[str, np.ndarray], dict[str, float], pd.DataFrame]:
    """Unit-level CAMPD gross MW per unit on the 8760 clock, plus each unit's hourly peak."""
    raw = pd.read_parquet(
        UNIT_DIR / f"NY_{year}.parquet",
        columns=["facilityId", "unitId", "date", "hour", "grossLoad", "opTime"],
    )
    raw = raw[pd.to_numeric(raw.facilityId, errors="coerce") == PLANT].copy()
    ts = raw["date"] + pd.to_timedelta(raw["hour"], unit="h")
    raw["hoy"] = hour_index_8760(ts, year)
    gross: dict[str, np.ndarray] = {}
    peaks: dict[str, float] = {}
    for uid, sub in raw.groupby("unitId"):
        arr = np.zeros(T)
        g = np.nan_to_num(sub.grossLoad.to_numpy(dtype=float), nan=0.0)
        ok = sub.hoy.to_numpy() >= 0
        np.add.at(arr, sub.hoy.to_numpy()[ok], g[ok])
        gross[str(uid)] = arr
        peaks[str(uid)] = float(arr.max())
    return gross, peaks, raw


def campd_facility_gross(year: int) -> np.ndarray:
    raw = pd.read_parquet(
        FAC_DIR / f"NY_{year}.parquet", columns=["facilityId", "date", "hour", "grossLoad"]
    )
    raw = raw[pd.to_numeric(raw.facilityId, errors="coerce") == PLANT]
    ts = raw["date"] + pd.to_timedelta(raw["hour"], unit="h")
    hoy = hour_index_8760(ts, year)
    arr = np.zeros(T)
    g = np.nan_to_num(raw.grossLoad.to_numpy(dtype=float), nan=0.0)
    ok = hoy >= 0
    np.add.at(arr, hoy[ok], g[ok])
    return arr


def deriver_windows(raw_units: pd.DataFrame, year: int) -> dict[str, list[tuple[str, str]]]:
    """Re-run the deriver's CC window rule on the CURRENT unit-level file (I4).

    ``_unit_year_grid`` semantics reproduced verbatim: the unit's reported hours
    on a gap-free FULL-calendar clock (leap day kept), missing hours zero-filled,
    clipped at the file's publication horizon; then
    ``detect_outages_eventbased(gross, 174.2, 120 h, 0.02)``.
    """
    horizon_end = raw_units["date"].max() + pd.Timedelta(hours=23)
    full = pd.date_range(f"{year}-01-01", horizon_end, freq="h")
    out: dict[str, list[tuple[str, str]]] = {}
    for uid, sub in raw_units.groupby("unitId"):
        ts = sub["date"] + pd.to_timedelta(sub["hour"], unit="h")
        series = pd.Series(sub["grossLoad"].to_numpy(dtype=float), index=ts)
        series = series.groupby(level=0).sum().sort_index()
        gross = series.reindex(full).fillna(0.0).to_numpy(dtype=float)
        wins = detect_outages_eventbased(gross, DETECT_CAP_MW, MIN_OUTAGE_HOURS, CF_PEAK)
        out[str(uid)] = [
            (full[s].strftime("%Y-%m-%d"), full[e - 1].strftime("%Y-%m-%d")) for s, e in wins
        ]
    return out


def main() -> None:
    prior = json.load(open(PRIOR))["target"]
    win = extract_windows()
    record: dict = {
        "session": "nyiso-212",
        "status": "phase 0, ZERO LP; pre-registered (PREREG-nyiso212-cricket-valley-outage-window-construction.md)",
        "keeper": KEEPER_ID,
        "plant": PLANT,
        "basis": "GROSS CAMPD on both sides: bench c_mon = facility-level grossLoad x 1.0 (no parasitic row at 57185); LP pmax = CAMPD gross p99.9 (cc_capacity_reconcile cap)",
        "scored_months": {str(y): m for y, m in SCORED.items()},
        "identity_checks": {},
        "years": {},
    }
    i1_worst_gwh, i1_worst_mean = 0.0, 0.0
    i2_worst, i2_spread_worst = 0.0, 0.0
    i3_rows = {}
    i4_rows = {}
    for year in YEARS:
        st = rebuild(year)
        assert st["extract_basis"] is True, "keeper recipe must carry unit_outage_extract_basis_share"
        pu = st["plant_units"]
        pmax_tr = pu.pmax.to_numpy()[:, None]
        pmax_plant = float(pu.pmax.sum())
        avail = st["plant_avail"]  # (n_tranches, T)
        c2_h = (avail * pmax_tr).sum(axis=0)  # MW per hour
        # ---- I1: the instrument reproduces nyiso-211's committed arm-basis numbers
        c2_m = monthly(c2_h)
        prior_m = [None] * 12
        pa = prior[str(year)]["arm_basis"]
        prior_mean = pa["mean_avail"]
        mean_avail = float((avail * pmax_tr).sum() / (pmax_tr.sum() * T))
        # nyiso-211 stored monthly ratios, not monthly GWh; reconstruct its
        # monthly available GWh from ratio x c_mon below once the bench is read.
        bench = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]["plants"][str(PLANT)]
        c_mon = [float(v) for v in bench["c_mon"]]
        c_ann = float(bench["c_ann"]) * 1e3
        e_mon = [float(v) for v in (bench.get("e_mon") or [0.0] * 12)]
        prior_m = [
            (c_mon[i] / pa["monthly_ratio"][i]) if pa["monthly_ratio"][i] else None
            for i in range(12)
        ]
        d_gwh = max(abs(c2_m[i] - prior_m[i]) for i in range(12) if prior_m[i] is not None)
        i1_worst_gwh = max(i1_worst_gwh, d_gwh)
        i1_worst_mean = max(i1_worst_mean, abs(mean_avail - prior_mean))
        # ---- I2: windows -> loader factor, and the statistical factor is tranche-flat
        ufac = loader_ufac(year)
        masks = window_masks(win, year)
        recon = 1.0 - np.clip(sum((1.0 / 3.0) * masks[u].astype(float) for u in UNITS), 0.0, 1.0)
        i2 = float(np.abs(recon - ufac).max())
        i2_worst = max(i2_worst, i2)
        with np.errstate(divide="ignore", invalid="ignore"):
            stat = np.where(ufac > 0, avail / ufac, np.nan)  # per tranche
        spread = float(np.nanmax(np.nanmax(stat, axis=0) - np.nanmin(stat, axis=0)))
        i2_spread_worst = max(i2_spread_worst, spread)
        zero_ok = bool((avail[:, ufac <= 0] <= 1e-12).all()) if (ufac <= 0).any() else True
        c1_h = pmax_plant * ufac
        c1_m = monthly(c1_h)
        # ---- meter sides
        gross_u, peaks, raw_units = campd_unit_gross(year)
        fac_h = campd_facility_gross(year)
        fac_m = monthly(fac_h)
        unit_sum_m = monthly(sum(gross_u.get(u, np.zeros(T)) for u in gross_u))
        i3_rows[str(year)] = {
            "sum_c_mon_minus_c_ann_gwh": round(sum(c_mon) - c_ann, 4),
            "c_ann_gwh": round(c_ann, 3),
            "facility_gross_annual_gwh": round(float(fac_h.sum()) / 1e3, 3),
            "rel_diff": round(abs(float(fac_h.sum()) / 1e3 - c_ann) / c_ann, 6) if c_ann else None,
            "unit_level_annual_gwh": round(sum(unit_sum_m), 3),
            "unit_ids_in_unit_file": sorted(gross_u),
        }
        # ---- I4: deriver reproduction on the current unit-level file
        dw = deriver_windows(raw_units, year)
        committed = {
            u: sorted(
                (r.start.strftime("%Y-%m-%d"), (r.end_excl - pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
                for r in win[(win.unit_id == u) & (win.start.dt.year == year)].itertuples()
            )
            for u in UNITS
        }
        missing = {
            u: [w for w in committed[u] if w not in set(dw.get(u, []))] for u in UNITS
        }
        extra = {u: [w for w in dw.get(u, []) if w not in set(committed[u])] for u in UNITS}
        i4_rows[str(year)] = {
            "committed_windows": committed,
            "reproduced_windows_current_file": {u: dw.get(u, []) for u in UNITS},
            "committed_NOT_reproduced": missing,
            "reproduced_not_committed (filters may drop)": extra,
            "pass": all(not v for v in missing.values()),
        }
        # ---- the decomposition, every month
        s_share = pmax_plant / 3.0
        months = []
        for m in range(12):
            sl = slice(MONTH_STARTS[m], MONTH_STARTS[m + 1])
            M = c_mon[m]
            C2 = c2_m[m]
            C1 = c1_m[m]
            e_in = e_out = h_out_total = 0.0
            per_unit = {}
            for u in UNITS:
                g = gross_u.get(u, np.zeros(T))[sl]
                mk = masks[u][sl]
                ein = float(g[mk].sum()) / 1e3
                eout = float(g[~mk].sum()) / 1e3
                hout = int((~mk).sum())
                e_in += ein
                e_out += eout
                h_out_total += hout
                per_unit[u] = {
                    "gwh_in_window": round(ein, 2),
                    "gwh_out_window": round(eout, 2),
                    "hours_in_window": int(mk.sum()),
                    "share_ceiling_out_gwh": round(s_share * hout / 1e3, 2),
                    "peak_mw_month": round(float(g.max()), 1),
                }
            unit_sum = e_in + e_out
            T_bench = M - unit_sum
            T_in = e_in
            T_cap = e_out - s_share * h_out_total / 1e3
            T_stat = C1 - C2
            X = M - C2
            months.append(
                {
                    "month": m + 1,
                    "scored": (m + 1) in SCORED[year],
                    "M_bench_gwh": round(M, 2),
                    "facility_file_gwh": round(fac_m[m], 2),
                    "unit_file_sum_gwh": round(unit_sum, 2),
                    "e923_net_gwh": round(e_mon[m], 2),
                    "C2_lp_ceiling_gwh": round(C2, 2),
                    "C1_window_ceiling_gwh": round(C1, 2),
                    "X_excess_gwh": round(X, 2),
                    "T_stat": round(T_stat, 2),
                    "T_bench": round(T_bench, 2),
                    "T_in": round(T_in, 2),
                    "T_cap": round(T_cap, 2),
                    "identity_residual": round(X - (T_stat + T_bench + T_in + T_cap), 6),
                    "per_unit": per_unit,
                }
            )
        record["years"][str(year)] = {
            "pmax_plant_mw": round(pmax_plant, 1),
            "tranches": int(len(pu)),
            "unit_share_mw": round(s_share, 1),
            "mean_avail": round(mean_avail, 4),
            "unit_peak_mw_year": {u: round(peaks.get(u, 0.0), 1) for u in UNITS},
            "months": months,
        }
    record["identity_checks"] = {
        "I1_instrument": {
            "worst_abs_monthly_gwh_vs_nyiso211": round(i1_worst_gwh, 4),
            "worst_abs_mean_avail_vs_nyiso211": round(i1_worst_mean, 6),
            "bar": "<= 0.5 GWh per month; mean_avail to 4 dp",
            "pass": bool(i1_worst_gwh <= 0.5 and i1_worst_mean < 5e-5),
        },
        "I2_windows": {
            "worst_abs_diff_recon_vs_loader": i2_worst,
            "worst_tranche_spread_of_statistical_factor": i2_spread_worst,
            "availability_zero_where_ufac_zero": zero_ok,
            "bar": "<= 1e-9 both",
            "pass": bool(i2_worst <= 1e-9 and i2_spread_worst <= 1e-9 and zero_ok),
        },
        "I3_basis": {
            "per_year": i3_rows,
            "bar": "sum(c_mon)=c_ann +-0.01 GWh; c_ann = facility gross x 1.0 within 0.1 %",
            "pass": all(
                abs(r["sum_c_mon_minus_c_ann_gwh"]) <= 0.01 and (r["rel_diff"] or 0) <= 0.001
                for r in i3_rows.values()
            ),
        },
        "I4_deriver": {
            "per_year": i4_rows,
            "bar": "every committed 2024/2025 window reproduced from the current unit-level file",
            "pass": all(i4_rows[str(y)]["pass"] for y in (2024, 2025)),
        },
    }
    # ---- verdict table over the scored months
    verdict = []
    for year in YEARS:
        for row in record["years"][str(year)]["months"]:
            if not row["scored"]:
                continue
            X = row["X_excess_gwh"]
            terms = {k: row[k] for k in ("T_stat", "T_bench", "T_in", "T_cap")}
            dom = max(terms, key=lambda k: terms[k])
            verdict.append(
                {
                    "year": year,
                    "month": row["month"],
                    "X": X,
                    **{k: round(v / X, 3) if X else None for k, v in terms.items()},
                    "dominant": dom if X and terms[dom] >= 0.5 * X else None,
                }
            )
    record["scored_month_shares"] = verdict
    dest = ROOT / "results/calibration/_nyiso212_overceiling_decomposition.json"
    dest.write_text(json.dumps(record, indent=1, default=str))
    print(json.dumps(record["identity_checks"], indent=1, default=str))
    print(pd.DataFrame(verdict).to_string())
    for year in YEARS:
        y = record["years"][str(year)]
        print(f"\n== {year} pmax {y['pmax_plant_mw']} share {y['unit_share_mw']} peaks {y['unit_peak_mw_year']}")
        cols = ["month", "scored", "M_bench_gwh", "facility_file_gwh", "unit_file_sum_gwh",
                "e923_net_gwh", "C2_lp_ceiling_gwh", "C1_window_ceiling_gwh", "X_excess_gwh",
                "T_stat", "T_bench", "T_in", "T_cap"]
        print(pd.DataFrame([{c: r[c] for c in cols} for r in y["months"]]).to_string(index=False))


if __name__ == "__main__":
    main()
