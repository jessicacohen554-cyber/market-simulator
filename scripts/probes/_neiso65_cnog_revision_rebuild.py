"""neiso-65 follow-up — the PUBLISHED side of the over-count is mis-reconstructed.

The residual CAMPD over-count (`RESULTS-neiso65-crossiso-reaudit-2026-07.md` §4:
CAISO 1.52-2.13x per-resource on the crosswalked active-plant scope) is the
freeze's lift condition. Before attributing it to the detector or to CNOG
under-reporting, the INSTRUMENT that measures it has to be right. It is not.

**What the charter assumed.** `_neiso64_meritguard_score.py` and
`_neiso65_caiso_crosswalk_score.py` both collapse the CNOG report with::

    d.sort_values("last_trade_date").groupby("mrid").tail(1)

documented as "the raw parquet repeats each outage on every trade date it was
reported: 794,103 rows over 151,758 mrids = 5.23x, ... the last report is the
settled version".

**What the file actually is.** The fetcher ALREADY collapsed the trade-date
repetition: it emits one row per *distinct reported segment* and records the
repetition in `first_trade_date` / `last_trade_date` / `days_reported`
(`days_reported` sums to 1,325,042 across 794,103 rows). Measured here:
`(mrid, start, end, curtailment_mw)` is unique on all 794,103 rows — **zero
duplicates**. The 5.23 rows per mrid are therefore not repeats of one outage;
they are distinct SEGMENTS of one outage record, carrying different spans and
different curtailment levels.

`tail(1)` consequently keeps one arbitrary segment and discards the rest: on the
crosswalked non-ambient 2023-25 scope it drops **72 % of segments and 23 % of
published MW-days**, which inflates every measured over-count ratio by ~1.3x.

**Why the naive fix is also wrong.** Segments of one mrid frequently OVERLAP in
time (the charter's own 64.7 % figure) — those are successive REVISIONS of the
same outage reported on later trade dates. Summing them double-counts, which is
exactly the failure `tail(1)` was reaching for.

**The correct reconstruction** honours both structures at once: for each mrid,
each wall-clock day takes the curtailment of the segment covering that day with
the LATEST `last_trade_date`. Overlapping revisions collapse to the settled
value; genuinely disjoint segments all survive. Nothing is summed within an
mrid; mrids are summed against each other, as they must be.

This probe rebuilds the published series three ways on the same scope and
reports the level ratio under each, so the correction to the charter's headline
is explicit and auditable.

Usage::

    python scripts/probes/_neiso65_cnog_revision_rebuild.py \\
        --guard data/raw/campd-unit-outages-CAISO.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw"
CROSSWALK = RAW / "reference" / "caiso-resource-eia-crosswalk.csv"
WINDOWS = RAW / "caiso-dam-outages" / "caiso-dam-outage-windows.parquet"

_AMBIENT = ("AMBIENT_DUE_TO_TEMP", "AMBIENT_NOT_DUE_TO_TEMP")


def _segments(years: list[int]) -> pd.DataFrame:
    """Crosswalked, non-ambient CNOG segments overlapping ``years``."""
    cw = pd.read_csv(CROSSWALK)
    # One plant per resource: a duplicated resource_id would fan the segment out
    # across plants and re-introduce the double-count this probe is measuring.
    cw = cw[cw["accepted"] == 1][["resource_id", "plant_code"]].drop_duplicates(
        "resource_id"
    )
    d = pd.read_parquet(WINDOWS)
    d = d[~d["nature_of_work"].isin(_AMBIENT)]
    d = d.merge(cw, on="resource_id", how="inner")
    d["start"] = pd.to_datetime(d["start"])
    d["end"] = pd.to_datetime(d["end"])
    lo, hi = pd.Timestamp(f"{min(years)}-01-01"), pd.Timestamp(f"{max(years)}-12-31")
    return d[(d["end"] >= lo) & (d["start"] <= hi)].copy()


def _day_index(years: list[int]) -> pd.DatetimeIndex:
    return pd.date_range(f"{min(years)}-01-01", f"{max(years)}-12-31", freq="D")


def build_tail1(seg: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    """The charter's reconstruction: one arbitrary segment per mrid."""
    idx = _day_index(years)
    k = seg.sort_values("last_trade_date").groupby("mrid").tail(1)
    out = pd.DataFrame(0.0, index=idx, columns=sorted(seg["plant_code"].unique()))
    for r in k.itertuples(index=False):
        a = max(r.start.normalize(), idx[0])
        b = min(r.end.normalize(), idx[-1])
        if b >= a:
            out.loc[a:b, r.plant_code] += float(r.curtailment_mw)
    return out


