"""Seed/refresh the DOF (free-parameter) ledger in a keeper's attestation.

CLAUDE.md rule 20 / audit §7 D-12: every keeper's
``calibration_attestation.json`` carries a ``free_parameters`` section listing
each tuned scalar (or tuned-scalar family) active in the run config, its
**identification source** — ``published`` | ``measured-physical`` |
``residual`` — and its lineage solve count. A ``residual``-sourced parameter
must carry an open ``root_cause`` reference (audit_keepers E8 fails a keeper
otherwise): a residual that can only be closed by a tuned value is an open
root-cause issue, not a parameter.

Entries come from two places:

* **Config-derived** (computed from the bundle's ``run_config.json``): the
  per-group offer-curve multiplier dict (scalar count computed), the offer
  smoothing shape, the wefor pair, the battery/PS dispatch adders, and the
  engaged coal passthrough sigmoids.
* **Curated per-ISO constants** (the audit §3 class-C table and the W1d
  "residual-identified, forecast-risk" markers in ``constants.py`` /
  ``fleet.py``), keyed on the config flags that engage them.

The script is idempotent: it replaces the ``free_parameters`` section and
touches nothing else in the attestation. Identification taxonomy:

* ``published`` — read from a published market/physical source.
* ``measured-physical`` — derived from measured physical/behaviour data by a
  frozen derive script (rule 23); admissible under rule #13.
* ``residual`` — chosen (wholly or finally) because it moved a backcast
  residual. Sanctioned only inside the rule-#1 offer-curve scope, and ALWAYS
  an open root-cause item.

Usage::

    python scripts/build_dof_ledger.py results/calibration/<bundle> [--check]
    python scripts/build_dof_ledger.py --all-keepers
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Lineage solve counts per ISO (audit §5.1 census, floor values; the registry
# top-15 retention hides most of the search, so these are ">=" counts).
LINEAGE = {
    "ERCOT": ">=165 solves (audit §5.1)",
    "PJM": ">=76 solves (audit §5.1 + pjm-76)",
    "MISO": ">=39 solves (audit §5.1 + miso-39)",
    "NYISO": ">=41 solves (audit §5.1 + nyiso-41)",
    "NEISO": ">=43 solves (audit §5.1)",
    "CAISO": ">=52 solves (audit §5.1 + caiso-51/52)",
}

_HOLDOUT_ROOT_CAUSE = (
    "identified in-sample only (2023-2025); no held-out validation exists — "
    "open: the one-shot D-6 holdout score (CLAUDE.md rule 22) and the D-7 "
    "statistical-mode gap reported on the Calibration Status page"
)

# Root-cause GitHub issues opened during the 2026-07 scalar-remediation B-GOV-1
# ledger sweep (docs/handoffs/scalar-remediation-prompts-2026-07.md) — every
# residual entry these constants are attached to MUST keep citing an open
# issue (audit_keepers E8).
_ISSUE_C4_MERCHANT_CHP = (
    "https://github.com/jessicacohen554-cyber/market-simulator/issues/1335"
)
_ISSUE_C8_CORE_STEPS = (
    "https://github.com/jessicacohen554-cyber/market-simulator/issues/1336"
)
_ISSUE_COMMITTED_BELOW_085 = (
    "https://github.com/jessicacohen554-cyber/market-simulator/issues/1302"
)
# Root-cause issues opened during the 2026-07 scalar-remediation B-NYI-1 batch
# (NYISO de-leak C-13 + LI floor C-17). Same E8 contract: the residual entries
# these are attached to keep citing an open issue.
_ISSUE_NYISO_C3A_CC_DELEAK = (
    "https://github.com/jessicacohen554-cyber/market-simulator/issues/1344"
)
_ISSUE_NYISO_LI_LCR_MISMATCH = (
    "https://github.com/jessicacohen554-cyber/market-simulator/issues/1345"
)
_ISSUE_C18_GAS_AVAILABILITY_DEAD_CODE = (
    "https://github.com/jessicacohen554-cyber/market-simulator/issues/1349"
)
# Root-cause issues opened during the 2026-07 scalar-remediation B-CAI-1 batch
# (CAISO C-16 PGE-TAC Path-15 split; C-5/C-14 WECC seam forecast-path fallbacks).
_ISSUE_C16_PGE_TAC_SPLIT = (
    "https://github.com/jessicacohen554-cyber/market-simulator/issues/1372"
)
_ISSUE_C5_C14_SEAM_FALLBACKS = (
    "https://github.com/jessicacohen554-cyber/market-simulator/issues/1373"
)

# scalar-remediation B-XISO-1 (audit C-18, 2026-07-05): NERC's public GADS
# Generating Unit Statistical Brochure 3 (2019-2023) is NERC-wide, with no
# per-ISO/region EFORd breakdown — see
# data/raw/reference/nerc-gads-eford-2019-2023/. "FOSSIL Gas Primary, All
# Sizes" (EFORd=13.44%, availability 1-0.1344=0.8656) is the closest published
# match to this constant's single "gas-fired generation availability" concept
# and now applies uniformly to every ISO (constants.py GAS_AVAILABILITY_FACTOR).
_GAS_AF_SOURCE = (
    "NERC GADS Generating Unit Statistical Brochure 3, 2019-2023 "
    "(NERC-wide — no per-ISO breakdown exists), 'FOSSIL Gas Primary, All "
    "Sizes', EFORd=13.44%"
)

# Committed-tranche multiplier floor (audit §2 flag; plan §2.1 exception): a
# group whose committed HR multiplier sits below this without a written
# physical rationale in ``offer_curve_by_group`` is pulled out of the R6 bulk
# population and gets its own ledger row citing the open issue.
_COMMITTED_MULT_FLOOR = 0.85


def _count_scalars(obj) -> int:
    """Count numeric leaves in a nested dict/list (tuned-scalar census)."""
    if isinstance(obj, bool):
        return 0
    if isinstance(obj, (int, float)):
        return 1
    if isinstance(obj, dict):
        return sum(_count_scalars(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return sum(_count_scalars(v) for v in obj)
    return 0


def _entry(
    name,
    where,
    identification,
    iso,
    *,
    value=None,
    n_scalars=None,
    source="",
    root_cause="",
):
    """Build one ledger entry; residual entries must carry a root cause."""
    e = {
        "name": name,
        "where": where,
        "identification": identification,
        "lineage_solves": LINEAGE.get(iso, "unknown"),
    }
    if value is not None:
        e["value"] = value
    if n_scalars is not None:
        e["n_scalars"] = n_scalars
    if source:
        e["source"] = source
    if identification == "residual":
        if not root_cause:
            raise ValueError(f"residual entry {name!r} needs a root_cause")
        e["root_cause"] = root_cause
    elif root_cause:
        e["note"] = root_cause
    return e


def config_entries(sc: dict, iso: str) -> list[dict]:
    """Ledger entries computed from the bundle's scenario_config."""
    out = []
    curves = sc.get("offer_curve_by_group") or {}
    if curves:
        out.append(
            _entry(
                "offer_curve_by_group",
                "run_config.scenario_config.offer_curve_by_group",
                "residual",
                iso,
                n_scalars=_count_scalars(curves),
                value={g: sorted(v) for g, v in curves.items()},
                source="per-group HR-band multipliers — the rule-#1-sanctioned "
                "offer-curve tuning surface (audit C-8/C-11/C-13)",
                root_cause=_HOLDOUT_ROOT_CAUSE
                + (
                    " · NYISO B-NYI-1/C-13: CC_REGULAR econ_high de-leaked "
                    "1.21 -> 1.0 (ERCOT cross-borrowed markup removed); the "
                    "exposed C3a hole is missing NYISO reserve/scarcity price "
                    "formation, not a CC markup — open: " + _ISSUE_NYISO_C3A_CC_DELEAK
                    if iso == "NYISO"
                    else ""
                ),
            )
        )
        below_floor = {
            g: b["committed"]
            for g, b in curves.items()
            if b.get("committed") is not None and b["committed"] < _COMMITTED_MULT_FLOOR
        }
        if below_floor:
            out.append(
                _entry(
                    f"offer_curve_committed_below_floor[{iso}]",
                    "run_config.scenario_config.offer_curve_by_group[*].committed",
                    "residual",
                    iso,
                    value=below_floor,
                    n_scalars=len(below_floor),
                    source="committed-tranche multiplier(s) below the audit §2 "
                    "0.85 physical-floor flag with no written rationale in the "
                    "config — pulled out of the R6 bulk offer-curve population "
                    "per plan §2.1 (docs/handoffs/scalar-remediation-plan-"
                    "2026-07.md)",
                    root_cause="open: "
                    + _ISSUE_COMMITTED_BELOW_085
                    + " (per-ISO evening-merit-style diagnosis before any "
                    "value is touched — rules #1/#18/#19/#26 apply, no "
                    "blanket fix)",
                )
            )
    smoothing = {
        k: sc[k]
        for k in (
            "offer_curve_smoothing_n",
            "offer_curve_smoothing_mid",
            "offer_curve_smoothing_exp",
        )
        if sc.get(k) is not None
    }
    if smoothing:
        out.append(
            _entry(
                "offer_curve_smoothing",
                "run_config.scenario_config.offer_curve_smoothing_*",
                "residual",
                iso,
                value=smoothing,
                n_scalars=_count_scalars(smoothing),
                source="econ-ramp shape of the offer curve (rule-#1 scope)",
                root_cause=_HOLDOUT_ROOT_CAUSE,
            )
        )
    sigmoids = [
        k
        for k in (
            "coal_prb_passthrough_sigmoid",
            "coal_lignite_passthrough_sigmoid",
            "coal_bit_passthrough_sigmoid",
            "coal_sub_passthrough_sigmoid",
            "coal_wc_passthrough_sigmoid",
        )
        if sc.get(k)
    ]
    if sigmoids:
        out.append(
            _entry(
                "COAL_SIGMOID_DEFAULTS[" + iso + "]",
                "scenarios.py COAL_SIGMOID_DEFAULTS (engaged via "
                + ", ".join(sigmoids)
                + ")",
                "residual",
                iso,
                n_scalars=4 * len(sigmoids),
                source="gas-keyed coal passthrough sigmoids — the largest fitted "
                "surface (audit C-1); owner-sanctioned under rule #1",
                root_cause="weakly identified: each asymptote is pinned by a "
                "single gas regime (floor by 2024, gas_mid/ceil by 2025 — "
                "docs/out-of-sample-results-2026-07.md §2C); open: literature/"
                "physical anchoring of floor/ceil, plus " + _HOLDOUT_ROOT_CAUSE,
            )
        )
    if sc.get("wefor_multiplier") not in (None, 1.0):
        out.append(
            _entry(
                "wefor_multiplier",
                "run_config.scenario_config.wefor_multiplier",
                "residual",
                iso,
                value=sc["wefor_multiplier"],
                source="wind EFOR haircut (audit C-15) — the name admits "
                "residual identification; stated purpose is coal shoulder-month "
                "generation",
                root_cause="audit C-15 open item: replace with a measured wind "
                "availability/curtailment input or delete; " + _HOLDOUT_ROOT_CAUSE,
            )
        )
    if sc.get("wefor_residual"):
        out.append(
            _entry(
                "wefor_residual",
                "run_config.scenario_config.wefor_residual"
                + (
                    f" (groups {sc.get('wefor_residual_groups')})"
                    if sc.get("wefor_residual_groups")
                    else ""
                ),
                "residual",
                iso,
                value=sc["wefor_residual"],
                source="wind-EFOR residual relief term (audit C-15) — "
                "residual-identified by name",
                root_cause="audit C-15 open item; statistical mode turns this "
                "off and the fit degrades (docs/statistical-mode-results-"
                "2026-07.md); " + _HOLDOUT_ROOT_CAUSE,
            )
        )
    if sc.get("battery_dispatch_adder"):
        out.append(
            _entry(
                "battery_dispatch_adder",
                "run_config.scenario_config.battery_dispatch_adder",
                "residual",
                iso,
                value=sc["battery_dispatch_adder"],
                source="grid-battery throughput/cycling adder $/MWh — inside the "
                "literature range (NREL ATB 2024 cycle-life ~$15-25/MWh; Xu et "
                "al. 2018 $25-50/MWh) but the specific value is calibrated",
                root_cause="reduced-form stand-in for cycling degradation + AS "
                "opportunity cost; forward-valid replacement is the measured AS "
                "power reservation (storage_as_commitment) + an ATB-derived "
                "degradation cost — open item to re-derive from those",
            )
        )
    if sc.get("pumped_storage_dispatch_adder"):
        out.append(
            _entry(
                "pumped_storage_dispatch_adder",
                "run_config.scenario_config.pumped_storage_dispatch_adder",
                "residual",
                iso,
                value=sc["pumped_storage_dispatch_adder"],
                source="PS throughput adder (the retired PJM $10 pattern)",
                root_cause="retired-knob pattern: replace with a measured "
                "reserve power reservation (see constants.py "
                "PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO retirement note)",
            )
        )
    return out


