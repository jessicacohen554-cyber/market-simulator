"""pjm-134 C2 (no LP): do the Dominion-facing interfaces bind in the model as they do in PJM?

ASK-pjm134 §4 candidate C2 -- "if the Dominion-facing interfaces are too
permissive, western coal and CC serve Dominion load and displace its local
CT/CC".

The committed ``hourly/`` sidecars carry per-zone hourly LP prices but no flow
column, so the binding test is run on **price separation**, which is exact for
this LP: every PJM link has ``flow_cost = 0`` and the transport formulation has
no losses, so two zones connected by an uncongested path clear at the *same*
energy-balance dual. Therefore

    P[Dominion, t] != P[neighbour, t]   <=>   the path between them binds at t

and the sign of the difference gives the direction (Dominion dearer = Dominion
is import-constrained). This is a stronger observable than a flow histogram --
a flow can sit at its bound with zero shadow price, price separation cannot.

Three measurements, all from committed data:

* **model** -- price separation on the three Dominion-facing links
  (AEP_Ohio->Dominion 4,050 MW, West_APS->Dominion 3,000 MW,
  SWMAAC->Dominion 3,500 MW; ``iso_configs`` + ``PJM_MEASURED_INTERNAL_TTC``).
* **measured LMP** -- the same separation on PJM's published hourly hub LMPs
  (DOMINION HUB vs AEP-DAYTON HUB / CHICAGO HUB), both the total LMP and the
  congestion component, which is PJM's own statement of whether the path bound.
* **measured interface** -- utilisation of the ``AEP/DOM Post-Contingency``
  reactive-transfer interface (``transfers`` / ``transfer_limit``) from the PJM
  transfer-limits feed, the flowgate the model's AEP_Ohio->Dominion link is
  crosswalked to (``PJM_INTERFACE_LINK_MAP``).

No LP is solved and nothing is written outside ``results/probes/``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR


YEARS = (2023, 2024, 2025)

KEEPER_DIR = Path("results/calibration/pjm121_ccbelt")

# Dominion's three import neighbours in the model topology, with the TTC the
# keeper actually enforces (PJM_MEASURED_INTERNAL_TTC overrides AEP->DOM to
# 4,050 MW; the other two have no published series on their boundary and ride
# their iso_configs static -- constants.py PJM_INTERFACE_LINK_MAP notes).
DOMINION_NEIGHBOURS = {
    "PJM_AEP_Ohio": 4050.0,
    "PJM_West_APS": 3000.0,
    "PJM_SWMAAC": 3500.0,
}

# PJM published hubs standing in for the model zones in the measured LMP test.
# DOMINION HUB is the Dominion zone hub; AEP-DAYTON HUB sits inside AEP_Ohio;
# CHICAGO HUB inside ComEd. Hub-to-zone is a representative-node mapping, not a
# zonal average -- adequate for a separation/direction test, not for a level.
HUB_FOR_ZONE = {
    "PJM_Dominion": "DOMINION HUB",
    "PJM_AEP_Ohio": "AEP-DAYTON HUB",
    "PJM_ComEd": "CHICAGO HUB",
}

# A dual difference below this is numerical noise from HiGHS, not congestion.
PRICE_EPS = 1e-6

# PJM LMPs carry marginal-loss components the transport LP has no analogue for
# (td_loss_factor = 0 in the keeper), so the measured "separation" test is also
# reported at a $1/MWh threshold where losses cannot account for the gap.
MATERIAL_SPREAD = 1.0

OUT_PATH = Path("results/probes/pjm134_c2_dominion_interface.json")


def _model_prices(year: int) -> pd.DataFrame:
    """Return the keeper's P1 hourly zonal price frame for ``year``."""
    frame = pd.read_parquet(KEEPER_DIR / "hourly" / f"system_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return frame.pivot(index="hour", columns="zone", values="price")


def _model_demand(year: int) -> pd.DataFrame:
    """Return the keeper's hourly zonal demand frame for ``year``."""
    frame = pd.read_parquet(KEEPER_DIR / "hourly" / f"system_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return frame.pivot(index="hour", columns="zone", values="demand")


def _separation_stats(diff: np.ndarray, eps: float) -> dict[str, float]:
    """Share of hours the near zone is dearer / equal / cheaper, and levels."""
    n = diff.size
    return {
        "n_hours": int(n),
        "share_near_dearer": round(float((diff > eps).sum() / n), 4),
        "share_equal": round(float((np.abs(diff) <= eps).sum() / n), 4),
        "share_near_cheaper": round(float((diff < -eps).sum() / n), 4),
        "mean_spread": round(float(diff.mean()), 3),
        "p90_spread": round(float(np.percentile(diff, 90)), 3),
        "max_spread": round(float(diff.max()), 3),
    }


def _measured_lmp(year: int) -> pd.DataFrame:
    """Load PJM published hourly hub LMPs for ``year``, indexed by EPT hour."""
    path = RAW_DATA_DIR / "lmp-data" / f"PJM_{year}_rt_da_monthly_lmps.csv"
    frame = pd.read_csv(path)
    frame["ept"] = pd.to_datetime(frame["datetime_beginning_ept"])
    frame = frame[frame["ept"].dt.year == year]
    return frame


#: The committed dashboard payload the ASK's own §1/§2 numbers were read from.
RUN_PAYLOAD = Path("frontend/data/backcast/runs/2026-07-25-pjm-121-cc-belt.js")


def _zonal_fossil_vs_demand() -> dict[str, dict[str, dict[str, float]]]:
    """Zonal fossil generation (model vs EIA-923) against zonal demand, per year.

    ``volErr[<class>].zoneMon`` in the committed run payload gives monthly model
    and actual TWh per (zone, fossil class); summing every class that carries a
    ``zoneMon`` block gives each zone's fossil output on both sides. Demand comes
    from the keeper's own hourly sidecar, so the ratio is internally consistent.

    Nuclear, hydro and storage are NOT in ``zoneMon``, so ``model_self_supply``
    is a fossil-only share, not a net-import balance -- what is comparable is the
    model-vs-actual DIFFERENCE, which is the displaced energy.
    """
    import base64
    import gzip
    import re as _re

    text = RUN_PAYLOAD.read_text()
    b64 = _re.search(r'runGz\["[^"]+"\]="([^"]+)"', text).group(1)
    payload = json.loads(gzip.decompress(base64.b64decode(b64)))

    out: dict[str, dict[str, dict[str, float]]] = {}
    for year in YEARS:
        totals: dict[str, dict[str, float]] = {}
        for block in payload["years"][str(year)]["volErr"].values():
            zone_mon = block.get("zoneMon")
            if not zone_mon:
                continue
            for zone, series in zone_mon.items():
                row = totals.setdefault(zone, {"m": 0.0, "a": 0.0})
                row["m"] += float(sum(series["m"]))
                row["a"] += float(sum(series["a"]))
        sidecar = pd.read_parquet(KEEPER_DIR / "hourly" / f"system_{year}.parquet")
        demand = sidecar[sidecar["pass"] == "P1"].groupby("zone")["demand"].sum() / 1e6
        out[str(year)] = {
            zone: {
                "demand_twh": round(float(demand[zone]), 3),
                "fossil_model_twh": round(row["m"], 3),
                "fossil_actual_twh": round(row["a"], 3),
                "delta_twh": round(row["m"] - row["a"], 3),
                "model_self_supply": round(row["m"] / float(demand[zone]), 4),
                "actual_self_supply": round(row["a"] / float(demand[zone]), 4),
            }
            for zone, row in totals.items()
        }
    return out


def main() -> None:
    """Run the C2 measurement and write the machine-readable verdict."""
    out: dict[str, object] = {"model": {}, "measured_lmp": {}, "measured_interface": {}}

    # ---------------------------------------------------------------- model
    print("=" * 104)
    print("C2 (a) MODEL -- price separation on the Dominion-facing links")
    print("     flow_cost=0 and lossless => P[A] != P[B] iff the A-B path binds")
    print("     'Dom dearer' = Dominion is import-constrained (its own units set")
    print("     the price); 'equal' = the link is slack and the west sets Dominion")
    print("=" * 104)
    for year in YEARS:
        prices = _model_prices(year)
        print(f"\n--- {year} ---")
        print(
            f"{'link':<34}{'Dom dearer':>12}{'equal':>9}{'Dom cheaper':>13}"
            f"{'mean $/MWh':>12}{'p90':>9}"
        )
        year_rows: dict[str, object] = {}
        for near, ttc in DOMINION_NEIGHBOURS.items():
            diff = (prices["PJM_Dominion"] - prices[near]).to_numpy(dtype=float)
            stats = _separation_stats(diff, PRICE_EPS)
            stats["ttc_mw"] = ttc
            year_rows[near] = stats
            print(
                f"{near + ' -> Dominion':<34}{stats['share_near_dearer']:>12.1%}"
                f"{stats['share_equal']:>9.1%}{stats['share_near_cheaper']:>13.1%}"
                f"{stats['mean_spread']:>12.2f}{stats['p90_spread']:>9.2f}"
            )
        # The operative question is whether Dominion is separated from ALL its
        # neighbours at once: if it clears with any one of them it is being
        # served from outside.
        neigh = prices[list(DOMINION_NEIGHBOURS)].to_numpy(dtype=float)
        dom = prices["PJM_Dominion"].to_numpy(dtype=float)[:, None]
        tied_any = (np.abs(dom - neigh) <= PRICE_EPS).any(axis=1)
        year_rows["tied_to_any_neighbour_share"] = round(
            float(tied_any.sum() / tied_any.size), 4
        )
        print(
            f"{'Dominion tied to >=1 neighbour':<34}"
            f"{year_rows['tied_to_any_neighbour_share']:>12.1%}"
            "   <- share of hours Dominion does NOT set its own price"
        )
        out["model"][str(year)] = year_rows

    # --------------------------------------------------------- measured LMP
    print("\n" + "=" * 104)
    print("C2 (b) MEASURED -- the same separation in PJM's published hourly hub LMPs")
    print("     congestion component: PJM's own statement that the path bound")
    print("=" * 104)
    for year in YEARS:
        lmp = _measured_lmp(year)
        print(f"\n--- {year} ---")
        year_rows: dict[str, object] = {}
        for near in ("PJM_AEP_Ohio", "PJM_ComEd"):
            piv = lmp[lmp["pnode_name"].isin([HUB_FOR_ZONE["PJM_Dominion"], HUB_FOR_ZONE[near]])]
            for tag, col in (("da", "total_lmp_da"), ("rt", "total_lmp_rt"),
                            ("da_cong", "congestion_price_da")):
                wide = piv.pivot_table(index="ept", columns="pnode_name", values=col)
                wide = wide.dropna()
                diff = (
                    wide[HUB_FOR_ZONE["PJM_Dominion"]] - wide[HUB_FOR_ZONE[near]]
                ).to_numpy(dtype=float)
                stats = _separation_stats(diff, MATERIAL_SPREAD)
                year_rows[f"{near}_{tag}"] = stats
                print(
                    f"  DOM - {near:<14} [{tag:<7}] Dom dearer "
                    f"{stats['share_near_dearer']:>6.1%}  |spread|<=$1 "
                    f"{stats['share_equal']:>6.1%}  Dom cheaper "
                    f"{stats['share_near_cheaper']:>6.1%}  mean "
                    f"{stats['mean_spread']:>7.2f}  p90 {stats['p90_spread']:>7.2f}"
                )
        out["measured_lmp"][str(year)] = year_rows

    # --------------------------------------------------- measured interface
    print("\n" + "=" * 104)
    print("C2 (c) MEASURED -- AEP/DOM Post-Contingency interface utilisation")
    print("     the flowgate PJM_INTERFACE_LINK_MAP crosswalks AEP_Ohio->Dominion to")
    print("=" * 104)
    for year in YEARS:
        path = (
            RAW_DATA_DIR
            / "iso-specific-transmission"
            / f"PJM_{year}_transfer_limits_and_flows.csv"
        )
        frame = pd.read_csv(path)
        sub = frame[frame["transfer_limit_area"] == "AEP/DOM Post-Contingency"].copy()
        sub = sub[(sub["transfer_limit"] > 0)]
        util = (sub["transfers"] / sub["transfer_limit"]).to_numpy(dtype=float)
        row = {
            "n_hours": int(util.size),
            "median_limit_mw": round(float(sub["transfer_limit"].median()), 1),
            "median_transfer_mw": round(float(sub["transfers"].median()), 1),
            "share_forward_flow": round(float((sub["transfers"] > 0).mean()), 4),
            "util_p50": round(float(np.percentile(util, 50)), 4),
            "util_p90": round(float(np.percentile(util, 90)), 4),
            "util_p99": round(float(np.percentile(util, 99)), 4),
            "share_util_ge_90pct": round(float((util >= 0.90).mean()), 4),
            "share_util_ge_99pct": round(float((util >= 0.99).mean()), 4),
        }
        out["measured_interface"][str(year)] = row
        print(
            f"  {year}: limit p50 {row['median_limit_mw']:>7.0f} MW  transfer p50 "
            f"{row['median_transfer_mw']:>7.0f} MW  util p50 {row['util_p50']:>5.1%} "
            f"p90 {row['util_p90']:>5.1%} p99 {row['util_p99']:>5.1%}  "
            f">=90% in {row['share_util_ge_90pct']:>5.1%} of hours"
        )

    # ----------------------------------------------- model import headroom
    print("\n" + "=" * 104)
    print("C2 (d) SIZING -- Dominion import capability vs its own peak demand")
    print("=" * 104)
    total_ttc = sum(DOMINION_NEIGHBOURS.values())
    for year in YEARS:
        dem = _model_demand(year)["PJM_Dominion"].to_numpy(dtype=float)
        row = {
            "total_import_ttc_mw": total_ttc,
            "peak_demand_mw": round(float(dem.max()), 1),
            "mean_demand_mw": round(float(dem.mean()), 1),
            "ttc_over_peak": round(total_ttc / float(dem.max()), 4),
            "ttc_over_mean": round(total_ttc / float(dem.mean()), 4),
        }
        out.setdefault("sizing", {})[str(year)] = row
        print(
            f"  {year}: import TTC {total_ttc:>7.0f} MW  vs Dominion peak "
            f"{row['peak_demand_mw']:>8.0f} MW ({row['ttc_over_peak']:.1%}) / mean "
            f"{row['mean_demand_mw']:>8.0f} MW ({row['ttc_over_mean']:.1%})"
        )

    # ------------------------------------- zonal displacement (the energy read)
    print("\n" + "=" * 104)
    print("C2 (e) DISPLACEMENT -- zonal fossil generation vs zonal demand, model vs actual")
    print("     zoneMon from the committed keeper payload (m = LP TWh, a = EIA-923 TWh);")
    print("     demand from the keeper's own hourly sidecar. A zone whose fossil serves")
    print("     a SMALLER share of its own load in the model than in reality is being")
    print("     served from outside by that difference.")
    print("=" * 104)
    zonal = _zonal_fossil_vs_demand()
    for year in YEARS:
        rows = zonal[str(year)]
        print(f"\n--- {year} (TWh) ---")
        print(
            f"{'zone':<16}{'demand':>9}{'foss_mod':>10}{'foss_act':>10}"
            f"{'mod-act':>9}{'mod/dem':>9}{'act/dem':>9}"
        )
        for zone in sorted(rows):
            r = rows[zone]
            print(
                f"{zone:<16}{r['demand_twh']:>9.1f}{r['fossil_model_twh']:>10.1f}"
                f"{r['fossil_actual_twh']:>10.1f}{r['delta_twh']:>9.1f}"
                f"{r['model_self_supply']:>9.2f}{r['actual_self_supply']:>9.2f}"
            )
    out["displacement"] = zonal

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
