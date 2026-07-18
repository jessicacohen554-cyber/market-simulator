#!/usr/bin/env python
"""Derive PJM ST_GAS extreme-day OVERNIGHT pre-positioning reliability floors.

PJM's legacy gas-steam boilers (ST_GAS — the Marcellus-belt coal-to-gas
conversions Brunner Island / Montour / Shawville / New Castle plus a few
downstate steamers) do not cycle off between consecutive extreme days: on a
hot cooling day, a cold snap, or a high-net-load stress day the ISO holds them
committed at part load through the low-price OVERNIGHT trough so the boiler
stays warm to ramp for the NEXT afternoon peak, rather than shutting and paying
a multi-hour cold start. The energy-only LP, free to de-commit each hour, cycles
them off overnight where hour-by-hour they are non-economic — the wrong physics
for a committed steam unit on a multi-day event.

This replaces the earlier ALL-DAY PJM ST_GAS reliability-floor limbs (which bound
the class 00:00-23:59, over-forcing the daytime hours the merit order already
dispatches and mis-shaping the diurnal profile) with an OVERNIGHT-WINDOWED
pre-positioning floor. For each PJM model zone and the ST_GAS class it emits
THREE limbs into ``reliability_floor_coeffs_PJM.csv``:

  * ``tmax``    — hot design-cooling day  (zone p95 tmax)
  * ``tmin``    — cold day                (PJM Manual-13 Cold-Weather-Alert -12 C)
  * ``netload`` — high system-stress day  (PJM-wide p70 daily-peak net-load)

On every flagged day the floor binds ONLY the overnight window
(:data:`OVERNIGHT_HOURS`, hours 0-6 local standard, the pre-dawn trough before
the afternoon/evening peak) at ``floor_pct = commit_frac_overnight ×
min_stable_pct``:

  * ``min_stable_pct`` = the ST_GAS physical minimum-stable level of a committed
    unit (``constants.MIN_STABLE_PCT_PHYSICAL['ST_GAS']`` = 0.12; NREL WWSIS-2
    Table 7), NOT an offer-curve must-run share and NOT a measured-CF ceiling.
  * ``commit_frac_overnight`` = the nameplate-weighted share of the zone's
    pure-play ST_GAS fleet that is ONLINE during the overnight window on
    flagged days (a commitment count from CAMPD CEMS gross load, not an energy
    average). The floor holds a committed boiler at its physical Pmin overnight;
    it never pins measured generation.

Honesty gate (identical to ``scripts/data/derive_reliability_coeffs.py``, never
residual-tuned — CLAUDE.md rules 1/9/11): a limb ships ``enabled=True`` ONLY when
``rho >= RHO_MIN`` (Spearman of the driver severity vs the overnight daily CF on
flagged days, so commitment RISES with the driver) AND ``n >= N_MIN`` (flagged-day
sample) AND ``commit_frac_overnight > baseline_commit`` (flagged-day overnight
online share exceeds the mild-day overnight online share — a like-for-like
commitment test). Otherwise the limb ships ``enabled=False`` and stays visible so
nothing is invented to plug a residual. Both the trigger (temperature / net-load,
forward-derivable from a load+weather forecast and a VRE build) and the magnitude
(a physical Pmin commitment) regenerate for a forward year and respond to changed
conditions, so the mechanism is admissible in backcast AND forecast (rules 12/13).

Data access mirrors ``scripts/data/derive_pjm_st_gas_netload_drag.py``: pure-play
ST_GAS plants (>= 90% ST_GAS by model capacity so the plant-summed CAMPD series
measures gas-steam units only), CAMPD gross netted by the ST_GAS 5% station
service, on the model's naive local-standard 8760 clock. Steam bridging
(``min_event_hours = 48``, the loader default for ST_GAS) is applied by the
engine so a committed boiler spans a multi-day event. Zero parameters are fitted
to a price or volume residual.

This is ALL in the ``reliability_floor`` engine: it does NOT enable the separate
``gas_st_netload_drag`` mechanism (that would stack a second floor on one
phenomenon — CLAUDE.md rule 14/19).

Usage:
    python scripts/data/derive_pjm_st_gas_overnight_drag.py            # derive + patch CSV
    python scripts/data/derive_pjm_st_gas_overnight_drag.py --dry-run  # print only
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

from scripts.data.derive_pjm_ct_netload_drag import HOURS, pjm_net_load_mw  # noqa: E402

# --- Overnight pre-positioning window (inclusive, local-standard hour-of-day) ---
# The pre-dawn trough (00:00-06:59) before the afternoon/evening peak. In these
# hours ST_GAS output is non-economic hour-by-hour (prices sit below the boiler's
# part-load MC), so any measured output is HELD COMMITMENT — the unit staying warm
# to ramp for the next peak, not merit dispatch. Contiguous and non-wrapping so it
# maps directly onto the engine's inclusive [start_hour, end_hour] gate (the
# engine cannot express a midnight-wrapping window; the deep-trough hours 0-6
# carry the pre-positioning signal without the post-peak ramp-down tail of h22-23).
OVERNIGHT_HOURS: tuple[int, int] = (0, 6)  # inclusive → engine start=0, end=6

# --- Enable/disable gate (diagnostics only, never residual-tuned) ---
RHO_MIN = 0.3
N_MIN = 30
MIN_STABLE_ST_GAS = MIN_STABLE_PCT_PHYSICAL["ST_GAS"]  # 0.12 (NREL WWSIS-2 T7)

# --- Physical driver onsets (physical anchors, not backcast-chosen) ---
HOT_PERCENTILE = 95.0  # hot onset = zone p95 tmax (design cooling day)
PJM_COLD_ALERT_C = -12.0  # PJM Manual 13 Cold Weather Alert (tmin <= 10 F)
NETLOAD_ONSET_PERCENTILE = 70.0  # high-stress onset = system p70 daily-peak NL

# --- Pure-play / station-service (same basis as derive_pjm_st_gas_netload_drag) ---
_PURE_PLAY_ST_SHARE = 0.90
_ST_NET_OF_GROSS = 1.0 - campd.DEFAULT_PARASITIC_LOAD_PCT["ST_GAS"]  # ~0.95
_STEAM_MIN_EVENT_HOURS = 48  # loader default for ST_GAS; engine bridges the event

_DAYS = HOURS // 24  # 365 (non-leap model clock)
# Cumulative days at the start of each month (non-leap), date -> day-of-year.
_MONTH_START_DAY = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]


def _doy_nonleap(dates: pd.Series) -> np.ndarray:
    """Map dates to non-leap day-of-year (0-364); Feb 29 -> -1."""
    m = dates.dt.month.to_numpy(dtype=int)
    d = dates.dt.day.to_numpy(dtype=int)
    base = np.array(_MONTH_START_DAY)[m - 1]
    idx = base + (d - 1)
    return np.where((m == 2) & (d == 29), -1, idx)


def zonal_pure_play_st_gas(year: int) -> dict[str, dict[int, float]]:
    """Return ``{zone: {plant_code: ST_GAS nameplate MW}}`` for pure-play plants.

    A plant enters its zone's group only when >= ``_PURE_PLAY_ST_SHARE`` of its
    model capacity is ST_GAS, so the plant-summed CAMPD series measures gas-steam
    units only. Zone comes from the eGRID/EIA-860 geography lookup (same names the
    per-zone weather series carries); class + nameplate from the model fleet.
    """
    cfg = get_iso_config("PJM")
    zl = build_zone_lookup("PJM")
    gens = load_fleet_from_csv("PJM", cfg, year=year)
    plant_cap: dict[int, float] = defaultdict(float)
    st_cap: dict[int, float] = defaultdict(float)
    for g in gens:
        pc = int(g.plant_code)
        if pc <= 0:
            continue
        plant_cap[pc] += float(g.pmax_mw)
        if g.plant_group == "ST_GAS":
            st_cap[pc] += float(g.pmax_mw)
    by_zone: dict[str, dict[int, float]] = defaultdict(dict)
    for pc, sc in st_cap.items():
        if sc <= 0.0 or pc not in zl:
            continue
        if sc / plant_cap[pc] >= _PURE_PLAY_ST_SHARE:
            by_zone[zl[pc]][pc] = sc
    return by_zone


def measured_plant_hourly(year: int, plant_codes: set[int]) -> dict[int, np.ndarray]:
    """Per-plant 8760-hour net MW (CAMPD CEMS, ST_GAS station-service netted)."""
    states = campd.states_for_iso("PJM")
    df = campd.load_campd_hourly(states, [year])
    net = campd.plant_hourly_net(
        df, {pid: _ST_NET_OF_GROSS for pid in plant_codes}, year, hours=HOURS
    )
    return {pid: series for pid, series in net.items() if pid in plant_codes}


def _overnight_daily(
    plant_hourly: dict[int, np.ndarray], plant_npl: dict[int, float], nameplate: float
) -> tuple[np.ndarray, np.ndarray]:
    """Daily overnight ``(cf, online_frac)`` arrays (length ``_DAYS``).

    * ``cf[d]``          = zone overnight MWh on day d / (nameplate × window_hours)
    * ``online_frac[d]`` = nameplate-weighted share of the fleet online (any
      positive gross load) DURING the overnight window on day d.
    """
    sh, eh = OVERNIGHT_HOURS
    win_cols = np.arange(sh, eh + 1)  # inclusive
    win_h = win_cols.size
    zone_mw = np.zeros(HOURS)
    online_npl = np.zeros(_DAYS)
    for pid, series in plant_hourly.items():
        zone_mw += series
        day_mat = series.reshape(_DAYS, 24)[:, win_cols]
        online = day_mat.sum(axis=1) > 0.0  # online overnight that day
        online_npl += online.astype(float) * plant_npl.get(pid, 0.0)
    overnight_mwh = zone_mw.reshape(_DAYS, 24)[:, win_cols].sum(axis=1)
    cf = np.clip(overnight_mwh / (nameplate * win_h), 0.0, 1.0)
    online_frac = np.clip(online_npl / nameplate, 0.0, 1.0)
    return cf, online_frac


def _zone_weather(zone: str) -> pd.DataFrame:
    """Per-year daily ``tmax_c``/``tmin_c`` arrays indexed by day-of-year for a zone."""
    path = RAW_DIR / "pjm-weather" / "pjm_zone_temp_daily.csv"
    w = pd.read_csv(path, parse_dates=["date"])
    return w[w["zone"] == zone].copy()


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


def _daily_peak_nl_gw(year: int) -> np.ndarray:
    """PJM system daily-peak net-load (GW), day-of-year aligned (length ``_DAYS``)."""
    nl = pjm_net_load_mw(year)  # 8760, MW
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
) -> dict:
    """Assemble one limb's coefficients + honesty diagnostics from pooled days."""
    n = int(cf_flag.size)
    commit_frac = float(online_flag.mean()) if n else 0.0
    baseline = float(cf_mild.mean()) if cf_mild.size else 0.0
    baseline_commit = float(online_mild.mean()) if online_mild.size else 0.0
    rho = _spearman(drive_flag, cf_flag) if n >= 2 else float("nan")
    floor_pct = commit_frac * MIN_STABLE_ST_GAS
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
    zone: str, years: tuple[int, ...], plant_year: dict[int, dict[int, float]]
) -> list[dict]:
    """Derive the tmax/tmin/netload overnight ST_GAS limbs for one zone."""
    # Pool the day-level overnight CF / online-share and each driver across years.
    cf_all, online_all, tmax_all, tmin_all, nl_all = [], [], [], [], []
    zw = _zone_weather(zone)
    for year in years:
        plant_npl = plant_year[year]
        nameplate = float(sum(plant_npl.values()))
        if nameplate <= 0.0:
            continue
        hourly = measured_plant_hourly(year, set(plant_npl))
        cf, online = _overnight_daily(hourly, plant_npl, nameplate)
        temps = _year_temps(zw, year)
        if temps is None:
            continue
        tmax, tmin = temps
        cf_all.append(cf)
        online_all.append(online)
        tmax_all.append(tmax)
        tmin_all.append(tmin)
        nl_all.append(_daily_peak_nl_gw(year))
    if not cf_all:
        return []
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
    fit = _fit_limb((tmax[hot] - thr_hot), cf[hot], online[hot], cf[mild], online[mild])
    rows.append(
        _row(
            zone,
            "tmax",
            thr_hot,
            fit,
            f"hot: zone p{int(HOT_PERCENTILE)} tmax (design cooling day); overnight "
            f"h{OVERNIGHT_HOURS[0]}-{OVERNIGHT_HOURS[1]} pre-positioning",
        )
    )

    # --- tmin (cold day) ---
    thr_cold = PJM_COLD_ALERT_C
    ok = ~np.isnan(tmin)
    cold = ok & (tmin < thr_cold)
    mildc = ok & (tmin >= thr_cold)
    fit = _fit_limb(
        (thr_cold - tmin[cold]), cf[cold], online[cold], cf[mildc], online[mildc]
    )
    rows.append(
        _row(
            zone,
            "tmin",
            thr_cold,
            fit,
            "cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C); overnight "
            f"h{OVERNIGHT_HOURS[0]}-{OVERNIGHT_HOURS[1]} pre-positioning",
        )
    )

    # --- netload (high system-stress day) ---
    thr_nl = float(np.nanpercentile(nl, NETLOAD_ONSET_PERCENTILE))
    hi = nl > thr_nl
    lo = nl <= thr_nl
    fit = _fit_limb((nl[hi] - thr_nl), cf[hi], online[hi], cf[lo], online[lo])
    rows.append(
        _row(
            zone,
            "netload",
            thr_nl,
            fit,
            f"netload: PJM system p{int(NETLOAD_ONSET_PERCENTILE)} daily-peak "
            f"net-load (demand-VRE) GW; overnight h{OVERNIGHT_HOURS[0]}-"
            f"{OVERNIGHT_HOURS[1]} pre-positioning",
            threshold_percentile=int(NETLOAD_ONSET_PERCENTILE),
        )
    )
    return rows


