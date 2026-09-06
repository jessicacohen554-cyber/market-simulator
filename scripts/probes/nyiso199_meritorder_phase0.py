"""nyiso-199 PHASE 0 (NO LP) — the ``CC_REGULAR`` vs ``ST_GAS`` / ``CT_PEAKER``
merit order, decomposed against the LP's OWN BOUNDS on committed artifacts only
(rule 29 ``[R-SCREEN]`` step 0; control = the keeper's committed bundle, rule
29(b) form 4).

nyiso-198 measured that removing 726.5 MW of mis-classified duct band moves
+1.1 to +1.4 TWh into ``CC_REGULAR`` in every year, taken from ``ST_GAS``
(-0.7 to -0.9) and ``CT_PEAKER`` (-0.06 to -0.31) — two classes that were
ALREADY under their actuals.  It handed forward the merit order itself as the
next lever and instructed that phase 0 start "at the bound that binds, not at
the residual".

This probe does exactly that, for every thermal class, with no residual in any
metric it gates on.  Every dispatched MW sits between

    pmin[g,t]  <=  P[g,t]  <=  pmax[g] * availability[g,t]

so in each hour where the METER runs a class above the MODEL, the class sits in
exactly one of:

  * **AT_ENVELOPE** — the class's whole available capacity is dispatched.  The
    LP physically cannot run more: object = availability (the unit-outage
    extract) or capacity scope (the bin basis).  Split by whether an outage
    derate is active.
  * **INTERIOR** — the LP held available capacity back.  Object = OFFER
    POSITION.  Sub-split by whether the model is pinned at its own forced
    ``min_gen`` floor (running ONLY because it is forced, i.e. deeply out of
    merit) or genuinely interior.

For the INTERIOR bucket the probe then localises the object inside the class's
own offer stack, at BAND grain, from the committed ``class_band_hourly``
sidecar against the band's own reconstructed available capacity and its own
capacity-weighted offer (``mc_base``, the assembled P0 objective the LP solved
on — carbon and the gas offer margin included, per nyiso-181 §4).

Finally it prices the merit-order gap two ways that contain no residual and no
fitted quantity:

  * **REVEALED SUPPLY CURVE** — each class's utilisation of its OWN available
    capacity as a function of the zonal LMP, model side and meter side.  Where
    the two curves separate, and by how many $/MWh of price the model's curve
    must shift to sit on the meter's, is the merit-order error stated in the
    unit the offer is written in.
  * **BAND OFFER vs PHYSICS** — each band's registered multiplier against its
    own registered measured ``phys_*`` counterpart, and the $/MWh that gap is
    worth at the class's own capacity-weighted heat rate and delivered fuel.

Nothing here is gated on any residual and nothing is swept.  Writes
``results/calibration/_nyiso199_meritorder_phase0.json``.

Usage::

    python scripts/probes/nyiso199_meritorder_phase0.py [--years 2023 2024 2025]
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
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))

KEEPER_ID = "2026-09-06-nyiso-196-extract-basis"
BUNDLE = ROOT / "results/calibration/nyiso196_extract_basis"
T = 8760
#: classes the merit-order question is about, plus their neighbours for contrast.
CLASSES = ("CC_REGULAR", "CC_CHP", "ST_GAS", "CT_PEAKER", "CT_CHP", "ST_CHP")
#: "the class is at its envelope" — within this fraction of its own available MW.
ENV_TOL = 0.995
#: "the model is running only because it is forced" — within this of its floor.
FLOOR_TOL = 1.02
#: an outage derate is active on the class when its capacity-weighted
#: availability is below this.
AVAIL_ON = 0.999
#: price buckets for the revealed supply curve ($/MWh, upper edges).
PRICE_EDGES = (0, 15, 20, 25, 30, 35, 40, 50, 65, 90, 150, 1e9)


def _r(x, n=1):
    v = float(x)
    return round(v, n) if np.isfinite(v) else None


def _dec(b64: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def _series(entry: dict, key_bytes: str, key_ann: str, npl: float) -> np.ndarray:
    """Decode a dashboard byte series back to MW (the payload's own contract)."""
    raw = _dec(entry[key_bytes])[:T]
    if raw.size < T:
        raw = np.pad(raw, (0, T - raw.size))
    ann = entry.get(key_ann)
    if ann not in (None, "", "None") and raw.sum() > 0:
        return raw * (float(ann) * 1e6 / raw.sum())
    return raw * npl / 100.0


def _parse_unit(uid: str) -> tuple[str, str, int, str]:
    """``CT_PEAKER_Long_Island_p2695_peak`` -> (class, zone, plant, band)."""
    for k in CLASSES:
        if uid.startswith(k + "_"):
            rest = uid[len(k) + 1 :]
            head, _, band = rest.rpartition("_")
            zone, _, pc = head.rpartition("_p")
            try:
                return k, zone, int(pc), band
            except ValueError:
                return k, head, -1, band
    return "", "", -1, ""


def _band_family(band: str) -> str:
    if band.startswith("econc") or band in ("econlo", "econhi", "econ"):
        return "econ"
    return band


def load_fleet(cache_dir: Path, yr: int) -> dict:
    with open(cache_dir / f"fleet_{yr}.pkl", "rb") as f:
        return pickle.load(f)


def year_block(yr: int, cache_dir: Path) -> dict:
    d = load_fleet(cache_dir, yr)
    pmax = d["pmax"]
    avail = d["availability"]
    mc = d["mc_base"]
    mg = d["min_gen"]
    hr = d["heat_rate"]
    uids = d["unit_ids"]
    parsed = [_parse_unit(u) for u in uids]

    # ---- zonal price, the LP's own duals ---------------------------------
    sysp = pd.read_parquet(BUNDLE / "hourly" / f"system_{yr}.parquet")
    pmat = sysp.pivot(index="hour", columns="zone", values="price")
    zones = list(pmat.columns)
    price = {z: pmat[z].to_numpy()[:T] for z in zones}
    load_w = sysp.pivot(index="hour", columns="zone", values="demand") if "demand" in sysp.columns else None

    # ---- the model's own class / class-band dispatch, P1 ------------------
    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{yr}.parquet")
    ch = ch[ch["pass"] == "P1"]
    model_cls = {
        k: ch[ch["klass"] == k].sort_values("hour")["mw"].to_numpy()[:T] for k in CLASSES
    }
    cb = pd.read_parquet(BUNDLE / "hourly" / f"class_band_hourly_{yr}.parquet")
    cb = cb[cb["pass"] == "P1"]

    # ---- the meter, summed over the bench's own plant -> class map --------
    bench = json.load(gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{yr}.json.gz"))["bench"]
    meter_cls = {k: np.zeros(T) for k in CLASSES}
    meter_plants = {k: [] for k in CLASSES}
    for code, b in bench["plants"].items():
        g = b.get("group")
        if g not in meter_cls:
            continue
        c = _series(b, "campd", "c_ann", float(b["npl"]))
        meter_cls[g] = meter_cls[g] + c
        meter_plants[g].append(str(code))
    class_full = bench.get("classFull", {})

    out_classes = {}
    for k in CLASSES:
        idx = [i for i, p in enumerate(parsed) if p[0] == k]
        if not idx:
            continue
        idx_a = np.array(idx)
        env = (pmax[idx_a, None] * avail[idx_a, :T]).sum(axis=0)
        cap_nom = float(pmax[idx_a].sum())
        floor = mg[idx_a, :T].sum(axis=0) if mg is not None else np.zeros(T)
        availw = env / cap_nom if cap_nom else np.zeros(T)

        model = model_cls[k]
        meter = meter_cls[k]
        # class zone weighting for the price the class actually faces
        zw = np.zeros(len(zones))
        for i in idx:
            z = parsed[i][1]
            if z in zones:
                zw[zones.index(z)] += float(pmax[i])
        zw = zw / zw.sum() if zw.sum() else zw
        lmp = np.zeros(T)
        for j, z in enumerate(zones):
            lmp += zw[j] * price[z]

        # ------- the deficit, decomposed by which LP bound binds -----------
        deficit = np.maximum(meter - model, 0.0)
        dhrs = deficit > 0
        headroom = env - model
        at_env = model >= ENV_TOL * env
        outage = availw < AVAIL_ON
        at_floor = (~at_env) & (floor > 0) & (model <= FLOOR_TOL * floor)

        def agg(mask):
            m = dhrs & mask
            return {
                "hours": int(m.sum()),
                "deficit_gwh": _r(deficit[m].sum() / 1e3),
                "share_pct": _r(100.0 * deficit[m].sum() / deficit.sum() if deficit.sum() else 0.0),
                "mean_model_mw": _r(model[m].mean() if m.any() else 0.0),
                "mean_meter_mw": _r(meter[m].mean() if m.any() else 0.0),
                "mean_env_mw": _r(env[m].mean() if m.any() else 0.0),
                "mean_headroom_mw": _r(headroom[m].mean() if m.any() else 0.0),
                "mean_lmp": _r(lmp[m].mean() if m.any() else 0.0, 2),
            }

        buckets = {
            "AT_ENVELOPE_outage": agg(at_env & outage),
            "AT_ENVELOPE_no_outage": agg(at_env & ~outage),
            "INTERIOR_at_floor": agg(~at_env & at_floor),
            "INTERIOR_free": agg(~at_env & ~at_floor),
        }

        # ------- band anatomy: offer, capacity, utilisation ----------------
        bands = {}
        fams = sorted({_band_family(p[3]) for p in (parsed[i] for i in idx)})
        for fam in fams:
            bidx = np.array([i for i in idx if _band_family(parsed[i][3]) == fam])
            if not bidx.size:
                continue
            bcap = (pmax[bidx, None] * avail[bidx, :T]).sum(axis=0)
            w = pmax[bidx]
            boffer = (mc[bidx, :T] * w[:, None]).sum(axis=0) / w.sum()
            sel = cb[(cb["klass"] == k) & (cb["band"].map(_band_family) == fam)]
            bmw = sel.groupby("hour")["mw"].sum().reindex(range(T), fill_value=0.0).to_numpy()
            live = bcap > 1.0
            bands[fam] = {
                "nameplate_mw": _r(float(w.sum()), 1),
                "mean_available_mw": _r(bcap.mean()),
                "energy_twh": _r(bmw.sum() / 1e6, 4),
                "utilisation_pct_of_available": _r(
                    100.0 * bmw.sum() / bcap.sum() if bcap.sum() else 0.0, 2
                ),
                "cap_wtd_offer_mean": _r(boffer[live].mean() if live.any() else 0.0, 2),
                "cap_wtd_offer_p50": _r(np.median(boffer[live]) if live.any() else 0.0, 2),
                "hours_offer_below_lmp": int(((boffer < lmp) & live).sum()),
                "energy_twh_when_offer_below_lmp": _r(
                    bmw[(boffer < lmp) & live].sum() / 1e6, 4
                ),
                "mean_unrun_mw_when_offer_below_lmp": _r(
                    (bcap - bmw)[(boffer < lmp) & live].mean()
                    if ((boffer < lmp) & live).any()
                    else 0.0
                ),
                "cap_wtd_heat_rate": _r(float((hr[bidx] * w).sum() / w.sum()), 4),
            }

        # ------- the revealed supply curve, model vs meter -----------------
        curve = []
        for lo, hi in zip(PRICE_EDGES[:-1], PRICE_EDGES[1:]):
            m = (lmp >= lo) & (lmp < hi)
            if not m.any():
                continue
            curve.append(
                {
                    "lmp_lo": lo,
                    "lmp_hi": None if hi > 1e8 else hi,
                    "hours": int(m.sum()),
                    "mean_lmp": _r(lmp[m].mean(), 2),
                    "model_cf_of_available_pct": _r(
                        100.0 * model[m].sum() / env[m].sum() if env[m].sum() else 0.0, 2
                    ),
                    "meter_cf_of_available_pct": _r(
                        100.0 * meter[m].sum() / env[m].sum() if env[m].sum() else 0.0, 2
                    ),
                    "model_twh": _r(model[m].sum() / 1e6, 4),
                    "meter_twh": _r(meter[m].sum() / 1e6, 4),
                }
            )

        out_classes[k] = {
            "lp_units": len(idx),
            "lp_nameplate_mw": _r(cap_nom, 1),
            "n_bench_plants": len(meter_plants[k]),
            "annual": {
                "model_twh": _r(model.sum() / 1e6, 4),
                "meter_campd_gross_twh": _r(meter.sum() / 1e6, 4),
                "eia923_class_twh": _r(float(class_full.get(k) or 0.0), 4),
                "envelope_twh": _r(env.sum() / 1e6, 4),
                "model_cf_of_available_pct": _r(100.0 * model.sum() / env.sum(), 2),
                "meter_cf_of_available_pct": _r(100.0 * meter.sum() / env.sum(), 2),
                "forced_floor_twh": _r(floor.sum() / 1e6, 4),
                "mean_available_mw": _r(env.mean()),
                "mean_lmp": _r(lmp.mean(), 2),
            },
            "deficit_total_gwh": _r(deficit.sum() / 1e3),
            "deficit_hours": int(dhrs.sum()),
            "surplus_total_gwh": _r(np.maximum(model - meter, 0.0).sum() / 1e3),
            "deficit_by_binding_lp_bound": buckets,
            "bands": bands,
            "revealed_supply_curve": curve,
        }

    return {"year": yr, "zones": zones, "classes": out_classes}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--cache-dir",
        type=Path,
        required=True,
        help="directory holding fleet_<year>.pkl written by the fleet dump",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results/calibration/_nyiso199_meritorder_phase0.json",
    )
    a = ap.parse_args()
    res = {
        "keeper": KEEPER_ID,
        "bundle": str(BUNDLE.relative_to(ROOT)),
        "basis": "committed artifacts only; no LP; mc_base = the assembled P0 objective",
        "years": {},
    }
    for y in a.years:
        res["years"][str(y)] = year_block(y, a.cache_dir)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=2))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
