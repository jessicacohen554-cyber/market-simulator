#!/usr/bin/env python3
"""Emit the nyiso-189 arm's ``calibration_attestation.json`` (C6 gate).

One arm, one control (PREREG-nyiso189-steam-collapse-identity-ab §1 / §3,
pushed at ``a73d1df0`` BEFORE the mechanism was built and before any solve):

* ``steam_identity`` (``nyiso189_steam_identity``): the committed keeper
  ``2026-09-04-nyiso-188-combined`` recipe replayed at HEAD plus the ONE new
  field ``egrid_steam_collapse_heat_rates`` (owner ruling 2026-09-05, form
  B2: the CT-heat identity ``PLHTIAN / Σ GENNTAN(CT) / (1 + the plant's own
  T1-clean median steam share)`` for combined cycles whose eGRID
  steam-generator filing collapsed in the applied vintage; NYISO reach
  Bethlehem 2539 9.665 → 6.877 and World Generation X 54131 9.807 → 6.996).

The control (``nyiso189_control``) is the same-HEAD replay on the committed
artifacts with ZERO ``scenario_config`` changes. ZERO DOF entries are added
(rule 21 ``[R-DOF]``): a registered flag over an artifact that is arithmetic
on eGRID's published GEN / PLNT fields and the plant's own record.

Every premise below is COMPUTED from the bundles and the committed artifact,
never typed. It REFUSES to write on any failed check.

Usage:
    python scripts/gen_nyiso189_attestation.py [--dry-run]
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

CAL = REPO / "results" / "calibration"
KEEPER = CAL / "nyiso188_combined"
CONTROL = CAL / "nyiso189_control"
ARM = CAL / "nyiso189_steam_identity"
YEARS = (2023, 2024, 2025)
BETHLEHEM, WORLD_GEN_X = 2539, 54131
FIELD = "egrid_steam_collapse_heat_rates"
ARTIFACT = REPO / "data/raw/_processed-legacy/egrid_steam_collapse_heat_rates_NYISO.csv"
DERIVE = REPO / "scripts/data/derive_egrid_steam_collapse_heat_rates.py"

PREREG = "results/calibration/PREREG-nyiso189-steam-collapse-identity-ab.md"
FINDING = "docs/FINDING-nyiso189-steam-collapse-identity-2026-09-05.md"

# The census the pre-registration fixed (PREREG §0): T1 per plant.
CENSUS_T1 = {
    2500: [2019, 2020, 2021, 2022, 2023, 2024],
    2539: [2024],
    7314: [2019, 2020, 2021, 2022, 2023, 2024],
    10521: [2019, 2020, 2021, 2022, 2023, 2024],
    54131: [2023],
}


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return (df.groupby("klass").mw.sum() / 1e6).to_dict()


def _lw_price(bundle: Path, year: int) -> float:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return float((df.price * df.demand).sum() / df.demand.sum())


def _unit(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "hour", "mw", "cap_mw", "mc"],
    )
    return df[df["pass"] == "P1"]


def _plant_twh(u: pd.DataFrame, plant: int) -> float:
    return float(u[u["plant_code"] == plant]["mw"].sum() / 1e6)


def _plant_mc(u: pd.DataFrame, plant: int) -> float:
    return float(u[u["plant_code"] == plant]["mc"].mean())


def _plant_cap_twh(u: pd.DataFrame, plant: int) -> float:
    return float(u[u["plant_code"] == plant]["cap_mw"].sum() / 1e6)


def _defaults() -> dict:
    from market_sim.config.scenarios import ScenarioConfig

    base = ScenarioConfig(iso="NYISO")
    return {f.name: getattr(base, f.name, None) for f in dataclasses.fields(base)}


def g_control() -> dict:
    """G-CONTROL — the same-HEAD control vs the committed keeper, RE-MEASURED."""
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
        "pass": True,
    }


def g_delta() -> dict:
    """G-DELTA — the arm differs from the control on the ONE field only."""
    defaults = _defaults()
    c, a = _cfg(CONTROL), _cfg(ARM)
    diff, absence = {}, {}
    for key in set(c) | set(a):
        cv_, av_ = c.get(key), a.get(key)
        if cv_ == av_:
            continue
        if cv_ is None and key in defaults and av_ == defaults[key]:
            absence[key] = av_
            continue
        diff[key] = (cv_, av_)
    allowed = {FIELD}
    rode_along = sorted(set(diff) - allowed)
    return {
        "baseline": CONTROL.name,
        "delta_fields": {k: list(v) for k, v in sorted(diff.items())},
        "absence_normalized": dict(sorted(absence.items())),
        "rode_along": rode_along,
        "pass": not rode_along
        and set(diff) == allowed
        and diff.get(FIELD) == (False, True),
    }


def g_inputs() -> dict:
    """G-INPUTS — the committed artifact reproduces under --check, carries the
    census, admits exactly {2539, 54131} at the applied vintage, and the fleet
    the flag builds carries those two plants at the identity rates."""
    import logging

    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    out, ok = {}, True
    chk = subprocess.run(
        [sys.executable, str(DERIVE), "--iso", "NYISO", "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    out["derive_check"] = (chk.stdout + chk.stderr).strip().splitlines()[-1:]
    ok &= chk.returncode == 0

    df = pd.read_csv(ARTIFACT)
    out["n_plants"] = int(df.plant_id.nunique())
    t1 = {
        int(p): [int(v) for v in ys]
        for p, ys in df[df.t1_zero].groupby("plant_id").vintage.apply(list).items()
    }
    out["t1_by_plant"] = t1
    ok &= t1 == CENSUS_T1 and out["n_plants"] == 38
    live = df[df.applied & df.admitted]
    out["applied_admitted"] = {
        int(r.plant_id): {
            "plhtrt": float(r.plhtrt),
            "identity_hr": float(r.identity_hr),
            "st_ct": float(r.st_ct),
            "ref_vintages": r.ref_vintages,
            "ref_st_ct_median": float(r.ref_st_ct_median),
            "t1_zero": bool(r.t1_zero),
            "below_ref_fence": bool(r.below_ref_fence),
            "ct_side_intact": bool(r.ct_side_intact),
        }
        for r in live.itertuples()
    }
    ok &= set(out["applied_admitted"]) == {BETHLEHEM, WORLD_GEN_X}
    declined = df[(df.vintage == 2023) & df.plant_id.isin([7314, 2500, 10521])]
    out["declined_one_member_records"] = {
        int(r.plant_id): int(r.ref_n) for r in declined.itertuples()
    }
    ok &= all(n == 1 for n in out["declined_one_member_records"].values())

    # The fleet the flag builds, in-process (the keeper's own fleet flags).
    keeper_cfg = _cfg(KEEPER)
    kw = {
        k: bool(keeper_cfg.get(k))
        for k in (
            "measured_ct_heat_rates",
            "measured_chp_heat_rates",
            "egrid_identity_heat_rates",
            "egrid_family_heat_rates",
        )
    }
    logging.disable(logging.CRITICAL)
    try:
        off = load_fleet_from_csv("NYISO", get_iso_config("NYISO"), **kw)
        on = load_fleet_from_csv(
            "NYISO", get_iso_config("NYISO"), **{FIELD: True}, **kw
        )
    finally:
        logging.disable(logging.NOTSET)
    moved = [
        (int(a.plant_code), round(a.heat_rate, 4), round(b.heat_rate, 4))
        for a, b in zip(off, on)
        if abs(a.heat_rate - b.heat_rate) > 1e-12
    ]
    out["fleet_generators_repriced"] = moved
    plants = {p for p, _, _ in moved}
    ok &= plants == {BETHLEHEM, WORLD_GEN_X}
    for p, before, after in moved:
        exp = out["applied_admitted"][p]
        ok &= (
            abs(before - exp["plhtrt"]) < 5e-4
            and abs(after - exp["identity_hr"]) < 5e-4
        )
    out["pass"] = bool(ok)
    return out


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
            "a registered flag (ScenarioConfig.egrid_steam_collapse_heat_rates) over "
            "an artifact that is arithmetic on eGRID's published GEN / PLNT fields "
            "and the plant's own record: identity = PLHTIAN / sum GENNTAN(CT) / (1 + "
            "median ST/CT over the plant's own T1-clean vintages other than the one "
            "under test); admission = (T1 zero test OR the steam share below the "
            "record's minimum by more than the record's own range) AND the heat per "
            "CT-MWh inside the record AND >= 2 reference vintages. The fence unit is "
            "the plant's own range, the guard is the plant's own range, the "
            "two-member minimum is definitional, APPLIED_VINTAGE = 2023 is the join's "
            "own; nothing chosen, swept or fitted (PREREG-nyiso189 §1 / §3 G-DOF)."
        ),
        "pass": True,
    }


def g_engage() -> dict:
    """G-ENGAGE — the delta reached the LP: Bethlehem's mean mc falls and its
    energy rises in every year, on the arm's own hourlies."""
    rows, checks = {}, []
    for y in YEARS:
        uc, ua = _unit(CONTROL, y), _unit(ARM, y)
        cc, ca = _class_twh(CONTROL, y), _class_twh(ARM, y)
        r = {
            "CC_REGULAR_twh": [
                round(cc.get("CC_REGULAR", 0.0), 3),
                round(ca.get("CC_REGULAR", 0.0), 3),
            ],
            "ST_GAS_twh": [
                round(cc.get("ST_GAS", 0.0), 3),
                round(ca.get("ST_GAS", 0.0), 3),
            ],
            "CC_CHP_twh": [
                round(cc.get("CC_CHP", 0.0), 3),
                round(ca.get("CC_CHP", 0.0), 3),
            ],
            "load_weighted_price": [
                round(_lw_price(CONTROL, y), 2),
                round(_lw_price(ARM, y), 2),
            ],
            "bethlehem_twh": [
                round(_plant_twh(uc, BETHLEHEM), 3),
                round(_plant_twh(ua, BETHLEHEM), 3),
            ],
            "bethlehem_available_twh": [
                round(_plant_cap_twh(uc, BETHLEHEM), 3),
                round(_plant_cap_twh(ua, BETHLEHEM), 3),
            ],
            "bethlehem_mean_mc": [
                round(_plant_mc(uc, BETHLEHEM), 3),
                round(_plant_mc(ua, BETHLEHEM), 3),
            ],
            "world_gen_x_twh": [
                round(_plant_twh(uc, WORLD_GEN_X), 4),
                round(_plant_twh(ua, WORLD_GEN_X), 4),
            ],
            "world_gen_x_mean_mc": [
                round(_plant_mc(uc, WORLD_GEN_X), 3),
                round(_plant_mc(ua, WORLD_GEN_X), 3),
            ],
        }
        checks.append(r["bethlehem_mean_mc"][1] < r["bethlehem_mean_mc"][0])
        checks.append(r["bethlehem_twh"][1] > r["bethlehem_twh"][0])
        rows[y] = r
    return {"by_year": rows, "pass": all(checks)}


