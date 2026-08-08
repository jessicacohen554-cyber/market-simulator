"""miso-143 shared harness — the model's OWN MISO offer stack at HEAD.

PREREG ``results/calibration/PREREG-miso143-coal-gas-merit-order-2026-08-08.md``.

**No LP solve, no keeper replay.**  The offer stack is reconstructed through
``run_calibration.run_year(fleet_only=True)`` — the orchestrator's OWN
availability-reconstruction exit, whose docstring states the contract this
session depends on: *"``mc_base`` / ``fuel_prices`` are the assembled P0
objective (fuel + VOM + carbon + NOx + EAC + coal tranches, all pricing
overlays applied) so post-solve offer-stack diagnostics read the SAME offer
prices the LP solved on — never a re-derivation that could drift"*.  That
removes the failure mode PREREG §9 named as most likely (hand-reproducing
``runner.py``'s offer sequence outside it).

**THE ONE THING THE EXIT CANNOT GIVE, disclosed here and bracketed rather than
glossed.**  ``mc_base`` is the **P0** objective.  P1 — the pass every run is
scored on — adds ``compute_monthly_markup``'s startup amortization, which is
sized from the **P0 dispatch** and is therefore not reconstructible without a
solve.  Its class incidence is not neutral to this session's question:

* **coal markup is exactly ZERO** (``compute_monthly_markup``: "Coal, nuclear
  and non-thermal fuels get zero markup"), and
* **gas CC/CT markup is positive.**

So a P0-basis reading under-prices gas relative to coal, which biases the
measured coal→gas merit-order gain **DOWNWARD**.  Every gain in this session is
therefore reported as a **BRACKET** with two named endpoints:

* ``lo`` — the pure P0 basis (markup 0 everywhere).  A **conservative lower
  bound** on the gain.
* ``hi`` — P0 plus the **v3 measured-horizon** markup ceiling
  ``startup_cost / fast_start_run_hours`` on the gas rows that carry one.  The
  measured horizon is the amortization-horizon **CEILING** (a P0 run may only
  SHORTEN it), so this markup is the **smallest** the P1 markup can be for
  those rows — the bracket is honest in the direction it claims.

The true P1 answer lies at or above ``hi`` for the rows carrying a measured
horizon.  Where a branch verdict is the same at both endpoints the bracket is
not load-bearing and the verdict stands on either; where it is not, the
boundary call is made on the **conservative** side and said so (PREREG §9).

Probe hygiene (miso-140b §6): REPO ROOT on ``sys.path`` (not just ``src/``) and
``load_zonal_shares`` asserted non-None in every entry point, even where no
per-zone demand is consumed, so the guard cannot rot.
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

KEEPER = REPO / "results/calibration/miso132_ccmin_B"
YEARS = (2023, 2024, 2025)  # rule 22 -- MISO holds NO marker
HOURS = 8760

# ---------------------------------------------------------------- windows
W1_MONTHS, W1_HOD = (6, 7), (8, 21)  # miso-142's W1 (Jun+Jul h8-20)
SUMMER_JJA = (6, 7, 8)
AFT_HOD = (12, 13, 14, 15, 16, 17)  # miso-139 §7 / miso-142's JJA h12-17

# ------------------------------------------------- sidecar class vocabulary
# TRAP 4: the explicit, ASSERTED coal alias.  plant_group is the bare "COAL"
# while the sidecar splits it three ways; an unmapped lookup silently reads
# ZERO and hands the class back as phantom headroom (~32 GW at miso-141).
COAL_COLS = ("COAL_BIT", "COAL_LIGNITE", "COAL_PRB")
GAS_COLS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP", "ST_CHP")
THERMAL_COLS = COAL_COLS + GAS_COLS + ("OTHER", "oil", "biomass")
SIDECAR_ALIAS = {"COAL": COAL_COLS}

# meta.json key -> run_year kwarg (the caiso-78/105 reconstruction convention).
_META_RENAME = {
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}


def hygiene() -> None:
    """miso-140b §6 guard — assert the measured zonal split is reachable.

    ``load_demand`` silently returns a DIFFERENT zonal allocation when the repo
    root is off ``sys.path`` (``_zonal_shares_from_raw`` imports
    ``scripts.data.curate_zonal_shares``; ``data/clean`` is gitignored so that
    raw path is the only measured route).  Same ISO total, different split — up
    to 6,747 MW per zone-hour on MISO 2025.  Asserted in every entry point even
    where no per-zone demand is consumed.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia930.zonal_shares import load_zonal_shares

    zs = load_zonal_shares("MISO", 2025, [z.name for z in get_iso_config("MISO").zones])
    assert zs is not None, "load_zonal_shares None -- repo root off sys.path"


