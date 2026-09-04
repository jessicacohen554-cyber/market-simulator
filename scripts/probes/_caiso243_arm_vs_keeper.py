"""caiso-243 — B1 (arm) vs the committed keeper: gates and predictions, scored against interest.

NO LP. Reads two committed bundles' hourly sidecars, metrics and attestations:

  * KEEPER — ``caiso241_b1_ctpeaker_committed`` (git_sha 607f9324)
  * B1     — ``caiso243_b1_f923_fallback_guard`` (keeper recipe + the two
             owner-chosen F923 fallback guards)

G-CTRL is FORM 2 (owner's choice, PRECOMMIT-caiso243 §0.4): the arm has two
measured-inert years (2023, 2024 — 12/12 hub-overlay coverage), so the arm's
own inert years are the HEAD-drift control: their class energies must
reproduce the keeper's to 0.001 TWh in every class (caiso-240 §0.7(1)). No
control solve is spent.

Scored here, each against the precommit's registered falsifier: G-CTRL (form
2), G-INERT, G-C3a envelope leg (annual LOAD-WEIGHTED mean price move,
[-2.634, +0.311] for 2025, exactly 0 for the inert years), G-C1 / G-C3b /
G-C8 / G-CAVEAT / G-C6 (verdict identity from metrics.json), P-1…P-8.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso243_arm_vs_keeper.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

CAL = REPO / "results/calibration"
KEEPER = CAL / "caiso241_b1_ctpeaker_committed"
B1 = CAL / "caiso243_b1_f923_fallback_guard"
YEARS = (2023, 2024, 2025)
OUT = CAL / "_caiso243_arm_vs_keeper.json"

#: PRECOMMIT §3 / §5.6 — the two-sided price-leg envelope on B1 − KEEPER.
ENVELOPE = {2023: (0.0, 0.0), 2024: (0.0, 0.0), 2025: (-2.6339, 0.3109)}
#: PRECOMMIT §4 P-2 — the registered prediction window for 2025.
P2_WINDOW = (-0.60, 0.00)
#: caiso-240 §0.7(1) dispatch-identity tolerance (TWh per class).
INERT_TOL_TWH = 0.001
#: keeper monthly-mean CC_REGULAR dispatch, Nov-2025 (precommit P-4 baseline).
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH_OF_HOUR = np.concatenate([np.full(d * 24, m + 1) for m, d in enumerate(_DAYS)])


def _system(bundle: Path, year: int) -> pd.DataFrame | None:
    p = bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    return df[(df["year"] == year) & (df["pass"] == "P1")]


def _classes(bundle: Path, year: int) -> pd.DataFrame | None:
    p = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    return df[(df["year"] == year) & (df["pass"] == "P1")]


def _class_twh(df: pd.DataFrame | None) -> dict[str, float]:
    if df is None:
        return {}
    return {
        str(k): float(v) / 1e6
        for k, v in df.groupby("klass", observed=True)["mw"].sum().items()
    }


def _lw_mean(df: pd.DataFrame | None) -> float | None:
    if df is None:
        return None
    return float(np.average(df["price"], weights=df["demand"]))


def _monthly_mean(df: pd.DataFrame | None, klass: str) -> dict[int, float]:
    if df is None:
        return {}
    sub = df[df["klass"] == klass]
    mo = MONTH_OF_HOUR[sub["hour"].to_numpy().astype(int)]
    return {int(m): float(v) for m, v in sub.groupby(mo)["mw"].mean().items()}


def _tail_hours(df: pd.DataFrame | None) -> int | None:
    if df is None:
        return None
    return int((df.groupby("hour")["price"].max() > 200.0).sum())


def _metrics(bundle: Path) -> dict:
    p = bundle / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _verdicts(m: dict) -> dict[str, str]:
    return {k: v.get("status", "?") for k, v in (m.get("criteria") or {}).items()}


def _c3a_records(bundle: Path) -> dict[int, dict]:
    """Per-year C3a model/actual/magnitude from the scorer's machine verdict."""
    p = bundle / "_verdict.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text())
    out = {}
    for r in d.get("criteria", {}).get("price_mean", {}).get("records") or []:
        if r.get("key") is None:
            out[int(r["year"])] = {
                k: r.get(k) for k in ("status", "model", "actual", "magnitude")
            }
    return out


def _dof(bundle: Path) -> dict:
    p = bundle / "calibration_attestation.json"
    if not p.exists():
        return {}
    fp = json.loads(p.read_text()).get("free_parameters") or {}
    return {"n_entries": fp.get("n_entries"), "n_residual": fp.get("n_residual")}


