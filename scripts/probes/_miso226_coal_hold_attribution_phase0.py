"""miso-226 phase 0 (queue item 2) — WHAT holds MISO's cheap-hour coal? Attribute it across the keeper's OWN armed coal commitment structure, with zero LP.

miso-225 G-3 killed the owner-ruled gas arm by 37 MW: coal fell **404 MW** in the
1,230 real sub-$20 hours against a static prediction of **-1,470 MW**, i.e.
**0.275x** — the SAME conversion ratio the bare-hub miso-224 arm measured (0.27x)
at 2.3x the fuel move.  So the hold scales with neither the fuel move nor the
price, and the keeper's own D-2 says it is NOT forcing (MISO COAL forced energy
0.30 / 0.34 / 0.17 % of the class, one ``reliability_floor`` mechanism).  The
FINDING named the successor object as the COMMITMENT structure and the queue
head made it item 2.

This is that object's phase 0, and it is answerable with no LP at all, because
the question is *which rows the static assumed it could displace*.  Two
measurements, both from committed artifacts plus one on-recipe fleet rebuild:

**(A) The keeper's cheap-hour coal, by BAND FAMILY** — straight off the
committed ``class_band_hourly_2023.parquet`` sidecar, no rebuild at all.  The
CAMPD per-plant binning splits every coal plant into a fuel-free price-taker
``mustrun`` band, a take-or-pay ``committed`` band, a rising ``econ*`` ramp and a
``peak`` rung (docs/binning-methodology.md).  Only rows whose OFFER a gas move
can outbid are displaceable at all.

**(B) WHICH rows the static displaced** — the miso-225 static re-merit re-run on
the same two bases (keeper vs the ruled hub+transport offer), but recording the
displaced coal MW **by band family** instead of only its total.  That is the
number that says whether the -1,470 MW the gate demanded was ever reachable, and
if it was, which band the LP refused to give up.

Rule 19 ``[R-ONE-MECH]`` is the point of the exercise: before anything is
proposed, enumerate what already holds this class.  Rule 29 clause 0: a zero-LP
phase 0 that can kill or reshape an arm before a solve is spent.

Zero-LP (one ``build_year`` fleet rebuild, no solve).  Rule 22 ``[R-HOLDOUT]``:
2023 only.  Writes ``_miso226_coal_hold_attribution.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from _miso224_floor_anatomy_phase0 import actual_zone_price  # noqa: E402
from _miso224_offer_decomposition_phase0 import (  # noqa: E402
    _month_of_hour,
    spot_gas_by_month,
)
from _miso224_static_remerit_phase0 import (  # noqa: E402
    COAL_CLASSES,
    HOURS,
    ZONE,
    fleet_dispatch,
    hh_by_month,
)

KEEPER = REPO / "results/calibration/miso220_nonsteamlift_B"
OUT = REPO / "results/calibration/_miso226_coal_hold_attribution.json"
YEAR = 2023
#: The realized LP response miso-225 measured, for the reconciliation line.
MISO225_REALIZED_COAL_MW = -404.0
MISO225_STATIC_COAL_MW = -1470.0


def _family(unit_id: str) -> str:
    """Band family from a tranche's unit id suffix (offer_surfaces._lowcurve_row_family)."""
    sfx = str(unit_id).rpartition("_")[2]
    if sfx == "mustrun":
        return "mustrun"
    if sfx == "committed":
        return "committed"
    if sfx == "peak":
        return "peak"
    if sfx.startswith("econ"):
        return "econ"
    return "other"


