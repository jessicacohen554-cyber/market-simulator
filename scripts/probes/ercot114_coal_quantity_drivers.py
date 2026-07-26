"""ERCOT-114 Task A: measure the two QUANTITY-side coal candidates before building either.

ERCOT-113 closed the whole availability side and the whole price side of the
summer coal over-run (``FINDING-ercot113-summer-coal-decomp-2026-07-26.md``):

* coal availability is already pinned to the measured 60-Day DAM live-HSL at
  plant-hour grain, and its measured seasonal movement is *upward* in summer;
* the coal->CC offer spread *reverses sign* across the three years while the
  over-run holds steady, and coal sits $46-67/MWh inframarginal in every month.

What is left is a mechanism that limits coal ENERGY or its sustained output
RATE independently of price. The charter enumerates two candidates with a
driver, a window and a forward story (rule 18). This probe measures both
**before** any mechanism is written — the discipline that closed six candidates
across ERCOT-111/112/113 without a line of mechanism code.

**A1 - CSAPR ozone-season NOx allowance budget.** Texas coal is in the CSAPR
NOx Ozone Season **Group 2** program (``CSOSG2``; the Good Neighbor Plan's move
of Texas to Group 3 was stayed). Its window, May 1 - Sep 30, matches the
over-run onset. Two things decide whether a budget can bind:

1. **Quantity.** Measured state ozone-season mass against the statutory Texas
   trading budget and its assurance level. A cap the fleet never reaches has a
   zero shadow price and cannot move dispatch.
2. **Price.** The allowance price needed to reverse coal's *measured* merit
   position, against the price allowances actually trade at. The objective
   already carries ``nox_rate x nox_price``, so this is the exact channel a
   built mechanism would use.

**A2 - coal fuel supply / delivery-rate limit.** A stockpile drawn against a
roughly constant rail/mine delivery rate produces a flat utilization ceiling
that does not respond to price. Two independent reads:

1. **Price-response saturation (fleet-wide, the decisive test).** Bin summer
   hours by *actual* RT price and track real coal output as a fraction of the
   measured committed HSL. A fuel-rationed fleet saturates below its envelope
   even in the highest-priced hours; an economically part-loaded fleet walks up
   to its envelope as price rises. This test needs no fuel data at all and
   covers the whole fleet.
2. **Receipts vs consumption (direct driver, partial coverage).** EIA-923
   monthly coal receipts against CAMPD monthly heat input, per plant, with the
   implied intra-year stock cycle. Coverage is partial — the mine-mouth lignite
   plants do not file market fuel receipts — so this read *supports*, and
   cannot by itself overturn, the fleet-wide test.

No LP (rule 15): reads the committed keeper sidecars and raw measured data.

Usage:
    python scripts/probes/ercot114_coal_quantity_drivers.py
    python scripts/probes/ercot114_coal_quantity_drivers.py \
        --arm results/calibration/ercot_netrev_margin
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia930.actuals import load_eia_hourly_benchmark  # noqa: E402

YEARS = (2023, 2024, 2025)
SUMMER = (6, 7, 8, 9)

# --- A1 reference values -----------------------------------------------------
# Texas CSAPR NOx Ozone Season Group 2 trading budget, "2017 and thereafter"
# (40 CFR 97.810(a)(21); confirmed current on eCFR 2026-07-26). The variability
# limit is the same section; the assurance level is budget + variability limit
# (40 CFR 97.825, variability set at 21 % of the state budget for ozone-season
# NOx). EPA's published state-budget workbook (budgets_ozoneseasonnox.xls)
# carries the same three numbers for Texas.
TX_G2_BUDGET_TONS = 52_301.0
TX_G2_VARIABILITY_TONS = 10_983.0
TX_G2_ASSURANCE_TONS = 63_284.0
# Last CSAPR NOx Ozone Season Group 2 allowance prices published in EPA's power
# sector Progress Report market-activity series: the program "started 2021 at
# $200 per ton and ended 2021 at $166 per ton".
G2_ALLOWANCE_PRICE_LO = 166.0
G2_ALLOWANCE_PRICE_HI = 200.0
# The measured coal->CC offer spread, i.e. how deeply inframarginal ERCOT coal
# sits, from FINDING-ercot113-summer-coal-decomp-2026-07-26.md section 6.
COAL_INFRAMARGINAL_LO = 46.0
COAL_INFRAMARGINAL_HI = 67.0
LB_PER_TON = 2000.0

# The measured 60-Day DAM disclosure, site-hour grain: the artifact the
# ercot_thermal_dam_availability overlay reads. Same source as ERCOT-113.
_DAM_SITE = REPO / "data/raw/ercot-thermal-dam-availability-site-hourly.parquet"
_CAMPD_TX = REPO / "data/raw/campd-unit-level"
_E923_RECEIPTS = REPO / "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet"
_E923_GEN = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
_ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"


def _month_of_hour() -> np.ndarray:
    """Month index (1-12) for each of the 8760 model hours (non-leap clock)."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.repeat(np.arange(1, 13), [d * 24 for d in days])


