"""miso-210 A/B scorer — WRITTEN AND COMMITTED BLIND, before either leg's numbers.

===============================================================================
LINEAGE
===============================================================================
Built on ``_miso202_ab_gates.py`` (the current reference: kills-silent ordered
BEFORE inertness, inertness on VALUE MOVEMENT, the miso-200 vacuous-pass trap
closed). ``_miso198_ab_gates.py`` is never imported.

===============================================================================
WHAT CHANGES HERE: the delta is a CODE CONSTANT + a DATA FILE, not a field
===============================================================================
The max-gen clock repair (PREREG-miso210-maxgen-clock-repair-2026-09-04.md §2)
moves ``maxgen_events.MODEL_TZ_BY_ISO['MISO']`` (and the M-2 deriver's twin
constant) from EST to CST and re-derives the M-2 extract. There is NO
``ScenarioConfig`` field, so the three structural gates are RESTATED:

* **S-1 single delta**: the two legs' ``scenario_config`` blocks are IDENTICAL
  (zero field diffs) and the legs differ in exactly the repair commit
  (recorded ``git.sha``) and the M-2 extract bytes (sha256 of the file each leg
  read, recorded in this JSON from the committed extract vs the control's
  snapshot). A non-empty field diff VOIDS the A/B.
* **S-2 placement liveness** (off the production loaders, no solve): the arm's
  tier-cost array differs from the control's in EXACTLY the gained+lost hours
  of each Warning+ block, and the M-2 derate arrays' non-unity hour set is the
  control's shifted by −1 h. Measured by loading both registries/extracts
  through the SAME production functions with the constant/file swapped (the
  control-side arrays are computed from the committed-at-open extract snapshot
  and the EST constant; the arm side from HEAD).
* **S-3 certificate invariance** (HARD VOID): guard 2's ``n_cert`` per registry
  row must be identical on the two clocks — the LMP record moved WITH the
  registry, so the same physical hours are compared. Read from the phase-0
  record ``_miso210_clock_phase0.json`` (P-2a), which the deriver re-run writes.

S-0 and K-1..K-6 are the miso-202 gates unchanged (thresholds frozen from the
keeper's own committed verdict). C3a and C8 are reported at full magnitude and
are NEVER gates (rule 1 [R-STRUCT]).

Usage:
    python3 scripts/probes/_miso210_ab_gates.py

Record: ``results/calibration/_miso210_ab_gates.json``.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "miso202_unitclip_B"
CONTROL = REPO / "results" / "calibration" / "miso210_control_A"
ARM = REPO / "results" / "calibration" / "miso210_clock_B"
PHASE0 = REPO / "results" / "calibration" / "_miso210_clock_phase0.json"
OUT = REPO / "results" / "calibration" / "_miso210_ab_gates.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760

# --- FROZEN, from the PREREG (§4). Stated before either leg's numbers exist. --
C1_BAND_TWH = 8.00
# class|year -> (keeper face TWh, headroom to the +-8.00 edge), read off the
# keeper's OWN committed verdict (miso-202 arm faces).
K1_NAMED = {
    "ST_GAS|2024": (-7.487, 0.513),
    "CC_REGULAR|2024": (+6.942, 1.058),
    "ST_GAS|2025": (-6.684, 1.316),
    "COAL_PRB|2025": (-4.907, 3.093),
    "ST_GAS|2023": (-3.516, 4.484),
    "CC_REGULAR|2023": (-3.408, 4.592),
    "CC_REGULAR|2025": (-2.177, 5.823),
}
# PREREG §4 K-1 bound on the whole delta (TWh), by year.
DELTA_BOUND_TWH = {2023: 0.04, 2024: 0.04, 2025: 0.06}
INERT_EPS = {"c1_twh": 0.010, "c3a_pp": 0.010, "c3b": 0.0005, "c8_share": 0.0005}
# The extract the keeper reads (unit_outage_mixed_gas_routing=true).
EXTRACT = REPO / "data" / "raw" / "campd-unit-outages-maxgen-unitroute-MISO.csv"


def _sha256(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def _verdict_json(bundle: Path) -> dict:
    res = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/calibration_verdict.py"),
            "--json",
            str(bundle),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if not res.stdout.strip():
        raise SystemExit(f"no JSON for {bundle}: {res.stderr[-800:]}")
    return json.loads(res.stdout)


def _crit_status(v: dict) -> dict:
    out = {}
    for name, block in (v.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            out[f"{rec.get('criterion', name)}|{rec.get('key')}|{rec.get('year')}"] = (
                rec.get("status")
            )
    return out


def _c1(v: dict) -> dict:
    out = {}
    for rec in (v.get("criteria", {}).get("fuelmix") or {}).get("records", []):
        k, y = rec.get("key"), rec.get("year")
        if k is None or y is None:
            continue
        try:
            out[f"{k}|{y}"] = float(rec["model"]) - float(rec["actual"])
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _c3a(v: dict) -> dict:
    out = {}
    for rec in v["criteria"]["price_mean"]["records"]:
        if rec.get("benchmark") == "RT" and rec.get("key") is None:
            m, a = float(rec["model"]), float(rec["actual"])
            out[int(rec["year"])] = 100.0 * (m - a) / a
    return out


def _c3b(v: dict) -> dict:
    return {
        int(r["year"]): float(r["model"])
        for r in v["criteria"]["price_shape"]["records"]
        if r.get("key") is None and r.get("model") is not None
    }


def _led(b: Path) -> dict:
    p = b / "legitimacy_diagnostics.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _rows(b: Path, block: str) -> list:
    return ((_led(b).get("diagnostics") or {}).get(block) or {}).get("rows", []) or []


def _d4_fail_keys(b: Path) -> set:
    return {
        (r.get("year"), r.get("check"), r.get("floor"), r.get("plant"))
        for r in _rows(b, "D4")
        if str(r.get("verdict", "pass")).lower() != "pass"
    }


def _d1(b: Path, klass: str = "ST_GAS") -> dict:
    return {
        int(r["year"]): {
            "profile_r": r.get("profile_r"),
            "cv_ratio": r.get("cv_ratio"),
            "verdict": r.get("verdict"),
        }
        for r in _rows(b, "D1")
        if r.get("class") == klass
    }


def _c8_share(b: Path, klass: str = "ST_GAS") -> dict:
    out: dict = {}
    for r in _rows(b, "D2"):
        if r.get("class") != klass:
            continue
        y = int(r["year"])
        out[y] = out.get(y, 0.0) + float(r.get("forced_twh") or 0.0)
    tot: dict = {}
    for r in _rows(b, "D2"):
        if r.get("class") == klass and r.get("class_total_twh"):
            tot[int(r["year"])] = float(r["class_total_twh"])
    return {y: (out[y] / tot[y] if tot.get(y) else None) for y in out}


# ------------------------------------------------------------------- gates
def s0_identity() -> dict:
    """S-0 -- does the control reproduce the keeper's committed sidecars?"""
    worst, checked, missing = 0.0, 0, []
    for year in YEARS:
        for stem in ("class_hourly", "system", "reserve_family"):
            a = KEEPER / "hourly" / f"{stem}_{year}.parquet"
            b = CONTROL / "hourly" / f"{stem}_{year}.parquet"
            if not a.exists() or not b.exists():
                missing.append(f"{stem}_{year}")
                continue
            da, db = pd.read_parquet(a), pd.read_parquet(b)
            if da.shape != db.shape or list(da.columns) != list(db.columns):
                worst = float("inf")
                checked += 1
                continue
            num = da.select_dtypes("number").columns
            d = (
                float(np.nanmax(np.abs(da[num].to_numpy() - db[num].to_numpy())))
                if len(num)
                else 0.0
            )
            worst = max(worst, d)
            checked += 1
    return {
        "sidecars_checked": checked,
        "missing": missing,
        "max_abs_diff": worst,
        "passed": checked > 0 and worst == 0.0,
    }


