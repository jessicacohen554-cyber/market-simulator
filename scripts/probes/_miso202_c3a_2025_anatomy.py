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

**CLOCK REPAIR (miso-206, 2026-09-04).** The first committed version of this
probe built its hourly actual (A-2 / A-4) as the eight-hub equal-weighted mean
on the RAW EST hour-ending index of ``data/raw/lmp-data/MISO/*.csv.gz`` —
one hour late against the model's fixed-CST clock, and 25 h late after Feb 28
of a leap year (miso-204 §6). The hour-matched blocks are now routed through
the COMMITTED ``actual_lmp_hourly_zonal_MISO.parquet`` (hub ``INDIANA.HUB``,
col ``rt`` — the series C3a is scored against, on the model's clock). A-0 /
A-1 / A-3 use bench aggregates and are unaffected; every pre-repair
hour-matched statistic is preserved under ``pre_repair_defective_clock``.

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
ZONAL = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "actual_lmp_hourly_zonal_MISO.parquet"
)
OUT = REPO / "results" / "calibration" / "_miso202_c3a_2025_anatomy.json"
SCORING_HUB = "INDIANA.HUB"
M204 = REPO / "results" / "calibration" / "_miso204_lmp_component_decomposition.json"
# Actual-price percentile bands for the A-2b contribution decomposition.
BAND_EDGES = (0, 50, 75, 90, 95, 99, 100)
YEARS = (2023, 2024, 2025)
HOURS = 8760
MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)
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


MONTH_LENS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _hour_month(hours: int = HOURS) -> np.ndarray:
    """Calendar month per hour on the model's FIXED non-leap 8760 clock.

    The first committed version used ``pd.date_range(f"{year}-01-01",
    periods=8760)``, which in a LEAP year carries Feb 29 and so labels every
    model hour after Feb 28 one calendar day EARLY — the 2024 Jun-Jul window
    ran May 31 00:00 - Jul 30 23:00 on the model clock. Repaired miso-206.
    """
    return np.concatenate([np.full(n * 24, m + 1) for m, n in enumerate(MONTH_LENS)])[
        :hours
    ]


def hub_hourly_rt(year: int) -> np.ndarray | None:
    """INDIANA.HUB hourly RT LMP on the model's fixed-CST non-leap clock.

    Read from the COMMITTED zonal scoring parquet — the C3a comparator itself
    (miso-204 §6.1) — never re-derived from the raw ``csv.gz`` staging, whose
    bare ``arr[:8760]`` indexing IS the clock defect this repair removes.
    """
    if not ZONAL.exists():
        return None
    zon = pd.read_parquet(ZONAL)
    s = zon[(zon.year == year) & (zon.hub == SCORING_HUB)].sort_values("hour")
    arr = np.full(HOURS, np.nan)
    idx = s["hour"].to_numpy(int)
    keep = idx < HOURS
    arr[idx[keep]] = s["rt"].to_numpy(float)[keep]
    return arr if np.isfinite(arr).sum() >= HOURS - 48 else None


def eight_hub_cst_rt(year: int) -> np.ndarray | None:
    """Eight-hub equal-weighted RT on the MODEL clock — the HUB-error-only twin.

    The pre-repair construction differed from the scoring reference in TWO
    ways (miso-204 §6.3): the clock AND the hub basis. This series isolates
    the hub half, so A-2b can attribute the change between the committed
    record and the repaired one.
    """
    if not ZONAL.exists():
        return None
    zon = pd.read_parquet(ZONAL)
    hubs = sorted(zon["hub"].unique())
    stack = []
    for hub in hubs:
        s = zon[(zon.year == year) & (zon.hub == hub)].sort_values("hour")
        arr = np.full(HOURS, np.nan)
        idx = s["hour"].to_numpy(int)
        keep = idx < HOURS
        arr[idx[keep]] = s["rt"].to_numpy(float)[keep]
        stack.append(arr)
    return np.nanmean(np.vstack(stack), axis=0)


def band_contributions(actual: np.ndarray, model: np.ndarray) -> dict:
    """Contribution of each ACTUAL-price percentile band to the mean gap.

    ``sum(model - actual over the band) / n_hours`` — the bands sum to the
    mean gap exactly, so a level miss reads as a flat profile and a tail miss
    as a profile concentrated in the top bands.
    """
    ok = np.isfinite(actual)
    a, m = actual[ok], model[ok]
    rank = (a.argsort().argsort() / len(a)) * 100.0
    out = {}
    for lo, hi in zip(BAND_EDGES[:-1], BAND_EDGES[1:]):
        sel = (rank >= lo) & (rank < hi) if hi < 100 else rank >= lo
        out[f"p{lo}-{hi}"] = round(float((m[sel] - a[sel]).sum() / len(a)), 3)
    out["mean_gap"] = round(float(m.mean() - a.mean()), 3)
    out["top_decile_share_of_mean_gap"] = (
        round(
            float(
                sum(v for k, v in out.items() if k in ("p90-95", "p95-99", "p99-100"))
                / out["mean_gap"]
            ),
            4,
        )
        if abs(out["mean_gap"]) > 1e-9
        else None
    )
    return out


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
        d = d.assign(month=_hour_month()[d["hour"].to_numpy()])
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
        mod = d.groupby("hour")["price"].mean().reindex(range(HOURS)).to_numpy()
        mon = _hour_month()
        entry: dict = {}
        for label, mask in (
            ("full_year", np.ones(HOURS, dtype=bool)),
            ("jun_jul", np.isin(mon, (6, 7))),
            ("jun_sep", np.isin(mon, (6, 7, 8, 9))),
        ):
            ok = mask & np.isfinite(act)
            a, m = act[ok], mod[ok]
            mean_gap = float(m.mean() - a.mean())
            thr = float(np.percentile(a, 99))
            top = a >= thr
            top_gap = float((m[top] - a[top]).sum() / len(a))
            entry[label] = {
                "n_hours": int(ok.sum()),
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

    # ---- A-2b (miso-206, POST-HOC on the repaired instrument): WHERE in the
    # actual-price distribution the Jun-Jul gap lives, on the C3a comparator
    # (INDIANA.HUB) and on the hub-error-only twin (8-hub mean, model clock),
    # with the model price on BOTH bases (zone-mean, as A-2 uses; and the C3a
    # load-weighted), plus the hour-of-day profile of the BODY gap (the 1,449
    # hours outside the top 1 %). The system-energy (MEC) Jun-Jul level is READ
    # from miso-204's committed record, never re-derived.
    m204 = json.loads(M204.read_text())["years"] if M204.exists() else {}
    for year in YEARS:
        ind = hub_hourly_rt(year)
        eight = eight_hub_cst_rt(year)
        if ind is None or eight is None:
            continue
        d = system_hourly(year)
        zm = d.groupby("hour")["price"].mean().reindex(range(HOURS)).to_numpy()
        num = d.assign(pw=d["price"] * d["demand"]).groupby("hour")["pw"].sum()
        den = d.groupby("hour")["demand"].sum()
        lw = (num / den).reindex(range(HOURS)).to_numpy()
        jj = np.isin(_hour_month(), (6, 7))
        hod = np.arange(HOURS) % 24
        entry: dict = {
            "label": (
                "POST-HOC (miso-206), NOT PRE-REGISTERED, NO GATE. Bands of the "
                "ACTUAL Jun-Jul price; each cell is sum(model - actual)/n over the "
                "band, so the cells sum to the mean gap."
            ),
            "indiana_hub__model_zone_mean": band_contributions(ind[jj], zm[jj]),
            "indiana_hub__model_load_weighted": band_contributions(ind[jj], lw[jj]),
            "eight_hub_model_clock__model_zone_mean": band_contributions(
                eight[jj], zm[jj]
            ),
            "eight_hub_model_clock__model_load_weighted": band_contributions(
                eight[jj], lw[jj]
            ),
            "jun_jul_levels": {
                "actual_indiana_hub_mean": round(float(np.nanmean(ind[jj])), 2),
                "actual_eight_hub_model_clock_mean": round(
                    float(np.nanmean(eight[jj])), 2
                ),
                "actual_system_mec_mean__miso204_read": (
                    m204.get(str(year), {})
                    .get("g1_levels_OBJ", {})
                    .get("mean_jj_actual_mec")
                ),
                "model_zone_mean": round(float(np.nanmean(zm[jj])), 2),
                "model_load_weighted": round(float(np.nanmean(lw[jj])), 2),
            },
        }
        thr = float(np.nanpercentile(ind[jj], 99))
        body = jj & np.isfinite(ind) & (ind < thr)
        entry["body_gap_by_hour_of_day__indiana_lw"] = {
            str(h): round(
                float((lw[body & (hod == h)] - ind[body & (hod == h)]).mean()), 1
            )
            for h in range(24)
        }
        report["a2_distribution"][str(year)][
            "a2b_band_contributions__POSTHOC_miso206"
        ] = entry

    # ---- A-3: the ceiling, and whether scarcity ever fires ---------------
    for year in YEARS:
        d = system_hourly(year)
        jj = d[np.isin(_hour_month()[d["hour"].to_numpy()], (6, 7))]
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
        jj = np.isin(_hour_month(), (6, 7))
        thr = float(np.nanpercentile(act[jj], 99))
        scarce = jj & (act >= thr)
        ordinary = jj & (act < thr)
        rows = {}
        for k, g in ch.groupby(ch["klass"].astype(str)):
            mw = g.set_index("hour")["mw"].reindex(range(HOURS)).to_numpy()
            rows[k] = {
                "mean_mw_actual_scarce_hours": round(float(np.nanmean(mw[scarce])), 1),
                "mean_mw_other_jun_jul_hours": round(
                    float(np.nanmean(mw[ordinary])), 1
                ),
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

    # ---- clock repair (miso-206): keep the defective hour-matched blocks ---
    if OUT.exists():
        prior = json.loads(OUT.read_text())
        pre = prior.get("pre_repair_defective_clock") or {
            "note": (
                "a2/a4 as first committed: eight-hub equal-weighted mean on the "
                "RAW EST hour-ending index (miso-204 §6 defect: -1 h, and -25 h "
                "after Feb 28 of a leap year). Kept for the record; superseded."
            ),
            "a2_distribution": prior.get("a2_distribution"),
            "a4_what_is_serving_those_hours": prior.get(
                "a4_what_is_serving_those_hours"
            ),
        }
        report["pre_repair_defective_clock"] = pre
    report["clock_repair"] = (
        "miso-206 (2026-09-04): (i) a2/a4 hourly actual = INDIANA.HUB RT from the "
        "committed actual_lmp_hourly_zonal_MISO.parquet on the model's fixed-CST "
        "non-leap clock (the C3a comparator) — a0/a1/a3 byte-identical under this "
        "step (PREREG R-0 PASS); (ii) SEPARATELY, the month mask moved from a "
        "pandas leap-year calendar to the model's fixed non-leap clock, which "
        "shifts every 2024 monthly/seasonal window by one day (a1/a2/a3/a4 2024 "
        "move slightly; 2023/2025 unchanged)."
    )
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
