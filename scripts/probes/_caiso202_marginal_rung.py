"""caiso-202 lane 1 (part 2) — marginal-rung attribution of the C3a 2024/2025
overrun on the caiso-200 keeper. NO LP, NO SOLVE — committed bytes plus the
caiso-105/121/131 ``run_year(fleet_only=True)`` offer reconstruction (assembles
the fleet + availability + P0 objective, builds no matrix, calls no solver).

For every hour, the C3a gap contribution (rt_lw common weights) is attributed
to the supply rung whose modeled offer sits closest to the model's CA λ:

* the per-hub priced import legs — hub + wheel + border-carbon×(EF/EF_unspec)
  (the keeper's armed ``caiso_per_hub_intertie`` pricing rule, reconstructed
  from the SAME measured hub parquet + constants the injector uses);
* the firm blocks at their static contract prices (``caiso_perhub_firm_base``);
* the corridor export legs (corridor-mean hub − ε);
* the in-state fleet rungs by class (nearest ``mc_base`` unit with available
  capacity), the caiso-131 recon.

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso202_marginal_rung.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
YEARS = (2024, 2025)
HOURS = 8760
BUNDLE = REPO / "results/calibration/caiso200_h1_memberpanel"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
CACHE = Path(
    "/tmp/claude-0/-home-user-market-simulator/83b5b890-b443-5cad-bc14-f2130fbb32bd/scratchpad"
)

_META_RENAME = {
    "outage_source": "outage_source",
}


def actual_rt(year: int) -> np.ndarray:
    a = pd.read_parquet(ACTUAL_LMP)
    return a[a["year"] == year].set_index("hour")["rt"].reindex(range(HOURS)).to_numpy()


def sidecars(year: int) -> dict:
    d = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return {
        "price": d.pivot_table(index="hour", columns="zone", values="price"),
        "demand": d.pivot_table(index="hour", columns="zone", values="demand"),
    }


def ca_lambda(sc: dict) -> np.ndarray:
    ca = [z for z in sc["price"].columns if not str(z).startswith("WECC")]
    p = (sc["price"][ca] * sc["demand"][ca]).sum(axis=1) / sc["demand"][ca].sum(axis=1)
    return p.to_numpy()


def rubric_weights(year: int) -> np.ndarray:
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia_loader import load_demand

    return np.asarray(load_demand(ISO, year, get_iso_config(ISO))).sum(axis=0)[:HOURS]


def import_leg_prices(year: int, carbon: float) -> dict[str, np.ndarray]:
    """Reconstruct the per-hub injector's delivered import-leg prices."""
    from market_sim.data.eia_loader import measured_import_hub_prices
    from market_sim.model.interchange.import_nodes import wecc_border_carbon_adder
    from market_sim.config.fuel_trajectories import CARB_UNSPECIFIED_IMPORT_EF
    from market_sim.model.interchange.caiso import CAISO_FIRM_IMPORT_TRANCHES
    from market_sim.model.interchange.spec import (
        CAISO_IMPORT_DELIVERY_BASIS,
        IMPORT_TRANCHE_EF,
    )

    prices = measured_import_hub_prices(ISO, year, HOURS)
    border = wecc_border_carbon_adder(carbon)
    ef = IMPORT_TRANCHE_EF[ISO]
    out = {}
    for name, series in prices.items():
        if name in CAISO_FIRM_IMPORT_TRANCHES:
            continue  # firm blocks keep static contract prices under firm_base
        _loss, wheel = CAISO_IMPORT_DELIVERY_BASIS.get(name, (0.0, 0.0))
        adder = border * (ef.get(name, CARB_UNSPECIFIED_IMPORT_EF) / CARB_UNSPECIFIED_IMPORT_EF)
        out[f"imp:{name}"] = np.asarray(series, dtype=float) + wheel + adder
    # corridor export legs: corridor-mean hub - eps
    from market_sim.model.interchange.spec import CAISO_IMPORT_TRANCHE_HUB, CAISO_PER_HUB_IMPORT_ZONES

    by_zone: dict[str, list] = {}
    for name, series in prices.items():
        hub = CAISO_IMPORT_TRANCHE_HUB.get(name)
        zone = CAISO_PER_HUB_IMPORT_ZONES.get(hub) if hub else None
        if zone:
            by_zone.setdefault(zone, []).append(np.asarray(series, dtype=float))
    for z, v in by_zone.items():
        out[f"exp:{z}"] = np.mean(np.vstack(v), axis=0)
    return out


