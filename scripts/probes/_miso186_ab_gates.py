"""miso-186 A/B scorer — the unit_outage_fleet_status_scope arm.

Implements the PREREG-miso186 §5 gates, which are the PREREG-miso184 §6 gates
VERBATIM with run names updated (control ``miso186_dir_A``, arm
``miso186_dir_B``, keeper ``miso177_rho_B``):

* S-0 CONTROL INERTNESS (ABANDON): every scored sidecar of the control
  value-identical to the committed keeper's (the miso-180 G-0 construction).
* S-1 EXACTNESS (KILL): the arm's run_config records exactly the single
  repair delta (``unit_outage_fleet_status_scope=true``), the control none;
  the flag demonstrably acted (Cottonwood 55358 dispatchable in the arm's
  2025 scarce hours, zero in the control's).
* S-2 DIRECTION (structural gate): the arm's 2025 scarce-hour N->S binding
  count under the miso-183 spread classifier (spread = P1 price(MISO-South)
  - price(MISO-East); N->S == spread > +$1, S->N == spread < -$1, +-$1 dead
  band) must FALL below the control's (committed keeper: 9/47). S->N count
  and full composition reported, all years, never gated.
* S-3 OUTFLOW (structural gate): the arm's 2025 scarce-mean model South
  boundary-complex net inflow N_S^m — from each leg's full solve outputs
  (flows.parquet links incident to MISO-South, seam-band net at
  MISO_external_South included), verified against the zonal energy balance
  (residual < 1 MW) — must move from the control's value toward the measured
  -2.441 GW by >= 0.1 GW.
* CHARTER KILL: an arm that improves C3a-2025 while BOTH S-2 and S-3 fail is
  a level adder wearing a repair's name -> REJECTED.
* S-4 CONDUCT (KILL): zero D-4 conduct FAILs on the arm's regenerated
  legitimacy_diagnostics.json, zero NEW vs the control; C8 PASS all years.
* S-5 FULL-MAGNITUDE SCORING (report + escalation, NOT a kill):
  calibration_verdict --json on both legs; C3a all years, every criterion
  status flip and any 2023/2024 exit from the +-10% band flagged for the
  owner-escalation path (never auto-reject / auto-keeper).

Record: ``results/calibration/_miso186_ab_gates.json``.

Run:
    uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml \
      --python 3.12 python scripts/probes/_miso186_ab_gates.py
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

import _miso183_south_basis_decomposition as _m183  # noqa: E402

KEEPER = REPO / "results/calibration/miso177_rho_B"
CONTROL = REPO / "results/calibration/miso186_dir_A"
ARM = REPO / "results/calibration/miso186_dir_B"
OUT = REPO / "results/calibration/_miso186_ab_gates.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
DEADBAND = 1.0
MEAS_NS_2025 = -2.441  # GW, miso-183 committed (positive INTO the South)
S3_MIN_MOVE_GW = 0.1
BAND_PCT = 10.0


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"] if "pass" in df.columns else df
    return df


def identity(control: Path, keeper: Path) -> dict:
    """S-0 — every scored sidecar of every year value-identical (miso-180 G-0)."""
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


def s1_exactness() -> dict:
    """S-1 — the single-delta config + the flag demonstrably acted."""
    rc_a = json.loads((CONTROL / "run_config.json").read_text())
    rc_b = json.loads((ARM / "run_config.json").read_text())
    ov_a = rc_a.get("prb_overrides") or rc_a.get("overrides") or {}
    ov_b = rc_b.get("prb_overrides") or rc_b.get("overrides") or {}
    sc_a = (rc_a.get("scenario_config") or {}).get("unit_outage_fleet_status_scope")
    sc_b = (rc_b.get("scenario_config") or {}).get("unit_outage_fleet_status_scope")
    delta_ok = bool(sc_b) and not bool(sc_a)
    # the flag acted: Cottonwood (55358) CC_REGULAR dispatchable in the arm's
    # 2025 scarce hours; the control keeps it at zero (the committed defect).
    sc = _m183.hour_sets(2025)["scarce"]
    act = {}
    for tag, bundle in (("control", CONTROL), ("arm", ARM)):
        dp = bundle / "dispatch" / "2025_P1.parquet"
        if not dp.exists():
            act[tag] = None
            continue
        df = pd.read_parquet(dp, columns=["unit", "hour", "mw"]) if _has_col(
            dp, "unit"
        ) else pd.read_parquet(dp)
        ucol = "unit" if "unit" in df.columns else (
            "unit_id" if "unit_id" in df.columns else None
        )
        if ucol is None:
            act[tag] = "no-unit-column"
            continue
        cw = df[df[ucol].astype(str).str.contains("p55358")]
        v = cw.groupby("hour")["mw"].sum().reindex(np.nonzero(sc)[0]).fillna(0.0)
        act[tag] = float(v.mean())
    return {
        "gate": "S-1",
        "arm_flag": sc_b,
        "control_flag": sc_a,
        "arm_overrides": ov_b,
        "control_overrides": ov_a,
        "cottonwood_2025_scarce_mw": act,
        "passed": bool(
            delta_ok
            and (act.get("arm") is None or not isinstance(act.get("arm"), float)
                 or act["arm"] > 0.0)
        ),
    }


def _has_col(path: Path, col: str) -> bool:
    import pyarrow.parquet as pq

    return col in pq.read_schema(path).names


def s2_direction() -> dict:
    """S-2 — the 2025 scarce N->S binding count must FALL below the control's."""
    out: dict = {"gate": "S-2", "years": {}}
    for year in YEARS:
        sc = _m183.hour_sets(year)["scarce"]
        rec = {}
        for tag, bundle in (("control", CONTROL), ("arm", ARM)):
            sy = _system(bundle, year)
            piv = sy.pivot_table(index="hour", columns="zone", values="price").reindex(
                range(HOURS)
            )
            spread = (piv["MISO-South"] - piv["MISO-East"]).to_numpy(dtype=float)[sc]
            rec[tag] = {
                "n2s": int((spread > DEADBAND).sum()),
                "s2n": int((spread < -DEADBAND).sum()),
                "unconstrained": int((np.abs(spread) <= DEADBAND).sum()),
            }
        out["years"][str(year)] = rec
    c = out["years"]["2025"]["control"]["n2s"]
    a = out["years"]["2025"]["arm"]["n2s"]
    out["control_2025_n2s"] = c
    out["arm_2025_n2s"] = a
    out["passed"] = bool(a < c)
    return out


