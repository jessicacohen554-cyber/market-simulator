"""Scope PJM root-cause item 15 with NO LP: which side of the seam binds?

Item 15 (opened by pjm-151, keeper-note NEW/OPEN): PJM's modelled net export is
SHORT of actual by 12.48 / 12.22 TWh in 2023-24 and LONG by 5.21 TWh in 2025.
The pjm-151 envelope repair moved all three years the SAME direction, so the
remainder is **not** a seam-deliverability *attribution* defect, and it must not
be chased by loosening caps, tuning ``PJM_TIE_NEIGHBOR`` or
``PJM_SEAM_FLOW_PERCENTILE``, or restoring the zone-summed path (rules 5 / 14 /
20 / 24).

pjm-151 framed the remainder as a **level/direction question in the
reference-price seam's own economics**: the measured record is
direction-STRUCTURAL and ``pjm_seam_measured_ladder`` already prices that
structure, so why does the LP still clear less export than the ladder's own
duration curve supports?

This probe is the **charter's scoping half only** — it identifies WHICH SIDE
binds and states the arithmetic. It proposes no mechanism, arms nothing, and
touches no config. Anything it identifies needs its own pre-registration and
its own arm (charter, Task C).

It measures three independent things, all off committed artifacts:

1. **The envelope CEILING.** ``inject_pjm_seam_flow_limit(direction="export")``
   floors each seam's export band at the measured per-(month x hour-of-day) p90,
   so the seam can never export more than that envelope in any hour. Summing
   the envelope over 8760 h gives the MAXIMUM annual export the cap admits,
   independent of price. If that ceiling already sits below the measured annual
   export, **the ceiling alone bounds the deficit and no price can close it** —
   a p90 cap is by construction exceeded by the measured flow in ~10 % of that
   cell's hours, and the energy in that upper tail is unreachable.

2. **The ladder's clearing side.** Each export band ``k`` is priced at
   ``p_k``, the DA quantile whose exceedance duration equals the measured
   duration of the seam flowing deeper than band ``k``'s midpoint. So the
   ladder's own duration curve says band ``k`` should flow in ``D_k`` of hours.
   We compare ``D_k`` with the fraction of hours the KEEPER's own modelled PJM
   price clears ``p_k``. ``D_model << D_k`` means the model's price duration
   curve sits below the one the ladder was identified on, and the bands simply
   do not clear.

3. **The two together.** Per seam and per year: measured export, the envelope
   ceiling, and the ladder-clearing estimate, so the binding side is named
   rather than inferred.

Reads only committed artifacts + ``data/raw``. No solve, no floor rebuild.

Usage:
    PYTHONPATH=.:src python <this> [--out results/calibration/_pjm152_item15_scope.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/user/market-simulator")
sys.path[:0] = [str(REPO), str(REPO / "src")]

KEEPER = REPO / "results/calibration/pjm151_seam_B"
YEARS = (2023, 2024, 2025)
HOURS = 8760

#: PJM zones whose LMP the seam bands clear against. The reference-price node
#: prices off the internal system, so the ISO-wide load-weighted price is the
#: right comparator for a band's clearing test.
_EXCLUDE_ZONES = ("PJM_external",)


def _keeper_price(year: int) -> np.ndarray | None:
    """Load-weighted PJM internal price from the keeper's P1 system sidecar."""
    p = KEEPER / "hourly" / f"system_{year}.parquet"
    if not p.is_file():
        return None
    df = pd.read_parquet(p)
    df = df[df["pass"].astype(str) == "P1"]
    df = df[~df["zone"].astype(str).isin(_EXCLUDE_ZONES)]
    if df.empty:
        return None
    g = df.groupby("hour").apply(
        lambda d: float(np.average(d["price"], weights=np.maximum(d["demand"], 1e-9))),
        include_groups=False,
    )
    return g.sort_index().to_numpy(dtype=float)


def _measured_da_lmp(year: int) -> np.ndarray | None:
    """Measured PJM DA system LMP on the model's 8760 clock, if available.

    The same series ``derive_pjm_seam_ladders.py`` identified the ladder on, so
    the ladder's own duration curve can be reproduced rather than assumed.
    """
    from market_sim.data.neighbor_price import neighbor_lmp_hourly

    v = neighbor_lmp_hourly("PJM", year, "da")
    if v is None or v.size < HOURS:
        return None
    return np.asarray(v, dtype=float)[:HOURS]