# =============================================================================
# A1 - CSAPR ozone-season NOx allowance budget
# =============================================================================


def _campd_tx(year: int) -> pd.DataFrame | None:
    """Load the CAMPD unit-hour record for Texas, or ``None`` if absent."""
    path = _CAMPD_TX / f"TX_{year}.parquet"
    if not path.exists():
        return None
    return pd.read_parquet(
        path,
        columns=["date", "noxMass", "grossLoad", "heatInput", "facilityId",
                 "primaryFuelInfo", "programCodeInfo"],
    )


def a1_budget_table() -> pd.DataFrame:
    """Measured Texas ozone-season NOx mass against the Group 2 statutory cap.

    ``noxMass`` in the CAMPD hourly feed is pounds; the CSAPR budget is short
    tons, so mass is divided by 2000. The ozone-season control period is
    May 1 - Sep 30 inclusive (40 CFR 97.802 "control period").
    """
    rows = []
    for year in YEARS:
        df = _campd_tx(year)
        if df is None:
            continue
        d = pd.to_datetime(df["date"])
        oz = (d.dt.month >= 5) & (d.dt.month <= 9)
        g2 = df["programCodeInfo"].fillna("").str.contains("CSOSG2")
        coal = df["primaryFuelInfo"].fillna("").str.contains("Coal", case=False)
        state_tons = df.loc[oz & g2, "noxMass"].sum() / LB_PER_TON
        coal_tons = df.loc[oz & g2 & coal, "noxMass"].sum() / LB_PER_TON
        coal_mwh = df.loc[oz & coal, "grossLoad"].sum()
        rows.append(
            {
                "year": year,
                "state_oz_tons": state_tons,
                "coal_oz_tons": coal_tons,
                "coal_share": coal_tons / state_tons if state_tons else np.nan,
                "pct_of_budget": 100.0 * state_tons / TX_G2_BUDGET_TONS,
                "pct_of_assurance": 100.0 * state_tons / TX_G2_ASSURANCE_TONS,
                "headroom_tons": TX_G2_BUDGET_TONS - state_tons,
                "coal_nox_rate_lb_mwh": (
                    coal_tons * LB_PER_TON / coal_mwh if coal_mwh else np.nan
                ),
            }
        )
    return pd.DataFrame(rows).set_index("year")


def a1_price_table(budget: pd.DataFrame) -> pd.DataFrame:
    """The allowance-price channel: $/MWh delivered vs $/MWh required.

    A NOx allowance price enters the objective as ``nox_rate x nox_price``. The
    adder it actually delivers is the traded price times the measured coal NOx
    rate; the adder it would *need* to deliver, to reverse coal's merit
    position, is the measured coal->CC inframarginal spread. The ratio of the
    two is how far short the mechanism falls.
    """
    rows = []
    for year, r in budget.iterrows():
        rate = r["coal_nox_rate_lb_mwh"] / LB_PER_TON  # tons NOx per MWh
        rows.append(
            {
                "year": year,
                "coal_nox_rate_lb_mwh": r["coal_nox_rate_lb_mwh"],
                "adder_at_166": rate * G2_ALLOWANCE_PRICE_LO,
                "adder_at_200": rate * G2_ALLOWANCE_PRICE_HI,
                "breakeven_price_lo": COAL_INFRAMARGINAL_LO / rate,
                "breakeven_price_hi": COAL_INFRAMARGINAL_HI / rate,
                "shortfall_x": COAL_INFRAMARGINAL_LO / (rate * G2_ALLOWANCE_PRICE_HI),
            }
        )
    return pd.DataFrame(rows).set_index("year")


