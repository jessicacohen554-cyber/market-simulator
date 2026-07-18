#!/usr/bin/env python
"""Derive NEISO extreme-day reliability drags for ST_GAS (overnight) + CT_PEAKER (evening).

ISO-NE analog of the PJM ST_GAS overnight drag
(``scripts/data/derive_pjm_st_gas_overnight_drag.py``) and the MISO steam-gas + CT
drag (``scripts/data/derive_miso_steamgas_ct_drag.py``), unified into one derivation.
On extreme days the energy-only LP, free to de-commit each hour, cycles two
classes out of windows a real ISO commits them in for reliability:

  * **ST_GAS — OVERNIGHT pre-positioning.** On a hot cooling day, a cold snap, or
    a high system-net-load stress day the ISO holds the lone gas-steam boiler
    committed at part load through the low-price OVERNIGHT trough (h0-6) so it
    stays warm to ramp for the NEXT afternoon/evening peak, rather than shutting
    and paying a multi-hour cold start. Hour-by-hour overnight the boiler is
    non-economic — the wrong physics for a committed steam unit on a multi-day
    event.
  * **CT_PEAKER — EVENING net-load ramp.** Simple-cycle CTs are committed for
    local Resource Adequacy during the afternoon-evening net-load ramp (cooling
    load climbs while solar collapses at sunset). Overnight their capacity factor
    is ~0, so a floor there would bind them in hours their own driver evidence
    says they are OFFLINE — a rule-12 off-window bug (the exact failure that
    scrubbed the old all-24h NEISO CT_PEAKER limbs, 2026-07-05). The floor is
    windowed to the evening ramp only.

For each NEISO model zone and each of the two classes it emits up to THREE limbs
into ``reliability_floor_coeffs_NEISO.csv``:

  * ``tmax``    — hot design-cooling day  (zone p95 tmax)
  * ``tmin``    — cold design-heating day (zone p1 tmin — matching the existing
                  NEISO temperature limbs; NEISO has no published cold trigger)
  * ``netload`` — high system-stress day  (NEISO-wide p70 daily-peak net-load)

On every flagged day the floor binds ONLY the class's justified window at
``floor_pct = commit_frac_window x min_stable_pct``:

  * ``min_stable_pct`` = the class's physical minimum-stable level of a committed
    unit (``constants.MIN_STABLE_PCT_PHYSICAL``: ST_GAS 0.12, CT_PEAKER 0.38;
    NREL WWSIS-2 Table 7), NOT an offer-curve must-run share and NOT a measured-CF
    ceiling.
  * ``commit_frac_window`` = the nameplate-weighted share of the zone's pure-play
    fleet that is ONLINE during the class's window on flagged days (a commitment
    count from CAMPD CEMS gross load, not an energy average). The floor holds a
    committed unit at its physical Pmin in-window; it never pins measured
    generation.

Honesty gate (identical to ``derive_reliability_coeffs.py`` /
``derive_pjm_st_gas_overnight_drag.py``, never residual-tuned — CLAUDE.md rules
1/9/11): a limb ships ``enabled=True`` ONLY when ``rho >= RHO_MIN`` (Spearman of
the driver severity vs the in-window daily CF on flagged days, so commitment RISES
with the driver) AND ``n >= N_MIN`` (flagged-day sample) AND
``commit_frac_window > baseline_commit`` (flagged-day in-window online share
exceeds the mild-day in-window online share — a like-for-like commitment test).
Otherwise the limb ships ``enabled=False`` and stays VISIBLE so nothing is
invented to plug a residual (rule 12). Coefficients are NEISO's own (rule 24) —
never reused from ERCOT/PJM/CAISO/MISO. Both the trigger (temperature / net-load,
forward-derivable from a load+weather forecast and a VRE build) and the magnitude
(a physical Pmin commitment) regenerate for a forward year and respond to changed
conditions, so the mechanism is admissible in backcast AND forecast (rules 12/13).

Rule-14 reconciliation with the WINTER FUEL-SECURITY must-run (Component B,
``winter_fuel_inventory.apply_winter_fuelsec_mustrun``, neiso53 keeper headline):
Component B ALREADY floors ST_GAS all-day at ``commit_frac x 0.40 x min-stable``
on Nov-Mar cold days (zone TMIN < -7 C, WRP/IEP/OFSA posture, 48h-bridged). That
program-grounded, all-day posture OWNS the ST_GAS cold-day phenomenon — a
superset of any overnight tmin drag. So the ST_GAS ``tmin`` drag limb is
FORCE-DISABLED here (:data:`_OWNED_BY`) and stays visible with its owner named;
never a second cold-day floor stacked on Component B (rules 14/19). The genuinely
additive ST_GAS pieces are the HOT (tmax) and HIGH-NETLOAD (netload) OVERNIGHT
pre-positioning limbs — non-winter / shoulder-season tight-system days Component B
does not touch. CT_PEAKER carries no competing NEISO floor (the slope-based
``neiso_ct_floor`` is off in the keeper), so all three CT limbs derive freely.

Steam bridging (``min_event_hours = 48``, the ST_GAS loader default) is applied by
the engine so a committed boiler spans a multi-day event; CT_PEAKER is single-day.
This is ALL in the ``reliability_floor`` engine — it does NOT enable the separate
``gas_st_netload_drag`` / ``ct_netload_drag`` mechanisms (that would stack a
second floor on one phenomenon — CLAUDE.md rule 14/19).

Usage:
    python scripts/data/derive_neiso_steamgas_ct_drag.py            # derive + patch CSV
    python scripts/data/derive_neiso_steamgas_ct_drag.py --dry-run  # print only
    python scripts/data/derive_neiso_steamgas_ct_drag.py --diurnal  # + hourly profiles
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import MIN_STABLE_PCT_PHYSICAL  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DIR, REFERENCE_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from market_sim.data.zone_assignment import build_zone_lookup  # noqa: E402
from market_sim.model.transmission import _bridge_flagged_runs  # noqa: E402

HOURS = 8760
_DAYS = HOURS // 24  # 365 (non-leap model clock)

# --- Per-class window + physical-parameter registry (rule 12: window + driver). ---
# ``window`` is INCLUSIVE (start_hour, end_hour) — the engine gate is
# ``(hod >= start) & (hod <= end)``. ST_GAS = the pre-dawn overnight trough
# (h0-6) where output is HELD COMMITMENT, not merit dispatch. CT_PEAKER = the
# afternoon-evening net-load ramp (h15-21); overnight CT CF ~0 so a floor there
# is a rule-12 bug (the failure that scrubbed the old all-24h CT limbs). Windows
# are derived from where each class's CF genuinely rises with the driver (see
# --diurnal) and pinned to the physical diurnal footprint, never chosen to move a
# residual.
_CLASS_SPEC: dict[str, dict] = {
    "ST_GAS": {
        "window": (0, 6),
        "min_stable": MIN_STABLE_PCT_PHYSICAL["ST_GAS"],  # 0.12
        "net_of_gross": 1.0 - campd.DEFAULT_PARASITIC_LOAD_PCT["ST_GAS"],  # ~0.95
        "steam": True,  # engine bridges to min_event_hours=48
    },
    "CT_PEAKER": {
        "window": (15, 21),
        "min_stable": MIN_STABLE_PCT_PHYSICAL["CT_PEAKER"],  # 0.38
        "net_of_gross": 1.0 - campd.DEFAULT_PARASITIC_LOAD_PCT["CT_PEAKER"],  # ~0.99
        "steam": False,
    },
}

# --- Rule-14 ownership: (class, driver) limbs OWNED by another armed mechanism. ---
# The NEISO winter fuel-security must-run (Component B,
# winter_fuel_inventory.apply_winter_fuelsec_mustrun; neiso53 keeper) floors
# ST_GAS all-day at commit x 0.40 x min-stable on Nov-Mar cold days
# (TMIN < -7 C) — the program-grounded, all-day posture that OWNS the ST_GAS
# cold-day phenomenon (a superset of any overnight tmin drag). Its limb is
# force-disabled and stays visible with the owner named (rules 12/14/19).
_OWNED_BY: dict[tuple[str, str], str] = {
    ("ST_GAS", "tmin"): (
        "owned by neiso_winter_fuel_mustrun (Component B - winter fuel-security "
        "WRP/IEP/OFSA all-day cold posture; TMIN<-7C) - not stacked (rule 14/19)"
    ),
}

# --- Classes with model capacity but no clean pure-play CAMPD signal. ---
# ST_GAS is a single 81 MW unit embedded in a 491 MW mixed facility (CAMPD
# code 546), so the plant-summed gross is contaminated by ~410 MW of non-steam
# capacity: no clean commitment signal can be measured. The class is owned
# entirely by the winter fuel-security must-run (Component B), which floors the
# model's 81 MW ST_GAS by plant_group on Nov-Mar cold days — the program-grounded,
# forward-native mechanism (rule 14/19). Visible disabled placeholder rows are
# emitted so the class never silently vanishes from the CSV (rule 12).
_NO_SIGNAL_REASON: dict[str, str] = {
    "ST_GAS": (
        "no pure-play CAMPD signal (81 MW steam unit shares facility 546 with "
        "~410 MW non-steam); ST_GAS commitment owned by neiso_winter_fuel_mustrun "
        "Component B (rule 14/19)"
    ),
}

# --- Enable/disable gate (diagnostics only, never residual-tuned). ---
RHO_MIN = 0.3
N_MIN = 30

# --- Physical driver onsets (physical anchors, not backcast-chosen). ---
HOT_PERCENTILE = 95.0  # hot onset = zone p95 tmax (design cooling day)
COLD_PERCENTILE = 1.0  # cold onset = zone p1 tmin (design heating day; NEISO)
NETLOAD_ONSET_PERCENTILE = 70.0  # high-stress onset = system p70 daily-peak NL

# --- Pure-play share so the plant-summed CAMPD series measures the class only. ---
_PURE_PLAY_SHARE = 0.90

# ISO-NE EIA-930 balancing-authority hourly extract; NEISO local standard = EST
# (UTC-5, no DST), the SAME convention derive_reliability_coeffs uses for the
# existing NEISO netload limb. The engine recomputes the GW threshold from its OWN
# model net-load via ``threshold_percentile``, so this offset only aligns the
# flagged-DAY set to the CAMPD daily CF for the honesty diagnostics.
_NEISO_BA_FILE = "ISNE hourly.parquet"
_NEISO_UTC_OFFSET = 5

# Cumulative days at the start of each month (non-leap), date -> day-of-year.
_MONTH_START_DAY = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]


def _doy_nonleap(dates: pd.Series) -> np.ndarray:
    """Map dates to non-leap day-of-year (0-364); Feb 29 -> -1."""
    m = dates.dt.month.to_numpy(dtype=int)
    d = dates.dt.day.to_numpy(dtype=int)
    base = np.array(_MONTH_START_DAY)[m - 1]
    idx = base + (d - 1)
    return np.where((m == 2) & (d == 29), -1, idx)


def zonal_pure_play(year: int, klass: str) -> dict[str, dict[int, float]]:
    """Return ``{zone: {plant_code: class nameplate MW}}`` for pure-play plants.

    A plant enters its zone's group only when >= ``_PURE_PLAY_SHARE`` of its model
    capacity is ``klass``, so the plant-summed CAMPD series measures that class
    only. Zone comes from the eGRID/EIA-860 geography lookup (same names the
    per-zone weather series and the LP zone_names carry); class + nameplate from
    the model fleet.
    """
    cfg = get_iso_config("NEISO")
    zl = build_zone_lookup("NEISO")
    gens = load_fleet_from_csv("NEISO", cfg, year=year)
    plant_cap: dict[int, float] = defaultdict(float)
    cls_cap: dict[int, float] = defaultdict(float)
    for g in gens:
        pc = int(getattr(g, "plant_code", 0) or 0)
        if pc <= 0:
            continue
        plant_cap[pc] += float(g.pmax_mw)
        if g.plant_group == klass:
            cls_cap[pc] += float(g.pmax_mw)
    by_zone: dict[str, dict[int, float]] = defaultdict(dict)
    for pc, sc in cls_cap.items():
        if sc <= 0.0 or pc not in zl:
            continue
        if sc / plant_cap[pc] >= _PURE_PLAY_SHARE:
            by_zone[zl[pc]][pc] = sc
    return by_zone


_HOURLY_CACHE: dict[int, pd.DataFrame] = {}


def _campd_hourly(year: int) -> pd.DataFrame:
    """Cache the full multi-state NEISO CAMPD hourly frame per year (heavy read)."""
    if year not in _HOURLY_CACHE:
        _HOURLY_CACHE[year] = campd.load_campd_hourly(
            campd.states_for_iso("NEISO"), [year]
        )
    return _HOURLY_CACHE[year]


def measured_plant_hourly(
    year: int, plant_codes: set[int], net_of_gross: float
) -> dict[int, np.ndarray]:
    """Per-plant 8760-hour net MW (CAMPD CEMS, class station-service netted)."""
    df = _campd_hourly(year)
    net = campd.plant_hourly_net(
        df, {pid: net_of_gross for pid in plant_codes}, year, hours=HOURS
    )
    return {pid: series for pid, series in net.items() if pid in plant_codes}


def _window_daily(
    plant_hourly: dict[int, np.ndarray],
    plant_npl: dict[int, float],
    nameplate: float,
    window: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Daily in-window ``(cf, online_frac, zone_mw)`` arrays.

    * ``cf[d]``          = zone in-window MWh on day d / (nameplate x window_hours)
    * ``online_frac[d]`` = nameplate-weighted share of the fleet online (any
      positive gross load) DURING the window on day d.
    * ``zone_mw``        = the full 8760 zone MW series (for the forced-energy
      report and diurnal diagnostics).
    """
    sh, eh = window
    win_cols = np.arange(sh, eh + 1)  # inclusive
    win_h = win_cols.size
    zone_mw = np.zeros(HOURS)
    online_npl = np.zeros(_DAYS)
    for pid, series in plant_hourly.items():
        zone_mw += series
        day_mat = series.reshape(_DAYS, 24)[:, win_cols]
        online = day_mat.sum(axis=1) > 0.0  # online in-window that day
        online_npl += online.astype(float) * plant_npl.get(pid, 0.0)
    win_mwh = zone_mw.reshape(_DAYS, 24)[:, win_cols].sum(axis=1)
    cf = np.clip(win_mwh / (nameplate * win_h), 0.0, 1.0)
    online_frac = np.clip(online_npl / nameplate, 0.0, 1.0)
    return cf, online_frac, zone_mw


