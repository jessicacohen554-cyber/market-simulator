"""Ex-ante validation of the proposed CHP steam-floor WINDOW, at zero LP.

The repair under test (PRECOMMIT-caiso293): stop multiplying the measured
on-frequency INTO the steam level and use it the way every OTHER per-plant
must-run floor in this repo already uses it — to size a WINDOW that the
loading-when-on level then fills. The derive already computes both factors
(``derive_thermal_tranches.py``: ``on_freq``, ``np.percentile(on_cat, 50)``)
and discards the first by multiplication.

This probe asks the one question that decides whether the window is placed by
the right driver, BEFORE any LP is spent: **if the floor is confined to the top
``on_freq x 8760`` hours of the shared commitment-floor window driver (system
load — ``fleet/arrays.py``'s ``_window_src``, SPP-66 default OFF ⇒ ``load_shape``),
how much of that window did the plant's own meter say it was running?**

Three placements are scored against the same per-plant window size:

* ``load``  — top-k system-load hours (the sibling floors' construction).
* ``duty``  — top-k hours of the plant's own POOLED (month x hour-of-day)
  on-frequency surface, built from the OTHER years only (leave-one-year-out),
  so the score is not read off the year it is placed on.
* ``random``— the ``on_frac`` baseline a windowless placement earns by luck.

``precision`` is the share of window hours the meter says the plant was online;
``lift`` is precision / on_frac. Lift 1.0 means the window is no better than
flat forcing — i.e. the driver is wrong.

Run: ``PYTHONPATH=.:src python scripts/probes/caiso293_window_placement.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/xiso8_leftedge_span"
YEARS = (2022, 2023, 2024, 2025)
OUT = REPO / "results/calibration/_caiso293_window_placement.json"

#: The seven plants the keeper's committed D-4 rows fail on, plus the three
#: CAMPD-visible plants whose flat conduct the mechanism's (0, 24) window
#: comment cites as its own evidence (the controls — the repair must leave
#: these essentially untouched), plus the three cyclers the D-4 conduct rider
#: SKIPS for a CT-only CEMS flag.
FAIL = (10034, 10294, 10649, 10650, 50612, 54749, 54768)
REF = (55400, 55217, 50865)
SKIPPED = (10405, 10349, 10156)


def system_load(year: int) -> np.ndarray:
    """ISO-wide hourly demand from the keeper's own committed P1 sidecar."""
    df = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return (
        df.groupby("hour")["demand"].sum().reindex(range(8760), fill_value=0.0).to_numpy()
    )


def meter(year: int, code: int):
    """(on-mask, month, hour-of-day) on the gap-free 8760 clock, or None."""
    from market_sim.data import campd

    raw = _RAW[year]
    grid = campd.plant_hourly_grid(raw, code, year)
    if grid.empty:
        return None
    # The LP clock is 8760: Feb 29 is dropped upstream (campd._hour_index_8760),
    # so the meter is put on the same clock before any hour-for-hour comparison.
    idx = grid.index
    keep = ~((idx.month == 2) & (idx.day == 29))
    grid = grid[keep]
    idx = grid.index
    on = grid["gross_mw"].to_numpy(dtype=float) > 0.0
    return on, idx.month.to_numpy(), idx.hour.to_numpy()


def topk_mask(score: np.ndarray, k: int) -> np.ndarray:
    """Boolean mask of the ``k`` highest-scoring hours."""
    m = np.zeros(score.size, dtype=bool)
    if k > 0:
        m[np.argpartition(-score, min(k, score.size - 1))[:k]] = True
    return m


def main() -> None:
    from market_sim.data import campd

    global _RAW
    _RAW = {y: campd.load_campd_hourly(["CA"], [y], prefer_unit_level=True) for y in YEARS}
    loads = {y: system_load(y) for y in YEARS}

    # Pooled (month x hod) on-frequency surface per plant, per year, built
    # LEAVE-ONE-YEAR-OUT so a duty window is never scored on its own year.
    per_year_on: dict[tuple[int, int], tuple] = {}
    for y in YEARS:
        for code in FAIL + REF + SKIPPED:
            m = meter(y, code)
            if m is not None:
                per_year_on[(code, y)] = m

    rows = []
    for code in FAIL + REF + SKIPPED:
        grp = "D4-FAIL" if code in FAIL else ("ref-flat" if code in REF else "rider-skipped")
        for y in YEARS:
            cur = per_year_on.get((code, y))
            if cur is None:
                continue
            on, mon, hod = cur
            n = on.size
            on_frac = float(on.mean())
            k = int(round(on_frac * n))
            if k == 0:
                continue

            # (1) load-ranked window
            load = loads[y][:n]
            p_load = float(on[topk_mask(load, k)].mean())

            # (2) leave-one-year-out (month x hod) duty surface
            surf = np.zeros((13, 24))
            cnt = np.zeros((13, 24))
            for oy in YEARS:
                if oy == y:
                    continue
                oth = per_year_on.get((code, oy))
                if oth is None:
                    continue
                o_on, o_mon, o_hod = oth
                np.add.at(surf, (o_mon, o_hod), o_on.astype(float))
                np.add.at(cnt, (o_mon, o_hod), 1.0)
            if cnt.sum() == 0:
                p_duty = float("nan")
            else:
                with np.errstate(invalid="ignore", divide="ignore"):
                    rate = np.where(cnt > 0, surf / np.maximum(cnt, 1e-9), 0.0)
                score = rate[mon, hod]
                # tie-break inside a (month, hod) cell by system load, so the
                # window is deterministic rather than argpartition-arbitrary
                score = score + 1e-9 * (load / max(load.max(), 1e-9))
                p_duty = float(on[topk_mask(score, k)].mean())

            rows.append(
                {
                    "plant": code,
                    "grp": grp,
                    "year": y,
                    "on_frac": round(on_frac, 4),
                    "k_hours": k,
                    "prec_load": round(p_load, 4),
                    "lift_load": round(p_load / on_frac, 2),
                    "prec_duty": round(p_duty, 4) if p_duty == p_duty else None,
                    "lift_duty": round(p_duty / on_frac, 2) if p_duty == p_duty else None,
                }
            )

    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200, "display.max_rows", 200)
    print("\n===== WINDOW PLACEMENT, per plant-year (lift 1.0 == no better than flat) =====")
    print(df.to_string(index=False))

    print("\n===== BY GROUP (mean over plant-years) =====")
    print(
        df.groupby("grp")[["on_frac", "lift_load", "lift_duty"]]
        .mean()
        .round(3)
        .to_string()
    )

    OUT.write_text(json.dumps(json.loads(df.to_json(orient="records")), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
