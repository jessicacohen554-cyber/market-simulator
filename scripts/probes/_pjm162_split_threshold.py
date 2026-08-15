"""pjm-162 Phase 0(c): WHERE does the CAMPD duration split sit, and is it a
free parameter or a boundary the data itself picks?

Phase 0(b) (`_pjm162_split_derivability.py`) established that the CAMPD outage
record IS separable: short windows track PJM's published FORCED series and rise
in winter events, long windows track published PLANNED+MAINTENANCE and fall.
That leaves one number to fix — the duration boundary between the two families —
and a threshold chosen to make a residual move would be a fitted parameter
(rules 20 / 23 / 24).

This probe sweeps the boundary from 1 to 21 days and reports, per year, two
statistics that are computed WITHOUT reference to any model output:

  * corr(short-stratum daily MW, PJM published FORCED daily MW) — does the
    stratum track the operator's own forced series?
  * event/annual ratio of the short stratum — does it RISE in the named winter
    event, as a forced-outage family physically must?

The claim to be tested: the boundary is NOT a free parameter, because the sign
of the first statistic flips at the same place in every year, and that place
coincides with the NERC/PJM GADS definitional boundary for a forced outage (one
that cannot be deferred past the end of the next weekend, i.e. ~7 days). If the
sweep is flat or the flip wanders by year, the boundary IS a free parameter and
must enter the DOF ledger as one.

No LP, no fleet build, no solve. Run:
  PYTHONPATH=. uv run python scripts/probes/_pjm162_split_threshold.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.probes._pjm162_split_derivability import (  # noqa: E402
    EVENTS,
    YEARS,
    daily_mw,
    load_windows,
    published,
)

OUT_PATH = REPO / "results/calibration/_pjm162_split_threshold.json"
THRESHOLDS = (1, 2, 3, 4, 5, 6, 7, 8, 10, 14, 21)


def main() -> None:
    w = load_windows()
    result: dict = {"thresholds": {}}

    for thr in THRESHOLDS:
        sub = w[w["duration_days"] < thr]
        per_year: dict = {}
        for year in YEARS:
            pub = published(year)
            if pub.empty:
                continue
            pf = pub["forced_outages_mw"]
            mw = (
                daily_mw(sub, year)
                if not sub.empty
                else pd.Series(0.0, index=pf.index)
            )
            j = (
                pd.DataFrame({"mw": mw})
                .join(pd.DataFrame({"f": pf}), how="inner")
                .dropna()
            )
            s, e, _ = EVENTS[year]
            ev = float(mw.reindex(pd.date_range(s, e, freq="D")).dropna().mean())
            ann = float(j["mw"].mean())
            corr = (
                float(np.corrcoef(j["mw"], j["f"])[0, 1])
                if float(j["mw"].std()) > 0
                else float("nan")
            )
            per_year[str(year)] = {
                "annual_mean_MW": ann,
                "corr_vs_published_FORCED": corr,
                "event_mean_MW": ev,
                "event_over_annual": (ev / ann) if ann > 0 else None,
            }
        result["thresholds"][str(thr)] = per_year

    OUT_PATH.write_text(json.dumps(result, indent=2))

    print()
    print("=" * 96)
    print("pjm-162 PHASE 0(c) — duration-boundary sweep: corr vs published FORCED / event-over-annual")
    print("=" * 96)
    print("A forced-outage family must have corr > 0 AND event/annual > 1.")
    print()
    print(f"{'thr(d)':>7} " + " ".join(f"{y:>17}" for y in YEARS))
    for thr in THRESHOLDS:
        cells = []
        for year in YEARS:
            v = result["thresholds"][str(thr)].get(str(year))
            if not v:
                cells.append(f"{'-':>17}")
                continue
            cells.append(
                f"{v['corr_vs_published_FORCED']:>7.3f}/{(v['event_over_annual'] or 0):>6.2f}   "
            )
        print(f"{thr:>7} " + " ".join(cells))
    print()
    print("  cell = corr(short-stratum MW, published FORCED) / (event mean / annual mean)")
    print()
    print(f"written: {OUT_PATH}")


if __name__ == "__main__":
    main()
