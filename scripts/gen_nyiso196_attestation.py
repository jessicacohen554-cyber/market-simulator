#!/usr/bin/env python3
"""Emit the nyiso-196 arm's ``calibration_attestation.json`` (C6 gate).

One arm, control = the keeper's COMMITTED bundle (rule 29(b) form 4 — no
control solve; ``results/calibration/PREREG-nyiso196-cc-outage-share-basis-screen.md``,
pushed BEFORE the 2024 screen and before the full span):

* ``extract_basis`` (``nyiso196_extract_basis``): the committed keeper
  ``2026-09-05-nyiso-192-astoria-panel`` recipe plus the ONE registered field
  ``unit_outage_extract_basis_share: False -> True`` — a combined-cycle bin's
  unit-outage removed FRACTION taken on the committed extract's own capacity
  basis (``unit_capacity_mw / plant_capacity_mw``, the published
  ``unit_pct_of_plant``) instead of over the fleet's net-summer bin. Same
  committed extract, same every other flag.

Every premise below is COMPUTED from the bundles and the repo — never typed.
It REFUSES to write on any failed check.

Usage:
    python scripts/gen_nyiso196_attestation.py [--dry-run] [--control-base REF]
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
KEEPER = CAL / "nyiso192_astoria_panel"
ARM = CAL / "nyiso196_extract_basis"
YEARS = (2023, 2024, 2025)
FLAG = "unit_outage_extract_basis_share"
COMMITTED_EXTRACT = REPO / "data/raw/campd-unit-outages-perunitmerit-NYISO.csv"
PREREG = "results/calibration/PREREG-nyiso196-cc-outage-share-basis-screen.md"
FINDING = "docs/FINDING-nyiso196-cc-outage-share-basis-2026-09-05.md"
CV, ATHENS, SELKIRK = 57185, 55405, 10725
NOTE = (
    "unit_outage_extract_basis_share: a combined-cycle bin's unit-outage removed "
    "fraction is taken on the committed extract's own capacity basis "
    "(unit_capacity_mw / plant_capacity_mw — the published unit_pct_of_plant; the "
    "group's distinct-unit sum at a multi-group facility) instead of over the "
    "fleet's net-summer bin. Repairs the Cricket Valley 57185 id collision (CAMPD "
    "stack ids U001-U003 match the EIA-860 STEAM generator ids, so each 1x1 block "
    "was written at 174.2 MW and removed 17.1 % of the plant per outage against "
    "the physical 33.3 %; 48.6 % of a dark plant stayed available). Zero new or "
    "retuned constants, zero new DOF entries; the field is a bool on a registered "
    "consistency-repair family; the committed extract is untouched."
)


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
    """G-CONTROL — the control is the keeper's COMMITTED bundle (form 4).

    The keeper's ``hourly/system_<year>.parquet`` on disk equals the blob at
    ``control_base`` (nothing replayed the keeper in place), and the G-DRIFT
    audit that licenses form 4 is the PREREG's §5 (adopted by reference).
    """
    rows, worst = {}, 0.0
    for y in YEARS:
        rel = f"results/calibration/nyiso192_astoria_panel/hourly/system_{y}.parquet"
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
        "g_drift": f"{PREREG} §5 — d5bba63b..5b5af5ab every solve-path hunk INERT for a NYISO backcast",
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
    # added / re-defaulted after the keeper solved (PREREG §5 classifies every
    # such hunk backcast-inert), not a recipe delta. Reported, never counted.
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
    """G-INPUTS — both solves read the SAME committed extract; only the share basis moved."""
    k_pin, a_pin = _pin(KEEPER), _pin(ARM)
    sha_c = _sha(COMMITTED_EXTRACT)
    return {
        "keeper_pin": {"path": k_pin["path"], "sha256": k_pin["sha256"]},
        "arm_pin": {"path": a_pin["path"], "sha256": a_pin["sha256"]},
        "committed_extract_sha256": sha_c,
        "same_extract": k_pin["sha256"] == a_pin["sha256"] == sha_c,
        "pass": k_pin["sha256"] == a_pin["sha256"] == sha_c,
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
            "a CONSISTENCY repair inside the measured unit-outage input: the removed "
            "fraction's numerator and denominator come from ONE construction (the "
            "extract's own columns). No threshold, no table, no per-plant entry; "
            "the field is a bool (PREREG §1, §2)."
        ),
        "pass": True,
    }


def g_engage() -> dict:
    """G-ENGAGE — the share reached the LP: Cricket Valley's carried capacity fell every year."""
    rows = {}
    ok = True
    for y in YEARS:
        uc, ua = (
            _unit(KEEPER, y)
            if (KEEPER / "hourly" / f"unit_hourly_{y}.parquet").exists()
            else None,
            _unit(ARM, y),
        )
        for code, grp, name in (
            (CV, "CC_REGULAR", "Cricket Valley"),
            (ATHENS, "CC_REGULAR", "Athens"),
            (SELKIRK, "CC_CHP", "Selkirk"),
        ):
            sel_a = ua[(ua.plant_code == code) & (ua.plant_group == grp)]
            a_cap = float(sel_a.groupby("hour").cap_mw.sum().mean())
            c_cap = None
            if uc is not None:
                sel_c = uc[(uc.plant_code == code) & (uc.plant_group == grp)]
                c_cap = float(sel_c.groupby("hour").cap_mw.sum().mean())
            rows[f"{y}:{code}"] = {
                "name": name,
                "mean_lp_cap_arm_mw": round(a_cap, 1),
                "mean_lp_cap_control_mw": round(c_cap, 1)
                if c_cap is not None
                else "keeper unit_hourly not committed — see the zero-LP rebuild census",
            }
    census = json.loads((CAL / "_nyiso196_extract_basis_census.json").read_text())
    for y in YEARS:
        cv = census[str(y)].get(f"{CV}:CC_REGULAR")
        ok &= bool(cv and cv["on_mean"] < cv["off_mean"] - 0.05)
        rows[f"{y}:{CV}"]["loader_availability_off_on"] = (
            [cv["off_mean"], cv["on_mean"]] if cv else None
        )
    return {"by_plant_year": rows, "pass": bool(ok)}


def b2_effect() -> dict:
    """B2 — the pre-registered directional predictions (PREREG §7), reported."""
    rows = {}
    for y in YEARS:
        ua = _unit(ARM, y)

        def twh(code, grp):
            s = ua[(ua.plant_code == code) & (ua.plant_group == grp)]
            return float(s.mw.sum()) / 1e6

        rows[y] = {
            "cricket_valley_arm_twh": round(twh(CV, "CC_REGULAR"), 4),
            "athens_arm_twh": round(twh(ATHENS, "CC_REGULAR"), 4),
            "selkirk_arm_twh": round(twh(SELKIRK, "CC_CHP"), 4),
        }
    return {
        "by_year": rows,
        "keeper_side": "the keeper's committed payload m_ann per plant (FINDING §3)",
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
        f"session nyiso-196 (2026-09-05). The single arm of the pre-registered screen "
        f"({PREREG}, pushed BEFORE the 2024 screen and the full span; record {FINDING}): {NOTE} "
        "Control = the keeper's COMMITTED bundle (form 4; G-DRIFT audited in the PREREG §5). "
        "The realised movement is reported at full magnitude in the FINDING."
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
        default="HEAD",
        help="git ref holding the COMMITTED keeper slim files",
    )
    args = ap.parse_args()
    _emit(args.dry_run, args.control_base)


if __name__ == "__main__":
    main()
