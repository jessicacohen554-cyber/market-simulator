"""caiso-258 (ZERO LP): the hod 22-23 energy balance, closed on BOTH sides.

Registered in
``results/calibration/PRECOMMIT-caiso258-hod2223-closure-2026-09-06.md``,
pushed before any cell of the object was computed. The hod 22-23 CC over-run
(+1,547 / +1,558 MW in 2025, CEMS basis) has had two carriers named and both
removed - import REFUSED on admissibility (caiso-253), storage on the WRONG SIDE
(caiso-255b / caiso-256). Rather than name a third from a mechanism looking for
a home, this probe writes the full closure at those hours - the keeper's LP
identity against the EIA-930 balancing-authority identity - and lets the
attribution fall out of it.

Legs, in the PRECOMMIT's order:

* **G-REPRO** - three published quantities reproduced ON THE caiso-257 KEEPER
  within +/-100 MW (the keeper changed identity at caiso-257).
* **G-CLOSE** - the model-side LP identity (< 1 MW every hour) and the
  EIA-930 balancing residual (shown, never absorbed).
* **G-CAT** - the 930-column <-> model-klass map checked on ANNUAL energy;
  ``NG: GEO`` is NaN all year, so the geothermal/biomass remainder is located
  as ``Net generation - sum(mapped NG columns)``.
* **D-1** - the closure table at hod 22 and 23, per year, model - measured.
* **D-2** - CAMPD unit conduct: where the CC over-run comes from, by the REAL
  unit's state (OFF / PART / HIGH), and the 21->23 shutdown transition counts.
* **D-4** - the object's C4-2025 exposure (share of the gas MSE at hod 22-23).
* **D-3** (``--import-stack``) - an on-recipe ``fleet_only`` rebuild reading the
  ARMED WECC import rows' capability / floor / offer at hod 22-23 against the
  committed node duals: capability gap or price gap.

Every EIA-930 actual comes through ``eia930.frames._eia_hourly_frame_filled``
(row k = local hour k on the model's clock; caiso-255b sec 6 #1). The CEMS
basis is the scorer's own (``calibration_verdict._cems_gas_hourly_fit``, via
the caiso-252 anatomy probe's ``_fleet``). Nothing here is an input to anything.

Output: ``results/calibration/_caiso258_hod2223_closure.json``.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso258_hod2223_closure.py
    PYTHONPATH=.:src uv run python scripts/probes/_caiso258_hod2223_closure.py --import-stack
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
_ARGV = list(sys.argv)
sys.argv = [sys.argv[0]]  # calibration_verdict parses argv at import

from scripts.calibration_verdict import GAS_CLASSES, load_artifacts  # noqa: E402

KEEPER = "2026-09-06-caiso-260-b1-demand"
BUNDLE = (
    REPO / "results/calibration/caiso260_demand_vintage"
)  # re-pointed caiso-261 (caiso-257 pruned, rule 15)
OUT = REPO / "results/calibration/_caiso258_hod2223_closure.json"
YEARS = (2023, 2024, 2025)
T = 8760
HOD = np.arange(T) % 24
DAY = np.arange(T) // 24
GAP = (22, 23)
CAISO_ZONES = ("NP15", "ZP26", "SP15_rest", "LA_BASIN", "SDGE")
NG_COLS = {
    "NG: NG": "gas",
    "NG: NUC": "nuclear",
    "NG: WAT": "hydro",
    "NG: SUN": "solar",
    "NG: WND": "wind",
    "NG: OTH": "oth",
    "NG: OIL": "oil",
    "NG: COL": "coal",
    "NG: GEO": "geo",
}
GAS_KLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")

#: G-REPRO comparators (caiso-252 keeper) and the registered tolerance.
PUB_CC_2223_2025 = (1547.0, 1558.0)
PUB_IMPORT_GAP = {2023: -984.0, 2024: -1405.0, 2025: -1662.0}
PUB_STORAGE_GAP = {2023: 532.3, 2024: 549.4, 2025: 707.3}
REPRO_TOL_MW = 100.0
#: D-2 state thresholds (fraction of nameplate).
OFF_MAX, HIGH_MIN, SHUTDOWN_FROM = 0.05, 0.80, 0.20


def _b64(s: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(s), dtype=np.uint8)[:T].astype(float)


def hod_mean(x: np.ndarray, hods=GAP) -> float:
    return float(np.nanmean(x[np.isin(HOD, hods)]))


# --------------------------------------------------------------------------- model
def model_hourlies(year: int) -> dict:
    """Keeper P1 hourlies from the committed sidecars, every series (T,)."""
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    piv = ch.pivot_table(index="hour", columns="klass", values="mw").reindex(range(T))
    klass = {str(k): piv[k].to_numpy(float) for k in piv.columns}
    st = pd.read_parquet(BUNDLE / f"hourly/storage_{year}.parquet")
    st = st[st["pass"] == "P1"]
    stor = {}
    for tech, g in st.groupby("tech", observed=True):
        gg = g.set_index("hour").reindex(range(T))
        stor[str(tech)] = {
            "dis": gg["discharge_mw"].to_numpy(float),
            "chg": gg["charge_mw"].to_numpy(float),
        }
    sy = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    sy = sy[sy["pass"] == "P1"]
    zones = {}
    for z, g in sy.groupby("zone"):
        gg = g.set_index("hour").reindex(range(T))
        zones[str(z)] = {
            c: gg[c].to_numpy(float) for c in ("price", "slack", "dump", "demand")
        }
    return {"klass": klass, "storage": stor, "zones": zones}


def model_close(m: dict) -> dict:
    """G-CLOSE, model side: sum(klass) + net storage + slack - dump - demand."""
    gen = sum(m["klass"].values())
    net_st = sum(v["dis"] - v["chg"] for v in m["storage"].values())
    dem = sum(m["zones"][z]["demand"] for z in CAISO_ZONES if z in m["zones"])
    slack = sum(m["zones"][z]["slack"] for z in CAISO_ZONES if z in m["zones"])
    dump = sum(m["zones"][z]["dump"] for z in CAISO_ZONES if z in m["zones"])
    other_z = [z for z in m["zones"] if z not in CAISO_ZONES]
    resid = gen + net_st + slack - dump - dem
    return {
        "max_abs_residual_mw": float(np.nanmax(np.abs(resid))),
        "mean_residual_mw": float(np.nanmean(resid)),
        "pass": bool(np.nanmax(np.abs(resid)) < 1.0),
        "non_caiso_zones": other_z,
        "non_caiso_demand_twh": float(
            sum(np.nansum(m["zones"][z]["demand"]) for z in other_z) / 1e6
        ),
        "non_caiso_slack_dump_twh": [
            float(sum(np.nansum(m["zones"][z]["slack"]) for z in other_z) / 1e6),
            float(sum(np.nansum(m["zones"][z]["dump"]) for z in other_z) / 1e6),
        ],
        "caiso_slack_twh": float(np.nansum(slack) / 1e6),
        "caiso_dump_twh": float(np.nansum(dump) / 1e6),
        "_series": {
            "gen": gen,
            "net_st": net_st,
            "dem": dem,
            "slack": slack,
            "dump": dump,
        },
    }


# --------------------------------------------------------------------------- measured
def measured(year: int) -> dict[str, np.ndarray]:
    """EIA-930 CISO on the MODEL's clock (row k = hour k). Never the raw stamps."""
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    f = _eia_hourly_frame_filled("CISO", year)
    if f is None or len(f) != T:
        raise SystemExit(f"EIA-930 CISO {year}: no clean 8760 frame")
    out = {}
    for col, name in NG_COLS.items():
        out[name] = (
            pd.to_numeric(f[col], errors="coerce").to_numpy(float)
            if col in f.columns
            else np.full(T, np.nan)
        )
    out["demand"] = pd.to_numeric(f["Demand"], errors="coerce").to_numpy(float)
    out["netgen"] = pd.to_numeric(f["Net generation"], errors="coerce").to_numpy(float)
    out["net_import"] = -pd.to_numeric(
        f["Total interchange"], errors="coerce"
    ).to_numpy(float)
    return out


