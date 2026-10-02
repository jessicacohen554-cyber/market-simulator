"""W0 NEISO regression tripwire, zero-LP half (closeout plan §3.2 row 4).

The NEISO keeper (``neiso119_span``) is closed; the W0 settlement must not move
it except by the ruled construction. Before any W0 shard, rebuild the keeper's
recipe ``fleet_only`` for 2019 and 2025 twice — ``recorded`` (each W0 field at
its recorded value, else its registration-time default) and ``w0`` (every W0
field armed) — and require byte-stability of the four named facts:

* Pilgrim 1590 (nuclear, retired 2019-05) and Mystic 1588 (CC, retired
  2024-05) are CARRIED with their exit timing (available energy per unit);
* Kendall 1595 CC_CHP stays on its basis (pmax, class);
* Canal 3 (1599) keeps its class.

Also reported: the fleet's mean ``mc_base`` by plant group in both postures
(the LP-input proxy of the C3a move). The C3a > 2 pp half of the tripwire needs
an LP and is read from the first W0 span (phase 3); this probe is the zero-LP
precondition. Writes ``W0-census/NEISO/neiso_tripwire_<Y>.json``.

Usage::

    python scripts/probes/_w0_neiso_tripwire.py --year 2019 --out <json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for _p in (".", "scripts", "src"):
    sys.path.insert(0, str(REPO / _p))

BUNDLE = REPO / "results/calibration/neiso119_span"
WATCH = {1590: "Pilgrim", 1588: "Mystic", 1595: "Kendall", 1599: "Canal"}


def _units(res: dict) -> dict:
    """Per watched-plant unit facts: class, pmax, available GWh."""
    fa = res["fleet_arrays"]
    pmax = np.asarray(fa.pmax, float)
    avail = np.asarray(fa.availability, float)
    out: dict[str, list] = {}
    for i, g in enumerate(res["fleet"]):
        code = int(g.plant_code)
        if code not in WATCH:
            continue
        out.setdefault(f"{code} {WATCH[code]}", []).append(
            {
                "unit": g.unit_id,
                "group": g.plant_group,
                "fuel": g.fuel_type,
                "pmax_mw": round(float(pmax[i]), 2),
                "available_gwh": round(float((pmax[i] * avail[i]).sum()) / 1e3, 3),
            }
        )
    return out


def _mc_by_group(res: dict) -> dict:
    """Capacity-weighted mean P0 marginal cost by plant group ($/MWh)."""
    mc = np.asarray(res["mc_base"], float)
    mc = mc.mean(axis=1) if mc.ndim == 2 else mc
    fa = res["fleet_arrays"]
    pmax = np.asarray(fa.pmax, float)
    groups: dict[str, list[float]] = {}
    for i, g in enumerate(res["fleet"]):
        groups.setdefault(g.plant_group or g.fuel_type, []).append(i)
    return {
        k: round(float(np.average(mc[v], weights=np.maximum(pmax[v], 1e-9))), 3)
        for k, v in sorted(groups.items())
    }


def main(argv: list[str] | None = None) -> int:
    """Run both postures for one year and write the comparison."""
    from build_fleet_census import rebuild_fleet

    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    sides = {}
    for posture in ("recorded", "w0"):
        res = rebuild_fleet(BUNDLE, args.year, posture)
        sides[posture] = {"units": _units(res), "mc_by_group": _mc_by_group(res)}
    stable = {
        k: sides["recorded"]["units"].get(k) == sides["w0"]["units"].get(k)
        for k in sorted(set(sides["recorded"]["units"]) | set(sides["w0"]["units"]))
    }
    out = {
        "year": args.year,
        "bundle": BUNDLE.name,
        "watched_plants_byte_stable": stable,
        "tripped_zero_lp": not all(stable.values()),
        **sides,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"year": args.year, "stable": stable}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