# =============================================================================
# A2 - coal fuel supply / delivery-rate limit
# =============================================================================


def _measured_coal_live(year: int) -> np.ndarray | None:
    """Measured committed coal HSL (MW) per model hour, or ``None``.

    Aggregates the 60-Day DAM site-hour disclosure to a system COAL total per
    date-hour and lays it on the 8760 non-leap clock. Days the disclosure does
    not cover stay NaN so they drop out of the binning rather than reading as
    a zero envelope.
    """
    if not _DAM_SITE.exists():
        return None
    df = pd.read_parquet(_DAM_SITE, columns=["date", "class", "he", "live_mw"])
    df = df[df["class"].astype(str) == "COAL"]
    if df.empty:
        return None
    dt = pd.to_datetime(df["date"].astype(str))
    df = df.assign(_dt=dt)
    df = df[df["_dt"].dt.year == year]
    if df.empty:
        return None
    per_hour = df.groupby(["_dt", "he"], observed=True)["live_mw"].sum().reset_index()
    # he is hour-ending 1..24; map (date, he) onto the non-leap 8760 clock.
    doy = per_hour["_dt"].dt.dayofyear.to_numpy()
    if not per_hour["_dt"].dt.is_leap_year.iloc[0]:
        idx = (doy - 1) * 24 + (per_hour["he"].to_numpy().astype(int) - 1)
    else:  # drop Feb 29 and shift the rest back a day, matching the model clock
        keep = doy != 60
        per_hour, doy = per_hour[keep], doy[keep]
        shifted = np.where(doy > 60, doy - 1, doy)
        idx = (shifted - 1) * 24 + (per_hour["he"].to_numpy().astype(int) - 1)
    out = np.full(8760, np.nan)
    ok = (idx >= 0) & (idx < 8760)
    out[idx[ok]] = per_hour["live_mw"].to_numpy(dtype=float)[ok]
    return out


def _actual_price(year: int) -> np.ndarray | None:
    """Actual ERCOT RT settlement price per hour, or ``None``."""
    if not _ACTUAL_LMP.exists():
        return None
    df = pd.read_parquet(_ACTUAL_LMP)
    df = df[df["year"] == year].sort_values("hour")
    return df["rt"].to_numpy(dtype=float) if not df.empty else None


def _model_coal(bundle: Path, year: int) -> np.ndarray | None:
    """Model P1 coal MW per hour from a bundle's class sidecar, or ``None``."""
    path = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"]
    if df.empty:
        return None
    coal = df[df["klass"].astype(str).str.upper().str.contains("COAL")]
    if coal.empty:
        return None
    return (
        coal.groupby("hour")["mw"]
        .sum()
        .reindex(range(8760), fill_value=0.0)
        .to_numpy(dtype=float)
    )


def _system_price(bundle: Path, year: int) -> np.ndarray | None:
    """Model load-weighted ORDC-inclusive P1 system price per hour, or ``None``.

    Same construction as ``scripts/probes/ercot112_score_coal_arms.py`` C3a, so
    the model price quoted here is the one the coal lane is already scored on.
    """
    path = bundle / "hourly" / f"system_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"].copy()
    if df.empty:
        return None
    df["_p"] = sum(df[c] for c in ("price", "ordc_adder", "rtordpa_overlay"))
    lw = df.groupby("hour").apply(
        lambda d: np.average(d["_p"], weights=d["demand"]), include_groups=False
    )
    return lw.reindex(range(8760)).to_numpy(dtype=float)


