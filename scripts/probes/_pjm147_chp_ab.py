#!/usr/bin/env python3
"""pjm-147 A/B scorer — measured power-only CHP heat rates at PJM.

Scores **only** the gates pre-registered in
``results/calibration/PREREG-pjm147-measured-chp-heat-rates-2026-08-03.md``
(K0-K5 in §4) and reports **only** the quantities §3 declares reportable.
Modeled on ``_pjm146_rggi_ab.py``: every scored criterion — C3a/C3c included —
is taken from each bundle's own ``metrics.json``, never re-derived. The only
quantities this file computes itself are construction/delta statistics (the
heat-rate seam audit, class-energy deltas, C1 volume moves against the
committed benchmark), none of which is a scored criterion.

The C1 block is the pjm-146 correction: that session licensed a C3a move ex
ante but registered NO C1 magnitude gate, so its C1 CC_REGULAR regression could
not be adjudicated on its pre-registration alone. PREREG §3 E1d declares the
band; this scores against it.

    PYTHONPATH=.:src uv run python scripts/probes/_pjm147_chp_ab.py
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/pjm143_hy_level_B"
ARM_A = REPO / "results/calibration/pjm147_control_A"
ARM_B = REPO / "results/calibration/pjm147_chp_B"
OUT_PATH = REPO / "results/calibration/_pjm147_chp_ab.json"
FIDELITY = REPO / "results/calibration/_pjm147_flag_fidelity.json"

YEARS = (2023, 2024, 2025)
FLAG = "measured_chp_heat_rates"
TARGET = ("CC_CHP", "CT_CHP")
EXTERNAL_PREFIX = "PJM_external"

#: PREREG §4 thresholds.
K1_MIN_CLASS_MW = 1.0  # max |delta class-hour MW| on CC_CHP+CT_CHP
K3_SCOPE_CLASSES = frozenset(TARGET)
E1D_C1_BAND_TWH = 1.5  # no C1-gated class moves more than this in any year
E1B_LO, E1B_HI = -2.0, -0.3  # CC_CHP volume delta band, TWh


# ── committed-artifact readers (the _pjm144/146 conventions) ────────────────


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _system(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    if "pass" in frame.columns:
        frame = frame[frame["pass"] == "P1"]
    return frame[~frame["zone"].astype(str).str.startswith(EXTERNAL_PREFIX)]


def _lw_price(bundle: Path, year: int) -> float:
    pj = _system(bundle, year)
    return float((pj["price"] * pj["demand"]).sum() / pj["demand"].sum())


def _pairwise(a: Path, b: Path, year: int) -> dict:
    left = _class_hourly(a, year).set_index(["klass", "hour"])["mw"].sort_index()
    right = _class_hourly(b, year).set_index(["klass", "hour"])["mw"].sort_index()
    lj, rj = left.align(right, join="outer", fill_value=0.0)
    diff = (lj - rj).abs()
    return {
        "max_abs_diff_mw": round(float(diff.max()), 6),
        "max_by_class_mw": {
            str(k): round(float(v), 4)
            for k, v in diff.groupby(level="klass").max().items()
            if float(v) > 1e-9
        },
    }


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    frame = _class_hourly(bundle, year)
    return {
        str(k): float(v) / 1e6
        for k, v in frame.groupby("klass")["mw"].sum().items()
    }


def _class_energy_delta(year: int) -> dict[str, float]:
    a, b = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
    keys = sorted(set(a) | set(b))
    return {
        k: round(b.get(k, 0.0) - a.get(k, 0.0), 4)
        for k in keys
        if abs(b.get(k, 0.0) - a.get(k, 0.0)) > 5e-5
    }


def _scenario_block(bundle: Path) -> dict:
    path = bundle / "run_config.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    return raw.get("scenario_config", raw) or {}


def _metrics(bundle: Path) -> dict | None:
    path = bundle / "metrics.json"
    return json.loads(path.read_text()) if path.exists() else None


def _criteria(bundle: Path) -> dict[str, str]:
    m = _metrics(bundle)
    if not m:
        return {}
    return {
        k: (v.get("status") if isinstance(v, dict) else v)
        for k, v in (m.get("criteria") or {}).items()
    }


def _slack_dump(bundle: Path, year: int) -> tuple[float, float]:
    frame = _system(bundle, year)
    return round(float(frame["slack"].sum()), 3), round(float(frame["dump"].sum()), 3)


# ── K3: the heat-rate seam, rebuilt through the real path ──────────────────


def k3_scope_audit() -> dict:
    """Exactly the artifact's applied pairs carry a changed heat rate — nothing else."""
    from scripts.replay_keeper import build_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    solve_kwargs = build_kwargs(meta)
    params = set(inspect.signature(run_year).parameters)
    rename = {"commitment": "commitment_enabled", "screen_coal": "commitment_screen_coal"}
    skip = {"year", "iso", "hours", "gas_price", "ttc_overrides", "fleet_only"}
    base = {
        rename.get(k, k): v
        for k, v in solve_kwargs.items()
        if rename.get(k, k) in params and rename.get(k, k) not in skip
    }
    gas_prices = meta.get("gas_prices", {})

    art = pd.read_csv(
        REPO / "data/raw/_processed-legacy/chp_power_only_heat_rates_PJM.csv"
    )
    applied = {
        (int(r.plant_code), str(r.plant_group))
        for r in art[art["flag"] == "ok"].itertuples()
    }

    out: dict = {"passed": True, "artifact_applied_pairs": len(applied), "years": {}}
    for year in YEARS:
        gas = float(gas_prices.get(str(year), gas_prices.get(year, 0.0)))
        fleets = {}
        for armed in (False, True):
            kw = dict(base)
            if armed:
                prb = dict(kw.get("prb_overrides") or {})
                prb[FLAG] = True
                kw["prb_overrides"] = prb
            fleets[armed] = list(
                run_year(year, "PJM", 8760, gas, {}, fleet_only=True, **kw)["fleet"]
            )
        moved: set[tuple[int, str]] = set()
        moved_mw = 0.0
        for a, b in zip(fleets[False], fleets[True]):
            if abs(float(a.heat_rate) - float(b.heat_rate)) > 1e-9:
                moved.add((int(a.plant_code or 0), str(a.plant_group)))
                moved_mw += float(a.pmax_mw)
        leak = sorted({k for _, k in moved} - K3_SCOPE_CLASSES)
        unexpected = sorted(moved - applied)
        ok = not leak and not unexpected
        out["passed"] &= ok
        out["years"][str(year)] = {
            "n_moved_pairs": len(moved),
            "moved_mw": round(moved_mw, 3),
            "classes_moved": sorted({k for _, k in moved}),
            "out_of_scope_classes": leak,
            "pairs_not_in_artifact": unexpected,
            "ok": ok,
        }
        del fleets
    return out