def _zone_weather() -> pd.DataFrame:
    """Per-zone daily ``date,zone,tmax_c,tmin_c`` series for NEISO."""
    path = RAW_DIR / "neiso-weather" / "neiso_zone_temp_daily.csv"
    return pd.read_csv(path, parse_dates=["date"])


def _year_temps(zw: pd.DataFrame, year: int) -> tuple[np.ndarray, np.ndarray] | None:
    """Return ``(tmax[_DAYS], tmin[_DAYS])`` for one year, day-of-year aligned."""
    sub = zw[zw["date"].dt.year == year]
    if sub.empty:
        return None
    doy = _doy_nonleap(sub["date"])
    ok = (doy >= 0) & (doy < _DAYS)
    tmax = np.full(_DAYS, np.nan)
    tmin = np.full(_DAYS, np.nan)
    tmax[doy[ok]] = pd.to_numeric(sub["tmax_c"], errors="coerce").to_numpy()[ok]
    tmin[doy[ok]] = pd.to_numeric(sub["tmin_c"], errors="coerce").to_numpy()[ok]
    return tmax, tmin


def neiso_net_load_mw(year: int) -> np.ndarray:
    """NEISO system hourly net-load = EIA-930 Demand - solar - wind (MW, 8760).

    UTC timestamps shifted -5 h to local standard (EST, no DST) and laid on the
    model's non-leap 8760-hour grid. Gaps (Feb 29 / missing stamps) interpolated.
    """
    df = pd.read_parquet(RAW_DIR / "eia-930-hourly" / _NEISO_BA_FILE)
    utc = pd.to_datetime(df["UTC time"], utc=True)
    lst = utc.dt.tz_convert(None) - pd.Timedelta(hours=_NEISO_UTC_OFFSET)
    mask = lst.dt.year == year
    df = df[mask].reset_index(drop=True)
    lst = lst[mask].reset_index(drop=True)
    doy = _doy_nonleap(lst.dt.normalize())
    hoy = doy * 24 + lst.dt.hour.to_numpy(dtype=int)
    ok = (doy >= 0) & (hoy >= 0) & (hoy < HOURS)
    dem = pd.to_numeric(df["Demand"], errors="coerce").to_numpy()[ok]
    sun = pd.to_numeric(df.get("NG: SUN"), errors="coerce").to_numpy()[ok]
    wnd = pd.to_numeric(df.get("NG: WND"), errors="coerce").to_numpy()[ok]
    out = np.full(HOURS, np.nan)
    out[hoy[ok]] = dem - np.nan_to_num(sun) - np.nan_to_num(wnd)
    return pd.Series(out).interpolate(limit_direction="both").to_numpy()


