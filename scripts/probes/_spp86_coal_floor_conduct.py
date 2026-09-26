"""SPP-86 (zero LP): where the keeper's coal must-run floor sits while the plant's meter is dark.

Record: ``docs/handoffs/FINDING-spp-86-coal-floor-conduct-2026-09-26.md``.

Rebuilds the keeper ``results/calibration/spp85_arm_span`` fleet ``fleet_only`` for each year and,
per coal plant and hour, reads (a) the ``coal_mustrun`` floor (``min_gen`` on rows whose
``min_gen_mechanism`` is ``MECH_COAL_MUSTRUN``), (b) the plant's LP-available MW
(``pmax x availability``), (c) the plant's CAMPD gross load, and (d) the share of the plant's
units the keeper's own outage extracts (std + short, both ``-netloadmask-``) place in a full-stop
window. Each floored hour at a dark meter is classed:

* ``full_window`` -- the extracts put every unit of the plant out (share >= 0.999), yet a floor
  survives: the residual availability the share-denominator leaves behind;
* ``part_window`` -- some units out;
* ``no_window`` -- no extract window covers the hour.

A plant whose CAMPD rows carry no gross load at all (River Valley 10671 reports ``opTime`` with a
null ``grossLoad`` in every hour) is UNMETERED and skipped, as the D-4 rider skips it -- a null
series is a metering gap, not conduct.

Solves nothing. Usage: ``python scripts/probes/_spp86_coal_floor_conduct.py --out <json>``
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

BUNDLE = REPO_ROOT / "results/calibration/spp85_arm_span"
RAW = REPO_ROOT / "data/raw"
EXTRACTS = ("campd-unit-outages-netloadmask-SPP.csv", "campd-unit-outages-short-netloadmask-SPP.csv")
STATES = ("KS", "OK", "NE", "MO", "TX", "NM", "AR", "LA", "IA", "SD", "ND", "MN", "WY", "MT", "CO")
DARK_MW = 1.0  # a plant hour below 1 MW gross is dark (the D-4 rider's zero test)
MECH_COAL_MUSTRUN = 3


def rebuild(y: int, cache: Path) -> dict:
    """``fleet_only`` rebuild of the keeper year (cached): coal rows only."""
    p = cache / f"fleet86_{y}.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    st, _ = reconstruct_bundle_fleet(BUNDLE, y, verbose=False)
    fa = st["fleet_arrays"]
    idx = [i for i, g in enumerate(st["fleet"]) if str(g.plant_group).startswith("COAL")]
    mech = np.asarray(fa.min_gen_mechanism)[idx]
    out = {
        "plant": np.array([int(st["fleet"][i].plant_code) for i in idx]),
        "unit": [st["fleet"][i].unit_id for i in idx],
        "group": [st["fleet"][i].plant_group for i in idx],
        "pmax": np.asarray(fa.pmax)[idx],
        "avail": np.asarray(fa.availability, dtype=np.float32)[idx],
        "floor": np.where(mech == MECH_COAL_MUSTRUN, np.asarray(fa.min_gen)[idx], 0.0).astype(np.float32),
    }
    p.write_bytes(pickle.dumps(out))
    return out


def meter(y: int, plants: set[int], n: int) -> dict[int, np.ndarray]:
    """Hourly CAMPD gross load per plant on the model clock (Jan 1 00:00, ``n`` hours)."""
    t0 = pd.Timestamp(f"{y}-01-01")
    out: dict[int, np.ndarray] = {}
    for s in STATES:
        f = RAW / f"campd-unit-level/{s}_{y}.parquet"
        if not f.exists():
            continue
        m = pd.read_parquet(f, columns=["facilityId", "date", "hour", "grossLoad"])
        m["facilityId"] = pd.to_numeric(m["facilityId"], errors="coerce")
        m = m[m.facilityId.isin(plants)]
        if m.empty:
            continue
        h = ((pd.to_datetime(m["date"]) - t0).dt.days * 24 + m["hour"]).to_numpy()
        ok = (h >= 0) & (h < n)
        for pc, grp in m[ok].assign(h=h[ok]).groupby("facilityId"):
            if grp["grossLoad"].notna().sum() == 0:
                continue  # no gross-load series (e.g. River Valley 10671): unmetered, not dark
            a = np.zeros(n)
            np.add.at(a, grp["h"].to_numpy(dtype=int), grp["grossLoad"].fillna(0).to_numpy())
            out[int(pc)] = out.get(int(pc), 0) + a
    return out


def window_share(y: int, plants: set[int], n: int) -> dict[int, np.ndarray]:
    """Per plant-hour share of the plant's units inside a keeper extract window (day grain)."""
    t0 = pd.Timestamp(f"{y}-01-01")
    frames = [pd.read_csv(RAW / f) for f in EXTRACTS]
    ev = pd.concat(frames, ignore_index=True)
    ev = ev[ev.facility_id.isin(plants)]
    out: dict[int, dict[str, np.ndarray]] = {}
    for r in ev.itertuples():
        s = int((pd.Timestamp(r.outage_start) - t0) / pd.Timedelta(hours=1))
        e = int((pd.Timestamp(r.outage_end) + pd.Timedelta(days=1) - t0) / pd.Timedelta(hours=1))
        s, e = max(s, 0), min(e, n)
        if e <= s:
            continue
        u = out.setdefault(int(r.facility_id), {}).setdefault(str(r.unit_id), np.zeros(n))
        u[s:e] = np.maximum(u[s:e], float(r.unit_pct_of_plant) / 100.0)
    return {pc: np.minimum(sum(us.values()), 1.0) for pc, us in out.items()}


