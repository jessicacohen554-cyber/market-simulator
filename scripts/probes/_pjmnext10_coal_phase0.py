"""PJM-NEXT-10 zero-LP phase 0: why COAL_BIT over-runs in 2019/2021/2025 and not 2023/2024.

Reads only committed / hydrated artifacts, no LP:

* the keeper run payload ``frontend/data/backcast/runs/<RUN_ID>.js`` (per-plant model
  hourly MW, class energy, EIA-930 fuel rows);
* the bench ``frontend/data/backcast/bench/PJM/<y>.json.gz`` (CAMPD net hourly,
  EIA-923 annual, EIA-930 annual);
* the keeper's committed ``hourly/system_<y>.parquet`` (zonal LP prices);
* CAMPD unit-level hourly (``data/raw/campd-unit-level``, ``--profile pjm``);
* the keeper's outage extracts (``resolved_inputs.campd_unit_outages``);
* EIA-923 coal receipts (``data/raw/coal-receipts``) for the delivered coal price;
* PJM DA hub LMPs (``data/clean/lmp/PJM/DAM``, ``regenerate_clean.py lmp``) and the DA
  binding-constraint record (``fetch_pjm_binding_constraints.py``, gitignored).

Sections (each one a hypothesis for the COAL_BIT level offset, with its result):

1. ``decomposition`` — model − CAMPD on bench COAL_BIT plants, split into energy above
   the capacity CAMPD shows synchronised (availability/commitment) and energy within it
   (loading). Extends PJM-NEXT-7 §2 to all seven years on the current keeper.
2. ``fuel_ratio`` — EIA-923 delivered coal $/MMBtu on the bench plants vs the keeper's
   gas price, against the C1 COAL_BIT residual.
3. ``window_coverage`` — share of dark coal capacity-hours carrying an outage window,
   by actual hub price bin.
4. ``pmax`` — Σ per-plant p99 output, model vs CAMPD.
5. ``aep_western_spread`` — the AEP GEN HUB − WESTERN HUB DA congestion spread
   regressed onto PJM's binding constraints (PJM-NEXT-9 method).
6. ``hour_shape`` — mean GW over-run by hour block and weekday/weekend.
"""

from __future__ import annotations

import base64
import glob
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
import _pjmnext9_congestion_boundary as P9  # noqa: E402

RUN_ID = "2026-09-28-pjm-next8-exitfix"
BUNDLE = REPO / "results/calibration/pjmnext8_xf_span"
BENCH = "frontend/data/backcast/bench/PJM/{y}.json.gz"
OUTAGES = (
    "data/raw/campd-unit-outages-rederive-peakerkeep-exitfix-unitfuel-PJM.csv",
    "data/raw/campd-unit-outages-short-rederive-PJM.csv",
)
OUT = REPO / "results/calibration/_pjmnext10_coal_phase0.json"
YEARS = tuple(range(2019, 2026))
KLASS = "COAL_BIT"
#: Model zone -> the PJM DA hub read as that zone's actual price (nearest published hub).
HUB = {
    "PJM_AEP_Ohio": "AEP GEN HUB",
    "PJM_West_APS": "WESTERN HUB",
    "PJM_ComEd": "CHICAGO GEN HUB",
    "PJM_Dominion": "DOMINION HUB",
    "PJM_EMAAC": "EASTERN HUB",
    "PJM_SWMAAC": "WESTERN HUB",
    "PJM_Central_PA": "WESTERN HUB",
    "PJM_ATSI": "ATSI GEN HUB",
}
PRICE_BINS = (-1e9, 35.0, 50.0, 1e9)


def load_run() -> dict:
    """Decode the registered run payload's per-year block."""
    s = (REPO / f"frontend/data/backcast/runs/{RUN_ID}.js").read_text()
    b64 = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b64)))["years"]


def decode(b64: str, ann: object, npl: float) -> np.ndarray:
    """Decode a CF%-byte 8760 series to MW, rescaled to its annual TWh."""
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    t = raw.sum()
    a = float(ann or 0.0)
    return raw * (a * 1e6 / t) if (a > 0 and t > 0) else raw / 100 * npl


def bench(y: int) -> dict:
    """The benchmark block for one year."""
    return json.load(gzip.open(REPO / BENCH.format(y=y)))["bench"]


def plant_series(y: int, run: dict) -> dict[str, tuple[np.ndarray, np.ndarray, dict]]:
    """``{key: (model MW, CAMPD MW, bench row)}`` for bench COAL_BIT plants."""
    b = bench(y)["plants"]
    mp = run[str(y)]["plants"]
    out = {}
    for k, v in b.items():
        if v["group"] != KLASS or k not in mp or v.get("nodata"):
            continue
        npl = v["npl"]
        out[k] = (
            decode(mp[k]["m"], mp[k]["m_ann"], npl),
            decode(v["campd"], v["c_ann"], npl),
            v,
        )
    return out


