"""Write ``calibration_attestation.json`` for the miso-98 sector-measured keeper.

``miso98_chp_sector_B`` is the ``2026-07-25-miso-88-egrid-hr`` keeper recipe
(rebuilt from its ``meta.json``, 208 kwargs) with ONE delta: the ``chp_sector``
column of ``thermal_tranches_MISO.csv`` populated from the measured EIA-860
plant sector. Governance posture and the accepted-limitation ledger are
therefore the keeper's, inherited unchanged — with one deliberate
**subtraction**, below.

The delta REPLACES an unsourced default with a measured source, so it removes a
degree of freedom rather than adding one (rule 24 `[R-DOF]` / rule 21
`[R-REGISTRY]`). The ``free_parameters`` ledger is refreshed from THIS bundle's
``run_config.json`` by ``scripts/build_dof_ledger.py`` (run separately).

Usage:
    python scripts/gen_miso98_attestation.py
    python scripts/build_dof_ledger.py results/calibration/miso98_chp_sector_B
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
KEEPER = REPO / "results/calibration/miso88_egrid_hr/calibration_attestation.json"
ARM = REPO / "results/calibration/miso98_chp_sector_B/calibration_attestation.json"

ATTESTED_BY = (
    "miso-98 CHP sector correction 2026-07-28: the "
    "2026-07-25-miso-88-egrid-hr keeper recipe, rebuilt from its meta.json "
    "(208 solve_and_persist kwargs, zero unmapped -- run_config.json's "
    "calibration_flags is a curated ~35-key subset and would have "
    "mis-specified the run), solved fresh for 2023/2024/2025 as one process "
    "per year into one bundle, with a SINGLE delta: the chp_sector column of "
    "data/raw/_processed-legacy/thermal_tranches_MISO.csv. It is a DATA "
    "correction, not a config flag and not a mechanism. MISO was the only ISO "
    "whose column was empty -- scripts/data/derive_thermal_tranches."
    "_chp_sector_map reads the raw f923_*.zip Page-1 workbooks, those archives "
    "are not committed, so the derive returned {} and the preserve-prior guard "
    "froze the emptiness permanently. data.chp.chp_btm_pct therefore fell "
    "through to CHP_BTM_PCT_BY_SECTOR['merchant'] = 35.0 for every "
    "CC_CHP/CT_CHP plant and CHP_ST_BTM_PCT = 90.0 for every ST_CHP -- the one "
    "value in that table constants.py itself marks 'residual-identified, "
    "forecast-risk' (DOF item S5, issue #1335). The same EIA sector attribute "
    "IS committed, in eia860_plant.parquet ('Sector', identical 1-7 taxonomy). "
    "Equivalence is MEASURED, not assumed: replaying the EIA-860 map onto the "
    "four ISOs whose chp_sector came from EIA-923 agrees on 232/232 plants "
    "(100 %, none absent) and moves their in-LP capacity by EXACTLY 0.0 MW. "
    "Rule 14 [R-ACCURATE] source swap; rule 25 [R-ISO-SCOPE] clean (ISO-generic "
    "channel, MISO-only effect because MISO was the only ISO on the default). "
    "Measured MISO mix: industrial 51.1 % of CHP MW, merchant 44.1 %, "
    "commercial 4.8 %; in-LP capacity 6,474 -> 5,069 MW (-1,405, -21.7 %), i.e. "
    "MISO had been offering ~1.4 GW of host self-supply into the LP as "
    "grid-facing merchant capacity. ZERO free parameters added and one REMOVED "
    "(rule 24 [R-DOF]: 104 artifact rows move off the fitted merchant 35.0 onto "
    "EIA-measured sector classes); no ScenarioConfig field added or altered, no "
    "per-ISO literal, no tuning channel (rule 21 [R-REGISTRY]). Promotion "
    "evidence: the pre-registered A/B against a same-HEAD control arm with the "
    "column reverted to all-NaN (2026-07-27-miso-98a-sectorabsent-control), "
    "results/calibration/FINDING-miso98-chp-sector-ab-2026-07.md."
)

DISCLOSURE = (
    "See metrics.json determination + reasons (NOT-YET, decided by C7 diurnal "
    "shape -- the COAL_PRB issue adjudicated in miso-96, entirely unrelated to "
    "this delta and unchanged by it). PROMOTED ON STRUCTURAL FIDELITY (rule 1 "
    "[R-STRUCT]) AND the gates agree: against the same-HEAD sector-absent "
    "control, C3b price shape flips FAIL -> PASS (NRMSE 0.087/0.137/0.214 -> "
    "0.077/0.121/0.198), C3a mean LMP improves in ALL THREE years (-4.7/-10.1/"
    "-17.5 % -> -2.5/-7.8/-15.4 %, 2024 flipping PASS), C1 fuel-mix PASSes in "
    "both arms, and NO criterion regresses. LEDGER SHRINKS 3/3 -> 2/3: the "
    "C3b-2025 price-shape caveat inherited from miso-81/86/88 is REMOVED, not "
    "re-scoped, because the criterion now passes on its own gate. It passes "
    "MARGINALLY (0.198 against a <=0.20 bound) and that is stated rather than "
    "smoothed -- a future re-solve could put it back over. {C3a-2025, C3c "
    "2023/2024/2025} and the two storage benchmark-basis limitations are "
    "inherited UNCHANGED and NOT widened to absorb anything from this delta. "
    "PRE-REGISTERED AND HONOURED: miso-97 §5.1 predicted CC_CHP would fit "
    "WORSE and it does (+4.9 -> +11.8 % in 2023); under rules 1 [R-STRUCT] / 14 "
    "[R-ACCURATE] the accurate input stays and the worse fit is the "
    "discovered-bug signal. The miss stays well inside the C1 band (+2.52 TWh "
    "of an 8 TWh gate). The pre-registered CT_CHP prediction is REFUTED "
    "(-21.8 -> -33.3 %): miso-97 §2.1's 'rho >= f is structural' bound assumed "
    "capacity and the benchmark subtrahend rescale by the SAME (1 - s), but s "
    "is applied to NAMEPLATE on the capacity side (ratio 0.531) and to NET "
    "GENERATION on the benchmark side (ratio 0.615), and MISO's high-BTM CT_CHP "
    "plants run at lower capacity factor. That refutation is recorded, not "
    "worked around. WHY THIS PROMOTION IS ALSO A CORRECTNESS FIX: the committed "
    "MISO benchmark now holds out the measured host share for every registered "
    "MISO run, so the outgoing keeper -- which solved on the 35.0 % default -- "
    "was being scored against a benchmark its own dispatch never used, "
    "inflating its C1 CC_CHP miss to +7.77 TWh (97 % of the gate) with no "
    "change to its dispatch at all. This keeper puts model and meter back on "
    "one BTM basis. Rule 22 [R-HOLDOUT] honoured: 2023-2025 only, all three "
    "years solved FRESH in one bundle (rule 16 [R-ALLYEARS]), no holdout year "
    "touched, freeze active."
)

# C3b-2025 no longer needs a ledger entry: the criterion PASSES in this run
# (NRMSE 0.198 against the <=0.20 bound) in all three years. Rule 26
# [R-DELETE]: a caveat whose criterion passes is removed, not zeroed or
# re-scoped to keep the slot warm.
_DROP = {("price_shape", 2025)}


def main() -> int:
    att = json.loads(KEEPER.read_text())
    att["governance"] = dict(att.get("governance", {}), attested_by=ATTESTED_BY)
    att["disclosures"] = dict(att.get("disclosures", {}), note=DISCLOSURE)
    before = len(att.get("exceptions", []))
    att["exceptions"] = [
        e
        for e in att.get("exceptions", [])
        if (e.get("criterion"), e.get("year")) not in _DROP
    ]
    ARM.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {ARM.relative_to(REPO)}")
    print(
        f"  exceptions {before} -> {len(att['exceptions'])} (dropped {sorted(_DROP)})"
    )
    print(
        "now run: python scripts/build_dof_ledger.py "
        "results/calibration/miso98_chp_sector_B"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
