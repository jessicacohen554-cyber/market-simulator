"""caiso-246 — B1 (arm) vs the committed keeper: gates and predictions, scored against interest.

NO LP. Reads two committed bundles' hourly sidecars, metrics and attestations:

  * KEEPER — ``caiso243_b1_f923_fallback_guard`` (run 2026-09-04-caiso-243-b1-f923)
  * B1     — ``caiso246_b1_spot_coverage`` (keeper recipe + the single flag
             ``caiso_citygate_spot_coverage``: the spot-level hub overlay
             covers a month on its own daily citygate prints where the EIA
             N3050CA3 survey published NA — Sep/Oct/Nov 2025)

G-CTRL is FORM 2 (owner's caiso-241 §B2 carve-out, PRECOMMIT-caiso246 §1): the
arm has two measured-inert years (2023, 2024 — 12/12 survey coverage, 0 rows
in the pre-solve footprint), so the arm's own inert years are the HEAD-drift
control: class energies must reproduce the keeper's to 0.001 TWh in every
class and the load-weighted price to 1e-6 $/MWh. No control solve is spent.

Scored here, each against the precommit's registered falsifier: G-CTRL (form
2), G-INERT, G-C3a envelope leg (annual LOAD-WEIGHTED mean price move,
[-3.1376, +0.1849] for 2025 from ``_caiso246_coverage_footprint.json``, exactly
0 for the inert years), G-C1 / G-C3b / G-C8 / G-CAVEAT / G-C6 (verdict identity
from metrics.json), P-3…P-8 (P-1/P-2 were scored pre-solve in
``_caiso246_coverage_footprint.json``).

P-6 uses the bench's monthly RT load-weighted actual (``avgLMP.rt_lw_mon``)
and P-8 the caiso-244 dual-merit reconstruction (import row marginal at its
WECC node AND the corridor link unbound), rebuilt on-recipe for EACH bundle.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso246_arm_vs_keeper.py
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

CAL = REPO / "results/calibration"
KEEPER = CAL / "caiso243_b1_f923_fallback_guard"
B1 = CAL / "caiso246_b1_spot_coverage"
YEARS = (2023, 2024, 2025)
OUT = CAL / "_caiso246_arm_vs_keeper.json"
BENCH = REPO / "frontend/data/backcast/bench/CAISO"
CA_ZONES = ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest")

#: PRECOMMIT-caiso246 §1 G-C3a envelope leg — registered pre-solve in
#: _caiso246_coverage_footprint.json (two-sided, on the assembled P0 offers).
ENVELOPE = {2023: (0.0, 0.0), 2024: (0.0, 0.0), 2025: (-3.1376, 0.1849)}
#: PRECOMMIT §2 P-3 — the registered prediction window for ΔC3a-2025.
P3_WINDOW = (-1.0, -0.2)
#: PRECOMMIT §2 P-5 — CC_REGULAR-2025 rise window (TWh).
P5_CC_WINDOW = (0.3, 1.0)
#: PRECOMMIT §2 P-6 — Sep/Oct/Nov slab shrink ≥ 1.0 $/MWh each; Dec |move| ≤ 0.3.
P6_LIVE_SHRINK = 1.0
P6_DEC_MAX = 0.3
#: PRECOMMIT §2 P-8 — import-marginal share 2025 rises ≥ 1 point.
P8_MIN_POINTS = 1.0
#: caiso-240 §0.7(1) dispatch-identity tolerance (TWh per class).
INERT_TOL_TWH = 0.001
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH_OF_HOUR = np.concatenate([np.full(d * 24, m + 1) for m, d in enumerate(_DAYS)])
HOURS = 8760

_spec = importlib.util.spec_from_file_location(
    "_caiso244_import_level_anatomy",
    REPO / "scripts/probes/_caiso244_import_level_anatomy.py",
)
C244 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C244)


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
    if df is None or df.empty:
        return None
    return float(np.average(df["price"], weights=df["demand"]))


def _monthly_mean(df: pd.DataFrame | None, klass: str) -> dict[int, float]:
    if df is None:
        return {}
    sub = df[df["klass"] == klass]
    mo = MONTH_OF_HOUR[sub["hour"].to_numpy(int)]
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
    m = _metrics(bundle)
    out: dict[int, dict] = {}
    for rec in ((m.get("criteria") or {}).get("price_mean") or {}).get("records", []):
        out[int(rec["year"])] = {
            k: rec.get(k) for k in ("status", "model", "actual", "pct", "delta")
        }
    return out


def _dof(bundle: Path) -> dict:
    p = bundle / "calibration_attestation.json"
    if not p.exists():
        return {}
    fp = json.loads(p.read_text()).get("free_parameters") or {}
    return {"n_entries": fp.get("n_entries"), "n_residual": fp.get("n_residual")}


def _monthly_slab(bundle: Path, year: int) -> dict[int, float] | None:
    """Model − actual RT (bench avgLMP.rt_lw_mon) load-weighted mean by month."""
    s = _system(bundle, year)
    bench_p = BENCH / f"{year}.json.gz"
    if s is None or not bench_p.exists():
        return None
    price = s.pivot(index="zone", columns="hour", values="price").reindex(
        columns=range(HOURS)
    )
    demand = s.pivot(index="zone", columns="hour", values="demand").reindex(
        columns=range(HOURS)
    )
    p = price.loc[list(CA_ZONES)].to_numpy(float)
    d = demand.loc[list(CA_ZONES)].to_numpy(float)
    lw = (p * d).sum(axis=0) / np.maximum(d.sum(axis=0), 1e-9)
    bench = json.load(gzip.open(bench_p))["bench"]["avgLMP"]
    return {
        m: round(
            float(lw[MONTH_OF_HOUR == m].mean()) - float(bench["rt_lw_mon"][m - 1]), 3
        )
        for m in range(1, 13)
    }


def _import_marginal_share(bundle: Path, year: int) -> float:
    """caiso-244 §3.6 share of hours an import row is marginal AND its link unbound."""
    C244.BUNDLE = bundle
    fl = C244.rebuild(year)
    price, klass_import, _ = C244.sidecars(year)
    _, _, state, lam, _, _ = C244.reconstruct(fl, price, klass_import)
    marg_unbound = np.zeros(HOURS, dtype=bool)
    for i, row in enumerate(fl["rows"]):
        if row["is_export"]:
            continue
        lam_l = price.loc[C244.CORRIDOR_LANDING[row["zone"]]].to_numpy(float)
        marg_unbound |= (state[i] == 0) & (np.abs(lam[i] - lam_l) <= C244.TOL)
    return float(marg_unbound.mean())


def main() -> None:
    out: dict = {
        "_provenance": {
            "session": "caiso-246",
            "keeper": str(KEEPER.relative_to(REPO)),
            "arm": str(B1.relative_to(REPO)),
            "control": "NONE — G-CTRL form 2 (owner's caiso-241 §B2 carve-out): the arm's inert years are the control",
            "solves_by_this_probe": 0,
            "precommit": "PRECOMMIT-caiso246-spot-coverage-2026-09-04.md §1/§2/§4",
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
            row["d_simple_mean_price"] = round(
                float(
                    sb.groupby("hour")["price"].mean().mean()
                    - sk.groupby("hour")["price"].mean().mean()
                ),
                6,
            )
            if year in (2023, 2024):
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
            for kl in ("CC_REGULAR", "CT_PEAKER", "import", "ST_GAS", "CC_CHP"):
                a_, b_ = _monthly_mean(ck, kl), _monthly_mean(cb, kl)
                row[f"{kl}_sep_oct_nov_dec_mean_mw"] = {
                    "keeper": [round(a_.get(m, 0.0), 1) for m in (9, 10, 11, 12)],
                    "arm": [round(b_.get(m, 0.0), 1) for m in (9, 10, 11, 12)],
                }
            slab_k, slab_b = _monthly_slab(KEEPER, year), _monthly_slab(B1, year)
            row["model_minus_actual_rt_by_month"] = {"keeper": slab_k, "arm": slab_b}
            if slab_k and slab_b:
                row["slab_move_by_month"] = {
                    m: round(slab_b[m] - slab_k[m], 3) for m in range(1, 13)
                }
        inert_ok[year] = row["year_is_inert_0.001TWh"]
        per_year[str(year)] = row
        print(
            f"[{year}] dC3a(lw) {row.get('dC3a_lw_arm_minus_keeper')} envelope {row.get('envelope')} PASS={row.get('envelope_PASS')} | max class Δ {row['max_abs_class_delta_twh']} TWh inert={row['year_is_inert_0.001TWh']} | h>200 {row['h_gt200_keeper']}->{row['h_gt200_arm']}"
        )
    out["per_year"] = per_year

    # P-8: import-marginal share, 2025, both bundles (on-recipe rebuilds, zero LP)
    share_k = _import_marginal_share(KEEPER, 2025)
    share_b = _import_marginal_share(B1, 2025)
    per_year["2025"]["import_marginal_share"] = {
        "keeper": round(share_k, 4),
        "arm": round(share_b, 4),
        "delta_points": round(100.0 * (share_b - share_k), 3),
    }

    out["gates"] = {
        "G_CTRL_form2": {
            "PASS": bool(inert_ok.get(2023) and inert_ok.get(2024)),
            "price_max_abs_diff": {
                y: per_year[str(y)].get("price_max_abs_diff") for y in (2023, 2024)
            },
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

    d25 = per_year["2025"].get("dC3a_lw_arm_minus_keeper")
    cc = per_year["2025"]["class_twh_delta"].get("CC_REGULAR", 0.0)
    ct = per_year["2025"]["class_twh_delta"].get("CT_PEAKER", 0.0)
    imp = per_year["2025"]["class_twh_delta"].get("import", 0.0)
    slab_move = per_year["2025"].get("slab_move_by_month") or {}
    dof_k, dof_b = _dof(KEEPER), _dof(B1)
    same_c3a_verdicts = all(
        (c3a_k.get(y) or {}).get("status") == (c3a_b.get(y) or {}).get("status")
        for y in YEARS
    )
    out["predictions"] = {
        "P1_gstruct": "scored pre-solve in _caiso246_coverage_footprint.json (HOLDS: gas rows only, Sep–Nov 2025 only, 0 rows 2023/2024)",
        "P2_nov_capwt_3.5_3.8_and_55077": "scored pre-solve in _caiso246_coverage_footprint.json (HOLDS: Nov capwt 5.5714→3.7643 $/MMBtu; 55077 Nov 96.161→3.764)",
        "P3_dC3a_2025_in_window_and_no_verdict_flip": {
            "window": list(P3_WINDOW),
            "measured": d25,
            "c3a_verdicts_keeper": {
                y: (c3a_k.get(y) or {}).get("status") for y in YEARS
            },
            "c3a_verdicts_arm": {y: (c3a_b.get(y) or {}).get("status") for y in YEARS},
            "HOLDS": bool(
                d25 is not None
                and P3_WINDOW[0] <= d25 <= P3_WINDOW[1]
                and same_c3a_verdicts
            ),
        },
        "P4_dC3a_2023_2024_exactly_zero": {
            "HOLDS": bool(
                abs(per_year["2023"].get("dC3a_lw_arm_minus_keeper") or 0.0) < 1e-6
                and abs(per_year["2024"].get("dC3a_lw_arm_minus_keeper") or 0.0) < 1e-6
            )
        },
        "P5_cc_rise_0.3_1.0_imports_fall_more_than_cc_rises_ct_falls": {
            "cc_regular_delta_twh": round(cc, 4),
            "import_delta_twh": round(imp, 4),
            "ct_peaker_delta_twh": round(ct, 4),
            "HOLDS": bool(
                P5_CC_WINDOW[0] <= cc <= P5_CC_WINDOW[1] and (-imp) > cc and ct < 0.0
            ),
        },
        "P6_sep_oct_nov_slab_shrinks_ge_1_dec_moves_le_0.3": {
            "slab_move_by_month": slab_move,
            "HOLDS": bool(
                slab_move
                and all(slab_move[m] <= -P6_LIVE_SHRINK for m in (9, 10, 11))
                and abs(slab_move[12]) <= P6_DEC_MAX
            ),
        },
        "P7_c3c2025_0h_c1_c8_dof_unchanged": {
            "differing": verdict_diff,
            "h_gt200_2025": [
                per_year["2025"]["h_gt200_keeper"],
                per_year["2025"]["h_gt200_arm"],
            ],
            "dof": {"keeper": dof_k, "arm": dof_b},
            "HOLDS": bool(
                not verdict_diff
                and per_year["2025"]["h_gt200_arm"] == 0
                and dof_k
                and dof_b
                and dof_k == dof_b
            ),
        },
        "P8_import_marginal_share_2025_up_ge_1_point": {
            **per_year["2025"]["import_marginal_share"],
            "HOLDS": bool(100.0 * (share_b - share_k) >= P8_MIN_POINTS),
        },
    }
    OUT.write_text(json.dumps(out, indent=2, default=float) + "\n")
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