def curated_entries(sc: dict, iso: str) -> list[dict]:
    """Audit §3 C-table / W1d-marker entries, keyed on engaging flags."""
    out = []
    gas_af = {
        # scalar-remediation B-XISO-1 (audit C-18, 2026-07-05): re-verified
        # against the actual NERC GADS Generating Unit Statistical Brochure 3
        # (2019-2023, "Units Reporting Events") — see
        # data/raw/reference/nerc-gads-eford-2019-2023/. The brochure is
        # NERC-wide (no ISO/region breakdown exists in NERC's public GADS
        # product), so the same verified value ("FOSSIL Gas Primary, All
        # Sizes", EFORd=13.44% -> availability 0.8656) applies to every ISO;
        # the old per-ISO nudge-trail/TODO values are gone (rule 26). All
        # five are now genuinely "published" — no residual/nudge component
        # remains.
        "ERCOT": ("published", 0.866, _GAS_AF_SOURCE),
        "CAISO": ("published", 0.866, _GAS_AF_SOURCE),
        "PJM": ("published", 0.866, _GAS_AF_SOURCE),
        "NYISO": ("published", 0.866, _GAS_AF_SOURCE),
        "NEISO": ("published", 0.866, _GAS_AF_SOURCE),
    }
    if iso in gas_af:
        ident, val, src = gas_af[iso]
        out.append(
            _entry(
                f"GAS_AVAILABILITY_FACTOR[{iso}]",
                "constants.py GAS_AVAILABILITY_FACTOR",
                ident,
                iso,
                value=val,
                source=src,
                root_cause=(
                    "open R2-vs-R5 disposition (not a residual on this "
                    "value): GAS_AVAILABILITY_FACTOR is not read anywhere in "
                    "src/market_sim (dead/orphaned, confirmed by grep "
                    "2026-07-05), so this verified value has zero materiality "
                    "today. Either wire it in with a fleet-mix-weighted "
                    "reconciliation against the ISO's own CT/CC/ST capacity "
                    "shares (replacing, never stacking with, the existing "
                    "per-unit EFORD-derived availability) or delete it as "
                    "dead code (rule 26) — tracked in "
                    f"{_ISSUE_C18_GAS_AVAILABILITY_DEAD_CODE}"
                ),
            )
        )
    if sc.get("cc_peaking_per_plant"):
        out.append(
            _entry(
                "CC_REGULAR_PEAKING_PCT_BY_PLANT",
                "constants.py CC_REGULAR_PEAKING_PCT_BY_PLANT (engaged via "
                "cc_peaking_per_plant)",
                "residual",
                iso,
                n_scalars=4,
                source="per-plant CC peaking-tranche % applied to exactly the "
                "four F-class CCs the model over-ran (audit C-12; W1d marker) — "
                "not a published turbine limit",
                root_cause="audit C-12 open item: derive duct-burner share from "
                "EIA-860 duct-firing capability or CAMPD max-vs-base output, "
                "or fold into the generic curve",
            )
        )
    if iso == "ERCOT":
        out.append(
            _entry(
                "coal_take_or_pay_tranches",
                "scenarios.py coal tranche shares 0.30/0.25/0.45 + passthrough "
                "0.35 (constants.py:154)",
                "residual",
                iso,
                n_scalars=4,
                source="core coal offer-curve step sizes (audit C-8) — "
                "'Tier 3 (calibration)'; sanctioned mechanism, undisciplined "
                "values",
                root_cause="audit C-8: ground on contract-structure data "
                "(EIA-923 fuel-cost dispersion) or freeze via rule 23; open: "
                + _ISSUE_C8_CORE_STEPS,
            )
        )
        out.append(
            _entry(
                "CHP_BTM_PCT_BY_SECTOR['merchant']",
                "constants.py CHP_BTM_PCT_BY_SECTOR",
                "residual",
                iso,
                value=35.0,
                source="merchant CHP behind-the-meter share — industrial/"
                "commercial re-derived from EIA-923 Schedule-8 (S3), merchant "
                "retained at its prior fitted value (audit C-4; W1d marker)",
                root_cause="no independent merchant-CHP host-load source found "
                "yet — replace when one exists (constants.py comment); open: "
                + _ISSUE_C4_MERCHANT_CHP,
            )
        )
    if iso == "CAISO":
        out.append(
            _entry(
                "CAISO_TAC_ZONE_WEIGHTS['PGE-TAC']",
                "constants.py CAISO_TAC_ZONE_WEIGHTS",
                "residual",
                iso,
                value={"NP15": 0.86, "ZP26": 0.14},
                source="PG&E TAC load split across Path 15 — preserves a prior "
                "ratio of unverified provenance (audit C-16; W1d marker). "
                "B-CAI-1 intake attempt (2026-07-05): FERC-714 unreachable "
                "(403/502 via proxy); CEC reachable but planning-area geography "
                "(PG&E Bay Area / PG&E Valley) is boundary-mismatched to Path 15 "
                "(rule-14); the direct NP15/ZP26 zonal load lives in CAISO OASIS "
                "(unreachable — needs fetch-caiso-oasis.yml). No refit (no source).",
                root_cause="audit C-16: refine when NP15/ZP26 zonal load lands "
                "via the OASIS fetch workflow (rule-23 trigger); open: "
                + _ISSUE_C16_PGE_TAC_SPLIT,
            )
        )
        # C-5 (audit): the 7,500 MW WECC_import_simultaneous cap. Superseded in
        # the caiso-51 keeper (published MIC sum + measured p95 corridor
        # envelopes), retained ONLY as the capacity_deliverability_limits-off
        # (forecast-path) fallback. Fallback-only ledger row so it cannot
        # silently re-become the binding import limit.
        out.append(
            _entry(
                "WECC_import_simultaneous.cap_mw",
                "iso_configs.py CAISO interface_limits (fallback; "
                "capacity_deliverability_limits OFF only)",
                "residual",
                iso,
                value=7500.0,
                source="fitted aggregate WECC import cap — SUPERSEDED in the "
                "caiso-51 keeper by the published branch-group MIC sum "
                "(16,055/16,452/16,148 MW 2023/24/25) + measured p95 corridor "
                "envelopes (docs/caiso-c5-wecc-cap-closeout-2026-07-03.md). "
                "Not in the keeper binding path; governs the forecast / "
                "non-deliverability path only.",
                root_cause="O-1 forecast/backcast parity: the fitted 7,500 still "
                "caps forecast-mode imports — re-ground the default on the "
                "published MIC/SIL or enable deliverability part-A in forecast; "
                "open: " + _ISSUE_C5_C14_SEAM_FALLBACKS,
            )
        )
        # C-14 (audit): the aggregate WECC export cap. Re-derived in B-CAI-1
        # from the SAME measured EIA-930 CISO net-interchange series the per-hub
        # export envelopes use (scripts/derive_caiso_export_cap.py): 3,500 (fitted
        # "typical peak", ~p99) -> 4,361 MW (peak-bucket p95, measured capability).
        # Used ONLY by the superseded caiso_bidir_intertie; the keeper's
        # caiso_per_hub_intertie bounds exports by physical TTC + measured
        # envelope, so this scalar is not in any keeper solve (fallback-only).
        out.append(
            _entry(
                "CAISO_BIDIR_EXPORT_CAP_MW",
                "transmission.py (fallback; caiso_bidir_intertie only)",
                "measured-physical",
                iso,
                value=4361.0,
                source="aggregate WECC export-direction capability ceiling, "
                "re-derived from EIA-930 CISO net-interchange (the realized ATC "
                "proxy; OASIS unreachable) at the corridor mechanism's own p95 "
                "peak-bucket convention, 2023-2025 (2026 holdout excluded, "
                "rule 22); frozen scripts/derive_caiso_export_cap.py. rule-23 "
                "source-data change: the caiso-51 keeper measured export "
                "envelopes.",
                root_cause="fallback-only (superseded by caiso_per_hub_intertie); "
                "refresh against a true OASIS export-ATC pull, or R5-delete the "
                "caiso_bidir_intertie mechanism (rule 26); tracked in "
                + _ISSUE_C5_C14_SEAM_FALLBACKS,
            )
        )
        if sc.get("ct_netload_drag"):
            out.append(
                _entry(
                    "ct_netload_drag hinge coefficients",
                    "ScenarioConfig drag defaults (CAMPD-regressed hinge)",
                    "measured-physical",
                    iso,
                    source="net-load->CT commitment hinge regressed from CAMPD "
                    "(the template mechanism, audit §2)",
                    root_cause="D-8 flags weak identification for CAISO: slope "
                    "drifts +18% leave-2025-out and the floor ~= measured CT "
                    "energy (docs/out-of-sample-results-2026-07.md §2A) — "
                    "re-derive only on source-data updates (rule 23)",
                )
            )
    if sc.get("reliability_floor"):
        out.append(
            _entry(
                "reliability_floor coefficients",
                f"data/raw/reference/reliability_floor_coeffs_{iso}.csv",
                "measured-physical",
                iso,
                source="temperature/net-load day-gated commitment floors, "
                "CAMPD-derived (frozen derive script); the three Spearman-rho "
                "sign-flip limbs are R1-disabled (r1_disabled=True, ships off)",
                root_cause="D-8 §2B: the three sign-flip limbs (PJM ComEd/"
                "CC_REGULAR, CAISO SP15/ST_GAS + SP15/CC_REGULAR tmax) were "
                "UNIDENTIFIED out-of-training and are now permanently disabled "
                "under rule R1 (B-LIMB-1; derive R1_DISABLED_LIMBS). Remaining "
                "R6-keep drift limbs (drift >gate, no sign flip): ERCOT Houston "
                "CT +13.5%, PJM EMAAC ST_GAS +35.8%, SWMAAC CT -15.6%, ATSI "
                "rho-decay limbs — kept enabled with this caveat; re-derive "
                "trigger is the 2026 CAMPD publication (a source-data change), "
                "never a residual (rule 23)",
            )
        )
    if sc.get("nyiso_local_selfsupply"):
        out.append(
            _entry(
                "NYISO_LOCAL_SELFSUPPLY_FRAC['Long_Island']",
                "constants.py NYISO_LOCAL_SELFSUPPLY_FRAC",
                "residual",
                iso,
                value=0.45,
                source="LI self-supply floor set 'a touch below' the 2023 "
                "realized share ~0.48 (audit C-17; W1d marker) — the LMIC rule "
                "is market design but the fraction is outcome-anchored",
                root_cause="audit C-17 / B-NYI-1: the published Zone-K LCR is "
                "now on disk (data/raw/capacity-deliverability/nyiso/nyiso.csv, "
                "value_pu 1.052/1.053/1.065) but it is a PEAK-capacity ratio, "
                "while this is an all-hours energy self-supply fraction — a "
                "rule-14 boundary mismatch: substituting the LCR% (~1.05) or the "
                "TSL-implied ~0.94 peak fraction over-forces ~2x the physical LI "
                "generation, and any scalar reproducing ~0.45 requires a "
                "load-duration haircut tuned to the realized share (rule-12 pin). "
                "The faithful fix is a peak-capacity/TSL MECHANISM, not a scalar "
                "re-ground; 0.45 left in place — open: " + _ISSUE_NYISO_LI_LCR_MISMATCH,
            )
        )
    if iso in ("NYISO", "NEISO", "PJM", "MISO", "CAISO"):
        out.append(
            _entry(
                f"IMPORT_TRANCHES/EXPORT_TRANCHES[{iso}]",
                "interchange_config.py per-ISO seam supply-curve ladders",
                "residual",
                iso,
                source="fitted seam price/volume ladders (audit C-6/L7/L8); "
                "CAISO's keeper supersedes the fitted ladder with measured hub "
                "prices on the binding path but the static ladder remains the "
                "fallback",
                root_cause="audit C-6 open item: replace year-keyed rungs with "
                "measured hub prices / published wheeling costs per seam; "
                + _HOLDOUT_ROOT_CAUSE,
            )
        )
    return out


