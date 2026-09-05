"""Generate the miso-210 A/B legs' calibration attestations from the keeper's.

The gen_miso186/.../202 pattern. Both legs are the miso-202 keeper recipe
re-solved via ``--replay-bundle``; the arm carries the max-gen CLOCK repair —
``maxgen_events.MODEL_TZ_BY_ISO['MISO']`` (and the M-2 deriver's twin constant)
moved from EST to the measured CST model clock, plus the re-derived M-2
extract. Each leg's attestation is the keeper's with a rewritten
``governance.attested_by`` and this session's disclosures appended AT FULL
MAGNITUDE.

**No new ledger entry.** The arm introduces no parameter: it corrects a
constant to a measured property of the model's own hour index (two r = 1.000
witnesses, miso-208 §0 item 2). ``n_entries`` stays 41 and ``n_residual`` 2.
The clock is recorded as a DISCLOSURE, not a free parameter — there is nothing
that could have been chosen differently once the model clock was measured.

Run this INSTEAD of ``scripts/build_dof_ledger.py`` (which would drop the
documented entries), and because a ``--replay-bundle`` solve writes NO
attestation at all (the miso-200 vacuous-pass trap).

Usage:
    python3 scripts/gen_miso210_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "results/calibration/miso202_unitclip_B/calibration_attestation.json"
CONTROL = REPO / "results/calibration/miso210_control_A"
ARM = REPO / "results/calibration/miso210_clock_B"
GATES = REPO / "results/calibration/_miso210_ab_gates.json"


def build(dst: Path, armed: bool, gates: dict) -> None:
    d = json.loads(SRC.read_text())
    leg = (
        "ARM leg B (MODEL_TZ_BY_ISO['MISO'] Etc/GMT+5 -> Etc/GMT+6 + re-derived M-2 extract)"
        if armed
        else "CONTROL leg A (HEAD 8f5cb32c: EST placement, committed extract)"
    )
    d["governance"]["attested_by"] = (
        f"miso-210 A/B (2026-09-04), {leg}: control miso210_control_A vs arm "
        "miso210_clock_B, both MISO 2023+2024+2025 in one invocation, years "
        "sequential, solved in-session and never on CI (rule 12/16), both from "
        "the SAME committed keeper recipe (2026-09-03-miso-202-unitclip) via "
        "--replay-bundle. The delta is NOT a ScenarioConfig field: it is one "
        "clock constant (mirrored in the M-2 deriver, with the deriver's DA-hub "
        "certificate record shifted by the same hour) and the extract that "
        "constant regenerates. Scored by scripts/probes/_miso210_ab_gates.py, "
        "COMMITTED BLIND with the PREREG (83e73bf8) before any window was "
        "re-placed and before either leg's numbers; S-1/S-2/S-3 restated for a "
        "code+data delta (zero config diffs + commit/extract identity; exact "
        "one-hour placement shift off the production functions; guard-2 "
        "certificate invariance as a hard void). "
        + str(gates.get("verdict", "verdict pending"))
    )
    d.setdefault("disclosures", {})["miso210_ab"] = DISCLOSURE
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(d, indent=1))
    print(
        f"wrote {dst.relative_to(REPO)} "
        f"(n_entries={d['free_parameters']['n_entries']}, "
        f"n_residual={d['free_parameters']['n_residual']})"
    )


# Rewritten by the session once the pair is scored, so the disclosure quotes
# MEASURED numbers rather than restating the PREREG's expectations. The guard in
# __main__ refuses to write while this is still the placeholder.
_PLACEHOLDER = "PLACEHOLDER"
DISCLOSURE = (
    "REPORTED AT FULL MAGNITUDE. (1) THE DEFECT: maxgen_events.MODEL_TZ_BY_ISO"
    "['MISO'] was Etc/GMT+5 (EST, MISO market time) while the model's 8760 "
    "index is CST hour-beginning (miso-208, two r = 1.000 witnesses), so both "
    "armed consumers of the declared-window registry — maxgen_emergency_tier_"
    "pricing and, through the M-2 deriver sharing the constant, unit_outage_"
    "maxgen_events — fired ONE HOUR LATE in every window. The repair is one "
    "constant (Etc/GMT+6), mirrored by the deriver reading the shared loader, "
    "the deriver's DA-hub certificate record shifted by the same hour, and the "
    "M-2 extract that regenerates (2,174 -> 2,171 rows, 41,874 -> 41,677 MW, "
    "-0.47 %; guard-2 n_cert IDENTICAL on all 9 registry rows). NO ScenarioConfig "
    "field, NO new mechanism, NO new ledger entry: n_entries 41 -> 41, "
    "n_residual 2 -> 2. (2) EVERY GATE IS SILENT. S-0 control BIT-IDENTICAL to "
    "the keeper on all 9 sidecars (max_abs_diff 0.0) and its D1/D2/D4 "
    "diagnostics byte-identical. S-1 zero config diffs (783 fields), legs at "
    "7812291a vs a9b67b53, the arm's extract sha256 equal to the phase-0 "
    "scratchpad prediction. S-2 the tier-cost array and the M-2 derate hour set "
    "move by EXACTLY -1 h in every year off the production functions. S-3 "
    "certificate invariance PASS. K-1 no band exit, largest class-year move "
    "0.002 TWh (CC_REGULAR-2024 +6.942 -> +6.940; ST_GAS-2024 -7.487 -> -7.486). "
    "K-2 C3b 0.081/0.109/0.182 -> 0.081/0.111/0.182. K-3 zero new D-4 failures "
    "(57 rows both legs). K-4 D-1 ST_GAS identical. K-5 status map IDENTICAL. "
    "(3) THE ONE SCORED VALUE THAT MOVED, and why, NEVER the justification "
    "(rule 1): C3a-2024 -4.613 -> -4.396 (+0.217 pp, inside the pre-registered "
    "[0, +1.5]); C3a-2023 +0.1218 and C3a-2025 -12.3845 UNCHANGED to the decimal. "
    "The PREREG's named 2024 mechanism was WRONG: it predicted the lost hour "
    "(19:00 CST) carried $500 slack to be re-priced; phase 0 measured that hour "
    "at 0.0 MWh of the window's 19,384 MWh. The move comes from the GAINED hour "
    "instead: 12:00 CST Aug 26 2024 — the declared first hour of the Warning — "
    "now takes the 10.2 GW M-2 derate and the $500 floor, and prices at $447.5 "
    "with 570 MWh of slack against the control's $62.1 and none; 19:00 CST "
    "falls $66.2 -> $49.2 as its misplaced derate is removed. Window slack "
    "19,384 -> 19,567 MWh. In 2023 the edges move 11:00 CST Aug 24 $44.9 -> "
    "$53.7 and 23:00 $36.1 -> $33.7; in 2025 11:00 CST Jul 28 $50.8 -> $58.5; "
    "the C3a comparator is unmoved in both years. (4) C8 unchanged: ST_GAS "
    "forced share 0.1553/0.1529/0.2714 -> 0.1552/0.1529/0.2714 (|delta| <= "
    "0.00006 vs the 0.0005 epsilon). (5) miso-208's 'tier floor silent in every "
    "2025 Warning+ hour' RE-SCORED on the corrected clock: HOLDS (slack 0 in all "
    "72 corrected hours, min idle thermal 2.178 GW unchanged, max price $141.7). "
    "(6) DISCLOSED DRIFT the repair rides on: the forward deriver could not run "
    "at HEAD at all (the 2021/2022 registry rows had no DA hub record; repaired "
    "by dropping uncertifiable years with notice), and at the OLD clock it "
    "reproduces the committed relabelled extract to one 1 MW row (New Ulm 2001 "
    "unit 7, ST_CHP, Jul-24-2025) plus 16 informational plant_capacity_mw "
    "cells, so the arm carries that 1 MW of fleet drift with the clock. The "
    "CAMPD grids stay on plant-local standard time: the <= 1 h skew now sits on "
    "the EST-minority plants (IN/MI/KY) instead of the CST majority — named, "
    "not repaired. (7) MAIN DRIFT MEASURED: origin/main advanced 24 commits "
    "during the session; none touch src/ or the runners for MISO, and the one "
    "shared data file that moved (plant_emission_rates_v2) changed NYISO plant "
    "8906 rows only. Both legs remain one code state for MISO."
)


if __name__ == "__main__":
    if DISCLOSURE.startswith(_PLACEHOLDER):
        raise SystemExit(
            "refusing to write: DISCLOSURE is still the placeholder. Score the "
            "pair first, then replace it with the measured disclosure."
        )
    if not GATES.exists():
        raise SystemExit(f"refusing to write: {GATES} does not exist — score first.")
    gates = json.loads(GATES.read_text())
    build(CONTROL / "calibration_attestation.json", False, gates)
    build(ARM / "calibration_attestation.json", True, gates)
