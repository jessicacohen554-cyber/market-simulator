"""PJM-NEXT-16 zero-LP: which LP units does one flag add to the keeper's fleet?

``fleet_only`` rebuild of the keeper recipe (the ``_pjmnext13_fleet_dump`` path, fidelity
guard on) with ``--set key=value`` overrides routed exactly as ``replay_keeper --set``
does (``prb_overrides`` + the top-level kwarg). Compares the rebuilt fleet with the
committed keeper rebuild ``<scratch>/pjmnext13_fleet_<year>.npz`` and prints the plants
added/removed with pmax and available MWh. Nothing here changes a solve.

Run: ``python3 scripts/probes/_pjmnext16_fleet_delta.py <scratch> <year> key=value ...``
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts/probes"))
from scripts.lib import bundle_fleet as BF  # noqa: E402

BUNDLE = REPO / "results/calibration/pjmnext8_xf_span"


def _parse(v: str):
    """Parse an override value (JSON where possible)."""
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return v


def rebuild(year: int, sets: dict) -> dict:
    """Rebuild the keeper fleet for ``year`` with ``sets`` overrides; return arrays."""
    BF.ensure_probe_path()
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = BF.full_run_year_kwargs(meta)
    kw["pjm_da_virtual_bids"] = False
    kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), **sets}
    import inspect

    params = set(inspect.signature(run_year).parameters)
    for k, v in sets.items():
        if k in kw or k in params:  # replay_keeper --set routes both channels
            kw[k] = v
    state = run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        BF.bundle_gas_price(meta, year),
        **kw,
        **derived_run_year_inputs(BUNDLE, year),
    )
    fa = state["fleet_arrays"]
    av = np.asarray(fa.availability, float)
    if av.shape[0] != len(fa.unit_ids):
        av = av.T
    return {
        "plant_code": np.asarray(fa.plant_code).astype(str),
        "plant_group": np.asarray(fa.plant_group, dtype=object),
        "pmax": np.asarray(fa.pmax, float),
        "avail_mwh": (np.asarray(fa.pmax, float)[:, None] * av).sum(axis=1),
        "flags": {k: getattr(state["config"], k, None) for k in sets},
    }


def main() -> None:
    """Print the plant-level delta against the keeper rebuild."""
    logging.disable(logging.CRITICAL)
    scratch, year = Path(sys.argv[1]), int(sys.argv[2])
    sets = dict(a.split("=", 1) for a in sys.argv[3:])
    sets = {k: _parse(v) for k, v in sets.items()}
    base = np.load(scratch / f"pjmnext13_fleet_{year}.npz", allow_pickle=True)
    arm = rebuild(year, sets)
    bp = base["plant_code"].astype(str)
    bmw = {p: base["pmax"][bp == p].sum() for p in set(bp)}
    amw = {p: arm["pmax"][arm["plant_code"] == p].sum() for p in set(arm["plant_code"])}
    rows = []
    for p in sorted(set(bmw) | set(amw)):
        d = amw.get(p, 0.0) - bmw.get(p, 0.0)
        if abs(d) > 0.5:
            m = arm["plant_code"] == p
            grp = sorted(set(arm["plant_group"][m])) if m.any() else ["(removed)"]
            rows.append(
                (p, grp, round(d, 1), round(arm["avail_mwh"][m].sum() / 1e6, 2))
            )
    print(
        json.dumps(
            {"year": year, "sets": sets, "config": arm["flags"], "delta": rows},
            default=str,
        )
    )


if __name__ == "__main__":
    main()
