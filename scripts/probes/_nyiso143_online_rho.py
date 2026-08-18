"""nyiso-143 — measure the online-gated class-2 headroom multiplier ``rho``.

Completes the ``nyiso_synchronised_reserve`` adjudication begun in
``_nyiso143_nyc_spin_liveness.py``. That probe established, from the keeper's
own committed dispatch, that the hand-scoped ``nyc_spin_online`` family (250 MW
static, NYC zone only) is slack in every hour **iff**

    rho >= rho*   with rho* = 250 / min_t P_NYC_quickstart(t)

measured at 3.1588 / 2.8981 / 3.0152 for 2023 / 2024 / 2025.

``rho`` is not a free parameter: it is the eligible fleet's own cap-weighted
``(pmax - pmin) / pmin`` clipped to [0.5, 4.0]
(``model/reserves/spec.py``, the ``(synch and not commit_gated) or
spin_online`` branch). This probe rebuilds the keeper's fleet through
``run_year(fleet_only=True)`` — the same reconstruction the D-2/D-4
diagnostics use, NO LP — and computes it.

No solve is spent and no out-of-training year is touched.
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.legitimacy_diagnostics import REBUILD_META_RENAMES  # noqa: E402
from scripts.run_calibration import run_year  # noqa: E402
from market_sim.model.reserves.spec import (  # noqa: E402
    NYISO_DOWNSTATE_SPIN_ZONES,
    QUICK_START_FUEL_TYPES,
)
from market_sim.data.fleet import FUEL_TYPE_NAMES  # noqa: E402

BUNDLE = REPO / "results/calibration/nyiso142_stackdup"
YEARS = (2023, 2024, 2025)


def _kwargs(meta: dict) -> dict:
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    out = {}
    for k, v in meta.items():
        k2 = REBUILD_META_RENAMES.get(k, k)
        if k2 in params and k2 not in skip:
            out[k2] = v
    return out


def main() -> int:
    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = _kwargs(meta)
    gas = meta.get("gas_prices", {})
    res: dict = {"bundle": BUNDLE.name, "clip": [0.5, 4.0], "years": {}}
    for year in YEARS:
        state = run_year(
            year,
            "NYISO",
            int(meta.get("hours", 8760)),
            float(gas.get(str(year), gas.get(year, 0.0))),
            {},
            fleet_only=True,
            **kwargs,
        )
        fa = state["fleet_arrays"]
        fuel = np.array([FUEL_TYPE_NAMES[i] for i in fa.fuel_type_idx])
        quick = np.isin(fuel, sorted(QUICK_START_FUEL_TYPES))
        # The keeper arms nyiso_hydro_reserve_eligible, which unions hydro
        # into BOTH eligibility classes — so hydro rides the class-2 quick
        # set and enters rho's cap-weighted average.
        hydro_armed = bool(meta.get("nyiso_hydro_reserve_eligible", False)) or bool(
            (meta.get("coal_prb_sigmoid_overrides") or {}).get(
                "nyiso_hydro_reserve_eligible", False
            )
        )
        if hydro_armed:
            quick = quick | (fuel == "hydro")
        # The OBLIGATION branch's own eligible set (rule 19 sibling
        # nyiso_incity_commitment_obligation): quick_elig | ST_GAS steam.
        groups = getattr(fa, "plant_group", None)
        steam = (
            (np.asarray(groups).astype(str) == "ST_GAS")
            if groups is not None
            else (fuel == "gas_st")
        )
        idx = np.flatnonzero(quick)
        pmin = np.asarray(fa.pmin, dtype=float)[idx]
        pmax = np.asarray(fa.pmax, dtype=float)[idx]
        valid = (pmin > 0) & (pmax > pmin)
        ratio = (pmax[valid] - pmin[valid]) / pmin[valid]
        raw = float(np.average(ratio, weights=pmax[valid])) if valid.any() else 1.0
        rho = float(np.clip(raw, 0.5, 4.0))
        from market_sim.config.iso_configs import get_iso_config

        # + the external node the interchange rows live on (zone index 5;
        # see any reserve_family sidecar's `zones` string).
        zones = np.array(
            [z.name for z in get_iso_config("NYISO").zones] + ["NYISO_external"],
            dtype=object,
        )
        zone_of = zones[np.asarray(fa.zone_idx, dtype=int)]
        nyc = np.isin(zone_of, sorted(NYISO_DOWNSTATE_SPIN_ZONES))
        o_sel = quick | steam
        o_idx = np.flatnonzero(o_sel)
        o_pmin = np.asarray(fa.pmin, dtype=float)[o_idx]
        o_pmax = np.asarray(fa.pmax, dtype=float)[o_idx]
        o_valid = (o_pmin > 0) & (o_pmax > o_pmin)
        o_ratio = (o_pmax[o_valid] - o_pmin[o_valid]) / o_pmin[o_valid]
        o_raw = (
            float(np.average(o_ratio, weights=o_pmax[o_valid]))
            if o_valid.any()
            else 1.0
        )
        res["years"][str(year)] = {
            "obligation_branch": {
                "n_units": int(o_idx.size),
                "n_units_valid_for_rho": int(o_valid.sum()),
                "rho_raw": round(o_raw, 4),
                "rho_used": round(float(np.clip(o_raw, 0.5, 4.0)), 4),
                "identified": bool(o_valid.any()),
            },
            "fleetwide_units": int(np.asarray(fa.pmin).size),
            "fleetwide_pmin_gt0_units": int(
                (np.asarray(fa.pmin, dtype=float) > 0).sum()
            ),
            "fleetwide_pmin_sum_mw": round(
                float(np.asarray(fa.pmin, dtype=float).sum()), 3
            ),
            "fleetwide_min_gen_present": bool(getattr(fa, "min_gen", None) is not None),
            "quick_pmin_gt0_units": int((pmin > 0).sum()),
            "quick_pmax_gt_pmin_units": int((pmax > pmin).sum()),
            "quick_pmin_sum_mw": round(float(pmin.sum()), 1),
            "fuel_mix_quick": {
                f: int((fuel[idx] == f).sum()) for f in sorted(set(fuel[idx]))
            },
            "hydro_in_quick_class": hydro_armed,
            "n_quick_units": int(idx.size),
            "n_quick_units_valid_for_rho": int(valid.sum()),
            "rho_raw": round(raw, 4),
            "rho_used": round(rho, 4),
            "rho_at_clip_ceiling": bool(raw >= 4.0),
            "nyc_quick_units": int((quick & nyc).sum()),
            "nyc_quick_pmax_mw": round(
                float(np.asarray(fa.pmax)[quick & nyc].sum()), 1
            ),
        }
        print(year, res["years"][str(year)])
    (REPO / "results/calibration/_nyiso143_online_rho.json").write_text(
        json.dumps(res, indent=1) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
