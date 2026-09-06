"""nyiso-204b — the two measurements the merged nyiso-204 refusal does not carry: the NARROWED
fallback (2480 alone) and the lay-up census's own cell counts.

The parent refusal is `docs/FINDING-nyiso204-ch-layup-exclusion-2026-09-06.md` (merged, PR #5199)
— it refuses the 2480+8006 arm on two independent grounds and this probe does not re-litigate it.
What it adds is (a) `--exclude 2480`, the narrowed arm the next lane would otherwise spend a
session on, and (b) `--census`, which re-derives the 18/18 zero-cell lay-up statistic that the
whole a-fortiori reading rests on and shows it flags the limb's own backbone (2625 Bowline) while
missing the one plant the channel carries (2517). See
`docs/ADDENDUM-nyiso204b-ch-exclusion-increment-2026-09-06.md`.

What it measures, for any membership: what the Capital_Hudson ST_GAS exclusion would actually
do to the limb, before any LP is spent (rule 29 `[R-SCREEN]` step 0).

ZERO LP. Rebuilds the keeper bundle's fleet with ``fleet_only`` twice per year — once on the
committed membership (CONTROL) and once with ``2480`` + ``8006`` added to the limb's
``exclude_plant_codes`` (ARM) — and diffs the ``FleetArrays.min_gen`` the floor engine
produces. The floor injection runs BEFORE the ``fleet_only`` exit in
``scripts/run_calibration.py``, so the reconstructed ``min_gen`` is the floor the keeper's own
solve sees, composed with the commitment bridge exactly as the engine composes it.

WHY THE ARM IS NOT A MEMBERSHIP CORRECTION HERE. nyiso-140's adjudicated exclusion was on a
``pro_rata`` limb, where the floor is a PER-UNIT assertion (``frac`` x each unit's own
available capacity) and dropping a unit removes only that unit's floor, leaving the coefficient
and every other member untouched (its §3.2: 0.2666 re-derived vs 0.2620 frozen — "the
correction is membership-only and costs ~zero degrees of freedom"). The live Capital_Hudson
limb's ``distribution`` column is EMPTY, so it defaults to ``cheapest_first``
(``iso_configs.ReliabilityFloorSpec.distribution``): the limb sizes a ZONAL target as
``floor_pct`` x the SELECTED fleet's available capacity and fills it cheapest-first. Dropping a
plant therefore shrinks the TARGET as well as the fill order — a change in the limb's
commitment LEVEL, not its membership. This probe measures that.

Reported per year: the zonal target under both memberships in the hours the limb binds, and
the per-plant forced energy, binding hours and peak floor under both.

Diagnostic only. Arms nothing, edits nothing, registers nothing — the arm membership is
injected in-process by patching ``RELIABILITY_FLOOR_REGISTRY`` and the committed CSV is never
touched.

Reproduce: ``uv run python scripts/probes/_nyiso204_ch_exclusion_phase0.py``.
Writes ``results/calibration/_nyiso204_ch_exclusion_phase0.json``.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

BUNDLE = ROOT / "results" / "calibration" / "nyiso202_startup_aware"
KEEPER_ID = "2026-09-06-nyiso-202-startup-aware"
ISO = "NYISO"
ZONE = "Capital_Hudson"
KLASS = "ST_GAS"
DRIVER = "tmax"
THRESHOLD_C = 31.1
FLOOR_PCT = 0.0973
YEARS = (2023, 2024, 2025)
CANDIDATES: tuple[int, ...] = (2480, 8006)
OUT = ROOT / "results" / "calibration" / "_nyiso204_ch_exclusion_phase0.json"


def _patch_membership(arm: bool) -> None:
    """Set the live CH ST_GAS step limb's ``exclude_plant_codes`` in the registry."""
    from market_sim.config import iso_configs

    specs = iso_configs.RELIABILITY_FLOOR_REGISTRY[ISO]
    for i, s in enumerate(specs):
        if (
            s.zone == ZONE
            and s.plant_class == KLASS
            and s.driver == DRIVER
            and abs(s.threshold - THRESHOLD_C) < 1e-9
            and not s.ramp_group
        ):
            specs[i] = dataclasses.replace(
                s,
                exclude_plant_codes=(frozenset(CANDIDATES) if arm else frozenset()),
            )
            return
    raise SystemExit("live CH ST_GAS tmax step limb not found in the registry")


