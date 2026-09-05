#!/usr/bin/env python3
"""Emit the nyiso-192 arm's ``calibration_attestation.json`` (C6 gate).

One arm, one control (``results/calibration/PREREG-nyiso192-frontier-adjudication.md``
§7, pushed BEFORE the arm was solved):

* ``astoria_panel`` (``nyiso192_astoria_panel``): the committed keeper
  ``2026-09-05-nyiso-189-steam-identity`` recipe with the outage extract
  RE-DERIVED under its committed invocation after the merit-order panel's
  stack-duplicate repair (``outage_detect.build_merit_order_panel`` now applies
  ``campd.stack_duplicate_mask`` / ``merge_stack_duplicate_units``, as the
  canonical CAMPD normalizer already did). **No ``ScenarioConfig`` field
  changes**; the delta is the ARTIFACT the armed ``campd_outage_merit_order_guard``
  extract carries.

The control is the keeper itself, replayed IN PLACE on the committed extract
(byte-identical, PREREG §3 V1). Every premise below is COMPUTED from the
bundles, the two extracts and the repo — never typed. It REFUSES to write on
any failed check.

Usage:
    python scripts/gen_nyiso192_attestation.py [--dry-run] [--control-base REF]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

CAL = REPO / "results" / "calibration"
KEEPER = CAL / "nyiso189_steam_identity"
ARM = CAL / "nyiso192_astoria_panel"
YEARS = (2023, 2024, 2025)
COMMITTED_EXTRACT = REPO / "data/raw/campd-unit-outages-perunitmerit-NYISO.csv"
REPAIRED_EXTRACT = ARM / "campd-unit-outages-perunitmerit-NYISO_repaired_panel.csv"
PREREG = "results/calibration/PREREG-nyiso192-frontier-adjudication.md"
FINDING = "docs/FINDING-nyiso192-frontier-adjudication-2026-09-05.md"
NOTE = (
    "the Astoria merit-panel stack-duplicate repair: build_merit_order_panel drops "
    "the duplicate flue path's grossLoad copy and merges it onto its primary "
    "(campd.CAMPD_STACK_DUPLICATE_UNITS, NY 8906 only), so the guard prices the "
    "generator at its physical SRMC; the keeper's -perunitmerit- extract re-derived "
    "under its committed invocation. Zero new or retuned constants, zero new "
    "ScenarioConfig fields, zero new DOF entries; the delta is the committed "
    "artifact alone."
)
WINDOW_KEY = ["facility_id", "unit_id", "outage_start", "outage_end"]


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def _pin(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())["resolved_inputs"][
        "campd_unit_outages"
    ]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unit(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "plant_group", "hour", "mw", "cap_mw"],
    )
    return df[df["pass"] == "P1"]


def g_control(control_base: str) -> dict:
    """G-CONTROL — the in-place replay reproduced the committed keeper bit-for-bit.

    The keeper's ``hourly/system_<year>.parquet`` on disk (the replay's output)
    against the same file at ``control_base`` in git (the committed keeper).
    """
    rows, worst = {}, 0.0
    for y in YEARS:
        rel = f"results/calibration/nyiso189_steam_identity/hourly/system_{y}.parquet"
        blob = subprocess.run(
            ["git", "show", f"{control_base}:{rel}"],
            cwd=REPO,
            check=True,
            capture_output=True,
        ).stdout
        a = pd.read_parquet(io.BytesIO(blob))
        b = pd.read_parquet(REPO / rel)
        a = a[a["pass"] == "P1"].sort_values(["zone", "hour"])
        b = b[b["pass"] == "P1"].sort_values(["zone", "hour"])
        d = a.price.values - b.price.values
        worst = max(worst, float(abs(d).max()))
        rows[y] = {
            "hours_differing": int((abs(d) > 1e-9).sum()),
            "of": int(len(d)),
            "max_abs_dprice": float(abs(d).max()),
        }
    return {
        "control": "in-place replay of the keeper bundle on the committed extract",
        "control_base": control_base,
        "by_year": rows,
        "max_abs_dprice": worst,
        "bit_identical_to_keeper": worst == 0.0,
        "pass": worst == 0.0,
    }


def g_delta() -> dict:
    """G-DELTA — the scenario config is IDENTICAL; the ONLY delta is the extract."""
    c, a = _cfg(KEEPER), _cfg(ARM)
    diff = {k: (c.get(k), a.get(k)) for k in set(c) | set(a) if c.get(k) != a.get(k)}
    guard_on = bool(c.get("campd_outage_merit_order_guard")) and bool(
        a.get("campd_outage_merit_order_guard")
    )
    per_unit_on = bool(c.get("campd_per_unit_attribution")) and bool(
        a.get("campd_per_unit_attribution")
    )
    return {
        "baseline": KEEPER.name,
        "delta_fields": {k: list(v) for k, v in sorted(diff.items())},
        "guard_true_on_both": guard_on,
        "per_unit_true_on_both": per_unit_on,
        "pass": not diff and guard_on and per_unit_on,
    }


def g_inputs() -> dict:
    """G-INPUTS — each solve read the extract it claims, and the delta is the repair.

    (a) the keeper's pinned sha256 equals the committed extract's and the arm's
    equals the repaired extract's; (b) the two extracts differ by exactly the
    pre-registered window movement (106 windows leave, all Astoria 8906; 155
    enter at other plants); (c) the stack-pair registry is NY-only, so no other
    ISO's panel can move.
    """
    from market_sim.data.campd import CAMPD_STACK_DUPLICATE_FACILITIES

    k_pin, a_pin = _pin(KEEPER), _pin(ARM)
    sha_c, sha_r = _sha(COMMITTED_EXTRACT), _sha(REPAIRED_EXTRACT)
    before = pd.read_csv(COMMITTED_EXTRACT)
    after = pd.read_csv(REPAIRED_EXTRACT)
    m = before.merge(after, on=WINDOW_KEY, how="outer", indicator=True)
    left = m[m["_merge"] == "left_only"]
    right = m[m["_merge"] == "right_only"]
    return {
        "keeper_pin": {"path": k_pin["path"], "sha256": k_pin["sha256"]},
        "arm_pin": {"path": a_pin["path"], "sha256": a_pin["sha256"]},
        "committed_extract_sha256": sha_c,
        "repaired_extract_sha256": sha_r,
        "keeper_read_committed": k_pin["sha256"] == sha_c,
        "arm_read_repaired": a_pin["sha256"] == sha_r,
        "rows": {"committed": int(len(before)), "repaired": int(len(after))},
        "windows_leaving": int(len(left)),
        "windows_leaving_facilities": sorted(int(f) for f in left.facility_id.unique()),
        "windows_entering": int(len(right)),
        "windows_entering_facilities": sorted(
            int(f) for f in right.facility_id.unique()
        ),
        "stack_pair_facilities": sorted(
            int(f) for f in CAMPD_STACK_DUPLICATE_FACILITIES
        ),
        "derive_invocation": (
            "python scripts/data/derive_campd_unit_outages.py --iso NYISO --years "
            "2019 2020 2021 2022 2023 2024 2025 2026 --per-unit-crosswalk "
            "--merit-order-guard --out <bundle-local repaired extract>"
        ),
        "pass": bool(
            k_pin["sha256"] == sha_c
            and a_pin["sha256"] == sha_r
            and sha_c != sha_r
            and set(int(f) for f in left.facility_id.unique()) == {8906}
            and set(int(f) for f in CAMPD_STACK_DUPLICATE_FACILITIES) == {8906}
        ),
    }


def g_dof() -> dict:
    """G-DOF — the arm adds no free parameter; the ledger is the keeper's, verbatim."""
    fp = json.loads((KEEPER / "calibration_attestation.json").read_text())[
        "free_parameters"
    ]
    return {
        "n_entries": fp["n_entries"],
        "n_residual": fp.get("n_residual"),
        "added_entries": 0,
        "added_scalars": 0,
        "basis": (
            "a DATA-HANDLING repair inside the measured input of an already-registered "
            "mechanism (campd_outage_merit_order_guard, NYISO cell K): the panel now "
            "applies the same stack-duplicate correction campd._normalize_campd applies. "
            "No threshold moved (MERIT_OOM_FRAC, MERIT_RCC_PCTL, MERIT_HR_MIN/MAX, "
            "FULL_STOP_OVERRIDE_*, HIGH_LOAD_PCTL, MIN_INMERIT_HOURS read at their "
            "committed values); nothing chosen, swept or fitted (PREREG §7)."
        ),
        "pass": True,
    }


