"""ERCOT-172 Phase 0 (NO LP): attribute the 2024 maintenance-season shed hours.

Charter: mechanism-testing-matrix §5.1 item 15 (the H4 item-4 object named in
``FINDING-ercot166-2023-diagnosis-triage-2026-08-05.md`` §5/§7), and the standing
gate on the ercot-167 SOC-reserve re-gate. Decision rule pre-registered in
``docs/PRECOMMIT-ercot172-maintenance-season-availability-2026-08-06.md`` before
any capture ran; every threshold below is read from that document, never
recomputed here.

The keeper (``2026-08-05-run168b-year-curves``) sheds load in exactly two 2024
hours — 2024-04-28 19:00 and 2024-05-08 19:00 CST — both at VOLL, on days ERCOT
did not shed. This probe attributes that shortage, at MW grain, to the measured
availability instruments, and reports which instrument disagrees with which.

Construction (all of it measured; no fitted value anywhere):

* **Captures A/B** — ``ercot148_availability_capture`` run twice as a
  subprocess, unmodified: A = the keeper config verbatim, B = the same config
  with only ``ercot_dam_availability_{coal,gas}_event_cap=false``. The event cap
  is a pure ``np.minimum``, so ``E = A_pin − A_final`` is the capability it
  removed, exactly.
* **G-FOOT / G-EXACT / G-SEAM** — the precommit's three construction gates.
* **L1 / L2** — the coverage licence on the per-plant attribution.
* **K-COP / K-CEMS** — the two certificates, reported per plant in both
  directions.
* **The ceiling decomposition** — ``f_ceiling = f_window × f_partial`` against
  the COP declaration and against the plant's own contemporaneous CEMS output.

Usage:
    python scripts/probes/ercot172_maintenance_availability_phase0.py \
        [--bundle results/calibration/ercot168_yearcurves_B] \
        [--work <scratch dir>] [--out results/calibration/ercot172_maintenance_availability.json]

Captures are cached in ``--work``; delete them to force a re-capture. No LP
solve, no network, no year outside 2023-2025 read (rule 22 ``[R-HOLDOUT]``:
2024 object, 2023/2025 untouched here).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import CAMPD_BINS_CSV, RAW_DATA_DIR  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    ercot_thermal_dam_availability_plant_series,
    partial_outage_derate_factors,
    unit_outage_derate_factors,
)

YEAR = 2024
SCOPE = ("COAL", "CC_REGULAR", "ST_GAS", "CT_PEAKER")  # fleet/arrays.py _evcap_scope
# The object, enumerated in the precommit §0 from the keeper's committed sidecars.
SHED = {2827: ("2024-04-28 19:00", 565.1), 3067: ("2024-05-08 19:00", 550.3)}
# Pre-registered bars (precommit §3a/§4) — read, never recomputed.
BAR_L1, BAR_L2, BAR_SHARE, BAR_PERR, BAR_FOOT = 0.90, 0.10, 0.60, 0.60, 1e-3
CAPTURE = REPO / "scripts" / "probes" / "ercot148_availability_capture.py"


def model_clock(year: int) -> pd.DatetimeIndex:
    """The model's fixed non-leap hourly clock for ``year`` (Feb 29 dropped)."""
    return pd.DatetimeIndex(
        [
            t
            for t in pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
            if not (t.month == 2 and t.day == 29)
        ][:8760]
    )


def run_captures(bundle: Path, work: Path) -> tuple[Path, Path]:
    """Produce (A, B) availability captures for ``YEAR``, cached in ``work``."""
    work.mkdir(parents=True, exist_ok=True)
    a, b = work / f"avail_{YEAR}_A.npz", work / f"avail_{YEAR}_B.npz"
    for out, extra in (
        (a, []),
        (
            b,
            [
                "--set",
                "ercot_dam_availability_coal_event_cap=false",
                "--set",
                "ercot_dam_availability_gas_event_cap=false",
            ],
        ),
    ):
        if out.exists():
            print(f"  cached {out.name}")
            continue
        cmd = [
            sys.executable,
            str(CAPTURE),
            str(bundle),
            "--year",
            str(YEAR),
            "--out",
            str(out),
            *extra,
        ]
        print(f"  capturing {out.name} ...")
        subprocess.run(cmd, check=True, cwd=str(REPO), stdout=subprocess.DEVNULL)
    return a, b


