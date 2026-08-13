"""miso-156 — decompose MISO's C3a mean-LMP miss into IDENTITY / COST-LEVEL / ABOVE-COST.

Pre-registration:
``results/calibration/PREREG-miso156-c3a-three-channel-decomposition-2026-08-13.md``
(pushed at ``162a51d``, blob ``7f124d18``, verified byte-identical against the
FETCHED remote ref BEFORE any adjudicating statistic was computed).

THE OBJECT (PREREG section 0). The keeper ``2026-08-09-miso-148-basis-aware``
scores **NOT-YET** on two load-bearing FAILs, C3a-2025 **-15.6 %** and C3b-2025
NRMSE **0.212**. miso-152 localized the miss to **June/July** (-27.9 / -30.9 %,
17 % of hours carrying 46 % of the annual gap) with the model's summer p99
sitting BELOW its own rest-of-year p99; miso-153 identified ``CT_PEAKER`` as
the peak price-setter; miso-155 closed the volume instrument (CT volumes to
~1 %). The Potomac Economics MISO IMM measures the system price-cost mark-up at
+3.0 % (2023) / -2.5 % (2024) with a de-minimis output gap, so MISO's real
market clears essentially AT COST. A level miss on a market that clears at cost,
with the right volumes, is therefore a statement about **which unit is marginal**
or **what that unit costs** -- or about hours no unit's cost explains.

THE DECOMPOSITION (PREREG section 3), an EXACTLY ADDITIVE per-zone-hour identity.
With ``IHR = (P - V) / G`` the implied heat rate, ``V`` the model's own
capacity-weighted gas VOM and ``HRmax`` the highest heat rate among the model's
gas tranches with headroom in that hour::

    D3 = max(0, P_act - (HRmax * G_act + V))          ABOVE-COST
    D2 = IHR_mod * (G_act - G_mod)                     COST LEVEL (fuel)
    D1 = G_act * (IHR*_act - IHR_mod)                  MARGINAL-UNIT IDENTITY
    IHR*_act = (P_act - D3 - V) / G_act

    D1 + D2 + D3 == P_act - P_mod                      (identically; gate V3)

Reported at three grains x three years: **annual** (the C3a grain, and the only
adjudicating one), **June+July** (miso-152's concentration) and the **top-200**
model-demand hours (miso-153's window).

THE FLOORS (PREREG section 2). ``results/calibration/*/floors/`` is GITIGNORED
(``.gitignore:443``), so miso-155's mandated "read the floors from the bundle"
correction is **not reproducible from a fresh checkout**. This probe instead
calls the PRODUCTION floor engine -- ``inject_reliability_floor`` driven by
``RELIABILITY_FLOOR_REGISTRY`` through the same override/drop chain
``run_calibration.py:3307-3372`` composes -- and **gates it** (V2) against
miso-155's committed ``FLOOR_source`` record. ``_miso134.build_year`` stops
before that registry, which is the miso-155 finding.

VALIDITY GATES, all run BEFORE any adjudicating statistic (PREREG section 7):

* **V1** -- the probe's load-weighted model mean reproduces the registered C3a
  (-1.98 / -8.03 / -15.58 %) to +/-0.5 pp.
* **V2** -- the rebuilt floors reproduce miso-155's committed CT floor TWh to
  0.5 % and its floored-row counts exactly. A miss fires **S-FLOORBLIND**.
* **V3** -- the decomposition identity holds elementwise to 1e-9.
* **V4** -- ``n_gen`` reproduces 2929 / 2923 / 2923; carry zones == 6.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds neither marker.

Usage::

    PYTHONPATH=$PWD:$PWD/src .venv/bin/python \\
        scripts/probes/_miso156_c3a_decomposition.py
"""

from __future__ import annotations