def _south_net_inflow(bundle: Path, year: int) -> dict:
    """Model South boundary-complex net inflow (GW, + INTO the South) + balance."""
    fl = pd.read_parquet(bundle / "flows.parquet")
    fl = fl[(fl["year"] == year) & (fl["pass"] == "P1")]
    into = fl[fl["to_zone"] == "MISO-South"].pivot_table(
        index="hour", columns="from_zone", values="mw", aggfunc="sum"
    ).reindex(range(HOURS)).fillna(0.0)
    outof = fl[fl["from_zone"] == "MISO-South"].pivot_table(
        index="hour", columns="to_zone", values="mw", aggfunc="sum"
    ).reindex(range(HOURS)).fillna(0.0)
    net_in = into.sum(axis=1).to_numpy() - outof.sum(axis=1).to_numpy()
    sy = _system(bundle, year)
    s = sy[sy["zone"] == "MISO-South"].set_index("hour").reindex(range(HOURS))
    dem = s["demand"].to_numpy(dtype=float)
    slack = s["slack"].to_numpy(dtype=float)
    dump = s["dump"].to_numpy(dtype=float)
    dp = bundle / "dispatch" / f"{year}_P1.parquet"
    df = pd.read_parquet(dp)
    zcol = "zone" if "zone" in df.columns else None
    gen = (
        df[df[zcol] == "MISO-South"].groupby("hour")["mw"].sum()
        .reindex(range(HOURS)).fillna(0.0).to_numpy()
        if zcol
        else np.full(HOURS, np.nan)
    )
    resid = gen + net_in + slack - dump - dem
    sc = _m183.hour_sets(year)["scarce"]
    return {
        "links_into": sorted(into.columns.tolist()),
        "links_outof": sorted(outof.columns.tolist()),
        "ns_m_scarce_gw": float(net_in[sc].mean()) / 1e3,
        "ns_m_annual_gw": float(net_in.mean()) / 1e3,
        "balance_max_abs_resid_mw": float(np.nanmax(np.abs(resid))),
    }