def g_foot() -> dict:
    """G-FOOT — the site-hourly parquet must reproduce the committed class-hour CSV."""
    sh = pd.read_parquet(
        RAW_DATA_DIR / "ercot-thermal-dam-availability-site-hourly.parquet",
        columns=["date", "class", "he", "live_mw", "rating_mw"],
    )
    sh["date"] = pd.to_datetime(sh["date"])
    sh = sh[sh.date.dt.year == YEAR]
    agg = sh.groupby(["class", "date", "he"], as_index=False)[
        ["live_mw", "rating_mw"]
    ].sum()
    agg["frac_site"] = np.where(
        agg.rating_mw > 0, agg.live_mw / agg.rating_mw, np.nan
    )
    ch = pd.read_csv(RAW_DATA_DIR / "ercot-thermal-dam-availability-hourly.csv")
    ch["date"] = pd.to_datetime(ch["date"])
    ch = ch[ch.date.dt.year == YEAR]
    long = ch.melt(
        id_vars=["date", "class"],
        value_vars=[f"he{h:02d}" for h in range(1, 25)],
        var_name="hecol",
        value_name="frac_csv",
    )
    long["he"] = long.hecol.str[2:].astype(int)
    m = agg.merge(long[["date", "class", "he", "frac_csv"]], on=["class", "date", "he"])
    m = m.dropna(subset=["frac_site", "frac_csv"])
    d = (m.frac_site - m.frac_csv).abs()
    share = float((d <= BAR_FOOT).mean())
    return {
        "class_hours": int(len(m)),
        "share_within_1e-3": share,
        "max_abs_delta": float(d.max()),
        "bar": 0.99,
        "pass": bool(share >= 0.99),
    }


