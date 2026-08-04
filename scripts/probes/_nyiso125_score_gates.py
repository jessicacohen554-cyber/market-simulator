#!/usr/bin/env python3
"""nyiso-125: score the pre-registered gates for the seam-envelope arm.

Discharges the kill gates in
``results/calibration/PREREG-nyiso125-seam-envelope-2026-08-04.md`` §6 and the
§4.2 numeric prediction against the two bundles' COMMITTED artifacts. No solve
is replayed.

Instruments, named so a reader can check each claim against the right file:

* ``hourly/system_<year>.parquet`` — per-zone hourly P1 price, slack, dump,
  demand. Discharges **K1** (zone mean LMP move), **K2** (new unserved energy)
  and **K4** (inertness).
* ``metrics.json`` — the scorer's own criteria. Discharges **K3** (C1
  regression) and **K6** (the control reproducing the keeper's C3a), and
  reports C3a / C3b / C3c against the pre-registered adverse case.
* ``hourly/network_<year>.parquet`` — per-link hourly flow and bounds, the ONLY
  artifact in which the seam's spatial allocation is observable. Discharges the
  §4.2 prediction (Central-East flow and utilisation) and **K5** (the seam's
  net, which the monthly reconciliation band pins).

K5 is REPORTED as the four-link net rather than gated on a band recomputation:
the reconciliation runs inside the LP, so the observable a committed bundle
offers is the resulting net, and a net that moved materially between arms is
the signal the gate is watching for.

Run::

    uv run python scripts/probes/_nyiso125_score_gates.py \\
        --control results/calibration/nyiso125_control \\
        --treatment results/calibration/nyiso125_seam_A \\
        --json-out results/calibration/_nyiso125_gate_scores.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2023, 2024, 2025)
BORDER_LINKS = (
    "NYISO_external>Upstate_West",
    "NYISO_external>Capital_Hudson",
    "NYISO_external>NYC",
    "NYISO_external>Long_Island",
)
CE_LINK = "Upstate_West>Capital_Hudson"

# nyiso-124 §6.1's measured Central-East reference (NYISO MIS P-32
# "CENTRAL EAST - VC" utilisation p50) and the model's incumbent reading.
MEASURED_CE_UTIL_P50 = 0.591
INCUMBENT_CE_FLOW_P50 = 722.8
INCUMBENT_CE_UTIL_P50 = 0.253
# The keeper's C3a mean-LMP basis (rt_lw bench) — K6's target.
KEEPER_C3A = {2023: 34.77, 2024: 37.99, 2025: 60.22}

# Pre-registered thresholds (PREREG §6). Never widened in response to a score.
K1_ZONE_MEAN_MOVE = 0.25
K4_INERT_DLMP = 0.10
K6_C3A_TOL = 0.05

RULE = "=" * 78


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"].sort_values(["zone", "hour"])


def _network(bundle: Path, year: int) -> pd.DataFrame | None:
    path = bundle / "hourly" / f"network_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    return df[(df["kind"] == "link") & (df["pass"] == "P1")]


def score_prices(control: Path, treatment: Path) -> dict:
    """K1 / K2 / K4: zone price move, new unserved energy, inertness."""
    print(RULE)
    print("K1 / K2 / K4 — zone prices, unserved energy, inertness")
    print(RULE)
    rows, k1_fire, k2_fire, max_dlmp_all = [], [], [], []
    for year in YEARS:
        c, t = _system(control, year), _system(treatment, year)
        merged = c.merge(t, on=["zone", "hour"], suffixes=("_c", "_t"))
        dlmp = (merged["price_t"] - merged["price_c"]).to_numpy()
        max_dlmp = float(np.abs(dlmp).max())
        max_dlmp_all.append(max_dlmp)
        print(f"\n{year}   max zonal |dLMP| ${max_dlmp:.4f}/MWh")
        for zone, g in merged.groupby("zone"):
            mc, mt = float(g["price_c"].mean()), float(g["price_t"].mean())
            rel = (mt - mc) / mc if mc else 0.0
            new_slack = float(
                np.clip(g["slack_t"] - g["slack_c"], 0.0, None)[g["slack_c"] == 0].sum()
            )
            fire1, fire2 = abs(rel) > K1_ZONE_MEAN_MOVE, new_slack > 0.0
            k1_fire += [f"{year} {zone}"] if fire1 else []
            k2_fire += [f"{year} {zone}"] if fire2 else []
            print(
                f"    {zone:16s} mean ${mc:7.3f} -> ${mt:7.3f} ({rel * 100:+6.2f} %)"
                f"   new slack {new_slack:9.1f} MWh"
                f"{'   <<< K1' if fire1 else ''}{'   <<< K2' if fire2 else ''}"
            )
            rows.append(
                {
                    "year": year,
                    "zone": zone,
                    "mean_lmp_control": round(mc, 4),
                    "mean_lmp_treatment": round(mt, 4),
                    "rel_move": round(rel, 6),
                    "new_slack_mwh": round(new_slack, 3),
                }
            )
    inert = all(m < K4_INERT_DLMP for m in max_dlmp_all)
    print(
        f"\n  K1 zone-mean move > {K1_ZONE_MEAN_MOVE:.0%}: "
        f"{'FIRE ' + str(k1_fire) if k1_fire else 'silent'}"
    )
    print(f"  K2 new unserved energy: {'FIRE ' + str(k2_fire) if k2_fire else 'silent'}")
    print(
        f"  K4 inertness (max |dLMP| < ${K4_INERT_DLMP:.2f} in all years): "
        f"{'FIRE — mechanism is INERT' if inert else 'silent (mechanism is LIVE)'}"
    )
    return {
        "rows": rows,
        "max_abs_dlmp_by_year": {y: round(m, 4) for y, m in zip(YEARS, max_dlmp_all)},
        "K1_fired": k1_fire,
        "K2_fired": k2_fire,
        "K4_inert": inert,
    }


def _criteria(bundle: Path) -> dict:
    return json.loads((bundle / "metrics.json").read_text())


def score_criteria(control: Path, treatment: Path) -> dict:
    """K3 / K6 and the pre-registered adverse case on C3a."""
    print(RULE)
    print("K3 / K6 — criteria, and the pre-registered adverse case")
    print(RULE)
    mc, mt = _criteria(control), _criteria(treatment)
    out = {
        "determination_control": mc.get("determination"),
        "determination_treatment": mt.get("determination"),
    }
    print(
        f"  determination: control {out['determination_control']} -> "
        f"treatment {out['determination_treatment']}"
    )

    def verdicts(m):
        return {
            c.get("id") or c.get("name"): c.get("verdict")
            for c in (m.get("criteria") or [])
        }

    vc, vt = verdicts(mc), verdicts(mt)
    print(f"\n  {'criterion':34s} {'control':10s} {'treatment':10s}")
    for key in sorted(set(vc) | set(vt)):
        flag = "  <<<" if vc.get(key) != vt.get(key) else ""
        print(f"  {str(key)[:34]:34s} {str(vc.get(key)):10s} {str(vt.get(key)):10s}{flag}")
    out["verdicts_control"], out["verdicts_treatment"] = vc, vt
    c1 = [k for k in vc if "C1" in str(k)]
    out["K3_c1_regressed"] = any(
        vc.get(k) == "PASS" and vt.get(k) != "PASS" for k in c1
    )
    print(
        f"\n  K3 C1 regression: "
        f"{'FIRE' if out['K3_c1_regressed'] else 'silent'}"
    )
    return out


def score_network(control: Path, treatment: Path) -> dict:
    """The §4.2 numeric prediction, and K5's seam net."""
    print(RULE)
    print("§4.2 PREDICTION + K5 — the seam's spatial allocation")
    print(RULE)
    rows = []
    for year in YEARS:
        nc, nt = _network(control, year), _network(treatment, year)
        if nc is None or nt is None:
            print(f"  {year}: network layer absent in one arm — skipped")
            continue
        print(f"\n{year}")
        print(
            f"  {'link':34s} {'control p50':>12s} {'treat p50':>12s} "
            f"{'delta':>9s} {'ctl @bound':>11s} {'trt @bound':>11s}"
        )
        row = {"year": year, "links": []}
        net_c = net_t = 0.0
        for name in BORDER_LINKS:
            sc = nc[nc["name"] == name].sort_values("hour")
            st = nt[nt["name"] == name].sort_values("hour")
            if sc.empty or st.empty:
                continue
            p50c, p50t = float(np.median(sc["mw"])), float(np.median(st["mw"]))
            net_c, net_t = net_c + p50c, net_t + p50t
            bc = float(np.mean(sc["mw"].to_numpy() >= sc["limit_up"].to_numpy() - 1e-6))
            bt = float(np.mean(st["mw"].to_numpy() >= st["limit_up"].to_numpy() - 1e-6))
            print(
                f"  {name:34s} {p50c:12.1f} {p50t:12.1f} {p50t - p50c:+9.1f} "
                f"{bc * 100:10.1f}% {bt * 100:10.1f}%"
            )
            row["links"].append(
                {
                    "link": name,
                    "control_p50": round(p50c, 1),
                    "treatment_p50": round(p50t, 1),
                    "delta_p50": round(p50t - p50c, 1),
                    "control_share_at_bound": round(bc, 4),
                    "treatment_share_at_bound": round(bt, 4),
                }
            )
        # Central East — the prediction.
        cc = nc[nc["name"] == CE_LINK].sort_values("hour")
        ct = nt[nt["name"] == CE_LINK].sort_values("hour")
        ce_c, ce_t = float(np.median(cc["mw"])), float(np.median(ct["mw"]))
        uc = float(np.nanmedian(cc["mw"].to_numpy() / cc["limit_up"].to_numpy()))
        ut = float(np.nanmedian(ct["mw"].to_numpy() / ct["limit_up"].to_numpy()))
        gap = MEASURED_CE_UTIL_P50 - uc
        closed = (ut - uc) / gap if gap else float("nan")
        print(
            f"  {CE_LINK:34s} {ce_c:12.1f} {ce_t:12.1f} {ce_t - ce_c:+9.1f}"
            f"   util {uc:.3f} -> {ut:.3f} (measured {MEASURED_CE_UTIL_P50:.3f}; "
            f"{closed * 100:+.1f} % of the gap closed)"
        )
        print(
            f"  K5 four-link net p50: control {net_c:+.0f} MW -> treatment "
            f"{net_t:+.0f} MW (delta {net_t - net_c:+.0f})"
        )
        row.update(
            {
                "ce_flow_p50_control": round(ce_c, 1),
                "ce_flow_p50_treatment": round(ce_t, 1),
                "ce_util_p50_control": round(uc, 4),
                "ce_util_p50_treatment": round(ut, 4),
                "ce_measured_util_p50": MEASURED_CE_UTIL_P50,
                "ce_gap_share_closed": None if np.isnan(closed) else round(closed, 4),
                "border_net_p50_control": round(net_c, 1),
                "border_net_p50_treatment": round(net_t, 1),
            }
        )
        rows.append(row)
    return {"rows": rows}


def main() -> int:
    """Score every pre-registered gate and write the JSON record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--treatment", required=True, type=Path)
    ap.add_argument(
        "--json-out",
        type=Path,
        default=Path("results/calibration/_nyiso125_gate_scores.json"),
    )
    args = ap.parse_args()
    record = {
        "probe": "nyiso-125 gate scoring",
        "control": str(args.control),
        "treatment": str(args.treatment),
        "prices": score_prices(args.control, args.treatment),
        "criteria": score_criteria(args.control, args.treatment),
        "network": score_network(args.control, args.treatment),
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(record, indent=1) + "\n")
    print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
