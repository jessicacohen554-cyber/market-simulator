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

# PER-ISO identification source for the ``coal_warm_committed`` warm-boiler
# exemption (rule 25 ``[R-ISO-SCOPE]`` / rule 28 (d)): each ISO that arms the
# gate cites the measurement made on ITS OWN market. A verdict transfers to no
# other ISO, so there is deliberately no cross-ISO fallback text that reads as
# evidence — the default says only that the arming ISO owes its own.
_COAL_WARM_COMMITTED_SOURCE = {
    "MISO": (
        "dispatch forensics on the miso-58 2023 replay (on/off LMP crossings: "
        "COAL_PRB committed $34.6 vs ~$26 static F923 SRMC, COAL_BIT $43.8 vs "
        "~$29-31, mustrun bands online 84-98% of the same hours) + MISO IMM "
        "measured conduct (som-competitive-conduct: offers AT cost, system "
        "price-cost markup +3.0%/-2.5% — self-committed units recover start "
        "costs outside the energy offer)"
    ),
    "SOCO": (
        "SOCO's own committed-keeper hourlies (lane SOCO-58 phase 0, zero LP, "
        "on 2026-09-20-soco57-measured-cc-heat): the warm-boiler predicate is "
        "measured at 100.0% in ALL EIGHTEEN coal plant-years 2023-2025 — in "
        "every hour in which a plant's _committed tranche carries capacity, "
        "that plant's _mustrun tranche is generating at load fraction 1.00, so "
        "the boiler is never dark when the committed band could be dispatched. "
        "The markup it removes is measured at EXACTLY $100.00/MWh on four of "
        "six plants in 2024 (the startup/max(avg_run,1.0) floor, i.e. ZERO P0 "
        "runs) and is anti-correlated with the year's need for coal (implied "
        "P0 run length 1.0 h in 2024 vs 769 h at plant 6002 in 2025), so its "
        "year-to-year variation is a P0 feedback artifact and not a physical "
        "driver. Scope verified exact: 6 of 6 coal tranches carrying a startup "
        "cost are exempted, 0 coal tranches carrying one are missed, and 0 "
        "non-coal tranches are touched"
    ),
}
_COAL_WARM_COMMITTED_SOURCE_DEFAULT = (
    "NOT IDENTIFIED FOR THIS ISO — rule 25 [R-ISO-SCOPE] requires the arming "
    "ISO to cite its own market's measurement of the warm-boiler predicate "
    "(mustrun tranche online in the hours the committed tranche is available) "
    "and of the markup being removed; add it to "
    "build_dof_ledger._COAL_WARM_COMMITTED_SOURCE"
)

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
# _ISSUE_C8_CORE_STEPS (issue #1336, the coal_tranche_* re-grounding debt)
# removed 2026-08-12 with its ledger entry: the scalars were deleted outright
# (ercot-188 G#3), so the debt closed rather than re-grounded.
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
# C-16 / #1372 is CLOSED by caiso-172 (2026-08-04): the PGE-TAC split is now
# MEASURED from OASIS ATL_LDF x ATL_PNODE_MAP, so its entry below is
# identification="measured" and carries no root_cause. The constant is retained
# for the historical citation only — do NOT re-attach it to a residual entry.
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


#: Sigmoid TOGGLE field -> the coal supply tag whose curve it engages, mirroring
#: `market_sim.data.fuel.trajectories._COAL_SIGMOID_FIELD_STEM` inverted. Used by
#: :func:`_coal_sigmoid_resolves` so the ledger attests a fitted sigmoid only where
#: one is actually characterized (caiso-236).
_COAL_SIGMOID_TOGGLE_SUPPLY: dict[str, tuple[str, str]] = {
    # toggle field -> (supply tag, the config field stem its overrides use)
    "coal_prb_passthrough_sigmoid": ("prb", "prb_passthrough"),
    "coal_lignite_passthrough_sigmoid": ("lignite", "lignite_passthrough"),
    "coal_bit_passthrough_sigmoid": ("bituminous", "bit_passthrough"),
    "coal_sub_passthrough_sigmoid": ("subbituminous", "sub_passthrough"),
    "coal_wc_passthrough_sigmoid": ("waste", "waste_passthrough"),
}

_COAL_SIGMOID_PARAMS = ("floor", "ceil", "gas_mid", "gas_slope")


def _coal_sigmoid_resolves(sc: dict, iso: str, toggle: str) -> bool:
    """Return whether ``toggle``'s coal sigmoid is actually characterized.

    Mirrors :func:`market_sim.data.fuel.trajectories.coal_sigmoid_params`: the
    registry entry for ``(iso, supply)`` overlaid by any explicitly-set
    ``coal_<stem>_<param>`` field, complete on all four parameters or nothing.
    An armed toggle over an uncharacterized supply engages NO parameters — the
    solve falls back to the flat passthrough — so it must not put a row in the
    DOF ledger (rule 21 ``[R-DOF]``: the ledger states the free parameters that
    exist, not the ones a flag name implies).
    """
    from market_sim.config.scenarios import COAL_SIGMOID_DEFAULTS

    supply, stem = _COAL_SIGMOID_TOGGLE_SUPPLY[toggle]
    params = dict(COAL_SIGMOID_DEFAULTS.get((iso.upper(), supply), {}))
    for name in _COAL_SIGMOID_PARAMS:
        value = sc.get(f"coal_{stem}_{name}")
        if value is not None:
            params[name] = value
    return all(name in params for name in _COAL_SIGMOID_PARAMS)


