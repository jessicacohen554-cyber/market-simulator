"""caiso-241 — the TWO-SIDED price envelope for the CT_PEAKER `committed` grounding.

NO LP, NO SOLVE. Reads the caiso-240 keeper's committed hourly sidecars
(`hourly/system_<year>.parquet` — per-zone P1 clearing prices) and rebuilds the
fleet twice (flag off / on, `run_year(fleet_only=True)`) to get each repriced
tranche's hourly marginal cost before and after.

WHY NOT THE caiso-230 §H FORM. §H sums only over zone-hours where the repriced
rung is ITSELF the matched marginal rung, so it is structurally blind to
INDIRECT RE-DISPATCH. caiso-240 FALSIFIED its description as a strict upper
bound (its 2024 leg under-predicted by 4.5x). This arm is in the regime where §H
under-predicts BY CONSTRUCTION: it LOWERS a band on a class that is 66-90 %
absent, so its dominant channel is energy attracted INTO a class that is not
currently running. §H is therefore reported here only as a DIAGNOSTIC (the count
of matched-marginal zone-hours, to show the degeneracy), and the envelope is the
CROSSING-ENVELOPE estimator §H' of the precommit §3.2.

§H' — for every repriced tranche g in zone z and hour t:

    crossing(g,z,t) = 1{ mc_old(g,t) > p(z,t) >= mc_new(g,t) }

i.e. the hours in which the repricing newly brings the tranche into the money.
The deepest the price can fall in such an hour is to the cheapest crossing
tranche's new cost, so

    B(year) = mean over zone-hours of  max(0, p(z,t) - min_g mc_new(g,t))
              restricted to crossing zone-hours

is the fall IF the repriced tranche sets price in EVERY hour it newly clears —
the maximum the channel can deliver. The registered two-sided interval is

    dP_mean(year) in [ -B(year), +0.05 $/MWh ]

both endpoints live falsifiers (precommit §3.2). A bound violation is a defect
in the estimator or the mechanism, reported as such and NEVER re-fitted.

WHAT IT STILL CANNOT SEE, stated in the precommit §3.3 and repeated here: second
-order re-dispatch among OTHER classes, storage/hydro re-scheduling, and changes
in which hours are scarce. It is an envelope on one dominant channel, not a
proof.

ONE FURTHER CONSERVATISM, DISCLOSED: the tranche costs are `mc_base` (the P0
basis). The P1 bid additionally carries the amortized startup markup, which is
strictly positive on these `_committed` rows, so the true bid is HIGHER, fewer
hours cross, and §H' OVER-states the crossing. That is the direction an envelope
should err in.

Pre-registered in ``PRECOMMIT-caiso241-ct-peaker-committed-2026-09-03.md`` §3.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso241_cell_bound.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import inspect
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

BUNDLE = REPO / "results/calibration/caiso240_b1_stgas_peak_measured"
FLAG = "caiso_ct_peaker_committed_measured"
YEARS = (2023, 2024, 2025)
HOURS = 8760
POSITIVE_TOLERANCE = 0.05  # $/MWh, the registered upper endpoint
OUT = REPO / "results/calibration/_caiso241_cell_bound.json"

_spec = importlib.util.spec_from_file_location(
    "_caiso240_default_hr_mult_census",
    REPO / "scripts/probes/_caiso240_default_hr_mult_census.py",
)
CENSUS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CENSUS)


def _zone_names() -> list[str]:
    from market_sim.config.iso_configs import get_iso_config

    return get_iso_config("CAISO").zone_names


def rebuild(year: int, armed: bool) -> dict:
    from run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {k: v for k, v in meta.items() if k in params and k not in skip}
    if armed:
        kwargs[FLAG] = True
    CENSUS._clear_fleet_caches()
    with contextlib.redirect_stderr(io.StringIO()):
        st = run_year(
            year,
            meta["iso"],
            HOURS,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kwargs,
        )
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    return {
        "uid": np.array([str(u) for u in fa.unit_ids]),
        "mc": mc,
        "zone_idx": np.asarray(fa.zone_idx, dtype=int),
        "pmax": np.asarray(fa.pmax, dtype=float),
        "avail": np.asarray(fa.availability, dtype=float),
        "zones": _zone_names(),
    }


def main() -> None:
    out: dict = {
        "_provenance": {
            "session": "caiso-241",
            "estimator": "crossing-envelope §H' (precommit §3.2) — REPLACES the "
            "caiso-230 §H form, which caiso-240 falsified as an upper bound and "
            "which is blind to the indirect re-dispatch that is THIS arm's "
            "dominant channel",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": "2026-09-03-caiso-240-b1-stgas",
            "flag": FLAG,
            "cost_basis": "mc_base (P0); the P1 startup markup is omitted, which "
            "makes the envelope CONSERVATIVE (true bid higher → fewer crossings)",
            "positive_tolerance_usd_mwh": POSITIVE_TOLERANCE,
            "solves": 0,
        }
    }
    per_year: dict = {}
    for year in YEARS:
        off = rebuild(year, False)
        on = rebuild(year, True)
        moved = np.flatnonzero(np.abs(on["mc"] - off["mc"]).max(axis=1) > 1e-9)
        sysd = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        zones = off["zones"]
        price = np.full((len(zones), HOURS), np.nan)
        for zi, zname in enumerate(zones):
            sub = sysd[sysd["zone"] == zname].sort_values("hour")
            if len(sub):
                price[zi, : len(sub)] = sub["price"].to_numpy()[:HOURS]
        live_z = sorted({int(off["zone_idx"][i]) for i in moved})

        # per zone-hour: cheapest NEW cost among that zone's crossing tranches
        best_new = np.full((len(zones), HOURS), np.inf)
        cross_cap = np.zeros((len(zones), HOURS))
        for i in moved:
            zi = int(off["zone_idx"][i])
            p = price[zi]
            cr = (off["mc"][i] > p) & (p >= on["mc"][i]) & np.isfinite(p)
            best_new[zi] = np.where(cr & (on["mc"][i] < best_new[zi]),
                                    on["mc"][i], best_new[zi])
            cross_cap[zi] += cr * off["pmax"][i] * off["avail"][i]
        crossing = np.isfinite(best_new) & (best_new < np.inf)
        fall = np.where(crossing, np.maximum(0.0, price - best_new), 0.0)
        n_zh = int(np.isfinite(price).sum())
        n_cross = int(crossing.sum())
        B = float(fall.sum() / n_zh) if n_zh else 0.0

        # DIAGNOSTIC: the §H matched-marginal count, to show its degeneracy here.
        tol = 0.75  # caiso-230 §H attribution tolerance, $/MWh
        n_matched = 0
        for i in moved:
            zi = int(off["zone_idx"][i])
            n_matched += int(
                (np.abs(off["mc"][i] - price[zi]) <= tol).sum()
            )

        vol_env = float(cross_cap.sum() / 1e6)  # TWh ceiling on attracted energy
        per_year[str(year)] = {
            "n_repriced_tranches": int(moved.size),
            "zones_live": [zones[z] for z in live_z],
            "n_zone_hours": n_zh,
            "n_crossing_zone_hours": n_cross,
            "crossing_share_pct": round(100.0 * n_cross / n_zh, 3) if n_zh else 0.0,
            "B_usd_mwh": round(B, 6),
            "interval_usd_mwh": [round(-B, 6), POSITIVE_TOLERANCE],
            "mean_fall_in_crossing_hours_usd_mwh": (
                round(float(fall[crossing].mean()), 4) if n_cross else 0.0
            ),
            "volume_envelope_twh": round(vol_env, 4),
            "sectionH_matched_marginal_zone_hours": n_matched,
            "degenerate": bool(n_cross == 0),
        }
        v = per_year[str(year)]
        print(
            f"[{year}] repriced {v['n_repriced_tranches']}  crossing "
            f"{n_cross}/{n_zh} zone-hours ({v['crossing_share_pct']} %)  "
            f"B = {B:.6f} $/MWh  interval {v['interval_usd_mwh']}  "
            f"volume envelope {vol_env:.3f} TWh  "
            f"(§H matched-marginal zone-hours: {n_matched})"
        )
    out["per_year"] = per_year
    out["registered_interval"] = {
        y: v["interval_usd_mwh"] for y, v in per_year.items()
    }
    out["falsifiers"] = {
        "lower": "measured annual mean price move BELOW -B — the channel "
        "delivered more than its maximum ⇒ estimator or mechanism is wrong",
        "upper": f"measured move ABOVE +{POSITIVE_TOLERANCE} — the arm moved "
        "price the UNEXPECTED way at material size",
        "degenerate_year": "a year with zero crossing zone-hours reports B as "
        "'zero to within the estimator's attribution tolerance', never as an "
        "exact zero; a small measured move there is a bound-form limitation, "
        "not a falsification (precommit §3.2)",
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