# ── C1: the pre-registered magnitude gate (E1d) ────────────────────────────


def c1_block() -> dict:
    """Per-class C1 volumes for both arms, scored against PREREG §3 E1b/E1c/E1d."""
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    import calibration_verdict as cv

    out: dict = {
        "band_twh": E1D_C1_BAND_TWH,
        "e1b_band_twh": [E1B_LO, E1B_HI],
        "years": {},
        "e1b_pass": True,
        "e1c_pass": True,
        "e1d_pass": True,
        "k5_overshoot_pass": True,
    }
    for arm_key, bundle in (("control", ARM_A), ("arm", ARM_B)):
        rid = (_metrics(bundle) or {}).get("run_id")
        if not rid:
            out.setdefault("errors", []).append(f"{arm_key}: no run_id in metrics.json")
            return out
        art = cv.load_artifacts(rid)
        for year in YEARS:
            recs = cv.score_fuelmix(
                year, art["payload"]["years"][str(year)], art["bench"][year], "PJM"
            )
            slot = out["years"].setdefault(str(year), {})
            for r in recs:
                slot.setdefault(r["key"], {})[arm_key] = {
                    "model": r["model"],
                    "actual": r["actual"],
                    "status": r["status"],
                }

    for year in YEARS:
        for klass, arms in out["years"][str(year)].items():
            if "control" not in arms or "arm" not in arms:
                continue
            c, a = arms["control"], arms["arm"]
            d = a["model"] - c["model"]
            arms["delta_twh"] = round(d, 4)
            arms["abs_err_control"] = round(abs(c["model"] - c["actual"]), 4)
            arms["abs_err_arm"] = round(abs(a["model"] - a["actual"]), 4)
            arms["abs_err_improves"] = arms["abs_err_arm"] < arms["abs_err_control"]
            arms["status_flip"] = c["status"] != a["status"]
            if abs(d) > E1D_C1_BAND_TWH:
                out["e1d_pass"] = False
            if klass == "CC_CHP":
                if not (E1B_LO <= d <= E1B_HI):
                    out["e1b_pass"] = False
                if not arms["abs_err_improves"]:
                    out["e1c_pass"] = False
                    out["k5_overshoot_pass"] = False
    return out