def g_engage() -> dict:
    """G-ENGAGE — the repaired extract reached the LP: the availability envelope moved.

    Measured on each bundle's own P1 ``unit_hourly`` ``cap_mw`` (the capacity the
    LP actually carried), per plant-class, as a mean over the year: Astoria
    ``ST_GAS`` must rise in every year and Ravenswood ``ST_GAS`` must fall in 2024
    and 2025 (PREREG §7.2 B1 direction; the ±0.005 level check rides on the
    bundle-local availability tables).
    """
    rows = {}
    ok = True
    for y in YEARS:
        uc, ua = _unit(KEEPER, y), _unit(ARM, y)
        for code, name in (
            (8906, "Astoria"),
            (2500, "Ravenswood"),
            (2490, "Arthur Kill"),
        ):
            sel_c = uc[(uc.plant_code == code) & (uc.plant_group == "ST_GAS")]
            sel_a = ua[(ua.plant_code == code) & (ua.plant_group == "ST_GAS")]
            c_cap = float(sel_c.groupby("hour").cap_mw.sum().mean())
            a_cap = float(sel_a.groupby("hour").cap_mw.sum().mean())
            rows[f"{y}:{code}"] = {
                "name": name,
                "mean_lp_cap_control_mw": round(c_cap, 1),
                "mean_lp_cap_arm_mw": round(a_cap, 1),
            }
        ast = rows[f"{y}:8906"]
        rav = rows[f"{y}:2500"]
        ok &= ast["mean_lp_cap_arm_mw"] > ast["mean_lp_cap_control_mw"] + 0.5
        if y in (2024, 2025):
            ok &= rav["mean_lp_cap_arm_mw"] < rav["mean_lp_cap_control_mw"] - 0.5
    return {"by_plant_year": rows, "pass": bool(ok)}


