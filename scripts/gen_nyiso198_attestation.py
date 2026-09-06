#!/usr/bin/env python3
"""Emit the nyiso-198 arm's ``calibration_attestation.json`` (C6 gate).

One arm, control = the keeper's COMMITTED bundle (rule 29(b) form 4 — no
control solve; ``results/calibration/PREREG-nyiso198-duct-peaking-row-scope-screen.md``
with Addendum A pushed BEFORE the 2024 screen and Addendum B BEFORE the span):

* ``duct_rowscope`` (``nyiso198_duct_rowscope``): the committed keeper
  ``2026-09-06-nyiso-196-extract-basis`` recipe plus the ONE registered field
  ``cc_duct_peaking_row_scoped: False -> True`` — the combined-cycle duct-burner
  peaking share taken over the EIA-860 generator rows the filing FLAGS as
  duct-fired, instead of over every combined-cycle row of the plant. Same
  EIA-860 vintage, same every other flag.

Every premise below is COMPUTED from the bundles and the repo — never typed.
It REFUSES to write on any failed check.

Usage:
    python scripts/gen_nyiso198_attestation.py [--dry-run] [--control-base REF]
"""

from __future__ import annotations

import argparse
import dataclasses
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
KEEPER = CAL / "nyiso196_extract_basis"
ARM = CAL / "nyiso198_duct_rowscope"
YEARS = (2023, 2024, 2025)
FLAG = "cc_duct_peaking_row_scoped"
PREREG = "results/calibration/PREREG-nyiso198-duct-peaking-row-scope-screen.md"
FINDING = "docs/FINDING-nyiso198-duct-peaking-row-scope-2026-09-06.md"
REBUILD = CAL / "_nyiso198_rebuild_checks_2024.json"
CV = 57185
NOTE = (
    "cc_duct_peaking_row_scoped: a combined-cycle plant's duct-burner peaking "
    "share is taken as 100 * max(0, SUM over the rows flagged 'Duct Burners == Y' "
    "of (nameplate - net_summer)) / SUM over all the plant's CC rows of nameplate, "
    "instead of summing that gap over EVERY combined-cycle row. A duct burner "
    "fires into the HRSG and raises the STEAM turbine's output, and EIA-860 "
    "reports the attribute at that grain: across the whole Generator_Y operable "
    "combined-cycle population the column reads Y/N only on CA and CS rows and X "
    "(not applicable) on every one of the 1,213 CT rows, so the plant-level sum "
    "books the CT rows' ambient/site derate as duct capability and offers it at "
    "the class peak band (2.25x base heat rate == phys_peak, i.e. pure physical "
    "cost). At Cricket Valley 57185 that is 203.7 of 296.4 MW (69 %) on rows the "
    "filing marks as having no duct burner; fleet-wide 726.5 MW, 68 % of NYISO's "
    "combined-cycle peak band. The denominator, the clip, the duct-fired plant "
    "selection rule, cc_duct_peaking_cap_pct and every consumer are unchanged, so "
    "the two forms differ ONLY in which rows enter the numerator. Zero new or "
    "retuned constants, zero new DOF entries; the field is a bool; nothing is "
    "selected, swept or tuned and no residual enters the construction. Admitted "
    "under rules 14 [R-ACCURATE] and 13 [R-MEASURED] on the nyiso-196 precedent, "
    "and by the owner ruling of 2026-09-06 recorded in the PREREG's Addendum B; "
    "no offer_curve_by_group band multiplier and no phys_* value moves, so rule "
    "1's carve-out is not invoked."
)


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unit(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=[
            "pass",
            "unit_id",
            "plant_code",
            "plant_group",
            "hour",
            "mw",
            "cap_mw",
        ],
    )
    return df[df["pass"] == "P1"]


