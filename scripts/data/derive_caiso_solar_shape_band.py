"""Derive the CAISO solar-shape net-load band from the EIA-930 net-load distribution.

Verifies/derives ``ScenarioConfig.caiso_solar_shape_nl_hi_pct`` /
``caiso_solar_shape_nl_lo_pct`` (the duck-belly percentile band over which
``transmission.inject_caiso_import_solar_shape`` collapses the marginal WECC
import/export offers toward the negative keep-running floor) from measured
EIA-930 CISO hourly data — the ISO-generic, forward-reproducible definition
(scalar-remediation C-7, R2 disposition).

Definition
----------
Net load = ``Demand − NG: SUN − NG: WND`` per hour (the same load-less-
utility-solar/wind quantity the mechanism gates on). Two independent,
physically-defined statistics read the band off the annual net-load
distribution:

* **HI (ramp-in edge)** — the *pure belly*: the largest percentile P such
  that ≥99 % of all hours with net load ≤ the P-th percentile are solar-
  driven *inversion* hours (net load below that local day's overnight 00–05h
  minimum — the duck curve's defining signature; midday load exceeds the
  overnight trough in any system without solar). Above this edge the deep-
  net-load population is no longer unambiguously the solar glut, so the
  offer collapse must have ramped out.
* **LO (full-collapse edge)** — the region the *canonical deep belly*
  saturates: the median annual net-load percentile rank of the spring
  (Mar–May) midday (11–16h local) population, the belly of CAISO's published
  duck chart, where the regional WECC solar glut is most acute.

Derived values (run of 2026-07-05, EIA-930 CISO on disk)
--------------------------------------------------------
==== ======================== ==========================================
year pure-belly edge (HI cand) spring-midday rank median / p75 (LO cand)
==== ======================== ==========================================
2023 33.0                      10.0 / 16.6
2024 30.0                      5.6 / 9.7
2025 34.5                      6.0 / 10.8
==== ======================== ==========================================

→ HI = 30 (conservative round edge of the ≥99 %-purity region, stable
across years) and LO = 10 (the deep-belly median sits at/below p10 every
year) — **equal to the values already carried**, so the definitional
re-grounding changes no solve output.

Because the band is expressed as percentiles of the dispatch year's *own*
net-load series, it re-centers automatically in a forecast year with more
solar (rule 13 admissibility); this script exists to re-run the check when
new EIA-930 vintages land (rule 23: re-derive on source-data change, never
on a residual).

Usage:
    python scripts/data/derive_caiso_solar_shape_band.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia_loader import _eia_hourly_frame_filled  # noqa: E402

#: Belly-purity threshold for the HI edge: full ramp-in is justified only
#: where essentially every hour that deep in the distribution IS the solar
#: glut (an inversion hour).
PURITY = 0.99
#: Canonical deep-belly window (CAISO published duck chart): spring months,
#: midday hours (local).
SPRING_MONTHS = (3, 4, 5)
MIDDAY_HOURS = (11, 16)  # inclusive local-hour band


def derive_year(year: int) -> dict | None:
    """Return the HI/LO band candidates for one EIA-930 CISO year.

    HI candidate = largest percentile (0.5 grid) with >= ``PURITY`` inversion
    share below it; LO candidate = median annual net-load percentile rank of
    the spring-midday deep-belly population. ``None`` when the 930 extract
    for the year is absent.
    """
    frame = _eia_hourly_frame_filled("CISO", year)
    if frame is None:
        return None
    local = pd.DatetimeIndex(frame["Local time"])
    dem = pd.to_numeric(frame["Demand"], errors="coerce").to_numpy(float)
    sun = pd.to_numeric(frame["NG: SUN"], errors="coerce").to_numpy(float)
    wnd = pd.to_numeric(frame["NG: WND"], errors="coerce").to_numpy(float)
    nl = dem - np.nan_to_num(sun) - np.nan_to_num(wnd)
    ok = np.isfinite(nl)
    s = pd.Series(nl[ok], index=local[ok])
    day = s.index.date
    hod = s.index.hour
    # Solar-driven inversion: net load below the local day's overnight minimum.
    overnight_min = s[hod <= 5].groupby(day[hod <= 5]).min()
    on_min = pd.Series(day, index=s.index).map(overnight_min)
    belly = (s < on_min) & on_min.notna()
    rank = s.rank(pct=True) * 100.0

    hi = 0.0
    for p in np.arange(0.5, 50.0, 0.5):
        below = s <= np.percentile(s, p)
        if belly[below].mean() >= PURITY:
            hi = float(p)
        else:
            break

    spring_mid = (
        s.index.month.isin(SPRING_MONTHS)
        & (hod >= MIDDAY_HOURS[0])
        & (hod <= MIDDAY_HOURS[1])
    )
    ranks_sm = rank[spring_mid]
    return {
        "year": year,
        "hi_pure_belly_edge": hi,
        "lo_spring_midday_median_rank": float(np.percentile(ranks_sm, 50)),
        "lo_spring_midday_p75_rank": float(np.percentile(ranks_sm, 75)),
        "belly_share_pct": float(100.0 * belly.mean()),
    }


def main() -> None:
    """Print the derived band candidates for every on-disk backcast year."""
    for year in (2023, 2024, 2025):
        row = derive_year(year)
        if row is None:
            print(f"{year}: no EIA-930 CISO extract on disk")
            continue
        print(
            f"{row['year']}: HI candidate (pure-belly edge, >={PURITY:.0%} "
            f"inversion purity) = {row['hi_pure_belly_edge']:.1f} | "
            f"LO candidate (spring-midday median rank) = "
            f"{row['lo_spring_midday_median_rank']:.1f} "
            f"(p75 {row['lo_spring_midday_p75_rank']:.1f}) | "
            f"inversion share of year = {row['belly_share_pct']:.1f}%"
        )
    print(
        "carried band: HI=30 / LO=10 "
        "(ScenarioConfig.caiso_solar_shape_nl_hi_pct / _nl_lo_pct)"
    )


if __name__ == "__main__":
    main()
