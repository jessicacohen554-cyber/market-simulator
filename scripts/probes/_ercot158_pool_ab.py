#!/usr/bin/env python3
"""ercot-158 A/B scorer — the ERCOT-88 fast-start pool armed with its 2023 block.

Scores **only** the gates pre-registered in
``docs/PRECOMMIT-ercot158-faststart-pool-arm-2026-08-03.md`` §4, Run A
(``ercot158_honest_A``, the honest-inputs zero-delta control) vs Run B
(``ercot158_poolarm_B``, single delta ``ercot_faststart_pool_offer=true``):

* The four standing ERCOT-89 analyzer gates, computed with the EXACT
  ``_ercot89_span_check.year_stats`` semantics (imported, never re-coded):
  C3a level guard (|resid| may rise <= 1.0 pp), zero-spurious
  (mid-band-model / actual<$150 delta <= 0), tail-count (h>$200 must not move
  AWAY from actual), NRMSE (<= base + 0.005) — per year, each of 2023-2025.
* The matched-hour C3c anatomy (the ercot148/149 discipline) on the Phase-0
  hour sets re-derived on Run A's own prices (2023 actual RT > $300; missed =
  load-weighted zonal model < $200 — the ercot101/phase0 basis, which is
  exactly ``eff_price``): A->B movement at the missed/hit sets, flips, and
  the ZERO-new-spurious-tail rule (every new model>$300 hour must lie inside
  the actual>$300 set; all three years).
* Scorecard non-degradation from each bundle's own ``metrics.json``
  (``calibration_verdict --write-metrics`` output, never re-derived): no
  criterion PASS in A may be FAIL in B; plus the per-(criterion, year, key)
  row comparison over the captured full verdicts
  (``_ercot158_verdict_{A,B}.json``) — the ercot150 P2 both-grains test.
* Zero-forced-energy: the pool is an offer-availability; B's
  ``legitimacy_diagnostics.json`` D-2 mechanism-id set must equal A's (no new
  forcing mechanism), forced-share rows unchanged within noise.

Read-only: consumes the two bundles' parquet/JSON outputs and the committed
actual RT parquet; solves nothing, registers nothing. Writes
``results/calibration/_ercot158_pool_ab.json``.

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_ercot158_pool_ab.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RUN_A = REPO / "results/calibration/ercot158_honest_A"
RUN_B = REPO / "results/calibration/ercot158_poolarm_B"
VERDICT_A = REPO / "results/calibration/_ercot158_verdict_A.json"
VERDICT_B = REPO / "results/calibration/_ercot158_verdict_B.json"
OUT_PATH = REPO / "results/calibration/_ercot158_pool_ab.json"
YEARS = (2023, 2024, 2025)
TAIL = 300.0  # Phase-0 scarcity-tail threshold, $/MWh (ercot151_offline_phase0)
MISS_MODEL_LT = 200.0  # Phase-0 "missed" model bar, $/MWh (ercot101 basis)

# One source of truth for the gate semantics: import the standing ERCOT-89
# analyzer and call its own year_stats/eff_price (charter §7 pre-committed
# gates; PRECOMMIT-ercot158 §4 binds this file to those exact definitions).
_spec = importlib.util.spec_from_file_location(
    "_ercot89_span_check", REPO / "scripts/probes/_ercot89_span_check.py"
)
_e89 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_e89)


def _hourly(bundle: Path) -> Path:
    """The dir eff_price reads (bundle hourly sidecars)."""
    return bundle / "hourly" if (bundle / "hourly").exists() else bundle


def gates_e89(actual: pd.DataFrame) -> dict:
    """The four standing analyzer gates per year, Run A (base) -> Run B."""
    out: dict = {}
    for y in YEARS:
        b = _e89.year_stats(_e89.eff_price(_hourly(RUN_A), y), actual, y)
        p = _e89.year_stats(_e89.eff_price(_hourly(RUN_B), y), actual, y)
        d_spur = p["spurious"] - b["spurious"]
        away = abs(p["h200_model"] - b["h200_actual"]) > abs(
            b["h200_model"] - b["h200_actual"]
        )
        out[str(y)] = {
            "base": b,
            "probe": p,
            "gates": {
                "C3a_level": (
                    "HELD"
                    if abs(p["resid_pct"]) <= abs(b["resid_pct"]) + 1.0
                    else "DEGRADED"
                ),
                "zero_spurious": "HELD" if d_spur <= 0 else "TRIPPED",
                "tail_count": "HELD" if not away else "DEGRADED",
                "nrmse": "HELD" if p["nrmse"] <= b["nrmse"] + 0.005 else "DEGRADED",
            },
            "spurious_delta": int(d_spur),
        }
    return out


def anatomy_c3c(actual: pd.DataFrame) -> dict:
    """Matched-hour C3c anatomy on the Phase-0 sets (Run A basis) + all-year
    spurious-tail census at the $300 grain."""
    out: dict = {}
    for y in YEARS:
        m_a = _e89.eff_price(_hourly(RUN_A), y)
        m_b = _e89.eff_price(_hourly(RUN_B), y)
        act = (
            actual[actual["year"] == y]
            .set_index("hour")["rt"]
            .reindex(range(len(m_a)))
            .to_numpy(float)
        )
        tail_act = np.flatnonzero(act > TAIL)
        tail_a = np.flatnonzero(m_a > TAIL)
        tail_b = np.flatnonzero(m_b > TAIL)
        new_tail = np.setdiff1d(tail_b, tail_a)
        new_inside = np.intersect1d(new_tail, tail_act)
        new_outside = np.setdiff1d(new_tail, tail_act)
        spur_a = np.setdiff1d(tail_a, tail_act)
        spur_b = np.setdiff1d(tail_b, tail_act)
        row = {
            "actual_tail_hours": int(tail_act.size),
            "model_tail_hours_A": int(tail_a.size),
            "model_tail_hours_B": int(tail_b.size),
            "new_tail_hours_B": int(new_tail.size),
            "new_tail_inside_actual": int(new_inside.size),
            "new_tail_outside_actual_KILL": int(new_outside.size),
            "spurious_tail_A": int(spur_a.size),
            "spurious_tail_B": int(spur_b.size),
        }
        if y == 2023:
            missed = tail_act[m_a[tail_act] < MISS_MODEL_LT]
            hit = tail_act[m_a[tail_act] >= MISS_MODEL_LT]
            flips = missed[m_b[missed] >= TAIL]
            row["phase0_rederived"] = {
                "missed_A": int(missed.size),
                "hit_A": int(hit.size),
                "missed_model_mean_A": float(np.nanmean(m_a[missed])),
                "missed_model_mean_B": float(np.nanmean(m_b[missed])),
                "missed_model_p50_A": float(np.nanmedian(m_a[missed])),
                "missed_model_p50_B": float(np.nanmedian(m_b[missed])),
                "missed_actual_mean": float(np.nanmean(act[missed])),
                "missed_flipped_to_tail_B": int(flips.size),
                "missed_delta_mean": float(
                    np.nanmean(m_b[missed]) - np.nanmean(m_a[missed])
                ),
                "hit_model_mean_A": float(np.nanmean(m_a[hit])) if hit.size else None,
                "hit_model_mean_B": float(np.nanmean(m_b[hit])) if hit.size else None,
            }
        out[str(y)] = row
    return out


def scorecard_holds() -> dict:
    """Criterion-status non-degradation from the two metrics.json, plus the
    per-(criterion, year, key) row grain over the captured full verdicts."""
    res: dict = {"available": False}
    ma, mb = RUN_A / "metrics.json", RUN_B / "metrics.json"
    if not (ma.exists() and mb.exists()):
        res["note"] = "metrics.json missing — run calibration_verdict --write-metrics"
        return res
    a, b = json.loads(ma.read_text()), json.loads(mb.read_text())
    ca = {k: v.get("status") for k, v in a["criteria"].items()}
    cb = {k: v.get("status") for k, v in b["criteria"].items()}
    degraded = sorted(
        k for k, s in ca.items() if s == "PASS" and cb.get(k) == "FAIL"
    )
    res.update(
        {
            "available": True,
            "determination_A": a.get("determination"),
            "determination_B": b.get("determination"),
            "criteria_A": ca,
            "criteria_B": cb,
            "pass_to_fail_KILL": degraded,
        }
    )
    if VERDICT_A.exists() and VERDICT_B.exists():
        va = json.loads(VERDICT_A.read_text())
        vb = json.loads(VERDICT_B.read_text())

        def _rows(v: dict) -> dict:
            rows = {}
            for cid, crit in (v.get("criteria") or {}).items():
                for r in crit.get("records", []) or []:
                    key = (str(cid), str(r.get("year")), str(r.get("key")))
                    rows["|".join(key)] = r.get("status")
            return rows

        ra, rb = _rows(va), _rows(vb)
        flips = sorted(
            k for k, s in ra.items() if s == "PASS" and rb.get(k) == "FAIL"
        )
        res["row_grain_pass_to_fail_KILL"] = flips
        res["row_grain_rows_compared"] = len(ra)
    return res


def zero_forced() -> dict:
    """D-2 mechanism-id parity: the pool must add no forcing mechanism."""
    res: dict = {"available": False}
    la, lb = RUN_A / "legitimacy_diagnostics.json", RUN_B / "legitimacy_diagnostics.json"
    if not (la.exists() and lb.exists()):
        res["note"] = "legitimacy_diagnostics.json missing on a bundle"
        return res
    a, b = json.loads(la.read_text()), json.loads(lb.read_text())

    def _d2(d: dict) -> dict:
        rows = (d.get("diagnostics") or {}).get("D2", {}).get("rows", []) or []
        return {
            f"{r['year']}|{r['class']}|{r['mechanism']}": float(r["forced_twh"])
            for r in rows
        }

    ra, rb = _d2(a), _d2(b)
    new_keys = sorted(set(rb) - set(ra))
    deltas = {
        k: round(rb[k] - ra[k], 4)
        for k in sorted(set(ra) & set(rb))
        if abs(rb[k] - ra[k]) > 0.05  # TWh noise floor on forced attribution
    }
    res.update(
        {
            "available": True,
            "d2_mechanisms_A": sorted({k.split("|")[2] for k in ra}),
            "d2_mechanisms_B": sorted({k.split("|")[2] for k in rb}),
            "new_forcing_rows_in_B_KILL": new_keys,
            "forced_twh_deltas_gt_0p05": deltas,
            "d2_passed_A": (a.get("diagnostics") or {}).get("D2", {}).get("passed"),
            "d2_passed_B": (b.get("diagnostics") or {}).get("D2", {}).get("passed"),
        }
    )
    return res


def main() -> None:
    """Score the pre-registered ercot-158 gate set and write the record."""
    actual = pd.read_parquet(_e89.ACTUAL_LMP)
    res = {
        "_doc": "PRECOMMIT-ercot158-faststart-pool-arm-2026-08-03.md §4 gates; "
        "Run A ercot158_honest_A (base) vs Run B ercot158_poolarm_B",
        "e89_gates": gates_e89(actual),
        "c3c_anatomy": anatomy_c3c(actual),
        "scorecard": scorecard_holds(),
        "zero_forced": zero_forced(),
    }
    kills: list[str] = []
    for y, blk in res["e89_gates"].items():
        for g, s in blk["gates"].items():
            if s != "HELD":
                kills.append(f"{y}:{g}={s}")
    for y, blk in res["c3c_anatomy"].items():
        if blk["new_tail_outside_actual_KILL"]:
            kills.append(f"{y}:new_tail_outside_actual={blk['new_tail_outside_actual_KILL']}")
    if res["scorecard"].get("pass_to_fail_KILL"):
        kills.append(f"scorecard:{res['scorecard']['pass_to_fail_KILL']}")
    if res["scorecard"].get("row_grain_pass_to_fail_KILL"):
        kills.append(f"rows:{res['scorecard']['row_grain_pass_to_fail_KILL']}")
    if res["zero_forced"].get("new_forcing_rows_in_B_KILL"):
        kills.append(f"d2:{res['zero_forced']['new_forcing_rows_in_B_KILL']}")
    res["kills_fired"] = kills
    res["all_gates_held"] = not kills

    OUT_PATH.write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(f"wrote {OUT_PATH.relative_to(REPO)}")
    for y in map(str, YEARS):
        g = res["e89_gates"][y]
        print(
            f"{y}: C3a {g['base']['resid_pct']:+.1f}% -> {g['probe']['resid_pct']:+.1f}%"
            f" | spurΔ {g['spurious_delta']:+d}"
            f" | h>$200 {g['base']['h200_model']}->{g['probe']['h200_model']}"
            f" (act {g['base']['h200_actual']})"
            f" | NRMSE {g['base']['nrmse']:.3f}->{g['probe']['nrmse']:.3f}"
            f" | gates {g['gates']}"
        )
    a23 = res["c3c_anatomy"]["2023"].get("phase0_rederived", {})
    if a23:
        print(
            f"2023 matched-hour: missed {a23['missed_A']} (mean "
            f"${a23['missed_model_mean_A']:.0f} -> ${a23['missed_model_mean_B']:.0f}, "
            f"actual ${a23['missed_actual_mean']:.0f}); flips {a23['missed_flipped_to_tail_B']}"
        )
    print("KILLS:", kills or "none — all gates held")


if __name__ == "__main__":
    main()
