#!/usr/bin/env python3
"""nyiso-109 D-STACK — WHAT sets the model's light-load (trough) price in NYISO,
and is the 2023 C3a breach a 2023-specific defect or an all-years one?

The nyiso-108 handoff named the successor as "the NYISO 2023 fossil over-pricing"
and pointed at a **2023-specific** offer-stack / fuel-basis skew. This probe tests
that framing on NYISO's own committed data before any arm is designed, because a
lever aimed at the wrong window is worse than no lever (rule 1 ``[R-STRUCT]``).

**No LP is solved.** Every measurement runs on the committed keeper bundle — its
``hourly/`` sidecars for duals / class MW / demand, its ``meta.json`` replayed
through ``replay_keeper.build_kwargs`` -> ``run_year(fleet_only=True)`` for the
offer arrays (fleet built, LP never constructed), the committed clean
``lmp/NYISO/RTM`` hourly actual, the committed bench payload for the scored
benchmark, and ``data/raw/NYISO/interface-flows/`` for the measured internal
interface flows and their posted limits.

Measurements
------------
* **A — residual by ACTUAL-price decile and by LOAD decile**, per year, on the
  hours whose hourly RT actual is committed in this checkout. Answers: is the
  2023 residual a level error spread over all hours, or concentrated?
* **B — zonal separation**, model vs actual, across each of the four model links.
  Answers whether the missing congestion gradient owns the residual.
* **C — the measured Central-East interface**: how often the REAL interface sits
  at its own posted limit, and how the model's monthly TTC envelope compares to
  the measured monthly mean limit. This is what decides whether
  ``measured_interface_limits`` is even a candidate lever for NYISO (rule 25 —
  NYISO's own measurement, never PJM's or ERCOT's verdict).
* **D — the marginal-tranche census** (the pjm-141 §1 test, re-derived on NYISO):
  a unit is marginal when its own hourly offer equals its own zone's dual to
  within ``EPS``. Reported by ``(class, tranche)`` at the trough window with the
  evening peak as a control, so the trough readout is never judged alone.
* **E — offer-stack depth** below NYISO's own measured trough p05, against the
  thermal MW the model actually has to serve in those hours.
* **F — within-day offer variation**: does ANY thermal row's offer move between
  the trough hour and the peak hour of the same calendar day?
* **G — diurnal amplitude**: what fraction of the measured trough->peak price
  swing the model reproduces, per year.

Usage
-----
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_nyiso109_trough_offer_stack.py \
        --bundle results/calibration/nyiso108_hydrorepair_B \
        --out results/calibration/_nyiso109_trough_offer_stack.json

Rebuilds one fleet per year for measurements D-F; years run sequentially and each
year's arrays are released before the next. Pass ``--no-fleet`` to run A-C and G
only (seconds, no fleet build).
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

YEARS = (2023, 2024, 2025)
HOURS = 8760

#: The trough window. h01-h05 local, the hours the nyiso-109 D1 decomposition
#: showed carrying the residual; h17-h19 is the evening-peak CONTROL.
TROUGH = (1, 2, 3, 4, 5)
PEAK = (17, 18, 19)

#: The model's five internal load zones (the external star node is excluded).
MODEL_ZONES = (
    "Upstate_West",
    "Capital_Hudson",
    "Lower_Hudson",
    "NYC",
    "Long_Island",
)
EXTERNAL_ZONE = "NYISO_external"

#: NYISO internal LBMP zones folded into each model zone. Mirrors
#: ``scripts/data/derive_actual_lmp.NYISO_ZONE_MAP``.
ZONE_MAP: dict[str, list[str]] = {
    "Upstate_West": ["WEST", "GENESE", "CENTRL", "NORTH", "MHK VL"],
    "Capital_Hudson": ["CAPITL"],
    "Lower_Hudson": ["HUD VL", "MILLWD", "DUNWOD"],
    "NYC": ["N.Y.C."],
    "Long_Island": ["LONGIL"],
}

#: The four model transfer links, in north-to-south order.
LINKS = (
    ("Upstate_West", "Capital_Hudson"),
    ("Capital_Hudson", "Lower_Hudson"),
    ("Lower_Hudson", "NYC"),
    ("NYC", "Long_Island"),
)

#: Measured NYISO internal transfer interfaces (MIS P-32) whose flows and posted
#: limits are committed under ``data/raw/NYISO/interface-flows/``.
INTERFACES = ("CENTRAL EAST - VC", "TOTAL EAST", "UPNY CONED", "SPR/DUN-SOUTH")

#: Tranche families, in merit order within a plant (``bins_to_fleet`` writes the
#: suffix onto ``unit_id``). Matched longest-first so ``committed01`` never
#: resolves through ``committed``'s prefix twice.
TRANCHE_FAMILIES = ("mustrun", "sync", "committed", "econ", "peak")

#: Marginal-set tolerance, $/MWh. The pjm-122 / pjm-138 §4.1 value, reused so the
#: census is comparable across ISOs; the census reports its own detection rate so
#: a mis-set tolerance is visible rather than silent.
EPS = 1.0


class _FleetCaptured(Exception):
    """Control-flow signal: the fleet arrays are built, unwind before the LP."""


# ── committed-artifact loaders ──────────────────────────────────────────────


def _actual_zonal(year: int) -> pd.DataFrame | None:
    """Model-zone hourly RT LBMP from the committed clean ``lmp`` datatype.

    Coverage is partial for every year in this checkout (the NYISO zonal RT zips
    are staged out of the repo); the caller reports the covered months so no
    statistic is quoted as full-year.
    """
    path = REPO / "data" / "clean" / "lmp" / "NYISO" / "RTM" / f"lmp_{year}.parquet"
    if not path.exists():
        return None
    raw = pd.read_parquet(path)
    raw = raw.assign(ts=pd.to_datetime(raw["interval_start_local"]))
    wide = raw.pivot_table(
        index="ts", columns="node", values="lmp_usd_per_mwh", aggfunc="mean"
    )
    cols = {
        z: [n for n in members if n in wide.columns]
        for z, members in ZONE_MAP.items()
    }
    if any(not v for v in cols.values()):
        return None
    return pd.DataFrame({z: wide[v].mean(axis=1) for z, v in cols.items()})


def _model_zonal(bundle: Path, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keeper P1 duals and zonal demand, indexed on the model's local hour."""
    sysf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sysf = sysf[sysf["zone"].isin(MODEL_ZONES)]
    if "pass" in sysf.columns and "P1" in set(sysf["pass"]):
        sysf = sysf[sysf["pass"] == "P1"]
    stamps = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
    sysf = sysf.assign(ts=stamps[sysf["hour"].to_numpy()])
    price = sysf.pivot_table(index="ts", columns="zone", values="price", aggfunc="mean")
    dem = sysf.pivot_table(index="ts", columns="zone", values="demand", aggfunc="mean")
    return price[list(MODEL_ZONES)], dem[list(MODEL_ZONES)]


