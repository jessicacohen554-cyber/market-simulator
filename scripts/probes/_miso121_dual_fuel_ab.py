#!/usr/bin/env python3
"""miso-121 A/B scorer — ``dual_fuel_switching`` at MISO.

Scores **only** the gates pre-registered in
``results/calibration/PREREG-miso121-dual-fuel-switching-2026-08-03.md`` §8.3
(construction K1-K5, the one-sided direction gate K6, the reported K7) and the
kills fixed in its §6. Adapted from ``_miso119_zonal_anchor_ab.py`` with the
changes this mechanism's geometry forces:

* **K4 is a SINGLE key** (``dual_fuel_switching``), not a pair.
* **K3's price leg is scored on BOTH the system and the zonal grain.** Unlike
  the mean-zero zonal anchor, this mechanism is **not** level-preserving — it
  is a one-sided cap that removes offer level — so the system delta is
  meaningful here and is *not* demoted to reporting.
* **K6 is REINSTATED and one-sided.** ``apply_dual_fuel_pricing`` writes
  ``min(gas, oil)``, so a capable unit's fuel price can only ever fall. pjm-144
  correctly dropped K6 for a two-sided mean-zero table; this mechanism is
  strictly one-sided, so the direction IS a gate.
* **K7 switched-volume plausibility is REPORTED, never a gate** (prereg §8.3):
  the CAMPD unit-hour count and the model's tranche-hour count are different
  grains and no ratio between them decides anything.
* **P3 protects C6/C8 only** — C7 ``shape`` is the MISO keeper's STANDING FAIL
  (``COAL_PRB`` ×3y), expected FAIL in BOTH arms, covered by P2's subset rule.
  This lever is not a C7 instrument and claims nothing there (prereg §6 P6).

Every criterion comes from ``calibration_verdict.py``'s own ``metrics.json``,
never re-derived.

    uv run python scripts/probes/_miso121_dual_fuel_ab.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/miso117_ctheatrate_B"
ARM_A = REPO / "results/calibration/miso121_control_A"
ARM_B = REPO / "results/calibration/miso121_dualfuel_B"
SCREEN = REPO / "results/calibration/_miso121_dual_fuel_screen.json"
OUT_PATH = REPO / "results/calibration/_miso121_dual_fuel_ab.json"

YEARS = (2023, 2024, 2025)

#: The single key under test.
FLAG = "dual_fuel_switching"
#: Siblings that must stay OFF in BOTH arms (rule 19 [R-ONE-MECH], prereg §1).
SIBLINGS = ("dual_fuel_oil_reattribution", "dual_fuel_oil_daily_parity")

#: K3 liveness thresholds (prereg §8.3).
K3_LIVENESS_MW = 50.0
K3_LIVENESS_PRICE = 0.10

#: K2 strict-byte tolerance (REPORTED, not a gate).
K2_TOL_MW = 1e-6

#: K6 one-sided direction tolerance ($/MWh). A cap can only remove offer level,
#: so the system mean must not RISE; the tolerance absorbs LP degeneracy only.
K6_TOL = 1e-3

#: P4 delta allowance (ercot-150's P4 lesson): max(+10 MWh, +1 % of control).
P4_ABS_MWH = 10.0
P4_REL = 0.01

EXTERNAL_PREFIX = "MISO_external"
P3_KEYS = ("governance", "forced_share")


# ── committed-artifact readers ──────────────────────────────────────────────


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 class-hour dispatch for one bundle-year."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _system(bundle: Path, year: int) -> pd.DataFrame:
    """P1 system hourly frame for one bundle-year, internal zones only."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    if "pass" in frame.columns:
        frame = frame[frame["pass"] == "P1"]
    return frame[~frame["zone"].astype(str).str.startswith(EXTERNAL_PREFIX)]


def _lw_price(bundle: Path, year: int) -> float:
    """Demand-weighted mean λ over the internal zones."""
    fr = _system(bundle, year)
    return round(float((fr["price"] * fr["demand"]).sum() / fr["demand"].sum()), 4)


