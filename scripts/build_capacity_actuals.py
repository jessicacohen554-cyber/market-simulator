#!/usr/bin/env python
"""Build the capacity-hindcast scoring target from the latest EIA-860 release.

Emits ``data/raw/_validation-source/capacity_actuals_<iso>.csv`` — every
generator **retirement** and **addition** an ISO saw in 2021-2025, in the
model's own fuel taxonomy — from the LATEST committed EIA-860 snapshot
(operable + retired-and-canceled sheets). These are *outcome registry facts*
(COD and retirement dates), the admissible scoring target for
``scripts/score_capacity_hindcast.py`` (plan §1.2.3).

Rule 22: the window is 2021-2025. 2022 rows are registry dates on real units
(EIA-860 already carries them in the current release), not the quarantined
2022 *bench* domain — they are retained so cumulative scoring is complete, and
the scorer flags any timing metric that lands on the 2022 bridge. No 2026 rows
are ever emitted.

Usage::

    python scripts/build_capacity_actuals.py --iso ERCOT
    python scripts/build_capacity_actuals.py --iso PJM
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from market_sim.data.fleet import BA_CODE_TO_ISO, _map_fuel_type  # noqa: E402

WINDOW = range(2021, 2026)  # 2021-2025 inclusive; never 2026 (rule 22).
LARGE_UNIT_MW = 300.0  # flagged per plan §1.2.3

EIA_860_DIR = Path("data/raw/eia-860")
OUT_DIR = Path("data/raw/_validation-source")
# Lives in OUT_DIR, not EIA_860_DIR: data/raw/eia-860/*.csv is gitignored
# (override-CSV convention, source of truth there is parquet/json only), and
# this file is a committed, citation-backed permanent fix, not a local
# override -- see OUT_DIR/README.md's "RD-5 actuals-coverage fix" note.
RETIRED_SHEET_GAP_FIX = OUT_DIR / "retired_sheet_coverage_gaps.csv"


def _iso_to_ba(iso: str) -> set[str]:
    """Return the EIA balancing-authority codes that map to ``iso``."""
    return {ba for ba, i in BA_CODE_TO_ISO.items() if i == iso}


def _renewable_or_storage_fuel(technology: object, prime_mover: object) -> str | None:
    """Classify the non-thermal resources ``_map_fuel_type`` returns None for."""
    tech = str(technology or "").strip().lower()
    mover = str(prime_mover or "").strip().upper()
    if "onshore wind" in tech or "offshore wind" in tech or mover == "WT":
        return "wind"
    if "solar" in tech or "photovoltaic" in tech or mover == "PV":
        return "solar"
    if "batter" in tech or mover in {"BA", "ES"} or "energy storage" in tech:
        return "storage"
    if "pumped" in tech or mover == "PS":
        return "storage"
    if "hydro" in tech or mover in {"HY", "HC"}:
        return "hydro"
    if "geothermal" in tech:
        return "geothermal"
    return None


def _fuel(technology: object, energy_source: object, prime_mover: object) -> str:
    """Model fuel/tech class, thermal first then renewable/storage."""
    thermal = _map_fuel_type(technology, energy_source, prime_mover)
    if thermal is not None:
        return thermal
    return _renewable_or_storage_fuel(technology, prime_mover) or "other"


def _uid(plant_code: int, generator_id: object) -> str:
    """``<plant>_<generator>`` id with the CSV comment char stripped.

    Some EIA generator IDs contain ``#`` (e.g. NYISO plant 63625 unit ``HJD#1``).
    Both this file's provenance header and the scorer's ``load_actuals`` read the
    CSV with ``pandas comment="#"``, which truncates *any* line at the first
    ``#`` — mangling such a row into an all-NaN entry. Replacing ``#`` with ``-``
    keeps the id readable and the CSV parseable; no existing committed actuals
    row carries ``#``, so ERCOT/PJM/MISO are byte-unchanged.
    """
    return f"{plant_code}_{str(generator_id).replace('#', '-')}"


def _plant_ba() -> pd.Series:
    """Return a Plant Code → Balancing Authority Code map from the plant sheet."""
    plant = pd.read_parquet(EIA_860_DIR / "eia860_plant.parquet")
    plant = plant[pd.to_numeric(plant["Plant Code"], errors="coerce").notna()]
    return plant.drop_duplicates("Plant Code").set_index(
        plant["Plant Code"].astype(float).astype(int)
    )["Balancing Authority Code"]


def build_additions(bas: set[str]) -> pd.DataFrame:
    """Additions: operable units whose COD (Operating Year) is in the window."""
    gens = pd.read_parquet(EIA_860_DIR / "eia860_generators.parquet")
    gens = gens[gens["balancing_authority_code"].isin(bas)].copy()
    gens["operating_year"] = pd.to_numeric(gens["operating_year"], errors="coerce")
    gens = gens[gens["operating_year"].isin(list(WINDOW))]
    rows = []
    for _, g in gens.iterrows():
        rows.append(
            {
                "kind": "addition",
                "unit_id": _uid(int(g["plant_id"]), g["generator_id"]),
                "plant_id": int(g["plant_id"]),
                "fuel": _fuel(g["technology"], g["energy_source"], g["prime_mover"]),
                "mw": float(g["nameplate_capacity_mw"] or 0.0),
                "year": int(g["operating_year"]),
                "state": g.get("state", ""),
            }
        )
    return pd.DataFrame(rows)


def load_retired_sheet_gap_fix(bas: set[str]) -> pd.DataFrame:
    """Retirement rows for plants the CURRENT top-level retired sheet omits.

    RD-5 (forecast-retirement-calibration-plan-2026-07.md §5): the committed
    ``eia860_generator_retired_and_canceled.parquet`` "2025 Early Release"
    snapshot has fully dropped some plants that genuinely retired inside the
    scoring window (Indian Point 3) or un-retired since (Palisades' 2025
    restart moved it back to the operable sheet, erasing its 2022 retirement
    row from the current snapshot). :data:`RETIRED_SHEET_GAP_FIX` carries
    those rows verbatim from this repo's own earlier EIA-860 vintage
    snapshots (still the authoritative EIA-860 survey, just read at the
    vintage where the plant was still in that release's retired sheet) with
    an explicit ``ba_code`` column, since the missing plant(s) may also be
    absent from the current plant sheet and so cannot resolve a BA via
    :func:`_plant_ba`. Returns an empty frame if the fix file is absent.
    """
    if not RETIRED_SHEET_GAP_FIX.is_file():
        return pd.DataFrame()
    gap = pd.read_csv(RETIRED_SHEET_GAP_FIX, comment="#")
    gap = gap[gap["ba_code"].isin(bas)]
    gap = gap[pd.to_numeric(gap["retirement_year"], errors="coerce").isin(list(WINDOW))]
    rows = []
    for _, g in gap.iterrows():
        rows.append(
            {
                "kind": "retirement",
                "unit_id": _uid(int(g["plant_code"]), g["generator_id"]),
                "plant_id": int(g["plant_code"]),
                "fuel": _fuel(g["technology"], g["energy_source_1"], g["prime_mover"]),
                "mw": float(g["nameplate_capacity_mw"] or 0.0),
                "year": int(g["retirement_year"]),
                "state": g.get("state", ""),
            }
        )
    return pd.DataFrame(rows)


def build_retirements(bas: set[str]) -> pd.DataFrame:
    """Retirements: retired-sheet units whose Retirement Year is in the window.

    Unions in :func:`load_retired_sheet_gap_fix` so plants the current
    top-level snapshot has dropped (RD-5) still score (see that function's
    docstring); both sources flow through the same fuel/window logic.
    """
    ret = pd.read_parquet(EIA_860_DIR / "eia860_generator_retired_and_canceled.parquet")
    ret = ret[pd.to_numeric(ret["Plant Code"], errors="coerce").notna()].copy()
    ret["Plant Code"] = ret["Plant Code"].astype(float).astype(int)
    ba_map = _plant_ba()
    ret["ba"] = ret["Plant Code"].map(ba_map)
    ret = ret[ret["ba"].isin(bas)]
    ret["Retirement Year"] = pd.to_numeric(ret["Retirement Year"], errors="coerce")
    ret = ret[ret["Retirement Year"].isin(list(WINDOW))]
    rows = []
    for _, g in ret.iterrows():
        rows.append(
            {
                "kind": "retirement",
                "unit_id": _uid(int(g["Plant Code"]), g["Generator ID"]),
                "plant_id": int(g["Plant Code"]),
                "fuel": _fuel(
                    g["Technology"], g.get("Energy Source 1"), g["Prime Mover"]
                ),
                "mw": float(g["Nameplate Capacity (MW)"] or 0.0),
                "year": int(g["Retirement Year"]),
                "state": g.get("State", ""),
            }
        )
    df = pd.DataFrame(rows)
    gap_fix = load_retired_sheet_gap_fix(bas)
    if not gap_fix.empty:
        existing = set(zip(df["plant_id"], df["unit_id"])) if not df.empty else set()
        gap_fix = gap_fix[
            ~gap_fix.apply(lambda r: (r["plant_id"], r["unit_id"]) in existing, axis=1)
        ]
        df = pd.concat([df, gap_fix], ignore_index=True)
    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO, e.g. ERCOT or PJM.")
    args = parser.parse_args(argv)
    iso = args.iso.upper()
    bas = _iso_to_ba(iso)
    if not bas:
        raise SystemExit(f"no EIA balancing authority maps to ISO {iso!r}")

    adds = build_additions(bas)
    rets = build_retirements(bas)
    both = pd.concat([rets, adds], ignore_index=True)
    both["large_unit"] = both["mw"] >= LARGE_UNIT_MW
    both = both.sort_values(
        ["kind", "year", "fuel", "mw"], ascending=[True, True, True, False]
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"capacity_actuals_{iso.lower()}.csv"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    gap_fix_note = ""
    gap_fix_rows = load_retired_sheet_gap_fix(bas)
    if not gap_fix_rows.empty:
        plants = sorted(gap_fix_rows["plant_id"].unique().tolist())
        gap_fix_note = (
            f"# RD-5 actuals-coverage fix applied: plant(s) {plants} unioned in from "
            f"{RETIRED_SHEET_GAP_FIX} (missing from the current top-level retired "
            f"sheet) -- see that file's header and data/raw/eia-860/README.md.\n"
        )
    header = (
        f"# capacity_actuals_{iso.lower()}.csv — capacity-hindcast scoring target "
        f"(W2-P5, plan §1.2.3)\n"
        f"# Source: latest committed EIA-860 (data/raw/eia-860/ operable + "
        f"retired_and_canceled sheets); registry outcome facts, not bench.\n"
        f"# Window 2021-2025 (rule 22: no 2026). Fuel in the model taxonomy "
        f"(data.fleet._map_fuel_type + renewable/storage). Built {stamp}.\n"
        f"# Units >= {LARGE_UNIT_MW:.0f} MW flagged (large_unit). "
        f"BA(s): {sorted(bas)}.\n"
        f"{gap_fix_note}"
    )
    with open(out, "w") as fh:
        fh.write(header)
        both.to_csv(fh, index=False)

    r = rets["mw"].sum() / 1000.0 if not rets.empty else 0.0
    a = adds["mw"].sum() / 1000.0 if not adds.empty else 0.0
    print(
        f"{iso}: {len(rets)} retirements ({r:.1f} GW), {len(adds)} additions ({a:.1f} GW)"
    )
    print(f"  wrote {out}")
    for kind, df in (("retired", rets), ("added", adds)):
        if not df.empty:
            by_fuel = df.groupby("fuel")["mw"].sum().div(1000).round(2).to_dict()
            print(f"  {kind} GW by fuel: {by_fuel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
