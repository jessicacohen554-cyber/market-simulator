"""ercot-225 G-SPUR band-top re-reading (read-only, no LP): every registered
ERCOT run's spurious count recomputed WITHOUT the $500 upper lid, per
PRECOMMIT-ercot225-gspur-bandtop-gate-revision-2026-08-21.md §3–§4.

Per run-year, on the shared scorer convention (demand-weighted P1 system
price from the committed ``hourly/system_<year>.parquet``; committed actual
RT parquet; finite-mask primary, ``ercot221_gates`` NaN rule cross-checked):

* ``S_band``  = #{model in [150, 500] & actual < 150}  (the CURRENT gate)
* ``S_top``   = #{model > 500 & actual < 150}          (the blind population)
* ``S_nolid`` = S_band + S_top                          (the revised count)

plus the S_top hour evidence, the §4 verdict re-derivation for V1–V6, and
the §6 baseline hour-identity hygiene check. Consumes committed bytes only;
writes nothing but its own JSON.

Usage::

    python scripts/probes/ercot225_gspur_bandtop_reread.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUAL_LMP = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
OUT = REPO / "results" / "calibration" / "ercot225_gspur_bandtop_reread.json"
YEARS = (2023, 2024, 2025)
MID_BAND = (150.0, 500.0)
LIST_CAP = 24  # S_top hours listed in full when <= cap, else first cap + count

#: PRECOMMIT §3 universe — every registered ERCOT run (registry sidecars).
RUNS: dict[str, str] = {
    "2026-08-15-ercot204-rule26-delete": "ercot204_rule26_delete",
    "2026-08-16-ercot213-ctl-headbase": "ercot213_control_A",
    "2026-08-16-ercot213-arm-pubanchor": "ercot213_anchor_B",
    "2026-08-17-ercot215-ctl-headbase": "ercot215_control_A",
    "2026-08-17-ercot215-arm-decontam": "ercot215_decontam_B",
    "2026-08-18-ercot219-ctl-headbase": "ercot219_control_A",
    "2026-08-18-ercot219-arm-optionb": "ercot219_optionb_B",
    "2026-08-19-ercot221-ctl-headbase": "ercot221_control_A",
    "2026-08-19-ercot221-arm-adaptive": "ercot221_adaptive_B",
    "2026-08-20-ercot223-ctl-headbase": "ercot223_control_replay",
    "2026-08-20-ercot223-arm-eventrelease": "ercot223_release_arm",
}
#: §4 baseline bundle for the V4–V6 bar (the source of the 9/11/1 constant).
BASELINE_BUNDLE = "ercot215_decontam_B"
SPUR_BAR = 5
#: ercot221_gates.py::SPUR_BASELINE hour lists, checked report-only (§6).
GATES_BASELINE_LISTS = {
    2023: [4283, 4404, 4547, 4548, 4571, 4572, 4593, 4832, 5024],
    2024: [4749, 4750, 4751, 4772, 4773, 4796, 4797, 5828, 5829, 5852, 6501],
    2025: [3355],
}


def lw_price(bundle: Path, year: int) -> np.ndarray:
    """Hourly demand-weighted system P1 price (the `_ercot173_ab` basis)."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    return (num / den).reindex(range(8760)).to_numpy(float)


def counts(m: np.ndarray, a: np.ndarray) -> dict:
    """S_band / S_top / S_nolid under both NaN conventions + S_top evidence."""
    # Primary: the _ercot173_ab finite mask.
    ok = np.isfinite(m) & np.isfinite(a)
    band = ok & (m >= MID_BAND[0]) & (m <= MID_BAND[1]) & (a < MID_BAND[0])
    top = ok & (m > MID_BAND[1]) & (a < MID_BAND[0])
    # Cross-check: the ercot221_gates._spur_hours rule (actual NaN -> +inf,
    # model NaN -> 0).
    mm = np.nan_to_num(m)
    aa = np.nan_to_num(a, nan=1e9)
    band_g = (mm >= MID_BAND[0]) & (mm <= MID_BAND[1]) & (aa < MID_BAND[0])
    top_g = (mm > MID_BAND[1]) & (aa < MID_BAND[0])
    top_hours = [int(h) for h in np.where(top)[0]]
    return {
        "S_band": int(band.sum()),
        "S_top": int(top.sum()),
        "S_nolid": int(band.sum() + top.sum()),
        "nan_rule_agrees": bool(
            band.sum() == band_g.sum() and top.sum() == top_g.sum()
        ),
        "S_top_hours": top_hours[:LIST_CAP],
        "S_top_hours_truncated": len(top_hours) > LIST_CAP,
        "S_top_evidence": [
            {"h": h, "model": round(float(m[h]), 2), "actual": round(float(a[h]), 2)}
            for h in top_hours[:LIST_CAP]
        ],
        "band_hours": [int(h) for h in np.where(band)[0]][:LIST_CAP]
        if band.sum() <= LIST_CAP
        else None,
    }