def measured_close(a: dict) -> dict:
    """G-CLOSE / G-CAT, measured side: the BA residual and the unmapped remainder."""
    mapped = ["gas", "nuclear", "hydro", "solar", "wind", "oth", "oil", "coal"]
    ng_sum = sum(np.nan_to_num(a[k], nan=0.0) for k in mapped)
    unmapped = a["netgen"] - ng_sum
    resid = a["demand"] - a["netgen"] - a["net_import"]
    geo_nan = int(np.isnan(a["geo"]).sum())
    return {
        "ba_residual_mean_mw": float(np.nanmean(resid)),
        "ba_residual_mean_at_2223_mw": hod_mean(resid),
        "ba_residual_p05_p95_mw": [
            float(np.nanpercentile(resid, 5)),
            float(np.nanpercentile(resid, 95)),
        ],
        "unmapped_mean_mw": float(np.nanmean(unmapped)),
        "unmapped_twh": float(np.nansum(unmapped) / 1e6),
        "unmapped_by_hod_mw": [
            float(np.nanmean(unmapped[HOD == h])) for h in range(24)
        ],
        "unmapped_cv_over_hod": float(
            np.std([np.nanmean(unmapped[HOD == h]) for h in range(24)])
            / abs(np.nanmean(unmapped))
        )
        if np.nanmean(unmapped)
        else None,
        "geo_nan_hours": geo_nan,
        "geo_twh_where_present": float(np.nansum(a["geo"]) / 1e6),
        "annual_twh": {
            k: float(np.nansum(a[k]) / 1e6)
            for k in mapped + ["demand", "netgen", "net_import"]
        },
        "_series": {"unmapped": unmapped, "resid": resid},
    }