def _lw(values: np.ndarray, weights: np.ndarray) -> float:
    """Load-weighted mean, the rubric-v2.4 ``rt_lw`` basis."""
    return float(np.average(values, weights=weights))


# ── A: where the residual lives ─────────────────────────────────────────────


def _residual_deciles(bundle: Path, year: int) -> dict | None:
    """Model-minus-actual system price by ACTUAL-price decile and LOAD decile."""
    act = _actual_zonal(year)
    if act is None:
        return None
    price, dem = _model_zonal(bundle, year)
    idx = price.index.intersection(act.index)
    if idx.empty:
        return None
    price, act, dem = price.loc[idx], act.loc[idx], dem.loc[idx]
    w = dem.to_numpy(float)
    model = np.average(price.to_numpy(float), weights=w, axis=1)
    actual = np.average(act[list(MODEL_ZONES)].to_numpy(float), weights=w, axis=1)
    load = w.sum(axis=1)

    def _by(order_key: np.ndarray) -> list[dict]:
        order = np.argsort(order_key)
        out = []
        for d in range(10):
            k = order[int(d * len(order) / 10) : int((d + 1) * len(order) / 10)]
            out.append(
                {
                    "decile": d + 1,
                    "load_gw": round(float(load[k].mean()) / 1000.0, 3),
                    "model": round(float(model[k].mean()), 3),
                    "actual": round(float(actual[k].mean()), 3),
                    "diff": round(float(model[k].mean() - actual[k].mean()), 3),
                    "model_std": round(float(model[k].std()), 3),
                    "actual_std": round(float(actual[k].std()), 3),
                }
            )
        return out

    pct = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    return {
        "covered_hours": int(len(idx)),
        "covered_months": sorted({int(m) for m in idx.month}),
        "model_mean": round(_lw(price.to_numpy(float), w), 3),
        "actual_mean": round(_lw(act[list(MODEL_ZONES)].to_numpy(float), w), 3),
        "percentiles": {
            f"p{p}": {
                "model": round(float(np.percentile(model, p)), 3),
                "actual": round(float(np.percentile(actual, p)), 3),
            }
            for p in pct
        },
        "by_actual_price_decile": _by(actual),
        "by_load_decile": _by(load),
    }


