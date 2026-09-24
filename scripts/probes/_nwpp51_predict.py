"""nwpp-51 phase 0: zero-LP prediction for arming ``eia860_vintage_tracks_solve_year`` on NWPP.

Reads the keeper's committed hourly sidecars (``results/calibration/
nwpp49_ror_span/hourly/``), its committed run payload (per-plant annual
dispatch), and the flag-off / flag-on fleet-only rebuilds of
``_nwpp51_vintage_census.py``. No LP.

THE PREDICTION, per year, is a two-sided bracket on the coal the arm adds:

* ``hi`` (coal displaces only gas): each touched plant's tranches are
  dispatched as PRICE-TAKERS against the keeper's own P1 zonal price — a
  tranche runs at ``availability x pmax`` in every hour its offer
  (``mc_base``) is at or below the price, or its ``min_gen`` floor binds.
  ``delta = PT(on) - PT(off)`` over the touched plants' COAL tranches. It
  holds price fixed, so it is an UPPER bound on the econ-band increment.
* ``lo`` (coal displaces coal first): only the flat-block increment
  (tranches offered at or below the ZONE's hourly price floor of the flat
  band, i.e. mustrun / committed) is added, and in every hour it first
  displaces the keeper's own coal econ/peak band output (all coal classes,
  ``class_band_hourly``) before any gas.

Gas displacement for the C1 margin: fixed demand, fixed measured interchange
and fixed monthly hydro budgets mean the added coal energy leaves gas
(or curtails VRE). The WORST C1 case books all of ``hi`` against
CC_REGULAR; that is what the CC_REGULAR margin is tested against.

Also reported (item 3 of the charter): how the flat block would change if
Jim Bridger had a measured COAL tranche row instead of the 45/5/2 default
(approximate — CAMPD gross over the 2023 coal-unit nameplate; the real
derive is ``scripts/data/derive_thermal_tranches.py``).

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwpp51_predict.py
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.probes._nwpp51_vintage_census import _build  # noqa: E402

BUNDLE = Path("results/calibration/nwpp49_ror_span")
RUN_ID = "2026-09-24-nwpp-49-ror-split"
EIA930 = Path("results/calibration/_shared/NWPP/eia930-e539ed483b64.parquet")
PLANTS = (8066, 8224, 6076)  # Jim Bridger, North Valmy, Colstrip (census)
COAL_KLASS = ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE", "COAL")
N = 8760


def _payload() -> dict:
    """Decode the keeper's committed run payload."""
    t = Path(f"frontend/data/backcast/runs/{RUN_ID}.js").read_text()
    b = re.search(r'="([A-Za-z0-9+/=]+)"', t).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b)))


