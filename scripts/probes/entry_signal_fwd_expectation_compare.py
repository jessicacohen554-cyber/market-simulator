#!/usr/bin/env python
"""Score the forward-expectation entry-signal A/B against its precommit.

The adjudicating measurement named by
``docs/FINDING-entry-signal-disarm-2026-08.md`` §6 and pre-registered in
``docs/PRECOMMIT-entry-signal-forward-expectation-2026-08-25.md``: an ERCOT
2021-2025 T1-H capacity hindcast at the registered t1h posture with ONE field
armed — ``entry_forward_expectation_signal`` — so every capacity screen reads
the run's own prior-year hourly zonal LP duals re-leveled hour-by-hour against
the entering year's stack, instead of the zone-flat MC-step object.

Four bundles enter; one artifact leaves:

* the TREATMENT arm (produced in-session; carries evolution ledgers),
* a SAME-TREE CONTROL re-solved at the registered posture from this HEAD
  (drift guard: HEAD moved since the committed brackets were solved —
  notably ercot-234's EASTEX static GTC 1,300 -> 2,300 MW repair),
* the two COMMITTED brackets — ``…-t1h-control`` / ``…-t1h-disarm`` — whose
  score.json anchors the comparison and whose per-step ledger rows are read
  from the committed probe artifact
  ``results/calibration/entry_signal_disarm_ledger_ercot.json`` (bundle
  internals are gitignored; the artifact is the record).

The P1/P2/P3 thresholds scored here were committed BEFORE the treatment solve
existed (the precommit §3); this probe only executes them. It hard-fails
rather than reports if the posture checks do not reproduce.

Usage::

    uv run python scripts/probes/entry_signal_fwd_expectation_compare.py \\
        --treatment results/hindcast/ercot-2021-2025-realized-t1h-fwdexp \\
        --control results/hindcast/ercot-2021-2025-realized-t1h-fwdexp-control \\
        --out results/calibration/entry_signal_fwd_expectation_ercot.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ISO = "ERCOT"

COMMITTED_CONTROL = REPO / "results/hindcast/ercot-2021-2025-realized-t1h-control"
COMMITTED_DISARM = REPO / "results/hindcast/ercot-2021-2025-realized-t1h-disarm"
COMMITTED_LEDGER_ARTIFACT = (
    REPO / "results/calibration/entry_signal_disarm_ledger_ercot.json"
)

# Precommit §3 thresholds (fixed 2026-08-25, before the treatment solve).
P3_CONFIRMED_MAX_RM_PCT = 30.2  # committed control 25.19 + 5 pp
P3_SURVIVES_MIN_RM_PCT = 35.2  # committed disarm 40.24 - 5 pp


def bundle_key_dir(bundle: Path) -> Path:
    """Return the single per-ISO cache-key directory inside a bundle."""
    keys = [p for p in sorted((bundle / ISO).iterdir()) if p.is_dir()]
    if len(keys) != 1:
        raise SystemExit(f"expected exactly one cache key under {bundle / ISO}")
    return keys[0]


def read_ledgers(bundle: Path) -> dict[int, dict]:
    """Load ``evolution_<year>.json`` for one bundle, keyed by year."""
    out: dict[int, dict] = {}
    for p in sorted(bundle_key_dir(bundle).glob("evolution_*.json")):
        out[int(p.stem.split("_")[1])] = json.loads(p.read_text())
    if not out:
        raise SystemExit(
            f"no evolution ledgers under {bundle} — the bundle's internals are "
            "gitignored, so this probe must run in the session that solved it"
        )
    return out


def step_rows(ledgers: dict[int, dict]) -> dict[str, dict]:
    """Per-ledger-year entry decisions, storage build by tech, and RM."""
    rows: dict[str, dict] = {}
    for year, led in sorted(ledgers.items()):
        storage: dict[str, float] = {}
        for add in led.get("storage_additions") or []:
            storage[add["tech"]] = storage.get(add["tech"], 0.0) + float(add["mw"])
        rm = led.get("reserve_margin")
        rows[str(year)] = {
            "bridge": bool(led.get("bridge")),
            "reserve_margin_pct": None if rm is None else round(100.0 * rm, 2),
            "entry_decided_mw_by_tech": {
                k: round(float(v), 1)
                for k, v in (led.get("entry_decided_mw_by_tech") or {}).items()
            },
            "storage_decided_mw_by_tech": {
                k: round(v, 1) for k, v in sorted(storage.items())
            },
            "peak_demand_mw": led.get("peak_demand_mw"),
            "n_retirements": len(led.get("retirements") or []),
        }
    return rows


def score_block(bundle: Path) -> dict:
    """The bundle's committed score.json."""
    return json.loads((bundle_key_dir(bundle) / "score.json").read_text())


