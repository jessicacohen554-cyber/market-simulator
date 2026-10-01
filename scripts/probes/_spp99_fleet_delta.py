"""SPP-99 (zero LP): LP-input delta of the CEMS->EIA remap re-derives on the SPP keeper.

Record: ``docs/records/spp/PRECOMMIT-spp-99-remap-rederive-2026-09-28.md``.

Rebuilds keeper ``results/calibration/spp98_remap_span``'s fleet ``fleet_only`` for one year with
a chosen set of SPP artifacts swapped for their re-derivations under the SPP-98 remap rows, and
writes the per-row fleet arrays needed to difference arms. Each arm runs in its own process
(the loaders are ``lru_cache``-d), and the swap is an overlay directory -- every committed file
symlinked, the arm's files replaced -- pointed at through the two module-level roots the solve
reads (``campd_bins.PROCESSED_DIR``, ``outages.UNIT_OUTAGE_CSV``). Solves nothing.

Arms (letters combine): ``O`` the standard unit-outage extract
(``campd-unit-outages-netloadmask-SPP.csv``), ``T`` the tranche rows of the remapped
facilities spliced into the committed ``thermal_tranches_SPP.csv``, ``H`` the remapped
facilities' rows spliced into ``campd_cc_heat_rates_SPP.csv``. ``control`` swaps nothing. ``F``
sets ``ScenarioConfig.campd_split_remap_companions`` instead of swapping a file -- the
committed companion through the real resolver; it must reproduce ``O`` byte-for-byte.

Usage: ``python scripts/probes/_spp99_fleet_delta.py --year 2024 --arm O --rd <dir> --out <npz>``
       ``python scripts/probes/_spp99_fleet_delta.py --compare <control.npz> <arm.npz>``
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

BUNDLE = REPO_ROOT / "results/calibration/spp98_remap_span"
RAW = REPO_ROOT / "data/raw"
PROC = RAW / "_processed-legacy"
#: Every facility code on either side of the SPP-98 remap rows.
REMAP_CODES = frozenset({1416, 56565, 3006, 55655, 762, 7546, 63628, 2953})
ARRAYS = ("availability", "min_gen", "pmax", "pmin", "heat_rate", "vom")


def _overlay(src: Path, dst: Path, swaps: dict[str, Path]) -> None:
    """Symlink every file of ``src`` into ``dst``, with ``swaps`` (name -> path) replaced."""
    for p in src.iterdir():
        if p.is_file():
            (dst / p.name).symlink_to(swaps.get(p.name, p))


def _splice(committed: Path, rederived: Path, key: str, out: Path) -> Path:
    """Committed rows outside ``REMAP_CODES`` + re-derived rows inside, committed columns only."""
    a = pd.read_csv(committed)
    b = pd.read_csv(rederived)
    keep = a[~a[key].isin(REMAP_CODES)]
    new = b[b[key].isin(REMAP_CODES)][list(a.columns)]
    pd.concat([keep, new], ignore_index=True).to_csv(out, index=False)
    return out


def build(year: int, arm: str, rd: Path) -> dict:
    """``fleet_only`` reconstruction of the keeper year under ``arm``."""
    from market_sim.data import outages
    from market_sim.data.fleet import campd_bins
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    tmp = Path(tempfile.mkdtemp(prefix="spp99_"))
    raw_ov, proc_ov = tmp / "raw", tmp / "proc"
    raw_ov.mkdir()
    proc_ov.mkdir()
    raw_swaps: dict[str, Path] = {}
    proc_swaps: dict[str, Path] = {}
    if "O" in arm:
        n = "campd-unit-outages-netloadmask-SPP.csv"
        raw_swaps[n] = rd / n
    if "T" in arm:
        n = "thermal_tranches_SPP.csv"
        proc_swaps[n] = _splice(PROC / n, rd / n, "plant_code", tmp / n)
    if "H" in arm:
        n = "campd_cc_heat_rates_SPP.csv"
        proc_swaps[n] = _splice(PROC / n, rd / "hr_cc.csv", "plant_code", tmp / n)
    _overlay(RAW, raw_ov, raw_swaps)
    _overlay(PROC, proc_ov, proc_swaps)
    if arm == "F":
        from market_sim.config.scenarios import ScenarioConfig

        orig = ScenarioConfig.__post_init__

        def _patched(self):
            orig(self)
            object.__setattr__(self, "campd_split_remap_companions", True)

        ScenarioConfig.__post_init__ = _patched
        st, _ = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
        assert st["config"].campd_split_remap_companions is True
        return st
    if arm != "control":
        outages.UNIT_OUTAGE_CSV = raw_ov / outages.UNIT_OUTAGE_CSV.name
        campd_bins.PROCESSED_DIR = proc_ov
    st, _ = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
    return st


def dump(st: dict, out: Path) -> None:
    """Write the fleet arrays + per-row identity to ``out`` (npz)."""
    fa = st["fleet_arrays"]
    arrs = {
        k: np.asarray(getattr(fa, k))
        for k in ARRAYS
        if getattr(fa, k, None) is not None
    }
    arrs["plant_code"] = np.array([int(g.plant_code) for g in st["fleet"]])
    arrs["group"] = np.array([str(g.plant_group or g.fuel_type) for g in st["fleet"]])
    np.savez_compressed(out, **arrs)


def compare(c_path: Path, a_path: Path) -> dict:
    """Per-plant availability-energy / floor / heat-rate deltas, arm minus control."""
    c, a = np.load(c_path), np.load(a_path)
    res: dict = {"row_aligned": bool(np.array_equal(c["plant_code"], a["plant_code"]))}
    if not res["row_aligned"]:
        return res
    e0 = c["pmax"][:, None] * c["availability"]
    e1 = a["pmax"][:, None] * a["availability"]
    d_av = (e1 - e0).sum(1) / 1e3
    mg0 = c["min_gen"] if c["min_gen"].ndim == 2 else c["min_gen"][:, None]
    mg1 = a["min_gen"] if a["min_gen"].ndim == 2 else a["min_gen"][:, None]
    d_mg = (mg1 - mg0).sum(1) / 1e3
    res["identical"] = {
        k: bool(np.array_equal(c[k], a[k])) for k in ARRAYS if k in c.files
    }
    rows = []
    for i in np.flatnonzero(
        (np.abs(d_av) > 1e-9)
        | (np.abs(d_mg) > 1e-9)
        | (c["heat_rate"] != a["heat_rate"])
        | (c["pmin"] != a["pmin"])
    ):
        rows.append(
            {
                "plant": int(c["plant_code"][i]),
                "group": str(c["group"][i]),
                "pmax": round(float(c["pmax"][i]), 1),
                "d_avail_gwh": round(float(d_av[i]), 2),
                "mean_avail": [
                    round(float(c["availability"][i].mean()), 4),
                    round(float(a["availability"][i].mean()), 4),
                ],
                "d_min_gen_gwh": round(float(d_mg[i]), 2),
                "min_gen_gwh": [
                    round(float(mg0[i].sum() / 1e3), 2),
                    round(float(mg1[i].sum() / 1e3), 2),
                ],
                "heat_rate": [
                    round(float(c["heat_rate"][i]), 4),
                    round(float(a["heat_rate"][i]), 4),
                ],
                "pmin": [round(float(c["pmin"][i]), 2), round(float(a["pmin"][i]), 2)],
            }
        )
    res["rows"] = rows
    res["outside_remap"] = sorted({r["plant"] for r in rows} - REMAP_CODES)
    res["d_avail_twh"] = round(float(d_av.sum() / 1e3), 4)
    res["d_min_gen_twh"] = round(float(d_mg.sum() / 1e3), 4)
    return res


def main() -> None:
    """Build one arm, or compare two dumps."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int)
    ap.add_argument("--arm", default="control")
    ap.add_argument("--rd", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--compare", nargs=2, type=Path)
    a = ap.parse_args()
    if a.compare:
        print(json.dumps(compare(*a.compare), indent=1))
        return
    dump(build(a.year, a.arm, a.rd), a.out)


if __name__ == "__main__":
    main()