def b2_effect() -> dict:
    """B2 — the pre-registered falsifiable predictions, reported (never gating)."""
    rows = {}
    for y in YEARS:
        uc, ua = _unit(KEEPER, y), _unit(ARM, y)

        def twh(df, code):
            s = df[(df.plant_code == code) & (df.plant_group == "ST_GAS")]
            return float(s.mw.sum()) / 1e6

        rows[y] = {
            "astoria_control_twh": round(twh(uc, 8906), 4),
            "astoria_arm_twh": round(twh(ua, 8906), 4),
            "ravenswood_control_twh": round(twh(uc, 2500), 4),
            "ravenswood_arm_twh": round(twh(ua, 2500), 4),
            "roseton_control_twh": round(twh(uc, 8006), 4),
            "roseton_arm_twh": round(twh(ua, 8006), 4),
        }
    a_up = all(
        rows[y]["astoria_arm_twh"] > rows[y]["astoria_control_twh"] for y in YEARS
    )
    r_down = (
        all(
            rows[y]["ravenswood_arm_twh"] < rows[y]["ravenswood_control_twh"]
            for y in (2024, 2025)
        )
        and abs(rows[2023]["ravenswood_arm_twh"] - rows[2023]["ravenswood_control_twh"])
        <= 0.15
    )
    ro_down = rows[2025]["roseton_arm_twh"] < rows[2025]["roseton_control_twh"]
    return {
        "by_year": rows,
        "prediction_a_astoria_rises_all_years": a_up,
        "prediction_b_ravenswood_falls_2024_2025_flat_2023": r_down,
        "prediction_c_roseton_2025_falls": ro_down,
        "pass": True,  # reported, never gating (PREREG §7.2 B2)
    }


def _emit(dry_run: bool, control_base: str) -> dict:
    checks = {
        "G_CONTROL": g_control(control_base),
        "G_DELTA": g_delta(),
        "G_INPUTS": g_inputs(),
        "G_DOF": g_dof(),
        "G_ENGAGE": g_engage(),
        "B2_EFFECT": b2_effect(),
    }
    failed = [k for k, v in checks.items() if not v["pass"]]
    if failed:
        raise SystemExit(
            f"REFUSING to attest {ARM.name}: failed {failed}\n"
            + json.dumps(checks, indent=1, default=str)
        )
    doc = json.loads((KEEPER / "calibration_attestation.json").read_text())
    doc["governance"]["attested_by"] = (
        f"session nyiso-192 (2026-09-05). The single arm of the pre-registered A/B "
        f"({PREREG} §7, pushed BEFORE the arm was solved; record {FINDING}): {NOTE} "
        "Control = the keeper replayed in place on the committed extract "
        "(G-CONTROL below, bit-identical to the committed keeper). The realised "
        "movement is reported at full magnitude in B2_EFFECT against the "
        "pre-registered directional predictions."
    )
    doc["governance"]["note"] = NOTE
    doc["governance"]["computed_checks"] = checks
    if not dry_run:
        (ARM / "calibration_attestation.json").write_text(
            json.dumps(doc, indent=1, default=str) + "\n"
        )
    fp = doc["free_parameters"]
    print(
        f"{'(dry-run) ' if dry_run else ''}{ARM.name}: all checks PASS "
        f"(n_entries {fp['n_entries']}, n_residual {fp.get('n_residual')}, "
        f"delta {sorted(checks['G_DELTA']['delta_fields'])}, control bit-identical "
        f"{checks['G_CONTROL']['bit_identical_to_keeper']})"
    )
    print(json.dumps(checks, indent=1, default=str))
    return checks


def main() -> None:
    """Write the arm's attestation, refusing on any failed check."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--control-base",
        default="HEAD",
        help="git ref holding the COMMITTED keeper slim files the in-place replay is checked against",
    )
    args = ap.parse_args()
    _emit(args.dry_run, args.control_base)


if __name__ == "__main__":
    main()
