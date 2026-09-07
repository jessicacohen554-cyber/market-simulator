"""nyiso-212 PHASE 0 (ZERO LP) for the ``cc_summer_derate_reconciled_basis`` arm.

Two on-recipe ``fleet_only`` rebuilds of the keeper
``2026-09-06-nyiso-202-startup-aware`` per year — flag OFF (the keeper recipe;
must be BYTE-IDENTICAL to the pre-change rebuild cached by
``nyiso212_overceiling_decomposition.py``, the G-DRIFT statement for the code
edit) and flag ON — and a diff of the assembled ``FleetArrays.availability``:

* **F-1 footprint** — which LP units move (must be exactly the CC_REGULAR
  tranches of the 15 plants ``cc_capacity_reconcile_NYISO.csv`` lists, and no
  other class), and that ``pmax``, heat rate and every other array are
  identical (the flag touches Jun-Sep availability and nothing else).
* **F-2 identity** — at every moved plant the ON/OFF ratio in Jun-Sep equals
  ``min(1, net_summer / carried) / min(1, net_summer / nameplate)`` to 1e-9,
  and off-summer hours are untouched.
* **F-3 the Cricket Valley ceiling** — the plant's summer statistical factor,
  its summer available energy and the count of summer hours / months in which
  the meter exceeds the ceiling, OFF vs ON (the pre-solve prediction the screen
  gate is written against).

Writes ``results/calibration/_nyiso212_arm_phase0.json``. Run::

    uv run python scripts/probes/nyiso212_arm_phase0.py
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))

import nyiso212_overceiling_decomposition as D  # noqa: E402
import nyiso212_summer_seam_census as C  # noqa: E402
from market_sim.data.fleet.campd_bins import cc_summer_capacity  # noqa: E402
from scripts.lib.bundle_fleet import (  # noqa: E402
    bundle_gas_price,
    clear_fleet_caches,
    ensure_probe_path,
    full_run_year_kwargs,
)

FLAG = "cc_summer_derate_reconciled_basis"
CACHE = ROOT / ".cache/nyiso212"
T = 8760


def rebuild(year: int, arm: bool) -> dict:
    cache = CACHE / f"arm_{year}_{'on' if arm else 'off'}.pkl"
    if cache.exists():
        return pickle.load(open(cache, "rb"))
    ensure_probe_path()
    from scripts.run_calibration import run_year

    meta = json.loads((D.BUNDLE / "meta.json").read_text())
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
    units = pd.DataFrame(
        [
            {
                "i": i,
                "unit_id": str(g.unit_id),
                "plant": int(getattr(g, "plant_code", 0) or 0),
                "group": str(getattr(g, "plant_group", "") or ""),
                "pmax": float(g.pmax_mw),
                "hr": float(getattr(g, "heat_rate", 0.0)),
            }
            for i, g in enumerate(state["fleet"])
        ]
    )
    st = {
        "units": units,
        "avail": np.asarray(fa.availability, dtype=np.float64)[:, :T],
        "mc_base": np.asarray(getattr(fa, "mc_base", np.zeros(len(units))), dtype=float),
        "flag": bool(getattr(state["config"], FLAG, False)),
    }
    cache.parent.mkdir(parents=True, exist_ok=True)
    pickle.dump(st, open(cache, "wb"))
    return st


def main() -> None:
    recon = pd.read_csv(C.RECON)
    listed = set(recon.plant_code.astype(int))
    caps = cc_summer_capacity()
    sm = C.summer_mask()
    out: dict = {
        "session": "nyiso-212",
        "status": "PHASE 0 (zero LP) for the cc_summer_derate_reconciled_basis arm; the screen is pre-registered separately",
        "keeper": D.KEEPER_ID,
        "flag": FLAG,
        "by_year": {},
    }
    for year in D.YEARS:
        off, on = rebuild(year, False), rebuild(year, True)
        assert off["flag"] is False and on["flag"] is True, "flag did not take"
        U = off["units"]
        assert (U.unit_id.to_numpy() == on["units"].unit_id.to_numpy()).all()
        # G-DRIFT for the code edit: flag OFF must equal the pre-change rebuild at 57185.
        pre = pickle.load(open(CACHE / f"keeper_{year}.pkl", "rb"))
        sel = pre["plant_units"].i.to_numpy()
        drift = float(np.abs(off["avail"][sel] - pre["plant_avail"]).max())
        # F-1 footprint
        dav = on["avail"] - off["avail"]
        moved = np.abs(dav).max(axis=1) > 1e-12
        moved_plants = sorted(set(U[moved].plant))
        moved_groups = sorted(set(U[moved].group))
        others_identical = bool(
            np.array_equal(on["units"].pmax.to_numpy(), U.pmax.to_numpy())
            and np.array_equal(on["units"].hr.to_numpy(), U.hr.to_numpy())
            and np.allclose(on["mc_base"], off["mc_base"], atol=0.0, rtol=0.0)
        )
        offsummer_untouched = bool(np.abs(dav[:, ~sm]).max() <= 1e-12)
        # F-2 identity per moved plant
        ident = {}
        worst = 0.0
        for plant in moved_plants:
            npl, ns = caps[plant]
            carried = float(U[(U.plant == plant) & (U.group == "CC_REGULAR")].pmax.sum())
            expected = min(1.0, ns / carried) / min(1.0, ns / npl)
            rows = U[(U.plant == plant) & moved].i.to_numpy()
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = on["avail"][rows][:, sm] / off["avail"][rows][:, sm]
            got = float(np.nanmedian(ratio))
            err = float(np.nanmax(np.abs(ratio - expected)))
            worst = max(worst, err)
            ident[str(plant)] = {
                "mode": str(recon.set_index("plant_code").loc[plant, "mode"]),
                "carried_mw": round(carried, 1),
                "nameplate_mw": round(npl, 1),
                "net_summer_mw": round(ns, 1),
                "expected_on_over_off": round(expected, 6),
                "measured_on_over_off": round(got, 6),
                "max_abs_err": err,
                "summer_capability_off_mw": round(carried * min(1.0, ns / npl), 1),
                "summer_capability_on_mw": round(carried * min(1.0, ns / carried), 1),
            }
        # F-3 Cricket Valley ceiling, OFF vs ON
        g = C.facility_gross(D.PLANT, year)
        cv = U[(U.plant == D.PLANT) & (U.group == "CC_REGULAR")]
        pm = cv.pmax.to_numpy()[:, None]
        ceil_off = (off["avail"][cv.i.to_numpy()] * pm).sum(axis=0)
        ceil_on = (on["avail"][cv.i.to_numpy()] * pm).sum(axis=0)
        ufac = D.loader_ufac(year)
        with np.errstate(divide="ignore", invalid="ignore"):
            f_off = float(np.nanmean(np.where(ufac > 0, off["avail"][cv.i.to_numpy()[0]] / ufac, np.nan)[sm]))
            f_on = float(np.nanmean(np.where(ufac > 0, on["avail"][cv.i.to_numpy()[0]] / ufac, np.nan)[sm]))
        months_over = lambda ceil: [  # noqa: E731
            m + 1
            for m in range(12)
            if g[D.MONTH_STARTS[m] : D.MONTH_STARTS[m + 1]].sum()
            > ceil[D.MONTH_STARTS[m] : D.MONTH_STARTS[m + 1]].sum()
        ]
        cvrow = {
            "summer_statistical_factor_off": round(f_off, 6),
            "summer_statistical_factor_on": round(f_on, 6),
            "summer_available_gwh_off": round(float(ceil_off[sm].sum()) / 1e3, 2),
            "summer_available_gwh_on": round(float(ceil_on[sm].sum()) / 1e3, 2),
            "summer_hours_meter_above_ceiling_off": int((g[sm] > ceil_off[sm] + 1e-6).sum()),
            "summer_hours_meter_above_ceiling_on": int((g[sm] > ceil_on[sm] + 1e-6).sum()),
            "summer_gwh_meter_above_ceiling_off": round(float(np.clip(g[sm] - ceil_off[sm], 0, None).sum()) / 1e3, 2),
            "summer_gwh_meter_above_ceiling_on": round(float(np.clip(g[sm] - ceil_on[sm], 0, None).sum()) / 1e3, 2),
            "months_meter_over_ceiling_off": months_over(ceil_off),
            "months_meter_over_ceiling_on": months_over(ceil_on),
            "annual_available_gwh_off": round(float(ceil_off.sum()) / 1e3, 2),
            "annual_available_gwh_on": round(float(ceil_on.sum()) / 1e3, 2),
        }
        class_delta = (
            pd.DataFrame({"group": U.group, "gwh": (dav * U.pmax.to_numpy()[:, None]).sum(axis=1) / 1e3})
            .groupby("group").gwh.sum()
        )
        out["by_year"][str(year)] = {
            "G_DRIFT_flag_off_vs_prechange_rebuild_max_abs": drift,
            "F1_units_moved": int(moved.sum()),
            "F1_units_total": int(len(U)),
            "F1_plants_moved": moved_plants,
            "F1_groups_moved": moved_groups,
            "F1_moved_set_equals_reconcile_table": bool(set(moved_plants) == listed),
            "F1_pmax_hr_mc_identical": others_identical,
            "F1_offsummer_untouched": offsummer_untouched,
            "F2_worst_abs_err": worst,
            "F2_per_plant": ident,
            "F3_cricket_valley": cvrow,
            "class_available_energy_delta_gwh": {k: round(float(v), 2) for k, v in class_delta.items() if abs(v) > 1e-6},
        }
    dest = ROOT / "results/calibration/_nyiso212_arm_phase0.json"
    dest.write_text(json.dumps(out, indent=1, default=str))
    for y, r in out["by_year"].items():
        print(y, {k: v for k, v in r.items() if k not in ("F2_per_plant",)})


if __name__ == "__main__":
    main()
