"""nyiso-121 G-1 — is ``miso_pjm_border_anchor`` observable on the MISO keeper?

**CONSTRUCTION probe. No LP, no solve, no dual.** The binding lesson of
nyiso-115 G2 / nyiso-118 is that ``dual`` and ``held_mw`` are solved
co-optimization outputs: a scope question gated on them can only pass when the
mechanism does nothing, and a provably-unchanged construction can still move its
dual through general equilibrium. So this probe builds the object **twice at one
HEAD** and diffs it.

**The question.** MISO keeper ``2026-08-04-miso-122b-scope-gate`` arms BOTH
``miso_pjm_border_anchor`` and ``miso_seam_measured_ladder``. The ladder's own
docstring (``model/interchange/miso.py``) states it

    Runs LAST among the seam price overwrites, displacing the
    ``miso_pjm_border_anchor`` / ``miso_pjm_lmp_import_pricing`` prices on any
    row it covers (the flags are alternatives, never stacked).

and ``scripts/run_calibration.py`` applies them in exactly that order. If
``MISO_SEAM_LADDER_BY_YEAR`` covers every PJM band in every keeper year, the
border anchor's re-anchored heat rate is overwritten before the solve ever sees
it — the caiso-161 §5 / pjm-151 "armed-looking but dead" shape, restated for
MISO.

**G-1, pre-registered in PREREG-nyiso121-miso-matrix-column-2026-08-04.md §4:**

* PASS (inert)  — the two constructions are EXACTLY equal (``np.array_equal``,
  not a tolerance: float32 exact equality, per nyiso-116 G3/P4) in all three
  keeper years, with the ladder ON in both.
* FAIL (live)   — any band differs; the O-1 hypothesis is WRONG and that is
  RECORDED as a failed pre-registration, never quietly redefined.
* UNINFORMATIVE — the probe cannot build a MISO seam at all. Reported as such,
  NEVER as a pass.

**The positive control is mandatory** (a same-HEAD instrument must be shown to
SEPARATE on something before its silence is trusted): the same two
constructions are also run with the ladder OFF, where the border anchor MUST
move the PJM bands. If that control does not separate, the whole probe is void.

This probe adjudicates NOTHING and moves no matrix cell (rules 25 / 28(d)). It
produces an OBSERVATION about what the MISO keeper's ``run_config.json``
overstates.

Usage::

    PYTHONPATH=.:src python scripts/probes/_nyiso121_miso_border_anchor_displacement_probe.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from market_sim.config.interchange_config import (
    MISO_PJM_BORDER_HR_BY_YEAR,
    MISO_SEAM_LADDER_BY_YEAR,
)
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.transmission import (
    _REF_EXPORT_MARK,
    _REF_IMPORT_MARK,
    build_reference_price_node,
    inject_miso_seam_ladder_prices,
    inject_reference_price_mc,
)

YEARS = (2023, 2024, 2025)
HOURS = 8760
SENTINEL = -123.0
OUT = Path("results/calibration/nyiso121_miso_border_anchor_displacement_probe.json")


def _fresh():
    """Build the MISO reference-price seam node and a sentinel mc, at one HEAD."""
    node = build_reference_price_node("MISO")
    zone_names = sorted({g.zone for g in node})
    fleet = generators_to_fleet_arrays(node, zone_names, hours=HOURS)
    mc = np.full((len(node), HOURS), SENTINEL, dtype=np.float32)
    return fleet, mc


def _seam_rows(fleet) -> dict[str, list[int]]:
    """Row indices per seam name, both directions (PJM is the seam under test)."""
    rows: dict[str, list[int]] = {}
    for row, uid in enumerate(fleet.unit_ids):
        for mark in (_REF_IMPORT_MARK, _REF_EXPORT_MARK):
            if mark in uid:
                name = uid.rsplit(mark, 1)[1].partition("#")[0]
                rows.setdefault(name, []).append(row)
    return rows


def _construct(year: int, *, border_anchor: bool, ladder: bool):
    """One construction: the keeper's seam price overwrites, in run_calibration order."""
    fleet, mc = _fresh()
    priced = inject_reference_price_mc(
        fleet, mc, "MISO", year, border_anchor=border_anchor
    )
    laddered = False
    if ladder:
        # Runs LAST among the seam price overwrites, exactly as
        # scripts/run_calibration.py sequences it.
        laddered = inject_miso_seam_ladder_prices(fleet, mc, "MISO", year)
    return fleet, mc, priced, laddered


