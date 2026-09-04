"""miso-208 second deliverable — repair miso-203's G-D reserve-margin block.

miso-203's G-D read the keeper's ``class_hourly`` dispatch by the FLEET's
``plant_group`` key ("COAL") while the sidecar reports coal as
``COAL_BIT`` / ``COAL_PRB`` / ``COAL_LIGNITE`` — so ``disp.get("COAL")`` was
``None``, the whole coal capability counted as IDLE, and the "broad" reserve
margin read 42.7 / 38.4 / 30.5 GW (miso-207 re-measured the tail's margin on
its own instrument at +0.14 GW mean / −5.2 GW min).  The miso-206
record-repair pattern: reproduce the DEFECTIVE numbers first (R-1), then change
exactly one thing — subtract the POOLED coal dispatch — on miso-203's OWN hour
set and capability matrix; the defective block is preserved under
``pre_repair``.  Zero-solve; the record is a diagnostic artifact.

Usage::

    PYTHONPATH=src python3 scripts/probes/_miso208_repair_miso203_gd.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso203_summer_peak_anchor_phase0 as m203  # noqa: E402

RECORD = m203.OUT
COAL_KLASSES = ("COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC", "COAL")
R1_TOL_MW = 5.0
HOURS = m203.HOURS


def _gd_block(groups, cap_ctrl, disp, req, scarce, rem, pooled_coal: bool) -> dict:
    """miso-203's G-D arithmetic; ``pooled_coal`` is the single repair switch."""
    idle_broad = np.zeros(HOURS)
    idle_armed = np.zeros(HOURS)
    unmatched: list[str] = []
    for cls in sorted(set(groups)):
        if not cls:
            continue
        sel = groups == cls
        capc = cap_ctrl[sel].sum(axis=0)
        if cls == "COAL" and pooled_coal:
            d = sum(disp[k] for k in COAL_KLASSES if k in disp)
        else:
            d = disp.get(cls)
        if d is None:
            unmatched.append(cls)
            d = np.zeros(HOURS)
        gap = np.maximum(0.0, capc - np.asarray(d, float)[:HOURS])
        if cls in m203.RESERVE_ELIGIBLE:
            idle_broad += gap
        if cls in m203.ARMED:
            idle_armed += gap
    margin_broad = idle_broad - req
    margin_armed = idle_armed - req
    sm_broad = float(margin_broad[scarce].min())
    sm_armed = float(margin_armed[scarce].min())
    return {
        "basis": (
            "reserve-eligible idle capability (model's own capability matrix "
            "minus its committed P1 class dispatch, COAL POOLED over the "
            "COAL_* klasses) minus the four families' summed requirement, in "
            "the G-C scarce hours."
            if pooled_coal
            else "DEFECTIVE: the COAL group's dispatch was looked up under the "
            "fleet key 'COAL' (absent from class_hourly) and read as ZERO."
        ),
        "reserve_requirement_mw_mean_scarce": round(float(req[scarce].mean()), 1),
        "idle_reserve_eligible_mw_mean_scarce": round(
            float(idle_broad[scarce].mean()), 1
        ),
        "idle_armed_classes_mw_mean_scarce": round(float(idle_armed[scarce].mean()), 1),
        "margin_broad_mw_min_scarce": round(sm_broad, 1),
        "margin_broad_mw_mean_scarce": round(float(margin_broad[scarce].mean()), 1),
        "margin_armed_only_mw_min_scarce": round(sm_armed, 1),
        "removal_mw_measured_anchor": rem,
        "removal_share_of_broad_margin": round(rem / sm_broad, 4)
        if sm_broad > 0
        else None,
        "removal_share_of_armed_margin": round(rem / sm_armed, 4)
        if sm_armed > 0
        else None,
        "license_threshold": m203.G_D_LICENSE,
        "G_D_PASS": bool(sm_broad > 0 and (rem / sm_broad) >= m203.G_D_LICENSE),
        "groups_with_no_class_hourly_key": unmatched,
    }


