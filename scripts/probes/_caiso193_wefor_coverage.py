"""caiso-193 (lane 2) — the G-COV measurement and G-DOF arithmetic. **NO LP.**

`GATESPEC-caiso193-wefor-residual-2026-08-11.md` §4 G-COV: a class enters
``wefor_residual_groups`` only if ≥ 95 % of its EIA-860 capacity (through the
shipped fleet path, so the population is exactly the LP's bins — the
caiso-187 probe's construction) belongs to plants PRESENT in the committed
CAMPD CAISO extract population. A class below the bar is EXCLUDED fail-closed.

"Present in the committed CAMPD CAISO extract population" is measured against
BOTH defensible readings, and the gate is taken on the STRICTER of the two
(GATESPEC §5 conservative default — exclusion keeps MORE removal in place,
the anti-C3a-favorable direction):

* ``pop_outage_extract`` — facility_ids appearing in the committed
  ``data/raw/campd-unit-outages-CAISO.csv`` (sha256 25360e90…, the extract the
  LP derates from). A plant here has at least one detected ≥5-day window
  2018–2026.
* ``pop_cems_unitlevel`` — facility_ids appearing in the CAMPD unit-level CA
  extracts for the solve years (``data/raw/campd-unit-level/CA_{2023..2025}``),
  the detector's own source. This is the 40 CFR Part 75 "observed by CEMS"
  population: a plant here is instrumented even if it never had a qualifying
  outage.

G-DOF baseline: the committed keeper attestation's ``free_parameters``
(11 entries / 8 residual) with the ``wefor_multiplier`` row quoted, so the
arm's 11/7 target is arithmetic, not choice.

No price series is read anywhere. Usage::

    python scripts/probes/_caiso193_wefor_coverage.py
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
OUT = REPO / "results" / "calibration" / "_caiso193_wefor_coverage.json"
BAR = 0.95  # GATESPEC §4 G-COV — fixed before measurement.
GRANTED_GROUPS = ["CC_CHP", "CC_REGULAR"]  # owner ruling 2, caiso-191.


def _keeper_config():
    """The incumbent keeper's ScenarioConfig, from its own committed run_config."""
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    sc = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(**{k: v for k, v in sc.items() if k in fields})


def _fleet_by_class(cfg):
    """``{class: [(plant_code, pmax_mw)]}`` for the CAISO LP fleet (shipped path)."""
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


def _pop_outage_extract() -> set[int]:
    """facility_ids present anywhere in the committed CAMPD outage extract."""
    with OUTAGE_EXTRACT.open() as fh:
        return {int(row["facility_id"]) for row in csv.DictReader(fh)}


def _pop_cems_unitlevel() -> set[int]:
    """facility_ids present in the CAMPD unit-level CA extracts for the solve years."""
    import pyarrow.parquet as pq

    ids: set[int] = set()
    for year in YEARS:
        path = UNIT_LEVEL_DIR / f"CA_{year}.parquet"
        col = pq.read_table(path, columns=["facilityId"]).column("facilityId")
        ids.update(int(v) for v in col.unique().to_pylist())
    return ids


def main() -> None:
    """Measure G-COV for the two granted classes and record the G-DOF baseline."""
    cfg = _keeper_config()
    fleet = _fleet_by_class(cfg)
    pops = {
        "pop_outage_extract": _pop_outage_extract(),
        "pop_cems_unitlevel": _pop_cems_unitlevel(),
    }

    per_class: dict[str, dict] = {}
    surviving: list[str] = []
    for klass in GRANTED_GROUPS:
        plants = fleet.get(klass, {})
        total = sum(plants.values())
        row: dict = {
            "class_capacity_mw": round(total, 1),
            "plants": len(plants),
        }
        shares = {}
        for pop_name, pop in pops.items():
            covered = sum(mw for code, mw in plants.items() if code in pop)
            uncovered = sorted(
                (code, round(mw, 1)) for code, mw in plants.items() if code not in pop
            )
            shares[pop_name] = {
                "covered_capacity_mw": round(covered, 1),
                "share": round(covered / total, 6) if total else 0.0,
                "plants_covered": sum(1 for c in plants if c in pop),
                "uncovered_plants": uncovered,
            }
        row["populations"] = shares
        strict = min(s["share"] for s in shares.values())
        row["strict_share"] = round(strict, 6)
        row["bar"] = BAR
        row["g_cov_pass"] = strict >= BAR
        per_class[klass] = row
        if row["g_cov_pass"]:
            surviving.append(klass)

    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    fp = att.get("free_parameters", {})
    entries = fp.get("entries", fp.get("parameters", []))
    wefor_rows = [
        e
        for e in entries
        if "wefor" in json.dumps(e).lower()
    ]
    n_entries = fp.get("n_entries", len(entries))
    n_residual = fp.get(
        "n_residual",
        sum(1 for e in entries if str(e.get("identification", "")).lower() == "residual"),
    )

    out = {
        "iso": ISO,
        "years": YEARS,
        "keeper": KEEPER.name,
        "gatespec": "GATESPEC-caiso193-wefor-residual-2026-08-11.md",
        "granted_groups": GRANTED_GROUPS,
        "bar": BAR,
        "population_definitions": {
            "pop_outage_extract": str(OUTAGE_EXTRACT.relative_to(REPO)),
            "pop_cems_unitlevel": f"{UNIT_LEVEL_DIR.relative_to(REPO)}/CA_{{2023,2024,2025}}.parquet",
            "gate_rule": "strict = min(share over both populations); fail-closed "
            "(GATESPEC §5: exclusion keeps MORE removal in place)",
        },
        "per_class": per_class,
        "g_cov_surviving_groups": surviving,
        "g_dof_baseline": {
            "n_entries": n_entries,
            "n_residual": n_residual,
            "wefor_rows": wefor_rows,
            "target_after_arm": {"n_entries": 11, "n_residual": 7},
        },
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
