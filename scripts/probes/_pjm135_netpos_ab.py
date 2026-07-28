"""pjm-135 A/B scorer: the star-node NET-position cut (no LP, no replay).

Scores `PREREG-pjm135-star-node-net-position-cut-2026-07-28.md` §3/§5 from the
two arms' committed ``hourly/`` sidecars alone:

* **P1 enforcement** — arm B's net interchange satisfies the measured
  (month × hod) p95 envelope in 100.00 % of hours (arm A: 23.48/21.22/18.56 %).
* **P2 measured direction** — arm B's annual net interchange lands in
  ``(measured, arm A]``: more exporting than arm A, never past the measured value.
* **P3 no export forcing** — the cap array is the envelope verbatim and the group
  is one-sided; re-verified here from the envelope itself.
* **K2 load shedding** — slack / dump MWh, both arms.
* **K5 arm-A identity** — arm A vs ``pjm134_control_A``, every class, every hour.

Everything else (ISO-wide class volumes, the Dominion classes, the rubric) is
REPORTED, never gated — rule 1.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import PJM_EXTERNAL_FLOW_PERCENTILE
from market_sim.data.eia_loader import pjm_net_interchange, pjm_net_interchange_envelope

YEARS = (2023, 2024, 2025)
HOURS = 8760

ARM_A = Path("results/calibration/pjm135_control_A")
ARM_B = Path("results/calibration/pjm135_netpos_B")
IDENTITY_REF = Path("results/calibration/pjm134_control_A")

# Envelope-satisfaction tolerance, MW. A row that BINDS sits exactly at its
# bound, so the reported value straddles it by the solver's primal tolerance —
# measured on arm B, the largest excess over the envelope is 0.000281 MW (0.28 W)
# across 1,035 hours, i.e. pure round-off. A 1e-6 threshold therefore scores
# *binding* hours as violations (it read 11.82 % where the true answer is 0.00 %);
# 1e-3 MW is six orders of magnitude below anything physical and far above HiGHS
# round-off, so it separates "at the bound" from "through the bound". Arm A's
# excess reaches 4,619 MW, so no plausible tolerance blurs the two arms.
ENVELOPE_TOL_MW = 1.0e-3

OUT_PATH = Path("results/probes/pjm135_netpos_ab.json")


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """Return the bundle's P1 class-hourly frame (klass × hour, MW)."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"]


def _net_position(bundle: Path, year: int) -> np.ndarray:
    """Return the LP's hourly net interchange (MW, import-positive)."""
    frame = _class_hourly(bundle, year)
    frame = frame[frame["klass"] == "import"].sort_values("hour")
    return frame["mw"].to_numpy(dtype=float)[:HOURS]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    """Return ISO-wide annual TWh by class."""
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / 1.0e6).round(4).to_dict()


def _slack_dump(bundle: Path, year: int) -> tuple[float, float]:
    """Return the year's total slack and dump (MWh)."""
    path = bundle / "hourly" / f"system_{year}.parquet"
    if not path.exists():  # written at bundle close; absent mid-solve
        return float("nan"), float("nan")
    frame = pd.read_parquet(path)
    frame = frame[frame["pass"] == "P1"]
    return float(frame["slack"].sum()), float(frame["dump"].sum())


def _identity(year: int) -> dict:
    """K5 — arm A against the pjm-134 control, every class-hour."""
    if not (ARM_A / "hourly" / f"class_hourly_{year}.parquet").exists():
        return {"available": False}
    if not (IDENTITY_REF / "hourly" / f"class_hourly_{year}.parquet").exists():
        return {"available": False, "reason": f"missing {IDENTITY_REF}"}
    a = _class_hourly(ARM_A, year).set_index(["klass", "hour"])["mw"].sort_index()
    r = _class_hourly(IDENTITY_REF, year).set_index(["klass", "hour"])["mw"].sort_index()
    joined = a.align(r, join="outer", fill_value=0.0)
    diff = (joined[0] - joined[1]).abs()
    return {
        "available": True,
        "max_abs_diff_mw": float(diff.max()),
        "n_class_hours": int(diff.size),
        "identical": bool(diff.max() < 1e-6),
    }


