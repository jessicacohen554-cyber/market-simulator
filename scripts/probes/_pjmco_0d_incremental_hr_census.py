"""PJM close-out census 0d (zero LP): CC_REGULAR incremental heat rate vs the keeper's econ band.

Plan ``docs/backcast-closeout-plan-2026-10.md`` §3.6 step 0d; research shard
``docs/records/governance/closeout-2026-10/SHARD-PJM-closeout-research-2026-10-02.md``
§4 L2. Pre-fixed reading: charter L2 iff (model econ-band HR - measured incremental HR)
>= 0.8 MMBtu/MWh, capacity-weighted over PJM CC_REGULAR, per year (headline 2020).
Also reported: whether the ``pjm_offer_midcurve`` belt prices the CC econ band above
the incremental cost (a rule-19 blocker for L2 even when the gap clears).

Nothing here solves, builds a fleet or touches ``data/clean``. Inputs:

* MEASURED (a) - EPA CAMPD unit-level hourly CEMS (``data/raw/campd-unit-level``,
  PJM states from ``campd.ISO_STATES``), units whose ``unitType`` starts with
  "combined cycle" at the keeper's CC_REGULAR plant codes. Per unit-year a Huber-IRLS
  linear fit ``heatInput = a + b * grossLoad`` over steady economic hours: opTime >= 0.99
  in the hour, the two hours before and the hour after (drops start-up / shut-down
  ramps), and grossLoad in [max(p5, 0.40 * p99), p99] of the unit's own running load
  (drops sub-min-load and spike hours); >= 200 hours and a load spread >= 10 % of p99,
  slope inside [3, 15] MMBtu/MWh, else the unit is not identified. ``b`` is the
  incremental HR (gross basis); the average HR is sum(HI)/sum(gross) over the SAME
  hours. Plant value = fit-MWh-weighted mean over its CC units, then moved to a
  whole-plant NET basis by ``k = CAMPD CC gross (all hours) / EIA-923 CC net``
  (prime movers CA/CT/CS, ``eia923_monthly_generation.parquet``): ~1.03 where the CEMS
  gross meters CT + ST, ~0.65 where only the CTs are metered (the CT-only signature,
  ``_pjm_cc_netgross_bases.py`` block 2) - in both cases ``b * k`` is MMBtu per whole-
  plant net MWh, assuming the unmetered ST output tracks CT output.
* MODEL (b) - the keeper's committed per-unit layer
  ``results/calibration/pjmnext16_A_span/hourly/unit_marginal_<y>.parquet`` (P1 offer
  ``mc``). CC_REGULAR econ rows (``econcNN``) are priced by the belt's SHAPE form
  (``pjm_offer_midcurve_shape_segments=['CC_LIKE']``):
  ``bid_g = (mc_c - vom) * m(s_g, bin)/m(s_c, bin) + vom`` with ``c`` the plant's
  ``committed`` row, whose heat rate is ``base_HR * offer['committed']`` (1.0 in the
  keeper) and ``base_HR`` the measured CC artifact (``measured_cc_heat_rates``). So the
  econ row's heat rate on the plant's own fuel(+RGGI) basis is exactly
  ``HR_c * (mc_g - vom)/(mc_c - vom)`` - fuel cancels, no price input needed.
  Capacity-weighted (econ-row cap) over all 8760 hours of the offer.
* BELT (c) - ``data/raw/_validation-source/pjm_offer_midcurve_condbinned.json``
  CC_LIKE ladders; each econ row's within-plant share and each hour's net-load bin are
  rebuilt exactly as ``_pjm_midcurve_context`` does (shares from the row caps ordered by
  mean offer; bins from the bundle's demand - solar - wind via ``_tightness_hour_bin``).
  ``belt level HR`` = m(s_g, bin) (the measured offer / delivered-gas-day multiplier the
  floor/level form would impose); the shape form's predicted ratio is checked against
  the bundle's observed ratio (fidelity).

Writes ``results/phase0/pjm/_pjmco_0d_incremental_hr_census.json`` (+ ``_plants.csv``).
Run: ``python3 scripts/probes/_pjmco_0d_incremental_hr_census.py [YEAR ...]``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.constants import VOM  # noqa: E402
from market_sim.data.campd import ISO_STATES  # noqa: E402
from market_sim.data.fleet.campd_bins import measured_cc_heat_rates  # noqa: E402
from market_sim.data.fleet.offer_surfaces import _tightness_hour_bin  # noqa: E402

KEEPER = REPO / "results/calibration/pjmnext16_A_span"
HOURLY = KEEPER / "hourly"
CAMPD = REPO / "data/raw/campd-unit-level"
E923 = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
SURFACE = REPO / "data/raw/_validation-source/pjm_offer_midcurve_condbinned.json"
OUT = REPO / "results/phase0/pjm/_pjmco_0d_incremental_hr_census.json"
OUT_CSV = REPO / "results/phase0/pjm/_pjmco_0d_incremental_hr_census_plants.csv"

YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
HEADLINE_YEAR = 2020
THRESHOLD = 0.8  # MMBtu/MWh, pre-fixed in the PRECOMMIT / plan §3.6 0d
CLASS = "CC_REGULAR"
VOM_CC = float(VOM["gas_cc"])
OPTIME_MIN = 0.99
PRE_STEADY, POST_STEADY = 2, 1  # hours that must also be fully on (start-up / shut-down)
MINLOAD_FRAC = 0.40  # of the unit's p99 load
LOAD_PCT_LO, LOAD_PCT_HI = 5.0, 99.0
MIN_HOURS = 200
SENS_PCT_HI = 90.0  # sensitivity window top (pre-duct-firing)
MIN_SPREAD = 0.10
SLOPE_BAND = (3.0, 15.0)
HUBER_K = 1.345
CC_PRIME_MOVERS = ("CA", "CT", "CS")
MONTHS = (
    "january february march april may june july august september october "
    "november december"
).split()


# ----------------------------------------------------------------------------- measured
def huber_line(x: np.ndarray, y: np.ndarray, iters: int = 30) -> tuple[float, float]:
    """Return ``(intercept, slope)`` of a Huber-IRLS robust line fit of y on x."""
    w = np.ones_like(x)
    a = b = 0.0
    for _ in range(iters):
        sw = w.sum()
        xm, ym = (w * x).sum() / sw, (w * y).sum() / sw
        sxx = (w * (x - xm) ** 2).sum()
        if sxx <= 0:
            return float("nan"), float("nan")
        b_new = (w * (x - xm) * (y - ym)).sum() / sxx
        a_new = ym - b_new * xm
        r = y - a_new - b_new * x
        s = 1.4826 * np.median(np.abs(r - np.median(r))) or 1e-9
        u = np.abs(r) / (HUBER_K * s)
        w = np.where(u <= 1.0, 1.0, 1.0 / np.maximum(u, 1e-12))
        if abs(b_new - b) < 1e-6 and abs(a_new - a) < 1e-4:
            a, b = a_new, b_new
            break
        a, b = a_new, b_new
    return float(a), float(b)


def campd_cc_year(year: int, plants: set[int]) -> pd.DataFrame:
    """CC-unit CEMS hours for ``plants`` in ``year``, streamed state by state."""
    cols = ["facilityId", "unitId", "date", "hour", "opTime", "grossLoad", "heatInput", "unitType"]
    ids = [str(p) for p in sorted(plants)]
    frames = []
    for st in ISO_STATES["PJM"]:
        f = CAMPD / f"{st}_{year}.parquet"
        if not f.exists():
            continue
        d = pq.read_table(f, columns=cols, filters=[("facilityId", "in", ids)]).to_pandas()
        if d.empty:
            continue
        d = d[d["unitType"].astype(str).str.lower().str.startswith("combined cycle")]
        frames.append(d.drop(columns="unitType"))
    if not frames:
        return pd.DataFrame(columns=cols[:-1])
    d = pd.concat(frames, ignore_index=True)
    d["facilityId"] = d["facilityId"].astype(int)
    d["ts"] = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    return d.drop(columns=["date", "hour"])


def fit_units(d: pd.DataFrame) -> pd.DataFrame:
    """Per-unit incremental (slope) and average HR over steady economic hours."""
    out = []
    for (pid, uid), u in d.groupby(["facilityId", "unitId"], sort=False):
        u = u.sort_values("ts")
        u = u.set_index("ts")
        idx = pd.date_range(u.index.min(), u.index.max(), freq="h")
        u = u[~u.index.duplicated()].reindex(idx)
        on = (u["opTime"].fillna(0) >= OPTIME_MIN) & (u["grossLoad"].fillna(0) > 0) & (
            u["heatInput"].fillna(0) > 0
        )
        steady = on.copy()
        for k in range(1, PRE_STEADY + 1):
            steady &= on.shift(k, fill_value=False)
        for k in range(1, POST_STEADY + 1):
            steady &= on.shift(-k, fill_value=False)
        gross_all = float(u["grossLoad"].fillna(0).sum())
        s = u[steady]
        rec = {"plant_code": int(pid), "unit_id": str(uid), "gross_mwh_all": gross_all}
        if len(s) < MIN_HOURS:
            out.append({**rec, "n_fit": int(len(s)), "status": "few_hours"})
            continue
        x, y = s["grossLoad"].to_numpy(float), s["heatInput"].to_numpy(float)
        hsl = np.percentile(x, LOAD_PCT_HI)
        lo = max(np.percentile(x, LOAD_PCT_LO), MINLOAD_FRAC * hsl)
        m = (x >= lo) & (x <= hsl)
        x, y = x[m], y[m]
        if len(x) < MIN_HOURS or (np.percentile(x, 95) - np.percentile(x, 5)) < MIN_SPREAD * hsl:
            out.append({**rec, "n_fit": int(len(x)), "status": "no_spread"})
            continue
        a, b = huber_line(x, y)
        ok = SLOPE_BAND[0] <= b <= SLOPE_BAND[1]
        # Sensitivity: cap the window at p90 (drops the duct-fired top, which the
        # model prices in its separate ``peak`` tranche).
        m90 = x <= np.percentile(x, SENS_PCT_HI)
        b90 = huber_line(x[m90], y[m90])[1] if m90.sum() >= MIN_HOURS else float("nan")
        out.append(
            {
                **rec,
                "n_fit": int(len(x)),
                "fit_mwh": float(x.sum()),
                "load_lo": float(lo),
                "load_hi": float(hsl),
                "inc_hr_gross": b,
                "inc_hr_gross_p90": b90 if SLOPE_BAND[0] <= b90 <= SLOPE_BAND[1] else float("nan"),
                "noload_mmbtu_h": a,
                "avg_hr_gross": float(y.sum() / x.sum()),
                "status": "ok" if ok else "slope_out_of_band",
            }
        )
    return pd.DataFrame(out)


def e923_cc_net(year: int, plants: set[int]) -> pd.Series:
    """EIA-923 annual CC net MWh (prime movers CA/CT/CS) per plant."""
    e = pd.read_parquet(E923)
    e = e[(e["year"] == year) & e["plant_id"].isin(plants) & e["prime_mover"].isin(CC_PRIME_MOVERS)]
    return e.groupby("plant_id")["netgen_annual_mwh"].sum()


def measured_plants(year: int, plants: set[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Plant-year measured incremental / average HR on a whole-plant net basis."""
    units = fit_units(campd_cc_year(year, plants))
    if units.empty:
        return pd.DataFrame(), units
    gross = units.groupby("plant_code")["gross_mwh_all"].sum()
    net = e923_cc_net(year, plants)
    ok = units[units["status"] == "ok"]
    rows = []
    for pid, g in ok.groupby("plant_code"):
        w = g["fit_mwh"].to_numpy()
        n = float(net.get(pid, np.nan))
        k = float(gross[pid] / n) if n and n > 0 else np.nan
        rows.append(
            {
                "plant_code": int(pid),
                "n_units_fit": int(len(g)),
                "n_units_cc": int((units["plant_code"] == pid).sum()),
                "inc_hr_gross": float(np.average(g["inc_hr_gross"], weights=w)),
                "inc_hr_gross_p90": float(
                    np.average(g["inc_hr_gross_p90"].fillna(g["inc_hr_gross"]), weights=w)
                ),
                "avg_hr_gross": float(np.average(g["avg_hr_gross"], weights=w)),
                "campd_gross_mwh": float(gross[pid]),
                "e923_net_mwh": n,
                "k_gross_over_net": k,
                "ct_only_meter": bool(np.isfinite(k) and k < 0.8),
            }
        )
    p = pd.DataFrame(rows)
    if not p.empty:
        p["inc_hr_net"] = p["inc_hr_gross"] * p["k_gross_over_net"]
        p["inc_hr_net_p90"] = p["inc_hr_gross_p90"] * p["k_gross_over_net"]
        p["avg_hr_net"] = p["avg_hr_gross"] * p["k_gross_over_net"]
    return p, units


