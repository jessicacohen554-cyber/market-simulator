"""miso-153 addendum — does the ``st_gas_mustrun_per_plant`` floor actually
SELF-WINDOW, as its ``D4_WINDOWS`` citation claims? NO LP.

Owner decision (2026-08-12): investigate the D-4 all-hours-window question in
the MISO lane. The registry's claim
(``scripts/legitimacy_diagnostics.py:362-376``) is that the mechanism is
"self-windowing by construction — each plant's committed tranche binds only in
its top measured-``online_frac`` fraction of hours ranked by system load", with
an ALL-24-HOUR *hour-of-day* window justified by the Entergy MISO-South
VLR/self-commitment trace (Nine Mile synchronized 98.2 % of ALL hours 2023-25,
Sabine 85.6 %, Lewis Creek 87.8 %).

D-4 as implemented scores off-window binding by HOUR-OF-DAY, so for this
mechanism it tests the hour-of-day declaration and NOT the load-rank
self-windowing claim. This probe measures the claim D-4 does not reach:

  W-1  the floor's binding profile by HOUR-OF-DAY (what D-4 does score) —
       cap-weighted floored MW per hour-of-day, and the max/min ratio.
  W-2  the floor's binding profile by SYSTEM-LOAD RANK (what D-4 does NOT
       score) — floored MW by load decile. If the mechanism self-windows,
       floored MW must RISE with load rank; if it is a flat all-hours base,
       it will be level.
  W-3  the per-plant binding frequency against the cited online_frac evidence
       (98.2 / 85.6 / 87.8 %). A plant floored in ~all hours is CONSISTENT
       with the citation; a plant floored in far more hours than its cited
       synchronization would be the defect.

Reads the keeper's own committed system demand; the floor is reconstructed
through the production chain at HEAD under the keeper's own config.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds no marker.

Usage::

    PYTHONPATH=$PWD .venv/bin/python scripts/probes/_miso153_stgas_window.py
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402

BUNDLE = REPO / "results/calibration/miso148_basis_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"T-1 FAIL: keeper bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE

from _miso134_ct_night_order_screen import (  # noqa: E402
    build_year,
    keeper_config,
    keeper_prices,
)
from market_sim.data.floor_mechanisms import (  # noqa: E402
    MECH_ST_GAS_MUSTRUN_PER_PLANT,
)

OUT = REPO / "results/calibration/_miso153_stgas_window.json"
YEARS = (2023, 2024, 2025)
HOD = np.arange(8760) % 24


def run_year(year: int) -> dict:
    """Measure the ST_GAS floor's hour-of-day and load-rank binding profile."""
    cfg = dataclasses.replace(keeper_config(), weather_year=year)
    _price, demand = keeper_prices(year)
    _raw, fleet, arrays, _fp, _mc, _zn = build_year(cfg, year)

    if arrays.min_gen is None:
        return {"error": "arrays.min_gen is None — floors not composed in this "
                         "rebuild; W-1/W-2/W-3 unmeasurable"}
    mg = np.asarray(arrays.min_gen, dtype=np.float64)          # (n_gen, T)
    mech = arrays.min_gen_mechanism
    if mech is None:
        return {"error": "arrays.min_gen_mechanism is None — no attribution"}
    mech = np.asarray(mech)

    sel = mech == MECH_ST_GAS_MUSTRUN_PER_PLANT                 # (n_gen, T) bool
    floored = np.where(sel, mg, 0.0)
    tot = floored.sum(axis=0)                                   # (T,) MW

    # W-1: hour-of-day profile (what D-4 scores)
    hod = np.array([tot[HOD == h].mean() for h in range(24)])
    # W-2: system-load decile profile (what D-4 does NOT score)
    order = np.argsort(demand)
    dec = np.array_split(order, 10)
    by_decile = [float(tot[ix].mean()) for ix in dec]           # low -> high load
    # W-3: per-generator binding frequency
    rows_any = sel.any(axis=1)
    freq = sel[rows_any].mean(axis=1) if rows_any.any() else np.array([])
    uids = [u for u, k in zip(arrays.unit_ids, rows_any) if k]

    return {
        "floored_mw_mean": float(tot.mean()),
        "floored_twh": float(tot.sum() / 1e6),
        "hod_profile_mw": hod.tolist(),
        "hod_max_over_min": float(hod.max() / hod.min()) if hod.min() > 0
        else None,
        "load_decile_mw_low_to_high": by_decile,
        "decile_top_over_bottom": (by_decile[-1] / by_decile[0])
        if by_decile[0] > 0 else None,
        "n_floored_rows": int(rows_any.sum()),
        "bind_freq_min": float(freq.min()) if freq.size else None,
        "bind_freq_median": float(np.median(freq)) if freq.size else None,
        "bind_freq_max": float(freq.max()) if freq.size else None,
        "bind_freq_ge_0995": int((freq >= 0.995).sum()) if freq.size else 0,
        "example_rows": [
            {"unit": str(u), "bind_freq": float(f)}
            for u, f in sorted(zip(uids, freq), key=lambda t: -t[1])[:8]
        ],
    }


def main() -> None:
    out = {"bundle": BUNDLE.name, "years": {}}
    for y in YEARS:
        print(f"\n===== {y} =====", flush=True)
        r = run_year(y)
        out["years"][str(y)] = r
        if "error" in r:
            print("  ", r["error"])
            continue
        print(f"  floored {r['floored_mw_mean']:.0f} MW mean "
              f"({r['floored_twh']:.3f} TWh) over {r['n_floored_rows']} rows")
        print(f"  W-1 hour-of-day max/min = {r['hod_max_over_min']}")
        print(f"  W-2 load-decile top/bottom = {r['decile_top_over_bottom']}")
        print("      deciles (low->high load MW): "
              + " ".join(f"{v:.0f}" for v in r["load_decile_mw_low_to_high"]))
        print(f"  W-3 bind freq min/median/max = {r['bind_freq_min']}"
              f"/{r['bind_freq_median']}/{r['bind_freq_max']}"
              f"  rows>=99.5%: {r['bind_freq_ge_0995']}")
    OUT.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
