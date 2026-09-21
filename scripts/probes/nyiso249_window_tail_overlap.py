"""nyiso-249 — G-3: does the form's TIGHT WINDOW even intersect the C3c deficit?

ZERO LP (rule 32 ``[R-SHARD]`` (a)). PRECOMMIT addendum A1.

The lane's brief is to build an upper-tail offer-dispersion form **because C3c
is NYISO's lone failing criterion** and the offer side is the only live route to
it (nyiso-242 section 4 forecloses the whole reserve / RCPF / ORDC successor).
That argument has a load-bearing premise nobody has checked: **the form can only
lift a price in the hours it fires, and it fires only in the measured book's
TIGHT window.** If the window does not overlap the hours the model misses, the
form cannot be a C3c route however well-measured its magnitudes are.

Two numbers per year, and they cut in opposite directions:

    COVERAGE   share of that year's MISSED hours (actual RT hub > $300 and the
               model's max zonal dual <= $300 -- the C3c gate's OWN two
               quantities, via nyiso242_tail_reachability.missed_mask) that
               fall INSIDE the tight window. This is a hard CEILING on how many
               hours the form can possibly fix.

    EXPOSURE   share of tight hours whose actual RT hub price is BELOW $300.
               In those hours the form lifts offers where the market had no
               tail, so any price it creates is a FALSE POSITIVE that costs
               C3a / C3b. Reported, never gating -- the LP, not this probe,
               decides whether a lifted offer becomes marginal.

The window is nyiso-248's corrected DAILY coordinate, built by the same
``windows()`` the ladder uses, so the two gates cannot drift apart.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso249_window_tail_overlap.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "calibration" / "_nyiso249_window_tail_overlap.json"
THRESHOLD = 300.0

#: Pre-registered bar (PRECOMMIT addendum A1): the form is a C3c route only if
#: at least TWO years put >= 25 % of their missed hours inside the tight window.
COVERAGE_BAR = 0.25
MIN_YEARS = 2


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=None)
    args = ap.parse_args()

    from scripts.data.derive_nyiso_offer_surface import (
        NETLOAD_PCTS,
        YEARS,
        net_load_by_year,
    )
    from scripts.probes.nyiso242_tail_reachability import HUB, missed_mask
    from scripts.probes.nyiso248_book_daily_regrain import daily_gas, windows

    years = args.year or list(YEARS)
    nl = net_load_by_year()
    hub_all = pd.read_parquet(HUB)

    result: dict = {
        "gate": "G-3",
        "session": "nyiso-249",
        "coverage_bar": COVERAGE_BAR,
        "min_years_at_bar": MIN_YEARS,
        "years": {},
    }
    cleared = 0

    for y in years:
        tight, _ordinary = windows(daily_gas(y), nl[y], NETLOAD_PCTS)
        missed, month = missed_mask(y)
        n = min(len(missed), len(tight))
        tight_n, missed_n = tight[:n], missed[:n]

        hub = hub_all[hub_all["year"] == y].sort_values("hour")["rt"].to_numpy()[:n]
        actual_tail = hub > THRESHOLD

        n_missed = int(missed_n.sum())
        n_tight = int(tight_n.sum())
        cov_n = int((missed_n & tight_n).sum())
        coverage = float(cov_n / n_missed) if n_missed else 0.0
        exposure_n = int((tight_n & ~actual_tail).sum())
        ok = coverage >= COVERAGE_BAR
        cleared += int(ok)

        wmonths = sorted({int(m) for m in month[:n][tight_n]})
        result["years"][str(y)] = {
            "n_actual_gt300": int(actual_tail.sum()),
            "n_missed": n_missed,
            "n_tight": n_tight,
            "tight_months": wmonths,
            "n_missed_inside_tight": cov_n,
            "coverage_of_missed": round(coverage, 4),
            "meets_coverage_bar": ok,
            "n_tight_with_actual_below_300": exposure_n,
            "exposure_share_of_tight": round(
                float(exposure_n / n_tight) if n_tight else 0.0, 4
            ),
            "tight_hours_with_actual_tail": int((tight_n & actual_tail).sum()),
        }
        print(
            f"{y}: actual>300={int(actual_tail.sum()):4d}  missed={n_missed:4d}  "
            f"tight={n_tight:4d}  missed_in_tight={cov_n:3d}  "
            f"COVERAGE={coverage:6.1%} {'OK' if ok else '--'}   "
            f"exposure={exposure_n:4d}/{n_tight} "
            f"({result['years'][str(y)]['exposure_share_of_tight']:.1%})  "
            f"months={wmonths}"
        )

    result["years_meeting_bar"] = cleared
    result["form_is_a_c3c_route"] = bool(cleared >= MIN_YEARS)
    print(
        f"\nG-3: {cleared} of {len(years)} years at or above the "
        f"{COVERAGE_BAR:.0%} coverage bar -> form is a C3c route: "
        f"{result['form_is_a_c3c_route']}"
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
