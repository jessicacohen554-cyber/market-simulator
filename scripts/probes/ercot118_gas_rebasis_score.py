"""ERCOT-118 scorer: the EP-rebasis joint arm's pre-committed yardsticks.

Scores the ERCOT-118 arm (EP-basis CC band-multiplier rebasis + measured coal
DAM envelope on the ercot115 keeper) against the criteria fixed in
``results/calibration/PRECOMMIT-ercot118-gas-rebasis-2026-07-26.md`` BEFORE
any arm year was solved. Complements — never replaces — the pinned
``ercot116_seasonal_shape.py`` gates, which are run verbatim alongside.

* **PRIMARY (pre-registered)** — the ERCOT-117 probe-§F crossing-band price
  formation: the arm's load-weighted ORDC-inclusive price minus actual inside
  actual-price band [15,25) must fall to <= $2.0 in EVERY year, with C3c
  within +/-5 h of the keeper and C1 (all + free pass counts from the rubric
  ``metrics.json``) not degraded.
* **G3-TRAP decomposition** — ERCOT-117 proved the keeper's annual C3a nets a
  mid-merit-HIGH error against a scarcity-LOW error, so a CORRECT mid-merit
  fix will likely push C3a-vs-keeper past the two-sided 2.0 pp tolerance.
  This decomposes the arm-minus-keeper C3a delta, per year, into the
  actual-$[10,40) leg (the mid-merit body the rebasis targets) and the
  remainder (the tail leg), and reports whether the $10-40-band model price
  moved TOWARD actual — the pre-declared ESCALATE-TO-OWNER pattern is
  "G3 fails SOLELY via C3a, with the delta carried by the mid-merit leg
  moving toward actual"; any other failure mode is an ordinary rejection.

All model series come from committed ``hourly/`` sidecars (rule 15 — no
re-solve); the price constructions are imported from the ERCOT-112/117 probe
scripts verbatim so every number is directly comparable to the published
ones.

Usage:
    python scripts/probes/ercot118_gas_rebasis_score.py \
        --keeper results/calibration/ercot115_coal_floor_only \
        --arm    results/calibration/ercot118_ep_rebasis_joint \
        [--also results/calibration/ercot116_coal_avail_on_keeper \
                results/calibration/ercot117_gas_basis_probe]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from ercot112_score_coal_arms import _actual_price, _system_price, year_row  # noqa: E402
from ercot117_coal_gas_ranking import crossing_band_prices  # noqa: E402

YEARS = (2023, 2024, 2025)

# Pre-committed thresholds — fixed in the ERCOT-118 pre-commit, never re-tuned.
_PRIMARY_MAX_ELEVATION_USD = 2.0  # [15,25) model-minus-actual, every year
_C3C_MAX_DEGRADE_HOURS = 5
_MIDMERIT_BAND = (10.0, 40.0)  # the G3-trap decomposition's mid-merit leg


def crossing_elevation(bundle: Path, year: int) -> float | None:
    """Model-minus-actual mean price in the actual-$[15,25) band."""
    t = crossing_band_prices(bundle, year)
    if t is None:
        return None
    row = t.loc["[15,25)"]
    return float(row["model_mean"] - row["actual_mean"])


def c3a_decomposition(keeper: Path, arm: Path, year: int) -> dict | None:
    """Split the arm-minus-keeper C3a delta into mid-merit vs tail legs.

    C3a = (mean(model) / mean(actual) - 1) x 100 (the pinned ercot112 form),
    so the arm-minus-keeper delta decomposes exactly over hour subsets:
    ``delta_pp(S) = sum_S(arm - keeper) / (8760 x mean(actual)) x 100``.
    The mid-merit leg is hours with actual price in [10,40); the tail leg is
    every other hour. Also reports the [10,40)-band model means of both
    bundles against actual, so "moved toward actual" is a printed fact.
    """
    kp, ap_ = _system_price(keeper, year), _system_price(arm, year)
    act = _actual_price(year)
    if kp is None or ap_ is None or act is None:
        return None
    n = min(len(kp), len(ap_), len(act))
    kp, ap_, act = kp[:n], ap_[:n], act[:n]
    ok = np.isfinite(kp) & np.isfinite(ap_) & np.isfinite(act)
    kp, ap_, act = kp[ok], ap_[ok], act[ok]
    mid = (act >= _MIDMERIT_BAND[0]) & (act < _MIDMERIT_BAND[1])
    denom = act.mean() * len(act)
    d = ap_ - kp
    return {
        "c3a_keeper": float((kp.mean() / act.mean() - 1.0) * 100.0),
        "c3a_arm": float((ap_.mean() / act.mean() - 1.0) * 100.0),
        "d_c3a_total_pp": float(d.sum() / denom * 100.0),
        "d_c3a_midmerit_pp": float(d[mid].sum() / denom * 100.0),
        "d_c3a_tail_pp": float(d[~mid].sum() / denom * 100.0),
        "midmerit_hours": int(mid.sum()),
        "band_actual_mean": float(act[mid].mean()),
        "band_keeper_mean": float(kp[mid].mean()),
        "band_arm_mean": float(ap_[mid].mean()),
        "band_moved_toward_actual": bool(
            abs(ap_[mid].mean() - act[mid].mean())
            < abs(kp[mid].mean() - act[mid].mean())
        ),
    }


def c1_counts(bundle: Path) -> tuple[int, int, int, int] | None:
    """(all_pass, all_total, free_pass, free_total) from the rubric metrics."""
    path = bundle / "metrics.json"
    if not path.exists():
        return None
    fcs = json.loads(path.read_text()).get("free_class_score") or {}
    a, f = fcs.get("all") or {}, fcs.get("free") or {}
    if "pass" not in a:
        return None
    return int(a["pass"]), int(a["total"]), int(f["pass"]), int(f["total"])


def main() -> None:
    """Score the arm and print the pre-committed ERCOT-118 verdicts."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keeper", required=True, type=Path)
    ap.add_argument("--arm", required=True, type=Path)
    ap.add_argument(
        "--also",
        nargs="*",
        type=Path,
        default=[],
        help="extra on-disk bundles to print the crossing table for "
        "(the ercot116 envelope arm and the ercot117 probe)",
    )
    args = ap.parse_args()
    pd.set_option("display.width", 240)

    bundles = [("keeper", args.keeper)] + [
        (p.name, p) for p in args.also
    ] + [("ARM", args.arm)]

    print("=== §F crossing-band elevation (model - actual, $ in actual-price bands) ===")
    rows = []
    for label, b in bundles:
        for year in YEARS:
            t = crossing_band_prices(b, year)
            if t is None:
                continue
            rows.append(
                {
                    "bundle": label,
                    "year": year,
                    "elev_10_15": float(
                        t.loc["[10,15)", "model_mean"] - t.loc["[10,15)", "actual_mean"]
                    ),
                    "elev_15_25": float(
                        t.loc["[15,25)", "model_mean"] - t.loc["[15,25)", "actual_mean"]
                    ),
                    "elev_25_40": float(
                        t.loc["[25,40)", "model_mean"] - t.loc["[25,40)", "actual_mean"]
                    ),
                    "h_15_25": int(t.loc["[15,25)", "hours"]),
                }
            )
    table = pd.DataFrame(rows).set_index(["bundle", "year"])
    print(table.round(2).to_string())

    print("\n=== PRIMARY yardstick (pre-registered) ===")
    primary_ok = True
    for year in YEARS:
        e = crossing_elevation(args.arm, year)
        ok = e is not None and e <= _PRIMARY_MAX_ELEVATION_USD
        primary_ok &= bool(ok)
        print(
            f"  {year}: [15,25) elevation {e:+.2f} $ "
            f"(<= {_PRIMARY_MAX_ELEVATION_USD:.1f}): {'PASS' if ok else 'FAIL'}"
        )
    c3c_ok = True
    for year in YEARS:
        kr, ar = year_row(args.keeper, year), year_row(args.arm, year)
        if kr is None or ar is None or kr["c3c"] is None:
            c3c_ok = False
            print(f"  {year}: C3c unavailable")
            continue
        ok = abs(ar["c3c"] - kr["c3c"]) <= _C3C_MAX_DEGRADE_HOURS
        c3c_ok &= bool(ok)
        print(
            f"  {year}: C3c keeper {kr['c3c']} -> arm {ar['c3c']} "
            f"(act {kr['c3c_act']}; +/-{_C3C_MAX_DEGRADE_HOURS} h): "
            f"{'PASS' if ok else 'FAIL'}"
        )
    kc1, ac1 = c1_counts(args.keeper), c1_counts(args.arm)
    if kc1 is None or ac1 is None:
        c1_ok = False
        print("  C1: metrics.json missing/unscored on one side — FAIL (report)")
    else:
        c1_ok = ac1[0] >= kc1[0] and ac1[2] >= kc1[2]
        print(
            f"  C1: keeper {kc1[0]}/{kc1[1]} free {kc1[2]}/{kc1[3]} -> "
            f"arm {ac1[0]}/{ac1[1]} free {ac1[2]}/{ac1[3]}: "
            f"{'PASS' if c1_ok else 'FAIL'}"
        )
    print(
        f"  PRIMARY: {'PASS' if (primary_ok and c3c_ok and c1_ok) else 'FAIL'}"
        "  (elevation + C3c + C1 legs above)"
    )

    print("\n=== G3-trap C3a decomposition (arm vs keeper) ===")
    for year in YEARS:
        d = c3a_decomposition(args.keeper, args.arm, year)
        if d is None:
            print(f"  {year}: sidecars unavailable")
            continue
        print(
            f"  {year}: C3a {d['c3a_keeper']:+.1f} -> {d['c3a_arm']:+.1f} pp "
            f"(delta {d['d_c3a_total_pp']:+.2f} = mid-merit "
            f"{d['d_c3a_midmerit_pp']:+.2f} + tail {d['d_c3a_tail_pp']:+.2f}); "
            f"$[10,40) model {d['band_keeper_mean']:.2f} -> "
            f"{d['band_arm_mean']:.2f} vs actual {d['band_actual_mean']:.2f} "
            f"({'TOWARD' if d['band_moved_toward_actual'] else 'AWAY'})"
        )
    print(
        "\n  (Pre-declared: G3 failing SOLELY via C3a with the delta carried "
        "by the mid-merit leg moving TOWARD actual = ESCALATE-TO-OWNER, not "
        "a revert signal. Any other G3 failure mode = ordinary rejection.)"
    )


if __name__ == "__main__":
    main()
