#!/usr/bin/env python3
"""ercot-150 A/B scorer — the zone-resolved gas-offer margin anchor at ERCOT.

Scores **only** the gates pre-registered in
``results/calibration/PREREG-ercot150-zonal-margin-anchor-2026-08-02.md``
(construction K1-K5 in §4, non-degradation kills P1-P5 in §5) and reports
**only** the quantities §3.2 declares reportable.

Adapted from ``_pjm144_zonal_anchor_ab.py`` with the changes ERCOT's applier
convention forces (prereg §1.2/§4):

* ERCOT's ``apply_ercot_zonal_gas_basis`` is a capacity-weighted MEAN-ZERO
  spread **plus a flat measured EP level correction** (the TX
  delivered-to-electric-power basis replacing the ``-0.50`` scalar), so the
  arm's effect is a TWO-SIDED spread on top of a one-sided level shift —
  nyiso-109's K6 direction gate stays DROPPED (the effect is not one-sided),
  and the per-zone direction table is REPORTED against the offer-side
  prediction ``sign(anchor_z − ISO anchor)``.
* **K3 liveness prices on the ZONAL grain** (the pjm-144 leg): ERCOT's West
  decouples under binding GTCs, so the interesting price effect is zonal;
  the system load-weighted delta is REPORTED with no threshold. West and
  Panhandle deltas are additionally broken out (the decoupling question).
* **P2 gains a per-year leg**: unlike PJM (whose control FAIL set was empty),
  ERCOT's control carries 4 criterion-grain FAILs, several failing in ONE
  year only (C3a/C3b 2023-only). The criterion-grain subset test alone would
  let a 2024 PASS→FAIL flip hide inside an already-FAIL criterion, so the
  per-(criterion, year, key) rows of the captured full verdicts
  (``_ercot150_verdict_{A,B}.json`` — ``calibration_verdict.determine``'s own
  output, never re-derived) are compared: every row PASS in the control must
  not be FAIL in the arm.

Every criterion is taken from ``scripts/calibration_verdict.py``'s own
``metrics.json`` / captured full-verdict JSON, never re-derived; the only λ
this file computes itself is the per-zone / demand-weighted means used for
the K3 delta and the reported direction table, which are construction
quantities on the DELTA between the two arms, not scored criteria.

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_ercot150_zonal_anchor_ab.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/ercot149_gas_event_cap_arm"
ARM_A = REPO / "results/calibration/ercot150_control_A"
ARM_B = REPO / "results/calibration/ercot150_zonalanchor_B"
VERDICT_A = REPO / "results/calibration/_ercot150_verdict_A.json"
VERDICT_B = REPO / "results/calibration/_ercot150_verdict_B.json"
OUT_PATH = REPO / "results/calibration/_ercot150_zonal_anchor_ab.json"

YEARS = (2023, 2024, 2025)

#: The two keys under test — both ``ScenarioConfig`` fields recorded in the
#: run_config scenario block.
FLAGS = ("gas_offer_margin_zonal_anchor", "gas_offer_margin_anchor_by_zone")

#: K3 liveness thresholds (prereg §4): class-hour MW plus the ZONAL price leg.
K3_LIVENESS_MW = 50.0
K3_LIVENESS_ZONAL_PRICE = 0.10

#: K2 strict-byte tolerance (REPORTED, not a gate).
K2_TOL_MW = 1e-6

#: The Waha-priced zones broken out in the K3 report (the decoupling question).
WAHA_ZONES = ("West", "Panhandle")


# ── committed-artifact readers ──────────────────────────────────────────────


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 class-hour dispatch for one bundle-year."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _system(bundle: Path, year: int) -> pd.DataFrame:
    """P1 system hourly frame for one bundle-year (ERCOT: all zones internal)."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    if "pass" in frame.columns:
        frame = frame[frame["pass"] == "P1"]
    return frame


def _lw_price(bundle: Path, year: int) -> float:
    """Demand-weighted mean λ over the zones."""
    fr = _system(bundle, year)
    return round(float((fr["price"] * fr["demand"]).sum() / fr["demand"].sum()), 4)


def _zone_price(bundle: Path, year: int) -> dict[str, float]:
    """Simple-mean λ per zone."""
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


