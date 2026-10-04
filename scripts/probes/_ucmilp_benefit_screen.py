"""UC-0 benefit screen (ZERO LP): which ISO-years would a MILP unit-commitment stage move most?

Spec: ``docs/records/governance/uc-milp-2026-10/GATESPEC-uc-milp-testing-protocol-2026-10-03.md``
section 1-2. Thresholds, ranking and selection rules and every physics parameter were fixed
BEFORE this probe produced a number in
``docs/records/governance/uc-milp-2026-10/PREDECL-uc-milp-benefit-screen-2026-10-03.md``
(PREDECL section 2 readings R-a..R-j, section 3 physics table, section 4 inputs).

Per keeper ISO-year (committed bundles only, ``frontend/data/backcast/keepers/<ISO>.json``),
for the slow-start classes CC_REGULAR / COAL_* / ST_GAS (``*_CHP`` excluded):

* M1  physics-violating cycling: plant on/off from the keeper's P1 dispatch (on = output >= 1 %
      of available capacity, SPP-97); energy inside on-runs shorter than the class min-up, off-gaps
      shorter than min-down, keeper starts vs CEMS starts (bench ``campd`` series, on = CF >= 5 %).
* M2  part-load online gap: (a) CEMS online at <= (mlf+0.10) x nameplate while the keeper is off
      -> TWh at min-load (mlf x model available capacity); (b) keeper on at <= (mlf+0.10) x
      available capacity while CEMS is off -> keeper TWh.
* M3  trough price residual: model demand-weighted system price vs actual RT by actual-price
      tercile; lower-tercile mean error x hours ($.h); model/actual count ratios <= $15 and < $0.
* M4  reserve dormancy: share of hours with reserve MCP < $1, model (bundle reserve duals) vs the
      ISO's measured AS clearing price; gap = model dormancy - actual dormancy.
* M5  price-taker DP bound (``_spp102_commit_dp.py`` generalized): per plant, exact on/off DP
      with min-up / min-down, start cost and no-load cost against the keeper's own P1 zonal price,
      (i) perfect foresight, (ii) 36-h rolling windows committing 24 h.  An UPPER bound on the
      economic commitment effect at fixed prices.
* M6  cluster census: integer clusters (plants) per class, MW, integers per 36-h window.

Then the board: S1 = |M3 lower-tercile $.h| on cells failing C3a or C3b (``calibration_verdict``
on the committed bundle), S2 = M2(a)+M2(b) TWh, tiebreak M1; eligible iff S2 >= 1.0 TWh or
M4 gap >= 0.20; selection = top 3 eligible failing cells by S1 + the two controls.

Reads only committed bundles and ``data/raw`` actuals; writes
``results/phase0/xiso/_ucmilp_benefit_screen.json``.  No LP is built or solved.
Run: ``uv run python scripts/probes/_ucmilp_benefit_screen.py [ISO ...]``
"""

from __future__ import annotations

import base64
import glob
import gzip
import io
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from market_sim.config.constants import (  # noqa: E402
    CC_COMMITMENT_PARAMS,
    MIN_STABLE_PCT_PHYSICAL,
    SPP_POSTURE_MIN_DOWN_HOURS,
    ST_GAS_COMMITMENT_PARAMS,
)
from market_sim.data.eia923 import (  # noqa: E402
    EIA923_MONTHLY_COSTS_PATH,
    load_monthly_fuel_costs,
)
from market_sim.data.fleet.eia860 import (  # noqa: E402
    BIN_STARTUP_COST_PER_MW,
    COAL_BIN_MIN_DOWN_HOURS,
    COAL_BIN_MIN_RUN_HOURS,
)

RAW = REPO / "data/raw"
VAL = RAW / "_validation-source"
PROC = RAW / "_processed-legacy"
CEMS = RAW / "campd-unit-level"
OUT = REPO / "results/phase0/xiso/_ucmilp_benefit_screen.json"
T = 8760
ISOS = ["ERCOT", "PJM", "CAISO", "NYISO", "NEISO", "MISO", "SPP", "SOCO", "NWPP"]
COAL = ("COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC")
SLOW = ("CC_REGULAR", "ST_GAS") + COAL
FLOOR_KINDS = ("mustrun", "sync")
ON_MODEL = 0.01  # share of available capacity (SPP-97), PREDECL R-f
ON_CEMS = 5  # % of nameplate (SPP-97), PREDECL R-f
PMIN_BAND = 0.10  # M2 "pmin-ish" band above mlf, PREDECL R-e
LOW_PRICE = 15.0  # $/MWh, M3 count ratio
MCP_DORMANT = 1.0  # $/MW-h, M4
WINDOW_H, COMMIT_H = 36, 24  # plan section 4 E2
CONTROLS = (("NEISO", 2023), ("NYISO", 2024))
GATE_C3A, GATE_C3B = 0.10, 0.20  # rubric bands read off the verdict records
ELIG_S2_TWH, ELIG_M4_GAP, TOP_N = 1.0, 0.20, 3  # GATESPEC section 1, verbatim

# PREDECL section 3 physics table ---------------------------------------------------------
_CC_F = next(d for cut, d in CC_COMMITMENT_PARAMS if cut == 7.5)  # NREL f-class row
_ST_EFF = next(d for cut, d in ST_GAS_COMMITMENT_PARAMS if cut == 10.0)  # efficient steam
CC_UT_MEASURED = {"SPP": 15, "PJM": 11, "MISO": 14, "CAISO": 13, "NYISO": 21}
ST_UT_MEASURED = {"SPP": 5, "PJM": 11, "MISO": 9, "CAISO": 10, "NYISO": 13}
CC_MLF_ISO = {
    "SPP": 0.209,
    "PJM": 0.436,
    "MISO": 0.324,
    "CAISO": 0.259,
    "ERCOT": 0.574,
    "NYISO": 0.523,
}
ST_MLF_ISO = {"SPP": 0.090, "PJM": 0.128, "MISO": 0.107, "CAISO": 0.104, "NYISO": 0.239}


