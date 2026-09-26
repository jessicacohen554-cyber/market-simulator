"""NYISO-NEXT phase 0 (zero LP): the NYC persistent-base floor at unit grain, and the
lay-up window mask on its pro-rata basis.

For each year 2021-2025 this rebuilds the keeper's fleet twice through the sanctioned
fleet-only path (``replay_keeper.run_year_kwargs`` -> ``run_calibration.run_year(
fleet_only=True)``): the keeper recipe as registered (CONTROL), and the same recipe with
``reliability_floor_layup_window_mask=True`` (ARM). It reads the reliability-floor
``min_gen`` rows (``min_gen_mechanism == MECH_RELIABILITY_FLOOR``) at LP-row grain and
reports, per floored plant and year:

* floored TWh (control / arm);
* floored TWh in hours the class's own CAMPD meter reads ~zero (the bench part's
  class-resolved series, below 0.5 % of class nameplate), plus the raw plant-level meter;
* floor-active hours, and BINDING hours on the keeper's registered dispatch (class model
  MW from the run payload within one 1 % quantum of the class's floor MW), and the floor
  energy the ARM removes inside those binding hours;
* mean availability, mean lay-up share, and the floor-MW / (pmax x availability) ratio
  that shows how the pro-rata floor scales with the guard-returned availability.

It also records the G-FOOTPRINT diff (every fleet array other than ``min_gen`` must be
byte-identical between CONTROL and ARM, and ``min_gen`` may differ only on pro-rata
reliability-floor rows), and the basis-matched coefficient disclosure: the limb's own
statistic (cool-day p25 of fleet CAMPD gross / fleet floor basis, hourly grain, pooled
over the identification span 2023-2025) on the unmasked and the masked basis.

Writes ``results/calibration/_nyiso_next_floor_layup_phase0.json``.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

T = 8760
BUNDLES = {2021: "results/calibration/nyisostg_2021"}
DEFAULT_BUNDLE = "results/calibration/nyisostg_span"
RUNS = {2021: "2026-09-25-nyiso-stgas-ldc-2021"}
DEFAULT_RUN = "2026-09-25-nyiso-stgas-ldc-leg"
PRO_RATA_ZONES = ("NYC", "Long_Island")  # the two pro_rata limbs the keeper arms
ARRAYS = ("pmax", "pmin", "heat_rate", "availability", "zone_idx", "vom")


def _payload(rid: str) -> dict:
    """Decode a gzip+base64 run payload."""
    s = (REPO / f"frontend/data/backcast/runs/{rid}.js").read_text()
    b = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b)))


def _cf(b64: str) -> np.ndarray:
    """Decode a uint8 CF% series."""
    return np.frombuffer(base64.b64decode(b64), np.uint8).astype(float)[:T]


def _build(year: int, arm: bool) -> dict:
    """Fleet-only rebuild of the keeper recipe (``arm``: the lay-up mask on)."""
    from scripts import run_calibration_full as rcf
    from scripts.replay_keeper import run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads(
        (REPO / BUNDLES.get(year, DEFAULT_BUNDLE) / "meta.json").read_text()
    )
    kw = run_year_kwargs(meta)
    if arm:
        prb = dict(kw.get("prb_overrides") or {})
        prb["reliability_floor_layup_window_mask"] = True
        kw["prb_overrides"] = prb
    ref = rcf._load_reference()
    gp = rcf._henry_hub_actual(ref, year)
    b = run_year(year, meta["iso"], T, gp, {}, fleet_only=True, **kw)
    assert (
        bool(getattr(b["config"], "reliability_floor_layup_window_mask", False)) == arm
    )
    return b


def _campd_plant_gross(year: int) -> dict[int, np.ndarray]:
    """Raw unit-level CAMPD gross MW summed to the plant, (8760,) per plant."""
    from market_sim.data.campd import load_campd_hourly

    df = load_campd_hourly(["NY"], [year], prefer_unit_level=True)
    df = df[(df["hour_of_year"] >= 0) & (df["hour_of_year"] < T)]
    out: dict[int, np.ndarray] = {}
    for pc, g in df.groupby("plant_id"):
        a = np.zeros(T)
        s = g.groupby("hour_of_year")["gross_mw"].sum()
        a[s.index.to_numpy(int)] = s.to_numpy(float)
        out[int(pc)] = a
    return out


def _layup(b: dict, year: int) -> dict:
    """The lay-up shares the ARM reads (the same loader call, reproduced)."""
    from scripts.run_calibration import _reliability_floor_layup_shares

    cfg = b["config"]
    import dataclasses

    cfg = dataclasses.replace(cfg, reliability_floor_layup_window_mask=True)
    return _reliability_floor_layup_shares(cfg, "NYISO", year, b["fleet_arrays"]) or {}


def measure(year: int) -> dict:
    """One year's control / arm census."""
    from market_sim.data.floor_mechanisms import MECH_RELIABILITY_FLOOR

    ctl = _build(year, False)
    arm = _build(year, True)
    fa, fb = ctl["fleet_arrays"], arm["fleet_arrays"]
    zones = list(ctl["iso_config"].zone_names)

    # ---- G-FOOTPRINT: every non-floor array byte-identical ----
    foot = {}
    for a in ARRAYS:
        x, y = getattr(fa, a, None), getattr(fb, a, None)
        foot[a] = bool(
            (x is None and y is None) or np.array_equal(np.asarray(x), np.asarray(y))
        )
    foot["mc_base"] = bool(
        np.array_equal(np.asarray(ctl["mc_base"]), np.asarray(arm["mc_base"]))
    )
    mga, mgb = np.asarray(fa.min_gen), np.asarray(fb.min_gen)
    diff_rows = np.flatnonzero((mga != mgb).any(axis=1))
    mech_a = np.asarray(fa.min_gen_mechanism)
    pg = np.asarray(fa.plant_group).astype(str)
    zn = np.array([zones[int(z)] for z in fa.zone_idx])
    foot["min_gen_rows_changed"] = int(diff_rows.size)
    foot["changed_rows_all_prorata_rel_floor"] = bool(
        all(
            pg[r] == "ST_GAS"
            and zn[r] in PRO_RATA_ZONES
            and (mech_a[r] == MECH_RELIABILITY_FLOOR).any()
            for r in diff_rows
        )
    )
    foot["changed_plants"] = sorted({int(fa.plant_code[r]) for r in diff_rows})
    foot["arm_never_raises"] = bool((mgb <= mga + 1e-9).all())

    # ---- per-plant reliability-floor census ----
    campd = _campd_plant_gross(year)
    pay = _payload(RUNS.get(year, DEFAULT_RUN))["years"][str(year)]["plants"]
    bench = json.loads(
        gzip.open(REPO / f"frontend/data/backcast/bench/NYISO/{year}.json.gz").read()
    )["bench"]["plants"]
    layup = _layup(ctl, year)
    av = np.asarray(fa.availability)
    rel_rows = np.flatnonzero((mech_a == MECH_RELIABILITY_FLOOR).any(axis=1))
    by_plant: dict[int, list[int]] = defaultdict(list)
    for r in rel_rows:
        by_plant[int(fa.plant_code[r])].append(int(r))
    plants = {}
    for pc, rows in sorted(by_plant.items()):
        rows = np.array(rows)
        fl_c = np.where(mech_a[rows] == MECH_RELIABILITY_FLOOR, mga[rows], 0.0)
        mech_b = np.asarray(fb.min_gen_mechanism)
        fl_a = np.where(mech_b[rows] == MECH_RELIABILITY_FLOOR, mgb[rows], 0.0)
        pf_c, pf_a = fl_c.sum(0), fl_a.sum(0)
        pmax = fa.pmax[rows]
        cap = (pmax[:, None] * av[rows]).sum(0)
        cls = str(pg[rows[0]])
        lu = layup.get((pc, cls))
        # Multi-class plants are keyed "<plant>:<class>", single-class plants "<plant>".
        key = f"{pc}:{cls}" if f"{pc}:{cls}" in bench else str(pc)
        bp = bench.get(key)
        if bp is not None and bp.get("group") != cls:
            bp = None
        # The class-resolved CAMPD series (bench part, uint8 CF% of class nameplate):
        # "meter ~zero" = below half a percent of the class's own nameplate. The raw
        # plant-level meter (every unit at the site) is kept alongside it.
        if bp is not None:
            npl = float(bp["npl"])
            cmeter = _cf(bp["campd"]) * npl / 100.0
        else:
            npl, cmeter = float(pmax.sum()), np.zeros(T)
        zero = cmeter <= 0.0
        pzero = campd.get(pc, np.zeros(T)) <= 0.0
        rec = {
            "zone": str(zn[rows[0]]),
            "class": cls,
            "rows": int(rows.size),
            "pmax_mw": round(float(pmax.sum()), 1),
            "avail_mean": round(float(cap.sum() / (pmax.sum() * T)), 4),
            "layup_share_mean": None if lu is None else round(float(np.mean(lu)), 4),
            "floor_twh_control": round(float(pf_c.sum()) / 1e6, 4),
            "floor_twh_arm": round(float(pf_a.sum()) / 1e6, 4),
            "floor_twh_meter_zero_control": round(float(pf_c[zero].sum()) / 1e6, 4),
            "floor_twh_meter_zero_arm": round(float(pf_a[zero].sum()) / 1e6, 4),
            "floor_twh_plant_meter_zero_control": round(
                float(pf_c[pzero].sum()) / 1e6, 4
            ),
            "floor_twh_plant_meter_zero_arm": round(float(pf_a[pzero].sum()) / 1e6, 4),
            "floor_active_h_control": int((pf_c > 0).sum()),
            "floor_active_h_arm": int((pf_a > 0).sum()),
            "floor_mw_mean_control": round(float(pf_c.mean()), 1),
            "floor_mw_mean_arm": round(float(pf_a.mean()), 1),
            "floor_over_availcap": round(float(pf_c.sum() / max(cap.sum(), 1e-9)), 4),
            "campd_class_twh": round(float(cmeter.sum()) / 1e6, 4),
            "campd_class_zero_h": int(zero.sum()),
        }
        # BINDING hours on the keeper's registered dispatch (payload CF%, class grain):
        # model MW within one uint8 quantum (1 % of class nameplate) of the floor.
        if key in pay and bp is not None:
            m = _cf(pay[key]["m"]) * npl / 100.0
            bind = (pf_c > 0) & (m <= pf_c + npl / 100.0)
            rec["model_twh_keeper"] = round(float(m.sum()) / 1e6, 4)
            rec["e923_twh"] = bp.get("e_ann")
            rec["binding_h_control"] = int(bind.sum())
            rec["binding_h_meter_zero_control"] = int((bind & zero).sum())
            rec["binding_floor_twh_control"] = round(float(pf_c[bind].sum()) / 1e6, 4)
            # The dispatch the arm can remove directly: floor energy it withdraws in
            # hours the keeper sat on that floor (an UPPER bound on the first-order
            # ST_GAS cut; the LP may re-dispatch part of it economically).
            rec["removed_floor_twh_in_binding_h"] = round(
                float((pf_c - pf_a)[bind].sum()) / 1e6, 4
            )
        plants[pc] = rec
    return {"footprint": foot, "plants": plants, "n_layup_series": len(layup)}


