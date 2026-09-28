"""R-CAISO-12 (ZERO LP): the "h15-17 import surplus" and the 2019-21 fold.

R-CAISO-11 handed on: "in Jun-Sep 2022-25 at h15-17 the model imports +1.0-2.1 GW
more than EIA-930 (-TI) and runs 3-5 GW less gas". This probe re-measures both
halves on the bases the scorer and the model actually use, then names the
import tranche that carries the residual, and tests one candidate source for
the 2019-20 hub-price STOP.

Sections written to ``results/calibration/_rcaiso12/import_census.json``:

* ``imports`` -- model net import into the five CAISO zones (zone demand minus
  every in-CAISO class and storage net) against EIA-930 CISO interchange per
  DIBA, both on the model's fixed-PST hour-beginning clock
  (``envelopes._caiso_interchange_model_clock``), per corridor, Jun-Sep by hod.
* ``gas_cems`` -- model gas vs the MEASURED gas basis C4 scores on
  (bench ``plants[].campd`` for the CEMS gas fleet), Jun-Sep by hod. The
  EIA-930 CISO NG cell is NOT used: it is registered corrupt
  (``benchmark_semantics.EIA930_NG_CELL_CORRUPT``).
* ``tranches`` -- per import tranche P1 dispatch, Jun-Sep by hod, read from the
  keeper's per-year legs (``unit_hourly``), and annual corridor totals vs
  EIA-930 for every year 2019-2025 (the fold question).
* ``spread`` -- model zonal price minus the measured intertie DAM LMP the
  import offers are built on, against the import residual, by hod.
* ``ice`` -- the EIA-published ICE daily on-peak Palo Verde / Mid-C indices
  against the committed OASIS intertie DAM on-peak mean, 2021-2025 overlap.

Inputs: the keeper's committed composites (``rcaiso11_A_span`` and the fold
``rcaiso11_A_tp_2019_2021`` registry payload + bench), and the per-year legs,
which are NOT on ``main`` (rule 32(d)); extract them with
``git archive <leg sha> results/calibration/rcaiso11_A_<y>/hourly/unit_hourly_<y>.parquet``
into ``--legs-root`` (leg SHAs: RESULT-r-caiso-11 section 7, provenance only,
rule 33(d)). ICE workbooks: ``https://www.eia.gov/electricity/wholesale/xls/
archive/ice_electric-<y>final.xlsx`` into ``--ice-dir`` (scratch; not a data
intake).

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso12_import_census.py \
        --legs-root <dir> --ice-dir <dir>
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts"]
import calibration_verdict as cv  # noqa: E402
from market_sim.config.interchange_config import CAISO_CORRIDOR_DIBA  # noqa: E402
from market_sim.data.eia930.envelopes import (  # noqa: E402
    _caiso_interchange_model_clock,
)
from market_sim.data.eia_loader import measured_import_hub_prices  # noqa: E402

KEEPER = "2026-09-28-caiso-r11-tacpst"
FOLD = "2026-09-28-caiso-r11-tacpst-touchpoints"
SPAN = Path("results/calibration/rcaiso11_A_span/hourly")
TI = Path("data/raw/eia-930-interchange/CISO interchange hourly.parquet")
WECC_LMP = Path("data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet")
OUT = Path("results/calibration/_rcaiso12/import_census.json")
T = 8760
HODS = [3, 8, 10, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22]
GAS = ["CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS"]
CAISO_ZONES = ["NP15", "ZP26", "SP15_rest", "LA_BASIN", "SDGE"]
SUMMER = (6, 9)  # Jun-Sep, the R-CAISO-11 window


def _idx(y: int) -> pd.DatetimeIndex:
    """Model clock: fixed-PST hour-beginning, 8,760 h."""
    return pd.date_range(f"{y}-01-01", periods=T, freq="h")


def _by_hod(df: pd.DataFrame, y: int, scale: float = 1e-3) -> dict:
    """Jun-Sep hour-of-day means of every column, rounded (GW when scale=1e-3)."""
    idx = _idx(y)
    m = (idx.month >= SUMMER[0]) & (idx.month <= SUMMER[1])
    g = df[m].groupby(idx[m].hour).mean() * scale
    return {c: {int(h): round(float(g.at[h, c]), 3) for h in HODS} for c in g}


def _ti() -> pd.DataFrame:
    """EIA-930 CISO per-DIBA interchange on the model clock, with corridor."""
    ti = pd.read_parquet(TI)
    ti["ts"] = _caiso_interchange_model_clock(pd.DatetimeIndex(ti["local_time"]))
    ti["cor"] = ti["diba"].astype(str).map(CAISO_CORRIDOR_DIBA)
    return ti


def _model_net_import(y: int) -> np.ndarray:
    """Model net import into the CAISO zones = zone demand - in-CAISO supply."""
    c = pd.read_parquet(SPAN / f"class_hourly_{y}.parquet")
    c = c[c["pass"] == "P1"]
    p = c.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
    p = p.reindex(range(T)).fillna(0.0)
    s = pd.read_parquet(SPAN / f"system_{y}.parquet")
    s = s[(s["pass"] == "P1") & s["zone"].isin(CAISO_ZONES)]
    dem = s.groupby("hour")["demand"].sum().reindex(range(T)).to_numpy()
    st = pd.read_parquet(SPAN / f"storage_{y}.parquet")
    st = st[st["pass"] == "P1"]
    stn = (st["discharge_mw"] - st["charge_mw"]).groupby(st["hour"]).sum()
    stn = stn.reindex(range(T)).fillna(0.0).to_numpy()
    return dem - (p.drop(columns=["import"]).sum(axis=1).to_numpy() + stn)


def imports(ti: pd.DataFrame) -> dict:
    """Model vs EIA-930 net import, total and per corridor, Jun-Sep by hod."""
    out = {}
    for y in (2022, 2023, 2024, 2025):
        idx = _idx(y)
        e = ti[ti["ts"].dt.year == y]
        per = -e.pivot_table(index="ts", columns="cor", values="mw", aggfunc="sum")
        per = per.reindex(idx)
        df = pd.DataFrame(
            {
                "model": _model_net_import(y),
                "eia930": per.sum(axis=1, min_count=1).to_numpy(),
                "eia930_PNW": per["WECC_PNW"].to_numpy(),
                "eia930_DSW": per["WECC_DSW"].to_numpy(),
            },
            index=idx,
        )
        df["model_minus_eia930"] = df["model"] - df["eia930"]
        out[y] = _by_hod(df, y)
    return out


def _b64(s: str, cap: float) -> np.ndarray:
    return np.frombuffer(base64.b64decode(s)[:T], np.uint8) * cap / 100.0


def gas_cems() -> dict:
    """Model gas vs CEMS gas (C4's measured basis), CEMS-covered plants only."""
    out = {}
    for rid, years in ((KEEPER, (2022, 2023, 2024, 2025)), (FOLD, (2019, 2020, 2021))):
        art = cv.load_artifacts(rid)
        for y in years:
            yb, yp = art["bench"][y], art["payload"]["years"][str(y)]
            m, a = np.zeros(T), np.zeros(T)
            for code, bp in yb["plants"].items():
                if bp.get("group") not in cv.GAS_CLASSES or bp.get("nodata"):
                    continue
                pp = yp["plants"].get(str(code))
                cap = float(bp.get("npl") or 0.0)
                if cap <= 0 or not bp.get("campd") or not pp or not pp.get("m"):
                    continue
                a += _b64(bp["campd"], cap)
                m += _b64(pp["m"], cap)
            df = pd.DataFrame({"model": m, "cems": a}, index=_idx(y))
            df["model_minus_cems"] = df["model"] - df["cems"]
            out[y] = _by_hod(df, y)
    return out


def tranches(legs_root: Path, ti: pd.DataFrame) -> dict:
    """Per import tranche dispatch by hod; annual corridor totals vs EIA-930."""
    out = {}
    for y in range(2019, 2026):
        path = (
            legs_root
            / f"results/calibration/rcaiso11_A_{y}/hourly/unit_hourly_{y}.parquet"
        )
        if not path.exists():
            continue
        u = pd.read_parquet(
            path, filters=[("pass", "==", "P1")], columns=["unit_id", "hour", "mw"]
        )
        u = u[u["unit_id"].astype(str).str.startswith("WECC_")].copy()
        uid = u["unit_id"].astype(str)
        u["tr"] = uid.str.replace(r"^WECC_(PNW|DSW)_", "", regex=True)
        u["cor"] = uid.str.extract(r"^(WECC_(?:PNW|DSW))")[0]
        w = u.pivot_table(index="hour", columns="tr", values="mw", aggfunc="sum")
        w = w.reindex(range(T)).fillna(0.0)
        w.index = _idx(y)
        e = ti[ti["ts"].dt.year == y]
        out[y] = {
            "jun_sep_by_hod_gw": _by_hod(w.loc[:, (w != 0).any()], y),
            "annual_twh": {
                "tranche": {
                    k: round(float(v) / 1e6, 3)
                    for k, v in u.groupby("tr")["mw"].sum().items()
                    if abs(v) > 1e3
                },
                "model_PNW": round(float(u[u.cor == "WECC_PNW"].mw.sum()) / 1e6, 2),
                "model_DSW": round(float(u[u.cor == "WECC_DSW"].mw.sum()) / 1e6, 2),
                "eia930_PNW": round(float(-e[e.cor == "WECC_PNW"].mw.sum()) / 1e6, 2),
                "eia930_DSW": round(float(-e[e.cor == "WECC_DSW"].mw.sum()) / 1e6, 2),
            },
        }
    return out


def spread(ti: pd.DataFrame) -> dict:
    """Model price minus the measured intertie DAM LMP vs the import residual."""
    out = {}
    for y in (2022, 2023, 2024, 2025):
        hubs = measured_import_hub_prices("CAISO", y, T) or {}
        hub = np.nanmean(
            np.vstack([np.asarray(hubs[k]) for k in ("PNW_midC", "DSW_CCGT")]), axis=0
        )
        s = pd.read_parquet(SPAN / f"system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        zp = s.pivot(index="hour", columns="zone", values="price").reindex(range(T))
        idx = _idx(y)
        eia = -ti[ti["ts"].dt.year == y].groupby("ts")["mw"].sum().reindex(idx)
        df = pd.DataFrame(
            {
                "price_minus_hub": zp[["NP15", "SP15_rest"]].mean(axis=1).to_numpy()
                - hub,
                "import_residual": _model_net_import(y) - eia.to_numpy(),
            },
            index=idx,
        )
        ok = df.notna().all(axis=1)
        hod = df[ok].groupby(idx[ok].hour).mean()
        out[y] = {
            "r_hourly": round(float(df[ok].corr().iloc[0, 1]), 3),
            "r_hod_profile": round(float(hod.corr().iloc[0, 1]), 3),
            "by_hod": {
                "price_minus_hub": {
                    int(h): round(float(hod.at[h, "price_minus_hub"]), 2) for h in HODS
                },
                "import_residual_gw": {
                    int(h): round(float(hod.at[h, "import_residual"]) / 1e3, 3)
                    for h in HODS
                },
            },
        }
    return out


def ice(ice_dir: Path) -> dict | None:
    """ICE daily on-peak index vs the committed OASIS intertie DAM on-peak mean."""
    files = sorted(ice_dir.glob("ice_*.xlsx"))
    if not files:
        return None
    x = pd.concat([pd.read_excel(f) for f in files])
    x["d"] = pd.to_datetime(x["Delivery start date"])
    x = x[x["d"] == pd.to_datetime(x["Delivery \nend date"])]
    w = pd.read_parquet(WECC_LMP)
    out = {}
    for hub, name in (("PALOVRDE", "Palo Verde Peak"), ("MALIN", "Mid C Peak")):
        parts = []
        for y, g in w[w["hub"] == hub].groupby("year"):
            ts = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(g["hour"], "h")
            loc = (
                pd.DatetimeIndex(ts)
                .tz_localize("Etc/GMT+8")
                .tz_convert("America/Los_Angeles")
            ) + pd.Timedelta(hours=1)  # hour-ending, prevailing time
            he = np.where(loc.hour == 0, 24, loc.hour)
            on = (he >= 7) & (he <= 22) & (loc.dayofweek < 6)  # WECC on-peak
            parts.append(
                pd.Series(g["price"].to_numpy()[on], index=loc.date[on])
                .groupby(level=0)
                .mean()
            )
        oas = pd.concat(parts)
        oas.index = pd.to_datetime(oas.index)
        oas = oas.groupby(level=0).mean()
        ic = x[x["Price hub"] == name].groupby("d")["Wtd avg price $/MWh"].mean()
        j = pd.concat([oas.rename("oasis"), ic.rename("ice")], axis=1, sort=True)
        j = j.dropna()
        out[hub] = {
            "ice_days_by_year": {
                int(y): int((ic.index.year == y).sum()) for y in range(2019, 2026)
            },
            "overlap": {
                int(y): {
                    "n": len(g),
                    "r": round(float(np.corrcoef(g.oasis, g.ice)[0, 1]), 3),
                    "ice_minus_oasis": round(float((g.ice - g.oasis).mean()), 2),
                    "ratio": round(float(g.ice.mean() / g.oasis.mean()), 3),
                }
                for y, g in j.groupby(j.index.year)
            },
        }
    return out


def main() -> None:
    """Run every section and write the census JSON."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--legs-root", type=Path, required=True)
    ap.add_argument("--ice-dir", type=Path, required=True)
    a = ap.parse_args()
    ti = _ti()
    res = {
        "keeper": KEEPER,
        "fold": FOLD,
        "window": "Jun-Sep, model clock (fixed-PST hour-beginning); GW unless named",
        "imports": imports(ti),
        "gas_cems": gas_cems(),
        "tranches": tranches(a.legs_root, ti),
        "spread": spread(ti),
        "ice": ice(a.ice_dir),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
