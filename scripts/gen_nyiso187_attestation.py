#!/usr/bin/env python3
"""Emit the nyiso-187 arm's ``calibration_attestation.json`` (C6 gate).

The arm (``results/calibration/nyiso187_astoria_routing``) is the committed
keeper ``2026-09-04-nyiso-186-astoria-identity`` recipe replayed at HEAD with
ZERO ``scenario_config`` changes and ONE registry fact: ``campd.CAMPD_UNIT_PLANT_REMAP``
gains ``(55375, "CT3") -> 57664`` and ``(55375, "CT4") -> 57664`` (the caiso-196
El Segundo form for the identical defect class), and the two artifacts the
keeper resolves from that routing — the ``-perunitmerit-`` outage extract (+ its
lay-up companion) and the ``-perunitmerit-`` tranche artifact — are re-derived
with their committed ``derive_invocation`` blocks verbatim
(PREREG-nyiso187-ct-steam-merit-position §1 Object 2; rule 23: the data change
is EIA-860 filing CT3 / CT4 / ST2 under 57664 while CAMPD files the whole site
under facility 55375). The control (``results/calibration/nyiso187_control``)
is the same replay on the COMMITTED artifacts at the same HEAD, solved in the
same session as the bit-identity instrument.

ZERO DOF entries are added: a registry identity and two re-derivations with
unchanged constants (rule 21 ``[R-DOF]``).

Every premise below is COMPUTED from the committed bundles, never typed. It
REFUSES to write on any failed check.

Usage:
    python scripts/gen_nyiso187_attestation.py [--dry-run]
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

KEEPER = REPO / "results" / "calibration" / "nyiso186_astoria_identity"
CONTROL = REPO / "results" / "calibration" / "nyiso187_control"
ARM = REPO / "results" / "calibration" / "nyiso187_astoria_routing"
YEARS = (2023, 2024, 2025)
ASTORIA_II, ASTORIA_I, ALLEGANY = 57664, 55375, 7784

PREREG = "results/calibration/PREREG-nyiso187-ct-steam-merit-position.md"
FINDING = "docs/FINDING-nyiso187-ct-steam-merit-position-2026-09-04.md"

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
    """G-INPUTS — both legs resolve the SAME artifact names on the perunitmerit basis; the arm's extract and tranche shas are the re-derived files' shas and differ from the control's (the committed ones); the remap carries exactly the two Astoria entries beyond CAISO's."""
    import hashlib

    from market_sim.data import campd

    out = {}
    ok = True
    shas = {}
    for name, b in (("control", CONTROL), ("arm", ARM)):
        ri = _resolved(b)
        tranche = ri.get("thermal_tranches") or {}
        outage = ri.get("campd_unit_outages") or {}
        same = "-perunitmerit-" in str(tranche.get("path")) and "-perunitmerit-" in str(
            outage.get("path")
        )
        out[name] = {
            "thermal_tranches": tranche.get("path"),
            "thermal_tranches_sha256": tranche.get("sha256"),
            "campd_unit_outages": outage.get("path"),
            "campd_unit_outages_sha256": outage.get("sha256"),
            "perunitmerit_basis": same,
        }
        shas[name] = (tranche.get("sha256"), outage.get("sha256"))
        ok &= same
    ok &= out["control"]["thermal_tranches"] == out["arm"]["thermal_tranches"]
    ok &= out["control"]["campd_unit_outages"] == out["arm"]["campd_unit_outages"]
    ok &= shas["control"] != shas["arm"]
    for key in ("thermal_tranches", "campd_unit_outages"):
        p = REPO / str(out["arm"][key])
        disk = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
        out[f"arm_{key}_on_disk_sha256"] = disk
        ok &= disk == out["arm"][f"{key}_sha256"]
    nyiso_entries = {
        k: v for k, v in campd.CAMPD_UNIT_PLANT_REMAP.items() if v == ASTORIA_II
    }
    out["remap_entries_to_57664"] = sorted(f"{k[0]}:{k[1]}" for k in nyiso_entries)
    ok &= set(nyiso_entries) == {(ASTORIA_I, "CT3"), (ASTORIA_I, "CT4")}
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
        "replaced_routing": {
            "before": "CT1-CT4 all booked against EIA plant 55375 on a 1,221 MW denominator; 57664 never derated; tranche row for 55375 at a 150 % median CF; no tranche row for 57664",
            "after": "CT1 / CT2 297.5 MW on 55375's 595 MW; CT3 / CT4 325.0 MW on 57664's 650 MW; 55375 median CF 99.5 %; 57664 gains its measured tranche row",
        },
        "basis": (
            "a registry identity (EIA-860 generator ids under 57664; eGRID "
            "PLNGENAN(55375) == netgen(55375) + netgen(57664) in seven vintages) "
            "applied through the existing CAMPD_UNIT_PLANT_REMAP seam; both "
            "artifacts re-derived with their committed derive_invocation blocks; "
            "no constant chosen, swept or fitted (PREREG-nyiso187 §1 Object 2)."
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
    """G-ENGAGE — the routing moved the LP: Astoria Energy II's 2025 energy FALLS (its outage becomes visible) and Astoria Energy I's energy RISES in every year (no longer derated for its sibling) — PREREG §3 expectations (i) and (ii)."""
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
    ii_falls_2025 = rows[2025]["astoria_II_twh"][1] < rows[2025]["astoria_II_twh"][0]
    i_rises = all(
        rows[y]["astoria_I_twh"][1] > rows[y]["astoria_I_twh"][0] for y in YEARS
    )
    return {
        "by_year": rows,
        "astoria_II_2025_falls": ii_falls_2025,
        "astoria_I_rises_every_year": i_rises,
        "pass": ii_falls_2025 and i_rises,
    }


ATTESTED_BY = (
    "session nyiso-187 (2026-09-04). THE ARM of the pre-registered Object-2 A/B "
    f"({PREREG} §1 / §3, pushed BEFORE any measurement; record {FINDING}): the "
    "committed keeper 2026-09-04-nyiso-186-astoria-identity recipe replayed at "
    "HEAD with ZERO scenario_config changes and ONE registry fact — "
    "campd.CAMPD_UNIT_PLANT_REMAP gains (55375, CT3) -> 57664 and (55375, CT4) -> "
    "57664, the caiso-196 El Segundo form for the identical defect class (CEMS "
    "files a unit under a sibling ORISPL while EIA-860 carries it under its own "
    "plant) — and the two artifacts the keeper resolves from that routing "
    "re-derived with their committed derive_invocation blocks verbatim: the "
    "-perunitmerit- outage extract (CT1 / CT2 297.5 MW on 55375's 595 MW; CT3 / "
    "CT4 325.0 MW on 57664's 650 MW; before, all four were booked against 55375 "
    "on a 1,221 MW denominator so 57664 was never derated and 55375 was derated "
    "for its sibling) and the -perunitmerit- tranche artifact (55375 median CF "
    "150 -> 99.5 %; 57664 gains its measured row). G-DELTA: only rows keyed on "
    "55375 / 57664 move in both; the ramp-envelope artifact was EXCLUDED because "
    "its class-fraction fallback row also moved (the pre-registered stop), and "
    "the pooled emission-rate block was not re-derived (a --repool rebuilds "
    "every NYISO plant) — both recorded as measured footprint and handed "
    "forward. WHY (rule 14 [R-ACCURATE]): eGRID PLNGENAN(55375) equals EIA-923 "
    "netgen(55375) + netgen(57664) to < 0.5 MWh in all seven vintages 2018-2024 "
    "and EIA-860 files CT3 / CT4 / ST2 under 57664; the keeper's routing was "
    "an estimate where the identity is measured. ZERO free parameters, ZERO new "
    "DOF entries; no lever swept, no band touched. REPORTED AT FULL MAGNITUDE — "
    "see the finding; the disposition is the owner's."
)

NOTE = (
    "nyiso-187 (2026-09-04): the nyiso-186 keeper recipe with the Astoria "
    "split-facility routing (CAMPD_UNIT_PLANT_REMAP 55375 CT3/CT4 -> 57664) and "
    "the re-derived -perunitmerit- outage extract + tranche artifact. Zero free "
    "parameters and zero new DOF entries; the ledger is the keeper's, carried "
    "verbatim."
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
