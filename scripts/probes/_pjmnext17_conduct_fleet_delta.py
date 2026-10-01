"""PJM-NEXT-17 zero-LP: what does ``cc_mustrun_conduct_window`` do to the keeper's floors?

Two ``fleet_only`` rebuilds of the keeper recipe (bundle ``pjmnext16_A_span``, the
``_pjmnext16_fleet_delta`` path), with the flag off and on. Compares the per-generator
``min_gen`` / ``min_gen_mechanism`` arrays: only MECH_CC_MUSTRUN_PER_PLANT rows may move,
floored-hour counts per plant must be unchanged, and the floored MWh in hours the plant's
bench CAMPD meter reads offline (< 1 % nameplate) is reported off vs on. Nothing is solved.

Run: ``python3 scripts/probes/_pjmnext17_conduct_fleet_delta.py <year> [<year> ...]``
"""

from __future__ import annotations

import base64
import gzip
import json
import logging
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts/probes"))
import _pjmnext16_fleet_delta as FD  # noqa: E402

FD.BUNDLE = REPO / "results/calibration/pjmnext16_A_span"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
OUT = REPO / "results/phase0/pjm/_pjmnext17_conduct_fleet_delta.json"
MECH_CC = None


def _floors(year: int, armed: bool) -> dict:
    """Rebuild and return the floor arrays plus unit identity."""
    from scripts.lib import bundle_fleet as BF
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    BF.ensure_probe_path()
    meta = json.loads((FD.BUNDLE / "meta.json").read_text())
    kw = BF.full_run_year_kwargs(meta)
    kw["pjm_da_virtual_bids"] = False
    kw["prb_overrides"] = {
        **(kw.get("prb_overrides") or {}),
        "cc_mustrun_conduct_window": armed,
    }
    st = run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        BF.bundle_gas_price(meta, year),
        **kw,
        **derived_run_year_inputs(FD.BUNDLE, year),
    )
    fa = st["fleet_arrays"]
    return {
        "armed": bool(getattr(st["config"], "cc_mustrun_conduct_window", False)),
        "unit": np.asarray(fa.unit_ids).astype(str),
        "plant": np.asarray(fa.plant_code).astype(str),
        "group": np.asarray(fa.plant_group).astype(str),
        "min_gen": np.asarray(fa.min_gen, float),
        "mech": np.asarray(fa.min_gen_mechanism),
    }


def _offline(year: int) -> dict[str, np.ndarray]:
    """Bench CC_REGULAR offline masks (< 1 % nameplate), by plant code."""
    b = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]["plants"]
    out = {}
    for pid, bp in b.items():
        if bp.get("group") != "CC_REGULAR" or bp.get("nodata") or not bp.get("campd"):
            continue
        raw = np.frombuffer(base64.b64decode(bp["campd"]), dtype=np.uint8)
        if raw.size == 8760:
            out[str(pid).split(":")[0]] = raw < 1
    return out


def main() -> None:
    """Report per year; write the JSON artifact."""
    from market_sim.data.floor_mechanisms import MECH_CC_MUSTRUN_PER_PLANT

    logging.disable(logging.CRITICAL)
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    for year in (int(a) for a in sys.argv[1:]):
        off, on = _floors(year, False), _floors(year, True)
        assert not off["armed"] and on["armed"]
        assert (off["unit"] == on["unit"]).all()
        moved = np.where((off["min_gen"] != on["min_gen"]).any(axis=1))[0]
        cc_rows = (off["mech"] == MECH_CC_MUSTRUN_PER_PLANT).any(axis=1) | (
            on["mech"] == MECH_CC_MUSTRUN_PER_PLANT
        ).any(axis=1)
        foreign = [off["unit"][i] for i in moved if not cc_rows[i]]
        hrs_off = (off["mech"] == MECH_CC_MUSTRUN_PER_PLANT).sum()
        hrs_on = (on["mech"] == MECH_CC_MUSTRUN_PER_PLANT).sum()
        dark = _offline(year)
        mwh = {"off": 0.0, "on": 0.0}
        for i in np.where(cc_rows)[0]:
            m = dark.get(off["plant"][i])
            if m is None:
                continue
            for k, a in (("off", off), ("on", on)):
                f = (a["mech"][i] == MECH_CC_MUSTRUN_PER_PLANT) & m
                mwh[k] += float(a["min_gen"][i][f].sum())
        rec = {
            "rows_moved": int(moved.size),
            "cc_floor_rows": int(cc_rows.sum()),
            "non_cc_rows_moved": foreign,
            "cc_floor_hours_off_on": [int(hrs_off), int(hrs_on)],
            "cc_floor_mwh_off_on": [
                round(float(off["min_gen"][cc_rows].sum()) / 1e6, 3),
                round(float(on["min_gen"][cc_rows].sum()) / 1e6, 3),
            ],
            "floor_twh_in_metered_offline_hours_off_on": [
                round(mwh["off"] / 1e6, 3),
                round(mwh["on"] / 1e6, 3),
            ],
        }
        res[str(year)] = rec
        print(year, json.dumps(rec), flush=True)
        OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
