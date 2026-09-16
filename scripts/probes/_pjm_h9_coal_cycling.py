"""pjm-h9 — does the model's PJM coal CYCLE in a way a >16 h min-run fleet cannot? ZERO LP.

Rule 29 ``[R-SCREEN]`` clause 0, rule 32 ``[R-SHARD]`` (a): the parent runs no LP. Every
number comes from **committed** ``hourly/class_band_hourly_<year>.parquet`` sidecars — the
keeper's own, and pjm-h8's arm bundle — so this replays nothing (the pjm-h8 method note:
"the keeper's committed hourly/ sidecars answer most questions with no solve").

WHY. ``RESULT-pjm-h8`` §5 leaves two readings of the 12.70 TWh coal shortfall. Route **(a)** is
that the model lacks a commitment mechanism PJM's coal has: the measured ``LONG_RUN`` segment's
own definition is median ``min_runtime`` **> 16 h**, and PJM is the only large ISO in this repo
with **no** P1-native commitment bridge (CAISO ``caiso_ra_mustoffer``, ERCOT
``ercot_gas_commitment_bridge``, NYISO ``nyiso_gas_commitment_bridge`` each have one).

Rule 19 ``[R-ONE-MECH]``'s D-2 attribution already closed the floor escape (96 % of PJM coal is
economic dispatch), so the question is not "is a floor missing" but **"can the model's coal do
something a real coal unit physically cannot?"** This probe measures that directly and
band-by-band, with no reference to any residual (rule 1 ``[R-STRUCT]``):

* **hours at zero** and **0 <-> on transitions** per band — a class-aggregate that drops to
  zero and returns is unambiguous, whatever the per-unit mix underneath;
* the **run-length distribution** of the aggregate's on-blocks, against the 16 h the segment's
  own physics definition implies;
* the **hour-to-hour swing** |dMW/dt| as a share of the band's own capacity — how fast the
  model moves a block of plant whose real counterparts need many hours to start and stop.

STATED LIMIT, not buried. These are CLASS-BAND AGGREGATES, not units. An aggregate that never
reaches zero does **not** prove no unit cycled — units can offset each other. So the measure is
**one-sided**: cycling found here is real; cycling not found here is not excluded. The per-unit
version needs ``dispatch/<year>_P1.parquet``, which the keeper does not commit (repo-wide
gitignore) and which would cost a replay. That is named as the cost of the sharper measurement,
not silently skipped.

THE PER-PLANT LEG lifts that limit wherever a bundle commits ``dispatch/<year>_P1.parquet``
(pjm-h8's arm does; the keeper does not). There a PLANT is off when the sum of ALL its bands is
zero, which IS decommitment, and the run-length distribution is directly comparable to the
segment's own ``min_runtime`` definition.

WHAT THE CODE ALREADY SAYS, verified rather than inferred. The LP is pure (CLAUDE.md: "Pure LP
— no MIP"), so there is **no minimum-run or minimum-down constraint anywhere in it**;
commitment is carried entirely by ``min_gen`` floors and the P1-native bridges in
``pipeline/commitment.py``, each of which is ISO-gated:

    caiso_ra_mustoffer -> CAISO   ercot_gas_commitment_bridge / ercot_ruc_commitment_floor ->
    ERCOT   nyiso_gas_commitment_bridge -> NYISO   spp_gas_commitment_bridge -> SPP
    miso_coal_night_floor -> MISO

**FIVE ISOs carry one and PJM carries none** — PJM's only entry in that module is
``energy_reserve_coopt``, which is not a commitment mechanism. So nothing in the model bounds
how fast PJM coal may start and stop, and what this probe measures is how much of that freedom
a given run actually uses. (Rule 25 ``[R-ISO-SCOPE]``: MISO's coal floor is named to show a
coal commitment mechanism is an established object here, NOT as a transfer — a PJM mechanism
would derive its own parameters from PJM's own data, and pjm-142's killed overnight GAS bridge
adjudicates nothing about a coal one.)

This probe adjudicates NOTHING and proposes NOTHING (rule 21 ``[R-DOF]``). It is evidence for a
successor charter, which is the owner's to open.

Run: ``python3 scripts/probes/_pjm_h9_coal_cycling.py --arm <bundle-dir>``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results/calibration/_pjm_h9_coal_cycling.json"

#: The LONG_RUN model classes (offer_surfaces._PJM_MIDCURVE_SEGMENT_OF), i.e. exactly
#: the fleet whose measured segment is defined by median min_runtime > 16 h.
LONG_RUN_CLASSES = ("COAL_BIT", "COAL_PRB", "COAL", "ST_GAS")
#: On/off threshold as a share of the band's own annual maximum. A band is "off"
#: when it is below this; 1 % is a rounding guard, not a tunable.
OFF_FRAC = 0.01


def profile(mw: np.ndarray, cap: float) -> dict:
    """On/off, run-length and swing statistics for one (class, band) hourly series."""
    on = mw > OFF_FRAC * cap if cap > 0 else np.zeros_like(mw, dtype=bool)
    flips = int(np.count_nonzero(np.diff(on.astype(np.int8)) != 0))
    # on-block run lengths
    runs, cur = [], 0
    for v in on:
        if v:
            cur += 1
        elif cur:
            runs.append(cur)
            cur = 0
    if cur:
        runs.append(cur)
    d = np.abs(np.diff(mw))
    return {
        "annual_max_mw": round(float(cap), 1),
        "twh": round(float(mw.sum()) / 1e6, 4),
        "hours_off": int(np.count_nonzero(~on)),
        "on_off_transitions": flips,
        "n_on_blocks": len(runs),
        "on_block_hours_median": float(np.median(runs)) if runs else None,
        "on_blocks_under_16h": int(np.count_nonzero(np.asarray(runs) < 16))
        if runs
        else 0,
        "swing_p99_mw_per_h": round(float(np.percentile(d, 99)), 1) if d.size else None,
        "swing_p99_pct_of_max": round(float(np.percentile(d, 99) / cap * 100), 2)
        if d.size and cap > 0
        else None,
        "hours_swing_over_10pct": int(np.count_nonzero(d > 0.10 * cap))
        if cap > 0
        else 0,
    }


def leg(path: Path, year: int) -> dict:
    df = pd.read_parquet(path)
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    out: dict = {}
    for (k, b), sub in df[df["klass"].isin(LONG_RUN_CLASSES)].groupby(
        ["klass", "band"]
    ):
        if not str(b):
            continue
        mw = sub.sort_values("hour")["mw"].to_numpy(float)
        out.setdefault(str(k), {})[str(b)] = profile(mw, float(mw.max()))
    return out


#: Coal classes as they appear in the dispatch layer's ``klass`` column.
DISPATCH_COAL = ["COAL_BIT", "COAL_PRB", "COAL_WC"]
#: PJM's measured LONG_RUN segment is defined by median min_runtime > 16 h
#: (derive_pjm_offer_midcurve.py, CC_MAX_MIN_RUNTIME_H) — the bar an on-block is
#: read against. The 8 h min-down comparator is the loosest coal min-down in the
#: fleet's own physics; neither is a tunable, both come from published physics.
MIN_RUN_H = 16
MIN_DOWN_H = 8


def per_plant(path: Path, year: int) -> dict:
    """Per-PLANT on/off behaviour from a committed dispatch layer.

    A plant is OFF when the sum of EVERY one of its bands is zero, so unlike the
    class-band aggregate this IS decommitment and can be read against the fleet's
    own ``min_runtime``.
    """
    import pyarrow.parquet as pq

    t = pq.read_table(
        path,
        columns=["unit_id", "klass", "hour", "mw"],
        filters=[("klass", "in", DISPATCH_COAL)],
    )
    d = t.to_pandas()
    del t
    d["plant"] = d["unit_id"].str.rpartition("_")[0]
    g = d.groupby(["plant", "hour"], observed=True)["mw"].sum().unstack(fill_value=0.0)
    cap = g.max(axis=1).to_numpy()
    on = g.to_numpy() > OFF_FRAC * cap[:, None]
    plants = []
    for i, name in enumerate(g.index):
        o = on[i]
        if not o.any():
            continue
        runs, offs, cur, curo = [], [], 0, 0
        for v in o:
            if v:
                cur += 1
                if curo:
                    offs.append(curo)
                    curo = 0
            else:
                curo += 1
                if cur:
                    runs.append(cur)
                    cur = 0
        if cur:
            runs.append(cur)
        if curo:
            offs.append(curo)
        ra, oa = np.asarray(runs), np.asarray(offs)
        plants.append(
            {
                "plant": str(name),
                "max_mw": round(float(cap[i]), 1),
                "twh": round(float(g.to_numpy()[i].sum()) / 1e6, 4),
                "hours_off": int(np.count_nonzero(~o)),
                "starts": int(len(runs) - (1 if o[0] else 0)),
                "on_blocks_under_min_run": int(np.count_nonzero(ra < MIN_RUN_H)),
                "off_blocks_under_min_down": int(np.count_nonzero(oa < MIN_DOWN_H))
                if oa.size
                else 0,
                "on_block_hours_median": float(np.median(ra)) if ra.size else None,
            }
        )
    tot = {
        "n_plants": len(plants),
        "n_never_off": sum(1 for p in plants if p["hours_off"] == 0),
        "n_cycling": sum(1 for p in plants if p["hours_off"] > 0),
        "total_starts": sum(p["starts"] for p in plants),
        "total_on_blocks_under_min_run": sum(
            p["on_blocks_under_min_run"] for p in plants
        ),
        "total_off_blocks_under_min_down": sum(
            p["off_blocks_under_min_down"] for p in plants
        ),
        "min_run_h": MIN_RUN_H,
        "min_down_h": MIN_DOWN_H,
    }
    return {"totals": tot, "plants": sorted(plants, key=lambda r: -r["max_mw"])}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument(
        "--keeper",
        default="results/calibration/pjm_d4_4_A",
        help="the designated keeper's committed bundle (the control, G-CTRL form 4)",
    )
    ap.add_argument(
        "--arm", default=None, help="optional second bundle to difference against"
    )
    args = ap.parse_args(argv)

    legs = {"keeper": REPO / args.keeper}
    if args.arm:
        legs["arm"] = REPO / args.arm
    out: dict = {
        "what": (
            "on/off, run-length and swing statistics for PJM's LONG_RUN classes from "
            "COMMITTED class_band_hourly sidecars; evidence for RESULT-pjm-h8 §5 route (a)"
        ),
        "limit": (
            "CLASS-BAND AGGREGATES, not units: cycling found is real, cycling not found "
            "is NOT excluded (units can offset). The per-unit version needs dispatch/."
        ),
        "off_threshold_frac_of_annual_max": OFF_FRAC,
        "year": args.year,
        "legs": {},
    }
    for name, d in legs.items():
        p = d / "hourly" / f"class_band_hourly_{args.year}.parquet"
        if not p.exists():
            print(f"[{name}] MISSING {p} — skipped")
            continue
        out["legs"][name] = leg(p, args.year)
        disp = d / "dispatch" / f"{args.year}_P1.parquet"
        if disp.exists():
            out.setdefault("per_plant", {})[name] = per_plant(disp, args.year)
        print(f"\n=== {name}  ({d.name}) ===")
        for k in sorted(out["legs"][name]):
            print(f"  -- {k} --")
            hdr = (
                f"   {'band':<10}{'TWh':>8}{'maxMW':>9}{'hrs_off':>9}"
                f"{'flips':>7}{'blocks':>8}{'med_len':>9}{'<16h':>6}{'swing99%':>10}"
            )
            print(hdr)
            for b, r in sorted(out["legs"][name][k].items()):
                print(
                    f"   {b:<10}{r['twh']:>8.3f}{r['annual_max_mw']:>9.0f}"
                    f"{r['hours_off']:>9}{r['on_off_transitions']:>7}"
                    f"{r['n_on_blocks']:>8}"
                    f"{(r['on_block_hours_median'] if r['on_block_hours_median'] else 0):>9.0f}"
                    f"{r['on_blocks_under_16h']:>6}"
                    f"{(r['swing_p99_pct_of_max'] if r['swing_p99_pct_of_max'] else 0):>10.2f}"
                )
    for name, pp in out.get("per_plant", {}).items():
        t = pp["totals"]
        print(
            f"\n=== PER-PLANT ({name}) — decommitment, not band back-down ===\n"
            f"   plants dispatching        {t['n_plants']}\n"
            f"   never off / cycling       {t['n_never_off']} / {t['n_cycling']}\n"
            f"   total starts in the year  {t['total_starts']}\n"
            f"   on-blocks  < {t['min_run_h']} h        {t['total_on_blocks_under_min_run']}"
            f"   <- the segment's OWN min_runtime bar\n"
            f"   off-blocks < {t['min_down_h']} h         "
            f"{t['total_off_blocks_under_min_down']}"
        )
        print(
            f"   {'plant':<28}{'maxMW':>9}{'hrs_off':>9}{'starts':>8}"
            f"{'on<16h':>8}{'off<8h':>8}"
        )
        for r in pp["plants"][:12]:
            print(
                f"   {r['plant']:<28}{r['max_mw']:>9.0f}{r['hours_off']:>9}"
                f"{r['starts']:>8}{r['on_blocks_under_min_run']:>8}"
                f"{r['off_blocks_under_min_down']:>8}"
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
