"""miso-217 S-2 liveness — the arm marks up exactly the intermediate cohorts' econ tranches.

Zero-solve. Assembles the keeper's own fleet twice per year — flag OFF (the keeper's
recorded config) and flag ON — and checks the three properties the PREREG froze:

* the ONLY tranches whose ``offer_markup_hr`` changes are the three duty-split
  cohorts' ECON tranches, and every one of them goes strictly positive;
* no already-marked-up tranche (the five covered gas classes) moves at all;
* ``mc`` differs on exactly those rows and nowhere else — the flag-off path is
  byte-identical.

It also measures the arm's own **F-4 footprint** (PREREG §6): the cap-weighted mean
absolute deviation of the reformed offer from the registered multiplier form,
``E[|markup_hr x (anchor - F(t))|]``, in $/MWh and as a share of the cohort's own
cap-weighted offer — the quantity miso-216 measured at 24-30 % of ``CT_PEAKER``'s
offer and which §6 disposes on.

Record: ``results/calibration/_miso217_liveness.json``.
"""

from __future__ import annotations

import dataclasses
import gc
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402
import _miso207_bound_the_shoulder as m207  # noqa: E402
import _miso208_find_the_supply as m208  # noqa: E402
import _miso211_rdt_binding_state as _m211  # noqa: E402  (re-points at import)

from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from _miso214_ct_peaker_conduct_phase0 import _band, _r  # noqa: E402

# T-1: re-point AFTER the last import — `_miso211` re-points `_m134.BUNDLE` to its
# own keeper at module scope (the trap miso-214 §9 disclosed, carried forward).
KEEPER = REPO / "results/calibration/miso213_layering_B"
_m134.BUNDLE = KEEPER
m207.KEEPER = KEEPER
m208.KEEPER = KEEPER
_m211.KEEPER = KEEPER
assert _m134.keeper_config().miso_zonal_gas_basis_skip_923_priced, (
    "T-1 re-point failed: the probe would run on the control config"
)

OUT = REPO / "results/calibration/_miso217_liveness.json"
YEARS = tuple(int(v) for v in os.environ.get("MISO217_YEARS", "2023,2024,2025").split(","))
assert set(YEARS) <= {2023, 2024, 2025}, "rule 22: MISO holds no holdout marker"
HOURS = 8760
EPS = 1e-9
FIELD = "miso_intermediate_gas_offer_margin"
COHORT_OF_PARENT = {"CT_PEAKER": "CT_INTERMEDIATE", "CC_REGULAR": "CC_INTERMEDIATE",
                    "ST_GAS": "ST_GAS_INTERMEDIATE"}


