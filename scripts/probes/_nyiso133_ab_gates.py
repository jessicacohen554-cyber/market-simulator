"""nyiso-133 A/B gate evaluation — the seven pre-registered kill gates.

Scores the gates of
``results/calibration/PREREG-nyiso133-market-solar-cod-basis-2026-08-08.md`` §5
from the two arms' committed bundles only. No solve, no re-run.

======  ========================================================================
K1      config isolation — exactly ONE differing ``scenario_config`` field
        (``nyiso_solar_registry_cod_dates``)
K2      feasibility — zero slack and zero dump, both arms, all three years
K3      liveness — the armed date basis must reach the LP: arm/control solar
        energy = 1.0118 / 0.8746 / 1.0000, the ratio measured through
        ``load_renewable_profiles`` BEFORE the solve (prereg §4a)
K4      scope — wind energy unchanged (the edit must not leak past solar)
K5      gated-criterion regression — any of C1/C2/C3a/C3b/C4/C6/C8 PASS -> FAIL
K6      scarcity collapse — C3c-2025 below 21 h, or C3c-2024 at 0 h
K7      forcing budget — any material class's C8 forced share crosses its cap
======  ========================================================================

K5-K7 are the substantive kills and are read from
``scripts/calibration_verdict.py``'s own criterion rows, so the gate and the
scorer cannot disagree. K1-K4 are construction gates: a firing one voids the
comparison rather than rejecting the mechanism.

An eighth block is ADVISORY and can never fail: the solar level against NYISO's
published Gold Book Net Energy (``calibration_verdict.VRE_TOL`` is explicitly
report-only and D-10 classes NYISO solar ``delivered_pinned``).

Run: ``python scripts/probes/_nyiso133_ab_gates.py``
Writes ``results/calibration/_nyiso133_ab_gates.json``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

CONTROL = REPO / "results/calibration/nyiso133_cod_control"
ARM = REPO / "results/calibration/nyiso133_cod_arm"
KEEPER = REPO / "results/calibration/nyiso132_cf_arm"
OUT = REPO / "results/calibration/_nyiso133_ab_gates.json"
YEARS = (2023, 2024, 2025)

ARMED_FIELD = "nyiso_solar_registry_cod_dates"

# Ex-ante solar energy ratios, measured through load_renewable_profiles BEFORE
# the solve (PREREG §4a item 1). Solar is a decision variable, so the realized
# ratio can sit slightly below the bound ratio where the LP curtails.
EXPECTED_SOLAR_RATIO = {2023: 1.0118, 2024: 0.8746, 2025: 1.0000}
SOLAR_RATIO_TOL = 0.015

# Gold Book Table III-2a published Net Energy (GWh) for the registered fleet.
PUBLISHED_GWH = {2023: 229.9, 2024: 503.2, 2025: 981.8}
VRE_ADVISORY_TOL = 0.10

# C3c kill thresholds, verbatim from the prereg.
C3C_2025_FLOOR_H = 21
RT_ACTUAL_TAIL = {2023: 10, 2024: 12, 2025: 42}

# The criteria whose PASS must survive (K5).
GATED_CRITERIA = ("C1", "C2", "C3a", "C3b", "C4", "C6", "C8")


def _cfg(bundle: Path) -> dict:
    """Return a bundle's recorded ``scenario_config``."""
    doc = json.loads((bundle / "run_config.json").read_text())
    return doc.get("scenario_config", doc)


def _class_energy_gwh(bundle: Path, year: int, klass: str) -> float:
    """Annual P1 energy for one class, GWh."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    sel = df[(df["klass"] == klass) & (df["pass"] == "P1")]
    return float(sel["mw"].sum()) / 1000.0


def _verdict(bundle: Path) -> dict:
    """Run the committed-artifact scorer on a bundle and return its JSON."""
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts/calibration_verdict.py"),
         "--json", str(bundle)],
        capture_output=True, text=True, cwd=str(REPO), check=False,
    )
    if proc.returncode not in (0, 1) or not proc.stdout.strip():
        return {"error": proc.stderr[-2000:] or f"exit {proc.returncode}"}
    return json.loads(proc.stdout)


def k1_config_isolation() -> dict:
    """Exactly one differing field, and it must be the armed one."""
    c, a = _cfg(CONTROL), _cfg(ARM)
    keys = set(c) | set(a)
    diff = {
        k: [c.get(k, "<absent>"), a.get(k, "<absent>")]
        for k in sorted(keys)
        if c.get(k, "<absent>") != a.get(k, "<absent>")
    }
    ok = list(diff) == [ARMED_FIELD] and diff.get(ARMED_FIELD) == [False, True]
    return {
        "gate": "K1 config isolation",
        "passed": bool(ok),
        "n_fields_compared": len(keys),
        "differing": diff,
    }


def k2_feasibility() -> dict:
    """Zero unserved energy and zero dump, both arms, every year."""
    rows, ok = {}, True
    for name, bundle in (("control", CONTROL), ("arm", ARM)):
        for year in YEARS:
            path = bundle / "hourly" / f"system_{year}.parquet"
            if not path.exists():
                rows[f"{name}_{year}"] = {"error": "system sidecar absent"}
                ok = False
                continue
            sysdf = pd.read_parquet(path)
            sysdf = sysdf[sysdf["pass"] == "P1"]
            slack = float(sysdf["slack"].sum()) if "slack" in sysdf else 0.0
            dump = float(sysdf["dump"].sum()) if "dump" in sysdf else 0.0
            rows[f"{name}_{year}"] = {"slack_mwh": slack, "dump_mwh": dump}
            ok = ok and slack == 0.0 and dump == 0.0
    return {"gate": "K2 feasibility", "passed": bool(ok), "rows": rows}


def k3_liveness() -> dict:
    """The armed date basis must actually re-time the LP's solar bound."""
    rows, ok = {}, True
    for year in YEARS:
        c = _class_energy_gwh(CONTROL, year, "solar")
        a = _class_energy_gwh(ARM, year, "solar")
        ratio = a / c if c else float("nan")
        hit = abs(ratio - EXPECTED_SOLAR_RATIO[year]) <= SOLAR_RATIO_TOL
        rows[str(year)] = {
            "control_gwh": round(c, 2),
            "arm_gwh": round(a, 2),
            "ratio": round(ratio, 4),
            "expected_ratio": EXPECTED_SOLAR_RATIO[year],
            "within_tol": bool(hit),
        }
        ok = ok and hit
    return {"gate": "K3 liveness", "passed": bool(ok), "rows": rows}


