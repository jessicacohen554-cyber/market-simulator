"""nyiso-181 — the nyiso-179 offer reconstruction, diagnosed exactly and repaired.

**POST-HOC. NOT A PRE-REGISTERED GATE.** This is a root-cause diagnosis of a
discrepancy the pre-registered instrument surfaced, in the nyiso-180 §6
discipline: the gate record was written first
(``_nyiso181_itm_degeneracy.json``, ``_nyiso181_unit_dispatch_nyiso180gates.json``),
and nothing here moves a bar. It rests on an EXACT identity, not a threshold.

**What the gates surfaced.** Run on the LP's own installed offer (the ``mc``
column PR #4650 added to ``unit_hourly``), the in-the-money-un-run ``ST_GAS``
object measures 0.073 / 0.061 / 0.070 TWh a year against the 3.84 / 9.09 / 3.99
TWh nyiso-179 §6.1 published, and ``R_aggregate`` 0.992 / 0.991 / 0.992 against
0.767 / 0.522 / 0.740.

**Why.** ``nyiso179_st_gas_offer_position.build_year`` reconstructs the offer
OUTSIDE the solve as ``assemble_mc(fa, fuel, 0.0, 0.0, so2=(fa.so2_rate, 0.0))``
and omits two armed, keeper-registered terms:

1. **The measured RGGI allowance price.** NYISO carries a state carbon program
   and the keeper arms ``state_carbon_pricing=True``, so the runner charges
   ``resolve_carbon_price(config, year)`` — $13.49 / $20.71 / $22.09 per tCO2 in
   2023 / 2024 / 2025. The reconstruction hardcodes ``0.0``.
2. **``apply_gas_offer_margin``**, the mc-side half of
   ``gas_offer_net_revenue_margin=True`` (zonal anchor $2.03-3.90/MMBtu), which
   ``runner.py:2494`` applies AFTER ``assemble_mc``. The reconstruction never
   calls it.

Together they under-state the class's offer by a median $9.57 / $15.39 / $11.98
per MWh, which is why 23.9 % / 46.4 % / 20.5 % of bin-hours were counted as in
the money when the LP's own offer puts them out of it.

**The identity that proves it** — zero free parameters, zero thresholds:
restoring both terms reproduces the LP's installed ``mc`` to ``max|d| = 0`` on
every one of 88 units x 8,760 hours, in all three years. The capacity basis was
never in doubt and is re-verified here at ``max|d| ~ 1.7e-5`` MW.

Usage:
    python scripts/probes/nyiso181_offer_reconstruction_repair.py <replay-bundle> [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.data.fleet.legacy_bins import assemble_mc  # noqa: E402
from market_sim.data.fuel import resolve_fuel_prices  # noqa: E402
from market_sim.data.offer_curves import apply_gas_offer_margin  # noqa: E402
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from scripts.probes import nyiso179_st_gas_offer_position as p179  # noqa: E402
from scripts.probes.nyiso178_offer_side_idling import lp_fleet  # noqa: E402

YEARS = (2023, 2024, 2025)
KLASS = "ST_GAS"
HOURS = 8760


def _fmt(x) -> float | None:
    if x is None:
        return None
    v = float(x)
    return None if not np.isfinite(v) else round(v, 6)


def _lp_arrays(bundle: Path, year: int, unit_ids: list[str]) -> pd.DataFrame:
    """The LP's own (mc, cap_mw, mw) for the class, pivoted unit x hour."""
    u = pd.read_parquet(bundle / "hourly" / f"unit_hourly_{year}.parquet")
    if "pass" in u.columns:
        u = u[u["pass"].astype(str) == "P1"]
    return u[u["plant_group"].astype(str) == KLASS]


