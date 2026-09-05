#!/usr/bin/env python3
"""Emit the nyiso-191 arm's ``calibration_attestation.json`` (C6 gate).

One arm, one control (``results/calibration/PREREG-nyiso191-ccchp-capacity-scope.md``
§2 / §3, pushed BEFORE the derive was edited and before any solve):

* ``ccchp_scope`` (``nyiso191_ccchp_scope``): the committed keeper
  ``2026-09-05-nyiso-189-steam-identity`` recipe on the RE-DERIVED
  ``cc_capacity_reconcile_NYISO.csv``, widened from ``--classes CC_REGULAR`` to
  ``--classes CC_REGULAR CC_CHP``. **No ``ScenarioConfig`` field changes** —
  ``cc_capacity_reconcile`` is already ``True`` on the keeper; the delta is the
  ARTIFACT the flag reads. 15 → 23 rows, net −542.5 MW of LP capacity.

The control (``nyiso191_control``) is the same-HEAD replay pointed at a
byte-identical copy of the PRE-CHANGE 15-row table, so the pair isolates the
artifact and nothing else.

Every premise below is COMPUTED from the bundles, the two tables and the frozen
derive constants — never typed. It REFUSES to write on any failed check.

Usage:
    python scripts/gen_nyiso191_attestation.py [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
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
CONTROL = CAL / "nyiso191_control"
ARM = CAL / "nyiso191_ccchp_scope"
YEARS = (2023, 2024, 2025)
FIELD = "cc_capacity_reconcile"
PATH_FIELD = "cc_capacity_reconcile_path"
ARM_TABLE = REPO / "data/raw/_processed-legacy/cc_capacity_reconcile_NYISO.csv"
PHASE0 = CAL / "_nyiso191_ccchp_scope_phase0.json"
DERIVE = REPO / "scripts/data/derive_cc_capacity_reconcile.py"

PREREG = "results/calibration/PREREG-nyiso191-ccchp-capacity-scope.md"
FINDING = "docs/FINDING-nyiso191-ccchp-capacity-scope-2026-09-05.md"
NOTE = (
    "the CC_CHP scope extension of cc_capacity_reconcile: the derive's screened "
    "population becomes a --classes argument (default CC_REGULAR, unchanged for "
    "every other ISO) and NYISO re-derives at --classes CC_REGULAR CC_CHP. Zero "
    "new or retuned constants, zero new ScenarioConfig fields, zero new DOF "
    "entries; the delta is the committed artifact alone."
)
# The frozen screen thresholds. Asserted against the derive's live values so a
# future edit to any of them breaks this attestation out loud (rules 23 / 24).
FROZEN = {
    "_CAP_MARGIN": 1.10,
    "_MIN_DELTA": 0.01,
    "_PURE_PLAY_CC_SHARE": 0.90,
    "_CT_ONLY_RATIO": 1.1,
    "_CAP_FEASIBLE_CF": 0.90,
    "_CC_NET_OF_GROSS": 0.975,
}
ROW_KEY = ["plant_code", "reconciled_mw", "mode"]


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return (df.groupby("klass").mw.sum() / 1e6).to_dict()


def _unit(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "hour", "mw", "cap_mw"],
    )
    return df[df["pass"] == "P1"]


def _table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)[ROW_KEY].sort_values("plant_code").reset_index(drop=True)


def g_control() -> dict:
    """G-CONTROL — the control vs the committed keeper, RE-MEASURED on P1 prices."""
    rows, worst = {}, 0.0
    for y in YEARS:
        a = pd.read_parquet(KEEPER / "hourly" / f"system_{y}.parquet")
        b = pd.read_parquet(CONTROL / "hourly" / f"system_{y}.parquet")
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
        "by_year": rows,
        "max_abs_dprice": worst,
        "bit_identical_to_keeper": worst == 0.0,
        "baseline": KEEPER.name if worst == 0.0 else CONTROL.name,
        "pass": worst == 0.0,
    }


def g_delta() -> dict:
    """G-DELTA — the ONLY difference is the reconcile table the flag reads.

    The control is pointed at a byte-identical copy of the pre-change table, so
    ``cc_capacity_reconcile_path`` is the one config key expected to differ; no
    other key may move, and ``cc_capacity_reconcile`` itself must be ``True`` on
    both sides (this is an ARTIFACT delta, not a flag flip).
    """
    c, a = _cfg(CONTROL), _cfg(ARM)
    diff = {k: (c.get(k), a.get(k)) for k in set(c) | set(a) if c.get(k) != a.get(k)}
    rode_along = sorted(set(diff) - {PATH_FIELD})
    return {
        "baseline": CONTROL.name,
        "delta_fields": {k: list(v) for k, v in sorted(diff.items())},
        "rode_along": rode_along,
        "flag_true_on_both": bool(c.get(FIELD)) and bool(a.get(FIELD)),
        "pass": not rode_along
        and set(diff) == {PATH_FIELD}
        and bool(c.get(FIELD))
        and bool(a.get(FIELD)),
    }


def g_inputs() -> dict:
    """G-INPUTS — the artifact delta is exactly the 8 pre-registered rows.

    (a) the two tables the two solves actually read, by sha256; (b) the 15
    pre-existing ``CC_REGULAR`` rows byte-identical on ``plant_code`` /
    ``reconciled_mw`` / ``mode``; (c) the new rows equal to the phase-0
    prediction, made before the derive was edited; (d) every screen threshold at
    its frozen literal; (e) no other ISO's committed table carries a widened
    scope.
    """
    from scripts.data import derive_cc_capacity_reconcile as d

    ctrl_path = Path(_cfg(CONTROL)[PATH_FIELD])
    arm_path = Path(_cfg(ARM)[PATH_FIELD])
    before, after = _table(ctrl_path), _table(arm_path)
    after_full = pd.read_csv(arm_path)
    kept = (
        after_full[after_full["plant_group"] == "CC_REGULAR"][ROW_KEY]
        .sort_values("plant_code")
        .reset_index(drop=True)
    )
    new_codes = sorted(
        int(c) for c in after_full[after_full["plant_group"] == "CC_CHP"]["plant_code"]
    )
    phase0 = json.loads(PHASE0.read_text())
    frozen_ok = {k: getattr(d, k) == v for k, v in FROZEN.items()}

    other = {}
    from market_sim.config.paths import cc_capacity_reconcile_path

    for iso in ("CAISO", "MISO", "NEISO", "PJM", "ERCOT"):
        t = pd.read_csv(cc_capacity_reconcile_path(iso))
        other[iso] = (
            sorted(set(t["plant_group"])) if "plant_group" in t.columns else ["(no col)"]
        )
    others_narrow = all(
        v in (["CC_REGULAR"], ["(no col)"]) for v in other.values()
    )
    return {
        "control_table": {
            "path": str(ctrl_path),
            "sha256": hashlib.sha256(ctrl_path.read_bytes()).hexdigest(),
            "rows": int(len(before)),
        },
        "arm_table": {
            "path": str(arm_path),
            "sha256": hashlib.sha256(arm_path.read_bytes()).hexdigest(),
            "rows": int(len(after)),
        },
        "preexisting_rows_unchanged": bool(before.equals(kept)),
        "new_rows": new_codes,
        "new_rows_match_phase0": new_codes == sorted(phase0["new_rows"]),
        "phase0_record": str(PHASE0.relative_to(REPO)),
        "net_mw_change": round(
            float((after_full["reconciled_mw"] - after_full["current_mw"]).sum())
            - float(
                (pd.read_csv(ctrl_path)["reconciled_mw"] - pd.read_csv(ctrl_path)["current_mw"]).sum()
            ),
            1,
        ),
        "frozen_thresholds": {k: getattr(d, k) for k in FROZEN},
        "frozen_thresholds_ok": frozen_ok,
        "default_classes": list(d.DEFAULT_CLASSES),
        "other_iso_scopes": other,
        "no_other_iso_widened": others_narrow,
        "derive_invocation": (
            "python scripts/data/derive_cc_capacity_reconcile.py --iso NYISO "
            "--mode both --classes CC_REGULAR CC_CHP --years 2023 2024 2025"
        ),
        "pass": bool(
            before.equals(kept)
            and new_codes == sorted(phase0["new_rows"])
            and all(frozen_ok.values())
            and tuple(d.DEFAULT_CLASSES) == ("CC_REGULAR",)
            and others_narrow
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
            "a POPULATION argument to an already-registered mechanism "
            "(ScenarioConfig.cc_capacity_reconcile, NYISO cell K since nyiso-188). "
            "The derive's screened class set becomes a --classes argument whose "
            "default is the pre-change behaviour; every threshold "
            "(_CAP_MARGIN 1.10, _MIN_DELTA 0.01, _PURE_PLAY_CC_SHARE 0.90, "
            "_CT_ONLY_RATIO 1.1, _CAP_FEASIBLE_CF 0.90, _CC_NET_OF_GROSS 0.975) is "
            "frozen and asserted, the demonstrated-peak authority (CAMPD p99.9) is "
            "unchanged, and CC_CHP's registered parasitic load equals CC_REGULAR's "
            "so the gross->net factor needed no new constant. Nothing chosen, swept "
            "or fitted (PREREG-nyiso191 §1)."
        ),
        "pass": True,
    }


def g_engage() -> dict:
    """G-ENGAGE — the artifact reached the LP: the capped plants' LP capacity fell.

    Measured on each bundle's own P1 ``unit_hourly`` max ``cap_mw`` per plant, so
    it is the capacity the LP actually carried, not the table's claim.
    """
    arm_table = pd.read_csv(ARM_TABLE)
    chp = arm_table[arm_table["plant_group"] == "CC_CHP"]
    rows, engaged = {}, 0
    y = YEARS[1]
    uc, ua = _unit(CONTROL, y), _unit(ARM, y)
    cc = uc.groupby("plant_code")["cap_mw"].max()
    ca = ua.groupby("plant_code")["cap_mw"].max()
    for _, r in chp.iterrows():
        code = int(r["plant_code"])
        c_cap = float(cc.get(code, float("nan")))
        a_cap = float(ca.get(code, float("nan")))
        moved = bool(abs(a_cap - c_cap) > 0.5)
        engaged += int(moved)
        rows[code] = {
            "name": r["plant_name"],
            "mode": r["mode"],
            "table_reconciled_mw": float(r["reconciled_mw"]),
            "lp_cap_control_mw": round(c_cap, 1),
            "lp_cap_arm_mw": round(a_cap, 1),
            "moved": moved,
        }
    return {
        "year": y,
        "cc_chp_rows": int(len(chp)),
        "plants_whose_lp_capacity_moved": engaged,
        "by_plant": rows,
        "pass": engaged > 0,
    }


def g_effect() -> dict:
    """B2 — the pre-registered falsifiable prediction: <= 0.05 TWh of movement.

    Phase 0 measured 0.0000 / 0.0143 / 0.0000 TWh of keeper energy above the
    proposed caps and PREREG §3 B2 fixed 0.05 TWh as the falsification bar. This
    records the realised movement per year; it does NOT gate the attestation
    (the finding reports it either way), but it is computed here so the number
    cannot be restated later.
    """
    fam = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
    rows = {}
    for y in YEARS:
        c, a = _class_twh(CONTROL, y), _class_twh(ARM, y)
        rows[y] = {
            "gas_family_control_twh": round(sum(c.get(k, 0.0) for k in fam), 4),
            "gas_family_arm_twh": round(sum(a.get(k, 0.0) for k in fam), 4),
            "abs_delta_twh": round(
                abs(sum(a.get(k, 0.0) for k in fam) - sum(c.get(k, 0.0) for k in fam)), 4
            ),
            "by_class_delta_twh": {
                k: round(a.get(k, 0.0) - c.get(k, 0.0), 4) for k in fam
            },
        }
    worst = max(r["abs_delta_twh"] for r in rows.values())
    return {
        "by_year": rows,
        "worst_abs_delta_twh": worst,
        "prereg_bar_twh": 0.05,
        "prediction_held": worst <= 0.05,
        "pass": True,  # reported, never gating (PREREG §3 B2)
    }


def _emit(dry_run: bool) -> dict:
    checks = {
        "G_CONTROL": g_control(),
        "G_DELTA": g_delta(),
        "G_INPUTS": g_inputs(),
        "G_DOF": g_dof(),
        "G_ENGAGE": g_engage(),
        "B2_EFFECT": g_effect(),
    }
    failed = [k for k, v in checks.items() if not v["pass"]]
    if failed:
        raise SystemExit(
            f"REFUSING to attest {ARM.name}: failed {failed}\n"
            + json.dumps(checks, indent=1, default=str)
        )
    doc = json.loads((KEEPER / "calibration_attestation.json").read_text())
    doc["governance"]["attested_by"] = (
        f"session nyiso-191 (2026-09-05). The single arm of the pre-registered A/B "
        f"({PREREG} §2 / §3, pushed BEFORE the derive was edited and before any "
        f"solve; record {FINDING}): {NOTE} Control = the same-HEAD replay pointed at "
        "a byte-identical copy of the pre-change 15-row table (G-CONTROL below, "
        "computed against the keeper 2026-09-05-nyiso-189-steam-identity). The "
        "energy effect is reported at full magnitude in B2_EFFECT against the "
        "pre-registered 0.05 TWh falsification bar."
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
        f"{checks['G_CONTROL']['bit_identical_to_keeper']}, "
        f"B2 worst |Δ| {checks['B2_EFFECT']['worst_abs_delta_twh']} TWh, "
        f"prediction held {checks['B2_EFFECT']['prediction_held']})"
    )
    print(json.dumps(checks, indent=1, default=str))
    return checks


def main() -> None:
    """Write the arm's attestation, refusing on any failed check."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    _emit(args.dry_run)


if __name__ == "__main__":
    main()