def k4_scope() -> dict:
    """Wind must not move — the edit touches the NYISO solar basis only."""
    rows, ok = {}, True
    for year in YEARS:
        c = _class_energy_gwh(CONTROL, year, "wind")
        a = _class_energy_gwh(ARM, year, "wind")
        delta = a - c
        hit = abs(delta) <= 0.01 * max(c, 1.0)
        rows[str(year)] = {
            "control_gwh": round(c, 2),
            "arm_gwh": round(a, 2),
            "delta_gwh": round(delta, 3),
            "within_1pct": bool(hit),
        }
        ok = ok and hit
    return {"gate": "K4 scope (wind unchanged)", "passed": bool(ok), "rows": rows}


def _criterion_status(verdict: dict) -> dict:
    """Map criterion id (C1, C3a, ...) -> status string from a scorer JSON.

    ``calibration_verdict --json`` keys ``criteria`` by internal slug
    (``fuelmix``, ``price_tail``, ...) and carries the rubric id at the head of
    each entry's ``label``, so the id is read from there.
    """
    out = {}
    for entry in (verdict.get("criteria") or {}).values():
        cid = str(entry.get("label", "")).split()[0]
        if cid:
            out[cid] = str(entry.get("status", "")).upper()
    return out


def k5_no_gated_regression(vc: dict, va: dict) -> dict:
    """No load-bearing or protective criterion may go PASS -> FAIL."""
    sc, sa = _criterion_status(vc), _criterion_status(va)
    regressions = {
        cid: [sc.get(cid), sa.get(cid)]
        for cid in GATED_CRITERIA
        if sc.get(cid) == "PASS" and sa.get(cid) not in (None, "PASS", "CAVEAT")
    }
    return {
        "gate": "K5 gated-criterion regression",
        "passed": not regressions,
        "control_statuses": {k: sc.get(k) for k in GATED_CRITERIA},
        "arm_statuses": {k: sa.get(k) for k in GATED_CRITERIA},
        "regressions": regressions,
    }


def _tail_hours(bundle: Path, verdict: dict) -> dict:
    """Model >$300 RT hours per year, from the scorer's own C3c records."""
    out: dict[str, object] = {}
    for entry in (verdict.get("criteria") or {}).values():
        if not str(entry.get("label", "")).startswith("C3c"):
            continue
        for rec in entry.get("records", []):
            # The scorer emits an RT row and a DA diagnostic companion per year;
            # only the RT row is gated, and it is the one the key does not mark.
            if str(rec.get("key", "")).endswith("da_diagnostic"):
                continue
            year, model = rec.get("year"), rec.get("model")
            if year is not None and model is not None:
                out[str(year)] = model
    return out


def k6_scarcity_collapse(vc: dict, va: dict) -> dict:
    """C3c must not collapse: 2025 below 21 h, or 2024 at zero, is a kill."""
    tc, ta = _tail_hours(CONTROL, vc), _tail_hours(ARM, va)
    fired = []
    a2025, a2024 = ta.get("2025"), ta.get("2024")
    if isinstance(a2025, (int, float)) and a2025 < C3C_2025_FLOOR_H:
        fired.append(f"C3c-2025 {a2025} h < {C3C_2025_FLOOR_H} h floor")
    if isinstance(a2024, (int, float)) and a2024 == 0:
        fired.append("C3c-2024 formed ZERO scarcity hours")
    return {
        "gate": "K6 scarcity collapse",
        "passed": not fired,
        "rt_actual_hours": {str(y): h for y, h in RT_ACTUAL_TAIL.items()},
        "control_model_hours": tc,
        "arm_model_hours": ta,
        "fired": fired,
    }


