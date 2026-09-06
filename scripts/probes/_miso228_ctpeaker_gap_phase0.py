"""miso-228 phase 0 — is MISO's CT_PEAKER under-production an OFFER problem or a PRICE problem? Zero LP.

miso-227 scored NOT-YET on ONE cell: CT_PEAKER-2023 at -8.29 TWh against a
+/-8.00 band. But the arm did not create it — the incumbent keeper sits at
-7.985 with 0.015 TWh of headroom, and MISO under-produces CT_PEAKER by
5.4-8.0 TWh in EVERY year (2023 9.053 vs 17.038, 2024 13.117 vs 19.225, 2025
13.888 vs 19.291). The owner's decision (2026-09-06) is rule 1 [R-STRUCT]'s own
prescription: keep the structural seam mechanism and FIX THE ROOT CAUSE.

This is the root cause's phase 0, and it asks the one question that partitions
the search before any solve is spent:

    Would the model's OWN CT_PEAKER offer stack produce the measured 17.0 TWh if
    it faced the MEASURED price instead of the model's price?

* If YES -> the offers are right and the model's PRICE (or what clears against
  it) is the defect. The lever is in price formation, not in the CT fleet.
* If NO  -> the offer stack itself cannot reach the measured energy at any
  price the market actually printed, and the lever is the CT representation
  (offer level, availability, capacity, or a duty the model does not carry).

Method, entirely from committed artifacts plus one on-recipe ``build_year``
rebuild (no LP): take every CT_PEAKER tranche's assembled P1 offer and its
hourly availability-scaled capacity, and integrate the energy that is IN MERIT
hour by hour against (a) the keeper's own P1 hub price and (b) the MEASURED
MISO-Indiana hub price. This is an upper bound in both cases — it ignores
commitment, min-up/down, reserve duty and the network, so the LP realizes some
fraction — but the CONTRAST between the two columns is the diagnostic, and it is
basis-consistent because the same stack is cleared twice.

Reported alongside, because they bound the alternative explanations:
  * installed CT_PEAKER capacity and the implied capacity factors, model vs
    actual, so a pure availability/capacity shortfall is visible;
  * the offer distribution against the price distribution (how much CT capacity
    sits under each price threshold), which says whether the stack is merely
    mispriced or structurally out of reach;
  * the band split, since 27.5 % of the model's CT energy is the committed
    (forced) band and the `peak` tranche produces 0.001 TWh.

Zero-LP. Rule 22 [R-HOLDOUT]: 2023-2025 only. Writes
``_miso228_ctpeaker_gap.json``.
"""

from __future__ import annotations

import json
import pathlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402

# The helper module pins a since-PRUNED bundle (miso132_ccmin_B) under rule 15's
# keeper-only retention, so its BUNDLE is repointed at the CURRENT designated
# keeper before anything reads it. build_year() and keeper_config() both resolve
# through this module global, so one assignment fixes both.
_m134.BUNDLE = pathlib.Path(__file__).resolve().parents[2] / (
    "results/calibration/miso220_nonsteamlift_B"
)
build_year, keeper_config = _m134.build_year, _m134.keeper_config
from _miso224_floor_anatomy_phase0 import actual_zone_price  # noqa: E402

KEEPER = REPO / "results/calibration/miso220_nonsteamlift_B"
OUT = REPO / "results/calibration/_miso228_ctpeaker_gap.json"
HOURS, ZONE = 8760, "MISO-Indiana"
YEARS = (2023, 2024, 2025)
#: Committed C1 actuals (bench classFull), for the gap line.
ACTUAL = {2023: 17.038, 2024: 19.225, 2025: 19.291}


def _keeper_price(year: int) -> np.ndarray:
    s = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    s = s[(s["pass"] == "P1") & (s["zone"] == ZONE)].sort_values("hour")
    return s["price"].to_numpy(float)


def _keeper_class_mw(year: int, klass: str) -> np.ndarray:
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & (c["klass"] == klass)]
    return (
        c.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    )