def _row(
    zone: str,
    driver: str,
    threshold: float,
    fit: dict,
    basis: str,
    threshold_percentile: int | None = None,
) -> dict:
    """Build one CSV row dict for a derived limb."""
    return {
        "iso": "PJM",
        "zone": zone,
        "plant_class": "ST_GAS",
        "driver": driver,
        "threshold": round(threshold, 2),
        "floor_pct": round(fit["floor_pct"], 4),
        "enabled": fit["enabled"],
        "commit_frac": round(fit["commit_frac"], 4),
        "min_stable_pct": round(MIN_STABLE_ST_GAS, 4),
        "rho": round(fit["rho"], 4) if not np.isnan(fit["rho"]) else "",
        "n": fit["n"],
        "baseline": round(fit["baseline"], 4),
        "baseline_commit": round(fit["baseline_commit"], 4),
        "threshold_basis": basis,
        "r1_disabled": False,
        "start_hour": OVERNIGHT_HOURS[0],
        "end_hour": OVERNIGHT_HOURS[1],
        "threshold_percentile": threshold_percentile if threshold_percentile else "",
    }


# New columns appended to the PJM CSV (after the existing 15). start_hour/end_hour
# window the floor to the overnight block; threshold_percentile lets the engine
# recompute the netload GW onset from its own net-load basis.
_NEW_COLS = ["start_hour", "end_hour", "threshold_percentile"]