def physics(iso: str, group: str) -> dict:
    """(S $/MW, UT h, DT h, class mlf) for an ISO x class, PREDECL section 3."""
    if group == "CC_REGULAR":
        return dict(
            S=float(BIN_STARTUP_COST_PER_MW["CC_REGULAR"]),
            UT=int(CC_UT_MEASURED.get(iso, _CC_F["min_run_hours"])),
            DT=int(SPP_POSTURE_MIN_DOWN_HOURS if iso == "SPP" else _CC_F["min_down_hours"]),
            mlf=float(CC_MLF_ISO.get(iso, MIN_STABLE_PCT_PHYSICAL["CC_REGULAR"])),
        )
    if group == "ST_GAS":
        return dict(
            S=float(BIN_STARTUP_COST_PER_MW["ST_GAS"]),
            UT=int(ST_UT_MEASURED.get(iso, _ST_EFF["min_run_hours"])),
            DT=int(_ST_EFF["min_down_hours"]),
            mlf=float(ST_MLF_ISO.get(iso, MIN_STABLE_PCT_PHYSICAL["ST_GAS"])),
        )
    return dict(
        S=float(BIN_STARTUP_COST_PER_MW[group]),
        UT=int(COAL_BIN_MIN_RUN_HOURS),
        DT=int(COAL_BIN_MIN_DOWN_HOURS),
        mlf=float(MIN_STABLE_PCT_PHYSICAL[group]),
    )


# ---------------------------------------------------------------- committed inputs ----
def keepers() -> dict[str, dict]:
    """ISO -> {run_id, bundle path, years} from the committed keeper shards + registry."""
    out = {}
    for iso in ISOS:
        k = json.load(open(REPO / f"frontend/data/backcast/keepers/{iso}.json"))["keeper"]
        reg = json.load(open(REPO / f"frontend/data/backcast/registry/{k}.json"))
        bundle = REPO / reg["bundle"]
        years = sorted(
            int(Path(f).stem.rsplit("_", 1)[-1])
            for f in glob.glob(str(bundle / "hourly/unit_marginal_*.parquet"))
        )
        out[iso] = {"run_id": k, "bundle": bundle, "years": years}
    return out


def load_slow_units(bundle: Path, y: int) -> pd.DataFrame:
    """P1 unit-hours of the slow-start classes from the committed slim layer."""
    t = pq.read_table(
        bundle / f"hourly/unit_marginal_{y}.parquet",
        columns=["unit_id", "plant_code", "plant_group", "zone", "hour", "mw", "cap_mw", "mc"],
        filters=[("plant_group", "in", list(SLOW))],
    ).to_pandas()
    for c in ("unit_id", "plant_group", "zone"):
        t[c] = t[c].astype(str)
    t["kind"] = (
        t["unit_id"].str.rsplit("_", n=1).str[-1].str.replace(r"\d+$", "", regex=True)
    )
    return t


def plant_blocks(um: pd.DataFrame) -> dict[int, dict]:
    """plant_code -> {group, zone, kinds, MW/CAP/MC (k, T)}."""
    out = {}
    for pc, g in um.groupby("plant_code", sort=True):
        tr = []
        for _, gu in g.groupby("unit_id", sort=True):
            h = gu["hour"].to_numpy()
            mw, cap, mc = np.zeros(T), np.zeros(T), np.full(T, np.nan)
            mw[h], cap[h], mc[h] = gu["mw"], gu["cap_mw"], gu["mc"]
            tr.append((str(gu["kind"].iloc[0]), mw, cap, mc))
        out[int(pc)] = {
            "group": str(g["plant_group"].iloc[0]),
            "zone": str(g["zone"].iloc[0]),
            "kinds": np.array([t[0] for t in tr]),
            "MW": np.vstack([t[1] for t in tr]),
            "CAP": np.vstack([t[2] for t in tr]),
            "MC": np.vstack([t[3] for t in tr]),
        }
    return out


def system_price(bundle: Path, y: int) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    """Zonal P1 price, demand-weighted system price (external zones excluded), demand."""
    s = pd.read_parquet(
        bundle / f"hourly/system_{y}.parquet", columns=["zone", "hour", "price", "demand"]
    )
    s["zone"] = s["zone"].astype(str)
    zp = {
        z: g.set_index("hour")["price"].reindex(range(T)).to_numpy(float)
        for z, g in s.groupby("zone")
    }
    core = s[~s["zone"].str.contains("_external|_ext_", regex=True)]
    pv = core.pivot(index="hour", columns="zone", values="price").reindex(range(T))
    dv = core.pivot(index="hour", columns="zone", values="demand").reindex(range(T))
    dem = dv.sum(axis=1).to_numpy(float)
    psys = (pv * dv).sum(axis=1).to_numpy(float) / np.where(dem > 0, dem, np.nan)
    return zp, psys, dem


def model_reserve_mcp(bundle: Path, y: int) -> np.ndarray:
    """Model reserve MCP per hour: max over zonal reserve_price and reserve-family duals."""
    s = pd.read_parquet(bundle / f"hourly/system_{y}.parquet", columns=["hour", "reserve_price"])
    mcp = s.groupby("hour")["reserve_price"].max().reindex(range(T)).fillna(0.0).to_numpy()
    rf = bundle / f"hourly/reserve_family_{y}.parquet"
    if rf.exists():
        r = pd.read_parquet(rf, columns=["hour", "dual"])
        d = r.groupby("hour")["dual"].max().reindex(range(T)).fillna(0.0).to_numpy()
        mcp = np.maximum(mcp, d)
    return np.maximum(mcp, 0.0)


def actual_rt(iso: str, y: int) -> np.ndarray | None:
    """Actual RT hourly system price on the model clock (NaN where absent)."""
    f = VAL / f"actual_lmp_hourly_{iso}.parquet"
    if not f.exists():
        return None
    a = pd.read_parquet(f)
    a = a[a["year"] == y]
    if a.empty:
        return None
    return a.set_index("hour")["rt"].reindex(range(T)).to_numpy(float)


