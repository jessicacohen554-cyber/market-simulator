"""caiso-294 ARM A: what does windowing the DILUTED level actually cost?

ZERO LP. Re-uses ``caiso293_gates.compose`` verbatim, so the control leg is
byte-for-byte the same construction the pre-registered gates measured.

THE QUESTION. caiso-293 armed ``chp_steam_duty_window`` with the UNDILUTED
level (``median_cf``) in a window of ``on_frac x live-hours``, which conserves
annual forced energy by construction (``on_frac x L x H == L x on_frac x H``)
and failed G-4 at -10.220 % in 2025 only because the undiluted level SATURATES
against ``pmax x availability`` (the floor runs 5-14x the capacity of the
tranches carrying it).

ARM A keeps ``steam_level_cf`` -- the diluted, energy-average level -- and
confines ONLY its hours. That is **not** energy-conserving: the level is
already ``on_freq x p50(on)``, so holding it in ``on_frac`` of the hours
delivers ``on_frac^2 x p50(on) x H``, i.e. the annual forced energy falls by
roughly a factor of ``on_frac`` (0.05-0.22 on these plants). This probe
MEASURES that factor rather than asserting it, on the same gate arithmetic
(G-3 flat-host controls, G-4 cyclers) the PRECOMMIT declared.

Arm A is reached WITHOUT touching ``src/``: ``fleet/assembly.py`` consumes the
loader's ``(on_frac, level_on_cf)`` pair as ``chp_duty_on_frac, pmin_cf``, so
returning ``(on_frac, on_frac x level_on_cf) == (on_frac, steam_level_cf)``
leaves the level exactly where the unarmed path puts it and changes only the
hours. The patch is applied to the symbol ``assembly`` imported, so the armed
build differs from the control in exactly one respect.

Run: ``PYTHONPATH=.:src python scripts/probes/caiso294_arm_a_energy.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes.caiso293_gates import (  # noqa: E402
    BUNDLE,
    CYCLERS,
    FLAT,
    G3_BAR,
    G4_BAR,
    YEARS,
    compose,
    forced_by_plant,
)

OUT = REPO / "results/calibration/_caiso294_arm_a.json"


def patch_arm_a() -> None:
    """Dilute the duty map's level back to ``steam_level_cf`` (ARM A)."""
    import market_sim.data.fleet.assembly as assembly

    original = assembly.thermal_tranche_chp_steam_duty
    if getattr(original, "_arm_a", False):
        return

    def diluted(iso: str, per_unit: bool = False, merit_guard: bool = False):
        out = original(iso, per_unit, merit_guard)
        # (on_frac, level_on_cf) -> (on_frac, on_frac x level_on_cf).
        # The second element is exactly ``steam_level_cf``, the value the
        # unarmed path already assigned to ``pmin_cf``, so ARM A's level is
        # the status-quo level and only the hours move.
        return {k: (v[0], v[0] * v[1]) for k, v in out.items()}

    diluted._arm_a = True  # type: ignore[attr-defined]
    assembly.thermal_tranche_chp_steam_duty = diluted  # type: ignore[assignment]


def plant_detail(gens) -> dict[int, dict]:
    """Per-plant floor MW and duty fraction as the fleet build assembled them."""
    out: dict[int, dict] = {}
    for gen in gens:
        mw = float(getattr(gen, "chp_grid_pmin_mw", 0.0) or 0.0)
        if mw <= 0.0:
            continue
        code = int(getattr(gen, "plant_code", 0) or 0)
        row = out.setdefault(code, {"floor_mw": 0.0, "on_frac": 1.0})
        row["floor_mw"] += mw
        row["on_frac"] = min(
            row["on_frac"], float(getattr(gen, "chp_grid_pmin_on_frac", 1.0))
        )
    return out


def main() -> None:
    report: dict = {
        "arm": "A — diluted level (steam_level_cf), hours confined to the duty window",
        "control": "keeper recipe, chp_steam_duty_window off",
        "reference": "results/calibration/_caiso293_gates.json (ARM B, undiluted median_cf)",
    }
    per_year: dict[str, dict] = {}
    for year in YEARS:
        gens_off, arr_off, _ = compose(year, armed=False)
        off_by_plant = forced_by_plant(gens_off, arr_off)

        patch_arm_a()
        gens_on, arr_on, _ = compose(year, armed=True)
        on_by_plant = forced_by_plant(gens_on, arr_on)
        detail_off = plant_detail(gens_off)
        detail_on = plant_detail(gens_on)

        def grp(d, keys):
            return sum(v for k, v in d.items() if k in keys)

        f_off, f_on = grp(off_by_plant, FLAT), grp(on_by_plant, FLAT)
        c_off, c_on = grp(off_by_plant, CYCLERS), grp(on_by_plant, CYCLERS)
        d_flat = abs(f_on - f_off) / f_off if f_off else 0.0
        d_cyc = abs(c_on - c_off) / c_off if c_off else 0.0
        plants = {}
        for code in sorted(CYCLERS):
            plants[str(code)] = {
                "floor_mw_off": round(detail_off.get(code, {}).get("floor_mw", 0.0), 3),
                "floor_mw_armA": round(detail_on.get(code, {}).get("floor_mw", 0.0), 3),
                "on_frac": round(detail_on.get(code, {}).get("on_frac", 1.0), 4),
                "forced_mwh_off": round(off_by_plant.get(code, 0.0), 1),
                "forced_mwh_armA": round(on_by_plant.get(code, 0.0), 1),
                "ratio": (
                    round(on_by_plant.get(code, 0.0) / off_by_plant[code], 4)
                    if off_by_plant.get(code)
                    else None
                ),
            }
        per_year[str(year)] = {
            "flat_off_twh": round(f_off / 1e6, 6),
            "flat_armA_twh": round(f_on / 1e6, 6),
            "flat_delta_pct": round(100 * d_flat, 4),
            "G3_pass": bool(d_flat < G3_BAR),
            "cyc_off_twh": round(c_off / 1e6, 6),
            "cyc_armA_twh": round(c_on / 1e6, 6),
            "cyc_delta_pct": round(100 * d_cyc, 4),
            "G4_pass": bool(d_cyc < G4_BAR),
            "plants": plants,
        }
        print(
            f"{year}: flat {f_off/1e6:.4f} -> {f_on/1e6:.4f} TWh "
            f"({100*d_flat:+.3f} %) G-3 {'PASS' if d_flat < G3_BAR else 'FAIL'} | "
            f"cyclers {c_off/1e6:.4f} -> {c_on/1e6:.4f} TWh "
            f"({-100*d_cyc if c_on < c_off else 100*d_cyc:+.3f} %) "
            f"G-4 {'PASS' if d_cyc < G4_BAR else 'FAIL'}"
        )

    report["per_year"] = per_year
    OUT.write_text(json.dumps(report, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
