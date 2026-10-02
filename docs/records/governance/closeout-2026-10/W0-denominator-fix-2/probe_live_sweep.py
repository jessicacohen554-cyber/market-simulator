"""Zero-LP before/after of the live dispatched-bin roster (closeout-W0 D-1, part 2).

Usage: probe_live_sweep.py <code_root> <bundle> <years,> <out.json> [overrides-json]

Rebuilds each year's fleet (``run_year(fleet_only=True)``) of a keeper bundle's
recipe at W0 posture with the ``src/`` + ``scripts/`` of ``<code_root>`` (data is
read from MARKET_SIM_DATA_ROOT), and records the hashes of every fleet array the
outage overlay feeds, available energy (sum pmax x availability) in total and
per plant, and the dispatched bins whose COD-ramp online capacity falls below
their pmax in some month (``offline_all_year``: rows the ramp masks every month,
e.g. dead exit cohorts; ``partial``: rows masked in some months only).
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "src"))
import market_sim  # noqa: E402

assert str(root) in market_sim.__file__, market_sim.__file__
from market_sim.config.paths import DATA_ROOT  # noqa: E402
from market_sim.data import cod_ramp  # noqa: E402
from scripts.build_fleet_census import rebuild_fleet  # noqa: E402

bundle, years = sys.argv[2], [int(y) for y in sys.argv[3].split(",")]
ov = json.loads(sys.argv[5]) if len(sys.argv) > 5 else None
out = {}
for y in years:
    res = rebuild_fleet(DATA_ROOT / "results/calibration" / bundle, y, "w0", ov)
    fa, fleet = res["fleet_arrays"], res["fleet"]
    pmax = np.asarray(fa.pmax, float)
    av = np.asarray(fa.availability, float)
    hashes = {}
    for name in ("availability", "pmax", "pmin", "min_gen", "mc_base"):
        v = getattr(fa, name, None)
        if v is not None:
            hashes[name] = hashlib.sha256(
                np.ascontiguousarray(np.asarray(v, float)).tobytes()
            ).hexdigest()[:16]
    energy = pmax[:, None] * av
    by_plant: dict[str, float] = {}
    for i, g in enumerate(fleet):
        k = f"{int(g.plant_code or 0)}|{g.plant_group}"
        by_plant[k] = by_plant.get(k, 0.0) + float(energy[i].sum()) / 1e6
    cod_map, unit_map = cod_ramp.load_cod_map(), cod_ramp.load_unit_cod_map()
    dead, partial = set(), set()
    for i, g in enumerate(fleet):
        if int(g.plant_code or 0) <= 0 or not g.plant_group or not pmax[i] > 0:
            continue
        m = np.asarray(
            cod_ramp.generator_online_mask(
                int(g.plant_code),
                g.plant_group,
                g.online_year,
                g.online_month,
                g.retirement_year,
                g.retirement_month,
                bool(g.is_campd_bin),
                cod_map,
                unit_map,
                y,
            )[0],
            float,
        )
        tag = f"{g.plant_code}|{g.plant_group}|{g.unit_id}"
        if not m.any():
            dead.add(tag)
        elif (m < 1.0).any():
            partial.add(tag)
    out[y] = dict(
        hashes=hashes,
        n_units=len(fleet),
        avail_twh=float(energy.sum()) / 1e6,
        by_plant_twh=by_plant,
        offline_all_year=sorted(dead),
        partial=sorted(partial),
        overrides=ov,
    )
    print(bundle, y, round(out[y]["avail_twh"], 4), hashes, flush=True)
Path(sys.argv[4]).write_text(json.dumps(out, indent=1, sort_keys=True))