def bench_cems(iso: str, y: int) -> dict[int, dict]:
    """plant_code -> {group, npl MW, cf (% of nameplate, uint8 -> float, T)} for slow classes."""
    f = REPO / f"frontend/data/backcast/bench/{iso}/{y}.json.gz"
    if not f.exists():
        return {}
    b = json.load(gzip.open(f))["bench"]["plants"]
    out = {}
    for k, v in b.items():
        if v.get("group") not in SLOW or not v.get("campd") or v.get("nodata") in (True, "True"):
            continue
        cf = np.frombuffer(base64.b64decode(v["campd"]), dtype=np.uint8).astype(float)
        if len(cf) != T:
            continue
        out[int(str(k).split(":")[0])] = {
            "group": v["group"],
            "npl": float(v["npl"]),
            "cf": cf,
        }
    return out


def committed_pct(iso: str) -> dict[int, float]:
    """Per-plant measured min-load share (CAMPD loading-when-on p5) where the ISO carries one."""
    f = PROC / f"thermal_tranches_{iso}.csv"
    if not f.exists():
        return {}
    t = pd.read_csv(f)
    t = t[t["committed_pct"].notna() & (t["committed_pct"] > 0)]
    return {int(r.plant_code): float(r.committed_pct) / 100.0 for r in t.itertuples()}


# -------------------------------------------------------------------- no-load cost ----
_FAC_STATE: dict[int, dict[str, str]] = {}


def facility_states(y: int) -> dict[str, str]:
    """CAMPD facilityId -> state for the year (one scan of the facilityId column per file)."""
    if y not in _FAC_STATE:
        m = {}
        for f in sorted(glob.glob(str(CEMS / f"*_{y}.parquet"))):
            st = Path(f).name[:2]
            for v in pq.read_table(f, columns=["facilityId"]).column(0).unique().to_pylist():
                m[str(v)] = st
        _FAC_STATE[y] = m
    return _FAC_STATE[y]


def noload_mmbtu(y: int, plants: dict[int, str]) -> tuple[dict[int, float], dict]:
    """Plant no-load MMBtu/h (sum of unit heat-input intercepts), closeout-PJM-decommit B0."""
    fs = facility_states(y)
    by_state: dict[str, list[str]] = {}
    for pc in plants:
        st = fs.get(str(pc))
        if st:
            by_state.setdefault(st, []).append(str(pc))
    cols = ["facilityId", "unitId", "opTime", "grossLoad", "heatInput", "primaryFuelInfo"]
    frames = []
    for st, ids in by_state.items():
        d = ds.dataset(str(CEMS / f"{st}_{y}.parquet"), format="parquet")
        frames.append(
            d.to_table(columns=cols, filter=ds.field("facilityId").isin(ids)).to_pandas()
        )
    nl: dict[int, float] = {}
    stats = {"units": 0, "fitted": 0, "r2": [], "plants_fitted": 0, "plants": len(plants)}
    if not frames:
        return nl, stats
    d = pd.concat(frames, ignore_index=True)
    d["pc"] = pd.to_numeric(d["facilityId"], errors="coerce")
    d["fuel"] = d["primaryFuelInfo"].astype(str)
    for pc, g in d.groupby("pc"):
        pc = int(pc)
        want = "Coal" if plants[pc] in COAL else "Gas"
        acc, any_fit = 0.0, False
        for _, gu in g.groupby("unitId"):
            if not gu["fuel"].str.contains(want, case=False).any():
                continue
            stats["units"] += 1
            peak = float(np.nan_to_num(gu["grossLoad"].max()))
            m = (gu["opTime"] >= 1.0) & (gu["grossLoad"] > 0) & (gu["heatInput"] > 0)
            x, h = gu.loc[m, "grossLoad"].to_numpy(float), gu.loc[m, "heatInput"].to_numpy(float)
            if peak <= 0 or len(x) < 200 or np.ptp(x) < 0.1 * peak:
                continue
            b, a = np.polyfit(x, h, 1)
            ss = np.sum((h - h.mean()) ** 2)
            r2 = 1.0 - np.sum((h - (a + b * x)) ** 2) / ss if ss > 0 else 0.0
            stats["fitted"] += 1
            stats["r2"].append(float(r2))
            acc += max(float(a), 0.0)
            any_fit = True
        if any_fit:
            nl[pc] = acc
            stats["plants_fitted"] += 1
    stats["r2_median"] = float(np.median(stats["r2"])) if stats["r2"] else None
    del stats["r2"]
    return nl, stats


_COSTS: pd.DataFrame | None = None


def fuel_price(y: int, plants: dict[int, str]) -> dict[int, np.ndarray]:
    """Plant hourly delivered fuel $/MMBtu: own month -> own-year mean -> state-month mean."""
    global _COSTS
    if _COSTS is None:
        _COSTS = load_monthly_fuel_costs(EIA923_MONTHLY_COSTS_PATH)
    month = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(T), "h")).month.to_numpy()
    out = {}
    for fg, grp in (("Coal", COAL), ("Natural Gas", ("CC_REGULAR", "ST_GAS"))):
        pcs = [pc for pc, g in plants.items() if g in grp]
        if not pcs:
            continue
        f = _COSTS[(_COSTS["year"] == y) & (_COSTS["fuel_group"] == fg)]
        own = f[f["plant_id"].isin(pcs)]
        st_price = (
            f[f["state"].isin(set(own["state"]))]
            .groupby(["state", "month"])
            .apply(
                lambda g: np.average(g["price_per_mmbtu"], weights=g["quantity"].clip(lower=1)),
                include_groups=False,
            )
        )
        all_m = f.groupby("month").apply(
            lambda g: np.average(g["price_per_mmbtu"], weights=g["quantity"].clip(lower=1)),
            include_groups=False,
        )
        for pc in pcs:
            g = own[own["plant_id"] == pc]
            mp = np.full(12, np.nan)
            if len(g):
                mon = g.groupby("month").apply(
                    lambda r: np.average(r["price_per_mmbtu"], weights=r["quantity"].clip(lower=1)),
                    include_groups=False,
                )
                mp = np.array([mon.get(m, np.nan) for m in range(1, 13)])
                yr = float(np.average(g["price_per_mmbtu"], weights=g["quantity"].clip(lower=1)))
                mp = np.where(np.isnan(mp), yr, mp)
                st = str(g["state"].iloc[0])
                mp = np.where(
                    np.isnan(mp), [st_price.get((st, m), np.nan) for m in range(1, 13)], mp
                )
            mp = np.where(np.isnan(mp), [all_m.get(m, np.nan) for m in range(1, 13)], mp)
            out[pc] = np.nan_to_num(mp[month - 1], nan=float(np.nanmean(mp)) if np.isfinite(mp).any() else 0.0)
    return out