def build_ledger(bundle: Path, iso: str) -> dict:
    """Assemble the free_parameters section for one bundle."""
    sc = json.loads((bundle / "run_config.json").read_text()).get("scenario_config", {})
    entries = config_entries(sc, iso) + curated_entries(sc, iso)
    n_res = sum(1 for e in entries if e["identification"] == "residual")
    return {
        "schema": "dof-ledger/v1",
        "seeded": "2026-07-04 S5 governance session — audit §3 class-C table + "
        "W1d residual-identified/forecast-risk markers "
        "(docs/model-legitimacy-audit-2026-07.md; CLAUDE.md rule 20)",
        "n_entries": len(entries),
        "n_residual": n_res,
        "entries": entries,
    }


def update_attestation(bundle: Path, iso: str, check: bool = False) -> bool:
    """Write (or verify) the ledger into the bundle's attestation.

    Returns True when the attestation already matched (check) / was written.
    """
    att_path = bundle / "calibration_attestation.json"
    att = json.loads(att_path.read_text()) if att_path.exists() else {}
    ledger = build_ledger(bundle, iso)
    if check:
        return att.get("free_parameters") == ledger
    att["free_parameters"] = ledger
    att_path.write_text(json.dumps(att, indent=2) + "\n")
    return True


def main() -> None:
    """CLI: seed one bundle's ledger, or every keeper's."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", nargs="?", type=Path)
    ap.add_argument("--iso", help="ISO id (required with a bundle path)")
    ap.add_argument("--all-keepers", action="store_true")
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify the ledger is current; exit 1 when stale",
    )
    args = ap.parse_args()
    targets: list[tuple[Path, str]] = []
    if args.all_keepers:
        keepers = json.loads((REPO / "frontend/data/backcast/keepers.json").read_text())
        for run_id in keepers.get("keepers", []):
            side = json.loads(
                (
                    REPO / "frontend/data/backcast/registry" / f"{run_id}.json"
                ).read_text()
            )
            targets.append((REPO / side["bundle"], side["iso"]))
    elif args.bundle:
        if not args.iso:
            ap.error("--iso is required with a bundle path")
        targets.append((args.bundle, args.iso))
    else:
        ap.error("pass a bundle path or --all-keepers")
    stale = []
    for bundle, iso in targets:
        ok = update_attestation(bundle, iso, check=args.check)
        state = ("current" if ok else "STALE") if args.check else "written"
        print(f"{iso:6s} {bundle}: free_parameters {state}")
        if not ok:
            stale.append(str(bundle))
    if stale:
        sys.exit(1)


if __name__ == "__main__":
    main()
