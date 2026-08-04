#!/usr/bin/env python3
"""nyiso-120 A/B scorer — the hybrid-cogen dark-fuel scope gate at NYISO.

Scores **only** the gates pre-registered in
``results/calibration/PREREG-nyiso120-eastriver-scope-gate-2026-08-04.md`` §4-§5,
adapted from ``_miso122_scope_gate_ab.py``. Three things about this lever's
geometry at NYISO differ from MISO's and are stated here so nothing is misread:

* **THE DELTA IS AN INPUT FILE, NOT A CONFIG FLAG.** There is no
  ``ScenarioConfig`` key under test — ``measured_chp_heat_rates`` is armed in
  BOTH arms and NYISO's cell is already ``K``. What changes is the committed
  artifact ``data/raw/_processed-legacy/chp_power_only_heat_rates_NYISO.csv``.
  So K1 inverts (identical ``run_config`` blocks, differing artifact sha256) and
  K4 demands **zero** differing config keys. An identical ``run_config`` is the
  EXPECTED result, never a wiring failure.
* **AT NYISO THE ROW LEAVES THE APPLIED MAP RATHER THAN MOVING INSIDE IT.**
  MISO's three rows were *corrected* (rate lowered in place). East River is
  *excluded* (``ok`` -> ``below_credited``), so it drops out of the
  ``flag == 'ok'`` map and reverts to the incumbent chain. The effective rate
  the LP sees therefore has to be read as "``heat_rate`` if ``ok`` else the
  incumbent", which is what :func:`_effective_rates` does — reading only the
  applied map would score the change as a no-op.
* **THE INCUMBENT IS THE PLAIN eGRID RATE, WITH NO HAND FACTOR.**
  ``CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`` is ``{CAISO, PJM}``; NYISO is not in
  it, so the fallback is ``basis_heat_rate`` itself (7.4205) and the direction
  is unambiguously **downward**, 11.8032 -> 7.4205 on 306 MW of NYC ``CT_CHP``.
  In a hand-factor ISO this same exclusion would push the rate UP and K6's
  direction leg would have to invert — it is asserted here, not assumed.

Every criterion comes from ``calibration_verdict.py``'s own ``metrics.json``,
never re-derived.

    python scripts/probes/_nyiso120_scope_gate_ab.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/nyiso118_seny_span"
ARM_A = REPO / "results/calibration/nyiso120_control_A"
ARM_B = REPO / "results/calibration/nyiso120_scopegate_B"
ARTIFACT = REPO / "data/raw/_processed-legacy/chp_power_only_heat_rates_NYISO.csv"
#: The pre-change copy, kept for the A-arm's provenance so the sha comparison
#: is runnable without a checkout (git history is the other copy).
ARTIFACT_A = REPO / "results/calibration/_nyiso120_artifact_A.csv"
OUT_PATH = REPO / "results/calibration/_nyiso120_scope_gate_ab.json"

YEARS = (2023, 2024, 2025)

#: The mechanism whose INPUT changed. Armed in BOTH arms — it is not the delta.
MECHANISM = "measured_chp_heat_rates"
#: The class the moved row sits in; everything else must be a bystander.
TOUCHED_CLASSES = ("CT_CHP",)
#: Carried too, because a rate change reshuffles the whole CHP merit order.
CHP_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP")
EXTERNAL_PREFIX = "NYISO_external"
#: Protective criteria that must be PASS in the treatment (prereg §5).
P3_KEYS = ("governance", "forced_share")
#: NYISO's sole ledgered caveat. This lever claims NOTHING about it in either
#: direction (prereg §4.1) — it is reported, never a promotion or revert basis.
LEDGERED_CAVEAT = "price_tail"

#: K3 liveness thresholds (prereg §4 KE7; the 0.10 $/MWh bar is
#: miso-119/121/122's, reused for cross-adjudication comparability).
K3_LIVENESS_MW = 50.0
K3_LIVENESS_PRICE = 0.10
#: K2 strict-byte tolerance (REPORTED, not a gate — FINDING-nyiso114 §2).
K2_TOL_MW = 1e-6
#: K6 one-sided direction tolerance ($/MWh), absorbing LP degeneracy only.
K6_TOL = 1e-3
#: P4 delta allowance (ercot-150's P4 lesson): max(+10 MWh, +1 % of control).
P4_ABS_MWH = 10.0
P4_REL = 0.01


# ── committed-artifact readers ──────────────────────────────────────────────


def _sha(path: Path) -> str | None:
    """sha256 of a file, or ``None`` when it is absent."""
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        str(k): round(float(v), 6) for k, v in fr.groupby("zone")["price"].mean().items()
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


def _applied_rates(path: Path) -> dict[tuple[int, str], float]:
    """The ``flag == 'ok'`` map an artifact file would hand the loader."""
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    return {
        (int(r.plant_code), str(r.plant_group)): float(r.heat_rate)
        for r in df.itertuples(index=False)
        if str(r.flag) == "ok" and float(r.heat_rate) > 0.0
    }


def _effective_rates(path: Path) -> dict[tuple[int, str], float]:
    """The rate the LP actually charges each row: applied if ``ok``, else incumbent.

    This is the reading the NYISO change requires. An excluded row does not
    vanish from the model — it reverts to the incumbent chain, which at NYISO is
    the plain eGRID rate ``basis_heat_rate`` because NYISO is not in
    ``CHP_STEAM_CREDIT_HR_CORRECTION_ISOS``. Scoring the applied map alone would
    read East River's exclusion as "a row disappeared" rather than as the 37 %
    rate cut it is.
    """
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    out: dict[tuple[int, str], float] = {}
    for r in df.itertuples(index=False):
        key = (int(r.plant_code), str(r.plant_group))
        rate = (
            float(r.heat_rate)
            if str(r.flag) == "ok" and float(r.heat_rate) > 0.0
            else float(r.model_heat_rate)
        )
        if rate > 0.0:
            out[key] = rate
    return out


def _no_hand_factor_at_nyiso() -> bool:
    """Assert the incumbent fallback carries no legacy hand factor at NYISO.

    Read from the code, not assumed: in a hand-factor ISO this exclusion would
    push East River's rate UP and K6's direction leg would have to invert.
    """
    from market_sim.data.fleet import CHP_STEAM_CREDIT_HR_CORRECTION_ISOS

    return "NYISO" not in CHP_STEAM_CREDIT_HR_CORRECTION_ISOS


# ── K1-K6: construction gates (prereg §5) ──────────────────────────────────


def k1_artifact_fidelity() -> dict:
    """The INPUT differs, the CONFIG does not, and the mechanism is on in both."""
    a, b = _scenario_block(ARM_A), _scenario_block(ARM_B)
    mech_on = a.get(MECHANISM) is True and b.get(MECHANISM) is True
    sha_a, sha_b = _sha(ARTIFACT_A), _sha(ARTIFACT)
    eff_a, eff_b = _effective_rates(ARTIFACT_A), _effective_rates(ARTIFACT)
    moved = {
        f"{k[0]}:{k[1]}": {
            "A": round(eff_a[k], 4),
            "B": round(eff_b.get(k, float("nan")), 4),
            "pct": round(eff_b.get(k, float("nan")) / eff_a[k] - 1.0, 6),
        }
        for k in eff_a
        if k not in eff_b or abs(eff_b[k] - eff_a[k]) > 1e-9
    }
    ap_a, ap_b = _applied_rates(ARTIFACT_A), _applied_rates(ARTIFACT)
    ok = bool(mech_on and sha_a and sha_b and sha_a != sha_b and moved)
    return {
        "passed": ok,
        "note": "the delta is an INPUT FILE, not a config key — identical "
        "run_config blocks are expected, not a wiring failure",
        "basis": "EFFECTIVE rates (applied if flag=='ok' else the incumbent), "
        "because at NYISO the moved row LEAVES the applied map",
        "mechanism_armed_both_arms": bool(mech_on),
        "artifact_sha256": {"A": sha_a, "B": sha_b},
        "applied_map_size": {"A": len(ap_a), "B": len(ap_b)},
        "rows_that_moved_effective": moved,
        "rows_dropped_from_applied_map": sorted(
            f"{k[0]}:{k[1]}" for k in set(ap_a) - set(ap_b)
        ),
        "rows_added_to_applied_map": sorted(
            f"{k[0]}:{k[1]}" for k in set(ap_b) - set(ap_a)
        ),
    }


def k2_control_integrity() -> dict:
    """Scorecard basis is the GATE; the strict byte basis is REPORTED.

    ``FINDING-nyiso114`` §2: a P0-run-pattern keeper does not re-solve to
    byte-identity once main moves, so a non-zero control-vs-keeper divergence is
    measured and reported rather than treated as a failure. What it forbids is
    quoting any A/B delta against the KEEPER instead of against this control
    (prereg KE5).
    """
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
    """Does the corrected input move dispatch, and does it move price?"""
    rows, live_mw, live_px = {}, True, True
    for year in YEARS:
        pw = _pairwise(ARM_A, ARM_B, year)
        pa, pb = _zone_price(ARM_A, year), _zone_price(ARM_B, year)
        zone_deltas = {z: round(pb[z] - pa[z], 6) for z in pa}
        max_zone = max(abs(v) for v in zone_deltas.values())
        d_sys = round(_lw_price(ARM_B, year) - _lw_price(ARM_A, year), 4)
        mw_ok = pw["max_abs_diff_mw"] > K3_LIVENESS_MW
        px_ok = max_zone > K3_LIVENESS_PRICE or abs(d_sys) > K3_LIVENESS_PRICE
        live_mw = live_mw and mw_ok
        live_px = live_px and px_ok
        rows[str(year)] = {
            "max_abs_class_hour_mw": pw["max_abs_diff_mw"],
            "max_by_class_mw": pw["max_by_class_mw"],
            "max_abs_zone_price_delta": round(max_zone, 6),
            "A_lw_price": _lw_price(ARM_A, year),
            "B_lw_price": _lw_price(ARM_B, year),
            "delta_system_lw_price": d_sys,
            "zone_price_deltas": zone_deltas,
            "dispatch_live": bool(mw_ok),
            "price_live": bool(px_ok),
        }
    n_px = sum(1 for v in rows.values() if v["price_live"])
    return {
        "passed": bool(live_mw and live_px),
        "dispatch_live_all_years": bool(live_mw),
        "price_live_all_years": bool(live_px),
        "price_live_year_count": n_px,
        "by_year": rows,
        "thresholds": {"mw": K3_LIVENESS_MW, "price": K3_LIVENESS_PRICE},
    }


def k4_zero_config_delta() -> dict:
    """The two recorded scenario blocks must differ in NOTHING."""
    a, b = _scenario_block(ARM_A), _scenario_block(ARM_B)
    diff = sorted(
        k
        for k in set(a) | set(b)
        if json.dumps(a.get(k), sort_keys=True, default=str)
        != json.dumps(b.get(k), sort_keys=True, default=str)
    )
    return {"passed": diff == [], "differing_keys": diff}


def k5_year_span() -> dict:
    """Both bundles solve exactly [2023, 2024, 2025] (rules 16 / 22)."""
    spans = {}
    for name, bundle in (("A", ARM_A), ("B", ARM_B)):
        meta = json.loads((bundle / "meta.json").read_text())
        spans[name] = sorted(int(y) for y in meta.get("years", []))
    return {"passed": all(v == list(YEARS) for v in spans.values()), "spans": spans}


def k6_direction_integrity() -> dict:
    """One-sided: the corrected row's effective rate FALLS, so its cost falls.

    The offer-side leg is arithmetic on the artifact — every effective rate that
    moved must have fallen — and it is only unambiguous because NYISO carries no
    legacy hand factor (asserted, not assumed). The scored system leg is the
    demand-weighted λ, which must not rise. Zone-level rises are REPORTED, not
    gated: a cheaper unit can lift a neighbouring zone's λ through commitment
    and flow second-order effects.
    """
    eff_a, eff_b = _effective_rates(ARTIFACT_A), _effective_rates(ARTIFACT)
    raised = sorted(
        f"{k[0]}:{k[1]}" for k in eff_a if eff_b.get(k, eff_a[k]) > eff_a[k] + 1e-9
    )
    no_hand = _no_hand_factor_at_nyiso()
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
        "passed": bool(ok_all and not raised and no_hand),
        "by_year": rows,
        "tolerance": K6_TOL,
        "nyiso_carries_no_legacy_hand_factor": bool(no_hand),
        "offer_side_arithmetic": {
            "rule": "the excluded row reverts to the incumbent eGRID rate "
            "(7.4205) from the all-fuel add-back (11.8032) — a fall, and "
            "unambiguously so only because NYISO is not in "
            "CHP_STEAM_CREDIT_HR_CORRECTION_ISOS",
            "effective_rows_whose_rate_ROSE": raised,
        },
        "zones_with_rising_lambda_REPORTED": zone_rises,
    }


# ── P1-P6: the pre-registered kills ────────────────────────────────────────


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
    p1 = bool(fb.get("pass", 0) >= fa.get("pass", 0))
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
            "B": {k: cb.get(k) for k in P3_KEYS},
        },
        "P4_slack_dump_delta": {"passed": p4, "by_year": p4_by_year, "raw": sd},
        "P5_no_fitted_followup": {
            "passed": True,
            "note": "declarative: the dark-fuel share is CAMPD's own unit-grain "
            "heat input over the same plant's total, at the artifact's own "
            "eGRID vintage year — zero free parameters, no threshold, nothing "
            "swept (rules 5 / 23 / 24). The gate itself is miso-122's, shipped "
            "unmodified; this session edited no derive logic.",
        },
        "P6_no_c3c_claim": {
            "passed": True,
            "note": "price_tail (C3c) is NYISO's sole ledgered caveat. Prereg "
            "§4.1 declared IN ADVANCE that a C3c degradation does not revert "
            "the correction (rules 1/14) and a C3c improvement is not the "
            "promotion basis. Reported, never a verdict input.",
            "price_tail_REPORTED": {
                "A": ca.get(LEDGERED_CAVEAT),
                "B": cb.get(LEDGERED_CAVEAT),
            },
        },
    }


# ── W2 + REPORTED ───────────────────────────────────────────────────────────


def reported() -> dict:
    """Quantities the prereg permits reporting; none can move a verdict."""
    out: dict = {}

    w2: dict = {"is_a_gate": True}
    fired = True
    for year in YEARS:
        a_cls = _class_hourly(ARM_A, year).groupby("klass")["mw"].sum() / 1e6
        b_cls = _class_hourly(ARM_B, year).groupby("klass")["mw"].sum() / 1e6
        delta = (b_cls - a_cls).round(6)
        touched = {
            k: float(delta.get(k, 0.0)) for k in TOUCHED_CLASSES if k in delta.index
        }
        moved = any(abs(v) > 0.0 for v in touched.values())
        fired = fired and moved
        w2[str(year)] = {"touched_class_twh_delta": touched, "moved": bool(moved)}
    w2["passed"] = bool(fired)
    w2["note"] = (
        "the moved row sits in CT_CHP; a zero delta there in any year would "
        "mean the corrected artifact never reached the LP (the miso-113 "
        "hazard), not that the correction is inert"
    )
    out["W2_mechanism_fired"] = w2

    for year in YEARS:
        a_cls = _class_hourly(ARM_A, year).groupby("klass")["mw"].sum() / 1e6
        b_cls = _class_hourly(ARM_B, year).groupby("klass")["mw"].sum() / 1e6
        delta = (b_cls - a_cls).round(6)
        out.setdefault("class_twh_delta_top", {})[str(year)] = {
            str(k): float(v)
            for k, v in delta.reindex(delta.abs().sort_values(ascending=False).index)
            .head(8)
            .items()
        }
        out.setdefault("chp_class_twh", {})[str(year)] = {
            k: {"A": round(float(a_cls.get(k, 0.0)), 6), "B": round(float(b_cls.get(k, 0.0)), 6)}
            for k in CHP_CLASSES
        }
    return out


def main() -> int:
    """Score every pre-registered gate and write the A/B record."""
    result = {
        "session": "nyiso-120",
        "lever": "hybrid-cogen dark-fuel scope gate (miso-122) applied to NYISO's "
        "chp_power_only_heat_rates artifact — ORIS 2493 East River",
        "prereg": "results/calibration/PREREG-nyiso120-eastriver-scope-gate-2026-08-04.md",
        "keeper": "2026-08-03-nyiso-118-seny-span",
        "arms": {"A": str(ARM_A.name), "B": str(ARM_B.name)},
        "K1_artifact_fidelity": k1_artifact_fidelity(),
        "K2_control_integrity": k2_control_integrity(),
        "K3_liveness": k3_liveness(),
        "K4_zero_config_delta": k4_zero_config_delta(),
        "K5_year_span": k5_year_span(),
        "K6_direction_integrity": k6_direction_integrity(),
        "P_gates": p_gates(),
        "REPORTED": reported(),
    }

    k3 = result["K3_liveness"]
    if k3["price_live_year_count"] >= 2:
        verdict = "LIVE"
    elif result["REPORTED"]["W2_mechanism_fired"]["passed"]:
        verdict = "DISPATCH-LIVE / PRICE-INERT"
    else:
        verdict = "FULLY INERT"
    result["VERDICT"] = {
        "branch": verdict,
        "rule": "prereg KE7: LIVE iff max zonal |Δλ| >= 0.10 $/MWh in >= 2 of 3 "
        "years; otherwise DISPATCH-LIVE/PRICE-INERT if CT_CHP moved, else "
        "FULLY INERT",
        "the_correction_ships_under_every_branch": True,
        "reason": "rule 14 [R-ACCURATE] — an accurate input is never reverted "
        "because it did not help a residual; prereg §4.1 declared this in "
        "advance, including for a C3c degradation",
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps(result, indent=2, default=str))
    print(f"\nwrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