import dataclasses
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (
    str(REPO),
    str(REPO / "src"),
    str(REPO / "scripts" / "probes"),
    str(REPO / "scripts" / "data"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _miso134_ct_night_order_screen as _m134  # noqa: E402

# T-1: _miso134 is HARD-WIRED to miso132_ccmin_B. Repoint to THIS lane's keeper
# and assert, before anything reads it.
BUNDLE = REPO / "results/calibration/miso148_basis_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"keeper bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE
assert _m134.BUNDLE == BUNDLE, "T-1: bundle repoint failed"

from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from market_sim.config.iso_configs import (  # noqa: E402
    RELIABILITY_FLOOR_REGISTRY,
    apply_reliability_floor_overrides,
    drop_drag_owned_reliability_specs,
    drop_obligation_owned_reliability_specs,
    get_iso_config,
)
from market_sim.data.fuel.hubs import _GAS_FUEL_IDX  # noqa: E402
from market_sim.data.renewables import load_renewable_profiles  # noqa: E402
from market_sim.model.interchange.core import inject_reliability_floor  # noqa: E402

# T-8: the floor engine must be the PRODUCTION one, never a re-implementation.
assert (
    inject_reliability_floor.__module__ == "market_sim.model.interchange.core"
), "T-8: inject_reliability_floor is not the production function"

YEARS = (2023, 2024, 2025)
OUT = REPO / "results/calibration/_miso156_c3a_decomposition.json"
CARRY = (
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
)

# ── Pre-registered gate constants (PREREG sections 6-7) ────────────────────
V1_PUBLISHED_C3A = {2023: -0.0198, 2024: -0.0803, 2025: -0.1558}
V1_TOL_PP = 0.005                      # +/-0.5 pp
V4_NGEN = {2023: 2929, 2024: 2923, 2025: 2923}
# miso-155's committed FLOOR_source record (results/calibration/
# _miso155_p0_exact_instrument.json), the target V2 must reproduce.
V2_M155_FLOOR = {
    2023: {"ct_mwh": 2845651.1787029505, "ct_rows": 158, "ct_max_mw": 144.6054229736328,
           "fleet_mwh": 117439452.37886085},
    2024: {"ct_mwh": 2877270.772639036, "ct_rows": 150, "ct_max_mw": 144.6054229736328,
           "fleet_mwh": 120699732.79016909},
    2025: {"ct_mwh": 2867716.6446470916, "ct_rows": 153, "ct_max_mw": 144.6054229736328,
           "fleet_mwh": 121859264.32636231},
}
V2_TOL_FRAC = 0.005                    # 0.5 % on the TWh figures
V3_TOL = 1e-9
BRANCH_DOMINANT = 0.50                 # B-IDENT / B-COST threshold
BRANCH_ABOVE = 0.40                    # B-ABOVE threshold
S_CEIL_CAPSHARE = 0.005                # HRmax owner < 0.5 % of gas capacity
T20_MIN_GAS = 0.50                     # $/MMBtu floor below which IHR explodes
T21_SPREAD = 1.0                       # $/MWh cross-zone spread -> congested


# ---------------------------------------------------------------------------
# Measured inputs
# ---------------------------------------------------------------------------


def measured_gas_monthly(year: int) -> np.ndarray:
    """Return the (12,) measured MISO delivered gas price, $/MMBtu.

    PREREG section 3.2 PRIMARY basis: the hub-month spot, i.e. Henry Hub monthly
    plus the measured MISO hub basis row -- the marginal opportunity cost of gas
    a cost-based offer is built from.
    """
    hh = pd.read_csv(REPO / "data/raw/gas-prices/henry_hub_monthly.csv")
    hh = hh[hh["year"] == year].set_index("month")["price_usd_mmbtu"]
    bs = pd.read_csv(REPO / "data/raw/gas_basis_by_iso_month.csv")
    bs = bs[(bs["iso"] == "MISO") & (bs["year"] == year)].set_index("month")
    out = np.full(12, np.nan)
    for m in range(1, 13):
        if m in hh.index and m in bs.index:
            out[m - 1] = float(hh.loc[m]) + float(bs.loc[m, "basis_usd_mmbtu"])
    return out


def measured_rt_zonal(year: int) -> np.ndarray:
    """Return the (8760, 6) measured MISO RT LMP, PER CARRY ZONE, model calendar.

    **T-22, resolved rather than approximated.** The first construction averaged
    the eight named trading hubs equally, which over-weights MISO-South 4:1 (four
    of the eight hubs -- ARKANSAS/LOUISIANA/TEXAS/MS -- map to that one zone in
    ``derive_miso_hub_lmp.HUB_TO_ZONE``) and read 6-7 % below the scorer's own
    bench. This reads the COMMITTED per-zone validation series
    ``data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet``, whose
    system companion ``actual_lmp_hourly_MISO.parquet`` reproduces the bench
    ``avgLMP.rt`` exactly (31.789 / 30.796 / 42.850), collapses hub->zone within
    each zone, and returns it aligned to ``CARRY``.

    Scoring zone-against-zone also makes the decomposition locational: MISO-South
    model price is compared with MISO-South measured price, not with an ISO mean.
    """
    d = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
    )
    d = d[d["year"] == year]
    piv = d.groupby(["hour", "zone"])["rt"].mean().unstack("zone")
    return piv.reindex(index=range(8760), columns=list(CARRY)).to_numpy(float)


def measured_rt_system(year: int) -> np.ndarray:
    """Return the (8760,) measured MISO RT LMP on the SCORER's own basis.

    **T-22, the PRIMARY basis.** ``actual_lmp_hourly_MISO.parquet`` reproduces the
    committed bench ``avgLMP.rt`` exactly (31.789 / 30.796 / 42.850), and weighting
    it by the model's own zonal demand reproduces the GATED ``rt_lw``
    (32.847/32.301/45.455 against 32.85/32.30/45.46, gate V1b). The decomposition's
    ``gap`` is therefore the C3a miss itself, not a near neighbour of it.

    The per-zone series (:func:`measured_rt_zonal`) is a DIFFERENT object -- it
    weights the eight named hubs equally inside each zone, four of which are
    MISO-South, and runs 7.2-9.0 % below the bench. It is reported as the
    locational COMPANION, never as the adjudicating basis.
    """
    d = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet")
    d = d[d["year"] == year].set_index("hour")["rt"]
    return d.reindex(range(8760)).to_numpy(float)


def _delivered_to_electric_power(year: int, mb: dict, gas: np.ndarray) -> float:
    """Capacity-weighted MISO delivered-to-electric-power gas price, $/MMBtu.

    NOT PRE-REGISTERED (PREREG section 10) -- a third measured comparator added
    so the S-SIGN sign claim does not rest on the single Chicago-hub proxy.
    ``data/raw/miso_zonal_gas_hub.csv`` carries each model zone's measured EIA
    delivered-to-electric-power basis vs Henry Hub; weights are the model's own
    gas capacity per zone.
    """
    hh = pd.read_csv(REPO / "data/raw/gas-prices/henry_hub_monthly.csv")
    hh_y = float(hh[hh["year"] == year]["price_usd_mmbtu"].mean())
    zb = pd.read_csv(REPO / "data/raw/miso_zonal_gas_hub.csv")
    zb = zb[zb["year"] == year].set_index("zone")["basis_vs_hh_usd_mmbtu"]
    pmax = np.asarray(mb["arrays"].pmax, float)
    zone_of = mb["zone_of"]
    zone_names = mb["zone_names"]
    num = den = 0.0
    for zi, zname in enumerate(zone_names):
        if zname not in zb.index:
            continue
        w = float(pmax[gas & (zone_of == zi)].sum())
        num += w * (hh_y + float(zb.loc[zname]))
        den += w
    return float(num / den) if den > 0 else float("nan")


def bench_actuals(year: int) -> dict:
    """Return the scorer's own committed ``bench.avgLMP`` block for ``year``."""
    p = REPO / f"frontend/data/backcast/bench/MISO/{year}.json.gz"
    with gzip.open(p, "rt") as fh:
        return json.load(fh)["bench"]["avgLMP"]


# ---------------------------------------------------------------------------
# The model side, WITH the reliability floors applied by the production engine
# ---------------------------------------------------------------------------


def model_year(
    cfg, year: int, *, apply_floors: bool = True, demand_bundle=None
) -> dict:
    """Assemble the keeper's fleet for ``year`` and apply the production floors.

    T-6: ``_apply_outage_overlays`` keys the CAMPD derate on
    ``config.weather_year`` (``data/fleet/arrays.py:1091-1092``), not the solve
    year, so the config is pinned per solve year before ``build_year``.
    """
    cfg_y = dataclasses.replace(cfg, weather_year=year)
    raw_fleet, fleet, arrays, fuel_prices, mc_base, zone_names = build_year(cfg_y, year)

    # T-5: the two MISO_external* rows are IMPORT NODES, not carry zones.
    carry_idx = [zone_names.index(z) for z in CARRY]
    assert len(carry_idx) == 6, "T-5: carry-zone count != 6"

    # S-FLOORBLIND root-cause leg: miso-155's committed FLOOR_source was read off
    # the CONTROL bundle miso155_p0_C, not off this keeper, and the two solves are
    # bit-identical ONLY in 2025 (2024 differs in 8 of 70,080 price cells, 2023 in
    # 1,220). ``demand_bundle`` selects which solve's own committed demand drives
    # the netload-driver limbs, so the gate can be scored against the same solve
    # it was recorded from.
    dsrc = Path(demand_bundle) if demand_bundle else BUNDLE
    sysf = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    price = sysf.pivot_table(index="hour", columns="zone", values="price")
    dsys = pd.read_parquet(dsrc / f"hourly/system_{year}.parquet")
    dsys = dsys[dsys["pass"] == "P1"]
    dem = dsys.pivot_table(index="hour", columns="zone", values="demand")
    hours = int(price.shape[0])

    # Per-zone demand in zone_names order, for the netload-driver limbs.
    dz = np.zeros((len(zone_names), hours))
    for i, z in enumerate(zone_names):
        if z in dem.columns:
            dz[i] = dem[z].to_numpy()

    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        "MISO", year, get_iso_config("MISO"), cfg_y
    )

    # PREREG section 2 -- the production floor chain, composed exactly as
    # run_calibration.py:3307-3372 composes it.
    specs = apply_reliability_floor_overrides(
        RELIABILITY_FLOOR_REGISTRY.get("MISO", []),
        cfg_y.reliability_floor_overrides,
    )
    specs = drop_drag_owned_reliability_specs(specs, cfg_y)
    specs = drop_obligation_owned_reliability_specs(specs, cfg_y)
    n_enabled = sum(1 for s in specs if s.enabled)
    applied = apply_floors and bool(cfg_y.reliability_floor) and inject_reliability_floor(
        arrays, "MISO", year, specs, zone_names,
        demand=dz, wind_cf=wind_cf, wind_cap=wind_cap,
        solar_cf=solar_cf, solar_cap=solar_cap,
    )

    labels = np.array([str(g.plant_group or "") for g in fleet])
    zone_of = np.array([zone_names.index(str(g.zone)) for g in fleet])
    min_gen = (
        np.zeros_like(arrays.availability)
        if arrays.min_gen is None
        else np.asarray(arrays.min_gen, float)
    )
    availcap = arrays.pmax[:, None] * arrays.availability
    return {
        "cfg": cfg_y, "fleet": fleet, "arrays": arrays, "fuel_prices": fuel_prices,
        "mc_base": mc_base, "zone_names": zone_names, "carry_idx": carry_idx,
        "price": price, "demand_zone": dz, "hours": hours, "labels": labels,
        "zone_of": zone_of, "min_gen": min_gen, "availcap": availcap,
        "floor_applied": applied, "n_enabled_limbs": n_enabled,
        "demand_bundle": str(dsrc.name),
    }


