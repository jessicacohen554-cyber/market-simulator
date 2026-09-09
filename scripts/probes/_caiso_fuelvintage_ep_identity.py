"""caiso-fuelvintage-1 phase 0 (ZERO LP): can the EP-level seam reach CAISO's LP at all?

Rule 29 ``[R-SCREEN]`` clause (0): an arm with a computable pre-solve gate does
not reach a solve until that gate passes. The gate here is an **identity**, not
a residual — the question is whether ``gas_electric_power_monthly_level``
changes the array the LP is handed, and that array can be rebuilt without
solving anything.

Why the answer is expected to be "no reach", stated before it is measured
(``FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md`` §4, and the
ordering comment in ``data/fuel/resolve.py``): the seam sets the ISO-month gas
LEVEL, and CAISO's keeper then runs **two** later level writers over the same
cells —

1. ``apply_plant_monthly_fuel_prices`` (``gas_plant_monthly_fuel_pricing``),
   each gas plant's own F923 monthly print; and
2. ``apply_hub_basis_overlay`` (``gas_hub_basis_overlay``), the SoCal / PG&E
   Citygate measured index, which the level ordering says supersedes a
   state-average outright.

Both run AFTER the seam, so whatever the seam writes survives only in cells
neither of them covers. This measures that surviving set directly instead of
inferring it from a mask census: two ``fleet_only`` rebuilds on the keeper's
own recipe, flag off and flag on, differenced on ``fuel_prices`` (the delivered
$/MMBtu the offer stack is built from) and ``mc_base`` (the assembled P0
objective the LP actually minimizes).

A max |delta| of 0.0 on both arrays is a **provably inert** arm: no solve can
show a difference that the inputs do not carry.

Usage::

    PYTHONPATH=.:src:scripts uv run python \
        scripts/probes/_caiso_fuelvintage_ep_identity.py
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
T = 8760

#: Bundle each year's keeper recipe is replayed from. 2023-2025 are the
#: designated keeper; 2022 is the registered validation touchpoint that carries
#: the SAME recipe on the held-out year (rule 30 ``[R-TOUCHPOINT-FOLD]``), and
#: is the only CAISO year where the seam's own table shows a material gap
#: (Dec-2022, +16.058 $/MMBtu — the western gas crisis).
BUNDLES = {
    2023: "results/calibration/caiso260_demand_vintage",
    2024: "results/calibration/caiso260_demand_vintage",
    2025: "results/calibration/caiso260_demand_vintage",
    2022: "results/calibration/caiso262_2022_touchpoint",
}


def _rebuild(bundle: Path, year: int, arm: bool) -> dict:
    """Return the LP-visible fuel arrays for one year, seam off or on."""
    sys.path[:0] = [str(REPO), str(REPO / "src"), str(REPO / "scripts")]
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year

    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if arm:
        # The generic ScenarioConfig override channel the CLI uses for this
        # flag (run_calibration_full.py, the prb_overrides comment).
        over = dict(kw.get("prb_overrides") or {})
        over["gas_electric_power_monthly_level"] = True
        kw["prb_overrides"] = over

    clear_fleet_caches()
    with contextlib.redirect_stderr(io.StringIO()):
        st = run_year(
            year,
            meta["iso"],
            T,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kw,
        )
    fa = st["fleet_arrays"]
    return {
        "fuel_prices": np.asarray(st["fuel_prices"], dtype=float),
        "mc_base": np.asarray(st["mc_base"], dtype=float),
        "fuel_type_idx": np.asarray(fa.fuel_type_idx),
        "pmax": np.asarray(fa.pmax, dtype=float),
        "n_units": len(fa.unit_ids),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2022])
    ap.add_argument("--out", default="results/calibration/_caiso_fuelvintage_ep_identity.json")
    args = ap.parse_args()

    from market_sim.data.fuel.electric_power import iso_electric_power_monthly_level

    out: dict = {"coverage": {}, "years": {}}

    # Zero-LP coverage assertion: the admission test's own guarantee.
    for y in (2019, 2020, 2021, 2022, 2023, 2024, 2025):
        lvl = iso_electric_power_monthly_level("CAISO", y)
        out["coverage"][str(y)] = (
            None if lvl is None else [round(float(v), 4) for v in list(lvl)]
        )

    for year in args.years:
        bundle = REPO / BUNDLES[year]
        off = _rebuild(bundle, year, arm=False)
        on = _rebuild(bundle, year, arm=True)

        d_fuel = np.abs(on["fuel_prices"] - off["fuel_prices"])
        d_mc = np.abs(on["mc_base"] - off["mc_base"])
        # Restrict to rows the seam could touch at all: gas-fuelled units.
        from market_sim.data.fuel.resolve import _GAS_FUEL_IDX

        gas_rows = np.isin(off["fuel_type_idx"], list(_GAS_FUEL_IDX))
        n_moved = int((d_fuel.max(axis=1) > 0).sum())

        out["years"][str(year)] = {
            "bundle": str(bundle.relative_to(REPO)),
            "n_units": off["n_units"],
            "n_gas_units": int(gas_rows.sum()),
            "max_abs_delta_fuel_prices": float(d_fuel.max()),
            "max_abs_delta_mc_base": float(d_mc.max()),
            "n_unit_rows_moved": n_moved,
            "gas_cell_share_moved": float((d_fuel[gas_rows] > 0).mean())
            if gas_rows.any()
            else 0.0,
            "ep_level_admitted": out["coverage"][str(year)] is not None,
        }
        r = out["years"][str(year)]
        print(
            f"  {year}: admitted={r['ep_level_admitted']}  "
            f"max|d fuel_prices|={r['max_abs_delta_fuel_prices']:.6f}  "
            f"max|d mc_base|={r['max_abs_delta_mc_base']:.6f}  "
            f"rows moved={n_moved}/{off['n_units']}",
            flush=True,
        )

    dest = REPO / args.out
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
