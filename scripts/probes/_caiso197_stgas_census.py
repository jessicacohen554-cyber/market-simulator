"""caiso-197 (lane 3) — the CAISO ST_GAS fleet census and the GADS-class EFORd
derivation for ``gas_st_wefor_base_override``. **NO LP. No price series.**

`GATESPEC-caiso193-stgas-wefor-2026-08-11.md` §2/§3: replace the ERCOT-fitted
ST_GAS WEFOR base (``constants.THERMAL_AVAILABILITY["ST_GAS"] = 0.21``) with a
CAISO-fleet-derived, publicly cited class EFOR, entered through the registered
field ``gas_st_wefor_base_override``. The chain this probe records:

1. **EIA-860 census** of the CAISO ST_GAS fleet through the SHIPPED fleet path
   (the caiso-187/193 probe construction, so the population is exactly the
   LP's bins), unit detail from ``data/raw/eia-860/eia860_generator_operable``.
2. **The published class table**: NERC GADS "Generating Unit Statistical
   Brochure 3 — 2020-2024 — Unit Reporting Events" (public, retrieval-recorded
   corpus ``data/raw/reference/nerc-gads-eford-2020-2024/``), FOSSIL Gas
   Primary rows by unit size class.
3. **The mapping arithmetic**: each census unit's EIA-860 summer capacity (the
   NMC analog) selects its GADS size-class row; the override value is the
   unit-capacity-weighted mean of the selected rows' EFORd.

Derivation rules, fixed BEFORE this probe was first run (PRECHECK §2 quotes
them; GATESPEC §4 G-FROZEN):

* **Metric = EFORd** (demand-adjusted equivalent forced outage rate). Anchor:
  the model applies the value as hourly availability derate — the probability
  the unit is forced-unavailable when the market demands it, which is EFORd's
  definition; EFOR overweights forced hours for cycling/intermediate units
  (service hours shrink, forced hours persist). The repo's own reading of the
  SAME document family is 1 − EFORd (``gas_availability_factor = 0.866`` =
  1 − 0.1344, the 2019-2023 brochure's Gas Primary All Sizes EFORd —
  ``docs/parameter-citations.md``), and the corpus README's availability table
  quotes EFORd.
* **Window = 2020-2024** (brochure 3): the newest published pool, the maximal
  overlap with the 2023-2025 solve years, AND the highest pooled Gas Primary
  value of the three rolling windows (12.60 → 13.44 → 14.26 across
  2018-2022 → 2019-2023 → 2020-2024) — the recency rule and the GATESPEC §4
  higher-defensible-value rule agree, so no ambiguity is spent.
* **Category = FOSSIL Gas Primary** (gas-fired fossil steam — the exact class
  semantics of ST_GAS). Fallback ONLY on NERC suppression of a needed size
  row: the same size row of FOSSIL Oil/Gas Primary (the published superset),
  then the Gas Primary All Sizes row. Every fallback taken is recorded.
* **Size classes**: GADS NMC bands (001-099 … 1000 Plus) keyed on EIA-860
  summer capacity per unit.

CAMPD is cited only to RE-VERIFY the zero-overlay-coverage premise (a count
over the committed extract — no fit): ST_GAS plants in
``data/raw/campd-unit-outages-CAISO.csv``.

Usage::

    python scripts/probes/_caiso197_stgas_census.py
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
KEEPER = REPO / "results" / "calibration" / "caiso196_e1_elsegundo"
EIA860_GEN = REPO / "data" / "raw" / "eia-860" / "eia860_generator_operable.parquet"
GADS_DIR = REPO / "data" / "raw" / "reference"
GADS_WINDOWS = ["2018-2022", "2019-2023", "2020-2024"]  # cited context; gate on last
GADS_GATE_WINDOW = "2020-2024"
OUTAGE_EXTRACT = REPO / "data" / "raw" / "campd-unit-outages-CAISO.csv"
OUT = REPO / "results" / "calibration" / "_caiso197_stgas_census.json"

# GADS size classes, keyed by (lo, hi] MW of unit NMC (EIA-860 summer capacity
# as the NMC analog). Labels exactly as printed in the brochure CSV.
SIZE_CLASSES = [
    (0.0, 99.5, "001-099"),
    (99.5, 199.5, "100-199"),
    (199.5, 299.5, "200-299"),
    (299.5, 399.5, "300-399"),
    (399.5, 599.5, "400-599"),
    (599.5, 799.5, "600-799"),
    (799.5, 999.5, "800-999"),
    (999.5, float("inf"), "1000 Plus"),
]


def _keeper_config():
    """The caiso-196 keeper's ScenarioConfig from its committed run_config."""
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    sc = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(**{k: v for k, v in sc.items() if k in fields})


