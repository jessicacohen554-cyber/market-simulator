"""nwpp-49 phase 0: can ``hydro_pondage_bound`` touch NWPP's hydro swing? ZERO LP.

Reproduces every number in
``docs/handoffs/FINDING-nwpp-49-pondage-design-2026-09-23.md`` from committed
artifacts only:

* the keeper's committed ``hourly/class_hourly_<y>.parquet``
  (``results/calibration/nwpp47_gridwind_span``, rule 15 ``[R-DASHBOARD]``);
* ``data/raw/nwpp-hydro/nwpp_hydro_pondage.csv`` (NID storage, this lane's intake);
* ``data/raw/nwpp-hydro/nwpp_hydro_cascade_{links,monthly}.csv`` (NWPP-36's
  measured operated pondage bands and water-to-energy ratios);
* ``data/raw/nwpp-hydro/nwpp_hydro_budget.parquet`` (the EIA-923 monthly budget);
* ``data/raw/nwpp-hydro/crohms/nwpp_crohms_hourly.parquet`` (measured hourly
  generation at the 16 CROHMS projects);
* the scorer's EIA-930 pool benchmark (17 per-BA extracts, ``_pool_hourly_benchmark``).

The static clip needs PER-PLANT model dispatch, which is not on ``main`` (the
NWPP-47 legs' ``dispatch/<y>_P1.parquet`` went with their shard branches, rule
33(f)). So each plant's model shape is a PRO-RATA PROXY: the keeper's fleet
hydro hour scaled by the plant's share of that month's budget. That is an
assumption, stated in the FINDING, and it is the reason the evaluator
(``_nwpp49_gates.py``) scores the LP legs against the keeper's own hourlies,
never against this proxy.

Usage::

    PYTHONPATH=.:src uv run --no-sync python3 scripts/probes/_nwpp49_pondage_phase0.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.fleet import _hour_to_month_index

BUNDLE = Path("results/calibration/nwpp47_gridwind_span")
HYDRO = Path("data/raw/nwpp-hydro")
YEARS = (2023, 2024, 2025)
COAL = ("COAL_BIT", "COAL_PRB", "COAL_WC")
N = 8760
# Keeper recipe: meta.json --hydro-backfill-year 2024 (2025 EIA-923 is an early release).
BACKFILL_YEAR = 2024
# Cascade membership at the keeper (NWPP-40 resolve line, FINDING-nwpp-36).
CASCADE_ROW = (3921, 3886, 6200, 3075, 3925)  # CHJ WEL RIS BON IHR: carry the cascade row
CASCADE_UP_ONLY = (6163, 3883, 3895, 3927)  # GCL RRH TDA LMN: P enters a downstream row only
# Diurnal bound: at a flat daily inflow, ANY within-day shape needs at most
# 24*c*(1-c) nameplate-hours of storage, maximised at c = 0.5 -> 6 h. A plant
# holding >= 6 nameplate-hours cannot be constrained WITHIN a day. Pure algebra.
DIURNAL_MAX_H = 6.0
OUT = Path("results/calibration/_nwpp49_pondage_phase0.json")


def _r(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r."""
    return float(np.corrcoef(a, b)[0, 1])