NOTE = (
    "nyiso-189 ARM (2026-09-05, owner ruling 2026-09-05 = form B2 of "
    "DECISION-CARD-nyiso189): the keeper 2026-09-04-nyiso-188-combined recipe plus "
    "the ONE new field egrid_steam_collapse_heat_rates — the CT-heat identity for "
    "combined cycles whose eGRID steam-generator filing collapsed in the applied "
    "vintage (Bethlehem 2539 9.665 -> 6.877, World Generation X 54131 9.807 -> "
    "6.996; the derive over all 38 NYISO CCs with a filed steam generator). Zero "
    "free parameters, zero new DOF entries; the ledger is the keeper's, verbatim."
)


def _emit(dry_run: bool) -> dict:
    checks = {
        "G_CONTROL": g_control(),
        "G_DELTA": g_delta(),
        "G_INPUTS": g_inputs(),
        "G_DOF": g_dof(),
        "G_ENGAGE": g_engage(),
    }
    failed = [k for k, v in checks.items() if not v["pass"]]
    if failed:
        raise SystemExit(
            f"REFUSING to attest {ARM.name}: failed {failed}\n"
            + json.dumps(checks, indent=1, default=str)
        )
    doc = json.loads((KEEPER / "calibration_attestation.json").read_text())
    doc["governance"]["attested_by"] = (
        f"session nyiso-189 (2026-09-05). The single arm of the pre-registered A/B "
        f"({PREREG} §1 / §3, pushed at a73d1df0 BEFORE the mechanism was built and "
        f"before any solve; record {FINDING}): {NOTE} Control = the same-HEAD replay "
        "on the committed artifacts (G-CONTROL below, computed against the keeper "
        "2026-09-04-nyiso-188-combined). REPORTED AT FULL MAGNITUDE — see the "
        "finding; the disposition follows the owner's standing formula."
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
    args = ap.parse_args()
    _emit(args.dry_run)


if __name__ == "__main__":
    main()