# ----------------------------------------------------------------------------- model
def egrid_fallback_hr(year: int) -> dict[int, float]:
    """``{plant: eGRID HR}`` the fleet keeps where the measured CC artifact refuses a row.

    Read from the same artifact's ``model_heat_rate_egrid`` column (solve year's row,
    else pooled ``year == 0``) for plants whose applied row is not ``ok`` (the
    ``steam_not_metered`` CT-only reporters); validated in the output by the
    ``fuel_basis_over_gasday`` column landing with its zone neighbours.
    """
    a = pd.read_csv(
        REPO / "data/raw/_processed-legacy/campd_cc_heat_rates_PJM.csv",
        usecols=["plant_code", "year", "model_heat_rate_egrid"],
    )
    out = dict(a[a["year"] == 0].set_index("plant_code")["model_heat_rate_egrid"])
    out.update(a[a["year"] == year].set_index("plant_code")["model_heat_rate_egrid"])
    return {int(k): float(v) for k, v in out.items() if np.isfinite(v)}


def net_load(year: int) -> np.ndarray:
    """Bundle demand - solar - wind (P1), the belt's tightness driver (dispatched VRE)."""
    s = pd.read_parquet(HOURLY / f"system_{year}.parquet", columns=["pass", "hour", "demand"])
    dem = s[s["pass"] == "P1"].groupby("hour")["demand"].sum().sort_index()
    c = pd.read_parquet(HOURLY / f"class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & c["klass"].isin(["solar", "wind"])]
    vre = c.groupby("hour")["mw"].sum().reindex(dem.index, fill_value=0.0)
    return (dem - vre).to_numpy(float)


def model_plants(year: int, surface: dict) -> tuple[pd.DataFrame, dict]:
    """Per CC_REGULAR plant: econ-band HR (shape form), belt level HR, fidelity."""
    t = pq.read_table(
        HOURLY / f"unit_marginal_{year}.parquet",
        columns=["unit_id", "plant_code", "plant_group", "hour", "mc", "cap_mw", "pass"],
        filters=[("plant_group", "=", CLASS)],
    ).to_pandas()
    t = t[t["pass"] == "P1"]
    t["unit_id"] = t["unit_id"].astype(str)
    mc = t.pivot(index="unit_id", columns="hour", values="mc").sort_index(axis=1)
    cap = t.groupby("unit_id")["cap_mw"].max()
    pcode = t.groupby("unit_id")["plant_code"].first()
    T = mc.shape[1]
    hr_meas = measured_cc_heat_rates("PJM", year)
    hr_fallback = egrid_fallback_hr(year)

    prov = surface["_provenance"]
    edges = tuple(float(x) for x in prov["netload_pct_edges"])
    shares_grid = np.asarray(prov["shares"], float)
    ent = surface["CC_LIKE"]
    ladders = ent["years"].get(str(year)) or ent["pooled"]
    table = np.array([[float(p[1]) for p in lad] for lad in ladders])  # (bins, shares)
    hour_bin = _tightness_hour_bin(net_load(year)[:T], edges)

    def m_of(share: float) -> np.ndarray:
        """(T,) measured CC_LIKE multiplier at a within-plant share."""
        return np.array([np.interp(share, shares_grid, table[b]) for b in range(len(table))])[hour_bin]

    hours = pd.date_range(f"{year}-01-01", periods=T, freq="h").normalize()
    hh = pd.read_csv(REPO / "data/raw/gas-prices/henry_hub_daily.csv", parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL

    gas_day = (s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["PJM"])).reindex(hours).ffill().bfill().to_numpy()

    rows, fid = [], []
    prefix = pd.Series(mc.index, index=mc.index).str.rpartition("_")[0]
    for pre, ids in prefix.groupby(prefix).groups.items():
        ids = list(ids)
        com = [u for u in ids if u.endswith("_committed")]
        econ = [u for u in ids if u.rpartition("_")[2].startswith("econ")]
        if not com or not econ:
            continue
        c = com[0]
        pid = int(pcode[c])
        order = sorted(ids, key=lambda u: float(mc.loc[u].mean()))
        caps = cap[order].to_numpy(float)
        if caps.sum() <= 0.0 or float(cap[econ].sum()) <= 0.0:
            continue  # retired / zero-capacity plant-year: no offer to read
        mids = (np.cumsum(caps) - 0.5 * caps) / caps.sum()
        share = dict(zip(order, mids))
        mcc = mc.loc[c].to_numpy(float)
        hr_c = hr_meas.get(pid, np.nan)
        hr_src = "measured_cc_artifact"
        if not np.isfinite(hr_c):
            hr_c, hr_src = hr_fallback.get(pid, np.nan), "egrid_fallback"
        m_c = m_of(share[c])
        ec = cap[econ].to_numpy(float)
        ratios = np.vstack([(mc.loc[u].to_numpy(float) - VOM_CC) / (mcc - VOM_CC) for u in econ])
        belt = np.vstack([m_of(share[u]) for u in econ])  # level HR, gas-day basis
        allin = np.vstack([(mc.loc[u].to_numpy(float) - VOM_CC) / gas_day for u in econ])
        pred = belt / m_c
        fid.append(float(np.nanmedian(np.abs(ratios - pred))))
        lo = int(np.argmin([share[u] for u in econ]))
        rows.append(
            {
                "plant_code": pid,
                "unit_prefix": pre,
                "econ_cap_mw": float(ec.sum()),
                "committed_cap_mw": float(cap[c]),
                "committed_share": float(share[c]),
                "econ_shares": [round(float(share[u]), 3) for u in econ],
                "hr_committed_model": float(hr_c),
                "hr_committed_source": hr_src if np.isfinite(hr_c) else "none",
                "econ_ratio_mean": float(np.average(ratios.mean(axis=1), weights=ec)),
                "model_econ_hr": float(hr_c * np.average(ratios.mean(axis=1), weights=ec)),
                "model_econ_lowest_hr": float(hr_c * ratios[lo].mean()),
                "allin_econ_hr_gasday": float(np.average(allin.mean(axis=1), weights=ec)),
                "belt_level_hr_gasday": float(np.average(belt.mean(axis=1), weights=ec)),
                "belt_level_committed_hr_gasday": float(m_c.mean()),
                "fuel_basis_over_gasday": float(np.median((mcc - VOM_CC) / hr_c / gas_day))
                if np.isfinite(hr_c) else float("nan"),
            }
        )
    meta = {
        "shape_form_fidelity_median_abs_ratio_err": float(np.median(fid)) if fid else None,
        "n_plants_model": len(rows),
        "n_plants_no_measured_hr": int(sum(np.isnan(r["hr_committed_model"]) for r in rows)),
        "gas_day_mean": float(gas_day.mean()),
    }
    return pd.DataFrame(rows), meta


# ----------------------------------------------------------------------------- census
def wavg(df: pd.DataFrame, col: str, w: str = "econ_cap_mw") -> float:
    """Capacity-weighted mean of ``col`` over finite rows."""
    d = df[np.isfinite(df[col]) & np.isfinite(df[w])]
    return float(np.average(d[col], weights=d[w])) if len(d) else float("nan")


def census_year(year: int, surface: dict) -> tuple[dict, pd.DataFrame]:
    """One year's matched-plant census row and the plant table."""
    mp, meta = model_plants(year, surface)
    meas, units = measured_plants(year, set(mp["plant_code"]))
    df = mp.merge(meas, on="plant_code", how="left")
    df["year"] = year
    matched = df[np.isfinite(df["model_econ_hr"]) & np.isfinite(df.get("inc_hr_net", np.nan))]
    row = {
        "year": year,
        "n_plants_model": int(len(mp)),
        "n_plants_matched": int(len(matched)),
        "econ_cap_mw_model": float(mp["econ_cap_mw"].sum()),
        "econ_cap_mw_matched": float(matched["econ_cap_mw"].sum()),
        "n_ct_only_meter_matched": int(matched["ct_only_meter"].sum()),
        "unit_fit_status": units["status"].value_counts().to_dict() if len(units) else {},
        "model_econ_hr": wavg(matched, "model_econ_hr"),
        "model_econ_lowest_slice_hr": wavg(matched, "model_econ_lowest_hr"),
        "model_committed_hr": wavg(matched, "hr_committed_model"),
        "measured_incremental_hr": wavg(matched, "inc_hr_net"),
        "measured_average_hr": wavg(matched, "avg_hr_net"),
        "measured_incremental_hr_p90window": wavg(matched, "inc_hr_net_p90"),
        "n_matched_egrid_fallback_hr": int((matched["hr_committed_source"] == "egrid_fallback").sum()),
        "allin_econ_hr_gasday": wavg(matched, "allin_econ_hr_gasday"),
        "belt_level_hr_gasday": wavg(matched, "belt_level_hr_gasday"),
        "belt_level_committed_hr_gasday": wavg(matched, "belt_level_committed_hr_gasday"),
        "fuel_basis_over_gasday_median": float(np.nanmedian(matched["fuel_basis_over_gasday"])),
        **meta,
    }
    row["gap"] = row["model_econ_hr"] - row["measured_incremental_hr"]
    row["gap_p90window"] = row["model_econ_hr"] - row["measured_incremental_hr_p90window"]
    row["gap_lowest_slice"] = row["model_econ_lowest_slice_hr"] - row["measured_incremental_hr"]
    row["gap_clears_0p8"] = bool(row["gap"] >= THRESHOLD)
    # Belt binds above incremental cost: the shape form SETS the econ rows, so the
    # belt-priced econ HR is model_econ_hr itself; the level/floor-form target
    # (gas-day basis, translated to the plant's own fuel basis) is the second read.
    row["belt_econ_above_incremental"] = bool(row["model_econ_hr"] > row["measured_incremental_hr"])
    row["belt_level_hr_plant_fuel_basis"] = row["belt_level_hr_gasday"] / row["fuel_basis_over_gasday_median"]
    row["belt_level_above_incremental"] = bool(
        row["belt_level_hr_plant_fuel_basis"] > row["measured_incremental_hr"]
    )
    return row, df


def main(years: list[int]) -> None:
    """Run the census for ``years`` and write the JSON + plant CSV."""
    surface = json.loads(SURFACE.read_text())
    rows, plants = [], []
    for y in years:
        r, df = census_year(y, surface)
        rows.append(r)
        plants.append(df)
        print(
            f"{y}: n={r['n_plants_matched']}/{r['n_plants_model']} model_econ={r['model_econ_hr']:.3f} "
            f"lowest={r['model_econ_lowest_slice_hr']:.3f} inc={r['measured_incremental_hr']:.3f} "
            f"avg={r['measured_average_hr']:.3f} inc90={r['measured_incremental_hr_p90window']:.3f} gap={r['gap']:+.3f} belt_lvl={r['belt_level_hr_gasday']:.3f} "
            f"fid={r['shape_form_fidelity_median_abs_ratio_err']:.4f}",
            flush=True,
        )
    head = next((r for r in rows if r["year"] == HEADLINE_YEAR), None)
    verdict = {
        "rule": f"charter L2 iff (model econ-band HR - measured incremental HR) >= {THRESHOLD} "
        "MMBtu/MWh, CC_REGULAR capacity-weighted, headline 2020",
        "headline_year": HEADLINE_YEAR,
        "headline_gap": None if head is None else head["gap"],
        "verdict": None if head is None else ("PASS" if head["gap_clears_0p8"] else "FAIL"),
        "years_clearing": [r["year"] for r in rows if r["gap_clears_0p8"]],
        "rule19_belt_econ_above_incremental_years": [
            r["year"] for r in rows if r["belt_econ_above_incremental"]
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "census": "PJM close-out 0d - CC_REGULAR incremental HR vs model econ band vs midcurve belt",
                "keeper_bundle": str(KEEPER.relative_to(REPO)),
                "method": __doc__,
                "verdict": verdict,
                "years": rows,
            },
            indent=2,
            default=str,
        )
    )
    pd.concat(plants, ignore_index=True).to_csv(OUT_CSV, index=False)
    print(json.dumps(verdict, indent=2))
    print(f"wrote {OUT}\nwrote {OUT_CSV}")


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or list(YEARS))