def _stgas_fleet(cfg) -> dict[int, float]:
    """``{plant_code: pmax_mw}`` for the LP's ST_GAS bins (shipped path)."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet.assembly import bins_to_fleet, load_or_synthesize_bins

    iso_cfg = get_iso_config(ISO)
    bins = load_or_synthesize_bins(cfg, ISO, iso_cfg, [])
    gens, _ = bins_to_fleet(bins, [z.name for z in iso_cfg.zones], cfg)
    out: dict[int, float] = {}
    for g in gens:
        if str(g.plant_group) == "ST_GAS":
            code = int(g.plant_code)
            out[code] = out.get(code, 0.0) + float(g.pmax_mw)
    return out


def _census_units(plant_codes: set[int]) -> list[dict]:
    """EIA-860 generator rows for the census plants: gas-fired steam units."""
    import pyarrow.parquet as pq

    t = pq.read_table(
        EIA860_GEN,
        columns=[
            "Plant Code",
            "Plant Name",
            "Generator ID",
            "Prime Mover",
            "Nameplate Capacity (MW)",
            "Summer Capacity (MW)",
            "Operating Year",
            "Energy Source 1",
            "Status",
        ],
    ).to_pylist()
    units = []
    for r in t:
        try:
            code = int(r["Plant Code"])
        except (TypeError, ValueError):
            continue
        if code not in plant_codes:
            continue
        if str(r["Prime Mover"]).strip().upper() != "ST":
            continue
        units.append(
            {
                "plant_code": code,
                "plant_name": str(r["Plant Name"]).strip(),
                "generator_id": str(r["Generator ID"]).strip(),
                "prime_mover": "ST",
                "energy_source_1": str(r["Energy Source 1"]).strip(),
                "status": str(r["Status"]).strip(),
                "nameplate_mw": float(r["Nameplate Capacity (MW)"] or 0.0),
                "summer_mw": float(r["Summer Capacity (MW)"] or 0.0),
                "operating_year": int(r["Operating Year"] or 0),
            }
        )
    return sorted(units, key=lambda u: (u["plant_code"], u["generator_id"]))


def _size_class(summer_mw: float) -> str:
    for lo, hi, label in SIZE_CLASSES:
        if lo < summer_mw <= hi or (lo == 0.0 and summer_mw <= hi):
            return label
    return "All Sizes"


def _gads_rows(window: str) -> dict[str, dict[str, float]]:
    """``{category-size: {FOR, EFOR, EFORd, units, unit_years}}`` for a window."""
    path = (
        GADS_DIR
        / f"nerc-gads-eford-{window}"
        / f"nerc_gads_eford_{window}.csv"
    )
    def _num(v: str) -> float | None:
        # NERC suppresses n<=3-unit rows with "*" in the older window files
        # (the 2020-2024 extraction drops them entirely); a suppressed row is
        # unusable and must never silently read as 0.
        v = (v or "").strip()
        if not v or v == "*":
            return None
        return float(v)

    rows: dict[str, dict[str, float | None]] = {}
    with path.open() as fh:
        for r in csv.DictReader(fh):
            label = " ".join(str(r["Generator Catagory/Classification"]).split())
            parsed = {
                "n_units": _num(r["# Units"]),
                "unit_years": _num(r["Unit-Years"]),
                "FOR": _num(r["FOR"]),
                "EFOR": _num(r["EFOR"]),
                "EFORd": _num(r["EFORd"]),
            }
            if parsed["EFORd"] is None:
                continue  # suppressed row — not a citable table value
            rows[label] = parsed
    return rows


def _lookup_eford(rows: dict, size_label: str) -> tuple[float, str]:
    """EFORd (%) for a size class: Gas Primary, else Oil/Gas, else All Sizes."""
    for cat in ("FOSSIL Gas Primary", "FOSSIL Oil/Gas Primary"):
        key = f"{cat} {size_label}"
        if key in rows:
            return rows[key]["EFORd"], key
    key = "FOSSIL Gas Primary All Sizes"
    return rows[key]["EFORd"], key + " (size row suppressed fallback)"


def _campd_zero_coverage(plant_codes: set[int]) -> dict:
    """Count-only re-verification: census plants in the committed extract."""
    with OUTAGE_EXTRACT.open() as fh:
        extract_ids = {int(row["facility_id"]) for row in csv.DictReader(fh)}
    covered = sorted(plant_codes & extract_ids)
    return {
        "extract": str(OUTAGE_EXTRACT.relative_to(REPO)),
        "census_plants_in_extract": covered,
        "n_covered": len(covered),
        "n_census_plants": len(plant_codes),
    }


def main() -> None:
    """Build the census, derive the capacity-weighted GADS EFORd, emit record."""
    cfg = _keeper_config()
    fleet = _stgas_fleet(cfg)
    codes = set(fleet)
    units = _census_units(codes)

    gads = {w: _gads_rows(w) for w in GADS_WINDOWS}
    gate_rows = gads[GADS_GATE_WINDOW]

    total_w = 0.0
    acc = 0.0
    per_unit = []
    for u in units:
        w = u["summer_mw"]
        label = _size_class(w)
        eford_pct, row_used = _lookup_eford(gate_rows, label)
        per_unit.append(
            {
                **u,
                "gads_size_class": label,
                "gads_row_used": row_used,
                "eford_pct": eford_pct,
            }
        )
        total_w += w
        acc += w * eford_pct
    weighted_pct = acc / total_w if total_w else float("nan")
    value = round(weighted_pct / 100.0, 4)

    context = {
        w: {
            k: v
            for k, v in gads[w].items()
            if k.startswith("FOSSIL Gas Primary")
            or k.startswith("FOSSIL Oil/Gas Primary All Sizes")
        }
        for w in GADS_WINDOWS
    }

    out = {
        "iso": ISO,
        "gatespec": "GATESPEC-caiso193-stgas-wefor-2026-08-11.md",
        "keeper_base": KEEPER.name,
        "fleet_path": "load_or_synthesize_bins + bins_to_fleet on the keeper "
        "config (caiso-187/193 construction; population == the LP's bins)",
        "st_gas_fleet_lp": {str(k): round(v, 1) for k, v in sorted(fleet.items())},
        "st_gas_fleet_total_mw": round(sum(fleet.values()), 1),
        "census_units": per_unit,
        "gads_corpus": {
            "gate_window": GADS_GATE_WINDOW,
            "gate_document": "NERC GADS Generating Unit Statistical Brochure 3 "
            "— 2020-2024 — Unit Reporting Events (public; corpus "
            "data/raw/reference/nerc-gads-eford-2020-2024/ with recorded "
            "retrieval + source URL)",
            "context_windows": context,
        },
        "derivation": {
            "metric": "EFORd",
            "weighting": "EIA-860 unit summer capacity (NMC analog) over "
            "GADS size-class rows",
            "weighted_eford_pct": round(weighted_pct, 4),
            "gas_st_wefor_base_override": value,
            "g_band": [0.03, 0.21],
            "in_band": 0.03 <= value <= 0.21,
        },
        "campd_zero_coverage_reverify": _campd_zero_coverage(codes),
        "incumbent": {
            "constants.THERMAL_AVAILABILITY['ST_GAS']": 0.21,
            "identification": "fitted to ERCOT once-through 1950s-60s steamers "
            "(matrix note; GATESPEC §1)",
        },
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
