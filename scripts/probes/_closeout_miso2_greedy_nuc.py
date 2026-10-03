"""closeout-miso-2 zero-LP greedy: MISO 2019-2022 NUCLEAR_MONTHLY_CF_BY_YEAR coverage repair.

Adapted from ``_closeout_soco2_greedy_nuc.py`` (closeout-soco-2). The keeper
(2026-10-02-w0-miso-fix2) reads the forecast fallback
``NUCLEAR_MONTHLY_CF["MISO"] x (1 - EFORD 0.03)`` in 2019-2022 (no per-year row;
the NRC daily overlay extract starts 2023-06). This re-clears the committed P1
hourlies with the measured rows from ``derive_nuclear_monthly_cf.py --isos MISO``:

* each nuclear unit's cap is rescaled hour by hour to the measured monthly CF
  (nuclear runs at cap in every keeper hour);
* extra nuclear MW displaces in-merit thermal (mc <= zone price + 0.05) from the
  highest offer down; a shortfall is filled cheapest-first from headroom;
* the system price moves only when the in-merit setter is exhausted
  (same-setter rule), and the hour's delta is applied to every zone's monthly
  price (demand-weighted), then C1 / C3a / C3b are re-scored with the live
  scorer on the edited payload.

Writes ``docs/records/miso/closeout-miso-2/greedy_nuc.csv``.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import calibration_verdict as cv  # noqa: E402
from market_sim.config.constants import NUCLEAR_MONTHLY_CF  # noqa: E402

OUT = REPO / "docs/records/miso/closeout-miso-2"
HOURLY = REPO / "results/calibration/w0_miso_span/hourly"
EFORD_NUC = 0.03  # constants EFORD["nuclear"], NERC GADS
FALL = np.array(NUCLEAR_MONTHLY_CF["MISO"]) * (1.0 - EFORD_NUC)
# scripts/data/derive_nuclear_monthly_cf.py --isos MISO --years 2019 2020 2021 2022
NEW = {
    2019: [0.91, 0.88, 0.90, 0.75, 0.76, 0.90, 0.93, 0.97, 0.95, 0.85, 0.92, 1.00],
    2020: [1.00, 1.00, 0.78, 0.71, 0.80, 0.88, 0.89, 0.87, 0.93, 0.72, 0.75, 0.87],
    2021: [0.91, 0.89, 0.83, 0.76, 0.81, 0.91, 0.89, 0.97, 0.91, 0.75, 0.93, 0.99],
    2022: [0.94, 0.93, 0.79, 0.57, 0.74, 0.91, 0.90, 0.96, 1.00, 0.93, 0.93, 0.93],
}
# Scenario B adds the NRC daily-status shutdowns the MISO reactor map omits
# (data/raw/nrc-reactor-status: Duane Arnold 0 % from 2020-08-11, the derecho;
# Palisades 0 % from 2022-05-21) — EIA-860 retires them 11/2020 and 6/2022.
NRC_DARK = {1060: "2020-08-11", 1715: "2022-05-21"}
THERMAL = ["gas_cc", "gas_ct", "gas_st", "coal", "oil"]
TOL = 0.05


def load_payload() -> dict:
    """Decode the keeper's committed run payload."""
    t = (REPO / "frontend/data/backcast/runs/2026-10-02-w0-miso-fix2.js").read_text()
    blob = re.search(r'="([A-Za-z0-9+/=]+)"', t).group(1)
    return json.loads(gzip.decompress(base64.b64decode(blob)))


