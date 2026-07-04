"""Derive the v2 per-plant CO2-rate artifact from ``emissions-unit-annual``.

The v2 artifact (``data/raw/_processed-legacy/plant_emission_rates_v2.parquet``)
is keyed ``(iso, plant_id, unit_id, year)`` with **per-year rows only** — no
baked pooled ``year == 0`` row (the forward estimator pools at consumption time;
see ``docs/handoffs/emissions-co2-rate-plan-2026-07.md`` §2/§4) and **no
quarantined 2022/H1-2026 rows** (CLAUDE.md rule 22). Unit grain is the whole
point: it dissolves the old mixed coal/gas facility exclusion — a plant that
retires a unit (or a Parish-style coal+gas facility) gets a forward rate from the
surviving/matching units via the estimator's composition mask.

Net conversion follows the existing parasitic factors
(``compute_parasitic_factors`` / ``parasitic_load_factors.parquet``): station
service is a plant-level quantity, so each unit inherits its plant's factor and
``net_mwh_unit = gross_mwh_unit × factor``. For years the parasitic file does not
cover yet (2018-2021), extend it first with EIA-923 those years
(``scripts/derive_parasitic_load.py``); missing factors fall back to the plant's
pooled factor, then 1.0.

Columns: iso, plant_id, unit_id, year, primary_fuel, unit_type, gross_mwh,
net_mwh, parasitic_factor, heat_mmbtu, co2_kg, co2_kg_per_mwh_net, co2_source,
starts, op_hours.

Usage:
    python scripts/derive_plant_emissions_v2.py                 # all ISOs, all years
    python scripts/derive_plant_emissions_v2.py --iso ERCOT --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config import paths  # noqa: E402
from market_sim.data import campd  # noqa: E402
from scripts.lib import clean_io  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_plant_emissions_v2")

QUARANTINED_YEARS = frozenset({2022, 2026})
PROCESSED_DIR = paths.RAW_DATA_DIR / "_processed-legacy"
PARASITIC_PATH = PROCESSED_DIR / "parasitic_load_factors.parquet"
OUT_PATH = PROCESSED_DIR / "plant_emission_rates_v2.parquet"
CSV_PATH = PROCESSED_DIR / "plant_emission_rates_v2.csv"

ALL_ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

_OUT_COLUMNS = [
    "iso",
    "plant_id",
    "unit_id",
    "year",
    "primary_fuel",
    "unit_type",
    "gross_mwh",
    "net_mwh",
    "parasitic_factor",
    "heat_mmbtu",
    "co2_kg",
    "co2_kg_per_mwh_net",
    "co2_source",
    "starts",
    "op_hours",
]


def _parasitic_maps() -> tuple[dict[tuple[int, int], float], dict[int, float]]:
    """Return ``({(plant,year): factor}, {plant: pooled_factor})``."""
    if not PARASITIC_PATH.exists():
        logger.warning(
            "no parasitic factors at %s; using 1.0 (gross==net)", PARASITIC_PATH
        )
        return {}, {}
    df = pd.read_parquet(PARASITIC_PATH)
    per = {
        (int(r.plant_id), int(r.year)): float(r.parasitic_factor)
        for r in df[df["year"] != 0].itertuples(index=False)
    }
    return per, campd.pooled_factor_map(df)


def _state_to_isos() -> dict[str, list[str]]:
    """Return ``{state: [iso, ...]}`` from campd.ISO_STATES (states overlap ISOs)."""
    out: dict[str, list[str]] = {}
    for iso in ALL_ISOS:
        for st in campd.states_for_iso(iso):
            out.setdefault(st, []).append(iso)
    return out


def derive(years: list[int], isos: list[str]) -> pd.DataFrame:
    """Build the v2 artifact frame for ``years`` × ``isos`` from the annual data."""
    per_paras, pooled_paras = _parasitic_maps()
    state_isos = _state_to_isos()
    want_states = {st for iso in isos for st in campd.states_for_iso(iso)}

    frames = []
    for year in years:
        if year in QUARANTINED_YEARS:
            logger.warning("skipping quarantined year %d (rule 22)", year)
            continue
        if not clean_io.clean_exists("emissions-unit-annual", year=year):
            logger.warning(
                "no emissions-unit-annual for %d; curate it first "
                "(scripts/curate_emissions_unit_annual.py)",
                year,
            )
            continue
        a = clean_io.read_clean("emissions-unit-annual", year=year, validate=False)
        a = a[a["state"].astype(str).isin(want_states)].copy()
        frames.append(a)
    if not frames:
        return pd.DataFrame(columns=_OUT_COLUMNS)
    annual = pd.concat(frames, ignore_index=True)

    def _factor(plant_id: int, year: int) -> float:
        return per_paras.get(
            (int(plant_id), int(year)), pooled_paras.get(int(plant_id), 1.0)
        )

    annual["parasitic_factor"] = [
        _factor(p, y) for p, y in zip(annual["plant_id"], annual["year"])
    ]
    annual["net_mwh"] = annual["gross_mwh"].astype(float) * annual["parasitic_factor"]
    annual["co2_kg_per_mwh_net"] = [
        (float(c) / float(n)) if n > 0 else 0.0
        for c, n in zip(annual["co2_kg"], annual["net_mwh"])
    ]

    # Fan out to one row per (iso, plant_id, unit_id, year): a plant in a state
    # shared by two ISOs appears under both; downstream each ISO's fleet build
    # filters to its own plant codes.
    rows = []
    for r in annual.itertuples(index=False):
        for iso in state_isos.get(str(r.state), []):
            if iso not in isos:
                continue
            rows.append(
                {
                    "iso": iso,
                    "plant_id": int(r.plant_id),
                    "unit_id": str(r.unit_id),
                    "year": int(r.year),
                    "primary_fuel": str(r.primary_fuel),
                    "unit_type": str(r.unit_type),
                    "gross_mwh": round(float(r.gross_mwh), 3),
                    "net_mwh": round(float(r.net_mwh), 3),
                    "parasitic_factor": round(float(r.parasitic_factor), 6),
                    "heat_mmbtu": round(float(r.heat_mmbtu), 3),
                    "co2_kg": round(float(r.co2_kg), 3),
                    "co2_kg_per_mwh_net": round(float(r.co2_kg_per_mwh_net), 6),
                    "co2_source": str(r.co2_source),
                    "starts": int(r.starts),
                    "op_hours": int(r.op_hours),
                }
            )
    out = pd.DataFrame(rows, columns=_OUT_COLUMNS)
    return out.sort_values(["iso", "plant_id", "unit_id", "year"]).reset_index(
        drop=True
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="+", default=list(ALL_ISOS))
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args(argv)

    bad = [y for y in args.years if y in QUARANTINED_YEARS]
    if bad:
        ap.error(f"quarantined years cannot enter the artifact: {bad} (rule 22)")

    out = derive(args.years, [i.upper() for i in args.iso])
    if out.empty:
        logger.error("no rows derived — curate emissions-unit-annual first")
        return 1
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PATH, index=False)
    out.to_csv(CSV_PATH, index=False)
    logger.info(
        "wrote %s: %d rows, %d plants, ISOs %s, years %s",
        OUT_PATH,
        len(out),
        out["plant_id"].nunique(),
        sorted(out["iso"].unique()),
        sorted(out["year"].unique()),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
