"""PJM-NEXT-33 post-hoc supplementary (ZERO LP, NOT a pre-registered reading).

Over the NEXT-32 M+L uncovered real-dark spells of COAL_BIT plants: the keeper's own offer
(capacity-weighted ``mc`` of the plant's non-floor tranches) against the REAL zonal DA in the
same hours, and the keeper zone price against the real zonal DA. Weighted by dark MW.

Writes ``results/phase0/pjm/_pjmnext33_dark_offer_margin.json``.
Run: ``.venv/bin/python scripts/probes/_pjmnext33_dark_offer_margin.py [YEAR ...]``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
sys.path.insert(0, str(REPO / "src"))
from _pjmnext28_sunk_noload import gas_daily  # noqa: E402
from _pjmnext32_coal_commitment_census import (  # noqa: E402
    FLOOR,
    MIN_DOWN,
    T,
    _runs,
    coal_units,
    covered_masks,
    keeper_plants,
    zone_price,
)

ZONAL = REPO / "data/raw/_validation-source/actual_lmp_zonal_PJM.parquet"
OUT = REPO / "results/phase0/pjm/_pjmnext33_dark_offer_margin.json"
YEARS = tuple(range(2019, 2026))


def run_year(y: int, gas: pd.Series) -> dict:
    """Dark-MW-weighted keeper offer, keeper price and real zonal DA."""
    real = pd.read_parquet(ZONAL)
    real = real[real["year"] == y]
    pr = {
        str(z): g.set_index("hour")["da"].reindex(range(T)).to_numpy(float)
        for z, g in real.groupby("zone")
    }
    zp = zone_price(y)
    days = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(T), "h")
    g_h = gas.reindex(days.normalize()).to_numpy(float)
    kp = keeper_plants(y)
    d = coal_units(y, set(kp))
    cov = covered_masks(y)
    acc = {
        k: 0.0 for k in ("w", "mc", "pk", "pr", "gas", "inmoney_real", "inmoney_keeper")
    }
    for pc, g in d.groupby("facilityId"):
        P = kp.get(int(pc))
        if P is None or P["zone"] not in pr:
            continue
        kinds = np.array([t[0] for t in P["tr"]])
        CAP = np.vstack([t[2] for t in P["tr"]])
        MC = np.vstack([t[3] for t in P["tr"]])
        kstar = float(CAP.sum(0).max())
        if kstar <= 0:
            continue
        capnf = np.where(~np.isin(kinds, FLOOR)[:, None], CAP, 0.0)
        mc_plant = np.nansum(np.nan_to_num(MC) * capnf, 0) / np.maximum(
            capnf.sum(0), 1e-9
        )
        units = {}
        for uid, gu in g.groupby("unitId"):
            gross = np.zeros(T)
            op = np.zeros(T)
            gross[gu["hoy"].to_numpy()] = gu["grossLoad"].fillna(0.0).to_numpy()
            op[gu["hoy"].to_numpy()] = gu["opTime"].fillna(0.0).to_numpy()
            if gross.max() > 0:
                units[uid] = (gross.max(), op <= 0.0)
        if not units:
            continue
        ptot = sum(v[0] for v in units.values())
        w = np.zeros(T)
        for uid, (pk, dark) in units.items():
            ud = dark & ~cov.get((int(pc), uid), np.zeros(T, bool))
            for s, e in _runs(ud):
                if e - s >= MIN_DOWN:
                    w[s:e] += kstar * pk / ptot
        ok = (w > 0) & (capnf.sum(0) > 0) & np.isfinite(pr[P["zone"]])
        if not ok.any():
            continue
        wv, m = w[ok], mc_plant[ok]
        pkz, prz = zp[P["zone"]][ok], pr[P["zone"]][ok]
        acc["w"] += wv.sum()
        acc["mc"] += (wv * m).sum()
        acc["pk"] += (wv * pkz).sum()
        acc["pr"] += (wv * prz).sum()
        acc["gas"] += (wv * g_h[ok]).sum()
        acc["inmoney_real"] += (wv * (prz >= m)).sum()
        acc["inmoney_keeper"] += (wv * (pkz >= m)).sum()
    W = acc["w"]
    return {
        "dark_twh": W / 1e6,
        "offer_mc": acc["mc"] / W,
        "p_keeper_zone": acc["pk"] / W,
        "p_real_zone": acc["pr"] / W,
        "gas": acc["gas"] / W,
        "offer_over_gas": acc["mc"] / acc["gas"],
        "share_inmoney_at_real": acc["inmoney_real"] / W,
        "share_inmoney_at_keeper": acc["inmoney_keeper"] / W,
    }


def main(years: list[int]) -> None:
    gas = gas_daily()
    res = {}
    for y in years:
        res[str(y)] = run_year(y, gas)
        print(
            y, json.dumps({k: round(v, 3) for k, v in res[str(y)].items()}), flush=True
        )
    OUT.write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or list(YEARS))