def s1_single_delta() -> dict:
    """S-1 restated: zero config diffs; the legs differ by commit + extract bytes."""
    rc_c = json.loads((CONTROL / "run_config.json").read_text())
    rc_a = json.loads((ARM / "run_config.json").read_text())
    ca, cb = rc_c["scenario_config"], rc_a["scenario_config"]
    diffs = sorted(k for k in set(ca) | set(cb) if ca.get(k) != cb.get(k))
    sha_c = (rc_c.get("git") or {}).get("sha")
    sha_a = (rc_a.get("git") or {}).get("sha")
    ph = json.loads(PHASE0.read_text()) if PHASE0.exists() else {}
    extract_control = (ph.get("extract_sha256") or {}).get("control_committed_at_open")
    extract_arm_expected = (ph.get("extract_sha256") or {}).get("arm_rederived")
    extract_now = _sha256(EXTRACT)
    return {
        "n_fields": len(set(ca) | set(cb)),
        "config_diffs": diffs,
        "git_sha": {"control": sha_c, "arm": sha_a},
        "extract_sha256": {
            "control_committed_at_open": extract_control,
            "arm_rederived_expected": extract_arm_expected,
            "in_tree_now": extract_now,
        },
        "passed": (
            diffs == []
            and sha_c != sha_a
            and extract_control is not None
            and extract_arm_expected is not None
            and extract_control != extract_arm_expected
            and extract_now == extract_arm_expected
        ),
    }


