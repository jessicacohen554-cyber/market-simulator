"""nyiso-117 gates G1-G6 and kills K-A..K-E, measured on the two solved arms.

Discharges the pre-registration
``results/calibration/PREREG-nyiso117-nyc-stepcurve-compose-2026-08-03.md``
(committed and pushed before either solve). The session composes two orthogonal
rule-14 ``[R-ACCURATE]`` corrections that neither contains the other: the CT
heat-rate meter-artifact INPUT fix (already on the designated keeper, promoted by
caiso-160) and the NYC locational RCPF demand-curve SHAPE mechanism
(``nyiso_nyc_rcpf_step_curve``, cell ``O`` after nyiso-115 yielded the keeper).

**Every reserve gate reads** ``hourly/reserve_family_<year>.parquet`` — the
per-family dual, requirement, held MW and ORDC shortfall — and **never**
``system_<year>.parquet``'s ``reserve_price``, which is the cross-family SUM
broadcast identically into every zone and is therefore inert by construction for
any locational question. That instrument error has been made three times in this
lane (nyiso-113's K3/K4, nyiso-114's ``held_mw``, nyiso-116's float32 tolerance),
so the choice is stated rather than assumed.

**G2 is written on CONSTRUCTION, inheriting nyiso-115's lesson.** That session's
G2 demanded byte-identity of ``dual``, ``requirement_mw``, ``held_mw`` and
``shortfall_mw`` for every non-NYC family — but three of those four are SOLVED
OUTPUTS of a co-optimization, so the gate could only pass if the mechanism did
nothing, and it failed uninformatively. What kill K-C actually asks is whether
the mechanism touched a family it was not scoped to, which is a question about
construction. So the kill leg here is:

* **G2a** — ``requirement_mw`` (a pure input: the balance-row RHS) byte-identical
  for every non-NYC family, asserted as float32 EXACT equality rather than
  against a ``1e-6`` MW tolerance the dtype cannot represent (nyiso-116);
* **G2b** — the ORDC step VECTORS, observed through the solve log's
  ``%d ORDC steps`` line (``pipeline/kwargs.py``), an instrument entirely
  independent of the parquet;
* **G2c** — ``shortfall_mw``, REPORTED but explicitly not a kill: it is a solved
  LP variable, identically zero on the non-NYC families only because they are
  slack, and gating on it would repeat the same category error at one remove;
* ``dual`` and ``held_mw`` for non-NYC families are reported and **explicitly not
  gated** — movement there is the expected equilibrium response.

Run:
    PYTHONPATH=.:src python scripts/probes/_nyiso117_stepcurve_gates.py
"""

from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

CAL = REPO_ROOT / "results" / "calibration"
CONTROL = CAL / "nyiso117_control"
TREAT = CAL / "nyiso117_nyc_stepcurve"
# The DESIGNATED KEEPER this session composes onto. Unlike nyiso-115's keeper it
# DOES carry the per-family sidecar, so K-A's drift can be quantified directly
# rather than only argued around.
KEEPER = CAL / "nyiso160_ctmeter_screen_B"
YEARS = (2023, 2024, 2025)

NYC_FAMILIES = ("nyc_10min_total", "nyc_30min_total")
PUBLISHED_RCPF = 25.0
# The 8-step ramp's interior rungs: max_penalty*(k+1)/8 for k<7. The step curve
# must reach the RCPF and must never sit on one of these.
RAMP_RUNGS = tuple(PUBLISHED_RCPF * (k + 1) / 8 for k in range(7))
# Expected ORDC step-count drop: the two NYC families lose 7 interior rungs each
# when their ramp collapses to the published single step.
EXPECTED_STEP_DROP = 14
TOL = 1e-6


def _rf(bundle, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"reserve_family_{year}.parquet")
    df["family"] = df["family"].astype(str)
    return df


def _system(bundle, year: int) -> pd.DataFrame:
    """The per-(zone, hour) system sidecar: price, slack, dump, demand."""
    return pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet").sort_values(
        ["zone", "hour"]
    )