def campd_units(y: int, fids: set[int]) -> pd.DataFrame:
    """Coal-unit CAMPD hourly rows (hour-of-year ``t``, unit p99 gross ``cap``)."""
    parts = []
    cols = ["facilityId", "unitId", "date", "hour", "opTime", "grossLoad"]
    for f in glob.glob(str(REPO / f"data/raw/campd-unit-level/*_{y}.parquet")):
        d = pd.read_parquet(f, columns=[*cols, "primaryFuelInfo"])
        d = d[
            d.facilityId.astype(int).isin(fids)
            & d.primaryFuelInfo.fillna("").str.contains("Coal")
        ]
        if len(d):
            parts.append(d[cols])
    u = pd.concat(parts, ignore_index=True)
    u["facilityId"] = u.facilityId.astype(int)
    u["unitId"] = u.unitId.astype(str).str.strip()
    u["ts"] = pd.to_datetime(u.date) + pd.to_timedelta(u.hour, "h")
    u["t"] = ((u.ts - pd.Timestamp(f"{y}-01-01")) / pd.Timedelta("1h")).astype(int)
    u = u[u.t < 8760]
    cap = u.groupby(["facilityId", "unitId"]).grossLoad.quantile(0.99).rename("cap")
    u = u.join(cap, on=["facilityId", "unitId"])
    u = u[u.cap > 0].copy()
    u["on"] = u.opTime.fillna(0) > 0
    return u


def hub_prices(y: int) -> pd.DataFrame:
    """Hour x hub DA LMP (first 8760 local-year hours)."""
    a = pd.read_parquet(
        REPO / f"data/clean/lmp/PJM/DAM/lmp_{y}.parquet",
        columns=["interval_start_utc", "node", "lmp_usd_per_mwh"],
    )
    return a.pivot_table(
        index="interval_start_utc", columns="node", values="lmp_usd_per_mwh"
    ).iloc[:8760]


def decomposition(y: int, ps: dict, u: pd.DataFrame) -> dict:
    """Model − CAMPD split into above-synced (availability) and within-synced (loading)."""
    syn = (
        (u.on * u.cap).groupby([u.t, u.facilityId]).sum().unstack().reindex(range(8760))
    )
    gross = (
        u.groupby([u.t, u.facilityId]).grossLoad.sum().unstack().reindex(range(8760))
    )
    syn, gross = syn.fillna(0.0), gross.fillna(0.0)
    above = within = no_cems = total = 0.0
    for k, (m, c, _v) in ps.items():
        fid = int(k.split(":")[0])
        total += (m - c).sum()
        if fid not in syn.columns or gross[fid].sum() <= 0:
            no_cems += (m - c).sum()
            continue
        sc = syn[fid].to_numpy() * c.sum() / gross[fid].sum()  # net/gross
        a = np.maximum(0.0, m - sc).sum()
        above += a
        within += m.sum() - a - c.sum()
    return {
        "total": round(total / 1e6, 2),
        "above_synced": round(above / 1e6, 2),
        "within_synced_loading": round(within / 1e6, 2),
        "no_cems": round(no_cems / 1e6, 2),
    }


def coal_price(y: int, fids: set[int]) -> float | None:
    """MMBtu-weighted EIA-923 delivered coal price on the bench plants ($/MMBtu)."""
    p = REPO / f"data/raw/coal-receipts/coal_receipts_{y}.csv"
    if not p.exists():
        return None
    d = pd.read_csv(p, low_memory=False)
    d = d[d["Plant Id"].astype(float).isin(fids) & (d.FUEL_GROUP == "Coal")]
    d = d.assign(FUEL_COST=pd.to_numeric(d.FUEL_COST, errors="coerce")).dropna(
        subset=["FUEL_COST"]
    )
    mm = d.QUANTITY * d["Average Heat Content"]
    return round(float((d.FUEL_COST * mm).sum() / mm.sum() / 100), 3)


def window_coverage(y: int, ps: dict, u: pd.DataFrame, lmp: pd.DataFrame) -> list:
    """Share of dark (opTime=0) coal capacity-hours carrying an outage window, by price."""
    w = pd.concat([pd.read_csv(REPO / f) for f in OUTAGES], ignore_index=True)
    w["unit_id"] = w.unit_id.astype(str).str.strip()
    on_h = u.groupby(["facilityId", "unitId"]).on.transform("sum")
    x = u[on_h > 0].copy()  # dark-all-year units are the exit cohort (PJM-NEXT-8)
    x["win"] = False
    for r in w[w.facility_id.isin(set(x.facilityId))].itertuples():
        s = pd.Timestamp(r.outage_start)
        e = pd.Timestamp(r.outage_end) + pd.Timedelta("1D")
        m = (
            (x.facilityId == r.facility_id)
            & (x.unitId == r.unit_id)
            & (x.ts >= s)
            & (x.ts < e)
        )
        x.loc[m, "win"] = True
    zone = {int(k.split(":")[0]): v["zone"] for k, (_m, _c, v) in ps.items()}
    x = x[x.facilityId.map(zone).isin(HUB)]
    hub_of = x.facilityId.map(zone).map(HUB)
    x["p"] = [lmp[h].to_numpy()[t] for h, t in zip(hub_of, x.t, strict=True)]
    rows = []
    for lo, hi in zip(PRICE_BINS[:-1], PRICE_BINS[1:], strict=True):
        b = x[(x.p > lo) & (x.p <= hi)]
        dark = (b.cap * ~b.on).sum()
        dw = (b.cap * (~b.on & b.win)).sum()
        rows.append(
            {
                "bin": f"({lo:g},{hi:g}]",
                "dark_pct_of_cap": round(100 * dark / b.cap.sum(), 1),
                "windowed_pct_of_dark": round(100 * dw / max(dark, 1.0), 1),
                "unwindowed_dark_twh": round((dark - dw) / 1e6, 2),
            }
        )
    return rows