def _slice(year: int) -> dict:
    """Reconstruct one year and return the CH ST_GAS floor slice."""
    from market_sim.config.iso_configs import get_iso_config

    state, meta = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
    fa = state["fleet_arrays"]
    zone_names = [z.name for z in get_iso_config(meta["iso"]).zones]
    z_idx = zone_names.index(ZONE)
    sel = (
        (np.asarray(fa.plant_group) == KLASS) & (fa.zone_idx == z_idx) & (fa.pmax > 0.0)
    )
    rows = np.flatnonzero(sel)
    mg = (
        fa.min_gen
        if fa.min_gen is not None
        else np.broadcast_to(fa.pmin[:, None], (fa.pmin.size, fa.availability.shape[1]))
    )
    return {
        "plant_code": np.asarray(fa.plant_code)[rows],
        "pmax": fa.pmax[rows],
        "pmin": fa.pmin[rows],
        "availability": fa.availability[rows, :],
        "forced": np.maximum(np.asarray(mg)[rows, :] - fa.pmin[rows, None], 0.0),
    }


def run_census() -> None:
    """Re-derive the bridge lay-up artifact's 18-cell statistic for CH ST_GAS + 2517.

    The a-fortiori reading the arm rested on ranks plants by ANNUAL online share. This
    re-derives the stricter per-cell criterion the adjudicated bridge channel actually uses
    (``derive_campd_bridge_layup_exclusions.BLOCK_HOURS = 4``: ``median(grossLoad) == 0`` in
    every (year, 4 h block) cell, 6 blocks x 3 years) and reports it beside each plant's
    conduct, so the reader can see the criterion flag the limb's own backbone.
    """
    import pandas as pd

    from market_sim.config.paths import RAW_DIR

    targets = (2517, 2625, 8006, 2480)
    frames = []
    for year in YEARS:
        c = pd.read_parquet(RAW_DIR / "campd-unit-level" / f"NY_{year}.parquet")
        c = c[c["facilityId"].astype(int).isin(targets)].copy()
        c["code"] = c["facilityId"].astype(int)
        c["ts"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
        g = c.groupby(["code", "ts"])["grossLoad"].sum().reset_index()
        g["year"] = year
        frames.append(g)
    df = pd.concat(frames, ignore_index=True)
    df["block"] = (df["ts"].dt.hour // 4).astype(int)

    rec: dict = {
        "session": "nyiso-204b",
        "status": "ZERO LP — CAMPD conduct only",
        "criterion": (
            "derive_campd_bridge_layup_exclusions: median(grossLoad) == 0 in EVERY "
            "(year, 4h block) cell; BLOCK_HOURS=4 -> 6 blocks x 3 years = 18 cells"
        ),
        "plants": {},
    }
    for code in targets:
        q = df[df["code"] == code]
        cells = q.groupby(["year", "block"])["grossLoad"].median()
        rec["plants"][str(code)] = {
            "zero_cells": int((cells <= 0).sum()),
            "total_cells": int(len(cells)),
            "annual_online_share": float((q["grossLoad"] > 0).mean())
            if len(q)
            else 0.0,
            "qualifies_laid_up": bool(int((cells <= 0).sum()) == int(len(cells))),
        }
    out = OUT.with_name("_nyiso204b_layup_census_cells.json")
    out.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
    print("=== nyiso-204b — the lay-up census's own cell counts (ZERO LP) ===\n")
    print(f"  {'plant':>8}{'zero cells':>13}{'annual online':>16}{'laid up?':>11}")
    for code, v in rec["plants"].items():
        print(
            f"  {code:>8}{str(v['zero_cells']) + '/' + str(v['total_cells']):>13}"
            f"{v['annual_online_share']:>16.4f}"
            f"{('YES' if v['qualifies_laid_up'] else 'no'):>11}"
        )
    print(f"\nwrote {out}")


def main() -> None:
    """Measure the arm's footprint on the limb, control vs arm, with no LP."""
    global CANDIDATES, OUT
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--exclude",
        default="2480,8006",
        help="comma-separated plant codes for the arm membership (default: the "
        "handoff's 2480,8006; pass 2480 for the narrowed fallback variant)",
    )
    ap.add_argument(
        "--census",
        action="store_true",
        help="instead of the footprint, re-derive the bridge lay-up artifact's own "
        "18-cell zero-median statistic for the CH ST_GAS fleet plus the adjudicated "
        "reference 2517, and write _nyiso204b_layup_census_cells.json",
    )
    args = ap.parse_args()
    if args.census:
        run_census()
        return
    CANDIDATES = tuple(int(c) for c in args.exclude.split(",") if c.strip())
    if CANDIDATES != (2480, 8006):
        OUT = OUT.with_name(
            f"_nyiso204_ch_exclusion_phase0_{'-'.join(str(c) for c in CANDIDATES)}.json"
        )

    rec: dict = {
        "session": "nyiso-204",
        "status": "ZERO LP — two fleet_only reconstructions per year, no solve",
        "keeper": KEEPER_ID,
        "limb": {
            "zone": ZONE,
            "plant_class": KLASS,
            "driver": DRIVER,
            "threshold_c": THRESHOLD_C,
            "floor_pct": FLOOR_PCT,
            "distribution": "cheapest_first (CSV column empty -> dataclass default)",
        },
        "arm": {"exclude_plant_codes": list(CANDIDATES)},
        "years": {},
    }

    for year in YEARS:
        _patch_membership(arm=False)
        c = _slice(year)
        _patch_membership(arm=True)
        a = _slice(year)
        _patch_membership(arm=False)

        pc = c["plant_code"]
        assert (pc == a["plant_code"]).all(), "fleet row order moved between arms"
        keep = ~np.isin(pc, CANDIDATES)
        avail = c["pmax"][:, None] * c["availability"]
        tgt_c = FLOOR_PCT * avail.sum(axis=0)
        tgt_a = FLOOR_PCT * avail[keep].sum(axis=0)
        bind = c["forced"].sum(axis=0) > 1e-9

        plants: dict = {}
        for p in sorted(set(int(x) for x in pc)):
            m = pc == p
            plants[str(p)] = {
                "is_candidate": p in CANDIDATES,
                "ctrl_forced_twh": float(c["forced"][m].sum() / 1e6),
                "arm_forced_twh": float(a["forced"][m].sum() / 1e6),
                "delta_twh": float((a["forced"][m].sum() - c["forced"][m].sum()) / 1e6),
                "ctrl_binding_hours": int((c["forced"][m] > 1e-9).any(axis=0).sum()),
                "arm_binding_hours": int((a["forced"][m] > 1e-9).any(axis=0).sum()),
                "ctrl_peak_floor_mw": float(c["forced"][m].sum(axis=0).max()),
                "arm_peak_floor_mw": float(a["forced"][m].sum(axis=0).max()),
            }
        tot_c = float(c["forced"].sum() / 1e6)
        tot_a = float(a["forced"].sum() / 1e6)
        delta = tot_a - tot_c
        off_noncand = sum(
            v["delta_twh"] for v in plants.values() if not v["is_candidate"]
        )
        rec["years"][str(year)] = {
            "binding_hours": int(bind.sum()),
            "zonal_target_ctrl_mean_mw": float(tgt_c[bind].mean())
            if bind.any()
            else 0.0,
            "zonal_target_arm_mean_mw": float(tgt_a[bind].mean())
            if bind.any()
            else 0.0,
            "zonal_target_shrink_pct": (
                float(100.0 * (1.0 - tgt_a[bind].mean() / tgt_c[bind].mean()))
                if bind.any()
                else 0.0
            ),
            "total_ctrl_forced_twh": tot_c,
            "total_arm_forced_twh": tot_a,
            "total_delta_twh": delta,
            "share_of_delta_taken_off_non_candidates_pct": (
                float(100.0 * off_noncand / delta) if delta else 0.0
            ),
            "plants": plants,
        }

    OUT.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")

    print(
        "=== nyiso-204 phase 0 — the CH ST_GAS exclusion arm's footprint (ZERO LP) ===\n"
    )
    for year in YEARS:
        y = rec["years"][str(year)]
        print(
            f"-- {year}: limb binds {y['binding_hours']} h; zonal target "
            f"{y['zonal_target_ctrl_mean_mw']:.1f} -> {y['zonal_target_arm_mean_mw']:.1f} MW "
            f"({y['zonal_target_shrink_pct']:.1f}% SHRINK)"
        )
        print(
            f"   {'plant':>8}{'ctrl TWh':>12}{'arm TWh':>11}{'delta':>11}"
            f"{'ctrl h':>9}{'arm h':>8}{'ctrl peak MW':>15}{'arm peak MW':>14}"
        )
        for p, v in y["plants"].items():
            tag = " *cand" if v["is_candidate"] else ""
            print(
                f"   {p:>8}{v['ctrl_forced_twh']:>12.5f}{v['arm_forced_twh']:>11.5f}"
                f"{v['delta_twh']:>11.5f}{v['ctrl_binding_hours']:>9}"
                f"{v['arm_binding_hours']:>8}{v['ctrl_peak_floor_mw']:>15.1f}"
                f"{v['arm_peak_floor_mw']:>14.1f}{tag}"
            )
        print(
            f"   TOTAL {y['total_ctrl_forced_twh']:.5f} -> {y['total_arm_forced_twh']:.5f} TWh "
            f"(delta {y['total_delta_twh']:.5f}); "
            f"{y['share_of_delta_taken_off_non_candidates_pct']:.1f}% of the removal comes off "
            f"NON-candidate plants\n"
        )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
