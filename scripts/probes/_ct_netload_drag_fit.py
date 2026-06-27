"""Fit the ERCOT CT_PEAKER net-load reliability-drag floor from CAMPD.

Mirrors the ST_GAS net-load drag derivation
(docs/ercot-st-gas-netload-drag-2026-06.md) for simple-cycle gas peakers:
ERCOT commits CT peakers for summer-peak + evening net-load-ramp reliability
(local RUC / RMR), a commitment the hourly energy-only LP — which sees their
~top-of-merit offer — never makes, so the backcast under-runs CT_PEAKER and the
freed energy spills onto cheaper CC. We characterize the missing dispatch as a
clipped line in system net-load (load - wind - solar), the same operational
reserve-tightness proxy the ST_GAS floor uses.

Measured signature (no LP solve): CAMPD hourly net for the registry's
CT_PEAKER plants vs EIA-930 ERCOT net-load, 2023-2025. Prints the CF-vs-net-load
curve overall and by time-of-day block, the Spearman rho, and a pooled
median-per-bin least-squares line with a cap, plus the annual TWh the floor
would add (vs the measured CT under-run it should match).

Usage: python scripts/probes/_ct_netload_drag_fit.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.data import campd  # noqa: E402

REG = REPO / "data/raw/reference/master-plant-registry.csv"
YEARS = [2023, 2024, 2025]
HOURS = 8760


def _ct_peaker_plants():
    """Registry CT_PEAKER plant ids + nameplate MW that carry CAMPD telemetry."""
    reg = pd.read_csv(REG)
    ct = reg[(reg["plant_group"] == "CT_PEAKER") & reg["has_campd_data"].astype(bool)]
    return dict(
        zip(ct["plantid"].astype(int), ct["nameplate_capacity_mw"].astype(float))
    )


def _net_load_eia930(year):
    """ERCOT hourly net-load = EIA-930 demand - wind - solar (MW), length 8760.

    EIA-930 ``period`` is UTC; CAMPD (and the model dispatch clock) are local
    STANDARD time (CST = UTC-6, no DST). We shift the UTC stamps to CST and lay
    the series on the same non-leap ``hour_of_year`` grid CAMPD uses, so the CT
    capacity factor and the net-load it is regressed on are time-aligned.
    """
    reg = pd.read_parquet(REPO / "data/raw/ERCO_region.parquet")
    fue = pd.read_parquet(REPO / "data/raw/ERCO_fueltype.parquet")
    dem = reg[reg["type"] == "D"].set_index("period")["value_mwh"].sort_index()
    vre = (
        fue[fue["fueltype"].isin(["WND", "SUN"])]
        .groupby("period")["value_mwh"]
        .sum()
        .sort_index()
    )
    nl = (dem - vre.reindex(dem.index).fillna(0.0)).dropna()
    # UTC -> CST (local standard), then map to the model's 8760 hour-of-year.
    local = nl.index.tz_convert("Etc/GMT+6")
    keep = local.year == year
    local, vals = local[keep], nl.to_numpy()[keep]
    hoy = campd._hour_index_8760(
        local.month.to_numpy(), local.day.to_numpy(), local.hour.to_numpy()
    )
    out = np.full(HOURS, np.nan)
    ok = hoy >= 0
    out[hoy[ok]] = vals[ok]
    # Fill any gaps (Feb 29 drop / missing stamps) by forward interpolation.
    return pd.Series(out).interpolate(limit_direction="both").to_numpy()


def _ct_fleet_cf(year, plants):
    """CT_PEAKER fleet capacity factor per hour (sum net MW / sum nameplate)."""
    states = campd.states_for_iso("ERCOT")
    df = campd.load_campd_hourly(states, [year])
    net = campd.plant_hourly_net(df, {}, year, hours=HOURS)
    cap = sum(plants.values())
    fleet = np.zeros(HOURS)
    for pid, series in net.items():
        if pid in plants:
            fleet[: series.shape[0]] += series[:HOURS]
    return fleet / cap, fleet, cap


def _hod():
    base = pd.date_range("2023-01-01", periods=HOURS, freq="h")
    return base.hour.to_numpy()


def _binned_median(nl_gw, cf, edges):
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (nl_gw >= lo) & (nl_gw < hi)
        if sel.sum() >= 30:
            rows.append((0.5 * (lo + hi), float(np.median(cf[sel])), int(sel.sum())))
    return rows


def main():
    plants = _ct_peaker_plants()
    print(
        f"CT_PEAKER fleet: {len(plants)} CAMPD plants, "
        f"{sum(plants.values()) / 1000:.2f} GW nameplate"
    )
    hod = _hod()
    pooled_nl, pooled_cf = [], []
    pooled_evening = []
    for year in YEARS:
        nl = _net_load_eia930(year)
        cf, fleet_mw, cap = _ct_fleet_cf(year, plants)
        nl_gw = nl / 1000.0
        twh = fleet_mw.sum() / 1e6
        rho = pd.Series(nl).corr(pd.Series(cf), method="spearman")
        print(
            f"\n=== {year}: CT_PEAKER {twh:.2f} TWh, net-load mean {nl_gw.mean():.1f}"
            f" / max {nl_gw.max():.1f} GW, Spearman(netload,CF) rho={rho:.2f} ==="
        )
        for label, mask in [
            ("overnight 00-05", (hod < 6)),
            ("midday 10-15", (hod >= 10) & (hod < 16)),
            ("evening 17-22", (hod >= 17) & (hod < 23)),
            ("all hours", np.ones(HOURS, bool)),
        ]:
            edges = np.arange(10, 56, 5)
            rows = _binned_median(nl_gw[mask], cf[mask], edges)
            s = "  ".join(f"{int(c)}:{m:.3f}" for c, m, _ in rows)
            print(f"  {label:<16} CFbyNL(GW)  {s}")
        pooled_nl.append(nl_gw)
        pooled_cf.append(cf)
        # evening-ramp signature for the fit (the reliability-commitment block)
        em = (hod >= 17) & (hod < 23)
        pooled_evening.append((nl_gw[em], cf[em]))

    # Pooled median-per-2GW-bin least-squares line on the evening ramp block.
    enl = np.concatenate([e[0] for e in pooled_evening])
    ecf = np.concatenate([e[1] for e in pooled_evening])
    edges = np.arange(10, 56, 2)
    rows = _binned_median(enl, ecf, edges)
    x = np.array([r[0] for r in rows])
    y = np.array([r[1] for r in rows])
    slope, intercept = np.polyfit(x, y, 1)
    cap_frac = float(np.percentile(ecf, 95))
    print("\n=== POOLED evening-ramp fit (median per 2-GW bin) ===")
    print(f"floor_frac = clip({slope:.5f}*netGW {intercept:+.4f}, 0, {cap_frac:.2f})")
    print(
        f"zero below ~{-intercept / slope:.1f} GW; cap {cap_frac:.2f} (95th pct evening CF)"
    )
    # CT serves reliability in the afternoon-evening ramp (solar collapse), NOT
    # overnight (CF~0 there even at high net-load): a pure all-hours net-load
    # floor over-floors. Gate the net-load line to the ramp window [START,END)
    # so it reproduces the measured CT total as a minimum the LP exceeds
    # economically in scarcity hours. (CAISO's CT floor uses the same evening
    # window; net-load inside it is still forward-derivable.)
    hod = _hod()
    for start, end in [(14, 23), (15, 22), (16, 22)]:
        win = (hod >= start) & (hod < end)
        print(f"\n  -- ramp window {start}-{end} ({win.sum()} h/yr) --")
        for year in YEARS:
            nl = _net_load_eia930(year)
            _, fleet_mw, cap = _ct_fleet_cf(year, plants)
            base = np.clip(slope * nl / 1000.0 + intercept, 0, cap_frac)
            floor = np.where(win, base, 0.0)
            floor_twh = (floor * cap).sum() / 1e6
            floored = np.maximum(floor * cap, fleet_mw).sum() / 1e6
            print(
                f"    {year}: floor-energy {floor_twh:.2f} TWh, floored-total "
                f"{floored:.2f} vs measured {fleet_mw.sum() / 1e6:.2f}"
            )


if __name__ == "__main__":
    main()
