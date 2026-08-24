#!/usr/bin/env python3
"""ercot-233 Phase-0: does ANY admissible zonal-grain driver predict measured
``NE_LOB`` binding-hour incidence materially better than chance?

Executes the card-Y (Y-C) RESOLUTIONS item under
``docs/PRECOMMIT-ercot233-nelob-timing-phase0-2026-08-24.md`` — pushed and
blob-verified before this file computed anything. Read-only, zero fitted
scalars, no LP, no solve, no mechanism; the verdict bars, driver list,
directions and tolerances are all fixed in the precommit.

Target constructions are imported from ``ercot232_gspur_phase0`` verbatim
(the hourly-equivalent measured dual and the model-side link dual), so model
hour *i* and measured hour *i* ride the exact conventions of the adjudicated
record. A target mismatch against the ercot-232 record (2,408 binding hours,
annual dual ~= $69,932) STOPS the probe.

Output: ``results/calibration/ercot233_nelob_timing_phase0.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ercot232_gspur_phase0 import _MC, _measured_nelob, _zonal_price  # noqa: E402

YEAR = 2023
KEEPER = "ercot231_tiegtc_full"  # 2026-08-24-231-tie-zone-measured
HOURS = 8760
# Registered constant (constants.ERCOT_DC_TIE_ZONE_MAP): the SWPP-tie share
# physically hosted in the Northeast zone (Monticello DC-East 600 of 820 MW).
NE_SWPP_SHARE = 600.0 / 820.0
# Thermal plant groups admitted to the lobe-capability driver (precommit §2).
THERMAL_GROUPS = {"COAL", "CC_REGULAR", "CT_PEAKER", "CC_CHP", "CT_CHP", "ST_GAS"}
# Precommit §3 bars — fixed before measurement.
AUC_NAMED, AUC_BORDER, LIFT_NAMED, AT_BAR_TOL = 0.70, 0.65, 1.5, 0.02


def _auc(x: np.ndarray, y: np.ndarray) -> float:
    """Mann-Whitney AUC of score ``x`` for binary ``y`` (ties mid-ranked)."""
    r = rankdata(x)
    n1, n0 = int(y.sum()), int((~y.astype(bool)).sum())
    return float((r[y.astype(bool)].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def _hoy_of_dates(dates: pd.Series) -> np.ndarray:
    """Hour-of-year of midnight of each date on the fixed non-leap calendar."""
    mo, dy = dates.dt.month.to_numpy(), dates.dt.day.to_numpy()
    return (_MC[mo - 1] + dy - 1) * 24


def _driver_d1() -> tuple[np.ndarray, np.ndarray]:
    """(limit series, active mask) from the curated gtc-limits partition."""
    g = pd.read_parquet(REPO / "data/clean/gtc-limits/ERCOT/gtc-limits_2023.parquet")
    g = g[g["gtc"] == "NE_LOB"]
    limit = np.full(HOURS, np.nan)
    limit[g["hour"].to_numpy(int)] = g["limit_mean_mw"].to_numpy(float)
    active = np.isfinite(limit)
    return limit, active


def _driver_d2() -> tuple[np.ndarray, dict]:
    """NE-lobe CAMPD-available thermal MW, and its provenance detail."""
    from market_sim.data.outages import _has_hour_grain, unit_outage_event_window
    from market_sim.data.zone_assignment import build_zone_lookup

    reg = pd.read_csv(REPO / "data/raw/reference/master-plant-registry.csv")
    zl = build_zone_lookup("ERCOT")
    reg["zone"] = reg["plantid"].map(zl)
    ne = reg[(reg["zone"] == "Northeast") & reg["plant_group"].isin(THERMAL_GROUPS)]
    nameplate = {int(r.plantid): float(r.nameplate_capacity_mw)
                 for r in ne.itertuples(index=False)}

    ev = pd.read_csv(REPO / "data/raw/campd-unit-outages.csv")
    ev = ev[ev["facility_id"].isin(nameplate)].copy()
    ev["outage_start"] = pd.to_datetime(ev["outage_start"])
    ev["outage_end"] = pd.to_datetime(ev["outage_end"])
    grain = _has_hour_grain(ev)

    y0, y1 = pd.Timestamp(f"{YEAR}-01-01"), pd.Timestamp(f"{YEAR + 1}-01-01")
    outaged = {pc: np.zeros(HOURS) for pc in nameplate}
    n_events = 0
    for r in ev.itertuples(index=False):
        start, stop = unit_outage_event_window(r, grain)
        start, stop = max(start, y0), min(stop, y1)
        if start >= stop:
            continue
        n_events += 1
        lo = int(_hoy_of_dates(pd.Series([start]))[0] + start.hour)
        hi = int(_hoy_of_dates(pd.Series([stop]))[0] + stop.hour)
        outaged[int(r.facility_id)][lo:min(hi, HOURS)] += float(r.unit_capacity_mw)

    avail = np.zeros(HOURS)
    for pc, cap in nameplate.items():
        avail += np.clip(cap - outaged[pc], 0.0, cap)
    detail = {
        "plants": {str(pc): {"name": str(reg.set_index("plantid").loc[pc, "plant_name"]),
                             "nameplate_mw": round(nameplate[pc], 1)}
                   for pc in nameplate},
        "total_nameplate_mw": round(sum(nameplate.values()), 1),
        "events_overlapping_year": n_events,
    }
    return avail, detail


def _driver_d4() -> np.ndarray:
    """Placed SWPP DC-tie import into the lobe (positive = import), MW."""
    d = pd.read_parquet(REPO / "data/raw/eia-930-interchange/ERCO interchange hourly.parquet")
    d = d[d["diba"] == "SWPP"].copy()
    d["local_time"] = pd.to_datetime(d["local_time"])
    # Hour-ending window slice [Jan-1 01:00 .. Jan-1 00:00 of year+1] -> model
    # hour, the ercot_tie_zone_interchange convention (chronological per DIBA).
    w = d[(d["local_time"] >= pd.Timestamp(f"{YEAR}-01-01 01:00:00"))
          & (d["local_time"] <= pd.Timestamp(f"{YEAR + 1}-01-01 00:00:00"))]
    mw = w.sort_values("local_time")["mw"].to_numpy(float)
    if len(mw) != HOURS:
        raise SystemExit(f"STOP: SWPP window carries {len(mw)} hours, not {HOURS}")
    # EIA-930 sign: positive = net export from ERCO; import is the negative.
    return -mw * NE_SWPP_SHARE


def _ne_demand() -> np.ndarray:
    """The keeper's committed P1 Northeast zone demand (the model input)."""
    d = pd.read_parquet(REPO / f"results/calibration/{KEEPER}/hourly/system_{YEAR}.parquet")
    d = d[(d["pass"] == "P1") & (d["zone"] == "Northeast")]
    return d.set_index("hour")["demand"].reindex(range(HOURS)).to_numpy(float)


