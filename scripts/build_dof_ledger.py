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
# Root-cause issues opened during the 2026-07 scalar-remediation B-CAI-1 batch
# (CAISO C-16 PGE-TAC Path-15 split; C-5/C-14 WECC seam forecast-path fallbacks).
_ISSUE_C16_PGE_TAC_SPLIT = (
    "https://github.com/jessicacohen554-cyber/market-simulator/issues/1372"
)
_ISSUE_C5_C14_SEAM_FALLBACKS = (
    "https://github.com/jessicacohen554-cyber/market-simulator/issues/1373"
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
        if iso.upper() == "MISO":
            # MISO's COAL_SIGMOID_DEFAULTS were re-derived 2026-07-09 from the
            # #1803 EIA Annual Coal Report region f.o.b.-mine price + BLS PPI
            # coal-mining series by scripts/derive_coal_sigmoid.py — each of the
            # four parameters is grounded in measured coal-commodity data (merit
            # crossover from region delivered cost; cost-tracking ceil; gas-trough
            # floor; cross-region dispersion slope), not fitted to a MISO residual
            # (docs/handoffs/coal-sigmoid-rederive-2026-07.md). So for MISO this
            # is a measured-physical parameter, no longer a residual DOF — the
            # frozen derive script + provenance CSV + freeze test are its
            # identification. Other ISOs' entries remain hand-tuned residuals
            # until their own re-derive (their live literals are unchanged).
            out.append(
                _entry(
                    "COAL_SIGMOID_DEFAULTS[MISO]",
                    "scenarios.py COAL_SIGMOID_DEFAULTS (engaged via "
                    + ", ".join(sigmoids)
                    + ")",
                    "measured-physical",
                    iso,
                    n_scalars=4 * len(sigmoids),
                    source="re-derived from #1803 region f.o.b./PPI by "
                    "scripts/derive_coal_sigmoid.py (frozen; provenance "
                    "data/raw/_processed-legacy/coal_sigmoid_params.csv; freeze "
                    "test tests/test_derive_coal_sigmoid.py) — retires the ERCOT "
                    "byte-copy (issue #1347/G-26); fit to measured coal commodity "
                    "movement, never a MISO residual",
                )
            )
        else:
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
    # C-12 CLOSED 2026-07 (rule 26, G-26 scalar sweep): CC_REGULAR_PEAKING_PCT_
    # BY_PLANT deleted from constants.py — confirmed dead in every current
    # keeper (ERCOT's keeper already carried cc_peaking_per_plant=False,
    # favoring the measured cc_duct_peaking mechanism; every non-ERCOT keeper
    # with cc_peaking_per_plant=True was driving only the separate,
    # legitimate CAMPD-measured thermal_tranche_peaking path — this entry was
    # a false positive for those ISOs, since their plant codes never matched
    # the deleted dict's four ERCOT-specific keys). No replacement entry
    # needed: no residual scalar remains.
    if iso == "ERCOT":
        out.append(
            _entry(
                "coal_take_or_pay_tranches",
                "scenarios.py ScenarioConfig.coal_tranche_{1,2,3}_{frac,"
                "fuel_passthrough} (0.30/0.25/0.45 capacity fracs, 0.00/0.35/1.00 "
                "fuel passthrough); the constants.py COAL_TRANCHES mirror of "
                "these values was dead code (never read) and was deleted 2026-07",
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
                "yet — replace when one exists (constants.py comment); survey "
                "of candidate sources + recommended EIA-923 Schedule-8 intake "
                "path: docs/handoffs/merchant-chp-host-load-memo-2026-07.md; "
                "open: " + _ISSUE_C4_MERCHANT_CHP,
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
                "(unreachable at the time — needs fetch-caiso-oasis.yml). "
                "RE-CHECKED 2026-07-07 (G-26 scalar sweep): OASIS "
                "(oasis.caiso.com SingleZip) IS now reachable — a SLD_FCST/"
                "ACTUAL zipped-XML load file fetched successfully, contradicting "
                "the 2026-07-05 finding. Re-opened as actionable; still not "
                "done (finding the NP15/ZP26 sub-TAC report + parse + validate "
                "is a data-intake project, not this session's scope). No refit.",
                root_cause="audit C-16: refine when NP15/ZP26 zonal load lands "
                "via the OASIS fetch workflow (rule-23 trigger; OASIS confirmed "
                "reachable 2026-07-07, unblocking that workflow); open: "
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
    if iso == "NEISO":
        # C-6 CLOSED for NEISO 2026-07-06 (docs/calibration-log.md same date):
        # IMPORT_TRANCHES/EXPORT_TRANCHES[NEISO] re-derived by the frozen
        # scripts/derive_neiso_import_tranches.py from measured EIA-930
        # per-seam flows + NYISO proxy-bus DA LBMPs (rule 23) — no longer a
        # residual fit. Listing it under the generic residual bucket below
        # would be a false positive (the CC-peaking-pct pattern this same
        # sweep found elsewhere), so NEISO gets its own measured-physical row.
        out.append(
            _entry(
                "IMPORT_TRANCHES/EXPORT_TRANCHES[NEISO]",
                "interchange_config.py NEISO seam supply-curve ladders",
                "measured-physical",
                iso,
                source="per-seam Q-Q duration coupling of measured ISO-NE DA "
                "hub LMP with measured EIA-930 per-seam flows, frozen "
                "scripts/derive_neiso_import_tranches.py (audit C-6 CLOSED "
                "2026-07-06)",
                root_cause="re-derive trigger is a source-data change only "
                "(rule 23), never a residual; shape gap: flat annual rungs "
                "cannot carry within-year seam variation (calibration-log "
                "2026-07-06 neiso-51 P9 re-test)",
            )
        )
    if iso == "MISO" and sc.get("miso_seam_measured_ladder"):
        # C-6 CLOSED for MISO 2026-07-07 (the NEISO pattern): every seam band
        # price comes from MISO_SEAM_LADDER_BY_YEAR — the frozen
        # scripts/derive_miso_seam_ladders.py Q-Q coupling of measured EIA-930
        # per-seam flows with the measured MISO DA hub LMP (rule 23). The
        # generic residual bucket below would be a false positive for this
        # config, so it gets its own measured-physical row instead.
        out.append(
            _entry(
                "MISO_SEAM_LADDER_BY_YEAR",
                "interchange_config.py MISO seam band-price ladders",
                "measured-physical",
                iso,
                source="per-seam Q-Q duration coupling of the measured MISO "
                "DA hub LMP with measured EIA-930 per-seam flows on the "
                "fixed 8-band grid, frozen scripts/derive_miso_seam_ladders"
                ".py (audit C-6 CLOSED for MISO 2026-07-07; G-23-residual "
                "import-starvation fix)",
                root_cause="re-derive trigger is a source-data change only "
                "(rule 23), never a residual; representation bound: hourly "
                "placement of the scheduled seam base is duration-curve-"
                "level only (docs/multi-iso/miso-import-starvation-"
                "rootcause-2026-07.md §3)",
            )
        )
    if iso == "PJM" and sc.get("pjm_seam_measured_ladder"):
        # C-6 CLOSED for PJM 2026-07-10 (the MISO/NEISO pattern): every seam
        # band price comes from PJM_SEAM_LADDER_BY_YEAR — the frozen
        # scripts/derive_pjm_seam_ladders.py Q-Q coupling of PJM's measured
        # settlement-grade tie-line flows with the measured PJM DA system
        # LMP (rule 23). The generic residual bucket below would be a false
        # positive for this config, so it gets its own measured-physical row.
        out.append(
            _entry(
                "PJM_SEAM_LADDER_BY_YEAR",
                "interchange_config.py PJM seam band-price ladders",
                "measured-physical",
                iso,
                source="per-seam Q-Q duration coupling of the measured PJM "
                "DA system LMP with PJM's measured settlement-grade "
                "tie-line flows (act_sch_interchange, pooled by "
                "PJM_SEAM_TIE) on the fixed 8-band grid, frozen "
                "scripts/derive_pjm_seam_ladders.py (audit C-6 CLOSED for "
                "PJM 2026-07-10; pjm-95 C1 2023-interchange-duration fix); "
                "displaces the firm scheduled-export floor on ladder years "
                "(rule 19, alternatives never stacked)",
                root_cause="re-derive trigger is a source-data change only "
                "(rule 23), never a residual; representation bound: hourly "
                "placement of the scheduled seam base is duration-curve-"
                "level only (same bound as the MISO ladder)",
            )
        )
    if iso == "PJM" and sc.get("pjm_measured_interface_limits"):
        # G-20 Phase-2 internal-interface overlay (pjm-97): the seven mapped
        # internal links' forward TTC flips static-estimate ->
        # measured-physical — the hourly published Data Miner 2 transfer
        # limits (transfer-interface-limits clean datatype) replace the
        # Tier-3 constants their 2024 means seeded. Zero fitted scalars: the
        # crosswalk (PJM_INTERFACE_LINK_MAP) is a documented boundary
        # reconciliation, not a tuned value.
        out.append(
            _entry(
                "PJM_INTERFACE_LINK_MAP hourly TTC overlay",
                "constants.py crosswalk + data/transfer_interface_limits.py "
                "(iso_configs._pjm_config static seeds superseded on mapped "
                "links, forward direction)",
                "measured-physical",
                iso,
                source="published hourly interface transfer limits (PJM Data "
                "Miner 2 transfer_limits_and_flows, 2023-2025 raw drops; "
                "min(pre,post) where both publish), curated by frozen "
                "scripts/curate_transfer_interface_limits.py onto the model "
                "clock; supersedes PJM_MEASURED_INTERNAL_TTC's pooled "
                "medians on mapped links (same feed, hourly — rule 19). "
                "Unmapped links (AEP_Ohio->ATSI, SWMAAC->EMAAC, "
                "SWMAAC->Dominion, West_APS->Dominion) and every reverse "
                "direction keep the Tier-3 static estimates (boundary "
                "misalignments documented at the crosswalk).",
                root_cause="re-derive trigger is a source-data change only "
                "(rule 23); representation bound: AP-South maps to the "
                "seeded West_APS->SWMAAC link only (parallel-path split of "
                "the reduced mesh), and the Average envelopes are regional "
                "means, not per-flowgate boundaries",
            )
        )
    if sc.get("tranche_startup_amortization") and sc.get(
        "tranche_startup_measured_runs"
    ):
        # Fast-start amortization v3 (Order-825/ELMP analogue): the CT
        # econ/peak tranches amortize the published NREL start cost over the
        # CAMPD-measured median start-to-stop run length (the horizon
        # ceiling; P0 runs may only shorten it). Both inputs are
        # independently sourced — the artifact is a frozen rule-23 derive,
        # so it gets a measured-physical row (the flag itself is a structure
        # gate, not a tuned scalar).
        out.append(
            _entry(
                f"campd_ct_run_lengths_{iso}.csv (fast-start v3 horizon)",
                "data/raw/_processed-legacy/campd_ct_run_lengths_"
                f"{iso}.csv via fleet.campd_ct_run_lengths",
                "measured-physical",
                iso,
                source="EPA CAMPD unit-level hourly grossLoad start-to-stop "
                "run blocks (simple-cycle CT units, pooled 2023-2025), "
                "frozen scripts/derive_campd_ct_run_lengths.py; start cost "
                "is the published NREL/SR-5500-55433 CT_STARTUP_PARAMS "
                "(constants.py)",
                root_cause="re-derive trigger is a source-data change only "
                "(rule 23), never a residual; representation bound: "
                "monthly-granularity amortization (compute_monthly_markup), "
                "no within-day run-length variation",
            )
        )
    if sc.get("tranche_startup_conditional_runs"):
        # Fast-start amortization v4 (condition-keyed horizon): the v3
        # measured ceiling scales per hour by the class net-load-percentile
        # band ratio — measured shape (CAMPD runs keyed by start-hour
        # EIA-930 net-load percentile), forward-native trigger (within-year
        # percentile of the run's own net-load series). Frozen rule-23
        # derive; no tuned scalar.
        out.append(
            _entry(
                f"campd_ct_run_bands_{iso}.csv (fast-start v4 band ratios)",
                "data/raw/_processed-legacy/campd_ct_run_bands_"
                f"{iso}.csv via fleet.campd_ct_run_band_ratios",
                "measured-physical",
                iso,
                source="EPA CAMPD start-to-stop runs keyed by start-hour "
                "within-year net-load percentile (EIA-930 D-WND-SUN), "
                "class-pooled band medians / pooled median (shape), plant "
                "median (level); frozen scripts/derive_campd_ct_run_lengths"
                ".py --condition-bands",
                root_cause="re-derive trigger is a CAMPD/EIA-930 source-data "
                "change only (rule 23); band edges recorded in the artifact "
                "and checked against the consumer",
            )
        )
    if sc.get("miso_measured_reserve_requirements"):
        # Measured hourly OR requirement basis: a measured AS power
        # reservation (rule-13 admissible quantity, never a price) replacing
        # the flat fleet-MSSC+400 and South within-zone-MSSC estimates
        # (rule-14 mandatory swap). Forecast years keep the MSSC+regulating
        # formula as the forward generator.
        out.append(
            _entry(
                "miso_measured_reserve_requirements (hourly OR series)",
                "data/raw/MISO-AS/asm_rt_cleared_mw_<year>.parquet via "
                "data.miso_reserve_requirements",
                "measured-physical",
                iso,
                source="MISO ASM real-time cleared-offers market report "
                "(masked unit MW, reg+spin+supp summed; STR excluded), "
                "fetch_miso_asm.py rollups; published curve shapes translate "
                "with the hourly requirement (NYISO #1344 convention)",
                root_cause="basis caveats documented in the module "
                "docstring: RT cleared (no DA hourly series is published) "
                "and cleared < requirement in rare true-shortage intervals; "
                "refresh rides the fetch pipeline only (rule 23)",
            )
        )
    if sc.get("miso_south_seam_split"):
        # Topology fix, ZERO scalars: the South seam's bands re-home onto
        # their own external zone, severing the fabricated free
        # South→external→Midwest wheel around the RDT contract path (the
        # only real S↔N boundary; MISO/SPP JOA). No parameter — the entry
        # documents the mechanism's provenance for the attestation.
        out.append(
            _entry(
                "miso_south_seam_split (South-seam external-zone split)",
                "transmission.split_miso_south_external_node + "
                "build_reference_price_node zone_overrides",
                "measured-physical",
                iso,
                n_scalars=0,
                source="MISO/SPP JOA (Midwest and South footprints exchange "
                "power only over the RDT contract path across SPP); 2025 "
                "diagnostic probe measured the shared-bus bypass at 1,255 MW "
                "summer mean / 7.7 TWh-yr vs an RDT S->N binding 13 h/yr",
                root_cause="pure topology correction — no tunable; reverts "
                "only if the JOA interconnection structure changes",
            )
        )
    if sc.get("miso_rdt_tcdc"):
        # Published RDT operating representation, ZERO fitted scalars: 92%
        # default derate + $40/$500 two-step TCDC + JOA contract hard bound,
        # all published values (constants.MISO_RDT_*).
        out.append(
            _entry(
                "miso_rdt_tcdc (RDT 92% default derate + $40/$500 TCDC tiers)",
                "constants.MISO_RDT_* via transmission.apply_miso_rdt_tcdc; "
                "priced one-way tiers (TransferLink.flow_cost)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="2024 MISO SOM §III.B (92% default derate; two-step "
                "TCDC $40 at the modeled limit, $500 from 102%); MISO/SPP "
                "JOA Attach. A (3,000 N->S / 2,500 S->N contract limits)",
                root_cause="deliberately conservative: the 92% DEFAULT "
                "derate is used, not the deeper condition-driven operator "
                "derates (utilization averaged 84% of contract when binding "
                "in 2024, SOM §II.E) — no published hourly derate series, so "
                "binding-hour congestion under-shoots rather than fitting a "
                "haircut; re-derives only when MISO publishes new TCDC/derate "
                "parameters (rule 23)",
            )
        )
    if sc.get("miso_rpe_pricing"):
        # RPE additive violation pricing, ZERO scalars: the single published
        # $200/MWh demand value added to both RDT violation tiers — the
        # measured 2023-2025 additive price formation ($240 small-violation /
        # $700 deep-violation spreads).
        out.append(
            _entry(
                "miso_rpe_pricing (RPE $200 additive on RDT violation tiers)",
                "constants.MISO_RPE_DEMAND_VALUE via "
                "transmission.apply_miso_rdt_tcdc (rpe_pricing=True); adds to "
                "the two violation tiers' TransferLink.flow_cost only",
                "measured-physical",
                iso,
                n_scalars=0,
                source="2024 MISO SOM §II.E ('MISO enforces STR requirements "
                "in its two subregions by enforcing reserve procurement "
                "enhancement (RPE) constraints over the RDT') + §III.B "
                "(single $200/MWh demand value; RDT+RPE 'apply additively' "
                "in real violations — measured $700 spreads, small "
                "violations overpriced by $200); IMM Summer-2025 quarterly "
                "($41M RDT+RPE congestion, +121% YoY)",
                root_cause="deliberately conservative: the RPE's "
                "STR-scarcity binding channel (binds with NO RDT violation "
                "when importing-subregion STR is limited — the quarterly's "
                "'RPE Only' category) is unrepresented because the LP "
                "carries no STR product, so separation under-shoots; the "
                "IMM's cap-at-$500 recommendation was not implemented "
                "in-window — date-gate the re-anchor if MISO adopts it "
                "(rule 23)",
            )
        )
    if sc.get("unit_outage_short_windows"):
        # Short (< 5-day) baseload-coal unit-outage windows, ZERO scalars:
        # each window is the unit's own CEMS record; the derive-script guards
        # (coal-only detector, CF >= 0.55 baseload screen, in-merit filter)
        # are shared published constants of the parent outage derivation.
        out.append(
            _entry(
                "unit_outage_short_windows (< 5-day baseload-coal CEMS windows)",
                "data/raw/campd-unit-outages-short-{ISO}.csv via "
                "outages.unit_outage_short_derate_factors (applied next to "
                "the >= 5-day parent overlay; disjoint by construction)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="per-unit EPA CAMPD hourly gross generation "
                "(scripts/derive_campd_unit_outages.py --short-windows); "
                "identification guards: coal-only detector + unit annual "
                "CF >= 0.55 (the partial-outage detector's baseload "
                "constant) + the revealed-availability in-merit filter "
                "(derive_campd_outages.filter_revealed_outages; the "
                "full-stop override cannot engage below the 5-day cap)",
                root_cause="the >= 5-day duration floor makes "
                "event-coincident short forced outages invisible (MISO "
                "Jul 28-29 2025: ~2.8 GW coal offline at the peak block "
                "beyond the overlay; "
                "docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md); CT/CC event "
                "unavailability stays unmodeled pending a max-gen-event "
                "registry intake (no identification without it)",
            )
        )
    if sc.get("class_aware_fuel_price_fallback"):
        # Class-aware F923 gap-fill donor, ZERO scalars: gap-filled months
        # are priced from same-class reporting plants first (state, then
        # zone), the class-blind fuel-group pools remaining the fallback.
        # The donor pools are the ISO's own EIA-923 Schedule-5 filings
        # re-aggregated by the recipient's plant class — no tunable exists.
        out.append(
            _entry(
                "class_aware_fuel_price_fallback (same-class F923 donor pools)",
                "data.fuel._NearbyFuelPrices same-class tier (state -> zone "
                "-> class-blind fuel-group fallback); donor plants "
                "classified by capacity-dominant model class within the "
                "fuel group",
                "measured-physical",
                iso,
                n_scalars=0,
                source="EIA-923 Schedule-5 delivered fuel costs (the same "
                "F923 parquet the fallback already reads), re-pooled by "
                "plant class; measured basis: MISO 2024 CT filers "
                "$4.13/MMBtu cap-wtd vs CC $2.57 while the quantity-weighted "
                "class-blind pool is CC-burn-dominated (~$2.6)",
                root_cause="the class-blind donor priced the ~33% of "
                "non-filing CT capacity ~$16-20/MWh below its measured "
                "class cost, feeding the 2024 CT_PEAKER economic over-run "
                "at PRB's expense and July-2025's too-cheap North margin "
                "(docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md §6, lane 1(b))",
            )
        )
    if sc.get("coal_warm_committed"):
        # Warm-boiler exemption, ZERO scalars: the P1 startup-amortization
        # markup (compute_monthly_markup, NREL $100/MW coal cold start) is
        # skipped for coal bins whose fuel-free mustrun tranche keeps the
        # boiler online — committed-band dispatch is a hot-unit output ramp,
        # not a cold start. No parameter; the boolean gates on the plant's
        # own CAMPD-derived must-run floor (must_run_pct > 0).
        out.append(
            _entry(
                "coal_warm_committed (warm-boiler committed-band exemption)",
                "model.commitment.compute_monthly_markup warm-boiler branch; "
                "gated per plant on must_run_pct > 0 (CAMPD thermal-tranche "
                "artifact)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="dispatch forensics on the miso-58 2023 replay "
                "(on/off LMP crossings: COAL_PRB committed $34.6 vs ~$26 "
                "static F923 SRMC, COAL_BIT $43.8 vs ~$29-31, mustrun bands "
                "online 84-98% of the same hours) + MISO IMM measured "
                "conduct (som-competitive-conduct: offers AT cost, system "
                "price-cost markup +3.0%/-2.5% — self-committed units "
                "recover start costs outside the energy offer)",
                root_cause="removes a fabricated cold-start premium, adds "
                "no tunable; reverts only if the fleet's measured must-run "
                "floors disappear (rule 23: rides the thermal-tranche "
                "artifact refresh)",
            )
        )
    if sc.get("coal_committed_takeorpay_regulated"):
        # Regulated/self-committed coal committed-band take-or-pay pricing,
        # ZERO fitted scalars: the _committed tranche of a coal plant in the
        # conduct scope (EIA-860 Regulatory Status RE UNION > 0.5 Schedule-4
        # cost-of-service ownership x utility Entity Type) passes
        # (1 - contract_share) of its own measured EIA-923 Schedule-5 fuel —
        # the identical sunk-contract rule the _mustrun band already uses.
        # Replaces the rank-scoped coal_bit_committed_takeorpay (rule 19
        # reconcile); a pricing bid, not a floor (rule 17/18: no min-gen row).
        out.append(
            _entry(
                "coal_committed_takeorpay_regulated (regulated/self-committed "
                "coal committed-band take-or-pay pricing)",
                "fleet.campd_tranche_fuel_frac committed_takeorpay_regulated "
                "branch; scope = fleet.eia860_selfcommit_scope_plants "
                "(EIA-860 Regulatory Status RE UNION > 0.5 Schedule-4 "
                "cost-of-service ownership x utility Entity Type I/M/C/P/S/F); "
                "committed tranche passes (1 - contract_share) of measured "
                "EIA-923 Schedule-5 fuel, bounded below by any supply "
                "passthrough",
                "measured-physical",
                iso,
                n_scalars=0,
                source="MISO SOM Table 7 regulated-utility coal conduct split "
                "(regulated self-commit 56%/53% must-run 2023/2024 vs merchant "
                "93%/74% offered economically; "
                "som-competitive-conduct/som_competitive_conduct.csv) + EIA-860 "
                "Regulatory Status RE set and Schedule-4 ownership x utility "
                "Entity Type (eia860_plant.parquet) + EIA-923 Schedule-5 "
                "take-or-pay shares (coal_takeorpay_MISO.csv) + CAMPD committed "
                "tranches (docs/handoffs/miso-coal-conduct-design-2026-07.md)",
                root_cause="replaces the rank-scoped coal_bit_committed_takeorpay "
                "(rule 19 reconcile — RE-BIT covered identically, NR-BIT "
                "merchants revert to the economic offers the SOM measures); "
                "re-derives only on a new EIA-860 vintage (RE UNION COS set), a "
                "new EIA-923 Schedule-5 vintage (shares), or a new SOM "
                "publication (conduct citation) — never a residual (rule 23)",
            )
        )
    if sc.get("st_gas_mustrun_per_plant"):
        # ST_GAS local-reliability commitment floor, ZERO fitted scalars:
        # each plant's measured committed tranche (thermal_tranches_<ISO>.csv
        # committed_pct, CEMS P5-when-online) is forced on in its measured
        # top-online_frac system-load window. Both quantities are CAMPD-
        # measured per plant; the boolean adds no tunable.
        out.append(
            _entry(
                "st_gas_mustrun_per_plant (ST_GAS local-reliability "
                "commitment floor, measured committed window)",
                "fleet.bins_to_fleet cc_mustrun_pmin_mw ST_GAS branch; "
                "window = top online_frac system-load hours "
                "(thermal_tranches_<ISO>.csv, derive_thermal_tranches.py)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="CAMPD/CEMS 2023-2025: Entergy MISO-South steam fleet "
                "synchronized supermajority of ALL hours (Nine Mile 98.2%, "
                "P5-all-hours 414 MW; Sabine 85.6%; Lewis Creek 87.8%) under "
                "VLR/self-commitment (MISO SOM out-of-market local-"
                "reliability commitments, South region) while the "
                "economically-dispatched class ran near-dark",
                root_cause="the committed share and online fraction re-derive "
                "from multi-year CAMPD when the record extends (rule 23); "
                "true cyclers publish small fractions and force little "
                "(self-limiting by measurement, rule 18)",
            )
        )
    if sc.get("st_gas_mustrun_p25_level"):
        # miso-67 LEVEL SWAP for st_gas_mustrun_per_plant, ZERO fitted scalars:
        # the floor level becomes each gate-armed ST_GAS plant's measured
        # 25th-percentile-of-online available-CF (thermal_tranches_<ISO>.csv
        # p25_cf) x nameplate, replacing the committed tranche (P5-of-online =
        # LSL). Same frozen CEMS estimator (p25_cf is written by the SAME
        # derive_thermal_tranches.py pass as committed_pct/online_frac — rule 23,
        # no deriver touch), same window, same mechanism id — only the level
        # source changes (rule 19). The boolean adds no tunable.
        out.append(
            _entry(
                "st_gas_mustrun_p25_level (ST_GAS floor level = measured "
                "p25-of-online available-CF x nameplate)",
                "fleet.thermal_tranche_p25_level + generators_to_fleet_arrays "
                "ST_GAS p25 block; window = top online_frac system-load hours "
                "(thermal_tranches_<ISO>.csv, derive_thermal_tranches.py)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="CAMPD/CEMS 2023-2025 p25-of-online available-CF per "
                "plant (Sabine 32.9%, Harding Street 36.7%, Lewis Creek 28.4%, "
                "Nine Mile 49.4%): the measured 25th-percentile dispatch level of "
                "the Entergy MISO-South VLR steam fleet, which ran 30-67% CF "
                "despite local LMP at/below SRMC (out-of-market VLR dispatch — "
                "Amite South / DSG / WOTAB, MISO SOM). Replaces the committed "
                "P5-of-online LSL (the correct min-stable-load but the wrong "
                "dispatch level — miso-67 triage design)",
                root_cause="p25_cf re-derives from multi-year CAMPD exactly like "
                "committed_pct/online_frac when the record extends (rule 23); the "
                "level stays BELOW available capacity so the floor never pins the "
                "plant and dispatch above it is free (rule 13 — no outcome "
                "pinning); a retired/deregulated plant exits the artifact",
            )
        )
    if sc.get("carry_operating_mothballs"):
        # miso-68 Cottonwood lane, ZERO fitted scalars: re-carry each OA
        # (mothballed) unit the canonical snapshot's OP filter drops for
        # backcast solve year Y iff it is OP in the year-matched EIA-860
        # vintage_<Y> — EIA's own contemporaneous status, the rule-13
        # availability oracle (a unit truly idle in Y is OA in vintage_<Y>
        # too, so OA status alone never re-carries capacity). Per-unit, from
        # the vintage rows (year-matched capacity); a solve year with no
        # committed vintage carries nothing. The boolean adds no tunable.
        out.append(
            _entry(
                "carry_operating_mothballs (OA-but-operating re-carry, "
                "vintage-status oracle)",
                "fleet.load_mothballed_but_operating + the run_calibration "
                "backcast fleet-build seam (joins the within-window retiree "
                "injection)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="EIA-860 year-matched vintage status (vintage_<Y>/"
                "eia860_generators.parquet): a unit OA in the 2025ER canonical "
                "snapshot is re-carried for solve year Y iff OP in vintage_<Y> "
                "(Cottonwood 55358: 4 of 8 units OA, ~572.6 MW vintage_2023 / "
                "~568.7 MW vintage_2024, with CAMPD showing the OA CTs running "
                "88-91% of 2023 hours). Real units at availability bounds — "
                "never a CAMPD-MWh pin or a MW offset (rules 1/11/13). Design: "
                "docs/handoffs/miso-cc-vintage-undercarry-plan-2026-07.md",
                root_cause="regenerates for any forward vintage (a unit OP in "
                "its latest vintage is physically available until a real exit "
                "removes it — rule 12 forward story); the LP dispatches the "
                "carried units freely (no outcome pinning)",
            )
        )
    if (
        iso in ("NYISO", "CAISO")
        or (iso == "MISO" and not sc.get("miso_seam_measured_ladder"))
        or (iso == "PJM" and not sc.get("pjm_seam_measured_ladder"))
    ):
        out.append(
            _entry(
                f"IMPORT_TRANCHES/EXPORT_TRANCHES[{iso}]",
                "interchange_config.py per-ISO seam supply-curve ladders",
                "residual",
                iso,
                source="fitted seam price/volume ladders (audit C-6/L7/L8); "
                "CAISO's keeper supersedes the fitted ladder with measured hub "
                "prices on the binding path but the static ladder remains the "
                "fallback; NEISO closed this item (see the NEISO-only entry, "
                "measured-physical), MISO closes it under "
                "miso_seam_measured_ladder and PJM under "
                "pjm_seam_measured_ladder (their own measured-physical rows) "
                "— remaining scope for this item is NYISO/CAISO's static "
                "ladder (and the MISO/PJM formula seams only when their "
                "measured ladders are off)",
                root_cause="audit C-6/#1350 open item: replace year-keyed "
                "rungs with measured hub prices / published wheeling costs "
                "per seam, following the NEISO precedent "
                "(scripts/derive_neiso_import_tranches.py); " + _HOLDOUT_ROOT_CAUSE,
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
