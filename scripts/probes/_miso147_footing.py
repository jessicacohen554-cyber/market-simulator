"""miso-147 footing gates — G-F0..G-F3 (PREREG §3), the HARD STOP before any probe.

G-F0 reproduces the charter's 2025 monthly deficit table (committed nowhere in
the repo — the charter's numbers ARE the target) from the keeper P1 sidecar +
the miso-137 hourly actual on the C3a weight. G-F1 reproduces miso-142/143's
six committed window deficits. G-F2 cross-checks the 88 >$200 hours against the
C3c ledger footing. G-F3 registers every universe (TRAP 1) before any
subtraction. Any failure => BRANCH-INSTRUMENT-FAIL: bars unmoved, gaps only.

Writes ``results/calibration/_miso147_footing.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _miso147_strata import (  # noqa: E402
    EXPECTED_KLASSES,
    FAMILY_TO_KLASSES,
    HOURS,
    REPO,
    TAIL_USD,
    YEARS,
    c3a_weight,
    campd_units,
    fleet_pack,
    hygiene,
    model_price,
    month_of_hour,
    sidecar_pivot,
    strata,
    windows,
    wmean,
)

OUT = REPO / "results" / "calibration" / "_miso147_footing.json"

# PREREG §3 G-F0 — the charter's 2025 monthly table (the reproduction target).
CHARTER_ALL = [-9.44, -2.99, -1.73, -2.24, 4.22, -17.36, -17.88, -3.49, -8.81, -2.70, -3.15, -5.50]
CHARTER_ORD = [-3.82, 0.12, 0.04, -0.28, 5.39, -3.31, -8.61, -1.47, -1.35, -1.74, -2.05, -3.69]
CHARTER_PCT = [-18.3, -6.4, -4.6, -5.9, 12.4, -30.2, -30.1, -8.6, -19.0, -7.0, -7.8, -11.6]
CHARTER_CNT = [16, 4, 4, 4, 3, 21, 13, 5, 8, 2, 3, 5]
TOL_USD = 0.005
TOL_PCT = 0.05
DISAMBIG_USD = 0.02  # the single pre-registered <=/< boundary re-check trigger

# PREREG §3 G-F1 — miso-142/143's six committed window deficits (TRAP 7).
COMMITTED_DEFICITS = {
    "2023|W1_jun_jul_h8_20": -4.750,
    "2023|JJA_h12_17": -8.333,
    "2024|W1_jun_jul_h8_20": -10.676,
    "2024|JJA_h12_17": -10.671,
    "2025|W1_jun_jul_h8_20": -30.999,
    "2025|JJA_h12_17": -30.435,
}
GF1_TOL = 0.01

LEDGER_88 = 88  # the C3c ledger's own committed 2025 RT>$200 count


def gate_f0() -> dict:
    """G-F0 — the charter monthly table, all-hours + ordinary + counts."""
    year = 2025
    s = strata(year)
    rt, valid = s["rt"], s["valid"]
    p = model_price(year)
    w = c3a_weight(year)
    diff = p - rt
    mo = month_of_hour(np.arange(HOURS))
    rows, ok = [], True
    for m in range(1, 13):
        base = valid & (mo == m)
        d_all = wmean(diff, w, base)
        d_ord = wmean(diff, w, base & (rt <= TAIL_USD))
        cnt = int((base & (rt > TAIL_USD)).sum())
        a_mean = wmean(rt, w, base)
        pct = 100.0 * d_all / a_mean if a_mean else float("nan")
        pct_model_den = 100.0 * d_all / wmean(p, w, base)
        e_all = d_all - CHARTER_ALL[m - 1]
        e_ord = d_ord - CHARTER_ORD[m - 1]
        e_pct = pct - CHARTER_PCT[m - 1]
        row_ok = abs(e_all) <= TOL_USD and abs(e_ord) <= TOL_USD and cnt == CHARTER_CNT[m - 1]
        disambig = (not row_ok) and (abs(e_all) <= DISAMBIG_USD or abs(e_ord) <= DISAMBIG_USD)
        ok &= row_ok
        rows.append(
            {
                "month": m,
                "deficit_all": round(d_all, 4),
                "charter_all": CHARTER_ALL[m - 1],
                "err_all": round(e_all, 4),
                "deficit_ordinary": round(d_ord, 4),
                "charter_ordinary": CHARTER_ORD[m - 1],
                "err_ordinary": round(e_ord, 4),
                "n_gt200": cnt,
                "charter_n_gt200": CHARTER_CNT[m - 1],
                "pct_actual_den": round(pct, 2),
                "charter_pct": CHARTER_PCT[m - 1],
                "pct_err": round(e_pct, 3),
                "pct_model_den": round(pct_model_den, 2),
                "row_ok": bool(row_ok),
                "disambig_boundary_recheck": bool(disambig),
            }
        )
    counts_sum = int(sum(r["n_gt200"] for r in rows))
    pct_note = [r["month"] for r in rows if abs(r["pct_err"]) > TOL_PCT]
    return {
        "pass": bool(ok and counts_sum == LEDGER_88),
        "counts_sum": counts_sum,
        "pct_denominator_notes": pct_note,
        "tolerances": {"usd": TOL_USD, "pct": TOL_PCT, "disambig_usd": DISAMBIG_USD},
        "months": rows,
    }


def gate_f1() -> dict:
    """G-F1 — the six committed window deficits, <= $0.01 each."""
    wins = windows()
    out, ok = {}, True
    for year in YEARS:
        s = strata(year)
        rt, valid = s["rt"], s["valid"]
        p = model_price(year)
        w = c3a_weight(year)
        for wname, sel in wins.items():
            key = f"{year}|{wname}"
            d = wmean(p - rt, w, valid & sel)
            err = d - COMMITTED_DEFICITS[key]
            ok &= abs(err) <= GF1_TOL
            out[key] = {"deficit": round(d, 4), "committed": COMMITTED_DEFICITS[key], "err": round(err, 4)}
    return {"pass": bool(ok), "tol_usd": GF1_TOL, "windows": out}


def gate_f2() -> dict:
    """G-F2 — 2025 RT>$200 count == 88 == the C3c ledger footing."""
    s = strata(2025)
    n = int((s["valid"] & (s["rt"] > TAIL_USD)).sum())
    return {"pass": n == LEDGER_88, "n_gt200_2025": n, "ledger": LEDGER_88}


def gate_f3() -> dict:
    """G-F3 — universe registration (TRAP 1): strata, fleet, CAMPD."""
    out: dict = {"strata": {}, "model_fleet": {}, "campd": {}}
    for year in YEARS:
        s = strata(year)
        out["strata"][year] = {
            "S1_thr_usd": s["S1_thr_usd"],
            "counts": s["counts"],
            "overlap_S1_S2": s["overlap_S1_S2"],
            "n_valid": s["n_valid"],
        }
        sidecar_pivot(year)  # asserts the 17-klass vocabulary
        fp = fleet_pack(year)
        kl = fp["klass"]
        by_k = {}
        for k in sorted(set(kl.tolist())):
            m = kl == k
            by_k[k] = {
                "n_units": int(m.sum()),
                "pmax_gw": round(float(fp["pmax"][m].sum()) / 1e3, 3),
                "avail_cap_gw_annual_mean": round(
                    float((fp["pmax"][m][:, None] * fp["availability"][m]).sum(axis=0).mean()) / 1e3, 3
                ),
            }
        out["model_fleet"][year] = {
            "by_klass": by_k,
            "import_tranches_gw": by_k.get("import", {}).get("pmax_gw", 0.0),
            "universe": "keeper fleet_state (fleet_only, no LP), incl. import tranches",
        }
        units, meta = campd_units(year)
        p99 = units.groupby(["family", "unit"])["gross"].quantile(0.99)
        fam_tab = {
            fam: {
                "n_units": int(units.loc[units["family"] == fam, "unit"].nunique()),
                "sum_p99_gross_gw": round(float(p99.loc[fam].sum()) / 1e3, 3) if fam in p99.index else 0.0,
            }
            for fam in FAMILY_TO_KLASSES
        }
        mo = month_of_hour(units["hoy"].to_numpy(int))
        on = units["gross"] > 0
        cov = {int(m): int(units.loc[(mo == m), "unit"].nunique()) for m in range(1, 13)}
        out["campd"][year] = {
            **meta,
            "by_family": fam_tab,
            "reporting_units_by_month": cov,
            "basis": "GROSS (state readings); NET via parasitic factors for cross-side",
        }
        del units
    return out


def run() -> dict:
    hygiene()
    res = {
        "session": "miso-147",
        "prereg": "results/calibration/PREREG-miso147-highprice-dispatch-composition-2026-08-09.md",
        "G_F0": gate_f0(),
        "G_F1": gate_f1(),
        "G_F2": gate_f2(),
    }
    hard = res["G_F0"]["pass"] and res["G_F1"]["pass"] and res["G_F2"]["pass"]
    res["G_F3"] = gate_f3()
    res["footing_pass"] = bool(hard)
    res["branch_on_fail"] = None if hard else "BRANCH-INSTRUMENT-FAIL"
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


if __name__ == "__main__":
    r = run()
    print(f"G-F0 {'PASS' if r['G_F0']['pass'] else 'FAIL'} (counts sum {r['G_F0']['counts_sum']})")
    print(f"G-F1 {'PASS' if r['G_F1']['pass'] else 'FAIL'}")
    print(f"G-F2 {'PASS' if r['G_F2']['pass'] else 'FAIL'} ({r['G_F2']['n_gt200_2025']}h)")
    print(f"FOOTING {'PASS' if r['footing_pass'] else 'FAIL -> BRANCH-INSTRUMENT-FAIL'}")
    print(f"-> {OUT}")