def _daily_peak_nl_gw(year: int) -> np.ndarray:
    """NEISO system daily-peak net-load (GW), day-of-year aligned (length ``_DAYS``)."""
    nl = neiso_net_load_mw(year)
    return nl.reshape(_DAYS, 24).max(axis=1) / 1000.0


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rho of ``x`` vs ``y`` (NaN when undefined)."""
    if x.size < 2 or np.unique(x).size < 2 or np.unique(y).size < 2:
        return float("nan")
    return float(pd.Series(x).corr(pd.Series(y), method="spearman"))


def _fit_limb(
    drive_flag: np.ndarray,
    cf_flag: np.ndarray,
    online_flag: np.ndarray,
    cf_mild: np.ndarray,
    online_mild: np.ndarray,
    min_stable: float,
) -> dict:
    """Assemble one limb's coefficients + honesty diagnostics from pooled days."""
    n = int(cf_flag.size)
    commit_frac = float(online_flag.mean()) if n else 0.0
    baseline = float(cf_mild.mean()) if cf_mild.size else 0.0
    baseline_commit = float(online_mild.mean()) if online_mild.size else 0.0
    rho = _spearman(drive_flag, cf_flag) if n >= 2 else float("nan")
    floor_pct = commit_frac * min_stable
    enabled = bool(
        (not np.isnan(rho))
        and rho >= RHO_MIN
        and n >= N_MIN
        and commit_frac > baseline_commit
    )
    return {
        "commit_frac": commit_frac,
        "baseline": baseline,
        "baseline_commit": baseline_commit,
        "rho": rho,
        "n": n,
        "floor_pct": floor_pct,
        "enabled": enabled,
    }


