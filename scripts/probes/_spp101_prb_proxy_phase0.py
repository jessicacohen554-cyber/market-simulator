"""SPP-101 phase 0 (ZERO LP): offer-array delta of ``coal_prb_proxy_own_iso`` on SPP.

Rebuilds the SPP keeper's fleet on its OWN recipe via the sanctioned
``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs`` path
(``run_year(..., fleet_only=True)``), once as the keeper (flag off) and once with
``coal_prb_proxy_own_iso=True``, and diffs the assembled marginal-cost array
row-for-row. Precedent: ``scripts/probes/_nwpp41_coalrank_phase0.py``.

Run: ``.venv/bin/python scripts/probes/_spp101_prb_proxy_phase0.py 2019 ... 2025``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BUNDLE = Path("results/calibration/spp100_arm_span")
OUT = Path("results/phase0/spp/_spp101_prb_proxy_phase0.json")


def build(year: int, arm: bool):
    """Return the ``fleet_only`` state for ``year`` with the flag off/on."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    if arm:
        kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
        kw["prb_overrides"]["coal_prb_proxy_own_iso"] = True
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def main() -> None:
    """Print and persist the per-year moved-row census."""
    years = [int(x) for x in sys.argv[1:] if x.isdigit()] or [2023]
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for y in years:
        c, a = build(y, False), build(y, True)
        fa = c["fleet_arrays"]
        mc0 = np.asarray(c["mc_base"], float)
        mc1 = np.asarray(a["mc_base"], float)
        assert list(fa.unit_ids) == list(a["fleet_arrays"].unit_ids)
        d = mc1 - mc0
        moved = np.where(np.abs(d).max(axis=1) > 0)[0]
        groups = list(fa.plant_group)
        rows = []
        for i in moved:
            rows.append({
                "unit": str(fa.unit_ids[i]), "plant": int(fa.plant_code[i]),
                "group": str(groups[i]), "pmax": float(fa.pmax[i]),
                "mc_ctl_mean": float(mc0[i].mean()), "mc_arm_mean": float(mc1[i].mean()),
                "d_mean": float(d[i].mean()), "d_maxabs": float(np.abs(d[i]).max()),
            })
        nonc = [r for r in rows if not r["group"].startswith("COAL")]
        pm_d = float(np.abs(np.asarray(a["fleet_arrays"].pmax) - np.asarray(fa.pmax)).max())
        av_d = float(np.abs(np.asarray(a["fleet_arrays"].availability) - np.asarray(fa.availability)).max())
        out[str(y)] = {"n_rows": len(fa.unit_ids), "moved": rows,
                       "noncoal_moved": len(nonc), "pmax_maxabs": pm_d, "avail_maxabs": av_d}
        print(f"== {y}: rows {len(fa.unit_ids)} moved {len(rows)} (non-coal {len(nonc)}) "
              f"pmax|d| {pm_d} avail|d| {av_d}")
        for r in rows:
            print(f"   {r['unit']:30s} {r['group']:10s} pmax {r['pmax']:7.1f} "
                  f"mc {r['mc_ctl_mean']:7.3f} -> {r['mc_arm_mean']:7.3f} (d {r['d_mean']:+.3f})")
        OUT.write_text(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
