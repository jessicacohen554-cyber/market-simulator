"""NYISO-NEXT-2 phase 0 (zero LP): the Astoria stack-duplicate boiler pair in the
merit-guarded hour-grain unit-outage extract.

The outage deriver's detector loop never folded CAMPD's stack-duplicate twins
(``campd.CAMPD_STACK_DUPLICATE_UNITS``: Astoria 8906 ``32SH`` -> ``31RH``,
``52SH`` -> ``51RH``). Each twin was detected on the generator's full gross load,
booked at the generator's full observed peak (plant basis 1,705 MW against a
physical ~934), and the duplicate -- absent from the merit panel that already folds
it onto its primary -- failed OPEN to "outage" on every stop its primary's merit
test classified as lay-up.

For each year this rebuilds the keeper's fleet twice through the sanctioned
fleet-only path (``replay_keeper.run_year_kwargs`` -> ``run_calibration.run_year(
fleet_only=True)``): on the COMMITTED extract pair (CONTROL) and on the repaired
pair re-derived under the committed invocation (ARM, passed with ``--arm-dir``;
swapped into ``data/raw`` for the build and restored in a ``finally``). It reports

* G-FOOTPRINT: every fleet array identical outside Astoria 8906 rows, and
  ``min_gen`` / ``availability`` the only arrays that may move at all;
* Astoria per class: pmax, mean availability, available TWh, floor TWh;
* the BINDING-HOUR BOUND: the added available energy in hours the keeper's
  registered dispatch sat at its availability cap (payload class CF within one
  uint8 quantum of ``pmax x availability``) -- an upper bound on the first-order
  energy the repair can add (the LP may also re-dispatch economically elsewhere).

Writes ``results/calibration/_nyisonext2_astoria_pair_phase0.json``.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

T = 8760
PLANT = 8906
BUNDLES = {2021: "results/calibration/nyisonext_2021"}
DEFAULT_BUNDLE = "results/calibration/nyisonext_span"
RUNS = {2021: "2026-09-26-nyisonext-floor-layup-2021"}
DEFAULT_RUN = "2026-09-26-nyisonext-floor-layup-span"
FILES = (
    "campd-unit-outages-perunitmerithour-NYISO.csv",
    "campd-unit-outages-layup-perunitmerithour-NYISO.csv",
)
ARRAYS = ("pmax", "pmin", "heat_rate", "availability", "min_gen", "zone_idx", "vom")


def _payload(rid: str) -> dict:
    """Decode a gzip+base64 run payload."""
    s = (REPO / f"frontend/data/backcast/runs/{rid}.js").read_text()
    b = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b)))


def _cf(b64: str) -> np.ndarray:
    """Decode a uint8 CF% series."""
    return np.frombuffer(base64.b64decode(b64), np.uint8).astype(float)[:T]


def _build(year: int) -> dict:
    """Fleet-only rebuild of the keeper recipe on whatever extract is in data/raw."""
    from scripts import run_calibration_full as rcf
    from scripts.replay_keeper import run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads(
        (REPO / BUNDLES.get(year, DEFAULT_BUNDLE) / "meta.json").read_text()
    )
    kw = run_year_kwargs(meta)
    ref = rcf._load_reference()
    gp = rcf._henry_hub_actual(ref, year)
    return run_year(year, meta["iso"], T, gp, {}, fleet_only=True, **kw)


def _clear_caches() -> None:
    """Drop every lru_cache in the loaded market_sim/scripts modules."""
    import functools

    for mod in list(sys.modules.values()):
        name = getattr(mod, "__name__", "")
        if not (name.startswith("market_sim") or name.startswith("scripts")):
            continue
        for v in list(vars(mod).values()):
            if isinstance(v, functools._lru_cache_wrapper):
                v.cache_clear()


def _build_on(year: int, arm_dir: Path | None) -> dict:
    """Build with the committed pair, or with ``arm_dir``'s pair swapped in."""
    raw = REPO / "data/raw"
    bak = {}
    try:
        if arm_dir is not None:
            for f in FILES:
                bak[f] = (raw / f).read_bytes()
                shutil.copyfile(arm_dir / f, raw / f)
        _clear_caches()
        return _build(year)
    finally:
        for f, b in bak.items():
            (raw / f).write_bytes(b)
        _clear_caches()