def patch_csv(new_st_rows: list[dict]) -> None:
    """Replace ST_GAS rows in reliability_floor_coeffs_PJM.csv; keep the rest.

    Non-ST_GAS rows are written back VERBATIM (their existing field values
    unchanged) with the three new columns appended empty, so the substance of
    every non-ST_GAS limb is byte-identical (CLAUDE.md rule 14/16: replace the
    ST_GAS limbs, never stack).
    """
    path = REFERENCE_DIR / "reliability_floor_coeffs_PJM.csv"
    lines = path.read_text().splitlines()
    header = lines[0].split(",")
    out = [",".join(header + _NEW_COLS)]
    cls_idx = header.index("plant_class")
    for ln in lines[1:]:
        if not ln.strip():
            continue
        if ln.split(",")[cls_idx].strip() == "ST_GAS":
            continue  # drop old all-day ST_GAS limbs
        out.append(ln + "," * len(_NEW_COLS))  # keep verbatim + empty new cols
    cols = header + _NEW_COLS
    for r in new_st_rows:
        vals = [str(r[c]) for c in cols]
        # The CSV is unquoted (DictReader on plain comma-split); a comma inside any
        # field (e.g. threshold_basis) would shift every downstream column. Fail
        # loudly rather than silently corrupt — basis strings use ';' separators.
        bad = [c for c, v in zip(cols, vals) if "," in v]
        if bad:
            raise ValueError(f"comma in unquoted field(s) {bad} of row {r['zone']}")
        out.append(",".join(vals))
    path.write_text("\n".join(out) + "\n")
    print(f"\npatched {path} ({len(new_st_rows)} ST_GAS overnight rows)")


