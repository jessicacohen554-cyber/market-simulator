"""STEP-1 outage-gate diagnosis: audit every CAMPD-detected down-span per ISO.

For the dispatchable thermal fleet (coal + combined-cycle + gas-steam) this
replicates the *unit-level* outage detector (``derive_campd_unit_outages``)
exactly, but instead of writing the filtered outage CSV it emits one row per
**pre-filter** detected down-span, tagged KEPT vs DROPPED by the current
local-band revealed-availability filter, and characterised so we can answer:

  Is the residual thermal over-run still outage-gate looseness (true long
  MECHANICAL outages dropped as "economic idle" because they sit in
  low-net-load windows), or has the gate become correct (residual is
  price-formation / fuel-cost the outage input cannot fix)?

Per span we record: duration_days, mean/max CF (full STOP vs partial low-CF
backdown), the fraction of hours fully off, the high-load overlap (the filter's
own statistic), the annual net-load percentile the span's hours sit in, and the
KEPT/DROPPED verdict. Capacity-weighted GW-days are split KEPT/DROPPED and, for
DROPPED, further into LONG FULL STOPS (the mechanical-outage signature) vs the
rest.

No solve, no LMP, no price target — exogenous CAMPD operation + EIA-930 net
load only. Writes a per-span CSV and prints a per-ISO summary.

    python scripts/probes/_outage_gate_audit.py --iso PJM --years 2023 2024 2025
    python scripts/probes/_outage_gate_audit.py --all --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import EIA_860_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    QUALIFYING_PLANT_GROUPS,
    ST_GAS_PEAKER_PLANTS,
)
from scripts.lib.outage_detect import (  # noqa: E402
    HIGH_LOAD_PCTL,
    MIN_INMERIT_HOURS,
    ST_GAS_CF_PEAK,
    WINDOW_DAYS,
    _ISO_TO_BA,
    detect_outages,
    detect_outages_eventbased,
    high_load_mask,
)
from scripts.data.derive_campd_unit_outages import (  # noqa: E402
    _load_unit_year,
    _unit_year_grid,
    build_capacity_index,
    unit_capacity_mw,
)

# Depth threshold separating a genuine FULL STOP from a partial low-CF backdown.
# A unit averaging below this CF across the whole span produced essentially
# nothing — the mechanical-outage signature; economic idling backs DOWN but
# rarely fully STOPS for the whole window. Audit-only (not a model knob).
FULL_STOP_CF: float = 0.02
# "Long" span floor for the long-full-stop tally (the mechanical signature).
LONG_DAYS: float = 14.0


def net_load_for_year(iso: str, year: int) -> np.ndarray | None:
    """Return the EIA-930 net-load array (demand - wind - solar) on the year clock.

    Same source/columns as ``high_load_mask`` so the percentile bands align with
    the filter. Returns ``None`` when the BA file/year is unavailable.
    """
    ba = _ISO_TO_BA.get(iso.upper())
    if ba is None:
        return None
    path = REPO / "data" / "raw" / "eia-930-hourly" / f"{ba} hourly.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[pd.to_datetime(df["Local date"]).dt.year == year].copy()
    if df.empty:
        return None
    df["dt"] = pd.to_datetime(df["Local date"]) + pd.to_timedelta(
        df["Hour"].astype(int) - 1, unit="h"
    )

    def _col(*names: str) -> np.ndarray:
        for nm in names:
            if nm in df.columns:
                return df[nm].to_numpy(dtype=float)
        return np.zeros(len(df), dtype=float)

    dem = _col("Adjusted demand", "Demand")
    if not np.isfinite(dem).any():
        return None
    wnd = np.nan_to_num(_col("Adjusted WND Gen", "NG: WND"))
    sun = np.nan_to_num(_col("Adjusted SUN Gen", "NG: SUN"))
    net = dem - wnd - sun
    n_hours = 8784 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 8760
    clock = pd.date_range(f"{year}-01-01", periods=n_hours, freq="h")
    key = {(t.month, t.day, t.hour): v for t, v in zip(df["dt"], net)}
    out = np.full(n_hours, np.nan)
    for i, t in enumerate(clock):
        v = key.get((t.month, t.day, t.hour))
        if v is None and t.month == 2 and t.day == 29:
            v = key.get((2, 28, t.hour))
        if v is not None:
            out[i] = v
    return out


def _group_map(iso: str) -> tuple[dict[int, str], dict[int, str]]:
    """Return ``(group_by_code, name_by_code)`` for the ISO fleet (qualifying)."""
    if iso == "ERCOT":
        bins = pd.read_csv(
            REPO / "data" / "raw" / "reference" / "custom-bin-assignments.csv"
        )
        group_by_code = {
            int(c): str(g) for c, g in zip(bins["Plant_Code"], bins["Plant_Group"])
        }
        name_by_code = {
            int(c): str(n) for c, n in zip(bins["Plant_Code"], bins["Plant_Name"])
        }
        return group_by_code, name_by_code
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv, load_retired_within_window

    cfg = get_iso_config(iso)
    group_by_code: dict[int, str] = {}
    name_by_code: dict[int, str] = {}
    fleet = load_fleet_from_csv(iso, cfg) + load_retired_within_window(iso, cfg)
    for g in fleet:
        if int(g.plant_code) > 0 and g.plant_group:
            group_by_code[int(g.plant_code)] = g.plant_group
            name_by_code[int(g.plant_code)] = g.name
    return group_by_code, name_by_code


def audit_iso(iso: str, years: list[int], min_outage_days: float) -> pd.DataFrame:
    """Return a per-span audit DataFrame for one ISO (unit-level detector)."""
    iso = iso.upper()
    min_outage_hours = int(round(min_outage_days * 24))
    group_by_code, name_by_code = _group_map(iso)
    eia860 = EIA_860_DIR / "eia860_generators.parquet"
    exact, by_digits = build_capacity_index(eia860)
    states = campd.states_for_iso(iso)

    mask_cache: dict[int, np.ndarray | None] = {}
    net_cache: dict[int, np.ndarray | None] = {}
    pctl_thresh: dict[int, np.ndarray | None] = {}  # annual pctl bands of net load
    rows: list[dict] = []

    for state in states:
        for year in years:
            df = _load_unit_year(state, year)
            if df.empty:
                continue
            df["facilityId"] = [
                campd.CAMPD_UNIT_PLANT_REMAP.get((f, u), f)
                for f, u in zip(df["facilityId"].astype(int), df["unitId"].astype(str))
            ]
            if year not in mask_cache:
                clock = pd.date_range(
                    f"{year}-01-01", f"{year}-12-31 23:00:00", freq="h"
                )
                mask_cache[year] = high_load_mask(
                    iso, year, len(clock), HIGH_LOAD_PCTL, WINDOW_DAYS
                )
                net = net_load_for_year(iso, year)
                net_cache[year] = net
                if net is not None:
                    fin = net[np.isfinite(net)]
                    # annual percentile-rank lookup table (10 bands)
                    pctl_thresh[year] = (
                        np.nanpercentile(fin, np.arange(0, 101, 10))
                        if fin.size
                        else None
                    )
            mask = mask_cache[year]
            net = net_cache[year]

            for fac_id, fac in df.groupby("facilityId", observed=True):
                group = group_by_code.get(int(fac_id))
                if group not in QUALIFYING_PLANT_GROUPS:
                    continue
                if int(fac_id) in ST_GAS_PEAKER_PLANTS:
                    continue
                fac_name = name_by_code.get(
                    int(fac_id), str(fac["facilityName"].iloc[0])
                )
                units = {
                    uid: _unit_year_grid(u, year)
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                unit_is_coal = {
                    uid: str(u["primaryFuelInfo"].iloc[0]).strip().lower()
                    in ("coal", "coal refuse")
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                peaks = {uid: float(g.max()) for uid, g in units.items()}
                caps = {
                    uid: unit_capacity_mw(
                        int(fac_id), uid, exact, by_digits, peaks[uid]
                    )
                    for uid in units
                }
                for uid, gross in units.items():
                    detect_cap, derate_cap, _src = caps[uid]
                    if peaks[uid] <= 0.0 or derate_cap <= 0.0:
                        continue
                    is_coal = unit_is_coal[uid]
                    if is_coal:
                        windows = detect_outages(gross, detect_cap, min_outage_hours)
                    else:
                        windows = detect_outages_eventbased(
                            gross, detect_cap, min_outage_hours, ST_GAS_CF_PEAK
                        )
                    if not windows:
                        continue
                    cf = gross / detect_cap if detect_cap > 0 else np.zeros_like(gross)
                    clock = pd.date_range(
                        f"{year}-01-01", f"{year}-12-31 23:00:00", freq="h"
                    )
                    for s, e in windows:
                        dur_h = e - s
                        span_cf = cf[s:e]
                        mean_cf = float(span_cf.mean())
                        max_cf = float(span_cf.max())
                        frac_off = float((span_cf < 0.01).mean())
                        overlap = int(mask[s:e].sum()) if mask is not None else -1
                        kept = (
                            overlap >= MIN_INMERIT_HOURS if mask is not None else True
                        )
                        # annual net-load percentile band the span's hours sit in
                        nl_pctl = np.nan
                        if net is not None and pctl_thresh.get(year) is not None:
                            span_net = net[s:e]
                            span_net = span_net[np.isfinite(span_net)]
                            if span_net.size:
                                bands = pctl_thresh[year]
                                nl_pctl = float(
                                    np.searchsorted(bands, np.median(span_net)) * 10
                                )
                        full_stop = mean_cf < FULL_STOP_CF
                        rows.append(
                            {
                                "iso": iso,
                                "year": year,
                                "facility_id": int(fac_id),
                                "facility_name": fac_name[:28],
                                "unit_id": str(uid),
                                "plant_group": group,
                                "is_coal": is_coal,
                                "detect_cap_mw": round(detect_cap, 1),
                                "derate_cap_mw": round(derate_cap, 1),
                                "start": clock[s].strftime("%Y-%m-%d"),
                                "end": clock[e - 1].strftime("%Y-%m-%d"),
                                "dur_days": round(dur_h / 24.0, 1),
                                "mean_cf": round(mean_cf, 3),
                                "max_cf": round(max_cf, 3),
                                "frac_off": round(frac_off, 3),
                                "full_stop": full_stop,
                                "hiload_overlap_h": overlap,
                                "median_nl_pctl": nl_pctl,
                                "kept": kept,
                                "gw_days": round(derate_cap * dur_h / 24.0 / 1000.0, 2),
                            }
                        )
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame, iso: str) -> None:
    """Print the per-ISO KEPT/DROPPED GW-day decomposition and the headline."""
    if df.empty:
        print(f"\n=== {iso}: no detected down-spans ===")
        return
    print(f"\n{'=' * 78}\n=== {iso} outage-gate audit ===\n{'=' * 78}")
    tot = df["gw_days"].sum()
    kept = df[df["kept"]]
    dropped = df[~df["kept"]]
    print(
        f"detected spans: {len(df)}  |  total GW-days: {tot:.0f}  "
        f"(KEPT {kept['gw_days'].sum():.0f} / {100 * kept['gw_days'].sum() / tot:.0f}%, "
        f"DROPPED {dropped['gw_days'].sum():.0f} / "
        f"{100 * dropped['gw_days'].sum() / tot:.0f}%)"
    )
    # The crux: of the DROPPED GW-days, how many are LONG FULL STOPS
    # (mechanical-outage signature) vs partial/short (economic idle)?
    dl = dropped[(dropped["dur_days"] >= LONG_DAYS) & dropped["full_stop"]]
    dl_partial = dropped[(dropped["dur_days"] >= LONG_DAYS) & ~dropped["full_stop"]]
    print(
        f"DROPPED breakdown: long(>={LONG_DAYS:.0f}d) FULL-STOP "
        f"{dl['gw_days'].sum():.0f} GWd ({len(dl)} spans)  |  "
        f"long partial-backdown {dl_partial['gw_days'].sum():.0f} GWd "
        f"({len(dl_partial)} spans)  |  "
        f"short/other {dropped[dropped['dur_days'] < LONG_DAYS]['gw_days'].sum():.0f} GWd"
    )
    # by fuel
    for fuel, sub in [("COAL", df[df["is_coal"]]), ("CC/gas", df[~df["is_coal"]])]:
        if sub.empty:
            continue
        d = sub[~sub["kept"]]
        dlf = d[(d["dur_days"] >= LONG_DAYS) & d["full_stop"]]
        print(
            f"  {fuel:7s}: {sub['gw_days'].sum():6.0f} GWd tot, "
            f"DROPPED {d['gw_days'].sum():6.0f}, "
            f"DROPPED long-full-stop {dlf['gw_days'].sum():6.0f} "
            f"({len(dlf)} spans)"
        )
    # top dropped long full-stops (the suspects)
    if not dl.empty:
        print("\n  TOP DROPPED LONG FULL-STOPS (mechanical-outage suspects):")
        print(
            f"  {'plant':<28}{'unit':<7}{'grp':<11}{'yr':>5}{'days':>6}"
            f"{'meanCF':>7}{'cap':>7}{'ovlp':>5}{'nlpct':>6}{'GWd':>7}"
        )
        for _, r in dl.sort_values("gw_days", ascending=False).head(20).iterrows():
            print(
                f"  {r['facility_name']:<28}{r['unit_id']:<7}{r['plant_group']:<11}"
                f"{r['year']:>5}{r['dur_days']:>6.0f}{r['mean_cf']:>7.3f}"
                f"{r['derate_cap_mw']:>7.0f}{r['hiload_overlap_h']:>5}"
                f"{r['median_nl_pctl']:>6.0f}{r['gw_days']:>7.1f}"
            )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="PJM")
    ap.add_argument("--all", action="store_true", help="run all six ISOs")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--min-outage-days", type=float, default=5.0)
    ap.add_argument("--out-dir", default=str(REPO / "results" / "outage_gate_audit"))
    args = ap.parse_args()

    isos = (
        ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]
        if args.all
        else [args.iso.upper()]
    )
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for iso in isos:
        df = audit_iso(iso, args.years, args.min_outage_days)
        if not df.empty:
            df.to_csv(out_dir / f"audit_{iso}.csv", index=False)
        summarize(df, iso)


if __name__ == "__main__":
    main()