def month_of_hour(hr: np.ndarray) -> np.ndarray:
    """Calendar month (1-12) of each hour-of-year index (non-leap basis)."""
    starts = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
    return np.searchsorted(starts, hr % HOURS, side="right").astype(int)


def windows() -> dict[str, np.ndarray]:
    """The two windows this lane is defined on, as boolean hour masks."""
    hr = np.arange(HOURS)
    mon, hod = month_of_hour(hr), hr % 24
    return {
        "W1_jun_jul_h8_20": (
            np.isin(mon, W1_MONTHS) & (hod >= W1_HOD[0]) & (hod < W1_HOD[1])
        ),
        "JJA_h12_17": np.isin(mon, SUMMER_JJA) & np.isin(hod, AFT_HOD),
    }


def fleet_state(year: int) -> dict:
    """``run_year(fleet_only=True)`` on the KEEPER's own meta.json flags.

    The caiso-105 ``fleet_state`` reconstruction, re-pointed at the MISO
    keeper: meta.json keys renamed onto the ``run_year`` signature, the generic
    scenario-override channel carried.  Returns the orchestrator's own dict --
    ``fleet``, ``fleet_arrays``, ``mc_base``, ``fuel_prices``, demand, caps.
    """
    from run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
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
    kwargs = {}
    for k, v in meta.items():
        k2 = _META_RENAME.get(k, k)
        if k2 in params and k2 not in skip:
            kwargs[k2] = v
    gp = meta["gas_prices"]
    gas_price = float(gp.get(str(year), gp.get(year, 0.0)))
    return run_year(
        year,
        meta["iso"],
        int(meta.get("hours", HOURS)),
        gas_price,
        {},
        fleet_only=True,
        **kwargs,
    )


def sidecar_classes(year: int) -> pd.DataFrame:
    """Keeper P1 class dispatch, hour x klass, with the TRAP 4/5 assertions."""
    df = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
    if "pass" in df:
        df = df[df["pass"].astype(str).str.upper() == "P1"]
    piv = df.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
    piv = piv.reindex(range(HOURS)).fillna(0.0)
    piv.columns = [str(c) for c in piv.columns]
    for c in THERMAL_COLS:
        assert c in piv.columns, (
            f"class {c!r} absent from the sidecar (have {sorted(piv.columns)}) -- "
            "an unmapped class silently reads ZERO (TRAP 4, miso-141)"
        )
    return piv


