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

2. **The ladder's clearing side.** An EXPORT band is a negative-output
   pseudo-unit offered at ``p_k``: it dispatches when PJM's own internal price
   sits **at or BELOW** ``p_k`` (PJM exports when it is cheap relative to the
   neighbour), so the clearing duration is ``P(price <= p_k)``, NOT the
   exceedance. The identification confirms the polarity on the data: for every
   band, the measured flow duration ``D_k`` and the measured DA LMP's
   *exceedance* of ``p_k`` sum to 1.0, i.e. ``p_k`` is exactly the quantile at
   which ``P(LMP <= p_k) = D_k``. We therefore compare ``D_k`` against
   ``P(model price <= p_k)``. ``P_model < D_k`` means the model's price
   duration curve sits ABOVE the one the ladder was identified on in the
   region that matters, and the deep bands simply never clear.

3. **The benchmark the residual is measured against.** Item 15's numbers come
   from the ``interchange`` family row, whose actual is EIA-930's
   ``Total interchange``, while the seam envelopes AND the ladder are both
   identified on PJM's settlement-grade tie-line file. The probe reports both
   series per year plus EIA-930's OWN internal identity
   (``Net generation - Demand``), so a year in which the two measured sources
   disagree is visible rather than silently charged to the model.

4. **The three together.** Per seam and per year, so the binding side is named
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
            # An export band clears when the internal price is at or BELOW
            # its offer, so the clearing duration is P(price <= p_k).
            d_model = (
                float(np.count_nonzero(model_p <= float(p_k))) / HOURS
                if model_p is not None
                else None
            )
            d_actual_lmp = (
                float(np.count_nonzero(meas_p <= float(p_k))) / HOURS
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
                    # the ladder's identification target, reproduced: this must
                    # come back ~= duration_measured, which is what proves the
                    # polarity above and that p_k is the P(LMP <= p_k) quantile
                    "duration_actual_lmp_clears": (
                        None if d_actual_lmp is None else round(d_actual_lmp, 4)
                    ),
                    # where the MODEL's own price actually sits
                    "duration_model_price_clears": (
                        None if d_model is None else round(d_model, 4)
                    ),
                    # NEGATIVE = the model under-clears this band
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


def benchmark_basis(year: int) -> dict:
    """Cross-source the interchange ACTUAL the item-15 residual is measured on.

    The ``interchange`` family row's actual is EIA-930's ``Total interchange``.
    The seam envelopes and the measured ladder are both identified on PJM's
    settlement-grade tie-line file. Those are different meters, and the ladder's
    own source comment already records that they disagree per-seam. This reports
    both totals, their hourly correlation, and EIA-930's OWN internal identity
    (``Net generation - Demand``, which must equal ``Total interchange``) so a
    year in which one source is internally inconsistent is visible.
    """
    import pandas as pd

    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia930.actuals import load_eia_hourly_benchmark
    from market_sim.data.eia_loader import pjm_neighbor_interchange

    names = [n.name for n in INTERFACE_NEIGHBORS.get("PJM", [])]
    tie = pjm_neighbor_interchange(year, names)
    bench = load_eia_hourly_benchmark("PJM", year)
    ix = None if bench is None else bench.get("interchange")
    out: dict[str, object] = {}
    if ix is not None:
        out["eia930_total_interchange_twh"] = round(float(np.sum(ix)) / 1e6, 3)
    if tie is not None:
        out["pjm_tie_file_net_export_twh"] = round(float(tie.sum()) / 1e6, 3)
    if ix is not None and tie is not None:
        a = np.asarray(ix, dtype=float)
        b = tie.sum(axis=0)
        out["difference_twh"] = round(
            out["eia930_total_interchange_twh"] - out["pjm_tie_file_net_export_twh"], 3
        )
        out["hourly_correlation"] = round(float(np.corrcoef(a, b)[0, 1]), 4)

    # EIA-930's own identity: Net generation - Demand must equal Total
    # interchange. A break localises the disagreement to the interchange COLUMN
    # rather than to the tie file.
    raw = REPO / "data/raw/eia-930-hourly/PJM hourly.parquet"
    if raw.is_file():
        df = pd.read_parquet(raw)
        sub = df[df["Local date"].dt.year == year]
        if len(sub) and {"Net generation", "Demand", "Total interchange"} <= set(
            sub.columns
        ):
            ng = float(sub["Net generation"].interpolate().bfill().ffill().sum()) / 1e6
            dem = float(sub["Demand"].interpolate().bfill().ffill().sum()) / 1e6
            tix = float(sub["Total interchange"].interpolate().bfill().ffill().sum())
            tix /= 1e6
            out["eia930_net_generation_twh"] = round(ng, 3)
            out["eia930_demand_twh"] = round(dem, 3)
            out["eia930_netgen_minus_demand_twh"] = round(ng - dem, 3)
            out["eia930_identity_residual_twh"] = round((ng - dem) - tix, 3)
    return out


def main() -> None:
    """Measure every candidate binding side and write the JSON record."""
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
            "benchmark_basis": benchmark_basis(year),
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
        bb = rec["years"][str(y)]["benchmark_basis"]
        print(
            f"{y}: tie-file net export {ec['total_measured_net_export_twh']} TWh | "
            f"envelope ceiling {ec['total_envelope_export_ceiling_twh']} TWh | "
            f"headroom {ec['net_export_headroom_twh']} TWh"
        )
        print(
            f"      benchmark basis: EIA-930 total interchange "
            f"{bb.get('eia930_total_interchange_twh')} TWh vs tie file "
            f"{bb.get('pjm_tie_file_net_export_twh')} TWh "
            f"(EIA-930 identity residual "
            f"{bb.get('eia930_identity_residual_twh')} TWh, hourly r "
            f"{bb.get('hourly_correlation')})"
        )


if __name__ == "__main__":
    main()
