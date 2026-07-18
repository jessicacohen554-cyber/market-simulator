"""ERCOT-79 leg 1: the availability/capability-envelope input audit (no LP solve).

Builds the per-class ledger the ERCOT-78 charter names as the successor lane:
on the 58h Jun/Sep-2023 event-afternoon set, compare

  * MODEL available capability   — Σ pmax × availability[g,t] per model plant_group,
    reconstructed byte-faithfully from the keeper meta.json config via
    run_calibration.run_year(fleet_only=True) (the same reconstruction
    scripts/data/derive_ordc_overlay.build_availability uses — no LP re-solve);
  * MODEL dispatch               — the keeper P1 dispatch, grouped by the SAME
    plant_group (mapped unit_id → fleet_arrays.plant_group);
  * MEASURED online envelope     — scripts/data/derive_ercot_rtolcap_forward._class_hourly:
    per class online_cap (summer-derated HSL of running CAMPD units), online_gross
    (their gross output), online_reserve (= online_cap − gross, the measured RTOLCAP
    headroom identity), offline_cap (class total − online).

The ledger names WHERE the ~5-8 GW of measured online room goes missing in the
model on those afternoons (ERCOT-78: model event-time room exhausted vs measured
RTOLCAP 6-9 GW). It is a DIAGNOSTIC — it prints a per-class table and the
system-level room reconciliation; it changes no input and pins nothing to the
measured outcome (rule 14 — no room-pin to RTOLCAP; the measured side is the
INPUT-basis reference, never fed back into a solve).

The set is recomputed from the bundle exactly as _ercot78_summer_anatomy.py:
Jun/Sep hours with model_lw − rt > $over.

Usage::

    uv run python scripts/probes/_ercot79_availability_ledger.py \
        [--bundle _ercot79_keeper_replay] [--year 2023] [--over 25] [--months 6 9]
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(REPO / "src"))

ROOT = REPO / "results" / "calibration"
ACTUAL = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
RESERVES = REPO / "data" / "raw" / "ercot" / "ercot_2023_ordc_reserves_hourly.parquet"

HOURS = 8760

# The measured-envelope derive reclassifies these two registry-OTHER gas STEAM
# plants into ST_GAS for its class accounting (ERCOT-71 shim, see
# derive_ercot_rtolcap_forward._OTHER_GROUP_GAS_STEAM_RECLASS). To compare the
# MODEL per-class capability like-with-like, mirror the same reclass on the
# model grouping so a unit is attributed to the same class on both sides.
_OTHER_GROUP_GAS_STEAM_RECLASS = {3611: "ST_GAS", 3612: "ST_GAS"}


def _model_lw_set(bundle: Path, year: int, over: float, months: list[int]):
    """Recompute the ERCOT-78 over-priced set from the bundle (payload lw basis)."""
    sysq = pd.read_parquet(bundle / "system.parquet")
    sysq = sysq[(sysq["pass"] == "P1") & (sysq["year"] == year)].copy()
    px = sysq.pivot_table(index="hour", columns="zone", values="price")
    dem = sysq.pivot_table(index="hour", columns="zone", values="demand")
    lw = (px * dem).sum(axis=1) / dem.sum(axis=1)
    lw = lw.reindex(range(HOURS)).to_numpy(float)

    act = pd.read_parquet(ACTUAL)
    a = act[act["year"] == year].set_index("hour").reindex(range(HOURS))
    rt = a["rt"].to_numpy(float)

    cal = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
    mo = cal.month.to_numpy()
    over_mask = (lw - rt > over) & np.isin(mo, months)
    return np.flatnonzero(over_mask), lw, rt


def _run_year_kwargs_from_meta(meta: dict, year: int) -> dict:
    """Map meta.json onto run_year kwargs (faithful thermal-availability config).

    Mirrors scripts/replay_keeper.build_kwargs' strictness but targets run_year
    (fleet_only) rather than solve_and_persist: every meta key must map to a
    run_year parameter or be an ignored provenance key. This guarantees the
    reconstructed fleet_arrays.availability is the SAME the LP solved against.
    """
    from run_calibration import run_year

    remap = {
        "commitment_screen_coal": "commitment_screen_coal",
        "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
        "coal_prb_sigmoid_overrides": "prb_overrides",
        "coal_bit_sigmoid_overrides": "bit_overrides",
    }
    params = set(inspect.signature(run_year).parameters)
    kwargs: dict = {}
    for k, v in meta.items():
        key = remap.get(k, k)
        if key == "coal_plant_monthly_pricing":
            if v is False:
                kwargs.setdefault("prb_overrides", {})
                kwargs["prb_overrides"]["coal_plant_monthly_pricing"] = False
            continue
        if key in params:
            kwargs[key] = v
    # These four are passed positionally by _reconstruct_model — drop them from
    # the mapped kwargs so they don't collide.
    for k in ("iso", "hours", "year", "gas_price"):
        kwargs.pop(k, None)
    kwargs["ttc_overrides"] = {}
    kwargs["commitment_enabled"] = False  # availability is pass-independent
    kwargs["fleet_only"] = True
    return kwargs


def _reconstruct_model(meta: dict, year: int):
    """Reconstruct fleet_arrays (fleet_only) → per-plant_group pmax×availability.

    Returns (avail_by_grp, unit_group, storage_power_cap_t, fa) where
    avail_by_grp[grp] is an (HOURS,) MW array of Σ pmax×availability[g,t] over
    units in that group, unit_group maps unit_id → group (for dispatch grouping),
    storage_power_cap_t is (HOURS,) storage MW cap.
    """
    from run_calibration import run_year

    kwargs = _run_year_kwargs_from_meta(meta, year)
    state = run_year(
        year,
        meta["iso"],
        int(meta.get("hours", HOURS)),
        meta["gas_prices"][str(year)],
        **kwargs,
    )
    fa = state["fleet_arrays"]
    pg = (
        np.asarray(fa.plant_group, dtype=object) if fa.plant_group is not None else None
    )
    if pg is None:
        raise SystemExit("fleet_arrays.plant_group is None — cannot group by class")
    # mirror the measured-side ST_GAS reclass for like-with-like attribution
    plant_code = np.asarray(fa.plant_code)
    pg = pg.copy()
    for pc, grp in _OTHER_GROUP_GAS_STEAM_RECLASS.items():
        pg[plant_code == pc] = grp
    avail = fa.pmax[:, None] * fa.availability  # (n_gen, T)
    groups = sorted(set(pg.tolist()))
    avail_by_grp = {g: avail[pg == g].sum(axis=0) for g in groups}
    unit_group = {str(u): g for u, g in zip(fa.unit_ids, pg)}
    cap = np.asarray(state["storage_power_cap"], dtype=float)
    cap_t = (
        cap.sum(axis=0)
        if cap.ndim == 2
        else np.full(int(meta.get("hours", HOURS)), cap.sum())
    )
    return avail_by_grp, unit_group, cap_t, fa


def _model_dispatch_by_group(bundle: Path, year: int, unit_group: dict) -> dict:
    """Model P1 dispatch grouped by the model plant_group (via unit_id map)."""
    disp = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet",
        columns=["unit_id", "klass", "zone", "hour", "mw"],
    )
    disp["grp"] = disp["unit_id"].astype(str).map(unit_group)
    out: dict[str, np.ndarray] = {}
    for grp, sub in disp.groupby("grp", observed=True):
        v = sub.groupby("hour")["mw"].sum().reindex(range(HOURS), fill_value=0.0)
        out[str(grp)] = v.to_numpy(float)
    # also return the storage/renewable klass dispatch for context
    return out, disp


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="_ercot79_keeper_replay")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--over", type=float, default=25.0)
    ap.add_argument("--months", type=int, nargs="+", default=[6, 9])
    args = ap.parse_args()

    bundle = ROOT / args.bundle
    meta = json.loads((bundle / "meta.json").read_text())

    hrs, lw, rt = _model_lw_set(bundle, args.year, args.over, args.months)
    print(
        f"=== ERCOT-79 availability ledger — bundle {args.bundle}, year {args.year} ==="
    )
    print(
        f"set: {len(hrs)} h (model_lw − rt > ${args.over:.0f}, months {args.months}); "
        f"model lw mean ${lw[hrs].mean():,.0f}, actual rt mean ${rt[hrs].mean():,.0f}"
    )

    print("\nreconstructing model fleet (fleet_only, no LP) ...")
    avail_by_grp, unit_group, cap_t, fa = _reconstruct_model(meta, args.year)
    disp_by_grp, disp_raw = _model_dispatch_by_group(bundle, args.year, unit_group)

    print(
        "computing measured CAMPD online envelope (_class_hourly, CHP export basis) ..."
    )
    # chp_export_basis=True scales each CHP plant's cap+gross by its measured
    # grid-export share (1 − chp_btm_pct): CAMPD CEMS measures FULL cogen gross
    # (host + grid) while the model's CHP units/dispatch are grid-export-basis
    # (host netted from demand). Export basis makes the measured CHP envelope
    # model-comparable; the non-CHP classes (COAL/CC_REGULAR/CT_PEAKER/ST_GAS)
    # are unaffected, so the eater-identification is robust regardless.
    from derive_ercot_rtolcap_forward import _class_hourly, RTOLCAP_CLASSES

    online_reserve, offline_cap, class_cap, online_cap, online_gross = _class_hourly(
        args.year, chp_export_basis=True
    )

    # --- per-class ledger on the set (MW means over the set hours) ---
    classes = [
        "COAL",
        "CC_REGULAR",
        "CC_CHP",
        "CT_PEAKER",
        "CT_CHP",
        "ST_GAS",
        "ST_CHP",
    ]
    rows = []
    for c in classes:
        m_avail = avail_by_grp.get(c, np.zeros(HOURS))[hrs].mean()
        m_disp = disp_by_grp.get(c, np.zeros(HOURS))[hrs].mean()
        m_room = m_avail - m_disp
        meas_oncap = online_cap.get(c, np.zeros(HOURS))[hrs].mean()
        meas_ongross = online_gross.get(c, np.zeros(HOURS))[hrs].mean()
        meas_onres = online_reserve.get(c, np.zeros(HOURS))[hrs].mean()
        meas_offcap = offline_cap.get(c, np.zeros(HOURS))[hrs].mean()
        rows.append(
            dict(
                klass=c,
                m_avail=m_avail,
                m_disp=m_disp,
                m_room=m_room,
                meas_oncap=meas_oncap,
                meas_ongross=meas_ongross,
                meas_onres=meas_onres,
                meas_offcap=meas_offcap,
                cap_gap=(meas_oncap + meas_offcap)
                - m_avail,  # measured total − model avail
                disp_gap=m_disp - meas_ongross,  # model runs harder than measured
            )
        )
    df = pd.DataFrame(rows).set_index("klass")
    pd.set_option("display.width", 200, "display.max_columns", 20)
    print("\n--- per-class ledger on the set (MW, mean over set hours) ---")
    print(
        "  m_avail  = model Σ pmax×availability      meas_oncap = measured online HSL (running units)"
    )
    print(
        "  m_disp   = model dispatch                 meas_ongross = measured online gross"
    )
    print(
        "  m_room   = m_avail − m_disp               meas_onres = measured RTOLCAP headroom (oncap−gross)"
    )
    print(
        "  cap_gap  = (meas_oncap+meas_offcap)−m_avail   disp_gap = m_disp − meas_ongross"
    )
    print(df.round(0).to_string())

    # --- system reconciliation: thermal room vs measured RTOLCAP ---
    thermal = [
        "COAL",
        "CC_REGULAR",
        "CC_CHP",
        "CT_PEAKER",
        "CT_CHP",
        "ST_GAS",
        "ST_CHP",
    ]
    m_room_sys = sum(
        avail_by_grp.get(c, np.zeros(HOURS))[hrs]
        - disp_by_grp.get(c, np.zeros(HOURS))[hrs]
        for c in thermal
    )
    meas_onres_sys = sum(
        online_reserve.get(c, np.zeros(HOURS))[hrs] for c in RTOLCAP_CLASSES
    )
    m_avail_sys = sum(avail_by_grp.get(c, np.zeros(HOURS))[hrs] for c in thermal)
    m_disp_sys = sum(disp_by_grp.get(c, np.zeros(HOURS))[hrs] for c in thermal)
    meas_oncap_sys = sum(
        online_cap.get(c, np.zeros(HOURS))[hrs] for c in RTOLCAP_CLASSES
    )
    meas_ongross_sys = sum(
        online_gross.get(c, np.zeros(HOURS))[hrs] for c in RTOLCAP_CLASSES
    )

    print("\n--- system thermal reconciliation on the set (MW mean) ---")
    print(
        f"  MODEL   avail {m_avail_sys.mean():,.0f}  dispatch {m_disp_sys.mean():,.0f}  "
        f"room {m_room_sys.mean():,.0f}"
    )
    print(
        f"  MEASURED online_cap {meas_oncap_sys.mean():,.0f}  online_gross {meas_ongross_sys.mean():,.0f}  "
        f"online_reserve(RTOLCAP-thermal) {meas_onres_sys.mean():,.0f}"
    )
    print(f"  storage power cap (model) {cap_t[hrs].mean():,.0f} MW")
    print(
        f"\n  ROOM GAP (measured RTOLCAP-thermal − model thermal room): "
        f"{meas_onres_sys.mean() - m_room_sys.mean():+,.0f} MW"
    )
    print(
        f"  CAPABILITY GAP (measured online_cap − model avail): "
        f"{meas_oncap_sys.mean() - m_avail_sys.mean():+,.0f} MW"
    )
    print(
        f"  DISPATCH GAP (model dispatch − measured online_gross): "
        f"{m_disp_sys.mean() - meas_ongross_sys.mean():+,.0f} MW"
    )

    # measured RTOLCAP actuals (NP6-905) for reference on the set
    if RESERVES.exists():
        res = pd.read_parquet(RESERVES).set_index("hour").reindex(range(HOURS))
        for col in ("rtolcap", "rtoffcap", "rtorpa"):
            if col in res.columns:
                q = np.nanpercentile(res[col].to_numpy(float)[hrs], [10, 50, 90])
                print(f"  measured {col.upper()} p10/50/90 on set: {q.round(0)}")


if __name__ == "__main__":
    main()