def _verdict_rows(path: Path) -> dict[tuple, str] | None:
    """``{(criterion, year, key): status}`` from a captured full verdict JSON."""
    if not path.exists():
        return None
    v = json.loads(path.read_text())
    rows: dict[tuple, str] = {}
    for cid, c in (v.get("criteria") or {}).items():
        for r in c.get("records") or []:
            rows[(cid, r.get("year"), r.get("key"))] = str(r.get("status"))
    return rows or None


def _anchor_sides() -> tuple[dict[str, float], list[str], list[str]]:
    """The registered ERCOT zone anchors split into above / below the ISO anchor."""
    from market_sim.config.constants import (
        GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
        GAS_OFFER_MARGIN_ANCHOR_BY_ZONE,
    )

    iso_anchor = GAS_OFFER_MARGIN_ANCHOR_BY_ISO["ERCOT"]
    table = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["ERCOT"]
    above = sorted(z for z, a in table.items() if a > iso_anchor)
    below = sorted(z for z, a in table.items() if a < iso_anchor)
    return table, above, below


# ── K1-K5: construction gates (prereg §4) ──────────────────────────────────


def k1_flag_fidelity() -> dict:
    """Arm B records the gate + the resolved zone map; the control records neither.

    ERCOT extension: the shared-anchor mechanisms this lever must NOT touch —
    ``gas_offer_margin_anchor`` (the ISO window anchor) and the ERCOT-139
    ``cc_committed_offer_margin`` / ``cc_committed_offer_level`` pair, which
    reads the CONFIG-level anchor only — are asserted equal in both arms.
    """
    from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ZONE

    table = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["ERCOT"]
    a, b = _scenario_block(ARM_A), _scenario_block(ARM_B)
    b_map = b.get("gas_offer_margin_anchor_by_zone")
    ok = (
        a.get("gas_offer_margin_zonal_anchor") in (False, None)
        and a.get("gas_offer_margin_anchor_by_zone") in (None, {})
        and b.get("gas_offer_margin_zonal_anchor") is True
        and isinstance(b_map, dict)
        and {k: round(float(v), 6) for k, v in b_map.items()}
        == {k: round(float(v), 6) for k, v in table.items()}
        # The mechanism this anchors must be armed in BOTH arms and unchanged.
        and a.get("gas_offer_net_revenue_margin") is True
        and b.get("gas_offer_net_revenue_margin") is True
        and a.get("gas_offer_margin_anchor") == b.get("gas_offer_margin_anchor")
        # The CC committed measured level keeps its own (ISO-anchor) identity.
        and a.get("cc_committed_offer_margin") is True
        and b.get("cc_committed_offer_margin") is True
        and a.get("cc_committed_offer_level") == b.get("cc_committed_offer_level")
    )
    return {
        "passed": bool(ok),
        "A": {k: a.get(k) for k in FLAGS},
        "B": {k: b.get(k) for k in FLAGS},
        "registry": table,
        "iso_anchor_A": a.get("gas_offer_margin_anchor"),
        "iso_anchor_B": b.get("gas_offer_margin_anchor"),
        "cc_committed_level_A": a.get("cc_committed_offer_level"),
        "cc_committed_level_B": b.get("cc_committed_offer_level"),
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
    """The mechanism moves dispatch AND some zone's price in every year.

    The price leg is ZONAL (prereg §4): the mean-zero spread can be live at
    ~zero net system effect (the pjm-144 lesson), and ERCOT's West decouples
    under binding GTCs, so the zone grain is where a real effect must show.
    The system load-weighted delta and the Waha-zone deltas are REPORTED.
    """
    rows, live = {}, True
    for year in YEARS:
        pw = _pairwise(ARM_A, ARM_B, year)
        pa, pb = _zone_price(ARM_A, year), _zone_price(ARM_B, year)
        zone_deltas = {z: round(pb[z] - pa[z], 6) for z in pa}
        max_zone = max(abs(v) for v in zone_deltas.values())
        d_sys = round(_lw_price(ARM_B, year) - _lw_price(ARM_A, year), 4)
        ok = (
            pw["max_abs_diff_mw"] > K3_LIVENESS_MW
            and max_zone > K3_LIVENESS_ZONAL_PRICE
        )
        live = live and ok
        rows[str(year)] = {
            "max_abs_class_hour_mw": pw["max_abs_diff_mw"],
            "max_abs_zone_price_delta": round(max_zone, 6),
            "waha_zone_deltas_REPORTED": {
                z: zone_deltas.get(z) for z in WAHA_ZONES if z in zone_deltas
            },
            "A_lw_price": _lw_price(ARM_A, year),
            "B_lw_price": _lw_price(ARM_B, year),
            "delta_system_lw_price_REPORTED": d_sys,
            "passed": bool(ok),
        }
    return {
        "passed": bool(live),
        "by_year": rows,
        "thresholds": {"mw": K3_LIVENESS_MW, "zonal_price": K3_LIVENESS_ZONAL_PRICE},
    }


def k4_single_delta() -> dict:
    """The two recorded scenario blocks differ in EXACTLY the two keys."""
    a, b = _scenario_block(ARM_A), _scenario_block(ARM_B)
    diff = sorted(
        k
        for k in set(a) | set(b)
        if json.dumps(a.get(k), sort_keys=True, default=str)
        != json.dumps(b.get(k), sort_keys=True, default=str)
    )
    return {"passed": diff == sorted(FLAGS), "differing_keys": diff}


def k5_year_span() -> dict:
    """Both bundles solve exactly [2023, 2024, 2025] (rules 16 / 22)."""
    spans = {}
    for name, bundle in (("A", ARM_A), ("B", ARM_B)):
        meta = json.loads((bundle / "meta.json").read_text())
        spans[name] = sorted(int(y) for y in meta.get("years", []))
    return {"passed": all(v == list(YEARS) for v in spans.values()), "spans": spans}


# ── P1-P5: the pre-registered kills (prereg §5) ────────────────────────────


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
    # P2 leg 1 — criterion grain: no NEW criterion-level FAIL.
    p2_criterion = fails_b.issubset(fails_a)
    # P2 leg 2 — per-(criterion, year, key) rows from the captured full
    # verdicts: a row PASSing in the control must not FAIL in the arm. This is
    # what stops a C3a-2024 / C3b-2024 PASS→FAIL flip hiding inside an
    # already-FAIL criterion (ERCOT's C3a/C3b fail in 2023 ONLY).
    ra, rb = _verdict_rows(VERDICT_A), _verdict_rows(VERDICT_B)
    if ra is None or rb is None:
        p2_rows_ok = None
        flipped: list = ["<captured verdict JSONs missing>"]
    else:
        flipped = sorted(
            str(k)
            for k, st in ra.items()
            if st == "PASS" and rb.get(k) == "FAIL"
        )
        p2_rows_ok = not flipped
    p2 = bool(p2_criterion and (p2_rows_ok is True))
    # P3 — protective gates that PASS in the control stay PASS. `shape` (C7)
    # is a KEEPER FAIL at ERCOT (the 2023 lignite cv-leg), so it is excluded
    # here and covered by P2's row grain instead.
    p3 = all(cb.get(k) == "PASS" for k in ("governance", "forced_share"))
    sd = {
        str(y): {"A": _slack_dump(ARM_A, y), "B": _slack_dump(ARM_B, y)}
        for y in YEARS
    }
    p4 = all(v["A"] == (0.0, 0.0) and v["B"] == (0.0, 0.0) for v in sd.values())
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
            "criterion_grain_passed": p2_criterion,
            "A_fails": sorted(fails_a),
            "B_fails": sorted(fails_b),
            "row_grain_passed": p2_rows_ok,
            "rows_flipped_pass_to_fail": flipped,
        },
        "P3_protective": {
            "passed": p3,
            "B": {k: cb.get(k) for k in ("governance", "forced_share")},
            "note": "shape (C7) is a control FAIL at ERCOT — covered by P2's "
            "row grain, not required PASS here",
        },
        "P4_slack_dump_zero": {"passed": p4, "by_year": sd},
        "P5_no_fitted_followup": {
            "passed": True,
            "note": "declarative: the zone anchors are the derive script's own "
            "output (keeper-fleet weights, runtime applier) and were never "
            "swept (rule 23)",
        },
    }


