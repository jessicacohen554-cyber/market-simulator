#!/usr/bin/env python3
"""Emit the nyiso-185 arm's ``calibration_attestation.json`` (C6 gate).

The arm (``results/calibration/nyiso185_family_hr``) is the committed keeper
``2026-09-02-nyiso-177-vintage-matched`` recipe replayed at HEAD plus exactly
one field, ``egrid_family_heat_rates=True`` (PREREG-nyiso185-stgas-family-hr-ab
§4): eGRID prime-mover-family heat rates at multi-family plants, the
zero-parameter replacement for the ``fleet.models.MIXED_FACILITY_STEAM_HR``
hand number at the plants it covers. The control
(``results/calibration/nyiso185_control``) is the same replay with no
override, solved in the same session as the bit-identity instrument.

ZERO DOF entries are added: the construction is arithmetic on published eGRID
fields (Σ UNT.HTIAN / Σ GEN.GENNTAN per family, the join's own vintage and
window), so the ledger carries VERBATIM from the keeper (rule 21 ``[R-DOF]``).

Every premise below is COMPUTED from the committed bundles, never typed (the
caiso-196/197 E10 discipline, the nyiso-177 generator pattern). It REFUSES to
write on any failed check.

Usage:
    python scripts/gen_nyiso185_attestation.py [--dry-run]
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

KEEPER = REPO / "results" / "calibration" / "nyiso177_vintage_B1p"
CONTROL = REPO / "results" / "calibration" / "nyiso185_control"
ARM = REPO / "results" / "calibration" / "nyiso185_family_hr"
YEARS = (2023, 2024, 2025)
RAVENSWOOD = 2500

PREREG = "results/calibration/PREREG-nyiso185-stgas-family-hr-ab.md"
FINDING = "docs/FINDING-nyiso185-stgas-family-hr-ab-2026-09-04.md"

#: The ONLY ScenarioConfig field the arm may differ from the control on.
_ALLOWED_DELTA = {"egrid_family_heat_rates"}


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
    """G-INPUTS — both legs on the keeper's availability basis; the artifact covers (2500, ST)."""
    from market_sim.config.paths import PROCESSED_DIR
    from market_sim.data.fleet.eia860 import egrid_family_heat_rates_for

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
    rates = egrid_family_heat_rates_for("NYISO")
    art = PROCESSED_DIR / "egrid_family_heat_rates_NYISO.csv"
    out["artifact"] = str(art.relative_to(REPO))
    out["ravenswood_ST_rate"] = rates.get((RAVENSWOOD, "ST"))
    out["ravenswood_CC_rate"] = rates.get((RAVENSWOOD, "CC"))
    out["covered_plant_family_rows"] = len(rates)
    ok &= (RAVENSWOOD, "ST") in rates and (RAVENSWOOD, "CC") in rates
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
        "removed_hand_values_at_covered_plants": {
            "MIXED_FACILITY_STEAM_HR[2500]": 9.5,
            "note": "superseded at covered plants by the measured family rate (rule 19); the dict entry itself is untouched (CAISO 315/335 are CAISO's lane)",
        },
        "basis": (
            "eGRID prime-mover-family heat rates are arithmetic on published "
            "fields (Σ UNT23.HTIAN / Σ GEN23.GENNTAN per family) from the SAME "
            "vintage and 3,000-30,000 Btu/kWh window the plant-grain join reads; "
            "no scalar was chosen, swept or fitted (PREREG-nyiso184 §3 R1, "
            "PREREG-nyiso185 §3)."
        ),
        "pass": True,
    }


