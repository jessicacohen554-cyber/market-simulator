"""ERCOT-135 Phase 1 — the coal-vs-gas merit-order instruments, NO LP.

The ERCOT-134 A/B established the target this probe measures against: on the
un-pinned fleet (``ercot_thermal_dam_availability_coal=true``) ERCOT coal runs
**+6 to +18 pp hotter than the real fleet at matched RT price in EVERY band of
EVERY year** (G1 1/21), over-running +6.5/+9.6/+11.4 TWh, displaced ~1:1 from
gas.  The bias is **uniform across bands**, so a single-band level lever is
refuted in advance — and the offer LEVEL rebasis is separately a registered
refutation (ERCOT-132 leg B, CLOSED).

This module measures the three instruments the ERCOT-134 §10 charter names, all
**without building an LP**:

* **A — the coal offer surface at the LP seam.**  The model's own bid array is
  captured at the exact point the LP consumes it (after
  :func:`market_sim.data.fleet.legacy_bins.apply_coal_tranches` applies the
  take-or-pay discount), per coal tranche, per plant, per year.  This is the
  model side of the ERCOT-112 §6 lead — *"the model's full-passthrough coal
  SRMC tops near $28/MWh"* — reproduced from the code rather than quoted.
* **B — the measured DAM coal offer curve.**  The real fleet's submitted
  incremental energy offer for ``Resource Type == CLLIG`` in the 60-Day DAM
  disclosure, per plant, per year.  This is the other half of ERCOT-112 §6 —
  *"the real fleet's top submitted DAM coal offer is ~$21"*.
* **C — the F923 delivered-coal-price reconciliation.**  ERCOT-112 §6 called
  this *"an F923 delivered-fuel-price question, its own charter with
  receipts"*.  The keeper runs ``coal_plant_monthly_pricing=True``, so the
  model's delivered coal price **is** the F923 receipt; this section proves
  that identity per plant-month rather than assuming it, which is what
  localises the A-vs-B gap to the offer *construction* instead of the fuel
  *price*.
* **D — the take-or-pay / committed share.**  The measured committed-band
  fraction on the 60-Day DAM CLLIG corpus, reproducing ``ERCOT-127`` section E's
  construction **verbatim** (imported, not re-implemented), against the model's
  own ``coal_tranche_*_frac`` split.
* **E — the plant-grain water-fill landing.**  ``FINDING-ercot134`` §2's
  prediction-4 partial: Martin Lake lands at **1.45x** its own COP declaration
  under the measured envelope because the redistribution pins the *class-hour
  mean* and water-fills per plant.  This decomposes each plant's landing
  against its declaration, on the ARM's own fleet-array build.

**Rule 13 [R-MEASURED] / rule 1 [R-STRUCT] scope.**  Nothing here is tuned and
nothing here is a mechanism.  Every number is either the model's own committed
construction read back, or a measured corpus read on an already-accepted
convention.  No ``ScenarioConfig`` field is written, no keeper file is touched,
no year outside {2023, 2024, 2025} is read (rule 22 [R-HOLDOUT]).

Usage::

    python scripts/probes/ercot135_coal_merit_order.py              # A-E
    python scripts/probes/ercot135_coal_merit_order.py --sections AB
    python scripts/probes/ercot135_coal_merit_order.py --year 2025

Output: a JSON blob at ``results/calibration/ercot135_coal_merit_order.json``
plus a human-readable table on stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (str(_REPO / "src"), str(_REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.config import paths  # noqa: E402
from scripts.probes.ercot127_coal_dispatch_band import (  # noqa: E402
    COAL_PLANTS,
    SITE_TO_PLANT,
    dam_declared,
    hour_index,
    section_e_coal_min_load,
)

YEARS: tuple[int, ...] = (2023, 2024, 2025)

#: The ERCOT keeper bundle whose recipe every capture in this module replays.
#: ``2026-07-28-ercot116-regate-base``, promoted 2026-07-28 (ERCOT-134).
KEEPER_BUNDLE = _REPO / "results" / "calibration" / "ercot116_regate_base"

OUT_JSON = _REPO / "results" / "calibration" / "ercot135_coal_merit_order.json"

#: Scratch run dir for the abort-early replays (never written -- every capture
#: raises before ``solve_and_persist`` reaches its first write).
SCRATCH = _REPO / "results" / "calibration" / "_ercot135_scratch"

#: EIA-923 fuel_group label for coal receipts.
F923_COAL = "Coal"

#: A tranche counts as carrying capacity above this level (MW).
CAP_EPS = 1e-6


class _Captured(Exception):
    """Raised to abort a replay once the seam of interest has been recorded."""


# --------------------------------------------------------------------------
# shared: replay the keeper recipe far enough to reach a seam, then abort
# --------------------------------------------------------------------------
def _keeper_kwargs(year: int, overrides: dict | None = None) -> dict:
    """Return ``solve_and_persist`` kwargs for the keeper recipe at ``year``.

    ``overrides`` are merged into the recipe's ``prb_overrides`` dict — the
    channel the ERCOT-134 ARM itself used.  Diffing the two committed bundles'
    ``meta.json`` shows the ARM's ONLY delta is
    ``coal_prb_sigmoid_overrides["ercot_thermal_dam_availability_coal"] =
    True``; it is not a top-level ``solve_and_persist`` parameter, so passing it
    as one raises ``TypeError``.  Routing through the same channel is what makes
    the section-E capture the ARM's own build rather than a lookalike.
    """
    from scripts import replay_keeper as rk
    from scripts import run_calibration_full as rcf

    meta = json.loads((KEEPER_BUNDLE / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = SCRATCH / str(year)
    if overrides:
        prb = dict(kwargs.get("prb_overrides") or {})
        prb.update(overrides)
        kwargs["prb_overrides"] = prb
    return kwargs


def capture_coal_offer_surface(year: int, overrides: dict | None = None) -> dict:
    """Capture the model's COAL bid array at the exact seam the LP consumes.

    Patches ``apply_coal_tranches`` — the LAST thing that touches a coal row's
    bid before the gas-side offer reforms run — calls the real implementation so
    the take-or-pay discount is applied, records every coal row, then aborts
    before any LP matrix is built.

    **The patch target is the copy imported into** ``scripts.run_calibration``
    (line 63, called from its own ``run_year`` at line 3168), NOT
    ``market_sim.runner``.  That module holds a second, dead copy of the same
    call; patching it lets the whole year solve — the identical trap
    ``ercot130_capoff_phase1.capture_availability`` records for the fleet-array
    constructor.  The call site sits ahead of the cache guard and runs
    unconditionally, so this seam is reached even on a cached year.

    Returns a dict of parallel arrays over the coal rows only: ``plant_code``,
    ``unit_id``, ``pmax``, ``heat_rate``, ``vom``, plus the hour-mean of the
    row's delivered fuel price (``fuel_price``, $/MMBtu), its resolved
    passthrough (``fuel_frac``) and its final bid (``bid``, $/MWh).
    """
    from scripts import run_calibration as rc
    from scripts import run_calibration_full as rcf

    real = rc.apply_coal_tranches
    box: dict = {}

    def _spy(mc, generators, fleet_arrays, fuel_fracs, fuel_prices, config=None):
        # ERCOT-137 added a trailing ``config`` parameter to the live seam
        # (the coal net-revenue margin gate); pass it through so the capture
        # stays replayable at HEAD and records the post-margin bid when armed.
        real(mc, generators, fleet_arrays, fuel_fracs, fuel_prices, config)
        is_coal = np.array(
            [str(getattr(g, "fuel_type", "")) == "coal" for g in generators],
            dtype=bool,
        )
        rows = np.flatnonzero(is_coal)
        fp = np.asarray(fuel_prices, dtype=float)
        # fuel_fracs[g] is a scalar OR an (T,) gas-keyed series (the PRB /
        # lignite passthrough sigmoids) -- reduce to its hour-mean so a row is
        # one number either way.
        frac = np.array(
            [float(np.mean(np.asarray(fuel_fracs[g], dtype=float))) for g in rows]
        )
        box.update(
            plant_code=np.array(
                [int(getattr(generators[g], "plant_code", 0) or 0) for g in rows]
            ),
            unit_id=[str(fleet_arrays.unit_ids[g]) for g in rows],
            pmax=np.asarray(fleet_arrays.pmax, dtype=float)[rows],
            heat_rate=np.asarray(fleet_arrays.heat_rate, dtype=float)[rows],
            vom=np.asarray(fleet_arrays.vom, dtype=float)[rows],
            fuel_price=fp[rows].mean(axis=1),
            fuel_frac=frac,
            bid=np.asarray(mc, dtype=float)[rows].mean(axis=1),
            bid_p95=np.percentile(np.asarray(mc, dtype=float)[rows], 95, axis=1),
        )
        raise _Captured

    rc.apply_coal_tranches = _spy
    try:
        rcf.solve_and_persist(**_keeper_kwargs(year, overrides))
    except _Captured:
        pass
    finally:
        rc.apply_coal_tranches = real
    if not box:
        raise RuntimeError(f"coal offer seam never reached for {year}")
    return box


def capture_coal_availability(year: int, overrides: dict | None = None) -> dict:
    """Capture per-plant hourly ``availability x pmax`` (MW) for the coal rows.

    Same replay, earlier seam (the fleet-array constructor).  With
    ``overrides={"ercot_thermal_dam_availability_coal": True}`` this is the ARM's
    plant-grain water-fill landing — section E's input — obtained without a
    solve, because the redistribution is a deterministic function of the
    measured class envelope and the fleet, computed before the LP exists.
    """
    from scripts import run_calibration as rc
    from scripts import run_calibration_full as rcf

    real = rc.generators_to_fleet_arrays
    box: dict = {}

    def _spy(generators, zone_names, **kw):
        fa = real(generators, zone_names, **kw)
        codes = np.array(
            [int(getattr(g, "plant_code", 0) or 0) for g in generators], dtype=int
        )
        is_coal = np.array(
            [str(getattr(g, "fuel_type", "")) == "coal" for g in generators], dtype=bool
        )
        avail = np.asarray(fa.availability, dtype=np.float32)
        pmax = np.asarray(fa.pmax, dtype=np.float64)
        out: dict[int, np.ndarray] = {}
        caps: dict[int, float] = {}
        for code in sorted({int(c) for c in codes[is_coal] if c}):
            rows = np.flatnonzero(is_coal & (codes == code))
            out[code] = (avail[rows] * pmax[rows, None]).sum(axis=0).astype(float)
            caps[code] = float(pmax[rows].sum())
        box.update(avail_mw=out, pmax=caps)
        raise _Captured

    rc.generators_to_fleet_arrays = _spy
    try:
        rcf.solve_and_persist(**_keeper_kwargs(year, overrides))
    except _Captured:
        pass
    finally:
        rc.generators_to_fleet_arrays = real
    if not box:
        raise RuntimeError(f"fleet-array seam never reached for {year}")
    return box


# --------------------------------------------------------------------------
# A -- the model's coal offer surface, per plant, from the LP seam
# --------------------------------------------------------------------------
def section_a_model_offer(year: int) -> dict:
    """A -- the model's COAL bid surface, per plant and fleet-wide ($/MWh).

    Reports, per plant: capacity, the capacity-weighted mean bid across its
    tranches, and the **top** tranche bid (the number ERCOT-112 §6 quotes as
    "the model's full-passthrough coal SRMC tops near $28/MWh").  The top is
    reported both on the hour-mean bid and on the hourly p95, because the
    passthrough sigmoids are gas-keyed and so the top moves within the year.
    """
    cap = capture_coal_offer_surface(year)
    codes = cap["plant_code"]
    rows = []
    for code in sorted(COAL_PLANTS):
        sel = codes == code
        if not sel.any():
            continue
        pmax, bid = cap["pmax"][sel], cap["bid"][sel]
        keep = pmax > CAP_EPS
        if not keep.any():
            continue
        pmax, bid = pmax[keep], bid[keep]
        rows.append(
            {
                "plant": COAL_PLANTS[code],
                "plant_code": code,
                "pmax_mw": round(float(pmax.sum()), 1),
                "n_tranches": int(keep.sum()),
                "bid_capwtd_mean": round(float((bid * pmax).sum() / pmax.sum()), 2),
                "bid_top_tranche": round(float(bid.max()), 2),
                # The BOTTOM of the model's offer curve and its width. The real
                # fleet's submitted DAM coal curve is flat (bot == top) at most
                # plants, so this spread is the direct structural comparison:
                # a steep model curve over-runs at every price above its own
                # bottom, which is the band-uniform signature FINDING-ercot134
                # §2 measured (G1 1/21, +6 to +18 pp in EVERY band).
                "bid_bot_tranche": round(float(bid.min()), 2),
                "bid_spread": round(float(bid.max() - bid.min()), 2),
                "bid_top_tranche_p95hr": round(
                    float(cap["bid_p95"][sel][keep].max()), 2
                ),
                "heat_rate_capwtd": round(
                    float(
                        (cap["heat_rate"][sel][keep] * pmax).sum() / pmax.sum()
                    ),
                    3,
                ),
                "fuel_price_mmbtu": round(
                    float((cap["fuel_price"][sel][keep] * pmax).sum() / pmax.sum()), 3
                ),
                "passthrough_capwtd": round(
                    float((cap["fuel_frac"][sel][keep] * pmax).sum() / pmax.sum()), 4
                ),
            }
        )
    allcap = cap["pmax"] > CAP_EPS
    w, bid = cap["pmax"][allcap], cap["bid"][allcap]
    order = np.argsort(bid)
    bs, ws = bid[order], w[order]
    cw = ws.cumsum() / ws.sum()
    return {
        "per_plant": rows,
        "fleet": {
            "pmax_mw": round(float(w.sum()), 1),
            "bid_capwtd_mean": round(float((bid * w).sum() / w.sum()), 2),
            "bid_top": round(float(bid.max()), 2),
            "bid_top_p95hr": round(float(cap["bid_p95"][allcap].max()), 2),
            # The model's own coal supply curve, as capacity-weighted deciles of
            # its bid. This is the object the measured DAM offer is compared
            # against: the real fleet's is nearly a step (one price), the
            # model's runs from VOM-only to full passthrough.
            "bid_deciles": {
                f"p{q}": round(float(bs[np.searchsorted(cw, q / 100.0)]), 2)
                for q in (10, 25, 50, 75, 90)
            },
        },
    }


def _cheap_share(model: dict, measured: dict) -> dict:
    """Share of model coal capacity bid BELOW the measured DAM offer level.

    The single most direct statement of the defect: capacity the model offers
    at a price no real ERCOT coal resource ever submits clears ahead of gas in
    every hour above that price, which is the band-uniform over-run.  The
    reference level is the measured capacity-weighted p50 top offer for the
    year (section B's fleet statistic).
    """
    ref = measured.get("fleet", {}).get("top_offer_capwtd_p50")
    if ref is None:
        return {}
    cap = below = 0.0
    for r in model["per_plant"]:
        cap += r["pmax_mw"]
        # Tranche-resolved share is not reconstructable from the plant summary,
        # so this uses the plant's own bid range: fully-below and fully-above
        # plants are exact, straddling plants are apportioned linearly across
        # their bid spread (stated, not hidden).
        lo, hi = r["bid_bot_tranche"], r["bid_top_tranche"]
        if hi <= ref:
            below += r["pmax_mw"]
        elif lo < ref < hi:
            below += r["pmax_mw"] * (ref - lo) / (hi - lo)
    return {
        "reference_dam_offer": ref,
        "capacity_below_mw": round(below, 1),
        "capacity_total_mw": round(cap, 1),
        "share_below": round(below / cap, 4) if cap else None,
    }


# --------------------------------------------------------------------------
# B -- the measured DAM coal offer curve (60-Day DAM, CLLIG)
# --------------------------------------------------------------------------
def _dam_coal_offers(year: int) -> pd.DataFrame:
    """Return per-(resource, hour) submitted DAM coal offer summary for ``year``.

    Same corpus, resource filter and holdout guard as ``ERCOT-127`` section E
    (``Resource Type == CLLIG``, rule 22 [R-HOLDOUT] year filter applied before
    any aggregate).  Adds the submitted incremental energy curve: for each
    resource-hour the curve is the (MW_k, Price_k) pairs, so the **top
    submitted offer** is the price at the highest offered MW point.
    """
    mw_cols = [f"QSE submitted Curve-MW{k}" for k in range(1, 11)]
    px_cols = [f"QSE submitted Curve-Price{k}" for k in range(1, 11)]
    files = sorted(
        (paths.RAW_DIR / "ercot").glob(
            "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_20*.parquet"
        )
    )
    files = [f for f in files if "2026" not in f.name]
    parts: list[pd.DataFrame] = []
    for f in files:
        df = pd.read_parquet(
            f,
            columns=["Delivery Date", "Hour Ending", "Resource Name", "Resource Type",
                     "HSL", "LSL"] + mw_cols + px_cols,
        )
        df = df[df["Resource Type"] == "CLLIG"]
        if df.empty:
            continue
        ts = pd.to_datetime(df["Delivery Date"]) + pd.to_timedelta(
            df["Hour Ending"].astype(str).str.slice(0, 2).astype(int) - 1, unit="h"
        )
        df = df.assign(ts=ts)
        df = df[df.ts.dt.year == year]
        if df.empty:
            continue
        parts.append(df)
    if not parts:
        return pd.DataFrame()
    S = pd.concat(parts, ignore_index=True)
    S = S[(S.HSL > 0.0)]
    S["plant"] = S["Resource Name"].map(SITE_TO_PLANT)

    mw = S[mw_cols].to_numpy(dtype=float)
    px = S[px_cols].to_numpy(dtype=float)
    valid = ~np.isnan(mw) & ~np.isnan(px)
    submits = valid.any(axis=1)
    # Top of the submitted curve = the price at the largest offered MW point.
    top_idx = np.where(valid, mw, -np.inf).argmax(axis=1)
    top_px = px[np.arange(len(px)), top_idx]
    top_mw = mw[np.arange(len(mw)), top_idx]
    bot_idx = np.where(valid, mw, np.inf).argmin(axis=1)
    bot_px = px[np.arange(len(px)), bot_idx]
    return pd.DataFrame(
        {
            "plant": S.plant.to_numpy(),
            "resource": S["Resource Name"].to_numpy(),
            "hsl": S.HSL.to_numpy(dtype=float),
            "lsl": S.LSL.to_numpy(dtype=float),
            "submits": submits,
            "top_price": np.where(submits, top_px, np.nan),
            "top_mw": np.where(submits, top_mw, np.nan),
            "bot_price": np.where(submits, bot_px, np.nan),
        }
    )


def _wp50(values: np.ndarray, weights: np.ndarray) -> float:
    """Capacity-weighted median (same construction as ERCOT-127 section E)."""
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = w.cumsum()
    return float(v[np.searchsorted(cw, cw[-1] / 2.0)])


def section_b_measured_offer(year: int) -> dict:
    """B -- the real fleet's submitted DAM coal offer, per plant ($/MWh).

    ``submit_share`` is the share of committed (``HSL > 0``) coal resource-hours
    that submit ANY incremental energy curve — ``DIAGNOSIS-ercot122`` §4's reach
    statistic from the offer side.  The price statistics are conditional on
    submitting, because an unsubmitted curve has no top price (pricing that
    block would be the fitted wall rule 13 [R-MEASURED] forbids and rule 19
    [R-ONE-MECH] would stack).
    """
    df = _dam_coal_offers(year)
    if df.empty:
        return {}
    rows = []
    for code in sorted(COAL_PLANTS):
        sub = df[df.plant == code]
        if sub.empty:
            continue
        sm = sub[sub.submits]
        rows.append(
            {
                "plant": COAL_PLANTS[code],
                "plant_code": code,
                "resource_hours": int(len(sub)),
                "submit_share": round(float(sub.submits.mean()), 4),
                "top_offer_capwtd_p50": (
                    round(_wp50(sm.top_price.to_numpy(), sm.hsl.to_numpy()), 2)
                    if len(sm)
                    else None
                ),
                "top_offer_mean": (
                    round(float(sm.top_price.mean()), 2) if len(sm) else None
                ),
                "bot_offer_capwtd_p50": (
                    round(_wp50(sm.bot_price.to_numpy(), sm.hsl.to_numpy()), 2)
                    if len(sm)
                    else None
                ),
            }
        )
    sm = df[df.submits]
    return {
        "per_plant": rows,
        "fleet": {
            "resource_hours": int(len(df)),
            "submit_share": round(float(df.submits.mean()), 4),
            "top_offer_capwtd_p50": round(
                _wp50(sm.top_price.to_numpy(), sm.hsl.to_numpy()), 2
            ),
            "top_offer_p90": round(float(np.nanpercentile(sm.top_price, 90)), 2),
            "top_offer_max": round(float(np.nanmax(sm.top_price)), 2),
        },
    }


# --------------------------------------------------------------------------
# C -- F923 delivered-coal-price reconciliation
# --------------------------------------------------------------------------
def section_c_f923(year: int, model_surface: dict) -> dict:
    """C -- does the model's delivered coal price equal the F923 receipt?

    The keeper carries ``coal_plant_monthly_pricing=True``, so
    :func:`market_sim.data.fuel.plant_prices` overwrites each coal plant-month
    with that plant's own EIA-923 delivered receipt.  If that identity holds,
    the A-vs-B gap **cannot** be a fuel-price error and is localised to the
    offer construction (heat rate x passthrough x tranche geometry) — which is
    what ERCOT-112 §6 left open and what this section closes.
    """
    costs = pd.read_parquet(
        paths.RAW_DIR / "_processed-legacy" / "eia923_monthly_fuel_costs.parquet"
    )
    c = costs[(costs.year == year) & (costs.fuel_group == F923_COAL)]
    by_plant = {}
    for code, sub in c.groupby("plant_id"):
        q = sub.quantity.to_numpy(dtype=float)
        p = sub.price_per_mmbtu.to_numpy(dtype=float)
        ok = ~np.isnan(p) & (q > 0)
        if ok.any():
            by_plant[int(code)] = float((p[ok] * q[ok]).sum() / q[ok].sum())
    rows = []
    rep_cap = tot_cap = 0.0
    for r in model_surface.get("per_plant", []):
        f923 = by_plant.get(r["plant_code"])
        months = int(
            ((c.plant_id == r["plant_code"]) & c.price_per_mmbtu.notna()).sum()
        )
        tot_cap += r["pmax_mw"]
        if months:
            rep_cap += r["pmax_mw"]
        rows.append(
            {
                "plant": r["plant"],
                "plant_code": r["plant_code"],
                "pmax_mw": r["pmax_mw"],
                "model_fuel_price": r["fuel_price_mmbtu"],
                "f923_qty_wtd_price": (round(f923, 3) if f923 is not None else None),
                "delta": (
                    round(r["fuel_price_mmbtu"] - f923, 3)
                    if f923 is not None
                    else None
                ),
                "months_reported": months,
                # With no receipt the plant cannot be priced plant-specifically:
                # data.fuel.plant_prices leaves it on the coal-supply trajectory
                # that apply_coal_supply_pricing set (mine-mouth lignite vs PRB
                # by rail), which is why the un-reported plants collapse onto a
                # small number of shared values.
                "priced_from": "f923_receipt" if months else "supply_trajectory",
            }
        )
    # The distinct fallback levels actually in force, so the trajectory side is
    # visible rather than implied.
    fallback = sorted(
        {r["model_fuel_price"] for r in rows if r["priced_from"] == "supply_trajectory"}
    )
    return {
        "per_plant": rows,
        "coverage": {
            "plants_reporting": sum(1 for r in rows if r["months_reported"]),
            "plants_total": len(rows),
            "capacity_reporting_mw": round(rep_cap, 1),
            "capacity_total_mw": round(tot_cap, 1),
            "capacity_share_reporting": (
                round(rep_cap / tot_cap, 4) if tot_cap else None
            ),
            "fallback_levels_mmbtu": fallback,
        },
    }


# --------------------------------------------------------------------------
# D -- take-or-pay / committed share
# --------------------------------------------------------------------------
def section_d_committed_share() -> dict:
    """D -- measured committed-band fraction vs the model's tranche split.

    The measured side is ``ERCOT-127`` section E **imported verbatim** (not
    re-implemented): the ERCOT-62 derive's construction for ``CLLIG``,
    committed = ``HSL > 0``, capacity-weighted p50 of ``LSL/HSL`` plus the
    fleet aggregate ``sum(LSL)/sum(HSL)``.  The model side is its own
    committed take-or-pay tranche share, read from the keeper's resolved
    config rather than from the class defaults.
    """
    measured = section_e_coal_min_load()
    cfg = json.loads((KEEPER_BUNDLE / "run_config.json").read_text())
    sc = cfg.get("scenario_config", {})
    t1 = float(sc.get("coal_tranche_1_frac", 0.30))
    t2 = float(sc.get("coal_tranche_2_frac", 0.25))
    t3 = float(sc.get("coal_tranche_3_frac", 0.45))
    return {
        "measured": measured,
        "model": {
            "coal_tranche_1_frac": t1,
            "coal_tranche_1_fuel_passthrough": float(
                sc.get("coal_tranche_1_fuel_passthrough", 0.0)
            ),
            "coal_tranche_2_frac": t2,
            "coal_tranche_2_fuel_passthrough": float(
                sc.get("coal_tranche_2_fuel_passthrough", 0.35)
            ),
            "coal_tranche_3_frac": t3,
            "coal_tranche_3_fuel_passthrough": float(
                sc.get("coal_tranche_3_fuel_passthrough", 1.0)
            ),
            "note": (
                "tranche 1 is the take-or-pay (VOM-only) band; the model's "
                "'committed' share is coal_tranche_1_frac"
            ),
        },
    }


# --------------------------------------------------------------------------
# E -- the plant-grain water-fill landing vs the COP declaration
# --------------------------------------------------------------------------
def section_e_waterfill(year: int) -> dict:
    """E -- per-plant ARM availability landing vs its own COP declaration.

    ``FINDING-ercot134`` §2 recorded Martin Lake landing at **1.45x** its
    declaration and left it "reported for the successor lane; not acted on".
    The redistribution pins the CLASS-hour mean to the measured fraction and
    water-fills per plant, so a plant whose model ``pmax`` exceeds its declared
    rating can land above its own declaration while the class total is right.
    This decomposes that: per plant, the ARM's mean available MW over hours the
    plant is declared live, against the declaration over the same hours, plus
    the ``pmax``/declaration headroom ratio that drives the overshoot.
    """
    arm = capture_coal_availability(
        year, {"ercot_thermal_dam_availability_coal": True}
    )
    base = capture_coal_availability(year)
    live = dam_declared(year)
    n = len(hour_index(year))
    rows = []
    for code in sorted(COAL_PLANTS):
        a = arm["avail_mw"].get(code)
        b = base["avail_mw"].get(code)
        if a is None or b is None or code not in live:
            continue
        a, b = a[:n], b[:n]
        dec = live[code].to_numpy(dtype=float)[:n]
        on = dec > 1.0
        if not on.any():
            continue
        pmax = arm["pmax"].get(code, float("nan"))
        rows.append(
            {
                "plant": COAL_PLANTS[code],
                "plant_code": code,
                "declared_live_hours": int(on.sum()),
                "pmax_mw": round(pmax, 1),
                "declared_mean_mw": round(float(dec[on].mean()), 1),
                "declared_max_mw": round(float(dec[on].max()), 1),
                "arm_mean_mw": round(float(a[on].mean()), 1),
                "base_mean_mw": round(float(b[on].mean()), 1),
                "arm_over_declared": round(float(a[on].mean() / dec[on].mean()), 4),
                "base_over_declared": round(float(b[on].mean() / dec[on].mean()), 4),
                # The headroom the water-fill can exploit: a plant whose model
                # pmax sits above its declared maximum can absorb more than its
                # share of the class-mean pin.
                "pmax_over_declared_max": round(float(pmax / dec[on].max()), 4),
                "hours_arm_above_declared": int((a > dec + 1e-6)[on].sum()),
            }
        )
    return {"per_plant": rows}


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------
def _print_a_b(year: int, a: dict, b: dict) -> None:
    """Print the A-vs-B per-plant offer comparison for ``year``."""
    print(f"\n=== A/B: model coal bid vs measured DAM coal offer — {year} ===")
    print(
        f"{'plant':<14}{'cap MW':>9}{'HR':>7}{'$/MMBtu':>9}"
        f"{'pass':>7}{'mdl top':>9}{'mdl mean':>10}"
        f"{'DAM top':>9}{'submit':>8}{'gap':>8}"
    )
    bmap = {r["plant_code"]: r for r in b.get("per_plant", [])}
    for r in a["per_plant"]:
        m = bmap.get(r["plant_code"], {})
        dam = m.get("top_offer_capwtd_p50")
        gap = None if dam is None else round(r["bid_top_tranche"] - dam, 2)
        print(
            f"{r['plant']:<14}{r['pmax_mw']:>9.0f}{r['heat_rate_capwtd']:>7.2f}"
            f"{r['fuel_price_mmbtu']:>9.2f}{r['passthrough_capwtd']:>7.3f}"
            f"{r['bid_top_tranche']:>9.2f}{r['bid_capwtd_mean']:>10.2f}"
            f"{(dam if dam is not None else float('nan')):>9.2f}"
            f"{(m.get('submit_share') or float('nan')):>8.3f}"
            f"{(gap if gap is not None else float('nan')):>8.2f}"
        )
    f, g = a["fleet"], b.get("fleet", {})
    print(
        f"{'FLEET':<14}{f['pmax_mw']:>9.0f}{'':>7}{'':>9}{'':>7}"
        f"{f['bid_top']:>9.2f}{f['bid_capwtd_mean']:>10.2f}"
        f"{(g.get('top_offer_capwtd_p50') or float('nan')):>9.2f}"
        f"{(g.get('submit_share') or float('nan')):>8.3f}"
    )
    print(f"  model coal supply curve (cap-wtd bid deciles): {f['bid_deciles']}")
    cs = _cheap_share(a, b)
    if cs:
        print(
            f"  model coal capacity bid BELOW the measured "
            f"${cs['reference_dam_offer']}/MWh DAM offer: "
            f"{cs['capacity_below_mw']:.0f} / {cs['capacity_total_mw']:.0f} MW = "
            f"{cs['share_below']:.1%}"
        )


def synthesize(out: dict) -> dict:
    """F -- the sized merit-order bias: cheap capacity that is NOT min-load.

    Pure post-processing of sections A/B/C/D — no capture, no LP.

    ``share_below`` (A vs B) is the share of model coal capacity offered under
    the price the real fleet actually submits.  Some of that is legitimate:
    a plant's minimum-load block runs price-independently, and the measured
    ``LSL/HSL`` fleet aggregate (section D, the ERCOT-62 convention) is how much
    of committed coal that is.  The DIFFERENCE is the part that has no
    min-load justification —

        excess_cheap = share_below - measured_committed_share

    — i.e. capacity the model offers below the measured DAM price while NOT
    being min-load.  That block clears ahead of gas in every hour whose price
    exceeds its bid, which is the band-uniform over-loading
    ``FINDING-ercot134`` §2 measured (+6 to +18 pp in EVERY band, G1 1/21).

    This is a SIZING statistic, not a mechanism.  Rule 19 [R-ONE-MECH] and
    ``DIAGNOSIS-ercot122`` §4 both still bind: whether the model's cheap block
    corresponds to real self-scheduled (price-taking) capacity is the open
    REACH question owned by the SCED TPO instrument (``FINDING-ercot117`` §E),
    and it is NOT settled here.
    """
    d = out.get("D_committed_share", {}).get("measured", {})
    rows = {}
    for y, cs in out.get("AB_cheap_share", {}).items():
        m = d.get(y)
        if not m or not cs:
            continue
        committed = float(m["fleet_aggregate_lsl_over_hsl"])
        below = float(cs["share_below"])
        total = float(cs["capacity_total_mw"])
        rows[y] = {
            "share_below_measured_offer": round(below, 4),
            "measured_committed_share": round(committed, 4),
            "excess_cheap_share": round(below - committed, 4),
            "excess_cheap_mw": round((below - committed) * total, 1),
        }
    return rows


def main() -> None:
    """Run the requested sections and write the JSON blob."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--sections",
        default="ABCDE",
        help="subset of ABCDE to run (default all)",
    )
    ap.add_argument(
        "--year",
        type=int,
        nargs="*",
        default=list(YEARS),
        help="years to score (default 2023 2024 2025)",
    )
    ap.add_argument(
        "--synthesize",
        action="store_true",
        help="recompute section F from the saved JSON (no capture, no LP)",
    )
    args = ap.parse_args()
    if args.synthesize:
        out = json.loads(OUT_JSON.read_text())
        out["F_excess_cheap"] = synthesize(out)
        OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
        print("\n=== F: cheap coal capacity that is NOT min-load ===")
        for y, r in out["F_excess_cheap"].items():
            print(
                f"  {y}: offered below measured DAM price "
                f"{r['share_below_measured_offer']:.1%}, measured min-load share "
                f"{r['measured_committed_share']:.1%}  ->  EXCESS "
                f"{r['excess_cheap_share']:.1%} = {r['excess_cheap_mw']:.0f} MW"
            )
        print(f"\nwrote {OUT_JSON}")
        return
    for y in args.year:
        if y not in YEARS:
            raise SystemExit(
                f"rule 22 [R-HOLDOUT]: {y} is outside the training window {YEARS}"
            )
    want = set(args.sections.upper())
    out: dict = {"keeper_bundle": KEEPER_BUNDLE.name, "years": args.year}

    if "D" in want:
        out["D_committed_share"] = section_d_committed_share()
        d = out["D_committed_share"]
        print("\n=== D: take-or-pay / committed share ===")
        print(f"  model coal_tranche_1_frac (take-or-pay) = {d['model']['coal_tranche_1_frac']}")
        for y in (*[str(x) for x in YEARS], "pooled"):
            if y in d["measured"]:
                m = d["measured"][y]
                print(
                    f"  measured {y:>6}: cap-wtd p50 LSL/HSL = "
                    f"{m['cap_weighted_p50_lsl_over_hsl']}, "
                    f"fleet agg = {m['fleet_aggregate_lsl_over_hsl']}"
                )

    for year in args.year:
        ykey = str(year)
        if "A" in want:
            out.setdefault("A_model_offer", {})[ykey] = section_a_model_offer(year)
        if "B" in want:
            out.setdefault("B_measured_offer", {})[ykey] = section_b_measured_offer(year)
        if "A" in want and "B" in want:
            _print_a_b(
                year, out["A_model_offer"][ykey], out["B_measured_offer"][ykey]
            )
            out.setdefault("AB_cheap_share", {})[ykey] = _cheap_share(
                out["A_model_offer"][ykey], out["B_measured_offer"][ykey]
            )
        if "C" in want and "A" in want:
            out.setdefault("C_f923", {})[ykey] = section_c_f923(
                year, out["A_model_offer"][ykey]
            )
            print(f"\n=== C: F923 delivered-coal reconciliation — {year} ===")
            for r in out["C_f923"][ykey]["per_plant"]:
                print(
                    f"  {r['plant']:<14} model {r['model_fuel_price']:>7.3f}  "
                    f"F923 {str(r['f923_qty_wtd_price']):>7}  "
                    f"delta {str(r['delta']):>7}  months {r['months_reported']:>2}"
                    f"  {r['priced_from']}"
                )
            cov = out["C_f923"][ykey]["coverage"]
            print(
                f"  COVERAGE: {cov['plants_reporting']}/{cov['plants_total']} plants, "
                f"{cov['capacity_share_reporting']:.1%} of coal MW have a receipt; "
                f"fallback levels {cov['fallback_levels_mmbtu']} $/MMBtu"
            )
        if "E" in want:
            out.setdefault("E_waterfill", {})[ykey] = section_e_waterfill(year)
            print(f"\n=== E: plant-grain water-fill landing vs COP — {year} ===")
            print(
                f"  {'plant':<14}{'pmax':>8}{'dec mean':>10}{'ARM':>9}"
                f"{'BASE':>9}{'ARM/dec':>9}{'pmax/decmax':>12}"
            )
            for r in out["E_waterfill"][ykey]["per_plant"]:
                print(
                    f"  {r['plant']:<14}{r['pmax_mw']:>8.0f}"
                    f"{r['declared_mean_mw']:>10.0f}{r['arm_mean_mw']:>9.0f}"
                    f"{r['base_mean_mw']:>9.0f}{r['arm_over_declared']:>9.3f}"
                    f"{r['pmax_over_declared_max']:>12.3f}"
                )

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nwrote {OUT_JSON}")


if __name__ == "__main__":
    main()
