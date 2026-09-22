"""nwpp-46 phase 0 (ZERO LP): the coal offer stack's VERTICAL EXTENT, per plant.

Rebuilds the NWPP-44 designated keeper (``nwpp44_takeorpay_reg``) fleet through
the sanctioned ``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs``
path (``run_year(..., fleet_only=True)``) and reports, for every coal LP row,
its band, capacity and assembled P0 offer ``mc_base`` — the array the LP is
actually handed.

NWPP-45 ruled C4 IN on the stack's vertical extent: how much coal MW sits at a
price a normal NWPP day crosses. This probe measures that extent three ways:

  (1) per BAND, cap-weighted mean offer and MW, per year;
  (2) per PLANT x band, so a fleet-level average cannot hide a plant that is
      already sloped or already flat;
  (3) the DISPATCHABLE SPREAD - the offer difference between a plant's cheapest
      and dearest dispatchable band, which is the quantity C4's amplitude
      responds to.

Run: ``PYTHONPATH=.:src python3 scripts/probes/_nwpp46_coal_stack_phase0.py [<year> ...]``
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BUNDLE = Path("results/calibration/nwpp44_takeorpay_reg")
COAL_GROUPS = ("COAL", "COAL_BIT", "COAL_PRB", "COAL_WC")
BAND_ORDER = ("mustrun", "sync", "committed", "econlo", "econhi", "econ", "peak")


def build(year: int):
    """Rebuild the keeper fleet for ``year`` on the keeper's own recipe."""
    import scripts.run_calibration as RC
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    return RC.run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def _band(unit_id: str) -> str:
    suffix = str(unit_id).rpartition("_")[2]
    if suffix in BAND_ORDER or suffix.startswith("econc"):
        return suffix
    return "<none>"


def _bkey(b: str) -> int:
    return BAND_ORDER.index(b) if b in BAND_ORDER else 99


def main() -> None:
    years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
    for year in years:
        out = build(year)
        fa = out["fleet_arrays"]
        mc = np.asarray(out["mc_base"], dtype=float)
        if mc.ndim == 2:
            mc = mc.mean(axis=1)
        groups = [str(x) for x in np.asarray(fa.plant_group)]
        pmax = np.asarray(fa.pmax, dtype=float)
        idx = [i for i, g in enumerate(groups) if g in COAL_GROUPS]
        print(f"\n{'=' * 94}\nYEAR {year} — COAL offer stack ({len(idx)} LP rows)\n{'=' * 94}")

        # (1) per band, fleet
        agg: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
        for i in idx:
            b = _band(fa.unit_ids[i])
            agg[b][0] += pmax[i]
            agg[b][1] += mc[i] * pmax[i]
        print(f"  {'band':<12}{'MW':>11}{'cap-wtd mc':>13}")
        base = None
        for b in sorted(agg, key=_bkey):
            p, w = agg[b]
            lvl = w / p if p else 0.0
            if b in ("econlo", "econ"):
                base = lvl
            print(f"  {b:<12}{p:>11,.1f}{lvl:>13.2f}")
        if base:
            hi = max(
                (w / p for b, (p, w) in agg.items() if b in ("econlo", "econhi", "peak") and p),
                default=base,
            )
            print(f"  econ-range spread (econlo -> dearest econ/peak): ${hi - base:.2f}/MWh")

        # (2)+(3) per plant
        per: dict[str, dict[str, tuple[float, float]]] = defaultdict(dict)
        for i in idx:
            nm = str(fa.unit_ids[i]).rpartition("_")[0]
            per[nm][_band(fa.unit_ids[i])] = (pmax[i], mc[i])
        print(f"\n  {'plant (LP row stem)':<34}" + "".join(f"{b[:7]:>9}" for b in BAND_ORDER[:1] + BAND_ORDER[2:]) + f"{'spread':>9}{'dispMW':>9}")
        tot_disp_mw = 0.0
        wsum = 0.0
        for nm in sorted(per):
            bands = per[nm]
            cells = []
            for b in BAND_ORDER[:1] + BAND_ORDER[2:]:
                cells.append(f"{bands[b][1]:>9.2f}" if b in bands else f"{'-':>9}")
            disp = {b: v for b, v in bands.items() if b not in ("mustrun", "sync")}
            if disp:
                lo = min(v[1] for v in disp.values())
                hi = max(v[1] for v in disp.values())
                mw = sum(v[0] for v in disp.values())
                tot_disp_mw += mw
                wsum += (hi - lo) * mw
                sp, smw = f"{hi - lo:>9.2f}", f"{mw:>9.1f}"
            else:
                sp, smw = f"{'-':>9}", f"{'-':>9}"
            print(f"  {nm[:33]:<34}" + "".join(cells) + sp + smw)
        if tot_disp_mw:
            print(
                f"\n  FLEET dispatchable-band spread, MW-weighted: "
                f"${wsum / tot_disp_mw:.2f}/MWh over {tot_disp_mw:,.1f} MW"
            )


if __name__ == "__main__":
    main()
