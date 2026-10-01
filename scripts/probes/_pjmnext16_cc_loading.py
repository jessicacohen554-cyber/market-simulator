"""PJM-NEXT-16 card 1 (zero LP): what pushes CC LOADING up in 2019/2020/2022/2023?

NEXT-15 split the keeper's CC_REGULAR over-run into on-hours (a constant +2..+8 TWh) and
LOADING when on (+ in the four C1-fail years, - in 2021/2024/2025). This probe
decomposes the loading term and sets it against the system energy ledger, hour by hour.

Sources (all committed, keeper ``2026-09-28-pjm-next8-exitfix``):
- per-plant hourly model MW: registered payload ``runs/<keeper>.js`` (``m`` rescaled to
  ``m_ann``); per-plant CAMPD hourly: ``bench/PJM/<y>.json.gz`` (rescaled to the EIA-923
  net annual) - the NEXT-15 basis;
- model class hourly: ``pjmnext8_xf_span/hourly/class_hourly_<y>.parquet`` (``import`` =
  net seam flow, negative = export); model zonal price/demand: ``system_<y>.parquet``;
- actual hourly: EIA-930 BALANCE, PJM BA (Adjusted demand, total interchange [+ =
  export], coal and gas net generation).

Per CC plant-hour the model-minus-actual gap is partitioned EXACTLY into
  LOAD  (both on:  mod - act),  ON (model on, actual off: mod),  OFF (actual on only: -act),
so every term is hour-attributable. Hour classes: actual PJM demand decile within the year,
and day (HE 08-23 EPT) / night. The model hour index is aligned to EIA-930 local hours by
the lag that maximises the demand correlation (reported).

System ledger per hour: dGAS (model gas family - EIA-930 gas), dCOAL, dEXPORT (model net
export - actual net export), dDEMAND. Writes ``results/calibration/_pjmnext16_cc_loading.json``.
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

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "frontend/data/backcast/bench/PJM"
RUN = REPO / "frontend/data/backcast/runs/2026-09-28-pjm-next8-exitfix.js"
HOURLY = REPO / "results/calibration/pjmnext8_xf_span/hourly"
E930 = REPO / "data/raw/eia-930"
OUT = REPO / "results/calibration/_pjmnext16_cc_loading.json"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
FAIL = (2019, 2020, 2022, 2023)
KLASS = "CC_REGULAR"
ON_FRAC = 0.05
GAS_FAM = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS")
COAL_FAM = ("COAL_BIT", "COAL_PRB", "COAL_WC")
T = 8760


def _payload(path: Path) -> dict:
    """Decode a registered run payload."""
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', path.read_text())
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def _dec(b64: str, ann_twh: float | None) -> np.ndarray:
    """Decode CF-percent bytes and rescale to the annual TWh total (MW per hour)."""
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    tot = raw.sum()
    return raw * (float(ann_twh) * 1e6 / tot) if ann_twh and tot > 0 else raw * 0.0


def _e930(year: int) -> pd.DataFrame:
    """PJM BA hourly from EIA-930 BALANCE, first 8760 local hours of the year."""
    fr = []
    for f in sorted(E930.glob(f"EIA930_BALANCE_{year}_*.parquet")):
        d = pd.read_parquet(f)
        fr.append(d[d["Balancing Authority"] == "PJM"])
    d = pd.concat(fr)
    # UTC -> fixed EST (UTC-5): a continuous 8760-hour axis with no DST gap/repeat.
    d["ts"] = pd.to_datetime(
        d["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p"
    ) - pd.Timedelta(hours=5)
    d = d.sort_values("ts").drop_duplicates("ts")
    d = d[d["ts"] > pd.Timestamp(f"{year}-01-01")]
    col = {
        "demand": "Demand (MW) (Adjusted)",
        "export": "Total Interchange (MW) (Adjusted)",
        "gas": "Net Generation (MW) from Natural Gas (Adjusted)",
        "coal": "Net Generation (MW) from Coal (Adjusted)",
    }
    out = pd.DataFrame(
        {k: pd.to_numeric(d[v], errors="coerce").values for k, v in col.items()}
    )
    out["he"] = d["ts"].dt.hour.values  # hour ENDING (0 == HE24)
    out = out.interpolate(limit_direction="both")
    out = out.iloc[:T].reset_index(drop=True)
    return out.reindex(range(T)).ffill()


def _lag(model: np.ndarray, act: np.ndarray) -> int:
    """Shift (hours) of the actual series that best matches the model demand."""
    best, arg = -2.0, 0
    for k in range(-8, 9):
        r = np.corrcoef(model, np.roll(act, k))[0, 1]
        if r > best:
            best, arg = r, k
    return arg


def _bucket(gap: dict, cls: np.ndarray, labels) -> dict:
    """Sum each hourly term (TWh) over hour classes."""
    return {
        str(lab): {
            k: round(float(v[cls == lab].sum()) / 1e6, 2) for k, v in gap.items()
        }
        for lab in labels
    }


def main() -> None:
    """Census every year; write the JSON artifact.

    Optional argv ``<run.js> <hourly dir> <out.json>`` points the census at another
    registered run (PJM-NEXT-16 arm B's B1 measurement); default is the keeper.
    """
    global RUN, HOURLY, OUT
    if len(sys.argv) == 4:
        RUN, HOURLY, OUT = (Path(a) for a in sys.argv[1:])
    pay = {int(y): rec["plants"] for y, rec in _payload(RUN)["years"].items()}
    res = {
        "what": "PJM-NEXT-16 card 1 - CC loading decomposition. ZERO LP.",
        "years": {},
    }
    for y in YEARS:
        ch = pd.read_parquet(HOURLY / f"class_hourly_{y}.parquet")
        cm = (
            ch[ch["pass"] == "P1"]
            .pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
            .reindex(range(T))
            .fillna(0.0)
        )
        sysd = pd.read_parquet(HOURLY / f"system_{y}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        dm = sysd.groupby("hour").demand.sum().reindex(range(T)).values
        z_price = (
            sysd[sysd.zone != "PJM_external"]
            .pivot_table(index="hour", columns="zone", values="price")
            .reindex(range(T))
        )
        z_dem = (
            sysd[sysd.zone != "PJM_external"]
            .pivot_table(index="hour", columns="zone", values="demand")
            .reindex(range(T))
        )
        lw_price = (z_price * z_dem).sum(axis=1).values / z_dem.sum(axis=1).values
        a = _e930(y)
        lag = _lag(dm, a.demand.values)
        a = a.apply(lambda s: np.roll(s.values, lag))
        dec_edges = np.quantile(a.demand.values, np.linspace(0, 1, 11))
        decile = np.clip(
            np.searchsorted(dec_edges, a.demand.values, side="right") - 1, 0, 9
        )
        he = a.he.values.astype(int)
        day = np.where((he >= 8) & (he <= 23), "day", "night")

        # System ledger (MW per hour).
        gas_m = cm[[c for c in GAS_FAM if c in cm]].sum(axis=1).values
        coal_m = cm[[c for c in COAL_FAM if c in cm]].sum(axis=1).values
        led = {
            "dGAS": gas_m - a.gas.values,
            "dCOAL": coal_m - a.coal.values,
            "dEXPORT": -cm["import"].values - a.export.values,
            "dDEMAND": dm - a.demand.values,
        }

        # CC plant partition.
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
        part = {"LOAD": np.zeros(T), "ON": np.zeros(T), "OFF": np.zeros(T)}
        zone_part: dict[str, dict] = {}
        for pid, bp in bench["plants"].items():
            if bp.get("group") != KLASS or bp.get("nodata") or not bp.get("campd"):
                continue
            npl = float(bp.get("npl") or 0.0)
            kp = pay[y].get(pid, {})
            if npl <= 0 or not kp.get("m"):
                continue
            act = _dec(bp["campd"], bp.get("e_ann") or bp.get("c_ann"))
            mod = _dec(kp["m"], kp.get("m_ann"))
            on_m, on_a = mod > ON_FRAC * npl, act > ON_FRAC * npl
            p = {
                "LOAD": np.where(on_m & on_a, mod - act, 0.0),
                "ON": np.where(on_m & ~on_a, mod, 0.0),
                "OFF": np.where(~on_m & on_a, -act, 0.0),
            }
            z = bp.get("zone", "").replace("PJM_", "")
            zp = zone_part.setdefault(z, {k: np.zeros(T) for k in part})
            for k in part:
                part[k] += p[k]
                zp[k] += p[k]
        load = part["LOAD"]
        both = {**part, **led}
        # Hour-level association of the CC loading term with the ledger.
        corr = {k: round(float(np.corrcoef(load, v)[0, 1]), 3) for k, v in led.items()}
        corr["lw_price"] = round(float(np.corrcoef(load, lw_price)[0, 1]), 3)
        # Where does the hour's thermal over-run go? share of dGAS in (dGAS + dCOAL), hours with over-run.
        dth = led["dGAS"] + led["dCOAL"]
        pos = dth > 0
        rec = {
            "lag_h": lag,
            "annual_twh": {k: round(float(v.sum()) / 1e6, 2) for k, v in both.items()},
            "by_decile": _bucket(both, decile, range(10)),
            "by_daynight": _bucket(both, day, ("day", "night")),
            "by_zone_load": {
                z: round(float(v["LOAD"].sum()) / 1e6, 2)
                for z, v in sorted(zone_part.items())
            },
            "by_zone_load_daynight": {
                z: _bucket({"LOAD": v["LOAD"]}, day, ("day", "night"))
                for z, v in sorted(zone_part.items())
            },
            "hourly_corr_LOAD_with": corr,
            "gas_share_of_thermal_overrun_hours": round(
                float(led["dGAS"][pos].sum() / dth[pos].sum()), 3
            ),
            "lw_price_mean": round(float(np.nanmean(lw_price)), 2),
        }
        res["years"][str(y)] = rec
        at = rec["annual_twh"]
        print(
            y,
            "FAIL" if y in FAIL else "pass",
            f"lag {lag:+d}",
            " ".join(f"{k} {v:+.1f}" for k, v in at.items()),
            f"| gas share {rec['gas_share_of_thermal_overrun_hours']:.2f}",
            f"| corr {corr}",
            flush=True,
        )
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