# ── B: zonal separation ─────────────────────────────────────────────────────


def _zonal_separation(bundle: Path, year: int) -> dict | None:
    """Per-link price separation, model vs actual, on the covered hours."""
    act = _actual_zonal(year)
    if act is None:
        return None
    price, _dem = _model_zonal(bundle, year)
    idx = price.index.intersection(act.index)
    price, act = price.loc[idx], act.loc[idx]
    rows = []
    for lo, hi in LINKS:
        dm, da = price[hi] - price[lo], act[hi] - act[lo]
        rows.append(
            {
                "link": f"{lo}->{hi}",
                "model_mean_spread": round(float(dm.mean()), 3),
                "actual_mean_spread": round(float(da.mean()), 3),
                "model_share_sep_gt_1": round(float((dm.abs() > 1.0).mean()), 4),
                "actual_share_sep_gt_1": round(float((da.abs() > 1.0).mean()), 4),
            }
        )
    return {
        "covered_hours": int(len(idx)),
        "links": rows,
        "zone_means": {
            z: {
                "model": round(float(price[z].mean()), 3),
                "actual": round(float(act[z].mean()), 3),
            }
            for z in MODEL_ZONES
        },
    }


# ── C: the measured interface, and whether the TTC is the defect ────────────


def _interface_reality(year: int) -> dict | None:
    """Measured NYISO internal interface flows vs their OWN posted limits.

    Decides whether an interface-limit lever is even a candidate: if the real
    interface is at its posted limit in a negligible share of hours, its limit is
    not what produces the observed zonal separation, and tightening the model's
    TTC would be a fitted constraint rather than a measured one (rules 5 / 14).
    """
    path = (
        REPO
        / "data"
        / "raw"
        / "NYISO"
        / "interface-flows"
        / f"NYISO_interface_flows_hourly_{year}.csv.gz"
    )
    if not path.exists():
        return None
    from market_sim.config.constants import NYISO_INTERFACE_TTC_BY_MONTH

    raw = pd.read_csv(path)
    raw = raw.assign(ts=pd.to_datetime(raw["interval_start_local"]))
    out: dict = {"interfaces": []}
    for iface in INTERFACES:
        sub = raw[raw["interface"] == iface]
        if sub.empty:
            continue
        # +-9999 is the posting's "unbounded" sentinel (see the intake README).
        lim = sub["positive_limit_mw"].replace({9999.0: np.nan, -9999.0: np.nan})
        flow = sub["flow_mw"]
        out["interfaces"].append(
            {
                "interface": iface,
                "flow_mean": round(float(flow.mean()), 1),
                "flow_p95": round(float(flow.quantile(0.95)), 1),
                "flow_max": round(float(flow.max()), 1),
                "limit_mean": round(float(lim.mean()), 1),
                "limit_p05": round(float(lim.quantile(0.05)), 1),
                "share_within_50mw_of_limit": round(
                    float((flow >= lim - 50.0).mean()), 4
                ),
            }
        )
    ce = raw[raw["interface"] == "CENTRAL EAST - VC"].assign(
        mon=lambda d: d["ts"].dt.month
    )
    model_ttc = NYISO_INTERFACE_TTC_BY_MONTH.get(year, {}).get(LINKS[0])
    out["central_east_monthly"] = {
        "measured_mean_flow": [
            round(float(v), 1) for v in ce.groupby("mon")["flow_mw"].mean()
        ],
        "measured_mean_limit": [
            round(float(v), 1) for v in ce.groupby("mon")["positive_limit_mw"].mean()
        ],
        "model_ttc": [float(v) for v in (model_ttc or [])],
    }
    return out


