"""miso-220 A/B scorer — COMMITTED BEFORE THE SOLVE, frozen against PREREG-miso220.

Scores the non-steam fossil ×1.10 offer lift (arm) against the designated keeper
(control, rule 29(b) form 4 — the keeper's committed bundle, never re-solved) on the
kills and predictions frozen in
``results/calibration/PREREG-miso220-nonsteam-offer-lift-2026-09-05.md``.

Every band and threshold below is transcribed from that PREREG. The control's C1 /
C3a / C8 numbers are frozen as literals from its own ``calibration_verdict --json``
so a control that drifts cannot silently move the bar.

Kills (PREREG §6):

* **K-1** any C1 ``fuelmix`` cell flips PASS -> FAIL (``CT_PEAKER``-2023 named ex ante
  as most likely; naming does NOT exempt it).
* **K-2** any C3a year outside +/-10 %.
* **K-3** ``ST_GAS``-2024 no better than the control's -7.155 TWh (mechanism refuted;
  reported at full magnitude, does not by itself block a gates-clean promotion).
* **K-4** C6 governance reads UNATTESTED.
* **K-5** determination worse in class than NOT-YET on C3a-2025 alone.

PROMOTION RULE (frozen): promote iff K-1, K-2, K-4 and K-5 are ALL silent AND
C3a-2025 lands inside +/-10 %.

Record: ``results/calibration/_miso220_ab_gates.json``. Exit 0 always — the verdict
is the record, not the exit code.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONTROL = REPO / "results/calibration/miso217_intermphys_B"
ARM = REPO / "results/calibration/miso220_nonsteamlift_B"
OUT = REPO / "results/calibration/_miso220_ab_gates.json"

C1_BAND_TWH = 8.00
C3A_BAND_PCT = 10.0

#: The CONTROL's every C1 cell (model - actual, TWh), frozen from its own verdict.
CONTROL_C1: dict[str, float] = {
    "CC_CHP|2023": -0.914, "CC_CHP|2024": +0.417, "CC_CHP|2025": +1.787,
    "CC_REGULAR|2023": -2.288, "CC_REGULAR|2024": +7.947, "CC_REGULAR|2025": -2.061,
    "COAL_BIT|2023": -2.272, "COAL_BIT|2024": -3.390, "COAL_BIT|2025": -1.465,
    "COAL_LIGNITE|2023": -0.568, "COAL_LIGNITE|2024": -0.744, "COAL_LIGNITE|2025": -0.726,
    "COAL_PRB|2023": +1.071, "COAL_PRB|2024": -2.159, "COAL_PRB|2025": -4.231,
    "CT_PEAKER|2023": -5.934, "CT_PEAKER|2024": -3.634, "CT_PEAKER|2025": -3.276,
    "ST_CHP|2023": -2.861, "ST_CHP|2024": -2.869, "ST_CHP|2025": -2.184,
    "ST_GAS|2023": -2.402, "ST_GAS|2024": -7.155, "ST_GAS|2025": -5.820,
}
CONTROL_C3A: dict[int, float] = {2023: +1.1, 2024: -2.9, 2025: -12.3}
CONTROL_C8_CT_PEAKER: dict[int, float] = {2023: 0.2280, 2024: 0.1573, 2025: 0.1319}
CONTROL_C8_ST_GAS: dict[int, float] = {2023: 0.1479, 2024: 0.1555, 2025: 0.2070}

#: PREREG §5 prediction bands, transcribed.
PRED = {
    "P1_passthrough_pct": (5.5, 7.5),
    "P2b_c3a_2025_pct": (-8.0, -5.0),
    "P2c_c3a_2023_pct": (6.5, 9.0),
    "P3_st_gas_2024_twh": (-6.8, -5.0),
    "P4_ct_peaker_2023_twh": (-8.5, -7.0),
    "P5_cc_regular_2024_twh": (5.5, 7.5),
}
NAMED_RISK_CELL = "CT_PEAKER|2023"


def _verdict(bundle: Path) -> dict:
    """Run ``calibration_verdict.py --json`` over a bundle and return the parsed report."""
    res = subprocess.run(
        [sys.executable, str(REPO / "scripts/calibration_verdict.py"), "--json", str(bundle)],
        capture_output=True, text=True, check=False,
    )
    if not res.stdout.strip():
        raise SystemExit(f"no JSON for {bundle}: {res.stderr[-800:]}")
    return json.loads(res.stdout)


def _c1(v: dict) -> dict:
    """``{class|year: model - actual TWh}`` from a verdict's C1 fuelmix records."""
    out = {}
    for rec in (v.get("criteria", {}).get("fuelmix") or {}).get("records", []):
        k, y = rec.get("key"), rec.get("year")
        if k is None or y is None:
            continue
        try:
            out[f"{k}|{y}"] = round(float(rec["model"]) - float(rec["actual"]), 4)
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _c1_status(v: dict) -> dict:
    """``{class|year: status}`` for the C1 fuelmix records."""
    return {
        f"{r.get('key')}|{r.get('year')}": r.get("status")
        for r in (v.get("criteria", {}).get("fuelmix") or {}).get("records", [])
        if r.get("key") is not None and r.get("year") is not None
    }


