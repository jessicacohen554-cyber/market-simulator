"""pjm-132: is the within-year conditioning artifact PJM-specific, or ISO-wide?

Two questions the owner asked, answered from measured EIA-930 net load only —
no LP, no surface, no solve:

1. **Do other ISOs need the same re-conditioning?** The artifact exists because
   an ISO that peaks hard in one season has an *annual* top-percentile net-load
   bin that is structurally a sample of that season alone — so the "tight"
   state can never fire in the other season, and offers made under the other
   season's scarcity get deposited into the middle bins. Whether that holds
   elsewhere is a measurable property of each ISO's seasonal peak structure,
   not something to assume from PJM (rule 25 ``[R-ISO-SCOPE]``).

2. **What changes in a FORECAST under the seasonal definition?** The same
   statistic answers it: the number of tight-state hours that move out of the
   dominant season and into the others is exactly the forecast-side expression
   memo §5 flagged — a forecast year's winter and shoulder hours see the
   measured tight-state offer level for the first time.

Metric per (ISO, year): the seasonal composition of the tightest bin
(> 97th percentile of net load) under within-YEAR ranking, versus under
within-SEASON ranking, using the same
:data:`~market_sim.config.constants.PJM_SEASON_OF_MONTH` calendar map. Under
within-season ranking the composition is balanced by construction, so the
within-year composition IS the artifact's magnitude.

Reported, deliberately, WITHOUT a pass/fail rule: this is a descriptive
measurement of an ISO property, and whether any non-PJM ISO acts on it is that
ISO's own decision on its own evidence (rule 25). Nothing here authorizes a
re-derive anywhere.

Usage:
    PYTHONPATH=. .venv/bin/python \
        scripts/probes/pjm132_conditioning_artifact_by_iso.py \
        --json-out results/calibration/pjm132_artifact_by_iso.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

#: Tightest-bin edge the PJM offer-surface family uses (top 3 % of net load).
TIGHT_EDGE = 0.97
ISOS = ("PJM", "ERCOT", "CAISO", "MISO", "NYISO", "NEISO")
YEARS = (2023, 2024, 2025)


def _net_load(iso: str, year: int) -> "tuple | None":
    """EIA-930 net load (Demand − wind − solar) for one ISO-year, or None.

    The frame loader keys on the eGRID **BA code**, not the model ISO name
    (they coincide only for PJM and MISO), so the canonical
    ``zone_assignment._ISO_TO_BA_CODE`` map is used rather than the ISO string.
    """
    from market_sim.data.eia_loader import _eia_hourly_frame_filled
    from market_sim.data.zone_assignment import _ISO_TO_BA_CODE

    try:
        df = _eia_hourly_frame_filled(_ISO_TO_BA_CODE.get(iso, iso), year)
    except Exception:
        return None
    if df is None:
        return None
    out = pd.to_numeric(df["Demand"], errors="coerce").interpolate(
        limit_direction="both"
    )
    for col in ("NG: WND", "NG: SUN"):
        if col in df.columns:
            out = out - pd.to_numeric(df[col], errors="coerce").interpolate(
                limit_direction="both"
            )
    return out.to_numpy(float), pd.DatetimeIndex(df["Local time"]).month.to_numpy()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    from market_sim.config.constants import PJM_SEASON_OF_MONTH

    rows = []
    for iso in ISOS:
        for year in YEARS:
            got = _net_load(iso, year)
            if got is None:
                continue
            net, month = got
            if net.size < 8000 or not np.isfinite(net).any():
                continue
            # NA-safe month map: a NaT "Local time" row (the DST fall-back day)
            # carries no month. Those hours are excluded from the composition
            # rather than silently bucketed, exactly as the derive drops them
            # at its finite-q filter.
            valid = np.isfinite(month.astype(float)) & np.isfinite(net)
            net, month = net[valid], month[valid]
            season = np.array(
                [PJM_SEASON_OF_MONTH.get(int(m), "shoulder") for m in month],
                dtype=object,
            )
            # Within-YEAR tight bin (the live construction).
            tight_y = net > np.quantile(net, TIGHT_EDGE)
            comp = {
                s: int((season[tight_y] == s).sum())
                for s in ("summer", "winter", "shoulder")
            }
            n_tight = int(tight_y.sum())
            dominant = max(comp, key=comp.get)
            # Within-SEASON: each season contributes ~its own top 3 % by
            # construction, so this is the balanced target composition.
            balanced = {
                s: int(round((season == s).sum() * (1.0 - TIGHT_EDGE)))
                for s in ("summer", "winter", "shoulder")
            }
            # Hours that MOVE into the tight state outside the dominant season
            # — the forecast-side expression (memo §5).
            reallocated = sum(
                max(0, balanced[s] - comp[s]) for s in balanced if s != dominant
            )
            rows.append(
                {
                    "iso": iso,
                    "year": year,
                    "tight_hours": n_tight,
                    "within_year_composition": comp,
                    "dominant_season": dominant,
                    "dominant_share": round(comp[dominant] / max(n_tight, 1), 4),
                    "balanced_composition": balanced,
                    "hours_reallocated_to_other_seasons": reallocated,
                }
            )

    by_iso: dict = {}
    for iso in ISOS:
        sub = [r for r in rows if r["iso"] == iso]
        if not sub:
            continue
        by_iso[iso] = {
            "years": [r["year"] for r in sub],
            "mean_dominant_share": round(
                float(np.mean([r["dominant_share"] for r in sub])), 4
            ),
            "dominant_season": sub[0]["dominant_season"],
            "mean_hours_reallocated": int(
                round(float(np.mean([r["hours_reallocated_to_other_seasons"] for r in sub])))
            ),
        }

    out = {"tight_edge": TIGHT_EDGE, "by_iso": by_iso, "rows": rows}
    print(json.dumps(out, indent=2))
    if args.json_out:
        p = Path(args.json_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2))
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
