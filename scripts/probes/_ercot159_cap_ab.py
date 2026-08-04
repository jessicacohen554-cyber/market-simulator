#!/usr/bin/env python3
"""ercot-159 A/B scorer — the energy-side online-capability cap (queue item 9).

Scores **only** the gates pre-registered in
``docs/PRECOMMIT-ercot159-energy-online-capability-cap-2026-08-04.md`` §6,
Run A (``ercot159_control_A``, zero-delta control replay) vs Run B
(``ercot159_cap_B``, single delta ``ercot_energy_online_capability_cap=true``):

* The four standing ERCOT-89 analyzer gates (imported from
  ``_ercot89_span_check``, never re-coded): C3a level (<= +1.0 pp), zero
  spurious, tail-count not-away, NRMSE (<= +0.005) — per year.
* **2024/2025 bit-identity** (ERCOT-159-specific): the frozen artifact carries
  a 2023 block only, so both later years must be BIT-IDENTICAL A->B in price
  (eff_price) and dispatch (class_hourly). Any delta is a wiring bug and a
  stop-the-line kill.
* Matched-hour C3c anatomy on the Phase-0 sets re-derived on Run A's own
  prices (2023: 91 missed / 53 hit), flips, and zero-new-spurious-tail.
* Scorecard non-degradation (metrics.json criterion grain + captured full
  verdicts ``_ercot159_verdict_{A,B}.json`` row grain) — this carries the
  pre-declared C1 16/16, C2 and C7 no-new-leg-failure holds.
* **Slack/dump guard** (quantity mechanism): per-year sums from the system
  sidecars; slack and dump deltas must stay within +0.1 % of annual demand.
* D-2 attribution: the cap adds NO floor and NO forced energy — a new D-2
  mechanism id in B is a kill; forced-TWh deltas > 0.05 on existing
  mechanisms are surfaced for escalation (the bridge detects from capped P0,
  so small shifts are expected and analyzed, not auto-killed).

Read-only; solves nothing, registers nothing. Writes
``results/calibration/_ercot159_cap_ab.json``.

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_ercot159_cap_ab.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RUN_A = REPO / "results/calibration/ercot159_control_A"
RUN_B = REPO / "results/calibration/ercot159_cap_B"
VERDICT_A = REPO / "results/calibration/_ercot159_verdict_A.json"
VERDICT_B = REPO / "results/calibration/_ercot159_verdict_B.json"
OUT_PATH = REPO / "results/calibration/_ercot159_cap_ab.json"
YEARS = (2023, 2024, 2025)
INERT_YEARS = (2024, 2025)  # artifact has a 2023 block only — must be bit-identical
TAIL = 300.0  # Phase-0 scarcity-tail threshold, $/MWh
MISS_MODEL_LT = 200.0  # Phase-0 "missed" model bar, $/MWh (ercot101 basis)
SLACK_GUARD_FRAC = 0.001  # slack/dump delta bound as a fraction of annual demand

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


def bit_identity() -> dict:
    """2024/2025 must be bit-identical A->B (no artifact block -> inert)."""
    out: dict = {}
    for y in INERT_YEARS:
        m_a = _e89.eff_price(_hourly(RUN_A), y)
        m_b = _e89.eff_price(_hourly(RUN_B), y)
        price_max_abs = float(np.nanmax(np.abs(m_b - m_a)))
        ca = pd.read_parquet(_hourly(RUN_A) / f"class_hourly_{y}.parquet")
        cb = pd.read_parquet(_hourly(RUN_B) / f"class_hourly_{y}.parquet")
        pa = ca.pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum", observed=True
        )
        pb = cb.pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum", observed=True
        )
        pa, pb = pa.align(pb, join="outer")
        disp_max_abs = float(np.nanmax(np.abs(pb.fillna(0.0) - pa.fillna(0.0)).to_numpy()))
        out[str(y)] = {
            "price_max_abs_delta": price_max_abs,
            "dispatch_max_abs_delta_mw": disp_max_abs,
            "bit_identical": bool(price_max_abs == 0.0 and disp_max_abs == 0.0),
        }
    return out


def anatomy_c3c(actual: pd.DataFrame) -> dict:
    """Matched-hour C3c anatomy on the Phase-0 sets (Run A basis)."""
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
        row = {
            "actual_tail_hours": int(tail_act.size),
            "model_tail_hours_A": int(tail_a.size),
            "model_tail_hours_B": int(tail_b.size),
            "new_tail_hours_B": int(new_tail.size),
            "new_tail_inside_actual": int(new_inside.size),
            "new_tail_outside_actual_KILL": int(new_outside.size),
            "spurious_tail_A": int(np.setdiff1d(tail_a, tail_act).size),
            "spurious_tail_B": int(np.setdiff1d(tail_b, tail_act).size),
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


def slack_dump_guard() -> dict:
    """Per-year slack/dump sums from the system sidecars; delta bound by
    SLACK_GUARD_FRAC x annual demand (the new upper-bound row must not shed
    load or strand energy)."""
    out: dict = {}
    for y in YEARS:
        sa = pd.read_parquet(_hourly(RUN_A) / f"system_{y}.parquet")
        sb = pd.read_parquet(_hourly(RUN_B) / f"system_{y}.parquet")
        if "pass" in sa.columns:
            sa = sa[sa["pass"] == "P1"]
        if "pass" in sb.columns:
            sb = sb[sb["pass"] == "P1"]
        demand = float(sa["demand"].sum())
        rows = {}
        breached = False
        for col in ("slack", "dump"):
            a_mwh = float(sa[col].sum())
            b_mwh = float(sb[col].sum())
            delta = b_mwh - a_mwh
            lim = SLACK_GUARD_FRAC * demand
            rows[col] = {
                "A_mwh": round(a_mwh, 1),
                "B_mwh": round(b_mwh, 1),
                "delta_mwh": round(delta, 1),
                "limit_mwh": round(lim, 1),
                "held": bool(delta <= lim),
            }
            breached = breached or delta > lim
        rows["guard"] = "BREACHED" if breached else "HELD"
        out[str(y)] = rows
    return out


def scorecard_holds() -> dict:
    """Criterion-status non-degradation + per-(criterion, year, key) row grain."""
    res: dict = {"available": False}
    ma, mb = RUN_A / "metrics.json", RUN_B / "metrics.json"
    if not (ma.exists() and mb.exists()):
        res["note"] = "metrics.json missing — run calibration_verdict --write-metrics"
        return res
    a, b = json.loads(ma.read_text()), json.loads(mb.read_text())
    ca = {k: v.get("status") for k, v in a["criteria"].items()}
    cb = {k: v.get("status") for k, v in b["criteria"].items()}
    degraded = sorted(k for k, s in ca.items() if s == "PASS" and cb.get(k) == "FAIL")
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
        flips = sorted(k for k, s in ra.items() if s == "PASS" and rb.get(k) == "FAIL")
        res["row_grain_pass_to_fail_KILL"] = flips
        res["row_grain_rows_compared"] = len(ra)
    return res


def d2_attribution() -> dict:
    """The cap adds no floor: a NEW D-2 mechanism id in B is a kill; forced-TWh
    deltas on existing mechanisms (the bridge re-detecting from capped P0) are
    surfaced for escalation, not auto-killed."""
    res: dict = {"available": False}
    la = RUN_A / "legitimacy_diagnostics.json"
    lb = RUN_B / "legitimacy_diagnostics.json"
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
            "forced_twh_deltas_gt_0p05_ESCALATE": deltas,
            "d2_passed_A": (a.get("diagnostics") or {}).get("D2", {}).get("passed"),
            "d2_passed_B": (b.get("diagnostics") or {}).get("D2", {}).get("passed"),
        }
    )
    return res


def main() -> None:
    """Score the pre-registered ercot-159 gate set and write the record."""
    actual = pd.read_parquet(_e89.ACTUAL_LMP)
    res = {
        "_doc": "PRECOMMIT-ercot159-energy-online-capability-cap-2026-08-04.md §6 "
        "gates; Run A ercot159_control_A (base) vs Run B ercot159_cap_B",
        "e89_gates": gates_e89(actual),
        "bit_identity_2024_2025": bit_identity(),
        "c3c_anatomy": anatomy_c3c(actual),
        "slack_dump": slack_dump_guard(),
        "scorecard": scorecard_holds(),
        "d2": d2_attribution(),
    }
    kills: list[str] = []
    for y, blk in res["e89_gates"].items():
        for g, s in blk["gates"].items():
            if s != "HELD":
                kills.append(f"{y}:{g}={s}")
    for y, blk in res["bit_identity_2024_2025"].items():
        if not blk["bit_identical"]:
            kills.append(
                f"{y}:bit_identity_BROKEN(price {blk['price_max_abs_delta']:.6g}, "
                f"disp {blk['dispatch_max_abs_delta_mw']:.6g})"
            )
    for y, blk in res["c3c_anatomy"].items():
        if blk["new_tail_outside_actual_KILL"]:
            kills.append(
                f"{y}:new_tail_outside_actual={blk['new_tail_outside_actual_KILL']}"
            )
    for y, blk in res["slack_dump"].items():
        if blk["guard"] != "HELD":
            kills.append(f"{y}:slack_dump={blk['guard']}")
    if res["scorecard"].get("pass_to_fail_KILL"):
        kills.append(f"scorecard:{res['scorecard']['pass_to_fail_KILL']}")
    if res["scorecard"].get("row_grain_pass_to_fail_KILL"):
        kills.append(f"rows:{res['scorecard']['row_grain_pass_to_fail_KILL']}")
    if res["d2"].get("new_forcing_rows_in_B_KILL"):
        kills.append(f"d2:{res['d2']['new_forcing_rows_in_B_KILL']}")
    res["kills_fired"] = kills
    res["all_gates_held"] = not kills
    res["escalations"] = res["d2"].get("forced_twh_deltas_gt_0p05_ESCALATE") or {}

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
