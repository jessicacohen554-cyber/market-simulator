"""PJM-NEXT-25 card 3 (zero LP): what do the soco-70 COAL coverage rows do to the keeper's fleet?

``derive_thermal_tranches.py --iso PJM --years 2019 ... 2025 --coal-unit-coverage`` appends
a measured COAL row for every coal plant ``thermal_tranches_PJM.csv`` has none for (the
2019-22 retirees: Homer City, Sammis, Zimmer, Morgantown, Chesterfield, ...), leaving the
29 existing rows byte-identical. This rebuilds the keeper recipe (bundle
``pjmnext16_A_span``, ``fleet_only`` path, ``pjm_da_virtual_bids`` off) once with the
incumbent artifact and once with the candidate, and compares per-unit arrays:

- confinement: only units of the appended plants may move (pmax split, min_gen, mc);
- per appended plant: tranche capacity (must-run / sync / committed / econ / peak),
  floored MWh (``min_gen``) and capacity-weighted P0 base cost (``mc_base``), incumbent vs
  candidate.

The candidate is swapped into ``data/raw/_processed-legacy/`` for the second build only
and the incumbent bytes are restored in ``finally`` (each build runs in its own process).
Nothing is solved.

Run: ``python3 scripts/probes/_pjmnext25_coalrows_fleet_delta.py <candidate.csv> <year> ...``
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/pjmnext16_A_span"
ART = REPO / "data/raw/_processed-legacy/thermal_tranches_PJM.csv"
OUT = REPO / "results/phase0/pjm/_pjmnext25_coalrows_fleet_delta.json"
TRANCHES = ("mustrun", "sync", "committed", "econ", "peak")


def _tranche(uid: str) -> str:
    """Tranche token of an LP unit id (econ slices collapse to ``econ``)."""
    tail = uid.rsplit("_", 1)[-1]
    for t in TRANCHES:
        if tail.startswith(t):
            return t
    return "other"


def build(year: int, npz: Path) -> None:
    """Child process: rebuild the keeper fleet for ``year`` and save its arrays."""
    sys.path.insert(0, str(REPO))
    from scripts.lib import bundle_fleet as BF
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    logging.disable(logging.CRITICAL)
    BF.ensure_probe_path()
    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = BF.full_run_year_kwargs(meta)
    kw["pjm_da_virtual_bids"] = False
    st = run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        BF.bundle_gas_price(meta, year),
        **kw,
        **derived_run_year_inputs(BUNDLE, year),
    )
    fa = st["fleet_arrays"]
    av = np.asarray(fa.availability, float)
    if av.shape[0] != len(fa.unit_ids):
        av = av.T
    mc = np.asarray(st["mc_base"], float)
    if mc.ndim == 2 and mc.shape[0] != len(fa.unit_ids):
        mc = mc.T
    np.savez(
        npz,
        unit=np.asarray(fa.unit_ids).astype(str),
        plant=np.asarray(fa.plant_code).astype(int),
        pmax=np.asarray(fa.pmax, float),
        avail=(np.asarray(fa.pmax, float)[:, None] * av).sum(axis=1),
        min_gen=np.asarray(fa.min_gen, float).sum(axis=1),
        mc=mc.mean(axis=1) if mc.ndim == 2 else mc,
    )


def _run(year: int, tag: str) -> dict:
    """Spawn one build and load its arrays."""
    npz = REPO / f"results/phase0/pjm/_pjmnext25_fleet_{tag}_{year}.npz"
    subprocess.run(
        [sys.executable, __file__, "--child", str(year), str(npz)], check=True, cwd=REPO
    )
    d = dict(np.load(npz))
    npz.unlink()
    return d


def compare(year: int, cand: Path, added: set[int]) -> dict:
    """Incumbent vs candidate fleet for one year."""
    base = _run(year, "base")
    keep = ART.read_bytes()
    try:
        shutil.copyfile(cand, ART)
        arm = _run(year, "arm")
    finally:
        ART.write_bytes(keep)
    ub, ua = list(base["unit"]), list(arm["unit"])
    ib, ia = {u: i for i, u in enumerate(ub)}, {u: i for i, u in enumerate(ua)}
    moved = []
    for u in sorted(set(ub) | set(ua)):
        a, b = ia.get(u), ib.get(u)
        same = (
            a is not None
            and b is not None
            and np.isclose(arm["pmax"][a], base["pmax"][b])
            and np.isclose(arm["min_gen"][a], base["min_gen"][b])
            and np.isclose(arm["mc"][a], base["mc"][b])
        )
        if not same:
            moved.append(u)
    plant_of = {**dict(zip(ub, base["plant"])), **dict(zip(ua, arm["plant"]))}
    foreign = [u for u in moved if int(plant_of[u]) not in added]
    foreign_delta = {
        u: {
            k: round(float(arm[k][ia[u]] - base[k][ib[u]]), 3)
            for k in ("pmax", "min_gen", "mc")
        }
        for u in foreign
        if u in ia and u in ib
    }
    plants: dict = {}
    for tag, d in (("incumbent", base), ("candidate", arm)):
        for i, u in enumerate(d["unit"]):
            pc = int(d["plant"][i])
            if pc not in added or "COAL" not in u:
                continue
            rec = plants.setdefault(str(pc), {}).setdefault(
                tag, {**{t: 0.0 for t in TRANCHES}, "floor_gwh": 0.0, "capmc": 0.0}
            )
            t = _tranche(u)
            if t in rec:
                rec[t] += float(d["pmax"][i])
            rec["floor_gwh"] += float(d["min_gen"][i]) / 1e3
            rec["capmc"] += float(d["pmax"][i]) * float(d["mc"][i])
    for v in plants.values():
        for rec in v.values():
            cap = sum(rec[t] for t in TRANCHES)
            rec["offer_capwtd"] = round(rec.pop("capmc") / cap, 2) if cap else None
            for k in list(rec):
                if isinstance(rec[k], float):
                    rec[k] = round(rec[k], 1)
    tot = {
        tag: round(
            sum(v.get(tag, {}).get("floor_gwh", 0.0) for v in plants.values()) / 1e3, 3
        )
        for tag in ("incumbent", "candidate")
    }
    return {
        "units_moved": len(moved),
        "foreign_units_moved": foreign,
        "foreign_delta": foreign_delta,
        "floor_twh_added_plants": tot,
        "plants": plants,
    }


def main() -> None:
    """Every requested year; write the JSON artifact."""
    if sys.argv[1] == "--child":
        build(int(sys.argv[2]), Path(sys.argv[3]))
        return
    import pandas as pd

    cand = Path(sys.argv[1])
    old = pd.read_csv(ART)
    new = pd.read_csv(cand)
    assert cand.read_bytes().startswith(ART.read_bytes()), "not a byte-prefix append"
    added = set(new.plant_code.iloc[len(old) :].astype(int))
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    res["added_plants"] = sorted(added)
    for year in (int(a) for a in sys.argv[2:]):
        rec = compare(year, cand, added)
        res[str(year)] = rec
        print(
            year,
            rec["units_moved"],
            "foreign:",
            len(rec["foreign_units_moved"]),
            rec["floor_twh_added_plants"],
            flush=True,
        )
        OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
