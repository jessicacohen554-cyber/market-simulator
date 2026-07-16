"""Derive the MEASURED CAISO DAM offer surface from OASIS public bids.

The CAISO analogue of ``scripts/derive_pjm_offer_surface.py`` (C1
CC-over/CT-under lane, WP-A — the measured route named by
``results/calibration/FINDING-caiso91b-ct-committed-conduct-refuted-2026-07-16.md``
and ``docs/DIAGNOSIS-caiso-evening-merit-c1-c3c-2026-07.md`` §3-4): from the
90-day-lag masked OASIS Public Bid Data (``dam-public-bids`` clean datatype,
``scripts/fetch_caiso_public_bids.py`` + ``scripts/curate_dam_public_bids.py``),
measure the CC-like and CT-like gas fleets' DAM energy-bid curves and freeze
them into

* ``caiso_offer_curve_measured.json`` — measured STATIC band multipliers
  (econ_low / econ_high / peak) that REPLACE the fitted ``_CAISO_OFFER_CURVE``
  gas multipliers when ``ScenarioConfig.caiso_offer_surface_measured`` is set
  (a rule-24/25 SHRINK of the fitted surface: the DOF ledger's
  offer_curve_by_group residual entries retire where measured rungs land);
* ``caiso_offer_surface_condbinned.json`` — the exact PJM/NEISO condbinned
  peak-rung ladder schema, consumed P1-only by
  ``data.fleet.build_caiso_offer_surface_conditional_markup``
  (``ScenarioConfig.caiso_offer_surface_conditional``).

Method (measured, NOT fit to any residual — CLAUDE.md rules 1/13/23)
--------------------------------------------------------------------
1. Population: GENERATOR energy (EN) bid curves, resource capacity >= 20 MW
   (capacity = p98 of hourly max cumulative bid MW, per year). Resources
   whose curves reach below -1 MW (withdrawal-capable storage NGRs) are
   excluded.
2. CLASSIFICATION — the public bids are MASKED (no fuel/physics columns, so
   the PJM min-runtime gate is unavailable). Gas resources are identified by
   the physics of daily fuel-cost passthrough: per resource, the BODY bid
   price (price at 35% of capacity, per-day median across hours) is
   regressed on the model's OWN measured CA-composite citygate daily series
   placed on gas FLOW days (trade+1 forward-fill staircase — the caiso-90
   keeper semantics). The slope of that regression IS the resource's
   marginal heat rate at the body (MMBtu/MWh): a fuel-price time-series
   identification that no non-gas resource reproduces (hydro / storage /
   renewables fail the correlation gate; verified on 2023 data: gas-like
   resources fit with r 0.90-0.99).

   * gas gate: pooled-span regression slope in [4.0, 18.0] MMBtu/MWh,
     r >= 0.6, >= 120 resource-days with gas coverage;
   * class split at ``--hr-cut`` (default 8.4 MMBtu/MWh — the observed
     capacity-density antimode between the old-CC and aero-CT shoulders,
     inside the near-empty 8.25-8.50 slope bin): CC_REGULAR below
     (fleet cap-weighted Plant_Avg_HR 7.44, marginal body HR measured
     0.9-1.0x of that), CT_PEAKER at/above (fleet 10.86; efficient
     aeroderivatives reach down to ~9.0 — LMS100 9.35). The cut must sit in
     a capacity-density valley (gate G2 below).
   * Known contamination, disclosed not hidden: the three OTC/RMR steamers
     (ST_GAS: Alamitos / Huntington Beach / Ormond Beach, 2.9 GW, HR ~11.85)
     and priced CT_CHP curves land in the CT bucket when they pass the
     bidder gates; CC_CHP (HR 6.90) lands in the CC bucket. Both are
     near-SRMC bidders of the same fuel, statistics are cap-weighted
     MEDIANS, and the bucket-vs-fleet capacity reconciliation (G1) bounds
     the weight. The masked ids cannot be plant-mapped, so the derive is
     per-CLASS only (the charter's "plant?" resolves to NO).
3. Multiplier bases (the exact model round-trip):

   * STATIC band mult (committed / econ_low / econ_high windows):
       mult = (band_price - VOM_class) / (base_HR_class x (gas_flow_day
              + CO2_FACTOR x P_carbon_year))
     because a model tranche prices at mult x base_HR x gas + VOM +
     0.057 x (mult x base_HR) x P_carbon — the CCA allowance cost ($15-22/MWh,
     STATE_CARBON_PRICE_BY_ISO) is far too large to fold into the
     multiplier the way the PJM derive folds RGGI.
     Band windows use the model's own class tranche geometry
     (bin_assignments_CAISO.csv cap-weighted Pct_Committed / Pct_Peaking +
     the class econ_low_share), so measured mults land on the same capacity
     the model prices there. band_price = capacity-weighted mean step price
     across the window, per resource-hour; per-resource median per year;
     cap-weighted class median across resources.
   * LADDER mult (top-of-curve, per net-load bin): the P1 markup mechanism
     reprices the FUEL component only, at the peak rung's resolved-height
     carbon basis, so
       mult = (top_price - VOM_class - CO2_FACTOR x base_HR_class x
               peak_static x P_carbon_year) / (base_HR_class x gas_flow_day)
     with ``peak_static`` the measured static peak from step 3 (the
     resolved height the mechanism divides by at solve time).
4. Tightness driver + ladder: identical to PJM — system net load (EIA-930
   CAISO Demand - Wind - Sun) percentile-ranked within year, bin edges
   0.80/0.90/0.97; per-unit median top-of-curve mult per bin, cap-weighted
   into 5 equal-capacity quantile rungs, clamped below by the all-hours
   class p50.
5. The measured COMMITTED-band multiplier is reported in provenance but NOT
   armed: real CC/CT min-load blocks bid below SRMC as self-commitment
   conduct whose physical owner is unit commitment (two-shifting), not the
   P1 offer (the Lever-A inversion lesson, backcast_config.py:471; rule 19
   one-mechanism-per-phenomenon). Arming it without a commitment layer
   would re-flood overnight CC.

Estimation gates (pre-registered; ALL must pass or the derive REFUSES to
write the consumed JSONs — the caiso-89 estimation-stage CV/LOYO precedent):
  G1 capacity reconciliation: classified CC bucket capacity in [50%, 130%]
     of the fleet CC_REGULAR 13.7 GW; CT bucket in [50%, 160%] of the fleet
     CT_PEAKER 7.6 GW (the ST_GAS/CT_CHP contamination allowance, disclosed
     in provenance).
  G2 cut robustness (direct form): every CONSUMED stat re-derived with the
     cut moved +/-0.25 MMBtu/MWh stays within max(0.08, 10%) of the base
     value. (Replaces the first-draft near-cut capacity-mass proxy, which
     could not represent the narrow measured density valley at 8.25-8.50;
     revised on the measured slope density only, before any solve — no
     residual entered.)
  G3 estimation-stage LOYO: each CONSUMED stat (econ_low / econ_high / peak
     per class) re-derived leaving each year out must sit within
     max(0.08, 10%) of the pooled value for every held-out year.
  G4 physical sanity: econ_low <= econ_high <= peak with a 0.05 flatness
     tolerance (measured CT curves are near-flat, so adjacent band medians
     may tie to within noise; a REAL inversion beyond 0.05 fails); every
     armed mult in [0.5, 6.0].

Frozen against residuals (rule 23): re-derives only when the source corpus
updates; if the A/B probe degrades the backcast the surface does NOT move
and the probe registers as REJECTED (rule 15). Measured OFFER prices are
the input — clearing prices stay validation-only (rule 13).

Usage:
    python scripts/derive_caiso_offer_surface.py [--years 2023 2024 2025]
        [--edges 0.80 0.90 0.97] [--rungs 5] [--hr-cut 8.5]
        [--allow-gate-failures]   # inspect-only: never writes consumed JSONs
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from lib import clean_io  # noqa: E402

OUT_STATIC = (
    REPO / "data" / "raw" / "_validation-source" / "caiso_offer_curve_measured.json"
)
OUT_COND = (
    REPO / "data" / "raw" / "_validation-source" / "caiso_offer_surface_condbinned.json"
)
OUT_CSV = (
    REPO / "data" / "raw" / "_validation-source" / "caiso_offer_surface_summary.csv"
)
BIN_ASSIGNMENTS = (
    REPO / "data" / "raw" / "_processed-legacy" / "bin_assignments_CAISO.csv"
)
CITYGATE_DAILY = REPO / "data" / "raw" / "gas-prices" / "caiso_citygate_daily.csv"

#: Minimum resource capacity (MW): micro/QF resources are not the priced
#: merit surface the model's class multipliers represent.
MIN_CAP_MW = 20.0
#: Gas-identification gates (see module docstring §2).
GAS_SLOPE_RANGE = (4.0, 18.0)
GAS_MIN_R = 0.6
GAS_MIN_DAYS = 120
#: Body point for the classification regression: 35% of capacity sits inside
#: every class's committed+econ_low window (below any duct/peak band).
BODY_FRAC = 0.35
#: Class VOM ($/MWh) — constants.VOM (NREL ATB 2024).
VOM_BY_CLASS = {"CC_REGULAR": 2.0, "CT_PEAKER": 3.5}
#: Gas CO2 factor (tCO2/MMBtu) — constants.FUEL_CO2_FACTOR_PER_MMBTU.
CO2_FACTOR = 0.057
#: econ_low share of the econ window — the model's class geometry
#: (_CAISO_OFFER_CURVE econ_low_share; kept, not re-derived).
ECON_LOW_SHARE = {"CC_REGULAR": 0.50, "CT_PEAKER": 0.526}
#: Ladder quantiles (5 equal-cap rungs) — the ERCOT/PJM/NEISO convention.
LADDER_QS = (0.1, 0.3, 0.5, 0.7, 0.9)
#: LOYO tolerance on consumed stats: max(0.08 mult units, 10%).
LOYO_ABS = 0.08
LOYO_REL = 0.10


def _carbon_price(year: int) -> float:
    """CARB cap-and-trade allowance price ($/t) — constants.STATE_CARBON_PRICE_BY_ISO."""
    from market_sim.config.constants import STATE_CARBON_PRICE_BY_ISO

    return float(STATE_CARBON_PRICE_BY_ISO["CAISO"][year])


def _gas_staircase() -> pd.Series:
    """CA-composite citygate daily spot on gas FLOW days (trade+1 staircase).

    The caiso-90 keeper placement semantics (a print keyed to trade day T
    fuels burns on T+1; weekend/holiday packages carry forward).
    """
    gas = pd.read_csv(CITYGATE_DAILY, parse_dates=["date"])
    gas = gas.sort_values("date")
    gas["flow"] = gas["date"] + pd.Timedelta(days=1)
    cal = pd.date_range(gas["flow"].min(), gas["flow"].max() + pd.Timedelta(days=7))
    s = gas.set_index("flow")["ca_composite_usd_mmbtu"].reindex(cal).ffill()
    s.index.name = "day"
    return s


def _fleet_geometry() -> dict[str, dict[str, float]]:
    """Class base HR + tranche geometry from the model's own fleet basis.

    Cap-weighted over ``bin_assignments_CAISO.csv`` — the same per-plant
    Plant_Avg_HR the offer multipliers scale at solve time (the round-trip
    convention; the CC 7.44 / CT 10.86 values cited in
    ``backcast_config._CAISO_OFFER_CURVE``'s grounding comment).
    """
    b = pd.read_csv(BIN_ASSIGNMENTS)
    out: dict[str, dict[str, float]] = {}
    for cls in ("CC_REGULAR", "CT_PEAKER"):
        sub = b[b.Plant_Group == cls]
        w = sub.Nameplate_MW.to_numpy(float)
        out[cls] = {
            "base_hr": float(np.average(sub.Plant_Avg_HR_MMBtu_MWh, weights=w)),
            "fleet_mw": float(w.sum()),
            "pct_committed": float(np.average(sub.Pct_Committed, weights=w)),
            "pct_peaking": float(np.average(sub.Pct_Peaking, weights=w)),
        }
    return out


def _netload_pct(years: list[int]) -> pd.DataFrame:
    """(local day, hour-ending) -> within-year net-load percentile (CAISO).

    The identical forward-native construction the PJM derive uses
    (EIA-930 Demand - Wind - Sun, percentile-ranked within year).
    """
    from market_sim.data.eia_loader import _eia_hourly_frame_filled

    frames = []
    for year in years:
        df = _eia_hourly_frame_filled("CISO", year)  # EIA-930 BA code
        if df is None:
            raise SystemExit(f"EIA-930 CAISO {year}: no clean 8760 frame")
        net = (
            pd.to_numeric(df["Demand"], errors="coerce")
            .interpolate(limit_direction="both")
            .to_numpy(float)
            - pd.to_numeric(df["NG: WND"], errors="coerce")
            .interpolate(limit_direction="both")
            .to_numpy(float)
            - pd.to_numeric(df["NG: SUN"], errors="coerce")
            .interpolate(limit_direction="both")
            .to_numpy(float)
        )
        q = pd.Series(net).rank(pct=True).to_numpy()
        local = pd.DatetimeIndex(df["Local time"])
        frames.append(
            pd.DataFrame({"day": local.normalize(), "he": local.hour + 1, "q": q})
        )
    out = pd.concat(frames, ignore_index=True)
    return out.groupby(["day", "he"], as_index=False).agg(q=("q", "mean"))


def _load_bids(years: list[int]) -> pd.DataFrame:
    """GENERATOR EN curve segments from the clean dam-public-bids tree."""
    frames = []
    for year in years:
        df = clean_io.read_clean(
            "dam-public-bids", iso="CAISO", year=year, market="DAM", validate=False
        )
        df = df[
            (df.resource_type == "GENERATOR")
            & (df["product"] == "EN")
            & (df.row_kind == "segment")
        ]
        frames.append(
            df[
                [
                    "trade_date",
                    "interval_start_utc",
                    "resource_seq",
                    "segment_mw",
                    "segment_price_usd_per_mwh",
                ]
            ].assign(year=year)
        )
    out = pd.concat(frames, ignore_index=True)
    out = out.rename(columns={"segment_price_usd_per_mwh": "price"})
    return out.sort_values(["resource_seq", "interval_start_utc", "segment_mw"])


def _price_at_frac(seg: pd.DataFrame, frac: float) -> pd.Series:
    """Per (resource, hour): price of the last step at/below frac x capacity.

    Falls back to the first step when the whole curve starts above the
    target (the step covering the target MW).
    """
    below = seg[seg.segment_mw <= frac * seg.cap]
    p = below.groupby(["resource_seq", "interval_start_utc"]).price.last()
    first = seg.groupby(["resource_seq", "interval_start_utc"]).price.first()
    return p.reindex(first.index).fillna(first)


def _band_price(seg: pd.DataFrame, lo: float, hi: float) -> pd.Series:
    """Per (resource, hour): capacity-weighted mean step price over [lo, hi) x cap.

    The bid curve is a step function on cumulative MW: step i prices the MW
    span [mw_i, mw_{i+1}). The band price integrates that step function
    across the window, so it is exactly the average $/MWh of the capacity
    the model prices in the same window.
    """
    s = seg.copy()
    s["mw_lo"] = s.segment_mw.clip(lower=0.0)
    g = s.groupby(["resource_seq", "interval_start_utc"], sort=False)
    s["mw_hi"] = g.mw_lo.shift(-1)
    s["mw_hi"] = s.mw_hi.fillna(s.cap)
    a = np.maximum(s.mw_lo.to_numpy(float), lo * s.cap.to_numpy(float))
    b = np.minimum(s.mw_hi.to_numpy(float), hi * s.cap.to_numpy(float))
    w = np.clip(b - a, 0.0, None)
    s["w"] = w
    s["pw"] = w * s.price.to_numpy(float)
    agg = s.groupby(["resource_seq", "interval_start_utc"], sort=False)[
        ["w", "pw"]
    ].sum()
    return (agg.pw / agg.w.replace(0.0, np.nan)).dropna()


def _wquantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w) - 0.5 * w
    return float(np.interp(q * w.sum(), cw, v))


def _classify(
    seg: pd.DataFrame, gas: pd.Series, hr_cut: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-resource gas-coupling regression -> (resource table, daily body table)."""
    body = _price_at_frac(seg, BODY_FRAC).rename("p_body").reset_index()
    body["day"] = body.interval_start_utc.dt.tz_convert("US/Pacific").dt.normalize()
    body["day"] = body.day.dt.tz_localize(None)
    daily = (
        body.groupby(["resource_seq", "day"], as_index=False)
        .p_body.median()
        .assign(gas=lambda d: d.day.map(gas))
        .dropna(subset=["gas"])
    )

    cap = seg.groupby("resource_seq").cap.first()
    min_mw = seg.groupby("resource_seq").segment_mw.min()

    rows = []
    for rid, g in daily.groupby("resource_seq"):
        n = len(g)
        if n < GAS_MIN_DAYS or g.gas.std() < 0.5:
            continue
        x, y = g.gas.to_numpy(float), g.p_body.to_numpy(float)
        slope, _ = np.polyfit(x, y, 1)
        r = float(np.corrcoef(x, y)[0, 1])
        rows.append({"resource_seq": rid, "slope": float(slope), "r": r, "n_days": n})
    res = pd.DataFrame(rows).set_index("resource_seq")
    res["cap"] = cap
    res["min_mw"] = min_mw
    res["is_gas"] = (
        res.slope.between(*GAS_SLOPE_RANGE)
        & (res.r >= GAS_MIN_R)
        & (res.min_mw >= -1.0)
    )
    res["cls"] = np.where(res.slope < hr_cut, "CC_REGULAR", "CT_PEAKER")
    res.loc[~res.is_gas, "cls"] = ""
    return res, daily


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--edges", nargs="*", type=float, default=[0.80, 0.90, 0.97])
    ap.add_argument("--rungs", type=int, default=5)
    ap.add_argument(
        "--hr-cut",
        type=float,
        default=8.5,
        help="CC/CT classification cut on the regression marginal HR "
        "(MMBtu/MWh); must sit in a capacity-density valley (gate G2)",
    )
    ap.add_argument(
        "--allow-gate-failures",
        action="store_true",
        help="inspect-only mode: report gates but do NOT write consumed JSONs",
    )
    args = ap.parse_args(argv)
    years = list(args.years)

    geom = _fleet_geometry()
    gas = _gas_staircase()
    print("loading clean dam-public-bids ...", flush=True)
    bids = _load_bids(years)
    ncurve = len(bids)

    # Per-resource-year capacity; the analysis frame carries cap on each row.
    cap_ry = bids.groupby(["resource_seq", "year"]).segment_mw.quantile(0.98)
    bids = bids.join(cap_ry.rename("cap"), on=["resource_seq", "year"])
    bids = bids[bids.cap >= MIN_CAP_MW]
    print(
        f"  {ncurve:,} curve rows -> {len(bids):,} rows at cap >= {MIN_CAP_MW} MW, "
        f"{bids.resource_seq.nunique()} resources",
        flush=True,
    )

    # ------------------------------------------------------------------ #
    # Classification (pooled span)                                        #
    # ------------------------------------------------------------------ #
    res, _daily = _classify(bids, gas, args.hr_cut)
    gaslike = res[res.is_gas]
    buckets = {cls: gaslike[gaslike.cls == cls] for cls in ("CC_REGULAR", "CT_PEAKER")}
    gates: dict[str, dict] = {}
    g1 = {}
    for cls, sub in buckets.items():
        ratio = sub.cap.sum() / geom[cls]["fleet_mw"]
        lo, hi = (0.5, 1.3) if cls == "CC_REGULAR" else (0.5, 1.6)
        g1[cls] = {
            "bucket_mw": round(float(sub.cap.sum()), 0),
            "fleet_mw": round(geom[cls]["fleet_mw"], 0),
            "ratio": round(float(ratio), 3),
            "bounds": [lo, hi],
            "pass": bool(lo <= ratio <= hi),
        }
    gates["G1_capacity_reconciliation"] = g1
    print(f"G1 {json.dumps(g1)}", flush=True)

    # ------------------------------------------------------------------ #
    # Static band multipliers                                             #
    # ------------------------------------------------------------------ #
    bids["day"] = (
        bids.interval_start_utc.dt.tz_convert("US/Pacific")
        .dt.normalize()
        .dt.tz_localize(None)
    )
    bids["gas"] = bids.day.map(gas)
    carbon = {y: _carbon_price(y) for y in years}

    def band_windows(cls: str) -> dict[str, tuple[float, float]]:
        c = geom[cls]["pct_committed"] / 100.0
        p = geom[cls]["pct_peaking"] / 100.0
        els = ECON_LOW_SHARE[cls]
        e_lo = c
        e_hi = 1.0 - p
        e_mid = e_lo + (e_hi - e_lo) * els
        return {
            "committed": (0.0, c),
            "econ_low": (e_lo, e_mid),
            "econ_high": (e_mid, e_hi),
            "peak": (e_hi, 1.0),
        }

    def static_bands(
        bucket_map: dict[str, pd.DataFrame], with_detail: bool
    ) -> tuple[dict, dict, dict]:
        """Cap-weighted median band mults per class (+ per-year/LOYO detail)."""
        static_: dict[str, dict] = {}
        per_year_: dict[str, dict] = {}
        loyo_: dict[str, dict] = {}
        for cls, sub in bucket_map.items():
            rows = bids[bids.resource_seq.isin(sub.index)]
            base_hr = geom[cls]["base_hr"]
            vom = VOM_BY_CLASS[cls]
            windows = band_windows(cls)
            band_res: dict[str, pd.DataFrame] = {}
            for band, (lo, hi) in windows.items():
                bp = _band_price(rows, lo, hi).rename("p").reset_index()
                bp = bp.merge(
                    rows[
                        ["resource_seq", "interval_start_utc", "day", "gas", "year"]
                    ].drop_duplicates(["resource_seq", "interval_start_utc"]),
                    on=["resource_seq", "interval_start_utc"],
                    how="left",
                ).dropna(subset=["gas"])
                bp["denom"] = base_hr * (bp.gas + CO2_FACTOR * bp.year.map(carbon))
                bp["mult"] = (bp.p - vom) / bp.denom
                # resource-year median -> the estimation unit
                ry = (
                    bp.groupby(["resource_seq", "year"])
                    .mult.median()
                    .rename("m")
                    .reset_index()
                )
                ry["cap"] = ry.resource_seq.map(sub.cap)
                band_res[band] = ry

            def _pool(band: str, drop_year: int | None = None) -> float:
                ry = band_res[band]
                if drop_year is not None:
                    ry = ry[ry.year != drop_year]
                return _wquantile(ry.m.to_numpy(float), ry.cap.to_numpy(float), 0.5)

            static_[cls] = {b: round(_pool(b), 3) for b in windows}
            if with_detail:
                per_year_[cls] = {
                    b: {
                        str(y): round(
                            _wquantile(
                                band_res[b][band_res[b].year == y].m.to_numpy(float),
                                band_res[b][band_res[b].year == y].cap.to_numpy(float),
                                0.5,
                            ),
                            3,
                        )
                        for y in years
                    }
                    for b in windows
                }
                loyo_[cls] = {
                    b: {str(y): round(_pool(b, drop_year=y), 3) for y in years}
                    for b in ("econ_low", "econ_high", "peak")
                }
        return static_, per_year_, loyo_

    static, per_year_stats, loyo_stats = static_bands(buckets, with_detail=True)
    for cls in buckets:
        print(f"{cls}: static bands {static[cls]}", flush=True)

    # G2 — cut robustness, the direct form: the CONSUMED stats must be
    # stable when the classification cut moves +/-0.25 MMBtu/MWh (replaces
    # the earlier near-cut capacity-mass proxy, which could not represent a
    # narrow density valley between the old-CC and aero-CT shoulders; the
    # revision is estimation-stage, driven by the measured slope density
    # only — no residual entered).
    g2 = {"cut": args.hr_cut, "deltas": {}}
    g2_pass = True
    for dcut in (-0.25, +0.25):
        alt = gaslike.copy()
        alt["cls"] = np.where(alt.slope < args.hr_cut + dcut, "CC_REGULAR", "CT_PEAKER")
        alt_buckets = {cls: alt[alt.cls == cls] for cls in ("CC_REGULAR", "CT_PEAKER")}
        alt_static, _, _ = static_bands(alt_buckets, with_detail=False)
        rowset = {}
        for cls in ("CC_REGULAR", "CT_PEAKER"):
            for b in ("econ_low", "econ_high", "peak"):
                dev = abs(alt_static[cls][b] - static[cls][b])
                tol = max(LOYO_ABS, LOYO_REL * abs(static[cls][b]))
                rowset[f"{cls}.{b}"] = {
                    "alt": alt_static[cls][b],
                    "dev": round(dev, 3),
                    "tol": round(tol, 3),
                    "pass": bool(dev <= tol),
                }
                g2_pass = g2_pass and dev <= tol
        g2["deltas"][f"{dcut:+.2f}"] = rowset
    g2["pass"] = bool(g2_pass)
    gates["G2_cut_robustness"] = g2
    print(f"G2 cut+/-0.25 robustness: {'PASS' if g2_pass else 'FAIL'}", flush=True)

    g3 = {}
    for cls in buckets:
        rows = {}
        for b in ("econ_low", "econ_high", "peak"):
            pooled = static[cls][b]
            worst = max(abs(loyo_stats[cls][b][str(y)] - pooled) for y in years)
            tol = max(LOYO_ABS, LOYO_REL * abs(pooled))
            rows[b] = {
                "pooled": pooled,
                "loyo": loyo_stats[cls][b],
                "worst_dev": round(worst, 3),
                "tol": round(tol, 3),
                "pass": bool(worst <= tol),
            }
        g3[cls] = rows
    gates["G3_estimation_loyo"] = g3

    g4 = {}
    for cls in buckets:
        s = static[cls]
        ordered = s["econ_low"] <= s["econ_high"] <= s["peak"]
        in_range = all(0.5 <= s[b] <= 6.0 for b in ("econ_low", "econ_high", "peak"))
        g4[cls] = {
            "ordered": bool(ordered),
            "in_range": bool(in_range),
            "pass": bool(ordered and in_range),
        }
    gates["G4_physical_sanity"] = g4

    # ------------------------------------------------------------------ #
    # Conditional peak-rung ladder (PJM condbinned schema)                #
    # ------------------------------------------------------------------ #
    nl = _netload_pct(years)
    edges = tuple(args.edges)
    n_bins = len(edges) + 1
    cap_share = round(1.0 / args.rungs, 3)

    tops = (
        bids.groupby(["resource_seq", "interval_start_utc"], sort=False)
        .agg(
            top=("price", "max"),
            day=("day", "first"),
            gas=("gas", "first"),
            year=("year", "first"),
        )
        .reset_index()
        .dropna(subset=["gas"])
    )
    local = tops.interval_start_utc.dt.tz_convert("US/Pacific")
    tops["he"] = local.dt.hour + 1
    tops = tops.merge(nl, on=["day", "he"], how="left").dropna(subset=["q"])
    tops["bin"] = np.searchsorted(
        np.asarray(edges), tops.q.to_numpy(), side="right"
    ).astype("int8")

    cond: dict[str, dict] = {}
    summary_rows = []
    for cls, sub in buckets.items():
        base_hr = geom[cls]["base_hr"]
        vom = VOM_BY_CLASS[cls]
        pk_static = static[cls]["peak"]
        t = tops[tops.resource_seq.isin(sub.index)].copy()
        t["mult"] = (
            t.top - vom - CO2_FACTOR * base_hr * pk_static * t.year.map(carbon)
        ) / (base_hr * t.gas)
        t["cap"] = t.resource_seq.map(sub.cap)

        pa = t.groupby("resource_seq").agg(m=("mult", "median"), cap=("cap", "first"))
        body_p50 = _wquantile(pa.m.to_numpy(float), pa.cap.to_numpy(float), 0.5)

        binned_ladder = []
        for b in range(n_bins):
            pab = (
                t[t.bin == b]
                .groupby("resource_seq")
                .agg(m=("mult", "median"), cap=("cap", "first"))
            )
            if len(pab) < 5:
                ladder = [[cap_share, round(body_p50, 3)] for _ in LADDER_QS]
            else:
                v, w = pab.m.to_numpy(float), pab.cap.to_numpy(float)
                ladder = [
                    [
                        cap_share,
                        max(round(body_p50, 3), round(_wquantile(v, w, q), 3)),
                    ]
                    for q in LADDER_QS[: args.rungs]
                ]
            binned_ladder.append(ladder)
            summary_rows.append(
                {
                    "class": cls,
                    "bin": b,
                    "n_units": len(pab),
                    "n_rows": int((t.bin == b).sum()),
                    **{f"rung{i + 1}_mult": ladder[i][1] for i in range(args.rungs)},
                }
            )
        cond[cls] = {
            "base_hr": round(base_hr, 3),
            "peak_p50": round(body_p50, 3),
            "binned_ladder": binned_ladder,
        }
        print(f"{cls}: ladder body_p50 {body_p50:.3f}", flush=True)

    all_pass = all(
        (
            all(v["pass"] for v in g1.values()),
            g2["pass"],
            all(v["pass"] for rows in g3.values() for v in rows.values()),
            all(v["pass"] for v in g4.values()),
        )
    )
    print(f"\nGATES {'ALL PASS' if all_pass else 'FAILED'}", flush=True)

    provenance = {
        "source": (
            "CAISO OASIS Public Bid Data (PUB_DAM_GRP GroupZip, 90-day-lag "
            "masked DAM bids), dam-public-bids clean datatype, trade years "
            f"{years}"
        ),
        "derived_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "method": "see scripts/derive_caiso_offer_surface.py module docstring",
        "gas_basis": (
            "CA-composite citygate daily on gas FLOW days (trade+1 staircase, "
            "caiso-90 semantics), data/raw/gas-prices/caiso_citygate_daily.csv"
        ),
        "carbon_basis": {
            "usd_per_t": {str(y): _carbon_price(y) for y in years},
            "co2_factor_t_per_mmbtu": CO2_FACTOR,
            "note": "CARB C&T allowance (STATE_CARBON_PRICE_BY_ISO); static "
            "mults net of carbon at band HR, ladder mults net of carbon at "
            "the measured static peak HR (the mechanism's fuel-only "
            "repricing basis)",
        },
        "vom_usd_per_mwh": VOM_BY_CLASS,
        "classifier": {
            "body_frac": BODY_FRAC,
            "gas_slope_range": list(GAS_SLOPE_RANGE),
            "min_r": GAS_MIN_R,
            "min_days": GAS_MIN_DAYS,
            "min_cap_mw": MIN_CAP_MW,
            "hr_cut": args.hr_cut,
            "contamination_note": (
                "CT bucket may include the 2.9 GW OTC/RMR ST_GAS steamers "
                "and priced CT_CHP; CC bucket may include CC_CHP. Same-fuel "
                "near-SRMC bidders; bounded by G1, robust via cap-weighted "
                "medians; masked ids preclude per-plant mapping."
            ),
        },
        "band_windows_geometry": {
            cls: {
                "pct_committed": round(geom[cls]["pct_committed"], 2),
                "pct_peaking": round(geom[cls]["pct_peaking"], 2),
                "econ_low_share": ECON_LOW_SHARE[cls],
            }
            for cls in buckets
        },
        "netload_pct_edges": list(edges),
        "peak_ladder_qs": list(LADDER_QS[: args.rungs]),
        "per_year_band_mults": per_year_stats,
        "gates": gates,
        "committed_band_unarmed_note": (
            "measured committed-band mults reported in per_year_band_mults "
            "but NOT consumed: min-load self-commitment conduct is owned by "
            "unit commitment, not the P1 offer (Lever-A inversion lesson; "
            "rule 19)"
        ),
    }

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary_rows).to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV}")

    if not all_pass and not args.allow_gate_failures:
        raise SystemExit(
            "estimation gates FAILED — consumed JSONs not written "
            "(re-run with --allow-gate-failures to inspect)"
        )
    if args.allow_gate_failures and not all_pass:
        print("gate failures — inspect-only, consumed JSONs NOT written")
        return 1

    static_doc = {
        "_provenance": provenance,
        **{
            cls: {
                "base_hr": round(geom[cls]["base_hr"], 3),
                "bands": {b: static[cls][b] for b in ("econ_low", "econ_high", "peak")},
                "unarmed": {"committed": static[cls]["committed"]},
            }
            for cls in buckets
        },
    }
    OUT_STATIC.write_text(json.dumps(static_doc, indent=1) + "\n")
    print(f"wrote {OUT_STATIC}")

    cond_doc = {"_provenance": provenance, **cond}
    OUT_COND.write_text(json.dumps(cond_doc, indent=1) + "\n")
    print(f"wrote {OUT_COND}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