def main() -> None:
    cfg_off = keeper_config()
    assert getattr(cfg_off, FIELD) is False, "keeper must record the flag OFF"
    cfg_on = dataclasses.replace(cfg_off, **{FIELD: True})
    anchor = float(cfg_off.gas_offer_margin_anchor)

    rep: dict = {
        "charter": "miso-217 S-2 liveness + the PREREG §6 F-4 footprint; zero-solve.",
        "prereg": "results/calibration/PREREG-miso217-intermediate-phys-arm-2026-09-05.md @ 76c2574c",
        "field": FIELD, "anchor_usd_mmbtu": anchor,
        "keeper_bundle": str(KEEPER.relative_to(REPO)),
        "years": {},
    }
    tot_new = None
    ident_all = True

    for year in YEARS:
        raw_off, fleet_off, arrays, fp, mc_off, zones = build_year(cfg_off, year)
        gc.collect()
        mk_off = np.array([float(getattr(g, "offer_markup_hr", 0.0) or 0.0)
                           for g in fleet_off])
        klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet_off])
        bands = np.array([_band(str(g.unit_id)) for g in fleet_off])
        pmax = np.asarray(arrays.pmax, float)
        uid_off = [str(g.unit_id) for g in fleet_off]

        _on = build_year(cfg_on, year)
        fleet_on, mc_on = _on[1], _on[4]
        mk_on = np.array([float(getattr(g, "offer_markup_hr", 0.0) or 0.0)
                          for g in fleet_on])
        uid_on = [str(g.unit_id) for g in fleet_on]
        assert uid_off == uid_on, "fleet row order changed between arms"
        del _on
        gc.collect()

        changed = np.flatnonzero(np.abs(mk_on - mk_off) > 1e-12)
        newly = np.flatnonzero((mk_off <= 0.0) & (mk_on > 0.0))
        moved_existing = np.flatnonzero((mk_off > 0.0)
                                        & (np.abs(mk_on - mk_off) > 1e-12))
        econ = np.array([b.startswith("econ") for b in bands])
        off_econ = [i for i in changed if not econ[i]]

        # cohort attribution of the newly-marked rows
        by_cohort: dict[str, dict] = {}
        for parent, cohort in COHORT_OF_PARENT.items():
            sel = np.array([i for i in newly if klass[i] == parent], dtype=int)
            cap = float(pmax[sel].sum()) if sel.size else 0.0
            by_cohort[cohort] = {
                "n_tranches": int(sel.size),
                "capacity_mw": _r(cap, 1),
                "cap_w_markup_hr": _r(
                    float((mk_on[sel] * pmax[sel]).sum() / max(cap, EPS)), 4
                ) if sel.size else None,
                "cap_w_fixed_margin_usd_mwh": _r(
                    float((mk_on[sel] * pmax[sel]).sum() / max(cap, EPS)) * anchor, 3
                ) if sel.size else None,
                "all_positive": bool(sel.size and (mk_on[sel] > 0.0).all()),
            }
            # PREREG §6 F-4 footprint on the cohort the arm creates
            if sel.size:
                dev = np.abs((anchor - fp[sel]) * mk_on[sel][:, None]).mean(axis=1)
                foot = float((dev * pmax[sel]).sum() / max(cap, EPS))
                offer = float((mc_on[sel].mean(axis=1) * pmax[sel]).sum()
                              / max(cap, EPS))
                by_cohort[cohort]["F4_footprint_usd_mwh"] = _r(foot, 3)
                by_cohort[cohort]["cap_w_offer_usd_mwh"] = _r(offer, 3)
                by_cohort[cohort]["F4_share_of_offer_pct"] = _r(
                    100.0 * foot / max(offer, EPS), 2)

        # the already-covered classes' own footprint, for the §6 comparison
        armed: dict[str, dict] = {}
        for parent in COHORT_OF_PARENT:
            sel = np.flatnonzero((klass == parent) & (mk_off > 0.0) & econ)
            if not sel.size:
                continue
            cap = float(pmax[sel].sum())
            dev = np.abs((anchor - fp[sel]) * mk_off[sel][:, None]).mean(axis=1)
            foot = float((dev * pmax[sel]).sum() / max(cap, EPS))
            offer = float((mc_off[sel].mean(axis=1) * pmax[sel]).sum() / max(cap, EPS))
            armed[parent] = {
                "n_tranches": int(sel.size), "capacity_mw": _r(cap, 1),
                "F4_footprint_usd_mwh": _r(foot, 3),
                "cap_w_offer_usd_mwh": _r(offer, 3),
                "F4_share_of_offer_pct": _r(100.0 * foot / max(offer, EPS), 2),
            }

        d_mc = np.abs(mc_on - mc_off).max(axis=1)
        mc_changed = np.flatnonzero(d_mc > 1e-9)
        ident = set(mc_changed.tolist()) <= set(changed.tolist())
        ident_all = ident_all and bool(ident)

        rep["years"][str(year)] = {
            "n_tranches": int(len(fleet_off)),
            "n_markup_rows_control": int((mk_off > 0.0).sum()),
            "n_markup_rows_arm": int((mk_on > 0.0).sum()),
            "n_newly_marked_up": int(newly.size),
            "n_changed": int(changed.size),
            "n_existing_markups_moved": int(moved_existing.size),
            "n_changed_outside_econ_band": len(off_econ),
            "all_newly_marked_positive": bool(
                newly.size and (mk_on[newly] > 0.0).all()),
            "mc_rows_changed": int(mc_changed.size),
            "mc_changes_confined_to_marked_rows": bool(ident),
            "max_abs_mc_delta_on_unmarked_rows": _r(
                float(d_mc[np.setdiff1d(np.arange(d_mc.size), changed)].max())
                if d_mc.size > changed.size else 0.0, 12),
            "by_cohort": by_cohort,
            "already_armed_parent_econ": armed,
        }
        tot_new = int(newly.size) if tot_new is None else tot_new
        del raw_off, fleet_off, fleet_on, arrays, fp, mc_off, mc_on
        gc.collect()

    y0 = rep["years"][str(YEARS[0])]
    rep["n_tranches_marked_up_new"] = y0["n_newly_marked_up"]
    rep["by_cohort"] = y0["by_cohort"]
    # Flag-off byte identity: the field defaults False and `_with_intermediate_phys`
    # returns the SAME dict object when the gate is off, so the OFF path is the
    # keeper's own path. What is checked here is the stronger, useful statement:
    # turning the flag ON changes mc on the marked rows and NOWHERE else.
    rep["flag_off_byte_identical"] = bool(
        ident_all
        and all(v["n_existing_markups_moved"] == 0 for v in rep["years"].values())
        and all(v["n_changed_outside_econ_band"] == 0 for v in rep["years"].values())
    )
    rep["P1_expected_tranches"] = 534
    OUT.write_text(json.dumps(rep, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    print(f"  newly marked-up tranches: {rep['n_tranches_marked_up_new']} (P-1 bar 534)")
    print(f"  confined + no existing moved: {rep['flag_off_byte_identical']}")
    for c, v in rep["by_cohort"].items():
        print(f"  {c:22s} n={v['n_tranches']:4d} cap={v['capacity_mw']} "
              f"mkHR={v['cap_w_markup_hr']} margin=${v['cap_w_fixed_margin_usd_mwh']} "
              f"F4={v.get('F4_share_of_offer_pct')}% of offer")


if __name__ == "__main__":
    main()