def sidecar_price(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Keeper P1 (load-weighted system price, zonal demand weight) per hour."""
    df = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    if "pass" in df:
        df = df[df["pass"].astype(str).str.upper() == "P1"]
    num = df.assign(w=df["price"] * df["demand"]).groupby("hour")["w"].sum()
    den = df.groupby("hour")["demand"].sum()
    p = (num / den).reindex(range(HOURS)).to_numpy(float)
    return p, den.reindex(range(HOURS)).to_numpy(float)


def klass_of(gens) -> np.ndarray:
    """Model class per generator row, reproducing the run's OWN klass logic.

    TRAP 5: ``plant_group`` is populated for the FOSSIL classes only; the
    sidecar's ``klass`` falls back to ``_model_class_for_unit``.  Filtering the
    fleet on ``plant_group`` silently returns ZERO units for
    hydro/OTHER/import (miso-142 hit exactly this).  Reproduced here from the
    run's own helper and asserted non-empty by the callers.
    """
    from run_calibration_full import _model_class_for_unit

    out = []
    for g in gens:
        pg = str(getattr(g, "plant_group", "") or "")
        out.append(
            pg
            if pg
            else _model_class_for_unit(
                str(g.unit_id), str(g.fuel_type), str(g.efficiency_bin)
            )
        )
    return np.array(out, dtype=object)


def markup_ceiling(gens, fleet_arrays, config) -> np.ndarray:
    """The ``hi`` bracket endpoint — a per-generator LOWER bound on P1 markup.

    ``compute_monthly_markup`` amortizes ``startup_cost`` over the P0 mean run
    length, with the CAMPD-measured ``fast_start_run_hours`` as the horizon
    **CEILING** (a P0 run may only SHORTEN the horizon, never lengthen it past
    the measured basis).  Amortizing over the ceiling therefore yields the
    **SMALLEST** markup those rows can carry under P1 -- an honest lower bound
    on a quantity this session needs bounded from below, because the markup's
    class incidence (zero on coal, positive on gas) biases the measured
    coal->gas gain downward when it is omitted.

    The startup cost itself comes from ``commitment._startup_cost`` — the
    model's OWN function (CAMPD-bin ``startup_cost_per_mw``, else the
    heat-rate-keyed ``STARTUP_PARAMS_BY_FUEL`` table), never a reimplementation
    — and every exemption ``compute_monthly_markup`` applies is applied here
    identically and from the run's own config: ``chp_startup_covered`` (a
    steam-host cogen never pays a cold start on its own account),
    ``coal_warm_committed`` (a CAMPD coal bin with a must-run floor never goes
    dark), and the ``gas_st_startup_cost`` ISO gate on ST_GAS.

    Rows with no measured horizon amortize over the P0 monthly mean run length,
    which is unknowable here; they contribute zero and their count is reported,
    never silently imputed.  That makes ``hi`` a lower bound in a second way as
    well.
    """
    from market_sim.model.commitment import _startup_cost

    chp_covered = bool(getattr(config, "chp_startup_covered", False))
    warm_coal = bool(getattr(config, "coal_warm_committed", False))
    st_gas_su = bool(getattr(config, "gas_st_startup_cost", False))

    n = len(gens)
    out = np.zeros(n, dtype=float)
    for i, g in enumerate(gens):
        if chp_covered and getattr(g, "plant_group", None) in (
            "CC_CHP",
            "CT_CHP",
            "ST_CHP",
        ):
            continue
        if (
            warm_coal
            and g.fuel_type == "coal"
            and float(getattr(g, "must_run_pct", 0.0) or 0.0) > 0.0
        ):
            continue
        if g.fuel_type == "gas_st" and not st_gas_su:
            continue
        su = float(_startup_cost(g, float(fleet_arrays.heat_rate[i])))
        if su <= 0.0:
            continue
        horizon = float(getattr(g, "fast_start_run_hours", 0.0) or 0.0)
        if horizon <= 0.0:
            continue
        # startup_cost is $/MW of capacity; amortized $/MWh over the horizon,
        # floored at the model's own max(horizon, 1.0).
        out[i] = su / max(horizon, 1.0)
    return out


def clear(offer: np.ndarray, cap: np.ndarray, need: float) -> tuple[float, int]:
    """Merit-order clearing offer and marginal row for ONE hour.

    ``offer`` and ``cap`` are 1-D per-generator arrays for the hour; ``need``
    is the MW the stack must serve.  Returns ``(clearing_offer, row)``; when
    the stack cannot reach ``need`` the top of the observed stack is returned
    with row = -1, which the callers report rather than extrapolate (a flat
    model must never be credited with a tail it never reaches).
    """
    order = np.argsort(offer, kind="stable")
    cum = np.cumsum(cap[order])
    j = int(np.searchsorted(cum, need, side="left"))
    if j >= order.size:
        return float(offer[order[-1]]), -1
    return float(offer[order[j]]), int(order[j])


def clear_many(
    offer: np.ndarray, cap: np.ndarray, need: np.ndarray, hours: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """:func:`clear` over a set of hours. ``offer``/``cap`` are (n_gen, T)."""
    p = np.empty(hours.size, dtype=float)
    row = np.empty(hours.size, dtype=int)
    for k, t in enumerate(hours):
        p[k], row[k] = clear(offer[:, t], cap[:, t], float(need[k]))
    return p, row