def additions_table(*, actual_from: dict, arms: dict[str, dict]) -> dict:
    """Per-tech actual/model GW and |error| GW for each arm, side by side."""
    techs = list(actual_from["additions"]["by_tech"])
    out: dict[str, dict] = {}
    for tech in techs:
        row: dict = {
            "actual_gw": actual_from["additions"]["by_tech"][tech]["actual_gw"]
        }
        for label, sc in arms.items():
            cell = sc["additions"]["by_tech"].get(tech, {})
            model = cell.get("model_gw")
            row[label] = {
                "model_gw": model,
                "err_frac": cell.get("err_frac"),
                "band": cell.get("band"),
                "abs_err_gw": (
                    None if model is None else round(abs(model - row["actual_gw"]), 3)
                ),
            }
        out[tech] = row
    return out


def score_predictions(rows_t: dict[str, dict]) -> dict:
    """Execute the precommit §3 P1/P2/P3 thresholds on the treatment ledger."""
    steps = [r for _, r in sorted(rows_t.items())]
    storage_steps = [r for r in steps if r["storage_decided_mw_by_tech"]]
    n_storage_steps = len(storage_steps)
    storage_2023_only = n_storage_steps >= 1 and all(
        not r["storage_decided_mw_by_tech"] for y, r in rows_t.items() if y != "2023"
    )
    long_duration = {"iron_air", "compressed_air", "flow_battery"}

    def _leading_tech(r: dict) -> str | None:
        d = r["storage_decided_mw_by_tech"]
        return max(d, key=d.get) if d else None

    leaders = [_leading_tech(r) for r in storage_steps]
    p1 = {
        "prediction": (
            "storage decided in >=3 of 4 steps, long-duration tech leading, "
            "no one-shot 2023-only recurrence"
        ),
        "n_steps_with_storage": n_storage_steps,
        "leading_tech_by_step": leaders,
        "one_shot_2023_only": storage_2023_only,
        "verdict": (
            "CONFIRMED"
            if (
                n_storage_steps >= 3
                and not storage_2023_only
                and all(t in long_duration for t in leaders if t)
            )
            else "NOT CONFIRMED"
        ),
    }

    wind_by_step = {
        y: r["entry_decided_mw_by_tech"].get("wind", 0.0)
        for y, r in sorted(rows_t.items())
    }
    p2 = {
        "prediction": "decided wind > 0 MW in >=1 step",
        "wind_decided_mw_by_step": wind_by_step,
        "verdict": (
            "CONFIRMED"
            if any(v > 0 for v in wind_by_step.values())
            else "NOT CONFIRMED"
        ),
    }

    terminal_rm = rows_t.get("2025", {}).get("reserve_margin_pct")
    if terminal_rm is None:
        p3_verdict = "UNSCORABLE (no 2025 reserve margin in the ledger)"
    elif terminal_rm <= P3_CONFIRMED_MAX_RM_PCT:
        p3_verdict = "CONFIRMED (no overshoot)"
    elif terminal_rm >= P3_SURVIVES_MIN_RM_PCT:
        p3_verdict = "OVERSHOOT SURVIVES — D-1's bang-bang volume rule owns it"
    else:
        p3_verdict = "BORDERLINE — escalate to the owner (precommit §3)"
    p3 = {
        "prediction": (
            f"terminal ledger-2025 RM <= {P3_CONFIRMED_MAX_RM_PCT} confirmed; "
            f">= {P3_SURVIVES_MIN_RM_PCT} the overshoot survives; between: "
            "borderline, owner escalation"
        ),
        "terminal_rm_pct": terminal_rm,
        "brackets": {"committed_control": 25.19, "committed_disarm": 40.24},
        "verdict": p3_verdict,
    }
    return {"P1_storage_repair": p1, "P2_wind_entry": p2, "P3_no_overshoot": p3}