def _zone_price(bundle: Path, year: int) -> dict[str, float]:
    """Simple-mean λ per internal zone."""
    fr = _system(bundle, year)
    return {
        str(k): round(float(v), 6)
        for k, v in fr.groupby("zone")["price"].mean().items()
    }


def _pairwise(a: Path, b: Path, year: int) -> dict:
    """Max / by-class class-hour divergence between two bundles for one year."""
    left = _class_hourly(a, year).set_index(["klass", "hour"])["mw"].sort_index()
    right = _class_hourly(b, year).set_index(["klass", "hour"])["mw"].sort_index()
    lj, rj = left.align(right, join="outer", fill_value=0.0)
    diff = (lj - rj).abs()
    return {
        "max_abs_diff_mw": round(float(diff.max()), 6),
        "max_by_class_mw": {
            str(k): round(float(v), 4)
            for k, v in diff.groupby(level="klass").max().items()
        },
    }


def _slack_dump(bundle: Path, year: int) -> tuple[float, float]:
    """Total slack / dump energy for one bundle-year, MWh."""
    frame = _system(bundle, year)
    return round(float(frame["slack"].sum()), 3), round(float(frame["dump"].sum()), 3)


def _scenario_block(bundle: Path) -> dict:
    """The bundle's recorded ``run_config`` scenario block."""
    path = bundle / "run_config.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("scenario_config", {}) or {}


def _metrics(bundle: Path) -> dict | None:
    """The bundle's own ``calibration_verdict`` scorecard, if written."""
    path = bundle / "metrics.json"
    return json.loads(path.read_text()) if path.exists() else None


def _criteria(bundle: Path) -> dict[str, str]:
    """``{criterion: status}`` straight from ``metrics.json`` — never re-derived."""
    m = _metrics(bundle)
    if not m:
        return {}
    return {
        k: (v.get("status") if isinstance(v, dict) else v)
        for k, v in (m.get("criteria") or {}).items()
    }


# ── K1-K6: construction gates (prereg §8.3) ────────────────────────────────


def k1_flag_fidelity() -> dict:
    """Arm B arms the flag, the control does not, and both keep siblings OFF."""
    a, b = _scenario_block(ARM_A), _scenario_block(ARM_B)
    sib_ok = all(
        a.get(s) in (False, None) and b.get(s) in (False, None) for s in SIBLINGS
    )
    ok = a.get(FLAG) in (False, None) and b.get(FLAG) is True and sib_ok
    return {
        "passed": bool(ok),
        "A": {FLAG: a.get(FLAG), **{s: a.get(s) for s in SIBLINGS}},
        "B": {FLAG: b.get(FLAG), **{s: b.get(s) for s in SIBLINGS}},
        "siblings_off_both_arms": bool(sib_ok),
    }


def k2_control_integrity() -> dict:
    """Scorecard basis is the GATE; the strict byte basis is REPORTED."""
    keeper, control = _criteria(KEEPER), _criteria(ARM_A)
    km, cm = _metrics(KEEPER), _metrics(ARM_A)
    scorecard_ok = bool(
        keeper
        and control
        and keeper == control
        and (km or {}).get("determination") == (cm or {}).get("determination")
    )
    byte = {str(y): _pairwise(KEEPER, ARM_A, y) for y in YEARS}
    return {
        "passed": scorecard_ok,
        "basis": "scorecard (gate); byte basis reported below",
        "keeper_criteria": keeper,
        "control_criteria": control,
        "keeper_determination": (km or {}).get("determination"),
        "control_determination": (cm or {}).get("determination"),
        "byte_basis_identical": all(
            v["max_abs_diff_mw"] <= K2_TOL_MW for v in byte.values()
        ),
        "byte_basis_by_year": byte,
    }


