#!/usr/bin/env python3
"""ercot-232 Phase-0: what SETS the keeper's 21 spurious mid-band hours, and
is the seasonal end-of-season term a live object?

Handoff moves (1) and (2), both answered WITHOUT a solve — every series is read
from artifacts already committed at HEAD:

* the keeper's own hourly sidecars (``results/calibration/ercot231_tiegtc_full``)
  and the immediately-prior keeper's (``ercot223_release_arm``) as the A/B
  comparator — the static-TTC / load-share-spread lineage;
* the hub RT actual (``_actual``) and the demand-weighted P1 zonal price
  (``_member``), both the FROZEN ercot221_gates constructions, so the
  measurement rides the exact conventions the scored criteria ride;
* ERCOT NP6-86-CD SCED Shadow Prices and Binding Transmission Constraints, for
  the measured NE_LOB truth. The SCED wall-clock -> hour-of-year mapping is
  copied EXACTLY from ``scripts/data/curate_gtc_limits.py::_to_hourly`` (the
  fixed non-leap calendar), so model hour i and measured hour i are the same
  clock.

Move (1) asks what the 21 hours are made of. Move (2) asks whether the ONLY
un-adjudicated adaptive successor — a seasonal end-of-season term — has a
residual to grip. Both are decided on measurement here; no mechanism is built,
no ``ScenarioConfig`` field is added, no LP is run and no model input is
written (rule 28(b): a verdict is minted for each, rule 28(c) is not engaged).

Output: ``results/calibration/ercot232_gspur_phase0.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ercot221_gates import MID_BAND, _actual, _member  # noqa: E402  (frozen)

YEAR = 2023
KEEPER = "ercot231_tiegtc_full"  # 2026-08-24-231-tie-zone-measured
PRIOR = "ercot223_release_arm"  # 2026-08-20-ercot223-arm-eventrelease
# The NE_LOB boundary as the topology models it (constants.ERCOT_GTC_LINK_MAP:
# NE_LOB -> [(("Northeast", "North"), 1.0)]). The export link's dual IS the
# North-minus-Northeast price separation, so that difference is the model-side
# analogue of the measured NE_LOB shadow price.
GTC = "NE_LOB"
LINK = ("North", "Northeast")
# Month starts on the fixed non-leap calendar the model and the curation share.
_MC = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
_MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
        "Sep", "Oct", "Nov", "Dec"]


def _sidecar(bundle: str, name: str) -> pd.DataFrame:
    """Read one committed P1 hourly sidecar of ``bundle`` for :data:`YEAR`."""
    df = pd.read_parquet(REPO / f"results/calibration/{bundle}/hourly/{name}_{YEAR}.parquet")
    return df[(df["year"] == YEAR) & (df["pass"] == "P1")].copy()


def _zonal_price(bundle: str) -> pd.DataFrame:
    """Per-zone P1 price, hour x zone."""
    d = _sidecar(bundle, "system")
    return d.pivot_table(index="hour", columns="zone", values="price")


def _link_dual(bundle: str) -> np.ndarray:
    """Model-side NE_LOB export dual = price(North) - price(Northeast).

    Positive means the Northeast->North export link is binding (the lobe is
    trapped behind it); negative means the reverse import link is binding.
    """
    zp = _zonal_price(bundle)
    return (zp[LINK[0]] - zp[LINK[1]]).reindex(range(8760)).to_numpy(float)


def _measured_nelob() -> tuple[np.ndarray, np.ndarray]:
    """Hourly-equivalent measured NE_LOB dual, and the binding-interval share.

    The hourly analogue of an hourly LP's constraint dual is the shadow price
    averaged over ALL SCED intervals in the hour (non-binding intervals at 0),
    NOT the average over binding intervals only — the latter overstates a
    constraint that binds for part of the hour.
    """
    src = REPO / f"data/raw/iso-specific-transmission/SCEDBTCNP686_SCEDBTCNP686_{YEAR}.parquet"
    d = pd.read_parquet(src)
    ts = pd.to_datetime(d["SCEDTimeStamp"], format="%m/%d/%Y %H:%M:%S")
    d = d.assign(ts=ts)
    d = d[(d.ts.dt.year == YEAR) & ~((d.ts.dt.month == 2) & (d.ts.dt.day == 29))]
    d["hoy"] = (_MC[d.ts.dt.month - 1] + d.ts.dt.day - 1) * 24 + d.ts.dt.hour

    intervals = d.groupby("hoy")["ts"].nunique()  # denominator: all SCED runs
    binding = d[(d["ConstraintName"] == GTC) & (d["ShadowPrice"] > 0)]
    dual = pd.Series(0.0, index=range(8760))
    dual.update(binding.groupby("hoy")["ShadowPrice"].sum() / intervals)
    frac = pd.Series(0.0, index=range(8760))
    frac.update(binding.groupby("hoy")["ts"].nunique() / intervals)
    return (dual.reindex(range(8760)).fillna(0.0).to_numpy(float),
            frac.reindex(range(8760)).fillna(0.0).to_numpy(float))


def _stamp(h: int) -> tuple[str, int]:
    """(ISO date, hour-of-day) of model hour ``h`` on the fixed calendar."""
    day, hod = h // 24, h % 24
    mo = int(np.searchsorted(_MC, day, side="right"))
    return f"{YEAR}-{mo:02d}-{int(day - _MC[mo - 1] + 1):02d}", hod


def _spur(model: np.ndarray, actual: np.ndarray) -> list[int]:
    """Mid-band hours the model prints where the actual sat below the band."""
    mm, aa = np.nan_to_num(model), np.nan_to_num(actual, nan=1e9)
    return [int(h) for h in np.where(
        (mm >= MID_BAND[0]) & (mm <= MID_BAND[1]) & (aa < MID_BAND[0]))[0]]


def move1(out: dict) -> None:
    """What sets the 21 spurious mid-band hours."""
    keep, prior = _member(REPO / "results/calibration" / KEEPER, YEAR), None
    prior = _member(REPO / "results/calibration" / PRIOR, YEAR)
    act = _actual(YEAR)
    spur = _spur(keep["price"], act)
    ctl = set(_spur(prior["price"], act))
    new = [h for h in spur if h not in ctl]

    zp = _zonal_price(KEEPER)
    others = [z for z in zp.columns if z != "Northeast"]
    gap_k, gap_p = _link_dual(KEEPER), _link_dual(PRIOR)
    meas, frac = _measured_nelob()

    rows = []
    for h in spur:
        date, hod = _stamp(h)
        rows.append({
            "hour": h, "date": date, "hod": hod, "new_vs_prior": h in new,
            "model_price": round(float(keep["price"][h]), 2),
            "lam": round(float(keep["lam"][h]), 2),
            "ordc_adder": round(float(keep["adder"][h]), 2),
            "actual_rt": round(float(act[h]), 2),
            "northeast_price": round(float(zp["Northeast"][h]), 2),
            "rest_of_ercot_price": round(float(zp[others].median(axis=1)[h]), 2),
            "model_nelob_dual": round(float(gap_k[h]), 2),
            "measured_nelob_dual": round(float(meas[h]), 2),
            "measured_nelob_binding": bool(frac[h] > 0),
        })

    lam_made = sum(1 for h in spur if keep["lam"][h] >= MID_BAND[0])
    out["move1_gspur_anatomy"] = {
        "question": "what sets the keeper's spurious mid-band hours",
        "spur_hours": spur,
        "spur_count": len(spur),
        "new_vs_prior_keeper": new,
        "prior_keeper_spur": sorted(ctl),
        "channel": {
            "lambda_made": lam_made, "adder_carried": len(spur) - lam_made,
            "shed_hours": int(sum(1 for h in spur if keep["slack"][h] > 1e-6)),
        },
        "season_span": [rows[0]["date"], rows[-1]["date"]],
        "hour_of_day": sorted(r["hod"] for r in rows),
        "northeast_decoupled_at_spur": {
            "model_nelob_dual_p50": round(float(np.median(gap_k[spur])), 2),
            "measured_nelob_dual_p50": round(float(np.median(meas[spur])), 2),
            "measured_binding_hours": int((frac[spur] > 0).sum()),
            "measured_binding_hours_of_the_new": int((frac[new] > 0).sum()),
        },
        "per_hour": rows,
    }

    # The whole-year NE_LOB object: is the placement right in aggregate?
    agg = {}
    for label, g in ((PRIOR, gap_p), (KEEPER, gap_k)):
        on_g, on_m = g > 1.0, frac > 0
        both = on_g & on_m
        agg[label] = {
            "model_congested_hours": int(on_g.sum()),
            "measured_binding_hours": int(on_m.sum()),
            "hours_both": int(both.sum()),
            "hours_model_only": int((on_g & ~on_m).sum()),
            "hours_measured_only": int((~on_g & on_m).sum()),
            "model_annual_dual_sum": round(float(g[on_g].sum()), 0),
            "pct_of_measured_annual": round(float(g[on_g].sum() / meas.sum() * 100), 1),
            "model_p50_on_agreeing": round(float(np.median(g[both])), 2) if both.any() else None,
            "measured_p50_on_agreeing": round(float(np.median(meas[both])), 2) if both.any() else None,
            "corr_model_vs_measured": round(float(np.corrcoef(g, meas)[0, 1]), 3),
        }
    agg["measured_annual_dual_sum"] = round(float(meas.sum()), 0)
    out["move1_nelob_whole_year"] = agg


def move2(out: dict) -> None:
    """Is there a fall-shape residual for a seasonal end-of-season term?"""
    keep = _member(REPO / "results/calibration" / KEEPER, YEAR)
    act = _actual(YEAR)
    price, dem = keep["price"], keep["demand"]
    month = np.searchsorted(_MC, np.arange(8760) // 24, side="right")

    monthly = []
    for m in range(1, 13):
        k = month == m
        w = dem[k]
        a_m = float((act[k] * w).sum() / w.sum())
        p_m = float((price[k] * w).sum() / w.sum())
        monthly.append({
            "month": _MON[m - 1],
            "actual_mean": round(a_m, 2), "model_mean": round(p_m, 2),
            "bias_pct": round((p_m - a_m) / a_m * 100, 1),
            "actual_hours_gt200": int((act[k] > 200).sum()),
            "model_hours_gt200": int((price[k] > 200).sum()),
            "mwh_weighted_error_musd": round(float(((price[k] - act[k]) * w).sum() / 1e6), 1),
        })
    under = {r["month"]: r["mwh_weighted_error_musd"] for r in monthly
             if r["mwh_weighted_error_musd"] < 0}
    tot_under = sum(under.values())

    # The adaptive floor's own seasonal envelope, and whether it BINDS in the
    # fall — an armed floor only moves price where storage is marginal at it.
    ad = _sidecar(KEEPER, "adaptive") if "pass" in pd.read_parquet(
        REPO / f"results/calibration/{KEEPER}/hourly/adaptive_{YEAR}.parquet"
    ).columns else pd.read_parquet(
        REPO / f"results/calibration/{KEEPER}/hourly/adaptive_{YEAR}.parquet")
    floor = ad.set_index("hour")["floor_usd"].reindex(range(8760)).fillna(0.0).to_numpy(float)
    st = _sidecar(KEEPER, "storage").groupby("hour")["discharge_mw"].sum()
    dis = st.reindex(range(8760)).fillna(0.0).to_numpy(float)

    env = []
    for m in range(1, 13):
        k = month == m
        armed = k & (floor > 1e-6)
        env.append({
            "month": _MON[m - 1],
            "floor_mean": round(float(floor[k].mean()), 2),
            "floor_max": round(float(floor[k].max()), 2),
            "armed_hours": int(armed.sum()),
            "armed_and_discharging": int((armed & (dis > 1e-6)).sum()),
            "price_pinned_at_floor": int((armed & (np.abs(price - floor) < 1.0)).sum()),
        })

    fall = np.isin(month, [10, 11, 12])
    w = dem[fall]
    out["move2_seasonal_end_of_season"] = {
        "question": "does a fall-shape residual exist for an end-of-season term",
        "monthly": monthly,
        "share_of_annual_underpricing_pct": {
            k: round(v / tot_under * 100, 1) for k, v in under.items()},
        "adaptive_floor_envelope": env,
        "fall_materiality": {
            "oct_dec_armed_hours": int((fall & (floor > 1e-6)).sum()),
            "oct_dec_price_pinned_at_floor_hours": int(
                (fall & (np.abs(price - floor) < 1.0)).sum()),
            "oct_dec_model_mean": round(float((price[fall] * w).sum() / w.sum()), 2),
            "oct_dec_actual_mean": round(float((act[fall] * w).sum() / w.sum()), 2),
            "oct_dec_bias_pct": round(float(
                ((price[fall] * w).sum() / w.sum() - (act[fall] * w).sum() / w.sum())
                / ((act[fall] * w).sum() / w.sum()) * 100), 1),
            "oct_dec_share_of_annual_underpricing_pct": round(
                abs(float(((price[fall] - act[fall]) * dem[fall]).sum()))
                / abs(float(((price - act) * dem).sum())) * 100, 1),
        },
    }


def main() -> None:
    """Run both phase-0 measurements and write the probe JSON."""
    out: dict = {
        "probe": "ercot232_gspur_phase0",
        "charter": "handoff moves (1) G-SPUR diagnosis and (2) the seasonal "
                   "end-of-season card — committed artifacts only, no solve",
        "keeper": KEEPER, "prior_keeper": PRIOR, "year": YEAR,
        "measured_source": "ERCOT NP6-86-CD SCED Shadow Prices and Binding "
                           "Transmission Constraints "
                           f"(data/raw/iso-specific-transmission/SCEDBTCNP686_SCEDBTCNP686_{YEAR}.parquet)",
    }
    move1(out)
    move2(out)
    dest = REPO / "results/calibration/ercot232_gspur_phase0.json"
    dest.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
