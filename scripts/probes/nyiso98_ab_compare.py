"""Compare the nyiso-98 arm against its same-HEAD zero-delta control.

Scores the single delta (``nuclear_unit_availability`` — measured per-reactor
DAILY NRC availability replacing the ``NUCLEAR_MONTHLY_CF_BY_YEAR``
fleet-month smear) against the gates pre-registered in
``docs/PREREG-nyiso98-nuclear-availability-2026-07-29.md`` §5, from the two
bundles' own committed sidecars.

Reports, per year:

* **the liveness check first** (the nyiso-89 §4a lesson): the max absolute
  hourly class delta between the arm and the control. A mechanism recorded ON
  in ``run_config.json`` that produces a byte-identical solve has not been
  tested — that is a stop-the-line result, not a null;
* **S2, the mechanism's own target** — nuclear r_day, gap-masked, arm vs
  control. The mask is the pre-registration's: EIA-930 ``NG: NUC`` gap days
  (0.0 MW posted in ≥1 hour) are falsified against NRC and dropped, because
  scoring against phantom zeros scores noise;
* **S1** — every class's energy so the C1 movement is visible, with the
  knife-edge 2023 ``CC_REGULAR`` cell (−2.76 of ±2.94) called out explicitly;
* **S3** — model hours over $300 against the measured tail (C3c: reported,
  not a gate).

Usage::

    python scripts/probes/nyiso98_ab_compare.py \
        --control results/calibration/nyiso98_control_zerodelta \
        --arm     results/calibration/nyiso98_nucavail
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes.nyiso98_nuclear_availability_provenance import (  # noqa: E402
    YEARS,
    _r,
    measured_daily,
)

C1_BAND = {"CC_REGULAR": 2.94}


def measured_hourly(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Measured hourly nuclear MW and the gap-HOUR mask (0.0 MW posted)."""
    from market_sim.data.eia930 import frames as fr

    mw = np.nan_to_num(
        fr._eia_hourly_frame_filled("NYIS", year)["NG: NUC"].to_numpy(float)
    )[:8760]
    return mw, (mw == 0.0)


def class_hourly(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """Model per-class hourly MW from a bundle's P1 class sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return {
        k: g.sort_values("hour")["mw"].to_numpy()[:8760]
        for k, g in df.groupby("klass")
    }


def system_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """Model hourly system frame (price/demand) from a bundle's P1 sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"]


def main(argv: list[str] | None = None) -> int:
    """Print the liveness check, then the S1/S2/S3 comparison."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    args = ap.parse_args(argv)

    for year in YEARS:
        ctl, arm = class_hourly(args.control, year), class_hourly(args.arm, year)
        shared = sorted(set(ctl) & set(arm))
        worst = max(
            (float(np.abs(arm[k] - ctl[k]).max()), k) for k in shared
        )
        print(f"\n=== {year} ===")
        print(
            f"LIVENESS  max |arm-control| hourly class delta: {worst[0]:,.1f} MW "
            f"(on {worst[1]}) — must be > 0 or the arm is inert"
        )

        # --- S2: the mechanism's own target -----------------------------
        act, gap = measured_daily(year)
        ok = ~gap
        print(
            f"S2 nuclear r_day (gap-masked, n={int(ok.sum())}/365; "
            f"{int(gap.sum())} falsified gap days dropped):"
        )
        for name, src in (("control", ctl), ("arm", arm)):
            nuc = src.get("nuclear")
            if nuc is None:
                print(f"    {name:<8} (no nuclear class row)")
                continue
            m = np.asarray(nuc, float)[:8760]
            d = m.reshape(365, 24).sum(1) / 1e3
            mwh, gaph = measured_hourly(year)
            okh = ~gaph
            print(
                f"    {name:<8} r_day {_r(d[ok], act[ok]):>6.3f}   "
                f"r_hr {_r(m[okh], mwh[okh]):>6.3f}   TWh {d.sum() / 1e3:>6.2f}"
            )

        # --- S1: class energies, C1 movement ----------------------------
        print("S1 class energy TWh (control -> arm, delta):")
        for k in shared:
            c, a = ctl[k].sum() / 1e6, arm[k].sum() / 1e6
            flag = ""
            if k in C1_BAND:
                flag = f"   [C1 band +-{C1_BAND[k]:.2f} TWh]"
            if abs(a - c) < 5e-4 and not flag:
                continue
            print(f"    {k:<13}{c:>8.3f} -> {a:>8.3f}  {a - c:>+7.3f}{flag}")

        # --- S3: C3c tail (reported, not a gate) ------------------------
        for name, b in (("control", args.control), ("arm", args.arm)):
            sysd = system_hourly(b, year)
            col = "price" if "price" in sysd.columns else sysd.columns[-1]
            p = sysd.groupby("hour")[col].max().to_numpy()
            print(f"S3 {name:<8} hours >$300: {int((p > 300).sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
