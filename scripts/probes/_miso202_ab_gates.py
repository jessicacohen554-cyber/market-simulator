"""miso-202 A/B scorer — WRITTEN AND COMMITTED BLIND, before either leg's numbers.

===============================================================================
LINEAGE
===============================================================================
Built on ``_miso201_ab_gates.py``, the current reference (it added the
vacuous-pass refusal). ``_miso198_ab_gates.py`` is left unrepaired on purpose and
is **never imported**; both of its defects stay fixed here, and the fixes are
restated before any result exists:

1. **ORDERING.** VOID -> KILL FIRED -> **KILLS SILENT** -> INERT. INERT is
   reachable ONLY when the arm moved nothing measurable.
2. **WHAT "IDENTICAL" MEANS.** Inertness is measured on **VALUE MOVEMENT** (the
   numeric C1 / C3a / C3b / C8 deltas against explicit epsilons), never on
   criterion-status identity. The status map is carried as a *report* only.

===============================================================================
WHAT THIS SCORER ADDS: S-3, THE MONOTONICITY VOID
===============================================================================
This lever has a soundness line the previous ones did not, and it is checkable
WITHOUT a solve. The per-unit clip can only ever remove **less** capacity than
the production accumulator, never more -- it is a ceiling on a sum, applied to
one unit at a time. So on every bin, every hour and every layer the arm's
availability must be **>= the control's**. A single hour in which the arm removes
MORE is a bug in the mechanism, not a result, and it **VOIDS** the A/B. S-3 is
run off the production loaders with the flag off and on, so it is decided before
either leg's dispatch matters.

===============================================================================
THE GATES, from PREREG-miso202-boundary-day-double-count-2026-09-03.md §4
===============================================================================
* **S-0** control integrity: BIT-IDENTICAL to the keeper's committed sidecars,
  ``max_abs_diff`` 0.0. Drift is DISCLOSED, never silently absorbed, not a kill.
* **S-1** single delta: exactly one ``ScenarioConfig`` field differs. A failure
  VOIDS the A/B -- it did not measure the lever.
* **S-2** liveness: at least one bin's availability strictly rises, in EACH of
  the std5d and layup layers. **Liveness only -- never a target.**
* **S-3** monotonicity: arm availability >= control availability everywhere.
  **A HARD VOID.**
* **K-1** C1 band, +-8.00 TWh, arithmetic frozen from the keeper's own verdict
  BEFORE the arm existed. **THE NAMED RISK is CC_REGULAR-2024 +6.931** (1.069
  headroom, expected to move UP/adverse: the model already over-produces CC there
  and the arm restores CC availability). The whole-arm capability bound is
  0.091 / 0.078 / 0.103 TWh, below every headroom in the table including the
  0.512 TWh at ST_GAS-2024.
* **K-2** C3b no PASS->FAIL. **K-3** D-4: zero NEW off-window binding.
  **K-4** D-1 shape: no PASS->FAIL. **K-5** zero PASS->non-PASS anywhere.
* **K-6** DOF/attestation. **THE miso-200 VACUOUS-PASS TRAP STAYS CLOSED:**
  K-3/K-4/K-6 are REFUSED (reported UNSCORED, never PASS) unless BOTH legs carry
  non-empty D1/D4 row blocks and attestation entries.

**C3a is reported at full magnitude and is NEVER a gate** (rule 1 ``[R-STRUCT]``).
No branch below reads it. Phase-0 N-4 measured, before this arm existed, that only
1.4 % / 0.0 % / 1.4 % of the restored capability lands in the keeper's own top-1 %
price hours -- so C3a is expected to barely move, and if it moves the right way
that is NOT evidence for the mechanism. The same holds for C3c, the ISO's single
ledgered caveat.

**C8 is a NAMED RISK, not a gate.** The lay-up layer feeds the must-run floor
mask and the clip REDUCES the laid-up share, which RAISES the floor's clip basis.
Reported at full magnitude whichever way it moves.

===============================================================================
STANDING CONTEXT, recorded BEFORE any result, and NOT a licence
===============================================================================
The owner's 2026-09-02 re-scoping -- *"if structural integrity improves but gates
regress that may still be a keeper"* -- is carried forward as context. It does NOT
silence a kill and changes no threshold above. A fired kill is reported as fired,
at full magnitude, and the scorer NEVER promotes on that branch.

Usage:
    python3 scripts/probes/_miso202_ab_gates.py

Record: ``results/calibration/_miso202_ab_gates.json``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "miso201_stbasis_B"
CONTROL = REPO / "results" / "calibration" / "miso202_control_A"
ARM = REPO / "results" / "calibration" / "miso202_unitclip_B"
OUT = REPO / "results" / "calibration" / "_miso202_ab_gates.json"
FIELD = "unit_outage_per_unit_clip"
YEARS = (2023, 2024, 2025)

# --- FROZEN, from the PREREG. Stated before either leg's numbers exist. ------
C1_BAND_TWH = 8.00
# class|year -> (keeper face TWh, headroom to the +-8.00 edge). Read off the
# keeper's OWN committed verdict before the arm existed; PREREG section 4.
K1_NAMED = {
    "ST_GAS|2024": (-7.488, 0.512),      # tightest cell; expected UP (favorable)
    "CC_REGULAR|2024": (+6.931, 1.069),  # THE NAMED RISK — expected UP, adverse
    "ST_GAS|2025": (-6.681, 1.319),
    "COAL_PRB|2025": (-4.904, 3.096),    # named adverse (displacement)
    "ST_GAS|2023": (-3.512, 4.488),
    "CC_REGULAR|2023": (-3.434, 4.566),
    "CC_REGULAR|2025": (-2.194, 5.806),
}
# Rigorous bound on the capability the arm can restore (phase-0 N-3), by year.
CAPABILITY_BOUND_TWH = {2023: 0.091, 2024: 0.078, 2025: 0.103}
INERT_EPS = {"c1_twh": 0.010, "c3a_pp": 0.010, "c3b": 0.0005, "c8_share": 0.0005}

# The keeper recipe every loader call below is made under, so S-2 and S-3
# measure the lever against the keeper's own configuration and nothing else.
LOADER_KW = dict(
    cc_steam_part_reclass=False,
    cc_nameplate_basis=False,
    fleet_status_scope=True,
    st_capacity_basis=True,
)


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


# ------------------------------------------------------------------- loaders
def _layer_arrays(flag: bool) -> dict:
    """Return ``{(layer, year, bin): availability array}`` under the flag.

    Read straight off the production loaders, so S-2 liveness and S-3
    monotonicity are decided by the mechanism's own output rather than inferred
    from a downstream number something else could have moved. The maxgen layer is
    deliberately absent: phase-0 N-5 measured ZERO same-unit overlaps in it, so
    it is out of scope by measurement and the flag must not reach it.
    """
    from market_sim.data.outages import (
        BINS_CSV_DEFAULT,
        unit_layup_removed_fractions,
        unit_outage_derate_factors,
        unit_outage_short_derate_factors,
    )

    out: dict = {}
    for year in YEARS:
        std = unit_outage_derate_factors(
            year,
            8760,
            BINS_CSV_DEFAULT,
            iso="MISO",
            mixed_gas_routing=True,
            per_unit_crosswalk=False,
            per_unit_clip=flag,
            **LOADER_KW,
        )
        short = unit_outage_short_derate_factors(
            year, 8760, BINS_CSV_DEFAULT, iso="MISO", per_unit_clip=flag, **LOADER_KW
        )
        layup = {
            k: 1.0 - v
            for k, v in unit_layup_removed_fractions(
                year,
                8760,
                BINS_CSV_DEFAULT,
                iso="MISO",
                cc_steam_part_reclass=LOADER_KW["cc_steam_part_reclass"],
                cc_nameplate_basis=LOADER_KW["cc_nameplate_basis"],
                st_capacity_basis=LOADER_KW["st_capacity_basis"],
                per_unit_clip=flag,
            ).items()
        }
        for layer, d in (("std5d", std), ("short", short), ("layup", layup)):
            for k, arr in d.items():
                out[(layer, year, k)] = np.asarray(arr, dtype=float)
    return out


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
    ca = json.loads((CONTROL / "run_config.json").read_text())["scenario_config"]
    cb = json.loads((ARM / "run_config.json").read_text())["scenario_config"]
    diffs = sorted(k for k in set(ca) | set(cb) if ca.get(k) != cb.get(k))
    return {"n_fields": len(set(ca) | set(cb)), "diffs": diffs, "passed": diffs == [FIELD]}


def s2_s3_loaders() -> tuple[dict, dict]:
    """S-2 liveness and S-3 monotonicity, both off the production loaders."""
    off, on = _layer_arrays(False), _layer_arrays(True)
    keys = sorted(set(off) | set(on), key=lambda k: (k[0], k[1], k[2][0], k[2][1]))

    gained: dict = {}
    worst_regression = {"key": None, "amount": 0.0}
    n_hours_regressed = 0
    per_layer_gain = {"std5d": 0, "short": 0, "layup": 0}
    for k in keys:
        a, b = off.get(k), on.get(k)
        if a is None or b is None:
            # A bin present under one flag and not the other would itself be a
            # monotonicity break; record it as an infinite regression.
            worst_regression = {"key": str(k), "amount": float("inf")}
            continue
        d = b - a
        neg = d < -1e-12
        if neg.any():
            n_hours_regressed += int(neg.sum())
            amt = float(-d[neg].min())
            if amt > worst_regression["amount"]:
                worst_regression = {"key": str(k), "amount": amt}
        if (d > 1e-12).any():
            per_layer_gain[k[0]] += 1
            gained[f"{k[0]}|{k[1]}|{k[2][0]}:{k[2][1]}"] = {
                "mean_availability_control": round(float(np.mean(a)), 6),
                "mean_availability_arm": round(float(np.mean(b)), 6),
                "hours_gaining": int((d > 1e-12).sum()),
                "max_gain": round(float(d.max()), 6),
            }

    s2 = {
        "bins_gaining_availability": len(gained),
        "per_layer_bins_gaining": per_layer_gain,
        "per_bin": dict(sorted(gained.items())),
        # The PREREG requires liveness in EACH of the two layers phase-0 found
        # overlaps in. `short` had zero overlapping pairs, so it must NOT move.
        "short_layer_moved": per_layer_gain["short"],
        "passed": per_layer_gain["std5d"] > 0 and per_layer_gain["layup"] > 0,
    }
    s3 = {
        "bins_checked": len(keys),
        "hours_with_arm_removing_more": n_hours_regressed,
        "worst_regression": worst_regression,
        "passed": n_hours_regressed == 0 and worst_regression["amount"] == 0.0,
    }
    return s2, s3


def kills(vc: dict, va: dict) -> dict:
    out: dict = {}
    c1c, c1a = _c1(vc), _c1(va)
    exits, named = [], {}
    for k in sorted(set(c1c) | set(c1a)):
        b, a = c1c.get(k), c1a.get(k)
        if b is None or a is None:
            continue
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
        "named_ex_ante": named,
        "all_band_exits": exits,
        "passed": not exits,
    }

    b3c, b3a = _c3b(vc), _c3b(va)
    sc, sa = _crit_status(vc), _crit_status(va)
    c3b_flip = [
        k
        for k in sc
        if k.startswith("price_shape") and sc[k] == "PASS" and sa.get(k) not in (None, "PASS")
    ]
    out["K2"] = {"control": b3c, "arm": b3a, "pass_to_fail": c3b_flip, "passed": not c3b_flip}

    # THE miso-200 VACUOUS-PASS TRAP, closed. A --replay-bundle solve writes no
    # legitimacy_diagnostics.json, so an unguarded K-3 compares the empty set
    # against the empty set and reports PASS having measured nothing.
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
        "passed": (not new_d4) if d4_scorable else None,  # None => never a PASS
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
    # The attestation nests its ledger under free_parameters, NOT a top-level
    # "entries" key (the miso-201 scorer read the wrong one for two passes).
    n_c = len((ac_.get("free_parameters") or {}).get("entries") or [])
    n_a = len((aa_.get("free_parameters") or {}).get("entries") or [])
    att = n_c > 0 and n_a > 0
    out["K6"] = {
        "attestation_entries": {"control": n_c, "arm": n_a},
        "status": "SCORED"
        if att
        else (
            "UNSCORED — a leg carries no attestation entries (replay bundles "
            "write none); generate by the gen_miso186/187/188/198/200/201 pattern"
        ),
        "passed": True if att else None,  # None => never counted as a PASS
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
    return {
        "epsilons": INERT_EPS,
        "d_c1_twh": d_c1,
        "c3a_control": ac,
        "c3a_arm": aa,
        "d_c3a_pp": d_c3a,
        "d_c3b": d_c3b,
        "c8_share_control": sc8,
        "c8_share_arm": sa8,
        "d_c8_share": d_c8,
        "status_map_identical": _crit_status(vc) == _crit_status(va),
        "arm_moved_values": moved,
    }


def main() -> dict:
    out: dict = {
        "prereg": "PREREG-miso202-boundary-day-double-count-2026-09-03.md §4",
        "keeper_at_open": "2026-09-02-miso-201-stbasis",
        "capability_bound_twh": CAPABILITY_BOUND_TWH,
        "field": FIELD,
        "control": CONTROL.name,
        "arm": ARM.name,
        "scorer_written_and_committed_before_any_arm_result": True,
        "miso198_scorer_defects_not_inherited": [
            "ordering: kills-silent is evaluated BEFORE inertness",
            "inertness measured on VALUE MOVEMENT, not criterion-status identity",
        ],
        "miso200_vacuous_pass_trap_closed": (
            "K-3/K-4/K-6 are REFUSED (reported UNSCORED, never PASS) unless BOTH "
            "legs carry non-empty D1/D4 rows and attestation entries."
        ),
        "c3a_is_never_a_gate": (
            "rule 1 [R-STRUCT]. Phase-0 N-4 measured 1.4 % / 0.0 % / 1.4 % of the "
            "restored capability landing in the keeper's own top-1 % price hours, "
            "so C3a is expected to barely move; if it moves the right way that is "
            "NOT evidence for the mechanism."
        ),
    }
    out["S0"] = s0_identity()
    print(
        "S-0",
        "PASS — BIT-IDENTICAL"
        if out["S0"]["passed"]
        else f"DRIFT max|diff|={out['S0']['max_abs_diff']} (DISCLOSED, not a kill)",
    )
    out["S1"] = s1_single_delta()
    print("S-1", "PASS" if out["S1"]["passed"] else f"VOID {out['S1']['diffs']}")
    s2, s3 = s2_s3_loaders()
    out["S2"], out["S3"] = s2, s3
    print("S-2", "PASS" if s2["passed"] else "NOT LIVE", s2["per_layer_bins_gaining"])
    print(
        "S-3",
        "PASS — monotone"
        if s3["passed"]
        else f"VOID — arm removes MORE at {s3['hours_with_arm_removing_more']} bin-hours",
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
        out["verdict"] = "VOID — not a single delta; the A/B does not measure the lever"
    elif not out["S3"]["passed"]:
        out["verdict"] = (
            "VOID — S-3 MONOTONICITY BROKEN. The per-unit clip removed MORE capacity "
            "than the production accumulator somewhere; that is a bug in the "
            "mechanism, not a result. Nothing below is scored as evidence."
        )
    elif fired:
        out["verdict"] = (
            f"KILL FIRED ({', '.join(fired)}) — reported at full magnitude and NOT "
            "renegotiated. Under the owner's 2026-09-02 re-scoped bar this is an "
            "OWNER DECISION, not an automatic reject: the structural case and the "
            "regression are stated side by side and the scorer does not promote."
        )
    elif moved:
        out["verdict"] = (
            "KILLS SILENT and the arm MOVED values -> keeper candidate on its own "
            "gates. C3a is reported at full magnitude and is NEVER the justification."
        )
    else:
        out["verdict"] = "INERT — no scored VALUE moved beyond epsilon; keeper unchanged."
    print("VERDICT:", out["verdict"])
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()