def gate_g1() -> dict:
    """G1 — the curve is actually armed, and the ramp is gone.

    Pass: the NYC families take the published $25.00 in >=1 hour and take NO
    interior-rung value in ANY hour, all three years.
    """
    out = {}
    ok = True
    for year in YEARS:
        df = _rf(TREAT, year)
        per = {}
        for fam in NYC_FAMILIES:
            d = df[df["family"] == fam]["dual"].to_numpy()
            at_rcpf = int(np.isclose(d, PUBLISHED_RCPF, atol=1e-3).sum())
            on_rungs = int(sum(np.isclose(d, r, atol=1e-3).sum() for r in RAMP_RUNGS))
            per[fam] = {
                "hours_at_published_rcpf": at_rcpf,
                "hours_on_ramp_interior_rungs": on_rungs,
                "hours_dual_positive": int((d > TOL).sum()),
                "max_dual": round(float(d.max()), 4),
            }
            if at_rcpf < 1 or on_rungs > 0:
                ok = False
        out[str(year)] = per
    return {"pass": ok, "per_year": out}


def gate_g2a() -> dict:
    """G2a — scope, CONSTRUCTION leg. THE KILL.

    ``requirement_mw`` is a pure input (the reserve balance-row RHS), so it is
    the one column in the sidecar that a scope leak must move and an equilibrium
    response cannot. Byte-identity is asserted as float32 EXACT equality: two
    identically-constructed input vectors satisfy it exactly, and the dtype's
    spacing (7.6e-06 - 6.1e-05 MW here) makes a 1e-6 tolerance unsatisfiable in
    principle (the nyiso-116 G3/P4 failure).
    """
    ok = True
    out = {}
    for year in YEARS:
        c, t = _rf(CONTROL, year), _rf(TREAT, year)
        fams = sorted(set(c["family"]) - set(NYC_FAMILIES))
        per = {}
        for fam in fams:
            a = c[c["family"] == fam].sort_values("hour")["requirement_mw"].to_numpy()
            b = t[t["family"] == fam].sort_values("hour")["requirement_mw"].to_numpy()
            identical = bool(a.shape == b.shape and np.array_equal(a, b))
            per[fam] = {
                "float32_exactly_identical": identical,
                "max_abs_delta": float(np.max(np.abs(a - b))) if a.shape == b.shape else None,
            }
            if not identical:
                ok = False
        out[str(year)] = per
    return {
        "pass": ok,
        "note": (
            "requirement_mw is the balance-row RHS — a pure INPUT. Equality is "
            "float32 exact (np.array_equal), not a tolerance the dtype cannot "
            "represent."
        ),
        "per_year": out,
    }


def _ordc_step_counts(bundle) -> dict:
    """Parse the co-opt line's ORDC step count out of a bundle's saved solve log.

    ``pipeline/kwargs.py`` logs 'energy+reserve co-opt (NYISO): N locational
    reserve families (...), M ORDC steps ($lo-$hi), ...' once per solve. The
    relevant lines are copied into the bundle as ``ordc_steps.log`` so this gate
    reads a COMMITTED artifact rather than a session-local file.
    """
    path = bundle / "ordc_steps.log"
    if not path.exists():
        return {"error": f"missing {path}"}
    lines = [ln for ln in path.read_text().splitlines() if "ORDC steps" in ln]
    counts, families = [], []
    for ln in lines:
        m = re.search(r"(\d+) ORDC steps", ln)
        f = re.search(r"(\d+) locational reserve families", ln)
        if m:
            counts.append(int(m.group(1)))
        if f:
            families.append(int(f.group(1)))
    return {
        "n_log_lines": len(lines),
        "step_counts": counts,
        "distinct_step_counts": sorted(set(counts)),
        "family_counts": sorted(set(families)),
    }


