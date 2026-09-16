#!/usr/bin/env python3
"""SPP-44 phase 0 (ZERO LP): the coal-deliverability lever, adjudicated.

Lane SPP-44 (2026-09-16) took SPP's NAMED STRUCTURAL SUCCESSOR -- "a coal offer
markup keyed to coal deliverability / stockpile days", entered as ``U`` by
SPP-41 (``RESULT-spp-41-coal-gas-crossover-2026-09-14.md`` section 2.6 point 4) and
recorded there as **blocked on an EIA-923 Schedule-5 coal receipts-and-stocks
intake that does not exist on disk**.

THAT BLOCKER IS STALE. Both datatypes landed 2026-09-14 (``data/raw/coal-receipts``
+ ``data/raw/coal-stocks``, 2018-2024, with schemas, curation scripts and the
rule-13-disciplined readers ``coal_receipts.prior_years_delivery_rate`` and
``coal_stocks.opening_stock_tons``). The data question is closed; this probe asks
the IDENTIFICATION question the data was blocking, and answers it in the
negative on measurement.

Six legs, all zero-LP and re-runnable::

    A  coverage of the model's own 32 SPP coal plants, per year
    B  LAGGED (<= Y-1, admissible) vs SAME-YEAR (inadmissible) statistics
       against the MMU's published coal offer markup
    C  per-plant concentration -- the MMU says "SEVERAL coal resources", so a
       fleet aggregate could wash out a concentrated event
    D  sub-annual DELIVERY-TIMING signature (zero-receipt months, CV, gaps),
       plus the reporting-frequency confound that would fake it
    E  would the existing ``coal_fuel_inventory`` mechanism BIND on SPP?
    F  is leg E's binding PHYSICAL, or an artifact of the row's flat /12 form?

THE RESULT. Legs B-D: no statistic -- lagged or same-year, fleet or per-plant,
tonnage or timing -- puts 2022 outside the other years' range, while the MMU
target has 2022 at 3.07x the maximum of every other year. 2022 is in fact the
SMOOTHEST delivery year in the 2018-2024 record, and the genuinely stressed
years (2020, 2024) carry the LOWEST markups. Legs E-F: the flat monthly budget
would bind in 2021/2022, but the physically correct cumulative constraint never
binds in any year, so that binding is a form artifact and not a fuel shortage.

Usage::

    PYTHONPATH=src python3 scripts/probes/_spp44_coal_deliverability_phase0.py

Requires the two clean datatypes::

    python3 scripts/data/curate_coal_receipts.py
    python3 scripts/data/curate_coal_stocks.py
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd

CLEAN = Path("data/clean")
SRC_YEARS = list(range(2018, 2025))

# The model's OWN SPP coal plant set, read from the committed keeper-lineage
# bundle's dispatch parquet (rule 25 [R-ISO-SCOPE]: SPP's fleet, nothing
# transferred from another ISO).
PRB = [59, 60, 108, 165, 1241, 1250, 2079, 2240, 2277, 2291, 2952, 2963, 6064,
       6065, 6068, 6077, 6095, 6096, 6138, 6139, 6193, 6194, 6195, 6772, 10671,
       10862, 54211, 56564, 57046]
LIGNITE = [2817, 6469, 7902]
FLEET = set(PRB) | set(LIGNITE)

# SPP MMU published coal offer markup, $/MWh -- the TARGET series, reported and
# never fitted (ASOM 2023 fn. 135/194, ASOM 2024, ASOM 2025; SPP-41 section 2.5).
MMU = {2021: 6.02, 2022: 21.12, 2023: 6.88, 2024: 4.29, 2025: 5.81}
# SPP delivered gas, $/MMBtu, same source table.
GAS = {2021: 3.72, 2022: 6.45, 2023: 2.54, 2024: 2.19, 2025: 3.52}

HOLDOUT = Path("results/calibration/spp43_holdout_span")
SPAN = Path("results/calibration/spp42_span_a")
BUNDLE = {y: (HOLDOUT if y <= 2022 else SPAN) for y in range(2019, 2026)}


def spearman(x: list[float], y: list[float]) -> float:
    """Spearman rank correlation without a scipy dependency."""
    return float(pd.Series(x).rank().corr(pd.Series(y).rank()))


def coal_twh(class_full: dict) -> float:
    """Annual coal TWh from a committed bench ``classFull`` block.

    The bench stores these as ALREADY-AGGREGATED annual TWh scalars (verified:
    SPP 2019 ``COAL_PRB`` = 76.821), not hourly MW arrays. The list branch is
    kept only so an older hourly-array bench vintage still reads correctly.
    """
    total = 0.0
    for key, value in class_full.items():
        if not key.upper().startswith("COAL"):
            continue
        total += float(sum(value)) / 1e6 if isinstance(value, (list, tuple)) else float(value)
    return total


def bench(year: int) -> dict:
    """Return the committed benchmark ``classFull`` block for ``year``."""
    path = f"frontend/data/backcast/bench/SPP/{year}.json.gz"
    with gzip.open(path) as handle:
        return json.load(handle)["bench"]["classFull"]


def load_clean(datatype: str) -> pd.DataFrame:
    """Concatenate a clean datatype over every curated source year."""
    files = [CLEAN / datatype / f"{datatype}_{y}.parquet" for y in SRC_YEARS]
    present = [f for f in files if f.exists()]
    if not present:
        raise SystemExit(
            f"no curated {datatype}; run scripts/data/curate_{datatype.replace('-', '_')}.py"
        )
    return pd.concat([pd.read_parquet(f) for f in present], ignore_index=True)


def fleet_annual(receipts: pd.DataFrame, stocks: pd.DataFrame) -> pd.DataFrame:
    """Annual fleet receipts, implied burn and December ending stock.

    Burn comes from the measured identity ``end[m] = end[m-1] + rec[m] - burn[m]``.
    """
    s = stocks.groupby(["year", "month"])["ending_stock_tons"].sum().rename("end").reset_index()
    r = receipts.groupby(["year", "month"])["quantity_tons"].sum().rename("rec").reset_index()
    m = s.merge(r, on=["year", "month"], how="outer").sort_values(["year", "month"])
    m["rec"] = m["rec"].fillna(0.0)
    m["burn"] = m["end"].shift(1) + m["rec"] - m["end"]
    return m.groupby("year").agg(rec=("rec", "sum"), burn=("burn", "sum"),
                                 dec=("end", "last")).sort_index()


def model_monthly_tons(year: int, annual: pd.DataFrame) -> tuple[pd.Series, float]:
    """The model's own monthly coal burn in tons, and the tons/TWh conversion.

    The conversion is taken from year ``Y-1``'s measured burn and generation
    wherever a prior bench exists, so it is a rule-13-admissible unit factor
    rather than a same-year outcome. 2019 falls back to its own year (there is
    no 2018 bench), which is flagged by the caller.
    """
    conv = year - 1 if Path(f"frontend/data/backcast/bench/SPP/{year-1}.json.gz").exists() else year
    tons_per_twh = float(annual.loc[conv, "burn"]) / coal_twh(bench(conv))
    hourly = pd.read_parquet(BUNDLE[year] / "hourly" / f"class_hourly_{year}.parquet")
    hourly = hourly[hourly["klass"].astype(str).str.upper().str.startswith("COAL")]
    per_hour = hourly.groupby("hour")["mw"].sum().astype("float64")
    index = pd.date_range(f"{year}-01-01", periods=len(per_hour), freq="h")
    monthly_twh = pd.Series(per_hour.to_numpy(), index=index).groupby(index.month).sum() / 1e6
    return monthly_twh * tons_per_twh, tons_per_twh


def leg_a(receipts: pd.DataFrame, stocks: pd.DataFrame) -> None:
    """Coverage of the model's 32 SPP coal plants in both datatypes."""
    print("== leg A: coverage of the model's 32 SPP coal plants ==")
    print(f"{'year':>5} {'rec_plants':>11} {'rec_Mt':>9} {'stk_plants':>11} {'stk_Dec_Mt':>11}")
    for y in SRC_YEARS:
        r = receipts[receipts["year"] == y]
        s = stocks[(stocks["year"] == y) & (stocks["month"] == 12)]
        print(f"{y:>5} {r['plant_id'].nunique():>11} {r['quantity_tons'].sum()/1e6:>9.2f} "
              f"{s['plant_id'].nunique():>11} {s['ending_stock_tons'].sum()/1e6:>11.2f}")


