"""UC-BANDS-ERCOT phase 1a: re-price 2019 with the SCED bands at fixed dispatch (zero LP).

This is a first-order reading, not a solve. It keeps each hour's marginal units
as the bundle records them (``unit_marginal_2019.parquet``) and changes their
offer by the band ratio. The resulting price change flows through to the
load-weighted mean (the C3a basis).

Assumptions (each one biases the result and is stated in the RESULT):

* **Δ offer.** For a marginal gas tranche of a re-banded class,
  ``Δmc = mc · (m_new / m_old − 1)``. ``m`` is the tranche's band multiplier.
  For an ``econcNN`` slice it is read off the registered ramp geometry, using
  ``offer_curves._econ_curve_steps`` with the keeper's smoothing (n=6, mid=0.35,
  top-refine on). The whole offer is scaled, so VOM and every additive P1
  adjuster (start markup, ``cc_committed_offer_margin``, surfaces) are scaled
  too. In 2019 the delivered gas sits near the margin anchor, so the
  ``gas_offer_net_revenue_margin`` form is close to the multiplier form.
* **Zone price.** A zone-hour moves by the mean Δmc of its own marginal units.
  A zone with none takes the hour's mean over all marginal units. That treats
  the network as uncongested for those zones.
* **No re-dispatch.** The merit order is held fixed. A band that falls would in
  reality pull in units that were not marginal, and a band that rises would push
  marginal units out. The reading is linear in the band change and grows less
  reliable as the change grows.

Usage: python reprice_2019.py <root holding the extracted uc bundle> <artifact.json> <out.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "src"))
from market_sim.data.offer_curves import _econ_curve_steps  # noqa: E402

ROOT, ART, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
BUNDLES = {
    "keeper": REPO / "results/calibration/closeout_ercot_l1_span",
    "uc": Path(ROOT) / "results/calibration/ucmilp_fix5_ercot_2019",
}
art = json.load(open(ART))
NEW = art["offer_curve_by_group"]
VARIANT_CT_COMMITTED = art["variants"]["CT_PEAKER"]["committed"]


def band_of(suffix: str) -> str | None:
    """Offer band a tranche suffix prices on (None: not re-banded)."""
    if suffix.startswith("committed"):
        return "committed"
    if suffix.startswith("econ"):
        return "econ"
    if suffix.startswith("peak"):
        return "peak"
    return None


def slice_pos(k: int, n_slices: int, sc: dict) -> float:
    """Fraction f of the econ_low→econ_high rise at slice ``k`` (registered geometry)."""
    n = int(sc["offer_curve_smoothing_n"])
    top = n_slices == 2 * n - 1
    steps = _econ_curve_steps(
        1.0,
        0.0,
        1.0,
        1.0,
        n,
        float(sc["offer_curve_smoothing_exp"]),
        sc.get("offer_curve_smoothing_mid"),
        top_refine=top,
    )
    return float(steps[min(k, len(steps) - 1)][2])


def mult(bands: dict, band: str, f: float) -> float:
    """Tranche multiplier for ``band`` (econ at ramp fraction ``f``)."""
    if band == "econ":
        return bands["econ_low"] + (bands["econ_high"] - bands["econ_low"]) * f
    return bands[band]


def reprice(name: str, bdir: Path, ct_committed: bool) -> dict:
    """Fixed-dispatch re-price of one bundle's 2019 P1."""
    rc = (
        json.load(open(bdir / "run_config_2019.json"))
        if (bdir / "run_config_2019.json").exists()
        else json.load(open(bdir / "run_config.json"))
    )
    sc = rc["scenario_config"]
    old = sc["offer_curve_by_group"]
    new = {g: {**old[g], **NEW[g]} for g in NEW}
    if ct_committed:
        new["CT_PEAKER"]["committed"] = VARIANT_CT_COMMITTED
    u = pd.read_parquet(
        bdir / "hourly/unit_marginal_2019.parquet",
        columns=["unit_id", "plant_group", "zone", "hour", "mc", "marginal"],
    )
    ids = u["unit_id"].astype(str)
    u = u.assign(
        pg=u["plant_group"].astype(str),
        zone=u["zone"].astype(str),
        sfx=ids.str.extract(r"_p\d+_(\w+)$")[0],
        plant=ids.str.extract(r"_p(\d+)_")[0],
    )
    nsl = u[u.sfx.str.startswith("econc", na=False)].groupby("plant").unit_id.nunique()
    m = u[u.marginal == 1].copy()
    ratio = np.ones(len(m))
    bandcol = np.full(len(m), "none", dtype=object)
    for i, (pg, sfx, plant) in enumerate(zip(m.pg, m.sfx, m.plant)):
        if pg not in new or not isinstance(sfx, str):
            continue
        b = band_of(sfx)
        if b is None:
            continue
        f = (
            slice_pos(int(sfx[5:7]), int(nsl.get(plant, 11)), sc)
            if sfx.startswith("econc")
            else 0.0
        )
        mo = mult(old[pg], b, f)
        if mo > 0:
            ratio[i] = mult(new[pg], b, f) / mo
            bandcol[i] = f"{pg}/{b}"
    m["dmc"] = m.mc.to_numpy(float) * (ratio - 1.0)
    s = pd.read_parquet(
        bdir / "hourly/system_2019.parquet",
        columns=["pass", "zone", "hour", "price", "demand"],
    )
    s = s[s["pass"] == "P1"].copy()
    s["zone"] = s["zone"].astype(str)
    zone_d = m.groupby(["hour", "zone"]).dmc.mean()
    hour_d = m.groupby("hour").dmc.mean()
    s = s.join(zone_d.rename("dz"), on=["hour", "zone"]).join(
        hour_d.rename("dh"), on="hour"
    )
    s["dp"] = s.dz.fillna(s.dh).fillna(0.0)
    base = float((s.price * s.demand).sum() / s.demand.sum())
    newp = float(((s.price + s.dp) * s.demand).sum() / s.demand.sum())
    by_cls = m.assign(w=1).groupby("pg").agg(n=("w", "size"), dmc=("dmc", "mean"))
    # Additive attribution: a zone-hour's dp is the mean dmc of the rows feeding
    # it, so each row carries dmc / n_rows x that zone's demand share.
    m["band"] = bandcol
    m["nz"] = m.groupby(["hour", "zone"]).dmc.transform("size")
    m["nh"] = m.groupby("hour").dmc.transform("size")
    dem = s.groupby(["hour", "zone"]).demand.sum()
    own = m.join(dem.rename("dz_dem"), on=["hour", "zone"])
    own_c = own.dmc / own.nz * own.dz_dem.fillna(0.0)
    orphan = s[s.dz.isna()].groupby("hour").demand.sum()
    orph_c = m.dmc / m.nh * m.hour.map(orphan).fillna(0.0).to_numpy()
    m["contrib"] = (own_c.to_numpy() + orph_c.to_numpy()) / s.demand.sum()
    by_band = m.groupby("band").agg(rows=("dmc", "size"), contrib=("contrib", "sum"))
    return {
        "lw_mean_base": base,
        "lw_mean_repriced": newp,
        "delta_usd_mwh": newp - base,
        "c3a_vs_actual_46.55": {
            "base_pct": 100 * (base / 46.55 - 1),
            "repriced_pct": 100 * (newp / 46.55 - 1),
        },
        "contrib_by_class_band": by_band.round(4).to_dict(orient="index"),
        "marginal_unit_hours_by_class": by_cls.round(3).to_dict(orient="index"),
        "bands_old": {
            g: {k: old[g][k] for k in ("committed", "econ_low", "econ_high", "peak")}
            for g in NEW
        },
        "bands_new": {
            g: {k: new[g][k] for k in ("committed", "econ_low", "econ_high", "peak")}
            for g in NEW
        },
    }


out = {}
for nm, bd in BUNDLES.items():
    out[nm] = reprice(nm, bd, ct_committed=False)
    out[nm + "_ct_committed_variant"] = reprice(nm, bd, ct_committed=True)
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(
    json.dumps(
        {
            k: {
                kk: v[kk]
                for kk in ("lw_mean_base", "lw_mean_repriced", "delta_usd_mwh")
            }
            for k, v in out.items()
        },
        indent=1,
    )
)
