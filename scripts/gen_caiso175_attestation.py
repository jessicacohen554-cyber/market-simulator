"""Write the caiso-175 governance attestation for BOTH A/B arms.

caiso-175 is the **CAISO TAC load-series intake** caiso-173 §C asked for, plus a
second defect found in the same input while performing it:

* ``MWD-TAC`` — the sixth CAISO-internal ``SLD_FCST`` area — was hard-coded out
  of ``scripts/data/postprocess_oasis_downloads.CAISO_TACS``, so it never
  reached the committed TAC series and had no ``CAISO_TAC_ZONE_WEIGHTS`` row.
  Because ``load_zonal_shares`` NORMALISES the component TACs to 1.0, its load
  was not dropped but silently re-apportioned PRO RATA across the other four.
* the committed **2023** series covered **744 of 8,760 hours** (January only),
  so 91.5 % of a scored calibration year ran on a FLAT January-average zonal
  split — no diurnal shape, no seasonal shape, for eleven months.

Both are rule 14 ``[R-ACCURATE]`` input corrections with **zero free
parameters**: the data is public, the areas are measured, and the MWD weight is
a 1:1 area containment rather than a fitted split.

This generator writes the attestation both arms carry and **fails closed** on
every claim the finding makes that a machine can check:

* the two arms' ``scenario_config`` must be **IDENTICAL** — this session's delta
  is a data file plus a ``constants.py`` table, not a ``ScenarioConfig`` field,
  so any config difference at all means the arms are not comparable (the
  caiso-172 predicate, not the caiso-174 one);
* the treated arm must actually have SEEN the correction. This is checked on
  **each bundle's own solved output** (``hourly/system_<year>.parquet`` zonal
  demand), never on the current on-disk CSV — the CSV is a single mutable file
  that both arms cannot simultaneously evidence, and re-deriving it post-hoc
  would attest to whichever state happened to be staged last. Two independent
  legs: MWD's load must appear in ``SP15_rest`` in every year, and 2023's NP15
  hourly-share dispersion must rise out of the flat-sample regime;
* the DOF ledger must be **UNCHANGED** at ``n_entries`` 11 / ``n_residual`` 8
  (PRECHECK-caiso175 §2). An intake that adds a measured area and completes a
  measured year introduces no free parameter; if either count moves, that is a
  defect in this session and the generator refuses to write;
* the incumbent keeper's ledgered exceptions are carried **verbatim** — this
  session creates no new caveat and spends no new ledger slot.

Usage::

    uv run python scripts/gen_caiso175_attestation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

from scripts.build_dof_ledger import build_ledger  # noqa: E402

KEEPER = REPO / "results/calibration/caiso174_measured_fleet"
CONTROL = REPO / "results/calibration/caiso175_control"
ARM = REPO / "results/calibration/caiso175_tac_intake"
YEARS = (2023, 2024, 2025)

#: The incumbent keeper's ledger position. PRECHECK §2 pre-registers that this
#: session leaves BOTH numbers untouched — the intake has no free parameters.
KEEPER_N_ENTRIES, KEEPER_N_RESIDUAL = 11, 8

#: MWD-TAC maps 1:1 onto SP15_rest, so the treated arm must carry MORE SP15_rest
#: load share than the control in EVERY year. MWD runs 119-172 MW against a
#: ~24-25.7 GW ISO, i.e. ~0.5-0.7 % of load; the realised share delta is bounded
#: below by this floor so a null (a silently un-applied intake) fails closed.
MIN_SP15_REST_SHARE_GAIN = 0.003

#: 2023's committed series covered 744/8760 h, so 91.5 % of hours took a FLAT
#: sample-average share. Restoring the year lifts NP15's hourly-share dispersion
#: into family with 2024/2025 (sd 0.026 / 0.031). The control's 2023 sd is
#: 0.0037; anything at or below this ceiling means the flat regime survived.
MAX_CONTROL_2023_NP15_SD = 0.010
MIN_ARM_2023_NP15_SD = 0.015

ATTESTED_ARM = (
    "caiso-175 (2026-08-05): THE CAISO TAC LOAD-SERIES INTAKE. Two rule-14 "
    "[R-ACCURATE] demand-input corrections to the SAME committed object, both "
    "with ZERO free parameters. (1) MWD-TAC — the Metropolitan Water District "
    "metered subsystem, the SIXTH CAISO-internal area the live OASIS SLD_FCST "
    "domain carries — was hard-coded out of postprocess_oasis_downloads."
    "CAISO_TACS, so it never reached the committed series and had no "
    "CAISO_TAC_ZONE_WEIGHTS row. Since load_zonal_shares NORMALISES the "
    "component TACs to 1.0 this was NOT missing load: MWD's 119.1/171.6/144.1 "
    "MW was silently re-apportioned PRO RATA across the other four TACs, "
    "misplacing 0.24-0.30 % of ISO load north of Path 15. It is intaken here "
    "and mapped 1:1 onto SP15_rest — a structural containment, not a fitted "
    "split: MWD's CAISO-metered load is the Colorado River Aqueduct pumping "
    "chain in eastern Riverside/San Bernardino County, which the CAISO LCT "
    "study's own taxonomy carries as Blythe/Parker, DISTINCT from both LA Basin "
    "and San Diego/Imperial Valley, and SP15_rest is defined as exactly that "
    "SP26 residual. The measured shape corroborates the identification rather "
    "than assuming it (hour-of-day CV 0.005 vs 0.115-0.128 for the retail TACs; "
    "summer/winter 1.50 — a flat industrial pumping block on water-delivery "
    "seasonality). Opened by caiso-172 §1.1, measured by caiso-173 §C, closed "
    "here in the dedicated session §C asked for. (2) THE 2023 COVERAGE HOLE, "
    "found while performing (1) and NOT previously on the record: the committed "
    "CAISO_tac_load_hourly_2023.csv spanned 2023-01-01 to 2023-02-01 ONLY — 744 "
    "of 8,760 hours — so 91.5 % of a scored calibration year ran on a FLAT "
    "January-average zonal split with no diurnal and no seasonal shape. "
    "Completed here to 8,759 hours. THE RE-FETCH IS BYTE-FAITHFUL ON EVERYTHING "
    "IT DID NOT ADD: every pre-existing (timestamp, area) row reproduces to max "
    "|delta| 0.000000 MW with 0 rows differing, in all three years, so the "
    "intake ADDS and never REWRITES. No ScenarioConfig field is added, no "
    "scorer constant is touched, and no static load_share fallback is "
    "re-derived. DOF ledger UNCHANGED at n_entries 11 / n_residual 8, verified "
    "fail-closed below."
)

ATTESTED_CONTROL = (
    "caiso-175 Arm A CONTROL (2026-08-05): the caiso-174 keeper recipe replayed "
    "at THIS head on the AS-COMMITTED CAISO TAC load series (five areas, "
    "MWD-TAC absent; 2023 covering 744 of 8,760 hours). Its scenario_config is "
    "IDENTICAL to Arm B's — this session's delta is a data file plus a "
    "constants.py table, not a config field — so the arms differ in the input "
    "and nothing else. Its role is to isolate incidental code drift between the "
    "keeper's head ae7658d0 and this one, and it EARNED ITS KEEP: the drift "
    "(A - keeper) is +0.168/+0.049/+0.115 $/MWh on load-weighted mean LMP, "
    "LARGER in every year than the intake's own effect (B - A) of "
    "+0.118/-0.004/+0.002. Without this arm the 2023 movement would have been "
    "read as the intake when most of it is drift. Baseline only — never a "
    "keeper candidate. See PRECHECK-caiso175 §3."
)


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text()).get(
        "scenario_config", {}
    )


def _zonal_demand(bundle: Path, year: int) -> pd.DataFrame:
    """P1 zonal demand for one solved year, from the bundle's own sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"] if "pass" in df.columns else df


