"""nwpp-41 phase 0 (ZERO LP): offer-array delta of the NWPP coal-rank derive.

Rebuilds the registered NWPP run's fleet on its OWN recipe via the sanctioned
``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs`` path
(``run_year(..., fleet_only=True)``), once as the CONTROL (no
``coal_supply_NWPP.csv`` on disk, the posture the registered run solved under)
and once with the derived file present, and diffs the assembled marginal-cost
array row-for-row.

The question it answers before any solve (rule 29 ``[R-SCREEN]`` clause 0,
which survives as the practice): landing
``data/raw/_processed-legacy/coal_supply_NWPP.csv`` moves the model's REPORTING
class from the bare ``COAL`` to ``COAL_PRB`` / ``COAL_BIT`` / ``COAL_WC`` (the
C1 taxonomy seam of ``docs/handoffs/FINDING-nwpp-40-2026-09-16.md`` §7.1) — but
does it also move the LP's INPUTS?  Two live channels could:

* the offer-curve router (``data.offer_curves``) keys the coal curve on the
  supply tag, and
* ``coal_prb_passthrough_sigmoid`` / ``coal_prb_passthrough_tiered`` — both ON
  in this run's recipe — apply the PRB fuel-cost passthrough to plants tagged
  ``prb``, of which the control has NONE.

Run: ``python3 scripts/probes/_nwpp41_coalrank_phase0.py <year> [<year> ...]``
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BUNDLE = Path("results/calibration/nwpp40_span_A")
DERIVED = Path("data/raw/_processed-legacy/coal_supply_NWPP.csv")
# The candidate artifact, derived to scratch by
# ``scripts/data/derive_coal_supply.py --iso NWPP --census-vintage 2023 2024 2025``.
SCRATCH = Path(sys.argv[0]).resolve().parents[2] / ".nwpp41_coal_supply_NWPP.csv"


def _clear_caches() -> None:
    """Drop every lru_cache that memoizes the coal-rank resolution chain."""
    import importlib

    coal = importlib.import_module("market_sim.data.coal")
    coal._derived_coal_supply.cache_clear()
    coal._eia860_retiree_coal_supply.cache_clear()
    for mod in ("market_sim.data.offer_curves", "market_sim.data.fleet"):
        m = importlib.import_module(mod)
        for name in dir(m):
            obj = getattr(m, name, None)
            if hasattr(obj, "cache_clear"):
                try:
                    obj.cache_clear()
                except Exception:
                    pass


def build(year: int, arm: bool):
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))

    existed = DERIVED.exists()
    try:
        if arm:
            shutil.copyfile(SCRATCH, DERIVED)
            if NO_REPRICE:
                # Leg (b): the derive lands (so the REPORTING class splits) but
                # ``coal_supply_repricing`` is off, so no coal plant takes a
                # supply-class price. Rule 25 [R-ISO-SCOPE]: the PRB proxy
                # ``_prb_monthly_actuals`` is built from COAL_PLANT_SUPPLY, which
                # is ERCOT-only (Fayette / J K Spruce), so leaving repricing on
                # imports a TEXAS delivered price onto Montana plants.
                kw.setdefault("prb_overrides", {})
                kw["prb_overrides"] = dict(kw["prb_overrides"])
                kw["prb_overrides"]["coal_supply_repricing"] = False
        elif existed:
            DERIVED.unlink()
        _clear_caches()
        return run_year(
            year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
    finally:
        if DERIVED.exists():
            DERIVED.unlink()
        _clear_caches()


def _arrays(state):
    """Return the comparison surface from a ``fleet_only`` state dict."""
    import numpy as np

    fa = state["fleet_arrays"]
    return {
        "unit_ids": list(fa.unit_ids),
        "groups": list(getattr(fa, "plant_group", [])),
        "codes": list(getattr(fa, "plant_code", [])),
        "bins": list(getattr(fa, "efficiency_bin", [])),
        "mc": np.asarray(state["mc_base"], dtype=float),
        "pmax": np.asarray(fa.pmax, dtype=float),
        "avail": np.asarray(fa.availability, dtype=float),
    }


COAL_CODES = set()
NO_REPRICE = "--no-reprice" in sys.argv


def _coal_rows(a):
    return [i for i, c in enumerate(a["codes"]) if int(c) in COAL_CODES]


def main() -> None:
    import pandas as pd

    COAL_CODES.update(
        int(c) for c in pd.read_csv(SCRATCH)["plant_code"]
    )
    years = [int(x) for x in sys.argv[1:] if x.isdigit()] or [2023]
    for y in years:
        ctl = _arrays(build(y, arm=False))
        arm = _arrays(build(y, arm=True))
        print(f"\n===== {y} =====")
        print(f"  rows  ctl {len(ctl['unit_ids'])}  arm {len(arm['unit_ids'])}")

        if ctl["unit_ids"] != arm["unit_ids"]:
            same = set(ctl["unit_ids"]) == set(arm["unit_ids"])
            print(f"  UNIT ID SET IDENTICAL: {same} (order differs: {not same})")
            continue
        if ctl["groups"] != arm["groups"]:
            moved = [
                (u, g0, g1)
                for u, g0, g1 in zip(ctl["unit_ids"], ctl["groups"], arm["groups"])
                if g0 != g1
            ]
            print(f"  plant_group moved on {len(moved)} rows, e.g. {moved[:3]}")
        else:
            print("  plant_group identical on every row")
        coal = _coal_rows(ctl)
        other = [i for i in range(len(ctl["unit_ids"])) if i not in set(coal)]
        for lab, idx in (("COAL", coal), ("NON-COAL", other)):
            if not idx:
                print(f"  {lab}: no rows")
                continue
            dmc = np.abs(arm["mc"][idx] - ctl["mc"][idx])
            dpm = np.abs(arm["pmax"][idx] - ctl["pmax"][idx])
            dav = np.abs(arm["avail"][idx] - ctl["avail"][idx])
            nmoved = int((dmc.max(axis=1) > 0).sum())
            print(
                f"  {lab:9s} n={len(idx):4d}  offer max|d| ${dmc.max():.10f}/MWh  "
                f"rows moved {nmoved}  pmax max|d| {dpm.max():.10f}  "
                f"avail max|d| {dav.max():.12f}"
            )
            for i in idx:
                d = float(np.abs(arm["mc"][i] - ctl["mc"][i]).max())
                if d > 0:
                    print(
                        f"      moved: {ctl['unit_ids'][i]:28s} bin={str(ctl['bins'][i]) if i < len(ctl['bins']) else '?':22s} "
                        f"pmax={ctl['pmax'][i]:8.2f}  max|d| ${d:9.4f}  "
                        f"mean ctl ${ctl['mc'][i].mean():8.3f} -> arm ${arm['mc'][i].mean():8.3f}"
                    )
        # Capacity-weighted mean coal offer, both legs.
        if coal:
            w = ctl["pmax"][coal]
            cw_c = float((ctl["mc"][coal].mean(axis=1) * w).sum() / w.sum())
            cw_a = float((arm["mc"][coal].mean(axis=1) * w).sum() / w.sum())
            print(
                f"  COAL capacity-weighted mean offer  ctl ${cw_c:9.4f}  "
                f"arm ${cw_a:9.4f}  d ${cw_a - cw_c:+9.4f}"
            )


if __name__ == "__main__":
    main()