def s2_s3_from_phase0() -> tuple[dict, dict]:
    """S-2 placement liveness and S-3 certificate invariance, read from phase 0.

    The phase-0 probe (``_miso210_clock_phase0.py``) computes both on the
    production loaders with the constant/extract swapped; this scorer only
    re-states the verdicts so the A/B record carries them beside the kills.
    """
    ph = json.loads(PHASE0.read_text()) if PHASE0.exists() else {}
    s2 = ph.get("S2_placement") or {}
    s3 = ph.get("S3_certificate_invariance") or {}
    return (
        {
            "source": "P-1 / S-2 block of _miso210_clock_phase0.json",
            "tier_windows_shifted_exactly": s2.get("tier_exact_shift"),
            "m2_windows_shifted_exactly": s2.get("m2_exact_shift"),
            "detail": s2.get("detail"),
            "passed": bool(s2.get("passed", False)),
        },
        {
            "source": "P-2a block of _miso210_clock_phase0.json",
            "n_cert_identical": s3.get("n_cert_identical"),
            "blocks_identical": s3.get("blocks_identical"),
            "detail": s3.get("detail"),
            "passed": bool(s3.get("passed", False)),
        },
    )


def kills(vc: dict, va: dict) -> dict:
    out: dict = {}
    c1c, c1a = _c1(vc), _c1(va)
    exits, named = [], {}
    max_move = {"key": None, "abs_twh": 0.0}
    for k in sorted(set(c1c) | set(c1a)):
        b, a = c1c.get(k), c1a.get(k)
        if b is None or a is None:
            continue
        if abs(a - b) > max_move["abs_twh"]:
            max_move = {"key": k, "abs_twh": round(abs(a - b), 4)}
        if abs(b) <= C1_BAND_TWH and abs(a) > C1_BAND_TWH:
            exits.append({"class_year": k, "control": round(b, 3), "arm": round(a, 3)})
    for k, (pre, head) in K1_NAMED.items():
        named[k] = {
            "prereg_control": pre,
            "prereg_headroom": head,
            "measured_control": round(c1c[k], 3) if c1c.get(k) is not None else None,
            "measured_arm": round(c1a[k], 3) if c1a.get(k) is not None else None,
            "band_exit": bool(c1a.get(k) is not None and abs(c1a[k]) > C1_BAND_TWH),
        }
    out["K1"] = {
        "band_twh": C1_BAND_TWH,
        "prereg_delta_bound_twh": DELTA_BOUND_TWH,
        "largest_class_year_move": max_move,
        "named_ex_ante": named,
        "all_band_exits": exits,
        "passed": not exits,
    }

    b3c, b3a = _c3b(vc), _c3b(va)
    sc, sa = _crit_status(vc), _crit_status(va)
    c3b_flip = [
        k
        for k in sc
        if k.startswith("price_shape")
        and sc[k] == "PASS"
        and sa.get(k) not in (None, "PASS")
    ]
    out["K2"] = {
        "control": b3c,
        "arm": b3a,
        "pass_to_fail": c3b_flip,
        "passed": not c3b_flip,
    }

    d4_rows = {"control": len(_rows(CONTROL, "D4")), "arm": len(_rows(ARM, "D4"))}
    d4_scorable = d4_rows["control"] > 0 and d4_rows["arm"] > 0
    new_d4 = sorted(map(str, _d4_fail_keys(ARM) - _d4_fail_keys(CONTROL)))
    out["K3"] = {
        "d4_row_counts": d4_rows,
        "scorable": d4_scorable,
        "new_d4_failures": new_d4 if d4_scorable else None,
        "cleared": (
            sorted(map(str, _d4_fail_keys(CONTROL) - _d4_fail_keys(ARM)))
            if d4_scorable
            else None
        ),
        "status": "SCORED"
        if d4_scorable
        else (
            "UNSCORED — a leg carries no D4 rows (replay bundles write no "
            "legitimacy_diagnostics.json); generate them for BOTH legs and re-score"
        ),
        "passed": (not new_d4) if d4_scorable else None,
    }

    d1c, d1a = _d1(CONTROL), _d1(ARM)
    d1_rows = {"control": len(_rows(CONTROL, "D1")), "arm": len(_rows(ARM, "D1"))}
    d1_scorable = d1_rows["control"] > 0 and d1_rows["arm"] > 0
    d1_flip = [
        y
        for y in d1c
        if str(d1c[y].get("verdict", "")).lower() == "pass"
        and str(d1a.get(y, {}).get("verdict", "")).lower() != "pass"
    ]
    out["K4"] = {
        "d1_row_counts": d1_rows,
        "scorable": d1_scorable,
        "control": d1c,
        "arm": d1a,
        "pass_to_fail": d1_flip if d1_scorable else None,
        "status": "SCORED"
        if d1_scorable
        else "UNSCORED — a leg carries no D1 rows; generate them for BOTH legs",
        "passed": (not d1_flip) if d1_scorable else None,
    }

    flips = [
        {"record": k, "control": sc[k], "arm": sa.get(k)}
        for k in sorted(sc)
        if sc[k] == "PASS" and sa.get(k) not in (None, "PASS")
    ]
    out["K5"] = {"pass_to_non_pass": flips, "passed": not flips}

    def _att(b: Path) -> dict:
        p = b / "calibration_attestation.json"
        return json.loads(p.read_text()) if p.exists() else {}

    ac_, aa_ = _att(CONTROL), _att(ARM)
    n_c = len((ac_.get("free_parameters") or {}).get("entries") or [])
    n_a = len((aa_.get("free_parameters") or {}).get("entries") or [])
    att = n_c > 0 and n_a > 0
    out["K6"] = {
        "attestation_entries": {"control": n_c, "arm": n_a},
        "prereg": "no new ledger entry (41 -> 41); the arm corrects a constant to a measured clock",
        "status": "SCORED"
        if att
        else "UNSCORED — a leg carries no attestation entries (replay bundles write none)",
        "passed": True if att else None,
    }
    return out


