"""miso-208 phase 0 — FIND THE 8-11 GW (zero-solve).

miso-207 measured that on the Jun-Jul 2025 p75-p99 SHOULDER (351 h) and the
15-hour TAIL the keeper clears within $0.59 of its own setter while the real
market clears $50-150 above the model's dearest in-merit tranche, with
8-11 GW of the model's capability idle within $20 of the price.  A QUANTITY
object.  This probe asks, from MEASURED sources only, where that supply sits
relative to what MISO actually ran, and whether any admissible (rule 13)
cause reaches >= 25 % of the gap in BOTH populations:

  item 0  the supply-mix map: keeper class dispatch vs EIA-930 by fuel and
          the CAMPD prime-mover split (WP-3 construction) — identification;
  item 1  MISO's published MOM unplanned-outage record vs the armed envelope
          on the shoulder DAYS (miso-195's W2/W4/W6 read in the shoulder);
  item 2  CT_PEAKER conduct: the measured CT fleet's output vs the model's
          idle-but-cheap CT cushion;
  item 3  deliverability: INDIANA.HUB MCC/MLC, M2M binding, the RDT binding
          record, the cushion's zonal split;
  item 4  declared-emergency windows: the hour census and the armed tier
          floor's silence.

Every candidate's MW is re-priced up the keeper's OWN idle census (miso-207's
``_seam_reprice`` generalized to a per-hour removal) and reported as a share
of each population's gap.  PREREG
``results/calibration/PREREG-miso208-find-the-supply-2026-09-04.md`` pushed at
``6a50d0fc`` BEFORE any statistic here was computed.  Rule 22: 2023-2025 only.
No LP is solved.

Usage::

    PYTHONPATH=src python3 scripts/probes/_miso208_find_the_supply.py
"""

from __future__ import annotations

import dataclasses
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso207_bound_the_shoulder as m207  # noqa: E402  (re-points _m134.BUNDLE)
from _miso134_ct_night_order_screen import (  # noqa: E402
    build_year,
    keeper_config,
    keeper_prices,
)
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.maxgen_events import (  # noqa: E402
    TIER_FLOOR_BY_LEVEL,
    load_maxgen_registry_model_clock,
)
from market_sim.data.miso_outages import (  # noqa: E402
    _THERMAL_GROUPS,
    miso_outage_mw_series,
)
from market_sim.data.outages import outage_hour_mask  # noqa: E402
from scripts.data import derive_thermal_tranches as dtt  # noqa: E402

KEEPER = m207.KEEPER
ZONAL = m207.ZONAL
OUT = REPO / "results/calibration/_miso208_find_the_supply.json"
HUB_LMP = RAW_DATA_DIR / "lmp-data" / "MISO"
M2M_DIR = RAW_DATA_DIR / "miso-m2m-flowgates"
PBC_DIR = RAW_DATA_DIR / "transfer-constraint-binding" / "MISO"

YEARS = (2023, 2024, 2025)
HOURS = 8760
HUB = m207.SCORING_HUB
CARRY = m207.CARRY_ZONES
COAL_POOL = m207.COAL_POOL
GAS = m207.GAS_CLASSES
IDLE_BAND = 20.0
LICENSE = 0.25
UNPLANNED = ("Derated", "Forced", "Unplanned")
ALL_CAUSES = ("Derated", "Forced", "Planned", "Unplanned")
POP_GROUPS = tuple(sorted(_THERMAL_GROUPS))
CUSHION = ("CT_PEAKER", "ST_GAS", "CC_REGULAR")
WARNING_PLUS = tuple(k for k, v in TIER_FLOOR_BY_LEVEL.items() if v is not None)
# The model clock, MEASURED (V-KEY-930 and V-KEY-LMP, r = 1.000 at the winning
# shift in both): the keeper's hours are CST hour-beginning, ONE HOUR BEHIND
# every EST-labelled MISO file (the LMP HE file, M2M settlement, PBC record,
# and the maxgen registry's "model clock", which maxgen_events.MODEL_TZ_BY_ISO
# pins to Etc/GMT+5). EST hour-beginning index j -> model index j + EST_TO_MODEL.
EST_TZ = "Etc/GMT+5"
EST_TO_MODEL = -1
E930_FUELS = ("COL", "NG", "NUC", "WND", "SUN", "WAT", "OTH", "BAT")
MODEL_TO_930 = {
    "COL": (COAL_POOL,),
    "NG": GAS,
    "NUC": ("nuclear",),
    "WND": ("wind",),
    "SUN": ("solar",),
    "WAT": ("hydro",),
    "OTH": ("biomass", "oil", "OTHER"),
}
EXCESS_ROWS_930 = ("COL", "NUC", "WAT", "OTH", "import", "NG")
EXCESS_ROWS_CAMPD = ("COAL", "CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP", "CT_CHP")
HE = [f"he{i:02d}" for i in range(1, 25)]


# ----------------------------------------------------------------- clocks
def _hoy_from_local(ts: pd.Series) -> np.ndarray:
    """Model hour-of-year for naive local timestamps; Feb 29 -> -1."""
    lens = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
    start = np.concatenate([[0], np.cumsum(lens)[:-1]])
    m = ts.dt.month.to_numpy() - 1
    d = ts.dt.day.to_numpy() - 1
    h = ts.dt.hour.to_numpy()
    out = (start[m] + d) * 24 + h
    out[(m == 1) & (d == 28)] = -1
    return out


