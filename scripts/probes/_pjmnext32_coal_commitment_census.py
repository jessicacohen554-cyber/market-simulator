"""PJM-NEXT-32 (ZERO LP): coal multi-day slack decommitment census, real vs keeper.

Readings fixed ex ante in
``docs/records/pjm/FINDING-pjm-next-32-coal-commitment-census-2026-10-03.md`` §1.

Per year, for each keeper COAL_BIT plant and its coal-fuel CAMPD units: the real online
share, the uncovered dark spells (NEXT-31 coverage logic: not inside any of the three
committed extracts at the loader's day grain), and the keeper's per-tranche dispatch from
``unit_marginal_<Y>``. Reads:

* Q1 model-runs-freed MW ``X = min(max(0, mw - K*·ON_real), K*·uncovered_dark_share)``;
* Q2 ``X`` allocated over the dispatched tranches from the highest ``mc`` down, floor share
  = ``mustrun`` + ``sync``; plus the share of ``X`` the keeper's own zone price clears;
* Q3 forgone margin per MW over each uncovered M/L dark spell, real DA system LMP and keeper
  zone price, against ``BIN_STARTUP_COST_PER_MW['COAL_BIT']``;
* Q4 real stop counts and spell lengths against ``COAL_BIN_MIN_DOWN_HOURS``, and the keeper's
  implied plant off-events.

Writes ``results/phase0/pjm/_pjmnext32_coal_commitment_census.json``.
Run: ``.venv/bin/python scripts/probes/_pjmnext32_coal_commitment_census.py [YEAR ...]``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
sys.path.insert(0, str(REPO / "src"))
from _pjmnext28_sunk_noload import _parquet  # noqa: E402

from market_sim.data.fleet.eia860 import (  # noqa: E402
    BIN_STARTUP_COST_PER_MW,
    COAL_BIN_MIN_DOWN_HOURS,
)

OUT = REPO / "results/phase0/pjm/_pjmnext32_coal_commitment_census.json"
UNIT_DIR = REPO / "data/raw/campd-unit-level"
RAW = REPO / "data/raw"
ACTUAL = RAW / "_validation-source/actual_lmp_hourly_PJM.parquet"
#: The three committed extracts the keeper resolves (NEXT-31 FINDING §1 table).
EXTRACTS = (
    RAW / "campd-unit-outages-rederive-peakerkeep-exitfix-unitfuel-PJM.csv",
    RAW / "campd-unit-outages-short-rederive-PJM.csv",
    RAW / "campd-unit-outages-shortgas-PJM.csv",
)
GROUP = "COAL_BIT"
T = 8760
YEARS = tuple(range(2019, 2026))
POOL = (2019, 2020, 2021)
#: Keeper C1 COAL_BIT overage vs CAMPD (TWh), keeper record 2026-10-02-w0-pjm-fix2.
C1_OVER_TWH = {2019: 19.0, 2020: 13.0, 2021: 15.0}
FLOOR = ("mustrun", "sync")
MIN_DOWN = int(COAL_BIN_MIN_DOWN_HOURS)
STARTUP = float(BIN_STARTUP_COST_PER_MW[GROUP])
#: Long band: the long extract's 5-day floor (NEXT-31 LONG_H).
LONG_H = 120


def _runs(mask: np.ndarray):
    """(start, stop) of each maximal True run."""
    if not mask.any():
        return []
    idx = np.flatnonzero(np.diff(np.r_[0, mask.view(np.int8), 0]))
    return list(zip(idx[::2].tolist(), idx[1::2].tolist()))


def covered_masks(y: int) -> dict[tuple[int, str], np.ndarray]:
    """Unit -> hour mask covered by any committed extract (day grain, end inclusive)."""
    y0 = pd.Timestamp(f"{y}-01-01")
    cov: dict[tuple[int, str], np.ndarray] = {}
    for path in EXTRACTS:
        df = pd.read_csv(path)
        df["outage_start"] = pd.to_datetime(df["outage_start"])
        df["outage_end"] = pd.to_datetime(df["outage_end"])
        df = df[(df["outage_end"].dt.year >= y) & (df["outage_start"].dt.year <= y)]
        for r in df.itertuples():
            k = (int(r.facility_id), str(r.unit_id))
            s = int((r.outage_start - y0) / pd.Timedelta(hours=1))
            e = int((r.outage_end + pd.Timedelta(days=1) - y0) / pd.Timedelta(hours=1))
            s, e = max(s, 0), min(e, T)
            if e > s:
                cov.setdefault(k, np.zeros(T, bool))[s:e] = True
    return cov


def coal_units(y: int, plants: set[int]) -> pd.DataFrame:
    """CAMPD unit-level rows for ``plants``, coal-fuel units only (NEXT-31 lesson x)."""
    fr = []
    for f in sorted(UNIT_DIR.glob(f"*_{y}.parquet")):
        x = (
            ds.dataset(str(f), format="parquet")
            .to_table(
                columns=[
                    "facilityId",
                    "unitId",
                    "date",
                    "hour",
                    "opTime",
                    "grossLoad",
                    "primaryFuelInfo",
                ]
            )
            .to_pandas()
        )
        x["facilityId"] = pd.to_numeric(x["facilityId"], errors="coerce")
        fr.append(x[x["facilityId"].isin(plants)])
    d = pd.concat(fr, ignore_index=True)
    d["unitId"] = d["unitId"].astype(str)
    coal = d.groupby(["facilityId", "unitId"])["primaryFuelInfo"].agg(
        lambda v: v.dropna().astype(str).str.contains("Coal").any()
    )
    keep = set(coal[coal].index)
    d = d[[k in keep for k in zip(d["facilityId"], d["unitId"])]].copy()
    d["hoy"] = (
        pd.to_datetime(d["date"]) - pd.Timestamp(f"{y}-01-01")
    ).dt.days * 24 + d["hour"].astype(int)
    return d[(d["hoy"] >= 0) & (d["hoy"] < T)]


def _kind(unit_id: pd.Series) -> pd.Series:
    """Tranche kind from the unit-id suffix (``econc07`` -> ``econc``)."""
    return (
        unit_id.astype(str)
        .str.rsplit("_", n=1)
        .str[-1]
        .str.replace(r"\d+$", "", regex=True)
    )


def keeper_plants(y: int) -> dict[int, dict]:
    """Per plant: tranche arrays (kind, mw, cap, mc) and zone from ``unit_marginal_<y>``."""
    um = _parquet(
        f"unit_marginal_{y}.parquet",
        columns=["unit_id", "plant_code", "zone", "hour", "mw", "cap_mw", "mc"],
        filters=[("plant_group", "=", GROUP), ("pass", "=", "P1")],
    )
    um["kind"] = _kind(um["unit_id"])
    out: dict[int, dict] = {}
    for pc, g in um.groupby("plant_code", observed=True):
        tr = []
        for uid, gu in g.groupby("unit_id", observed=True):
            h = gu["hour"].to_numpy()
            mw, cap, mc = np.zeros(T), np.zeros(T), np.full(T, np.nan)
            mw[h], cap[h], mc[h] = gu["mw"], gu["cap_mw"], gu["mc"]
            tr.append((str(gu["kind"].iloc[0]), mw, cap, mc))
        out[int(pc)] = {"zone": str(g["zone"].iloc[0]), "tr": tr}
    return out


def zone_price(y: int) -> dict[str, np.ndarray]:
    """Keeper P1 zone price by hour."""
    s = _parquet(f"system_{y}.parquet", columns=["pass", "zone", "hour", "price"])
    s = s[s["pass"] == "P1"]
    return {
        z: g.set_index("hour")["price"].reindex(range(T)).to_numpy(float)
        for z, g in s.groupby("zone")
    }


def run_year(y: int) -> dict:
    """Census one year (FINDING §1 Q1..Q4)."""
    a = pd.read_parquet(ACTUAL)
    p_real = a[a["year"] == y].set_index("hour")["da"].reindex(range(T)).to_numpy(float)
    zp = zone_price(y)
    sysp = np.nanmean(np.vstack(list(zp.values())), axis=0)
    kp = keeper_plants(y)
    d = coal_units(y, set(kp))
    cov = covered_masks(y)

    X_tot = X_floor = X_cleared = 0.0
    unc_dark_mwh = {"S": 0.0, "M": 0.0, "L": 0.0}
    econ_mwh = {"M": 0.0, "L": 0.0}
    keeper_econ_mwh = {"M": 0.0, "L": 0.0}
    floor_in_ml = 0.0
    keeper_mw_in_ml = 0.0
    real_stops = 0
    stop_lens: list[int] = []
    units_n = 0
    keeper_off_events = 0
    X_month = np.zeros(12)
    hod = np.zeros(24)
    month_of = (
        pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(T), "h")
    ).month.to_numpy() - 1
    for pc, g in d.groupby("facilityId"):
        pc = int(pc)
        P = kp.get(pc)
        if P is None:
            continue
        tr = P["tr"]
        kinds = np.array([t[0] for t in tr])
        MW = np.vstack([t[1] for t in tr])
        CAP = np.vstack([t[2] for t in tr])
        MC = np.vstack([t[3] for t in tr])
        Kh = CAP.sum(0)
        kstar = float(Kh.max())
        if kstar <= 0:
            continue
        mw = MW.sum(0)
        on_k = mw > 1e-3
        keeper_off_events += int((on_k[:-1] & ~on_k[1:]).sum())
        units = {}
        for uid, gu in g.groupby("unitId"):
            gross = np.zeros(T)
            op = np.zeros(T)
            gross[gu["hoy"].to_numpy()] = gu["grossLoad"].fillna(0.0).to_numpy()
            op[gu["hoy"].to_numpy()] = gu["opTime"].fillna(0.0).to_numpy()
            if gross.max() <= 0:
                continue
            units[uid] = (gross.max(), op <= 0.0)
        if not units:
            continue
        ptot = sum(v[0] for v in units.values())
        on_real = np.zeros(T)
        unc = np.zeros(T)
        unc_ml = np.zeros(T)
        nonfloor = ~np.isin(kinds, FLOOR)
        capnf = np.where(nonfloor[:, None], CAP, 0.0)
        mc_plant = np.nansum(np.nan_to_num(MC) * capnf, 0) / np.maximum(
            capnf.sum(0), 1e-9
        )
        price = zp.get(P["zone"], sysp)
        for uid, (pk, dark) in units.items():
            w = pk / ptot
            units_n += 1
            on_real += w * ~dark
            runs = _runs(dark)
            real_stops += sum(1 for s, _ in runs if s > 0)
            stop_lens += [e - s for s, e in runs if s > 0 and e < T]
            ud = dark & ~cov.get((pc, uid), np.zeros(T, bool))
            unc += w * ud
            for s, e in _runs(ud):
                L = e - s
                band = "S" if L < MIN_DOWN else ("M" if L < LONG_H else "L")
                mwh = w * kstar * L
                unc_dark_mwh[band] += mwh
                if band == "S":
                    continue
                unc_ml[s:e] += w
                seg = slice(s, e)
                if np.nansum(p_real[seg] - mc_plant[seg]) < STARTUP:
                    econ_mwh[band] += mwh
                if np.nansum(price[seg] - mc_plant[seg]) < STARTUP:
                    keeper_econ_mwh[band] += mwh
        X = np.minimum(np.maximum(0.0, mw - kstar * on_real), kstar * unc)
        X_tot += X.sum()
        X_month += np.bincount(month_of, weights=X, minlength=12)
        hod += np.bincount(np.arange(T) % 24, weights=X, minlength=24)
        # Allocate X over dispatched tranches from the highest mc down.
        order = np.argsort(-np.nan_to_num(MC, nan=-1e9), axis=0)
        mws = np.take_along_axis(MW, order, 0)
        ks = kinds[order]
        cum = np.cumsum(mws, 0)
        alloc = np.clip(X[None, :] - (cum - mws), 0.0, mws)
        X_floor += float(alloc[np.isin(ks, FLOOR)].sum())
        top_mc = np.where(MW > 1e-3, np.nan_to_num(MC, nan=-1e9), -1e9).max(0)
        X_cleared += float(X[price >= top_mc].sum())
        floor_mw = MW[~nonfloor].sum(0)
        floor_in_ml += float(np.minimum(floor_mw, kstar * unc_ml).sum())
        keeper_mw_in_ml += float(np.minimum(mw, kstar * unc_ml).sum())

    sl = np.array(stop_lens) if stop_lens else np.array([0])
    ml = unc_dark_mwh["M"] + unc_dark_mwh["L"]
    return {
        "X_twh": X_tot / 1e6,
        "X_floor_twh": X_floor / 1e6,
        "X_price_cleared_twh": X_cleared / 1e6,
        "X_month_twh": (X_month / 1e6).round(3).tolist(),
        "X_hod_share": (hod / max(hod.sum(), 1e-9)).round(4).tolist(),
        "unc_dark_twh": {k: v / 1e6 for k, v in unc_dark_mwh.items()},
        "econ_real_share_ml": sum(econ_mwh.values()) / ml if ml else None,
        "econ_real_share": {
            b: econ_mwh[b] / unc_dark_mwh[b] if unc_dark_mwh[b] else None
            for b in ("M", "L")
        },
        "econ_keeper_share_ml": sum(keeper_econ_mwh.values()) / ml if ml else None,
        "keeper_mw_in_ml_twh": keeper_mw_in_ml / 1e6,
        "floor_mw_in_ml_twh": floor_in_ml / 1e6,
        "units": units_n,
        "real_stops": real_stops,
        "real_stops_per_unit": real_stops / max(units_n, 1),
        "stop_len_p10_p50_p90": np.percentile(sl, [10, 50, 90]).tolist(),
        "stop_share_lt_min_down": float((sl < MIN_DOWN).mean()),
        "keeper_plant_off_events": keeper_off_events,
    }


def readings(res: dict) -> dict:
    """Apply FINDING §1 Q1..Q3 and the verdict as fixed."""
    r1 = {y: res[y]["X_twh"] / C1_OVER_TWH[y] for y in POOL}
    q1 = (
        "MATERIAL"
        if all(v >= 0.5 for v in r1.values())
        else ("PARTIAL" if all(v >= 0.25 for v in r1.values()) else "IMMATERIAL")
    )
    xt = sum(res[y]["X_twh"] for y in POOL)
    fs = sum(res[y]["X_floor_twh"] for y in POOL) / xt if xt else 0.0
    cs = sum(res[y]["X_price_cleared_twh"] for y in POOL) / xt if xt else 0.0
    q2 = "FLOOR-HELD" if fs >= 0.5 else "PRICE-CLEARED"
    ml = sum(res[y]["unc_dark_twh"]["M"] + res[y]["unc_dark_twh"]["L"] for y in POOL)
    es = (
        sum(
            res[y]["econ_real_share_ml"]
            * (res[y]["unc_dark_twh"]["M"] + res[y]["unc_dark_twh"]["L"])
            for y in POOL
            if res[y]["econ_real_share_ml"] is not None
        )
        / ml
        if ml
        else 0.0
    )
    q3 = "ECONOMIC" if es >= 0.5 else "NOT ECONOMIC"
    charter = q1 in ("MATERIAL", "PARTIAL") and q2 == "FLOOR-HELD" and q3 == "ECONOMIC"
    return {
        "Q1": {"ratio_to_c1_overage": r1, "verdict": q1},
        "Q2": {"floor_share": fs, "price_cleared_share": cs, "verdict": q2},
        "Q3": {"econ_share_ml_pooled": es, "verdict": q3},
        "VERDICT": "CHARTERED" if charter else "NOT CHARTERED",
    }


def main(years: list[int]) -> None:
    """Run the census and write the JSON."""
    res = {}
    for y in years:
        res[y] = run_year(y)
        print(y, json.dumps(res[y]), flush=True)
    out = {"years": res}
    if all(y in res for y in POOL):
        out["readings"] = readings(res)
        print(json.dumps(out["readings"], indent=2))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or list(YEARS))
