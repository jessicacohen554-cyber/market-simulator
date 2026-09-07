"""miso-234 phase 0 part E — the CC_REGULAR-2023 residual, attributed by hour.
Zero LP.

The lever queue's item 3 names the CC_REGULAR-2023 give-back (-6.313 -> -6.445
TWh across the miso-233 promotion, the largest adverse C1 move) and asks: which
hours lost CC energy, and to whom?

The hour-level DIFF against miso-232 is not computable at HEAD — that bundle was
pruned under rule 15 [R-DASHBOARD]'s keeper-only retention when miso-233 was
promoted, and git history is the record. What IS computable, and is the bigger
object anyway, is the -6.445 TWh LEVEL residual itself, attributed hour by hour
against the same measured basis the C1 scorer uses: the committed per-plant CAMPD
hourly (bench ``plants[*].campd``, base64 bytes x npl/100) versus the run
payload's own per-plant model hourly (``plants[*].m``, same encoding). Both sides
are read from committed artifacts; no solve, no bundle regeneration.

Reported per year: where the deficit sits in the day, in the measured-price
distribution and in the load distribution, and what the model is running in those
same hours instead.

Usage: python3 scripts/probes/_miso234_cc_giveback_phase0.py
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

RUN_ID = "2026-09-07-miso-233-spp-hourly"
KEEPER = REPO / "results/calibration/miso233_sppseam_K"
OUT = REPO / "results/calibration/_miso234_cc_giveback_phase0.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
GROUP = "CC_REGULAR"


def load_payload() -> dict:
    txt = (REPO / f"frontend/data/backcast/runs/{RUN_ID}.js").read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', txt)
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))).decode())


def series(b64: str, cap: float) -> np.ndarray:
    x = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)[:HOURS]
    out = np.zeros(HOURS)
    out[: x.size] = x * (cap / 100.0)
    return out


def main() -> int:
    from _miso224_floor_anatomy_phase0 import actual_zone_price

    pay = load_payload()
    years_pay = pay.get("years") or pay
    report = {
        "probe": "miso-234 phase 0 part E — CC_REGULAR residual attributed by hour",
        "keeper": RUN_ID,
        "zero_lp": True,
        "basis": "committed bench plants[*].campd vs committed payload plants[*].m",
        "note_on_item3": (
            "the miso-232 hour-level DIFF is not computable at HEAD: that bundle "
            "was pruned under rule 15 keeper-only retention at the miso-233 "
            "promotion; git history is the record. The LEVEL residual is "
            "attributed instead."
        ),
        "years": {},
    }
    years_out = {}

    for year in YEARS:
        yb = json.load(gzip.open(REPO / f"frontend/data/backcast/bench/MISO/{year}.json.gz"))["bench"]
        bplants = yb["plants"]
        yp = years_pay.get(str(year)) or years_pay.get(year)
        pplants = yp["plants"]

        act = np.zeros(HOURS)
        mod = np.zeros(HOURS)
        n = 0
        for code, bp in bplants.items():
            if bp.get("group") != GROUP or bp.get("nodata"):
                continue
            cap = float(bp.get("npl") or 0.0)
            cb = bp.get("campd")
            pp = pplants.get(str(code))
            if cap <= 0 or not cb or not pp or not pp.get("m"):
                continue
            act += series(cb, cap)
            mod += series(pp["m"], cap)
            n += 1
        if n == 0:
            years_out[str(year)] = {"plants_matched": 0}
            continue

        deficit = act - mod  # + = model short of measured
        # SHAPE-ONLY control: the matched CAMPD-gross plant subset is NOT the
        # C1 grid-delivered basis (coverage and gross-vs-net differ on BOTH
        # sides), so the LEVEL here is not the C1 cell. Rescaling the model
        # series to the measured annual total cancels every level/coverage
        # term and leaves the pure SHAPE deficit, which is what item 3 asks.
        mod_n = mod * (act.sum() / mod.sum())
        deficit_shape = act - mod_n

        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        dem = sysf.groupby("hour")["demand"].sum().reindex(range(HOURS)).to_numpy(float)
        cls = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
        cls = cls[cls["pass"] == "P1"]
        by_class = {k: g.set_index("hour")["mw"].reindex(range(HOURS)).fillna(0.0).to_numpy(float)
                    for k, g in cls.groupby("klass")}

        p = actual_zone_price(year)["MISO-Indiana"].to_numpy(float)
        ok = np.isfinite(p)
        order = np.argsort(p[ok], kind="stable")
        idx = np.arange(HOURS)[ok]
        parts = np.array_split(order, 10)

        dec = []
        for i, part in enumerate(parts):
            h = idx[part]
            dec.append({
                "decile": i + 1,
                "mean_price": round(float(p[h].mean()), 2),
                "mean_deficit_mw": round(float(deficit[h].mean()), 1),
                "deficit_TWh": round(float(deficit[h].sum() / 1e6), 4),
                "model_cc_mw": round(float(mod[h].mean()), 1),
                "measured_cc_mw": round(float(act[h].mean()), 1),
                "shape_deficit_mw": round(float(deficit_shape[h].mean()), 1),
                "deficit_pct_of_measured": round(
                    float(100 * deficit[h].mean() / act[h].mean()), 2),
            })

        hod = np.arange(HOURS) % 24
        hod_def = [round(float(deficit[hod == h].mean()), 1) for h in range(24)]

        # what the model runs in the worst-deficit hours vs the rest
        thr = np.quantile(deficit, 0.9)
        hi = deficit >= thr
        comp = {}
        for k, v in by_class.items():
            comp[k] = round(float(v[hi].mean() - v[~hi].mean()), 1)
        comp = dict(sorted(comp.items(), key=lambda kv: -abs(kv[1]))[:8])

        years_out[str(year)] = {
            "plants_matched": n,
            "measured_TWh": round(float(act.sum() / 1e6), 3),
            "model_TWh": round(float(mod.sum() / 1e6), 3),
            "residual_TWh": round(float((mod - act).sum() / 1e6), 3),
            "basis_warning": (
                "matched CAMPD-gross plant subset; NOT the C1 grid-delivered "
                "cell (2023 C1 reads -6.445 TWh). Use the shape columns."),
            "shape_deficit_range_mw": [
                round(float(min(d["shape_deficit_mw"] for d in dec)), 1),
                round(float(max(d["shape_deficit_mw"] for d in dec)), 1),
            ],
            "hours_model_short_pct": round(float(100 * (deficit > 0).mean()), 1),
            "deficit_p90_mw": round(float(np.quantile(deficit, 0.9)), 1),
            "share_of_deficit_in_top_decile_of_deficit_pct": round(
                float(100 * deficit[hi].sum() / deficit[deficit > 0].sum()), 1),
            "by_price_decile": dec,
            "by_hour_of_day_mean_deficit_mw": hod_def,
            "mean_demand_hi_vs_lo_mw": round(float(dem[hi].mean() - dem[~hi].mean()), 1),
            "model_class_mw_hi_minus_lo": comp,
        }

    report["years"] = years_out
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {OUT}\n")
    for year in YEARS:
        y = years_out[str(year)]
        if not y.get("plants_matched"):
            print(f"{year}: no matched plants"); continue
        print(f"===================== {year}  {GROUP} =====================")
        print(f"  {y['plants_matched']} plants matched;  measured {y['measured_TWh']:.3f}"
              f"  model {y['model_TWh']:.3f}  residual {y['residual_TWh']:+.3f} TWh")
        print(f"  model is SHORT in {y['hours_model_short_pct']:.1f} % of hours;"
              f" the worst decile of hours carries"
              f" {y['share_of_deficit_in_top_decile_of_deficit_pct']:.1f} % of all shortfall")
        print(f"  LEVEL WARNING: {y['basis_warning']}")
        print(f"  {'dec':>4} {'price':>8} {'meas MW':>9} {'model MW':>9} {'raw def':>9}"
              f" {'%meas':>7} {'SHAPE def':>10}")
        for d in y["by_price_decile"]:
            print(f"  {d['decile']:>4} {d['mean_price']:>8.2f} {d['measured_cc_mw']:>9.0f}"
                  f" {d['model_cc_mw']:>9.0f} {d['mean_deficit_mw']:>9.0f}"
                  f" {d['deficit_pct_of_measured']:>7.1f} {d['shape_deficit_mw']:>+10.0f}")
        h = y["by_hour_of_day_mean_deficit_mw"]
        print(f"  hour-of-day deficit MW: min {min(h):.0f} (h{h.index(min(h))})"
              f"  max {max(h):.0f} (h{h.index(max(h))})")
        print(f"  in the worst-deficit decile of hours the model runs (MW vs other hours):")
        for k, v in y["model_class_mw_hi_minus_lo"].items():
            print(f"      {k:<12} {v:+9.0f}")
        print(f"      (demand there is {y['mean_demand_hi_vs_lo_mw']:+.0f} MW vs other hours)")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