def _intra(x: np.ndarray) -> np.ndarray:
    """Within-day deviation from the daily mean."""
    x = x[: len(x) // 24 * 24].reshape(-1, 24)
    return (x - x.mean(1, keepdims=True)).ravel()


def _r(a, b) -> float:
    """Pearson r."""
    return float(np.corrcoef(a, b)[0, 1])


def _pt(built: dict, prices: dict[str, np.ndarray]) -> pd.DataFrame:
    """Price-taker hourly MW per touched-plant tranche (rows = units, cols = hours)."""
    fa, fleet = built["fleet_arrays"], built["fleet"]
    zones = list(built["config"].zones) if getattr(built["config"], "zones", None) else None
    codes = np.asarray(fa.plant_code).astype(int)
    idx = [i for i in range(len(codes)) if codes[i] in PLANTS]
    avail = np.asarray(fa.availability, float)
    mc = np.asarray(built["mc_base"], float)
    mg = None if fa.min_gen is None else np.asarray(fa.min_gen, float)
    rows = {}
    for i in idx:
        g = fleet[i]
        z = str(getattr(g, "zone", ""))
        if z not in prices and zones is not None:
            z = zones[int(np.asarray(fa.zone_idx)[i])]
        p = prices[z]
        cap = avail[i] * float(np.asarray(fa.pmax)[i]) if avail.ndim == 2 else np.full(N, avail[i] * fa.pmax[i])
        m = mc[i] if mc.ndim == 2 else np.full(N, mc[i])
        on = m <= p
        out = np.where(on, cap, 0.0)
        if mg is not None:
            floor = mg[i] if mg.ndim == 2 else np.full(N, mg[i])
            out = np.maximum(out, np.minimum(floor, cap))
        rows[str(g.unit_id)] = dict(plant=int(codes[i]), klass=str(getattr(g, "plant_group", "")),
                                    flat=bool(np.median(m) < 10.0), mw=out[:N])
    return rows


def predict(year: int, payload: dict, e930: pd.DataFrame) -> dict:
    """Bracket the arm's coal and gas movement, and coal r, for one year."""
    sy = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    sy = sy[sy["pass"] == "P1"]
    prices = {z: g.sort_values("hour").price.to_numpy(float)[:N] for z, g in sy.groupby("zone")}
    off, on = _pt(_build(year, False), prices), _pt(_build(year, True), prices)

    def tot(rows, pred):
        v = [r["mw"] for r in rows.values() if pred(r)]
        return np.sum(v, axis=0) if v else np.zeros(N)

    def coal_of(plants, flat_only=False):
        def pred(r):
            return r["klass"] == "COAL" and r["plant"] in plants and (r["flat"] or not flat_only)
        return pred

    by_plant = {p: float((tot(on, coal_of({p})) - tot(off, coal_of({p}))).sum() / 1e6) for p in PLANTS}
    pt_off_plant = {p: float(tot(off, coal_of({p})).sum() / 1e6) for p in PLANTS}
    band = pd.read_parquet(BUNDLE / "hourly" / f"class_band_hourly_{year}.parquet")
    band = band[(band["pass"] == "P1") & band.klass.isin(COAL_KLASS) & band.band.isin(["econlo", "econhi", "peak"])]
    coal_econ = band.groupby("hour").mw.sum().reindex(range(N), fill_value=0).to_numpy(float)
    # The two units that CHANGE FUEL (JB, Valmy) add capacity; Colstrip only
    # re-prices its committed band (the vintage dirs' missing utility sheet —
    # see the FINDING). Variant "as_is" carries Colstrip's price-taker loss;
    # variant "repaired" (utility sheet restored => Colstrip unchanged) does not.
    fuel_switch = {8066, 8224}
    d_add_hi = tot(on, coal_of(fuel_switch)) - tot(off, coal_of(fuel_switch))
    d_add_flat = tot(on, coal_of(fuel_switch, True)) - tot(off, coal_of(fuel_switch, True))
    d_add_lo = np.maximum(0.0, d_add_flat - coal_econ)
    d_colstrip = tot(on, coal_of({6076})) - tot(off, coal_of({6076}))
    variants = {"repaired": (d_add_lo, d_add_hi), "as_is": (d_add_lo + d_colstrip, d_add_hi + d_colstrip)}
    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    cm = ch[ch.klass.isin(COAL_KLASS)].groupby("hour").mw.sum().reindex(range(N), fill_value=0).to_numpy(float)
    ca = e930[(e930.year == year) & (e930.series == "coal")].sort_values("hour").mw.to_numpy(float)[:N]
    pl = payload["years"][str(year)]["plants"]
    keeper_plant = {k: v.get("m_ann") for k, v in pl.items() if k.split(":")[0] in {str(p) for p in PLANTS}}
    st_gas_lost = sum(v for k, v in keeper_plant.items() if k.endswith("ST_GAS") and v)
    out = {
        "year": year,
        "keeper_plant_twh": keeper_plant,
        "pricetaker_off_coal_twh": {str(k): round(v, 3) for k, v in pt_off_plant.items()},
        "d_coal_twh_by_plant_pricetaker": {str(k): round(v, 3) for k, v in by_plant.items()},
        "st_gas_keeper_twh_removed": round(float(st_gas_lost), 3),
        "coal_r_keeper": round(_r(cm, ca), 3), "coal_r_intra_keeper": round(_r(_intra(cm), _intra(ca)), 3),
    }
    for name, (lo, hi) in variants.items():
        out[name] = {
            "d_coal_twh_lo": round(float(lo.sum() / 1e6), 3),
            "d_coal_twh_hi": round(float(hi.sum() / 1e6), 3),
            "coal_r_lo": round(_r(cm + lo, ca), 3), "coal_r_intra_lo": round(_r(_intra(cm + lo), _intra(ca)), 3),
            "coal_r_hi": round(_r(cm + hi, ca), 3), "coal_r_intra_hi": round(_r(_intra(cm + hi), _intra(ca)), 3),
        }
    return out


def jb_measured_row(year: int = 2023) -> dict:
    """Approximate measured tranche shares for Jim Bridger's 4 coal units (CAMPD gross)."""
    u = pd.read_parquet(Path(f"data/raw/campd-unit-level/WY_{year}.parquet"))
    u = u[u.facilityId.astype(int) == 8066].copy()
    u["h"] = ((pd.to_datetime(u.date) + pd.to_timedelta(u.hour, "h") - pd.Timestamp(f"{year}-01-01"))
              / pd.Timedelta("1h")).astype(int)
    mw = u.groupby("h").grossLoad.sum().reindex(range(N), fill_value=0).to_numpy(float)
    cf = mw / 2119.0
    on = cf[cf > 0]
    return {"year": year, "campd_gross_twh": round(mw.sum() / 1e6, 3),
            "mustrun_pct_allhours_p5": round(100 * float(np.percentile(cf, 5)), 1),
            "committed_pct_online_p5": round(100 * float(np.percentile(on, 5)), 1),
            "default_pct": {"mustrun": 45.0, "committed": 5.0, "peaking": 2.0}}


def main() -> None:
    """Print and write the prediction record."""
    payload = _payload()
    e930 = pd.read_parquet(EIA930)
    rec = {"predictions": [predict(y, payload, e930) for y in (2023, 2024)],
           "jb_measured_row_approx": [jb_measured_row(y) for y in (2023,)]}
    for p in rec["predictions"]:
        print(json.dumps(p, indent=1))
    print(json.dumps(rec["jb_measured_row_approx"], indent=1))
    Path("results/calibration/_nwpp51_predict.json").write_text(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
