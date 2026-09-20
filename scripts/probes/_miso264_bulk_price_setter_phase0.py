#!/usr/bin/env python3
"""miso-264 phase 0: WHAT SETS MISO's BULK PRICE, and is the gas-margin ANCHOR the index?

ZERO LP (rule 32 ``[R-SHARD]`` (a)).  Nothing is solved.  Every number is read
from the designated keeper's committed sidecars or produced by
``run_calibration.run_year(..., fleet_only=True)`` — the data-only fleet/offer
assembly, which builds no LP matrix and calls no solver.

THE OBJECT
----------
``FINDING-miso262`` §5 reported, and did not fix, a BULK price residual present
in all six span years: the model's price distribution is compressed — too high
through the bulk, too low in the tail.  The tail half is C3c and is ledgered;
the bulk half is not, and it sits behind C3a 2020 (+16.3 %) and C3a 2022
(−14.6 %) and, through the seam transducer (§1 of that finding, r = +0.957),
behind part of C1 2020 COAL_BIT.  ``FINDING-miso262`` §6 also refused the one
lever the charter named — a COAL_BIT offer-band multiplier — on structure, not
on a sweep: rule 1 ``[R-STRUCT]``'s authorised price-tuning carve-out binds on
condition (b), ONE config across every scored year, and MISO's price bias FLIPS
SIGN across the span (+18.2 % in 2020, −17.3 % in 2022).

So the repair, if one exists, must be a single year-invariant CONFIG whose
effect is nonetheless year-responsive because a MEASURED INPUT inside it moves.

WHAT THIS PROBE MEASURES
------------------------
A  The per-year VINTAGE anchor of ``gas_offer_net_revenue_margin`` — the mean
   of the solve year's own delivered-gas series ``_gas_series``, resolved by
   the production path itself (``run_year``'s own ``gas_offer_margin_anchor_
   vintage`` block) — against the FROZEN 2023-2025 window anchor 3.0492 the
   keeper prices every year at.  This is a statement about an INPUT, not about
   a residual.
B  The offer-surface response, exact and at zero LP: the keeper's own assembled
   ``mc_base`` rebuilt twice per year, control and armed, differenced per
   (class, band).  ``apply_gas_offer_margin`` adds
   ``offer_markup_hr[g] x (anchor - fuel[g, t])``, so the arm's effect is a
   closed-form per-row shift ``offer_markup_hr[g] x (anchor_vintage -
   anchor_frozen)`` — reported here as the measured array difference, never the
   formula re-implemented.
C  WHICH (class, band) SETS THE BULK PRICE, 2020, internal zone-hours — the
   charter's literal phase-0 ask.  A row is a candidate price-setter in a
   zone-hour when it is available and its ``mc`` is within ``TOL`` of that
   zone's P1 dual.  Reported zone-local and pooled, by price decile.
D  The PREDICTED price move the arm produces, bounded from C and B without a
   solve: the demand-weighted mean of the arm's ``dmc`` over each zone-hour's
   matched marginal rows.  This is a MAGNITUDE REPORT the gate requires, NOT
   the reason to arm anything (rule 1 ``[R-STRUCT]``): the basis is rule 14
   ``[R-ACCURATE]`` — the anchor is DEFINED as the mean of the year's own
   delivered-gas series, and evaluating it on a frozen 2023-2025 window for a
   2020 solve is the wrong index, which the mechanism's own identity says so
   ("at ``fuel == anchor`` the reformed offer reduces EXACTLY to the registered
   band multiplier").

WHAT IT IS NOT
--------------
No mechanism is armed, no parameter is tuned, no criterion is consulted to
choose anything, and nothing is swept (rule 1 ``[R-STRUCT]``; rule 21
``[R-DOF]`` — zero free parameters, the arm adds none).  ``TOL`` is fixed
before the first number at $0.05/MWh and three wider settings are reported
beside it precisely so the reader can see the census does not move.

Usage::

    uv run python scripts/probes/_miso264_bulk_price_setter_phase0.py --year 2020
    uv run python scripts/probes/_miso264_bulk_price_setter_phase0.py --all
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

BUNDLE = REPO / "results/calibration/miso263_coalcap_span"
OUT = REPO / "results/calibration/_miso264_bulk_price_setter.json"
YEARS = (2020, 2021, 2022, 2023, 2024, 2025)
INTERNAL = (
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
)

#: Price-match tolerance, $/MWh. FIXED before the first number and never swept.
#: MISO's persisted P1 price is the raw energy-balance dual (no post-solve
#: adder on this keeper), and 2020's reserve duals are non-zero in 0.01 % of
#: hours, so the only wedge is float round-trip through float32 sidecars.
TOL = 0.05
TOL_SENSITIVITY = (0.01, 0.10, 0.25)


def band_of(unit_id: str) -> str:
    """The LP tranche suffix — the last underscore token of ``unit_id``.

    Verbatim the split ``run_calibration_full._write_class_band_hourly_sidecar``
    uses, so this probe's band key IS the committed sidecar's band key.
    """
    return str(unit_id).rsplit("_", 1)[-1]


def family(klass: str, band: str) -> str:
    """Collapse (klass, band) to the offer-stack family the census reports."""
    k = str(klass)
    b = str(band)
    if k.startswith("COAL"):
        grp = "coal"
    elif k.startswith("CC"):
        grp = "CC"
    elif k.startswith("CT"):
        grp = "CT"
    elif k.startswith("ST_GAS"):
        grp = "ST_GAS"
    elif k in ("import", "export") or k.startswith("import"):
        return "seam"
    else:
        return k
    if b.startswith("committed"):
        return f"{grp} committed"
    if b.startswith("econ"):
        return f"{grp} econ"
    if b.startswith("peak"):
        return f"{grp} peak"
    return f"{grp} {b}" if b else grp


def build_state(year: int, armed: bool) -> dict:
    """Rebuild the keeper's ``year`` fleet/offer arrays, no LP.

    ``armed`` adds ``gas_offer_margin_anchor_vintage=True`` — resolved by
    ``run_year``'s own production block, so the anchor this probe reports is
    the one a solve would price against, never a re-implementation.
    """
    from scripts.lib.bundle_fleet import (
        bundle_gas_price,
        clear_fleet_caches,
        full_run_year_kwargs,
    )
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    clear_fleet_caches()
    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = full_run_year_kwargs(meta)
    kwargs.update(derived_run_year_inputs(BUNDLE, year))
    # The keeper is a DATA-PARTITIONED composite whose span-wide meta carries
    # the 2020 leg's reserve configuration (RESULT-miso263 §3). Restore each
    # year's own declared values from its own run_config, exactly as that
    # session's --set workaround does, so the reconstruction is the keeper's.
    rc = json.loads((BUNDLE / f"run_config_{year}.json").read_text())
    sc = rc["scenario_config"]
    for f in ("miso_measured_reserve_requirements", "miso_reserve_online_gated"):
        if f in kwargs or True:
            kwargs[f] = bool(sc[f])
    if armed:
        kwargs["gas_offer_margin_anchor_vintage"] = True
    return run_year(
        year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, year), **kwargs
    )


def arrays(state: dict) -> dict:
    """Project a ``fleet_only`` state onto the arrays the census needs."""
    fa, fleet = state["fleet_arrays"], state["fleet"]
    raw = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    fuel = np.array([str(getattr(g, "fuel_type", "") or "") for g in fleet])
    binned = raw != ""
    return {
        "klass": np.where(binned, raw, fuel),
        "band": np.where(binned, [band_of(u) for u in fa.unit_ids], ""),
        "zone": np.array([str(getattr(g, "zone", "") or "") for g in fleet]),
        "markup_hr": np.array(
            [float(getattr(g, "offer_markup_hr", 0.0) or 0.0) for g in fleet]
        ),
        "pmax": np.asarray(fa.pmax, float),
        "avail": np.asarray(fa.availability, float),
        "mc": np.asarray(state["mc_base"], float),
        "anchor": float(getattr(state["config"], "gas_offer_margin_anchor", np.nan)),
    }


def census(A: dict, price: np.ndarray, demand: np.ndarray, tol: float) -> dict:
    """Price-setter census over MISO's internal zones for one year.

    ``price`` / ``demand`` are ``(n_zone, T)`` on :data:`INTERNAL`'s order.  A
    row is a candidate in a zone-hour when its available capacity is positive
    and ``|mc - lambda| <= tol``; the hour's zonal demand is split evenly over
    the candidates, so the reported shares are MWh-weighted, not hour-weighted.
    Both the zone-LOCAL variant (rows physically in that zone) and the POOLED
    variant (any MISO row, which is what a congested zone can price off) are
    returned.
    """
    cap = A["pmax"][:, None] * A["avail"]
    fams = np.array([family(k, b) for k, b in zip(A["klass"], A["band"])])
    out: dict[str, dict] = {}
    for mode in ("local", "pooled"):
        w: Counter = Counter()
        dmc_w: Counter = Counter()
        matched = unmatched = total = 0.0
        un_above = un_below = 0.0
        for zi, zz in enumerate(INTERNAL):
            gi = (
                np.where(A["zone"] == zz)[0]
                if mode == "local"
                else np.arange(len(A["zone"]))
            )
            if gi.size == 0:
                continue
            mc_z = A["mc"][gi]
            live = cap[gi] > 1e-6
            hit = live & (np.abs(mc_z - price[zi][None, :]) <= tol)
            n = hit.sum(axis=0)
            d = demand[zi]
            total += float(d.sum())
            has = n > 0
            matched += float(d[has].sum())
            unmatched += float(d[~has].sum())
            if (~has).any():
                # Is the unmatched dual above or below the whole live stack?
                lo = np.where(live, mc_z, np.inf).min(axis=0)
                hi = np.where(live, mc_z, -np.inf).max(axis=0)
                u = ~has
                un_above += float(d[u & (price[zi] > hi)].sum())
                un_below += float(d[u & (price[zi] < lo)].sum())
            if not has.any():
                continue
            share = np.zeros_like(mc_z)
            share[hit] = 1.0
            share /= np.maximum(n, 1)[None, :]
            mwh = share * d[None, :]
            per_row = mwh.sum(axis=1)
            dmc_row = A.get("dmc")
            for j, i in enumerate(gi):
                if per_row[j] <= 0:
                    continue
                w[fams[i]] += float(per_row[j])
                if dmc_row is not None:
                    dmc_w[fams[i]] += float((mwh[j] * dmc_row[i]).sum())
        out[mode] = {
            "matched_share": matched / total if total else 0.0,
            "unmatched_share": unmatched / total if total else 0.0,
            "unmatched_above_stack": un_above / total if total else 0.0,
            "unmatched_below_stack": un_below / total if total else 0.0,
            "family_share": {
                k: v / max(matched, 1e-9) for k, v in w.most_common() if v > 0
            },
            "family_dmc_mwh": {k: v for k, v in dmc_w.most_common()} if dmc_w else {},
            "predicted_d_price": (sum(dmc_w.values()) / matched) if matched else None,
        }
    return out


def run_year_probe(year: int) -> dict:
    sysdf = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    sysdf = sysdf[sysdf["pass"] == "P1"]
    pr = sysdf.pivot(index="hour", columns="zone", values="price")[list(INTERNAL)]
    dm = sysdf.pivot(index="hour", columns="zone", values="demand")[list(INTERNAL)]
    price = pr.to_numpy(float).T
    demand = dm.to_numpy(float).T

    ctl = arrays(build_state(year, armed=False))
    gc.collect()
    arm = arrays(build_state(year, armed=True))
    gc.collect()

    dmc_full = arm["mc"] - ctl["mc"]
    # The arm's shift is constant in t per row by construction; report the row
    # mean and CHECK the constancy rather than assume it.
    dmc_row = dmc_full.mean(axis=1)
    row_ptp = float(np.abs(dmc_full - dmc_row[:, None]).max())
    ctl["dmc"] = dmc_row

    fams = np.array([family(k, b) for k, b in zip(ctl["klass"], ctl["band"])])
    cap = ctl["pmax"] * ctl["avail"].mean(axis=1)
    by_fam = {}
    for f in sorted(set(fams[np.abs(dmc_row) > 1e-9])):
        m = fams == f
        wsum = cap[m].sum()
        by_fam[f] = {
            "n_rows": int(m.sum()),
            "n_marked": int((m & (np.abs(dmc_row) > 1e-9)).sum()),
            "cap_mw": float(wsum),
            "capw_dmc": float((dmc_row[m] * cap[m]).sum() / wsum) if wsum else 0.0,
            "min_dmc": float(dmc_row[m].min()),
            "max_dmc": float(dmc_row[m].max()),
        }

    res: dict = {
        "year": year,
        "anchor_frozen": ctl["anchor"],
        "anchor_vintage": arm["anchor"],
        "d_anchor": arm["anchor"] - ctl["anchor"],
        "row_shift_constancy_max_abs_dev": row_ptp,
        "n_markup_rows": int((ctl["markup_hr"] > 0).sum()),
        "dmc_by_family": by_fam,
        "census": census(ctl, price, demand, TOL),
        "census_tol_sensitivity": {
            str(t): census(ctl, price, demand, t)["pooled"]["matched_share"]
            for t in TOL_SENSITIVITY
        },
        "model_price_pctiles": {
            str(q): float(np.percentile(price, q)) for q in (1, 10, 25, 50, 75, 90, 99)
        },
        "model_load_weighted_price": float((price * demand).sum() / demand.sum()),
    }

    # Per-decile census on the model's own price, so the BULK is separable
    # from the tail C3c already owns.
    flat_p = price.reshape(-1)
    edges = np.percentile(flat_p, [0, 10, 50, 90, 100])
    deciles = {}
    for lab, lo, hi in (
        ("p00_p10", edges[0], edges[1]),
        ("p10_p50", edges[1], edges[2]),
        ("p50_p90", edges[2], edges[3]),
        ("p90_p100", edges[3], edges[4]),
    ):
        mask = (price >= lo) & (price <= hi)
        deciles[lab] = census(
            ctl, np.where(mask, price, -1e9), np.where(mask, demand, 0.0), TOL
        )["pooled"]
    res["census_by_price_band"] = deciles
    del ctl, arm, dmc_full
    gc.collect()
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, action="append")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    years = YEARS if a.all else tuple(a.year or (2020,))

    prior = {}
    if a.out.exists():
        prior = json.loads(a.out.read_text())
    for y in years:
        print(f"\n===== {y} =====", flush=True)
        r = run_year_probe(y)
        prior[str(y)] = r
        a.out.write_text(json.dumps(prior, indent=1, sort_keys=True))
        print(
            f"  anchor frozen {r['anchor_frozen']:.4f} -> vintage "
            f"{r['anchor_vintage']:.4f}  (d {r['d_anchor']:+.4f} $/MMBtu)"
        )
        print(f"  markup rows {r['n_markup_rows']}")
        for f, d in sorted(r["dmc_by_family"].items()):
            print(
                f"    {f:18s} n={d['n_marked']:4d}/{d['n_rows']:4d} "
                f"cap={d['cap_mw']:9.1f}  capw dmc {d['capw_dmc']:+8.3f} $/MWh"
            )
        for mode in ("local", "pooled"):
            c = r["census"][mode]
            print(
                f"  census[{mode}] matched {100 * c['matched_share']:.1f}% of MWh; "
                f"predicted d price {c['predicted_d_price']}"
            )
            for f, s in list(c["family_share"].items())[:8]:
                print(f"      {f:18s} {100 * s:5.1f}%")
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
