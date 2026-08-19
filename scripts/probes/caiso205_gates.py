"""caiso-205 A/B gate scorer — the PRECOMMIT-caiso205 §4 direction-blind table.

Adapted from the committed ercot221_gates.py to the CAISO leg's pre-registered
gates (PRECOMMIT-caiso205-adaptive-ab-2026-08-19.md §4): G-REPRO (control ≡
keeper, sha256 over every committed hourly sidecar), G-CAP (no arm-introduced
above-$2,000 zone-hour), G-SHED (arm shed hours ⊆ control's), G-BAT (battery
discharge energy arm/control in [0.80, 1.25]), G-D2 (D-5 attribution row
present, no new D-4 rows), G-DOF (ledger delta = exactly the caiso_adaptive_*
entry), and the reported-never-gated G-ADA signature. C3a/C3b probe-basis
numbers are side-effect reporting only (charter: C3a inadmissible as
acceptance evidence in either direction); the official C3b/C8/C6
MUST-NOT-REGRESS legs are judged from the registration scorecards.

Usage:
    python scripts/probes/caiso205_gates.py \
        --keeper results/calibration/caiso200_h1_memberpanel \
        --control results/calibration/caiso205_control_A \
        --arm results/calibration/caiso205_adaptive_B
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

YEARS = (2023, 2024, 2025)
HARD_CAP = 2000.0  # CAISO Tariff §39.6.1 cost-verified hard cap
GBAT_BAND = (0.80, 1.25)
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_CUM = np.cumsum((0,) + MONTH_DAYS)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _g_repro(keeper: Path, control: Path) -> dict:
    """Every committed keeper hourly sidecar byte-identical in the control."""
    files = sorted((keeper / "hourly").glob("*.parquet"))
    rows = {}
    ok = True
    for f in files:
        c = control / "hourly" / f.name
        same = c.exists() and _sha(f) == _sha(c)
        rows[f.name] = bool(same)
        ok = ok and same
    extra = sorted(
        set(p.name for p in (control / "hourly").glob("*.parquet"))
        - set(f.name for f in files)
    )
    return {"files": rows, "extra_in_control": extra, "pass": bool(ok and not extra)}


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[(df["year"] == year) & (df["pass"] == "P1")].copy()


def _dw_price(df: pd.DataFrame) -> np.ndarray:
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    return (num / den).reindex(range(8760)).to_numpy(float)


def _actual(year: int) -> np.ndarray:
    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
    )
    return lmp[lmp["year"] == year].sort_values("hour")["rt"].to_numpy(float)[:8760]


def _bat_discharge(bundle: Path, year: int) -> float:
    st = pd.read_parquet(bundle / "hourly" / f"storage_{year}.parquet")
    st = st[(st["pass"] == "P1") & (st["tech"] != "pumped_storage")]
    return float(st["discharge_mw"].sum())


def _gada(bundle: Path, year: int) -> dict:
    p = bundle / "hourly" / f"adaptive_{year}.parquet"
    if not p.exists():
        return {"present": False}
    df = pd.read_parquet(p)
    ph = df["p_hat_day"].to_numpy(float)
    fl = df["floor_usd"].to_numpy(float)
    hoy = df["hour"].to_numpy(int)
    month = np.searchsorted(_MONTH_CUM, hoy // 24, side="right")
    day_spike = df.groupby(hoy // 24)["s_model_day"].first()
    active = fl > 5.0  # above the battery vom+adder incumbent
    return {
        "present": True,
        "model_spike_days": int(day_spike.sum()),
        "p_hat_max": round(float(ph.max()), 4),
        "floor_gt_vom_hours": int(active.sum()),
        "floor_gt_vom_by_month": {
            str(m): int((active & (month == m)).sum())
            for m in range(1, 13)
            if (active & (month == m)).any()
        },
        "floor_max_usd": round(float(fl.max()), 1),
    }


def _d4_rows(bundle: Path) -> list[str]:
    d = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    rows = d["diagnostics"].get("D4", {}).get("rows", [])
    return sorted(
        f"{r['year']}|{r['floor']}|{r['window']}|{r['verdict']}" for r in rows
    )


def _d5_adaptive_rows(bundle: Path) -> list[str]:
    d = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    rows = d["diagnostics"].get("D5", {}).get("rows", [])
    return sorted(
        r["mechanism"]
        for r in rows
        if r["mechanism"].startswith("caiso_storage_adaptive")
    )


def _dof_names(bundle: Path) -> list[str]:
    from scripts.build_dof_ledger import build_ledger  # noqa: PLC0415

    ledger = build_ledger(bundle, "CAISO")
    return sorted(e["name"] for e in ledger["entries"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keeper", required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument(
        "--out", default=str(REPO / "results/calibration/caiso205_gates.json")
    )
    args = ap.parse_args()
    kee_b, ctl_b, arm_b = Path(args.keeper), Path(args.control), Path(args.arm)

    out: dict = {
        "probe": "caiso205_gates",
        "charter": "PRECOMMIT-caiso205-adaptive-ab-2026-08-19.md §4",
        "keeper": str(kee_b),
        "control": str(ctl_b),
        "arm": str(arm_b),
        "years": list(YEARS),
        "per_year": {},
    }
    out["g_repro"] = _g_repro(kee_b, ctl_b)

    gcap_viol = 0
    shed_fail = gbat_fail = False
    byte_identical_years = []
    for y in YEARS:
        a = _actual(y)
        sys_c = _system(ctl_b, y)
        sys_a = _system(arm_b, y)
        # G-CAP: arm-introduced above-hard-cap zone-hours.
        key = ["zone", "hour"]
        merged = sys_c[key + ["price"]].merge(
            sys_a[key + ["price"]], on=key, suffixes=("_c", "_a")
        )
        viol = int(
            ((merged["price_a"] > HARD_CAP) & ~(merged["price_c"] > HARD_CAP)).sum()
        )
        gcap_viol += viol
        # G-SHED: arm shed hours must be a subset of control shed hours.
        shed_c = set(sys_c.loc[sys_c["slack"] > 1e-6, "hour"].astype(int))
        shed_a = set(sys_a.loc[sys_a["slack"] > 1e-6, "hour"].astype(int))
        new_shed = sorted(shed_a - shed_c)
        if new_shed:
            shed_fail = True
        # G-BAT: battery discharge energy ratio.
        d_c = _bat_discharge(ctl_b, y)
        d_a = _bat_discharge(arm_b, y)
        ratio = d_a / d_c if d_c > 0 else None
        if ratio is not None and not (GBAT_BAND[0] <= ratio <= GBAT_BAND[1]):
            gbat_fail = True
        # Byte-identity of the arm's system sidecar vs control (ex-ante §3).
        ident = _sha(ctl_b / "hourly" / f"system_{y}.parquet") == _sha(
            arm_b / "hourly" / f"system_{y}.parquet"
        )
        if ident:
            byte_identical_years.append(y)
        # Side-effect reporting only (charter: never acceptance evidence).
        mp_c, mp_a = _dw_price(sys_c), _dw_price(sys_a)
        ok = np.isfinite(mp_c) & np.isfinite(mp_a) & np.isfinite(a)
        yr = {
            "gcap_arm_introduced": viol,
            "shed_control": sorted(shed_c),
            "shed_arm": sorted(shed_a),
            "new_shed_hours": new_shed,
            "bat_discharge_mwh": {
                "control": round(d_c, 1),
                "arm": round(d_a, 1),
                "ratio": round(ratio, 4) if ratio is not None else None,
            },
            "system_sidecar_byte_identical": bool(ident),
            "side_effects_probe_basis": {
                "c3a_pct_control": round(
                    float((mp_c[ok].mean() - a[ok].mean()) / a[ok].mean() * 100), 2
                ),
                "c3a_pct_arm": round(
                    float((mp_a[ok].mean() - a[ok].mean()) / a[ok].mean() * 100), 2
                ),
                "tail_gt200_control": int((mp_c[ok] > 200.0).sum()),
                "tail_gt200_arm": int((mp_a[ok] > 200.0).sum()),
            },
            "gada_arm": _gada(arm_b, y),
        }
        out["per_year"][str(y)] = yr

    out["d4_rows_control"] = _d4_rows(ctl_b)
    out["d4_rows_arm"] = _d4_rows(arm_b)
    out["d4_no_new_rows"] = set(out["d4_rows_arm"]) <= set(out["d4_rows_control"])
    out["d5_adaptive_rows_arm"] = _d5_adaptive_rows(arm_b)
    dof_c, dof_a = _dof_names(ctl_b), _dof_names(arm_b)
    dof_delta = sorted(set(dof_a) - set(dof_c))
    out["dof"] = {
        "control_n": len(dof_c),
        "arm_n": len(dof_a),
        "delta": dof_delta,
        "pass": dof_delta == ["caiso_adaptive_half_life_days / caiso_adaptive_beta"]
        and not (set(dof_c) - set(dof_a)),
    }
    out["byte_identical_years"] = byte_identical_years
    out["gates"] = {
        "G-REPRO": {"pass": out["g_repro"]["pass"]},
        "G-CAP": {"violations": gcap_viol, "pass": gcap_viol == 0},
        "G-SHED": {"pass": not shed_fail},
        "G-BAT": {"pass": not gbat_fail, "band": list(GBAT_BAND)},
        "G-D2": {
            "no_new_d4_rows": bool(out["d4_no_new_rows"]),
            "adaptive_row_present": len(out["d5_adaptive_rows_arm"]) == 1,
            "pass": bool(out["d4_no_new_rows"])
            and len(out["d5_adaptive_rows_arm"]) == 1,
        },
        "G-DOF": {"pass": out["dof"]["pass"]},
        "G-ADA": {"reported_not_gated": True},
    }
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {args.out}")
    print(json.dumps(out["gates"], indent=1))
    print("byte-identical years:", byte_identical_years)


if __name__ == "__main__":
    main()
