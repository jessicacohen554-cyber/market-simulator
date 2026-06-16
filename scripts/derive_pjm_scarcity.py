"""Derive the PJM net-load reserve-demand scarcity overlay for a bundle.

Post-solve overlay (no LP re-solve). PJM's energy-only dispatch dual cannot
produce the $75-200 afternoon reserve-scarcity regime: the LP sits on ~60 GW
of idle headroom in its priciest hours, so a reserve-keyed ORDC curve (the
ERCOT mechanism) is flat across price bands and fails the honesty gate. The
discriminating variable is net load — the residual is monotone in the
net-load percentile — so the adder is keyed off net load (demand - wind -
solar) via ``scarcity.netload_scarcity_adder``, anchored to PJM's reserve
penalty factors. See docs/multi-iso/pjm-lmp-residual.md.

Writes ``scarcity.parquet`` (year, hour, netload_mw, scarcity_adder, lmp,
lmp_scarcity) next to the untouched energy-only parquets, consumed by
``analyze_lmp_residual.py --with-scarcity``. With ``--score`` (default) it
prints the energy-only vs overlay monthly-LMP MAE and tail-hour counts
against the hourly actuals; nothing is written unless ``--write`` is passed.

Usage:
    python scripts/derive_pjm_scarcity.py results/calibration/pjm_26 \
        --onset-frac 0.85 --penalty-max 220 --exponent 2.0 [--write]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from market_sim.config.constants import PJM_SCARCITY_CURVE  # noqa: E402
from market_sim.results.scarcity import netload_scarcity_adder  # noqa: E402

CAL_DIR = Path(__file__).resolve().parents[1] / "inputs" / "calibration"
RENEWABLE_FUELS = ("wind", "solar")


def _system_hourly(bundle: Path) -> pd.DataFrame:
    """Per (year, hour): total demand and demand-weighted energy LMP (P1)."""
    sy = pd.read_parquet(bundle / "system.parquet")
    if "pass" in sy.columns and (sy["pass"] == "P1").any():
        sy = sy[sy["pass"] == "P1"]
    sy = sy.assign(pd_=sy["price"] * sy["demand"])
    g = sy.groupby(["year", "hour"], observed=True).agg(
        pd_=("pd_", "sum"), demand=("demand", "sum"))
    g["lmp"] = g["pd_"] / g["demand"]
    return g.reset_index()[["year", "hour", "demand", "lmp"]]


def _renewable_hourly(bundle: Path) -> pd.DataFrame:
    """Per (year, hour): dispatched wind + solar MW (the net-load credit)."""
    frames = []
    for f in sorted((bundle / "dispatch").glob("*_P1.parquet")):
        d = pd.read_parquet(f, columns=["year", "fuel", "hour", "mw"])
        d = d[d["fuel"].astype(str).isin(RENEWABLE_FUELS)]
        frames.append(d.groupby(["year", "hour"], observed=True)["mw"].sum())
    ren = pd.concat(frames)
    return ren.rename("renewable").reset_index()


def build_overlay(bundle: Path, onset_frac: float, penalty_max: float,
                  exponent: float) -> pd.DataFrame:
    """Net load and the per-year net-load scarcity adder for the bundle."""
    sysd = _system_hourly(bundle)
    ren = _renewable_hourly(bundle)
    df = sysd.merge(ren, on=["year", "hour"], how="left")
    df["renewable"] = df["renewable"].fillna(0.0)
    df["netload_mw"] = df["demand"] - df["renewable"]
    out = []
    for year, g in df.groupby("year"):
        g = g.sort_values("hour").copy()
        adder = netload_scarcity_adder(
            g["netload_mw"].to_numpy(),
            peak_netload_mw=float(g["netload_mw"].max()),
            onset_frac=onset_frac, penalty_max=penalty_max,
            exponent=exponent)
        g["scarcity_adder"] = adder
        g["lmp_scarcity"] = g["lmp"] + adder
        out.append(g)
    return pd.concat(out)[["year", "hour", "netload_mw", "lmp",
                           "scarcity_adder", "lmp_scarcity"]]


def _actual(iso: str = "PJM") -> pd.DataFrame:
    return pd.read_parquet(CAL_DIR / f"actual_lmp_hourly_{iso}.parquet")


def score(overlay: pd.DataFrame) -> None:
    """Print energy-only vs overlay monthly-MAE + tail hours vs actual RT."""
    act = _actual().rename(columns={"rt": "act"})[["year", "hour", "act"]]
    m = overlay.merge(act, on=["year", "hour"], how="inner")
    m["month"] = (m["hour"] // (24 * 30.5)).clip(upper=11).astype(int) + 1
    print(f"{'year':>4} {'MAE_eo':>7} {'MAE_ov':>7} {'Δ':>6}  "
          f"{'>75 act/eo/ov':>16}  {'>200 act/eo/ov':>16}")
    for year, g in m.groupby("year"):
        # monthly-mean MAE (demand-weighted means already in lmp)
        mo = g.groupby(g["hour"] // 730)
        mae_eo = (mo["lmp"].mean() - mo["act"].mean()).abs().mean()
        mae_ov = (mo["lmp_scarcity"].mean() - mo["act"].mean()).abs().mean()
        t75 = (int((g["act"] >= 75).sum()), int((g["lmp"] >= 75).sum()),
               int((g["lmp_scarcity"] >= 75).sum()))
        t200 = (int((g["act"] >= 200).sum()), int((g["lmp"] >= 200).sum()),
                int((g["lmp_scarcity"] >= 200).sum()))
        print(f"{int(year):>4} {mae_eo:>7.2f} {mae_ov:>7.2f} "
              f"{mae_ov - mae_eo:>+6.2f}  {str(t75):>16}  {str(t200):>16}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--onset-frac", type=float,
                    default=PJM_SCARCITY_CURVE["onset_frac"])
    ap.add_argument("--penalty-max", type=float,
                    default=PJM_SCARCITY_CURVE["penalty_max"])
    ap.add_argument("--exponent", type=float,
                    default=PJM_SCARCITY_CURVE["exponent"])
    ap.add_argument("--write", action="store_true",
                    help="write scarcity.parquet (default: score only)")
    ap.add_argument("--no-score", action="store_true")
    args = ap.parse_args()

    overlay = build_overlay(args.bundle, args.onset_frac, args.penalty_max,
                            args.exponent)
    if not args.no_score:
        print(f"# {args.bundle.name} — onset {args.onset_frac} "
              f"pen_max {args.penalty_max} exp {args.exponent}")
        score(overlay)
        print(f"adder: mean ${overlay['scarcity_adder'].mean():.2f}, "
              f">$1 in {(overlay['scarcity_adder'] > 1).sum()} h, "
              f"max ${overlay['scarcity_adder'].max():.0f}")
    if args.write:
        overlay.to_parquet(args.bundle / "scarcity.parquet", index=False)
        print(f"wrote {args.bundle / 'scarcity.parquet'}")


if __name__ == "__main__":
    main()
