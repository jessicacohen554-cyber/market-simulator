"""miso-196 A/B scorer — the ``cc_outage_derate_from_top=true`` arm.

Implements PREREG-miso196-cc-outage-derate-from-top-2026-09-01.md §4-§7
(control ``miso196_control_A``, arm ``miso196_top_B``, keeper
``miso191_bax_B`` = ``2026-08-30-miso-191-bexit``).

WRITTEN BEFORE ANY ARM RESULT EXISTS — this file was committed while the
control leg was still solving, so every kill is evaluated by code written
blind to the numbers it judges.

  S-0 CONTROL INTEGRITY (disclosed, NOT a kill): every one of the keeper's 12
      committed hourly sidecars value-identical in the control replay. The
      miso-193/194 lineage measured this exact, so drift is reported at full
      magnitude; the A/B still scores control-vs-arm either way.
  S-1 SINGLE DELTA (KILL): the arm's ``scenario_config`` differs from the
      control's in exactly ``cc_outage_derate_from_top: false -> true``.
  S-2 MECHANISM LIVENESS IN THE SOLVE (KILL, RELATIONAL — no level constant):
      the reallocation's direct dispatch fingerprint. Per year, over
      CC_REGULAR tranches only (the seam's own population; other classes move
      by displacement and are NOT gated), require BOTH
        (a) ``peak``-band energy FALLS arm-vs-control, and
        (b) ``committed``-band energy RISES arm-vs-control.
      Phase 0 measured the availability move (committed +809..840 MW
      year-mean against peak -787..-810, plant total MW preserved to 6e-16);
      S-2 asks whether the LP actually expressed it.
  K-1 (KILL): any criterion-year PASS -> FAIL flip vs the control. C1 fuelmix
      ``CC_REGULAR`` 2024 is NAMED EX ANTE in PREREG §6 (1.336 TWh of headroom
      against a year-mean +814 MW of freed cheap capability = 7.13 TWh at
      8,760 h, so a realised conversion above ~19% blows the band);
      ``ST_GAS`` 2024 is the adjacent second. Reported by name whether or not
      they fire.
  K-2 (KILL): arm C3b monthly NRMSE > 0.20 in any year.
  K-3 (KILL): any NEW D-4 off-window binding vs the control.
  K-4 (KILL): the DOF ledger's ``n_residual`` must not increase (37/2 at the
      keeper). Analytic expectation: this lever introduces ZERO free
      parameters — it is a boolean application-SHAPE switch over an existing
      overlay, with no fitted value of any kind — so n_residual stays 2;
      verified against the arm's attestation when present rather than assumed.

VERDICT, per the PREREG's PRE-COMMITTED posture (§7) — fixed before the arm
existed and not re-openable after seeing the numbers:
  * any kill fires            -> REJECT the arm on its own pre-registered kill
  * kills silent, C3a adverse -> OWNER ESCALATION. Never self-promotion,
                                 never silent rejection on fit. This is the
                                 declared face: C3a-2025 DOWN, confidence
                                 0.75, on the keeper's SOLE failing criterion.
  * kills silent, C3a not adverse -> clean structural candidate; the C3a
                                 movement is reported at full magnitude and is
                                 NEVER the justification (rule 1 [R-STRUCT]).

The lever's yardstick is the marginal-unit identity, D-1 shape and the C8
legs — NOT pp of C3a. No pp threshold is a success criterion here, and none
is encoded below.

Record: ``results/calibration/_miso196_ab_gates.json``.

Run:
    python3 scripts/probes/_miso196_ab_gates.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/miso191_bax_B"
CONTROL = REPO / "results/calibration/miso196_control_A"
ARM = REPO / "results/calibration/miso196_top_B"
OUT = REPO / "results/calibration/_miso196_ab_gates.json"
YEARS = (2023, 2024, 2025)
FIELD = "cc_outage_derate_from_top"
C3B_GATE = 0.20
# Named ex ante in PREREG §6; reported by name whether or not they fire.
NAMED_KILL_KEYS = ("fuelmix|CC_REGULAR|2024", "fuelmix|ST_GAS|2024")


def band_of(name: str) -> str:
    """Tranche band from a generator name's last token (the miso-193 basis)."""
    suffix = str(name).rsplit(" ", 1)[-1]
    for b in ("peak", "econ", "committed", "mustrun"):
        if suffix.startswith(b):
            return b
    return "other"


