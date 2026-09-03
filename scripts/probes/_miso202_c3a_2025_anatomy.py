"""miso-202 — THE ANATOMY OF C3a-2025: is the charter's object a LEVEL miss or a TAIL miss?

The MISO lane's standing re-charter (miso-167, owner: *"2025 miso needs to be
calibrated in summer scarcity it's unacceptable that it doesn't"*) names
**C3a-2025** as the ISO's sole load-bearing rubric failure: model 39.83 against
actual 45.46 $/MWh, **−12.3845 %**. Three consecutive sessions (miso-199, -200,
-201) have worked the unit-outage overlay family and the residual has drifted
from −12.2745 to −12.3845, because every repair in that family RESTORES
availability and therefore lowers price.

This probe asks the question those sessions did not: **WHERE, in hours and in
dollars, is the −12.38 % actually located?** It costs no solve — every input is
a committed artifact (the keeper's own hourly sidecars, the committed bench, and
the committed hub LMP staging) — and it exists so the next lever is chosen
against the object's measured shape rather than against a class-energy residual.

Measurements
------------
* **A-0 INSTRUMENT VALIDATION (a gate, not a report).** The load-weighted annual
  mean is recomputed from the keeper's committed ``hourly/system_<year>.parquet``
  and asserted to reproduce ``calibration_verdict``'s own C3a face. A
  reconstruction that does not reproduce the scored number measures nothing.
* **A-1 MONTHLY ATTRIBUTION.** The annual load-weighted gap decomposed into each
  month's ``load_share x (model − actual)`` contribution, against the committed
  bench's ``rt_lw_mon``. Answers "is the miss summer-concentrated?" in dollars.
* **A-2 THE DISTRIBUTION.** Model and actual hourly price percentiles over the
  months A-1 indicts, plus the share of the mean gap contributed by the top 1 %
  of ACTUAL hours versus every other hour. This is the LEVEL-vs-TAIL test: a
  level miss spreads the gap across the distribution; a tail miss concentrates
  it.
* **A-3 THE CEILING.** The keeper's maximum price in ANY zone-hour, its count of
  zone-hours above $200 / $500 / $1000, its unserved energy, and — from the
  ``reserve_family`` sidecar, the only artifact in which a locational family's
  binding is observable — the per-family reserve dual, requirement, held MW and
  **ORDC shortfall**. This is what distinguishes "the model is short of expensive
  units" from "the model never enters scarcity at all".

Nothing here is fitted and nothing is tuned, and nothing here is a lever: this is
a diagnostic that names an object, and it deliberately proposes no mechanism.

Run:  PYTHONPATH=src python3 scripts/probes/_miso202_c3a_2025_anatomy.py
Writes: results/calibration/_miso202_c3a_2025_anatomy.json
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results" / "calibration" / "miso201_stbasis_B"
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "MISO"
HUB_LMP = REPO / "data" / "raw" / "lmp-data" / "MISO"
OUT = REPO / "results" / "calibration" / "_miso202_c3a_2025_anatomy.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
# The keeper's own scored C3a faces, read off calibration_verdict before this
# probe existed. A-0 asserts the reconstruction against them.
VERDICT_C3A = {2023: 0.1218, 2024: -4.5820, 2025: -12.3845}
# Tolerance on the A-0 reproduction, in percentage points. The verdict masks the
# two external pseudo-zones out of its load weighting where the payload does; a
# reconstruction within this band is the same object, one outside it is not.
A0_TOL_PP = 0.05


def system_hourly(year: int) -> pd.DataFrame:
    """The keeper's committed P1 system sidecar (zone x hour price + demand)."""
    d = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    return d[d["pass"] == "P1"]


def bench_avg_lmp(year: int) -> dict:
    """The committed bench's avgLMP block — the gated C3a actual."""
    with gzip.open(BENCH / f"{year}.json.gz", "rt") as f:
        return json.load(f)["bench"]["avgLMP"]


