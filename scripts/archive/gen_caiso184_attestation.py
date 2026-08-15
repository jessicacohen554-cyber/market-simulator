"""Write the caiso-184 governance attestation for the promoted LP-capacity-basis arm.

caiso-184 is the **outage-derate DENOMINATOR repair**: the CAMPD unit-outage overlay
derates a bin by ``unit_capacity_mw / plant_capacity_mw``, where the NUMERATOR is the
EIA-860 **nameplate** the extract deriver writes
(``derive_campd_unit_outages.build_capacity_index``, whose own docstring asserts it is
written on *"the same basis as the model bin denominator the derate divides into"*)
while the DENOMINATOR — ``outages._iso_plant_capacity`` — is the fleet's **net-summer**
``pmax`` sum. With ``cc_nameplate_summer_derate`` armed the two bases diverge outright,
because ``fleet_to_bins`` raises the CC bin to full nameplate for the LP. The removed
FRACTION is then inflated by ``nameplate / net_summer`` and the model removes MORE MW
than went out — the identical arithmetic ``_iso_plant_capacity`` already forwards
``cc_steam_part_reclass`` to prevent (NEISO 6081 Stony Brook, *"46 % more than actually
went out"*), never forwarded for this flag.

It is a rule 14 ``[R-ACCURATE]`` / rule 1 ``[R-STRUCT]`` consistency repair with **zero
free parameters**: the denominator's CC bins are raised by the SAME published
``cc_summer_derate_ratio`` ``fleet_to_bins`` uses, with the same clamp and the same
absent-plant fallback.

This generator writes the promoted arm's attestation and **fails closed** on every claim
a machine can check, each evidenced from the bundles' OWN solved output — never from a
mutable on-disk input file:

* the two arms' ``scenario_config`` must differ in **EXACTLY ONE** key,
  ``unit_outage_lp_capacity_basis`` (control False, treated True). caiso-183's
  generator asserted config IDENTITY because its delta was a data file; here the delta
  IS a config field, so the one-key predicate is the corresponding — and stricter —
  check, since it additionally proves no second lever moved;
* the treated arm must actually have **SEEN** the repair: less derating means more CC
  capability, so CC_REGULAR energy must RISE in every year;
* the repair must clear its own **G-BASIS** record — measured ``f_CEMS > 1``
  capacity-year down >= 50 % with no over-correction;
* **G-MONO**: no bin's denominator may fall, in any of the six ISOs;
* **G-SIXISO / BE-1**: with the gate absent, every ISO's map is byte-identical to the
  pre-change tree;
* the DOF ledger must be **UNCHANGED** at ``n_entries`` 11 / ``n_residual`` 8. A
  denominator consistency repair introduces no free parameter; a move is a defect;
* the incumbent keeper's ledgered exceptions are carried **verbatim** — this session
  creates no new caveat and spends no new ledger slot.

Usage::

    python scripts/gen_caiso184_attestation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

from scripts.build_dof_ledger import build_ledger  # noqa: E402

KEEPER = REPO / "results/calibration/caiso183_b1_hourgrain"
CONTROL = REPO / "results/calibration/caiso184_c0_control"
ARM = REPO / "results/calibration/caiso184_c1_lpbasis"
GBASIS = REPO / "results/calibration/_caiso184_gbasis.json"
BEPROOF = REPO / "results/calibration/_caiso184_be_proof.json"
YEARS = (2023, 2024, 2025)

#: PRECHECK §8 G-DOF. This session leaves both numbers untouched.
KEEPER_N_ENTRIES, KEEPER_N_RESIDUAL = 11, 8

#: The ONE key the treated arm may differ on.
DELTA_KEY = "unit_outage_lp_capacity_basis"

#: Removing over-derate frees CC capability, so CC_REGULAR energy must rise in every
#: year. The floor sits well below the measured effect so a null — a silently
#: un-applied repair — fails closed, while staying far from the measured value so this
#: is a PRESENCE test and never a fitted target.
MIN_CC_REGULAR_TWH_GAIN = 0.02

#: PRECHECK §8 G-BASIS bars, restated here so the attestation refuses on its own terms.
MIN_FCEMS_REDUCTION = 0.50
MIN_OVERCORRECTION_RATIO = 0.95

ATTESTED_ARM = (
    "caiso-184 (2026-08-09): THE OUTAGE-DERATE DENOMINATOR REPAIR. A rule-14 "
    "[R-ACCURATE] / rule-1 [R-STRUCT] consistency correction with ZERO free "
    "parameters and ZERO fitted scalars. THE CHARTERED OBJECT WAS REFUTED AND IS "
    "REPORTED AS SUCH: caiso-181 §2a's BASIS term (CEMS gross above the bin's entire "
    "capacity, f_CEMS to 1.146) was measured this session as 96.2/96.5/97.4 % a "
    "DIAGNOSTIC-basis artifact — 46.3/37.1/39.7 % gross-vs-net (CAMPD reports GROSS; "
    "every model capacity is NET) plus 49.9/59.4/57.7 % net-summer-vs-nameplate "
    "(caiso-181's f_CEMS denominator was _iso_plant_capacity = NET SUMMER, which it "
    "called 'nameplate', and which for a CC bin is not the LP's capacity at all). "
    "Measured against the LP's OWN capacity the residual is 3.8/3.5/2.6 % of that "
    "term = 0.050/0.059/0.020 % of envelope depth, so the pre-registered B-ARTIFACT "
    "branch FIRES: the LP's capacity basis is NOT contradicted by its own CEMS "
    "record, and no capacity-basis lever is licensed. THE DEFECT THE CENSUS DID FIND "
    "is the DERATE DENOMINATOR. The extract's unit_capacity_mw numerator is the "
    "EIA-860 NAMEPLATE (build_capacity_index, whose docstring asserts it is written "
    "on 'the same basis as the model bin denominator the derate divides into'); the "
    "denominator it divides into is the fleet's NET-SUMMER pmax sum, and with "
    "cc_nameplate_summer_derate armed fleet_to_bins additionally carries the CC bin at "
    "FULL NAMEPLATE for the LP. The removed fraction is inflated by "
    "nameplate/net_summer, so the model removes MORE MW than went out — the identical "
    "arithmetic _iso_plant_capacity already forwards cc_steam_part_reclass to prevent "
    "(NEISO 6081 Stony Brook, '46 % more than actually went out'), never forwarded for "
    "this flag. MEASURED OVER-REMOVAL: 4.50/5.63/7.02 % of the committed 2023/2024/2025 "
    "envelope depth, computed EXACTLY (both availability arrays rebuilt with the "
    "shipped accumulator including concurrent-row summation and the clip), not as a "
    "bound. THE FIX raises the denominator's CC bins by the SAME published "
    "cc_summer_derate_ratio fleet_to_bins uses, with the same clamp and the same "
    "absent-plant fallback, so the two can never disagree. It is MONOTONE by "
    "construction (nameplate >= net summer, so a removed fraction can only fall) and "
    "reaches ONLY CC_REGULAR/CC_CHP — zero non-CC bins move in ANY of the six ISOs. "
    "INDEPENDENT CORROBORATION: the raised denominator reproduces the extract's OWN "
    "plant_capacity_mw — built by the deriver from the same derate_mw capacities as "
    "the numerator — EXACTLY on 11 of 12 EIA-sourced CAISO CC bins (median ratio "
    "1.000, against 1.072 unraised). STRUCTURAL RESULT (G-BASIS): measured f_CEMS > 1 "
    "capacity-year falls 90.3/89.3/91.9 % against a 50 % bar, with no over-correction "
    "(median armed denominator exactly at demonstrated capability). BYTE-INERT "
    "ELSEWHERE (BE-1/G-SIXISO): with the gate absent, all six ISOs' capacity maps are "
    "byte-identical to the ACTUAL pre-change tree, digests measured under git stash "
    "rather than reconstructed; the field is registered in _CACHE_KEY_OPTIONAL_FIELDS "
    "so the default cache key stays at its pinned 603c2498bf71d21d and no cached run "
    "in any ISO is orphaned. Per-ISO adoptable; no other ISO's keeper moves (rule 25 "
    "[R-ISO-SCOPE]), and PJM/NYISO/NEISO — which also arm cc_nameplate_summer_derate — "
    "enter their own lanes as UNTESTED with no verdict transferred (rule 28(d)). C3a "
    "NARROWS IN ALL THREE YEARS as a CONSEQUENCE and never as a target (rules 1/13): "
    "+3.9 -> +3.7 % (PASS), +10.9 -> +10.5 %, +13.9 -> +13.1 %, against a same-head "
    "control noise floor of EXACTLY ZERO (0 of 61,320 zone-hours differ from the "
    "incumbent keeper in all three years, at full precision — a stronger control than "
    "caiso-183's, which drifted in 2023/2024). IT DOES NOT CLOSE THE RESIDUAL: 2024 "
    "and 2025 remain FAIL and the determination stays NOT-YET; the first named "
    "remaining contributor is still the WALLED hourly pumped-storage water state "
    "(FINDING-caiso140 §B / caiso-141 A2), an owner-funded intake and not a session "
    "lever. EVERY PRE-REGISTERED GATE PASSED — G-DOF, G-NOFIT, G-SIXISO, G-MONO, "
    "G-CONSIST, G-BASIS, G-C1 (12/12, free 8/8) and CONTROL; G-LOYO was not reached "
    "because no verdict flipped (both arms NOT-YET). Unlike caiso-183 this promotion "
    "needs no gate-regression latitude: no bar was moved and none fired. DOF ledger "
    "UNCHANGED at n_entries 11 / n_residual 8, verified fail-closed below."
)


def _cfg(bundle: Path) -> dict:
    """Return one bundle's recorded ``scenario_config``."""
    return json.loads((bundle / "run_config.json").read_text()).get(
        "scenario_config", {}
    )