# ── REPORTED, never a kill (prereg §3.2) ───────────────────────────────────


def reported() -> dict:
    """Quantities the prereg permits reporting; none of them can move a verdict."""
    table, above, below = _anchor_sides()
    out: dict = {
        "anchor_table": table,
        "zones_above_iso_anchor": above,
        "zones_below_iso_anchor": below,
    }
    direction: dict = {}
    for year in YEARS:
        pa, pb = _zone_price(ARM_A, year), _zone_price(ARM_B, year)
        deltas = {z: round(pb[z] - pa[z], 6) for z in pa}
        agree = sum(1 for z in above if deltas.get(z, 0.0) > 0.0) + sum(
            1 for z in below if deltas.get(z, 0.0) < 0.0
        )
        direction[str(year)] = {
            "delta_by_zone": deltas,
            "above_zone_mean": round(
                float(np.mean([deltas.get(z, 0.0) for z in above])), 6
            ),
            "below_zone_mean": round(
                float(np.mean([deltas.get(z, 0.0) for z in below])), 6
            ),
            "offer_side_sign_agreement": f"{agree}/{len(above) + len(below)}",
        }
    out["zonal_direction_REPORTED"] = direction
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
    # Every scored criterion, straight from each bundle's own metrics.json —
    # including the four control FAILs whose per-year movement P2 polices.
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
        tail = ((m or {}).get("criteria") or {}).get("price_tail")
        out.setdefault("price_tail_detail", {})[name] = tail
    return out


