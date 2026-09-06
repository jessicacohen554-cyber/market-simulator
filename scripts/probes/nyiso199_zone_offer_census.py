"""nyiso-199 PHASE 0b (NO LP) — the CT_PEAKER / ST_GAS deficit split by ZONE and
by DELIVERED FUEL, on committed artifacts only.

Phase 0a (``nyiso199_meritorder_phase0.py``) killed the availability and floor
limbs: 100 % of ``CT_PEAKER``'s deficit and 88 % of ``ST_GAS``'s sits INTERIOR,
so the object is offer position.  The offer decomposition then showed the one
input that separates ``CT_PEAKER`` from every other gas class: its delivered
fuel is **$4.35-4.52/MMBtu against $2.04-2.47 for CC / ST_GAS / CT_CHP**, the
``nyiso_downstate_ct_gas_basis`` LDC non-firm transport re-grounding applied to
109 downstate units.

This probe asks the discriminating question, with no residual in it: **is the
deficit concentrated where the premium is applied?**  If the NYC / Long Island
CT rows carry the deficit and the upstate rows (which pay the hub price) do
not, the premium is load-bearing for the merit order; if the deficit is
uniform across zones, the premium is not the object and the class's band
position is.

It reports, per (class, zone): the LP's own delivered fuel, offered and
effective heat rate, capacity-weighted offer, the model's CF of its own
available capacity, the meter's CF on the same denominator, and the deficit.
Nothing is gated on a residual.

Writes ``results/calibration/_nyiso199_zone_offer_census.json``.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts"):
    sys.path.insert(0, str(p))

KEEPER_ID = "2026-09-06-nyiso-196-extract-basis"
BUNDLE = ROOT / "results/calibration/nyiso196_extract_basis"
T = 8760
CLASSES = ("CC_REGULAR", "CC_CHP", "ST_GAS", "CT_PEAKER", "CT_CHP", "ST_CHP")
#: measured RGGI allowance price the keeper solved on (state_carbon_pricing).
RGGI = {2023: 13.49, 2024: 20.71, 2025: 22.09}


def _r(x, n=2):
    v = float(x)
    return round(v, n) if np.isfinite(v) else None


def _dec(b64: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def _series(entry: dict, kb: str, ka: str, npl: float) -> np.ndarray:
    raw = _dec(entry[kb])[:T]
    if raw.size < T:
        raw = np.pad(raw, (0, T - raw.size))
    ann = entry.get(ka)
    if ann not in (None, "", "None") and raw.sum() > 0:
        return raw * (float(ann) * 1e6 / raw.sum())
    return raw * npl / 100.0


def _parse(uid: str):
    for k in CLASSES:
        if uid.startswith(k + "_"):
            rest = uid[len(k) + 1 :]
            head, _, band = rest.rpartition("_")
            zone, _, pc = head.rpartition("_p")
            return k, zone, pc, band
    return "", "", "", ""


def year_block(yr: int, cache: Path) -> dict:
    with open(cache / f"fleet_{yr}.pkl", "rb") as f:
        d = pickle.load(f)
    mc, fp, hr = d["mc_base"], d["fuel_prices"], d["heat_rate"]
    vom, er, pmax, av = d["vom"], d["emission_rate"], d["pmax"], d["availability"]
    P = [_parse(u) for u in d["unit_ids"]]
    carb = RGGI[yr]

    sysp = pd.read_parquet(BUNDLE / "hourly" / f"system_{yr}.parquet")
    price = sysp.pivot(index="hour", columns="zone", values="price")

    bench = json.load(gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{yr}.json.gz"))["bench"]
    # meter, per (class, zone), from the bench's own plant -> (group, zone) map
    meter = {}
    for code, b in bench["plants"].items():
        key = (b.get("group"), b.get("zone"))
        if key[0] not in CLASSES:
            continue
        c = _series(b, "campd", "c_ann", float(b["npl"]))
        meter[key] = meter.get(key, np.zeros(T)) + c

    # the model has no per-(class, zone) sidecar; the class total is
    # apportioned by each zone's own share of the class's dispatchable
    # in-the-money capacity -- stated as an APPORTIONMENT, never a measurement.
    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{yr}.parquet")
    ch = ch[ch["pass"] == "P1"]
    model_cls = {
        k: ch[ch["klass"] == k].sort_values("hour")["mw"].to_numpy()[:T] for k in CLASSES
    }

    rows = []
    for k in CLASSES:
        for z in sorted({p[1] for p in P if p[0] == k}):
            idx = np.array([i for i, p in enumerate(P) if p[0] == k and p[1] == z])
            if not idx.size:
                continue
            live = av[idx, :T] > 0
            w = pmax[idx][:, None] * live
            tw = w.sum()
            if tw == 0:
                continue
            envz = (pmax[idx][:, None] * av[idx, :T]).sum(axis=0)
            fuel = float((fp[idx, :T] * w).sum() / tw)
            offer = float((mc[idx, :T] * w).sum() / tw)
            cv = float((er[idx][:, None] * carb * w).sum() / tw)
            vv = float((vom[idx][:, None] * w).sum() / tw)
            offhr = float((hr[idx][:, None] * w).sum() / tw)
            lmp = price[z].to_numpy()[:T] if z in price.columns else np.zeros(T)
            mt = meter.get((k, z))
            rows.append(
                {
                    "class": k,
                    "zone": z,
                    "lp_units": int(idx.size),
                    "nameplate_mw": _r(float(pmax[idx].sum()), 1),
                    "mean_available_mw": _r(envz.mean(), 1),
                    "delivered_fuel_usd_mmbtu": _r(fuel, 3),
                    "offered_heat_rate": _r(offhr, 3),
                    "effective_heat_rate": _r((offer - vv - cv) / fuel if fuel else 0.0, 3),
                    "cap_wtd_offer_usd_mwh": _r(offer),
                    "carbon_usd_mwh": _r(cv),
                    "vom_usd_mwh": _r(vv),
                    "mean_zonal_lmp": _r(lmp.mean()),
                    "hours_offer_below_lmp": 0,
                    "envelope_twh": _r(envz.sum() / 1e6, 4),
                    "meter_twh": _r(mt.sum() / 1e6, 4) if mt is not None else None,
                    "meter_cf_of_lp_available_pct": (
                        _r(100.0 * mt.sum() / envz.sum(), 2)
                        if mt is not None and envz.sum()
                        else None
                    ),
                }
            )
    # per-hour share of the class's offer that is in the money, per zone
    for r in rows:
        k, z = r["class"], r["zone"]
        idx = np.array([i for i, p in enumerate(P) if p[0] == k and p[1] == z])
        live = av[idx, :T] > 0
        w = pmax[idx][:, None] * live
        off_h = (mc[idx, :T] * w).sum(axis=0) / np.maximum(w.sum(axis=0), 1e-9)
        lmp = price[z].to_numpy()[:T] if z in price.columns else np.zeros(T)
        ok = (w.sum(axis=0) > 0) & (off_h < lmp)
        r["hours_offer_below_lmp"] = int(ok.sum())
        r["hours_available"] = int((w.sum(axis=0) > 0).sum())

    return {
        "year": yr,
        "class_total_model_twh": {k: _r(model_cls[k].sum() / 1e6, 4) for k in CLASSES},
        "rows": rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--cache-dir", type=Path, required=True)
    ap.add_argument(
        "--out", type=Path, default=ROOT / "results/calibration/_nyiso199_zone_offer_census.json"
    )
    a = ap.parse_args()
    res = {"keeper": KEEPER_ID, "years": {}}
    for y in a.years:
        res["years"][str(y)] = year_block(y, a.cache_dir)
    a.out.write_text(json.dumps(res, indent=2))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
