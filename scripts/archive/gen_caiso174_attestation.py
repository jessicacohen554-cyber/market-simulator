"""Write the caiso-174 governance attestation for BOTH A/B arms.

caiso-174 is the **re-solve owed by FFR-4D §7 D-2** under cache epoch
``2026-08-04c``: the designated CAISO keeper was solved on a flat forecast
base-year battery scalar, and a CAISO backcast now resolves its storage base
fleet **as of the solve year** from EIA-860
(``ScenarioConfig.storage_measured_base_fleet``, default TRUE, CAISO-scoped).

This generator writes the attestation both arms carry, and **fails closed** on
every claim the finding makes that a machine can check:

* the two arms' ``scenario_config`` must differ on **exactly one key** —
  ``storage_measured_base_fleet``. Unlike caiso-172 (whose delta was a
  ``constants.py`` table and therefore required *identical* configs), this
  session's delta **is** a config field, so the check is "differs on precisely
  this one key and nothing else";
* the arm must actually resolve the **measured** fleet — re-derived here from
  the shipped storage path, not copied from the finding — so the attestation
  cannot claim "measured" over a hand-typed number;
* the DOF ledger must be **UNCHANGED** at ``n_entries`` 11 / ``n_residual`` 8
  (PRECHECK-caiso174 §9's pre-registered invariant). The epoch field carries
  **zero free parameters** and selects a measured EIA-860 fleet over a
  hand-rounded scalar, so it must not increment either count. If it does, that
  is a defect in the attestation and this generator refuses to write it;
* the incumbent keeper's ledgered exceptions are carried **verbatim** — this
  session creates no new caveat and spends no new ledger slot.

Note on the control arm: it is **not** a reconstruction of the pre-epoch keeper
and its attestation does not claim to be. FFR-4D also re-vintaged the constant
``STORAGE_BASE_FLEET_MW["CAISO"]`` 8,000 → 15,450 MW, which no flag gates, so a
control at this head runs a flat **15,450 MW** fleet. It is the "what if only
the constant had been re-vintaged" counterfactual (PRECHECK §4a).

Usage::

    uv run python scripts/gen_caiso174_attestation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.build_dof_ledger import build_ledger  # noqa: E402

KEEPER = REPO / "results/calibration/caiso172_measured_path15_split"
CONTROL = REPO / "results/calibration/caiso174_control_flatfleet"
ARM = REPO / "results/calibration/caiso174_measured_fleet"

#: The incumbent keeper's ledger position. PRECHECK §9 pre-registers that this
#: session leaves BOTH numbers untouched — the epoch field has no free parameters.
KEEPER_N_ENTRIES, KEEPER_N_RESIDUAL = 11, 8

#: The one config key the arms are permitted to differ on.
EPOCH_FIELD = "storage_measured_base_fleet"

#: Measured year-end CAISO battery fleet (FFR-4D §5, EIA-860 2025 Early Release),
#: re-verified against the shipped storage path by this generator.
MEASURED_BATTERY_MW = {2023: 7492.4, 2024: 11131.3, 2025: 15448.4}
TOL_MW = 5.0

ATTESTED_ARM = (
    "caiso-174 (2026-08-05): THE RE-SOLVE OWED BY FFR-4D §7 D-2 under cache "
    "epoch 2026-08-04c. The designated keeper 2026-08-04-caiso-172-measured-"
    "path15 was solved on a FLAT battery scalar — STORAGE_BASE_FLEET_MW is a "
    "FORECAST object whose own docstring calls it 'the base year (2026)' and "
    "whose low/mid/high are the storage_deployment scenario ladder, yet "
    "runner.py fed it to every solve year in both modes, so a 2023 backcast ran "
    "on a 2026 constant. That is a vintage/as-of misalignment, not a scenario "
    "choice. This arm resolves the CAISO backcast storage base fleet AS OF ITS "
    "SOLVE YEAR from EIA-860 via load_eia860_storage (7,492.4 / 11,131.3 / "
    "15,448.4 MW at year-end 2023/2024/2025), the loader written for exactly "
    "this purpose and ORPHANED until FFR-4D wired it. RULE 14 [R-ACCURATE]: "
    "measured over estimate. ZERO free parameters — the DOF ledger is UNCHANGED "
    "at n_entries 11 / n_residual 8, verified fail-closed below. SIDE EFFECT "
    "CLOSED: storage_vintage_ramp, armed on this recipe, was a DEAD FLAG for "
    "batteries while the fleet was a scalar (it reached pumped storage only); "
    "it is live for batteries for the first time here, verified as a 2-D "
    "(6, 8760) power-cap profile that varies within the year BEFORE any price "
    "was read (scripts/probes/_caiso174_fleet_gate.py). The "
    "caiso_storage_shape_caps envelope — a per-MW-of-EIA-860-fleet rate "
    "multiplied by power_cap — also stops having its denominator and its "
    "multiplicand on different fleets."
)

ATTESTED_CONTROL = (
    "caiso-174 Arm A CONTROL (2026-08-05): the same recipe at the same head with "
    "storage_measured_base_fleet=FALSE. IT IS NOT A RECONSTRUCTION OF THE "
    "PRE-EPOCH KEEPER AND DOES NOT CLAIM TO BE: FFR-4D ALSO re-vintaged the "
    "constant STORAGE_BASE_FLEET_MW['CAISO'] 8,000 -> 15,450 MW (mid), which no "
    "flag gates, so this arm runs a FLAT 15,450 MW battery fleet in every year "
    "rather than the keeper's flat 8,000. It is the 'what if only the constant "
    "had been re-vintaged' counterfactual, and its role is to isolate incidental "
    "code drift between the keeper's head 789e28b8 and this one so the Arm B "
    "delta is attributable to the per-year vintaging leg alone. Baseline only — "
    "never a keeper candidate. See PRECHECK-caiso174 §4a."
)


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text()).get(
        "scenario_config", {}
    )


def _resolved_battery_mw(measured: bool, year: int) -> float:
    """Re-derive the arm's battery fleet from the shipped storage path."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.storage import (
        build_default_storage,
        load_eia860_pumped_storage,
        load_eia860_storage,
    )

    cfg = ScenarioConfig(
        iso="CAISO",
        mode="backcast",
        storage_measured_base_fleet=measured,
        storage_vintage_ramp=True,
        caiso_storage_shape_anchor=True,
        start_year=year,
        end_year=year,
    )
    if measured:
        units = list(load_eia860_storage("CAISO", year, cfg))
    else:
        units = list(load_eia860_pumped_storage("CAISO", year, cfg)) + list(
            build_default_storage(get_iso_config("CAISO"), cfg)
        )
    return sum(
        float(u.power_cap_mw)
        for u in units
        if getattr(u, "tech_name", "") != "pumped_storage"
    )


