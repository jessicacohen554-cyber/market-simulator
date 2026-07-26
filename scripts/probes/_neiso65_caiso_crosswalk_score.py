"""neiso-65 — CAISO per-plant crosswalk validation of the CAMPD outage extract.

STEP D of the CAMPD economic-layup fix charter
(``docs/handoffs/campd-economic-layup-fix-charter-2026-07.md`` §8 follow-on):
upgrade CAISO from the WEAKEST instrument reading to the strongest available.

The neiso-64 scorer (``_neiso64_meritguard_score.py``) compared the CEMS-thermal
CAMPD extract against the whole CNOG report filtered by a resource-NAME
heuristic — a scope so mismatched the extract sat at ~1/3 of the published level
and the placebo test returned an honest null (0/3). CAISO's Curtailed and
Non-Operational Generator report is PER-RESOURCE, so the reviewed resource→plant
crosswalk (``data/raw/reference/caiso-resource-eia-crosswalk.csv``, accepted
rows only) turns it into per-plant ground truth: BOTH sides of the comparison
are restricted to the same crosswalked plant set, making the level ratio
interpretable in both directions for the first time anywhere in this charter.

Methodology holds the neiso-64 conventions fixed so the only change is scope:

* CNOG deduplicated to one row per outage ``mrid`` (the raw parquet repeats an
  outage on every trade date it was reported — ~5.2x over-count if summed raw;
  the last report is the settled version);
* ambient CAPABILITY derates excluded (not unavailability events);
* level = daily-mean ratio, shape = monthly correlation, placebo = same
  GW-days dropped at random (30 draws, p95 gate), per year.

Per-plant grain: for every crosswalked plant with a material published signal,
the monthly correlation between its own CAMPD and CNOG series — the
distributional evidence that the guard fixes plants, not just the aggregate.

Usage::

    python scripts/probes/_neiso65_caiso_crosswalk_score.py \\
        --base <guard-off extract>.csv --guard data/raw/campd-unit-outages-CAISO.csv \\
        --layup data/raw/campd-unit-outages-layup-CAISO.csv
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

# Ambient capability derates are not unavailability events (same exclusion as
# the neiso-64 scorer, kept identical so the only methodological delta is the
# crosswalk scope).
_AMBIENT = ("AMBIENT_DUE_TO_TEMP", "AMBIENT_NOT_DUE_TO_TEMP")


def _crosswalk() -> pd.DataFrame:
    cw = pd.read_csv(CROSSWALK)
    return cw[cw["accepted"] == 1][["resource_id", "plant_code"]]


def cnog_daily(years: list[int]) -> pd.DataFrame:
    """Published daily outage MW per crosswalked plant (columns = plant_code)."""
    cw = _crosswalk()
    d = pd.read_parquet(WINDOWS)
    # One row per outage mrid: the raw file repeats an outage on every trade
    # date it was reported; the last report is the settled version.
    d = d.sort_values("last_trade_date").groupby("mrid").tail(1)
    d = d[~d["nature_of_work"].isin(_AMBIENT)]
    d = d.merge(cw, on="resource_id", how="inner")
    idx = pd.date_range(f"{min(years)}-01-01", f"{max(years)}-12-31", freq="D")
    out = pd.DataFrame(0.0, index=idx, columns=sorted(d["plant_code"].unique()))
    for r in d.itertuples(index=False):
        lo = max(pd.Timestamp(r.start).normalize(), idx[0])
        hi = min(pd.Timestamp(r.end).normalize(), idx[-1])
        if hi >= lo:
            out.loc[lo:hi, r.plant_code] += float(r.curtailment_mw)
    return out


def extract_daily(win: pd.DataFrame, years: list[int], plants: list[int]) -> pd.DataFrame:
    """CAMPD-extract daily outage MW per plant, same plant set as CNOG."""
    idx = pd.date_range(f"{min(years)}-01-01", f"{max(years)}-12-31", freq="D")
    out = pd.DataFrame(0.0, index=idx, columns=plants)
    w = win[win["facility_id"].isin(plants)]
    for r in w.itertuples(index=False):
        lo = max(pd.Timestamp(r.outage_start), idx[0])
        hi = min(pd.Timestamp(r.outage_end), idx[-1])
        if hi >= lo:
            out.loc[lo.normalize():hi.normalize(), r.facility_id] += float(
                r.unit_capacity_mw
            )
    return out


def score_years(model: pd.Series, pub: pd.Series, years: list[int]) -> dict[int, tuple]:
    """{year: (level_ratio, monthly_r)} on the summed crosswalked-plant series."""
    j = pd.concat([model.rename("m"), pub.rename("p")], axis=1).dropna()
    res = {}
    for y in years:
        jj = j[j.index.year == y]
        if jj.empty or jj["p"].mean() <= 0:
            continue
        mm = jj.groupby(jj.index.month)[["m", "p"]].mean()
        res[y] = (jj["m"].mean() / jj["p"].mean(), mm["m"].corr(mm["p"]))
    return res


def placebo_p95(base: pd.DataFrame, target_gwd: float, pub: pd.Series,
                years: list[int], plants: list[int], draws: int = 30) -> dict[int, float]:
    """p95 of monthly r when the SAME GW-days are dropped at random from base."""
    gwd = (base["unit_capacity_mw"] * base["duration_days"]).to_numpy(dtype=float)
    rng = np.random.default_rng(2026)
    rs: dict[int, list[float]] = {y: [] for y in years}
    for _ in range(draws):
        pick = np.zeros(len(base), dtype=bool)
        acc = 0.0
        for i in rng.permutation(len(base)):
            if acc >= target_gwd:
                break
            pick[i] = True
            acc += gwd[i]
        s = extract_daily(base[~pick], years, plants).sum(axis=1)
        for y, (_, r) in score_years(s, pub, years).items():
            rs[y].append(r)
    return {y: float(np.percentile(v, 95)) for y, v in rs.items() if v}


def _load(path: Path, years: list[int]) -> pd.DataFrame:
    d = pd.read_csv(path, parse_dates=["outage_start", "outage_end"])
    return d[d["outage_start"].dt.year.isin(years)].copy()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True, help="Baseline (guard-off) extract CSV.")
    ap.add_argument("--guard", required=True, help="Guard-on extract CSV.")
    ap.add_argument("--layup", default=None, help="Guard's layup companion CSV.")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--min-plant-mw", type=float, default=20.0,
                    help="Per-plant table: min published mean MW to report.")
    args = ap.parse_args()

    years = sorted(args.years)
    pub_by_plant = cnog_daily(years)
    plants = list(pub_by_plant.columns)
    pub = pub_by_plant.sum(axis=1)
    base = _load(Path(args.base), years)
    guard = _load(Path(args.guard), years)
    n_cw = base["facility_id"].isin(plants).sum()
    print(f"\n===== CAISO crosswalked per-plant validation {years} =====")
    print(f"  crosswalked plants: {len(plants)}; baseline windows in scope: {n_cw}")

    for tag, ext in (("BASELINE", base), ("GUARD ON", guard)):
        s = extract_daily(ext, years, plants).sum(axis=1)
        print(f"  {tag}")
        for y, (lv, r) in score_years(s, pub, years).items():
            print(f"    {y}: level {lv:.2f}x  monthly r {r:+.2f}")

    if args.layup and Path(args.layup).exists():
        lay = _load(Path(args.layup), years)
        lay_scope = lay[lay["facility_id"].isin(plants)]
        gwd = float((lay_scope["unit_capacity_mw"] * lay_scope["duration_days"]).sum())
        print(f"\n  reclassified in scope: {len(lay_scope)} windows, {gwd/1000:,.0f} GW-days")
        s_lay = extract_daily(lay_scope, years, plants).sum(axis=1)
        print("  LAYUP windows vs published (should be uncorrelated/anti):")
        for y, (lv, r) in score_years(s_lay, pub, years).items():
            print(f"    {y}: level {lv:.2f}x  monthly r {r:+.2f}")
        p95 = placebo_p95(base, gwd, pub, years, plants)
        s_g = extract_daily(guard, years, plants).sum(axis=1)
        print("\n  PLACEBO (same GW-days dropped at random, 30 draws)")
        for y, (_, r) in score_years(s_g, pub, years).items():
            if y in p95:
                verdict = "BEATS" if r > p95[y] else "inside"
                print(f"    {y}: guard r {r:+.2f}  placebo p95 {p95[y]:+.2f}  -> {verdict} p95")

    # Active-plant scope: CNOG's "Non-Operational" bucket includes long-term
    # mothball / seasonal-RMR states (Ormond Beach, the Alamitos steam units)
    # that the model owns through fleet status, not the outage overlay — and
    # for which the CEMS detector has no windows at all (a constant extract
    # series). Restricting BOTH sides to plants where the CAMPD baseline has
    # any signal is the like-for-like grain for judging the detector itself.
    b_by = extract_daily(base, years, plants)
    g_by = extract_daily(guard, years, plants)
    active = [pc for pc in plants if b_by[pc].std() > 0]
    print(f"\n  ACTIVE-PLANT SCOPE ({len(active)} plants with CAMPD signal)")
    pub_a = pub_by_plant[active].sum(axis=1)
    for tag, by in (("BASELINE", b_by), ("GUARD ON", g_by)):
        s = by[active].sum(axis=1)
        print(f"  {tag}")
        for y, (lv, r) in score_years(s, pub_a, years).items():
            print(f"    {y}: level {lv:.2f}x  monthly r {r:+.2f}")

    # Per-plant grain: the ground-truth distribution.
    print(f"\n  PER-PLANT monthly r (published mean >= {args.min_plant_mw:.0f} MW)")
    rows = []
    for pc in plants:
        p = pub_by_plant[pc]
        if p.mean() < args.min_plant_mw:
            continue
        pm = p.groupby([p.index.year, p.index.month]).mean()
        bm = b_by[pc].groupby([b_by.index.year, b_by.index.month]).mean()
        gm = g_by[pc].groupby([g_by.index.year, g_by.index.month]).mean()
        rows.append((pc, p.mean(), pm.corr(bm), pm.corr(gm)))
    rows.sort(key=lambda t: -t[1])
    print("    plant   pubMW   r_base  r_guard")
    for pc, mw, rb, rg in rows:
        print(f"    {pc:6d} {mw:7.0f}   {rb:+.2f}   {rg:+.2f}")
    rb = np.array([r[2] for r in rows], dtype=float)
    rg = np.array([r[3] for r in rows], dtype=float)
    ok = ~(np.isnan(rb) | np.isnan(rg))
    print(f"    median r: base {np.median(rb[ok]):+.2f} -> guard {np.median(rg[ok]):+.2f} "
          f"({(rg[ok] > rb[ok]).sum()}/{ok.sum()} plants improve)")


if __name__ == "__main__":
    main()
