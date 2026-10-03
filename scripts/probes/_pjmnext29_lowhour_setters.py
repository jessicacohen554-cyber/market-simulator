"""PJM-NEXT-29 phase 0 (ZERO LP): who sets the model's price in PJM's real low-price hours.

Readings pre-fixed in ``docs/records/pjm/FINDING-pjm-next-29-lowhour-price-setters-2026-10-02.md``
§1 (committed before this probe ran). Population ``L_y``: hours where the real PJM DA LMP /
delivered gas < :data:`LOW_HR` (hour-of-year, lag 0, the ``_pjmnext11`` convention).

* R1 — model price-setter cells (``plant_group`` x tranche) in ``L_y``: zone-hours anchored to
  the hour's nearest-in-ratio ``marginal == 1`` unit within :data:`ANCHOR_TOL` (the NEXT-28
  attribution, reused from ``_pjmnext28_sunk_noload``); load-weighted shares; ``T*`` = the
  fewest cells covering :data:`TSTAR_COVER` of anchored load pooled over the fail years.
* R2 — IMM Marginal Fuel Postings (time-weighted) averaged over ``L_y`` vs the model's
  anchored attribution mapped to the same fuels.
* R3 — per ``T*`` cell: median ``mc``/gas vs median real DA LMP/gas over its anchored hours.
* R4 — stranded band: thermal units with ``p_real < mc <= p_model`` per ``L_y`` hour (mean
  available MW by cell; COAL_BIT dispatched MWh in the band).
* R5 — PJM's own offers (fleet-level, unit-masked feed): offer-implied MW at or below the real
  DA LMP vs the model's capacity at ``mc <= p_real``; only years whose 12 offer month-files are
  on disk.

Inputs are read-only: the keeper bundle sidecars (tree, else the ``origin/main`` blob),
``actual_lmp_hourly_PJM.parquet``, ``data/raw/pjm-marginal-fuel/by-year/`` and
``data/raw/pjm-energy-offers/``. Writes ``results/phase0/pjm/_pjmnext29_lowhour_setters.json``.
Run: ``python3 scripts/probes/_pjmnext29_lowhour_setters.py [YEAR ...]``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
from _pjmnext28_sunk_noload import (  # noqa: E402
    ANCHOR_TOL,
    _parquet,
    _tranche,
    gas_daily,
)

ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
IMM_DIR = REPO / "data/raw/pjm-marginal-fuel/by-year"
OFFERS = REPO / "data/raw/pjm-energy-offers"
OUT = REPO / "results/phase0/pjm/_pjmnext29_lowhour_setters.json"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
FAIL_YEARS = (2019, 2020, 2021)
#: Real-hour population threshold (implied HR, MMBtu/MWh): the NEXT-11/12 "below 6.5 x gas" object.
LOW_HR = 6.5
TSTAR_COVER = 0.60
TSTAR_MAX = 3
MISASSIGN = 0.15
R3_MIN_GAP = 1.0
STRAND_SHARE = 0.25
R5_MIN_GW = 5.0
EXTERNAL_ZONE = "PJM_external"
#: IMM fuel label -> comparison fuel.
IMM_FUEL = {
    "Natural Gas": "gas",
    "Coal": "coal",
    "Waste Coal": "coal",
    "Uranium": "nuclear",
    "Wind": "vre",
    "Solar": "vre",
}
#: Model ``fuel`` -> comparison fuel.
MODEL_FUEL = {
    "gas_cc": "gas",
    "gas_ct": "gas",
    "gas_st": "gas",
    "coal": "coal",
    "nuclear": "nuclear",
    "wind": "vre",
    "solar": "vre",
}
THERMAL = ("gas", "coal")


def _cell(df: pd.DataFrame) -> pd.Series:
    """``plant_group:tranche`` with the econ rungs split (econc / econlo / econhi)."""
    sfx = df["unit_id"].str.rsplit("_", n=1).str[-1]
    kind = _tranche(df["unit_id"]).to_numpy()
    kind = np.where(sfx.str.match(r"^econc\d*$"), "econc", kind)
    kind = np.where(sfx == "econlo", "econlo", kind)
    kind = np.where(sfx == "econhi", "econhi", kind)
    return df["plant_group"] + ":" + pd.Series(kind, index=df.index)


def real_low_hours(year: int, gas: pd.Series) -> pd.DataFrame:
    """Real DA LMP, gas and the low-hour flag by hour of year."""
    a = pd.read_parquet(ACTUAL)
    a = a[a["year"] == year].set_index("hour")["da"].sort_index()
    days = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(a.index, "h")
    g = gas.reindex(days.normalize()).to_numpy(float)
    f = pd.DataFrame({"p_real": a.to_numpy(float), "gas": g}, index=a.index)
    f["low"] = (f["p_real"] / f["gas"]) < LOW_HR
    return f


def imm_shares(year: int, hours: np.ndarray) -> dict:
    """IMM time-weighted marginal-fuel shares averaged over ``hours`` (hour of year)."""
    d = pd.read_csv(IMM_DIR / f"pjm_marginal_fuel_{year}.csv")
    ts = pd.to_datetime(d["hour_beginning_ept"], format="%Y-%m-%d %H:%M")
    d["hoy"] = ((ts - pd.Timestamp(f"{year}-01-01")) / pd.Timedelta("1h")).astype(int)
    d["f"] = d["fuel_type"].map(IMM_FUEL).fillna("other")
    w = d.pivot_table(
        index="hoy", columns="f", values="percent_marginal", aggfunc="sum"
    )
    w = w.div(w.sum(axis=1), axis=0).fillna(0.0)  # repeated fall hour: renormalise
    w = w.reindex(hours).dropna(how="all")
    return {k: round(float(v), 4) for k, v in w.mean().items()}


def offer_capacity(year: int, p_real: pd.Series) -> pd.Series | None:
    """PJM fleet offer-implied MW at or below the real DA LMP, by hour of year."""
    from _pjmnext11_offered_ecomax import offer_dispatch  # noqa: PLC0415

    files = sorted(OFFERS.glob(f"pjm_energy_offers_{year}_*.parquet"))
    if len(files) < 12:
        return None
    probe = pd.read_parquet(files[0]).columns
    mw_cols = [c for c in probe if c.startswith("mw") and c[2:].isdigit()]
    bid_cols = [f"bid{c[2:]}" for c in mw_cols]
    out = []
    for p in files:
        df = pd.read_parquet(
            p, columns=["bid_datetime_beginning_ept", "avg_ecomax", *mw_cols, *bid_cols]
        )
        ts = pd.to_datetime(
            df["bid_datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        hoy = ((ts - pd.Timestamp(f"{year}-01-01")) / pd.Timedelta("1h")).astype(int)
        price = p_real.reindex(hoy.to_numpy()).to_numpy(float)
        e = df["avg_ecomax"].to_numpy(float)
        d = np.minimum(
            offer_dispatch(
                df[mw_cols].to_numpy(float), df[bid_cols].to_numpy(float), price
            ),
            np.where(e > 0, e, np.inf),
        )
        out.append(pd.Series(d, index=hoy.to_numpy()).groupby(level=0).sum())
    return pd.concat(out).groupby(level=0).sum()


def run_year(year: int, gas: pd.Series) -> dict:
    """R1-R5 for one year."""
    rl = real_low_hours(year, gas)
    low = rl.index[rl["low"]].to_numpy()
    sysd = _parquet(f"system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"][["zone", "hour", "price", "demand"]].copy()
    sysd["zone"] = sysd["zone"].astype(str)
    sysd = sysd[sysd["zone"] != EXTERNAL_ZONE]
    cols = ["unit_id", "plant_group", "fuel", "hour", "mw", "cap_mw", "mc", "marginal"]
    um = _parquet(
        f"unit_marginal_{year}.parquet",
        columns=cols,
        filters=[("pass", "=", "P1"), ("hour", "in", [int(h) for h in low])],
    )
    um = um[um["fuel"].astype(str) != "import"]
    # cell / comparison fuel on the unique (unit, group, fuel) keys, not per row
    key = um[["unit_id", "plant_group", "fuel"]].astype(str).drop_duplicates()
    key["cell"] = _cell(key.reset_index(drop=True)).to_numpy()
    key["cf"] = key["fuel"].map(MODEL_FUEL).fillna("other")
    keyed = key.set_index("unit_id")
    uid = um["unit_id"].astype(str)
    um = um.drop(columns=["unit_id", "fuel"])
    um["cell"] = pd.Categorical(uid.map(keyed["cell"]))
    um["cf"] = pd.Categorical(uid.map(keyed["cf"]))
    um["plant_group"] = um["plant_group"].astype(str).astype("category")
    del uid

    # model system price (load-weighted) and the real-vs-model share of low hours
    pw = sysd.assign(pw=sysd["price"] * sysd["demand"]).groupby("hour")[
        ["pw", "demand"]
    ]
    pw = pw.sum()
    p_model = (pw["pw"] / pw["demand"]).reindex(rl.index)
    model_low_share = float(np.mean((p_model / rl["gas"]) < LOW_HR))

    # --- R1/R2/R3 attribution in L_y ----------------------------------------------
    m = um[(um["marginal"] == 1) & (um["mc"] > 0)]
    zl = sysd[sysd["hour"].isin(low)]
    x = zl.merge(m[["hour", "cell", "cf", "mc"]], on="hour")
    x["dev"] = (x["price"] / x["mc"] - 1.0).abs()
    x = x[x["dev"] <= ANCHOR_TOL]
    a = x.loc[x.groupby(["zone", "hour"])["dev"].idxmin()]
    W = float(zl["demand"].sum())
    wa = float(a["demand"].sum())
    cells = (a.groupby("cell")["demand"].sum() / wa).sort_values(ascending=False)
    fuels = (a.groupby("cf")["demand"].sum() / wa).to_dict()
    a = a.merge(rl[["p_real", "gas"]], left_on="hour", right_index=True)
    r3 = {}
    for c in cells.index[:8]:
        s = a[a["cell"] == c]
        r3[c] = {
            "median_mc_over_gas": round(float(np.median(s["mc"] / s["gas"])), 3),
            "median_real_over_gas": round(float(np.median(s["p_real"] / s["gas"])), 3),
        }
        r3[c]["gap"] = round(
            r3[c]["median_mc_over_gas"] - r3[c]["median_real_over_gas"], 3
        )

    # --- R4 stranded band ------------------------------------------------------------
    t = um[um["cf"].isin(THERMAL) & (um["cap_mw"] > 0)]
    t = t.merge(rl[["p_real"]], left_on="hour", right_index=True)
    t["p_model"] = p_model.reindex(t["hour"]).to_numpy()
    band = t[(t["mc"] > t["p_real"]) & (t["mc"] <= t["p_model"])]
    nlow = max(len(low), 1)
    strand = band.groupby("cell")["cap_mw"].sum() / nlow
    strand_total = float(strand.sum())
    strand_share = (strand / strand_total).sort_values(ascending=False)
    cb_band = band[band["plant_group"] == "COAL_BIT"]

    # --- R5 offers -------------------------------------------------------------------
    r5 = None
    oc = offer_capacity(year, rl["p_real"])
    if oc is not None:
        mc_cap = um.merge(rl[["p_real"]], left_on="hour", right_index=True)
        q_model = (
            mc_cap[mc_cap["mc"] <= mc_cap["p_real"]].groupby("hour")["cap_mw"].sum()
        )
        q = pd.DataFrame({"pjm": oc.reindex(low), "model": q_model.reindex(low)})
        q = q.dropna()
        dq = (q["pjm"] - q["model"]) / 1e3
        r5 = {
            "hours": int(len(q)),
            "median_pjm_offered_gw": round(float(q["pjm"].median() / 1e3), 2),
            "median_model_cap_gw": round(float(q["model"].median() / 1e3), 2),
            "median_dq_gw": round(float(dq.median()), 2),
            "p25_dq_gw": round(float(dq.quantile(0.25)), 2),
            "p75_dq_gw": round(float(dq.quantile(0.75)), 2),
        }

    return {
        "year": year,
        "real_low_hour_share": round(float(rl["low"].mean()), 4),
        "model_low_hour_share": round(model_low_share, 4),
        "low_hours": int(len(low)),
        "median_real_hr_in_low": round(
            float(np.median(rl.loc[rl["low"], "p_real"] / rl.loc[rl["low"], "gas"])), 3
        ),
        "median_model_hr_in_low": round(
            float(
                np.nanmedian(
                    p_model.reindex(low).to_numpy() / rl.loc[low, "gas"].to_numpy()
                )
            ),
            3,
        ),
        "anchored_low_load_share": round(wa / W, 4),
        "R1_cells": {k: round(float(v), 4) for k, v in cells.head(12).items()},
        "R2_model_fuel": {k: round(float(v), 4) for k, v in fuels.items()},
        "R2_imm_fuel": imm_shares(year, low),
        "R3": r3,
        "R4_band_mean_gw": round(strand_total / 1e3, 2),
        "R4_band_cells": {
            k: round(float(v), 4) for k, v in strand_share.head(10).items()
        },
        "R4_coal_bit_band_dispatch_twh": round(float(cb_band["mw"].sum()) / 1e6, 3),
        "R4_coal_bit_band_dispatch_by_cell_twh": {
            k: round(float(v) / 1e6, 3)
            for k, v in cb_band.groupby("cell")["mw"].sum().items()
        },
        "R5": r5,
    }


def verdicts(by: dict[int, dict]) -> dict:
    """Apply the §1 readings over the fail years."""
    fy = [y for y in FAIL_YEARS if y in by]
    pooled: dict[str, float] = {}
    for y in fy:
        for c, s in by[y]["R1_cells"].items():
            pooled[c] = pooled.get(c, 0.0) + s / len(fy)
    tstar, cum = [], 0.0
    for c, s in sorted(pooled.items(), key=lambda kv: -kv[1]):
        tstar.append(c)
        cum += s
        if cum >= TSTAR_COVER:
            break
    mis = {}
    for f in ("gas", "coal", "nuclear", "vre", "other"):
        n = sum(
            abs(by[y]["R2_model_fuel"].get(f, 0.0) - by[y]["R2_imm_fuel"].get(f, 0.0))
            >= MISASSIGN
            for y in fy
        )
        mis[f] = n >= 2
    strand = {}
    for y in fy:
        for c, s in by[y]["R4_band_cells"].items():
            if s >= STRAND_SHARE:
                strand[c] = strand.get(c, 0) + 1
    stranding = sorted(c for c, n in strand.items() if n >= 2)
    r5 = [by[y]["R5"] for y in (2019, 2021) if y in by and by[y]["R5"]]
    return {
        "Tstar": tstar,
        "Tstar_cover": round(cum, 4),
        "R1_concentrated": len(tstar) <= TSTAR_MAX,
        "R2_misassigned": mis,
        "R4_stranding_cells": stranding,
        "R5_quantity_short": (
            all(r["median_dq_gw"] >= R5_MIN_GW for r in r5) if len(r5) == 2 else None
        ),
    }


def main(years: list[int]) -> None:
    """Run every year, apply the readings, write the JSON."""
    gas = gas_daily()
    rows = []
    for y in years:
        r = run_year(y, gas)
        rows.append(r)
        top = list(r["R1_cells"].items())[:4]
        print(
            f"{y}: low real {r['real_low_hour_share']:.3f} model {r['model_low_hour_share']:.3f} "
            f"HR {r['median_real_hr_in_low']:.2f}/{r['median_model_hr_in_low']:.2f} "
            f"anch {r['anchored_low_load_share']:.2f} top {top} "
            f"band {r['R4_band_mean_gw']} GW cb {r['R4_coal_bit_band_dispatch_twh']} TWh "
            f"R5 {r['R5']}",
            flush=True,
        )
    by = {r["year"]: r for r in rows}
    v = verdicts(by)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "probe": "PJM-NEXT-29 phase 0: low-hour price-setters (zero LP)",
                "keeper_bundle": "results/calibration/w0_pjm_span",
                "low_hr": LOW_HR,
                "anchor_tol": ANCHOR_TOL,
                "verdicts": v,
                "years": rows,
            },
            indent=2,
        )
    )
    print(json.dumps(v, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or list(YEARS))
