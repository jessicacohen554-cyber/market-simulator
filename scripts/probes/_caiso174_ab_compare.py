"""caiso-174 A/B scorer — the FFR-4D epoch re-solve.

Reads COMMITTED sidecars only (``hourly/system_<year>.parquet``,
``hourly/class_hourly_<year>.parquet``, ``metrics.json``,
``calibration_attestation.json``). **No LP, no replay.**

It reports exactly what ``PRECHECK-caiso174-epoch-resolve-2026-08-05.md``
pre-registered, and it is deliberately built around the fact that this is a
**THREE-state** comparison, not the usual two (§4a):

===== ==================== ==================== =====================
year   keeper (PRE-epoch)   Arm A (new const)    Arm B (measured)
===== ==================== ==================== =====================
2023   flat 8,000.0 MW      flat 15,450.0 MW     7,492.4 MW
2024   flat 8,000.0 MW      flat 15,450.0 MW     11,131.3 MW
2025   flat 8,000.0 MW      flat 15,450.0 MW     15,448.4 MW
===== ==================== ==================== =====================

So the scorer prints **both** differences, because they answer different
questions and conflating them is the trap:

* **B − keeper** = *what the epoch did to the designated keeper.* This is the
  re-gate question and the one the promotion turns on.
* **B − A** = *the per-year vintaging leg alone*, net of the constant
  re-vintage and of incidental code drift between head ``789e28b8`` and this
  one. Expected to be concentrated in 2023/2024, since the re-vintaged constant
  IS the 2025 measured fleet rounded.

**GATED:** the determination, and only the determination (PRECHECK §2).
**REPORTED, NEVER GATED:** C3a/C3c movement in either direction (the FFR-4D §5
hypothesis is a hypothesis this run TESTS, never an expected result), the
storage dispatch shift, and KNOWN-OPEN 1.

Usage::

    PYTHONPATH=.:src python scripts/probes/_caiso174_ab_compare.py
    PYTHONPATH=.:src python scripts/probes/_caiso174_ab_compare.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/caiso172_measured_path15_split"
CONTROL = REPO / "results/calibration/caiso174_control_flatfleet"
ARM = REPO / "results/calibration/caiso174_measured_fleet"
YEARS = (2023, 2024, 2025)

#: Measured CAISO NP15-ZP26 annual-mean basis ($/MWh), ASSESSMENT-caiso171 §4 /
#: re-measured at caiso-173 F3.
MEASURED_BASIS = {2023: 5.947, 2024: 8.576, 2025: 5.727}
#: The incumbent (pre-epoch) keeper's modelled basis, caiso-173 F3.
KEEPER_BASIS = {2023: 0.333, 2024: 0.217, 2025: 0.179}

#: Fleet ladder, PRECHECK §4a. For the report header only.
FLEET = {
    "keeper (PRE-epoch)": {2023: 8000.0, 2024: 8000.0, 2025: 8000.0},
    "A control (new const)": {2023: 15450.0, 2024: 15450.0, 2025: 15450.0},
    "B treated (measured)": {2023: 7492.4, 2024: 11131.3, 2025: 15448.4},
}

BUNDLES = {"keeper": KEEPER, "A": CONTROL, "B": ARM}


def _system(bundle: Path, year: int) -> pd.DataFrame | None:
    p = bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    return df[df["pass"] == "P1"] if "pass" in df.columns else df


def _classes(bundle: Path, year: int) -> pd.DataFrame | None:
    p = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    return df[df["pass"] == "P1"] if "pass" in df.columns else df


def load_weighted_price(df: pd.DataFrame) -> float:
    """Load-weighted mean price ($/MWh) — the C3a basis."""
    return float((df["price"] * df["demand"]).sum() / df["demand"].sum())


def basis(df: pd.DataFrame, a: str = "NP15", b: str = "ZP26") -> float:
    """Annual-mean price basis a - b ($/MWh), clock-invariant simple mean."""
    p = df.pivot_table(index="hour", columns="zone", values="price", aggfunc="mean")
    if a not in p.columns or b not in p.columns:
        return float("nan")
    return float((p[a] - p[b]).mean())


def class_twh(df: pd.DataFrame, needle: str) -> float:
    """Annual TWh for classes whose name contains ``needle`` (case-insensitive)."""
    m = df[df["klass"].str.contains(needle, case=False, na=False)]
    return float(m["mw"].sum() / 1e6)


def determination(bundle: Path) -> dict:
    """The scored determination and its caveat/FAIL counts, off metrics.json."""
    p = bundle / "metrics.json"
    if not p.exists():
        return {"determination": "(absent)", "n_fail": None, "caveats": None}
    m = json.loads(p.read_text())
    crit = m.get("criteria", [])
    fails = [
        c
        for c in crit
        if isinstance(c, dict)
        and str(c.get("status", c.get("verdict", ""))).upper().startswith("FAIL")
    ]
    return {
        "determination": m.get("determination"),
        "n_fail": len(fails),
        "fails": [f"{c.get('id', c.get('criterion'))} {c.get('year', '')}".strip() for c in fails],
        "caveats": m.get("caveats"),
    }


def dof(bundle: Path) -> dict:
    """The DOF ledger counts — PRECHECK §9's pre-registered invariant."""
    p = bundle / "calibration_attestation.json"
    if not p.exists():
        return {}
    fp = json.loads(p.read_text()).get("free_parameters", {})
    return {"n_entries": fp.get("n_entries"), "n_residual": fp.get("n_residual")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    record: dict = {"probe": "caiso174_ab_compare", "fleet_ladder": FLEET}

    missing = [k for k, b in BUNDLES.items() if not (b / "metrics.json").exists()]
    if missing:
        print(f"NOTE: bundle(s) not yet solved: {missing} — partial report.\n")

    print("=" * 88)
    print("caiso-174 A/B — THE FFR-4D EPOCH RE-SOLVE  (three-state, PRECHECK §4a)")
    print("=" * 88)
    print(f"{'arm':26}{'2023 MW':>12}{'2024 MW':>12}{'2025 MW':>12}   battery fleet")
    for name, row in FLEET.items():
        print(f"{name:26}{row[2023]:>12,.1f}{row[2024]:>12,.1f}{row[2025]:>12,.1f}")

    # ---- the GATE: determination ----
    print()
    print("=" * 88)
    print("DETERMINATION — THE ONLY THING THAT GATES THE PROMOTION (PRECHECK §2)")
    print("=" * 88)
    for k, b in BUNDLES.items():
        d = determination(b)
        record.setdefault("determination", {})[k] = d
        record.setdefault("dof", {})[k] = dof(b)
        fails = f"  fails={d['fails']}" if d.get("fails") else ""
        print(f"  {k:8} {str(d['determination']):28} n_FAIL={d['n_fail']}{fails}")
        print(f"           DOF {record['dof'][k]}")

    # ---- REPORTED: price level (C3a) ----
    print()
    print("=" * 88)
    print("C3a load-weighted mean price — REPORTED, NEVER GATED")
    print("  (FFR-4D §5's hypothesis is a HYPOTHESIS THIS RUN TESTS, not an expectation)")
    print("=" * 88)
    print(f"{'year':6}{'keeper':>12}{'A control':>12}{'B treated':>12}{'B-keeper':>12}{'B-A':>10}")
    for year in YEARS:
        vals = {}
        for k, b in BUNDLES.items():
            df = _system(b, year)
            vals[k] = load_weighted_price(df) if df is not None else float("nan")
        dk = vals["B"] - vals["keeper"]
        da = vals["B"] - vals["A"]
        record.setdefault("c3a_price", {})[year] = {
            **{k: round(v, 4) for k, v in vals.items()},
            "B_minus_keeper": round(dk, 4),
            "B_minus_A": round(da, 4),
        }
        print(
            f"{year:<6}{vals['keeper']:>12.2f}{vals['A']:>12.2f}{vals['B']:>12.2f}"
            f"{dk:>+12.2f}{da:>+10.2f}"
        )

    # ---- REPORTED: what the fleet change DISPLACES ----
    #
    # MEASURED LIMITATION, stated rather than worked around: storage is NOT a
    # class in the committed `class_hourly_<year>.parquet` sidecars (their klass
    # domain is CC_CHP / CC_REGULAR / COAL / CT_CHP / CT_PEAKER / OTHER / ST_GAS
    # / biomass / hydro / import / nuclear / oil / solar / wind). So battery
    # charge/discharge is NOT directly observable from committed artifacts and
    # this scorer does not pretend otherwise. The fleet effect is observed
    # THROUGH WHAT IT DISPLACES — the gas classes a battery competes with in the
    # evening peak, which is precisely the channel FFR-4D §5's hypothesis runs
    # through ("7.4 GW of missing evening-peak battery leaves that load to
    # thermal"). A unit-level storage read would need a keeper replay, which
    # rule 15 reserves for unit-level questions.
    print()
    print("=" * 88)
    print("WHAT THE FLEET CHANGE DISPLACES (TWh) — storage is NOT in the class sidecars,")
    print("  so the effect is read through the gas classes it competes with (see source note)")
    print("=" * 88)
    print(f"{'year':6}{'class':>14}{'keeper':>11}{'A control':>12}{'B treated':>12}{'B-keeper':>11}{'B-A':>9}")
    for year in YEARS:
        for needle in ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "import"):
            row = {}
            for k, b in BUNDLES.items():
                df = _classes(b, year)
                row[k] = class_twh(df, needle) if df is not None else float("nan")
            record.setdefault("displaced_twh", {}).setdefault(str(year), {})[needle] = {
                **{k: round(v, 4) for k, v in row.items()},
                "B_minus_keeper": round(row["B"] - row["keeper"], 4),
                "B_minus_A": round(row["B"] - row["A"], 4),
            }
            print(
                f"{year:<6}{needle:>14}{row['keeper']:>11.3f}{row['A']:>12.3f}"
                f"{row['B']:>12.3f}{row['B'] - row['keeper']:>+11.3f}{row['B'] - row['A']:>+9.3f}"
            )

    # ---- REPORTED: KNOWN-OPEN 1 ----
    print()
    print("=" * 88)
    print("KNOWN-OPEN 1 — NP15-ZP26 basis, REPORTED, NEVER GATED")
    print("=" * 88)
    print(f"{'year':6}{'measured':>11}{'keeper':>10}{'A':>10}{'B':>10}{'B % of meas':>13}")
    for year in YEARS:
        vals = {}
        for k, b in BUNDLES.items():
            df = _system(b, year)
            vals[k] = basis(df) if df is not None else float("nan")
        meas = MEASURED_BASIS[year]
        record.setdefault("ns_basis", {})[year] = {
            "measured": meas,
            **{k: round(v, 4) for k, v in vals.items()},
            "B_pct_of_measured": round(100.0 * vals["B"] / meas, 2) if meas else None,
        }
        print(
            f"{year:<6}{meas:>+11.3f}{vals['keeper']:>+10.3f}{vals['A']:>+10.3f}"
            f"{vals['B']:>+10.3f}{100.0 * vals['B'] / meas:>12.1f}%"
        )

    if args.json:
        args.json.write_text(json.dumps(record, indent=1, default=str))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