def derive_zone_limbs(
    zone: str,
    klass: str,
    years: tuple[int, ...],
    plant_year: dict[int, dict[int, float]],
) -> tuple[list[dict], dict]:
    """Derive the tmax/tmin/netload limbs for one (zone, class); return (rows, ctx).

    ``ctx`` carries the pooled in-window CF and the full-year zone MW per year for
    the diurnal diagnostics and forced-energy report.
    """
    spec = _CLASS_SPEC[klass]
    window = spec["window"]
    min_stable = spec["min_stable"]
    cf_all, online_all, tmax_all, tmin_all, nl_all = [], [], [], [], []
    zw = _zone_weather()
    zone_mw_by_year: dict[int, np.ndarray] = {}
    for year in years:
        plant_npl = plant_year.get(year, {})
        nameplate = float(sum(plant_npl.values()))
        if nameplate <= 0.0:
            continue
        hourly = measured_plant_hourly(year, set(plant_npl), spec["net_of_gross"])
        cf, online, zone_mw = _window_daily(hourly, plant_npl, nameplate, window)
        zone_mw_by_year[year] = zone_mw
        temps = _year_temps(zw[zw["zone"] == zone], year)
        if temps is None:
            continue
        tmax, tmin = temps
        cf_all.append(cf)
        online_all.append(online)
        tmax_all.append(tmax)
        tmin_all.append(tmin)
        nl_all.append(_daily_peak_nl_gw(year))
    if not cf_all:
        return [], {}
    cf = np.concatenate(cf_all)
    online = np.concatenate(online_all)
    tmax = np.concatenate(tmax_all)
    tmin = np.concatenate(tmin_all)
    nl = np.concatenate(nl_all)

    rows: list[dict] = []

    # --- tmax (hot design-cooling day) ---
    thr_hot = float(np.nanpercentile(tmax, HOT_PERCENTILE))
    ok = ~np.isnan(tmax)
    hot = ok & (tmax >= thr_hot)
    mild = ok & (tmax < thr_hot)
    fit = _fit_limb(
        (tmax[hot] - thr_hot), cf[hot], online[hot], cf[mild], online[mild], min_stable
    )
    rows.append(
        _row(
            zone,
            klass,
            "tmax",
            thr_hot,
            fit,
            min_stable,
            window,
            f"hot: zone p{int(HOT_PERCENTILE)} tmax (design cooling day); "
            f"window h{window[0]}-{window[1]}",
        )
    )

    # --- tmin (cold design-heating day) ---
    thr_cold = float(np.nanpercentile(tmin, COLD_PERCENTILE))
    ok = ~np.isnan(tmin)
    cold = ok & (tmin < thr_cold)
    mildc = ok & (tmin >= thr_cold)
    fit = _fit_limb(
        (thr_cold - tmin[cold]),
        cf[cold],
        online[cold],
        cf[mildc],
        online[mildc],
        min_stable,
    )
    rows.append(
        _row(
            zone,
            klass,
            "tmin",
            thr_cold,
            fit,
            min_stable,
            window,
            f"cold: zone p{int(COLD_PERCENTILE)} tmin (design heating day); "
            f"window h{window[0]}-{window[1]}",
        )
    )

    # --- netload (high system-stress day) ---
    thr_nl = float(np.nanpercentile(nl, NETLOAD_ONSET_PERCENTILE))
    hi = nl > thr_nl
    lo = nl <= thr_nl
    fit = _fit_limb(
        (nl[hi] - thr_nl), cf[hi], online[hi], cf[lo], online[lo], min_stable
    )
    rows.append(
        _row(
            zone,
            klass,
            "netload",
            thr_nl,
            fit,
            min_stable,
            window,
            f"netload: NEISO system p{int(NETLOAD_ONSET_PERCENTILE)} daily-peak "
            f"net-load (demand-VRE) GW; window h{window[0]}-{window[1]}",
            threshold_percentile=int(NETLOAD_ONSET_PERCENTILE),
        )
    )
    ctx = {"cf_pooled": cf, "nl_pooled": nl, "zone_mw_by_year": zone_mw_by_year}
    return rows, ctx