def build_rawsum(seg: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    """Naive: sum every segment (double-counts overlapping revisions)."""
    idx = _day_index(years)
    out = pd.DataFrame(0.0, index=idx, columns=sorted(seg["plant_code"].unique()))
    for r in seg.itertuples(index=False):
        a = max(r.start.normalize(), idx[0])
        b = min(r.end.normalize(), idx[-1])
        if b >= a:
            out.loc[a:b, r.plant_code] += float(r.curtailment_mw)
    return out


def build_revision(seg: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    """Revision-aware: per mrid-day, the segment with the latest trade date.

    Overlapping segments of one mrid are successive revisions, so the latest
    report settles the day; disjoint segments of one mrid are distinct
    sub-periods and all survive. Distinct mrids are summed.
    """
    idx = _day_index(years)
    plants = sorted(seg["plant_code"].unique())
    pos = {p: i for i, p in enumerate(plants)}
    n_d, n_p = len(idx), len(plants)
    day0 = idx[0]
    acc = np.zeros((n_d, n_p), dtype=float)

    ltd = pd.to_datetime(seg["last_trade_date"]).to_numpy("datetime64[D]").astype(int)
    seg = seg.assign(ltd=ltd)
    for _, grp in seg.groupby("mrid", sort=False):
        mw = np.zeros(n_d, dtype=float)
        best = np.full(n_d, -(2**31), dtype=np.int64)  # winning trade date per day
        # Ascending trade date, so a later revision overwrites an earlier one on
        # the days they share and leaves the others alone.
        for r in grp.sort_values("ltd").itertuples(index=False):
            a = max(r.start.normalize(), idx[0])
            b = min(r.end.normalize(), idx[-1])
            if b < a:
                continue
            i = (a - day0).days
            j = (b - day0).days + 1
            win = r.ltd >= best[i:j]
            sl = mw[i:j]
            sl[win] = float(r.curtailment_mw)
            mw[i:j] = sl
            bb = best[i:j]
            bb[win] = r.ltd
            best[i:j] = bb
        p = pos[grp["plant_code"].iloc[0]]
        acc[:, p] += mw
    return pd.DataFrame(acc, index=idx, columns=plants)


def extract_daily(win: pd.DataFrame, years: list[int], plants: list[int]) -> pd.DataFrame:
    """CAMPD-extract daily outage MW per plant (unchanged from the §4 scorer)."""
    idx = _day_index(years)
    out = pd.DataFrame(0.0, index=idx, columns=plants)
    w = win[win["facility_id"].isin(plants)]
    for r in w.itertuples(index=False):
        a = max(pd.Timestamp(r.outage_start), idx[0])
        b = min(pd.Timestamp(r.outage_end), idx[-1])
        if b >= a:
            out.loc[a.normalize():b.normalize(), r.facility_id] += float(r.unit_capacity_mw)
    return out


def score(model: pd.Series, pub: pd.Series, years: list[int]) -> dict:
    j = pd.concat([model.rename("m"), pub.rename("p")], axis=1).dropna()
    res = {}
    for y in years:
        jj = j[j.index.year == y]
        if jj.empty or jj["p"].mean() <= 0:
            continue
        mm = jj.groupby(jj.index.month)[["m", "p"]].mean()
        res[y] = (jj["m"].mean() / jj["p"].mean(), mm["m"].corr(mm["p"]))
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--guard", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()
    years = sorted(args.years)

    seg = _segments(years)
    print(f"\n===== CNOG reconstruction audit {years} =====")
    print(f"  crosswalked non-ambient segments: {len(seg)}  mrids: {seg['mrid'].nunique()}")
    dup = len(seg) - len(seg.drop_duplicates(["mrid", "start", "end", "curtailment_mw"]))
    print(f"  duplicate (mrid,start,end,curtailment_mw) rows: {dup}   <- the charter's premise")

    ext = pd.read_csv(Path(args.guard), parse_dates=["outage_start", "outage_end"])
    ext = ext[ext["outage_start"].dt.year.isin(years)]

    builds = {
        "tail(1)  [charter §4]": build_tail1(seg, years),
        "raw sum  [double-counts]": build_rawsum(seg, years),
        "revision-aware [correct]": build_revision(seg, years),
    }
    plants = list(builds["revision-aware [correct]"].columns)
    e_by = extract_daily(ext, years, plants)
    active = [p for p in plants if e_by[p].std() > 0]
    print(f"  plants: {len(plants)}   active scope: {len(active)}")

    for tag, pub_by in builds.items():
        pub = pub_by[active].sum(axis=1)
        mw = pub.mean()
        print(f"\n  {tag}   published mean {mw:,.0f} MW")
        for y, (lv, r) in score(e_by[active].sum(axis=1), pub, years).items():
            print(f"    {y}: level {lv:.2f}x   monthly r {r:+.2f}")


if __name__ == "__main__":
    main()