def v2_floor_gate(mb: dict, year: int) -> dict:
    """**V2** -- do the rebuilt floors reproduce miso-155's committed record?"""
    ct = mb["labels"] == "CT_PEAKER"
    fl = mb["min_gen"]
    tgt = V2_M155_FLOOR[year]
    ct_mwh = float(fl[ct].sum())
    fleet_mwh = float(fl.sum())
    rows = int((fl[ct].sum(axis=1) > 0).sum())
    d_ct = abs(ct_mwh - tgt["ct_mwh"]) / tgt["ct_mwh"]
    d_fl = abs(fleet_mwh - tgt["fleet_mwh"]) / tgt["fleet_mwh"]
    # S-FLOORBLIND localization: the per-row CT floor energies, smallest first.
    per_row = np.sort(fl[ct].sum(axis=1))[::-1]
    nz = per_row[per_row > 0]
    return {
        "ct_floor_mwh": ct_mwh, "m155_ct_floor_mwh": tgt["ct_mwh"],
        "ct_floor_rel_err": d_ct,
        "fleet_floor_mwh": fleet_mwh, "m155_fleet_floor_mwh": tgt["fleet_mwh"],
        "fleet_floor_rel_err": d_fl,
        "ct_rows_floored": rows, "m155_ct_rows_floored": tgt["ct_rows"],
        "ct_max_mw": float(fl[ct].max()), "m155_ct_max_mw": tgt["ct_max_mw"],
        "n_enabled_limbs": mb["n_enabled_limbs"], "floor_applied": mb["floor_applied"],
        "smallest_floored_ct_rows_mwh": [float(v) for v in nz[-4:]],
        "marginal_row_share_of_ct_floor": float(nz[-1] / ct_mwh) if nz.size else None,
        "pass": bool(
            d_ct <= V2_TOL_FRAC and d_fl <= V2_TOL_FRAC and rows == tgt["ct_rows"]
        ),
    }


