"""nyiso-119: score the pre-registered gates for the SENY increment-tier arm.

Discharges the gate set in
``results/calibration/PREREG-nyiso119-seny-increment-2026-08-03.md`` §7 against
the two bundles' COMMITTED artifacts. No solve is replayed.

THE INSTRUMENT SPLIT, stated because it is the point:

* ``hourly/reserve_family_<year>.parquet`` carries ``requirement_mw`` (the
  balance-row RHS — a pure INPUT) and ``dual`` / ``held_mw`` / ``shortfall_mw``
  (SOLVED co-optimization outputs). It does **not** carry the ORDC width or
  penalty vectors. So the parquet discharges the requirement legs, the LP row
  identity and the §5 price prediction (G4, which is a statement ABOUT the
  solved dual and is gated deliberately — it is this mechanism's own liveness
  test, not a scope claim), and it CANNOT discharge any curve-shape leg.
* Every curve-shape/level leg (G1, G2, G3a's width+penalty halves, G3b, K-A…K-E)
  is scored on the committed CONSTRUCTION artifact
  ``results/calibration/nyiso119_seny_increment_construction_probe.json`` plus
  each bundle's committed ``ordc_steps.log`` — never on a dual.

Gating a SCOPE kill on ``dual`` or ``held_mw`` can only pass when the mechanism
does nothing (the nyiso-115 G2 error; nyiso-118 is the live proof that a
provably-unchanged curve still moves its dual through general equilibrium).
Non-SENY duals are therefore REPORTED here (G3d), never gated.

Byte-identity is float32 EXACT equality (``np.array_equal``). No tolerance is
used: the sidecar columns are float32 with spacing 7.6e-06-6.1e-05 MW, so a
1e-6 MW tolerance is unsatisfiable in principle (nyiso-116 G3/P4).

Run:
    PYTHONPATH=.:src python scripts/probes/_nyiso119_score_gates.py \\
        --control results/calibration/nyiso119_control \\
        --treatment results/calibration/nyiso119_seny_increment \\
        --construction \\
          results/calibration/nyiso119_seny_increment_construction_probe.json \\
        --json-out results/calibration/nyiso119_gate_scores.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2023, 2024, 2025)
SENY = "seny_30min_total"
NYC_PAIR = ("nyc_10min_total", "nyc_30min_total")
LI30 = "li_30min_total"

#: Published SENY base MW and increment RCPF — imported, never re-typed (rule 5).
from market_sim.model.reserves.spec import (  # noqa: E402
    NYISO_RCPF_LOCATIONAL,
    NYISO_SENY_30MIN_INCREMENT_RCPF,
)

SENY_BASE_MW = float(NYISO_RCPF_LOCATIONAL["SENY"]["products"][0][1])


def _fam(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"reserve_family_{year}.parquet")
    return df.sort_values(["pass", "family", "hour"], kind="mergesort").reset_index(
        drop=True
    )


def _sys(bundle: Path, year: int) -> pd.DataFrame:
    return pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument("--treatment", type=Path, required=True)
    ap.add_argument("--construction", type=Path, required=True)
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()

    constr = json.loads(args.construction.read_text())
    out: dict = {
        "probe": "nyiso-119 pre-registered gate scoring",
        "prereg": "results/calibration/PREREG-nyiso119-seny-increment-2026-08-03.md §7",
        "control": str(args.control),
        "treatment": str(args.treatment),
        "published_increment_rcpf": NYISO_SENY_30MIN_INCREMENT_RCPF,
        "published_base_mw": SENY_BASE_MW,
        "instrument_note": (
            "requirement legs + LP row identity + the §5 price prediction from "
            "the reserve_family parquet; every CURVE SHAPE/LEVEL leg from the "
            "committed construction probe + ordc_steps.log (the parquet carries "
            "no width or penalty vectors); non-SENY dual/held/shortfall "
            "REPORTED, never gated"
        ),
        "years": {},
        "gates": {},
        "kills": {},
    }

    g3a_ok, g5_ok, g6_ok = True, True, True
    g4_ok = True
    per_year: dict = {}
    g4_detail: dict = {}

    for year in YEARS:
        c, t = _fam(args.control, year), _fam(args.treatment, year)
        assert list(c.columns) == list(t.columns)
        fams = sorted(set(c["family"].astype(str)))
        yr: dict = {"families": {}}

        for name in fams:
            cc = c[c["family"].astype(str) == name]
            tt = t[t["family"].astype(str) == name]
            req_c = cc["requirement_mw"].to_numpy()
            req_t = tt["requirement_mw"].to_numpy()
            same_req = bool(
                req_c.shape == req_t.shape and np.array_equal(req_c, req_t)
            )
            if not same_req:
                g3a_ok = False
            # G5: LP row identity, both arms
            for _arm, df in (("control", cc), ("treatment", tt)):
                held = df["held_mw"].to_numpy(dtype=float)
                short = df["shortfall_mw"].to_numpy(dtype=float)
                req = df["requirement_mw"].to_numpy(dtype=float)
                if not bool((held + short >= req - 1e-3).all()):
                    g5_ok = False
            d_c = cc["dual"].to_numpy(dtype=float)
            d_t = tt["dual"].to_numpy(dtype=float)
            s_c = cc["shortfall_mw"].to_numpy(dtype=float)
            s_t = tt["shortfall_mw"].to_numpy(dtype=float)
            h_c = cc["held_mw"].to_numpy(dtype=float)
            h_t = tt["held_mw"].to_numpy(dtype=float)
            yr["families"][name] = {
                "requirement_identical": same_req,  # GATED (G3a / K-A)
                # REPORTED, NOT GATED (G3d) — solved co-optimization outputs.
                "dual_identical": bool(np.array_equal(d_c, d_t)),
                "max_abs_dual_delta": float(np.abs(d_c - d_t).max()),
                "hours_dual_pos_control": int((d_c > 0).sum()),
                "hours_dual_pos_treatment": int((d_t > 0).sum()),
                "max_dual_control": float(d_c.max()),
                "max_dual_treatment": float(d_t.max()),
                "max_abs_held_delta": float(np.abs(h_c - h_t).max()),
                "max_abs_shortfall_delta": float(np.abs(s_c - s_t).max()),
                "max_shortfall_control": float(s_c.max()),
                "max_shortfall_treatment": float(s_t.max()),
            }

        # --- G4 / K-G: the §5 PREDICTION, on the solved treatment sidecar ---
        # In the treatment, every hour whose shortfall stays INSIDE the
        # published increment band must price at EXACTLY the published $40.00.
        # A deeper shortfall reaches the base ramp legitimately and is reported
        # separately rather than failing the gate (prereg §5).
        tt = t[t["family"].astype(str) == SENY]
        # P1 is THE scored pass; restrict to it so a P0 row cannot mask the test.
        if "pass" in tt.columns and (tt["pass"].astype(str) == "P1").any():
            tt = tt[tt["pass"].astype(str) == "P1"]
        d = tt["dual"].to_numpy(dtype=float)
        s = tt["shortfall_mw"].to_numpy(dtype=float)
        r = tt["requirement_mw"].to_numpy(dtype=float)
        band = np.maximum(0.0, r - SENY_BASE_MW)
        inside = (d > 0) & (s > 0) & (s <= band + 1e-6)
        deeper = (d > 0) & (s > band + 1e-6)
        at_published = np.isclose(
            d[inside], NYISO_SENY_30MIN_INCREMENT_RCPF, rtol=0, atol=1e-6
        )
        if inside.sum() and not bool(at_published.all()):
            g4_ok = False
        g4_detail[str(year)] = {
            "hours_binding_treatment": int((d > 0).sum()),
            "hours_shortfall_inside_increment_band": int(inside.sum()),
            "hours_priced_exactly_at_published_40": int(at_published.sum()),
            "hours_shortfall_deeper_than_band": int(deeper.sum()),
            "max_dual_treatment": float(d.max()),
            "max_shortfall_treatment": float(s.max()),
            "distinct_duals_when_binding": sorted(
                {round(float(v), 6) for v in d[d > 0]}
            )[:12],
        }

        # G6: feasibility, both arms
        sc, st = _sys(args.control, year), _sys(args.treatment, year)
        feas = {
            "control_max_slack": float(sc["slack"].max()),
            "control_max_dump": float(sc["dump"].max()),
            "treatment_max_slack": float(st["slack"].max()),
            "treatment_max_dump": float(st["dump"].max()),
        }
        if max(feas.values()) > 1e-6:
            g6_ok = False
        yr["feasibility"] = feas
        per_year[str(year)] = yr

    out["years"] = per_year

    # ---- curve legs: committed construction artifact + ordc_steps.log ----
    steps = {}
    for tag, b in (("control", args.control), ("treatment", args.treatment)):
        p = b / "ordc_steps.log"
        txt = p.read_text() if p.exists() else ""
        steps[tag] = [int(m) for m in re.findall(r"(\d+) ORDC steps", txt)]
    # G3c: EXACTLY +1 step, in exactly one family, in every solve pass.
    g3c_ok = bool(
        steps["control"]
        and len(steps["control"]) == len(steps["treatment"])
        and all(b - a == 1 for a, b in zip(steps["control"], steps["treatment"]))
    )
    out["ordc_steps"] = {**steps, "delta_is_plus_one_everywhere": g3c_ok}

    cyears = constr["years"]

    def _all(fam: str, key: str) -> bool:
        return all(bool(cyears[str(y)]["families"][fam][key]) for y in YEARS)

    non_seny = [n for n in cyears["2023"]["families"] if n != SENY]
    scope_widths = all(_all(n, "widths_identical") for n in non_seny)
    scope_pens = all(_all(n, "penalties_identical") for n in non_seny)
    scope_reqs = all(_all(n, "requirement_identical") for n in non_seny)
    scope_price = all(_all(n, "reachable_price_identical") for n in non_seny)
    frozen_price_same = all(
        _all(n, "reachable_price_identical") for n in (*NYC_PAIR, LI30)
    )
    seny_price_changed = all(
        not bool(cyears[str(y)]["families"][SENY]["reachable_price_identical"])
        for y in YEARS
    )
    seny_never_up = _all(SENY, "reachable_price_never_increases")

    sc = {str(y): cyears[str(y)]["seny_construction"] for y in YEARS}
    g1_ok = all(
        s["n_steps_on"] - s["n_steps_off"] == 1
        and abs(s["first_rung_on"] - NYISO_SENY_30MIN_INCREMENT_RCPF) < 1e-9
        and s["base_ramp_penalties_unchanged"]
        and s["increment_band_width_matches_published"]
        and s["base_band_total_matches_published"]
        for s in sc.values()
    )
    # G2: the nyiso-118 identity must SURVIVE in BOTH arms.
    identity_off = [
        cyears[str(y)]["families"][SENY]["hours_totalwidth_ne_requirement_off"]
        for y in YEARS
    ]
    identity_on = [
        cyears[str(y)]["families"][SENY]["hours_totalwidth_ne_requirement_on"]
        for y in YEARS
    ]
    g2_ok = all(v == 0 for v in identity_off) and all(v == 0 for v in identity_on)

    out["gates"] = {
        "G1_increment_tier_live": {
            "pass": bool(g1_ok and seny_price_changed),
            "seny_n_steps": {y: (s["n_steps_off"], s["n_steps_on"]) for y, s in sc.items()},
            "seny_first_rung": {
                y: (s["first_rung_off"], s["first_rung_on"]) for y, s in sc.items()
            },
            "base_ramp_penalties_unchanged": {
                y: s["base_ramp_penalties_unchanged"] for y, s in sc.items()
            },
            "increment_band_width_matches_published": {
                y: s["increment_band_width_matches_published"] for y, s in sc.items()
            },
            "base_band_total_matches_published": {
                y: s["base_band_total_matches_published"] for y, s in sc.items()
            },
            "seny_reachable_price_changed": bool(seny_price_changed),
            "seny_price_never_increases": bool(seny_never_up),
            "source": "construction probe (widths/penalties are not in the sidecar)",
        },
        "G2_nyiso118_identity_survives": {
            "pass": bool(g2_ok),
            "seny_hours_totalwidth_ne_requirement_control": identity_off,
            "seny_hours_totalwidth_ne_requirement_treatment": identity_on,
            "claim": "total step width == requirement_mw in EVERY hour of BOTH arms",
        },
        "G3a_scope_construction": {
            "pass": bool(g3a_ok and scope_widths and scope_pens and scope_reqs),
            "non_seny_widths_identical": bool(scope_widths),
            "non_seny_penalties_identical": bool(scope_pens),
            "non_seny_requirement_identical_construction": bool(scope_reqs),
            "non_seny_requirement_identical_sidecar": bool(g3a_ok),
            "non_seny_reachable_price_identical": bool(scope_price),
        },
        "G3b_frozen_nyc_and_li_undisturbed": {
            "pass": bool(frozen_price_same),
            "families": [*NYC_PAIR, LI30],
        },
        "G3c_ordc_step_count_plus_one": {"pass": g3c_ok, **steps},
        "G4_increment_tier_prices_at_published_40": {
            "pass": bool(g4_ok),
            "years": g4_detail,
        },
        "G5_lp_row_identity": {"pass": bool(g5_ok)},
        "G6_no_feasibility_damage": {"pass": bool(g6_ok)},
    }
    out["kills"] = {
        "K_A_scope_leak": {
            "fired": bool(not (scope_widths and scope_pens and scope_reqs and g3a_ok))
        },
        "K_B_frozen_nyc_or_li_disturbed": {"fired": bool(not frozen_price_same)},
        "K_C_nyiso118_identity_broken": {"fired": bool(not all(v == 0 for v in identity_on))},
        "K_D_base_tier_relevelled": {
            "fired": bool(
                not all(
                    s["base_ramp_penalties_unchanged"]
                    and s["n_steps_on"] - s["n_steps_off"] == 1
                    for s in sc.values()
                )
            )
        },
        "K_E_fitted_level_needed": {
            "fired": False,
            "why": (
                "no number in the mechanism outside the published $40 (ASM §6.8 "
                "item 12), the published 1,300 MW base read from "
                "NYISO_RCPF_LOCATIONAL, and the already-committed measured "
                "hourly series — prereg §2.1"
            ),
        },
        "K_F_feasibility_damage": {"fired": bool(not g6_ok)},
        "K_G_tier_not_reachable": {"fired": bool(not g4_ok)},
    }
    out["all_gates_pass"] = all(g["pass"] for g in out["gates"].values())
    out["any_kill_fired"] = any(k["fired"] for k in out["kills"].values())

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(out, indent=2))

    for k, v in out["gates"].items():
        print(f"{'PASS' if v['pass'] else 'FAIL'}  {k}")
    for k, v in out["kills"].items():
        print(f"{'FIRED' if v['fired'] else 'ok   '} {k}")
    print(f"\nall_gates_pass={out['all_gates_pass']} any_kill={out['any_kill_fired']}")
    for y, d in g4_detail.items():
        print(
            f"  G4 {y}: binding={d['hours_binding_treatment']} "
            f"inside_band={d['hours_shortfall_inside_increment_band']} "
            f"at_$40={d['hours_priced_exactly_at_published_40']} "
            f"deeper={d['hours_shortfall_deeper_than_band']} "
            f"max_dual={d['max_dual_treatment']}"
        )
    print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