def gate_g2b() -> dict:
    """G2b — scope, INDEPENDENT corroboration from the solve log.

    The ORDC step vectors are pure construction. If the mechanism were leaking
    into another family, the total step count would fall by more than the two
    NYC families' 7 interior rungs each; if it were inert, it would not fall at
    all. This instrument never touches the parquet, so it cannot share a failure
    mode with G2a.
    """
    c, t = _ordc_step_counts(CONTROL), _ordc_step_counts(TREAT)
    ok = False
    drop = None
    if "error" not in c and "error" not in t:
        if len(c["distinct_step_counts"]) == 1 and len(t["distinct_step_counts"]) == 1:
            drop = c["distinct_step_counts"][0] - t["distinct_step_counts"][0]
            ok = drop == EXPECTED_STEP_DROP and c["family_counts"] == t["family_counts"]
    return {
        "pass": ok,
        "control": c,
        "treatment": t,
        "observed_drop": drop,
        "expected_drop": EXPECTED_STEP_DROP,
        "note": (
            "expected drop = 2 NYC families x 7 lost interior rungs. The family "
            "COUNT must be unchanged: the mechanism collapses two curves, it does "
            "not remove a family."
        ),
    }


def gate_g2c() -> dict:
    """G2c — scope, REPORTED ONLY. Not a kill, and the docstring says why.

    ``shortfall_mw`` is a solved LP variable, not an input. It is identically
    zero on the non-NYC families only because those families are slack, so a
    pass here is a statement about the dispatch, not about construction. It is
    reported because a MOVE would be a finding worth explaining — but it cannot
    fire K-C on its own.
    """
    out = {}
    all_zero_delta = True
    for year in YEARS:
        c, t = _rf(CONTROL, year), _rf(TREAT, year)
        fams = sorted(set(c["family"]) - set(NYC_FAMILIES))
        per = {}
        for fam in fams:
            a = c[c["family"] == fam].sort_values("hour")
            b = t[t["family"] == fam].sort_values("hour")
            rec = {
                col: round(
                    float(np.max(np.abs(a[col].to_numpy() - b[col].to_numpy()))), 8
                )
                for col in ("shortfall_mw", "dual", "held_mw")
            }
            per[fam] = rec
            if rec["shortfall_mw"] > 0.0:
                all_zero_delta = False
        out[str(year)] = per
    return {
        "shortfall_delta_is_zero_everywhere": all_zero_delta,
        "note": (
            "REPORTED, NOT A KILL. shortfall_mw is a solved LP variable; dual and "
            "held_mw are shown alongside it precisely because their movement is "
            "the EXPECTED equilibrium response of a co-optimization and must not "
            "be read as a scope leak (the nyiso-115 G2 mis-specification)."
        ),
        "per_year": out,
    }


def gate_g3() -> dict:
    """G3 — the LP row identity holds: held + shortfall >= requirement."""
    out = {}
    ok = True
    for year in YEARS:
        df = _rf(TREAT, year)
        gap = (df["held_mw"] + df["shortfall_mw"] - df["requirement_mw"]).to_numpy()
        priced = df["dual"].to_numpy() > TOL
        rec = {
            "min_slack_mw": round(float(gap.min()), 6),
            "max_abs_slack_where_priced": round(
                float(np.max(np.abs(gap[priced]))) if priced.any() else 0.0, 6
            ),
            "n_priced_rows": int(priced.sum()),
        }
        # Feasible everywhere, and tight exactly where the family prices. The
        # tolerances are float32-representable at these magnitudes (nyiso-116).
        if rec["min_slack_mw"] < -1e-3 or rec["max_abs_slack_where_priced"] > 1e-2:
            ok = False
        out[str(year)] = rec
    return {"pass": ok, "per_year": out}