def part_a() -> dict:
    """The keeper's own cheap-hour coal, by band family — committed sidecar only."""
    act = actual_zone_price(YEAR)[ZONE].to_numpy(float)
    sel = np.isfinite(act) & (act < 20.0)
    c = pd.read_parquet(KEEPER / f"hourly/class_band_hourly_{YEAR}.parquet")
    c = c[(c["pass"] == "P1") & c["klass"].astype(str).str.startswith("COAL")]
    fam = c["band"].astype(str).map(
        lambda b: b if b in ("mustrun", "committed", "peak") else "econ"
    )
    piv = (
        c.assign(fam=fam)
        .pivot_table(index="hour", columns="fam", values="mw", aggfunc="sum")
        .reindex(range(HOURS))
        .fillna(0.0)
    )
    tot = piv.sum(axis=1)
    fams = ["mustrun", "committed", "econ", "peak"]
    out = {
        "n_cheap_hours": int(sel.sum()),
        "coal_mw_all_hours": round(float(tot.mean()), 0),
        "coal_mw_cheap_hours": round(float(tot[sel].mean()), 0),
        "by_family": {},
    }
    for f in fams:
        col = piv[f] if f in piv else pd.Series(0.0, index=piv.index)
        out["by_family"][f] = {
            "mw_all_hours": round(float(col.mean()), 0),
            "pct_all_hours": round(100 * float(col.mean()) / float(tot.mean()), 1),
            "mw_cheap_hours": round(float(col[sel].mean()), 0),
            "pct_cheap_hours": round(
                100 * float(col[sel].mean()) / float(tot[sel].mean()), 1
            ),
        }
    price_taking = out["by_family"]["mustrun"]["mw_cheap_hours"]
    take_or_pay = out["by_family"]["committed"]["mw_cheap_hours"]
    out["price_insensitive_mw_cheap_hours"] = round(price_taking + take_or_pay, 0)
    out["price_insensitive_pct_cheap_hours"] = round(
        100 * (price_taking + take_or_pay) / out["coal_mw_cheap_hours"], 1
    )
    out["displaceable_mw_cheap_hours"] = round(
        out["coal_mw_cheap_hours"] - price_taking - take_or_pay, 0
    )
    return out


def part_b() -> dict:
    """WHICH coal band family the ruled static displaced — one on-recipe rebuild, no LP."""
    from market_sim.data.fuel.basis.miso import _miso_gas_variable_transport_vector

    cfg = keeper_config()
    _raw, fleet, arrays, fuel_prices, mc, zone_names = build_year(cfg, YEAR)
    uid = np.array([str(u) for u in arrays.unit_ids])
    fam = np.array([_family(u) for u in uid])
    klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    fuel_name = np.array([str(getattr(g, "fuel_type", "") or "").lower() for g in fleet])
    is_gas = np.array([f.startswith("gas") for f in fuel_name])
    is_coal = np.isin(klass, COAL_CLASSES) | (fuel_name == "coal")
    south = np.array([str(g.zone) for g in fleet]) == "MISO-South"

    pmax = np.asarray(arrays.pmax, float)
    avail = np.asarray(arrays.availability, float)
    if avail.ndim == 1:
        avail = np.tile(avail[:, None], (1, HOURS))
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    fp = np.asarray(fuel_prices, float)
    if fp.ndim == 1:
        fp = np.tile(fp[:, None], (1, HOURS))
    hr = np.asarray(arrays.heat_rate, float)

    moh = _month_of_hour() - 1
    spot = np.where(
        south[:, None],
        hh_by_month(YEAR)[moh][None, :],
        spot_gas_by_month(YEAR)[moh][None, :],
    )
    gas_rows = np.flatnonzero(is_gas)
    v = np.zeros(len(fleet))
    v[gas_rows] = _miso_gas_variable_transport_vector(arrays, gas_rows, tuple(zone_names))
    mc_ruled = mc + np.where(
        is_gas[:, None], (spot + v[:, None] - fp) * hr[:, None], 0.0
    )

    q = fleet_dispatch(YEAR)
    act = actual_zone_price(YEAR)[ZONE].to_numpy(float)
    sel = np.isfinite(act) & (act < 20.0)
    hours = np.flatnonzero(sel)

    fams = ("mustrun", "committed", "econ", "peak", "other")
    disp = {f: 0.0 for f in fams}          # coal MW displaced, by family
    held = {f: 0.0 for f in fams}          # coal MW still in merit under the ruled basis
    keep = {f: 0.0 for f in fams}          # coal MW in merit under the keeper basis
    for h in hours:
        cap = pmax * avail[:, h]
        live = cap > 1.0
        for basis, sink in ((mc[:, h], keep), (mc_ruled[:, h], held)):
            idx = np.flatnonzero(live)
            order = idx[np.argsort(basis[idx], kind="stable")]
            csum = np.cumsum(cap[order])
            n_full = int(np.searchsorted(csum, q[h], side="left"))
            take = np.zeros(len(fleet))
            if n_full:
                take[order[:n_full]] = cap[order[:n_full]]
            if n_full < len(order):
                prev = csum[n_full - 1] if n_full else 0.0
                take[order[n_full]] = max(0.0, min(cap[order[n_full]], q[h] - prev))
            for f in fams:
                m = (fam == f) & is_coal
                sink[f] += float(take[m].sum())
    n = float(len(hours))
    for f in fams:
        keep[f] /= n
        held[f] /= n
        disp[f] = held[f] - keep[f]

    total_disp = sum(disp.values())
    return {
        "n_cheap_hours": int(n),
        "n_tranches": int(len(fleet)),
        "static_coal_delta_mw_total": round(total_disp, 0),
        "static_coal_delta_mw_by_family": {f: round(disp[f], 0) for f in fams},
        "coal_in_merit_mw_keeper_basis_by_family": {f: round(keep[f], 0) for f in fams},
        "coal_in_merit_mw_ruled_basis_by_family": {f: round(held[f], 0) for f in fams},
        "prereg_static_total_for_reference": MISO225_STATIC_COAL_MW,
    }


