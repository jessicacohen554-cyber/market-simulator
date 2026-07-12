"""ERCOT-61 binding-hour ST_GAS mask analysis (no LP solve — reads a bundle).

The decision input for the binding-regime ST_GAS lane (ERCOT-58 §5 /
ERCOT-60 §7.3): over the top-30 % net-load hours, decompose the keeper's
ST_GAS dispatch into

* MWh sitting ON the ``st_netload_drag`` min-gen floor (the D-2 at-floor
  convention: ``min_gen > 1 MW & P <= min_gen*1.02 + 1``, mechanism id 6) —
  if the binding-hour excess lives here, the defect is the hinge's
  high-net-load extrapolation (the hinge was derived from OVERNIGHT CF vs
  net-load, ``docs/ercot-st-gas-netload-drag-2026-06.md``, but applies at
  ALL hours);
* MWh dispatched economically ABOVE the floor — the defect is then the
  ST_GAS offer curve (the keeper's econ_high −0.35 / peak −1.0 markdowns);
* MWh on units the drag never touches (peaker-class plants, ``_peak``
  tranches, other mechanisms).

Also compares model vs CAMPD measured per class (ST_GAS + the CT_PEAKER
−0.6 GW counterpart) on the same measured machinery ERCOT-58 §4 used
(``derive_ercot_rtolcap_forward._net_load`` / ``_class_hourly``), and
evaluates the hinge line against the MEASURED binding-hour CF split
overnight (23–05h, the hinge's own evidence window) vs other hours.

Usage::

    python scripts/probes/_ercot61_stgas_binding_mask.py \
        [--bundle ercot61_stgas_drag_2023] [--year 2023]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from derive_ercot_rtolcap_forward import _class_hourly, _net_load  # noqa: E402

from market_sim.data.floor_mechanisms import (  # noqa: E402
    MECH_NAMES,
    MECH_ST_NETLOAD_DRAG,
)

# D-2 at-floor convention (scripts/legitimacy_diagnostics.py).
FLOOR_MIN_MW = 1.0
REL_TOL = 0.02

# The hinge (ScenarioConfig defaults; the keeper carries no overrides).
SLOPE, INTERCEPT, CAP = 0.00906, -0.1376, 0.34
OVERNIGHT_HOD = (23, 0, 1, 2, 3, 4, 5)  # the hinge's own evidence window


def load_unit_matrix(disp: pd.DataFrame, unit_ids: np.ndarray, hours: int):
    """Return (n_units, T) dispatch MW aligned to the floors-npz unit order."""
    sub = disp[disp["unit_id"].isin(set(unit_ids.tolist()))]
    piv = sub.pivot_table(index="unit_id", columns="hour", values="mw", observed=True)
    piv = piv.reindex(index=list(unit_ids), columns=range(hours), fill_value=0.0)
    return piv.to_numpy(dtype=float)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="ercot61_stgas_drag_2023")
    ap.add_argument("--year", type=int, default=2023)
    args = ap.parse_args()

    bundle = REPO / "results" / "calibration" / args.bundle
    year = args.year

    fl = np.load(bundle / "floors" / f"{year}_P1.npz", allow_pickle=False)
    min_gen = fl["min_gen"].astype(float)  # (n, T)
    mech = fl["mechanism"]  # (n, T) int8
    unit_ids = fl["unit_ids"]
    pgroup = fl["plant_group"]
    hours = min_gen.shape[1]

    disp = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet",
        columns=["pass", "unit_id", "klass", "hour", "mw"],
    )
    disp = disp[disp["pass"] == "P1"]

    nl = _net_load(year)[:hours]
    bind = nl >= np.percentile(nl, 70.0)
    n_bind = int(bind.sum())

    # ---- model per-class binding-hour means (all units of the class) --------
    kl = (
        disp.groupby(["klass", "hour"], observed=True)["mw"]
        .sum()
        .unstack(fill_value=0.0)
    )
    kl = kl.reindex(columns=range(hours), fill_value=0.0)

    # ---- measured (CAMPD, export-basis CHP — the ERCOT-58 §4 basis) ---------
    _, _, class_cap, _, online_gross = _class_hourly(year, chp_export_basis=True)

    print(f"== ERCOT-61 binding-hour mask — {args.bundle}, {year} ==")
    print(f"net-load p70 = {np.percentile(nl, 70.0):,.0f} MW; {n_bind} binding hours")
    print("\n-- model vs CAMPD gross, binding-hour mean MW (ERCOT-58 §4 repro) --")
    for cls in ("COAL", "CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS"):
        model_rows = [
            c for c in kl.index if (c.startswith("COAL") if cls == "COAL" else c == cls)
        ]
        m = (
            kl.loc[model_rows].sum(axis=0).to_numpy()[:hours]
            if model_rows
            else np.zeros(hours)
        )
        meas = online_gross.get(cls, np.zeros(hours))[:hours]
        print(
            f"  {cls:<11} model {m[bind].mean():8,.0f}   CAMPD {meas[bind].mean():8,.0f}"
            f"   diff {m[bind].mean() - meas[bind].mean():+8,.0f}"
        )

    # ---- ST_GAS decomposition on the floors basis ---------------------------
    st_rows = np.where(pgroup == "ST_GAS")[0]
    st_units = unit_ids[st_rows]
    P = load_unit_matrix(disp, st_units, hours)  # (n_st, T)
    mg = min_gen[st_rows]
    mk = mech[st_rows]

    dragged = mk == MECH_ST_NETLOAD_DRAG
    at_floor = (mg > FLOOR_MIN_MW) & (P <= mg * (1.0 + REL_TOL) + FLOOR_MIN_MW)
    on_drag_floor = dragged & at_floor
    above_floor = dragged & ~at_floor

    tot = P.sum(axis=0)  # class MW per hour (floors basis: all ST_GAS pgroup rows)
    on_mw = np.where(on_drag_floor, P, 0.0).sum(axis=0)
    above_excess = np.where(above_floor, P - mg, 0.0).sum(axis=0)
    above_base = np.where(above_floor, mg, 0.0).sum(axis=0)
    undragged_mw = np.where(~dragged, P, 0.0).sum(axis=0)

    def s(x, m):  # mean MW over mask
        return float(x[m].mean())

    print("\n-- ST_GAS (plant_group rows) decomposition, mean MW --")
    hdr = f"{'':<34}{'binding':>10}{'non-bind':>10}{'all':>10}"
    print(hdr)
    for label, arr in (
        ("total dispatch", tot),
        ("ON drag floor (P≈min_gen, mech=6)", on_mw),
        ("drag-raised, floor part", above_base),
        ("drag-raised, economic excess", above_excess),
        ("not drag-raised (other/none)", undragged_mw),
    ):
        print(
            f"  {label:<32}{s(arr, bind):>10,.0f}{s(arr, ~bind):>10,.0f}{arr.mean():>10,.0f}"
        )

    ann_forced = np.where(on_drag_floor, P, 0.0).sum() / 1e6
    print(
        f"\n  annual ON-drag-floor energy: {ann_forced:.2f} TWh "
        f"(keeper D-2 st_netload_drag 2023: 4.96 TWh)"
    )

    # what other mechanisms floor ST_GAS rows (rule 19 reconciliation input)
    ids, counts = np.unique(mk[mk != 0], return_counts=True)
    print(
        "  mechanisms on ST_GAS unit-hours:",
        {MECH_NAMES.get(int(i), str(i)): int(c) for i, c in zip(ids, counts)},
    )

    # ---- hinge-line vs measured CF, binding hours ---------------------------
    st_cap_meas = class_cap.get("ST_GAS", np.nan)
    gross = online_gross.get("ST_GAS", np.zeros(hours))[:hours]
    floor_line = np.clip(SLOPE * nl / 1000.0 + INTERCEPT, 0.0, CAP)
    hod = np.arange(hours) % 24
    overnight = np.isin(hod, OVERNIGHT_HOD)

    print(f"\n-- hinge line vs measured CF (CAMPD ST_GAS cap {st_cap_meas:,.0f} MW) --")
    for label, m in (
        ("binding & overnight", bind & overnight),
        ("binding & day/evening", bind & ~overnight),
        ("non-binding & overnight", ~bind & overnight),
    ):
        if not m.any():
            continue
        cf_meas = gross[m].mean() / st_cap_meas
        fl_mean = floor_line[m].mean()
        print(
            f"  {label:<24} hours {int(m.sum()):>5}   measured CF {cf_meas:5.3f}   "
            f"hinge floor-frac {fl_mean:5.3f}   model CF {tot[m].mean() / st_cap_meas:5.3f}"
        )

    # hod profile at binding hours: on-floor vs measured
    print(
        "\n-- binding hours by hour-of-day: model on-floor / model total / measured --"
    )
    for h in range(24):
        m = bind & (hod == h)
        if not m.any():
            continue
        print(
            f"  hod {h:>2}: n={int(m.sum()):>4}  onfloor {on_mw[m].mean():7,.0f}  "
            f"total {tot[m].mean():7,.0f}  CAMPD {gross[m].mean():7,.0f}"
        )

    # ---- CT_PEAKER attribution ----------------------------------------------
    ct_rows = np.where(pgroup == "CT_PEAKER")[0]
    if len(ct_rows):
        ct_units = unit_ids[ct_rows]
        Pc = load_unit_matrix(disp, ct_units, hours)
        mkc = mech[ct_rows]
        ct_tot = Pc.sum(axis=0)
        ct_meas = online_gross.get("CT_PEAKER", np.zeros(hours))[:hours]
        ids, counts = np.unique(mkc[mkc != 0], return_counts=True)
        print("\n-- CT_PEAKER attribution --")
        print(
            f"  binding-hour mean MW: model {ct_tot[bind].mean():,.0f} vs "
            f"CAMPD {ct_meas[bind].mean():,.0f} (diff {ct_tot[bind].mean() - ct_meas[bind].mean():+,.0f})"
        )
        print(
            "  mechanisms on CT_PEAKER unit-hours:",
            {MECH_NAMES.get(int(i), str(i)): int(c) for i, c in zip(ids, counts)},
        )

    out = {
        "bundle": args.bundle,
        "year": year,
        "n_bind": n_bind,
        "st_gas_binding_model_mw": float(tot[bind].mean()),
        "st_gas_binding_onfloor_mw": float(on_mw[bind].mean()),
        "st_gas_binding_measured_mw": float(gross[bind].mean()),
        "annual_onfloor_twh": float(ann_forced),
    }
    (bundle / "ercot61_mask_summary.json").write_text(json.dumps(out, indent=2))
    print(f"\nsummary -> {bundle / 'ercot61_mask_summary.json'}")


if __name__ == "__main__":
    main()