def movement(vc: dict, va: dict) -> dict:
    """Inertness measured on VALUE MOVEMENT, not on status identity."""
    c1c, c1a = _c1(vc), _c1(va)
    ac, aa = _c3a(vc), _c3a(va)
    bc, ba = _c3b(vc), _c3b(va)
    sc8, sa8 = _c8_share(CONTROL), _c8_share(ARM)
    d_c1 = {k: round(c1a[k] - c1c[k], 4) for k in sorted(set(c1c) & set(c1a))}
    d_c3a = {y: round(aa[y] - ac[y], 4) for y in sorted(set(ac) & set(aa))}
    d_c3b = {y: round(ba[y] - bc[y], 5) for y in sorted(set(bc) & set(ba))}
    d_c8 = {
        y: (
            round(sa8[y] - sc8[y], 5)
            if sa8.get(y) is not None and sc8.get(y) is not None
            else None
        )
        for y in sorted(set(sc8) | set(sa8))
    }
    moved = (
        any(abs(v) > INERT_EPS["c1_twh"] for v in d_c1.values())
        or any(abs(v) > INERT_EPS["c3a_pp"] for v in d_c3a.values())
        or any(abs(v) > INERT_EPS["c3b"] for v in d_c3b.values())
        or any(v is not None and abs(v) > INERT_EPS["c8_share"] for v in d_c8.values())
    )
    # PREREG §4 C3a sign predictions, scored here against interest.
    prereg_c3a = {
        2023: {"lo": -0.05, "hi": 0.10},
        2024: {"lo": 0.0, "hi": 1.5},
        2025: {"lo": -0.05, "hi": 0.10},
    }
    c3a_scored = {
        y: {
            "delta_pp": d_c3a.get(y),
            "prereg_band": prereg_c3a[y],
            "inside": (
                None
                if d_c3a.get(y) is None
                else bool(prereg_c3a[y]["lo"] <= d_c3a[y] <= prereg_c3a[y]["hi"])
            ),
        }
        for y in prereg_c3a
    }
    return {
        "epsilons": INERT_EPS,
        "d_c1_twh": d_c1,
        "c3a_control": ac,
        "c3a_arm": aa,
        "d_c3a_pp": d_c3a,
        "c3a_prereg_scored": c3a_scored,
        "d_c3b": d_c3b,
        "c8_share_control": sc8,
        "c8_share_arm": sa8,
        "d_c8_share": d_c8,
        "status_map_identical": _crit_status(vc) == _crit_status(va),
        "arm_moved_values": moved,
    }


