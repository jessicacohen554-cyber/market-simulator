"""miso-220 phase 0 — WHICH CLASS IS AT THE MARGIN IN THE HOURS THE PRICE IS MISSING?

Zero-solve. Rebuilds the designated keeper's OWN fleet and offer basis
(``2026-09-05-miso-217-intermphys``, bundle ``miso217_intermphys_B``) through the
same chain ``runner.py`` runs — fleet -> bins -> arrays -> resolved delivered fuel
-> ``assemble_mc`` -> coal tranches -> gas offer margin -> anchored spread — via
``_miso134_ct_night_order_screen.build_year``, and reads the marginal position of
every class-band tranche against the keeper's own committed P1 clearing price at
the object's hours.

**Owner ruling (2026-09-05), recorded here because it scopes the probe:** the
offer-curve multipliers ARE the intended channel for tuning on price and adjusting
merit order, and one config held across all three years is the discipline that
makes that legitimate. This probe therefore reports the merit ladder as a TUNING
SURFACE — which class sets price, what sits above it, and how much capacity lies
between the model's price and the measured one — rather than adjudicating whether
a multiplier may move.

The object (carried in, not re-derived): the top-1 % of measured Jun-Jul RT price
hours, hub ``INDIANA.HUB`` on the committed scoring instrument's fixed-CST clock.
15 hours per year; miso-219 measured the model's energy dual as the ONLY live
price-formation channel in them (reserve/ORDC/congestion inert), so the merit-order
reading below is the operative one.

Method and its self-check. In an hour whose price is set by the energy balance and
not by congestion (miso-219 A-1: mean zonal dispersion $0.06 in 2025), the clearing
dual sits at the offer of the last in-merit tranche. The probe therefore ranks every
available tranche by ``mc`` and reports the tranche bracketing the committed price,
**and reports the reconstruction residual** (committed P1 price minus the highest
in-merit ``mc``) rather than assuming the reconstruction is exact: ``mc_base`` is
the P0 bid basis, so a positive residual is the P1 amortized-startup adder plus any
unmodelled wedge, and it is stated at full magnitude.

Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only. No LP is solved; nothing is minted.

Usage::

    python3 scripts/probes/_miso220_marginal_class_phase0.py
"""

from __future__ import annotations

import gc
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402

KEEPER = REPO / "results/calibration/miso217_intermphys_B"
_m134.BUNDLE = KEEPER

from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from _miso214_ct_peaker_conduct_phase0 import _band, _r  # noqa: E402

OUT = REPO / "results/calibration/_miso220_marginal_class.json"
ZONAL_ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
SCORING_HUB = "INDIANA.HUB"
SCORING_ZONE = "MISO-Indiana"
YEARS = tuple(int(v) for v in os.environ.get("MISO220_YEARS", "2023,2024,2025").split(","))
assert set(YEARS) <= {2023, 2024, 2025}, "rule 22: MISO holds no holdout marker"
HOURS = 8760
TOP_N = 15
MONTH_LENS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
EPS = 1e-9


def _month_of_hour() -> np.ndarray:
    """Calendar month (1-12) per hour on the model's fixed non-leap 8760 clock."""
    return np.concatenate(
        [np.full(n * 24, m + 1) for m, n in enumerate(MONTH_LENS)]
    )[:HOURS]


def _stamp(h: int) -> str:
    """``'MM-DD HEkk'`` on the model's own 8760 clock (February is always 28 days)."""
    doy, hod = divmod(int(h), 24)
    m, d = 0, doy
    for i, n in enumerate(MONTH_LENS):
        if d < n:
            m = i + 1
            break
        d -= n
    return f"{m:02d}-{d + 1:02d} HE{hod + 1:02d}"


def actual_lmp(year: int) -> np.ndarray:
    """(8760,) measured RT LMP at the C3a scoring hub, on the model's clock."""
    df = pd.read_parquet(ZONAL_ACTUAL)
    sub = df[(df["year"] == year) & (df["hub"] == SCORING_HUB)]
    out = np.full(HOURS, np.nan)
    out[sub["hour"].to_numpy(int)] = sub["rt"].to_numpy(float)
    return out


def object_hours(year: int) -> list[int]:
    """The year's top-15 measured-price Jun-Jul hours (the object's own hours)."""
    act = actual_lmp(year)
    mon = _month_of_hour()
    jj = np.where(((mon == 6) | (mon == 7)) & np.isfinite(act))[0]
    return sorted(int(h) for h in jj[np.argsort(act[jj])[::-1]][:TOP_N])


