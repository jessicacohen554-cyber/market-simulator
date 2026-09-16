"""SPP-43 phase 0b: does the new 2019-2022 extract actually reach the LP?

Zero-LP. Builds the keeper's OWN unit-outage availability multipliers
(``unit_outage_derate_factors`` + ``unit_outage_short_derate_factors`` at the
keeper's flags: ``fleet_status_scope=False``, ``st_capacity_basis=False``,
``per_unit_clip=False``, ``extract_basis_share=False``, ``hour_grain=False``,
``merit_order_guard=False``, ``unit_outage_short_windows=True``) for every year
2019-2025 and reports, per model plant-group and for the ST_GAS floored set
specifically, how many (bin, hour) cells are derated and how much capability
that removes.

Before this intake the 2019-2022 overlays were EMPTY, which is what made
availability the flat EFOR baseline there ("min availcap == p05 availcap for
all 21 floored ST_GAS plant-groups in 2019") and made every outage-conditioned
mechanism inert in the held-out years. This probe is the measurement that the
gap is closed and by how much.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.outages import (  # noqa: E402
    unit_outage_derate_factors,
    unit_outage_short_derate_factors,
)

ISO = "SPP"
YEARS = list(range(2019, 2026))


def main() -> None:
    print(f"{'year':>5} {'overlay':<8} {'bins':>5} {'derated_cells':>14} "
          f"{'mean_avail':>11} {'min_avail':>10} {'ST_GAS bins':>12} "
          f"{'ST_GAS cells':>13}")
    for y in YEARS:
        hours = 8784 if y % 4 == 0 else 8760
        for label, fn in (
            ("std", lambda: unit_outage_derate_factors(y, hours=hours, iso=ISO)),
            ("short", lambda: unit_outage_short_derate_factors(y, hours=hours, iso=ISO)),
        ):
            d = fn()
            if not d:
                print(f"{y:>5} {label:<8} {0:>5} {0:>14} {'-':>11} {'-':>10} "
                      f"{0:>12} {0:>13}")
                continue
            arrs = np.stack([v for v in d.values()])
            cells = int((arrs < 1.0).sum())
            sg = {k: v for k, v in d.items() if k[1] == "ST_GAS"}
            sg_cells = (
                int((np.stack([v for v in sg.values()]) < 1.0).sum()) if sg else 0
            )
            print(f"{y:>5} {label:<8} {len(d):>5} {cells:>14,} "
                  f"{arrs.mean():>11.4f} {arrs.min():>10.4f} {len(sg):>12} "
                  f"{sg_cells:>13,}")

    # The specific symptom the lane was opened on: a FLAT availability series
    # (min == p05) means the EFOR baseline and nothing else.
    print()
    print("=== flatness of the ST_GAS overlay (min vs p05 of the multiplier) ===")
    for y in YEARS:
        hours = 8784 if y % 4 == 0 else 8760
        d = unit_outage_derate_factors(y, hours=hours, iso=ISO)
        sg = {k: v for k, v in d.items() if k[1] == "ST_GAS"}
        flat = sum(1 for v in sg.values() if float(v.min()) == float(np.percentile(v, 5)))
        print(f"  {y}: ST_GAS plant-groups with an overlay {len(sg):>3}   "
              f"of which FLAT (min == p05) {flat:>3}")


if __name__ == "__main__":
    main()