def gate_g4() -> dict:
    """G4 — no feasibility damage: zero unserved-energy slack and zero dump."""
    out = {}
    ok = True
    for year in YEARS:
        rec = {}
        for name, bundle in (("control", CONTROL), ("treatment", TREAT)):
            d = _system(bundle, year)
            rec[name] = {
                "slack_mwh": round(float(d["slack"].abs().sum()), 6),
                "dump_mwh": round(float(d["dump"].abs().sum()), 6),
            }
        for key in ("slack_mwh", "dump_mwh"):
            if rec["treatment"][key] > rec["control"][key] + 1e-6:
                ok = False
        out[str(year)] = rec
    return {"pass": ok, "per_year": out}


def kill_ka() -> dict:
    """K-A — is the effect main's drift rather than the mechanism?

    Discharged BY MEASUREMENT, and this session can do it directly: unlike
    nyiso-115's keeper, the designated keeper carries the per-family sidecar, so
    control-vs-keeper drift is observable on the SAME column the mechanism moves.
    The kill FIRES if that drift is as large as the mechanism's own effect on the
    NYC families' duals.
    """
    out = {}
    fires = False
    for year in YEARS:
        c, t = _rf(CONTROL, year), _rf(TREAT, year)
        kp = KEEPER / "hourly" / f"reserve_family_{year}.parquet"
        k = _rf(KEEPER, year) if kp.exists() else None
        rec = {}
        for fam in NYC_FAMILIES:
            a = c[c["family"] == fam].sort_values("hour")["dual"].to_numpy()
            b = t[t["family"] == fam].sort_values("hour")["dual"].to_numpy()
            effect = float(np.max(np.abs(a - b)))
            entry = {
                "treatment_vs_control_max_abs_ddual": round(effect, 4),
                "treatment_vs_control_hours_differing": int((np.abs(a - b) > TOL).sum()),
            }
            if k is not None:
                kk = k[k["family"] == fam].sort_values("hour")["dual"].to_numpy()
                if kk.shape == a.shape:
                    drift = float(np.max(np.abs(a - kk)))
                    entry["control_vs_keeper_max_abs_ddual_DRIFT"] = round(drift, 4)
                    entry["drift_exceeds_effect"] = bool(drift >= effect)
                    if drift >= effect:
                        fires = True
            rec[fam] = entry
        rec["keeper_carries_sidecar"] = kp.exists()
        out[str(year)] = rec
    return {
        "fires": fires,
        "note": (
            "Every attribution reported anywhere in this probe is TREATMENT vs the "
            "same-HEAD CONTROL, never treatment vs keeper. The keeper is "
            "differenced HERE ONLY, to quantify the drift the same-HEAD design "
            "exists to neutralize."
        ),
        "per_year": out,
    }


def kill_ke() -> dict:
    """K-E — is the composition additive, or did the input fix move the binding set?

    The mechanism can only act in hours the NYC families bind. If the CT
    heat-rate correction changed WHICH hours those are so much that the
    mechanism's effect is unreadable, that is reported as measured — it does not
    license changing either correction.
    """
    out = {}
    for year in YEARS:
        c, t = _rf(CONTROL, year), _rf(TREAT, year)
        kp = KEEPER / "hourly" / f"reserve_family_{year}.parquet"
        k = _rf(KEEPER, year) if kp.exists() else None
        rec = {}
        for fam in NYC_FAMILIES:
            cb = set(
                c[(c["family"] == fam) & (c["dual"] > TOL)]["hour"].astype(int).tolist()
            )
            tb = set(
                t[(t["family"] == fam) & (t["dual"] > TOL)]["hour"].astype(int).tolist()
            )
            entry = {
                "control_binding_hours": len(cb),
                "treatment_binding_hours": len(tb),
                "binding_hours_gained": len(tb - cb),
                "binding_hours_lost": len(cb - tb),
            }
            if k is not None:
                kb = set(
                    k[(k["family"] == fam) & (k["dual"] > TOL)]["hour"]
                    .astype(int)
                    .tolist()
                )
                entry["keeper_binding_hours"] = len(kb)
                entry["control_vs_keeper_jaccard"] = (
                    round(len(cb & kb) / len(cb | kb), 4) if (cb | kb) else 1.0
                )
            rec[fam] = entry
        out[str(year)] = rec
    return {
        "note": (
            "PRE-REGISTERED NULL (prereg §5): a step and a ramp are BOTH $0 at or "
            "above the requirement, so the mechanism moves the LEVEL in hours a "
            "family already binds and CANNOT add binding hours. Any change in the "
            "binding SET is therefore either the co-optimization re-equilibrating "
            "or a shortfall crossing zero — reported in either direction, and not "
            "grounds for rejecting the mechanism (rule 1 [R-STRUCT])."
        ),
        "per_year": out,
    }


