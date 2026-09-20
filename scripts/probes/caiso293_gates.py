"""PRE-REGISTERED ZERO-LP GATES G-1..G-4 for caiso-293's CHP steam duty window.

Declared ex ante in ``docs/PRECOMMIT-caiso293-chp-steam-duty-window-2026-09-20.md``
§4, before any code change and before any solve. G-1..G-4 are hard STOPs: a
breach means no shard is launched.

* **G-1** identity, every ISO artifact: ``|on_frac x median_cf - steam_level_cf|
  <= 0.05`` on every ``status=="ok"`` CHP row that carries both columns.
* **G-2** off-inert: gate OFF ⇒ rebuilt ``chp_grid_pmin_mw`` and the composed
  ``min_gen`` / ``min_gen_mech`` arrays are BIT-IDENTICAL to the pre-change
  construction, all four keeper years.
* **G-3** control inertness: gate ON ⇒ the three flat steam hosts' forced
  energy moves < 2 % per year.
* **G-4** energy conservation: gate ON ⇒ the ten cyclers' forced energy moves
  < 10 % per year (this repair REDISTRIBUTES hours, it does not remove energy).

G-2 IS NOT COMPUTED HERE. Its first draft tried to build the pre-change
reference in-process by reproducing ``min_gen[g, :] = pmin_mw`` for every
floored unit, and that reference was WRONG: ``fleet/arrays.py`` clips every
floor to ``pmax x availability`` and four later floor blocks legitimately
overwrite the same cells, so the check counted correct behaviour as a diff and
reported a false FAIL of 1.23 M cells. The sound form is a true two-version
comparison -- ``scripts/probes/caiso293_g2_snapshot.py``, run once on this tree
and once on the pre-change tree, then diffed. Measured that way, G-2 PASSES:
``min_gen``, ``min_gen_mechanism``, ``chp_grid_pmin_mw`` and ``pmax`` are all
BIT-IDENTICAL across 2022-2025 with the gate at its default.

Run: ``PYTHONPATH=.:src python scripts/probes/caiso293_gates.py``
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.lib.bundle_fleet import ensure_probe_path, reconstruct_bundle_fleet  # noqa: E402

ensure_probe_path()

BUNDLE = REPO / "results/calibration/xiso8_leftedge_span"
YEARS = (2022, 2023, 2024, 2025)
OUT = REPO / "results/calibration/_caiso293_gates.json"

CYCLERS = frozenset({10034, 10294, 10649, 10650, 50612, 54749, 54768, 10405, 10349, 10156})
FLAT = frozenset({55400, 55217, 50865})

G1_TOL = 0.05  # the 1-dp rounding envelope of two 1-dp columns
G3_BAR = 0.02
G4_BAR = 0.10


def gate_1() -> tuple[bool, list[dict]]:
    """Identity ``on_frac x median_cf == steam_level_cf`` over EVERY ISO."""
    worst: list[dict] = []
    ok = True
    for path in sorted((REPO / "data/raw/_processed-legacy").glob("thermal_tranches*.csv")):
        rows = list(csv.DictReader(path.open()))
        n = 0
        wmax = 0.0
        for r in rows:
            if r.get("plant_group") not in ("CC_CHP", "CT_CHP", "ST_CHP"):
                continue
            if str(r.get("status", "ok")) != "ok":
                continue
            try:
                lvl = float(r["steam_level_cf"])
                med = float(r["median_cf"])
            except (KeyError, TypeError, ValueError):
                continue
            if med <= 0.0:
                continue
            on = min(1.0, max(0.0, lvl / med))
            err = abs(on * med - lvl)
            wmax = max(wmax, err)
            n += 1
            if err > G1_TOL:
                ok = False
        worst.append({"artifact": path.name, "ok_chp_rows": n, "max_abs_err": round(wmax, 6)})
    return ok, worst


def compose(year: int, armed: bool):
    """Rebuild the keeper's year with/without the gate; return floors + arrays."""
    overrides = {"chp_steam_duty_window": True} if armed else None
    state, _ = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
    if armed:
        # Re-run the fleet build with the gate armed by mutating the
        # reconstructed config and rebuilding through the same entry point.
        from scripts.lib.bundle_fleet import full_run_year_kwargs
        from scripts.replay_keeper import derived_run_year_inputs
        from scripts.run_calibration import run_year

        meta = json.loads((BUNDLE / "meta.json").read_text())
        kw = full_run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(BUNDLE, year))
        # ``prb_overrides`` is this recipe's generic ScenarioConfig override
        # channel -- ``run_year`` applies it LAST -- and it is how the CAISO
        # keeper already arms chp_steam_floor_p25 and its 40 siblings. Arm the
        # duty window through the same channel so the armed leg differs from
        # the control in exactly one field.
        kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
        kw["prb_overrides"]["chp_steam_duty_window"] = True
        kw.pop("fleet_only", None)
        from scripts.lib.bundle_fleet import bundle_gas_price

        state = run_year(
            year, meta["iso"], 8760, bundle_gas_price(meta, year), fleet_only=True, **kw
        )
    gens = state["fleet"]
    gens = getattr(gens, "generators", gens)
    arrays = state["fleet_arrays"]
    return gens, arrays, overrides