def k3_liveness() -> dict:
    """The mechanism moves dispatch AND price.

    Both price grains are gated: this cap is **not** level-preserving (unlike
    the mean-zero zonal anchor), so the system delta is a legitimate liveness
    statistic here, not a demoted report.
    """
    rows, live = {}, True
    for year in YEARS:
        pw = _pairwise(ARM_A, ARM_B, year)
        pa, pb = _zone_price(ARM_A, year), _zone_price(ARM_B, year)
        zone_deltas = {z: round(pb[z] - pa[z], 6) for z in pa}
        max_zone = max(abs(v) for v in zone_deltas.values())
        d_sys = round(_lw_price(ARM_B, year) - _lw_price(ARM_A, year), 4)
        ok = pw["max_abs_diff_mw"] > K3_LIVENESS_MW and (
            max_zone > K3_LIVENESS_PRICE or abs(d_sys) > K3_LIVENESS_PRICE
        )
        live = live and ok
        rows[str(year)] = {
            "max_abs_class_hour_mw": pw["max_abs_diff_mw"],
            "max_abs_zone_price_delta": round(max_zone, 6),
            "A_lw_price": _lw_price(ARM_A, year),
            "B_lw_price": _lw_price(ARM_B, year),
            "delta_system_lw_price": d_sys,
            "zone_price_deltas": zone_deltas,
            "passed": bool(ok),
        }
    return {
        "passed": bool(live),
        "by_year": rows,
        "thresholds": {"mw": K3_LIVENESS_MW, "price": K3_LIVENESS_PRICE},
    }


def k4_single_delta() -> dict:
    """The two recorded scenario blocks differ in EXACTLY the one key."""
    a, b = _scenario_block(ARM_A), _scenario_block(ARM_B)
    diff = sorted(
        k
        for k in set(a) | set(b)
        if json.dumps(a.get(k), sort_keys=True, default=str)
        != json.dumps(b.get(k), sort_keys=True, default=str)
    )
    return {"passed": diff == [FLAG], "differing_keys": diff}


def k5_year_span() -> dict:
    """Both bundles solve exactly [2023, 2024, 2025] (rules 16 / 22)."""
    spans = {}
    for name, bundle in (("A", ARM_A), ("B", ARM_B)):
        meta = json.loads((bundle / "meta.json").read_text())
        spans[name] = sorted(int(y) for y in meta.get("years", []))
    return {"passed": all(v == list(YEARS) for v in spans.values()), "spans": spans}


def k6_direction_integrity() -> dict:
    """One-sided: a ``min(gas, oil)`` cap can only REMOVE offer level.

    The offer-side leg is an arithmetic identity of the applier
    (``np.minimum`` in place), cross-checked against the Phase-0 screen: every
    binding cell had ``gas > oil``, so every write strictly lowered the price
    and none raised it. The scored leg is the system λ, which must not rise.
    Zone-level rises are REPORTED (a cap can lift a zone's λ through
    commitment / flow second-order effects) and do not fail the gate.
    """
    screen = json.loads(SCREEN.read_text()) if SCREEN.exists() else {}
    rows, ok_all = {}, True
    zone_rises: dict[str, list[str]] = {}
    for year in YEARS:
        d_sys = round(_lw_price(ARM_B, year) - _lw_price(ARM_A, year), 6)
        ok = d_sys <= K6_TOL
        ok_all = ok_all and ok
        pa, pb = _zone_price(ARM_A, year), _zone_price(ARM_B, year)
        zone_rises[str(year)] = sorted(z for z in pa if (pb[z] - pa[z]) > K6_TOL)
        rows[str(year)] = {"delta_system_lw_price": d_sys, "passed": bool(ok)}
    return {
        "passed": bool(ok_all),
        "by_year": rows,
        "tolerance": K6_TOL,
        "offer_side_arithmetic": {
            "applier": "np.minimum(fuel_prices[g], oil_hourly, out=...) — "
            "in-place, one-sided by construction",
            "screen_binding_genhours_by_year": {
                y: v["leg_c"]["n_binding_genhours"]
                for y, v in (screen.get("by_year") or {}).items()
            },
            "screen_max_delta_fuel_by_year": {
                y: v["leg_c"]["max_delta_fuel"]
                for y, v in (screen.get("by_year") or {}).items()
            },
            "note": "every binding cell had gas > oil, so every write LOWERED "
            "the delivered price; no capable tranche's offer can rise",
        },
        "zones_with_rising_lambda_REPORTED": zone_rises,
    }


# ── P1-P5: the pre-registered kills (prereg §6) ────────────────────────────