def _model_class_zones(klass: str, years: tuple[int, ...]) -> dict[str, float]:
    """Return ``{zone: nameplate MW}`` where the MODEL fleet carries ``klass``.

    Unlike :func:`zonal_pure_play` this counts a class's capacity even at a mixed
    facility (used to place a VISIBLE disabled placeholder row for a class that
    has model capacity but no clean pure-play CAMPD signal — rule 12).
    """
    zl = build_zone_lookup("NEISO")
    cfg = get_iso_config("NEISO")
    by_zone: dict[str, float] = defaultdict(float)
    for year in years:
        for g in load_fleet_from_csv("NEISO", cfg, year=year):
            if g.plant_group != klass:
                continue
            pc = int(getattr(g, "plant_code", 0) or 0)
            if pc in zl:
                by_zone[zl[pc]] += float(g.pmax_mw)
    # Average across years so a plant present every year is not triple-counted.
    return {z: mw / len(years) for z, mw in by_zone.items() if mw > 0.0}


def _disabled_placeholder_rows(
    zone: str, klass: str, years: tuple[int, ...], reason: str
) -> list[dict]:
    """Emit VISIBLE disabled tmax/tmin/netload rows for a class with no clean
    pure-play CAMPD signal (rule 12 — invent nothing, but stay visible).

    Thresholds are computed from the zone weather / system net-load exactly as the
    live path would; the fit is empty (commit_frac=0, floor=0) and every row ships
    ``enabled=False`` with ``reason`` appended to the basis.
    """
    spec = _CLASS_SPEC[klass]
    window = spec["window"]
    min_stable = spec["min_stable"]
    zw = _zone_weather()
    tmax_all, tmin_all, nl_all = [], [], []
    for year in years:
        temps = _year_temps(zw[zw["zone"] == zone], year)
        if temps is None:
            continue
        tmax_all.append(temps[0])
        tmin_all.append(temps[1])
        nl_all.append(_daily_peak_nl_gw(year))
    tmax = np.concatenate(tmax_all) if tmax_all else np.array([np.nan])
    tmin = np.concatenate(tmin_all) if tmin_all else np.array([np.nan])
    nl = np.concatenate(nl_all) if nl_all else np.array([np.nan])
    empty = {
        "commit_frac": 0.0,
        "baseline": 0.0,
        "baseline_commit": 0.0,
        "rho": float("nan"),
        "n": 0,
        "floor_pct": 0.0,
        "enabled": False,
    }
    thr_hot = float(np.nanpercentile(tmax, HOT_PERCENTILE))
    thr_cold = float(np.nanpercentile(tmin, COLD_PERCENTILE))
    thr_nl = float(np.nanpercentile(nl, NETLOAD_ONSET_PERCENTILE))
    return [
        _row(
            zone,
            klass,
            "tmax",
            thr_hot,
            empty,
            min_stable,
            window,
            f"hot: zone p{int(HOT_PERCENTILE)} tmax; window h{window[0]}-{window[1]} "
            f"[DISABLED: {reason}]",
        ),
        _row(
            zone,
            klass,
            "tmin",
            thr_cold,
            empty,
            min_stable,
            window,
            f"cold: zone p{int(COLD_PERCENTILE)} tmin; window h{window[0]}-{window[1]} "
            f"[DISABLED: {reason}]",
        ),
        _row(
            zone,
            klass,
            "netload",
            thr_nl,
            empty,
            min_stable,
            window,
            f"netload: system p{int(NETLOAD_ONSET_PERCENTILE)} daily-peak net-load GW; "
            f"window h{window[0]}-{window[1]} [DISABLED: {reason}]",
            threshold_percentile=int(NETLOAD_ONSET_PERCENTILE),
        ),
    ]


