"""NYISO-NEXT-31 phase 0 (zero LP): which bridge leg puts the floor on meter-zero hours.

Open item 4 (the ``nyiso_gas_commitment_bridge`` D-4 unit-conduct rows). The bridge floor is
the union of legs written by ``model.commitment.caiso_ra_mustoffer_min_gen`` from the P0 run
pattern: (i) the min-run extension ``[e, s + min_run)``, (ii) the level (class min-load share),
(iii) the run detection that anchors every leg (startup-aware screen), plus the gap legs
(physical < min-down, economic <= DA horizon) and the online-hours state leg (state cohort only).

The keeper bundle carries the P1 floor (``floors/<y>_P1.npz``: ``min_gen`` + int8 ``mechanism``)
and P1 unit dispatch (``unit_hourly_<y>.parquet``), not the P0 run pattern. Each floored block
of a non-state-cohort plant is P0-OFF by construction (only ext and gap legs write there), so a
block is classified from its P1 neighbours, a labelled proxy for P0:

* ``gap`` — the hour after the block is a free (unfloored) P1 run hour and the anchor run plus
  the block exceed the class min-run (only a gap leg reaches that far);
* ``min_run`` — the block ends with the unit off, within min-run of the anchor run's start;
* ``min_run_or_gap`` — the block reaches the next run inside min-run (an extension that closes a
  gap; both legs would write it);
* ``unanchored`` — no free P1 run abuts the block start (P1 moved the run P0 detected).

For every binding hour (dispatch AT the bridge floor) it reads the CAMPD meter
(``frontend/data/backcast/bench/NYISO/<y>.json.gz``) and records: meter zero vs meter below the
floor (the level question), the measured off-stretch containing it, and whether the ANCHOR run
itself overlaps any measured-on hour (an anchor with none is a run the real unit never made —
a detection defect, not a min-run or level one).

Leg branches ``claude/nyisonext21-<y>`` are read from ``--legs-dir`` (``git archive`` of
``results/calibration/nyisonext21_<y>/{floors,hourly/unit_hourly_<y>.parquet}``).
Writes ``results/phase0/nyiso/_nyisonext31_bridge_d4_legs.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.floor_mechanisms import MECH_NYISO_GAS_COMMITMENT_BRIDGE
from market_sim.model.commitment import find_runs

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from legitimacy_diagnostics import (  # noqa: E402
    D2_FLOOR_MIN_MW,
    D2_REL_TOL,
    bench_plant_view,
    load_bench,
)

OUT = ROOT / "results/phase0/nyiso/_nyisonext31_bridge_d4_legs.json"
YEARS = (2021, 2022, 2023, 2024, 2025)
# Keeper recipe (run_config.json): class min-run of the bridge's min-run leg.
MIN_RUN = {"gas_cc": 21, "gas_st": 13}
# Detector run threshold (caiso_ra_mustoffer_min_gen default run_threshold_frac).
RUN_FRAC = 0.05


def _plant_series(uh: pd.DataFrame, fl: np.lib.npyio.NpzFile, code: int) -> dict:
    """Per-plant hourly bridge floor, dispatch and the anchor row's free-run mask."""
    rows = np.flatnonzero(fl["plant_code"] == code)
    mech = fl["mechanism"][rows]
    mg = fl["min_gen"][rows].astype(float)
    bridge = mech == MECH_NYISO_GAS_COMMITMENT_BRIDGE
    floor_rows = np.flatnonzero(bridge.any(axis=1))
    F = np.where(bridge, mg, 0.0).sum(axis=0)
    ids = [str(u) for u in fl["unit_ids"][rows]]
    sub = uh[uh.plant_code == code]
    mw = (
        sub.pivot_table(index="hour", columns="unit_id", values="mw", aggfunc="sum")
        .reindex(columns=ids)
        .fillna(0.0)
        .to_numpy()
        .T
    )
    T = F.shape[0]
    mw = mw[:, :T]
    D = mw.sum(axis=0)
    g = rows[floor_rows[0]] if floor_rows.size else rows[0]
    gi = int(np.flatnonzero(rows == g)[0])
    on_free = (mw[gi] > RUN_FRAC * float(fl["pmax"][g])) & (F <= 0.0)
    at = (F > D2_FLOOR_MIN_MW) & (D <= F * (1.0 + D2_REL_TOL) + D2_FLOOR_MIN_MW)
    group = str(fl["plant_group"][g])
    fuel = "gas_cc" if group.startswith("CC") else "gas_st"
    return {"F": F, "D": D, "on_free": on_free, "at": at, "fuel": fuel, "group": group}