def leg_b(annual: pd.DataFrame, receipts: pd.DataFrame) -> None:
    """Lagged (admissible) vs same-year (inadmissible) statistics vs the MMU."""
    print("\n== leg B: LAGGED (<= Y-1, admissible) vs SAME-YEAR (rule-13 forbidden) ==")
    head = (f"{'Y':>5} {'MMU$':>7} || {'L:openDays':>11} {'L:rec/burn':>11} {'L:rail%':>8} || "
            f"{'S:rec/burn':>11} {'S:deficit_Mt':>13}")
    print(head)
    print("-" * len(head))
    rows = []
    for y in sorted(MMU):
        src = [k for k in (y - 2, y - 1) if k in annual.index]
        opening = annual["dec"].get(y - 1)
        lag_days = opening / (annual.loc[src, "burn"].mean() / 365.0)
        lag_ratio = annual.loc[src, "rec"].sum() / annual.loc[src, "burn"].sum()
        window = receipts[receipts["year"].isin(src)]
        by_mode = window.groupby("primary_transportation_mode")["quantity_tons"].sum()
        rail = 100.0 * by_mode.get("RR", 0.0) / by_mode.sum()
        if y in annual.index:
            same_ratio = annual.loc[y, "rec"] / annual.loc[y, "burn"]
            same_def = (annual.loc[y, "rec"] - annual.loc[y, "burn"]) / 1e6
            tail = f"{same_ratio:>11.4f} {same_def:>13.3f}"
        else:
            same_ratio = same_def = None
            tail = f"{'--':>11} {'--':>13}"
        print(f"{y:>5} {MMU[y]:>7.2f} || {lag_days:>11.1f} {lag_ratio:>11.4f} {rail:>8.1f} || {tail}")
        rows.append((y, lag_days, lag_ratio, rail, same_ratio, same_def))

    frame = pd.DataFrame(rows, columns=["year", "L:openDays", "L:rec/burn", "L:rail%",
                                        "S:rec/burn", "S:deficit"]).set_index("year")
    print("\n  rank agreement with the MMU markup (sign expected NEGATIVE:")
    print("  tighter deliverability -> higher markup), and the 2022 outlier test:")
    for col in frame.columns:
        sub = frame[col].dropna()
        if len(sub) < 3 or 2022 not in sub.index:
            continue
        target = [MMU[y] for y in sub.index]
        others = sub.drop(2022)
        outside = sub.loc[2022] < others.min() or sub.loc[2022] > others.max()
        print(f"    {col:>12}: rho {spearman(target, sub.tolist()):+.3f} (n={len(sub)}) | "
              f"2022 {sub.loc[2022]:>9.4f} | others [{others.min():.4f}, {others.max():.4f}] "
              f"-> {'OUTSIDE' if outside else 'INSIDE'}")
    others = {k: v for k, v in MMU.items() if k != 2022}
    print(f"    {'MMU target':>12}: 2022 {MMU[2022]:>9.4f} | others "
          f"[{min(others.values()):.4f}, {max(others.values()):.4f}] -> OUTSIDE "
          f"({MMU[2022]/max(others.values()):.2f}x the max)")
    print(f"\n  for contrast, markup vs DELIVERED GAS: rho "
          f"{spearman([MMU[y] for y in sorted(MMU)], [GAS[y] for y in sorted(MMU)]):+.3f} "
          f"(n=5) -- reported for routing only; SPP-41 section 2.6 killed the gas-keyed "
          f"SIGMOID form and nothing here revives it.")