# -------------------------------------------------------------------- DP machinery ----
def on_state(P: dict, price: np.ndarray, mlf: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """On-state output X (T), gross margin (T) and available capacity A (T) for one plant.

    In-merit tranches run at cap; output is raised to mlf*A at the cheapest offers; floor
    tranches (mustrun / sync) are priced at the plant's committed offer (PREDECL R-g).
    """
    kinds, CAP = P["kinds"], P["CAP"]
    MC = np.where(CAP > 0, np.nan_to_num(P["MC"], nan=1e6), 1e6)
    fl = np.isin(kinds, FLOOR_KINDS)
    com = kinds == "committed"
    if fl.any():
        ref = MC[com].min(0) if com.any() else np.where(fl[:, None], 1e6, MC).min(0)
        MC = np.where(fl[:, None], ref[None, :], MC)
    X = np.where(price[None, :] >= MC, CAP, 0.0)
    A = CAP.sum(0)
    need = np.maximum(0.0, mlf * A - X.sum(0))
    order = np.argsort(MC, axis=0)
    room = np.take_along_axis(CAP - X, order, 0)
    cum = np.cumsum(room, 0)
    add = np.clip(need[None, :] - (cum - room), 0.0, room)
    X = X + np.take_along_axis(add, np.argsort(order, axis=0), 0)
    margin = ((price[None, :] - MC) * X).sum(0)
    return X.sum(0), margin, A


def dp_group(
    m: np.ndarray, s_cost: np.ndarray, U: int, D: int, s0: np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Exact binary UC by DP, vectorized over rows (plants) sharing (U, D).

    States on_1..on_U (index 0..U-1; on_U = "at least U"), off_1..off_D (U..U+D-1; off_D =
    "at least D", may start).  ``m[n,t]`` = profit if online in hour t (no-load included);
    ``s_cost[n]`` = start cost.  ``s0`` = initial state index per row (default off_D).
    Returns (on mask (n, Th), final state index (n,)).
    """
    n, Th = m.shape
    ns = U + D
    NEG = -1e18
    V = np.full((n, ns), NEG)
    if s0 is None:
        V[:, ns - 1] = 0.0
    else:
        V[np.arange(n), s0] = 0.0
    back = np.zeros((Th, n, ns), np.int16)
    rows = np.arange(n)
    for t in range(Th):
        mt = m[:, t]
        nv = np.empty_like(V)
        nb = np.empty((n, ns), np.int16)
        # on_1: start from off_D
        nv[:, 0] = V[:, ns - 1] - s_cost + mt
        nb[:, 0] = ns - 1
        if U > 1:
            nv[:, 1:U] = V[:, 0 : U - 1] + mt[:, None]
            nb[:, 1:U] = np.arange(0, U - 1)[None, :]
        stay = V[:, U - 1] + mt  # stay in on_U
        better = stay > nv[:, U - 1]
        nv[:, U - 1] = np.where(better, stay, nv[:, U - 1])
        nb[:, U - 1] = np.where(better, U - 1, nb[:, U - 1])
        # off_1: stop from on_U
        nv[:, U] = V[:, U - 1]
        nb[:, U] = U - 1
        if D > 1:
            nv[:, U + 1 : ns] = V[:, U : ns - 1]
            nb[:, U + 1 : ns] = np.arange(U, ns - 1)[None, :]
        stay = V[:, ns - 1]  # stay in off_D
        better = stay > nv[:, ns - 1]
        nv[:, ns - 1] = np.where(better, stay, nv[:, ns - 1])
        nb[:, ns - 1] = np.where(better, ns - 1, nb[:, ns - 1])
        V, back[t] = nv, nb
    s = V.argmax(1)
    final = s.copy()
    on = np.zeros((n, Th), bool)
    for t in range(Th - 1, -1, -1):
        on[:, t] = s < U
        s = back[t, rows, s].astype(int)
    return on, final


def dp_rolling(m: np.ndarray, s_cost: np.ndarray, U: int, D: int) -> np.ndarray:
    """36-h windows, commit 24 h, carry the committed end state (plan section 4 E2)."""
    n, Th = m.shape
    on = np.zeros((n, Th), bool)
    s0 = np.full(n, U + D - 1)
    for h0 in range(0, Th, COMMIT_H):
        h1 = min(h0 + WINDOW_H, Th)
        o, _ = dp_group(m[:, h0:h1], s_cost, U, D, s0)
        keep = min(COMMIT_H, h1 - h0)
        on[:, h0 : h0 + keep] = o[:, :keep]
        s0 = _state_after(o[:, :keep], s0, U, D)
    return on


def _state_after(o: np.ndarray, s0: np.ndarray, U: int, D: int) -> np.ndarray:
    """Replay a committed on/off path from state s0 to the state index at its end."""
    s = s0.copy()
    for t in range(o.shape[1]):
        on_now = o[:, t]
        was_on = s < U
        s = np.where(
            on_now,
            np.where(was_on, np.minimum(s + 1, U - 1), 0),
            np.where(was_on, U, np.minimum(s + 1, U + D - 1)),
        )
    return s


# ---------------------------------------------------------------- run-length tools ----
def runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """(start, stop) of each maximal True run."""
    if not mask.any():
        return []
    idx = np.flatnonzero(np.diff(np.r_[0, mask.view(np.int8), 0]))
    return list(zip(idx[::2].tolist(), idx[1::2].tolist()))


def starts(mask: np.ndarray) -> int:
    """Number of off->on transitions."""
    return int(np.sum(np.diff(mask.view(np.int8)) == 1))


# ------------------------------------------------------------------ AS references ----
def _hoy(ts: pd.Series) -> np.ndarray:
    """Hour-of-year on the fixed non-leap 8760 clock (Feb 29 -> -1)."""
    ts = pd.DatetimeIndex(ts)
    doy = ts.dayofyear.to_numpy().copy()
    leap = ts.is_leap_year
    feb29 = leap & (ts.month == 2) & (ts.day == 29)
    doy = np.where(leap & (doy > 60), doy - 1, doy)
    h = (doy - 1) * 24 + ts.hour.to_numpy()
    return np.where(feb29, -1, h)


def _to_series(h: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Mean of v per hour-of-year on the 8760 clock (NaN where absent)."""
    ok = (h >= 0) & (h < T) & np.isfinite(v)
    out = np.full(T, np.nan)
    if ok.any():
        s = pd.Series(v[ok]).groupby(h[ok]).mean()
        out[s.index.to_numpy()] = s.to_numpy()
    return out


def actual_as_price(iso: str, y: int) -> np.ndarray | None:
    """The ISO's measured reserve clearing price per hour (PREDECL R-d), or None."""
    try:
        if iso == "PJM":
            f = RAW / f"PJM-AS/ancillary_services_{y}.parquet"
            if not f.exists():
                return None
            t = pd.read_parquet(f)
            t = t[(t["ancillary_service"] == "RTO Synchronized Reserve") & t["row_is_current"]]
            ts = pd.to_datetime(t["datetime_beginning_ept"])
            return _to_series(_hoy(ts), t["value"].to_numpy(float))
        if iso == "MISO":
            f = RAW / f"MISO-AS/asm_rtmcp_zonal_{y}.parquet"
            if not f.exists():
                return None
            t = pd.read_parquet(f)
            t = t[(t["zone"] == "Miso-Wide") & (t["product"] == "GENSPINMCP")]
            he = [f"he{i:02d}" for i in range(1, 25)]
            long = t.melt(id_vars=["date"], value_vars=he, var_name="he", value_name="v")
            ts = pd.to_datetime(long["date"]) + pd.to_timedelta(
                long["he"].str[2:].astype(int) - 1, "h"
            )
            return _to_series(_hoy(ts), pd.to_numeric(long["v"], errors="coerce").to_numpy(float))
        if iso == "SPP":
            f = RAW / f"spp-or-mcp/RTBM_MCP_{y}.csv.zip"
            if not f.exists():
                return None
            with zipfile.ZipFile(f) as z:
                name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
                t = pd.read_csv(io.BytesIO(z.read(name)))
            t.columns = [c.strip().upper().replace(" ", "_") for c in t.columns]  # 2022 is upper-case
            ts = pd.to_datetime(t["GMTINTERVALEND"]) - pd.Timedelta(minutes=1) - pd.Timedelta(hours=6)
            ts = ts.dt.floor("h")
            v = pd.to_numeric(t["SPIN"], errors="coerce").to_numpy(float)
            return _to_series(_hoy(ts), v)
        if iso == "NYISO":
            f = RAW / f"NYISO-AS/NYISO_as_rt_{y}.csv"
            if not f.exists():
                return None
            t = pd.read_csv(f)
            ts = pd.to_datetime(t["Time Stamp"]).dt.floor("h")
            return _to_series(_hoy(ts), pd.to_numeric(t["spin_10"], errors="coerce").to_numpy(float))
        if iso == "CAISO":
            fr = []
            for f in sorted(glob.glob(str(RAW / "CAISO-AS/asprc_sr_ALL_*.csv"))):
                tag = Path(f).stem.split("_")[-2:]
                if int(tag[0][:4]) > y or int(tag[1][:4]) < y:
                    continue
                t = pd.read_csv(f, usecols=["OPR_DT", "OPR_HR", "ANC_REGION", "XML_DATA_ITEM", "MW"])
                fr.append(t[(t["ANC_REGION"] == "AS_CAISO_EXP") & (t["XML_DATA_ITEM"] == "SP_CLR_PRC")])
            if not fr:
                return None
            t = pd.concat(fr)
            t = t[pd.to_datetime(t["OPR_DT"]).dt.year == y]
            ts = pd.to_datetime(t["OPR_DT"]) + pd.to_timedelta(t["OPR_HR"].astype(int) - 1, "h")
            return _to_series(_hoy(ts), pd.to_numeric(t["MW"], errors="coerce").to_numpy(float))
        if iso == "ERCOT":
            f = RAW / f"ercot/ercot_{y}_dam_as_mcpc_hourly.parquet"
            if f.exists():
                t = pd.read_parquet(f, columns=["hour", "rrs_mcpc"])
                return t.set_index("hour")["rrs_mcpc"].reindex(range(T)).to_numpy(float)
            fs = sorted(glob.glob(str(RAW / f"ercot-AS/60d_DAM_Gen_Resource_Data_{y}_*.parquet")))
            if not fs:
                return None
            parts = []
            for g in fs:
                d = pd.read_parquet(g, columns=["Delivery Date", "Hour Ending", "RRS MCPC"])
                d = d.dropna(subset=["RRS MCPC"])
                parts.append(d.groupby(["Delivery Date", "Hour Ending"])["RRS MCPC"].max().reset_index())
            d = pd.concat(parts).groupby(["Delivery Date", "Hour Ending"])["RRS MCPC"].max().reset_index()
            ts = pd.to_datetime(d["Delivery Date"]) + pd.to_timedelta(d["Hour Ending"].astype(int) - 1, "h")
            return _to_series(_hoy(ts), d["RRS MCPC"].to_numpy(float))
    except (OSError, ValueError, KeyError, IndexError) as e:  # a missing/odd payload is a gap
        print(f"   AS reference {iso} {y}: unreadable ({e})")
        return None
    return None


# ----------------------------------------------------------------------- the board ----
def gate_status(run_id: str) -> dict[int, dict]:
    """year -> {c3a_status, c3a_model, c3a_actual, c3b_status, c3b, failing, scoreable}."""
    import scripts.calibration_verdict as cv  # noqa: E402  (rubric 3.20 on main)

    v = cv.determine(run_id)
    out: dict[int, dict] = {}
    for crit, key in (("price_mean", "c3a"), ("price_shape", "c3b")):
        for r in v["criteria"].get(crit, {}).get("records", []):
            if "diagnostic" in str(r.get("metric", "")):
                continue
            o = out.setdefault(int(r["year"]), {})
            o[f"{key}_status"] = r["status"]
            o[f"{key}_model"], o[f"{key}_actual"] = r.get("model"), r.get("actual")
    for y, o in out.items():
        a_m, a_a, b_m = o.get("c3a_model"), o.get("c3a_actual"), o.get("c3b_model")
        a_fail = o.get("c3a_status") == "FAIL" or (
            o.get("c3a_status") == "CAVEAT"
            and a_m is not None
            and a_a
            and abs(a_m / a_a - 1.0) > GATE_C3A
        )
        b_fail = o.get("c3b_status") == "FAIL" or (
            o.get("c3b_status") == "CAVEAT" and b_m is not None and b_m > GATE_C3B
        )
        o["scoreable"] = a_m is not None or b_m is not None
        o["failing"] = bool(a_fail or b_fail)
        o["failing_gates"] = [g for g, f in (("C3a", a_fail), ("C3b", b_fail)) if f]
    return out


def d2_census(bundle: Path) -> list[dict]:
    """Every D-2 mechanism row on a slow-start class, summed over years."""
    d = json.load(open(bundle / "legitimacy_diagnostics.json"))["diagnostics"]["D2"]["rows"]
    agg: dict[tuple[str, str], dict] = {}
    for r in d:
        if r["class"] not in SLOW:
            continue
        a = agg.setdefault((r["class"], r["mechanism"]), {"years": [], "forced_twh": 0.0, "class_twh": 0.0})
        a["years"].append(int(r["year"]))
        a["forced_twh"] += float(r["forced_twh"])
        a["class_twh"] += float(r["class_total_twh"])
    return [
        {
            "class": c,
            "mechanism": m,
            "years": sorted(v["years"]),
            "forced_twh": round(v["forced_twh"], 3),
            "class_twh": round(v["class_twh"], 1),
            "share": round(v["forced_twh"] / max(v["class_twh"], 1e-9), 4),
        }
        for (c, m), v in sorted(agg.items())
    ]


# --------------------------------------------------------------------- per ISO-year ----
def screen_year(iso: str, bundle: Path, y: int, cp: dict[int, float]) -> dict:
    """M1-M6 for one ISO-year."""
    t0 = time.time()
    um = load_slow_units(bundle, y)
    kp = plant_blocks(um)
    zp, psys, dem = system_price(bundle, y)
    cems = bench_cems(iso, y)
    res: dict = {"plants": len(kp), "plants_with_cems": 0, "classes": {}}

    # per-plant physics, mlf, prices
    groups = {pc: P["group"] for pc, P in kp.items()}
    nl_mmbtu, nl_stats = noload_mmbtu(y, groups)
    fp = fuel_price(y, groups)
    cls_nl_per_mw: dict[str, float] = {}
    for g in set(groups.values()):
        num = den = 0.0
        for pc in kp:
            if groups[pc] == g and pc in nl_mmbtu:
                a = float(kp[pc]["CAP"].sum(0).max())
                num += nl_mmbtu[pc]
                den += a
        cls_nl_per_mw[g] = num / den if den > 0 else 0.0
    res["noload_fit"] = nl_stats

    per_plant = {}
    for pc, P in kp.items():
        ph = physics(iso, P["group"])
        mlf = cp.get(pc, ph["mlf"])
        price = zp.get(P["zone"], psys)
        price = np.where(np.isfinite(price), price, np.nan_to_num(psys, nan=0.0))
        X, margin, A = on_state(P, price, mlf)
        Apk = float(A.max())
        nl_h = (nl_mmbtu.get(pc, cls_nl_per_mw[P["group"]] * Apk)) * fp[pc]
        mw = P["MW"].sum(0)
        on_m = (A > 0) & (mw >= ON_MODEL * A)
        per_plant[pc] = dict(
            group=P["group"], UT=ph["UT"], DT=ph["DT"], S=ph["S"], mlf=mlf, A=A, Apk=Apk,
            X=X, r_on=np.where(A > 0, margin - nl_h, -1e9), s_cost=ph["S"] * Apk, mw=mw,
            on_m=on_m, nl_fallback=pc not in nl_mmbtu, price=price,
        )

    # M1 / M2 / M6 per class
    for g in sorted(set(groups.values())):
        pcs = [pc for pc in kp if groups[pc] == g]
        ph = physics(iso, g)
        e_cls = sum(float(per_plant[pc]["mw"].sum()) for pc in pcs) / 1e6
        short_on_twh = short_on_runs = short_off = short_off_h = 0.0
        st_m = st_c = 0
        n_cems = 0
        m2a = m2b = gap_any_twh = 0.0
        online_cems_h = online_model_h = 0
        for pc in pcs:
            q = per_plant[pc]
            on_m = q["on_m"]
            for a, b in runs(on_m):
                if b - a < q["UT"]:
                    short_on_twh += float(q["mw"][a:b].sum()) / 1e6
                    short_on_runs += 1
            for a, b in runs(~on_m):
                if 0 < a and b < T and b - a < q["DT"]:
                    short_off += 1
                    short_off_h += b - a
            if pc in cems:
                n_cems += 1
                cf = cems[pc]["cf"]
                on_c = cf >= ON_CEMS
                st_m += starts(on_m)
                st_c += starts(on_c)
                band = q["mlf"] + PMIN_BAND
                a_mask = on_c & (cf <= band * 100.0) & ~on_m
                m2a += float((q["mlf"] * q["A"])[a_mask].sum()) / 1e6
                b_mask = on_m & (q["mw"] <= band * q["A"]) & ~on_c
                m2b += float(q["mw"][b_mask].sum()) / 1e6
                gap_any_twh += float((cf / 100.0 * cems[pc]["npl"])[on_c & ~on_m].sum()) / 1e6
                online_cems_h += int(on_c.sum())
                online_model_h += int(on_m.sum())
        res["classes"][g] = dict(
            plants=len(pcs), plants_with_cems=n_cems, physics=ph,
            class_twh=round(e_cls, 3),
            m1_short_on_twh=round(short_on_twh, 4),
            m1_short_on_share=round(short_on_twh / e_cls, 4) if e_cls > 0 else None,
            m1_short_on_runs=int(short_on_runs),
            m1_short_off_gaps=int(short_off), m1_short_off_hours=int(short_off_h),
            m1_starts_model=st_m, m1_starts_cems=st_c,
            m1_starts_ratio=round(st_m / st_c, 3) if st_c else None,
            m2a_twh=round(m2a, 4), m2b_twh=round(m2b, 4),
            m2_cems_on_model_off_twh=round(gap_any_twh, 4),
            online_hours_cems=online_cems_h, online_hours_model=online_model_h,
            m6_clusters=len(pcs),
            m6_mw=round(sum(per_plant[pc]["Apk"] for pc in pcs), 1),
            m6_integers_per_window=len(pcs) * WINDOW_H,
            noload_fallback_plants=sum(per_plant[pc]["nl_fallback"] for pc in pcs),
        )
        res["plants_with_cems"] += n_cems

    # M5: DP per (UT, DT) group, both forms
    m5 = {"pf": {}, "h36": {}}
    by_ud: dict[tuple[int, int], list[int]] = {}
    for pc, q in per_plant.items():
        by_ud.setdefault((q["UT"], q["DT"]), []).append(pc)
    for (U, D), pcs in by_ud.items():
        m = np.vstack([per_plant[pc]["r_on"] for pc in pcs])
        s_cost = np.array([per_plant[pc]["s_cost"] for pc in pcs])
        on_pf, _ = dp_group(m, s_cost, U, D)
        on_36 = dp_rolling(m, s_cost, U, D)
        for form, on in (("pf", on_pf), ("h36", on_36)):
            for i, pc in enumerate(pcs):
                q = per_plant[pc]
                g = q["group"]
                acc = m5[form].setdefault(
                    g,
                    dict(dp_twh=0.0, keeper_twh=0.0, added_twh=0.0, removed_twh=0.0,
                         dp_minload_twh=0.0, keeper_minload_twh=0.0, starts_dp=0,
                         starts_keeper=0, added_low_h=0, added_low_cems_on_h=0),
                )
                u = on[i]
                dp_mw = np.where(u, q["X"], 0.0)
                acc["dp_twh"] += float(dp_mw.sum()) / 1e6
                acc["keeper_twh"] += float(q["mw"].sum()) / 1e6
                acc["added_twh"] += float(dp_mw[u & ~q["on_m"]].sum()) / 1e6
                acc["removed_twh"] += float(q["mw"][q["on_m"] & ~u].sum()) / 1e6
                floor = u & (q["X"] <= q["mlf"] * q["A"] + 1e-6)
                acc["dp_minload_twh"] += float(dp_mw[floor].sum()) / 1e6
                kfl = q["on_m"] & (q["mw"] <= (q["mlf"] + PMIN_BAND) * q["A"])
                acc["keeper_minload_twh"] += float(q["mw"][kfl].sum()) / 1e6
                acc["starts_dp"] += starts(u)
                acc["starts_keeper"] += starts(q["on_m"])
                if pc in cems:
                    low = q["price"] <= LOW_PRICE
                    add = u & ~q["on_m"] & low
                    acc["added_low_h"] += int(add.sum())
                    acc["added_low_cems_on_h"] += int((add & (cems[pc]["cf"] >= ON_CEMS)).sum())
    for form in m5:
        for g, acc in m5[form].items():
            acc["delta_twh"] = round(acc["dp_twh"] - acc["keeper_twh"], 4)
            acc["delta_minload_twh"] = round(acc["dp_minload_twh"] - acc["keeper_minload_twh"], 4)
            acc["precision_added_low"] = (
                round(acc["added_low_cems_on_h"] / acc["added_low_h"], 3) if acc["added_low_h"] else None
            )
            for k in list(acc):
                if isinstance(acc[k], float):
                    acc[k] = round(acc[k], 4)
    res["m5"] = m5

    # M3
    rt = actual_rt(iso, y)
    if rt is not None and np.isfinite(rt).sum() > 24:
        ok = np.isfinite(rt) & np.isfinite(psys)
        q1, q2 = np.quantile(rt[ok], [1 / 3, 2 / 3])
        err = psys - rt
        lo, mid, hi = ok & (rt <= q1), ok & (rt > q1) & (rt <= q2), ok & (rt > q2)
        n_a15, n_m15 = int((rt[ok] <= LOW_PRICE).sum()), int((psys[ok] <= LOW_PRICE).sum())
        n_a0, n_m0 = int((rt[ok] < 0).sum()), int((psys[ok] < 0).sum())
        res["m3"] = dict(
            coverage=round(float(ok.mean()), 3),
            tercile_edges=[round(float(q1), 2), round(float(q2), 2)],
            lower_mean_err=round(float(err[lo].mean()), 3), lower_hours=int(lo.sum()),
            lower_dollar_h=round(float(err[lo].sum()), 0),
            mid_mean_err=round(float(err[mid].mean()), 3), upper_mean_err=round(float(err[hi].mean()), 3),
            model_mean=round(float(np.average(psys[ok], weights=dem[ok])), 2),
            actual_mean=round(float(np.average(rt[ok], weights=dem[ok])), 2),
            hours_le15_actual=n_a15, hours_le15_model=n_m15,
            ratio_le15=round(n_m15 / n_a15, 3) if n_a15 else None,
            hours_neg_actual=n_a0, hours_neg_model=n_m0,
            ratio_neg=round(n_m0 / n_a0, 3) if n_a0 else None,
        )
    else:
        res["m3"] = None

    # M4
    mm = model_reserve_mcp(bundle, y)
    am = actual_as_price(iso, y)
    if am is not None and np.isfinite(am).sum() > 24:
        ok = np.isfinite(am)
        res["m4"] = dict(
            coverage=round(float(ok.mean()), 3),
            model_dormant_share=round(float((mm[ok] < MCP_DORMANT).mean()), 3),
            actual_dormant_share=round(float((am[ok] < MCP_DORMANT).mean()), 3),
            model_mean_mcp=round(float(mm[ok].mean()), 2), actual_mean_mcp=round(float(am[ok].mean()), 2),
        )
        res["m4"]["gap"] = round(res["m4"]["model_dormant_share"] - res["m4"]["actual_dormant_share"], 3)
    else:
        res["m4"] = None
    res["seconds"] = round(time.time() - t0, 1)
    return res


def board_cell(r: dict, gate: dict) -> dict:
    """S1 / S2 / M1 / M4 and the flags for one ISO-year."""
    cls = r["classes"]
    s2 = sum(c["m2a_twh"] + c["m2b_twh"] for c in cls.values())
    m1 = sum(c["m1_short_on_twh"] for c in cls.values())
    s1 = abs(r["m3"]["lower_dollar_h"]) if r["m3"] else None
    gap = r["m4"]["gap"] if r["m4"] else None
    failing, scoreable = gate.get("failing", False), gate.get("scoreable", False)
    eligible = (s2 >= ELIG_S2_TWH) or (gap is not None and gap >= ELIG_M4_GAP)
    return dict(
        S1=s1, S1_sign=(np.sign(r["m3"]["lower_dollar_h"]) if r["m3"] else None),
        S2=round(s2, 3), M1=round(m1, 4), M4_gap=gap,
        failing=failing, failing_gates=gate.get("failing_gates", []), scoreable=scoreable,
        eligible=bool(eligible), rankable=bool(failing and scoreable and s1 is not None),
    )


def main(argv: list[str]) -> int:
    """Run the screen for the named ISOs (default all nine) and write the JSON."""
    want = [a for a in argv if a in ISOS] or ISOS
    K = keepers()
    out = {
        "schema": "ucmilp-benefit-screen/v1",
        "predecl": "docs/records/governance/uc-milp-2026-10/PREDECL-uc-milp-benefit-screen-2026-10-03.md",
        "conventions": dict(on_model=ON_MODEL, on_cems_pct=ON_CEMS, pmin_band=PMIN_BAND, low_price=LOW_PRICE,
                            mcp_dormant=MCP_DORMANT, window_h=WINDOW_H, commit_h=COMMIT_H,
                            elig_s2_twh=ELIG_S2_TWH, elig_m4_gap=ELIG_M4_GAP, top_n=TOP_N, controls=CONTROLS),
        "isos": {},
    }
    if OUT.exists():  # resume: keep ISOs already screened in a previous invocation
        try:
            prev = json.load(open(OUT))
            out["isos"] = {k: v for k, v in prev.get("isos", {}).items() if k not in want}
        except (OSError, ValueError):
            pass
    for iso in want:
        k = K[iso]
        print(f"== {iso} {k['run_id']} ({k['bundle'].name}) years {k['years']}", flush=True)
        gates = gate_status(k["run_id"])
        cp = committed_pct(iso)
        rec = {"run_id": k["run_id"], "bundle": k["bundle"].name, "years": {}, "d2_census": d2_census(k["bundle"]),
               "physics": {g: physics(iso, g) for g in SLOW}, "committed_pct_plants": len(cp)}
        for y in k["years"]:
            r = screen_year(iso, k["bundle"], y, cp)
            r["gates"] = gates.get(y, {})
            r["board"] = board_cell(r, r["gates"])
            rec["years"][str(y)] = r
            b = r["board"]
            print(f"   {y}: S1={b['S1']} S2={b['S2']} M1={b['M1']} M4gap={b['M4_gap']} failing={b['failing_gates']} "
                  f"eligible={b['eligible']} ({r['seconds']}s)", flush=True)
        out["isos"][iso] = rec
        OUT.parent.mkdir(parents=True, exist_ok=True)
        json.dump(out, open(OUT, "w"), indent=1, default=_js)
    # ranking + selection over everything screened so far
    rows = []
    for iso, rec in out["isos"].items():
        for y, r in rec["years"].items():
            b = r["board"]
            rows.append(dict(iso=iso, year=int(y), **{k2: b[k2] for k2 in ("S1", "S2", "M1", "M4_gap", "failing", "failing_gates", "scoreable", "eligible", "rankable")}))
    ranked = sorted([r for r in rows if r["rankable"]], key=lambda r: (-r["S1"], -r["S2"], -r["M1"]))
    elig = [r for r in ranked if r["eligible"]]
    out["ranking"] = ranked
    out["selection"] = {
        "targets": [(r["iso"], r["year"]) for r in elig[:TOP_N]],
        "controls": list(CONTROLS),
        "eligible_failing_cells": len(elig),
        "rankable_cells": len(ranked),
        "fallback_highest_s1": [(ranked[0]["iso"], ranked[0]["year"])] if ranked and not elig else [],
    }
    json.dump(out, open(OUT, "w"), indent=1, default=_js)
    print("selection:", out["selection"])
    return 0


def _js(o):
    """JSON default for numpy scalars / paths."""
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, Path):
        return str(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