def _forced_energy_report(
    zone_rows: dict[str, list[dict]],
    years: tuple[int, ...],
    plant_by_year: dict[str, dict[int, dict[int, float]]],
) -> None:
    """Estimate overnight forced ST_GAS TWh vs measured class total (rule 20).

    Combines the ENABLED limbs per zone via the engine's ``maximum`` composition
    (per-hour floor = max floor across active limbs), applies steam event-bridging
    (min_event_hours=48) and the overnight window exactly as the engine would, and
    sums floor MWh (frac × nameplate) against the measured pure-play ST_GAS energy.
    """
    sh, eh = OVERNIGHT_HOURS
    hod = np.arange(HOURS) % 24
    window = (hod >= sh) & (hod <= eh)
    print("\n=== Forced overnight ST_GAS energy vs measured (rule 20 budget) ===")
    for year in years:
        forced_mwh = 0.0
        measured_mwh = 0.0
        nl = pjm_net_load_mw(year)
        peak_nl = nl.reshape(_DAYS, 24).max(axis=1) / 1000.0
        for zone, rows in zone_rows.items():
            plant_npl = plant_by_year[zone][year]
            nameplate = float(sum(plant_npl.values()))
            if nameplate <= 0.0:
                continue
            hourly = measured_plant_hourly(year, set(plant_npl))
            zone_mw = np.zeros(HOURS)
            for s in hourly.values():
                zone_mw += s
            measured_mwh += float(zone_mw.sum())
            zw = _zone_weather(zone)
            temps = _year_temps(zw, year)
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
                else:  # netload
                    thr = float(np.nanpercentile(peak_nl, NETLOAD_ONSET_PERCENTILE))
                    day_flag = peak_nl > thr
                flagged = np.repeat(np.nan_to_num(day_flag), 24)[:HOURS] > 0
                flagged = _bridge_flagged_runs(flagged, _STEAM_MIN_EVENT_HOURS)
                flagged = flagged & window
                frac = np.where(flagged, float(r["floor_pct"]), 0.0)
                combined = np.maximum(combined, frac)
            forced_mwh += float((combined * nameplate).sum())
        pct = forced_mwh / max(measured_mwh, 1.0) * 100.0
        print(
            f"  {year}: forced overnight {forced_mwh / 1e6:.3f} TWh vs measured "
            f"ST_GAS {measured_mwh / 1e6:.2f} TWh  ({pct:.1f}% of class energy)"
        )


