"""Derive the commitment bridge's laid-up plant exclusions from CAMPD conduct.

The MEMBERSHIP correction for the NYISO gas commitment bridge
(``ScenarioConfig.nyiso_gas_bridge_plant_exclusions``), the bridge's analogue
of the reliability floor's ``exclude_plant_codes``
(``config.iso_configs.apply_reliability_floor_plant_exclusions``).

THE DEFECT. ``nyiso_gas_commitment_bridge`` holds a merchant slow-start gas
plant at minimum stable load across an idle gap its own physics says it cannot
economically cycle through. That is a statement about a plant that is IN the
day-ahead commitment population. A plant in economic LAY-UP is not: it is idle
in its own metered conduct while reading ~100 % available in the outage extract,
because lay-up is correctly not booked as a forced outage. Bridging it holds a
mothballed boiler at min load across gaps it never operated in — rule 17
``[R-FLOOR-WINDOW]``'s *"a floor binding in hours its own driver evidence says
the class is offline is a bug by definition"*.

The exclusion channel existed only on the reliability floor, so the SAME plants
were still floored by the OTHER mechanism (nyiso-140 fixed one mechanism, not
the plant). This artifact is the bridge's own identification of the same
physical fact — rule 19 ``[R-ONE-MECH]``'s "enumerate what already floors the
same class", one mechanism later.

THE TEST, and why it is this one. A plant is in economic lay-up when its own
meter says it produced NOTHING in the typical hour of every part of every
year::

    median(grossLoad | plant, year, 4-hour block) == 0   for ALL 18 cells
                                                          (6 blocks x 3 years)

This is the nyiso-140 criterion verbatim — *"median CF exactly 0.000 in every
hour block of every year"* — and the per-cell quantifier is what makes it a
lay-up test rather than a low-capacity-factor test. **A pooled median is not
enough**: measured on NYISO's own bridge population, a single pooled median of
zero also captures ordinary CYCLERS (Saranac, P(on) = 0.426; Port Jefferson,
P(on) = 0.375) — plants that genuinely start, run and stop, which is exactly
the population a commitment bridge exists to hold together. Requiring every
block of every year to be zero separates them cleanly: the qualifying set stops
at 18/18 and the nearest non-qualifier sits at 16/18.

WHAT IT DELIBERATELY DOES NOT DO. It is not fitted to the mechanism's own
failures. The test reads only the meter, so it is computed without reference to
which plants the bridge floors or to any D-4 verdict — and that independence is
what makes the agreement evidence: on the nyiso-143 keeper the test selects 7
of the bridge's 8 D-4 unit-conduct FAILURES without being shown any of them.
The eighth (plant 7314, D-4 FAIL, 77.1 % of its floored hours metered at zero)
does NOT qualify, and is deliberately LEFT IN: it is a cycler the model's own
P0 over-runs, so its forcing is an offer/economics defect and excluding it here
would bury that error inside a membership list instead of fixing it (rule 14
``[R-ACCURATE]``, rule 1 ``[R-STRUCT]``).

Output: ``data/raw/_processed-legacy/campd_bridge_layup_exclusions_{ISO}.csv``
— one row per qualifying plant, plus the full population with its cell counts
under ``--detail`` so a reader can see the separation rather than take it on
trust.

Governance (CLAUDE.md rules 13 ``[R-MEASURED]`` / 23 ``[R-FROZEN-DERIVE]``):
a measured unit-conduct property in the same admissibility class as the CAMPD
min-stable loads, committed shares and run lengths. Rule 13 — could this
quantity be produced for a forward year from forward drivers, and would it
respond to changed conditions? Yes: it regenerates from the CAMPD pipeline for
any vintage and a plant returning to service leaves the set on its own meter.
It reads no price and no volume residual, and re-derives ONLY when its source
data updates.

THREE MECHANISMS, ONE CENSUS (miso-170). Lay-up is a property of the SITE, so
the same census now serves every mechanism that floors a laid-up plant, each
through its own gate: the NYISO commitment bridge
(``nyiso_gas_bridge_plant_exclusions``, reading this artifact directly), the
per-plant must-run floors (``mustrun_plant_exclusions``, likewise), and the
reliability floor (``reliability_floor_plant_exclusions``, which consumes its
membership through the coefficient CSV's ``exclude_plant_codes`` column —
written from this same census by ``--patch-reliability-coeffs``, so the two can
never drift apart). Nothing about the TEST is per-mechanism; keeping it that way
is what stops a membership list from becoming a place to bury a dispatch error.

Usage::

    python scripts/data/derive_campd_bridge_layup_exclusions.py --iso NYISO
    python scripts/data/derive_campd_bridge_layup_exclusions.py --iso NYISO --detail
    python scripts/data/derive_campd_bridge_layup_exclusions.py --iso MISO \
        --detail --patch-reliability-coeffs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

# Model plant groups the gas commitment bridge can floor — the merchant
# slow-start gas fleet. Cogens (*_CHP) follow their steam host and are never
# bridged; the fast-start CT classes fail the bridge's own min-down physics
# gate. Mirrors derive_campd_gas_commitment_params.TARGET_CLASSES, which
# identifies the LEVEL this artifact corrects the MEMBERSHIP of.
TARGET_CLASSES: tuple[str, ...] = ("CC_REGULAR", "ST_GAS")

# CAMPD vintages pooled. 2023-2025 = the calibration span; 2022 and H1-2026 are
# the designated holdouts (CLAUDE.md rule 22), excluded by construction.
POOLED_VINTAGES: tuple[int, ...] = (2023, 2024, 2025)

# Width of the diurnal blocks the per-cell median is taken over. Four hours
# gives six blocks a day: coarse enough that each cell holds ~500 hours a year
# (a median over that many hours is not a small-sample artifact), fine enough
# that a plant running only its own peak window still shows a positive cell.
BLOCK_HOURS: int = 4

# Robust maximum-sustained-load percentile, for the reported capacity factor
# and the online share only — the qualifying test itself reads raw MW medians
# and needs no capability basis at all. Frozen convention of the sibling
# derivations.
_HSL_PCTILE: float = 99.5
_ONLINE_FRAC: float = 0.05


def population(iso: str) -> dict[int, tuple[str, str, float]]:
    """Return ``{plant_code: (plant_group, zone, pmax_mw)}`` for the bridge set.

    The bridge's own eligible population: model rows in
    :data:`TARGET_CLASSES`, keyed by EIA plant code because a CAMPD facility
    carries no model class. A plant whose rows span both target classes is
    kept once under the class holding more capacity — the test is a
    PLANT-level conduct statement (is this site laid up?), so it needs no
    per-class split and no ambiguity drop.

    Args:
        iso: The ISO name.
    """
    by_code: dict[int, dict[str, float]] = {}
    zones: dict[int, str] = {}
    for gen in load_fleet_from_csv(iso, get_iso_config(iso)):
        group = getattr(gen, "plant_group", None) or ""
        if group not in TARGET_CLASSES:
            continue
        code = int(gen.plant_code or 0)
        if not code:
            continue
        by_code.setdefault(code, {})
        by_code[code][group] = by_code[code].get(group, 0.0) + float(gen.pmax_mw)
        zones[code] = gen.zone
    return {
        code: (max(groups, key=groups.get), zones[code], sum(groups.values()))
        for code, groups in by_code.items()
    }


def plant_series(iso: str, years: tuple[int, ...], codes: set[int]) -> pd.DataFrame:
    """Return the pooled hourly PLANT gross-load series for *codes*.

    Units are summed to one plant series per hour before any statistic is
    taken, because lay-up is a property of the SITE: a two-unit station with
    one unit mothballed is not laid up, and a per-unit test would call it so.

    Args:
        iso: The ISO name.
        years: CAMPD vintages to pool.
        codes: EIA plant codes to keep.
    """
    frames: list[pd.DataFrame] = []
    for state in states_for_iso(iso):
        for year in years:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                print(f"  (skip {path.name}: not on disk)")
                continue
            df = pd.read_parquet(
                path,
                columns=[
                    "facilityId",
                    "facilityName",
                    "date",
                    "hour",
                    "grossLoad",
                ],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            if df.empty:
                continue
            plant = df.groupby(
                ["facilityId", "facilityName", "date", "hour"], as_index=False
            )["grossLoad"].sum()
            plant["year"] = year
            frames.append(plant)
    if not frames:
        raise SystemExit(f"{iso}: no CAMPD hours found for the bridge population")
    return pd.concat(frames, ignore_index=True)


def layup_table(
    series: pd.DataFrame, pop: dict[int, tuple[str, str, float]]
) -> pd.DataFrame:
    """Return one row per population plant with its lay-up cell counts.

    ``cells_zero == cells`` is the qualifying condition: the plant's median
    output is zero in EVERY (year, diurnal block) cell.

    Args:
        series: Pooled plant-hour frame from :func:`plant_series`.
        pop: Population map from :func:`population`.
    """
    series = series.copy()
    series["block"] = (series["hour"] // BLOCK_HOURS).astype(int)
    rows: list[dict] = []
    for code, grp in series.groupby("facilityId"):
        code = int(code)
        plant_group, zone, pmax = pop[code]
        load = grp["grossLoad"].to_numpy(dtype=float)
        hsl = float(np.percentile(load, _HSL_PCTILE))
        cell_median = grp.groupby(["year", "block"])["grossLoad"].median()
        cells = int(cell_median.size)
        cells_zero = int((cell_median <= 0.0).sum())
        rows.append(
            {
                "plant_code": code,
                "plant_name": str(grp["facilityName"].iloc[0]),
                "plant_group": plant_group,
                "zone": zone,
                "model_pmax_mw": round(pmax, 3),
                "observed_hsl_mw": round(hsl, 3),
                "cells": cells,
                "cells_zero": cells_zero,
                "pooled_median_mw": round(float(np.median(load)), 3),
                "online_share": round(
                    float((load >= max(_ONLINE_MW, _ONLINE_FRAC * hsl)).mean()), 4
                ),
                "laid_up": bool(cells_zero == cells and cells > 0),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["laid_up", "cells_zero", "plant_code"], ascending=[False, False, True]
    )


def patch_reliability_coeffs(iso: str, excluded: pd.DataFrame) -> None:
    """Write the lay-up census into the ISO's reliability-floor coefficient CSV.

    The reliability floor consumes its membership correction through the
    coefficient CSV's optional ``exclude_plant_codes`` column
    (``config.iso_configs.apply_reliability_floor_plant_exclusions``, armed by
    ``ScenarioConfig.reliability_floor_plant_exclusions``), not through this
    artifact. That column was hand-populated at nyiso-140 for a single plant;
    doing the same by hand for a 15-plant census would leave the ISO's
    identification unreproducible and would be silently wiped by the next
    ``derive_reliability_coeffs.py`` run. This step makes it mechanical instead:
    each limb receives exactly the laid-up plants that carry its own ``zone``
    and ``plant_class``, so the census and the column can never drift apart.

    Rewrites in place, preserving every other column and row order. Plants
    already listed on a limb are kept (union), so a hand-identified exclusion
    from an earlier session is never dropped. A limb with no laid-up plant of
    its (zone, class) gets an empty cell — and the whole column stays inert
    until a run arms the flag, so this is byte-identical for every existing run.

    Args:
        iso: The ISO name.
        excluded: The qualifying rows written to the lay-up artifact.
    """
    path = REPO / "data" / "raw" / "reference" / f"reliability_floor_coeffs_{iso}.csv"
    if not path.exists():
        print(f"  (skip reliability-coeff patch: {path.name} not on disk)")
        return
    by_zone_class: dict[tuple[str, str], set[int]] = {}
    for _, r in excluded.iterrows():
        by_zone_class.setdefault((str(r.zone), str(r.plant_group)), set()).add(
            int(r.plant_code)
        )
    coeffs = pd.read_csv(path, dtype=str).fillna("")
    if "exclude_plant_codes" not in coeffs.columns:
        coeffs["exclude_plant_codes"] = ""
    new_col: list[str] = []
    touched = 0
    for _, row in coeffs.iterrows():
        prior = {
            int(code)
            for code in str(row["exclude_plant_codes"]).replace(",", ";").split(";")
            if code.strip()
        }
        codes = prior | by_zone_class.get(
            (str(row["zone"]), str(row["plant_class"])), set()
        )
        new_col.append(";".join(str(c) for c in sorted(codes)))
        touched += 1 if codes else 0
    coeffs["exclude_plant_codes"] = new_col
    coeffs.to_csv(path, index=False)
    print(
        f"  patched {path.name}: {touched} of {len(coeffs)} limb(s) now carry an "
        f"exclude_plant_codes list (inert unless "
        f"ScenarioConfig.reliability_floor_plant_exclusions is armed)"
    )


def main() -> None:
    """CLI entry point: derive and write one ISO's lay-up exclusion artifact."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--iso", default="NYISO", help="ISO name (default NYISO)")
    ap.add_argument(
        "--years",
        type=int,
        nargs="*",
        default=list(POOLED_VINTAGES),
        help="CAMPD vintages to pool (default 2023 2024 2025)",
    )
    ap.add_argument(
        "--detail",
        action="store_true",
        help="also write the full population with its cell counts",
    )
    ap.add_argument(
        "--patch-reliability-coeffs",
        action="store_true",
        help=(
            "also write the census into data/raw/reference/"
            "reliability_floor_coeffs_<ISO>.csv's exclude_plant_codes column "
            "(the reliability floor's own consumption seam; inert unless "
            "ScenarioConfig.reliability_floor_plant_exclusions is armed)"
        ),
    )
    args = ap.parse_args()
    iso = args.iso.upper()
    years = tuple(int(y) for y in args.years)

    pop = population(iso)
    if not pop:
        raise SystemExit(f"{iso}: model fleet has no {TARGET_CLASSES} plants")
    print(f"{iso}: {len(pop)} bridge-population plant(s)")
    table = layup_table(plant_series(iso, years, set(pop)), pop)
    table.insert(0, "iso", iso)
    table["years"] = "-".join(str(y) for y in years)
    table["source"] = (
        "EPA CAMPD unit-level hourly grossLoad (data/raw/campd-unit-level), "
        "units summed to one PLANT series; laid_up iff median(grossLoad) == 0 "
        f"in every (year, {BLOCK_HOURS}h block) cell over the pooled window"
    )

    excluded = table[table["laid_up"]]
    print(
        f"  {len(excluded)} laid-up plant(s) of {len(table)} with CAMPD "
        f"coverage; nearest non-qualifier at "
        f"{int(table[~table['laid_up']]['cells_zero'].max())}/"
        f"{int(table['cells'].max())} zero cells"
    )
    for _, r in excluded.iterrows():
        print(
            f"    {r.plant_code:>6} {r.plant_name[:32]:32s} {r.plant_group:11s} "
            f"{r.zone:14s} {r.model_pmax_mw:8.1f} MW  P(on)={r.online_share:.3f}"
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / f"campd_bridge_layup_exclusions_{iso}.csv"
    excluded.to_csv(out, index=False)
    print(f"wrote {out}")
    if args.detail:
        out_all = PROCESSED_DIR / f"campd_bridge_layup_exclusions_{iso}_population.csv"
        table.to_csv(out_all, index=False)
        print(f"wrote {out_all}")
    if args.patch_reliability_coeffs:
        patch_reliability_coeffs(iso, excluded)


if __name__ == "__main__":
    main()
