"""C-1 joint wind charter: the dual-based signal + D11-R volume rule, A/B'd together (ERCOT).

Executes owner ruling **R-B** (2026-08-31): compare the JOINT arm
(``entry_lookahead_reprice=False`` + ``entry_margin_exhaustion=True``)
against a same-tree control at the registered T1-H posture, with the
kill-gates fixed ex ante by ``docs/PRECOMMIT-c1-joint-wind-2026-08-31.md``:

* **K1 (REJECTED)** — some addition-metric band moves AWAY from actuals by
  more (in ``|err_frac|``) than the SUM of the improvements on the others;
* **K2 (INERT)** — the arm is indistinguishable from the control on every
  addition metric AND every per-step decision row.

and the **complementarity read** of charter §3.1 — REPORTED, never gated —
which places the joint arm's share of the wind entry miss against the two
committed single arms (``t1h-disarm``, the signal leg; ``t1h-d11r-exhaustion``,
the volume leg) and against their naive sum.

The probe hard-fails unless the two bundles differ in EXACTLY the two
chartered ``run_config`` fields, so a contaminated posture aborts the
comparison instead of being explained afterwards (charter §6 stop rule 2).

Usage::

    python3 scripts/probes/joint_wind_entry_compare.py \
        --arm results/hindcast/ercot-2021-2025-realized-t1h-c1joint-arm \
        --control results/hindcast/ercot-2021-2025-realized-t1h-c1joint-control \
        --out results/calibration/joint_wind_entry_ab_ercot.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

ISO = "ERCOT"

# The registered T1-H bundle the control must reproduce (the v13 C-1
# precedent: measure and record any source-tree drift rather than assume none).
REGISTERED = REPO / "results/hindcast/ercot-2021-2025-realized-t1h-refresh"
REGISTERED_KEY = "28cef3500ec1fd9e"

# The two committed SINGLE arms the complementarity read is taken against
# (charter §3.1). Both are committed artifacts of earlier lanes, read here
# from their own score.json — never re-solved.
SINGLE_ARMS = {
    "signal_alone": REPO / "results/hindcast/ercot-2021-2025-realized-t1h-disarm",
    "volume_alone": (
        REPO / "results/hindcast/ercot-2021-2025-realized-t1h-d11r-exhaustion"
    ),
}

# Exactly the two chartered fields, in their chartered directions.
EXPECTED_DELTA = {
    "entry_lookahead_reprice": {"control": True, "arm": False},
    "entry_margin_exhaustion": {"control": False, "arm": True},
}

ADDITION_TECHS = ("wind", "solar", "gas_cc", "gas_ct", "storage")

# Additivity tolerance for the §3.1 classification, in percentage points of
# the miss closed. A resolution constant for the READ ONLY — it gates
# nothing and enters no model path.
ADDITIVITY_TOL_PP = 0.25


def key_dir(bundle: Path) -> Path:
    """The single cache-key directory under ``<bundle>/ERCOT``."""
    keys = [p for p in sorted((bundle / ISO).iterdir()) if p.is_dir()]
    if len(keys) != 1:
        raise SystemExit(f"expected exactly one cache key under {bundle / ISO}")
    return keys[0]


def read_ledgers(bundle: Path) -> dict[int, dict]:
    """Load ``evolution_<year>.json`` for one bundle, keyed by year."""
    out: dict[int, dict] = {}
    for p in sorted(key_dir(bundle).glob("evolution_*.json")):
        out[int(p.stem.split("_")[1])] = json.loads(p.read_text())
    if not out:
        raise SystemExit(
            f"no evolution ledgers under {bundle} — this probe must run in "
            "the session that solved the bundle (internals are gitignored)"
        )
    return out


def step_rows(ledgers: dict[int, dict]) -> dict[str, dict]:
    """Per-ledger-year entry decisions, storage build by tech, RM, retirements."""
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
            "n_retirements": len(led.get("retirements") or []),
        }
    return rows


def storage_mix(rows: dict[str, dict]) -> dict:
    """Whole-window storage build by tech + capacity-weighted duration.

    Duration weights come from the live ``STORAGE_TECHS`` registry — the same
    committed constants the screen built from.
    """
    from market_sim.config.capacity_market import STORAGE_TECHS

    by_tech: dict[str, float] = {}
    for row in rows.values():
        for tech, mw in row["storage_decided_mw_by_tech"].items():
            by_tech[tech] = by_tech.get(tech, 0.0) + float(mw)
    mw = sum(by_tech.values())
    mwh = sum(
        m * float(STORAGE_TECHS[t]["duration_hr"])
        for t, m in by_tech.items()
        if t in STORAGE_TECHS
    )
    return {
        "by_tech_mw": {k: round(v, 1) for k, v in sorted(by_tech.items())},
        "total_mw": round(mw, 1),
        "cap_weighted_duration_hr": None if mw <= 0 else round(mwh / mw, 2),
        "li_ion_share": None
        if mw <= 0
        else round(sum(v for k, v in by_tech.items() if "li_ion" in k) / mw, 4),
    }


def rm_path(rows: dict[str, dict]) -> dict:
    """RM path over the ledger years, swings, terminal value (B-2's object)."""
    years = sorted(rows)
    path = {y: rows[y]["reserve_margin_pct"] for y in years}
    vals = [v for v in path.values() if v is not None]
    swings = [round(b - a, 2) for a, b in zip(vals, vals[1:])]
    return {
        "path_pct": path,
        "swings_pp": swings,
        "swing_signs": ["+" if s > 0 else "-" if s < 0 else "0" for s in swings],
        "terminal_rm_pct": vals[-1] if vals else None,
    }


def config_delta(arm: Path, control: Path) -> dict:
    """Every scenario_config field that differs between the two bundles."""
    a = json.loads((arm / "run_config.json").read_text())["scenario_config"]
    c = json.loads((control / "run_config.json").read_text())["scenario_config"]
    keys = sorted(set(a) | set(c))
    return {
        k: {"control": c.get(k), "arm": a.get(k)} for k in keys if a.get(k) != c.get(k)
    }


def score_block(bundle: Path) -> dict | None:
    """The bundle's score.json, if it has been scored."""
    p = key_dir(bundle) / "score.json"
    return json.loads(p.read_text()) if p.exists() else None


def control_vs_committed(control: Path) -> dict:
    """Control-vs-registered drift record (the v13 C-1 precedent).

    A drifted control is still a valid A/B base (one tree for both arms) but
    the drift must be visible in the record rather than assumed away.
    """
    reg_score = json.loads(
        (REGISTERED / ISO / REGISTERED_KEY / "score.json").read_text()
    )
    ctrl_key = json.loads((control / "meta.json").read_text())["cache_key"]
    ctrl_score = score_block(control)
    drift_rows: dict[str, dict] = {}
    identical = True
    for tech in ADDITION_TECHS:
        reg = reg_score["additions"]["by_tech"][tech]
        cur = (ctrl_score or {}).get("additions", {}).get("by_tech", {}).get(tech, {})
        row_same = (
            cur.get("model_gw") == reg["model_gw"]
            and cur.get("err_frac") == reg["err_frac"]
        )
        identical = identical and row_same
        drift_rows[tech] = {
            "registered": {
                k: reg[k] for k in ("actual_gw", "model_gw", "err_frac", "band")
            },
            "control": {
                k: cur.get(k) for k in ("actual_gw", "model_gw", "err_frac", "band")
            },
            "identical": row_same,
        }
    return {
        "registered_bundle": str(REGISTERED),
        "registered_cache_key": REGISTERED_KEY,
        "control_cache_key": ctrl_key,
        "cache_key_reproduced": ctrl_key == REGISTERED_KEY,
        "additions_rows": drift_rows,
        "additions_identical": identical,
    }


def band_table(score_c: dict, score_a: dict) -> dict:
    """Per-tech addition bands, both directions at full magnitude, + K1."""
    rows: dict[str, dict] = {}
    improvements = 0.0
    worsenings: dict[str, float] = {}
    any_diff = False
    for tech in ADDITION_TECHS:
        c = score_c["additions"]["by_tech"][tech]
        a = score_a["additions"]["by_tech"][tech]
        d = round(abs(a["err_frac"]) - abs(c["err_frac"]), 4)
        if abs(a["model_gw"] - c["model_gw"]) > 1e-9:
            any_diff = True
        rows[tech] = {
            "actual_gw": c["actual_gw"],
            "control_model_gw": c["model_gw"],
            "arm_model_gw": a["model_gw"],
            "control_err_frac": c["err_frac"],
            "arm_err_frac": a["err_frac"],
            "control_band": c["band"],
            "arm_band": a["band"],
            "abs_err_delta": d,  # >0 moved AWAY from actuals, <0 moved toward
        }
        if d < 0:
            improvements += -d
        elif d > 0:
            worsenings[tech] = d
    # K1 as chartered: a band that moves away by MORE than the sum of the
    # improvements on the others. "The others" excludes the worsening band
    # itself, which never contributes to `improvements` by construction.
    k1_detail = {
        t: {
            "worsening": w,
            "sum_improvements_elsewhere": round(improvements, 4),
            "fails_k1": w > improvements + 1e-12,
        }
        for t, w in worsenings.items()
    }
    return {
        "rows": rows,
        "sum_abs_err_improvement": round(improvements, 4),
        "worsenings": k1_detail,
        "k1_rejected": any(v["fails_k1"] for v in k1_detail.values()),
        "any_model_gw_delta": any_diff,
    }


def _wind_row(score: dict) -> dict:
    """The wind addition row of one score.json."""
    return score["additions"]["by_tech"]["wind"]


def complementarity_read(score_c: dict, score_a: dict) -> dict:
    """Charter §3.1: the joint arm against the two committed single arms.

    REPORTED, never gated. Each arm's share of the wind entry miss is
    ``(model_arm - model_control) / (actual - model_control)`` on the
    2023-2025 decision basis — the same construction the Leg-B measurement
    used (Phase-0 §4.1).
    """
    wc = _wind_row(score_c)
    base = float(wc["model_gw"])
    actual = float(wc["actual_gw"])
    miss = actual - base

    def share(model_gw: float) -> float:
        return round(100.0 * (float(model_gw) - base) / miss, 2)

    arms: dict[str, dict] = {
        "control": {
            "source": "this session",
            "wind_model_gw": base,
            "share_of_miss_closed_pct": 0.0,
        }
    }
    singles: dict[str, float] = {}
    for name, path in SINGLE_ARMS.items():
        s = score_block(path)
        if s is None:
            arms[name] = {"source": "committed", "wind_model_gw": None}
            continue
        gw = float(_wind_row(s)["model_gw"])
        singles[name] = gw
        arms[name] = {
            "source": "committed",
            "bundle": str(path),
            "wind_model_gw": gw,
            "share_of_miss_closed_pct": share(gw),
            "all_addition_model_gw": {
                t: s["additions"]["by_tech"][t]["model_gw"] for t in ADDITION_TECHS
            },
        }
    joint_gw = float(_wind_row(score_a)["model_gw"])
    arms["joint"] = {
        "source": "this session",
        "wind_model_gw": joint_gw,
        "share_of_miss_closed_pct": share(joint_gw),
    }

    naive_sum_gw = base + sum(gw - base for gw in singles.values())
    naive_pct = share(naive_sum_gw) if singles else None
    best_single_pct = max(share(gw) for gw in singles.values()) if singles else None
    joint_pct = share(joint_gw)

    # WIRING-INERT is checked on the scored rows of the committed signal arm:
    # a joint arm that reproduces it on every addition metric means the walk
    # never became live (charter §6 stop rule 3).
    sig_bundle = SINGLE_ARMS["signal_alone"]
    sig_score = score_block(sig_bundle)
    wiring_inert = bool(
        sig_score
        and all(
            abs(
                float(score_a["additions"]["by_tech"][t]["model_gw"])
                - float(sig_score["additions"]["by_tech"][t]["model_gw"])
            )
            <= 1e-9
            for t in ADDITION_TECHS
        )
    )

    if wiring_inert:
        verdict = "WIRING_INERT"
    elif naive_pct is None or best_single_pct is None:
        verdict = "UNCLASSIFIED (a committed single arm is unscored)"
    elif joint_pct > naive_pct + ADDITIVITY_TOL_PP:
        verdict = "SUPER_ADDITIVE"
    elif abs(joint_pct - naive_pct) <= ADDITIVITY_TOL_PP:
        verdict = "ADDITIVE"
    elif joint_pct > best_single_pct + ADDITIVITY_TOL_PP:
        verdict = "SUB_ADDITIVE_COMPLEMENTARY"
    else:
        verdict = "NON_COMPLEMENTARY"

    return {
        "basis": "2023-2025 additions decision basis, wind, from each "
        "bundle's own score.json",
        "control_wind_gw": base,
        "actual_wind_gw": actual,
        "miss_gw": round(miss, 3),
        "arms": arms,
        "naive_sum_wind_gw": round(naive_sum_gw, 3),
        "naive_sum_share_pct": naive_pct,
        "best_single_share_pct": best_single_pct,
        "joint_share_pct": joint_pct,
        "additivity_tol_pp": ADDITIVITY_TOL_PP,
        "wiring_inert_vs_committed_signal_arm": wiring_inert,
        "verdict": verdict,
    }


def main() -> None:
    """CLI entry: verify posture, compare arms, emit the A/B record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True, type=Path)
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    arm = args.arm if args.arm.is_absolute() else REPO / args.arm
    control = args.control if args.control.is_absolute() else REPO / args.control

    delta = config_delta(arm, control)
    if delta != EXPECTED_DELTA:
        raise SystemExit(
            "posture verification FAILED — the arms must differ in exactly "
            f"{json.dumps(EXPECTED_DELTA)}; got {json.dumps(delta)}"
        )

    rows_c = step_rows(read_ledgers(control))
    rows_a = step_rows(read_ledgers(arm))
    score_c = score_block(control)
    score_a = score_block(arm)
    if score_c is None or score_a is None:
        raise SystemExit("both bundles must be scored (score_capacity_hindcast) first")

    bands = band_table(score_c, score_a)
    # K2 as chartered: indistinguishable from the control on every addition
    # metric AND every per-step decision row.
    k2_inert = (not bands["any_model_gw_delta"]) and rows_c == rows_a

    out = {
        "probe": "joint_wind_entry_compare",
        "lane": "C-1 joint wind charter (owner ruling R-B, 2026-08-31; "
        "docs/PRECOMMIT-c1-joint-wind-2026-08-31.md)",
        "iso": ISO,
        "bundles": {"control": str(control), "arm": str(arm)},
        "posture": {
            "config_delta": delta,
            "expected_delta": EXPECTED_DELTA,
            "cache_keys": {
                "control": json.loads((control / "meta.json").read_text())["cache_key"],
                "arm": json.loads((arm / "meta.json").read_text())["cache_key"],
            },
        },
        "control_vs_committed": control_vs_committed(control),
        "steps": {"control": rows_c, "arm": rows_a},
        "storage_mix": {"control": storage_mix(rows_c), "arm": storage_mix(rows_a)},
        "rm": {"control": rm_path(rows_c), "arm": rm_path(rows_a)},
        "addition_bands": bands,
        "kill_gates": {"k1_rejected": bands["k1_rejected"], "k2_inert": k2_inert},
        "complementarity_read": complementarity_read(score_c, score_a),
        "score": {"control": score_c, "arm": score_a},
    }
    out_path = args.out if args.out.is_absolute() else REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {out_path}")
    cr = out["complementarity_read"]
    print(
        "wind GW: control",
        cr["control_wind_gw"],
        "-> joint",
        cr["arms"]["joint"]["wind_model_gw"],
        f"({cr['joint_share_pct']}% of the miss; singles "
        f"{cr['arms'].get('signal_alone', {}).get('share_of_miss_closed_pct')}% / "
        f"{cr['arms'].get('volume_alone', {}).get('share_of_miss_closed_pct')}%, "
        f"naive sum {cr['naive_sum_share_pct']}%)",
    )
    print("complementarity:", cr["verdict"])
    print(
        "terminal RM: control",
        out["rm"]["control"]["terminal_rm_pct"],
        "arm",
        out["rm"]["arm"]["terminal_rm_pct"],
        "| arm swing signs",
        out["rm"]["arm"]["swing_signs"],
    )
    print("K1 rejected:", bands["k1_rejected"], "| K2 inert:", k2_inert)


if __name__ == "__main__":
    main()