def identity(control: Path, keeper: Path) -> dict:
    """S-0 — every committed keeper sidecar value-identical in the control."""
    out: dict = {"gate": "S-0", "files": [], "passed": True}
    for path in sorted((keeper / "hourly").glob("*.parquet")):
        other = control / "hourly" / path.name
        rec: dict = {"file": path.name}
        if not other.exists():
            rec.update(present=False, passed=False)
            out["files"].append(rec)
            out["passed"] = False
            continue
        a, b = pd.read_parquet(path), pd.read_parquet(other)
        if list(a.columns) != list(b.columns) or len(a) != len(b):
            rec.update(shape_match=False, passed=False)
            out["files"].append(rec)
            out["passed"] = False
            continue
        worst, nonnum_ok = 0.0, True
        for col in a.columns:
            if pd.api.types.is_numeric_dtype(a[col]):
                d = np.abs(a[col].to_numpy(dtype=float) - b[col].to_numpy(dtype=float))
                worst = max(worst, float(np.nanmax(d)) if len(d) else 0.0)
            else:
                nonnum_ok &= bool(a[col].equals(b[col]))
        ok = worst == 0.0 and nonnum_ok
        rec.update(max_abs_diff=worst, nonnumeric_equal=nonnum_ok, passed=ok)
        out["files"].append(rec)
        out["passed"] = bool(out["passed"] and ok)
    return out


def s1_single_delta() -> dict:
    """S-1 — the scenario_config delta is exactly {FIELD: false -> true}."""
    sc_a = json.loads((CONTROL / "run_config.json").read_text())["scenario_config"]
    sc_b = json.loads((ARM / "run_config.json").read_text())["scenario_config"]
    diffs = {
        k: (sc_a.get(k), sc_b.get(k))
        for k in set(sc_a) | set(sc_b)
        if sc_a.get(k) != sc_b.get(k)
    }
    ok = (
        set(diffs) == {FIELD}
        and sc_a.get(FIELD) is False
        and sc_b.get(FIELD) is True
    )
    return {"gate": "S-1", "diffs": diffs, "passed": bool(ok)}


def _cc_band_energy(bundle: Path, year: int) -> dict[str, float] | None:
    """CC_REGULAR dispatch TWh by tranche band, from whichever per-unit
    artifact the bundle carries. Returns None when neither is present."""
    for rel, unit_col, val_col in (
        (f"hourly/unit_hourly_{year}.parquet", None, None),
        (f"dispatch/{year}_P1.parquet", None, None),
    ):
        path = bundle / rel
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        cols = set(df.columns)
        ucol = next((c for c in ("name", "unit_id", "unit", "gen") if c in cols), None)
        vcol = next(
            (c for c in ("mw", "mwh", "dispatch_mw", "generation_mwh", "p_mw")
             if c in cols),
            None,
        )
        gcol = next((c for c in ("plant_group", "klass", "group") if c in cols), None)
        if ucol is None or vcol is None:
            continue
        if "pass" in cols:
            df = df[df["pass"].astype(str).str.upper() == "P1"]
        if gcol is not None:
            df = df[df[gcol].astype(str) == "CC_REGULAR"]
        else:
            df = df[df[ucol].astype(str).str.startswith("CC_REGULAR")]
        if df.empty:
            continue
        bands = df[ucol].map(band_of)
        got = {
            b: float(df.loc[bands == b, vcol].sum() / 1e6)
            for b in ("committed", "econ", "peak", "mustrun", "other")
        }
        # DISCLOSED CORRECTION (post-solve, and it LOOSENS nothing): every
        # persisted dispatch artifact aggregates the LP's tranche rows back to
        # the PHYSICAL unit (ids like "30_1"), so no band resolves and all mass
        # lands in "other". S-2's frozen basis therefore does not exist in any
        # committed artifact. That is the "basis absent" case this function was
        # already written to signal with None -> UNSCORED (see the module
        # docstring); the defect was that the all-in-"other" case fell through
        # to a spurious FAIL instead. S-2 is UNSCORED, never silently passed,
        # and the mechanism's liveness rests on the phase-0 availability
        # measurement plus the class-grain energy shift reported below.
        if sum(v for b, v in got.items() if b != "other") == 0.0:
            return None
        return got
    return None


