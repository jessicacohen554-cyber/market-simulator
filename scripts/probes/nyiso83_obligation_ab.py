"""nyiso-83 A/B: in-city J/K commitment obligation vs a same-HEAD control.

Compares the nyiso-83 obligation probe against the zero-delta control replay of
the nyiso-81 keeper recipe, on the quantities this lane is judged by:

* **C3c price tail** — hours the max zonal dual exceeds ``$300``
  (``TAIL_THRESHOLD["NYISO"]``), the gated scarcity-formation metric, and where
  in the zone stack those hours sit. This is the supporting-tier lane the
  obligation mechanism is hypothesised to move
  (``docs/FINDING-nyiso-c3c-scarcity-formation-2026-07-26.md`` §3).
* **ST_GAS volume and diurnal shape** — the charter's acceptance criterion #3:
  the added energy must be EVENING-concentrated, not flat overnight. A fix that
  adds flat volume is the rejected floor-up probe again.
* **Class energy mix** — so a downstate ST/CC merit inversion is visible rather
  than hidden inside a matching total.

A control arm is used rather than the registered keeper metrics because the
replay environment's solver/pandas/pyarrow versions differ from the keeper's
recorded ones, so byte-identity is not guaranteed and only a same-HEAD,
same-environment baseline isolates the mechanism's own effect.

Usage:
    python scripts/probes/nyiso83_obligation_ab.py \
        --probe results/calibration/nyiso83_probe_obligation_2024 \
        --control results/calibration/nyiso83_control_2024 \
        --year 2024
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

TAIL_THRESHOLD_NYISO = 300.0
# Charter acceptance criterion #3: the measured gap is evening-concentrated
# (2023 overnight gap 44 MW mean vs evening gap 438 MW), and the NYC/LI ST_GAS
# reliability-floor evening ramp limbs the obligation supersedes bind hours
# 14-21 (reliability_floor_coeffs_NYISO.csv start_hour/end_hour).
EVENING_HOURS = range(14, 22)
OVERNIGHT_HOURS = list(range(0, 7)) + [22, 23]


def _system(bundle: Path, year: int) -> pd.DataFrame:
    """Load a bundle's P1 system hourly sidecar for *year*."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"]


def _classes(bundle: Path, year: int) -> pd.DataFrame:
    """Load a bundle's P1 class hourly sidecar for *year*."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return df[df["pass"] == "P1"]


def tail_rows(df: pd.DataFrame) -> dict:
    """Return the C3c tail counts (any-zone and per-zone) for one arm."""
    p = df.pivot_table(index="hour", columns="zone", values="price")
    out = {"any_zone": int((p.max(axis=1) > TAIL_THRESHOLD_NYISO).sum())}
    for z in p.columns:
        out[z] = int((p[z] > TAIL_THRESHOLD_NYISO).sum())
    load = df.pivot_table(index="hour", columns="zone", values="demand")
    w = (p * load).sum(axis=1) / load.sum(axis=1)
    out["_wtd_p999"] = round(float(w.quantile(0.999)), 1)
    out["_wtd_max"] = round(float(w.max()), 1)
    return out


def class_profile(df: pd.DataFrame, klass: str) -> dict:
    """Return annual TWh plus the evening/overnight mean MW of one class."""
    s = df[df["klass"] == klass]
    if s.empty:
        return {}
    by_hour = s.groupby("hour")["mw"].sum()
    hod = by_hour.groupby(by_hour.index % 24).mean()
    evening = float(hod.loc[list(EVENING_HOURS)].mean())
    overnight = float(hod.loc[OVERNIGHT_HOURS].mean())
    return {
        "twh": round(float(by_hour.sum()) / 1e6, 3),
        "evening_mw": round(evening, 1),
        "overnight_mw": round(overnight, 1),
        # > 1 means evening-weighted, the shape the charter requires.
        "ev_over_night": round(evening / overnight, 3) if overnight else float("nan"),
    }


def main() -> None:
    """Print the probe-vs-control A/B table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe", required=True, type=Path)
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--year", required=True, type=int)
    args = ap.parse_args()

    ps, cs = _system(args.probe, args.year), _system(args.control, args.year)
    pt, ct = tail_rows(ps), tail_rows(cs)

    print(f"=== C3c price tail (> ${TAIL_THRESHOLD_NYISO:.0f}), {args.year} ===")
    print(f"{'zone':<18}{'control':>9}{'probe':>9}{'delta':>9}")
    for k in ct:
        d = pt.get(k, 0) - ct[k]
        print(f"{k:<18}{ct[k]:>9}{pt.get(k, 0):>9}{d:>+9}")

    pc, cc = _classes(args.probe, args.year), _classes(args.control, args.year)
    classes = sorted(set(cc["klass"]) | set(pc["klass"]))
    print(f"\n=== class energy TWh + diurnal shape, {args.year} ===")
    print(
        f"{'class':<16}{'ctl TWh':>9}{'prb TWh':>9}{'dTWh':>8}"
        f"{'ctl ev/ng':>11}{'prb ev/ng':>11}"
    )
    for k in classes:
        a, b = class_profile(cc, k), class_profile(pc, k)
        if not a and not b:
            continue
        at, bt = a.get("twh", 0.0), b.get("twh", 0.0)
        if max(abs(at), abs(bt)) < 0.05:
            continue
        print(
            f"{k:<16}{at:>9.3f}{bt:>9.3f}{bt - at:>+8.3f}"
            f"{a.get('ev_over_night', np.nan):>11.3f}"
            f"{b.get('ev_over_night', np.nan):>11.3f}"
        )

    print("\n=== ST_GAS detail (charter acceptance criterion #3) ===")
    for name, d in (("control", class_profile(cc, "ST_GAS")),
                    ("probe", class_profile(pc, "ST_GAS"))):
        if d:
            print(
                f"  {name:<8} {d['twh']:.3f} TWh | evening {d['evening_mw']:.0f} MW"
                f" | overnight {d['overnight_mw']:.0f} MW"
                f" | ev/ng {d['ev_over_night']:.3f}"
            )


if __name__ == "__main__":
    main()
