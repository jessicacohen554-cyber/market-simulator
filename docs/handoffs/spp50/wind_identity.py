"""SPP-50 leg (ii): the wind identity `model / delivered = 1.106808`, per year.

Keeper-3's defining structural identity (FINDING-spp-43 §3): SPP's wind bound is the
delivered EIA-930 series grossed up by the SPP-32 MEASURED reference curtailment rate
0.096501 — a year-invariant factor 1/(1-0.096501) = 1.106808 — and the LP re-curtails
0.0 %, so ``model_wind / delivered_wind`` MUST equal 1.10681 in every year.

R-LEVEL is a pure re-split (SPP-48 proved the system total ``M(t)`` moves 0.000 MW in
every hour) but it moves up to 9.0 GW of wind ACROSS a seam served by a single 3,400 MW
link. If the LP can no longer deliver the re-split energy it will **re-curtail**, the
identity will break, and that is a finding about the repair rather than a detail.

Two measurements, because the first is precision-limited and the second is exact:

1. **ratio vs delivered** — model wind (the bundle's committed P1 ``class_hourly``
   sidecar) over the published screened EIA-930 annual delivered energy. The published
   constants carry three decimals, so this ratio has a ~3e-5 precision floor; it is
   reported for BOTH the run and keeper-3 so the comparison is like for like.
2. **LP re-curtailment** — model wind against the LP's OWN wind potential
   (``Σ cap × cf``) from the fleet-only array census. This is exact and is the
   mechanism the identity actually rests on: 0.0 % re-curtailment IS the identity.

usage: uv run python docs/handoffs/spp50/wind_identity.py <bundle>[:<tag>] ...
       (tag = the array-census tag whose potential pairs with that bundle;
        default `post` for the first bundle, `pre` for any later one)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]

#: Screened EIA-930 delivered SPP wind, TWh (FINDING-spp-43 §3). The LP's bound is built
#: from this same series, so the ratio below is a CONSTRUCTION identity, never a skill
#: claim — which is exactly why it is a usable test of whether the LP re-curtailed.
DELIVERED_TWH = {2023: 103.049, 2024: 109.317, 2025: 110.457}
#: 1 / (1 - 0.096501), the SPP-32 measured reference curtailment gross-up.
FACTOR = 1.106808
YEARS = (2023, 2024, 2025)
#: The fleet-only array census this lane wrote (docs/handoffs/spp50/array_census.py).
CENSUS = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "5bccefaf-1c50-588c-8c84-94ab3b579daf/scratchpad/spp50"
)


def model_wind_twh(bundle: Path, year: int) -> float | None:
    """Return the P1 model wind energy (TWh) from a bundle's class-hourly sidecar."""
    p = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    col = next(c for c in ("klass", "class", "plant_group") if c in df.columns)
    w = df[df[col].astype(str).str.upper().str.contains("WIND")]
    val = next(c for c in ("mw", "gen_mwh", "mwh") if c in w.columns)
    return float(w[val].sum()) / 1e6


def potential_twh(tag: str, year: int) -> float | None:
    """Return the LP's own wind POTENTIAL (Σ cap × cf, TWh) for a census tag."""
    p = CENSUS / f"arrays_{tag}_{year}.npz"
    if not p.exists():
        return None
    z = np.load(p)
    return float((z["wind_cf"] * z["wind_cap"][:, None]).sum()) / 1e6


def main() -> int:
    """Report both measurements for every `<bundle>[:<tag>]` on the command line."""
    args = sys.argv[1:]
    for i, spec in enumerate(args):
        b, _, tag = spec.partition(":")
        tag = tag or ("post" if i == 0 else "pre")
        bundle = Path(b) if Path(b).is_absolute() else REPO / b
        print(f"\n=== {bundle.name}  (census tag: {tag}) ===")
        print(
            f"{'year':>6} {'model TWh':>11} {'delivered':>10} {'ratio':>9} "
            f"{'|dev|':>9} {'potential':>11} {'re-curtail %':>13}"
        )
        for y in YEARS:
            m = model_wind_twh(bundle, y)
            if m is None:
                print(f"{y:>6}   (no class_hourly sidecar)")
                continue
            d = DELIVERED_TWH[y]
            r = m / d
            pot = potential_twh(tag, y)
            rc = "" if pot is None else f"{100.0 * (pot - m) / pot:>13.5f}"
            pots = "" if pot is None else f"{pot:>11.4f}"
            print(
                f"{y:>6} {m:>11.4f} {d:>10.4f} {r:>9.5f} "
                f"{abs(r - FACTOR):>9.5f} {pots} {rc}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
