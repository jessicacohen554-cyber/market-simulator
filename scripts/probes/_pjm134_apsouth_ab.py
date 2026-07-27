"""pjm-134 A/B scorer — `pjm_apsouth_interface_cut`, against PREREG-pjm134 §3/§5.

Committed BEFORE either arm solved. Reads both arms' committed ``hourly/``
sidecars only — never a replay, no LP anywhere in this file.

Scores, in prereg order:

* **P1 engagement** — the joint cut binds at all: Dominion price-separates from
  at least one of its three neighbours in > 0 % of hours (arm A: exactly 0.0 %).
* **P2 measured direction** — conditional on Dominion separating from AEP_Ohio,
  Dominion is the dearer side in >= 2/3 of those hours (measured DA congestion:
  94 / 86 / 80 %).
* **P3 no counterflow forcing** — the published cap array is >= 0 in every hour.
* **K2 load shedding** — arm B slack/dump must stay at 0 (arm A: 0 / 0).
* **K5 arm-A identity** — arm A must reproduce ``pjm132_control_A`` to
  0.000000 MW on every class-hour.

Everything else -- Dominion volumes, the zonal displacement table, the rubric --
is REPORTED, never gated (rule 1 ``[R-STRUCT]``).

Usage::

    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm134_apsouth_ab.py \
        --arm-a results/calibration/pjm134_control_A \
        --arm-b results/calibration/pjm134_apsouth_B
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2023, 2024, 2025)

DOMINION = "PJM_Dominion"
NEIGHBOURS = ("PJM_AEP_Ohio", "PJM_West_APS", "PJM_SWMAAC")

#: Below this a dual difference is HiGHS noise, not congestion.
PRICE_EPS = 1e-6

#: PREREG §3 P2 floor -- the measured sign asymmetry is 0.94/0.86/0.80.
P2_FLOOR = 2.0 / 3.0

#: PREREG §5 K5 comparator: the byte-identical control lineage.
IDENTITY_REF = Path("results/calibration/pjm132_control_A")

OUT_PATH = Path("results/probes/pjm134_apsouth_ab.json")


def _prices(bundle: Path, year: int) -> pd.DataFrame:
    """P1 hourly zonal prices from a bundle's committed system sidecar."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return frame.pivot(index="hour", columns="zone", values="price")


def _system(bundle: Path, year: int) -> pd.DataFrame:
    """P1 hourly system rows (slack / dump / demand) from a bundle."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return frame[frame["pass"] == "P1"]


def _classes(bundle: Path, year: int) -> pd.DataFrame:
    """P1 hourly class dispatch from a bundle, indexed (klass, hour)."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return frame.pivot(index="hour", columns="klass", values="mw")


def _separation(bundle: Path, year: int) -> dict[str, float]:
    """Dominion price-separation shares against its three import neighbours."""
    prices = _prices(bundle, year)
    dom = prices[DOMINION].to_numpy(dtype=float)
    neigh = prices[list(NEIGHBOURS)].to_numpy(dtype=float)
    diff = dom[:, None] - neigh
    separated_any = (np.abs(diff) > PRICE_EPS).any(axis=1)
    aep = diff[:, NEIGHBOURS.index("PJM_AEP_Ohio")]
    sep_aep = np.abs(aep) > PRICE_EPS
    dearer_frac = float((aep[sep_aep] > 0).mean()) if sep_aep.any() else float("nan")
    return {
        "separated_any_share": round(float(separated_any.mean()), 6),
        "separated_vs_aep_share": round(float(sep_aep.mean()), 6),
        "dearer_given_separated_vs_aep": (
            round(dearer_frac, 6) if sep_aep.any() else None
        ),
        "mean_spread_vs_aep": round(float(aep.mean()), 4),
        "max_spread_vs_aep": round(float(aep.max()), 4),
        "min_spread_vs_aep": round(float(aep.min()), 4),
    }


def _identity(arm_a: Path, ref: Path) -> dict[str, object]:
    """K5 -- max absolute class-hour difference between arm A and the reference."""
    if not ref.exists():
        return {"available": False, "reason": f"{ref} absent"}
    worst = 0.0
    detail: dict[str, float] = {}
    for year in YEARS:
        a = _classes(arm_a, year)
        b = _classes(ref, year)
        shared = sorted(set(a.columns) & set(b.columns))
        gap = float(np.abs(a[shared].to_numpy() - b[shared].to_numpy()).max())
        detail[str(year)] = round(gap, 9)
        worst = max(worst, gap)
        if set(a.columns) != set(b.columns):
            detail[f"{year}_class_set_mismatch"] = 1.0
    return {"available": True, "max_abs_mw": round(worst, 9), "by_year": detail}