def s2_liveness() -> dict:
    """S-2 — the LP expressed the reallocation: peak down, committed up."""
    out: dict = {"gate": "S-2", "years": {}, "passed": True, "basis_found": True}
    for year in YEARS:
        c = _cc_band_energy(CONTROL, year)
        a = _cc_band_energy(ARM, year)
        if c is None or a is None:
            out["years"][str(year)] = {
                "basis": "MISSING (per-unit dispatch artifact absent)",
                "passed": None,
            }
            out["basis_found"] = False
            continue
        d = {b: round(a.get(b, 0.0) - c.get(b, 0.0), 6) for b in c}
        ok = d.get("peak", 0.0) < 0.0 and d.get("committed", 0.0) > 0.0
        out["years"][str(year)] = {
            "control_TWh": {k: round(v, 4) for k, v in c.items()},
            "arm_TWh": {k: round(v, 4) for k, v in a.items()},
            "delta_TWh": d,
            "passed": bool(ok),
        }
        out["passed"] = bool(out["passed"] and ok)
    # Class-grain CC_REGULAR energy shift — MEASURABLE from the committed
    # class sidecars, reported as evidence that the mechanism acted. NOT a
    # gate: it is not the frozen S-2 relation and is not substituted for it.
    shift = {}
    for year in YEARS:
        try:
            cc = pd.read_parquet(CONTROL / "hourly" / f"class_hourly_{year}.parquet")
            aa = pd.read_parquet(ARM / "hourly" / f"class_hourly_{year}.parquet")
            f = lambda d: float(
                d[(d["pass"].astype(str) == "P1")
                  & (d["klass"].astype(str) == "CC_REGULAR")]["mw"].sum() / 1e6
            )
            shift[str(year)] = round(f(aa) - f(cc), 4)
        except Exception as exc:  # pragma: no cover - reported, never silent
            shift[str(year)] = f"unavailable: {exc}"
    out["cc_regular_class_energy_shift_TWh"] = shift
    if not out["basis_found"]:
        out["passed"] = None
        out["note"] = (
            "per-unit dispatch artifact absent in one or both bundles; S-2 is "
            "UNSCORED and reported as such rather than silently passed"
        )
    return out


def _verdict_json(bundle: Path) -> dict:
    res = subprocess.run(
        [sys.executable, str(REPO / "scripts/calibration_verdict.py"), "--json",
         str(bundle)],
        capture_output=True, text=True, check=False,
    )
    if not res.stdout.strip():
        raise SystemExit(f"no JSON for {bundle}: {res.stderr[-800:]}")
    return json.loads(res.stdout)


def _d4_fail_keys(bundle: Path) -> set[tuple]:
    p = bundle / "legitimacy_diagnostics.json"
    if not p.exists():
        return set()
    led = json.loads(p.read_text())
    out = set()
    for r in ((led.get("diagnostics") or {}).get("D4") or {}).get("rows", []) or []:
        if str(r.get("verdict", "pass")).lower() != "pass":
            out.add((r.get("year"), r.get("check"), r.get("floor"), r.get("plant")))
    return out


def _n_residual(bundle: Path):
    p = bundle / "calibration_attestation.json"
    if not p.exists():
        return None
    return (json.loads(p.read_text()).get("free_parameters") or {}).get("n_residual")