def main() -> None:
    out: dict = {
        "_provenance": {
            "session": "caiso-243",
            "keeper": str(KEEPER.relative_to(REPO)),
            "arm": str(B1.relative_to(REPO)),
            "control": "NONE — G-CTRL form 2 (owner's choice): the arm's inert years are the control",
            "solves_by_this_probe": 0,
        }
    }
    mk, mb = _metrics(KEEPER), _metrics(B1)
    vk, vb = _verdicts(mk), _verdicts(mb)
    verdict_diff = {
        k: (vk.get(k), vb.get(k)) for k in set(vk) | set(vb) if vk.get(k) != vb.get(k)
    }
    out["verdicts"] = {"keeper": vk, "arm": vb, "differing": verdict_diff}
    out["determinations"] = {
        "keeper": {
            "determination": mk.get("determination"),
            "reasons": mk.get("reasons"),
            "caveats": (mk.get("caveats") or {}).get("ledgered"),
        },
        "arm": {
            "determination": mb.get("determination"),
            "reasons": mb.get("reasons"),
            "caveats": (mb.get("caveats") or {}).get("ledgered"),
        },
    }
    c3a_k, c3a_b = _c3a_records(KEEPER), _c3a_records(B1)

    per_year: dict = {}
    inert_ok = {}
    for year in YEARS:
        sk, sb = _system(KEEPER, year), _system(B1, year)
        ck, cb = _classes(KEEPER, year), _classes(B1, year)
        tk, tb = _class_twh(ck), _class_twh(cb)
        classes = sorted(set(tk) | set(tb))
        deltas = {k: tb.get(k, 0.0) - tk.get(k, 0.0) for k in classes}
        maxd = max((abs(v) for v in deltas.values()), default=0.0)
        lw_k, lw_b = _lw_mean(sk), _lw_mean(sb)
        row: dict = {
            "class_twh_keeper": {k: round(v, 4) for k, v in tk.items()},
            "class_twh_arm": {k: round(v, 4) for k, v in tb.items()},
            "class_twh_delta": {
                k: round(v, 6) for k, v in deltas.items() if abs(v) > 1e-6
            },
            "max_abs_class_delta_twh": round(maxd, 6),
            "year_is_inert_0.001TWh": bool(maxd <= INERT_TOL_TWH),
            "lw_mean_price_keeper": round(lw_k, 4) if lw_k is not None else None,
            "lw_mean_price_arm": round(lw_b, 4) if lw_b is not None else None,
        }
        if lw_k is not None and lw_b is not None:
            d = lw_b - lw_k
            lo, hi = ENVELOPE[year]
            tol = 1e-6 if lo == hi == 0.0 else 0.0
            row["dC3a_lw_arm_minus_keeper"] = round(d, 6)
            row["envelope"] = [lo, hi]
            row["envelope_PASS"] = bool(lo - tol <= d <= hi + tol)
            # simple hour-mean (the caiso-241 scorer's convention), reported alongside
            row["d_simple_mean_price"] = round(
                float(
                    sb.groupby("hour")["price"].mean().mean()
                    - sk.groupby("hour")["price"].mean().mean()
                ),
                6,
            )
            if sk is not None and sb is not None and year in (2023, 2024):
                a = sk.sort_values(["zone", "hour"])["price"].to_numpy()
                b = sb.sort_values(["zone", "hour"])["price"].to_numpy()
                row["price_max_abs_diff"] = (
                    float(np.abs(a - b).max()) if a.shape == b.shape else None
                )
        row["c3a_record_keeper"] = c3a_k.get(year)
        row["c3a_record_arm"] = c3a_b.get(year)
        row["h_gt200_keeper"] = _tail_hours(sk)
        row["h_gt200_arm"] = _tail_hours(sb)
        if year == 2025:
            mk_cc, mb_cc = (
                _monthly_mean(ck, "CC_REGULAR"),
                _monthly_mean(cb, "CC_REGULAR"),
            )
            row["cc_regular_monthly_mean_mw"] = {
                "keeper": {m: round(v, 1) for m, v in mk_cc.items()},
                "arm": {m: round(v, 1) for m, v in mb_cc.items()},
            }
            row["cc_regular_nov_delta_mw"] = round(
                mb_cc.get(11, 0.0) - mk_cc.get(11, 0.0), 1
            )
            for kl in ("CT_PEAKER", "import"):
                a_, b_ = _monthly_mean(ck, kl), _monthly_mean(cb, kl)
                row[f"{kl}_sep_oct_nov_mean_mw"] = {
                    "keeper": [round(a_.get(m, 0.0), 1) for m in (9, 10, 11)],
                    "arm": [round(b_.get(m, 0.0), 1) for m in (9, 10, 11)],
                }
        inert_ok[year] = row["year_is_inert_0.001TWh"]
        per_year[str(year)] = row
        print(
            f"[{year}] dC3a(lw) {row.get('dC3a_lw_arm_minus_keeper')} envelope {row.get('envelope')} PASS={row.get('envelope_PASS')} | max class Δ {row['max_abs_class_delta_twh']} TWh inert={row['year_is_inert_0.001TWh']} | h>200 {row['h_gt200_keeper']}->{row['h_gt200_arm']}"
        )
    out["per_year"] = per_year

    # ---- gates
    out["gates"] = {
        "G_CTRL_form2": {
            "PASS": bool(inert_ok.get(2023) and inert_ok.get(2024)),
            "falsifier": "an inert year's class energy moving > 0.001 TWh ⇒ a control solve is spent (form 3)",
        },
        "G_INERT": {
            "PASS": not inert_ok.get(2025, True),
            "falsifier": "2025 byte-identical to the keeper",
        },
        "G_C3a_envelope": {
            "PASS": all(per_year[str(y)].get("envelope_PASS", False) for y in YEARS),
            "falsifier": "any year outside its envelope ⇒ estimator/mechanism defect, reported, never re-fitted",
        },
        "G_verdicts_identity_C1_C3b_C8_CAVEAT_C6": {
            "PASS": not verdict_diff and bool(vk) and bool(vb),
            "differing": verdict_diff,
        },
    }
    # ---- predictions
    d25 = per_year["2025"].get("dC3a_lw_arm_minus_keeper")
    cc = per_year["2025"]["class_twh_delta"].get("CC_REGULAR", 0.0)
    ct = per_year["2025"]["class_twh_delta"].get("CT_PEAKER", 0.0)
    imp = per_year["2025"]["class_twh_delta"].get("import", 0.0)
    dof_k, dof_b = _dof(KEEPER), _dof(B1)
    out["predictions"] = {
        "P1_inert_years_reproduce_keeper": {
            "HOLDS": out["gates"]["G_CTRL_form2"]["PASS"],
            "max_delta_2023": per_year["2023"]["max_abs_class_delta_twh"],
            "max_delta_2024": per_year["2024"]["max_abs_class_delta_twh"],
        },
        "P2_dC3a_2025_in_window_and_no_verdict_flip": {
            "window": list(P2_WINDOW),
            "measured": d25,
            "c3a_verdicts_keeper": {
                y: (c3a_k.get(y) or {}).get("status") for y in YEARS
            },
            "c3a_verdicts_arm": {y: (c3a_b.get(y) or {}).get("status") for y in YEARS},
            "HOLDS": bool(
                d25 is not None
                and P2_WINDOW[0] <= d25 <= P2_WINDOW[1]
                and all(
                    (c3a_k.get(y) or {}).get("status")
                    == (c3a_b.get(y) or {}).get("status")
                    for y in YEARS
                )
            ),
        },
        "P3_dC3a_2023_2024_exactly_zero": {
            "HOLDS": bool(
                abs(per_year["2023"].get("dC3a_lw_arm_minus_keeper") or 0.0) < 1e-6
                and abs(per_year["2024"].get("dC3a_lw_arm_minus_keeper") or 0.0) < 1e-6
            )
        },
        "P4_cc_regular_2025_rise_lt_0.5TWh_and_nov_lt_500MW": {
            "delta_twh": round(cc, 4),
            "nov_delta_mw": per_year["2025"].get("cc_regular_nov_delta_mw"),
            "HOLDS": bool(
                cc < 0.5
                and (per_year["2025"].get("cc_regular_nov_delta_mw") or 0.0) < 500.0
            ),
        },
        "P5_ct_peaker_2025_falls_and_imports_fall_less_than_cc_rises": {
            "ct_peaker_delta_twh": round(ct, 4),
            "import_delta_twh": round(imp, 4),
            "cc_regular_delta_twh": round(cc, 4),
            "HOLDS": bool(ct < 0.0 and (-imp) < cc),
        },
        "P6_no_verdict_change_C3c2025_stays_0h": {
            "differing": verdict_diff,
            "h_gt200_2025": [
                per_year["2025"]["h_gt200_keeper"],
                per_year["2025"]["h_gt200_arm"],
            ],
            "HOLDS": bool(not verdict_diff and per_year["2025"]["h_gt200_arm"] == 0),
        },
        "P7_dof_ledger_unmoved": {
            "keeper": dof_k,
            "arm": dof_b,
            "HOLDS": bool(dof_k and dof_b and dof_k == dof_b),
        },
        "P8_gstruct": "scored pre-solve in _caiso243_gstruct_presolve.json (PASS, byte-identical in every case)",
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out["gates"], indent=1))
    print(
        json.dumps(
            {
                k: (v.get("HOLDS") if isinstance(v, dict) else v)
                for k, v in out["predictions"].items()
            },
            indent=1,
        )
    )
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