def analyse_year(bundle: Path, year: int) -> dict:
    gens, fa = lp_fleet(year, p179._cfg_obj())
    cfg_y = p179._cfg_obj().with_overrides(weather_year=year)
    grp = np.asarray([str(g or "") for g in fa.plant_group])
    idx = np.nonzero(grp == KLASS)[0]

    fuel = resolve_fuel_prices(cfg_y, fa, year)
    carbon = resolve_carbon_price(cfg_y, year)

    mc_179 = assemble_mc(fa, fuel, 0.0, 0.0, so2=(fa.so2_rate, 0.0))
    mc_carbon = assemble_mc(fa, fuel, carbon, 0.0, so2=(fa.so2_rate, 0.0))
    mc_full = mc_carbon.copy()
    apply_gas_offer_margin(mc_full, gens, fuel, cfg_y)

    uid = [str(fa.unit_ids[g]) for g in idx]
    lp = _lp_arrays(bundle, year, uid)
    piv_mc = lp.pivot_table(index="unit_id", columns="hour", values="mc", aggfunc="first")
    piv_cap = lp.pivot_table(index="unit_id", columns="hour", values="cap_mw", aggfunc="first")
    piv_mw = lp.pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="first")
    common = [x for x in uid if x in piv_mc.index]
    sel = np.array([uid.index(x) for x in common])

    B = piv_mc.loc[common].to_numpy()
    cap_lp = piv_cap.loc[common].to_numpy()
    mw_lp = piv_mw.loc[common].to_numpy()
    cap_179 = (fa.pmax[idx][:, None] * fa.availability[idx, :])[sel]

    zones = [z.name for z in __import__(
        "market_sim.config.iso_configs", fromlist=["get_iso_config"]
    ).get_iso_config("NYISO").zones]
    zprice = p179._model_zone_price(year, zones)
    px = np.vstack([zprice[str(zones[int(fa.zone_idx[g])])] for g in idx[sel]])

    stages = {
        "nyiso179_assemble_mc_alone": mc_179[idx][sel],
        "plus_rggi_carbon": mc_carbon[idx][sel],
        "plus_rggi_and_offer_margin": mc_full[idx][sel],
    }
    ident = {}
    for name, A in stages.items():
        d = A - B
        ident[name] = {
            "median_recon_minus_lp": _fmt(np.median(d)),
            "mean_recon_minus_lp": _fmt(d.mean()),
            "max_abs_delta": _fmt(np.abs(d).max()),
            "share_bin_hours_differing_gt_0_01": _fmt(np.mean(np.abs(d) > 0.01)),
            "EXACT": bool(np.abs(d).max() <= 1e-4),
        }

    # nyiso-179's OWN G1 statistic, on the defective and the repaired offer.
    # mo(t) is its numerator: the class's total hourly dispatch. Taken here
    # from the LP's own per-unit frame so the class basis carries no
    # dual-fuel undercount (nyiso-180 §5).
    mo = np.nan_to_num(mw_lp).sum(axis=0)
    g1 = {}
    for name, A in (("nyiso179_published_basis", stages["nyiso179_assemble_mc_alone"]),
                    ("repaired_basis", stages["plus_rggi_and_offer_margin"])):
        itm_cap = np.where(A <= px, cap_179, 0.0).sum(axis=0)
        r = mo / np.maximum(itm_cap, 1.0)
        g1[name] = {
            "median_R": _fmt(np.median(r)),
            "aggregate_R_all_hours": _fmt(mo.sum() / max(itm_cap.sum(), 1.0)),
            "mean_itm_cap_mw": _fmt(itm_cap.mean()),
            "mean_class_dispatch_mw": _fmt(mo.mean()),
            "share_bin_hours_in_the_money": _fmt(float((A <= px).mean())),
        }

    itm_full = stages["plus_rggi_and_offer_margin"] <= px
    itm_179 = stages["nyiso179_assemble_mc_alone"] <= px
    spurious = itm_179 & ~itm_full

    return {
        "year": year,
        "units": len(common),
        "rggi_allowance_price_usd_per_tco2": _fmt(carbon),
        "capacity_basis_max_abs_delta_mw": _fmt(np.abs(cap_179 - cap_lp).max()),
        "offer_identity": ident,
        "nyiso179_G1_statistic": g1,
        "spurious_in_the_money": {
            "share_of_bin_hours": _fmt(spurious.mean()),
            "mean_capacity_mw": _fmt(np.where(spurious, cap_179, 0.0).sum() / HOURS),
            "median_lp_mc_minus_price_usd": _fmt(
                np.median((stages["plus_rggi_and_offer_margin"] - px)[spurious])
            )
            if spurious.any()
            else None,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    bundle = args.bundle if args.bundle.is_absolute() else REPO / args.bundle

    report = {
        "bundle": str(bundle.relative_to(REPO)),
        "status": "POST-HOC root-cause diagnosis; NOT a pre-registered gate",
        "years": {str(y): analyse_year(bundle, y) for y in YEARS},
    }
    report["identity_closes_all_years"] = all(
        v["offer_identity"]["plus_rggi_and_offer_margin"]["EXACT"]
        for v in report["years"].values()
    )
    out = args.out or (REPO / "results/calibration/_nyiso181_offer_reconstruction_repair.json")
    out.write_text(json.dumps(report, indent=2))
    json.dump(report, sys.stdout, indent=2)
    print(f"\n\nwrote {out}")


if __name__ == "__main__":
    main()