def _split(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (daily-mean broadcast, within-day deviation) of an hourly vector."""
    x = x[: len(x) // 24 * 24].reshape(-1, 24)
    dm = x.mean(1, keepdims=True)
    return np.repeat(dm.ravel(), 24), (x - dm).ravel()


def model_class(y: int, klasses: tuple[str, ...]) -> np.ndarray:
    """Keeper P1 hourly MW summed over ``klasses``."""
    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{y}.parquet")
    ch = ch[(ch["pass"] == "P1") & ch.klass.isin(klasses)]
    return ch.groupby("hour").mw.sum().reindex(range(N), fill_value=0).to_numpy(float)


def e930(y: int, series: str) -> np.ndarray:
    """One NWPP EIA-930 benchmark series, via the scorer's own pool builder.

    ``build_calibration_reference._pool_hourly_benchmark`` is the dict the
    ``eia930`` bundle input and the scorer's reference are both built from
    (``run_calibration_full._eia930_frame_generic``), so the r printed here is
    the scored r, spike screen and non-leap calendar included.
    """
    from scripts.data.build_calibration_reference import _pool_hourly_benchmark

    if y not in _BENCH:
        _BENCH[y] = _pool_hourly_benchmark("NWPP", y)
    return np.asarray(_BENCH[y][series], dtype=float)[:N]


_BENCH: dict[int, dict] = {}


def fleet_budget(y: int) -> pd.DataFrame:
    """Per-plant monthly budget (MWh, clipped >= 0) for the keeper's year-y fleet."""
    b = pd.read_parquet(HYDRO / "nwpp_hydro_budget.parquet")
    m = [f"m{i:02d}" for i in range(1, 13)]
    own = b[(b.year == y) & b.loader_kept]
    if y == 2025:  # keeper backfills every plant without a 2025 series with 2024 water
        fill = b[(b.year == BACKFILL_YEAR) & b.loader_kept & ~b.plant_id.isin(own.plant_id)]
        own = pd.concat([own, fill])
    out = own[["plant_id", "max_mw"] + m].copy()
    out[m] = out[m].clip(lower=0.0)
    return out.groupby("plant_id", as_index=False).agg({"max_mw": "max", **{c: "sum" for c in m}})


def max_drawdown(inflow: np.ndarray, p: np.ndarray) -> float:
    """Smallest storage B (MWh) under which ``p`` is feasible given ``inflow``.

    V(t) = min(B, V(t-1) + I - P) with free spill; infeasible iff V < 0. The
    required B is the largest net withdrawal over any window: the max drawdown
    of cumsum(I - P). The year is tiled twice so a cyclic window counts.
    """
    c = np.cumsum(np.tile(inflow - p, 2))
    return float((np.maximum.accumulate(np.maximum(c, 0.0)) - c).max())


def storage_tables() -> tuple[dict[int, float], dict[int, float]]:
    """NID storage (MWh) and the measured operated band (MWh) per plant."""
    nid = pd.read_csv(HYDRO / "nwpp_hydro_pondage.csv")
    nid_b = dict(zip(nid.plant_id.astype(int), nid.storage_mwh.astype(float)))
    links = pd.read_csv(HYDRO / "nwpp_hydro_cascade_links.csv")
    mon = pd.read_csv(HYDRO / "nwpp_hydro_cascade_monthly.csv")
    eta = mon.groupby("plant_id").eta_mwh_per_kcfsh.median()
    band = {
        int(r.d_plant_id): float(r.pond_kcfsh) * float(eta.get(int(r.d_plant_id), np.nan))
        for r in links.drop_duplicates("d_plant_id").itertuples()
    }
    return nid_b, {k: v for k, v in band.items() if np.isfinite(v)}


def coverage(y: int, nid_b: dict[int, float]) -> dict:
    """MW coverage of the NID pondage table on the year-y LP hydro fleet."""
    f = fleet_budget(y)
    m = [f"m{i:02d}" for i in range(1, 13)]
    rows = []
    for r in f.itertuples():
        pid, mw = int(r.plant_id), float(r.max_mw)
        maxm = max(getattr(r, c) for c in m)
        b = nid_b.get(pid)
        grp = ("cascade_row" if pid in CASCADE_ROW else
               "cascade_upstream_only" if pid in CASCADE_UP_ONLY else "off_cascade")
        if b is None:
            st = "UNSET"
        elif b >= maxm:
            st = "redundant"
        else:
            st = "binding_row"
        h = b / mw if (b is not None and mw > 0) else np.nan
        rows.append(dict(pid=pid, mw=mw, grp=grp, st=st, h=h))
    d = pd.DataFrame(rows)
    out = {"fleet_mw": round(d.mw.sum(), 1), "n": len(d)}
    for (g, s), x in d.groupby(["grp", "st"]):
        out[f"{g}:{s}"] = {"n": len(x), "mw": round(x.mw.sum(), 1)}
    live = d[(d.grp == "off_cascade") & (d.st == "binding_row")]
    out["off_cascade_binding_mw_by_hours"] = {
        lab: round(live[(live.h >= lo) & (live.h < hi)].mw.sum(), 1)
        for lab, lo, hi in (("<6h", 0, 6), ("6-24h", 6, 24), ("24-168h", 24, 168), (">=168h", 168, 1e12))
    }
    return out


def static_clip(y: int, bound: dict[int, float], eligible) -> dict:
    """Clip the pro-rata per-plant proxy of the keeper's hydro to ``bound``.

    Each eligible plant with a bound below its largest month is given the
    keeper's fleet hydro shape scaled to its budget share; where that shape's
    required storage exceeds B, its within-month deviation is shrunk by the
    largest factor k in [0, 1] that fits (bisection). Monthly energy is kept.
    """
    f = fleet_budget(y)
    m = [f"m{i:02d}" for i in range(1, 13)]
    moh = np.asarray(_hour_to_month_index(N), dtype=int)
    hpm = np.bincount(moh, minlength=12).astype(float)
    H = model_class(y, ("hydro",))
    Hm = np.bincount(moh, weights=H, minlength=12)
    E = f[m].to_numpy(float)
    share = E / np.where(E.sum(0) > 0, E.sum(0), 1.0)  # (n, 12) plant share of month
    delta = np.zeros(N)
    n_hit, mw_hit = 0, 0.0
    for i, r in enumerate(f.itertuples()):
        pid = int(r.plant_id)
        b = bound.get(pid)
        if b is None or not eligible(pid) or b >= E[i].max():
            continue
        p = share[i][moh] * H
        mean = (share[i] * Hm / hpm)[moh]
        inflow = (E[i] / hpm)[moh]
        if max_drawdown(inflow, p) <= b:
            continue
        lo, hi = 0.0, 1.0
        for _ in range(30):
            k = 0.5 * (lo + hi)
            lo, hi = (k, hi) if max_drawdown(inflow, mean + k * (p - mean)) <= b else (lo, k)
        delta += (mean + lo * (p - mean)) - p
        n_hit += 1
        mw_hit += float(r.max_mw)
    H2 = H + delta
    coal = model_class(y, COAL)
    a_coal = e930(y, "coal")
    _, hi0 = _split(H)
    _, hi1 = _split(H2)
    # Bracket for coal: (lo) coal absorbs none of the removed hydro swing;
    # (hi) coal absorbs all of it. Any real re-dispatch lies between.
    return {
        "n_plants_clipped": n_hit,
        "mw_clipped": round(mw_hit, 1),
        "hydro_intra_sd_keeper": round(hi0.std(), 1),
        "hydro_intra_sd_clipped": round(hi1.std(), 1),
        "hydro_daily_sd_keeper": round(_split(H)[0][::24].std(), 1),
        "hydro_daily_sd_clipped": round(_split(H2)[0][::24].std(), 1),
        "abs_delta_twh": round(np.abs(delta).sum() / 2e6, 3),
        "coal_r_keeper": round(_r(coal, a_coal), 3),
        "coal_r_intra_keeper": round(_r(_split(coal)[1], _split(a_coal)[1]), 3),
        "coal_r_if_coal_takes_all": round(_r(coal - delta, a_coal), 3),
        "coal_r_intra_if_coal_takes_all": round(_r(_split(coal - delta)[1], _split(a_coal)[1]), 3),
    }


def measured_admissibility(nid_b: dict[int, float], band_b: dict[int, float]) -> list[dict]:
    """Would each CROHMS project's MEASURED generation satisfy a flat-inflow pondage row?

    Inflow = the plant's own measured monthly-mean generation (the pondage
    row's construction). Reports the storage reality needed, in hours of the
    plant's mean output, and whether NID storage / the measured band covers it.
    Also the within-day part alone (inflow = measured daily mean).
    """
    c = pd.read_parquet(HYDRO / "crohms" / "nwpp_crohms_hourly.parquet")
    c = c[c.series.str.startswith("Power.Total")]
    ids = pd.read_csv(HYDRO / "nwpp_hydro_cascade_monthly.csv").drop_duplicates("station")
    pid_of = dict(zip(ids.station, ids.plant_id.astype(int)))
    out = []
    for st, g in c.groupby("station"):
        pid = pid_of.get(st)
        for y in YEARS:
            s = g[g.ts.dt.year == y].set_index("ts").value
            s = s.reindex(pd.date_range(f"{y}-01-01", periods=N, freq="h")).interpolate().bfill().ffill()
            p = s.to_numpy(float).clip(0)
            moh = np.asarray(_hour_to_month_index(N), dtype=int)
            hpm = np.bincount(moh, minlength=12).astype(float)
            inflow_m = (np.bincount(moh, weights=p, minlength=12) / hpm)[moh]
            dm, _ = _split(p)
            need_m = max_drawdown(inflow_m, p)
            need_d = max(max_drawdown(dm[i:i + 24], p[i:i + 24]) for i in range(0, N - 23, 24))
            mean = p.mean()
            out.append(dict(
                station=st, plant_id=pid, year=y, mean_mw=round(mean, 0),
                need_month_h=round(need_m / mean, 2), need_day_h=round(need_d / mean, 2),
                nid_h=round(nid_b.get(pid, np.nan) / mean, 2),
                band_h=round(band_b.get(pid, np.nan) / mean, 2),
            ))
    return out


def main() -> None:
    """Run every section and write the JSON the FINDING cites."""
    nid_b, band_b = storage_tables()
    chain = set(pd.read_csv(HYDRO / "nwpp_hydro_chain.csv").plant_id.astype(int))
    res: dict = {
        "coverage": {},
        "clip_nid_off_cascade": {},
        "clip_nid_off_chain": {},
        "clip_band_uncoupled_mainstem": {},
    }
    for y in YEARS:
        res["coverage"][y] = coverage(y, nid_b)
        # Option (a): NID storage on every plant that carries no cascade row.
        res["clip_nid_off_cascade"][y] = static_clip(y, nid_b, lambda p: p not in CASCADE_ROW)
        # Option (a2): NID storage only OFF the registered regulated chains
        # (nwpp_hydro_chain.csv, NWPP-36's reach table): a plant below a
        # regulating project has no flat within-month inflow.
        res["clip_nid_off_chain"][y] = static_clip(y, nid_b, lambda p: p not in chain)
        # Option (c) bracket: the measured operated band on the uncoupled mainstem only.
        res["clip_band_uncoupled_mainstem"][y] = static_clip(
            y, band_b, lambda p: p not in CASCADE_ROW
        )
    adm = measured_admissibility(nid_b, band_b)
    res["measured_admissibility"] = adm
    res["measured_hydro_intra_sd"] = {y: round(_split(e930(y, "hydro"))[1].std(), 1) for y in YEARS}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k != "measured_admissibility"}, indent=1, default=float))
    print(pd.DataFrame(adm).to_string(index=False))


if __name__ == "__main__":
    main()
