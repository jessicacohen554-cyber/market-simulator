"""Price every measured CT_PEAKER start the model does NOT make.

The follow-on to ``nyiso90_ct_gap_decomposition.py``. nyiso-90 established that
the NYISO CT_PEAKER gap is a **start-count** gap, not a run-length gap: mean run
length agrees within 7 % while the model synchronizes the fleet 2-5x less often
(1,138 / 937 / 2,061 model starts against 4,790 / 4,694 / 4,521 measured).

This probe asks the next question directly. For each hour in which the METER
shows a plant starting and the MODEL has that plant offline, what did the model
think the hour was worth, and what did it think the plant cost? The answer
splits the missing starts three ways and each branch implies a different
mechanism:

  (a) IN MERIT, declined anyway (model LMP >= the plant's own model offer)
      -- the model's cost and price are both right and it still did not start.
      A pure commitment/scheduling defect: the LP has no reason NOT to be on,
      so something else (a binding constraint, a reserve posture, transmission)
      is holding it off. This is the branch a commitment mechanism could fix.
  (b) OUT OF MERIT BY < $5/MWh -- the start is decided by a small cost or price
      error. This is the branch nyiso-88 §3's at-the-money measurement predicts,
      and the one where a modest, structurally-grounded input correction moves
      thousands of starts.
  (c) OUT OF MERIT BY A LOT -- the model believes the hour is deeply
      uneconomic. No merit-order repair reaches these; they are the branch that
      would require a genuinely non-energy driver (or an input that is wrong by
      much more than the fleet's whole margin).

Everything is read from committed artifacts and the same-HEAD zero-delta control
solve (rule 13 [R-MEASURED]: this is scoring-side characterisation, no measured
outcome enters any model input).

THE MODEL'S OWN OFFER, two independent ways
-------------------------------------------
The bundle's dispatch frame carries dispatched MW and the zonal LMP but not the
generator's marginal cost, so the offer the LP charged has to be recovered. Both
available routes are computed and reported against each other:

* ``revealed`` -- from the solve itself. In an hour where a plant is loaded
  strictly between zero and its own maximum, LP optimality makes it marginal, so
  its offer EQUALS the zonal LMP. Writing the offer as ``HR x gas(t) + k`` (the
  only time-varying term in a gas CT's marginal cost is the delivered fuel
  index), ``k`` is recovered as the median of ``lmp(t) - HR x gas(t)`` over those
  hours. This is the model's own number, with no reconstruction of the LP
  builder's tranche/markup stack.
* ``direct`` -- ``HR x gas(t) + vom``, assembled from the model fleet the keeper
  actually loads (``measured_ct_heat_rates=True``, nyiso-89) and the keeper's own
  per-zone delivered-gas seam (``nyiso_downstate_ct_gas_daily``).

``revealed`` is the primary: it is what the LP charged, including any tranche
markup or offer-curve band the direct assembly would miss. ``direct`` is the
cross-check, and the two are reported side by side so a disagreement is visible
rather than assumed away.

CLOCK: the committed bench series and the committed LMP parquet share the model's
non-leap 8760 local-standard clock, so the measured and model series are
index-aligned with no remap (nyiso-88's note). The raw CAMPD files are NOT --
this probe therefore takes its measured on/off from the BENCH, never from the
raw wall-clock files, because unlike nyiso-90's totals-only decomposition every
number here is hour-matched.

SCOPE: restricted to PURE combustion-turbine plants (every model unit at the
plant is ``CT_PEAKER``), the nyiso-88 §3 convention. That makes the bench series
unambiguously CT energy and side-steps the nyiso-88 §5 bench multi-class
collapse entirely.

Usage::

    python scripts/probes/nyiso91_ct_start_economics.py \
        --bundle results/calibration/nyiso91_ctrl_zerodelta
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.campd import _ONLINE_MW  # noqa: E402
from scripts.legitimacy_diagnostics import load_bench  # noqa: E402
from scripts.probes.nyiso88_peaker_economics import (  # noqa: E402
    LMP_PATH,
    downstate_ct_gas_hourly,
    measured_locational_premium,
    pure_ct_plants,
)

#: Model zone -> the zone name in the raw NYISO zonal RTD files, for the
#: locational robustness check. The committed ``actual_lmp_hourly_NYISO``
#: series is the 11-zone HUB the C criteria score against, while this fleet
#: sits in NYC and Long Island, which price above it (nyiso-88 §3). The
#: measured premium is added to the hub series as a SENSITIVITY only -- the
#: primary model-price column is already genuinely zonal (it is the LP's own
#: per-zone energy dual), so nothing in the headline depends on this.
_ZONE_TO_RTD = {"NYC": "N.Y.C.", "Long_Island": "LONGIL"}

PEAKER_CLASS = "CT_PEAKER"
ONLINE_FRAC = 0.05
HSL_PCTILE = 99.5

#: Band edge separating "decided by a small error" from "deeply uneconomic"
#: ($/MWh). Set to the magnitude of the measured fleet margin nyiso-88 §3
#: reports (-1.39 / +5.82 / +3.49), i.e. the scale at which a cost or price
#: error is large enough to flip a start on an at-the-money fleet.
NEAR_MISS_USD = 5.0

#: Minimum strictly-interior (marginal) hours a plant needs before its revealed
#: offer intercept is trusted; below this the direct assembly is used and the
#: plant is reported in ``n_plants_direct_fallback``.
MIN_MARGINAL_HOURS = 30


def starts(on: np.ndarray) -> np.ndarray:
    """Return the boolean mask of hours at which a run begins in ``on``."""
    prev = np.concatenate([[False], on[:-1]])
    return on & ~prev


def _plant_bar(series: np.ndarray) -> float:
    """Return the common physical online bar for a plant, in net MW.

    ``max(1 MW, 0.05 x HSL)`` where HSL is the p99.5 of the plant's measured
    net output -- the same construction as
    ``nyiso90_ct_gap_decomposition`` (there on the gross CAMPD basis), applied
    here to the bench's net series so BOTH sides are thresholded at one number.
    """
    hsl = float(np.percentile(series, HSL_PCTILE))
    return max(_ONLINE_MW, ONLINE_FRAC * hsl)


def model_heat_rates(year: int) -> tuple[dict[int, float], dict[int, float]]:
    """Return ``({plant_code: heat rate}, {plant_code: vom})``, capacity-weighted.

    Loaded with ``measured_ct_heat_rates=True`` -- the KEEPER's setting since
    nyiso-89 -- so this is the heat rate the LP actually charges, not the
    superseded eGRID plant average.
    """
    import collections

    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet.eia860 import load_fleet_from_csv

    gens = load_fleet_from_csv(
        "NYISO", get_iso_config("NYISO"), year=year, measured_ct_heat_rates=True
    )
    acc: dict[int, list[float]] = collections.defaultdict(lambda: [0.0, 0.0])
    vom: dict[int, list[float]] = collections.defaultdict(lambda: [0.0, 0.0])
    for g in gens:
        if (getattr(g, "plant_group", "") or "") != PEAKER_CLASS:
            continue
        code = int(getattr(g, "plant_code", 0) or 0)
        pmax = float(getattr(g, "pmax_mw", 0.0) or 0.0)
        acc[code][0] += pmax * float(getattr(g, "heat_rate", 0.0) or 0.0)
        acc[code][1] += pmax
        vom[code][0] += pmax * float(getattr(g, "vom", 0.0) or 0.0)
        vom[code][1] += pmax
    hr = {k: v[0] / v[1] for k, v in acc.items() if v[1] > 0}
    vm = {k: v[0] / v[1] for k, v in vom.items() if v[1] > 0}
    return hr, vm


def model_plant_series(bundle: Path, year: int, hours: int = 8760) -> dict[int, dict]:
    """Return ``{plant_code: {'mw','units','lmp','zone'}}`` for the model's CT fleet.

    ``units`` is the per-tranche ``{unit_id: (hours,) MW}`` map, needed because
    the offer that decides a START is the plant's CHEAPEST tranche, not the
    plant-level marginal one.

    **Dual-fuel hours are kept.** ``_dispatch_frame`` relabels a gas unit that
    switched to its backup oil as ``klass == "oil"``, so filtering on
    ``klass == "CT_PEAKER"`` silently drops those unit-hours (24 h of 2023 at
    plant 2494, for instance) and leaves a short series. The physical plant is
    still online in them, and this probe hour-matches starts, so the CT unit ids
    are resolved first and then ALL of their rows are taken whatever the hour's
    fuel label. Every series is reindexed onto the full ``0..hours-1`` clock with
    absent hours zero-filled, so a dropped row can never be read as an offline
    hour by accident.
    """
    df = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet",
        columns=["pass", "plant_code", "klass", "unit_id", "zone", "hour", "mw", "lmp"],
    )
    df = df[df["pass"] == "P1"]
    ct_units = set(df.loc[df["klass"] == PEAKER_CLASS, "unit_id"].astype(str).unique())
    df = df[df["unit_id"].astype(str).isin(ct_units)]
    idx = pd.RangeIndex(hours)
    out: dict[int, dict] = {}
    for code, g in df.groupby("plant_code", observed=True):
        mw = g.groupby("hour", observed=True)["mw"].sum().reindex(idx, fill_value=0.0)
        lmp = g.groupby("hour", observed=True)["lmp"].first().reindex(idx).ffill().bfill()
        units = {
            str(uid): (
                u.groupby("hour", observed=True)["mw"]
                .sum()
                .reindex(idx, fill_value=0.0)
                .to_numpy(dtype=float)
            )
            for uid, u in g.groupby("unit_id", observed=True)
        }
        out[int(code)] = {
            "mw": mw.to_numpy(dtype=float),
            "units": units,
            "lmp": lmp.to_numpy(dtype=float),
            "zone": str(g["zone"].iloc[0]),
        }
    return out


def plant_offer(
    units: dict[str, np.ndarray],
    mw: np.ndarray,
    lmp: np.ndarray,
    gas: np.ndarray,
    hr: float,
    vom: float,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Return ``(offer_start, offer_direct, diagnostics)`` for one plant.

    The offer that decides whether a plant STARTS is its cheapest tranche's, so
    the recovery runs per tranche and the plant offer is the per-hour minimum
    over them. For tranche ``u``, the hours in which it is loaded strictly
    between zero and its own maximum are the hours LP optimality makes it
    marginal, so its offer there EQUALS the zonal LMP; writing the offer as
    ``HR x gas(t) + k_u`` (delivered fuel is the only time-varying term in a gas
    CT's marginal cost), ``k_u`` is the median of ``lmp(t) - HR x gas(t)`` over
    those hours.

    ``hr`` is the plant's capacity-weighted model heat rate, shared by every
    tranche, so a tranche's own heat-rate markup lands in its ``k_u`` rather than
    in its gas slope. ``spread_iqr`` reports how well that form holds: a tight
    interquartile range on the per-hour estimate confirms the recovery, a wide
    one says the tranche's loading is not a clean price rule and the number
    carries that caveat.

    ``on_violation`` is the self-test: the share of hours in which the plant is
    online while the recovered offer sits ABOVE the LMP. A recovered offer that
    is right should almost never do that, so a low rate validates the recovery
    and a high one means something other than price (a floor, a reserve posture,
    transmission) is driving this plant's commitment.
    """
    direct = hr * gas + vom
    offers: list[np.ndarray] = []
    ks: list[float] = []
    iqrs: list[float] = []
    n_revealed = 0
    for arr in units.values():
        cap = float(arr.max())
        if cap <= _ONLINE_MW:
            continue
        interior = (arr > _ONLINE_MW) & (arr < 0.99 * cap)
        est = lmp[interior] - hr * gas[interior]
        if est.size >= MIN_MARGINAL_HOURS:
            k = float(np.median(est))
            iqrs.append(float(np.percentile(est, 75) - np.percentile(est, 25)))
            n_revealed += 1
        else:
            k = float(vom)
        ks.append(k)
        offers.append(hr * gas + k)
    if not offers:
        offers = [direct]
        ks = [float(vom)]
    offer = np.min(np.vstack(offers), axis=0)

    cap_p = float(mw.max())
    on = mw > max(_ONLINE_MW, 0.01 * cap_p) if cap_p > 0 else np.zeros_like(mw, bool)
    diag = {
        "n_tranches": len(offers),
        "n_tranches_revealed": n_revealed,
        "k_min": float(min(ks)),
        "k_direct": float(vom),
        "spread_iqr": float(np.median(iqrs)) if iqrs else float("nan"),
        "used_revealed": bool(n_revealed > 0),
        "on_violation": float((offer[on] > lmp[on]).mean()) if on.any() else float("nan"),
    }
    return offer, direct, diag