def _row(
    zone: str,
    klass: str,
    driver: str,
    threshold: float,
    fit: dict,
    min_stable: float,
    window: tuple[int, int],
    basis: str,
    threshold_percentile: int | None = None,
) -> dict:
    """Build one CSV row dict for a derived limb.

    Rule-14 ownership override (:data:`_OWNED_BY`): a (class, driver) limb owned
    by another armed mechanism is force-disabled and its owner named in the basis,
    so the limb stays visible but never stacks a second floor on one phenomenon.
    """
    enabled = fit["enabled"]
    owner = _OWNED_BY.get((klass, driver))
    if owner is not None:
        enabled = False
        # Avoid a redundant second [DISABLED:...] tag when this is already a
        # no-signal placeholder row (its basis names the owning mechanism too).
        if "[DISABLED:" not in basis:
            basis = f"{basis} [DISABLED: {owner}]"
    return {
        "iso": "NEISO",
        "zone": zone,
        "plant_class": klass,
        "driver": driver,
        "threshold": round(threshold, 2),
        "floor_pct": round(fit["floor_pct"], 4),
        "enabled": enabled,
        "commit_frac": round(fit["commit_frac"], 4),
        "min_stable_pct": round(min_stable, 4),
        "rho": round(fit["rho"], 4) if not np.isnan(fit["rho"]) else "",
        "n": fit["n"],
        "baseline": round(fit["baseline"], 4),
        "baseline_commit": round(fit["baseline_commit"], 4),
        "threshold_basis": basis,
        "threshold_percentile": threshold_percentile if threshold_percentile else "",
        "start_hour": window[0],
        "end_hour": window[1],
    }


# The NEISO CSV carries threshold_percentile already; start_hour/end_hour are the
# new windowing columns appended here (the CSV predates sub-daily windows).
_NEW_COLS = ["start_hour", "end_hour"]
_PATCH_CLASSES = frozenset(_CLASS_SPEC)


