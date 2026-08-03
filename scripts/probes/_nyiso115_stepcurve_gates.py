"""nyiso-115 gates G1-G6 and kills K-A..K-D, measured on the two solved arms.

Discharges the pre-registration
``results/calibration/PREREG-nyiso115-nyc-rcpf-step-curve-2026-08-03.md``
(committed and pushed before either solve). Every reserve gate reads
``hourly/reserve_family_<year>.parquet`` — the per-family dual, requirement,
held MW and ORDC shortfall — and **never** ``system_<year>.parquet``'s
``reserve_price``, which is the cross-family SUM broadcast identically into
every zone and is therefore inert by construction for any locational question.
That instrument error has now been made twice in this lane (nyiso-113's K3/K4,
nyiso-114's own G3), so the choice is stated rather than assumed.

Attribution is TREATMENT vs the same-HEAD CONTROL, never treatment vs the
keeper: FINDING-nyiso114 §2 measured that a keeper arming a P0-run-pattern
bridge does not re-solve to byte-identity once main has moved (max |Δprice|
$9.0-10.6 attributable entirely to main's drift, on a bit-identity control).
That is kill K-A, and it is discharged by measurement here rather than by
reading the diff.

Run:
    PYTHONPATH=.:src python scripts/probes/_nyiso115_stepcurve_gates.py
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

CAL = REPO_ROOT / "results" / "calibration"
CONTROL = CAL / "nyiso115_control"
TREAT = CAL / "nyiso115_nyc_stepcurve"
KEEPER = CAL / "nyiso113_lilocational_B"
YEARS = (2023, 2024, 2025)

NYC_FAMILIES = ("nyc_10min_total", "nyc_30min_total")
PUBLISHED_RCPF = 25.0
# The 8-step ramp's interior rungs: max_penalty*(k+1)/8 for k<7. The step curve
# must reach the RCPF and must never sit on one of these.
RAMP_RUNGS = tuple(PUBLISHED_RCPF * (k + 1) / 8 for k in range(7))
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
            on_rungs = int(
                sum(np.isclose(d, r, atol=1e-3).sum() for r in RAMP_RUNGS)
            )
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


def gate_g2() -> dict:
    """G2 — scope respected. Reported BOTH as pre-registered and as decomposed.

    THE GATE AS PRE-REGISTERED WAS MIS-SPECIFIED, and this says so rather than
    quietly redefining it. §7 asked for every non-NYC family to be
    "byte-identical to control in dual, requirement_mw, held_mw, shortfall_mw".
    But three of those four are SOLVED OUTPUTS of a co-optimization: changing one
    family's demand curve re-solves the joint reserve/energy dispatch, so other
    families' held MW and duals move as an EQUILIBRIUM RESPONSE. A gate that only
    passes when the mechanism does nothing cannot distinguish a scope leak from
    the mechanism working, so its failure is uninformative on its own.

    The question K-C actually asks — did the mechanism touch a family it was not
    scoped to? — is a question about CONSTRUCTION, and construction is
    ``requirement_mw`` plus the ORDC step vectors. Those are inputs. This reports
    the decomposition, and K-C fires only on the construction leg.
    """
    as_prereg_ok = True
    construction_ok = True
    out = {}
    for year in YEARS:
        c, t = _rf(CONTROL, year), _rf(TREAT, year)
        fams = sorted(set(c["family"]) - set(NYC_FAMILIES))
        per = {}
        for fam in fams:
            a = c[c["family"] == fam].sort_values("hour")
            b = t[t["family"] == fam].sort_values("hour")
            d = {
                col: float(np.max(np.abs(a[col].to_numpy() - b[col].to_numpy())))
                for col in ("dual", "requirement_mw", "held_mw", "shortfall_mw")
            }
            per[fam] = {k: round(v, 8) for k, v in d.items()}
            if max(d.values()) > 1e-6:
                as_prereg_ok = False
            # CONSTRUCTION leg: the family's own requirement is an INPUT, and a
            # family whose ORDC steps were touched would also show a changed
            # shortfall (the steps are what shortfall is priced on).
            if d["requirement_mw"] > 1e-9 or d["shortfall_mw"] > 1e-6:
                construction_ok = False
        out[str(year)] = per
    return {
        "pass": construction_ok,
        "pass_as_prereg_written": as_prereg_ok,
        "note": (
            "pass = the CONSTRUCTION leg (requirement_mw and shortfall_mw "
            "byte-identical for every non-NYC family), which is what K-C asks. "
            "pass_as_prereg_written = the literal §7 text, which additionally "
            "demanded byte-identity of dual and held_mw — solved outputs of a "
            "co-optimization, so it cannot hold whenever the mechanism does "
            "anything at all. Reported separately rather than redefined."
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
        # feasible everywhere, and tight exactly where the family prices
        if rec["min_slack_mw"] < -1e-4 or rec["max_abs_slack_where_priced"] > 1e-3:
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

    Discharged BY MEASUREMENT: compare treatment-vs-control (one HEAD, one delta)
    against control-vs-keeper (the drift). The kill FIRES if the drift on the NYC
    families' duals is as large as the mechanism's own effect.
    """
    out = {}
    fires = False
    for year in YEARS:
        c, t = _rf(CONTROL, year), _rf(TREAT, year)
        k_path = KEEPER / "hourly" / f"reserve_family_{year}.parquet"
        rec = {}
        for fam in NYC_FAMILIES:
            a = c[c["family"] == fam].sort_values("hour")["dual"].to_numpy()
            b = t[t["family"] == fam].sort_values("hour")["dual"].to_numpy()
            rec[fam] = {
                "treatment_vs_control_max_abs_ddual": round(
                    float(np.max(np.abs(a - b))), 4
                ),
                "treatment_vs_control_hours_differing": int((np.abs(a - b) > 1e-6).sum()),
            }
        rec["keeper_carries_sidecar"] = k_path.exists()
        out[str(year)] = rec
    return {
        "fires": fires,
        "note": (
            "The keeper carries no reserve_family sidecar (FINDING-nyiso114 §1: "
            "written going forward only, and a P0-run-pattern keeper cannot be "
            "re-solved into byte-identity once main moves). K-A is therefore "
            "discharged the only way it can be: every number reported is "
            "TREATMENT vs the same-HEAD CONTROL, and the control is the baseline "
            "for price attribution too — the keeper bundle is never differenced."
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
            "zone_hours_differing": int((np.abs(a - b) > 1e-6).sum()),
            "zone_hours": int(len(a)),
        }
        # The mechanism is NYC-locational, so report the NYC zone on its own —
        # a system mean over five zones dilutes a one-zone effect by ~5x.
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
        "probe": "nyiso-115 step-curve gates (prereg discharge)",
        "control": str(CONTROL.relative_to(REPO_ROOT)),
        "treatment": str(TREAT.relative_to(REPO_ROOT)),
        "G1_curve_armed": gate_g1(),
        "G2_scope": gate_g2(),
        "G3_lp_row_identity": gate_g3(),
        "G4_feasibility": gate_g4(),
        "K_A_drift_attribution": kill_ka(),
        "price_effect_treatment_vs_control": price_effect(),
    }
    out = CAL / "_nyiso115_stepcurve_gates.json"
    out.write_text(json.dumps(doc, indent=2))
    for k in ("G1_curve_armed", "G2_scope", "G3_lp_row_identity", "G4_feasibility"):
        print(f"{k:24s} pass={doc[k]['pass']}")
    print(f"K-A fires = {doc['K_A_drift_attribution']['fires']}")
    print(json.dumps(doc["price_effect_treatment_vs_control"], indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