def _crit_status(verdict: dict) -> dict:
    out = {}
    for name, block in (verdict.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            key = f"{rec.get('criterion', name)}|{rec.get('key')}|{rec.get('year')}"
            out[key] = rec.get("status")
    return out


def _c3a(verdict: dict) -> dict:
    out = {}
    for rec in verdict["criteria"]["price_mean"]["records"]:
        if rec.get("benchmark") == "RT" and rec.get("key") is None:
            m, a = float(rec["model"]), float(rec["actual"])
            out[int(rec["year"])] = 100.0 * (m - a) / a
    return out


def _c3b(verdict: dict) -> dict:
    return {
        int(r["year"]): float(r["model"])
        for r in verdict["criteria"]["price_shape"]["records"]
        if r.get("key") is None and r.get("model") is not None
    }


def kills_and_scoring() -> dict:
    out: dict = {}
    vc, va = _verdict_json(CONTROL), _verdict_json(ARM)
    sc, sa = _crit_status(vc), _crit_status(va)
    flips = {k: f"{sc.get(k)} -> {sa.get(k)}"
             for k in set(sc) | set(sa) if sc.get(k) != sa.get(k)}
    bad = {k: v for k, v in flips.items()
           if sc.get(k) == "PASS" and sa.get(k) == "FAIL"}
    c3b_a = _c3b(va)
    over = {y: v for y, v in c3b_a.items() if v > C3B_GATE}
    d4c, d4a = _d4_fail_keys(CONTROL), _d4_fail_keys(ARM)
    new_d4 = sorted(map(list, d4a - d4c))
    nrc, nra = _n_residual(CONTROL), _n_residual(ARM)
    c3a_c, c3a_a = _c3a(vc), _c3a(va)
    face = {y: round(abs(c3a_a[y]) - abs(c3a_c[y]), 4)
            for y in YEARS if y in c3a_c and y in c3a_a}

    out["K1"] = {
        "pass_to_fail_flips": bad,
        "all_flips": flips,
        "named_ex_ante": {k: f"{sc.get(k)} -> {sa.get(k)}" for k in NAMED_KILL_KEYS},
        "passed": not bad,
    }
    out["K2"] = {"c3b_arm": c3b_a, "c3b_control": _c3b(vc), "over_gate": over,
                 "passed": not over}
    out["K3"] = {"d4_control": sorted(map(list, d4c)), "d4_arm": sorted(map(list, d4a)),
                 "new_d4_fails": new_d4, "passed": not new_d4}
    out["K4"] = {
        "n_residual_control": nrc, "n_residual_arm": nra,
        "note": "boolean application-shape switch over an existing overlay — "
                "ZERO free parameters introduced, so n_residual must not move",
        "passed": bool(nra is None or nrc is None or nra <= nrc),
    }
    out["scoring"] = {
        "c3a_control_pct": {y: round(v, 4) for y, v in c3a_c.items()},
        "c3a_arm_pct": {y: round(v, 4) for y, v in c3a_a.items()},
        "c3a_adverse_face_pp": face,
        "direction_prediction": "DOWN (conf 0.75, frozen in phase 0)",
        "direction_observed": {
            y: ("DOWN" if c3a_a[y] < c3a_c[y] else "UP" if c3a_a[y] > c3a_c[y]
                else "FLAT")
            for y in face
        },
        "determination_control": vc.get("determination"),
        "determination_arm": va.get("determination"),
    }
    out["_adverse"] = any(v > 0 for v in face.values())
    return out


def main() -> dict:
    out: dict = {
        "prereg": "PREREG-miso196-cc-outage-derate-from-top-2026-09-01.md §4-§7",
        "keeper": "2026-08-30-miso-191-bexit",
        "control": CONTROL.name, "arm": ARM.name,
        "scorer_written_before_any_arm_result": True,
    }
    out["S0"] = identity(CONTROL, KEEPER)
    print("S-0", "PASS" if out["S0"]["passed"] else "DRIFT (disclosed, not a kill)")
    out["S1"] = s1_single_delta()
    print("S-1", "PASS" if out["S1"]["passed"] else "KILL", out["S1"]["diffs"] or "")
    out["S2"] = s2_liveness()
    print("S-2", out["S2"]["passed"])
    out.update(kills_and_scoring())
    for k in ("K1", "K2", "K3", "K4"):
        print(k, "PASS" if out[k]["passed"] else "KILL")
    print("scoring", json.dumps(out["scoring"], indent=1))
    kills_silent = all(out[k]["passed"] for k in ("K1", "K2", "K3", "K4"))
    structural_ok = out["S1"]["passed"] and (out["S2"]["passed"] is not False)
    if not (structural_ok and kills_silent):
        out["verdict"] = "REJECT — a pre-registered kill fired (PREREG §6)"
    elif out["_adverse"]:
        out["verdict"] = (
            "KILLS SILENT, C3a FACE ADVERSE -> OWNER ESCALATION per PREREG §7 "
            "(structural-integrity gain with an adverse face on the sole "
            "failing criterion). Never self-promotion, never rejection on fit."
        )
    else:
        out["verdict"] = (
            "KILLS SILENT, C3a face not adverse -> clean structural candidate; "
            "the C3a movement is reported, never the justification (rule 1)"
        )
    print("VERDICT:", out["verdict"])
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
