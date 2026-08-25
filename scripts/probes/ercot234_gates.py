"""ercot-234 A/B gate scorer — the PRECOMMIT-ercot234 P-6 table.

Adapted from the committed ercot221_gates.py constructions (G-SPUR / G-SHED /
probe-basis C3a/C3b / D-4 compare), with the P-6 differences: the shed and
spur baselines are the CONTROL bundle's own live sets (the ercot-231 keeper,
control-by-identity per P-5), never the stale ercot-215 constants; G-COAL148
(coal TWh arm-vs-control per year, STOP at >2.0 TWh, report at >0.5 TWh),
G-SPAN (max class annual-energy move as % of ISO load), the lidless G-SPUR
decomposition (the unsigned ercot-225 card's reporting form), and the
Northeast zonal-separation report (the congestion object the repair moves)
are added. C3a/C3b probe-basis numbers are side-effect reporting under
Q-B FINAL / R-A — never a gate.

Usage:
    python scripts/probes/ercot234_gates.py \
        --control results/calibration/ercot231_tiegtc_full \
        --arm results/calibration/ercot234_eastex_identity
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

YEARS = (2023, 2024, 2025)
MID_BAND = (150.0, 500.0)
COAL_KLASSES = ("COAL_LIGNITE", "COAL_PRB")
COAL_STOP_TWH = 2.0  # P-6 STOP-class bar (gross physical implausibility)
COAL_REPORT_TWH = 0.5  # the standing report bar
SPAN_REPORT_PCT = 2.0  # P-6: name any class moving > 2% of ISO load


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[(df["year"] == year) & (df["pass"] == "P1")].copy()


def _member(df: pd.DataFrame) -> dict[str, np.ndarray]:
    def dw(col: str) -> np.ndarray:
        num = (df[col] * df["demand"]).groupby(df["hour"]).sum()
        den = df.groupby("hour")["demand"].sum()
        return (num / den).reindex(range(8760)).to_numpy(float)

    g = df.groupby("hour")
    return {
        "price": dw("price"),
        "slack": g["slack"].sum().reindex(range(8760)).fillna(0.0).to_numpy(float),
    }


def _zone_price(df: pd.DataFrame, zone: str) -> np.ndarray:
    z = df[df["zone"] == zone].sort_values("hour")
    return z.set_index("hour")["price"].reindex(range(8760)).to_numpy(float)


def _actual(year: int) -> np.ndarray:
    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    return lmp[lmp["year"] == year].sort_values("hour")["rt"].to_numpy(float)[:8760]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[(ch["year"] == year) & (ch["pass"] == "P1")]
    return (ch.groupby("klass")["mw"].sum() / 1e6).to_dict()


def _d4_rows(bundle: Path) -> list[str]:
    d = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    rows = d["diagnostics"].get("D4", {}).get("rows", [])
    return sorted(
        f"{r['year']}|{r['floor']}|{r['window']}|{r['verdict']}" for r in rows
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument(
        "--out", default=str(REPO / "results/calibration/ercot234_gates.json")
    )
    args = ap.parse_args()
    ctl_b, arm_b = Path(args.control), Path(args.arm)

    out: dict = {
        "probe": "ercot234_gates",
        "charter": "PRECOMMIT-ercot234-eastex-identity-repair-2026-08-25 P-6",
        "control": str(ctl_b),
        "arm": str(arm_b),
        "years": list(YEARS),
        "per_year": {},
    }
    stop_shed = stop_coal = False
    coal_report = spur_regress = False
    for y in YEARS:
        a = _actual(y)
        aa = np.nan_to_num(a, nan=1e9)
        yr: dict = {}
        twh: dict[str, dict[str, float]] = {}
        for name, b in (("control", ctl_b), ("arm", arm_b)):
            df = _system(b, y)
            m = _member(df)
            mm = np.nan_to_num(m["price"])
            band = (mm >= MID_BAND[0]) & (mm <= MID_BAND[1]) & (aa < MID_BAND[0])
            nolid = (mm >= MID_BAND[0]) & (aa < MID_BAND[0])
            top = (mm > MID_BAND[1]) & (aa < MID_BAND[0])
            shed = [int(h) for h in np.where(m["slack"] > 1e-6)[0]]
            ok = np.isfinite(m["price"]) & np.isfinite(a)
            p_ne = np.nan_to_num(_zone_price(df, "Northeast"))
            p_n = np.nan_to_num(_zone_price(df, "North"))
            sep = np.abs(p_ne - p_n) > 0.01
            twh[name] = _class_twh(b, y)
            yr[name] = {
                "spur_band_hours": [int(h) for h in np.where(band)[0]],
                "spur_band": int(band.sum()),
                "spur_top": int(top.sum()),
                "spur_nolid": int(nolid.sum()),
                "shed_hours": shed,
                "slack_mwh": round(float(m["slack"].sum()), 1),
                "c3a_probe_pct": round(
                    float(
                        (m["price"][ok].mean() - a[ok].mean()) / a[ok].mean() * 100.0
                    ),
                    2,
                ),
                "c3b_probe_nrmse": round(
                    float(
                        np.sqrt(np.mean((m["price"][ok] - a[ok]) ** 2)) / a[ok].mean()
                    ),
                    4,
                ),
                "tail_model_gt200": int((np.nan_to_num(m["price"]) > 200.0).sum()),
                "ne_north_separated_hours": int(sep.sum()),
                "ne_below_north_hours": int(((p_ne - p_n) < -0.01).sum()),
                "ne_above_north_hours": int(((p_ne - p_n) > 0.01).sum()),
                "coal_twh": round(
                    sum(twh[name].get(k, 0.0) for k in COAL_KLASSES), 4
                ),
            }
        # --- gates on the arm, vs the CONTROL's own live sets ---
        new_shed = sorted(set(yr["arm"]["shed_hours"]) - set(yr["control"]["shed_hours"]))
        yr["g_shed_new_hours"] = new_shed
        if new_shed:
            stop_shed = True
        coal_rise = yr["arm"]["coal_twh"] - yr["control"]["coal_twh"]
        yr["g_coal148_rise_twh"] = round(coal_rise, 4)
        if coal_rise > COAL_STOP_TWH:
            stop_coal = True
        if coal_rise > COAL_REPORT_TWH:
            coal_report = True
        if yr["arm"]["spur_band"] > yr["control"]["spur_band"]:
            spur_regress = True
        # G-SPAN: max class move as % of ISO load-energy (demand TWh proxy:
        # sum of class TWh in control).
        total = sum(twh["control"].values())
        span = {
            k: abs(twh["arm"].get(k, 0.0) - twh["control"].get(k, 0.0))
            / max(total, 1e-9)
            * 100.0
            for k in set(twh["control"]) | set(twh["arm"])
        }
        top_k = max(span, key=span.get)
        yr["g_span_max_class"] = top_k
        yr["g_span_max_pct"] = round(span[top_k], 4)
        yr["g_span_named"] = sorted(
            [k for k, v in span.items() if v > SPAN_REPORT_PCT]
        )
        out["per_year"][str(y)] = yr

    out["d4_rows_control"] = _d4_rows(ctl_b)
    out["d4_rows_arm"] = _d4_rows(arm_b)
    out["d4_no_new_rows"] = set(out["d4_rows_arm"]) <= set(out["d4_rows_control"])
    out["gates"] = {
        "STOP_g_shed_new": bool(stop_shed),
        "STOP_g_coal148_gross_gt2twh": bool(stop_coal),
        "REPORT_g_coal148_gt0p5twh": bool(coal_report),
        "REPORT_g_spur_banded_regressed_vs_keeper": bool(spur_regress),
        "REPORT_d4_new_rows": not out["d4_no_new_rows"],
        "any_stop": bool(stop_shed or stop_coal),
    }
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out["gates"], indent=1))
    for y in YEARS:
        yr = out["per_year"][str(y)]
        print(
            f"[{y}] spur band {yr['control']['spur_band']}->{yr['arm']['spur_band']}"
            f" (nolid {yr['control']['spur_nolid']}->{yr['arm']['spur_nolid']},"
            f" top {yr['control']['spur_top']}->{yr['arm']['spur_top']})"
            f" | new shed {yr['g_shed_new_hours']}"
            f" | coal rise {yr['g_coal148_rise_twh']:+.3f} TWh"
            f" | span max {yr['g_span_max_class']} {yr['g_span_max_pct']:.3f}%"
            f" | C3a {yr['control']['c3a_probe_pct']:+.2f} -> "
            f"{yr['arm']['c3a_probe_pct']:+.2f}"
            f" | C3b {yr['control']['c3b_probe_nrmse']:.4f} -> "
            f"{yr['arm']['c3b_probe_nrmse']:.4f}"
            f" | NE|N sep h {yr['control']['ne_north_separated_hours']} -> "
            f"{yr['arm']['ne_north_separated_hours']}"
        )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