def v1_c3a_gate(mb: dict, year: int) -> dict:
    """**V1** -- reproduce the registered C3a from committed artifacts."""
    price = mb["price"]
    sysf = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    sysf = sysf[(sysf["pass"] == "P1") & (sysf["zone"].isin(CARRY))]
    w = sysf["demand"].to_numpy()
    p = sysf["price"].to_numpy()
    model_lw = float((p * w).sum() / w.sum())
    av = bench_actuals(year)
    actual = float(av["rt_lw"])
    err = model_lw / actual - 1.0
    return {
        "model_lw_mean": model_lw, "actual_rt_lw": actual,
        "c3a_pct": err * 100.0, "published_c3a_pct": V1_PUBLISHED_C3A[year] * 100.0,
        "delta_pp": (err - V1_PUBLISHED_C3A[year]) * 100.0,
        "n_zone_hours": int(len(p)), "carry_zones": int(price.shape[1] and len(CARRY)),
        "pass": bool(abs(err - V1_PUBLISHED_C3A[year]) <= V1_TOL_PP),
    }


# ---------------------------------------------------------------------------
# The decomposition
# ---------------------------------------------------------------------------


def _month_of_hour(hours: int, year: int) -> np.ndarray:
    idx = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    return idx.month.to_numpy() - 1