def leg_c(receipts: pd.DataFrame, stocks: pd.DataFrame) -> None:
    """Per-plant concentration -- the MMU names 'several coal resources'."""
    print("\n== leg C: per-plant concentration (is a fleet aggregate hiding the event?) ==")
    s = (stocks.groupby(["plant_id", "year", "month"])["ending_stock_tons"].sum()
         .rename("end").reset_index())
    r = (receipts.groupby(["plant_id", "year", "month"])["quantity_tons"].sum()
         .rename("rec").reset_index())
    d = s.merge(r, on=["plant_id", "year", "month"], how="outer").sort_values(
        ["plant_id", "year", "month"])
    d["rec"] = d["rec"].fillna(0.0)
    d["burn"] = d.groupby("plant_id")["end"].shift(1) + d["rec"] - d["end"]
    per = d.groupby(["plant_id", "year"]).agg(rec=("rec", "sum"), burn=("burn", "sum"),
                                              dec=("end", "last")).reset_index()
    per = per[per["burn"] > 0]
    per["cover"] = per["rec"] / per["burn"]
    print("   a plant is STRESSED if it received < 90 % of what it burned that year")
    print(f"{'year':>5} {'plants':>7} {'n<0.90':>7} {'n<0.75':>7} {'p10':>7} {'median':>7}")
    for y in sorted(per["year"].unique()):
        g = per[per["year"] == y]
        print(f"{y:>5} {len(g):>7} {(g['cover']<0.90).sum():>7} {(g['cover']<0.75).sum():>7} "
              f"{g['cover'].quantile(.10):>7.3f} {g['cover'].median():>7.3f}")


