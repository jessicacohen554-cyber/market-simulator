"""SPP-48 phase 0 step 3 (ZERO LP): does the mid-vintage-year exit carry REACH the LP?

The gate on whether this lane spends any LP at all. The repair
(``ScenarioConfig.mid_vintage_exit_carry``, ``data/fleet/eia860.py::
_mid_vintage_exit_rows``) re-injects a plant that a year-matched native EIA-860
vintage drops from BOTH its sheets because it retired DURING that year -- for
SPP, Oklaunion (plant 127, 650 MW summer, EIA retirement 9/2020, 1,209.2 GWh
metered by CAMPD over May-September 2020).

An injected unit only moves a solve if it is in the fleet AND has availability
left. SPP-45 measured the exact opposite outcome for plant 762 (Ponca): present
in the fleet, but behind an availability array IDENTICALLY ZERO in all 8,760
hours, so 0.000 MWh moved. That is the most likely way this lane ends too, it
ends cleanly, and it costs no LP to find out -- which is what this probe is for.

Method: ``run_year(..., fleet_only=True)`` on the bundle's OWN recipe through
``replay_keeper.run_year_kwargs`` (the only sanctioned fleet-only
reconstruction), control vs arm, and diff every ``FleetArrays`` LP input.

**THE lru_cache TRAP (SPP-45 trap (b)) -- why each leg runs in its OWN
process.** ``outages.unit_outage_derate_factors`` is ``@lru_cache``d on its
ARGUMENTS, never on file CONTENTS, and the fleet builders carry their own
directory-keyed caches (``_chp_by_plant``, ``cod_ramp._load_cod_map``). An
arm/control pair run in ONE interpreter can therefore return a delta of exactly
0.000 that is indistinguishable from a real null. The ``--leg`` mode exists so
the driver forks a fresh interpreter per leg.

**Unit-id trap (SPP-45 trap (a)).** SPP unit ids come in TWO shapes --
``<CLASS>_<zone>_p<plant>_<tranche>`` and ``<plant>_<unit>``. A
``startswith("127_")`` test loses ~57 % of plant codes and reports Oklaunion
ABSENT in 2019, destroying this lane's central contrast. Both are matched.

Run: ``PYTHONPATH=src python3 scripts/probes/_spp48_midvintage_fleet_reach.py``
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

RUNG = "spp43_holdout_span"      # 2019-2022, committed with dispatch/
KEEPER = "spp42_span_a"          # 2023-2025, the designated keeper
OKLAUNION = 127

#: ``FleetArrays`` fields that are LP inputs (the SPP-45 footprint list).
LP_INPUT_FIELDS = (
    "pmax", "pmin", "heat_rate", "vom", "emission_rate", "nox_rate", "so2_rate",
    "zone_idx", "fuel_type_idx", "availability", "efficiency_bin", "plant_code",
    "min_gen", "min_gen_mechanism",
)


def _has_plant(unit_id: str, code: int) -> bool:
    """Match a plant code in EITHER SPP unit-id convention."""
    for part in str(unit_id).split("_"):
        if part.isdigit() and int(part) == code:
            return True
        if len(part) > 1 and part[0] == "p" and part[1:].isdigit() and int(part[1:]) == code:
            return True
    return False


def _hash(x) -> str:
    if x is None:
        return "None"
    a = np.ascontiguousarray(np.asarray(x))
    if a.dtype == object:
        a = np.asarray([str(v) for v in a.ravel()]).astype("U")
    return hashlib.sha256(a.tobytes()).hexdigest()[:16]


def leg(bundle: str, year: int, armed: bool) -> dict:
    """One leg, in THIS process. The driver forks one interpreter per call."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    b = REPO / "results/calibration" / bundle
    meta = json.loads((b / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(b, year))
    if armed:
        # The generic ScenarioConfig override bag -- the same channel SPP's
        # keeper uses to carry eia860_vintage_tracks_solve_year.
        ov = dict(kw.get("prb_overrides") or {})
        ov["mid_vintage_exit_carry"] = True
        kw["prb_overrides"] = ov

    fa = run_year(
        year, meta["iso"], 8760, float(meta["gas_prices"][str(year)]), {},
        fleet_only=True, **kw,
    )["fleet_arrays"]

    ids = [str(v) for v in fa.unit_ids]
    idx = [i for i, v in enumerate(ids) if _has_plant(v, OKLAUNION)]
    av = np.asarray(fa.availability, dtype=float)
    pm = np.asarray(fa.pmax, dtype=float)

    out: dict = {
        "bundle": bundle, "year": year, "armed": armed,
        "n_units": len(ids),
        "hashes": {f: _hash(getattr(fa, f, None)) for f in LP_INPUT_FIELDS},
        "fleet_pmax_sum": float(pm.sum()),
        "fleet_avail_energy_mwh": float((av * pm[:, None]).sum()) if av.ndim == 2 else None,
        "oklaunion": {"present": bool(idx), "unit_ids": [ids[i] for i in idx],
                      "pmax_sum": float(pm[idx].sum()) if idx else 0.0},
    }
    if idx and av.ndim == 2:
        sub = av[idx, :]
        rowpm = pm[idx]
        out["oklaunion"].update({
            "avail_all_zero": bool(np.all(sub == 0.0)),
            "avail_max": float(sub.max()),
            "avail_mean": float(sub.mean()),
            "live_hours_any_unit": int(np.count_nonzero(sub.max(axis=0) > 0.0)),
            "available_energy_mwh": float((sub * rowpm[:, None]).sum()),
            # Month-by-month, which is the whole claim: on May-September and
            # off otherwise. Hour 0 = Jan 1 00:00.
            "monthly_live_hours": _monthly(sub.max(axis=0) > 0.0, year),
            "monthly_available_gwh": _monthly_energy(sub, rowpm, year),
        })
    return out


def _month_index(year: int) -> np.ndarray:
    import pandas as pd
    h = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    return np.asarray(h.month)


def _monthly(mask: np.ndarray, year: int) -> dict:
    m = _month_index(year)[: len(mask)]
    return {int(k): int(np.count_nonzero(mask[m == k])) for k in range(1, 13)}


def _monthly_energy(sub: np.ndarray, rowpm: np.ndarray, year: int) -> dict:
    m = _month_index(year)[: sub.shape[1]]
    e = (sub * rowpm[:, None]).sum(axis=0)
    return {int(k): round(float(e[m == k].sum()) / 1000.0, 1) for k in range(1, 13)}


def _fork(bundle: str, year: int, armed: bool) -> dict:
    cmd = [sys.executable, __file__, "--leg", bundle, str(year), "1" if armed else "0"]
    env_note = f"{bundle} {year} armed={armed}"
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO))
    marker = "<<<JSON>>>"
    if marker not in r.stdout:
        raise SystemExit(f"leg failed ({env_note}):\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return json.loads(r.stdout.split(marker, 1)[1])


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--leg":
        res = leg(sys.argv[2], int(sys.argv[3]), sys.argv[4] == "1")
        print("<<<JSON>>>" + json.dumps(res))
        return

    plan = [(RUNG, y) for y in (2019, 2020, 2021, 2022)] + [(KEEPER, y) for y in (2023, 2024, 2025)]
    results = []
    for bundle, year in plan:
        ctl = _fork(bundle, year, False)
        arm = _fork(bundle, year, True)
        moved = [f for f in LP_INPUT_FIELDS if ctl["hashes"][f] != arm["hashes"][f]]
        results.append({"year": year, "bundle": bundle, "ctl": ctl, "arm": arm, "moved": moved})
        print(f"\n{'='*84}\n{year}  ({bundle})\n{'='*84}")
        print(f"  units        ctl {ctl['n_units']:5d}   arm {arm['n_units']:5d}")
        print(f"  fleet pmax   ctl {ctl['fleet_pmax_sum']:12.3f}   arm {arm['fleet_pmax_sum']:12.3f}"
              f"   delta {arm['fleet_pmax_sum']-ctl['fleet_pmax_sum']:+.3f} MW")
        print(f"  LP inputs MOVED: {moved if moved else 'NONE (byte-identical)'}")
        print(f"  Oklaunion(127)  ctl present={ctl['oklaunion']['present']}"
              f"   arm present={arm['oklaunion']['present']}")
        if arm["oklaunion"]["present"]:
            o = arm["oklaunion"]
            print(f"     unit_ids: {o['unit_ids']}")
            print(f"     pmax_sum: {o['pmax_sum']:.3f} MW")
            print(f"     availability all-zero? {o.get('avail_all_zero')}"
                  f"   max={o.get('avail_max')}   live hours={o.get('live_hours_any_unit')}")
            print(f"     available energy: {o.get('available_energy_mwh', 0.0)/1000.0:.1f} GWh")
            print(f"     monthly live hours:    {o.get('monthly_live_hours')}")
            print(f"     monthly available GWh: {o.get('monthly_available_gwh')}")

    out = REPO / "results/calibration/_spp48_midvintage_fleet_reach.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=1))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
