"""caiso-124 A/B scorer: the hydro minimum-flow floor against its PRE-REGISTERED gates.

Reads two committed bundles' hourly sidecars + rubric metrics + legitimacy
diagnostics and scores exactly the gates written down BEFORE arm B solved
(``results/calibration/PREREG-caiso124-hydro-min-flow-floor-2026-07-26.md``).
No LP solve, no re-derivation: the bundles are the evidence.

Gates implemented, verbatim from the pre-registration:

* P1 parks-at-zero eliminated — hours < 10 MW → 0, hours < 100 MW → < 150/yr.
* P2 belly gap closes — |hod 9-15 hydro gap| <= 200 MW and strictly smaller
  than arm A's, every year.
* P3 shape does not degrade — diurnal profile r >= arm A's and the 24-hour
  profile MAE strictly falls, every year.
* P4 mechanism accounting is clean — a D-2 row for ``hydro_min_flow`` exists and
  its D-4 off-window share is exactly 0.
* K1 evening overshoot > +300 MW / K2 evening starvation < -600 MW / K3 shape
  degradation / K5 off-window binding — any one KILLS the delta.

S-series (regime-conditional, directional only) and the rubric verdict table are
REPORTED, never gated — the floor is judged on its own gates (rule 1).

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_caiso124_minflow_ab.py \
        --control results/calibration/caiso124_control_A \
        --arm results/calibration/caiso124_minflow_B
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2023, 2024, 2025)
BELLY = range(9, 16)  # hod 9-15, the solar-surplus belly
EVENING = range(17, 22)  # hod 17-21, the net-load peak

# Pre-registered thresholds (PREREG §3/§5) — never edited to make a gate pass.
P1_MAX_SUB10_HOURS = 0
P1_MAX_SUB100_HOURS = 150
P2_MAX_BELLY_GAP_MW = 200.0
K1_MAX_EVENING_OVERSHOOT_MW = 300.0
K2_MAX_EVENING_STARVATION_MW = 600.0


def hydro_hourly(bundle: Path, year: int) -> np.ndarray:
    """Return the bundle's P1 hydro-class hourly dispatch (MW), model clock."""
    path = bundle / "hourly" / f"class_hourly_{year}.parquet"
    frame = pd.read_parquet(path)
    rows = frame[(frame["klass"] == "hydro") & (frame["pass"] == "P1")]
    return rows.sort_values("hour")["mw"].to_numpy(dtype=float)


def measured_hydro(year: int, hours: int) -> np.ndarray:
    """Return measured EIA-930 ``NG: WAT`` on the model clock (MW)."""
    from market_sim.data.eia930.envelopes import _hydro_wat_month_hod

    frame = _hydro_wat_month_hod("CAISO", year)
    return frame["mw"].to_numpy(dtype=float)[:hours]


def profile(series: np.ndarray) -> np.ndarray:
    """Return the 24 hour-of-day means of an hourly series."""
    hod = np.arange(len(series)) % 24
    return np.array([np.nanmean(series[hod == h]) for h in range(24)])


def window_gap(model: np.ndarray, meas: np.ndarray, window: range) -> float:
    """Return mean(model) - mean(measured) over an hour-of-day window (MW)."""
    hod = np.arange(len(model)) % 24
    sel = np.isin(hod, list(window))
    return float(np.nanmean(model[sel]) - np.nanmean(meas[sel]))


def dispatch_stats(bundle: Path) -> dict:
    """Return per-year hydro dispatch statistics for one bundle."""
    out: dict[int, dict] = {}
    for year in YEARS:
        model = hydro_hourly(bundle, year)
        meas = measured_hydro(year, len(model))
        pm, pw = profile(model), profile(meas)
        out[year] = {
            "twh": model.sum() / 1e6,
            "sub10": int((model < 10.0).sum()),
            "sub100": int((model < 100.0).sum()),
            "p5": float(np.percentile(model, 5)),
            "belly_gap": window_gap(model, meas, BELLY),
            "evening_gap": window_gap(model, meas, EVENING),
            "profile_r": float(np.corrcoef(pm, pw)[0, 1]),
            "profile_mae": float(np.abs(pm - pw).mean()),
            "meas_twh": float(np.nansum(meas)) / 1e6,
        }
    return out


def diagnostics_rows(bundle: Path, mechanism: str = "hydro_min_flow") -> dict:
    """Return the D-2 / D-4 rows a bundle carries for one floor mechanism."""
    path = bundle / "legitimacy_diagnostics.json"
    if not path.is_file():
        return {"present": False}
    doc = json.loads(path.read_text())
    diag = doc.get("diagnostics", {})
    d2 = [
        r for r in diag.get("D2", {}).get("rows", []) if r.get("mechanism") == mechanism
    ]
    d4 = [r for r in diag.get("D4", {}).get("rows", []) if r.get("floor") == mechanism]
    return {"present": True, "d2": d2, "d4": d4}


def rubric(bundle: Path) -> dict:
    """Return the bundle's rubric criteria statuses and determination."""
    path = bundle / "metrics.json"
    if not path.is_file():
        return {}
    doc = json.loads(path.read_text())
    return {
        "determination": doc.get("determination"),
        "criteria": {k: v.get("status") for k, v in doc.get("criteria", {}).items()},
    }


