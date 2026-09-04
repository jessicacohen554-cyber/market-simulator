"""miso-210 phase 0 — THE MAX-GEN CLOCK REPAIR, zero-solve.

Pre-registered in ``results/calibration/PREREG-miso210-maxgen-clock-repair-
2026-09-04.md`` (pushed blind at ``83e73bf8``) BEFORE any window was re-placed.
Everything here is computed WITHOUT editing a repo file: the corrected clock is
applied by converting the curated registry to ``Etc/GMT+6`` in this process,
and the M-2 deriver is re-run with its two clock constants monkey-patched,
writing ONLY to the session scratchpad (never under ``data/raw``).

  P-1  the exact hour sets each armed consumer fires in today (EST placement)
       vs on the corrected clock (CST), per window: gained / lost hours, and
       the KEEPER's own load-weighted price, slack and idle thermal in them;
  P-2  the M-2 extract re-derived on the corrected clock: per-block row and
       derate-MW deltas; S-3 certificate invariance (guard 2's n_cert per
       registry row must be identical — the DA hub record moves WITH the
       registry);
  P-3  static reach in the corrected 2025 Warning+ hours (min idle thermal;
       demand minus capability) — miso-208's "tier floor silent in 2025"
       RE-SCORED on the corrected clock as a claim that may fail;
  S-2  placement liveness off the production functions: the tier-cost array
       and the M-2 derate hour set move by EXACTLY one hour;
  V-KEY-LMP  the corrected placement checked against the LMP file's own HE
       stamps (the miso-208 key re-established at r = 1.000).

Usage::

    PYTHONPATH=src python3 scripts/probes/_miso210_clock_phase0.py

Record: ``results/calibration/_miso210_clock_phase0.json``.
"""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import io
import json
import os
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
from market_sim.data import outages  # noqa: E402
from market_sim.data.maxgen_events import (  # noqa: E402
    TIER_FLOOR_BY_LEVEL,
    load_maxgen_registry_model_clock,
    tier_slack_cost_from_registry,
)
from market_sim.data.outages import outage_hour_mask  # noqa: E402
from scripts.data import derive_campd_maxgen_outages as drv  # noqa: E402
from scripts.lib import clean_io  # noqa: E402

if drv.MODEL_TZ != "Etc/GMT+5":  # pragma: no cover - record guard
    raise SystemExit(
        "this probe measured the PRE-repair deriver (MODEL_TZ = Etc/GMT+5, HEAD "
        "8f5cb32c) by monkey-patching the corrected clock in-process; at HEAD the "
        "repair has landed, so its 'armed' leg would already be corrected. The "
        "committed record _miso210_clock_phase0.json stands; do not re-run."
    )

KEEPER = m207.KEEPER
ZONAL = m207.ZONAL
OUT = REPO / "results/calibration/_miso210_clock_phase0.json"
SCRATCH = Path(
    os.environ.get(
        "MISO210_SCRATCH",
        "/tmp/claude-0/-home-user-market-simulator/"
        "ccb65b10-d751-5226-aeb3-8e4a91d68d0f/scratchpad",
    )
)
YEARS = (2023, 2024, 2025)
HOURS = 8760
HUB = m207.SCORING_HUB
CARRY = m207.CARRY_ZONES
COAL_POOL = m207.COAL_POOL
GAS = m207.GAS_CLASSES
ARMED_TZ = "Etc/GMT+5"  # what HEAD pins (EST) — the defect
MODEL_TZ = "Etc/GMT+6"  # the measured model clock (CST hour-beginning)
EST_TO_MODEL = -1  # miso-208 V-KEY-LMP winner
WARNING_PLUS = tuple(k for k, v in TIER_FLOOR_BY_LEVEL.items() if v is not None)
ZONES = [
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
    "MISO_external",
    "MISO_external_South",
]
HE = [f"he{i:02d}" for i in range(1, 25)]
COMMITTED = {
    "incumbent": RAW_DATA_DIR / "campd-unit-outages-maxgen-MISO.csv",
    "unitroute": RAW_DATA_DIR / "campd-unit-outages-maxgen-unitroute-MISO.csv",
}


