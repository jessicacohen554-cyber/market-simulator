"""caiso-164 A/B gate reader — every gate the PRECHECK pre-registered.

Reads the two same-HEAD bundles and prints L1-L3 (liveness, on FLOWS and the
loss array — never on prices), S1-S4 (the structural quantity under test), and
the load-weighted price level. The measured targets are computed from
``data/raw/lmp-data/CAISO/CAISO_dam_hourly_<y>.csv`` and are REPORTED AGAINST,
never applied to anything (rules 1 / 13).

Exit code 1 if L3 is violated (a treatment hour over a published caiso-163
directional rating) or if S2's ceiling is breached (the basis moves further
than the measured loss component can explain, which would mean the mechanism is
doing something other than representing losses).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CONTROL = REPO / "results/calibration/caiso164_control_lossless"
ARM = REPO / "results/calibration/caiso164_zonal_loss_surface"
YEARS = (2023, 2024, 2025)
TOL = 1e-6
SEP_TOL = 0.01

# The caiso-163 published WECC directional ratings, keyed by the model link
# orientation (from, to) = the listed N->S direction: (N->S cap, S->N cap).
# Listed only to be ASSERTED against realised flows, never applied.
PATHS = {
    "Path15": (("NP15", "ZP26"), 3265.0, 5400.0),
    "Path26": (("ZP26", "SP15_rest"), 4000.0, 3000.0),
}

# Measured CAISO DAM hub basis and its LOSS component (TH_*_GEN-APND), mean
# $/MWh, computed by scripts/probes/caiso164_ns_basis_decomp.py. S2's ceiling
# is the dMCL column: the mechanism represents losses, so it may not move the
# basis by more than the measured loss component.
ACTUAL = {
    2023: {"np15_zp26": 5.947, "np15_zp26_dmcl": 1.176, "np15_sp15": 2.337},
    2024: {"np15_zp26": 8.576, "np15_zp26_dmcl": 1.102, "np15_sp15": 7.992},
    2025: {"np15_zp26": 5.727, "np15_zp26_dmcl": 1.049, "np15_sp15": 6.009},
}


def directional_flow(bundle: Path, year: int, pair: tuple[str, str]) -> np.ndarray:
    """Return the signed hourly P1 flow on ``pair`` (+ = listed N->S direction).

    Sums every link joining the two zones with the sign of its own orientation,
    matching ``interchange.core.build_interface_groups`` — so the one-way pair
    the loss split creates reads as the net corridor flow in the listed
    direction, directly comparable to the control's single signed link.
    """
    f = pd.read_parquet(bundle / "flows.parquet")
    f = f[(f["pass"] == "P1") & (f["year"] == year)]
    a, b = pair
    fwd = f[(f["from_zone"] == a) & (f["to_zone"] == b)]
    rev = f[(f["from_zone"] == b) & (f["to_zone"] == a)]
    net = fwd.groupby("hour")["mw"].sum()
    if len(rev):
        net = net.subtract(rev.groupby("hour")["mw"].sum(), fill_value=0.0)
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
    """Print every caiso-164 gate for both arms; return 1 on L3/S2 breach."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", default=None, help="also write the report here")
    args = ap.parse_args()

    report: dict = {"liveness": {}, "structural": {}, "lambda": {}}
    failed = False

    print("=" * 79)
    print("L1/L3 — LIVENESS AND THE caiso-163 RATINGS, ON FLOWS (never prices)")
    print("=" * 79)
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
                "control_hrs_over_cap": int((ctl > ns_cap + TOL).sum())
                + int((-ctl > sn_cap + TOL).sum()),
                "arm_hrs_over_cap": int((trt > ns_cap + TOL).sum())
                + int((-trt > sn_cap + TOL).sum()),
                "control_hrs_sn": int((ctl < -TOL).sum()),
                "arm_hrs_sn": int((trt < -TOL).sum()),
                "control_twh_sn": round(float(-ctl[ctl < 0].sum()) / 1e6, 4),
                "arm_twh_sn": round(float(-trt[trt < 0].sum()) / 1e6, 4),
            }
            if row["arm_hrs_over_cap"]:
                failed = True
            report["liveness"][f"{name}_{year}"] = row
            print(
                f"{name} {year}: control max N->S {row['control_max_ns_mw']:>8.1f} "
                f"S->N {row['control_max_sn_mw']:>8.1f} over-cap "
                f"{row['control_hrs_over_cap']:>3} | arm max N->S "
                f"{row['arm_max_ns_mw']:>8.1f} S->N {row['arm_max_sn_mw']:>8.1f} "
                f"over-cap {row['arm_hrs_over_cap']:>3}  "
                f"[L3 {'FAIL' if row['arm_hrs_over_cap'] else 'PASS'}]"
            )
            print(
                f"{' ':>14} S->N hours {row['control_hrs_sn']} -> "
                f"{row['arm_hrs_sn']}, S->N energy "
                f"{row['control_twh_sn']:.3f} -> {row['arm_twh_sn']:.3f} TWh"
            )

    print()
    print("=" * 79)
    print("S1-S4 — THE QUANTITY UNDER TEST (model vs measured DAM hub basis)")
    print("   S2 CEILING: the change may not exceed the measured dMCL")
    print("=" * 79)
    for year in YEARS:
        pc, pa = zone_prices(CONTROL, year), zone_prices(ARM, year)
        row = {}
        for label, p in (("control", pc), ("arm", pa)):
            sep = (p["NP15"] - p["ZP26"]).abs() > SEP_TOL
            d_zp = (p["NP15"] - p["ZP26"]).to_numpy()
            row[label] = {
                "hrs_np15_ne_zp26": int(sep.sum()),
                "pct_np15_ne_zp26": round(100.0 * float(sep.mean()), 3),
                "mean_np15_minus_zp26": round(float(d_zp.mean()), 4),
                "mean_np15_minus_sp15": round(
                    float((p["NP15"] - p["SP15_rest"]).mean()), 4
                ),
                "hrs_np15_dearer": int((d_zp > SEP_TOL).sum()),
            }
        act = ACTUAL[year]
        d_zp26 = (
            row["arm"]["mean_np15_minus_zp26"] - row["control"]["mean_np15_minus_zp26"]
        )
        d_sp15 = (
            row["arm"]["mean_np15_minus_sp15"] - row["control"]["mean_np15_minus_sp15"]
        )
        s1 = d_zp26 > 0
        s2 = abs(d_zp26) <= act["np15_zp26_dmcl"] + 1e-9
        s3 = row["arm"]["hrs_np15_ne_zp26"] > row["control"]["hrs_np15_ne_zp26"]
        s4 = d_sp15 > 0
        if not s2:
            failed = True
        row["actual"] = act
        row["deltas"] = {
            "d_np15_zp26": round(d_zp26, 4),
            "d_np15_sp15": round(d_sp15, 4),
            "S1_moves_toward_measured": bool(s1),
            "S2_within_measured_dMCL": bool(s2),
            "S2_ceiling": act["np15_zp26_dmcl"],
            "S2_used_pct_of_ceiling": round(100.0 * abs(d_zp26) / act["np15_zp26_dmcl"], 1),
            "S3_more_separated_hours": bool(s3),
            "S4_moves_toward_measured": bool(s4),
            "recovered_pct_of_total_basis": round(100.0 * d_zp26 / act["np15_zp26"], 2),
            "recovered_pct_of_loss_component": round(
                100.0 * d_zp26 / act["np15_zp26_dmcl"], 1
            ),
        }
        report["structural"][str(year)] = row
        print(f"-- {year}")
        print(
            f"  S1 mean NP15-ZP26  control {row['control']['mean_np15_minus_zp26']:+.4f}"
            f" -> arm {row['arm']['mean_np15_minus_zp26']:+.4f}  "
            f"(delta {d_zp26:+.4f})  ACTUAL {act['np15_zp26']:+.3f}  "
            f"[{'PASS' if s1 else 'MISS'}]"
        )
        print(
            f"  S2 ceiling = measured dMCL {act['np15_zp26_dmcl']:.3f}; used "
            f"{row['deltas']['S2_used_pct_of_ceiling']:.1f} %  "
            f"[{'PASS' if s2 else 'FAIL'}]"
        )
        print(
            f"  S3 hours NP15!=ZP26  control {row['control']['hrs_np15_ne_zp26']} "
            f"({row['control']['pct_np15_ne_zp26']} %) -> arm "
            f"{row['arm']['hrs_np15_ne_zp26']} ({row['arm']['pct_np15_ne_zp26']} %)  "
            f"[{'PASS' if s3 else 'MISS'}]"
        )
        print(
            f"     hours NP15 DEARER than ZP26 (the measured direction): "
            f"{row['control']['hrs_np15_dearer']} -> {row['arm']['hrs_np15_dearer']}"
        )
        print(
            f"  S4 mean NP15-SP15  control "
            f"{row['control']['mean_np15_minus_sp15']:+.4f} -> arm "
            f"{row['arm']['mean_np15_minus_sp15']:+.4f}  (delta {d_sp15:+.4f})  "
            f"ACTUAL {act['np15_sp15']:+.3f}  [{'PASS' if s4 else 'MISS'}]"
        )
        print(
            f"     recovered {row['deltas']['recovered_pct_of_loss_component']:.1f} % "
            f"of the measured LOSS component, "
            f"{row['deltas']['recovered_pct_of_total_basis']:.2f} % of the total basis"
        )

    print()
    print("=" * 79)
    print("PRICE LEVEL (reported, not gated — this is not a level arm)")
    print("=" * 79)
    for year in YEARS:
        lc, la = load_weighted_lambda(CONTROL, year), load_weighted_lambda(ARM, year)
        report["lambda"][str(year)] = {
            "control": round(lc, 4),
            "arm": round(la, 4),
            "pct": round(100.0 * (la - lc) / lc, 4),
        }
        print(
            f"{year}: load-weighted lambda {lc:.4f} -> {la:.4f} "
            f"({100.0 * (la - lc) / lc:+.4f} %)"
        )

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
        print(f"\nwrote {args.json}")
    print()
    print("GATE RESULT:", "FAIL" if failed else "PASS (L3 + S2 ceiling)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
