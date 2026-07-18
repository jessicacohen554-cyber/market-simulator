"""pjm-105 no-LP pre-check: clear the SYMMETRIC net virtual curve at actual DA.

The pre-registered expectation for the symmetric-form build
(docs/FINDING-pjm-midmerit-level-2026-07.md §2/§6 item 1): the measured
per-hour ``net(λ) = Σ DEC≥λ − Σ INC≤λ`` curve, cleared at the ACTUAL DA
prices, nets to ≈ 0 over a year — −0.6 / −0.9 / +1.3 TWh (2023/24/25) —
versus the one-sided clamp's +10.3/+14.8/+17.2 TWh. This script clears the
rendered rung ladders (the exact arrays the LP will see, quantile
compression included) at the measured hourly DA LMP and reports:

* annual cleared DEC, cleared INC and net (TWh) — must reproduce the §2
  unclamped column to within rung-discretization error;
* the clamped-form equivalent (DEC side only) for reference;
* hour-of-day incidence of the cleared DEC/INC/net (GW by hour), showing
  where the INC side will displace generation (expected: overnight/trough).

Run BEFORE the pjm-105 solve — the reported net is the build's
pre-registered expectation, not a post-hoc fit.

Usage:
    python scripts/probes/_pjm105_symmetric_equilibrium.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.virtual_bids import load_hourly_net_virtual_curve  # noqa: E402

CAL_DIR = REPO / "data" / "raw" / "_validation-source"
HOURS = 8760


def _actual_da(year: int, hours: int) -> np.ndarray:
    """Hourly measured PJM DA system LMP ($/MWh) from the validation source."""
    df = pd.read_parquet(CAL_DIR / "actual_lmp_hourly_PJM.parquet")
    df = df[df["year"] == year]
    out = np.full(hours, np.nan)
    idx = df["hour"].to_numpy(dtype=int)
    keep = (idx >= 0) & (idx < hours)
    out[idx[keep]] = df["da"].to_numpy(dtype=float)[keep]
    return out


def clear_year(year: int) -> dict:
    """Clear the symmetric rung ladders at the actual DA price, one year."""
    curve = load_hourly_net_virtual_curve("PJM", year, HOURS)
    if curve is None:
        raise FileNotFoundError(
            f"no hrl_da_incs_decs_{year}_* parquets — run "
            "scripts/data/fetch_pjm_da_virtuals.py"
        )
    dec_mw, dec_price, inc_mw, inc_price = curve
    lam = _actual_da(year, HOURS)
    ok = np.isfinite(lam)
    lam_row = np.where(ok, lam, np.inf)[None, :]  # missing hours clear nothing
    dec = np.where(dec_price > lam_row, dec_mw, 0.0).sum(axis=0)  # (T,) MW
    inc = np.where((inc_price < lam_row) & (inc_mw > 0), inc_mw, 0.0).sum(axis=0)
    hod = np.arange(HOURS) % 24
    by_hod = pd.DataFrame({"hod": hod, "dec": dec, "inc": inc}).groupby("hod").mean()
    return {
        "year": year,
        "hours_scored": int(ok.sum()),
        "dec_twh": float(dec[ok].sum() / 1e6),
        "inc_twh": float(inc[ok].sum() / 1e6),
        "net_twh": float((dec[ok] - inc[ok]).sum() / 1e6),
        "by_hod_gw": (by_hod / 1e3).round(2),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()
    print("pjm-105 symmetric-net no-LP equilibrium at ACTUAL DA prices")
    print("expected net (finding §2 unclamped): 2023 −0.6 / 2024 −0.9 / 2025 +1.3 TWh")
    for y in args.years:
        r = clear_year(y)
        print(
            f"\n{y}: cleared DEC {r['dec_twh']:+.2f} TWh | "
            f"cleared INC {r['inc_twh']:+.2f} TWh | "
            f"NET {r['net_twh']:+.2f} TWh "
            f"(clamped-form equivalent {r['dec_twh']:+.2f}) "
            f"[{r['hours_scored']} hours scored]"
        )
        print("hour-of-day mean cleared GW (dec / inc):")
        t = r["by_hod_gw"]
        print(
            "  "
            + " ".join(
                f"{h:02d}:{t.loc[h, 'dec']:.1f}/{t.loc[h, 'inc']:.1f}"
                for h in range(24)
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