def _block_stats(blocks: list[dict]) -> dict:
    """Return the profitability summary of the runs the model never begins."""
    if not blocks:
        return {}
    ma = np.array([b["block_margin_actual"] for b in blocks])
    mm = np.array([b["block_margin_model"] for b in blocks])
    mz = np.array([b["block_margin_zonal"] for b in blocks])
    fh = np.array([b["first_hour_margin_actual"] for b in blocks])
    hrs = np.array([b["hours"] for b in blocks], dtype=float)
    mwh = np.array([b["mwh"] for b in blocks])
    return {
        "n_blocks": len(blocks),
        "mean_hours": float(hrs.mean()),
        "share_block_profitable_actual": float((ma > 0).mean()),
        "share_block_profitable_model": float((mm > 0).mean()),
        "share_block_profitable_zonal": float((mz > 0).mean()),
        "total_block_margin_zonal_musd": float(mz.sum()) / 1e6,
        "median_block_margin_per_mwh_zonal": float(mz.sum() / mwh.sum())
        if mwh.sum()
        else float("nan"),
        "share_first_hour_profitable_actual": float((fh > 0).mean()),
        "share_first_hour_loss_block_profit": float(((fh <= 0) & (ma > 0)).mean()),
        "total_block_margin_actual_musd": float(ma.sum()) / 1e6,
        "total_block_margin_model_musd": float(mm.sum()) / 1e6,
        "median_block_margin_actual_usd": float(np.median(ma)),
        "median_block_margin_per_mwh_actual": float(ma.sum() / mwh.sum())
        if mwh.sum()
        else float("nan"),
    }


