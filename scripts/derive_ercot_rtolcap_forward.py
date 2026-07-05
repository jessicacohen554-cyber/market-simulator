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

    Returns ``(online_reserve, offline_cap, class_cap)`` dicts keyed by model
    class, each an ``(8760,)`` MW array (class_cap a scalar), computed from the
    committed CAMPD extracts and the model nameplate/derate. Everything here is a
    measured physical quantity (CAMPD gross output + model capacity), never a
    price and never the LP's own dispatch.
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
    # Online capacity (of committed units) — the base for the OFF-line remainder.
    ph["online_cap"] = np.where(online, eff_cap, 0.0)

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
    for grp in class_cap:
        sub = ph[ph["grp"] == grp]
        onl = np.zeros(HOURS)
        oncap = np.zeros(HOURS)
        v = sub.groupby("hour_of_year")["online_reserve"].sum()
        onl[v.index.to_numpy()] = v.to_numpy()
        v = sub.groupby("hour_of_year")["online_cap"].sum()
        oncap[v.index.to_numpy()] = v.to_numpy()
        # Off-line startable capacity = class total (summer-derated) − on-line.
        class_eff = class_cap[grp] * (1.0 - np.where(summer_hr, class_derate[grp], 0.0))
        online_reserve[grp] = onl
        offline_cap[grp] = np.clip(class_eff - oncap, 0.0, None)
    return online_reserve, offline_cap, class_cap


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
        online_reserve, offline_cap, class_cap = _class_hourly(year)
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


def _fmt_table(tbl: np.ndarray) -> str:
    rows = []
    for s in range(N_SEASON):
        vals = ", ".join(f"{v:.4f}" for v in tbl[s])
        rows.append(f"        ({vals}),")
    return "\n".join(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--emit", choices=["report", "constant"], default="report")
    args = ap.parse_args()

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
