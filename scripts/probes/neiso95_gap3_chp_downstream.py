"""neiso-95 — gap 3 downstream check: is the CHP classification the SOLVE PATH consumes
vintage-correct per year, and are the tuned years 2023-2025 unmoved?

neiso-93 extended ``data/raw/_processed-legacy/eia860_chp_by_year.parquet`` from
2023-2025 (40,037 rows) to 2018-2025 (92,633 rows). The claim under test is that
this changed **coverage**, not the tuned years. Three legs:

  **A. Artifact diff.** The 2023 / 2024 / 2025 partitions of the extended
     artifact vs the pre-neiso-93 blob (``git show 20c2a4b^:``), plant-for-plant.

  **B. Reader.** ``market_sim.data.chp._chp_by_plant(dir, year)`` returns THAT
     year's row for every year now covered, and the snapshot fallback (``year=None``)
     is a distinct series — i.e. the vintage path is live, not silently falling back.

  **C. Fleet.** The NEISO fleet the backcast actually builds
     (``load_fleet_from_csv(iso, cfg, year=<solve year>)`` — the call
     ``scripts/run_calibration.py`` makes at BOTH its fleet-sourcing branches,
     lines 2943 and 2969 ``vintage_year=year``) carries the same CHP classes and
     capacities in 2023-2025 as it did before the extension, and the extension
     is what changes the 2019-2022 classification away from the 2025-era snapshot.

Rule 22 ``[R-HOLDOUT]``: leg C reads INPUTS for 2019-2022 — permitted and
unrestricted ("what is held out is the SCORE, never the DATA"). **No LP is
constructed, no year is solved, scored or registered.** The pre-extension
artifact is materialized read-only into a scratch path; the committed file is
never modified.

Usage::

    uv run python scripts/probes/neiso95_gap3_chp_downstream.py
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ARTIFACT = REPO / "data/raw/_processed-legacy/eia860_chp_by_year.parquet"
PRE_GAP3_COMMIT = "20c2a4b^"  # parent of "neiso-93 gap 3: extend EIA-860 CHP-by-vintage"
TUNED = (2023, 2024, 2025)
COVERED = (2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025)
CHP_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP")
OUT = REPO / "results/calibration/_neiso95_gap3_chp_downstream.json"


def pre_gap3_artifact() -> pd.DataFrame:
    """The committed CHP-by-year artifact as it stood before neiso-93's gap 3."""
    blob = subprocess.run(
        ["git", "show", f"{PRE_GAP3_COMMIT}:data/raw/_processed-legacy/eia860_chp_by_year.parquet"],
        cwd=REPO,
        capture_output=True,
        check=True,
    ).stdout
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as fh:
        fh.write(blob)
        tmp = fh.name
    return pd.read_parquet(tmp)


def leg_a(old: pd.DataFrame, new: pd.DataFrame) -> dict:
    """Plant-for-plant diff of the tuned-year partitions."""
    rows = []
    for y in TUNED:
        o = old[old["year"] == y].set_index("plant_id")["chp"].sort_index()
        n = new[new["year"] == y].set_index("plant_id")["chp"].sort_index()
        index_same = bool(o.index.equals(n.index))
        rows.append(
            {
                "year": y,
                "plants_before": int(len(o)),
                "plants_after": int(len(n)),
                "index_identical": index_same,
                "values_identical": bool(index_same and (o == n).all()),
                "chp_y_before": int((o == "Y").sum()),
                "chp_y_after": int((n == "Y").sum()),
            }
        )
    return {
        "rows_before": int(len(old)),
        "rows_after": int(len(new)),
        "years_before": sorted(int(y) for y in old["year"].unique()),
        "years_after": sorted(int(y) for y in new["year"].unique()),
        "tuned_years": rows,
        "tuned_years_all_identical": all(r["values_identical"] for r in rows),
    }