def _pos_stats(rows: list[dict]) -> dict:
    """Return the median actual-DA margin by position within a missed run."""
    pooled: dict[int, list[float]] = {}
    for r in rows:
        for p, vals in r["pos_margin"].items():
            pooled.setdefault(int(p), []).extend(vals)
    return {
        str(p): {"n": len(v), "median_margin": float(np.median(v))}
        for p, v in sorted(pooled.items())
    }


def analyse(bundle: Path, year: int) -> dict:
    """Return the missed-start economics for one bundle-year."""
    pure, _vom_fleet = pure_ct_plants(year)
    bench = load_bench(REPO, "NYISO", year)
    model = model_plant_series(bundle, year)
    hr_by_plant, vom_by_plant = model_heat_rates(year)
    gas_by_zone = downstate_ct_gas_hourly(year) or {}
    gas_mean = (
        np.mean(list(gas_by_zone.values()), axis=0) if gas_by_zone else np.zeros(8760)
    )

    lmp_actual = pd.read_parquet(LMP_PATH)
    lmp_actual = lmp_actual[lmp_actual["year"] == year].sort_values("hour")
    da_hub = lmp_actual["da"].to_numpy(dtype=float)[:8760]
    premium = measured_locational_premium(year)

    rows: list[dict] = []
    per_plant: list[dict] = []
    n_gas_fallback = 0
    for pid, rec in bench.items():
        code = int(pid)
        if rec["group"] != PEAKER_CLASS or code not in pure or code not in model:
            continue
        meas = np.asarray(rec["mw"], dtype=float)[:8760]
        if meas.max() <= _ONLINE_MW:
            continue
        m = model[code]
        mw, lmp_m = m["mw"][:8760], m["lmp"][:8760]
        if mw.size < 8760:
            continue
        hr = hr_by_plant.get(code)
        if hr is None:
            continue
        gas = gas_by_zone.get(m["zone"])
        if gas is None:
            gas = gas_mean
            n_gas_fallback += 1
        gas = np.asarray(gas, dtype=float)[:8760]

        prem = premium.get(_ZONE_TO_RTD.get(m["zone"], ""), 0.0)
        da, da_zonal = da_hub, da_hub + prem
        bar = _plant_bar(meas)
        meas_on = meas >= bar
        model_on = mw >= bar
        meas_starts = starts(meas_on)
        missed = meas_starts & ~model_on

        offer, offer_direct, diag = plant_offer(
            m["units"], mw, lmp_m, gas, hr, float(vom_by_plant.get(code, 0.0))
        )
        # 2x2: each price series against each cost basis, so a price error and a
        # cost error can be told apart rather than confounded. ``offer`` is the
        # model's own offer (tranche markup included, recovered from the solve);
        # ``offer_direct`` is the plant's bare SRMC (HR x gas + VOM), the same
        # basis nyiso-88 §3 measured the fleet's margin on.
        idx = np.flatnonzero(missed)
        margin_model = lmp_m - offer
        margin_actual = da - offer
        margin_model_srmc = lmp_m - offer_direct
        margin_actual_srmc = da - offer_direct
        margin_actual_srmc_zonal = da_zonal - offer_direct

        # The energy at stake: measured MWh inside runs that BEGIN at a start
        # the model never makes. This converts the start deficit into the units
        # the level gap is quoted in.
        run_id = np.cumsum(starts(meas_on)) * meas_on
        missed_ids = sorted(set(run_id[idx].tolist()))
        in_missed_run = meas_on & np.isin(run_id, missed_ids)

        # THE BLOCK TEST. An hour-by-hour merit screen judges the START hour;
        # a day-ahead commitment judges the whole BLOCK it commits to. For every
        # run the model never begins, integrate the measured MWh against price
        # minus the plant's own bare SRMC over the entire run. If those blocks
        # are profitable in total while their first hours are not, the fleet is
        # recovering a start over a committed block — something an hourly LP
        # screen structurally cannot see. If they are unprofitable in total, the
        # fleet is running for a genuinely non-energy reason.
        blocks: list[dict] = []
        for rid in missed_ids:
            sel = run_id == rid
            m_run = meas[sel]
            blocks.append(
                {
                    "hours": int(sel.sum()),
                    "mwh": float(m_run.sum()),
                    "block_margin_actual": float(
                        ((da[sel] - offer_direct[sel]) * m_run).sum()
                    ),
                    "block_margin_model": float(
                        ((lmp_m[sel] - offer_direct[sel]) * m_run).sum()
                    ),
                    "block_margin_zonal": float(
                        ((da_zonal[sel] - offer_direct[sel]) * m_run).sum()
                    ),
                    "first_hour_margin_actual": float(da[sel][0] - offer_direct[sel][0]),
                }
            )
        # Margin by position in the run: the head-of-run signature, if there is
        # one, shows up here as negative early positions turning positive later.
        pos_margin: dict[int, list[float]] = {}
        for rid in missed_ids:
            sel = np.flatnonzero(run_id == rid)
            for p, t in enumerate(sel[:12], start=1):
                pos_margin.setdefault(p, []).append(float(da[t] - offer_direct[t]))
        rows.append(
            {
                "plant_code": code,
                "zone": m["zone"],
                "meas_starts": int(meas_starts.sum()),
                "model_starts": int(starts(model_on).sum()),
                "missed_starts": int(missed.sum()),
                "margins_model": margin_model[idx],
                "margins_actual": margin_actual[idx],
                "margins_model_srmc": margin_model_srmc[idx],
                "margins_actual_srmc": margin_actual_srmc[idx],
                "margins_actual_srmc_zonal": margin_actual_srmc_zonal[idx],
                "loc_premium": prem,
                "missed_run_hours": int(in_missed_run.sum()),
                "missed_run_mwh": float(meas[in_missed_run].sum()),
                "blocks": blocks,
                "pos_margin": pos_margin,
                "meas_online_h": int(meas_on.sum()),
                "meas_mwh": float(meas[meas_on].sum()),
                "mean_mw_when_on_model": (
                    float(mw[model_on].mean()) if model_on.any() else 0.0
                ),
                "mean_mw_when_on_meas": float(meas[meas_on].mean()),
                "offer_direct_gap": float(np.median(offer - offer_direct)),
                **diag,
            }
        )
        per_plant.append(rows[-1])

    if not rows:
        return {"year": year, "plants": 0}

    def _pool(key: str) -> np.ndarray:
        return np.concatenate([r[key] for r in rows])

    def _split(margins: np.ndarray) -> dict:
        n = margins.size
        if n == 0:
            return {}
        a = int((margins >= 0).sum())
        b = int(((margins < 0) & (margins >= -NEAR_MISS_USD)).sum())
        c = int((margins < -NEAR_MISS_USD).sum())
        return {
            "n": n,
            "a_in_merit": a,
            "a_share": a / n,
            "b_near_miss": b,
            "b_share": b / n,
            "c_deep": c,
            "c_share": c / n,
            "median_margin": float(np.median(margins)),
            "p25_margin": float(np.percentile(margins, 25)),
            "p75_margin": float(np.percentile(margins, 75)),
            "p90_shortfall": float(-np.percentile(margins, 10)),
        }

    return {
        "year": year,
        "plants": len(rows),
        "meas_starts": sum(r["meas_starts"] for r in rows),
        "model_starts": sum(r["model_starts"] for r in rows),
        "missed_starts": sum(r["missed_starts"] for r in rows),
        "gas_zone_fallback_plants": n_gas_fallback,
        "plants_direct_fallback": sum(1 for r in rows if not r["used_revealed"]),
        "median_revealed_intercept": float(
            np.median([r["k_min"] for r in rows if np.isfinite(r["k_min"])])
        ),
        "median_revealed_iqr": float(
            np.nanmedian([r["spread_iqr"] for r in rows])
        ),
        "median_on_violation": float(np.nanmedian([r["on_violation"] for r in rows])),
        "median_offer_minus_direct": float(np.median([r["offer_direct_gap"] for r in rows])),
        "missed_run_hours": sum(r["missed_run_hours"] for r in rows),
        "missed_run_twh": sum(r["missed_run_mwh"] for r in rows) / 1e6,
        "meas_online_h": sum(r["meas_online_h"] for r in rows),
        "meas_twh": sum(r["meas_mwh"] for r in rows) / 1e6,
        "median_offer_minus_direct_revealed": (
            float(
                np.median(
                    [r["offer_direct_gap"] for r in rows if r["used_revealed"]]
                )
            )
            if any(r["used_revealed"] for r in rows)
            else float("nan")
        ),
        "blocks": _block_stats([b for r in rows for b in r["blocks"]]),
        "pos_margin": _pos_stats(rows),
        "model_offer__model_price": _split(_pool("margins_model")),
        "model_offer__actual_price": _split(_pool("margins_actual")),
        "direct_srmc__model_price": _split(_pool("margins_model_srmc")),
        "direct_srmc__actual_price": _split(_pool("margins_actual_srmc")),
        "direct_srmc__actual_price_zonal": _split(_pool("margins_actual_srmc_zonal")),
        "locational_premium": premium,
        "per_plant": [
            {
                k: v
                for k, v in r.items()
                if not isinstance(v, np.ndarray) and k not in ("blocks", "pos_margin")
            }
            for r in per_plant
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """Run the missed-start economics probe and print the three-way split."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, type=Path)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args(argv)

    out = []
    for year in args.years:
        if not (args.bundle / "dispatch" / f"{year}_P1.parquet").exists():
            print(f"  (skip {year}: dispatch not on disk)")
            continue
        out.append(analyse(args.bundle, year))

    print("--- fleet and start counts (pure-CT plants, common physical bar) ---")
    print(f"{'year':>6} {'plants':>7} {'meas starts':>12} {'model starts':>13} {'missed':>8}")
    for r in out:
        print(
            f"{r['year']:>6} {r['plants']:>7} {r['meas_starts']:>12} "
            f"{r['model_starts']:>13} {r['missed_starts']:>8}"
        )

    print("\n--- offer recovery (revealed vs direct assembly) ---")
    print(
        f"{'year':>6} {'direct-fallback':>16} {'median k':>10} {'median IQR':>12} "
        f"{'median offer-direct':>20} {'on-hour violation':>19}"
    )
    for r in out:
        print(
            f"{r['year']:>6} {r['plants_direct_fallback']:>16} "
            f"{r['median_revealed_intercept']:>10.2f} {r['median_revealed_iqr']:>12.2f} "
            f"{r['median_offer_minus_direct']:>+20.2f} {r['median_on_violation']:>18.1%}"
        )

    print("\n--- the energy at stake: runs the model never begins ---")
    print(
        f"{'year':>6} {'meas online h':>14} {'h in missed runs':>17} "
        f"{'meas TWh':>10} {'TWh in missed runs':>19}"
    )
    for r in out:
        print(
            f"{r['year']:>6} {r['meas_online_h']:>14} {r['missed_run_hours']:>17} "
            f"{r['meas_twh']:>10.3f} {r['missed_run_twh']:>19.3f}"
        )

    for key, title in (
        ("model_offer__model_price", "model OFFER vs the MODEL's own P1 LMP  (what the LP decided)"),
        ("model_offer__actual_price", "model OFFER vs the ACTUAL NYISO DA price  (is the price the error?)"),
        ("direct_srmc__model_price", "bare SRMC vs the MODEL's own P1 LMP  (is the offer markup the error?)"),
        ("direct_srmc__actual_price", "bare SRMC vs the ACTUAL NYISO DA price  (is the real start economic at all?)"),
        ("direct_srmc__actual_price_zonal", "bare SRMC vs ACTUAL DA + measured NYC/LI premium  (locational robustness)"),
    ):
        print(f"\n--- {title} ---")
        print(
            f"{'year':>6} {'n':>7} {'(a) in merit':>14} {'(b) < $5 out':>14} "
            f"{'(c) deep':>12} {'median margin':>15} {'p90 shortfall':>15}"
        )
        for r in out:
            s = r.get(key) or {}
            if not s:
                continue
            print(
                f"{r['year']:>6} {s['n']:>7} {s['a_in_merit']:>7} ({s['a_share']:>5.1%}) "
                f"{s['b_near_miss']:>7} ({s['b_share']:>5.1%}) "
                f"{s['c_deep']:>5} ({s['c_share']:>5.1%}) "
                f"{s['median_margin']:>+15.2f} {s['p90_shortfall']:>15.2f}"
            )

    print("\n--- THE BLOCK TEST: are the runs the model never begins profitable AS BLOCKS? ---")
    print(
        f"{'year':>6} {'blocks':>7} {'mean h':>7} {'1st h profitable':>17} "
        f"{'BLOCK profitable':>17} {'loss-lead, block+':>18} {'$/MWh over SRMC':>17} "
        f"{'total $M':>9} {'BLOCK+ zonal':>13} {'$/MWh zonal':>12}"
    )
    for r in out:
        b = r.get("blocks") or {}
        if not b:
            continue
        print(
            f"{r['year']:>6} {b['n_blocks']:>7} {b['mean_hours']:>7.2f} "
            f"{b['share_first_hour_profitable_actual']:>16.1%} "
            f"{b['share_block_profitable_actual']:>16.1%} "
            f"{b['share_first_hour_loss_block_profit']:>17.1%} "
            f"{b['median_block_margin_per_mwh_actual']:>+17.2f} "
            f"{b['total_block_margin_actual_musd']:>+9.1f} "
            f"{b['share_block_profitable_zonal']:>12.1%} "
            f"{b['median_block_margin_per_mwh_zonal']:>+12.2f}"
        )

    print("\n--- actual-DA margin over bare SRMC by POSITION in a missed run ($/MWh) ---")
    print(f"{'year':>6} " + " ".join(f"{'h'+str(p):>7}" for p in range(1, 9)))
    for r in out:
        pm = r.get("pos_margin") or {}
        cells = " ".join(
            f"{pm.get(str(p), {}).get('median_margin', float('nan')):>+7.1f}"
            for p in range(1, 9)
        )
        print(f"{r['year']:>6} {cells}")

    if args.json_out:
        args.json_out.write_text(json.dumps(out, indent=2, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