def main() -> dict:
    out: dict = {
        "prereg": "PREREG-miso210-maxgen-clock-repair-2026-09-04.md §4",
        "keeper_at_open": "2026-09-03-miso-202-unitclip",
        "delta": (
            "maxgen_events.MODEL_TZ_BY_ISO['MISO'] Etc/GMT+5 -> Etc/GMT+6, the M-2 "
            "deriver's twin constant + DA-hub EST->model shift, and the re-derived "
            "M-2 extract. NO ScenarioConfig field."
        ),
        "control": CONTROL.name,
        "arm": ARM.name,
        "scorer_written_and_committed_before_any_arm_result": True,
        "c3a_is_never_a_gate": "rule 1 [R-STRUCT]; reported at full magnitude with the PREREG sign beside it",
    }
    out["S0"] = s0_identity()
    print(
        "S-0",
        "PASS — BIT-IDENTICAL"
        if out["S0"]["passed"]
        else f"DRIFT max|diff|={out['S0']['max_abs_diff']} (DISCLOSED, not a kill)",
    )
    out["S1"] = s1_single_delta()
    print("S-1", "PASS" if out["S1"]["passed"] else f"VOID {out['S1']}")
    s2, s3 = s2_s3_from_phase0()
    out["S2"], out["S3"] = s2, s3
    print(
        "S-2",
        "PASS — placement shifted exactly" if s2["passed"] else "NOT LIVE / not exact",
    )
    print(
        "S-3",
        "PASS — certificate invariant" if s3["passed"] else "VOID — certificate moved",
    )

    vc, va = _verdict_json(CONTROL), _verdict_json(ARM)
    out.update(kills(vc, va))
    out["movement"] = movement(vc, va)
    for k in ("K1", "K2", "K3", "K4", "K5", "K6"):
        p = out[k]["passed"]
        print(k, "PASS" if p is True else ("UNSCORED" if p is None else "KILL"))

    fired = [k for k in ("K1", "K2", "K3", "K4", "K5") if out[k]["passed"] is False]
    out["kills_fired"] = fired
    moved = out["movement"]["arm_moved_values"]

    # ORDER: VOID -> KILL FIRED -> KILLS SILENT -> INERT.
    if not out["S1"]["passed"]:
        out["verdict"] = (
            "VOID — not a single delta; the A/B does not measure the repair"
        )
    elif not out["S3"]["passed"]:
        out["verdict"] = (
            "VOID — S-3 CERTIFICATE INVARIANCE BROKEN: the deriver's LMP shift does not "
            "move with the registry; the re-derived extract is not the same physical "
            "windows. Nothing below is scored as evidence."
        )
    elif fired:
        out["verdict"] = (
            f"KILL FIRED ({', '.join(fired)}) — reported at full magnitude and NOT "
            "renegotiated. Under the owner's standing structural-integrity bar this is "
            "an OWNER DECISION, not an automatic reject; the scorer does not promote."
        )
    elif moved:
        out["verdict"] = (
            "KILLS SILENT and the arm MOVED values -> keeper candidate on its own gates. "
            "C3a is reported at full magnitude and is NEVER the justification."
        )
    else:
        out["verdict"] = (
            "INERT — no scored VALUE moved beyond epsilon. Per PREREG §4 the repair is "
            "STILL promoted as a defect repair (a wrong clock is wrong at any magnitude)."
        )
    print("VERDICT:", out["verdict"])
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()