def coefficient_disclosure(years=(2023, 2024, 2025)) -> dict:
    """The NYC limb's own statistic on the unmasked and the masked basis.

    Cool-day (zone tmax < 25 C) p25 of fleet CAMPD gross / fleet floor basis at hourly
    grain, pooled over ``years`` (the limb's identification span), on the model's own
    availability arrays. REPORTED, never armed: the arm leaves floor_pct at its frozen
    value (the level is not the instrument; rule 21).
    """
    from market_sim.data.eia930.weather import iso_zone_tmax

    num, den_u, den_m, cool = [], [], [], []
    for y in years:
        b = _build(y, False)
        fa = b["fleet_arrays"]
        zones = list(b["iso_config"].zone_names)
        pg = np.asarray(fa.plant_group).astype(str)
        zn = np.array([zones[int(z)] for z in fa.zone_idx])
        rows = np.flatnonzero((pg == "ST_GAS") & (zn == "NYC") & (fa.pmax > 0))
        lay = _layup(b, y)
        av = np.asarray(fa.availability)
        camp = _campd_plant_gross(y)
        codes = sorted({int(fa.plant_code[r]) for r in rows})
        g = sum(camp.get(c, np.zeros(T)) for c in codes)
        du = (fa.pmax[rows, None] * av[rows]).sum(0)
        dm = np.zeros(T)
        for r in rows:
            s = lay.get((int(fa.plant_code[r]), str(pg[r])))
            a = av[r] if s is None else np.maximum(av[r] - s, 0.0)
            dm += fa.pmax[r] * a
        tm = iso_zone_tmax("NYISO", y, T, zone="NYC")
        tmax = tm[0] if tm is not None else np.full(T, np.nan)
        num.append(g)
        den_u.append(du)
        den_m.append(dm)
        cool.append(tmax < 25.0)
    g, du, dm, c = (np.concatenate(x) for x in (num, den_u, den_m, cool))
    ru = np.where(du > 0, g / np.maximum(du, 1e-9), np.nan)
    rm = np.where(dm > 0, g / np.maximum(dm, 1e-9), np.nan)
    return {
        "years": list(years),
        "p25_cool_unmasked": round(float(np.nanpercentile(ru[c], 25)), 4),
        "p25_cool_masked": round(float(np.nanpercentile(rm[c & (dm > 0)], 25)), 4),
        "masked_basis_zero_h": int((dm <= 0).sum()),
        "mean_basis_mw_unmasked": round(float(du.mean()), 1),
        "mean_basis_mw_masked": round(float(dm.mean()), 1),
    }


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--years", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025]
    )
    ap.add_argument("--no-coef", action="store_true")
    ap.add_argument(
        "--out",
        default=str(REPO / "results/calibration/_nyiso_next_floor_layup_phase0.json"),
    )
    a = ap.parse_args()
    logging.basicConfig(level=logging.WARNING)
    p = Path(a.out)
    res = json.loads(p.read_text()) if p.exists() else {}
    for y in a.years:
        res[str(y)] = measure(y)
        p.write_text(json.dumps(res, indent=1, default=str))
        r = res[str(y)]
        print(y, "footprint", r["footprint"], flush=True)
        for pc, q in r["plants"].items():
            print(f"  {pc} {q['zone']} {q['class']} {q}", flush=True)
    if not a.no_coef:
        res["coefficient_disclosure"] = coefficient_disclosure()
        p.write_text(json.dumps(res, indent=1, default=str))
        print("coef", res["coefficient_disclosure"], flush=True)


if __name__ == "__main__":
    main()