def main() -> None:
    rec = json.loads(RECORD.read_text())
    mon = m203._hour_month()
    jun_jul = np.isin(mon, (6, 7))
    repairs = {}
    for year in m203.YEARS:
        old = rec["g_d_reserve_binding"][str(year)]
        if "pre_repair" in old:
            print(f"{year}: already repaired — skipping")
            continue
        cfg = m203.keeper_config(year)
        gens, fa = m203.control_capability(year, cfg)
        groups = np.array([g.plant_group for g in gens])
        cap_ctrl = fa.pmax[:, None] * fa.availability
        act = m203.hub_hourly_rt(year)
        jj = np.where(jun_jul)[0]
        thr = float(np.percentile(act[jj], 99.0))
        scarce = jj[act[jj] >= thr]
        assert (
            abs(thr - rec["g_c_tail_reach"][str(year)]["threshold_usd_per_mwh"]) < 0.01
        )
        ch = pd.read_parquet(m203.KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        disp = {
            k: g.sort_values("hour")["mw"].to_numpy() for k, g in ch.groupby("klass")
        }
        rf = pd.read_parquet(m203.KEEPER / "hourly" / f"reserve_family_{year}.parquet")
        rf = rf[rf["pass"] == "P1"]
        req = rf.groupby("hour")["requirement_mw"].sum().sort_index().to_numpy()
        rem = old["removal_mw_measured_anchor"]

        defective = _gd_block(
            groups, cap_ctrl, disp, req, scarce, rem, pooled_coal=False
        )
        r1 = {
            k: (old[k], defective[k], abs(old[k] - defective[k]) <= R1_TOL_MW)
            for k in (
                "idle_reserve_eligible_mw_mean_scarce",
                "idle_armed_classes_mw_mean_scarce",
                "margin_broad_mw_min_scarce",
                "margin_broad_mw_mean_scarce",
            )
        }
        r1_pass = all(v[2] for v in r1.values())
        repaired = _gd_block(groups, cap_ctrl, disp, req, scarce, rem, pooled_coal=True)
        repaired["miso139_summer_aft_732h_idle_mw_mean"] = old.get(
            "miso139_summer_aft_732h_idle_mw_mean"
        )
        repaired["pre_repair"] = old
        repaired["repair"] = {
            "session": "miso-208 (2026-09-04)",
            "defect": (
                "class-key mismatch: fleet plant_group 'COAL' vs class_hourly "
                "klass COAL_BIT/COAL_PRB/COAL_LIGNITE — the coal fleet's dispatch "
                "was read as zero and its whole capability counted as idle"
            ),
            "change": "exactly one: the COAL group's dispatch = the pooled COAL_* klass dispatch",
            "R1_defective_block_reproduced": r1,
            "R1_PASS": r1_pass,
            "coal_dispatch_mw_mean_scarce": round(
                float(sum(disp[k] for k in COAL_KLASSES if k in disp)[scarce].mean()), 1
            ),
        }
        rec["g_d_reserve_binding"][str(year)] = repaired
        repairs[str(year)] = {
            "R1_PASS": r1_pass,
            "broad_margin_min_mw": (
                old["margin_broad_mw_min_scarce"],
                repaired["margin_broad_mw_min_scarce"],
            ),
            "broad_margin_mean_mw": (
                old["margin_broad_mw_mean_scarce"],
                repaired["margin_broad_mw_mean_scarce"],
            ),
            "armed_idle_mw": (
                old["idle_armed_classes_mw_mean_scarce"],
                repaired["idle_armed_classes_mw_mean_scarce"],
            ),
            "removal_share_of_broad_margin": (
                old["removal_share_of_broad_margin"],
                repaired["removal_share_of_broad_margin"],
            ),
            "G_D_PASS": (old["G_D_PASS"], repaired["G_D_PASS"]),
            "unmatched_groups": repaired["groups_with_no_class_hourly_key"],
        }
        print(year, json.dumps(repairs[str(year)]))
    rec.setdefault("record_repairs", []).append(
        {
            "session": "miso-208",
            "date": "2026-09-04",
            "block": "g_d_reserve_binding",
            "pattern": "miso-206 record repair (pre_repair preserved)",
            "summary": repairs,
        }
    )
    RECORD.write_text(json.dumps(rec, indent=1))
    print(f"wrote {RECORD.relative_to(REPO)}")


if __name__ == "__main__":
    main()
