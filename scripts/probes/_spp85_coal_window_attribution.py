"""SPP-85 (zero LP): unit-level attribution of the keeper's CAMPD coal outage windows.

Record: ``docs/handoffs/FINDING-spp-85-coal-outage-basis-2026-09-26.md``.

SPP-84 found the keeper ``results/calibration/rspp_span`` carries +1.2-3.4 GW MORE coal outage
than SPP publishes (portal ``capacity-of-generation-on-outage``) in every year 2019-2024. This
probe attributes that excess window by window, against the three committed SPP coal layers the
keeper reads (``unit_outage_short_windows`` and ``unit_partial_outage_windows`` are both ON):

* ``data/raw/campd-unit-outages-SPP.csv``       (>= 5-day full stops, COAL rows)
* ``data/raw/campd-unit-outages-short-SPP.csv`` (1-5 day coal full stops)
* ``data/raw/campd-partial-outages-SPP.csv``    (>= 5-day coal CF-ceiling plateaus, derate_factor)

Per window it measures, with no parameter chosen here:

1. **the deriver's OWN revealed-availability verdict** — whether the window survives in the
   ``-netloadmask-`` companion, i.e. the SAME deriver re-run at the extract's own recorded
   invocation once ``scripts/lib/outage_detect._ISO_TO_BA`` carries ``SPP -> SWPP``. The committed
   SPP extracts were derived with that key ABSENT, so ``high_load_mask("SPP", ...)`` returned
   ``None`` and ``filter_revealed_outages`` kept every span (its documented no-mask no-op): the
   recorded ``min_inmerit_hours`` was never in effect. (A day-grain re-application of the filter
   to the extract's own dates OVER-drops: re-expanding a window to whole days pulls the unit's
   running return-to-service hours into the span. Only the hour-grain re-derivation is the test.)
2. **LMP in-merit hours** — hours in the window where SPP's ACTUAL RT system LMP is at or above
   the plant's own keeper offer (median ``mc_base`` over the plant's coal rows). Reported, never
   used as a removal test (rule 13: a realized price is an outcome, see the FINDING §4).
3. **SPP's published coal outage** over the window's hours, and the window's season.

Then the hourly keeper coal outage is rebuilt from the three layers (MW = the unit's share of its
plant x the keeper plant's coal pmax, x (1 - derate_factor) for plateaus; concurrent units summed and
clipped at the plant) and the keeper-minus-SPP excess is decomposed by removing classes in a fixed,
pre-declared order: (i) main windows the deriver's own filter drops, (ii) partial plateaus,
(iii) short windows, (iv) residual.

Solves nothing. Usage:
``python scripts/probes/_spp85_coal_window_attribution.py --cache <fleet pkl dir> --outage <dir of o<y>.zip>
[--gencap <dir>] [--years 2019 ... 2024] [--out <json>] [--windows-out <csv>]``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from scripts.probes._spp81b_upper_tercile_marginal_unit import rebuild  # noqa: E402
from scripts.probes._spp84_published_outage_rebasis import (  # noqa: E402
    edge_mask,
    load_outage_zips,
    spp_outage_on_model_clock,
)

FINDING = "docs/handoffs/FINDING-spp-85-coal-outage-basis-2026-09-26.md"
T = 8760
STATES = ("AR", "CO", "IA", "KS", "LA", "MN", "MO", "MT", "ND", "NE", "NM", "OK", "SD", "TX")
NLM = {
    "main": "campd-unit-outages-netloadmask-SPP.csv",
    "short": "campd-unit-outages-short-netloadmask-SPP.csv",
    "partial": "campd-partial-outages-netloadmask-SPP.csv",
}
KEY = ["facility_id", "unit_id", "outage_start", "outage_end"]
LAYERS = {
    "main": "campd-unit-outages-SPP.csv",
    "short": "campd-unit-outages-short-SPP.csv",
    "partial": "campd-partial-outages-SPP.csv",
}
SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
          6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}






def unit_gross(y: int) -> dict[tuple[int, str], np.ndarray]:
    """CEMS gross MW per (facility, unit) on the calendar clock of year ``y`` (zero-filled)."""
    clock = pd.date_range(f"{y}-01-01", f"{y}-12-31 23:00", freq="h")
    out = {}
    for st in STATES:
        p = RAW_DATA_DIR / f"campd-unit-level/{st}_{y}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(p, columns=["facilityId", "unitId", "date", "hour", "grossLoad"])
        d["t"] = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"].astype(int), unit="h")
        d["g"] = pd.to_numeric(d.grossLoad, errors="coerce").fillna(0.0)
        for (f, u), g in d.groupby(["facilityId", "unitId"]):
            s = g.groupby("t").g.sum().reindex(clock, fill_value=0.0).to_numpy()
            out[(int(f), str(u).strip())] = s
    return out


def windows(layer: str, y: int) -> pd.DataFrame:
    """Coal windows of one layer overlapping ``y``, as calendar hour indices [s, e)."""
    d = pd.read_csv(RAW_DATA_DIR / LAYERS[layer])
    d = d[d.plant_group == "COAL"].copy()
    d["t0"] = pd.to_datetime(d.outage_start)
    d["t1"] = pd.to_datetime(d.outage_end) + pd.Timedelta(days=1)  # day-grain, as the loader
    y0 = pd.Timestamp(f"{y}-01-01")
    d = d[(d.t1 > y0) & (d.t0 < pd.Timestamp(f"{y + 1}-01-01"))].copy()
    d["s"] = ((d.t0.clip(lower=y0) - y0) / pd.Timedelta(hours=1)).astype(int)
    d["e"] = ((d.t1.clip(upper=pd.Timestamp(f"{y + 1}-01-01")) - y0) / pd.Timedelta(hours=1)).astype(int)
    if layer == "main":
        d = d[d.duration_days >= 5.0]
    if layer == "short":
        d = d[d.duration_days < 5.0]
    d["layer"] = layer
    if "derate_factor" not in d:
        d["derate_factor"] = 0.0
    return d




def year_run(y: int, cache: Path, o: pd.DataFrame, lmp: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Per-window attribution and the per-class hourly decomposition for one year."""
    fl = rebuild(y, cache, False)
    r = pd.DataFrame(fl["rows"])
    coal = (r.fuel_type == "coal").to_numpy()
    av = fl["avail"].astype(float)
    pm = av.max(1)
    rc = r[coal].assign(pm=pm[coal])
    plant_pm = rc.groupby(rc.plant_code.astype(int)).pm.sum()
    mc = pd.DataFrame(fl["mc"][coal].astype(float)).groupby(rc.plant_code.astype(int).to_numpy()).median()
    # keeper coal unavailable, SPP-84's exact measure (edge masks excluded)
    em = np.array([edge_mask(a, 30 * 24) for a in av[coal]])
    k_un = (np.where(em, av[coal], pm[coal][:, None]) - av[coal]).sum(0)
    sp = spp_outage_on_model_clock(o, y)
    s_coal = sp["Coal MW"].to_numpy() if sp["Coal MW"].notna().mean() >= 0.9 else None
    rt = lmp[lmp.year == y].set_index("hour").rt.reindex(range(T)).to_numpy()
    n_cal = len(pd.date_range(f"{y}-01-01", f"{y}-12-31 23:00", freq="h"))
    gross = unit_gross(y)
    kept = {
        k: set(map(tuple, pd.read_csv(RAW_DATA_DIR / f)[KEY].astype(str).to_numpy()))
        for k, f in NLM.items()
    }
    rec = []
    W = pd.concat([windows(k, y) for k in LAYERS])
    for w in W.itertuples():
        pc, uid = int(w.facility_id), str(w.unit_id).strip()
        g = gross.get((pc, uid))
        cap = float(w.unit_capacity_mw)
        cf = g / cap if (g is not None and cap > 0) else np.zeros(n_cal)
        keep = (str(w.facility_id), str(w.unit_id), str(w.outage_start), str(w.outage_end)) in kept[w.layer]
        s, e = w.s, min(w.e, T)
        in_merit = (
            int(np.nansum(rt[s:e] >= mc.loc[pc].to_numpy()[s:e])) if pc in mc.index and e > s else -1
        )
        mid = pd.Timestamp(f"{y}-01-01") + pd.Timedelta(hours=(w.s + w.e) // 2)
        rec.append({
            "year": y, "layer": w.layer, "plant": pc, "unit": uid, "name": w.facility_name,
            "in_fleet": pc in plant_pm.index, "start": str(w.t0.date()), "end": str((w.t1 - pd.Timedelta(days=1)).date()),
            "s": w.s, "e": w.e, "hours": w.e - w.s, "duration_days": float(w.duration_days),
            "season": SEASON[mid.month], "unit_mw": cap, "pct": float(w.unit_pct_of_plant) / 100.0,
            "derate_factor": float(w.derate_factor), "span_cf": float(cf[w.s:w.e].mean()) if w.e > w.s else np.nan,
            "deriver_keeps_swpp": keep,
            "lmp_inmerit_h": in_merit,
            "spp_coal_outage_gw": float(np.nanmean(s_coal[s:e]) / 1e3) if s_coal is not None and e > s else np.nan,
        })
    R = pd.DataFrame(rec)
    R = R[R.in_fleet].copy()
    R["mw"] = R.pct * R.plant.map(plant_pm) * np.where(R.layer == "partial", 1.0 - R.derate_factor, 1.0)
    R["cls"] = np.select(
        [(R.layer == "main") & ~R.deriver_keeps_swpp, R.layer == "partial",
         (R.layer == "short") & ~R.deriver_keeps_swpp, R.layer == "short"],
        ["i_main_filter_drop", "ii_partial", "iii_short_filter_drop", "iii_short_kept"], "iv_main_kept",
    )
    # hourly MW by class, concurrent units summed and clipped at the plant pmax (pro rata by class)
    classes = ["i_main_filter_drop", "ii_partial", "iii_short_filter_drop", "iii_short_kept", "iv_main_kept"]
    H = {c: np.zeros(T) for c in classes}
    for pc, g in R.groupby("plant"):
        A = np.zeros((len(classes), T))
        for w in g.itertuples():
            A[classes.index(w.cls), w.s:min(w.e, T)] += w.mw
        tot = A.sum(0)
        scale = np.where(tot > plant_pm[pc], plant_pm[pc] / np.maximum(tot, 1e-9), 1.0)
        for i, c in enumerate(classes):
            H[c] += A[i] * scale
    rebuilt = sum(H.values())
    out = {
        "year": y, "coal_pmax_gw": float(plant_pm.sum() / 1e3),
        "keeper_unavail_gw": float(k_un.mean() / 1e3), "windows_rebuilt_gw": float(rebuilt.mean() / 1e3),
        "non_window_unavail_gw": float((k_un - rebuilt).mean() / 1e3),
        "class_gw": {c: float(H[c].mean() / 1e3) for c in classes},
        "n_windows": R.groupby("cls").size().to_dict(),
        "main_windows_n": int((R.layer == "main").sum()),
        "main_windows_dropped_by_deriver_swpp": int(((R.layer == "main") & ~R.deriver_keeps_swpp).sum()),
        "short_dropped_by_deriver_swpp": int(((R.layer == "short") & ~R.deriver_keeps_swpp).sum()),
        "partial_dropped_by_deriver_swpp": int(((R.layer == "partial") & ~R.deriver_keeps_swpp).sum()),
        "main_lmp_inmerit_lt24_n": int(((R.layer == "main") & (R.lmp_inmerit_h < 24)).sum()),
        "main_lmp_inmerit_lt24_gw": float(
            sum((R.mw * (R.e.clip(upper=T) - R.s))[(R.layer == "main") & (R.lmp_inmerit_h < 24)]) / T / 1e3
        ),
        "main_fullstop_share": float((R[R.layer == "main"].span_cf < 0.02).mean()),
    }
    if s_coal is not None:
        out["spp_coal_outage_gw"] = float(np.nanmean(s_coal) / 1e3)
        out["keeper_minus_spp_gw"] = float(np.nanmean(k_un - s_coal) / 1e3)
        # sequential removal, pre-declared order i -> ii -> iii
        rest = k_un.copy()
        steps = {}
        for c in ["i_main_filter_drop", "ii_partial", "iii_short_filter_drop", "iii_short_kept"]:
            rest = rest - H[c]
            steps[c] = float(np.nanmean(rest - s_coal) / 1e3)
        out["excess_after_removing_gw"] = steps
        mon = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(T), unit="h")).month
        out["monthly_gw"] = {
            "keeper_minus_spp": (pd.Series(k_un - s_coal).groupby(mon).mean() / 1e3).round(2).tolist(),
            **{c: (pd.Series(H[c]).groupby(mon).mean() / 1e3).round(2).tolist() for c in classes},
            "spp": (pd.Series(s_coal).groupby(mon).mean() / 1e3).round(2).tolist(),
        }
        # SPP published coal outage on window hours vs off-window hours
        on = rebuilt > 1.0
        out["spp_coal_outage_on_window_hours_gw"] = float(np.nanmean(s_coal[on]) / 1e3)
        out["spp_coal_outage_off_window_hours_gw"] = float(np.nanmean(s_coal[~on]) / 1e3) if (~on).any() else None
    return out, R


def main() -> None:
    """Run all years; print and write JSON + the per-window CSV."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--outage", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2025)))
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "results/calibration/_spp85_coal_window_attribution.json")
    ap.add_argument("--windows-out", type=Path)
    a = ap.parse_args()
    o = load_outage_zips(a.outage)
    lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet")
    res = {"lane": "SPP-85", "finding": FINDING, "per_year": {}}
    allw = []
    for y in a.years:
        row, R = year_run(y, a.cache, o, lmp)
        res["per_year"][str(y)] = row
        allw.append(R)
        print(json.dumps({k: v for k, v in row.items() if k != "monthly_gw"}, default=str), flush=True)
    a.out.write_text(json.dumps(res, indent=1, default=float))
    if a.windows_out:
        pd.concat(allw).to_csv(a.windows_out, index=False)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
