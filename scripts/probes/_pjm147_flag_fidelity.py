"""pjm-147 K0 — does ``measured_chp_heat_rates`` actually reach PJM's LP seam?

The ERCOT-146 hazard, checked BEFORE a solve is spent. That cell was stamped
``I`` because the flag's only consumer is ``eia860._rows_to_generators``, while
under ``use_campd_bins`` ERCOT's thermal fleet comes from the curated per-plant
sheet, which never receives the kwarg — so flag-on and flag-off built a
BYTE-IDENTICAL fleet and an A/B would have burned two solves to reproduce the
control. ``assembly.load_or_synthesize_bins`` reads that sheet only for
``iso == "ERCOT"``; every other ISO synthesises its bins through
``load_fleet_from_csv(..., measured_chp_heat_rates=...)``, which is why neiso-70
cleared the same check. PJM runs the same ``use_campd_bins`` /
``plant_level_fleet`` configuration as NEISO, so the expectation is LIVE — but
neiso-70's clearance is NEISO's, not PJM's (rule 25 [R-ISO-SCOPE]), so it is
measured here on PJM's own fleet.

Builds the keeper's fleet through the REAL solve path
(``replay_keeper.build_kwargs`` -> ``run_calibration.run_year(fleet_only=True)``,
the pjm-145/146 pattern) with the flag off and on, and reports the per-generator
heat-rate delta at the seam the LP prices from.

PREREG-pjm147-measured-chp-heat-rates-2026-08-03.md §4 K0: the flag must move
>= 1 generator and the CC_CHP cap-weighted heat rate, and must move NO class
outside (CC_CHP, CT_CHP). No movement => stamp ``I``, spend no solve.

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
YEARS = (2023, 2024, 2025)
FLAG = "measured_chp_heat_rates"
TARGET = ("CC_CHP", "CT_CHP")


def _run_year_kwargs(meta: dict) -> dict:
    """Bind the keeper's stored kwargs onto ``run_year``'s signature."""
    from scripts.replay_keeper import build_kwargs
    from scripts.run_calibration import run_year

    solve_kwargs = build_kwargs(meta)
    params = set(inspect.signature(run_year).parameters)
    rename = {"commitment": "commitment_enabled", "screen_coal": "commitment_screen_coal"}
    skip = {"year", "iso", "hours", "gas_price", "ttc_overrides", "fleet_only"}
    kwargs, dropped = {}, []
    for k, v in solve_kwargs.items():
        k2 = rename.get(k, k)
        if k2 in params and k2 not in skip:
            kwargs[k2] = v
        else:
            dropped.append(k)
    print(f"[map] {len(kwargs)} kwargs bound; dropped: {sorted(dropped)}")
    return kwargs


def _fleet(kwargs: dict, year: int, gas: float, armed: bool) -> list:
    from scripts.run_calibration import run_year

    kw = dict(kwargs)
    if armed:
        prb = dict(kw.get("prb_overrides") or {})
        prb[FLAG] = True
        kw["prb_overrides"] = prb
    state = run_year(year, "PJM", 8760, gas, {}, fleet_only=True, **kw)
    return list(state["fleet"])


def main() -> int:
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = _run_year_kwargs(meta)
    gas_prices = meta.get("gas_prices", {})
    print(f"[cfg] keeper {FLAG} = {(kwargs.get('prb_overrides') or {}).get(FLAG)}")

    out: dict = {"flag": FLAG, "years": {}, "k0_live": False, "k0_scope_ok": True}
    for year in YEARS:
        gas = float(gas_prices.get(str(year), gas_prices.get(year, 0.0)))
        off = _fleet(kwargs, year, gas, False)
        on = _fleet(kwargs, year, gas, True)
        if len(off) != len(on):
            raise SystemExit(f"{year}: fleet size {len(off)} -> {len(on)}; not a pure reprice")

        rows = []
        for a, b in zip(off, on):
            if a.unit_id != b.unit_id:
                raise SystemExit(f"{year}: fleet order changed at {a.unit_id}/{b.unit_id}")
            if abs(float(a.heat_rate) - float(b.heat_rate)) > 1e-9:
                rows.append(
                    {
                        "plant_code": int(a.plant_code or 0),
                        "klass": str(a.plant_group),
                        "pmax_mw": round(float(a.pmax_mw), 3),
                        "hr_off": round(float(a.heat_rate), 4),
                        "hr_on": round(float(b.heat_rate), 4),
                    }
                )

        moved_classes = sorted({r["klass"] for r in rows})
        leak = sorted(set(moved_classes) - set(TARGET))
        rec: dict = {
            "n_generators": len(off),
            "n_moved": len(rows),
            "moved_mw": round(sum(r["pmax_mw"] for r in rows), 3),
            "moved_plant_class_pairs": len({(r["plant_code"], r["klass"]) for r in rows}),
            "moved_classes": moved_classes,
            "out_of_scope_classes": leak,
        }
        for klass in TARGET:
            w = np.array([float(g.pmax_mw) for g in off if g.plant_group == klass])
            if not w.size:
                continue
            h0 = np.array([float(g.heat_rate) for g in off if g.plant_group == klass])
            h1 = np.array([float(g.heat_rate) for g in on if g.plant_group == klass])
            rec[f"{klass}_mw"] = round(float(w.sum()), 3)
            rec[f"{klass}_capw_hr_off"] = round(float(np.average(h0, weights=w)), 4)
            rec[f"{klass}_capw_hr_on"] = round(float(np.average(h1, weights=w)), 4)
        rec["moved_rows"] = rows
        out["years"][str(year)] = rec
        out["k0_live"] |= len(rows) > 0
        out["k0_scope_ok"] &= not leak

        print(
            f"\n  {year}: {len(off)} generators, {len(rows)} moved "
            f"({rec['moved_mw']:,.1f} MW, {rec['moved_plant_class_pairs']} (plant,class) pairs)"
        )
        for klass in TARGET:
            a, b = rec.get(f"{klass}_capw_hr_off"), rec.get(f"{klass}_capw_hr_on")
            if a and b:
                print(
                    f"    {klass:<7} {rec[f'{klass}_mw']:8.1f} MW  cap-wt HR "
                    f"{a:7.4f} -> {b:7.4f}  ({100 * (b / a - 1):+5.2f} %)"
                )
        print(f"    classes moved: {moved_classes}   out-of-scope leak: {leak or 'none'}")
        del off, on

    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {OUT_PATH.relative_to(REPO)}")
    verdict = "LIVE" if (out["k0_live"] and out["k0_scope_ok"]) else "K0 FAIL"
    print(f"  K0 VERDICT: {verdict}  (live={out['k0_live']}, scope_ok={out['k0_scope_ok']})")
    return 0 if out["k0_live"] and out["k0_scope_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
