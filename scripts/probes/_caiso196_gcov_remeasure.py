"""caiso-196 — G-COV re-measured on the REPAIRED instrument. **NO LP.**

Companion to :mod:`scripts.probes._caiso193_wefor_coverage` (the frozen-instrument
measurement that killed lane 2 at G-COV). Run AFTER the El Segundo remap repair
(``campd.CAMPD_UNIT_PLANT_REMAP`` gains ``(330, "5"/"7") → 57901``) and the
full-span extract re-derivation, to record what the same two population readings
measure on the repaired instrument (PRECHECK-caiso196 §7 artifact;
FINDING-caiso193 §3's numbers re-produced from bytes rather than arithmetic).

The CEMS population is remap-aware here: a fleet plant is CEMS-observed if its own
code OR any legacy ORIS that remaps to it appears in the solve-year unit-level
files. No price series is read. Usage::

    python scripts/probes/_caiso196_gcov_remeasure.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

ISO = "CAISO"
YEARS = [2023, 2024, 2025]
KEEPER = REPO / "results" / "calibration" / "caiso188_d1_micseam"
OUTAGE_EXTRACT = REPO / "data" / "raw" / "campd-unit-outages-CAISO.csv"
UNIT_LEVEL_DIR = REPO / "data" / "raw" / "campd-unit-level"
OUT = REPO / "results" / "calibration" / "_caiso196_gcov_remeasure.json"
BAR = 0.95
GROUPS = ["CC_CHP", "CC_REGULAR"]


def _keeper_config():
    """The incumbent keeper's ScenarioConfig, from its own committed run_config."""
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    sc = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(**{k: v for k, v in sc.items() if k in fields})


def _fleet_by_class(cfg):
    """``{class: {plant_code: pmax_mw}}`` for the CAISO LP fleet (shipped path)."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet.assembly import bins_to_fleet, load_or_synthesize_bins

    iso_cfg = get_iso_config(ISO)
    bins = load_or_synthesize_bins(cfg, ISO, iso_cfg, [])
    gens, _ = bins_to_fleet(bins, [z.name for z in iso_cfg.zones], cfg)
    out: dict[str, dict[int, float]] = {}
    for g in gens:
        cls = out.setdefault(str(g.plant_group), {})
        code = int(g.plant_code)
        cls[code] = cls.get(code, 0.0) + float(g.pmax_mw)
    return out


def main() -> None:
    """Re-measure both G-COV population readings on the repaired instrument."""
    import pyarrow.parquet as pq

    from market_sim.data import campd

    cfg = _keeper_config()
    fleet = _fleet_by_class(cfg)

    with OUTAGE_EXTRACT.open() as fh:
        pop_extract = {int(row["facility_id"]) for row in csv.DictReader(fh)}

    cems_raw: set[int] = set()
    for year in YEARS:
        col = pq.read_table(
            UNIT_LEVEL_DIR / f"CA_{year}.parquet", columns=["facilityId"]
        ).column("facilityId")
        cems_raw.update(int(v) for v in col.unique().to_pylist())
    # Remap-aware view: a fleet plant is observed if any legacy ORIS maps to it.
    remap_targets = {
        eia: oris for (oris, _u), eia in campd.CAMPD_UNIT_PLANT_REMAP.items()
    }
    pop_cems = set(cems_raw) | {
        eia for eia, oris in remap_targets.items() if oris in cems_raw
    }

    per_class: dict[str, dict] = {}
    for klass in GROUPS:
        plants = fleet.get(klass, {})
        total = sum(plants.values())
        row: dict = {"class_capacity_mw": round(total, 1), "plants": len(plants)}
        for pop_name, pop in (
            ("pop_outage_extract", pop_extract),
            ("pop_cems_unitlevel_remap_aware", pop_cems),
        ):
            covered = sum(mw for code, mw in plants.items() if code in pop)
            row[pop_name] = {
                "covered_capacity_mw": round(covered, 1),
                "share": round(covered / total, 6) if total else 0.0,
                "uncovered_plants": sorted(
                    (code, round(mw, 1))
                    for code, mw in plants.items()
                    if code not in pop
                ),
            }
        shares = [
            row["pop_outage_extract"]["share"],
            row["pop_cems_unitlevel_remap_aware"]["share"],
        ]
        row["strict_share"] = round(min(shares), 6)
        row["bar"] = BAR
        row["g_cov_pass"] = min(shares) >= BAR
        per_class[klass] = row

    out = {
        "iso": ISO,
        "years": YEARS,
        "keeper": KEEPER.name,
        "instrument": "REPAIRED (campd.CAMPD_UNIT_PLANT_REMAP + re-derived extract; "
        "PRECHECK-caiso196-elsegundo-remap-2026-08-15.md §2)",
        "remap_entries": sorted(
            f"({o}, {u!r}) -> {e}"
            for (o, u), e in campd.CAMPD_UNIT_PLANT_REMAP.items()
        ),
        "per_class": per_class,
        "g_cov_surviving_groups": [k for k in GROUPS if per_class[k]["g_cov_pass"]],
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