# ----------------------------------------------------------------- helpers
def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _hoy_from_local(ts: pd.Series) -> np.ndarray:
    lens = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
    start = np.concatenate([[0], np.cumsum(lens)[:-1]])
    m = ts.dt.month.to_numpy() - 1
    d = ts.dt.day.to_numpy() - 1
    h = ts.dt.hour.to_numpy()
    out = (start[m] + d) * 24 + h
    out[(m == 1) & (d == 28)] = -1
    return out


def registry_on(tz: str) -> pd.DataFrame:
    """The curated registry with model-clock columns on clock ``tz``."""
    ev = clean_io.read_clean("maxgen-events", iso="MISO").copy()
    start = ev["start_utc"].dt.tz_convert(tz).dt.tz_localize(None)
    end = ev["end_utc"].dt.tz_convert(tz).dt.tz_localize(None)
    ev["start_model"] = start.dt.floor("h")
    ev["end_model_excl"] = end.dt.ceil("h")
    return ev


def hub_rt_he_on_model_clock(year: int) -> np.ndarray:
    """INDIANA.HUB RT LMP from the HE (EST) file placed at EST_TO_MODEL."""
    df = pd.read_csv(
        RAW_DATA_DIR / "lmp-data" / "MISO" / f"miso_hub_lmp_{year}_rt.csv.gz"
    )
    df = df[(df["node"] == HUB) & (df["value"] == "LMP")].copy()
    df["date"] = pd.to_datetime(df["date"])
    long = df.melt(id_vars=["date"], value_vars=HE, var_name="he", value_name="lmp")
    hoy = _hoy_from_local(long["date"]) + (
        long["he"].str.slice(2).astype(int).to_numpy() - 1
    )
    arr = np.full(HOURS, np.nan)
    j = hoy + EST_TO_MODEL
    ok = (hoy >= 0) & (j >= 0) & (j < HOURS)
    arr[j[ok]] = long["lmp"].to_numpy(float)[ok]
    return arr


def _mask_rows(ev: pd.DataFrame, year: int, warning_only: bool) -> list[dict]:
    rows = []
    for r in ev.itertuples(index=False):
        if warning_only and str(r.level) not in WARNING_PLUS:
            continue
        m = outage_hour_mask(r.start_model, r.end_model_excl, year, HOURS)
        if not m.any():
            continue
        rows.append(
            {
                "level": str(r.level),
                "region": str(r.region),
                "start": str(r.start_model),
                "end_excl": str(r.end_model_excl),
                "hours": np.flatnonzero(m),
            }
        )
    return rows


# ----------------------------------------------------------------- P-2 deriver
@contextlib.contextmanager
def corrected_deriver():
    """Monkey-patch the deriver's two clock constants; restore on exit.

    ``MODEL_TZ`` -> the CST model clock, and the DA hub HE record shifted by
    EST_TO_MODEL onto the same clock so guard 2 compares the same physical
    hours (the PREREG §2 repair, applied in-process only).
    """
    orig_tz, orig_hub = drv.MODEL_TZ, drv.load_da_hub_wide

    def _hub_model(iso: str, year: int) -> pd.DataFrame:
        wide = orig_hub(iso, year)
        wide.index = wide.index + pd.Timedelta(hours=EST_TO_MODEL)
        return wide

    drv.MODEL_TZ = MODEL_TZ
    drv.load_da_hub_wide = _hub_model
    try:
        yield
    finally:
        drv.MODEL_TZ, drv.load_da_hub_wide = orig_tz, orig_hub


def run_deriver(out: Path, mixed_gas_routing: bool) -> str:
    argv = ["derive", "--iso", "MISO", "--out", str(out)]
    if mixed_gas_routing:
        argv.append("--mixed-gas-routing")
    old = sys.argv
    sys.argv = argv
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            drv.main()
    finally:
        sys.argv = old
    return buf.getvalue()