def a2_price_response(
    bundle: Path, year: int, months: tuple[int, ...] = SUMMER, n_bins: int = 10
) -> pd.DataFrame | None:
    """Coal utilization of the measured envelope, binned by actual-price decile.

    Localizes the over-run in price space. Model and actual are compared inside
    the *same* bin, against the *same* measured committed-HSL envelope, so the
    comparison is paired and needs no fuel data.

    Two readings the bins discriminate:

    * a fuel/energy budget imposes a uniform opportunity cost, so it withholds
      coal in low-price hours and releases it at high prices — a gap that is
      large at the bottom and closes at the top;
    * an offer-curve level error does the same thing. They are *not*
      distinguishable here, which is why ``a2_receipts_balance`` (does a budget
      exist at all?) is the test that separates them.

    What the bins *do* settle is whether the fleet is hard-capped: a resource
    against a binding physical delivery ceiling cannot reach its envelope at
    any price. ``model_price`` is carried alongside so an over-run at matched
    price can be told apart from one driven by the model's own price formation.
    """
    live = _measured_coal_live(year)
    price = _actual_price(year)
    act = load_eia_hourly_benchmark("ERCOT", year)
    if live is None or price is None or act is None:
        return None
    a_coal = np.asarray(act["coal"], dtype=float)
    m_coal = _model_coal(bundle, year)
    m_price = _system_price(bundle, year)
    mo = _month_of_hour()

    sel = np.isin(mo, months) & np.isfinite(live) & (live > 0) & np.isfinite(price)
    if sel.sum() < n_bins * 10:
        return None
    p, lv, ac = price[sel], live[sel], a_coal[sel]
    mc = m_coal[sel] if m_coal is not None else np.full(sel.sum(), np.nan)
    mp = m_price[sel] if m_price is not None else np.full(sel.sum(), np.nan)

    # Rank-based binning: robust to ERCOT's extremely fat price tail.
    order = np.argsort(p, kind="stable")
    bins = np.empty(len(p), dtype=int)
    bins[order] = np.minimum((np.arange(len(p)) * n_bins) // len(p), n_bins - 1)

    rows = []
    for b in range(n_bins):
        m = bins == b
        rows.append(
            {
                "decile": b + 1,
                "hours": int(m.sum()),
                "price_mean": p[m].mean(),
                "price_max": p[m].max(),
                "model_price": np.nanmean(mp[m]),
                "live_mw": lv[m].mean(),
                "act_coal_mw": ac[m].mean(),
                "act_util": ac[m].sum() / lv[m].sum(),
                "model_coal_mw": np.nanmean(mc[m]),
                "model_util": np.nansum(mc[m]) / lv[m].sum(),
                "util_gap_pp": 100.0
                * (np.nansum(mc[m]) - ac[m].sum())
                / lv[m].sum(),
            }
        )
    return pd.DataFrame(rows).set_index("decile")


def _ercot_coal_plants() -> set[int]:
    """EIA plant ids for ERCOT coal plants, from the EIA-923 BA code.

    ``ba_code`` on the EIA-923 monthly generation record is the reporting
    balancing authority, so ``ERCO`` selects the ERCOT fleet and excludes the
    Texas plants that sit in SPP/MISO (Harrington, Tolk, Welsh, Pirkey).
    """
    if not _E923_GEN.exists():
        return set()
    gen = pd.read_parquet(_E923_GEN, columns=["plant_id", "fuel_type", "ba_code", "year"])
    coal_codes = {"BIT", "SUB", "LIG", "RC", "WC"}
    sel = gen["fuel_type"].isin(coal_codes) & (gen["ba_code"] == "ERCO")
    sel &= gen["year"].isin(YEARS)
    return set(gen.loc[sel, "plant_id"].astype(int).unique())


def a2_receipts_balance() -> pd.DataFrame | None:
    """Monthly coal receipts vs consumption, per ERCOT plant, with stock cycle.

    Receipts (EIA-923 Schedule 5, short tons) and consumption (CAMPD heat
    input, MMBtu) are in different units, so a per-plant heat content is backed
    out by requiring receipts and consumption to balance over the whole
    2023-2025 window — i.e. assuming the stockpile is stationary across three
    years, not within any one of them. The residual monthly balance is then the
    intra-year stock cycle in MMBtu, which is what a delivery-rate limit acts on.
    """
    if not _E923_RECEIPTS.exists():
        return None
    plants = _ercot_coal_plants()
    if not plants:
        return None

    rec = pd.read_parquet(_E923_RECEIPTS)
    rec = rec[
        (rec["fuel_group"] == "Coal")
        & rec["year"].isin(YEARS)
        & rec["plant_id"].astype(int).isin(plants)
    ]
    if rec.empty:
        return None
    rec = rec.assign(plant_id=rec["plant_id"].astype(int))
    rec = (
        rec.groupby(["plant_id", "year", "month"], as_index=False)["quantity"]
        .sum()
        .rename(columns={"quantity": "receipt_tons"})
    )

    cons = []
    for year in YEARS:
        df = _campd_tx(year)
        if df is None:
            continue
        coal = df[df["primaryFuelInfo"].fillna("").str.contains("Coal", case=False)]
        coal = coal[coal["facilityId"].astype(int).isin(plants)]
        if coal.empty:
            continue
        d = pd.to_datetime(coal["date"])
        cons.append(
            coal.assign(
                year=year,
                month=d.dt.month.to_numpy(),
                facilityId=coal["facilityId"].astype(int),
            )
            .groupby(["facilityId", "year", "month"], as_index=False)
            .agg(cons_mmbtu=("heatInput", "sum"), gen_mwh=("grossLoad", "sum"))
            .rename(columns={"facilityId": "plant_id"})
        )
    if not cons:
        return None
    con = pd.concat(cons, ignore_index=True)

    mg = rec.merge(con, on=["plant_id", "year", "month"], how="outer").fillna(
        {"receipt_tons": 0.0, "cons_mmbtu": 0.0, "gen_mwh": 0.0}
    )
    # Implied heat content per plant: total MMBtu burned / total tons received
    # across the full window.
    tot = mg.groupby("plant_id")[["receipt_tons", "cons_mmbtu"]].sum()
    hc = (tot["cons_mmbtu"] / tot["receipt_tons"].where(tot["receipt_tons"] > 0)).rename(
        "mmbtu_per_ton"
    )
    mg = mg.merge(hc, on="plant_id", how="left")
    # Only plants that actually file market fuel receipts can be balanced. The
    # mine-mouth lignite plants burn captive fuel and file no Schedule 5
    # receipts, so they carry consumption with no receipt side; leaving them in
    # would read as a fleet-wide supply shortfall that is really a reporting
    # gap. They are excluded here and reported separately as uncovered.
    mg = mg[mg["mmbtu_per_ton"].notna()].copy()
    mg["receipt_mmbtu"] = mg["receipt_tons"] * mg["mmbtu_per_ton"]
    mg["balance_mmbtu"] = mg["receipt_mmbtu"] - mg["cons_mmbtu"]
    return mg.sort_values(["plant_id", "year", "month"])


def a2_matched_price_bands(
    bundle: Path, year: int, edges: tuple[float, ...] = (10, 15, 20, 25, 30, 40, 60)
) -> pd.DataFrame | None:
    """Coal utilization by ABSOLUTE actual-price band, summer vs shoulder.

    The decile tables bin within a season, so their bands are not comparable
    across seasons. This one fixes the price bands, which is what isolates a
    genuinely *seasonal* driver: if real coal's price-response curve is the
    same in both seasons and the model's is not, the seasonal term is the
    model's, not the market's.
    """
    live = _measured_coal_live(year)
    price = _actual_price(year)
    act = load_eia_hourly_benchmark("ERCOT", year)
    if live is None or price is None or act is None:
        return None
    a_coal = np.asarray(act["coal"], dtype=float)
    m_coal = _model_coal(bundle, year)
    if m_coal is None:
        return None
    mo = _month_of_hour()
    ok = np.isfinite(live) & (live > 0) & np.isfinite(price)

    rows = []
    for lo, hi in zip((0.0,) + edges, edges + (np.inf,)):
        band = ok & (price >= lo) & (price < hi)
        for label, months in (("summer", SUMMER), ("shoulder",
                              tuple(m for m in range(1, 13) if m not in SUMMER))):
            m = band & np.isin(mo, months)
            if m.sum() < 20:
                continue
            rows.append(
                {
                    "band": f"[{lo:g},{hi:g})",
                    "season": label,
                    "hours": int(m.sum()),
                    "price": price[m].mean(),
                    "act_util": a_coal[m].sum() / live[m].sum(),
                    "model_util": m_coal[m].sum() / live[m].sum(),
                    "gap_pp": 100.0 * (m_coal[m].sum() - a_coal[m].sum()) / live[m].sum(),
                }
            )
    if not rows:
        return None
    out = pd.DataFrame(rows)
    piv = out.pivot(index="band", columns="season",
                    values=["hours", "price", "act_util", "model_util", "gap_pp"])
    # Preserve band order rather than the pivot's lexical sort.
    order = [f"[{lo:g},{hi:g})" for lo, hi in zip((0.0,) + edges, edges + (np.inf,))]
    return piv.reindex([b for b in order if b in piv.index])


def a2_stock_cycle(bal: pd.DataFrame) -> pd.DataFrame:
    """Fleet monthly balance and the cumulative (relative) stock trajectory.

    ``days_burn`` expresses the cumulative balance in days of that month's burn
    rate — the unit a stockpile constraint is actually stated in. The level is
    relative (the true opening stock is not in this dataset); what is readable
    is the *depth* of the summer drawdown against the fleet's own burn rate.
    """
    fleet = (
        bal.groupby(["year", "month"], as_index=False)[
            ["receipt_mmbtu", "cons_mmbtu", "balance_mmbtu"]
        ]
        .sum()
        .sort_values(["year", "month"])
    )
    fleet["cum_balance_mmbtu"] = fleet["balance_mmbtu"].cumsum()
    daily = fleet["cons_mmbtu"] / 30.4
    fleet["days_burn"] = fleet["cum_balance_mmbtu"] / daily.where(daily > 0)
    fleet["receipt_over_cons"] = fleet["receipt_mmbtu"] / fleet["cons_mmbtu"].where(
        fleet["cons_mmbtu"] > 0
    )
    return fleet


def main() -> None:
    """Print the A1 and A2 measurement tables for every year."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--arm",
        type=Path,
        default=REPO / "results/calibration/ercot_netrev_margin",
        help="bundle whose P1 sidecars supply the model comparison series",
    )
    args = ap.parse_args()

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 40)

    print("=" * 78)
    print("A1 - CSAPR NOx Ozone Season GROUP 2: does the budget bind?")
    print("=" * 78)
    print(
        f"Texas statutory budget {TX_G2_BUDGET_TONS:,.0f} t | "
        f"variability {TX_G2_VARIABILITY_TONS:,.0f} t | "
        f"assurance {TX_G2_ASSURANCE_TONS:,.0f} t   [40 CFR 97.810 / 97.825]"
    )
    budget = a1_budget_table()
    print(budget.round(3).to_string())
    print()
    print("A1 price channel ($/MWh):")
    print(a1_price_table(budget).round(4).to_string())

    print()
    print("=" * 78)
    print("A2 - fuel supply / delivery rate")
    print("=" * 78)
    print("(1) Price-response saturation of the measured committed HSL")
    shoulder = tuple(m for m in range(1, 13) if m not in SUMMER)
    for label, months in (("SUMMER Jun-Sep", SUMMER), ("SHOULDER (control)", shoulder)):
        for year in YEARS:
            tab = a2_price_response(args.arm, year, months=months)
            if tab is None:
                print(f"  {label} {year}: unavailable")
                continue
            print(f"\n  --- {label} {year} (actual RT price deciles) ---")
            print(tab.round(3).to_string())

    print()
    print("(1b) MATCHED absolute price bands: summer vs shoulder")
    seasonal = []
    for year in YEARS:
        tab = a2_matched_price_bands(args.arm, year)
        if tab is None:
            print(f"  {year}: unavailable")
            continue
        print(f"\n  --- {year} ---")
        print(tab.round(3).to_string())
        both = tab.dropna(subset=[("act_util", "summer"), ("act_util", "shoulder")])
        seasonal.append(
            {
                "year": year,
                "bands": len(both),
                "act_summer_lift_pp": 100.0
                * (both[("act_util", "summer")] - both[("act_util", "shoulder")]).mean(),
                "model_summer_lift_pp": 100.0
                * (both[("model_util", "summer")] - both[("model_util", "shoulder")]).mean(),
            }
        )
    if seasonal:
        sm = pd.DataFrame(seasonal).set_index("year")
        sm["excess_pp"] = sm["model_summer_lift_pp"] - sm["act_summer_lift_pp"]
        sm["ratio"] = sm["model_summer_lift_pp"] / sm["act_summer_lift_pp"]
        print()
        print("  HEADLINE - mean summer-minus-shoulder utilization lift at MATCHED price:")
        print(sm.round(2).to_string())

    print()
    print("(2) ERCOT coal receipts vs consumption (EIA-923 x CAMPD)")
    bal = a2_receipts_balance()
    if bal is None:
        print("  unavailable")
        return
    plants = sorted(bal["plant_id"].astype(int).unique())
    print(f"  covered ERCOT coal plants: {plants}")
    hc = bal.groupby("plant_id")["mmbtu_per_ton"].first()
    print("  implied heat content (MMBtu/ton):")
    print(hc.round(2).to_string())
    print()
    print("  fleet monthly balance and relative stock cycle:")
    print(a2_stock_cycle(bal).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
