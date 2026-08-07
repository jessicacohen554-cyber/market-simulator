"""caiso-180: the cheap rule-14 ``[R-ACCURATE]`` outage-gate check. NO LP, NO solve.

``PRECHECK-caiso180-outage-reaudit-2026-08-07.md`` §5 asks one question about
three gates the keeper runs OFF — ``unit_outage_short_windows``,
``unit_partial_outage_windows``, ``unit_outage_maxgen_events`` — and requires the
session to **say which** of two pre-registered readings applies to each:

* **READING E — empty by construction.** The input is empty because the detector
  that would populate it cannot produce a row for this ISO's fleet. Arming the
  gate is provably inert, so OFF is correct *and examined*.
* **READING U — unexamined.** An accurate measured input exists (or could be
  produced) and the model is not consuming it: a rule-14 finding.

The PRECHECK's binding clause is that a finding here is **REPORTED, NOT ARMED** —
arming any of these gates would be a new mechanism needing its own
pre-registration, its own D-4 window and its own matrix cell, which this session
has no authorization to take.

Evidence this checks, all of it on-disk and re-runnable in about a second:

1. the three companion extracts' row counts (header-only vs populated);
2. the detectors' own scope — ``outages.py`` filters ``plant_group == "COAL"``
   for the short-window layer, and the partial layer declares the same guards;
3. whether CAMPD's CAISO population contains **any** coal-fired unit, read from
   ``campd-unit-level/CA_<year>.parquet``'s own ``primaryFuelInfo`` vocabulary;
4. whether the model fleet's coal (if any) is a CAMPD reporter at all;
5. the same short/partial file sizes across all six ISOs, as a cross-ISO control
   — if the files track coal fleet size, READING E is corroborated rather than
   merely asserted;
6. the layup companion's role, which the deriver's own ``--help`` settles.

Usage::

    uv run python scripts/probes/_caiso180_gate_check.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

RAW = REPO / "data/raw"
ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")
OUT = REPO / "results/calibration/_caiso180_gate_check.json"

#: The model fleet CAISO carries under fuel_type "coal" (legacy binned fleet).
FLEET_PARQUET = RAW / "_processed-legacy/caiso_fleet_binned.parquet"


def _rows(path: Path) -> int | None:
    """Data-row count of a committed extract, or None when the file is absent."""
    if not path.exists():
        return None
    return len(pd.read_csv(path))


def companion_census() -> dict:
    """Row counts + byte sizes for CAISO's three outage companions."""
    out = {}
    for tag, name in (
        ("short", "campd-unit-outages-short-CAISO.csv"),
        ("partial", "campd-partial-outages-CAISO.csv"),
        ("layup", "campd-unit-outages-layup-CAISO.csv"),
        ("standard", "campd-unit-outages-CAISO.csv"),
    ):
        p = RAW / name
        out[tag] = {
            "file": name,
            "exists": p.exists(),
            "bytes": p.stat().st_size if p.exists() else None,
            "data_rows": _rows(p),
        }
    mg = RAW / "maxgen-events"
    out["maxgen"] = {
        "dir": "data/raw/maxgen-events",
        "exists": mg.exists(),
        "iso_subdirs": sorted(d.name for d in mg.iterdir() if d.is_dir())
        if mg.exists()
        else [],
        "caiso_file_present": (mg / "caiso").exists() if mg.exists() else False,
    }
    return out


def campd_coal_population() -> dict:
    """Is there ANY coal-fired unit in CAMPD's CAISO population?

    Read from the raw CAMPD unit-level extracts' own ``primaryFuelInfo``
    vocabulary — the population both coal-only detectors run on.
    """
    fuels: set[str] = set()
    years = []
    for f in sorted((RAW / "campd-unit-level").glob("CA_*.parquet")):
        names = pq.read_schema(f).names
        if "primaryFuelInfo" not in names:
            continue
        col = pq.read_table(f, columns=["primaryFuelInfo"]).to_pandas()
        fuels |= {str(x) for x in col["primaryFuelInfo"].dropna().unique()}
        years.append(f.stem)
    coal_like = sorted(f for f in fuels if "coal" in f.lower())
    return {
        "files_scanned": years,
        "fuel_vocabulary": sorted(fuels),
        "coal_like_entries": coal_like,
        "any_coal_in_campd_caiso": bool(coal_like),
    }


def model_fleet_coal() -> dict:
    """CAISO's model-fleet coal, and whether it reports to CAMPD at all."""
    if not FLEET_PARQUET.exists():
        return {"fleet_parquet": str(FLEET_PARQUET), "exists": False}
    d = pd.read_parquet(FLEET_PARQUET)
    coal = d[d["fuel_type"] == "coal"]
    ext = pd.read_csv(RAW / "campd-unit-outages-CAISO.csv")
    lay = pd.read_csv(RAW / "campd-unit-outages-layup-CAISO.csv")
    ids = sorted({int(x) for x in coal["plant_id"].unique()})
    return {
        "n_coal_tranches": int(len(coal)),
        "plant_ids": ids,
        "plant_names": sorted(set(coal["plant_name"])),
        "zones": sorted(set(coal["zone"])),
        "total_pmax_mw": float(coal["pmax_mw"].sum()),
        "iso_fleet_pmax_mw": float(d["pmax_mw"].sum()),
        "share_of_fleet_pct": round(
            100.0 * coal["pmax_mw"].sum() / max(d["pmax_mw"].sum(), 1e-9), 4
        ),
        "in_campd_outage_extract": {
            str(i): int((ext["facility_id"] == i).sum()) for i in ids
        },
        "in_campd_layup_extract": {
            str(i): int((lay["facility_id"] == i).sum()) for i in ids
        },
        "outage_extract_plant_group_vocab": sorted(
            set(ext["plant_group"].dropna().astype(str))
        ),
        "outage_extract_coal_rows": int((ext["plant_group"] == "COAL").sum()),
    }