def cert_table(tz: str) -> list[dict]:
    """Guard 2's n_cert per registry row on clock ``tz`` (hub record shifted alike)."""
    ev = registry_on(tz)
    shift = 0 if tz == ARMED_TZ else EST_TO_MODEL
    out = []
    hubs: dict[int, pd.DataFrame] = {}
    for r in ev.itertuples(index=False):
        y = int(r.start_model.year)
        if not drv.da_hub_path("MISO", y).exists():
            continue  # uncertifiable year (no DA hub record) -- the deriver drops it
        if y not in hubs:
            w = drv.load_da_hub_wide("MISO", y)
            w.index = w.index + pd.Timedelta(hours=shift)
            hubs[y] = w
        out.append(
            {
                "level": str(r.level),
                "region": str(r.region),
                "start": str(r.start_model),
                "n_cert": drv.certificate_hours(
                    hubs[y], str(r.region), r.start_model, r.end_model_excl
                ),
            }
        )
    return out


SOLVE_COLS = [
    "facility_id",
    "unit_id",
    "plant_group",
    "window_start",
    "window_end",
    "derate_mw",
]


def reproduction(committed: Path, fresh: Path) -> dict:
    """Compare two extracts on the solve-relevant columns (N-1)."""
    da, db = pd.read_csv(committed), pd.read_csv(fresh)
    ka = set(map(tuple, da[SOLVE_COLS].astype(str).to_numpy().tolist()))
    kb = set(map(tuple, db[SOLVE_COLS].astype(str).to_numpy().tolist()))
    return {
        "rows": {"committed": len(da), "fresh": len(db)},
        "solve_rows_identical": ka == kb,
        "only_in_committed": len(ka - kb),
        "only_in_fresh": len(kb - ka),
        "derate_mw_total": {
            "committed": round(float(da["derate_mw"].sum()), 1),
            "fresh": round(float(db["derate_mw"].sum()), 1),
        },
        "bytes_identical": _sha(committed) == _sha(fresh),
    }


def block_summary(path: Path) -> dict:
    df = pd.read_csv(path)
    g = df.groupby(["window_start", "window_end", "region", "levels"])["derate_mw"].agg(
        ["count", "sum"]
    )
    return {
        " | ".join(map(str, k)): {
            "rows": int(v["count"]),
            "derate_mw": round(float(v["sum"]), 1),
        }
        for k, v in g.iterrows()
    }


def m2_factor_hours(csv_path: Path, year: int) -> dict[tuple, np.ndarray]:
    """Production M-2 loader on an arbitrary extract path (cache cleared)."""
    orig = outages.unit_outage_maxgen_csv_for_iso
    outages.unit_outage_maxgen_csv_for_iso = lambda iso, mixed_gas_routing=False: (
        csv_path
    )
    outages.unit_outage_maxgen_derate_factors.cache_clear()
    try:
        fac = outages.unit_outage_maxgen_derate_factors(
            year, HOURS, iso="MISO", mixed_gas_routing=True
        )
    finally:
        outages.unit_outage_maxgen_csv_for_iso = orig
        outages.unit_outage_maxgen_derate_factors.cache_clear()
    return {k: np.asarray(v) for k, v in fac.items()}


