"""caiso-163 A/B gate reader: liveness on FLOWS + the primary structural gates.

Reads the two committed-bundle sidecars (``flows.parquet`` and
``hourly/system_<year>.parquet``) for the control and treatment arms and reports
every gate registered in
``results/calibration/PRECHECK-caiso163-asymmetric-path-ratings-2026-08-03.md``
§4. No LP, no solve, no writes.

Why flows and not prices (the caiso-162 lesson): a mechanism that never executed
reads on prices as a clean INERT verdict and would write a FALSE matrix ``I``, a
DO-NOT-REDO code. The liveness gates below are therefore asserted directly on
the realised link flows against the published WECC directional ratings.

Usage::

    PYTHONPATH=.:src python scripts/probes/caiso163_ab_gates.py [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CONTROL = REPO / "results/calibration/caiso163_control_A"
ARM = REPO / "results/calibration/caiso163_asym_path_ratings"
YEARS = (2023, 2024, 2025)
TOL = 1e-6

# Published WECC Path Rating Catalog directional ratings, keyed by the model
# link orientation (from, to) = the listed N->S direction:
# (N->S cap, S->N cap). Mirrors interchange.caiso.CAISO_PATH_DIRECTIONAL_RATINGS
# — listed here only to be ASSERTED against realised flows, never applied.
PATHS = {
    "Path15": (("NP15", "ZP26"), 3265.0, 5400.0),
    "Path26": (("ZP26", "SP15_rest"), 4000.0, 3000.0),
}

# Measured CAISO DAM hub basis (TH_*_GEN-APND), mean $/MWh, computed this
# session from data/raw/lmp-data/CAISO/CAISO_dam_hourly_<y>.csv. The target the
# structural gates are read against — never applied to anything.
ACTUAL = {
    2023: {"np15_zp26": 5.947, "np15_sp15": 2.337, "hrs_np15_ne_zp26_pct": 99.5},
    2024: {"np15_zp26": 8.576, "np15_sp15": 7.992, "hrs_np15_ne_zp26_pct": 99.9},
    2025: {"np15_zp26": 5.727, "np15_sp15": 6.009, "hrs_np15_ne_zp26_pct": 100.0},
}


def directional_flow(bundle: Path, year: int, pair: tuple[str, str]) -> np.ndarray:
    """Return the signed hourly P1 flow on ``pair`` (+ = listed N->S direction).

    Sums every link joining the two zones with the sign of its own orientation,
    matching ``interchange.core.build_interface_groups`` — so a one-way link
    pair reads as the net corridor flow in the listed direction.
    """
    f = pd.read_parquet(bundle / "flows.parquet")
    f = f[(f["pass"] == "P1") & (f["year"] == year)]
    a, b = pair
    fwd = f[(f["from_zone"] == a) & (f["to_zone"] == b)]
    rev = f[(f["from_zone"] == b) & (f["to_zone"] == a)]
    idx = "hour"
    net = fwd.groupby(idx)["mw"].sum()
    if len(rev):
        net = net.subtract(rev.groupby(idx)["mw"].sum(), fill_value=0.0)
    return net.sort_index().to_numpy(dtype=float)


def zone_prices(bundle: Path, year: int) -> pd.DataFrame:
    """Return the P1 hour x zone price frame for ``year``."""
    d = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return d.pivot_table(index="hour", columns="zone", values="price")


def load_weighted_lambda(bundle: Path, year: int) -> float:
    """Return the P1 load-weighted mean LMP for ``year``."""
    d = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    price = d.pivot_table(index="hour", columns="zone", values="price")
    load = d.pivot_table(index="hour", columns="zone", values="demand")
    zones = [z for z in price.columns if load[z].sum() > 0]
    total = sum(load[z].sum() for z in zones)
    return float(sum((price[z] * load[z]).sum() for z in zones) / total)


def main() -> int:
    """Print every caiso-163 gate for both arms; return 1 if L2 is violated."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", default=None, help="also write the report here")
    args = ap.parse_args()

    report: dict = {"liveness": {}, "structural": {}, "lambda": {}}
    l2_violation = False

    print("=" * 78)
    print("L1/L2/L3 — LIVENESS ON FLOWS (published WECC directional ratings)")
    print("=" * 78)
    for name, (pair, ns_cap, sn_cap) in PATHS.items():
        for year in YEARS:
            ctl = directional_flow(CONTROL, year, pair)
            trt = directional_flow(ARM, year, pair)
            row = {
                "pair": f"{pair[0]}->{pair[1]}",
                "ns_cap_mw": ns_cap,
                "sn_cap_mw": sn_cap,
                "control_max_ns_mw": round(float(ctl.max()), 2),
                "control_max_sn_mw": round(float((-ctl).max()), 2),
                "arm_max_ns_mw": round(float(trt.max()), 2),
                "arm_max_sn_mw": round(float((-trt).max()), 2),
                "control_hrs_over_ns_cap": int((ctl > ns_cap + TOL).sum()),
                "control_hrs_over_sn_cap": int((-ctl > sn_cap + TOL).sum()),
                "arm_hrs_over_ns_cap": int((trt > ns_cap + TOL).sum()),
                "arm_hrs_over_sn_cap": int((-trt > sn_cap + TOL).sum()),
                "arm_hrs_at_ns_cap": int((np.abs(trt - ns_cap) < 1e-3).sum()),
                "arm_hrs_at_sn_cap": int((np.abs(-trt - sn_cap) < 1e-3).sum()),
            }
            if row["arm_hrs_over_ns_cap"] or row["arm_hrs_over_sn_cap"]:
                l2_violation = True
            report["liveness"][f"{name}_{year}"] = row
            print(
                f"{name} {year}: control max N->S {row['control_max_ns_mw']:>8.1f} "
                f"(cap {ns_cap:.0f}, over {row['control_hrs_over_ns_cap']} h) | "
                f"S->N {row['control_max_sn_mw']:>8.1f} (cap {sn_cap:.0f}, over "
                f"{row['control_hrs_over_sn_cap']} h)"
            )
            print(
                f"{' ':>12} arm     max N->S {row['arm_max_ns_mw']:>8.1f} "
                f"(over {row['arm_hrs_over_ns_cap']} h, AT cap "
                f"{row['arm_hrs_at_ns_cap']} h) | S->N {row['arm_max_sn_mw']:>8.1f} "
                f"(over {row['arm_hrs_over_sn_cap']} h, AT cap "
                f"{row['arm_hrs_at_sn_cap']} h)"
            )

    print()
    print("=" * 78)
    print("S1-S4 — PRIMARY STRUCTURAL GATES (model vs measured DAM hub basis)")
    print("=" * 78)
    for year in YEARS:
        pc, pa = zone_prices(CONTROL, year), zone_prices(ARM, year)
        row = {}
        for label, p in (("control", pc), ("arm", pa)):
            sep = (p["NP15"] - p["ZP26"]).abs() > 0.01
            row[label] = {
                "hrs_np15_ne_zp26": int(sep.sum()),
                "pct_np15_ne_zp26": round(100.0 * float(sep.mean()), 3),
                "mean_np15_minus_zp26": round(float((p["NP15"] - p["ZP26"]).mean()), 3),
                "mean_np15_minus_sp15": round(
                    float((p["NP15"] - p["SP15_rest"]).mean()), 3
                ),
                "byte_identical_np15_zp26": bool(
                    np.allclose(p["NP15"], p["ZP26"], atol=1e-9)
                ),
            }
        row["actual"] = ACTUAL[year]
        report["structural"][str(year)] = row
        print(
            f"{year} S1 hours NP15!=ZP26: control "
            f"{row['control']['hrs_np15_ne_zp26']} "
            f"({row['control']['pct_np15_ne_zp26']}%) -> arm "
            f"{row['arm']['hrs_np15_ne_zp26']} ({row['arm']['pct_np15_ne_zp26']}%) "
            f"| ACTUAL {ACTUAL[year]['hrs_np15_ne_zp26_pct']}%"
        )
        print(
            f"{year} S2 NP15==ZP26 byte-identical: control "
            f"{row['control']['byte_identical_np15_zp26']} -> arm "
            f"{row['arm']['byte_identical_np15_zp26']}"
        )
        print(
            f"{year} S3 mean NP15-ZP26: control "
            f"{row['control']['mean_np15_minus_zp26']:+.3f} -> arm "
            f"{row['arm']['mean_np15_minus_zp26']:+.3f} | ACTUAL "
            f"{ACTUAL[year]['np15_zp26']:+.3f}"
        )
        print(
            f"{year} S4 mean NP15-SP15: control "
            f"{row['control']['mean_np15_minus_sp15']:+.3f} -> arm "
            f"{row['arm']['mean_np15_minus_sp15']:+.3f} | ACTUAL "
            f"{ACTUAL[year]['np15_sp15']:+.3f}"
        )

    print()
    print("=" * 78)
    print("LOAD-WEIGHTED LAMBDA (reported plainly, not leaned on)")
    print("=" * 78)
    for year in YEARS:
        c, a = load_weighted_lambda(CONTROL, year), load_weighted_lambda(ARM, year)
        report["lambda"][str(year)] = {
            "control": round(c, 4),
            "arm": round(a, 4),
            "delta": round(a - c, 4),
            "pct_of_level": round(100.0 * (a - c) / c, 4),
        }
        print(f"{year}: {c:.4f} -> {a:.4f} ({100.0 * (a - c) / c:+.4f}% of level)")

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=1))

    if l2_violation:
        print("\nFATAL (L2): a flow exceeded a published cap in the TREATMENT arm.")
        return 1
    print("\nL2 PASS: no treatment-arm flow exceeds a published directional cap.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
