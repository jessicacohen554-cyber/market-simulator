"""miso-188 A/B scorer — the retiree-channel vintage-status scope arm.

Implements the PREREG-miso188 §4 gates (the PREREG-miso184 §6 gates verbatim
where they apply, re-keyed to this lever's structure; control
``miso188_rvs_A``, arm ``miso188_rvs_B``, keeper ``miso187_nuc_B`` =
``2026-08-26-miso-187-nucavail``):

* S-0 CONTROL INERTNESS (ABANDON): every scored sidecar of the control
  value-identical to the committed keeper's.
* S-1 EXACTNESS (KILL): the arm's run_config records exactly the single
  repair delta (``retiree_vintage_status_scope=true``), the control none;
  the flag demonstrably acted (frozen witnesses, PREREG-miso188 §4):
  (a) Grand Tower (862) total dispatch > 0 in the CONTROL in 2023 and 2024
  and exactly 0 in the ARM in both; (b) Carl Bailey (202), Baxter Wilson
  (2050) and Taconite Harbor (10075) each have arm dispatch exactly 0 in
  every year (control values reported, never gated); (c) Rush Island
  (6155) has nonzero dispatch in BOTH legs in 2023 and 2024 (keep-side
  witness); (d) Lansing (1047) nonzero in BOTH legs in 2023 (the accepted
  miss, unchanged by construction).
* S-2 STRUCTURE: the arm's 2024 CC_REGULAR class energy (P1 class_hourly)
  falls below the control's by >= 0.10 TWh.
* CHARTER KILL: an arm whose scored C1 CC_REGULAR-2024 improves while S-1
  shows the flag did not act as specified is an unidentified level lever ->
  REJECTED.
* S-4 CONDUCT (KILL): zero D-4 conduct FAILs on the arm's regenerated
  legitimacy_diagnostics.json, zero NEW vs the control; C8 PASS all years.
* S-5 FULL-MAGNITUDE SCORING (report + escalation, NOT a kill):
  calibration_verdict --json on both legs; every criterion status flip and
  any 2023/2024 C3a exit from the +-10% band flagged for the
  owner-escalation path. Promotion additionally requires ZERO gated
  PASS->FAIL flips (PREREG-miso188 §4 promotion rule).

Record: ``results/calibration/_miso188_ab_gates.json``.

Run:
    python3 scripts/probes/_miso188_ab_gates.py
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
sys.path.insert(0, str(REPO / "scripts" / "probes"))

KEEPER = REPO / "results/calibration/miso187_nuc_B"
CONTROL = REPO / "results/calibration/miso188_rvs_A"
ARM = REPO / "results/calibration/miso188_rvs_B"
OUT = REPO / "results/calibration/_miso188_ab_gates.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
BAND_PCT = 10.0
S2_MIN_FALL_TWH = 0.10
FIELD = "retiree_vintage_status_scope"
# Frozen S-1 witness plants (PREREG-miso188 §4).
GRAND_TOWER = 862
DARK_DROPS = (202, 2050, 10075)  # arm dispatch must be exactly 0 every year
RUSH_ISLAND = 6155  # keep-side witness: nonzero BOTH legs 2023+2024
LANSING = 1047  # accepted miss: nonzero BOTH legs 2023


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"] if "pass" in df.columns else df
    return df


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


def _plant_total_mwh(bundle: Path, plant: int, year: int) -> float | None:
    dp = bundle / "dispatch" / f"{year}_P1.parquet"
    if not dp.exists():
        return None
    df = pd.read_parquet(dp, columns=["plant_code", "mw"])
    return float(df.loc[df["plant_code"] == plant, "mw"].sum())


def s1_exactness() -> dict:
    """S-1 — the single-delta config + the flag demonstrably acted."""
    rc_a = json.loads((CONTROL / "run_config.json").read_text())
    rc_b = json.loads((ARM / "run_config.json").read_text())
    sc_a = (rc_a.get("scenario_config") or {}).get(FIELD)
    sc_b = (rc_b.get("scenario_config") or {}).get(FIELD)
    delta_ok = bool(sc_b) and not bool(sc_a)
    wit: dict = {}
    for pid in (GRAND_TOWER, RUSH_ISLAND, LANSING, *DARK_DROPS):
        wit[str(pid)] = {
            str(y): {
                "control": _plant_total_mwh(CONTROL, pid, y),
                "arm": _plant_total_mwh(ARM, pid, y),
            }
            for y in YEARS
        }

    def _v(pid: int, year: int, leg: str) -> float | None:
        return wit[str(pid)][str(year)][leg]

    have = all(
        isinstance(_v(p, y, leg), float)
        for p in (GRAND_TOWER, RUSH_ISLAND, LANSING, *DARK_DROPS)
        for y in YEARS
        for leg in ("control", "arm")
    )
    gt_ok = have and all(
        _v(GRAND_TOWER, y, "control") > 0.0 and _v(GRAND_TOWER, y, "arm") == 0.0
        for y in (2023, 2024)
    )
    dark_ok = have and all(
        _v(p, y, "arm") == 0.0 for p in DARK_DROPS for y in YEARS
    )
    rush_ok = have and all(
        _v(RUSH_ISLAND, y, leg) > 0.0
        for y in (2023, 2024)
        for leg in ("control", "arm")
    )
    lansing_ok = have and all(
        _v(LANSING, 2023, leg) > 0.0 for leg in ("control", "arm")
    )
    return {
        "gate": "S-1",
        "arm_flag": sc_b,
        "control_flag": sc_a,
        "witness_mwh": wit,
        "grand_tower_ok": bool(gt_ok),
        "dark_drops_ok": bool(dark_ok),
        "rush_island_ok": bool(rush_ok),
        "lansing_ok": bool(lansing_ok),
        "passed": bool(delta_ok and gt_ok and dark_ok and rush_ok and lansing_ok),
    }


def _class_energy_twh(bundle: Path, klass: str, year: int) -> float:
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch["klass"] == klass)]
    return float(ch["mw"].sum()) / 1e6


def s2_structure() -> dict:
    """S-2 — arm 2024 CC_REGULAR class energy falls >= 0.10 TWh vs control."""
    out: dict = {"gate": "S-2", "years": {}}
    for year in YEARS:
        out["years"][str(year)] = {
            "control_cc_twh": round(_class_energy_twh(CONTROL, "CC_REGULAR", year), 4),
            "arm_cc_twh": round(_class_energy_twh(ARM, "CC_REGULAR", year), 4),
        }
    c = out["years"]["2024"]["control_cc_twh"]
    a = out["years"]["2024"]["arm_cc_twh"]
    out["fall_2024_twh"] = round(c - a, 4)
    out["passed"] = bool((c - a) >= S2_MIN_FALL_TWH)
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


def _c1_cc_2024(verdict: dict) -> dict | None:
    for rec in verdict["criteria"]["fuelmix"]["records"]:
        if rec.get("key") == "CC_REGULAR" and rec.get("year") == 2024:
            return {
                "err_twh": round(float(rec["model"]) - float(rec["actual"]), 4),
                "status": rec.get("status"),
                "model": rec.get("model"),
                "actual": rec.get("actual"),
            }
    return None


def _c3a(verdict: dict) -> dict:
    out = {}
    for rec in verdict["criteria"]["price_mean"]["records"]:
        if rec.get("benchmark") == "RT" and rec.get("key") is None:
            m, a = float(rec["model"]), float(rec["actual"])
            out[int(rec["year"])] = 100.0 * (m - a) / a
    return out


def s4_s5() -> dict:
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
    cc_c, cc_a = _c1_cc_2024(vc), _c1_cc_2024(va)
    out["S5"] = {
        "gate": "S-5 (report + escalation, not a kill)",
        "c3a_control_pct": {y: round(v, 4) for y, v in c3a_c.items()},
        "c3a_arm_pct": {y: round(v, 4) for y, v in c3a_a.items()},
        "c1_cc_regular_2024_control": cc_c,
        "c1_cc_regular_2024_arm": cc_a,
        "criterion_status_flips": flips,
        "pass_to_fail_flips": bad_flips,
        "band_exit_2023_2024": band_exit,
        "determination_control": vc.get("determination"),
        "determination_arm": va.get("determination"),
        "escalation_fires": bool(bad_flips or any(band_exit.values())),
    }
    out["_c1_cc_2024_improves"] = bool(
        cc_c and cc_a and abs(cc_a["err_twh"]) < abs(cc_c["err_twh"])
    )
    return out


def main() -> dict:
    out: dict = {
        "prereg": "PREREG-miso188-retiree-vintage-status-scope-2026-08-30.md §4",
        "keeper": "2026-08-26-miso-187-nucavail",
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
        f"gt {out['S1']['grand_tower_ok']} dark {out['S1']['dark_drops_ok']} "
        f"rush {out['S1']['rush_island_ok']} lansing {out['S1']['lansing_ok']}",
        flush=True,
    )
    out["S2"] = s2_structure()
    print(
        "S-2",
        "PASS" if out["S2"]["passed"] else "FAIL",
        f"CC_REGULAR 2024 fall {out['S2']['fall_2024_twh']:+.4f} TWh",
        out["S2"]["years"],
        flush=True,
    )
    out.update(s4_s5())
    print("S-4", "PASS" if out["S4"]["passed"] else "FAIL", flush=True)
    print("S-5", json.dumps(out["S5"], indent=1), flush=True)
    charter_kill = bool(out["_c1_cc_2024_improves"] and not out["S1"]["passed"])
    out["charter_kill_fires"] = charter_kill
    if charter_kill:
        out["verdict"] = "REJECT (charter kill: unidentified level lever)"
    elif not out["S1"]["passed"] or not out["S4"]["passed"]:
        out["verdict"] = "REJECT (kill gate failed)"
    elif out["S2"]["passed"]:
        if out["S5"]["pass_to_fail_flips"]:
            out["verdict"] = "STRUCTURAL PASS (S-1 + S-2); OWNER ESCALATION (PASS->FAIL flip)"
        else:
            out["verdict"] = "PROMOTE per PREREG-miso188 §4 (all gates clean, zero PASS->FAIL flips)"
    else:
        out["verdict"] = "MIXED (S-1 clean, S-2 silent) -> cell I; owner escalation"
    print("VERDICT:", out["verdict"], flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