def main() -> None:
    """Score the A/B against the pre-registered gates and print the verdict."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", required=True, help="arm A bundle (no delta)")
    ap.add_argument("--arm", required=True, help="arm B bundle (floor on)")
    ap.add_argument("--json-out", default=None, help="write the scored dict here")
    args = ap.parse_args()

    a_dir, b_dir = Path(args.control), Path(args.arm)
    a, b = dispatch_stats(a_dir), dispatch_stats(b_dir)

    print("=== hydro dispatch, arm A (control) vs arm B (min-flow floor) ===")
    hdr = (
        f"{'year':>5} {'arm':>4} {'TWh':>6} {'<10h':>6} {'<100h':>6} {'p5':>6} "
        f"{'belly':>7} {'even':>7} {'prof_r':>7} {'prof_MAE':>8}"
    )
    print(hdr)
    for year in YEARS:
        for tag, stats in (("A", a), ("B", b)):
            s = stats[year]
            print(
                f"{year:>5} {tag:>4} {s['twh']:>6.2f} {s['sub10']:>6d} "
                f"{s['sub100']:>6d} {s['p5']:>6.0f} {s['belly_gap']:>+7.0f} "
                f"{s['evening_gap']:>+7.0f} {s['profile_r']:>7.3f} "
                f"{s['profile_mae']:>8.0f}"
            )

    failures: list[str] = []
    kills: list[str] = []
    for year in YEARS:
        sa, sb = a[year], b[year]
        if sb["sub10"] > P1_MAX_SUB10_HOURS:
            failures.append(f"P1 {year}: {sb['sub10']} h below 10 MW (need 0)")
        if sb["sub100"] > P1_MAX_SUB100_HOURS:
            failures.append(
                f"P1 {year}: {sb['sub100']} h below 100 MW "
                f"(need < {P1_MAX_SUB100_HOURS})"
            )
        if abs(sb["belly_gap"]) > P2_MAX_BELLY_GAP_MW:
            failures.append(
                f"P2 {year}: belly gap {sb['belly_gap']:+.0f} MW exceeds "
                f"±{P2_MAX_BELLY_GAP_MW:.0f}"
            )
        if abs(sb["belly_gap"]) >= abs(sa["belly_gap"]):
            failures.append(
                f"P2 {year}: belly gap not improved vs control "
                f"({sb['belly_gap']:+.0f} vs {sa['belly_gap']:+.0f} MW)"
            )
        if sb["profile_mae"] >= sa["profile_mae"]:
            failures.append(
                f"P3 {year}: profile MAE did not fall "
                f"({sb['profile_mae']:.0f} vs {sa['profile_mae']:.0f} MW)"
            )
        if sb["profile_r"] < sa["profile_r"]:
            kills.append(
                f"K3 {year}: diurnal r fell {sa['profile_r']:.3f} -> "
                f"{sb['profile_r']:.3f}"
            )
        if sb["evening_gap"] > K1_MAX_EVENING_OVERSHOOT_MW:
            kills.append(
                f"K1 {year}: evening overshoot {sb['evening_gap']:+.0f} MW "
                f"> +{K1_MAX_EVENING_OVERSHOOT_MW:.0f}"
            )
        if sb["evening_gap"] < -K2_MAX_EVENING_STARVATION_MW:
            kills.append(
                f"K2 {year}: evening starvation {sb['evening_gap']:+.0f} MW "
                f"< -{K2_MAX_EVENING_STARVATION_MW:.0f}"
            )

    print("\n=== P4 mechanism accounting (D-2 / D-4, arm B) ===")
    diag = diagnostics_rows(b_dir)
    if not diag["present"]:
        failures.append("P4: arm B carries no legitimacy_diagnostics.json")
    else:
        if not diag["d2"]:
            failures.append("P4: no D-2 row for hydro_min_flow (mechanism unwired?)")
        for row in diag["d2"]:
            print(
                f"  D-2 {row['year']} class={row['class']!r} "
                f"forced={row['forced_twh']} TWh "
                f"share_of_class={row['share_of_class']}"
            )
        if not diag["d4"]:
            failures.append("P4: no D-4 row for hydro_min_flow")
        for row in diag["d4"]:
            print(
                f"  D-4 {row['year']} window={row['window']} "
                f"floored={row['floored_twh']} TWh "
                f"offwindow_share={row['offwindow_share']} ({row['verdict']})"
            )
            if float(row["offwindow_share"]) != 0.0:
                kills.append(
                    f"K5 {row['year']}: off-window binding share "
                    f"{row['offwindow_share']} (window is all-hours — wiring bug)"
                )

    print("\n=== rubric (REPORTED, not gated for this delta — rule 1) ===")
    ra, rb = rubric(a_dir), rubric(b_dir)
    keys = sorted(set(ra.get("criteria", {})) | set(rb.get("criteria", {})))
    print(f"  determination  A={ra.get('determination')}  B={rb.get('determination')}")
    for key in keys:
        sa = ra.get("criteria", {}).get(key, "-")
        sb = rb.get("criteria", {}).get(key, "-")
        flag = "  <-- moved" if sa != sb else ""
        print(f"  {key:<14} A={sa:<5} B={sb:<5}{flag}")

    print("\n=== VERDICT ===")
    if kills:
        print("KILLED — pre-registered kill criterion tripped:")
        for k in kills:
            print(f"  * {k}")
    if failures:
        print("PRIMARY GATE FAILURES:")
        for f in failures:
            print(f"  * {f}")
    if not kills and not failures:
        print("ALL PRE-REGISTERED PRIMARY GATES PASS, no kill criterion tripped.")
    print(
        "(Promotion is an OWNER call regardless — PREREG §6. Arm A is never "
        "registered.)"
    )

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(
                {
                    "control": str(a_dir),
                    "arm": str(b_dir),
                    "stats_A": {str(k): v for k, v in a.items()},
                    "stats_B": {str(k): v for k, v in b.items()},
                    "diagnostics_B": diag,
                    "rubric_A": ra,
                    "rubric_B": rb,
                    "failures": failures,
                    "kills": kills,
                },
                indent=1,
            )
        )


if __name__ == "__main__":
    main()
