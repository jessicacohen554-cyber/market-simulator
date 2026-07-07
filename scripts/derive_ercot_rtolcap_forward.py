#!/usr/bin/env python
"""Derive ERCOT's forward RTOLCAP/RTOFFCAP online-responsive reserve-supply shares.

The forward analogue of the measured ERCOT on-line responsive reserve-supply cap
(``scarcity.ercot_rtolcap_supply_cap_mw``, which reads
``data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet`` and returns ``None``
for any year with no measured parquet — so forecast years run UNCAPPED and the
whole ORDC-era supply re-scope goes inert forward). WS-A of
``docs/handoffs/ercot-as-coopt-plan-2026-07.md``: the last AS-path lever with no
forward analogue.

Construction (derived committed-share × capability, the
``MAINTENANCE_MONTHLY_SHAPE`` / ST_GAS-drag derive-script family):

    RTOLCAP_fwd(t)  = deliv × Σ_c online_share_c(nl_decile(t), season(t)) × cap_c(year,t)
                      + online_storage_power(t)
    RTOFFCAP_fwd(t) = deliv × Σ_{c∈quick} offline_share_c(nl_decile(t), season(t)) × cap_c(year,t)

* ``online_share_c`` — per responsive class ``c``, the **on-line
  reserve-realization share**: the median over the committed CAMPD unit extracts
  of ``Σ_online (eff_cap − gross) / installed_cap`` for the class, conditioned on
  the net-load percentile decile and the season. ``eff_cap`` is the model
  nameplate summer-derated (``fleet._SUMMER_CLASS_DERATE``); "online" is a unit
  generating (gross > 1 MW, i.e. CF > 0). RTOLCAP is the on-line *headroom*
  (HSL − telemetered basepoint) an ORDC deployment can call, **not** a strict
  10-minute-ramp slice — the measured series (~13.5/16.7/19.1 GW) runs ~1.8× the
  fleet's aggregate 10-min ramp (~9 GW ramp-limited headroom), so the share is a
  headroom fraction of *installed capacity*, not of ``ramp10`` (a rule-#11
  finding documented in the handoff; 10-min ramp physics still gates the
  RTOFFCAP quick-start eligibility below). The share is a function of the model's
  own forecast net-load, so it regenerates for a forecast year and responds to
  changed conditions (more VRE → different net-load regime → different share).
* ``offline_share_c`` — for the quick-start classes (CT/oil), the share of
  installed capacity **off-line and startable** (1 − online, availability-
  limited), the RTOFFCAP analogue.
* ``cap_c(year, t)`` — the class's installed reserve-eligible capacity from the
  model fleet, summer-derated per hour; regenerates as the fleet evolves.
* ``deliv`` — a single deliverability coefficient fit to the measured
  RTOLCAP/RTOFFCAP **MW quantity** (like G3's ASPLANNP433 requirement fit),
  never a price (CLAUDE.md #12); it centers the pooled-year level.

Rule #23: the shares re-derive ONLY when their source data updates — the
committed CAMPD unit extracts (``data/raw/campd-{unit,facility}-level/TX_*.parquet``)
and the measured reserve-capability series
(``data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet``). They must NOT be
re-fit because a price/backcast residual moved. A re-derivation commit cites the
data change.

Honesty gate (this task): the derive reads the measured RTOLCAP/RTOFFCAP MW
QUANTITY series only — nothing on the path touches LMP / RTSPP / MCPC / RTORPA
(those columns of the parquet are never read here).

Run ``python scripts/derive_ercot_rtolcap_forward.py`` for the report /
validation preview, or ``--emit constant`` for the paste-ready constant block.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.eia_loader import load_demand  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    RAMP10_FRAC_BY_GROUP,
    _SUMMER_CLASS_DERATE,
    load_fleet_from_csv,
)
from market_sim.data.renewables import load_renewable_profiles  # noqa: E402

HOURS = 8760
YEARS = (2023, 2024, 2025)

# The responsive thermal classes whose on-line headroom forms RTOLCAP (the model
# plant groups carrying a 10-min ramp fraction — i.e. reserve-eligible thermal).
RTOLCAP_CLASSES = (
    "COAL",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
)
# Quick-start classes whose OFF-LINE capacity forms RTOFFCAP (fast-start
# simple-cycle CT / oil peakers — reachable within the off-line deployment
# window; the same physics gate as scarcity.QUICK_START_FUEL_TYPES).
RTOFFCAP_CLASSES = ("CT_PEAKER", "CT_CHP")

# Season index by calendar month (0=winter DJF, 1=spring MAM, 2=summer JJA,
# 3=fall SON): the maintenance/commitment seasonality the share conditions on,
# alongside the net-load decile (which carries the diurnal/tightness signal).
_SEASON_BY_MONTH = np.array([0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0])
N_SEASON = 4
N_DECILE = 10  # net-load percentile deciles

_MONTH_START_HOUR = np.array(
    [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016]
)


def _hour_month() -> np.ndarray:
    """Calendar month (1-12) for each of the 8760 non-leap hour-of-year slots."""
    hod = pd.date_range("2023-01-01", periods=HOURS, freq="h")
    return hod.month.to_numpy()


def _season_index() -> np.ndarray:
    """Season index (0-3) for each of the 8760 hours."""
    return _SEASON_BY_MONTH[_hour_month() - 1]


def _net_load_decile(net_load: np.ndarray) -> np.ndarray:
    """Within-year net-load percentile decile (0-9) per hour, vectorized.

    The decile is the driver axis the share conditions on: rank the year's
    net-load and bucket into ten equal-count bins. A forecast year ranks its OWN
    net-load, so the mapping regenerates and a changed VRE build shifts which
    hours fall in which decile.
    """
    order = np.argsort(np.argsort(net_load))  # ascending rank per hour
    return np.minimum((order * N_DECILE) // len(net_load), N_DECILE - 1)


def _fleet_class_maps(year: int):
    """Return (plant_group, plant_cap, summer_derate) maps for ERCOT ``year``.

    ``plant_group`` maps each CAMPD plant code to its dominant model class;
    ``plant_cap`` its model nameplate MW; ``summer_derate`` the class Jun-Sep
    ambient derate fraction.
    """
    iso = get_iso_config("ERCOT")
    gens = load_fleet_from_csv("ERCOT", iso, year=year)
    plant_cap: dict[int, float] = {}
    plant_class_cap: dict[tuple[int, str], float] = {}
    for g in gens:
        grp = getattr(g, "plant_group", "") or ""
        if RAMP10_FRAC_BY_GROUP.get(grp) is None:
            continue  # non-responsive (nuclear/hydro/wind/solar/storage)
        pc = int(g.plant_code)
        if pc <= 0:
            continue
        plant_cap[pc] = plant_cap.get(pc, 0.0) + float(g.pmax_mw)
        plant_class_cap[(pc, grp)] = plant_class_cap.get((pc, grp), 0.0) + float(
            g.pmax_mw
        )
    dominant: dict[int, tuple[str, float]] = {}
    for (pc, grp), cap in plant_class_cap.items():
        if pc not in dominant or cap > dominant[pc][1]:
            dominant[pc] = (grp, cap)
    plant_group = {pc: v[0] for pc, v in dominant.items()}
    summer_derate = {
        pc: _SUMMER_CLASS_DERATE.get(plant_group[pc], 0.0) for pc in plant_group
    }
    return plant_group, plant_cap, summer_derate


def _net_load(year: int) -> np.ndarray:
    """ERCOT forecast net-load MW (8760) = served load − wind − solar."""
    sc = ScenarioConfig(iso="ERCOT", weather_year=year, mode="backcast")
    iso = get_iso_config("ERCOT")
    demand = load_demand(
        "ERCOT", year, iso, td_loss_factor=sc.td_loss_factor, include_interchange=True
    )
    wcf, wcap, scf, scap = load_renewable_profiles("ERCOT", year, iso, sc)
    H = min(HOURS, demand.shape[1])
    nl = np.zeros(HOURS)
    nl[:H] = (
        demand[:, :H].sum(0)
        - (wcap[:, None] * wcf[:, :H]).sum(0)
        - (scap[:, None] * scf[:, :H]).sum(0)
    )
    return nl


def _class_hourly(year: int):
    """Per-class hourly on-line headroom + off-line quick-start capacity (MW).

    Returns ``(online_reserve, offline_cap, class_cap, online_cap, online_gross)``
    dicts keyed by model class, each an ``(8760,)`` MW array (class_cap a scalar),
    computed from the committed CAMPD extracts and the model nameplate/derate.
    ``online_cap`` is the summer-derated nameplate (HSL) of the class's ON-LINE
    (committed, gross > 1 MW) units per hour — the on-line *capacity* envelope
    (the base for the G-22 commitment-thinness energy+reserve cap), distinct from
    ``online_reserve`` which is that envelope MINUS the on-line gross (the RTOLCAP
    headroom). ``online_gross`` is the class's on-line gross output per hour, so
    the identity ``online_cap - online_gross == online_reserve`` holds cell-by-cell
    (the measured-data anchor: ``online_cap - gross`` reproduces measured RTOLCAP).
    Everything here is a measured physical quantity (CAMPD gross output + model
    capacity), never a price and never the LP's own dispatch.
    """
    plant_group, plant_cap, summer_derate = _fleet_class_maps(year)
    df = campd.load_campd_hourly(["TX"], [year])
    df = df[df["plant_id"].isin(plant_group)].copy()
    ph = df.groupby(["plant_id", "hour_of_year"])["gross_mw"].sum().reset_index()
    ph["grp"] = ph["plant_id"].map(plant_group)
    ph["cap"] = ph["plant_id"].map(plant_cap)
    ph["derate"] = ph["plant_id"].map(summer_derate)
    ph["gross"] = ph["gross_mw"].clip(lower=0.0)
    summer = np.isin(_hour_month()[ph["hour_of_year"].to_numpy()], [6, 7, 8, 9])
    eff_cap = ph["cap"].to_numpy() * (
        1.0 - np.where(summer, ph["derate"].to_numpy(), 0.0)
    )
    online = ph["gross"].to_numpy() > 1.0
    ph["online_reserve"] = np.where(
        online, np.clip(eff_cap - ph["gross"].to_numpy(), 0.0, None), 0.0
    )
    # Online capacity (summer-derated HSL of committed units) — the base for both
    # the OFF-line remainder (RTOFFCAP) AND the G-22 on-line-capacity envelope.
    ph["online_cap"] = np.where(online, eff_cap, 0.0)
    # Online gross output of committed units (the envelope's energy term anchor;
    # online_cap - online_gross == online_reserve, the measured RTOLCAP identity).
    ph["online_gross"] = np.where(online, ph["gross"].to_numpy(), 0.0)

    # Class capacity = the CAMPD-covered nameplate of the class (the denominator
    # the reserve-realization fraction is normalized by; ERCOT thermal is almost
    # entirely EPA-reporting, so this ≈ the model class capacity the forward
    # formula multiplies back). Per-class summer-derate factor for the hourly
    # class-total on-line-headroom base of RTOFFCAP.
    summer_hr = np.isin(_hour_month(), [6, 7, 8, 9])
    class_cap: dict[str, float] = {}
    class_derate: dict[str, float] = {}
    for grp in set(plant_group.values()):
        pcs = [p for p in plant_cap if plant_group[p] == grp]
        class_cap[grp] = float(sum(plant_cap[p] for p in pcs))
        class_derate[grp] = _SUMMER_CLASS_DERATE.get(grp, 0.0)

    online_reserve: dict[str, np.ndarray] = {}
    offline_cap: dict[str, np.ndarray] = {}
    online_cap: dict[str, np.ndarray] = {}
    online_gross: dict[str, np.ndarray] = {}
    for grp in class_cap:
        sub = ph[ph["grp"] == grp]
        onl = np.zeros(HOURS)
        oncap = np.zeros(HOURS)
        ongross = np.zeros(HOURS)
        v = sub.groupby("hour_of_year")["online_reserve"].sum()
        onl[v.index.to_numpy()] = v.to_numpy()
        v = sub.groupby("hour_of_year")["online_cap"].sum()
        oncap[v.index.to_numpy()] = v.to_numpy()
        v = sub.groupby("hour_of_year")["online_gross"].sum()
        ongross[v.index.to_numpy()] = v.to_numpy()
        # Off-line startable capacity = class total (summer-derated) − on-line.
        class_eff = class_cap[grp] * (1.0 - np.where(summer_hr, class_derate[grp], 0.0))
        online_reserve[grp] = onl
        offline_cap[grp] = np.clip(class_eff - oncap, 0.0, None)
        online_cap[grp] = oncap
        online_gross[grp] = ongross
    return online_reserve, offline_cap, class_cap, online_cap, online_gross


def derive():
    """Derive the online/offline share tables + deliverability coefficient.

    Returns ``(online_share, offline_share, deliv, preview)`` where the shares
    are ``{class: (N_SEASON, N_DECILE) array}`` of the reserve-realization
    fraction, ``deliv`` the pooled-year level coefficient, and ``preview`` the
    per-year validation dict.
    """
    from market_sim.results.scarcity import ercot_storage_as_reserve_mw

    season = _season_index()
    per_year = {}
    for year in YEARS:
        online_reserve, offline_cap, class_cap, _oncap, _ongross = _class_hourly(year)
        nl = _net_load(year)
        decile = _net_load_decile(nl)
        per_year[year] = (online_reserve, offline_cap, class_cap, decile)

    # Pooled (season, decile) median share per class, over all years — a shape
    # that is not pinned to any one backcast year (rule #23).
    def _share(kind: str) -> dict[str, np.ndarray]:
        classes = RTOLCAP_CLASSES if kind == "online" else RTOFFCAP_CLASSES
        out: dict[str, np.ndarray] = {}
        for grp in classes:
            frac_cells = [[[] for _ in range(N_DECILE)] for _ in range(N_SEASON)]
            for year in YEARS:
                onl, off, ccap, decile = per_year[year]
                cap = ccap.get(grp, 0.0)
                if cap <= 0:
                    continue
                series = (onl if kind == "online" else off).get(grp)
                if series is None:
                    continue
                frac = series / cap
                for s in range(N_SEASON):
                    for d in range(N_DECILE):
                        m = (season == s) & (decile == d)
                        if m.any():
                            frac_cells[s][d].append(frac[m])
            tbl = np.zeros((N_SEASON, N_DECILE))
            for s in range(N_SEASON):
                for d in range(N_DECILE):
                    if frac_cells[s][d]:
                        tbl[s, d] = float(np.median(np.concatenate(frac_cells[s][d])))
            out[grp] = tbl
        return out

    online_share = _share("online")
    offline_share = _share("offline")

    # Fit the deliverability coefficient to the measured RTOLCAP MW quantity
    # (pooled least-squares through the storage-credited residual). Thermal-only
    # RTOLCAP portion = Σ_c share_c[season,decile] × cap_c; measured =
    # deliv × thermal + storage.
    thermal_all, meas_all, stor_all = [], [], []
    for year in YEARS:
        onl, off, ccap, decile = per_year[year]
        thermal = np.zeros(HOURS)
        for grp in RTOLCAP_CLASSES:
            cap = ccap.get(grp, 0.0)
            if cap <= 0:
                continue
            thermal += online_share[grp][season, decile] * cap
        stor = ercot_storage_as_reserve_mw(year, HOURS)
        meas = pd.read_parquet(
            REPO / f"data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"
        )["rtolcap"].to_numpy()[:HOURS]
        thermal_all.append(thermal)
        meas_all.append(meas)
        stor_all.append(stor)
    T = np.concatenate(thermal_all)
    M = np.concatenate(meas_all)
    S = np.concatenate(stor_all)
    ok = ~np.isnan(M) & (T > 0)
    deliv = float(((M[ok] - S[ok]) * T[ok]).sum() / (T[ok] ** 2).sum())

    # Separate off-line deliverability coefficient, fit to the measured RTOFFCAP
    # MW quantity — the off-line startable capacity clears a smaller reserve
    # fraction than the RTOLCAP fit implies, so RTOFFCAP carries its own level.
    offthermal_all, offmeas_all = [], []
    for year in YEARS:
        onl, off, ccap, decile = per_year[year]
        offth = np.zeros(HOURS)
        for grp in RTOFFCAP_CLASSES:
            cap = ccap.get(grp, 0.0)
            if cap <= 0:
                continue
            offth += offline_share[grp][season, decile] * cap
        offmeas = pd.read_parquet(
            REPO / f"data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"
        )["rtoffcap"].to_numpy()[:HOURS]
        offthermal_all.append(offth)
        offmeas_all.append(offmeas)
    OT = np.concatenate(offthermal_all)
    OM = np.concatenate(offmeas_all)
    ok_off = ~np.isnan(OM) & (OT > 0)
    deliv_off = float((OM[ok_off] * OT[ok_off]).sum() / (OT[ok_off] ** 2).sum())

    # Per-year validation preview.
    preview = {}
    for i, year in enumerate(YEARS):
        pred = deliv * thermal_all[i] + stor_all[i]
        meas = meas_all[i]
        ok = ~np.isnan(meas)
        preview[year] = {
            "pred_mean_gw": pred[ok].mean() / 1000.0,
            "meas_mean_gw": meas[ok].mean() / 1000.0,
            "err_pct": 100.0 * (pred[ok].mean() / meas[ok].mean() - 1.0),
            "corr": float(np.corrcoef(pred[ok], meas[ok])[0, 1]),
            "pred_p": np.percentile(pred[ok], [10, 50, 90]) / 1000.0,
            "meas_p": np.percentile(meas[ok], [10, 50, 90]) / 1000.0,
        }
    return online_share, offline_share, deliv, deliv_off, preview


# Classes forming the on-line-capacity envelope (G-22 commitment thinness). Same
# responsive-thermal set as RTOLCAP_CLASSES — the envelope caps energy+reserve
# drawn on the shared headroom at the committed on-line capacity, of which
# RTOLCAP is the un-dispatched remainder.
ONLINE_CAP_CLASSES = RTOLCAP_CLASSES

# Net-load decile at/above which the envelope is in its BINDING REGIME — the
# high-net-load hours where the co-opt's shared headroom is tight and the
# envelope decides whether reserve tightens (below it the ENERGY term keeps the
# envelope slack). deliv_env is fit to reproduce the measured on-line HSL over
# these deciles (top 30%), so the envelope reproduces the measured RTOLCAP
# capability where it operates rather than only in the annual mean.
ONLINE_CAP_BINDING_DECILE = 7  # deciles 7,8,9 of N_DECILE=10 → top 30%


def _model_class_cap(year: int) -> dict[str, float]:
    """Per-class model-fleet reserve-eligible pmax (MW) — the production cap basis.

    ``scarcity.ercot_online_capacity_envelope_mw`` builds the envelope from the
    model ``FleetArrays.pmax`` summed over the responsive-fuel generators of each
    plant_group class — NOT the derive's CAMPD-covered class nameplate (they
    differ: tranche binning, non-CAMPD units, the responsive-fuel eligibility).
    ``deliv_env`` must be fit on THIS basis so it transfers exactly to the LP;
    fitting on the CAMPD nameplate leaves the in-LP envelope ~20-30% too tight in
    the binding regime (the validator-basis mismatch). Mirrors the production
    function's class summation exactly.
    """
    from market_sim.config.reserve_config import RESERVE_FUEL_TYPES
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet import FUEL_TYPE_NAMES, generators_to_fleet_arrays

    cfg = ScenarioConfig(
        iso="ERCOT",
        weather_year=year,
        mode="backcast",
        ercot_multiproduct_as_coopt=True,
        ercot_online_capacity_envelope=True,
    )
    iso = get_iso_config("ERCOT")
    gens = load_fleet_from_csv("ERCOT", iso, year=year)
    fleet = generators_to_fleet_arrays(
        gens, [z.name for z in iso.zones], HOURS, iso="ERCOT", config=cfg, year=year
    )
    pmax = np.asarray(fleet.pmax, dtype=float)
    pg = np.asarray(getattr(fleet, "plant_group"))
    fn = np.array([FUEL_TYPE_NAMES[i] for i in fleet.fuel_type_idx])
    responsive = np.isin(fn, sorted(RESERVE_FUEL_TYPES))
    return {
        grp: float(pmax[(pg == grp) & responsive].sum()) for grp in ONLINE_CAP_CLASSES
    }


def derive_online_capacity():
    """Derive the on-line-CAPACITY share tables + envelope deliverability coef.

    The G-22 commitment-thinness anchor. Where :func:`derive` fits the on-line
    *headroom* share (RTOLCAP = HSL − gross of committed units), this fits the
    on-line *capacity* share — the committed HSL fraction itself:

        online_cap_share_c(season, decile) = median_over_years(
            Σ_online eff_cap_c / installed_cap_c )

    conditioned on the same net-load-decile × season axes. The on-line-capacity
    envelope the LP imposes is

        online_cap_env(t) = deliv_env × Σ_c online_cap_share_c(nl,season) × cap_c(t)

    capping ``Σ energy_c + Σ reserve_c ≤ online_cap_env`` on the shared-headroom
    rows, so the LP cannot dispatch (or reserve) more thermal than the real
    system had on-line — the ~3.2 GW phantom sub-$200 spare the P1
    perfect-commitment assumption manufactures beyond RTOLCAP
    (``docs/FINDING-ercot-priceshape-2026-07.md`` §3, structural conclusion #2).

    ``deliv_env`` is fit to the measured on-line HSL quantity — CAMPD on-line
    gross + measured RTOLCAP (the thermal portion, storage-AS removed) — a MW
    quantity, never a price (rule #13). The **identification anchor** (returned in
    the preview and hard-gated by ``scripts/validate_ercot_online_capacity.py``):
    ``online_cap_env(t) − CAMPD_online_gross(t)`` must reproduce the measured
    RTOLCAP series (level within ±10%, sane p10/p50/p90 band, coverage ~2× the
    AS requirement — NOT the 1.0× ercot27 artifact), so the envelope reproduces
    the measured on-line capability rather than merely tightening in the right
    direction (the MISO-43 posture-lever lesson, G-25). Rule #23: re-derives only
    on a CAMPD / measured-RTOLCAP source-data update, never a residual.
    """
    from market_sim.results.scarcity import ercot_storage_as_reserve_mw

    season = _season_index()
    per_year = {}
    for year in YEARS:
        _onl, _off, class_cap, online_cap, online_gross = _class_hourly(year)
        nl = _net_load(year)
        decile = _net_load_decile(nl)
        per_year[year] = (class_cap, online_cap, online_gross, decile)

    # Pooled (season, decile) median on-line-capacity share per class.
    online_cap_share: dict[str, np.ndarray] = {}
    for grp in ONLINE_CAP_CLASSES:
        frac_cells = [[[] for _ in range(N_DECILE)] for _ in range(N_SEASON)]
        for year in YEARS:
            ccap, oncap, ongross, decile = per_year[year]
            cap = ccap.get(grp, 0.0)
            if cap <= 0 or grp not in oncap:
                continue
            frac = oncap[grp] / cap
            for s in range(N_SEASON):
                for d in range(N_DECILE):
                    m = (season == s) & (decile == d)
                    if m.any():
                        frac_cells[s][d].append(frac[m])
        tbl = np.zeros((N_SEASON, N_DECILE))
        for s in range(N_SEASON):
            for d in range(N_DECILE):
                if frac_cells[s][d]:
                    tbl[s, d] = float(np.median(np.concatenate(frac_cells[s][d])))
        online_cap_share[grp] = tbl

    # Fit deliv_env to the measured on-line HSL quantity = CAMPD on-line gross +
    # measured RTOLCAP (thermal, storage-AS removed) — a pooled LS through the
    # gross-anchored target, so the envelope's headroom remainder reproduces the
    # measured RTOLCAP (rule #13; never a price).
    # Summer (Jun-Sep) ambient-derate mask, applied to the class cap exactly as
    # the production envelope does (scarcity.ercot_online_capacity_envelope_mw).
    summer = np.isin(_hour_month(), [6, 7, 8, 9])
    F_all, Y_all, gross_all, meas_all, stor_all, bind_all = [], [], [], [], [], []
    for year in YEARS:
        ccap, oncap, ongross, decile = per_year[year]
        mcap = _model_class_cap(year)  # PRODUCTION cap basis (model FleetArrays)
        F = np.zeros(HOURS)  # Σ_c cap_share_c[season,decile] × model cap_c (derated)
        gross = np.zeros(HOURS)  # Σ_c CAMPD on-line gross_c
        for grp in ONLINE_CAP_CLASSES:
            cap = mcap.get(grp, 0.0)
            if cap <= 0:
                continue
            derate = _SUMMER_CLASS_DERATE.get(grp, 0.0)
            cap_t = cap * (1.0 - np.where(summer, derate, 0.0))
            F += online_cap_share[grp][season, decile] * cap_t
            gross += ongross.get(grp, np.zeros(HOURS))
        stor = ercot_storage_as_reserve_mw(year, HOURS)
        meas = pd.read_parquet(
            REPO / f"data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"
        )["rtolcap"].to_numpy()[:HOURS]
        rtolcap_thermal = meas - stor  # storage-AS removed → thermal RTOLCAP
        F_all.append(F)
        Y_all.append(gross + rtolcap_thermal)  # measured on-line HSL (thermal)
        gross_all.append(gross)
        meas_all.append(meas)
        stor_all.append(stor)
        bind_all.append(decile >= ONLINE_CAP_BINDING_DECILE)
    F = np.concatenate(F_all)
    Y = np.concatenate(Y_all)
    bind = np.concatenate(bind_all)
    # Fit deliv_env to reproduce the measured on-line HSL in the BINDING REGIME
    # (top net-load deciles) — the hours where the envelope is not slack and its
    # reproduction of the measured RTOLCAP capability decides whether the co-opt
    # tightens correctly. A whole-year LS fit reproduces the annual MEAN but lets
    # the pooled-median share undershoot the *committable* capacity in the tight
    # tail (room collapses far below measured RTOLCAP → over-fire); the envelope
    # is a CAP (upper bound on what can be on-line), so it must reflect the
    # capability the tight hours actually mustered. A ratio-of-means fit over the
    # binding deciles reproduces that capability where it binds; the (harmless)
    # overshoot in the slack hours never reaches the LP because the ENERGY term
    # keeps the envelope slack there (rule #13: a measured-MW-quantity fit to the
    # RTOLCAP band, never the price).
    ok = ~np.isnan(Y) & (F > 0) & bind
    deliv_env = float(Y[ok].sum() / F[ok].sum())

    # Per-year identification preview: the envelope's headroom remainder
    # (online_cap_env − CAMPD on-line gross) vs the measured RTOLCAP series.
    preview = {}
    for i, year in enumerate(YEARS):
        env = deliv_env * F_all[i]
        headroom = env - gross_all[i]  # what the model's post-envelope spare tracks
        meas = meas_all[i]
        stor = stor_all[i]
        # Add the measured on-line storage-AS back for an apples-to-apples RTOLCAP
        # comparison (the LP's envelope + storage reserve = the full RTOLCAP row).
        headroom_full = headroom + stor
        ok = ~np.isnan(meas)
        bind = bind_all[i] & ok  # binding-regime hours (top net-load deciles)
        preview[year] = {
            "env_mean_gw": env[ok].mean() / 1000.0,
            "headroom_mean_gw": headroom_full[ok].mean() / 1000.0,
            "meas_mean_gw": meas[ok].mean() / 1000.0,
            "err_pct": 100.0 * (headroom_full[ok].mean() / meas[ok].mean() - 1.0),
            "corr": float(np.corrcoef(headroom_full[ok], meas[ok])[0, 1]),
            "headroom_p": np.percentile(headroom_full[ok], [10, 50, 90]) / 1000.0,
            "meas_p": np.percentile(meas[ok], [10, 50, 90]) / 1000.0,
            # Binding-regime reproduction (the operative tail): the headroom the
            # envelope leaves in the top-net-load hours vs measured RTOLCAP there.
            "bind_headroom_gw": headroom_full[bind].mean() / 1000.0,
            "bind_meas_gw": meas[bind].mean() / 1000.0,
            "bind_err_pct": 100.0
            * (headroom_full[bind].mean() / meas[bind].mean() - 1.0),
        }
    return online_cap_share, deliv_env, preview


# --- G-22 extreme-peak-resolved variant (envelope handoff §5 forward path) ----

# Number of net-load bins on the extreme axis: deciles 0-8 + five 2-percentile
# sub-bins of the top decile (scarcity.ercot_online_cap_extreme_bin).
N_BIN_EXTREME = 14
# Minimum pooled hours (across the source years) for a top-decile sub-bin
# share cell to stand on its own median; thinner cells inherit the parent
# decile-9 (same-season, whole-top-decile) median. One diurnal cycle of pooled
# support — the spring sub-bins carry only 2-13 pooled hours (the top decile is
# summer/winter-dominated) and a median over so few observations is noise, not
# measurement. A hierarchical coarsening to the parent cell, never a new number.
MIN_CELL_HOURS_EXTREME = 24


def derive_online_capacity_extreme():
    """Derive the EXTREME-PEAK-RESOLVED on-line-capacity share + deliv profile.

    The filed G-22 forward path (``ercot-online-capacity-envelope-2026-07.md``
    §5) after the ercot41 rejection: the base envelope reproduced measured
    RTOLCAP in the binding regime (±2%) but its pooled decile-9 median
    under-stated the *committable* capacity in the top-2% net-load hours, so the
    in-LP room collapsed (4.4/6.7 GW vs measured 8.0/11.1) and the ORDC
    over-fired. Two coupled refinements, both identified on measured MW
    quantities (rules #13/#23, never a price):

    1. **Shape — the share table resolved at 2-pp grain in the top decile**
       (:func:`market_sim.results.scarcity.ercot_online_cap_extreme_bin`,
       ``N_BIN_EXTREME`` = 14 bins): the pooled-median committed on-line HSL
       fraction rises through the top-decile sub-bins (measured CAMPD
       saturation, e.g. CT_PEAKER 0.40→0.61, ST_GAS 0.83→0.95 summer), which the
       single decile-9 median collapsed. Thin cells (< ``MIN_CELL_HOURS_EXTREME``
       pooled hours) inherit the parent decile-9 same-season median.
    2. **Level — a per-bin deliverability profile** replacing the scalar
       ``deliv_env``: ``deliv_b = pooled_mean_b(target) / pooled_mean_b(F)``
       where ``F`` is the share-composite on the production cap basis and the
       target is the measured thermal on-line HSL identity

           target(t) = CAMPD on-line gross(t)
                       + (measured RTOLCAP(t) − storage AS(t) − LR credit(t)).

       The same ratio-of-means identification as the base ``deliv_env`` fit,
       resolved on the same axis as the share — "the peak states resolved at
       finer grain" — because a single scalar provably cannot carry the
       capability margin that GROWS toward the extreme peak (the measured
       thermal RTOLCAP exceeds the CAMPD share-reconstruction by ~2.3–3.4 GW in
       the top-2%: non-CEMS capability + telemetered HSL above the summer-
       derated nameplate, exactly where scarcity operations muster everything).

    **Target-construction note (differs from the base derive, documented):** the
    base fit's target netted only storage AS out of measured RTOLCAP. The
    keeper LP *also* credits the measured load-resource RRS-UFR series against
    the reserve requirement (``ercot_load_resource_reserve``, G4), so a thermal
    envelope whose target keeps LR capability would count those MW twice. The
    extreme target nets both measured non-thermal series. Both are measured
    procurement quantities (rule #13).

    **Residual ledger (recorded, not tuned — the §3.1 pattern):** the pooled
    per-bin fit reproduces the pooled top-2% mean by construction, but the
    per-year spread remains ±~20% (2023 −23%, 2024 −2%, 2025 +18%): at a fixed
    WITHIN-YEAR rank the 2023 scarcity summer mustered more absolute capability
    (and dispatched ~4 GW more) than 2025's milder tail, and a year-symmetric
    pooled coefficient cannot span that without year-pinning (forbidden, rule
    #13). Recorded in the preview; the A/B scores what this does to dispatch.

    Rule #23: re-derives only on a CAMPD / measured-RTOLCAP / storage-AS /
    LR-credit source-data update, never a residual.

    Returns ``(share_extreme, deliv_profile, preview)``.
    """
    from market_sim.results.scarcity import (
        ercot_load_resource_reserve_mw,
        ercot_online_cap_extreme_bin,
        ercot_storage_as_reserve_mw,
    )

    season = _season_index()
    summer = np.isin(_hour_month(), [6, 7, 8, 9])
    per_year = {}
    for year in YEARS:
        _onl, _off, class_cap, online_cap, online_gross = _class_hourly(year)
        nl = _net_load(year)
        per_year[year] = (class_cap, online_cap, online_gross, nl)

    # 1. Pooled (season, bin) median on-line-capacity share per class, with the
    # thin-cell fallback to the parent decile-9 (whole-top-decile) median.
    share_extreme: dict[str, np.ndarray] = {}
    fallback_cells: list[tuple[str, int, int, int]] = []
    for grp in ONLINE_CAP_CLASSES:
        tbl = np.full((N_SEASON, N_BIN_EXTREME), np.nan)
        for s in range(N_SEASON):
            for b in range(N_BIN_EXTREME):
                vals, nh = [], 0
                for year in YEARS:
                    ccap, oncap, _g, nl = per_year[year]
                    cap = ccap.get(grp, 0.0)
                    if cap <= 0 or grp not in oncap:
                        continue
                    m = (season == s) & (ercot_online_cap_extreme_bin(nl) == b)
                    nh += int(m.sum())
                    if m.any():
                        vals.append(oncap[grp][m] / cap)
                if vals and (b < 9 or nh >= MIN_CELL_HOURS_EXTREME):
                    tbl[s, b] = float(np.median(np.concatenate(vals)))
                elif b >= 9:
                    fallback_cells.append((grp, s, b, nh))
        # Parent decile-9 cell per season = pooled median over the WHOLE top
        # decile (bins 9-13 together) — the base table's own grain.
        dec9 = np.zeros(N_SEASON)
        for s in range(N_SEASON):
            vals = []
            for year in YEARS:
                ccap, oncap, _g, nl = per_year[year]
                cap = ccap.get(grp, 0.0)
                if cap <= 0 or grp not in oncap:
                    continue
                m = (season == s) & (ercot_online_cap_extreme_bin(nl) >= 9)
                if m.any():
                    vals.append(oncap[grp][m] / cap)
            dec9[s] = float(np.median(np.concatenate(vals))) if vals else 0.0
        nanm = np.isnan(tbl)
        tbl[nanm] = np.repeat(dec9[:, None], N_BIN_EXTREME, axis=1)[nanm]
        share_extreme[grp] = tbl

    # 2. Per-bin deliverability profile on the production cap basis.
    F_y, Y_y, gross_y, meas_y, nonth_y, nl_y = {}, {}, {}, {}, {}, {}
    for year in YEARS:
        ccap, oncap, ongross, nl = per_year[year]
        mcap = _model_class_cap(year)
        b = ercot_online_cap_extreme_bin(nl)
        F = np.zeros(HOURS)
        gross = np.zeros(HOURS)
        for grp in ONLINE_CAP_CLASSES:
            cap = mcap.get(grp, 0.0)
            if cap <= 0:
                continue
            derate = _SUMMER_CLASS_DERATE.get(grp, 0.0)
            cap_t = cap * (1.0 - np.where(summer, derate, 0.0))
            F += share_extreme[grp][season, b] * cap_t
            gross += ongross.get(grp, np.zeros(HOURS))
        stor = ercot_storage_as_reserve_mw(year, HOURS)
        lr = ercot_load_resource_reserve_mw(year, HOURS)
        meas = pd.read_parquet(
            REPO / f"data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"
        )["rtolcap"].to_numpy(dtype=float)[:HOURS]
        F_y[year] = F
        Y_y[year] = gross + (meas - stor - lr)  # measured thermal on-line HSL
        gross_y[year], meas_y[year], nonth_y[year], nl_y[year] = (
            gross,
            meas,
            stor + lr,
            nl,
        )
    FF = np.concatenate([F_y[y] for y in YEARS])
    YY = np.concatenate([Y_y[y] for y in YEARS])
    BB = np.concatenate([ercot_online_cap_extreme_bin(nl_y[y]) for y in YEARS])
    ok = ~np.isnan(YY) & (FF > 0)
    deliv_profile = np.zeros(N_BIN_EXTREME)
    for b in range(N_BIN_EXTREME):
        m = ok & (BB == b)
        deliv_profile[b] = float(YY[m].sum() / FF[m].sum()) if m.any() else 1.0

    # 3. Per-year identification preview: headroom remainder vs measured RTOLCAP
    # in the binding regime (top-30%) and the extreme tail (top-2%).
    preview = {"fallback_cells": fallback_cells}
    for year in YEARS:
        b = ercot_online_cap_extreme_bin(nl_y[year])
        env = deliv_profile[b] * F_y[year]
        headroom = env - gross_y[year] + nonth_y[year]  # + measured stor+LR back
        meas = meas_y[year]
        okm = ~np.isnan(meas)
        nl = nl_y[year]
        row = {}
        for regime, mask in [
            ("all", okm),
            ("bind", (nl >= np.percentile(nl, 70)) & okm),
            ("extreme", (nl >= np.percentile(nl, 98)) & okm),
        ]:
            h = headroom[mask].mean() / 1000.0
            mm = meas[mask].mean() / 1000.0
            row[regime] = {
                "headroom_gw": h,
                "meas_gw": mm,
                "err_pct": 100.0 * (h / mm - 1.0),
            }
        row["corr"] = float(np.corrcoef(headroom[okm], meas[okm])[0, 1])
        row["headroom_p"] = np.percentile(headroom[okm], [10, 50, 90]) / 1000.0
        row["meas_p"] = np.percentile(meas[okm], [10, 50, 90]) / 1000.0
        preview[year] = row
    return share_extreme, deliv_profile, preview


def _fmt_table(tbl: np.ndarray) -> str:
    rows = []
    for s in range(N_SEASON):
        vals = ", ".join(f"{v:.4f}" for v in tbl[s])
        rows.append(f"        ({vals}),")
    return "\n".join(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--emit",
        choices=[
            "report",
            "constant",
            "online-cap-constant",
            "online-cap-report",
            "online-cap-extreme-constant",
            "online-cap-extreme-report",
        ],
        default="report",
    )
    args = ap.parse_args()

    # G-22 EXTREME-PEAK-RESOLVED on-line-capacity envelope derivation (the §5
    # forward path after the ercot41 rejection; separate emit modes so the base
    # envelope constants above stay frozen — rule #23).
    if args.emit in ("online-cap-extreme-constant", "online-cap-extreme-report"):
        share_extreme, deliv_profile, preview = derive_online_capacity_extreme()
        if args.emit == "online-cap-extreme-constant":
            print("# Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON);")
            print(
                "# each inner tuple is the 14 extreme-resolved net-load bins "
                "(deciles 0-8 + five 2-pp sub-bins of the top decile, low->high)."
            )
            print(
                "ERCOT_ONLINE_CAP_SHARE_EXTREME: "
                "dict[str, tuple[tuple[float, ...], ...]] = {"
            )
            for grp in ONLINE_CAP_CLASSES:
                print(f'    "{grp}": (')
                print(_fmt_table(share_extreme[grp]))
                print("    ),")
            print("}")
            vals = ", ".join(f"{v:.4f}" for v in deliv_profile)
            print("ERCOT_ONLINE_CAP_DELIV_PROFILE_EXTREME: tuple[float, ...] = (")
            print(f"    {vals}")
            print(")")
            return
        print(
            "=== ERCOT EXTREME-PEAK-RESOLVED on-line-capacity envelope "
            "(G-22, handoff §5) ==="
        )
        print("deliv profile (bins 0-8 deciles, 9-13 = 2-pp sub-bins of top decile):")
        print("  " + " ".join(f"{v:.3f}" for v in deliv_profile))
        fb = preview["fallback_cells"]
        print(
            f"share fallback cells (< {MIN_CELL_HOURS_EXTREME} pooled h, inherit "
            f"parent decile-9 median): {len(fb)}"
            + (f" — seasons {sorted({s for _g, s, _b, _n in fb})}" if fb else "")
        )
        print(
            "\nIdentification: (envelope − CAMPD on-line gross + measured "
            "storage-AS + LR credit) vs measured RTOLCAP\n"
        )
        print(
            f"{'year':>5} {'corr':>5}  {'hdrm p10/50/90':>20}  {'meas p10/50/90':>20}"
            f"  {'BIND h/m/err':>18}  {'EXTREME(top2%) h/m/err':>24}"
        )
        for year in YEARS:
            p = preview[year]
            pp = "/".join(f"{v:.1f}" for v in p["headroom_p"])
            mp = "/".join(f"{v:.1f}" for v in p["meas_p"])
            bind = (
                f"{p['bind']['headroom_gw']:.1f}/{p['bind']['meas_gw']:.1f}/"
                f"{p['bind']['err_pct']:+.0f}%"
            )
            ext = (
                f"{p['extreme']['headroom_gw']:.1f}/{p['extreme']['meas_gw']:.1f}/"
                f"{p['extreme']['err_pct']:+.0f}%"
            )
            print(
                f"{year:>5} {p['corr']:5.2f}  {pp:>20}  {mp:>20}  {bind:>18}  {ext:>24}"
            )
        print(
            "\nGate: scripts/validate_ercot_online_capacity.py --extreme "
            "(binding ±10% AND extreme-tail reproduction, band, coverage)."
        )
        return

    # G-22 on-line-capacity envelope derivation (separate emit modes so the
    # commitment-thinness constants can be regenerated without re-touching the
    # frozen RTOLCAP-headroom shares above).
    if args.emit in ("online-cap-constant", "online-cap-report"):
        online_cap_share, deliv_env, preview = derive_online_capacity()
        if args.emit == "online-cap-constant":
            print("# Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON);")
            print(
                "# each inner tuple is the 10 net-load-percentile deciles (low→high)."
            )
            print(
                "ERCOT_ONLINE_CAP_SHARE: dict[str, tuple[tuple[float, ...], ...]] = {"
            )
            for grp in ONLINE_CAP_CLASSES:
                print(f'    "{grp}": (')
                print(_fmt_table(online_cap_share[grp]))
                print("    ),")
            print("}")
            print(f"ERCOT_ONLINE_CAP_DELIV_COEF: float = {deliv_env:.4f}")
            return
        print("=== ERCOT on-line-CAPACITY envelope (G-22 commitment thinness) ===")
        print(
            f"envelope deliverability coefficient (fit to measured on-line HSL "
            f"MW): {deliv_env:.4f}\n"
        )
        print(
            "Identification: (envelope − CAMPD on-line gross + storage-AS) vs "
            "measured RTOLCAP\n"
        )
        print(
            f"{'year':>5} {'env GW':>7} {'hdrm GW':>8} {'meas GW':>8} {'err%':>6} "
            f"{'corr':>5}  {'hdrm p10/50/90':>22}  {'meas p10/50/90':>22}  "
            f"{'BIND hdrm/meas/err':>20}"
        )
        for year in YEARS:
            p = preview[year]
            pp = "/".join(f"{v:.1f}" for v in p["headroom_p"])
            mp = "/".join(f"{v:.1f}" for v in p["meas_p"])
            bind = f"{p['bind_headroom_gw']:.1f}/{p['bind_meas_gw']:.1f}/{p['bind_err_pct']:+.0f}%"
            print(
                f"{year:>5} {p['env_mean_gw']:7.2f} {p['headroom_mean_gw']:8.2f} "
                f"{p['meas_mean_gw']:8.2f} {p['err_pct']:+6.1f} {p['corr']:5.2f}  "
                f"{pp:>22}  {mp:>22}  {bind:>20}"
            )
        print(
            "\nGate: headroom remainder within ±10% of measured RTOLCAP, sane "
            "band, coverage ~2× (scripts/validate_ercot_online_capacity.py)."
        )
        return

    online_share, offline_share, deliv, deliv_off, preview = derive()

    if args.emit == "constant":
        print("# Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON);")
        print("# each inner tuple is the 10 net-load-percentile deciles (low→high).")
        print(
            "ERCOT_RTOLCAP_FWD_ONLINE_SHARE: dict[str, tuple[tuple[float, ...], ...]] = {"
        )
        for grp in RTOLCAP_CLASSES:
            print(f'    "{grp}": (')
            print(_fmt_table(online_share[grp]))
            print("    ),")
        print("}")
        print(
            "ERCOT_RTOLCAP_FWD_OFFLINE_SHARE: dict[str, tuple[tuple[float, ...], ...]] = {"
        )
        for grp in RTOFFCAP_CLASSES:
            print(f'    "{grp}": (')
            print(_fmt_table(offline_share[grp]))
            print("    ),")
        print("}")
        print(f"ERCOT_RTOLCAP_FWD_DELIV_COEF: float = {deliv:.4f}")
        print(f"ERCOT_RTOLCAP_FWD_OFFLINE_DELIV_COEF: float = {deliv_off:.4f}")
        return

    print("=== ERCOT forward RTOLCAP online-share (headroom-realization fraction) ===")
    print(f"deliverability coefficient (fit to measured RTOLCAP MW): {deliv:.4f}\n")
    print(
        f"{'year':>5} {'pred GW':>8} {'meas GW':>8} {'err%':>6} {'corr':>5}  "
        f"{'pred p10/50/90':>22}  {'meas p10/50/90':>22}"
    )
    for year in YEARS:
        p = preview[year]
        pp = "/".join(f"{v:.1f}" for v in p["pred_p"])
        mp = "/".join(f"{v:.1f}" for v in p["meas_p"])
        print(
            f"{year:>5} {p['pred_mean_gw']:8.2f} {p['meas_mean_gw']:8.2f} "
            f"{p['err_pct']:+6.1f} {p['corr']:5.2f}  {pp:>22}  {mp:>22}"
        )
    print(
        "\nGate: annual mean within ±10%, sane p10/50/90 band, coverage ~2× "
        "(see scripts/validate_ercot_rtolcap_forward.py)."
    )


if __name__ == "__main__":
    main()
