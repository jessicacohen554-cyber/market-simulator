"""miso-145 probe — MISO's REAL submitted offer curve vs the model's own stack.

PREREG ``results/calibration/PREREG-miso145-summer-offer-conduct-2026-08-09.md``
(pushed at ``083222bf`` before any adjudicating statistic).

**No LP solve, no keeper replay.**  The model side is reconstructed through
``_miso143_stack.fleet_state`` (``run_year(fleet_only=True)`` — the
orchestrator's OWN availability/offer reconstruction), reused verbatim, so the
offer prices read here are the ones the LP solved on.  The real side is the
``energy-offers`` clean datatype curated from MISO's masked submitted-offer
corpus (``scripts/data/curate_miso_energy_offers.py``); its dispatch-award
columns do not exist in that datatype (rule 13, enforced at curation).

WHAT THIS PROBE MAY AND MAY NOT CLAIM
-------------------------------------
miso-138 built the offer-side class bridge for this corpus and the
pre-committed verdict was **REFUTED** — coal and CC are not separable in this
feature family.  So **no class-conditional statistic is computed here**; every
reading is at FLEET grain, and PREREG §2(a) declared that limit before any
number was seen.  What miso-138 *did* establish is the basis this rests on: the
corpus reconciles to EIA-860 MISO at fleet grain (+12.9 / +9.0 / +6.0 % MW).

THE UNIVERSE DISCIPLINE (TRAP 3, the miso-144 lesson)
-----------------------------------------------------
Two devices, both pre-registered:

1. **Price-identified positions, never need-matched ones.**  Each side's
   clearing position is located by its OWN clearing PRICE — the model's
   committed P1 price on the model stack, the measured RT price on the real
   curve — so no demand/import/renewable alignment enters the primary reading
   at all.  The headline "GW between $P_model and $P_actual" is evaluated on
   BOTH curves between the SAME two price levels.
2. **Percentile-of-own-capability** for the level decomposition, computed on
   two universes: ALL corpus rows, and a declaration-screened "conventional"
   subset (no curtailment-offer price, no storage SOC bounds) that is the
   closer match to the model's fleet, which carries no wind/solar rows at all
   (they are LP decision variables, not generator rows).  The verdict must hold
   on both or the disagreement IS the finding.

Probe hygiene (miso-140b §6): repo root on ``sys.path`` and
``load_zonal_shares`` asserted non-None, via ``_miso143_stack.hygiene``.

Usage::

    python scripts/probes/_miso145_offer_conduct.py \
        [--out results/calibration/_miso145_offer_conduct.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso143_stack import (  # noqa: E402
    GAS_COLS,
    THERMAL_COLS,
    YEARS,
    fleet_state,
    hygiene,
    klass_of,
    markup_ceiling,
    month_of_hour,
    sidecar_classes,
    sidecar_price,
    windows,
)
from market_sim.config import paths  # noqa: E402

HOURS = 8760
#: Ladder positions above a curve's own clearing, in GW (miso-143's construction).
LADDER_GW = (1.0, 2.0, 5.0)
#: TRAP 5 — the C3c tail lives above this actual-price level and is separated out.
TAIL_USD = 200.0
#: PREREG §1: the six committed miso-142/143 window deficits, for gate G-F1.
COMMITTED_DEFICITS = {
    "2023|W1_jun_jul_h8_20": -4.750,
    "2023|JJA_h12_17": -8.333,
    "2024|W1_jun_jul_h8_20": -10.676,
    "2024|JJA_h12_17": -10.671,
    "2025|W1_jun_jul_h8_20": -30.999,
    "2025|JJA_h12_17": -30.435,
}


# --------------------------------------------------------------- real side


def _hour_of_year(local: pd.Series) -> np.ndarray:
    """Map published EST timestamps to the model's NON-LEAP hour-of-year index.

    ``_miso143_stack.month_of_hour`` builds the model's calendar on a 365-day
    basis, so 2024 is treated as non-leap by the model itself.  The corpus is
    mapped onto the SAME basis (cumulative non-leap month starts + day + hour)
    rather than onto a true calendar, so a JJA hour on one side is the same
    JJA hour on the other.  Feb-29 never enters this lane's window.
    """
    starts = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30])
    doy = starts[local.dt.month.to_numpy() - 1] + (local.dt.day.to_numpy() - 1)
    return doy * 24 + local.dt.hour.to_numpy()


def load_real_segments(year: int, market: str, hours: np.ndarray) -> pd.DataFrame:
    """Return INCREMENTAL offer segments for ``hours`` from the clean datatype.

    The source curve is cumulative: ``MW1..MW10`` are output levels and
    ``Price1..Price10`` the offer at each level.  This converts it to
    incremental (MW, price) segments per unit-hour:

    * the cumulative levels are clipped to ``[0, ecomax_mw]`` — a curve point
      above the declared economic maximum is not deliverable capability and is
      dropped rather than credited;
    * ``seg_mw`` is the increment over the previous clipped level;
    * ``seg_price`` is the step's own price for a BLOCK offer
      (``bid_slope_flag`` False) and the mean of the segment's two endpoint
      prices for a piecewise-LINEAR offer (True), which is that segment's mean
      $/MWh — the ``price_hi`` sensitivity column keeps the endpoint price so
      the construction choice is visible, never buried.

    Also returned per row: ``is_conventional`` — the declaration-based screen
    (no curtailment-offer price, no storage SOC bounds).  It is NOT a fuel
    classification and no class is claimed from it (miso-138).
    """
    path = paths.clean_path("energy-offers", iso="MISO", year=year, market=market)
    df = pd.read_parquet(
        path,
        columns=[
            "interval_start_local",
            "unit_code",
            "region",
            "bid_slope_flag",
            "step_idx",
            "step_mw",
            "step_price_usd_per_mwh",
            "ecomax_mw",
            "unit_available_flag",
            "must_run_flag",
            "self_scheduled_mw",
            "curtailment_offer_price_usd_per_mwh",
            "min_energy_storage_level_mwh",
            "max_energy_storage_level_mwh",
        ],
    )
    df["hour"] = _hour_of_year(df["interval_start_local"])
    df = df[df["hour"].isin(hours)]
    df = df.sort_values(["hour", "unit_code", "step_idx"], kind="stable")

    cap = df["ecomax_mw"].to_numpy(float)
    cum = np.clip(df["step_mw"].to_numpy(float), 0.0, np.where(np.isfinite(cap), cap, np.inf))
    grp = df.groupby(["hour", "unit_code"], sort=False)
    prev_cum = grp["step_mw"].shift(1).to_numpy(float)
    prev_cum = np.where(np.isnan(prev_cum), 0.0, prev_cum)
    prev_cum = np.clip(prev_cum, 0.0, np.where(np.isfinite(cap), cap, np.inf))

    price = df["step_price_usd_per_mwh"].to_numpy(float)
    prev_price = grp["step_price_usd_per_mwh"].shift(1).to_numpy(float)
    prev_price = np.where(np.isnan(prev_price), price, prev_price)
    sloped = df["bid_slope_flag"].to_numpy(bool)
    seg_price = np.where(sloped, 0.5 * (price + prev_price), price)

    out = pd.DataFrame(
        {
            "hour": df["hour"].to_numpy(),
            "seg_mw": cum - prev_cum,
            "seg_price": seg_price,
            "price_hi": price,
            "is_conventional": (
                ~np.isfinite(df["curtailment_offer_price_usd_per_mwh"].to_numpy(float))
                & ~np.isfinite(df["min_energy_storage_level_mwh"].to_numpy(float))
                & ~np.isfinite(df["max_energy_storage_level_mwh"].to_numpy(float))
            ),
            "available": df["unit_available_flag"].to_numpy(bool),
        }
    )
    return out[out["seg_mw"] > 0.0].reset_index(drop=True)


# ------------------------------------------------------- curve primitives


def price_at_cum(sorted_price: np.ndarray, cum: np.ndarray, x: float) -> float:
    """Offer price at cumulative MW ``x`` on one hour's price-sorted curve.

    Returns the TOP of the observed curve (and the caller reports it as
    unreached) when ``x`` exceeds the curve — a flat stack is never credited
    with a tail it does not reach (the ``_miso143_stack.clear`` convention).
    """
    if sorted_price.size == 0:
        return float("nan")
    j = int(np.searchsorted(cum, x, side="left"))
    if j >= sorted_price.size:
        return float(sorted_price[-1])
    return float(sorted_price[j])


#: Percentiles of a curve's OWN capability at which both sides are compared.
PCTL_GRID = (0.50, 0.70, 0.80, 0.85, 0.90, 0.95, 0.98)


def price_at_pctl(
    hours: np.ndarray,
    seg_h: np.ndarray,
    seg_p: np.ndarray,
    seg_mw: np.ndarray,
    pctl: np.ndarray,
) -> np.ndarray:
    """Offer price at a per-hour percentile of the curve's OWN total MW.

    ``pctl`` is one fraction per hour (a scalar grid point broadcast, or the
    other side's measured clearing percentile).  This is the universe-
    normalising comparison device of PREREG §4: each side is positioned
    against its own stack, so a universe that is larger on one side cannot
    manufacture a level difference.
    """
    order = np.lexsort((seg_p, seg_h))
    h_s, p_s, m_s = seg_h[order], seg_p[order], seg_mw[order]
    i0s = np.searchsorted(h_s, hours, side="left")
    i1s = np.searchsorted(h_s, hours, side="right")
    out = np.full(hours.size, np.nan)
    for k, (i0, i1) in enumerate(zip(i0s, i1s)):
        if i1 <= i0:
            continue
        cum = np.cumsum(m_s[i0:i1])
        out[k] = price_at_cum(p_s[i0:i1], cum, float(pctl[k]) * float(cum[-1]))
    return out


def curve_readings(
    hours: np.ndarray,
    seg_h: np.ndarray,
    seg_p: np.ndarray,
    seg_mw: np.ndarray,
    anchor: np.ndarray,
) -> dict[str, np.ndarray]:
    """Per-hour ladder readings above each hour's ``anchor`` price.

    Returns ``price_at_plus_<G>gw`` for every G in :data:`LADDER_GW`, the total
    curve MW, and the MW at or below the anchor.
    """
    order = np.lexsort((seg_p, seg_h))
    h_s, p_s, m_s = seg_h[order], seg_p[order], seg_mw[order]
    bounds = np.searchsorted(h_s, hours, side="left")
    ends = np.searchsorted(h_s, hours, side="right")

    below = np.zeros(hours.size)
    total = np.zeros(hours.size)
    out = {f"p_plus_{g:g}gw": np.full(hours.size, np.nan) for g in LADDER_GW}
    for k, (i0, i1) in enumerate(zip(bounds, ends)):
        if i1 <= i0:
            continue
        p = p_s[i0:i1]
        cum = np.cumsum(m_s[i0:i1])
        total[k] = cum[-1]
        a = anchor[k]
        below[k] = float(m_s[i0:i1][p <= a].sum())
        for g in LADDER_GW:
            out[f"p_plus_{g:g}gw"][k] = price_at_cum(p, cum, below[k] + g * 1000.0)
    out["mw_below_anchor"] = below
    out["mw_total"] = total
    return out


# --------------------------------------------------------------- model side


def model_block(year: int) -> dict:
    """Rebuild the model's own offer stack and committed window quantities."""
    st = fleet_state(year)
    gens, fa = st["fleet"], st["fleet_arrays"]
    mc0 = np.asarray(st["mc_base"], dtype=float)
    mk = markup_ceiling(gens, fa, st["config"])
    kl = klass_of(gens)
    for k in ("COAL", "CC_REGULAR", "CT_PEAKER", "ST_GAS"):
        assert (kl == k).sum() > 0, f"class {k!r} has ZERO fleet rows (TRAP 5)"
    price, _ = sidecar_price(year)
    piv = sidecar_classes(year)
    return {
        "offer": {"lo": mc0, "hi": mc0 + mk[:, None]},
        "cap": fa.pmax[:, None] * fa.availability,
        "klass": kl,
        "p1_price": price,
        "sidecar": piv,
        "n_gen": len(gens),
    }


def model_curve_readings(mb: dict, hours: np.ndarray, bracket: str, anchor: np.ndarray):
    """:func:`curve_readings` over the model's per-generator stack."""
    offer = mb["offer"][bracket][:, hours]
    cap = mb["cap"][:, hours]
    n_gen, n_h = offer.shape
    seg_h = np.repeat(hours, n_gen)
    seg_p = offer.T.reshape(-1)
    seg_mw = cap.T.reshape(-1)
    ok = seg_mw > 0
    return curve_readings(hours, seg_h[ok], seg_p[ok], seg_mw[ok], anchor)


def model_price_at_pctl(mb: dict, hours, bracket: str, pctl: np.ndarray) -> np.ndarray:
    """:func:`price_at_pctl` over the model's per-generator stack."""
    offer = mb["offer"][bracket][:, hours]
    cap = mb["cap"][:, hours]
    n_gen = offer.shape[0]
    seg_h = np.repeat(hours, n_gen)
    seg_p = offer.T.reshape(-1)
    seg_mw = cap.T.reshape(-1)
    ok = seg_mw > 0
    return price_at_pctl(hours, seg_h[ok], seg_p[ok], seg_mw[ok], pctl)


def model_mw_between(mb: dict, hours, bracket: str, lo: np.ndarray, hi: np.ndarray):
    """Model-stack MW priced strictly above ``lo`` and at or below ``hi``."""
    offer = mb["offer"][bracket][:, hours]
    cap = mb["cap"][:, hours]
    m = (offer > lo[None, :]) & (offer <= hi[None, :])
    return (cap * m).sum(axis=0)


# ------------------------------------------------------------------- main


def run(markets=("RT", "DA"), out_path: Path | None = None) -> dict:
    """Execute gates G-F1..G-F4 and predictions P-A*/P-B* for every year."""
    hygiene()
    from _miso137_c3a_gap_decomposition import actual_hourly, model_hourly

    wins = windows()
    result: dict = {
        "prereg": "results/calibration/PREREG-miso145-summer-offer-conduct-2026-08-09.md",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "posture": "NO SOLVE -- run_year(fleet_only=True) stack vs the measured MISO offer corpus",
        "grain": "FLEET (miso-138 REFUTED the offer-side class bridge; no class statistic computed)",
        "committed_deficits": COMMITTED_DEFICITS,
        "years": {},
    }

    for year in YEARS:
        mb = model_block(year)
        rt_actual, _da_actual = actual_hourly(year)
        _h, _p, w_model, _z = model_hourly(year)
        yr: dict = {"n_gen": mb["n_gen"], "windows": {}}
        # Load each market's segments ONCE per year, over the union of both
        # windows' hours: the parquet slices are ~11 M rows and re-reading them
        # per window would dominate runtime.
        union_hours = np.nonzero(np.logical_or.reduce(list(wins.values())))[0]
        seg_cache = {m: load_real_segments(year, m, union_hours) for m in markets}

        for wname, sel in wins.items():
            ok = sel & np.isfinite(mb["p1_price"]) & np.isfinite(rt_actual)
            hours = np.nonzero(ok)[0]
            anchor = mb["p1_price"][hours]
            target = rt_actual[hours]
            w = w_model[hours]
            wgt = w / max(1e-9, w.sum())

            # ---- G-F1 footing: the committed deficit, one weight (TRAP 7) ----
            model_lw = float((anchor * w).sum() / max(1e-9, w.sum()))
            actual_lw = float((target * w).sum() / max(1e-9, w.sum()))
            blk: dict = {
                "n_hours": int(hours.size),
                "anchor_lw_price": round(model_lw, 3),
                "actual_lw_price": round(actual_lw, 3),
                "deficit_usd_per_mwh": round(model_lw - actual_lw, 3),
            }

            # ---- G-F4 tail separation (TRAP 5) ----
            ordinary = target <= TAIL_USD
            blk["tail_separation"] = {
                "n_ordinary_le_200": int(ordinary.sum()),
                "n_tail_gt_200": int((~ordinary).sum()),
                "n_actual_le_100": int((target <= 100.0).sum()),
                "n_actual_100_200": int(((target > 100.0) & ordinary).sum()),
                "ordinary_deficit_usd_per_mwh": round(
                    float(
                        (anchor[ordinary] * w[ordinary]).sum()
                        / max(1e-9, w[ordinary].sum())
                        - (target[ordinary] * w[ordinary]).sum()
                        / max(1e-9, w[ordinary].sum())
                    ),
                    3,
                ),
            }

            blk["real"] = {}
            # ---- model side: ladder, walk, clearing percentile, pctl grid ----
            m_pctl_clear: dict[str, np.ndarray] = {}
            for bracket in ("lo", "hi"):
                mcr = model_curve_readings(mb, hours, bracket, anchor)
                m_between = model_mw_between(mb, hours, bracket, anchor, target)
                pc = np.clip(
                    mcr["mw_below_anchor"] / np.maximum(1e-9, mcr["mw_total"]), 0.0, 1.0
                )
                m_pctl_clear[bracket] = pc
                # miso-143's construction, reproduced for comparability: the
                # walk target there is the WINDOW-MEAN actual, not the hour's
                # own actual.  Both are reported; they are different statistics
                # and the finding says which is which.
                m_between_wm = model_mw_between(
                    mb, hours, bracket, anchor, np.full(hours.size, actual_lw)
                )
                mrec: dict = {
                    "model_ladder_slope_usd_per_gw": {
                        f"+{g:g}GW": round(
                            float(((mcr[f"p_plus_{g:g}gw"] - anchor) / g * wgt).sum()), 4
                        )
                        for g in LADDER_GW
                    },
                    "model_gw_anchor_to_hour_actual": round(
                        float((m_between * wgt).sum()) / 1000.0, 4
                    ),
                    "model_gw_anchor_to_window_mean_actual": round(
                        float((m_between_wm * wgt).sum()) / 1000.0, 4
                    ),
                    "model_capability_gw": round(
                        float((mcr["mw_total"] * wgt).sum()) / 1000.0, 3
                    ),
                    "model_clearing_percentile": round(float((pc * wgt).sum()), 4),
                    "model_price_at_pctl": {
                        f"p{int(q * 100)}": round(
                            float(
                                (
                                    model_price_at_pctl(
                                        mb, hours, bracket, np.full(hours.size, q)
                                    )
                                    * wgt
                                ).sum()
                            ),
                            3,
                        )
                        for q in PCTL_GRID
                    },
                }
                blk[bracket] = {"model": mrec}

            # ---- real side, per market and per universe ----
            for market in markets:
                segs_all = seg_cache[market]
                segs = segs_all[segs_all["hour"].isin(hours)]
                universes = {
                    "all": segs,
                    "conventional": segs[segs["is_conventional"]],
                    "available": segs[segs["available"]],
                }
                for uni, s in universes.items():
                    seg_h = s["hour"].to_numpy()
                    seg_p = s["seg_price"].to_numpy(float)
                    seg_mw = s["seg_mw"].to_numpy(float)

                    rcr_actual = curve_readings(hours, seg_h, seg_p, seg_mw, target)
                    rcr_model = curve_readings(hours, seg_h, seg_p, seg_mw, anchor)
                    total = np.maximum(1e-9, rcr_actual["mw_total"])
                    p_real = np.clip(rcr_actual["mw_below_anchor"] / total, 0.0, 1.0)

                    # GW between the model's clearing price and the actual price,
                    # on the REAL curve -- the like-for-like against the model's
                    # own walk.  Price-identified, no need matching (TRAP 3).
                    gw_real = (
                        rcr_actual["mw_below_anchor"] - rcr_model["mw_below_anchor"]
                    ) / 1000.0

                    rec = {
                        "real_capability_gw": round(
                            float((rcr_actual["mw_total"] * wgt).sum()) / 1000.0, 3
                        ),
                        "real_clearing_percentile": round(float((p_real * wgt).sum()), 4),
                        "real_gw_model_price_to_actual": round(
                            float((gw_real * wgt).sum()), 4
                        ),
                        "real_ladder_slope_usd_per_gw": {
                            f"+{g:g}GW": round(
                                float(
                                    ((rcr_actual[f"p_plus_{g:g}gw"] - target) / g * wgt).sum()
                                ),
                                4,
                            )
                            for g in LADDER_GW
                        },
                        "real_price_at_pctl": {
                            f"p{int(q * 100)}": round(
                                float(
                                    (
                                        price_at_pctl(
                                            hours,
                                            seg_h,
                                            seg_p,
                                            seg_mw,
                                            np.full(hours.size, q),
                                        )
                                        * wgt
                                    ).sum()
                                ),
                                3,
                            )
                            for q in PCTL_GRID
                        },
                        "n_segments": int(s.shape[0]),
                        "level_decomposition": {},
                    }

                    # PREREG §4 identity, at the MODEL's OWN clearing percentile
                    # (never the real curve's -- reading it off the real curve
                    # would make the level term identically zero by construction).
                    for bracket in ("lo", "hi"):
                        rp = price_at_pctl(
                            hours, seg_h, seg_p, seg_mw, m_pctl_clear[bracket]
                        )
                        fin = np.isfinite(rp)
                        wl = wgt * fin
                        wl = wl / max(1e-9, wl.sum())
                        level = float(((rp - anchor) * wl)[fin].sum())
                        position = float(((target - rp) * wl)[fin].sum())
                        wo = wgt * ordinary * fin
                        wo = wo / max(1e-9, wo.sum())
                        rec["level_decomposition"][bracket] = {
                            "real_at_model_percentile_usd": round(
                                float((rp * wl)[fin].sum()), 3
                            ),
                            "LEVEL_term_usd_per_mwh": round(level, 3),
                            "POSITION_term_usd_per_mwh": round(position, 3),
                            "level_share_of_deficit": round(
                                level / max(1e-9, actual_lw - model_lw), 4
                            ),
                            "ordinary_LEVEL_term_usd_per_mwh": round(
                                float(((rp - anchor) * wo)[fin].sum()), 3
                            ),
                            "n_finite_hours": int(fin.sum()),
                        }
                    rec["ordinary_hours"] = {
                        "real_gw_model_price_to_actual": round(
                            float((gw_real * (wgt * ordinary / max(1e-9, (wgt * ordinary).sum()))).sum()),
                            4,
                        )
                    }
                    blk["real"].setdefault(market, {})[uni] = rec

            yr["windows"][wname] = blk
        result["years"][str(year)] = yr

    if out_path:
        out_path.write_text(json.dumps(result, indent=1))
    return result


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out", default="results/calibration/_miso145_offer_conduct.json", type=Path
    )
    ap.add_argument("--markets", nargs="+", default=["RT", "DA"])
    args = ap.parse_args()
    res = run(markets=tuple(args.markets), out_path=args.out)
    for year, yr in res["years"].items():
        for wname, blk in yr["windows"].items():
            key = f"{year}|{wname}"
            print(
                f"{key}: deficit {blk['deficit_usd_per_mwh']} "
                f"(committed {COMMITTED_DEFICITS.get(key)})"
            )
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
