"""nyiso-199 PHASE 0c (NO LP) — the CT_PEAKER band basis: the measured offer-array
delta, its reachability bound, and its two-sided price exposure, on committed
artifacts plus a MEASUREMENT-ONLY ``fleet_only`` rebuild (rule 29 ``[R-SCREEN]``
step 0).

Phase 0a/0b established that ``CT_PEAKER``'s whole deficit is INTERIOR — 100.0 %
in every one of 2023/2024/2025, zero at the availability envelope and zero at a
floor — so the object is offer position and nothing else.  This probe measures
what the class's own registered measured basis would do to that offer, WITHOUT
solving:

  * **D-1 the delta** — rebuild the fleet with ``CT_PEAKER``'s
    ``committed``/``econ_low``/``econ_high`` set to its OWN registered
    ``phys_committed``/``phys_econ_low``/``phys_econ_high``
    (``nyiso_campd_marginal_hr_summary.csv`` p50s, n=70) and diff ``mc_base``.
    Zero values are chosen; the arm selects nothing.
  * **D-2 the reachability bound** — available CT capacity whose offer sits
    below its own zonal LMP, before and after, and the energy that bounds.
  * **D-3 the price exposure** — the same-weights merit-order crossing: the
    price at which the ARM's cumulative available capacity equals the KEEPER's
    at the keeper's own clearing price.  An INDICATOR, never the scored C3a.
  * **D-4 the footprint by year** — newly in-the-money CT MWh.  Contains no
    meter and no residual, so it may name the rule-29 screen year.

Writes ``results/calibration/_nyiso199_ct_band_basis_phase0.json``.

Usage::

    python scripts/probes/nyiso199_ct_band_basis_phase0.py \
        --keeper-cache <dir with fleet_<yr>.pkl> --arm-cache <dir with armCT_<yr>.pkl>
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "results/calibration/nyiso196_extract_basis"
KEEPER_ID = "2026-09-06-nyiso-196-extract-basis"
T = 8760
CLASSES = ("CC_REGULAR", "CC_CHP", "ST_GAS", "CT_PEAKER", "CT_CHP", "ST_CHP")
#: the arm's values -- NYISO's own registered measured counterparts, nothing chosen.
ARM_BANDS = {"committed": 0.843, "econ_low": 0.661, "econ_high": 0.658}


def _r(x, n=3):
    v = float(x)
    return round(v, n) if np.isfinite(v) else None


def _parse(u: str):
    for k in CLASSES:
        if u.startswith(k + "_"):
            rest = u[len(k) + 1 :]
            head, _, band = rest.rpartition("_")
            zone, _, pc = head.rpartition("_p")
            return k, zone, pc, band
    return "", "", "", ""


def _fam(b: str) -> str:
    return "econ" if (b.startswith("econc") or b in ("econlo", "econhi", "econ")) else b


def year_block(yr: int, kc: Path, ac: Path) -> dict:
    k0 = pickle.load(open(kc / f"fleet_{yr}.pkl", "rb"))
    a0 = pickle.load(open(ac / f"armCT_{yr}.pkl", "rb"))
    if k0["unit_ids"] != a0["unit_ids"]:
        raise SystemExit("roster changed between the two rebuilds — not a pure offer delta")
    P = [_parse(u) for u in k0["unit_ids"]]
    delta = a0["mc_base"][:, :T] - k0["mc_base"][:, :T]
    moved = np.abs(delta).max(axis=1) > 1e-9

    # ---- D-1: exactly which rows moved, and by how much --------------------
    from collections import Counter

    cells = Counter((P[i][0], _fam(P[i][3])) for i in np.where(moved)[0])
    band_rows = {}
    ct = np.array([i for i, p in enumerate(P) if p[0] == "CT_PEAKER"])
    for f in ("committed", "econ", "peak"):
        idx = np.array([i for i in ct if _fam(P[i][3]) == f])
        if not idx.size:
            continue
        live = k0["availability"][idx, :T] > 0
        w = k0["pmax"][idx][:, None] * live
        tw = w.sum()
        band_rows[f] = {
            "rows": int(idx.size),
            "nameplate_mw": _r(float(k0["pmax"][idx].sum()), 1),
            "keeper_offer_cap_wtd": _r(float((k0["mc_base"][idx, :T] * w).sum() / tw), 2),
            "arm_offer_cap_wtd": _r(float((a0["mc_base"][idx, :T] * w).sum() / tw), 2),
            "delta_usd_mwh": _r(float((delta[idx] * w).sum() / tw), 2),
            "delta_std_over_hours": _r(float(np.std((delta[idx] * w).sum(axis=0) / np.maximum(w.sum(axis=0), 1e-9))), 4),
        }

    # ---- D-2 / D-3 / D-4 ---------------------------------------------------
    sysp = pd.read_parquet(BUNDLE / "hourly" / f"system_{yr}.parquet")
    pm = sysp.pivot(index="hour", columns="zone", values="price")
    zones = list(pm.columns)
    lw = (
        sysp.pivot(index="hour", columns="zone", values="demand")[zones].to_numpy()[:T]
        if "demand" in sysp.columns
        else np.ones((T, len(zones)))
    )
    W = lw / np.maximum(lw.sum(axis=1, keepdims=True), 1e-9)
    P0z = pm[zones].to_numpy()[:T]

    lmp_ct = np.zeros((ct.size, T))
    for j, i in enumerate(ct):
        z = P[i][1]
        lmp_ct[j] = pm[z].to_numpy()[:T] if z in pm.columns else 0.0
    cap_ct = k0["pmax"][ct][:, None] * k0["availability"][ct, :T]
    itm_k = (k0["mc_base"][ct, :T] < lmp_ct) & (cap_ct > 0)
    itm_a = (a0["mc_base"][ct, :T] < lmp_ct) & (cap_ct > 0)

    cap_all = k0["pmax"][:, None] * k0["availability"][:, :T]
    P1z = P0z.copy()
    for zi, z in enumerate(zones):
        p0 = P0z[:, zi]
        below_k = ((k0["mc_base"][:, :T] <= p0[None, :]) * cap_all).sum(axis=0)
        lo = np.minimum(p0, a0["mc_base"][:, :T].min(axis=0))
        hi = p0.copy()
        for _ in range(28):
            mid = 0.5 * (lo + hi)
            ok = ((a0["mc_base"][:, :T] <= mid[None, :]) * cap_all).sum(axis=0) >= below_k
            hi = np.where(ok, mid, hi)
            lo = np.where(ok, lo, mid)
        P1z[:, zi] = hi
    p0s = (P0z * W).sum(axis=1)
    p1s = (P1z * W).sum(axis=1)

    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{yr}.parquet")
    ch = ch[ch["pass"] == "P1"]
    model = ch[ch["klass"] == "CT_PEAKER"].sort_values("hour")["mw"].to_numpy()[:T]

    return {
        "year": yr,
        "D1_offer_delta": {
            "rows_moved": int(moved.sum()),
            "rows_total": int(moved.size),
            "cells_moved": {f"{a}|{b}": n for (a, b), n in sorted(cells.items())},
            "pmax_max_abs_delta_mw": _r(float(np.abs(a0["pmax"] - k0["pmax"]).max()), 9),
            "availability_max_abs_delta": _r(
                float(np.abs(a0["availability"] - k0["availability"]).max()), 9
            ),
            "by_band": band_rows,
        },
        "D2_reachability": {
            "keeper_mean_itm_available_mw": _r((cap_ct * itm_k).sum() / T, 1),
            "arm_mean_itm_available_mw": _r((cap_ct * itm_a).sum() / T, 1),
            "keeper_itm_bound_twh": _r((cap_ct * itm_k).sum() / 1e6, 4),
            "arm_itm_bound_twh": _r((cap_ct * itm_a).sum() / 1e6, 4),
            "model_dispatch_twh": _r(model.sum() / 1e6, 4),
        },
        "D3_price_exposure_indicator": {
            "keeper_mean_lmp": _r(p0s.mean(), 3),
            "arm_mean_lmp": _r(p1s.mean(), 3),
            "delta_pct": _r(100.0 * (p1s.mean() / p0s.mean() - 1.0), 2),
            "keeper_p95": _r(np.percentile(p0s, 95), 2),
            "arm_p95": _r(np.percentile(p1s, 95), 2),
            "hours_price_falls": int((p0s - p1s > 0.005).sum()),
            "note": "same-weights merit-order crossing on the LP's own offer stack; an INDICATOR, never the scored C3a",
        },
        "D4_footprint_no_meter_no_residual": {
            "newly_itm_twh": _r(((cap_ct * itm_a).sum() - (cap_ct * itm_k).sum()) / 1e6, 4),
            "newly_itm_mean_mw": _r(((cap_ct * itm_a).sum() - (cap_ct * itm_k).sum()) / T, 1),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--keeper-cache", type=Path, required=True)
    ap.add_argument("--arm-cache", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results/calibration/_nyiso199_ct_band_basis_phase0.json",
    )
    a = ap.parse_args()
    res = {
        "keeper": KEEPER_ID,
        "arm_bands": ARM_BANDS,
        "arm_band_source": "the CT_PEAKER curve's OWN registered phys_* keys "
        "(nyiso_campd_marginal_hr_summary.csv p50s, n=70) — zero values chosen",
        "years": {str(y): year_block(y, a.keeper_cache, a.arm_cache) for y in a.years},
    }
    a.out.write_text(json.dumps(res, indent=2))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
