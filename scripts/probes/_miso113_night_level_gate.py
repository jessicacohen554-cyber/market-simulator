"""miso-113 guard G6: the per-plant model NIGHT LEVEL, against the meter.

Reproduces FINDING-miso112 §4's structural test verbatim and promotes it to a
first-class pre-registered gate (PREREG-miso113-prb-night-floor-2026-08-01.md
§6 G6). That test is what closed the offer-side family: it found the KEEPER's
within-run night level already essentially exact (0.437 model vs a measured
0.434 in 2024) and the miso-112 split arm driving it BELOW the meter (0.374) —
so an arm that buys C7's within-day CV by overshooting the backdown is the
miso-112 failure repeated, whatever the shape gate says.

Construction, per plant, capacity-weighted over the regulated MISO COAL_PRB
plants, ONLINE hours only — the WP-3 loading-when-on identification applied to
each side's own series, so model and meter are measured the same way:

    plant load  = sum of the plant's unit rows in the P1 dispatch
    HSL         = the plant's MEASURED hsl_mw from the artifact — the SHARED
                  denominator, so model and meter are the same ratio and the
                  comparison is a level comparison rather than a shape one
                  (using each side's own p99.5 instead rescales the model onto
                  its own maximum and inflates both arms by ~0.06)
    online      = load >= max(10 MW, 2% x HSL)
    night level = p50 of load / HSL over ONLINE hours h0-5

Reproduction check: on the miso-113 control this yields 0.488 (2023) / 0.444
(2024) against a measured 0.437/0.438, versus FINDING-miso112 §4's 0.483 /
0.437 against 0.434 — i.e. the construction is recovered to ~0.005, the
residual being the 2025-vintage HEAD drift and the keeper-vs-control rebuild.

The measured side is the frozen artifact's pooled ``night_p50``
(``data/raw/_processed-legacy/coal_prb_committed_split_MISO.csv``, deriver
``scripts/data/derive_prb_committed_split.py`` — rule 23, not re-derived).

G6 VERDICT: the capacity-weighted model night level must move TOWARD the
measured level relative to the control, never past it — i.e. the cap-weighted
absolute error must not increase, and the arm must not cross from one side of
the meter to the other.

Usage:
    _miso113_night_level_gate.py <control-bundle> <arm-bundle> [years...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.coal import _coal_class_for  # noqa: E402
from market_sim.data.fleet.eia860 import (  # noqa: E402
    eia860_selfcommit_scope_plants,
)

SPLIT = REPO / "data/raw/_processed-legacy/coal_prb_committed_split_MISO.csv"
ONLINE_MW = 10.0
ONLINE_FRAC = 0.02
NIGHT_H = range(0, 6)  # h0-5, the deriver's own night window


def _scope() -> tuple[dict[int, float], dict[int, float]]:
    """Return ``({plant: measured night_p50}, {plant: measured hsl_mw})``."""
    night = pd.read_csv(SPLIT)
    reg = eia860_selfcommit_scope_plants()
    rows = [
        r
        for r in night.itertuples(index=False)
        if int(r.plant_code) in reg and _coal_class_for(int(r.plant_code)) == "COAL_PRB"
    ]
    return (
        {int(r.plant_code): float(r.night_p50) for r in rows},
        {int(r.plant_code): float(r.hsl_mw) for r in rows},
    )


def _model_night_levels(
    bundle: Path, year: int, scope: dict[int, float], hsl_mw: dict[int, float]
):
    """Return ``{plant: (model_night_level, plant_cap_mw)}`` for one bundle-year."""
    path = bundle / "hourly" / f"unit_hourly_{year}.parquet"
    if not path.exists():
        raise SystemExit(f"missing per-unit hourly: {path}")
    df = pd.read_parquet(path, columns=["pass", "plant_code", "hour", "mw", "cap_mw"])
    df = df[(df["pass"] == "P1") & (df["plant_code"].isin(scope))]
    out: dict[int, tuple[float, float]] = {}
    for pc, grp in df.groupby("plant_code"):
        # Plant load per hour = the sum of its tranche rows; plant cap likewise.
        load = grp.groupby("hour")["mw"].sum().sort_index()
        cap = float(grp.groupby("hour")["cap_mw"].sum().max())
        arr = load.to_numpy(dtype=float)
        hod = load.index.to_numpy() % 24
        hsl = float(hsl_mw[int(pc)])  # the MEASURED HSL, shared with the meter
        if hsl <= 0.0:
            continue
        online = arr >= max(ONLINE_MW, ONLINE_FRAC * hsl)
        night = online & np.isin(hod, list(NIGHT_H))
        if not night.any():
            continue
        out[int(pc)] = (float(np.median(arr[night] / hsl)), cap)
    return out


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    control = Path(sys.argv[1])
    arm = Path(sys.argv[2])
    years = [int(y) for y in sys.argv[3:]] or [2023, 2024, 2025]
    scope, hsl_mw = _scope()
    print(f"regulated MISO COAL_PRB plants in scope: {len(scope)}")

    rows = []
    for year in years:
        ctl = _model_night_levels(control, year, scope, hsl_mw)
        armv = _model_night_levels(arm, year, scope, hsl_mw)
        plants = sorted(set(ctl) & set(armv))
        w = np.array([ctl[p][1] for p in plants], dtype=float)
        meas = np.array([scope[p] for p in plants], dtype=float)
        c = np.array([ctl[p][0] for p in plants], dtype=float)
        a = np.array([armv[p][0] for p in plants], dtype=float)
        wsum = w.sum()
        rows.append(
            {
                "year": year,
                "n_plants": len(plants),
                "measured": float((meas * w).sum() / wsum),
                "control": float((c * w).sum() / wsum),
                "arm": float((a * w).sum() / wsum),
                "abs_err_control": float((np.abs(c - meas) * w).sum() / wsum),
                "abs_err_arm": float((np.abs(a - meas) * w).sum() / wsum),
            }
        )

    df = pd.DataFrame(rows)
    df["err_delta"] = df["abs_err_arm"] - df["abs_err_control"]
    print()
    print(df.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print()
    # G6: the cap-weighted absolute error must not increase in any year, and the
    # arm must not overshoot the meter where the control undershot (or vice
    # versa) — "toward, not past" is the whole point of the gate.
    worse = df[df["err_delta"] > 1e-4]
    crossed = df[
        np.sign(df["control"] - df["measured"]) * np.sign(df["arm"] - df["measured"])
        < 0
    ]
    for _, r in df.iterrows():
        print(
            f"  {int(r.year)}: measured {r.measured:.4f} | control {r.control:.4f} "
            f"-> arm {r.arm:.4f}; cap-wtd abs error {r.abs_err_control:.4f} -> "
            f"{r.abs_err_arm:.4f} ({r.err_delta:+.4f})"
        )
    print()
    if len(worse):
        print(f"G6 FAIL — error grew in {sorted(worse['year'].astype(int))}")
    elif len(crossed):
        print(
            "G6 FAIL — the arm crossed the meter (overshoot) in "
            f"{sorted(crossed['year'].astype(int))}"
        )
    else:
        print("G6 PASS — the night level moved toward the meter in every year")


if __name__ == "__main__":
    main()