def _c3a(v: dict) -> dict:
    """``{year: signed % error}`` on the RT load-weighted mean LMP."""
    return {
        int(r["year"]): round(100.0 * (float(r["model"]) - float(r["actual"])) / float(r["actual"]), 4)
        for r in v["criteria"]["price_mean"]["records"]
        if r.get("benchmark") == "RT" and r.get("key") is None
    }


def _price(v: dict) -> dict:
    """``{year: model load-weighted mean LMP}`` — the P-1 pass-through numerator."""
    return {
        int(r["year"]): float(r["model"])
        for r in v["criteria"]["price_mean"]["records"]
        if r.get("benchmark") == "RT" and r.get("key") is None
    }


def _c8(bundle: Path, klass: str) -> dict:
    """``{year: forced share}`` for a class, from the bundle's D-2 diagnostics."""
    p = bundle / "legitimacy_diagnostics.json"
    if not p.exists():
        return {}
    rows = ((json.loads(p.read_text()).get("diagnostics") or {}).get("D2") or {}).get("rows", []) or []
    forced: dict = {}
    tot: dict = {}
    for r in rows:
        if r.get("class") != klass:
            continue
        y = int(r["year"])
        forced[y] = forced.get(y, 0.0) + float(r.get("forced_twh") or 0.0)
        if r.get("class_total_twh"):
            tot[y] = float(r["class_total_twh"])
    return {y: (round(forced[y] / tot[y], 4) if tot.get(y) else None) for y in forced}


def _c3c(v: dict) -> dict:
    """C3c price-tail records, as reported (hours above the tail threshold)."""
    return {
        f"{r.get('key')}|{r.get('year')}": {"model": r.get("model"), "actual": r.get("actual"),
                                            "status": r.get("status")}
        for r in (v.get("criteria", {}).get("price_tail") or {}).get("records", [])
    }


def _in(x, lo, hi) -> bool:
    """True when ``x`` is a finite number inside the inclusive band ``[lo, hi]``."""
    return x is not None and lo <= x <= hi