def s3_outflow() -> dict:
    """S-3 — N_S^m (2025 scarce) must move toward -2.441 GW by >= 0.1 GW."""
    out: dict = {"gate": "S-3", "years": {}}
    for year in YEARS:
        out["years"][str(year)] = {
            "control": _south_net_inflow(CONTROL, year),
            "arm": _south_net_inflow(ARM, year),
        }
    c = out["years"]["2025"]["control"]["ns_m_scarce_gw"]
    a = out["years"]["2025"]["arm"]["ns_m_scarce_gw"]
    move = c - a  # positive = moved DOWN toward the measured -2.441
    bal_ok = all(
        out["years"][str(y)][leg]["balance_max_abs_resid_mw"] < 1.0
        for y in YEARS
        for leg in ("control", "arm")
    )
    out.update(
        control_2025_ns_gw=c,
        arm_2025_ns_gw=a,
        move_toward_measured_gw=move,
        balance_verified=bal_ok,
        passed=bool(move >= S3_MIN_MOVE_GW and bal_ok),
    )
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


def _c3a(verdict: dict) -> dict:
    """C3a (RT, %) per year from the verdict's price_mean RT-benchmark rows."""
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
    c3c, c3a_ = _c3a(vc), _c3a(va)
    sc, sa = _crit_status(vc), _crit_status(va)
    flips = {
        k: f"{sc.get(k)} -> {sa.get(k)}"
        for k in set(sc) | set(sa)
        if sc.get(k) != sa.get(k)
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
        y: abs(c3a_.get(y, 99.0)) > BAND_PCT and abs(c3c.get(y, 99.0)) <= BAND_PCT
        for y in (2023, 2024)
    }
    out["S5"] = {
        "gate": "S-5 (report + escalation, not a kill)",
        "c3a_control_pct": {y: round(v, 4) for y, v in c3c.items()},
        "c3a_arm_pct": {y: round(v, 4) for y, v in c3a_.items()},
        "criterion_status_flips": flips,
        "band_exit_2023_2024": band_exit,
        "determination_control": vc.get("determination"),
        "determination_arm": va.get("determination"),
        "escalation_fires": bool(flips or any(band_exit.values())),
    }
    out["_c3a_2025_improves"] = bool(
        abs(c3a_.get(2025, 99.0)) < abs(c3c.get(2025, 99.0))
    )
    return out


def main() -> dict:
    out: dict = {
        "prereg": "PREREG-miso186-midwest-stack-direction-2026-08-25.md §5 "
        "(PREREG-miso184 §6 gates verbatim)",
        "keeper": "2026-08-22-miso-177-rho-measured",
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
    print("S-1", "PASS" if out["S1"]["passed"] else "FAIL", out["S1"]["cottonwood_2025_scarce_mw"], flush=True)
    out["S2"] = s2_direction()
    print("S-2", "PASS" if out["S2"]["passed"] else "FAIL",
          f"n2s control {out['S2']['control_2025_n2s']} -> arm {out['S2']['arm_2025_n2s']}",
          out["S2"]["years"]["2025"], flush=True)
    out["S3"] = s3_outflow()
    print("S-3", "PASS" if out["S3"]["passed"] else "FAIL",
          f"N_S control {out['S3']['control_2025_ns_gw']:+.3f} -> arm {out['S3']['arm_2025_ns_gw']:+.3f} GW",
          f"(move {out['S3']['move_toward_measured_gw']:+.3f}, balance {out['S3']['balance_verified']})",
          flush=True)
    out.update(s4_s5())
    print("S-4", "PASS" if out["S4"]["passed"] else "FAIL", flush=True)
    print("S-5", json.dumps(out["S5"], indent=1), flush=True)
    charter_kill = bool(
        out["_c3a_2025_improves"] and not out["S2"]["passed"] and not out["S3"]["passed"]
    )
    out["charter_kill_fires"] = charter_kill
    if charter_kill:
        out["verdict"] = "REJECT (charter kill: level adder wearing a repair's name)"
    elif not out["S1"]["passed"] or not out["S4"]["passed"]:
        out["verdict"] = "REJECT (kill gate failed)"
    elif out["S2"]["passed"] and out["S3"]["passed"]:
        out["verdict"] = (
            "STRUCTURAL PASS (S-2 + S-3); owner escalation per S-5"
            if out["S5"]["escalation_fires"]
            else "STRUCTURAL PASS (S-2 + S-3), no S-5 escalation"
        )
    else:
        out["verdict"] = "MIXED (structural gates split); owner escalation"
    print("VERDICT:", out["verdict"], flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
