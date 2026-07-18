"""Modeled-vs-measured renewable curtailment diagnostic for a calibration bundle.

Reads a solved bundle's per-year dispatch parquet, reconstructs the uncurtailed
renewable potential the LP saw (``load_renewable_profiles`` with the bundle's
backcast config), and prints modeled curtailment ``potential - dispatched`` per
year/fuel against the *measured* curtailment — the ISO-reported ``HSL - GEN``
where an HSL parquet covers the year, else the per-tech reference curtailment
rate the gross-up fallback assumed (from the most recent HSL year). The gap is a
diagnostic, never a fit target (CLAUDE.md #11).

Usage:
    python scripts/archive/report_curtailment_diag.py results/calibration/<bundle> ISO
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.renewables import (  # noqa: E402
    _reference_curtailment_rate,
    load_hsl_hourly,
    load_renewable_profiles,
)

_TWH = 1e6  # MWh per TWh


def _potential_twh(iso: str, year: int) -> dict[str, float]:
    """Uncurtailed potential TWh per fuel the LP saw (backcast keeper config)."""
    cfg = ScenarioConfig(
        mode="backcast", vintage_capacity_ramp=True, renewable_cf_adjustment=1.0
    )
    ic = get_iso_config(iso)
    wcf, wcap, scf, scap = load_renewable_profiles(iso, year, ic, cfg)
    return {
        "wind": float((wcf * wcap[:, None]).sum()) / _TWH,
        "solar": float((scf * scap[:, None]).sum()) / _TWH,
    }


def main() -> None:
    bundle = Path(sys.argv[1])
    iso = sys.argv[2].upper()
    print(f"\n=== Renewable curtailment — {iso} (modeled vs measured) ===")
    print(f"bundle: {bundle}")
    hdr = (
        f"  {'year':>4} {'fuel':>5} {'potTWh':>7} {'genTWh':>7} "
        f"{'mdlCurt%':>8} {'measCurt%':>9} {'measured source':<28}"
    )
    print(hdr)
    for disp in sorted(bundle.glob("dispatch/*_P1.parquet")):
        year = int(disp.stem.split("_")[0])
        df = pd.read_parquet(disp, columns=["fuel", "hour", "mw"])
        pot = _potential_twh(iso, year)
        hsl = load_hsl_hourly(iso, year)
        for fuel in ("wind", "solar"):
            gen = float(df[df["fuel"] == fuel]["mw"].sum()) / _TWH
            p = pot[fuel]
            mdl = 100.0 * max(p - gen, 0.0) / p if p > 0 else float("nan")
            if hsl is not None:
                g = float(hsl[f"{fuel}_gen_mw"].clip(lower=0).sum())
                h = float(hsl[f"{fuel}_hsl_mw"].clip(lower=0).sum())
                meas = 100.0 * (1 - g / h) if h > 0 else float("nan")
                src = "ISO-reported HSL-GEN"
            else:
                rinfo = _reference_curtailment_rate(iso, fuel)
                meas = 100.0 * rinfo[0] if rinfo else float("nan")
                src = f"assumed ref rate ({rinfo[1]} HSL)" if rinfo else "n/a"
            print(
                f"  {year:>4} {fuel:>5} {p:>7.2f} {gen:>7.2f} "
                f"{mdl:>8.2f} {meas:>9.2f} {src:<28}"
            )


if __name__ == "__main__":
    main()
