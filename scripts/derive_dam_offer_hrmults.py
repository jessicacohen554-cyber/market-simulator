"""Derive MEASURED offer-curve heat-rate multipliers from the ERCOT 60-Day DAM.

This is the gated, *measured* successor to the analysis-only
``scripts/analyze_dam_offer_multipliers.py``. Where the model today prices each
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

    python scripts/derive_dam_offer_hrmults.py                       # report only
    python scripts/derive_dam_offer_hrmults.py --peak-mode A --write-json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
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
    args = ap.parse_args()

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


if __name__ == "__main__":
    main()
