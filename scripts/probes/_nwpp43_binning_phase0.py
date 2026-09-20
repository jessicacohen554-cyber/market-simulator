"""nwpp-43 phase 0 (ZERO LP): the exact fleet/offer delta of per-plant CAMPD binning.

Rebuilds NWPP's designated keeper (``nwpp42_coalhr_span``) on its OWN recipe via
the sanctioned ``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs``
path (``run_year(..., fleet_only=True)``), once as the CONTROL and once with
``NWPP`` added to :data:`CAMPD_BINNING_ISOS` — the ONLY gate standing between
NWPP and the per-plant tranche path, since ``use_campd_bins`` already reads
``True`` in the keeper's own recipe.

Answers, before any solve (rule 29 ``[R-SCREEN]`` clause 0, which survives as
practice):

* whether the per-plant synthesis produces a non-empty bin frame for NWPP at
  all — i.e. whether the "blocked on ``bin_assignments_NWPP.csv``" premise three
  lanes have carried is true (it is not: that file is read only by
  ``ct_intermediate_plants`` / ``st_gas_intermediate_plants``, both default-off
  here, and NEVER by ``fleet_to_bins``, which reads
  ``thermal_tranches_NWPP.csv`` — committed and tracked on ``main``);
* the LP size delta, which is what owner gate **G21** (memory) turns on;
* the COAL offer stack in both legs — unit count, the hard ``pmin`` floor the
  legacy path carries, and the per-plant measured must-run / committed shares
  the tranche path carries instead;
* that ``pmax`` is conserved (the binning must re-SHAPE the coal stack, never
  add or remove capacity).

Run: ``python3 scripts/probes/_nwpp43_binning_phase0.py [<year> ...]``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BUNDLE = Path("results/calibration/nwpp42_coalhr_span")
ISO = "NWPP"


def build(year: int, arm: bool):
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))

    # The gate is a module-level frozenset read by
    # ``fleet.assembly.load_or_synthesize_bins``. Patch the name IN THAT MODULE
    # (the import binding is what the function resolves), restore it after.
    from market_sim.data.fleet import assembly as A

    saved = A.CAMPD_BINNING_ISOS
    try:
        if arm:
            A.CAMPD_BINNING_ISOS = frozenset(set(saved) | {ISO})
        return run_year(
            year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
    finally:
        A.CAMPD_BINNING_ISOS = saved


def _coal(fleet):
    return [g for g in fleet if str(g.fuel_type).lower() == "coal"]


def summarise(tag: str, out) -> dict:
    fleet = out["fleet"] if isinstance(out, dict) else out[0]
    coal = _coal(fleet)
    d = {
        "tag": tag,
        "lp_units": len(fleet),
        "lp_mw": sum(g.pmax_mw for g in fleet),
        "coal_units": len(coal),
        "coal_mw": sum(g.pmax_mw for g in coal),
        "coal_pmin_mw": sum(getattr(g, "pmin_mw", 0.0) for g in coal),
    }
    d["coal_pmin_pct"] = 100.0 * d["coal_pmin_mw"] / d["coal_mw"] if d["coal_mw"] else 0.0
    bands: dict[str, float] = {}
    for g in coal:
        suffix = str(g.unit_id).rpartition("_")[2]
        key = suffix if suffix in (
            "mustrun", "sync", "committed", "econlo", "econhi", "econ", "peak"
        ) or suffix.startswith("econc") else "<no band>"
        bands[key] = bands.get(key, 0.0) + g.pmax_mw
    d["coal_band_mw"] = {k: round(v, 1) for k, v in sorted(bands.items())}
    return d


def main() -> None:
    years = [int(a) for a in sys.argv[1:]] or [2024]
    for year in years:
        print(f"\n{'='*72}\nYEAR {year}\n{'='*72}")
        ctl = summarise("CONTROL (legacy)", build(year, arm=False))
        arm = summarise("ARM (per-plant bins)", build(year, arm=True))
        for d in (ctl, arm):
            print(
                f"\n[{d['tag']}]\n"
                f"  LP units      {d['lp_units']:>6d}   ({d['lp_mw']:,.1f} MW)\n"
                f"  COAL units    {d['coal_units']:>6d}   ({d['coal_mw']:,.1f} MW)\n"
                f"  COAL hard pmin {d['coal_pmin_mw']:>9,.1f} MW = {d['coal_pmin_pct']:.1f}% of coal pmax\n"
                f"  COAL band MW  {d['coal_band_mw']}"
            )
        print(
            f"\n[DELTA] LP units {arm['lp_units']-ctl['lp_units']:+d}"
            f"  |  coal pmax {arm['coal_mw']-ctl['coal_mw']:+.3f} MW"
            f"  |  coal hard pmin {arm['coal_pmin_mw']-ctl['coal_pmin_mw']:+,.1f} MW"
        )


if __name__ == "__main__":
    main()
