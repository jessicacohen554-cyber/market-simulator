"""nyiso-203 — do the plants drawing D-4 unit-conduct FAIL rows qualify for the EXISTING,
already-armed `reliability_floor_plant_exclusions` channel?

ZERO LP. Source data ONLY (rule 23 `[R-FROZEN-DERIVE]`, rule 1 `[R-STRUCT]`): EPA CAMPD
unit-level hourly `grossLoad` and the committed bin assignments. No metrics file, no solve
output, no price/volume residual is opened.

WHY. The keeper `2026-09-06-nyiso-202-startup-aware` carries **six** D-4 unit-conduct FAIL rows
and its `D4.passed` reads False. Rule 20 `[R-FORCED-BUDGET]`'s escalation path for a class over
the C8 cap is a conditional pass on **(a) D-4 provenance + (b) D-1 shape**, so a C8 re-based to
unit grain (the UNRULED `docs/DECISION-CARD-nyiso193-d2-unit-grain-2026-09-05.md`) would fail
NYISO `ST_GAS` on leg (a) — the card predicted exactly this. Five of the six rows are trivial in
energy (<= 0.0028 TWh); the question this probe answers is whether they are *removable* through
the channel the owner has already adjudicated, rather than through new structure.

THE CRITERION is nyiso-140's, applied verbatim in FORM — *"median CF exactly 0.000 in every hour
block of every year"* — as a per-(year, block) zero-median census over the plant's own metered
conduct. It is reported alongside the pooled median and the online share so the reading does not
rest on the cell count alone; the decisive comparison is **a fortiori against Port Jefferson
2517**, the plant nyiso-140 excluded by owner ruling, since a plant that is *less* online than an
already-excluded one cannot be a closer call.

This probe DECIDES NOTHING and arms nothing: `reliability_floor_plant_exclusions` is already
armed on the keeper and carries exactly one entry (2517). Adding an entry is a new arm that owes
its own PREREG and rule-29 screen.

Reproduce: `uv run python scripts/probes/_nyiso203_d4_layup_census.py`.
Writes `results/calibration/_nyiso203_d4_layup_census.json`.
"""

from __future__ import annotations

import json

import pandas as pd

from market_sim.config.paths import RAW_DIR, REPO_ROOT

YEARS = (2023, 2024, 2025)
HOUR_BLOCKS = {
    "h00-05": range(0, 6),
    "h06-13": range(6, 14),
    "h14-21": range(14, 22),
    "h22-23": range(22, 24),
}
# Every plant drawing a D-4 unit-conduct FAIL row on the keeper's committed
# legitimacy_diagnostics.json, plus 2517 as the adjudicated reference point.
TARGETS = (2480, 8006, 8906, 54574, 2517)
REFERENCE = 2517  # excluded by nyiso-140 + owner ruling 2026-08-16
OUT = REPO_ROOT / "results" / "calibration" / "_nyiso203_d4_layup_census.json"


def main() -> None:
    """Census the D-4 failing plants and report which qualify a fortiori."""
    b = pd.read_csv(RAW_DIR / "_processed-legacy" / "bin_assignments_NYISO.csv")
    meta = {
        int(r.Plant_Code): (str(r.Plant_Name), str(r.Zone), str(r.Plant_Group))
        for r in b.itertuples()
    }
    frames = []
    for yr in YEARS:
        c = pd.read_parquet(RAW_DIR / "campd-unit-level" / f"NY_{yr}.parquet")
        c = c[c["facilityId"].astype(int).isin(TARGETS)].copy()
        c["code"] = c["facilityId"].astype(int)
        c["ts"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
        g = c.groupby(["code", "ts"])["grossLoad"].sum().reset_index()
        g["year"] = yr
        frames.append(g)
    df = pd.concat(frames, ignore_index=True)
    df["hour"] = df["ts"].dt.hour

    rec: dict = {"session": "nyiso-203", "years": list(YEARS), "plants": {}}
    rows = []
    for code in TARGETS:
        p = df[df["code"] == code]
        zero_cells = total_cells = 0
        for yr in YEARS:
            for hrs in HOUR_BLOCKS.values():
                s = p[(p["year"] == yr) & (p["hour"].isin(hrs))]["grossLoad"]
                total_cells += 1
                if len(s) == 0 or float(s.median()) <= 0.0:
                    zero_cells += 1
        name, zone, group = meta.get(code, ("?", "?", "?"))
        r = {
            "name": name,
            "zone": zone,
            "plant_group": group,
            "zero_cells": zero_cells,
            "total_cells": total_cells,
            "pooled_median_mw": float(p["grossLoad"].median()) if len(p) else 0.0,
            "online_share": float((p["grossLoad"] > 0).mean()) if len(p) else 0.0,
            "all_cells_zero": zero_cells == total_cells,
        }
        rec["plants"][str(code)] = r
        rows.append((code, r))

    ref = rec["plants"][str(REFERENCE)]
    for code, r in rows:
        r["qualifies_a_fortiori"] = bool(
            code != REFERENCE
            and r["all_cells_zero"]
            and r["online_share"] < ref["online_share"]
        )
    rec["reference"] = {
        "plant": REFERENCE,
        "note": (
            "Port Jefferson 2517 — the ONLY entry the exclusion channel currently carries, "
            "excluded by nyiso-140 + owner ruling 2026-08-16. A plant with every cell at a zero "
            "median AND a lower online share than 2517 cannot be a closer call than the "
            "adjudicated case."
        ),
        "online_share": ref["online_share"],
    }
    OUT.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")

    print(
        "=== nyiso-203 — D-4 failing plants vs the adjudicated lay-up criterion (ZERO LP) ===\n"
    )
    print(
        f"  {'plant':<34}{'zone':<16}{'class':<12}{'zero cells':>12}"
        f"{'median MW':>11}{'online':>8}   verdict"
    )
    for code, r in rows:
        v = (
            "REFERENCE (already excluded)"
            if code == REFERENCE
            else "QUALIFIES a fortiori"
            if r["qualifies_a_fortiori"]
            else "does NOT qualify"
        )
        print(
            f"  {r['name'][:31] + ' ' + str(code):<34}{r['zone']:<16}{r['plant_group']:<12}"
            f"{str(r['zero_cells']) + '/' + str(r['total_cells']):>12}"
            f"{r['pooled_median_mw']:>11.1f}{r['online_share']:>8.3f}   {v}"
        )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
