"""Derive the MEASURED CAISO DAM offer surface from OASIS public bids.

The CAISO analogue of ``scripts/data/derive_pjm_offer_surface.py`` (C1
CC-over/CT-under lane, WP-A — the measured route named by
``results/calibration/FINDING-caiso91b-ct-committed-conduct-refuted-2026-07-16.md``
and ``docs/DIAGNOSIS-caiso-evening-merit-c1-c3c-2026-07.md`` §3-4): from the
90-day-lag masked OASIS Public Bid Data (``dam-public-bids`` clean datatype,
``scripts/data/fetch_caiso_public_bids.py`` + ``scripts/data/curate_dam_public_bids.py``),
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

   The slope estimator is THEIL-SEN, not least squares (caiso-153,
   ``results/calibration/FINDING-caiso153-offer-classifier-reid-2026-08-02.md``).
   The regressor's variance is dominated by an extreme tail — the citygate
   reaches $24.29/MMBtu in January 2023 against a 2023-25 median near $3-4 —
   so an OLS slope is levered on a few days of one month of one year and
   attenuates toward zero for any resource that did not track that spike
   proportionally (a different CA hub, a monthly index, a cost-verified DEB
   on a lagged index) while its correlation survives. Measured over the
   frozen 3x3 body-probe x estimator grid on the full 1,095-day corpus: all
   three OLS cells are physically inadmissible (implied non-fuel adder
   $32.7-37.5/MWh against a $2.0-3.5 VOM, slope p50 ~6.0); all six
   Theil-Sen / TRIM cells are admissible ($9.6-12.7, slope p50 9.2-10.4).
   Under OLS the CT bucket collapses to G1 0.235 and 32 resources /
   10,880 MW sit at r >= 0.6 with a slope below 4 MMBtu/MWh — physically
   impossible for a thermal unit; under Theil-Sen that population falls to
   13 / 2,692 MW and G1 reconciles at CC 0.871 / CT 1.306. The BODY PROBE
   was tested on the same grid and REFUTED as the cause — it moves the
   statistics far less than the estimator does — so ``BODY_FRAC`` is
   unchanged at 0.35.

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

Estimation gates (pre-registered; ALL must pass **on the CONSUMED classes**
or the derive REFUSES to write the consumed JSONs — the caiso-89
estimation-stage CV/LOYO precedent). CONSUMED == MEASURED except under
``--st-split-report-only``, where a measured class is published with its gate
rows under ``_provenance.reported_not_consumed`` and kept OUT of the artifact;
the gate itself is never relaxed and the refused class keeps its FAIL:
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

Class partition (caiso-254 / caiso-255). The gas population is split on the
regression marginal HR at ``--hr-cut`` (CC below) and, above it, at a SECOND
cut ``st_cut`` located as the CT-side capacity-density antimode inside
``ST_CUT_WINDOW`` — the aero-CT mode below, the OTC/RMR steam mode above.
Three modes:
  default                  three-way; all three buckets gated and consumed.
  --no-st-split            two-way; reproduces the frozen 2026-08-02
                           construction, steamers pooled into CT (the
                           disclosed contamination). NOT a measurement that
                           the population is unimodal.
  --st-split-report-only   three-way CLASSIFICATION, two-way CONSUMPTION:
                           the CT bucket is de-contaminated (that is what the
                           classification does) but only CC_REGULAR and
                           CT_PEAKER are written and gated; ST_GAS is measured
                           and published as refused. caiso-255, owner grant of
                           FINDING-caiso254 §4 option 1 — the separated ST_GAS
                           bucket fails G4, and on CAISO its bands are LP-inert
                           regardless (the ST_GAS_PEAKER_PLANTS bypass in
                           data/offer_curves.py).

Usage:
    python scripts/data/derive_caiso_offer_surface.py [--years 2023 2024 2025]
        [--edges 0.80 0.90 0.97] [--rungs 5] [--hr-cut 8.5]
        [--from-reduced-store]    # the clean tree needs ~14.3 GB/year
        [--no-st-split | --st-split-report-only]
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
from scipy.stats import theilslopes

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import (  # noqa: E402
    CAISO_PUBLIC_BIDS_DIR,
    CALIBRATION_DIR,
    GAS_PRICES_DIR,
    PROCESSED_DIR,
)

from scripts.lib import clean_io  # noqa: E402

OUT_STATIC = CALIBRATION_DIR / "caiso_offer_curve_measured.json"
OUT_COND = CALIBRATION_DIR / "caiso_offer_surface_condbinned.json"
OUT_CSV = CALIBRATION_DIR / "caiso_offer_surface_summary.csv"
BIN_ASSIGNMENTS = PROCESSED_DIR / "bin_assignments_CAISO.csv"
CITYGATE_DAILY = GAS_PRICES_DIR / "caiso_citygate_daily.csv"

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
#: Class VOM ($/MWh) — constants.VOM (NREL ATB 2024). ST_GAS reads the SAME
#: table's ``gas_st`` entry the CC/CT values come from (``gas_cc`` / ``gas_ct``),
#: so the third bucket introduces no new constant (rule 21 [R-DOF]).
VOM_BY_CLASS = {"CC_REGULAR": 2.0, "CT_PEAKER": 3.5, "ST_GAS": 4.0}
#: Gas CO2 factor (tCO2/MMBtu) — constants.FUEL_CO2_FACTOR_PER_MMBTU.
CO2_FACTOR = 0.057
#: econ_low share of the econ window — the model's class geometry
#: (_CAISO_OFFER_CURVE econ_low_share; kept, not re-derived).
ECON_LOW_SHARE = {"CC_REGULAR": 0.50, "CT_PEAKER": 0.526, "ST_GAS": 0.50}
#: The three measured buckets, in rising marginal-heat-rate order.
CLASSES = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")
#: G1 bucket-vs-fleet capacity reconciliation bounds, per class. CC is tight;
#: the two CT-side buckets keep the WIDER band the pooled CT bucket already
#: carried, because the antimode separates two same-fuel near-SRMC populations
#: that published fleet boundaries do not cut in exactly the same place. NOT
#: retuned by this repair — CT_PEAKER's band is unchanged and ST_GAS inherits it.
G1_BOUNDS = {
    "CC_REGULAR": (0.5, 1.3),
    "CT_PEAKER": (0.5, 1.6),
    "ST_GAS": (0.5, 1.6),
}
#: Search window for the SECOND cut, between the CT_PEAKER fleet base HR
#: (10.862) and above the OTC/RMR steamers' fleet HR (11.847) — published fleet
#: heat rates, fixed before the density was built (caiso-253b PRECOMMIT §2.1,
#: G-BIMODAL) and never moved to admit a mode. The cut itself is LOCATED as the
#: capacity-density antimode inside it, exactly the way ``hr_cut`` = 8.5 was
#: located in its own valley — it is not swept and not chosen against any
#: criterion, so it adds no free parameter.
ST_CUT_WINDOW = (10.9, 12.5)
#: Capacity-weighted KDE bandwidth (MMBtu/MWh) for locating that antimode. A
#: density smoother, not a gate threshold.
ST_CUT_KDE_BW = 0.35
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
    for cls in CLASSES:
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


#: Clean columns this derive actually reads. ``trade_date`` is deliberately
#: absent: the derive keys everything off the LOCAL day recomputed from
#: ``interval_start_utc``, so carrying the trade date costs ~8 bytes/row for a
#: column nothing downstream touches. Reading only these columns is what keeps
#: the RLE-expanded corpus (caiso-152: ~72 M GENERATOR EN curve-hours over the
#: full 2023-25 span, ~2.4x the pre-expansion row count) inside a 16 GB box.
_BID_COLS = [
    "resource_type",
    "product",
    "row_kind",
    "interval_start_utc",
    "resource_seq",
    "segment_mw",
    "segment_price_usd_per_mwh",
]


#: Slim per-day reduced store written by
#: ``scripts/probes/_caiso253b_ct_bucket_bimodality.py --pass1``: the SAME four
#: columns and the SAME three row filters this module's clean-tree loader
#: applies, streamed straight from the OASIS zips.
REDUCED_STORE = CAISO_PUBLIC_BIDS_DIR / "_caiso253b_reduced"


def _load_bids_reduced(years: list[int]) -> pd.DataFrame:
    """GENERATOR EN curve segments from the slim reduced store.

    An INTAKE path, not a method change — it returns the identical frame
    :func:`_load_bids` builds, and the two are interchangeable by construction
    (same columns, same filters, same rename, same sort key).

    It exists because ``curate_dam_public_bids.py`` needs ~14.3 GB for ONE
    CAISO year against a 15 GB box (the corpus README's measured limit), so the
    clean tree cannot be built here at all, while the whole reduced corpus is
    ~57 M rows (~1.2 GB at these dtypes) and loads whole.

    EQUIVALENCE IS VERIFIED, NOT ASSUMED: running this module with
    ``--no-st-split`` over this store reproduces the frozen 2026-08-02
    artifact's consumed bands, and the same store reproduced the frozen bucket
    populations EXACTLY (46 / 11.935 GW and 100 / 9.950 GW) in
    ``results/calibration/_caiso253b_ct_bucket_bimodality.json``.
    """
    # CORPUS-COVERAGE GUARD (caiso-255). The G-BIMODAL probe refuses an
    # under-covered corpus (its `gate()`, added by caiso-254 after a mid-fetch
    # run scored 296 days of 2023 alone and returned the OPPOSITE verdict --
    # FINDING-caiso254 §5.2). The DERIVE had no such guard, which is the more
    # dangerous omission of the two: the probe only reports a number, while the
    # derive WRITES the artifact the LP then consumes. A partial store is a
    # different bid population, so its cap-weighted medians are different
    # measurements -- not noisier versions of the same one. Same tolerance and
    # same reasoning as the probe: exactly one trade date (2023-06-01) is a
    # genuine OASIS archive hole, so the span admits a handful of absences and
    # nothing more.
    MAX_MISSING_DAYS = 6
    have = {f.stem for f in REDUCED_STORE.glob("*.parquet") if int(f.stem[:4]) in years}
    want = {
        d.strftime("%Y%m%d")
        for d in pd.date_range(f"{min(years)}-01-01", f"{max(years)}-12-31", freq="D")
    }
    missing = sorted(want - have)
    per_year = {y: sum(1 for t in have if int(t[:4]) == y) for y in years}
    if not have:
        raise SystemExit(
            f"no reduced days for {years} under {REDUCED_STORE} — run "
            "scripts/probes/_caiso253b_ct_bucket_bimodality.py --pass1 first"
        )
    if len(missing) > MAX_MISSING_DAYS or any(per_year[y] == 0 for y in years):
        raise SystemExit(
            f"REFUSED: reduced store is under-covered — {len(have)} day(s), "
            f"per-year {per_year}, {len(missing)} missing of {len(want)} "
            f"(tolerance {MAX_MISSING_DAYS}). First missing: {missing[:5]}. "
            "The measured bands are cap-weighted medians over the POOLED span; "
            "a partial corpus is a DIFFERENT population, not a noisier sample "
            "of this one. Finish the fetch and re-run --pass1."
        )
    print(
        f"  reduced-store coverage {len(have)}/{len(want)} days, "
        f"per-year {per_year}, missing {missing or 'none'}",
        flush=True,
    )

    frames = []
    for f in sorted(REDUCED_STORE.glob("*.parquet")):
        year = int(f.stem[:4])
        if year not in years:
            continue
        d = pd.read_parquet(f)
        d = d.rename(columns={"segment_price_usd_per_mwh": "price"})
        d["year"] = np.int16(year)
        frames.append(d)
    out = pd.concat(frames, ignore_index=True, copy=False)
    frames.clear()
    return out.sort_values(["resource_seq", "interval_start_utc", "segment_mw"])


def _load_bids(years: list[int]) -> pd.DataFrame:
    """GENERATOR EN curve segments from the clean dam-public-bids tree."""
    frames = []
    for year in years:
        df = clean_io.read_clean(
            "dam-public-bids",
            iso="CAISO",
            year=year,
            market="DAM",
            validate=False,
            columns=_BID_COLS,
        )
        df = df[
            (df.resource_type == "GENERATOR")
            & (df["product"] == "EN")
            & (df.row_kind == "segment")
        ]
        frames.append(
            df[
                [
                    "interval_start_utc",
                    "resource_seq",
                    "segment_mw",
                    "segment_price_usd_per_mwh",
                ]
            ].assign(year=np.int16(year))
        )
        del df
    out = pd.concat(frames, ignore_index=True, copy=False)
    frames.clear()
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
    """Capacity-weighted quantile; NaN for an empty sample.

    An empty sample has no quantile, and saying so is the correct answer — the
    alternative (``np.interp`` raising) conflates "this cell has no data" with
    "the derive is broken". A NaN here is NOT tolerated on a CONSUMED band:
    ``main`` hard-fails on that, and only the reported-but-unarmed per-year
    detail is allowed to carry one (caiso-254 — the three-way partition gives
    ST_GAS a narrow 6.6 %-of-capacity committed window, which some
    resource-years simply do not price).
    """
    if values.size == 0 or weights.size == 0 or not np.isfinite(weights.sum()):
        return float("nan")
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w) - 0.5 * w
    return float(np.interp(q * w.sum(), cw, v))


def _kde(x: np.ndarray, w: np.ndarray, grid: np.ndarray, bw: float) -> np.ndarray:
    """Capacity-weighted Gaussian KDE — the antimode smoother."""
    z = (grid[:, None] - x[None, :]) / bw
    return (np.exp(-0.5 * z**2) * w[None, :]).sum(axis=1) / (bw * np.sqrt(2 * np.pi))


def locate_st_cut(res: pd.DataFrame, hr_cut: float) -> float | None:
    """Locate the CT/ST cut as the CT-side capacity-density antimode.

    The second cut is found the same way ``hr_cut`` = 8.5 was — as an interior
    local minimum of the capacity-weighted slope density, inside a window fixed
    from PUBLISHED fleet heat rates (:data:`ST_CUT_WINDOW`) rather than from
    where a mode happens to land. It is not swept, and nothing about it is
    chosen against a criterion, so it introduces no free parameter (rule 21
    [R-DOF]).

    Returns ``None`` when the CT-side density is unimodal inside the window, in
    which case the caller must NOT split: a unimodal population means the
    contamination is not separable from measured conduct (caiso-253b PRECOMMIT
    §2.1's FAIL branch) and the pooled bucket stands with its disclosed bound.
    """
    ct = res[res.is_gas & (res.slope >= hr_cut)]
    if len(ct) < 5:
        return None
    x = ct.slope.to_numpy(float)
    w = ct.cap.to_numpy(float)
    grid = np.linspace(hr_cut, GAS_SLOPE_RANGE[1], 400)
    dens = _kde(x, w, grid, ST_CUT_KDE_BW)
    lo, hi = ST_CUT_WINDOW
    win = (grid >= lo) & (grid <= hi)
    interior = np.r_[False, (dens[1:-1] < dens[:-2]) & (dens[1:-1] < dens[2:]), False]
    cands = grid[interior & win]
    if not cands.size:
        return None
    return float(cands[np.argmin(dens[interior & win])])


def _assign_classes(
    res: pd.DataFrame, hr_cut: float, st_cut: float | None
) -> pd.Series:
    """Three-way class assignment on the measured marginal-HR slope.

    ``CC_REGULAR`` below ``hr_cut``; ``CT_PEAKER`` between the cuts; ``ST_GAS``
    at/above ``st_cut``. With ``st_cut=None`` this is exactly the pre-repair
    two-way split, so the frozen construction remains reachable.
    """
    cls = np.where(res.slope < hr_cut, "CC_REGULAR", "CT_PEAKER")
    if st_cut is not None:
        cls = np.where(res.slope >= st_cut, "ST_GAS", cls)
    out = pd.Series(cls, index=res.index)
    out[~res.is_gas] = ""
    return out


def class_band_windows(
    geom: dict[str, dict[str, float]], cls: str
) -> dict[str, tuple[float, float]]:
    """Band windows (fractions of resource capacity) from the model's class geometry.

    ``committed`` = [0, pct_committed); ``econ_low`` / ``econ_high`` split the
    economic window at :data:`ECON_LOW_SHARE`; ``peak`` = [1 - pct_peaking, 1].
    Module-level (caiso-283) so the per-market-year reducer
    ``scripts/data/reduce_caiso_bid_year.py`` prices exactly the windows this
    derive prices — the same function, not a re-typed copy. ``main``'s
    ``band_windows`` closure delegates here; behaviour is unchanged.
    """
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
        # Theil-Sen, NOT least squares (caiso-153). The citygate regressor's
        # variance is dominated by an extreme tail — $24.29/MMBtu in January
        # 2023 against a 2023-25 median near $3-4 — so an OLS slope is levered
        # on a few days of one month of one year, and every resource that did
        # not track that spike proportionally (a different CA hub, a monthly
        # index, a cost-verified DEB on a lagged index) is attenuated toward
        # zero with its correlation intact. That is exactly the r >= 0.6 with
        # slope < 4 MMBtu/MWh signature FINDING-caiso152 §I reported as
        # physically impossible for a thermal unit.
        slope, _, _, _ = theilslopes(y, x)
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
    # Two-way here; the caller re-assigns three-way once the CT-side antimode
    # has been located off this same population (:func:`locate_st_cut`).
    res["cls"] = _assign_classes(res, hr_cut, None)
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
        "--from-reduced-store",
        action="store_true",
        help="read bids from the slim reduced store instead of the clean tree "
        "(the clean tree needs ~14.3 GB/year and cannot be built on a 15 GB box)",
    )
    ap.add_argument(
        "--no-st-split",
        action="store_true",
        help="keep the pre-caiso-254 TWO-way partition (CC/CT only), i.e. leave "
        "the OTC/RMR steamers pooled in the CT bucket with the disclosed "
        "contamination. Reproduces the frozen 2026-08-02 construction.",
    )
    ap.add_argument(
        "--st-split-report-only",
        action="store_true",
        help="THREE-way classification (so the CT bucket is de-contaminated) "
        "but consume only CC_REGULAR + CT_PEAKER: the ST_GAS bucket is still "
        "measured and published under _provenance.reported_not_consumed with "
        "its gate rows, and is EXCLUDED from the written artifact and from the "
        "consumed-gate verdict. caiso-255, owner grant of FINDING-caiso254 §4 "
        "option 1 (2026-09-06): the separated ST_GAS bucket FAILS G4 physical "
        "sanity (peak inverted below econ_high), and its bands are LP-inert on "
        "CAISO anyway (data.offer_curves bypasses ST_GAS_PEAKER_PLANTS, which "
        "is the whole CAISO ST_GAS fleet). NOT a gate relaxation: G4 runs "
        "unchanged and the refused bucket keeps its FAIL on the record.",
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
    if args.from_reduced_store:
        print(f"loading dam-public-bids from {REDUCED_STORE} ...", flush=True)
        bids = _load_bids_reduced(years)
    else:
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
    # The CLASS-PARTITION REPAIR (caiso-254). The pooled CT bucket mixed two
    # populations 9 % apart in fleet heat rate — CT_PEAKER's 10.862 and the
    # 2.9 GW of OTC/RMR ST_GAS steamers at 11.847 — so its cap-weighted median
    # was a statistic of the mixture, and `caiso_offer_surface_measured_
    # ungrounded` then priced ST_GAS off a bucket its own presence had biased.
    # A multiplier is defined against ITS OWN class base HR, so that is a
    # construction defect whichever way repairing it moves the price
    # (rule 23 [R-FROZEN-DERIVE]: this re-derives the PARTITION, not the same
    # construction hoping for a different number — the estimator, body probe,
    # gas gates, statistic, VOM, carbon netting and band geometry are all
    # untouched). Admitted by G-BIMODAL on the pooled 2023-25 population:
    # antimode 11.738 inside [10.9, 12.5] with 2.559 GW above it, inside
    # [1.5, 4.5] GW (results/calibration/_caiso253b_ct_bucket_bimodality.json).
    st_cut = None if args.no_st_split else locate_st_cut(res, args.hr_cut)
    if st_cut is not None:
        res["cls"] = _assign_classes(res, args.hr_cut, st_cut)
    # Distinguish the two reasons st_cut can be None: the operator ASKED for the
    # pre-repair two-way construction, vs the CT-side density having no antimode
    # in the window (G-BIMODAL's own FAIL branch). Conflating them would let a
    # `--no-st-split` run read as evidence that the population is unimodal.
    if st_cut is not None:
        _why = round(st_cut, 3)
    elif args.no_st_split:
        _why = "(--no-st-split: pre-repair TWO-way construction, not a measurement)"
    else:
        _why = "(MEASURED unimodal in the window - NOT split)"
    print(f"class partition: hr_cut={args.hr_cut} st_cut={_why}", flush=True)
    gaslike = res[res.is_gas]
    active_classes = [c for c in CLASSES if (c != "ST_GAS" or st_cut is not None)]
    buckets = {cls: gaslike[gaslike.cls == cls] for cls in active_classes}
    # CONSUMED vs MEASURED (caiso-255, owner grant of FINDING-caiso254 §4
    # option 1). `active_classes` is what the derive MEASURES and REPORTS;
    # `consumed_classes` is what it WRITES and what the gate verdict is taken
    # over. They differ only under --st-split-report-only, which drops ST_GAS
    # from consumption while leaving the three-way CLASSIFICATION intact -- so
    # the steamers are still removed from the CT bucket (the de-contamination
    # lives in the classification, not in the consumption) and their own
    # measured bucket is published as refused rather than hidden.
    consumed_classes = [
        c for c in active_classes if not (args.st_split_report_only and c == "ST_GAS")
    ]
    if args.st_split_report_only and st_cut is None:
        raise SystemExit(
            "--st-split-report-only requires the three-way partition: it is "
            "the CLASSIFICATION that de-contaminates the CT bucket. It is "
            "incompatible with --no-st-split (which would simply drop a class "
            "that was never separated) and with a measured-unimodal CT-side "
            "population (G-BIMODAL's own FAIL branch, where nothing is "
            "re-derived at all)."
        )
    if consumed_classes != active_classes:
        print(
            f"consumed classes {consumed_classes}; measured-but-REFUSED "
            f"{[c for c in active_classes if c not in consumed_classes]} "
            "(reported under _provenance.reported_not_consumed)",
            flush=True,
        )
    gates: dict[str, dict] = {}
    g1 = {}
    for cls, sub in buckets.items():
        ratio = sub.cap.sum() / geom[cls]["fleet_mw"]
        lo, hi = G1_BOUNDS[cls]
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
        return class_band_windows(geom, cls)

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
    # Both cuts are perturbed, each independently at the SAME +/-0.25 the
    # single-cut form used (the magnitude is not retuned by this repair; the
    # gate is generalized to the partition it now has to defend).
    g2 = {"cut": args.hr_cut, "st_cut": st_cut, "deltas": {}}
    g2_pass = True
    perturbations = [("hr_cut", d) for d in (-0.25, +0.25)]
    if st_cut is not None:
        perturbations += [("st_cut", d) for d in (-0.25, +0.25)]
    for which, dcut in perturbations:
        alt = gaslike.copy()
        alt["cls"] = _assign_classes(
            alt,
            args.hr_cut + (dcut if which == "hr_cut" else 0.0),
            None if st_cut is None else st_cut + (dcut if which == "st_cut" else 0.0),
        )
        alt_buckets = {cls: alt[alt.cls == cls] for cls in active_classes}
        alt_static, _, _ = static_bands(alt_buckets, with_detail=False)
        rowset = {}
        for cls in active_classes:
            for b in ("econ_low", "econ_high", "peak"):
                dev = abs(alt_static[cls][b] - static[cls][b])
                tol = max(LOYO_ABS, LOYO_REL * abs(static[cls][b]))
                rowset[f"{cls}.{b}"] = {
                    "alt": alt_static[cls][b],
                    "dev": round(dev, 3),
                    "tol": round(tol, 3),
                    "pass": bool(dev <= tol),
                }
                # Reported for every measured class; only a CONSUMED
                # class's deviation can fail the gate.
                if cls in consumed_classes:
                    g2_pass = g2_pass and dev <= tol
        g2["deltas"][f"{which}{dcut:+.2f}"] = rowset
    g2["pass"] = bool(g2_pass)
    gates["G2_cut_robustness"] = g2
    print(f"G2 cut+/-0.25 robustness: {'PASS' if g2_pass else 'FAIL'}", flush=True)

    # A consumed band with no sample is not a number the artifact may carry.
    # Reported-only cells (the unarmed `committed` band, the per-year detail)
    # may be null; econ_low / econ_high / peak may not.
    _nan_consumed = {
        f"{cls}.{b}": static[cls][b]
        for cls in consumed_classes
        for b in ("econ_low", "econ_high", "peak")
        if not np.isfinite(static[cls][b])
    }
    if _nan_consumed:
        raise SystemExit(
            "REFUSED: consumed band(s) have no sample on the pooled span: "
            f"{sorted(_nan_consumed)}. A class whose armed bands cannot be "
            "estimated must not be split out — re-run with --no-st-split "
            "(or --st-split-report-only, which refuses the class consumption "
            "while still publishing its measurement) and report the partition "
            "as inestimable rather than writing a null."
        )
    _nan_reported = {
        f"{cls}.{b}.{y}": v
        for cls in buckets
        for b, per in per_year_stats[cls].items()
        for y, v in per.items()
        if not np.isfinite(v)
    }
    if _nan_reported:
        print(
            f"per-year REPORTED cells with no sample (unarmed, null in "
            f"provenance): {sorted(_nan_reported)}",
            flush=True,
        )

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
    # 0.05 flatness tolerance: measured CT curves are near-flat, so adjacent
    # band medians may tie to within noise; a real inversion beyond it fails.
    _ORD_TOL = 0.05
    for cls in buckets:
        s = static[cls]
        ordered = (
            s["econ_high"] >= s["econ_low"] - _ORD_TOL
            and s["peak"] >= s["econ_high"] - _ORD_TOL
        )
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

    # The verdict is taken over the CONSUMED classes. A measured-but-refused
    # class (--st-split-report-only) keeps its gate rows in `gates` and in
    # `_provenance.reported_not_consumed` at full magnitude -- it is excluded
    # from the verdict because it is excluded from the ARTIFACT, not because
    # its failure was forgiven.
    all_pass = all(
        (
            all(g1[c]["pass"] for c in consumed_classes),
            g2["pass"],
            all(v["pass"] for c in consumed_classes for v in g3[c].values()),
            all(g4[c]["pass"] for c in consumed_classes),
        )
    )
    print(f"\nGATES {'ALL PASS' if all_pass else 'FAILED'}", flush=True)

    # Measured, gated, and REFUSED CONSUMPTION -- published rather than
    # dropped, so a reader of the artifact can see exactly what was left out
    # and why (caiso-255; rule 26 [R-DELETE] in spirit: a refused measurement
    # is recorded, never silently zeroed).
    def _f(v):
        """JSON-safe: a band with no sample is null, never a bare NaN."""
        return None if v is None or not np.isfinite(v) else v

    _reported_not_consumed = {
        cls: {
            "base_hr": round(geom[cls]["base_hr"], 3),
            "bands": {b: _f(static[cls][b]) for b in ("econ_low", "econ_high", "peak")},
            "unarmed": {"committed": _f(static[cls]["committed"])},
            "gates": {
                "G1_capacity_reconciliation": g1.get(cls),
                "G3_estimation_loyo": g3.get(cls),
                "G4_physical_sanity": g4.get(cls),
            },
            "reason": (
                "MEASURED AND REFUSED. caiso-255, owner grant of "
                "FINDING-caiso254-partition-repair-2026-09-06.md §4 option 1 "
                "(2026-09-06), pre-registered in "
                "PRECOMMIT-caiso255-ct-only-partition-adoption-2026-09-06.md "
                "BEFORE this artifact was written. The separated ST_GAS "
                "bucket FAILS G4 physical sanity -- its peak band sits below "
                "its econ_high, an inverted offer curve -- so it is not "
                "consumed. G4 is NOT relaxed and its tolerance is NOT retuned: "
                "the failure stands here at full magnitude. The three-way "
                "CLASSIFICATION is retained, which is what removes these "
                "resources from the CT_PEAKER bucket; consumers with no "
                "ST_GAS entry fall back to the (now de-contaminated) "
                "CT_PEAKER bucket exactly as a pre-repair artifact does. On "
                "CAISO this is additionally LP-inert: data.offer_curves "
                "bypasses offer_curve_by_group for every plant in "
                "ST_GAS_PEAKER_PLANTS, which is the entire CAISO ST_GAS "
                "fleet (plants 315 / 335 / 350, 2,858.8 MW), whose bands come "
                "from the caiso-239/240 per-plant measured registries instead."
            ),
        }
        for cls in active_classes
        if cls not in consumed_classes
    }

    provenance = {
        "source": (
            "CAISO OASIS Public Bid Data (PUB_DAM_GRP GroupZip, 90-day-lag "
            "masked DAM bids), dam-public-bids clean datatype, trade years "
            f"{years}"
        ),
        "derived_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "method": "see scripts/data/derive_caiso_offer_surface.py module docstring",
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
            "st_cut": st_cut,
            "st_cut_window": list(ST_CUT_WINDOW),
            "st_cut_kde_bw": ST_CUT_KDE_BW,
            "classes": list(active_classes),
            "consumed_classes": list(consumed_classes),
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
        "reported_not_consumed": _reported_not_consumed,
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
            for cls in consumed_classes
        },
    }
    OUT_STATIC.write_text(json.dumps(static_doc, indent=1) + "\n")
    print(f"wrote {OUT_STATIC}")

    cond_doc = {
        "_provenance": provenance,
        **{c: cond[c] for c in consumed_classes},
    }
    OUT_COND.write_text(json.dumps(cond_doc, indent=1) + "\n")
    print(f"wrote {OUT_COND}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
