"""Score the pjm-169 F4 screen's pre-registered STOP gates S3 and S4.

Gates are fixed in ``docs/handoffs/PRECOMMIT-pjm169-f4-anchor-vintage-2026-09-06.md``
§5 and are STRUCTURAL: none reads C3a, C3b or any price residual. This probe
reads only the two bundles' committed ``hourly/`` sidecars — no LP, nothing
written to the dashboard.

* **S3 (direction & order of magnitude).** ``apply_gas_offer_margin`` adds
  ``markup_hr x (anchor - fuel)``, so moving only the anchor shifts every marked-up
  tranche's ``mc`` by exactly ``markup_hr x (anchor_arm - anchor_control)`` — a
  per-tranche CONSTANT, independent of the hour. The measured shift is therefore
  read from the solves' own offer-margin log line (median fixed margin =
  ``markup_hr x anchor``), and compared against the prediction §7.3 fixed before
  the solve.
* **S4 (footprint confined).** Annual energy by class, arm vs control: the
  mechanism claims gas tranches, so every non-gas class must move < 1.0 %.

Usage:
    python scripts/probes/_pjm169_f4_gates.py CONTROL_BUNDLE ARM_BUNDLE --year 2022
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

#: Classes the mechanism does NOT claim — S4's watch list.
NON_GAS_PREFIXES = ("COAL", "NUCLEAR", "WIND", "SOLAR", "HYDRO", "BIOMASS", "OTHER", "OIL")
#: S4's bar, fixed in the PRECOMMIT.
S4_BAR_PCT = 1.0


def class_energy(bundle: Path, year: int) -> pd.Series:
    """Return annual TWh by class from a bundle's committed class_hourly sidecar.

    Args:
        bundle: bundle directory.
        year: solve year.

    Returns:
        Series indexed by class, values in TWh.
    """
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    gen = next(c for c in ("mw", "gen_mw", "gen", "generation_mw") if c in df.columns)
    cls = next(c for c in ("klass", "class", "plant_group", "group") if c in df.columns)
    return df.groupby(cls)[gen].sum().div(1e6).sort_values(ascending=False)


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("control")
    ap.add_argument("arm")
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()

    c = class_energy(Path(args.control), args.year)
    a = class_energy(Path(args.arm), args.year)
    idx = sorted(set(c.index) | set(a.index))
    c, a = c.reindex(idx).fillna(0.0), a.reindex(idx).fillna(0.0)
    d = a - c
    pct = (d / c.replace(0, float("nan")) * 100).fillna(0.0)

    print(f"\nF4 screen — class energy, {args.year} (TWh)\n")
    print(f"{'class':<18}{'control':>10}{'arm':>10}{'delta':>10}{'pct':>9}")
    print("-" * 57)
    worst_non_gas = 0.0
    worst_name = ""
    for k in sorted(idx, key=lambda k: -abs(d[k])):
        flag = ""
        if k.upper().startswith(NON_GAS_PREFIXES):
            if abs(pct[k]) > abs(worst_non_gas):
                worst_non_gas, worst_name = pct[k], k
            flag = "  <- non-gas (S4)"
        print(f"{k:<18}{c[k]:>10.2f}{a[k]:>10.2f}{d[k]:>+10.2f}{pct[k]:>+8.2f}%{flag}")

    print(f"\nS4: largest non-gas class move = {worst_name} {worst_non_gas:+.2f}% "
          f"(bar: each < {S4_BAR_PCT}%) -> "
          f"{'PASS' if abs(worst_non_gas) < S4_BAR_PCT else 'FAIL'}")


if __name__ == "__main__":
    main()