def main() -> None:
    """CLI entry point: emit the fwd-expectation A/B comparison artifact."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--treatment", required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    treatment = REPO / args.treatment
    control = REPO / args.control
    sc_t, sc_c = score_block(treatment), score_block(control)
    sc_cc, sc_cd = score_block(COMMITTED_CONTROL), score_block(COMMITTED_DISARM)
    meta_t = json.loads((treatment / "meta.json").read_text())
    meta_c = json.loads((control / "meta.json").read_text())
    meta_cc = json.loads((COMMITTED_CONTROL / "meta.json").read_text())
    cfg_t = json.loads((treatment / "run_config.json").read_text())["scenario_config"]
    cfg_c = json.loads((control / "run_config.json").read_text())["scenario_config"]
    field_diffs = sorted(
        k for k in set(cfg_t) | set(cfg_c) if cfg_t.get(k) != cfg_c.get(k)
    )
    committed_ledger = json.loads(COMMITTED_LEDGER_ARTIFACT.read_text())

    rows_t = step_rows(read_ledgers(treatment))
    rows_c = step_rows(read_ledgers(control))

    # Same-tree control vs the COMMITTED control: drift guard (reported,
    # never chased — precommit §2).
    cc_co2 = (sc_cc.get("co2") or {}).get("model") or {}
    c_co2 = (sc_c.get("co2") or {}).get("model") or {}
    drift = {
        "control_reproduces_committed_key": (
            meta_c["cache_key"] == meta_cc["cache_key"]
        ),
        "co2_delta_t_by_year": {
            y: (
                None
                if (c_co2.get(y) is None or cc_co2.get(y) is None)
                else round(c_co2[y] - cc_co2[y], 3)
            )
            for y in sorted(set(c_co2) | set(cc_co2))
        },
        "fleet_metrics_identical_to_committed": all(
            sc_c.get(k) == sc_cc.get(k)
            for k in ("additions", "retirements", "retirements_is", "bands")
        ),
    }

    result = {
        "probe": "entry_signal_fwd_expectation_compare",
        "precommit": ("docs/PRECOMMIT-entry-signal-forward-expectation-2026-08-25.md"),
        "charter": "docs/FINDING-entry-signal-disarm-2026-08.md §6",
        "iso": ISO,
        "arms": {
            "treatment": {
                "bundle": args.treatment,
                "cache_key": meta_t["cache_key"],
                "entry_forward_expectation_signal": meta_t.get(
                    "entry_forward_expectation_signal"
                ),
                "solved_years": meta_t["solved_years"],
                "bridged_years": meta_t["bridged_years"],
            },
            "control_same_tree": {
                "bundle": args.control,
                "cache_key": meta_c["cache_key"],
                "entry_forward_expectation_signal": meta_c.get(
                    "entry_forward_expectation_signal"
                ),
                "solved_years": meta_c["solved_years"],
                "bridged_years": meta_c["bridged_years"],
            },
            "committed_control": {
                "bundle": str(COMMITTED_CONTROL.relative_to(REPO)),
                "cache_key": meta_cc["cache_key"],
            },
            "committed_disarm": {
                "bundle": str(COMMITTED_DISARM.relative_to(REPO)),
            },
        },
        "posture_check": {
            "single_field_delta": field_diffs == ["entry_forward_expectation_signal"],
            "config_field_diffs": field_diffs,
            "treatment_armed": cfg_t.get("entry_forward_expectation_signal") is True,
            "control_reproduces_committed_key": (
                meta_c["cache_key"] == meta_cc["cache_key"]
            ),
            "same_solve_span": (
                meta_t["solved_years"] == meta_c["solved_years"]
                and meta_t["bridged_years"] == meta_c["bridged_years"]
            ),
        },
        "ledger": {
            "treatment": rows_t,
            "control_same_tree": rows_c,
            "committed_brackets_from": str(COMMITTED_LEDGER_ARTIFACT.relative_to(REPO)),
            "committed_control": committed_ledger["ledger"]["control"],
            "committed_disarm": committed_ledger["ledger"]["disarm"],
        },
        "predictions": score_predictions(rows_t),
        "additions": additions_table(
            actual_from=sc_cc,
            arms={
                "committed_control": sc_cc,
                "committed_disarm": sc_cd,
                "control_same_tree": sc_c,
                "treatment": sc_t,
            },
        ),
        "retirements_total_gw": {
            "actual": sc_cc["retirements"]["total_gw"]["actual"],
            "committed_control": sc_cc["retirements"]["total_gw"]["model"],
            "committed_disarm": sc_cd["retirements"]["total_gw"]["model"],
            "control_same_tree": sc_c["retirements"]["total_gw"]["model"],
            "treatment": sc_t["retirements"]["total_gw"]["model"],
        },
        "head_drift_vs_committed_control": drift,
        "dump_production": {
            "treatment_npz": len(list(bundle_key_dir(treatment).glob("*.npz"))),
            "control_npz": len(list(bundle_key_dir(control).glob("*.npz"))),
            "note": (
                "L-5 alive under the replacement (disarm §3.3 relocation "
                "carried): the treatment's dumps additionally record the "
                "composed zonal signal, the forward delta and the S_current "
                "internals"
            ),
        },
    }

    out_path = Path(args.out) if Path(args.out).is_absolute() else REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=1) + "\n")
    print(f"wrote {out_path}")
    pc = result["posture_check"]
    print(f"posture_check: {pc}")
    for name, block in result["predictions"].items():
        print(f"{name}: {block['verdict']}")
    if not all(
        pc[k] for k in ("single_field_delta", "treatment_armed", "same_solve_span")
    ):
        raise SystemExit(
            "posture check FAILED — the arms are not the single-field pair "
            "this probe claims to compare"
        )


if __name__ == "__main__":
    main()
