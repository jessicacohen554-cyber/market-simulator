"""NYISO-NEXT-3 phase 0 (zero LP): the thermal-tranche artifact on the repaired availability basis.

NYISO-NEXT-2 folded Astoria 8906's stack-duplicate boilers (``32SH``/``52SH``) in the outage
deriver and re-derived only the HOUR-grain merit-guarded extract pair. The DAY-grain
``campd-unit-outages-perunitmerit-NYISO.csv`` and the tranche artifact derived from it,
``thermal_tranches-perunitmerit-NYISO.csv``, still carry the double count: a tranche row's
``online_hours`` / ``committed_pct`` / ``median_cf`` / ``p25_cf`` / ``online_frac`` are computed
over ``avail_cap = nameplate x avail_mult``, and Astoria's ``avail_mult`` was read off an
extract that booked each twin at the generator's full peak.

For each year this rebuilds the keeper's fleet through the sanctioned fleet-only path
(``replay_keeper.run_year_kwargs`` -> ``run_calibration.run_year(fleet_only=True)``) in up to
three states:

* ``control`` -- the committed artifacts;
* ``arm`` -- ``--arm-dir``'s re-derived files swapped into ``data/raw`` (restored in a
  ``finally``);
* ``arm_sel`` (``--with-selector``) -- ``arm`` plus the per-plant committed-share read at
  ``campd_bins._generators_to_bins`` taken from the SAME ``-perunitmerit-`` artifact every
  other tranche consumer reads (the call omitted ``merit_guard``; patched here in-process).

It reports G-FOOTPRINT (which fleet arrays move, and at which plants), per NYC/LI steam plant
the tranche capacities and offer levels, and two bounds on the energy the change can move:

* BINDING bound -- added available energy in hours the keeper's registered dispatch of the
  plant sat at its availability cap (the NYISO-NEXT-2 construction);
* ECONOMIC-REACH bound -- the change in the plant's IN-MERIT available energy at the
  keeper's own hourly zonal price: ``sum_t sum_rows cap[r,t] * 1(mc[r,t] < price[z,t])``,
  arm minus control, split into its positive and negative parts. It is a first-order
  re-dispatch estimate at a fixed price, not a bound in the strict sense: the price moves.

Writes ``results/calibration/_nyisonext3_tranche_basis_phase0.json``.
"""

from __future__ import annotations

import argparse
import functools
import json
import shutil
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes import nyisonext2_astoria_pair_phase0 as prev  # noqa: E402

T = 8760
BUNDLES = {2021: "results/calibration/nyisonext2_2021"}
DEFAULT_BUNDLE = "results/calibration/nyisonext2_span"
RUNS = {2021: "2026-09-26-nyisonext2-astoria-pair-2021"}
DEFAULT_RUN = "2026-09-26-nyisonext2-astoria-pair-span"
#: NYC (Con Ed LDC) steam, then LI / Hudson steam for contrast.
PLANTS = {8906: "Astoria", 2500: "Ravenswood", 2490: "Arthur Kill", 2516: "Northport",
          2511: "Barrett", 2625: "Bowline", 8006: "Roseton"}
ARRAYS = ("pmax", "pmin", "heat_rate", "availability", "min_gen", "zone_idx", "vom")
#: file name in --arm-dir -> destination relative to data/raw
DEST = {
    "campd-unit-outages-perunitmerit-NYISO.csv": "",
    "campd-unit-outages-layup-perunitmerit-NYISO.csv": "",
    "thermal_tranches-perunitmerit-NYISO.csv": "_processed-legacy",
}


def _selector_patch():
    """Return (apply, undo) for the committed-share merit-guard selector."""
    from market_sim.data.fleet import campd_bins as cb

    orig = cb.thermal_tranche_overrides

    @functools.wraps(orig)
    def patched(iso, coal_online_pmin=False, per_unit=False, merit_guard=False):
        return orig(iso, coal_online_pmin, per_unit, merit_guard or per_unit)

    def apply():
        cb.thermal_tranche_overrides = patched

    def undo():
        cb.thermal_tranche_overrides = orig

    return apply, undo