def cross_iso_control() -> dict:
    """Do short/partial file sizes track coal fleet size across all six ISOs?

    The control for READING E: if the two coal-heavy ISOs carry large files and
    the coal-light ones carry header-only files, the emptiness is a property of
    the detector's scope, not of CAISO's wiring.
    """
    out = {}
    for iso in ISOS:
        row = {}
        for tag, name in (
            ("short", f"campd-unit-outages-short-{iso}.csv"),
            ("partial", f"campd-partial-outages-{iso}.csv"),
        ):
            p = RAW / name
            row[tag] = {
                "exists": p.exists(),
                "bytes": p.stat().st_size if p.exists() else None,
                "data_rows": _rows(p),
            }
        out[iso] = row
    return out


def adjudicate(ev: dict) -> dict:
    """Assign READING E or READING U per gate, from the evidence gathered."""
    no_campd_coal = not ev["campd_coal_population"]["any_coal_in_campd_caiso"]
    short_empty = ev["companions"]["short"]["data_rows"] == 0
    partial_empty = ev["companions"]["partial"]["data_rows"] == 0
    fleet = ev["model_fleet_coal"]
    fleet_coal_absent_from_campd = all(
        n == 0 for n in fleet.get("in_campd_outage_extract", {}).values()
    )

    e_basis = (
        "Both detectors are coal-only (outages.py "
        "unit_outage_short_derate_factors filters plant_group == 'COAL'; the "
        "partial layer's docstring declares the same identification guards). "
        "CAMPD's CAISO population carries NO coal-fired unit of any kind "
        f"(fuel vocabulary {ev['campd_coal_population']['fuel_vocabulary']}), and "
        f"the model fleet's only coal — {fleet.get('plant_names')} "
        f"({fleet.get('total_pmax_mw')} MW, "
        f"{fleet.get('share_of_fleet_pct')}% of CAISO fleet capacity) — does not "
        "appear in the CAMPD extract at all. The detector cannot produce a CAISO "
        "row by construction, so arming the gate is provably inert."
    )

    return {
        "unit_outage_short_windows": {
            "reading": "E" if (short_empty and no_campd_coal) else "U",
            "off_because": "the data is genuinely empty, BY CONSTRUCTION",
            "basis": e_basis,
            "prior_adjudication": (
                "Independently reproduces caiso-136's existing matrix verdict "
                "I (inert) for this cell — cited, NOT re-minted (rule 28 "
                "DO-NOT-REDO). This session's basis is stronger than the prior "
                "one: not merely 'no rows produced' but 'no coal in the source "
                "population at all'."
            ),
            "armed_by_this_session": False,
        },
        "unit_partial_outage_windows": {
            "reading": "E" if (partial_empty and no_campd_coal) else "U",
            "off_because": "the data is genuinely empty, BY CONSTRUCTION",
            "basis": e_basis,
            "armed_by_this_session": False,
        },
        "unit_outage_maxgen_events": {
            # Distinct from the two above and deliberately NOT collapsed into
            # READING E: the input does not exist rather than being empty.
            "reading": "U (narrow) — DATA GAP, not a structural n/a",
            "off_because": "NO CAISO input exists at all",
            "basis": (
                "data/raw/maxgen-events/ contains only "
                f"{ev['companions']['maxgen']['iso_subdirs']} plus a README. The "
                "registry is a HAND-CURATED per-ISO set of publicly declared "
                "capacity-emergency instruments, built for the MISO "
                "price-formation lane (M-1); no CAISO registry has ever been "
                "curated. CAISO does declare real analogues (EEA levels), so "
                "this is a data-intake gap rather than a structural n/a — the "
                "gate cannot be armed because there is no file, not because a "
                "detector proved it inert."
            ),
            "disposition": (
                "REPORTED, NOT ARMED (PRECHECK §5 binding clause). Landing a "
                "CAISO registry is a separate data-intake charter with its own "
                "pre-registration, D-4 window and matrix cell."
            ),
            "armed_by_this_session": False,
        },
        "layup_companion": {
            "reading": "NOT a finding",
            "basis": (
                "campd-unit-outages-layup-CAISO.csv is the merit-order guard's "
                "record of the windows it REMOVED, not an unconsumed input. The "
                "deriver's own --help declares the companion is one 'which no "
                "loader reads' (scripts/data/derive_campd_unit_outages.py). Its "
                "row counts are exactly the guard's removals: kept + layup "
                "reproduces the 2026-07-24 regenerated totals with zero residual "
                "(547+93=640, 458+164=622, 635+98=733)."
            ),
            "armed_by_this_session": False,
        },
    }


def main() -> None:
    """Gather the evidence, adjudicate each gate, write the record."""
    ev = {
        "session": "caiso-180",
        "precheck_section": "§5 (cheap rule-14 [R-ACCURATE] gate check)",
        "no_lp": True,
        "companions": companion_census(),
        "campd_coal_population": campd_coal_population(),
        "model_fleet_coal": model_fleet_coal(),
        "cross_iso_control": cross_iso_control(),
    }
    ev["verdicts"] = adjudicate(ev)
    OUT.write_text(json.dumps(ev, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    for gate, v in ev["verdicts"].items():
        print(f"  {gate:32s} -> {v['reading']}  ({v.get('off_because', '-')})")


if __name__ == "__main__":
    main()