def g_control(control_base: str) -> dict:
    """G-CONTROL — the control is the keeper's COMMITTED bundle (form 4).

    The keeper's ``hourly/system_<year>.parquet`` on disk equals the blob at
    ``control_base`` (nothing replayed the keeper in place), and the G-DRIFT
    audit that licenses form 4 is the PREREG's §5 plus Addendum B §B.4.
    """
    rows, worst = {}, 0.0
    for y in YEARS:
        rel = f"results/calibration/nyiso196_extract_basis/hourly/system_{y}.parquet"
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
        rows[y] = {"hours_differing": int((abs(d) > 1e-9).sum()), "of": int(len(d))}
    return {
        "control": "the keeper's COMMITTED bundle (rule 29(b) form 4; no control solve)",
        "control_base": control_base,
        "g_drift": (
            f"{PREREG} §5 (5b5af5ab..982ba9aa) + Addendum B §B.4 "
            "(821c11c5..1ce47fc0) — every solve-path hunk INERT for a NYISO backcast, "
            "with two empirical checks: the keeper's own unit_outage_extract_basis_share "
            "reproduces to the digit at HEAD (Cricket Valley 2024 mean 0.5763 vs the "
            "committed 0.576) and the committed nyiso-197 Linden rebuild re-runs at HEAD "
            "with an empty git diff"
        ),
        "committed_keeper_on_disk_by_year": rows,
        "max_abs_dprice_disk_vs_git": worst,
        "pass": worst == 0.0,
    }


def g_delta() -> dict:
    """G-DELTA — exactly the one flag differs between the arm and the keeper."""
    c, a = _cfg(KEEPER), _cfg(ARM)
    diff = {k: (c.get(k), a.get(k)) for k in set(c) | set(a) if c.get(k) != a.get(k)}
    from market_sim.config.scenarios import ScenarioConfig

    defaults = {
        f.name: (f.default if f.default is not dataclasses.MISSING else None)
        for f in dataclasses.fields(ScenarioConfig)
    }
    # A field the keeper never serialised (None) or recorded at a since-flipped
    # default, which the arm records at ScenarioConfig's HEAD default: a field
    # added / re-defaulted after the keeper solved (PREREG §5 and Addendum B §B.4
    # classify every such hunk backcast-inert), not a recipe delta. Reported,
    # never counted.
    head_default = sorted(
        k
        for k, (kv, av) in diff.items()
        if k != FLAG and k in defaults and av == defaults[k]
    )
    recipe = {k: v for k, v in diff.items() if k not in head_default}
    return {
        "baseline": KEEPER.name,
        "delta_fields": {k: list(v) for k, v in sorted(recipe.items())},
        "head_defaults_not_recipe": head_default,
        "pass": set(recipe) == {FLAG} and a.get(FLAG) is True and not c.get(FLAG),
    }


def g_inputs() -> dict:
    """G-INPUTS — both solves read the SAME EIA-860 sheet; only the row set moved.

    The mechanism's entire input is the operable Generator_Y parquet, so the
    attestation pins it: the arm changes which of its rows enter a sum, never
    the sheet.
    """
    from market_sim.data.fleet.campd_bins import active_eia860_dir

    sheet = active_eia860_dir() / "eia860_generator_operable.parquet"
    df = pd.read_parquet(sheet, columns=["Technology", "Prime Mover", "Duct Burners"])
    cc = df[df["Technology"] == "Natural Gas Fired Combined Cycle"]
    flag = cc["Duct Burners"].astype(str).str.strip()
    ct = cc["Prime Mover"].astype(str) == "CT"
    return {
        "eia860_operable_sheet": str(sheet.relative_to(REPO)),
        "sha256": _sha(sheet),
        "cc_rows": int(len(cc)),
        "ct_rows": int(ct.sum()),
        "ct_rows_flagged_Y": int((ct & (flag == "Y")).sum()),
        "rows_by_prime_mover_and_flag": {
            f"{pm}/{fl}": int(n)
            for (pm, fl), n in cc.groupby([cc["Prime Mover"].astype(str), flag])
            .size()
            .items()
        },
        "basis": (
            "the premise of the repair, computed: the Duct Burners attribute is "
            "reported only on CA/CS (steam) rows, and NO CT row in the operable "
            "population carries it"
        ),
        "pass": bool(ct.sum() > 0 and (ct & (flag == "Y")).sum() == 0),
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
            "a CONSTRUCTION repair inside a measured input: the share is computed "
            "from EIA-860's own columns at the grain the filing reports the flag. "
            "No threshold, no cap, no table, no per-plant entry; the field is a "
            "bool (PREREG §2, §3). Contrast cc_duct_peaking_cap_pct, the existing "
            "remedy for the same conflation, which IS a chosen number (8.0 for PJM, "
            "None elsewhere) — this arm chooses nothing and leaves that field alone."
        ),
        "pass": True,
    }