def analyse(year: int) -> dict:
    cfg = keeper_config()
    _raw, fleet, arrays, _fp, mc, _zones = build_year(cfg, year)
    grp = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    ct = grp == "CT_PEAKER"
    pmax = np.asarray(arrays.pmax, float)
    avail = np.asarray(arrays.availability, float)
    if avail.ndim == 1:
        avail = np.tile(avail[:, None], (1, HOURS))
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))

    cap = pmax[ct][:, None] * avail[ct]          # (n_ct, T) deliverable MW
    off = mc[ct]                                  # (n_ct, T) assembled P1 offer
    p_model = _keeper_price(year)
    p_act = actual_zone_price(year)[ZONE].to_numpy(float)[:HOURS]
    ok = np.isfinite(p_act)

    def in_merit_twh(price: np.ndarray, mask: np.ndarray) -> float:
        sel = (off[:, mask] < price[None, mask]) * cap[:, mask]
        return float(sel.sum()) / 1e6

    # Scale the actual-price column to a full year so the two columns compare
    # on the same hour count when the measured series has gaps.
    frac = float(ok.sum()) / HOURS
    twh_model_price = in_merit_twh(p_model, np.ones(HOURS, bool))
    twh_actual_price = in_merit_twh(p_act, ok) / max(frac, 1e-9)

    dispatched = _keeper_class_mw(year, "CT_PEAKER").sum() / 1e6
    nameplate = float(pmax[ct].sum())
    deliverable = float(cap.mean(1).sum())
    act = ACTUAL[year]

    # How much CT capacity sits under each price threshold (cap-weighted mean
    # offer per tranche, integrated) — the stack's reach.
    thresholds = (20.0, 30.0, 40.0, 50.0, 75.0, 100.0, 150.0)
    off_mean = off.mean(1)
    reach = {
        f"under_${int(t)}": round(float(cap.mean(1)[off_mean < t].sum()), 0)
        for t in thresholds
    }
    return {
        "year": year,
        "n_ct_tranches": int(ct.sum()),
        "nameplate_mw": round(nameplate, 0),
        "mean_deliverable_mw": round(deliverable, 0),
        "actual_twh": act,
        "model_dispatched_twh": round(dispatched, 3),
        "gap_twh": round(dispatched - act, 3),
        "implied_cf_actual": round(act * 1e6 / (nameplate * HOURS), 4),
        "implied_cf_model": round(dispatched * 1e6 / (nameplate * HOURS), 4),
        "static_in_merit_twh_at_MODEL_price": round(twh_model_price, 3),
        "static_in_merit_twh_at_ACTUAL_price": round(twh_actual_price, 3),
        "n_hours_actual_price_finite": int(ok.sum()),
        "offer_cap_weighted_mean": round(
            float((off_mean * cap.mean(1)).sum() / cap.mean(1).sum()), 2
        ),
        "offer_percentiles": {
            f"p{q}": round(float(np.percentile(off_mean, q)), 2)
            for q in (5, 25, 50, 75, 95)
        },
        "deliverable_mw_with_offer_reach": reach,
        "price_mean_model": round(float(p_model.mean()), 2),
        "price_mean_actual": round(float(np.nanmean(p_act)), 2),
    }


def main() -> int:
    rec = {
        "probe": (
            "miso-228 phase 0 — CT_PEAKER under-production: OFFER problem or "
            "PRICE problem? (zero LP, keeper recipe rebuilt)"
        ),
        "keeper": "2026-09-05-miso-220-nonsteam-lift",
        "question": (
            "would the model's OWN CT offer stack reach the measured energy if it "
            "faced the MEASURED price? YES => the defect is price formation; "
            "NO => the defect is the CT representation itself"
        ),
        "by_year": {},
    }
    for y in YEARS:
        rec["by_year"][str(y)] = analyse(y)
        r = rec["by_year"][str(y)]
        print(
            f"{y}: actual {r['actual_twh']:.3f} | model {r['model_dispatched_twh']:.3f} "
            f"| static@model_price {r['static_in_merit_twh_at_MODEL_price']:.3f} "
            f"| static@ACTUAL_price {r['static_in_merit_twh_at_ACTUAL_price']:.3f} "
            f"| nameplate {r['nameplate_mw']:.0f} MW | CF act {r['implied_cf_actual']:.3f} "
            f"model {r['implied_cf_model']:.3f}"
        )
    OUT.write_text(json.dumps(rec, indent=1))
    print(f"-> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
