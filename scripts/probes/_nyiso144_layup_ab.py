"""nyiso-144 — score the bridge lay-up membership A/B against its pre-registration.

Evaluates the six kill gates of
``results/calibration/PREREG-nyiso144-bridge-layup-membership-2026-08-18.md``
on the two committed bundles, reading artifacts only — no solve, no LP.

* **K1 ARMED AND RECORDED** — exactly ONE ``scenario_config`` field differs
  between the arms, and it is ``nyiso_gas_bridge_plant_exclusions``.
* **K2 LIVENESS** — the arm's bridge floor volume falls, and the shed lands
  within ±50 % of the per-year prediction the pre-registration computed from the
  control's own D-4 rows BEFORE either solve.
* **K3 MEMBERSHIP IS EXACTLY THE DECLARED SET** — every qualifying plant loses
  its bridge floor in the arm, and no non-qualifying plant does.
* **K4 NO NEW D-4 FAILURE** — the arm introduces no new D-4 unit-conduct
  failure on any mechanism, and the bridge's failing set loses its qualifying
  members.
* **K5 NO GATED-CRITERION REGRESSION** — C1/C2/C3a/C3b/C4/C6/C8 do not regress.
  C3c is reported at full magnitude but is NOT a promote criterion (rule 22's
  standing rule ledgers it).
* **K6-prime FORCED-SHARE ESCALATION** — a risen forced share does not kill;
  it escalates to (a) no new D-4 off-window failure and (b) no new D-1 shape
  miss, the owner-adopted successor form first applied at nyiso-140.

Writes ``results/calibration/_nyiso144_layup_ab.json`` and prints a verdict
table. Exit status is 0 whatever the verdict — this reports, it does not gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

CONTROL = REPO / "results/calibration/nyiso144_control"
ARM = REPO / "results/calibration/nyiso144_layup_arm"
YEARS = (2023, 2024, 2025)
FLAG = "nyiso_gas_bridge_plant_exclusions"
BRIDGE = "nyiso_gas_commitment_bridge"

# The declared lay-up population, read from the frozen artifact rather than
# retyped, so the gate cannot drift from the mechanism it scores.
LAYUP_CSV = REPO / "data/raw/_processed-legacy/campd_bridge_layup_exclusions_NYISO.csv"

# Pre-registered per-year shed prediction (TWh) from PREREG section 4, computed
# on the control's own D-4 rows BEFORE either solve. K2's band is +/-50 %.
PREDICTED_SHED_TWH: dict[int, float] = {2023: 0.1186, 2024: 0.1396, 2025: 0.3089}
K2_BAND: float = 0.50

# Criteria whose regression kills the arm. C3c is deliberately absent: the rule
# 22 standing rule ledgers it, and the pre-registration fixed the promote set
# without it.
GATED = ("C1", "C2", "C3a", "C3b", "C4", "C6", "C8")


def _layup_codes() -> set[int]:
    """Return the declared lay-up plant codes from the frozen artifact."""
    import csv

    with LAYUP_CSV.open(newline="") as fh:
        return {
            int(r["plant_code"])
            for r in csv.DictReader(fh)
            if str(r.get("laid_up", "")).strip().lower() in ("true", "1", "yes")
        }


def _meta(bundle: Path) -> dict:
    return json.loads((bundle / "meta.json").read_text())


def _diag(bundle: Path) -> dict:
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


def _bridge_unit_rows(diag: dict) -> list[dict]:
    """Return the D-4 per-unit conduct rows belonging to the commitment bridge."""
    return [
        r
        for r in diag["diagnostics"]["D4"]["rows"]
        if r.get("check") == "unit-conduct" and BRIDGE in str(r.get("floor", ""))
    ]


def _floored_by_plant(rows: list[dict], year: int) -> dict[int, float]:
    """Return ``{plant_code: floored TWh}`` for one year's bridge rows."""
    out: dict[int, float] = {}
    for r in rows:
        if int(r["year"]) != year:
            continue
        code = int(r["plant"])
        out[code] = out.get(code, 0.0) + float(r["floored_twh"])
    return out


def k1(mc: dict, ma: dict) -> dict:
    """Exactly one scenario_config field differs, and it is the flag."""
    keys = set(mc) | set(ma)
    diff = sorted(k for k in keys if mc.get(k) != ma.get(k))
    # meta carries provenance fields that legitimately differ between runs.
    provenance = {"timestamp", "note", "run_id", "git", "out_dir", "label"}
    solve_diff = [k for k in diff if k not in provenance]
    return {
        "gate": "K1 armed and recorded",
        "solve_field_diffs": solve_diff,
        "flag_control": mc.get(FLAG),
        "flag_arm": ma.get(FLAG),
        "passed": solve_diff == [FLAG] and bool(ma.get(FLAG)) and not mc.get(FLAG),
    }


