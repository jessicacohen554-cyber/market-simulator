"""Derive MEASURED offer-curve heat-rate multipliers from the ERCOT 60-Day DAM.

This is the gated, *measured* successor to the analysis-only
``scripts/archive/analyze_dam_offer_multipliers.py``. Where the model today prices each
thermal band as ``MC = VOM + (base_HR x fuel_price) x mult`` with **chosen**
per-class multipliers (``cc_committed_hr_mult`` = 1.23, ``ct_committed_hr_mult``
= 1.28, ``coal_committed_hr_mult`` = 1.22, the ``*_econ_hr_mult`` set, and the
ERCOT ``offer_curve_by_group`` bands), this script replaces those heights with
the multipliers **implied by the real QSE-submitted DAM offer curves**, per asset
class, averaged across 2023-2025.

Method (measured, NOT fit to the LMP residual)
----------------------------------------------
1. Per resource-hour, per energy-curve point ``k``::

       hr_mult_k = (Curve-Price_k / fuel_price_day) / base_HR(resource)

   ``fuel_price_day`` is the delivery-date Henry Hub daily price plus the ERCOT
   gas basis (``GAS_BASIS_DIFFERENTIAL['ERCOT']`` = -0.5 $/MMBtu). ``base_HR`` is
   the class cap-weighted ``Plant_Avg_HR_MMBtu_MWh`` taken straight from the model
   fleet (``data/raw/reference/custom-bin-assignments.csv``), so the heat rate we DIVIDE by is
   the same one the model later MULTIPLIES each plant's own heat rate by. No VOM
   is subtracted (the task formula is ``price / fuel / HR``); VOM is a constant
   $2-4/MWh adder the model re-applies on top, so the recovered offer is the
   measured price plus that small constant -- a conservative, documented choice,
   not a tuning lever.

   The **committed** band is anchored on the three-part **Min Gen Cost** (the
   all-in $/MWh price the unit holds at LSL), not on the incremental energy curve
   -- the energy curve is incremental energy *above* LSL, so its points map onto
   the economic ramp and the peak, while the min-gen floor is the committed band.

2. Bin each energy-curve point by its MW position in the operating range,
   ``rel = (curve_mw - LSL) / (HSL - LSL)``, into the model tranches:
   ``econ_low`` (rel <= 0.33), ``econ_high`` (rel >= 0.67), with the top-of-curve
   point feeding the peak/scarcity reach.

3. Aggregate per class, **capacity-weighted across resources** (each resource
   contributes its own median per band so a high-frequency QSE cannot dominate,
   then resources are weighted by their HSL capacity), pooled across 2023-2025.
   Report the weighted median plus p25/p75, not just a point.

4. Separate the **competitive body** (curve_price < ``--body-cap``, default
   $1,000) from **near-cap bids**: report how often each class bids >= $1,000 and
   >= $4,500, and the realized SPP when it does (the scarcity condition).

The one decision -- the Peak tranche (A vs B)
---------------------------------------------
ERCOT RTSPP = energy LMP (offers, can hit the $5,000 cap) + ORDC reserve adder,
the sum capped at $5,000. The model's energy+reserve co-optimization already
produces the scarcity tail, so the body multipliers (steps 1-3) are identical
either way; only the **peak** band differs:

  * ``--peak-mode A`` (recommended): competitive-body peak (the top-of-curve
    multiplier below the body cap). Co-opt owns the spike; no double-count.
  * ``--peak-mode B``: full empirical peak including the near-cap bids (the
    capacity-weighted mean of the top-of-curve multiplier including >= body-cap
    points). Verify the combined LMP+reserve price is clamped at ``ordc_voll``.

Outputs
-------
* ``data/raw/_processed-legacy/ercot_dam_offer_hrmult_summary.csv`` -- the full measured
  distribution (committed / econ_low / econ_high / peak-body + near-cap incidence)
  per class, always written.
* ``data/raw/_validation-source/offer_curve_dam_hrmults.json`` -- the override curve
  (mirrors ``offer_curve_deltas_cc_merit_ramp.json``: class -> band -> value),
  written only with ``--write-json`` once the peak mode is chosen, and fed to the
  run via ``--offer-curve-override-json``.

Usage::

    python scripts/data/derive_dam_offer_hrmults.py                       # report only
    python scripts/data/derive_dam_offer_hrmults.py --peak-mode A --write-json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "src"))
from market_sim.config import paths  # noqa: E402

# W1 data reorg: inputs/processed -> data/raw/_processed-legacy,
# inputs/raw-data -> data/raw, inputs/calibration -> data/raw/_validation-source,
# inputs/custom-bin-assignments.csv -> data/raw/reference/. All resolved through
# config/paths.py (CLAUDE.md data rule) instead of the pre-reorg literals.
OFFERS = paths.PROCESSED_DIR / "ercot_dam_offers.parquet"
HENRY_HUB = paths.RAW_DIR / "gas-prices" / "henry_hub_daily.csv"
CAMPD_BINS = paths.CAMPD_BINS_CSV
OUT_SUMMARY = paths.PROCESSED_DIR / "ercot_dam_offer_hrmult_summary.csv"
OUT_JSON = paths.CALIBRATION_DIR / "offer_curve_dam_hrmults.json"
# --peak-ladder writes to its own artifact so the keeper-lineage p50 override
# file stays byte-stable: a run opts into the ladder by naming this file, it
# never rides in silently on the existing --offer-curve-json path.
OUT_JSON_LADDER = paths.CALIBRATION_DIR / "offer_curve_dam_hrmults_ladder.json"
# --condition-binned writes the heterogeneity-preserving, condition-responsive
# surface (ERCOT G-22 §8 / ercot37 filed path): the measured peak-band quantile
# ladder derived SEPARATELY within each net-load-percentile bin, so the model can
# select the tighter (higher) wall in its own anticipated-tight hours and leave the
# loose-hour offer stack untouched. Its own artifact so the p50/ladder files stay
# byte-stable; a run opts in via ScenarioConfig.ercot_offer_surface_binned_path.
OUT_JSON_CONDBINNED = paths.CALIBRATION_DIR / "offer_curve_dam_hrmults_condbinned.json"
# --low-curve-binned writes the trough-price-formation MIRROR of the condition-
# binned surface: the measured LOWER-tail quantile ladders (committed Min-Gen-Cost
# LSL block + lower-body incremental curve) per net-load bin, COMMITTED resources
# only. Its own artifact so the adopted top-surface JSON stays byte-stable
# (rule 23); a run opts in via ScenarioConfig.ercot_offer_surface_lowcurve.
OUT_JSON_LOWCURVE = paths.CALIBRATION_DIR / "offer_curve_dam_lowcurve_condbinned.json"
# --ep-basis-yearly writes the ERCOT-118 re-grounded CC band-multiplier tables:
# the SAME committed/econ_low/econ_high/peak p50 derivation as the adopted
# cconly file (peak mode B), but normalized by the EP-ANCHORED delivered-gas
# series the dispatch actually prices gas at (HH daily + the measured EIA
# N3045TX3 electric-power basis, data.fuel.basis.ercot.
# ercot_electric_power_gas_basis) instead of the stale HH-0.50 scalar, and
# derived PER DELIVERY YEAR instead of pooled 2023-2025. Rule-23 source-change
# citation: the ercot_zonal_gas_basis adoption moved the dispatch delivered-gas
# series (+0.50/+0.41/+0.04 $/MMBtu over HH-0.50 in 2023/24/25) under artifacts
# whose stated purpose is "the multiplier the model multiplies by", so the
# normalization series must follow it (derivation-consistency, ERCOT-117
# FINDING §4.3 — never a residual chase). Its own artifact; the pooled
# HH-0.50 files above stay byte-stable as the record of the old basis. A run
# opts in via ScenarioConfig.ercot_offer_hrmult_ep_rebasis.
OUT_JSON_EP_YEARLY = paths.CALIBRATION_DIR / "offer_curve_dam_hrmults_ep_yearly.json"

# Low-curve rel-band edges: the lower-body (rel < 0.67) incremental curve is
# measured in three equal curve-position bands, matching the model's per-plant
# rising econ ramp position-for-position (the v2 within-plant mapping — a
# cross-fleet RANK mapping conflated plant cheapness with curve position and
# eroded the mild-day evening margin, the v1 probe finding). The upper third
# (rel >= 0.67) belongs to the top leg's econ_high/peak repricing (rule 19 —
# disjoint by construction).
LOWCURVE_REL_BANDS = (0.0, 0.22, 0.44, 0.67)

# Net-load percentile bin EDGES for the condition-binned surface. Must match
# ScenarioConfig.ercot_offer_surface_netload_pcts (the mechanism asserts the JSON's
# recorded edges agree with the config). n edges → n+1 bins on the year's own
# net-load distribution (percentile-ranked → forward-native); bin 0 is loosest.
NETLOAD_PCT_EDGES = (0.80, 0.90, 0.97)

ERCOT_GAS_BASIS = -0.5  # GAS_BASIS_DIFFERENTIAL['ERCOT'], $/MMBtu over Henry Hub

# Map each measured DAM class -> the offer_curve_by_group output keys it grounds,
# and the model-fleet Plant_Group(s) whose cap-weighted Plant_Avg_HR is the
# divisor base_HR for that output group. One DAM CC class feeds both CC_REGULAR
# and CC_CHP; each is divided by ITS OWN group base_HR so the model recovers the
# measured offer when it multiplies that group's plants by their own heat rate.
# COAL is split into the two ERCOT solid-fuel offer-curve keys (lignite mine-mouth
# and railed PRB); both share the measured COAL distribution and the COAL fleet HR.
CLASS_TO_OUTPUT: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    "CC": [("CC_REGULAR", ("CC_REGULAR",)), ("CC_CHP", ("CC_CHP",))],
    "CT_PEAKER": [("CT_PEAKER", ("CT_PEAKER",))],
    "ST_GAS": [("ST_GAS", ("ST_GAS",))],
    "COAL": [("COAL_LIGNITE", ("COAL",)), ("COAL_PRB", ("COAL",))],
}

# Years to pool (delivery-date year). 60-day file labels lag, so the actual
# delivery dates run a full three years 2023-2025.
YEARS = (2023, 2024, 2025)

PCTS = (0.25, 0.50, 0.75)
SCARCITY_THRESH = 1000.0  # >= this is a scarcity / near-cap bid, not body
NEAR_CAP_THRESH = 4500.0  # >= this is right at the $5,000 offer-cap wall

# Published ERCOT system-wide offer cap (HCAP), $/MWh — 16 TAC §25.505(g)(6)(B),
# post-Uri PUCT order (docs/parameter-citations.md). Energy offers may not
# exceed it, so the top peak-ladder rung's implied price is clamped here at the
# pooled-mean derivation gas (the multiplier form drifts around HCAP with the
# hourly fuel price; the LP's $5,000 VOLL slack bounds the dual either way).
HCAP_USD_MWH = 5000.0

# Peak-ladder quantiles: equal-capacity rungs at the capacity-weighted
# quantiles of the per-resource top-of-curve multiplier (mode-B basis,
# near-cap bids included), each rung clamped FROM BELOW at the class p50.
# The upper rungs are the real market's always-posted scarcity wall the p50
# collapse deleted (docs/FINDING-ercot-priceshape-2026-07.md §4 — why the
# modeled duals top out at ~$150-200). The below-median clamp is structural,
# not a fit: the sub-p50 top-of-curve dispersion belongs to resources whose
# ENTIRE curve is cheap — their MW is already priced by those plants' cheaper
# committed/econ bands in the model's per-plant rising curves — and letting it
# re-price every plant's scarcity band cheapened the CT peak below the ST econ
# band, reproducing the documented CT<->ST coupling crater
# (docs/ercot-dam-offer-grounding-2026-06.md §4/§5: measured wall-probe A/B,
# CT +5.3 TWh / ST -8.0 TWh vs the CAMPD-measured volumes). A plant's scarcity
# band never bids below its class's measured median top-of-curve.
PEAK_LADDER_QUANTILES = (0.10, 0.30, 0.50, 0.70, 0.90)


def class_base_hr() -> dict[str, float]:
    """Cap-weighted Plant_Avg_HR per model-fleet Plant_Group (the divisor base_HR)."""
    df = pd.read_csv(CAMPD_BINS)
    out: dict[str, float] = {}
    for grp, d in df.groupby("Plant_Group"):
        w = d["Nameplate_MW"].to_numpy(float)
        hr = d["Plant_Avg_HR_MMBtu_MWh"].to_numpy(float)
        m = np.isfinite(hr) & np.isfinite(w) & (w > 0) & (hr > 0)
        if m.any():
            out[grp] = float(np.average(hr[m], weights=w[m]))
    return out


def output_base_hr(fleet_hr: dict[str, float], groups: tuple[str, ...]) -> float:
    """Cap-weighted base_HR for an output group from one or more fleet groups."""
    df = pd.read_csv(CAMPD_BINS)
    d = df[df["Plant_Group"].isin(groups)]
    w = d["Nameplate_MW"].to_numpy(float)
    hr = d["Plant_Avg_HR_MMBtu_MWh"].to_numpy(float)
    m = np.isfinite(hr) & np.isfinite(w) & (w > 0) & (hr > 0)
    return float(np.average(hr[m], weights=w[m]))


def coal_fuel_price(output_group: str) -> dict[int, float]:
    """Delivered coal $/MMBtu per year for a coal output group (lignite / PRB).

    Coal is take-or-pay: its delivered cost is the lignite mine-mouth or railed-PRB
    trajectory the model dispatches on, NOT Henry Hub. Coal offers MUST be divided
    by this so the recovered multiplier matches what the model multiplies coal
    base_HR by (the coal fuel price, via the supply-keyed passthrough).
    """
    from market_sim.data.fuel import COAL_PRICE_LIGNITE_BY_YEAR, COAL_PRICE_PRB_BY_YEAR

    table = (
        COAL_PRICE_PRB_BY_YEAR
        if output_group == "COAL_PRB"
        else COAL_PRICE_LIGNITE_BY_YEAR
    )
    return {y: float(table[y]) for y in YEARS}


def load_offers() -> pd.DataFrame:
    cols = [
        "delivery_date",
        "hour_ending",
        "model_class",
        "resource_name",
        "committed",
        "hsl",
        "lsl",
        "awarded_qty",
        "curve_mw",
        "curve_price",
        "min_gen_cost",
        "spp",
        "point",
    ]
    df = pd.read_parquet(OFFERS, columns=cols)
    df = df[df["model_class"].isin(CLASS_TO_OUTPUT)].copy()
    df["year"] = df["delivery_date"].dt.year
    df = df[df["year"].isin(YEARS)].copy()
    # Delivery-date Henry Hub daily + ERCOT basis -> delivered gas $/MMBtu.
    hh = pd.read_csv(HENRY_HUB, parse_dates=["date"]).rename(
        columns={"price_usd_mmbtu": "hh"}
    )
    hh = hh.set_index("date")["hh"].sort_index()
    daily = hh.reindex(pd.date_range(hh.index.min(), hh.index.max())).ffill()
    df["gas"] = df["delivery_date"].map(daily) + ERCOT_GAS_BASIS
    df = df[df["gas"] > 0].copy()
    return df


def netload_pct_by_hour() -> pd.DataFrame:
    """System net-load percentile per (year, delivery_date, hour_ending).

    The tightness driver for the condition-binned surface. Net-load is proxied by
    the DAM-awarded dispatchable quantity summed over all kept thermal resources
    per delivery hour (``awarded_qty`` is repeated across a resource-hour's curve
    points, so each resource-hour is counted once) — the same self-contained,
    forward-native proxy ``scripts/data/derive_ct_offer_surface.py`` uses (a load+VRE
    forecast regenerates it). Ranked to a percentile ``q`` WITHIN each year, so the
    bins track that year's own scarcity structure rather than an absolute MW line —
    the identical construction the mechanism applies at solve time on the model's
    own net-load.
    """
    raw = pd.read_parquet(
        OFFERS,
        columns=["delivery_date", "hour_ending", "resource_name", "awarded_qty"],
    )
    raw["year"] = raw["delivery_date"].dt.year
    raw = raw[raw["year"].isin(YEARS)]
    # One awarded value per resource-hour (drop the curve-point duplication), then
    # sum to a per-hour system dispatchable quantity.
    rh = raw.drop_duplicates(["delivery_date", "hour_ending", "resource_name"])
    net = (
        rh.groupby(["year", "delivery_date", "hour_ending"])["awarded_qty"]
        .sum()
        .rename("net_load")
        .reset_index()
    )
    net["q"] = net.groupby("year")["net_load"].rank(pct=True)
    return net[["delivery_date", "hour_ending", "q"]]


def netload_bin_index(q: np.ndarray, edges: tuple[float, ...]) -> np.ndarray:
    """Map net-load percentiles ``q`` onto bin indices ``0..len(edges)``.

    ``edges`` are ascending percentile cut points; bin 0 is ``q < edges[0]``
    (loosest), the last bin is ``q >= edges[-1]`` (tightest). The identical
    partition the mechanism uses at solve time.
    """
    return np.searchsorted(
        np.asarray(edges, dtype=float), np.asarray(q, dtype=float), side="right"
    )


def _wquantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    """Weighted quantile via the cumulative-weight CDF."""
    if len(values) == 0:
        return float("nan")
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w) - 0.5 * w
    cw /= w.sum()
    return float(np.interp(q, cw, v))


def _capwt_band(per_res: pd.DataFrame, col: str) -> dict[str, float]:
    """Capacity-weighted p25/p50/p75 of a per-resource band multiplier."""
    d = per_res[np.isfinite(per_res[col]) & np.isfinite(per_res["cap"])]
    d = d[d["cap"] > 0]
    if d.empty:
        return {f"p{int(p * 100)}": float("nan") for p in PCTS}
    v = d[col].to_numpy(float)
    w = d["cap"].to_numpy(float)
    return {f"p{int(p * 100)}": round(_wquantile(v, w, p), 3) for p in PCTS}


def derive_class(df_cls: pd.DataFrame, base_hr: float, body_cap: float) -> dict:
    """Measured band multipliers + near-cap incidence for one output group.

    ``df_cls`` must carry a per-row ``fuel`` column (delivered $/MMBtu: Henry
    Hub + ERCOT basis for gas, the lignite/PRB trajectory for coal).
    """
    d = df_cls.copy()
    d["cap"] = d["hsl"].astype(float)

    # --- committed band: from Min Gen Cost (the all-in LSL floor price) ---
    cm = d[
        (d["point"] == 1)
        & d["min_gen_cost"].notna()
        & (d["min_gen_cost"] > 0)
        & (d["lsl"] > 0)
    ].copy()
    cm["mult"] = cm["min_gen_cost"].to_numpy(float) / (
        cm["fuel"].to_numpy(float) * base_hr
    )
    comm_per_res = (
        cm.groupby("resource_name")
        .agg(mult=("mult", "median"), cap=("cap", "median"))
        .reset_index()
    )
    committed = _capwt_band(
        comm_per_res.rename(columns={"mult": "committed"}), "committed"
    )

    # --- energy-curve points: economic ramp + peak/scarcity ---
    e = d[(d["hsl"] > d["lsl"]) & (d["lsl"] >= 0) & (d["curve_price"] > 0)].copy()
    e["mult"] = e["curve_price"].to_numpy(float) / (e["fuel"].to_numpy(float) * base_hr)
    e["rel"] = ((e["curve_mw"] - e["lsl"]) / (e["hsl"] - e["lsl"])).clip(0.0, 1.0)
    body = e[e["curve_price"] < body_cap]

    # econ_low (bottom third) / econ_high (top third), competitive body only.
    lo = body[body["rel"] <= 0.33]
    hi = body[body["rel"] >= 0.67]
    lo_pr = (
        lo.groupby("resource_name")
        .agg(econ_low=("mult", "median"), cap=("cap", "median"))
        .reset_index()
    )
    hi_pr = (
        hi.groupby("resource_name")
        .agg(econ_high=("mult", "median"), cap=("cap", "median"))
        .reset_index()
    )
    econ_low = _capwt_band(lo_pr, "econ_low")
    econ_high = _capwt_band(hi_pr, "econ_high")

    # peak-body: top-of-curve multiplier below the body cap, per resource.
    topb = (
        body.groupby("resource_name")
        .agg(peak=("mult", "max"), cap=("cap", "median"))
        .reset_index()
    )
    peak_body = _capwt_band(topb, "peak")
    # peak-full (mode B): top-of-curve including near-cap bids.
    topf = (
        e.groupby("resource_name")
        .agg(peak=("mult", "max"), cap=("cap", "median"))
        .reset_index()
    )
    peak_full = _capwt_band(topf, "peak")

    # Peak ladder: equal-capacity rungs at the capacity-weighted quantiles of
    # the same per-resource top-of-curve distribution peak_full's p50 is the
    # median of — the across-resource dispersion, not a new measurement. The
    # top rung is clamped so its implied price at the pooled-mean derivation
    # fuel does not exceed the published HCAP offer cap.
    tf = topf[np.isfinite(topf["peak"]) & (topf["cap"] > 0)]
    mean_fuel = float(d["fuel"].mean()) if "fuel" in d else float("nan")
    peak_ladder: list[list[float]] = []
    if not tf.empty and np.isfinite(mean_fuel) and mean_fuel > 0:
        v = tf["peak"].to_numpy(float)
        w = tf["cap"].to_numpy(float)
        cap_mult = HCAP_USD_MWH / (mean_fuel * base_hr)
        p50 = _wquantile(v, w, 0.50)
        share = round(1.0 / len(PEAK_LADDER_QUANTILES), 3)
        peak_ladder = [
            [share, round(min(max(_wquantile(v, w, q), p50), cap_mult), 3)]
            for q in PEAK_LADDER_QUANTILES
        ]

    # --- near-cap incidence: per energy-offer-point share, plus the realized
    # SPP under scarcity bids (the condition the cap-reaching bids fire in) ---
    scarce = e["curve_price"] >= SCARCITY_THRESH
    nearcap = e["curve_price"] >= NEAR_CAP_THRESH
    spp_when_scarce = (
        float(e.loc[scarce, "spp"].median()) if scarce.any() else float("nan")
    )

    return {
        "n_resources": int(d["resource_name"].nunique()),
        "n_points": int(len(e)),
        "base_hr": round(base_hr, 3),
        "committed": committed,
        "econ_low": econ_low,
        "econ_high": econ_high,
        "peak_body": peak_body,
        "peak_full": peak_full,
        "peak_ladder": peak_ladder,
        "scarcity_bid_share": round(float(scarce.mean()), 5),
        "near_cap_bid_share": round(float(nearcap.mean()), 5),
        "spp_when_scarcity_bid_p50": round(spp_when_scarce, 1),
    }


def _peak_ladder_from(
    topf: pd.DataFrame, mean_fuel: float, base_hr: float, floor_mult: float
) -> list[list[float]]:
    """Equal-capacity quantile rungs of the per-resource top-of-curve multiplier.

    ``topf`` carries one ``peak`` (max top-of-curve multiplier) and ``cap`` (HSL)
    per resource. Returns ``[[share, mult], ...]`` at the capacity-weighted
    :data:`PEAK_LADDER_QUANTILES`, each rung clamped FROM BELOW at ``floor_mult``
    (the finding's below-median clamp — a plant's scarcity band never bids below
    the class all-hours median, so the ladder is a pure upward widening) and from
    above at the published HCAP offer cap. Empty when the bin has no resources.
    """
    tf = topf[np.isfinite(topf["peak"]) & (topf["cap"] > 0)]
    if tf.empty or not (np.isfinite(mean_fuel) and mean_fuel > 0):
        return []
    v = tf["peak"].to_numpy(float)
    w = tf["cap"].to_numpy(float)
    cap_mult = HCAP_USD_MWH / (mean_fuel * base_hr)
    share = round(1.0 / len(PEAK_LADDER_QUANTILES), 3)
    return [
        [share, round(min(max(_wquantile(v, w, q), floor_mult), cap_mult), 3)]
        for q in PEAK_LADDER_QUANTILES
    ]


def derive_peak_binned(
    df_cls: pd.DataFrame, base_hr: float, edges: tuple[float, ...], floor_mult: float
) -> list[list[list[float]]]:
    """Per-net-load-bin measured peak-band quantile ladders for one output group.

    ``df_cls`` must carry the per-row ``fuel`` (delivered $/MMBtu) and ``q`` (system
    net-load percentile) columns. For each of the ``len(edges)+1`` net-load bins,
    the per-resource top-of-curve multiplier (mode-B: the max of ``curve_price /
    (fuel x base_HR)`` over the resource's offer points whose delivery hour falls in
    that bin) is reduced to equal-capacity quantile rungs (:func:`_peak_ladder_from`).
    So the tightest bin carries the wall QSEs post when scarcity is anticipated, the
    loose bins the competitive body — the measured condition response
    (docs/FINDING-ercot-priceshape-2026-07.md §4). ``floor_mult`` clamps every rung
    from below (the class all-hours peak median) so no bin lowers the stack.

    Returns one ladder (``[[share, mult], ...]``) per bin, loosest first. A bin with
    no resources yields ``[]`` — the mechanism treats an empty/loose bin as inert.
    """
    d = df_cls[(df_cls["hsl"] > df_cls["lsl"]) & (df_cls["curve_price"] > 0)].copy()
    d["mult"] = d["curve_price"].to_numpy(float) / (d["fuel"].to_numpy(float) * base_hr)
    d["cap"] = d["hsl"].astype(float)
    d["bin"] = netload_bin_index(d["q"].to_numpy(float), edges)
    ladders: list[list[list[float]]] = []
    for b in range(len(edges) + 1):
        db = d[d["bin"] == b]
        # Per-resource top-of-curve within this tightness bin (incl. near-cap bids).
        topf = (
            db.groupby("resource_name")
            .agg(peak=("mult", "max"), cap=("cap", "median"))
            .reset_index()
        )
        mean_fuel = float(db["fuel"].mean()) if len(db) else float("nan")
        ladders.append(_peak_ladder_from(topf, mean_fuel, base_hr, floor_mult))
    return ladders


def derive_econ_high_binned(
    df_cls: pd.DataFrame,
    base_hr: float,
    edges: tuple[float, ...],
    body_cap: float,
    floor_mult: float,
) -> list[float]:
    """Per-net-load-bin measured econ_high (upper economic ramp) multiplier.

    The finding's §6 evidence is decisive: repricing the thin peak band ALONE cannot
    flip the missed mid-merit hours, whose marginal unit sits in the *economic* band
    (LP dual ~$43-51, CC econ). So the condition surface must also lift the top of the
    economic ramp — the ``econ_high`` tranche (curve position ``rel >= 0.67``) — to
    its MEASURED tight-hour offer, which exhausts the phantom sub-$200 spare so the
    price finds the next (peak-ladder) offer. Heterogeneity is preserved: ``econ_low``
    is never touched, only the upper economic ramp. Capacity-weighted per-resource
    median of the competitive-body (``curve_price < body_cap``) multiplier within each
    tightness bin, clamped from below at the class all-hours econ_high median (so no
    bin lowers the stack). ``nan`` for an empty bin (mechanism treats as inert).
    """
    e = df_cls[(df_cls["hsl"] > df_cls["lsl"]) & (df_cls["curve_price"] > 0)].copy()
    e["mult"] = e["curve_price"].to_numpy(float) / (e["fuel"].to_numpy(float) * base_hr)
    e["rel"] = ((e["curve_mw"] - e["lsl"]) / (e["hsl"] - e["lsl"])).clip(0.0, 1.0)
    e["cap"] = e["hsl"].astype(float)
    e["bin"] = netload_bin_index(e["q"].to_numpy(float), edges)
    hi = e[(e["rel"] >= 0.67) & (e["curve_price"] < body_cap)]
    out: list[float] = []
    for b in range(len(edges) + 1):
        hb = hi[hi["bin"] == b]
        pr = (
            hb.groupby("resource_name")
            .agg(econ_high=("mult", "median"), cap=("cap", "median"))
            .reset_index()
        )
        band = _capwt_band(pr, "econ_high")
        v = band["p50"]
        out.append(float(max(v, floor_mult)) if v == v else float("nan"))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--body-cap",
        type=float,
        default=SCARCITY_THRESH,
        help="curve_price below this is the competitive body (default 1000)",
    )
    ap.add_argument(
        "--peak-mode",
        choices=["A", "B"],
        default="A",
        help="A: body-only peak (co-opt owns the spike, default); "
        "B: full empirical peak incl. near-cap bids",
    )
    ap.add_argument(
        "--write-json",
        action="store_true",
        help="write the override curve JSON for --offer-curve-override-json",
    )
    ap.add_argument(
        "--include-coal",
        action="store_true",
        help="include COAL_LIGNITE/COAL_PRB in the override JSON. OFF by "
        "default: ERCOT coal is take-or-pay sunk fuel priced cheap by "
        "design, its DAM Min Gen Cost is non-fuel-dominated (measured "
        "2-3x), and it is governed by the dedicated lignite-sigmoid / "
        "PRB-floor calibration — so the measured override scopes to the "
        "gas energy stack (CC/CT/ST_GAS). Coal is always REPORTED.",
    )
    ap.add_argument(
        "--only-groups",
        default=None,
        metavar="G1,G2",
        help="restrict the override JSON to these output groups "
        "(e.g. CC_REGULAR,CC_CHP for the CC-only variant that "
        "avoids the CT<->ST coupling crater). Default: all gas groups.",
    )
    ap.add_argument(
        "--out-json",
        default=None,
        metavar="PATH",
        help="override JSON output path (default offer_curve_dam_hrmults.json)",
    )
    ap.add_argument(
        "--peak-ladder",
        action="store_true",
        help="emit the measured peak-band quantile ladder (mode B only): "
        "equal-capacity rungs at the capacity-weighted "
        f"{'/'.join(f'p{int(q * 100)}' for q in PEAK_LADDER_QUANTILES)} of the "
        "per-resource top-of-curve multiplier, top rung clamped at the "
        "published HCAP. Represents the measured across-resource offer "
        "dispersion (the scarcity wall) instead of collapsing it to the p50 "
        "(docs/FINDING-ercot-priceshape-2026-07.md §4).",
    )
    ap.add_argument(
        "--condition-binned",
        action="store_true",
        help="emit the HETEROGENEITY-PRESERVING condition-responsive surface "
        "(ERCOT G-22 §8 / ercot37 filed path): the measured peak-band quantile "
        "ladder derived SEPARATELY within each net-load-percentile bin "
        f"(edges {NETLOAD_PCT_EDGES}), so the model selects the tighter wall in "
        "its own anticipated-tight hours. Writes "
        "offer_curve_dam_hrmults_condbinned.json (its own artifact; the p50/ladder "
        "files are untouched). Implies mode B; coal excluded (gas peak bands only).",
    )
    ap.add_argument(
        "--low-curve-binned",
        action="store_true",
        help="emit the conditional LOW-curve surface (the trough-price-formation "
        "mirror of --condition-binned): the measured lower-tail quantile ladders "
        "(committed Min-Gen-Cost LSL block + lower-body incremental curve) per "
        f"net-load-percentile bin (edges {NETLOAD_PCT_EDGES}), COMMITTED "
        "resources only. Writes offer_curve_dam_lowcurve_condbinned.json (its "
        "own artifact; the adopted top-surface JSON is untouched). Gas only.",
    )
    ap.add_argument(
        "--ep-basis-yearly",
        action="store_true",
        help="emit the ERCOT-118 re-grounded CC band multipliers: the identical "
        "committed/econ_low/econ_high/peak p50 derivation as the adopted "
        "cconly override (peak mode B), normalized by the EP-anchored "
        "delivered-gas series dispatch prices gas at (HH daily + measured EIA "
        "N3045TX3 electric-power basis) with PER-YEAR tables replacing the "
        "pooled p50s. Writes offer_curve_dam_hrmults_ep_yearly.json (its own "
        "artifact; the pooled HH-0.50 files are untouched, rule 23).",
    )
    ap.add_argument(
        "--coal-yearly",
        action="store_true",
        help="emit the ERCOT-122 per-year measured COAL band multipliers: the "
        "ERCOT-118 econ_low/econ_high/peak(B) derivation applied to the CLLIG "
        "fleet, divided by the delivered coal price the model dispatches on "
        "(lignite / PRB trajectories, never Henry Hub). Records per-band "
        "capacity COVERAGE and the offered-headroom REACH so the "
        "non-fleet-representative bands (committed absent, econ_high 21-47 %% "
        "coverage) cannot be adopted blind. Writes "
        "offer_curve_dam_hrmults_coal_yearly.json (its own artifact; the "
        "pooled files are untouched, rule 23).",
    )
    ap.add_argument(
        "--continuous",
        action="store_true",
        help="ERCOT-178: write the continuous-node vintage of the "
        "condition-binned peak surface (offer_curve_dam_hrmults_contpct.json) "
        "— the frozen stepped artifact is never touched by this mode",
    )
    args = ap.parse_args()

    if args.continuous:
        derive_condition_continuous(args.out_json)
        return
    if args.coal_yearly:
        derive_coal_yearly(args.out_json, args.body_cap)
        return
    if args.condition_binned:
        derive_condition_binned(NETLOAD_PCT_EDGES, args.out_json)
        return
    if args.low_curve_binned:
        derive_lowcurve_binned(NETLOAD_PCT_EDGES, args.out_json)
        return
    if args.ep_basis_yearly:
        derive_ep_basis_yearly(args.out_json, args.body_cap)
        return

    fleet_hr = class_base_hr()
    df = load_offers()
    print(
        f"Loaded {len(df):,} offer-point rows, {df['delivery_date'].min().date()} "
        f"-> {df['delivery_date'].max().date()}  (years {YEARS})\n"
    )
    print("Model-fleet cap-weighted base_HR (MMBtu/MWh):")
    for g in ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS", "COAL"):
        print(f"  {g:12s} {fleet_hr.get(g, float('nan')):.3f}")
    print()

    results: dict[str, dict] = {}
    rows = []
    for dam_cls, outputs in CLASS_TO_OUTPUT.items():
        df_cls = df[df["model_class"] == dam_cls]
        for out_group, fleet_groups in outputs:
            bhr = output_base_hr(fleet_hr, fleet_groups)
            # Per-row delivered fuel price: gas for gas classes, the coal
            # trajectory for coal so the divisor is the fuel the model prices on.
            d_cls = df_cls.copy()
            if dam_cls == "COAL":
                cp = coal_fuel_price(out_group)
                d_cls["fuel"] = d_cls["year"].map(cp).astype(float)
            else:
                d_cls["fuel"] = d_cls["gas"].astype(float)
            r = derive_class(d_cls, bhr, args.body_cap)
            results[out_group] = r
            rows.append(
                {
                    "output_group": out_group,
                    "dam_class": dam_cls,
                    "base_hr": r["base_hr"],
                    "n_resources": r["n_resources"],
                    "committed_p50": r["committed"]["p50"],
                    "committed_p25": r["committed"]["p25"],
                    "committed_p75": r["committed"]["p75"],
                    "econ_low_p50": r["econ_low"]["p50"],
                    "econ_low_p25": r["econ_low"]["p25"],
                    "econ_low_p75": r["econ_low"]["p75"],
                    "econ_high_p50": r["econ_high"]["p50"],
                    "econ_high_p25": r["econ_high"]["p25"],
                    "econ_high_p75": r["econ_high"]["p75"],
                    "peak_body_p50": r["peak_body"]["p50"],
                    "peak_full_p50": r["peak_full"]["p50"],
                    "scarcity_bid_share": r["scarcity_bid_share"],
                    "near_cap_bid_share": r["near_cap_bid_share"],
                    "spp_when_scarcity_bid_p50": r["spp_when_scarcity_bid_p50"],
                }
            )

    summary = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    print("=== MEASURED DAM offer-curve multipliers (capacity-weighted, 2023-2025) ===")
    print(summary.to_string(index=False))

    summary.to_csv(OUT_SUMMARY, index=False)
    print(f"\nWrote {OUT_SUMMARY}")

    if args.write_json:
        only = (
            set(g.strip() for g in args.only_groups.split(","))
            if args.only_groups
            else None
        )
        curve = build_override_curve(
            results,
            args.peak_mode,
            args.include_coal,
            only,
            peak_ladder=args.peak_ladder,
        )
        out_path = (
            Path(args.out_json)
            if args.out_json
            else (OUT_JSON_LADDER if args.peak_ladder else OUT_JSON)
        )
        out_path.write_text(json.dumps(curve, indent=1) + "\n")
        print(
            f"Wrote {out_path}  (peak-mode {args.peak_mode}, "
            f"coal {'included' if args.include_coal else 'excluded'}, "
            f"groups {sorted(curve)})"
        )
        print(json.dumps(curve, indent=1))


def build_override_curve(
    results: dict[str, dict],
    peak_mode: str,
    include_coal: bool = False,
    only_groups: set[str] | None = None,
    peak_ladder: bool = False,
) -> dict:
    """Assemble the class -> band -> multiplier override from the measured p50s.

    With ``peak_ladder`` (mode B only), each group additionally carries a
    ``peak_ladder`` band — ``[[capacity_share, multiplier], ...]`` equal-capacity
    rungs at the measured across-resource quantiles — which the fleet builder
    uses to split the peak tranche instead of the single p50 ``peak`` height
    (kept alongside for provenance and for consumers that ignore the ladder).
    """
    curve: dict[str, dict[str, float]] = {}
    for group, r in results.items():
        if only_groups is not None and group not in only_groups:
            continue
        if group.startswith("COAL") and not include_coal:
            continue
        bands = {
            "committed": r["committed"]["p50"],
            "econ_low": r["econ_low"]["p50"],
            "econ_high": r["econ_high"]["p50"],
        }
        bands["peak"] = (
            r["peak_body"]["p50"] if peak_mode == "A" else r["peak_full"]["p50"]
        )
        curve[group] = {
            k: round(float(v), 3) for k, v in bands.items() if v == v
        }  # drop NaN bands
        if peak_ladder and peak_mode == "B" and r.get("peak_ladder"):
            curve[group]["peak_ladder"] = r["peak_ladder"]
    return curve


# Gas peak bands the condition-responsive surface prices (rule 19: it supersedes
# the static p50 peak on exactly these classes). Coal is take-or-pay sunk fuel with
# its own dedicated sigmoid/floor calibration, and CT_CHP has no measured DAM class,
# so both are excluded — the surface scopes to the gas energy stack, matching §3 of
# the finding (the missed-tail spare is CC/CT/ST peak capacity).
CONDBINNED_GROUPS: tuple[str, ...] = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS")


def derive_condition_binned(edges: tuple[float, ...], out_json: str | None) -> None:
    """Derive and write the condition-binned peak-offer surface (mode B, gas only).

    For each gas peak-band group, the measured peak-band quantile ladder is derived
    SEPARATELY within each net-load-percentile bin (:func:`derive_peak_binned`),
    every rung clamped from below at the class all-hours peak median (so no bin
    lowers the stack) and from above at HCAP. The JSON records the bin edges (the
    mechanism asserts they match ``ScenarioConfig.ercot_offer_surface_netload_pcts``)
    and, per group, ``peak_p50`` (the all-hours reference) plus ``binned_ladder``
    (one ladder per bin, loosest first). Written to
    ``offer_curve_dam_hrmults_condbinned.json`` by default.
    """
    fleet_hr = class_base_hr()
    df = load_offers()
    netq = netload_pct_by_hour()
    df = df.merge(netq, on=["delivery_date", "hour_ending"], how="inner")
    print(
        f"Loaded {len(df):,} offer-point rows with net-load percentile, "
        f"{df['delivery_date'].min().date()} -> {df['delivery_date'].max().date()} "
        f"(years {YEARS}); edges {edges}\n"
    )

    payload: dict = {
        "_provenance": {
            "source": "ERCOT 60-Day DAM Disclosure Gen Resource Data, delivery "
            "years 2023-2025 (ercot_dam_offers.parquet)",
            "method": "mode-B per-resource top-of-curve heat-rate multiplier, "
            "capacity-weighted quantiles, derived within net-load-percentile bins; "
            "each rung clamped [class all-hours peak median, HCAP]",
            "driver": "system net-load percentile within year (DAM dispatchable "
            "awarded quantity), forward-native (load+VRE forecast regenerates it)",
            "netload_pct_edges": list(edges),
            "peak_ladder_quantiles": list(PEAK_LADDER_QUANTILES),
            "hcap_usd_mwh": HCAP_USD_MWH,
            "iso": "ERCOT",
        }
    }
    for dam_cls, outputs in CLASS_TO_OUTPUT.items():
        if dam_cls == "COAL":
            continue
        df_cls = df[df["model_class"] == dam_cls].copy()
        df_cls["fuel"] = df_cls["gas"].astype(float)
        for out_group, fleet_groups in outputs:
            if out_group not in CONDBINNED_GROUPS:
                continue
            bhr = output_base_hr(fleet_hr, fleet_groups)
            # All-hours peak median (mode B) — the below-clamp floor and the
            # reference the mechanism divides by to recover the ratio-on-fleet-height.
            topf_all = (
                df_cls[(df_cls["hsl"] > df_cls["lsl"]) & (df_cls["curve_price"] > 0)]
                .assign(
                    mult=lambda x: (
                        x["curve_price"].to_numpy(float)
                        / (x["fuel"].to_numpy(float) * bhr)
                    ),
                    cap=lambda x: x["hsl"].astype(float),
                )
                .groupby("resource_name")
                .agg(peak=("mult", "max"), cap=("cap", "median"))
                .reset_index()
            )
            p50 = _capwt_band(topf_all.rename(columns={"peak": "pk"}), "pk")["p50"]
            ladders = derive_peak_binned(df_cls, bhr, edges, floor_mult=p50)
            # All-hours econ_high median — the below-clamp floor for the binned
            # econ_high (so a loose bin never lowers the upper economic ramp).
            eh_all = df_cls[
                (df_cls["hsl"] > df_cls["lsl"]) & (df_cls["curve_price"] > 0)
            ].copy()
            eh_all["mult"] = eh_all["curve_price"].to_numpy(float) / (
                eh_all["fuel"].to_numpy(float) * bhr
            )
            eh_all["rel"] = (
                (eh_all["curve_mw"] - eh_all["lsl"]) / (eh_all["hsl"] - eh_all["lsl"])
            ).clip(0.0, 1.0)
            eh_all["cap"] = eh_all["hsl"].astype(float)
            eh_hi = eh_all[(eh_all["rel"] >= 0.67) & (eh_all["curve_price"] < 1000.0)]
            eh_pr = (
                eh_hi.groupby("resource_name")
                .agg(econ_high=("mult", "median"), cap=("cap", "median"))
                .reset_index()
            )
            eh_p50 = _capwt_band(eh_pr, "econ_high")["p50"]
            econ_high_binned = derive_econ_high_binned(
                df_cls, bhr, edges, body_cap=1000.0, floor_mult=eh_p50
            )
            payload[out_group] = {
                "base_hr": round(bhr, 3),
                "peak_p50": round(float(p50), 3),
                "econ_high_p50": round(float(eh_p50), 3),
                "binned_ladder": ladders,
                "binned_econ_high": [
                    round(v, 3) if v == v else None for v in econ_high_binned
                ],
            }
            top_by_bin = [round(lad[-1][1], 1) if lad else None for lad in ladders]
            print(
                f"  {out_group:11s} base_HR {bhr:5.2f}  peak_p50 {p50:6.2f}  "
                f"econ_hi_p50 {eh_p50:5.2f}  eh/bin "
                f"{[round(v, 2) if v == v else None for v in econ_high_binned]}  "
                f"top-rung/bin {top_by_bin}"
            )

    out_path = Path(out_json) if out_json else OUT_JSON_CONDBINNED
    out_path.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"\nWrote {out_path}  (groups {sorted(CONDBINNED_GROUPS)})")


def derive_condition_continuous(out_json: str | None) -> None:
    """Derive and write the ERCOT-178 continuous-node peak surface vintage.

    The IDENTICAL statistic :func:`derive_condition_binned` computes per
    net-load bin — the per-resource top-of-curve multiplier reduced by
    :func:`_peak_ladder_from` with the class all-hours ``floor_mult`` and HCAP
    clamps — keyed per corpus HOUR NODE at the hour's within-year net-load
    percentile ``q`` instead of per bin (PRECOMMIT-ercot178 §2). The pooled
    identification basis is unchanged: all disclosure years pool, and hours
    from different years sharing an exactly tied rank pool their rows (the
    only cross-hour pooling, forced by x-monotonicity). Zero new parameters;
    the stepped artifact is never touched. Writes
    ``offer_curve_dam_hrmults_contpct.json`` (mode B, gas only).
    """
    fleet_hr = class_base_hr()
    df = load_offers()
    netq = netload_pct_by_hour()
    df = df.merge(netq, on=["delivery_date", "hour_ending"], how="inner")
    print(
        f"Loaded {len(df):,} offer-point rows with net-load percentile, "
        f"{df['delivery_date'].min().date()} -> {df['delivery_date'].max().date()} "
        f"(years {YEARS}); continuous-node vintage\n"
    )

    payload: dict = {
        "_provenance": {
            "source": "ERCOT 60-Day DAM Disclosure Gen Resource Data, delivery "
            "years 2023-2025 (ercot_dam_offers.parquet)",
            "method": "IDENTICAL statistic to the stepped vintage (mode-B "
            "per-resource top-of-curve heat-rate multiplier, capacity-weighted "
            "quantiles, each rung clamped [class all-hours peak median, HCAP]), "
            "keyed per corpus HOUR NODE at the hour's within-year net-load "
            "percentile instead of per bin; rank-tied hours (within and across "
            "years) pool their rows (PRECOMMIT-ercot178 §2, zero new "
            "parameters)",
            "driver": "system net-load percentile within year (DAM dispatchable "
            "awarded quantity), forward-native (load+VRE forecast regenerates "
            "it)",
            "conditioning": "continuous-netload-pct",
            "peak_ladder_quantiles": list(PEAK_LADDER_QUANTILES),
            "hcap_usd_mwh": HCAP_USD_MWH,
            "iso": "ERCOT",
        }
    }
    for dam_cls, outputs in CLASS_TO_OUTPUT.items():
        if dam_cls == "COAL":
            continue
        df_cls = df[df["model_class"] == dam_cls].copy()
        df_cls["fuel"] = df_cls["gas"].astype(float)
        for out_group, fleet_groups in outputs:
            if out_group not in CONDBINNED_GROUPS:
                continue
            bhr = output_base_hr(fleet_hr, fleet_groups)
            # All-hours peak median (mode B) — the below-clamp floor, computed
            # exactly as the stepped derive (unchanged reference).
            topf_all = (
                df_cls[(df_cls["hsl"] > df_cls["lsl"]) & (df_cls["curve_price"] > 0)]
                .assign(
                    mult=lambda x: (
                        x["curve_price"].to_numpy(float)
                        / (x["fuel"].to_numpy(float) * bhr)
                    ),
                    cap=lambda x: x["hsl"].astype(float),
                )
                .groupby("resource_name")
                .agg(peak=("mult", "max"), cap=("cap", "median"))
                .reset_index()
            )
            p50 = _capwt_band(topf_all.rename(columns={"peak": "pk"}), "pk")["p50"]

            d = df_cls[
                (df_cls["hsl"] > df_cls["lsl"]) & (df_cls["curve_price"] > 0)
            ].copy()
            d["mult"] = d["curve_price"].to_numpy(float) / (
                d["fuel"].to_numpy(float) * bhr
            )
            d["cap"] = d["hsl"].astype(float)
            pct_nodes: list[float] = []
            mult_nodes: list[list[float]] = []
            for x, dn in d.groupby("q", sort=True):
                topf = (
                    dn.groupby("resource_name")
                    .agg(peak=("mult", "max"), cap=("cap", "median"))
                    .reset_index()
                )
                mean_fuel = float(dn["fuel"].mean()) if len(dn) else float("nan")
                lad = _peak_ladder_from(topf, mean_fuel, bhr, floor_mult=p50)
                if not lad:
                    continue
                pct_nodes.append(round(float(x), 6))
                mult_nodes.append([float(m) for _s, m in lad])
            payload[out_group] = {
                "base_hr": round(bhr, 3),
                "peak_p50": round(float(p50), 3),
                "cont": {
                    "pct": pct_nodes,
                    "mult": mult_nodes,
                    "n_rungs": len(PEAK_LADDER_QUANTILES),
                    "n_nodes": len(pct_nodes),
                },
            }
            print(
                f"  {out_group:11s} base_HR {bhr:5.2f}  peak_p50 {p50:6.2f}  "
                f"nodes {len(pct_nodes)}"
            )

    out_path = (
        Path(out_json)
        if out_json
        else paths.CALIBRATION_DIR / "offer_curve_dam_hrmults_contpct.json"
    )
    out_path.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"\nWrote {out_path}  (groups {sorted(CONDBINNED_GROUPS)})")


def _lowcurve_p50(per_res: pd.DataFrame) -> float | None:
    """Capacity-weighted p50 multiplier from per-resource median rows."""
    d = per_res[np.isfinite(per_res["mult"]) & (per_res["cap"] > 0)]
    if d.empty:
        return None
    v = d["mult"].to_numpy(float)
    w = d["cap"].to_numpy(float)
    return round(_wquantile(v, w, 0.50), 3)


def derive_lowcurve_binned(edges: tuple[float, ...], out_json: str | None) -> None:
    """Derive and write the conditional LOW-curve gas offer surface (gas only).

    The trough-price-formation mirror of :func:`derive_condition_binned`
    (the ERCOT G-22 conditional-offer-distribution lane's LOW leg): for each gas
    group and each net-load-percentile bin, the measured LOWER-tail quantile
    ladders of the offer distribution, restricted to COMMITTED (online)
    resources — an OFF unit's cheap segments are not in the cleared supply
    stack, so the low side is derived online-only where the top-of-curve wall
    is rightly derived offer-posted-regardless-of-award (the asymmetry is
    deliberate and documented here).

    Two bands per group per bin:

    * ``binned_committed_p50`` — the capacity-weighted p50 of the per-resource
      median Min-Gen-Cost (LSL block) multiplier: committed units bid their LSL
      far below SRMC to stay on (cycling avoidance), and more so in tight bins.
    * ``binned_low_body`` — the capacity-weighted p50 of the per-resource median
      incremental-curve multiplier within each ``LOWCURVE_REL_BANDS`` curve-
      position band (``rel`` < 0.22 / 0.44 / 0.67), competitive body
      (``curve_price < $1000``) — the measured price of each plant's FIRST
      segments, matched to the model's per-plant rising econ ramp position-for-
      position (the v2 within-plant mapping; heterogeneity rides on each
      plant's own heat rate).

    Written to ``offer_curve_dam_lowcurve_condbinned.json`` (its own artifact —
    the adopted top-surface JSON stays byte-stable, rule 23). Applied by
    ``data.fleet.build_ercot_offer_surface_lowcurve_markdown`` (P1-only,
    ratio clamped <= 1).
    """
    fleet_hr = class_base_hr()
    df = load_offers()
    netq = netload_pct_by_hour()
    df = df.merge(netq, on=["delivery_date", "hour_ending"], how="inner")
    df = df[df["committed"] == True].copy()  # noqa: E712 — online resources only
    print(
        f"Loaded {len(df):,} COMMITTED offer-point rows with net-load percentile, "
        f"{df['delivery_date'].min().date()} -> {df['delivery_date'].max().date()} "
        f"(years {YEARS}); edges {edges}\n"
    )

    payload: dict = {
        "_provenance": {
            "source": "ERCOT 60-Day DAM Disclosure Gen Resource Data, delivery "
            "years 2023-2025 (ercot_dam_offers.parquet), COMMITTED (online-status) "
            "resources only",
            "method": "capacity-weighted quantile ladders of per-resource median "
            "heat-rate multipliers, derived within net-load-percentile bins: "
            "committed = Min Gen Cost (LSL block); low body = incremental curve "
            "rel < 0.67, competitive body (< $1000). Lower-tail mirror of the "
            "condition-binned peak surface; applied P1-only with ratio <= 1.",
            "driver": "system net-load percentile within year (DAM dispatchable "
            "awarded quantity), forward-native (load+VRE forecast regenerates it)",
            "netload_pct_edges": list(edges),
            "rel_bands": list(LOWCURVE_REL_BANDS),
            "iso": "ERCOT",
        }
    }
    n_bins = len(edges) + 1
    for dam_cls, outputs in CLASS_TO_OUTPUT.items():
        if dam_cls == "COAL":
            continue
        df_cls = df[df["model_class"] == dam_cls].copy()
        df_cls["fuel"] = df_cls["gas"].astype(float)
        df_cls["bin"] = netload_bin_index(df_cls["q"].to_numpy(float), edges)
        for out_group, fleet_groups in outputs:
            if out_group not in CONDBINNED_GROUPS:
                continue
            bhr = output_base_hr(fleet_hr, fleet_groups)

            # committed (LSL block) band: Min Gen Cost multiplier, point==1 rows
            cm = df_cls[
                (df_cls["point"] == 1)
                & df_cls["min_gen_cost"].notna()
                & (df_cls["min_gen_cost"] > 0)
                & (df_cls["lsl"] > 0)
            ].copy()
            cm["mult"] = cm["min_gen_cost"].to_numpy(float) / (
                cm["fuel"].to_numpy(float) * bhr
            )
            cm["cap"] = cm["hsl"].astype(float)

            # lower-body incremental band: rel < 0.67, competitive body only
            e = df_cls[
                (df_cls["hsl"] > df_cls["lsl"])
                & (df_cls["curve_price"] > 0)
                & (df_cls["curve_price"] < SCARCITY_THRESH)
            ].copy()
            e["mult"] = e["curve_price"].to_numpy(float) / (
                e["fuel"].to_numpy(float) * bhr
            )
            e["rel"] = ((e["curve_mw"] - e["lsl"]) / (e["hsl"] - e["lsl"])).clip(
                0.0, 1.0
            )
            e["cap"] = e["hsl"].astype(float)
            lo = e[e["rel"] < 0.67]

            binned_committed: list = []
            binned_low: list = []
            for b in range(n_bins):
                cb = cm[cm["bin"] == b]
                pr = (
                    cb.groupby("resource_name")
                    .agg(mult=("mult", "median"), cap=("cap", "median"))
                    .reset_index()
                )
                binned_committed.append(_lowcurve_p50(pr))
                bands: list = []
                lb = lo[lo["bin"] == b]
                for k in range(len(LOWCURVE_REL_BANDS) - 1):
                    kb = lb[
                        (lb["rel"] >= LOWCURVE_REL_BANDS[k])
                        & (lb["rel"] < LOWCURVE_REL_BANDS[k + 1])
                    ]
                    pr = (
                        kb.groupby("resource_name")
                        .agg(mult=("mult", "median"), cap=("cap", "median"))
                        .reset_index()
                    )
                    bands.append(_lowcurve_p50(pr))
                binned_low.append(bands)

            payload[out_group] = {
                "base_hr": round(bhr, 3),
                "binned_committed_p50": binned_committed,
                "binned_low_body": binned_low,
            }
            print(
                f"  {out_group:11s} base_HR {bhr:5.2f}  committed p50/bin "
                f"{binned_committed}  low-body bands/bin {binned_low}"
            )

    out_path = Path(out_json) if out_json else OUT_JSON_LOWCURVE
    out_path.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"\nWrote {out_path}  (groups {sorted(CONDBINNED_GROUPS)})")


# Output groups of the EP-rebasis per-year tables: exactly the classes the
# keeper's offer_curve_overrides carry (the cconly lineage — the CC-only
# variant that avoids the CT<->ST coupling crater). CT/ST mults are calibrated
# values outside the measured band-multiplier family (ERCOT-118 charter scope).
EP_YEARLY_GROUPS: tuple[str, ...] = ("CC_REGULAR", "CC_CHP")

# ERCOT 60-day Resource Type codes per measured DAM class. CC is the
# ERCOT-118/119 lineage (CCGT90 = combined cycle > 90 MW, CCLE90 = <= 90 MW);
# CLLIG ("Coal and Lignite") is the ENTIRE ERCOT solid-fuel fleet — the 19
# resources behind the pooled summary's COAL rows (ERCOT-122).
CC_RESOURCE_TYPES: tuple[str, ...] = ("CCGT90", "CCLE90")
COAL_RESOURCE_TYPES: tuple[str, ...] = ("CLLIG",)

# Output groups of the per-year COAL tables: the two ERCOT solid-fuel offer
# curve keys. Both read the SAME measured CLLIG offer distribution (the
# disclosure carries no lignite/PRB split) and differ only by the delivered
# coal price each is divided by — the pooled derivation's own convention.
COAL_YEARLY_GROUPS: tuple[str, ...] = ("COAL_LIGNITE", "COAL_PRB")

OUT_JSON_COAL_YEARLY = (
    paths.CALIBRATION_DIR / "offer_curve_dam_hrmults_coal_yearly.json"
)


def _load_raw_cc_curve_points(
    resource_types: tuple[str, ...] = CC_RESOURCE_TYPES,
    with_hour_status: bool = False,
) -> pd.DataFrame:
    """Long-form energy-curve points straight from the raw 60-day parquets.

    ``resource_types`` selects the measured DAM class: :data:`CC_RESOURCE_TYPES`
    (the ERCOT-118/119 CC lineage, the default) or :data:`COAL_RESOURCE_TYPES`
    (the ERCOT-122 solid-fuel fleet). The row universe, column set and
    delivery-year filter are otherwise identical, so the coal tables are the
    same measurement as the CC ones on a different fleet.

    Reproduces the ``ercot_dam_offers.parquet`` row universe for the energy
    curve (any Resource Status, every finite curve point) WITHOUT the parsed
    intermediate, which is not rebuildable on this container: the owner-ordered
    2026-07-22 disclosure slimming (``slim_ercot_dam_disclosure.py``) dropped
    the three-part columns (``Min Gen Cost`` / ``Start Up *``) that
    ``parse_ercot_dam_offers.py`` requires. The kept columns (Delivery Date,
    Hour Ending, Resource Type/Name, HSL, LSL, the 10-point QSE curve) fully
    determine the econ_low/econ_high/peak measurements; the committed
    (Min-Gen-Cost) band is NOT derivable from the slimmed raws — see
    :func:`derive_ep_basis_yearly` for the declared consequence. Files are
    globbed across ALL publication windows and filtered by DELIVERY year
    (publication labels lag deliveries by 60 days).
    """
    mw_cols = [f"QSE submitted Curve-MW{k}" for k in range(1, 11)]
    pr_cols = [f"QSE submitted Curve-Price{k}" for k in range(1, 11)]
    cols = ["Delivery Date", "Resource Type", "Resource Name", "HSL", "LSL"]
    # The reach measurement needs a true resource-HOUR key and the commitment
    # status; the CC lineage does not, and the CC load is 9.26 M rows, so the
    # extra columns are opt-in and the default CC path is unchanged.
    extra = ["Hour Ending", "Resource Status"] if with_hour_status else []
    cols = cols + extra
    pat = str(
        paths.RAW_DIR
        / "ercot"
        / "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet"
    )
    import glob as _glob

    frames = []
    for f in sorted(_glob.glob(pat)):
        df = pd.read_parquet(f, columns=cols + mw_cols + pr_cols)
        df = df[df["Resource Type"].isin(resource_types)]
        if df.empty:
            continue
        dt = pd.to_datetime(df["Delivery Date"])
        df = df.assign(_date=dt, year=dt.dt.year)
        df = df[df["year"].isin(YEARS)]
        if df.empty:
            continue
        long = pd.concat(
            [
                df[["_date", "year", "Resource Name", "HSL", "LSL"] + extra].assign(
                    curve_mw=df[mc].to_numpy(float),
                    curve_price=df[pc].to_numpy(float),
                )
                for mc, pc in zip(mw_cols, pr_cols)
            ],
            ignore_index=True,
        )
        long = long[np.isfinite(long["curve_mw"]) & np.isfinite(long["curve_price"])]
        frames.append(
            long.rename(
                columns={
                    "_date": "delivery_date",
                    "Resource Name": "resource_name",
                    "HSL": "hsl",
                    "LSL": "lsl",
                }
            )
        )
    if not frames:
        raise SystemExit("no raw 60-day DAM Gen_Resource parquets found")
    return pd.concat(frames, ignore_index=True)


def derive_ep_basis_yearly(out_json: str | None, body_cap: float) -> None:
    """Derive and write the per-year EP-basis CC band multipliers (ERCOT-118).

    The identical measurement as the adopted ``offer_curve_dam_hrmults_cconly``
    override's energy-curve bands — per-point heat-rate multipliers reduced to
    per-resource medians then capacity-weighted p50s (econ_low rel<=0.33 /
    econ_high rel>=0.67, competitive body < body_cap; peak = mode-B
    top-of-curve incl. near-cap bids) — with exactly two declared changes,
    both rule-23 source-change consequences of the ``ercot_zonal_gas_basis``
    adoption (ERCOT-117 FINDING §4):

    1. **Basis.** The per-point fuel divisor is the EP-anchored delivered-gas
       series dispatch prices gas at: ``HH_daily(delivery_date) +
       ercot_electric_power_gas_basis(year)`` (measured EIA N3045TX3 minus
       measured HH, the level ``apply_ercot_zonal_gas_basis`` re-levels every
       ERCOT gas unit to) — replacing the stale ``HH_daily − 0.50``.
    2. **Pooling.** One table per delivery year (2023/2024/2025) replaces the
       pooled p50s: real CC offers scale sub-proportionally with gas, so a
       pooled multiplier over-prices the dear-gas year (the 2025 leg).

    **The committed band is deliberately ABSENT from the tables** (it stays at
    the run's resolved value): its instrument is the three-part Min Gen Cost,
    whose rows were dropped from the raw parquets by the owner-ordered
    2026-07-22 slimming, the parsed intermediate was never committed, the free
    MIS path's ~2.3-year retention has already lost all 2023 publications, and
    the credentialed archive was owner-declined
    (docs/handoffs/ercot-as-coopt-plan-2026-07.md §WS-E). A per-year committed
    rebasis is therefore not measurable today; re-deriving it is an owner
    decision (archive access, or a 2024/25-only partial intake).

    Each year table also records ``anchor_usd_mmbtu`` — the year's EP-anchored
    delivered annual mean (``mean(HH_monthly) + ep_basis``, i.e. the measured
    EP series annual mean on the model's own HH table) — the identification
    point at which the year's multiplier form and the
    ``gas_offer_net_revenue_margin`` fixed-margin form coincide. The apply
    seam threads it onto the rebased classes as their per-class margin anchor
    so the whole markup decomposition sits on ONE basis (the charter's
    anchor-consistency audit).
    """
    from market_sim.data.fuel._shared import _pkg_ns
    from market_sim.data.fuel.basis.ercot import ercot_electric_power_gas_basis

    fleet_hr = class_base_hr()
    ep_basis = {y: ercot_electric_power_gas_basis(y) for y in YEARS}
    missing = [y for y, b in ep_basis.items() if b is None]
    if missing:
        raise SystemExit(
            f"EP electric-power gas basis unavailable for {missing} — the "
            "EP-rebasis artifact cannot be derived without the measured series"
        )
    df = _load_raw_cc_curve_points()
    # EP-anchored delivered fuel per point: ffill'd daily HH at the delivery
    # date plus the year's measured EP level (the exact analogue of
    # load_offers' HH_daily - 0.50 construction, basis swapped).
    hh_daily = pd.read_csv(HENRY_HUB, parse_dates=["date"]).rename(
        columns={"price_usd_mmbtu": "hh"}
    )
    hh_daily = hh_daily.set_index("date")["hh"].sort_index()
    daily = hh_daily.reindex(
        pd.date_range(hh_daily.index.min(), hh_daily.index.max())
    ).ffill()
    df["fuel"] = df["delivery_date"].map(daily) + df["year"].map(ep_basis)
    df = df[df["fuel"] > 0]
    hh = _pkg_ns()._henry_hub_monthly(None)
    print(
        f"Loaded {len(df):,} CC curve-point rows "
        f"({df['delivery_date'].min().date()} -> "
        f"{df['delivery_date'].max().date()}); per-year EP basis vs HH: "
        + ", ".join(f"{y}: {ep_basis[y]:+.4f}" for y in YEARS)
    )

    payload: dict = {
        "_provenance": {
            "source": "ERCOT 60-Day DAM Disclosure Gen Resource Data raw "
            "parquets (slimmed 2026-07-22), delivery years 2023-2025, CC "
            "(CCGT90/CCLE90) energy-curve points, any Resource Status — the "
            "ercot_dam_offers.parquet row universe for these bands",
            "method": "per-point mult = curve_price / (fuel x base_HR); "
            "econ_low rel<=0.33 / econ_high rel>=0.67 competitive body "
            "(< $1000), per-resource median then capacity(HSL)-weighted p50; "
            "peak = mode-B per-resource top-of-curve incl. near-cap bids — "
            "the cconly derivation per delivery YEAR",
            "basis": "HH_daily(delivery_date) + "
            "ercot_electric_power_gas_basis(year) (EIA N3045TX3 measured TX "
            "electric-power delivered level — the series "
            "apply_ercot_zonal_gas_basis re-levels dispatch gas to), "
            "replacing HH_daily - 0.50",
            "rule23_citation": "ercot_zonal_gas_basis adoption changed the "
            "dispatch delivered-gas series (+0.50/+0.41/+0.04 $/MMBtu over "
            "HH-0.50 in 2023/24/25) under the band-multiplier artifacts; "
            "derivation-consistency re-derive per ERCOT-117 FINDING §4.3 "
            "(FINDING-ercot117-gas-basis-ranking-2026-07-26.md), not a "
            "residual chase",
            "committed_band": "ABSENT by data destruction, not by choice: "
            "Min Gen Cost was dropped by the owner-ordered 2026-07-22 raw "
            "slimming (slim_ercot_dam_disclosure.py), the parsed "
            "ercot_dam_offers.parquet was never committed, the free MIS "
            "path retains only ~2.3 years (2023 publications gone), and the "
            "credentialed archive was owner-declined. The committed band "
            "keeps the run's resolved (pooled HH-0.50-derived) value.",
            "peak_mode": "B",
            "ep_basis_vs_hh": {str(y): round(float(ep_basis[y]), 4) for y in YEARS},
            "iso": "ERCOT",
        }
    }
    for year in YEARS:
        hh_year = [hh[(year, m)] for m in range(1, 13) if (year, m) in hh]
        anchor = float(np.mean(hh_year)) + float(ep_basis[year])
        table: dict = {"anchor_usd_mmbtu": round(anchor, 4)}
        d_year = df[df["year"] == year]
        for out_group in EP_YEARLY_GROUPS:
            bhr = output_base_hr(fleet_hr, (out_group,))
            e = d_year[
                (d_year["hsl"] > d_year["lsl"]) & (d_year["curve_price"] > 0)
            ].copy()
            e["mult"] = e["curve_price"].to_numpy(float) / (
                e["fuel"].to_numpy(float) * bhr
            )
            e["rel"] = ((e["curve_mw"] - e["lsl"]) / (e["hsl"] - e["lsl"])).clip(
                0.0, 1.0
            )
            e["cap"] = e["hsl"].astype(float)
            body = e[e["curve_price"] < body_cap]
            lo_pr = (
                body[body["rel"] <= 0.33]
                .groupby("resource_name")
                .agg(econ_low=("mult", "median"), cap=("cap", "median"))
                .reset_index()
            )
            hi_pr = (
                body[body["rel"] >= 0.67]
                .groupby("resource_name")
                .agg(econ_high=("mult", "median"), cap=("cap", "median"))
                .reset_index()
            )
            topf = (
                e.groupby("resource_name")
                .agg(peak=("mult", "max"), cap=("cap", "median"))
                .reset_index()
            )
            econ_low = _capwt_band(lo_pr, "econ_low")
            econ_high = _capwt_band(hi_pr, "econ_high")
            peak_full = _capwt_band(topf.rename(columns={"peak": "pk"}), "pk")
            table[out_group] = {
                "econ_low": econ_low["p50"],
                "econ_high": econ_high["p50"],
                "peak": peak_full["p50"],  # mode B, the cconly lineage
            }
            table[f"_{out_group}_detail"] = {
                "base_hr": round(bhr, 3),
                "n_resources": int(e["resource_name"].nunique()),
                "n_points": int(len(e)),
                "econ_low": econ_low,
                "econ_high": econ_high,
                "peak_full": peak_full,
            }
            print(
                f"  {year} {out_group:11s} base_HR {bhr:5.2f}  "
                f"econ_low {econ_low['p50']:.3f}  "
                f"econ_high {econ_high['p50']:.3f}  "
                f"peak(B) {peak_full['p50']:.3f}  "
                f"anchor {anchor:.4f}"
            )
        payload[str(year)] = table

    out_path = Path(out_json) if out_json else OUT_JSON_EP_YEARLY
    out_path.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"\nWrote {out_path}  (groups {sorted(EP_YEARLY_GROUPS)}, years {YEARS})")


def _band_capacity_coverage(band_rows: pd.DataFrame, fleet_rows: pd.DataFrame) -> float:
    """Share of fleet HSL carrying at least one submitted point in a band.

    The ERCOT-122 selection-bias receipt. A band whose coverage is well below
    1.0 is measured on a *subsample* of the fleet, so its capacity-weighted p50
    describes those resources' offer behaviour and NOT the class's — the model
    would apply it to 100 % of the class. Reported per band, per year, so an
    adoption decision can see which bands are fleet-representative.
    """
    tot = fleet_rows.groupby("resource_name")["hsl"].max().sum()
    if not np.isfinite(tot) or tot <= 0:
        return float("nan")
    cov = band_rows.groupby("resource_name")["hsl"].max().sum()
    return float(cov / tot)


def measure_offered_headroom_share(
    resource_types: tuple[str, ...],
) -> dict[int, float]:
    """Per-year share of ONLINE operating headroom carrying an incremental offer.

    The ERCOT-122 *reach* measurement, read straight from the raws rather than
    from :func:`_load_raw_cc_curve_points` because it must count the
    resource-hours that submit **no curve point at all** as zero offered — that
    long-form loader drops them, which would bias the share upward (0.37 rather
    than 0.17 on coal). Over half of ERCOT's online coal resource-hours are in
    exactly that state, so the distinction is the measurement.

    Aggregated as ``sum(reach - LSL) / sum(HSL - LSL)`` over online
    (``Resource Status`` starting ``ON``) resource-hours: a capacity-weighted
    fleet share, not a per-unit mean. An OFF/OUT unit has no incremental offer
    to make, so including it would measure commitment, not offer behaviour.

    Measured 2023/2024/2025: **coal 0.168 / 0.184 / 0.161** against
    **CC 0.622 / 0.594 / 0.677** — the coal fleet exposes roughly a quarter as
    much of its ramp range to the DAM energy merit order as the CC fleet does.
    """
    mw_cols = [f"QSE submitted Curve-MW{k}" for k in range(1, 11)]
    cols = [
        "Delivery Date",
        "Hour Ending",
        "Resource Type",
        "Resource Name",
        "HSL",
        "LSL",
        "Resource Status",
    ]
    pat = str(
        paths.RAW_DIR
        / "ercot"
        / "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet"
    )
    import glob as _glob

    num = {y: 0.0 for y in YEARS}
    den = {y: 0.0 for y in YEARS}
    for f in sorted(_glob.glob(pat)):
        d = pd.read_parquet(f, columns=cols + mw_cols)
        d = d[d["Resource Type"].isin(resource_types)]
        if d.empty:
            continue
        year = pd.to_datetime(d["Delivery Date"]).dt.year
        d = d.assign(year=year)
        d = d[d["year"].isin(YEARS)]
        d = d[d["Resource Status"].astype(str).str.startswith("ON")]
        d = d[(d["HSL"] > d["LSL"]) & (d["HSL"] > 0)]
        if d.empty:
            continue
        # No finite curve point at all -> the unit offered nothing above LSL.
        reach = d[mw_cols].max(axis=1).fillna(d["LSL"])
        head = (d["HSL"] - d["LSL"]).clip(lower=0.0)
        inc = (reach - d["LSL"]).clip(lower=0.0)
        for y in YEARS:
            m = (d["year"] == y).to_numpy()
            num[y] += float(inc[m].sum())
            den[y] += float(head[m].sum())
    return {y: (num[y] / den[y]) if den[y] > 0 else float("nan") for y in YEARS}


def _typical_top_of_curve(
    fleet_rows: pd.DataFrame, fuel: float, base_hr: float
) -> dict[str, float]:
    """Capacity-weighted p50 of each resource's TYPICAL daily top-of-curve.

    The stable companion to the lineage's mode-B ``peak`` (which is each
    resource's annual *maximum* top-of-curve and swings 46 -> 80 -> 61 $/MWh
    across 2023-2025 on coal, the same per-year instability ERCOT-118 §4.2
    found on CC). Here each resource's top-of-curve is reduced to its median
    over delivery days FIRST, so the statistic describes what the fleet posts
    on an ordinary day rather than its once-a-year extreme.

    This is the quantity ``FINDING-ercot112 §6`` reported as "the real fleet's
    ~$21 top submitted DAM coal offer", and it reproduces it to the cent.
    """
    d = fleet_rows[fleet_rows["curve_price"] > 0]
    if d.empty:
        return {"p25": float("nan"), "p50": float("nan"), "p75": float("nan")}
    daily_top = d.groupby(["resource_name", "delivery_date"])["curve_price"].max()
    per_res = daily_top.groupby("resource_name").median().rename("typ")
    cap = d.groupby("resource_name")["hsl"].max().rename("cap")
    j = pd.concat([per_res, cap], axis=1).dropna().reset_index()
    j["typ"] = j["typ"] / (fuel * base_hr)
    return _capwt_band(j, "typ")


def derive_coal_yearly(out_json: str | None, body_cap: float) -> None:
    """Derive and write the per-year measured COAL band multipliers (ERCOT-122).

    The ERCOT-118 :func:`derive_ep_basis_yearly` measurement, applied to the
    ``CLLIG`` (Coal and Lignite) fleet, with the one basis change coal requires:
    the per-point divisor is the **delivered coal price the model dispatches
    on** (``COAL_PRICE_LIGNITE_BY_YEAR`` / ``COAL_PRICE_PRB_BY_YEAR`` via
    :func:`coal_fuel_price`), never Henry Hub. The EP gas basis is a *gas*
    correction and has no coal analogue; what carries over from ERCOT-118 is the
    principle — divide by the same fuel series the model later multiplies —
    not the gas series itself.

    Both output groups read the SAME measured distribution (the disclosure
    carries no lignite/PRB split) and differ only by that divisor, exactly as
    the pooled ``ercot_dam_offer_hrmult_summary.csv`` COAL rows do.

    **Two bands are NOT fleet-representative and must not be adopted blind**
    (both recorded as ``coverage`` in each year's detail block):

    * ``committed`` — absent entirely, same data destruction as ERCOT-118: the
      Min-Gen-Cost instrument was dropped by the owner-ordered 2026-07-22 raw
      slimming, the parsed intermediate was never committed, the free MIS path
      has lost all 2023 publications, and the credentialed archive was
      owner-declined.
    * ``econ_high`` — measured on only **21-47 % of fleet capacity** (8 of 18
      resources in 2023; 3 of 16 and 3 of 12 in 2024/2025), because most ERCOT
      coal resources submit no curve point above ``rel = 0.67`` at all. Its
      capacity-weighted p50 is therefore the offer behaviour of the few
      resources that DO reach that high — the expensive ones — and it is the
      quantity behind the pooled summary's ``COAL_LIGNITE econ_high = 2.856``.
      ``econ_low`` and ``peak`` carry 100 % coverage and are the
      fleet-representative pair.

    Each year's ``_reach`` field records the share of operating headroom the
    submitted curve covers at all (coal 0.16-0.18 vs CC 0.59-0.68) — the
    measurement that says the coal fleet offers only a thin incremental slice
    into DAM energy, and the reason a band *level* rebasis alone cannot express
    the class's real offer behaviour.
    """
    fleet_hr = class_base_hr()
    df = _load_raw_cc_curve_points(COAL_RESOURCE_TYPES)
    reach_by_year = measure_offered_headroom_share(COAL_RESOURCE_TYPES)
    cc_reach_by_year = measure_offered_headroom_share(CC_RESOURCE_TYPES)
    print(
        f"Loaded {len(df):,} COAL curve-point rows "
        f"({df['delivery_date'].min().date()} -> "
        f"{df['delivery_date'].max().date()}); "
        f"{df['resource_name'].nunique()} resources"
    )

    payload: dict = {
        "_provenance": {
            "source": "ERCOT 60-Day DAM Disclosure Gen Resource Data raw "
            "parquets (slimmed 2026-07-22), delivery years 2023-2025, CLLIG "
            "(Coal and Lignite) energy-curve points, any Resource Status",
            "method": "per-point mult = curve_price / (delivered_coal x "
            "base_HR(COAL)); econ_low rel<=0.33 / econ_high rel>=0.67 "
            "competitive body (< body_cap), per-resource median then "
            "capacity(HSL)-weighted p50; peak = mode-B per-resource "
            "top-of-curve incl. near-cap bids — the ERCOT-118 derivation "
            "per delivery YEAR on the coal fleet",
            "basis": "delivered coal $/MMBtu the model dispatches on "
            "(COAL_PRICE_LIGNITE_BY_YEAR / COAL_PRICE_PRB_BY_YEAR), NOT Henry "
            "Hub: the EP gas-basis correction is gas-specific and has no coal "
            "analogue; what carries over is the divide-by-what-you-multiply "
            "principle (ERCOT-118 FINDING §1)",
            "rule23_citation": "derived from the raw disclosure on the "
            "ERCOT-122 charter's measurement question (reconciling "
            "FINDING-ercot112 §6's ~$21 top submitted coal offer against the "
            "pooled summary's COAL_LIGNITE econ_high 2.856); no residual "
            "entered the derivation",
            "committed_band": "ABSENT by data destruction, not by choice — "
            "identical cause to the ERCOT-118 CC tables: Min Gen Cost was "
            "dropped by the owner-ordered 2026-07-22 raw slimming, the parsed "
            "ercot_dam_offers.parquet was never committed, the free MIS path "
            "retains only ~2.3 years, and the credentialed archive was "
            "owner-declined.",
            "econ_high_band": "DERIVED BUT NOT FLEET-REPRESENTATIVE: see each "
            "year's detail 'coverage' — only 21-47 % of fleet capacity submits "
            "any point above rel=0.67, so this p50 describes that subsample, "
            "not the class. econ_low and peak carry 100 % coverage.",
            "peak_mode": "B",
            "iso": "ERCOT",
        }
    }

    for year in YEARS:
        d_year = df[df["year"] == year]
        table: dict = {}
        e_base = d_year[
            (d_year["hsl"] > d_year["lsl"]) & (d_year["curve_price"] > 0)
        ].copy()
        e_base["rel"] = (
            (e_base["curve_mw"] - e_base["lsl"]) / (e_base["hsl"] - e_base["lsl"])
        ).clip(0.0, 1.0)
        e_base["cap"] = e_base["hsl"].astype(float)
        table["_reach"] = {
            "offered_share_of_headroom": round(float(reach_by_year[year]), 4),
            "cc_offered_share_of_headroom": round(float(cc_reach_by_year[year]), 4),
            "n_resources": int(d_year["resource_name"].nunique()),
        }
        for out_group in COAL_YEARLY_GROUPS:
            bhr = output_base_hr(fleet_hr, ("COAL",))
            fuel = coal_fuel_price(out_group)[year]
            e = e_base.copy()
            e["mult"] = e["curve_price"].to_numpy(float) / (fuel * bhr)
            body = e[e["curve_price"] < body_cap]
            lo_rows = body[body["rel"] <= 0.33]
            hi_rows = body[body["rel"] >= 0.67]
            lo_pr = (
                lo_rows.groupby("resource_name")
                .agg(econ_low=("mult", "median"), cap=("cap", "median"))
                .reset_index()
            )
            hi_pr = (
                hi_rows.groupby("resource_name")
                .agg(econ_high=("mult", "median"), cap=("cap", "median"))
                .reset_index()
            )
            topf = (
                e.groupby("resource_name")
                .agg(pk=("mult", "max"), cap=("cap", "median"))
                .reset_index()
            )
            econ_low = _capwt_band(lo_pr, "econ_low")
            econ_high = _capwt_band(hi_pr, "econ_high")
            peak_full = _capwt_band(topf, "pk")
            peak_typ = _typical_top_of_curve(e, float(fuel), bhr)
            table[out_group] = {
                "econ_low": econ_low["p50"],
                "econ_high": econ_high["p50"],
                "peak": peak_full["p50"],
                "peak_typical": peak_typ["p50"],
            }
            table[f"_{out_group}_detail"] = {
                "base_hr": round(bhr, 3),
                "delivered_fuel_usd_mmbtu": round(float(fuel), 4),
                "n_resources": int(e["resource_name"].nunique()),
                "n_points": int(len(e)),
                "coverage": {
                    "econ_low": round(_band_capacity_coverage(lo_rows, e), 4),
                    "econ_high": round(_band_capacity_coverage(hi_rows, e), 4),
                    "peak": 1.0,
                    "peak_typical": 1.0,
                },
                "usd_mwh_p50": {
                    "econ_low": round(econ_low["p50"] * fuel * bhr, 2),
                    "econ_high": round(econ_high["p50"] * fuel * bhr, 2),
                    "peak": round(peak_full["p50"] * fuel * bhr, 2),
                    "peak_typical": round(peak_typ["p50"] * fuel * bhr, 2),
                },
                "econ_low": econ_low,
                "econ_high": econ_high,
                "peak_full": peak_full,
                "peak_typical": peak_typ,
            }
            det = table[f"_{out_group}_detail"]
            print(
                f"  {year} {out_group:12s} base_HR {bhr:5.2f} fuel {fuel:5.3f}  "
                f"econ_low {econ_low['p50']:.3f} (${det['usd_mwh_p50']['econ_low']:.2f}, "
                f"cov {det['coverage']['econ_low']:.2f})  "
                f"econ_high {econ_high['p50']:.3f} (${det['usd_mwh_p50']['econ_high']:.2f}, "
                f"cov {det['coverage']['econ_high']:.2f})  "
                f"peak {peak_full['p50']:.3f} (${det['usd_mwh_p50']['peak']:.2f})  "
                f"peak_typ {peak_typ['p50']:.3f} "
                f"(${det['usd_mwh_p50']['peak_typical']:.2f})"
            )
        print(
            f"  {year} reach: submitted curve covers "
            f"{table['_reach']['offered_share_of_headroom']:.3f} of coal "
            f"operating headroom (CC control "
            f"{table['_reach']['cc_offered_share_of_headroom']:.3f})"
        )
        payload[str(year)] = table

    out_path = Path(out_json) if out_json else OUT_JSON_COAL_YEARLY
    out_path.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"\nWrote {out_path}  (groups {sorted(COAL_YEARLY_GROUPS)}, years {YEARS})")


if __name__ == "__main__":
    main()
