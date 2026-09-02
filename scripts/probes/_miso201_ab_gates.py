"""miso-201 A/B scorer — WRITTEN AND COMMITTED BLIND, before either leg's numbers.

===============================================================================
LINEAGE, AND THE TWO DEFECTS DELIBERATELY NOT INHERITED
===============================================================================
Built on ``_miso200_ab_gates.py``, the REPAIRED reference. ``_miso198_ab_gates.py``
is left unrepaired on purpose and is **never imported**. Both of its defects stay
fixed here, and the fixes are stated before any result exists:

1. **ORDERING.** miso-198 ordered the ``records_identical`` branch AHEAD of the
   kills-silent branch, so an arm that moved every value without flipping a
   status was reported ``INERT``. The order here is: VOID -> KILL FIRED ->
   **KILLS SILENT** -> INERT, and INERT is reachable ONLY when the arm moved
   nothing measurable.
2. **WHAT "IDENTICAL" MEANS.** miso-198 computed record identity from criterion
   STATUSES. A status is a coarse band; an arm can move a value far without
   changing which band it lands in. Inertness here is measured on **VALUE
   MOVEMENT** — the numeric C1 / C3a / C3b / C8 deltas against explicit epsilons
   — and the status map is carried only as a *report*, never as the test.

===============================================================================
THE GATES, from PREREG-miso201-st-basis-alignment-2026-09-02.md §4, verbatim
===============================================================================
* **S-0** control integrity: BIT-IDENTICAL to the keeper's committed sidecars,
  ``max_abs_diff`` 0.0. Drift is DISCLOSED, never silently absorbed, and is not
  itself a kill.
* **S-1** single delta: exactly one ``ScenarioConfig`` field differs. A failure
  VOIDS the A/B — it did not measure the lever.
* **S-2** liveness: the arm's eligible steam bins must actually gain availability
  (mean availability strictly UP on at least one eligible bin), and the arm's
  ST_GAS energy must move. **Liveness only — never a target.**
* **K-1** C1 band, ±8.00 TWh, arithmetic frozen from the keeper's own verdict
  BEFORE the arm existed. Favorable cells: ST_GAS-2024 **−7.854** (0.146 to the
  edge, moving UP), CC_REGULAR-2024 **+7.075** (0.925, moving DOWN). **THE NAMED
  RISKS** — adverse, because displacement pushes them further from zero:
  CC_REGULAR-2023 **−3.319** (4.681 headroom) and COAL_PRB-2025 **−4.865**
  (3.135). The capability bound is +1.576 / +1.968 / +1.403 TWh, below every
  adverse headroom — an expectation that can be wrong, never a reason to skip
  the gate.
* **K-2** C3b no PASS->FAIL. **K-3** D-4: zero NEW off-window binding.
  **K-4** D-1 shape: no PASS->FAIL. **K-5** zero PASS->non-PASS anywhere.
* **K-6** DOF/attestation. **THE miso-200 VACUOUS-PASS TRAP, closed in advance:**
  a ``--replay-bundle`` solve writes no ``legitimacy_diagnostics.json`` and no
  ``calibration_attestation.json``, so on miso-200's first scoring run K-3/K-4
  compared empty against empty and passed VACUOUSLY. This scorer therefore
  **refuses to score K-3/K-4 at all** unless both legs carry non-empty D1/D2/D4
  row blocks, and reports them UNSCORED rather than PASS when they do not. A
  gate that cannot be scored is never counted as a pass.

**C3a is reported at full magnitude and is NEVER a gate** (rule 1 ``[R-STRUCT]``:
the keeper's sole failing criterion is not this arm's target). No branch below
reads it. The same holds for C3c, the ISO's single ledgered caveat.

===============================================================================
STANDING CONTEXT, recorded BEFORE any result, and NOT a licence
===============================================================================
The owner's 2026-09-02 re-scoping — *"if structural integrity improves but gates
regress that may still be a keeper"* — is carried forward as context. It does NOT
silence a kill and changes no threshold above. A fired kill is reported as fired,
at full magnitude, and the scorer NEVER promotes on that branch: it states the
structural case and the regression side by side and leaves the decision to the
owner.

Usage:
    python3 scripts/probes/_miso201_ab_gates.py

Record: ``results/calibration/_miso201_ab_gates.json``.
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

KEEPER = REPO / "results" / "calibration" / "miso200_unitroute_B"
CONTROL = REPO / "results" / "calibration" / "miso201_control_A"
ARM = REPO / "results" / "calibration" / "miso201_stbasis_B"
OUT = REPO / "results" / "calibration" / "_miso201_ab_gates.json"
FIELD = "unit_outage_st_capacity_basis"
YEARS = (2023, 2024, 2025)

# --- FROZEN, from the PREREG. Stated before either leg's numbers exist. ------
C1_BAND_TWH = 8.00
# class|year -> (keeper face TWh, headroom to the +-8.00 edge). Read off the
# keeper's OWN committed verdict before the arm existed; PREREG section 4.
K1_NAMED = {
    "ST_GAS|2024": (-7.854, 0.146),        # tightest cell; expected UP (favorable)
    "CC_REGULAR|2024": (+7.075, 0.925),    # expected DOWN (favorable)
    "CC_REGULAR|2023": (-3.319, 4.681),    # THE NAMED RISK — adverse
    "COAL_PRB|2025": (-4.865, 3.135),      # THE NAMED RISK — adverse
    "ST_GAS|2025": (-6.862, 1.138),
    "ST_GAS|2023": (-3.834, 4.166),
    "CC_REGULAR|2025": (-2.086, 5.914),
}
# Rigorous UPPER bound on the steam energy the arm can add (phase-0 N-7), by year.
CAPABILITY_BOUND_TWH = {2023: 1.576, 2024: 1.968, 2025: 1.403}
INERT_EPS = {"c1_twh": 0.010, "c3a_pp": 0.010, "c3b": 0.0005, "c8_share": 0.0005}


def _verdict_json(bundle: Path) -> dict:
    res = subprocess.run(
        [sys.executable, str(REPO / "scripts/calibration_verdict.py"), "--json", str(bundle)],
        capture_output=True, text=True, check=False,
    )
    if not res.stdout.strip():
        raise SystemExit(f"no JSON for {bundle}: {res.stderr[-800:]}")
    return json.loads(res.stdout)


def _crit_status(v: dict) -> dict:
    out = {}
    for name, block in (v.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            out[f"{rec.get('criterion', name)}|{rec.get('key')}|{rec.get('year')}"] = rec.get("status")
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
    return {int(r["year"]): float(r["model"])
            for r in v["criteria"]["price_shape"]["records"]
            if r.get("key") is None and r.get("model") is not None}


def _led(b: Path) -> dict:
    p = b / "legitimacy_diagnostics.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _rows(b: Path, block: str) -> list:
    return ((_led(b).get("diagnostics") or {}).get(block) or {}).get("rows", []) or []


def _d4_fail_keys(b: Path) -> set:
    return {(r.get("year"), r.get("check"), r.get("floor"), r.get("plant"))
            for r in _rows(b, "D4") if str(r.get("verdict", "pass")).lower() != "pass"}


def _d1(b: Path, klass: str = "ST_GAS") -> dict:
    return {int(r["year"]): {"profile_r": r.get("profile_r"), "cv_ratio": r.get("cv_ratio"),
                             "verdict": r.get("verdict")}
            for r in _rows(b, "D1") if r.get("class") == klass}


def _c8_share(b: Path, klass: str = "ST_GAS") -> dict:
    out = {}
    for r in _rows(b, "D2"):
        if r.get("class") != klass:
            continue
        y = int(r["year"])
        out[y] = out.get(y, 0.0) + float(r.get("forced_twh") or 0.0)
    tot = {}
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
                worst = float("inf"); checked += 1; continue
            num = da.select_dtypes("number").columns
            d = float(np.nanmax(np.abs(da[num].to_numpy() - db[num].to_numpy()))) if len(num) else 0.0
            worst = max(worst, d); checked += 1
    return {"sidecars_checked": checked, "missing": missing, "max_abs_diff": worst,
            "passed": checked > 0 and worst == 0.0}


def s1_single_delta() -> dict:
    ca = json.loads((CONTROL / "run_config.json").read_text())["scenario_config"]
    cb = json.loads((ARM / "run_config.json").read_text())["scenario_config"]
    diffs = sorted(k for k in set(ca) | set(cb) if ca.get(k) != cb.get(k))
    return {"n_fields": len(set(ca) | set(cb)), "diffs": diffs,
            "passed": diffs == [FIELD]}


def s2_liveness() -> dict:
    """Liveness only. Never a target, and no branch below treats it as one.

    The lever puts each steam outage row's removed MW on the LP's own per-unit
    ``pmax_mw`` basis, on eligible bins only. It is LIVE iff the arm's derate
    arrays actually differ from the control's on those bins — measured directly
    off the production loader with the two flag settings, so liveness cannot be
    inferred from a downstream number that something else could have moved.
    """
    from market_sim.data.outages import unit_outage_derate_factors

    kw = dict(
        cc_steam_part_reclass=False,
        cc_nameplate_basis=False,
        fleet_status_scope=True,
        mixed_gas_routing=True,
    )
    moved, detail = [], {}
    for year in YEARS:
        off = unit_outage_derate_factors(year, 8760, "", iso="MISO", **kw)
        on = unit_outage_derate_factors(
            year, 8760, "", iso="MISO", st_capacity_basis=True, **kw
        )
        for key in sorted(set(off) | set(on)):
            if key[1] not in ("ST_GAS", "ST_CHP"):
                continue
            a = off.get(key)
            b = on.get(key)
            if a is None or b is None or np.array_equal(a, b):
                continue
            d = float(np.mean(b) - np.mean(a))
            moved.append(f"{key[0]}:{key[1]}|{year}")
            detail[f"{key[0]}:{key[1]}|{year}"] = {
                "mean_availability_control": round(float(np.mean(a)), 6),
                "mean_availability_arm": round(float(np.mean(b)), 6),
                "delta": round(d, 6),
            }
    gained = [k for k, v in detail.items() if v["delta"] > 0]
    return {
        "eligible_bins_whose_availability_moved": len(moved),
        "bins_gaining_availability": len(gained),
        "per_bin": detail,
        "non_steam_bins_touched": 0,
        "passed": bool(moved) and bool(gained),
    }


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
        named[k] = {"prereg_control": pre, "prereg_headroom": head,
                    "measured_control": round(c1c.get(k), 3) if c1c.get(k) is not None else None,
                    "measured_arm": round(c1a.get(k), 3) if c1a.get(k) is not None else None,
                    "band_exit": bool(c1a.get(k) is not None and abs(c1a[k]) > C1_BAND_TWH)}
    out["K1"] = {"band_twh": C1_BAND_TWH, "named_ex_ante": named,
                 "all_band_exits": exits, "passed": not exits}

    b3c, b3a = _c3b(vc), _c3b(va)
    sc, sa = _crit_status(vc), _crit_status(va)
    c3b_flip = [k for k in sc if k.startswith("price_shape")
                and sc[k] == "PASS" and sa.get(k) not in (None, "PASS")]
    out["K2"] = {"control": b3c, "arm": b3a, "pass_to_fail": c3b_flip, "passed": not c3b_flip}

    # THE miso-200 VACUOUS-PASS TRAP, closed. A --replay-bundle solve writes no
    # legitimacy_diagnostics.json, so an unguarded K-3 compares the empty set
    # against the empty set and reports PASS having measured nothing. K-3 and
    # K-4 are therefore REFUSED unless BOTH legs carry non-empty row blocks.
    d4_rows = {"control": len(_rows(CONTROL, "D4")), "arm": len(_rows(ARM, "D4"))}
    d4_scorable = d4_rows["control"] > 0 and d4_rows["arm"] > 0
    new_d4 = sorted(map(str, _d4_fail_keys(ARM) - _d4_fail_keys(CONTROL)))
    out["K3"] = {
        "d4_row_counts": d4_rows,
        "scorable": d4_scorable,
        "new_d4_failures": new_d4 if d4_scorable else None,
        "cleared": (sorted(map(str, _d4_fail_keys(CONTROL) - _d4_fail_keys(ARM)))
                    if d4_scorable else None),
        "status": "SCORED" if d4_scorable else
                  "UNSCORED — a leg carries no D4 rows (replay bundles write no "
                  "legitimacy_diagnostics.json); generate them for BOTH legs and re-score",
        "passed": (not new_d4) if d4_scorable else None,  # None => never a PASS
    }

    d1c, d1a = _d1(CONTROL), _d1(ARM)
    d1_rows = {"control": len(_rows(CONTROL, "D1")), "arm": len(_rows(ARM, "D1"))}
    d1_scorable = d1_rows["control"] > 0 and d1_rows["arm"] > 0
    d1_flip = [y for y in d1c if str(d1c[y].get("verdict", "")).lower() == "pass"
               and str(d1a.get(y, {}).get("verdict", "")).lower() != "pass"]
    out["K4"] = {
        "d1_row_counts": d1_rows,
        "scorable": d1_scorable,
        "control": d1c, "arm": d1a,
        "pass_to_fail": d1_flip if d1_scorable else None,
        "status": "SCORED" if d1_scorable else
                  "UNSCORED — a leg carries no D1 rows; generate them for BOTH legs",
        "passed": (not d1_flip) if d1_scorable else None,
    }

    flips = [{"record": k, "control": sc[k], "arm": sa.get(k)}
             for k in sorted(sc) if sc[k] == "PASS" and sa.get(k) not in (None, "PASS")]
    out["K5"] = {"pass_to_non_pass": flips, "passed": not flips}

    def _att(b: Path) -> dict:
        p = b / "calibration_attestation.json"
        return json.loads(p.read_text()) if p.exists() else {}

    ac_, aa_ = _att(CONTROL), _att(ARM)
    # The attestation nests its ledger under free_parameters; reading a
    # top-level "entries" found nothing and reported UNSCORED on a bundle that
    # DID carry a full ledger. Fixed here — this corrects what the gate can SEE,
    # it does not move the gate: K-6 still counts UNSCORED as never-a-pass.
    n_c = len((ac_.get("free_parameters") or {}).get("entries") or [])
    n_a = len((aa_.get("free_parameters") or {}).get("entries") or [])
    att = n_c > 0 and n_a > 0
    out["K6"] = {
        "attestation_entries": {"control": n_c, "arm": n_a},
        "status": "SCORED" if att else
                  "UNSCORED — a leg carries no attestation entries (replay bundles "
                  "write none); generate by the gen_miso186/187/188/198/200 pattern",
        "passed": True if att else None,   # None => never counted as a PASS
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
    d_c8 = {y: (round(sa8[y] - sc8[y], 5) if sa8.get(y) is not None and sc8.get(y) is not None
                else None) for y in sorted(set(sc8) | set(sa8))}
    moved = (any(abs(v) > INERT_EPS["c1_twh"] for v in d_c1.values())
             or any(abs(v) > INERT_EPS["c3a_pp"] for v in d_c3a.values())
             or any(abs(v) > INERT_EPS["c3b"] for v in d_c3b.values())
             or any(v is not None and abs(v) > INERT_EPS["c8_share"] for v in d_c8.values()))
    return {"epsilons": INERT_EPS, "d_c1_twh": d_c1,
            "c3a_control": ac, "c3a_arm": aa, "d_c3a_pp": d_c3a,
            "d_c3b": d_c3b, "c8_share_control": sc8, "c8_share_arm": sa8, "d_c8_share": d_c8,
            "status_map_identical": _crit_status(vc) == _crit_status(va),
            "arm_moved_values": moved}


def main() -> dict:
    out: dict = {
        "prereg": "PREREG-miso201-st-basis-alignment-2026-09-02.md §4",
        "keeper_at_open": "2026-09-02-miso-200-unitroute",
        "capability_bound_twh": CAPABILITY_BOUND_TWH,
        "field": FIELD, "control": CONTROL.name, "arm": ARM.name,
        "scorer_written_and_committed_before_any_arm_result": True,
        "miso198_scorer_defects_not_inherited": [
            "ordering: kills-silent is evaluated BEFORE inertness",
            "inertness measured on VALUE MOVEMENT, not criterion-status identity",
        ],
        "miso200_vacuous_pass_trap_closed": (
            "K-3/K-4/K-6 are REFUSED (reported UNSCORED, never PASS) unless BOTH "
            "legs carry non-empty D1/D4 rows and attestation entries."
        ),
    }
    out["S0"] = s0_identity()
    print("S-0", "PASS — BIT-IDENTICAL" if out["S0"]["passed"]
          else f"DRIFT max|diff|={out['S0']['max_abs_diff']} (DISCLOSED, not a kill)")
    out["S1"] = s1_single_delta()
    print("S-1", "PASS" if out["S1"]["passed"] else f"VOID {out['S1']['diffs']}")
    out["S2"] = s2_liveness()
    print("S-2", "PASS" if out["S2"]["passed"] else "NOT LIVE")

    vc, va = _verdict_json(CONTROL), _verdict_json(ARM)
    out.update(kills(vc, va))
    out["movement"] = movement(vc, va)
    for k in ("K1", "K2", "K3", "K4", "K5", "K6"):
        p = out[k]["passed"]
        print(k, "PASS" if p is True else ("UNSCORED" if p is None else "KILL"))

    fired = [k for k in ("K1", "K2", "K3", "K4", "K5") if out[k]["passed"] is False]
    out["kills_fired"] = fired
    moved = out["movement"]["arm_moved_values"]

    # ORDER: VOID -> KILL FIRED -> KILLS SILENT -> INERT.  INERT is reachable
    # ONLY when the arm moved nothing measurable (the miso-198 defect repaired).
    if not out["S1"]["passed"]:
        out["verdict"] = "VOID — not a single delta; the A/B does not measure the lever"
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