# ── fleet reconstruction (D / E / F) ────────────────────────────────────────


def _keeper_fleet(bundle: Path, year: int) -> dict:
    """Rebuild the EXACT fleet/offer arrays the keeper solved against — no LP.

    Replays ``meta.json`` through ``replay_keeper``'s mapping into
    ``solve_and_persist`` with ``run_year`` intercepted: the interceptor forces
    ``fleet_only=True`` (which returns the built arrays instead of constructing
    the LP), stashes the state and unwinds. Verbatim reuse of
    ``_pjm138_marginal_ownership._keeper_fleet`` so the offers censused are the
    offers the keeper solved on, never a re-derivation that could drift.
    """
    spec = importlib.util.spec_from_file_location(
        "_replay_keeper", REPO / "scripts" / "replay_keeper.py"
    )
    rk = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(rk)

    from scripts import run_calibration
    from scripts import run_calibration_full as rcf

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", HOURS))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = bundle

    captured: dict = {}
    real_run_year = run_calibration.run_year

    def _intercept(*args, **kw):
        kw["fleet_only"] = True
        captured["state"] = real_run_year(*args, **kw)
        raise _FleetCaptured

    run_calibration.run_year = _intercept
    rcf.run_year = _intercept
    try:
        rcf.solve_and_persist(**kwargs)
    except _FleetCaptured:
        pass
    finally:
        run_calibration.run_year = real_run_year
        rcf.run_year = real_run_year

    if "state" not in captured:
        raise SystemExit("fleet reconstruction did not reach run_year")
    return captured["state"]


def _tranche_of(unit_id: str) -> str:
    """Tranche family from an LP ``unit_id`` suffix, longest-prefix-first."""
    suffix = str(unit_id).rsplit("_", 1)[-1]
    for family in sorted(TRANCHE_FAMILIES, key=len, reverse=True):
        if suffix.startswith(family):
            return family
    return "_unbinned"


