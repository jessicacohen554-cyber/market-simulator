"""xiso-2 — post-guard provenance census of the outage-derived artifacts, all six ISOs.

§5.7's oldest open cross-cutting audit (flagged in ``docs/calibration-log/governance.md``
2026-07-26, unaudited until now). Mechanical, **zero LP**.

THE QUESTION
------------
The neiso-64 merit-order guard was adopted 2026-07-26 (governance.md, charter
``docs/handoffs/campd-economic-layup-fix-charter-2026-07.md`` §8) and every ISO's
committed ``campd-unit-outages[-<ISO>].csv`` was re-derived guard-on in commit
``6a8f285c5`` (2026-07-26 00:36 UTC), with the vetoed economic-layup windows moved
to ``campd-unit-outages-layup-<ISO>.csv`` companions. The audit asks, per ISO:

1. Which committed artifacts are DOWNSTREAM of those extracts?
2. Were they produced BEFORE the guard landed (i.e. are they stale)?
3. Does re-deriving them at HEAD reproduce the committed bytes?
4. Does any KEEPER consume a stale one?

ADMISSIBILITY (stated up front, per the arm's method note)
-----------------------------------------------------------
This is an AUDIT, not a mechanism. It reads committed bytes and re-runs frozen
derive scripts; it changes no ScenarioConfig field, arms nothing, and spends no
holdout year (the extracts span 2018–2026 but only their BYTES are compared —
rule 20 ``[R-HOLDOUT]`` explicitly permits "byte-identity / loader-resolvability
checks" on out-of-training data, and no solve, scoring or registration occurs).
Rule 23 ``[R-FROZEN-DERIVE]`` is the governing constraint on any FOLLOW-UP: a
re-derivation is admissible only on a SOURCE-DATA change, never on a residual.
The guard IS a source-data change, so re-derivation of a stale artifact is
admissible — but it is a separate act from this census and is not performed here.

Reporting against interest is the point: an artifact that reproduces
byte-identically is a full result, and is reported as prominently as a miss.

WHAT IT DOES
------------
* ``--census`` (default) — the dependency census: every producer that actually
  READS a guard-affected extract (a real file read, not a docstring mention),
  the committed artifact it writes, that artifact's last content-changing
  commit, and its position relative to the guard commit.
* the ``derive_maintenance_shape`` GLOB CONTAMINATION check: that script USED to
  pool ``data/raw/campd-unit-outages*.csv``, a glob that since 2026-07-26 also
  matches the guard's OWN vetoed-window companions (plus the e923 fallback,
  short-window and maxgen extracts). Reported as a file/row count and as the
  resulting difference in the derived constant. **xiso-2 FIXED the selector** —
  the script now enumerates the six standard extracts
  (``derive_maintenance_shape._STANDARD_EXTRACTS``) — so this section documents
  the defect the audit found and the probe keeps reproducing its size.
* the ``MAINTENANCE_MONTHLY_SHAPE`` reproduction test: re-derive at HEAD under
  (a) the PRE-FIX contaminated glob and (b) the six intended standard extracts
  (what the fixed script now does), and compare both to the committed constant
  in ``config/fuel_trajectories.py``.
* ``--verify-extracts DIR`` — byte-compare re-derived standard extracts staged in
  DIR against the committed ones. Produce DIR with, per ISO::

      python scripts/data/derive_campd_unit_outages.py --iso <ISO> \
          --years 2018 2019 2020 2021 2022 2023 2024 2025 2026 \
          --merit-order-guard --out DIR/<ISO>.csv

Run: ``python scripts/probes/_xiso2_outage_artifact_provenance_census.py``
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

# The commit that re-derived every ISO's committed extract guard-on, and moved the
# vetoed windows to the layup companions (governance.md 2026-07-26).
GUARD_COMMIT = "6a8f285c5"

# The six guard-affected STANDARD extracts — the only files the guard re-derived.
STANDARD_EXTRACTS: dict[str, str] = {
    "ERCOT": "campd-unit-outages.csv",
    "CAISO": "campd-unit-outages-CAISO.csv",
    "MISO": "campd-unit-outages-MISO.csv",
    "NEISO": "campd-unit-outages-NEISO.csv",
    "NYISO": "campd-unit-outages-NYISO.csv",
    "PJM": "campd-unit-outages-PJM.csv",
}

# Producers that perform a REAL read of a guard-affected extract, the committed
# artifact each writes, and that artifact's consumer. Established by dependency
# inspection in session xiso-2; docstring-only mentions are excluded (they are
# listed under NON_CONSUMERS so the exclusion is auditable rather than silent).
CENSUS: list[dict] = [
    {
        "artifact": "config/fuel_trajectories.py::MAINTENANCE_MONTHLY_SHAPE",
        "producer": "scripts/data/derive_maintenance_shape.py",
        "reads": "glob data/raw/campd-unit-outages*.csv (ALL six + companions)",
        "consumer": "data/fleet/arrays.py — FORECAST mode only "
        "(ScenarioConfig.maintenance_monthly_shape, default True)",
        # A code constant, not a path: date it by the commit that BAKED the values
        # (a later commit moved the block constants.py -> fuel_trajectories.py
        # without re-deriving, so pickaxing the symbol would over-state freshness).
        "dated_by": "1fd092221",
        "dated_note": "values baked here; block MOVED to fuel_trajectories.py by "
        "9824177b7 (2026-07-20) with no re-derivation",
    },
    {
        "artifact": "data/raw/reference/caiso-dam-resource-crosswalk.csv",
        "producer": "scripts/data/derive_caiso_dam_resource_crosswalk.py",
        "reads": "campd-unit-outages-CAISO.csv",
        "consumer": "NONE — no code path reads it (docs/findings only)",
    },
    {
        "artifact": "data/raw/reference/reliability_floor_coeffs_NYISO.csv "
        "(NYC/LI/Capital ST_GAS limbs)",
        "producer": "scripts/data/derive_nyiso_st_reliability_floor.py "
        "(prints coefficients; CSV hand-transcribed)",
        "reads": "campd-unit-outages-NYISO.csv (outage-free CF denominator)",
        "consumer": "config/iso_configs.py::RELIABILITY_FLOOR_REGISTRY — NYISO keeper",
    },
    {
        "artifact": "data/raw/campd-unit-outages-maxgen-MISO.csv",
        "producer": "scripts/data/derive_campd_maxgen_outages.py",
        "reads": "campd-unit-outages-MISO.csv (imports the standard deriver)",
        "consumer": "data/outages.py::unit_outage_maxgen_derate_factors (gated, default off)",
    },
    {
        "artifact": "data/raw/campd-unit-outages-short-<ISO>.csv (5 ISOs)",
        "producer": "scripts/data/derive_campd_unit_outages.py --short-windows",
        "reads": "same CAMPD source; disjoint-by-construction with the standard extract",
        "consumer": "data/outages.py::unit_outage_short_derate_factors",
        # One row per ISO — dated individually so a single stale ISO cannot hide
        # behind the freshest sibling.
        "date_paths": [
            f"data/raw/campd-unit-outages-short-{i}.csv"
            for i in ("CAISO", "MISO", "NEISO", "NYISO", "PJM")
        ],
    },
    {
        "artifact": "data/clean/** (curated Parquet)",
        "producer": "scripts/data/curate_outages.py, curate_unit_outage_events.py",
        "reads": "the six standard extracts",
        "consumer": "clean_io readers — DERIVED/disposable/gitignored, regenerated on "
        "demand, so not a staleness surface",
        "dated_by": None,
        "dated_note": "gitignored derived tree — no committed bytes, so no staleness "
        "surface by construction",
    },
]

# Scripts that MENTION an extract in prose but never read one — excluded from the
# census by inspection, listed so the exclusion is checkable.
NON_CONSUMERS: list[str] = [
    "scripts/data/build_calibration_reference.py (comment only)",
    "scripts/data/build_neiso_operable_capacity.py (docstring; reads morning_report_*.csv)",
    "scripts/data/derive_ct_deployment.py (docstring only)",
    "scripts/data/derive_ercot_commitment_loading_state.py (comment only)",
    "scripts/data/derive_partial_outages.py (comment; reads CAMPD unit-level directly)",
    "scripts/data/derive_nyiso_ct_reliability_floor.py (reads bin_assignments + weather)",
    "scripts/data/derive_reliability_coeffs.py and the *_drag derives (no outage read)",
]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True
    ).stdout.strip()


def last_commit(path: str) -> tuple[str, str, str]:
    """(sha, date, subject) of the last non-merge commit touching *path*."""
    out = _git("log", "-1", "--no-merges", "--format=%h|%ad|%s", "--date=short", "--", path)
    if not out:
        return ("-", "-", "(not a tracked path)")
    sha, date, subj = out.split("|", 2)
    return sha, date, subj


def post_guard(sha: str) -> bool | None:
    """True if *sha* contains the guard commit; None if undeterminable."""
    if sha == "-":
        return None
    r = subprocess.run(
        ["git", "merge-base", "--is-ancestor", GUARD_COMMIT, sha],
        cwd=REPO,
        capture_output=True,
    )
    return r.returncode == 0


def report_census() -> None:
    print("=" * 78)
    print("A. GUARD TIMELINE")
    print("=" * 78)
    print(f"  guard commit {GUARD_COMMIT}  {_git('show', '-s', '--format=%ad  %s', '--date=iso', GUARD_COMMIT)}")
    print()
    print("  Per-ISO standard extract, last content-changing commit:")
    for iso, name in STANDARD_EXTRACTS.items():
        sha, date, subj = last_commit(f"data/raw/{name}")
        print(f"    {iso:6} {date}  {sha}  {subj[:52]}")
    print()

    print("=" * 78)
    print("B. DEPENDENCY CENSUS — artifacts downstream of a guard-affected extract")
    print("=" * 78)
    for row in CENSUS:
        art = row["artifact"]
        print(f"\n  artifact : {art}")
        print(f"  producer : {row['producer']}")
        print(f"  reads    : {row['reads']}")
        print(f"  consumer : {row['consumer']}")

        if "date_paths" in row:
            # Multi-file artifact: date each member, so one stale ISO is visible.
            for p in row["date_paths"]:
                sha, date, subj = last_commit(p)
                pg = post_guard(sha)
                tag = {True: "POST-GUARD", False: "PRE-GUARD (STALE)", None: "n/a"}[pg]
                print(f"    {Path(p).name:38} {date}  {sha}  [{tag}]")
            continue

        if "dated_by" in row and row["dated_by"] is None:
            print(f"  last-derived: n/a — {row['dated_note']}")
            continue

        ref = row.get("dated_by") or art.split("::")[0].split(" ")[0]
        if row.get("dated_by"):
            sha = ref
            date = _git("show", "-s", "--format=%ad", "--date=short", ref)
            subj = _git("show", "-s", "--format=%s", ref)
        else:
            sha, date, subj = last_commit(ref)
        pg = post_guard(sha)
        tag = {True: "POST-GUARD", False: "PRE-GUARD (STALE)", None: "n/a"}[pg]
        print(f"  last-derived: {date}  {sha}  [{tag}]")
        print(f"                {subj[:66]}")
        if row.get("dated_note"):
            print(f"                note: {row['dated_note']}")
    print("\n  Excluded by inspection (mention an extract, never read one):")
    for n in NON_CONSUMERS:
        print(f"    - {n}")
    print()


def report_glob() -> list[str]:
    """The derive_maintenance_shape glob contamination. Returns the HEAD file list."""
    raw = REPO / "data" / "raw"
    head = sorted(glob.glob(str(raw / "campd-unit-outages*.csv")))
    std = [str(raw / n) for n in STANDARD_EXTRACTS.values()]
    print("=" * 78)
    print("C. derive_maintenance_shape GLOB CONTAMINATION (defect found + FIXED by xiso-2)")
    print("=" * 78)
    print("  The script USED to pool glob('data/raw/campd-unit-outages*.csv'). Intended:")
    print("  the six STANDARD extracts. That glob matches at HEAD:")
    buckets: dict[str, list[str]] = {}
    for p in head:
        b = Path(p).name
        kind = (
            "layup (the guard's OWN vetoes)"
            if "-layup" in b
            else "e923 fallback (different source)"
            if "-e923-" in b
            else "short-window companion"
            if "-short-" in b
            else "maxgen derate companion"
            if "-maxgen-" in b
            else "STANDARD (intended)"
        )
        buckets.setdefault(kind, []).append(b)
    for kind, names in sorted(buckets.items(), key=lambda kv: kv[0] != "STANDARD (intended)"):
        print(f"    [{len(names):2}] {kind}")
        for n in names:
            print(f"         {n}")
    n_head = sum(len(pd.read_csv(p)) for p in head)
    n_std = sum(len(pd.read_csv(p)) for p in std)
    print()
    print(f"  files: glob {len(head):3}   intended {len(std):3}")
    print(f"  rows : glob {n_head:,}   intended {n_std:,}   "
          f"inflation +{100 * (n_head - n_std) / n_std:.1f} %")
    print("\n  The layup companions are the windows the guard EXISTS to remove; pooling")
    print("  them back in partially inverts the guard for this artifact (rule 19).")
    print("  FIXED by xiso-2: derive_maintenance_shape now enumerates the six standard")
    print("  extracts (_STANDARD_EXTRACTS) instead of globbing.")
    print()
    return head


def report_maintenance_shape(head_paths: list[str]) -> None:
    import scripts.data.derive_maintenance_shape as m
    from market_sim.config.fuel_trajectories import MAINTENANCE_MONTHLY_SHAPE as COMMITTED

    raw = REPO / "data" / "raw"
    std_paths = [str(raw / n) for n in STANDARD_EXTRACTS.values()]

    def derive_with(paths: list[str]):
        def loader() -> pd.DataFrame:
            frames = []
            for p in paths:
                d = pd.read_csv(p)
                d["_iso_file"] = Path(p).stem
                frames.append(d)
            return pd.concat(frames, ignore_index=True)

        original, m.load_unit_outages = m.load_unit_outages, loader
        try:
            shapes, pooled, _obs = m.derive()
        finally:
            m.load_unit_outages = original
        out = {g: tuple(round(float(v), 3) for v in shapes[g]) for g in m._TARGET_GROUPS}
        out["_POOLED"] = tuple(round(float(v), 3) for v in pooled)
        return out

    head = derive_with(head_paths)
    std = derive_with(std_paths)

    print("=" * 78)
    print("D. MAINTENANCE_MONTHLY_SHAPE — does it reproduce at HEAD?")
    print("=" * 78)
    print("  COMMITTED = config/fuel_trajectories.py (baked 2026-06-25, PRE-guard)")
    print("  PREFIX    = re-derived at HEAD with the PRE-FIX contaminated glob")
    print("  STD6      = re-derived at HEAD from the six standard extracts only")
    print("              (what the xiso-2-fixed script now does)\n")
    any_miss = False
    for grp in head:
        c, h, s = COMMITTED[grp], head[grp], std[grp]
        dh = max(abs(x - y) for x, y in zip(c, h))
        ds = max(abs(x - y) for x, y in zip(c, s))
        any_miss |= (dh > 1e-9) or (ds > 1e-9)
        print(f"  {grp}")
        print(f"    COMMITTED {' '.join(f'{v:5.3f}' for v in c)}")
        print(f"    PREFIX    {' '.join(f'{v:5.3f}' for v in h)}   max|d| {dh:.3f}")
        print(f"    STD6      {' '.join(f'{v:5.3f}' for v in s)}   max|d| {ds:.3f}")
    print()
    print("  VERDICT: " + (
        "the committed constant does NOT reproduce at HEAD under either selector."
        if any_miss else "reproduces byte-for-byte."))
    print("  Note, against interest: STD6 is not uniformly closer to the committed")
    print("  value than PREFIX (CT_CHP / ST_GAS / ST_CHP are further). Fixing the")
    print("  glob alone therefore does NOT restore the committed constant — the")
    print("  artifact is genuinely stale w.r.t. the 2026-07-24 backfill and the")
    print("  2026-07-26 guard, which are BOTH source-data changes and so make a")
    print("  re-derivation rule-23 ADMISSIBLE (as a separate, gated act).")
    print()


def verify_extracts(stage: Path) -> None:
    print("=" * 78)
    print("E. BYTE-REPRODUCTION of the six committed STANDARD extracts at HEAD")
    print("=" * 78)
    print(f"  staged re-derivations: {stage}\n")
    print(f"  {'ISO':6} {'re-derived md5':34} {'committed md5':34} verdict")
    ok = miss = absent = 0
    for iso, name in STANDARD_EXTRACTS.items():
        committed = REPO / "data" / "raw" / name
        cand = None
        for probe in (stage / f"{iso}.csv", stage / f"{iso.lower()}.csv"):
            if probe.exists():
                cand = probe
                break
        if cand is None:
            print(f"  {iso:6} {'(not staged)':34} {'':34} SKIPPED")
            absent += 1
            continue
        a = hashlib.md5(cand.read_bytes()).hexdigest()
        b = hashlib.md5(committed.read_bytes()).hexdigest()
        if a == b:
            ok += 1
            verdict = "BYTE-IDENTICAL"
        else:
            miss += 1
            verdict = "*** MISMATCH ***"
        print(f"  {iso:6} {a:34} {b:34} {verdict}")
    print(f"\n  {ok} byte-identical, {miss} mismatched, {absent} not staged.")
    print()
    print("  xiso-2 baseline (2026-08-02): 5/6 byte-identical; MISO the sole mismatch.")
    print("  MISO's re-derivation is a strict SUPERSET — +17 windows, 0 lost, ALL of")
    print("  them 2022 COAL — and its layup companion is byte-identical, so the guard's")
    print("  own classification reproduces exactly. Root cause is a SOURCE-DATA change,")
    print("  not detector drift: commit 5cd937407 (2026-07-31) filled the MISO EIA-930")
    print("  2022 wide-hourly hole, taking 2022 from 7 rows to 8,760 (8,757 non-null")
    print("  Demand), and the detector's revealed-availability filter needs that system")
    print("  load. The 2023-2025 TRAINING window is IDENTICAL row-for-row, so no MISO")
    print("  keeper reads a stale byte; the drift is entirely inside the 2022 VALIDATION")
    print("  holdout. Re-derivation is therefore rule-23 ADMISSIBLE (a source-data")
    print("  change) but NOT urgent — and it must not be done as a side effect of a")
    print("  calibration session (rule 23: cite the data change).")
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--verify-extracts",
        metavar="DIR",
        help="Byte-compare re-derived standard extracts staged in DIR against "
        "the committed ones (see module docstring for the recipe).",
    )
    ap.add_argument(
        "--skip-shape",
        action="store_true",
        help="Skip the MAINTENANCE_MONTHLY_SHAPE re-derivation (the slow part).",
    )
    args = ap.parse_args()

    print("\nxiso-2 — post-guard provenance census of outage-derived artifacts")
    print(f"repo HEAD: {_git('rev-parse', '--short', 'HEAD')}\n")

    report_census()
    head_paths = report_glob()
    if not args.skip_shape:
        report_maintenance_shape(head_paths)
    if args.verify_extracts:
        verify_extracts(Path(args.verify_extracts))


if __name__ == "__main__":
    main()
