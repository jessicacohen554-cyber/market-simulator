"""miso-247 ``P-3'`` — the REPAIRED pre-solve energy predictor. Zero LP.

Declared in ``ADDENDUM-miso247-B-is-LIVE-form-4-is-falsified-and-my-own-predictor-is-repaired-2026-09-09.md``
§4, **before any repaired or realised number existed**, and strictly stricter than
the ``P-3`` it replaces (published verbatim in that addendum §3):

  **(a)** ``P-3`` cleared the WHOLE committed load against fleet rows only.
  Renewables are LP decision variables (rule 3 ``[R-RENEW-VAR]``) and so are not
  in ``fleet_arrays``, so it filled 2024's load from thermal / import / nuclear /
  hydro rows while omitting the keeper's own 103.3 TWh of wind and 14.4 TWh of
  solar -- clearing ~117 TWh too deep and siting the margin far too high in the
  stack. ``P-3'`` clears against the **thermal residual the fleet rows actually
  serve**, read from the keeper's OWN committed ``class_hourly_<year>.parquet``:
  the P1 MW at each hour summed over every ``klass`` except ``wind`` and
  ``solar``. Measured, not assumed; no LP.

  **(b)** ``P-3``'s ``_class_of`` fell through to ``""`` for 664 rows / 32,247.7
  MW (``oil`` 587, ``import`` 64, ``nuclear`` 13). ``P-3'`` attributes EVERY row:
  ``plant_group`` where non-blank, else the ``FUEL_TYPE_MAP`` fuel name. No row is
  dropped and no class is excluded.

  **(c)** The bundle-side mapping ``G-1`` reads, fixed in the same addendum:
  ``COAL_PRB`` / ``COAL_BIT`` / ``COAL_LIGNITE`` / ``COAL`` -> ``COAL``; ``wind``
  and ``solar`` excluded from BOTH sides; every other ``klass`` name-for-name.

``G-1``'s bar is NOT moved: same sign, and within [1/3, 3]x the magnitude, for
every class where ``|prediction| >= 0.5`` TWh. Rule 22: the screen year (2024)
only, an in-training year.

Writes ``results/calibration/_miso247_p3prime_reclear.json``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes._miso247_p19_posture_phase0 import KEEPER, build  # noqa: E402
from market_sim.data.fleet.arrays import FUEL_TYPE_MAP  # noqa: E402

OUT = REPO / "results/calibration/_miso247_p3prime_reclear.json"
YEAR = 2024

#: Addendum 2 §4(c): excluded from BOTH the clearing target and the class
#: comparison. They are LP decision variables, not fleet rows.
NON_FLEET_KLASS = frozenset({"wind", "solar"})

#: Addendum 2 §4(c): the bundle's coal grain collapsed onto the fleet's.
COAL_KLASS = frozenset({"COAL_PRB", "COAL_BIT", "COAL_LIGNITE", "COAL"})


#: ``FUEL_TYPE_MAP`` is name -> index; the attribution needs the inverse.
_FUEL_NAME: dict[int, str] = {v: k for k, v in FUEL_TYPE_MAP.items()}


def klass_of(fleet_arrays, i: int) -> str:
    """Attribute row ``i`` to a class. Addendum 2 §4(b) -- never blank."""
    pg = getattr(fleet_arrays, "plant_group", None)
    if pg is not None:
        v = str(pg[i]).strip()
        if v:
            return v
    return _FUEL_NAME[int(fleet_arrays.fuel_type_idx[i])]


def thermal_target(year: int) -> np.ndarray:
    """The keeper's own committed P1 hourly MW over fleet-row classes."""
    frame = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    frame = frame[(frame["pass"] == "P1") & (~frame["klass"].isin(NON_FLEET_KLASS))]
    hours = int(frame["hour"].max()) + 1
    out = np.zeros(hours)
    np.add.at(out, frame["hour"].to_numpy(int), frame["mw"].to_numpy(float))
    return out


def clear(state: dict, target: np.ndarray) -> np.ndarray:
    """Merit-fill the assembled offer stack to ``target``; per-row energy (MWh)."""
    mc = np.asarray(state["mc_base"], dtype=float)
    pmax = np.asarray(state["fleet_arrays"].pmax, dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], target.size, axis=1)
    energy = np.zeros(pmax.size)
    for t in range(target.size):
        order = np.argsort(mc[:, t], kind="stable")
        cum = np.cumsum(pmax[order])
        k = int(np.searchsorted(cum, target[t]))
        energy[order[:k]] += pmax[order[:k]]
        if k < order.size:
            energy[order[k]] += max(0.0, target[t] - (cum[k - 1] if k else 0.0))
    return energy


def main() -> None:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO
    ).stdout.strip()
    target = thermal_target(YEAR)
    s_keeper = build(YEAR, screen=False, hr_floor=False)
    s_arm = build(YEAR, screen=True, hr_floor=True)
    fa = s_arm["fleet_arrays"]
    e_k, e_a = clear(s_keeper, target), clear(s_arm, target)
    by: dict[str, float] = {}
    for i in range(len(fa.pmax)):
        k = klass_of(fa, i)
        by[k] = by.get(k, 0.0) + float(e_a[i] - e_k[i]) / 1e6
    pred = {k: round(v, 4) for k, v in sorted(by.items(), key=lambda kv: -abs(kv[1]))}
    rec = {
        "probe": "_miso247_p3prime_reclear",
        "declared_in": (
            "ADDENDUM-miso247-B-is-LIVE-form-4-is-falsified-and-my-own-"
            "predictor-is-repaired-2026-09-09.md §4"
        ),
        "zero_lp": True,
        "year": YEAR,
        "provenance": {"head": head},
        "target_TWh": round(float(target.sum()) / 1e6, 4),
        "keeper_cleared_TWh": round(float(e_k.sum()) / 1e6, 4),
        "arm_cleared_TWh": round(float(e_a.sum()) / 1e6, 4),
        "P3prime_pred_TWh": pred,
        "G1_in_scope": sorted(k for k, v in pred.items() if abs(v) >= 0.5),
        "coal_klass_map": sorted(COAL_KLASS),
        "excluded_both_sides": sorted(NON_FLEET_KLASS),
    }
    OUT.write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