def leg_d(receipts: pd.DataFrame) -> None:
    """Sub-annual delivery-TIMING signature, and its reporting-frequency confound."""
    print("\n== leg D: sub-annual DELIVERY-TIMING signature (annual total held aside) ==")
    per_month = (receipts.groupby(["plant_id", "year", "month"])["quantity_tons"].sum()
                 .rename("t").reset_index())
    grid = pd.MultiIndex.from_product(
        [sorted(per_month["plant_id"].unique()), SRC_YEARS, range(1, 13)],
        names=["plant_id", "year", "month"])
    full = per_month.set_index(["plant_id", "year", "month"]).reindex(grid, fill_value=0.0)
    active = per_month.groupby(["plant_id", "year"])["t"].sum()
    full = full.reset_index().set_index(["plant_id", "year"]).loc[
        active[active > 0].index].reset_index()

    def max_gap(values) -> int:
        best = run = 0
        for v in values:
            run = run + 1 if v <= 0 else 0
            best = max(best, run)
        return best

    rows = []
    for (plant, year), g in full.groupby(["plant_id", "year"]):
        t = g.sort_values("month")["t"].to_numpy()
        rows.append((plant, year, (t <= 0).sum(),
                     t.std() / t.mean() if t.mean() else 0.0, max_gap(t)))
    tim = pd.DataFrame(rows, columns=["plant_id", "year", "zero_m", "cv", "maxgap"])
    print(f"{'year':>5} {'plants':>7} {'mean_zero_m':>12} {'mean_cv':>8} {'n_gap>=2':>9}")
    for y in sorted(tim["year"].unique()):
        g = tim[tim["year"] == y]
        print(f"{y:>5} {len(g):>7} {g['zero_m'].mean():>12.2f} {g['cv'].mean():>8.3f} "
              f"{(g['maxgap']>=2).sum():>9}")

    agg = tim.groupby("year").agg(cv=("cv", "mean"), zero=("zero_m", "mean"),
                                  gap2=("maxgap", lambda s: (s >= 2).sum()))
    common = [y for y in sorted(MMU) if y in agg.index]
    print("\n  vs the MMU markup (a NEGATIVE rho would mean rougher deliveries -> higher markup):")
    for col in ["cv", "zero", "gap2"]:
        v = agg.loc[common, col]
        others = v.drop(2022)
        outside = v.loc[2022] < others.min() or v.loc[2022] > others.max()
        print(f"    {col:>5}: rho {spearman([MMU[y] for y in common], v.tolist()):+.3f} | "
              f"2022 {v.loc[2022]:>7.3f} | others [{others.min():.3f}, {others.max():.3f}] "
              f"-> {'OUTSIDE' if outside else 'INSIDE'}")
    print("\n  CONFOUND CHECK -- an ANNUAL filer fakes 11 zero-delivery months, so a")
    print("  year-on-year shift in the filer mix would manufacture this whole leg:")
    for y in SRC_YEARS:
        raw = pd.read_csv(f"data/raw/coal-receipts/coal_receipts_{y}.csv", low_memory=False)
        raw = raw[raw["Plant Id"].isin(FLEET)]
        freq = raw.groupby("Plant Id")["Reporting Frequency"].agg(
            lambda s: ",".join(sorted(set(map(str, s)))))
        mix = "  ".join(f"{k}={v}" for k, v in freq.value_counts().items())
        print(f"    {y}: {len(freq)} plants  {mix}")