def price_effect() -> dict:
    """Treatment-vs-control price attribution, the same-HEAD comparison."""
    out = {}
    for year in YEARS:
        c, t = _system(CONTROL, year), _system(TREAT, year)
        a, b = c["price"].to_numpy(), t["price"].to_numpy()
        rec = {
            "mean_price_control": round(float(a.mean()), 4),
            "mean_price_treatment": round(float(b.mean()), 4),
            "mean_price_pct_delta": round(float((b.mean() / a.mean() - 1) * 100), 4),
            "max_abs_dprice": round(float(np.max(np.abs(a - b))), 4),
            "zone_hours_differing": int((np.abs(a - b) > TOL).sum()),
            "zone_hours": int(len(a)),
        }
        # The mechanism is NYC-locational, so report the NYC zone on its own — a
        # system mean over five zones dilutes a one-zone effect by ~5x.
        for zone in ("NYC", "Long_Island"):
            za = c[c["zone"] == zone]["price"].to_numpy()
            zb = t[t["zone"] == zone]["price"].to_numpy()
            if len(za):
                rec[f"{zone}_mean_control"] = round(float(za.mean()), 4)
                rec[f"{zone}_mean_treatment"] = round(float(zb.mean()), 4)
                rec[f"{zone}_hours_gt_300_control"] = int((za > 300).sum())
                rec[f"{zone}_hours_gt_300_treatment"] = int((zb > 300).sum())
                rec[f"{zone}_max_control"] = round(float(za.max()), 2)
                rec[f"{zone}_max_treatment"] = round(float(zb.max()), 2)
        out[str(year)] = rec
    return out


def main() -> None:
    doc = {
        "probe": "nyiso-117 step-curve compose gates (prereg discharge)",
        "prereg": "results/calibration/PREREG-nyiso117-nyc-stepcurve-compose-2026-08-03.md",
        "control": str(CONTROL.relative_to(REPO_ROOT)),
        "treatment": str(TREAT.relative_to(REPO_ROOT)),
        "keeper_composed_onto": str(KEEPER.relative_to(REPO_ROOT)),
        "G1_curve_armed": gate_g1(),
        "G2a_scope_construction_KILL": gate_g2a(),
        "G2b_scope_ordc_step_count": gate_g2b(),
        "G2c_scope_reported_not_a_kill": gate_g2c(),
        "G3_lp_row_identity": gate_g3(),
        "G4_feasibility": gate_g4(),
        "K_A_drift_attribution": kill_ka(),
        "K_E_composition_additivity": kill_ke(),
        "price_effect_treatment_vs_control": price_effect(),
    }
    out = CAL / "_nyiso117_stepcurve_gates.json"
    out.write_text(json.dumps(doc, indent=2))
    for k in (
        "G1_curve_armed",
        "G2a_scope_construction_KILL",
        "G2b_scope_ordc_step_count",
        "G3_lp_row_identity",
        "G4_feasibility",
    ):
        print(f"{k:32s} pass={doc[k]['pass']}")
    print(f"G2c shortfall delta zero everywhere = "
          f"{doc['G2c_scope_reported_not_a_kill']['shortfall_delta_is_zero_everywhere']}")
    print(f"K-A fires = {doc['K_A_drift_attribution']['fires']}")
    print(json.dumps(doc["price_effect_treatment_vs_control"], indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