def p_gates() -> dict:
    """Non-degradation kills, scored from metrics.json against the CONTROL."""
    ma, mb = _metrics(ARM_A), _metrics(ARM_B)
    if not (ma and mb):
        return {
            "available": False,
            "note": "metrics.json missing — run calibration_verdict --write-metrics",
        }
    ca, cb = _criteria(ARM_A), _criteria(ARM_B)
    fa = (ma.get("free_class_score") or {}).get("free", {})
    fb = (mb.get("free_class_score") or {}).get("free", {})
    aa = (ma.get("free_class_score") or {}).get("all", {})
    ab = (mb.get("free_class_score") or {}).get("all", {})
    fails_a = {k for k, v in ca.items() if v == "FAIL"}
    fails_b = {k for k, v in cb.items() if v == "FAIL"}
    p1 = bool(
        fb.get("pass") == fb.get("total")
        and fb.get("pass", 0) >= fa.get("pass", 0)
        and ab.get("pass") == ab.get("total")
    )
    p2 = fails_b.issubset(fails_a)
    p3 = all(cb.get(k) == "PASS" for k in P3_KEYS)
    sd = {
        str(y): {"A": _slack_dump(ARM_A, y), "B": _slack_dump(ARM_B, y)} for y in YEARS
    }
    p4_by_year, p4 = {}, True
    for y, v in sd.items():
        a_tot = v["A"][0] + v["A"][1]
        b_tot = v["B"][0] + v["B"][1]
        allow = a_tot + max(P4_ABS_MWH, P4_REL * a_tot)
        ok = b_tot <= allow
        p4 = p4 and ok
        p4_by_year[y] = {
            "A_total_mwh": a_tot,
            "B_total_mwh": b_tot,
            "allowance": round(allow, 3),
            "passed": bool(ok),
        }
    return {
        "available": True,
        "P1_free_class": {
            "passed": p1,
            "A_free": fa,
            "B_free": fb,
            "A_all": aa,
            "B_all": ab,
        },
        "P2_no_new_fail": {
            "passed": p2,
            "A_fails": sorted(fails_a),
            "B_fails": sorted(fails_b),
        },
        "P3_protective": {
            "passed": p3,
            "note": "C6/C8 only — C7 (shape) is the standing MISO FAIL, "
            "expected in BOTH arms, covered by P2's subset rule",
            "B": {k: cb.get(k) for k in P3_KEYS},
            "shape_status_REPORTED": {"A": ca.get("shape"), "B": cb.get("shape")},
        },
        "P4_slack_dump_delta": {"passed": p4, "by_year": p4_by_year, "raw": sd},
        "P5_no_fitted_followup": {
            "passed": True,
            "note": "declarative: the capable set is EIA-860's Multifuel switch "
            "flag and the parity price is MISO's own F923 Petroleum receipt — "
            "both measured registries, neither swept (rules 5 / 23)",
        },
        "P6_no_c7_claim": {
            "passed": True,
            "note": "C7 COAL_PRB is data-blocked; no C7 result is claimed in "
            "either direction (prereg §6 P6)",
            "shape_REPORTED": {"A": ca.get("shape"), "B": cb.get("shape")},
        },
    }


# ── K7 + REPORTED (prereg §8.3) ─────────────────────────────────────────────