# --------------------------------------------------------------------------- CEMS
def cems_fleet(art: dict, year: int) -> dict:
    """The scorer's C4 basis, plant for plant (caiso-252 anatomy probe `_fleet`)."""
    ypay = art["payload"]["years"][str(year)]
    ybench = art["bench"][year]
    e930 = ybench["e930"]
    cogen = float(e930["gas_cogen_grid"])
    model_twh = next(r["m"] for r in ypay["fuelRows"] if r["fuel"] == "gas")
    plants = {}
    btm_twh = 0.0
    for code, bp in ybench["plants"].items():
        if bp.get("group") not in GAS_CLASSES or bp.get("nodata"):
            continue
        cap = float(bp.get("npl") or 0.0)
        pp = ypay["plants"].get(str(code))
        if cap <= 0.0 or not bp.get("campd") or not pp or not pp.get("m"):
            continue
        scale = cap / 100.0
        plants[str(code)] = {
            "group": bp["group"],
            "name": bp.get("name"),
            "zone": bp.get("zone"),
            "npl": cap,
            "act": _b64(bp["campd"]) * scale,
            "mod": _b64(pp["m"]) * scale,
        }
        btm_twh += float(bp.get("btm") or 0.0)
    btm_mw = btm_twh * 1e6 / T
    core_twh = sum(p["mod"].sum() for p in plants.values()) / 1e6 - btm_twh
    fill_mw = (float(model_twh) - core_twh) * 1e6 / T
    act = sum(p["act"] for p in plants.values()) - btm_mw + cogen * 1e6 / T
    mod = sum(p["mod"] for p in plants.values()) - btm_mw + fill_mw
    r = float(np.corrcoef(mod, act)[0, 1])
    nrmse = float(np.sqrt(np.mean((mod - act) ** 2)) / act.mean())
    return {
        "plants": plants,
        "act": act,
        "mod": mod,
        "e": mod - act,
        "fit": (round(r, 3), round(nrmse, 3)),
        "fill_mw": fill_mw,
        "cogen_mw": cogen * 1e6 / T,
        "btm_mw": btm_mw,
        "n_plants": len(plants),
    }


def cems_class_error(fl: dict, group: str) -> np.ndarray:
    ps = [p for p in fl["plants"].values() if p["group"] == group]
    return sum(p["mod"] - p["act"] for p in ps) if ps else np.zeros(T)


def cems_class_pair(fl: dict, group: str) -> tuple[np.ndarray, np.ndarray]:
    ps = [p for p in fl["plants"].values() if p["group"] == group]
    if not ps:
        return np.zeros(T), np.zeros(T)
    return sum(p["mod"] for p in ps), sum(p["act"] for p in ps)


# --------------------------------------------------------------------------- D-2
def unit_conduct(fl: dict, hods=GAP) -> dict:
    """CC_REGULAR over-run at `hods` split by the REAL unit's state, plus 21->23 shutdowns."""
    sel = np.isin(HOD, hods)
    by_state = {"OFF": 0.0, "PART": 0.0, "HIGH": 0.0}
    by_state_neg = {"OFF": 0.0, "PART": 0.0, "HIGH": 0.0}
    ph_act = {"OFF": 0, "PART": 0, "HIGH": 0}
    ph_mod = {"OFF": 0, "PART": 0, "HIGH": 0}
    per_plant = []
    sd_act = sd_mod = 0
    n_days = T // 24
    for code, p in fl["plants"].items():
        if p["group"] != "CC_REGULAR":
            continue
        npl = p["npl"]
        fa, fm = p["act"] / npl, p["mod"] / npl
        e = p["mod"] - p["act"]
        st_a = np.where(fa < OFF_MAX, 0, np.where(fa < HIGH_MIN, 1, 2))
        st_m = np.where(fm < OFF_MAX, 0, np.where(fm < HIGH_MIN, 1, 2))
        names = ("OFF", "PART", "HIGH")
        contrib = {}
        for i, nm in enumerate(names):
            m = sel & (st_a == i)
            pos = float(np.clip(e[m], 0, None).sum())
            neg = float(np.clip(e[m], None, 0).sum())
            by_state[nm] += pos
            by_state_neg[nm] += neg
            ph_act[nm] += int(m.sum())
            ph_mod[nm] += int((sel & (st_m == i)).sum())
            contrib[nm] = pos + neg
        # evening shutdown: >= 20 % at hod 21, < 5 % at hod 23, same day
        a21, a23 = fa.reshape(n_days, 24)[:, 21], fa.reshape(n_days, 24)[:, 23]
        m21, m23 = fm.reshape(n_days, 24)[:, 21], fm.reshape(n_days, 24)[:, 23]
        sda = int(((a21 >= SHUTDOWN_FROM) & (a23 < OFF_MAX)).sum())
        sdm = int(((m21 >= SHUTDOWN_FROM) & (m23 < OFF_MAX)).sum())
        sd_act += sda
        sd_mod += sdm
        per_plant.append(
            {
                "code": code,
                "name": p["name"],
                "zone": p["zone"],
                "npl": npl,
                "err_2223_mean_mw": float(e[sel].mean()),
                "act_2223_mean_cf": float(fa[sel].mean()),
                "mod_2223_mean_cf": float(fm[sel].mean()),
                "act_off_share_2223": float((st_a[sel] == 0).mean()),
                "mod_off_share_2223": float((st_m[sel] == 0).mean()),
                "shutdowns_21_23_act": sda,
                "shutdowns_21_23_mod": sdm,
                "contrib_mwh_by_act_state": contrib,
            }
        )
    n_sel = int(sel.sum())
    tot_pos = sum(by_state.values())
    tot = sum(by_state.values()) + sum(by_state_neg.values())
    return {
        "n_cc_plants": len(per_plant),
        "plant_hours": n_sel * len(per_plant),
        "over_run_mean_mw_at_2223": float(tot / n_sel),
        "positive_mwh_by_act_state": by_state,
        "negative_mwh_by_act_state": by_state_neg,
        "positive_share_by_act_state": {
            k: (v / tot_pos if tot_pos else None) for k, v in by_state.items()
        },
        "net_share_by_act_state": {
            k: ((by_state[k] + by_state_neg[k]) / tot if tot else None)
            for k in by_state
        },
        "plant_hours_by_state_actual": ph_act,
        "plant_hours_by_state_model": ph_mod,
        "shutdowns_21_23_actual": sd_act,
        "shutdowns_21_23_model": sd_mod,
        "top_plants_by_err": sorted(per_plant, key=lambda r: -r["err_2223_mean_mw"])[
            :12
        ],
        "bottom_plants_by_err": sorted(per_plant, key=lambda r: r["err_2223_mean_mw"])[
            :5
        ],
    }


