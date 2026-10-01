"""PJM-NEXT-11 audit (a) (zero LP): is the COAL_BIT over-run an OFFER/response defect or a PRICE defect?

For every bench COAL_BIT plant (PJM-NEXT-10 helpers: the keeper's registered run payload + the
bench's CAMPD net hourly), a plant-hour's loading is ``MW / cap`` with ``cap`` = the plant's CAMPD
p99 net output (the same denominator on both sides). Each plant-hour is binned by price:

* model side: the keeper's own zonal P1 price (committed ``hourly/system_<y>.parquet``);
* actual side: the PJM DA hub LMP read as that zone's price (``HUB`` map, PJM-NEXT-10), shifted
  from UTC to the local year.

With ``L(b)`` = loading in bin ``b`` and ``H(b)`` = capacity-hours in bin ``b``, the energy gap
splits exactly:

    E_model - E_actual = sum_b [L_m(b) - L_a(b)] H_m(b)     # response: same price, more MW
                       + sum_b L_a(b) [H_m(b) - H_a(b)]     # price: model hours sit in dearer bins

A bin the actual side never visits takes the nearest populated bin's ``L_a``.
Writes ``results/phase0/pjm/_pjmnext11_margin_audit.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
import _pjmnext10_coal_phase0 as P10  # noqa: E402

OUT = REPO / "results/phase0/pjm/_pjmnext11_margin_audit.json"
EDGES = np.array([-1e9, 0, 10, 15, 20, 25, 30, 35, 40, 50, 60, 80, 100, 150, 1e9])
UTC_TO_EPT_H = (
    5  # EST offset; DST ignored (one-hour shifts do not move a $5 bin materially)
)


def model_zone_prices(y: int) -> pd.DataFrame:
    """Hour x zone keeper P1 price."""
    d = pd.read_parquet(P10.BUNDLE / f"hourly/system_{y}.parquet")
    d = d[d["pass"] == "P1"]
    return d.pivot_table(index="hour", columns="zone", values="price").sort_index()


def actual_hub_prices(y: int) -> pd.DataFrame:
    """Hour x hub DA LMP on the local year (UTC shifted by the EST offset, tail padded)."""
    h = P10.hub_prices(y)
    h = h.iloc[UTC_TO_EPT_H:]
    pad = pd.DataFrame([h.iloc[-1]] * UTC_TO_EPT_H, columns=h.columns)
    return pd.concat([h, pad], ignore_index=True).iloc[:8760]


def curves(load: np.ndarray, cap: np.ndarray, price: np.ndarray) -> tuple:
    """Per-bin loading L(b) and capacity-hours H(b)."""
    b = np.clip(np.searchsorted(EDGES, price, side="right") - 1, 0, len(EDGES) - 2)
    n = len(EDGES) - 1
    mw = np.bincount(b, weights=load, minlength=n)
    ch = np.bincount(b, weights=cap, minlength=n)
    with np.errstate(invalid="ignore", divide="ignore"):
        lo = mw / ch
    return lo, ch


def fill_nearest(lo: np.ndarray, ch: np.ndarray) -> np.ndarray:
    """Fill empty bins with the nearest populated bin's loading."""
    ok = np.where(ch > 0)[0]
    out = lo.copy()
    for i in np.where(ch <= 0)[0]:
        out[i] = lo[ok[np.argmin(np.abs(ok - i))]]
    return out


def main() -> None:
    """Decompose every year and write the JSON."""
    run = P10.load_run()
    out = {}
    for y in P10.YEARS:
        ps = P10.plant_series(y, run)
        mz, ah = model_zone_prices(y), actual_hub_prices(y)
        lm, pm, la, pa, cp = [], [], [], [], []
        for m, c, v in ps.values():
            zone = v["zone"]
            if zone not in mz.columns or P10.HUB.get(zone) not in ah.columns:
                continue
            cap = float(np.quantile(c, 0.99)) if c.max() > 0 else float(m.max())
            if cap <= 0:
                continue
            lm.append(m)
            la.append(c)
            pm.append(mz[zone].to_numpy()[:8760])
            pa.append(ah[P10.HUB[zone]].to_numpy()[:8760])
            cp.append(np.full(8760, cap))
        lm, la, pm, pa, cp = map(np.concatenate, (lm, la, pm, pa, cp))
        ok = np.isfinite(pm) & np.isfinite(pa)
        lm_b, hm = curves(lm[ok], cp[ok], pm[ok])
        la_b, ha = curves(la[ok], cp[ok], pa[ok])
        la_f = fill_nearest(la_b, ha)
        lm_f = np.nan_to_num(lm_b)
        response = float(((lm_f - la_f) * hm).sum() / 1e6)
        price = float((la_f * (hm - ha)).sum() / 1e6)
        rec = {
            "n_plants": len(ps),
            "model_twh": round(float(lm[ok].sum() / 1e6), 2),
            "campd_twh": round(float(la[ok].sum() / 1e6), 2),
            "gap_twh": round(float((lm[ok].sum() - la[ok].sum()) / 1e6), 2),
            "response_part_twh": round(response, 2),
            "price_part_twh": round(price, 2),
            "bins_usd": [float(e) for e in EDGES[1:-1]],
            "loading_model": [
                None if not np.isfinite(x) else round(float(x), 3) for x in lm_b
            ],
            "loading_actual": [
                None if not np.isfinite(x) else round(float(x), 3) for x in la_b
            ],
            "cap_share_model": [round(float(x / hm.sum()), 3) for x in hm],
            "cap_share_actual": [round(float(x / ha.sum()), 3) for x in ha],
            "median_price_model": round(float(np.median(pm[ok])), 2),
            "median_price_actual": round(float(np.median(pa[ok])), 2),
        }
        out[str(y)] = rec
        print(
            y,
            {
                k: rec[k]
                for k in (
                    "gap_twh",
                    "response_part_twh",
                    "price_part_twh",
                    "median_price_model",
                    "median_price_actual",
                )
            },
            flush=True,
        )
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