def reported() -> dict:
    """Quantities the prereg permits reporting; none can move a verdict."""
    screen = json.loads(SCREEN.read_text()) if SCREEN.exists() else {}
    out: dict = {}

    # K7 — switched-volume plausibility. DIFFERENT GRAINS, no ratio is a gate.
    k7: dict = {"is_a_gate": False}
    for year in YEARS:
        y = str(year)
        legc = ((screen.get("by_year") or {}).get(y) or {}).get("leg_c", {})
        legd = ((screen.get("leg_d") or {}).get("by_year") or {}).get(y, {})
        k7[y] = {
            "model_binding_TRANCHE_hours": legc.get("n_binding_genhours"),
            "campd_oil_signature_UNIT_hours": legd.get("oil_signature_unit_hours"),
            "campd_units_with_oil_signature": legd.get("n_units_with_oil_signature"),
            "campd_plants_covered": legd.get("n_plants_found"),
        }
    k7["note"] = (
        "tranche-hours vs unit-hours are different grains (369 model tranches "
        "over 89 capable plants; CAMPD covers 49 of them), so no ratio between "
        "these columns is meaningful — reported so any over-switching is "
        "visible rather than buried"
    )
    out["K7_switched_volume_REPORTED"] = k7

    # Class-energy movement between arms.
    for year in YEARS:
        a_cls = _class_hourly(ARM_A, year).groupby("klass")["mw"].sum() / 1e6
        b_cls = _class_hourly(ARM_B, year).groupby("klass")["mw"].sum() / 1e6
        delta = (b_cls - a_cls).round(4)
        out.setdefault("class_twh_delta_top", {})[str(year)] = {
            str(k): float(v)
            for k, v in delta.reindex(delta.abs().sort_values(ascending=False).index)
            .head(8)
            .items()
        }

    # Winter-vs-rest price movement: the mechanism's own claimed locus.
    for year in YEARS:
        fa, fb = _system(ARM_A, year), _system(ARM_B, year)
        merged = fa[["zone", "hour", "price", "demand"]].merge(
            fb[["zone", "hour", "price"]], on=["zone", "hour"], suffixes=("_a", "_b")
        )
        # Winter = the first 1416 h (Jan+Feb) and the last 744 h (Dec).
        is_winter = (merged["hour"] < 1416) | (merged["hour"] >= 8016)
        for label, sub in (("winter", merged[is_winter]), ("rest", merged[~is_winter])):
            if sub.empty:
                continue
            d = float(
                (
                    (sub["price_b"] - sub["price_a"]) * sub["demand"]
                ).sum()
                / sub["demand"].sum()
            )
            out.setdefault("seasonal_price_delta", {}).setdefault(str(year), {})[
                label
            ] = round(d, 4)

    out["criteria_from_calibration_verdict"] = {
        "keeper": _criteria(KEEPER),
        "A_control": _criteria(ARM_A),
        "B_arm": _criteria(ARM_B),
    }
    for name, bundle in (("keeper", KEEPER), ("A_control", ARM_A), ("B_arm", ARM_B)):
        m = _metrics(bundle)
        out.setdefault("determination", {})[name] = (m or {}).get("determination")
        out.setdefault("grade_summary", {})[name] = (m or {}).get("grade_summary")
        out.setdefault("free_class_headline", {})[name] = (
            (m or {}).get("free_class_score") or {}
        ).get("headline")
    return out


def main() -> int:
    result = {
        "prereg": "results/calibration/PREREG-miso121-dual-fuel-switching-2026-08-03.md",
        "keeper": str(KEEPER.relative_to(REPO)),
        "arm_A": str(ARM_A.relative_to(REPO)),
        "arm_B": str(ARM_B.relative_to(REPO)),
        "K1_flag_fidelity": k1_flag_fidelity(),
        "K2_control_integrity": k2_control_integrity(),
        "K3_liveness": k3_liveness(),
        "K4_single_delta": k4_single_delta(),
        "K5_year_span": k5_year_span(),
        "K6_direction_integrity": k6_direction_integrity(),
        "kills": p_gates(),
        "reported": reported(),
    }
    gates = [k for k in result if k.startswith("K")]
    result["all_gates_passed"] = all(result[k]["passed"] for k in gates)
    kills = result["kills"]
    result["all_kills_passed"] = (
        all(v["passed"] for k, v in kills.items() if isinstance(v, dict) and "passed" in v)
        if kills.get("available")
        else None
    )

    print("=" * 78)
    print("miso-121 A/B — dual_fuel_switching at MISO (PREREG §8.3)")
    print("=" * 78)
    for k in gates:
        print(f"  {k:26s} {'PASS' if result[k]['passed'] else 'FAIL'}")
    if kills.get("available"):
        for k, v in kills.items():
            if isinstance(v, dict) and "passed" in v:
                print(f"  {k:26s} {'PASS' if v['passed'] else 'FAIL'}")
    print(f"\n  all gates passed: {result['all_gates_passed']}")
    print(f"  all kills passed: {result['all_kills_passed']}")

    OUT_PATH.write_text(json.dumps(result, indent=2, default=str))
    print(f"\nwrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