def main() -> None:
    """CLI: derive PJM ST_GAS overnight limbs, print diagnostics, patch the CSV."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--dry-run", action="store_true", help="print only; don't write")
    args = ap.parse_args()
    years = tuple(args.years)

    # Pure-play ST_GAS plants per zone, per year (fleet can change year to year).
    plant_by_year: dict[str, dict[int, dict[int, float]]] = defaultdict(dict)
    zones: set[str] = set()
    for year in years:
        for zone, plants in zonal_pure_play_st_gas(year).items():
            plant_by_year[zone][year] = plants
            zones.add(zone)

    zone_rows: dict[str, list[dict]] = {}
    all_rows: list[dict] = []
    print(
        "=== PJM ST_GAS overnight pre-positioning limbs "
        f"(window h{OVERNIGHT_HOURS[0]}-{OVERNIGHT_HOURS[1]}, "
        f"min_stable={MIN_STABLE_ST_GAS}) ==="
    )
    hdr = (
        f"{'zone':16s} {'driver':8s} {'thr':>7s} {'rho':>6s} {'n':>4s} "
        f"{'commit':>7s} {'basel_c':>8s} {'floor':>6s}  enabled"
    )
    print(hdr)
    for zone in sorted(zones):
        # Ensure every requested year has an entry (fall back to empty).
        for year in years:
            plant_by_year[zone].setdefault(year, {})
        rows = derive_zone_limbs(zone, years, plant_by_year[zone])
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

    n_on = sum(1 for r in all_rows if r["enabled"])
    print(f"\n{len(all_rows)} ST_GAS overnight limbs, {n_on} enabled")

    _forced_energy_report(zone_rows, years, plant_by_year)

    if args.dry_run:
        print("\n[dry-run] CSV not written")
        return
    patch_csv(all_rows)


if __name__ == "__main__":
    main()
