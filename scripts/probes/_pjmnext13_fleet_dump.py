"""PJM-NEXT-13 zero-LP: dump the keeper's rebuilt fleet arrays for one year (no LP).

``fleet_only`` rebuild of the keeper recipe (``pjmnext8_xf_span``) through the
sanctioned, fidelity-guarded :func:`scripts.lib.bundle_fleet.reconstruct_bundle_fleet`.
Writes ``<scratch>/pjmnext13_fleet_<year>.npz`` with, per LP unit: ``unit_ids``,
``plant_code``, ``plant_group``, ``zone`` (name), ``pmax``, hourly ``availability``
(float32, 8760), hourly ``fuel_price`` and ``mc_base`` where the rebuild carries them
hourly, and ``heat_rate``. The three NEXT-13 cards read these arrays; nothing here
changes a solve.

Run: ``python3 scripts/probes/_pjmnext13_fleet_dump.py <out_dir> 2019 [...]``
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from scripts.lib import bundle_fleet as BF  # noqa: E402

BUNDLE = REPO / "results/calibration/pjmnext8_xf_span"


def _hourly(a: np.ndarray, n: int, t: int = 8760) -> np.ndarray:
    """Coerce a per-unit array to (n, t) float32 (broadcasting a per-unit scalar)."""
    a = np.asarray(a, dtype=float)
    if a.ndim == 2 and a.shape == (n, t):
        return a.astype(np.float32)
    if a.ndim == 2 and a.shape == (t, n):
        return a.T.astype(np.float32)
    if a.ndim == 1 and a.shape[0] == n:
        return np.repeat(a[:, None], t, axis=1).astype(np.float32)
    raise ValueError(f"unexpected shape {a.shape} for n={n}")


def _rebuild(year: int) -> dict:
    """``reconstruct_bundle_fleet`` with ONE override: ``pjm_da_virtual_bids`` off.

    The DA virtual INC/DEC units are demand-side LP rows (``VIRTUAL_*`` groups) that
    carry no availability, fuel price or offer for any physical unit, and their
    gitignored corpus is not needed to read the physical fleet (the
    ``_pjmnext8_exitfix_avail_delta.py`` precedent). Every other recorded flag is
    carried and the fidelity guard still runs.
    """
    import json

    BF.ensure_probe_path()
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = BF.full_run_year_kwargs(meta)
    kw["pjm_da_virtual_bids"] = False
    state = run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        BF.bundle_gas_price(meta, year),
        **kw,
        **derived_run_year_inputs(BUNDLE, year),
    )
    BF.assert_reconstruction_fidelity(
        meta, state["config"], BF.DEFAULT_REQUIRED_FLAGS, BF.DEFAULT_REQUIRED_SEQUENCES
    )
    return state


def dump(year: int, out_dir: Path) -> Path:
    """Rebuild ``year`` and write the npz."""
    state = _rebuild(year)
    fa = state["fleet_arrays"]
    n = len(fa.unit_ids)
    zones = list(state["config"].zones) if hasattr(state["config"], "zones") else None
    zidx = np.asarray(fa.zone_idx, int)
    zname = (
        np.asarray([zones[i] for i in zidx], dtype=object)
        if zones
        else zidx.astype(str).astype(object)
    )
    arrs = {
        "unit_ids": np.asarray(fa.unit_ids, dtype=object),
        "plant_code": np.asarray(fa.plant_code).astype(str).astype(object),
        "plant_group": np.asarray(fa.plant_group, dtype=object),
        "zone": zname,
        "pmax": np.asarray(fa.pmax, float),
        "heat_rate": np.asarray(fa.heat_rate, float),
        "availability": _hourly(fa.availability, n),
    }
    for key in ("fuel_prices", "mc_base"):
        v = state.get(key)
        if v is not None:
            try:
                arrs[key] = _hourly(v, n)
            except ValueError as e:
                print(f"  {key}: {e}", flush=True)
    dest = out_dir / f"pjmnext13_fleet_{year}.npz"
    np.savez_compressed(dest, **arrs, allow_pickle=True)
    print(f"{year}: {n} units -> {dest}", flush=True)
    return dest


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for y in [int(a) for a in sys.argv[2:]]:
        dump(y, out)