def decompose(mb: dict, year: int) -> dict:
    """The PREREG section 3 three-channel decomposition, per zone-hour."""
    T = mb["hours"]
    mo = _month_of_hour(T, year)
    arrays = mb["arrays"]

    gas = np.isin(arrays.fuel_type_idx, _GAS_FUEL_IDX)
    assert gas.sum() > 0, "no gas tranches"
    hr = np.asarray(arrays.heat_rate, float)
    vom = np.asarray(arrays.vom, float)
    pmax = np.asarray(arrays.pmax, float)

    # V -- the model's own capacity-weighted gas VOM. A constant, not a knob.
    V = float((vom[gas] * pmax[gas]).sum() / pmax[gas].sum())

    # G_mod -- the model's delivered gas LEVEL, capacity-weighted over its gas
    # tranches (PREREG section 3: the level is the channel-(ii) object; using the
    # marginal tranche's own price would confound level with which-plant, which
    # belongs to channel (i)).
    fp = np.asarray(mb["fuel_prices"], float)
    fp_gas = fp[gas] if fp.ndim == 2 else np.broadcast_to(fp[gas][:, None], (int(gas.sum()), T))
    w = pmax[gas][:, None]
    G_mod_t = (fp_gas * w).sum(axis=0) / w.sum()

    # Headroom-weighted counter-measurement (T-7).
    head = np.maximum(mb["availcap"] - mb["min_gen"], 0.0)[gas]
    hw = head.sum(axis=0)
    G_mod_head_t = np.where(
        hw > 0, (fp_gas * head).sum(axis=0) / np.where(hw > 0, hw, 1.0), G_mod_t
    )

    G_act_t = measured_gas_monthly(year)[mo]
    # NOT PRE-REGISTERED (labelled per PREREG section 10): a THIRD measured
    # comparator, so the S-SIGN claim does not rest on the single Chicago-hub
    # proxy the PRIMARY basis uses. data/raw/miso_zonal_gas_hub.csv carries the
    # per-zone EIA DELIVERED-TO-ELECTRIC-POWER basis vs Henry Hub (annual) --
    # what MISO plants actually pay, capacity-weighted here across the six carry
    # zones with the model's own gas capacity as the weight.
    G_act_dtep = _delivered_to_electric_power(year, mb, gas)

    # HRmax -- the highest heat rate among gas tranches with HEADROOM this hour.
    # Floors matter here: a fully floored tranche offers no headroom.
    has_head = head > 1e-6
    hr_gas = hr[gas][:, None]
    HRmax_t = np.where(has_head, hr_gas, -np.inf).max(axis=0)
    # S-CEIL: who owns HRmax, and what capacity share do they carry?
    owner = np.where(has_head, hr_gas, -np.inf).argmax(axis=0)
    gp = pmax[gas]
    counts = np.bincount(owner, minlength=int(gas.sum())).astype(float)
    top_owner = int(counts.argmax())
    # Capacity share of the tranche that owns HRmax in the most hours.
    owner_share = float(gp[top_owner] / gp.sum())
    # Capacity-weighted p99 gas heat rate (the S-CEIL sensitivity basis).
    _o = np.argsort(hr[gas])
    _cw = np.cumsum(gp[_o]) / gp.sum()
    hr_p99 = float(hr[gas][_o][int(np.searchsorted(_cw, 0.99))])
    # S-CEIL sensitivity ceiling: the p99 heat rate, still masked to headroom.
    HRp99_t = np.where(has_head, np.minimum(hr_gas, hr_p99), -np.inf).max(axis=0)

    price = mb["price"].reindex(columns=CARRY).to_numpy()          # (T, 6)
    sysf = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    dem = sysf.pivot_table(index="hour", columns="zone", values="demand")
    wgt = dem.reindex(columns=CARRY).to_numpy()                     # (T, 6)

    # T-21: congestion means an LMP need not equal any unit's mc. Measure it.
    spread = price.max(axis=1) - price.min(axis=1)
    congested = float(np.mean(spread > T21_SPREAD))

    # Measured actual (T-22). PRIMARY = the scorer's own system basis, broadcast
    # across zones; COMPANION = the per-zone hub series, reported never gated.
    Pact = np.broadcast_to(measured_rt_system(year)[:T, None], price.shape)
    Pzon = measured_rt_zonal(year)[:T]                              # (T, 6)
    av = bench_actuals(year)

    # T-20: IHR explodes for tiny G or P below VOM. Count, report, EXCLUDE.
    Pa = Pact
    Ga = np.broadcast_to(G_act_t[:, None], price.shape)
    Gm = np.broadcast_to(G_mod_t[:, None], price.shape)
    bad_h = (
        (G_act_t <= T20_MIN_GAS)
        | ~np.isfinite(G_act_t)
        | (G_mod_t <= T20_MIN_GAS)
    )
    # T-20: IHR explodes for tiny G or for a price below VOM. Count, report,
    # EXCLUDE -- never silently clip.
    bad = (
        np.broadcast_to(bad_h[:, None], price.shape)
        | (Pa < V)
        | (price < V)
        | ~np.isfinite(price)
        | ~np.isfinite(Pa)
    )
    ok = ~bad

    # V1b -- the measured side reconciles to the scorer's own load-weighted bench.
    _w = np.where(np.isfinite(Pa), wgt, 0.0)
    act_lw = float((np.nan_to_num(Pa) * _w).sum() / _w.sum())
    recon_lw = act_lw / float(av["rt_lw"]) - 1.0
    _wz = np.where(np.isfinite(Pzon), wgt, 0.0)
    zon_lw = float((np.nan_to_num(Pzon) * _wz).sum() / _wz.sum())

    IHR_mod = (price - V) / Gm

    def _channels(hr_ceiling: np.ndarray):
        """Return (D1, D2, D3, IHR*_act) for one ceiling basis."""
        hrc = hr_ceiling[:, None]
        d3 = np.maximum(0.0, Pa - (hrc * Ga + V))
        ihr_star = (Pa - d3 - V) / Ga
        d2 = IHR_mod * (Ga - Gm)
        d1 = Ga * (ihr_star - IHR_mod)
        return d1, d2, d3, ihr_star

    D1, D2, D3, IHR_act_star = _channels(HRmax_t)
    # S-CEIL (PREREG section 6.1) fires when the HRmax owner carries < 0.5 % of gas
    # capacity: report the whole decomposition again on the capacity-weighted p99
    # ceiling, as a DECLARED, LABELLED sensitivity alongside the primary.
    D1p, D2p, D3p, IHR_star_p99 = _channels(HRp99_t)
    total = Pa - price

    # V3 -- the identity, elementwise.
    resid = np.abs(D1 + D2 + D3 - total)
    v3_max = float(np.nanmax(np.where(ok, resid, 0.0)))

    def _agg(mask: np.ndarray) -> dict:
        m = mask & ok
        if not m.any():
            return {"n_zone_hours": 0}
        ww = np.where(m, wgt, 0.0)
        s = ww.sum()
        g = lambda a: float((np.where(m, a, 0.0) * ww).sum() / s)  # noqa: E731
        tot = g(total)
        d1, d2, d3 = g(D1), g(D2), g(D3)
        return {
            "n_zone_hours": int(m.sum()),
            "mean_P_act": g(np.broadcast_to(Pa, price.shape)),
            "mean_P_mod": g(price),
            "gap_usd_mwh": tot,
            "D1_identity_usd_mwh": d1,
            "D2_costlevel_usd_mwh": d2,
            "D3_abovecost_usd_mwh": d3,
            "D1_share": (d1 / tot) if abs(tot) > 1e-9 else None,
            "D2_share": (d2 / tot) if abs(tot) > 1e-9 else None,
            "D3_share": (d3 / tot) if abs(tot) > 1e-9 else None,
            "mean_G_act": g(np.broadcast_to(Ga, price.shape)),
            "mean_G_mod": g(np.broadcast_to(Gm, price.shape)),
            "mean_IHR_mod": g(IHR_mod),
            "mean_IHR_act_star": g(IHR_act_star),
            "mean_HRmax": g(np.broadcast_to(HRmax_t[:, None], price.shape)),
        }

    def _agg_p99(mask: np.ndarray) -> dict:
        m = mask & ok
        if not m.any():
            return {"n_zone_hours": 0}
        ww = np.where(m, wgt, 0.0)
        sden = ww.sum()
        g = lambda a: float((np.where(m, a, 0.0) * ww).sum() / sden)  # noqa: E731
        tot = g(total)
        d1, d2, d3 = g(D1p), g(D2p), g(D3p)
        return {
            "gap_usd_mwh": tot,
            "D1_identity_usd_mwh": d1, "D2_costlevel_usd_mwh": d2,
            "D3_abovecost_usd_mwh": d3,
            "D1_share": (d1 / tot) if abs(tot) > 1e-9 else None,
            "D2_share": (d2 / tot) if abs(tot) > 1e-9 else None,
            "D3_share": (d3 / tot) if abs(tot) > 1e-9 else None,
            "mean_IHR_act_star": g(IHR_star_p99),
            "mean_HR_ceiling": g(np.broadcast_to(HRp99_t[:, None], price.shape)),
        }

    allm = np.ones_like(price, dtype=bool)
    jj = np.broadcast_to(((mo == 5) | (mo == 6))[:, None], price.shape)
    iso_dem = wgt.sum(axis=1)
    top200 = np.zeros(T, dtype=bool)
    top200[np.argsort(-iso_dem)[:200]] = True
    t200 = np.broadcast_to(top200[:, None], price.shape)

    # PREREG section 3.1 -- where does IHR*_act land in the model's OWN available
    # gas heat-rate distribution, and where does IHR_mod land?
    def _pct_in_fleet(vals: np.ndarray, mask: np.ndarray) -> dict:
        hs = hr[gas]
        wcap = gp
        order = np.argsort(hs)
        hs_s, w_s = hs[order], wcap[order]
        cw = np.cumsum(w_s) / w_s.sum()
        v = vals[mask]
        pcts = np.interp(v, hs_s, cw, left=0.0, right=1.0)
        inside = (v >= hs_s[0]) & (v <= hs_s[-1])
        return {
            "median_pctile": float(np.median(pcts)),
            "share_inside_fleet_hr_range": float(np.mean(inside)),
            "median_value": float(np.median(v)),
            "fleet_hr_min": float(hs_s[0]), "fleet_hr_max": float(hs_s[-1]),
        }

    def _class_at_hr(vals: np.ndarray, mask: np.ndarray) -> dict:
        """PREREG section 3.1, second half -- WHICH CLASS sits at that heat rate.

        For each admitted zone-hour, find the model gas tranche whose own heat
        rate is nearest the given implied heat rate and report the capacity-
        weighted class mix. Answers "what kind of unit would have to be marginal
        for the market's price to be a cost-based price".
        """
        hs = hr[gas]
        cls = mb["labels"][gas]
        order = np.argsort(hs)
        hs_s, cls_s, w_s = hs[order], cls[order], gp[order]
        v = vals[mask]
        j = np.clip(np.searchsorted(hs_s, v), 0, hs_s.size - 1)
        out: dict[str, float] = {}
        for c, wq in zip(cls_s[j], w_s[j]):
            out[str(c)] = out.get(str(c), 0.0) + 1.0
        tot = sum(out.values()) or 1.0
        return {k: v2 / tot for k, v2 in sorted(out.items(), key=lambda kv: -kv[1])}

    jj_ok = jj & ok
    census = {
        "class_at_IHR_act_star_junjul": _class_at_hr(IHR_act_star, jj_ok),
        "class_at_IHR_mod_junjul": _class_at_hr(IHR_mod, jj_ok),
        "class_at_IHR_act_star_top200": _class_at_hr(IHR_act_star, t200 & ok),
        "class_at_IHR_mod_top200": _class_at_hr(IHR_mod, t200 & ok),
        "IHR_act_star_junjul": _pct_in_fleet(IHR_act_star, jj_ok),
        "IHR_mod_junjul": _pct_in_fleet(IHR_mod, jj_ok),
        "IHR_act_star_annual": _pct_in_fleet(IHR_act_star, ok),
        "IHR_mod_annual": _pct_in_fleet(IHR_mod, ok),
    }

    return {
        "V_gas_vom": V,
        "n_gas_tranches": int(gas.sum()),
        "T20_excluded_zone_hours": int((~ok).sum()),
        "T20_excluded_share": float(np.mean(~ok)),
        "T21_congested_hour_share": congested,
        "T22_zonal_actual_vs_bench_rt_lw_rel": recon_lw,
        "T22_zonal_actual_lw_mean": act_lw,
        "T22_bench_rt_lw": float(av["rt_lw"]),
        "V1b_pass": bool(abs(recon_lw) <= 0.005),
        "T22_COMPANION_zonal_hub_lw_mean": zon_lw,
        "T22_COMPANION_zonal_vs_primary_rel": zon_lw / act_lw - 1.0,
        "S_CEIL_hrmax_owner_capshare": owner_share,
        "S_CEIL_hrmax_top_owner_hr": float(hr[gas][top_owner]),
        "S_CEIL_gas_hr_p99": hr_p99,
        "V3_identity_max_abs_resid": v3_max,
        "V3_pass": bool(v3_max <= V3_TOL),
        "G_mod_annual_capwt": float(G_mod_t.mean()),
        "G_mod_annual_headwt": float(G_mod_head_t.mean()),
        "G_act_annual_hubspot": float(np.nanmean(G_act_t)),
        "G_act_annual_delivered_to_electric_power": G_act_dtep,
        "S_SIGN_G_mod_minus_G_act_hubspot": float(G_mod_t.mean() - np.nanmean(G_act_t)),
        "S_SIGN_G_mod_minus_G_act_dtep": float(G_mod_t.mean() - G_act_dtep),
        "annual": _agg(allm),
        "jun_jul": _agg(jj),
        "top200": _agg(t200),
        "S_CEIL_SENSITIVITY_p99_ceiling": {
            "annual": _agg_p99(allm), "jun_jul": _agg_p99(jj), "top200": _agg_p99(t200),
        },
        "census_3_1": census,
    }