def _series_on_clock(ts_local: pd.Series, val: np.ndarray, year: int) -> np.ndarray:
    arr = np.full(HOURS, np.nan)
    keep = ts_local.dt.year.to_numpy() == year
    hoy = _hoy_from_local(ts_local[keep])
    v = np.asarray(val)[keep]
    ok = (hoy >= 0) & (hoy < HOURS)
    arr[hoy[ok]] = v[ok]
    return arr


def _shift_corr(a: np.ndarray, b: np.ndarray, idx: np.ndarray, shifts=range(-2, 3)):
    """r(a[idx], b[idx + s]) per shift s; the winner names the clock offset."""
    out = {}
    for s in shifts:
        j = idx + s
        ok = (j >= 0) & (j < HOURS)
        x, y = a[idx[ok]], b[j[ok]]
        m = np.isfinite(x) & np.isfinite(y)
        out[str(s)] = (
            round(float(np.corrcoef(x[m], y[m])[0, 1]), 5) if m.sum() > 10 else None
        )
    best = max((k for k in out if out[k] is not None), key=lambda k: out[k])
    return {"r_by_shift": out, "winner": int(best)}


# ----------------------------------------------------------------- EIA-930
def e930_year(year: int) -> dict[str, np.ndarray]:
    """EIA-930 MISO fuel-type gen, D and TI, keyed on the UTC ``period`` label
    converted to EST; V-KEY-930 measures the residual shift to the model clock
    (the parquet's ``period`` is an hour-ENDING label, so EST-label index j is
    model index j + 2 — the +2 winner)."""
    ft = pd.read_parquet(RAW_DATA_DIR / "MISO_fueltype.parquet")
    rg = pd.read_parquet(RAW_DATA_DIR / "MISO_region.parquet")
    out = {}
    # The region file's "NG" is NET GENERATION, the fuel file's "NG" is natural
    # gas — read each file for its own keys only (a shared-key collision here
    # silently replaced the gas row with total generation on the first run).
    for src, key, want in (
        (ft, "fueltype", E930_FUELS),
        (rg, "type", ("D", "TI", "NG")),
    ):
        loc = (
            pd.to_datetime(src["period"], utc=True)
            .dt.tz_convert(EST_TZ)
            .dt.tz_localize(None)
        )
        for k, g in src.assign(loc=loc).groupby(key, observed=True):
            if k in want:
                name = "NG_TOTAL" if (key == "type" and k == "NG") else str(k)
                out[name] = _series_on_clock(
                    g["loc"], g["value_mwh"].to_numpy(float), year
                )
    return out


# ----------------------------------------------------------------- CAMPD
def campd_group_series(
    year: int,
) -> tuple[dict[str, np.ndarray], dict[str, float], dict[str, int]]:
    """Measured net MW per MODEL GROUP (matched plants), matched nameplate, n."""
    states = campd.states_for_iso("MISO")
    df = campd.load_campd_hourly(states, [year])
    factors = dtt._parasitic_factor_map()
    net = campd.plant_hourly_net(df, factors, year, hours=HOURS)
    cap, primary = dtt._fleet_nameplate_and_group("MISO")
    n_with_factor = sum(1 for code in net if int(code) in factors)
    print(
        f"  campd {year}: {len(net)} plants, {n_with_factor} with a parasitic factor",
        flush=True,
    )
    series: dict[str, np.ndarray] = {}
    npl: dict[str, float] = {}
    n: dict[str, int] = {}
    for code, s in net.items():
        g = primary.get(int(code))
        if not g:
            continue
        series[g] = series.get(g, np.zeros(HOURS)) + s
        npl[g] = npl.get(g, 0.0) + float(cap.get((int(code), g), 0.0))
        n[g] = n.get(g, 0) + 1
    return series, npl, n


# ----------------------------------------------------------------- LMP components
def hub_components(year: int) -> dict[str, np.ndarray] | None:
    path = HUB_LMP / f"miso_hub_lmp_{year}_rt.csv.gz"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df = df[df["node"] == HUB].copy()
    df["date"] = pd.to_datetime(df["date"])
    out = {}
    for label in ("LMP", "MCC", "MLC"):
        g = df[df["value"] == label].groupby("date")[HE].mean().sort_index()
        g = g[~((g.index.month == 2) & (g.index.day == 29))]
        arr = g.to_numpy().ravel()
        full = np.full(HOURS, np.nan)
        full[: min(HOURS, len(arr))] = arr[:HOURS]
        out[label] = full
    return out