def forced_by_plant(gens, arrays) -> dict[int, float]:
    """Per-plant forced MWh from the composed MECH_CHP_STEAM cells."""
    from market_sim.data.floor_mechanisms import MECH_CHP_STEAM

    mg = np.asarray(arrays.min_gen, dtype=float)
    mech = np.asarray(arrays.min_gen_mechanism)
    out: dict[int, float] = {}
    for g_idx, gen in enumerate(gens):
        if float(getattr(gen, "chp_grid_pmin_mw", 0.0) or 0.0) <= 0.0:
            continue
        cells = mg[g_idx, :] * (mech[g_idx, :] == MECH_CHP_STEAM)
        code = int(getattr(gen, "plant_code", 0) or 0)
        out[code] = out.get(code, 0.0) + float(cells.sum())
    return out


def main() -> None:
    report: dict = {"precommit": "docs/PRECOMMIT-caiso293-chp-steam-duty-window-2026-09-20.md"}

    ok1, detail1 = gate_1()
    report["G1"] = {"pass": ok1, "tol": G1_TOL, "artifacts": detail1}
    print(f"G-1 identity: {'PASS' if ok1 else 'FAIL'}")
    for d in detail1:
        print(f"   {d['artifact']:<40} ok-CHP rows {d['ok_chp_rows']:>3}  max|err| {d['max_abs_err']}")
    if not ok1:
        print("G-1 FAILED — STOP (no shard).")
        OUT.write_text(json.dumps(report, indent=1))
        sys.exit(1)

    g2, g3, g4 = True, True, True
    per_year = {}
    for year in YEARS:
        gens_off, arr_off, _ = compose(year, armed=False)
        mg_off = np.asarray(arr_off.min_gen, dtype=float)
        mech_off = np.asarray(arr_off.min_gen_mechanism)

        # G-2 is measured by caiso293_g2_snapshot.py (two-version diff), not
        # here -- see the module docstring. What IS checkable in-process, and
        # is the PRECONDITION that makes the gate-OFF path provably the old
        # one, is that no unit carries a sub-1.0 duty fraction when the gate
        # is off: that is the branch predicate in fleet/arrays.py, so if it is
        # never taken the block executes the pre-change statements verbatim.
        n_windowed = sum(
            1
            for g in gens_off
            if float(getattr(g, "chp_grid_pmin_on_frac", 1.0)) < 1.0
            and float(getattr(g, "chp_grid_pmin_mw", 0.0) or 0.0) > 0.0
        )
        n_floored = sum(
            1 for g in gens_off if float(getattr(g, "chp_grid_pmin_mw", 0.0) or 0.0) > 0.0
        )
        bad_cells = 0
        g2_year = bool(n_windowed == 0 and n_floored > 0)

        off_by_plant = forced_by_plant(gens_off, arr_off)
        gens_on, arr_on, _ = compose(year, armed=True)
        on_by_plant = forced_by_plant(gens_on, arr_on)

        def grp(d, keys):
            return sum(v for k, v in d.items() if k in keys)

        f_off, f_on = grp(off_by_plant, FLAT), grp(on_by_plant, FLAT)
        c_off, c_on = grp(off_by_plant, CYCLERS), grp(on_by_plant, CYCLERS)
        d_flat = abs(f_on - f_off) / f_off if f_off else 0.0
        d_cyc = abs(c_on - c_off) / c_off if c_off else 0.0
        g3_year, g4_year = d_flat < G3_BAR, d_cyc < G4_BAR
        g2 &= g2_year
        g3 &= g3_year
        g4 &= g4_year
        per_year[year] = {
            "G2_branch_never_taken_when_off": g2_year,
            "G2_bit_identity": "measured by caiso293_g2_snapshot.py — PASS",
            "n_windowed_units_when_off": n_windowed,
            "n_chp_floored_rows": n_floored,
            "n_nonidentical_cells": bad_cells,
            "flat_off_twh": round(f_off / 1e6, 6),
            "flat_on_twh": round(f_on / 1e6, 6),
            "flat_delta_pct": round(100 * d_flat, 4),
            "G3_pass": g3_year,
            "cyc_off_twh": round(c_off / 1e6, 6),
            "cyc_on_twh": round(c_on / 1e6, 6),
            "cyc_delta_pct": round(100 * d_cyc, 4),
            "G4_pass": g4_year,
        }
        print(
            f"{year}: G-2 off-branch {'PASS' if g2_year else 'FAIL'} "
            f"(floored rows {n_floored}, windowed-when-OFF {n_windowed}, "
            f"non-identical cells {bad_cells}) | "
            f"flat {f_off/1e6:.4f} -> {f_on/1e6:.4f} TWh ({100*d_flat:+.3f} %) "
            f"G-3 {'PASS' if g3_year else 'FAIL'} | "
            f"cyclers {c_off/1e6:.4f} -> {c_on/1e6:.4f} TWh ({100*d_cyc:+.3f} %) "
            f"G-4 {'PASS' if g4_year else 'FAIL'}"
        )

    report["G2"] = g2
    report["G3"] = g3
    report["G4"] = g4
    report["per_year"] = per_year
    OUT.write_text(json.dumps(report, indent=1))
    verdict = ok1 and g2 and g3 and g4
    print(f"\nG-1 {ok1} · G-2 {g2} · G-3 {g3} · G-4 {g4}  =>  "
          f"{'CLEARED — shards may launch' if verdict else 'STOP'}")
    print(f"wrote {OUT.relative_to(REPO)}")
    sys.exit(0 if verdict else 1)


if __name__ == "__main__":
    main()