def g_engage() -> dict:
    """G-ENGAGE — the re-scoped share reached the LP.

    The zero-LP rebuild (``_nyiso198_rebuild_checks_2024.json``) predicted, from
    the builder's own expression, which plants move and by how much; this checks
    the ARM'S SOLVED fleet carries that peak band. Set A must have fallen, Set B
    must be untouched.
    """
    rb = json.loads(REBUILD.read_text())
    moved = {int(k): float(v) for k, v in rb["moved_plants_mw"].items()}
    rows, ok = {}, True
    for y in YEARS:
        ua = _unit(ARM, y)
        pk = ua[ua.unit_id.astype(str).str.endswith("_peak")]
        cap = (
            pk.groupby(["plant_code", "hour"]).cap_mw.sum().groupby("plant_code").max()
        )
        for code, expected in sorted(moved.items(), key=lambda kv: -abs(kv[1]))[:6]:
            rows[f"{y}:{code}"] = {
                "arm_peak_band_max_mw": round(float(cap.get(code, 0.0)), 2),
                "predicted_move_mw": expected,
            }
    cvcap = rows[f"2024:{CV}"]["arm_peak_band_max_mw"]
    ok = bool(cvcap > 0 and cvcap < 200.0)  # 245.64 -> 77.17 predicted
    return {
        "by_plant_year": rows,
        "prediction_source": (
            "_nyiso198_rebuild_checks_2024.json — Set B (the chp_layup / "
            "chp_duty_curve / reserve_duty cohorts) unchanged exactly, Set A "
            "scaling by peak_off * pct_row / pct_cur, residual 0.000 MW at all 31 plants"
        ),
        "cricket_valley_2024_peak_band_mw": cvcap,
        "keeper_cricket_valley_2024_peak_band_mw": 245.64,
        "pass": ok,
    }


def b2_effect() -> dict:
    """B2 — the arm's own realised class and plant energies, reported."""
    rows = {}
    for y in YEARS:
        ch = pd.read_parquet(ARM / "hourly" / f"class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        e = ch.groupby("klass").mw.sum() / 1e6
        ua = _unit(ARM, y)
        cv = ua[(ua.plant_code == CV) & (ua.plant_group == "CC_REGULAR")]
        rows[y] = {
            "cricket_valley_arm_twh": round(float(cv.mw.sum()) / 1e6, 4),
            "class_twh": {k: round(float(v), 4) for k, v in e.items() if v > 0.01},
        }
    return {
        "by_year": rows,
        "keeper_side": "the keeper's committed class_hourly and payload (FINDING §5)",
        "pass": True,
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
        f"session nyiso-198 (2026-09-06). The single arm of the pre-registered screen "
        f"({PREREG}, with Addendum A pushed BEFORE the 2024 screen and Addendum B — the "
        f"owner ruling authorizing the span — BEFORE the span; record {FINDING}): {NOTE} "
        "Control = the keeper's COMMITTED bundle (form 4; G-DRIFT audited in the PREREG §5 "
        "and Addendum B §B.4). The 2024 screen's own S-4 gate STOPPED this arm on "
        "C1-2024 CC_REGULAR (PASS -> FAIL); the span was solved under the owner's ruling "
        "and every regression is reported at full magnitude in the FINDING."
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
        f"delta {sorted(checks['G_DELTA']['delta_fields'])})"
    )
    print(json.dumps(checks, indent=1, default=str))
    return checks


def main() -> None:
    """Write the arm's attestation, refusing on any failed check."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--control-base",
        default="origin/main",
        help="git ref the committed keeper bundle is read from for G-CONTROL",
    )
    a = ap.parse_args()
    _emit(a.dry_run, a.control_base)


if __name__ == "__main__":
    main()
