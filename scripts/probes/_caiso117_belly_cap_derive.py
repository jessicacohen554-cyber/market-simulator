"""caiso-117 LEG 1 DERIVE: the West's measured belly export capability as the
belly-hour import cap, vs the CA-side gate targets — derive-first, NO SOLVE.

The belly (C5a) fix must cap CAISO's belly (hod 10-15) imports at a WEST-SIDE
physical quantity (wecc-west-supply), NOT a CA-side flow observable (rule 13 /
the caiso-107/109 kills). This probe measures the candidate West-side caps and
checks the two derive gates BEFORE any code is written or any LP is solved:

  GATE-A (will it bind?):   West belly cap  <  current corridor p95 import cap
                            (so the belly cap is TIGHTER and actually reduces
                            the model's belly over-import).
  GATE-B (won't it over-correct?):  West belly cap  >=  CA MEASURED belly net
                            import (0.7/1.4/1.9 GW) — the level the model should
                            land at. A cap BELOW measured would force belly
                            import under the real level (over-correct C5a the
                            other way).

Candidate West-side measures (all per-(month x belly-hod) percentiles of a
West-side physical quantity from wecc-west-supply, mapped to the model clock):
  (1) net_export_mw           — the West's measured net interchange out (all
                                fuels); the actual amount the West sends out.
  (2) clip(net_export_mw, 0)  — the West's exportable surplus (>=0), the
                                Inv-2/redirect-#3 "belly export capability".

Reference lines:
  * CA measured belly net import (the gate-B target) — raw EIA-930 CISO Total
    interchange, belly hod, per year.
  * current corridor p95 import cap in the belly — the loose ceiling this leg
    tightens (measured_corridor_flow_envelope, summed across corridors).

Run:  PYTHONPATH=<repo> python scripts/probes/_caiso117_belly_cap_derive.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.data.eia930.envelopes import measured_corridor_flow_envelope
from market_sim.data.fleet import _hour_to_month_index
from scripts.lib.clean_io import read_clean

BELLY = [10, 11, 12, 13, 14, 15]  # handoff hod ~10-15
CISO_HOURLY = "data/raw/eia-930-hourly/CISO hourly.parquet"
HOURS = 8760
YEARS = (2023, 2024, 2025)


def _ca_belly_net_import() -> dict[int, float]:
    """CA measured belly net import (GW) per year — the gate-B target."""
    w = pd.read_parquet(CISO_HOURLY)
    lt = pd.to_datetime(w["Local time"])
    w = w.assign(
        year=lt.dt.year,
        hod=lt.dt.hour,
        net_import=-pd.to_numeric(w["Total interchange"], errors="coerce"),
    )
    out = {}
    for y in YEARS:
        a = w[(w["year"] == y) & (w["hod"].isin(BELLY))]
        out[y] = a["net_import"].mean() / 1e3
    return out


def _west_belly_cap(year: int, measure: str, pct: float) -> np.ndarray:
    """Per-hour West belly export cap (MW): per-(month x belly-hod) percentile of
    the West-side quantity in belly hours, np.inf elsewhere. Maps the UTC frame
    onto the model clock (US/Pacific hod), the same alignment the LP uses."""
    f = read_clean("wecc-west-supply", iso="CAISO", year=year).copy()
    loc = f["interval_start_utc"].dt.tz_convert("US/Pacific")
    f["month"] = loc.dt.month
    f["hod"] = loc.dt.hour
    if measure == "net_export":
        q = f["net_export_mw"].to_numpy()
    elif measure == "export_surplus":
        q = np.clip(f["net_export_mw"].to_numpy(), 0.0, None)
    else:
        raise ValueError(measure)
    f["q"] = q
    tab = {}
    sub = f[f["hod"].isin(BELLY)]
    for (m, h), g in sub.groupby(["month", "hod"]):
        tab[(m, h)] = np.percentile(g["q"].to_numpy(), pct)
    rm = _hour_to_month_index(HOURS) + 1
    rh = np.arange(HOURS) % 24
    cap = np.full(HOURS, np.inf)
    for t in range(HOURS):
        if rh[t] in BELLY:
            cap[t] = tab.get((rm[t], rh[t]), np.inf)
    return cap


def main() -> None:
    ca_import = _ca_belly_net_import()
    print("=" * 82)
    print("caiso-117 LEG 1 DERIVE — West belly export capability vs gate targets")
    print(f"belly hod = {BELLY}")
    print("=" * 82)

    # Current corridor p95 import cap in the belly (summed across corridors).
    print("\nReference — CA MEASURED belly net import (gate-B target) and current")
    print("corridor p95 import cap (the loose ceiling this leg tightens):")
    corridor_belly = {}
    for y in YEARS:
        env = measured_corridor_flow_envelope("CAISO", y, HOURS)
        tot = np.sum(list(env.values()), axis=0)
        rh = np.arange(HOURS) % 24
        belly_mask = np.isin(rh, BELLY)
        corridor_belly[y] = tot[belly_mask].mean() / 1e3
        print(
            f"  {y}: CA measured belly import {ca_import[y]:.2f} GW | "
            f"corridor p95 cap belly {corridor_belly[y]:.2f} GW"
        )

    # Candidate West-side caps.
    for measure in ("net_export", "export_surplus"):
        print(f"\n--- Candidate: West {measure} (per month x belly-hod percentile) ---")
        for pct in (50.0, 75.0, 90.0, 95.0):
            row = []
            gate_a = []
            gate_b = []
            for y in YEARS:
                cap = _west_belly_cap(y, measure, pct)
                belly_mean = cap[np.isfinite(cap)].mean() / 1e3
                row.append(belly_mean)
                gate_a.append(belly_mean < corridor_belly[y])  # tighter → binds
                gate_b.append(belly_mean >= ca_import[y])  # >= measured → no overcorr
            ga = "BIND" if all(gate_a) else ("part" if any(gate_a) else "loose")
            gb = "ok" if all(gate_b) else ("part" if any(gate_b) else "UNDER")
            print(
                f"  p{pct:>4.0f}: belly cap GW = "
                + " / ".join(f"{v:.2f}" for v in row)
                + f"   [GATE-A {ga}, GATE-B {gb}]"
            )
    print("\nREAD: pick the (measure, percentile) that BOTH binds (< corridor p95)")
    print("      and does not under-cut CA measured import (>= 0.7/1.4/1.9). That")
    print("      is the forward-stable West-physical belly cap for the LP delta.")


if __name__ == "__main__":
    main()
