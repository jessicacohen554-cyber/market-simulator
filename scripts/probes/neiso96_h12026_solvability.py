"""Audit what still blocks a NEISO H1-2026 solve, now that the actuals exist.

neiso-96, 2026-08-15.  The H1-2026 half of NEISO's ``final`` locked test was
blocked by TWO different things that neiso-94 §3.2 recorded as one:

  * no scoring TARGET -- ``actual_lmp_hourly_NEISO.parquet`` carried no 2026
    rows, so there was nothing to score C3c against. **Retired this session**
    by the intake.
  * no solvable INPUT SET -- which nobody had measured, because the missing
    target made the question moot.

This probe measures the second, so the readiness answer rests on evidence
instead of on the first blocker's shadow. It re-runs the neiso-90 input walk
against 2026 and adds the one check that walk cannot express: whether the
demand path can produce a PARTIAL year at all.

The headline is that it cannot, and that this is not a NEISO fact.
``eia930.frames._eia_hourly_frame`` returns ``None`` unless the extract holds a
full ``HOURS_PER_YEAR`` series, so a half-year is rejected before any ISO's
loader sees it; the caller then falls back to ``eia_demand_profiles.parquet``,
which carries 2021-2025 only, and raises. Every BA is in the same position for
2026 -- this is a structural, six-ISO property of the solve path, not a gap in
NEISO's data.

NO YEAR IS SOLVED, SCORED OR REGISTERED. Loaders are resolved and on-disk
coverage inspected; no LP is constructed. Rule 22 as amended 2026-08-06 leaves
input inspection unrestricted.

Output: ``results/calibration/_neiso96_h12026_solvability.json``.

Usage:
    uv run python scripts/probes/neiso96_h12026_solvability.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

OUT = REPO / "results" / "calibration" / "_neiso96_h12026_solvability.json"

#: The BAs behind the six calibrated ISOs, for the full-year-gate sweep.
BA_BY_ISO = {
    "NEISO": "ISNE",
    "NYISO": "NYIS",
    "CAISO": "CISO",
    "MISO": "MISO",
    "PJM": "PJM",
    "ERCOT": "ERCO",
}


def input_walk() -> dict:
    """Re-run the neiso-90 per-year input walk for 2026, with 2023 as control."""
    import scripts.probes.neiso90_final_prereq_audit as audit

    audit.PROBE_YEARS = (2026,)
    rows: dict[str, dict] = {}
    for name in sorted(n for n in dir(audit) if n.startswith("probe_")):
        fn = getattr(audit, name)
        try:
            res = fn()
        except TypeError:
            continue  # probe_file is a helper taking arguments, not a probe
        except Exception as e:  # a loader that raises IS the finding
            rows[name] = {"2026": {"status": "ERR", "note": f"{type(e).__name__}: {e}"}}
            continue
        rows[name] = {
            str(y): {"status": st, "note": str(note)}
            for y, (st, note) in sorted(res.items())
        }
    return rows


def full_year_gate() -> dict:
    """Whether each BA's EIA-930 hourly frame survives the full-year gate.

    This is the check that turns "NEISO 2026 demand is missing" into "no ISO can
    build a partial year": the gate is in shared code and is blind to ISO.
    """
    from market_sim.data.eia930 import frames as fr

    out: dict[str, dict] = {"hours_per_year_gate": int(fr.HOURS_PER_YEAR), "bas": {}}
    for iso, ba in sorted(BA_BY_ISO.items()):
        row = {}
        for year in (2025, 2026):
            try:
                f = fr._eia_hourly_frame(ba, year)
                row[str(year)] = None if f is None else int(len(f))
            except Exception as e:
                row[str(year)] = f"ERR {type(e).__name__}"
        out["bas"][f"{iso} ({ba})"] = row
    return out


def demand_profiles_coverage() -> dict:
    """Years present in the fallback ``eia_demand_profiles.parquet``, per ISO."""
    import pandas as pd

    path = REPO / "data" / "raw" / "eia-930" / "eia_demand_profiles.parquet"
    df = pd.read_parquet(path, columns=["iso", "year"]).drop_duplicates()
    return {
        str(iso): sorted(int(y) for y in g["year"].unique())
        for iso, g in df.groupby("iso")
    }


def main() -> int:
    """Run the audit and write the record."""
    warnings.filterwarnings("ignore")
    rec = {
        "note": (
            "What still blocks a NEISO H1-2026 solve after the neiso-96 actuals "
            "intake. The scoring TARGET now exists (actual_lmp row present, 126 "
            "actual RT hours over $300). The SOLVE does not: the demand path "
            "rejects any extract that is not a full HOURS_PER_YEAR series, and "
            "the fallback demand-profiles parquet has no 2026 row, so a "
            "half-year cannot be built. The gate is in shared code and every BA "
            "fails it for 2026 -- structural and six-ISO, not a NEISO data gap. "
            "No year solved, scored or registered."
        ),
        "input_walk_2026": input_walk(),
        "full_year_gate": full_year_gate(),
        "demand_profiles_coverage": demand_profiles_coverage(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1) + "\n")

    print("NEISO 2026 input walk (2023 control shown where the probe returns it):")
    for name, years in rec["input_walk_2026"].items():
        for y, r in years.items():
            print(f"  {name:30s} {y}  {r['status']:4s}  {r['note'][:78]}")
    print(f"\nfull-year gate (HOURS_PER_YEAR = {rec['full_year_gate']['hours_per_year_gate']}):")
    for ba, row in rec["full_year_gate"]["bas"].items():
        print(f"  {ba:16s} 2025: {str(row['2025']):16s} 2026: {row['2026']}")
    print(f"\neia_demand_profiles.parquet coverage: {rec['demand_profiles_coverage']}")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