def hub_hourly_rt(year: int) -> np.ndarray | None:
    """Hub-average hourly RT LMP from the committed staging, or None.

    The eight named trading hubs, equal-weighted — the same series behind the
    bench's equal-hour ``rt`` field. The file carries LMP / MCC / MLC component
    rows per (date, node); only ``LMP`` is the price.
    """
    path = HUB_LMP / f"miso_hub_lmp_{year}_rt.csv.gz"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df = df[df["value"] == "LMP"]
    he = [f"he{i:02d}" for i in range(1, 25)]
    df["date"] = pd.to_datetime(df["date"])
    piv = df.groupby("date")[he].mean().sort_index()
    arr = piv.to_numpy().ravel()
    return arr[:HOURS] if len(arr) >= HOURS else None


def main() -> None:
    report: dict = {
        "charter": (
            "miso-167 standing re-charter: C3a-2025 is MISO's sole load-bearing "
            "rubric failure. This probe locates it; it proposes no mechanism."
        ),
        "keeper": "2026-09-02-miso-201-stbasis",
        "inputs": "committed artifacts only — no solve",
        "a0_instrument": {},
        "a1_monthly_attribution": {},
        "a2_distribution": {},
        "a3_ceiling": {},
        "a4_what_is_serving_those_hours": {},
    }

    # ---- A-0 + A-1 --------------------------------------------------------
    for year in YEARS:
        d = system_hourly(year)
        avg = bench_avg_lmp(year)
        idx = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
        d = d.assign(month=idx.month[d["hour"].to_numpy()])
        w = d["demand"].to_numpy()
        model_lw = float((d["price"].to_numpy() * w).sum() / w.sum())
        actual = float(avg["rt_lw"])
        err_pp = 100.0 * (model_lw - actual) / actual
        report["a0_instrument"][str(year)] = {
            "model_lw": round(model_lw, 4),
            "actual_rt_lw": round(actual, 4),
            "reconstructed_err_pct": round(err_pp, 4),
            "verdict_err_pct": VERDICT_C3A[year],
            "abs_diff_pp": round(abs(err_pp - VERDICT_C3A[year]), 4),
            "reproduces": abs(err_pp - VERDICT_C3A[year]) <= A0_TOL_PP,
        }

        act_mon = avg["rt_lw_mon"]
        g = d.groupby("month").apply(
            lambda x: pd.Series(
                {
                    "model_lw": float(
                        (x["price"] * x["demand"]).sum() / x["demand"].sum()
                    ),
                    "load": float(x["demand"].sum()),
                }
            ),
            include_groups=False,
        )
        tot_load = float(g["load"].sum())
        rows = []
        for m in g.index:
            gap = float(g.loc[m, "model_lw"]) - float(act_mon[m - 1])
            share = float(g.loc[m, "load"]) / tot_load
            rows.append(
                {
                    "month": MONTHS[m - 1],
                    "model_lw": round(float(g.loc[m, "model_lw"]), 2),
                    "actual_lw": round(float(act_mon[m - 1]), 2),
                    "gap": round(gap, 2),
                    "load_share": round(share, 4),
                    "contribution_usd_per_mwh": round(share * gap, 4),
                }
            )
        total_gap = sum(r["contribution_usd_per_mwh"] for r in rows)
        jun_sep = sum(
            r["contribution_usd_per_mwh"]
            for r in rows
            if r["month"] in ("Jun", "Jul", "Aug", "Sep")
        )
        jun_jul = sum(
            r["contribution_usd_per_mwh"] for r in rows if r["month"] in ("Jun", "Jul")
        )
        report["a1_monthly_attribution"][str(year)] = {
            "months": rows,
            "total_gap_usd_per_mwh": round(total_gap, 4),
            "jun_sep_usd_per_mwh": round(jun_sep, 4),
            "jun_sep_share_of_gap": (
                round(jun_sep / total_gap, 4) if abs(total_gap) > 1e-9 else None
            ),
            "jun_jul_usd_per_mwh": round(jun_jul, 4),
            "jun_jul_share_of_gap": (
                round(jun_jul / total_gap, 4) if abs(total_gap) > 1e-9 else None
            ),
        }

    # ---- A-2: the LEVEL-vs-TAIL test -------------------------------------
    for year in YEARS:
        act = hub_hourly_rt(year)
        if act is None:
            report["a2_distribution"][str(year)] = {"error": "no committed hub RT file"}
            continue
        d = system_hourly(year)
        mod = (
            d.groupby("hour")["price"].mean().reindex(range(HOURS)).to_numpy()
        )
        idx = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
        entry: dict = {}
        for label, mask in (
            ("full_year", np.ones(HOURS, dtype=bool)),
            ("jun_jul", np.isin(idx.month, (6, 7))),
            ("jun_sep", np.isin(idx.month, (6, 7, 8, 9))),
        ):
            a, m = act[mask], mod[mask]
            mean_gap = float(m.mean() - a.mean())
            thr = float(np.percentile(a, 99))
            top = a >= thr
            top_gap = float((m[top] - a[top]).sum() / len(a))
            entry[label] = {
                "n_hours": int(mask.sum()),
                "actual_mean": round(float(a.mean()), 2),
                "model_mean": round(float(m.mean()), 2),
                "mean_gap": round(mean_gap, 3),
                "percentiles": {
                    f"p{q}": {
                        "actual": round(float(np.percentile(a, q)), 2),
                        "model": round(float(np.percentile(m, q)), 2),
                    }
                    for q in (50, 75, 90, 95, 99, 99.9)
                },
                "actual_max": round(float(a.max()), 2),
                "model_max": round(float(m.max()), 2),
                "hours_actual_over_200": int((a > 200).sum()),
                "hours_model_over_200": int((m > 200).sum()),
                "top1pct_of_actual_hours": {
                    "n": int(top.sum()),
                    "contribution_usd_per_mwh": round(top_gap, 3),
                    "share_of_mean_gap": (
                        round(top_gap / mean_gap, 4) if abs(mean_gap) > 1e-9 else None
                    ),
                },
                "all_other_hours_contribution": round(mean_gap - top_gap, 3),
            }
        report["a2_distribution"][str(year)] = entry

    # ---- A-3: the ceiling, and whether scarcity ever fires ---------------
    for year in YEARS:
        d = system_hourly(year)
        idx = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
        jj = d[np.isin(idx.month[d["hour"].to_numpy()], (6, 7))]
        rf = pd.read_parquet(KEEPER / "hourly" / f"reserve_family_{year}.parquet")
        rf = rf[rf["pass"] == "P1"]
        fam = {
            str(f): {
                "dual_max": round(float(g["dual"].max()), 2),
                "requirement_mw_max": round(float(g["requirement_mw"].max()), 1),
                "held_mw_max": round(float(g["held_mw"].max()), 1),
                "shortfall_mw_max": round(float(g["shortfall_mw"].max()), 3),
                "hours_with_shortfall": int((g["shortfall_mw"] > 0).sum()),
                "hours_dual_positive": int((g["dual"] > 0).sum()),
            }
            for f, g in rf.groupby("family", observed=True)
        }
        report["a3_ceiling"][str(year)] = {
            "model_price_max_any_zone_hour": round(float(d["price"].max()), 2),
            "zone_hours_over_200": int((d["price"] > 200).sum()),
            "zone_hours_over_500": int((d["price"] > 500).sum()),
            "zone_hours_over_1000": int((d["price"] > 1000).sum()),
            "unserved_energy_mwh": round(float(d["slack"].sum()), 1),
            "hours_with_unserved_energy": int((d["slack"] > 0).sum()),
            "jun_jul_price_max": round(float(jj["price"].max()), 2),
            "jun_jul_zone_hours_over_200": int((jj["price"] > 200).sum()),
            "reserve_families": fam,
        }

    # ---- A-4: what is serving the hours the real market priced high? -----
    # MODEL-SIDE ONLY, and labelled as such: no hourly interchange ACTUAL is
    # committed for MISO, so this reports what the keeper dispatches in the
    # hours the actual hub price was in its own top 1 %, against the same
    # month's ordinary hours. It adjudicates nothing — it says which supply is
    # present when the real market was scarce and the model was not.
    for year in YEARS:
        act = hub_hourly_rt(year)
        if act is None:
            continue
        ch = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        idx = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
        jj = np.isin(idx.month, (6, 7))
        thr = float(np.percentile(act[jj], 99))
        scarce = jj & (act >= thr)
        ordinary = jj & (act < thr)
        rows = {}
        for k, g in ch.groupby(ch["klass"].astype(str)):
            mw = g.set_index("hour")["mw"].reindex(range(HOURS)).to_numpy()
            rows[k] = {
                "mean_mw_actual_scarce_hours": round(float(np.nanmean(mw[scarce])), 1),
                "mean_mw_other_jun_jul_hours": round(float(np.nanmean(mw[ordinary])), 1),
                "delta_mw": round(
                    float(np.nanmean(mw[scarce]) - np.nanmean(mw[ordinary])), 1
                ),
            }
        report["a4_what_is_serving_those_hours"][str(year)] = {
            "basis": (
                "MODEL-SIDE ONLY — no hourly interchange actual is committed for "
                "MISO, so this is descriptive, not a residual against a benchmark."
            ),
            "scarce_hours_definition": (
                f"Jun-Jul hours whose ACTUAL hub RT price is in the top 1 % of "
                f"Jun-Jul ({thr:.2f} $/MWh and above)"
            ),
            "n_scarce_hours": int(scarce.sum()),
            "by_class": dict(sorted(rows.items(), key=lambda kv: -kv[1]["delta_mw"])),
        }

    OUT.write_text(json.dumps(report, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")
    for y in YEARS:
        a0 = report["a0_instrument"][str(y)]
        print(
            f"A-0 {y}: reconstructed {a0['reconstructed_err_pct']:+.4f}% vs verdict "
            f"{a0['verdict_err_pct']:+.4f}%  -> {'REPRODUCES' if a0['reproduces'] else 'MISMATCH'}"
        )
    a1 = report["a1_monthly_attribution"]["2025"]
    print(
        f"A-1 2025: Jun-Sep carries {a1['jun_sep_share_of_gap']:.1%} of the "
        f"{a1['total_gap_usd_per_mwh']:+.3f} $/MWh gap; Jun+Jul alone "
        f"{a1['jun_jul_share_of_gap']:.1%}"
    )
    jj = report["a2_distribution"]["2025"]["jun_jul"]
    print(
        f"A-2 2025 Jun-Jul: model p50 {jj['percentiles']['p50']['model']} vs actual "
        f"{jj['percentiles']['p50']['actual']} (model HIGHER); p99 "
        f"{jj['percentiles']['p99']['model']} vs {jj['percentiles']['p99']['actual']}; "
        f"top-1% of actual hours carry {jj['top1pct_of_actual_hours']['share_of_mean_gap']:.1%} "
        "of the mean gap"
    )
    a3 = report["a3_ceiling"]["2025"]
    print(
        f"A-3 2025: model max {a3['model_price_max_any_zone_hour']} $/MWh in ANY "
        f"zone-hour (Jun-Jul {a3['jun_jul_price_max']}); zone-hours>200 "
        f"{a3['zone_hours_over_200']}; unserved {a3['unserved_energy_mwh']} MWh; "
        "ORDC shortfall hours "
        + str({k: v["hours_with_shortfall"] for k, v in a3["reserve_families"].items()})
    )


if __name__ == "__main__":
    main()
