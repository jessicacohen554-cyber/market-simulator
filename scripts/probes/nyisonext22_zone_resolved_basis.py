#!/usr/bin/env python3
"""NYISO-NEXT-22 phase 0 (ZERO LP): NYISO C3a/C3b on the ZONE-RESOLVED load-weighted actual.

Rubric v2.4 defines the C3a/C3b actual as "the committed hourly actual weighted by
the same measured demand the model dispatches, zone-resolved where a zonal archive
exists". ``derive_actual_lmp._lw_fields`` registers ERCOT and MISO (miso-294) in
``ZONAL_LW_SOURCES``; NYISO is scored on its HUB (simple mean of the eleven internal
zones) weighted by SYSTEM demand, although its own staging already builds every
model zone's series (``nyiso_zone_hourly``, the simple mean of its constituent NYISO
zones, from the public archive ``fetch_nyiso_zonal_lmp.py`` stages).

This probe builds the zone-resolved fields with the registry branch's exact
construction (per model zone: its series, weighted by that zone's measured demand;
then zone-demand-weighted across zones), patches them into the keeper's bench IN
MEMORY, and re-scores both registered NYISO runs through ``calibration_verdict``.
Nothing is written to the bench or the reference. Rule 13: the actual is a
benchmark, never an input. The direct analogue of
``scripts/probes/_miso293_zone_resolved_basis.py``.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402

import calibration_verdict as cv  # noqa: E402
from scripts.data import derive_actual_lmp as dal  # noqa: E402

RUNS = {
    "span": ("2026-10-01-nyisonext21-astoria-hr-span", (2022, 2023, 2024, 2025)),
    "2021": ("2026-10-01-nyisonext21-astoria-hr-2021", (2021,)),
}
OUT = REPO / "results/phase0/nyiso/_nyisonext22_zone_resolved_basis.json"


def zone_lw(year: int) -> dict:
    """Zone-resolved ``{rt,da}_lw`` + ``_lw_mon`` for one NYISO year."""
    from market_sim.config.iso_configs import get_iso_config

    demand = dal._measured_zone_demand("NYISO", year)
    names = [zn.name for zn in get_iso_config("NYISO").zones]
    out: dict = {}
    for kind in ("rt", "da"):
        fr = dal.nyiso_zone_hourly(year, kind)
        pairs = []
        for zi, zone in enumerate(names):
            if zone not in fr.columns:
                continue
            p = dal._densify_std(fr[zone], year, dal._STD_TZ["NYISO"])
            annual, mon = dal._lw_stats(p, demand[zi])
            if np.isnan(annual):
                continue
            pairs.append((annual, mon, float(demand[zi].sum()), zone))
        ws = sum(w for _, _, w, _ in pairs)
        out[f"{kind}_lw"] = round(sum(a * w for a, _, w, _ in pairs) / ws, 2)
        out[f"{kind}_lw_mon"] = [
            round(sum(m[i] * w for _, m, w, _ in pairs if m[i] is not None)
                  / sum(w for _, m, w, _ in pairs if m[i] is not None), 2)
            if any(m[i] is not None for _, m, _, _ in pairs) else None
            for i in range(12)
        ]
        out[f"_{kind}_zone_annual"] = {z: round(a, 2) for a, _, _, z in pairs}
    return out


def price_rows(verdict: dict) -> dict:
    """``{criterion-year: (status, magnitude, model, actual)}`` for C3a/C3b."""
    rows = {}
    for crit in ("price_mean", "price_shape"):
        for r in verdict["criteria"][crit]["records"]:
            if r.get("key") is None:
                rows[f"{crit} {r['year']}"] = (r["status"], r.get("magnitude"), r.get("model"), r.get("actual"))
    return rows


def main() -> None:
    """CLI entry point."""
    res = {}
    for tag, (run, years) in RUNS.items():
        art = cv.load_artifacts(run)
        base = cv.determine_from_artifacts(run, art)
        art2 = copy.deepcopy(art)
        fields = {}
        for y in years:
            f = zone_lw(y)
            fields[str(y)] = {k: v for k, v in f.items() if not k.endswith("_mon")}
            fields[str(y)]["hub_rt_lw"] = art["bench"][y]["avgLMP"].get("rt_lw")
            art2["bench"][y]["avgLMP"].update({k: v for k, v in f.items() if not k.startswith("_")})
        v = cv.determine_from_artifacts(run, art2)
        res[tag] = {
            "run": run,
            "fields": fields,
            "base": {"determination": base.get("determination"), "reasons": base.get("reasons"), "rows": price_rows(base)},
            "zone_resolved": {"determination": v.get("determination"), "reasons": v.get("reasons"), "rows": price_rows(v)},
        }
    OUT.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