def legs_e_f(annual: pd.DataFrame) -> None:
    """Would `coal_fuel_inventory` bind on SPP -- and is that binding physical?"""
    print("\n== legs E/F: would `coal_fuel_inventory` BIND on SPP, and is it PHYSICAL? ==")
    print("   budget = opening stock (Dec Y-1) + prior-2yr mean receipts   [both <= Y-1]")
    print("   flat   = the row as built: each month capped INDEPENDENTLY at budget/12")
    print("   cum    = the physically correct constraint: stock may never go negative")
    head = (f"{'Y':>5} {'budget_Mt':>10} {'model_Mt':>9} {'headroom%':>10} || "
            f"{'flat_bind':>10} {'flat_worst%':>12} || {'cum_bind':>9} {'min_stock_days':>15}")
    print(head)
    print("-" * len(head))
    for y in range(2019, 2026):
        opening = float(annual["dec"].get(y - 1))
        src = [k for k in (y - 2, y - 1) if k in annual.index]
        rate = float(annual.loc[src, "rec"].mean())
        budget = opening + rate
        cap = budget / 12.0
        monthly, _ = model_monthly_tons(y, annual)
        model_total = float(monthly.sum())

        flat_bind = int((monthly > cap).sum())
        flat_worst = 100.0 * (float(monthly.max()) / cap - 1.0)

        stock, path = opening, []
        for month in range(1, 13):
            stock = stock + rate / 12.0 - float(monthly.loc[month])
            path.append(stock)
        series = pd.Series(path, index=range(1, 13))
        cum_bind = int((series < 0).sum())
        min_days = series.min() / (model_total / 365.0)
        flag = "" if y != 2019 else "  [conv: own year, no 2018 bench]"
        print(f"{y:>5} {budget/1e6:>10.2f} {model_total/1e6:>9.2f} "
              f"{100.0*(budget/model_total - 1.0):>10.1f} || {flat_bind:>10} {flat_worst:>12.1f} "
              f"|| {cum_bind:>9} {min_days:>15.1f}{flag}")
    print("\n  cum_bind 0 in EVERY year with a large positive min_stock_days means the")
    print("  flat cap's binding is a FORM ARTIFACT, not a fuel shortage: the measured")
    print("  stockpile supports exactly the seasonal drawdown the /12 row forbids.")


def main() -> None:
    receipts = load_clean("coal-receipts")
    stocks = load_clean("coal-stocks")
    receipts = receipts[receipts["plant_id"].isin(FLEET)]
    stocks = stocks[stocks["plant_id"].isin(FLEET)]
    annual = fleet_annual(receipts, stocks)

    leg_a(receipts, stocks)
    leg_b(annual, receipts)
    leg_c(receipts, stocks)
    leg_d(receipts)
    legs_e_f(annual)


if __name__ == "__main__":
    main()