def patch_csv(new_rows: list[dict]) -> None:
    """Replace ST_GAS + CT_PEAKER rows in reliability_floor_coeffs_NEISO.csv.

    Every other class's row is written back VERBATIM (its existing field values
    unchanged) with the new ``start_hour``/``end_hour`` columns appended empty, so
    the substance of every non-drag limb is byte-identical (CLAUDE.md rule 14/16:
    replace the two drag classes' limbs, never stack). An all-day (empty
    start/end) limb is byte-identical to its pre-window behaviour.
    """
    path = REFERENCE_DIR / "reliability_floor_coeffs_NEISO.csv"
    lines = path.read_text().splitlines()
    header = lines[0].split(",")
    cls_idx = header.index("plant_class")
    # Idempotent: only append window columns the CSV does not already carry, so
    # re-running the derivation never duplicates start_hour/end_hour.
    add_cols = [c for c in _NEW_COLS if c not in header]
    cols = header + add_cols
    out = [",".join(cols)]
    for ln in lines[1:]:
        if not ln.strip():
            continue
        fields = ln.split(",")
        if fields[cls_idx].strip() in _PATCH_CLASSES:
            continue  # drop old ST_GAS / CT_PEAKER limbs
        # Pad short rows (some legacy rows omit the trailing threshold_percentile
        # field) to the full original width, THEN add the new window columns, so
        # every row aligns exactly to ``cols`` (no column-shift misparse).
        fields += [""] * (len(header) - len(fields))
        out.append(",".join(fields + [""] * len(add_cols)))
    for r in new_rows:
        vals = [str(r[c]) for c in cols]
        bad = [c for c, v in zip(cols, vals) if "," in v]
        if bad:
            raise ValueError(f"comma in unquoted field(s) {bad} of row {r['zone']}")
        out.append(",".join(vals))
    path.write_text("\n".join(out) + "\n")
    print(f"\npatched {path} ({len(new_rows)} ST_GAS+CT_PEAKER rows)")


def _diurnal_report(zone: str, klass: str, ctx: dict) -> None:
    """Print the hourly CF profile on high- vs low-netload days (window evidence).

    Confirms WHERE the class's CF genuinely rises with the driver: the window is
    put only in those hours (rule 12 — no floor outside its diurnal footprint).
    """
    zone_mw_by_year = ctx.get("zone_mw_by_year", {})
    if not zone_mw_by_year:
        return
    mats, nls = [], []
    for year, zone_mw in zone_mw_by_year.items():
        mats.append(zone_mw.reshape(_DAYS, 24))
        nls.append(_daily_peak_nl_gw(year))
    mat = np.concatenate(mats)  # (n_days, 24)
    nl = np.concatenate(nls)
    thr = np.nanpercentile(nl, NETLOAD_ONSET_PERCENTILE)
    hi = nl > thr
    lo = nl <= thr
    denom = max(mat.max(), 1.0)
    hi_prof = mat[hi].mean(axis=0) / denom
    lo_prof = mat[lo].mean(axis=0) / denom
    win = _CLASS_SPEC[klass]["window"]
    print(f"\n  diurnal {zone}/{klass} (hi-NL vs lo-NL, normalised; window {win}):")
    print("    hour " + " ".join(f"{h:4d}" for h in range(24)))
    print("    hiNL " + " ".join(f"{v:4.2f}" for v in hi_prof))
    print("    loNL " + " ".join(f"{v:4.2f}" for v in lo_prof))


def _forced_energy_report(
    class_rows: dict[str, dict[str, list[dict]]],
    years: tuple[int, ...],
    plant_by_year: dict[str, dict[str, dict[int, dict[int, float]]]],
) -> None:
    """Estimate forced in-window TWh vs measured class total per year (rule 20).

    Combines the ENABLED limbs per (zone, class) via the engine's ``maximum``
    composition, applies steam event-bridging + the window exactly as the engine
    would, and sums floor MWh (frac x nameplate) against the measured pure-play
    energy for that class.
    """
    print("\n=== Forced in-window energy vs measured (rule 20 budget) ===")
    for klass, zone_rows in class_rows.items():
        spec = _CLASS_SPEC[klass]
        sh, eh = spec["window"]
        hod = np.arange(HOURS) % 24
        window = (hod >= sh) & (hod <= eh)
        min_event = 48 if spec["steam"] else 24
        print(f"\n  [{klass}] window h{sh}-{eh}, min_event_hours={min_event}")
        for year in years:
            forced_mwh = 0.0
            measured_mwh = 0.0
            peak_nl = _daily_peak_nl_gw(year)
            zw = _zone_weather()
            for zone, rows in zone_rows.items():
                plant_npl = plant_by_year[klass][zone].get(year, {})
                nameplate = float(sum(plant_npl.values()))
                if nameplate <= 0.0:
                    continue
                hourly = measured_plant_hourly(
                    year, set(plant_npl), spec["net_of_gross"]
                )
                zone_mw = np.zeros(HOURS)
                for s in hourly.values():
                    zone_mw += s
                measured_mwh += float(zone_mw.sum())
                temps = _year_temps(zw[zw["zone"] == zone], year)
                if temps is None:
                    continue
                tmax, tmin = temps
                combined = np.zeros(HOURS)  # per-hour max floor across enabled limbs
                for r in rows:
                    if not r["enabled"]:
                        continue
                    if r["driver"] == "tmax":
                        day_flag = tmax > float(r["threshold"])
                    elif r["driver"] == "tmin":
                        day_flag = tmin < float(r["threshold"])
                    else:  # netload — recompute threshold at the derivation pctile
                        thr = float(np.nanpercentile(peak_nl, NETLOAD_ONSET_PERCENTILE))
                        day_flag = peak_nl > thr
                    flagged = np.repeat(np.nan_to_num(day_flag), 24)[:HOURS] > 0
                    if min_event > 24:
                        flagged = _bridge_flagged_runs(flagged, min_event)
                    flagged = flagged & window
                    frac = np.where(flagged, float(r["floor_pct"]), 0.0)
                    combined = np.maximum(combined, frac)
                forced_mwh += float((combined * nameplate).sum())
            pct = forced_mwh / max(measured_mwh, 1.0) * 100.0
            print(
                f"    {year}: forced {forced_mwh / 1e6:.4f} TWh vs measured "
                f"{klass} {measured_mwh / 1e6:.3f} TWh  ({pct:.1f}% of class energy)"
            )


