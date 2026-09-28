"""R-CAISO-10 Object 2 (ZERO LP): who sets the model's SP15_rest price, 2021 vs 2023-25.

R-CAISO-9 found the 2021 evening (h17-22, PALOVRDE-printed hours) SP15_rest price at
$68.9 against measured DAM TH_SP15 $77.8, with DSW imports (hub input $79.1) priced
out. This probe names the price-setter per hour from the keeper legs' per-unit P1
hourly (``hourly/unit_hourly_<y>.parquet``): a unit is MARGINAL in an hour when it is
partially loaded (``ON < mw < cap - ON``) with ``|red_cost| <= TOL`` and sits in a
zone whose price equals SP15_rest's within ``TOL`` (the same uncongested pocket).
Ties split the hour equally. An hour with no such unit is ``none_thermal`` -- set by
storage (whose opportunity cost is not in the unit file), a transmission limit, or
a unit at a bound.

Also reports the measured OASIS DAM TH_SP15 in the same hours where available.

Inputs: legs extracted locally from their shard commits (gitignored; provenance in
RESULT-r-caiso-9 §Retrievability). Writes
``results/calibration/_rcaiso10/object2_price_setter.json``.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso10_object2_price_setter.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

LEG = "results/calibration/rcaiso9_A_{y}"
HUBS = Path("data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet")
DAM = "data/raw/lmp-data/CAISO/CAISO_dam_hourly_{y}.csv"
OUT = Path("results/calibration/_rcaiso10/object2_price_setter.json")
T = 8760
HOD = np.arange(T) % 24
ON = 0.1  # MW
TOL = 0.05  # $/MWh
WINDOWS = {"h0_6": (0, 6), "h8_16": (8, 16), "h17_22": (17, 22)}


def _dam_sp15(y: int) -> np.ndarray | None:
    """Measured OASIS DAM TH_SP15 on the model's fixed-PST hour-of-year clock."""
    p = Path(DAM.format(y=y))
    if not p.exists():
        return None
    d = pd.read_csv(p)
    d = d[d.node == "TH_SP15_GEN-APND"]
    t = pd.to_datetime(d.interval_start_gmt).dt.tz_convert("Etc/GMT+8")
    h = ((t - pd.Timestamp(f"{y}-01-01", tz="Etc/GMT+8")).dt.total_seconds() // 3600).astype(int)
    out = np.full(T, np.nan)
    k = (h >= 0) & (h < T)
    out[h[k].to_numpy()] = d.LMP.to_numpy()[k.to_numpy()]
    return out


def setter(y: int) -> dict:
    """Name the SP15_rest price-setter by class for each window of year ``y``."""
    leg = Path(LEG.format(y=y))
    s = pd.read_parquet(leg / f"hourly/system_{y}.parquet", columns=["zone", "hour", "price"])
    zp = s.pivot(index="hour", columns="zone", values="price").reindex(range(T))
    sp = zp["SP15_rest"].to_numpy()
    same = {z: np.abs(zp[z].to_numpy() - sp) <= TOL for z in zp.columns}
    u = pd.read_parquet(
        leg / f"hourly/unit_hourly_{y}.parquet",
        columns=["unit_id", "plant_group", "fuel", "zone", "hour", "mw", "cap_mw", "red_cost"],
    )
    u = u[(u.mw > ON) & (u.mw < u.cap_mw - ON) & (u.red_cost.abs() <= TOL)]
    u = u[[bool(same[z][h]) for z, h in zip(u.zone.astype(str), u.hour)]]
    u["cls"] = np.where(
        u.fuel.astype(str) == "import",
        "import:" + u.zone.astype(str),
        u.plant_group.astype(str).replace("", "other"),
    )
    w = u.groupby("hour").cls.transform("size")
    u["wt"] = 1.0 / w
    by_hour_cls = u.groupby(["hour", "cls"]).wt.sum().unstack(fill_value=0.0).reindex(range(T), fill_value=0.0)
    none = by_hour_cls.sum(axis=1).to_numpy() == 0

    hubs = pd.read_parquet(HUBS)
    pv = hubs[(hubs.year == y) & (hubs.hub == "PALOVRDE")].set_index("hour").price.reindex(range(T)).to_numpy()
    printed = ~np.isnan(pv)
    dam = _dam_sp15(y)
    out = {}
    for nm, (a, b) in WINDOWS.items():
        msk = (HOD >= a) & (HOD <= b) & printed
        n = int(msk.sum())
        if not n:
            continue
        shares = (by_hour_cls[msk].sum(axis=0) / n).sort_values(ascending=False)
        out[nm] = {
            "hours": n,
            "model_sp15_rest": round(float(np.nanmean(sp[msk])), 1),
            "measured_dam_sp15": round(float(np.nanmean(dam[msk])), 1) if dam is not None and (~np.isnan(dam[msk])).any() else None,
            "hub_palovrde": round(float(np.nanmean(pv[msk])), 1),
            "setter_share": {k: round(float(v), 3) for k, v in shares.items() if v >= 0.01},
            "none_thermal_share": round(float(none[msk].mean()), 3),
            "model_price_when_none": round(float(np.nanmean(sp[msk & none])), 1) if (msk & none).any() else None,
        }
    return out


def main() -> None:
    """Run for 2021 and the scored 2022-25 legs; write JSON."""
    res = {"tol": TOL, "on_mw": ON, "hours": "PALOVRDE-printed only", "years": {}}
    for y in (2021, 2022, 2023, 2024, 2025):
        res["years"][str(y)] = setter(y)
        print(y, json.dumps(res["years"][str(y)].get("h17_22")))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