def year_rows(y: int, cache: Path) -> list[dict]:
    """One row per floored coal plant: floored hours / MWh at a dark meter, by window class."""
    fl = rebuild(y, cache)
    n = fl["avail"].shape[1]
    plants = set(int(p) for p in np.unique(fl["plant"][fl["floor"].sum(1) > 0]))
    mw = meter(y, plants, n)
    ws = window_share(y, plants, n)
    rows = []
    for pc in sorted(plants):
        k = fl["plant"] == pc
        floor = fl["floor"][k].sum(0)
        avail_mw = (fl["pmax"][k][:, None] * fl["avail"][k]).sum(0)
        m = mw.get(pc)
        if m is None:
            continue
        w = ws.get(pc, np.zeros(n))
        on = floor > 0
        dark = on & (m < DARK_MW)
        cls = {
            "full_window": dark & (w >= 0.999),
            "part_window": dark & (w > 0) & (w < 0.999),
            "no_window": dark & (w == 0),
        }
        rows.append({
            "year": y, "plant": pc, "floor_hours": int(on.sum()),
            "floor_twh": round(float(floor[on].sum() / 1e6), 4),
            "dark_floor_hours": int(dark.sum()),
            "dark_share": round(float(dark.sum() / max(on.sum(), 1)), 3),
            **{f"{c}_h": int(v.sum()) for c, v in cls.items()},
            **{f"{c}_mwh": round(float(floor[v].sum()), 1) for c, v in cls.items()},
            "full_window_floor_mw_median": (
                round(float(np.median(floor[cls["full_window"]])), 2) if cls["full_window"].any() else None
            ),
            "full_window_avail_mw_median": (
                round(float(np.median(avail_mw[cls["full_window"]])), 2) if cls["full_window"].any() else None
            ),
            "lp_pmax_mw": round(float(fl["pmax"][k].sum()), 1),
        })
    return rows


def main() -> None:
    """All seven keeper years; print the per-year totals and write every plant row."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument("--cache", type=Path, default=Path("/tmp/spp86_cache"))
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.cache.mkdir(parents=True, exist_ok=True)
    rows = [r for y in a.years for r in year_rows(y, a.cache)]
    df = pd.DataFrame(rows)
    tot = df.groupby("year")[[c for c in df.columns if c.endswith(("_h", "_mwh")) or c == "floor_twh"]].sum()
    print(tot.to_string())
    print(df[df.plant == 108].to_string())
    a.out.write_text(json.dumps({"rows": rows, "by_year": tot.reset_index().to_dict("records")}, indent=1))


if __name__ == "__main__":
    main()
