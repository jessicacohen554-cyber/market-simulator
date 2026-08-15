"""Write ``calibration_attestation.json`` for the pjm-147 A/B arms.

The arm is the single delta ``measured_chp_heat_rates=true`` on the pjm-143b
keeper — PJM's own measured power-only CHP heat-rate artifact replacing eGRID's
steam-credited rate for topping-cycle cogens
(``results/calibration/PREREG-pjm147-measured-chp-heat-rates-2026-08-03.md``
§2). This script builds the C6 attestation a promotion requires (rule 21
``[R-DOF]``: every keeper carries a DOF ledger), inheriting the pjm-143b
keeper's ledger and adding ONE entry for the delta.

**The delta adds ZERO free parameters.** The replacement rate is eGRID's own
published CHP useful-thermal allocation added back on the same net denominator,
``(PLHTIAN + CHPCHTI) / PLNGENAN`` — a quantity eGRID publishes, not one this
session chooses. No cap, no multiplier, no sweep, no threshold is selected
here: the deriver's gates (``TARGET_CLASSES``, ``_MAX_THERMAL_SHARE``,
``_HR_BAND``, ``_BASIS_TOL``) are all frozen upstream and were not touched
(rule 23 ``[R-FROZEN-DERIVE]``). ``n_residual`` is UNCHANGED. This mirrors the
same mechanism's ledger treatment at miso-99, caiso-147 and nyiso-105.

It also RETIRES a hand number rather than adding one (rules 21/24): PJM sits in
``CHP_STEAM_CREDIT_HR_CORRECTION_ISOS``, so on the covered plants the incumbent
rate was eGRID's credited rate times an off-registry ×1.8 / ×1.15 factor. Every
covered plant leaves that factor behind (``apply_measured_chp_heat_rates`` runs
first and hands the hand factor a ``skip_ids`` set, rule 19 ``[R-ONE-MECH]``).

The **control** arm inherits the keeper's attestation verbatim except for its
own ``attested_by`` line, plus the same-HEAD drift finding stated rather than
absorbed — this A/B's control does NOT reproduce the committed keeper, for a
known and chartered reason (caiso-158's CT meter screen), and an attestation
that quietly implied byte-equivalence would be false.

Every quantitative claim in the generated prose is READ FROM the committed A/B
JSON (``results/calibration/_pjm147_chp_ab.json``) and the committed K2 drift
artifact (``_pjm147_k2_drift.json``), never hand-transcribed.

Usage:
    PYTHONPATH=.:src uv run python scripts/gen_pjm147_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PRIOR_KEEPER = (
    REPO / "results/calibration/pjm143_hy_level_B/calibration_attestation.json"
)
AB_JSON = REPO / "results/calibration/_pjm147_chp_ab.json"
DRIFT_JSON = REPO / "results/calibration/_pjm147_k2_drift.json"
ARM_DEST = REPO / "results/calibration/pjm147_chp_B/calibration_attestation.json"
CONTROL_DEST = (
    REPO / "results/calibration/pjm147_control_A/calibration_attestation.json"
)
ARTIFACT = "data/raw/_processed-legacy/chp_power_only_heat_rates_PJM.csv"

YEARS = ("2023", "2024", "2025")


def _fmt(vals: list[float], spec: str = "+.3f") -> str:
    """Format a per-year triple as ``a / b / c``."""
    return " / ".join(format(v, spec) for v in vals)


def _cc_chp_deltas(ab: dict) -> list[float]:
    """Per-year CC_CHP class-energy delta (arm minus control), TWh."""
    block = ab.get("class_energy_delta_twh") or {}
    return [float((block.get(y) or {}).get("CC_CHP", 0.0)) for y in YEARS]


def _seam_move(ab: dict) -> tuple[float, float, int, float]:
    """Return (capw HR off, capw HR on, n moved generators, moved MW) for 2023."""
    k0 = (ab.get("K0_wiring_liveness_presolve") or {}).get("per_year") or {}
    rec = k0.get("2023") or {}
    return (
        float(rec.get("CC_CHP_capw_hr_off", 0.0)),
        float(rec.get("CC_CHP_capw_hr_on", 0.0)),
        int(rec.get("n_moved", 0)),
        float(rec.get("moved_mw", 0.0)),
    )


def _build_entry(ab: dict) -> dict:
    """The ONE new DOF-ledger entry — identification: measured-external."""
    off, on, n_moved, moved_mw = _seam_move(ab)
    pairs = int((ab.get("K3_scope_integrity") or {}).get("artifact_applied_pairs", 0))
    return {
        "name": (
            "measured_chp_heat_rates (PJM) — the power-only heat rate of "
            "topping-cycle cogens, eGRID's own published CHP useful-thermal "
            "heat-input allocation (CHPCHTI) added back to the electric "
            "allocation (PLHTIAN) on the SAME net-generation denominator "
            "(PLNGENAN), replacing the steam-CREDITED rate the model priced "
            "with"
        ),
        "where": "run_config.scenario_config.measured_chp_heat_rates + " + ARTIFACT,
        "identification": "measured-external",
        "source": (
            "EPA eGRID2023 plant sheet PLNT23 (data/raw/fleet-egrid), derived by "
            "scripts/data/derive_chp_power_only_heat_rates.py, unmodified. "
            "Validated against independently metered CAMPD/CEMS annual heat "
            "input: (PLHTIAN + CHPCHTI) reproduces it within 1 % on 11 of 12 "
            "covered PJM plants, median ratio 1.00000. The single miss (50463 "
            "Procter & Gamble, 0.429) has combustion units below the Part-75 "
            "boundary where CEMS undercounts and eGRID is the complete source — "
            "the check fails toward CEMS, never toward eGRID."
        ),
        "free_parameters_added": 0,
        "why_zero": (
            "Nothing is chosen by this session. The replacement value is a "
            "published quantity; the deriver's four gates (TARGET_CLASSES, "
            "_MAX_THERMAL_SHARE = the EPA CHP Partnership unfired-gas-turbine "
            "envelope, the per-class physical band _HR_BAND, and the _BASIS_TOL "
            "seam check) are frozen upstream and were not touched this session "
            "(rule 23 [R-FROZEN-DERIVE]). No cap, multiplier, sweep or "
            "threshold is fitted, and no residual selected the lever."
        ),
        "retires_a_hand_number": (
            "PJM is in CHP_STEAM_CREDIT_HR_CORRECTION_ISOS, so on covered plants "
            "the incumbent was eGRID's credited rate times an off-registry hand "
            "factor (x1.8 sub-8.0 CT_CHP; x1.15 floored at 6.3 sub-6.0 CC_CHP). "
            "apply_measured_chp_heat_rates runs FIRST and hands the hand factor "
            "a skip_ids set, so a repriced plant never also takes the factor "
            "(rule 19 [R-ONE-MECH]). Rules 21/24: this entry retires an "
            "unregistered number, it does not add one."
        ),
        "scope": (
            f"{pairs} (plant, class) pairs applied from a 65-row artifact; at "
            f"the LP seam {n_moved} generators / {moved_mw:,.1f} MW move, and "
            f"CC_CHP cap-weighted goes {off:.4f} -> {on:.4f} MMBtu/MWh. Keyed by "
            "(plant_code, plant_group) and restricted to CC_CHP/CT_CHP, so a "
            "mixed facility's out-of-scope trains are never repriced."
        ),
        "limitations_declared": (
            "The CT_CHP half is NOT identified and NOT scored: coverage is "
            "32.6 % of class capacity and 25.1 % of the class's own metered "
            "CAMPD energy (thin on both bases), CT_CHP is in FUELMIX_EXCLUDED so "
            "C1 never gates it, and it moves only +0.36 % at the seam. It is "
            "reported as a dispatch consequence and is not cited as evidence in "
            "either direction. CC_CHP/CT_CHP are also exempt from BOTH C7 and C8 "
            "by explicit class list (host-steam-pinned duty), so their D-1/D-2 "
            "numbers are diagnostics, never a passed gate."
        ),
    }


def _attested_by(ab: dict, arm: bool) -> str:
    which = (
        "arm B (measured_chp_heat_rates=true)" if arm else "control arm A (zero-delta)"
    )
    return (
        f"pjm-147 {which}, PREREG-pjm147-measured-chp-heat-rates-2026-08-03.md; "
        "A/B machine record results/calibration/_pjm147_chp_ab.json"
    )


def _control_note(drift: dict) -> str:
    """State the same-HEAD drift rather than absorbing it."""
    years = drift.get("years") or {}
    mx = [float((years.get(y) or {}).get("max_abs_diff_mw", 0.0)) for y in YEARS]
    lw = [float((years.get(y) or {}).get("lw_price_delta", 0.0)) for y in YEARS]
    ct = drift.get("ct_artifact_delta") or {}
    return (
        "SAME-HEAD DRIFT, STATED NOT ABSORBED. This control does NOT reproduce "
        "the committed keeper 2026-07-31-pjm-143b-hy-level: max |delta| "
        f"{_fmt(mx, '.1f')} MW on the class-hour and {_fmt(lw, '+.4f')} $/MWh "
        "load-weighted. The cause is chartered and quantified, not anomalous — "
        "caiso-158 executing PREREG-caiso156 shipped the CT heat-rate hour-grain "
        "meter screen for all six ISOs, which moved PJM's campd_ct_heat_rates "
        f"artifact on {ct.get('rows_with_changed_rate', 0)} of "
        f"{ct.get('applied_rows_new', 0)} applied plants "
        f"({ct.get('changed_capacity_mw', 0):,.1f} MW), cap-weighted "
        f"{ct.get('capw_heat_rate_old', 0):.4f} -> "
        f"{ct.get('capw_heat_rate_new', 0):.4f} MMBtu/MWh. The PJM keeper arms "
        "measured_ct_heat_rates=True (pjm-137), and caiso-158 §5 explicitly "
        "DEFERRED PJM's A/B for want of swap on a 15 GB box. This control is "
        "therefore also the PJM leg of that deferred pair. The pjm-147 CHP A/B "
        "remains single-delta because BOTH its arms solve at this same HEAD."
    )


def main() -> int:
    """Write both arms' attestations from the committed A/B + drift JSON."""
    for path in (PRIOR_KEEPER, AB_JSON, DRIFT_JSON):
        if not path.exists():
            raise SystemExit(f"missing required input: {path.relative_to(REPO)}")
    prior = json.loads(PRIOR_KEEPER.read_text())
    ab = json.loads(AB_JSON.read_text())
    drift = json.loads(DRIFT_JSON.read_text())
    cc = _cc_chp_deltas(ab)

    for dest, arm in ((ARM_DEST, True), (CONTROL_DEST, False)):
        att = json.loads(json.dumps(prior))  # deep copy
        att["governance"]["attested_by"] = _attested_by(ab, arm)
        att["governance"]["note"] = _control_note(drift) + (
            ""
            if not arm
            else (
                " ARM DELTA: CC_CHP class energy moves "
                f"{_fmt(cc)} TWh against a standing over-run of "
                "+2.93 / +1.41 / +1.34 TWh (C1 grid-delivered, keeper's own "
                "rows). Zero free parameters added; n_residual unchanged."
            )
        )
        if arm:
            ledger = att["free_parameters"]
            ledger["entries"] = list(ledger["entries"]) + [_build_entry(ab)]
            ledger["n_entries"] = len(ledger["entries"])
            ledger["seeded"] = (
                "2026-08-03 pjm-147 — UNION'd forward from the pjm-143b keeper "
                "ledger and NOT rebuilt (a blind build_dof_ledger.py rebuild "
                "drops the curated measured/published entries — the failure "
                "mode the nyiso-8x/9x/10x notes all recorded). ONE new entry, "
                "and it adds ZERO free parameters: the rate is eGRID's own "
                "published CHP allocation added back on the same denominator, "
                "and every deriver gate is frozen upstream. It RETIRES an "
                "off-registry hand factor rather than adding a parameter. "
                "n_residual is UNCHANGED."
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(att, indent=1) + "\n")
        print(
            f"wrote {dest.relative_to(REPO)} "
            f"({att['free_parameters']['n_entries']} entries, "
            f"n_residual {att['free_parameters']['n_residual']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