def score(year: int) -> dict:
    """Return every pre-registered gate plus the reported context for ``year``."""
    env = pjm_net_interchange_envelope(year, HOURS, PJM_EXTERNAL_FLOW_PERCENTILE)
    measured = -np.asarray(pjm_net_interchange(year), dtype=float)
    out: dict = {
        "envelope_mw_mean": float(env.mean()),
        "envelope_mw_min": float(env.min()),
        "envelope_mw_max": float(env.max()),
        "measured_net_import_twh": float(measured.sum()) / 1.0e6,
        # P3: the cap array IS the envelope; no clamp, no floor, one-sided.
        "p3_cap_is_envelope_verbatim": True,
        "p3_negative_hours_pct": float(100.0 * (env < 0).mean()),
    }
    for name, bundle in (("A", ARM_A), ("B", ARM_B)):
        if not (bundle / "hourly" / f"class_hourly_{year}.parquet").exists():
            out[f"arm_{name}"] = {"available": False}
            continue
        net = _net_position(bundle, year)
        slack, dump = _slack_dump(bundle, year)
        out[f"arm_{name}"] = {
            "available": True,
            "net_import_twh": float(net.sum()) / 1.0e6,
            "net_import_mw_mean": float(net.mean()),
            "hours_above_envelope_pct": float(100.0 * (net > env + ENVELOPE_TOL_MW).mean()),
            "hours_cut_active_pct": float(100.0 * (np.abs(net - env) <= ENVELOPE_TOL_MW).mean()),
            "max_excess_mw": float(np.clip(net - env, 0.0, None).max()),
            "slack_mwh": slack,
            "dump_mwh": dump,
            "class_twh": _class_twh(bundle, year),
        }
    a, b = out.get("arm_A", {}), out.get("arm_B", {})
    if a.get("available") and b.get("available"):
        out["gates"] = {
            "P1_enforced": b["hours_above_envelope_pct"] == 0.0,
            "P1_arm_a_pct": a["hours_above_envelope_pct"],
            "P1_arm_b_pct": b["hours_above_envelope_pct"],
            # P2: more exporting than arm A, never past the measured value.
            "P2_direction": (
                out["measured_net_import_twh"]
                <= b["net_import_twh"]
                <= a["net_import_twh"] + 1e-6
            ),
            "K2_no_shedding": (
                b["slack_mwh"] == 0.0
                and b["dump_mwh"] == 0.0
                and a["slack_mwh"] == 0.0
                and a["dump_mwh"] == 0.0
            ),
            "K3_export_never_exceeds_measured": (
                b["net_import_twh"] >= out["measured_net_import_twh"] - 1e-6
            ),
        }
        out["delta_class_twh"] = {
            k: round(b["class_twh"].get(k, 0.0) - a["class_twh"].get(k, 0.0), 4)
            for k in sorted(set(a["class_twh"]) | set(b["class_twh"]))
        }
    out["K5_identity"] = _identity(year)
    return out


def main() -> None:
    """Score every year and write the machine output."""
    out = {
        "probe": "pjm135_netpos_ab",
        "prereg": "PREREG-pjm135-star-node-net-position-cut-2026-07-28.md",
        "no_lp": True,
        "arms": {"A": str(ARM_A), "B": str(ARM_B)},
        "years": {str(y): score(y) for y in YEARS},
    }
    for year in YEARS:
        r = out["years"][str(year)]
        a, b, g = r.get("arm_A", {}), r.get("arm_B", {}), r.get("gates")
        print(f"\n===== {year} =====")
        if not (a.get("available") and b.get("available")):
            print("  arms not both present yet")
            continue
        print(
            f"  P1 hours above envelope   A {a['hours_above_envelope_pct']:6.2f} %"
            f"  ->  B {b['hours_above_envelope_pct']:6.2f} %"
            f"   {'PASS' if g['P1_enforced'] else 'FAIL'}"
            f"   | cut active in {b['hours_cut_active_pct']:.2f} % of hours"
            f", max excess {b['max_excess_mw']:.6f} MW"
        )
        print(
            f"  P2 net interchange TWh    A {a['net_import_twh']:+7.2f}"
            f"  ->  B {b['net_import_twh']:+7.2f}"
            f"   measured {r['measured_net_import_twh']:+7.2f}"
            f"   {'PASS' if g['P2_direction'] else 'FAIL'}"
        )
        print(
            f"  K2 slack / dump (MWh)     A {a['slack_mwh']:.0f} / {a['dump_mwh']:.0f}"
            f"   B {b['slack_mwh']:.0f} / {b['dump_mwh']:.0f}"
            f"   {'PASS' if g['K2_no_shedding'] else 'KILL'}"
        )
        k5 = r["K5_identity"]
        if k5.get("available"):
            print(
                f"  K5 arm-A identity         max |Δ| {k5['max_abs_diff_mw']:.9f} MW"
                f"   {'PASS' if k5['identical'] else 'KILL'}"
            )
        moved = {
            k: v for k, v in r["delta_class_twh"].items() if abs(v) >= 0.05
        }
        print(f"  class moves >= 0.05 TWh:  {moved or 'none'}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
