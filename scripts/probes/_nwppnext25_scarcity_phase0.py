"""NWPP-NEXT-25 phase 0 (zero LP): is there a measured, forward-reproducible driver of the C3a tail-day gap?

A. WEIM ELAP price decomposition (MCE system energy vs MCC NW congestion) on the tail days.
B. Seam flows during Jan 12-17 2024: keeper vs EIA-930 legs, COI vs CAISO OTC(E) and ETC/TOR usage.
C. Contingency-reserve adequacy (BAL-002-WECC-3, 3 % load + 3 % generation) on keeper dispatch:
   internal headroom (online thermal + offline quick-start + hydro to the measured envelope) with
   and without the seam import headroom at the measured limits.
D. CA citygate daily vs monthly gas on the tail days (the COI reference's daily-fuel route).
Keeper 2026-10-03-nwpp-next-24-head. FINDING-nwppnext25-scarcity-phase0-2026-10-03.md.

Usage: PYTHONPATH=src:. python scripts/probes/_nwppnext25_scarcity_phase0.py
"""

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts/data")
sys.path.insert(0, "scripts/probes")

H = "results/calibration/nwppnext24_span/hourly/"
NW_BAS = ["BPAT", "PACW", "PGE", "PSEI", "SCL", "TPWR", "AVA", "NWMT", "IPCO"]
TAIL_DAYS = [
    "2023-07-25", "2023-07-26", "2023-08-15", "2023-08-16", "2023-10-25",
    "2023-10-26", "2023-10-27", "2023-10-30", "2023-10-31", "2024-01-12",
    "2024-01-13", "2024-01-14", "2024-01-15", "2024-01-16", "2024-01-17",
]
SEAM_KEY = {"CAISO_COI": "COI", "CAISO_NEVP": "NEVP", "WECC_CAN": "BC"}
BAL002_LOAD_FRAC = 0.03  # BAL-002-WECC-3 R1: 3 % of load
BAL002_GEN_FRAC = 0.03  # ... + 3 % of net generation


def section_a() -> None:
    """A: MCE / MCC split of the NW ELAP price on the tail days."""
    d = pd.read_parquet("data/raw/nwpp-weim/weim_rtpd_lmp_15min.parquet")
    t = pd.to_datetime(d.interval_start_utc, utc=True).dt.tz_convert("Etc/GMT+8")
    d["day"] = t.dt.strftime("%Y-%m-%d")
    x = d[d.day.isin(TAIL_DAYS) & d.baa.isin(NW_BAS)]
    print("\n## A. NW ELAP (9 BAAs) daily mean: lmp = mce + mcc (+mcl)")
    print(
        x.groupby("day")
        .agg(lmp=("lmp", "mean"), mce=("mce", "mean"), mcc=("mcc", "mean"))
        .round(0)
        .to_string()
    )


def section_b() -> None:
    """B: keeper seam flows vs EIA-930 legs, Jan 12-17 2024 (import-positive, MW)."""
    from _nwppnext20_seam_phase0 import _measured

    from market_sim.data.transfer_interface_limits import nwpp_seam_limits_hourly

    y = 2024
    u = pd.read_parquet(
        H + f"unit_marginal_{y}.parquet", columns=["unit_id", "fuel", "hour", "mw"]
    )
    im = u[u.fuel == "import"]
    meas = _measured(y)
    lim = nwpp_seam_limits_hourly(y, 8760)
    sl = slice(11 * 24, 17 * 24)
    day = np.arange(8760)[sl] // 24 + 1
    out = {}
    for name, k in SEAM_KEY.items():
        f = im[im.unit_id.str.contains(k)].groupby("hour").mw.sum()
        out[f"model_{k}"] = f.reindex(range(8760), fill_value=0).to_numpy()[sl]
        out[f"meas_{k}"] = -meas[name][sl]
        if name in lim:
            out[f"imp_cap_{k}"] = lim[name][0][sl]
    print("\n## B. Seam import (MW, + = into NWPP), Jan 12-17 2024 daily means")
    print(pd.DataFrame(out).groupby(day).mean().round(0).T.to_string())


def _margins(y: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (internal margin, margin incl. seam import headroom) vs BAL-002-WECC-3, MW."""
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia_loader import measured_hydro_hourly_envelope
    from market_sim.data.transfer_interface_limits import nwpp_seam_limits_hourly

    spec = {n.name: n for n in INTERFACE_NEIGHBORS["NWPP"]}
    env = measured_hydro_hourly_envelope("NWPP", y, 8760)
    u = pd.read_parquet(
        H + f"unit_marginal_{y}.parquet",
        columns=["unit_id", "fuel", "hour", "mw", "cap_mw"],
    )
    s = pd.read_parquet(H + f"system_{y}.parquet")
    s = s[s.zone.str.startswith("NWPP-")]
    load = s.groupby("hour").demand.sum().reindex(range(8760)).to_numpy()
    th = u[u.fuel.isin(["coal", "gas_cc", "gas_ct", "gas_st", "oil"])]
    on = th[th.mw > 1e-3]
    onh = (on.cap_mw - on.mw).groupby(on.hour).sum().reindex(range(8760), fill_value=0)
    qs = th[(th.mw <= 1e-3) & th.fuel.isin(["gas_ct", "oil"])]
    qsh = qs.cap_mw.groupby(qs.hour).sum().reindex(range(8760), fill_value=0)
    hy = u[u.fuel == "hydro"].groupby("hour").mw.sum().reindex(range(8760)).to_numpy()
    im = u[u.fuel == "import"]
    lim = nwpp_seam_limits_hourly(y, 8760)
    seam_head = np.zeros(8760)
    net_imp = np.zeros(8760)
    for name, k in SEAM_KEY.items():
        f = im[im.unit_id.str.contains(k)].groupby("hour").mw.sum()
        f = f.reindex(range(8760), fill_value=0).to_numpy()
        cap = lim[name][0] if name in lim else np.full(8760, spec[name].interface_limit_mw)
        seam_head += np.maximum(cap - f, 0.0)
        net_imp += f
    req = BAL002_LOAD_FRAC * load + BAL002_GEN_FRAC * (load - net_imp)
    internal = onh.to_numpy() + qsh.to_numpy() + np.maximum(env - hy, 0.0)
    return internal - req, internal - req + seam_head


def section_c() -> None:
    """C: hours the contingency requirement is short, without / with seam headroom."""
    print("\n## C. BAL-002-WECC-3 contingency reserve vs keeper headroom (hours short)")
    for y in range(2019, 2026):
        m_int, m_all = _margins(y)
        print(
            f"{y}: internal-only short {int((m_int < 0).sum()):5d} h | with seam headroom "
            f"short {int((m_all < 0).sum()):3d} h, min margin {m_all.min():6.0f} MW"
        )


def section_d() -> None:
    """D: CA citygate daily vs its month mean on the tail days ($/MMBtu)."""
    g = pd.read_csv("data/raw/gas-prices/caiso_citygate_daily.csv", parse_dates=["date"])
    mm = g.groupby(g.date.dt.to_period("M")).ca_composite_usd_mmbtu.mean()
    print("\n## D. CA citygate composite daily vs month mean")
    for dd in TAIL_DAYS:
        r = g[g.date == dd]
        if len(r):
            print(
                f"{dd} {float(r.ca_composite_usd_mmbtu.iloc[0]):6.2f}  month "
                f"{float(mm[pd.Period(dd, 'M')]):5.2f}"
            )


def main() -> None:
    """Run sections A-D."""
    section_a()
    section_b()
    section_c()
    section_d()


if __name__ == "__main__":
    main()