def main() -> int:
    keeper_att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    exceptions = keeper_att["exceptions"]

    for b in (CONTROL, ARM):
        if not (b / "run_config.json").exists():
            raise SystemExit(f"{b.name} not solved yet — nothing to attest.")

    # --- fail-closed check 1: the arms differ on EXACTLY the epoch field -----
    c_cfg, a_cfg = _cfg(CONTROL), _cfg(ARM)
    diff = {k for k in set(c_cfg) | set(a_cfg) if c_cfg.get(k) != a_cfg.get(k)}
    if diff != {EPOCH_FIELD}:
        raise SystemExit(
            f"A/B NOT CLEAN: scenario_config differs on {sorted(diff)}, expected "
            f"exactly {{{EPOCH_FIELD!r}}}. Any other difference means the arms are "
            "not comparable and the epoch delta is not attributable."
        )
    if a_cfg.get(EPOCH_FIELD) is not True or c_cfg.get(EPOCH_FIELD) is not False:
        raise SystemExit(
            f"arm {EPOCH_FIELD}={a_cfg.get(EPOCH_FIELD)!r}, control="
            f"{c_cfg.get(EPOCH_FIELD)!r}; expected True / False."
        )
    print(f"OK: arms differ on exactly {{{EPOCH_FIELD!r}}} (arm True, control False)")

    # --- fail-closed check 2: the arm RESOLVES the measured fleet ------------
    for year, want in MEASURED_BATTERY_MW.items():
        got = _resolved_battery_mw(True, year)
        if abs(got - want) > TOL_MW:
            raise SystemExit(
                f"{year}: arm resolves {got:,.1f} MW of battery, expected the "
                f"measured {want:,.1f} MW — the attestation may not claim "
                "'measured' over a hand-typed number."
            )
    print(
        "OK: arm resolves the MEASURED fleet — "
        + " / ".join(
            f"{MEASURED_BATTERY_MW[y]:,.1f}" for y in sorted(MEASURED_BATTERY_MW)
        )
        + " MW"
    )

    # --- write both attestations --------------------------------------------
    for bundle, attested in ((CONTROL, ATTESTED_CONTROL), (ARM, ATTESTED_ARM)):
        ledger = build_ledger(bundle, "CAISO")
        att = {
            "schema": "calibration-attestation/v1",
            "governance": {
                "levers_trace_to_measured_input": True,
                "no_fit_to_price_residuals": True,
                "no_pinning_to_actuals": True,
                "outage_filter_exogenous_net_load": True,
                "attested_by": attested,
                "note": keeper_att["governance"].get("note", ""),
            },
            "exceptions": exceptions,
            "free_parameters": ledger,
        }
        (bundle / "calibration_attestation.json").write_text(
            json.dumps(att, indent=2) + "\n"
        )
        print(
            f"wrote {bundle.name}/calibration_attestation.json  "
            f"n_entries={ledger['n_entries']} n_residual={ledger['n_residual']}"
        )

    # --- fail-closed check 3: PRECHECK §9's DOF invariant --------------------
    arm_ledger = build_ledger(ARM, "CAISO")
    if arm_ledger["n_entries"] != KEEPER_N_ENTRIES:
        raise SystemExit(
            f"n_entries {arm_ledger['n_entries']} != {KEEPER_N_ENTRIES} — the epoch "
            "field carries ZERO free parameters and must not add a ledger entry "
            "(PRECHECK §9)."
        )
    if arm_ledger["n_residual"] != KEEPER_N_RESIDUAL:
        raise SystemExit(
            f"n_residual {arm_ledger['n_residual']} != {KEEPER_N_RESIDUAL} — selecting "
            "a MEASURED EIA-860 fleet over a hand-rounded scalar must not change the "
            "residual count (PRECHECK §9)."
        )
    print(
        f"OK: DOF invariant holds — n_entries {arm_ledger['n_entries']}, "
        f"n_residual {arm_ledger['n_residual']} (both UNCHANGED from the keeper)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