def main() -> int:
    """Score every pre-registered gate and write the A/B JSON."""
    res = {
        "probe": "ercot-150 zone-resolved gas-offer margin anchor A/B",
        "prereg": (
            "results/calibration/PREREG-ercot150-zonal-margin-anchor-2026-08-02.md"
        ),
        "arms": {"A_control": ARM_A.name, "B": ARM_B.name, "keeper": KEEPER.name},
        "construction_gates": {
            "K1_flag_fidelity": k1_flag_fidelity(),
            "K2_control_integrity": k2_control_integrity(),
            "K3_liveness": k3_liveness(),
            "K4_single_delta": k4_single_delta(),
            "K5_year_span": k5_year_span(),
        },
        "k6_dropped": (
            "nyiso-109's K6 direction-integrity gate stays DROPPED: ERCOT's "
            "applier is a capacity-weighted mean-zero spread plus a flat "
            "measured EP level correction — a two-sided spread on a one-sided "
            "level, neither of which admits a one-sided gate; direction is "
            "REPORTED, never gated"
        ),
        "kill_gates": p_gates(),
        "reported_never_a_kill": reported(),
    }

    print("\n=== ercot-150 construction gates (prereg §4) ===")
    for name, gate in res["construction_gates"].items():
        print(f"  {name:<26} {'PASS' if gate['passed'] else 'FAIL'}")
    k2 = res["construction_gates"]["K2_control_integrity"]
    print(
        f"  K2 byte basis (REPORTED)   "
        f"{'identical' if k2['byte_basis_identical'] else 'DRIFTED — its own finding'}"
    )

    print("\n=== kill gates (prereg §5) ===")
    kg = res["kill_gates"]
    if kg.get("available"):
        for name in (
            "P1_free_class",
            "P2_no_new_fail",
            "P3_protective",
            "P4_slack_dump_zero",
            "P5_no_fitted_followup",
        ):
            print(f"  {name:<26} {'PASS' if kg[name]['passed'] else 'KILL'}")
    else:
        print(f"  {kg.get('note')}")

    print("\n=== system λ (A control -> B arm; REPORTED, no threshold) ===")
    for year in YEARS:
        r = res["construction_gates"]["K3_liveness"]["by_year"][str(year)]
        print(
            f"  {year}  {r['A_lw_price']:>8.3f} -> {r['B_lw_price']:>8.3f}"
            f"   Δ {r['delta_system_lw_price_REPORTED']:>+7.3f} $/MWh"
            f"   max|Δzone| {r['max_abs_zone_price_delta']:.3f}"
            f"   West Δ {r['waha_zone_deltas_REPORTED'].get('West')}"
        )

    print("\n=== zonal direction (level + spread, REPORTED) ===")
    for year in YEARS:
        d = res["reported_never_a_kill"]["zonal_direction_REPORTED"][str(year)]
        print(
            f"  {year}  above-anchor mean {d['above_zone_mean']:>+8.4f}"
            f"   below-anchor mean {d['below_zone_mean']:>+8.4f}"
            f"   sign agreement {d['offer_side_sign_agreement']}"
        )

    print("\n=== determination ===")
    for name in ("keeper", "A_control", "B_arm"):
        print(f"  {name:<12} {res['reported_never_a_kill']['determination'][name]}")

    OUT_PATH.write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(f"\nwrote {OUT_PATH}")
    ok = all(g["passed"] for g in res["construction_gates"].values())
    if kg.get("available"):
        ok = ok and all(
            kg[k]["passed"]
            for k in (
                "P1_free_class",
                "P2_no_new_fail",
                "P3_protective",
                "P4_slack_dump_zero",
                "P5_no_fitted_followup",
            )
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
