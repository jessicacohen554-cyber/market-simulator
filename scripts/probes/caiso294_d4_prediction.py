"""caiso-294: the EX-ANTE D-4 conduct-rider prediction for the duty window.

ZERO LP. Declared before any shard is launched, exactly as caiso-293 declared
its own (28 -> 20 failing rows) from the pooled placement artifact. This probe
recomputes the prediction from the arm's OWN composed ``min_gen`` arrays rather
than from an analytic pooled window, which is tighter: the hours it scores are
the hours ``fleet/arrays.py`` actually floors, availability clip included.

WHY THE PREDICTION IS LEVEL-INDEPENDENT. The D-4 per-unit conduct rider
(``legitimacy_diagnostics.py``) convicts on
``median(measured MW over the hours the floor binds for this plant) <= 0``. The
statistic reads the measured series over a SET OF HOURS; the floor's magnitude
never enters it. ARM A (diluted level) and ARM B (undiluted level) place the
floor in the SAME hours — same ``on_frac``, same shared window series, same
top-k-by-load rank — so both arms carry the SAME D-4 prediction, and this probe
is run once for both.

WHAT IT APPROXIMATES, stated rather than buried. The real rider scores
``at_floor_mask(dispatch, min_gen, npl)`` — the subset of floored hours where
the SOLVED dispatch actually sits at the floor — and there is no dispatch
without an LP. This probe scores the full floored-hour set (``min_gen > 0``),
which is that subset's superset. The direction of the approximation is known:
hours the LP lifts off the floor are hours the unit is economic, which are
hours it is more likely to be metered ON, so dropping them can only lower the
measured median. **The prediction here is therefore the conservative one** — the
solve can clear more rows than predicted, not fewer, for that reason alone.

Run: ``PYTHONPATH=.:src python scripts/probes/caiso294_d4_prediction.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.legitimacy_diagnostics import (  # noqa: E402
    bench_plant_view,
    ct_only_span_union,
    load_bench,
)
from scripts.probes.caiso293_gates import BUNDLE, YEARS, compose  # noqa: E402

OUT = REPO / "results/calibration/_caiso294_d4_prediction.json"


def floored_hours(gens, arrays) -> dict[str, np.ndarray]:
    """Union, per plant, of the hours any of its rows carries a CHP floor."""
    from market_sim.data.floor_mechanisms import MECH_CHP_STEAM

    mg = np.asarray(arrays.min_gen, dtype=float)
    mech = np.asarray(arrays.min_gen_mechanism)
    out: dict[str, np.ndarray] = {}
    for g_idx, gen in enumerate(gens):
        if float(getattr(gen, "chp_grid_pmin_mw", 0.0) or 0.0) <= 0.0:
            continue
        pid = str(int(getattr(gen, "plant_code", 0) or 0))
        hrs = (mg[g_idx, :] > 0.0) & (mech[g_idx, :] == MECH_CHP_STEAM)
        out[pid] = hrs if pid not in out else (out[pid] | hrs)
    return out


def rider(hours_by_plant: dict[str, np.ndarray], bench_pl: dict) -> dict[str, dict]:
    """The rider's own statistic over each plant's floored hours."""
    rows: dict[str, dict] = {}
    for pid, hrs in sorted(hours_by_plant.items()):
        b = bench_pl.get(pid)
        if b is None:
            rows[pid] = {"verdict": "skipped-unmetered"}
            continue
        if b.get("ct_only"):
            rows[pid] = {"verdict": "skipped-ct_only"}
            continue
        meas = np.asarray(b["mw"], dtype=float)
        n = min(len(meas), len(hrs))
        win = meas[:n][hrs[:n]]
        if win.size == 0:
            rows[pid] = {"verdict": "no-binding-hours"}
            continue
        med = float(np.median(win))
        rows[pid] = {
            "binding_hours": int(win.size),
            "measured_median_mw": round(med, 3),
            "measured_zero_share": round(float((win <= 0.0).mean()), 4),
            "verdict": "FAIL" if med <= 0.0 else "pass",
        }
    return rows


def main() -> None:
    ct_span = ct_only_span_union(REPO, "CAISO", list(YEARS))
    report: dict = {
        "scope": "MECH_CHP_STEAM per-unit conduct rider, zero LP",
        "level_independent": (
            "ARM A and ARM B place the floor in identical hours; the rider "
            "reads only the hour set, so this prediction covers both"
        ),
        "approximation": "scores min_gen>0, the superset of at_floor_mask — conservative",
    }
    per_year = {}
    tot_off = tot_on = 0
    for year in YEARS:
        bench = load_bench(REPO, "CAISO", year)
        bench_pl = bench_plant_view(bench)
        for p in ct_span & bench_pl.keys():
            bench_pl[p]["ct_only"] = True

        gens_off, arr_off, _ = compose(year, armed=False)
        off_rows = rider(floored_hours(gens_off, arr_off), bench_pl)
        gens_on, arr_on, _ = compose(year, armed=True)
        on_rows = rider(floored_hours(gens_on, arr_on), bench_pl)

        n_off = sum(1 for r in off_rows.values() if r.get("verdict") == "FAIL")
        n_on = sum(1 for r in on_rows.values() if r.get("verdict") == "FAIL")
        tot_off += n_off
        tot_on += n_on
        flips = sorted(
            p
            for p in off_rows
            if off_rows[p].get("verdict") == "FAIL"
            and on_rows.get(p, {}).get("verdict") == "pass"
        )
        per_year[str(year)] = {
            "keeper_rider_fails": n_off,
            "armed_rider_fails": n_on,
            "cleared_plants": flips,
            "keeper_rows": off_rows,
            "armed_rows": on_rows,
        }
        print(
            f"{year}: rider FAILs {n_off} -> {n_on}"
            + (f"   cleared: {', '.join(flips)}" if flips else "")
        )

    report["per_year"] = per_year
    report["prediction"] = {"keeper_total": tot_off, "armed_total": tot_on}
    OUT.write_text(json.dumps(report, indent=1))
    print(f"\nPREDICTION (span 2022-2025): rider FAILs {tot_off} -> {tot_on}")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