def _fleet_census(bundle: Path, year: int) -> dict:
    """D / E / F: marginal tranche, stack depth, within-day offer variation."""
    state = _keeper_fleet(bundle, year)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], HOURS, axis=1)
    avail = np.asarray(fa.pmax, dtype=float)[:, None] * np.asarray(
        fa.availability, dtype=float
    )
    if avail.ndim == 1:
        avail = np.repeat(avail[:, None], HOURS, axis=1)
    groups = np.array(
        [str(g) if g else "?" for g in np.asarray(fa.plant_group, dtype=object)],
        dtype=object,
    )
    unit_ids = np.asarray(fa.unit_ids, dtype=object)
    tranches = np.array([_tranche_of(u) for u in unit_ids], dtype=object)
    zone_idx = np.asarray(fa.zone_idx, dtype=int)
    heat_rate = np.asarray(fa.heat_rate, dtype=float)
    vom = np.asarray(fa.vom, dtype=float)
    fuel_px = np.asarray(state.get("fuel_prices"), dtype=float)
    if fuel_px.ndim == 1:
        fuel_px = np.repeat(fuel_px[:, None], HOURS, axis=1)

    price, dem = _model_zonal(bundle, year)
    duals = price.to_numpy(float).T  # (n_zones, T) in MODEL_ZONES order
    n_zones = duals.shape[0]
    # Rows homed on the external star node index past the internal zone list are
    # excluded from the census — they carry no internal dual to compare against.
    internal = zone_idx < n_zones
    row_dual = np.full(mc.shape, np.nan)
    row_dual[internal] = duals[zone_idx[internal]]

    hod = np.asarray(price.index.hour)
    day = np.asarray(price.index.dayofyear)
    trough_h = np.isin(hod, TROUGH)
    peak_h = np.isin(hod, PEAK)

    def _census(window: np.ndarray) -> dict:
        live = internal[:, None] & window[None, :] & (avail > 0.0)
        marginal = live & (np.abs(mc - row_dual) <= EPS)
        # T5 analogue: decompose the MARGINAL rung's own offer into the inputs a
        # successor lever would have to move — physical burn (heat rate x
        # delivered fuel), VOM, and the residual markup the offer band adds on
        # top. Capacity-weighted over the marginal unit-hours in this window.
        wgt = np.where(marginal, avail, 0.0)
        tot = float(wgt.sum())
        decomp = None
        if tot > 0:
            burn = heat_rate[:, None] * fuel_px
            decomp = {
                "cap_weighted_offer": round(float((mc * wgt).sum() / tot), 4),
                "cap_weighted_burn": round(float((burn * wgt).sum() / tot), 4),
                "cap_weighted_vom": round(
                    float((np.broadcast_to(vom[:, None], mc.shape) * wgt).sum() / tot), 4
                ),
                "cap_weighted_residual_markup": round(
                    float(((mc - burn - vom[:, None]) * wgt).sum() / tot), 4
                ),
                "cap_weighted_heat_rate": round(
                    float((np.broadcast_to(heat_rate[:, None], mc.shape) * wgt).sum() / tot),
                    4,
                ),
                "cap_weighted_fuel_price": round(float((fuel_px * wgt).sum() / tot), 4),
            }
        by_tranche: dict[str, int] = {}
        by_pair: dict[str, int] = {}
        for fam in list(TRANCHE_FAMILIES) + ["_unbinned"]:
            sel = tranches == fam
            by_tranche[fam] = int(marginal[sel].sum())
        for g in sorted(set(groups)):
            for fam in list(TRANCHE_FAMILIES) + ["_unbinned"]:
                sel = (groups == g) & (tranches == fam)
                n = int(marginal[sel].sum())
                if n:
                    by_pair[f"{g}:{fam}"] = n
        total = sum(by_tranche.values())
        detected = int((marginal.any(axis=0) & window).sum())
        return {
            "marginal_count_share_by_tranche": {
                k: round(v / total, 4) for k, v in by_tranche.items() if total
            },
            "top_pairs": dict(
                sorted(by_pair.items(), key=lambda kv: -kv[1])[:8]
            ),
            "top_pair_shares": {
                k: round(v / total, 4)
                for k, v in sorted(by_pair.items(), key=lambda kv: -kv[1])[:8]
            }
            if total
            else {},
            "detection_rate": round(detected / max(int(window.sum()), 1), 4),
            "marginal_offer_decomposition": decomp,
        }

    # E — depth of the offer stack below the measured trough p05.
    act = _actual_zonal(year)
    target = None
    if act is not None:
        idx = price.index.intersection(act.index)
        if not idx.empty:
            w = dem.loc[idx].to_numpy(float)
            a_sys = np.average(act.loc[idx][list(MODEL_ZONES)].to_numpy(float),
                               weights=w, axis=1)
            night = np.isin(np.asarray(idx.hour), TROUGH)
            if night.any():
                target = float(np.percentile(a_sys[night], 5))
    depth = None
    if target is not None:
        cheap = np.where(
            internal[:, None] & trough_h[None, :] & (mc <= target), avail, 0.0
        )
        depth = {
            "measured_trough_p05_target": round(target, 3),
            "mean_gw_offered_below_target": round(
                float(cheap[:, trough_h].sum(axis=0).mean()) / 1000.0, 4
            ),
            "mean_gw_available_total": round(
                float(avail[internal][:, trough_h].sum(axis=0).mean()) / 1000.0, 4
            ),
            "cheapest_thermal_offer": round(float(np.nanmin(mc[internal])), 3),
        }

    # F — within-day offer variation (the pjm-141 T6 test).
    dsigma = []
    for d in np.unique(day):
        k = day == d
        block = mc[internal][:, k]
        dsigma.append(float(np.nanmax(block.std(axis=1))))
    trough_offer = float(
        np.average(mc[internal][:, trough_h], weights=avail[internal][:, trough_h])
        if avail[internal][:, trough_h].sum()
        else np.nan
    )
    peak_offer = float(
        np.average(mc[internal][:, peak_h], weights=avail[internal][:, peak_h])
        if avail[internal][:, peak_h].sum()
        else np.nan
    )

    result = {
        "n_lp_rows": int(mc.shape[0]),
        "n_internal_rows": int(internal.sum()),
        "trough_census": _census(trough_h),
        "peak_control_census": _census(peak_h),
        "stack_depth": depth,
        "within_day_offer_sigma_max": round(float(np.nanmax(dsigma)), 8),
        "cap_weighted_offer_trough": round(trough_offer, 4),
        "cap_weighted_offer_peak": round(peak_offer, 4),
    }
    del state, fa, mc, avail, row_dual
    gc.collect()
    return result


