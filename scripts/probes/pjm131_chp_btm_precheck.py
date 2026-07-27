"""pjm-131 no-LP pre-check — can the measured CHP host share arm gate 1?

Charter (pre-registered, committed before this ran):
``docs/handoffs/pjm-131-gate1-arm-charter-2026-07.md``.

Gate 1's target is the 2023 overshoot **against the meter** — CC_CHP +2.54 TWh
(+41 %) and ST_GAS +1.72 TWh (+19 %) against CC_REGULAR −8.10 TWh (band 8.00).

For the gas CHP classes the behind-the-meter host share is a **grid-capacity
pull-out**, not a floor (``offer_curves.plant_cf_bands``: ``pct_mr =
chp_btm_pct(...)``, then ``grid_cap = nameplate × (1 − pct_mr/100)`` with
``mustrun_cap = 0``), and the same share is the bench subtrahend
(``run_calibration_full._btm_frame``). The backcast uses the sector-keyed
**estimate** (``CHP_BTM_PCT_BY_SECTOR``, merchant 35.0 — "residual-identified,
no independent source yet"); the **measured** per-plant ``chp-btm-share``
artifact exists but ``runner.py`` resolves it for forecast years only. Rule 14
``[R-ACCURATE]`` reads on that inversion.

PRE-REGISTERED DECISION RULES (unmet-means-dead; charter §4):

Q1 materiality  ``delta_cap = (s_applied − s_measured)/(1 − s_applied)``,
                capacity-weighted over PJM CC_CHP plants.
                DEAD, no solve, if ``|delta_cap| < 5 %``.

Q2 direction    ``s_measured < s_applied`` ⇒ more grid capacity ⇒ the overshoot
                can only enlarge. Still the accurate input (rule 14), but NOT a
                gate-1 arm: record, root-cause, spend no solve as an arm.

Q3 invariance   ``kappa`` = share of CC_CHP 2023 model energy in hours where the
                class is at ≥99 % of its reconstructed hour-varying grid-facing
                available capacity.
                kappa ≥ 0.80 — capacity-bound: both sides scale by (1 − s), the
                    RELATIVE overshoot is invariant, absolute-TWh lever only.
                kappa ≤ 0.20 — economically dispatched: the model barely responds
                    to the cap while the bench actual falls in full ⇒ the
                    overshoot WORSENS ⇒ REFUTED as a gate-1 arm.
                else — mixed; Q4 decides.

Q4 THE kill    (inherited, pjm-130 charter §5) predicted 2023 overshoot with both
   criterion    sides moved:
                  ``model_new  = model_old × (1 − kappa × delta_cap)``
                  ``actual_new = actual_old × (1 − s_meas)/(1 − s_app)``
                Survives ONLY if ``model_new − actual_new < model_old −
                actual_old`` for CC_CHP. An arm that lifts CC_REGULAR while
                leaving the returned classes above their metered energy is
                displacement-neutral — the refutation signature. Else DEAD.

Nothing here is tuned, and no measured value is fitted to a residual: both
``chp-btm-share`` sides are measured and independent of the model's dispatch, so
the swap regenerates for a forward year (rule 13 ``[R-MEASURED]``).

Usage:
    PYTHONPATH=. .venv/bin/python scripts/probes/pjm131_chp_btm_precheck.py \
        --bundle results/calibration/pjm129_meritguard_a1 --year 2023 \
        --json-out results/calibration/pjm131_chp_btm_precheck.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

#: Gate-1 decision thresholds, charter §4. Never moved to chase a result.
MATERIALITY_MIN = 0.05  # Q1: |delta_cap| below this ⇒ DEAD
KAPPA_BOUND = 0.80  # Q3: at/above ⇒ capacity-bound
KAPPA_ECON = 0.20  # Q3: at/below ⇒ economically dispatched ⇒ REFUTED
CAP_BOUND_TOL = 0.99  # Q3: "at the ceiling" = ≥99 % of available grid capacity

#: The gas CHP classes carrying a BTM pull-out.
CHP_GROUPS = ("CC_CHP", "CT_CHP", "ST_CHP")


def _sys_path() -> None:
    """Put ``scripts/`` and ``scripts/data/`` on the path (bundle_fleet's rule)."""
    import sys

    for p in (REPO, REPO / "scripts", REPO / "scripts" / "data"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/pjm129_meritguard_a1")
    ap.add_argument("--iso", default="PJM")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    _sys_path()
    from market_sim.data.chp import chp_btm_pct, measured_btm_share_by_plant
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    iso = args.iso.upper()
    bundle = Path(args.bundle)
    out: dict = {"iso": iso, "year": args.year, "bundle": str(bundle)}

    measured = measured_btm_share_by_plant(iso)
    print(f"chp-btm-share: {len(measured)} measured plants for {iso}")

    # ---- reconstruct the fleet the bundle actually solved (no LP) ----------
    state, meta = reconstruct_bundle_fleet(bundle, args.year)
    fleet = state["fleet"]
    fa = state["fleet_arrays"]
    groups = np.array([str(g.plant_group) for g in fleet])
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    pcode = np.asarray(fa.plant_code, dtype=int)

    # ---- Q1/Q2: applied vs measured share, capacity-weighted ---------------
    rows = []
    for grp in CHP_GROUPS:
        sel = groups == grp
        if not sel.any():
            continue
        for code in sorted(set(int(c) for c in pcode[sel] if int(c) > 0)):
            m = sel & (pcode == code)
            # Reconstructed grid-facing capacity = nameplate × (1 − s_applied),
            # so nameplate is recovered by dividing it back out.
            s_app = float(chp_btm_pct(code, grp, iso=iso)) / 100.0
            grid_cap = float(pmax[m].sum())
            nameplate = grid_cap / (1.0 - s_app) if s_app < 1.0 else float("nan")
            s_meas = measured.get(code)
            rows.append(
                {
                    "plant_code": code,
                    "group": grp,
                    "grid_cap_mw": grid_cap,
                    "nameplate_mw": nameplate,
                    "s_applied": s_app,
                    "s_measured": None if s_meas is None else float(s_meas),
                }
            )
    df = pd.DataFrame(rows)
    out["n_chp_plants_in_fleet"] = int(len(df))
    out["n_with_measurement"] = int(df["s_measured"].notna().sum()) if len(df) else 0

    def _weighted(sub: pd.DataFrame) -> dict:
        """Capacity-weighted applied/measured share and the implied cap change."""
        have = sub[sub["s_measured"].notna()]
        if have.empty:
            return {"covered_nameplate_mw": 0.0}
        w = have["nameplate_mw"].to_numpy()
        s_app = float(np.average(have["s_applied"], weights=w))
        s_meas = float(np.average(have["s_measured"], weights=w))
        delta_cap = (s_app - s_meas) / (1.0 - s_app) if s_app < 1.0 else float("nan")
        return {
            "covered_nameplate_mw": float(w.sum()),
            "coverage_frac_of_group_nameplate": float(
                w.sum() / sub["nameplate_mw"].sum()
            )
            if sub["nameplate_mw"].sum() > 0
            else 0.0,
            "s_applied_capwt": s_app,
            "s_measured_capwt": s_meas,
            "delta_cap_frac": delta_cap,
        }

    out["by_group"] = {}
    for grp in CHP_GROUPS:
        sub = df[df["group"] == grp]
        if not sub.empty:
            out["by_group"][grp] = _weighted(sub)

    cc = out["by_group"].get("CC_CHP", {})
    delta_cap = cc.get("delta_cap_frac", float("nan"))

    # ---- Q3: is model CC_CHP capacity-bound? ------------------------------
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{args.year}.parquet")
    ch = ch[(ch["klass"] == "CC_CHP") & (ch["pass"] == "P1")].sort_values("hour")
    disp = ch["mw"].to_numpy(dtype=float)
    sel_cc = groups == "CC_CHP"
    # Hour-varying available grid capacity for the class.
    cap_t = (pmax[sel_cc, None] * avail[sel_cc, : disp.size]).sum(axis=0)
    at_ceiling = disp >= CAP_BOUND_TOL * cap_t
    kappa = float(disp[at_ceiling].sum() / disp.sum()) if disp.sum() > 0 else 0.0
    out["kappa_capacity_bound_energy_share"] = kappa
    out["model_cc_chp_twh"] = float(disp.sum() / 1e6)
    out["mean_class_utilization"] = float(disp.sum() / cap_t.sum())

    # ---- Q4: predicted overshoot with BOTH sides moved --------------------
    # Bench actual for the year, as scored (classFull = e923 − btm).
    cand = (
        REPO / "frontend" / "data" / "backcast" / "bench" / iso / f"{args.year}.json.gz"
    )
    actual_old = None
    if cand.exists():
        import gzip

        bench = json.loads(gzip.decompress(cand.read_bytes()).decode())
        # ``classFull`` is nested under the payload's ``bench`` key.
        cf = (bench.get("bench") or {}).get("classFull") or {}
        if "CC_CHP" in cf:
            actual_old = float(cf["CC_CHP"])
    out["actual_cc_chp_twh_bench"] = actual_old

    model_old = out["model_cc_chp_twh"]
    if actual_old is not None and np.isfinite(delta_cap):
        s_app = cc["s_applied_capwt"]
        s_meas = cc["s_measured_capwt"]
        # SIGN CORRECTION, disclosed (finding §4): the charter/docstring wrote
        # ``model_old × (1 − kappa × delta_cap)``, but ``delta_cap`` is defined
        # as the SIGNED relative capacity change ((1−s_meas)/(1−s_app) − 1), so
        # the propagation is ``(1 + kappa × delta_cap)``. Corrected here rather
        # than left to report a wrong number. It changes no verdict: Q3 refutes
        # independently and Q4 is moot while no valid measured share exists.
        model_new = model_old * (1.0 + kappa * delta_cap)
        actual_new = actual_old * (1.0 - s_meas) / (1.0 - s_app)
        out["predicted"] = {
            "model_old_twh": model_old,
            "model_new_twh": model_new,
            "actual_old_twh": actual_old,
            "actual_new_twh": actual_new,
            "overshoot_old_twh": model_old - actual_old,
            "overshoot_new_twh": model_new - actual_new,
        }

    # ---- verdicts, applied exactly as pre-registered ----------------------
    verdicts = {}
    verdicts["Q1_material"] = bool(abs(delta_cap) >= MATERIALITY_MIN)
    # delta_cap is the SIGNED relative capacity change: > 0 means the measured
    # share gives MORE grid capacity (s_meas < s_app) and the overshoot can only
    # enlarge — the charter §4 Q2 "not a gate-1 arm" branch. Renamed from the
    # first draft's ``Q2_direction_reduces_capacity``, which read the sign
    # backwards; the underlying test is unchanged.
    verdicts["Q2_measured_gives_more_grid_capacity"] = bool(delta_cap > 0)
    if kappa >= KAPPA_BOUND:
        verdicts["Q3"] = "CAPACITY-BOUND (absolute-TWh lever only)"
    elif kappa <= KAPPA_ECON:
        verdicts["Q3"] = "ECONOMIC (REFUTED as gate-1 arm)"
    else:
        verdicts["Q3"] = "MIXED (Q4 decides)"
    pred = out.get("predicted")
    if pred is not None:
        verdicts["Q4_overshoot_reduces"] = bool(
            pred["overshoot_new_twh"] < pred["overshoot_old_twh"]
        )
    out["verdicts"] = verdicts

    print(json.dumps(out, indent=2, default=str))
    if args.json_out:
        p = Path(args.json_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2, default=str))
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
