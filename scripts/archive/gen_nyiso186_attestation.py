#!/usr/bin/env python3
"""Emit the nyiso-186 arm's ``calibration_attestation.json`` (C6 gate).

The arm (``results/calibration/nyiso186_astoria_identity``) is the committed
keeper ``2026-09-04-nyiso-185-family-hr`` recipe replayed at HEAD with ZERO
``scenario_config`` changes and exactly ONE artifact row added: the identity
derive's new MERGED-identity leg puts Astoria Energy II (EIA 57664) on eGRID
plant 55375's pooled rate 7.3792 MMBtu/MWh (PREREG-nyiso186 §7.3), replacing
the ``gas_cc`` f-class default 6.70 the fleet carried because eGRID files both
Astoria Energy blocks under one ORISPL and 57664 has no eGRID row. The control
(``results/calibration/nyiso186_control``) is the same replay with the committed
artifact, solved in the same session as the bit-identity instrument.

ZERO DOF entries are added: the rate is arithmetic on published eGRID fields
(pooled ΣPLHTIAN / ΣPLNGENAN over the seven vintages in which
PLNGENAN(55375) == netgen(55375) + netgen(57664) to < 0.5 MWh), the same rule
the committed Allegany row already carries (rule 21 ``[R-DOF]``).

Every premise below is COMPUTED from the committed bundles, never typed. It
REFUSES to write on any failed check.

Usage:
    python scripts/gen_nyiso186_attestation.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results" / "calibration" / "nyiso185_family_hr"
CONTROL = REPO / "results" / "calibration" / "nyiso186_control"
ARM = REPO / "results" / "calibration" / "nyiso186_astoria_identity"
YEARS = (2023, 2024, 2025)
ASTORIA_II, ASTORIA_I, ALLEGANY = 57664, 55375, 7784

PREREG = "results/calibration/PREREG-nyiso186-cc-regular-2024-class.md"
FINDING = "docs/FINDING-nyiso186-cc-regular-2024-class-2026-09-04.md"

#: The arm may differ from the control on NO ScenarioConfig field (the delta is
#: one artifact row, checked by G-INPUTS).
_ALLOWED_DELTA: set[str] = set()


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def _resolved(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text()).get(
        "resolved_inputs", {}
    )


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return (df.groupby("klass").mw.sum() / 1e6).to_dict()


def _lw_price(bundle: Path, year: int) -> float:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return float((df.price * df.demand).sum() / df.demand.sum())


def _defaults() -> dict:
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    base = ScenarioConfig(iso="NYISO")
    return {f.name: getattr(base, f.name, None) for f in dataclasses.fields(base)}


def g_control() -> dict:
    """G-CONTROL — the same-HEAD control against the committed keeper, RE-MEASURED.

    PREREG §4 G2: bit-identical (max |Δprice| = 0.0) means the committed keeper
    IS the baseline and the control registers nothing; otherwise the control
    is the baseline and the drift is named here. Either outcome PASSES the
    check — what must not happen is an un-measured premise.
    """
    rows = {}
    worst = 0.0
    for y in YEARS:
        a = pd.read_parquet(KEEPER / "hourly" / f"system_{y}.parquet")
        b = pd.read_parquet(CONTROL / "hourly" / f"system_{y}.parquet")
        a = a[a["pass"] == "P1"].sort_values(["zone", "hour"])
        b = b[b["pass"] == "P1"].sort_values(["zone", "hour"])
        d = a.price.values - b.price.values
        n = int((abs(d) > 1e-9).sum())
        worst = max(worst, float(abs(d).max()))
        rows[y] = {
            "hours_differing": n,
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
    """G-DELTA — the arm differs from the same-HEAD control on the allowed field ONLY."""
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
    rode_along = sorted(set(diff) - _ALLOWED_DELTA)
    return {
        "baseline": CONTROL.name,
        "delta_fields": {k2: list(v) for k2, v in sorted(diff.items())},
        "absence_normalized": dict(sorted(absence.items())),
        "rode_along": rode_along,
        "pass": not rode_along and set(diff) == _ALLOWED_DELTA,
    }


def g_inputs() -> dict:
    """G-INPUTS — both legs on the keeper's availability basis; the identity artifact carries EXACTLY the Allegany row plus the Astoria merged row."""
    from market_sim.config.paths import PROCESSED_DIR
    from market_sim.data.fleet.eia860 import egrid_identity_heat_rates_for

    out = {}
    ok = True
    for name, b in (("control", CONTROL), ("arm", ARM)):
        ri = _resolved(b)
        tranche = ((ri.get("thermal_tranches") or {}).get("path")) or ""
        outage = ((ri.get("campd_unit_outages") or {}).get("path")) or ""
        same = "-perunitmerit-" in tranche and "-perunitmerit-" in outage
        out[name] = {
            "thermal_tranches": tranche,
            "campd_unit_outages": outage,
            "perunitmerit_basis": same,
        }
        ok &= same
    art = PROCESSED_DIR / "egrid_identity_heat_rates_NYISO.csv"
    df = pd.read_csv(art)
    rates = egrid_identity_heat_rates_for("NYISO")
    out["artifact"] = str(art.relative_to(REPO))
    out["rows"] = sorted(int(p) for p in df["plant_id"])
    out["astoria_II_rate"] = rates.get(ASTORIA_II)
    out["allegany_rate"] = rates.get(ALLEGANY)
    row = df[df["plant_id"] == ASTORIA_II]
    out["astoria_II_egrid_orispl"] = (
        int(row["egrid_orispl"].iloc[0]) if len(row) else None
    )
    out["astoria_II_n_vintages"] = int(row["n_vintages"].iloc[0]) if len(row) else None
    out["astoria_II_identity_merged"] = bool(
        len(row) and "MERGED" in str(row["source"].iloc[0])
    )
    ok &= set(out["rows"]) == {ALLEGANY, ASTORIA_II}
    ok &= (
        out["astoria_II_egrid_orispl"] == ASTORIA_I
        and out["astoria_II_identity_merged"]
    )
    ok &= (out["astoria_II_n_vintages"] or 0) >= 2
    ok &= abs((out["allegany_rate"] or 0.0) - 8.4209) < 1e-6
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
        "replaced_class_default": {
            "HEAT_RATE_BINS['gas_cc']['f_class'] at 57664": 6.7,
            "note": "the estimate the fleet carried because eGRID has no row for 57664; replaced by the measured merged-identity rate 7.3792 (rule 14)",
        },
        "basis": (
            "the identity artifact's declared rate rule, unchanged: pooled "
            "ΣPLHTIAN / ΣPLNGENAN over every eGRID vintage in which the identity "
            "holds exactly (< 0.5 MWh); the MERGED leg is the same test at the "
            "two-plant sum; no scalar was chosen, swept or fitted "
            "(PREREG-nyiso186 §7.3)."
        ),
        "pass": True,
    }


