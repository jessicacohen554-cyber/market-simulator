"""nyiso-196 PHASE 0 part 2 (NO LP) — zero-LP rebuilds of the keeper's fleet
with ``unit_outage_extract_basis_share`` OFF (the keeper recipe) and ON (the
arm), plus the three step-3 measured-input checks the decomposition left open.

On the keeper's committed ``meta.json`` recipe (``scripts.lib.bundle_fleet``,
rule 29 ``[R-SCREEN]`` step 0; control = the keeper's committed bundle, form 4):

* **F-1 footprint** — which LP units' ``availability`` differ between the two
  rebuilds (must be CC bins only, the plants the census names), and that
  ``pmax``, heat rate, ``offer_markup_hr`` and the assembled ``mc_base`` are
  byte-identical on every unit (the flag touches availability and nothing else).
* **F-2 identity** — on every moved plant the arm/keeper availability ratio
  equals the loader's own on/off ratio hour for hour (the flag reaches the LP
  through ``unit_outage_derate_factors`` and through nothing else).
* **A-1 bucket-(a) economics at Cricket Valley** — in the hours the keeper has
  the plant on and the meter has it off, the share where the keeper-zone LMP
  clears the committed tranche's assembled offer (plain economics on the
  availability the LP was given) and the share inside the over-availed
  windows.
* **G-1 delivered gas** — the keeper's assembled delivered gas price for each
  zone's CC_REGULAR units (cap-weighted monthly mean) against the committed
  measured hub series (``transco_z6_iroquois_monthly.csv`` Iroquois Z2 for the
  east zones, Transco Z6 NY for NYC; the SOM annual Tenn Z4 200L for
  Upstate_West) — a basis error would show as a monthly ratio away from 1.
* **I-1 import capability** — the model's hourly import capability (import
  pseudo-units' ``pmax x availability``) against the measured scheduled
  interchange (sum of the SCH-* interfaces): the hours and MWh in which the
  measured flow exceeds what the LP could import at all.

Writes ``results/calibration/_nyiso196_rebuild_checks_<year>.json``.

Usage::

    python scripts/probes/nyiso196_rebuild_checks.py [--year 2024]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))
from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402
from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402
from scripts.lib.bundle_fleet import (  # noqa: E402
    bundle_gas_price,
    clear_fleet_caches,
    ensure_probe_path,
    full_run_year_kwargs,
)

KEEPER_ID = "2026-09-05-nyiso-192-astoria-panel"
BUNDLE = ROOT / "results/calibration/nyiso192_astoria_panel"
FLAG = "unit_outage_extract_basis_share"
T = 8760
CV = 57185
MONTH_STARTS = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
SCHED_INTERFACES = (
    "SCH - HQ - NY",
    "SCH - HQ_CEDARS",
    "SCH - NE - NY",
    "SCH - NPX_1385",
    "SCH - NPX_CSC",
    "SCH - OH - NY",
    "SCH - PJ - NY",
    "SCH - PJM_HTP",
    "SCH - PJM_NEPTUNE",
    "SCH - PJM_VFT",
)


def _dec(b64: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def _series(entry: dict, key_bytes: str, key_ann: str, npl: float) -> np.ndarray | None:
    raw_b64 = entry.get(key_bytes)
    if not raw_b64:
        return None
    raw = _dec(raw_b64)[:T]
    ann = entry.get(key_ann)
    if ann not in (None, "", "None") and raw.sum() > 0:
        return raw * (float(ann) * 1e6 / raw.sum())
    return raw * npl / 100.0 if npl > 0 else None


def rebuild(year: int, arm: bool) -> dict:
    """On-recipe ``run_year(fleet_only=True)`` rebuild, cached as slim arrays."""
    cache = (
        ROOT
        / ".cache"
        / "nyiso196"
        / f"rebuild_{year}_{'arm' if arm else 'keeper'}.pkl"
    )
    if cache.exists():
        return pickle.load(open(cache, "rb"))
    ensure_probe_path()
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = full_run_year_kwargs(meta)
    if arm:
        bag = dict(kwargs.get("prb_overrides") or {})
        bag[FLAG] = True
        kwargs["prb_overrides"] = bag
    clear_fleet_caches()
    state = run_year(
        year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, year), **kwargs
    )
    fa = state["fleet_arrays"]
    cfg = state["config"]
    rows = []
    for i, g in enumerate(state["fleet"]):
        rows.append(
            {
                "i": i,
                "unit_id": str(g.unit_id),
                "plant": int(getattr(g, "plant_code", 0) or 0),
                "group": str(getattr(g, "plant_group", "") or ""),
                "zone": str(getattr(g, "zone", "")),
                "fuel": str(getattr(g, "fuel_type", "")),
                "pmax": float(g.pmax_mw),
                "hr": float(getattr(g, "heat_rate", 0.0) or 0.0),
                "markup_hr": float(getattr(g, "offer_markup_hr", 0.0) or 0.0),
            }
        )
    st = {
        "units": pd.DataFrame(rows),
        "avail": np.asarray(fa.availability, dtype=np.float32),
        "mc": np.asarray(state["mc_base"], dtype=np.float32),
        "fuel": np.asarray(state["fuel_prices"], dtype=np.float32),
        "flag": bool(getattr(cfg, FLAG, False)),
        "lp_capacity_basis": bool(getattr(cfg, "unit_outage_lp_capacity_basis", False)),
    }
    cache.parent.mkdir(parents=True, exist_ok=True)
    pickle.dump(st, open(cache, "wb"))
    return st


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2024)
    a = ap.parse_args()
    yr = a.year
    K = rebuild(yr, arm=False)
    A = rebuild(yr, arm=True)
    U = K["units"]
    assert (U.unit_id.to_numpy() == A["units"].unit_id.to_numpy()).all(), (
        "unit roster differs"
    )
    out = {
        "session": "nyiso-196",
        "year": yr,
        "keeper": KEEPER_ID,
        "flag": FLAG,
        "flag_state": {"keeper": K["flag"], "arm": A["flag"]},
    }

    # ---- F-1 footprint ---------------------------------------------------------------
    dav = np.abs(A["avail"] - K["avail"]).max(axis=1)
    moved = U[dav > 1e-6]
    out["F1_footprint"] = {
        "units_availability_moved": int(len(moved)),
        "plants_moved": sorted({int(p) for p in moved.plant}),
        "groups_moved": sorted(set(moved.group)),
        "non_cc_units_moved": int((~moved.group.isin(["CC_REGULAR", "CC_CHP"])).sum()),
        "pmax_max_abs_delta": float(
            np.abs(A["units"].pmax.to_numpy() - U.pmax.to_numpy()).max()
        ),
        "hr_max_abs_delta": float(
            np.abs(A["units"].hr.to_numpy() - U.hr.to_numpy()).max()
        ),
        "markup_hr_max_abs_delta": float(
            np.abs(A["units"].markup_hr.to_numpy() - U.markup_hr.to_numpy()).max()
        ),
        "mc_base_max_abs_delta": float(np.abs(A["mc"] - K["mc"]).max()),
        "fuel_price_max_abs_delta": float(np.abs(A["fuel"] - K["fuel"]).max()),
        "PASS": bool(
            (~moved.group.isin(["CC_REGULAR", "CC_CHP"])).sum() == 0
            and np.abs(A["mc"] - K["mc"]).max() == 0.0
        ),
    }

    # ---- F-2 identity: arm/keeper availability ratio == loader on/off ratio ---------------
    off = unit_outage_derate_factors(
        yr, iso="NYISO", per_unit_crosswalk=True, merit_order_guard=True
    )
    on = unit_outage_derate_factors(
        yr,
        iso="NYISO",
        per_unit_crosswalk=True,
        merit_order_guard=True,
        extract_basis_share=True,
    )
    ident = []
    worst = 0.0
    for (plant, group), grp in moved.groupby(["plant", "group"]):
        k_off, k_on = off.get((plant, group)), on.get((plant, group))
        if k_off is None or k_on is None:
            ident.append(
                {"plant": int(plant), "group": group, "note": "no loader factor"}
            )
            continue
        ratio_loader = np.where(
            k_off > 0, k_on / np.where(k_off > 0, k_off, 1.0), np.nan
        )[:T]
        errs = []
        for i in grp.i:
            ka, aa = K["avail"][i][:T], A["avail"][i][:T]
            m = (ka > 1e-6) & ~np.isnan(ratio_loader)
            errs.append(
                float(np.abs(aa[m] / ka[m] - ratio_loader[m]).max()) if m.any() else 0.0
            )
        e = max(errs) if errs else 0.0
        worst = max(worst, e)
        ident.append(
            {
                "plant": int(plant),
                "group": group,
                "tranches": int(len(grp)),
                "mean_avail_keeper": round(
                    float(
                        np.average(
                            K["avail"][grp.i.to_numpy()][:, :T].mean(axis=1),
                            weights=grp.pmax,
                        )
                    ),
                    4,
                ),
                "mean_avail_arm": round(
                    float(
                        np.average(
                            A["avail"][grp.i.to_numpy()][:, :T].mean(axis=1),
                            weights=grp.pmax,
                        )
                    ),
                    4,
                ),
                "loader_off_mean": round(float(k_off.mean()), 4),
                "loader_on_mean": round(float(k_on.mean()), 4),
                "max_ratio_err": round(e, 6),
            }
        )
    out["F2_identity"] = {
        "plants": ident,
        "max_ratio_err": worst,
        "PASS": bool(worst < 1e-4),
    }

    # ---- A-1 bucket-(a) economics at Cricket Valley -------------------------------------
    run = decode_run_js(
        (ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    )
    bench = json.load(
        gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{yr}.json.gz")
    )["bench"]["plants"]
    ent, b = run["years"][str(yr)]["plants"][str(CV)], bench[str(CV)]
    npl = float(b["npl"])
    m = _series(ent, "m", "m_ann", npl)
    c = _series(b, "campd", "c_ann", npl)
    thr = 0.01 * npl + 1.0
    sysp = pd.read_parquet(BUNDLE / "hourly" / f"system_{yr}.parquet")
    lmp = sysp.pivot(index="hour", columns="zone", values="price").iloc[:T]
    cv = U[(U.plant == CV) & (U.group == "CC_REGULAR")]
    zone = cv.zone.iloc[0]
    lz = lmp[zone].to_numpy()
    comm = cv[cv.unit_id.str.endswith("_committed")]
    mc_comm = K["mc"][comm.i.to_numpy()][:, :T].min(axis=0) if len(comm) else None
    a_mask = (m > thr) & (c <= thr)
    k_off_cv, k_on_cv = off[(CV, "CC_REGULAR")][:T], on[(CV, "CC_REGULAR")][:T]
    over = k_off_cv > k_on_cv + 1e-9
    dark = k_on_cv <= 1e-9
    out["A1_cv_bucket_a"] = {
        "zone": zone,
        "bucket_a_hours": int(a_mask.sum()),
        "bucket_a_gwh": round(float(m[a_mask].sum()) / 1e3, 1),
        "share_hours_lmp_ge_committed_offer": round(
            float((lz[a_mask] >= mc_comm[a_mask]).mean()), 3
        )
        if mc_comm is not None
        else None,
        "committed_offer_mean_$MWh": round(float(mc_comm.mean()), 2)
        if mc_comm is not None
        else None,
        "zone_lmp_mean_in_a_$MWh": round(float(lz[a_mask].mean()), 2)
        if a_mask.any()
        else None,
        "share_a_hours_in_over_availed_windows": round(float(over[a_mask].mean()), 3)
        if a_mask.any()
        else None,
        "share_a_hours_in_extract_dark_windows": round(float(dark[a_mask].mean()), 3)
        if a_mask.any()
        else None,
        "a_gwh_in_over_availed_windows": round(float(m[a_mask & over].sum()) / 1e3, 1),
        "a_gwh_in_extract_dark_windows": round(float(m[a_mask & dark].sum()) / 1e3, 1),
        "bridge_binding_h_d4_2024": 40,
    }

    # ---- G-1 delivered gas vs measured hubs ----------------------------------------------
    hub = pd.read_csv(ROOT / "data/raw/gas-prices/transco_z6_iroquois_monthly.csv")
    hub = hub[hub.date.astype(str).str.startswith(f"{yr}-")]
    iroq = hub.iroquois_z2_usd_mmbtu.to_numpy()
    transco = hub.transco_z6_ny_usd_mmbtu.to_numpy()
    som = pd.read_csv(ROOT / "data/raw/nyiso_zonal_gas_hub.csv")
    som = som[som.year == yr].set_index("zone").hub_usd_mmbtu.to_dict()
    month = np.zeros(T, dtype=int)
    for i in range(12):
        month[MONTH_STARTS[i] : MONTH_STARTS[i + 1]] = i
    gas = {}
    for z, grp in U[(U.group == "CC_REGULAR")].groupby("zone"):
        fp = K["fuel"][grp.i.to_numpy()][:, :T]
        w = grp.pmax.to_numpy()
        zm = np.array(
            [np.average(fp[:, month == k].mean(axis=1), weights=w) for k in range(12)]
        )
        ref = transco if z == "NYC" else iroq
        gas[z] = {
            "model_monthly_$MMBtu": [round(float(v), 3) for v in zm],
            "measured_ref_monthly": [round(float(v), 3) for v in ref],
            "ref_series": "Transco Z6 NY"
            if z == "NYC"
            else "Iroquois Z2 (committed monthly construction)",
            "model_over_ref_monthly": [
                round(float(a_ / b_), 3) for a_, b_ in zip(zm, ref)
            ],
            "model_annual": round(float(zm.mean()), 3),
            "ref_annual": round(float(ref.mean()), 3),
            "som_annual_zone_hub": som.get(z),
        }
    out["G1_delivered_gas_cc_regular_by_zone"] = gas

    # ---- I-1 import capability vs measured scheduled imports -----------------------------
    imp = U[(U.plant <= 0) | (U.fuel.str.lower().str.contains("import"))]
    imports = None
    f = (
        ROOT
        / f"data/raw/NYISO/interface-flows/NYISO_interface_flows_hourly_{yr}.csv.gz"
    )
    if len(imp) and f.exists():
        capab = (
            K["avail"][imp.i.to_numpy()][:, :T] * imp.pmax.to_numpy()[:, None]
        ).sum(axis=0)
        fl = pd.read_csv(f)
        fl = fl[fl.interface.isin(SCHED_INTERFACES)]
        fl["t"] = pd.to_datetime(fl.interval_start_local)
        fl = fl[~((fl.t.dt.month == 2) & (fl.t.dt.day == 29))]
        fl["hoy"] = (
            fl.t.dt.dayofyear - 1 - ((fl.t.dt.month > 2) & (yr % 4 == 0)).astype(int)
        ) * 24 + fl.t.dt.hour
        meas = fl.groupby("hoy").flow_mw.sum().reindex(range(T)).ffill().to_numpy()
        exceed = meas > capab + 1.0
        imports = {
            "import_pseudo_units": int(len(imp)),
            "unit_ids": sorted(imp.unit_id)[:20],
            "capability_twh": round(float(capab.sum()) / 1e6, 3),
            "measured_sched_import_twh": round(float(meas.sum()) / 1e6, 3),
            "hours_measured_exceeds_capability": int(exceed.sum()),
            "mwh_measured_above_capability_gwh": round(
                float((meas - capab)[exceed].sum()) / 1e3, 1
            ),
            "capability_p50_mw": round(float(np.percentile(capab, 50)), 0),
            "measured_p50_mw": round(float(np.percentile(meas, 50)), 0),
            "measured_p99_mw": round(float(np.percentile(meas, 99)), 0),
        }
    out["I1_import_capability"] = imports

    dst = ROOT / f"results/calibration/_nyiso196_rebuild_checks_{yr}.json"
    dst.write_text(
        json.dumps(
            out,
            indent=1,
            default=lambda o: (
                float(o)
                if isinstance(o, np.floating)
                else int(o)
                if isinstance(o, np.integer)
                else bool(o)
            ),
        )
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in out.items()
                if k != "G1_delivered_gas_cc_regular_by_zone"
            },
            indent=1,
            default=str,
        )[:6000]
    )
    for z, g in gas.items():
        print(
            z,
            "model/ref monthly",
            g["model_over_ref_monthly"],
            "annual",
            g["model_annual"],
            "ref",
            g["ref_annual"],
            "SOM",
            g["som_annual_zone_hub"],
        )
    print(f"wrote {dst.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
