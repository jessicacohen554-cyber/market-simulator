#!/usr/bin/env python3
"""closeout-MISO-w3 phase 0 (ZERO LP): reach of the hourly neighbour seam ladder on 2019-2022.

The keeper arms ``miso_seam_neighbour_hourly_ladder`` + ``_spp`` in every leg, but
``MISO_SEAM_LADDER_NEIGHBOUR_HOURLY{,_SPP}_BY_YEAR`` carry 2023-2025 only, so the
2019-2022 legs degrade to the flat annual MISO-hub ladder (every band one price
all year). This probe re-prices the PJM and SPP bands of the committed keeper's
2019-2022 legs with the frozen derive's 2019-2022 offsets against the measured
PJM western-border DA / SPP North hub DA, holds the keeper's MISO_external price
fixed (static), and walks the keeper's own internal merit stack (unit_marginal)
to size the price response. Static: no LP feedback (the seam re-clears against a
price the arm itself moves), so the quantity reading is an upper bound.

Output: results/phase0/miso/_closeout_miso_w3_seam_hourly_phase0.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia_loader import (  # noqa: E402
    measured_miso_pjm_border_prices,
    measured_miso_spp_hub_prices,
)

BUNDLE = REPO / "results/calibration/closeout_miso_nuc_span/hourly"
OUT = REPO / "results/phase0/miso/_closeout_miso_w3_seam_hourly_phase0.json"

# Frozen derive output (scripts/data/derive_miso_seam_ladders.py --years 2019..2025
# on the 2019-2025 border parquet; 2023-2025 reproduce the committed rows exactly).
OFFSETS = {
    2019: {
        "PJM": {
            "import": (-25.55, -11.82, -5.1, -0.76, 1.65, 3.55, 6.54, 14.69),
            "export": (-31.59,) * 8,
        },
        "SPP": {
            "import": (-1.0, 6.3, 14.3, 24.27, 74.33, 151.78, 151.78, 151.78),
            "export": (-11.78, -36.0, -49.35, -67.92, -67.92, -67.92, -67.92, -67.92),
        },
    },
    2020: {
        "PJM": {
            "import": (-12.33, -12.33, -7.26, -1.47, 0.9, 2.74, 5.12, 9.27),
            "export": (-14.41,) * 8,
        },
        "SPP": {
            "import": (2.73, 8.56, 19.28, 32.87, 42.04, 56.14, 56.14, 56.14),
            "export": (-4.8, -16.91, -31.76, -38.67, -38.67, -38.67, -38.67, -38.67),
        },
    },
    2021: {
        "PJM": {
            "import": (-18.93, -14.28, -6.21, -0.93, 2.47, 7.07, 13.36, 19.15),
            "export": (-46.19,) * 8,
        },
        "SPP": {
            "import": (8.69, 31.26, 59.14, 80.03, 117.33, 117.33, 117.33, 117.33),
            "export": (
                -2.21,
                -12.66,
                -36.57,
                -61.67,
                -927.56,
                -1818.19,
                -2879.68,
                -3194.88,
            ),
        },
    },
    2022: {
        "PJM": {
            "import": (-34.11, -13.62, -4.61, 2.17, 7.4, 14.2, 23.5, 39.3),
            "export": (-63.95,) * 8,
        },
        "SPP": {
            "import": (26.16, 43.22, 58.22, 70.29, 84.31, 127.95, 208.74, 319.0),
            "export": (8.55, -5.68, -22.74, -46.7, -97.28, -97.28, -97.28, -97.28),
        },
    },
}
MONTH_START = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) * 24


def month_of(h: np.ndarray) -> np.ndarray:
    return np.searchsorted(MONTH_START, h, side="right") - 1


def stack_walk(units: pd.DataFrame, dni: np.ndarray, price0: np.ndarray) -> np.ndarray:
    """New system price per hour after ``dni`` MW more net import (static merit walk)."""
    newp = price0.copy()
    disp = units[units.mw > 0.5].sort_values(["hour", "mc"], ascending=[True, False])
    head = units[(units.cap_mw - units.mw) > 0.5].assign(room=lambda d: d.cap_mw - d.mw)
    head = head.sort_values(["hour", "mc"], ascending=[True, True])
    dh = {h: g for h, g in disp.groupby("hour", sort=False)}
    hh = {h: g for h, g in head.groupby("hour", sort=False)}
    for t in np.nonzero(np.abs(dni) > 1.0)[0]:
        if dni[t] > 0 and t in dh:
            g = dh[t]
            g = g[g.mc <= price0[t] + 1e-6]
            cum = g.mw.to_numpy().cumsum()
            i = np.searchsorted(cum, dni[t])
            if i < len(g):
                newp[t] = min(price0[t], float(g.mc.to_numpy()[i]))
        elif dni[t] < 0 and t in hh:
            g = hh[t]
            g = g[g.mc >= price0[t] - 1e-6]
            cum = g.room.to_numpy().cumsum()
            i = np.searchsorted(cum, -dni[t])
            if i < len(g):
                newp[t] = max(price0[t], float(g.mc.to_numpy()[i]))
    return newp


def one_year(y: int) -> dict:
    sysf = pd.read_parquet(BUNDLE / f"system_{y}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    piv = sysf.pivot_table(index="hour", columns="zone", values="price")
    dem = sysf.pivot_table(index="hour", columns="zone", values="demand").fillna(0.0)
    p_ext = piv["MISO_external"].to_numpy()
    zones = [z for z in dem.columns if not z.startswith("MISO_external")]
    load = dem[zones].sum(axis=1).to_numpy()
    p_sys = (piv[zones] * dem[zones]).sum(axis=1).to_numpy() / np.maximum(load, 1.0)
    u = pd.read_parquet(
        BUNDLE / f"unit_marginal_{y}.parquet",
        columns=["unit_id", "fuel", "zone", "hour", "mw", "cap_mw", "mc"],
    )
    u["unit_id"] = u.unit_id.astype(str)
    anchors = {
        "PJM": measured_miso_pjm_border_prices("MISO", y, 8760),
        "SPP": measured_miso_spp_hub_prices("MISO", y, 8760),
    }
    hours = np.arange(8760)
    hod, mon = hours % 24, month_of(hours)
    out = {"year": y}
    dni = np.zeros(8760)
    for seam in ("PJM", "SPP"):
        for side, mark in (("import", "refimp"), ("export", "refexp")):
            rows = u[u.unit_id.str.contains(f"_{mark}_{seam}#", regex=False)]
            piv_mw = (
                rows.pivot_table(index="hour", columns="unit_id", values="mw")
                .reindex(hours)
                .fillna(0.0)
            )
            cap = rows.groupby("unit_id").cap_mw.max()
            cols = sorted(piv_mw.columns, key=lambda c: int(c.rsplit("#", 1)[1]))
            keep = piv_mw[cols].to_numpy()
            k_tot = np.abs(keep).sum(axis=1)
            # envelope proxy: the keeper's own max |flow| in that (month, hod) cell
            env = pd.Series(k_tot).groupby([mon, hod]).transform("max").to_numpy()
            new = np.zeros_like(keep)
            for j, c in enumerate(cols):
                k = int(c.rsplit("#", 1)[1]) - 1
                off = OFFSETS[y][seam][side][k]
                offer = anchors[seam] + off
                clears = p_ext > offer if side == "import" else p_ext < offer
                new[:, j] = np.where(clears, cap[c], 0.0)
            # cheapest-first clip to the envelope proxy
            cum = np.cumsum(new, axis=1)
            new = np.clip(new - np.clip(cum - env[:, None], 0, None), 0, None)
            n_tot = new.sum(axis=1)
            sgn = 1.0 if side == "import" else -1.0
            d = sgn * (n_tot - k_tot)
            dni += d
            out[f"{seam}_{side}_twh_keeper"] = round(float(k_tot.sum()) / 1e6, 3)
            out[f"{seam}_{side}_twh_static"] = round(float(n_tot.sum()) / 1e6, 3)
    internal = u[
        (u.fuel != "import") & ~u.zone.astype(str).str.startswith("MISO_external")
    ]
    internal = internal[["hour", "mw", "cap_mw", "mc"]]
    newp = stack_walk(internal, dni, p_sys)
    dp = newp - p_sys
    lw = lambda x, m=slice(None): float((x[m] * load[m]).sum() / load[m].sum())  # noqa: E731
    out["dNI_twh"] = round(float(dni.sum()) / 1e6, 3)
    out["dP_lw_all"] = round(lw(dp), 3)
    out["dP_lw_month"] = [round(lw(dp, mon == m), 2) for m in range(12)]
    out["dNI_month_twh"] = [
        round(float(dni[mon == m].sum()) / 1e6, 2) for m in range(12)
    ]
    q = pd.qcut(load, 5, labels=False)
    out["dP_lw_load_quintile"] = [round(lw(dp, q == i), 2) for i in range(5)]
    out["keeper_p_lw"] = round(lw(p_sys), 3)
    return out


def main() -> None:
    res = {y: one_year(y) for y in (2019, 2020, 2021, 2022)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    for y, r in res.items():
        print(json.dumps(r))


if __name__ == "__main__":
    main()
