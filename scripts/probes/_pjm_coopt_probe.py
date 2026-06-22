"""PJM energy+reserve co-optimization probe analyzer.

Reads a solved bundle's ``system.parquet`` and reports the two things the
co-optimization build hinges on (docs/multi-iso/pjm-reserve-ordc.md):

  PROBE #2 (the bind gate) — does the measured ~3.4 GW Primary requirement bind
  with a NONZERO reserve clearing price? The reserve-balance-row dual is
  persisted as the ``reserve_price`` column. We report its nonzero-hour count,
  mean, max, and afternoon (HE 11-18) mean. If it is ~0 everywhere, the
  zone-aggregate shared-headroom row is slack (zone-total headroom >> 3 GW) and
  reserve clears free — the finding-#2 prediction; the next step is the ramp cap.

  PROBE #1 (the lever) — is the $75-200 afternoon regime populated, and does the
  Jul/Aug LMP residual shrink without an overnight overshoot? Compares the
  demand-weighted model LMP to the actual hub-mean hourly series, optionally
  against an energy-only baseline bundle.

Usage:
  python scripts/probes/_pjm_coopt_probe.py <coopt_bundle> [baseline_bundle]
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CAL = ROOT / "data" / "raw" / "_validation-source"


def _model_lmp(bundle: Path) -> pd.DataFrame:
    """Demand-weighted hourly LMP per (year, hour) from system.parquet (P1)."""
    sy = pd.read_parquet(bundle / "system.parquet")
    if "pass" in sy.columns and (sy["pass"] == "P1").any():
        sy = sy[sy["pass"] == "P1"]
    sy = sy.assign(pd_=sy["price"] * sy["demand"])
    g = sy.groupby(["year", "hour"], observed=True).agg(
        pd_=("pd_", "sum"), d=("demand", "sum"), p=("price", "mean")
    )
    lmp = np.where(g["d"] > 0, g["pd_"] / g["d"], g["p"])
    return g.assign(lmp=lmp).reset_index()[["year", "hour", "lmp"]]


def _reserve_price(bundle: Path) -> pd.DataFrame:
    """System-wide reserve clearing price per (year, hour), or zeros."""
    sy = pd.read_parquet(bundle / "system.parquet")
    if "pass" in sy.columns and (sy["pass"] == "P1").any():
        sy = sy[sy["pass"] == "P1"]
    if "reserve_price" not in sy.columns:
        out = sy.groupby(["year", "hour"], observed=True).size().reset_index()
        out["reserve_price"] = 0.0
        return out[["year", "hour", "reserve_price"]]
    return (
        sy.groupby(["year", "hour"], observed=True)["reserve_price"]
        .mean()
        .reset_index()
    )


# Local non-leap 8760 hour -> (month, hour-of-day). Matches the fleet clock.
_HRS = pd.date_range("2023-01-01", "2023-12-31 23:00", freq="h")
_MONTH = np.array(_HRS.month)
_HOD = np.array(_HRS.hour)


def main(bundle: Path, baseline: Path | None) -> None:
    iso = "PJM"
    actual = pd.read_parquet(CAL / f"actual_lmp_hourly_{iso}.parquet")
    acol = "rt" if "rt" in actual.columns else actual.columns[-1]

    lmp = _model_lmp(bundle)
    rp = _reserve_price(bundle)
    base = _model_lmp(baseline) if baseline else None

    years = sorted(lmp["year"].unique())
    afternoon = (_HOD >= 11) & (_HOD <= 18)
    summer = np.isin(_MONTH, [7, 8])

    print(f"\n=== PJM co-opt probe: {bundle.name} ===")
    for y in years:
        m = lmp[lmp["year"] == y].sort_values("hour")["lmp"].to_numpy()
        r = rp[rp["year"] == y].sort_values("hour")["reserve_price"].to_numpy()
        a = actual[actual["year"] == y].sort_values("hour")[acol].to_numpy()
        n = min(len(m), len(a), 8760)
        m, a = m[:n], a[:n]
        r = r[:n] if len(r) >= n else np.pad(r, (0, n - len(r)))
        aff, sm = afternoon[:n], summer[:n]
        ss = sm  # Jul/Aug mask

        # --- PROBE #2: reserve clearing price (the balance-row dual) ---
        nz = r > 1e-6
        print(f"\n[{y}] PROBE#2 reserve clearing price (balance dual):")
        print(
            f"   hours>0: {int(nz.sum())}/{n}  mean=${r.mean():.3f}  "
            f"max=${r.max():.1f}  afternoon-mean=${r[aff].mean():.3f}  "
            f"Jul/Aug-mean=${r[ss].mean():.3f}"
        )
        if nz.any():
            print(
                f"   nonzero-hour reserve price: mean=${r[nz].mean():.1f}  "
                f"p50=${np.median(r[nz]):.1f}  max=${r[nz].max():.1f}"
            )

        # --- PROBE #1: LMP regime ---
        def band(mask):
            mm, aa = np.nanmean(m[mask]), np.nanmean(a[mask])
            return f"model {mm:6.2f}  actual {aa:6.2f}  resid {mm - aa:+6.2f}"

        print(f"[{y}] PROBE#1 LMP demand-weighted:")
        print(f"   full-year : {band(np.ones(n, bool))}")
        print(f"   Jul/Aug   : {band(ss)}")
        print(f"   JA-aftn   : {band(ss & aff)}")
        print(f"   overnight : {band((_HOD[:n] <= 5))}")
        h75_m = int((m[ss] > 75).sum())
        h75_a = int((a[ss] > 75).sum())
        print(f"   Jul/Aug hours>$75: model {h75_m}  actual {h75_a}")
        if base is not None:
            b = base[base["year"] == y].sort_values("hour")["lmp"].to_numpy()[:n]
            print(
                f"   vs baseline: full-yr {m.mean() - b.mean():+.2f}  "
                f"JA-aftn {m[ss & aff].mean() - b[ss & aff].mean():+.2f}  "
                f"overnight {m[_HOD[:n] <= 5].mean() - b[_HOD[:n] <= 5].mean():+.2f}  "
                f"(model−baseline $/MWh)"
            )


if __name__ == "__main__":
    bundle = Path(sys.argv[1])
    baseline = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    main(bundle, baseline)
