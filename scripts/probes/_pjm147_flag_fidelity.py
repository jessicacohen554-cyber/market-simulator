"""pjm-147 — does ``measured_chp_heat_rates`` actually reach PJM's LP seam?

The ERCOT-146 hazard, checked BEFORE a solve is spent: that cell was stamped
``I`` because the flag's only consumer is ``eia860._rows_to_generators``, while
under ``use_campd_bins`` ERCOT's thermal fleet comes from the curated per-plant
sheet, which never receives the kwarg — so flag-on and flag-off built a
BYTE-IDENTICAL fleet and an A/B would have burned two solves to reproduce the
control. ``assembly.load_or_synthesize_bins`` reads that sheet only for
``iso == "ERCOT"``; every other ISO synthesises its bins through
``load_fleet_from_csv(..., measured_chp_heat_rates=...)``, which is why neiso-70
cleared the same check. PJM runs the same ``use_campd_bins`` /
``plant_level_fleet`` configuration as NEISO, so the expectation is LIVE — but
neiso-70's precedent is NEISO's, not PJM's (rule 25 [R-ISO-SCOPE]), so it is
measured here on PJM's own fleet.

Builds the keeper's fleet through the REAL solve path
(``replay_keeper.build_kwargs`` -> ``run_calibration.run_year(fleet_only=True)``)
with the flag off and on, and reports the per-generator heat-rate delta at the
seam the LP prices from.

    uv run python scripts/probes/_pjm147_flag_fidelity.py
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/pjm143_hy_level_B"
OUT_PATH = REPO / "results/calibration/_pjm147_flag_fidelity.json"
YEAR = 2023
TARGET = ("CC_CHP", "CT_CHP")


def _run_year_kwargs(meta: dict) -> dict:
    """Bind the keeper's stored kwargs onto ``run_year``'s signature."""
    from scripts.replay_keeper import build_kwargs
    from scripts.run_calibration import run_year

    solve_kwargs = build_kwargs(meta)
    params = set(inspect.signature(run_year).parameters)
    rename = {"commitment": "commitment_enabled", "screen_coal": "commitment_screen_coal"}
    skip = {"year", "iso", "hours", "gas_price", "ttc_overrides", "fleet_only"}
    kwargs = {}
    for k, v in solve_kwargs.items():
        k2 = rename.get(k, k)
        if k2 in params and k2 not in skip:
            kwargs[k2] = v
    return kwargs


def _build(kwargs: dict, flag: bool) -> list:
    from scripts.run_calibration import run_year

    state = run_year(year=YEAR, iso="PJM", fleet_only=True, **{**kwargs, "measured_chp_heat_rates": flag})
    gens = state.get("generators") or state.get("fleet")
    return list(gens)


def main() -> int:
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = _run_year_kwargs(meta)
    print(f"[map] {len(kwargs)} kwargs bound from the keeper meta")
    print(f"[cfg] keeper measured_chp_heat_rates = {kwargs.get('measured_chp_heat_rates')}")

    off = _build(kwargs, False)
    on = _build(kwargs, True)
    if len(off) != len(on):
        raise SystemExit(f"fleet size changed {len(off)} -> {len(on)}; not a pure reprice")

    moved, dmw, rows = 0, 0.0, []
    for a, b in zip(off, on):
        if a.unit_id != b.unit_id:
            raise SystemExit(f"fleet order changed at {a.unit_id} vs {b.unit_id}")
        if abs(float(a.heat_rate) - float(b.heat_rate)) > 1e-9:
            moved += 1
            dmw += float(b.pmax_mw)
            rows.append(
                {
                    "unit_id": str(a.unit_id),
                    "plant_code": int(a.plant_code or 0),
                    "klass": str(a.plant_group),
                    "pmax_mw": round(float(a.pmax_mw), 3),
                    "hr_off": round(float(a.heat_rate), 4),
                    "hr_on": round(float(b.heat_rate), 4),
                }
            )

    print(f"\n  generators: {len(off)}   moved: {moved}   moved capacity: {dmw:,.1f} MW")
    summary = {"year": YEAR, "n_generators": len(off), "n_moved": moved, "moved_mw": round(dmw, 3)}

    for klass in TARGET:
        for label, fleet in (("off", off), ("on", on)):
            w = np.array([float(g.pmax_mw) for g in fleet if g.plant_group == klass])
            hr = np.array([float(g.heat_rate) for g in fleet if g.plant_group == klass])
            if not w.size:
                continue
            capw = float(np.average(hr, weights=w))
            summary[f"{klass}_capw_hr_{label}"] = round(capw, 4)
            summary[f"{klass}_mw"] = round(float(w.sum()), 3)
        a = summary.get(f"{klass}_capw_hr_off")
        b = summary.get(f"{klass}_capw_hr_on")
        if a and b:
            print(
                f"  {klass:<7} {summary[f'{klass}_mw']:8.1f} MW   "
                f"cap-wt HR {a:7.4f} -> {b:7.4f}  ({100 * (b / a - 1):+5.2f} %)"
            )

    other = sorted({r["klass"] for r in rows} - set(TARGET))
    if other:
        raise SystemExit(f"flag touched out-of-scope classes: {other}")
    print(f"  scope check: only {sorted({r['klass'] for r in rows})} moved (no leak)")

    summary["moved_rows"] = rows
    OUT_PATH.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\nwrote {OUT_PATH.relative_to(REPO)}")
    print(
        "  VERDICT: "
        + ("LIVE — the flag reaches PJM's LP seam" if moved else "INERT — ERCOT-146 hazard applies")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