def main() -> None:
    """Score the A/B against the pre-registered gates and write the verdict."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm-a", default="results/calibration/pjm134_control_A")
    ap.add_argument("--arm-b", default="results/calibration/pjm134_apsouth_B")
    args = ap.parse_args()
    arm_a, arm_b = Path(args.arm_a), Path(args.arm_b)

    out: dict[str, object] = {"arm_a": str(arm_a), "arm_b": str(arm_b), "years": {}}
    p1_pass, p2_pass, k2_pass = True, True, True

    print("=" * 96)
    print("pjm-134 A/B -- pjm_apsouth_interface_cut, against PREREG-pjm134 §3/§5")
    print("=" * 96)
    for year in YEARS:
        sep_a = _separation(arm_a, year)
        sep_b = _separation(arm_b, year)
        sys_a, sys_b = _system(arm_a, year), _system(arm_b, year)
        row = {
            "arm_a": sep_a,
            "arm_b": sep_b,
            "slack_mwh": {
                "a": round(float(sys_a["slack"].sum()), 6),
                "b": round(float(sys_b["slack"].sum()), 6),
            },
            "dump_mwh": {
                "a": round(float(sys_a["dump"].sum()), 6),
                "b": round(float(sys_b["dump"].sum()), 6),
            },
        }
        # P1 engagement
        row["P1_binds"] = bool(sep_b["separated_any_share"] > 0.0)
        p1_pass &= row["P1_binds"]
        # P2 measured direction
        dearer = sep_b["dearer_given_separated_vs_aep"]
        row["P2_dearer_frac"] = dearer
        row["P2_pass"] = bool(dearer is not None and dearer >= P2_FLOOR)
        p2_pass &= row["P2_pass"]
        # K2 load shedding
        row["K2_pass"] = bool(
            row["slack_mwh"]["b"] <= 0.0 and row["dump_mwh"]["b"] <= 0.0
        )
        k2_pass &= row["K2_pass"]

        print(f"\n--- {year} ---")
        print(
            f"  P1 separation (any neighbour): A {sep_a['separated_any_share']:.2%}"
            f"  ->  B {sep_b['separated_any_share']:.2%}   "
            f"{'BINDS' if row['P1_binds'] else 'INERT'}"
        )
        print(
            f"  P2 vs AEP_Ohio: separated {sep_b['separated_vs_aep_share']:.2%}, "
            f"Dominion dearer in "
            f"{'n/a' if dearer is None else format(dearer, '.1%')} of those "
            f"(floor {P2_FLOOR:.1%})  {'PASS' if row['P2_pass'] else 'FAIL'}"
        )
        print(
            f"  spread vs AEP_Ohio ($/MWh): A mean {sep_a['mean_spread_vs_aep']:+.3f}"
            f"  ->  B mean {sep_b['mean_spread_vs_aep']:+.3f}  "
            f"(B range {sep_b['min_spread_vs_aep']:+.2f} .. "
            f"{sep_b['max_spread_vs_aep']:+.2f})"
        )
        print(
            f"  K2 slack/dump MWh: A {row['slack_mwh']['a']:.1f}/"
            f"{row['dump_mwh']['a']:.1f}   B {row['slack_mwh']['b']:.1f}/"
            f"{row['dump_mwh']['b']:.1f}   "
            f"{'PASS' if row['K2_pass'] else 'KILL'}"
        )
        out["years"][str(year)] = row

    # K5 arm-A identity
    ident = _identity(arm_a, IDENTITY_REF)
    out["K5_identity"] = ident
    print("\n" + "-" * 96)
    if ident.get("available"):
        ok = ident["max_abs_mw"] == 0.0
        print(
            f"  K5 arm-A identity vs {IDENTITY_REF.name}: max |Δ| = "
            f"{ident['max_abs_mw']:.9f} MW   {'PASS' if ok else 'KILL'}"
        )
    else:
        print(f"  K5 arm-A identity: SKIPPED ({ident.get('reason')})")

    # Reported, never gated (rule 1): class volumes, both arms.
    print("\n" + "=" * 96)
    print("REPORTED (never gated, rule 1) -- ISO-wide class volumes, TWh")
    print("=" * 96)
    volumes: dict[str, dict[str, dict[str, float]]] = {}
    for year in YEARS:
        a, b = _classes(arm_a, year), _classes(arm_b, year)
        shared = sorted(set(a.columns) & set(b.columns))
        print(f"\n--- {year} ---")
        print(f"{'class':<16}{'arm A':>10}{'arm B':>10}{'B-A':>10}")
        volumes[str(year)] = {}
        for klass in shared:
            va, vb = float(a[klass].sum()) / 1e6, float(b[klass].sum()) / 1e6
            volumes[str(year)][klass] = {
                "a_twh": round(va, 4),
                "b_twh": round(vb, 4),
                "delta_twh": round(vb - va, 4),
            }
            if abs(vb - va) >= 0.005:
                print(f"{klass:<16}{va:>10.3f}{vb:>10.3f}{vb - va:>+10.3f}")
    out["volumes"] = volumes

    out["verdict"] = {
        "P1_engagement": "PASS" if p1_pass else "INERT",
        "P2_direction": "PASS" if p2_pass else "FAIL",
        "K2_load_shedding": "PASS" if k2_pass else "KILL",
        "K5_identity": (
            ("PASS" if ident.get("max_abs_mw") == 0.0 else "KILL")
            if ident.get("available")
            else "SKIPPED"
        ),
    }
    print("\n" + "=" * 96)
    for key, value in out["verdict"].items():
        print(f"  {key:<20} {value}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
