"""R-CAISO-23 phase 0 (ZERO LP): the midday RT north-south spread on keeper 2026-09-30-caiso-r20-overnight.

One Path-15 / Path-26 census, 2022-2025, h10-16, on the model's fixed-PST hour-of-year clock
(R-CAISO-21's ``measured`` reader; hubs TH_NP15 / TH_ZP26 / TH_SP15, RTM):

* A. the split by cut: NP15-ZP26 (Path 15) and ZP26-SP15_rest (Path 26), model vs measured, mean,
  median, and the count of hours above $15 (caiso-215's split-hour statistic);
* B. the same split with the measured RT tail removed (3-hub mean > $200, R-CAISO-22's class), so
  the chronic body and the C3c-tail congestion hours are reported apart;
* C. the measured split conditioned on measured curtailment (CAISO Production & Curtailments
  workbook, Local vs System, h10-16 hourly MWh), against the model's zonal dump;
* D. the model's own zonal separation hours (|NP15-ZP26| > $1, > $15) — the LP binds a link only
  where the two prices separate, so this is the zero-LP witness of how often the Path-15 cut binds;
* E. the PNW / DSW legs: model WECC_PNW / WECC_DSW price vs the committed OASIS intertie DAM
  MALIN / PALOVRDE hub price, midday;
* F. the Jan-2024 + Oct-7 north-congestion tail hours (R-CAISO-22 §1): per-hour table.

Inputs: the keeper's committed hourly sidecars (results/calibration/rcaiso20_A_span/hourly/),
data/raw/lmp-data/CAISO RTM, data/raw/caiso-curtailment, the committed intertie LMP parquet.
Writes results/calibration/_rcaiso23/ns_spread_phase0.json (gitignored scratch).

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso23_ns_spread_phase0.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import _rcaiso21_evening_phase0 as r21  # noqa: E402

BUNDLE = Path("results/calibration/rcaiso20_A_span/hourly")
OUT = Path("results/calibration/_rcaiso23/ns_spread_phase0.json")
CURT = "data/raw/caiso-curtailment/productionandcurtailmentsdata_{y}.xlsx"
WECC_LMP = Path("data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet")
T = 8760
HOD = r21.HOD
MID = (HOD >= 10) & (HOD <= 16)
THR = 200.0  # calibration_verdict.TAIL_THRESHOLD["CAISO"]
SPLIT = 15.0  # caiso-215 split-hour statistic, $/MWh


def model_prices(y: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Model P1 zonal price and dump (hour x zone)."""
    s = pd.read_parquet(BUNDLE / f"system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    p = s.pivot(index="hour", columns="zone", values="price").iloc[:T]
    d = s.pivot(index="hour", columns="zone", values="dump").iloc[:T]
    return p, d


def curtailment(y: int) -> pd.DataFrame:
    """Measured hourly curtailment MWh (Local, System) on the fixed-PST hour-of-year clock."""
    d = pd.read_excel(CURT.format(y=y), sheet_name="Curtailments")
    mw = d["Wind Curtailment"].fillna(0) + d["Solar Curtailment"].fillna(0)
    # The workbook's Date is the local calendar day; Hour is hour-ending 1-24, prevailing time.
    loc = pd.to_datetime(d["Date"]).dt.normalize() + pd.to_timedelta(d["Hour"] - 1, "h")
    utc = loc.dt.tz_localize(
        "America/Los_Angeles", ambiguous="NaT", nonexistent="NaT"
    ).dt.tz_convert("Etc/GMT+8")
    h = (utc - pd.Timestamp(f"{y}-01-01", tz="Etc/GMT+8")).dt.total_seconds() // 3600
    df = pd.DataFrame({"h": h, "mwh": mw / 12.0, "r": d["Reason"].astype(str)})
    df = df.dropna(subset=["h"])
    df = df[(df.h >= 0) & (df.h < T)]
    out = pd.DataFrame(0.0, index=np.arange(T), columns=["Local", "System"])
    for r in ("Local", "System"):
        g = df[df.r == r].groupby("h").mwh.sum()
        out.loc[g.index.astype(int), r] = g.to_numpy()
    return out


def wecc_hub(y: int, hub: str) -> np.ndarray:
    """Committed OASIS intertie DAM hub price, fixed-PST hour-of-year."""
    w = pd.read_parquet(WECC_LMP)
    g = w[(w.year == y) & (w.hub == hub)].set_index("hour").price
    return g.reindex(np.arange(T)).to_numpy()


def stats(a: np.ndarray) -> dict:
    """Mean / median / count above SPLIT of a spread array (NaNs dropped)."""
    a = a[~np.isnan(a)]
    return {
        "mean": round(float(a.mean()), 2),
        "median": round(float(np.median(a)), 2),
        "n_gt15": int((a > SPLIT).sum()),
        "n_lt_m15": int((a < -SPLIT).sum()),
        "n": int(a.size),
    }


def main() -> None:
    """Run the census and write the JSON."""
    res: dict = {}
    for y in (2022, 2023, 2024, 2025):
        p, dump = model_prices(y)
        m = r21.measured(y, "rtm")
        ok = (
            MID
            & ~np.isnan(m["NP15"])
            & ~np.isnan(m["ZP26"])
            & ~np.isnan(m["SP15_rest"])
        )
        tail = (m["NP15"] + m["ZP26"] + m["SP15_rest"]) / 3 > THR
        body = ok & ~tail
        mp = {z: p[z].to_numpy() for z in p.columns}
        cut = {
            "P15_NP_ZP": (mp["NP15"] - mp["ZP26"], m["NP15"] - m["ZP26"]),
            "P26_ZP_SP": (mp["ZP26"] - mp["SP15_rest"], m["ZP26"] - m["SP15_rest"]),
            "NP_SP": (mp["NP15"] - mp["SP15_rest"], m["NP15"] - m["SP15_rest"]),
        }
        yr: dict = {"n_mid": int(ok.sum()), "n_mid_tail": int((ok & tail).sum())}
        for c, (mo, me) in cut.items():
            yr[c] = {
                "all": {"model": stats(mo[ok]), "meas": stats(me[ok])},
                "body": {"model": stats(mo[body]), "meas": stats(me[body])},
            }
        # Hub levels (body), so the zone-level residual is visible beside the spread.
        yr["level_body"] = {
            z: {
                "model": round(float(mp[z][body].mean()), 2),
                "meas": round(float(m[z][body].mean()), 2),
            }
            for z in ("NP15", "ZP26", "SP15_rest")
        }
        # C. curtailment conditioning.
        cu = curtailment(y)
        loc = cu["Local"].to_numpy()
        sysc = cu["System"].to_numpy()
        np_zp = m["NP15"] - m["ZP26"]
        bins = {
            "no_curt": body & (loc + sysc < 1),
            "local_only": body & (loc >= 1) & (sysc < 1),
            "system": body & (sysc >= 1),
        }
        yr["curt"] = {
            "meas_local_TWh_mid": round(float(loc[MID].sum() / 1e6), 3),
            "meas_system_TWh_mid": round(float(sysc[MID].sum() / 1e6), 3),
            "model_dump_TWh_mid_by_zone": {
                z: round(float(dump[z].to_numpy()[MID].sum() / 1e6), 3)
                for z in dump.columns
                if dump[z].to_numpy()[MID].sum() > 1e3
            },
            "meas_P15_by_curt_bin": {
                k: {
                    "n": int(v.sum()),
                    "meas_mean": round(float(np.nanmean(np_zp[v])), 2),
                    "meas_n_gt15": int((np_zp[v] > SPLIT).sum()),
                    "model_mean": round(float(np.nanmean(cut["P15_NP_ZP"][0][v])), 2),
                    "model_n_gt15": int((cut["P15_NP_ZP"][0][v] > SPLIT).sum()),
                }
                for k, v in bins.items()
            },
            "corr_meas_P15_vs_local_curt_body": round(
                float(np.corrcoef(np_zp[body], loc[body])[0, 1]), 3
            ),
        }
        # D. model-own separation.
        mo = cut["P15_NP_ZP"][0]
        yr["model_P15_separation_mid"] = {
            "abs_gt1": int((np.abs(mo[ok]) > 1).sum()),
            "gt15": int((mo[ok] > SPLIT).sum()),
            "lt_m15": int((mo[ok] < -SPLIT).sum()),
        }
        # E. PNW / DSW legs (DAM intertie hub vs model node price), midday body.
        legs = {}
        for z, hub in (("WECC_PNW", "MALIN"), ("WECC_DSW", "PALOVRDE")):
            h = wecc_hub(y, hub)
            k = body & ~np.isnan(h)
            legs[z] = {
                "n": int(k.sum()),
                "model": round(float(mp[z][k].mean()), 2) if k.any() else None,
                "meas_dam": round(float(h[k].mean()), 2) if k.any() else None,
                "model_minus_NP15": round(float((mp[z] - mp["NP15"])[k].mean()), 2)
                if k.any()
                else None,
                "meas_minus_NP15_rt": round(float((h - m["NP15"])[k].mean()), 2)
                if k.any()
                else None,
            }
        yr["legs"] = legs
        # F. the tail congestion hours (measured NP15-SP15 > $100 among tail hours).
        if y == 2024:
            ex = MID & tail & ((m["NP15"] - m["SP15_rest"]) > 100)
            ex_all = tail & ((m["NP15"] - m["SP15_rest"]) > 100)
            rows = []
            pnw = wecc_hub(y, "MALIN")
            dsw = wecc_hub(y, "PALOVRDE")
            for h in np.flatnonzero(ex_all):
                ts = pd.Timestamp(f"{y}-01-01") + pd.Timedelta(hours=int(h))
                rows.append(
                    {
                        "pst": str(ts),
                        "meas": [
                            round(float(m[z][h]), 1)
                            for z in ("NP15", "ZP26", "SP15_rest")
                        ],
                        "model": [
                            round(float(mp[z][h]), 1)
                            for z in ("NP15", "ZP26", "SP15_rest")
                        ],
                        "model_pnw_dsw": [
                            round(float(mp["WECC_PNW"][h]), 1),
                            round(float(mp["WECC_DSW"][h]), 1),
                        ],
                        "meas_malin_pv_dam": [
                            round(float(pnw[h]), 1),
                            round(float(dsw[h]), 1),
                        ],
                        "curt_local_sys_mwh": [
                            round(float(loc[h]), 0),
                            round(float(sysc[h]), 0),
                        ],
                    }
                )
            yr["tail_congestion_hours"] = {"n_mid": int(ex.sum()), "rows": rows}
        res[y] = yr
        print(y, json.dumps({k: yr[k] for k in ("P15_NP_ZP", "P26_ZP_SP")})[:900])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
