"""Derive the CHP fleet's economic-lay-up census from CAMPD conduct.

The MEMBERSHIP identification for ``ScenarioConfig.chp_layup_duty_split``
(nyiso-148) — the cogeneration analogue of the bridge/floor lay-up census
(``derive_campd_bridge_layup_exclusions.py``), which is scoped by design to
the commitment bridge's ``(CC_REGULAR, ST_GAS)`` population because *"cogens
(*_CHP) follow their steam host and are never bridged"*.

THE DEFECT. nyiso-147 restored the NYISO CHP fleet's measured grid capacity
(``nyiso_chp_btm_measured``, the Gold-Book/EIA-923 per-plant share replacing
the residual-identified 35 % sector carve) and PROVED the 2023 upstate price
object with it — while exposing what the carve had been masking. Selkirk
(10725), a semi-mothballed 754-MW cogen metered at 92 GWh in 2024, dispatches
**730 GWh (7.9x)** once its capacity is restored. There is **no floor
involved**: D-2 books CHP forcing at 0.38 % of CC_CHP energy and the CHP
classes are D-2-exempt, so the phantom energy is *economic*, where D-2 and
D-4 do not look. Capacity truth without conduct truth manufactures energy.

THE TEST, and why it is this one. The nyiso-140/144 criterion **verbatim** —
a plant is in economic lay-up when its own meter says it produced NOTHING in
the typical hour of every part of every year::

    median(grossLoad | plant, year, 4-hour block) == 0   for ALL 18 cells
                                                          (6 blocks x 3 years)

The per-cell quantifier is what makes it a lay-up test rather than a
low-capacity-factor test; a pooled median of zero also catches ordinary
cyclers. Measured on the NYISO CHP population the separation reproduces the
bridge census's shape: qualifiers stop at 18/18 and the nearest non-qualifier
sits at 13/18 (Indeck-Corinth 50458, on-share 0.457).

THE GUARD THE MEASUREMENT FORCED — a silent meter is not an idle plant.
Applied naively the criterion convicts three NYISO plants that are not idle
at all but **CAMPD-INVISIBLE**: RED-Rochester (10025), Ticonderoga Mill
(54099) and Cornell's Ithaca campus (50368) each carry an identically-zero
CAMPD series (p99.5 HSL = 0.0 MW, pooled gross 0.0 GWh, zero online hours)
while EIA-923 reports 949.5 / 576.3 / 439.1 GWh of net generation. Industrial
and campus cogens are frequently outside the CEMS gross-load population. The
census therefore **abstains where the meter is silent**: a plant whose CAMPD
series is degenerate carries no conduct evidence, so it receives no verdict
rather than a conviction. This is a DEGENERACY test (``hsl > 0``), not a
threshold, so it adds no free parameter (CLAUDE.md rule 21 ``[R-DOF]``).

WHAT IT DELIBERATELY DOES NOT DO. It is not fitted to any mechanism's
failures: the test reads only the meter, and is computed without reference to
which plants the LP over-runs, to any D-4 verdict, or to any price residual.
That independence is what makes agreement with those verdicts evidence rather
than circularity.

Output: ``data/raw/_processed-legacy/chp_layup_census_{ISO}.csv`` — one row
per qualifying plant, plus the full population with its cell counts and CAMPD
coverage under ``--detail``.

Governance (CLAUDE.md rules 13 ``[R-MEASURED]`` / 23 ``[R-FROZEN-DERIVE]``):
a measured unit-conduct property in the same admissibility class as the CAMPD
min-stable loads, committed shares and run lengths. Rule 13 — could this
quantity be produced for a forward year from forward drivers, and would it
respond to changed conditions? Yes: it regenerates from the CAMPD pipeline
for any vintage and a plant returning to service leaves the set on its own
meter. It reads no price and no volume residual, and re-derives ONLY when its
source data updates.

Usage::

    python scripts/data/derive_campd_chp_layup_census.py --iso NYISO
    python scripts/data/derive_campd_chp_layup_census.py --iso NYISO --detail
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

# The cogeneration model plant groups — the population the bridge census
# excludes by design. Membership is a PLANT-level (site) statement, so a
# station spanning several CHP classes is tested once, whole.
TARGET_CLASSES: tuple[str, ...] = ("CC_CHP", "CT_CHP", "ST_CHP")

# CAMPD vintages pooled. 2023-2025 = the calibration span; 2022 and H1-2026
# are the designated holdouts (CLAUDE.md rule 22), excluded by construction.
POOLED_VINTAGES: tuple[int, ...] = (2023, 2024, 2025)

# Width of the diurnal blocks the per-cell median is taken over — the
# nyiso-140/144 convention, six blocks a day.
BLOCK_HOURS: int = 4

# Robust maximum-sustained-load percentile. Frozen convention of the sibling
# derivations; here it also carries the DEGENERACY guard (hsl > 0), which is
# the only thing separating an idle plant from a plant CAMPD cannot see.
_HSL_PCTILE: float = 99.5
_ONLINE_FRAC: float = 0.05


def population(iso: str) -> dict[int, tuple[str, str, float]]:
    """Return ``{plant_code: (plant_group, zone, pmax_mw)}`` for the CHP set.

    Keyed by EIA plant code because a CAMPD facility carries no model class. A
    plant whose rows span several CHP classes is kept once under the class
    holding more capacity — the test is a PLANT-level conduct statement, so it
    needs no per-class split and no ambiguity drop.

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
    taken, because lay-up is a property of the SITE: a multi-train station
    with one train mothballed is not laid up, and a per-unit test would call
    it so.

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
                columns=["facilityId", "facilityName", "date", "hour", "grossLoad"],
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
        raise SystemExit(f"{iso}: no CAMPD hours found for the CHP population")
    return pd.concat(frames, ignore_index=True)