# ----------------------------------------------------------------- M2M / PBC
def m2m_hourly(year: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(n coordinated flowgates, n binding, sum MISO shadow) per model hour."""
    path = M2M_DIR / f"M2M_Settlement_srw_{year}.csv.gz"
    with gzip.open(path, "rt") as fh:
        df = pd.read_csv(fh, usecols=["HOUR_ENDING", "MISO_SHADOW_PRICE"])
    parts = df["HOUR_ENDING"].str.split(" ", n=1, expand=True)
    date = pd.to_datetime(parts[0])
    he = parts[1].str.split(":", n=1, expand=True)[0].astype(int)
    hoy = _hoy_from_local(pd.Series(date)) + (he.to_numpy() - 1) + EST_TO_MODEL
    ok = (hoy >= 0) & (hoy < HOURS) & (date.dt.year.to_numpy() == year)
    sp = np.abs(
        pd.to_numeric(df["MISO_SHADOW_PRICE"], errors="coerce").fillna(0.0).to_numpy()
    )
    n_all = np.bincount(hoy[ok], minlength=HOURS)[:HOURS].astype(float)
    n_bind = np.bincount(hoy[ok], weights=(sp[ok] > 0), minlength=HOURS)[:HOURS]
    ssp = np.bincount(hoy[ok], weights=sp[ok], minlength=HOURS)[:HOURS]
    return n_all, n_bind, ssp


def pbc_rt_hourly(year: int) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    """RDT / sub-regional PBC RT binding: (any-binding, South->North) hour masks."""
    path = PBC_DIR / f"miso_pbc_rt_{year}.csv.gz"
    with gzip.open(path, "rt") as fh:
        df = pd.read_csv(fh, skipinitialspace=True, index_col=False)
    df.columns = [c.strip() for c in df.columns]
    ts = pd.to_datetime(df["MARKET_HOUR_EST"], errors="coerce")
    df = df[ts.notna()].reset_index(drop=True)
    ts = ts[ts.notna()].reset_index(drop=True)
    hoy = _hoy_from_local(ts) + EST_TO_MODEL
    ok = (hoy >= 0) & (hoy < HOURS) & (ts.dt.year.to_numpy() == year)
    name = df["CONSTRAINT_NAME"].astype(str)
    any_b = np.zeros(HOURS, bool)
    s2n = np.zeros(HOURS, bool)
    any_b[hoy[ok]] = True
    s_n = ok & name.str.contains("South_North", case=False).to_numpy()
    s2n[hoy[s_n]] = True
    counts = name[ok].value_counts().to_dict()
    return any_b, s2n, {str(k): int(v) for k, v in counts.items()}


# ----------------------------------------------------------------- windows
def window_masks(year: int) -> dict[str, np.ndarray]:
    ev = load_maxgen_registry_model_clock("MISO")
    any_m = np.zeros(HOURS, bool)
    warn = np.zeros(HOURS, bool)
    warn_armed = np.zeros(HOURS, bool)
    rows = []
    for r in ev.itertuples(index=False):
        m_armed = outage_hour_mask(r.start_model, r.end_model_excl, year, HOURS)
        # the registry's "model clock" is EST; the true model clock is CST
        m = outage_hour_mask(
            r.start_model + pd.Timedelta(hours=EST_TO_MODEL),
            r.end_model_excl + pd.Timedelta(hours=EST_TO_MODEL),
            year,
            HOURS,
        )
        if not (m.any() or m_armed.any()):
            continue
        any_m |= m
        if str(r.level) in WARNING_PLUS:
            warn |= m
            warn_armed |= m_armed
        rows.append(
            {
                "level": str(r.level),
                "region": str(r.region),
                "start": str(r.start_model),
                "end_excl": str(r.end_model_excl),
                "n_hours": int(m.sum()),
            }
        )
    return {
        "any": any_m,
        "warning_plus": warn,
        "warning_plus_as_armed": warn_armed,
        "rows": rows,
    }


# ----------------------------------------------------------------- lift engine
def lift(idx, mc, avail_mw, zones, price_df, removal) -> dict:
    """Re-price a per-hour removal (MW) up the keeper's own idle census.

    miso-207's ``_seam_reprice`` with the scalar X replaced by ``removal[h]``
    (carry zones pooled: the price after removing X MW of supply is the mc of
    the X-th idle MW above the current price)."""
    removal = np.asarray(removal, float)
    lifts = np.zeros(idx.size)
    pz = {z: price_df[z].to_numpy() for z in CARRY if z in price_df.columns}
    for i, h in enumerate(idx):
        x = float(removal[i])
        if x <= 0:
            continue
        col_mc, col_av = [], []
        for z, p_arr in pz.items():
            zsel = zones == z
            p = float(p_arr[h])
            m = mc[zsel, h]
            a = avail_mw[zsel, h]
            sel = (m > p + 1e-6) & (a > 1e-6)
            col_mc.append(m[sel])
            col_av.append(a[sel])
        m_all = np.concatenate(col_mc)
        a_all = np.concatenate(col_av)
        order = np.argsort(m_all)
        cum = np.cumsum(a_all[order])
        p_now = float(np.mean([p_arr[h] for p_arr in pz.values()]))
        k = int(np.searchsorted(cum, x))
        p_new = float(m_all[order][min(k, len(order) - 1)]) if len(order) else p_now
        lifts[i] = max(0.0, p_new - p_now)
    return {
        "removal_gw_mean": round(float(removal.mean()) / 1e3, 3),
        "removal_gw_p50": round(float(np.median(removal)) / 1e3, 3),
        "lift_usd_mean": round(float(lifts.mean()), 3),
        "lift_usd_p50": round(float(np.median(lifts)), 3),
        "lift_usd_p90": round(float(np.percentile(lifts, 90)), 3),
        "hours_lifted_over_5": int((lifts > 5).sum()),
    }


def with_share(block: dict, gap: float) -> dict:
    block["share_of_gap"] = round(block["lift_usd_mean"] / abs(gap), 4) if gap else None
    block["reaches_25pct"] = bool((block["share_of_gap"] or 0.0) >= LICENSE)
    return block


def idle_census(idx, mc, avail_mw, labels, zones, price_df, band=IDLE_BAND):
    """Idle MW priced within ``band`` above the zonal price: per hour, by class,
    by zone (the miso-207 cushion, re-derived so its zonal split is visible)."""
    per_hour = np.zeros(idx.size)
    by_class: dict[str, float] = {}
    by_zone: dict[str, np.ndarray] = {}
    for z in CARRY:
        if z not in price_df.columns:
            continue
        zsel = zones == z
        p = price_df[z].to_numpy()[idx][None, :]
        m = mc[zsel][:, idx]
        a = avail_mw[zsel][:, idx]
        sel = (m > p + 1e-6) & (m <= p + band) & (a > 1e-6)
        mw = np.where(sel, a, 0.0)
        per_hour += mw.sum(axis=0)
        by_zone[z] = mw.sum(axis=0)
        lab = labels[zsel]
        for k in np.unique(lab):
            by_class[k] = by_class.get(k, 0.0) + float(mw[lab == k].sum(axis=0).mean())
    return per_hour, by_class, by_zone


def _mean(a, idx):
    return float(np.nanmean(np.asarray(a, float)[idx]))


def main() -> None:  # noqa: PLR0915
    zon = pd.read_parquet(ZONAL)
    m207rec = json.loads(m207.OUT.read_text())["years"]
    cfg0 = keeper_config()
    mon = m207._hour_month()
    jj = np.where(np.isin(mon, (6, 7)))[0]
    hod = np.arange(HOURS) % 24
    report: dict = {
        "charter": "miso-208 phase 0 — find the 8-11 GW; zero-solve; nothing armed.",
        "prereg": "results/calibration/PREREG-miso208-find-the-supply-2026-09-04.md @ 6a50d0fc",
        "keeper": "2026-09-03-miso-202-unitclip",
        "instrument": m207.__doc__.split("Instrument:")[1].split("PREREG")[0].strip(),
        "model_clock": "CST hour-beginning (measured: V-KEY-930 winner +2 on hour-ending UTC->EST labels, V-KEY-LMP winner +1 on EST HE labels); EST_TO_MODEL = -1",
        "years": {},
    }

    for year in YEARS:
        y: dict = {}
        rt = m207.hub_series(zon, year, "rt")
        price_df, demand = keeper_prices(year)
        price_df = price_df.reindex(range(HOURS))
        carry = [z for z in CARRY if z in price_df.columns]
        sysd = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        num = sysd.assign(pw=sysd["price"] * sysd["demand"]).groupby("hour")["pw"].sum()
        den = sysd.groupby("hour")["demand"].sum()
        price_lw = (num / den).reindex(range(HOURS)).to_numpy()
        slack = (
            sysd.groupby("hour")["slack"]
            .sum()
            .reindex(range(HOURS))
            .fillna(0)
            .to_numpy()
        )
        ch = m207.keeper_class_hourly(year)
        st = pd.read_parquet(KEEPER / f"hourly/storage_{year}.parquet")
        st = st[st["pass"] == "P1"].groupby("hour")[["charge_mw", "discharge_mw"]].sum()
        st_net = (
            (st["discharge_mw"] - st["charge_mw"])
            .reindex(range(HOURS))
            .fillna(0)
            .to_numpy()
        )
        st_raw = pd.read_parquet(KEEPER / f"hourly/storage_{year}.parquet")
        st_raw = st_raw[st_raw["pass"] == "P1"]
        st_by_tech = {
            t: (
                g.groupby("hour")["discharge_mw"].sum()
                - g.groupby("hour")["charge_mw"].sum()
            )
            .reindex(range(HOURS))
            .fillna(0)
            .to_numpy()
            for t, g in st_raw.groupby("tech", observed=True)
        }

        # ---- populations (miso-207's construction, verbatim) ---------------
        a = rt[jj]
        rank = (a.argsort().argsort() / len(a)) * 100.0
        thr99 = float(np.nanpercentile(a, 99.0))
        tail = jj[a >= thr99]
        shoulder = jj[(rank >= 75.0) & (a < thr99)]
        other = np.array(sorted(set(jj) - set(shoulder) - set(tail)))
        day_other = other[np.isin(hod[other], range(10, 21))]
        bands = {
            "p75-90": jj[(rank >= 75.0) & (rank < 90.0)],
            "p90-95": jj[(rank >= 90.0) & (rank < 95.0)],
            "p95-99": jj[(rank >= 95.0) & (a < thr99)],
        }
        pops = {"SHOULDER": shoulder, "TAIL": tail}
        gaps = {k: _mean(price_lw, v) - _mean(rt, v) for k, v in pops.items()}
        y["populations"] = {
            "threshold_p99": round(thr99, 2),
            "n_tail": int(tail.size),
            "n_shoulder": int(shoulder.size),
            "shoulder_days": int(len(set((shoulder // 24).tolist()))),
            "gap_lw_minus_rt": {k: round(v, 3) for k, v in gaps.items()},
            "m207_gap": {
                k: m207rec[str(year)]["gaps"][k]["gap_lw_minus_rt"] for k in pops
            },
        }

        # ---- fleet chain ---------------------------------------------------
        cfg = dataclasses.replace(cfg0, weather_year=year, mode="backcast")
        _raw, fleet, arrays, _fp, mc, _zn = build_year(cfg, year)
        mc = np.asarray(mc, dtype=np.float64)
        labels = np.array([m207.class_label(g) for g in fleet], dtype=object)
        groups = np.array([str(g.plant_group or "") for g in fleet], dtype=object)
        zones = np.array([str(g.zone) for g in fleet], dtype=object)
        avail = np.asarray(arrays.availability, dtype=np.float64)
        if avail.ndim == 1:
            avail = np.broadcast_to(avail[:, None], (len(fleet), HOURS))
        pmax = np.asarray(arrays.pmax, dtype=np.float64)
        avail_mw = pmax[:, None] * avail
        thermal_sel = np.isin(labels, list(GAS) + [COAL_POOL])
        cap_by_group = {
            g: float(pmax[groups == g].sum()) for g in np.unique(groups) if g
        }

        # N-1: the cushion reproduces miso-207
        cush = {}
        for k, idx in pops.items():
            per_hour, by_class, by_zone = idle_census(
                idx, mc, avail_mw, labels, zones, price_df
            )
            cush[k] = {"per_hour": per_hour, "by_class": by_class, "by_zone": by_zone}
        y["n1_cushion_reproduces_m207"] = {
            k: {
                "idle_gw_within_20_mean": round(
                    float(cush[k]["per_hour"].mean()) / 1e3, 3
                ),
                "m207": m207rec[str(year)]["setter_and_cushion"][k][
                    "idle_gw_within_band_above_price_total_mean"
                ]["20"],
                "by_class_gw": {
                    c: round(v / 1e3, 3)
                    for c, v in sorted(
                        cush[k]["by_class"].items(), key=lambda kv: -kv[1]
                    )
                },
            }
            for k in pops
        }
        # total idle thermal (leg A headroom) per hour
        idle_thermal = {
            k: (
                avail_mw[thermal_sel][:, idx].sum(axis=0)
                - sum(
                    ch.loc[c, idx].to_numpy()
                    for c in ch.index
                    if c in GAS or c == COAL_POOL
                )
            )
            for k, idx in pops.items()
        }

        # ================================================================ item 0
        e = e930_year(year)
        y["v_key_930"] = _shift_corr(demand, e["D"], jj)
        s930 = y["v_key_930"]["winner"]

        def e_at(key, idx):  # noqa: E306
            j = np.clip(idx + s930, 0, HOURS - 1)
            return np.asarray(e[key], float)[j]

        model_of = {
            k: sum(ch.loc[c].to_numpy() for c in v if c in ch.index)
            for k, v in MODEL_TO_930.items()
        }
        model_of["import"] = (
            ch.loc["import"].to_numpy() if "import" in ch.index else np.zeros(HOURS)
        )
        model_of["BAT"] = st_net
        model_of["D"] = demand
        camp, camp_npl, camp_n = campd_group_series(year)
        item0 = {}
        for k, idx in {**pops, **bands, "OTHER_JJ_DAYTIME": day_other}.items():
            rows = {}
            for f in E930_FUELS + ("D",):
                act = e_at(f, idx)
                mod = model_of[f][idx] if f in model_of else np.zeros(idx.size)
                rows[f] = {
                    "actual_gw": round(float(np.nanmean(act)) / 1e3, 3),
                    "model_gw": round(float(mod.mean()) / 1e3, 3),
                    "model_minus_actual_gw": round(
                        float(np.nanmean(mod - act)) / 1e3, 3
                    ),
                }
            # POST-HOC (disclosed): the 930 fuel rows do not sum to the 930 net
            # generation total — MISO reports a large UNKNOWN fuel category that
            # the parquet does not carry — so a per-fuel "model − actual" on the
            # 930 basis is biased HIGH by that gap (coal/gas mostly). Reported.
            fuel_sum = sum(np.nan_to_num(e_at(f, idx)) for f in E930_FUELS)
            rows["UNK_gap__POSTHOC"] = {
                "ng_total_gw": round(float(np.nanmean(e_at("NG_TOTAL", idx))) / 1e3, 3),
                "sum_fuel_rows_gw": round(float(fuel_sum.mean()) / 1e3, 3),
                "unknown_fuel_gw": round(
                    float(np.nanmean(e_at("NG_TOTAL", idx) - fuel_sum)) / 1e3, 3
                ),
            }
            rows["storage_split__POSTHOC"] = {
                t: round(float(v[idx].mean()) / 1e3, 3) for t, v in st_by_tech.items()
            }
            rows["storage_split__POSTHOC"]["e930_BAT_gw"] = round(
                float(np.nanmean(e_at("BAT", idx))) / 1e3, 3
            )
            act_imp = -e_at("TI", idx)
            rows["import"] = {
                "actual_gw": round(float(np.nanmean(act_imp)) / 1e3, 3),
                "model_gw": round(float(model_of["import"][idx].mean()) / 1e3, 3),
                "model_minus_actual_gw": round(
                    float(np.nanmean(model_of["import"][idx] - act_imp)) / 1e3, 3
                ),
            }
            # per-hour excess on the 930 grain
            ex = np.zeros(idx.size)
            for f in EXCESS_ROWS_930:
                act = act_imp if f == "import" else e_at(f, idx)
                ex += np.maximum(0.0, np.nan_to_num(model_of[f][idx] - act))
            # CAMPD prime-mover split (matched plants)
            split = {}
            ex_c = np.zeros(idx.size)
            for g in (
                "COAL",
                "CC_REGULAR",
                "CC_CHP",
                "CT_PEAKER",
                "CT_CHP",
                "ST_GAS",
                "ST_CHP",
            ):
                act = camp.get(g, np.zeros(HOURS))[idx]
                mk = COAL_POOL if g == "COAL" else g
                mod = (
                    ch.loc[mk, idx].to_numpy() if mk in ch.index else np.zeros(idx.size)
                )
                cap_cls = cap_by_group.get(g, 0.0)
                split[g] = {
                    "actual_matched_gw": round(float(act.mean()) / 1e3, 3),
                    "model_gw": round(float(mod.mean()) / 1e3, 3),
                    "model_minus_actual_gw": round(float((mod - act).mean()) / 1e3, 3),
                    "matched_nameplate_gw": round(camp_npl.get(g, 0.0) / 1e3, 3),
                    "class_capacity_gw": round(cap_cls / 1e3, 3),
                    "coverage": round(camp_npl.get(g, 0.0) / cap_cls, 3)
                    if cap_cls
                    else None,
                    "n_plants_matched": camp_n.get(g, 0),
                    "actual_online_share_of_matched": round(
                        float(act.mean()) / camp_npl[g], 4
                    )
                    if camp_npl.get(g)
                    else None,
                    "model_dispatch_over_capability": round(
                        float(mod.mean())
                        / float(avail_mw[groups == g][:, idx].sum(axis=0).mean()),
                        4,
                    )
                    if (groups == g).any()
                    else None,
                }
                if g in EXCESS_ROWS_CAMPD:
                    ex_c += np.maximum(0.0, mod - act)
            for f in ("NUC", "WAT", "OTH", "import"):
                act = act_imp if f == "import" else e_at(f, idx)
                ex_c += np.maximum(0.0, np.nan_to_num(model_of[f][idx] - act))
            blk = {
                "rows_930": rows,
                "campd_split": split,
                "excess_930_gw_mean": round(float(ex.mean()) / 1e3, 3),
                "excess_930_gw_p50": round(float(np.median(ex)) / 1e3, 3),
                "excess_campd_refined_gw_mean": round(float(ex_c.mean()) / 1e3, 3),
            }
            if k in pops:
                blk["lift_excess_930"] = with_share(
                    lift(idx, mc, avail_mw, zones, price_df, ex), gaps[k]
                )
                blk["lift_excess_campd_refined"] = with_share(
                    lift(idx, mc, avail_mw, zones, price_df, ex_c), gaps[k]
                )
            item0[k] = blk
        y["item0_supply_mix_map"] = item0

        # ================================================================ item 1
        pop_sel = np.isin(groups, POP_GROUPS) & (pmax > 0)
        c_pop = float(pmax[pop_sel].sum())
        offline_m = (pmax[pop_sel][:, None] * (1.0 - avail[pop_sel])).sum(axis=0)
        p_u = np.asarray(miso_outage_mw_series(year, "MISO", UNPLANNED), float)
        p_all = np.asarray(miso_outage_mw_series(year, "MISO", ALL_CAUSES), float)
        p_reg = {
            r: np.asarray(miso_outage_mw_series(year, r, UNPLANNED), float)
            for r in ("North", "Central", "South")
        }
        deficit = np.maximum(0.0, p_u - offline_m)
        # W6 on the population days: capped availability vs measured daily max
        # POST-HOC (disclosed): the record is infeasible against MISO's own
        # metered coal+gas output on many population days, so the deficit is
        # also reported FEASIBILITY-CLIPPED — the largest removal consistent
        # with the day's measured max output: max(0, min(P_U, c_pop - gm) - M).
        ft = pd.read_parquet(RAW_DATA_DIR / "MISO_fueltype.parquet")
        loc = pd.to_datetime(ft["period"], utc=True).dt.tz_convert(
            EST_TZ
        ) - pd.Timedelta(hours=2)
        cg = (
            ft.assign(loc=loc)[ft["fueltype"].isin(["COL", "NG"])]
            .groupby("loc")["value_mwh"]
            .sum()
        )
        cg = cg[cg.index.year == year]
        dmax = cg.groupby(cg.index.normalize()).max()
        dmax = {
            (t.month, t.day): float(v)
            for t, v in dmax.items()
            if not (t.month == 2 and t.day == 29)
        }
        deficit_feas = deficit.copy()
        for d in range(365):
            stamp = m207._stamp(year, d * 24)[:10]
            gm = dmax.get((int(stamp[5:7]), int(stamp[8:10])))
            if gm is None:
                continue
            m_d = float(offline_m[d * 24 : (d + 1) * 24].mean())
            pu_d = float(p_u[d * 24])
            deficit_feas[d * 24 : (d + 1) * 24] = max(0.0, min(pu_d, c_pop - gm) - m_d)
        item1 = {
            "n5_reproduces_miso195": {
                "M_armed_gw_annual": round(float(offline_m.mean()) / 1e3, 3),
                "P_U_gw_annual": round(float(p_u.mean()) / 1e3, 3),
                "P_all_gw_annual": round(float(p_all.mean()) / 1e3, 3),
                "miso195_2025": {"M": 36.82, "P_U": 28.06, "P_all": 48.69},
                "population_gw": round(c_pop / 1e3, 3),
            }
        }
        for k, idx in {**pops, "OTHER_JJ_DAYTIME": day_other}.items():
            days = sorted(set((idx // 24).tolist()))
            viol = []
            for d in days:
                m_d = float(offline_m[d * 24 : (d + 1) * 24].mean())
                pu_d = float(p_u[d * 24])
                stamp = m207._stamp(year, d * 24)[:10]
                mo, dy = int(stamp[5:7]), int(stamp[8:10])
                gm = dmax.get((mo, dy))
                capped = c_pop - max(m_d, pu_d)
                if gm is not None and capped < gm:
                    viol.append(
                        {
                            "day": stamp,
                            "capped_avail_gw": round(capped / 1e3, 2),
                            "measured_max_gw": round(gm / 1e3, 2),
                            "cap_caused": bool(c_pop - m_d >= gm),
                        }
                    )
            blk = {
                "n_days": len(days),
                "M_armed_gw_mean": round(float(offline_m[idx].mean()) / 1e3, 3),
                "P_U_gw_mean": round(float(p_u[idx].mean()) / 1e3, 3),
                "P_all_gw_mean": round(float(p_all[idx].mean()) / 1e3, 3),
                "deficit_gw_mean": round(float(deficit[idx].mean()) / 1e3, 3),
                "deficit_gw_p50": round(float(np.median(deficit[idx])) / 1e3, 3),
                "share_hours_binding": round(float((deficit[idx] > 0).mean()), 4),
                "P_U_by_region_gw_mean": {
                    r: round(float(v[idx].mean()) / 1e3, 3) for r, v in p_reg.items()
                },
                "w6_violation_days": viol,
                "w6_n_violation_days": len(viol),
            }
            if k in pops:
                per_hour = cush[k]["per_hour"]
                blk["w4_conversion"] = {
                    "legA_deficit_over_total_idle_thermal": round(
                        float((deficit[idx] > idle_thermal[k]).mean()), 4
                    ),
                    "legBprime_deficit_over_idle_within_20": round(
                        float((deficit[idx] > per_hour).mean()), 4
                    ),
                    "median_idle_thermal_gw": round(
                        float(np.median(idle_thermal[k])) / 1e3, 3
                    ),
                    "median_idle_within_20_gw": round(
                        float(np.median(per_hour)) / 1e3, 3
                    ),
                }
                blk["lift_deficit"] = with_share(
                    lift(idx, mc, avail_mw, zones, price_df, deficit[idx]), gaps[k]
                )
                blk["lift_P_U_entire"] = with_share(
                    lift(idx, mc, avail_mw, zones, price_df, p_u[idx]), gaps[k]
                )
                blk["deficit_feasibility_clipped__POSTHOC"] = {
                    "deficit_gw_mean": round(float(deficit_feas[idx].mean()) / 1e3, 3),
                    "deficit_gw_p50": round(
                        float(np.median(deficit_feas[idx])) / 1e3, 3
                    ),
                    "share_hours_clip_binds": round(
                        float((deficit_feas[idx] < deficit[idx] - 1e-6).mean()), 4
                    ),
                    "lift": with_share(
                        lift(idx, mc, avail_mw, zones, price_df, deficit_feas[idx]),
                        gaps[k],
                    ),
                }
            item1[k] = blk
        y["item1_outage_record"] = item1

        # ================================================================ item 2
        item2 = {}
        for k, idx in pops.items():
            s = item0[k]["campd_split"]["CT_PEAKER"]
            act = camp.get("CT_PEAKER", np.zeros(HOURS))[idx]
            mod = (
                ch.loc["CT_PEAKER", idx].to_numpy()
                if "CT_PEAKER" in ch.index
                else np.zeros(idx.size)
            )
            d = float((act - mod).mean())
            item2[k] = {
                **s,
                "actual_minus_model_gw": round(d / 1e3, 3),
                "model_ct_idle_within_20_gw": round(
                    cush[k]["by_class"].get("CT_PEAKER", 0.0) / 1e3, 3
                ),
                "verdict": (
                    "real CT fleet RUNNING while the model's sits idle-but-cheap: not a CT-availability object"
                    if d >= 1500
                    else "CT unavailability object"
                    if d <= -1000
                    else "inert"
                ),
            }
        y["item2_ct_conduct"] = item2

        # ================================================================ item 3
        comp = hub_components(year)
        item3 = {}
        if comp is not None:
            y["v_key_lmp"] = _shift_corr(rt, comp["LMP"], jj)
            s_l = y["v_key_lmp"]["winner"]

            def c_at(lbl, idx):  # noqa: E306
                return comp[lbl][np.clip(idx + s_l, 0, HOURS - 1)]

        n_all, n_bind, ssp = m2m_hourly(year)
        any_b, s2n, pbc_names = pbc_rt_hourly(year)
        spread = (price_df[carry].max(axis=1) - price_df[carry].min(axis=1)).to_numpy()
        for k, idx in {**pops, "OTHER_JJ_DAYTIME": day_other}.items():
            blk = {
                "m2m_flowgates_coordinated_mean": round(float(n_all[idx].mean()), 2),
                "m2m_flowgates_binding_mean": round(float(n_bind[idx].mean()), 3),
                "m2m_sum_shadow_mean": round(float(ssp[idx].mean()), 2),
                "rdt_any_binding_share": round(float(any_b[idx].mean()), 4),
                "rdt_south_to_north_binding_share": round(float(s2n[idx].mean()), 4),
                "model_zone_spread_usd_mean": round(float(np.nanmean(spread[idx])), 3),
                "model_zone_spread_usd_max": round(float(np.nanmax(spread[idx])), 2),
            }
            if comp is not None:
                blk["hub_components"] = {
                    lbl: round(float(np.nanmean(c_at(lbl, idx))), 3)
                    for lbl in ("LMP", "MCC", "MLC")
                }
                blk["hub_MEC_mean"] = round(
                    float(
                        np.nanmean(
                            c_at("LMP", idx) - c_at("MCC", idx) - c_at("MLC", idx)
                        )
                    ),
                    3,
                )
                blk["hub_MCC_abs_mean"] = round(
                    float(np.nanmean(np.abs(c_at("MCC", idx)))), 3
                )
            if k in pops:
                bz = cush[k]["by_zone"]
                tot = cush[k]["per_hour"]
                blk["cushion_by_zone_gw"] = {
                    z: round(float(v.mean()) / 1e3, 3) for z, v in bz.items()
                }
                south = bz.get("MISO-South", np.zeros(idx.size))
                blk["south_share_of_cushion"] = (
                    round(float(south.sum() / tot.sum()), 4) if tot.sum() else None
                )
                blk["mcc_share_of_gap"] = (
                    round(abs(blk["hub_components"]["MCC"]) / abs(gaps[k]), 4)
                    if comp is not None
                    else None
                )
                strand = np.where(s2n[idx], south, 0.0)
                blk["lift_strand_south_in_rdt_hours"] = with_share(
                    lift(idx, mc, avail_mw, zones, price_df, strand), gaps[k]
                )
                blk["lift_strand_south_all_hours"] = with_share(
                    lift(idx, mc, avail_mw, zones, price_df, south), gaps[k]
                )
            item3[k] = blk
        item3["rdt_constraint_names_year"] = dict(
            sorted(pbc_names.items(), key=lambda kv: -kv[1])[:6]
        )
        y["item3_deliverability"] = item3

        # ================================================================ item 4
        wm = window_masks(year)
        item4 = {"windows": wm["rows"]}
        for k, idx in pops.items():
            inw = wm["any"][idx]
            wp = wm["warning_plus"][idx]
            g_h = price_lw[idx] - rt[idx]
            tot = float(g_h.sum())
            blk = {
                "n_in_any_window": int(inw.sum()),
                "share_in_any_window": round(float(inw.mean()), 4),
                "n_in_warning_plus": int(wp.sum()),
                "gap_share_in_any_window": round(float(g_h[inw].sum() / tot), 4)
                if tot
                else None,
                "gap_share_in_warning_plus": round(float(g_h[wp].sum() / tot), 4)
                if tot
                else None,
                "actual_mean_in_window": round(float(rt[idx][inw].mean()), 2)
                if inw.any()
                else None,
                "actual_mean_out_of_window": round(float(rt[idx][~inw].mean()), 2)
                if (~inw).any()
                else None,
                "model_mean_in_window": round(float(price_lw[idx][inw].mean()), 2)
                if inw.any()
                else None,
                "model_mean_out_of_window": round(float(price_lw[idx][~inw].mean()), 2)
                if (~inw).any()
                else None,
                "out_of_window_gap_mean": round(float(g_h[~inw].mean()), 3)
                if (~inw).any()
                else None,
                "regspin_bind_hours_in_window": None,
            }
            item4[k] = blk
        wp_all = np.where(wm["warning_plus_as_armed"])[0]
        item4["tier_floor_check"] = {
            "note": "read on the hours the keeper ACTUALLY repriced (registry EST placement, one hour late on the CST model clock)",
            "n_warning_plus_hours": int(wp_all.size),
            "model_price_max_in_windows": round(float(np.nanmax(price_lw[wp_all])), 2)
            if wp_all.size
            else None,
            "slack_mwh_in_windows": round(float(slack[wp_all].sum()), 1)
            if wp_all.size
            else None,
            "min_idle_thermal_gw_in_windows": round(
                float(
                    (
                        avail_mw[thermal_sel][:, wp_all].sum(axis=0)
                        - sum(
                            ch.loc[c, wp_all].to_numpy()
                            for c in ch.index
                            if c in GAS or c == COAL_POOL
                        )
                    ).min()
                )
                / 1e3,
                3,
            )
            if wp_all.size
            else None,
            "tier_floor_printed": bool(
                wp_all.size and np.nanmax(price_lw[wp_all]) >= 500.0
            ),
        }
        rf = m207.reserve_frame(year)
        rs = (
            rf[rf["family"] == "miso_rbdc_regspin"]
            .set_index("hour")["dual"]
            .reindex(range(HOURS))
            .fillna(0)
            .to_numpy()
        )
        for k, idx in pops.items():
            item4[k]["regspin_bind_hours_in_window"] = int(
                ((np.abs(rs[idx]) > 0.01) & wm["any"][idx]).sum()
            )
            item4[k]["regspin_bind_hours_total"] = int((np.abs(rs[idx]) > 0.01).sum())
        y["item4_emergency_windows"] = item4

        report["years"][str(year)] = y
        del mc, avail_mw, avail, arrays, fleet
        print(f"{year} done", flush=True)

    # ---------------------------------------------------------------- verdict
    d = report["years"]["2025"]
    v = {}
    for k in ("SHOULDER", "TAIL"):
        v[k] = {
            "gap": d["populations"]["gap_lw_minus_rt"][k],
            "excess_930_gw": d["item0_supply_mix_map"][k]["excess_930_gw_mean"],
            "excess_campd_gw": d["item0_supply_mix_map"][k][
                "excess_campd_refined_gw_mean"
            ],
            "share_item0_930": d["item0_supply_mix_map"][k]["lift_excess_930"][
                "share_of_gap"
            ],
            "share_item0_campd": d["item0_supply_mix_map"][k][
                "lift_excess_campd_refined"
            ]["share_of_gap"],
            "share_item1_deficit": d["item1_outage_record"][k]["lift_deficit"][
                "share_of_gap"
            ],
            "item2": d["item2_ct_conduct"][k]["verdict"],
            "mcc_share_item3": d["item3_deliverability"][k]["mcc_share_of_gap"],
            "share_item3_strand": d["item3_deliverability"][k][
                "lift_strand_south_in_rdt_hours"
            ]["share_of_gap"],
            "item4_gap_share_in_window": d["item4_emergency_windows"][k][
                "gap_share_in_any_window"
            ],
        }
    v["P9_any_candidate_reaches_both"] = bool(
        all(d["item1_outage_record"][k]["lift_deficit"]["reaches_25pct"] for k in pops)
        or all(
            d["item3_deliverability"][k]["lift_strand_south_in_rdt_hours"][
                "reaches_25pct"
            ]
            for k in pops
        )
    )
    v["tier_floor_printed_2025"] = d["item4_emergency_windows"]["tier_floor_check"][
        "tier_floor_printed"
    ]
    report["verdict"] = v
    OUT.write_text(json.dumps(report, indent=1, default=float))
    print(f"wrote {OUT.relative_to(REPO)}")
    print(json.dumps(v, indent=1))


if __name__ == "__main__":
    main()
