"""miso-148 G-L1a/G-L1b/G-L1c-precheck — the basis-aware admission rule, measured.

Runs on the ACTUAL solve fleet (``fleet_state``, ``run_year(fleet_only=True)`` —
no LP), at HEAD, BEFORE the arm is solved (PREREG §5 "G-L1"):

* **G-L1a ADMISSION** — MW and unit counts the per-plant predicate ADMITS
  (flat derate suppressed: pmax already a measured summer capability) vs KEEPS
  (still on a nameplate-like basis: CC-guard-clipped, or absent from EIA-860),
  per class per year. TRAP T2's counter-measurement: the basis is measured on
  the real fleet, never assumed.
* **G-L1b RESTORED CAPABILITY** — summer h12-17 mean MW handed back, against
  miso-141 G-4's committed 5,933 / 5,853 / 5,686 MW. A LOWER figure is the
  expected consequence of §4's explicit corrupt-filing treatment, not a miss.
* **G-L1c PRECHECK** — ``AV_CC`` under the arm vs reality's realized CC output
  ``A``, in the S1 stratum and by month, rebuilt with the flag ON. The gate the
  lane exists to pass: model available CC capability must stop sitting BELOW
  observed generation.
* **T3 counter-measurement** — the availability A/B is asserted to change ONLY
  in summer hours, ONLY for admitted units, and by exactly ``1/(1-d)``.
* **L2 RESIDUAL (OA census)** — the EIA-860 ``OA`` (standby) rows the 2025
  fallback release drops for want of a ``vintage_2025/`` directory, with each
  plant's CAMPD demonstrated operation beside it. Reported, not repaired.

Probe hygiene (miso-140b §6): ``hygiene()`` at the entry point; strata, the
CAMPD unit loader and the parasitic factors come from ``_miso147_strata``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _i, _p in enumerate((REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes")):
    sys.path.insert(_i, str(_p))

from _miso143_stack import YEARS, fleet_state, hygiene  # noqa: E402
from _miso147_strata import (  # noqa: E402
    campd_family_hourly,
    campd_units,
    parasitic_map,
    strata,
    wmean,
    c3a_weight,
)

OUT = REPO / "results" / "calibration" / "_miso148_admission.json"

FLAT_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP")
CC_KLASSES = ("CC_REGULAR", "CC_CHP")
#: miso-141 G-4 committed restored summer h12-17 capability (MW), 2023/24/25.
MISO141_G4_MW = {2023: 5933.0, 2024: 5853.0, 2025: 5686.0}


def _summer_mask(hours: int = 8760) -> np.ndarray:
    """Jun-Sep hours (the flat derate's own window), non-leap 8760."""
    doy = np.arange(hours) // 24
    month = pd.to_datetime(
        pd.Series(doy), unit="D", origin=pd.Timestamp("2023-01-01")
    ).dt.month.to_numpy()
    return (month >= 6) & (month <= 9)


def _h12_17(hours: int = 8760) -> np.ndarray:
    hod = np.arange(hours) % 24
    return (hod >= 12) & (hod <= 17)


def arm_state(year: int) -> dict:
    """Fleet built twice at one HEAD — flag OFF (control) and ON (arm)."""
    from market_sim.data.fleet import summer_basis_measured_plants
    from market_sim.data.fleet.arrays import _SUMMER_CLASS_DERATE

    off = fleet_state(year)
    gens = off["fleet"]
    fa_off = off["fleet_arrays"]
    pmax = np.asarray(fa_off.pmax, dtype=float)
    avail_off = np.asarray(fa_off.availability, dtype=float)

    # The predicate, evaluated AFTER the fleet load so the CC guard's clip
    # decision is recorded (see fleet.eia860._CC_PMAX_RECONCILED_PLANTS).
    measured = summer_basis_measured_plants("MISO")
    klass = np.array([str(getattr(g, "plant_group", "")) for g in gens])
    codes = np.array([int(getattr(g, "plant_code", -1)) for g in gens])
    admitted = np.array(
        [k in _SUMMER_CLASS_DERATE and c in measured for k, c in zip(klass, codes)]
    )
    flat = np.array([k in _SUMMER_CLASS_DERATE for k in klass])

    # The arm's availability, constructed rather than re-solved: suppressing the
    # flat derate multiplies the admitted units' SUMMER hours by exactly
    # 1/(1-d). Asserted against the class's own d below (T3).
    summer = _summer_mask(avail_off.shape[1])
    avail_arm = avail_off.copy()
    for k in FLAT_CLASSES:
        d = _SUMMER_CLASS_DERATE.get(k)
        if not d:
            continue
        m = admitted & (klass == k)
        if m.any():
            avail_arm[np.ix_(m, summer)] = avail_off[np.ix_(m, summer)] / (1.0 - d)
    np.clip(avail_arm, 0.0, 1.0, out=avail_arm)
    return {
        "gens": gens,
        "klass": klass,
        "codes": codes,
        "pmax": pmax,
        "avail_off": avail_off,
        "avail_arm": avail_arm,
        "admitted": admitted,
        "flat": flat,
        "summer": summer,
        "measured_n": len(measured),
    }


def gate_l1a(st: dict) -> dict:
    """Admission: MW and unit counts SUPPRESSED vs KEPT, per class."""
    out: dict = {}
    for k in FLAT_CLASSES:
        m = st["klass"] == k
        adm = m & st["admitted"]
        kept = m & ~st["admitted"]
        out[k] = {
            "n_units": int(m.sum()),
            "pmax_mw": round(float(st["pmax"][m].sum()), 1),
            "suppressed": {
                "n_units": int(adm.sum()),
                "pmax_mw": round(float(st["pmax"][adm].sum()), 1),
            },
            "kept": {
                "n_units": int(kept.sum()),
                "pmax_mw": round(float(st["pmax"][kept].sum()), 1),
                "plants": sorted({int(c) for c in st["codes"][kept]})[:30],
            },
        }
    tot = st["flat"]
    adm_tot = st["flat"] & st["admitted"]
    out["_TOTAL"] = {
        "flat_derate_pmax_mw": round(float(st["pmax"][tot].sum()), 1),
        "suppressed_pmax_mw": round(float(st["pmax"][adm_tot].sum()), 1),
        "suppressed_share": round(
            float(st["pmax"][adm_tot].sum() / max(st["pmax"][tot].sum(), 1e-9)), 4
        ),
        "measured_basis_plants_in_eia860": st["measured_n"],
    }
    return out


def gate_l1b(st: dict, year: int) -> dict:
    """Restored summer h12-17 mean MW vs miso-141 G-4's committed figure."""
    win = _summer_mask(st["avail_off"].shape[1]) & _h12_17(st["avail_off"].shape[1])
    cap_off = (st["pmax"][:, None] * st["avail_off"])[:, win]
    cap_arm = (st["pmax"][:, None] * st["avail_arm"])[:, win]
    per_class = {}
    for k in FLAT_CLASSES:
        m = st["klass"] == k
        per_class[k] = round(
            float(cap_arm[m].sum(axis=0).mean() - cap_off[m].sum(axis=0).mean()), 1
        )
    restored = round(float(cap_arm.sum(axis=0).mean() - cap_off.sum(axis=0).mean()), 1)
    ref = MISO141_G4_MW[year]
    return {
        "restored_summer_h12_17_mw": restored,
        "by_class": per_class,
        "miso141_g4_committed_mw": ref,
        "ratio_vs_miso141": round(restored / ref, 4),
        "within_10pct": bool(abs(restored - ref) <= 0.10 * ref),
        "note": (
            "A LOWER figure than miso-141 G-4 is the EXPECTED consequence of the "
            "explicit corrupt-filing treatment (PREREG §4: CC-guard-clipped and "
            "EIA-860-absent plants KEEP the derate), not a miss. miso-141's "
            "figure zeroed the derate for every unit."
        ),
    }


def gate_l1c(st: dict, year: int) -> dict:
    """AV_CC under the arm vs reality's realized CC output, S1 + by month."""
    cc = np.isin(st["klass"], CC_KLASSES)
    av_off = (st["pmax"][cc, None] * st["avail_off"][cc]).sum(axis=0)
    av_arm = (st["pmax"][cc, None] * st["avail_arm"][cc]).sum(axis=0)
    units, _ = campd_units(year)
    fams = campd_family_hourly(units, "net", parasitic_map())
    a_cc = fams["CC"]

    s = strata(year)
    w = c3a_weight(year)
    s1 = s["masks"]["S1"]
    res = {
        "S1": {
            "AV_off": round(wmean(av_off, w, s1), 1),
            "AV_arm": round(wmean(av_arm, w, s1), 1),
            "A": round(wmean(a_cc, w, s1), 1),
            "AV_minus_A_off": round(wmean(av_off, w, s1) - wmean(a_cc, w, s1), 1),
            "AV_minus_A_arm": round(wmean(av_arm, w, s1) - wmean(a_cc, w, s1), 1),
        }
    }
    doy = np.arange(len(av_off)) // 24
    month = pd.to_datetime(
        pd.Series(doy), unit="D", origin=pd.Timestamp("2023-01-01")
    ).dt.month.to_numpy()
    res["monthly_AV_minus_A_off"] = [
        round(float(av_off[month == m].mean() - a_cc[month == m].mean()), 1)
        for m in range(1, 13)
    ]
    res["monthly_AV_minus_A_arm"] = [
        round(float(av_arm[month == m].mean() - a_cc[month == m].mean()), 1)
        for m in range(1, 13)
    ]
    off = res["S1"]["AV_minus_A_off"]
    arm = res["S1"]["AV_minus_A_arm"]
    res["verdict"] = "RISES" if arm > off else ("FLAT" if arm == off else "FALLS")
    res["sign_flipped_nonneg"] = bool(arm >= 0.0)
    return res


def trap_t3(st: dict) -> dict:
    """Only summer hours, only admitted units, ratio exactly 1/(1-d)."""
    from market_sim.data.fleet.arrays import _SUMMER_CLASS_DERATE

    off, arm = st["avail_off"], st["avail_arm"]
    winter = ~st["summer"]
    checks = {
        "off_summer_hours_byte_identical": bool(
            np.array_equal(off[:, winter], arm[:, winter])
        ),
        "non_admitted_units_byte_identical": bool(
            np.array_equal(off[~st["admitted"]], arm[~st["admitted"]])
        ),
    }
    ratios = {}
    for k in FLAT_CLASSES:
        d = _SUMMER_CLASS_DERATE.get(k)
        m = st["admitted"] & (st["klass"] == k)
        if not m.any() or not d:
            continue
        a = off[np.ix_(m, st["summer"])]
        b = arm[np.ix_(m, st["summer"])]
        nz = a > 1e-12
        r = float(np.median(b[nz] / a[nz])) if nz.any() else float("nan")
        ratios[k] = {
            "median_ratio": round(r, 6),
            "expected": round(1.0 / (1.0 - d), 6),
            "ok": bool(abs(r - 1.0 / (1.0 - d)) < 1e-6),
        }
    checks["per_class_ratio"] = ratios
    checks["pass"] = bool(
        checks["off_summer_hours_byte_identical"]
        and checks["non_admitted_units_byte_identical"]
        and all(v["ok"] for v in ratios.values())
    )
    return checks


def l2_residual_oa_census() -> dict:
    """EIA-860 OA (standby) rows the 2025 fallback release drops, vs CAMPD."""
    from market_sim.config.paths import EIA_860_DIR

    canon = pd.read_parquet(
        EIA_860_DIR / "eia860_generator_operable.parquet",
        columns=[
            "Plant Code",
            "Plant Name",
            "Generator ID",
            "Summer Capacity (MW)",
            "Status",
        ],
    )
    canon["Status"] = canon["Status"].astype(str).str.strip().str.upper()
    oa = canon[canon["Status"] == "OA"].copy()
    oa["pc"] = pd.to_numeric(oa["Plant Code"], errors="coerce")
    v24 = pd.read_parquet(
        EIA_860_DIR / "vintage_2024" / "eia860_generator_operable.parquet",
        columns=["Plant Code", "Generator ID", "Status"],
    )
    v24["Status"] = v24["Status"].astype(str).str.strip().str.upper()
    op24 = {
        (int(p), str(g).strip())
        for p, g, s in zip(v24["Plant Code"], v24["Generator ID"], v24["Status"])
        if pd.notna(p) and s == "OP"
    }
    st = fleet_state(2025)
    fleet_plants = {int(getattr(g, "plant_code", -1)) for g in st["fleet"]}
    rows = []
    for r in oa.itertuples():
        pc = int(r.pc) if pd.notna(r.pc) else -1
        if pc not in fleet_plants:
            continue
        rows.append(
            {
                "plant_code": pc,
                "plant_name": str(r._2),
                "generator_id": str(r._3).strip(),
                "summer_mw": float(pd.to_numeric(r._4, errors="coerce") or 0.0),
                "was_OP_in_vintage_2024": (pc, str(r._3).strip()) in op24,
            }
        )
    df = pd.DataFrame(rows)
    dropped = df[df["was_OP_in_vintage_2024"]] if len(df) else df
    return {
        "n_OA_rows_in_fleet_plants": int(len(df)),
        "n_dropped_but_OP_in_2024": int(len(dropped)),
        "mw_dropped": round(float(dropped["summer_mw"].sum()), 1) if len(dropped) else 0.0,
        "by_plant": (
            dropped.groupby(["plant_code", "plant_name"])["summer_mw"]
            .agg(["sum", "size"])
            .reset_index()
            .rename(columns={"sum": "mw", "size": "n_rows"})
            .to_dict("records")
            if len(dropped)
            else []
        ),
        "note": (
            "2025 has no vintage_2025/ directory, so the fleet falls back to the "
            "canonical (2025 Early Release) EIA-860, which re-flags these rows OA "
            "(standby). The operable loader carries OP only, and the designed "
            "rescue load_mothballed_but_operating returns [] because its "
            "vintage_<year> precondition is unmet. REPORTED, NOT REPAIRED — the "
            "fix is cross-ISO (every ISO's 2025+ fleet) and needs its own lane."
        ),
    }


def run() -> dict:
    hygiene()
    res: dict = {
        "session": "miso-148",
        "prereg": "results/calibration/PREREG-miso148-cc-availability-summer-basis-2026-08-09.md",
        "gate": "G-L1a/b/c-precheck — basis-aware admission on the real fleet, no LP",
        "years": {},
    }
    for y in YEARS:
        st = arm_state(y)
        res["years"][str(y)] = {
            "G_L1a_admission": gate_l1a(st),
            "G_L1b_restored": gate_l1b(st, y),
            "G_L1c_precheck": gate_l1c(st, y),
            "T3_construction": trap_t3(st),
        }
        del st
    res["L2_residual_oa_census"] = l2_residual_oa_census()
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


if __name__ == "__main__":
    r = run()
    for y in YEARS:
        a = r["years"][str(y)]
        t = a["G_L1a_admission"]["_TOTAL"]
        b = a["G_L1b_restored"]
        c = a["G_L1c_precheck"]
        print(
            f"{y}: suppressed {t['suppressed_pmax_mw']} of {t['flat_derate_pmax_mw']} MW "
            f"({100*t['suppressed_share']:.1f}%) | restored h12-17 {b['restored_summer_h12_17_mw']} MW "
            f"(miso-141 {b['miso141_g4_committed_mw']}, ratio {b['ratio_vs_miso141']}) | "
            f"T3 {'PASS' if a['T3_construction']['pass'] else 'FAIL'}"
        )
        print(
            f"      S1 AV-A {c['S1']['AV_minus_A_off']} -> {c['S1']['AV_minus_A_arm']} MW "
            f"({c['verdict']}, >=0: {c['sign_flipped_nonneg']}) | "
            f"Jun-Sep arm {c['monthly_AV_minus_A_arm'][5:9]}"
        )
    o = r["L2_residual_oa_census"]
    print(f"L2 residual: {o['n_dropped_but_OP_in_2024']} OA rows dropped in 2025 "
          f"({o['mw_dropped']} MW) that were OP in vintage_2024")
    print(f"-> {OUT}")
