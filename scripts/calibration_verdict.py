"""Reproducible calibration determination for an ISO backcast keeper.

Implements ``docs/calibration-determination-rubric.md`` (RUBRIC v2, the
2026-07-06 fitness-for-purpose re-anchor): reads a run's COMMITTED artifacts
only — the registry sidecar, the run payload, the per-(ISO, year) benchmark
parts, the committed actual-tail part (``tail/actual_tail.json``), the bundle
config, the bundle's calibration attestation, and the bundle's
legitimacy-diagnostics artifact (``legitimacy_diagnostics.json``, written by
``scripts/legitimacy_diagnostics.py --json-out``, whose D-2 forced-share
summary is scored as C8 and whose D-1 diurnal rows C8's grounded-above-budget
escalation reads; the C7 criterion that also scored D-1 was retired at v3.1) —
and emits a ``PASS`` / ``CAVEAT`` / ``FAIL`` per
criterion plus one overall determination in
``{CALIBRATED, CALIBRATED-WITH-CAVEATS, NOT-YET}``. Criteria are tiered
(load-bearing / supporting / protective) against the §0 statement of intended
use; graded load-bearing criteria are two-band scored (target band ->
commercial-grade band, each anchored to a published external benchmark —
``docs/rubric-v2-benchmark-memo-2026-07.md``). It never re-solves the LP and
never touches the gitignored ``dispatch``/``system`` parquets, so re-running it
on any keeper reproduces the verdict byte-for-byte.

The generation-mix criteria (C1/C2/C4) score the grid-delivered basis (grid LP
dispatch, no behind-the-meter CHP add-back) against EIA-923 minus the per-class
BTM host supply (``classFull``) and EIA-930 grid totals — model-grid vs
actual-grid, the same numbers the dashboard renders
(``scripts/render_calibration_html.py``). C5a (system CO2) is the exception
(rubric v2.3, owner amendment 2026-07-09): the eGRID/CAMPD rates anchoring the
actual count each cogen's FULL net generation (host + grid), so both sides of
the CO2 comparison carry the measured BTM CHP host supply added back — the
payload's ``co2`` blocks are already on that full-plant basis.

Stdlib-only (json, gzip, base64, re, math) so it runs anywhere the committed
artifacts are checked out, with no pandas / numpy / model import.

Usage:
    python scripts/calibration_verdict.py results/calibration/<name>
    python scripts/calibration_verdict.py --run-id <id>
    python scripts/calibration_verdict.py --json results/calibration/<name>
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))  # resolve `scripts.lib` when run as a plain script

from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.lib import benchmark_semantics as bs  # noqa: E402
from scripts.lib.backcast_artifacts import (  # noqa: E402
    decode_run_js as _decode_run_js,
    resolve_run_id,
)
from scripts.lib.bundle_io import bundle_meta  # noqa: E402  (stdlib-only helpers)

DATA_DIR = ba.DATA
REGISTRY_DIR = ba.REGISTRY
RUNS_DIR = ba.RUNS
BENCH_DIR = ba.BENCH
# Per-year EIA-923 completeness parts (scripts/audit_eia923_completeness.py): the
# committed source of truth for which (ISO, class) actuals are complete enough to
# gate in a preliminary-vintage year. Stdlib-readable so this scorer stays
# pandas/numpy-free.
COMPLETENESS_DIR = DATA_DIR / "completeness"

# Rubric version implemented by this scorer (rubric §0/§1/§9; v2 = the
# 2026-07-06 fitness-for-purpose re-anchor: criterion tiers, two-band
# target/commercial tolerances, DA-expressible C3c; v2.1 = the same-day owner
# amendments: C7/C8 materiality floor + C8 peaker cap 15%; v2.2 = the 2026-07-07
# owner amendment: C8 grounded-above-budget escalation — an over-cap class passes
# clean iff it clears D-4 provenance + D-1 shape, surfaced as a note; v2.3 = the
# 2026-07-09 owner amendments: C3a/C3b target bands set to the commercial values
# (±10% mean LMP / 0.20 NRMSE pass clean, no caveat band), and C5a re-based to
# the full-plant CHP-inclusive CO2 basis — the measured BTM CHP host supply is
# added back onto BOTH sides before the comparison, because the eGRID/CAMPD
# rates that anchor the actual count each cogen's full net generation;
# v2.4 = the 2026-07-09 owner amendment (second): C3a/C3b score on the
# LIKE-FOR-LIKE load-weighted actual (``rt_lw``/``da_lw`` bench fields —
# the committed hourly actual weighted by the same measured demand the
# model dispatches, zone-resolved where a zonal archive exists) instead of
# the legacy equal-hour hub mean. The legacy basis mixed a demand-weighted
# model mean with an equal-hour actual, a wedge that grows with tail
# realism — a byte-perfect ERCOT 2023 model scores +33.5% against its own
# actual on the old basis (docs/rubric-v24-price-basis-memo-2026-07.md,
# docs/handoffs/ercot-ordc-capdual-adder-2026-07.md §4). ISO-years without
# lw fields fall back to the legacy basis with an explicit label);
# v2.5 = the 2026-07-13 owner amendment: C2 gates ONLY fully-reported
# EIA-923 families — EIA-923 is the C2 source of truth, and a
# preliminary-vintage family (incomplete 923 booking, e.g. every ISO's
# 2025) is NOT gated against any fallback basis (the G-21b 930-derived
# family total or the CAISO CEMS anchor): those rows print as SKIPPED
# diagnostics and re-gate when the final vintage lands. Mirrors C1's
# incomplete-class skip — an incomplete benchmark can fabricate a miss in
# either direction, so it is evidence, not a gate;
# v2.6 = the 2026-07-16 owner amendments (session-logged, ERCOT-73 session):
# (a) C3c gates per-ISO on TAIL_BASIS — ERCOT moves to the RT hourly tail
# (the DA count becomes its report-only diagnostic; every other ISO stays
# DA-gated): ERCOT's DA tail runs ABOVE RT (2023: 311 vs 181 h) and the
# excess is the day-ahead forecast-risk premium, out of representation for
# a realized-weather backcast — see the TAIL_BASIS block comment; (b) C5c
# scores only OBSERVED months — the bench builder emits null (never 0.0)
# for months with no EIA-930 storage observation (pre-breakout months, e.g.
# ERCO battery before Oct-2024), and the existing null-month skip rule then
# holds the year out instead of correlating against fabricated zeros; (c)
# C5b + C5c are RETIRED to report-only for EVERY ISO (TIER_RETIRED): the
# storage numbers stay computed and printed on every keeper, but EIA-930
# storage-dispatch data is not yet reliable enough to be a calibration
# judgment — no PASS/FAIL, no ledger budget, no determination cap. Re-arming
# is a future owner decision;
# v2.7 = the 2026-07-16 owner amendments (second of the day, this session):
# (a) C3c gates on the ACTUAL RT scarcity tail for EVERY ISO — the RT hourly
# hub tail is the scarcity the market actually realized, and it is now the
# judged quantity everywhere (v2.6(a) had moved only ERCOT); the DA count
# becomes the report-only diagnostic row for every ISO (it embeds the
# day-ahead forecast-risk premium a realized-weather backcast is out of
# representation to price). The TAIL_BASIS per-ISO switch is gone — the
# basis is uniform again, now RT. (b) C5b + C5c are REMOVED from the rubric
# outright (v2.6(c) had retired them to report-only): storage-dispatch data
# is not reliable enough to participate in a calibration determination at
# any level, so the criteria no longer exist — not scored, not printed.
# The storage numbers remain visible on the dashboard run pages (payload/
# bench diagnostics, untouched); the pre-removal definitions live in the
# rubric doc's v2.6 history entry and git history. TIER_RETIRED leaves with
# them (it existed only for C5b/C5c);
# v2.8 = the 2026-07-27 coal gate-blindness correction (ERCOT-121 owner
# charter: "the fix ... is a scorer/gate correction that RE-SCORES every
# existing keeper in place"). Two distinct blind spots, both scorer-side so
# committed artifacts re-score without regeneration: (a) C8's materiality
# lookup resolved the D-2 summary's CAMPD plant-group vocabulary ("COAL")
# against the payload/bench scored-class split (COAL_LIGNITE/COAL_PRB/...),
# got 0.0 on both sides, and SKIPPED-immaterial the entire coal fleet of
# every coal ISO (ERCOT 13-14%, MISO 33-36%, PJM 14-16% of load) while the
# artifact's own load_share said material — _class_load_share now resolves
# plant-group aggregates via PLANT_GROUP_MEMBERS; (b) C7 gated only the
# artifact-baked ``gated`` rows (d1_gated_classes = peaker/intermediate), so
# a merchant-coal class pinned flat — the exact caiso-42 signature C7 exists
# to catch, e.g. ERCOT COAL_LIGNITE 2023 cv_ratio 0.294 — was reported and
# never scored. C7 now derives gatedness rubric-side (C7_GATED_CLASSES:
# peaker/intermediate + merchant coal) and evaluates each row's STORED
# metrics against the artifact's gates block, mirroring C8's
# measured-share-overrides-baked-verdict design (verified to reproduce every
# baked verdict on previously-gated rows across all six keepers).
# v2.9 (owner amendment 2026-07-27): C5a CO2 vs eGRID REMOVED from the scored
# rubric and demoted to REPORTED-ONLY. eGRID's latest released workbook is the
# 2024 vintage, so a 2025 C5a "actual" is the 2024 intensities standing in
# rather than a measurement — a criterion whose actual does not exist for a
# scored year cannot be load-bearing. Same grounds and same mechanism as the
# v2.7 C5b/C5c removal: score_co2 still runs and its number stays on the
# payload/dashboard, but "co2" is no longer in CRITERIA, so it contributes no
# status to the determination and consumes no caveat budget. See the CRITERIA
# comment for the year-scoped restoration path.
# v3.0 (owner amendment 2026-08-05, session-logged, ERCOT-2023-diagnosis
# session): a second LEDGERED caveat kind, ACCEPTED MODEL-CLASS LIMITATION
# (ledger entry `"kind": "model-class"`). It reclassifies a FAIL exactly like
# the measured-input kind and consumes the same non-protective ledgered budget
# (max 3), but is admissible ONLY for SUPPORTING-tier criteria — a model-class
# entry matching a load-bearing or protective criterion is IGNORED (the FAIL
# stands; fail-closed). Purpose: record an owner-accepted limitation of the
# model CLASS itself (e.g. C3c — an LP with competitive/measured offers cannot
# reproduce the equilibrium scarcity-hour offer conduct that formed the
# realized RT tail, and every mechanism family that reached the count
# fabricated scarcity elsewhere: ERCOT-95/97/102/107/108/155/159/161/162)
# after the root-cause program has EXHAUSTED the within-class mechanism space.
# Each entry must cite that exhaustion record and any still-open residual lane
# (the caveat documents a bound, it never closes root-causing — a later
# mechanism that fixes the criterion simply PASSes and the entry goes inert).
# Rubric §3 (v3.0) narrows the former "a collapsed price tail is never
# ledgerable" example accordingly: never ledgerable AS A MEASURED-INPUT claim,
# ledgerable as model-class only under this owner-signed, exhaustion-cited
# form.
# v3.1 (OWNER AMENDMENT 2026-08-06, session-logged in this session's directive)
# — TWO changes, both narrowing what a determination may excuse:
#   (a) LEDGERING IS NARROWED TO C3c ALONE (``LEDGERABLE_CRITERIA``). The owner's
#       determination is that C3c price tail / scarcity is the ONLY acceptable
#       ledgered caveat: it is the one criterion with no published commercial
#       comparable at all (see the C3c band note — "no commercial or public
#       model publishes tail-hour-count accuracy"), so a documented bound is the
#       honest reporting form for it. EVERY other criterion now stands or falls
#       on its own band, ledger entry or not — in particular C3a mean LMP, whose
#       band IS the certification claim: a mean-LMP miss beyond ±10% is a model
#       miss, and calling it an accepted limitation certified a price level the
#       model does not reproduce. Enforced in :func:`_apply_ledger` and
#       fail-closed: an entry for any other criterion is IGNORED and the FAIL
#       stands. Pre-existing entries are not deleted (they stay on their
#       bundles' attestations as the historical record) — they simply no longer
#       reclassify anything, so every affected keeper re-scores in place with no
#       re-solve. EFFECT AT AMENDMENT: CAISO 2026-08-06-caiso-175-tac-intake
#       CALIBRATED-WITH-CAVEATS -> NOT-YET (C3a 2024 +11.7% / 2025 +14.8%) and
#       MISO 2026-08-05-miso-132b-cc-committed NOT-YET (unchanged label; C3a
#       2025 -14.0% moves CAVEAT -> FAIL). NEISO/PJM/NYISO/ERCOT unchanged.
#   (b) C7 DIURNAL SHAPE IS RETIRED — dropped from the calibration report AND
#       the determination altogether, on the owner's stated condition that no
#       other commercial-grade model gates or publishes on it. That condition is
#       met on this rubric's OWN benchmark evidence: the v2 benchmark memo
#       (docs/rubric-v2-benchmark-memo-2026-07.md §, the comparables table) and
#       rubric §8's comparables row both record C6/C7/C8 as "beyond commercial
#       practice" with NO external anchor — every graded criterion here is
#       two-band scored against a published comparable, and C7 never had one.
#       Unlike C5a/C5b/C5c (removed but REPORTED_ONLY) this is a full removal
#       per rule 26 [R-DELETE]: ``score_shape`` and ``C7_GATED_CLASSES`` are
#       deleted, not zeroed, so the gate cannot be silently re-armed.
#       WHAT SURVIVES, DELIBERATELY: the D-1 diurnal rows stay in
#       ``legitimacy_diagnostics.json`` and C8 still reads them through
#       :func:`_d1_shape` — CLAUDE.md rule 20 [R-FORCED-BUDGET] makes an
#       over-budget class's conditional pass depend on its D-1 profile clearing
#       ``profile_r``/``cv_ratio``, so retiring the C7 GATE must not retire the
#       D-1 MEASUREMENT. The anti-flat-floor protection therefore still binds
#       exactly where rule 20 puts it: on classes that are actually being
#       forced. EFFECT AT AMENDMENT: C7 was PASS on CAISO/NYISO/PJM/ERCOT,
#       SKIPPED on NEISO and FAIL on MISO (COAL_PRB 2025) — so only MISO's
#       reported basis changes, and its NOT-YET label is unaffected because C3a
#       fails it independently under (a).
# v3.2 — 2026-08-09 owner amendment, session neiso-keeper-87-control, verbatim:
#       "make sure c3c is an acceptable caveat for any holdout or training
#       year". The C3c standing rule declared at v3.1-time for out-of-training
#       years only (`_apply_c3c_standing_rule`) now fires in EVERY year: a LONE
#       C3c failure with governance passing auto-ledgers to CALIBRATED-WITH-
#       CAVEATS on 2023-2025 exactly as it already did on 2020-2022/2019/2026.
#       NOT a loosening of the band: the scope split governed only whether the
#       justification had to be typed into an exceptions-ledger entry by hand —
#       in-sample the SAME reclassification was already reachable that way, and
#       is the route every current keeper carrying a C3c caveat used. The real
#       guard is untouched: LONE failure only, governance must pass, supporting
#       tier only (fail-closed), never CALIBRATED, and it still spends the one
#       ledgerable slot. [The "never CALIBRATED" clause of this v3.2 entry was
#       SUPERSEDED by v3.3 below, which is why the entry is left verbatim: it
#       is the genealogy, not the live rule. Every OTHER guard listed here
#       survives v3.3 intact.]
#       (b) A DEFECT IN THE LONE-FAILURE TEST IS FIXED IN THE SAME AMENDMENT,
#       and it was suppressing the rule as originally declared. "Lone" was
#       measured over EVERY record, including the REPORTED-ONLY streams the
#       rubric has demoted out of the determination -- C5a `co2`, removed at
#       v2.9. A `co2` FAIL therefore silenced the rule even though co2
#       contributes no status, no caveat budget and no reason line. It is now
#       measured over CRITERIA membership, i.e. the criteria that actually
#       constitute the determination. This under-fired out-of-training years
#       too, so (b) is a correction, not part of the widening.
#       EFFECT AT AMENDMENT, MEASURED over all 66 registered runs against a
#       pre-change snapshot rather than asserted: 2 determinations change, both
#       NYISO NON-KEEPER probes from the nyiso-130 `nyiso_li_tsl_n11_security`
#       pair (2026-08-06-nyiso-130-control and -n11-tsl, NOT-YET ->
#       CALIBRATED-WITH-CAVEATS; C3c FAIL -> CAVEAT, nothing else moves) and
#       both unlocked by (b) rather than by the widening. EVERY KEEPER OF ALL
#       SIX ISOs IS UNCHANGED: each either has no C3c failure at all, already
#       carries an explicit ledger entry for it, or fails a second criterion so
#       the lone-failure guard keeps the rule silent. PJM
#       2026-08-06-pjm-158-novirtual-disarmed is a lone C3c failure and still
#       does NOT reclassify -- its C6 is UNATTESTED, which is the governance
#       guard working.
# v3.3 — 2026-08-17 owner amendment, session nyiso-calibration-declaration,
#       verbatim: "NYISO should be declared calibrated. C3c is an acceptable
#       miss and shouldn't change a declaration from calibrated to calibrated
#       with caveats because it's a known model limitation that's been
#       ledgered". A LEDGERED caveat no longer DOWNGRADES the determination.
#       Since v3.1 ledgering is restricted to C3c alone (LEDGERABLE_CRITERIA),
#       so this is exactly and only the owner's rule: an accepted, ledgered
#       C3c price-tail limitation is REPORTED but is not the thing that turns
#       CALIBRATED into CALIBRATED-WITH-CAVEATS. This supersedes the v3.0-v3.2
#       clause "IT IS NOT A PASS ... the run reads CALIBRATED-WITH-CAVEATS,
#       never CALIBRATED" — that clause is withdrawn by the owner, and the
#       CLAUDE.md rule 22 C3c standing rule's guard (d) is amended in step.
#       WHAT IS NOT LOOSENED, and why this is a reporting change rather than a
#       band change:
#         - The C3c BAND, TIER and REPORTED MAGNITUDE are untouched. The miss
#           is still measured and printed at full size, still listed in
#           `caveats.ledgered`, still counted in `grade_summary.ledgered`, and
#           still named on the determination basis of a CALIBRATED run. The
#           ledger entry (or the standing rule's auto-entry) is still required.
#         - It is still NOT A PASS at the criterion level: C3c reads CAVEAT,
#           never PASS, so `grade_summary.target_grade` does not absorb it and
#           a reader can always see the model missed the tail.
#         - EVERY OTHER ROUTE TO A CAVEAT STILL DOWNGRADES: commercial-band
#           target misses, protective-gate (C6/C8) caveats, unscored criteria
#           and data-blocked years are untouched. So a run reads CALIBRATED
#           only when C3c is the SINGLE blemish on it.
#         - The FAIL path is untouched: a C3c failure that is not ledgerable —
#           because a second criterion also fails, or governance does not pass
#           — still stands as a FAIL and still carries the run to NOT-YET
#           (`_apply_c3c_standing_rule`'s lone-failure and governance guards).
#         - The budgets are untouched: >1 ledgered or >0 protective caveats is
#           still NOT-YET, checked BEFORE this branch is reached.
#       EFFECT AT AMENDMENT, MEASURED over all 26 registered runs against a
#       pre-change snapshot rather than asserted: SIX determinations change,
#       all CALIBRATED-WITH-CAVEATS -> CALIBRATED, and all six are the same
#       shape (lone ledgered C3c, zero band caveats, zero protective caveats,
#       nothing skipped, nothing data-blocked). TWO ARE KEEPERS —
#       NYISO 2026-08-16-nyiso-140-layup-exclusion (the ISO this amendment was
#       requested for) and NEISO 2026-08-17-neiso-99-joint-p1 (an unavoidable
#       cross-ISO consequence: the scorer is ONE instrument and an ISO-scoped
#       verdict rule would be an off-registry tuning channel in spirit, rules
#       24 [R-REGISTRY] / 25 [R-ISO-SCOPE]). The other four are non-keepers:
#       NYISO 2026-08-08-nyiso-133-cod-arm and 2026-08-17-nyiso-142-stackdup,
#       NEISO 2026-08-17-neiso-97-dstrepair and 2026-08-06-neiso-2022-
#       corrected-basis. NO run changes in either direction beyond those six;
#       no NOT-YET is reclassified, and CAISO/ERCOT/MISO/PJM are UNCHANGED
#       (each keeper either fails a criterion outright or carries no ledgered
#       C3c). NO SOLVE RAN — this is a scorer-side reclassification on the
#       committed artifacts, so every keeper re-scores in place.
# v3.4 — 2026-08-18 owner amendment, session caiso-c1-lmp-pricing, verbatim:
#       "Ccgt is fine at -1.8% for passing c1 gate ... I want ... a shift that
#       declares c1 for 2023 calibrated". THE C1 VOLUME BAND IS FLOORED AT THE
#       SHARE LEG'S OWN MATERIALITY SCALE:
#           vol_band = min(max(2.0% of ISO load, 3.0% of ACTUAL total
#                              generation), 8 TWh)
#       (:func:`_fuelmix_vol_band`). NO NEW CONSTANT: the floor is
#       FUELMIX_SHARE_PP (3.0) applied to the actual-side generation total —
#       the same ±3.0-pp-of-mix materiality the share leg already declares.
#       WHY THIS IS A COHERENCE REPAIR AND NOT A RESIDUAL FIT: C1's two legs
#       state one standard (a class may not misrepresent the mix by more than
#       3.0 pp) plus an absolute drift bound. But on a deep net-importing ISO
#       the 2%-of-load volume leg could bind TIGHTER than the declared 3.0-pp
#       mix standard on the SAME class — CAISO 2023: 2% of 207 TWh load =
#       ±4.15 TWh vs 3% of 176 TWh actual generation = ±5.27 TWh — failing a
#       class whose miss the rubric's own materiality standard calls fine
#       (CC_REGULAR −4.24 TWh = −2.4% of actual generation, share −1.8 pp).
#       The floor makes the volume leg bottom out at that same declared scale,
#       measured in raw |model−actual| TWh over the ACTUAL generation
#       denominator — deliberately NOT the model-vs-actual share_pp, which a
#       system-total shrink (e.g. over-import displacing the class) flatters:
#       the same CC row reads −1.8 pp on share but −2.4 pp of actual gen, and
#       the floor gates on the un-flatterable −2.4. WHAT IS UNCHANGED: the
#       8 TWh cap still tops the band (a big-ISO class can never buy more than
#       8 TWh of drift: PJM/MISO-scale bands are bit-identical, cap binds
#       either way), the ±3.0 pp share leg still binds independently (MISO
#       CC_REGULAR +47 TWh / +7.7 pp still fails BOTH legs), and the 2%-of-
#       load term still governs wherever it is the wider one. The floor
#       binds — i.e. the band moves at all — only where actual generation
#       > (2/3) × load, and widens mid-size-ISO bands by at most the
#       load-vs-gen basis gap. Doc: docs/calibration-determination-rubric.md
#       §C1 (amendment note), mirrored to the dashboard via
#       scripts/lib/rubric_consts.py (fuelmixVolGenFloorFrac) and
#       docs/codebase-site/js/backcast-runs.js volInTol.
#       EFFECT AT AMENDMENT, MEASURED over all 26 registered runs against a
#       pre-change snapshot rather than asserted: exactly ONE row flips —
#       CAISO keeper 2026-08-17-caiso-200-h1-memberpanel C1 2023 CC_REGULAR
#       FAIL -> PASS (|−4.244| ≤ 5.272; the run's C1 criterion goes FAIL ->
#       PASS, its determination stays NOT-YET on the standing C3a mean-LMP
#       miss, +12.8/+15.7% in 2024/2025). NO OTHER RECORD of any run of any
#       ISO changes status, and no determination label changes anywhere.
#       NO SOLVE RAN — scorer-side only; every keeper re-scores in place.
RUBRIC_VERSION = 3.4

# Statuses (per criterion-year and aggregated).
PASS, CAVEAT, FAIL, SKIPPED = "PASS", "CAVEAT", "FAIL", "SKIPPED"
# Failure classifications (rubric §1). A CAVEAT is one of:
#  - MEASURED_LIMIT: an out-of-tolerance criterion reclassified by an explicit
#    exceptions-ledger entry (the actual is the limitation) — BUDGETED, and
#    since v3.3 REPORTED-BUT-NOT-DOWNGRADING (it can only be C3c).
#  - COMMERCIAL_BAND: inside the evidence-anchored commercial-grade outer band
#    but outside our stricter target band — auto-recorded, listed, NOT budgeted
#    (the certification claim of CALIBRATED-WITH-CAVEATS is exactly
#    "commercial-grade or better on every load-bearing criterion").
MODEL_MISS = "MODEL MISS"
MEASURED_LIMIT = "ACCEPTED MEASURED-INPUT LIMITATION"
# v3.0: owner-accepted limitation of the model class itself (ledger entry
# kind "model-class"); supporting-tier criteria only, same ledgered budget.
MODEL_LIMIT = "ACCEPTED MODEL-CLASS LIMITATION"
COMMERCIAL_BAND = "WITHIN COMMERCIAL BAND (TARGET MISS)"
# Overall determinations.
CALIBRATED = "CALIBRATED"
CALIBRATED_CAVEATS = "CALIBRATED-WITH-CAVEATS"
NOT_YET = "NOT-YET"

# Criterion tiers (rubric §0 statement of intended use → §1 triage):
#  - load-bearing: certifies the intended uses directly (annual/monthly price
#    level & shape, generation mix by class, system CO2). Two-band scored where
#    a published commercial comparable exists.
#  - supporting: informative sub-annual dynamics (hourly correlation, storage
#    cycling, scarcity-tail counts) — single wide band; a gross breach still
#    FAILs, a documented data limitation may be ledgered.
#  - protective: the anti-self-deception gates (C6 governance, C8 forced
#    share; C7 diurnal shape until its v3.1 retirement). v1 logic and
#    thresholds, and since v3.1 NO protective criterion is ledgerable at all —
#    stricter than v1's budget of 1 (CLAUDE.md rules 13/14/17-22).
TIER_LOAD, TIER_SUPPORT, TIER_PROTECT = "load-bearing", "supporting", "protective"
# Tier of a criterion that was removed from the rubric but is still computed and
# displayed (REPORTED_ONLY below). It never gates and never budgets a caveat.
TIER_REPORT = "reported-only"
# (v2.6(c) briefly held C5b/C5c in a TIER_RETIRED report-only tier; v2.7
# removed the two criteria from the rubric outright, and the tier with them.)

# --- fuel-family class membership (plant_taxonomy.classes_for_fuel930 roll-up) --
GAS_CLASSES = bs.GAS_CLASSES
# Same membership as bs.COAL_CLASSES, but this scorer emits its per-class records
# in COAL_CLASSES iteration order, so the historical record ORDER is frozen here
# for verdict byte-parity (bs is the taxonomy roll-up order, which differs). The
# set is drift-guarded against the taxonomy via bs (tests/test_benchmark_semantics).
COAL_CLASSES = ("COAL_PRB", "COAL_LIGNITE", "COAL_BIT", "COAL_WC", "COAL")
# Classes excluded from the per-class fuel-mix gate (C1), each justified in the
# rubric: CT_CHP is a BTM peaker the grid LP zeroes by construction; OTHER /
# OTHER_FOSSIL are the mixed-plant reconciliation bucket, not merit-order classes.
FUELMIX_EXCLUDED = frozenset({"CT_CHP", "OTHER", "OTHER_FOSSIL"})

# --- tolerances (rubric §1) -------------------------------------------------
# C1 fuel-mix — the universal class gate (mirrors classInTol in the run
# explorer, docs/codebase-site/backcast-runs.html; supersedes the old ±5%/±1 TWh
# size-tiered band): a class passes iff BOTH (a) its grid-delivered volume miss
# |model−actual| is within min(max(2.0% of ISO total load, 3.0% of actual total
# generation), 8 TWh) — the gen-floor added by the v3.4 owner amendment
# 2026-08-18, see the RUBRIC_VERSION entry — AND (b) its share of total
# generation is within 3.0 percentage points of the actual share.
# The volume band scales with system size (≈2 pp of load, floored at the share
# leg's own ±3.0-pp-of-mix materiality on the actual-generation basis) but is
# capped at an absolute 8 TWh so it can't balloon on large ISOs (2% of an
# 800 TWh system would be 16 TWh, letting a small class drift far on the
# margin). Applied uniformly across classes and ISOs; the share band stops a
# class passing on volume alone while still misrepresenting the mix. Using
# total LOAD (= gen + net imports) rather than generation so net-importing
# ISOs get the correct ≈2 pp band; for energy-only ISOs with no interchange,
# load = gen and (since gen > (2/3)·load trivially holds there) the 3%-of-gen
# floor is the binding percent term.
# 2026-07-02 rubric re-balance (docs/calibration-determination-rubric.md §1):
# loosened from 1.0%/5 TWh/1.5 pp — the old bands failed keepers on ±1–2 TWh
# small-class residuals that are TWh noise, not a structural miss, while a
# genuine structural miss (e.g. MISO CC_REGULAR +47 TWh / +7.7 pp) still FAILs
# the new bands by a wide margin. Paired with a TIGHTER C3 (price) gate below.
FUELMIX_VOL_LOAD_FRAC = 0.02  # volume band = 2.0% of ISO total load ...
# ... floored at FUELMIX_SHARE_PP% of ACTUAL total generation (v3.4: the share
# leg's declared mix-materiality applied to the un-flatterable actual-side
# denominator; no new constant — see _fuelmix_vol_band) ...
FUELMIX_VOL_CAP_TWH = 8.0  # ... but never more than an absolute 8 TWh
FUELMIX_SHARE_PP = 3.0  # +/-3.0 share percentage points of total generation
# Non-fossil fuels whose grid actual comes from EIA-930 (not 923) for the
# system-total used by the share/volume bands (matches totalGen in the run
# explorer, docs/codebase-site/backcast-runs.html).
NONFOSSIL_FUELS = ("nuclear", "wind", "solar")

# D-10 free-class rescore (audit §7 D-10 / §4 L-rows): the per-ISO set of C1
# classes whose actual is a MEASURED REALIZATION the model is pinned to — so a C1
# pass there scores plumbing, not skill. Declared from the audit L-rows, not
# inferred (mirrors the D-5 overlay registry pattern):
#   L1 wind/solar (delivered-CF upper bound), L3 nuclear (measured monthly CF),
#   L6 hydro (monthly budgets) + MISO Manitoba firm imports, L4 CHP (measured
#   export floor), L2 NYISO net imports (measured reconciliation band).
# C1 only scores the fossil gas/coal families, so in practice the free-class
# rescore drops the CHP subclasses (CC_CHP / ST_CHP; CT_CHP is already
# C1-excluded); wind/solar/nuclear/hydro/imports are declared for provenance and
# excluded harmlessly (they are never C1 rows). No gate — the number itself is
# the deliverable (the audit's "pinned-class gate inflation" made visible).
_PINNED_CLASSES_COMMON = frozenset(
    {"wind", "solar", "nuclear", "hydro", "CC_CHP", "CT_CHP", "ST_CHP"}
)
PINNED_CLASSES_BY_ISO: dict[str, frozenset[str]] = {
    "ERCOT": _PINNED_CLASSES_COMMON,
    "CAISO": _PINNED_CLASSES_COMMON,
    "PJM": _PINNED_CLASSES_COMMON,
    "MISO": _PINNED_CLASSES_COMMON | {"imports"},  # L6 Manitoba firm-hydro block
    "NYISO": _PINNED_CLASSES_COMMON | {"imports"},  # L2 net-interchange band
    "NEISO": _PINNED_CLASSES_COMMON,
}

SYSVOL_TOL = 0.025  # +/-2.5% gas/coal family grid-delivered (target band)
# Commercial-grade outer band for the preliminary-vintage EIA-930 family
# fallback (the only C2 path that applies a percent band): family-level
# generation-by-fuel error of ~5% is the best published comparable (EIA AEO
# retrospective short-horizon generation-by-fuel; ISO planning-study PCM
# benchmarks) and the fallback's own benchmark carries the 923-vs-930
# reconciliation uncertainty. Between 2.5% and 5% -> auto CAVEAT
# (COMMERCIAL_BAND); beyond 5% -> FAIL (ledgerable as before).
SYSVOL_COMMERCIAL = 0.05
SYSVOL_MIN_TWH = 10.0  # below this a family is immaterial: C1's per-class
# absolute band governs it, so the ±2.5% system-volume gate is N/A (e.g. NEISO
# coal ~0.3 TWh — a percent band on a near-zero family is pure noise).
DISP_MIN_TWH = 5.0  # below this a fleet's hourly r/NRMSE is degenerate (NEISO
# coal); the per-class C1 absolute band is the meaningful check, not correlation.
VINTAGE_RECONCILE_FRAC = (
    bs.VINTAGE_RECONCILE_FRAC
)  # render_calibration_html._VINTAGE_RECONCILE_FRAC
# ISOs whose EIA-930 "Natural Gas" cell is demonstrably corrupted against two
# independent measured sources, with the CEMS-anchored replacement committed in
# the bench part by render_calibration_html (owner-signed rework 2026-07-12;
# results/calibration/FINDING-caiso-c2c4-bench-basis-930ng-2026-07-12.md §5).
# CAISO: from ~2024-05 the CISO NG cell carries a growing noon-peaked,
# solar-shaped block no gas fleet produced (+4.2/+7.9 TWh unexplained in
# 2024/25 vs CEMS + cogens + fold-in). Effects here:
#  * C2 gas family fallback gates against the committed anchor fields
#    (``e930.gas_cems_grid`` + ``e930.gas_cogen_grid``) instead of the 930 cell.
#  * C4 gas hourly r/NRMSE is recomputed from the committed hourly series
#    (payload ``plants[].m`` vs bench ``plants[].campd`` + flat cogen block)
#    from the onset VINTAGE onward; pre-onset years keep the payload's 930-based
#    fit. The CAISO onset moved 2024 -> 2023 (owner ruling 2026-07-26,
#    caiso-121): the original "pre-onset years agree" premise is false for 2023,
#    where the deflated 930 cell reads +10.5% over EIA-923 and +8.0% over
#    CEMS+cogen (which agree within 2.3%) — see benchmark_semantics
#    .EIA930_NG_CORRUPT_ONSET for the three-source level test.
# Mirrors render_calibration_html.EIA930_NG_CELL_CORRUPT / _ONSET; membership
# is CEMS-evidence-gated per ISO, never generic (the other ISOs' NG cells show
# no corruption and keep G-21/G-21b unchanged).
CEMS_GAS_ANCHOR_ISOS: frozenset = bs.EIA930_NG_CELL_CORRUPT
CEMS_GAS_ANCHOR_ONSET = bs.EIA930_NG_CORRUPT_ONSET  # first contaminated vintage year
PRELIM_923_FROM_YEAR = 2025  # current-year preliminary EIA-923 vintage
# C3 price gates — rubric v2 two-band (2026-07-06 fitness re-anchor), target
# bands re-set by the 2026-07-09 owner amendment (rubric v2.3): the target
# band now COINCIDES with the evidence-anchored commercial-grade band
# (docs/rubric-v2-benchmark-memo-2026-07.md §2), so a run inside ±10% mean /
# 0.20 NRMSE is a clean PASS with no COMMERCIAL_BAND caveat; beyond it ->
# FAIL (ledgerable only as a measured-input limitation). The former stricter
# targets (±5% / 0.15 — the SEM regulator criterion) remain as reported
# magnitudes, not gates: the primary market signal is still price, but a
# caveat between the SEM criterion and the published commercial envelope
# graded honest runs as second-class for a miss no published model avoids.
#   Mean anchor: the SEM/Ireland regulator criterion for its official PLEXOS
#   model is +/-5% aggregate price error with monthly within +/-10% (ECA,
#   SEM-20-004); NYISO's accepted GE MAPS benchmark ran -2% to -17% zonal
#   (Outlook Appendix A); monitors' competitive re-simulations sit 0-4% from
#   actual prices (CAISO DMM / MISO SOM), the market-conduct noise floor.
PRICE_MEAN_TOL = 0.10  # PASS: +/-10% mean LMP (v2.3 owner amendment 2026-07-09)
PRICE_MEAN_COMMERCIAL = 0.10  # coincident outer band (memo §2)
#   Shape anchor: SEM's regulator-accepted backcast carried -9% winter-peak /
#   +11% off-peak period biases; published monthly norms run ~5-15% with
#   correct seasonality. A 12-month NRMSE of 0.20 is the outer edge of that
#   demonstrated band (also the pre-2026-07-02 value, now externally anchored).
PRICE_SHAPE_NRMSE_MAX = 0.20  # PASS: monthly NRMSE (v2.3 owner amendment)
PRICE_SHAPE_NRMSE_COMMERCIAL = 0.20  # coincident outer band (memo §2)
# C3c scarcity tail — scores the hourly tail (rubric §1 C3c, §5) from the
# committed actual-tail part (frontend/data/backcast/tail/actual_tail.json,
# scripts/data/derive_actual_tail.py). The gated basis is the ACTUAL RT scarcity
# tail for EVERY ISO (rubric v2.7 owner amendment 2026-07-16): the RT hourly
# hub tail is the scarcity the market actually realized — the judged
# quantity. The DA count is always emitted as the report-only diagnostic
# row: it prices scarcity *expectations*, and its wedge over RT is the
# day-ahead weather/load forecast-risk premium a realized-weather
# (perfect-foresight) backcast is out of representation to price (ERCOT
# 2023: DA 311 h vs RT 181 h). History: v2 gated the DA-expressible tail on
# the sub-hourly-transient argument (miso-scarcity-tail-diagnosis.md §1);
# v2.6(a) moved ERCOT to RT; v2.7 makes RT the uniform judged basis — both
# counts are hourly hub averages, and the owner's determination is that the
# tail criterion judges realized scarcity, not the DA market's forecast of
# it. Sub-hourly transients that push an hourly RT average over the
# threshold are part of that realized scarcity and now gate.
# Band [0.5x, 2x]: no commercial or public model publishes tail-hour-count
# accuracy at all, so the band's job is order-of-magnitude realism — a
# collapsed tail (0x) and an invented tail (>2x) both still FAIL. Counts
# below TAIL_SMALL_COUNT hours are scored by absolute difference (a ratio on
# a handful of hours is degenerate).
TAIL_LO, TAIL_HI = 0.5, 2.0  # tail hours within [0.5x, 2x] of the RT actual
TAIL_SMALL_COUNT = 10  # below this, |model-actual| <= TAIL_SMALL_COUNT passes
DISP_R_FLOOR = 0.70  # fleet hourly pearson r floor (gas, coal)
DISP_NRMSE_MAX = 0.30  # fleet hourly NRMSE ceiling (gas, coal)
CO2_TOL = 0.07  # target: +/-7% vs eGRID (mid of the playbook's 5-10%)
# Commercial-grade outer band for system CO2: ~10% is the demonstrated
# public-model grade at short horizons (AEO retrospective energy-CO2 errors;
# eGRID-vs-model comparisons in academic PCM validations — memo §2).
CO2_COMMERCIAL = 0.10
# (C5b/C5c storage tolerances removed with the criteria — rubric v2.7.)
VRE_TOL = 0.10  # +/-10% advisory band for solar/wind (report-only)

# Per-ISO scarcity-tail definition (rubric §5): (threshold $/MWh).
TAIL_THRESHOLD = {
    "ERCOT": 200.0,
    "PJM": 200.0,
    "MISO": 200.0,
    "CAISO": 200.0,
    "NYISO": 300.0,
    "NEISO": 300.0,
}

# Governance: outage sources that are exogenous availability events (rubric C6.4).
EXOGENOUS_OUTAGE_SOURCES = frozenset({"historic", "statistical"})
# scenario_config flags that, if truthy, indicate a forbidden fitted mechanism
# (output-pinning / price-residual adder). Curated by exact name to avoid false
# positives on legitimate structural terms (e.g. wefor_residual, a renewable
# forecast-error term). Empty today; extend as such a flag is ever introduced.
FORBIDDEN_FLAGS: tuple[str, ...] = ()

# Caveat budgets / quorum (rubric §2, v2). Two DISTINCT caveat kinds:
#  - Auto COMMERCIAL_BAND caveats (inside the evidence-anchored outer band,
#    outside target): UNBUDGETED — they are inside the certification claim by
#    construction; the scorer lists every one with its magnitude.
#  - LEDGERED caveats (beyond the outer band, reclassified by an explicit
#    exceptions-ledger entry as an accepted measured-input limitation):
#    budgeted. THE BUDGET NUMBERS BELOW ARE v3.1's (protective 0, ledgered 1)
#    and are derived from LEDGERABLE_CRITERIA, not set independently; the v2
#    rationale that follows is retained for genealogy. Under v2 the protective
#    criteria (C7/C8) kept the v1 hard budget of 1 and non-protective ledgered
#    caveats were capped at 3. v2 rationale (memo §3a, replacing the 2026-07-02
#    3->2 cut whose stated concern — price caveated wholesale — is now
#    structurally addressed by the commercial outer band): the recurring
#    documented data-limitation classes are three by construction
#    (preliminary-923 vintage, EIA-930 storage coverage, data-blocked scarcity
#    requirement series), and a budget of 2 mechanically forced NOT-YET on data
#    availability rather than model quality. Each ledgered caveat still
#    requires its own named measured-input reason — the budget bounds excuses,
#    it never grants them.
# v3.1 (owner amendment 2026-08-06) collapses BOTH budgets, because ledgering
# is now restricted to C3c alone (LEDGERABLE_CRITERIA below) and C3c is a
# single SUPPORTING-tier criterion:
#  - protective -> 0: no protective criterion is ledgerable any more, so a C8
#    forced-share FAIL is NOT-YET, full stop (C6 was never caveatable). This
#    HARDENS the anti-self-deception tier — the v1/v2 budget of 1 let one
#    protective gate be excused.
#  - ledgered -> 1: exactly one ledgerable criterion exists, and caveats
#    aggregate per criterion, so 1 is the true ceiling. Publishing "0/3" would
#    advertise slots that cannot be filled.
# Both checks are retained as defense-in-depth invariants rather than deleted:
# they are the assertion that re-widening LEDGERABLE_CRITERIA without an owner
# amendment cannot silently buy back excuse capacity.
# v3.3 (owner amendment 2026-08-17) does NOT touch either budget — it is
# checked BEFORE the v3.3 branch, so >1 ledgered or >0 protective caveats is
# still NOT-YET. What v3.3 changes is only what a WITHIN-budget ledgered
# caveat costs the overall determination: nothing. This is why the ledgered
# budget staying at exactly 1 matters more after v3.3, not less — it is now
# the sole numeric bound on how much can be carried without a downgrade.
MAX_PROTECTIVE_CAVEATS = 0  # C6/C8 — no protective criterion is ledgerable (v3.1)
MAX_LEDGERED_CAVEATS = 1  # C3c is the only ledgerable criterion (v3.1)

# Criteria a ledger entry may reclassify at all (rubric v3.1, OWNER AMENDMENT
# 2026-08-06). C3c price tail / scarcity is the ONLY one: it is the single
# criterion with no published commercial comparable (see PRICE_TAIL_BAND below
# — "no commercial or public model publishes tail-hour-count accuracy at all"),
# so an owner-accepted documented bound is the honest reporting form for it.
# Every other criterion is two-band scored against a published comparable, and
# for those the band IS the certification claim — C3a mean LMP most of all: a
# mean-LMP miss beyond ±10% is a MODEL MISS, and ledgering it certified a price
# level the model does not reproduce. The budget above still applies on top
# (a criterion being ledgerABLE never means ledgering is free).
LEDGERABLE_CRITERIA = frozenset({"price_tail"})

# C8 materiality floor (rubric v2.1, owner amendment 2026-07-06; scoped to C8
# alone since C7's v3.1 retirement): the protective forced-share gate — and the
# D-1 shape leg of its grounded-above-budget escalation — scores only classes
# whose annual energy
# — max(model, actual), so a forced floor cannot hide a class below the line
# by its own inflation, and a model that zeroes a material class stays scored
# — is at least this fraction of total ISO load. Smaller classes are emitted
# SKIPPED-immaterial (reported by the D-1/D-2 diagnostics, never gated): a
# trivial class's diurnal r or forced share is not worth structural work
# (mirrors C2's 10 TWh / C4's 5 TWh immateriality cut-offs). 2% is the clean
# cut in the keeper data: NEISO ST_GAS 0.1-0.3%, NEISO CT 0.5-0.7% and NYISO
# CT 1.4-1.9% of load (the named trivial cases) fall below it, while CAISO CT
# 2023/24 (2.1-2.3% — the caiso-42 flat-floor case C8 exists to catch),
# PJM/MISO CT (3.5-4.2%) and every material ST_GAS (2.1-10.6%) stay gated.
# Any change to this floor — or to the D-1 thresholds C8's grounded-pass
# escalation reads — is an owner amendment: date and attribute it AT the point
# of change, not afterwards.
PROTECTIVE_MIN_LOAD_FRAC = 0.02
# (The rubric-side C7 gate set ``C7_GATED_CLASSES`` was DELETED by the v3.1
# owner amendment 2026-08-06 along with ``score_shape`` — C7 is retired, and
# rule 26 [R-DELETE] says a retired gate is removed, not zeroed, so it cannot
# be silently re-armed. The D-1 rows it read still exist in
# legitimacy_diagnostics.json and are still scored by C8's grounded-above-budget
# escalation via :func:`_d1_shape`, which applies the artifact's own
# ``d1_min_profile_r``/``d1_min_cv_ratio`` gates to whichever class is actually
# over its forced-energy budget — a wider test than a fixed class tuple, and
# the one CLAUDE.md rule 20 [R-FORCED-BUDGET] actually requires.)
# D-2 rows/summary label classes by CAMPD plant_group (the floor-attribution
# vocabulary: coal plants are "COAL"), while the run payload's gmModel and
# the bench classFull carry the scored-class rank split. _class_load_share
# bridges the aggregate to its members (mirrors
# config/plant_taxonomy.COAL_SUPPLY_TO_CLASS values + the bare-COAL parent;
# kept literal here because this scorer is deliberately stdlib-only). Without
# the bridge the C8 materiality lookup read 0.0 TWh on both sides for "COAL"
# and skipped the whole coal fleet as immaterial (v2.8).
PLANT_GROUP_MEMBERS = {
    "COAL": ("COAL_LIGNITE", "COAL_PRB", "COAL_BIT", "COAL_WC"),
}
# C8 forced-share caps (rubric v2.1): the peaker cap was raised 0.10 -> 0.15
# by the same owner amendment (CLAUDE.md rule 20 amended in-place); merchant
# cap unchanged. The scorer derives PASS/FAIL from the artifact's MEASURED
# forced_share against these caps — the rubric owns tolerances, the S1
# artifact owns measurement — so committed artifacts written under earlier
# gate values keep scoring correctly without regeneration.
FORCED_SHARE_PEAKER_MAX = 0.15
FORCED_SHARE_MERCHANT_MAX = 0.30
FORCED_SHARE_PEAKER_CLASSES = ("CT_PEAKER",)

# C8 grounded-above-budget escalation (rubric v2.2, owner amendment 2026-07-07).
# The 15%/30% caps and the 2% materiality floor are UNCHANGED — a class within
# the cap still passes cheaply on volume alone. What changes is the treatment of
# a class ABOVE the cap: instead of an automatic FAIL, it escalates to a
# conditional pass on PROVENANCE + SHAPE (the true legitimacy question), because
# a class can legitimately be forced past the budget when the forcing is a real
# grid/RA/AS driver that reproduces the observed dispatch. A class above the cap
# passes iff BOTH:
#   (a) PROVENANCE — every binding *non-exempt* mechanism it is forced by clears
#       D-4 off-window binding (it binds only in its driver-justified window;
#       a mechanism with NO declared D-4 window fails here — rule 12, "no floor
#       without a window"), AND
#   (b) SHAPE — the class's D-1 hour-of-day profile clears the artifact's own
#       gates (profile r >= d1_min_profile_r AND off-peak CV ratio >=
#       d1_min_cv_ratio), applied to ANY escalating class (not only the default
#       D1_GATED_CLASSES) — this is the "shape mismatch means the forcing
#       variables are wrong" test.
# Both signals are already in every committed legitimacy_diagnostics.json
# (D1.rows / D2.rows / D4.rows / gates), so this stays scorer-only — no
# re-solve, no bundle regen — and existing keepers re-score in place. A pass
# here is a CLEAN PASS (owner decision 2026-07-07: surfaced as a report NOTE,
# never a caveat); a fail is classified as a forcing shape/provenance mismatch.
GROUNDED_ABOVE_BUDGET = "GROUNDED ABOVE BUDGET (D-4 window + D-1 shape clear)"
# Mechanism NAMES excluded from the C8 forced-share arithmetic — the union of
# data.floor_mechanisms.D2_EXEMPT_MECHS (structural must-run: nuclear / CHP-steam
# / coal take-or-pay) and NON_THERMAL_MECHS (interchange pseudo-unit boundaries).
# Kept as a local literal so this scorer stays stdlib-only (no market_sim import);
# floor_mechanisms is the source of truth and tests/test_calibration_verdict.py
# asserts this set matches MECH_NAMES for those id sets so it cannot silently
# drift. run_d2 already excludes these from a class's gated forced_share; the
# escalation re-derives the binding *merchant* mechanism set from the same names.
FORCED_EXEMPT_MECH_NAMES = frozenset(
    {
        "nuclear_mustrun",  # MECH_NUCLEAR
        "chp_steam",  # MECH_CHP_STEAM
        "coal_mustrun",  # MECH_COAL_MUSTRUN
        "firm_import",  # MECH_FIRM_IMPORT (non-thermal boundary)
        "nyiso_local_selfsupply",  # MECH_NYISO_SELFSUPPLY (non-thermal boundary)
        "hydro_min_flow",  # MECH_HYDRO_MIN_FLOW (non-thermal boundary)
        "hydro_ror_flat",  # MECH_HYDRO_ROR_FLAT (non-thermal boundary)
    }
)

# Criterion id -> (label, tier). The v1 HARD/SOFT split conflated two things —
# strict data gates (C1/C2) and anti-gaming gates (C6/C7/C8); v2 tiers them by
# role in the intended-use certification (rubric §0/§1). Any FAIL on ANY tier
# still forces NOT-YET (unchanged v1 rule).
CRITERIA = {
    "fuelmix": ("C1 fuel-mix by class (grid-delivered)", TIER_LOAD),
    "sysvol": ("C2 system volume (gas/coal families)", TIER_LOAD),
    "price_mean": ("C3a mean LMP", TIER_LOAD),
    "price_shape": ("C3b price duration/shape", TIER_LOAD),
    # v2.7: gated on the actual RT hourly scarcity tail for every ISO; the
    # DA count is each row's report-only diagnostic companion.
    "price_tail": ("C3c price tail / scarcity (RT hourly)", TIER_SUPPORT),
    "dispatch_corr": ("C4 fleet hourly dispatch correlation", TIER_SUPPORT),
    # (C5a CO2 vs eGRID was REMOVED from the rubric by the v2.9 owner amendment
    # 2026-07-27, on the same grounds and the same pattern as C5b/C5c below:
    # the actual is not measured for every scored year. eGRID's latest released
    # workbook is the 2024 vintage (data/raw/fleet-egrid/, egrid2024_data.xlsx),
    # and data.egrid.egrid_vintage_for_year falls any later year back to it — so
    # a 2025 C5a "actual" is the 2024 intensities standing in, not a 2025
    # measurement. A criterion whose actual does not exist for a scored year
    # cannot be load-bearing in a calibration determination. C5a is now
    # REPORTED-ONLY: score_co2 still runs and its number stays on the payload
    # and the dashboard run pages, but it no longer contributes a status to the
    # determination or consumes caveat budget. Restoring it is an owner act and
    # should be year-scoped — 2023 and 2024 DO have their own released vintages;
    # only years past the latest vintage lack a measured actual.)
    # (C5b storage throughput and C5c storage dispatch shape were REMOVED from
    # the rubric by the v2.7 owner amendment 2026-07-16 — EIA-930
    # storage-dispatch data is not reliable enough to participate in a
    # calibration determination. The storage numbers stay visible on the
    # dashboard run pages as payload/bench diagnostics.)
    "governance": ("C6 governance gate", TIER_PROTECT),
    # (C7 diurnal shape (D-1) was RETIRED OUTRIGHT by the v3.1 owner amendment
    # 2026-08-06 — dropped from the report AND the determination, on the finding
    # that no commercial-grade comparable gates or publishes diurnal-shape
    # accuracy (rubric §8's comparables row and the v2 benchmark memo both score
    # C6/C7/C8 "beyond commercial practice", i.e. with no external anchor at
    # all). This is a HARDER removal than C5a/C5b/C5c, which stayed computed and
    # REPORTED_ONLY: score_shape and C7_GATED_CLASSES are deleted per rule 26
    # [R-DELETE]. The D-1 measurement itself is untouched — it stays in
    # legitimacy_diagnostics.json and C8 still gates on it through _d1_shape
    # wherever CLAUDE.md rule 20 requires a forced class to prove its shape.)
    "forced_share": ("C8 forced-energy share (D-2)", TIER_PROTECT),
}

# Criteria that still SCORE (their scorer runs and their number reaches the
# payload, the JSON detail and the dashboard run pages) but are NOT aggregated
# into the determination and consume no caveat budget, because they were
# removed from the rubric. Kept here only so their records carry a readable
# label — membership in this dict is what makes a criterion reported-only.
REPORTED_ONLY = {
    "co2": "C5a CO2 vs eGRID (REPORTED-ONLY, v2.9 — see the CRITERIA note)",
}


# ---------------------------------------------------------------------------
# Artifact loading
# ---------------------------------------------------------------------------
def load_artifacts(run_id: str) -> dict:
    """Load every committed artifact the scorer needs for ``run_id``.

    Returns ``{sidecar, payload, bench, config, attestation}``; ``bench`` is
    ``{year: bench_payload}`` and missing pieces are ``None`` so the scorer can
    SKIP rather than crash.
    """
    side_path = REGISTRY_DIR / f"{run_id}.json"
    if not side_path.exists():
        raise SystemExit(f"no registry sidecar for run id {run_id!r}.")
    sidecar = json.loads(side_path.read_text())
    iso = sidecar.get("iso", "ERCOT")

    run_js = RUNS_DIR / f"{run_id}.js"
    payload = _decode_run_js(run_js.read_text()) if run_js.exists() else None

    bench: dict[int, dict] = {}
    for part in sorted((BENCH_DIR / iso).glob("*.json.gz")) if iso else []:
        obj = ba.load_bench_part(part)
        for y in obj.get("meta", {}).get("years", []):
            bench[int(y)] = obj.get("bench", {})

    bundle_dir = REPO / sidecar["bundle"] if sidecar.get("bundle") else None
    config = None
    attestation = None
    if bundle_dir and bundle_dir.exists():
        rc = bundle_dir / "run_config.json"
        config = {
            "scenario_config": (
                json.loads(rc.read_text()).get("scenario_config", {})
                if rc.exists()
                else {}
            ),
            "meta": bundle_meta(bundle_dir),
        }
        att = bundle_dir / "calibration_attestation.json"
        if att.exists():
            attestation = json.loads(att.read_text())
    legitimacy = None
    if bundle_dir and bundle_dir.exists():
        legit_path = bundle_dir / "legitimacy_diagnostics.json"
        if legit_path.exists():
            legitimacy = json.loads(legit_path.read_text())
    return {
        "sidecar": sidecar,
        "payload": payload,
        "bench": bench,
        "config": config,
        "attestation": attestation,
        "legitimacy": legitimacy,
    }


# ---------------------------------------------------------------------------
# Small numeric helpers (stdlib only)
# ---------------------------------------------------------------------------
def _pct(model: float, actual: float) -> float | None:
    """Signed fractional error ``(model-actual)/actual``; None when undefined."""
    if actual is None or abs(actual) < 1e-9:
        return None
    return (model - actual) / actual


def _wmean(pairs: list[tuple[float, float]]) -> float | None:
    """Demand-weighted mean of ``(value, weight)`` pairs."""
    w = sum(wt for _, wt in pairs)
    if w <= 0:
        return None
    return sum(v * wt for v, wt in pairs) / w


def _nrmse(model: list[float], actual: list[float]) -> float | None:
    """Normalised RMSE of two equal-length monthly vectors (skip None cells)."""
    cells = [(m, a) for m, a in zip(model, actual) if m is not None and a is not None]
    if not cells:
        return None
    mean_a = sum(a for _, a in cells) / len(cells)
    if abs(mean_a) < 1e-9:
        return None
    rmse = math.sqrt(sum((m - a) ** 2 for m, a in cells) / len(cells))
    return rmse / mean_a


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------
def _ledger_match(exceptions: list[dict], criterion: str, year: int, key: str | None):
    """Return the ledger entry matching (criterion, year, class/family) or None.

    ``key`` is the class (fuelmix) or family (sysvol/dispatch_corr); criteria
    without a sub-key match on (criterion, year) alone.
    """
    for e in exceptions or []:
        if e.get("criterion") != criterion or int(e.get("year", -1)) != int(year):
            continue
        ekey = e.get("klass") or e.get("family")
        if key is None or ekey is None or str(ekey) == str(key):
            return e
    return None


C3C_STANDING_RULE_REASON = (
    'OWNER STANDING RULE, declared 2026-08-06 (session neiso-86), verbatim: "a c3c '
    "failure with all other gates passing should always be treated as a ledgered "
    "calibrated with caveats across all ISOs for holdout years and testing years going "
    'forward as a rule"; EXTENDED TO EVERY YEAR 2026-08-09 (session '
    'neiso-keeper-87-control), verbatim: "make sure c3c is an acceptable caveat for any '
    'holdout or training year". Auto-applied: C3c (price tail / scarcity) is the ONLY '
    "failing criterion and the governance gate passes. Classified ACCEPTED MODEL-CLASS "
    "LIMITATION -- admissible because C3c is SUPPORTING tier; the v3.0 fail-closed guard "
    "still refuses model-class on load-bearing and protective criteria, so this rule can "
    "never wave through C1/C2/C3a/C3b or C6/C8. IT IS NOT A PASS: C3c reads CAVEAT, "
    "never PASS, and the miss is reported at full magnitude on the determination basis. "
    "SINCE RUBRIC v3.3 (owner amendment 2026-08-17) the resulting ledgered caveat no "
    "longer DOWNGRADES the determination, so an otherwise-clean run reads CALIBRATED "
    "rather than CALIBRATED-WITH-CAVEATS -- the owner's determination being that a "
    "known, ledgered model-class limitation is not a caveat on the calibration. "
    "THE LONE-FAILURE CONDITION IS WHAT KEEPS IT FROM BEING AN ESCAPE HATCH: "
    "it fires only when the model is otherwise clean on every criterion, so it can never "
    "mask a second defect, and the caveat still consumes the single ledgerable slot."
)


def _apply_c3c_standing_rule(records: list[dict], gov: dict) -> None:
    """Reclassify a LONE C3c failure to a ledgered CAVEAT, in ANY year.

    The owner's standing rule of 2026-08-06, EXTENDED 2026-08-09 to every year
    rather than out-of-training years only. C3c (scarcity price tail) is a
    known, declared frontier in several ISOs; when it is the *only* thing
    failing, the run is a CALIBRATED-WITH-CAVEATS reading rather than a
    NOT-YET, and that is now true on a training year exactly as it already was
    on a validation or locked-test one.

    Why extending it is admissible rather than a loosening of the gate. The
    scope split it removes was never a statement about C3c's *severity* — the
    band, the tier and the reported magnitude are identical in every year. It
    was a procedural asymmetry: in-sample the same reclassification was
    available all along through an explicit exceptions-ledger entry (the route
    every current keeper carrying a C3c caveat actually used), so the split
    governed *who typed the justification*, not what the run was allowed to
    claim. Collapsing it removes a difference between years that the rubric
    could not otherwise defend, and it takes nothing off the model: the miss is
    still measured and reported at full magnitude, and it still spends the
    single ledgerable slot.

    RUBRIC v3.3 (owner amendment 2026-08-17) changed what that caveat COSTS,
    not what it IS: a ledgered C3c caveat no longer downgrades the overall
    determination, so an otherwise-clean run reads CALIBRATED. This function is
    unchanged by that — it still produces a CAVEAT, never a PASS, and every
    guard below still binds.

    What still stops it from being a general escape hatch — unchanged:

    * **Lone failure only.** If ANY other criterion fails, the rule does not
      fire and every failure stands -- including C3c's. This is the real guard:
      it fires only on a model that is otherwise clean, so it can never mask a
      second defect.
    * **Governance must pass.** A failing or unattested C6 blocks it.
    * **Supporting tier only, fail-closed.** It classifies MODEL_LIMIT, which
      :func:`_apply_ledger`'s v3.0 guard admits only for a SUPPORTING-tier
      criterion, so the rule can never reach C1/C2/C3a/C3b or C6/C8.
    * **Never a criterion-level PASS.** It produces a CAVEAT, the magnitude is
      reported in full, and it consumes the one ledgerable caveat slot. Since
      v3.3 that caveat no longer downgrades the OVERALL determination, but C3c
      itself never reads PASS, so ``grade_summary.target_grade`` does not
      absorb it and the miss stays visible on every report.

    "Lone" is measured over the criteria that CONSTITUTE the determination, i.e.
    :data:`CRITERIA` membership. ``records`` also carries REPORTED-ONLY streams
    that the rubric has demoted out of the determination -- C5a ``co2``, removed
    at v2.9 because eGRID's latest released vintage is 2024 and a 2025 "actual"
    would be the 2024 intensities standing in. Those contribute no status, no
    caveat budget and no reason line, so they must not silence this rule either.
    Measured 2026-08-09 on the committed artifacts: NYISO
    ``2026-08-06-nyiso-130-control`` fails C3c on 2023 and 2024 and NOTHING else
    -- its own determination basis reads "undocumented out-of-tolerance (FAIL)
    criteria: price_tail" -- yet an unrelated ``('co2', 2025)`` FAIL record was
    making the pre-2026-08-09 test see a non-C3c failure and keep silent. That
    was under-firing the rule as declared, on out-of-training years too, not
    only on the training years this amendment adds.

    Args:
        records: Scored criterion records, mutated in place.
        gov: The governance-gate record from :func:`score_governance`.
    """
    fails = [
        r for r in records if r["status"] == FAIL and r.get("criterion") in CRITERIA
    ]
    if not fails or any(r["criterion"] != "price_tail" for r in fails):
        return  # nothing failing, or something OTHER than C3c is -- rule silent
    if str(gov.get("status", "")).upper() != PASS:
        return  # governance failing/unattested -- never waved through
    for rec in fails:
        rec["status"] = CAVEAT
        rec["classification"] = MODEL_LIMIT
        rec["ledger_reason"] = C3C_STANDING_RULE_REASON
        rec["standing_rule"] = "c3c-any-year-2026-08-09"


def _apply_ledger(rec: dict, exceptions: list[dict]) -> dict:
    """Reclassify an out-of-tolerance result to CAVEAT iff the ledger documents it.

    A FAIL with a matching ledger entry becomes a CAVEAT: classified ACCEPTED
    MEASURED-INPUT LIMITATION by default, or ACCEPTED MODEL-CLASS LIMITATION
    when the entry carries ``"kind": "model-class"`` (rubric v3.0). A FAIL
    without an entry stays a FAIL (MODEL MISS).

    Fail-closed guards, applied in order:

    * **v3.1 (owner amendment 2026-08-06)** — the criterion must be in
      :data:`LEDGERABLE_CRITERIA`, i.e. C3c and nothing else. An entry naming
      any other criterion is IGNORED and the FAIL stands, whatever its kind or
      reason. Entries already sitting on committed attestations are left in
      place as the historical record; they simply stop reclassifying, so every
      keeper re-scores from its committed artifacts with no re-solve.
    * **v3.0** — a model-class entry is admissible ONLY for a SUPPORTING-tier
      criterion; matched against a load-bearing or protective criterion it is
      ignored and the FAIL stands. Owner acceptance of a model-class limit never
      waves through the certifying or anti-self-deception tiers.
    """
    if rec["status"] != FAIL:
        return rec
    if rec["criterion"] not in LEDGERABLE_CRITERIA:
        return rec  # fail-closed: C3c is the only ledgerable criterion (v3.1)
    entry = _ledger_match(exceptions, rec["criterion"], rec["year"], rec.get("key"))
    if not entry:
        return rec
    if entry.get("kind") == "model-class":
        tier = CRITERIA.get(rec["criterion"], (None, None))[1]
        if tier != TIER_SUPPORT:
            return rec  # fail-closed: model-class is supporting-tier-only
        rec["status"] = CAVEAT
        rec["classification"] = MODEL_LIMIT
    else:
        rec["status"] = CAVEAT
        rec["classification"] = MEASURED_LIMIT
    rec["ledger_reason"] = entry.get("reason", "")
    return rec


# ---------------------------------------------------------------------------
# EIA-923 completeness map (per-year committed part)
# ---------------------------------------------------------------------------
_COMPLETENESS_CACHE: dict | None = None


def _completeness_map() -> dict:
    """Return ``{year: {iso: {class: record}}}`` from the committed parts.

    Reads every ``completeness/eia923_<year>.json`` produced by
    ``scripts/audit_eia923_completeness.py``. Cached after the first load.
    Returns an empty map when the directory is absent (no preliminary-year
    completeness has been audited yet — every class then falls back to the blanket
    preliminary-vintage skip).
    """
    global _COMPLETENESS_CACHE
    if _COMPLETENESS_CACHE is not None:
        return _COMPLETENESS_CACHE
    out: dict[int, dict] = {}
    if COMPLETENESS_DIR.exists():
        for part in sorted(COMPLETENESS_DIR.glob("eia923_*.json")):
            obj = json.loads(part.read_text())
            out[int(obj["year"])] = obj  # full part: carries isos + families
    _COMPLETENESS_CACHE = out
    return out


def _band_result(err_abs: float, target: float, commercial: float):
    """Two-band scoring (rubric v2 §1): PASS inside the target band; auto
    CAVEAT (``COMMERCIAL_BAND``, listed but not budgeted) between the target
    and the evidence-anchored commercial-grade band; FAIL beyond it
    (ledgerable only as an accepted measured-input limitation)."""
    if err_abs <= target:
        return PASS, None
    if err_abs <= commercial:
        return CAVEAT, COMMERCIAL_BAND
    return FAIL, MODEL_MISS


# ---------------------------------------------------------------------------
# Actual scarcity-tail part (committed, scripts/data/derive_actual_tail.py)
# ---------------------------------------------------------------------------
TAIL_DIR = DATA_DIR / "tail"
_TAIL_CACHE: dict | None = None


def _tail_part() -> dict:
    """Return the committed actual-tail part (``tail/actual_tail.json``).

    ``{iso: {year(str): {threshold, da_gt, rt_gt, da_coverage, rt_coverage}}}``
    — the C3c DA-expressible benchmark (rubric §1 C3c / §5). Empty when the
    part is absent (C3c then SKIPs, never silently passes).
    """
    global _TAIL_CACHE
    if _TAIL_CACHE is not None:
        return _TAIL_CACHE
    p = TAIL_DIR / "actual_tail.json"
    _TAIL_CACHE = json.loads(p.read_text()).get("isos", {}) if p.exists() else {}
    return _TAIL_CACHE


def class_is_gated(iso: str, klass: str, year: int) -> bool:
    """Whether (iso, class) has a complete-enough 923 actual to gate in ``year``.

    Complete-vintage years (those with no completeness part) always gate — only a
    preliminary vintage with an audited completeness part restricts gating to the
    verified-complete, verified-complete-family classes
    (:func:`audit_eia923_completeness.audit`'s ``gate`` flag).
    """
    cmap = _completeness_map()
    if year not in cmap:
        return True  # complete vintage / no preliminary audit -> gate as usual
    rec = cmap[year].get("isos", {}).get(iso.upper(), {}).get(klass)
    return bool(rec and rec.get("gate"))


def family_is_complete(iso: str, family: str, year: int) -> bool:
    """Whether ``family`` (``gas``/``coal``) is fully reported for (iso, year).

    Complete-vintage years (no completeness part) are always complete — C2 then
    defers to the per-class C1 gate as it always has. A preliminary year defers
    only the families the audit flagged complete; the rest fall back to the
    EIA-930 family aggregate gate.
    """
    cmap = _completeness_map()
    if year not in cmap:
        return True
    return bool(cmap[year].get("families", {}).get(iso.upper(), {}).get(family))


# ---------------------------------------------------------------------------
# Per-criterion scoring (one record per criterion-year, pre-ledger)
# ---------------------------------------------------------------------------
def _gen_totals(ypay: dict, ybench: dict) -> tuple[float, float]:
    """System model/actual TOTAL generation (TWh), grid-delivered.

    Mirrors ``totalGen`` in the run explorer (docs/codebase-site/
    backcast-runs.html) exactly so the verdict's C1 bands match
    the dashboard scorecard. Each benchmarked class is counted ONCE: ``classFull``
    now carries the grid-delivered actual for every class — fossil (EIA-923 − BTM
    CHP), nuclear (EIA-923) and the variable renewables wind/solar on the EIA-930
    grid basis (distribution-connected / net-metered BTM PV removed in
    ``render_calibration_html``, the same source-authority as
    :func:`results.calibration.actuals_source`). actual = Σ ``classFull``; model =
    Σ ``gmModel`` over those same class keys. The earlier ``+ EIA-930
    nuclear/wind/solar`` term double-counted the renewables and re-introduced the
    BTM-inflated EIA-923 solar through ``classFull``, inflating the share
    denominator (NEISO 2023 read a_gen ≈ 128 vs the true grid ≈ 97 TWh).
    """
    gm = ypay.get("gmModel", {})
    cf = ybench.get("classFull", {})
    a_gen = sum(float(v) for v in cf.values())
    m_gen = sum(float(gm.get(g, 0.0)) for g in cf)  # over the classFull keys
    return m_gen, a_gen


def _total_load(ypay: dict, a_gen: float) -> float:
    """Total load served (TWh) = sum of zone demand from the LMP payload.

    For ISOs with scheduled interchange folded into demand (NEISO, NYISO, …),
    this equals generation + net imports — the correct denominator for the
    ≈1 pp volume band.  Falls back to ``a_gen`` when zone data is absent.
    """
    lmp = ypay.get("lmp", {})
    if not lmp:
        return a_gen
    return sum(float(z.get("d", 0.0)) for z in lmp.values())


def _fuelmix_vol_band(total_load: float, a_gen: float) -> float:
    """C1/C2 volume band (TWh): min(max(2% load, 3% actual gen), 8 TWh).

    The gen-floor term is the v3.4 owner amendment (2026-08-18, see the
    RUBRIC_VERSION genealogy): the volume leg may never bind tighter than the
    ±3.0-pp-of-mix materiality the share leg itself declares, measured on the
    ACTUAL total-generation denominator (raw |model−actual| over actual gen —
    immune to the system-total shrink that can flatter model-vs-actual
    share_pp). The 8 TWh cap is applied after the floor, so large-ISO bands
    are unchanged (the cap binds either way).
    """
    return min(
        max(
            FUELMIX_VOL_LOAD_FRAC * total_load,
            (FUELMIX_SHARE_PP / 100.0) * a_gen,
        ),
        FUELMIX_VOL_CAP_TWH,
    )


def score_fuelmix(
    year: int, ypay: dict, ybench: dict, iso: str = "ERCOT"
) -> list[dict]:
    """C1 — per-class grid-delivered fuel-mix, the universal gate.

    A class passes iff BOTH its grid-delivered volume miss is within
    min(max(2.0% of ISO total load, 3.0% of actual total generation), 8 TWh)
    (:func:`_fuelmix_vol_band`; the gen-floor is the v3.4 owner amendment)
    AND its share of total generation is within 3.0 pp of actual (the run
    explorer's ``classInTol`` on the gmModel/classFull basis).

    Gating is restricted to (ISO, class) pairs whose EIA-923 actual is VERIFIED
    COMPLETE for the year. A complete-vintage year (no committed completeness part)
    gates every benchmarked class as before. A PRELIMINARY-EIA-923 year (e.g. 2025
    today) gates only the classes the completeness audit
    (:mod:`scripts.audit_eia923_completeness`) flagged ``gate`` — a class whose own
    plants ALL reported AND whose whole fossil family reported (so the
    vintage-reconcile leaves its per-class actual un-scaled). Every other class is
    emitted SKIPPED (recorded, never a silent pass): its plant data is incomplete,
    so there is no trustworthy per-class actual to gate against. The C2 family
    system-volume gate still covers the skipped classes via the authoritative
    EIA-930 grid reconcile. The map auto-extends as a year's 923 finalises: re-run
    the audit and the now-complete classes begin gating with no code change.
    """
    gm = ypay.get("gmModel", {})
    cf = ybench.get("classFull", {})
    m_gen, a_gen = _gen_totals(ypay, ybench)
    total_load = _total_load(ypay, a_gen)
    vol_band = _fuelmix_vol_band(total_load, a_gen)
    out = []
    classes = [c for c in (*GAS_CLASSES, *COAL_CLASSES) if c not in FUELMIX_EXCLUDED]
    cmap_year = _completeness_map().get(year, {}).get("isos", {}).get(iso.upper(), {})
    for c in classes:
        a = cf.get(c)
        if a is None:
            continue  # class not benchmarked for this ISO-year
        a = float(a)
        m = float(gm.get(c, 0.0))
        d = m - a
        if m_gen > 0 and a_gen > 0:
            share_pp = 100.0 * m / m_gen - 100.0 * a / a_gen
        else:
            share_pp = None
        if not class_is_gated(iso, c, year):
            comp = cmap_year.get(c, {})
            why = comp.get("status", "incomplete")
            reasons = "; ".join(comp.get("reasons", [])) or "no per-class actual"
            rec = {
                "criterion": "fuelmix",
                "key": c,
                "year": year,
                "status": SKIPPED,
                "classification": None,
                "metric": f"{c} grid-delivered TWh + share of generation",
                "model": round(m, 3),
                "actual": round(a, 3),
                "share_pp": round(share_pp, 2) if share_pp is not None else None,
                "tol": None,
                "completeness": why,
                "magnitude": (
                    f"preliminary EIA-923 vintage: {why} plant data ({reasons}); "
                    "not gated — C2 family grid reconcile covers this class"
                ),
                "vintage_gap_twh": round(d, 3),  # report-only; does not gate
            }
            out.append(rec)
            continue
        vol_ok = a_gen > 0 and abs(d) <= vol_band
        share_ok = abs(share_pp) <= FUELMIX_SHARE_PP if share_pp is not None else True
        if vol_ok and share_ok:
            status, classification = PASS, None
        else:
            status, classification = FAIL, MODEL_MISS
        mag = f"{d:+.2f} TWh"
        if share_pp is not None:
            mag += f", share {share_pp:+.1f}pp"
        if status == FAIL:
            breach = "/".join(
                lab
                for lab, good in (("volume", vol_ok), ("share", share_ok))
                if not good
            )
            mag += f" ({breach} out of band)"
        rec = {
            "criterion": "fuelmix",
            "key": c,
            "year": year,
            "status": status,
            "classification": classification,
            "metric": f"{c} grid-delivered TWh + share of generation",
            "model": round(m, 3),
            "actual": round(a, 3),
            "share_pp": round(share_pp, 2) if share_pp is not None else None,
            "tol": (
                f"±min(max({FUELMIX_VOL_LOAD_FRAC * 100:.1f}% ISO-load, "
                f"{FUELMIX_SHARE_PP:g}% actual-gen), "
                f"{FUELMIX_VOL_CAP_TWH:g} TWh) = ±{vol_band:.2f} TWh "
                f"& ±{FUELMIX_SHARE_PP:g}pp share"
            ),
            "completeness": cmap_year.get(c, {}).get("status", "complete"),
            "magnitude": mag,
        }
        out.append(rec)
    return out


def _fallback_coal_anchor(
    iso: str, ybench: dict, bench_all: dict | None
) -> tuple[float, float, int] | None:
    """CEMS-anchored coal-family actual for a preliminary-vintage year.

    Every coal unit ≥25 MW is CEMS-metered, so CAMPD coal is complete even when
    the EIA-923 vintage is not. The bench part carries the CEMS-net coal total
    (``e930["coal_cems"]``, written solely by ``render_calibration_html`` when the
    bench part is built — the earlier post-hoc splice script was deleted
    2026-07-12 to keep a single writer, per the owner default directive);
    this helper translates it onto the 923-grid family scale with the measured
    CEMS→923-grid ratio ``k`` from the run's own complete-vintage years
    (Σ classFull coal classes ÷ that year's ``coal_cems`` — the parasitic-factor
    / coverage gap, ~0.95–1.01 per ISO). Returns ``(anchor_twh, k, n_years)``
    or ``None`` when the bench predates the splice or no complete coal vintage
    is in the run (the caller then keeps the legacy raw-930 fallback).
    """
    cems = float((ybench.get("e930") or {}).get("coal_cems", 0.0) or 0.0)
    if cems <= 0.0 or not bench_all:
        return None
    ratios = []
    for y2, yb2 in bench_all.items():
        e2 = yb2.get("e930") or {}
        cems2 = float(e2.get("coal_cems", 0.0) or 0.0)
        if cems2 <= 0.0 or not family_is_complete(iso, "coal", int(y2)):
            continue
        grid2 = sum(
            float((yb2.get("classFull") or {}).get(c, 0.0)) for c in COAL_CLASSES
        )
        if grid2 > 0.0:
            ratios.append(grid2 / cems2)
    if not ratios:
        return None
    k = sum(ratios) / len(ratios)
    return cems * k, k, len(ratios)


def score_sysvol(
    year: int,
    ypay: dict,
    ybench: dict,
    iso: str = "ERCOT",
    bench_all: dict | None = None,
) -> list[dict]:
    """C2 — gas/coal family system volume, folded into the per-class universal gate.

    **Rubric v2.5 (owner amendment 2026-07-13): C2 gates ONLY fully-reported
    EIA-923 families.** EIA-923 is the C2 source of truth; a
    preliminary-vintage family (incomplete 923 booking) is NOT gated against
    any fallback basis — the G-21b 930-derived family total and the CAISO
    CEMS anchor below now print as SKIPPED diagnostics only, and the family
    re-gates when the final vintage lands. Mirrors C1's incomplete-class
    skip: an incomplete benchmark can fabricate a miss in either direction,
    so it is evidence, not a gate.

    For COMPLETE-VINTAGE years a family passes iff EVERY constituent fossil class
    is within the universal per-class gate (|model−actual| within the C1 volume
    band AND share within ±FUELMIX_SHARE_PP) — the same scale-relative band C1
    applies, evaluated per class rather than on the netted family aggregate. This
    retires the old ±2.5%-of-family percent band, which had two failure modes: it
    (a) INVENTED a family fail when a mid-size family's small absolute miss
    exceeded 2.5% of itself (e.g. ERCOT coal +1.75 TWh = +3.0% of a 58 TWh family,
    yet only +0.34 pp of generation and well inside the C1 volume band), and (b)
    MASKED a real per-class miss when offsetting class errors netted out across the
    family (e.g. a CT_PEAKER over-build cancelled by a CC under-build summing to
    ~0% at the family level). The per-class roll-up does neither: it nets nothing.

    For a PRELIMINARY-EIA-923 family — one the completeness audit flags as not
    fully reported (:func:`family_is_complete`) — there is no trustworthy per-class
    actual (missing plants under-report thermal; EIA-930 carries no per-class
    split), so the family aggregate vs the authoritative EIA-930 grid total is the
    only available volume check — retained here as the ±2.5% family fallback,
    explicitly scoped to the no-per-class-data case. A preliminary year whose
    family DID fully report (e.g. ERCOT coal 2025) defers to the C1 per-class gate
    exactly like a complete vintage — only the still-incomplete families fall back.

    The fallback compares like for like against the EIA-930 grid cell: the model
    gas sum spans every gas class PLUS the OTHER_FOSSIL scoring bucket (930 books
    mixed gas-thermal plants under NG:NG — same membership as
    ``render_calibration_html._GAS_GROUPS``), and when the bundle carries the
    EIA-930 "other" series the gas target is deflated by the genuinely-folded
    OTHER+biomass portion (post-Nov-2024 storage breakout, ERCO's Other series is
    ~biomass alone, so the 923 OTHER-class generation sits inside NG:NG).

    **G-21b (2026-07-12) — the fallback's per-fuel SPLIT is CEMS-anchored.**
    EIA-930's per-fuel gas/coal attribution is BA-reported and demonstrably
    unreliable against CEMS (every coal unit ≥25 MW is metered): on the
    complete vintages 930 coal runs −17..−21 TWh below CEMS in MISO and
    +7..+11 above in PJM, with the mirror error booked in the NG:NG cell —
    so gating a preliminary family on the raw 930 per-fuel cell fabricates
    misses of exactly that size (the same defect class the G-21 combined
    reconcile fixed for C1's ``classFull``). The fallback therefore keeps the
    930 level but corrects the split with measured data: an incomplete COAL
    family gates against the CEMS anchor (:func:`_fallback_coal_anchor` —
    CAMPD coal × the run's complete-vintage CEMS→923-grid ratio), and an
    incomplete GAS family gates against the 930 COMBINED fossil total minus
    the coal anchor (the anchor from classFull when coal is complete, else
    CEMS). A bench part predating the ``coal_cems`` splice — or a run with no
    complete coal vintage — keeps the legacy raw-930 cell, labelled as such.
    """
    gm = ypay.get("gmModel", {})
    cf = ybench.get("classFull", {})
    e930 = ybench.get("e930", {})
    m_gen, a_gen = _gen_totals(ypay, ybench)
    total_load = _total_load(ypay, a_gen)
    vol_band = _fuelmix_vol_band(total_load, a_gen)
    out = []
    for fam, classes in (("gas", GAS_CLASSES), ("coal", COAL_CLASSES)):
        scored = [c for c in classes if c not in FUELMIX_EXCLUDED]
        m = sum(float(gm.get(c, 0.0)) for c in scored)
        a923 = sum(float(cf.get(c, 0.0)) for c in scored)
        a930 = float(e930.get(fam, 0.0)) or None
        use_family_fallback = not family_is_complete(iso, fam, year)
        if max(a923, a930 or 0.0) < SYSVOL_MIN_TWH:
            out.append(
                _skip(
                    "sysvol",
                    year,
                    f"{fam} family immaterial (<{SYSVOL_MIN_TWH:g} TWh); "
                    "governed by the C1 per-class absolute band",
                    key=fam,
                )
            )
            continue
        if use_family_fallback:
            # EIA-930 NG:NG includes ALL gas-fired generation at the grid
            # meter (CC, CT, ST — including CHP exports AND the genuinely-
            # mixed gas-thermal plants the scoring transform re-buckets into
            # OTHER_FOSSIL), so the model sum must also include every gas
            # class plus OTHER_FOSSIL, not just the C1-scored subset.  The
            # scored list excludes CT_CHP (a BTM class ungated in C1) and
            # OTHER_FOSSIL (not a merit-order class), but omitting them here
            # creates an apples-to-oranges gap of ~6 + ~1 TWh/yr in ERCOT —
            # the same family membership reconcile_vintage_classes uses
            # (render_calibration_html._GAS_GROUPS).
            fam_all = (*classes, "OTHER_FOSSIL") if fam == "gas" else classes
            m_fam = sum(float(gm.get(c, 0.0)) for c in fam_all)
            a923_fam = sum(float(cf.get(c, 0.0)) for c in fam_all)
            # G-21b: correct the 930 per-fuel split with the CEMS coal anchor
            # (docstring above); keep the 930 combined level. Falls back to
            # the legacy raw cell when the anchor is unavailable.
            anchor = _fallback_coal_anchor(iso, ybench, bench_all)
            actual = a930
            source = "EIA-930 grid (preliminary-923 vintage)"
            if (
                fam == "gas"
                and iso in CEMS_GAS_ANCHOR_ISOS
                and e930.get("gas_cems_grid") is not None
                and e930.get("gas_cogen_grid") is not None
            ):
                # Corrupted-NG-cell ISO: the family actual is the committed
                # CEMS anchor — CEMS bench-gas net (grid-delivered) + the
                # carried 923 non-CEMS cogen block — never the 930 NG cell
                # (which carries the fabricated solar-shaped block). No
                # fold-in deflation applies: the anchor contains no
                # geothermal/biomass by construction.
                actual = float(e930["gas_cems_grid"]) + float(e930["gas_cogen_grid"])
                source = (
                    "CAMPD CEMS bench-gas + EIA-923 non-CEMS cogen block "
                    "(930 NG cell corrupted; FINDING 2026-07-12)"
                )
                err = _pct(m_fam, actual) if actual else None
                # Rubric v2.5 (owner amendment 2026-07-13): a preliminary-923
                # vintage is never gated — the anchor comparison prints as a
                # SKIPPED diagnostic and re-gates when the final vintage lands.
                status, classification = SKIPPED, None
                out.append(
                    {
                        "criterion": "sysvol",
                        "key": fam,
                        "year": year,
                        "status": status,
                        "classification": classification,
                        "metric": (
                            f"{fam} family grid-delivered TWh "
                            "(preliminary vintage, CEMS-anchored diagnostic — "
                            "not gated, rubric v2.5)"
                        ),
                        "model": round(m_fam, 2),
                        "actual": round(actual, 2) if actual else None,
                        "tol": (
                            f"±{SYSVOL_TOL * 100:.1f}% target / "
                            f"±{SYSVOL_COMMERCIAL * 100:.1f}% commercial "
                            "(family, no per-class actual)"
                        ),
                        "magnitude": (
                            f"{err * 100:+.1f}%" if err is not None else "n/a"
                        ),
                        "source": source,
                        "vintage_reconciled": False,
                    }
                )
                continue
            if fam == "coal" and anchor is not None:
                actual, _k, _n = anchor
                source = (
                    "CAMPD CEMS coal × complete-vintage grid ratio "
                    f"(k={_k:.3f}, {_n} yr; G-21b split anchor)"
                )
            elif fam == "gas":
                coal930 = float(e930.get("coal", 0.0) or 0.0)
                coal_anchor = None
                if family_is_complete(iso, "coal", year):
                    _grid = sum(float(cf.get(c, 0.0)) for c in COAL_CLASSES)
                    coal_anchor = _grid if _grid > 0.0 else None
                elif anchor is not None:
                    coal_anchor = anchor[0]
                if coal_anchor is not None and a930 is not None and coal930 > 0.0:
                    actual = (a930 + coal930) - coal_anchor
                    source = (
                        "EIA-930 combined fossil minus coal anchor "
                        "(G-21b split correction)"
                    )
            if fam == "gas" and actual is not None and "other" in e930:
                # ERCO's post-Nov-2024 EIA-930 "Other" series carries roughly
                # biomass alone (the storage breakout moved batteries to
                # BAT/UES), so the OTHER-class generation the 923 books sits
                # inside NG:NG — subtract only the genuinely-folded portion
                # (mirrors render_calibration_html._gas_foldin_deflation).
                actual -= bs.gas_foldin_deflation(cf, e930, iso)
            reconciled = bool(actual and a923_fam < VINTAGE_RECONCILE_FRAC * actual)
            err = _pct(m_fam, actual) if actual else None
            # Rubric v2.5 (owner amendment 2026-07-13): a preliminary-923
            # vintage is never gated — the fallback comparison prints as a
            # SKIPPED diagnostic and re-gates when the final vintage lands.
            status, classification = SKIPPED, None
            out.append(
                {
                    "criterion": "sysvol",
                    "key": fam,
                    "year": year,
                    "status": status,
                    "classification": classification,
                    "metric": (
                        f"{fam} family grid-delivered TWh (preliminary "
                        "vintage diagnostic — not gated, rubric v2.5)"
                    ),
                    "model": round(m_fam, 2),
                    "actual": round(actual, 2) if actual else None,
                    "tol": (
                        f"±{SYSVOL_TOL * 100:.1f}% target / "
                        f"±{SYSVOL_COMMERCIAL * 100:.1f}% commercial "
                        "(family, no per-class actual)"
                    ),
                    "magnitude": f"{err * 100:+.1f}%" if err is not None else "n/a",
                    "source": source,
                    "vintage_reconciled": reconciled,
                }
            )
            continue
        breaches = [
            c
            for c in scored
            if cf.get(c) is not None
            and (
                abs(float(gm.get(c, 0.0)) - float(cf[c])) > vol_band
                or (
                    m_gen > 0
                    and a_gen > 0
                    and abs(
                        100.0 * float(gm.get(c, 0.0)) / m_gen
                        - 100.0 * float(cf[c]) / a_gen
                    )
                    > FUELMIX_SHARE_PP
                )
            )
        ]
        out.append(
            {
                "criterion": "sysvol",
                "key": fam,
                "year": year,
                "status": PASS,  # fully-reported family: governed by C1 per-class
                "classification": None,
                "metric": (
                    f"{fam} family — fully reported; per-class volume/share "
                    "governed by the C1 universal gate (no family netting/percent band)"
                ),
                "model": round(m, 2),
                "actual": round(a923, 2),
                "tol": (
                    f"per-class ±min(max({FUELMIX_VOL_LOAD_FRAC * 100:.1f}% "
                    f"ISO-load, {FUELMIX_SHARE_PP:g}% actual-gen), "
                    f"{FUELMIX_VOL_CAP_TWH:g} TWh) = ±{vol_band:.2f} TWh "
                    f"& ±{FUELMIX_SHARE_PP:g}pp share (via C1)"
                ),
                "magnitude": (
                    "all classes in band (C1)"
                    if not breaches
                    else f"C1 flags: {', '.join(breaches)}"
                ),
                "source": "EIA-923 − BTM (grid-delivered), per-class via C1",
                "vintage_reconciled": False,
            }
        )
    return out


def score_price_mean(year: int, ypay: dict, ybench: dict) -> dict:
    """C3a — system load-weighted mean LMP vs actual RT (fallback DA).

    The gated benchmark is named in the record's ``metric`` (``vs RT`` /
    ``vs DA``): the model is structurally a real-time analogue (a
    perfect-foresight dispatch LP prices RT physics, not day-ahead risk
    premia), so RT is the honest benchmark and DA is only a fallback when no
    RT actual is committed. The DA comparison is surfaced separately as a
    non-gated diagnostic (:func:`score_price_mean_da_diagnostic`).

    Rubric v2.4: the gated actual is the LIKE-FOR-LIKE load-weighted bench
    (``rt_lw``/``da_lw`` — the committed hourly actual weighted by the same
    measured demand the model dispatches; see the RUBRIC_VERSION note). The
    legacy equal-hour hub fields (``rt``/``da``) remain a labelled fallback
    for ISO-years the lw retrofit does not cover, so no year loses coverage.
    """
    lmp = ypay.get("lmp", {})
    avg = ybench.get("avgLMP") or {}
    # v2.4 basis ladder: load-weighted RT > load-weighted DA > legacy
    # equal-hour RT > legacy equal-hour DA.
    if avg.get("rt_lw") is not None:
        bench_kind, bench_key, lw_basis = "RT", "rt_lw", True
    elif avg.get("da_lw") is not None:
        bench_kind, bench_key, lw_basis = "DA", "da_lw", True
    elif avg.get("rt") is not None:
        bench_kind, bench_key, lw_basis = "RT", "rt", False
    else:
        bench_kind, bench_key, lw_basis = "DA", "da", False
    actual = avg.get(bench_key)
    # Like-for-like calendar coverage: when the actual series is partial (its
    # monthly vector has empty months — e.g. CAISO 2023, whose Jan–Feb aged
    # out of OASIS retention), the committed actual mean only averages the
    # covered months, so the model side must be masked to the SAME months.
    # Comparing a full-year model mean (which correctly carries the $190
    # gas-crisis January) against a Mar–Dec actual is a coverage artifact,
    # not a price error. Full-coverage years are byte-identical.
    actual_mon = avg.get(f"{bench_key}_mon")
    covered = [i for i, v in enumerate(actual_mon or []) if v is not None]
    masked = bool(actual_mon) and 0 < len(covered) < 12
    if masked:
        pairs = []
        for z in lmp.values():
            p_mon = z.get("pMon") or [None] * 12
            d_mon = z.get("dMon") or [0.0] * 12
            pairs.extend((p_mon[i], d_mon[i]) for i in covered if p_mon[i] is not None)
    else:
        pairs = [
            (z.get("p"), z.get("d", 0.0))
            for z in lmp.values()
            if z.get("p") is not None
        ]
    model = _wmean(pairs) if pairs else None
    if model is None or actual is None:
        return _skip("price_mean", year, "no model or actual mean LMP")
    err = _pct(model, actual)
    status, classification = _band_result(
        abs(err), PRICE_MEAN_TOL, PRICE_MEAN_COMMERCIAL
    )
    basis = "load-weighted" if lw_basis else "LEGACY equal-hour basis"
    label = (
        f"vs RT ({basis})"
        if bench_kind == "RT"
        else f"vs DA ({basis}) — no RT actual committed"
    )
    if masked:
        label += f" (model masked to actual's {len(covered)}-month coverage)"
    return {
        "criterion": "price_mean",
        "key": None,
        "year": year,
        "status": status,
        "classification": classification,
        "metric": f"system load-weighted mean LMP $/MWh ({label})",
        "benchmark": bench_kind,
        "model": round(model, 2),
        "actual": round(actual, 2),
        "tol": (
            f"±{PRICE_MEAN_TOL * 100:.0f}% target / "
            f"±{PRICE_MEAN_COMMERCIAL * 100:.0f}% commercial"
        ),
        "magnitude": f"{err * 100:+.1f}%",
    }


def score_price_mean_da_diagnostic(year: int, ypay: dict, ybench: dict) -> dict | None:
    """C3a DA diagnostic — model mean LMP vs the DA actual, never gated.

    A perfect-foresight dispatch LP is a real-time analogue: the DA−RT spread
    (the DART risk premium — e.g. 2023 ERCOT DA $55.94 vs RT $48.36) is a
    forward risk premium the LP has no mechanism to price, and modeling it
    with offers/adders is forbidden (a fit to the price residual). C3a
    therefore gates on RT; this record makes the DA gap *visible* instead of
    hidden, as a SKIPPED (never PASS/FAIL) diagnostic row. Returns ``None``
    when the DA actual is absent or DA is already the gated fallback
    benchmark (no second series to diagnose).
    """
    avg = ybench.get("avgLMP") or {}
    # v2.4: diagnose on the load-weighted pair when both sides carry it, so
    # the DART premium is read on the same basis C3a gates on; legacy
    # equal-hour pair otherwise.
    if avg.get("rt_lw") is not None and avg.get("da_lw") is not None:
        rt, da = avg.get("rt_lw"), avg.get("da_lw")
        da_mon_key = "da_lw_mon"
    else:
        rt, da = avg.get("rt"), avg.get("da")
        da_mon_key = "da_mon"
    if rt is None or da is None:
        return None  # DA absent, or DA is already the gated benchmark
    lmp = ypay.get("lmp", {})
    # Mirror score_price_mean's partial-coverage masking (same calendar on
    # both sides when the DA actual has empty months).
    da_mon = avg.get(da_mon_key)
    covered = [i for i, v in enumerate(da_mon or []) if v is not None]
    if da_mon and 0 < len(covered) < 12:
        pairs = []
        for z in lmp.values():
            p_mon = z.get("pMon") or [None] * 12
            d_mon = z.get("dMon") or [0.0] * 12
            pairs.extend((p_mon[i], d_mon[i]) for i in covered if p_mon[i] is not None)
    else:
        pairs = [
            (z.get("p"), z.get("d", 0.0))
            for z in lmp.values()
            if z.get("p") is not None
        ]
    model = _wmean(pairs) if pairs else None
    if model is None:
        return None
    err = _pct(model, da)
    return {
        "criterion": "price_mean",
        "key": "da_diagnostic",
        "year": year,
        "status": SKIPPED,
        "classification": None,
        "metric": "mean LMP vs DA (diagnostic — DART premium, not gated)",
        "benchmark": "DA",
        "model": round(model, 2),
        "actual": round(float(da), 2),
        "tol": "not gated",
        "magnitude": (
            f"{err * 100:+.1f}% vs DA (DA−RT premium ${float(da) - float(rt):+.2f})"
        ),
    }


def score_price_shape(year: int, ypay: dict, ybench: dict) -> dict:
    """C3b — monthly load-weighted price NRMSE (quantitative shape metric)."""
    lmp = ypay.get("lmp", {})
    # Model monthly = demand-weighted across zones of pMon by dMon.
    model_mon: list[float | None] = []
    for mo in range(12):
        pairs = []
        for z in lmp.values():
            pm = (z.get("pMon") or [None] * 12)[mo]
            dm = (z.get("dMon") or [0.0] * 12)[mo]
            if pm is not None:
                pairs.append((pm, dm))
        model_mon.append(_wmean(pairs) if pairs else None)
    avg = ybench.get("avgLMP") or {}
    # v2.4 basis ladder mirroring score_price_mean: load-weighted monthly
    # actual first, legacy equal-hour monthly as labelled fallback.
    actual_mon = avg.get("rt_lw_mon") or avg.get("da_lw_mon")
    lw_basis = actual_mon is not None
    if actual_mon is None:
        actual_mon = avg.get("rt_mon") or avg.get("da_mon")
    if actual_mon is None or all(v is None for v in model_mon):
        return _skip("price_shape", year, "no monthly model or actual LMP")
    nrmse = _nrmse(model_mon, actual_mon)
    if nrmse is None:
        return _skip("price_shape", year, "monthly NRMSE undefined")
    status, classification = _band_result(
        nrmse, PRICE_SHAPE_NRMSE_MAX, PRICE_SHAPE_NRMSE_COMMERCIAL
    )
    basis = "load-weighted" if lw_basis else "LEGACY equal-hour basis"
    return {
        "criterion": "price_shape",
        "key": None,
        "year": year,
        "status": status,
        "classification": classification,
        "metric": f"monthly load-weighted price NRMSE ({basis} actual)",
        "model": round(nrmse, 3),
        "actual": None,
        "tol": (
            f"≤{PRICE_SHAPE_NRMSE_MAX:.2f} target / "
            f"≤{PRICE_SHAPE_NRMSE_COMMERCIAL:.2f} commercial"
        ),
        "magnitude": f"NRMSE {nrmse:.3f}",
    }


def score_price_tail(year: int, ypay: dict, iso: str) -> list[dict]:
    """C3c — scarcity tail hours vs the actual RT hourly tail (rubric v2.7).

    The model tail (count of hours the LP's max zonal dual exceeds the per-ISO
    threshold, from the payload's ``ordc.hoursGt200.model``) is gated against
    the committed **RT hourly** actual tail count (``tail/actual_tail.json``,
    ``scripts/data/derive_actual_tail.py``) for EVERY ISO (rubric §5, v2.7 owner
    amendment 2026-07-16): the RT hourly hub tail is the scarcity the market
    actually realized — the judged quantity. The DA count is the report-only
    diagnostic row: it prices scarcity *expectations*, and its wedge over RT
    is the day-ahead forecast-risk premium a realized-weather backcast is out
    of representation to price (see the TAIL_LO block comment for the basis
    history — v2 DA-everywhere, v2.6 ERCOT-RT, v2.7 RT-everywhere).

    Band: model within [TAIL_LO x, TAIL_HI x] of the RT actual. Small
    counts (actual < TAIL_SMALL_COUNT) are scored by absolute difference
    (|model − actual| ≤ TAIL_SMALL_COUNT) — a ratio on a handful of hours is
    degenerate, and it doubles as the invented-tail guard against a ~0 actual.
    """
    ordc = ypay.get("ordc")
    thr = TAIL_THRESHOLD.get(iso, 200.0)
    if not ordc or "hoursGt200" not in ordc:
        return [
            _skip(
                "price_tail",
                year,
                f"hourly scarcity series not in committed payload (tail>${thr:.0f})",
            )
        ]
    h = ordc["hoursGt200"]
    # G-20a (2026-07-07, owner-approved): score the SETTLEMENT price
    # (energy LMP + the published reserve/scarcity overlay) when the render
    # derived one for this ISO-year (``overlay`` present), else the energy-only
    # LP dual (``model``). Real RT settlement IS energy LMP + reserve price
    # (ERCOT RTSPP, PJM SRMCP-into-LMP, NYISO RCPF-into-LBMP); the adder is a
    # published, forward-reproducible input (CLAUDE.md rule 13), not fitted to
    # this residual. ``model`` stays emitted (and read below for the diagnostic
    # note) so the energy-only tail remains visible; the settlement count is the
    # gated one. Every VOLUME gate keeps reading the energy-only dual elsewhere.
    settled = h.get("overlay") is not None
    model = float(h["overlay"]) if settled else float(h.get("model", 0))
    energy_only = float(h.get("model", 0))
    tail_rec = _tail_part().get(iso, {}).get(str(year))
    # Gated basis (rubric §5, v2.7): RT for every ISO; DA is the diagnostic.
    gate_key, diag_key = "rt_gt", "da_gt"
    gate_lbl, diag_lbl = "RT", "DA"
    out: list[dict] = []
    if tail_rec is None or tail_rec.get(gate_key) is None:
        out.append(
            _skip(
                "price_tail",
                year,
                f"no committed {gate_lbl} actual tail for this ISO-year "
                "(frontend/data/backcast/tail/actual_tail.json — run "
                "scripts/data/derive_actual_tail.py)",
            )
        )
    else:
        actual = float(tail_rec[gate_key])
        cov = tail_rec.get(f"{gate_key[:2]}_coverage", 1.0)
        cov_note = (
            f"; {gate_lbl} coverage {cov:.0%} — count is a lower bound"
            if cov < 0.999
            else ""
        )
        # ``model`` above is the settlement count when an overlay was derived;
        # note the basis and, when overlaid, the energy-only count it was lifted
        # from — so the tail's provenance (energy dual vs energy+reserve price)
        # is visible in the verdict, not just the number.
        basis = "settlement (LMP+overlay)" if settled else "energy-only LMP"
        settle_note = (
            f"; energy-only {energy_only:.0f}h + published overlay" if settled else ""
        )
        if actual < TAIL_SMALL_COUNT:
            ok = abs(model - actual) <= TAIL_SMALL_COUNT
            mag = (
                f"model {model:.0f}h [{basis}] vs {gate_lbl} actual {actual:.0f}h "
                f"(small-count |Δ|≤{TAIL_SMALL_COUNT}h, >${thr:.0f}){settle_note}{cov_note}"
            )
        else:
            ratio = model / actual
            ok = TAIL_LO <= ratio <= TAIL_HI
            mag = (
                f"model {model:.0f}h [{basis}] vs {gate_lbl} actual {actual:.0f}h "
                f"({ratio:.2f}×, >${thr:.0f}){settle_note}{cov_note}"
            )
        out.append(
            {
                "criterion": "price_tail",
                "key": None,
                "year": year,
                "status": PASS if ok else FAIL,
                "classification": None if ok else MODEL_MISS,
                "metric": (
                    f"hours {gate_lbl}-expressible "
                    f"{'settlement price' if settled else 'LMP'} > ${thr:.0f}/MWh"
                ),
                "model": model,
                "actual": actual,
                "tol": (
                    f"[{TAIL_LO:g}×, {TAIL_HI:g}×] of {gate_lbl} actual "
                    f"(|Δ|≤{TAIL_SMALL_COUNT}h when actual <{TAIL_SMALL_COUNT}h)"
                ),
                "magnitude": mag,
            }
        )
    # Companion DA basis — reported, never gated (v2.7): the DA count embeds
    # the day-ahead forecast-risk premium a realized-weather backcast is out
    # of scope to price.
    diag_actual = (
        float(tail_rec[diag_key])
        if tail_rec is not None and tail_rec.get(diag_key) is not None
        else None
    )
    diag_why = "embeds the DA forecast-risk premium, not gated"
    if diag_actual is not None:
        out.append(
            {
                "criterion": "price_tail",
                "key": f"{diag_key[:2]}_diagnostic",
                "year": year,
                "status": SKIPPED,
                "classification": None,
                "metric": (
                    f"hours {diag_lbl} LMP > ${thr:.0f}/MWh (diagnostic — {diag_why})"
                ),
                "model": model,
                "actual": diag_actual,
                "tol": "not gated",
                "magnitude": (
                    f"model {model:.0f}h vs {diag_lbl} actual {diag_actual:.0f}h "
                    "(out-of-representation companion)"
                ),
            }
        )
    return out


def _pearson_nrmse(m: list, o: list) -> tuple[float, float]:
    """Pearson r and mean-normalized RMSE of two equal-length hourly series."""
    n = len(m)
    mm = sum(m) / n
    om = sum(o) / n
    sxy = sxx = syy = sse = 0.0
    for a, b in zip(m, o):
        da, db = a - mm, b - om
        sxy += da * db
        sxx += da * da
        syy += db * db
        sse += (a - b) * (a - b)
    denom = math.sqrt(sxx * syy)
    r = sxy / denom if denom > 0 else 0.0
    nrmse = math.sqrt(sse / n) / om if om > 0 else 9.9
    return r, nrmse


def _cems_gas_hourly_fit(
    ypay: dict, ybench: dict, model_twh: float | None
) -> tuple[float, float, float] | None:
    """C4 gas fit on the CEMS basis, from committed artifacts only.

    Returns ``(r, nrmse, actual_twh)`` of the model's hourly gas fleet against
    the MEASURED gas hourly actual — CEMS bench-gas hourly (bench part
    ``plants[].campd``, CAMPD net, grid-delivered via a flat BTM CHP removal)
    plus the flat non-CEMS cogen block (``e930.gas_cogen_grid``) — instead of
    the corrupted EIA-930 NG cell. Both sides decode the committed base64 CF%
    series (payload ``plants[].m`` / bench ``plants[].campd``, uint8 percent of
    nameplate): the model core is the CEMS-covered gas plants' dispatch, and
    the payload's remaining gas mass (plants with no CAMPD series) is added as
    a flat fill up to the committed fuel-row level ``model_twh`` — flat terms
    are pearson-invariant, so ``r`` measures the measured-fleet shape while
    NRMSE keeps the coherent grid level on both sides. Payloads rendered after
    the rework carry the same basis natively in ``fuelRows``; this recompute
    scores committed pre-rework payloads identically (to b64 quantization,
    ≤~0.01 in r). ``None`` when the committed artifacts lack the series.
    """
    e930 = ybench.get("e930") or {}
    cogen = e930.get("gas_cogen_grid")
    bplants = ybench.get("plants") or {}
    pplants = ypay.get("plants") or {}
    if cogen is None or not bplants or not pplants:
        return None
    t = 8760
    model = [0.0] * t
    act = [0.0] * t
    btm_twh = 0.0
    n_used = 0
    for code, bp in bplants.items():
        if bp.get("group") not in GAS_CLASSES or bp.get("nodata"):
            continue
        cap = float(bp.get("npl") or 0.0)
        camp_b64 = bp.get("campd")
        pp = pplants.get(str(code))
        if cap <= 0.0 or not camp_b64 or not pp or not pp.get("m"):
            continue
        scale = cap / 100.0
        for h, v in enumerate(base64.b64decode(camp_b64)[:t]):
            act[h] += v * scale
        for h, v in enumerate(base64.b64decode(pp["m"])[:t]):
            model[h] += v * scale
        btm_twh += float(bp.get("btm") or 0.0)
        n_used += 1
    if n_used == 0:
        return None
    btm_mw = btm_twh * 1e6 / t  # flat BTM CHP host removal (both sides carry it)
    act = [a - btm_mw + float(cogen) * 1e6 / t for a in act]
    core_twh = sum(model) / 1e6 - btm_twh
    fill_mw = 0.0
    if model_twh is not None:
        fill_mw = (float(model_twh) - core_twh) * 1e6 / t
    model = [m - btm_mw + fill_mw for m in model]
    r, nrmse = _pearson_nrmse(model, act)
    return round(r, 3), round(nrmse, 3), round(sum(act) / 1e6, 2)


def score_dispatch_corr(
    year: int, ypay: dict, ybench: dict | None = None, iso: str = "ERCOT"
) -> list[dict]:
    """C4 — fleet hourly r/NRMSE floors for the gas and coal fleets.

    For a :data:`CEMS_GAS_ANCHOR_ISOS` ISO from the onset vintage onward, the
    gas fit is recomputed on the CEMS basis (:func:`_cems_gas_hourly_fit`) —
    the committed payload's 930-based ``fuelRows`` values score benchmark
    corruption there, not the model. Pre-onset years and every other ISO keep
    the payload's committed fit unchanged.
    """
    rows = {r.get("fuel"): r for r in ypay.get("fuelRows", [])}
    out = []
    for fam in ("gas", "coal"):
        r = rows.get(fam, {})
        rr, nr = r.get("r"), r.get("nrmse")
        cems_fit = None
        if (
            fam == "gas"
            and iso in CEMS_GAS_ANCHOR_ISOS
            and year >= CEMS_GAS_ANCHOR_ONSET.get(iso, 9999)
            and ybench is not None
        ):
            cems_fit = _cems_gas_hourly_fit(ypay, ybench, r.get("m"))
            if cems_fit is not None:
                rr, nr = cems_fit[0], cems_fit[1]
                r = dict(r, b=cems_fit[2])
        if rr is None and nr is None:
            out.append(
                _skip("dispatch_corr", year, f"{fam} hourly fit absent", key=fam)
            )
            continue
        twh = max(abs(r.get("m") or 0.0), abs(r.get("b") or 0.0))
        if twh < DISP_MIN_TWH:
            out.append(
                _skip(
                    "dispatch_corr",
                    year,
                    f"{fam} fleet immaterial (<{DISP_MIN_TWH:g} TWh); "
                    "hourly correlation degenerate",
                    key=fam,
                )
            )
            continue
        ok = (rr is not None and rr >= DISP_R_FLOOR) and (
            nr is not None and nr <= DISP_NRMSE_MAX
        )
        out.append(
            {
                "criterion": "dispatch_corr",
                "key": fam,
                "year": year,
                "status": PASS if ok else FAIL,
                "classification": None if ok else MODEL_MISS,
                "metric": (
                    f"{fam} fleet hourly r / NRMSE"
                    + (
                        " (CEMS hourly + flat cogen block; 930 NG cell "
                        "corrupted — FINDING 2026-07-12)"
                        if cems_fit is not None
                        else ""
                    )
                ),
                "model": f"r={rr} nrmse={nr}",
                "actual": None,
                "tol": f"r≥{DISP_R_FLOOR:.2f}, NRMSE≤{DISP_NRMSE_MAX:.2f}",
                "magnitude": f"r={rr}, NRMSE={nr}",
            }
        )
    return out


def score_co2(year: int, ypay: dict, ybench: dict) -> dict:
    """C5a — CO2 vs eGRID; SKIPPED unless an emissions actual is committed.

    Both sides are the full-plant CHP-inclusive basis (rubric v2.3): the
    renderer/retrofit adds the measured BTM CHP host supply back onto the
    model's grid dispatch and onto the EIA-923 class totals before applying
    the eGRID/CAMPD intensities, because those per-plant rates are defined
    over each cogen's FULL net generation. Committed payloads carry the
    already-based numbers; this gate just compares them.
    """
    model = (ypay.get("co2") or {}).get("model")
    actual = (ybench.get("co2") or {}).get("egrid")
    if model is None or actual is None:
        return _skip("co2", year, "no CO2/eGRID actual in committed artifacts")
    err = _pct(model, actual)
    if err is None:
        return _skip("co2", year, "CO2 percentage undefined (zero actual)")
    status, classification = _band_result(abs(err), CO2_TOL, CO2_COMMERCIAL)
    return {
        "criterion": "co2",
        "key": None,
        "year": year,
        "status": status,
        "classification": classification,
        "metric": "system CO2 vs eGRID (full-plant basis, BTM CHP added back)",
        "model": model,
        "actual": actual,
        "tol": (
            f"±{CO2_TOL * 100:.0f}% target / ±{CO2_COMMERCIAL * 100:.0f}% commercial"
        ),
        "magnitude": f"{err * 100:+.1f}%",
    }


# (score_storage / score_storage_shape — the C5b/C5c scorers — were removed
# with the criteria by the v2.7 owner amendment 2026-07-16. The storage
# payload/bench diagnostics they read stay committed and rendered on the
# dashboard run pages; the pre-removal scoring definitions live in git
# history and the rubric doc's v2.6 history entry.)


_LEGIT_HOWTO = (
    "run scripts/legitimacy_diagnostics.py --bundle <dir> --iso <ISO> "
    "--json-out <dir>/legitimacy_diagnostics.json and commit it"
)


def _class_load_share(klass: str, ypay: dict, ybench: dict) -> float | None:
    """Class annual energy as a fraction of total ISO load (C8 materiality).

    Uses ``max(model, actual)`` energy for the class — a binding floor cannot
    hide a class below the materiality line by its own forcing (forcing raises
    model energy), and a model that zeroes a genuinely material class stays
    scored via the actual side. ``None`` when the totals are unavailable
    (caller then gates — conservative, never a silent skip).
    """
    gm = ypay.get("gmModel") or {}
    cf = ybench.get("classFull") or {}
    m = float(gm.get(klass, 0.0))
    a = float(cf.get(klass) or 0.0)
    if m == 0.0 and a == 0.0 and klass in PLANT_GROUP_MEMBERS:
        # The class label is a CAMPD plant-group aggregate (D-2 vocabulary)
        # whose energy the payload/bench carry under the scored-class split —
        # sum the members so the coal fleet is not read as 0 % of load (v2.8).
        members = PLANT_GROUP_MEMBERS[klass]
        m = sum(float(gm.get(c, 0.0)) for c in members)
        a = sum(float(cf.get(c) or 0.0) for c in members)
    _, a_gen = _gen_totals(ypay, ybench)
    load = _total_load(ypay, a_gen)
    if load <= 0:
        return None
    return max(m, a) / load


def _immaterial_protective(criterion, klass, year, share, extra=""):
    """SKIPPED-immaterial record for a C8 class below the materiality floor."""
    rec = _skip(
        criterion,
        year,
        (
            f"{klass} immaterial ({share:.1%} of ISO load < "
            f"{PROTECTIVE_MIN_LOAD_FRAC:.0%} floor, max(model, actual) energy): "
            "reported by the D-1/D-2 diagnostics, not gated (rubric v2.1 owner "
            f"amendment 2026-07-06){extra}"
        ),
        key=klass,
    )
    return rec


# (``score_shape`` — the C7 diurnal-shape scorer — was DELETED by the v3.1
# owner amendment 2026-08-06. C7 is retired from the report and the
# determination, and rule 26 [R-DELETE] requires removal rather than a
# zeroed/dormant gate. Its D-1 source rows are untouched: C8's
# grounded-above-budget escalation still reads them via ``_d1_shape`` below,
# which is where CLAUDE.md rule 20 [R-FORCED-BUDGET] puts the shape test.)


def _binding_merchant_mechs(legit: dict, year: int, klass: str) -> list[str]:
    """Mechanism NAMES the class is forced by that count toward the C8 gate.

    From the committed D-2 per-(class, mechanism) rows: every mechanism with a
    positive ``share_of_class`` for ``(year, klass)`` that is NOT in
    :data:`FORCED_EXEMPT_MECH_NAMES` (structural must-run / non-thermal
    boundaries, which run_d2 already excludes from the class forced share). This
    is exactly the set whose forcing must be justified for a grounded-above-budget
    pass.
    """
    out: list[str] = []
    for r in legit.get("diagnostics", {}).get("D2", {}).get("rows", []):
        if int(r.get("year", -1)) != int(year) or str(r.get("class")) != str(klass):
            continue
        mech = str(r.get("mechanism", ""))
        if float(r.get("share_of_class", 0) or 0.0) > 0.0 and (
            mech not in FORCED_EXEMPT_MECH_NAMES
        ):
            out.append(mech)
    return sorted(set(out))


def _d4_provenance(legit: dict, year: int, klass: str, mechs: list[str]):
    """(ok, detail) — do ALL of the class's binding merchant mechanisms clear D-4.

    A mechanism clears when the committed D-4 off-window rows carry at least one
    entry for it (a declared, driver-justified window — the ``floor`` label is
    the mechanism name, optionally ``<mech> × <class>``) that applies to this
    class, and EVERY applicable entry passes (off-window share within the D-4
    tolerance). A mechanism with NO applicable D-4 row has no declared window —
    provenance fails for it (rule 12: no floor without a window). ``detail``
    names the offending mechanism(s) for the report.
    """
    if not mechs:
        # No attributable binding merchant mechanism (D-2 rows absent, or a
        # legacy artifact without them): forcing above the cap that cannot be
        # traced to a mechanism cannot be grounded — fail conservatively.
        return False, (
            "no attributable binding merchant mechanism in D-2 rows "
            "(provenance unverifiable)"
        )
    d4_rows = legit.get("diagnostics", {}).get("D4", {}).get("rows", [])
    unwindowed: list[str] = []
    offwindow: list[str] = []
    misconduct: list[str] = []
    for mech in mechs:
        applicable = [
            row
            for row in d4_rows
            if int(row.get("year", -1)) == int(year)
            and str(row.get("floor", "")) in (mech, f"{mech} × {klass}")
        ]
        if not applicable:
            unwindowed.append(mech)
            continue
        # Two D-4 checks share the ``rows`` list and the ``floor`` label
        # (legitimacy_diagnostics.run_d4): the original off-window energy
        # share (``check == "window"``, or absent in a pre-rider artifact)
        # and the per-unit conduct rider adopted with K6' at nyiso-140. Both
        # are provenance failures; they are separated only so the report says
        # which one fired. A pre-rider bundle re-scores exactly as before.
        for row in applicable:
            if str(row.get("verdict")) != "FAIL":
                continue
            if str(row.get("check", "window")) == "unit-conduct":
                misconduct.append(f"{mech} (plant {row.get('plant', '?')})")
            else:
                offwindow.append(mech)
    ok = not unwindowed and not offwindow and not misconduct
    bits = []
    if unwindowed:
        bits.append("no declared D-4 window: " + ", ".join(unwindowed))
    if offwindow:
        bits.append("binds off-window (D-4 FAIL): " + ", ".join(sorted(set(offwindow))))
    if misconduct:
        bits.append(
            "floors a unit its own meter says is offline (D-4 per-unit conduct "
            "FAIL): " + ", ".join(sorted(set(misconduct)))
        )
    return ok, ("; ".join(bits) if bits else "all binding mechanisms clear D-4")


def _d1_shape(legit: dict, year: int, klass: str):
    """(ok, detail) — does the class's D-1 hour-of-day profile clear the gates.

    Applies the artifact's own D-1 gates (``d1_min_profile_r`` /
    ``d1_min_cv_ratio``) to ``klass`` regardless of whether it is in the default
    ``d1_gated_classes`` — the escalation treats any above-budget class as
    shape-gated. A missing D-1 row (no profile to check) fails conservatively:
    an unverifiable shape cannot ground the forcing.
    """
    gates = legit.get("gates", {})
    min_r = float(gates.get("d1_min_profile_r", 0.8))
    min_cv = float(gates.get("d1_min_cv_ratio", 0.5))
    row = next(
        (
            r
            for r in legit.get("diagnostics", {}).get("D1", {}).get("rows", [])
            if int(r.get("year", -1)) == int(year) and str(r.get("class")) == str(klass)
        ),
        None,
    )
    if row is None:
        return False, f"no D-1 profile for {klass} (shape unverifiable)"
    r_val = row.get("profile_r")
    cv = row.get("cv_ratio")  # None when actual off-peak CV is degenerate
    r_ok = r_val is not None and float(r_val) >= min_r
    cv_ok = cv is None or float(cv) >= min_cv
    detail = (
        f"profile r {r_val} (≥{min_r}) & off-peak CV ratio "
        f"{cv if cv is not None else 'n/a'} (≥{min_cv})"
    )
    return (r_ok and cv_ok), detail


def score_forced_share(
    year: int, legit: dict | None, ypay: dict, ybench: dict
) -> list[dict]:
    """C8 — forced-energy share (audit D-2 / CLAUDE.md rule 20, as amended).

    Reads the D-2 per-class summary from the bundle's committed
    ``legitimacy_diagnostics.json`` — the share of a class's energy dispatched
    AT a binding non-exempt ``min_gen`` floor (nuclear / CHP-steam /
    coal-take-or-pay mechanisms exempt) — and gates the MEASURED share against
    the rubric's caps (< 15 % peaker / < 30 % merchant, rule 20 as amended
    2026-07-06; the artifact's own embedded verdict is ignored so artifacts
    written under earlier gate values score correctly). Materiality floor
    (rubric v2.1): a class below ``PROTECTIVE_MIN_LOAD_FRAC`` of ISO load is
    SKIPPED-immaterial (reported, never gated). Rebuilt-floor shares
    (``lower_bound``) are flagged in the record: a PASS there is a lower
    bound, never an upper one. SKIPPED when the artifact or the year is
    absent.

    ``upper_bound`` (pjm-149 §3.2) is the mirror flag and is likewise
    ANNOTATED, never acted on: the class holds a plant whose dispatch the
    diagnostics substituted with its own floor because the active dispatch
    source carried no series for it, which bounds the numerator above and the
    denominator below. A PASS under an upper bound is therefore SOUND (under
    the cap proves under the cap) while a breach is INDETERMINATE and escalates
    to the owner rather than convicting — the status logic below is deliberately
    unchanged, so this text arms only on artifacts written after pjm-149 and
    re-scores every existing keeper byte-identically.

    Grounded-above-budget escalation (rubric v2.2, 2026-07-07): a class ABOVE
    its cap is no longer an automatic FAIL. It escalates to a conditional pass
    on PROVENANCE (every binding merchant mechanism clears D-4 off-window
    binding — :func:`_d4_provenance`) AND SHAPE (the class's D-1 profile clears
    the artifact gates — :func:`_d1_shape`). Both clear -> CLEAN PASS classified
    :data:`GROUNDED_ABOVE_BUDGET` (surfaced as a report note, not a caveat);
    either fails -> FAIL, the miss described as a forcing shape/provenance
    mismatch (the "forcing variables are wrong" signal). See the constant block
    for the full rationale.
    """
    if legit is None:
        return [
            _skip(
                "forced_share",
                year,
                f"no legitimacy_diagnostics.json in bundle — {_LEGIT_HOWTO}",
            )
        ]
    rows = [
        r
        for r in legit.get("diagnostics", {}).get("D2", {}).get("summary", [])
        if int(r.get("year", -1)) == int(year)
    ]
    if not rows:
        return [
            _skip(
                "forced_share",
                year,
                "no D-2 per-class summary for this year in legitimacy_diagnostics.json",
            )
        ]
    out = []
    for r in rows:
        klass = r.get("class")
        fs = float(r.get("forced_share", 0) or 0.0)
        share = _class_load_share(klass, ypay, ybench)
        if share is not None and share < PROTECTIVE_MIN_LOAD_FRAC:
            out.append(
                _immaterial_protective(
                    "forced_share",
                    klass,
                    year,
                    share,
                    extra=f"; D-2 reads {fs * 100:.1f}% forced",
                )
            )
            continue
        cap = (
            FORCED_SHARE_PEAKER_MAX
            if klass in FORCED_SHARE_PEAKER_CLASSES
            else FORCED_SHARE_MERCHANT_MAX
        )
        lb = (
            " (rebuilt floors exclude the P1-dependent RA bridge — share is a lower bound)"
            if r.get("lower_bound")
            else ""
        )
        # pjm-149 §3.2 — annotation only, deliberately not a status change.
        lb += (
            " (holds a floor-substituted plant absent from the dispatch source "
            "— share is an UPPER bound: a pass is sound, a breach indeterminate)"
            if r.get("upper_bound")
            else ""
        )
        base = f"{fs * 100:.1f}% forced ({r.get('forced_twh')} of {r.get('class_total_twh')} TWh)"
        if fs <= cap:
            # Within budget: passes cheaply on the share alone (unchanged).
            status, classification, magnitude = PASS, None, base + lb
        else:
            # Above budget: escalate on provenance (D-4) + shape (D-1).
            mechs = _binding_merchant_mechs(legit, year, klass)
            prov_ok, prov_detail = _d4_provenance(legit, year, klass, mechs)
            shape_ok, shape_detail = _d1_shape(legit, year, klass)
            if prov_ok and shape_ok:
                status, classification = PASS, GROUNDED_ABOVE_BUDGET
                magnitude = (
                    f"{base} — above the {cap * 100:.0f}% cap but GROUNDED: "
                    f"{prov_detail}; {shape_detail}{lb}"
                )
            else:
                status, classification = FAIL, MODEL_MISS
                miss = "; ".join(
                    part
                    for part in (
                        None if prov_ok else f"provenance — {prov_detail}",
                        None if shape_ok else f"shape — {shape_detail}",
                    )
                    if part
                )
                magnitude = (
                    f"{base} — above the {cap * 100:.0f}% cap and NOT grounded "
                    f"(forcing variables miscalibrated): {miss}{lb}"
                )
        out.append(
            {
                "criterion": "forced_share",
                "key": klass,
                "year": year,
                "status": status,
                "classification": classification,
                "metric": f"{klass} energy at binding non-exempt floors (D-2)",
                "model": fs,
                "actual": None,
                "tol": (
                    f"< {cap * 100:.0f}% of class energy, OR above-cap with D-4 "
                    f"window + D-1 shape clear (class ≥ {PROTECTIVE_MIN_LOAD_FRAC:.0%} "
                    "of load)"
                ),
                "magnitude": magnitude,
            }
        )
    return out


def _skip(criterion: str, year: int, reason: str, key: str | None = None) -> dict:
    """Build a SKIPPED record (recorded as not-scored, never a silent pass)."""
    return {
        "criterion": criterion,
        "key": key,
        "year": year,
        "status": SKIPPED,
        "classification": None,
        "metric": (
            CRITERIA[criterion][0]
            if criterion in CRITERIA
            else REPORTED_ONLY[criterion]
        ),
        "model": None,
        "actual": None,
        "tol": None,
        "magnitude": reason,
    }


def score_governance(config: dict | None, attestation: dict | None) -> dict:
    """C6 — governance gate (machine cross-check + required attestation).

    PASS iff config is clean (exogenous outage source, no forbidden flags) AND an
    attestation is present with all four assertions true. FAIL if the machine
    check trips or any assertion is false. UNATTESTED (-> NOT-YET) if no
    attestation file exists — a run cannot be certified unattested.
    """
    sc = (config or {}).get("scenario_config", {})
    meta = (config or {}).get("meta", {})
    outage = meta.get("outage_source") or sc.get("outage_source")
    machine_issues = []
    if outage is not None and outage not in EXOGENOUS_OUTAGE_SOURCES:
        machine_issues.append(
            f"outage_source={outage!r} is not an exogenous availability source"
        )
    for flag in FORBIDDEN_FLAGS:
        if sc.get(flag):
            machine_issues.append(f"forbidden fitted-mechanism flag active: {flag}")

    assertions = [
        "levers_trace_to_measured_input",
        "no_fit_to_price_residuals",
        "no_pinning_to_actuals",
        "outage_filter_exogenous_net_load",
    ]
    if attestation is None or not attestation.get("governance"):
        # A bundle whose attestation carries no governance block (e.g. only a
        # free_parameters DOF ledger) is exactly as unattested as one with no
        # file: nobody has asserted the four governance claims.
        status, detail = (
            "UNATTESTED",
            "no governance attestation in bundle"
            + ("" if attestation is None else " (attestation has no governance block)"),
        )
    else:
        gov = attestation.get("governance", {})
        false_asserts = [a for a in assertions if not gov.get(a, False)]
        if machine_issues:
            status, detail = FAIL, "; ".join(machine_issues)
        elif false_asserts:
            status, detail = FAIL, "attestation false: " + ", ".join(false_asserts)
        else:
            status = PASS
            detail = gov.get("attested_by", "attested")
    if attestation is None and machine_issues:
        detail = "; ".join(machine_issues) + "; and no attestation"
    return {
        "criterion": "governance",
        "key": None,
        "year": None,
        "status": status,
        "classification": None if status == PASS else MODEL_MISS,
        "metric": "every lever measured; no residual fit / pinning; exogenous outages",
        "model": None,
        "actual": None,
        "tol": "pass/fail",
        "magnitude": detail,
        "machine_issues": machine_issues,
    }


# ---------------------------------------------------------------------------
# Aggregation + determination
# ---------------------------------------------------------------------------
def _agg_status(records: list[dict]) -> str:
    """Aggregate per-year statuses for one criterion (FAIL>CAVEAT>PASS>SKIPPED)."""
    s = {r["status"] for r in records}
    if FAIL in s:
        return FAIL
    if CAVEAT in s:
        return CAVEAT
    if PASS in s:
        return PASS
    return SKIPPED


def free_class_score(iso: str, records: list[dict]) -> dict:
    """D-10 — recompute the C1 pass rate with the pinned classes excluded.

    ``records`` are the already-scored per-criterion records; this reads the C1
    (``fuelmix``) rows only. Returns both the all-class C1 pass rate and the
    "free-class" rate that excludes the ISO's pinned classes
    (:data:`PINNED_CLASSES_BY_ISO`) — the classes the audit L-rows show are
    pinned to a measured realization (wind/solar/nuclear/hydro/CHP/imports), so a
    pass there is plumbing. Pass = clean in-tolerance (``PASS``); the denominator
    is the gated (scored, non-``SKIPPED``) C1 rows. No gate — the number is the
    deliverable ("pinned-class gate inflation" made visible; audit §7 D-10).
    """
    pinned = PINNED_CLASSES_BY_ISO.get(iso.upper(), _PINNED_CLASSES_COMMON)
    scored = [
        r
        for r in records
        if r["criterion"] == "fuelmix" and r["status"] in (PASS, FAIL, CAVEAT)
    ]
    free = [r for r in scored if r.get("key") not in pinned]

    def _rate(rows: list[dict]) -> dict:
        return {
            "pass": sum(1 for r in rows if r["status"] == PASS),
            "total": len(rows),
        }

    all_rate, free_rate = _rate(scored), _rate(free)
    return {
        "iso": iso,
        "pinned_classes": sorted(pinned),
        "excluded_from_free": sorted(
            {r.get("key") for r in scored if r.get("key") in pinned}
        ),
        "all": all_rate,
        "free": free_rate,
        "headline": (
            f"C1 all {all_rate['pass']}/{all_rate['total']} · "
            f"free {free_rate['pass']}/{free_rate['total']}"
        ),
    }


def determine(run_id: str) -> dict:
    """Score one run from its committed artifacts (rubric §2)."""
    return determine_from_artifacts(run_id, load_artifacts(run_id))


def determine_from_artifacts(run_id: str, art: dict) -> dict:
    """Score one run's loaded artifacts and return the full verdict dict.

    Split out from :func:`determine` so the decision logic can be unit-tested on
    synthetic artifacts without reading files.
    """
    sidecar, payload, bench = art["sidecar"], art["payload"], art["bench"]
    iso = sidecar.get("iso", "ERCOT")
    exceptions = (art["attestation"] or {}).get("exceptions", [])

    target_years = [int(y) for y in sidecar.get("years", [])]
    scorable_years = sorted(int(y) for y in (payload or {}).get("years", {}))
    data_blocked = sorted(set(target_years) - set(scorable_years))

    # Score every criterion-year.
    records: list[dict] = []
    for year in scorable_years:
        ypay = payload["years"][str(year)]
        ybench = bench.get(year, {})
        records += score_fuelmix(year, ypay, ybench, iso)
        records += score_sysvol(year, ypay, ybench, iso, bench_all=bench)
        records.append(score_price_mean(year, ypay, ybench))
        da_diag = score_price_mean_da_diagnostic(year, ypay, ybench)
        if da_diag is not None:
            records.append(da_diag)
        records.append(score_price_shape(year, ypay, ybench))
        records += score_price_tail(year, ypay, iso)
        records += score_dispatch_corr(year, ypay, ybench, iso)
        records.append(score_co2(year, ypay, ybench))
        # (No C7 row: retired outright by the v3.1 owner amendment 2026-08-06.)
        records += score_forced_share(year, art.get("legitimacy"), ypay, ybench)

    # Apply the exceptions ledger (FAIL -> CAVEAT where documented).
    for r in records:
        _apply_ledger(r, exceptions)

    gov = score_governance(art["config"], art["attestation"])

    # Owner STANDING RULE (2026-08-06) — auto-ledger a LONE C3c failure on an
    # out-of-training year. Runs AFTER the explicit ledger and AFTER governance,
    # because it is conditioned on both.
    _apply_c3c_standing_rule(records, gov)

    # Aggregate per criterion.
    per_criterion: dict[str, dict] = {}
    for cid, (label, tier) in CRITERIA.items():
        if cid == "governance":
            per_criterion[cid] = {
                "label": label,
                "tier": tier,
                "hard": True,  # legacy display key: protective = the v1 hard gate
                "status": gov["status"],
                "records": [gov],
            }
            continue
        recs = [r for r in records if r["criterion"] == cid]
        # A criterion at CAVEAT is LEDGERED when any of its caveat records was
        # earned by an exceptions-ledger entry (MEASURED_LIMIT or, v3.0,
        # MODEL_LIMIT — both budgeted); otherwise every caveat sits inside the
        # commercial band (auto, listed not budgeted).
        ledgered = any(
            r["status"] == CAVEAT
            and r.get("classification") in (MEASURED_LIMIT, MODEL_LIMIT)
            for r in recs
        )
        per_criterion[cid] = {
            "label": label,
            "tier": tier,
            "hard": tier == TIER_PROTECT,
            "status": _agg_status(recs) if recs else SKIPPED,
            "caveat_kind": (
                ("ledgered" if ledgered else "commercial-band")
                if (_agg_status(recs) if recs else SKIPPED) == CAVEAT
                else None
            ),
            "records": recs,
        }

    # Caveat budgets (rubric §2 v2): protective ledgered caveats keep the v1
    # budget of 1; non-protective LEDGERED caveats are capped at 3; auto
    # commercial-band caveats are unbudgeted (inside the certification claim)
    # but every one is listed below with its magnitude.
    protective_caveats = [
        c
        for cid, c in per_criterion.items()
        if c["tier"] == TIER_PROTECT and cid != "governance" and c["status"] == CAVEAT
    ]
    ledgered_caveats = [
        c
        for cid, c in per_criterion.items()
        if c["tier"] != TIER_PROTECT
        and c["status"] == CAVEAT
        and c["caveat_kind"] == "ledgered"
    ]
    band_caveats = [
        c
        for cid, c in per_criterion.items()
        if c["tier"] != TIER_PROTECT
        and c["status"] == CAVEAT
        and c["caveat_kind"] == "commercial-band"
    ]
    fails = [cid for cid, c in per_criterion.items() if c["status"] == FAIL]
    # An unscored criterion can never be a silent pass: it caps the
    # determination at CALIBRATED-WITH-CAVEATS and is named in the reasons
    # (protective skips — e.g. C8 with no committed
    # legitimacy_diagnostics.json — are called out explicitly).
    skipped = [
        cid
        for cid, c in per_criterion.items()
        if cid != "governance" and c["status"] == SKIPPED
    ]
    skipped_protective = [
        cid for cid in skipped if per_criterion[cid]["tier"] == TIER_PROTECT
    ]

    # Determination (rubric §2).
    reasons: list[str] = []
    if gov["status"] != PASS:
        determination = NOT_YET
        reasons.append(f"governance gate {gov['status']}: {gov['magnitude']}")
    elif fails:
        determination = NOT_YET
        reasons.append(
            "undocumented out-of-tolerance (FAIL) criteria: " + ", ".join(fails)
        )
    elif (
        len(protective_caveats) > MAX_PROTECTIVE_CAVEATS
        or len(ledgered_caveats) > MAX_LEDGERED_CAVEATS
    ):
        determination = NOT_YET
        reasons.append(
            "caveat budget exceeded (protective "
            f"{len(protective_caveats)}/{MAX_PROTECTIVE_CAVEATS}, ledgered "
            f"{len(ledgered_caveats)}/{MAX_LEDGERED_CAVEATS})"
        )
    else:
        # RUBRIC v3.3 (owner amendment 2026-08-17): a LEDGERED caveat does not
        # downgrade the determination. Ledgering is restricted to C3c alone
        # (LEDGERABLE_CRITERIA, v3.1), so this is exactly the owner's rule —
        # an accepted, ledgered C3c price-tail limitation is reported in full
        # but is not itself the thing that turns CALIBRATED into
        # CALIBRATED-WITH-CAVEATS. Every other route to a caveat still
        # downgrades: commercial-band target misses, protective-gate caveats,
        # unscored criteria and data-blocked years are untouched.
        downgrading_caveats = len(protective_caveats) + len(band_caveats)
        if downgrading_caveats == 0 and not skipped and not data_blocked:
            determination = CALIBRATED
        else:
            determination = CALIBRATED_CAVEATS
            if band_caveats:
                reasons.append(
                    f"{len(band_caveats)} criterion(s) within the commercial-grade "
                    "band but outside target: "
                    + ", ".join(c["label"] for c in band_caveats)
                )
            if protective_caveats:
                reasons.append(
                    f"{len(protective_caveats)} protective-gate ledgered caveat(s): "
                    + ", ".join(c["label"] for c in protective_caveats)
                )
            if skipped_protective:
                reasons.append(
                    "unscored PROTECTIVE criteria: " + ", ".join(skipped_protective)
                )
            other_skips = [c for c in skipped if c not in skipped_protective]
            if other_skips:
                reasons.append("unscored criteria: " + ", ".join(other_skips))
            if data_blocked:
                reasons.append(
                    "data-blocked target year(s): " + ", ".join(map(str, data_blocked))
                )
        # Emitted on BOTH branches, and LAST so it never displaces a
        # downgrading reason from :func:`headline`'s reasons[0]. A CALIBRATED
        # run carrying a ledgered C3c states it on its own determination basis,
        # at full magnitude — silence here is what would make v3.3 an escape
        # hatch, so the caveat stays visible in `reasons`, in `caveats.ledgered`
        # and in `grade_summary.ledgered` exactly as before.
        if ledgered_caveats:
            reasons.append(
                f"{len(ledgered_caveats)} ledgered caveat(s) (measured-input or "
                "model-class) — REPORTED, and NOT determination-downgrading "
                "under rubric v3.3: " + ", ".join(c["label"] for c in ledgered_caveats)
            )

    # Report notes (not caveats): grounded-above-budget C8 passes — a class
    # forced past its cap that cleared the D-4 provenance + D-1 shape escalation
    # (owner decision 2026-07-07: a CLEAN PASS surfaced as a note so the high
    # forcing stays visible and auditable without counting against any budget).
    notes: list[str] = []
    for r in records:
        if (
            r.get("criterion") == "forced_share"
            and r.get("status") == PASS
            and r.get("classification") == GROUNDED_ABOVE_BUDGET
        ):
            notes.append(
                f"C8 {r['year']} {r.get('key')}: grounded above budget — {r['magnitude']}"
            )

    # Grade summary (reported): how many scored criteria sit at target grade
    # (clean PASS) vs commercial grade (auto band caveat) vs ledgered.
    scored = [
        c for cid, c in per_criterion.items() if c["status"] in (PASS, CAVEAT, FAIL)
    ]
    grade_summary = {
        "scored": len(scored),
        "target_grade": sum(1 for c in scored if c["status"] == PASS),
        "commercial_grade": len(band_caveats),
        "ledgered": len(ledgered_caveats) + len(protective_caveats),
        "fails": len(fails),
    }

    return {
        "run_id": run_id,
        "iso": iso,
        "label": sidecar.get("label", run_id),
        "rubric_version": RUBRIC_VERSION,
        "target_years": target_years,
        "scorable_years": scorable_years,
        "data_blocked_years": data_blocked,
        "determination": determination,
        "reasons": reasons,
        "notes": notes,
        "criteria": per_criterion,
        "free_class_score": free_class_score(iso, records),
        "grade_summary": grade_summary,
        "caveats": {
            "protective": [c["label"] for c in protective_caveats],
            "ledgered": [c["label"] for c in ledgered_caveats],
            "commercial_band": [c["label"] for c in band_caveats],
            "budget": {
                "protective_max": MAX_PROTECTIVE_CAVEATS,
                "ledgered_max": MAX_LEDGERED_CAVEATS,
            },
        },
        "ledger_entries": exceptions,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
_MARK = {PASS: "✓", CAVEAT: "~", FAIL: "✗", SKIPPED: "·", "UNATTESTED": "?"}


def render_text(v: dict) -> str:
    """Render the verdict as a compact, auditable text block."""
    lines = []
    lines.append("=" * 72)
    lines.append(f"CALIBRATION DETERMINATION: {v['determination']}")
    lines.append(f"  run {v['run_id']}  ({v['iso']}: {v['label']})")
    yrs = ", ".join(map(str, v["scorable_years"])) or "none"
    lines.append(f"  scorable years: {yrs}")
    if v["data_blocked_years"]:
        lines.append(
            "  data-blocked years: " + ", ".join(map(str, v["data_blocked_years"]))
        )
    lines.append("=" * 72)
    _TIER_TAG = {
        TIER_LOAD: "LOAD",
        TIER_SUPPORT: "SUPP",
        TIER_PROTECT: "PROT",
    }
    for cid, c in v["criteria"].items():
        gate = _TIER_TAG.get(c.get("tier"), "?")
        kind = f" [{c['caveat_kind']}]" if c.get("caveat_kind") else ""
        lines.append(
            f"[{_MARK.get(c['status'], '?')}] {c['status']:7s} {gate:4s}  "
            f"{c['label']}{kind}"
        )
        for r in c["records"]:
            if r["status"] == PASS:
                continue  # keep the block focused on what isn't a clean pass
            key = f" {r['key']}" if r.get("key") else ""
            yr = f" {r['year']}" if r.get("year") else ""
            cls = f"  [{r['classification']}]" if r.get("classification") else ""
            lines.append(f"        {r['status']:7s}{yr}{key}: {r['magnitude']}{cls}")
            if r.get("ledger_reason"):
                lines.append(f"          ledger: {r['ledger_reason']}")
    lines.append("-" * 72)
    fcs = v.get("free_class_score")
    if fcs:
        lines.append(f"D-10 free-class C1: {fcs['headline']}")
        if fcs.get("excluded_from_free"):
            lines.append(
                "  pinned (excluded from free): " + ", ".join(fcs["excluded_from_free"])
            )
    if v["reasons"]:
        lines.append("determination basis:")
        for rsn in v["reasons"]:
            lines.append(f"  - {rsn}")
    else:
        lines.append("determination basis: all criteria pass, governance attested.")
    if v.get("notes"):
        lines.append("notes:")
        for note in v["notes"]:
            lines.append(f"  - {note}")
    lines.append("=" * 72)
    return "\n".join(lines)


def headline(v: dict) -> str:
    """One-line determination headline for the calibration-report skill output."""
    extra = f" — {v['reasons'][0]}" if v["reasons"] else ""
    return f"DETERMINATION: {v['determination']} [{v['iso']} {v['label']}]{extra}"


# ---------------------------------------------------------------------------
# Plaintext metrics sidecar (G-49, docs/verifying-dashboard-numbers.md
# "Proposed improvement: a plaintext metrics sidecar")
# ---------------------------------------------------------------------------
def condensed_metrics(v: dict) -> dict:
    """Condense a full verdict to the headline numbers a verifier checks first.

    Drops the per-class/per-year ``records`` detail that already lives in
    ``SUMMARY*.md`` / ``legitimacy_diagnostics.json`` / the ``runs/<id>.js``
    payload, keeping only the aggregate determination and per-criterion
    status — small enough to ``git show`` or ``jq`` directly.
    """
    return {
        "run_id": v["run_id"],
        "iso": v["iso"],
        "label": v["label"],
        "target_years": v["target_years"],
        "scorable_years": v["scorable_years"],
        "data_blocked_years": v["data_blocked_years"],
        "rubric_version": v.get("rubric_version", 1),
        "determination": v["determination"],
        "reasons": v["reasons"],
        "notes": v.get("notes", []),
        "criteria": {
            cid: {
                "label": c["label"],
                "tier": c.get("tier"),
                "status": c["status"],
                **({"caveat_kind": c["caveat_kind"]} if c.get("caveat_kind") else {}),
            }
            for cid, c in v["criteria"].items()
        },
        "caveats": v["caveats"],
        "grade_summary": v.get("grade_summary"),
        "free_class_score": v["free_class_score"],
    }


def bundle_dir_for(run_id: str) -> Path:
    """Return the repo-relative bundle directory a run id's sidecar points at."""
    sidecar = json.loads((REGISTRY_DIR / f"{run_id}.json").read_text())
    return REPO / sidecar["bundle"]


def write_metrics_sidecar(bundle_dir: Path, v: dict) -> Path:
    """Write the condensed metrics sidecar into ``bundle_dir/metrics.json``.

    This scorer remains the authoritative *generator*: the sidecar is its own
    condensed output, never a hand-maintained duplicate.
    """
    path = Path(bundle_dir) / "metrics.json"
    path.write_text(json.dumps(condensed_metrics(v), indent=2) + "\n")
    return path


def main() -> None:
    """CLI: score one run (by bundle dir or run id) and print its determination."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "run",
        nargs="?",
        help="bundle dir (results/calibration/<name>) or a run id",
    )
    ap.add_argument("--run-id", help="run id (alternative to the positional bundle)")
    ap.add_argument("--json", action="store_true", help="emit the machine verdict JSON")
    ap.add_argument(
        "--write-metrics",
        action="store_true",
        help=(
            "also write the condensed metrics.json sidecar (G-49) into the "
            "run's bundle dir"
        ),
    )
    args = ap.parse_args()
    target = args.run_id or args.run
    if not target:
        ap.error("provide a bundle dir or --run-id")
    run_id = args.run_id or resolve_run_id(target)
    verdict = determine(run_id)
    if args.json:
        print(json.dumps(verdict, indent=2))
    else:
        print(render_text(verdict))
    if args.write_metrics:
        path = write_metrics_sidecar(bundle_dir_for(run_id), verdict)
        print(f"wrote {path.relative_to(REPO)}")
    # Exit nonzero on NOT-YET so a CI gate / the forecast-validation check can
    # assert on the determination directly.
    sys.exit(0 if verdict["determination"] != NOT_YET else 1)


if __name__ == "__main__":
    main()