# ── G: diurnal amplitude ────────────────────────────────────────────────────


def _amplitude(bundle: Path, year: int) -> dict | None:
    """Fraction of the measured trough->peak price swing the model reproduces."""
    act = _actual_zonal(year)
    if act is None:
        return None
    price, dem = _model_zonal(bundle, year)
    idx = price.index.intersection(act.index)
    if idx.empty:
        return None
    price, act, dem = price.loc[idx], act.loc[idx], dem.loc[idx]
    w = dem.to_numpy(float)
    model = np.average(price.to_numpy(float), weights=w, axis=1)
    actual = np.average(act[list(MODEL_ZONES)].to_numpy(float), weights=w, axis=1)
    hod = np.asarray(idx.hour)
    t, p = np.isin(hod, TROUGH), np.isin(hod, PEAK)
    m_swing = float(model[p].mean() - model[t].mean())
    a_swing = float(actual[p].mean() - actual[t].mean())
    return {
        "model_trough": round(float(model[t].mean()), 3),
        "model_peak": round(float(model[p].mean()), 3),
        "actual_trough": round(float(actual[t].mean()), 3),
        "actual_peak": round(float(actual[p].mean()), 3),
        "model_swing": round(m_swing, 3),
        "actual_swing": round(a_swing, 3),
        "share_reproduced": round(m_swing / a_swing, 4) if a_swing else None,
        "trough_error": round(float(model[t].mean() - actual[t].mean()), 3),
        "peak_error": round(float(model[p].mean() - actual[p].mean()), 3),
    }


def main(argv: list[str] | None = None) -> int:
    """Run every measurement and write the machine-readable result."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/nyiso108_hydrorepair_B")
    ap.add_argument("--out", default="results/calibration/_nyiso109_trough_offer_stack.json")
    ap.add_argument(
        "--no-fleet",
        action="store_true",
        help="skip D/E/F (no fleet build) — A/B/C/G only",
    )
    args = ap.parse_args(argv)
    bundle = Path(args.bundle)

    out: dict = {"bundle": str(bundle), "eps": EPS, "trough_hours": list(TROUGH),
                 "peak_hours": list(PEAK), "years": {}}
    for year in YEARS:
        rec: dict = {
            "A_residual_deciles": _residual_deciles(bundle, year),
            "B_zonal_separation": _zonal_separation(bundle, year),
            "C_interface_reality": _interface_reality(year),
            "G_amplitude": _amplitude(bundle, year),
        }
        if not args.no_fleet:
            rec["DEF_fleet_census"] = _fleet_census(bundle, year)
        out["years"][str(year)] = rec
        print(f"[nyiso-109] {year} done", flush=True)

    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