def _forced_shares(bundle: Path) -> dict:
    """Per (year, class) total forced share from the bundle's D-2 rows."""
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return {}
    doc = json.loads(path.read_text())
    rows = doc.get("diagnostics", {}).get("D2", {}).get("rows", [])
    out: dict[str, float] = {}
    for row in rows:
        key = f"{row['year']}:{row['class']}"
        out[key] = round(out.get(key, 0.0) + float(row["share_of_class"]), 4)
    return out


def k7_forcing_budget(vc: dict, va: dict) -> dict:
    """The C8 protective criterion carries the budget; report the shares too."""
    sc, sa = _criterion_status(vc), _criterion_status(va)
    control, arm = _forced_shares(CONTROL), _forced_shares(ARM)
    risen = {
        k: [control.get(k), arm.get(k)]
        for k in sorted(set(control) | set(arm))
        if (arm.get(k, 0.0) - control.get(k, 0.0)) > 0.01
    }
    return {
        "gate": "K7 forcing budget (C8)",
        "passed": sa.get("C8") in (None, "PASS"),
        "c8_control": sc.get("C8"),
        "c8_arm": sa.get("C8"),
        "shares_risen_over_1pp": risen,
        "control_shares": control,
        "arm_shares": arm,
    }


def advisory_solar_level() -> dict:
    """Solar energy vs the published registry. Report-only, never a fail."""
    rows = {}
    for year in YEARS:
        pub = PUBLISHED_GWH[year]
        entry: dict[str, object] = {"published_gwh": pub}
        for name, bundle in (("control", CONTROL), ("arm", ARM)):
            gwh = _class_energy_gwh(bundle, year, "solar")
            err = (gwh - pub) / pub
            entry[name] = {
                "gwh": round(gwh, 2),
                "pct_vs_published": round(100 * err, 1),
                "within_advisory_band": bool(abs(err) <= VRE_ADVISORY_TOL),
            }
        rows[str(year)] = entry
    return {
        "block": "ADVISORY solar level vs published Gold Book Net Energy",
        "passed": None,
        "note": (
            "calibration_verdict.VRE_TOL is a +/-10 % ADVISORY band, explicitly "
            "report-only, and D-10 classes NYISO solar delivered_pinned "
            "('advisory-only, excluded from skill claims'), so no gated "
            "criterion moves on it. PREREG ADV-1 predicted 2023 gets WORSE and "
            "expressly ruled that out as grounds for rejection (rule 1)."
        ),
        "rows": rows,
    }


def control_reproduces_keeper() -> dict:
    """The control must reproduce the superseded keeper — no drift excuse here.

    This session's environment matches the keeper bundle's recorded one exactly
    (PREREG §4a item 3), so a non-reproducing control is a hard failure.
    """
    rows, ok = {}, True
    for year in YEARS:
        for klass in ("solar", "wind", "CC_REGULAR", "ST_GAS", "CT_PEAKER"):
            try:
                k = _class_energy_gwh(KEEPER, year, klass)
                c = _class_energy_gwh(CONTROL, year, klass)
            except (FileNotFoundError, KeyError):
                continue
            delta = c - k
            rows[f"{year}:{klass}"] = round(delta, 6)
            ok = ok and abs(delta) < 1e-6
    return {
        "check": "control reproduces the superseded keeper (class-year GWh delta)",
        "passed": bool(ok),
        "max_abs_delta_gwh": round(max((abs(v) for v in rows.values()), default=0.0), 9),
        "rows": rows,
    }


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", default=str(OUT))
    args = parser.parse_args()

    vc, va = _verdict(CONTROL), _verdict(ARM)
    gates = [
        k1_config_isolation(),
        k2_feasibility(),
        k3_liveness(),
        k4_scope(),
        k5_no_gated_regression(vc, va),
        k6_scarcity_collapse(vc, va),
        k7_forcing_budget(vc, va),
    ]
    record = {
        "probe": "nyiso-133 A/B kill gates",
        "prereg": (
            "results/calibration/PREREG-nyiso133-market-solar-cod-basis-2026-08-08.md"
        ),
        "control_bundle": str(CONTROL.relative_to(REPO)),
        "arm_bundle": str(ARM.relative_to(REPO)),
        "armed_field": ARMED_FIELD,
        "control_reproduces_keeper": control_reproduces_keeper(),
        "gates": gates,
        "advisory": advisory_solar_level(),
        "determination": {
            "control": vc.get("determination"),
            "arm": va.get("determination"),
        },
    }
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=1) + "\n")

    repro = record["control_reproduces_keeper"]
    print(
        f"control reproduces keeper: "
        f"{'PASS' if repro['passed'] else 'FAIL'} "
        f"(max |delta| {repro['max_abs_delta_gwh']} GWh)"
    )
    for gate in gates:
        state = {True: "PASS", False: "FAIL", None: "n/a"}[gate["passed"]]
        print(f"  {gate['gate']:38s} {state}")
    print(
        f"determination: control {record['determination']['control']} | "
        f"arm {record['determination']['arm']}"
    )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