def main() -> int:
    """Score every kill and prediction, write the record, print the verdict."""
    if not (ARM / "run_config.json").exists():
        raise SystemExit(f"arm bundle not found: {ARM}")
    vc, va = _verdict(CONTROL), _verdict(ARM)
    c1c, c1a = _c1(vc), _c1(va)
    sc, sa = _c1_status(vc), _c1_status(va)
    a3c, a3a = _c3a(vc), _c3a(va)
    pc, pa = _price(vc), _price(va)

    # ---- K-1 : any C1 PASS -> FAIL
    flips = [
        {"cell": k, "control": c1c.get(k), "arm": c1a.get(k),
         "named_ex_ante": k == NAMED_RISK_CELL}
        for k in sorted(set(sc) | set(sa))
        if sc.get(k) == "PASS" and sa.get(k) == "FAIL"
    ]
    k1 = bool(flips)

    # ---- K-2 : any C3a year outside the band
    k2_years = [y for y, v in sorted(a3a.items()) if abs(v) > C3A_BAND_PCT]
    k2 = bool(k2_years)

    # ---- K-3 : the mechanism test on ST_GAS-2024
    st24 = c1a.get("ST_GAS|2024")
    k3 = st24 is None or st24 <= CONTROL_C1["ST_GAS|2024"]

    # ---- K-4 : governance attested?
    gov = (va.get("criteria", {}).get("governance") or {}).get("status")
    k4 = str(gov).upper() in {"UNATTESTED", "NONE", "NULL"} or gov is None

    # ---- K-5 : determination worse in class
    det = va.get("determination")
    reasons = va.get("reasons") or []
    only_c3a = det == "NOT-YET" and all("price_mean" in str(r) for r in reasons)
    k5 = not (det in {"CALIBRATED", "CALIBRATED-WITH-CAVEATS"} or only_c3a)

    passthrough = {
        y: round(100.0 * (pa[y] / pc[y] - 1.0), 4) for y in sorted(pa) if pc.get(y)
    }
    preds = {
        "P1_passthrough_pct": {
            "value": passthrough,
            "band": PRED["P1_passthrough_pct"],
            "held": all(_in(v, *PRED["P1_passthrough_pct"]) for v in passthrough.values()),
        },
        "P2a_all_c3a_in_band": {"value": a3a, "held": not k2},
        "P2b_c3a_2025": {"value": a3a.get(2025), "band": PRED["P2b_c3a_2025_pct"],
                         "held": _in(a3a.get(2025), *PRED["P2b_c3a_2025_pct"])},
        "P2c_c3a_2023": {"value": a3a.get(2023), "band": PRED["P2c_c3a_2023_pct"],
                         "held": _in(a3a.get(2023), *PRED["P2c_c3a_2023_pct"])},
        "P3_st_gas_2024": {"value": st24, "band": PRED["P3_st_gas_2024_twh"],
                           "control": CONTROL_C1["ST_GAS|2024"],
                           "improved_vs_control": (st24 is not None
                                                   and st24 > CONTROL_C1["ST_GAS|2024"]),
                           "held": _in(st24, *PRED["P3_st_gas_2024_twh"])},
        "P4_ct_peaker_2023": {"value": c1a.get("CT_PEAKER|2023"),
                              "band": PRED["P4_ct_peaker_2023_twh"],
                              "exited_band": (c1a.get("CT_PEAKER|2023") is not None
                                              and abs(c1a["CT_PEAKER|2023"]) > C1_BAND_TWH),
                              "held": _in(c1a.get("CT_PEAKER|2023"), *PRED["P4_ct_peaker_2023_twh"])},
        "P5_cc_regular_2024": {"value": c1a.get("CC_REGULAR|2024"),
                               "band": PRED["P5_cc_regular_2024_twh"],
                               "held": _in(c1a.get("CC_REGULAR|2024"), *PRED["P5_cc_regular_2024_twh"])},
        "P6_tail_unchanged": {"control": _c3c(vc), "arm": _c3c(va),
                              "note": "pre-committed as a NON-claim; no tail claim is made from this arm"},
        "P7_c8": {
            "ct_peaker": {"control": CONTROL_C8_CT_PEAKER, "arm": _c8(ARM, "CT_PEAKER")},
            "st_gas": {"control": CONTROL_C8_ST_GAS, "arm": _c8(ARM, "ST_GAS")},
        },
    }

    promote = (not k1) and (not k2) and (not k4) and (not k5) and abs(a3a.get(2025, 99)) <= C3A_BAND_PCT
    rep = {
        "probe": "miso-220 A/B gates - non-steam fossil x1.10 offer lift",
        "prereg": "results/calibration/PREREG-miso220-nonsteam-offer-lift-2026-09-05.md",
        "control": str(CONTROL.relative_to(REPO)),
        "arm": str(ARM.relative_to(REPO)),
        "kills": {
            "K1_c1_pass_to_fail": {"fired": k1, "flips": flips},
            "K2_c3a_out_of_band": {"fired": k2, "years": k2_years, "c3a": a3a},
            "K3_st_gas_2024_not_improved": {"fired": k3, "arm": st24,
                                            "control": CONTROL_C1["ST_GAS|2024"]},
            "K4_governance_unattested": {"fired": k4, "status": gov},
            "K5_determination_worse": {"fired": k5, "determination": det, "reasons": reasons},
        },
        "predictions": preds,
        "c1_control": c1c, "c1_arm": c1a,
        "c3a_control": a3c, "c3a_arm": a3a,
        "promotion_rule": "K1,K2,K4,K5 all silent AND |C3a-2025| <= 10%",
        "verdict": "PROMOTE" if promote else "REJECT",
    }
    OUT.write_text(json.dumps(rep, indent=2))
    fired = [k for k, v in rep["kills"].items() if v["fired"]]
    print(f"  kills fired: {fired or 'NONE'}")
    print(f"  C3a arm: {a3a}")
    print(f"  ST_GAS|2024: {CONTROL_C1['ST_GAS|2024']} -> {st24}")
    print(f"  CT_PEAKER|2023: {CONTROL_C1['CT_PEAKER|2023']} -> {c1a.get('CT_PEAKER|2023')}")
    print(f"  VERDICT: {rep['verdict']}")
    print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