# ── assembly ────────────────────────────────────────────────────────────────


def main() -> None:
    a_cfg, b_cfg = _scenario_block(ARM_A), _scenario_block(ARM_B)
    flag_fidelity = {
        "passed": a_cfg.get(FLAG) in (False, None) and b_cfg.get(FLAG) is True,
        "A": a_cfg.get(FLAG),
        "B": b_cfg.get(FLAG),
    }

    k0 = json.loads(FIDELITY.read_text()) if FIDELITY.exists() else {}
    k0_summary = {
        "passed": bool(k0.get("k0_live") and k0.get("k0_scope_ok")),
        "source": str(FIDELITY.relative_to(REPO)),
        "per_year": {
            y: {
                k: v
                for k, v in rec.items()
                if k != "moved_rows"
            }
            for y, rec in (k0.get("years") or {}).items()
        },
    }

    keeper_c, a_c, b_c = _criteria(KEEPER), _criteria(ARM_A), _criteria(ARM_B)
    km, am, bm = _metrics(KEEPER), _metrics(ARM_A), _metrics(ARM_B)
    k2 = {
        "passed": bool(
            keeper_c
            and a_c
            and keeper_c == a_c
            and (km or {}).get("determination") == (am or {}).get("determination")
        ),
        "basis": "scorecard (gate); strict byte basis reported below",
        "byte": {str(y): _pairwise(KEEPER, ARM_A, y) for y in YEARS},
        "keeper_criteria": keeper_c,
        "control_criteria": a_c,
    }

    class_delta = {str(y): _class_energy_delta(y) for y in YEARS}
    k1_live, k4_sign_ok = False, True
    for y in YEARS:
        pw = _pairwise(ARM_A, ARM_B, y)["max_by_class_mw"]
        if max((pw.get(k, 0.0) for k in TARGET), default=0.0) > K1_MIN_CLASS_MW:
            k1_live = True
        if class_delta[str(y)].get("CC_CHP", 0.0) > 0:
            k4_sign_ok = False

    report = {
        "prereg": "results/calibration/PREREG-pjm147-measured-chp-heat-rates-2026-08-03.md",
        "arms": {"control": str(ARM_A), "arm": str(ARM_B), "keeper": str(KEEPER)},
        "flag_fidelity": flag_fidelity,
        "K0_wiring_liveness_presolve": k0_summary,
        "K1_mechanism_live": {
            "passed": bool(k1_live),
            "rule": f"max |delta class-hour MW| on {TARGET} > {K1_MIN_CLASS_MW} in >=1 year",
            "per_year": {
                str(y): _pairwise(ARM_A, ARM_B, y)["max_by_class_mw"] for y in YEARS
            },
        },
        "K2_control_integrity": k2,
        "K3_scope_integrity": k3_scope_audit(),
        "K4_sign": {
            "passed": bool(k4_sign_ok),
            "rule": "CC_CHP is one-sided dearer at the seam; a RISE is a defect signal",
        },
        "K5_overshoot_and_C1": c1_block(),
        "price_deltas": {
            str(y): {
                "lw_control": round(_lw_price(ARM_A, y), 4),
                "lw_arm": round(_lw_price(ARM_B, y), 4),
                "lw_delta": round(_lw_price(ARM_B, y) - _lw_price(ARM_A, y), 4),
            }
            for y in YEARS
        },
        "class_energy_delta_twh": class_delta,
        "criteria": {
            "keeper": keeper_c,
            "control": a_c,
            "arm": b_c,
            "determinations": {
                "keeper": (km or {}).get("determination"),
                "control": (am or {}).get("determination"),
                "arm": (bm or {}).get("determination"),
            },
        },
        "slack_dump": {
            str(y): {"control": _slack_dump(ARM_A, y), "arm": _slack_dump(ARM_B, y)}
            for y in YEARS
        },
    }
    OUT_PATH.write_text(json.dumps(report, indent=1, default=str))
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "flag_fidelity",
                    "K0_wiring_liveness_presolve",
                    "K1_mechanism_live",
                    "K2_control_integrity",
                    "K3_scope_integrity",
                    "K4_sign",
                    "K5_overshoot_and_C1",
                    "price_deltas",
                    "class_energy_delta_twh",
                    "criteria",
                )
                if k in report
            },
            indent=1,
            default=str,
        )[:6000]
    )
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src"))
    main()