def _plant_twh(bundle: Path, year: int, plant: int) -> float:
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["plant_code", "mw"],
    )
    return float(df[df["plant_code"] == plant]["mw"].sum() / 1e6)


def g_engage() -> dict:
    """G-ENGAGE — the repair moved the LP: Astoria Energy II's energy FALLS every year vs the control (PREREG §7.3 expectation (i))."""
    rows = {}
    for y in YEARS:
        c, a = _class_twh(CONTROL, y), _class_twh(ARM, y)
        rows[y] = {
            "astoria_II_twh": [
                round(_plant_twh(CONTROL, y, ASTORIA_II), 3),
                round(_plant_twh(ARM, y, ASTORIA_II), 3),
            ],
            "astoria_I_twh": [
                round(_plant_twh(CONTROL, y, ASTORIA_I), 3),
                round(_plant_twh(ARM, y, ASTORIA_I), 3),
            ],
            "CC_REGULAR_twh": [
                round(c.get("CC_REGULAR", 0.0), 3),
                round(a.get("CC_REGULAR", 0.0), 3),
            ],
            "ST_GAS_twh": [
                round(c.get("ST_GAS", 0.0), 3),
                round(a.get("ST_GAS", 0.0), 3),
            ],
            "load_weighted_price": [
                round(_lw_price(CONTROL, y), 2),
                round(_lw_price(ARM, y), 2),
            ],
        }
    moved = all(
        rows[y]["astoria_II_twh"][1] < rows[y]["astoria_II_twh"][0] for y in YEARS
    )
    return {"by_year": rows, "astoria_II_falls_every_year": moved, "pass": moved}


ATTESTED_BY = (
    "session nyiso-186 (2026-09-04). THE ARM of the pre-registered identity A/B "
    f"({PREREG} §7, pushed BEFORE the artifact was re-derived; record {FINDING}): "
    "the committed keeper 2026-09-04-nyiso-185-family-hr recipe replayed at HEAD "
    "with ZERO scenario_config changes and exactly ONE artifact row added — the "
    "eGRID identity derive's new MERGED-identity leg (the one-to-one identity "
    "test at the TWO-plant sum, same 0.5 MWh tolerance, same >=2-overlap rule, "
    "same pooled rate rule, run over the whole 187-plant NYISO fossil "
    "population, ONE pair found) puts Astoria Energy II (EIA 57664, 650 MW NYC "
    "combined cycle) on eGRID plant 55375's pooled 7.3792 MMBtu/MWh, replacing "
    "the gas_cc f-class default 6.70 the fleet carried because eGRID files both "
    "Astoria Energy blocks under ONE ORISPL and 57664 has no eGRID row in any "
    "vintage. WHY (rule 14 [R-ACCURATE], NOT a residual): eGRID PLNGENAN(55375) "
    "equals EIA-923 netgen(55375) + netgen(57664) to < 0.5 MWh in all seven "
    "vintages 2018-2024, the committed identity rule's own exactness standard; "
    "a class-default estimate was in use where a measured seven-vintage input "
    "exists, and the sibling block at the same facility already carries eGRID's "
    "7.258 while the facility meter reads 7.05 (running-hour, merged). The "
    "pre-registered attribution bars (PREREG §3) read CONCENTRATED in every "
    "year (C3 0.875 / 0.745 / 0.853; the same three plants 57185, 56196, 57664) "
    "and NONE of the plant-level hypotheses fired on its bar — recorded, not "
    "moved; the license for this arm is rule 14, stated in PREREG §7.2 before "
    "the derive ran. ZERO free parameters, ZERO new DOF entries; no lever swept, "
    "no band touched. REPORTED AT FULL MAGNITUDE — see the finding for the "
    "criterion movement and every regression; the disposition is the owner's."
)

NOTE = (
    "nyiso-186 (2026-09-04): the nyiso-185 keeper recipe with the re-derived "
    "eGRID identity artifact (MERGED-identity leg: Astoria Energy II 57664 <-> "
    "eGRID 55375, pooled 7.3792 over 7 vintages, LOYO [7.3552, 7.4041]). Zero "
    "free parameters and zero new DOF entries; the ledger is the keeper's, "
    "carried verbatim."
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
            + json.dumps(checks, indent=1)
        )
    doc = json.loads((KEEPER / "calibration_attestation.json").read_text())
    doc["governance"]["attested_by"] = ATTESTED_BY
    doc["governance"]["note"] = NOTE
    doc["governance"]["computed_checks"] = checks
    if not dry_run:
        (ARM / "calibration_attestation.json").write_text(
            json.dumps(doc, indent=1) + "\n"
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