def main() -> int:
    result: dict = {
        "probe": "nyiso-121 G-1 — miso_pjm_border_anchor displacement (CONSTRUCTION)",
        "prereg": "results/calibration/PREREG-nyiso121-miso-matrix-column-2026-08-04.md §4",
        "keeper": "2026-08-04-miso-122b-scope-gate",
        "no_lp": True,
        "border_hr_by_year": MISO_PJM_BORDER_HR_BY_YEAR,
        "ladder_years": sorted(MISO_SEAM_LADDER_BY_YEAR),
        "years": {},
    }

    verdicts: list[str] = []
    controls: list[bool] = []

    for year in YEARS:
        try:
            f_on, mc_on, priced_on, lad_on = _construct(
                year, border_anchor=True, ladder=True
            )
            _f_off, mc_off, priced_off, lad_off = _construct(
                year, border_anchor=False, ladder=True
            )
            # Positive control: same pair with the ladder OFF.
            _fc_on, mcc_on, _pc_on, _ = _construct(
                year, border_anchor=True, ladder=False
            )
            _fc_off, mcc_off, _pc_off, _ = _construct(
                year, border_anchor=False, ladder=False
            )
        except Exception as exc:  # pragma: no cover - reported, never swallowed
            result["years"][year] = {"status": "UNINFORMATIVE", "error": repr(exc)}
            verdicts.append("UNINFORMATIVE")
            controls.append(False)
            continue

        if not (priced_on and priced_off):
            result["years"][year] = {
                "status": "UNINFORMATIVE",
                "reason": "inject_reference_price_mc priced no seam row",
            }
            verdicts.append("UNINFORMATIVE")
            controls.append(False)
            continue

        rows = _seam_rows(f_on)
        pjm_rows = rows.get("PJM", [])

        # --- the treatment comparison: ladder ON in BOTH arms ---
        equal = bool(np.array_equal(mc_on, mc_off))  # float32 EXACT, no tolerance
        pjm_equal = bool(np.array_equal(mc_on[pjm_rows], mc_off[pjm_rows]))
        max_abs = float(np.max(np.abs(mc_on - mc_off))) if mc_on.size else 0.0

        # --- the mandatory positive control: ladder OFF, anchor must bite ---
        ctrl_sep = not bool(np.array_equal(mcc_on[pjm_rows], mcc_off[pjm_rows]))
        ctrl_max = (
            float(np.max(np.abs(mcc_on[pjm_rows] - mcc_off[pjm_rows])))
            if pjm_rows
            else 0.0
        )
        # The control must ALSO leave the non-PJM seams alone (the anchor is
        # PJM-scoped) — a control that moves everything is not a control.
        other = [r for name, rs in rows.items() if name != "PJM" for r in rs]
        ctrl_other_equal = bool(np.array_equal(mcc_on[other], mcc_off[other]))

        status = "PASS_INERT" if equal else "FAIL_LIVE"
        if not ctrl_sep:
            status = "VOID_CONTROL_DID_NOT_SEPARATE"

        result["years"][year] = {
            "status": status,
            "ladder_applied_both_arms": bool(lad_on and lad_off),
            "n_seam_rows": int(len(f_on.unit_ids)),
            "n_pjm_rows": len(pjm_rows),
            "seams": {k: len(v) for k, v in sorted(rows.items())},
            "treatment_all_rows_exactly_equal": equal,
            "treatment_pjm_rows_exactly_equal": pjm_equal,
            "treatment_max_abs_delta": max_abs,
            "control_pjm_separates": ctrl_sep,
            "control_pjm_max_abs_delta": ctrl_max,
            "control_non_pjm_seams_untouched": ctrl_other_equal,
        }
        verdicts.append(status)
        controls.append(ctrl_sep)

    if all(v == "PASS_INERT" for v in verdicts) and all(controls):
        overall = "G-1 PASS — miso_pjm_border_anchor is PROVABLY UNOBSERVABLE on the keeper"
    elif any(v == "FAIL_LIVE" for v in verdicts):
        overall = "G-1 FAIL — the flag is LIVE; the O-1 hypothesis is WRONG (recorded)"
    elif not all(controls):
        overall = "G-1 VOID — the positive control did not separate; instrument untrusted"
    else:
        overall = "G-1 UNINFORMATIVE — the construction could not be built"
    result["verdict"] = overall

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps(result, indent=2, default=str))
    print(f"\n{overall}\nwritten: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