# --------------------------------------------------------------------------- G-REPRO decomposition
E930_RAW = REPO / "data/raw/eia-930-hourly/CISO hourly.parquet"


def net_import_caiso253_construction(year: int) -> np.ndarray:
    """caiso-253 P-5's OWN clock: raw parquet ``Local time`` minus one hour, Feb-29 dropped.

    Reproduced here (not imported — the caiso-253 probe hard-codes the pruned
    caiso-252 bundle path) so the one G-REPRO miss can be decomposed into
    clock-construction vs keeper-identity by measurement. This is NOT the
    loader's model clock (caiso-255b sec 6 #1) and is used for nothing else.
    """
    d = pd.read_parquet(E930_RAW)
    lt = pd.to_datetime(d["Local time"]) - pd.Timedelta(hours=1)
    d = d.assign(lt=lt)
    d = d[
        (d["lt"].dt.year == year) & ~((d["lt"].dt.month == 2) & (d["lt"].dt.day == 29))
    ]
    dt = pd.DatetimeIndex(d["lt"])
    doy = dt.dayofyear.to_numpy()
    if year % 4 == 0:
        doy = np.where(dt.month.to_numpy() > 2, doy - 1, doy)
    h = (doy - 1) * 24 + dt.hour.to_numpy()
    a = np.full(T, np.nan)
    a[h] = -d["Total interchange"].to_numpy(float)
    return a


def offstate_split(fl: dict, hods=GAP) -> dict:
    """D-2b (post-registration refinement of D-2 item 2, labelled): the OFF-state
    over-run split into plant-days where the REAL unit was off ALL DAY
    (daily max < 5 % of nameplate) vs days it RAN and had cycled off by `hods`
    (daily max >= 20 %). Also each plant's whole-day-off day counts, actual vs model."""
    n_days = T // 24
    tot = {
        "whole_day_off_plant_hours": 0,
        "cycled_plant_hours": 0,
        "whole_day_off_pos_mwh": 0.0,
        "cycled_pos_mwh": 0.0,
    }
    rows = []
    for code, p in fl["plants"].items():
        if p["group"] != "CC_REGULAR":
            continue
        fa = (p["act"] / p["npl"]).reshape(n_days, 24)
        fm = (p["mod"] / p["npl"]).reshape(n_days, 24)
        e = (p["mod"] - p["act"]).reshape(n_days, 24)[:, list(hods)]
        off = fa[:, list(hods)] < OFF_MAX
        dmax = fa.max(axis=1)
        wd = (dmax < OFF_MAX)[:, None] & off
        cy = (dmax >= SHUTDOWN_FROM)[:, None] & off
        w_mwh = float(np.clip(e[wd], 0, None).sum())
        c_mwh = float(np.clip(e[cy], 0, None).sum())
        tot["whole_day_off_plant_hours"] += int(wd.sum())
        tot["cycled_plant_hours"] += int(cy.sum())
        tot["whole_day_off_pos_mwh"] += w_mwh
        tot["cycled_pos_mwh"] += c_mwh
        rows.append(
            {
                "code": code,
                "name": p["name"],
                "npl": p["npl"],
                "whole_day_off_days_actual": int((dmax < OFF_MAX).sum()),
                "whole_day_off_days_model": int((fm.max(axis=1) < OFF_MAX).sum()),
                "over_run_mw_from_whole_day_off": w_mwh / (n_days * len(hods)),
                "over_run_mw_from_cycled": c_mwh / (n_days * len(hods)),
            }
        )
    nh = n_days * len(hods)
    return {
        **tot,
        "over_run_mw_from_whole_day_off_days": tot["whole_day_off_pos_mwh"] / nh,
        "over_run_mw_from_cycled_days": tot["cycled_pos_mwh"] / nh,
        "plants": sorted(
            rows,
            key=lambda r: (
                -(r["over_run_mw_from_whole_day_off"] + r["over_run_mw_from_cycled"])
            ),
        )[:10],
    }