def _prb_follower_engaged(sc: dict, iso: str) -> bool:
    """Return whether the tiered PRB follower curve consumes its own parameters.

    ``prb_follower`` is the one coal passthrough tier with **no sigmoid toggle of
    its own**: its gate is the conjunction ``coal_prb_passthrough_sigmoid AND
    coal_prb_passthrough_tiered`` (``data.fleet.assembly``), and when it fires
    ``data.fuel.trajectories.prb_follower_passthrough_series`` resolves a SECOND
    four-parameter set — ``COAL_SIGMOID_DEFAULTS[(iso, "prb_follower")]`` overlaid
    by the explicit ``coal_prb_follower_*`` fields — for the low-must-run PRB
    cyclers, alongside the baseload prb curve.

    Same resolve-or-nothing discipline as :func:`_coal_sigmoid_resolves`: an
    incomplete set makes ``prb_follower_passthrough_series`` fall back to the
    baseload prb curve, so there are no additional free parameters to attest.
    """
    if not (
        sc.get("coal_prb_passthrough_sigmoid") and sc.get("coal_prb_passthrough_tiered")
    ):
        return False
    from market_sim.config.scenarios import COAL_SIGMOID_DEFAULTS

    params = dict(COAL_SIGMOID_DEFAULTS.get((iso.upper(), "prb_follower"), {}))
    for name in _COAL_SIGMOID_PARAMS:
        value = sc.get(f"coal_prb_follower_{name}")
        if value is not None:
            params[name] = value
    return all(name in params for name in _COAL_SIGMOID_PARAMS)


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
    # caiso-236 (rule 21 [R-DOF] ledger integrity): a sigmoid TOGGLE being on is
    # NOT evidence that a fitted sigmoid exists. `fuel.trajectories.coal_sigmoid_params`
    # resolves each (ISO, supply) pair against COAL_SIGMOID_DEFAULTS, overlaid by the
    # explicit `coal_<stem>_{floor,ceil,gas_mid,gas_slope}` fields; when the resolved
    # set is incomplete it returns None and `coal_passthrough_series` falls back to the
    # FLAT passthrough — so the toggle is armed over nothing and there are no free
    # parameters to attest. Counting the toggle alone made the ledger claim four fitted
    # scalars that do not exist anywhere in the code for any ISO carrying no curve:
    # CAISO arms `coal_prb_passthrough_sigmoid` and COAL_SIGMOID_DEFAULTS holds no
    # ("CAISO", *) key at all, so its "COAL_SIGMOID_DEFAULTS[CAISO]" row was a PHANTOM,
    # over-counting the residual by one entry and four scalars. The gate below counts a
    # toggle only when its supply's parameter set actually RESOLVES. This can only
    # REMOVE over-counted rows, never add one.
    # Record: results/calibration/FINDING-caiso236-dof-residual-ledger-audit-2026-09-02.md
    sigmoids = [
        k
        for k in (
            "coal_prb_passthrough_sigmoid",
            "coal_lignite_passthrough_sigmoid",
            "coal_bit_passthrough_sigmoid",
            "coal_sub_passthrough_sigmoid",
            "coal_wc_passthrough_sigmoid",
        )
        if sc.get(k) and _coal_sigmoid_resolves(sc, iso, k)
    ]
    # xiso-7 (rule 21 [R-DOF] ledger integrity, the UNDER-count half — the mirror
    # of the caiso-236 over-count fix above). The list comprehension enumerates the
    # five `coal_*_passthrough_sigmoid` TOGGLES, but the tiered PRB follower tier
    # has no toggle of its own (see `_prb_follower_engaged`): armed by the
    # conjunction with `coal_prb_passthrough_tiered`, it resolves a SECOND
    # four-parameter set for the low-must-run PRB cyclers that
    # `n_scalars = 4 * len(sigmoids)` counted nowhere. An over-count is the
    # conservative direction — it claims more fitted surface than exists; an
    # UNDER-count states fewer free parameters than the solve consumes, which is
    # the disclosure failure rule 21 exists to prevent, so it is counted here.
    # `tiers` (not `sigmoids`) also gates the row's emission: the follower set can
    # resolve for an ISO whose BASELOAD prb pair does not, in which case the tier
    # is live and is the row's only engaged parameter set.
    # Record: results/calibration/FINDING-xiso7-prb-follower-dof-undercount-2026-09-02.md
    tiers = sigmoids + (
        ["coal_prb_passthrough_tiered (prb_follower tier)"]
        if _prb_follower_engaged(sc, iso)
        else []
    )
    if tiers:
        if iso.upper() == "MISO":
            # MISO's COAL_SIGMOID_DEFAULTS were re-derived 2026-07-09 from the
            # #1803 EIA Annual Coal Report region f.o.b.-mine price + BLS PPI
            # coal-mining series by scripts/data/derive_coal_sigmoid.py — each of the
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
                    + ", ".join(tiers)
                    + ")",
                    "measured-physical",
                    iso,
                    n_scalars=4 * len(tiers),
                    source="re-derived from #1803 region f.o.b./PPI by "
                    "scripts/data/derive_coal_sigmoid.py (frozen; provenance "
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
                    + ", ".join(tiers)
                    + ")",
                    "residual",
                    iso,
                    n_scalars=4 * len(tiers),
                    source="gas-keyed coal passthrough sigmoids — the largest fitted "
                    "surface (audit C-1); owner-sanctioned under rule #1",
                    root_cause="weakly identified: each asymptote is pinned by a "
                    "single gas regime (floor by 2024, gas_mid/ceil by 2025 — "
                    "docs/out-of-sample-results-2026-07.md §2C); open: literature/"
                    "physical anchoring of floor/ceil, plus " + _HOLDOUT_ROOT_CAUSE,
                )
            )
    if sc.get("coal_perplant_offer_level"):
        # ERCOT-144: the per-plant measured coal offer curves — the rule-19
        # REPLACEMENT of the COAL_* band multipliers + supply sigmoids on the
        # CAMPD committed/econ rows. The armed harness strips the COAL_*
        # groups from offer_curve_by_group and disarms the sigmoids, so the
        # residual entries those config keys generated drop out of this
        # ledger by construction; this measured-physical row is their
        # replacement (rule 21 — every retired entry replaced by a measured
        # one, never a re-tuned one).
        out.append(
            _entry(
                "coal_perplant_offer_curves (per-plant measured TPO curves)",
                "constants.COAL_PERPLANT_OFFER_CURVE_BY_ISO via "
                "run_config.scenario_config.coal_perplant_offer_curves; "
                "applied in fleet.legacy_bins.apply_coal_tranches",
                "measured-physical",
                iso,
                n_scalars=0,
                source="each plant's merged modal 60-Day SCED Submitted TPO "
                "supply curve, pooled over the four 2024-2025 disclosure "
                "subsets — verbatim submitted conduct, zero fitted "
                "parameters (frozen scripts/data/derive_coal_perplant_offer.py; "
                "provenance data/raw/_processed-legacy/"
                "coal_perplant_offer_curves_ERCOT.json; ERCOT-144, chartered "
                "by ERCOT-143 §2's per-plant measurement)",
                root_cause="re-derive trigger is a new SCED disclosure "
                "subset only (rule 23), never a residual; representation "
                "bounds declared in the ERCOT-144 precommit: the 2023 "
                "application is an extrapolation (no 2023 SCED exists), "
                "levels are fuel-invariant by measurement (mid-band only — "
                "_mustrun/_peak keep their measured fuel/gas responses), and "
                "within-tranche measured dispersion is capacity-weight "
                "averaged at the CAMPD tranche grain",
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
    if sc.get("ercot_storage_adaptive_expectation"):
        # ercot-221: the two rule-23 frozen constants of the adaptive-
        # expectation storage offer, identified in the PRE-REGISTERED Phase-0
        # v2 instrument on the MEASURED 2023 daily evening storage offer
        # surface (delivery-2023 60-Day SCED corpus, ERCOT-154/161 population
        # discipline) — measured CONDUCT as identification evidence, never a
        # price residual (the ercot-210/211/218 instrument class). Re-derive
        # only on a source-data change (rule 23), never on a residual.
        out.append(
            _entry(
                "ercot_adaptive_half_life_days / ercot_adaptive_beta",
                "run_config.scenario_config.ercot_adaptive_*",
                "measured-physical",
                iso,
                value=[
                    sc.get("ercot_adaptive_half_life_days"),
                    sc.get("ercot_adaptive_beta"),
                ],
                n_scalars=2,
                source="EWMA half-life (days) and gain beta of the daily "
                "spike-frequency expectation P_hat, SSE-fit of "
                "implied_P(d) = evening storage offer p50 / ordc_voll on "
                "P_hat(d) over admissible days 2023-06-10..12-31 on the "
                "pre-registered grid (PRECOMMIT-ercot221-adaptive-"
                "expectation-2026-08-18.md Amendment 1 family v2; artifact "
                "results/calibration/ercot221_adaptive_phase0.json). The "
                "armed path consumes only the model's own pass-1 price path "
                "(Amendment 4) — the measured surface is identification "
                "evidence only. Phase-0 v1+v2 FAILED their gates; Phase-1 "
                "entered on owner instruction (recorded in the precommit "
                "Amendment 2), so these constants are additionally flagged "
                "by that standing record.",
            )
        )
    if sc.get("caiso_storage_adaptive_expectation"):
        # caiso-205: the two rule-23 frozen constants of the CAISO leg,
        # identified in the PRE-REGISTERED caiso-204 Phase-0 instrument on
        # the MEASURED 2023-2025 daily evening storage offer surface
        # (PUB_BID_DAM 585-date balanced subset, caiso-178 classifier) —
        # measured CONDUCT as identification evidence, never a price
        # residual. Re-derive only on a source-data change (rule 23).
        out.append(
            _entry(
                "caiso_adaptive_half_life_days / caiso_adaptive_beta",
                "run_config.scenario_config.caiso_adaptive_*",
                "measured-physical",
                iso,
                value=[
                    sc.get("caiso_adaptive_half_life_days"),
                    sc.get("caiso_adaptive_beta"),
                ],
                n_scalars=2,
                source="EWMA half-life (days) and gain beta of the daily "
                "spike-frequency expectation P_hat, SSE-fit of "
                "implied_P(d) = evening battery discharge offer p50 / "
                "$1,000 park cap on P_hat(d) over 585 admissible days "
                "2023-2025 on the pre-registered grid (PRECHECK-caiso204-"
                "adaptive-phase0-2026-08-19.md §2-3; artifact "
                "results/calibration/caiso204_adaptive_phase0.json, G-ID "
                "daily corr 0.704, G-DECAY 2023-only fit transfers 79%). "
                "The armed path consumes only the model's own pass-1 price "
                "path — the measured surface is identification evidence "
                "only. Phase-0 FAILED G-BOOT (bootstrap infeasible on the "
                "caiso-200 keeper path); Phase-1 entered on owner order "
                "(caiso-205 charter branch 1), so these constants are "
                "additionally flagged by that standing record.",
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
    # coal_take_or_pay_tranches CLOSED 2026-08-12 (rule 26, ercot-188 G#3
    # owner ruling): the ScenarioConfig.coal_tranche_{1,2,3}_* sextet and its
    # sole consumer, the legacy (non-CAMPD) offer_curves.split_coal_tranches
    # path, were DELETED — dead in build_dispatch_fleet's else limb for every
    # registered bundle of all six ISOs (use_campd_bins=True everywhere;
    # proof: results/calibration/ercot188_g3_unreachability_proof.json;
    # miso-128 §4 proved inertness dynamically). The former entry here was
    # already scoped to `not use_campd_bins` configs, i.e. it never fired on
    # a registered run. No replacement entry: the issue-#1336 re-grounding
    # debt closes with the scalars — there is nothing left to re-ground.
    if iso == "ERCOT":
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
                "measured",
                iso,
                value={"NP15": 0.883951, "ZP26": 0.116049},
                source="PG&E TAC load split across Path 15 — MEASURED "
                "(caiso-172, 2026-08-04), closing audit C-16. Derived by "
                "scripts/data/derive_caiso_path15_load_split.py (rule 23 "
                "[R-FROZEN-DERIVE]) from two published OASIS Atlas reports: "
                "ATL_LDF's per-pnode load distribution factors inside "
                "DLAP_PGAE-APND (1,668 load pnodes summing to exactly 100.000 "
                "— CAISO's own weighting for distributing PG&E LAP load onto "
                "nodes), joined by substation to ATL_PNODE_MAP's authoritative "
                "TH_NP15_GEN / TH_ZP26_GEN membership, which IS the Path-15 "
                "geography as CAISO defines it. Two-tier assignment (direct "
                "substation match; else the node's PG&E sub-LAP dominant hub — "
                "SLAP_PGZP and SLAP_PGKN are 100% ZP26, the other thirteen "
                "~100% NP15); ~2.2 residue points reported and EXCLUDED from "
                "the normalisation; day-weighted over every live effective "
                "window. Per-year ZP26 0.11644/0.11554/0.11600 (2023/24/25), "
                "backcast-mean 0.116049, spread 0.0011, acceptance 10/10. "
                "Supersedes the 0.86/0.14 estimate, which put 17% too much "
                "PG&E load in ZP26. Artifact: data/raw/zone-specific-demand/"
                "CAISO/CAISO_path15_load_split.{csv,json}. RECONCILIATION, not "
                "identity (rule 14's clause): an LDF is a *typical* "
                "distribution factor, so this is a measured STATIC scalar "
                "replacing an assumed static scalar — NOT an hourly NP15/ZP26 "
                "load series, which no source publishes (five alternatives "
                "walled and re-checkable in "
                "scripts/probes/_caiso172_subtac_load_survey.py).",
            )
        )
        out.append(
            _entry(
                "caiso-plant-hub-membership crosswalk",
                "data/raw/reference/caiso-plant-hub-membership.csv "
                "(zone_assignment CAISO first-check)",
                "measured",
                iso,
                value={"plants": 446, "gw_joined": 41.1, "movers": 78},
                source="generator -> trading-hub membership, CAISO's own "
                "geography — MEASURED (caiso-217 intake, 2026-08-23; the "
                "caiso-216 §F.1 packet item C1, completing the caiso-172 "
                "path15_load_split program on the generation side). Derived "
                "by scripts/data/derive_caiso_plant_hub_membership.py (rule "
                "23 [R-FROZEN-DERIVE]) from the committed ATL_PNODE_MAP "
                "(pnode -> TH_NP15/TH_ZP26/TH_SP15 membership at latest "
                "effective window) joined to EIA-860 plants through four "
                "evidence tiers (verified-pin / eia-lmp-node / "
                "reviewed-crosswalk / resource-name), hub-unanimity enforced, "
                "precision-over-recall (two looser channels built, audited, "
                "REMOVED). ZERO free scalars: measured membership overrides "
                "the lat-cut/county-lift estimate wherever joined "
                "[R-ACCURATE]; unjoined plants keep the geographic rule; "
                "TH_SP15 carries no sub-zone information so LCR-pocket "
                "resolution is preserved. Witness gates (caiso-216 §E) ALL "
                "PASS: DIABLO->TH_ZP26, ALTA/WINDHUB->TH_SP15, "
                "TOPAZ->TH_ZP26, MUSTANG->TH_NP15. Artifact sidecar carries "
                "the full mover table as the committed review surface.",
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
                source="fitted aggregate WECC import cap. Its supersession by "
                "the published branch-group MIC sum (16,055/16,452/16,148 MW "
                "2023/24/25; docs/caiso-c5-wecc-cap-closeout-2026-07-03.md) is "
                "CONDITIONAL on capacity_deliverability_limits Part A actually "
                "resolving, which happens through the GITIGNORED, disposable "
                "clean partition data/clean/capacity-deliverability/ that no "
                "solve auto-builds. caiso-188 MEASURED the condition failing: "
                "every CAISO bundle from caiso-175 (2026-08-06) onward — the "
                "designated keeper caiso184_c1_lpbasis included — pins total "
                "net import at exactly 7,500.0 MW in 764/477/809 hours of "
                "2023/24/25 and never exceeds it, while run_config.json "
                "records capacity_deliverability_limits: true. So this scalar "
                "IS on the keeper's backcast binding path, and the earlier "
                "'not in the keeper binding path' text was an assertion, not a "
                "measurement (FINDING-caiso188-import-tranche-dof-2026-08-09.md "
                "§4; FINDING-caiso133 §3/§4 remain correct for the MIC cap they "
                "assumed and do not cover the value that actually bound). "
                "Rule 14 [R-ACCURATE]: the measured EIA-930 record falsifies "
                "7,500 as a physical bound — the real CAISO system exceeded it "
                "in 271/293/681 hours, reaching 13,136/13,312/15,080 MW, all "
                "of which the published MIC envelopes.",
                root_cause="TWO open items. (1) caiso-188: Part A must not be "
                "able to no-op silently — the LP now WARNs and names the baked "
                "fallback it will solve against (interchange/spec.py), but "
                "nothing COMMITTED yet records which cap a bundle solved "
                "against; the durable fix is to persist the resolved seam cap "
                "into run_config.json (or make the clean partition a build "
                "dependency of the flag). (2) O-1 forecast/backcast parity: "
                "the fitted 7,500 also caps forecast-mode imports — re-ground "
                "the default on the published MIC/SIL; open: "
                + _ISSUE_C5_C14_SEAM_FALLBACKS,
            )
        )
        # C-14 (audit) CLOSED BY DELETION at caiso-236. The row that stood here,
        # CAISO_BIDIR_EXPORT_CAP_MW = 4,361 MW (the aggregate WECC export cap),
        # was read ONLY by caiso_bidir_intertie, which was off on the CAISO keeper
        # AND off in the ScenarioConfig defaults — dead in every shipped
        # configuration while one CLI flag could re-arm it. Rule 26 [R-DELETE]
        # ("a deprecated parameter that still parses is a re-armable answer key")
        # says such a knob is removed, not zeroed, so the mechanism and its cap
        # were deleted rather than re-documented. Its own root_cause named this
        # exit: "R5-delete the caiso_bidir_intertie mechanism (rule 26)".
        # Record: results/calibration/FINDING-caiso236-dof-residual-ledger-audit-2026-09-02.md
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
    if sc.get("temp_dependent_derate") and (
        sc.get("temp_derate_slope_st_chp") is not None
        or sc.get("temp_derate_slope_ct_chp") is not None
    ):
        # miso-101: the ISO-OWN cogen ambient slope. Only enumerated when an ISO
        # has overridden the committed literature value with its own measured
        # one — the literature defaults are `published` rows, this is the
        # measured-physical replacement (rule 25 [R-ISO-SCOPE]: pjm-95 refuted
        # the literature slopes on PJM's own fleet, so they do not transfer).
        _slope = sc.get("temp_derate_slope_st_chp") or sc.get(
            "temp_derate_slope_ct_chp"
        )
        out.append(
            _entry(
                "temp_derate_slope_st_chp / _ct_chp",
                "ScenarioConfig (per-ISO measured cogen ambient slope)",
                "measured-physical",
                iso,
                value=_slope,
                source="within-day PLANT-DAY fixed-effects regression of log "
                "CEMS gross load on the hour-grain dry-bulb over the ISO's own "
                "CEMS-identifiable cogens, 2023-2025; class value = the "
                "capacity-weighted p50 across plants (the same population "
                "statistic derive_campd_gas_commitment_params.py uses for "
                "min_load_frac). Frozen derive script "
                "scripts/data/derive_campd_temp_derate_params.py; artifact "
                "data/raw/_processed-legacy/campd_temp_derate_params_<ISO>.csv. "
                "The onset was measured ABSENT (response present below 15 C), "
                "hence the hinge-free mean-anchored form. ZERO fitted scalars: "
                "the estimator never sees a price, a benchmark or a model "
                "output, and it is level-neutral by construction",
                root_cause="not a residual DOF. Leave-one-year-out on MISO "
                "gives 0.00153/0.00140/0.00130 vs 0.00141 full-sample (+-8 %), "
                "so no year drives it; re-derive trigger is a CAMPD or weather "
                "source-data update, never a residual (rule 23 "
                "[R-FROZEN-DERIVE]). Per-ISO by construction — a slope measured "
                "on one ISO's fleet never fills another's (rule 25)",
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
        # scripts/data/derive_neiso_import_tranches.py from measured EIA-930
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
                "scripts/data/derive_neiso_import_tranches.py (audit C-6 CLOSED "
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
        # scripts/data/derive_miso_seam_ladders.py Q-Q coupling of measured EIA-930
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
                "fixed 8-band grid, frozen scripts/data/derive_miso_seam_ladders"
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
        # scripts/data/derive_pjm_seam_ladders.py Q-Q coupling of PJM's measured
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
                "scripts/data/derive_pjm_seam_ladders.py (audit C-6 CLOSED for "
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
        # G-20 Phase-2 internal-interface overlay (pjm-97): the mapped
        # internal links' forward TTC flips static-estimate ->
        # measured-physical — the hourly published Data Miner 2 transfer
        # limits (transfer-interface-limits clean datatype) replace the
        # Tier-3 constants their 2024 means seeded. Zero fitted scalars: the
        # crosswalk (PJM_INTERFACE_LINK_MAP) is a documented boundary
        # reconciliation, not a tuned value. (pjm-cong-1 2026-07-16: the
        # mis-attributed 50045005 -> ComEd->AEP entry was removed — Manual 03
        # §3.8 puts the 5004/5005 interface in Pennsylvania — so ComEd->AEP
        # rides its static estimate again; six mapped links remain.)
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
                "scripts/data/curate_transfer_interface_limits.py onto the model "
                "clock; supersedes PJM_MEASURED_INTERNAL_TTC's pooled "
                "medians on mapped links (same feed, hourly — rule 19). "
                "Unmapped links (AEP_Ohio->ATSI, SWMAAC->EMAAC, "
                "SWMAAC->Dominion, West_APS->Dominion) and every reverse "
                "direction keep the Tier-3 static estimates (boundary "
                "misalignments documented at the crosswalk).",
                root_cause="re-derive trigger is a source-data change only "
                "(rule 23); representation bound: AP-South maps to the "
                "seeded West_APS->SWMAAC link only (parallel-path split of "
                "the reduced mesh), and the Average Western/Central series "
                "are Manual-03 PA-corridor interfaces applied to the links "
                "their means seeded (boundary misalignment documented at "
                "the crosswalk, pjm-cong-1 identity correction 2026-07-16)",
            )
        )
    if iso == "PJM" and sc.get("pjm_east_interface_cut"):
        # pjm-cong-1 (2026-07-16): the measured joint EMAAC-import cut — one
        # one-sided hourly aggregate group capping Flow(Central_PA->EMAAC) +
        # Flow(SWMAAC->EMAAC) at the published "Average Eastern" limit (PJM
        # Manual 03 §3.8: the EASTERN reactive transfer interface's monitored
        # EHV set spans both model links, so the joint cap is the faithful
        # reduced-network reading). Zero fitted scalars: the cap is the
        # measured series verbatim; the link set is the topology's existing
        # EMAAC import pair.
        out.append(
            _entry(
                "PJM EAST interface cut (joint EMAAC import cap)",
                "model/transmission.py PJM_EAST_CUT_LINKS + "
                "data/transfer_interface_limits.pjm_eastern_interface_hourly",
                "measured-physical",
                iso,
                source="published hourly 'Average Eastern' interface "
                "transfer limit (PJM Data Miner 2 transfer_limits_and_flows, "
                "2023-2025 raw drops), curated by frozen "
                "scripts/data/curate_transfer_interface_limits.py onto the model "
                "clock; interface identity verified against PJM Manual 03 "
                "§3.8 Rev 71 (diagnosis §10.3). One-sided (import "
                "direction); reverse flow and per-link statics unchanged.",
                root_cause="re-derive trigger is a source-data change only "
                "(rule 23); representation bound: the interface's monitored "
                "set sits slightly upstream of the exact EMAAC zone edge "
                "(Alburtis/Hosensack are PPL-side buses), documented as the "
                "rule-14 reduced-network reconciliation in diagnosis §10.5",
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
                "frozen scripts/data/derive_campd_ct_run_lengths.py; start cost "
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
                "median (level); frozen scripts/data/derive_campd_ct_run_lengths"
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
    if sc.get("miso_midwest_subregional_reserves"):
        # Midwest sub-regional reserve-holding family, ZERO scalars: the
        # MEASURED North+Central cleared OR reservation held IN the 5 physical
        # Midwest zones, priced at the single published $200 RPE demand value,
        # reserve_class 0 nested inside the market-wide RBDC. Closes the
        # ledgered "RPE Only" STR-scarcity gap the congestion-blind market-wide
        # family leaves open (a cost-min LP otherwise parks the market-wide
        # requirement in the RDT-trapped South surplus and converts Midwest
        # headroom to energy). Measured series + cited $200 + topology zone
        # list — no tunable.
        out.append(
            _entry(
                "miso_midwest_subregional_reserves (Midwest OR family, $200 RPE step)",
                "data/raw/MISO-AS/asm_rt_cleared_mw_<year>.parquet (North+Central "
                "leg) via data.miso_reserve_requirements + "
                "constants.MISO_RPE_DEMAND_VALUE via reserve_config._miso_design",
                "measured-physical",
                iso,
                n_scalars=0,
                source="MISO ASM RT cleared-offers (reg+spin+supp summed over "
                "regions {North, Central}); published RPE demand value $200/MWh "
                "(2024 SOM §III.B — the demand value of the sub-regional "
                "reserve-deliverability construct); 5 physical Midwest model "
                "zones (topology). The per-Reserve-Zone §5.2.1.2 Zonal ORDC "
                "ladder is NOT used — the per-zone Zonal ORDC never separated in "
                "26,280 measured 2023-2025 hours (miso-71 design §1b/§2a)",
                root_cause="LEDGERED LOWER BOUND (leg (b), the NYISO B1 "
                "precedent): the cleared series understates the true requirement "
                "in genuine-shortage intervals — the Midwest cleared DIPS to 957 "
                "MW (Jun-23/24-2025) / 851 MW (Jul-28/29-2025) against a ~2,165 "
                "MW mean — so holding it in the 2025 tail creates no shortfall "
                "(family dual $0 there) and the engagement is a LOWER BOUND, NOT "
                "'fixed' by any dip-undoing construction (rules 1/13); forecast "
                "years fall back to the within-region MSSC (rule 13); refresh "
                "rides the ASM fetch pipeline only (rule 23)",
            )
        )
    if sc.get("miso_winter_citygate_daily"):
        # Winter fuel-security Chicago Citygate daily gas shape, ZERO scalars:
        # in Dec/Jan/Feb the Chicago-hub zones' gas rows carry the MEASURED
        # Chicago Citygate daily shape (flow-date placed, mean-preserving
        # within month) in place of the national-HH gas_daily_shape — the
        # regional delivered-gas signal (Jan-12-2024 $25.82 vs HH $13.08)
        # that prices the Winter Storm Heather tail. Measured daily series +
        # published zone-hub assignment + market-structure conventions — no
        # tunable.
        out.append(
            _entry(
                "miso_winter_citygate_daily (Chicago Citygate winter daily gas shape)",
                "data/raw/gas-prices/miso_citygate_daily.csv via "
                "data.fuel.miso_chicago_daily_shape_factors / "
                "apply_miso_winter_citygate_daily (before "
                "apply_miso_zonal_gas_basis; supersedes the national "
                "gas_daily_shape in covered cells only)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="EIA Natural Gas Weekly Update spot-price table "
                "('Chicago' row = NGI Daily GPI), 680 weekday prints "
                "2023-2025 (scripts/data/fetch_miso_citygate_daily.py); Chicago-hub "
                "zone set {Illinois, Indiana, East} READ from "
                "miso_zonal_gas_hub.csv (hub == 'Chicago Citygate (IL)' — the "
                "same file apply_miso_zonal_gas_basis reads); winter months "
                "{12, 1, 2} (meteorological-winter pipeline-scarcity season); "
                "flow-date placement trade+1, weekend/holiday forward-fill "
                "(NG gas-day market structure; the caiso-90 "
                "_flow_date_staircase precedent)",
                root_cause="shape-only and mean-preserving WITHIN month by "
                "construction (rule 11: the keeper's monthly MISO gas level "
                "is measured EIA-923 and already correct — only the "
                "within-month daily placement changes); Chicago-only "
                "coverage: West/Plains/South keep the national-HH shape (HH "
                "is a conservative under-proxy for MidCon/Gulf, rule 14; "
                "Lower-Michigan/MichCon daily stays a paywalled-ICE open "
                "item, miso-data-audit Item 4); forecast years take the "
                "forward curve's regional Chicago basis and its own daily "
                "shape (rule 13 forward-native); refresh rides the EIA NGWU "
                "fetch only (rule 23)",
            )
        )
    if sc.get("miso_seam_envelope_merit_cap"):
        # G-23 seam-envelope composition fix, ZERO scalars: the measured seam
        # deliverability envelope applied with merit-order (waterfall) band
        # bounds instead of the uniform per-band derate — cheap base rungs
        # keep full width, the seam total is capped at min(cap, limit)
        # exactly, restoring the Q-Q ladder's price-to-depth pairing. No new
        # data: the envelope and the ladder (both already ledgered) are
        # byte-unchanged; this entry records the composition gate only.
        out.append(
            _entry(
                "miso_seam_envelope_merit_cap (seam envelope merit-order ceiling)",
                "model.transmission.inject_miso_seam_flow_limit(merit_cap=True), "
                "both directions (scripts/run_calibration.py seam-cap sites)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="Composition semantics only — no new measured series: "
                "the (month x hod) EIA-930 deliverability envelope and the "
                "MISO_SEAM_LADDER_BY_YEAR Q-Q rungs are byte-unchanged; band "
                "k's bound becomes clip(cap - (k-1)*step, 0, step). Root "
                "cause and frozen charter: docs/handoffs/miso-g23-seam-"
                "envelope-composition-design-2026-07.md (the uniform-derate "
                "offline replay reproduces the miso-72 keeper's solved "
                "priced-seam net +/-0.12 TWh in all three years).",
            )
        )
    if iso == "MISO" and sc.get("miso_manitoba_seam"):
        # miso-74 Manitoba two-way seam, ZERO fitted scalars: the import-only
        # annual-flat MHEB firm block (three measured per-year MW values) is
        # REPLACED by a fourth measured two-way priced seam — the
        # MISO_MANITOBA_SEAM_SPEC bands priced by the frozen Q-Q ladder
        # MISO_SEAM_LADDER_BY_YEAR["Manitoba"] (derived by
        # scripts/data/derive_miso_seam_ladders.py, same construction as PJM/SPP/
        # South) and capped by the measured (month x hod) two-way MHEB
        # deliverability envelope. Measured-for-measured swap: the interface
        # limit is physically pinned (measured +2,827 MW import extreme), the
        # emission factor 0.0 (hydro); it RETIRES the 3 firm-block MW values in
        # favor of the measured revealed supply curve — a net DOF improvement
        # (a flat import estimate -> a two-way measured structure).
        out.append(
            _entry(
                "miso_manitoba_seam (Manitoba MHEB two-way priced seam)",
                "interchange_config.MISO_MANITOBA_SEAM_SPEC + "
                'MISO_SEAM_LADDER_BY_YEAR["Manitoba"] + MISO_SEAM_DIBA["Manitoba"]',
                "measured-physical",
                iso,
                n_scalars=0,
                source="Q-Q duration coupling of the measured MISO DA hub LMP "
                "with the measured EIA-930 MHEB flow on the fixed 8-band grid, "
                "frozen scripts/data/derive_miso_seam_ladders.py; the two-way "
                "deliverability envelope is the per-(month x hod) percentile of "
                "the measured MHEB flow, both directions. Replaces the "
                "import-only firm block (retires its 3 per-year MW values). "
                "Frozen charter: docs/handoffs/miso-manitoba-seam-design-"
                "2026-07.md (offline P9 reproduces measured MHEB net flow "
                "+/-0.02 TWh/yr incl. the 2025 net export).",
                root_cause="re-derive trigger is a source-data change only "
                "(rule 23), never a residual; representation bound: hourly "
                "placement is duration-curve-level (price-decorrelated seam)",
            )
        )
    if iso == "MISO" and sc.get("miso_zonal_loss_surface"):
        # miso-76 M3 marginal-loss physics, ZERO fitted scalars: the Midwest
        # L1-L6 links become one-way pairs whose receiving-end energy-balance
        # coefficient is 1 - eps(month), eps derived from MISO's OWN published
        # per-hub LMP component record (MLC = MEC x (DF - 1), MISO BPM-002) as
        # the dimensionless per-zone monthly delivery-factor deviation surface
        # (frozen derive; per-year rows for backcast train years — the
        # same-year measured-physical class as CEMS emission rates — and
        # pooled rows as the forecast forward analogue). Zonal duals then
        # separate by the measured DF ratio: losses consume MWh and prices
        # stay LP duals (rule 4), never a price adder. The surface is the
        # measured object; the only non-measured device is the 0.001 flow
        # tiebreak (storage-eps class, transmission.MISO_LOSS_LINK_TIEBREAK_EPS).
        out.append(
            _entry(
                "miso_zonal_loss_surface (marginal delivery-factor surface)",
                "data/raw/iso-specific-transmission/MISO_loss_surface.csv via "
                "data.loss_surface.load_zone_month_deviation -> "
                "transmission.apply_miso_zonal_loss_links + "
                "build_miso_link_loss -> dispatch.build_constraints(link_loss)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="Ratio-of-sums dev_z,m = sum(MLC)/sum(MEC) per zone-"
                "month from the lmp-components clean record (MISO daily "
                "da_expost_lmp, 8 named hubs, DA basis; MEC recovered as the "
                "cross-hub mean of LMP-MCC-MLC, identity checked at "
                "curation). Plains (hub-less) = the documented West+Illinois "
                "bracketing proxy (D6). Frozen derive "
                "scripts/data/derive_miso_loss_surface.py; offline B1 "
                "acceptance 9/9 pair-years in [0.5x,1.5x] (ratios 0.96-1.01) "
                "before any solve. Charter: docs/handoffs/miso-nc-price-"
                "separation-design-2026-07.md §4.",
                root_cause="re-derive trigger is a source-data change only "
                "(rule 23), never a residual; representation bound: one-way "
                "monthly linearization (reverse direction clamps to 0 — "
                "under-transmits in atypical-direction/congested hours; the "
                "congestion component of separation is the documented "
                "data-blocked M4 gap)",
            )
        )
    if iso == "PJM" and sc.get("pjm_zonal_loss_surface"):
        # pjm-136 M2 marginal-loss physics, ZERO fitted scalars: the internal
        # PJM links become one-way pairs whose receiving-end energy-balance
        # coefficient is 1 - eps(month), eps derived from PJM's OWN published
        # per-ZONE LMP component record (LMP = MEC + MCC + MLC, PJM Manual 11
        # §2 / OATT Att. K) as the dimensionless per-zone monthly
        # delivery-factor deviation surface (frozen derive; per-year rows for
        # backcast train years — the same-year measured-physical class as CEMS
        # emission rates — and pooled rows as the forecast forward analogue).
        # Zonal duals then separate by the measured DF ratio: losses consume
        # MWh and prices stay LP duals (rule 4), never a price adder. The
        # surface is the measured object; the only non-measured device is the
        # 0.001 flow tiebreak (storage-eps class,
        # transmission.PJM_LOSS_LINK_TIEBREAK_EPS).
        out.append(
            _entry(
                "pjm_zonal_loss_surface (marginal delivery-factor surface)",
                "data/raw/iso-specific-transmission/PJM_loss_surface.csv via "
                "data.loss_surface.load_zone_month_deviation -> "
                "transmission.apply_pjm_zonal_loss_links + "
                "build_pjm_link_loss -> dispatch.build_constraints(link_loss)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="Ratio-of-sums dev_z,m = sum(MLC)/sum(MEC) per zone-"
                "month from PJM's published da_hrl_lmps type=ZONE record (all "
                "21 transmission zones, DA basis; MEC published per row and "
                "identity-checked uniform across zones per UTC interval to "
                "0.000000 $/MWh). Transmission zones roll up to model zones "
                "load-weighted by the metered hrl_load_metered series through "
                "the canonical eia930.zonal_shares._PJM_LOAD_ZONE_GROUPS "
                "crosswalk — every model zone is real, NONE interpolated. "
                "Frozen derive scripts/data/derive_pjm_loss_surface.py; "
                "offline acceptance 12/12 pair-years in [0.5x,1.5x] (ratios "
                "0.95-1.07) before any solve. Charter: results/calibration/"
                "FINDING-pjm136-zonal-dual-structure-2026-07-28.md.",
                root_cause="re-derive trigger is a source-data change only "
                "(rule 23), never a residual; representation bounds: one-way "
                "monthly linearization (reverse direction clamps to 0 — "
                "under-transmits in atypical-direction/congested hours), and "
                "the external star node carries NO loss (PJM_external is a "
                "fictitious pricing node with no published deviation), so "
                "seam-sourced energy is delivered lossless",
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
                "(scripts/data/derive_campd_unit_outages.py --short-windows); "
                "identification guards: coal-only detector + unit annual "
                "CF >= 0.55 (the partial-outage detector's baseload "
                "constant) + the revealed-availability in-merit filter "
                "(outage_detect.filter_revealed_outages; the "
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
        #
        # The identification SOURCE is PER-ISO (rule 25 ``[R-ISO-SCOPE]`` /
        # rule 28 (d)): a verdict transfers to no other ISO, so an ISO that
        # arms this gate must cite its OWN market's measurement. The entry
        # previously carried MISO's dispatch forensics verbatim for every
        # ISO, which would have published MISO's evidence as SOCO's
        # identification source the moment a second ISO armed it (found in
        # lane SOCO-58 phase 0, before any solve).
        out.append(
            _entry(
                "coal_warm_committed (warm-boiler committed-band exemption)",
                "model.commitment.compute_monthly_markup warm-boiler branch; "
                "gated per plant on must_run_pct > 0 (CAMPD thermal-tranche "
                "artifact)",
                "measured-physical",
                iso,
                n_scalars=0,
                source=_COAL_WARM_COMMITTED_SOURCE.get(
                    iso, _COAL_WARM_COMMITTED_SOURCE_DEFAULT
                ),
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
    if sc.get("unit_outage_maxgen_events"):
        # M-2 declared-event-window channel (miso-69 lane), ZERO fitted
        # scalars, TWO measured inputs: (1) the maxgen-events registry — each
        # row a declared MISO emergency-procedure instrument transcribed from
        # a primary IMM/SOM document; (2) the CAMPD revealed derates inside
        # those windows. The deriver's constants ($150 in-merit certificate,
        # ±45-day capability window, 2-hour certificate floor) are published
        # identification guards frozen in the design doc, not residual-tuned
        # values (the certificate's [$120,$200] sensitivity is recomputed and
        # printed at every derivation).
        out.append(
            _entry(
                "maxgen-events registry (declared capacity-emergency windows)",
                "data/raw/maxgen-events/{iso}/ via scripts/data/curate_maxgen_events "
                "(clean_io seam; schema maxgen-events.schema.yaml)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="primary IMM/SOM documents, one row per (declaration, "
                "region), every row cited (2023 SOM pp.11-12; 2024 SOM p.15; "
                "2025 SOM pp.iii/14-15 Figs 9-11; IMM Quarterly Summer-2025 "
                "pp.20-23): the pre-2026 Max Gen ladder — capacity advisories, "
                "alerts, warnings, event steps — with declared start/end "
                "(EST -> UTC) and declared region scope. A window with no "
                "primary document is NOT in the registry (F4: never "
                "reconstructed from prices)",
                root_cause="regenerates from each new declaration vintage "
                "(rule 23: re-derives only on source-data change); "
                "backcast-only availability-event family (rule 13) — a "
                "forecast year carries the class outage-rate machinery, no "
                "forward window is fabricated",
            )
        )
        out.append(
            _entry(
                "unit_outage_maxgen_events (declared-window revealed derates)",
                "data/raw/campd-unit-outages-maxgen-{ISO}.csv via "
                "outages.unit_outage_maxgen_derate_factors (applied next to "
                "the std/short overlays; class-agnostic — the only channel "
                "carrying the CT/CC event-window leg; disjointness vs "
                "std/short asserted at derivation)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="per-unit EPA CAMPD hourly gross generation inside the "
                "registry windows only (scripts/data/derive_campd_maxgen_outages."
                "py); frozen guards: declared-window scope clipped to the "
                "declared start/end, $150 DA in-merit certificate "
                "(region-scoped hubs, >= 2 window hours; sensitivity across "
                "[$120,$200] recomputed at derivation), capability = max "
                "gross in a ±45-day window centered on the event with "
                "best-event-hour credit (F3 dual-basis stability check), "
                "no control-day screen",
                root_cause="inside a declared, in-merit-certified window an "
                "available unit runs, so absence/reduction below the unit's "
                "own demonstrated capability is revealed unavailability — "
                "dispatch above the derate stays free (no outcome pinning, "
                "rules 1/11/13); re-derives only on a new CAMPD/declaration "
                "vintage (rule 23)",
            )
        )
    if sc.get("maxgen_emergency_tier_pricing"):
        # F5 declared-window ELMP emergency-tier pricing (miso-70 lane),
        # ZERO fitted scalars: the two $ floors are verbatim tariff/SOM
        # values and the windows/levels/regions are the maxgen-events
        # registry's rows (already ledgered above when M-2 is armed; this
        # entry carries the tier-floor schedule itself).
        out.append(
            _entry(
                "maxgen_emergency_tier_pricing (declared-window ELMP "
                "emergency-tier offer floors)",
                "reserve_config.MISO_EMERGENCY_TIER{1,2}_OFFER_FLOOR via "
                "data.maxgen_events.emergency_tier_slack_cost (load-slack "
                "repriced min(voll, floor) inside registry Warning+ windows, "
                "physical zones only; RBDC/zonal-ORDC curves never edited)",
                "measured-physical",
                iso,
                n_scalars=0,
                source="SOM-footnoted ELMP emergency pricing (2023 SOM fn.21 "
                "= 2024/2025 SOM fn.17): $500/MWh Tier-1 offer floor at Max "
                "Gen Warning, $1,000/MWh Tier-2 at Event Step 2; ladder "
                "scoping (Warning/Step-1 -> Tier 1, Step 2+ -> Tier 2, "
                "advisory/alert -> no pricing effect) from the 2023 SOM "
                "p.10-11 emergency-declaration ladder. Depth unbounded "
                "within the declared window — identified by the ladder's own "
                "declaration discipline (2023 SOM p.11: each level declared "
                "only when its MWs are needed), so the declared level is the "
                "measured depth indicator and no per-window MW bound exists "
                "to fit",
                root_cause="backcast-only availability-event family "
                "(rule 13): regenerates from each new declaration vintage; a "
                "forecast year carries no declared windows (the post-9/30/"
                "2025 ER25-579 regime is the forecast lane's charter)",
            )
        )
    if (
        iso in ("NYISO", "CAISO")
        or (iso == "MISO" and not sc.get("miso_seam_measured_ladder"))
        or (iso == "PJM" and not sc.get("pjm_seam_measured_ladder"))
    ):
        # CAISO carries the caiso-188 LIMB CENSUS instead of the generic text:
        # the single row covers four limbs with different identifications, and
        # a one-verdict-for-all row understates the keeper's own free
        # parameters (rule 21 [R-DOF]). Every other ISO's text is unchanged
        # (rule 25 [R-ISO-SCOPE] — a CAISO measurement fills no other ISO's
        # row).
        if iso == "CAISO":
            out.append(
                _entry(
                    "IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]",
                    "interchange_config.py CAISO seam supply-curve ladder",
                    "residual",
                    iso,
                    n_scalars=6,
                    source="FOUR LIMBS, measured on the keeper's own built "
                    "fleet by scripts/probes/_caiso188_import_tranche_census.py "
                    "(FINDING-caiso188-import-tranche-dof-2026-08-09.md §1-§3), "
                    "not asserted. CLOSED: (a) firm CAPACITY — PNW_hydro_base / "
                    "DSW_solar_PV at 1,072/1,558/1,566 and 1,251/1,813/1,805 MW, "
                    "measured per year from the DMM annual RA-import capacity x "
                    "the published branch-group MIC north/south split, two cited "
                    "primary sources; (b) spot PRICE — the per-hub injector "
                    "overwrites all four spot mc rows with their own measured "
                    "hub series hour by hour (measured as HOURLY on the built "
                    "fleet in all three years). LIVE AND FITTED, 6 scalars: "
                    "(c) firm PRICE — $28.00/$48.00, measured as CONSTANT mc "
                    "rows on the built fleet, identical in all three years; the "
                    "injector's firm_base branch deliberately skips them and "
                    "caiso-151's caiso_firm_import_selfsched_clip re-arms the "
                    "un-floored capability onto the margin at exactly these two "
                    "prices (0.969/4.634/5.705 TWh, FINDING-caiso150 §C/§F); "
                    "(d) spot CAPACITY — 1,800/1,800/2,200/3,000 = 8,800 MW, no "
                    "primary source anywhere. The spot depths are NOT the "
                    "operative corridor ceiling: the measured p95 deliverability "
                    "envelope is the tightest per-corridor bound in 25,866 of "
                    "26,280 corridor-hours (the ladder in 214, all north, all "
                    "2023-24), so their live roles are filling the band between "
                    "the firm + measured-clean depth and that envelope, and "
                    "placing the CARB-EF price breakpoints. EXPORT_TRANCHES"
                    "[CAISO] is NOT on this keeper's binding path at all — the "
                    "per-hub export legs are bounded by the published corridor "
                    "link ratings (COI 4,800 / Path-46 10,623 MW).",
                    root_cause="audit C-6/#1350, NARROWED by caiso-188 to the "
                    "two live limbs. No published object maps onto either: MIC "
                    "is an annual RA-showing allocation already spent twice in "
                    "this model (firm split + seam limit), so a third use would "
                    "be a rule 19 [R-ONE-MECH] double-count on a category "
                    "error; the path ratings map only to the ceiling role the "
                    "measured envelope already owns. The measured route is a "
                    "Q-Q revealed supply curve, whose PRICE side failed its "
                    "pre-registered LOYO gate at 30.5 % against a 25 % bar "
                    "(derive_caiso_import_tranches.py, caiso-83/86/86b, "
                    "DO-NOT-REDO) — and the CAPACITY side is the same estimator "
                    "with the axes swapped, so it must be derived and gated on "
                    "its own before anything is armed. Open root-cause issue, "
                    "never a value to re-fit (rule 20 [R-DOF]); " + _HOLDOUT_ROOT_CAUSE,
                )
            )
            return out
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
                "(scripts/data/derive_neiso_import_tranches.py); "
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


def _carry_hand_notes(ledger: dict, previous: dict | None) -> dict:
    """Carry a committed row's HAND-WRITTEN ``note`` onto its regenerated twin.

    caiso-236. Several rows' most load-bearing provenance is a ``note`` no
    generator writes — e.g. the CAISO ``offer_curve_by_group`` row carries the
    caiso-220/231 correction recording that five of its CAISO groups are now
    MEASURED, so the row's ``identification: "residual"`` overstates it. A blind
    regeneration silently DELETED that text, which is the ledger losing exactly
    the disclosure rule 21 ``[R-DOF]`` exists to preserve.

    Only rows that SURVIVE the rebuild keep their note, and only where the
    rebuild does not supply one of its own — a row the generator no longer emits
    is gone on purpose and its note goes with it.
    """
    if not previous:
        return ledger
    old_notes = {
        e.get("name"): e["note"] for e in previous.get("entries", []) if e.get("note")
    }
    for entry in ledger.get("entries", []):
        carried = old_notes.get(entry.get("name"))
        if carried and not entry.get("note"):
            entry["note"] = carried
    return ledger


def update_attestation(bundle: Path, iso: str, check: bool = False) -> bool:
    """Write (or verify) the ledger into the bundle's attestation.

    Returns True when the attestation already matched (check) / was written.
    """
    att_path = bundle / "calibration_attestation.json"
    att = json.loads(att_path.read_text()) if att_path.exists() else {}
    ledger = _carry_hand_notes(build_ledger(bundle, iso), att.get("free_parameters"))
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
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        from scripts.lib import keeper_store

        for run_id in keeper_store.keeper_list(REPO):
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