def greedy_year(
    y: int, dark: bool = False, nextup: bool = False
) -> tuple[dict, np.ndarray, np.ndarray]:
    """Return (class delta TWh, hourly system price delta, hour->month index)."""
    u = pd.read_parquet(HOURLY / f"unit_marginal_{y}.parquet")
    u = u[u["pass"] == "P1"]
    s = pd.read_parquet(HOURLY / f"system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    n_h = int(u.hour.max()) + 1
    mo = (
        pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(n_h), unit="h")
    ).month.values - 1
    nuc = u[u.fuel.astype(str) == "nuclear"]
    cap = nuc.pivot_table(
        index="hour", columns="unit_id", values="cap_mw", observed=True
    ).values
    newcap = cap * (np.array(NEW[y])[mo] / FALL[mo])[:, None]
    if dark:
        cols = nuc.pivot_table(
            index="hour", columns="unit_id", values="cap_mw", observed=True
        ).columns
        for j, uid in enumerate(cols):
            start = NRC_DARK.get(int(str(uid).split("_")[0]))
            if start and pd.Timestamp(start).year == y:
                h0 = int(
                    (pd.Timestamp(start) - pd.Timestamp(f"{y}-01-01"))
                    / pd.Timedelta(hours=1)
                )
                newcap[h0:, j] = 0.0
    dN = (newcap - cap).sum(1)
    zp = s.pivot_table(index="hour", columns="zone", values="price", observed=True)
    th = u[
        u.fuel.astype(str).isin(THERMAL)
        & ~u.unit_id.astype(str).str.endswith("mustrun")
    ]
    zi = zp.columns.get_indexer(th.zone.astype(str))
    ok = zi >= 0
    th = th[ok]
    zprice = zp.values[th.hour.values, zi[ok]]
    H = th.hour.values
    MW = th.mw.values.astype(float)
    CAP = th.cap_mw.values.astype(float)
    MC = th.mc.values.astype(float)
    GRP = np.where(
        th.fuel.astype(str).values == "oil", "oil", th.plant_group.astype(str).values
    )
    order = np.lexsort((-MC, H))
    H, MW, CAP, MC, GRP, ZP = (
        H[order],
        MW[order],
        CAP[order],
        MC[order],
        GRP[order],
        zprice[order],
    )
    bnd = np.searchsorted(H, np.arange(n_h + 1))
    new = MW.copy()
    dprice = np.zeros(n_h)
    for h in range(n_h):
        a, b = bnd[h], bnd[h + 1]
        d = dN[h]
        mw, mc, cp = new[a:b], MC[a:b], CAP[a:b]
        inm = (mc <= ZP[a:b] + TOL) & (mw > 1e-3)
        p0 = mc[inm].max() if inm.any() else 0.0
        if d > 0:
            av = np.where(inm, mw, 0.0)  # sorted by -mc: highest offer first
            cum = np.cumsum(av)
            take = np.clip(d - (cum - av), 0.0, av)
            mw -= take
            still = inm & (mw > 1e-3)
            if take.sum() > 0:
                setter = mc[still].max() if still.any() else 0.0
                dprice[h] = min(0.0, setter - p0)
        elif d < 0:
            hr = np.clip(cp - mw, 0.0, None)
            if nextup:
                # bracketing variant: a unit below the setter with headroom is
                # held by a constraint (floor bridge, fuel envelope), so the
                # shortfall goes to the setter and the offers above it
                up = mc >= p0 - TOL
                if hr[up].sum() >= -d:
                    hr = np.where(up, hr, 0.0)
            hr = hr[::-1]  # cheapest first
            cum = np.cumsum(hr)
            add = np.clip(-d - (cum - hr), 0.0, hr)
            mw += add[::-1]
            used = np.nonzero(add > 1e-6)[0]
            if used.size:
                top = mc[::-1][used[-1]]
                dprice[h] = max(0.0, top - p0)
    dcls = pd.Series(new - MW).groupby(GRP).sum().div(1e6).to_dict()
    dcls["nuclear"] = dN.sum() / 1e6
    return dcls, dprice, mo


def main() -> None:
    P = load_payload()
    rows = []
    cases = [
        (y, d, n)
        for n in (False, True)
        for y in range(2019, 2023)
        for d in (False, True)
        if not d or y in (2020, 2022)
    ]
    for y, dark, nextup in cases:
        yp = json.loads(json.dumps(P["years"][str(y)]))
        yb = json.load(
            gzip.open(REPO / f"frontend/data/backcast/bench/MISO/{y}.json.gz")
        )["bench"]
        b1 = {
            r["key"]: r for r in cv.score_fuelmix(y, P["years"][str(y)], yb, iso="MISO")
        }
        b3a = cv.score_price_mean(y, P["years"][str(y)], yb, "MISO")
        b3b = cv.score_price_shape(y, P["years"][str(y)], yb, "MISO")
        dcls, dprice, mo = greedy_year(y, dark, nextup)
        for k, v in dcls.items():
            yp["gmModel"][k] = yp["gmModel"].get(k, 0) + v
        dmon = np.array([dprice[mo == m].mean() for m in range(12)])
        for z in yp["lmp"].values():
            if z.get("pMon"):
                z["pMon"] = [
                    p if p is None else p + dmon[m] for m, p in enumerate(z["pMon"])
                ]
            if z.get("p") is not None:
                z["p"] = z["p"] + float(dprice.mean())
        n1 = {r["key"]: r for r in cv.score_fuelmix(y, yp, yb, iso="MISO")}
        n3a = cv.score_price_mean(y, yp, yb, "MISO")
        n3b = cv.score_price_shape(y, yp, yb, "MISO")
        flips = [
            (k, b1[k]["status"], n1[k]["status"])
            for k in n1
            if k in b1 and b1[k]["status"] != n1[k]["status"]
        ]
        stg = n1.get("ST_GAS", {})
        rows.append(
            {
                "year": y,
                "scenario": ("B anchor+NRC-dark" if dark else "A anchor")
                + (" / next-up fill" if nextup else " / cheapest fill"),
                "dNuc": round(dcls.get("nuclear", 0), 3),
                "dCC": round(dcls.get("CC_REGULAR", 0), 3),
                "dCCCHP": round(dcls.get("CC_CHP", 0), 3),
                "dCT": round(dcls.get("CT_PEAKER", 0), 3),
                "dSTG": round(dcls.get("ST_GAS", 0), 3),
                "dPRB": round(dcls.get("COAL_PRB", 0), 3),
                "dBIT": round(dcls.get("COAL_BIT", 0), 3),
                "dLIG": round(dcls.get("COAL_LIGNITE", 0), 3),
                "stg_mag_new": stg.get("magnitude"),
                "c3a_base": b3a.get("magnitude"),
                "c3a_new": n3a.get("magnitude"),
                "c3b_base": b3b.get("model"),
                "c3b_new": n3b.get("model"),
                "dP_mean": round(float(dprice.mean()), 3),
                "flips": flips,
            }
        )
    S = pd.DataFrame(rows)
    S.to_csv(OUT / "greedy_nuc.csv", index=False)
    pd.set_option("display.width", 300)
    print(S.to_string())


if __name__ == "__main__":
    main()