def main() -> int:
    a = part_a()
    b = part_b()
    disp = b["static_coal_delta_mw_by_family"]
    reachable = a["displaceable_mw_cheap_hours"]
    rec = {
        "probe": (
            "miso-226 phase 0 (queue item 2) — attribution of the LP's cheap-hour "
            "coal hold across the keeper's armed coal commitment structure"
        ),
        "keeper": "2026-09-05-miso-220-nonsteam-lift (miso220_nonsteamlift_B)",
        "year": YEAR,
        "hour_set": "the 1,230 hours the REAL MISO-Indiana hub cleared < $20 (miso-225's G-3 set)",
        "A_keeper_coal_by_band_family": a,
        "B_static_displacement_by_band_family": b,
        "reconciliation": {
            "miso225_static_demanded_mw": MISO225_STATIC_COAL_MW,
            "miso225_lp_realized_mw": MISO225_REALIZED_COAL_MW,
            "miso225_realized_fraction_of_static": round(
                MISO225_REALIZED_COAL_MW / MISO225_STATIC_COAL_MW, 3
            ),
            "keeper_price_taking_plus_takeorpay_coal_mw": a[
                "price_insensitive_mw_cheap_hours"
            ],
            "keeper_price_taking_plus_takeorpay_pct": a[
                "price_insensitive_pct_cheap_hours"
            ],
            "keeper_econ_plus_peak_coal_mw": reachable,
            "realized_fraction_of_the_econ_band_alone": (
                round(MISO225_REALIZED_COAL_MW / -reachable, 3) if reachable else None
            ),
            "static_displacement_charged_to_the_committed_band_mw": disp.get(
                "committed", 0.0
            ),
            "static_displacement_charged_to_the_econ_band_mw": disp.get("econ", 0.0),
        },
    }
    OUT.write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec["A_keeper_coal_by_band_family"], indent=1))
    print(json.dumps(rec["B_static_displacement_by_band_family"], indent=1))
    print(json.dumps(rec["reconciliation"], indent=1))
    print(f"-> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