def pmax(ps: dict) -> dict:
    """Σ per-plant p99 output, model vs CAMPD (plants with ≥ 0.3 TWh actual)."""
    sm = sa = 0.0
    for m, c, _v in ps.values():
        if c.sum() < 0.3e6:
            continue
        sm += np.percentile(m, 99)
        sa += np.percentile(c, 99)
    return {
        "model_mw": round(sm),
        "campd_mw": round(sa),
        "pct": round(100 * (sm / sa - 1), 1),
    }


def hour_shape(y: int, ps: dict) -> dict:
    """Mean GW over-run (model − CAMPD) by hour block and weekday/weekend."""
    d = sum(m - c for m, c, _v in ps.values()) / 1e3
    idx = pd.date_range(f"{y}-01-01", periods=8760, freq="h")
    s = pd.Series(d, index=idx)
    h = s.groupby(idx.hour).mean()
    wk = s.groupby(idx.dayofweek >= 5).mean()
    return {
        "mean_gw": round(float(s.mean()), 2),
        "night_00_05": round(float(h.iloc[0:6].mean()), 2),
        "day_10_19": round(float(h.iloc[10:20].mean()), 2),
        "weekday": round(float(wk[False]), 2),
        "weekend": round(float(wk[True]), 2),
    }


def aep_western_spread(y: int) -> dict:
    """AEP GEN HUB − WESTERN HUB DA congestion spread onto binding constraints."""
    mu = P9.load_mu(y)
    hub = P9.load_hubs(y)
    mu = mu.reindex(hub.index).fillna(0.0)
    keep = mu.abs().sum().sort_values(ascending=False).index[: P9.N_TOP]
    x = mu[keep].to_numpy()
    s = (hub["AEP GEN HUB"] - hub["WESTERN HUB"]).to_numpy()
    ok = np.isfinite(s)
    beta, *_ = np.linalg.lstsq(x[ok], s[ok], rcond=None)
    fit = x[ok] @ beta
    r2 = 1 - ((s[ok] - fit) ** 2).sum() / ((s[ok] - s[ok].mean()) ** 2).sum()
    c = pd.Series(beta * x[ok].mean(axis=0), index=keep)
    fac = c.groupby(keep.str.split(" | ", regex=False).str[0]).sum()
    fac = fac.reindex(fac.abs().sort_values(ascending=False).index)
    return {
        "mean_spread": round(float(s[ok].mean()), 3),
        "r2": round(float(r2), 3),
        "top_facilities": {k: round(float(v), 3) for k, v in fac.iloc[:6].items()},
    }


def main() -> None:
    """Run every section for 2019–2025 and write the JSON record."""
    run = load_run()
    rec: dict = {"run_id": RUN_ID, "years": {}}
    for y in YEARS:
        ps = plant_series(y, run)
        fids = {int(k.split(":")[0]) for k in ps}
        u = campd_units(y, fids)
        lmp = hub_prices(y)
        cf = bench(y)["classFull"]
        gm = run[str(y)]["gmModel"]
        gas = json.loads((BUNDLE / f"run_config_{y}.json").read_text())[
            "calibration_flags"
        ]["gas_prices"][str(y)]
        coal = coal_price(y, fids)
        rec["years"][str(y)] = {
            "c1_coal_bit_twh": round(gm[KLASS] - cf[KLASS], 2),
            "decomposition": decomposition(y, ps, u),
            "fuel_ratio": {
                "gas": gas,
                "coal_delivered": coal,
                "coal_over_gas": round(coal / gas, 3) if coal else None,
            },
            "window_coverage": window_coverage(y, ps, u, lmp),
            "pmax": pmax(ps),
            "hour_shape": hour_shape(y, ps),
            "aep_western_spread": aep_western_spread(y),
        }
        r = rec["years"][str(y)]
        print(
            y,
            f"C1 {r['c1_coal_bit_twh']:+.2f}",
            r["decomposition"],
            r["fuel_ratio"],
            f"pmax {r['pmax']['pct']:+.1f}%",
            f"AEP-W {r['aep_western_spread']['mean_spread']:+.2f}",
        )
    OUT.write_text(json.dumps(rec, indent=1))
    print("wrote", OUT.relative_to(REPO))


if __name__ == "__main__":
    sys.exit(main())