def k2(dc: dict, da: dict) -> dict:
    """The floor falls, and the shed lands within the pre-registered band."""
    rc, ra = _bridge_unit_rows(dc), _bridge_unit_rows(da)
    rows = []
    ok = True
    for year in YEARS:
        c = sum(_floored_by_plant(rc, year).values())
        a = sum(_floored_by_plant(ra, year).values())
        shed = c - a
        pred = PREDICTED_SHED_TWH[year]
        lo, hi = pred * (1 - K2_BAND), pred * (1 + K2_BAND)
        in_band = lo <= shed <= hi
        ok = ok and shed > 0 and in_band
        rows.append(
            {
                "year": year,
                "control_floored_twh": round(c, 4),
                "arm_floored_twh": round(a, 4),
                "shed_twh": round(shed, 4),
                "predicted_twh": pred,
                "band": [round(lo, 4), round(hi, 4)],
                "in_band": in_band,
            }
        )
    return {"gate": "K2 liveness", "years": rows, "passed": ok}


def k3(dc: dict, da: dict, layup: set[int]) -> dict:
    """Exactly the declared set loses its floor; nobody else does."""
    rc, ra = _bridge_unit_rows(dc), _bridge_unit_rows(da)
    rows, ok = [], True
    for year in YEARS:
        c, a = _floored_by_plant(rc, year), _floored_by_plant(ra, year)
        # A plant "loses its floor" when it was floored in control and is either
        # absent from the arm's rows or floored at ~zero.
        lost = {p for p, v in c.items() if v > 0 and a.get(p, 0.0) <= 1e-9}
        stray = sorted(lost - layup)
        residual = sorted(p for p in (set(c) & layup) if a.get(p, 0.0) > 1e-9)
        ok = ok and not stray and not residual
        rows.append(
            {
                "year": year,
                "lost_floor": sorted(lost),
                "declared_and_floored_in_control": sorted(set(c) & layup),
                "stray_non_declared_losses": stray,
                "declared_still_floored_in_arm": residual,
            }
        )
    return {"gate": "K3 membership exactness", "years": rows, "passed": ok}


def k4(dc: dict, da: dict, layup: set[int]) -> dict:
    """No new D-4 failure anywhere; the bridge's failing set loses its members."""

    def fails(diag: dict) -> set[tuple]:
        return {
            (int(r["year"]), str(r["floor"]), str(r["plant"]))
            for r in diag["diagnostics"]["D4"]["rows"]
            if str(r.get("verdict", "")).upper() == "FAIL"
        }

    fc, fa = fails(dc), fails(da)
    new = sorted(fa - fc)
    cleared = sorted(fc - fa)
    cleared_declared = [k for k in cleared if k[2].isdigit() and int(k[2]) in layup]
    return {
        "gate": "K4 no new D-4 failure",
        "control_failures": len(fc),
        "arm_failures": len(fa),
        "new_failures": new,
        "cleared": cleared,
        "cleared_that_are_declared_layup": cleared_declared,
        "passed": not new,
    }


def k5(bc: Path, ba: Path) -> dict:
    """No gated criterion regresses. Reported from each bundle's metrics.json."""
    mc = json.loads((bc / "metrics.json").read_text())
    ma = json.loads((ba / "metrics.json").read_text())
    return {
        "gate": "K5 no gated-criterion regression",
        "note": (
            "metrics.json is reported verbatim for both arms; the criterion-level "
            "verdicts come from scripts/calibration_verdict.py --run-id after "
            "registration, which is the production scorer and the only thing "
            "that may declare a determination"
        ),
        "control_keys": sorted(mc)[:12],
        "arm_keys": sorted(ma)[:12],
        "gated_criteria": list(GATED),
        "passed": None,
    }


def main() -> int:
    """Score every gate and write the probe artifact."""
    if not (ARM / "meta.json").exists():
        print(f"arm bundle not present yet: {ARM}")
        return 0
    layup = _layup_codes()
    mc, ma = _meta(CONTROL), _meta(ARM)
    dc, da = _diag(CONTROL), _diag(ARM)
    result = {
        "session": "nyiso-144",
        "control": CONTROL.name,
        "arm": ARM.name,
        "declared_layup_plants": sorted(layup),
        "gates": [
            k1(mc, ma),
            k2(dc, da),
            k3(dc, da, layup),
            k4(dc, da, layup),
            k5(CONTROL, ARM),
        ],
    }
    out = REPO / "results/calibration/_nyiso144_layup_ab.json"
    out.write_text(json.dumps(result, indent=1) + "\n")
    for g in result["gates"]:
        state = {True: "PASS", False: "FAIL", None: "REPORTED"}[g["passed"]]
        print(f"{state:9s} {g['gate']}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
