"""nyiso-132 A/B gate evaluation — the solar CF-level arm, from committed bundles only.

Scores the gates and ex-ante predictions of
``results/calibration/PREREG-nyiso132-solar-cf-level-2026-08-07.md`` across the
paired control/arm bundles. **No solve, no re-run** — it reads each bundle's
``run_config.json`` and ``hourly/`` sidecars.

This arm is an **UNGATED constants.py change** (owner-chosen construction,
matching the D-25 / caiso-175 precedent), so its config isolation gate is the
INVERSE of the usual one: ``RENEWABLE_AVG_CF`` is a ``constants.py`` value, not
a ``ScenarioConfig`` field, so the two arms' ``scenario_config`` blocks must be
**identical** and the delta lives in the source trees instead. K1 asserts that.

======  ========================================================================
K1      config isolation — ZERO differing ``scenario_config`` fields (the delta
        is a constant, invisible to ``run_config.json``)
K2      feasibility — any new unserved energy (slack) or dump, either arm
K3      liveness — NYISO solar energy must rise by the CF ratio 0.1955/0.15
K4      scope — no OTHER renewable class (wind) may change its annual energy
K5      solar level vs the published registry (ADVISORY, ``VRE_TOL`` = +/-10 %,
        report-only in the rubric — reported here, never a fail)
======  ========================================================================

C3a and C3c are gated criteria and are NOT scored here: run
``scripts/calibration_verdict.py`` on each bundle for those.

Run: ``python scripts/probes/_nyiso132_ab_gates.py``
Writes ``results/calibration/_nyiso132_ab_gates.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

CONTROL = REPO / "results/calibration/nyiso132_cf_control"
ARM = REPO / "results/calibration/nyiso132_cf_arm"
YEARS = (2023, 2024, 2025)

CF_CONTROL = 0.15
CF_ARM = 0.1955
CF_RATIO = CF_ARM / CF_CONTROL
RATIO_TOL = 0.02  # the dispatch may curtail at the margin; 2 % is the liveness band
# Gold Book Table III-2a published Net Energy for the registered market fleet.
PUBLISHED_GWH = {2023: 229.9, 2024: 503.2, 2025: 981.8}
VRE_TOL = 0.10  # mirrors calibration_verdict.VRE_TOL — ADVISORY, report-only


def _cfg(bundle: Path) -> dict:
    doc = json.loads((bundle / "run_config.json").read_text())
    return doc.get("scenario_config", doc)


def _class_energy_gwh(bundle: Path, year: int, klass: str) -> float:
    """Annual P1 energy for one class, GWh."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    sel = df[(df["klass"] == klass) & (df["pass"] == "P1")]
    return float(sel["mw"].sum()) / 1000.0


# The paired-control harness runs the control from a sibling checkout whose
# data/ is a symlink back to the main tree, so every absolute *_path field
# differs by checkout prefix while resolving to the SAME file. Normalize the
# prefix before comparing — the same class of artifact scenarios.py folds out
# of the cache key via _normalize_cache_key_paths.
_TREE_PREFIXES = ("/home/user/market-simulator-control", "/home/user/market-simulator")


def _normalize(value: object) -> object:
    """Strip the checkout prefix from a path-valued config field."""
    if isinstance(value, str):
        for prefix in _TREE_PREFIXES:
            if value.startswith(prefix):
                return value[len(prefix) :]
    return value


