"""Generate the miso-213 ARM leg's calibration attestation from the keeper's.

The gen_miso186/.../210 pattern. The arm is the miso-210 keeper recipe
re-solved via ``scripts/replay_keeper.py --set
miso_zonal_gas_basis_skip_923_priced=true`` (single delta). The CONTROL is the
keeper bundle itself (``miso210_clock_B``, already attested, never re-solved),
so only the arm's attestation is written: the keeper's with a rewritten
``governance.attested_by`` and this session's disclosures appended AT FULL
MAGNITUDE.

**No new ledger entry.** The arm introduces no parameter: a boolean SCOPE on an
existing measured input (rule 19 [R-ONE-MECH] — the EIA-923 print already
embeds the regional delivered premium the zonal basis adds). ``n_entries``
stays 41 and ``n_residual`` 2.

Run this INSTEAD of ``scripts/build_dof_ledger.py`` (which would drop the
documented entries), and because a replay solve writes NO attestation at all
(the miso-200 vacuous-pass trap).

Usage:
    python3 scripts/gen_miso213_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/miso210_clock_B/calibration_attestation.json"
ARM = REPO / "results/calibration/miso213_layering_B"
GATES = REPO / "results/calibration/_miso213_ab_gates.json"


def build(dst: Path, gates: dict) -> None:
    d = json.loads(SRC.read_text())
    d["governance"]["attested_by"] = (
        "miso-213 A/B (2026-09-05), ARM leg B (miso_zonal_gas_basis_skip_923_priced "
        "False -> True): control = the miso-210 keeper bundle miso210_clock_B itself "
        "(bit-identity of the replay channel established at miso-210 S-0, not "
        "re-solved) vs arm miso213_layering_B, MISO 2023+2024+2025 in one "
        "invocation, years sequential, solved in-session and never on CI (rule "
        "12/16), from the SAME committed keeper recipe via replay_keeper --set. "
        "The delta is ONE ScenarioConfig field (rule 24 registry): the MISO zonal "
        "basis skips the cells the EIA-923 print path priced. Scored by "
        "scripts/probes/_miso213_ab_gates.py, COMMITTED BLIND with the arm code "
        "before the solve; S-1 single delta, S-2 fuel-price liveness on the keeper "
        "chain, K-1..K-6, six pre-registered object gates. "
        + str(gates.get("verdict", "verdict pending"))
    )
    d.setdefault("disclosures", {})["miso213_ab"] = DISCLOSURE
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(d, indent=1))
    print(
        f"wrote {dst.relative_to(REPO)} "
        f"(n_entries={d['free_parameters']['n_entries']}, "
        f"n_residual={d['free_parameters']['n_residual']})"
    )


# Rewritten by the session once the arm is scored, so the disclosure quotes
# MEASURED numbers rather than restating the PREREG's expectations. The guard in
# __main__ refuses to write while this is still the placeholder.
_PLACEHOLDER = "PLACEHOLDER"
DISCLOSURE = (
    "REPORTED AT FULL MAGNITUDE. (1) THE DEFECT: miso_zonal_gas_basis added its "
    "mean-zero per-zone increment (N3045<ST>3 state delivered-to-electric-power "
    "minus Henry Hub) to EVERY gas cell, including the cells the EIA-923 print "
    "path (gas_plant_monthly_fuel_pricing, a harness default for every non-ERCOT "
    "ISO) had just priced from the plant's own print or the class-aware "
    "state/zone pool of other plants' prints — the same receipts the state series "
    "aggregates, so the regional delivered premium entered twice (rule 19 "
    "[R-ONE-MECH]; named at miso-212 §8, in every MISO keeper since gate 2). "
    "Phase 0 (_miso213_basis_layering.json) measured the print path pricing "
    "100.0 % of MISO gas capacity-hours in all three years (own print ~74 %, "
    "pool ~26 %), so on this recipe the repair removes the increment from every "
    "gas cell: in a MISO BACKCAST the mean-zero basis was fully redundant under "
    "the print path (disclosed in the PREREG §5 before the measurement); a "
    "trajectory cell — any forecast-mode cell — still receives it. (2) THE "
    "REPAIR: one default-off ScenarioConfig field, "
    "miso_zonal_gas_basis_skip_923_priced; apply_plant_monthly_fuel_prices "
    "returns its written-cell mask and the MISO applier skips those cells. ZERO "
    "FREE PARAMETERS, no new ledger entry (41 -> 41, n_residual 2 -> 2); the "
    "spread values are unchanged (mean over ALL gas rows), only the recipient set. "
    "(3) GATES: S-0 inherited (control = the keeper bundle, miso-210 bit-identity, "
    "not re-solved); S-1 single delta restated over the recorded configs (zero "
    "in-common diffs; five fields new on main since the keeper solved sit at their "
    "defaults) — an amendment made after the first scoring pass, disclosed; S-2 "
    "arm fuel prices live on the keeper chain (every masked cell equals "
    "F_nobasis). K-1 no C1 band exit; K-2 C3b 0.081/0.111/0.182 -> "
    "0.080/0.109/0.177; K-3 zero new D-4 failures, one cleared (2023 "
    "reliability_floor x ST_GAS plant 1122); K-4 D-1 ST_GAS profile_r "
    "0.941/0.956/0.977 -> 0.951/0.957/0.982; K-5 the ONLY status flip is "
    "governance PASS -> UNATTESTED, i.e. this attestation not yet existing (the "
    "miso-200 vacuous trap), silent once it is written. (4) THE VALUES MOVED FAR "
    "MORE THAN THE PREREG PREDICTED, and are reported so: PREREG P-5 said gas "
    "classes < 0.3 TWh/yr; measured (arm - control, TWh, 2023/2024/2025): "
    "CT_PEAKER -3.33/-2.32/-3.62, ST_GAS +1.34/+0.68/+0.94, CC_REGULAR "
    "+0.63/+0.48/-0.25, CC_CHP -1.17/-0.56/+0.36, COAL_PRB +0.85/+0.54/+0.70, "
    "COAL_BIT +0.35/+0.00/+0.59; gas classes total -2.43/-1.69/-2.61. The "
    "largest class-year move 3.62 TWh (CT_PEAKER 2025) stays inside the +-8 TWh "
    "band. The Midwest CT fleet lost the increment's discount (Illinois/Indiana/"
    "East -0.26/-0.15/-0.04, West/Plains +0.31/+0.09/-0.64 removed) and the "
    "South fleet its surcharge (+0.14/+0.12/+0.29). C8 ST_GAS forced share "
    "0.155/0.153/0.271 -> 0.138/0.138/0.212 (LESS forcing in every year). (5) "
    "C3a, NEVER the justification (rule 1): +0.79/+0.56/+0.64 pp — 2023 +0.12 -> "
    "+0.91 (AWAY from zero; PREREG predicted -0.05..-0.5: WRONG sign), 2024 "
    "-4.40 -> -3.84 (PREREG predicted negative: WRONG sign), 2025 -12.38 -> "
    "-11.75 (inside the pre-registered +0.2..+1.5). (6) THE OBJECT (2025 real "
    "S->N binding shoulder hours, control from miso-211): South boundary net "
    "+0.05 -> -0.73 GW (measured -2.9; band -0.1..-0.6, overshoot), S->N flow "
    "357 -> 710 MW (inside), free-tier binding share 2.8 -> 6.8 % (inside), "
    "Indiana-South spread -0.16 -> +0.16 $/MWh (band +0.3..+3, short), South gas "
    "15.56 -> 16.33 GW vs 18.9 measured (inside), Midwest gas -1.05 GW (band "
    "-0.2..-0.8, overshoot). Every gate moved in the pre-registered direction; "
    "three overshot the band, one fell short."
)


if __name__ == "__main__":
    if DISCLOSURE.startswith(_PLACEHOLDER):
        raise SystemExit(
            "refusing to write: DISCLOSURE is still the placeholder. Score the "
            "arm first, then replace it with the measured disclosure."
        )
    if not GATES.exists():
        raise SystemExit(f"refusing to write: {GATES} does not exist — score first.")
    build(ARM / "calibration_attestation.json", json.loads(GATES.read_text()))
