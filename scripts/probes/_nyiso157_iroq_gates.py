"""nyiso-157 companion scorer — iroquois winter spread ON TOP OF the seam arm.

Scores `PREREG-nyiso157-iroquois-companion-2026-08-30.md` §3: the nyiso-150
§4 W-gates VERBATIM (`_nyiso150_ab_gates.py::score_arm_w` is the template and
the gate arithmetic is unchanged), with exactly one re-basing — CONTROL is the
seam arm `nyiso157_pararm_B`, because the companion condition itself is the
mechanism difference between the two tests. W-K1 counts the dual-channel echo
of the single `--set` flag as one delta (documented at
`_nyiso157_par_ab_gates.json` K1); W-K5 reads "no PASS->FAIL vs the new
control" (the control's own C3b-2025 FAIL standing is not a flip).

Usage::

    python scripts/probes/_nyiso157_iroq_gates.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

CONTROL = REPO / "results/calibration/nyiso157_pararm_B"
ARM = REPO / "results/calibration/nyiso157_iroq_C"
REF = REPO / "data/raw/_validation-source/actual_lmp.json"
OUT = REPO / "results/calibration/_nyiso157_iroq_gates.json"

YEARS = (2023, 2024, 2025)
ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
DOWNSTATE = ("Capital_Hudson", "NYC", "Long_Island")
FLAG = "nyiso_iroquois_winter_spread"

#: nyiso-150 §4 W-K3(a) — gated months (the nyiso-82 decisively-fixed three);
#: Jan-2025 and the summer months are reported, never gated.
GATED_WINTER = [(2023, 2), (2024, 12), (2025, 2)]
REPORTED_MONTHS = [
    (2025, 1),
    (2025, 6),
    (2025, 7),
    (2025, 12),
    (2024, 1),
    (2024, 7),
    (2023, 1),
    (2023, 12),
]


def _meta(bundle: Path) -> dict:
    return json.loads((bundle / "meta.json").read_text())


def _diag(bundle: Path) -> dict:
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[(df["pass"] == "P1") & (df["zone"].isin(ZONES))].copy()


def _zone_month(df: pd.DataFrame, year: int) -> pd.DataFrame:
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    df = df.copy()
    df["month"] = df["hour"].map(dict(enumerate(idx.month)))
    return df.groupby(["zone", "month"])["price"].mean().unstack("month")


def _d4_fails(diag: dict) -> set[tuple]:
    return {
        (int(r["year"]), str(r["floor"]), str(r["plant"]))
        for r in diag["diagnostics"]["D4"]["rows"]
        if str(r.get("verdict", "")).upper() == "FAIL"
    }


def _d2_shares(diag: dict) -> dict:
    return {
        (int(r["year"]), str(r["mechanism"]), str(r["class"])): float(
            r["share_of_class"]
        )
        for r in diag["diagnostics"]["D2"]["rows"]
    }


def _d1_miss(diag: dict) -> set:
    return {
        (int(r["year"]), str(r["class"]))
        for r in diag["diagnostics"]["D1"]["rows"]
        if str(r.get("verdict", "")).lower() not in ("pass", "exempt", "skip")
    }


def w_k1() -> dict:
    """W-K1 exactness — the one flag, through both recording channels."""
    provenance = {
        "timestamp",
        "note",
        "run_id",
        "git",
        "git_sha",
        "basis_sha",
        "out_dir",
        "label",
        "environment",
        "highspy_version",
    }
    mc, ma = _meta(CONTROL), _meta(ARM)
    diff = sorted(
        k for k in set(mc) | set(ma) if mc.get(k) != ma.get(k) and k not in provenance
    )
    # The generic overrides dict is a recording channel, not a second delta:
    # its internal difference must itself be exactly the flag.
    oc = mc.get("coal_prb_sigmoid_overrides") or {}
    oa = ma.get("coal_prb_sigmoid_overrides") or {}
    inner = sorted(k for k in set(oc) | set(oa) if oc.get(k) != oa.get(k))
    expected = sorted({FLAG, "coal_prb_sigmoid_overrides"} & set(diff)) == diff
    return {
        "gate": f"W-K1 exactness ({FLAG}, dual-channel)",
        "solve_field_diffs": diff,
        "overrides_inner_diffs": inner,
        "passed": bool(
            expected and inner == [FLAG] and bool(ma.get(FLAG)) and not mc.get(FLAG)
        ),
    }


def w_k2_construction() -> dict:
    """W-K2 — (a) cited standing identity; (b) conservation re-verified;
    (c) LP liveness scored below with the zone-month tables."""
    from market_sim.data.fuel.basis.nyiso import nyiso_reconciled_reference_monthly

    rows, ok = {}, True
    for year in YEARS:
        out = nyiso_reconciled_reference_monthly(year)
        if out is None:
            rows[year] = {"available": False}
            ok = False
            continue
        iroq_m, transco_m = out
        # The committed flat construction's annual spread is the measured SOM
        # annual by construction; conservation = the reconciled monthly mean
        # preserves it exactly (nyiso-122 Delta=0.00000 re-verified here).
        flat = pd.read_csv(REPO / "data/raw/gas-prices/transco_z6_iroquois_monthly.csv")
        sub = flat[flat["date"].astype(str).str.startswith(f"{year}-")]
        flat_spread = float(
            (sub["iroquois_z2_usd_mmbtu"] - sub["transco_z6_ny_usd_mmbtu"]).mean()
        )
        got = float((iroq_m - transco_m).mean())
        rows[year] = {
            "available": True,
            "reconciled_annual_spread": round(got, 5),
            "measured_flat_annual_spread": round(flat_spread, 5),
            "delta": round(got - flat_spread, 6),
        }
        ok = ok and abs(got - flat_spread) <= 0.005
    return {
        "gate": "W-K2ab construction (NYC identity cited; conservation <= $0.005)",
        "nyc_identity_citation": (
            "nyiso-122 Delta=0.00000 x3; _nyiso150_gradient_phase0.json: NYC "
            "gas bit-identical on/off (construction unchanged since)"
        ),
        "per_year": rows,
        "passed": bool(ok),
    }


def score() -> dict:
    ref = json.loads(REF.read_text())["NYISO"]
    gates: list[dict] = [w_k1(), w_k2_construction()]

    zm_c, zm_a, act = {}, {}, {}
    for year in YEARS:
        zm_c[year] = _zone_month(_system(CONTROL, year), year)
        zm_a[year] = _zone_month(_system(ARM, year), year)
        act[year] = ref[str(year)]["zones"]

    # W-K2(c): LP liveness — DJF mean |dLMP| > $1/MWh (pooled over years).
    deltas = []
    for year in YEARS:
        for m in (1, 2, 12):
            for z in ZONES:
                deltas.append(abs(zm_a[year].loc[z, m] - zm_c[year].loc[z, m]))
    djf_mean = float(np.mean(deltas))
    gates.append(
        {
            "gate": "W-K2c LP liveness (DJF mean |dLMP|)",
            "djf_mean_abs_dlmp": round(djf_mean, 3),
            "passed": djf_mean > 1.0,
        }
    )

    # W-K3(a): gated winter months — spread recovery >=30 %, overshoot kill.
    rows, ok_a = [], True
    for year, m in GATED_WINTER + REPORTED_MONTHS:
        gated = (year, m) in GATED_WINTER
        uw_c = float(zm_c[year].loc["Upstate_West", m])
        uw_a = float(zm_a[year].loc["Upstate_West", m])
        for z in DOWNSTATE:
            mz_c = float(zm_c[year].loc[z, m])
            mz_a = float(zm_a[year].loc[z, m])
            z_act = float(act[year][z]["rt_mon"][m - 1])
            uw_act = float(act[year]["Upstate_West"]["rt_mon"][m - 1])
            sp_c, sp_a = mz_c - uw_c, mz_a - uw_a
            sp_act = z_act - uw_act
            gap_c = sp_act - sp_c
            rec = (sp_a - sp_c) / gap_c if abs(gap_c) > 1e-9 else 1.0
            overshoot = (mz_a - z_act) / z_act > 0.15
            hit = (rec >= 0.30) and not overshoot if gated else None
            if gated:
                ok_a = ok_a and bool(hit)
            rows.append(
                {
                    "year": year,
                    "month": m,
                    "zone": z,
                    "gated": gated,
                    "spread_ctl": round(sp_c, 1),
                    "spread_arm": round(sp_a, 1),
                    "spread_actual": round(sp_act, 1),
                    "recovery": round(rec, 3),
                    "model_ctl": round(mz_c, 1),
                    "model_arm": round(mz_a, 1),
                    "actual": round(z_act, 1),
                    "overshoot": overshoot,
                    "ok": hit,
                }
            )
    gates.append(
        {
            "gate": "W-K3a gated winter spread recovery >=30% (no overshoot >+15%)",
            "rows": rows,
            "passed": ok_a,
        }
    )

    # W-K3(b): annual gradient at least doubles toward actual, <= 1.10x actual.
    grads, ok_b = [], True
    for year in (2024, 2025):
        ann_c = _system(CONTROL, year).groupby("zone")["price"].mean()
        ann_a = _system(ARM, year).groupby("zone")["price"].mean()
        g_c = float(ann_c[ZONES].max() - ann_c[ZONES].min())
        g_a = float(ann_a[ZONES].max() - ann_a[ZONES].min())
        g_act = max(act[year][z]["rt"] for z in ZONES) - min(
            act[year][z]["rt"] for z in ZONES
        )
        hit = (g_a >= 2.0 * g_c or g_a >= g_act) and g_a <= 1.10 * g_act
        ok_b = ok_b and hit
        grads.append(
            {
                "year": year,
                "gradient_ctl": round(g_c, 2),
                "gradient_arm": round(g_a, 2),
                "gradient_actual": round(g_act, 2),
                "ok": hit,
            }
        )
    gates.append(
        {
            "gate": "W-K3b annual gradient toward actual (2024+2025)",
            "rows": grads,
            "passed": ok_b,
        }
    )

    # W-K3(c): UW-2023 annual over-pricing strictly improves.
    uw23_c = float(
        _system(CONTROL, 2023).groupby("zone")["price"].mean()["Upstate_West"]
    )
    uw23_a = float(_system(ARM, 2023).groupby("zone")["price"].mean()["Upstate_West"])
    uw23_act = float(act[2023]["Upstate_West"]["rt"])
    ok_c = abs(uw23_a - uw23_act) < abs(uw23_c - uw23_act)
    gates.append(
        {
            "gate": "W-K3c UW-2023 annual improves",
            "ctl": round(uw23_c, 2),
            "arm": round(uw23_a, 2),
            "actual": round(uw23_act, 2),
            "passed": ok_c,
        }
    )

    # W-K3(d): anti-relocation — worst-zone |annual err| must not worsen.
    reloc, ok_d = [], True
    for year in YEARS:
        ann_c = _system(CONTROL, year).groupby("zone")["price"].mean()
        ann_a = _system(ARM, year).groupby("zone")["price"].mean()
        wc = max(
            abs(float(ann_c[z]) - act[year][z]["rt"]) / act[year][z]["rt"]
            for z in ZONES
        )
        wa = max(
            abs(float(ann_a[z]) - act[year][z]["rt"]) / act[year][z]["rt"]
            for z in ZONES
        )
        hit = wa <= wc + 1e-9
        ok_d = ok_d and hit
        reloc.append(
            {
                "year": year,
                "worst_ctl_pct": round(100 * wc, 1),
                "worst_arm_pct": round(100 * wa, 1),
                "ok": hit,
            }
        )
    gates.append(
        {
            "gate": "W-K3d anti-relocation (worst zone |ann err|)",
            "rows": reloc,
            "passed": ok_d,
        }
    )

    # W-K4: zero NEW failing D-rows; forced-share rises escalate through D-1.
    dc, da = _diag(CONTROL), _diag(ARM)
    fc, fa = _d4_fails(dc), _d4_fails(da)
    new_d4 = sorted(fa - fc)
    sc, sa = _d2_shares(dc), _d2_shares(da)
    rises = sorted(
        (
            {"key": list(k), "ctl": round(sc.get(k, 0.0), 4), "arm": round(v, 4)}
            for k, v in sa.items()
            if v > sc.get(k, 0.0) + 1e-6
        ),
        key=lambda r: r["key"],
    )
    new_d1 = sorted(_d1_miss(da) - _d1_miss(dc))
    escalated = bool(rises)
    gates.append(
        {
            "gate": "W-K4 D-4/D-2 (K6-prime)",
            "new_d4_failures": new_d4,
            "cleared_d4": sorted(fc - fa),
            "forced_share_rises": rises,
            "escalated": escalated,
            "new_d1_misses": new_d1,
            "passed": (not new_d4) and ((not escalated) or not new_d1),
        }
    )

    # W-K5: no PASS->FAIL vs the new control (metrics.json criteria).
    m_c = json.loads((CONTROL / "metrics.json").read_text())["criteria"]
    m_a_path = ARM / "metrics.json"
    if m_a_path.exists():
        m_a = json.loads(m_a_path.read_text())["criteria"]
        flips = sorted(
            k
            for k in m_c
            if isinstance(m_c[k], dict)
            and m_c[k].get("status") == "PASS"
            and (m_a.get(k) or {}).get("status") == "FAIL"
        )
        gates.append(
            {
                "gate": "W-K5 criteria (no PASS->FAIL vs the seam-arm control)",
                "control": {k: v.get("status") for k, v in m_c.items()},
                "arm": {k: v.get("status") for k, v in m_a.items()},
                "pass_to_fail": flips,
                "note": (
                    "the control's own C3b-2025 FAIL standing is not a flip "
                    "(companion prereg §3); C3c reported never gated"
                ),
                "passed": not flips,
            }
        )
    else:
        gates.append(
            {
                "gate": "W-K5 criteria (no PASS->FAIL vs the seam-arm control)",
                "note": "arm metrics.json absent — register the arm first",
                "passed": None,
            }
        )

    # W-K6 LOYO gate-side: W-K3a per gated month, W-K3b per year — already
    # evaluated per-unit above.
    gates.append(
        {
            "gate": "W-K6 LOYO (gate-side per-month/per-year legs)",
            "passed": ok_a and ok_b,
        }
    )

    # ADV-W1/W2 report tables: summer downstate + UW winter months.
    adv = []
    for year in YEARS:
        for m in (1, 2, 6, 7, 12):
            for z in ZONES:
                adv.append(
                    {
                        "year": year,
                        "month": m,
                        "zone": z,
                        "ctl": round(float(zm_c[year].loc[z, m]), 1),
                        "arm": round(float(zm_a[year].loc[z, m]), 1),
                        "actual": round(float(act[year][z]["rt_mon"][m - 1]), 1),
                    }
                )
    gates.append(
        {
            "gate": "ADV-W1/W2 monthly report (reported, not gated)",
            "rows": adv,
            "passed": None,
        }
    )
    return {
        "probe": "nyiso-157 iroquois companion A/B (seam+iroquois vs seam)",
        "prereg": "results/calibration/PREREG-nyiso157-iroquois-companion-2026-08-30.md",
        "arms": {"control_seam": CONTROL.name, "arm_companion": ARM.name},
        "gates": gates,
    }


def main() -> int:
    res = score()
    print("\n=== nyiso-157 companion W-gates (vs the seam arm) ===")
    for g in res["gates"]:
        status = (
            "PASS" if g["passed"] else ("FAIL" if g["passed"] is False else "REPORT")
        )
        print(f"  {g['gate']:<58} {status}")
    for g in res["gates"]:
        if g["gate"].startswith("W-K3a"):
            print("\n=== gated winter months ===")
            for r in g["rows"]:
                if r["gated"]:
                    print(
                        f"  {r['year']}-{r['month']:02d} {r['zone']:<15} "
                        f"spread ctl {r['spread_ctl']:+6.1f} -> arm "
                        f"{r['spread_arm']:+6.1f} (actual {r['spread_actual']:+6.1f}) "
                        f"recovery {r['recovery']:+.2f} ok={r['ok']}"
                    )
        if g["gate"].startswith("W-K3b"):
            for r in g["rows"]:
                print(
                    f"  gradient {r['year']}: ctl {r['gradient_ctl']} -> arm "
                    f"{r['gradient_arm']} (actual {r['gradient_actual']}) ok={r['ok']}"
                )
    OUT.write_text(json.dumps(res, indent=1, default=str))
    print(f"\nwrote {OUT}")
    hard = [g for g in res["gates"] if g["passed"] is False]
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
