"""PREREG-miso167 §3 pre-check: can the online-gated reserve split bind at all?

Executes the no-LP pre-check EXACTLY as pre-registered
(``results/calibration/PREREG-miso167-online-gated-reserve-supply-2026-08-18.md``
§3, thresholds fixed there before measurement), on the tranche-grain
``hourly/unit_hourly_<year>.parquet`` sidecars of the miso-169 zero-delta
CONTROL replay — which the miso-168 corrected execution order
(``FINDING-miso168-precheck-data-gap-2026-08-18.md`` §3) established is the
keeper's own P1 once the control's bit-identity vs the committed keeper is
verified. Read-only: nothing here feeds a solve.

Constructions, each pinned to an existing repo convention rather than chosen
here:

* **Scarce hours** — the 47 actual summer-2025 RT>$200 hours, reconstructed
  from ``data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`` with the
  miso-167 instrument's own summer window and threshold
  (``scripts/probes/_miso167_summer_scarcity_instrument.py``: fixed non-leap
  CST calendar, Jun 1–Sep 30 = hours 3624..6551, ``rt > 200``).
* **Plant online** — ``sum(mw) > 1.0 MW`` over the plant's tranches, the
  ``online_threshold_mw`` default of ``results.scarcity.reserve_headroom``
  (the plant-level online/synchronized measure the sidecar exists to feed).
* **Eligibility** — ``RESERVE_FUEL_TYPES`` (gas_cc/gas_ct/gas_st/coal/
  nuclear/oil), the same mask the MISO per-asset reserve design draws its
  members from; offline quick-start capacity (``QUICK_START_FUEL_TYPES``)
  is reported as H_off, the ungated Supplemental/STR side's supply.
* **Requirement** — MISO's measured RT cleared Regulation + Spin MW summed
  over regions (``data/raw/MISO-AS/asm_rt_cleared_mw_<y>.parquet``), aligned
  hour-ending-EST → CST exactly as the miso-167 instrument's
  ``asm_cleared`` (its ``_est_he_to_cst_hour``: HE k EST = hour k−2 CST).

Kill gates (thresholds VERBATIM from the prereg, fixed before measurement):

* **K-PRE-A (inertness):** H_on ≥ (reg+spin req) in ≥ 80 % of the 47 scarce
  hours → the gate cannot bind where it matters → DECLARE INERT, mint the
  MISO cell ``I``, DO NOT SOLVE THE ARM.
* **K-PRE-B (over-reach):** H_on < (reg+spin req) in ≥ 99 % of ALL 8,760
  hours of any year → the construction is wrong; fix or abandon, do not
  solve.

Usage:
    python scripts/probes/_miso169_online_gated_precheck.py <control_bundle_dir>

writes ``results/calibration/_miso169_online_gated_precheck.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.model.reserves.spec import (  # noqa: E402
    QUICK_START_FUEL_TYPES,
    RESERVE_FUEL_TYPES,
)

ACTUAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
ASDIR = ROOT / "data" / "raw" / "MISO-AS"
YEARS = (2023, 2024, 2025)

# miso-167 instrument conventions (fixed non-leap CST calendar).
MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[9])  # Jun 1 .. Sep 30 inclusive
SCARCE_RT = 200.0
ONLINE_THRESHOLD_MW = 1.0  # results.scarcity.reserve_headroom default


def _est_he_to_cst_hour(frame: pd.DataFrame, k: pd.Series) -> pd.Series:
    """Hour-ending-k EST → CST hour stamp (miso-167 instrument, verbatim)."""
    return frame["date"] + pd.to_timedelta(k - 2, unit="h")


def reg_spin_requirement(year: int) -> pd.DataFrame:
    """(hour, req_mw): measured RT cleared Reg+Spin MW summed over regions."""
    d = pd.read_parquet(ASDIR / f"asm_rt_cleared_mw_{year}.parquet")
    d = d[d["product"].isin(["reg", "spin"])].copy()
    d["date"] = pd.to_datetime(d["date"])
    d["ts"] = _est_he_to_cst_hour(d, d["hour_end_est"])
    d = d[d["ts"].dt.year == year]
    d = d[~((d["ts"].dt.month == 2) & (d["ts"].dt.day == 29))]
    base = pd.Timestamp(f"{year}-01-01")
    d["hour"] = ((d["ts"] - base).dt.total_seconds() // 3600).astype(int)
    d = d[(d["hour"] >= 0) & (d["hour"] < 8760)]
    return d.groupby("hour")["cleared_mw"].sum().rename("req_mw").reset_index()


def scarce_hours_2025() -> np.ndarray:
    """The actual summer-2025 RT>$200 hours on the model hour key."""
    a = pd.read_parquet(ACTUAL)
    a = a[a["year"] == 2025]
    sc = a[(a["hour"] >= SUMMER[0]) & (a["hour"] < SUMMER[1]) & (a["rt"] > SCARCE_RT)]
    return np.sort(sc["hour"].to_numpy())


def hourly_headroom(bundle: Path, year: int) -> pd.DataFrame:
    """(hour, h_on_mw, h_off_mw) from the control's tranche-grain sidecar.

    h_on: headroom (Σcap − Σmw) summed over reserve-eligible plants whose
    plant-level dispatch exceeds the online threshold. h_off: available
    capacity on quick-start plants below it (the offline-eligible side).
    Both sums are linear in the tranches, so the plant grain is exact
    (the ``_unit_hourly_frame`` docstring's construction).
    """
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "fuel", "hour", "mw", "cap_mw"],
    )
    df = df[df["pass"] == "P1"]
    df = df[df["fuel"].isin(sorted(RESERVE_FUEL_TYPES))]
    g = (
        df.groupby(["plant_code", "fuel", "hour"], observed=True)
        .agg(mw=("mw", "sum"), cap_mw=("cap_mw", "sum"))
        .reset_index()
    )
    online = g["mw"] > ONLINE_THRESHOLD_MW
    quick = g["fuel"].isin(sorted(QUICK_START_FUEL_TYPES))
    g["h_on"] = np.where(online, np.maximum(g["cap_mw"] - g["mw"], 0.0), 0.0)
    g["h_off"] = np.where(~online & quick, g["cap_mw"], 0.0)
    out = g.groupby("hour").agg(h_on_mw=("h_on", "sum"), h_off_mw=("h_off", "sum"))
    return out.reset_index()


def main() -> None:
    bundle = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if bundle is None or not (bundle / "hourly").is_dir():
        raise SystemExit(
            "usage: _miso169_online_gated_precheck.py <control_bundle_dir>"
        )

    scarce = scarce_hours_2025()
    out: dict = {
        "basis": {
            "session": "miso-169",
            "prereg": "PREREG-miso167-online-gated-reserve-supply-2026-08-18.md §3",
            "control_bundle": str(bundle),
            "hour_key": "model chronological non-leap 8760 CST calendar",
            "summer": f"hours {SUMMER[0]}..{SUMMER[1] - 1}",
            "scarce_rt_threshold": SCARCE_RT,
            "online_threshold_mw": ONLINE_THRESHOLD_MW,
            "eligibility": sorted(RESERVE_FUEL_TYPES),
            "quick_start": sorted(QUICK_START_FUEL_TYPES),
            "requirement": "asm_rt_cleared_mw_<y> reg+spin summed over regions",
            "n_scarce_2025": int(scarce.size),
            "scarce_hours_2025": [int(h) for h in scarce],
        },
        "years": {},
    }

    for year in YEARS:
        hh = hourly_headroom(bundle, year)
        req = reg_spin_requirement(year)
        m = hh.merge(req, on="hour", how="left")
        # An ASM hour missing from the measured record cannot count as a
        # binding hour for K-PRE-B (fail-open would inflate the kill); track
        # coverage explicitly instead.
        covered = m["req_mw"].notna()
        mm = m[covered]
        short = mm["h_on_mw"] < mm["req_mw"]
        yr: dict = {
            "hours_covered": int(covered.sum()),
            "share_short_all_hours": float(short.mean()),
            "h_on_annual_mean_gw": float(m["h_on_mw"].mean() / 1000.0),
            "h_off_annual_mean_gw": float(m["h_off_mw"].mean() / 1000.0),
            "req_annual_mean_gw": float(mm["req_mw"].mean() / 1000.0),
        }
        if year == 2025:
            sc = m[m["hour"].isin(scarce)]
            sc_cov = sc[sc["req_mw"].notna()]
            meets = sc_cov["h_on_mw"] >= sc_cov["req_mw"]
            yr["scarce"] = {
                "n_hours": int(len(sc)),
                "n_covered": int(len(sc_cov)),
                "share_h_on_meets_req": float(meets.mean()),
                "h_on_mean_gw": float(sc_cov["h_on_mw"].mean() / 1000.0),
                "h_off_mean_gw": float(sc_cov["h_off_mw"].mean() / 1000.0),
                "req_mean_gw": float(sc_cov["req_mw"].mean() / 1000.0),
                "per_hour": [
                    {
                        "hour": int(r.hour),
                        "h_on_mw": round(float(r.h_on_mw), 1),
                        "h_off_mw": round(float(r.h_off_mw), 1),
                        "req_mw": (
                            round(float(r.req_mw), 1) if np.isfinite(r.req_mw) else None
                        ),
                    }
                    for r in sc.itertuples()
                ],
            }
        out["years"][str(year)] = yr

    # --- Kill gates, thresholds verbatim from the prereg -------------------
    sc = out["years"]["2025"]["scarce"]
    k_pre_a = sc["share_h_on_meets_req"] >= 0.80
    k_pre_b_years = {
        y: out["years"][y]["share_short_all_hours"] >= 0.99 for y in map(str, YEARS)
    }
    out["verdict"] = {
        "K_PRE_A_fired_inert": bool(k_pre_a),
        "K_PRE_A_share": sc["share_h_on_meets_req"],
        "K_PRE_B_fired_overreach": {y: bool(v) for y, v in k_pre_b_years.items()},
        "proceed_to_arm": bool(not k_pre_a and not any(k_pre_b_years.values())),
    }

    dest = ROOT / "results" / "calibration" / "_miso169_online_gated_precheck.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}")
    print(
        f"K-PRE-A: H_on >= req in {sc['share_h_on_meets_req']:.1%} of the "
        f"{sc['n_covered']}/{sc['n_hours']} covered scarce hours "
        f"(fires at >=80% -> INERT): {'FIRED' if k_pre_a else 'clear'}"
    )
    for y in map(str, YEARS):
        s = out["years"][y]["share_short_all_hours"]
        print(
            f"K-PRE-B {y}: H_on < req in {s:.1%} of covered hours "
            f"(fires at >=99%): {'FIRED' if k_pre_b_years[y] else 'clear'}"
        )
    print("proceed_to_arm:", out["verdict"]["proceed_to_arm"])


if __name__ == "__main__":
    main()