def _classify_blocks(F: np.ndarray, on_free: np.ndarray, mr: int) -> tuple:
    """Label every floored block by leg; return (per-hour leg label, per-hour anchor run)."""
    T = F.shape[0]
    leg = np.full(T, "", dtype=object)
    anchor = np.full((T, 2), -1, dtype=int)
    free_runs = find_runs(on_free)
    end_at = {e: (s, e) for s, e in free_runs}
    for a, b in find_runs(F > 0.0):
        run = end_at.get(a)
        if run is None:
            leg[a:b] = "unanchored"
            continue
        reach = b - run[0]  # anchor start to block end
        nxt = b < T and bool(on_free[b])
        if nxt:
            leg[a:b] = "min_run_or_gap" if reach <= mr else "gap"
        else:
            leg[a:b] = "min_run" if reach <= mr else "other"
        anchor[a:b] = run
    return leg, anchor


def _off_stretch(on: np.ndarray) -> np.ndarray:
    """Per hour: length of the measured OFF stretch containing it (0 where on)."""
    out = np.zeros(on.shape[0])
    for s, e in find_runs(~on):
        out[s:e] = e - s
    return out


def analyse_year(year: int, legs_dir: Path) -> list[dict]:
    """Census every bridge-floored plant of one keeper leg."""
    b = legs_dir / f"results/calibration/nyisonext21_{year}"
    fl = np.load(b / f"floors/{year}_P1.npz", allow_pickle=False)
    uh = pd.read_parquet(
        b / f"hourly/unit_hourly_{year}.parquet",
        columns=["unit_id", "plant_code", "hour", "mw"],
    )
    bench = bench_plant_view(load_bench(ROOT, "NYISO", year))
    codes = sorted(
        {
            int(c)
            for c, m in zip(fl["plant_code"], fl["mechanism"])
            if (m == MECH_NYISO_GAS_COMMITMENT_BRIDGE).any()
        }
    )
    out = []
    for code in codes:
        s = _plant_series(uh, fl, code)
        mr = MIN_RUN[s["fuel"]]
        leg, anchor = _classify_blocks(s["F"], s["on_free"], mr)
        meas = bench.get(str(code))
        at = s["at"]
        row = {
            "year": year,
            "plant": code,
            "group": s["group"],
            "floor_hours": int((s["F"] > 0).sum()),
            "floored_gwh": round(float(s["D"][s["F"] > 0].sum()) / 1e3, 2),
            "binding_hours": int(at.sum()),
            "binding_gwh": round(float(s["D"][at].sum()) / 1e3, 2),
            "binding_by_leg": {
                k: int((at & (leg == k)).sum())
                for k in ("min_run", "min_run_or_gap", "gap", "other", "unanchored")
            },
        }
        if meas is None or meas.get("ct_only"):
            row["meter"] = "none" if meas is None else "ct_only"
            out.append(row)
            continue
        m = np.asarray(meas["mw"], float)[: at.size]
        m_on = m > 0.0
        zero = at & ~m_on
        below = at & m_on & (m < s["F"])
        stretch = _off_stretch(m_on)
        phantom = np.zeros(at.size, dtype=bool)
        for t in np.flatnonzero(zero):
            a0, a1 = anchor[t]
            if a0 >= 0 and not m_on[a0:a1].any():
                phantom[t] = True
        row.update(
            meter="campd",
            measured_zero_share=round(float(zero.sum()) / max(1, int(at.sum())), 3),
            meter_zero_by_leg={
                k: int((zero & (leg == k)).sum())
                for k in ("min_run", "min_run_or_gap", "gap", "other", "unanchored")
            },
            meter_zero_gwh=round(float(s["D"][zero].sum()) / 1e3, 2),
            meter_zero_in_measured_off_gt24h=int((zero & (stretch > 24)).sum()),
            meter_zero_anchor_phantom=int(phantom.sum()),
            meter_below_floor_hours=int(below.sum()),
            measured_runs=len(find_runs(m_on)),
            measured_run_median_h=(
                float(np.median([e - a for a, e in find_runs(m_on)]))
                if m_on.any()
                else None
            ),
        )
        out.append(row)
    return out


def main() -> None:
    """Run the census over the five keeper legs and write the JSON."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--legs-dir", type=Path, required=True)
    args = ap.parse_args()
    rows = [r for y in YEARS for r in analyse_year(y, args.legs_dir)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"probe": "nyisonext31_bridge_d4_legs", "rows": rows}, indent=1)
    )
    for r in rows:
        print(json.dumps(r))


if __name__ == "__main__":
    main()
