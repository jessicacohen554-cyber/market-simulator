"""nyiso-196 STEP 1-3 (NO LP) — decompose the keeper's ``CC_REGULAR`` over-run
into online-hours / loading / netted-under buckets per plant, and overlay the
ONE measured input the buckets point at: the unit-outage availability the LP
was actually given versus the availability the committed extract states.

Everything here reads committed artifacts only (rule 29 ``[R-SCREEN]`` step 0;
control = the keeper's committed bundle, rule 29(b) form 4):

* the keeper's dashboard payload (``frontend/data/backcast/runs/<id>.js``) for
  every plant's model hourly MW (decoded exactly as ``legitimacy_diagnostics``
  and the nyiso-194/195 probes decode it) and the per-year bench part for the
  plant's CAMPD hourly series on the SAME plant/group split;
* ``hourly/system_<yr>.parquet`` (zonal price) and
  ``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`` (measured RT
  system price) for the price-regime axis;
* the keeper's ``legitimacy_diagnostics.json`` D-4 unit-conduct rows (the
  commitment bridge's per-plant binding hours);
* the committed ``-perunitmerit-`` unit-outage extract, accumulated two ways:
  exactly as ``outages.unit_outage_derate_factors`` accumulates it for the LP
  (numerator = the extract's ``unit_capacity_mw``, denominator = the fleet's
  net-summer bin sum), and on the extract's OWN capacity basis (numerator and
  denominator both from the extract — ``unit_pct_of_plant`` for a
  single-group facility).

Buckets, per plant-hour (``m`` model MW, ``c`` measured MW, ``on`` = > 1 % of
nameplate + 1 MW):

  (a) model on, meter off            -> Σ m            (online-hours excess)
  (b+) both on, model above meter    -> Σ (m - c)      (loading excess)
  (b-) both on, model below meter    -> Σ (c - m)      (loading deficit)
  (c) meter on, model off            -> Σ c            (netted under-run)

so that ``a + b+ - b- - c == model annual - measured annual`` by identity.
Each bucket is split by month, hour-of-day, and model-zone / measured-system
price quartile, per plant and for the class, 2023 / 2024 / 2025.

Nothing here is gated on any residual; the output is a measurement. Writes
``results/calibration/_nyiso196_cc_overrun_decomp.json``.

Usage::

    python scripts/probes/nyiso196_cc_overrun_decomp.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import base64
import csv
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))
from market_sim.data.outages import (  # noqa: E402
    UNIT_OUTAGE_MIN_DAYS,
    _iso_plant_capacity,
    _has_hour_grain,
    outage_hour_mask,
    unit_outage_csv_for_iso,
    unit_outage_derate_factors,
    unit_outage_event_window,
)
from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402

KEEPER_ID = "2026-09-05-nyiso-192-astoria-panel"
BUNDLE = ROOT / "results/calibration/nyiso192_astoria_panel"
PHASE0_195 = ROOT / "results/calibration/_nyiso195_econ_basis_phase0.json"
CLASS = "CC_REGULAR"
T = 8760
MONTH_STARTS = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
GAS_FAMILY = ("CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP", "CT_CHP", "CT_PEAKER")
# NYISO scheduled-interchange interfaces in the measured tie-flow file (imports
# positive into NYCA on the posting's sign convention).
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
    """Decode a payload/bench hourly series, annual-rescaled (the LD decode)."""
    raw_b64 = entry.get(key_bytes)
    if not raw_b64:
        return None
    raw = _dec(raw_b64)[:T]
    if raw.size < T:
        raw = np.pad(raw, (0, T - raw.size))
    ann = entry.get(key_ann)
    if ann not in (None, "", "None") and raw.sum() > 0:
        return raw * (float(ann) * 1e6 / raw.sum())
    if npl > 0:
        return raw * npl / 100.0
    return None


def _month_of_hour() -> np.ndarray:
    m = np.zeros(T, dtype=int)
    for i in range(12):
        m[MONTH_STARTS[i] : MONTH_STARTS[i + 1]] = i + 1
    return m


def _quartile(x: np.ndarray) -> np.ndarray:
    q = np.percentile(x, [25, 50, 75])
    return np.digitize(x, q) + 1  # 1..4


def _by(mask_energy: np.ndarray, groups: np.ndarray, keys) -> dict:
    return {str(k): round(float(mask_energy[groups == k].sum()) / 1e3, 1) for k in keys}


def extract_windows(csv_path: Path):
    """Per-(facility, group) unit windows + the two capacity bases per row."""
    rows = list(csv.DictReader(open(csv_path)))
    groups_at = defaultdict(set)
    units_cap = defaultdict(dict)
    for r in rows:
        f = int(r["facility_id"])
        groups_at[f].add(r["plant_group"])
        units_cap[(f, r["plant_group"])][r["unit_id"]] = float(r["unit_capacity_mw"])
    return rows, groups_at, units_cap


def same_basis_availability(
    rows, groups_at, units_cap, plant: int, group: str, year: int
) -> tuple[np.ndarray, dict]:
    """Availability from the extract on its OWN capacity basis.

    removed share = ``unit_capacity_mw / basis``, ``basis`` = the row's
    ``plant_capacity_mw`` when the facility carries one model group in the
    extract (then it is exactly ``unit_pct_of_plant``), else the sum of the
    group's distinct unit capacities in the extract. Same >= 5-day filter,
    same window reconstruction and clock as the LP accumulator.
    """
    df = pd.DataFrame(
        [
            r
            for r in rows
            if int(r["facility_id"]) == plant and r["plant_group"] == group
        ]
    )
    out = np.zeros(T)
    info = {"rows": 0, "single_group": len(groups_at[plant]) == 1, "basis_mw": None}
    if df.empty:
        return np.ones(T), info
    for c in ("unit_capacity_mw", "plant_capacity_mw", "duration_days"):
        df[c] = pd.to_numeric(df[c])
    df = df[df.duration_days >= UNIT_OUTAGE_MIN_DAYS]
    has_hours = _has_hour_grain(df)
    for r in df.itertuples(index=False):
        basis = (
            float(r.plant_capacity_mw)
            if info["single_group"]
            else float(sum(units_cap[(plant, group)].values()))
        )
        info["basis_mw"] = basis
        w0, w1 = unit_outage_event_window(r, has_hours)
        mask = outage_hour_mask(w0, w1, year, T)
        if not mask.any():
            continue
        out[mask] += float(r.unit_capacity_mw) / basis
        info["rows"] += 1
    return np.clip(1.0 - out, 0.0, 1.0), info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    a = ap.parse_args()
    run = decode_run_js(
        (ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    )
    ld = json.loads((BUNDLE / "legitimacy_diagnostics.json").read_text())
    d4 = [
        r
        for r in ld["diagnostics"]["D4"]["rows"]
        if r.get("check") == "unit-conduct"
        and "nyiso_gas_commitment_bridge" in str(r.get("floor"))
    ]
    p0 = json.loads(PHASE0_195.read_text())
    pmax_lp = {int(r["plant"]): float(r["pmax"]) for r in p0["plants"]}
    cap_fleet = _iso_plant_capacity("NYISO")
    csv_path = unit_outage_csv_for_iso("NYISO", False, True, True)
    rows, groups_at, units_cap = extract_windows(csv_path)
    act = pd.read_parquet(
        ROOT / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
    )
    month = _month_of_hour()
    hod = np.arange(T) % 24

    out = {
        "session": "nyiso-196",
        "status": "STEP 1-3 — NO LP, MEASUREMENT ONLY",
        "keeper": KEEPER_ID,
        "extract": str(csv_path.relative_to(ROOT)),
        "years": {},
    }
    for yr in a.years:
        ypay = run["years"][str(yr)]
        bench = json.load(
            gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{yr}.json.gz")
        )["bench"]
        bplants = bench["plants"]
        sysp = pd.read_parquet(BUNDLE / "hourly" / f"system_{yr}.parquet")
        lmp = sysp.pivot(index="hour", columns="zone", values="price").iloc[:T]
        zq = {z: _quartile(lmp[z].to_numpy()) for z in lmp.columns}
        rt = act[act.year == yr].sort_values("hour").rt.to_numpy()[:T]
        rtq = _quartile(rt) if rt.size == T else None
        ufac = unit_outage_derate_factors(
            yr, iso="NYISO", per_unit_crosswalk=True, merit_order_guard=True
        )
        cls_hourly = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{yr}.parquet")
        cls_piv = cls_hourly.pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum"
        ).iloc[:T]

        # ---------------- per-plant buckets -------------------------------------------
        plants = []
        cls_tot = defaultdict(float)
        zone_excess_mask: dict[str, np.ndarray] = {}
        zone_cc_delta: dict[str, np.ndarray] = {}
        series_by_key: dict[str, tuple[str, str, np.ndarray, np.ndarray]] = {}
        for key, ent in ypay["plants"].items():
            b = bplants.get(key)
            if not b:
                continue
            group = b.get("group")
            zone = b.get("zone")
            npl = float(b.get("npl") or 0.0)
            m = _series(ent, "m", "m_ann", npl)
            c = _series(b, "campd", "c_ann", npl)
            if m is None or c is None:
                continue
            series_by_key[key] = (group, zone, m, c)
        for key, (group, zone, m, c) in series_by_key.items():
            if group != CLASS:
                continue
            pcode = int(key.split(":")[0])
            b = bplants[key]
            npl = float(b.get("npl") or 0.0)
            thr = 0.01 * npl + 1.0
            on_m, on_c = m > thr, c > thr
            A = on_m & ~on_c
            Bp = on_m & on_c & (m > c)
            Bm = on_m & on_c & (m < c)
            C = ~on_m & on_c
            e_a = np.where(A, m, 0.0)
            e_bp = np.where(Bp, m - c, 0.0)
            e_bm = np.where(Bm, c - m, 0.0)
            e_c = np.where(C, c, 0.0)
            net = m.sum() - c.sum()
            zq_p = zq.get(zone)
            # availability: LP-applied vs extract-own-basis
            A_L = ufac.get((pcode, CLASS))
            A_L = np.ones(T) if A_L is None else np.asarray(A_L)[:T]
            A_S, sinfo = same_basis_availability(
                rows, groups_at, units_cap, pcode, CLASS, yr
            )
            plp = pmax_lp.get(pcode) or float(cap_fleet.get((pcode, CLASS), npl))
            over_avail = A_L > A_S + 1e-9
            contra = np.where(over_avail, np.clip(m - A_S * plp, 0.0, None), 0.0)
            dark = (A_S <= 1e-9) & on_m
            rec = {
                "key": key,
                "plant": pcode,
                "name": b.get("name"),
                "zone": zone,
                "npl_mw": npl,
                "pmax_lp_mw": round(plp, 1),
                "cap_fleet_denominator_mw": round(
                    float(cap_fleet.get((pcode, CLASS), 0.0)), 1
                ),
                "model_gwh": round(m.sum() / 1e3, 1),
                "campd_gwh": round(c.sum() / 1e3, 1),
                "net_gwh": round(net / 1e3, 1),
                "online_h_model": int(on_m.sum()),
                "online_h_campd": int(on_c.sum()),
                "buckets_gwh": {
                    "a_model_on_meter_off": round(e_a.sum() / 1e3, 1),
                    "b_plus_loading_excess": round(e_bp.sum() / 1e3, 1),
                    "b_minus_loading_deficit": round(e_bm.sum() / 1e3, 1),
                    "c_meter_on_model_off": round(e_c.sum() / 1e3, 1),
                    "identity_check": round(
                        (e_a.sum() + e_bp.sum() - e_bm.sum() - e_c.sum() - net) / 1e3, 3
                    ),
                },
                "bucket_hours": {
                    "a": int(A.sum()),
                    "b_plus": int(Bp.sum()),
                    "b_minus": int(Bm.sum()),
                    "c": int(C.sum()),
                },
                "a_by_month_gwh": _by(e_a, month, range(1, 13)),
                "a_by_hod_gwh": _by(e_a, hod, range(24)),
                "b_plus_by_month_gwh": _by(e_bp, month, range(1, 13)),
                "a_by_zone_lmp_quartile_gwh": _by(e_a, zq_p, range(1, 5))
                if zq_p is not None
                else None,
                "b_plus_by_zone_lmp_quartile_gwh": _by(e_bp, zq_p, range(1, 5))
                if zq_p is not None
                else None,
                "a_by_actual_rt_quartile_gwh": _by(e_a, rtq, range(1, 5))
                if rtq is not None
                else None,
                "bridge_binding_h_d4": next(
                    (
                        int(r["binding_hours"])
                        for r in d4
                        if int(r["year"]) == yr and str(r["plant"]) == str(pcode)
                    ),
                    0,
                ),
                "availability": {
                    "extract_rows_ge5d": sinfo["rows"],
                    "single_group_facility": sinfo["single_group"],
                    "extract_basis_mw": sinfo["basis_mw"],
                    "mean_lp_applied": round(float(A_L.mean()), 4),
                    "mean_extract_own_basis": round(float(A_S.mean()), 4),
                    "min_lp_applied": round(float(A_L.min()), 3),
                    "min_extract_own_basis": round(float(A_S.min()), 3),
                    "hours_lp_over_avails": int(over_avail.sum()),
                    "extra_available_gwh_lp_minus_extract": round(
                        float(((A_L - A_S) * plp).sum()) / 1e3, 1
                    ),
                    "model_energy_above_extract_availability_gwh": round(
                        contra.sum() / 1e3, 1
                    ),
                    "dark_window_hours_model_on": int(dark.sum()),
                    "dark_window_model_gwh": round(float(m[dark].sum()) / 1e3, 1),
                    "a_bucket_gwh_in_over_avail_hours": round(
                        float(e_a[over_avail].sum()) / 1e3, 1
                    ),
                    "b_plus_gwh_in_over_avail_hours": round(
                        float(e_bp[over_avail].sum()) / 1e3, 1
                    ),
                    "campd_gwh_in_over_avail_hours": round(
                        float(c[over_avail].sum()) / 1e3, 1
                    ),
                    "model_gwh_in_over_avail_hours": round(
                        float(m[over_avail].sum()) / 1e3, 1
                    ),
                },
            }
            plants.append(rec)
            for k_, v_ in (
                ("a", e_a.sum()),
                ("b_plus", e_bp.sum()),
                ("b_minus", e_bm.sum()),
                ("c", e_c.sum()),
                ("net", net),
                ("model", m.sum()),
                ("campd", c.sum()),
            ):
                cls_tot[k_] += float(v_)
            cls_tot["extra_avail"] += float(((A_L - A_S) * plp).sum())
            cls_tot["contra"] += float(contra.sum())
            cls_tot["online_h_model"] += int(on_m.sum())
            cls_tot["online_h_campd"] += int(on_c.sum())
            if zone:
                zone_cc_delta[zone] = zone_cc_delta.get(zone, np.zeros(T)) + (m - c)
        plants.sort(key=lambda r: -abs(r["net_gwh"]))

        # ---------------- zonal displacement in the class's excess hours ---------------
        disp = {}
        for zone, dcc in zone_cc_delta.items():
            ex = dcc > 0.0
            zone_excess_mask[zone] = ex
            row = {
                "excess_hours": int(ex.sum()),
                "cc_regular_excess_gwh_in_those_hours": round(
                    float(dcc[ex].sum()) / 1e3, 1
                ),
                "other_classes_model_minus_meter_gwh": {},
                "other_classes_annual_model_minus_meter_gwh": {},
            }
            for g in ("CC_CHP", "ST_GAS", "ST_CHP", "CT_CHP", "CT_PEAKER"):
                tot_ex = 0.0
                tot_ann = 0.0
                for key, (group, z, m, c) in series_by_key.items():
                    if group == g and z == zone:
                        tot_ex += float((m - c)[ex].sum())
                        tot_ann += float((m - c).sum())
                row["other_classes_model_minus_meter_gwh"][g] = round(tot_ex / 1e3, 1)
                row["other_classes_annual_model_minus_meter_gwh"][g] = round(
                    tot_ann / 1e3, 1
                )
            disp[zone] = row
        # imports: model class vs measured scheduled interchange (ISO total)
        imp_file = (
            ROOT
            / f"data/raw/NYISO/interface-flows/NYISO_interface_flows_hourly_{yr}.csv.gz"
        )
        imports = None
        if imp_file.exists() and "import" in cls_piv.columns:
            f = pd.read_csv(imp_file)
            f = f[f.interface.isin(SCHED_INTERFACES)]
            f["t"] = pd.to_datetime(f.interval_start_local)
            f = f[~((f.t.dt.month == 2) & (f.t.dt.day == 29))]
            f["hoy"] = (
                f.t.dt.dayofyear - 1 - ((f.t.dt.month > 2) & (yr % 4 == 0)).astype(int)
            ) * 24 + f.t.dt.hour
            meas = f.groupby("hoy").flow_mw.sum().reindex(range(T)).ffill().to_numpy()
            mod = cls_piv["import"].to_numpy()
            imports = {
                "measured_sched_import_twh": round(float(meas.sum()) / 1e6, 3),
                "model_import_class_twh": round(float(mod.sum()) / 1e6, 3),
                "sign_note": "measured = sum of SCH-* interface flows as posted; positive into NYCA",
                "model_minus_measured_in_zone_excess_hours_gwh": {
                    z: round(float((mod - meas)[ex].sum()) / 1e3, 1)
                    for z, ex in zone_excess_mask.items()
                },
            }
        out["years"][str(yr)] = {
            "class": {
                "model_twh": round(cls_tot["model"] / 1e6, 3),
                "campd_twh": round(cls_tot["campd"] / 1e6, 3),
                "net_twh": round(cls_tot["net"] / 1e6, 3),
                "a_model_on_meter_off_twh": round(cls_tot["a"] / 1e6, 3),
                "b_plus_loading_excess_twh": round(cls_tot["b_plus"] / 1e6, 3),
                "b_minus_loading_deficit_twh": round(cls_tot["b_minus"] / 1e6, 3),
                "c_meter_on_model_off_twh": round(cls_tot["c"] / 1e6, 3),
                "online_plant_h_model": int(cls_tot["online_h_model"]),
                "online_plant_h_campd": int(cls_tot["online_h_campd"]),
                "extra_available_twh_lp_minus_extract": round(
                    cls_tot["extra_avail"] / 1e6, 3
                ),
                "model_energy_above_extract_availability_twh": round(
                    cls_tot["contra"] / 1e6, 3
                ),
                "payload_gmModel_cc_regular_twh": ypay["gmModel"].get(CLASS),
            },
            "plants": plants,
            "zonal_displacement": disp,
            "imports": imports,
        }
    dst = ROOT / "results/calibration/_nyiso196_cc_overrun_decomp.json"
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
    # ---- print ---------------------------------------------------------------------
    for yr, y in out["years"].items():
        c = y["class"]
        print(
            f"\n=== {yr} CC_REGULAR class: model {c['model_twh']} vs campd {c['campd_twh']} TWh (net {c['net_twh']:+.3f}); online plant-h {c['online_plant_h_model']} vs {c['online_plant_h_campd']}"
        )
        print(
            f"    a(on/off) {c['a_model_on_meter_off_twh']:+.3f}  b+(loading) {c['b_plus_loading_excess_twh']:+.3f}  b-(deficit) -{c['b_minus_loading_deficit_twh']:.3f}  c(off/on) -{c['c_meter_on_model_off_twh']:.3f}"
        )
        print(
            f"    availability: LP-applied minus extract-own-basis = {c['extra_available_twh_lp_minus_extract']:+.3f} TWh available; model energy above the extract's availability {c['model_energy_above_extract_availability_twh']:.3f} TWh"
        )
        print(
            f"{'plant':>6} {'zone':<14} {'model':>7} {'campd':>7} {'net':>7} | {'a':>6} {'b+':>6} {'b-':>6} {'c':>6} | {'onM':>5} {'onC':>5} {'brdg':>5} | {'A_lp':>5} {'A_ex':>5} {'xAv':>7} {'contra':>7} {'darkH':>5}"
        )
        for r in y["plants"][:14]:
            bk, av = r["buckets_gwh"], r["availability"]
            print(
                f"{r['plant']:>6} {r['zone']:<14} {r['model_gwh']:7.0f} {r['campd_gwh']:7.0f} {r['net_gwh']:+7.0f} | {bk['a_model_on_meter_off']:6.0f} {bk['b_plus_loading_excess']:6.0f} {bk['b_minus_loading_deficit']:6.0f} {bk['c_meter_on_model_off']:6.0f} | {r['online_h_model']:5d} {r['online_h_campd']:5d} {r['bridge_binding_h_d4']:5d} | {av['mean_lp_applied']:5.3f} {av['mean_extract_own_basis']:5.3f} {av['extra_available_gwh_lp_minus_extract']:+7.0f} {av['model_energy_above_extract_availability_gwh']:7.0f} {av['dark_window_hours_model_on']:5d}"
            )
        for z, d in y["zonal_displacement"].items():
            print(
                f"    zone {z}: CC_REGULAR excess {d['cc_regular_excess_gwh_in_those_hours']} GWh over {d['excess_hours']} h; same-zone model-meter in those hours {d['other_classes_model_minus_meter_gwh']}; annual {d['other_classes_annual_model_minus_meter_gwh']}"
            )
        if y["imports"]:
            print(f"    imports: {y['imports']}")
    print(f"\nwrote {dst.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
