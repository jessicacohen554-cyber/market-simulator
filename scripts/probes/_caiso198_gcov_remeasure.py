"""caiso-198 — G-COV re-measured on the state-scope-repaired instrument. **NO LP.**

Companion to :mod:`scripts.probes._caiso193_wefor_coverage` (the frozen-instrument
measurement) and :mod:`scripts.probes._caiso196_gcov_remeasure` (the remap-repaired
instrument). Run AFTER the Desert Star NV extract re-derive
(`PRECHECK-caiso198-desertstar-extract-2026-08-16.md` §2) to record what the same
two population readings measure once the LAST unobserved CC_REGULAR plant (EIA
55077) enters the extract. Two constructions inherit and one extends:

* ``pop_outage_extract`` — facility_ids in the re-derived
  ``data/raw/campd-unit-outages-CAISO.csv`` (the extract the LP derates from).
* ``pop_cems_unitlevel_remap_aware`` — facility_ids in the solve-year unit-level
  files over the ISO's FULL committed state list (``campd.states_for_iso`` —
  CA + NV since caiso-197; the caiso-196 probe predates the NV landing and read
  CA only), remap-aware per caiso-196.

The gate is taken on the STRICTER reading (GATESPEC-caiso193 §5 conservative
default). The frozen ``wefor_residual = 0.0`` is NOT recomputed — it is the
caiso-187 record's arithmetic identity and invariant to this repair (X_c can
only rise). No price series is read. Usage::

    python scripts/probes/_caiso198_gcov_remeasure.py
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
KEEPER = REPO / "results" / "calibration" / "caiso197_w2_r5"
OUTAGE_EXTRACT = REPO / "data" / "raw" / "campd-unit-outages-CAISO.csv"
UNIT_LEVEL_DIR = REPO / "data" / "raw" / "campd-unit-level"
OUT = REPO / "results" / "calibration" / "_caiso198_gcov_remeasure.json"
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

    states = campd.states_for_iso(ISO)
    cems_raw: set[int] = set()
    for state in states:
        for year in YEARS:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            col = pq.read_table(path, columns=["facilityId"]).column("facilityId")
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
        "states": list(states),
        "instrument": "STATE-SCOPE REPAIRED (ISO_STATES CAISO = CA+NV, caiso-197 "
        "NV landing + the caiso-198 re-derived extract; "
        "PRECHECK-caiso198-desertstar-extract-2026-08-16.md §2)",
        "per_class": per_class,
        "g_cov_surviving_groups": [k for k in GROUPS if per_class[k]["g_cov_pass"]],
        "frozen_value_note": "wefor_residual = 0.0 NOT recomputed — the "
        "caiso-187 record's arithmetic identity, invariant to this repair "
        "(X_c can only rise; residual_c = max(0, W_c - X_c)).",
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
