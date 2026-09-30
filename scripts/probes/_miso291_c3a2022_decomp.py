#!/usr/bin/env python3
"""miso-291 phase 0 (ZERO LP): where the keeper's C3a 2022 gap lives, on the scorer's own basis.

C3a for MISO scores the model's zone-demand-weighted mean P1 price against the
equal-hour RT price of the system reference series (INDIANA.HUB,
``actual_lmp_hourly_MISO.parquet``), both masked to the actual's covered months
(2022: Jan-Oct, ``_covered_months``). This probe reproduces that number from the
keeper's committed ``hourly/system_<Y>.parquet`` and splits it four ways:

1. **Comparator wedge.** INDIANA.HUB = MEC + MCC + MLC (MISO's published hub
   components). The model is a copper plate across the Midwest (miso-277), so
   the part of the gap equal to ``-(MCC + MLC)`` at the comparator is congestion
   and losses the model cannot carry. ``internal_congestion_split`` is G.
2. **Band of actual price** (miso-206 §8.3 construction): contribution of each
   band of the actual hourly price to the equal-hour gap, so the bands sum.
3. **Hour group and month**, same additive construction.
4. **Implied heat rate** against the Chicago Citygate daily print (MISO's
   North gas hub; the keeper prices North gas at that hub plus measured
   transport): if the model's price/gas ratio matches the actual's, gas level
   explains the level; if it falls short, the gap is in the stack, not the fuel.

All seven years are reported so 2022 reads against years that pass.
Rule 13: nothing here feeds a solve.

Usage::

    uv run python scripts/probes/_miso291_c3a2022_decomp.py --out results/calibration/_miso291_c3a2022_decomp.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso277_c3a2022_congestion as m277  # noqa: E402

KEEPER = REPO / "results/calibration/miso280_span"
ACT = REPO / "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet"
REF = REPO / "data/raw/_validation-source/actual_lmp.json"
GAS = REPO / "data/raw/gas-prices/miso_citygate_daily.csv"
YEARS = tuple(range(2019, 2026))
#: Actual-price band edges (percentiles of the covered hours), miso-206 §8.3.
BANDS = (0, 50, 75, 90, 95, 99, 100)
#: Hour-of-day groups (model clock, hour-ending index 0-23), miso-283 §2.
HOUR_GROUPS = {
    "night_h0_5": (0, 6),
    "morning_h6": (6, 7),
    "day_h7_14": (7, 15),
    "evening_h15_20": (15, 21),
    "late_h21_23": (21, 24),
}


def r(x: float, n: int = 2):
    """Round, NaN-safe for JSON."""
    return None if x is None or not np.isfinite(x) else round(float(x), n)


def covered_months(year: int) -> list[int]:
    """Months (1-12) the C3a mask keeps, read from the committed coverage vector."""
    import scripts.calibration_verdict as cv  # type: ignore

    ref = json.load(open(REF))["MISO"][str(year)]
    cov = cv._coverage_mon({"rt_mon": ref.get("rt_mon")}, "rt", "MISO", year)
    idx = cv._covered_months(ref.get("rt_mon"), cov)
    return [i + 1 for i in idx]


def load_year(year: int):
    """Model (zone,8760) price/demand, actual 8760 INDIANA RT, month/hod arrays."""
    s = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    p = s.pivot(index="hour", columns="zone", values="price").reindex(range(8760))
    d = s.pivot(index="hour", columns="zone", values="demand").reindex(range(8760))
    a = pd.read_parquet(ACT)
    a = a[a["year"] == year].set_index("hour")["rt"].reindex(range(8760)).to_numpy()
    ts = pd.Timestamp("2021-01-01") + pd.to_timedelta(np.arange(8760), "h")
    return (
        p.to_numpy(float).T,
        d.to_numpy(float).T,
        a,
        ts.month.to_numpy(),
        ts.hour.to_numpy(),
    )


def chicago_gas(year: int) -> np.ndarray:
    """(8760,) Chicago Citygate daily spot on the non-leap model clock."""
    g = pd.read_csv(GAS, parse_dates=["date"]).set_index("date")[
        "chicago_citygate_usd_mmbtu"
    ]
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31")
    days = days[~((days.month == 2) & (days.day == 29))]
    v = (
        g.reindex(pd.date_range(f"{year - 1}-12-01", f"{year}-12-31"))
        .ffill()
        .reindex(days)
    )
    return np.repeat(v.to_numpy(float), 24)[:8760]


def probe_year(year: int) -> dict:
    """The four-way split for one year."""
    P, D, a, month, hod = load_year(year)
    months = covered_months(year)
    mask = np.isin(month, months) & np.isfinite(a) & np.isfinite(P).all(0)
    n = int(mask.sum())
    # Scorer basis: model = sum(p*d)/sum(d) over covered hours; actual = equal-hour mean.
    model_lw = float((P[:, mask] * D[:, mask]).sum() / D[:, mask].sum())
    actual = float(a[mask].mean())
    # Hourly system model price (load-weighted across zones), and the load-weight term.
    msys = (P * D).sum(0) / D.sum(0)
    model_eq = float(msys[mask].mean())
    lw_term = model_lw - model_eq
    diff = msys - a
    res = {
        "months": months,
        "hours": n,
        "model_lw": r(model_lw),
        "actual_indiana_rt": r(actual),
        "gap": r(model_lw - actual),
        "gap_pct": r(100 * (model_lw / actual - 1), 1),
        "load_weight_term": r(lw_term),
        "equal_hour_gap": r(model_eq - actual),
    }
    # (1) Comparator wedge from published hub components.
    comp = m277.hub_components(year)
    if comp is not None:
        ind = {k: comp[k]["INDIANA.HUB"] for k in ("LMP", "MCC", "MLC")}
        ok = (
            mask
            & np.isfinite(ind["LMP"])
            & np.isfinite(ind["MCC"])
            & np.isfinite(ind["MLC"])
        )
        mec = ind["LMP"] - ind["MCC"] - ind["MLC"]
        res["components_hours"] = int(ok.sum())
        res["components_lmp_vs_actuals_maxabs"] = r(
            np.nanmax(np.abs(ind["LMP"][ok] - a[ok])), 3
        )
        res["indiana_mcc_mean"] = r(ind["MCC"][ok].mean())
        res["indiana_mlc_mean"] = r(ind["MLC"][ok].mean())
        res["mec_mean"] = r(mec[ok].mean())
        res["model_eq_minus_mec"] = r((msys[ok] - mec[ok]).mean())
        # Other hubs' congestion+loss, for context (is Indiana the outlier?).
        res["hub_mcc_plus_mlc"] = {
            h: r(np.nanmean((comp["MCC"][h] + comp["MLC"][h])[ok])) for h in comp["MCC"]
        }
        e_diff = msys - mec
    else:
        e_diff = None
    # (2) Band of actual price.
    q = np.percentile(a[mask], BANDS)
    bands = {}
    for lo, hi, qlo, qhi in zip(BANDS[:-1], BANDS[1:], q[:-1], q[1:]):
        b = mask & (a >= qlo) & ((a < qhi) if hi < 100 else (a <= qhi))
        row = {
            "n": int(b.sum()),
            "actual_lo": r(qlo),
            "actual_hi": r(qhi),
            "contrib_vs_indiana": r(diff[b].sum() / n),
        }
        if e_diff is not None:
            row["contrib_vs_mec"] = r(np.nansum(e_diff[b]) / n)
            row["contrib_wedge"] = r(np.nansum((mec - a)[b]) / n)
        bands[f"p{lo}-{hi}"] = row
    res["bands"] = bands
    # (3) Hour group and month.
    hg = {}
    for k, (h0, h1) in HOUR_GROUPS.items():
        b = mask & (hod >= h0) & (hod < h1)
        row = {
            "n": int(b.sum()),
            "contrib_vs_indiana": r(diff[b].sum() / n),
            "mean_diff_vs_indiana": r(diff[b].mean()),
        }
        if e_diff is not None:
            row["contrib_vs_mec"] = r(np.nansum(e_diff[b]) / n)
            row["mean_diff_vs_mec"] = r(np.nanmean(e_diff[b]))
        hg[k] = row
    res["hour_groups"] = hg
    res["by_hod_vs_indiana"] = [r(diff[mask & (hod == h)].mean(), 1) for h in range(24)]
    if e_diff is not None:
        res["by_hod_vs_mec"] = [
            r(np.nanmean(e_diff[mask & (hod == h)]), 1) for h in range(24)
        ]
    mon = {}
    g = chicago_gas(year)
    for m in months:
        b = mask & (month == m)
        row = {
            "actual": r(a[b].mean()),
            "model": r(msys[b].mean()),
            "contrib_vs_indiana": r(diff[b].sum() / n),
            "chicago_gas": r(np.nanmean(g[b]), 3),
            "ihr_actual": r(a[b].mean() / np.nanmean(g[b])),
            "ihr_model": r(msys[b].mean() / np.nanmean(g[b])),
        }
        if e_diff is not None:
            row["mec"] = r(np.nanmean(mec[b]))
            row["ihr_mec"] = r(np.nanmean(mec[b]) / np.nanmean(g[b]))
        mon[str(m)] = row
    res["months_detail"] = mon
    # (4) Implied heat rate, covered hours.
    gm = float(np.nanmean(g[mask]))
    res["chicago_gas_mean"] = r(gm, 3)
    res["ihr_actual"] = r(actual / gm)
    res["ihr_model"] = r(model_eq / gm)
    if e_diff is not None:
        res["ihr_mec"] = r(float(np.nanmean(mec[mask])) / gm)
    # Hour-level model reach: max model price and top-1 % model vs actual.
    res["model_max"] = r(np.nanmax(msys[mask]))
    res["actual_max"] = r(np.nanmax(a[mask]))
    res["hours_actual_gt_150"] = int((a[mask] > 150).sum())
    res["hours_model_gt_150"] = int((msys[mask] > 150).sum())
    return res


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = {
        "keeper": "2026-09-28-miso-280-splitremap",
        "bundle": str(KEEPER.relative_to(REPO)),
        "years": {str(y): probe_year(y) for y in YEARS},
    }
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    for y, v in out["years"].items():
        print(
            y,
            v["gap_pct"],
            v["gap"],
            v.get("indiana_mcc_mean"),
            v.get("indiana_mlc_mean"),
            v.get("model_eq_minus_mec"),
            v["ihr_actual"],
            v["ihr_model"],
            v.get("ihr_mec"),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def dispatch_identity(out_path: Path) -> None:
    """Coal / gas / wind / net-import TWh: keeper P1 vs EIA-930, by hour group, Jan-Oct.

    Answers whether the day/evening under-pricing coincides with the model running
    more coal and less gas than MISO did (the 2022 coal-conservation year) — a
    quantity question, not a price one. Uses the benchmark's own EIA-930 frame
    (``build_benchmark_frames``) and the miso-285 class -> series map.
    """
    from scripts.probes._miso285_night_supply_identity import SERIES
    from scripts.run_calibration_full import build_benchmark_frames  # type: ignore

    _, frames = build_benchmark_frames(KEEPER)
    e930 = frames["eia930"]
    res = {}
    for y in YEARS:
        ch = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        ch["series"] = ch["klass"].map(SERIES)
        mdl = ch.groupby(["series", "hour"])["mw"].sum().unstack(0).reindex(range(8760))
        act = e930[e930.year == y].pivot(index="hour", columns="series", values="mw")
        act = act.reindex(range(8760))
        ts = pd.Timestamp("2021-01-01") + pd.to_timedelta(np.arange(8760), "h")
        month, hod = ts.month.to_numpy(), ts.hour.to_numpy()
        mask = np.isin(month, covered_months(y))
        row = {}
        for k, (h0, h1) in HOUR_GROUPS.items():
            b = mask & (hod >= h0) & (hod < h1)
            row[k] = {
                s: {
                    "model_twh": r(mdl[s].to_numpy()[b].sum() / 1e6, 2)
                    if s in mdl
                    else None,
                    "actual_twh": r(np.nansum(act[s].to_numpy()[b]) / 1e6, 2)
                    if s in act
                    else None,
                }
                for s in ("coal", "gas", "wind", "nuclear", "interchange")
            }
        summer = mask & np.isin(month, [5, 6, 7, 8, 9]) & (hod >= 7) & (hod < 21)
        row["summer_day_evening_h7_20"] = {
            s: {
                "model_twh": r(mdl[s].to_numpy()[summer].sum() / 1e6, 2)
                if s in mdl
                else None,
                "actual_twh": r(np.nansum(act[s].to_numpy()[summer]) / 1e6, 2)
                if s in act
                else None,
            }
            for s in ("coal", "gas", "wind", "nuclear", "interchange")
        }
        res[str(y)] = row
    Path(out_path).write_text(json.dumps(res, indent=1) + "\n")


def gas_vs_hub(year: int, out_path: Path) -> None:
    """Model delivered gas (pmax-weighted, gas classes) vs Chicago / Henry daily, by zone and month.

    Fleet-only rebuild of the keeper's recipe for ``year`` (miso-283 pattern).
    """
    from scripts.probes import _miso271_cc_decomp as dec
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    hh = _henry_hub_actual(_load_reference(), year)
    st = run_year(year, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(year, {}))
    fa, isoc = st["fleet_arrays"], st["iso_config"]
    n = len(fa.pmax)
    pmax = np.asarray(fa.pmax, dtype=float)
    zn = list(isoc.zone_names)
    zone = np.array([zn[i] for i in np.asarray(fa.zone_idx).astype(int)])
    grp = np.asarray(list(fa.plant_group))
    fp = np.asarray(st.get("fuel_prices"), dtype=float)
    if fp.ndim == 1:
        fp = np.repeat(fp[:, None], 8760, axis=1)
    g = pd.read_csv(GAS, parse_dates=["date"]).set_index("date")
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31")
    days = days[~((days.month == 2) & (days.day == 29))]
    gd = (
        g.reindex(pd.date_range(f"{year - 1}-12-01", f"{year}-12-31"))
        .ffill()
        .reindex(days)
    )
    chi = np.repeat(gd["chicago_citygate_usd_mmbtu"].to_numpy(float), 24)[:8760]
    hen = np.repeat(gd["henry_hub_usd_mmbtu"].to_numpy(float), 24)[:8760]
    month = (
        pd.Timestamp("2021-01-01") + pd.to_timedelta(np.arange(8760), "h")
    ).month.to_numpy()
    res = {}
    for z in zn:
        m = (
            (zone == z)
            & np.isin(
                grp, ["CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS", "CT_CHP", "ST_CHP"]
            )
            & (pmax > 0)
        )
        if not m.any() or fp.shape[0] != n:
            continue
        w = pmax[m]
        gh = (fp[m] * w[:, None]).sum(0) / w.sum()
        res[z] = {
            str(mm): {
                "model": r(gh[month == mm].mean(), 3),
                "chicago": r(chi[month == mm].mean(), 3),
                "henry": r(hen[month == mm].mean(), 3),
            }
            for mm in range(1, 13)
        }
        res[z]["annual"] = {
            "model": r(gh.mean(), 3),
            "chicago": r(np.nanmean(chi), 3),
            "henry": r(np.nanmean(hen), 3),
        }
    Path(out_path).write_text(json.dumps(res, indent=1) + "\n")
