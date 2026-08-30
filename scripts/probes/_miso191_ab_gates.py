"""miso-191 A/B scorer — the binning-aware partial-plant exit-cohort arm.

Implements the PREREG-miso191 §4 gates (the PREREG-miso190 §4 gates re-keyed
to plant/capacity grain — the miso-190 §5.1 vacuous-witness repair; control
``miso191_bax_A``, arm ``miso191_bax_B``, keeper ``miso188_rvs_B`` =
``2026-08-30-miso-188-rvsscope``):

* S-0 CONTROL INERTNESS (ABANDON): every scored sidecar of the control
  value-identical to the committed keeper's.
* S-1 EXACTNESS (KILL): the arm's run_config records exactly the single
  repair delta (``partial_plant_exit_carry=true``), the control none; the
  flag demonstrably acted AT THE LP GRAIN. Every presence witness asserts
  PRESENCE (fails on an empty match set). Witness grains: CAPACITY = the
  per-unit ``dispatch/<year>_P1_fleet.parquet`` listing (unit_id, pmax_mw
  — written by run_calibration_full beside the dispatch frame; the PREREG
  named FleetContext schema metadata as the channel, but the dispatch
  parquet is written as a plain long table without it, so the listing
  carries the SAME frozen quantities — instrument correction, quantities
  unchanged, disclosed); DISPATCH = the long dispatch frame's hourly MW.
  (a) cohort presence + per-cohort pmax within ±2 MW of the exited MW;
  (b) unit-grain exit timing — cohort dispatch exactly 0 after each exit
  month; (c) plant-grain post-exit ceilings (the handoff's primary,
  form-independent); (d) plant survival — 6090 coal > 0 in 2024+2025,
  4041 coal > 0 in Jul-Dec 2024; (e) oracle drops — no r202403 cohort at
  963, no r202301 cohort at 4078; (f) leg-2 capacity deltas — 6055 coal
  +517.0 MW (2023, 2024) / unchanged 2025, 6705 coal +126.4 MW (2023) /
  unchanged 2024+2025; (g) miso-188 regression guard — Grand Tower (862)
  exactly 0 in the arm every year, Rush Island (6155) nonzero BOTH legs
  2023+2024.
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
  any 2023/2024 C3a exit from the +-10% band flagged for the
  owner-escalation path. Promotion additionally requires ZERO gated
  PASS->FAIL flips AND no band exit (PREREG-miso191 §4 promotion rule).

Record: ``results/calibration/_miso191_ab_gates.json``.

Run:
    python3 scripts/probes/_miso191_ab_gates.py
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
CONTROL = REPO / "results/calibration/miso191_bax_A"
ARM = REPO / "results/calibration/miso191_bax_B"
OUT = REPO / "results/calibration/_miso191_ab_gates.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
BAND_PCT = 10.0
S2_MIN_RISE_TWH = 0.50
KILL1_C3A2025_TOL_PP = 0.10
FIELD = "partial_plant_exit_carry"
COAL_CLASSES = ("COAL_PRB", "COAL_BIT", "COAL_LIGNITE", "COAL")

ALL = tuple(range(1, 13))

# (a) Frozen cohorts: {(plant, rtag): exited net-summer MW} (phase-0 census).
COHORTS: dict[tuple[int, str], float] = {
    (994, "r202306"): 421.8,
    (1400, "r202406"): 250.0,
    (1702, "r202305"): 486.0,
    (4014, "r202505"): 186.0,
    (4041, "r202405"): 496.0,
    (6090, "r202312"): 682.0,
    (6137, "r202310"): 485.0,
    (8056, "r202403"): 409.5,
}
CAP_TOL_MW = 2.0

# (b) {(plant, rtag): {year: 1-based months that must be EXACTLY zero}}.
EXIT_ZERO: dict[tuple[int, str], dict[int, tuple[int, ...]]] = {
    (6090, "r202312"): {2024: ALL, 2025: ALL},
    (1702, "r202305"): {2023: tuple(range(6, 13)), 2024: ALL, 2025: ALL},
    (994, "r202306"): {2023: tuple(range(7, 13)), 2024: ALL, 2025: ALL},
    (6137, "r202310"): {2023: (11, 12), 2024: ALL, 2025: ALL},
    (4041, "r202405"): {2024: tuple(range(6, 13)), 2025: ALL},
    (1400, "r202406"): {2024: tuple(range(7, 13)), 2025: ALL},
    (8056, "r202403"): {2024: tuple(range(4, 13)), 2025: ALL},
    (4014, "r202505"): {2025: tuple(range(6, 13))},
}

# (c) Plant-grain post-exit ceilings: (plant, unit-id class prefix,
# {year: months}, ceiling MW) — frozen from the committed operable snapshot
# (phase-0 `witness_ceilings`, net-summer basis).
CEILINGS: tuple[tuple[int, str, dict[int, tuple[int, ...]], float], ...] = (
    (1702, "COAL", {2023: tuple(range(6, 13)), 2024: ALL, 2025: ALL}, 0.0),
    (6137, "COAL", {2023: (11, 12), 2024: ALL, 2025: ALL}, 0.0),
    (6090, "COAL", {2024: ALL, 2025: ALL}, 1556.0),
    (994, "COAL", {2023: tuple(range(7, 13)), 2024: ALL, 2025: ALL}, 1057.2),
    (4041, "COAL", {2024: tuple(range(6, 13)), 2025: ALL}, 616.0),
    (1400, "ST_GAS", {2024: tuple(range(7, 13)), 2025: ALL}, 0.0),
    (8056, "ST_GAS", {2024: tuple(range(4, 13)), 2025: ALL}, 417.3),
    (4014, "CT_PEAKER", {2025: tuple(range(6, 13))}, 0.0),
)
CEIL_TOL_MW = 0.001

# (e) Oracle-dropped units must have NO cohort in the arm.
ORACLE_DROP_TAGS = ((963, "r202403"), (4078, "r202301"))

# (f) Leg-2 capacity deltas (coal pmax sum, arm - control).
LEG2_DELTAS = {
    6055: {2023: 517.0, 2024: 517.0, 2025: 0.0},
    6705: {2023: 126.4, 2024: 0.0, 2025: 0.0},
}
LEG2_TOL_ON_MW = 2.0
LEG2_TOL_OFF_MW = 0.5

GRAND_TOWER = 862
RUSH_ISLAND = 6155


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


def _fleet_listing(bundle: Path, year: int) -> pd.DataFrame | None:
    fp = bundle / "dispatch" / f"{year}_P1_fleet.parquet"
    if not fp.exists():
        return None
    return pd.read_parquet(fp)


def _cohort_ids(ids, plant: int, rtag: str) -> set[str]:
    tok = f"_p{plant}_{rtag}_"
    return {u for u in ids if tok in u}


def _plant_tech_mask(uids: pd.Series, plant: int, prefix: str) -> pd.Series:
    tok = f"_p{plant}_"
    return uids.str.startswith(prefix) & uids.str.contains(tok, regex=False)


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
    fleets = {
        (leg, y): _fleet_listing(b, y)
        for leg, b in (("control", CONTROL), ("arm", ARM))
        for y in YEARS
    }
    have = all(f is not None for f in frames.values()) and all(
        f is not None for f in fleets.values()
    )

    def unit_ids(leg: str, year: int) -> set[str]:
        f = fleets[(leg, year)]
        return set() if f is None else set(f["unit_id"].astype(str))

    def cohort_pmax(leg: str, year: int, plant: int, rtag: str) -> float:
        f = fleets[(leg, year)]
        if f is None:
            return float("nan")
        ids = f["unit_id"].astype(str)
        return float(f.loc[ids.isin(_cohort_ids(ids, plant, rtag)), "pmax_mw"].sum())

    def coal_pmax(leg: str, year: int, plant: int) -> float:
        f = fleets[(leg, year)]
        if f is None:
            return float("nan")
        ids = f["unit_id"].astype(str)
        return float(f.loc[_plant_tech_mask(ids, plant, "COAL"), "pmax_mw"].sum())

    def cohort_month_mwh(year: int, plant: int, rtag: str, month_set) -> float:
        f = frames[("arm", year)]
        ids = f["unit_id"].astype(str)
        sub = f[ids.isin(_cohort_ids(set(ids), plant, rtag))]
        if sub.empty:
            return 0.0
        m = months[sub["hour"].to_numpy(dtype=int)]
        return float(sub["mw"].to_numpy(dtype=float)[np.isin(m, month_set)].sum())

    def plant_tech_max_mw(year: int, plant: int, prefix: str, month_set) -> float:
        f = frames[("arm", year)]
        sub = f[_plant_tech_mask(f["unit_id"].astype(str), plant, prefix)]
        if sub.empty:
            return 0.0
        m = months[sub["hour"].to_numpy(dtype=int)]
        sub = sub[np.isin(m, month_set)]
        if sub.empty:
            return 0.0
        return float(sub.groupby("hour", observed=True)["mw"].sum().max())

    def plant_mwh(leg: str, year: int, plant: int, month_set=None) -> float:
        f = frames[(leg, year)]
        sub = f[f["plant_code"] == plant]
        if sub.empty:
            return 0.0
        if month_set is None:
            return float(sub["mw"].sum())
        m = months[sub["hour"].to_numpy(dtype=int)]
        return float(sub["mw"].to_numpy(dtype=float)[np.isin(m, month_set)].sum())

    def plant_tech_mwh(year: int, plant: int, prefix: str, month_set=None) -> float:
        f = frames[("arm", year)]
        sub = f[_plant_tech_mask(f["unit_id"].astype(str), plant, prefix)]
        if sub.empty:
            return 0.0
        if month_set is None:
            return float(sub["mw"].sum())
        m = months[sub["hour"].to_numpy(dtype=int)]
        return float(sub["mw"].to_numpy(dtype=float)[np.isin(m, month_set)].sum())

    wit: dict = {}

    # (a) Cohort presence + capacity, every year; absent from the control.
    a_ok = have
    wit["cohorts"] = {}
    for (plant, rtag), mw in COHORTS.items():
        rec: dict = {}
        for y in YEARS:
            arm_ids = _cohort_ids(unit_ids("arm", y), plant, rtag)
            ctl_ids = _cohort_ids(unit_ids("control", y), plant, rtag)
            pm = cohort_pmax("arm", y, plant, rtag)
            rec[str(y)] = {
                "arm_n_units": len(arm_ids),
                "control_n_units": len(ctl_ids),
                "arm_pmax_mw": round(pm, 3) if pm == pm else None,
            }
            if have:
                a_ok &= (
                    len(arm_ids) > 0
                    and len(ctl_ids) == 0
                    and abs(pm - mw) <= CAP_TOL_MW
                )
        wit["cohorts"][f"p{plant}_{rtag}"] = rec

    # (b) Exit timing — cohort dispatch exactly 0 after the exit month.
    b_ok = have
    wit["exit_zero_mwh"] = {}
    for (plant, rtag), spec in EXIT_ZERO.items():
        rec = {}
        for y, mset in spec.items():
            v = cohort_month_mwh(y, plant, rtag, mset) if have else None
            rec[str(y)] = v
            if have:
                b_ok &= v == 0.0
        wit["exit_zero_mwh"][f"p{plant}_{rtag}"] = rec

    # (c) Plant-grain post-exit ceilings (max hourly same-tech MW).
    c_ok = have
    wit["post_exit_ceiling_max_mw"] = {}
    for plant, prefix, spec, ceiling in CEILINGS:
        rec = {"ceiling_mw": ceiling}
        for y, mset in spec.items():
            v = plant_tech_max_mw(y, plant, prefix, mset) if have else None
            rec[str(y)] = v
            if have:
                c_ok &= v <= ceiling + CEIL_TOL_MW
        wit["post_exit_ceiling_max_mw"][f"p{plant}_{prefix}"] = rec

    # (d) Plant survival.
    d_ok = have and (
        plant_tech_mwh(2024, 6090, "COAL") > 0.0
        and plant_tech_mwh(2025, 6090, "COAL") > 0.0
        and plant_tech_mwh(2024, 4041, "COAL", tuple(range(7, 13))) > 0.0
    )
    wit["survival"] = {
        "6090_coal_arm_2024_mwh": plant_tech_mwh(2024, 6090, "COAL") if have else None,
        "6090_coal_arm_2025_mwh": plant_tech_mwh(2025, 6090, "COAL") if have else None,
        "4041_coal_arm_2024_jul_dec_mwh": (
            plant_tech_mwh(2024, 4041, "COAL", tuple(range(7, 13))) if have else None
        ),
    }

    # (e) Oracle drops — no cohort for the dropped units.
    e_ok = have and all(
        len(_cohort_ids(unit_ids("arm", y), plant, rtag)) == 0
        for plant, rtag in ORACLE_DROP_TAGS
        for y in YEARS
    )

    # (f) Leg-2 capacity deltas at plant-coal grain.
    f_ok = have
    wit["leg2_coal_pmax_mw"] = {}
    for plant, spec in LEG2_DELTAS.items():
        rec = {}
        for y, want in spec.items():
            ca = coal_pmax("control", y, plant)
            aa = coal_pmax("arm", y, plant)
            rec[str(y)] = {
                "control": round(ca, 3) if ca == ca else None,
                "arm": round(aa, 3) if aa == aa else None,
                "want_delta": want,
            }
            if have:
                tol = LEG2_TOL_ON_MW if want > 0.0 else LEG2_TOL_OFF_MW
                f_ok &= abs((aa - ca) - want) <= tol
        wit["leg2_coal_pmax_mw"][str(plant)] = rec

    # (g) miso-188 regression guard.
    gt_ok = have and all(plant_mwh("arm", y, GRAND_TOWER) == 0.0 for y in YEARS)
    rush_ok = have and all(
        plant_mwh(leg, y, RUSH_ISLAND) > 0.0
        for leg in ("control", "arm")
        for y in (2023, 2024)
    )
    wit["regression_guard"] = {
        "862_arm": {
            str(y): plant_mwh("arm", y, GRAND_TOWER) if have else None for y in YEARS
        },
        "6155": {
            leg: {
                str(y): plant_mwh(leg, y, RUSH_ISLAND) if have else None
                for y in (2023, 2024)
            }
            for leg in ("control", "arm")
        },
    }
    # Reported, never gated.
    wit["reported_only"] = {
        "8056_r202403_arm_2023_mwh": (
            cohort_month_mwh(2023, 8056, "r202403", ALL) if have else None
        ),
        "4014_wheaton6_note": "oil unit ret 2024-01 rides its own small cohort/raw "
        "path; reported via the plant CT ceiling only",
    }

    return {
        "gate": "S-1",
        "arm_flag": sc_b,
        "control_flag": sc_a,
        "witnesses": wit,
        "have_all_frames": bool(have),
        "cohort_presence_capacity_ok": bool(a_ok),
        "exit_timing_ok": bool(b_ok),
        "post_exit_ceilings_ok": bool(c_ok),
        "plant_survival_ok": bool(d_ok),
        "oracle_drops_ok": bool(e_ok),
        "leg2_capacity_ok": bool(f_ok),
        "grand_tower_still_zero_ok": bool(gt_ok),
        "rush_island_ok": bool(rush_ok),
        "passed": bool(
            delta_ok
            and a_ok
            and b_ok
            and c_ok
            and d_ok
            and e_ok
            and f_ok
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
    """The scored 2023 coal-side C1 records (COAL_BIT + COAL_PRB [+ others])."""
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
    kill_2025 = bool(
        abs(c3a_a.get(2025, 0.0)) > abs(c3a_c.get(2025, 0.0)) + KILL1_C3A2025_TOL_PP
    )
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
        "prereg": "PREREG-miso191-binning-aware-exit-2026-08-30.md §4",
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
        {
            k: out["S1"][k]
            for k in (
                "cohort_presence_capacity_ok",
                "exit_timing_ok",
                "post_exit_ceilings_ok",
                "plant_survival_ok",
                "oracle_drops_ok",
                "leg2_capacity_ok",
                "grand_tower_still_zero_ok",
                "rush_island_ok",
            )
        },
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
                "PROMOTE per PREREG-miso191 §4 (all gates clean, zero "
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