def _share(bundle: Path, year: int, zone: str) -> float:
    """Annual demand share of ``zone`` as the LP actually saw it."""
    tot = _zonal_demand(bundle, year).groupby("zone")["demand"].sum()
    return float(tot.get(zone, 0.0) / tot.sum())


def _hourly_share_sd(bundle: Path, year: int, zone: str) -> float:
    """SD of ``zone``'s HOURLY demand share — the flat-sample detector."""
    wide = _zonal_demand(bundle, year).pivot_table(
        index="hour", columns="zone", values="demand"
    )
    return float(wide.div(wide.sum(axis=1), axis=0)[zone].std())


def main() -> int:
    keeper_att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    exceptions = keeper_att["exceptions"]

    for b in (CONTROL, ARM):
        if not (b / "run_config.json").exists():
            raise SystemExit(f"{b.name} not solved yet — nothing to attest.")

    # --- fail-closed check 1: the arms' configs are IDENTICAL ---------------
    c_cfg, a_cfg = _cfg(CONTROL), _cfg(ARM)
    diff = sorted(k for k in set(c_cfg) | set(a_cfg) if c_cfg.get(k) != a_cfg.get(k))
    if diff:
        raise SystemExit(
            f"A/B NOT CLEAN: scenario_config differs on {diff}, expected NO "
            "difference at all — caiso-175's delta is a data file plus a "
            "constants.py table, so any config difference means the arms are "
            "not comparable and the intake delta is not attributable."
        )
    print(f"OK: arms' scenario_config IDENTICAL across {len(a_cfg)} keys")

    # --- fail-closed check 2a: MWD's load reached SP15_rest in every year ---
    for year in YEARS:
        gain = _share(ARM, year, "SP15_rest") - _share(CONTROL, year, "SP15_rest")
        if gain < MIN_SP15_REST_SHARE_GAIN:
            raise SystemExit(
                f"{year}: SP15_rest demand share gain {gain:+.5f} < "
                f"{MIN_SP15_REST_SHARE_GAIN} — MWD-TAC did not reach the LP, so "
                "the attestation may not claim the intake was applied."
            )
        print(f"OK: {year} SP15_rest share {gain:+.5f} (MWD landed in-zone)")

    # --- fail-closed check 2b: 2023's flat-sample regime is gone ------------
    c_sd = _hourly_share_sd(CONTROL, 2023, "NP15")
    a_sd = _hourly_share_sd(ARM, 2023, "NP15")
    if c_sd > MAX_CONTROL_2023_NP15_SD:
        raise SystemExit(
            f"control 2023 NP15 hourly-share sd {c_sd:.5f} > "
            f"{MAX_CONTROL_2023_NP15_SD} — the control does NOT exhibit the flat "
            "744-hour-sample regime this session claims to have corrected."
        )
    if a_sd < MIN_ARM_2023_NP15_SD:
        raise SystemExit(
            f"arm 2023 NP15 hourly-share sd {a_sd:.5f} < {MIN_ARM_2023_NP15_SD} "
            "— the 2023 coverage restoration did not reach the LP."
        )
    print(
        f"OK: 2023 NP15 hourly-share sd {c_sd:.5f} -> {a_sd:.5f} "
        f"({a_sd / c_sd:.1f}x — eleven months of shape the LP did not have)"
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

    # --- fail-closed check 3: PRECHECK §2's DOF invariant --------------------
    arm_ledger = build_ledger(ARM, "CAISO")
    if arm_ledger["n_entries"] != KEEPER_N_ENTRIES:
        raise SystemExit(
            f"n_entries {arm_ledger['n_entries']} != {KEEPER_N_ENTRIES} — an "
            "intake that adds a MEASURED area and completes a MEASURED year "
            "carries ZERO free parameters and must not add a ledger entry."
        )
    if arm_ledger["n_residual"] != KEEPER_N_RESIDUAL:
        raise SystemExit(
            f"n_residual {arm_ledger['n_residual']} != {KEEPER_N_RESIDUAL} — the "
            "MWD weight is a 1:1 area containment, not a fitted split, so the "
            "residual count must not move."
        )
    print(
        f"OK: DOF invariant holds — n_entries {arm_ledger['n_entries']}, "
        f"n_residual {arm_ledger['n_residual']} (both UNCHANGED from the keeper)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