def measure(year: int, arm_dir: Path) -> dict:
    """One year's control / arm census."""
    ctl = _build_on(year, None)
    arm = _build_on(year, arm_dir)
    fa, fb = ctl["fleet_arrays"], arm["fleet_arrays"]
    pc = np.asarray(fa.plant_code).astype(int)
    assert np.array_equal(pc, np.asarray(fb.plant_code).astype(int))
    ast = pc == PLANT
    foot = {}
    for a in ARRAYS:
        x, y = np.asarray(getattr(fa, a)), np.asarray(getattr(fb, a))
        foot[a] = {
            "identical": bool(np.array_equal(x, y)),
            "identical_outside_8906": bool(np.array_equal(x[~ast], y[~ast])),
        }
    foot["mc_base_identical"] = bool(
        np.array_equal(np.asarray(ctl["mc_base"]), np.asarray(arm["mc_base"]))
    )
    pg = np.asarray(fa.plant_group).astype(str)
    pay = _payload(RUNS.get(year, DEFAULT_RUN))["years"][str(year)]["plants"]
    bench = json.loads(
        gzip.open(REPO / f"frontend/data/backcast/bench/NYISO/{year}.json.gz").read()
    )["bench"]["plants"]
    out = {"footprint": foot, "classes": {}}
    for cls in sorted(set(pg[ast])):
        rows = np.flatnonzero(ast & (pg == cls))
        pmax = np.asarray(fa.pmax)[rows]
        ca = (pmax[:, None] * np.asarray(fa.availability)[rows]).sum(0)
        cb = (pmax[:, None] * np.asarray(fb.availability)[rows]).sum(0)
        fla = np.asarray(fa.min_gen)[rows].sum(0)
        flb = np.asarray(fb.min_gen)[rows].sum(0)
        rec = {
            "rows": int(rows.size),
            "pmax_mw": round(float(pmax.sum()), 1),
            "avail_mean_control": round(float(ca.mean() / pmax.sum()), 4),
            "avail_mean_arm": round(float(cb.mean() / pmax.sum()), 4),
            "avail_twh_control": round(float(ca.sum()) / 1e6, 4),
            "avail_twh_arm": round(float(cb.sum()) / 1e6, 4),
            "min_gen_twh_control": round(float(fla.sum()) / 1e6, 4),
            "min_gen_twh_arm": round(float(flb.sum()) / 1e6, 4),
            "hours_avail_up": int((cb > ca + 1e-6).sum()),
            "hours_avail_down": int((cb < ca - 1e-6).sum()),
        }
        key = f"{PLANT}:{cls}" if f"{PLANT}:{cls}" in bench else str(PLANT)
        bp = bench.get(key)
        if bp is not None and bp.get("group") == cls and key in pay:
            npl = float(bp["npl"])
            m = _cf(pay[key]["m"]) * npl / 100.0
            bind = m >= ca - npl / 100.0
            gain = np.clip(cb - ca, 0.0, None)
            rec["model_twh_keeper"] = round(float(m.sum()) / 1e6, 4)
            rec["e923_twh"] = bp.get("e_ann")
            rec["binding_h_keeper"] = int(bind.sum())
            rec["binding_bound_add_twh"] = round(float(gain[bind].sum()) / 1e6, 4)
            rec["removal_twh_where_down"] = round(
                float(np.clip(ca - cb, 0.0, None).sum()) / 1e6, 4
            )
        out["classes"][cls] = rec
    return out


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm-dir", type=Path, required=True)
    ap.add_argument(
        "--years", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025]
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=REPO / "results/calibration/_nyisonext2_astoria_pair_phase0.json",
    )
    a = ap.parse_args()
    res = {str(y): measure(y, a.arm_dir) for y in a.years}
    a.out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
