"""neiso-76 — Phase-0 of the neiso-75 charter: is the SUPPLY-CONDUCT limb of
NEISO's DA-bid offer formation real? MEASUREMENT ONLY, NO LP.

The charter (`results/calibration/CHARTER-neiso75-c3c-frontier-2026-08-02.md`
§4) authorizes exactly this: measure the submitted DA book's WITHIN-DAY
movement and test it against the pre-registered kill rules K1–K5. A solve arm
is NOT authorized by that charter and is not attempted here.

Theory of change being tested (charter §4, stated before any measurement): the
keeper's offer stack is within-day STATIC by construction (daily fuel shape,
static tranche markups, run-constant P1 startup amortization), while xiso-1's
attribution has `CC_REGULAR` absorbing 2,045 MW of the 4,117 MW diurnal demand
swing with peakers already online at the trough — the same offer band marginal
at h02 and h17. If the MEASURED submitted book moves within the day, that
movement is a forward-conditionable conduct object the model lacks, and it is
the missing amplitude. If it does not move, the supply-conduct limb is empty
and that kill is itself decisive.

THE FROZEN STATISTIC (charter §4, verbatim; frozen BEFORE this session):

    per (asset, day), the capacity-weighted mean submitted incremental-segment
    price over peak hours (h16-19 EST) minus over trough hours (h01-04 EST);
    aggregated capacity-weighted over the NON-fast-start band (the complement
    of neiso-58's physics selection, Claim30 < 0.9 x EcoMax), per year;
    conditioned only on hour-of-day x net-load bin x month.

Read as implemented:

* incremental-segment price, capacity weighted = sum(p_i * dMW_i) / sum(dMW_i)
  over an asset-hour's non-null offer segments. The ISO-NE report's
  ``Segment N MW`` columns are INCREMENTAL block widths (verified: they sum to
  Economic Maximum), so this is the mean offer price over the asset's own
  offered capacity — the body band, not the tail rung (charter §3 L6 draws
  that boundary: this is a NEW identification, never a re-conditioning of the
  neiso-58 Limb-B tail artifact).
* peak window = hours-beginning 16-19 = report hour-ending 17-20; trough =
  hours-beginning 01-04 = HE 02-05. The alternate reading (HE 16-19 / HE 01-04)
  is reported as a sensitivity — the verdict is quoted on the primary.
* PAIRED: an (asset, day) contributes only if it offers in BOTH windows that
  day, so the statistic is within-asset movement and cannot be a composition
  artifact. The unpaired aggregate is reported as a control.
* capacity weight = the asset-day's mean Economic Maximum over its window
  hours.

KILL RULES (pre-registered in charter §4; evaluated verbatim here):

* K1 movement floor: the supply limb dies if fleet-level within-day movement
  is < $5/MWh in 2023 and 2024, < $8/MWh in 2025 (~25 % of each year's
  measured hour-of-day range gap $18.93 / $22.14 / $31.17).
* K2 conditioning admissibility: conditioning is hour-of-day x net-load x
  month, NEVER the clearing price or the residual. Measured here by computing
  the conditioned (net-load bin x month) movement surface with no price input
  anywhere in the construction.
* K3 demand-limb existence + lambda0 attractor: existence checked by
  ``--check-demand-book`` (does ISO-NE publish a SUBMITTED priced DA
  demand/virtual book?); the attractor half is a separate measurement.
* K4 fuel-granularity robustness: every conduct statistic recomputed excluding
  the 34 Algonquin fuel-tail days (caiso-154: the top ceil(1 %) of 2023-25
  daily Algonquin prints, ties included = all days >= $25.00). A component
  moving > 15 % relative is fuel-series granularity, not conduct.
* K5 event-day coverage: the statistic must be computable on the five 2025
  event days (Jun-23/24/25, Jul-28/29).

AUXILIARY (report-only, price-free, NOT a kill-rule input): the fixed-depth
book traversal. For each hour, the aggregate submitted supply curve is built
over the whole offering fleet and the marginal offer price is read at fixed
depths q of cumulative offered capacity. The hour-of-day range of P_q(h) is
the amplitude a perfect static-merit-order model would inherit from the real
book's own CONDUCT at constant quantity; comparing it to the measured DA
hour-of-day range ($25.96 / $28.96 / $44.47) and to the keeper's own
($7.03 / $6.82 / $13.30) splits the real amplitude into "the book moves" vs
"the market traverses the book". No price series enters this construction.

Rule 13: nothing here is fed back into a solve; measured prices are quoted
only as the validation target the movement is sized against (the hod-range
gaps, which are already on record from xiso-1/neiso-74).

Usage:
    python scripts/probes/_neiso76_dabid_phase0.py                 # full corpus
    python scripts/probes/_neiso76_dabid_phase0.py --years 2025
    python scripts/probes/_neiso76_dabid_phase0.py --check-demand-book
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import NEISO_AS_DIR  # noqa: E402

RAW_DIR = NEISO_AS_DIR / "da-energy-offers"

#: ISO-NE fast-start concept (neiso-58 physics selection). The NON-fast-start
#: band this probe measures is its COMPLEMENT: Claim 30 < 0.9 x EcoMax.
FAST_START_CLAIM30_FRAC = 0.9

#: Charter §4 windows, primary reading: hours-BEGINNING 16-19 and 01-04, i.e.
#: report hour-ending labels 17-20 and 02-05.
PEAK_HE = (17, 18, 19, 20)
TROUGH_HE = (2, 3, 4, 5)
#: The alternate reading (report HE 16-19 / HE 01-04), reported as sensitivity.
PEAK_HE_ALT = (16, 17, 18, 19)
TROUGH_HE_ALT = (1, 2, 3, 4)

#: K1 bars (charter §4) and the measured hour-of-day range gaps they are 25 %
#: of (xiso-1 / neiso-75 §2: model hod range $7.03/$6.82/$13.30 vs DA
#: $25.96/$28.96/$44.47).
K1_BAR = {2023: 5.0, 2024: 5.0, 2025: 8.0}
HOD_GAP = {2023: 18.93, 2024: 22.14, 2025: 31.17}
MODEL_HOD_RANGE = {2023: 7.03, 2024: 6.82, 2025: 13.30}
DA_HOD_RANGE = {2023: 25.96, 2024: 28.96, 2025: 44.47}

#: K4 (caiso-154): the NEISO fuel-tail set is every 2023-25 day whose model
#: Algonquin daily print is >= $25.00 (top ceil(1 %) of days, ties included).
ALGONQUIN_TAIL_USD = 25.00

#: K5: the five 2025 C3c event days (charter §2 / neiso-75 §2).
K5_EVENT_DAYS = ("20250623", "20250624", "20250625", "20250728", "20250729")

#: Fixed depths for the auxiliary book traversal (fractions of the hour's own
#: total offered capacity). Price-free.
AUX_DEPTHS = (0.50, 0.60, 0.70, 0.80, 0.90, 0.95)

#: Fixed ABSOLUTE quantities (MW) for the constant-quantity read of the same
#: book. NEISO load runs ~11-26 GW; these bracket the traversal the market
#: actually performs within a day.
AUX_ABS_MW = (12000, 14000, 16000, 18000, 20000, 22000)


# --------------------------------------------------------------------------
# corpus
# --------------------------------------------------------------------------
def _day_files(years: list[int]) -> tuple[list[Path], dict]:
    """Present, non-empty day files per year + the coverage record."""
    files, coverage = [], {}
    for year in years:
        present = sorted(RAW_DIR.glob(f"hbdayaheadenergyoffer_{year}*.csv"))
        nonempty = [p for p in present if p.stat().st_size > 1000]
        n_days = (dt.date(year, 12, 31) - dt.date(year, 1, 1)).days + 1
        coverage[year] = {
            "days_in_year": n_days,
            "files": len(present),
            "nonempty": len(nonempty),
        }
        files.extend(nonempty)
    return files, coverage


def _parse_day(path: Path) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """One day's offers -> (asset-hour frame, segment-ladder frame).

    Asset-hour columns: day, he, asset_id, cw_price, top_price, eco_max,
    seg_mw, fast_start, status.

    ``cw_price`` is the capacity-weighted mean incremental-segment price (the
    frozen statistic's per-asset-hour primitive); ``top_price`` the highest
    segment price (the neiso-58 tail-rung basis, auxiliary only).
    """
    recs, segrows = [], []
    with path.open(newline="") as fh:
        for r in csv.reader(fh):
            if not r or r[0] != "D":
                continue
            try:
                eco_max = float(r[7] or 0.0)
                claim30 = float(r[34] or 0.0)
            except (ValueError, IndexError):
                continue
            status = r[35].strip() if len(r) > 35 else ""
            if eco_max <= 0.0 or status not in ("ECONOMIC", "MUST_RUN"):
                continue
            prices, mws = [], []
            for k in range(13, 33, 2):
                pv = r[k] if k < len(r) else ""
                mv = r[k + 1] if k + 1 < len(r) else ""
                if pv in ("", None) or mv in ("", None):
                    continue
                try:
                    p, w = float(pv), float(mv)
                except ValueError:
                    continue
                if w <= 0.0:
                    continue
                prices.append(p)
                mws.append(w)
            if not prices:
                continue
            p_arr = np.asarray(prices, float)
            w_arr = np.asarray(mws, float)
            he = int(r[2].strip().upper().rstrip("X"))
            recs.append(
                (
                    r[1],
                    he,
                    int(r[4]),
                    float(np.average(p_arr, weights=w_arr)),
                    float(p_arr.max()),
                    eco_max,
                    float(w_arr.sum()),
                    bool(claim30 >= FAST_START_CLAIM30_FRAC * eco_max),
                    status,
                )
            )
            for p, w in zip(p_arr, w_arr):
                segrows.append((he, float(p), float(w)))
    if not recs:
        return None, None
    df = pd.DataFrame(
        recs,
        columns=[
            "day",
            "he",
            "asset_id",
            "cw_price",
            "top_price",
            "eco_max",
            "seg_mw",
            "fast_start",
            "status",
        ],
    )
    df["day"] = pd.to_datetime(df["day"], format="%m/%d/%Y")
    segs = pd.DataFrame(segrows, columns=["he", "seg_price", "seg_dmw"])
    segs["day"] = df["day"].iloc[0]
    return df, segs


def _load_offers(years: list[int], with_aux: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Parse the corpus once: the asset-hour frame + (streamed, per day so the
    segment ladder never has to be held whole) the fixed-depth aux frame."""
    files, coverage = _day_files(years)
    demand = _demand_lookup(years) if with_aux else None
    print(f"parsing {len(files)} day files ...", flush=True)
    frames, aux = [], []
    for i, p in enumerate(files, 1):
        d, segs = _parse_day(p)
        if d is not None:
            frames.append(d)
            if with_aux:
                aux.append(_fixed_depth_prices(segs, demand=demand))
        if i % 200 == 0:
            print(f"  ... {i}/{len(files)}", flush=True)
    offers = pd.concat(frames, ignore_index=True)
    offers["year"] = offers["day"].dt.year
    offers["month"] = offers["day"].dt.month
    aux_df = pd.concat(aux, ignore_index=True) if aux else pd.DataFrame()
    return offers, aux_df, coverage


# --------------------------------------------------------------------------
# conditioning inputs (price-free — K2)
# --------------------------------------------------------------------------
def _netload_pct(years: list[int]) -> pd.DataFrame:
    """(local day, hour-ending) -> within-year net-load percentile.

    Byte-identical construction to
    ``scripts/data/derive_neiso_offer_surface.py::_netload_pct`` (EIA-930 ISNE
    Demand - wind - solar, percentile-ranked within year): the forward-native
    tightness driver, no price anywhere.
    """
    from market_sim.data.eia_loader import _eia_hourly_frame

    frames = []
    for year in years:
        df = _eia_hourly_frame("ISNE", year)
        if df is None:
            raise SystemExit(f"EIA-930 ISNE {year}: no clean 8760 frame")
        net = (
            df["Demand"].to_numpy(float)
            - df["NG: WND"].to_numpy(float)
            - df["NG: SUN"].to_numpy(float)
        )
        q = pd.Series(net).rank(pct=True).to_numpy()
        local = pd.DatetimeIndex(df["Local time"])
        frames.append(
            pd.DataFrame(
                {"day": local.normalize(), "he": local.hour + 1, "q": q, "year": year}
            )
        )
    out = pd.concat(frames, ignore_index=True)
    return out.groupby(["day", "he"], as_index=False).agg(
        q=("q", "mean"), year=("year", "first")
    )


def _algonquin_tail_days() -> set[pd.Timestamp]:
    """The caiso-154 NEISO fuel-tail day set: model Algonquin daily >= $25.00."""
    from market_sim.data.fuel import ALGONQUIN_DAILY_PATH

    df = pd.read_csv(ALGONQUIN_DAILY_PATH, parse_dates=["date"])
    s = df.set_index("date")["algonquin_citygate_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    s = s.reindex(full).ffill()
    s = s[(s.index.year >= 2023) & (s.index.year <= 2025)]
    return set(s[s >= ALGONQUIN_TAIL_USD].index)


# --------------------------------------------------------------------------
# the frozen statistic
# --------------------------------------------------------------------------
def _movement(
    offers: pd.DataFrame,
    peak_he: tuple[int, ...],
    trough_he: tuple[int, ...],
    paired: bool = True,
) -> pd.DataFrame:
    """Per (asset, day): peak-window minus trough-window capacity-weighted
    mean offer price, with the asset-day capacity weight.

    ``paired`` requires the asset to offer in BOTH windows that day (the
    charter's within-asset construction); False keeps asset-days present in
    only one window, as the composition control.
    """
    pk = offers[offers["he"].isin(peak_he)]
    tr = offers[offers["he"].isin(trough_he)]
    gp = pk.groupby(["asset_id", "day"]).agg(
        peak=("cw_price", "mean"),
        peak_top=("top_price", "mean"),
        cap_p=("eco_max", "mean"),
        n_p=("cw_price", "size"),
    )
    gt = tr.groupby(["asset_id", "day"]).agg(
        trough=("cw_price", "mean"),
        trough_top=("top_price", "mean"),
        cap_t=("eco_max", "mean"),
        n_t=("cw_price", "size"),
    )
    how = "inner" if paired else "outer"
    m = gp.join(gt, how=how).reset_index()
    m["move"] = m["peak"] - m["trough"]
    m["move_top"] = m["peak_top"] - m["trough_top"]
    m["cap"] = m[["cap_p", "cap_t"]].mean(axis=1)
    m["year"] = m["day"].dt.year
    m["month"] = m["day"].dt.month
    return m.dropna(subset=["move"])


def _wmean(v: np.ndarray, w: np.ndarray) -> float:
    w = np.asarray(w, float)
    if w.sum() <= 0:
        return float("nan")
    return float(np.average(np.asarray(v, float), weights=w))


def _fleet_movement(mv: pd.DataFrame, col: str = "move") -> dict[int, float]:
    return {
        int(y): _wmean(g[col].to_numpy(), g["cap"].to_numpy())
        for y, g in mv.groupby("year")
    }


# --------------------------------------------------------------------------
# auxiliary: fixed-depth book traversal (price-free)
# --------------------------------------------------------------------------
def _fixed_depth_prices(
    segs: pd.DataFrame,
    depths=AUX_DEPTHS,
    abs_mw=AUX_ABS_MW,
    demand: dict | None = None,
) -> pd.DataFrame:
    """Marginal submitted-offer price at fixed depths of the hour's aggregate
    submitted supply curve — the TRUE segment ladder, not an asset-mean proxy.

    For each hour: sort every submitted (price, dMW) segment of every offering
    asset ascending by price, walk cumulative MW, and read the marginal price
    at (a) depth ``q`` of the hour's own total offered MW and (b) fixed
    ABSOLUTE quantities. (b) is the constant-quantity read: its hour-of-day
    range is what the real book alone contributes to diurnal amplitude with
    the traversal held still. Quantity-free of any model or actual series;
    no price series enters.
    """
    rows = []
    for (day, he), g in segs.groupby(["day", "he"], sort=False):
        p = g["seg_price"].to_numpy(float)
        w = g["seg_dmw"].to_numpy(float)
        order = np.argsort(p)
        p, w = p[order], w[order]
        cw = np.cumsum(w)
        tot = cw[-1]
        rec = {"day": day, "he": he, "offered_mw": float(tot)}
        for q in depths:
            idx = min(int(np.searchsorted(cw, q * tot, side="left")), len(p) - 1)
            rec[f"p{int(q * 100)}"] = float(p[idx])
        for q_mw in abs_mw:
            if q_mw > tot:
                rec[f"a{q_mw}"] = np.nan
                continue
            idx = min(int(np.searchsorted(cw, float(q_mw), side="left")), len(p) - 1)
            rec[f"a{q_mw}"] = float(p[idx])
        if demand is not None:
            d_mw = demand.get((day, he))
            for tag, off in (("dem", 0.0), ("dem_imp", 3000.0)):
                if d_mw is None or not np.isfinite(d_mw) or (d_mw - off) > tot:
                    rec[tag] = np.nan
                    continue
                idx = min(
                    int(np.searchsorted(cw, float(d_mw - off), side="left")), len(p) - 1
                )
                rec[tag] = float(p[idx])
            rec["demand_mw"] = float(d_mw) if d_mw is not None else np.nan
        rows.append(rec)
    out = pd.DataFrame(rows)
    out["year"] = out["day"].dt.year
    return out


def _hod_range(df: pd.DataFrame, col: str) -> dict[int, float]:
    """Mean hour-of-day profile range (max-min) per year — the xiso-1 statistic."""
    res = {}
    for y, g in df.groupby("year"):
        prof = g.groupby("he")[col].mean()
        res[int(y)] = float(prof.max() - prof.min())
    return res


def _hod_shape(df: pd.DataFrame, col: str, year: int) -> str:
    """`range (peak HEnn / trough HEnn)` — the SIGN of the diurnal structure.

    A book whose fixed-depth marginal price peaks overnight is inverted
    relative to the demand cycle; the range alone cannot say so.
    """
    g = df[df["year"] == year]
    prof = g.groupby("he")[col].mean().dropna()
    if prof.empty:
        return "--"
    return (
        f"{prof.max() - prof.min():.2f} (max HE{int(prof.idxmax())}"
        f" / min HE{int(prof.idxmin())})"
    )


def _demand_lookup(years: list[int]) -> dict:
    """(local day, hour-ending) -> measured ISNE demand MW (EIA-930).

    A physical quantity, not a price: used only to cross the real submitted
    book at the real hourly quantity (the traversal read).
    """
    from market_sim.data.eia_loader import _eia_hourly_frame

    out = {}
    for year in years:
        df = _eia_hourly_frame("ISNE", year)
        if df is None:
            raise SystemExit(f"EIA-930 ISNE {year}: no clean 8760 frame")
        local = pd.DatetimeIndex(df["Local time"])
        for day, he, mw in zip(
            local.normalize(), local.hour + 1, df["Demand"].to_numpy(float)
        ):
            out[(day, int(he))] = float(mw)
    return out


# --------------------------------------------------------------------------
# K3(i): does ISO-NE publish a SUBMITTED priced DA demand/virtual book?
# --------------------------------------------------------------------------
def check_demand_book(days: list[str]) -> None:
    """Fetch the DA demand-bid report for ``days`` and report its identification
    properties: price axis, bid types, virtual presence (the nyiso-94 test)."""
    import importlib.util
    import urllib.request

    spec = importlib.util.spec_from_file_location(
        "neiso_fetch", REPO / "scripts" / "data" / "fetch_neiso_da_energy_offers.py"
    )
    fetch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fetch)
    opener = fetch._opener()
    for day in days:
        url = f"https://www.iso-ne.com/transform/csv/hbdayaheaddemandbid?start={day}"
        req = urllib.request.Request(url, headers={"Referer": fetch.REPORT_PAGE})
        with opener.open(req, timeout=180) as resp:
            body = resp.read()
        rows = [r for r in csv.reader(body.decode("utf-8").splitlines()) if r]
        head = next(r for r in rows if r and r[0] == "H")
        data = [r for r in rows if r and r[0] == "D"]
        types = {}
        priced_mw = unpriced_mw = 0.0
        for r in data:
            bid_type = r[6].strip('"')
            types[bid_type] = types.get(bid_type, 0) + 1
            for k in range(8, len(r) - 1, 2):
                pv, mv = r[k], r[k + 1]
                if mv in ("", None):
                    continue
                try:
                    w = float(mv)
                except ValueError:
                    continue
                if pv in ("", None):
                    unpriced_mw += w
                else:
                    priced_mw += w
        print(f"\n{day}: {len(data)} bid-hour rows; {len(head) - 1} columns")
        print(f"  bid types: {types}")
        print(f"  segment MW with a PRICE: {priced_mw:,.0f}; without: {unpriced_mw:,.0f}")


# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--edges", nargs="*", type=float, default=[0.80, 0.90, 0.97])
    ap.add_argument("--check-demand-book", nargs="*", default=None)
    ap.add_argument("--skip-aux", action="store_true")
    args = ap.parse_args(argv)

    if args.check_demand_book is not None:
        days = args.check_demand_book or ["20230117", "20240115", "20250624"]
        check_demand_book(days)
        return 0

    offers, aux_df, coverage = _load_offers(args.years, with_aux=not args.skip_aux)
    print("\n=== CORPUS COVERAGE ===")
    for y, c in coverage.items():
        print(f"  {y}: {c['nonempty']}/{c['days_in_year']} non-empty day files")
    band = offers[~offers["fast_start"]]
    fs = offers[offers["fast_start"]]
    print(
        f"  offer rows {len(offers):,}; NON-fast-start band {len(band):,} rows / "
        f"{band.asset_id.nunique()} assets; fast-start {len(fs):,} rows / "
        f"{fs.asset_id.nunique()} assets"
    )

    # ---- K5 first: event-day coverage (charter §4) ----
    print("\n=== K5 — 2025 event-day coverage ===")
    have_days = set(offers["day"].dt.strftime("%Y%m%d"))
    k5_missing = [d for d in K5_EVENT_DAYS if d not in have_days]
    band_days = set(band["day"].dt.strftime("%Y%m%d"))
    k5_band_missing = [d for d in K5_EVENT_DAYS if d not in band_days]
    print(f"  corpus: {[d for d in K5_EVENT_DAYS if d in have_days]}")
    print(f"  missing from corpus: {k5_missing or 'none'}")
    print(f"  missing from the NON-fast-start band: {k5_band_missing or 'none'}")
    print(f"  K5 -> {'FIRES (coverage incomplete)' if k5_missing else 'PASSES'}")

    # ---- the frozen statistic ----
    mv = _movement(band, PEAK_HE, TROUGH_HE, paired=True)
    fleet = _fleet_movement(mv)
    mv_unpaired = _movement(band, PEAK_HE, TROUGH_HE, paired=False)
    fleet_unpaired = _fleet_movement(mv_unpaired)
    mv_alt = _movement(band, PEAK_HE_ALT, TROUGH_HE_ALT, paired=True)
    fleet_alt = _fleet_movement(mv_alt)
    fleet_top = _fleet_movement(mv, col="move_top")
    mv_fs = _movement(fs, PEAK_HE, TROUGH_HE, paired=True)
    fleet_fs = _fleet_movement(mv_fs)

    print("\n=== THE FROZEN STATISTIC (charter §4) — within-day movement of the")
    print("    NON-fast-start band's submitted book, $/MWh ===")
    print(
        f"{'year':>6} {'movement':>10} {'K1 bar':>8} {'hod gap':>8} "
        f"{'share of gap':>13} {'verdict':>10} | {'unpaired':>9} {'HE16-19':>9} "
        f"{'top-rung':>9} {'fast-start':>11}"
    )
    k1_fires = {}
    for y in sorted(fleet):
        m = fleet[y]
        bar = K1_BAR[y]
        gap = HOD_GAP[y]
        k1_fires[y] = m < bar
        print(
            f"{y:>6} {m:>10.3f} {bar:>8.2f} {gap:>8.2f} {m / gap * 100:>12.1f}% "
            f"{'FIRES' if k1_fires[y] else 'survives':>10} | "
            f"{fleet_unpaired[y]:>9.3f} {fleet_alt[y]:>9.3f} "
            f"{fleet_top.get(y, float('nan')):>9.3f} "
            f"{fleet_fs.get(y, float('nan')):>11.3f}"
        )
    print(
        f"  K1 -> {'FIRES' if any(k1_fires.values()) else 'survives'} "
        f"(charter: any year below its bar kills the limb)"
    )

    # ---- distribution: is the book flat within the day at all? ----
    print("\n=== the book's within-day distribution (paired asset-days) ===")
    print(
        f"{'year':>6} {'n asset-days':>13} {'flat (<$0.01)':>14} {'|move|<$1':>10} "
        f"{'p10':>8} {'p25':>8} {'p50':>8} {'p75':>8} {'p90':>8} {'cap-w mean':>11}"
    )
    for y, g in mv.groupby("year"):
        v = g["move"].to_numpy()
        print(
            f"{int(y):>6} {len(g):>13,} "
            f"{np.mean(np.abs(v) < 0.01) * 100:>13.1f}% "
            f"{np.mean(np.abs(v) < 1.0) * 100:>9.1f}% "
            f"{np.percentile(v, 10):>8.2f} {np.percentile(v, 25):>8.2f} "
            f"{np.percentile(v, 50):>8.2f} {np.percentile(v, 75):>8.2f} "
            f"{np.percentile(v, 90):>8.2f} "
            f"{_wmean(v, g['cap'].to_numpy()):>11.3f}"
        )

    # ---- the band's own hour-of-day offer profile (the movement generalized) ----
    print("\n=== the NON-fast-start band's hour-of-day submitted-offer profile ===")
    print("    (capacity-weighted mean incremental-segment price, $/MWh)")
    for y, g in band.groupby("year"):
        prof = g.groupby("he").apply(
            lambda s: _wmean(s["cw_price"].to_numpy(), s["eco_max"].to_numpy()),
            include_groups=False,
        )
        print(
            f"  {int(y)}: min ${prof.min():.2f} (HE{int(prof.idxmin())}) -> "
            f"max ${prof.max():.2f} (HE{int(prof.idxmax())}), "
            f"hod range ${prof.max() - prof.min():.2f} "
            f"vs DA ${DA_HOD_RANGE[int(y)]:.2f} / model ${MODEL_HOD_RANGE[int(y)]:.2f}"
        )
        print(
            "        HE01-24: "
            + " ".join(f"{prof.get(h, float('nan')):.1f}" for h in range(1, 25))
        )

    # ---- composition controls on the frozen statistic ----
    print("\n=== composition controls on the frozen statistic ===")
    econ = band[band["status"] == "ECONOMIC"]
    mv_econ = _movement(econ, PEAK_HE, TROUGH_HE, paired=True)
    fleet_econ = _fleet_movement(mv_econ)
    for y in sorted(fleet):
        g = mv[mv["year"] == y]
        print(
            f"  {y}: cap-weighted {fleet[y]:+.3f} | unweighted "
            f"{g['move'].mean():+.3f} | median {g['move'].median():+.3f} | "
            f"ECONOMIC-only {fleet_econ.get(y, float('nan')):+.3f} | "
            f"movers (|move|>=$0.01) {int((g['move'].abs() >= 0.01).sum()):,} of "
            f"{len(g):,}"
        )
    print("  the five largest capacity-weighted contributions (masked asset IDs):")
    for y, g in mv.groupby("year"):
        g = g.assign(contrib=g["move"] * g["cap"])
        by_asset = (
            g.groupby("asset_id")
            .agg(contrib=("contrib", "sum"), cap=("cap", "mean"), n=("move", "size"))
            .sort_values("contrib")
        )
        tot = g["cap"].sum()
        head = by_asset.head(5)
        print(
            f"    {int(y)}: "
            + "; ".join(
                f"#{i} {r.contrib / tot:+.3f} $/MWh (cap {r.cap:,.0f} MW, {r.n} days)"
                for i, r in head.iterrows()
            )
        )

    # ---- K2: the conditioned surface, no price anywhere ----
    print("\n=== K2 — conditioning admissibility (hour-of-day x net-load x month) ===")
    nl = _netload_pct(args.years)
    # asset-day net-load bin: the day's own peak-window mean percentile.
    nl_pk = (
        nl[nl["he"].isin(PEAK_HE)].groupby("day", as_index=False).agg(q=("q", "mean"))
    )
    mvq = mv.merge(nl_pk, on="day", how="left").dropna(subset=["q"])
    edges = np.asarray(args.edges, float)
    mvq["bin"] = np.searchsorted(edges, mvq["q"].to_numpy(), side="right")
    print(f"  net-load bin edges (percentile): {list(edges)}")
    print(f"{'year':>6} " + " ".join(f"{'bin' + str(b):>9}" for b in range(len(edges) + 1)))
    for y, g in mvq.groupby("year"):
        cells = []
        for b in range(len(edges) + 1):
            s = g[g["bin"] == b]
            cells.append(
                f"{_wmean(s['move'].to_numpy(), s['cap'].to_numpy()):>9.3f}"
                if len(s)
                else f"{'--':>9}"
            )
        print(f"{int(y):>6} " + " ".join(cells))
    print("  conditioned max-cell movement per year (the best any admissible")
    print("  conditioning can deliver without touching price):")
    for y, g in mvq.groupby("year"):
        best = max(
            (
                _wmean(s["move"].to_numpy(), s["cap"].to_numpy())
                for _, s in g.groupby("bin")
                if len(s)
            ),
            default=float("nan"),
        )
        print(
            f"    {int(y)}: {best:.3f} $/MWh vs K1 bar {K1_BAR[int(y)]:.2f} "
            f"-> {'clears the bar' if best >= K1_BAR[int(y)] else 'below the bar'}"
        )
    # month x hod granularity, reported for completeness
    print("  monthly cap-weighted movement (min / max month per year):")
    for y, g in mvq.groupby("year"):
        mm = g.groupby("month").apply(
            lambda s: _wmean(s["move"].to_numpy(), s["cap"].to_numpy()),
            include_groups=False,
        )
        print(
            f"    {int(y)}: min {mm.min():.3f} (month {int(mm.idxmin())}), "
            f"max {mm.max():.3f} (month {int(mm.idxmax())})"
        )

    # ---- K4: fuel-tail robustness ----
    print("\n=== K4 — Algonquin fuel-tail robustness (>= $25.00 days excluded) ===")
    tail_days = _algonquin_tail_days()
    in_corpus = sorted(d for d in tail_days if d in set(offers["day"]))
    print(f"  tail-day set: {len(tail_days)} days 2023-25; {len(in_corpus)} in corpus")
    mv_k4 = mv[~mv["day"].isin(tail_days)]
    fleet_k4 = _fleet_movement(mv_k4)
    k4_fires = {}
    for y in sorted(fleet):
        base, excl = fleet[y], fleet_k4.get(y, float("nan"))
        rel = abs(excl - base) / abs(base) * 100 if base else float("nan")
        k4_fires[y] = rel > 15.0
        print(
            f"  {y}: {base:.3f} -> {excl:.3f} ({rel:+.1f}% relative) "
            f"-> {'FIRES (fuel granularity)' if k4_fires[y] else 'robust'}"
        )
    print(f"  K4 -> {'FIRES' if any(k4_fires.values()) else 'PASSES'}")

    # ---- auxiliary: fixed-depth traversal ----
    if not args.skip_aux:
        print("\n=== AUXILIARY (report-only, price-free): fixed-depth book traversal ===")
        fd = aux_df
        print(
            "  hour-of-day range of the marginal submitted-offer price at fixed"
            " depth q of the hour's own offered capacity ($/MWh):"
        )
        hdr = " ".join(f"{'q=' + str(int(q * 100)):>9}" for q in AUX_DEPTHS)
        print(f"{'year':>6} {hdr} | {'model':>7} {'DA':>7}")
        for y in sorted(fd["year"].unique()):
            g = fd[fd["year"] == y]
            cells = " ".join(
                f"{_hod_range(g, f'p{int(q * 100)}')[int(y)]:>9.2f}" for q in AUX_DEPTHS
            )
            print(
                f"{int(y):>6} {cells} | {MODEL_HOD_RANGE[int(y)]:>7.2f} "
                f"{DA_HOD_RANGE[int(y)]:>7.2f}"
            )
        print("  direction of the fixed-RELATIVE-depth profile (q=80):")
        for y in sorted(fd["year"].unique()):
            print(f"    {int(y)}: {_hod_shape(fd, 'p80', int(y))}")
        print(
            "  CONSTANT-QUANTITY read — hour-of-day range of the marginal offer"
            " price at fixed ABSOLUTE MW ($/MWh; blank = quantity above the"
            " hour's offered capacity somewhere in the year):"
        )
        hdr = " ".join(f"{str(q // 1000) + ' GW':>9}" for q in AUX_ABS_MW)
        print(f"{'year':>6} {hdr} | {'model':>7} {'DA':>7}")
        for y in sorted(fd["year"].unique()):
            g = fd[fd["year"] == y]
            cells = []
            for q in AUX_ABS_MW:
                col = f"a{q}"
                sub = g.dropna(subset=[col])
                cells.append(
                    f"{_hod_range(sub, col)[int(y)]:>9.2f}"
                    if len(sub) == len(g)
                    else f"{'--':>9}"
                )
            print(
                f"{int(y):>6} {' '.join(cells)} | {MODEL_HOD_RANGE[int(y)]:>7.2f} "
                f"{DA_HOD_RANGE[int(y)]:>7.2f}"
            )
        print("  direction of the constant-quantity profile (18 GW):")
        for y in sorted(fd["year"].unique()):
            print(f"    {int(y)}: {_hod_shape(fd, 'a18000', int(y))}")
        print(
            "  TRAVERSAL read — the real book crossed at the REAL hourly quantity"
            " (EIA-930 ISNE demand; 'less 3 GW' books a flat import allowance)."
            " This is the amplitude a model inherits from the real book with the"
            " real traversal, energy-only, no congestion/losses/reserve:"
        )
        for y in sorted(fd["year"].unique()):
            y = int(y)
            n_ok = int(fd[fd["year"] == y]["dem"].notna().sum())
            n_tot = int((fd["year"] == y).sum())
            print(
                f"    {y}: at demand      hod range {_hod_shape(fd, 'dem', y)}"
                f"   [{n_ok}/{n_tot} hours inside the book]"
            )
            print(
                f"          at demand-3GW  hod range {_hod_shape(fd, 'dem_imp', y)}"
                f"   | model {MODEL_HOD_RANGE[y]:.2f} · DA {DA_HOD_RANGE[y]:.2f}"
            )
        print("  hour-of-day range of the hour's TOTAL offered capacity (MW):")
        for y in sorted(fd["year"].unique()):
            g = fd[fd["year"] == y]
            prof = g.groupby("he")["offered_mw"].mean()
            print(
                f"    {int(y)}: {prof.min():,.0f} (h{int(prof.idxmin())}) -> "
                f"{prof.max():,.0f} (h{int(prof.idxmax())}), "
                f"range {prof.max() - prof.min():,.0f} MW"
            )

    print("\n=== PHASE-0 VERDICT (charter §4 kill rules) ===")
    print(f"  K1 movement floor : {'FIRES' if any(k1_fires.values()) else 'survives'}")
    print("  K2 conditioning    : admissible by construction (no price input)")
    print("  K3 demand limb     : see --check-demand-book")
    print(f"  K4 fuel-tail       : {'FIRES' if any(k4_fires.values()) else 'passes'}")
    print(f"  K5 event coverage  : {'FIRES' if k5_missing else 'passes'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