def keeper_zone_price(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(8760,) committed P1 price at the scoring zone, and the load-weighted system price."""
    sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    p = sysf.pivot_table(index="hour", columns="zone", values="price", aggfunc="first")
    d = sysf.pivot_table(index="hour", columns="zone", values="demand", aggfunc="first")
    zones = [z for z in p.columns if not str(z).startswith("MISO_external")]
    pa, da = p[zones].to_numpy(float), d[zones].to_numpy(float)
    lw = (pa * da).sum(axis=1) / np.maximum(da.sum(axis=1), EPS)
    return p[SCORING_ZONE].to_numpy(float), lw


def analyse_year(year: int) -> dict:
    """Merit-ladder position of every class-band tranche at the object's hours."""
    cfg = keeper_config()
    raw_fleet, fleet, arrays, fuel_prices, mc, zone_names = build_year(cfg, year)

    n = len(fleet)
    klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    band = np.array([_band(g.unit_id) for g in fleet])
    zone = np.array([str(g.zone) for g in fleet])
    pmax = np.asarray(arrays.pmax, float)
    avail = np.asarray(arrays.availability, float)
    if avail.ndim == 1:
        avail = np.tile(avail[:, None], (1, HOURS))
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))

    zprice, lwprice = keeper_zone_price(year)
    hrs = object_hours(year)
    act = actual_lmp(year)

    rows, ladders = [], {}
    for h in hrs:
        cap_h = pmax * avail[:, h]
        live = cap_h > 1.0                       # tranches with real capacity this hour
        mc_h = mc[:, h]
        p = float(zprice[h])

        inm = live & (mc_h <= p + EPS)           # in-merit at the committed dual
        marg_i = int(np.flatnonzero(inm)[np.argmax(mc_h[inm])]) if inm.any() else -1
        out_of = live & (mc_h > p + EPS)
        next_i = int(np.flatnonzero(out_of)[np.argmin(mc_h[out_of])]) if out_of.any() else -1

        row = {
            "hour": int(h),
            "stamp": _stamp(h),
            "hod": int(h % 24),
            "committed_price_usd": _r(p, 2),
            "actual_rt_usd": _r(float(act[h]), 2),
            "gap_usd": _r(float(act[h]) - p, 2),
            "marginal_klass": str(klass[marg_i]) if marg_i >= 0 else None,
            "marginal_band": str(band[marg_i]) if marg_i >= 0 else None,
            "marginal_zone": str(zone[marg_i]) if marg_i >= 0 else None,
            "marginal_mc_usd": _r(float(mc_h[marg_i]), 2) if marg_i >= 0 else None,
            # committed P1 dual minus the highest in-merit P0 bid basis: the
            # amortized-startup adder plus any unmodelled wedge. Stated, not assumed away.
            "reconstruction_residual_usd": _r(p - float(mc_h[marg_i]), 2) if marg_i >= 0 else None,
            "next_klass": str(klass[next_i]) if next_i >= 0 else None,
            "next_band": str(band[next_i]) if next_i >= 0 else None,
            "next_mc_usd": _r(float(mc_h[next_i]), 2) if next_i >= 0 else None,
            "capacity_in_merit_mw": _r(float(cap_h[inm].sum()), 0),
            "capacity_above_price_mw": _r(float(cap_h[out_of].sum()), 0),
            "capacity_between_price_and_actual_mw": _r(
                float(cap_h[live & (mc_h > p + EPS) & (mc_h <= float(act[h]))].sum()), 0
            ),
        }
        rows.append(row)

        # the ladder: class-band capacity by offer decile ABOVE the clearing price,
        # i.e. what a multiplier would have to move through to reach the actual.
        lad = {}
        for k in sorted(set(klass[live])):
            sel = live & (klass == k)
            for b in sorted(set(band[sel])):
                s2 = sel & (band == b)
                if not s2.any():
                    continue
                cw = float((mc_h[s2] * cap_h[s2]).sum() / max(cap_h[s2].sum(), EPS))
                lad[f"{k}|{b}"] = {
                    "cap_mw": _r(float(cap_h[s2].sum()), 0),
                    "cap_w_mc_usd": _r(cw, 2),
                    "min_mc_usd": _r(float(mc_h[s2].min()), 2),
                    "max_mc_usd": _r(float(mc_h[s2].max()), 2),
                    "cap_in_merit_mw": _r(float(cap_h[s2 & inm].sum()), 0),
                    "cap_above_price_mw": _r(float(cap_h[s2 & out_of].sum()), 0),
                }
        ladders[str(h)] = lad

    # which class holds the margin, over the object's hours
    tally: dict[str, int] = {}
    for r in rows:
        key = f"{r['marginal_klass']}|{r['marginal_band']}"
        tally[key] = tally.get(key, 0) + 1

    # the multiplier arithmetic the owner's question turns on: to lift the
    # marginal offer to the measured price, by how much would it have to move?
    mults = []
    for r in rows:
        if r["marginal_mc_usd"] and r["marginal_mc_usd"] > 0 and r["actual_rt_usd"]:
            mults.append(r["actual_rt_usd"] / r["marginal_mc_usd"])
    out = {
        "year": year,
        "n_tranches": int(n),
        "object_hours": hrs,
        "rows": rows,
        "marginal_class_tally": dict(sorted(tally.items(), key=lambda kv: -kv[1])),
        "implied_multiplier_marginal_to_actual": {
            "mean": _r(float(np.mean(mults)), 2) if mults else None,
            "median": _r(float(np.median(mults)), 2) if mults else None,
            "min": _r(float(np.min(mults)), 2) if mults else None,
            "max": _r(float(np.max(mults)), 2) if mults else None,
        },
        "ladders": ladders,
    }
    del raw_fleet, fleet, arrays, fuel_prices, mc
    gc.collect()
    return out


def main() -> int:
    """Analyse every requested year and write the JSON record."""
    rec = {
        "probe": "miso-220 phase 0 - which class sets price when the price is missing",
        "keeper": "2026-09-05-miso-217-intermphys",
        "bundle": str(KEEPER.relative_to(REPO)),
        "solved": False,
        "owner_ruling_2026_09_05": (
            "offer-curve multipliers are the intended channel for tuning on price and "
            "adjusting merit order; one config held across 2023-2025 is the discipline"
        ),
        "by_year": {},
    }
    for y in YEARS:
        rec["by_year"][str(y)] = analyse_year(y)
        print(f"  {y} done", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=2))
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