# ----------------------------------------------------------------- main
def main() -> None:  # noqa: PLR0915
    SCRATCH.mkdir(parents=True, exist_ok=True)
    zon = pd.read_parquet(ZONAL)
    cfg0 = keeper_config()
    rep: dict = {
        "charter": "miso-210 phase 0 — the max-gen clock repair; zero-solve; nothing under data/raw touched.",
        "prereg": "results/calibration/PREREG-miso210-maxgen-clock-repair-2026-09-04.md @ 83e73bf8",
        "keeper": "2026-09-03-miso-202-unitclip",
        "clocks": {
            "armed_at_head": ARMED_TZ,
            "corrected": MODEL_TZ,
            "est_to_model": EST_TO_MODEL,
        },
    }
    ev_armed = registry_on(ARMED_TZ)
    ev_fixed = registry_on(MODEL_TZ)
    # Sanity: the loader at HEAD reproduces the ARMED frame exactly.
    ev_head = load_maxgen_registry_model_clock("MISO")
    rep["head_loader_is_est"] = bool(
        (ev_head["start_model"].to_numpy() == ev_armed["start_model"].to_numpy()).all()
        and (
            ev_head["end_model_excl"].to_numpy()
            == ev_armed["end_model_excl"].to_numpy()
        ).all()
    )

    # ================================================================ V-KEY-LMP
    vkey = {}
    for year in YEARS:
        rt_committed = m207.hub_series(zon, year, "rt")
        rt_he = hub_rt_he_on_model_clock(year)
        m = np.isfinite(rt_committed) & np.isfinite(rt_he)
        r = float(np.corrcoef(rt_committed[m], rt_he[m])[0, 1])
        maxdiff = float(np.nanmax(np.abs(rt_committed[m] - rt_he[m])))
        # also the naive (unshifted) placement, for the record
        rt_naive = np.roll(rt_he, -EST_TO_MODEL)
        m2 = np.isfinite(rt_committed) & np.isfinite(rt_naive)
        r0 = float(np.corrcoef(rt_committed[m2], rt_naive[m2])[0, 1])
        vkey[year] = {
            "r_at_est_to_model_minus1": round(r, 6),
            "max_abs_diff_at_minus1": round(maxdiff, 4),
            "r_at_zero_shift": round(r0, 6),
            "key_reproduces": bool(r > 0.9999 and maxdiff < 0.01),
        }
    rep["v_key_lmp"] = vkey
    # Corrected windows == model hours whose EST HE label lies in the declared window:
    # by construction hoy_model = hoy_est - 1, i.e. the registry converted to CST.
    rep["v_key_lmp_note"] = (
        "A declared EST window [s, e) covers EST hour-beginning indices s..e-1; the "
        "model hour carrying EST label j is j + EST_TO_MODEL = j - 1 (r = 1.000 key "
        "above), so the corrected model-hour set is [s-1, e-1) — exactly the registry "
        "converted to Etc/GMT+6."
    )

    # ================================================================ P-1 / P-3 / S-2
    years: dict = {}
    for year in YEARS:
        y: dict = {}
        price_df, demand = keeper_prices(year)
        price_df = price_df.reindex(range(HOURS))
        sysd = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        num = sysd.assign(pw=sysd["price"] * sysd["demand"]).groupby("hour")["pw"].sum()
        den = sysd.groupby("hour")["demand"].sum()
        price_lw = (num / den).reindex(range(HOURS)).to_numpy()
        slack_z = (
            sysd.pivot_table(index="hour", columns="zone", values="slack")
            .reindex(range(HOURS))
            .fillna(0.0)
        )
        slack = slack_z.sum(axis=1).to_numpy()
        ch = m207.keeper_class_hourly(year)
        rt = m207.hub_series(zon, year, "rt")

        cfg = dataclasses.replace(cfg0, weather_year=year, mode="backcast")
        _raw, fleet, arrays, _fp, _mc, _zn = build_year(cfg, year)
        labels = np.array([m207.class_label(g) for g in fleet], dtype=object)
        avail = np.asarray(arrays.availability, dtype=np.float64)
        if avail.ndim == 1:
            avail = np.broadcast_to(avail[:, None], (len(fleet), HOURS))
        pmax = np.asarray(arrays.pmax, dtype=np.float64)
        avail_mw = pmax[:, None] * avail
        thermal_sel = np.isin(labels, list(GAS) + [COAL_POOL])
        thermal_cap = avail_mw[thermal_sel].sum(axis=0)
        thermal_disp = sum(
            ch.loc[c].to_numpy() for c in ch.index if c in GAS or c == COAL_POOL
        )
        idle_thermal = thermal_cap - thermal_disp
        # whole-fleet capability (thermal + non-thermal dispatchable + renewables at CF)
        cap_all = avail_mw.sum(axis=0)

        def hour_block(hs: np.ndarray) -> dict:
            hs = np.asarray(hs, int)
            return {
                "n": int(hs.size),
                "stamps": [m207._stamp(year, int(h)) for h in hs[:4]]
                + (["..."] if hs.size > 4 else []),
                "keeper_price_lw_mean": round(float(np.nanmean(price_lw[hs])), 3),
                "keeper_price_lw_max": round(float(np.nanmax(price_lw[hs])), 3),
                "actual_rt_hub_mean": round(float(np.nanmean(rt[hs])), 3),
                "slack_mwh": round(float(slack[hs].sum()), 2),
                "idle_thermal_gw_min": round(float(idle_thermal[hs].min()) / 1e3, 3),
                "idle_thermal_gw_mean": round(float(idle_thermal[hs].mean()) / 1e3, 3),
                "demand_minus_capability_gw_max": round(
                    float((demand[hs] - cap_all[hs]).max()) / 1e3, 3
                ),
            }

        # ---- P-1: per registry row, armed vs corrected hour sets
        p1 = []
        for ra, rf in zip(
            _mask_rows(ev_armed, year, False), _mask_rows(ev_fixed, year, False)
        ):
            assert ra["level"] == rf["level"] and ra["region"] == rf["region"]
            ha, hf = set(ra["hours"].tolist()), set(rf["hours"].tolist())
            gained, lost = sorted(hf - ha), sorted(ha - hf)
            entry = {
                "level": ra["level"],
                "region": ra["region"],
                "tier_priced": ra["level"] in WARNING_PLUS,
                "armed_est": {
                    "start": ra["start"],
                    "end_excl": ra["end_excl"],
                    "n": len(ha),
                },
                "corrected_cst": {
                    "start": rf["start"],
                    "end_excl": rf["end_excl"],
                    "n": len(hf),
                },
                "gained": hour_block(np.array(gained)) if gained else None,
                "lost": hour_block(np.array(lost)) if lost else None,
                "exact_one_hour_shift": bool(
                    hf == {h - 1 for h in ha}
                    or (min(ha) == 0 and hf == {h - 1 for h in ha if h > 0})
                ),
                "armed_window": hour_block(np.array(sorted(ha))),
                "corrected_window": hour_block(np.array(sorted(hf))),
            }
            p1.append(entry)
        y["p1_windows"] = p1
        # 2024 P-1b: slack by hour inside the armed and corrected Warning+ windows
        if year == 2024:
            wa = [r for r in _mask_rows(ev_armed, year, True)]
            wf = [r for r in _mask_rows(ev_fixed, year, True)]
            hs_a = sorted({h for r in wa for h in r["hours"].tolist()})
            hs_f = sorted({h for r in wf for h in r["hours"].tolist()})
            y["p1b_2024_slack_by_hour"] = {
                "armed": {
                    m207._stamp(year, h): round(float(slack[h]), 1) for h in hs_a
                },
                "corrected": {
                    m207._stamp(year, h): round(float(slack[h]), 1) for h in hs_f
                },
                "lost_hour_share_of_window_slack": (
                    round(float(slack[max(hs_a)] / max(slack[hs_a].sum(), 1e-9)), 4)
                ),
                "window_slack_total_mwh": round(float(slack[hs_a].sum()), 1),
                "keeper_price_lw_at_gained_hour": round(float(price_lw[min(hs_f)]), 2),
                "keeper_price_lw_by_hour_armed": {
                    m207._stamp(year, h): round(float(price_lw[h]), 1) for h in hs_a
                },
            }

        # ---- P-3: the corrected Warning+ hours, static reach
        warn_f = sorted(
            {h for r in _mask_rows(ev_fixed, year, True) for h in r["hours"].tolist()}
        )
        warn_a = sorted(
            {h for r in _mask_rows(ev_armed, year, True) for h in r["hours"].tolist()}
        )
        y["p3_static_reach"] = {
            "warning_plus_hours_corrected": hour_block(np.array(warn_f))
            if warn_f
            else None,
            "warning_plus_hours_armed": hour_block(np.array(warn_a))
            if warn_a
            else None,
            "tier_floor_reachable_corrected": (
                bool((demand[warn_f] - cap_all[warn_f]).max() > 0) if warn_f else None
            ),
            "tier_floor_printed_in_keeper_armed": (
                bool(slack[warn_a].sum() > 0) if warn_a else None
            ),
        }

        # ---- S-2a: tier-cost placement off the production function
        voll = float(cfg0.voll)
        cost_a = tier_slack_cost_from_registry(
            ev_armed, "MISO", year, ZONES, voll, HOURS
        )
        cost_f = tier_slack_cost_from_registry(
            ev_fixed, "MISO", year, ZONES, voll, HOURS
        )
        if cost_a is None and cost_f is None:
            y["s2_tier"] = {"no_warning_plus_window": True, "exact_shift": True}
        else:
            cost_a = (
                cost_a if cost_a is not None else np.full((len(ZONES), HOURS), voll)
            )
            cost_f = (
                cost_f if cost_f is not None else np.full((len(ZONES), HOURS), voll)
            )
            shifted = np.full_like(cost_a, voll)
            shifted[:, :-1] = cost_a[:, 1:]  # armed hour h -> corrected hour h-1
            diff_cells = int((cost_a != cost_f).sum())
            y["s2_tier"] = {
                "cells_differing": diff_cells,
                "cells_priced_below_voll_armed": int((cost_a < voll).sum()),
                "cells_priced_below_voll_corrected": int((cost_f < voll).sum()),
                "exact_shift": bool(np.array_equal(shifted, cost_f)),
                "external_buses_untouched": bool(
                    (cost_f[6:] == voll).all() and (cost_a[6:] == voll).all()
                ),
            }
        years[year] = y
    rep["years"] = years

    # ================================================================ P-2 / S-3
    rep["S3_certificate_invariance"] = {}
    ca, cf = cert_table(ARMED_TZ), cert_table(MODEL_TZ)
    ident = all(a["n_cert"] == f["n_cert"] for a, f in zip(ca, cf))
    qa = [a for a in ca if a["n_cert"] >= drv.MIN_CERTIFICATE_HOURS]
    qf = [f for f in cf if f["n_cert"] >= drv.MIN_CERTIFICATE_HOURS]
    rep["S3_certificate_invariance"] = {
        "n_cert_identical": ident,
        "rows": [
            {**a, "n_cert_corrected": f["n_cert"], "start_corrected": f["start"]}
            for a, f in zip(ca, cf)
        ],
        "qualifying_windows": {"armed": len(qa), "corrected": len(qf)},
        "blocks_identical": len(qa) == len(qf),
        "detail": "guard 2 n_cert per registry row, DA hub record shifted with the registry",
        "passed": bool(ident and len(qa) == len(qf)),
    }

    p2: dict = {"scratchpad": str(SCRATCH), "variants": {}}
    for name, mgr in (("incumbent", False), ("unitroute", True)):
        stem = f"campd-unit-outages-maxgen{'-unitroute' if mgr else ''}-MISO"
        committed = COMMITTED[name]
        # N-1: the forward deriver at the ARMED clock vs the committed extract, on
        # the solve-relevant columns (the loader reads facility_id, plant_group,
        # derate_mw, window_start, window_end; plant_capacity_mw is informational
        # and may drift with the fleet). Without this the corrected re-derive
        # could carry detector/fleet drift and call it the clock.
        out_armed = SCRATCH / f"{stem}.armed-clock.csv"
        log_armed = run_deriver(out_armed, mgr)
        (SCRATCH / f"derive_{name}_armed.log").write_text(log_armed)
        n1 = reproduction(committed, out_armed)
        out = SCRATCH / f"{stem}.corrected.csv"
        with corrected_deriver():
            log = run_deriver(out, mgr)
        (SCRATCH / f"derive_{name}.log").write_text(log)
        bc, bf = block_summary(committed), block_summary(out)
        blocks = {}
        for (ka, va), (kf, vf) in zip(bc.items(), bf.items()):
            blocks[ka] = {
                "corrected_key": kf,
                "rows_committed": va["rows"],
                "rows_corrected": vf["rows"],
                "rows_delta_pct": round(
                    100.0 * (vf["rows"] - va["rows"]) / va["rows"], 2
                ),
                "mw_committed": va["derate_mw"],
                "mw_corrected": vf["derate_mw"],
                "mw_delta_pct": round(
                    100.0 * (vf["derate_mw"] - va["derate_mw"]) / va["derate_mw"], 2
                ),
            }
        tot_c = sum(v["derate_mw"] for v in bc.values())
        tot_f = sum(v["derate_mw"] for v in bf.values())
        p2["variants"][name] = {
            "committed": str(committed.relative_to(REPO)),
            "n1_forward_deriver_at_armed_clock_reproduces_committed": n1,
            "corrected_scratch": str(out),
            "n_blocks": {"committed": len(bc), "corrected": len(bf)},
            "blocks": blocks,
            "total_mw": {"committed": round(tot_c, 1), "corrected": round(tot_f, 1)},
            "total_rows": {
                "committed": sum(v["rows"] for v in bc.values()),
                "corrected": sum(v["rows"] for v in bf.values()),
            },
            "f3_lines": [ln for ln in log.splitlines() if ln.startswith("F3")],
            "cert_lines": [ln.strip() for ln in log.splitlines() if "hours>$" in ln],
            "sha256": {"committed": _sha(committed), "corrected": _sha(out)},
        }
    rep["P2_rederive"] = p2
    rep["extract_sha256"] = {
        "control_committed_at_open": _sha(COMMITTED["unitroute"]),
        "arm_rederived": p2["variants"]["unitroute"]["sha256"]["corrected"],
    }

    # ---- S-2b: M-2 derate hour set moves by exactly one hour (union over bins)
    s2m2 = {}
    fixed_csv = Path(p2["variants"]["unitroute"]["corrected_scratch"])
    for year in YEARS:
        fa = m2_factor_hours(COMMITTED["unitroute"], year)
        ff = m2_factor_hours(fixed_csv, year)
        ua = np.zeros(HOURS, bool)
        uf = np.zeros(HOURS, bool)
        for v in fa.values():
            ua |= v < 1.0
        for v in ff.values():
            uf |= v < 1.0
        shifted = np.zeros(HOURS, bool)
        shifted[:-1] = ua[1:]
        per_bin_exact = 0
        for k in set(fa) & set(ff):
            sa = np.zeros(HOURS, bool)
            sa[:-1] = (fa[k] < 1.0)[1:]
            per_bin_exact += int(np.array_equal(sa, ff[k] < 1.0))
        s2m2[year] = {
            "bins": {
                "committed": len(fa),
                "corrected": len(ff),
                "common": len(set(fa) & set(ff)),
            },
            "union_hours": {"committed": int(ua.sum()), "corrected": int(uf.sum())},
            "union_exact_shift": bool(np.array_equal(shifted, uf)),
            "per_bin_exact_shift": per_bin_exact,
            "mean_removed_gw_in_window_committed": round(
                float(np.mean([(1 - fa[k][ua]).mean() for k in fa]) if fa else 0.0), 4
            ),
        }
    rep["S2_placement"] = {
        "tier_exact_shift": {y: years[y]["s2_tier"]["exact_shift"] for y in YEARS},
        "m2_exact_shift": {y: s2m2[y]["union_exact_shift"] for y in YEARS},
        "m2_detail": s2m2,
        "detail": "tier cost off tier_slack_cost_from_registry; M-2 off unit_outage_maxgen_derate_factors on the committed vs re-derived extract",
        "passed": bool(
            all(years[y]["s2_tier"]["exact_shift"] for y in YEARS)
            and all(s2m2[y]["union_exact_shift"] for y in YEARS)
        ),
    }

    OUT.write_text(json.dumps(rep, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)}")
    print("head loader is EST:", rep["head_loader_is_est"])
    print("V-KEY-LMP:", json.dumps(vkey))
    print(
        "S-3:",
        rep["S3_certificate_invariance"]["passed"],
        rep["S3_certificate_invariance"]["qualifying_windows"],
    )
    print(
        "S-2:",
        rep["S2_placement"]["tier_exact_shift"],
        rep["S2_placement"]["m2_exact_shift"],
    )
    for y in YEARS:
        print(y, "P-3:", json.dumps(years[y]["p3_static_reach"], default=str)[:600])
    for name, v in p2["variants"].items():
        print(name, json.dumps(v["blocks"], indent=0)[:1500])


if __name__ == "__main__":
    main()