def leg_b() -> dict:
    """The reader returns each year's own vintage; the snapshot is a distinct series."""
    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.chp import _chp_by_plant

    art = pd.read_parquet(ARTIFACT)
    snap = _chp_by_plant(EIA_860_DIR, None)
    rows = []
    for y in COVERED:
        got = _chp_by_plant(EIA_860_DIR, y)
        want = art[art["year"] == y].set_index("plant_id")["chp"]
        matches = bool(
            len(got) == len(want)
            and got.sort_index().index.equals(want.sort_index().index)
            and (got.sort_index().to_numpy() == want.sort_index().to_numpy()).all()
        )
        common = got.index.intersection(snap.index)
        rows.append(
            {
                "year": y,
                "plants": int(len(got)),
                "matches_artifact_row": matches,
                "differs_from_snapshot_on_plants": int(
                    (got.loc[common].to_numpy() != snap.loc[common].to_numpy()).sum()
                ),
                "snapshot_common_plants": int(len(common)),
            }
        )
    return {"snapshot_plants": int(len(snap)), "per_year": rows}


def leg_c() -> dict:
    """NEISO fleet CHP composition per vintage year, on the solve-path loader."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    cfg = get_iso_config("NEISO")
    rows = []
    for y in COVERED:
        gens = load_fleet_from_csv("NEISO", cfg, year=y)
        cnt = Counter(g.plant_group for g in gens if g.plant_group in CHP_CLASSES)
        cap = {
            k: round(
                sum(g.pmax_mw for g in gens if g.plant_group == k),
                3,
            )
            for k in CHP_CLASSES
        }
        plants = sorted(
            {int(g.plant_code) for g in gens if g.plant_group in CHP_CLASSES}
        )
        rows.append(
            {
                "year": y,
                "fleet_units": int(len(gens)),
                "chp_units": {k: int(cnt.get(k, 0)) for k in CHP_CLASSES},
                "chp_mw": cap,
                "chp_plants": plants,
                "chp_plant_count": len(plants),
            }
        )
    return {"per_year": rows}


def main() -> None:
    new = pd.read_parquet(ARTIFACT)
    old = pre_gap3_artifact()

    result = {
        "probe": "neiso95_gap3_chp_downstream",
        "artifact": str(ARTIFACT.relative_to(REPO)),
        "pre_gap3_commit": PRE_GAP3_COMMIT,
        "solve_performed": False,
        "leg_a_artifact_diff": leg_a(old, new),
        "leg_b_reader": leg_b(),
        "leg_c_fleet": leg_c(),
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")

    a = result["leg_a_artifact_diff"]
    print("=== LEG A — artifact diff across neiso-93 gap 3 ===")
    print(f"  rows {a['rows_before']} -> {a['rows_after']}")
    print(f"  years {a['years_before']} -> {a['years_after']}")
    for r in a["tuned_years"]:
        print(
            f"  {r['year']}: {r['plants_before']} -> {r['plants_after']} plants, "
            f"index identical={r['index_identical']}, values identical={r['values_identical']}, "
            f"CHP=Y {r['chp_y_before']} -> {r['chp_y_after']}"
        )
    print(f"  TUNED YEARS ALL IDENTICAL: {a['tuned_years_all_identical']}")

    b = result["leg_b_reader"]
    print(f"\n=== LEG B — reader (snapshot fallback = {b['snapshot_plants']} plants) ===")
    for r in b["per_year"]:
        print(
            f"  {r['year']}: {r['plants']:>6} plants  matches artifact row={r['matches_artifact_row']}"
            f"  differs from snapshot on {r['differs_from_snapshot_on_plants']:>4}"
            f" / {r['snapshot_common_plants']} common"
        )

    print("\n=== LEG C — NEISO fleet CHP composition per vintage ===")
    for r in result["leg_c_fleet"]["per_year"]:
        print(
            f"  {r['year']}: units {r['fleet_units']:>4}  "
            f"CC_CHP {r['chp_units']['CC_CHP']:>2}u/{r['chp_mw']['CC_CHP']:>8.1f}MW  "
            f"CT_CHP {r['chp_units']['CT_CHP']:>2}u/{r['chp_mw']['CT_CHP']:>7.1f}MW  "
            f"ST_CHP {r['chp_units']['ST_CHP']:>2}u/{r['chp_mw']['ST_CHP']:>7.1f}MW  "
            f"({r['chp_plant_count']} plants)"
        )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