def main() -> None:
    act = pd.read_parquet(ACTUAL_LMP)
    actual = {
        y: act[act.year == y]
        .set_index("hour")["rt"]
        .reindex(range(8760))
        .to_numpy(float)
        for y in YEARS
    }

    out: dict = {
        "probe": "ercot225_gspur_bandtop_reread",
        "charter": "PRECOMMIT-ercot225-gspur-bandtop-gate-revision-2026-08-21 §3-§4",
        "band": list(MID_BAND),
        "runs": {},
    }
    S: dict[str, dict[int, dict]] = {}
    for rid, bdir in RUNS.items():
        bundle = REPO / "results" / "calibration" / bdir
        per = {}
        for y in YEARS:
            per[y] = counts(lw_price(bundle, y), actual[y])
        S[bdir] = per
        out["runs"][rid] = {
            "bundle": bdir,
            "per_year": {str(y): per[y] for y in YEARS},
        }

    def triple(bdir: str, key: str) -> list[int]:
        return [S[bdir][y][key] for y in YEARS]

    base = {y: S[BASELINE_BUNDLE][y]["S_nolid"] for y in YEARS}

    def ab_no_increase(ctl: str, arm: str) -> dict:
        legs = {
            str(y): [S[ctl][y]["S_nolid"], S[arm][y]["S_nolid"]] for y in YEARS
        }
        return {
            "pass": all(v[1] <= v[0] for v in legs.values()),
            "by_year_nolid": legs,
        }

    def ab_bar(ctl: str, arm: str) -> dict:
        legs = {
            str(y): [S[ctl][y]["S_nolid"], S[arm][y]["S_nolid"]] for y in YEARS
        }
        return {
            "pass": all(v[1] <= v[0] + SPUR_BAR for v in legs.values()),
            "by_year_nolid": legs,
        }

    def arm_vs_baseline(arm: str) -> dict:
        legs = {
            str(y): {"bar": base[y] + SPUR_BAR, "arm": S[arm][y]["S_nolid"]}
            for y in YEARS
        }
        return {
            "pass": all(v["arm"] <= v["bar"] for v in legs.values()),
            "by_year": legs,
        }

    # §4 verdict re-derivation, each under its OWN operative rule.
    verdicts = {
        "V1_ercot204": {
            "recorded": "PASS",
            "rule": "no-increase (ercot204_ab)",
            "revised": ab_no_increase("ercot204_rule26_delete", "ercot204_rule26_delete"),
        },
        "V2_ercot213": {
            "recorded": "FAIL (REJECTED-AS-ARMED on G-SPUR; owner-promoted over it)",
            "rule": "+5 bar vs ctl (session) / strict no-increase (artifact)",
            "revised_bar": ab_bar("ercot213_control_A", "ercot213_anchor_B"),
            "revised_strict": ab_no_increase("ercot213_control_A", "ercot213_anchor_B"),
        },
        "V3_ercot215": {
            "recorded": "session PASS (+5 bar) / strict leg FAIL on 2025 0->1",
            "rule": "+5 bar vs ctl (session) / strict no-increase (artifact)",
            "revised_bar": ab_bar("ercot215_control_A", "ercot215_decontam_B"),
            "revised_strict": ab_no_increase("ercot215_control_A", "ercot215_decontam_B"),
        },
        "V4_ercot219": {
            "recorded": "FAIL",
            "rule": "+5/yr vs baseline (9/11/1)",
            "revised": arm_vs_baseline("ercot219_optionb_B"),
        },
        "V5_ercot221": {
            "recorded": "PASS",
            "rule": "+5/yr vs baseline (9/11/1)",
            "revised": arm_vs_baseline("ercot221_adaptive_B"),
        },
        "V6_ercot223": {
            "recorded": "PASS",
            "rule": "+5/yr vs baseline (9/11/1)",
            "revised": arm_vs_baseline("ercot223_release_arm"),
        },
    }
    out["verdicts"] = verdicts
    out["revised_baseline_nolid"] = {str(y): base[y] for y in YEARS}
    out["baseline_bundle"] = BASELINE_BUNDLE
    out["baseline_banded"] = {
        str(y): S[BASELINE_BUNDLE][y]["S_band"] for y in YEARS
    }

    # §6 hygiene: do the gates-file baseline hour lists match the baseline
    # bundle's own banded hours on this construction?
    hyg = {}
    for y in YEARS:
        m = lw_price(REPO / "results" / "calibration" / BASELINE_BUNDLE, y)
        a = actual[y]
        ok = np.isfinite(m) & np.isfinite(a)
        band = ok & (m >= MID_BAND[0]) & (m <= MID_BAND[1]) & (a < MID_BAND[0])
        hours = [int(h) for h in np.where(band)[0]]
        hyg[str(y)] = {
            "baseline_bundle_band_hours": hours,
            "gates_file_list": GATES_BASELINE_LISTS[y],
            "counts_match": len(hours) == len(GATES_BASELINE_LISTS[y]),
            "identities_match": hours == sorted(GATES_BASELINE_LISTS[y]),
        }
    out["hygiene_spur_baseline_lists"] = hyg

    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {OUT}")
    for rid in RUNS:
        b = RUNS[rid]
        print(
            f"{rid}: band={triple(b, 'S_band')} top={triple(b, 'S_top')} "
            f"nolid={triple(b, 'S_nolid')}"
        )
    for k, v in verdicts.items():
        keys = [kk for kk in v if kk.startswith("revised")]
        print(k, v["recorded"], "->", {kk: v[kk]["pass"] for kk in keys})


if __name__ == "__main__":
    main()