def fleet_recon(year: int) -> dict:
    p = CACHE / f"caiso202_recon_{year}.npz"
    if p.exists():
        z = np.load(p, allow_pickle=True)
        return {"cap": z["cap"], "mc": z["mc"], "klass": z["klass"]}
    import inspect

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
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    state = run_year(year, meta["iso"], HOURS, gas, {}, fleet_only=True, **kwargs)
    from market_sim.data.fleet import FUEL_TYPE_MAP

    inv = {v: k for k, v in FUEL_TYPE_MAP.items()}
    fa = state["fleet_arrays"]
    cap = (fa.pmax[:, None] * np.asarray(fa.availability, dtype=float)).astype(
        np.float32
    )
    mc = np.asarray(state["mc_base"], dtype=np.float32)
    fuel = np.array([inv.get(int(i), str(i)) for i in np.asarray(fa.fuel_type_idx)])
    uid = np.array([str(u) for u in fa.unit_ids])
    klass = np.array(
        [
            f"{f}:{u.split('_')[-1]}" if f in ("gas", "coal") else f
            for f, u in zip(fuel, uid)
        ]
    )
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(p, cap=cap, mc=mc, klass=klass)
    return {"cap": cap, "mc": mc, "klass": klass}


def main() -> None:
    from market_sim.config.fuel_trajectories import STATE_CARBON_PRICE_BY_ISO

    for year in YEARS:
        print("=" * 78)
        print(f"YEAR {year}")
        print("=" * 78)
        carbon = STATE_CARBON_PRICE_BY_ISO["CAISO"][year]
        sc = sidecars(year)
        lam = ca_lambda(sc)
        act = actual_rt(year)
        w = rubric_weights(year)
        ok = ~np.isnan(act)
        wsum = w[ok].sum()
        contrib = np.where(ok, w * (lam - np.where(ok, act, 0.0)), 0.0) / wsum

        legs = import_leg_prices(year, carbon)
        rec = fleet_recon(year)
        mc, cap, klass = rec["mc"], rec["cap"], rec["klass"]
        if mc.ndim == 1:
            mc = np.tile(mc[:, None], (1, HOURS))
        # The full runner injects biomass as an EIA-923 monthly must-run
        # profile and DROPS the raw biomass LP units (run_calibration_full
        # `_must_run_profiles` -> inject_biomass_mustrun); the keeper's
        # sidecar biomass is month-flat, confirming it. Exclude those units
        # from the marginal-rung candidates — they never clear the merit
        # order in the scored solve.
        keep = klass != "biomass"
        mc, cap, klass = mc[keep], cap[keep], klass[keep]

        pos = contrib > 0
        idx = np.where(pos)[0]
        TOL = 0.75
        cats: dict[str, float] = {}
        cat_hours: dict[str, int] = {}
        samples: dict[str, list] = {}
        for h in idx:
            best_name, best_d = None, np.inf
            for name, series in legs.items():
                d = abs(series[h] - lam[h])
                if d < best_d:
                    best_name, best_d = name, d
            # fleet: nearest unit with available cap
            avail = cap[:, h] > 1.0
            if avail.any():
                dmc = np.abs(mc[avail, h] - lam[h])
                j = int(np.argmin(dmc))
                if dmc[j] < best_d:
                    best_name, best_d = f"fleet:{klass[np.where(avail)[0][j]]}", dmc[j]
            if best_d > TOL:
                best_name = "unmatched"
            cats[best_name] = cats.get(best_name, 0.0) + contrib[h]
            cat_hours[best_name] = cat_hours.get(best_name, 0) + 1
            samples.setdefault(best_name, []).append((lam[h], act[h]))

        total_pos = contrib[pos].sum()
        print(
            f"\n  positive-gap attribution (n={pos.sum()} h, gap +{total_pos:.2f}; "
            f"tol ${TOL})"
        )
        print(f"    {'rung':<28}{'hours':>7}{'gap$':>9}{'share':>7}"
              f"{'lam p50':>9}{'act p50':>9}")
        for name, g in sorted(cats.items(), key=lambda kv: -kv[1]):
            s = np.array(samples[name])
            print(
                f"    {name:<28}{cat_hours[name]:>7}{g:>+9.3f}"
                f"{g / total_pos * 100:>6.0f}%"
                f"{np.percentile(s[:, 0], 50):>9.1f}{np.percentile(s[:, 1], 50):>9.1f}"
            )


if __name__ == "__main__":
    main()