def cems_by_plant_fuel() -> pd.DataFrame:
    """CAMPD TX hourly gross load, summed per (facility, coal?) on the model clock."""
    d = pd.read_parquet(
        RAW_DATA_DIR / "campd-unit-level" / f"TX_{YEAR}.parquet",
        columns=["facilityId", "primaryFuelInfo", "grossLoad", "date", "hour"],
    )
    d = d[~((d.date.dt.month == 2) & (d.date.dt.day == 29))].copy()
    d["fid"] = pd.to_numeric(d.facilityId, errors="coerce")
    d["gl"] = d.grossLoad.fillna(0.0)
    d["isCoal"] = d.primaryFuelInfo.astype(str).str.contains("Coal", na=False)
    d["h"] = (d.date.dt.dayofyear - 1 - (d.date.dt.month > 2).astype(int)) * 24 + d.hour
    return (
        d.groupby(["fid", "isCoal", "h"])["gl"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(columns=range(8760), fill_value=0.0)
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/ercot168_yearcurves_B")
    ap.add_argument("--work", default="/tmp/ercot172")
    ap.add_argument(
        "--out", default="results/calibration/ercot172_maintenance_availability.json"
    )
    args = ap.parse_args()

    rec: dict = {
        "session": "ercot-172",
        "phase": 0,
        "lp_solved": False,
        "year": YEAR,
        "bundle": args.bundle,
        "precommit": "docs/PRECOMMIT-ercot172-maintenance-season-availability-2026-08-06.md",
        "object": {
            str(h): {"ts_cst": ts, "shed_mw": mw} for h, (ts, mw) in SHED.items()
        },
    }

    print("== G-FOOT ==")
    rec["G_FOOT"] = g_foot()
    print(f"   {rec['G_FOOT']}")

    print("== captures ==")
    pa, pb = run_captures(REPO / args.bundle, Path(args.work))
    A, B = np.load(pa, allow_pickle=True), np.load(pb, allow_pickle=True)
    for k in ("pmax", "plant_code", "group", "name"):
        assert (A[k] == B[k]).all(), f"fleet identity mismatch on {k}"
    aA, aB = A["availability"].astype(float), B["availability"].astype(float)
    grp, pmax, pc, nm = A["group"], A["pmax"], A["plant_code"], A["name"]
    ins = np.array([g in SCOPE for g in grp])

    bad = int(((aA > aB + 1e-9) & ins[:, None]).any(axis=1).sum())
    seam = float(np.abs(aA[~ins] - aB[~ins]).max()) if (~ins).any() else 0.0
    rec["G_EXACT"] = {"rows_violating": bad, "pass": bad == 0}
    rec["G_SEAM"] = {
        "out_of_scope_rows": int((~ins).sum()),
        "max_abs_delta": seam,
        "pass": seam == 0.0,
    }
    print(f"== G-EXACT {rec['G_EXACT']} ==\n== G-SEAM {rec['G_SEAM']} ==")

    win = unit_outage_derate_factors(YEAR, 8760, str(CAMPD_BINS_CSV), iso="ERCOT")
    part = partial_outage_derate_factors(YEAR, 8760)
    cop = ercot_thermal_dam_availability_plant_series(YEAR)
    cems = cems_by_plant_fuel()
    idx = model_clock(YEAR)

    rec["hours"] = {}
    for h, (ts, shed) in SHED.items():
        rows = []
        for p in sorted({int(x) for x in pc[ins]}):
            for cls in SCOPE:
                m = ins & (pc == p) & (grp == cls)
                if not m.any():
                    continue
                v_a = float((pmax[m] * aA[m, h]).sum())
                v_b = float((pmax[m] * aB[m, h]).sum())
                if v_b - v_a <= 1e-9:
                    continue
                pm = float(pmax[m].sum())
                fw = float(win[(p, cls)][h]) if (p, cls) in win else 1.0
                fq = float(part[p][h]) if p in part else 1.0
                ca = cop.get(p)
                fc = (
                    float(ca[h])
                    if (ca is not None and np.isfinite(ca[h]))
                    else None
                )
                key = (p, cls == "COAL")
                c = float(cems.loc[key][h]) if key in cems.index else 0.0
                # K-CEMS: did the plant operate within +/-7 days of the hour?
                lo, hi = max(0, h - 168), min(8760, h + 169)
                wmax = (
                    float(cems.loc[key][lo:hi].max()) if key in cems.index else 0.0
                )
                rows.append(
                    {
                        "plant_code": p,
                        "name": str(nm[pc == p][0]).split("[")[0].strip(),
                        "class": cls,
                        "pmax_mw": pm,
                        "avail_model_mw": v_a,
                        "avail_no_evcap_mw": v_b,
                        "E_mw": v_b - v_a,
                        "f_window": fw,
                        "f_partial": fq,
                        "f_ceiling": fw * fq,
                        "f_ceiling_min_rule": min(fw, fq),
                        "f_cop": fc,
                        "f_cems": c / pm if pm else None,
                        "cems_mw": c,
                        "impossible_mw": max(0.0, c - v_a),
                        "K_COP": bool(fc is not None and fc > 0.0),
                        "K_CEMS": bool(wmax > 0.02 * pm),
                        "ceiling_below_physical": bool(fw * fq < c / pm - 1e-6)
                        if pm
                        else False,
                    }
                )
        E = sum(r["E_mw"] for r in rows)
        named = [r for r in rows if r["E_mw"] >= 25.0]
        En = sum(r["E_mw"] for r in named)
        cov = sum(r["E_mw"] for r in rows if r["f_cop"] is not None)
        amb = sum(r["E_mw"] for r in rows if r["plant_code"] <= 0)
        rec["hours"][str(h)] = {
            "ts_cst": ts,
            "shed_mw": shed,
            "E_mw": E,
            "E_over_shed": E / shed,
            "E_named_mw": En,
            "E_named_over_E": En / E if E else None,
            "E_named_over_shed": En / shed,
            "L1_cop_resolvable": cov / E if E else None,
            "L2_ambiguous": amb / E if E else None,
            "L1_pass": bool(E and cov / E >= BAR_L1),
            "L2_pass": bool(E == 0 or amb / E <= BAR_L2),
            "share_pass": bool(E and En / E >= BAR_SHARE),
            "shed_pass": bool(En >= shed),
            "impossible_mw": sum(r["impossible_mw"] for r in rows),
            "plants": sorted(rows, key=lambda r: -r["E_mw"]),
        }

    # P-ERR: share of the two days' |price error| in hours where E(h) > 0.
    E_h = ((pmax[:, None] * (aB - aA)) * ins[:, None]).sum(axis=0)
    sysf = pd.read_parquet(
        REPO / args.bundle / "hourly" / f"system_{YEAR}.parquet"
    )
    sysf = sysf[sysf["pass"] == "P1"]
    pr = sysf.pivot_table(index="hour", columns="zone", values="price").to_numpy()
    dm = sysf.pivot_table(index="hour", columns="zone", values="demand").to_numpy()
    model = (pr * dm).sum(1) / dm.sum(1)
    act = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
    )
    act = act[act.year == YEAR]["rt"].to_numpy(float)
    err = np.abs(model - act)
    days = np.isin(idx.normalize(), [pd.Timestamp(ts).normalize() for ts, _ in SHED.values()])
    perr = float(err[days & (E_h > 0)].sum() / err[days].sum())
    rec["P_ERR"] = {
        "value": perr,
        "bar": BAR_PERR,
        "pass": perr >= BAR_PERR,
        "day_hours_with_E_positive": int((days & (E_h > 0)).sum()),
        "day_hours": int(days.sum()),
        "year_hours_with_E_positive": int((E_h > 0).sum()),
        "note": (
            "weak discriminator as pre-registered: the event cap binds somewhere in "
            "almost every hour of the year, so E(h)>0 is nearly always true"
        ),
    }

    # Rating-basis term R (precommit §2): ERCOT-declared MW vs the model's
    # post-pin MW, per class. Measured and reported; explicitly not this lane's
    # object — a material R re-points to the fleet-scope/crosswalk lane.
    sh = pd.read_parquet(
        RAW_DATA_DIR / "ercot-thermal-dam-availability-site-hourly.parquet",
        columns=["date", "class", "he", "live_mw", "rating_mw"],
    )
    sh["date"] = pd.to_datetime(sh["date"])
    sh = sh[sh.date.dt.year == YEAR]
    sh["ts"] = sh["date"] + pd.to_timedelta(sh["he"] - 1, unit="h")
    cop_mw = sh.groupby(["class", "ts"])[["live_mw", "rating_mw"]].sum()
    rec["R_rating_basis"] = {}
    for h, (ts, _) in SHED.items():
        per = {}
        for cls in SCOPE:
            try:
                row = cop_mw.loc[(cls, pd.Timestamp(ts))]
            except KeyError:
                continue
            m = ins & (grp == cls)
            per[cls] = {
                "cop_live_mw": float(row.live_mw),
                "cop_rating_mw": float(row.rating_mw),
                "model_pmax_mw": float(pmax[m].sum()),
                "A_pin_mw": float((pmax[m] * aB[m, h]).sum()),
                "R_mw": float(row.live_mw - (pmax[m] * aB[m, h]).sum()),
            }
        per["TOTAL_R_mw"] = sum(v["R_mw"] for v in per.values())
        rec["R_rating_basis"][str(h)] = per

    # Fleet-wide 2024 scale (CONTEXT ONLY, non-gating): plant-class-hours where
    # fuel-matched CEMS gross exceeds the model's ENTIRE available MW. This is
    # this session's own construction and is NOT the committed
    # `impossible plant-hours` metric of the ercot_thermal_dam_availability cell.
    excess = np.zeros(8760)
    n_ph = 0
    for p in sorted({int(x) for x in pc[ins]}):
        for cls in SCOPE:
            m = ins & (pc == p) & (grp == cls)
            key = (p, cls == "COAL")
            if not m.any() or key not in cems.index:
                continue
            av = (pmax[m][:, None] * aA[m, :]).sum(axis=0)
            ex = np.maximum(0.0, cems.loc[key].to_numpy(float) - av)
            excess += ex
            n_ph += int((ex > 1.0).sum())
    monthly = pd.Series(excess, index=idx).resample("MS")
    rec["fleetwide_context"] = {
        "construction": (
            "fuel-matched CAMPD gross load above the model's entire available MW, "
            "per (plant, class, hour); own construction, NOT the committed "
            "impossible-plant-hours metric"
        ),
        "gating": False,
        "plant_class_hours": n_ph,
        "excess_twh": float(excess.sum() / 1e6),
        "monthly_mean_mw": {
            t.strftime("%b"): float(v) for t, v in monthly.mean().items()
        },
    }

    gates = [rec["G_FOOT"]["pass"], rec["G_EXACT"]["pass"], rec["G_SEAM"]["pass"]]
    lic = all(
        rec["hours"][k][f] for k in rec["hours"] for f in ("L1_pass", "L2_pass")
    )
    act_ok = all(
        rec["hours"][k][f] for k in rec["hours"] for f in ("share_pass", "shed_pass")
    )
    rec["verdict"] = (
        "FILED-UNLICENSED"
        if not (all(gates) and lic)
        else "FILED-REDIRECTED"
        if not rec["P_ERR"]["pass"]
        else "ACTIONABLE"
        if act_ok
        else "FILED-NULL"
    )
    out = REPO / args.out
    out.write_text(json.dumps(rec, indent=1))
    print(f"\nVERDICT: {rec['verdict']}   ->  {out}")
    for k, v in rec["hours"].items():
        print(
            f"  h{k} {v['ts_cst']}: E {v['E_mw']:.1f} MW = {v['E_over_shed']:.2f}x shed; "
            f"L1 {v['L1_cop_resolvable']:.4f}; E_named/E {v['E_named_over_E']:.4f}; "
            f"impossible {v['impossible_mw']:.1f} MW"
        )


if __name__ == "__main__":
    main()
