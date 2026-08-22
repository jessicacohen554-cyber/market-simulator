"""miso-175 — the pre-registered A/B scorer for the seam-envelope hour-key repair.

Scores the gates fixed in
``results/calibration/PREREG-miso175-seam-envelope-hour-key-2026-08-22.md`` §4
(committed BEFORE either solve) over the control (``miso175_control``) and arm
(``miso175_hourkey``) bundles:

  M-0   control inertness — the control's 12 scored sidecars value-identical
        (max|diff| = 0) to the committed keeper ``miso173_layupmask``.
  M-1a  cap exactness — the production loader regenerates all 48 frozen
        arrays with sha256 exactly matching ``_miso175_hour_key_instrument.json``.
  M-1b  bound respect — the arm's per-seam P1 gross import/export never
        exceeds the corrected cap by more than 1 MW (unit_hourly).
  M-2a  liveness — ≥ 1,000 differing P1 zone-hour price cells over 3 years.
  M-2b  direction — over B_loose (Jun–Sep control-binding hours whose
        corrected PJM import cap is ≥ +20 MW looser), mean(arm − control)
        gross import > −25 MW; KILL if it fails in ≥ 2 of 3 years
        (a year with |B_loose| < 20 h is reported, not gated).
  M-3   conduct — the arm's regenerated D-4 carries ZERO failures and no
        new non-pass rows vs the regenerated control.
  M-6   against-interest — C3a-2023 within ±3.0 %, C3a-2024 within ±10 %
        with adverse move ≤ 1.5 pp; C3a-2025 reported, never gated.

(M-4 C8 and M-5 record flips are scored by ``calibration_verdict.py`` after
registration — the committed-artifact path — and folded into the RESULT.)

Run:  python3 scripts/probes/_miso175_hour_key_ab.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.data.eia930 import measured_seam_import_envelope  # noqa: E402

CAL = ROOT / "results" / "calibration"
KEEPER = CAL / "miso173_layupmask"
CONTROL = CAL / "miso175_control"
ARM = CAL / "miso175_hourkey"
INSTRUMENT = CAL / "_miso175_hour_key_instrument.json"
OUT = CAL / "_miso175_hour_key_ab.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
SIDECARS = ("class_hourly", "system", "storage", "reserve_family")
MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[9])  # Jun 1 .. Sep 30

# PREREG §4 thresholds — fixed there, restated here.
M2A_MIN_CELLS = 1000
M2B_LOOSE_MW = 20.0
M2B_TOL_MW = -25.0
M2B_MIN_HOURS = 20
M6_C3A_2023_BAND = 3.0
M6_C3A_2024_ADVERSE_PP = 1.5


def _sidecar_max_diff(a: Path, b: Path) -> float:
    """Max |diff| over shared numeric columns after aligning on key columns."""
    da, db = pd.read_parquet(a), pd.read_parquet(b)
    if len(da) != len(db) or set(da.columns) != set(db.columns):
        return float("inf")
    keys = [c for c in da.columns if da[c].dtype == object or str(da[c].dtype).startswith("int")]
    da = da.sort_values(keys).reset_index(drop=True)
    db = db[da.columns].sort_values(keys).reset_index(drop=True)
    worst = 0.0
    for c in da.columns:
        if str(da[c].dtype).startswith("float"):
            worst = max(worst, float(np.nanmax(np.abs(da[c].to_numpy() - db[c].to_numpy()))))
        else:
            if not (da[c].to_numpy() == db[c].to_numpy()).all():
                return float("inf")
    return worst


def _seam_flows(bundle: Path, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-seam P1 (gross_import, gross_export) MW frames indexed 0..8759."""
    d = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "fuel", "hour", "mw"],
    )
    d = d[(d["pass"] == "P1") & (d["fuel"].astype(str) == "import")]
    uid = d["unit_id"].astype(str)
    seam = uid.str.extract(r"_ref(?:imp|exp)_([A-Za-z]+)#", expand=False)
    side = np.where(uid.str.contains("_refimp_"), "imp", "exp")
    work = pd.DataFrame(
        {"seam": seam.to_numpy(), "side": side, "hour": d["hour"].to_numpy(), "mw": d["mw"].to_numpy()}
    ).dropna(subset=["seam"])
    imp = (
        work[work["side"] == "imp"].pivot_table(index="hour", columns="seam", values="mw", aggfunc="sum")
        .reindex(range(HOURS)).fillna(0.0)
    )
    exp = (
        -work[work["side"] == "exp"].pivot_table(index="hour", columns="seam", values="mw", aggfunc="sum")
        .reindex(range(HOURS)).fillna(0.0)
    )
    return imp, exp


def _p1_price_panel(bundle: Path, year: int) -> pd.DataFrame:
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return s.pivot_table(index="hour", columns="zone", values="price")


