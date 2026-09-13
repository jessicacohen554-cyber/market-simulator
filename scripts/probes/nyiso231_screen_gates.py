"""Score nyiso-231's five pre-registered screen gates on the repaired 2022 arm.

The gates are fixed in ``results/calibration/PRECOMMIT-nyiso231-mirror-repair-rescreen.md``
§6 and this scorer is committed BEFORE the arm's numbers exist, so it cannot be
shaped by them. All five are STRUCTURAL and STOP-ONLY (rule 29 ``[R-SCREEN]``):
none reads C1, C3a, C3b or C3c, and clearing them promotes nothing.

**What changed from nyiso-230's scorer, and why.** nyiso-230's screen STOPPED on
G-CONF and G-PRED, and the cause was a defect in the RECORD, not the mechanism:
``run_calibration_full._recorded_config``'s mirror resolved the per-zone anchors
~144 lines above the block that puts ``gas_hub_basis_overlay`` on the recorded
config, so ``run_config.json`` recorded a uniform ``-1.3868 $/MMBtu`` in every
zone while the LP priced against the correct table. Two repairs are made here,
both pre-registered before this session's solve:

* **G-CONF** waives ONE named benign transition —
  ``miso_import_sil_measured_envelope`` ``None -> False``, a field that did not
  exist when the control's config was serialized and now materializes at its
  dataclass default. It is MISO-only and at ``False``. Nothing else is waived:
  any other field move, including any other ``None -> default``, still STOPS.
* **G-PRED is REPLACED by G-ANCHOR-LOG, which reads the SOLVE PATH rather than
  the record.** nyiso-230's G-PRED read ``run_config.json``'s recorded anchors and
  divided them by the prediction, which made it a RESTATEMENT of G-CONF, not an
  independent test — one defect therefore failed two gates. The obvious repair,
  measuring the offer shift from the LP's own ``unit_hourly.mc``, was BUILT AND
  REJECTED here on measurement, before the solve: P1's ``mc`` is the BID cost
  (base cost plus the amortized startup markup keyed on the run pattern P0
  discovered), so it is not the offer. Measured on nyiso-230's arm against its
  control: **6.44 % of 4,309,920 gas unit-hours carry a NEGATIVE mc delta** where
  every predicted tranche shift is ``>= 0``, and **only 7.7 % of 492 gas units
  have an hour-CONSTANT delta** where the identity says every one must. Both
  violations are the amortization, not the mechanism — and P0's ``mc``, which
  would be clean, is not persisted by any runner flag. So the gate reads the
  resolution INSIDE the solve path instead: the runner's own
  ``gas offer margin ZONAL anchors VINTAGE <year>:`` log line, captured to
  ``solve.log`` in the bundle. That is the artifact nyiso-230 asked its shard for
  and did not get, and it is the direct answer to "which anchor did the LP price
  against".

**Deliberately NOT gated: any non-gas class's mc, and any class's generation.**
For the same reason — P1 ``mc`` is a bid cost, so changing a gas offer
legitimately re-prices a coal committed tranche through a changed P0 pattern
(measured: one unit, 1,416 of 236,520 coal unit-hours, +3.12 $/MWh). The NYISO LP
is intertemporally and globally coupled (cyclic storage SOC, hydro budgets, the
monthly import quota, P0-detected commitment bridges), so out-of-footprint
movement is guaranteed and gating it asks the LP not to be an LP — the gate
nyiso-229 had to withdraw. Conservation is gated on SERVED DEMAND only.

Usage::

    python3 scripts/probes/nyiso231_screen_gates.py \
        --arm results/calibration/nyiso231_arm_y2022 \
        --control results/calibration/nyiso229_arm_y2022 \
        --prior-arm results/calibration/nyiso230_arm_y2022
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

#: PRECOMMIT §5, fixed before the solve: the solve-year per-zone anchors the
#: repaired mirror must record and the LP must price against.
PREDICTED_ANCHORS: dict[str, float] = {
    "Upstate_West": 5.3731,
    "Capital_Hudson": 8.4431,
    "Lower_Hudson": 8.4431,
    "NYC": 6.6631,
    "Long_Island": 8.4431,
}
#: constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["NYISO"], the frozen 2023-2025 table.
FROZEN_ANCHORS: dict[str, float] = {
    "Upstate_West": 2.0346,
    "Capital_Hudson": 3.9046,
    "Lower_Hudson": 3.9046,
    "NYC": 2.7612,
    "Long_Island": 3.9046,
}
#: ``markup_hr = base_HR x max(0, mult - phys)`` from the registered NYISO curve
#: (`pipeline/backcast_config.py::_NYISO_OFFER_CURVE` as recorded in the control
#: bundle). PRECOMMIT §5. Nothing here is fitted: it is the curve's own arithmetic.
CLASS_MARKUP_HR: dict[str, tuple[float, float]] = {
    # class: (min nonzero markup_hr, max markup_hr) over its priced bands
    "CC_REGULAR": (0.5822, 1.2887),
    "CC_CHP": (0.9575, 0.9575),
    "ST_GAS": (2.6535, 33.9648),
    "CT_PEAKER": (4.0497, 35.8380),
}
#: The line the runner logs when it resolves the anchors INSIDE the solve path
#: (``run_calibration.run_year``). G-ANCHOR-LOG greps ``solve.log`` for it.
ANCHOR_LOG_MARKER = "gas offer margin ZONAL anchors VINTAGE"
GAS_FUELS = ("gas_cc", "gas_ct", "gas_st")
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_CHP", "ST_GAS", "ST_CHP", "CT_PEAKER")
BAND_KEYS = (
    "committed",
    "econ_low",
    "econ_high",
    "peak",
    "econ_low_share",
    "pct_peaking",
)
EXPECTED_DELTA_FIELDS = {
    "gas_offer_margin_zonal_anchor_vintage",
    "gas_offer_margin_anchor_by_zone",
}
#: The ONE waived transition, named exactly, with its exact values (see module
#: docstring). A different field, or a different pair of values, still STOPS.
WAIVED_TRANSITIONS: dict[str, tuple[object, object]] = {
    "miso_import_sil_measured_envelope": (None, False),
}
#: nyiso-230's arm, whose LP the repair must reproduce byte-for-byte in effect:
#: `_recorded_config` is write-only (it reaches `write_run_config` and nothing
#: else), so moving the mirror cannot move the solve. G-REPRO is how that claim
#: is made falsifiable rather than asserted.
REPRO_TOL_USD_MWH = 0.01


def _cfg(bundle: Path) -> dict:
    d = json.loads((bundle / "run_config.json").read_text())
    return d.get("scenario_config", d)


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"]


def _lw(df: pd.DataFrame) -> float:
    return float((df["price"] * df["demand"]).sum() / df["demand"].sum())


def _unit_mc(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "plant_group", "fuel", "zone", "hour", "mc"],
    )
    return df[df["pass"] == "P1"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, type=Path)
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--prior-arm", type=Path, default=None)
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument("--json-out", type=Path)
    a = ap.parse_args()

    arm, ctl = _cfg(a.arm), _cfg(a.control)
    out: dict = {"year": a.year, "gates": {}}

    # ---- G-CONF -----------------------------------------------------------
    moved = {k for k in set(arm) | set(ctl) if arm.get(k) != ctl.get(k)}
    waived = {
        k
        for k in moved
        if k in WAIVED_TRANSITIONS
        and (ctl.get(k, "<absent>"), arm.get(k, "<absent>")) == WAIVED_TRANSITIONS[k]
    }
    unexplained = sorted(moved - EXPECTED_DELTA_FIELDS - waived)
    got = arm.get("gas_offer_margin_anchor_by_zone") or {}
    anchor_ok = bool(got) and all(
        abs(float(got.get(z, -1)) - v) < 1e-6 for z, v in PREDICTED_ANCHORS.items()
    )
    out["gates"]["G-CONF"] = {
        "pass": bool(not unexplained and anchor_ok),
        "fields_moved": sorted(moved),
        "waived": sorted(waived),
        "unexplained": unexplained,
        "recorded_anchors": got,
        "predicted_anchors": PREDICTED_ANCHORS,
        "anchors_match_1e-6": anchor_ok,
    }

    # ---- G-SCOPE ----------------------------------------------------------
    a_oc, c_oc = (
        arm.get("offer_curve_by_group") or {},
        ctl.get("offer_curve_by_group") or {},
    )
    band_moves = []
    for grp in sorted(set(a_oc) | set(c_oc)):
        ab, cb = a_oc.get(grp, {}), c_oc.get(grp, {})
        for k in sorted(set(ab) | set(cb)):
            if k in BAND_KEYS or k.startswith("phys_"):
                if ab.get(k) != cb.get(k):
                    band_moves.append(f"{grp}.{k}: {cb.get(k)} -> {ab.get(k)}")
    out["gates"]["G-SCOPE"] = {"pass": not band_moves, "moved": band_moves}

    # ---- G-ANCHOR-LOG (the SOLVE PATH's own resolution) ------------------
    # The record and the solve are computed by two different call sites, and
    # nyiso-230 proved they can disagree. G-CONF checks the record; this checks
    # the solve, by reading the line run_year logs at the moment it resolves.
    log_path = a.arm / "solve.log"
    log_line, log_anchors, log_ok = None, {}, False
    if log_path.exists():
        for raw in log_path.read_text(errors="replace").splitlines():
            if ANCHOR_LOG_MARKER in raw and str(a.year) in raw:
                log_line = raw.strip()
        if log_line:
            for zone, want in PREDICTED_ANCHORS.items():
                hit = re.search(rf"'{zone}':\s*([0-9.]+)", log_line)
                if hit:
                    log_anchors[zone] = float(hit.group(1))
            log_ok = bool(log_anchors) and all(
                abs(log_anchors.get(z, -1) - v) < 5e-4
                for z, v in PREDICTED_ANCHORS.items()
            )
    out["gates"]["G-ANCHOR-LOG"] = {
        "pass": bool(log_ok),
        "solve_log_present": log_path.exists(),
        "log_line": log_line,
        "anchors_logged_by_run_year": log_anchors,
        "predicted_anchors": PREDICTED_ANCHORS,
        "note": (
            "The run_config.json copy of these numbers is computed by a DIFFERENT "
            "call site than the LP's; nyiso-230 recorded them 1.3868 $/MMBtu low "
            "in every zone. This gate reads the solve path's own resolution, so "
            "the two halves are checked independently."
        ),
    }

    # ---- G-DEMAND ---------------------------------------------------------
    sa, sc = _system(a.arm, a.year), _system(a.control, a.year)
    served_a = float(sa["demand"].sum()) - float(sa["slack"].sum())
    served_c = float(sc["demand"].sum()) - float(sc["slack"].sum())
    dump_a = float(sa["dump"].sum())
    out["gates"]["G-DEMAND"] = {
        "pass": bool(
            round(served_a / 1e6, 4) == round(served_c / 1e6, 4) and dump_a == 0.0
        ),
        "served_TWh_arm": round(served_a / 1e6, 6),
        "served_TWh_control": round(served_c / 1e6, 6),
        "dump_MWh_arm": dump_a,
        "slack_MWh_arm": float(sa["slack"].sum()),
        "slack_MWh_control": float(sc["slack"].sum()),
    }

    # ---- G-REPRO ----------------------------------------------------------
    # The mirror repair touches `_recorded_config` only, which is write-only, so
    # the LP must be unmoved. If it IS unmoved, then nyiso-230's arm priced
    # against the anchors THIS run records (8.4431 at Capital_Hudson) -- which
    # settles what that session could not: `run_config.json` was wrong and the LP
    # was right (rule 24 [R-REGISTRY], the FFR-2E class). Reproduction, never a
    # residual: the test is "unchanged", not "improved".
    if a.prior_arm is not None and (a.prior_arm / "hourly").exists():
        sp = _system(a.prior_arm, a.year)
        lw_new, lw_old = _lw(sa), _lw(sp)
        prior_anchor = (
            _cfg(a.prior_arm).get("gas_offer_margin_anchor_by_zone") or {}
        ).get("Capital_Hudson")
        out["gates"]["G-REPRO"] = {
            "pass": bool(abs(lw_new - lw_old) <= REPRO_TOL_USD_MWH),
            "load_weighted_LMP_this_arm": round(lw_new, 4),
            "load_weighted_LMP_nyiso230_arm": round(lw_old, 4),
            "delta": round(lw_new - lw_old, 6),
            "tolerance": REPRO_TOL_USD_MWH,
            "nyiso230_recorded_capital_hudson_anchor": prior_anchor,
            "this_arm_recorded_capital_hudson_anchor": got.get("Capital_Hudson"),
            "settles": (
                "an unmoved LP beside a moved RECORD proves nyiso-230's LP "
                "priced against the overlay-inclusive anchors while its "
                "run_config.json recorded the pre-overlay ones"
            ),
        }
    else:
        out["gates"]["G-REPRO"] = {"pass": None, "note": "prior arm not supplied"}

    # ---- REPORTED, NEVER GATED -------------------------------------------
    ua, uc = _unit_mc(a.arm, a.year), _unit_mc(a.control, a.year)
    m = ua.merge(
        uc[["unit_id", "hour", "mc", "fuel"]],
        on=["unit_id", "hour"],
        suffixes=("_arm", "_ctl"),
    )
    m["d"] = m["mc_arm"] - m["mc_ctl"]
    g = m[(m["fuel_arm"] == m["fuel_ctl"]) & m["fuel_arm"].isin(GAS_FUELS)]
    per_unit = g.groupby("unit_id")["d"]
    nongas = m[~m["plant_group"].isin(GAS_CLASSES)]
    d_anchor = {z: PREDICTED_ANCHORS[z] - FROZEN_ANCHORS[z] for z in PREDICTED_ANCHORS}
    gz = g[g["zone"].isin(d_anchor)].copy()
    gz["implied"] = gz["d"] / gz["zone"].map(d_anchor)
    implied = {
        k: round(float(v), 4)
        for k, v in gz[gz["d"] > 1e-6]
        .groupby("plant_group")["implied"]
        .median()
        .items()
    }
    out["reported_not_gated"] = {
        "load_weighted_LMP_arm": round(_lw(sa), 4),
        "gas_unit_hours": int(len(g)),
        "share_negative_gas_mc_delta": round(float((g["d"] < -1e-6).mean()), 6),
        "share_gas_units_hour_constant_delta": round(
            float(((per_unit.max() - per_unit.min()).abs() < 1e-6).mean()), 4
        ),
        "median_implied_markup_hr_by_class": implied,
        "registered_markup_hr_envelope_by_class": {
            k: [round(lo, 4), round(hi, 4)] for k, (lo, hi) in CLASS_MARKUP_HR.items()
        },
        "nongas_unit_hours_with_moved_mc": int((nongas["d"].abs() > 1e-9).sum()),
        "nongas_unit_hours_total": int(len(nongas)),
        "load_weighted_LMP_control": round(_lw(sc), 4),
        "hours_gt_300_arm": int((sa.groupby("hour")["price"].mean() > 300).sum()),
        "hours_gt_300_control": int((sc.groupby("hour")["price"].mean() > 300).sum()),
        "note": (
            "Reported for the record, NOT gated. Prices: a screen that reads the "
            "target residual is the fitted-mechanism selection rule 1 [R-STRUCT] "
            "forbids, done one year at a time. Non-gas mc: P1's mc is the BID "
            "cost (base + amortized startup markup keyed on P0's run pattern), so "
            "a changed gas offer legitimately re-prices a coal committed tranche "
            "through a changed P0 pattern -- the intertemporal coupling that made "
            "nyiso-229 withdraw its out-of-footprint confinement gate."
        ),
    }

    scored = [g for g in out["gates"].values() if g.get("pass") is not None]
    verdict = all(g["pass"] for g in scored)
    out["screen_verdict"] = (
        "CLEARS (stop-gate only — promotes nothing)" if verdict else "STOP"
    )
    print(json.dumps(out, indent=2))
    if a.json_out:
        a.json_out.write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