def _build(year: int) -> dict:
    """Fleet-only rebuild of the keeper recipe on whatever is in data/raw."""
    from scripts import run_calibration_full as rcf
    from scripts.replay_keeper import run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((REPO / BUNDLES.get(year, DEFAULT_BUNDLE) / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    ref = rcf._load_reference()
    gp = rcf._henry_hub_actual(ref, year)
    return run_year(year, meta["iso"], T, gp, {}, fleet_only=True, **kw)


def _build_on(year: int, arm_dir: Path | None, selector: bool) -> dict:
    """Build with committed files, or with ``arm_dir``'s swapped in (and the selector)."""
    raw = REPO / "data/raw"
    bak: dict[Path, bytes] = {}
    apply, undo = _selector_patch()
    try:
        if arm_dir is not None:
            for f, sub in DEST.items():
                src = arm_dir / f
                if not src.exists():
                    continue
                dst = raw / sub / f
                bak[dst] = dst.read_bytes()
                shutil.copyfile(src, dst)
        if selector:
            apply()
        prev._clear_caches()
        return _build(year)
    finally:
        undo()
        for dst, b in bak.items():
            dst.write_bytes(b)
        prev._clear_caches()


def _mc(res: dict, n: int) -> np.ndarray:
    """(G, T) offer levels from a fleet-only result."""
    mc = np.asarray(res["mc_base"], dtype=float)
    return np.broadcast_to(mc[:, None], (n, T)) if mc.ndim == 1 else mc


def _prices(year: int) -> dict[int, np.ndarray]:
    """Keeper P1 hourly zonal price, keyed by zone index order of the fleet build."""
    import pandas as pd

    p = REPO / BUNDLES.get(year, DEFAULT_BUNDLE) / "hourly" / f"system_{year}.parquet"
    d = pd.read_parquet(p)
    d = d[d["pass"] == "P1"]
    return {z: g.sort_values("hour")["price"].to_numpy()[:T] for z, g in d.groupby("zone")}


def _diff(ctl: dict, arm: dict) -> dict:
    """G-FOOTPRINT between two builds, plus per-plant detail and both bounds."""
    fa, fb = ctl["fleet_arrays"], arm["fleet_arrays"]
    pc = np.asarray(fa.plant_code).astype(int)
    assert np.array_equal(pc, np.asarray(fb.plant_code).astype(int)), "row set moved"
    pg = np.asarray(fa.plant_group).astype(str)
    foot: dict = {}
    for a in ARRAYS:
        x, y = np.asarray(getattr(fa, a)), np.asarray(getattr(fb, a))
        if x.shape != y.shape:
            foot[a] = {"identical": False, "shape": [list(x.shape), list(y.shape)]}
            continue
        neq = ~np.isclose(x, y, rtol=0, atol=1e-9)
        rows = np.flatnonzero(neq.reshape(neq.shape[0], -1).any(1)) if neq.ndim else []
        foot[a] = {
            "identical": not bool(neq.any()),
            "plants_moved": sorted({f"{pc[r]}:{pg[r]}" for r in rows}),
        }
    n = pc.size
    ma, mb = _mc(ctl, n), _mc(arm, n)
    neq = ~np.isclose(ma, mb, rtol=0, atol=1e-9)
    foot["mc_base"] = {
        "identical": not bool(neq.any()),
        "plants_moved": sorted({f"{pc[r]}:{pg[r]}" for r in np.flatnonzero(neq.any(1))}),
    }
    return foot


def _plant_detail(year: int, ctl: dict, arm: dict, extra: set[str]) -> dict:
    """Tranche capacities, offer levels and both bounds per watched / moved plant-class."""
    import gzip

    fa, fb = ctl["fleet_arrays"], arm["fleet_arrays"]
    pc = np.asarray(fa.plant_code).astype(int)
    pg = np.asarray(fa.plant_group).astype(str)
    zi = np.asarray(fa.zone_idx).astype(int)
    zones = list(ctl["iso_config"].zone_names)
    n = pc.size
    ma, mb = _mc(ctl, n), _mc(arm, n)
    price = _prices(year)
    pay = prev._payload(RUNS.get(year, DEFAULT_RUN))["years"][str(year)]["plants"]
    bench = json.loads(
        gzip.open(REPO / f"frontend/data/backcast/bench/NYISO/{year}.json.gz").read()
    )["bench"]["plants"]
    out = {}
    keys = [(c, "ST_GAS", n) for c, n in PLANTS.items()]
    keys += [
        (int(k.split(":")[0]), k.split(":")[1], "")
        for k in sorted(extra)
        if (int(k.split(":")[0]), k.split(":")[1]) not in {(c, g) for c, g, _ in keys}
    ]
    for code, cls, name in keys:
        rows = np.flatnonzero((pc == code) & (pg == cls))
        if rows.size == 0:
            continue
        pmax_a = np.asarray(fa.pmax, float)[rows]
        pmax_b = np.asarray(fb.pmax, float)[rows]
        cap_a = pmax_a[:, None] * np.asarray(fa.availability, float)[rows]
        cap_b = pmax_b[:, None] * np.asarray(fb.availability, float)[rows]
        zname = zones[zi[rows[0]]] if zones else None
        rec = {
            "name": name,
            "zone": zname,
            "tranche_pmax_control": [round(float(v), 1) for v in pmax_a],
            "tranche_pmax_arm": [round(float(v), 1) for v in pmax_b],
            "tranche_mc_mean_control": [round(float(v), 2) for v in ma[rows].mean(1)],
            "tranche_mc_mean_arm": [round(float(v), 2) for v in mb[rows].mean(1)],
            "avail_twh_control": round(float(cap_a.sum()) / 1e6, 4),
            "avail_twh_arm": round(float(cap_b.sum()) / 1e6, 4),
            "min_gen_twh_control": round(float(np.asarray(fa.min_gen)[rows].sum()) / 1e6, 4),
            "min_gen_twh_arm": round(float(np.asarray(fb.min_gen)[rows].sum()) / 1e6, 4),
        }
        if zname in price:
            p = price[zname]
            ina = (cap_a * (ma[rows] < p[None, :])).sum(0)
            inb = (cap_b * (mb[rows] < p[None, :])).sum(0)
            d = inb - ina
            rec["inmerit_twh_control"] = round(float(ina.sum()) / 1e6, 4)
            rec["inmerit_twh_arm"] = round(float(inb.sum()) / 1e6, 4)
            rec["econ_reach_up_twh"] = round(float(np.clip(d, 0, None).sum()) / 1e6, 4)
            rec["econ_reach_down_twh"] = round(float(np.clip(d, None, 0).sum()) / 1e6, 4)
        key = f"{code}:{cls}" if f"{code}:{cls}" in pay else str(code)
        bp = bench.get(key)
        if bp is not None and key in pay and bp.get("group", cls) == cls:
            npl = float(bp["npl"])
            m = prev._cf(pay[key]["m"]) * npl / 100.0
            ca, cb_ = cap_a.sum(0), cap_b.sum(0)
            bind = m >= ca - npl / 100.0
            rec["model_twh_keeper"] = round(float(m.sum()) / 1e6, 4)
            rec["e923_twh"] = bp.get("e_ann")
            rec["binding_h_keeper"] = int(bind.sum())
            rec["binding_bound_add_twh"] = round(
                float(np.clip(cb_ - ca, 0, None)[bind].sum()) / 1e6, 4
            )
        out[f"{code}:{cls}"] = rec
    return out


def measure(year: int, arm_dir: Path, selector: bool) -> dict:
    """One year's control / arm (/ arm_sel) census."""
    ctl = _build_on(year, None, False)
    arm = _build_on(year, arm_dir, False)
    res = {}
    for name, b in (("arm", arm),) + ((("arm_sel", _build_on(year, arm_dir, True)),) if selector else ()):
        foot = _diff(ctl, b)
        moved = set()
        for v in foot.values():
            moved |= set(v.get("plants_moved", []))
        res[name] = {"footprint": foot, "plants": _plant_detail(year, ctl, b, moved)}
    return res


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm-dir", type=Path, required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025])
    ap.add_argument("--with-selector", action="store_true")
    ap.add_argument(
        "--out", type=Path,
        default=REPO / "results/calibration/_nyisonext3_tranche_basis_phase0.json",
    )
    a = ap.parse_args()
    res = {str(y): measure(y, a.arm_dir, a.with_selector) for y in a.years}
    a.out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