def _score(name: str, x: np.ndarray, sign: int, y: np.ndarray,
           dual: np.ndarray, mask: np.ndarray) -> dict:
    """Precommit §3 metrics for one driver over its scored hours."""
    m = mask & np.isfinite(x)
    xs, ys, ds = sign * x[m], y[m].astype(bool), dual[m]
    base = float(ys.mean())
    auc = _auc(xs, ys)
    top = xs >= np.quantile(xs, 0.9)
    lift = float(ys[top].mean() / base) if base > 0 else float("nan")
    rho = float(spearmanr(xs, ds).statistic)
    if auc >= AUC_NAMED - AT_BAR_TOL and auc < AUC_NAMED + AT_BAR_TOL:
        verdict = "AT-BAR (NAMED bar) — ESCALATE"
    elif auc >= AUC_NAMED:
        verdict = "NAMED — ESCALATE" if lift >= LIFT_NAMED else \
            "AUC past NAMED bar but lift below 1.5 — ESCALATE as borderline"
    elif auc >= AUC_BORDER - AT_BAR_TOL:
        verdict = ("BORDERLINE — ESCALATE" if auc >= AUC_BORDER
                   else "AT-BAR (BORDERLINE bar) — ESCALATE")
    else:
        verdict = "CLOSES"
    return {
        "driver": name, "scored_hours": int(m.sum()),
        "binding_base_rate": round(base, 4),
        "auc_presigned": round(auc, 4), "auc_raw_direction": int(sign),
        "top_decile_lift": round(lift, 3),
        "spearman_vs_dual": round(rho, 4),
        "verdict": verdict,
    }


def main() -> None:
    """Run the precommitted Phase-0 and write the probe JSON."""
    dual, frac = _measured_nelob()
    y = (frac > 0).astype(int)
    if int(y.sum()) != 2408 or abs(float(dual.sum()) - 69932) > 1.0:
        raise SystemExit(
            f"STOP: target mismatch vs ercot-232 record "
            f"(binding {int(y.sum())}, dual sum {dual.sum():.0f})")

    limit, active = _driver_d1()
    d2, d2_detail = _driver_d2()
    d4 = _driver_d4()
    dem = _ne_demand()
    d3 = d2 + d4 - dem

    all_h = np.ones(HOURS, bool)
    rows = [
        _score("d1_measured_limit_level", limit, -1, y, dual, active),
        _score("d2_lobe_campd_available_mw", d2, +1, y, dual, all_h),
        _score("d3_export_pressure_margin", d3, +1, y, dual, all_h),
        _score("d4_placed_tie_import_mw", d4, +1, y, dual, all_h),
    ]

    # Context (never scored as a driver): the model's own binding indicator.
    zp = _zonal_price(KEEPER)
    g = (zp["North"] - zp["Northeast"]).reindex(range(HOURS)).to_numpy(float)
    on = np.nan_to_num(g) > 1.0
    yb = y.astype(bool)
    sens = float(on[yb].mean())
    spec = float((~on[~yb]).mean())
    context = {
        "model_binding_hours": int(on.sum()),
        "sensitivity": round(sens, 4), "specificity": round(spec, 4),
        "implied_auc": round((sens + spec) / 2.0, 4),
        "corr_model_vs_measured_dual": round(float(np.corrcoef(np.nan_to_num(g), dual)[0, 1]), 4),
    }

    closes = all(r["verdict"] == "CLOSES" for r in rows)
    out = {
        "probe": "ercot233_nelob_timing_phase0",
        "precommit": "docs/PRECOMMIT-ercot233-nelob-timing-phase0-2026-08-24.md",
        "authorization": "card Y signed (Y-C) 2026-08-24; RESOLUTIONS item",
        "keeper": KEEPER, "year": YEAR,
        "target": {"binding_hours": int(y.sum()),
                   "annual_dual_sum": round(float(dual.sum()), 0),
                   "active_hours": int(active.sum())},
        "drivers": rows,
        "d2_provenance": d2_detail,
        "model_indicator_context": context,
        "object_verdict": (
            "CLOSES AT ZONAL GRAIN — no admissible zonal-grain driver reaches "
            "the precommit bars" if closes else
            "SURVIVING DRIVER(S) — ESCALATE TO THE OWNER, nothing armed"),
    }
    dest = REPO / "results/calibration/ercot233_nelob_timing_phase0.json"
    dest.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