def main() -> dict:
    cfg = keeper_config()
    out = {
        "prereg": "PREREG-miso156-c3a-three-channel-decomposition-2026-08-13.md",
        "prereg_commit": "162a51d", "prereg_blob": "7f124d18",
        "bundle": BUNDLE.name, "years": {},
    }
    for year in YEARS:
        mb = model_year(cfg, year)
        v4 = {
            "n_gen": len(mb["fleet"]), "published_n_gen": V4_NGEN[year],
            "carry_zones": len(mb["carry_idx"]),
            "pass": bool(len(mb["fleet"]) == V4_NGEN[year] and len(mb["carry_idx"]) == 6),
        }
        v2 = v2_floor_gate(mb, year)
        v1 = v1_c3a_gate(mb, year)
        rec = {"V4_fleet": v4, "V2_floors": v2, "V1_c3a": v1}
        # S-FLOORBLIND root-cause leg: re-score V2 with the CONTROL bundle's own
        # committed demand -- the solve miso-155 actually read its floors from.
        ctrl = REPO / "results/calibration/miso155_p0_C"
        if ctrl.is_dir():
            mbc = model_year(cfg, year, demand_bundle=ctrl)
            rec["V2_floors_on_control_demand"] = v2_floor_gate(mbc, year)
        if v1["pass"] and v4["pass"]:
            rec["decomposition"] = decompose(mb, year)
            # S-FLOORBLIND fired at V2, so the floor rebuild is not certified
            # equal to the solve's. The FLOORS-OFF twin brackets any floor error
            # by a perturbation ~100x larger than the measured V2 miss: if the
            # channel shares are invariant across it, a 0.2-1.2 % floor
            # discrepancy provably cannot move the adjudicating statistic.
            mb0 = model_year(cfg, year, apply_floors=False)
            rec["decomposition_FLOORS_OFF"] = decompose(mb0, year)
        else:
            rec["decomposition"] = {"SKIPPED": "validity gate failed"}
        out["years"][str(year)] = rec
        print(f"[{year}] V4 {v4['pass']}  V2 {v2['pass']} "
              f"(ct {v2['ct_floor_mwh']/1e6:.4f} TWh vs {v2['m155_ct_floor_mwh']/1e6:.4f}, "
              f"{100*(v2['ct_floor_mwh']/v2['m155_ct_floor_mwh']-1):+.2f}%, "
              f"rows {v2['ct_rows_floored']}/{v2['m155_ct_rows_floored']})  "
              f"V1 {v1['pass']} ({v1['c3a_pct']:+.2f}% vs {v1['published_c3a_pct']:+.2f}%)",
              flush=True)
        d = rec["decomposition"]
        if "annual" in d:
            for grain in ("annual", "jun_jul", "top200"):
                a = d[grain]
                print(f"    {grain:8s} gap {a['gap_usd_mwh']:+7.3f}  "
                      f"D1 {a['D1_usd'] if 'D1_usd' in a else a['D1_identity_usd_mwh']:+7.3f} "
                      f"({100*(a['D1_share'] or 0):5.1f}%)  "
                      f"D2 {a['D2_costlevel_usd_mwh']:+7.3f} ({100*(a['D2_share'] or 0):5.1f}%)  "
                      f"D3 {a['D3_abovecost_usd_mwh']:+7.3f} ({100*(a['D3_share'] or 0):5.1f}%)",
                      flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