# --------------------------------------------------------------------------- D-3
def import_stack(year: int, m: dict) -> dict:
    """On-recipe fleet_only rebuild: the ARMED WECC rows at hod 22-23 vs the committed duals."""
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    clear_fleet_caches()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        st = run_year(
            year,
            meta["iso"],
            T,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kw,
        )
    warn = [
        ln
        for ln in buf.getvalue().splitlines()
        if "7,500" in ln or "7500" in ln or "fallback" in ln.lower()
    ]
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], dtype=float)
    sel = np.isin(HOD, GAP)
    imp = m["klass"]["import"]
    rows = {}
    cap_tot = np.zeros(T)
    floor_tot = np.zeros(T)
    priced_out_tot = np.zeros(T)
    for row, uid in enumerate(np.asarray(fa.unit_ids).astype(str)):
        if not uid.startswith("WECC"):
            continue
        zone = (
            "WECC_DSW"
            if uid.startswith("WECC_DSW")
            else "WECC_PNW"
            if uid.startswith("WECC_PNW")
            else None
        )
        node = m["zones"].get(zone, {}).get("price") if zone else None
        av = np.asarray(fa.availability[row], float)
        av = np.broadcast_to(av, (T,)) if av.ndim == 0 else av
        cap = float(fa.pmax[row]) * av
        mg = getattr(fa, "min_gen", None)
        floor = (
            np.broadcast_to(np.asarray(mg[row], float), (T,))
            if mg is not None
            else np.zeros(T)
        )
        offer = np.broadcast_to(np.asarray(mc[row], float), (T,))
        po = (offer > node + 1e-6) if node is not None else np.zeros(T, bool)
        cap_tot += cap
        floor_tot += floor
        priced_out_tot += np.where(po, cap - floor, 0.0)
        rows[uid] = {
            "zone": zone,
            "pmax": float(fa.pmax[row]),
            "offer_2223_mean": float(offer[sel].mean()),
            "node_dual_2223_mean": float(node[sel].mean())
            if node is not None
            else None,
            "cap_2223_mean_mw": float(cap[sel].mean()),
            "floor_2223_mean_mw": float(floor[sel].mean()),
            "priced_out_share_2223": float(po[sel].mean()),
            "priced_out_headroom_2223_mean_mw": float(
                np.where(po, cap - floor, 0.0)[sel].mean()
            ),
            "cap_by_hod": [float(cap[HOD == h].mean()) for h in range(24)],
            "floor_by_hod": [float(floor[HOD == h].mean()) for h in range(24)],
        }
    bound_ok = bool(np.all(imp <= cap_tot + 1.0))
    return {
        "rebuild_stderr_fallback_lines": warn,
        "n_wecc_rows": len(rows),
        "committed_import_2223_mean_mw": hod_mean(imp),
        "sum_cap_2223_mean_mw": hod_mean(cap_tot),
        "sum_floor_2223_mean_mw": hod_mean(floor_tot),
        "import_over_cap_2223": hod_mean(imp) / hod_mean(cap_tot)
        if hod_mean(cap_tot)
        else None,
        "priced_out_headroom_2223_mean_mw": hod_mean(priced_out_tot),
        "committed_import_within_cap_every_hour": bound_ok,
        "max_import_minus_cap_mw": float(np.nanmax(imp - cap_tot)),
        "import_by_hod": [float(np.nanmean(imp[HOD == h])) for h in range(24)],
        "cap_by_hod": [float(cap_tot[HOD == h].mean()) for h in range(24)],
        "rows": rows,
    }


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--import-stack", action="store_true", help="D-3: the fleet_only rebuild leg"
    )
    a = ap.parse_args(_ARGV[1:])

    art = load_artifacts(KEEPER)
    res: dict = {
        "session": "caiso-258",
        "keeper": KEEPER,
        "gap_hours": list(GAP),
        "years": {},
        "gates": {},
    }

    repro: dict = {}
    for y in YEARS:
        m = model_hourlies(y)
        mc_ = model_close(m)
        a930 = measured(y)
        ac = measured_close(a930)
        fl = cems_fleet(art, y)
        yr: dict = {}

        # ---- G-REPRO ---------------------------------------------------------
        cc_e = cems_class_error(fl, "CC_REGULAR")
        imp_gap = m["klass"]["import"] - a930["net_import"]
        st_all = sum(v["dis"] - v["chg"] for v in m["storage"].values())
        st_gap = st_all - a930["oth"]
        rp = {
            "import_gap_2223": hod_mean(imp_gap),
            "storage_allteck_gap_2223": hod_mean(st_gap),
            "c4_fit": fl["fit"],
        }
        if y == 2025:
            rp["cc_err_hod22"] = float(cc_e[HOD == 22].mean())
            rp["cc_err_hod23"] = float(cc_e[HOD == 23].mean())
        rp["import_gap_2223_caiso253_construction"] = hod_mean(
            m["klass"]["import"] - net_import_caiso253_construction(y)
        )
        rp["import_klass_min_mw"] = float(np.nanmin(m["klass"]["import"]))
        repro[str(y)] = rp

        # ---- D-1 closure table ------------------------------------------------
        li = m["storage"].get("li_ion", {"dis": np.zeros(T), "chg": np.zeros(T)})
        ps = m["storage"].get(
            "pumped_storage", {"dis": np.zeros(T), "chg": np.zeros(T)}
        )
        li_net, ps_net = li["dis"] - li["chg"], ps["dis"] - ps["chg"]
        k = m["klass"]
        gas_model_klass = sum(k.get(g, np.zeros(T)) for g in GAS_KLASSES)
        other_model = k.get("OTHER", np.zeros(T)) + k.get("biomass", np.zeros(T))
        rows = {
            "demand": (mc_["_series"]["dem"], a930["demand"]),
            "gas_930_basis": (gas_model_klass, a930["gas"]),
            "gas_cems_basis_total": (fl["mod"], fl["act"]),
            "nuclear": (k.get("nuclear", np.zeros(T)), a930["nuclear"]),
            "hydro_conv_vs_WAT": (k.get("hydro", np.zeros(T)), a930["hydro"]),
            "hydro_plus_ps_vs_WAT": (
                k.get("hydro", np.zeros(T)) + ps_net,
                a930["hydro"],
            ),
            "solar": (k.get("solar", np.zeros(T)), a930["solar"]),
            "wind": (k.get("wind", np.zeros(T)), a930["wind"]),
            "storage_li_ion_vs_OTH": (li_net, a930["oth"]),
            "storage_alltech_vs_OTH": (st_all, a930["oth"]),
            "other_geo_bio_vs_unmapped": (other_model, ac["_series"]["unmapped"]),
            "oil": (k.get("oil", np.zeros(T)), a930["oil"]),
            "coal": (k.get("COAL", np.zeros(T)), a930["coal"]),
            "net_import": (k["import"], a930["net_import"]),
        }
        closure = {}
        for h in GAP:
            hh = {}
            for name, (mo, ac_) in rows.items():
                hh[name] = {
                    "model": float(np.nanmean(mo[HOD == h])),
                    "actual": float(np.nanmean(ac_[HOD == h])),
                    "delta": float(np.nanmean((mo - ac_)[HOD == h])),
                }
            for g in GAS_KLASSES:
                mo, ac_ = cems_class_pair(fl, g)
                hh[f"cems_{g}"] = {
                    "model": float(mo[HOD == h].mean()),
                    "actual": float(ac_[HOD == h].mean()),
                    "delta": float((mo - ac_)[HOD == h].mean()),
                }
            hh["model_slack_minus_dump"] = float(
                (mc_["_series"]["slack"] - mc_["_series"]["dump"])[HOD == h].mean()
            )
            hh["ba_residual_930"] = float(np.nanmean(ac["_series"]["resid"][HOD == h]))
            # identity check: sum of supply deltas == delta demand + residual terms
            supply = [
                "gas_930_basis",
                "nuclear",
                "hydro_plus_ps_vs_WAT",
                "solar",
                "wind",
                "storage_li_ion_vs_OTH",
                "other_geo_bio_vs_unmapped",
                "oil",
                "coal",
                "net_import",
            ]
            s_delta = sum(hh[n]["delta"] for n in supply)
            hh["identity"] = {
                "sum_supply_delta": s_delta,
                "delta_demand": hh["demand"]["delta"],
                "closure_gap": s_delta
                - hh["demand"]["delta"]
                + hh["ba_residual_930"]
                - hh["model_slack_minus_dump"],
            }
            closure[str(h)] = hh
        yr["closure"] = closure
        yr["G_CLOSE_model"] = {k_: v for k_, v in mc_.items() if k_ != "_series"}
        yr["G_CLOSE_measured"] = {k_: v for k_, v in ac.items() if k_ != "_series"}
        yr["G_CAT_annual_twh"] = {
            "model": {kk: float(np.nansum(v) / 1e6) for kk, v in k.items()},
            "model_storage": {
                tt: {
                    "dis": float(v["dis"].sum() / 1e6),
                    "chg": float(v["chg"].sum() / 1e6),
                }
                for tt, v in m["storage"].items()
            },
            "model_demand_caiso": float(np.nansum(mc_["_series"]["dem"]) / 1e6),
            "measured": ac["annual_twh"],
            "cems_gas_actual_twh": float(fl["act"].sum() / 1e6),
            "cems_gas_model_twh": float(fl["mod"].sum() / 1e6),
        }
        # the demand-basis gap by hour of day
        dgap = mc_["_series"]["dem"] - a930["demand"]
        yr["demand_gap_by_hod_mw"] = [
            float(np.nanmean(dgap[HOD == h])) for h in range(24)
        ]
        yr["demand_gap_2223_mw"] = hod_mean(dgap)
        yr["cc_err_by_hod_mw"] = [float(cc_e[HOD == h].mean()) for h in range(24)]
        yr["import_gap_by_hod_mw"] = [
            float(np.nanmean(imp_gap[HOD == h])) for h in range(24)
        ]
        yr["li_ion_gap_by_hod_mw"] = [
            float(np.nanmean((li_net - a930["oth"])[HOD == h])) for h in range(24)
        ]
        yr["hydro_ps_gap_by_hod_mw"] = [
            float(
                np.nanmean(
                    (k.get("hydro", np.zeros(T)) + ps_net - a930["hydro"])[HOD == h]
                )
            )
            for h in range(24)
        ]
        yr["unmapped_gap_by_hod_mw"] = [
            float(np.nanmean((other_model - ac["_series"]["unmapped"])[HOD == h]))
            for h in range(24)
        ]

        # ---- D-2 ------------------------------------------------------------
        yr["D2_unit_conduct"] = unit_conduct(fl)
        yr["D2b_offstate_split_POST_REGISTRATION"] = offstate_split(fl)

        # ---- D-4 ------------------------------------------------------------
        e = fl["e"]
        sel = np.isin(HOD, GAP)
        mse = float(np.mean(e**2))
        e0 = e.copy()
        e0[sel] = 0.0
        yr["D4_c4_exposure"] = {
            "fit": fl["fit"],
            "mse_mw2": mse,
            "share_of_mse_at_2223": float(np.sum(e[sel] ** 2) / np.sum(e**2)),
            "nrmse_if_2223_zeroed": float(np.sqrt(np.mean(e0**2)) / fl["act"].mean()),
            "share_of_mse_by_hod": [
                float(np.sum(e[HOD == h] ** 2) / np.sum(e**2)) for h in range(24)
            ],
        }

        if a.import_stack:
            yr["D3_import_stack"] = import_stack(y, m)

        res["years"][str(y)] = yr

    # ---- G-REPRO verdict ----------------------------------------------------
    checks = []
    checks.append(("cc_hod22_2025", repro["2025"]["cc_err_hod22"], PUB_CC_2223_2025[0]))
    checks.append(("cc_hod23_2025", repro["2025"]["cc_err_hod23"], PUB_CC_2223_2025[1]))
    for y in YEARS:
        checks.append(
            (f"import_gap_{y}", repro[str(y)]["import_gap_2223"], PUB_IMPORT_GAP[y])
        )
        checks.append(
            (
                f"storage_gap_{y}",
                repro[str(y)]["storage_allteck_gap_2223"],
                PUB_STORAGE_GAP[y],
            )
        )
    res["gates"]["G_REPRO"] = {
        "tolerance_mw": REPRO_TOL_MW,
        "checks": [
            {
                "name": n,
                "measured": round(v, 1),
                "published": p,
                "diff": round(v - p, 1),
                "pass": abs(v - p) <= REPRO_TOL_MW,
            }
            for n, v, p in checks
        ],
        "c4_fit_reproduced": {str(y): repro[str(y)]["c4_fit"] for y in YEARS},
        "import_gap_on_caiso253_clock_construction": {
            str(y): {
                "measured": round(
                    repro[str(y)]["import_gap_2223_caiso253_construction"], 1
                ),
                "published": PUB_IMPORT_GAP[y],
                "diff": round(
                    repro[str(y)]["import_gap_2223_caiso253_construction"]
                    - PUB_IMPORT_GAP[y],
                    1,
                ),
            }
            for y in YEARS
        },
        "import_klass_min_mw": {
            str(y): repro[str(y)]["import_klass_min_mw"] for y in YEARS
        },
        "pass": all(abs(v - p) <= REPRO_TOL_MW for _, v, p in checks),
    }
    res["gates"]["G_CLOSE_model_pass_all_years"] = all(
        res["years"][str(y)]["G_CLOSE_model"]["pass"] for y in YEARS
    )

    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n")

    # ---- console ---------------------------------------------------------------
    g = res["gates"]["G_REPRO"]
    print(f"G-REPRO: {'PASS' if g['pass'] else 'FAIL'}")
    for c in g["checks"]:
        print(
            f"  {c['name']:18s} measured {c['measured']:9.1f} published {c['published']:9.1f} diff {c['diff']:+7.1f} {'ok' if c['pass'] else 'FAIL'}"
        )
    print(f"  C4 fit reproduced: {g['c4_fit_reproduced']}")
    print(
        f"  import gap on caiso-253's OWN clock construction: {g['import_gap_on_caiso253_clock_construction']}"
    )
    print(
        f"  import klass minimum (export sinks dispatch?): {g['import_klass_min_mw']}"
    )
    for y in YEARS:
        yr = res["years"][str(y)]
        print(f"\n===== {y}")
        gm = yr["G_CLOSE_model"]
        print(
            f"G-CLOSE model: max|resid| {gm['max_abs_residual_mw']:.3f} MW pass={gm['pass']}  non-CAISO zones {gm['non_caiso_zones']} demand {gm['non_caiso_demand_twh']:.3f} TWh"
        )
        ga = yr["G_CLOSE_measured"]
        print(
            f"G-CLOSE 930: BA residual mean {ga['ba_residual_mean_mw']:+.0f} MW (at 22-23 {ga['ba_residual_mean_at_2223_mw']:+.0f}); unmapped mean {ga['unmapped_mean_mw']:+.0f} MW ({ga['unmapped_twh']:.2f} TWh, cv over hod {ga['unmapped_cv_over_hod']}); GEO NaN hours {ga['geo_nan_hours']}"
        )
        print(f"  unmapped by hod: {[round(x) for x in ga['unmapped_by_hod_mw']]}")
        print(
            f"  annual TWh measured: { {k_: round(v, 2) for k_, v in ga['annual_twh'].items()} }"
        )
        print(
            f"  annual TWh model:    { {k_: round(v, 2) for k_, v in yr['G_CAT_annual_twh']['model'].items()} } demand {yr['G_CAT_annual_twh']['model_demand_caiso']:.2f}"
        )
        print(f"  demand gap by hod: {[round(x) for x in yr['demand_gap_by_hod_mw']]}")
        for h in GAP:
            hh = yr["closure"][str(h)]
            print(f"  --- hod {h}: (model / actual / delta MW)")
            for name, v in hh.items():
                if isinstance(v, dict) and "delta" in v:
                    print(
                        f"     {name:28s} {v['model']:9.0f} {v['actual']:9.0f} {v['delta']:+9.0f}"
                    )
            print(
                f"     slack-dump {hh['model_slack_minus_dump']:+.1f}  930 resid {hh['ba_residual_930']:+.0f}  identity: sum supply delta {hh['identity']['sum_supply_delta']:+.0f} vs delta demand {hh['identity']['delta_demand']:+.0f} -> closure gap {hh['identity']['closure_gap']:+.0f}"
            )
        d2 = yr["D2_unit_conduct"]
        print(
            f"D-2: CC plants {d2['n_cc_plants']} over-run {d2['over_run_mean_mw_at_2223']:+.0f} MW; positive share by ACTUAL state {d2['positive_share_by_act_state']}; net share {d2['net_share_by_act_state']}"
        )
        print(
            f"     plant-hours by state actual {d2['plant_hours_by_state_actual']} model {d2['plant_hours_by_state_model']}; shutdowns 21->23 actual {d2['shutdowns_21_23_actual']} model {d2['shutdowns_21_23_model']}"
        )
        for p in d2["top_plants_by_err"][:8]:
            print(
                f"     {p['code']:>6} {str(p['name'])[:28]:28s} {p['zone']:9s} npl {p['npl']:6.0f} err {p['err_2223_mean_mw']:+7.0f} act cf {p['act_2223_mean_cf']:.2f} mod cf {p['mod_2223_mean_cf']:.2f} act off {p['act_off_share_2223']:.2f} mod off {p['mod_off_share_2223']:.2f} sd a/m {p['shutdowns_21_23_act']}/{p['shutdowns_21_23_mod']}"
            )
        d2b = yr["D2b_offstate_split_POST_REGISTRATION"]
        print(
            f"D-2b: OFF plant-hours whole-day-off {d2b['whole_day_off_plant_hours']} cycled {d2b['cycled_plant_hours']}; over-run MW from whole-day-off days {d2b['over_run_mw_from_whole_day_off_days']:.0f} from cycled days {d2b['over_run_mw_from_cycled_days']:.0f}"
        )
        for p in d2b["plants"][:6]:
            print(
                f"     {p['code']:>6} {str(p['name'])[:28]:28s} npl {p['npl']:6.0f} whole-day-off days act/mod {p['whole_day_off_days_actual']}/{p['whole_day_off_days_model']}  MW from whole-day-off {p['over_run_mw_from_whole_day_off']:.0f} cycled {p['over_run_mw_from_cycled']:.0f}"
            )
        d4 = yr["D4_c4_exposure"]
        print(
            f"D-4: C4 fit {d4['fit']}; share of MSE at 22-23 {d4['share_of_mse_at_2223']:.3f}; NRMSE if zeroed {d4['nrmse_if_2223_zeroed']:.3f}"
        )
        if "D3_import_stack" in yr:
            d3 = yr["D3_import_stack"]
            print(
                f"D-3: WECC rows {d3['n_wecc_rows']}; committed import 22-23 {d3['committed_import_2223_mean_mw']:.0f} vs sum cap {d3['sum_cap_2223_mean_mw']:.0f} (ratio {d3['import_over_cap_2223']}); floor {d3['sum_floor_2223_mean_mw']:.0f}; priced-out headroom {d3['priced_out_headroom_2223_mean_mw']:.0f} MW; within-cap every hour {d3['committed_import_within_cap_every_hour']} (max over {d3['max_import_minus_cap_mw']:.1f}); fallback lines {d3['rebuild_stderr_fallback_lines']}"
            )
            for uid, r in d3["rows"].items():
                print(
                    f"     {uid:36s} pmax {r['pmax']:7.0f} cap22-23 {r['cap_2223_mean_mw']:7.0f} floor {r['floor_2223_mean_mw']:6.0f} offer {r['offer_2223_mean']:7.1f} dual {r['node_dual_2223_mean']} po-share {r['priced_out_share_2223']:.2f} po-headroom {r['priced_out_headroom_2223_mean_mw']:.0f}"
                )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