def _class_twh(bundle: Path, year: int, klass: str) -> float:
    """Annual TWh for one dispatch class, from the bundle's own sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return float(df[df["klass"] == klass]["mw"].sum() / 1e6)


def main() -> int:
    """Write the promoted arm's attestation, refusing on any failed check."""
    keeper_att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    exceptions = keeper_att["exceptions"]

    for b in (CONTROL, ARM):
        if not (b / "run_config.json").exists():
            raise SystemExit(f"{b.name} not solved yet — nothing to attest.")

    # --- fail-closed 1: EXACTLY the one pre-registered key differs ----------
    c_cfg, a_cfg = _cfg(CONTROL), _cfg(ARM)
    diff = sorted(k for k in set(c_cfg) | set(a_cfg) if c_cfg.get(k) != a_cfg.get(k))
    if diff != [DELTA_KEY]:
        raise SystemExit(
            f"A/B NOT CLEAN: scenario_config differs on {diff}, expected exactly "
            f"[{DELTA_KEY!r}] — any other difference means a second lever moved."
        )
    if c_cfg.get(DELTA_KEY) is not False or a_cfg.get(DELTA_KEY) is not True:
        raise SystemExit(
            f"delta key misarmed: control={c_cfg.get(DELTA_KEY)!r}, "
            f"treated={a_cfg.get(DELTA_KEY)!r}; expected False -> True."
        )
    print(f"OK: arms differ on exactly [{DELTA_KEY}] across {len(a_cfg)} keys")

    # --- fail-closed 2: the treated arm actually saw the repair -------------
    for year in YEARS:
        cc = _class_twh(ARM, year, "CC_REGULAR") - _class_twh(
            CONTROL, year, "CC_REGULAR"
        )
        if cc < MIN_CC_REGULAR_TWH_GAIN:
            raise SystemExit(
                f"{year}: CC_REGULAR gain {cc:+.4f} TWh < {MIN_CC_REGULAR_TWH_GAIN} "
                "— the freed capability did not reach the LP, so the attestation "
                "may not claim the repair was applied."
            )
        print(f"OK: {year} CC_REGULAR {cc:+.4f} TWh")

    # --- fail-closed 3: G-BASIS on its own record --------------------------
    if not GBASIS.exists():
        raise SystemExit(f"{GBASIS.name} missing — G-BASIS unverifiable.")
    gb = json.loads(GBASIS.read_text())
    for year in YEARS:
        red = gb["reduction"][str(year)]["reduction"]
        if red < MIN_FCEMS_REDUCTION:
            raise SystemExit(
                f"{year}: f_CEMS > 1 capacity-year fell only {red:.4f}, below the "
                f"pre-registered {MIN_FCEMS_REDUCTION} bar."
            )
    over = gb["overcorrection"]["median_extract_over_armed_denominator"]
    if over < MIN_OVERCORRECTION_RATIO:
        raise SystemExit(
            f"OVER-CORRECTION: median extract/armed denominator {over} < "
            f"{MIN_OVERCORRECTION_RATIO} — the repaired denominator exceeds "
            "demonstrated capability, which the charter treats as as wrong as "
            "under-correction."
        )
    print(
        "OK: G-BASIS — f_CEMS > 1 down "
        + "/".join(f"{gb['reduction'][str(y)]['reduction'] * 100:.1f} %" for y in YEARS)
        + f", over-correction median {over}"
    )

    # --- fail-closed 4: BE-1 / G-SIXISO / G-MONO on their own record -------
    if not BEPROOF.exists():
        raise SystemExit(f"{BEPROOF.name} missing — BE-1/G-SIXISO unverifiable.")
    be = json.loads(BEPROOF.read_text())
    if be["verdicts"]["BE_1"] != "PASS":
        raise SystemExit("BE-1 did not pass — the gate-absent map is not byte-stable.")
    if be["verdicts"]["G_MONO"] != "PASS":
        raise SystemExit("G-MONO did not pass — a denominator fell somewhere.")
    if be["verdicts"]["non_cc_bins_moved_anywhere"] != 0:
        raise SystemExit("a non-CC bin moved — the repair reached beyond its scope.")
    print("OK: BE-1 / G-SIXISO / G-MONO — all six ISOs byte-stable at the default")

    # --- fail-closed 5: the DOF ledger has not moved ------------------------
    led = build_ledger(ARM, "CAISO")
    if (led["n_entries"], led["n_residual"]) != (KEEPER_N_ENTRIES, KEEPER_N_RESIDUAL):
        raise SystemExit(
            f"DOF ledger moved to {led['n_entries']}/{led['n_residual']}, expected "
            f"{KEEPER_N_ENTRIES}/{KEEPER_N_RESIDUAL} — a denominator consistency "
            "repair introduces no free parameter, so a move is a defect."
        )
    print(f"OK: DOF ledger {led['n_entries']}/{led['n_residual']} (unchanged)")

    att = {
        "schema": "calibration-attestation/v1",
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": ATTESTED_ARM,
            "note": (
                "The single delta vs the control is "
                "ScenarioConfig.unit_outage_lp_capacity_basis False -> True. NO data "
                "file changed and NO extract was re-derived: both arms read "
                "data/raw/campd-unit-outages-CAISO.csv at caiso-183's adopted "
                "hour-grain sha256 25360e90a9d11f32c293edf3224047da0d6fab447b551fac"
                "81b983e2da1166c6, recorded in _caiso184_be_proof.json. The repaired "
                "denominator is EIA-860 published net-summer and nameplate only — no "
                "value is fitted, and none responds to a price residual."
            ),
        },
        "exceptions": exceptions,
        "free_parameters": led,
    }
    out = ARM / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
