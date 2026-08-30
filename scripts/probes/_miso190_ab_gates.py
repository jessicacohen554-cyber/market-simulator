"""miso-190 A/B scorer — the partial-plant mid-window exit carry arm.

Implements the PREREG-miso190 §4 gates (the PREREG-miso188 §4 gates verbatim
where they apply, re-keyed to this lever's structure and the miso-188
baselines; control ``miso190_ppx_A``, arm ``miso190_ppx_B``, keeper
``miso188_rvs_B`` = ``2026-08-30-miso-188-rvsscope``):

* S-0 CONTROL INERTNESS (ABANDON): every scored sidecar of the control
  value-identical to the committed keeper's.
* S-1 EXACTNESS (KILL): the arm's run_config records exactly the single
  repair delta (``partial_plant_exit_carry=true``), the control none; the
  flag demonstrably acted (frozen witnesses, PREREG-miso190 §4, unit ids
  ``{plant_id}_{generator_id}`` from the legs' dispatch parquets):
  (a) the leg-1 injection set present in the arm every year, absent from
  the control every year; (b) unit-grain exit timing — dispatch exactly 0
  in every hour after each unit's actual retirement month (month mapping =
  the COD ramp's own non-leap ``_hour_to_month_index``); (c) plant
  survival — Sherco (6090) dispatches > 0 in the arm in 2024 AND 2025 and
  South Oak Creek (4041) in Jul–Dec 2024, in the same LP that zeroed their
  retired siblings; (d) oracle drops — Dallman-3 (963_3) and Weston-2
  (4078_2) absent from the arm; (e) leg-2 scope — Big Cajun 2-1 (6055_1)
  present 2023+2024 / absent 2025, Warrick-2 (6705_2) present 2023 only;
  (f) miso-188 regression guard — Grand Tower (862) exactly 0 in the arm
  every year, Rush Island (6155) nonzero in BOTH legs 2023+2024.
* S-2 STRUCTURE: the arm's 2023 combined coal-class energy (P1
  class_hourly, COAL_PRB + COAL_BIT + COAL_LIGNITE + any bare COAL row)
  exceeds the control's by >= 0.50 TWh.
* CHARTER KILLS (both REJECT regardless of every other number):
  (1) C3a-2025 regress — |arm C3a-2025| > |control C3a-2025| + 0.10 pp;
  (2) identification integrity — the scored 2023 coal-side C1 improves
  while any S-1 clause failed (an unidentified level lever).
* S-4 CONDUCT (KILL): zero D-4 conduct FAILs on the arm's regenerated
  legitimacy_diagnostics.json, zero NEW vs the control; C8 not FAIL.
* S-5 FULL-MAGNITUDE SCORING (report + escalation, NOT a kill):
  calibration_verdict --json on both legs; every criterion status flip and
  any 2023/2024 C3a exit from the +-10% band (the miso-188 instrument's
  frozen commercial band) flagged for the owner-escalation path. Promotion
  additionally requires ZERO gated PASS->FAIL flips AND no band exit
  (PREREG-miso190 §4 promotion rule).

Record: ``results/calibration/_miso190_ab_gates.json``.

Run:
    python3 scripts/probes/_miso190_ab_gates.py
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

KEEPER = REPO / "results/calibration/miso188_rvs_B"
CONTROL = REPO / "results/calibration/miso190_ppx_A"
ARM = REPO / "results/calibration/miso190_ppx_B"
OUT = REPO / "results/calibration/_miso190_ab_gates.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
BAND_PCT = 10.0
S2_MIN_RISE_TWH = 0.50
KILL1_C3A2025_TOL_PP = 0.10
FIELD = "partial_plant_exit_carry"
COAL_CLASSES = ("COAL_PRB", "COAL_BIT", "COAL_LIGNITE", "COAL")

# Frozen S-1 witnesses (PREREG-miso190 §4). Leg-1 units: present in the arm
# every year (the channel injects all years; the COD ramp zeroes post-exit).
INJ_UNITS = (
    "6090_2",
    "1702_1A",
    "1702_1B",
    "1702_2A",
    "1702_2B",
    "994_ST2",
    "6137_1",
    "6137_2",
    "4041_5",
    "4041_6",
    "1400_3",
    "8056_1",
)
# {unit_id: {year: 1-based months that must be EXACTLY zero in the arm}}.
ALL = tuple(range(1, 13))
EXIT_ZERO: dict[str, dict[int, tuple[int, ...]]] = {
    "6090_2": {2024: ALL, 2025: ALL},  # ret 2023-12
    "1702_1A": {2023: tuple(range(6, 13)), 2024: ALL, 2025: ALL},  # ret 2023-05
    "1702_1B": {2023: tuple(range(6, 13)), 2024: ALL, 2025: ALL},
    "1702_2A": {2023: tuple(range(6, 13)), 2024: ALL, 2025: ALL},
    "1702_2B": {2023: tuple(range(6, 13)), 2024: ALL, 2025: ALL},
    "994_ST2": {2023: tuple(range(7, 13)), 2024: ALL, 2025: ALL},  # ret 2023-06
    "6137_1": {2023: (11, 12), 2024: ALL, 2025: ALL},  # ret 2023-10
    "6137_2": {2023: (11, 12), 2024: ALL, 2025: ALL},
    "4041_5": {2024: tuple(range(6, 13)), 2025: ALL},  # ret 2024-05
    "4041_6": {2024: tuple(range(6, 13)), 2025: ALL},
    "1400_3": {2024: tuple(range(7, 13)), 2025: ALL},  # ret 2024-06
    "8056_1": {2024: tuple(range(4, 13)), 2025: ALL},  # ret 2024-03
}
ORACLE_DROPS = ("963_3", "4078_2")  # absent from the arm every year
LEG2_PRESENT = {"6055_1": (2023, 2024), "6705_2": (2023,)}
LEG2_ABSENT = {"6055_1": (2025,), "6705_2": (2024, 2025)}
GRAND_TOWER = 862  # exactly 0 in the arm every year (miso-188 drops persist)
RUSH_ISLAND = 6155  # nonzero BOTH legs 2023+2024


def _month_index() -> np.ndarray:
    from market_sim.data.fleet.models import _hour_to_month_index

    return _hour_to_month_index(HOURS) + 1  # 1-based


def identity(control: Path, keeper: Path) -> dict:
    """S-0 — every scored sidecar of every year value-identical."""
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
        worst = 0.0
        nonnum_ok = True
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


def _unit_frame(bundle: Path, year: int) -> pd.DataFrame | None:
    dp = bundle / "dispatch" / f"{year}_P1.parquet"
    if not dp.exists():
        return None
    return pd.read_parquet(dp, columns=["unit_id", "plant_code", "hour", "mw"])


def s1_exactness() -> dict:
    """S-1 — the single-delta config + the flag demonstrably acted."""
    rc_a = json.loads((CONTROL / "run_config.json").read_text())
    rc_b = json.loads((ARM / "run_config.json").read_text())
    sc_a = (rc_a.get("scenario_config") or {}).get(FIELD)
    sc_b = (rc_b.get("scenario_config") or {}).get(FIELD)
    delta_ok = bool(sc_b) and not bool(sc_a)

    months = _month_index()
    frames = {
        (leg, y): _unit_frame(b, y)
        for leg, b in (("control", CONTROL), ("arm", ARM))
        for y in YEARS
    }
    have = all(f is not None for f in frames.values())

    def units(leg: str, year: int) -> set[str]:
        f = frames[(leg, year)]
        return set() if f is None else set(f["unit_id"].astype(str).unique())

    def unit_mwh(leg: str, year: int, uid: str) -> float:
        f = frames[(leg, year)]
        return float(f.loc[f["unit_id"].astype(str) == uid, "mw"].sum())

    def unit_month_mwh(leg: str, year: int, uid: str, month_set) -> float:
        f = frames[(leg, year)]
        sub = f[f["unit_id"].astype(str) == uid]
        if sub.empty:
            return 0.0
        m = months[sub["hour"].to_numpy(dtype=int)]
        return float(sub["mw"].to_numpy(dtype=float)[np.isin(m, month_set)].sum())

    def plant_mwh(leg: str, year: int, plant: int, month_set=None) -> float:
        f = frames[(leg, year)]
        sub = f[f["plant_code"] == plant]
        if sub.empty:
            return 0.0
        if month_set is None:
            return float(sub["mw"].sum())
        m = months[sub["hour"].to_numpy(dtype=int)]
        return float(sub["mw"].to_numpy(dtype=float)[np.isin(m, month_set)].sum())

    wit: dict = {"present": {}, "exit_zero_mwh": {}, "plant_mwh": {}}
    inj_ok = have
    for uid in INJ_UNITS:
        wit["present"][uid] = {
            str(y): {
                "arm": uid in units("arm", y),
                "control": uid in units("control", y),
            }
            for y in YEARS
        }
        if have:
            inj_ok &= all(
                wit["present"][uid][str(y)]["arm"]
                and not wit["present"][uid][str(y)]["control"]
                for y in YEARS
            )

    exit_ok = have
    for uid, spec in EXIT_ZERO.items():
        wit["exit_zero_mwh"][uid] = {}
        for y, mset in spec.items():
            v = unit_month_mwh("arm", y, uid, mset) if have else None
            wit["exit_zero_mwh"][uid][str(y)] = v
            if have:
                exit_ok &= v == 0.0

    surv_ok = have and (
        plant_mwh("arm", 2024, 6090) > 0.0
        and plant_mwh("arm", 2025, 6090) > 0.0
        and plant_mwh("arm", 2024, 4041, tuple(range(7, 13))) > 0.0
    )
    wit["plant_mwh"]["survival"] = {
        "6090_arm_2024": plant_mwh("arm", 2024, 6090) if have else None,
        "6090_arm_2025": plant_mwh("arm", 2025, 6090) if have else None,
        "4041_arm_2024_jul_dec": (
            plant_mwh("arm", 2024, 4041, tuple(range(7, 13))) if have else None
        ),
    }

    drops_ok = have and all(
        uid not in units("arm", y) for uid in ORACLE_DROPS for y in YEARS
    )

    leg2_ok = have
    for uid, ys in LEG2_PRESENT.items():
        for y in ys:
            leg2_ok &= uid in units("arm", y) and uid not in units("control", y)
    for uid, ys in LEG2_ABSENT.items():
        for y in ys:
            leg2_ok &= uid not in units("arm", y)
    leg2_ok = have and all(
        uid not in units("control", y) for uid in LEG2_PRESENT for y in YEARS
    ) and leg2_ok

    gt_ok = have and all(plant_mwh("arm", y, GRAND_TOWER) == 0.0 for y in YEARS)
    rush_ok = have and all(
        plant_mwh(leg, y, RUSH_ISLAND) > 0.0
        for leg in ("control", "arm")
        for y in (2023, 2024)
    )
    wit["plant_mwh"]["regression_guard"] = {
        "862_arm": {str(y): plant_mwh("arm", y, GRAND_TOWER) if have else None for y in YEARS},
        "6155": {
            leg: {str(y): plant_mwh(leg, y, RUSH_ISLAND) if have else None for y in (2023, 2024)}
            for leg in ("control", "arm")
        },
    }
    # Reported, never gated: the accepted-miss and small-tail dispatch.
    wit["reported_only"] = {
        "8056_1_arm_2023_mwh": unit_mwh("arm", 2023, "8056_1") if have else None,
        "6055_1_arm_mwh": {
            str(y): unit_mwh("arm", y, "6055_1") if have else None for y in (2023, 2024)
        },
        "6705_2_arm_2023_mwh": unit_mwh("arm", 2023, "6705_2") if have else None,
    }

    return {
        "gate": "S-1",
        "arm_flag": sc_b,
        "control_flag": sc_a,
        "witnesses": wit,
        "have_all_frames": bool(have),
        "injection_ok": bool(inj_ok),
        "exit_timing_ok": bool(exit_ok),
        "plant_survival_ok": bool(surv_ok),
        "oracle_drops_ok": bool(drops_ok),
        "leg2_scope_ok": bool(leg2_ok),
        "grand_tower_still_zero_ok": bool(gt_ok),
        "rush_island_ok": bool(rush_ok),
        "passed": bool(
            delta_ok
            and inj_ok
            and exit_ok
            and surv_ok
            and drops_ok
            and leg2_ok
            and gt_ok
            and rush_ok
        ),
    }


def _coal_energy_twh(bundle: Path, year: int) -> float:
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch["klass"].astype(str).isin(COAL_CLASSES))]
    return float(ch["mw"].sum()) / 1e6


def s2_structure() -> dict:
    """S-2 — arm 2023 combined coal-class energy rises >= 0.50 TWh vs control."""
    out: dict = {"gate": "S-2", "years": {}}
    for year in YEARS:
        out["years"][str(year)] = {
            "control_coal_twh": round(_coal_energy_twh(CONTROL, year), 4),
            "arm_coal_twh": round(_coal_energy_twh(ARM, year), 4),
        }
    c = out["years"]["2023"]["control_coal_twh"]
    a = out["years"]["2023"]["arm_coal_twh"]
    out["rise_2023_twh"] = round(a - c, 4)
    out["passed"] = bool((a - c) >= S2_MIN_RISE_TWH)
    return out


def _verdict_json(bundle: Path) -> dict:
    res = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "calibration_verdict.py"),
            "--json",
            str(bundle),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if not res.stdout.strip():
        raise SystemExit(
            f"calibration_verdict.py produced no JSON for {bundle}: {res.stderr[-800:]}"
        )
    return json.loads(res.stdout)


def _d4_fail_keys(bundle: Path) -> set[tuple]:
    led = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    out = set()
    for r in ((led.get("diagnostics") or {}).get("D4") or {}).get("rows", []) or []:
        if str(r.get("verdict", "pass")).lower() != "pass":
            out.add((r.get("year"), r.get("check"), r.get("floor"), r.get("plant")))
    return out


def _crit_status(verdict: dict) -> dict:
    out = {}
    for name, block in (verdict.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            out[f"{rec.get('criterion', name)}|{rec.get('key')}|{rec.get('year')}"] = (
                rec.get("status")
            )
    return out


def _c1_coal_2023(verdict: dict) -> dict:
    """The scored 2023 coal-side C1 records (COAL_BIT + COAL_PRB [+ COAL_LIGNITE])."""
    out: dict = {"records": {}, "sum_abs_err_twh": None}
    tot = 0.0
    n = 0
    for rec in verdict["criteria"]["fuelmix"]["records"]:
        if rec.get("year") == 2023 and str(rec.get("key", "")).startswith("COAL"):
            err = round(float(rec["model"]) - float(rec["actual"]), 4)
            out["records"][rec["key"]] = {"err_twh": err, "status": rec.get("status")}
            tot += abs(err)
            n += 1
    if n:
        out["sum_abs_err_twh"] = round(tot, 4)
    return out


def _c3a(verdict: dict) -> dict:
    out = {}
    for rec in verdict["criteria"]["price_mean"]["records"]:
        if rec.get("benchmark") == "RT" and rec.get("key") is None:
            m, a = float(rec["model"]), float(rec["actual"])
            out[int(rec["year"])] = 100.0 * (m - a) / a
    return out


def s4_s5(s1_passed: bool) -> dict:
    out: dict = {}
    d4_c, d4_a = _d4_fail_keys(CONTROL), _d4_fail_keys(ARM)
    vc, va = _verdict_json(CONTROL), _verdict_json(ARM)
    c3a_c, c3a_a = _c3a(vc), _c3a(va)
    sc, sa = _crit_status(vc), _crit_status(va)
    flips = {
        k: f"{sc.get(k)} -> {sa.get(k)}"
        for k in set(sc) | set(sa)
        if sc.get(k) != sa.get(k)
    }
    bad_flips = {
        k: v for k, v in flips.items() if sc.get(k) == "PASS" and sa.get(k) == "FAIL"
    }
    c8_ok = (va["criteria"].get("forced_share") or {}).get("status") != "FAIL"
    out["S4"] = {
        "gate": "S-4",
        "d4_fail_control": sorted(map(list, d4_c)),
        "d4_fail_arm": sorted(map(list, d4_a)),
        "new_d4_fails": sorted(map(list, d4_a - d4_c)),
        "c8_arm_not_fail": c8_ok,
        "passed": bool(len(d4_a) == 0 and len(d4_a - d4_c) == 0 and c8_ok),
    }
    band_exit = {
        y: abs(c3a_a.get(y, 99.0)) > BAND_PCT and abs(c3a_c.get(y, 99.0)) <= BAND_PCT
        for y in (2023, 2024)
    }
    coal_c, coal_a = _c1_coal_2023(vc), _c1_coal_2023(va)
    # Charter kill 1: C3a-2025 regress beyond tolerance.
    kill_2025 = bool(
        abs(c3a_a.get(2025, 0.0)) > abs(c3a_c.get(2025, 0.0)) + KILL1_C3A2025_TOL_PP
    )
    # Charter kill 2: coal C1 improves while the flag did not act as specified.
    coal_improves = bool(
        coal_c["sum_abs_err_twh"] is not None
        and coal_a["sum_abs_err_twh"] is not None
        and coal_a["sum_abs_err_twh"] < coal_c["sum_abs_err_twh"]
    )
    kill_ident = bool(coal_improves and not s1_passed)
    out["S5"] = {
        "gate": "S-5 (report + escalation, not a kill)",
        "c3a_control_pct": {y: round(v, 4) for y, v in c3a_c.items()},
        "c3a_arm_pct": {y: round(v, 4) for y, v in c3a_a.items()},
        "c1_coal_2023_control": coal_c,
        "c1_coal_2023_arm": coal_a,
        "criterion_status_flips": flips,
        "pass_to_fail_flips": bad_flips,
        "band_exit_2023_2024": band_exit,
        "determination_control": vc.get("determination"),
        "determination_arm": va.get("determination"),
        "escalation_fires": bool(bad_flips or any(band_exit.values())),
    }
    out["charter_kill_c3a2025_fires"] = kill_2025
    out["charter_kill_identification_fires"] = kill_ident
    out["_coal_c1_2023_improves"] = coal_improves
    return out


def main() -> dict:
    out: dict = {
        "prereg": "PREREG-miso190-partial-plant-exit-carry-2026-08-30.md §4",
        "keeper": "2026-08-30-miso-188-rvsscope",
        "control": CONTROL.name,
        "arm": ARM.name,
    }
    out["S0"] = identity(CONTROL, KEEPER)
    print("S-0", "PASS" if out["S0"]["passed"] else "FAIL", flush=True)
    if not out["S0"]["passed"]:
        out["verdict"] = "ABANDON (S-0 HEAD drift)"
        OUT.write_text(json.dumps(out, indent=1))
        return out
    out["S1"] = s1_exactness()
    print(
        "S-1",
        "PASS" if out["S1"]["passed"] else "FAIL",
        {k: out["S1"][k] for k in (
            "injection_ok",
            "exit_timing_ok",
            "plant_survival_ok",
            "oracle_drops_ok",
            "leg2_scope_ok",
            "grand_tower_still_zero_ok",
            "rush_island_ok",
        )},
        flush=True,
    )
    out["S2"] = s2_structure()
    print(
        "S-2",
        "PASS" if out["S2"]["passed"] else "FAIL",
        f"coal 2023 rise {out['S2']['rise_2023_twh']:+.4f} TWh",
        out["S2"]["years"],
        flush=True,
    )
    out.update(s4_s5(out["S1"]["passed"]))
    print("S-4", "PASS" if out["S4"]["passed"] else "FAIL", flush=True)
    print("S-5", json.dumps(out["S5"], indent=1), flush=True)
    if out["charter_kill_c3a2025_fires"]:
        out["verdict"] = "REJECT (charter kill 1: C3a-2025 regressed beyond 0.10 pp)"
    elif out["charter_kill_identification_fires"]:
        out["verdict"] = "REJECT (charter kill 2: unidentified level lever)"
    elif not out["S1"]["passed"] or not out["S4"]["passed"]:
        out["verdict"] = "REJECT (kill gate failed)"
    elif out["S2"]["passed"]:
        if out["S5"]["pass_to_fail_flips"] or any(
            out["S5"]["band_exit_2023_2024"].values()
        ):
            out["verdict"] = (
                "STRUCTURAL PASS (S-1 + S-2); OWNER ESCALATION "
                "(PASS->FAIL flip or C3a band exit)"
            )
        else:
            out["verdict"] = (
                "PROMOTE per PREREG-miso190 §4 (all gates clean, zero "
                "PASS->FAIL flips, no band exit)"
            )
    else:
        out["verdict"] = "MIXED (S-1 clean, S-2 silent) -> cell I; owner escalation"
    print("VERDICT:", out["verdict"], flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