def census_table(
    series: pd.DataFrame, pop: dict[int, tuple[str, str, float]]
) -> pd.DataFrame:
    """Return one row per population plant with its lay-up verdict.

    ``cells_zero == cells`` is the qualifying condition; ``observed_hsl_mw >
    0`` is the degeneracy guard that makes the census ABSTAIN on a plant CAMPD
    cannot see (``verdict = "no-evidence"``) instead of convicting it.

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
        metered = bool(hsl > 0.0)
        laid_up = bool(metered and cells > 0 and cells_zero == cells)
        rows.append(
            {
                "iso": "",
                "plant_code": code,
                "plant_name": str(grp["facilityName"].iloc[0]),
                "plant_group": plant_group,
                "zone": zone,
                "model_pmax_mw": round(pmax, 3),
                "observed_hsl_mw": round(hsl, 3),
                "cells": cells,
                "cells_zero": cells_zero,
                "pooled_median_mw": round(float(np.median(load)), 3),
                "campd_gross_gwh": round(float(load.sum()) / 1000.0, 3),
                "online_share": round(
                    float((load >= max(_ONLINE_MW, _ONLINE_FRAC * hsl)).mean()), 4
                )
                if metered
                else 0.0,
                "laid_up": laid_up,
                "verdict": (
                    "laid-up"
                    if laid_up
                    else ("no-evidence" if not metered else "operating")
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["laid_up", "cells_zero", "plant_code"], ascending=[False, False, True]
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", default="NYISO")
    ap.add_argument(
        "--detail",
        action="store_true",
        help="also write the full population with its cell counts",
    )
    args = ap.parse_args()
    iso = args.iso.upper()

    pop = population(iso)
    print(f"{iso}: {len(pop)} CHP plant(s) in the model fleet")
    table = census_table(plant_series(iso, POOLED_VINTAGES, set(pop)), pop)
    table["iso"] = iso
    table["years"] = "-".join(str(y) for y in POOLED_VINTAGES)
    table["source"] = (
        "EPA CAMPD unit-level hourly grossLoad (data/raw/campd-unit-level), "
        "units summed to one PLANT series; laid_up iff median(grossLoad) == 0 "
        "in every (year, 4h block) cell over the pooled window AND the series "
        "is non-degenerate (p99.5 HSL > 0 — a plant CAMPD cannot see carries "
        "no conduct evidence and gets no verdict)"
    )

    qualifying = table[table["laid_up"]]
    out = PROCESSED_DIR / f"chp_layup_census_{iso}.csv"
    qualifying.to_csv(out, index=False)
    print(f"  wrote {out.relative_to(REPO)} — {len(qualifying)} laid-up plant(s)")
    if args.detail:
        det = out.with_name(f"chp_layup_census_{iso}_population.csv")
        table.to_csv(det, index=False)
        print(f"  wrote {det.relative_to(REPO)} — {len(table)} population row(s)")

    cols = [
        "plant_code",
        "plant_name",
        "plant_group",
        "zone",
        "model_pmax_mw",
        "observed_hsl_mw",
        "cells_zero",
        "online_share",
        "campd_gross_gwh",
        "verdict",
    ]
    with pd.option_context("display.width", 220, "display.max_rows", 60):
        print(table[cols].to_string(index=False))


if __name__ == "__main__":
    main()
