"""miso-266 — A/B the DISPATCHED-bin denominator on the ceiling contradiction, ZERO LP.

FINDING-miso265 §2.2 measures the object this probe scores: the hours in which
the plant's own committed CAMPD meter sits ABOVE the LP's hard upper bound
``sum_g pmax[g] * availability[g, t]`` -- 20-32 TWh/yr across 2020-2025, every
hour of it an hour the solved dispatch could not have reproduced at any price.

The candidate is ``ScenarioConfig.unit_outage_dispatched_bin_denominator``
(miso-266): take the derate denominator from the capacity the derate multiplier
is APPLIED to, instead of from ``outages._iso_plant_capacity``'s independently
reconstructed map. It is chosen on the construction -- the accumulator's own
stated invariant -- and NOT on this number (rule 1 ``[R-STRUCT]``); the number
exists so the blast radius is stated before a solve, not to select the repair.

Both legs rebuild the SAME year's fleet from the SAME keeper recipe with
``fleet_only=True``, differing in exactly one flag, so the delta is provably
that flag. The partition fields are taken from each year's OWN
``run_config_<year>.json`` (RESULT-miso263 §3), so 2023-2025 measure the leg the
keeper actually solved.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib.bundle_fleet import (  # noqa: E402
    bundle_gas_price,
    full_run_year_kwargs,
)
from scripts.probes._miso265_ceiling_vs_meter_hourly import decode_plant_mw  # noqa: E402
from scripts.probes._miso265_coal_availability_ceiling import (  # noqa: E402
    COAL_CLASSES,
    _PARTITION_FIELDS,
    load_bench,
)

#: Decode step tolerance, in QUANTIZATION STEPS. The committed per-plant series
#: is ``_b64`` uint8 percent-of-capacity, so one step is ``npl / 100`` MW and a
#: breach under one step is codec noise (FINDING-miso265 §2.3).
TOL_STEPS = 1.0


def _leg_meta(bundle: Path, year: int) -> dict:
    """The span ``meta.json`` with ``year``'s OWN partition values substituted.

    The span meta carries the 2020 leg's values for MISO's two partition
    fields, so reconstructing a 2023+ year straight off it measures a fleet the
    keeper never solved (RESULT-miso263 §3). Each year's own
    ``run_config_<year>.json`` records what that leg actually solved, so the
    substitution is a read, never a guess.
    """
    meta = json.loads((bundle / "meta.json").read_text())
    sc = json.loads((bundle / f"run_config_{year}.json").read_text())["scenario_config"]
    for field in _PARTITION_FIELDS:
        if field in sc:
            meta[field] = sc[field]
    return meta


def _ceiling(bundle: Path, year: int, armed: bool) -> dict[str, np.ndarray]:
    """Per-coal-plant ``sum_g pmax * availability`` for one leg of the A/B."""
    from scripts.run_calibration import run_year

    meta = _leg_meta(bundle, year)
    kwargs = full_run_year_kwargs(meta)
    kwargs["unit_outage_dispatched_bin_denominator"] = armed
    state = run_year(
        year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, year), **kwargs
    )
    fa = state["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    codes = np.asarray(fa.plant_code)

    from market_sim.data.fleet import FUEL_TYPE_MAP

    is_coal = np.asarray(fa.fuel_type_idx) == FUEL_TYPE_MAP["coal"]
    out: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(avail.shape[1]))
    for i in np.nonzero(is_coal)[0]:
        out[str(codes[i])] += pmax[i] * avail[i]
    return dict(out)


def _score(ceiling: dict[str, np.ndarray], bench: dict) -> tuple[float, int, int]:
    """``(infeasible TWh, plant-hours, plants)`` of meter above the ceiling.

    The TWh is the EXCESS ``meter - ceiling`` summed over breach hours — the
    energy the plant metered that the LP could not have produced — which is the
    quantity FINDING-miso265 §2.2 tabulates (2020: 25.414 TWh), not the whole
    metered energy of those hours.
    """
    twh = 0.0
    ph = 0
    plants = 0
    for key, rec in bench["plants"].items():
        if rec.get("group") not in COAL_CLASSES:
            continue
        base = key.split(":")[0]
        c = ceiling.get(base)
        if c is None:
            continue
        m = decode_plant_mw(rec, key)
        if m is None:
            continue
        n = min(len(c), len(m))
        tol = TOL_STEPS * float(rec.get("npl") or 0.0) / 100.0
        exc = m[:n] - c[:n]
        bad = exc > tol
        if bad.any():
            plants += 1
            ph += int(bad.sum())
            twh += float(exc[bad].sum()) / 1e6
    return twh, ph, plants


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/miso264_anchor_span")
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--years", type=int, nargs="+", default=[2020])
    args = ap.parse_args()

    bundle = REPO / args.bundle
    print(f"=== {args.iso} — dispatched-bin denominator A/B on the METER-ABOVE-CEILING object ===")
    print(f"fleet: {args.bundle}   tolerance: {TOL_STEPS:g} decode step(s)   ZERO LP")
    print()
    hdr = (
        f"{'year':>5} | {'control TWh':>11} {'ctl p-h':>9} {'ctl pl':>6} | "
        f"{'armed TWh':>10} {'arm p-h':>9} {'arm pl':>6} | {'dTWh':>8} {'closed':>7}"
    )
    print(hdr)
    print("-" * len(hdr))
    tot_c = tot_a = 0.0
    for year in args.years:
        bench = load_bench(args.iso, year)
        c_twh, c_ph, c_pl = _score(_ceiling(bundle, year, False), bench)
        a_twh, a_ph, a_pl = _score(_ceiling(bundle, year, True), bench)
        tot_c += c_twh
        tot_a += a_twh
        closed = (1.0 - a_twh / c_twh) * 100.0 if c_twh > 0 else float("nan")
        print(
            f"{year:5d} | {c_twh:11.3f} {c_ph:9,d} {c_pl:6d} | "
            f"{a_twh:10.3f} {a_ph:9,d} {a_pl:6d} | {a_twh - c_twh:8.3f} {closed:6.1f}%"
        )
    print("-" * len(hdr))
    print(
        f"{'TOTAL':>5} | {tot_c:11.3f} {'':9} {'':6} | {tot_a:10.3f} {'':9} {'':6} | "
        f"{tot_a - tot_c:8.3f} "
        f"{(1.0 - tot_a / tot_c) * 100.0 if tot_c else float('nan'):6.1f}%"
    )
    print()
    print("  TWh = metered energy in hours the meter exceeds the LP's own hard ceiling.")
    print("  Every such hour is infeasible for the solved dispatch at ANY price.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