def k1_config_isolation() -> dict:
    """ZERO differing scenario_config fields — the delta is a constants.py value.

    Compared after checkout-prefix normalization: a control run from the sibling
    tree reports its own absolute paths, but they resolve through symlinks to the
    same files, so a raw string compare is a false positive.
    """
    c, a = _cfg(CONTROL), _cfg(ARM)
    keys = set(c) | set(a)
    raw = {
        k: [c.get(k, "<absent>"), a.get(k, "<absent>")]
        for k in sorted(keys)
        if c.get(k, "<absent>") != a.get(k, "<absent>")
    }
    diff = {k: v for k, v in raw.items() if _normalize(v[0]) != _normalize(v[1])}
    return {
        "gate": "K1 config isolation (ungated-constant arm: expect ZERO diffs)",
        "passed": not diff,
        "n_fields_compared": len(keys),
        "differing": diff,
        "path_prefix_only_diffs": sorted(set(raw) - set(diff)),
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
    """Solar energy must rise by the CF ratio — proves the constant reached the LP."""
    rows, ok = {}, True
    for year in YEARS:
        c = _class_energy_gwh(CONTROL, year, "solar")
        a = _class_energy_gwh(ARM, year, "solar")
        ratio = a / c if c else float("nan")
        hit = abs(ratio - CF_RATIO) <= RATIO_TOL
        rows[str(year)] = {
            "control_gwh": round(c, 2),
            "arm_gwh": round(a, 2),
            "ratio": round(ratio, 4),
            "expected_ratio": round(CF_RATIO, 4),
            "within_tol": bool(hit),
        }
        ok = ok and hit
    return {"gate": "K3 liveness", "passed": bool(ok), "rows": rows}


def k4_scope() -> dict:
    """Wind must not move — the edit touches the NYISO solar entry only."""
    rows, ok = {}, True
    for year in YEARS:
        c = _class_energy_gwh(CONTROL, year, "wind")
        a = _class_energy_gwh(ARM, year, "wind")
        delta = a - c
        # Wind is a decision variable, so dispatch may re-order at the margin;
        # a LEVEL change would mean the edit leaked past the solar entry.
        hit = abs(delta) <= 0.01 * max(c, 1.0)
        rows[str(year)] = {
            "control_gwh": round(c, 2),
            "arm_gwh": round(a, 2),
            "delta_gwh": round(delta, 3),
            "within_1pct": bool(hit),
        }
        ok = ok and hit
    return {"gate": "K4 scope (wind unchanged)", "passed": bool(ok), "rows": rows}


def k5_published_level() -> dict:
    """Solar level vs the published registry. ADVISORY — reported, never a fail."""
    rows = {}
    for year in YEARS:
        pub = PUBLISHED_GWH[year]
        entry = {"published_gwh": pub}
        for name, bundle in (("control", CONTROL), ("arm", ARM)):
            gwh = _class_energy_gwh(bundle, year, "solar")
            err = (gwh - pub) / pub
            entry[name] = {
                "gwh": round(gwh, 2),
                "pct_vs_published": round(100 * err, 1),
                "within_advisory_band": bool(abs(err) <= VRE_TOL),
            }
        rows[str(year)] = entry
    return {
        "gate": "K5 solar level vs published (ADVISORY, report-only)",
        "passed": None,
        "note": (
            "calibration_verdict.VRE_TOL is a +/-10 % ADVISORY band for wind/solar, "
            "explicitly report-only, so neither arm can fail C1 on this. Reported "
            "because the arm trades an exact mature year for two commissioning "
            "years: the model's monthly capacity ramp has no commissioning curve, "
            "so one CF cannot track a fleet whose own realized CF runs 0.1468-0.1955."
        ),
        "rows": rows,
    }


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-out",
        type=Path,
        default=REPO / "results/calibration/_nyiso132_ab_gates.json",
    )
    args = parser.parse_args()

    gates = [
        k1_config_isolation(),
        k2_feasibility(),
        k3_liveness(),
        k4_scope(),
        k5_published_level(),
    ]
    for g in gates:
        verdict = (
            "ADVISORY" if g["passed"] is None else ("PASS" if g["passed"] else "FAIL")
        )
        print(f"[{verdict:8s}] {g['gate']}")
        for key, val in (g.get("rows") or {}).items():
            print(f"    {key}: {json.dumps(val)}")
        if g.get("differing"):
            print(f"    differing: {json.dumps(g['differing'])}")

    record = {"control": str(CONTROL), "arm": str(ARM), "gates": gates}
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(record, indent=2) + "\n")
    print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
