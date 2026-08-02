#!/usr/bin/env python3
"""pjm-144 A/B scorer — the zone-resolved gas-offer margin anchor at PJM.

Scores **only** the gates pre-registered in
``results/calibration/PREREG-pjm144-zonal-margin-anchor-2026-08-02.md``
(construction K1-K5 in §4, non-degradation kills P1-P5 in §5) and reports
**only** the quantities §3.2 declares reportable.

Adapted from ``_nyiso109_zonal_anchor_ab.py`` with the two changes PJM's
applier convention forces (prereg §1.2/§4): PJM's zonal basis is the
capacity-weighted MEAN-ZERO core, so the arm's price effect is TWO-SIDED —

* nyiso-109's **K6 direction-integrity gate is DROPPED**, not copied: a
  two-sided mechanism must not be scored on a one-sided gate. The zonal
  direction pattern is REPORTED (offer-side expectation: premium-anchor zones
  up, discount-anchor zones down) and can never kill.
* **K3 liveness prices on the ZONAL grain**: a mean-zero redistribution can be
  fully live while its net system-level price effect is ~0, so the price leg is
  ``max over internal zones |Δ mean λ| > $0.10`` in every year; the system
  load-weighted delta is REPORTED with no threshold.

Every criterion — C3c included — is taken from
``scripts/calibration_verdict.py``'s own ``metrics.json``, never re-derived
(the nyiso-108 scorer's measurement-bug class); the only λ this file computes
itself is the per-zone / demand-weighted means used for the K3 delta and the
reported direction table, which are construction quantities on the DELTA
between the two arms, not scored criteria.

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_pjm144_zonal_anchor_ab.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/pjm143_hy_level_B"
ARM_A = REPO / "results/calibration/pjm144_control_A"
ARM_B = REPO / "results/calibration/pjm144_zonalanchor_B"
OUT_PATH = REPO / "results/calibration/_pjm144_zonal_anchor_ab.json"

YEARS = (2023, 2024, 2025)

#: The two keys under test — both ``ScenarioConfig`` fields recorded in the
#: run_config scenario block.
FLAGS = ("gas_offer_margin_zonal_anchor", "gas_offer_margin_anchor_by_zone")

#: K3 liveness thresholds (prereg §4): class-hour MW plus the ZONAL price leg.
K3_LIVENESS_MW = 50.0
K3_LIVENESS_ZONAL_PRICE = 0.10

#: K2 strict-byte tolerance (REPORTED, not a gate).
K2_TOL_MW = 1e-6

EXTERNAL_PREFIX = "PJM_external"


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
    pj = _system(bundle, year)
    return round(float((pj["price"] * pj["demand"]).sum() / pj["demand"].sum()), 4)


def _zone_price(bundle: Path, year: int) -> dict[str, float]:
    """Simple-mean λ per internal zone."""
    pj = _system(bundle, year)
    return {
        str(k): round(float(v), 6)
        for k, v in pj.groupby("zone")["price"].mean().items()
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


def _anchor_sides() -> tuple[dict[str, float], list[str], list[str]]:
    """The registered PJM zone anchors split into premium / discount sides."""
    from market_sim.config.constants import (
        GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
        GAS_OFFER_MARGIN_ANCHOR_BY_ZONE,
    )

    iso_anchor = GAS_OFFER_MARGIN_ANCHOR_BY_ISO["PJM"]
    table = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["PJM"]
    premium = sorted(z for z, a in table.items() if a > iso_anchor)
    discount = sorted(z for z, a in table.items() if a < iso_anchor)
    return table, premium, discount


# ── K1-K5: construction gates (prereg §4) ──────────────────────────────────


def k1_flag_fidelity() -> dict:
    """Arm B records the gate + the resolved zone map; the control records neither."""
    from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ZONE

    table = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["PJM"]
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
    )
    return {
        "passed": bool(ok),
        "A": {k: a.get(k) for k in FLAGS},
        "B": {k: b.get(k) for k in FLAGS},
        "registry": table,
        "iso_anchor_A": a.get("gas_offer_margin_anchor"),
        "iso_anchor_B": b.get("gas_offer_margin_anchor"),
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

    The price leg is ZONAL (prereg §4): PJM's mean-zero re-centring preserves
    the aggregate offer level by construction, so the system-level delta is
    reported with no threshold and cannot decide liveness.
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
    p2 = fails_b.issubset(fails_a)
    p3 = all(cb.get(k) == "PASS" for k in ("governance", "shape", "forced_share"))
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
            "A_fails": sorted(fails_a),
            "B_fails": sorted(fails_b),
        },
        "P3_protective": {
            "passed": p3,
            "B": {k: cb.get(k) for k in ("governance", "shape", "forced_share")},
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
    table, premium, discount = _anchor_sides()
    out: dict = {
        "anchor_table": table,
        "premium_zones": premium,
        "discount_zones": discount,
    }
    direction: dict = {}
    for year in YEARS:
        pa, pb = _zone_price(ARM_A, year), _zone_price(ARM_B, year)
        deltas = {z: round(pb[z] - pa[z], 6) for z in pa}
        agree = sum(1 for z in premium if deltas.get(z, 0.0) > 0.0) + sum(
            1 for z in discount if deltas.get(z, 0.0) < 0.0
        )
        direction[str(year)] = {
            "delta_by_zone": deltas,
            "premium_zone_mean": round(
                float(np.mean([deltas.get(z, 0.0) for z in premium])), 6
            ),
            "discount_zone_mean": round(
                float(np.mean([deltas.get(z, 0.0) for z in discount])), 6
            ),
            "offer_side_sign_agreement": f"{agree}/{len(premium) + len(discount)}",
        }
    out["zonal_direction_two_sided_REPORTED"] = direction
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
    # including price_tail (C3c), whose PJM margin is the keeper's thinnest.
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
        "probe": "pjm-144 zone-resolved gas-offer margin anchor A/B",
        "prereg": (
            "results/calibration/PREREG-pjm144-zonal-margin-anchor-2026-08-02.md"
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
            "nyiso-109's K6 direction-integrity gate is DROPPED by the prereg: "
            "PJM's applier is capacity-weighted mean-zero, so the effect is "
            "two-sided and direction is REPORTED, never gated"
        ),
        "kill_gates": p_gates(),
        "reported_never_a_kill": reported(),
    }

    print("\n=== pjm-144 construction gates (prereg §4) ===")
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
        )

    print("\n=== zonal direction (two-sided, REPORTED) ===")
    for year in YEARS:
        d = res["reported_never_a_kill"]["zonal_direction_two_sided_REPORTED"][
            str(year)
        ]
        print(
            f"  {year}  premium mean {d['premium_zone_mean']:>+8.4f}"
            f"   discount mean {d['discount_zone_mean']:>+8.4f}"
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