def main() -> None:
    """CLI: derive NEISO ST_GAS + CT_PEAKER drag limbs, print diagnostics, patch CSV."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--dry-run", action="store_true", help="print only; don't write")
    ap.add_argument("--diurnal", action="store_true", help="print hourly profiles")
    args = ap.parse_args()
    years = tuple(args.years)

    # Pure-play plants per zone, per class, per year (fleet changes year to year).
    plant_by_year: dict[str, dict[str, dict[int, dict[int, float]]]] = {
        k: defaultdict(dict) for k in _CLASS_SPEC
    }
    for klass in _CLASS_SPEC:
        for year in years:
            for zone, plants in zonal_pure_play(year, klass).items():
                plant_by_year[klass][zone][year] = plants

    class_rows: dict[str, dict[str, list[dict]]] = {}
    all_rows: list[dict] = []
    for klass in _CLASS_SPEC:
        print(
            f"\n=== NEISO {klass} drag limbs "
            f"(window h{_CLASS_SPEC[klass]['window'][0]}-"
            f"{_CLASS_SPEC[klass]['window'][1]}, "
            f"min_stable={_CLASS_SPEC[klass]['min_stable']}) ==="
        )
        print(
            f"{'zone':16s} {'driver':8s} {'thr':>7s} {'rho':>6s} {'n':>4s} "
            f"{'commit':>7s} {'basel_c':>8s} {'floor':>6s}  enabled"
        )
        zone_rows: dict[str, list[dict]] = {}
        zones = sorted(plant_by_year[klass])
        for zone in zones:
            rows, ctx = derive_zone_limbs(
                zone, klass, years, plant_by_year[klass][zone]
            )
            if not rows:
                continue
            zone_rows[zone] = rows
            all_rows.extend(rows)
            for r in rows:
                print(
                    f"{zone:16s} {r['driver']:8s} {r['threshold']:7.2f} "
                    f"{(r['rho'] if r['rho'] != '' else float('nan')):6.2f} "
                    f"{r['n']:4d} {r['commit_frac']:7.3f} {r['baseline_commit']:8.3f} "
                    f"{r['floor_pct']:6.3f}  {r['enabled']}"
                )
            if args.diurnal:
                _diurnal_report(zone, klass, ctx)

        # Rule-12 visibility: a class with MODEL capacity but no clean pure-play
        # CAMPD signal (its lone unit shares a facility with other classes) gets
        # VISIBLE disabled placeholder rows naming the owning mechanism, never a
        # silently-vanished class. NEISO ST_GAS is a single 81 MW unit embedded in
        # a 491 MW mixed facility (code 546), so its CAMPD gross is contaminated by
        # ~410 MW of non-steam capacity — no clean signal exists; the ST_GAS
        # commitment is owned entirely by the winter fuel-security must-run
        # (Component B), which floors by model plant_group, not by CAMPD (rule 14).
        reason = _NO_SIGNAL_REASON.get(klass)
        if reason is not None:
            for zone in sorted(_model_class_zones(klass, years)):
                if zone in zone_rows:
                    continue
                ph = _disabled_placeholder_rows(zone, klass, years, reason)
                zone_rows[zone] = ph
                all_rows.extend(ph)
                for r in ph:
                    print(
                        f"{zone:16s} {r['driver']:8s} {r['threshold']:7.2f} "
                        f"{'  nan':>6s} {0:4d} {0.0:7.3f} {0.0:8.3f} "
                        f"{0.0:6.3f}  {r['enabled']} (placeholder)"
                    )
        class_rows[klass] = zone_rows

    n_on = sum(1 for r in all_rows if r["enabled"])
    print(f"\n{len(all_rows)} drag limbs total, {n_on} enabled")

    _forced_energy_report(class_rows, years, plant_by_year)

    if args.dry_run:
        print("\n[dry-run] CSV not written")
        return
    patch_csv(all_rows)


if __name__ == "__main__":
    main()
