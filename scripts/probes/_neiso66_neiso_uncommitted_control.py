"""neiso-66 — NEISO positive control: does the residual over-count track ISO-NE's
PUBLISHED available-but-not-committed capacity?

`FINDING-neiso66-overcount-rootcause-2026-07-26.md` concludes, from CAISO, that
the residual CAMPD outage over-count is a **definitional seam**: CNOG publishes
*unavailability*, the CEMS detector measures *non-operation*, and the difference
is capacity that is available but not committed.

NEISO is the one ISO that can test that directly rather than by inference.
ISO-NE's Morning Report Section 3 (`data/raw/neiso-operable-capacity/`) publishes
BOTH sides on the same daily clock:

* ``gen_outages_reductions_mw`` — the outage series the extract is scored against;
* ``uncommitted_available_gen_nonfast_mw`` — **available-but-not-committed
  capacity, i.e. the seam population itself.**

The neiso-64 scorer's docstring flagged this as NEISO's positive control; this
probe runs it. Predictions, stated before the read:

* seam TRUE  -> residual correlates with the UNCOMMITTED column;
* seam FALSE (residual is unbooked outage) -> residual correlates with the
  OUTAGE column instead.

Scope caveat (unchanged from neiso-64): the extract is CEMS-thermal only while
the published columns are whole-fleet, so the level ratio is one-directional and
the monthly correlation is the robust axis.

NOTE — the CAISO `tail(1)` reconstruction defect found in the same session does
NOT apply here. NEISO's instrument is a daily one-row-per-report_date CSV with no
`mrid` and no segment structure, so nothing is collapsed and its 1.29-1.36x
levels stand as measured.

Usage::

    python scripts/probes/_neiso66_neiso_uncommitted_control.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
PUB = REPO / "data" / "raw" / "neiso-operable-capacity"
EXT = REPO / "data" / "raw" / "campd-unit-outages-NEISO.csv"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()
    years = sorted(args.years)

    pub = (
        pd.concat(
            [
                pd.read_csv(PUB / f"neiso_operable_capacity_{y}.csv", parse_dates=["report_date"])
                for y in years
            ]
        )
        .set_index("report_date")
        .sort_index()
    )
    ext = pd.read_csv(EXT, parse_dates=["outage_start", "outage_end"])
    ext = ext[ext["outage_start"].dt.year.isin(years)]

    idx = pd.date_range(f"{min(years)}-01-01", f"{max(years)}-12-31", freq="D")
    model = pd.Series(0.0, index=idx)
    for r in ext.itertuples(index=False):
        a = max(r.outage_start.normalize(), idx[0])
        b = min(r.outage_end.normalize(), idx[-1])
        if b >= a:
            model.loc[a:b] += float(r.unit_capacity_mw)

    j = pd.DataFrame({"model": model}).join(
        pub[["gen_outages_reductions_mw", "uncommitted_available_gen_nonfast_mw"]],
        how="inner",
    ).dropna()
    j["residual"] = j["model"] - j["gen_outages_reductions_mw"]

    print("\n===== NEISO positive control: residual vs published UNCOMMITTED-available =====")
    for y in years:
        s = j[j.index.year == y]
        if s.empty:
            continue
        mm = s.groupby(s.index.month).mean()
        print(
            f"\n {y}: model {s['model'].mean():6,.0f} MW | published outages "
            f"{s['gen_outages_reductions_mw'].mean():6,.0f} MW -> level "
            f"{s['model'].mean() / s['gen_outages_reductions_mw'].mean():.2f}x"
        )
        print(
            f"      residual {s['residual'].mean():6,.0f} MW | published uncommitted "
            f"{s['uncommitted_available_gen_nonfast_mw'].mean():6,.0f} MW"
        )
        print(
            f"      monthly r(residual, published OUTAGES)     "
            f"{mm['residual'].corr(mm['gen_outages_reductions_mw']):+.2f}"
        )
        print(
            f"      monthly r(residual, published UNCOMMITTED) "
            f"{mm['residual'].corr(mm['uncommitted_available_gen_nonfast_mw']):+.2f}   <- seam"
        )


if __name__ == "__main__":
    main()
