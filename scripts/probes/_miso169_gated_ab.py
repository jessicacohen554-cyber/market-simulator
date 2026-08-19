"""miso-169 A/B instrument: the PREREG-miso167 §6 decision-rule measurements.

Read-only over the two committed bundles (control ``miso169_gated_A``, arm
``miso169_gated_B``); nothing feeds back into a solve. Measures, per year:

* the load-weighted P1 system-price deltas (annual, summer, the 47 scarce
  hours) — the §4 disclosed-direction magnitudes;
* **K-5's decomposition**: the reserve-dual and price movement split between
  the DA-FORESEEN scarce hours (MISO's own DA market priced the hour above
  $150 — hours a deterministic LP is *capable* of reaching) and the RT-ONLY
  scarce hours (DA ≤ $150 — operational events perfect-foresight dispatch
  should not reach). A rise concentrated RT-only FAILS K-5 whatever it does
  to C3a (prereg §6).
* the arm's new ``miso_rbdc_regspin`` family: requirement, held, shortfall
  and dual, so the mechanism's own binding is on the record.

Hour conventions verbatim from the miso-167 instrument
(``_miso167_summer_scarcity_instrument.py``): fixed non-leap CST calendar,
summer = hours 3624..6551, scarce = actual RT > $200, foreseen = actual
DA > $150, actuals from ``_validation-source/actual_lmp_hourly_MISO.parquet``.

Usage:
    python scripts/probes/_miso169_gated_ab.py

writes ``results/calibration/_miso169_gated_ab.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "results" / "calibration" / "miso169_gated_A" / "hourly"
ARM = ROOT / "results" / "calibration" / "miso169_gated_B" / "hourly"
ACTUAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
YEARS = (2023, 2024, 2025)

MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[9])
SCARCE_RT = 200.0
FORESEEN_DA = 150.0


def system_price(bundle: Path, year: int) -> pd.DataFrame:
    """(hour, price): load-weighted P1 system price."""
    d = pd.read_parquet(bundle / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    d["pw"] = d["price"] * d["demand"]
    g = d.groupby("hour").agg(pw=("pw", "sum"), demand=("demand", "sum"))
    g["price"] = g["pw"] / g["demand"]
    return g[["price"]].reset_index()


def reserve_families(bundle: Path, year: int) -> pd.DataFrame:
    """Per-(family, hour) P1 requirement/held/shortfall/dual."""
    d = pd.read_parquet(bundle / f"reserve_family_{year}.parquet")
    return d[d["pass"] == "P1"].reset_index(drop=True)


def hour_classes(year: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(scarce, foreseen, rt_only) hour arrays for the year."""
    a = pd.read_parquet(ACTUAL)
    a = a[a["year"] == year]
    su = a[(a["hour"] >= SUMMER[0]) & (a["hour"] < SUMMER[1])]
    sc = su[su["rt"] > SCARCE_RT]
    foreseen = sc[sc["da"] > FORESEEN_DA]["hour"].to_numpy()
    rt_only = sc[sc["da"] <= FORESEEN_DA]["hour"].to_numpy()
    return sc["hour"].to_numpy(), np.sort(foreseen), np.sort(rt_only)


def _mean_over(df: pd.DataFrame, hours: np.ndarray, col: str) -> float:
    sub = df[df["hour"].isin(hours)]
    return float(sub[col].mean()) if len(sub) else float("nan")


def main() -> None:
    out: dict = {
        "basis": {
            "session": "miso-169",
            "prereg": "PREREG-miso167-online-gated-reserve-supply-2026-08-18.md §4/§6",
            "control": str(CONTROL.parent),
            "arm": str(ARM.parent),
            "hour_key": "model chronological non-leap 8760 CST calendar",
            "scarce_rt_threshold": SCARCE_RT,
            "foreseen_da_threshold": FORESEEN_DA,
        },
        "years": {},
    }
    for year in YEARS:
        pa = system_price(CONTROL, year)
        pb = system_price(ARM, year)
        m = pa.merge(pb, on="hour", suffixes=("_a", "_b"))
        m["d"] = m["price_b"] - m["price_a"]
        su = m[(m["hour"] >= SUMMER[0]) & (m["hour"] < SUMMER[1])]
        scarce, foreseen, rt_only = hour_classes(year)

        ra = reserve_families(CONTROL, year)
        rb = reserve_families(ARM, year)
        fam_b = sorted(rb["family"].unique().tolist())
        # Total reserve dual per hour (sum across families) in both runs.
        da_tot = ra.groupby("hour")["dual"].sum().rename("dual_a").reset_index()
        db_tot = rb.groupby("hour")["dual"].sum().rename("dual_b").reset_index()
        dm = da_tot.merge(db_tot, on="hour")
        dm["dd"] = dm["dual_b"] - dm["dual_a"]

        yr: dict = {
            "price_delta_mean": {
                "annual": float(m["d"].mean()),
                "annual_pct_of_control": float(
                    100.0 * m["d"].mean() / m["price_a"].mean()
                ),
                "summer": float(su["d"].mean()),
                "summer_pct_of_control": float(
                    100.0 * su["d"].mean() / su["price_a"].mean()
                ),
                "scarce": _mean_over(m, scarce, "d"),
                "foreseen": _mean_over(m, foreseen, "d"),
                "rt_only": _mean_over(m, rt_only, "d"),
            },
            "n_hours": {
                "scarce": int(scarce.size),
                "foreseen": int(foreseen.size),
                "rt_only": int(rt_only.size),
            },
            "reserve_dual_delta_mean": {
                "annual": float(dm["dd"].mean()),
                "scarce": _mean_over(dm, scarce, "dd"),
                "foreseen": _mean_over(dm, foreseen, "dd"),
                "rt_only": _mean_over(dm, rt_only, "dd"),
            },
            "arm_families": fam_b,
        }
        if "miso_rbdc_regspin" in fam_b:
            rs = rb[rb["family"] == "miso_rbdc_regspin"]
            yr["regspin_family"] = {
                "req_mean_mw": float(rs["requirement_mw"].mean()),
                "held_mean_mw": float(rs["held_mw"].mean()),
                "shortfall_hours": int((rs["shortfall_mw"] > 1e-6).sum()),
                "dual_pos_hours": int((rs["dual"] > 0.01).sum()),
                "dual_mean": float(rs["dual"].mean()),
                "dual_mean_scarce": _mean_over(rs, scarce, "dual"),
                "dual_mean_foreseen": _mean_over(rs, foreseen, "dual"),
                "dual_mean_rt_only": _mean_over(rs, rt_only, "dual"),
            }
        out["years"][str(year)] = yr

    dest = ROOT / "results" / "calibration" / "_miso169_gated_ab.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}")
    for y, yr in out["years"].items():
        pd_ = yr["price_delta_mean"]
        print(
            f"{y}: annual {pd_['annual']:+.3f} $/MWh ({pd_['annual_pct_of_control']:+.2f}%), "
            f"summer {pd_['summer']:+.3f}, scarce {pd_['scarce']:+.2f}, "
            f"foreseen {pd_['foreseen']:+.2f}, rt_only {pd_['rt_only']:+.2f}"
        )
        if "regspin_family" in yr:
            rs = yr["regspin_family"]
            print(
                f"    regspin: req {rs['req_mean_mw']:.0f} MW, dual>0 in "
                f"{rs['dual_pos_hours']} h (mean {rs['dual_mean']:.2f}), "
                f"foreseen {rs['dual_mean_foreseen']:.2f} vs rt_only "
                f"{rs['dual_mean_rt_only']:.2f}"
            )


if __name__ == "__main__":
    main()
