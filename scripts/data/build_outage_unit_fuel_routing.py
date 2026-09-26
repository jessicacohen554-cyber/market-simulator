"""Build the ``-unitfuel-`` companion of an ISO's ``-memberrepair-`` CAMPD outage extract.

PJM-NEXT-3 card 2 (rule 14 [R-ACCURATE]). The standard deriver tags every
window at a facility with ONE ``plant_group`` per year (its facility-level
class). That is correct wherever a plant's steam units burn one fuel, and wrong
at a plant mid-conversion whose units burn DIFFERENT fuels in the same year:
the fleet then carries one LP slice per fuel (one per generator), but every
unit's window lands on whichever slice the facility tag names. Measured at
Montour (3149, PJM): EIA-860 vintages 2023 and 2024 list generator 1 as
Conventional Steam Coal (BIT) and generator 2 as Natural Gas Steam Turbine
(NG), 752 MW each, while the extract tags both units ``COAL`` in 2023 and
``ST_GAS`` in 2024 -- so in 2024 the coal slice runs fully available through
unit 1's 253 outage days (PRECOMMIT-pjm-next-2-card2 §1: 4.53 TWh modelled vs
0.42 TWh actual on the coal slice).

The companion routes each such window to its OWN unit's class:

    companion = the ``-memberrepair-`` extract, row-for-row, with ONLY the
                ``plant_group`` of a row re-tagged when (a) the row is a steam
                row (``COAL`` / ``ST_GAS``), (b) its facility's operable steam
                generators split across both classes in the EIA-860 vintage of
                the row's own calendar year, and (c) the row's unit id matches
                one of those generators.

Rows are never added, dropped, moved or resized; a row whose unit id matches no
generator keeps its tag (fail-open, reported). The vintage is the one the
backcast fleet reads for that year (``paths.resolve_backcast_eia860_vintage``
under ``eia860_vintage_tracks_solve_year``: ``vintage_<year>/`` when committed,
else the canonical snapshot). Zero free parameters: a categorical re-tag read
from a published per-generator field. A separate file, never an overwrite
(rule 23).

Usage::

    python3 scripts/data/build_outage_unit_fuel_routing.py --iso PJM
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

#: EIA-860 ``Energy Source 1`` codes that make a steam generator a coal unit
#: (EIA-860 instructions, Table 28 "Energy source codes": solid coal fuels).
COAL_ENERGY_SOURCES = frozenset({"BIT", "SUB", "LIG", "ANT", "RC", "WC", "SGC"})
#: Gas codes whose steam generator is the fleet's ST_GAS class (same table).
GAS_ENERGY_SOURCES = frozenset({"NG", "OG", "BFG"})
#: The two extract tags a steam window can carry (artifact tokens).
STEAM_TAGS = ("COAL", "ST_GAS")


def _gen_frame(year: int) -> pd.DataFrame:
    """Return the operable-generator sheet the backcast fleet reads for ``year``."""
    from market_sim.config import paths

    vdir = paths.EIA_860_DIR / f"vintage_{int(year)}"
    base = vdir if vdir.is_dir() else paths.EIA_860_DIR
    return pd.read_parquet(base / "eia860_generator_operable.parquet")


def steam_unit_classes(year: int) -> dict[int, dict[str, str]]:
    """Return ``{plant_code: {gen_id: 'COAL'|'ST_GAS'}}`` for MIXED-steam plants.

    Only plants whose steam (prime mover ``ST``) generators resolve to BOTH
    classes in ``year``'s vintage are returned -- everywhere else the facility
    tag is already each unit's class and nothing is re-tagged.
    """
    g = _gen_frame(year)
    g = g[g["Prime Mover"].astype(str).str.strip() == "ST"]
    out: dict[int, dict[str, str]] = {}
    for code, grp in g.groupby(pd.to_numeric(g["Plant Code"], errors="coerce")):
        cls: dict[str, str] = {}
        for gid, es1 in zip(grp["Generator ID"], grp["Energy Source 1"]):
            es1 = str(es1).strip().upper()
            if es1 in COAL_ENERGY_SOURCES:
                cls[str(gid).strip().upper()] = "COAL"
            elif es1 in GAS_ENERGY_SOURCES:
                cls[str(gid).strip().upper()] = "ST_GAS"
        if len(set(cls.values())) > 1:
            out[int(code)] = cls
    return out


def build_companion(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ``(companion, retag_log)`` -- see the module docstring."""
    comp = base.copy()
    start_year = pd.to_datetime(comp["outage_start"]).dt.year
    end_year = pd.to_datetime(comp["outage_end"]).dt.year
    if (start_year != end_year).any():
        raise SystemExit(
            "rows span a calendar year; the per-year vintage lookup needs "
            "year-clipped windows"
        )
    log = []
    cache: dict[int, dict[int, dict[str, str]]] = {}
    for i, r in comp.iterrows():
        if str(r["plant_group"]) not in STEAM_TAGS:
            continue
        y = int(start_year.iloc[i])
        if y not in cache:
            cache[y] = steam_unit_classes(y)
        mixed = cache[y]
        plant = mixed.get(int(r["facility_id"]))
        if plant is None:
            continue
        cls = plant.get(str(r["unit_id"]).strip().upper())
        if cls is None:
            log.append(
                (
                    int(r["facility_id"]),
                    str(r["unit_id"]),
                    y,
                    r["plant_group"],
                    "UNMATCHED",
                )
            )
            continue
        if cls != r["plant_group"]:
            log.append(
                (int(r["facility_id"]), str(r["unit_id"]), y, r["plant_group"], cls)
            )
            comp.at[i, "plant_group"] = cls
    return comp, pd.DataFrame(
        log, columns=["facility_id", "unit_id", "year", "from_tag", "to_tag"]
    )


def main() -> None:
    """CLI entry point."""
    from market_sim.data.outages import unit_outage_csv_for_iso

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    base_path = unit_outage_csv_for_iso(args.iso, membership_repair=True)
    if "memberrepair" not in base_path.name:
        raise SystemExit(
            f"{args.iso}: no -memberrepair- extract to build on ({base_path})"
        )
    out = args.out or base_path.with_name(
        f"campd-unit-outages-memberrepair-unitfuel-{args.iso.upper()}.csv"
    )
    base = pd.read_csv(base_path, dtype={"unit_id": str})
    comp, log = build_companion(base)
    comp.to_csv(out, index=False)
    print(f"{out}: {len(comp)} rows ({len(base)} in {base_path.name}); re-tagged rows:")
    print(
        log.groupby(["facility_id", "year", "unit_id", "from_tag", "to_tag"])
        .size()
        .to_string()
        if len(log)
        else "  none"
    )


if __name__ == "__main__":
    main()