def envelope_ceiling(year: int) -> dict:
    """Per-seam measured export/import against what the p90 envelope admits."""
    from market_sim.config.constants import PJM_SEAM_FLOW_PERCENTILE
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia_loader import (
        pjm_neighbor_interchange,
        pjm_neighbor_interchange_envelope,
    )

    neighbors = INTERFACE_NEIGHBORS.get("PJM", [])
    names = [n.name for n in neighbors]
    series = pjm_neighbor_interchange(year, names)
    env = pjm_neighbor_interchange_envelope(
        year, names, HOURS, float(PJM_SEAM_FLOW_PERCENTILE)
    )
    if series is None or env is None:
        return {"status": f"no measured tie file for {year}"}
    import_cap, export_cap = env

    rows = []
    for i, n in enumerate(neighbors):
        meas = series[i]
        meas_exp = float(np.clip(meas, 0.0, None).sum()) / 1e6
        meas_imp = float(np.clip(-meas, 0.0, None).sum()) / 1e6
        # The cap the injector actually applies: the envelope, clipped to the
        # band block's total capacity (the interface limit).
        lim = float(n.interface_limit_mw)
        ceil_exp = float(np.minimum(np.clip(export_cap[i], 0.0, None), lim).sum()) / 1e6
        ceil_imp = float(np.minimum(np.clip(import_cap[i], 0.0, None), lim).sum()) / 1e6
        rows.append(
            {
                "seam": n.name,
                "interface_limit_mw": lim,
                "measured_export_twh": round(meas_exp, 3),
                "measured_import_twh": round(meas_imp, 3),
                "measured_net_export_twh": round(meas_exp - meas_imp, 3),
                "envelope_export_ceiling_twh": round(ceil_exp, 3),
                "envelope_import_ceiling_twh": round(ceil_imp, 3),
                # >0 means the cap CANNOT reproduce the measured export even at
                # 100 % utilisation in every hour.
                "export_ceiling_shortfall_twh": round(meas_exp - ceil_exp, 3),
                "export_ceiling_utilisation_needed": (
                    round(meas_exp / ceil_exp, 4) if ceil_exp > 0 else None
                ),
                "hours_measured_export_above_cap": int(
                    np.count_nonzero(
                        np.clip(meas, 0.0, None)
                        > np.minimum(np.clip(export_cap[i], 0.0, None), lim) + 1e-6
                    )
                ),
            }
        )

    tot_meas_net = sum(r["measured_net_export_twh"] for r in rows)
    tot_ceiling = sum(r["envelope_export_ceiling_twh"] for r in rows)
    return {
        "percentile": float(PJM_SEAM_FLOW_PERCENTILE),
        "seams": rows,
        "total_measured_net_export_twh": round(tot_meas_net, 3),
        "total_envelope_export_ceiling_twh": round(tot_ceiling, 3),
        # The decisive number: the most net export the caps admit, against the
        # measured net export the model is scored on.
        "net_export_headroom_twh": round(tot_ceiling - tot_meas_net, 3),
    }


def ladder_clearing(year: int) -> dict:
    """Per-band: the ladder's own duration vs where the model's price sits."""
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia_loader import pjm_neighbor_interchange
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import PJM_SEAM_LADDER_BY_YEAR

    ladder = PJM_SEAM_LADDER_BY_YEAR.get(year)
    if not ladder:
        return {"status": f"no ladder for {year}"}
    model_p = _keeper_price(year)
    meas_p = _measured_da_lmp(year)
    neighbors = INTERFACE_NEIGHBORS.get("PJM", [])
    names = [n.name for n in neighbors]
    series = pjm_neighbor_interchange(year, names)

    rows = []
    for i, n in enumerate(neighbors):
        legs = ladder.get(n.name)
        if not legs or "export" in legs is None:
            continue
        prices = legs.get("export")
        if not prices:
            continue
        step = float(n.interface_limit_mw) / SEAM_FLOW_TRANCHES
        for k, p_k in enumerate(prices, start=1):
            mid = (k - 0.5) * step
            d_meas = (
                float(np.count_nonzero(np.clip(series[i], 0.0, None) > mid)) / HOURS
                if series is not None
                else None
            )
            d_model = (
                float(np.count_nonzero(model_p >= float(p_k))) / HOURS
                if model_p is not None
                else None
            )
            d_actual_lmp = (
                float(np.count_nonzero(meas_p >= float(p_k))) / HOURS
                if meas_p is not None
                else None
            )
            rows.append(
                {
                    "seam": n.name,
                    "band": k,
                    "band_mid_mw": round(mid, 1),
                    "ladder_price": float(p_k),
                    # what the measured record says this band flows
                    "duration_measured": None if d_meas is None else round(d_meas, 4),
                    # the ladder's identification target, reproduced
                    "duration_actual_lmp_clears": (
                        None if d_actual_lmp is None else round(d_actual_lmp, 4)
                    ),
                    # where the MODEL's own price actually sits
                    "duration_model_price_clears": (
                        None if d_model is None else round(d_model, 4)
                    ),
                    "model_minus_measured_duration": (
                        None
                        if (d_model is None or d_meas is None)
                        else round(d_model - d_meas, 4)
                    ),
                }
            )
    out: dict[str, object] = {"bands": rows}
    if model_p is not None:
        out["model_price_quantiles"] = {
            f"p{q}": round(float(np.percentile(model_p, q)), 2)
            for q in (5, 25, 50, 75, 90, 95, 99)
        }
    if meas_p is not None:
        out["measured_da_lmp_quantiles"] = {
            f"p{q}": round(float(np.percentile(meas_p, q)), 2)
            for q in (5, 25, 50, 75, 90, 95, 99)
        }
    else:
        out["measured_da_lmp"] = "unavailable in this environment"
    return out


def main() -> None:
    """Measure both candidate binding sides and write the JSON record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="results/calibration/_pjm152_item15_scope.json")
    args = ap.parse_args()

    rec: dict[str, object] = {
        "_what": "pjm-152 Task C: NO-LP scoping of PJM root-cause item 15 (the "
        "net-export level residual). Names which side binds -- the measured p90 "
        "deliverability ceiling or the ladder's clearing price -- and proposes "
        "NOTHING. Any mechanism it points at needs its own pre-registration.",
        "keeper": "results/calibration/pjm151_seam_B",
        "years": {},
    }
    for year in YEARS:
        rec["years"][str(year)] = {
            "envelope_ceiling": envelope_ceiling(year),
            "ladder_clearing": ladder_clearing(year),
        }
    (REPO / args.out).write_text(json.dumps(rec, indent=2))
    print(f"wrote {args.out}")
    for y in YEARS:
        ec = rec["years"][str(y)]["envelope_ceiling"]
        if "seams" not in ec:
            print(y, ec)
            continue
        print(
            f"{y}: measured net export {ec['total_measured_net_export_twh']} TWh | "
            f"envelope export ceiling {ec['total_envelope_export_ceiling_twh']} TWh | "
            f"headroom {ec['net_export_headroom_twh']} TWh"
        )


if __name__ == "__main__":
    main()