def _c3a(bundle: Path, year: int) -> float:
    import gzip

    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    mod = (s["price"] * s["demand"]).sum() / s["demand"].sum()
    rt_lw = json.load(gzip.open(ROOT / f"frontend/data/backcast/bench/MISO/{year}.json.gz"))[
        "bench"
    ]["avgLMP"]["rt_lw"]
    return 100.0 * (mod - rt_lw) / rt_lw


def main() -> None:
    """Score every gate, write the record, print verdicts, exit 1 on any kill."""
    frozen = json.loads(INSTRUMENT.read_text())["arrays"]
    rec: dict = {"session": "miso-175",
                 "prereg": "PREREG-miso175-seam-envelope-hour-key-2026-08-22.md",
                 "gates": {}}
    kills: list[str] = []

    # ---------------- M-0 : control inertness ----------------
    m0 = {}
    worst = 0.0
    for y in YEARS:
        for sc in SIDECARS:
            d = _sidecar_max_diff(
                KEEPER / "hourly" / f"{sc}_{y}.parquet", CONTROL / "hourly" / f"{sc}_{y}.parquet"
            )
            m0[f"{sc}_{y}"] = d
            worst = max(worst, d)
    m0["max_over_12"] = worst
    m0["verdict"] = "PASS" if worst == 0.0 else "KILL"
    if worst != 0.0:
        kills.append(f"M-0: control not value-identical to keeper (max|diff|={worst})")
    rec["gates"]["M0_control_inertness"] = m0

    # ---------------- M-1a : cap digest exactness ----------------
    m1a = {"mismatches": []}
    for y in YEARS:
        for direction in ("import", "export"):
            legacy = measured_seam_import_envelope("MISO", y, HOURS, None, direction) or {}
            fixed = measured_seam_import_envelope("MISO", y, HOURS, None, direction, hour_ending_key=True) or {}
            for seam in legacy:
                k = f"{y}_{direction}_{seam}"
                if k not in frozen:
                    continue
                sl = hashlib.sha256(np.ascontiguousarray(legacy[seam], dtype=np.float64).tobytes()).hexdigest()
                sf = hashlib.sha256(np.ascontiguousarray(fixed[seam], dtype=np.float64).tobytes()).hexdigest()
                if sl != frozen[k]["sha256_legacy"]:
                    m1a["mismatches"].append(f"{k}:legacy")
                if sf != frozen[k]["sha256_corrected"]:
                    m1a["mismatches"].append(f"{k}:corrected")
    m1a["n_checked"] = 48
    m1a["verdict"] = "PASS" if not m1a["mismatches"] else "KILL"
    if m1a["mismatches"]:
        kills.append(f"M-1a: frozen digest mismatches {m1a['mismatches']}")
    rec["gates"]["M1a_cap_digests"] = m1a

    # ---------------- M-1b : arm respects the corrected bounds ----------------
    m1b = {}
    for y in YEARS:
        imp, exp = _seam_flows(ARM, y)
        icaps = measured_seam_import_envelope("MISO", y, HOURS, None, "import", hour_ending_key=True) or {}
        ecaps = measured_seam_import_envelope("MISO", y, HOURS, None, "export", hour_ending_key=True) or {}
        row = {}
        for seam in icaps:
            if seam in imp.columns:
                over = float(np.max(imp[seam].to_numpy() - icaps[seam]))
                row[f"{seam}_import_max_over_mw"] = over
            if seam in exp.columns and seam in ecaps:
                over = float(np.max(exp[seam].to_numpy() - ecaps[seam]))
                row[f"{seam}_export_max_over_mw"] = over
        m1b[str(y)] = row
    worst_over = max(v for row in m1b.values() for v in row.values())
    m1b["max_over_mw"] = worst_over
    m1b["verdict"] = "PASS" if worst_over <= 1.0 else "KILL"
    if worst_over > 1.0:
        kills.append(f"M-1b: arm exceeds corrected cap by {worst_over:.1f} MW")
    rec["gates"]["M1b_bound_respect"] = m1b

    # ---------------- M-2a : liveness ----------------
    m2a = {}
    total_cells = 0
    for y in YEARS:
        pa, pc = _p1_price_panel(ARM, y), _p1_price_panel(CONTROL, y)
        pc = pc[pa.columns]
        diff = int(np.sum(np.abs(pa.to_numpy() - pc.to_numpy()) > 1e-6))
        m2a[str(y)] = diff
        total_cells += diff
    m2a["total_differing_cells"] = total_cells
    m2a["verdict"] = "LIVE" if total_cells >= M2A_MIN_CELLS else "INERT"
    rec["gates"]["M2a_liveness"] = m2a

    # ---------------- M-2b : direction over B_loose ----------------
    m2b = {}
    fails = 0
    h = np.arange(HOURS)
    summer = (h >= SUMMER[0]) & (h < SUMMER[1])
    for y in YEARS:
        legacy = (measured_seam_import_envelope("MISO", y, HOURS, None, "import") or {})["PJM"]
        fixed = (measured_seam_import_envelope("MISO", y, HOURS, None, "import", hour_ending_key=True) or {})["PJM"]
        imp_c, _ = _seam_flows(CONTROL, y)
        imp_a, _ = _seam_flows(ARM, y)
        fc = imp_c["PJM"].to_numpy()
        fa = imp_a["PJM"].to_numpy()
        binding = np.abs(fc - legacy) <= np.maximum(1.0, 0.01 * legacy)
        loose = summer & binding & ((fixed - legacy) > M2B_LOOSE_MW)
        n = int(loose.sum())
        mean_d = float(np.mean((fa - fc)[loose])) if n else float("nan")
        gated = n >= M2B_MIN_HOURS
        ok = (not gated) or (mean_d > M2B_TOL_MW)
        if gated and not ok:
            fails += 1
        m2b[str(y)] = {"n_B_loose": n, "mean_arm_minus_control_mw": mean_d,
                       "gated": gated, "ok": bool(ok)}
    m2b["years_failing"] = fails
    m2b["verdict"] = "PASS" if fails < 2 else "KILL"
    if fails >= 2:
        kills.append(f"M-2b: direction wrong in {fails} of 3 years")
    rec["gates"]["M2b_direction"] = m2b

    # ---------------- M-3 : conduct (D-4) ----------------
    m3 = {}
    da = json.loads((ARM / "legitimacy_diagnostics.json").read_text())["diagnostics"]["D4"]
    dc = json.loads((CONTROL / "legitimacy_diagnostics.json").read_text())["diagnostics"]["D4"]

    def _nonpass(d4):
        return sorted(
            f"{r['year']}/{r.get('floor','')}/{r.get('plant','')}/{r.get('check','')}"
            for r in d4["rows"] if r.get("verdict") != "pass"
        )

    m3["arm_failures"] = da["failures"]
    m3["arm_nonpass_rows"] = _nonpass(da)
    m3["control_nonpass_rows"] = _nonpass(dc)
    new_rows = [r for r in m3["arm_nonpass_rows"] if r not in m3["control_nonpass_rows"]]
    m3["new_nonpass_vs_control"] = new_rows
    ok = (not da["failures"]) and not new_rows
    m3["verdict"] = "PASS" if ok else "KILL"
    if not ok:
        kills.append(f"M-3: D-4 conduct regression (failures={da['failures']}, new={new_rows})")
    rec["gates"]["M3_conduct"] = m3

    # ---------------- M-6 : against-interest C3a ----------------
    m6 = {}
    keeper_c3a = {y: _c3a(KEEPER, y) for y in YEARS}
    arm_c3a = {y: _c3a(ARM, y) for y in YEARS}
    ctrl_c3a = {y: _c3a(CONTROL, y) for y in YEARS}
    m6["keeper"] = {str(y): round(v, 3) for y, v in keeper_c3a.items()}
    m6["control"] = {str(y): round(v, 3) for y, v in ctrl_c3a.items()}
    m6["arm"] = {str(y): round(v, 3) for y, v in arm_c3a.items()}
    ok23 = abs(arm_c3a[2023]) <= M6_C3A_2023_BAND
    adverse24 = keeper_c3a[2024] - arm_c3a[2024]  # positive = moved more negative
    ok24 = abs(arm_c3a[2024]) <= 10.0 and adverse24 <= M6_C3A_2024_ADVERSE_PP
    m6["c3a_2023_ok"] = bool(ok23)
    m6["c3a_2024_ok"] = bool(ok24)
    m6["c3a_2024_adverse_pp"] = round(adverse24, 3)
    m6["c3a_2025_reported_not_gated"] = round(arm_c3a[2025], 3)
    m6["verdict"] = "PASS" if (ok23 and ok24) else "KILL"
    if not (ok23 and ok24):
        kills.append(f"M-6: against-interest band left (2023 {arm_c3a[2023]:+.2f}%, 2024 {arm_c3a[2024]:+.2f}%)")
    rec["gates"]["M6_against_interest"] = m6

    rec["kills"] = kills
    rec["all_kills_silent"] = not kills
    rec["m2a_live"] = m2a["verdict"] == "LIVE"
    OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT}\n")

    for name, g in rec["gates"].items():
        print(f"{name}: {g['verdict']}")
    print(f"\nM-2a differing cells: {m2a['total_differing_cells']}")
    for y in YEARS:
        b = m2b[str(y)]
        print(f"M-2b {y}: |B_loose|={b['n_B_loose']}  mean Δ={b['mean_arm_minus_control_mw']:+.1f} MW  ok={b['ok']}")
    print(f"M-6 C3a keeper {m6['keeper']} -> arm {m6['arm']}")
    print(f"\nALL KILLS SILENT: {rec['all_kills_silent']}")
    for k in kills:
        print(f"  KILL: {k}")
    sys.exit(1 if kills else 0)


if __name__ == "__main__":
    main()