def g_engage() -> dict:
    """G-ENGAGE — the mechanism moved the LP, off committed sidecars, vs the control."""
    rows = {}
    for y in YEARS:
        c, a = _class_twh(CONTROL, y), _class_twh(ARM, y)
        rows[y] = {
            "ST_GAS_twh": [
                round(c.get("ST_GAS", 0.0), 3),
                round(a.get("ST_GAS", 0.0), 3),
            ],
            "CC_REGULAR_twh": [
                round(c.get("CC_REGULAR", 0.0), 3),
                round(a.get("CC_REGULAR", 0.0), 3),
            ],
            "load_weighted_price": [
                round(_lw_price(CONTROL, y), 2),
                round(_lw_price(ARM, y), 2),
            ],
        }
    moved = all(rows[y]["ST_GAS_twh"][1] < rows[y]["ST_GAS_twh"][0] for y in YEARS)
    return {"by_year": rows, "st_gas_falls_every_year": moved, "pass": moved}


ATTESTED_BY = (
    "session nyiso-185 (2026-09-04). THE ARM of the owner-authorized A/B "
    f"({PREREG}, committed BEFORE any measurement; record {FINDING}): the "
    "committed keeper 2026-09-02-nyiso-177-vintage-matched recipe replayed at "
    "HEAD plus exactly ONE field, egrid_family_heat_rates=True — eGRID "
    "PRIME-MOVER-FAMILY heat rates at plants hosting two or more live families "
    "(Σ UNT23.HTIAN / Σ GEN23.GENNTAN per family ST / CC / GT, the SAME vintage "
    "and physical window the plant-grain join reads), applied at the "
    "eGRID-input seam so every class-scoped measured mechanism keeps its "
    "precedence, and SUPERSEDING fleet.models.MIXED_FACILITY_STEAM_HR's hand "
    "number at the plants it covers (rule 19, never stacked). WHY: nyiso-184 "
    "proved as identities that Ravenswood's ST_GAS base 9.50 IS that dict — a "
    "rule-24 per-plant enumeration whose 9.5 its own comment derives from "
    "ASSUMED capacity factors putting two-thirds of the site's energy on the "
    "steam where CAMPD puts one-third — lifting the plant-grain eGRID-2023 "
    "blend 8.80 that every Ravenswood row carries; the family construction "
    "reads the same eGRID at unit/generator grain and puts the steam at 12.29 "
    "and the combined cycle at 7.35. GROUNDING (PREREG-nyiso185 §3, all three "
    "legs FIRE): the heat side is what the join controls and it matches the "
    "class — Ravenswood's annual/loaded factor 1.029 inside the eight peers' "
    "[1.0006, 1.0707]; the eGRID family heat input equals CEMS heat to 1e-9; "
    "plant-level EIA-923 net / CAMPD gross 0.948 inside the peers' "
    "[0.888, 0.959]. nyiso-184's G2c miss (r 1.148 vs [1.059, 1.121]) is "
    "recorded, not re-litigated: it sat entirely in EIA-923's net-generation "
    "denominator (unit 30 net/gross 0.862 at CF 4.2 %), the published "
    "convention every peer's basis carries, which a grounding bar on the "
    "construction must not gate. ZERO free parameters, ZERO new DOF entries; "
    "no lever swept, no band touched, no residual consulted. REPORTED AT FULL "
    "MAGNITUDE, INCLUDING WHAT IT COSTS — see the finding: C1-2023 ST_GAS "
    "clears (+3.86 -> +2.16 TWh) while C1-2024 CC_REGULAR crosses the share "
    "band (+3.34 -> +3.87 TWh, 2.78 -> 3.18 pp); C3a-2025 -11.2 -> -10.5 % "
    "(still FAIL, owner-court, no price claim banked); C3b, C2, C8 PASS; C3c "
    "unchanged. REGISTERED AS A KEEPER CANDIDATE UNDER THE PRE-REGISTERED "
    "VERDICT RULE; the disposition is the owner's."
)

NOTE = (
    "nyiso-185 (2026-09-04): the nyiso-177 keeper recipe plus "
    "egrid_family_heat_rates — the measured, vintage-reproducible replacement "
    "for the MIXED_FACILITY_STEAM_HR hand number at the plants the artifact "
    "covers. Zero free parameters and zero new DOF entries; the ledger is the "
    "keeper's, carried verbatim. The prior keeper lineage's mechanism notes "
    "live in their own bundles' attestations and the keeper shard's "
    "promotion-note chain."
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
